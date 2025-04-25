![Steam Friend Info](./docs/Steam%20Friend%20Info.png)
# 🎮 Steam Friend Info（自架版）

一個輕量級、可在 Raspberry Pi 5 或 Linux VM 上運行的 Steam 好友記錄分析系統，使用 Docker 可一鍵部署。所有資料皆保存在本地端，無需將 Steam API Key 上傳到第三方服務，適合重視隱私的用戶。

---

## 🌟 系統功能

- ✅ **好友清單變動追蹤**（新增 / 刪除 / 暱稱變更）
- 🌐 **國別統計分析**（人數統計 + 國家分布圖表）
- 🕹️ **成就達成趨勢分析**（支援輸入 AppID 查詢）
- 🟢 **好友狀態面板**（查看誰在線上、最後上線時間）
- 🔍 **條件篩選器**（國家、有頭像、最近登入天數）
- 💾 **自動備份 / ZIP 匯出 / 快照保留**
- 🐧 **可執行於 Raspberry Pi 5 / Linux 虛擬機（Debian / Ubuntu）**
- 🐳 **使用 Docker 快速部署，可運行於Raspberry Pi 5 (使用SSD裝置)**
- 🔄 **每日 11:05 AM 快取 Steam 遊戲列表（可手動執行）**
  
## ❌ 不支援功能
- 多Steam帳號
- 好友等級資料相關
- 穩私資料如登入 / 登出時間 / 動態牆資料

---

## ⚙️ 運行環境建議

你可以在以下平台運行此系統：

- Raspberry Pi 5（建議接 SSD）
- VMWare / VirtualBox / Hyper-V 等虛擬機（建議記憶體 2GB 以上）
- 或 Windows WSL2（不建議，一些設定需額外調整及測試）

---

## 💡 補充注意事項

- 你的 Steam 帳號需設為「好友清單」與「遊戲庫公開」，否則資料將無法擷取。
- 若擁有遊戲太多（上千款），快取名稱作業將耗時甚久（Steam API 有頻率限制），請留意資源。
- 快取過後的遊戲名稱不會自動隨 Steam 名稱異動，僅當每日 11:05 或你手動快取時、才會補上新遊戲。
- 定時自動抓取Steam好友清單；設計上是每10分鐘更新一次，好友如果太多更新不完可能造成系統報錯，則需要自行調整cron job。時間如果拉太長，會影響好友名字變更的資料精度、及上線狀況精度。

## 圖例：好友清單
![首頁預覽](./docs/index.png)
## 圖例：國別分析
![國別分析](./docs/country.png)
## 圖例：好友趨勢圖
![好友趨勢圖](./docs/trend.png)
## 圖例：好友狀態看板 
![好友狀態看板](./docs/status_board.png)
## 圖例：變更記錄 
從此對方再怎改，也不會改到認不得娘親
![變更記錄](./docs/history.png)
## 圖例：成就達成趨勢圖
![成就達成趨勢圖](./docs/achievement_trend.png)
### 需要輸入AppID
![appid](./docs/appid.png)
---

# 🛠️ 安裝方法 (使用Raspberry Pi 5 8GB版本)

