from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import config

class DatabaseManager:
    def __init__(self):
        self.engine = create_engine(config.Config.DATABASE_URL)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def init_db(self):
        """ایجاد جداول دیتابیس"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """دریافت یک session جدید"""
        return self.SessionLocal()
    
    def add_user(self, user_data):
        """افزودن کاربر جدید"""
        session = self.get_session()
        try:
            user = User(**user_data)
            session.add(user)
            session.commit()
            return user
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_user(self, user_id, bot_id=None):
        """دریافت اطلاعات کاربر"""
        session = self.get_session()
        try:
            query = session.query(User).filter(User.user_id == user_id)
            if bot_id:
                query = query.filter(User.bot_id == bot_id)
            return query.first()
        finally:
            session.close()
    
    def update_user(self, user_id, updates):
        """به‌روزرسانی اطلاعات کاربر"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            if user:
                for key, value in updates.items():
                    setattr(user, key, value)
                session.commit()
                return user
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def add_child_bot(self, bot_token, owner_id, mother_bot_id):
        """افزودن ربات فرزند"""
        session = self.get_session()
        try:
            bot = ChildBot(
                bot_token=bot_token,
                owner_id=owner_id,
                mother_bot_id=mother_bot_id
            )
            session.add(bot)
            session.commit()
            return bot
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_child_bots(self, owner_id=None):
        """دریافت لیست ربات‌های فرزند"""
        session = self.get_session()
        try:
            query = session.query(ChildBot)
            if owner_id:
                query = query.filter(ChildBot.owner_id == owner_id)
            return query.all()
        finally:
            session.close()
