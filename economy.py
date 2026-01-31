from datetime import datetime, timedelta
from database import DatabaseManager
import config

class EconomyManager:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def calculate_daily_production(self, user):
        """محاسبه تولید روزانه"""
        daily_production = 0
        
        # تولید از کارخانه‌ها
        for building, count in user.buildings.items():
            if "کارخانه" in building:
                base_production = 50  # تولید پایه
                if "پیشرفته" in building:
                    base_production = 100
                elif "حرفه ای" in building:
                    base_production = 150
                
                daily_production += count * base_production
        
        # تولید از معادن
        for building, count in user.buildings.items():
            if "معدن" in building:
                base_production = 30
                if "حرفه ای" in building:
                    base_production = 60
                elif "پیشرفته" in building:
                    base_production = 90
                
                daily_production += count * base_production
        
        # تولید از نیروگاه‌ها
        for building, count in user.buildings.items():
            if "نیروگاه" in building:
                base_production = 40
                if "پیشرفته" in building:
                    base_production = 80
                elif "حرفه ای" in building:
                    base_production = 120
                elif "هسته ای" in building:
                    base_production = 200
                
                daily_production += count * base_production
        
        # تولید از نفت‌کش‌ها
        for building, count in user.buildings.items():
            if "نفت کش" in building:
                base_production = 25
                if "حرفه ای" in building:
                    base_production = 50
                
                daily_production += count * base_production
        
        # اعمال بونوس تکنولوژی
        tech_bonus = 1 + (user.tech_level * 0.1)  # 10% افزایش به ازای هر سطح
        daily_production *= tech_bonus
        
        # اعمال اثر روحیه
        morale_effect = user.morale / 100
        daily_production *= morale_effect
        
        return int(daily_production)
    
    def process_loan(self, user, amount):
        """پردازش وام"""
        # بررسی cooldown
        if user.last_loan_time:
            time_since_last = datetime.utcnow() - user.last_loan_time
            if time_since_last < timedelta(hours=config.Config.LOAN_COOLDOWN_HOURS):
                return False, f"شما باید {config.Config.LOAN_COOLDOWN_HOURS} ساعت صبر کنید"
        
        # بررسی محدودیت مقدار
        if amount > config.Config.MAX_LOAN_AMOUNT:
            return False, f"حداکثر وام {config.Config.MAX_LOAN_AMOUNT} است"
        
        # اعطای وام
        session = self.db.get_session()
        try:
            user.money += amount
            user.loan_amount += amount
            user.last_loan_time = datetime.utcnow()
            session.commit()
            return True, f"وام {amount} واحد دریافت شد"
        except Exception as e:
            session.rollback()
            return False, "خطا در پردازش وام"
        finally:
            session.close()
    
    def repay_loan(self, user, amount):
        """بازپرداخت وام"""
        if amount > user.loan_amount:
            return False, "مبلغ بیشتر از وام شماست"
        
        if amount > user.money:
            return False, "پول کافی ندارید"
        
        session = self.db.get_session()
        try:
            user.money -= amount
            user.loan_amount -= amount
            session.commit()
            return True, f"مبلغ {amount} بازپرداخت شد"
        except Exception as e:
            session.rollback()
            return False, "خطا در بازپرداخت"
        finally:
            session.close()
    
    def update_user_resources(self, user_id, bot_id):
        """به‌روزرسانی منابع کاربر"""
        user = self.db.get_user(user_id, bot_id)
        if not user:
            return
        
        # محاسبه تولید از آخرین به‌روزرسانی
        now = datetime.utcnow()
        if user.last_active:
            hours_passed = (now - user.last_active).total_seconds() / 3600
            
            # تولید منابع
            daily_production = self.calculate_daily_production(user)
            hourly_production = daily_production / 24
            production = int(hourly_production * hours_passed)
            
            # به‌روزرسانی پول
            user.money += production
            user.last_active = now
            
            # ذخیره تغییرات
            self.db.update_user(user_id, {
                'money': user.money,
                'last_active': user.last_active
            })
    
    def can_afford(self, user, cost):
        """بررسی توانایی مالی"""
        return user.money >= cost
    
    def deduct_money(self, user_id, bot_id, amount):
        """کسر پول"""
        user = self.db.get_user(user_id, bot_id)
        if not user:
            return False
        
        if user.money < amount:
            return False
        
        session = self.db.get_session()
        try:
            user.money -= amount
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()
