#!/bin/bash

# 記錄開始時間
echo "🕒 daily.sh started at $(date)" >> /var/log/cron_exec.log

# 設定 PATH，避免 cron 環境缺少常用指令
export PATH="/usr/local/bin:/usr/bin:/bin"

# 移除 PYTHONPATH 的 wild card，會被誤當字串傳進 python
# 如果真的需要 PYTHONPATH，應該動態取得
# export PYTHONPATH="/usr/local/lib/python3.*/dist-packages:$PYTHONPATH"

# 保險一點，確保工作目錄正確
cd /app || {
    echo "❌ Failed to cd /app" >> /var/log/cron_exec.log
    exit 1
}

# 每天凌晨 3:00 存長期備份
cp database/friends.json backups/daily_$(date +'%Y%m%d').json 2>> /var/log/cron_exec.log

# 刪除 30 天以前的 daily 備份
find backups/ -name "daily_*.json" -mtime +30 -delete

# 🔄 快取 Steam 遊戲清單
echo "[$(date)] 🎮 Updating game title cache..." >> /var/log/cron_exec.log
python3 utils/cache_games.py >> /var/log/cron_exec.log 2>&1
