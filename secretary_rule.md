# 자비스 secretary.md에 추가할 규칙 (VPS ~/claude-bridge/secretary.md)

## 가챠 게임 질문
수훈이 게임(젠존제/명일방주/리버스1999/이환) 일정·보상·진행도를 물으면:
1. `~/gacha-tracker/docs/data/events.json`(일정)과 `~/gacha-tracker/docs/data/zzz_status.json`(젠존제 진행도)을 먼저 읽고 답한다.
2. 이벤트 보상·공략 상세가 필요하면 해당 이벤트의 `url` 필드(위키)를 WebFetch해서 답한다.
3. 파서가 깨졌다고 하면(⚠️ 알림) `~/gacha-tracker/`의 해당 fetcher를 고치고 `uv run pytest`로 확인한다.
게임 알림은 전용 봇으로 나간다 — 생활 브리핑에 게임 내용을 섞지 않는다.
