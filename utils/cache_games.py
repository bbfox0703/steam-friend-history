# utils/cache_games.py

import argparse
import time
from datetime import datetime
from utils.steam_api import fetch_owned_games, fetch_store_name
from utils.game_titles_db import save_game_title, get_all_game_titles

# 支援的語系
LANGUAGES = {
    'en': 'en',
    'tchinese': 'zh-tw',
    'japanese': 'ja'
}

def update_cached_game_titles(langs, sleep_time):
    print("🔍 讀取目前持有遊戲清單...")
    owned_appids = fetch_owned_games()
    print(f"✅ 共 {len(owned_appids)} 個遊戲將進行更新")

    # 從資料庫讀取已存在的標題資料
    existing_data = get_all_game_titles()

    for idx, appid in enumerate(owned_appids):
        appid_str = str(appid)
        existing = existing_data.get(appid_str, {})

        # 如果所有語系都存在，跳過
        if all(existing.get(lang) for lang in langs):
            print(f"✅ [{idx+1}/{len(owned_appids)}] AppID {appid} 所有語系已存在，跳過")
            continue

        # 建立更新後的標題資料
        updated_titles = {
            'en': existing.get('en'),
            'tchinese': existing.get('tchinese'),
            'japanese': existing.get('japanese')
        }

        for lang in langs:
            if not updated_titles.get(lang):
                store_lang = LANGUAGES.get(lang, 'en')
                name = fetch_store_name(appid, store_lang)
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if name:
                    print(f"✅ {timestamp} [{idx+1}/{len(owned_appids)}] {appid} ({lang}): {name}")
                    updated_titles[lang] = name
                else:
                    print(f"⚠️ {timestamp} [{idx+1}/{len(owned_appids)}] {appid} ({lang}): 無法取得標題")
                time.sleep(sleep_time)

        # 寫入資料庫
        save_game_title(appid,
                        updated_titles.get('en'),
                        updated_titles.get('tchinese'),
                        updated_titles.get('japanese'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='更新 Steam 遊戲標題快取')
    parser.add_argument('--lang', type=str, default='all', help='語言選擇：en, tchinese, japanese, 或 all')
    parser.add_argument('--sleep', type=float, default=1.0, help='每次API呼叫後睡眠秒數，避免被封鎖')
    args = parser.parse_args()

    if args.lang == 'all':
        langs = list(LANGUAGES.keys())
    else:
        langs = [args.lang] if args.lang in LANGUAGES else ['en']

    update_cached_game_titles(langs, args.sleep)