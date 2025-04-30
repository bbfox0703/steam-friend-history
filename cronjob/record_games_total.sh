#!/bin/bash
# 取得持有遊戲總數
(
  flock -n 9 || { echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔒 record_games_total.sh skipped, another instance running" >> /var/log/cron_exec.log; exit 1; }
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🕒 record_games_total.sh started" >> /var/log/cron_exec.log
  cd /app
  /usr/local/bin/python3 -m utils.record_games_total >> /var/log/cron_exec.log 2 /var/log/record_games_total_err.log
) 9>/tmp/record_games_total.lock