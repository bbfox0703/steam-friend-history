#
# 補齊昨天有、但今天沒有的appid成就資料
#
import os
import json
from datetime import datetime, timedelta

def main():
    db_path = "./database/achievement_trend.json"

    if not os.path.exists(db_path):
        print("⚠️ No achievement_trend.json found")
        return

    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    today = datetime.today().strftime("%Y-%m-%d")
    yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    if yesterday not in data or today not in data:
        print("⚠️ Missing yesterday or today data, skip filling")
        return

    yesterday_data = data[yesterday]
    today_data = data[today]

    # 將昨天有但今天沒有的 appid補進來
    for appid, val in yesterday_data.items():
        if appid not in today_data:
            today_data[appid] = val

    # 保存回原檔案
    data[today] = today_data

    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ Achievement data filled successfully.")

if __name__ == "__main__":
    main()
