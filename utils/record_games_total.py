# utils/record_games_total.py

import os
import json
from datetime import datetime
from utils.game_titles_db import get_all_game_titles

def main():
    history_path = "./database/games_total_history.json"

    # 改成從 SQLite 撈 titles
    titles = get_all_game_titles()
    today = datetime.today().strftime("%Y-%m-%d")
    total_games = len(titles.keys())

    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = {}

    history[today] = total_games

    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    print(f"✅ {today}: {total_games} games recorded.")

if __name__ == "__main__":
    main()
