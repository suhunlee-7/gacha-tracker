"""알림 판정 + 전용 텔레그램 봇 발송. state.json으로 중복 방지."""
from __future__ import annotations

from datetime import datetime, timedelta

import httpx

from .models import GAME_LABELS, Event, load_env, now_kst

WEEKDAYS = "월화수목금토일"


def fmt_dt(dt: datetime) -> str:
    return f"{dt.month}/{dt.day}({WEEKDAYS[dt.weekday()]}) {dt:%H:%M}"


def build_alerts(events: list[Event], state: dict, now: datetime | None = None) -> list[tuple[str, str, str]]:
    """(event_id, tag, line) 목록. state는 수정하지 않음."""
    now = now or now_kst()
    notified: dict = state.get("notified", {})
    alerts: list[tuple[str, str, str]] = []
    for e in events:
        sent = notified.get(e.id, [])
        label = GAME_LABELS[e.game]
        kind = "픽업" if e.kind == "banner" else "이벤트"
        left = e.end_dt - now
        if e.start_dt <= now < e.end_dt and (now - e.start_dt) <= timedelta(hours=36) and "new" not in sent:
            alerts.append((e.id, "new",
                f"🆕 [{label}] {kind} 시작 — <b>{e.display_name}</b>\n"
                f"   ~{fmt_dt(e.end_dt)} 종료"))
        elif timedelta(hours=36) < left <= timedelta(days=3) and "d3" not in sent and "d1" not in sent:
            alerts.append((e.id, "d3",
                f"⏳ [{label}] <b>{e.display_name}</b> 종료 D-3\n"
                f"   ~{fmt_dt(e.end_dt)}"))
        elif timedelta(0) < left <= timedelta(hours=36) and "d1" not in sent:
            alerts.append((e.id, "d1",
                f"🚨 [{label}] <b>{e.display_name}</b> 종료 임박!\n"
                f"   ~{fmt_dt(e.end_dt)}"))
    return alerts


def send_telegram(text: str) -> bool:
    env = load_env()
    token, chat = env.get("TG_GAME_BOT_TOKEN"), env.get("TG_CHAT_ID")
    if not token or not chat:
        print("[notify] 봇 미설정 — 콘솔 출력:\n" + text)
        return False
    r = httpx.post(f"https://api.telegram.org/bot{token}/sendMessage", json={
        "chat_id": chat, "text": text, "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }, timeout=30)
    r.raise_for_status()
    return True


def notify(events: list[Event], state: dict) -> dict:
    """알림 발송 후 갱신된 state 반환."""
    first_run = "notified" not in state
    alerts = build_alerts(events, state)
    notified = state.setdefault("notified", {})
    if first_run:
        # 첫 실행: 기존 진행분 전부 발송 없이 시딩 (백필 폭탄 방지)
        for eid, tag, _ in alerts:
            notified.setdefault(eid, []).append(tag)
        now = now_kst()
        live = [e for e in events if e.start_dt <= now < e.end_dt]
        send_telegram("🎮 가챠 트래커 가동 시작!\n현재 진행 중: " +
                      ", ".join(f"{GAME_LABELS[e.game]} {len([x for x in live if x.game == e.game])}건"
                                for e in {e.game: e for e in live}.values()))
        return state
    if alerts:
        send_telegram("\n\n".join(line for _, _, line in alerts))
        for eid, tag, _ in alerts:
            notified.setdefault(eid, []).append(tag)
    # 오래된 state 청소
    live_ids = {e.id for e in events}
    for eid in list(notified):
        if eid not in live_ids:
            del notified[eid]
    return state
