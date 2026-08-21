"""젠존제 진행도 + 데일리 체크인 (genshin.py, HoYoLAB 쿠키).
cron 08/14/21시. 쿠키 미설정이면 조용히 종료."""
from __future__ import annotations

import asyncio
import json
import traceback

from gacha.models import DOCS_DATA, iso, load_env, load_state, now_kst, save_state
from gacha.notify import send_telegram

BATTERY_WARN = 220


def _today() -> str:
    return now_kst().strftime("%Y-%m-%d")


async def collect(client, state: dict) -> dict:
    import genshin

    status: dict = {"updated": iso(now_kst())}

    notes = await client.get_zzz_notes()
    status["battery"] = {
        "current": notes.battery_charge.current,
        "max": notes.battery_charge.max,
        "seconds_till_full": notes.battery_charge.seconds_till_full,
    }
    status["engagement"] = {"current": notes.engagement.current, "max": notes.engagement.max}
    if notes.weekly_task:
        status["weekly"] = {"current": notes.weekly_task.cur_point, "max": notes.weekly_task.max_point}

    try:
        cal = await client.get_zzz_event_calendar()
        status["events"] = [{
            "name": e.name,
            "obtained": e.obtained_monochromes, "max": e.max_monochromes,
            "end": iso(e.end) if e.end else None,
            "status": str(e.status),
        } for e in cal]
    except Exception:
        status["events_error"] = traceback.format_exc(limit=1)

    try:
        gi = await client.get_zzz_gacha_info()
        status["currencies"] = {
            "polychrome": gi.currencies.polychrome,
            "master_tape": gi.currencies.master_tape,
            "encrypted_master_tape": gi.currencies.encrypted_master_tape,
            "boopon": gi.currencies.boopon,
        }
        status["pity"] = [{"type": str(b.type), "s_rank_in": b.pity} for b in gi.banners]
    except Exception:
        status["gacha_error"] = traceback.format_exc(limit=1)

    # 데일리 체크인 (하루 1회, 실패 시만 알림)
    zst = state.setdefault("zzz", {})
    if zst.get("checkin") != _today():
        try:
            reward = await client.claim_daily_reward(game=genshin.Game.ZZZ)
            status["checkin"] = f"{reward.name} x{reward.amount}"
            zst["checkin"] = _today()
        except genshin.AlreadyClaimed:
            status["checkin"] = "already"
            zst["checkin"] = _today()
        except Exception as e:
            status["checkin"] = f"failed: {e}"
            if zst.get("checkin_warned") != _today():
                send_telegram(f"⚠️ [젠존제] 데일리 체크인 실패: {e}")
                zst["checkin_warned"] = _today()
    return status


def alerts(status: dict, state: dict) -> None:
    zst = state.setdefault("zzz", {})
    bat = status.get("battery", {})
    if bat.get("current", 0) >= BATTERY_WARN and zst.get("battery_warned") != _today():
        send_telegram(f"🔋 [젠존제] 배터리 {bat['current']}/{bat['max']} — 곧 넘친다, 소모하자")
        zst["battery_warned"] = _today()
    eng = status.get("engagement", {})
    if (now_kst().hour >= 21 and eng and eng["current"] < eng["max"]
            and zst.get("engagement_warned") != _today()):
        send_telegram(f"📝 [젠존제] 일일 활약도 {eng['current']}/{eng['max']} — 오늘 아직 안 끝남")
        zst["engagement_warned"] = _today()


async def main() -> None:
    env = load_env()
    ltuid = env.get("HOYOLAB_LTUID_V2") or env.get("HOYOLAB_LTUID")
    ltoken = env.get("HOYOLAB_LTOKEN_V2") or env.get("HOYOLAB_LTOKEN")
    if not ltuid or not ltoken:
        print("[zzz] HoYoLAB 쿠키 미설정 — 건너뜀 (.env에 HOYOLAB_LTUID_V2/HOYOLAB_LTOKEN_V2)")
        return

    import genshin
    client = genshin.Client({"ltuid_v2": ltuid, "ltoken_v2": ltoken}, game=genshin.Game.ZZZ)
    state = load_state()
    zst = state.setdefault("zzz", {})
    try:
        status = await collect(client, state)
        alerts(status, state)
        zst["cookie_warned"] = None
    except genshin.InvalidCookies:
        if zst.get("cookie_warned") != _today():
            send_telegram(
                "🍪 [젠존제] HoYoLAB 쿠키 만료 — 갱신 필요\n"
                "1) 브라우저로 hoyolab.com 로그인\n"
                "2) F12 → Application → Cookies에서 ltuid_v2, ltoken_v2 복사\n"
                "3) VPS ~/gacha-tracker/.env 값 교체")
            zst["cookie_warned"] = _today()
        save_state(state)
        return
    DOCS_DATA.mkdir(parents=True, exist_ok=True)
    (DOCS_DATA / "zzz_status.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=1), encoding="utf-8")
    save_state(state)
    print(f"OK — battery {status.get('battery')}, checkin {status.get('checkin', '-')}")


if __name__ == "__main__":
    asyncio.run(main())
