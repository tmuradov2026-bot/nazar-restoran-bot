"""
Start va Help komanda handlerlari
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models.database import SessionLocal, User
from config.settings import RESTAURANT_NAME, RESTAURANT_ADDRESS, RESTAURANT_PHONE, RESTAURANT_WORKING_HOURS


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Botni boshlash - foydalanuvchini ro'yxatdan o'tkazish."""
    user = update.effective_user
    db = SessionLocal()

    try:
        # Foydalanuvchini bazaga saqlash yoki yangilash
        db_user = db.query(User).filter(User.telegram_id == user.id).first()
        if not db_user:
            db_user = User(
                telegram_id=user.id,
                username=user.username,
                full_name=user.full_name or user.first_name,
            )
            db.add(db_user)
            db.commit()
    finally:
        db.close()

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
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"🌟 *{RESTAURANT_NAME}* ga xush kelibsiz!\n\n"
        f"Salom, {user.first_name}! 👋\n\n"
        f"Men sizga quyidagilarda yordam bera olaman:\n"
        f"• 🍽️ Menyuni ko'rish\n"
        f"• 🪑 Stol bandligini tekshirish\n"
        f"• 🛒 Buyurtma berish\n"
        f"• 📋 Buyurtmalaringizni kuzatish\n\n"
        f"Quyidagi tugmalardan birini tanlang:"
    )

    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Yordam ma'lumotlari."""
    help_text = (
        f"🤖 *Bot buyruqlari:*\n\n"
        f"/start - Botni boshlash\n"
        f"/menu - Menyuni ko'rish\n"
        f"/tables - Stol holatini ko'rish\n"
        f"/orders - Buyurtmalarimni ko'rish\n"
        f"/cancel - Amalni bekor qilish\n\n"
        f"📍 *Restoran ma'lumotlari:*\n"
        f"🏠 {RESTAURANT_ADDRESS}\n"
        f"📞 {RESTAURANT_PHONE}\n"
        f"🕐 Ish vaqti: {RESTAURANT_WORKING_HOURS}\n\n"
        f"Savollaringiz bo'lsa, adminlarimizga murojaat qiling."
    )

    await update.message.reply_text(help_text, parse_mode="Markdown")
