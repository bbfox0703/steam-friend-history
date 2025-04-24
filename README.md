# 目前大部份皆可執行，部份未驗證

# Steam Friend History

一個輕量級、可在Raspberry Pi 5上跑的系統，可記錄自己的Steam好友列表與變化。  
Steam api key可不用外流，自己用就好。  
好友列表要公開，不然api抓不到會變空值。  

## 📦 目前功能
- 定時自動抓取Steam好友清單
- 網頁界面顯示好友新增與刪除資料 (刪除資料要定時抓取才較準)
- 從App開始定期執行後，記錄好友暱稱變更歷程
- 國別統計與國別分類
- 好友加入趨勢圖
- 好友狀態看板
- 單一遊戲成就達成趨勢圖
- 點擊好友可以連到Steam個人頁面
- **移除記錄功能沒有實際測過**
- 使用Docker簡單部署，可運行於Raspberry Pi 5 (使用SSD裝置)

## 圖例：好友清單
![首頁預覽](./docs/index.png)
## 圖例：國別分析
![國別分析](./docs/country.png)
## 圖例：好友趨勢圖
![好友趨勢圖](./docs/trend.png)
## 圖例：好友狀態看板 
![好友狀態看板 ](./docs/status_board.png)
## 圖例：變更記錄 
從此對方再怎改，也不會改到認不得娘親
![變更記錄 ](./docs/history.png)
## 圖例：成就達成趨勢圖
![成就達成趨勢圖 ](./docs/achievement_trend.png)
### 需要輸入AppID
![appid ](./docs/appid.png)
---

## 🛠️ 安裝方法 (使用Raspberry Pi 5)

### 1. 安裝 Docker
```bash
curl -sSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Git Clone或下載專案
#### 此例為Git clone
```bash
git clone https://github.com/bbfox0703/steam-friend-history.git
cd steam-friend-history
cp .env.example .env
vi .env
```

### 3. 修改 .env的API KEY及ID，填入Steam API KEY、和帳號的64位元ID 76561xxxxxxxxxxxx
Steam api key: https://steamcommunity.com/dev/apikey
**好友列表如未公開，則無法取得資料**

### 4. 建立docker映像檔：
```bash
COMPOSE_BAKE=true docker compose build
docker compose up -d
```

### 5. 如要更新repos
```bash
docker compose down
git pull
COMPOSE_BAKE=true docker compose build
docker compose up -d
```

## 完成後、連線網址
http://伺服器ip:3000

例如ip是192.168.1.100的話：
http://192.168.1.100:3000