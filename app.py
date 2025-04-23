from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, send_file
import utils.steam_api as steam_api
from utils.steam_api import get_friend_data
from utils.steam_api import fetch_game_info
import requests
import utils.backup as backup
import pandas as pd
import json
import os
import io
import zipfile
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

lang_map = {
    "zh-tw": "tchinese",
    "ja": "japanese",
    "en": "english"
}

def load_data():
    path = os.path.join('database', 'friends.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []
    
def filter_friend_list(args):
    friends = get_friend_data()

    # 判斷是否有勾選條件（只看 key 是否存在）
    online_only = 'online_only' in args
    has_avatar = 'has_avatar' in args
    has_country = 'has_country' in args
    recent_days = args.get('recent_days')
    country_filter = args.get('country_code', '')
    sort_order = args.get('sort', 'newest')

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

    # 排序
    if sort_order == 'newest':
        filtered.sort(key=lambda f: f.get('friend_since', 0), reverse=True)
    elif sort_order == 'oldest':
        filtered.sort(key=lambda f: f.get('friend_since', 0))

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
            raw_changes = json.load(f)
            changes = {}
            for time_str, change in raw_changes.items():
                try:
                    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    dt = dt.replace(tzinfo=tz)
                    ts = int(dt.timestamp())  # Unix timestamp 秒數
                    changes[ts] = change
                except Exception as e:
                    print(f"⚠️ 時間字串格式錯誤：{time_str}, error: {e}")
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

    for logs in name_history.values():
        for r in logs:
            if isinstance(r.get("time"), str):
                try:
                    dt = datetime.strptime(r["time"], "%Y-%m-%d %H:%M:%S")
                    r["ts"] = int(dt.timestamp())
                except Exception as e:
                    r["ts"] = 0  # fallback
            elif isinstance(r.get("time"), (int, float)):
                r["ts"] = int(r["time"])
            else:
                r["ts"] = 0

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

@app.route('/filter')
def filter_friends():
    friends = filter_friend_list(request.args)

    all_countries = sorted(set(
        f['country_code'] for f in get_friend_data()
        if f.get('country_code') and f['country_code'] != '??'
    ))

    # 若為 AJAX 呼叫，回傳 JSON 給 JS 使用
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(friends)

    # 一般頁面渲染
    return render_template(
        'filter.html',
        friends=friends,
        status_map=STATUS_MAP,
        all_countries=all_countries
    )

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

@app.route('/backups')
def backups():
    sort_by = request.args.get('sort', 'mtime')
    order = request.args.get('order', 'desc')
    base = 'backups'
    files = []

    for f in os.listdir(base):
        path = os.path.join(base, f)
        if os.path.isfile(path):
            stat = os.stat(path)
            files.append({
                'name': f,
                'size_kb': int(stat.st_size / 1024),
                'mtime': int(stat.st_mtime)
            })

    reverse = (order == 'desc')
    if sort_by == 'name':
        files.sort(key=lambda f: f['name'], reverse=reverse)
    elif sort_by == 'size_kb':
        files.sort(key=lambda f: f['size_kb'], reverse=reverse)
    else:
        files.sort(key=lambda f: f['mtime'], reverse=reverse)

    return render_template('backups.html', files=files, sort_by=sort_by, order=order)

@app.route('/backups/download/<filename>')
def download_backup(filename):
    return send_from_directory('backups', filename, as_attachment=True)

@app.route('/backups/delete/<filename>', methods=['POST'])
def delete_backup(filename):
    path = os.path.join('backups', filename)
    if os.path.exists(path):
        os.remove(path)
        return jsonify({'status': 'deleted'})
    return jsonify({'status': 'not_found'})

@app.route('/backups/zip', methods=['POST'])
def zip_backups():
    filenames = request.form.getlist('files')
    if not filenames:
        return "未選取任何檔案", 400

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for name in filenames:
            path = os.path.join('backups', name)
            if os.path.exists(path):
                zf.write(path, arcname=name)
    memory_file.seek(0)

    now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    return send_file(memory_file, as_attachment=True, download_name=f"steam_backups_{now_str}.zip", mimetype='application/zip')

@app.route("/achievement")
def achievement_input():
    appid = request.args.get("appid")
    if appid:
        return redirect(url_for("achievement_trend", appid=appid))
    return render_template("achievement_search.html")

@app.route("/achievement/<appid>")
def achievement_trend(appid):
    # 語言偵測
    lang_override = request.args.get("lang")
    if lang_override in lang_map:
        steam_lang = lang_map[lang_override]
    else:
        lang = request.accept_languages.best_match(["zh-tw", "ja", "en"], default="en")
        steam_lang = lang_map.get(lang, "english")
    
    game_info = fetch_game_info(appid, steam_lang)
    game_name = game_info["name"] or get_game_title(appid)
    header_image = game_info["header_image"]


    mode = request.args.get("mode", "day")

    try:
        achievements = steam_api.fetch_achievements(appid)
    except Exception as e:
        return render_template("achievement_trend.html", appid=appid, error=str(e), game_name=game_name)

    timeline = []
    for a in achievements:
        if a.get("achieved") == 1 and a.get("unlocktime"):
            dt = datetime.fromtimestamp(a["unlocktime"])
            if mode == "month":
                timeline.append(dt.strftime("%Y-%m"))
            else:
                timeline.append(dt.strftime("%Y-%m-%d"))

    if not timeline:
        return render_template("achievement_trend.html", appid=appid, error="無達成成就資料", game_name=game_name)

    # pandas 處理與補齊空白區間
    df = pd.DataFrame({"date": timeline})
    df["date"] = pd.to_datetime(df["date"])

    if mode == "month":
        df["period"] = df["date"].dt.to_period("M")
        full_range = pd.period_range(df["period"].min(), df["period"].max(), freq="M")
    else:
        df["period"] = df["date"].dt.to_period("D")
        full_range = pd.period_range(df["period"].min(), df["period"].max(), freq="D")

    stat = df.groupby("period").size().reindex(full_range, fill_value=0).reset_index()
    stat.columns = ["date", "count"]
    stat["date"] = stat["date"].astype(str)

    data = stat.to_dict(orient="records")
    total = len(achievements)
    unlocked = sum(a.get("achieved", 0) for a in achievements)  

    return render_template("achievement_trend.html",
                           appid=appid,
                           game_name=game_name,
                           header_image=header_image,
                           dates=dates,
                           counts=counts,
                           data=data,
                           total=total,
                           unlocked=unlocked,
                           mode=mode)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
