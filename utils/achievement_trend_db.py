# utils/achievement_trend_db.py

import sqlite3
from utils.db import get_connection, init_db

# 匯入資料庫，確保表格存在
init_db()

# --- 遊玩時間 ---

def save_playtime(date, appid, playtime_minutes):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO playtime_trend (date, appid, playtime_minutes)
        VALUES (?, ?, ?)
    ''', (date, appid, playtime_minutes))
    conn.commit()
    conn.close()

def get_playtime_by_date(date):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT appid, playtime_minutes
        FROM playtime_trend
        WHERE date = ?
    ''', (date,))
    rows = c.fetchall()
    conn.close()
    return {str(appid): playtime_minutes for appid, playtime_minutes in rows}

# --- 成就數量 ---

def save_achievement(date, appid, achievements):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO achievement_trend (date, appid, achievements)
        VALUES (?, ?, ?)
    ''', (date, appid, achievements))
    conn.commit()
    conn.close()

def get_achievements_by_date(date):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT appid, achievements
        FROM achievement_trend
        WHERE date = ?
    ''', (date,))
    rows = c.fetchall()
    conn.close()
    return {str(appid): achievements for appid, achievements in rows}

# 測試用 (單獨執行時)
if __name__ == "__main__":
    print("測試：今日成就資料：", get_achievements_by_date("2025-04-25"))
