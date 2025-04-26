# 遊玩時間假資料生成
# Container:
# cd /app
# /usr/local/bin/python3 -m utils.backfill_fake_data

import os
import json
import random
from datetime import datetime, timedelta

# 路徑設定
ACHIEVEMENT_PATH = './database/achievement_trend.json'
PLAYTIME_PATH = './database/playtime_trend.json'

# 模擬的遊戲 appid 列表（自己可以換成真實常玩的遊戲ID）
sample_appids = [
    "480", "730", "570", "440", "578080", "252490", "271590"
]

# 生成的天數
DAYS = 14

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def backfill():
    achievement_data = load_json(ACHIEVEMENT_PATH)
    playtime_data = load_json(PLAYTIME_PATH)

    base_achievements = {appid: random.randint(0, 20) for appid in sample_appids}
    base_playtime = {appid: random.randint(100, 1000) for appid in sample_appids}

    for i in range(DAYS, 0, -1):
        day = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        achievement_entry = {}
        playtime_entry = {}

        for appid in sample_appids:
            # 成就數增加 0~5個
            base_achievements[appid] += random.randint(0, 5)
            # 遊玩時間增加10~120分鐘
            base_playtime[appid] += random.randint(10, 120)

            achievement_entry[appid] = base_achievements[appid]
            playtime_entry[appid] = base_playtime[appid]

        achievement_data[day] = achievement_entry
        playtime_data[day] = playtime_entry

    # 最後補上今天
    today = datetime.now().strftime('%Y-%m-%d')
    achievement_data[today] = {appid: base_achievements[appid] + random.randint(0, 3) for appid in sample_appids}
    playtime_data[today] = {appid: base_playtime[appid] + random.randint(5, 60) for appid in sample_appids}

    save_json(ACHIEVEMENT_PATH, achievement_data)
    save_json(PLAYTIME_PATH, playtime_data)
    print("✅ backfill完成！生成了 {} 天資料".format(DAYS + 1))

if __name__ == '__main__':
    backfill()
