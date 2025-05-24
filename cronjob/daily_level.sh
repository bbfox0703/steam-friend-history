#!/bin/bash
# Steam 等級記錄
(
  flock -n 9 || { echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔒 daily_level.sh skipped, another instance running" >> /var/log/cron_exec.log; exit 1; }
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🕒 daily_level.sh started" >> /var/log/cron_exec.log
  cd /app
  /usr/local/bin/python3 -m utils.daily_level_update >> /var/log/cron_exec.log 2>> /var/log/daily_level_update_err.log
) 9>/tmp/daily_level.lock
