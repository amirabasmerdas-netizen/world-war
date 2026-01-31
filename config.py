import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # توکن ربات مادر
    MOTHER_BOT_TOKEN = os.getenv('MOTHER_BOT_TOKEN')
    
    # تنظیمات دیتابیس
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///game.db')
    
    # تنظیمات وب‌هوک
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')
    PORT = int(os.getenv('PORT', 8443))
    
    # تنظیمات Render
    RENDER_EXTERNAL_HOSTNAME = os.getenv('RENDER_EXTERNAL_HOSTNAME')
    
    # تنظیمات بازی
    INITIAL_RESOURCES = 10000
    MAX_LOAN_AMOUNT = 5000
    LOAN_COOLDOWN_HOURS = 24
    AI_DECISION_INTERVAL_MIN = (10, 30)  # دقیقه
    
    # کشورهای موجود
    COUNTRIES = [
        "ایران", "آمریکا", "روسیه", "چین", "آلمان", 
        "انگلیس", "فرانسه", "ژاپن", "هند", "ترکیه",
        "کره جنوبی", "برزیل", "کانادا", "استرالیا", "ایتالیا"
    ]
    
    # تنظیمات نیروها
    UNITS = {
        "ground": {
            "تازه نفس": {"emoji": "👶", "price": 50, "attack": 10, "defense": 5},
            "ارپیجی زن": {"emoji": "🚀", "price": 150, "attack": 45, "defense": 20},
            "تک تیرانداز": {"emoji": "⛺", "price": 200, "attack": 70, "defense": 30},
            "سرباز حرفه ای": {"emoji": "🪖", "price": 300, "attack": 100, "defense": 80},
            "توپخانه حرفه ای": {"emoji": "⚽", "price": 500, "attack": 150, "defense": 100},
            "سرباز": {"emoji": "🙍‍♂️", "price": 100, "attack": 30, "defense": 20},
            "توپخانه": {"emoji": "⚽", "price": 250, "attack": 80, "defense": 60}
        },
        "air": {
            "جنگنده سبک": {"emoji": "✈️", "price": 1000, "attack": 200, "defense": 100},
            "جنگنده سنگین": {"emoji": "🛩️", "price": 1500, "attack": 300, "defense": 150},
            "بمب افکن": {"emoji": "💣", "price": 2000, "attack": 400, "defense": 200},
            "بالگرد رزمی": {"emoji": "🚁", "price": 800, "attack": 150, "defense": 100}
        },
        "missiles": {
            "کوتاه‌برد": {"emoji": "🚀", "price": 3000, "attack": 500, "defense": 0},
            "میان‌برد": {"emoji": "🚀", "price": 5000, "attack": 800, "defense": 0},
            "دوربرد": {"emoji": "🚀", "price": 8000, "attack": 1200, "defense": 0},
            "بالستیک": {"emoji": "🚀", "price": 12000, "attack": 1800, "defense": 0}
        },
        "defense": {
            "پدافند معمولی": {"emoji": "📡", "price": 400, "attack": 20, "defense": 100},
            "پدافند حرفه ای": {"emoji": "📡", "price": 800, "attack": 40, "defense": 200},
            "پدافند قدرتمند": {"emoji": "📡", "price": 1200, "attack": 60, "defense": 300}
        },
        "navy": {
            "ناو جنگی": {"emoji": "⛴️", "price": 2000, "attack": 300, "defense": 200},
            "زیردریایی": {"emoji": "💧", "price": 1500, "attack": 250, "defense": 150},
            "کشتی جنگی": {"emoji": "⛵️", "price": 1000, "attack": 200, "defense": 100},
            "قایق جنگی": {"emoji": "🚤", "price": 500, "attack": 100, "defense": 50}
        },
        "cyber": {
            "هکر حرفه ای": {"emoji": "🧑‍💻", "price": 1500, "attack": 200, "defense": 100},
            "تیم هکری": {"emoji": "👥", "price": 3000, "attack": 400, "defense": 200}
        },
        "special": {
            "بمب کوچولو": {"emoji": "💣", "price": 10000, "attack": 1500, "defense": 0},
            "بمب هسته ای": {"emoji": "🍄", "price": 50000, "attack": 5000, "defense": 0}
        },
        "buildings": {
            "کارخانه ساده": {"emoji": "🏚", "price": 2000, "production": 100, "defense": 50},
            "کارخانه معمولی": {"emoji": "🏭", "price": 5000, "production": 250, "defense": 100},
            "کارخانه پیشرفته": {"emoji": "🏢", "price": 10000, "production": 500, "defense": 200},
            "معدن": {"emoji": "🧑‍🔧", "price": 3000, "production": 150, "defense": 80},
            "نیروگاه هسته ای": {"emoji": "⚡️", "price": 8000, "production": 400, "defense": 150}
        }
    }
