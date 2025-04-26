# 個別遊玩時間假資料生成
# Container:
# cd /app
# /usr/local/bin/python3 -m utils.backfill_fake_gameplay
import json
from datetime import datetime, timedelta

# 讀取原本的 playtime_trend.json
with open('./database/playtime_trend.json', 'r', encoding='utf-8') as f:
    playtime_data = json.load(f)

appid = "22330"
start_date = datetime(2025, 4, 20)
end_date = datetime(2025, 4, 26)

# 假設初始遊玩時間
base_playtime = 100

for i in range((end_date - start_date).days + 1):
    day = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')

    if day not in playtime_data:
        playtime_data[day] = {}

    # 如果當天已經有 22330，略過也可以，但通常是直接覆蓋比較乾淨
    playtime_data[day][appid] = base_playtime

    # 每天玩隨機 40~80 分鐘（可以自己調）
    base_playtime += 40 + i * 10

# 儲存回 playtime_trend.json
with open('./database/playtime_trend.json', 'w', encoding='utf-8') as f:
    json.dump(playtime_data, f, indent=2, ensure_ascii=False)

print("✅ 測試資料已產生完成！")
