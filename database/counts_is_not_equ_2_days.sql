WITH day_count AS (
  SELECT COUNT(DISTINCT date) AS total_days
  FROM achievement_trend
),
appid_counts AS (
  SELECT appid, COUNT(*) AS record_count
  FROM achievement_trend
  GROUP BY appid
)
SELECT a.appid, a.record_count, d.total_days
FROM appid_counts a
CROSS JOIN day_count d
WHERE a.record_count != d.total_days
ORDER BY a.appid;
