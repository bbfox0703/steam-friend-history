# utils/db.py

import sqlite3
from pathlib import Path

# 資料庫路徑
DB_PATH = Path('./database/steam_data.db')

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

    conn.commit()
    conn.close()

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


# 第一次執行用來建表
if __name__ == "__main__":
    init_db()
    print("資料表建立完成！")
