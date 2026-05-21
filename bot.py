"""
Telegram Restoran Bot - Asosiy fayl
Ishlatish: pip install python-telegram-bot firebase-admin python-dotenv
"""

import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters
)

from handlers.menu_handler import MenuHandler
from handlers.order_handler import OrderHandler
from handlers.table_handler import TableHandler
from handlers.admin_handler import AdminHandler
from services.firebase_service import FirebaseService

load_dotenv()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(MAIN_MENU, VIEW_MENU, ORDER_ITEM, CONFIRM_ORDER,
 TABLE_STATUS, ADMIN_PANEL, ADMIN_MENU_MANAGE,
 ADMIN_ADD_ITEM, ADMIN_EDIT_ITEM, ADMIN_ORDERS) = range(10)


def main():
    """Botni ishga tushirish"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN .env faylida topilmadi!")

    # Firebase ulanish
    firebase = FirebaseService()

    # Handler'larni yaratish
    menu_handler = MenuHandler(firebase)
    order_handler = OrderHandler(firebase)
    table_handler = TableHandler(firebase)
    admin_handler = AdminHandler(firebase)

    # Application yaratish
    app = Application.builder().token(token).build()

    # /start va /help komandalar
    app.add_handler(CommandHandler("start", menu_handler.start))
    app.add_handler(CommandHandler("help", menu_handler.help_command))
    app.add_handler(CommandHandler("admin", admin_handler.admin_panel))

    # Menyu ko'rish
    app.add_handler(CommandHandler("menu", menu_handler.show_menu))

    # Stol holati
    app.add_handler(CommandHandler("tables", table_handler.show_tables))

    # Buyurtmalar
    app.add_handler(CommandHandler("myorders", order_handler.show_user_orders))

    # Callback query handler (inline tugmalar uchun)
    app.add_handler(CallbackQueryHandler(
        menu_handler.handle_menu_callback, pattern="^menu_"
    ))
    app.add_handler(CallbackQueryHandler(
        order_handler.handle_order_callback, pattern="^order_"
    ))
    app.add_handler(CallbackQueryHandler(
        table_handler.handle_table_callback, pattern="^table_"
    ))
    app.add_handler(CallbackQueryHandler(
        admin_handler.handle_admin_callback, pattern="^admin_"
    ))

    # Xato xabarlarni boshqarish
    app.add_error_handler(error_handler)

    logger.info("Bot ishga tushdi!")

    # Webhook yoki polling rejimi
    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        # Production: Webhook rejimi (Cloud Run uchun)
        port = int(os.getenv("PORT", 8080))
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=token,
            webhook_url=f"{webhook_url}/{token}"
        )
    else:
        # Development: Polling rejimi
        app.run_polling(allowed_updates=Update.ALL_TYPES)


async def error_handler(update, context):
    """Xatolarni log qilish"""
    logger.error(f"Update {update} xatolikka sabab bo'ldi: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Xatolik yuz berdi. Iltimos qayta urinib ko'ring."
        )


if __name__ == "__main__":
    main()
