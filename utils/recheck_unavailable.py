# utils/recheck_unavailable.py

import json
import os
import time
from datetime import datetime, timedelta
from utils.steam_api import fetch_store_name

UNAVAILABLE_FILE = "./database/unavailable_titles.json"

LOG_DIR = "./logs"
LOG_FILE = os.path.join(LOG_DIR, "recheck_unavailable.log")

def log(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")

def load_unavailable_titles():
    if os.path.exists(UNAVAILABLE_FILE):
        with open(UNAVAILABLE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {}

def save_unavailable_titles(unavailable):
    with open(UNAVAILABLE_FILE, "w", encoding="utf-8") as f:
        json.dump(unavailable, f, ensure_ascii=False, indent=2)

def recheck_unavailable(days_threshold=30):
    unavailable = load_unavailable_titles()
    today = datetime.today()
    updated = {}

    log(f"🔍 開始重新檢查 unavailable appids（超過 {days_threshold} 天）...")

    for appid, date_str in unavailable.items():
        try:
            last_checked = datetime.strptime(date_str, "%Y-%m-%d")
            if (today - last_checked).days < days_threshold:
                updated[appid] = date_str
                continue

            # recheck
            name = fetch_store_name(appid, "en")
            if name:
                log(f"✅ AppID {appid} 已恢復！標題：{name}")
            else:
                log(f"⚠️ AppID {appid} 仍然無法取得，保留")
                updated[appid] = today.strftime("%Y-%m-%d")
            time.sleep(2)    
        except Exception as e:
            log(f"❌ AppID {appid} 檢查失敗: {e}")
            updated[appid] = today.strftime("%Y-%m-%d")

    save_unavailable_titles(updated)
    log("✅ unavailable_titles.json 已更新完成！")

if __name__ == "__main__":
    recheck_unavailable(30)
