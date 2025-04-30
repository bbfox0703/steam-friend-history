# utils/db.py

import sqlite3
import os
import time
from pathlib import Path

LOG_DIR = "./logs"
LOG_FILE = os.path.join(LOG_DIR, "db.log")


# 資料庫路徑
DB_PATH = Path('./database/steam_data.db')

def log(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")


# 取得資料庫連線
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 初始化資料庫（建立資料表）
def init_db():
    conn = get_connection()
    c = conn.cursor()

    # 建立 playtime_trend 表
    c.execute('''
        CREATE TABLE IF NOT EXISTS playtime_trend (
            date TEXT NOT NULL,
            appid INTEGER NOT NULL,
            playtime_minutes INTEGER,
            PRIMARY KEY (date, appid)
        )
    ''')

    # 建立 achievement_trend 表
    c.execute('''
        CREATE TABLE IF NOT EXISTS achievement_trend (
            date TEXT NOT NULL,
            appid INTEGER NOT NULL,
            achievements INTEGER,
            PRIMARY KEY (date, appid)
        )
    ''')

    # 建立 level_history 表
    c.execute('''
        CREATE TABLE IF NOT EXISTS level_history (
            date TEXT NOT NULL PRIMARY KEY,
            level INTEGER
        )
    ''')

    # 建立 game_titles 表
    c.execute('''
        CREATE TABLE IF NOT EXISTS game_titles (
            appid INTEGER NOT NULL PRIMARY KEY,
            en TEXT,
            tchinese TEXT,
            japanese TEXT
        )
    ''')

    # 🔥 新增 achievement_queue 表
    c.execute('''
        CREATE TABLE IF NOT EXISTS achievement_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appid INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            retry_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_attempt_at TEXT
        )
    ''')

    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_achievement_queue_status ON achievement_queue (status)
    ''')

    # 🔥 新增 achievement_history 表
    c.execute('''
        CREATE TABLE IF NOT EXISTS achievement_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            appid INTEGER NOT NULL,
            cumulative_achievements INTEGER NOT NULL
        )
    ''')

    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_achievement_history_date ON achievement_history (date)
    ''')

    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_achievement_history_appid ON achievement_history (appid)
    ''')
    # 成就快取表
    c.execute("""
        CREATE TABLE IF NOT EXISTS achievement_cache (
            steamid TEXT,
            appid INTEGER,
            achievement_name TEXT,
            unlock_time INTEGER,
            PRIMARY KEY (steamid, appid, achievement_name)
        )
    """)
    # 📦 遊戲資訊快取表
    c.execute("""
        CREATE TABLE IF NOT EXISTS game_info_cache (
            appid INTEGER,
            lang TEXT,
            name TEXT,
            header_image TEXT,
            raw_json TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (appid, lang)
        )
    """)

    conn.commit()
    conn.close()

def get_cached_achievements(steamid, appid):
    # conn = sqlite3.connect(DB_FILE)
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT achievement_name, unlock_time
        FROM achievement_cache
        WHERE steamid = ? AND appid = ?
    """, (steamid, appid))
    result = c.fetchall()
    conn.close()
    log(f"🧪 快取查詢結果: {result}")
    return [{"name": row[0], "unlock_time": row[1]} for row in result]

def save_achievement_cache(steamid, appid, achievements):
    # conn = sqlite3.connect(DB_FILE)
    conn = get_connection()
    c = conn.cursor()
    c.executemany("""
        INSERT OR REPLACE INTO achievement_cache (steamid, appid, achievement_name, unlock_time)
        VALUES (?, ?, ?, ?)
    """, [(steamid, appid, a["name"], a["unlock_time"]) for a in achievements])
    conn.commit()
    conn.close()
    log(f"🧪 快取寫入結果: {steamid}, {appid}, {achievements}")

def get_appids_from_playtime_trend():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT DISTINCT appid FROM playtime_trend')
    appids = [str(row[0]) for row in c.fetchall()]
    conn.close()
    return appids

def count_appid_entries(appid: str) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM playtime_trend WHERE appid = ?', (appid,))
    count = c.fetchone()[0]
    conn.close()
    return count

# 查詢某日所有 AppID 的成就數
def get_achievements_by_date(date: str) -> dict:
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT appid, achievements
        FROM achievement_trend
        WHERE date = ?
    ''', (date,))
    rows = c.fetchall()
    conn.close()
    return {str(row["appid"]): row["achievements"] for row in rows}

# 查詢某日所有 AppID 的遊玩分鐘數
def get_playtime_by_date(date: str) -> dict:
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT appid, playtime_minutes
        FROM playtime_trend
        WHERE date = ?
    ''', (date,))
    rows = c.fetchall()
    conn.close()
    return {str(row["appid"]): row["playtime_minutes"] for row in rows}

# 查詢成就趨勢資料中，所有存在的日期（升冪排序）
def get_all_dates() -> list[str]:
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT DISTINCT date
        FROM achievement_trend
        ORDER BY date ASC
    ''')
    rows = c.fetchall()
    conn.close()
    return [row["date"] for row in rows]

def insert_or_update_achievement(date: str, appid: str, achievements: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO achievement_trend (date, appid, achievements)
        VALUES (?, ?, ?)
        ON CONFLICT(date, appid) DO UPDATE SET achievements=excluded.achievements
    ''', (date, appid, achievements))
    conn.commit()
    conn.close()

def insert_or_update_playtime(date: str, appid: str, playtime_minutes: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO playtime_trend (date, appid, playtime_minutes)
        VALUES (?, ?, ?)
        ON CONFLICT(date, appid) DO UPDATE SET playtime_minutes=excluded.playtime_minutes
    ''', (date, appid, playtime_minutes))
    conn.commit()
    conn.close()

def get_game_info_cache(appid, lang):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT name, header_image, raw_json
        FROM game_info_cache
        WHERE appid = ? AND lang = ?
    """, (appid, lang))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def save_game_info_cache(appid, lang, name, header_image, raw_json):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO game_info_cache (appid, lang, name, header_image, raw_json, last_updated)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (appid, lang, name, header_image, raw_json))
    conn.commit()
    conn.close()

# 第一次執行用來建表
if __name__ == "__main__":
    init_db()
    print("資料表建立完成！")
