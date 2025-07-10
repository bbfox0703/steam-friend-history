#!/bin/bash
# SQLite備份

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🕒 backup_sqlite.sh started at $(date)" >> /var/log/cron_exec.log
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔍 backup_sqlite.sh cron: Working dir: $(pwd)" >> /var/log/cron_exec.log

# 設定來源資料庫位置與備份目錄
DB_FILE="/app/database/steam_data.db"
BACKUP_DIR="/app/backups"

# 確保備份目錄存在
mkdir -p "$BACKUP_DIR"

# 產生時間戳記
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")

# 設定中繼備份檔名
TEMP_BACKUP="$BACKUP_DIR/steam_data_$TIMESTAMP.db"
ZIP_BACKUP="$BACKUP_DIR/steam_data_$TIMESTAMP.db.zip"

# 複製資料庫
cp "$DB_FILE" "$TEMP_BACKUP"

# 壓縮成 zip
zip -j "$ZIP_BACKUP" "$TEMP_BACKUP"

# 刪除未壓縮的 db 檔案
rm "$TEMP_BACKUP"

# 刪除 30 天以前的 daily 備份
find /app/backups/ -name "steam_data_*.db.zip" -mtime +30 -delete

echo "[$(date)] 資料庫已壓縮備份：$ZIP_BACKUP"
