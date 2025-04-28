#!/bin/bash
# 1) 取得持有遊戲名稱：繁中、日文、英文
# 2) 下架或是不存在的遊戲30天內不再抓取
# 3) 取得持有遊戲總數
(
  flock -n 9 || { echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔒 cache_games_daily.sh skipped, another instance running" >> /var/log/cron_exec.log; exit 1; }
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🕒 cache_games_daily.sh started at $(date)" >> /var/log/cron_exec.log
  export PYTHONPATH="/app"
  cd /app
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🎮 Updating game title cache (all languages)..." >> /var/log/cron_exec.log
  /usr/local/bin/python3 -m utils.cache_games --lang all --sleep 3 >> /var/log/cron_exec.log 2>&1
  /usr/local/bin/python3 -m utils.recheck_unavailable >> /var/log/cron_exec.log 2>&1
  /usr/local/bin/python3 -m utils.record_games_total >> /var/log/cron_exec.log 2>&1
) 9>/tmp/cache_games_daily.lock