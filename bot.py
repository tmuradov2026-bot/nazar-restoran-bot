import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

SELECT_CATEGORY, SELECT_DISH, ENTER_TABLE_NUMBER, ENTER_GUEST_COUNT, CONFIRM_ORDER = range(5)

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

user_orders = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "?? *Nazar Restoraniga xush kelibsiz!*\n\n"
        "?? *Menyu bo'yicha buyurtma berishingiz mumkin.*\n\n"
        "Buyurtma berish uchun /menu ni bosing.",
        parse_mode='Markdown'
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(cat, callback_data=f"cat_{cat}")] for cat in MENU.keys()]
    keyboard.append([InlineKeyboardButton("?? Buyurtmalarim", callback_data="my_orders_btn")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("?? *Kategoriyani tanlang:*\n", reply_markup=reply_markup, parse_mode='Markdown')
    return SELECT_CATEGORY

async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.replace("cat_", "")
    if category == "my_orders_btn":
        return await my_orders(update, context)
    context.user_data['selected_category'] = category
    keyboard = [[InlineKeyboardButton(f"{name} - {info['narx']:,} so'm", callback_data=f"dish_{name}")] 
                for name, info in MENU[category].items()]
    keyboard.append([InlineKeyboardButton("?? Orqaga", callback_data="back_to_menu")])
    await query.edit_message_text(f"??? *{category}*\n\nTaomni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return SELECT_DISH

async def dish_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "back_to_menu":
        return await menu_command(update, context)
    dish_name = query.data.replace("dish_", "")
    context.user_data['selected_dish'] = dish_name
    dish_info = next((d for cat in MENU.values() for n, d in cat.items() if n == dish_name), None)
    if not dish_info:
        await query.edit_message_text("? Xatolik!")
        return SELECT_CATEGORY
    await query.edit_message_text(
        f"??? *{dish_name}*\n\n?? *Tavsif:* {dish_info['tavsif']}\n?? *Narx:* {dish_info['narx']:,} so'm\n\n?? *Stol raqamingizni kiriting:*",
        parse_mode='Markdown'
    )
    return ENTER_TABLE_NUMBER

async def table_number_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        await update.message.reply_text("? Faqat raqam kiriting!"); return ENTER_TABLE_NUMBER
    context.user_data['table_number'] = update.message.text
    await update.message.reply_text("?? *Nechta mehmon?* (raqam kiriting)"); return ENTER_GUEST_COUNT

async def guest_count_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit() or int(update.message.text) < 1:
        await update.message.reply_text("? 1 yoki undan katta raqam kiriting!"); return ENTER_GUEST_COUNT
    context.user_data['guest_count'] = update.message.text
    dish_name = context.user_data.get('selected_dish', '')
    dish_price = next((d['narx'] for cat in MENU.values() for n, d in cat.items() if n == dish_name), 0)
    total = dish_price * int(update.message.text)
    await update.message.reply_text(
        f"? *Tasdiqlaysizmi?*\n\n??? {dish_name}\n?? Stol: {context.user_data['table_number']}\n?? Mehmonlar: {update.message.text}\n?? Jami: {total:,} so'm\n\nTasdiqlash: /confirm | Bekor qilish: /cancel",
        parse_mode='Markdown'
    )
    return CONFIRM_ORDER

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dish = context.user_data.get('selected_dish', 'Noma\'lum')
    table = context.user_data.get('table_number', '?')
    guests = context.user_data.get('guest_count', 1)
    price = next((d['narx'] for cat in MENU.values() for n, d in cat.items() if n == dish), 0)
    total = price * int(guests)
    uid = update.effective_user.id
    user_orders.setdefault(uid, []).append({'dish': dish, 'table': table, 'guests': guests, 'total': total})
    await update.message.reply_text(f"? *Buyurtma qabul qilindi!*\n\n??? {dish}\n?? Stol {table}\n?? {guests} mehmon\n?? {total:,} so'm\n\n????? Tayyorlanmoqda!\nYangi buyurtma: /menu", parse_mode='Markdown')
    context.user_data.clear(); return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("? Bekor qilindi.\nYangi buyurtma: /menu"); return ConversationHandler.END

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    orders = user_orders.get(uid, [])
    if not orders:
        await (update.message.reply_text if update.message else update.callback_query.edit_message_text)("?? Buyurtmalar yo'q.\n/menu orqali bering.")
        return SELECT_CATEGORY if update.callback_query else ConversationHandler.END
    text = "?? *Sizning buyurtmalaringiz:*\n\n" + "\n".join(f"{i}. {o['dish']} | Stol:{o['table']} | {o['guests']}x | ??{o['total']:,}" for i, o in enumerate(orders, 1))
    await (update.message.reply_text if update.message else update.callback_query.edit_message_text)(text, parse_mode='Markdown')
    return SELECT_CATEGORY if update.callback_query else ConversationHandler.END

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
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
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("myorders", my_orders))
    app.add_handler(conv)
    logger.info("?? Bot ishga tushdi...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    await app.run_until_stopped()

if __name__ == '__main__':
    asyncio.run(main())