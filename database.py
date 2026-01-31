import sqlite3
from pathlib import Path

DB_PATH = Path("game.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# جدول کاربران
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    country TEXT,
    resources INTEGER DEFAULT 1000,
    loan INTEGER DEFAULT 0,
    units TEXT DEFAULT '{}'
)
""")

# جدول ربات‌ها
c.execute("""
CREATE TABLE IF NOT EXISTS bots (
    bot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_token TEXT,
    owner_id INTEGER,
    created_at TEXT,
    status TEXT
)
""")

# جدول AI
c.execute("""
CREATE TABLE IF NOT EXISTS ai (
    ai_id INTEGER PRIMARY KEY AUTOINCREMENT,
    country TEXT,
    personality TEXT,
    strategy_state TEXT,
    last_action TEXT
)
""")

# جدول جنگ‌ها
c.execute("""
CREATE TABLE IF NOT EXISTS battles (
    battle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    attacker_id INTEGER,
    defender_id INTEGER,
    units_used TEXT,
    result TEXT,
    timestamp TEXT
)
""")

conn.commit()
