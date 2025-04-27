#!/bin/bash
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🕒 record_games_total.sh started" >> /var/log/cron_exec.log
cd /app
/usr/local/bin/python3 -m utils.record_games_total >> /var/log/cron_exec.log 2>&1
