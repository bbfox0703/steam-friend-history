from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, jsonify
import utils.steam_api as steam_api
from utils.steam_api import get_friend_data
import utils.backup as backup
import pandas as pd
import json
import os
import operator
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict, Counter

tz = ZoneInfo("Asia/Taipei")

# 國碼對照英文名稱表（完整）
country_name_map = {
    # 亞洲
    "TW": "Taiwan", "CN": "China", "HK": "Hong Kong", "MO": "Macau",
    "JP": "Japan", "KR": "South Korea", "KP": "North Korea",
    "SG": "Singapore", "MY": "Malaysia", "ID": "Indonesia", "TH": "Thailand",
    "VN": "Vietnam", "PH": "Philippines", "IN": "India", "PK": "Pakistan",
    "BD": "Bangladesh", "NP": "Nepal", "LK": "Sri Lanka", "KH": "Cambodia",
    "LA": "Laos", "MM": "Myanmar", "AF": "Afghanistan", "IR": "Iran",
    "IQ": "Iraq", "SA": "Saudi Arabia", "SY": "Syria", "IL": "Israel",
    "AE": "United Arab Emirates", "QA": "Qatar", "KW": "Kuwait", "OM": "Oman",
    "BH": "Bahrain", "JO": "Jordan", "YE": "Yemen", "GE": "Georgia",
    "AM": "Armenia", "AZ": "Azerbaijan", "TJ": "Tajikistan", "TM": "Turkmenistan",
    "UZ": "Uzbekistan", "KZ": "Kazakhstan", "KG": "Kyrgyzstan", "MN": "Mongolia",
    "BT": "Bhutan", "BN": "Brunei", "MV": "Maldives", "PS": "Palestine",

    # 歐洲
    "GB": "United Kingdom", "IE": "Ireland", "FR": "France", "DE": "Germany",
    "IT": "Italy", "ES": "Spain", "PT": "Portugal", "BE": "Belgium",
    "NL": "Netherlands", "CH": "Switzerland", "AT": "Austria", "SE": "Sweden",
    "NO": "Norway", "DK": "Denmark", "FI": "Finland", "IS": "Iceland",
    "CZ": "Czech Republic", "SK": "Slovakia", "HU": "Hungary", "PL": "Poland",
    "RO": "Romania", "BG": "Bulgaria", "GR": "Greece", "SI": "Slovenia",
    "HR": "Croatia", "BA": "Bosnia and Herzegovina", "RS": "Serbia", "ME": "Montenegro",
    "MK": "North Macedonia", "AL": "Albania", "XK": "Kosovo", "BY": "Belarus",
    "UA": "Ukraine", "RU": "Russia", "MD": "Moldova", "EE": "Estonia",
    "LV": "Latvia", "LT": "Lithuania", "LU": "Luxembourg", "MT": "Malta",
    "CY": "Cyprus", "LI": "Liechtenstein", "MC": "Monaco", "SM": "San Marino",
    "VA": "Vatican City",

    # 美洲
    "US": "United States", "CA": "Canada", "MX": "Mexico",
    "AR": "Argentina", "BR": "Brazil", "CL": "Chile", "CO": "Colombia",
    "PE": "Peru", "VE": "Venezuela", "UY": "Uruguay", "PY": "Paraguay",
    "BO": "Bolivia", "EC": "Ecuador", "GT": "Guatemala", "HN": "Honduras",
    "SV": "El Salvador", "NI": "Nicaragua", "CR": "Costa Rica", "PA": "Panama",
    "CU": "Cuba", "DO": "Dominican Republic", "HT": "Haiti", "JM": "Jamaica",
    "TT": "Trinidad and Tobago", "PR": "Puerto Rico", "BS": "Bahamas",
    "BB": "Barbados", "GD": "Grenada", "AG": "Antigua and Barbuda",
    "LC": "Saint Lucia", "KN": "Saint Kitts and Nevis",

    # 非洲
    "EG": "Egypt", "DZ": "Algeria", "MA": "Morocco", "TN": "Tunisia",
    "LY": "Libya", "SD": "Sudan", "SS": "South Sudan", "ET": "Ethiopia",
    "KE": "Kenya", "UG": "Uganda", "TZ": "Tanzania", "GH": "Ghana",
    "NG": "Nigeria", "CM": "Cameroon", "SN": "Senegal", "CI": "Ivory Coast",
    "ZM": "Zambia", "ZW": "Zimbabwe", "AO": "Angola", "MW": "Malawi",
    "MZ": "Mozambique", "NA": "Namibia", "BW": "Botswana", "LS": "Lesotho",
    "SZ": "Eswatini", "RW": "Rwanda", "BI": "Burundi", "GA": "Gabon",
    "CG": "Congo", "CD": "Democratic Republic of the Congo", "NE": "Niger",
    "ML": "Mali", "BF": "Burkina Faso", "TG": "Togo", "GN": "Guinea",
    "GM": "Gambia", "SL": "Sierra Leone", "LR": "Liberia", "MR": "Mauritania",
    "DJ": "Djibouti", "SO": "Somalia", "MG": "Madagascar", "MU": "Mauritius",
    "SC": "Seychelles", "RE": "Réunion",

    # 大洋洲與其他地區
    "AU": "Australia", "NZ": "New Zealand", "FJ": "Fiji", "PG": "Papua New Guinea",
    "WS": "Samoa", "TO": "Tonga", "SB": "Solomon Islands", "FM": "Micronesia",
    "MH": "Marshall Islands", "TV": "Tuvalu", "VU": "Vanuatu", "NC": "New Caledonia",
    "PF": "French Polynesia", "GU": "Guam", "MP": "Northern Mariana Islands",
    "CK": "Cook Islands", "NU": "Niue", "NR": "Nauru",

    # 特殊與未知
    "??": "Unknown", "ZZ": "Unknown"
}

