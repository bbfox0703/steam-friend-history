import os
import time
from datetime import datetime
from utils.db import (
    get_all_dates,
    get_appids_from_playtime_trend,
    count_appid_entries,
    insert_or_update_achievement
)
from utils.steam_api import fetch_achievements

LOG_DIR = "./logs"
LOG_FILE = os.path.join(LOG_DIR, "achievement_trend_batch_backfill.log")

def log(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")

def backfill_one_appid(appid: str, date_list: list[str]):
    achievement_list = fetch_achievements(appid)

    if achievement_list is None or not achievement_list:
        log(f"⚠️ backfill_one_appid(): AppID {appid} 沒有成就或抓取失敗")
        return

    unlock_dates = []
    for achievement in achievement_list:
        unlock_time = achievement.get("unlocktime", 0)
        if unlock_time > 0:
            dt = datetime.utcfromtimestamp(unlock_time)
            unlock_dates.append(dt)

    if not unlock_dates:
        log(f"ℹ️ backfill_one_appid() AppID {appid} 沒有解鎖成就，視為 0 不處理")
        return False

    unlock_dates.sort()
    cumulative_by_day = {}

    for date in date_list:
        day = datetime.strptime(date, "%Y-%m-%d")
        count = sum(1 for d in unlock_dates if d <= day)
        cumulative_by_day[date] = count

    for date, total in cumulative_by_day.items():
        insert_or_update_achievement(date, appid, total)

    log(f"✅ backfill_one_appid() AppID {appid} 回填完成，共補 {len(date_list)} 天")
    return True

def main():
    log("🚀 成就趨勢全自動批次回填開始")

    date_list = get_all_dates()
    total_days = len(date_list)
    if total_days == 0:
        log("❌ playtime_trend 中沒有日期，無法補資料")
        return

    all_appids = get_appids_from_playtime_trend()
    log(f"📦 共偵測到 {len(all_appids)} 個 AppID，總天數 = {total_days}")

    processed = 0
    skipped = 0

    for i, appid in enumerate(all_appids):
        entry_count = count_appid_entries(appid)
        if entry_count >= total_days:
            skipped += 1
            continue

        success = backfill_one_appid(appid, date_list)
        if success:
            processed += 1

        if (i + 1) % 3 == 0:
            time.sleep(1)

    log(f"🎯 回填完成：成功 {processed} 款，略過 {skipped} 款")
    log("✅ 成就趨勢批次回填結束\n")

if __name__ == "__main__":
    main()
