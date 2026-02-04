#!/usr/bin/env python3
"""
Ancient World Wars - Telegram Strategy Game v2
A sophisticated multiplayer strategy game set in ancient times with dynamic AI, seasons, and more.
"""

import os
import asyncio
import random
import json
import sqlite3
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    filters, 
    ContextTypes,
    ConversationHandler
)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
OWNER_ID = int(os.getenv("OWNER_ID", 8588773170))
CHANNEL_ID = os.getenv("CHANNEL_ID", "@your_channel")  # Channel for automatic updates

# Game constants
SEASON_DURATION_HOURS = 24  # Season lasts 24 hours by default
COUNTRIES = [
    "پارس", "روم", "مصر", "یونان", "چین", "بابل", "آشور", "کارتاژ", "هند", "مقدونیه",
    "اسپارت", "اتریا", "سومر", "هلنیسم", "کوش", "اشکانیان", "سلوکیان", "فرنگ", 
    "اوگو", "گوت", "واندال", "بیزانس", "ساسانیان", "اکسوم", "هفتسیون", "گوپت"
]

# Database setup
class DatabaseManager:
    def __init__(self, db_path="ancient_world_wars.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        """Create all necessary tables for the game"""
        cursor = self.conn.cursor()
        
        # Players table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                country TEXT NOT NULL,
                username TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Countries table (for both human and AI players)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS countries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT CHECK(type IN ('HUMAN', 'AI')) NOT NULL,
                owner_telegram_id INTEGER,
                FOREIGN KEY (owner_telegram_id) REFERENCES players(telegram_id)
            )
        """)
        
        # Army table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS army (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                country_id INTEGER NOT NULL,
                soldier_type TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                count INTEGER DEFAULT 0,
                FOREIGN KEY (country_id) REFERENCES countries(id)
            )
        """)
        
        # Resources table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                country_id INTEGER NOT NULL,
                gold INTEGER DEFAULT 0,
                iron INTEGER DEFAULT 0,
                stone INTEGER DEFAULT 0,
                food INTEGER DEFAULT 0,
                FOREIGN KEY (country_id) REFERENCES countries(id)
            )
        """)
        
        # Alliances table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alliances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                country1_id INTEGER NOT NULL,
                country2_id INTEGER NOT NULL,
                alliance_type TEXT DEFAULT 'PEACE',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (country1_id) REFERENCES countries(id),
                FOREIGN KEY (country2_id) REFERENCES countries(id)
            )
        """)
        
        # Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                country_id INTEGER,
                target_country_id INTEGER,
                season_number INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (country_id) REFERENCES countries(id),
                FOREIGN KEY (target_country_id) REFERENCES countries(id)
            )
        """)
        
        # Seasons table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seasons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season_number INTEGER UNIQUE NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL,
                winner_country_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (winner_country_id) REFERENCES countries(id)
            )
        """)
        
        # Advisors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS advisors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_telegram_id INTEGER NOT NULL,
                last_advice_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                advice_count INTEGER DEFAULT 0,
                FOREIGN KEY (player_telegram_id) REFERENCES players(telegram_id)
            )
        """)
        
        # Initialize default countries if they don't exist
        for country_name in COUNTRIES:
            cursor.execute("""
                INSERT OR IGNORE INTO countries (name, type) 
                VALUES (?, 'AI')
            """, (country_name,))
        
        self.conn.commit()
    
    def add_player(self, telegram_id: int, country_name: str, username: str = None):
        """Add a new player to the game"""
        cursor = self.conn.cursor()
        
        # Add player
        cursor.execute("""
            INSERT OR REPLACE INTO players (telegram_id, country, username, is_active)
            VALUES (?, ?, ?, 1)
        """, (telegram_id, country_name, username))
        
        # Update country to be controlled by human
        cursor.execute("""
            UPDATE countries 
            SET type = 'HUMAN', owner_telegram_id = ?
            WHERE name = ?
        """, (telegram_id, country_name))
        
        # Initialize resources for the country
        country_id = self.get_country_id_by_name(country_name)
        if country_id:
            cursor.execute("""
                INSERT OR IGNORE INTO resources (country_id, gold, iron, stone, food)
                VALUES (?, 1000, 500, 500, 1000)
            """, (country_id,))
            
            # Initialize basic army
            cursor.execute("""
                INSERT OR IGNORE INTO army (country_id, soldier_type, level, count)
                VALUES (?, 'infantry', 1, 100)
            """, (country_id,))
        
        self.conn.commit()
    
    def get_country_id_by_name(self, country_name: str) -> Optional[int]:
        """Get country ID by name"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM countries WHERE name = ?", (country_name,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def get_free_countries(self) -> List[str]:
        """Get list of countries not controlled by humans"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name FROM countries 
            WHERE type = 'AI' AND owner_telegram_id IS NULL
        """)
        return [row[0] for row in cursor.fetchall()]
    
    def get_player_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """Get player info by telegram ID"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT p.telegram_id, p.country, p.username, c.type
            FROM players p
            JOIN countries c ON p.country = c.name
            WHERE p.telegram_id = ?
        """, (telegram_id,))
        result = cursor.fetchone()
        if result:
            return {
                'telegram_id': result[0],
                'country': result[1],
                'username': result[2],
                'control_type': result[3]
            }
        return None
    
    def get_resources(self, country_id: int) -> Dict:
        """Get resources for a specific country"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT gold, iron, stone, food 
            FROM resources 
            WHERE country_id = ?
        """, (country_id,))
        result = cursor.fetchone()
        if result:
            return {
                'gold': result[0],
                'iron': result[1],
                'stone': result[2],
                'food': result[3]
            }
        return {'gold': 0, 'iron': 0, 'stone': 0, 'food': 0}
    
    def update_resources(self, country_id: int, resources: Dict):
        """Update resources for a country"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE resources 
            SET gold = ?, iron = ?, stone = ?, food = ?
            WHERE country_id = ?
        """, (
            resources['gold'], 
            resources['iron'], 
            resources['stone'], 
            resources['food'],
            country_id
        ))
        self.conn.commit()
    
    def get_army(self, country_id: int) -> List[Dict]:
        """Get army information for a country"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT soldier_type, level, count 
            FROM army 
            WHERE country_id = ?
        """, (country_id,))
        return [{'type': r[0], 'level': r[1], 'count': r[2]} for r in cursor.fetchall()]
    
    def update_army(self, country_id: int, soldier_type: str, level: int, count: int):
        """Update army composition"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO army (country_id, soldier_type, level, count)
            VALUES (?, ?, ?, ?)
        """, (country_id, soldier_type, level, count))
        self.conn.commit()
    
    def start_new_season(self):
        """Start a new season"""
        cursor = self.conn.cursor()
        
        # Get the highest season number to increment
        cursor.execute("SELECT MAX(season_number) FROM seasons")
        result = cursor.fetchone()
        season_number = (result[0] or 0) + 1
        
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=SEASON_DURATION_HOURS)
        
        cursor.execute("""
            INSERT INTO seasons (season_number, start_time, end_time, is_active)
            VALUES (?, ?, ?, 1)
        """, (season_number, start_time, end_time))
        
        self.conn.commit()
        return season_number
    
    def get_current_season(self) -> Optional[Dict]:
        """Get current active season"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, season_number, start_time, end_time, winner_country_id
            FROM seasons 
            WHERE is_active = 1
            ORDER BY start_time DESC 
            LIMIT 1
        """)
        result = cursor.fetchone()
        if result:
            return {
                'id': result[0],
                'season_number': result[1],
                'start_time': result[2],
                'end_time': result[3],
                'winner_country_id': result[4]
            }
        return None
    
    def end_season(self, winner_country_id: int):
        """End current season and declare winner"""
        cursor = self.conn.cursor()
        
        # End current season
        cursor.execute("""
            UPDATE seasons 
            SET is_active = 0, winner_country_id = ?
            WHERE is_active = 1
        """, (winner_country_id,))
        
        self.conn.commit()
    
    def log_event(self, event_type: str, description: str, country_id: int = None, target_country_id: int = None):
        """Log an event in the database"""
        cursor = self.conn.cursor()
        
        # Get current season
        current_season = self.get_current_season()
        season_number = current_season['season_number'] if current_season else 0
        
        cursor.execute("""
            INSERT INTO events (event_type, description, country_id, target_country_id, season_number)
            VALUES (?, ?, ?, ?, ?)
        """, (event_type, description, country_id, target_country_id, season_number))
        
        self.conn.commit()
    
    def get_advisor_info(self, player_telegram_id: int) -> Dict:
        """Get advisor information for a player"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT last_advice_time, advice_count
            FROM advisors
            WHERE player_telegram_id = ?
        """, (player_telegram_id,))
        result = cursor.fetchone()
        if result:
            return {
                'last_advice_time': result[0],
                'advice_count': result[1]
            }
        # Create new advisor record if doesn't exist
        cursor.execute("""
            INSERT INTO advisors (player_telegram_id)
            VALUES (?)
        """, (player_telegram_id,))
        self.conn.commit()
        return {'last_advice_time': None, 'advice_count': 0}
    
    def update_advisor_info(self, player_telegram_id: int):
        """Update advisor information"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE advisors
            SET last_advice_time = CURRENT_TIMESTAMP, advice_count = advice_count + 1
            WHERE player_telegram_id = ?
        """, (player_telegram_id,))
        self.conn.commit()

# Game manager class
class GameManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.current_season = None
        self.ai_manager = AIManager(self.db)
        self.advisor = Advisor(self.db)
    
    async def start_new_season_if_needed(self):
        """Check if we need to start a new season"""
        current_season = self.db.get_current_season()
        if not current_season:
            season_number = self.db.start_new_season()
            self.current_season = season_number
            
            # Notify channel about new season
            await self.broadcast_to_channel(
                f"🏆 شروع فصل جدید جنگ‌های باستان! فصل شماره {season_number} آغاز شد!\n"
                f"کشورهای بازیکنان: {[p['country'] for p in self.get_all_players()]}"
            )
        elif datetime.now() > datetime.fromisoformat(current_season['end_time']):
            # Season ended, find winner and start new one
            winner_country_id = self.determine_season_winner()
            if winner_country_id:
                winner_country = self.get_country_name_by_id(winner_country_id)
                winner_player = self.get_player_by_country_id(winner_country_id)
                
                # Announce winner
                await self.broadcast_to_channel(
                    f"🏆 پایان فصل جنگ‌های باستان\n"
                    f"👑 فاتح نهایی جهان: {winner_country}\n"
                    f"👤 بازیکن: {winner_player['telegram_id'] if winner_player else 'AI'}\n"
                    f"ساخته شده توسط @amele55\n"
                    f"منتظر فصل بعد باشید"
                )
                
                # End current season
                self.db.end_season(winner_country_id)
            
            # Start new season
            season_number = self.db.start_new_season()
            self.current_season = season_number
            
            await self.broadcast_to_channel(
                f"🏆 شروع فصل جدید جنگ‌های باستان! فصل شماره {season_number} آغاز شد!"
            )
    
    def determine_season_winner(self) -> Optional[int]:
        """Determine the winner of the season (human player with strongest army/resources)"""
        cursor = self.db.conn.cursor()
        
        # Find human players with their army strength
        cursor.execute("""
            SELECT c.id, c.name, p.telegram_id
            FROM countries c
            JOIN players p ON c.owner_telegram_id = p.telegram_id
            WHERE c.type = 'HUMAN'
        """)
        
        human_countries = cursor.fetchall()
        best_country_id = None
        best_score = 0
        
        for country_row in human_countries:
            country_id = country_row[0]
            
            # Calculate score based on army strength and resources
            army = self.db.get_army(country_id)
            resources = self.db.get_resources(country_id)
            
            army_strength = sum(unit['count'] * unit['level'] for unit in army)
            resource_value = resources['gold'] + resources['iron'] + resources['stone'] + resources['food']
            
            total_score = army_strength + resource_value
            
            if total_score > best_score:
                best_score = total_score
                best_country_id = country_id
        
        return best_country_id
    
    def get_all_players(self) -> List[Dict]:
        """Get all registered players"""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT telegram_id, country, username FROM players WHERE is_active = 1")
        return [{'telegram_id': r[0], 'country': r[1], 'username': r[2]} for r in cursor.fetchall()]
    
    def get_country_name_by_id(self, country_id: int) -> Optional[str]:
        """Get country name by ID"""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT name FROM countries WHERE id = ?", (country_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def get_player_by_country_id(self, country_id: int) -> Optional[Dict]:
        """Get player info by country ID"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT p.telegram_id, p.country, p.username
            FROM players p
            JOIN countries c ON p.country = c.name
            WHERE c.id = ?
        """, (country_id,))
        result = cursor.fetchone()
        if result:
            return {
                'telegram_id': result[0],
                'country': result[1],
                'username': result[2]
            }
        return None
    
    async def broadcast_to_channel(self, message: str):
        """Broadcast message to channel (in real implementation)"""
        print(f"[CHANNEL BROADCAST]: {message}")  # Placeholder for actual channel broadcast

# AI Manager for dynamic AI behavior
class AIManager:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.personalities = ["aggressive", "defensive", "diplomatic", "balanced"]
    
    def make_decisions(self):
        """Make decisions for all AI countries"""
        cursor = self.db.conn.cursor()
        
        # Get all AI-controlled countries
        cursor.execute("""
            SELECT id, name 
            FROM countries 
            WHERE type = 'AI' AND owner_telegram_id IS NULL
        """)
        
        ai_countries = cursor.fetchall()
        
        for country_id, country_name in ai_countries:
            # Simple AI decision making
            action = random.choice(["upgrade_army", "gather_resources", "attack", "form_alliance", "do_nothing"])
            
            if action == "upgrade_army":
                # Upgrade a random army unit
                current_army = self.db.get_army(country_id)
                if current_army:
                    unit_to_upgrade = random.choice(current_army)
                    new_level = min(unit_to_upgrade['level'] + 1, 10)
                    self.db.update_army(country_id, unit_to_upgrade['type'], new_level, unit_to_upgrade['count'])
                    
                    self.db.log_event(
                        "ARMY_UPGRADE", 
                        f"{country_name} ارتش خود را ارتقا داد", 
                        country_id
                    )
            
            elif action == "gather_resources":
                # Increase resources randomly
                resources = self.db.get_resources(country_id)
                resource_types = ['gold', 'iron', 'stone', 'food']
                resource_to_increase = random.choice(resource_types)
                resources[resource_to_increase] += random.randint(50, 200)
                self.db.update_resources(country_id, resources)
                
                self.db.log_event(
                    "RESOURCE_GAIN", 
                    f"{country_name} منابع خود را افزایش داد", 
                    country_id
                )

# Advisor system for strategic suggestions
class Advisor:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def get_advice(self, player_telegram_id: int) -> str:
        """Generate strategic advice for a player"""
        player_info = self.db.get_player_by_telegram_id(player_telegram_id)
        if not player_info:
            return "متاسفانه اطلاعات شما یافت نشد."
        
        country_id = self.db.get_country_id_by_name(player_info['country'])
        if not country_id:
            return "کشور شما یافت نشد."
        
        # Get player's current situation
        resources = self.db.get_resources(country_id)
        army = self.db.get_army(country_id)
        
        # Generate advice based on situation
        advice_parts = []
        
        # Check resource levels
        low_resources = []
        if resources['gold'] < 200:
            low_resources.append("طلا")
        if resources['food'] < 300:
            low_resources.append("غذا")
        
        if low_resources:
            advice_parts.append(f"⚠️ منابع {', '.join(low_resources)} شما کم است. به افزایش آن‌ها بپردازید.")
        
        # Check army strength
        total_soldiers = sum(unit['count'] for unit in army)
        avg_level = sum(unit['level'] for unit in army) / len(army) if army else 0
        
        if total_soldiers < 200:
            advice_parts.append("👥 ارتش شما ضعیف است. به تقویت نیروهای خود بپردازید.")
        elif avg_level < 3:
            advice_parts.append("⚔️ سطح ارتش شما پایین است. ارتقای نیروها را در نظر بگیرید.")
        
        # Default advice if no specific issues found
        if not advice_parts:
            advice_parts.append("✅ وضعیت فعلی شما خوب است. می‌توانید به گسترش قلمرو یا تشکیل اتحاد فکر کنید.")
        
        # Add a random strategic tip
        tips = [
            "🤝 اتحاد با کشورهای ضعیف‌تر می‌تواند در مقابل حریفان قدرتمند مؤثر باشد.",
            "🛡️ دفاع محکم و تقویت شهرها قبل از حمله بهترین راه برای پیروزی است.",
            "💰 منابع مداوم مانند معادن و مزارع را در اولویت قرار دهید.",
            "⚔️ حملات غافلگیرانه در ساعات مختلف روز می‌تواند موثر باشد."
        ]
        advice_parts.append(f"💡 نکته استراتژیک: {random.choice(tips)}")
        
        return "\n".join(advice_parts)

# Conversation states
ADD_PLAYER_COUNTRY, ADD_PLAYER_USER_ID = range(2)

# Handler functions
game_manager = GameManager()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id
    
    if user_id == OWNER_ID:
        # Owner menu
        keyboard = [
            [InlineKeyboardButton("افزودن بازیکن", callback_data="add_player")],
            [InlineKeyboardButton("شروع فصل", callback_data="start_season")],
            [InlineKeyboardButton("پایان فصل", callback_data="end_season")],
            [InlineKeyboardButton("ریست کل بازی", callback_data="reset_game")],
            [InlineKeyboardButton("ارسال پیام عمومی", callback_data="broadcast")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("پنل مالک - جنگ جهانی باستان ورژن ۲", reply_markup=reply_markup)
    else:
        # Regular player menu
        player_info = game_manager.db.get_player_by_telegram_id(user_id)
        if player_info:
            # Player is registered
            await show_player_menu(update, context)
        else:
            await update.message.reply_text("شما عضو بازی نیستید. با مالک ربات تماس بگیرید.")

async def show_player_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu for registered players"""
    user_id = update.effective_user.id
    player_info = game_manager.db.get_player_by_telegram_id(user_id)
    
    if not player_info:
        await update.message.reply_text("شما عضو بازی نیستید.")
        return
    
    # Get player resources and army
    country_id = game_manager.db.get_country_id_by_name(player_info['country'])
    if not country_id:
        await update.message.reply_text("خطا در دریافت اطلاعات کشور.")
        return
    
    resources = game_manager.db.get_resources(country_id)
    army = game_manager.db.get_army(country_id)
    
    # Create player menu
    keyboard = [
        [InlineKeyboardButton("مشاهده منابع", callback_data="show_resources")],
        [InlineKeyboardButton("مشاهده ارتش", callback_data="show_army")],
        [InlineKeyboardButton("ارتقای ارتش", callback_data="upgrade_army")],
        [InlineKeyboardButton("دریافت مشاوره", callback_data="get_advice")],
        [InlineKeyboardButton("اطلاعات فصل", callback_data="season_info")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (f"🏛️ کشور شما: {player_info['country']}\n"
               f"💰 منابع:\n"
               f"  - طلا: {resources['gold']}\n"
               f"  - آهن: {resources['iron']}\n"
               f"  - سنگ: {resources['stone']}\n"
               f"  - غذا: {resources['food']}\n\n"
               f"👥 ارتش: {sum(u['count'] for u in army)} سرباز")
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id == OWNER_ID:
        await handle_owner_callback(query, context)
    else:
        await handle_player_callback(query, context)

async def handle_owner_callback(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle callbacks from owner"""
    data = query.data
    
    if data == "add_player":
        # Show free countries for selection
        free_countries = game_manager.db.get_free_countries()
        if not free_countries:
            await query.edit_message_text("هیچ کشور آزادی موجود نیست!")
            return
        
        # Create keyboard with countries
        keyboard = []
        for i in range(0, len(free_countries), 2):  # Two buttons per row
            row = []
            for j in range(i, min(i+2, len(free_countries))):
                row.append(InlineKeyboardButton(free_countries[j], callback_data=f"select_country_{free_countries[j]}"))
            keyboard.append(row)
        
        await query.edit_message_text("کشور مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data.startswith("select_country_"):
        country_name = data.replace("select_country_", "")
        context.user_data['selected_country'] = country_name
        await query.edit_message_text(f"کشور انتخاب شده: {country_name}\n\nلطفاً ID عددی تلگرام بازیکن را وارد کنید:")
        return ADD_PLAYER_USER_ID
    
    elif data == "start_season":
        await game_manager.start_new_season_if_needed()
        await query.edit_message_text("فصل جدید شروع شد!")
    
    elif data == "broadcast":
        await query.edit_message_text("لطفاً پیام خود را برای ارسال به همه بازیکنان وارد کنید:")
        # We would implement this in a full version with a conversation handler

async def handle_player_callback(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle callbacks from regular players"""
    data = query.data
    user_id = query.from_user.id
    
    if data == "show_resources":
        player_info = game_manager.db.get_player_by_telegram_id(user_id)
        country_id = game_manager.db.get_country_id_by_name(player_info['country'])
        resources = game_manager.db.get_resources(country_id)
        
        message = (f"💰 منابع کشور {player_info['country']}:\n"
                  f"  - طلا: {resources['gold']}\n"
                  f"  - آهن: {resources['iron']}\n"
                  f"  - سنگ: {resources['stone']}\n"
                  f"  - غذا: {resources['food']}")
        
        await query.edit_message_text(message)
    
    elif data == "show_army":
        player_info = game_manager.db.get_player_by_telegram_id(user_id)
        country_id = game_manager.db.get_country_id_by_name(player_info['country'])
        army = game_manager.db.get_army(country_id)
        
        if army:
            army_list = "\n".join([f"  - {unit['type']}: {unit['count']} نفر (سطح {unit['level']})" for unit in army])
            message = f"👥 ارتش کشور {player_info['country']}:\n{army_list}"
        else:
            message = f"👥 ارتش کشور {player_info['country']}:\nهیچ نیرویی وجود ندارد."
        
        await query.edit_message_text(message)
    
    elif data == "get_advice":
        advice = game_manager.advisor.get_advice(user_id)
        await query.edit_message_text(f"📜 مشاور استراتژیک:\n\n{advice}")
        
        # Update advisor info
        game_manager.db.update_advisor_info(user_id)
    
    elif data == "season_info":
        season = game_manager.db.get_current_season()
        if season:
            start_time = datetime.fromisoformat(season['start_time']).strftime("%Y-%m-%d %H:%M")
            end_time = datetime.fromisoformat(season['end_time']).strftime("%Y-%m-%d %H:%M")
            message = (f"📅 اطلاعات فصل جاری:\n"
                      f"  - شماره فصل: {season['season_number']}\n"
                      f"  - زمان شروع: {start_time}\n"
                      f"  - زمان پایان: {end_time}")
        else:
            message = "هیچ فصل فعالی وجود ندارد."
        
        await query.edit_message_text(message)

async def add_player_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user ID input for adding player"""
    try:
        user_id = int(update.message.text)
        selected_country = context.user_data.get('selected_country')
        
        if not selected_country:
            await update.message.reply_text("خطا: هیچ کشوری انتخاب نشده است.")
            return
        
        # Add player to database
        game_manager.db.add_player(user_id, selected_country, f"user_{user_id}")
        
        await update.message.reply_text(f"بازیکن با ID {user_id} به کشور {selected_country} اضافه شد!")
        
        # Reset context
        context.user_data.clear()
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("لطفاً یک ID عددی معتبر وارد کنید.")
        return ADD_PLAYER_USER_ID

def main():
    """Main function to run the bot"""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_callback_handler))
    
    # Add conversation handler for adding players
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(lambda u, c: None, pattern="^select_country_.*$")],  # This will be handled in button_callback_handler
        states={
            ADD_PLAYER_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_player_user_id)]
        },
        fallbacks=[]
    )
    # Note: In a real implementation, we'd need to properly set up the conversation handler
    
    application.add_handler(conv_handler)
    
    # Run the bot
    print("Starting Ancient World Wars Bot v2...")
    application.run_polling()

if __name__ == "__main__":
    main()