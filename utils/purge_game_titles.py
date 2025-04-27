# utils/purge_game_titles.py

from utils.db import get_connection

def purge_game_titles():
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM game_titles')
    conn.commit()
    conn.close()
    print("✅ game_titles 資料表已清空！")

if __name__ == "__main__":
    purge_game_titles()
