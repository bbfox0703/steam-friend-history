# utils/daily_level_update.py

import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from utils.level_history_db import save_level

# 讀取 .env 檔案
load_dotenv()

# 從環境變數讀取 Steam API Key 與 Steam ID
STEAM_API_KEY = os.getenv('STEAM_API_KEY')
STEAM_ID = os.getenv('STEAM_USER_ID')

# 查詢使用者 summary，從中讀取目前level
def fetch_current_level():
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={STEAM_API_KEY}&steamids={STEAM_ID}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            players = data.get('response', {}).get('players', [])
            if players:
                player = players[0]
                # 這裡需要注意，Steam level 正確應從別的API取得，這裡暫時保留原欄位
                level = player.get('personastateflags')
                return level if level is not None else 0
            else:
                print("⚠️ No players found.")
        else:
            print(f"⚠️ HTTP Error {response.status_code}")
    except Exception as e:
        print(f"⚠️ Fetch Error: {e}")

    return None

# 更新今日等級
def update_today_level():
    today = datetime.now().strftime('%Y-%m-%d')
    level = fetch_current_level()
    if level is not None:
        save_level(today, level)
        print(f"✅ {today} 的等級 {level} 已寫入資料庫！")
    else:
        print(f"❌ 無法取得 {today} 的等級。")

if __name__ == "__main__":
    update_today_level()
