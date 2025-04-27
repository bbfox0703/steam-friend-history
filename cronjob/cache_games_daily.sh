#!/bin/bash

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🕒 cache_games_daily.sh started at $(date)" >> /var/log/cron_exec.log

# 明確設定 PYTHONPATH
export PYTHONPATH="/app"

# 切換到專案根目錄
cd /app

# 快取 Steam 遊戲清單（支援繁中、日文、英文）
echo "[$(date '+%Y-%m-%d %H:%M:%S')]  🎮 Updating game title cache (all languages)..." >> /var/log/cron_exec.log
/usr/local/bin/python3 -m utils.cache_games --lang all --sleep 1 >> /var/log/cron_exec.log 2>&1
