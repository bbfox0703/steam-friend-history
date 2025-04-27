#!/bin/bash

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🕒 daily.sh started at $(date)" >> /var/log/cron_exec.log
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔍 daily cron: Working dir: $(pwd)" >> /var/log/cron_exec.log

# 切換到專案根目錄
cd /app

# 每天資料備份
cp /app/database/friends.json /app/backups/daily_friends_$(date +'%Y%m%d').json
cp /app/database/friend_changes.json /app/backups/daily_friend_changes_$(date +'%Y%m%d').json
cp /app/database/name_history.json /app/backups/daily_name_history_$(date +'%Y%m%d').json
cp /app/database/games_total_history.json /app/backups/daily_games_total_history_$(date +'%Y%m%d').json

# 刪除 30 天以前的 daily 備份
find /app/backups/ -name "daily_*.json" -mtime +30 -delete
