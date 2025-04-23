from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template
import utils.steam_api as steam_api
import utils.backup as backup
from datetime import datetime
from collections import defaultdict, Counter

app = Flask(__name__)
import os
# print("=== API_KEY Loaded ===", os.getenv('STEAM_API_KEY'))
# print("=== STEAM_USER_ID Loaded ===", os.getenv('STEAM_USER_ID'))
@app.template_filter('datetimeformat')
def datetimeformat(value):
    if not value:
        return ""
    try:
        return datetime.utcfromtimestamp(int(value)).strftime('%Y-%m-%d')
    except Exception:
        return value

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

@app.route("/country")
def country():
    try:
        with open("database/friends.json", "r") as f:
            friends = json.load(f)
    except:
        friends = []

    stats = defaultdict(list)
    for f in friends:
        code = f.get('country_code', '??')
        stats[code].append(f)

    # 預設排序：依照人數多寡
    sorted_countries = sorted(stats.items(), key=lambda x: len(x[1]), reverse=True)

    return render_template("country.html", stats=sorted_countries)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
