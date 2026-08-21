"""이환(NTE) — Fandom Version 페이지 Infobox + 배너 반기 섹션. 제일 취약한 파서."""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import httpx

from .models import Event, iso, now_kst

API = "https://neverness-to-everness.fandom.com/api.php"
GMT8 = timezone(timedelta(hours=8))
MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}

_FIELD = re.compile(r"\|\s*(time_start|time_end)\s*=\s*([\d\-: ]+)")
# "==== First Half (August 19 - September 9, 2026) ===="
_HALF = re.compile(
    r"====\s*(First|Second) Half \((\w+) (\d+) - (\w+) (\d+), (\d{4})\)\s*====(.*?)(?=====|\Z)",
    re.S)
_SRANK = re.compile(r"Featured S-Rank:'''\s*(?:\[\[File:[^\]]+\]\]\s*)*\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
_EVENT_LINKS = re.compile(r"==\s*Events\s*==\s*(.*?)(?=\n==[^=]|\Z)", re.S)
_LINK = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


def _wiki_url(page: str) -> str:
    return "https://neverness-to-everness.fandom.com/wiki/" + quote(page.replace(" ", "_"))


def parse_version(wikitext: str, title: str) -> list[Event]:
    fields = dict(_FIELD.findall(wikitext))
    if "time_start" not in fields or "time_end" not in fields:
        return []
    # Infobox 시각은 GMT+8 (time_start_offset 필드로 명시됨)
    start = datetime.strptime(fields["time_start"].strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=GMT8)
    end = datetime.strptime(fields["time_end"].strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=GMT8)

    ev_m = _EVENT_LINKS.search(wikitext)
    event_names = _LINK.findall(ev_m.group(1)) if ev_m else []

    ver = title.split("/")[-1]
    events: list[Event] = [Event(
        game="nte", kind="event", name=f"버전 {ver}",
        start=iso(start), end=iso(end), url=_wiki_url(title),
        extra={"events": event_names},
    )]

    for half, m1, d1, m2, d2, year, body in _HALF.findall(wikitext):
        names = _SRANK.findall(body) or \
            [n for n in _LINK.findall(body) if not n.startswith("File:")][:2]
        if not names:
            continue
        y1 = int(year) - 1 if MONTHS[m1] > MONTHS[m2] else int(year)
        # ponytail: 반기 경계 시각은 위키에 날짜만 있음 — 일 단위 근사 (12:00 KST)
        h_start = datetime(y1, MONTHS[m1], int(d1), 12, 0, tzinfo=GMT8)
        h_end = datetime(int(year), MONTHS[m2], int(d2), 12, 0, tzinfo=GMT8)
        if half == "First":
            h_start = start  # 전반 픽업은 버전 시작과 동시
        else:
            h_end = end      # 후반 픽업은 버전 종료까지
        featured = ", ".join(names)
        events.append(Event(
            game="nte", kind="banner", name=f"{featured} 픽업",
            start=iso(h_start), end=iso(h_end), url=_wiki_url(title),
            extra={"version": ver, "half": half.lower(), "featured": names},
        ))
    return events


def _version_titles() -> list[str]:
    r = httpx.get(API, params={
        "action": "query", "list": "allpages", "apprefix": "Version/",
        "aplimit": 50, "format": "json",
    }, timeout=30)
    r.raise_for_status()
    titles = [p["title"] for p in r.json()["query"]["allpages"]]

    def key(t: str):
        m = re.search(r"(\d+)\.(\d+)$", t)
        return (int(m.group(1)), int(m.group(2))) if m else (-1, -1)

    return sorted((t for t in titles if key(t) != (-1, -1)), key=key)


def fetch() -> list[Event]:
    events: list[Event] = []
    for title in _version_titles()[-3:]:  # 최신 3개 버전만 (과거+미래 커버)
        r = httpx.get(API, params={
            "action": "parse", "page": title, "prop": "wikitext", "format": "json",
        }, timeout=30)
        r.raise_for_status()
        if "parse" not in r.json():
            continue
        events += parse_version(r.json()["parse"]["wikitext"]["*"], title)
    # 종료 30일 지난 것 제외
    cutoff = now_kst() - timedelta(days=30)
    return [e for e in events if e.end_dt >= cutoff]
