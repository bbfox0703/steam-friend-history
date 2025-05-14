WITH date_info AS (
  SELECT MAX(date) AS max_date FROM achievement_trend
),
recent_appids AS (
  SELECT DISTINCT appid
  FROM achievement_trend, date_info
  WHERE date >= DATE(max_date, '-2 day') -- 最近三天（含 max_date）
),
old_appids AS (
  SELECT DISTINCT appid
  FROM achievement_trend, date_info
  WHERE date < DATE(max_date, '-2 day')  -- 三天前以前
)
SELECT appid
FROM recent_appids
WHERE appid NOT IN (SELECT appid FROM old_appids)
ORDER BY appid;
