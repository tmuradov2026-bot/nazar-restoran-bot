"""
Admin panel handlerlari
"""

from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from models.database import SessionLocal, MenuItem, Category, Order, Table
from config.settings import ADMIN_IDS, OrderStatus

# Admin suhbat holatlari
ITEM_NAME = 1
ITEM_PRICE = 2
ITEM_CATEGORY = 3
ITEM_DESC = 4


def admin_only(func):
    """Faqat adminlar uchun decorator."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            msg = update.message or update.callback_query
            if update.callback_query:
                await update.callback_query.answer("⛔ Ruxsat yo'q!", show_alert=True)
            else:
                await update.message.reply_text("⛔ Bu buyruq faqat adminlar uchun!")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


@admin_only
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin bosh paneli."""
    db = SessionLocal()
    try:
        total_orders = db.query(Order).count()
        pending_orders = db.query(Order).filter(Order.status == OrderStatus.PENDING).count()
        total_items = db.query(MenuItem).filter(MenuItem.is_available == True).count()
        available_tables = db.query(Table).filter(Table.is_available == True).count()

        text = (
            f"👨‍💼 *Admin paneli*\n\n"
            f"📊 *Statistika:*\n"
            f"• Jami buyurtmalar: *{total_orders}*\n"
            f"• Kutilayotgan: *{pending_orders}*\n"
            f"• Menyu taomlar: *{total_items}*\n"
            f"• Bo'sh stollar: *{available_tables}*\n\n"
            f"Nima qilmoqchisiz?"
        )

        keyboard = [
            [
                InlineKeyboardButton("🍽️ Menyu boshqarish", callback_data="adm_menu"),
                InlineKeyboardButton("📋 Buyurtmalar", callback_data="adm_orders"),
            ],
            [
                InlineKeyboardButton("🪑 Stollarni boshqarish", callback_data="adm_tables"),
                InlineKeyboardButton("📊 Hisobot", callback_data="adm_report"),
            ],
        ]

        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    finally:
        db.close()


@admin_only
async def add_menu_item_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Yangi taom qo'shishni boshlash."""
    await update.message.reply_text(
        "🍴 *Yangi taom qo'shish*\n\n"
        "Taom nomini kiriting:\n"
        "(Bekor qilish uchun /cancel)",
        parse_mode="Markdown"
    )
    return ITEM_NAME


async def get_item_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Taom nomini olish."""
    context.user_data["new_item_name"] = update.message.text.strip()
    await update.message.reply_text(
        f"✅ Nom: *{context.user_data['new_item_name']}*\n\n"
        f"Narxini kiriting (so'mda, faqat raqam):",
        parse_mode="Markdown"
    )
    return ITEM_PRICE


async def get_item_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Narxni olish."""
    try:
        price = float(update.message.text.strip().replace(" ", "").replace(",", ""))
        context.user_data["new_item_price"] = price
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri narx! Faqat raqam kiriting:")
        return ITEM_PRICE

    db = SessionLocal()
    try:
        categories = db.query(Category).filter(Category.is_active == True).all()
        keyboard = [[InlineKeyboardButton(f"{c.emoji} {c.name}", callback_data=f"cat_{c.id}")] for c in categories]

        await update.message.reply_text(
            f"✅ Narx: *{price:,.0f} so'm*\n\nKategoriyani tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return ITEM_CATEGORY
    finally:
        db.close()


async def get_item_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Kategoriyani olish."""
    query = update.callback_query
    await query.answer()
    cat_id = int(query.data.split("_")[-1])
    context.user_data["new_item_category_id"] = cat_id

    await query.edit_message_text(
        "Taom haqida qisqacha tavsif kiriting\n(o'tkazib yuborish uchun `-` yozing):"
    )
    return ITEM_DESC


async def get_item_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tavsif olib, bazaga saqlash."""
    desc = update.message.text.strip()
    if desc == "-":
        desc = None

    db = SessionLocal()
    try:
        item = MenuItem(
            name=context.user_data["new_item_name"],
            price=context.user_data["new_item_price"],
            category_id=context.user_data["new_item_category_id"],
            description=desc,
        )
        db.add(item)
        db.commit()

        await update.message.reply_text(
            f"✅ *{item.name}* muvaffaqiyatli qo'shildi!\n"
            f"💰 Narxi: {item.price:,.0f} so'm",
            parse_mode="Markdown"
        )
    finally:
        db.close()

    context.user_data.clear()
    return ConversationHandler.END


async def cancel_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Admin amali bekor qilish."""
    context.user_data.clear()
    await update.message.reply_text("❌ Amal bekor qilindi.")
    return ConversationHandler.END


@admin_only
async def manage_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Buyurtmalarni boshqarish."""
    db = SessionLocal()
    try:
        orders = db.query(Order).filter(
            Order.status.in_([OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PREPARING])
        ).order_by(Order.created_at.desc()).limit(20).all()

        if not orders:
            await update.message.reply_text("📋 Faol buyurtmalar yo'q.")
            return

        for order in orders:
            table_num = order.table.number if order.table else "—"
            user_name = order.user.full_name if order.user else "Noma'lum"

            keyboard = [[
                InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"adm_confirm_{order.id}"),
                InlineKeyboardButton("🍳 Tayyorlanmoqda", callback_data=f"adm_prepare_{order.id}"),
                InlineKeyboardButton("🎉 Tayyor", callback_data=f"adm_ready_{order.id}"),
            ]]

            await update.message.reply_text(
                f"📋 *Buyurtma #{order.id}*\n"
                f"👤 Mijoz: {user_name}\n"
                f"🪑 Stol: #{table_num}\n"
                f"💰 Summa: {order.total_price:,.0f} so'm\n"
                f"📊 Holat: *{order.status}*",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
    finally:
        db.close()


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin inline tugmalarini ishlash."""
    query = update.callback_query
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await query.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return

    await query.answer()
    data = query.data
    db = SessionLocal()

    try:
        if data.startswith("adm_confirm_"):
            order_id = int(data.split("_")[-1])
            _update_order_status(db, order_id, OrderStatus.CONFIRMED)
            await query.edit_message_text(f"✅ Buyurtma #{order_id} tasdiqlandi!")

        elif data.startswith("adm_prepare_"):
            order_id = int(data.split("_")[-1])
            _update_order_status(db, order_id, OrderStatus.PREPARING)
            await query.edit_message_text(f"🍳 Buyurtma #{order_id} tayyorlanmoqda!")

        elif data.startswith("adm_ready_"):
            order_id = int(data.split("_")[-1])
            _update_order_status(db, order_id, OrderStatus.READY)
            # Stolni bo'shatish
            order = db.query(Order).filter(Order.id == order_id).first()
            if order and order.table_id:
                table = db.query(Table).filter(Table.id == order.table_id).first()
                if table:
                    table.is_available = True
                    db.commit()
            await query.edit_message_text(f"🎉 Buyurtma #{order_id} tayyor — stol bo'shatildi!")

        elif data == "adm_report":
            total = db.query(Order).count()
            total_revenue = db.query(Order).filter(
                Order.status == OrderStatus.DELIVERED
            ).with_entities(Order.total_price).all()
            revenue = sum(r[0] for r in total_revenue)
            await query.edit_message_text(
                f"📊 *Hisobot*\n\n"
                f"Jami buyurtmalar: *{total}*\n"
                f"Jami daromad: *{revenue:,.0f} so'm*",
                parse_mode="Markdown"
            )
    finally:
        db.close()


def _update_order_status(db, order_id: int, status: str):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        order.status = status
        db.commit()
