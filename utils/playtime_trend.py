# utils/playtime_trend.py

import json
from utils.db import get_connection, init_db
from datetime import datetime, timedelta
from collections import OrderedDict

# 匯入現有 JSON 檔案，轉存進 SQLite 資料庫
def import_playtime_json(json_path):
    init_db()
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    conn = get_connection()
    c = conn.cursor()

    for date, games in data.items():
        for appid_str, playtime_minutes in games.items():
            appid = int(appid_str)
            c.execute('''
                INSERT OR REPLACE INTO playtime_trend (date, appid, playtime_minutes)
                VALUES (?, ?, ?)
            ''', (date, appid, playtime_minutes))

    conn.commit()
    conn.close()
    print(f"成功匯入 {json_path} 的資料！")

# 新增或更新單筆資料
def save_playtime(date, appid, playtime_minutes):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO playtime_trend (date, appid, playtime_minutes)
        VALUES (?, ?, ?)
    ''', (date, appid, playtime_minutes))
    conn.commit()
    conn.close()

# 查詢某天的所有遊戲資料 (回傳 dict)
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

# 查詢某遊戲的所有日期資料 (回傳 list of dict)
def get_playtime_by_appid(appid):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT date, playtime_minutes
        FROM playtime_trend
        WHERE appid = ?
        ORDER BY date ASC
    ''', (appid,))
    rows = c.fetchall()
    conn.close()

    return [{"date": date, "playtime_minutes": playtime_minutes} for date, playtime_minutes in rows]

# 計算每日新增遊玩時間
def calculate_daily_minutes(playtime_records):
    daily_minutes = {}
    last_playtime = None

    for record in playtime_records:
        date = record["date"]
        today_playtime = record["playtime_minutes"]

        if last_playtime is None:
            # Treat the first record as baseline to avoid inflating playtime
            diff = 0
        else:
            diff = today_playtime - last_playtime if today_playtime is not None else 0
            if diff < 0 or diff > 1440:
                diff = 0

        daily_minutes[date] = diff

        if today_playtime is not None:
            last_playtime = today_playtime

    return daily_minutes

# 匯總成月或年資料
def summarize_minutes(daily_minutes, mode='month'):
    summary = {}
    for d, v in daily_minutes.items():
        key = d[:7] if mode == 'month' else d[:4]
        summary[key] = summary.get(key, 0) + v
    return OrderedDict(sorted(summary.items()))

# 測試用 (單獨執行時)
if __name__ == "__main__":
    import_playtime_json('database/playtime_trend.json')
