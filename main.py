import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from config import MOTHER_BOT_TOKEN, OWNER_ID, WEBHOOK_URL
from database import add_user, get_user, update_user_resources

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text(f"شما مالک ربات نیستید. مالک اصلی: @amele55")
        return
    keyboard = [
        [InlineKeyboardButton("اضافه کردن ربات فرزند", callback_data="add_bot")],
        [InlineKeyboardButton("نمایش کاربران", callback_data="show_users")]
    ]
    await update.message.reply_text("پنل مالک ربات مادر", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "add_bot":
        await query.edit_message_text("لطفاً توکن ربات فرزند را ارسال کنید...")
    elif data == "show_users":
        await query.edit_message_text("لیست کاربران فعلی:\n(برای نمونه)")

app = ApplicationBuilder().token(MOTHER_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))

# وب هوک
app.run_webhook(listen="0.0.0.0",
                port=int(os.environ.get("PORT", 8443)),
                url_path=MOTHER_BOT_TOKEN,
                webhook_url=f"{WEBHOOK_URL}/{MOTHER_BOT_TOKEN}")

