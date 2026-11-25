import os
import json
import requests
from utils.api_utils import safe_api_get, mask_key
from utils.db import get_cached_achievements, save_achievement_cache, get_game_info_cache, save_game_info_cache
import time
import functools
from datetime import datetime
from utils.game_titles_db import get_game_title as db_get_game_title, get_all_game_titles 
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('STEAM_API_KEY')
STEAM_ID = os.getenv('STEAM_USER_ID')
DB_PATH = './database/friends.json'
HISTORY_PATH = './database/name_history.json'
CHANGELOG_PATH = './database/friend_changes.json'
BACKUP_DIR = './backups'

LOG_DIR = "./logs"
LOG_FILE = os.path.join(LOG_DIR, "steam_api.log")

print = functools.partial(print, flush=True)

STORE_LANG_MAP = {
    "english": "en",
    "tchinese": "tchinese",
    "japanese": "japanese"
}

_cached_titles = None

def log(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {mask_key(msg)}"  # 避免 API key 進 log
    print(full_msg)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")

# 抓所有遊戲標題 cache
# 📦 載入本地快取的所有遊戲標題（多語系）
def load_cached_titles():
    global _cached_titles
    if _cached_titles is None:
        _cached_titles = get_all_game_titles()
    return _cached_titles

class FriendListPrivateError(Exception):
    """GetFriendList 回 401：好友清單非公開（或 API key 無效）。"""

# 👥 從 Steam API 抓取好友 SteamID 清單
def fetch_friend_list():
    url = f"https://api.steampowered.com/ISteamUser/GetFriendList/v1/?key={API_KEY}&steamid={STEAM_ID}&relationship=friend"
    log(f" fetch_friend_list(): {url}")
    response = safe_api_get(url)
    if response.status_code == 401:
        # GetFriendList 對「好友清單非公開」的帳號一律回 401 {}（API key 本身沒問題時也一樣）
        msg = ("Steam API 401: 好友清單無法讀取（隱私設定非「公開」，或 STEAM_API_KEY 無效）。")
        log(f"⚠️ {msg}")
        raise FriendListPrivateError(msg)
    if response.status_code != 200:
        raise Exception(f"Steam API Error: {response.status_code} {response.text}")
    data = response.json()
    if 'friendslist' not in data:
        raise Exception(f"Steam API 回傳格式異常（沒有 friendslist）：{response.text[:200]}")
    return data['friendslist'].get('friends', [])

# 📇 從 Steam API 抓取好友個人資料（名稱、頭像、狀態、國家）
def fetch_friend_profiles(steam_ids):
    if not steam_ids:
        return {}

    result = {}
    for i in range(0, len(steam_ids), 100):
        batch = steam_ids[i:i + 100]
        ids_str = ','.join(batch)
        url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={API_KEY}&steamids={ids_str}"
        response = safe_api_get(url)
        log(f"🔍 fetch_friend_profiles(), batch {i}: {url}")

        # time.sleep(5)  # ← 檢查是否仍需要

        if response.status_code == 200:
            players = response.json().get('response', {}).get('players', [])
            for p in players:
                result[p['steamid']] = {
                    'personaname': p.get('personaname', ''),
                    'avatar': p.get('avatar', ''),
                    'profileurl': p.get('profileurl', ''),
                    'loccountrycode': p.get('loccountrycode', '??'),
                    'lastlogoff': p.get('lastlogoff'),
                    'personastate': p.get('personastate', 0)
                }
        else:
            log(f"⚠️ Failed batch {i} - Status {response.status_code} {response.text}")

    return result

# 🔄 若好友資料不完整，從備份中回補欄位
def try_restore_from_backup(sid, fields=("persona_name", "avatar", "lastlogoff", "personastate"), lookback=10):
    files = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.startswith("friends_") and f.endswith(".json")],
        reverse=True
    )
    for filename in files[:lookback]:
        path = os.path.join(BACKUP_DIR, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for entry in data:
                    if entry.get("steamid") == sid:
                        if all(entry.get(k) is not None and entry.get(k) != '' for k in fields):
                            return {k: entry[k] for k in fields if k in entry}
        except Exception as e:
            log(f"⚠️ 無法從備份 {filename} 讀取 {sid}：{e}")
            continue
    return {}

# 📂 讀取目前的好友資料（friends.json）
def get_friend_data():
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, 'r') as f:
        return json.load(f)

# 💾 儲存好友資料，使用暫存檔方式避免損毀
def save_friend_data(friend_list):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    tmp_path = DB_PATH + ".tmp"
    with open(tmp_path, 'w') as f:
        json.dump(friend_list, f, indent=2)
    os.replace(tmp_path, DB_PATH)  # ✅ 原子替換，避免讀到寫到一半的檔案

