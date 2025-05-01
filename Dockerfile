# fallback 階段建構 tzfallback image
FROM busybox as tzfallback
RUN mkdir -p /etc && \
    echo "Asia/Taipei" > /etc/timezone && \
    ln -snf /usr/share/zoneinfo/Asia/Taipei /etc/localtime

FROM python:3.11-slim-bookworm

# 停用互動模式，避免 tzdata 等卡住
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Taipei

# OS must installed tzdata
# 嘗試從主機複製時區資訊，若失敗則使用 Asia/Taipei 預設值
COPY --from=tzfallback /etc/localtime /etc/localtime
COPY --from=tzfallback /etc/timezone /etc/timezone

WORKDIR /app

# 更新 & 安裝必要套件
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y cron curl supervisor logrotate procps tzdata jq zip sqlite3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 設定時區為 Asia/Taipei
# RUN ln -snf /usr/share/zoneinfo/Asia/Taipei /etc/localtime && echo "Asia/Taipei" > /etc/timezone

# 複製需求並安裝 Python 套件
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 恢復互動模式（可選）
ENV DEBIAN_FRONTEND=dialog

# 複製專案本體
COPY . .

# 確保 utils 是模組（解決 ModuleNotFoundError）
RUN touch /app/utils/__init__.py

# 複製 cronjob 目錄（內含 shell script 與排程設定）
COPY cronjob /app/cronjob
RUN chmod +x /app/cronjob/*.sh

# 複製 logrotate 設定檔
COPY logrotate/steam-friend-logs /etc/logrotate.d/steam-friend-logs

# 複製 cronjob 設定檔與 script
RUN chmod 0644 /app/cronjob/steam-friend-cron && \
    cp /app/cronjob/steam-friend-cron /etc/cron.d/steam-friend-cron

# 複製 supervisor 設定
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord"]
