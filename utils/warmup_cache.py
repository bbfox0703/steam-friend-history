# utils/warmup_cache.py
# refresh db table game_info_cache
import time
import os

from utils.api_utils import log
from utils.steam_api import fetch_game_info, fetch_owned_games

def warmup_game_info_cache(langs=["en", "tchinese", "japanese"], sleep_time=1):
    log("♨️ 開始批次快取遊戲名稱...")
    owned_games = fetch_owned_games()
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
