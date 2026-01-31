from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

class Keyboards:
    @staticmethod
    def main_menu(is_owner=False):
        """منوی اصلی"""
        keyboard = [
            ["🪖 نیروی زمینی", "✈️ نیروی هوایی"],
            ["📡 پدافندها", "🚢 نیروی دریایی"],
            ["💻 نیروی سایبری", "💣 تسلیحات ویژه"],
            ["🏭 بخش اقتصادی", "🏢 سازه‌ها"],
            ["🧠 تکنولوژی", "⚔️ حمله"],
            ["🏛 اتحادها", "👤 اطلاعات من"],
            ["📘 راهنمای بازی", "🛒 فروشگاه"],
            ["⚙️ تنظیمات", "💰 وام"]
        ]
        
        if is_owner:
            keyboard.append(["👑 پنل مالک"])
            
        keyboard.append(["⬅️ بازگشت به منوی اصلی"])
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def owner_panel():
        """پنل مالک ربات"""
        keyboard = [
            ["➕ افزودن کاربر", "👥 لیست کاربران"],
            ["🏳️ انتخاب کشور کاربر", "🗑 حذف کاربر"],
            ["📊 آمار ربات", "⬅️ بازگشت"]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def ground_forces_menu():
        """منوی نیروی زمینی"""
        keyboard = [
            ["👶 تازه نفس", "🚀 ارپیجی زن"],
            ["⛺ تک تیرانداز", "🪖 سرباز حرفه ای"],
            ["⚽ توپخانه حرفه ای", "🙍‍♂️ سرباز"],
            ["⚽ توپخانه", "📊 وضعیت نیروها"],
            ["⬅️ بازگشت"]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def air_forces_menu():
        """منوی نیروی هوایی"""
        keyboard = [
            ["✈️ جنگنده سبک", "🛩️ جنگنده سنگین"],
            ["💣 بمب افکن", "🚁 بالگرد رزمی"],
            ["🚀 موشک کوتاه‌برد", "🚀 موشک میان‌برد"],
            ["🚀 موشک دوربرد", "🚀 موشک بالستیک"],
            ["📊 وضعیت نیروها", "⬅️ بازگشت"]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def attack_menu():
        """منوی حمله"""
        keyboard = [
            ["🎯 حمله به کاربر", "🤖 حمله به AI"],
            ["📊 وضعیت جنگ‌ها", "⬅️ بازگشت"]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def economy_menu():
        """منوی اقتصادی"""
        keyboard = [
            ["🏭 ساخت کارخانه", "⛏️ ساخت معدن"],
            ["⚡️ ساخت نیروگاه", "🛢️ ساخت نفت‌کش"],
            ["💰 وضعیت منابع", "⬅️ بازگشت"]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def building_menu():
        """منوی سازه‌ها"""
        keyboard = [
            ["🏥 بیمارستان", "🤰 زایشگاه"],
            ["🏞 پارک", "📊 وضعیت سازه‌ها"],
            ["⬅️ بازگشت"]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def settings_menu():
        """منوی تنظیمات"""
        keyboard = [
            ["🔔 تنظیم نوتیفیکیشن", "🌐 تغییر زبان"],
            ["👤 تغییر نام", "⬅️ بازگشت"]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def shop_menu():
        """منوی فروشگاه"""
        keyboard = [
            ["💎 خرید الماس", "⚡ خرید انرژی"],
            ["🛡 خرید پدافند", "⬅️ بازگشت"]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def yes_no_keyboard():
        """کیبورد بله/خیر"""
        keyboard = [
            ["✅ بله", "❌ خیر"]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    @staticmethod
    def country_selection_keyboard():
        """کیبورد انتخاب کشور"""
        from config import Config
        
        keyboard = []
        row = []
        for i, country in enumerate(Config.COUNTRIES, 1):
            row.append(KeyboardButton(country))
            if i % 3 == 0:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append(["⬅️ بازگشت"])
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    @staticmethod
    def numeric_keyboard():
        """کیبورد عددی"""
        keyboard = [
            ["1", "2", "3"],
            ["4", "5", "6"],
            ["7", "8", "9"],
            ["0", "⬅️ بازگشت"]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
