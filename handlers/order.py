"""
Buyurtma berish handlerlari — ConversationHandler bilan
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from models.database import SessionLocal, User, MenuItem, Table, Order, OrderItem
from config.settings import OrderStatus

# ConversationHandler holatlari
SELECT_TABLE = 1
CONFIRM_ORDER = 2


async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Buyurtmani boshlash — mahsulotni context'ga saqlash."""
    query = update.callback_query
    await query.answer()

    item_id = int(query.data.split("_")[-1])
    db = SessionLocal()
    try:
        item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
        if not item or not item.is_available:
            await query.edit_message_text("😔 Bu taom hozircha mavjud emas.")
            return ConversationHandler.END

        # Mahsulotni context'da saqlash
        context.user_data["order_item_id"] = item.id
        context.user_data["order_item_name"] = item.name
        context.user_data["order_item_price"] = item.price

        # Bo'sh stollarni ko'rsatish
        tables = db.query(Table).filter(Table.is_available == True).all()

        if not tables:
            await query.edit_message_text(
                "😔 Hozircha barcha stollar band. Iltimos, keyinroq urinib ko'ring."
            )
            return ConversationHandler.END

        keyboard = []
        for t in tables:
            keyboard.append([
                InlineKeyboardButton(
                    f"🪑 Stol #{t.number} ({t.capacity} kishi)",
                    callback_data=f"table_{t.id}"
                )
            ])
        keyboard.append([InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_order")])

        await query.edit_message_text(
            f"🛒 *{item.name}* — {item.price:,.0f} so'm\n\n"
            f"Qaysi stolda o'tirasiz?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return SELECT_TABLE

    finally:
        db.close()


async def select_table(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stol tanlash."""
    query = update.callback_query
    await query.answer()

    table_id = int(query.data.split("_")[-1])
    db = SessionLocal()
    try:
        table = db.query(Table).filter(Table.id == table_id).first()
        context.user_data["order_table_id"] = table.id
        context.user_data["order_table_number"] = table.number

        item_name = context.user_data["order_item_name"]
        item_price = context.user_data["order_item_price"]

        keyboard = [
            [
                InlineKeyboardButton("✅ Tasdiqlash", callback_data="confirm_order"),
                InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_order"),
            ]
        ]

        await query.edit_message_text(
            f"📋 *Buyurtma tasdiqlanishi:*\n\n"
            f"🍴 Taom: *{item_name}*\n"
            f"💰 Narxi: *{item_price:,.0f} so'm*\n"
            f"🪑 Stol: *#{table.number}*\n\n"
            f"Buyurtmani tasdiqlaysizmi?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return CONFIRM_ORDER

    finally:
        db.close()


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Buyurtmani tasdiqlash va bazaga saqlash."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel_order":
        await query.edit_message_text("❌ Buyurtma bekor qilindi.")
        context.user_data.clear()
        return ConversationHandler.END

    db = SessionLocal()
    try:
        # Foydalanuvchini topish
        tg_user = update.effective_user
        user = db.query(User).filter(User.telegram_id == tg_user.id).first()

        item_id = context.user_data["order_item_id"]
        table_id = context.user_data["order_table_id"]
        table_number = context.user_data["order_table_number"]
        item_price = context.user_data["order_item_price"]

        # Buyurtma yaratish
        order = Order(
            user_id=user.id,
            table_id=table_id,
            status=OrderStatus.PENDING,
            total_price=item_price,
        )
        db.add(order)
        db.flush()

        # Buyurtma elementi qo'shish
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=item_id,
            quantity=1,
            unit_price=item_price,
        )
        db.add(order_item)

        # Stolni band qilish
        table = db.query(Table).filter(Table.id == table_id).first()
        table.is_available = False

        db.commit()

        await query.edit_message_text(
            f"✅ *Buyurtmangiz qabul qilindi!*\n\n"
            f"📋 Buyurtma raqami: *#{order.id}*\n"
            f"🪑 Stol: *#{table_number}*\n"
            f"💰 Jami: *{item_price:,.0f} so'm*\n\n"
            f"⏳ Holat: *{OrderStatus.PENDING}*\n\n"
            f"Ofitsiant tez orada sizning stolingizga keladi. Rahmat! 🙏",
            parse_mode="Markdown"
        )
    finally:
        db.close()

    context.user_data.clear()
    return ConversationHandler.END


async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Buyurtmani bekor qilish."""
    context.user_data.clear()
    await update.message.reply_text("❌ Buyurtma bekor qilindi.")
    return ConversationHandler.END


async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchining buyurtmalarini ko'rsatish."""
    tg_user = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == tg_user.id).first()
        if not user:
            await update.message.reply_text("Avval /start tugmasini bosing.")
            return

        orders = db.query(Order).filter(Order.user_id == user.id).order_by(
            Order.created_at.desc()
        ).limit(10).all()

        if not orders:
            await update.message.reply_text("📋 Sizda hali buyurtma mavjud emas.")
            return

        text = "📋 *So'nggi buyurtmalaringiz:*\n\n"
        for order in orders:
            table_num = order.table.number if order.table else "—"
            text += (
                f"🔖 *Buyurtma #{order.id}*\n"
                f"   🪑 Stol: #{table_num}\n"
                f"   💰 Jami: {order.total_price:,.0f} so'm\n"
                f"   📊 Holat: {order.status}\n"
                f"   📅 Sana: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            )

        await update.message.reply_text(text, parse_mode="Markdown")
    finally:
        db.close()
