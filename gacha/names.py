"""EN→KO 이름 캐시 (docs/data/names_ko.json). 신규 이름만 translate_names.py가 1회 번역."""
from __future__ import annotations

import json

from .models import DOCS_DATA, Event

CACHE_PATH = DOCS_DATA / "names_ko.json"


def load() -> dict[str, str]:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def save(cache: dict[str, str]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")


def apply(events: list[Event], cache: dict[str, str]) -> None:
    for e in events:
        if e.name_ko:
            continue
        ko = cache.get(e.name)
        if not ko and e.name.endswith(" 픽업"):
            # 번역 캐시 키에서 '픽업' 접미사가 떨어져 돌아오는 경우 폴백
            ko = cache.get(e.name.removesuffix(" 픽업"))
            if ko and not ko.endswith("픽업"):
                ko += " 픽업"
        e.name_ko = ko
