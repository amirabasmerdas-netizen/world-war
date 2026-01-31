import sqlite3
from pathlib import Path
import json

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

# --- توابع عمومی ---
def add_user(user_id, username, country):
    c.execute("INSERT OR IGNORE INTO users (user_id, username, country) VALUES (?, ?, ?)",
              (user_id, username, country))
    conn.commit()

def get_user(user_id):
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return c.fetchone()

def update_user_resources(user_id, amount):
    c.execute("UPDATE users SET resources = resources + ? WHERE user_id=?", (amount, user_id))
    conn.commit()

def give_loan(user_id, loan_amount):
    c.execute("UPDATE users SET resources = resources + ?, loan = loan + ? WHERE user_id=?",
              (loan_amount, loan_amount, user_id))
    conn.commit()

def set_units(user_id, units_dict):
    units_json = json.dumps(units_dict)
    c.execute("UPDATE users SET units=? WHERE user_id=?", (units_json, user_id))
    conn.commit()

def get_units(user_id):
    c.execute("SELECT units FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    return json.loads(result[0]) if result and result[0] else {}
