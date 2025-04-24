FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

# 安裝 cron + curl + supervisor + logrotate + ps
RUN apt-get update && \
    apt-get install -y cron curl supervisor logrotate procps && \
    rm -rf /var/lib/apt/lists/*	

# 複製專案
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
    cp /app/cronjob/steam-friend-cron /etc/cron.d/steam-friend-cron && \
    chmod +x /app/cronjob/update.sh

# 複製 supervisor 設定
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord"]

RUN mkdir -p /app/database
