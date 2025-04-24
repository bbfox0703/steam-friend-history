#!/bin/bash

echo "🕒 daily.sh started at $(date)" >> /var/log/cron_exec.log

# 確保 cron 執行時能找到 python 指令與模組
export PATH="/usr/local/bin:/usr/bin:/bin"

cd /app || {
    echo "❌ Failed to cd /app" >> /var/log/cron_exec.log
    exit 1
}

# 每天凌晨 3:00 存長期備份
cp database/friends.json backups/daily_$(date +'%Y%m%d').json 2>> /var/log/cron_exec.log

# 刪除 30 天以前的 daily 備份
find backups/ -name "daily_*.json" -mtime +30 -delete

# 🔄 快取 Steam 遊戲清單（用 module 方式）
echo "[$(date)] 🎮 Updating game title cache..." >> /var/log/cron_exec.log
python3 -m utils.cache_games >> /var/log/cron_exec.log 2>&1
