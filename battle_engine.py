import random
from datetime import datetime
from database import DatabaseManager
from models import Battle
import config

class BattleEngine:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def calculate_battle(self, attacker, defender, attacker_units, defender_units=None):
        """محاسبه نتیجه جنگ"""
        
        # محاسبه قدرت حمله
        attacker_power = self.calculate_power(attacker, attacker_units, "attack")
        
        # اگر مدافع نیروهای مشخصی فرستاده
        if defender_units:
            defender_power = self.calculate_power(defender, defender_units, "defense")
        else:
            # استفاده از تمام نیروهای دفاعی
            defender_power = self.calculate_power(defender, defender.units, "defense")
        
        # اعمال شانس (10-20%)
        attacker_luck = random.uniform(0.9, 1.2)
        defender_luck = random.uniform(0.9, 1.2)
        
        attacker_final = attacker_power * attacker_luck * (attacker.morale / 100)
        defender_final = defender_power * defender_luck * (defender.morale / 100)
        
        # محاسبه نتیجه
        result = ""
        attacker_losses = {}
        defender_losses = {}
        resources_stolen = {}
        
        if attacker_final > defender_final * 1.5:
            # پیروزی قاطع
            result = "win"
            attacker_loss_rate = 0.1  # 10% تلفات
            defender_loss_rate = 0.4  # 40% تلفات
            
            # سرقت منابع
            if isinstance(defender, dict) and 'money' in defender:
                steal_amount = defender['money'] * 0.3  # 30% پول
                resources_stolen = {"money": steal_amount}
        
        elif attacker_final > defender_final:
            # پیروزی جزئی
            result = "minor_win"
            attacker_loss_rate = 0.25  # 25% تلفات
            defender_loss_rate = 0.3   # 30% تلفات
            
            if isinstance(defender, dict) and 'money' in defender:
                steal_amount = defender['money'] * 0.15  # 15% پول
                resources_stolen = {"money": steal_amount}
        
        elif attacker_final < defender_final * 0.7:
            # شکست سنگین
            result = "heavy_loss"
            attacker_loss_rate = 0.4   # 40% تلفات
            defender_loss_rate = 0.1   # 10% تلفات
        
        elif attacker_final < defender_final:
            # شکست جزئی
            result = "minor_loss"
            attacker_loss_rate = 0.3   # 30% تلفات
            defender_loss_rate = 0.2   # 20% تلفات
        
        else:
            # تساوی
            result = "draw"
            attacker_loss_rate = 0.2   # 20% تلفات
            defender_loss_rate = 0.2   # 20% تلفات
        
        # محاسبه تلفات واحدها
        attacker_losses = self.calculate_losses(attacker_units, attacker_loss_rate)
        defender_losses = self.calculate_losses(defender_units if defender_units else defender.units, defender_loss_rate)
        
        return {
            "result": result,
            "attacker_losses": attacker_losses,
            "defender_losses": defender_losses,
            "resources_stolen": resources_stolen,
            "attacker_power": attacker_final,
            "defender_power": defender_final
        }
    
    def calculate_power(self, player, units, action_type):
        """محاسبه قدرت کلی"""
        power = 0
        
        for unit_type, unit_dict in units.items():
            for unit_name, count in unit_dict.items():
                if unit_name in config.Config.UNITS.get(unit_type, {}):
                    unit_info = config.Config.UNITS[unit_type][unit_name]
                    if action_type == "attack":
                        power += count * unit_info.get("attack", 0)
                    else:  # defense
                        power += count * unit_info.get("defense", 0)
        
        # اعمال بونوس تکنولوژی
        tech_bonus = 1 + (player.tech_level * 0.05)  # 5% افزایش به ازای هر سطح
        power *= tech_bonus
        
        return power
    
    def calculate_losses(self, units, loss_rate):
        """محاسبه تلفات واحدها"""
        losses = {}
        
        for unit_type, unit_dict in units.items():
            losses[unit_type] = {}
            for unit_name, count in unit_dict.items():
                lost = int(count * loss_rate)
                if lost > 0:
                    losses[unit_type][unit_name] = lost
        
        return losses
    
    def save_battle(self, attacker_id, defender_id, attacker_type, defender_type,
                   units_used, result, attacker_losses, defender_losses, resources_stolen):
        """ذخیره اطلاعات جنگ"""
        session = self.db.get_session()
        try:
            battle = Battle(
                attacker_id=attacker_id,
                defender_id=defender_id,
                attacker_type=attacker_type,
                defender_type=defender_type,
                units_used=units_used,
                result=result,
                attacker_losses=attacker_losses,
                defender_losses=defender_losses,
                resources_stolen=resources_stolen
            )
            session.add(battle)
            session.commit()
            return battle.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
