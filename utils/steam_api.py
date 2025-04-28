import os
import json
import requests
import time
import functools
from datetime import datetime
from utils.game_titles_db import get_game_title as db_get_game_title, get_all_game_titles
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('STEAM_API_KEY')
STEAM_ID = os.getenv('STEAM_USER_ID')
DB_PATH = './database/friends.json'
HISTORY_PATH = './database/name_history.json'
CHANGELOG_PATH = './database/friend_changes.json'
BACKUP_DIR = './backups'

print = functools.partial(print, flush=True)

STORE_LANG_MAP = {
    "english": "en",
    "tchinese": "tchinese",
    "japanese": "japanese"
}

_cached_titles = None

# 抓所有遊戲標題 cache
def load_cached_titles():
    global _cached_titles
    if _cached_titles is None:
        _cached_titles = get_all_game_titles()
    return _cached_titles

def fetch_friend_list():
    url = f"https://api.steampowered.com/ISteamUser/GetFriendList/v1/?key={API_KEY}&steamid={STEAM_ID}&relationship=friend"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Steam API Error: {response.status_code} {response.text}")
    time.sleep(0.2)
    return response.json().get('friendslist', {}).get('friends', [])

def fetch_friend_profiles(steam_ids):
    if not steam_ids:
        return {}

    result = {}
    for i in range(0, len(steam_ids), 20):
        batch = steam_ids[i:i + 20]
        ids_str = ','.join(batch)
        url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={API_KEY}&steamids={ids_str}"
        response = requests.get(url)
        print(f"🔍 {time.strftime('%Y-%m-%d %H:%M:%S')} fetch_friend_profiles(), batch {i}: {url}")

        time.sleep(4)

        if response.status_code == 200:
            players = response.json().get('response', {}).get('players', [])
            for p in players:
                result[p['steamid']] = {
                    'personaname': p.get('personaname', ''),
                    'avatar': p.get('avatar', ''),
                    'profileurl': p.get('profileurl', ''),
                    'loccountrycode': p.get('loccountrycode', '??'),
                    'lastlogoff': p.get('lastlogoff'),
                    'personastate': p.get('personastate', 0)
                }
        else:
            print(f"⚠️ Failed batch {i} - Status {response.status_code} {response.text}")

    return result

def try_restore_from_backup(sid, fields=("persona_name", "avatar", "lastlogoff", "personastate"), lookback=10):
    files = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.startswith("friends_") and f.endswith(".json")],
        reverse=True
    )
    for filename in files[:lookback]:
        path = os.path.join(BACKUP_DIR, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for entry in data:
                    if entry.get("steamid") == sid:
                        if all(entry.get(k) is not None and entry.get(k) != '' for k in fields):
                            return {k: entry[k] for k in fields if k in entry}
        except Exception as e:
            print(f"⚠️ 無法從備份 {filename} 讀取 {sid}：{e}")
            continue
    return {}

def get_friend_data():
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, 'r') as f:
        return json.load(f)

def save_friend_data(friend_list):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    tmp_path = DB_PATH + ".tmp"
    with open(tmp_path, 'w') as f:
        json.dump(friend_list, f, indent=2)
    os.replace(tmp_path, DB_PATH)  # ✅ 原子替換，避免讀到寫到一半的檔案

def backup_friend_data(friend_list):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    path = os.path.join(BACKUP_DIR, f'friends_{timestamp}.json')
    with open(path, 'w') as f:
        json.dump(friend_list, f, indent=2)

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def update_friend_list():
    friend_list = fetch_friend_list()
    steam_ids = [f['steamid'] for f in friend_list]
    profiles = fetch_friend_profiles(steam_ids)

    old_friends = get_friend_data()
    old_dict = {f['steamid']: f for f in old_friends}
    old_ids = set(old_dict.keys())
    new_ids = set(steam_ids)

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    name_history = load_json(HISTORY_PATH)
    changes = load_json(CHANGELOG_PATH)
    added = sorted(list(new_ids - old_ids))
    removed = sorted(list(old_ids - new_ids))
    if added or removed:
        changes[now] = {"added": added, "removed": removed}

    enriched_friends = []
    for f in friend_list:
        sid = f['steamid']
        profile = profiles.get(sid, {})
        new_name = profile.get('personaname', '')
        old_name = old_dict.get(sid, {}).get('persona_name', '')

        if old_name and new_name and old_name != new_name:
            if sid not in name_history:
                name_history[sid] = []
            name_history[sid].append({
                'time': now,
                'old': old_name,
                'new': new_name
            })

        enriched = {
            'steamid': sid,
            'friend_since': f['friend_since'],
            'persona_name': new_name,
            'avatar': profile.get('avatar', ''),
            'profile_url': profile.get('profileurl', f'https://steamcommunity.com/profiles/{sid}'),
            'country_code': profile.get('loccountrycode', '??'),
            'lastlogoff': profile.get('lastlogoff'),
            'personastate': profile.get('personastate')
        }

        important_fields = ['persona_name', 'avatar', 'lastlogoff', 'personastate', 'country_code']

        # 判斷真正缺失的欄位（None 或 空字串）
        missing_keys = [
            k for k in important_fields
            if enriched.get(k) is None or enriched.get(k) == '' or (k == 'country_code' and enriched.get(k) == '??')
        ]

        if missing_keys:
            enriched['incomplete'] = True
            restored = try_restore_from_backup(sid, fields=missing_keys)
            if restored:
                enriched.update(restored)
                enriched['restored'] = True

                still_missing = [k for k in important_fields if enriched.get(k) is None or enriched.get(k) == '']
                if not still_missing:
                    enriched.pop('incomplete', None)

        enriched_friends.append(enriched)

    save_friend_data(enriched_friends)
    save_json(HISTORY_PATH, name_history)
    save_json(CHANGELOG_PATH, changes)
    backup_friend_data(enriched_friends)
    return len(enriched_friends)

