"""명일방주 — arknights.wiki.gg Cargo API. global 서버 시각 = KST 그대로 (KR 공지와 대조 검증됨)."""
from __future__ import annotations

from datetime import timedelta
from urllib.parse import quote

import httpx

from .models import Event, now_kst

API = "https://arknights.wiki.gg/api.php"


def _wiki_url(page: str) -> str:
    return "https://arknights.wiki.gg/wiki/" + quote(page.replace(" ", "_"))


def _kst_iso(s: str) -> str:
    # "2026-08-20 17:00:00" (naive, KST로 검증됨) → ISO
    return s.replace(" ", "T") + "+09:00"


def _query(tables: str, fields: str, where: str) -> list[dict]:
    r = httpx.get(API, params={
        "action": "cargoquery", "format": "json", "limit": 100,
        "tables": tables, "fields": fields, "where": where,
    }, timeout=30, headers={"User-Agent": "gacha-tracker/0.1 (personal)"})
    r.raise_for_status()
    return [row["title"] for row in r.json().get("cargoquery", [])]


def parse(event_rows: list[dict], banner_rows: list[dict]) -> list[Event]:
    events: list[Event] = []
    for row in event_rows:
        if not row.get("startTime") or not row.get("endTime"):
            continue
        name = row["event"]
        events.append(Event(
            game="arknights", kind="event", name=name,
            start=_kst_iso(row["startTime"]), end=_kst_iso(row["endTime"]),
            url=_wiki_url(name.split("/")[0]),
        ))
    for row in banner_rows:
        if not row.get("startTimeGlobal") or not row.get("endTimeGlobal"):
            continue
        ops = [o.strip() for o in (row.get("operators") or "").split(",") if o.strip()]
        name = row.get("name") or (", ".join(ops[:3]) + " 픽업" if ops else "")
        if not name:
            continue
        events.append(Event(
            game="arknights", kind="banner", name=name,
            start=_kst_iso(row["startTimeGlobal"]), end=_kst_iso(row["endTimeGlobal"]),
            url=_wiki_url("Headhunting"),
            extra={"operators": ops, "banner_type": row.get("bannerType")},
        ))
    return events


def fetch() -> list[Event]:
    cutoff = (now_kst() - timedelta(days=30)).strftime("%Y-%m-%d")
    event_rows = _query(
        "EventServerDetails", "event,server,startTime,endTime",
        f"server='global' AND endTime>'{cutoff}'",
    )
    banner_rows = _query(
        "Banners", "name,operators,bannerType,startTimeGlobal,endTimeGlobal",
        f"endTimeGlobal>'{cutoff}'",
    )
    return parse(event_rows, banner_rows)
