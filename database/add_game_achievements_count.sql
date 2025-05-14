-- 刪除目標 appid 中 achievements = 0 的資料
DELETE FROM achievement_trend
WHERE appid IN (1121560, 1257290, 1999770, 2138090, 936160, 1152300, 
                936180, 936190, 1152310, 921570, 3319980, 1450120,
				1450090, 1450080, 1457510, 1562940, 1060220)
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
    (1121560, 49),
	(1257290, 49),
	(1999770, 48),
	(2138090, 49),
	(936160, 54),
	(1152300, 41),
	(936180, 29),
	(936190, 44),
	(1152310, 53),
	(921570, 11),
	(3319980, 53),
	(1450120, 51),
	(1450090, 51),
	(1450080, 53),
	(1457510, 53),
	(1562940, 53),
	(1060220, 42)
)
INSERT OR REPLACE INTO achievement_trend(date, appid, achievements)
SELECT d.date, t.appid, t.achievements
FROM date_range d
CROSS JOIN targets t;
