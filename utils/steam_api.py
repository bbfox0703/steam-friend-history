import os
import json
import requests
from datetime import datetime

API_KEY = os.getenv('STEAM_API_KEY')
STEAM_ID = os.getenv('STEAM_USER_ID')
DB_PATH = './database/friends.json'

def fetch_friend_list():
    url = f"https://api.steampowered.com/ISteamUser/GetFriendList/v1/?key={API_KEY}&steamid={STEAM_ID}&relationship=friend"
    response = requests.get(url)
    data = response.json()
    return data.get('friendslist', {}).get('friends', [])

def get_friend_data():
    if not os.path.exists(DB_PATH):
        return []

    with open(DB_PATH, 'r') as f:
        return json.load(f)

def save_friend_data(friend_list):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, 'w') as f:
        json.dump(friend_list, f, indent=2)

def update_friend_list():
    new_list = fetch_friend_list()
    save_friend_data(new_list)
    return len(new_list)
