# utils/import_game_titles_json.py

import os
import json
from utils.game_titles_db import save_game_title

def import_game_titles(json_path):
    if not os.path.exists(json_path):
        print(f"❌ 找不到檔案: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    count = 0
    for appid_str, names in data.items():
        appid = int(appid_str)
        en = names.get('en')
        tchinese = names.get('tchinese')
        japanese = names.get('japanese')
        save_game_title(appid, en, tchinese, japanese)
        count += 1

    print(f"✅ 成功匯入 {count} 筆遊戲標題資料到資料庫！")

if __name__ == "__main__":
    import_game_titles('./database/game_titles.json')
