#!/bin/bash

# 每天凌晨 3:00 存長期備份
cp database/friends.json backups/daily_$(date +'%Y%m%d').json

# 刪除 30 天以前的 daily 備份
find backups/ -name "daily_*.json" -mtime +30 -delete