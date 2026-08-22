#!/bin/sh
# cron 진입점. 사용: cron.sh schedule | cron.sh zzz
cd "$(dirname "$0")" || exit 1
export PATH="$HOME/.local/bin:$PATH"
mkdir -p data

case "$1" in
  schedule) uv run run.py >> data/cron.log 2>&1
            uv run translate_names.py >> data/cron.log 2>&1 ;;
  zzz)      uv run zzz_progress.py >> data/cron.log 2>&1 ;;
  *) echo "usage: cron.sh schedule|zzz"; exit 1 ;;
esac

# 대시보드 데이터 push (origin 설정돼 있을 때만 — GitHub Pages 갱신)
if git remote get-url origin >/dev/null 2>&1; then
  git add docs/data >/dev/null 2>&1
  git -c user.name="gacha-bot" -c user.email="bot@gacha-tracker" \
      commit -qm "data: $(date '+%Y-%m-%d %H:%M')" >/dev/null 2>&1 && git push -q >/dev/null 2>&1
fi
exit 0
