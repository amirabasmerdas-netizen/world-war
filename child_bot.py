from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from database import add_user, get_user, update_user_resources, give_loan

CHILD_BOT_TOKEN = "توکن_ربات_فرزند_اینجا"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user:
        await update.message.reply_text("شما عضو این ربات نیستید. با مالک ربات تماس بگیرید.")
        return
    keyboard = [
        [InlineKeyboardButton("اطلاعات من", callback_data="info")],
        [InlineKeyboardButton("درخواست وام", callback_data="loan")]
    ]
    await update.message.reply_text("پنل کاربر", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "info":
        user = get_user(user_id)
        await query.edit_message_text(f"کشور: {user[2]}\nمنابع: {user[3]}\nوام: {user[4]}")
    elif data == "loan":
        give_loan(user_id, 500)
        await query.edit_message_text("وام ۵۰۰ واحدی به شما تعلق گرفت. لطفاً بازپرداخت را فراموش نکنید!")

app = ApplicationBuilder().token(CHILD_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()
