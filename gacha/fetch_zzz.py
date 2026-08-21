"""젠존제 — ennead.cc 캘린더 API (무인증, 한국어)."""
from __future__ import annotations

from datetime import datetime

import httpx

from .models import KST, Event, iso, slugify

URL = "https://api.ennead.cc/mihoyo/zenless/calendar?lang=ko-kr"
WIKI = "https://zenless-zone-zero.fandom.com/wiki/Event"


def _ts(unix: int) -> str:
    return iso(datetime.fromtimestamp(unix, tz=KST))


def parse(payload: dict) -> list[Event]:
    events: list[Event] = []
    for e in payload.get("events", []):
        name = " ".join(str(e["name"]).split())  # 개행 등 정리
        events.append(Event(
            game="zzz", kind="event", name=name, name_ko=name,
            start=_ts(e["start_time"]), end=_ts(e["end_time"]),
            url=WIKI,
            extra={"polychrome": e.get("polychrome"), "image": e.get("image_url")},
        ))
    for b in payload.get("banners", []):
        agents = b.get("agents") or []
        engines = b.get("w_engines") or []
        s_rank = [a["name"] for a in agents if a.get("rarity") == "S"] or \
                 [w.get("name") for w in engines if w.get("rarity") == "S" and w.get("name")]
        featured = ", ".join(s_rank) or "상설"
        is_weapon = bool(engines) and not agents
        name = f"{featured} 픽업" + (" (W-엔진)" if is_weapon else "")
        events.append(Event(
            game="zzz", kind="banner", name=name, name_ko=name,
            start=_ts(b["start_time"]), end=_ts(b["end_time"]),
            url=WIKI,
            id=f"zzz:banner:{slugify(featured)}:{_ts(b['start_time'])[:10]}",
            extra={
                "version": b.get("version"),
                "banner_type": b.get("banner_type"),
                "agents": [a["name"] for a in agents],
                "icons": [a.get("icon") for a in agents if a.get("rarity") == "S"],
            },
        ))
    return events


def fetch() -> list[Event]:
    r = httpx.get(URL, timeout=30)
    r.raise_for_status()
    return parse(r.json())
