# utils/level_history_db.py

from utils.db import get_connection, init_db

# 確保資料表存在
init_db()

# 儲存單日的level紀錄
def save_level(date, level):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO level_history (date, level)
        VALUES (?, ?)
    ''', (date, level))
    conn.commit()
    conn.close()

# 取得特定日期的level資料（如果要用）
def get_level_by_date(date):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT level FROM level_history WHERE date = ?
    ''', (date,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

# 取得所有level歷史資料（用於前台趨勢頁面）
def get_all_levels():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT date, level FROM level_history ORDER BY date ASC
    ''')
    rows = c.fetchall()
    conn.close()
    return {date: level for date, level in rows}

# 測試用 (單獨執行)
if __name__ == "__main__":
    print("所有等級歷史紀錄：", get_all_levels())
