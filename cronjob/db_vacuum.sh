#!/bin/bash
# DB compact
(
  flock -n 9 || { echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔒 db_vacuum.sh skipped, another instance running" >> /var/log/cron_exec.log; exit 1; }
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🕒 db_vacuum.sh started at $(date)" >> /var/log/cron_exec.log
  export PYTHONPATH="/app"
  cd /app
  $(which python3) -m utils.vacuum >> /var/log/cron_exec.log 2>> /var/log/vacuum_err.log
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ db_vacuum.sh completed." >> /var/log/cron_exec.log
) 9>/tmp/db_vacuum.lock