STATUS_MAP = {
    0: '離線',
    1: '在線上',
    2: '忙碌',
    3: '離開',
    4: '請勿打擾',
    5: '想交易',
    6: '想玩遊戲'
}

def load_data():
    path = os.path.join('database', 'friends.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []
    
def filter_friend_list(args):
    friends = get_friend_data()

    # 取得查詢參數
    online_only = args.get('online_only') == 'true'
    has_avatar = args.get('has_avatar') == 'true'
    has_country = args.get('has_country') == 'true'
    recent_days = args.get('recent_days')
    country_filter = args.get('country_code', '')

    now = datetime.utcnow()
    filtered = []

    for f in friends:
        if online_only and f.get('personastate', 0) == 0:
            continue
        if has_avatar and not f.get('avatar'):
            continue
        if has_country and (not f.get('country_code') or f['country_code'] == '??'):
            continue
        if recent_days:
            try:
                days = int(recent_days)
                last = int(f.get('lastlogoff', 0))
                last_time = datetime.utcfromtimestamp(last)
                if now - last_time > timedelta(days=days):
                    continue
            except:
                pass
        if country_filter and f.get('country_code', '').lower() != country_filter.lower():
            continue
        filtered.append(f)

    return filtered    

app = Flask(__name__)
import os
# print("=== API_KEY Loaded ===", os.getenv('STEAM_API_KEY'))
# print("=== STEAM_USER_ID Loaded ===", os.getenv('STEAM_USER_ID'))

@app.template_filter('datetimeformat')
def datetimeformat(ts):
    try:
        dt = datetime.fromtimestamp(int(ts), tz)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return ts

@app.template_filter('timeago')
def timeago(ts):
    try:
        now = datetime.now(tz=tz)
        dt = datetime.fromtimestamp(int(ts), tz)
        diff = now - dt

        seconds = int(diff.total_seconds())
        minutes = seconds // 60
        hours = minutes // 60
        days = hours // 24

        if seconds < 60:
            return f"{seconds} 秒前"
        elif minutes < 60:
            return f"{minutes} 分鐘前"
        elif hours < 24:
            return f"{hours} 小時前"
        else:
            return f"{days} 天前"
    except:
        return "時間未知"

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

    sorted_items = [(code, len(friends)) for code, friends in country_members.items()]
    if sort_mode == "name":
        sorted_items.sort(key=lambda x: x[0])
    else:
        sorted_items.sort(key=lambda x: x[1], reverse=True)

    return render_template("country.html",
                           sorted_items=sorted_items,
                           country_members=country_members,
                           sort_mode=sort_mode,
                           country_name_map=country_name_map)

@app.route("/country-chart")
def country_chart():
    from collections import defaultdict
    import operator

    friends = steam_api.get_friend_data()
    country_counts = defaultdict(int)

    for f in friends:
        code = f.get("country_code", "??")
        country_counts[code] += 1

    global country_name_map  # 使用 app.py 裡的全域變數
    stats = []
    for code, count in sorted(country_counts.items(), key=lambda x: x[1], reverse=True):
        name = country_name_map.get(code, "Unknown")
        stats.append({"code": code, "name": name, "count": count})

    return render_template("country_chart.html", stats=stats)

@app.route('/filter', methods=['GET'])
def filter_friends():
    friends = filter_friend_list(request.args)
    all_countries = sorted(set(f['country_code'] for f in get_friend_data() if f.get('country_code') and f['country_code'] != '??'))

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(friends)

    return render_template('filter.html', friends=friends, status_map=STATUS_MAP, all_countries=all_countries)

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

@app.route('/status-board')
def status_board():
    friends = get_friend_data()
    show_online_only = request.args.get('online_only') == 'on'

    def sort_key(f):
        state = f.get('personastate', 0)
        lastlogoff = f.get('lastlogoff') or 0
        return (-1 if state != 0 else 1, -lastlogoff)

    filtered = [f for f in friends if not show_online_only or f.get('personastate', 0) != 0]
    sorted_friends = sorted(filtered, key=sort_key)

    return render_template('status_board.html', friends=sorted_friends, status_map=STATUS_MAP, show_online_only=show_online_only)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
