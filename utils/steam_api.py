import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('STEAM_API_KEY')
STEAM_ID = os.getenv('STEAM_USER_ID')
DB_PATH = './database/friends.json'
BACKUP_DIR = './backups'

def fetch_friend_list():
    url = f"https://api.steampowered.com/ISteamUser/GetFriendList/v1/?key={API_KEY}&steamid={STEAM_ID}&relationship=friend"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Steam API Error: {response.status_code} {response.text}")
    return response.json().get('friendslist', {}).get('friends', [])

def fetch_friend_profiles(steam_ids):
    if not steam_ids:
        return {}
    ids_str = ','.join(steam_ids)
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={API_KEY}&steamids={ids_str}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Steam API Error: {response.status_code} {response.text}")
    players = response.json().get('response', {}).get('players', [])
    return {p['steamid']: p for p in players}

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

def update_friend_list():
    friend_list = fetch_friend_list()
    steam_ids = [f['steamid'] for f in friend_list]
    profiles = fetch_friend_profiles(steam_ids)

    enriched_friends = []
    for f in friend_list:
        sid = f['steamid']
        profile = profiles.get(sid, {})
        enriched_friends.append({
            'steamid': sid,
            'friend_since': f['friend_since'],
            'persona_name': profile.get('personaname', ''),
            'avatar': profile.get('avatar', ''),
            'profile_url': profile.get('profileurl', f'https://steamcommunity.com/profiles/{sid}')
        })

    save_friend_data(enriched_friends)
    backup_friend_data(enriched_friends)
    return len(enriched_friends)
