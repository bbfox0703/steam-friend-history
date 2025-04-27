import os
import json
from datetime import datetime

def main():
    titles_path = "./database/game_titles.json"
    history_path = "./database/games_total_history.json"

    if not os.path.exists(titles_path):
        print("⚠️ No game_titles.json found")
        return

    with open(titles_path, "r", encoding="utf-8") as f:
        titles = json.load(f)

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

if __name__ == "__main__":
    main()
