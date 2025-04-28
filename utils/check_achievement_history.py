# utils/check_achievement_history.py

import sqlite3
import sys
from utils.db import get_connection, init_db

# 確保資料表存在
init_db()

def check_history(appid: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM achievement_history WHERE appid = ? ORDER BY date ASC", (appid,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        print(f"❌ 找不到 AppID {appid} 的成就歷史資料")
    else:
        print(f"✅ AppID {appid} 成就歷史紀錄：")
        for row in rows:
            print(f"{row['date']} | 累積成就數: {row['cumulative_achievements']}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ 請提供 AppID，例如：")
        print("    python3 -m utils.check_achievement_history 1044720")
        sys.exit(1)

    try:
        appid = int(sys.argv[1])
        check_history(appid)
    except ValueError:
        print("❌ AppID 必須是整數！")