### 1. 安裝 Docker
```bash
cd
curl -sSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Git Clone 或下載專案
#### 此例為Git clone
```bash
sudo apt update;sudo apt upgrade -y
sudo apt install git -y
cd
git clone https://github.com/bbfox0703/steam-friend-history.git
cd steam-friend-history
cp .env.example .env
vi .env
```

### 3.1 修改 .env 的API KEY及ID
填入Steam API KEY、和Steam帳號的64位元ID 76561xxxxxxxxxxxx  
Steam api key: https://steamcommunity.com/dev/apikey  
**好友列表、遊戲資料如未公開，則無法取得資料且有可能報錯**  

Steam帳號ID:  
開啟你的 Steam 個人檔案（例如：https://steamcommunity.com/id/你的自訂ID 或 https://steamcommunity.com/profiles/數字ID）  
如果是 https://steamcommunity.com/profiles/7656119XXXXXXXXXX  
→ 後面這串就是 SteamID64  
  
或是：  
如果有註冊SteamDB https://steamdb.info/ ，SteamDB個人頁面也有  
  
或是：  
前往網站：https://steamid.io/  
輸入你的 Steam 自訂 ID 或個人頁面網址  
會顯示包括：
- SteamID64 <== 此為要的ID
- SteamID3
- SteamID
- CustomURL 等資訊

### 3.2 修改 docker-compose.yml 的 DNS 設定，請調整成自己環境的設置

### 4. 建立docker映像檔：
```bash
COMPOSE_BAKE=true docker compose build
docker compose up -d
```

### 5. 如要更新repos
```bash
docker compose down
#忽略本地變更：
#git reset --hard
git pull
COMPOSE_BAKE=true docker compose build
docker compose up -d
```

## 完成後、連線網址
http://伺服器ip:3000

例如ip是192.168.1.100的話：
http://192.168.1.100:3000

## 如何手動更新遊戲清單
安裝完後，系統會在11:05AM執行遊戲清單更新，如果你裝置的系統不是整天執行，而要取得遊戲清單的話，可手動執行。
### 取得 container name
```bash
docker ps
```
![docker ps](./docs/docker_ps.png)
  
### 執行 docker bash
更改 container name 為你系統上的名字
```bash
docker exec -it steam-friend-history-web-1 /bin/bash
cd /app
PYTHONPATH="." python3 utils/cache_games.py --lang all --sleep 1
```
沒問題的話會開始執行  
![Cache game](./docs/cache_game.png)
- 一個遊戲要花約 10~15 秒，第一次執行一定要讓它全跑完，否則不會寫入資料
- 第二次執行時，只更新缺少的部份
- 遊戲名稱如果變更，系統不會跟著改變
遊戲清單更新後用途：在要看成就走勢時，會列出遊戲供選擇，不然就要自行輸入appid
![Game search](./docs/game_search.png)
  
  
  
# VMware下 Debian OS 內的安裝方法範例：

### 使用root權限，先把使用者加到 sudo group (例子中帳號為 admin01)：
```bash
su -
usermod -aG sudo admin01
```
  
### 以下使用一般使用者帳號 (有進sudo group) 權限執行 (要重新登入)：
```bash
sudo apt update;sudo apt upgrade -y
sudo apt install open-vm-tools -y
sudo apt install git curl -y
cd
curl -sSL https://get.docker.com | sudo sh
sudo apt-get install -y uidmap
dockerd-rootless-setuptool.sh install
id -u
```
記下輸出數字，例如 1000

```bash
vi .bashrc
```
加入：  
export PATH=/usr/bin:$PATH  
export DOCKER_HOST=unix:///run/user/1000/docker.sock  
  
上面的 1000 是之前 id -u輸出的數字  

```bash
sudo loginctl enable-linger admin01
source ~/.bashrc
```
  
#### 測試 Docker 是否可用
```bash
docker version
docker info
docker run hello-world
```
![Hello Docker](./docs/hello_docker.png)
  
```bash
cd
git clone https://github.com/bbfox0703/steam-friend-history.git
cd steam-friend-history
cp .env.example .env
vi .env
```
### 接上方的 Raspberry Pi 5步驟的 3.1
[跳到該處](#31-修改-env-的api-key及id)
  
  
## 🛠️ Windows WSL安裝方法未完成版 (使用Windwos 11 Home)
需要安裝元件：WSL2  
WSL要改的地方不少，例如cron jobs等，還有Python venv問題。這邊不會說明。  

### WSL2 安裝
使用管理員模式開啟命令提示字元 (cmd.exe)  
輸入：  
```powershell
wsl --install
```
![wsl2 ](./docs/wsl2.png)
重開機  

### Windows Store 安裝 Debian
確認WSL版本是 v2
```powershell
wsl -l -v
```

#### 執行 Debian
```powershell
wsl
```
  
Linux OS中：
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install git curl procps -y
sudo apt install python3-venv -y
sudo apt install cron -y
sudo service cron start
cd
git clone https://github.com/bbfox0703/steam-friend-history.git
cd steam-friend-history/
cp .env.example .env
```

修改 .env ，填入steam api key & steam id  

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```
到此網頁應該會起來

### 其它系統定
背景 cronjobs ，請參考steam-friend-cron-wsl、update_wsl.sh、daily_wsl.sh  
如果沒設定背景程式，好友資料和遊戲名稱是不會抓取的，基本上就是整個沒有什麼作用。  
  
  
  
  
## 部份Docker指令

### 看container狀態
```bash
docker ps
```
>CONTAINER ID   IMAGE                      COMMAND                  CREATED              STATUS              PORTS                                         NAMES
>a32ffd9b20f5   steam-friend-history-web   "/usr/bin/supervisord"   About a minute ago   Up About a minute   0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp   steam-friend-history-web-1

由上得知container name為steam-friend-history-web-1

### bash進Container：用以上例子
```bash
docker exec -it steam-friend-history-web-1 /bin/bash
```

### cronjob process是否執行
```bash
docker exec steam-friend-history-web-1 sh -c "ps aux | grep cron"
```

### crob jobs 是否 import
```bash
docker exec -it steam-friend-history-web-1 cat /etc/cron.d/steam-friend-cron
```
  
  
## 如何調整好友資料背景更新頻率
修改 cronjob 資料夾下的 steam-friend-cron 第一行:  
\*\/10 代表每10分鐘一次，調整完後存檔、重起 docker  
其它批次工作的時間，也可在這調整
```bash
*/10 * * * * root /app/cronjob/update.sh >> /var/log/cron_exec.log 2>&1
0 * * * * root echo "✅ Ping cron at $(date)" >> /var/log/cron_exec.log
0 11 * * * root /usr/sbin/logrotate /etc/logrotate.d/steam-friend-logs >> /var/log/cron_exec.log 2>&1
5 11 * * * root /app/cronjob/daily.sh >> /var/log/cron_exec.log 2>&1
2 11 * * * root /app/cronjob/daily_level.sh >> /var/log/cron_exec.log 2>&1
```