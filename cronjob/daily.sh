#!/bin/bash

echo "🕒 daily.sh started at $(date)" >> /var/log/cron_exec.log
echo "🔍 Working dir: $(pwd)" >> /var/log/cron_exec.log

# 明確設定 PYTHONPATH
export PYTHONPATH="/app"

# 確保切換目錄
cd /app

# 每天凌晨 3:00 存長期備份
cp /app/database/friends.json /app/backups/daily_$(date +'%Y%m%d').json

# 刪除 30 天以前的 daily 備份
find /app/backups/ -name "daily_*.json" -mtime +30 -delete

# 快取 Steam 遊戲清單
echo "[$(date)] 🎮 Updating game title cache..." >> /var/log/cron_exec.log
/usr/local/bin/python3 -m utils.cache_games >> /var/log/cron_exec.log 2>&1
