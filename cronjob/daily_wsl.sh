#!/bin/bash

#BASE_DIR="/home/youruser/steam-friend-history"
BASE_DIR="/home/pi/steam-friend-history"
DB="$BASE_DIR/database"
BK="$BASE_DIR/backups"
LOG="/var/log/cron_exec.log"
PY="$BASE_DIR/venv/bin/python"

echo "🕒 daily.sh started at $(date)" >> $LOG
echo "🔍 daily cron: Working dir: $(pwd)" >> $LOG

cd "$BASE_DIR"

cp "$DB/friends.json" "$BK/daily_friends_$(date +'%Y%m%d').json"
cp "$DB/friend_changes.json" "$BK/daily_friend_changes_$(date +'%Y%m%d').json"
cp "$DB/name_history.json" "$BK/daily_name_history_$(date +'%Y%m%d').json"
cp "$DB/game_titles.json" "$BK/daily_game_titles_$(date +'%Y%m%d').json"

find "$BK" -name "daily_*.json" -mtime +30 -delete

echo "[$(date)] 🎮 Updating game title cache (all languages)..." >> $LOG
"$PY" -m utils.cache_games --lang all --sleep 1 >> $LOG 2>&1
