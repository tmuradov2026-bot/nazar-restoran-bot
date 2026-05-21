"""
Menu ko'rsatish handlerlari
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models.database import SessionLocal, Category, MenuItem
from config.settings import RESTAURANT_NAME, RESTAURANT_ADDRESS, RESTAURANT_PHONE, RESTAURANT_WORKING_HOURS


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Barcha kategoriyalarni ko'rsatish."""
    db = SessionLocal()
    try:
        categories = db.query(Category).filter(Category.is_active == True).all()

        if not categories:
            await update.message.reply_text("😔 Hozircha menyu mavjud emas.")
            return

        keyboard = []
        for cat in categories:
            keyboard.append([
                InlineKeyboardButton(
                    f"{cat.emoji} {cat.name}",
                    callback_data=f"menu_cat_{cat.id}"
                )
            ])
        keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="menu_back")])

        await update.message.reply_text(
            "🍽️ *Bizning menyu kategoriyalari:*\n\nBiror kategoriyani tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    finally:
        db.close()


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menyu tugma bosilganda ishlash."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu_show":
        await _show_categories(query)
    elif data.startswith("menu_cat_"):
        cat_id = int(data.split("_")[-1])
        await _show_category_items(query, cat_id)
    elif data.startswith("menu_item_"):
        item_id = int(data.split("_")[-1])
        await _show_item_detail(query, item_id)
    elif data == "menu_about":
        await _show_about(query)
    elif data == "menu_back":
        await _show_main_menu(query)


async def _show_categories(query) -> None:
    db = SessionLocal()
    try:
        categories = db.query(Category).filter(Category.is_active == True).all()
        keyboard = []
        for cat in categories:
            count = db.query(MenuItem).filter(
                MenuItem.category_id == cat.id,
                MenuItem.is_available == True
            ).count()
            keyboard.append([
                InlineKeyboardButton(
                    f"{cat.emoji} {cat.name} ({count} ta)",
                    callback_data=f"menu_cat_{cat.id}"
                )
            ])
        keyboard.append([InlineKeyboardButton("🔙 Bosh menyu", callback_data="menu_back")])

        await query.edit_message_text(
            "🍽️ *Menyu kategoriyalari:*\n\nBiror kategoriyani tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    finally:
        db.close()


async def _show_category_items(query, cat_id: int) -> None:
    db = SessionLocal()
    try:
        category = db.query(Category).filter(Category.id == cat_id).first()
        items = db.query(MenuItem).filter(
            MenuItem.category_id == cat_id,
            MenuItem.is_available == True
        ).all()

        if not items:
            await query.edit_message_text(
                f"😔 {category.name} da hozircha taom mavjud emas.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Orqaga", callback_data="menu_show")
                ]])
            )
            return

        keyboard = []
        for item in items:
            keyboard.append([
                InlineKeyboardButton(
                    f"🍴 {item.name} - {item.price:,.0f} so'm",
                    callback_data=f"menu_item_{item.id}"
                )
            ])
        keyboard.append([InlineKeyboardButton("🔙 Kategoriyalar", callback_data="menu_show")])

        await query.edit_message_text(
            f"{category.emoji} *{category.name}*\n\nTaomni tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    finally:
        db.close()


async def _show_item_detail(query, item_id: int) -> None:
    db = SessionLocal()
    try:
        item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
        if not item:
            await query.answer("Taom topilmadi!", show_alert=True)
            return

        text = (
            f"🍴 *{item.name}*\n\n"
            f"💰 Narxi: *{item.price:,.0f} so'm*\n"
        )
        if item.description:
            text += f"📝 {item.description}\n"

        keyboard = [
            [InlineKeyboardButton(f"🛒 Buyurtma berish", callback_data=f"order_{item.id}")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data=f"menu_cat_{item.category_id}")],
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    finally:
        db.close()


async def _show_about(query) -> None:
    text = (
        f"🏠 *{RESTAURANT_NAME}*\n\n"
        f"📍 Manzil: {RESTAURANT_ADDRESS}\n"
        f"📞 Telefon: {RESTAURANT_PHONE}\n"
        f"🕐 Ish vaqti: {RESTAURANT_WORKING_HOURS}\n\n"
        f"Bizning manzilga kelib, mazali taomlarimizdan bahramand bo'ling! 🌟"
    )
    keyboard = [[InlineKeyboardButton("🔙 Bosh menyu", callback_data="menu_back")]]
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def _show_main_menu(query) -> None:
    keyboard = [
        [
            InlineKeyboardButton("🍽️ Menyu", callback_data="menu_show"),
            InlineKeyboardButton("🪑 Stollar", callback_data="tbl_show"),
        ],
        [
            InlineKeyboardButton("🛒 Buyurtmalarim", callback_data="order_my"),
            InlineKeyboardButton("ℹ️ Restoran haqida", callback_data="menu_about"),
        ],
    ]
    await query.edit_message_text(
        "🌟 Bosh menyu — nima qilmoqchisiz?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
