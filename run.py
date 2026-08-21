"""cron 진입점: 4개 게임 fetch → events.json → 알림. 게임별 실패 격리."""
from __future__ import annotations

import traceback
from datetime import datetime, timedelta

from gacha import fetch_arknights, fetch_nte, fetch_r1999, fetch_zzz
from gacha.models import (GAME_LABELS, iso, load_events, load_state, now_kst,
                          save_events, save_state)
from gacha.notify import notify, send_telegram

FETCHERS = {
    "zzz": fetch_zzz.fetch,
    "arknights": fetch_arknights.fetch,
    "reverse1999": fetch_r1999.fetch,
    "nte": fetch_nte.fetch,
}
STALE_DAYS = 7


def main() -> None:
    now = now_kst()
    state = load_state()
    fetch_log: dict = state.setdefault("fetch", {})
    old = load_events()
    merged = []

    for game, fetcher in FETCHERS.items():
        try:
            events = fetcher()
            assert events, "empty result"
            fetch_log[game] = {"ok": iso(now), "warned": False}
        except Exception:
            print(f"[{game}] fetch 실패:\n{traceback.format_exc()}")
            events = [e for e in old if e.game == game]  # 기존 데이터 유지
            info = fetch_log.setdefault(game, {"ok": None, "warned": False})
            last_ok = datetime.fromisoformat(info["ok"]) if info.get("ok") else None
            if (last_ok is None or now - last_ok > timedelta(days=STALE_DAYS)) and not info.get("warned"):
                send_telegram(f"⚠️ [{GAME_LABELS[game]}] 일정 수집이 {STALE_DAYS}일째 실패 중 — 파서 점검 필요")
                info["warned"] = True
        merged += events

    # 종료 30일 지난 항목은 대시보드에서도 제외
    cutoff = now - timedelta(days=30)
    merged = [e for e in merged if e.end_dt >= cutoff]

    save_events(merged)
    state = notify(merged, state)
    save_state(state)
    print(f"OK — {len(merged)}건 저장, {iso(now)}")


if __name__ == "__main__":
    main()
