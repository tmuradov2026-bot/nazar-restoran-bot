"""
Stol holati handlerlari
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models.database import SessionLocal, Table


async def show_tables(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Barcha stollar holatini ko'rsatish."""
    text, keyboard = _build_table_view()
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def table_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stol tugmasi bosilganda."""
    query = update.callback_query
    await query.answer()

    if query.data == "tbl_show":
        text, keyboard = _build_table_view()
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    elif query.data == "tbl_refresh":
        text, keyboard = _build_table_view()
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


def _build_table_view():
    """Stol ko'rinishini yaratish."""
    db = SessionLocal()
    try:
        tables = db.query(Table).order_by(Table.number).all()
        total = len(tables)
        available = sum(1 for t in tables if t.is_available)

        text = (
            f"🪑 *Stollar holati*\n\n"
            f"✅ Bo'sh: *{available}* ta\n"
            f"❌ Band: *{total - available}* ta\n"
            f"📊 Jami: *{total}* ta\n\n"
        )

        # Jadval ko'rinishida
        row = []
        keyboard = []
        for i, table in enumerate(tables):
            icon = "✅" if table.is_available else "❌"
            status = "Bo'sh" if table.is_available else "Band"
            text += f"{icon} Stol #{table.number} — {status} ({table.capacity} kishi)\n"

            row.append(
                InlineKeyboardButton(
                    f"{icon} #{table.number}",
                    callback_data=f"tbl_detail_{table.id}"
                )
            )
            if len(row) == 3 or i == len(tables) - 1:
                keyboard.append(row)
                row = []

        keyboard.append([
            InlineKeyboardButton("🔄 Yangilash", callback_data="tbl_refresh"),
            InlineKeyboardButton("🔙 Orqaga", callback_data="menu_back"),
        ])

        return text, keyboard
    finally:
        db.close()
