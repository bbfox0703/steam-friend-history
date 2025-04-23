import os
import json
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('STEAM_API_KEY')
STEAM_ID = os.getenv('STEAM_USER_ID')
DB_PATH = './database/friends.json'
HISTORY_PATH = './database/name_history.json'
CHANGELOG_PATH = './database/friend_changes.json'
BACKUP_DIR = './backups'

def fetch_friend_list():
    url = f"https://api.steampowered.com/ISteamUser/GetFriendList/v1/?key={API_KEY}&steamid={STEAM_ID}&relationship=friend"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Steam API Error: {response.status_code} {response.text}")
    return response.json().get('friendslist', {}).get('friends', [])

import time

def fetch_friend_profiles(steam_ids):
    if not steam_ids:
        return {}

    result = {}
    for i in range(0, len(steam_ids), 100):
        batch = steam_ids[i:i+100]
        ids_str = ','.join(batch)
        url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={API_KEY}&steamids={ids_str}"
        response = requests.get(url)

        if response.status_code == 200:
            players = response.json().get('response', {}).get('players', [])
            for p in players:
                result[p['steamid']] = p
        else:
            print(f"⚠️ Failed batch {i} - Status {response.status_code}")

        time.sleep(0.3)

    return result

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

def update_trend_log(enriched_friends):
    path = "database/friend_trend.json"
    data = {}

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

    for f in enriched_friends:
        ts = datetime.fromtimestamp(int(f.get("friend_since", 0))).strftime("%Y-%m-%d")
        data[ts] = data.get(ts, 0) + 1

    with open(path, "w", encoding="utf-8") as f:
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

    # 比對名字變更
    name_history = load_json(HISTORY_PATH)

    # 比對好友增減
    changes = load_json(CHANGELOG_PATH)
    added = sorted(list(new_ids - old_ids))
    removed = sorted(list(old_ids - new_ids))
    if added or removed:
        changes[now] = {"added": added, "removed": removed}

    # 建立 enriched_friends 資料
    enriched_friends = []
    for f in friend_list:
        sid = f['steamid']
        profile = profiles.get(sid, {})
        new_name = profile.get('personaname', '')
        old_name = old_dict.get(sid, {}).get('persona_name', '')

        # 記錄暱稱變更
        if old_name and new_name and old_name != new_name:
            if sid not in name_history:
                name_history[sid] = []
            name_history[sid].append({
                'time': now,
                'old': old_name,
                'new': new_name
            })

        enriched_friends.append({
            'steamid': sid,
            'friend_since': f['friend_since'],
            'persona_name': new_name,
            'avatar': profile.get('avatar', ''),
            'profile_url': profile.get('profileurl', f'https://steamcommunity.com/profiles/{sid}'),
            'country_code': profile.get('loccountrycode', '??')
        })

    save_friend_data(enriched_friends)
    save_json(HISTORY_PATH, name_history)
    save_json(CHANGELOG_PATH, changes)
    backup_friend_data(enriched_friends)
    update_trend_log(enriched_friends)
    return len(enriched_friends)
