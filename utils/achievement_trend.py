import os
import time
from datetime import datetime, timedelta
from utils.db import (
    get_achievements_by_date,
    get_playtime_by_date,
    get_all_dates,
    insert_or_update_achievement,
    insert_or_update_playtime
)
from utils.steam_api import fetch_achievements, fetch_playtimes

LOG_DIR = "./logs"
LOG_FILE = os.path.join(LOG_DIR, "achievement_trend.log")

def log(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {msg}"

    # 顯示到畫面
    print(full_msg)

    # 寫入log檔
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")

def update_trends():
    today = datetime.today().strftime('%Y-%m-%d')
    yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')

    log(f"📈 更新成就與遊玩時間趨勢 - {today}")

    try:
        yesterday_achievements = get_achievements_by_date(yesterday) or {}
    except Exception:
        yesterday_achievements = {}
        log(f"⚠️ 昨天({yesterday})無成就資料，將以空集合處理")

    try:
        yesterday_playtimes = get_playtime_by_date(yesterday) or {}
    except Exception:
        yesterday_playtimes = {}
        log(f"⚠️ 昨天({yesterday})無遊玩時間資料，將以空集合處理")

    # 抓取今天資料
    achievements_today = fetch_achievements() or {}
    playtimes_today = fetch_playtimes() or {}

    log(f"🎯 抓取到 {len(achievements_today)} 筆成就資料，{len(playtimes_today)} 筆遊玩時間資料")

    # 找出今天新出現但昨天沒有的
    new_achievement_apps = set(achievements_today.keys()) - set(yesterday_achievements.keys())
    new_playtime_apps = set(playtimes_today.keys()) - set(yesterday_playtimes.keys())

    if new_achievement_apps:
        log(f"➕ 新成就AppID出現: {', '.join(map(str, new_achievement_apps))}")
    if new_playtime_apps:
        log(f"➕ 新遊玩時間AppID出現: {', '.join(map(str, new_playtime_apps))}")

    all_dates = get_all_dates()

    if not all_dates:
        all_dates = [yesterday]
        log(f"📅 資料庫無歷史日期，初始化為昨日 {yesterday}")

    log(f"🔄 對歷史日期回填: {', '.join(all_dates)}")

    # 補回歷史資料
    for date in all_dates:
        for appid in new_achievement_apps:
            insert_or_update_achievement(date, appid, 0)
        for appid in new_playtime_apps:
            insert_or_update_playtime(date, appid, 0)

    # 補齊今天缺少的app
    for appid in yesterday_achievements:
        if appid not in achievements_today:
            achievements_today[appid] = yesterday_achievements[appid]

    for appid in yesterday_playtimes:
        if appid not in playtimes_today:
            playtimes_today[appid] = yesterday_playtimes[appid]

    # 寫入今天資料
    for appid, value in achievements_today.items():
        insert_or_update_achievement(today, appid, value)
    for appid, value in playtimes_today.items():
        insert_or_update_playtime(today, appid, value)

    log("✅ 今天的成就與遊玩時間資料更新完成")

if __name__ == '__main__':
    update_trends()
