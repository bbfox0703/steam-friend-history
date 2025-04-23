#!/bin/bash

# Flask 更新資料
curl -s http://localhost:3000/update

# 快照儲存路徑
DB_PATH="/app/database/friends.json"
BACKUP_DIR="/app/backups"

# 檢查檔案是否存在再進行備份
if [ -f "$DB_PATH" ]; then
  cp "$DB_PATH" "$BACKUP_DIR/friends_$(date +'%Y%m%d_%H%M%S').json"
fi

# 清除多餘快照，僅保留最新 30 份
ls -1t "$BACKUP_DIR"/friends_*.json 2>/dev/null | tail -n +31 | xargs -r rm -f
