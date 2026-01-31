import random
from datetime import datetime, timedelta
from threading import Thread
import time
from database import DatabaseManager
from battle_engine import BattleEngine
import config

class AIManager:
    def __init__(self, db_manager):
        self.db = db_manager
        self.battle_engine = BattleEngine(db_manager)
        self.running = False
        self.ai_thread = None
    
    def start(self):
        """شروع مدیریت AI"""
        self.running = True
        self.ai_thread = Thread(target=self._ai_loop)
        self.ai_thread.daemon = True
        self.ai_thread.start()
    
    def stop(self):
        """توقف مدیریت AI"""
        self.running = False
        if self.ai_thread:
            self.ai_thread.join()
    
    def _ai_loop(self):
        """حلقه اصلی تصمیم‌گیری AI"""
        while self.running:
            try:
                # تصمیم‌گیری برای هر کشور AI
                session = self.db.get_session()
                ai_countries = session.query(AICountry).all()
                
                for ai_country in ai_countries:
                    self._make_decision(ai_country)
                
                session.close()
                
                # خواب بین 10 تا 30 دقیقه
                sleep_time = random.randint(
                    config.Config.AI_DECISION_INTERVAL_MIN[0] * 60,
                    config.Config.AI_DECISION_INTERVAL_MIN[1] * 60
                )
                time.sleep(sleep_time)
                
            except Exception as e:
                print(f"Error in AI loop: {e}")
                time.sleep(60)  # خواب یک دقیقه در صورت خطا
    
    def _make_decision(self, ai_country):
        """تصمیم‌گیری برای یک کشور AI"""
        session = self.db.get_session()
        
        try:
            personality = ai_country.personality
            
            if personality == 'aggressive':
                decision = self._aggressive_decision(ai_country, session)
            elif personality == 'defensive':
                decision = self._defensive_decision(ai_country, session)
            else:  # diplomatic
                decision = self._diplomatic_decision(ai_country, session)
            
            # اعمال تصمیم
            if decision:
                ai_country.last_action = datetime.utcnow()
                ai_country.strategy_state['last_decision'] = decision
                session.commit()
                
        except Exception as e:
            print(f"Error making AI decision: {e}")
        finally:
            session.close()
    
    def _aggressive_decision(self, ai_country, session):
        """تصمیم‌گیری تهاجمی"""
        decisions = ['attack', 'build_military', 'upgrade_tech']
        decision = random.choice(decisions)
        
        if decision == 'attack':
            # حمله به یک کشور تصادفی
            users = session.query(User).all()
            if users:
                target = random.choice(users)
                self._ai_attack(ai_country, target)
                return f"حمله به {target.country}"
        
        elif decision == 'build_military':
            # ساخت نیروی نظامی
            unit_types = list(config.Config.UNITS.keys())
            unit_type = random.choice(unit_types)
            
            if unit_type in config.Config.UNITS:
                units = list(config.Config.UNITS[unit_type].keys())
                unit = random.choice(units)
                
                # افزایش نیروها
                current_units = ai_country.units or {}
                if unit_type not in current_units:
                    current_units[unit_type] = {}
                if unit not in current_units[unit_type]:
                    current_units[unit_type][unit] = 0
                
                current_units[unit_type][unit] += random.randint(1, 5)
                ai_country.units = current_units
                return f"ساخت {unit}"
        
        return "بررسی وضعیت"
    
    def _defensive_decision(self, ai_country, session):
        """تصمیم‌گیری دفاعی"""
        decisions = ['build_defense', 'upgrade_buildings', 'form_alliance']
        decision = random.choice(decisions)
        
        if decision == 'build_defense':
            # ساخت پدافند
            defense_units = config.Config.UNITS.get('defense', {})
            if defense_units:
                unit = random.choice(list(defense_units.keys()))
                
                current_units = ai_country.units or {}
                if 'defense' not in current_units:
                    current_units['defense'] = {}
                if unit not in current_units['defense']:
                    current_units['defense'][unit] = 0
                
                current_units['defense'][unit] += random.randint(1, 3)
                ai_country.units = current_units
                return f"ساخت پدافند {unit}"
        
        return "تقویت دفاعی"
    
    def _diplomatic_decision(self, ai_country, session):
        """تصمیم‌گیری دیپلماتیک"""
        decisions = ['form_alliance', 'trade', 'research']
        decision = random.choice(decisions)
        
        if decision == 'form_alliance':
            # تلاش برای تشکیل اتحاد
            return "پیشنهاد اتحاد"
        
        elif decision == 'research':
            # تحقیقات
            ai_country.tech_level = min(ai_country.tech_level + 1, 10)
            return "ارتقاء تکنولوژی"
        
        return "مذاکره"
    
    def _ai_attack(self, ai_country, target_user):
        """حمله AI به کاربر"""
        # انتخاب نیروهای حمله‌کننده
        attacker_units = {}
        if ai_country.units:
            for unit_type, units in ai_country.units.items():
                if units:
                    unit_name = random.choice(list(units.keys()))
                    count = min(units[unit_name], random.randint(1, 10))
                    if count > 0:
                        if unit_type not in attacker_units:
                            attacker_units[unit_type] = {}
                        attacker_units[unit_type][unit_name] = count
        
        if not attacker_units:
            return
        
        # محاسبه جنگ
        result = self.battle_engine.calculate_battle(
            attacker=ai_country,
            defender=target_user,
            attacker_units=attacker_units
        )
        
        # ذخیره نتیجه جنگ
        self.battle_engine.save_battle(
            attacker_id=ai_country.id,
            defender_id=target_user.id,
            attacker_type='ai',
            defender_type='user',
            units_used=attacker_units,
            result=result['result'],
            attacker_losses=result['attacker_losses'],
            defender_losses=result['defender_losses'],
            resources_stolen=result['resources_stolen']
        )
