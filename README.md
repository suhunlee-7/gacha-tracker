# 가챠 트래커

4개 게임(젠존제·명일방주·리버스1999·이환)의 이벤트/픽업 일정 알림 + 젠존제 진행도 자동 추적.

- `run.py` — 하루 2회: 위키/API에서 일정 수집 → `docs/data/events.json` → 전용 텔레그램 봇으로 신규 시작·D-3·D-1 알림
- `zzz_progress.py` — 하루 3회: HoYoLAB로 배터리·일일활약도·이벤트 보상 진척·천장 조회 + 데일리 체크인. 배터리 220↑·21시 일일 미완 시 알림
- `docs/index.html` — GitHub Pages 대시보드 (버전 로드맵식 타임라인, 폰 북마크용)
- 이벤트 보상·공략 상세는 파싱하지 않음 — 각 이벤트 `url`(위키)을 자비스가 온디맨드로 읽어 답변 (`secretary_rule.md` 참고)

## 셋업 (VPS)

```sh
# 1. 코드 전송 (맥에서)
rsync -a --exclude .venv --exclude data --exclude .git ~/gacha-tracker/ <VPS>:~/gacha-tracker/

# 2. VPS에서
cd ~/gacha-tracker && sh deploy.sh          # uv sync + crontab 등록 (KST/UTC 자동 판별)
cp .env.example .env && chmod 600 .env      # 토큰·쿠키 채우기
git remote add origin https://github.com/<user>/gacha-tracker.git   # Pages push용 (선택)

# 3. 첫 실행 (알림 시딩 — 진행 중 이벤트는 발송 없이 기록됨)
uv run run.py && uv run zzz_progress.py
```

## GitHub Pages

repo Settings → Pages → Deploy from branch → `main` / `/docs`.
cron이 `docs/data/*.json`을 push할 때마다 대시보드 자동 갱신.

## 테스트

`uv run pytest` — 실응답 fixture로 파서 4종 + 알림 dedupe 스모크.
파서가 깨지면(위키 구조 변경) 해당 게임만 실패하고 나머지는 정상 동작, 7일 지속 시 경고 알림 1회.

## 주의

- `.env`는 커밋·Drive 업로드 금지 (HoYoLAB 쿠키 = 계정 접근 권한)
- 명일방주 배너 시각은 위키 기준으로 ±수 시간 오차 가능 (날짜 단위는 정확)
- 이환 파서가 제일 취약 (Fandom Infobox + 반기 섹션 헤더 의존)
