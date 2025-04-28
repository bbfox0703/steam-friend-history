#!/bin/bash
# 每日成就和遊玩時間記錄
(
  flock -n 9 || { echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔒 achievement_daily.sh skipped, another instance running" >> /var/log/cron_exec.log; exit 1; }
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🕒 achievement_daily.sh started" >> /var/log/cron_exec.log
  cd /app
  /usr/local/bin/python3 -m utils.achievement_trend >> /var/log/cron_exec.log 2>&1
) 9>/tmp/achievement_daily.lock
