FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

# 安裝 curl + cron
RUN apt-get update && \
    apt-get install -y cron curl && \
    rm -rf /var/lib/apt/lists/*

# 複製專案檔案
COPY . .

# 複製 crontab 設定檔
COPY cronjob /etc/cron.d/steam-friend-cron

# 給予權限
RUN chmod 0644 /etc/cron.d/steam-friend-cron

# 設定 crontab 並啟動 cron + flask
CMD cron && python app.py
