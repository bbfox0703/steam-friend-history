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

# 第一次執行用來建表
if __name__ == "__main__":
    init_db()
    print("資料表建立完成！")
