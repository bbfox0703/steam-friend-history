# 📄 Python Scripts 說明

---

## `achievement_trend.py`
- 功能：每天自動從 Steam API 取得最近14天內有玩過的遊戲，抓取每款遊戲的成就達成數。
- 寫入檔案：`/database/achievement_trend.json`
- 特色：可搭配每日 cron job 定時更新成就趨勢資料。
- 注意事項：抓取每款遊戲成就時，建議加 `time.sleep(0.5)` 延遲，避免 Steam API 限速。

---

## `backfill_fake_data.py`
- 功能：產生假資料，用於補齊 `achievement_trend.json` 測試用。
- 用途：讓成就趨勢圖表在無真實資料情況下也能正常顯示和開發。
- 寫入檔案：直接修改 `/database/achievement_trend.json`。

---

## `backfill_fake_gameplay.py`
- 功能：產生假資料，用於補齊 `playtime_trend.json` 測試用。
- 用途：模擬每日遊玩時間變化，用於測試遊玩時間趨勢功能。
- 寫入檔案：直接修改 `/database/playtime_trend.json`。

---

## `backup.py`
- 功能：備份 `/database/` 資料夾中的所有資料（如好友清單、成就快照等）。
- 產出格式：自動打包成 `.zip` 檔案，存放到 `/backups/` 資料夾。
- 用途：確保每天資料變更前有快照可回溯。

---

## `cache_games.py`
- 功能：從 Steam API 拉取持有的所有遊戲清單，並快取遊戲的中/日/英文名稱。
- 寫入檔案：`/database/game_titles.json`
- 特色：支援繁體中文、日文、英文三語快取，用於後續多語系顯示。

---

## `fill_missing_achievements.py`
- 功能：補齊成就資料。
- 邏輯：如果今天的 `achievement_trend.json` 裡某個 appid 消失，沿用昨天的資料補齊。
- 用途：保持成就趨勢資料的連續性，避免因 Steam Recent 限制導致成就趨勢中斷。

---

## `i18n.py`
- 功能：多語系管理工具。
- 用途：解析、載入、切換不同語言（zh-tw, ja, en）顯示。
- 特色：自動偵測瀏覽器語系，並套用對應翻譯 JSON。

---

## `record_games_total.py`
- 功能：每天記錄持有遊戲總數，生成總量變化趨勢資料。
- 寫入檔案：`/database/games_total_history.json`
- 用途：讓 `/games-trend` 頁面可以畫出「持有總數趨勢」與「每日變動數」。

---

## `steam_api.py`
- 功能：Steam Web API 通訊模組。
- 提供功能：
  - 抓取好友清單
  - 抓取成就資料
  - 抓取持有遊戲清單
  - 抓取最近遊戲列表
- 特色：統一封裝 Steam API 存取，方便其他模組呼叫。
