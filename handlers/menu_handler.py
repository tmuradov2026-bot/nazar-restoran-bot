"""
Menyu ko'rish uchun handler
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.firebase_service import FirebaseService


class MenuHandler:
    STATUS_EMOJI = {"available": "✅", "occupied": "🔴", "reserved": "🟡"}

    def __init__(self, firebase: FirebaseService):
        self.db = firebase

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Botni boshlash"""
        user = update.effective_user
        self.db.save_user(user.id, user.username or "", user.full_name)

        keyboard = [
            [InlineKeyboardButton("🍽 Menyu", callback_data="menu_categories"),
             InlineKeyboardButton("📋 Buyurtmalarim", callback_data="order_myorders")],
            [InlineKeyboardButton("🪑 Stol holati", callback_data="table_view"),
             InlineKeyboardButton("ℹ️ Yordam", callback_data="menu_help")],
        ]
        await update.message.reply_text(
            f"👋 Xush kelibsiz, {user.first_name}!\n\n"
            "🍴 *Restoran Bot*ga xush kelibsiz!\n"
            "Quyidagi tugmalardan foydalaning:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Yordam xabari"""
        text = (
            "📌 *Bot buyruqlari:*\n\n"
            "/start — Bosh menyu\n"
            "/menu — Menyu ko'rish\n"
            "/tables — Stol holati\n"
            "/myorders — Mening buyurtmalarim\n"
            "/admin — Admin panel (faqat adminlar uchun)\n\n"
            "❓ Savollar uchun: @support"
        )
        await update.message.reply_text(text, parse_mode="Markdown")

    async def show_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Kategoriyalarni ko'rsatish"""
        categories = self.db.get_categories()
        if not categories:
            await update.message.reply_text("😔 Menyu hali to'ldirilmagan.")
            return

        keyboard = []
        for cat in categories:
            keyboard.append([InlineKeyboardButton(
                f"{cat.get('emoji', '🍽')} {cat['name']}",
                callback_data=f"menu_cat_{cat['id']}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="menu_back")])

        text = "📋 *Menyu kategoriyalari:*\nKo'rmoqchi bo'lgan kategoriyani tanlang:"
        if update.message:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    async def handle_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Menyu callback'larini boshqarish"""
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "menu_categories":
            await self.show_menu(update, context)

        elif data.startswith("menu_cat_"):
            category_id = data.replace("menu_cat_", "")
            await self._show_category_items(query, category_id)

        elif data.startswith("menu_item_"):
            item_id = data.replace("menu_item_", "")
            await self._show_item_detail(query, item_id)

        elif data == "menu_back":
            await self.show_menu(update, context)

        elif data == "menu_help":
            await query.edit_message_text(
                "📌 *Yordam:*\n\n"
                "🍽 Menyu — ovqatlarni ko'ring\n"
                "📋 Buyurtmalarim — faol buyurtmalar\n"
                "🪑 Stol holati — bo'sh stollar\n\n"
                "Buyurtma qilish uchun menyudan mahsulot tanlang!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Bosh menyu", callback_data="menu_back")
                ]])
            )

    async def _show_category_items(self, query, category_id: str):
        """Kategoriya mahsulotlarini ko'rsatish"""
        items = self.db.get_menu_items(category_id)
        if not items:
            await query.edit_message_text(
                "😔 Bu kategoriyada mahsulot yo'q.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Kategoriyalar", callback_data="menu_categories")
                ]])
            )
            return

        keyboard = []
        for item in items:
            price = f"{item['price']:,} so'm"
            keyboard.append([InlineKeyboardButton(
                f"{item.get('emoji', '🍽')} {item['name']} — {price}",
                callback_data=f"menu_item_{item['id']}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 Kategoriyalar", callback_data="menu_categories")])

        await query.edit_message_text(
            "📋 *Mahsulotlar:*\nBatafsil ko'rish uchun tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def _show_item_detail(self, query, item_id: str):
        """Bitta mahsulot tafsiloti"""
        item = self.db.get_menu_item(item_id)
        if not item:
            await query.answer("❌ Mahsulot topilmadi", show_alert=True)
            return

        text = (
            f"{item.get('emoji', '🍽')} *{item['name']}*\n\n"
            f"📝 {item.get('description', 'Tavsif mavjud emas')}\n\n"
            f"💰 Narx: *{item['price']:,} so'm*\n"
            f"⏱ Tayyorlanish vaqti: {item.get('prep_time', 15)} daqiqa\n"
            f"{'🌶 Achchiq' if item.get('is_spicy') else ''}"
            f"{'🥗 Vegetarian' if item.get('is_vegetarian') else ''}"
        )
        keyboard = [
            [InlineKeyboardButton("🛒 Buyurtma berish", callback_data=f"order_add_{item_id}")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data=f"menu_cat_{item.get('category_id', '')}")],
        ]
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
