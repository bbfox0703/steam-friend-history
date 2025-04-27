# utils/db.py

import sqlite3
from pathlib import Path

# 資料庫路徑（你可以改成你想放的位置）
DB_PATH = Path('./database/steam_data.db')

# 取得資料庫連線
def get_connection():
    conn = sqlite3.connect(DB_PATH)
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

    conn.commit()
    conn.close()

# 第一次執行用來建表
if __name__ == "__main__":
    init_db()
    print("資料表建立完成！")