from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json

Base = declarative_base()

class MotherBot(Base):
    __tablename__ = 'mother_bot'
    
    id = Column(Integer, primary_key=True)
    bot_token = Column(String(255), unique=True, nullable=False)
    owner_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default='active')
    child_bots = relationship("ChildBot", back_populates="mother")

class ChildBot(Base):
    __tablename__ = 'child_bots'
    
    id = Column(Integer, primary_key=True)
    bot_token = Column(String(255), unique=True, nullable=False)
    mother_bot_id = Column(Integer, ForeignKey('mother_bot.id'))
    owner_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default='active')
    users = relationship("User", back_populates="bot")
    
    mother = relationship("MotherBot", back_populates="child_bots")

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    country = Column(String(100), nullable=False)
    bot_id = Column(Integer, ForeignKey('child_bots.id'))
    
    # منابع
    money = Column(Float, default=10000)
    resources = Column(JSON, default=lambda: {
        "food": 1000,
        "oil": 1000,
        "metal": 1000,
        "electronics": 500
    })
    
    # نیروها
    units = Column(JSON, default=lambda: {
        "ground": {
            "تازه نفس": 10,
            "ارپیجی زن": 60,
            "تک تیرانداز": 65,
            "سرباز حرفه ای": 1185,
            "توپخانه حرفه ای": 53,
            "سرباز": 100,
            "توپخانه": 2
        },
        "air": {
            "جنگنده سبک": 5,
            "جنگنده سنگین": 3,
            "بمب افکن": 2,
            "بالگرد رزمی": 10
        },
        "defense": {
            "پدافند معمولی": 5,
            "پدافند حرفه ای": 312,
            "پدافند قدرتمند": 100
        },
        "navy": {
            "ناو جنگی": 20,
            "زیردریایی": 31,
            "کشتی جنگی": 105,
            "قایق جنگی": 10
        },
        "cyber": {
            "هکر حرفه ای": 10,
            "تیم هکری": 2
        },
        "missiles": {
            "کوتاه‌برد": 10,
            "میان‌برد": 5,
            "دوربرد": 3,
            "بالستیک": 2
        },
        "special": {
            "بمب کوچولو": 1340,
            "بمب هسته ای": 295
        }
    })
    
    # سازه‌ها
    buildings = Column(JSON, default=lambda: {
        "کارخانه ساده": 3,
        "کارخانه معمولی": 15,
        "کارخانه پیشرفته": 102,
        "کارخانه پستونک سازی": 226,
        "کارخانه حرفه ای": 110,
        "معدن": 3,
        "معدن حرفه ای": 221,
        "معدن پیشرفته": 10,
        "نیروگاه هسته ای": 3,
        "نیروگاه پیشرفته": 110,
        "نیروگاه حرفه ای": 10,
        "نفت کش": 10,
        "نفت کش حرفه ای": 330,
        "بیمارستان": 3,
        "زایشگاه": 9,
        "پارک": 10
    })
    
    # تکنولوژی و وضعیت
    tech_level = Column(Integer, default=1)
    morale = Column(Float, default=100.0)
    last_loan_time = Column(DateTime)
    loan_amount = Column(Float, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    is_admin = Column(Boolean, default=False)
    
    bot = relationship("ChildBot", back_populates="users")
    alliances = relationship("Alliance", back_populates="creator")

class AICountry(Base):
    __tablename__ = 'ai_countries'
    
    id = Column(Integer, primary_key=True)
    country = Column(String(100), nullable=False)
    personality = Column(String(50), default='aggressive')  # aggressive, defensive, diplomatic
    strategy_state = Column(JSON, default=lambda: {
        "last_decision": None,
        "target_country": None,
        "alliance_partner": None,
        "resources_focus": "military"
    })
    units = Column(JSON, default=lambda: {})
    resources = Column(JSON, default=lambda: {})
    money = Column(Float, default=10000)
    last_action = Column(DateTime, default=datetime.utcnow)

class Battle(Base):
    __tablename__ = 'battles'
    
    id = Column(Integer, primary_key=True)
    attacker_id = Column(Integer, ForeignKey('users.id'))
    defender_id = Column(Integer)
    attacker_type = Column(String(20))  # 'user' or 'ai'
    defender_type = Column(String(20))  # 'user' or 'ai'
    units_used = Column(JSON)
    result = Column(String(50))  # 'win', 'lose', 'draw'
    attacker_losses = Column(JSON)
    defender_losses = Column(JSON)
    resources_stolen = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Alliance(Base):
    __tablename__ = 'alliances'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    creator_id = Column(Integer, ForeignKey('users.id'))
    members = Column(JSON, default=lambda: [])  # List of user IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    
    creator = relationship("User", back_populates="alliances")
