# Stage 0: fallback 時區來源（含 tzdata）
FROM python:3.11-slim-bookworm AS tzfallback

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Taipei

RUN apt-get update && \
    apt-get install -y tzdata && \
    echo "Asia/Taipei" > /etc/timezone && \
    ln -snf /usr/share/zoneinfo/Asia/Taipei /etc/localtime && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Stage 1: 主建置階段
FROM python:3.11-slim-bookworm

# --- 基本環境設定 ---
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Taipei
WORKDIR /app

# --- 嘗試使用主機掛載時區，否則 fallback copy ---
COPY --from=tzfallback /etc/timezone /etc/timezone
COPY --from=tzfallback /etc/localtime /etc/localtime

# --- 安裝必要套件 ---
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y cron curl supervisor logrotate procps tzdata jq zip sqlite3 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# --- 安裝 Python 套件 ---
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# --- 恢復互動模式（可選）---
ENV DEBIAN_FRONTEND=dialog

# --- 複製專案與設定檔 ---
COPY . .

# --- 確保 utils 是 Python 模組 ---
RUN touch /app/utils/__init__.py

# --- shell script 與 cron 設定 ---
COPY cronjob /app/cronjob
RUN chmod +x /app/cronjob/*.sh

COPY logrotate/steam-friend-logs /etc/logrotate.d/steam-friend-logs
RUN chmod 0644 /app/cronjob/steam-friend-cron && \
    cp /app/cronjob/steam-friend-cron /etc/cron.d/steam-friend-cron

# --- Supervisor 啟動配置 ---
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# --- 容器啟動入口 ---
CMD ["/usr/bin/supervisord"]
