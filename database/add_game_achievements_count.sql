-- 刪除目標 appid 中 achievements = 0 的資料
DELETE FROM achievement_trend
WHERE appid IN (790820, 824550)
  AND achievements = 0;

-- 回填數值從最早日 ~ 最新日（包含）
WITH RECURSIVE
date_bounds AS (
  SELECT MIN(date) AS start_date, MAX(date) AS end_date
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
    (790820, 7),
	(617480, 9)
)
INSERT OR REPLACE INTO achievement_trend(date, appid, achievements)
SELECT d.date, t.appid, t.achievements
FROM date_range d
CROSS JOIN targets t;