# 🗂️ 備份好友資料到 backups 資料夾
def backup_friend_data(friend_list):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    path = os.path.join(BACKUP_DIR, f'friends_{timestamp}.json')
    with open(path, 'w') as f:
        json.dump(friend_list, f, indent=2)

# 📥 讀取任意 JSON 檔案為 dict
def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        return json.load(f)

# 📤 將資料儲存為 JSON 檔案
def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

# 🔁 更新好友清單，記錄變動並嘗試補齊缺失資料
# 回傳 {'count': 好友數, 'mode': 'full' | 'names_only'}
#   full       ：好友清單公開，偵測新增 / 刪除 / 改名
#   names_only ：好友清單非公開（401），只用 friends.json 既有的 steamid 追蹤改名、頭像、狀態；
#                無法偵測新增 / 刪除好友，也不會寫入 friend_changes.json
def update_friend_list():
    old_friends = get_friend_data()
    old_dict = {f['steamid']: f for f in old_friends}
    old_ids = set(old_dict.keys())

    mode = 'full'
    try:
        friend_list = fetch_friend_list()
    except FriendListPrivateError:
        if not old_friends:
            raise Exception("好友清單非公開，且沒有既有的 friends.json 可供追蹤；請先把好友清單設為公開執行一次")
        mode = 'names_only'
        log(f"ℹ️ 好友清單非公開，改用備援模式：只追蹤既有 {len(old_friends)} 位好友的改名（無法偵測新增 / 刪除）")
        friend_list = [{'steamid': f['steamid'], 'friend_since': f.get('friend_since', 0)} for f in old_friends]

    steam_ids = [f['steamid'] for f in friend_list]
    new_ids = set(steam_ids)

    # 🛡️ 防呆：API 若暫時回傳空清單 / 大幅縮水，不要把所有人記成「刪除好友」並覆寫 friends.json
    if mode == 'full' and old_ids and (not new_ids or len(old_ids - new_ids) > max(20, len(old_ids) // 2)):
        msg = (f"好友清單異常縮水（舊 {len(old_ids)} → 新 {len(new_ids)}，"
               f"減少 {len(old_ids - new_ids)}），本次不寫入以免誤判")
        log(f"❌ {msg}")
        raise Exception(msg)

    profiles = fetch_friend_profiles(steam_ids)
    if mode == 'names_only' and not profiles:
        # 401 也可能是 API key 失效；這時 GetPlayerSummaries 同樣拿不到資料，不要拿空資料覆寫
        raise Exception("備援模式下 GetPlayerSummaries 也沒有回傳任何資料，請確認 STEAM_API_KEY 是否有效")

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    name_history = load_json(HISTORY_PATH)
    changes = load_json(CHANGELOG_PATH)
    added = sorted(list(new_ids - old_ids))
    removed = sorted(list(old_ids - new_ids))
    if mode == 'full' and (added or removed):
        changes[now] = {"added": added, "removed": removed}

    enriched_friends = []
    for f in friend_list:
        sid = f['steamid']
        profile = profiles.get(sid, {})
        new_name = profile.get('personaname', '')
        old_name = old_dict.get(sid, {}).get('persona_name', '')

        if old_name and new_name and old_name != new_name:
            if sid not in name_history:
                name_history[sid] = []
            name_history[sid].append({
                'time': now,
                'old': old_name,
                'new': new_name
            })

        enriched = {
            'steamid': sid,
            'friend_since': f['friend_since'],
            'persona_name': new_name,
            'avatar': profile.get('avatar', ''),
            'profile_url': profile.get('profileurl', f'https://steamcommunity.com/profiles/{sid}'),
            'country_code': profile.get('loccountrycode', '??'),
            'lastlogoff': profile.get('lastlogoff'),
            'personastate': profile.get('personastate')
        }

        important_fields = ['persona_name', 'avatar', 'lastlogoff', 'personastate', 'country_code']

        # 判斷真正缺失的欄位（None 或 空字串）
        missing_keys = [
            k for k in important_fields
            if enriched.get(k) is None or enriched.get(k) == '' or (k == 'country_code' and enriched.get(k) == '??')
        ]

        if missing_keys:
            enriched['incomplete'] = True
            restored = try_restore_from_backup(sid, fields=missing_keys)
            if restored:
                enriched.update(restored)
                enriched['restored'] = True

                still_missing = [k for k in important_fields if enriched.get(k) is None or enriched.get(k) == '']
                if not still_missing:
                    enriched.pop('incomplete', None)

        enriched_friends.append(enriched)

    save_friend_data(enriched_friends)
    save_json(HISTORY_PATH, name_history)
    save_json(CHANGELOG_PATH, changes)
    backup_friend_data(enriched_friends)
    log(f"✅ update_friend_list(): mode={mode}, count={len(enriched_friends)}")
    return {'count': len(enriched_friends), 'mode': mode}

#def fetch_achievements(appid, steam_id=None):
#    if steam_id is None:
#        steam_id = STEAM_ID
#    url = f"https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?key={API_KEY}&steamid={steam_id}&appid={appid}"
#    print(f"🔍 {time.strftime('%Y-%m-%d %H:%M:%S')} fetch_achievements()")
#    response = safe_api_get(url)
#    if response.status_code != 200:
#        raise Exception(f"Steam API Error: {response.status_code} {response.text}")
#    return response.json().get("playerstats", {}).get("achievements", [])


# 🏆 查詢某遊戲成就清單，支援 SQLite 快取（如為全成就）
def fetch_achievements(appid):
    log(f"🔍 fetch_achievements(appid={appid})")

    # 先查快取
    cached = get_cached_achievements(STEAM_ID, appid)
    if cached:
        log(f"✅ 快取命中 appid={appid}")
        return [{"apiname": a["name"], "unlocktime": a["unlock_time"], "achieved": 1} for a in cached]

    # 沒命中則呼叫 API
    url = f"https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?key={API_KEY}&steamid={STEAM_ID}&appid={appid}"
    try:
        response = safe_api_get(url, timeout=10)
        time.sleep(0.2)
        if response.status_code == 200:
            data = response.json()
            achievements = data.get('playerstats', {}).get('achievements', [])

            unlocked = [a for a in achievements if a.get("achieved") == 1 and a.get("unlocktime", 0) > 0]
            if achievements and len(unlocked) == len(achievements):
                save_achievement_cache(STEAM_ID, appid, [
                    {"name": a["apiname"], "unlock_time": a.get("unlocktime", 0)} for a in unlocked
                ])
                log(f"📝 已快取全成就 appid={appid}")

            return achievements

        elif response.status_code == 400:
            # ⚡ 特別處理無成就遊戲
            err_data = response.json()
            if 'error' in err_data.get('playerstats', {}):
                log(f"⚠️ AppID {appid} 無成就，跳過")
                return []
            else:
                raise Exception(f"Steam API Error: {response.status_code} {response.text}")
        else:
            raise Exception(f"Steam API Error: {response.status_code} {response.text}")
    except Exception as e:
        log(f"❌ Fetch achievements failed: {e}")
        return []

# ****** fetch_achievement_data 並未使用到 
# ****** 如有使用到時移除此註解
# 📊 查詢成就原始 JSON 結構（不使用快取）
def fetch_achievement_data(appid, steam_id=None):
    if steam_id is None:
        steam_id = STEAM_ID
    url = f"https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?key={API_KEY}&steamid={steam_id}&appid={appid}"
    log(f"🔍 fetch_achievement_data()")
    # time.sleep(4)  # ← 檢查是否仍需要
    response = safe_api_get(url)
    if response.status_code != 200:
        raise Exception(f"Steam API Error: {response.status_code} {response.text}")
    return response.json().get("playerstats", {})

# 📈 成就摘要（已解鎖 / 總數）
def fetch_achievement_summary(appid):
    log(f"🔄 fetch_achievement_summary(appid={appid})")
    try:
        achievements = fetch_achievements(appid)  # ✅ 會使用快取
        if not achievements:
            return None
        unlocked = sum(1 for a in achievements if a.get("achieved", 0) == 1)
        total = len(achievements)
        log(f"✅ appid={appid}, unlocked={unlocked}, total={total}")
        return {"unlocked": unlocked, "total": total}
    except Exception as e:
        log(f"❌ Fetch achievement summary failed: {e}")
        return None

# 查目前持有的遊戲 (原本 fetch_owned_games 保留)
# 🎮 查詢帳號持有的所有遊戲清單（含 appid 與名稱）
def fetch_owned_games(lang="en"):
    url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={API_KEY}&steamid={STEAM_ID}&include_appinfo=true&l={lang}"
    log(f"🔍 fetch_owned_games()")
    try:
        response = safe_api_get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('response', {}).get('games', [])
    except Exception as e:
        log(f"⚠️ Fetch owned games error: {e}")
    return []    

# 查單個遊戲標題
# 🏷️ 取得快取中指定 AppID 的遊戲名稱
def get_game_title(appid, lang='en'):
    return db_get_game_title(appid, lang)


from datetime import datetime, timedelta


# 🛒 查詢 Steam Store 的遊戲名稱與封面，快取 30 天有效
def fetch_game_info(appid, lang="en"):
    log(f"🔍 fetch_game_info(appid={appid}, lang={lang})")

    from datetime import datetime, timedelta
    import time

    lang_to_api = {
        "en": "english",
        "tchinese": "tchinese",
        "japanese": "japanese"
    }
    api_lang = lang_to_api.get(lang, "english")

    cached = get_game_info_cache(appid, lang)
    if cached:
        last_updated_str = cached.get("last_updated")
        if last_updated_str:
            last_updated = datetime.fromisoformat(last_updated_str)
            if datetime.now() - last_updated <= timedelta(days=30):
                log(f"✅ fetch_game_info(): 使用快取遊戲資料 appid={appid} lang={lang}")
                return {
                    "name": cached["name"],
                    "header_image": cached["header_image"]
                }
            else:
                log(f"♻️ fetch_game_info(): 快取過期（超過30天） appid={appid} lang={lang}")

    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l={api_lang}"
    try:
        r = safe_api_get(url)
        if r.status_code == 200:
            data = r.json().get(str(appid), {}).get("data", {})
            name = data.get("name", "")
            header_image = data.get("header_image", "")
            raw_json = json.dumps(data)
            save_game_info_cache(appid, lang, name, header_image, raw_json)
        else:
            raise Exception(f"Steam API Error: {r.status_code} {r.text}")
    except Exception as e:
        log(f"❌ fetch_game_info(lang={lang}) failed: {e}")
        name = ""
        header_image = ""

    if lang != "en":
        cached_en = get_game_info_cache(appid, "en")
        need_en = True
        if cached_en:
            en_updated = datetime.fromisoformat(cached_en["last_updated"])
            if datetime.now() - en_updated <= timedelta(days=30):
                need_en = False
        if need_en:
            log(f"🈯 fetch_game_info(): 同步英文名稱快取 appid={appid}")
            try:
                time.sleep(1)
                r_en = safe_api_get(f"https://store.steampowered.com/api/appdetails?appids={appid}&l=english")
                if r_en.status_code == 200:
                    data_en = r_en.json().get(str(appid), {}).get("data", {})
                    name_en = data_en.get("name", "")
                    raw_json_en = json.dumps(data_en)
                    save_game_info_cache(appid, "en", name_en, "", raw_json_en)
            except Exception as e:
                log(f"⚠️ fetch_game_info() fallback english failed: {e}")

    return {"name": name, "header_image": header_image}

# 🔖 取得遊戲名稱（優先語言快取，否則備援英文）
def fetch_store_name(appid, lang="en"):
    log(f"🔍 fetch_store_name(appid={appid}, lang={lang})")

    # 優先查詢目標語言快取
    cached = get_game_info_cache(appid, lang)
    if cached and cached.get("name"):
        return cached["name"]

    # fallback 查詢英文快取
    fallback = get_game_info_cache(appid, "en")
    if fallback and fallback.get("name"):
        log(f"↩️ 使用英文名稱 fallback appid={appid}")
        return fallback["name"]

    # 查無資料
    return ""
    
# 🕹️ 取得最近遊玩的遊戲清單
def fetch_recent_games():
    url = f"https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v1/?key={API_KEY}&steamid={STEAM_ID}"
    log(f"🔍 fetch_recent_games(): {url}")
    resp = safe_api_get(url)
    if resp.status_code == 200:
        return resp.json().get('response', {}).get('games', [])
    return []

# 🔢 統計某遊戲目前解鎖的成就數
def fetch_achievement_count(appid):
    url = f"https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?key={API_KEY}&steamid={STEAM_ID}&appid={appid}"
    log(f"🔍 fetch_achievement_count(): {url}")
    # time.sleep(4)  # ← 檢查是否仍需要
    resp = safe_api_get(url)
    if resp.status_code == 200:
        achievements = resp.json().get('playerstats', {}).get('achievements', [])
        unlocked = [a for a in achievements if a.get('achieved', 0) == 1]
        return len(unlocked)
    return 0
    
# 🧬 查詢目前 Steam 帳號的等級
def fetch_current_level():
    url = f"https://api.steampowered.com/IPlayerService/GetSteamLevel/v1/?key={API_KEY}&steamid={STEAM_ID}"
    try:
        response = safe_api_get(url)
        if response.status_code == 200:
            data = response.json()
            level = data.get('response', {}).get('player_level')
            if level is not None:
                return level
            else:
                log("⚠️ player_level not found.")
        else:
            log(f"⚠️ HTTP Error {response.status_code}")
    except Exception as e:
        log(f"⚠️ Fetch Error: {e}")

    return None    
