from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler
)
from database import DatabaseManager
from keyboards import Keyboards
from economy import EconomyManager
from battle_engine import BattleEngine
import config
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# حالت‌های مکالمه
SELECTING_COUNTRY, ADDING_USER, REMOVING_USER, ATTACK_TARGET, LOAN_AMOUNT = range(5)

class ChildBot:
    def __init__(self, bot_token, bot_id):
        self.bot_token = bot_token
        self.bot_id = bot_id
        self.db = DatabaseManager()
        self.economy = EconomyManager(self.db)
        self.battle_engine = BattleEngine(self.db)
        self.application = None
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع ربات فرزند"""
        user = update.effective_user
        user_id = user.id
        
        # بررسی وجود کاربر
        db_user = self.db.get_user(user_id, self.bot_id)
        
        if not db_user:
            # کاربر جدید
            await update.message.reply_text(
                "👋 سلام! به ربات استراتژیک خوش آمدید.\n"
                "لطفاً کشور خود را انتخاب کنید:",
                reply_markup=Keyboards.country_selection_keyboard()
            )
            return SELECTING_COUNTRY
        else:
            # کاربر موجود
            is_owner = db_user.is_admin or db_user.user_id == context.bot_data.get('owner_id')
            await update.message.reply_text(
                f"🌍 کشور شما: {db_user.country}\n"
                f"💰 دارایی: {int(db_user.money)} واحد\n"
                f"🎯 سطح تکنولوژی: {db_user.tech_level}\n"
                f"😊 روحیه: {db_user.morale:.1f}%",
                reply_markup=Keyboards.main_menu(is_owner)
            )
            return ConversationHandler.END
    
    async def select_country(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انتخاب کشور"""
        country = update.message.text
        
        if country == "⬅️ بازگشت":
            await update.message.reply_text(
                "عملیات لغو شد.",
                reply_markup=ReplyKeyboardRemove()
            )
            return ConversationHandler.END
        
        if country not in config.Config.COUNTRIES:
            await update.message.reply_text(
                "لطفاً یک کشور معتبر انتخاب کنید:",
                reply_markup=Keyboards.country_selection_keyboard()
            )
            return SELECTING_COUNTRY
        
        # ذخیره کاربر
        user = update.effective_user
        user_data = {
            'user_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'country': country,
            'bot_id': self.bot_id,
            'money': config.Config.INITIAL_RESOURCES
        }
        
        self.db.add_user(user_data)
        
        await update.message.reply_text(
            f"✅ کشور {country} با موفقیت انتخاب شد!\n"
            f"شروع با {config.Config.INITIAL_RESOURCES} واحد پول.",
            reply_markup=Keyboards.main_menu(False)
        )
        return ConversationHandler.END
    
    async def ground_forces(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نیروی زمینی"""
        user_id = update.effective_user.id
        user = self.db.get_user(user_id, self.bot_id)
        
        if not user:
            await update.message.reply_text("لطفاً ابتدا با دستور /start شروع کنید.")
            return
        
        units = user.units.get('ground', {})
        message = "🪖 نیروی زمینی شما:\n\n"
        
        for unit_name, count in units.items():
            message += f"{unit_name}: {count} نفر\n"
        
        await update.message.reply_text(
            message,
            reply_markup=Keyboards.ground_forces_menu()
        )
    
    async def air_forces(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نیروی هوایی"""
        user_id = update.effective_user.id
        user = self.db.get_user(user_id, self.bot_id)
        
        if not user:
            await update.message.reply_text("لطفاً ابتدا با دستور /start شروع کنید.")
            return
        
        units = user.units.get('air', {})
        missiles = user.units.get('missiles', {})
        
        message = "✈️ نیروی هوایی شما:\n\n"
        message += "هواپیماها:\n"
        for unit_name, count in units.items():
            message += f"{unit_name}: {count} فروند\n"
        
        message += "\nموشک‌ها:\n"
        for missile_name, count in missiles.items():
            message += f"{missile_name}: {count} عدد\n"
        
        await update.message.reply_text(
            message,
            reply_markup=Keyboards.air_forces_menu()
        )
    
    async def economy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بخش اقتصادی"""
        user_id = update.effective_user.id
        user = self.db.get_user(user_id, self.bot_id)
        
        if not user:
            await update.message.reply_text("لطفاً ابتدا با دستور /start شروع کنید.")
            return
        
        # محاسبه تولید فعلی
        daily_production = self.economy.calculate_daily_production(user)
        
        message = (
            f"🏭 وضعیت اقتصادی:\n\n"
            f"💰 پول: {int(user.money)} واحد\n"
            f"📈 تولید روزانه: {daily_production} واحد\n"
            f"💸 وام باقی‌مانده: {user.loan_amount} واحد\n"
            f"🏢 تعداد سازه‌ها: {sum(user.buildings.values())}\n"
            f"⚡️ مصرف انرژی: {len(user.buildings) * 10}"
        )
        
        await update.message.reply_text(
            message,
            reply_markup=Keyboards.economy_menu()
        )
    
    async def loan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دریافت وام"""
        user_id = update.effective_user.id
        user = self.db.get_user(user_id, self.bot_id)
        
        if not user:
            await update.message.reply_text("لطفاً ابتدا با دستور /start شروع کنید.")
            return
        
        await update.message.reply_text(
            f"💰 دریافت وام\n\n"
            f"حداکثر وام: {config.Config.MAX_LOAN_AMOUNT} واحد\n"
            f"وام فعلی: {user.loan_amount} واحد\n\n"
            f"مبلغ وام را وارد کنید:",
            reply_markup=Keyboards.numeric_keyboard()
        )
        return LOAN_AMOUNT
    
    async def process_loan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش وام"""
        try:
            amount = int(update.message.text)
        except ValueError:
            await update.message.reply_text(
                "لطفاً یک عدد وارد کنید:",
                reply_markup=Keyboards.numeric_keyboard()
            )
            return LOAN_AMOUNT
        
        user_id = update.effective_user.id
        user = self.db.get_user(user_id, self.bot_id)
        
        success, message = self.economy.process_loan(user, amount)
        
        await update.message.reply_text(
            message,
            reply_markup=Keyboards.main_menu(user.is_admin)
        )
        return ConversationHandler.END
    
    async def owner_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پنل مالک"""
        user_id = update.effective_user.id
        user = self.db.get_user(user_id, self.bot_id)
        
        # بررسی مالک بودن
        if not user or not user.is_admin:
            await update.message.reply_text("دسترسی denied.")
            return
        
        await update.message.reply_text(
            "👑 پنل مالک ربات\n\n"
            "گزینه مورد نظر را انتخاب کنید:",
            reply_markup=Keyboards.owner_panel()
        )
    
    async def add_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """افزودن کاربر"""
        await update.message.reply_text(
            "لطفاً آیدی عددی کاربر را وارد کنید:",
            reply_markup=ReplyKeyboardRemove()
        )
        return ADDING_USER
    
    async def process_add_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش افزودن کاربر"""
        try:
            new_user_id = int(update.message.text)
        except ValueError:
            await update.message.reply_text("آیدی باید عددی باشد. دوباره وارد کنید:")
            return ADDING_USER
        
        # بررسی وجود کاربر
        existing_user = self.db.get_user(new_user_id, self.bot_id)
        if existing_user:
            await update.message.reply_text(
                "این کاربر قبلاً اضافه شده است.",
                reply_markup=Keyboards.owner_panel()
            )
            return ConversationHandler.END
        
        # ذخیره آیدی در context
        context.user_data['new_user_id'] = new_user_id
        
        await update.message.reply_text(
            "کشور کاربر را انتخاب کنید:",
            reply_markup=Keyboards.country_selection_keyboard()
        )
        return SELECTING_COUNTRY
    
    async def assign_country_to_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انتساب کشور به کاربر جدید"""
        country = update.message.text
        
        if country not in config.Config.COUNTRIES:
            await update.message.reply_text(
                "لطفاً یک کشور معتبر انتخاب کنید:",
                reply_markup=Keyboards.country_selection_keyboard()
            )
            return SELECTING_COUNTRY
        
        new_user_id = context.user_data.get('new_user_id')
        
        if new_user_id:
            # ایجاد کاربر
            user_data = {
                'user_id': new_user_id,
                'country': country,
                'bot_id': self.bot_id,
                'money': config.Config.INITIAL_RESOURCES,
                'is_admin': False
            }
            
            self.db.add_user(user_data)
            
            await update.message.reply_text(
                f"✅ کاربر با آیدی {new_user_id} و کشور {country} اضافه شد.",
                reply_markup=Keyboards.owner_panel()
            )
        
        return ConversationHandler.END
    
    async def user_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """اطلاعات کاربر"""
        user_id = update.effective_user.id
        user = self.db.get_user(user_id, self.bot_id)
        
        if not user:
            await update.message.reply_text("لطفاً ابتدا با دستور /start شروع کنید.")
            return
        
        # محاسبه قدرت کلی
        total_power = 0
        for unit_type, units in user.units.items():
            for unit_name, count in units.items():
                if unit_type in config.Config.UNITS:
                    if unit_name in config.Config.UNITS[unit_type]:
                        unit_info = config.Config.UNITS[unit_type][unit_name]
                        total_power += count * (unit_info.get('attack', 0) + unit_info.get('defense', 0))
        
        message = (
            f"👤 اطلاعات کاربر:\n\n"
            f"🏳️ کشور: {user.country}\n"
            f"💰 پول: {int(user.money)} واحد\n"
            f"⚡️ قدرت کلی: {total_power}\n"
            f"🧠 سطح تکنولوژی: {user.tech_level}\n"
            f"😊 روحیه: {user.morale:.1f}%\n"
            f"📅 عضویت از: {user.created_at.strftime('%Y-%m-%d')}\n"
            f"🏗 سازه‌ها: {sum(user.buildings.values())} عدد\n"
            f"🪖 کل نیروها: {sum(sum(v.values()) for v in user.units.values())} نفر"
        )
        
        await update.message.reply_text(message)
    
    async def guide(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """راهنمای بازی"""
        guide_text = """
📘 راهنمای بازی استراتژیک:

🎮 هدف بازی:
کشور خود را مدیریت کنید، نیرو بسازید، اقتصاد را توسعه دهید و بر سایر کشورها پیروز شوید.

🔧 بخش‌های اصلی:

🪖 نیروی زمینی: سربازان و توپخانه
✈️ نیروی هوایی: هواپیماها و موشک‌ها
📡 پدافندها: دفاع در برابر حملات
🚢 نیروی دریایی: کشتی‌های جنگی
💻 نیروی سایبری: هکرها و تیم‌های هکری
💣 تسلیحات ویژه: بمب‌های هسته‌ای

🏭 اقتصاد:
کارخانه‌ها، معادن، نیروگاه‌ها و نفت‌کش‌ها پول تولید می‌کنند.

⚔️ جنگ:
می‌توانید به کشورهای دیگر یا AI حمله کنید.
نتایج جنگ بستگی به نیروها، تکنولوژی و شانس دارد.

💰 وام:
یک بار در روز می‌توانید وام دریافت کنید.
وام باید بازپرداخت شود.

🏛 اتحادها:
با دیگران متحد شوید تا قدرت بیشتری داشته باشید.

👑 مالک ربات:
اگر مالک هستید، می‌توانید کاربران جدید اضافه کنید.
        """
        
        await update.message.reply_text(guide_text)
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """لغو عملیات"""
        await update.message.reply_text(
            "عملیات لغو شد.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    def run(self):
        """اجرای ربات فرزند"""
        # ساخت اپلیکیشن
        self.application = Application.builder().token(self.bot_token).build()
        
        # اضافه کردن مالک به context
        session = self.db.get_session()
        bot = session.query(ChildBot).filter(ChildBot.id == self.bot_id).first()
        if bot:
            self.application.bot_data['owner_id'] = bot.owner_id
        session.close()
        
        # Conversation Handler برای افزودن کاربر
        add_user_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^➕ افزودن کاربر$"), self.add_user)],
            states={
                ADDING_USER: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_add_user)
                ],
                SELECTING_COUNTRY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.assign_country_to_user)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )
        
        # Conversation Handler برای وام
        loan_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^💰 وام$"), self.loan)],
            states={
                LOAN_AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_loan)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )
        
        # اضافه کردن handlers
        self.application.add_handler(ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                SELECTING_COUNTRY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.select_country)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        ))
        
        self.application.add_handler(add_user_conv)
        self.application.add_handler(loan_conv)
        
        # سایر handlers
        self.application.add_handler(MessageHandler(filters.Regex("^🪖 نیروی زمینی$"), self.ground_forces))
        self.application.add_handler(MessageHandler(filters.Regex("^✈️ نیروی هوایی$"), self.air_forces))
        self.application.add_handler(MessageHandler(filters.Regex("^🏭 بخش اقتصادی$"), self.economy))
        self.application.add_handler(MessageHandler(filters.Regex("^👑 پنل مالک$"), self.owner_panel))
        self.application.add_handler(MessageHandler(filters.Regex("^👤 اطلاعات من$"), self.user_info))
        self.application.add_handler(MessageHandler(filters.Regex("^📘 راهنمای بازی$"), self.guide))
        
        # Handler برای دکمه بازگشت
        self.application.add_handler(MessageHandler(filters.Regex("^⬅️ بازگشت"), self.start))
        
        # اجرای ربات
        self.application.run_polling()
