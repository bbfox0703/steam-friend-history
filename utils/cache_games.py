# utils/cache_games.py

import argparse
import json
import os
import time
from datetime import datetime
from utils.steam_api import fetch_owned_games, fetch_store_name
from utils.game_titles_db import save_game_title, get_all_game_titles

import functools
print = functools.partial(print, flush=True)

UNAVAILABLE_FILE = "./database/unavailable_titles.json"

LANGUAGES = ['en', 'tchinese', 'japanese']

LOG_DIR = "./logs"
LOG_FILE = os.path.join(LOG_DIR, "cache_games.log")

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

def update_cached_game_titles(langs, sleep_time=4):
    log("🔍 讀取目前持有遊戲清單...")
    owned_games = fetch_owned_games()
    log(f"✅ 共 {len(owned_games)} 個遊戲將進行更新")

    existing_data = get_all_game_titles()
    unavailable = load_unavailable_titles()

    for idx, game in enumerate(owned_games):
        appid = game.get('appid')
        en_name = game.get('name')
        if not appid:
            continue

        appid_str = str(appid)

        if appid_str in unavailable:
            log(f"⚡ [{idx+1}/{len(owned_games)}] AppID {appid} 已列為unavailable，跳過")
            continue

        existing = existing_data.get(appid_str, {})

        updated_titles = {
            'en': existing.get('en') or en_name,
            'tchinese': existing.get('tchinese'),
            'japanese': existing.get('japanese')
        }

        if all(updated_titles.get(lang) for lang in langs):
            log(f"✅ [{idx+1}/{len(owned_games)}] AppID {appid} 所有語系已存在，跳過")
            continue

        for lang in langs:
            if lang == 'en':
                continue
            if not updated_titles.get(lang):
                store_lang = lang
                name = fetch_store_name(appid, store_lang)
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if name:
                    log(f"✅ {timestamp} [{idx+1}/{len(owned_games)}] {appid} ({lang}): {name}")
                    updated_titles[lang] = name
                else:
                    log(f"⚠️ {timestamp} [{idx+1}/{len(owned_games)}] {appid} ({lang}): 無法取得標題")
                    unavailable[appid_str] = datetime.today().strftime("%Y-%m-%d")
                time.sleep(sleep_time)  # ← 檢查是否仍需要

        save_game_title(appid,
                        updated_titles.get('en'),
                        updated_titles.get('tchinese'),
                        updated_titles.get('japanese'))

    save_unavailable_titles(unavailable)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='更新 Steam 遊戲標題快取')
    parser.add_argument('--lang', type=str, default='all', help='語言選擇：en, tchinese, japanese, 或 all')
    parser.add_argument('--sleep', type=float, default=4, help='每次API呼叫後睡眠秒數，避免被封鎖')
    args = parser.parse_args()

    if args.lang == 'all':
        langs = LANGUAGES
    else:
        langs = [args.lang] if args.lang in LANGUAGES else ['en']

    update_cached_game_titles(langs, args.sleep)
