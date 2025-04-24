import os
import json
import requests
import time
import functools
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('STEAM_API_KEY')
STEAM_ID = os.getenv('STEAM_USER_ID')
DB_PATH = './database/friends.json'
HISTORY_PATH = './database/name_history.json'
CHANGELOG_PATH = './database/friend_changes.json'
BACKUP_DIR = './backups'

print = functools.partial(print, flush=True)

def fetch_friend_list():
    url = f"https://api.steampowered.com/ISteamUser/GetFriendList/v1/?key={API_KEY}&steamid={STEAM_ID}&relationship=friend"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Steam API Error: {response.status_code} {response.text}")
    return response.json().get('friendslist', {}).get('friends', [])


def fetch_friend_profiles(steam_ids):
    if not steam_ids:
        return {}

    result = {}
    for i in range(0, len(steam_ids), 100):
        batch = steam_ids[i:i + 100]
        ids_str = ','.join(batch)
        url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={API_KEY}&steamids={ids_str}"
        response = requests.get(url)

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

        time.sleep(0.5)

    return result


def try_restore_from_backup(sid, fields=("persona_name", "avatar"), lookback=10):
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
                        if all(entry.get(k) for k in fields):
                            return {k: entry[k] for k in fields}
        except:
            pass
    return {}


def get_friend_data():
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, 'r') as f:
        return json.load(f)


def save_friend_data(friend_list):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, 'w') as f:
        json.dump(friend_list, f, indent=2)


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

        if enriched['persona_name'] == '' or enriched['avatar'] == '':
            enriched['incomplete'] = True
            restored = try_restore_from_backup(sid)
            if restored:
                enriched.update(restored)
                enriched['restored'] = True

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
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Steam API Error: {response.status_code} {response.text}")
    return response.json().get("playerstats", {}).get("achievements", [])


def fetch_achievement_data(appid, steam_id=None):
    if steam_id is None:
        steam_id = STEAM_ID
    url = f"https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?key={API_KEY}&steamid={steam_id}&appid={appid}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Steam API Error: {response.status_code} {response.text}")
    return response.json().get("playerstats", {})


def load_game_title_cache():
    path = "./database/game_titles.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def fetch_owned_games(lang="en"):
    url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={API_KEY}&steamid={STEAM_ID}&include_appinfo=true&l={lang}"
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} fetch_owned_games(): {url}")
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Steam API Error: {response.status_code} {response.text}")
    return response.json().get("response", {}).get("games", [])

_game_title_cache = None

def get_game_title(appid: str) -> str:
    global _game_title_cache
    if _game_title_cache is None:
        _game_title_cache = load_game_title_cache()
    return _game_title_cache.get(str(appid), f"[AppID: {appid}]")


def fetch_game_info(appid, lang="en"):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l={lang}"
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


def fetch_store_name(appid: str, lang: str) -> str:
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l={lang}"
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} URL: {url}")
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json().get(str(appid), {}).get("data", {}).get("name", "")
    except Exception as e:
        print(f"❌ {appid} ({lang}) 錯誤: {e}")
    return ""
