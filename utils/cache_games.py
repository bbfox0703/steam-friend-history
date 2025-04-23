import os
import json
import time
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

def fetch_owned_games():
    return steam_api.fetch_owned_games()  # 從 steam_api 共用

def build_game_title_cache():
    print("🚀 正在建立遊戲名稱快取中...")
    games = fetch_owned_games()
    print(f"🔍 共 {len(games)} 筆遊戲")

    appid_map = {}
    for i, game in enumerate(games):
        appid = str(game["appid"])
        name = game.get("name", "")
        appid_map[appid] = name
        print(f"✅ [{i+1}/{len(games)}] {appid}: {name}")
        time.sleep(1)  # 每秒一個請求，避免觸發 API 限制

    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(appid_map, f, indent=2, ensure_ascii=False)
    print(f"📦 完成快取儲存：{CACHE_PATH}")

if __name__ == "__main__":
    build_game_title_cache()
