"""
Stol holati uchun handler
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.firebase_service import FirebaseService


class TableHandler:
    STATUS_EMOJI = {
        "available": "✅ Bo'sh",
        "occupied":  "🔴 Band",
        "reserved":  "🟡 Bron",
    }

    def __init__(self, firebase: FirebaseService):
        self.db = firebase

    async def show_tables(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Barcha stollarni ko'rsatish"""
        tables = self.db.get_all_tables()
        if not tables:
            text = "😔 Stol ma'lumotlari kiritilmagan."
            if update.message:
                await update.message.reply_text(text)
            else:
                await update.callback_query.edit_message_text(text)
            return

        lines = ["🪑 *Stol holati:*\n"]
        available = 0
        for t in tables:
            status = self.STATUS_EMOJI.get(t.get("status", "available"), "❓")
            seats = t.get("seats", 4)
            lines.append(f"Stol {t.get('number', '?')} ({seats} o'rin): {status}")
            if t.get("status") == "available":
                available += 1
        lines.append(f"\n✅ Bo'sh stollar: {available} ta")

        keyboard = [[InlineKeyboardButton("🔄 Yangilash", callback_data="table_view")]]
        if update.message:
            await update.message.reply_text(
                "\n".join(lines),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await update.callback_query.edit_message_text(
                "\n".join(lines),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )

    async def handle_table_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        if query.data == "table_view":
            await self.show_tables(update, context)
