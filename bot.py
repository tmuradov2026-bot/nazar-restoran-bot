import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Tokenni o'qish
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi! Render da Environment Variables ni tekshiring.")

# Holatlar
SELECT_CATEGORY, SELECT_DISH, ENTER_TABLE_NUMBER, ENTER_GUEST_COUNT, CONFIRM_ORDER = range(5)

# Menyu ma'lumotlari
MENU = {
    "?? Salatalar": {
        "Sezar salatasi": {"narx": 45000, "tavsif": "Tovuq go'shti, pomidor, parmesan"},
        "Yunon salatasi": {"narx": 38000, "tavsif": "Bodring, pomidor, zaytun, feta"},
        "Olivye": {"narx": 35000, "tavsif": "An'anaviy yangi yil salatasi"},
    },
    "?? Sho'rvalar": {
        "Mastava": {"narx": 35000, "tavsif": "Go'shtli sho'rva"},
        "Shurpa": {"narx": 40000, "tavsif": "Qo'y go'shti bilan"},
        "Lag'mon sho'rva": {"narx": 38000, "tavsif": "Xitoycha sho'rva"},
    },
    "?? Issiq taomlar": {
        "Osh": {"narx": 50000, "tavsif": "Milliy taomimiz"},
        "Mastava": {"narx": 45000, "tavsif": "Go'shtli guruch"},
        "Kabob": {"narx": 55000, "tavsif": "Mol go'shti kabobi (100g)"},
        "Lag'mon": {"narx": 42000, "tavsif": "Uy lag'moni"},
    },
    "?? Xamir ovqatlar": {
        "Manti": {"narx": 40000, "tavsif": "Bug'da pishirilgan (4 dona)"},
        "Chuchvara": {"narx": 38000, "tavsif": "Go'shtli xamir (8 dona)"},
        "Somsa": {"narx": 15000, "tavsif": "Go'shtli somsa"},
    },
    "?? Shirinliklar": {
        "Paxlava": {"narx": 25000, "tavsif": "Asalli shirinlik (100g)"},
        "Navat": {"narx": 20000, "tavsif": "Milliy shirinlik"},
        "Muzqaymoq": {"narx": 18000, "tavsif": "3 ta shar"},
    },
    "?? Ichimliklar": {
        "Choy (qora/yashil)": {"narx": 10000, "tavsif": "Issiq choy"},
        "Kofe": {"narx": 25000, "tavsif": "Espresso/Cappuccino"},
        "Cola/Fanta": {"narx": 15000, "tavsif": "0.5L"},
        "Suv": {"narx": 8000, "tavsif": "0.5L"},
    }
}

