"""
Restaurant Telegram Bot - Asosiy kirish nuqtasi
"""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)
from config.settings import BOT_TOKEN
from handlers import menu, order, table, admin, start
from models.database import init_db

# Logging sozlamalari
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Botni ishga tushirish."""
    # Ma'lumotlar bazasini ishga tushirish
    init_db()
    logger.info("Ma'lumotlar bazasi tayyor.")

    # Bot Application yaratish
    application = Application.builder().token(BOT_TOKEN).build()

    # --- Asosiy komandalar ---
    application.add_handler(CommandHandler("start", start.start_command))
    application.add_handler(CommandHandler("help", start.help_command))
    application.add_handler(CommandHandler("menu", menu.show_menu))
    application.add_handler(CommandHandler("tables", table.show_tables))
    application.add_handler(CommandHandler("orders", order.my_orders))

    # --- Admin komandalar ---
    application.add_handler(CommandHandler("admin", admin.admin_panel))
    application.add_handler(CommandHandler("add_item", admin.add_menu_item_start))
    application.add_handler(CommandHandler("manage_orders", admin.manage_orders))

    # --- Buyurtma berish suhbati (ConversationHandler) ---
    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(order.start_order, pattern="^order_")],
        states={
            order.SELECT_TABLE: [
                CallbackQueryHandler(order.select_table, pattern="^table_")
            ],
            order.CONFIRM_ORDER: [
                CallbackQueryHandler(order.confirm_order, pattern="^(confirm|cancel)_order$")
            ],
        },
        fallbacks=[CommandHandler("cancel", order.cancel_order)],
    )
    application.add_handler(order_conv)

    # --- Admin menu qo'shish suhbati ---
    add_item_conv = ConversationHandler(
        entry_points=[CommandHandler("add_item", admin.add_menu_item_start)],
        states={
            admin.ITEM_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.get_item_name)],
            admin.ITEM_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.get_item_price)],
            admin.ITEM_CATEGORY: [CallbackQueryHandler(admin.get_item_category, pattern="^cat_")],
            admin.ITEM_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.get_item_description)],
        },
        fallbacks=[CommandHandler("cancel", admin.cancel_action)],
    )
    application.add_handler(add_item_conv)

    # --- Inline tugmalar ---
    application.add_handler(CallbackQueryHandler(menu.menu_callback, pattern="^menu_"))
    application.add_handler(CallbackQueryHandler(table.table_callback, pattern="^tbl_"))
    application.add_handler(CallbackQueryHandler(admin.admin_callback, pattern="^adm_"))

    # Xatolarni ushlash
    application.add_error_handler(error_handler)

    logger.info("Bot ishga tushdi!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


def error_handler(update: object, context) -> None:
    """Xatolarni log qilish."""
    logger.error(f"Xato yuz berdi: {context.error}", exc_info=context.error)


if __name__ == "__main__":
    main()
