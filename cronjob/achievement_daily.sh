#!/bin/bash
# 每日成就和遊玩時間記錄 - 增強版
(
  flock -n 9 || { echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔒 achievement_daily.sh skipped, another instance running" >> /var/log/cron_exec.log; exit 1; }

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🕒 achievement_daily.sh started" >> /var/log/cron_exec.log
  cd /app

  # 跑成就及遊玩時間更新
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🚀 Start achievement_trend.py" >> /var/log/cron_exec.log
  timeout 30m /usr/local/bin/python3 -m utils.achievement_trend >> /var/log/achievement_trend.log 2>&1
  if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ achievement_trend.py finished" >> /var/log/cron_exec.log
  else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ achievement_trend.py failed or timeout" >> /var/log/cron_exec.log
  fi

  # 跑成就回填
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🚀 Start achievement_trend_batch_backfill.py" >> /var/log/cron_exec.log
  timeout 60m /usr/local/bin/python3 -m utils.achievement_trend_batch_backfill >> /var/log/achievement_trend_batch_backfill.log 2>&1
  if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ achievement_trend_batch_backfill.py finished" >> /var/log/cron_exec.log
  else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ achievement_trend_batch_backfill.py failed or timeout" >> /var/log/cron_exec.log
  fi

) 9>/tmp/achievement_daily.lock
