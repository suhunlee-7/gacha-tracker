"""리버스: 1999 — Fandom Events 페이지 wikitable (글로벌 서버, UTC-5 명시)."""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import httpx

from .models import Event, iso

API = "https://reverse1999.fandom.com/api.php"
UTC_M5 = timezone(timedelta(hours=-5))
MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}

# "November 9th, 05:00" / "December 7th, 2023, 05:00"
_DT = re.compile(r"(\w+) (\d+)\w{2},(?: (\d{4}),)? (\d{2}):(\d{2})")
# 이름 행: '''[[Page|Display]]''' 또는 '''[[Page]]'''
_NAME = re.compile(r"'''\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'''")
_VERSION = re.compile(r"\[\[Version ([^\]|]+)(?:\|[^\]]+)?\]\]")


def _parse_range(text: str) -> tuple[str, str] | None:
    m = _DT.findall(text)
    if len(m) != 2:
        return None
    (m1, d1, y1, h1, min1), (m2, d2, y2, h2, min2) = m
    if not y2:
        return None
    end = datetime(int(y2), MONTHS[m2], int(d2), int(h2), int(min2), tzinfo=UTC_M5)
    y1 = int(y1) if y1 else (end.year - 1 if MONTHS[m1] > MONTHS[m2] else end.year)
    start = datetime(y1, MONTHS[m1], int(d1), int(h1), int(min1), tzinfo=UTC_M5)
    return iso(start), iso(end)


def parse(wikitext: str) -> list[Event]:
    events: list[Event] = []
    for row in wikitext.split("|-"):
        name_m = _NAME.search(row)
        rng = _parse_range(row)
        if not name_m or not rng:
            continue
        page, display = name_m.group(1), name_m.group(2) or name_m.group(1)
        ver_m = _VERSION.search(row)
        events.append(Event(
            game="reverse1999", kind="event", name=display,
            start=rng[0], end=rng[1],
            url="https://reverse1999.fandom.com/wiki/" + quote(page.replace(" ", "_")),
            extra={"version": ver_m.group(1) if ver_m else None,
                   "note": "버전 이벤트 시작 = 신규 픽업 시작(동시 오픈)"},
        ))
    return events


def fetch() -> list[Event]:
    r = httpx.get(API, params={
        "action": "parse", "page": "Events", "prop": "wikitext", "format": "json",
    }, timeout=30)
    r.raise_for_status()
    return parse(r.json()["parse"]["wikitext"]["*"])
