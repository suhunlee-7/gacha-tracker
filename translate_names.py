"""신규 영문 이벤트·배너명을 claude CLI로 한국어화해 캐시. claude 없으면 조용히 건너뜀."""
from __future__ import annotations

import json
import re
import shutil
import subprocess

from gacha import names
from gacha.models import load_events, save_events

GAME_KO = {"arknights": "명일방주", "reverse1999": "리버스: 1999", "nte": "이환(NTE)"}
BATCH = 40


def main() -> None:
    events = load_events()
    cache = names.load()
    todo = sorted({(e.game, e.name) for e in events
                   if e.game in GAME_KO and e.name not in cache})[:BATCH]

    if todo and shutil.which("claude"):
        items = "\n".join(f"- [{GAME_KO[g]}] {n}" for g, n in todo)
        prompt = (
            "아래는 가챠 게임의 이벤트/픽업 배너/캐릭터 이름이다. 각 항목의 **한국 서버 공식 명칭**을 "
            "아는 경우 그것을, 확실하지 않으면 자연스러운 한국어 번역을 제시하라. "
            "'픽업' 같은 한국어 접미사는 유지하고 캐릭터 이름은 공식 한국어 표기로. "
            "설명 없이 JSON 하나만 출력: {\"영문 원문\": \"한국어\"} (원문 키는 게임 태그 제외, 그대로).\n"
            + items)
        try:
            out = subprocess.run(
                ["claude", "-p", prompt, "--model", "sonnet"],
                capture_output=True, text=True, timeout=600).stdout
            m = re.search(r"\{.*\}", out, re.S)
            if m:
                new = {k: v for k, v in json.loads(m.group()).items()
                       if isinstance(v, str) and v.strip()}
                cache.update(new)
                names.save(cache)
                print(f"[names] {len(new)}건 번역 캐시 추가")
        except Exception as e:
            print(f"[names] 번역 실패 (다음 주기 재시도): {e}")
    elif todo:
        print(f"[names] claude CLI 없음 — {len(todo)}건 미번역 유지")

    names.apply(events, cache)
    save_events(events)


if __name__ == "__main__":
    main()
