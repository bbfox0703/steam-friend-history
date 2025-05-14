-- 先刪除這些 appid 中 achievements 為 0 的紀錄
DELETE FROM achievement_trend
WHERE appid IN (2215430, 2455640, 1046480, 812140, 916440, 281990)
  AND achievements = 0;

-- 接著進行覆蓋或插入
-- 例如 2025-5-13前的皆填滿
WITH RECURSIVE
date_range(date) AS (
  SELECT MIN(date) FROM achievement_trend
  UNION ALL
  SELECT DATE(date, '+1 day') FROM date_range
  WHERE date < '2025-05-13'
),
targets(appid, achievements) AS (
  VALUES
    (2215430, 54),
    (2455640, 51),
    (1046480, 47),
    (812140, 21),
    (916440, 56),
    (281990, 74)
)
INSERT OR REPLACE INTO achievement_trend(date, appid, achievements)
SELECT d.date, t.appid, t.achievements
FROM date_range d
CROSS JOIN targets t;
