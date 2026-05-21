"""
Buyurtmalar bilan ishlash uchun handler
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.firebase_service import FirebaseService


ORDER_STATUS = {
    "pending":    "⏳ Kutilmoqda",
    "confirmed":  "✅ Tasdiqlandi",
    "preparing":  "👨‍🍳 Tayyorlanmoqda",
    "ready":      "🔔 Tayyor",
    "delivered":  "✔️ Yetkazildi",
    "cancelled":  "❌ Bekor qilindi",
}


class OrderHandler:
    def __init__(self, firebase: FirebaseService):
        self.db = firebase

    async def handle_order_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Buyurtma callback'larini boshqarish"""
        query = update.callback_query
        await query.answer()
        data = query.data
        user = update.effective_user

        if data.startswith("order_add_"):
            item_id = data.replace("order_add_", "")
            await self._add_to_cart(query, context, item_id)

        elif data == "order_cart":
            await self._show_cart(query, context)

        elif data == "order_confirm":
            await self._confirm_order(query, context, user.id)

        elif data == "order_clear":
            context.user_data.pop("cart", None)
            await query.edit_message_text(
                "🛒 Savat tozalandi.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🍽 Menyuga qaytish", callback_data="menu_categories")
                ]])
            )

        elif data == "order_myorders":
            await self.show_user_orders(update, context)

        elif data.startswith("order_detail_"):
            order_id = data.replace("order_detail_", "")
            await self._show_order_detail(query, order_id)

    async def _add_to_cart(self, query, context, item_id: str):
        """Savatga qo'shish"""
        item = self.db.get_menu_item(item_id)
        if not item:
            await query.answer("❌ Mahsulot topilmadi", show_alert=True)
            return

        cart = context.user_data.get("cart", {})
        if item_id in cart:
            cart[item_id]["quantity"] += 1
        else:
            cart[item_id] = {
                "item_id": item_id,
                "name": item["name"],
                "price": item["price"],
                "quantity": 1
            }
        context.user_data["cart"] = cart

        total_items = sum(v["quantity"] for v in cart.values())
        await query.answer(f"✅ {item['name']} savatga qo'shildi! (Jami: {total_items} ta)")

        keyboard = [
            [InlineKeyboardButton(f"🛒 Savatni ko'rish ({total_items} ta)", callback_data="order_cart")],
            [InlineKeyboardButton("➕ Yana qo'shish", callback_data=f"menu_item_{item_id}")],
            [InlineKeyboardButton("🍽 Menyuga qaytish", callback_data="menu_categories")],
        ]
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

    async def _show_cart(self, query, context):
        """Savatni ko'rsatish"""
        cart = context.user_data.get("cart", {})
        if not cart:
            await query.edit_message_text(
                "🛒 Savat bo'sh.\nMenyudan mahsulot tanlang!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🍽 Menyu", callback_data="menu_categories")
                ]])
            )
            return

        lines = ["🛒 *Savatingiz:*\n"]
        total = 0
        for v in cart.values():
            subtotal = v["price"] * v["quantity"]
            total += subtotal
            lines.append(f"• {v['name']} × {v['quantity']} = {subtotal:,} so'm")
        lines.append(f"\n💰 *Jami: {total:,} so'm*")

        keyboard = [
            [InlineKeyboardButton("✅ Buyurtma berish", callback_data="order_confirm")],
            [InlineKeyboardButton("🗑 Savatni tozalash", callback_data="order_clear")],
            [InlineKeyboardButton("🍽 Yana qo'shish", callback_data="menu_categories")],
        ]
        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def _confirm_order(self, query, context, user_id: int):
        """Buyurtmani tasdiqlash va saqlash"""
        cart = context.user_data.get("cart", {})
        if not cart:
            await query.answer("❌ Savat bo'sh!", show_alert=True)
            return

        items = list(cart.values())
        order_id = self.db.create_order(user_id, items)

        context.user_data.pop("cart", None)

        total = sum(i["price"] * i["quantity"] for i in items)
        await query.edit_message_text(
            f"🎉 *Buyurtma qabul qilindi!*\n\n"
            f"📌 Buyurtma raqami: `{order_id[:8]}...`\n"
            f"💰 Jami: *{total:,} so'm*\n"
            f"⏳ Holat: Kutilmoqda\n\n"
            f"Buyurtmangiz tez orada tayyorlanadi! 👨‍🍳",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📋 Buyurtmalarim", callback_data="order_myorders"),
                InlineKeyboardButton("🏠 Bosh menyu", callback_data="menu_back")
            ]]),
            parse_mode="Markdown"
        )

    async def show_user_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Foydalanuvchi buyurtmalarini ko'rsatish"""
        user = update.effective_user
        orders = self.db.get_user_orders(user.id, limit=5)

        if not orders:
            text = "📋 Sizda hech qanday buyurtma yo'q.\nBuyurtma berish uchun /menu bosing."
            if update.message:
                await update.message.reply_text(text)
            else:
                await update.callback_query.edit_message_text(
                    text,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🍽 Menyu", callback_data="menu_categories")
                    ]])
                )
            return

        keyboard = []
        for order in orders:
            status = ORDER_STATUS.get(order["status"], order["status"])
            total = order.get("total_price", 0)
            date = order["created_at"].strftime("%d.%m %H:%M") if hasattr(order.get("created_at"), "strftime") else ""
            keyboard.append([InlineKeyboardButton(
                f"{status} — {total:,} so'm ({date})",
                callback_data=f"order_detail_{order['id']}"
            )])
        keyboard.append([InlineKeyboardButton("🍽 Menyu", callback_data="menu_categories")])

        text = "📋 *So'nggi buyurtmalaringiz:*"
        if update.message:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    async def _show_order_detail(self, query, order_id: str):
        """Buyurtma tafsiloti"""
        order = self.db.get_order(order_id)
        if not order:
            await query.answer("❌ Buyurtma topilmadi", show_alert=True)
            return

        status = ORDER_STATUS.get(order["status"], order["status"])
        lines = [f"📌 *Buyurtma #{order_id[:8]}*\n", f"Holat: {status}\n"]
        for item in order.get("items", []):
            lines.append(f"• {item['name']} × {item['quantity']} = {item['price']*item['quantity']:,} so'm")
        lines.append(f"\n💰 *Jami: {order.get('total_price', 0):,} so'm*")

        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Orqaga", callback_data="order_myorders")
            ]]),
            parse_mode="Markdown"
        )
