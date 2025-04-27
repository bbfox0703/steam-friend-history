# utils/game_titles_db.py

from utils.db import get_connection, init_db

# 確保資料表存在
init_db()

# 儲存一個遊戲的名稱資料
def save_game_title(appid, en=None, tchinese=None, japanese=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO game_titles (appid, en, tchinese, japanese)
        VALUES (?, ?, ?, ?)
    ''', (appid, en, tchinese, japanese))
    conn.commit()
    conn.close()

# 根據 appid 取得指定語言的遊戲名稱
def get_game_title(appid, lang='en'):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT en, tchinese, japanese FROM game_titles WHERE appid = ?
    ''', (appid,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None

    en, tchinese, japanese = row
    if lang == 'tchinese':
        return tchinese or en
    elif lang == 'japanese':
        return japanese or en
    else:
        return en

# 取得所有遊戲的標題資料
def get_all_game_titles():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT appid, en, tchinese, japanese FROM game_titles
    ''')
    rows = c.fetchall()
    conn.close()
    return {str(appid): {'en': en, 'tchinese': tchinese, 'japanese': japanese} for appid, en, tchinese, japanese in rows}

# 測試用 (單獨執行)
if __name__ == "__main__":
    print("所有遊戲標題：", get_all_game_titles())