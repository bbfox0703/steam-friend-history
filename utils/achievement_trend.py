import os
import json
from datetime import datetime
from utils.steam_api import fetch_recent_games, fetch_achievement_count

ACHIEVEMENT_PATH = './database/achievement_trend.json'
PLAYTIME_PATH = './database/playtime_trend.json'

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def update_trends():
    today = datetime.now().strftime('%Y-%m-%d')
    achievements_data = load_json(ACHIEVEMENT_PATH)
    playtime_data = load_json(PLAYTIME_PATH)

    games = fetch_recent_games()

    today_achievements = {}
    today_playtime = {}

    for game in games:
        appid = str(game.get('appid'))
        playtime = game.get('playtime_forever', 0)
        achievement_count = fetch_achievement_count(appid)
        today_achievements[appid] = achievement_count
        today_playtime[appid] = playtime

    achievements_data[today] = today_achievements
    playtime_data[today] = today_playtime

    save_json(ACHIEVEMENT_PATH, achievements_data)
    save_json(PLAYTIME_PATH, playtime_data)

if __name__ == '__main__':
    update_trends()
