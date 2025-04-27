# utils/import_level_history_json.py

import os
import json
from utils.level_history_db import save_level

def import_level_history(json_path):
    if not os.path.exists(json_path):
        print(f"❌ 找不到檔案: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    count = 0
    for date, level in data.items():
        save_level(date, level)
        count += 1

    print(f"✅ 成功匯入 {count} 筆等級資料到資料庫！")

if __name__ == "__main__":
    import_level_history('./database/level_history.json')
