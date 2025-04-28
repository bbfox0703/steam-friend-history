# utils/add_to_achievement_queue_batch.py

import sqlite3
import sys
from utils.db import get_connection, init_db

# 確保資料表存在
init_db()

def add_appid_to_queue(appid: int):
    conn = get_connection()
    c = conn.cursor()

    # 檢查是否已存在
    c.execute("SELECT id FROM achievement_queue WHERE appid = ?", (appid,))
    existing = c.fetchone()
    if existing:
        print(f"⚠️ AppID {appid} 已經在 queue 中，跳過")
        conn.close()
        return

    # 新增進queue
    c.execute("INSERT INTO achievement_queue (appid) VALUES (?)", (appid,))
    conn.commit()
    conn.close()
    print(f"✅ 成功新增 AppID {appid} 到 queue！")

def batch_add_from_file(filepath: str):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"❌ 無法讀取檔案: {e}")
        return

    appids = set()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        for part in line.split(","):
            part = part.strip()
            if part.isdigit():
                appids.add(int(part))

    print(f"🔍 共讀取 {len(appids)} 個 AppID，開始加入 queue...")

    for appid in sorted(appids):
        add_appid_to_queue(appid)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ 請提供 AppID列表檔案路徑，例如：python3 -m utils.add_to_achievement_queue_batch ./appid_list.txt")
        sys.exit(1)

    filepath = sys.argv[1]
    batch_add_from_file(filepath)
