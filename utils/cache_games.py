import os
import json
import time
import argparse
from dotenv import load_dotenv

#python3 utils/cache_games.py --lang en
#python3 utils/cache_games.py --lang tchinese
#python3 utils/cache_games.py --lang japanese

# 自動載入環境變數
load_dotenv()

# 嘗試動態引入 steam_api（支援模組與 CLI 執行）
try:
    from . import steam_api
except ImportError:
    import utils.steam_api as steam_api

# 路徑配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_PATH = os.path.join(BASE_DIR, "database", "game_titles.json")

def fetch_and_cache_games(lang="en", sleep_interval=1.0):
    games = steam_api.fetch_owned_games(lang=lang)
    print(f"🌐 抓取語言：{lang}，共 {len(games)} 筆")

    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
    else:
        cache = {}

    for i, game in enumerate(games):
        appid = str(game["appid"])
        name = game.get("name", "")
        if not name:
            continue

        if appid not in cache:
            cache[appid] = {}
        if lang not in cache[appid]:
            cache[appid][lang] = name
            print(f"✅ [{i+1}/{len(games)}] {appid} - {lang}: {name}")
        else:
            print(f"⏩ [{i+1}/{len(games)}] {appid} - {lang} 已存在，略過")

        time.sleep(sleep_interval)

    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
    print(f"📦 已儲存至：{CACHE_PATH}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", choices=["en", "tchinese", "japanese"], default="en", help="語言代碼")
    parser.add_argument("--sleep", type=float, default=1.0, help="每筆資料延遲秒數")
    args = parser.parse_args()

    fetch_and_cache_games(lang=args.lang, sleep_interval=args.sleep)
