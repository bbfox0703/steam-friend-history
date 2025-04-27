# utils/achievement_trend.py

import time
from datetime import datetime, timedelta
from utils.steam_api import fetch_recent_games, fetch_achievement_count
from utils.achievement_trend_db import save_playtime, save_achievement, get_playtime_by_date, get_achievements_by_date

# 每日更新成就與遊玩時間，並補齊資料
def update_trends():
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    # 從DB讀取昨天的成就與遊玩時間資料
    yesterday_achievements = get_achievements_by_date(yesterday)
    yesterday_playtimes = get_playtime_by_date(yesterday)

    # 取得今天從Steam API拉回的資料
    games = fetch_recent_games()

    today_achievements = {}
    today_playtime = {}

    for game in games:
        appid = str(game.get('appid'))
        playtime = game.get('playtime_forever', 0)
        achievement_count = fetch_achievement_count(appid)
        today_achievements[appid] = achievement_count
        today_playtime[appid] = playtime
        time.sleep(1.1)

    # 補齊今天沒有資料的AppID (成就)
    for appid, count in yesterday_achievements.items():
        if appid not in today_achievements:
            today_achievements[appid] = count

    # 補齊今天沒有資料的AppID (遊玩時間)
    for appid, minutes in yesterday_playtimes.items():
        if appid not in today_playtime:
            today_playtime[appid] = minutes

    # 寫入DB
    for appid_str, achievements in today_achievements.items():
        save_achievement(today, int(appid_str), achievements)

    for appid_str, minutes in today_playtime.items():
        save_playtime(today, int(appid_str), minutes)

    print(f"✅ Trends updated for {today}.")

if __name__ == '__main__':
    update_trends()
