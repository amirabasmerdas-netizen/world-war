from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, ConversationHandler
)
from database import DatabaseManager
from keyboards import Keyboards
import config
import logging
import asyncio

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# حالت‌های مکالمه
WAITING_FOR_TOKEN, WAITING_FOR_OWNER_ID = range(2)

class MotherBot:
    def __init__(self):
        self.db = DatabaseManager()
        self.db.init_db()
        self.application = None
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع ربات مادر"""
        user = update.effective_user
        
        await update.message.reply_text(
            f"👑 سلام {user.first_name}!\n"
            f"به ربات مادر استراتژیک خوش آمدید.\n\n"
            "گزینه مورد نظر را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup([
                ["➕ ثبت ربات جدید", "📋 لیست ربات‌ها"],
                ["🔄 فعال/غیرفعال کردن ربات", "🗑 حذف ربات"],
                ["📊 آمار کلی"]
            ], resize_keyboard=True)
        )
    
    async def register_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ثبت ربات جدید"""
        await update.message.reply_text(
            "لطفاً توکن ربات فرزند را وارد کنید:",
            reply_markup=ReplyKeyboardRemove()
        )
        return WAITING_FOR_TOKEN
    
    async def receive_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دریافت توکن"""
        token = update.message.text
        
        # اعتبارسنجی اولیه توکن
        if not token.startswith('') or ':' not in token:
            await update.message.reply_text(
                "توکن نامعتبر است. لطفاً توکن صحیح را وارد کنید:"
            )
            return WAITING_FOR_TOKEN
        
        # ذخیره توکن در context
        context.user_data['bot_token'] = token
        
        await update.message.reply_text(
            "✅ توکن دریافت شد.\n"
            "لطفاً آیدی عددی مالک ربات را وارد کنید:"
        )
        return WAITING_FOR_OWNER_ID
    
    async def receive_owner_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دریافت آیدی مالک"""
        try:
            owner_id = int(update.message.text)
        except ValueError:
            await update.message.reply_text(
                "آیدی باید عددی باشد. لطفاً دوباره وارد کنید:"
            )
            return WAITING_FOR_OWNER_ID
        
        token = context.user_data.get('bot_token')
        
        if token:
            # ثبت ربات در دیتابیس
            # در اینجا mother_bot_id را 1 در نظر می‌گیریم (ربات مادر اصلی)
            new_bot = self.db.add_child_bot(token, owner_id, 1)
            
            if new_bot:
                await update.message.reply_text(
                    f"✅ ربات با موفقیت ثبت شد!\n\n"
                    f"🔑 توکن: {token[:15]}...\n"
                    f"👑 مالک: {owner_id}\n"
                    f"📅 تاریخ ایجاد: {new_bot.created_at}\n\n"
                    f"ربات فرزند اکنون می‌تواند اجرا شود.",
                    reply_markup=ReplyKeyboardMarkup([
                        ["➕ ثبت ربات جدید", "📋 لیست ربات‌ها"],
                        ["🔄 فعال/غیرفعال کردن ربات", "🗑 حذف ربات"],
                        ["📊 آمار کلی"]
                    ], resize_keyboard=True)
                )
            else:
                await update.message.reply_text(
                    "خطا در ثبت ربات. لطفاً دوباره تلاش کنید.",
                    reply_markup=ReplyKeyboardMarkup([
                        ["➕ ثبت ربات جدید", "📋 لیست ربات‌ها"],
                        ["🔄 فعال/غیرفعال کردن ربات", "🗑 حذف ربات"],
                        ["📊 آمار کلی"]
                    ], resize_keyboard=True)
                )
        
        return ConversationHandler.END
    
    async def list_bots(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش لیست ربات‌ها"""
        user = update.effective_user
        bots = self.db.get_child_bots(user.id)
        
        if not bots:
            await update.message.reply_text("شما هیچ رباتی ثبت نکرده‌اید.")
            return
        
        message = "📋 لیست ربات‌های شما:\n\n"
        
        for i, bot in enumerate(bots, 1):
            status_emoji = "✅" if bot.status == 'active' else "❌"
            message += (
                f"{i}. ربات #{bot.id}\n"
                f"   وضعیت: {status_emoji} {bot.status}\n"
                f"   تاریخ ایجاد: {bot.created_at.strftime('%Y-%m-%d')}\n"
                f"   توکن: {bot.bot_token[:10]}...\n\n"
            )
        
        await update.message.reply_text(message)
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """لغو عملیات"""
        await update.message.reply_text(
            "عملیات لغو شد.",
            reply_markup=ReplyKeyboardMarkup([
                ["➕ ثبت ربات جدید", "📋 لیست ربات‌ها"],
                ["🔄 فعال/غیرفعال کردن ربات", "🗑 حذف ربات"],
                ["📊 آمار کلی"]
            ], resize_keyboard=True)
        )
        return ConversationHandler.END
    
    def run(self):
        """اجرای ربات مادر"""
        # ساخت اپلیکیشن
        self.application = Application.builder().token(config.Config.MOTHER_BOT_TOKEN).build()
        
        # Conversation Handler برای ثبت ربات
        conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^➕ ثبت ربات جدید$"), self.register_bot)],
            states={
                WAITING_FOR_TOKEN: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_token)
                ],
                WAITING_FOR_OWNER_ID: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_owner_id)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )
        
        # اضافه کردن handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(conv_handler)
        self.application.add_handler(MessageHandler(filters.Regex("^📋 لیست ربات‌ها$"), self.list_bots))
        
        # اجرای ربات
        self.application.run_polling()

if __name__ == "__main__":
    bot = MotherBot()
    bot.run()
