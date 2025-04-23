#!/bin/bash
# curl 指令請使用完整形式
# 跑 Flask 更新
curl http://localhost:3000/update

# 保存快照（只留最近 24 份）
cp database/friends.json backups/friends_$(date +'%Y%m%d_%H%M%S').json
ls -1t backups/friends_*.json | tail -n +25 | xargs rm -f