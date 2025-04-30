import os
import time
from datetime import datetime, timedelta
from utils.db import (
    get_achievements_by_date,
    get_playtime_by_date,
    get_all_dates,
    insert_or_update_achievement,
    insert_or_update_playtime,
    get_connection
)
from utils.steam_api import fetch_recent_games, fetch_achievement_summary

LOG_DIR = "./logs"
LOG_FILE = os.path.join(LOG_DIR, "achievement_trend.log")

def log(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")

def find_nearest_available_day(table: str, before_day: str) -> str | None:
    conn = get_connection()
    c = conn.cursor()

    check_day = datetime.strptime(before_day, "%Y-%m-%d")
    while True:
        day_str = check_day.strftime("%Y-%m-%d")
        c.execute(f'SELECT COUNT(*) FROM {table} WHERE date = ?', (day_str,))
        count = c.fetchone()[0]
        if count > 0:
            conn.close()
            return day_str
        check_day -= timedelta(days=1)
        if check_day.year < 2000:
            conn.close()
            return None  # 保險：找不到任何資料

def update_trends():
    today = datetime.today().strftime('%Y-%m-%d')
    yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')

    log(f"📈 更新成就與遊玩時間趨勢 - {today}")

    # 成就資料
    try:
        nearest_day_achievements = find_nearest_available_day('achievement_trend', yesterday)
        if nearest_day_achievements:
            yesterday_achievements = get_achievements_by_date(nearest_day_achievements) or {}
            log(f"📅 成就資料使用最近的 {nearest_day_achievements}")
        else:
            yesterday_achievements = {}
            log(f"⚠️ 沒有任何成就歷史資料，視為空集合")
    except Exception as e:
        yesterday_achievements = {}
        log(f"⚠️ 成就資料讀取錯誤: {e}，使用空集合")

    # 遊玩時間資料
    try:
        nearest_day_playtimes = find_nearest_available_day('playtime_trend', yesterday)
        if nearest_day_playtimes:
            yesterday_playtimes = get_playtime_by_date(nearest_day_playtimes) or {}
            log(f"📅 遊玩時間資料使用最近的 {nearest_day_playtimes}")
        else:
            yesterday_playtimes = {}
            log(f"⚠️ 沒有任何遊玩時間歷史資料，視為空集合")
    except Exception as e:
        yesterday_playtimes = {}
        log(f"⚠️ 遊玩時間資料讀取錯誤: {e}，使用空集合")

    # 抓今天 Steam 資料
    recent_games = fetch_recent_games() or []
    log(f"🎮 抓到最近遊玩 {len(recent_games)} 款遊戲")

    achievements_today = {}
    playtimes_today = {}

    for idx, game in enumerate(recent_games):
        appid = game['appid']
        playtime = game.get('playtime_forever', 0)

        try:
            achievement_summary = fetch_achievement_summary(appid)
            if achievement_summary:
                unlocked_count = achievement_summary.get('unlocked', 0)
            else:
                unlocked_count = 0
            achievements_today[str(appid)] = unlocked_count

        except Exception as e:
            log(f"⚠️ AppID {appid} 抓成就失敗: {e}")
            achievements_today[str(appid)] = 0

        playtimes_today[str(appid)] = playtime

        if idx % 3 == 0:
            time.sleep(3)

    log(f"🎯 成就 {len(achievements_today)} 筆，遊玩時間 {len(playtimes_today)} 筆")

    # 新出現 AppID
    new_achievement_apps = set(achievements_today.keys()) - set(yesterday_achievements.keys())
    new_playtime_apps = set(playtimes_today.keys()) - set(yesterday_playtimes.keys())

    if new_achievement_apps:
        log(f"➕ 新成就AppID: {', '.join(map(str, new_achievement_apps))}")
    if new_playtime_apps:
        log(f"➕ 新遊玩時間AppID: {', '.join(map(str, new_playtime_apps))}")

    all_dates = get_all_dates()
    if not all_dates:
        all_dates = [yesterday]
        log(f"📅 資料庫無歷史日期，初始化為昨日 {yesterday}")

    for appid in yesterday_achievements:
        if appid not in achievements_today:
            achievements_today[appid] = yesterday_achievements[appid]

    for appid in yesterday_playtimes:
        if appid not in playtimes_today:
            playtimes_today[appid] = yesterday_playtimes[appid]

    log(f"🔄 對歷史日期回填: {', '.join(all_dates)}")

    # ✅ 用今天的值補過去日期（避免補 0）
    for date in all_dates:
        for appid in new_achievement_apps:
            value = achievements_today.get(appid, 0)
            insert_or_update_achievement(date, appid, value)
        for appid in new_playtime_apps:
            value = playtimes_today.get(appid, 0)
            insert_or_update_playtime(date, appid, value)

    for appid, value in achievements_today.items():
        current = get_achievements_by_date(today).get(str(appid), None)

        if current is None:
            insert_or_update_achievement(today, appid, value)
        else:
            if value != current:
                insert_or_update_achievement(today, appid, value)
            else:
                log(f"🛑 AppID {appid} 成就數未變 ({value})，跳過更新")

    for appid, value in playtimes_today.items():
        insert_or_update_playtime(today, appid, value)

    log("✅ 今日資料更新完成")

if __name__ == "__main__":
    update_trends()
