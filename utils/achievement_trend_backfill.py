import os
import time
from datetime import datetime, timedelta
from utils.db import (
    get_all_dates,
    insert_or_update_achievement
)
from utils.steam_api import fetch_achievements

LOG_DIR = "./logs"
LOG_FILE = os.path.join(LOG_DIR, "achievement_trend_backfill.log")

def log(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {msg}"

    print(full_msg)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")

def backfill_appid(appid: int):
    log(f"🔍 backfill_appid(): 開始回填 AppID {appid}")

    # 取得 trend中所有日期
    dates = get_all_dates()
    if not dates:
        log("⚠️ backfill_appid(): 找不到趨勢資料，無法回填")
        return

    trend_start = datetime.strptime(dates[0], "%Y-%m-%d")

    # 抓這個遊戲所有成就解鎖資料
    achievements = fetch_achievements(appid)
    if achievements is None:
        log(f"⚠️ backfill_appid(): AppID {appid} 抓取成就失敗")
        return

    # 整理每個成就的解鎖時間
    unlock_dates = []
    for achievement in achievement_list:
        unlock_time = achievement.get("unlocktime", 0)
        if unlock_time > 0:
            dt = datetime.utcfromtimestamp(unlock_time)
            unlock_dates.append(dt)

    if not unlock_dates:
        log(f"⚠️ backfill_appid(): AppID {appid} 沒有任何成就解鎖記錄")
        return

    # 計算每天累積成就數
    unlock_dates.sort()
    cumulative_count = 0
    cumulative_by_day = {}

    for date in dates:
        day = datetime.strptime(date, "%Y-%m-%d")
        count_today = sum(1 for d in unlock_dates if d <= day)
        cumulative_by_day[date] = count_today

    # 把資料寫入 achievement_trend
    for date, total in cumulative_by_day.items():
        insert_or_update_achievement(date, appid, total)

    log(f"✅ backfill_appid(): 回填完成 AppID {appid}，補齊 {len(dates)} 天資料")

def main():
    # 這邊可改成讀一個app list
    import sys
    if len(sys.argv) < 2:
        print("❌ 請指定要回填的 AppID")
        print("例如：python achievement_trend_backfill.py 123456")
        return

    appid = int(sys.argv[1])
    backfill_appid(appid)

if __name__ == "__main__":
    main()
