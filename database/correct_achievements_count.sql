-- sqlite3 ./database/steam_data.db
--
-- 回填數值到從最舊日期 ~ 最新日期 -1，填入成就數
-- 久沒玩又已經有成就的遊戲，會造成成就圖顯示不正確數值
-- 使用此SQL回填資料
-- 
--
-- 這段會自動
-- MIN(date)：找出你表中最早的日期作為回填起點
-- MAX(date) - 1 day：找出目前資料中最新的一天，往前一天作為回填終點
-- 不需要手動指定日期，未來自動適應資料的增長
--
-- 刪除目標 appid 中 achievements = 0 的資料
DELETE FROM achievement_trend
WHERE appid IN (524220, 645730, 1128920, 1245620)
  AND achievements = 0;

WITH RECURSIVE
date_bounds AS (
  SELECT MIN(date) AS start_date, DATE(MAX(date), '-1 day') AS end_date
  FROM achievement_trend
),
date_range(date) AS (
  SELECT start_date FROM date_bounds
  UNION ALL
  SELECT DATE(date, '+1 day') FROM date_range, date_bounds
  WHERE date < end_date
),
targets(appid, achievements) AS (
  VALUES
    (524220, 23),
    (645730, 11),
	(1128920, 28),
	(1245620, 4)
)
INSERT OR REPLACE INTO achievement_trend(date, appid, achievements)
SELECT d.date, t.appid, t.achievements
FROM date_range d
CROSS JOIN targets t;
