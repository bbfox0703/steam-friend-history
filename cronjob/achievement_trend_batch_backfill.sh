#!/bin/bash
# 每日成就和遊玩時間記錄
(
  flock -n 9 || { echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔒 achievement_trend_batch_backfill.sh skipped, another instance running" >> /var/log/cron_exec.log; exit 1; }
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🕒 achievement_trend_batch_backfill.sh started" >> /var/log/cron_exec.log
  cd /app
  /usr/local/bin/python3 -m utils.achievement_trend_batch_backfill >> /var/log/cron_exec.log 2>&1
) 9>/tmp/achievement_trend_batch_backfill.lock