# Buyurtma ma'lumotlari
user_orders = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Botni boshlash"""
    await update.message.reply_text(
        "?? *Nazar Restoraniga xush kelibsiz!*\n\n"
        "?? *Menyu bo'yicha buyurtma berishingiz mumkin.*\n\n"
        "Buyurtma berish uchun /menu ni bosing.",
        parse_mode='Markdown'
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menyuni ko'rsatish"""
    keyboard = []
    for category in MENU.keys():
        keyboard.append([InlineKeyboardButton(category, callback_data=f"cat_{category}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "?? *Kategoriyani tanlang:*\n",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return SELECT_CATEGORY

async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kategoriya tanlanganda"""
    query = update.callback_query
    await query.answer()
    
    category = query.data.replace("cat_", "")
    context.user_data['selected_category'] = category
    
    keyboard = []
    for dish_name, dish_info in MENU[category].items():
        keyboard.append([
            InlineKeyboardButton(
                f"{dish_name} - {dish_info['narx']:,} so'm", 
                callback_data=f"dish_{dish_name}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("?? Orqaga", callback_data="back_to_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"??? *{category}*\n\nTaomni tanlang:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return SELECT_DISH

async def dish_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Taom tanlanganda"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_menu":
        return await menu_command(update, context)
    
    dish_name = query.data.replace("dish_", "")
    context.user_data['selected_dish'] = dish_name
    
    # Kategoriya bo'yicha taomni topish
    dish_info = None
    for category, dishes in MENU.items():
        if dish_name in dishes:
            dish_info = dishes[dish_name]
            break
    
    if not dish_info:
        await query.edit_message_text("? Xatolik! Qaytadan urinib ko'ring.")
        return SELECT_CATEGORY
    
    await query.edit_message_text(
        f"??? *{dish_name}*\n\n"
        f"?? *Tavsif:* {dish_info['tavsif']}\n"
        f"?? *Narx:* {dish_info['narx']:,} so'm\n\n"
        f"?? *Stol raqamingizni kiriting:*",
        parse_mode='Markdown'
    )
    
    return ENTER_TABLE_NUMBER

async def table_number_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stol raqami kiritilganda"""
    table_number = update.message.text
    
    if not table_number.isdigit():
        await update.message.reply_text("? Iltimos, faqat raqam kiriting!")
        return ENTER_TABLE_NUMBER
    
    context.user_data['table_number'] = table_number
    
    await update.message.reply_text(
        "?? *Nechta mehmon?* (raqam kiriting)"
    )
    
    return ENTER_GUEST_COUNT

async def guest_count_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mehmonlar soni kiritilganda"""
    guest_count = update.message.text
    
    if not guest_count.isdigit() or int(guest_count) < 1:
        await update.message.reply_text("? Iltimos, 1 yoki undan katta raqam kiriting!")
        return ENTER_GUEST_COUNT
    
    context.user_data['guest_count'] = guest_count
    
    dish_name = context.user_data.get('selected_dish', 'Noma\'lum')
    table_number = context.user_data.get('table_number', 'Noma\'lum')
    
    # Narxni topish
    dish_price = 0
    for category, dishes in MENU.items():
        if dish_name in dishes:
            dish_price = dishes[dish_name]['narx']
            break
    
    total_price = dish_price * int(guest_count)
    
    await update.message.reply_text(
        f"? *Buyurtmani tasdiqlaysizmi?*\n\n"
        f"??? Taom: {dish_name}\n"
        f"?? Stol: {table_number}\n"
        f"?? Mehmonlar: {guest_count}\n"
        f"?? Jami: {total_price:,} so'm\n\n"
        f"Tasdiqlash uchun /confirm ni bosing,\n"
        f"Bekor qilish uchun /cancel",
        parse_mode='Markdown'
    )
    
    return CONFIRM_ORDER

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buyurtmani tasdiqlash"""
    dish_name = context.user_data.get('selected_dish', 'Noma\'lum')
    table_number = context.user_data.get('table_number', 'Noma\'lum')
    guest_count = context.user_data.get('guest_count', 1)
    
    # Narxni topish
    dish_price = 0
    for category, dishes in MENU.items():
        if dish_name in dishes:
            dish_price = dishes[dish_name]['narx']
            break
    
    total_price = dish_price * int(guest_count)
    
    # Buyurtmani saqlash
    user_id = update.effective_user.id
    if user_id not in user_orders:
        user_orders[user_id] = []
    
    user_orders[user_id].append({
        'dish': dish_name,
        'table': table_number,
        'guests': guest_count,
        'total': total_price
    })
    
    await update.message.reply_text(
        f"? *Buyurtma qabul qilindi!*\n\n"
        f"??? {dish_name}\n"
        f"?? Stol {table_number}\n"
        f"?? {guest_count} mehmon uchun\n"
        f"?? {total_price:,} so'm\n\n"
        f"????? Oshpazlar hozir tayyorlay boshlaydi!\n"
        f"Yangi buyurtma uchun /menu",
        parse_mode='Markdown'
    )
    
    # Ma'lumotlarni tozalash
    context.user_data.clear()
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bekor qilish"""
    context.user_data.clear()
    
    await update.message.reply_text(
        "? Buyurtma bekor qilindi.\n"
        "Yangi buyurtma uchun /menu ni bosing."
    )
    
    return ConversationHandler.END

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mening buyurtmalarim"""
    user_id = update.effective_user.id
    
    if user_id not in user_orders or not user_orders[user_id]:
        await update.message.reply_text("?? Sizda hali buyurtmalar yo'q.\n/menu orqali buyurtma bering.")
        return
    
    orders_text = "?? *Sizning buyurtmalaringiz:*\n\n"
    for i, order in enumerate(user_orders[user_id], 1):
        orders_text += (
            f"{i}. {order['dish']}\n"
            f"   Stol: {order['table']}, Mehmonlar: {order['guests']}\n"
            f"   ?? {order['total']:,} so'm\n\n"
        )
    
    await update.message.reply_text(orders_text, parse_mode='Markdown')

def main():
    """Botni ishga tushirish"""
    # Application yaratish
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('menu', menu_command)],
        states={
            SELECT_CATEGORY: [CallbackQueryHandler(category_selected)],
            SELECT_DISH: [CallbackQueryHandler(dish_selected)],
            ENTER_TABLE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, table_number_entered)],
            ENTER_GUEST_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, guest_count_entered)],
            CONFIRM_ORDER: [CommandHandler('confirm', confirm_order)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Handlerlarni qo'shish
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("myorders", my_orders))
    application.add_handler(conv_handler)
    
    # Botni ishga tushirish
    logger.info("?? Bot ishga tushdi...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()