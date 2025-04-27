from utils.achievement_trend_db import save_achievement
import json
import os

def import_achievement_json(json_path):
    if not os.path.exists(json_path):
        print(f"找不到 {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        achievement_data = json.load(f)

    for date, apps in achievement_data.items():
        for appid_str, achievements in apps.items():
            appid = int(appid_str)
            save_achievement(date, appid, achievements)

    print(f"✅ 匯入完成，共 {len(achievement_data)} 天資料。")

if __name__ == "__main__":
    import_achievement_json('./database/achievement_trend.json')
