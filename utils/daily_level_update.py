# utils/daily_level_update.py

import requests
import os
from datetime import datetime
from utils.level_history_db import save_level
from utils.steam_api import fetch_current_level

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
