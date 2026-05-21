"""
Admin panel uchun handler
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.firebase_service import FirebaseService


ORDER_STATUS_STEPS = ["pending", "confirmed", "preparing", "ready", "delivered"]
ORDER_STATUS_LABELS = {
    "pending":    "⏳ Kutilmoqda",
    "confirmed":  "✅ Tasdiqlandi",
    "preparing":  "👨‍🍳 Tayyorlanmoqda",
    "ready":      "🔔 Tayyor",
    "delivered":  "✔️ Yetkazildi",
    "cancelled":  "❌ Bekor qilindi",
}


class AdminHandler:
    def __init__(self, firebase: FirebaseService):
        self.db = firebase

    def _is_admin(self, update: Update) -> bool:
        return self.db.is_admin(update.effective_user.id)

    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin panel bosh sahifasi"""
        if not self._is_admin(update):
            await update.message.reply_text("❌ Sizda admin huquqi yo'q.")
            return

        keyboard = [
            [InlineKeyboardButton("📋 Buyurtmalar", callback_data="admin_orders"),
             InlineKeyboardButton("🍽 Menyu", callback_data="admin_menu")],
            [InlineKeyboardButton("🪑 Stollar", callback_data="admin_tables"),
             InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
        ]
        await update.message.reply_text(
            "🔑 *Admin Panel*\n\nNimani boshqarmoqchisiz?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def handle_admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin callback'larini boshqarish"""
        query = update.callback_query
        if not self._is_admin(update):
            await query.answer("❌ Admin huquqi yo'q!", show_alert=True)
            return
        await query.answer()
        data = query.data

        if data == "admin_orders":
            await self._show_orders(query)
        elif data.startswith("admin_orders_"):
            status = data.replace("admin_orders_", "")
            await self._show_orders(query, status=status if status != "all" else None)
        elif data.startswith("admin_order_next_"):
            order_id = data.replace("admin_order_next_", "")
            await self._advance_order_status(query, order_id)
        elif data.startswith("admin_order_cancel_"):
            order_id = data.replace("admin_order_cancel_", "")
            self.db.update_order_status(order_id, "cancelled")
            await query.answer("❌ Bekor qilindi", show_alert=True)
            await self._show_orders(query)
        elif data == "admin_menu":
            await self._show_menu_admin(query)
        elif data == "admin_tables":
            await self._show_tables_admin(query)
        elif data.startswith("admin_table_toggle_"):
            table_id = data.replace("admin_table_toggle_", "")
            await self._toggle_table(query, table_id)
        elif data == "admin_stats":
            await self._show_stats(query)
        elif data == "admin_back":
            keyboard = [
                [InlineKeyboardButton("📋 Buyurtmalar", callback_data="admin_orders"),
                 InlineKeyboardButton("🍽 Menyu", callback_data="admin_menu")],
                [InlineKeyboardButton("🪑 Stollar", callback_data="admin_tables"),
                 InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
            ]
            await query.edit_message_text(
                "🔑 *Admin Panel*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
            )

    async def _show_orders(self, query, status: str = None):
        """Buyurtmalar ro'yxati"""
        orders = self.db.get_all_orders(status=status, limit=20)
        if not orders:
            await query.edit_message_text(
                "📋 Buyurtmalar yo'q.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")
                ]])
            )
            return

        filter_keyboard = [
            [InlineKeyboardButton("Barchasi", callback_data="admin_orders_all"),
             InlineKeyboardButton("⏳ Kutmoqda", callback_data="admin_orders_pending"),
             InlineKeyboardButton("👨‍🍳 Tayyorlanmoqda", callback_data="admin_orders_preparing")],
        ]

        order_keyboard = []
        for order in orders[:10]:
            status_label = ORDER_STATUS_LABELS.get(order["status"], order["status"])
            total = order.get("total_price", 0)
            uid = order.get("user_id", "?")
            order_keyboard.append([
                InlineKeyboardButton(
                    f"{status_label} | {total:,} so'm | User:{uid}",
                    callback_data=f"admin_order_next_{order['id']}"
                )
            ])
        order_keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")])

        await query.edit_message_text(
            f"📋 *Buyurtmalar* ({len(orders)} ta)\nTugma bosing → keyingi holat:",
            reply_markup=InlineKeyboardMarkup(filter_keyboard + order_keyboard),
            parse_mode="Markdown"
        )

    async def _advance_order_status(self, query, order_id: str):
        """Buyurtma holatini oldinga siljitish"""
        order = self.db.get_order(order_id)
        if not order:
            await query.answer("❌ Topilmadi", show_alert=True)
            return
        current = order.get("status", "pending")
        if current in ORDER_STATUS_STEPS:
            idx = ORDER_STATUS_STEPS.index(current)
            if idx + 1 < len(ORDER_STATUS_STEPS):
                new_status = ORDER_STATUS_STEPS[idx + 1]
                self.db.update_order_status(order_id, new_status)
                label = ORDER_STATUS_LABELS[new_status]
                await query.answer(f"✅ → {label}", show_alert=True)
            else:
                await query.answer("Bu buyurtma allaqachon yetkazilgan.", show_alert=True)
        await self._show_orders(query)

    async def _show_menu_admin(self, query):
        """Menyu boshqaruvi"""
        items = self.db.get_menu_items()
        text_lines = ["🍽 *Menyu elementlari:*\n"]
        for item in items[:15]:
            text_lines.append(f"• {item['name']} — {item['price']:,} so'm")
        text_lines.append("\n✏️ Menyu qo'shish/o'chirish uchun admin platformasidan foydalaning.")

        await query.edit_message_text(
            "\n".join(text_lines),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")
            ]]),
            parse_mode="Markdown"
        )

    async def _show_tables_admin(self, query):
        """Stol boshqaruvi"""
        tables = self.db.get_all_tables()
        keyboard = []
        for t in tables:
            status = t.get("status", "available")
            emoji = {"available": "✅", "occupied": "🔴", "reserved": "🟡"}.get(status, "❓")
            keyboard.append([InlineKeyboardButton(
                f"{emoji} Stol {t.get('number')} ({t.get('seats', 4)} o'rin) — Bosing: holat o'zgartirish",
                callback_data=f"admin_table_toggle_{t['id']}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")])

        await query.edit_message_text(
            "🪑 *Stol boshqaruvi:*\nToggle uchun stoln bosing:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def _toggle_table(self, query, table_id: str):
        """Stol holatini almashish"""
        table = self.db.get_table(table_id)
        if not table:
            await query.answer("❌ Stol topilmadi", show_alert=True)
            return
        current = table.get("status", "available")
        new_status = "available" if current in ("occupied", "reserved") else "occupied"
        self.db.update_table_status(table_id, new_status)
        label = "✅ Bo'sh" if new_status == "available" else "🔴 Band"
        await query.answer(f"Stol {table.get('number')} → {label}", show_alert=True)
        await self._show_tables_admin(query)

    async def _show_stats(self, query):
        """Statistika"""
        all_orders = self.db.get_all_orders(limit=100)
        total_revenue = sum(o.get("total_price", 0) for o in all_orders)
        pending = sum(1 for o in all_orders if o.get("status") == "pending")
        delivered = sum(1 for o in all_orders if o.get("status") == "delivered")

        await query.edit_message_text(
            f"📊 *Statistika:*\n\n"
            f"📦 Jami buyurtmalar: {len(all_orders)} ta\n"
            f"⏳ Kutilmoqda: {pending} ta\n"
            f"✔️ Yetkazildi: {delivered} ta\n"
            f"💰 Jami daromad: {total_revenue:,} so'm",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")
            ]]),
            parse_mode="Markdown"
        )
