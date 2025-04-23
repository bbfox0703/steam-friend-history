FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

# 安裝 cron + curl + supervisor
RUN apt-get update && \
    apt-get install -y cron curl supervisor && \
    rm -rf /var/lib/apt/lists/*

# 複製專案
COPY . .

# 複製 cronjob 設定檔與 script
RUN chmod 0644 /cronjob/steam-friend-cron && \
    cp /cronjob/steam-friend-cron /etc/cron.d/steam-friend-cron && \
    chmod +x /app/cronjob/update.sh

# 複製 supervisor 設定
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord"]