import os
import json
import time
import argparse
from dotenv import load_dotenv

# 動態引入 steam_api，兼容模組與獨立執行
try:
    from . import steam_api
except ImportError:
    import utils.steam_api as steam_api

# 自動載入環境變數
load_dotenv()

# 🔐 基於當前文件位置，確保存儲路徑穩定（無論在哪裡執行都正確）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_PATH = os.path.join(BASE_DIR, "database", "game_titles.json")

SUPPORTED_LANGS = ["en", "tchinese", "japanese"]


def fetch_and_cache_games(lang="en", sleep_interval=1):
    print(f"🌐 正在抓取語言：{lang}")
    games = steam_api.fetch_owned_games(lang=lang)
    print(f"📋 獲得 {len(games)} 筆遊戲（{lang}）")

    data = {}
    for i, game in enumerate(games):
        appid = str(game["appid"])
        name = game.get("name", "")
        if appid not in data:
            data[appid] = {}
        data[appid][lang] = name
        print(f"✅ [{i+1}/{len(games)}] {appid} ({lang}): {name}")
        time.sleep(sleep_interval)

    return data


def build_game_title_cache(langs=["en"], sleep_interval=1):
    print("🚀 開始建立遊戲名稱多語系快取...")

    # 載入現有快取（如果有的話）
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            merged = json.load(f)
    else:
        merged = {}

    for lang in langs:
        partial = fetch_and_cache_games(lang=lang, sleep_interval=sleep_interval)
        for appid, names in partial.items():
            if appid not in merged:
                merged[appid] = {}
            merged[appid].update(names)

    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    print(f"📦 快取已儲存：{CACHE_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", nargs="*", default=["en"], choices=SUPPORTED_LANGS + ["all"],
                        help="指定要抓取的語言，例如 --lang en 或 --lang all")
    parser.add_argument("--sleep", type=float, default=1.0, help="每筆遊戲間的延遲秒數，預設為 1")
    args = parser.parse_args()

    langs = SUPPORTED_LANGS if "all" in args.lang else args.lang
    build_game_title_cache(langs=langs, sleep_interval=args.sleep)
