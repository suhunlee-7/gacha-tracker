#!/bin/sh
# VPS에서 1회 실행: 의존성 설치 + crontab 등록 (기존 crontab 보존)
set -e
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"

command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync -q
chmod +x cron.sh

DIR="$(pwd)"
if [ "$(cat /etc/timezone 2>/dev/null)" = "Asia/Seoul" ]; then
  LINES="30 6,18 * * * $DIR/cron.sh schedule
0 8,14,21 * * * $DIR/cron.sh zzz"
else  # UTC 가정: 06:30/18:30 KST = 21:30/09:30 UTC, 08/14/21 KST = 23/05/12 UTC
  LINES="30 21,9 * * * $DIR/cron.sh schedule
0 23,5,12 * * * $DIR/cron.sh zzz"
fi

( crontab -l 2>/dev/null | grep -v gacha-tracker ; echo "$LINES" ) | crontab -
echo "설치 완료. crontab:"
crontab -l | grep gacha-tracker
echo "다음: .env 채우기 (cp .env.example .env && chmod 600 .env)"
