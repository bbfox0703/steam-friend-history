#!/bin/bash
(
  flock -n 9 || { echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔒 achievement_backfill.sh skipped, another instance running" >> /var/log/cron_exec.log; exit 1; }
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🕒 achievement_backfill.sh started at $(date)" >> /var/log/cron_exec.log
  export PYTHONPATH="/app"
  cd /app
  /usr/local/bin/python3 -m utils.achievement_backfill >> /var/log/cron_exec.log 2>&1
) 9>/tmp/achievement_backfill.lock
