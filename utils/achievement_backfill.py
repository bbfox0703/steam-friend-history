# utils/achievement_backfill.py

import sqlite3
import time
import functools
from datetime import datetime
from utils.steam_api import fetch_achievements
from utils.db import get_connection, init_db

print = functools.partial(print, flush=True)

# 確保資料表存在
init_db()

DB_PATH = "./database/steam_data.db"

BATCH_SIZE = 10
SLEEP_TIME = 2  # seconds
MAX_RETRY = 3

def fetch_pending_queue():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM achievement_queue WHERE status = 'pending' ORDER BY created_at ASC LIMIT ?", (BATCH_SIZE,))
    rows = c.fetchall()
    conn.close()
    return rows

def update_queue_status(appid, status, retry_count=0):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        UPDATE achievement_queue
        SET status = ?, retry_count = ?, last_attempt_at = ?
        WHERE appid = ?
    """, (status, retry_count, now, appid))
    conn.commit()
    conn.close()

def insert_achievement_history(appid, date_counts):
    conn = get_connection()
    c = conn.cursor()
    for date, count in date_counts.items():
        c.execute("""
            INSERT INTO achievement_history (date, appid, cumulative_achievements)
            VALUES (?, ?, ?)
        """, (date, appid, count))
    conn.commit()
    conn.close()

def process_appid(appid):
    print(f"🔍 {time.strftime('%Y-%m-%d %H:%M:%S')} 開始補資料 AppID: {appid}")
    achievements = fetch_achievements(appid)
    if not achievements:
        print(f"⚠️ {time.strftime('%Y-%m-%d %H:%M:%S')} AppID {appid} 沒有回傳任何成就資料")
        return False

    date_counts = {}
    for item in achievements:
        if item.get('achieved', 0) == 1:
            unlocktime = item.get('unlocktime')  # 🔥 正確欄位名
            if unlocktime:
                date = datetime.utcfromtimestamp(unlocktime).strftime('%Y-%m-%d')
                date_counts[date] = date_counts.get(date, 0) + 1

    if not date_counts:
        print(f"⚠️ {time.strftime('%Y-%m-%d %H:%M:%S')} AppID {appid} 沒有有效成就解鎖紀錄")
        return False

    # 按日期累積成就數
    sorted_dates = sorted(date_counts.keys())
    cumulative = 0
    cumulative_counts = {}
    for date in sorted_dates:
        cumulative += date_counts[date]
        cumulative_counts[date] = cumulative

    insert_achievement_history(appid, cumulative_counts)
    print(f"✅ {time.strftime('%Y-%m-%d %H:%M:%S')} 完成補資料 AppID: {appid}")
    return True

def main():
    init_db()  # 確保資料表存在
    pending_rows = fetch_pending_queue()
    if not pending_rows:
        print("✅ 沒有 pending 成就需要補資料")
        return

    for row in pending_rows:
        appid = row["appid"]
        retry_count = row["retry_count"]

        success = process_appid(appid)

        if success:
            update_queue_status(appid, "done")
        else:
            if retry_count + 1 >= MAX_RETRY:
                update_queue_status(appid, "error", retry_count + 1)
                print(f"❌ {time.strftime('%Y-%m-%d %H:%M:%S')} AppID {appid} 多次失敗，標記為 error")
            else:
                update_queue_status(appid, "pending", retry_count + 1)
                print(f"🔁 {time.strftime('%Y-%m-%d %H:%M:%S')} AppID {appid} 重試次數增加 {retry_count + 1}")

        time.sleep(SLEEP_TIME)

if __name__ == "__main__":
    main()
