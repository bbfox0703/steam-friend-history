from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for
import utils.steam_api as steam_api
import utils.backup as backup
import json
import os
from datetime import datetime
from collections import defaultdict, Counter
import operator

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

    # 補充 steamid 對應的名稱與加入時間
    friend_data = steam_api.get_friend_data()
    id_map = {f['steamid']: f for f in friend_data}

    for timestamp, change in changes.items():
        if "added" in change:
            change["added_info"] = []
            for sid in change["added"]:
                info = id_map.get(sid, {})
                change["added_info"].append({
                    "steamid": sid,
                    "persona_name": info.get("persona_name", "[未知名稱]"),
                    "profile_url": info.get("profile_url", f"https://steamcommunity.com/profiles/{sid}"),
                    "friend_since": info.get("friend_since", 0)
                })

    return render_template("history.html", name_history=name_history, changes=changes)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