def fetch_achievements(appid, steam_id=None):
    if steam_id is None:
        steam_id = STEAM_ID
    url = f"https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?key={API_KEY}&steamid={steam_id}&appid={appid}"
    print(f"🔍 {time.strftime('%Y-%m-%d %H:%M:%S')} fetch_achievements()")
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Steam API Error: {response.status_code} {response.text}")
    return response.json().get("playerstats", {}).get("achievements", [])


def fetch_achievement_data(appid, steam_id=None):
    if steam_id is None:
        steam_id = STEAM_ID
    url = f"https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?key={API_KEY}&steamid={steam_id}&appid={appid}"
    print(f"🔍 {time.strftime('%Y-%m-%d %H:%M:%S')} fetch_achievement_data()")
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Steam API Error: {response.status_code} {response.text}")
    return response.json().get("playerstats", {})


# 查目前持有的遊戲 (原本 fetch_owned_games 保留)
def fetch_owned_games(lang="en"):
    url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={API_KEY}&steamid={STEAM_ID}&include_appinfo=true&l={lang}"
    print(f"🔍 {time.strftime('%Y-%m-%d %H:%M:%S')} fetch_owned_games()")
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('response', {}).get('games', [])
    except Exception as e:
        print(f"⚠️ Fetch owned games error: {e}")
    return []    

# 查單個遊戲標題
def get_game_title(appid, lang='en'):
    return db_get_game_title(appid, lang)


def fetch_game_info(appid, lang="en"):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l={lang}"
    print(f"🔍 {time.strftime('%Y-%m-%d %H:%M:%S')} fetch_game_info(): {url}")
    try:
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json().get(str(appid), {}).get("data", {})
            return {
                "name": data.get("name", ""),
                "header_image": data.get("header_image", "")
            }
    except:
        pass
    return {"name": "", "header_image": ""}


# 查單個遊戲的Steam Store標題
def fetch_store_name(appid: str, lang: str) -> str:
    def query_store(appid, lang_code):
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l={lang_code}"
        print(f"🔍 {time.strftime('%Y-%m-%d %H:%M:%S')} fetch_store_name(): {url}")
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                app_info = data.get(str(appid), {})
                if not app_info.get("success"):
                    return None
                return app_info.get("data", {}).get("name")
        except Exception as e:
            print(f"❌ {appid} ({lang_code}) 錯誤: {e}")
        return None

    lang_code = STORE_LANG_MAP.get(lang, "en")

    # 第一次用目標語言查
    name = query_store(appid, lang_code)
    if name:
        return name

    # 如果失敗，再用英文查
    if lang_code != "en":
        time.sleep(2)
        name = query_store(appid, "en")
        if name:
            return name

    # 最後都查不到，返回空字串
    return ""

    
def fetch_recent_games():
    url = f"https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v1/?key={API_KEY}&steamid={STEAM_ID}"
    print(f"🔍 {time.strftime('%Y-%m-%d %H:%M:%S')} fetch_recent_games(): {url}")
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json().get('response', {}).get('games', [])
    return []

def fetch_achievement_count(appid):
    url = f"https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?key={API_KEY}&steamid={STEAM_ID}&appid={appid}"
    print(f"🔍 {time.strftime('%Y-%m-%d %H:%M:%S')} fetch_achievement_count(): {url}")
    resp = requests.get(url)
    if resp.status_code == 200:
        achievements = resp.json().get('playerstats', {}).get('achievements', [])
        unlocked = [a for a in achievements if a.get('achieved', 0) == 1]
        return len(unlocked)
    return 0
    
def fetch_current_level():
    url = f"https://api.steampowered.com/IPlayerService/GetSteamLevel/v1/?key={API_KEY}&steamid={STEAM_ID}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            level = data.get('response', {}).get('player_level')
            if level is not None:
                return level
            else:
                print("⚠️ player_level not found.")
        else:
            print(f"⚠️ HTTP Error {response.status_code}")
    except Exception as e:
        print(f"⚠️ Fetch Error: {e}")

    return None    
