#!/bin/bash
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🕒 achievement_daily.sh started" >> /var/log/cron_exec.log
cd /app
/usr/local/bin/python3 -m utils.achievement_trend >> /var/log/cron_exec.log 2>&1
