# utils/daily_level_update.py

import requests
import os
import time
from datetime import datetime
from utils.level_history_db import save_level
from utils.steam_api import fetch_current_level

LOG_DIR = "./logs"
LOG_FILE = os.path.join(LOG_DIR, "daily_level_update.log")

def log(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")

# 更新今日等級
def update_today_level():
    today = datetime.now().strftime('%Y-%m-%d')
    level = fetch_current_level()
    if level is not None:
        save_level(today, level)
        log(f"✅ {today} 的等級 {level} 已寫入資料庫！")
    else:
        log(f"❌ 無法取得 {today} 的等級。")

if __name__ == "__main__":
    update_today_level()
