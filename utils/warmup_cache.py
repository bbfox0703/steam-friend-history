# utils/warmup_cache.py
# refresh db table game_info_cache
import time
import os

from utils.steam_api import fetch_game_info, fetch_owned_games

LOG_DIR = "./logs"
LOG_FILE = os.path.join(LOG_DIR, "warmup_cache.log")

def log(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")

def warmup_game_info_cache(langs=["en", "tchinese", "japanese"], sleep_time=5):
    log("♨️ 開始批次快取遊戲名稱...")
    owned_games = fetch_owned_games()
    time.sleep(1)
    for idx, game in enumerate(owned_games):
        appid = game.get("appid")
        for lang in langs:
            try:
                fetch_game_info(appid, lang)
                log(f"✅ [{idx+1}/{len(owned_games)}] AppID {appid} lang={lang} 快取完成")
                time.sleep(sleep_time)
            except Exception as e:
                log(f"⚠️ 無法快取 AppID {appid} lang={lang} - {e}")
    log("✅ 快取建構完成")

if __name__ == "__main__":
    warmup_game_info_cache()