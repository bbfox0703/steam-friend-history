#!/bin/bash

# 讀取 .env
set -o allexport
source /app/.env
set +o allexport

OUT_PATH="/app/database/level_history.json"
TODAY=$(date +%F)

LEVEL=$(curl -s "https://api.steampowered.com/IPlayerService/GetSteamLevel/v1/?key=$STEAM_API_KEY&steamid=$STEAM_USER_ID" | jq '.response.player_level')

if [ -n "$LEVEL" ]; then
  tmp=$(mktemp)
  if [ -f "$OUT_PATH" ]; then
    # 如果當日已存在，就跳過
    if jq -e --arg d "$TODAY" 'has($d)' "$OUT_PATH" > /dev/null; then
      echo "🔁 $TODAY 已存在，跳過"
    else
      jq --arg d "$TODAY" --argjson l "$LEVEL" '. + {($d): $l}' "$OUT_PATH" > "$tmp" && mv "$tmp" "$OUT_PATH"
      echo "✅ 已記錄 $TODAY 等級：$LEVEL"
    fi
  else
    echo "{\"$TODAY\": $LEVEL}" > "$OUT_PATH"
    echo "✅ 新增紀錄：$TODAY 等級：$LEVEL"
  fi
fi
