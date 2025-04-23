from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template
import utils.steam_api as steam_api
import utils.backup as backup
import json
import os
from datetime import datetime
from collections import defaultdict, Counter

def load_data():
    path = os.path.join('database', 'friend_data.json')
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

    return render_template("history.html", name_history=name_history, changes=changes)

@app.route('/country')
def country():
    friends = load_data()
    country_counts = {}
    country_members = {}

    for f in friends:
        code = f.get('country_code', '??')
        country_counts[code] = country_counts.get(code, 0) + 1
        country_members.setdefault(code, []).append(f)

    sort_mode = request.args.get('sort', 'count')  # 預設依人數
    if sort_mode == 'name':
        sorted_items = sorted(country_counts.items(), key=lambda x: x[0])
    else:
        sorted_items = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)

    return render_template("country.html",
                           sorted_items=sorted_items,
                           country_members=country_members,
                           sort_mode=sort_mode)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
