"""파서 4종 스모크 — 실응답 fixture 기준. 파서가 깨지면 여기서 먼저 죽는다."""
import json
from pathlib import Path

from gacha import fetch_arknights, fetch_nte, fetch_r1999, fetch_zzz
from gacha.notify import build_alerts
from gacha.models import Event, now_kst

FX = Path(__file__).parent / "fixtures"


def _check(events, game):
    assert events, f"{game}: 파싱 결과 0건"
    for e in events:
        assert e.game == game and e.kind in ("event", "banner")
        assert e.name and not e.name.startswith("File:")
        assert e.start.endswith("+09:00") and e.end.endswith("+09:00"), "KST 아님"
        assert e.start < e.end
    return events


def test_zzz():
    payload = json.loads((FX / "zzz_calendar.json").read_text())
    events = _check(fetch_zzz.parse(payload), "zzz")
    assert any(e.kind == "banner" for e in events)


def test_arknights():
    evs = json.loads((FX / "ak_events.json").read_text())
    bans = json.loads((FX / "ak_banners.json").read_text())
    events = _check(fetch_arknights.parse(evs, bans), "arknights")
    # KR 공지 대조 검증된 앵커: 위수 협의(Stronghold ... Part 2) 8/20 17:00 KST
    anchor = [e for e in events if "Stronghold" in e.name]
    assert anchor and anchor[0].start == "2026-08-20T17:00:00+09:00"


def test_r1999():
    wikitext = (FX / "r1999_events.wikitext").read_text()
    events = _check(fetch_r1999.parse(wikitext), "reverse1999")
    # UTC-5 05:00 → KST 19:00 변환 확인 (앵커 이벤트)
    anchor = [e for e in events if e.name == "Call from the Alma Mater"]
    assert anchor and anchor[0].start == "2026-08-06T19:00:00+09:00"


def test_nte():
    wikitext = (FX / "nte_v13.wikitext").read_text()
    events = fetch_nte.parse_version(wikitext, "Version/1.3")
    _check(events, "nte")
    banners = [e for e in events if e.kind == "banner"]
    assert {b.extra["half"] for b in banners} == {"first", "second"}
    assert any("Zankou" in b.name for b in banners)


def test_alert_dedupe():
    from datetime import timedelta
    from gacha.models import iso
    now = now_kst()
    e = Event(game="zzz", kind="event", name="테스트",
              start=iso(now - timedelta(hours=1)), end=iso(now + timedelta(days=30)))
    alerts = build_alerts([e], {"notified": {}})
    assert [a[1] for a in alerts] == ["new"]
    alerts2 = build_alerts([e], {"notified": {e.id: ["new"]}})
    assert alerts2 == []
