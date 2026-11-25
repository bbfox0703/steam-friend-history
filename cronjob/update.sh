#!/bin/bash
# 取得好友列表及更名歷史資料；此指令使用大量api call

# 記錄開始時間
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🕒 update.sh started at $(date)" >> /var/log/cron_exec.log
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔍 update.sh cron: Working dir: $(pwd)" >> /var/log/cron_exec.log

# Flask 更新資料
if ! curl -fsS http://localhost:3000/update; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ /update failed (詳見 /app/logs/app.log)" | tee -a /var/log/cron_exec.log
fi
echo

# 快照儲存路徑
DB_PATH="/app/database/friends.json"
BACKUP_DIR="/app/backups"

# 檢查檔案是否存在再進行備份
if [ -f "$DB_PATH" ]; then
  cp "$DB_PATH" "$BACKUP_DIR/friends_$(date +'%Y%m%d_%H%M%S').json"
fi

# 清除多餘快照，僅保留最新 30 份
ls -1t "$BACKUP_DIR"/friends_*.json 2>/dev/null | tail -n +31 | xargs -r rm -f
