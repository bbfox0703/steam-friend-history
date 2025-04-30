#!/bin/bash
# 建立持有遊戲的遊戲名稱快取
(
  flock -n 9 || { echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔒 daily_warmup.sh skipped, another instance running" >> /var/log/cron_exec.log; exit 1; }
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🕒 daily_warmup.sh started at $(date)" >> /var/log/cron_exec.log
  export PYTHONPATH="/app"
  cd /app
  $(which python3) -m utils.warmup_cache >> /var/log/cron_exec.log 2>> /var/log/warmup_err.log
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ daily_warmup.sh completed." >> /var/log/cron_exec.log
) 9>/tmp/daily_warmup.lock