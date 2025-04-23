from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for
import utils.steam_api as steam_api
import utils.backup as backup
import pandas as pd
import json
import os
import operator
from datetime import datetime
from collections import defaultdict, Counter

def load_data():
    path = os.path.join('database', 'friends.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

app = Flask(__name__)
import os
# print("=== API_KEY Loaded ===", os.getenv('STEAM_API_KEY'))
# print("=== STEAM_USER_ID Loaded ===", os.getenv('STEAM_USER_ID'))

@app.template_filter('datetimeformat')
def datetimeformat(ts):
    try:
        return datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d')
    except:
        return ts


@app.route('/')
def index():
    data = steam_api.get_friend_data()
    return render_template('index.html', data=data)

@app.route('/update')
def update():
    result = steam_api.update_friend_list()
    backup.backup_today()
    return {'status': 'ok', 'updated': result}

@app.route("/history")
def history():
    try:
        with open("database/name_history.json", "r") as f:
            name_history = json.load(f)
    except:
        name_history = {}

    try:
        with open("database/friend_changes.json", "r") as f:
            changes = json.load(f)
    except:
        changes = {}

    join_sort = request.args.get("join_sort", "new")
    reverse = (join_sort == "new")

    all_friends = steam_api.get_friend_data()
    friend_map = {f["steamid"]: f for f in all_friends}

    # 加入歷史備份資料
    backup_dir = "./backups"
    if os.path.exists(backup_dir):
        for file in os.listdir(backup_dir):
            if file.startswith("friends_") and file.endswith(".json"):
                with open(os.path.join(backup_dir, file), "r") as bf:
                    try:
                        data = json.load(bf)
                        for f in data:
                                if f["steamid"] not in friend_map:
                                    friend_map[f["steamid"]] = f
                    except:
                        pass

    for ts, change in changes.items():
        for sid in change.get("added", []):
            if sid not in friend_map:
                print(f"❗️ {sid} not found in friend_map (added)")      
                
        added_info = []
        for sid in change.get("added", []):
            f = friend_map.get(sid)
            if f:
                print(f"🧪 SID: {sid} name: {f.get('persona_name')}")
                added_info.append(f)
        added_info.sort(key=lambda f: int(f.get("friend_since", 0)), reverse=reverse)
        change["added_info"] = added_info

        removed_info = []
        for sid in change.get("removed", []):
            f = friend_map.get(sid, {"steamid": sid})
            removed_info.append(f)
        removed_info.sort(key=lambda f: int(f.get("friend_since", 0)), reverse=reverse)
        change["removed_info"] = removed_info

    return render_template("history.html",
                           name_history=name_history,
                           changes=changes,
                           friend_map=friend_map,
                           join_sort=join_sort)

@app.route("/country")
def country():
    sort_mode = request.args.get("sort", "count")
    friends = load_data()

    country_members = defaultdict(list)
    for f in friends:
        code = f.get("country_code", "??")
        country_members[code].append(f)

    # 正確處理排序所需資料
    sorted_items = [(code, len(friends)) for code, friends in country_members.items()]
    if sort_mode == "name":
        sorted_items.sort(key=lambda x: x[0])
    else:
        sorted_items.sort(key=lambda x: x[1], reverse=True)

    return render_template("country.html",
                           sorted_items=sorted_items,
                           country_members=country_members,
                           sort_mode=sort_mode)

@app.route("/filter")
def filter():
    import flask
    try:
        with open("database/friends.json", "r") as f:
            friends = json.load(f)
    except:
        friends = []

    mode = flask.request.args.get("mode", "all")

    if mode == "named":
        friends = [f for f in friends if f.get("persona_name") and f.get("avatar")]
    elif mode == "with_country":
        friends = [f for f in friends if f.get("country_code") and f.get("country_code") != "??"]

    return render_template("filter.html", friends=friends, mode=mode)

@app.route("/trend")
def trend():
    mode = request.args.get("mode", "month")  # 預設為月份

    # 讀取 friends.json 作為新增好友依據
    friends_path = "database/friends.json"
    if not os.path.exists(friends_path):
        return "尚無統計資料"

    with open(friends_path, "r", encoding="utf-8") as f:
        friends_raw = json.load(f)

    # 讀取 friend_changes.json 來補上移除好友資訊
    changes_path = "database/friend_changes.json"
    changes_raw = {}
    if os.path.exists(changes_path):
        with open(changes_path, "r", encoding="utf-8") as f:
            changes_raw = json.load(f)

    records = []

    # 來自 friends.json 的新增好友（可能不完整，只是目前還在的）
    for f in friends_raw:
        try:
            ts = int(f.get("friend_since", 0))
            if ts == 0:
                continue
            date = datetime.fromtimestamp(ts)
            records.append({"date": date, "added": 1, "removed": 0})
        except:
            continue

    # 來自 friend_changes.json 的移除好友（歷史紀錄）
    for ts, change in changes_raw.items():
        try:
            date = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            removed = len(change.get("removed", []))
            if removed > 0:
                records.append({"date": date, "added": 0, "removed": removed})
        except:
            continue

    df = pd.DataFrame(records)
    if df.empty:
        return "尚無可視覺化的統計資料"

    # 分群處理
    if mode == "day":
        df["group"] = df["date"].dt.to_period("D")
        full_range = pd.period_range(start=df["group"].min(), end=df["group"].max(), freq="D")
    elif mode == "year":
        df["group"] = df["date"].dt.to_period("Y")
        full_range = pd.period_range(start=df["group"].min(), end=df["group"].max(), freq="Y")
    else:
        df["group"] = df["date"].dt.to_period("M")
        full_range = pd.period_range(start=df["group"].min(), end=df["group"].max(), freq="M")

    stat = df.groupby("group")[["added", "removed"]].sum()
    stat = stat.reindex(full_range, fill_value=0).reset_index()
    stat.rename(columns={"index": "group"}, inplace=True)
    stat["group"] = stat["group"].astype(str)

    return render_template("trend.html", stats=stat.to_dict(orient="records"), mode=mode)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
