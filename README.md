# 未完成

# Steam Friend History

一個輕量級的 Raspberry Pi 專用系統，記錄自己的 Steam 好友列表與變化。

---

## 📦 預計功能、但可能沒有
- 每天自動抓取 Steam 好友清單
- 自動備份每日快照
- 網頁界面顯示好友新增與刪除
- 好友暱稱變更記錄
- 國別統計與國別分類
- 點擊好友可以連到 Steam 個人頁面
- 使用 Docker 簡單部署

---

## 🛠️ 安裝方法

### 1. 安裝 Docker
```bash
curl -sSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Clone 或下載專案

```bash
git clone https://github.com/bbfox0703/steam-friend-history.git
cd steam-friend-history
cp .env.example .env
vi .env
```

修改 .env APIKEY & ID，填入Steam APIKEY和帳號的64位元ID 76561xxxxxxxxxxxx

```bash
docker compose build
docker compose up -d
```

如要更新repos
```bash
docker compose down
git pull
docker compose build
docker compose up -d
```