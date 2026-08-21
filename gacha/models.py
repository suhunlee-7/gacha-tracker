"""공통 이벤트 스키마 + 시간 정규화. 모든 시각은 KST ISO8601 문자열."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parent.parent
DOCS_DATA = ROOT / "docs" / "data"   # Pages로 서빙되는 공개 데이터
STATE_DIR = ROOT / "data"            # 로컬 전용 (알림 상태 등)

GAME_LABELS = {
    "zzz": "젠존제",
    "arknights": "명일방주",
    "reverse1999": "리버스1999",
    "nte": "이환",
}


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9가-힣]+", "-", s.lower()).strip("-")


def iso(dt: datetime) -> str:
    return dt.astimezone(KST).isoformat(timespec="seconds")


def now_kst() -> datetime:
    return datetime.now(KST)


@dataclass
class Event:
    game: str          # zzz | arknights | reverse1999 | nte
    kind: str          # event | banner
    name: str
    start: str         # ISO8601 KST
    end: str           # ISO8601 KST
    url: str = ""
    name_ko: str | None = None
    extra: dict = field(default_factory=dict)
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"{self.game}:{self.kind}:{slugify(self.name)}:{self.start[:10]}"

    @property
    def start_dt(self) -> datetime:
        return datetime.fromisoformat(self.start)

    @property
    def end_dt(self) -> datetime:
        return datetime.fromisoformat(self.end)

    @property
    def display_name(self) -> str:
        return self.name_ko or self.name


def save_events(events: list[Event], path: Path | None = None) -> None:
    path = path or DOCS_DATA / "events.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated": iso(now_kst()),
        "events": [asdict(e) for e in sorted(events, key=lambda e: (e.start, e.game))],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")


def load_events(path: Path | None = None) -> list[Event]:
    path = path or DOCS_DATA / "events.json"
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [Event(**e) for e in payload["events"]]


def load_state() -> dict:
    p = STATE_DIR / "state.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (STATE_DIR / "state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8"
    )


def load_env() -> dict[str, str]:
    """~/gacha-tracker/.env 의 KEY=VALUE 로드 (의존성 없이)."""
    env: dict[str, str] = {}
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env
