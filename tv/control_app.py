#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
# 📺 TV DIABLO — Control App (Mac + Windows · v927)
#
#   HD grimoire UI · ON / OFF / STOP / RESTART / SIM · agent HIDDEN.
#   Window: pywebview (real OS app window — NOT Chrome). Browser is fallback only.
#   ONE WINDOW: board = same-origin /board?app=1 · dual-launch refused.
#   Mac:     python3 tv/control_app.py --open  ·  TV DIABLO.app
#   Windows: pythonw tv/control_app.py --open · Desktop shortcut
#            ON = capture_win.ps1 (hidden, auto-pin D2R + eye.jpg) + tv_diablo.py --watch
#   ver stamp MUST match tv_diablo.VERSION (parity lock in test_control).
# ═══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

import bisect
import collections
import inspect
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import base64
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CONTROL_PORT = int(os.environ.get("TV_CONTROL_PORT", "17772"))
AGENT_PORT = int(os.environ.get("TV_PORT", "17771"))
LOG_PATH = os.path.join(HERE, "control_agent.log")
PID_PATH = os.path.join(HERE, "control_agent.pid")
CAP_PID_PATH = os.path.join(HERE, "control_capture.pid")
UI_PATH = os.path.join(HERE, "control_ui.html")
BIBLE = os.path.join(REPO, "bible.html")
ART_DIR = os.path.realpath(os.path.join(REPO, "art"))
CAPTURE_PS1 = os.path.join(HERE, "capture_win.ps1")
HIST_DIR = os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")   # v765 · v885 — TV_HIST = harness isolation
BOARD_PID_PATH = os.path.join(HERE, "board_window.pid")   # v773.1 — the ONE board window
WINDOW_PID_PATH = os.path.join(HERE, ".tvd_window.pid")   # v1248 — pid of a live native window (takeover guard)


def _hist_frame_paths(fid):
    """v940.4 — candidate on-disk paths for a journaled frameId.
    Verify beats use frameId 'N_ts#v' but the JPEG is always 'N_ts.jpg' (no #v file).
    Reel footage uses 'reel_<sid>/f_<ts>' relative form."""
    if not fid:
        return []
    fid = str(fid).strip()
    base = fid.split("#", 1)[0]  # strip verify suffix
    out = []
    for stem in (fid, base):
        if not stem:
            continue
        if stem.endswith(".jpg"):
            out.append(os.path.join(HIST_DIR, stem))
        else:
            out.append(os.path.join(HIST_DIR, stem + ".jpg"))
            out.append(os.path.join(HIST_DIR, stem))
    # de-dupe preserve order
    seen, uniq = set(), []
    for p in out:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def _hist_has_frame(fid):
    """True if the archived photo for this frameId exists (base or #v or reel path)."""
    return any(os.path.isfile(p) for p in _hist_frame_paths(fid))


def _hist_frame_rel(fid):
    """Relative path under /hist/ for the UI (prefer the file that actually exists)."""
    if not fid:
        return ""
    for p in _hist_frame_paths(fid):
        if os.path.isfile(p):
            rel = os.path.relpath(p, HIST_DIR).replace("\\", "/")
            return rel
    return ""

# ── v941 THE DOSSIER — join all three eyes onto one beat ─────────────────────
# The theatre reads each frame three ways: 📸 the LOCKED intake pipeline (tally
# receipts), 🔵 the second-look verify lane, and 🧠 KAI (per-frame class + judge).
# These live as separate journal lanes keyed by different frameId shapes:
#   • verify rows carry frameId 'N_ts#v'      → base == the deep read's 'N_ts'
#   • kai rows carry frameId 'reel_<sid>/f_<ms>' → == the footage beat's frameId
#   • intake receipts carry no read frameId    → matched by tab + ts nearest
# _build_dossier_maps walks the session's rows ONCE (no O(n^2)) into lookup maps;
# _beat_dossier hangs {tally,verify,kai} on a read/footage beat from those maps.
def _build_dossier_maps(sess_rows):
    """v941/v947.2 — single-pass join index for one session's journal rows.
    Returns maps for O(1)/O(log n) hits + time-ordered AI events for stamp ledgers."""
    verify_by_base = {}   # deep frameId (verify '#v' stripped) -> compact verify dict
    kai_by_frame = {}     # reel frameId -> {"cls":.., "judge":.., "texts":..}
    tab_ts = {}           # tab(lower) -> sorted [ts] for bisect-nearest
    tab_receipts = {}     # tab(lower) -> {ts: compact receipt}
    # v947.2 — every AI journal event at its captureTs (live + aftermath) for surgical debug
    events = []           # [{ts, lane, kind, summary, names, frameId, ...}]
    for r in sess_rows:
        ln = r.get("lane")
        ts = int(r.get("captureTs") or r.get("ts") or 0)
        fid = str(r.get("frameId") or "")
        if ln == "verify":
            v = r.get("verify")
            if isinstance(v, dict):
                base = fid.split("#", 1)[0]
                if base:
                    verify_by_base[base] = {
                        "conf": v.get("conf"),
                        "confirm": len(v.get("confirm") or []),
                        "corrected": len(v.get("not_present") or []),
                        "missed": len(v.get("missed") or []),
                        "confirmNames": list(v.get("confirm") or [])[:8],
                        "missedNames": list(v.get("missed") or [])[:6],
                        "correctedNames": list(v.get("not_present") or [])[:6],
                        "ts": ts,
                    }
                    events.append({
                        "ts": ts, "lane": "verify", "eye": "second",
                        "kind": "verify",
                        "summary": "second eye re-check",
                        "names": list(v.get("confirm") or [])[:6],
                        "frameId": base, "conf": v.get("conf"),
                    })
        elif ln == "kai":
            k = r.get("kai") if isinstance(r.get("kai"), dict) else {}
            if fid:
                slot = kai_by_frame.setdefault(fid, {"cls": None, "judge": None, "texts": None})
                if k.get("cls") is not None:
                    slot["cls"] = k.get("cls")
                if k.get("texts"):
                    slot["texts"] = list(k.get("texts") or [])[:8]
                j = k.get("judge")
                if isinstance(j, dict):
                    # v948.3 — keep live/applied so Theatre stamp ledger shows the full route
                    slot["judge"] = {"name": j.get("name") or "",
                                     "tier": j.get("tier") or "",
                                     "score": j.get("score"),
                                     "live": bool(j.get("live")),
                                     "applied": j.get("applied") or None,
                                     "actions": list(j.get("actions") or [])[:6]}
            mode = str(r.get("mode") or "kai")
            j = k.get("judge") if isinstance(k.get("judge"), dict) else None
            # Judge receipts carry the item name on judge{}, not texts[]
            _ev_names = []
            if j and j.get("name"):
                _ev_names = [j.get("name")]
            elif k.get("texts"):
                _ev_names = list(k.get("texts") or [])[:6]
            events.append({
                "ts": ts, "lane": "kai", "eye": "kai",
                "kind": mode,
                "summary": (r.get("note") or "KAI closer")[:100],
                "names": _ev_names,
                "frameId": fid,
                "cls": k.get("cls") if k else None,
                "judge": j,
            })
        elif ln == "deep":
            names = list(r.get("names") or r.get("confirmed_names") or [])[:8]
            events.append({
                "ts": ts, "lane": "deep", "eye": "live",
                "kind": "deep",
                "summary": ("deep · " + (r.get("scene") or "") + (
                    (" · " + str(r.get("stashTab"))) if r.get("stashTab") else "")),
                "names": names,
                "frameId": fid,
                "conf": r.get("conf"),
                "model": r.get("model") or "",
                "stashTab": r.get("stashTab") or "",
                "completedTs": int(r.get("completedTs") or ts),
                "n": r.get("n"),
            })
        elif ln == "ocr":
            names = list(r.get("names") or r.get("ocr_names") or [])[:8]
            events.append({
                "ts": ts, "lane": "ocr", "eye": "text",
                "kind": "ocr",
                "summary": "text-eye flash",
                "names": names,
                "frameId": fid,
                "ocr_ms": r.get("ocr_ms") or r.get("ms"),
            })
        elif ln == "intake" or r.get("intakeBeat") or isinstance(r.get("intake"), dict):
            ik = r.get("intake") if isinstance(r.get("intake"), dict) else {}
            events.append({
                "ts": ts, "lane": "intake", "eye": "intake",
                "kind": str(ik.get("kind") or "intake"),
                "summary": (r.get("note") or ("intake · " + str(ik.get("tab") or "")))[:100],
                "names": [],
                "frameId": fid,
                "tab": ik.get("tab") or "",
                "total": int(ik.get("total") or 0),
                "ok": bool(ik.get("ok", True)),
            })
        ik = r.get("intake")
        if isinstance(ik, dict):
            tab = str(ik.get("tab") or ik.get("kind") or "").lower()
            if tab and ts:
                cnts = ik.get("counts") if isinstance(ik.get("counts"), dict) else {}
                top = sorted(cnts.items(),
                             key=lambda kv: (-int(kv[1] or 0), str(kv[0])))[:8]
                tab_receipts.setdefault(tab, {})[ts] = {
                    "tab": ik.get("tab") or tab,
                    "kind": ik.get("kind") or "",
                    "ok": bool(ik.get("ok", True)),
                    "total": int(ik.get("total") or 0),
                    "counts": [[str(k2), int(v2 or 0)] for k2, v2 in top],
                    "ts": ts,
                }
                tab_ts.setdefault(tab, []).append(ts)
    for tab in tab_ts:
        tab_ts[tab].sort()
    # v944.5 — BEST receipt per tab this session (never-zero truth)
    tab_best = {}
    for tab, byts in tab_receipts.items():
        best = None
        for rc in byts.values():
            if not rc.get("ok", True):
                continue
            if best is None or int(rc.get("total") or 0) > int(best.get("total") or 0):
                best = rc
        if best is not None and int(best.get("total") or 0) > 0:
            tab_best[tab] = best
    events.sort(key=lambda e: (int(e.get("ts") or 0), str(e.get("lane") or "")))
    return {"verify": verify_by_base, "kai": kai_by_frame,
            "tab_ts": tab_ts, "tab_receipts": tab_receipts, "tab_best": tab_best,
            "events": events}


def _intake_is_real(ik):
    """v944.6 — a real tally receipt: ok and total>0. Zero/error is a FAILURE SIGNAL,
    never a value (Konyo: 'I don't want ANYTHING read 0'). Vault empty can legitimately
    total 0 — callers must gate vault separately."""
    if not isinstance(ik, dict):
        return False
    if not ik.get("ok", True):
        return False
    return int(ik.get("total") or 0) > 0


def _tab_best_total(rows, tab):
    """v948.17 — Grok P0-1 (2026-07-21 fast-run soak): the max REAL receipt total already
    landed for `tab` this session. Mirrors the `tab_best` never-zero display law (see
    `_beat_dossier`'s tab_best map) so the SAME 'biggest real total wins' truth also governs
    the funnel WRITE path, not just what the theatre displays."""
    tab = str(tab or "").lower().strip()
    best = 0
    for r in rows or []:
        ik = r.get("intake")
        if isinstance(ik, dict) and str(ik.get("tab") or "").lower() == tab and _intake_is_real(ik):
            t = int(ik.get("total") or 0)
            if t > best:
                best = t
    return best


def _funnel_never_zero_guard(existing_total, new_total):
    """v948.17 — Grok P0-1 pin target: pure never-zero WRITE decision. A funnel's fresh read
    (often thin/partial — a single reel still, not a careful hover) must NEVER overwrite an
    existing REAL tally when the existing total is materially bigger — Konyo's law: '404 then
    a funnel says 4' must keep 404. Only apply the funnel's SET-style write when the existing
    tally is missing/0/error, or the new read is at least as large (a genuine bigger recount,
    not a partial miss). Returns True when it's safe to apply the new read."""
    try:
        existing_total = int(existing_total or 0)
    except Exception:
        existing_total = 0
    try:
        new_total = int(new_total or 0)
    except Exception:
        new_total = 0
    if existing_total <= 0:
        return True
    return new_total >= existing_total


def _drv_freshest_tab_fid(tab, reads=None, journal_rows=None, fallback=""):
    """v944.6 — newest deep stash frameId for `tab` from bridge reads and/or journal.
    Re-fire against the UPDATED picture, not the stale shot that errored to 0."""
    tab = (tab or "").lower()
    best_fid, best_ts = fallback or "", 0
    for src in (reads or [], journal_rows or []):
        for rd in src:
            if rd.get("provisional"):
                continue
            lane = rd.get("lane")
            if lane is not None and lane != "deep":
                continue
            scene = str(rd.get("scene") or "")
            if scene and scene != "stash":
                continue
            if str(rd.get("stashTab") or "").lower() != tab:
                continue
            ts = max(int(rd.get("completedTs") or 0), int(rd.get("ts") or 0),
                     int(rd.get("captureTs") or 0))
            fid = str(rd.get("frameId") or "")
            if fid and ts >= best_ts:
                best_ts, best_fid = ts, fid
    return best_fid or fallback or ""


def _vault_names_worth_auto(names):
    """v946.7 — vaultIntake needs TOOLTIP text, not an icon grid.
    Return True only when the deep read carries real item-identity names (manual-photo shape).
    Garble ('Ii', 'IA Lla') and empty names = raw grid → do NOT auto-fire."""
    if not names:
        return False
    good = 0
    for n in names:
        s = str(n or "").strip()
        if len(s) < 4:
            continue
        letters = sum(1 for c in s if c.isalpha())
        if letters < max(3, len(s) // 2):
            continue
        low = s.lower().strip("'\"")
        if low in ("ii", "ia lla", "stash", "inventory", "personal", "shared",
                   "runes", "gems", "materials", "required", "defense"):
            continue
        # at least one vowel-ish → real word, not OCR noise
        if not any(v in low for v in "aeiou"):
            continue
        good += 1
    return good >= 1


def _drv_empty_refire_plan(inflight, intake, freshest_fid, max_tries=3):
    """v944.6/v946.8 pure decision for never-zero re-fire.
    Returns ('done', None) | ('refire', job_dict) | ('giveup', None).
    Tally + vault-count: re-fire on !ok or total==0.
    Vault identity: only re-fire when job.has_names (tooltip path)."""
    if not isinstance(inflight, dict):
        return ("giveup", None)
    key = str(inflight.get("key") or "")
    is_vaultcount = key.startswith("vaultcount_")
    is_vault = key.startswith("vault_") and not is_vaultcount
    if is_vaultcount:
        # COUNT path — 0 is a failed count; re-fire like tally
        if _intake_is_real(intake):
            return ("done", None)
    elif is_vault:
        if bool((intake or {}).get("ok", True)):
            return ("done", None)
        # identity vault without tooltip names → don't thrash
        if not inflight.get("has_names"):
            return ("giveup", None)
        # tooltip-path vault error → re-fire ladder
    elif _intake_is_real(intake):
        return ("done", None)
    tries = int(inflight.get("tries") or 0) + 1
    job = dict(inflight)
    job["tries"] = tries
    if tries < max_tries:
        fid = freshest_fid or job.get("fid") or ""
        if fid:
            job["fid"] = fid
        return ("refire", job)
    return ("giveup", None)


def _drv_live_judged_reserve(live_judged, fid, cap=2000):
    """v1205 — bounded reserve for `_engine_driver`'s `live_judged` dedup set. Mutates
    `live_judged` in place (mirrors the driver's own bare-set style); no return value.

    `live_judged` exists purely to stop a frameId being re-queued for a live judge call
    after it's already fired — `judge_q`'s own membership check independently covers "still
    pending", so this set's ONLY remaining job is remembering frames that already fired.
    `_engine_driver` is ONE daemon thread started once at process boot and runs `while True`
    for the process's ENTIRE lifetime — spanning many game sessions across hours/days on
    Konyo's always-on, launchd-supervised console — yet before this fix the set was never
    trimmed: it grew by one entry per unique judge-candidate frameId FOREVER (the FUNNEL
    analog of engine-read's worker-orphan leak). frameIds are globally unique per reel
    (reel_<sid>/<n>_<capturems>), so nothing from a closed session's reel can ever reappear —
    remembering it past the point it can fall out of the bridge's own rolling `reads` window
    buys nothing. `cap` is far larger than any single session could plausibly produce;
    crossing it clears the whole set, then immediately re-seeds it with `fid` so the frame
    just reserved this pass doesn't lose its own protection."""
    if len(live_judged) > cap:
        live_judged.clear()
    live_judged.add(fid)


def _capture_ts_from_frame_id(frame_id):
    """Mirrors tv_diablo.py's helper (kept separate — control_app.py is a different process
    and does not import tv_diablo). frameId = '{n}_{captureMs}' — the exact settle freeze
    time of the archived photo. A0 fix (2026-07-21, arch panel Q5 blocker): this is the ONLY
    honest source for an intake receipt's captureTs — the receipt's `ts` is when the client's
    fetch landed (Date.now()), which floats SECONDS right of the frame it describes because
    auto-intake (screenshot+tally) takes seconds to run."""
    try:
        if frame_id and "_" in str(frame_id):
            return int(str(frame_id).rsplit("_", 1)[-1])
    except Exception:
        pass
    return None


# ── v945.6 INTAKE LEASE — exactly one owner fires a given tab at a time ──
# Engine iframe + open board can both see the same stash tab. SET semantics keep
# counts convergent, but dual-fire wastes AI calls and double-journals. Control
# holds a soft TTL lease per tab; owners claim before fire, release in finally.
_INTAKE_LEASES = {}   # tab -> {owner, until, since}
_INTAKE_LEASE_TTL_MS = 120_000
_INTAKE_LEASE_LOCK = threading.Lock()


def _intake_lease_claim(tab, owner, ttl_ms=None, now_ms=None, now_mono_ms=None):
    """Pure-ish lease claim. Returns {ok, tab, owner, until} or {ok:False, why, holder?}.

    v1202 — CLOCK-SKEW class (same sweep as v1199-v1201): the expiry DECISION (drop-expired,
    "is it still held") used to compare `until` against `time.time()*1000` — a backward
    NTP/sleep-wake jump between claim and a later check makes `now` smaller than it should be,
    so an already-expired lease reads as still-held for an extra `jump_size` ms — a tab stuck
    "busy" longer than its 120s TTL. But `until` ITSELF must stay wall-clock: it's returned
    straight to the caller (verified per-spot — the /intake_claim HTTP handler ships it
    unmodified to the board's browser JS, and _intake_lease_status's snapshot rides the same
    'until'/'since' shape into /api/status's `leases` field for the theatre UI, both comparing
    it against THEIR OWN wall clock / Date.now()). A monotonic value would be meaningless
    across that process boundary. Same split as the closer loop's _t0f/_t0f_mono: `until`
    (wall-clock) stays the DISPLAYED/RETURNED field; a new internal-only `untilMono` (never
    returned) drives the actual expiry comparison. now_ms/now_mono_ms are optional overrides
    (both independently, for deterministic tests of skew scenarios) — real callers omit both."""
    tab = str(tab or "").lower().strip()
    owner = str(owner or "anon")[:48]
    if not tab:
        return {"ok": False, "why": "no-tab"}
    if not owner:
        return {"ok": False, "why": "no-owner"}
    ttl = int(ttl_ms if ttl_ms is not None else _INTAKE_LEASE_TTL_MS)
    now = int(now_ms if now_ms is not None else time.time() * 1000)
    now_mono = float(now_mono_ms if now_mono_ms is not None else time.monotonic() * 1000)
    with _INTAKE_LEASE_LOCK:
        # drop expired — monotonic decision, immune to a backward wall-clock jump
        for k in list(_INTAKE_LEASES.keys()):
            if float((_INTAKE_LEASES[k] or {}).get("untilMono") or 0) <= now_mono:
                _INTAKE_LEASES.pop(k, None)
        cur = _INTAKE_LEASES.get(tab)
        if cur and float(cur.get("untilMono") or 0) > now_mono and cur.get("owner") != owner:
            return {"ok": False, "why": "held", "holder": cur.get("owner"),
                    "until": int(cur.get("until") or 0)}
        until = now + max(5_000, ttl)
        until_mono = now_mono + max(5_000, ttl)
        _INTAKE_LEASES[tab] = {"owner": owner, "until": until, "untilMono": until_mono,
                               "since": int((cur or {}).get("since") or now)}
        return {"ok": True, "tab": tab, "owner": owner, "until": until}


def _intake_lease_release(tab, owner):
    """Release if caller still holds. Returns {ok, released:bool}.
    No clock logic here — ownership + pop only, nothing time-based to skew."""
    tab = str(tab or "").lower().strip()
    owner = str(owner or "")[:48]
    with _INTAKE_LEASE_LOCK:
        cur = _INTAKE_LEASES.get(tab)
        if not cur:
            return {"ok": True, "released": False}
        if cur.get("owner") != owner:
            return {"ok": False, "why": "not-holder", "holder": cur.get("owner"),
                    "released": False}
        _INTAKE_LEASES.pop(tab, None)
        return {"ok": True, "released": True}


def _intake_lease_status(tab=None, now_mono_ms=None):
    """Snapshot of active (non-expired) leases for doctor/debug.
    v1202 — same monotonic-expiry / wall-clock-display split as _intake_lease_claim. The
    returned snapshot deliberately omits `untilMono` (internal-only, meaningless outside this
    process) — callers (the /api/status `leases` field) only ever see the wall-clock
    `owner`/`until`/`since` shape they always have."""
    now_mono = float(now_mono_ms if now_mono_ms is not None else time.monotonic() * 1000)
    with _INTAKE_LEASE_LOCK:
        out = {}
        for k, v in list(_INTAKE_LEASES.items()):
            if float((v or {}).get("untilMono") or 0) <= now_mono:
                _INTAKE_LEASES.pop(k, None)
                continue
            if tab is None or k == str(tab).lower():
                out[k] = {"owner": v.get("owner"), "until": v.get("until"), "since": v.get("since")}
        return out


def _nearest_receipt(maps, tab, ts, window_ms=None):
    """Compact intake receipt for `tab` nearest to `ts` (bisect); None if none
    (or outside window_ms when given)."""
    tab = (tab or "").lower()
    tslist = maps["tab_ts"].get(tab)
    if not tslist or not ts:
        return None
    i = bisect.bisect_left(tslist, ts)
    best = None
    for j in (i - 1, i):
        if 0 <= j < len(tslist):
            cand = tslist[j]
            if best is None or abs(cand - ts) < abs(best - ts):
                best = cand
    if best is None or (window_ms is not None and abs(best - ts) > window_ms):
        return None
    return maps["tab_receipts"][tab].get(best)


def _stamps_near(maps, ts, window_ms=2500, limit=12):
    """v947.2 — AI events whose captureTs is within ±window of this photo (live + aftermath)."""
    evs = maps.get("events") or []
    if not evs or not ts:
        return []
    out = []
    for e in evs:
        ets = int(e.get("ts") or 0)
        if abs(ets - ts) <= window_ms:
            out.append(e)
    return out[:limit]


def _beat_dossier(maps, beat):
    """v941/v947.2 — full multi-eye dossier + time-synced stamp ledger for Theatre debug.

    Reads (lane deep) hit verify by base + tally by stashTab.
    Footage hits KAI/router exact + tally by stash class + nearby live/aftermath events.
    """
    fid = str(beat.get("frameId") or "")
    ts = int(beat.get("captureTs") or beat.get("ts") or 0)
    is_footage = bool(beat.get("footage"))
    verify = maps["verify"].get(fid.split("#", 1)[0]) if fid else None
    kai = maps["kai"].get(fid)
    # film stills: KAI missed-text from kai_report.missed rides the beat
    if beat.get("kaiMissTexts"):
        kai = dict(kai or {})
        kai["texts"] = list(beat.get("kaiMissTexts") or [])[:8]
        if beat.get("label") and not kai.get("cls"):
            kai["cls"] = beat.get("label")
    if kai and kai.get("cls") is None and kai.get("judge") is None and not kai.get("texts"):
        kai = None
    tally = None
    _rlabel = str(beat.get("label") or (kai or {}).get("cls") or "")
    if is_footage:
        cls = _rlabel
        if isinstance(cls, str) and cls.startswith("stash-"):
            tally = _nearest_receipt(maps, cls[6:], ts, window_ms=120000)
        elif beat.get("stashTab"):
            tally = _nearest_receipt(maps, str(beat.get("stashTab")), ts, window_ms=120000)
    else:
        tab = str(beat.get("stashTab") or "")
        if tab:
            tally = _nearest_receipt(maps, tab, ts, window_ms=None)
    read_status = None
    if _rlabel.startswith("stash-") or _rlabel in ("stash", "inventory"):
        _tab = _rlabel[6:] if _rlabel.startswith("stash-") else _rlabel
        _best = (maps.get("tab_best") or {}).get(_tab.lower())
        _near_tot = int((tally or {}).get("total") or 0) if tally else 0
        if _best and int(_best.get("total") or 0) > 0:
            if _near_tot <= 0:
                tally = _best
            read_status = {"kind": "read", "tab": _tab,
                           "counted": int(_best.get("total") or 0), "superseded": _near_tot <= 0}
        else:
            read_status = {"kind": "miss", "tab": _tab, "counted": _near_tot}
    elif (beat.get("names") or []):
        read_status = {"kind": "named", "counted": len(beat.get("names") or [])}

    # Full router row (from kai_report join on the beat)
    router = None
    if beat.get("label") or beat.get("route") or beat.get("routeVerdict"):
        router = {
            "label": beat.get("label"),
            "verdict": beat.get("routeVerdict"),
            "route": beat.get("route"),
            "routed": beat.get("routed"),
            "sources": list(beat.get("routeSources") or []),
            "confidence": beat.get("routeConf"),
            "skipReason": beat.get("routeVerdict") if not beat.get("routed") else None,
            "eyeSources": list(beat.get("eyeSources") or []),
            "stashTab": beat.get("stashTab") or "",
        }

    # ── STAMP LEDGER (capture-time ordered authorization trail) ──
    stamps = []
    # 1 photo itself
    stamps.append({
        "phase": "photo", "eye": "film" if is_footage else (beat.get("lane") or "read"),
        "ts": ts, "auth": "capture",
        "summary": ("film still" if is_footage else ("AI " + str(beat.get("lane") or "read"))),
        "names": list(beat.get("names") or [])[:6],
    })
    # 2 text-eye / OCR on this beat
    if beat.get("ocr_names") or beat.get("ocr_raw") or beat.get("lane") == "ocr":
        stamps.append({
            "phase": "text-eye", "eye": "text", "ts": ts,
            "auth": "ocr",
            "summary": "OCR flash · " + str(beat.get("ocr_ms") or beat.get("ms") or "?") + "ms",
            "names": list(beat.get("ocr_names") or beat.get("names") or [])[:6],
        })
    # 3 deep live read
    if beat.get("lane") == "deep" or (not is_footage and (beat.get("names") or beat.get("model"))):
        stamps.append({
            "phase": "live-deep", "eye": "live",
            "ts": int(beat.get("completedTs") or ts),
            "auth": "deep",
            "summary": "deep " + str(beat.get("model") or "") + (
                " · tab " + str(beat.get("stashTab")) if beat.get("stashTab") else ""),
            "names": list(beat.get("names") or [])[:8],
            "conf": beat.get("conf"),
        })
    # 4 second eye
    if verify:
        stamps.append({
            "phase": "second-eye", "eye": "second",
            "ts": int(verify.get("ts") or ts),
            "auth": "verify",
            "summary": ("verify · conf " + str(verify.get("conf") or "?")
                        + (" · +" + str(verify.get("confirm") or 0) + " ok"
                           if verify.get("confirm") else "")
                        + (" · ⚡" + str(verify.get("corrected") or 0) + " corrected"
                           if verify.get("corrected") else "")),
            "names": list(verify.get("confirmNames") or [])[:6],
        })
    # 5 KAI aftermath (class / miss / judge)
    if kai:
        stamps.append({
            "phase": "kai-close", "eye": "kai",
            "ts": ts,  # joined to this photo's capture
            "auth": "kai",
            "summary": "KAI · " + str(kai.get("cls") or "class") + (
                (" · unread: " + ", ".join(kai.get("texts") or [])[:60])
                if kai.get("texts") else ""),
            "names": list(kai.get("texts") or [])[:6],
            "judge": kai.get("judge"),
        })
        if isinstance(kai.get("judge"), dict) and kai["judge"].get("name"):
            _jj = kai["judge"]
            _jsum = (("live-judge · " if _jj.get("live") else "judge · ")
                     + str(_jj.get("tier") or "") + " " + str(_jj.get("name") or ""))
            if _jj.get("applied"):
                _jsum += " → " + str(_jj.get("applied"))
            stamps.append({
                "phase": "kai-judge", "eye": "kai",
                "ts": ts, "auth": "judge",
                "summary": _jsum[:120],
                "names": [_jj.get("name")],
                "live": bool(_jj.get("live")),
                "applied": _jj.get("applied"),
            })
    # 6 router authorization
    if router and (router.get("label") or router.get("route")):
        conf = router.get("confidence")
        src = router.get("sources") or []
        stamps.append({
            "phase": "router", "eye": "router",
            "ts": ts, "auth": "router",
            "summary": ("router · " + str(router.get("label") or "?")
                        + (" · conf " + str(conf) if conf is not None else "")
                        + (" · " + ",".join(src) if src else "")
                        + (" · " + str(router.get("verdict") or router.get("skipReason") or "")
                           if (router.get("verdict") or router.get("skipReason")) else "")
                        + (" · FIRED " + str(router.get("routed"))
                           if router.get("routed") else "")),
            "names": [],
            "route": router.get("route"),
            "routed": router.get("routed"),
            "confidence": conf,
            "sources": src,
        })
    # 7 intake / funnel receipt
    if tally:
        stamps.append({
            "phase": "intake", "eye": "intake",
            "ts": int(tally.get("ts") or ts),
            "auth": "intake",
            "summary": ("intake · " + str(tally.get("tab") or tally.get("kind") or "")
                        + " ×" + str(tally.get("total") or 0)
                        + (" ✓" if tally.get("ok", True) else " ✗")),
            "names": [p[0] for p in (tally.get("counts") or [])[:6]
                      if isinstance(p, (list, tuple)) and p],
            "total": tally.get("total"),
            "ok": tally.get("ok", True),
        })
    # 8 nearby live/aftermath events (other frames' AI work at this timestamp window)
    # v948.3 — ±4s so live-judge (fts = deep captureTs) lands on film stills + deep beats;
    # never drop a kai-judge when this photo's slot has no judge yet (live vs reel frameId).
    _has_judge = bool(isinstance((kai or {}).get("judge"), dict) and (kai or {}).get("judge", {}).get("name"))
    for e in _stamps_near(maps, ts, window_ms=4000, limit=14):
        # skip exact dups already covered
        if e.get("lane") == "deep" and not is_footage and str(e.get("frameId") or "") == fid:
            continue
        if e.get("lane") == "ocr" and beat.get("lane") == "ocr":
            continue
        if e.get("lane") == "kai" and kai:
            if e.get("kind") == "kai-judge" and not _has_judge:
                pass  # keep — attach live/post-seal verdict to this photo by time
            else:
                continue
        if e.get("lane") == "verify" and verify:
            continue
        stamps.append({
            "phase": "near-" + str(e.get("lane") or "ai"),
            "eye": e.get("eye") or e.get("lane"),
            "ts": int(e.get("ts") or ts),
            "auth": e.get("kind") or e.get("lane"),
            "summary": (e.get("summary") or "")[:120],
            "names": list(e.get("names") or [])[:6],
            "near": True,
            "dtMs": int(e.get("ts") or ts) - ts,
        })
    stamps.sort(key=lambda s: (int(s.get("ts") or 0), str(s.get("phase") or "")))

    return {"tally": tally, "verify": verify or None, "kai": kai,
            "router": router,
            "readStatus": read_status,
            "stamps": stamps}


IS_WIN = sys.platform.startswith("win")
# Windows: CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
_WIN_CREATE = 0x00000200 | 0x08000000 if IS_WIN else 0

_ART_MIME = {
    ".png": "image/png",
    ".gif": "image/gif",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}

_lock = threading.Lock()
_agent_proc = None  # type: ignore
_stop_inflight = False   # v768 (Grok R2) — a threaded stop/farewell is running; ON/RESTART must wait
_capture_proc = None  # type: ignore
_agent_mode = "off"  # off | live | sim
_log_fp = None
_EXIT_STOP_DONE = False
_EXIT_STOP_LOCK = threading.Lock()
_WINDOW_ONLY = False   # v935.8 — secondary --window-only attach must NOT kill ON AIR


def _env_clean(sim=False):
    env = os.environ.copy()
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("ANTHROPIC_AUTH_TOKEN", None)
    extras = []
    if IS_WIN:
        extras = [
            os.path.expandvars(r"%LocalAppData%\Programs\Python\Python312"),
            os.path.expandvars(r"%LocalAppData%\Programs\Python\Python312\Scripts"),
            os.path.expandvars(r"%LocalAppData%\Programs\Python\Python313"),
            os.path.expandvars(r"%LocalAppData%\Programs\Python\Python313\Scripts"),
            os.path.expandvars(r"%LocalAppData%\Microsoft\WinGet\Links"),
            os.path.expandvars(r"%ProgramFiles%\Git\cmd"),
            os.path.expanduser(r"~\.local\bin"),
        ]
    else:
        extras = [
            "/opt/homebrew/bin",
            "/usr/local/bin",
            os.path.expanduser("~/.local/bin"),
        ]
    head = os.pathsep.join([p for p in extras if p and os.path.isdir(p)])
    if head:
        env["PATH"] = head + os.pathsep + env.get("PATH", "")
    if sim:
        env["TV_STUB"] = "1"
    else:
        env.pop("TV_STUB", None)
    env["TV_PORT"] = str(AGENT_PORT)
    # v784 — Windows capture default AUTO (pin D2R.exe); Mac agent reads TV_CAPTURE itself
    if IS_WIN and not (env.get("TV_CAPTURE") or "").strip():
        env["TV_CAPTURE"] = "auto"
    return env


_BR_CACHE = {"ping": False, "st": None, "ts": 0.0}
_PID_CACHE = {"pid": None, "ts": 0.0}


def _pid_cached():
    """v872 — the status poll must NEVER pay an lsof subprocess. Prefer the tracked child;
    fall back to a port scan at most every 10s."""
    with _lock:
        if _agent_proc is not None and _agent_proc.poll() is None:
            return int(_agent_proc.pid)
    now = time.time()
    if now - _PID_CACHE["ts"] > 10.0:
        _PID_CACHE["pid"] = _port_listener_pid()
        _PID_CACHE["ts"] = now
    return _PID_CACHE["pid"]


def _console_beacon(event="hb"):
    """v875 (Konyo: 'a tracker so I know whose console is online — like the site visits') —
    phone the presence beacon home. Silent on any failure; never blocks a caller."""
    try:
        import base64 as _b64, socket as _sock
        st = status_payload()
        body = json.dumps({
            "machine": _sock.gethostname().split(".")[0],
            "platform": st.get("platform"), "ver": st.get("ver"),
            "mode": st.get("mode"), "event": event,
            "user": os.environ.get("TVD_USER", ""),
            "reads": st.get("readCount") or 0,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://bull-4-u.com/api/console", data=body,
            headers={"Content-Type": "application/json", "User-Agent": "TVD-Console/1.0",
                     "Authorization": "Basic " + _b64.b64encode(b"app:DeanDiablo").decode()},
            method="POST")
        with urllib.request.urlopen(req, timeout=8) as r:
            r.read()
    except Exception:
        pass


def _console_beacon_async(event):
    threading.Thread(target=_console_beacon, args=(event,), daemon=True).start()


def _console_beacon_loop():
    _console_beacon("boot")
    _last_mode = [None]
    while True:
        time.sleep(240)
        try:
            m = status_payload().get("mode")
            _console_beacon("mode:" + str(m) if m != _last_mode[0] and _last_mode[0] is not None else "hb")
            _last_mode[0] = m
        except Exception:
            pass


def _bridge_prober():
    """v872 (Konyo: 'STANDBY keeps jumping at me mid session') — ONE background thread probes
    the agent bridge every 1.2s; every /api/status poll reads the cache. Under full game load
    the console poll went 300ms × (ping 0.6s + state 0.8s + lsof) and choked itself."""
    while True:
        try:
            ping = _bridge_ping() is not None
            st = _bridge_state() if ping else None
            _BR_CACHE["ping"], _BR_CACHE["st"], _BR_CACHE["ts"] = ping, st, time.time()
            if ping:
                globals()["_BRIDGE_LAST_OK"] = time.time()
        except Exception:
            pass
        time.sleep(1.2)


def _bridge_ping():
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{AGENT_PORT}/ping", timeout=0.6
        ) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None


def _bridge_state():
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{AGENT_PORT}/state", timeout=0.8
        ) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None


_TZ_CACHE = {"ts": 0.0, "code": 0, "body": None}
_TZ_LOCK = threading.Lock()
_TZ_UPSTREAM = os.environ.get("TVD_TZ_UPSTREAM", "https://bull-4-u.com/api/tz")
_TZ_AUTH = base64.b64encode(b"app:DeanDiablo").decode("ascii")


def _tz_proxy():
    # Terror Zone tracker relay: the board's /api/tz only exists as a Pages
    # function on the live deploy; the shell serves the board locally, so we
    # fetch upstream (through the site's basic-auth gate) and cache 90s.
    # Upstream dead → serve the last good rotation (stale flag) so the card
    # degrades to old-but-honest instead of "tracker is down".
    with _TZ_LOCK:
        now = time.time()
        if _TZ_CACHE["body"] is not None and now - _TZ_CACHE["ts"] < 90:
            return _TZ_CACHE["code"], _TZ_CACHE["body"]
        try:
            req = urllib.request.Request(
                _TZ_UPSTREAM,
                headers={
                    "Authorization": "Basic " + _TZ_AUTH,
                    # Cloudflare 403s the default Python-urllib UA
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) TVDiablo/944",
                },
            )
            with urllib.request.urlopen(req, timeout=12) as r:
                body = json.loads(r.read().decode("utf-8", "replace"))
            _TZ_CACHE.update(ts=now, code=200, body=body)
            return 200, body
        except Exception as e:
            if _TZ_CACHE["body"] is not None:
                stale = dict(_TZ_CACHE["body"])
                stale["stale"] = True
                return 200, stale
            return 502, {"error": f"tz upstream unreachable: {e}"}


def _port_listener_pid(port=None):
    """PID listening on TCP port (cross-platform)."""
    port = int(port or AGENT_PORT)
    if IS_WIN:
        try:
            # netstat -ano: find LISTENING on :port
            out = subprocess.check_output(
                ["netstat", "-ano", "-p", "tcp"],
                stderr=subprocess.DEVNULL,
                text=True,
                creationflags=_WIN_CREATE,
            )
            needle = f":{port}"
            for line in out.splitlines():
                if "LISTENING" not in line.upper():
                    continue
                if needle not in line:
                    continue
                # only care about local bind
                parts = line.split()
                if len(parts) < 5:
                    continue
                local = parts[1] if parts[0].upper() == "TCP" else parts[0]
                if not local.endswith(needle) and f"]{needle}" not in local:
                    # also accept 0.0.0.0:port / [::]:port
                    if needle not in local:
                        continue
                try:
                    return int(parts[-1])
                except ValueError:
                    continue
        except Exception:
            return None
        return None
    try:
        out = subprocess.check_output(
            ["lsof", f"-tiTCP:{port}", "-sTCP:LISTEN"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        if not out:
            return None
        return int(out.splitlines()[0])
    except Exception:
        return None


def _agent_alive():
    global _agent_proc
    with _lock:
        if _agent_proc is not None and _agent_proc.poll() is None:
            return True
    return _pid_cached() is not None   # v877 (army B#1) — the fallback ran a fresh lsof PER POLL


def _write_pid(path, pid):
    try:
        with open(path, "w") as f:
            f.write(str(pid))
    except Exception:
        pass


def _read_pid(path):
    try:
        with open(path) as f:
            return int(f.read().strip())
    except Exception:
        return None


def _kill_pid(pid, force=False):
    if pid is None:
        return
    if IS_WIN:
        args = ["taskkill", "/PID", str(pid), "/T"]
        if force:
            args.append("/F")
        try:
            subprocess.run(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=_WIN_CREATE,
            )
        except Exception:
            pass
        return
    # v847 — agent is NOT setsid on Mac (TCC). killpg(pid) often fails; prefer kill then group.
    sig = signal.SIGKILL if force else signal.SIGTERM
    try:
        os.kill(pid, sig)
    except ProcessLookupError:
        return
    except Exception:
        pass
    try:
        os.killpg(pid, sig)
    except Exception:
        pass


def _ask_agent_shutdown(farewell=True, reason="stop", timeout=2.0):
    """v847 — polite shutdown: agent journals session_end (+ optional farewell) then exits."""
    try:
        from urllib.parse import quote as _quote
        q = "farewell=%s&reason=%s" % ("1" if farewell else "0",
                                        _quote(str(reason)[:40]))
        urllib.request.urlopen(
            f"http://127.0.0.1:{AGENT_PORT}/shutdown?{q}", timeout=timeout
        ).read()
        return True
    except Exception:
        return False


def _collect_agent_pids():
    """Every PID that might be the live agent (owned child, port listener, pid file)."""
    pids = set()
    with _lock:
        if _agent_proc is not None and _agent_proc.poll() is None:
            pids.add(int(_agent_proc.pid))
    for p in (_port_listener_pid(), _read_pid(PID_PATH)):
        if p:
            pids.add(int(p))
    return [p for p in pids if p]


def _pid_alive(pid):
    if pid is None:
        return False
    # v778-pre (BUG A) — our OWN child becomes a ZOMBIE on death until reaped: os.kill(pid,0)
    # succeeds on zombies, so the stop thread stared at a corpse for the full 90s farewell
    # window. poll() both answers truthfully AND reaps.
    try:
        with _lock:
            if _agent_proc is not None and _agent_proc.pid == pid:
                return _agent_proc.poll() is None
    except Exception:
        pass
    if IS_WIN:
        try:
            out = subprocess.check_output(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                stderr=subprocess.DEVNULL,
                text=True,
                creationflags=_WIN_CREATE,
            )
            return str(pid) in out
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except Exception:
        return False


def _start_capture(env, log_fp):
    """Windows only: hidden capture_win.ps1 loop."""
    global _capture_proc
    if not IS_WIN:
        return None
    if not os.path.isfile(CAPTURE_PS1):
        log_fp.write("!! capture_win.ps1 missing — Windows ON will have no frames\n")
        log_fp.flush()
        return None
    # already running?
    old = _read_pid(CAP_PID_PATH)
    if old and _pid_alive(old):
        return old
    try:
        _capture_proc = subprocess.Popen(
            [
                "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-WindowStyle",
                "Hidden",
                "-File",
                CAPTURE_PS1,
            ],
            cwd=REPO,
            env=env,
            stdout=log_fp,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            creationflags=_WIN_CREATE,
        )
        _write_pid(CAP_PID_PATH, _capture_proc.pid)
        log_fp.write(f"capture_win.ps1 pid {_capture_proc.pid}\n")
        log_fp.flush()
        return _capture_proc.pid
    except Exception as e:
        log_fp.write(f"!! capture start failed: {e}\n")
        log_fp.flush()
        return None


_CAP_RESTARTED = False
def _capture_health():
    """v793 (Grok R4 #5a) — Windows capture lamp: LINKED / DEAD / n/a. A dead capture_win.ps1
    used to leave a frozen eye with the lamp still mint. Auto-restart ONCE, loudly."""
    global _CAP_RESTARTED
    if not IS_WIN:
        return ""
    if _agent_mode not in ("live", "sim"):
        _CAP_RESTARTED = False
        return ""
    pid = None
    try:
        with _lock:
            if _capture_proc is not None and _capture_proc.poll() is None:
                return "LINKED"
        pid = _read_pid(CAP_PID_PATH)
    except Exception:
        pass
    if pid and _pid_alive(pid):
        return "LINKED"
    if not _CAP_RESTARTED and _log_fp:
        _CAP_RESTARTED = True
        try:
            _log_fp.write("!! capture_win.ps1 DIED mid-session — auto-restarting once\n")
            _log_fp.flush()
            _start_capture(_env_clean(sim=(_agent_mode == "sim")), _log_fp)
            return "RESTARTED"
        except Exception:
            pass
    return "DEAD"


def _stop_capture():
    global _capture_proc
    pid = None
    with _lock:
        if _capture_proc is not None and _capture_proc.poll() is None:
            pid = _capture_proc.pid
        else:
            pid = _read_pid(CAP_PID_PATH)
        _capture_proc = None
    if pid:
        _kill_pid(pid, force=True)
    try:
        if os.path.isfile(CAP_PID_PATH):
            os.remove(CAP_PID_PATH)
    except Exception:
        pass


def start_agent(sim=False, test=False):
    global _agent_proc, _agent_mode, _log_fp
    # v847 — never "already live" on a stranger/orphan: hard-stop anything on the bridge first
    if _stop_inflight:
        return {"ok": False, "msg": "farewell still finishing — try again in a moment",
                "mode": "stopping", "error": "still stopping"}
    if _agent_alive() or _port_listener_pid() is not None:
        # If we own a healthy child and user re-clicked ON, treat as already on
        with _lock:
            owned = _agent_proc is not None and _agent_proc.poll() is None
        if owned and _bridge_ping() is not None and not sim:
            return {"ok": True, "msg": "already on air", "mode": _agent_mode or "live",
                    "pid": _agent_proc.pid if _agent_proc else None}
        # Orphan / stale / wrong mode → kill cleanly (no second farewell if already stopping)
        stop_agent(farewell=False)
        time.sleep(0.35)

    with _lock:
        if _agent_proc is not None and _agent_proc.poll() is None:
            return {"ok": True, "msg": "already running", "mode": _agent_mode}
        # re-check port after stop
        if _port_listener_pid() is not None:
            # last resort force-kill port holder
            _kill_pid(_port_listener_pid(), force=True)
            time.sleep(0.2)

        os.makedirs(HERE, exist_ok=True)
        if _log_fp:
            try:
                _log_fp.close()
            except Exception:
                pass
        try:   # v765 — cap the agent log (~2MB keeps months; never grows unbounded)
            if os.path.isfile(LOG_PATH) and os.path.getsize(LOG_PATH) > 2_000_000:
                with open(LOG_PATH) as _lf:
                    _tail = _lf.readlines()[-4000:]
                with open(LOG_PATH, "w") as _lf:
                    _lf.writelines(_tail)
        except Exception:
            pass
        _log_fp = open(LOG_PATH, "a", buffering=1)
        plat = "windows" if IS_WIN else "mac"
        _log_fp.write(
            f"\n—— control start {time.strftime('%Y-%m-%d %H:%M:%S')} "
            f"mode={'sim' if sim else 'live'} · {plat} ——\n"
        )
        _log_fp.flush()

        env = _env_clean(sim=sim)
        if test:
            # v786 - button-matrix / harness runs must NEVER become theatre reels
            env["TV_NO_JOURNAL"] = "1"
        # v786 (cousin: 'ON AIR just spins') - LOUD preflight: the #1 silent killer is a
        # missing claude CLI; the agent dies at boot and the UI spun forever with no reason.
        if not sim and not env.get("TV_STUB") and not env.get("TV_CLAUDE_BIN"):
            import shutil as _sh
            if not _sh.which("claude", path=env.get("PATH", "")):
                _agent_mode = "off"
                _log_fp.write("!! claude CLI not found on PATH - agent cannot see\n")
                _log_fp.flush()
                return {"ok": False,
                        "error": "Claude Code CLI not found - install it, then press ON AIR again",
                        "fix": ("irm https://claude.ai/install.ps1 | iex" if IS_WIN
                                else "curl -fsSL https://claude.ai/install.sh | bash"),
                        "mode": "off"}
        # Windows needs the capture half; Mac agent uses screencapture itself
        if IS_WIN:
            _start_capture(env, _log_fp)

        # v1251 — refuse LIVE start when THIS process lacks Screen Recording TCC.
        # Headless supervisor spawn → agent inherits deny → window pin fails → desktop
        # wallpaper on the eye (Konyo live 2026-07-22). SIM still allowed.
        if (sys.platform == "darwin" and not sim and not env.get("TV_STUB")
                and not _screen_recording_ok_quick()):
            _agent_mode = "off"
            msg = ("Screen Recording not granted to this Python — the eye would only "
                   "see the desktop. Quit the headless console, run: "
                   "bash tv/tvd-scan.sh  (or open TV DIABLO.app via Terminal), "
                   "enable Python in System Settings → Privacy → Screen Recording, "
                   "then press ON AIR again.")
            _log_fp.write("!! " + msg + "\n")
            _log_fp.flush()
            return {"ok": False, "error": msg, "mode": "off",
                    "fix": "bash tv/tvd-scan.sh"}

        cmd = [sys.executable, os.path.join(HERE, "tv_diablo.py")]
        if IS_WIN:
            cmd.append("--watch")

        popen_kw = dict(
            args=cmd,
            cwd=REPO,
            env=env,
            stdout=_log_fp,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
        )
        if IS_WIN:
            popen_kw["creationflags"] = _WIN_CREATE
        else:
            # v779 — do NOT setsid on Mac. A start_new_session child of a launchd-orphaned
            # control (ppid 1) loses the Screen Recording TCC chain; screencapture then
            # writes nothing and the eye freezes on a stale desktop frame.
            popen_kw["start_new_session"] = False

        _agent_proc = subprocess.Popen(**popen_kw)
        _write_pid(PID_PATH, _agent_proc.pid)
        _agent_mode = "sim" if sim else "live"

    for _ in range(50):
        if _bridge_ping() is not None:
            break
        time.sleep(0.15)
    # v786 - a dead-at-boot agent must SAY SO, not leave the lamp spinning (cousin's Windows hang)
    if _bridge_ping() is None and (_agent_proc is None or _agent_proc.poll() is not None):
        with _lock:
            _agent_mode = "off"
        tail = ""
        try:
            with open(LOG_PATH, "rb") as _lf:
                tail = _lf.read()[-1500:].decode("utf-8", "replace")
        except Exception:
            pass
        return {"ok": False, "error": "agent died at boot - see log", "logTail": tail, "mode": "off"}
    return {
        "ok": True,
        "msg": "started",
        "mode": _agent_mode,
        "pid": _agent_proc.pid if _agent_proc else None,
        "platform": "windows" if IS_WIN else "mac",
        "watch": IS_WIN,
    }


def _prewarm_seal_cache():
    """v880 (Grok j / back-pass #4) — build the theatre's ?w=1280 derivatives for the NEWEST
    sealed session in a low-priority background thread: first playback pays no sips storm.
    Mac only, concurrency 1, errors swallowed, never blocks the seal."""
    if IS_WIN:
        return
    def _run():
        try:
            time.sleep(2.0)
            if HERE not in sys.path:
                sys.path.insert(0, HERE)
            import replay as _rp
            try:
                sessions = _rp.split_sessions(_rp.load_journal())
                rows = sessions[-1] if sessions else []
            except Exception:
                rows = []
            fids = [str(r.get("frameId")) + ".jpg" for r in (rows or []) if r.get("frameId")]
            cache_dir = os.path.join(HIST_DIR, "cache1280")
            os.makedirs(cache_dir, exist_ok=True)
            for fb in fids[:400]:
                src = os.path.join(HIST_DIR, fb)
                dst = os.path.join(cache_dir, fb)
                if not os.path.isfile(src) or os.path.isfile(dst):
                    continue
                try:
                    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "72",
                                    "--resampleHeightWidthMax", "1280", src, "--out", dst],
                                   capture_output=True, timeout=10,
                                   preexec_fn=(lambda: os.nice(15)))
                except Exception:
                    pass
        except Exception:
            pass
    threading.Thread(target=_run, daemon=True, name="tvd-prewarm").start()


def _force_kill_all_agents(reason=""):
    """v926.2 — the guaranteed stop: SIGKILL every agent pid + port holder, clear state, always
    return a valid response. The agent journals incrementally, so a hard kill loses at most the
    session_end marker (the library still shows the run). Used when the polite path raises/hangs."""
    global _agent_proc, _agent_mode, _stop_inflight, _BOARD_OPENED
    try:
        pids = set(_collect_agent_pids()) | set(filter(None, [_port_listener_pid(), _read_pid(PID_PATH)]))
        for pid in pids:
            try: _kill_pid(pid, force=True)
            except Exception: pass
        time.sleep(0.4)
    except Exception:
        pass
    try: _stop_capture()
    except Exception: pass
    with _lock:
        _agent_proc = None
        _agent_mode = "off"
    _stop_inflight = False
    _BOARD_OPENED = False
    try:
        if os.path.isfile(PID_PATH):
            os.remove(PID_PATH)
    except Exception:
        pass
    dead = _port_listener_pid() is None
    return {"ok": True, "msg": "force-stopped · off" + (" · " + reason if reason else ""),
            "farewell": False, "sessionSaved": True, "bridgeDown": dead, "forced": True}


def _console_exit_stop_onair(reason="quit"):
    """v935.8 — EXIT SAFEGUARD (Konyo: 'exiting the console must stop ON AIR — it's always on').

    Closing the pywebview window used to only `srv.shutdown()` and LEAVE the agent live on
    :17771 (the banner even said 'agent left as-is'). That orphan kept ON AIR forever.
    Now every real exit path — window close, atexit, SIGTERM/SIGINT — seals + stops the
    agent (same as tvd stop /api/stop, farewell OFF so quit is instant). Idempotent.
    """
    global _EXIT_STOP_DONE
    # Secondary --window-only attach: the primary control process owns the agent.
    if globals().get("_WINDOW_ONLY"):
        return {"ok": True, "msg": "window-only — primary owns ON AIR", "skipped": True}
    with _EXIT_STOP_LOCK:
        if _EXIT_STOP_DONE:
            return {"ok": True, "msg": "exit stop already ran", "skipped": True}
        _EXIT_STOP_DONE = True
    print(f"📺 exit safeguard — stopping ON AIR ({reason})…", flush=True)
    try:
        # If nothing is on air, stop_agent is cheap and returns already-off.
        if not _agent_alive() and _port_listener_pid() is None and _agent_mode == "off":
            print("   already off — nothing to stop", flush=True)
            return {"ok": True, "msg": "already off", "farewell": False}
    except Exception:
        pass
    try:
        r = stop_agent(farewell=False)
        print(f"   stop_agent → {r.get('msg') or r}", flush=True)
        # Belt + suspenders: anything still holding :17771 dies now
        if _port_listener_pid() is not None or _agent_alive():
            r2 = _force_kill_all_agents(f"exit-safeguard residual ({reason})")
            print(f"   residual force → {r2.get('msg') or r2}", flush=True)
            return r2
        return r
    except Exception as e:
        print(f"   stop_agent raised ({e}) — force kill", flush=True)
        try:
            return _force_kill_all_agents(f"exit-safeguard ({reason}): {e}")
        except Exception as e2:
            print(f"   force kill failed: {e2}", flush=True)
            return {"ok": False, "msg": str(e2)}


def stop_agent(farewell=True):
    """v847/v899 — OFF/STOP both SAVE the session (session_end journal via /shutdown).
    STOP: short farewell (hard-cap ~18s, was 95s). OFF: seal only. Then hard-kill orphans.
    Never leave _stop_inflight True if the agent is already dead (unstick ON AIR)."""
    global _agent_proc, _agent_mode, _stop_inflight, _BOARD_OPENED
    if _stop_inflight:
        # v946.2 — another stop in flight: wait SHORT, then force-clear (never hang End Session)
        deadline = time.time() + 2.5
        while _stop_inflight and time.time() < deadline:
            if not _agent_alive() and _port_listener_pid() is None:
                _stop_inflight = False
                _agent_mode = "off"
                return {"ok": True, "msg": "already off", "farewell": farewell, "sessionSaved": True}
            time.sleep(0.15)
        if not _agent_alive() and _port_listener_pid() is None:
            _stop_inflight = False
            _agent_mode = "off"
            return {"ok": True, "msg": "already off", "farewell": farewell, "sessionSaved": True}
        # hung stop — force clear so ON AIR is not permanently blocked
        _stop_inflight = False
    _stop_inflight = True
    try:
        pids = _collect_agent_pids()
        if not pids and not IS_WIN and _port_listener_pid() is None:
            _agent_mode = "off"
            _stop_capture()
            _BOARD_OPENED = False
            return {"ok": True, "msg": "already off", "farewell": farewell, "sessionSaved": True}

        # 1) Polite shutdown — agent seals sessions.jsonl (session_end) then exits
        asked = _ask_agent_shutdown(
            farewell=bool(farewell),
            reason=("stop" if farewell else "off"),
            timeout=1.0,
        )

        # 2) If polite path didn't engage, fall back to signals
        if not asked and pids:
            sent_break = False
            if IS_WIN:
                with _lock:
                    if (
                        _agent_proc is not None
                        and _agent_proc.poll() is None
                    ):
                        try:
                            _agent_proc.send_signal(signal.CTRL_BREAK_EVENT)
                            sent_break = True
                        except Exception:
                            pass
            if not sent_break:
                for pid in pids:
                    _kill_pid(pid, force=False)

        # 3) Wait for bridge death, then FORCE-KILL — v946.2: 2.5s max (was 3–6s); seal is
        # already on disk before kill, so a stuck agent must never pin End Session.
        wait_s = 2.5
        deadline = time.time() + wait_s
        while time.time() < deadline:
            if _port_listener_pid() is None and not any(_pid_alive(p) for p in (pids or [])):
                break
            time.sleep(0.15)
        else:
            # force-kill every remaining agent pid + port holder
            for pid in set(pids or []) | set(filter(None, [_port_listener_pid(), _read_pid(PID_PATH)])):
                _kill_pid(pid, force=True)
            time.sleep(0.2)

        # always stop Windows capture with the agent
        _stop_capture()

        with _lock:
            if _agent_proc is not None:
                try:
                    _agent_proc.poll()  # reap zombie
                except Exception:
                    pass
            _agent_proc = None
            _agent_mode = "off"
        try:
            if os.path.isfile(PID_PATH):
                os.remove(PID_PATH)
        except Exception:
            pass
        # v785 — belt for the agent's own _eye_clear
        try:
            _eye = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames", "eye.jpg")
            if os.path.isfile(_eye):
                os.remove(_eye)
        except Exception:
            pass
        _BOARD_OPENED = False
        dead = _port_listener_pid() is None
        return {
            "ok": True,
            "msg": "session saved · off" if dead else "stop requested · forcing",
            "farewell": bool(farewell),
            "sessionSaved": True,
            "bridgeDown": dead,
        }
    finally:
        _stop_inflight = False
        # v946.2 — kill sticky ON AIR: clear bridge cache so status never reports bridge=True
        # after a deliberate stop (was the "End Session stuck" ghost for up to ~6–10s).
        try:
            _BR_CACHE["ping"] = False
            _BR_CACHE["ts"] = 0.0
            _BR_CACHE["st"] = None
            globals()["_BRIDGE_LAST_OK"] = 0.0
            globals()["_agent_mode"] = "off"
        except Exception:
            pass
        try:
            _prewarm_seal_cache()   # v879 (Grok j) — theatre derivatives warm while the Mac is quiet
        except Exception:
            pass


def _file_url(path, fragment=""):
    ap = os.path.abspath(path).replace("\\", "/")
    if IS_WIN:
        # file:///C:/Users/...
        if not ap.startswith("/"):
            ap = "/" + ap
        url = "file://" + ap
    else:
        url = "file://" + ap
    if fragment:
        url += "#" + fragment
    return url


_MAC_BROWSERS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
]

_BOARD_OPENED = False
def _open_board_once():
    """v764 — ON/SIM auto-open the board only ONCE per control session; afterwards the
    already-open tab lights up by itself (the board's auto-sync probe). No duplicate tabs."""
    global _BOARD_OPENED
    if _BOARD_OPENED:
        return "already-open (auto-sync)"
    _BOARD_OPENED = True
    open_board(auto_on=True)
    return "opened"

def _open_board_native(tab="session"):
    """v767.1 (Konyo: 'no need for Chrome anymore') — the BOARD opens in its own native
    window too: a sibling process runs pywebview on the LOCAL bible.html#tvd. Returns True
    if the native window spawned; False → caller falls back to a browser."""
    try:
        import webview  # noqa: F401
    except ImportError:
        if not ensure_webview():
            return False
    # v773.1 — SINGLETON: Grok's button-testing spawned 26 accumulated board windows (each a
    # python+WebKit tree) and lagged the whole Mac. Exactly ONE board window may live.
    try:
        if os.path.isfile(BOARD_PID_PATH):
            try:
                old = int(open(BOARD_PID_PATH).read().strip() or 0)
                if old:
                    os.kill(old, signal.SIGKILL)
            except Exception:
                pass
    except Exception:
        pass
    try:
        proc = subprocess.Popen(
            [sys.executable, os.path.abspath(__file__), "--board-window", "--hash=" + (tab or "session")],
            cwd=REPO,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=_WIN_CREATE if IS_WIN else 0,
        )
        try:
            with open(BOARD_PID_PATH, "w") as f:
                f.write(str(proc.pid))
        except Exception:
            pass
        return True
    except Exception:
        return False

def open_board(auto_on=True, tab="session"):
    """Open the bible TV·D tab. v764: the board AUTO-SYNCS to the bridge now (lamp + probe),
    so the deep link only needs to LAND on #tvd — and macOS `open` DROPS file:// fragments
    (the 'routes me to the wrong page' bug), so prefer a direct browser spawn like Windows."""
    if not os.path.isfile(BIBLE):
        return {"ok": False, "msg": "bible.html missing"}
    if _open_board_native(tab):
        return {"ok": True, "msg": "board opened (native window)", "tab": tab}
    url = _file_url(BIBLE, tab or "session")
    try:
        if sys.platform == "darwin":
            opened = False
            for browser in _MAC_BROWSERS:
                if os.path.isfile(browser):
                    try:
                        subprocess.Popen(
                            [browser, url],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        opened = True
                        break
                    except Exception:
                        continue
            if not opened:
                subprocess.Popen(
                    ["open", url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        elif IS_WIN:
            # Prefer a real browser so the #hash survives (os.startfile often drops it)
            opened = False
            for browser in _windows_browsers():
                try:
                    subprocess.Popen(
                        [browser, url],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=_WIN_CREATE,
                    )
                    opened = True
                    break
                except Exception:
                    continue
            if not opened:
                os.startfile(url)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", url])
        return {"ok": True, "msg": "board opened", "url": url}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def _windows_browsers():
    """Ordered Chrome/Edge/Brave paths for --app fallback only."""
    cands = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        os.path.expandvars(r"%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe"),
    ]
    return [c for c in cands if c and os.path.isfile(c)]


def ensure_webview():
    """Import pywebview; try a one-shot user pip install if missing."""
    try:
        import webview  # noqa: F401

        return True
    except ImportError:
        pass
    # one attempt — installers also pre-install; this covers first-run edge cases
    # PEP 668 (Homebrew/managed pythons) blocks even --user installs — try plain first,
    # then once more with --break-system-packages (a user-scoped GUI dep, not a system change).
    for extra in ([], ["--break-system-packages"]):
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--user", "--quiet",
                 "pywebview>=5.0", *extra],
                check=False,
                timeout=180,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=_WIN_CREATE if IS_WIN else 0,
            )
        except Exception:
            continue
        try:
            import webview  # noqa: F401
            break
        except ImportError:
            continue
    try:
        import webview  # noqa: F401

        return True
    except ImportError:
        return False


def _open_browser_app_fallback(url):
    """Last resort if pywebview is unavailable — Chrome/Edge app mode."""
    if sys.platform == "darwin":
        for app in (
            "Google Chrome",
            "Chromium",
            "Microsoft Edge",
            "Brave Browser",
            "Arc",
        ):
            try:
                r = subprocess.run(
                    ["open", "-na", app, "--args", f"--app={url}", "--new-window"],
                    capture_output=True,
                    timeout=5,
                )
                if r.returncode == 0:
                    return
            except Exception:
                continue
        subprocess.Popen(["open", url])
        return
    if IS_WIN:
        for browser in _windows_browsers():
            try:
                subprocess.Popen(
                    [browser, f"--app={url}", "--window-size=1100,780"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=_WIN_CREATE,
                )
                return
            except Exception:
                continue
        try:
            os.startfile(url)  # type: ignore[attr-defined]
        except Exception:
            pass
        return
    try:
        import webbrowser

        webbrowser.open(url)
    except Exception:
        pass


def _window_lock_write():
    """v1248 — mark that THIS process holds a live native window (takeover guard)."""
    try:
        with open(WINDOW_PID_PATH, "w") as f:
            f.write(str(os.getpid()))
    except Exception:
        pass


def _window_lock_clear():
    try:
        if os.path.isfile(WINDOW_PID_PATH):
            os.remove(WINDOW_PID_PATH)
    except Exception:
        pass


def _window_present():
    """v1248 — True iff a live native TV DIABLO window (this or another process) is open.
    Self-healing: a stale lock whose pid is dead reads as NOT present."""
    try:
        if not os.path.isfile(WINDOW_PID_PATH):
            return False
        pid = int((open(WINDOW_PID_PATH).read().strip() or 0))
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)          # raises if the pid is dead
        except ProcessLookupError:
            return False             # stale lock → no window
        except PermissionError:
            return True              # alive, owned by another user/context
        return True
    except Exception:
        return False


def _screen_recording_ok_quick():
    """v1251 — True when THIS process holds macOS Screen Recording TCC.
    Headless supervisor launches do NOT — children inherit the deny, so window pin
    fails and the old full-screen fallback captured the DESKTOP wallpaper."""
    if sys.platform != "darwin":
        return True
    try:
        from Quartz import CGPreflightScreenCaptureAccess
        return bool(CGPreflightScreenCaptureAccess())
    except Exception:
        return True  # no Quartz → don't block; capture path will self-diagnose


def _reclaim_headless_for_scan():
    """v1251 — free :17772 from the supervisor's headless console so a TCC-capable
    --open launch can BECOME the primary server (agent inherits Screen Recording).

    The v1248 window-only takeover left the headless process owning the agent child,
    so ON AIR always ran without Screen Recording → window pin failed → desktop feed.
    Returns True when a reclaim was attempted (caller should re-bind)."""
    pause = os.path.join(HERE, ".tvd_supervisor_pause")
    try:
        with open(pause, "a", encoding="utf-8") as f:
            f.write("scan-reclaim %s\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
    except Exception:
        pass
    # Prefer a clean kill of the known headless launcher only (never kill ourselves).
    killed = 0
    try:
        out = subprocess.run(
            ["pgrep", "-f", "control_app.py --no-open"],
            capture_output=True, text=True, timeout=3)
        for line in (out.stdout or "").splitlines():
            try:
                pid = int(line.strip())
            except Exception:
                continue
            if pid == os.getpid() or pid <= 1:
                continue
            try:
                os.kill(pid, signal.SIGTERM)
                killed += 1
            except Exception:
                pass
    except Exception:
        pass
    if killed:
        time.sleep(0.6)
        # escalate stragglers
        try:
            out2 = subprocess.run(
                ["pgrep", "-f", "control_app.py --no-open"],
                capture_output=True, text=True, timeout=3)
            for line in (out2.stdout or "").splitlines():
                try:
                    pid = int(line.strip())
                except Exception:
                    continue
                if pid == os.getpid() or pid <= 1:
                    continue
                try:
                    os.kill(pid, signal.SIGKILL)
                except Exception:
                    pass
            time.sleep(0.25)
        except Exception:
            pass
    print(f"📺 reclaimed headless console for live scan "
          f"(paused supervisor · killed {killed} --no-open) — "
          f"this process is now PRIMARY with Screen Recording chain", flush=True)
    return True


def open_control_window():
    """Open the real native app window (pywebview). Blocks until the user closes it."""
    # v1251 — cache-bust the WKWebView URL with the ship stamp so a relaunch never
    # keeps a stale control_ui / board iframe from a prior version (Konyo: "I only see v1248"
    # while /api/status already served v1251 — classic WebKit document cache).
    url = f"http://127.0.0.1:{CONTROL_PORT}/?v={_app_ver()}"
    # wait for the local server to answer (up to ~3s)
    for _ in range(30):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{CONTROL_PORT}/api/status", timeout=0.3) as r:
                if r.status == 200:
                    break
        except Exception:
            time.sleep(0.1)

    if not ensure_webview():
        print("⚠ pywebview not installed — falling back to browser app window")
        print("   fix:  python3 -m pip install --user pywebview")
        _loud_fail("TV DIABLO", "Native window engine missing (pywebview/WebView2). "
                   "Opening in your browser instead.\n\nFix: re-run the installer one-liner "
                   "from the website — it now bootstraps everything.\nLog: " + LOG_PATH)
        _open_browser_app_fallback(url)
        return

    import webview

    icon = None
    for cand in (
        os.path.join(HERE, "tv_diablo_icon.png"),
        os.path.join(REPO, "art", "diablo_icon.png"),
    ):
        if os.path.isfile(cand):
            icon = cand
            break

    kwargs = dict(
        title="TV DIABLO",
        url=url,
        width=1120,
        height=800,
        min_size=(880, 600),
        background_color="#070605",
        text_select=False,
        confirm_close=False,
        easy_drag=False,
    )
    # icon= supported on some backends; ignore if it errors
    try:
        if icon:
            globals()["_MAIN_WIN"] = webview.create_window(**kwargs, icon=icon)
        else:
            globals()["_MAIN_WIN"] = webview.create_window(**kwargs)
    except TypeError:
        globals()["_MAIN_WIN"] = webview.create_window(
            title="TV DIABLO",
            url=url,
            width=1120,
            height=800,
            min_size=(880, 600),
            background_color="#070605",
        )

    # v935.8 — window closed → stop ON AIR (events fire before webview.start returns on most backends)
    try:
        win = globals().get("_MAIN_WIN")
        if win is not None and hasattr(win, "events"):
            def _on_win_closed():
                _console_exit_stop_onair("window-closed")
            try:
                win.events.closed += _on_win_closed
            except Exception:
                try:
                    win.events.closing += lambda: _console_exit_stop_onair("window-closing")
                except Exception:
                    pass
    except Exception:
        pass

    # v928→v931 ONE SYSTEM (Konyo: "put it inside the console — better architecture") —
    # the tally/vault/chronicle engines live ONLY in bible.html JS. v928's second window
    # and v930's mini tile are DEAD: the engine is now an invisible same-origin iframe
    # (#tvd-eng) inside control_ui.html itself — one window, JS alive because the console
    # is visible. The control-side driver reaches its board through contentWindow.
    # v1248 — a --window-only / takeover attach must NOT start a second engine driver:
    # the PRIMARY (the process that bound :17772) owns the driver + closer. A duplicate
    # driver would double-fire the board. Only the primary starts these.
    if not globals().get("_WINDOW_ONLY"):
        try:
            threading.Thread(target=_engine_driver, daemon=True, name="tvd-engine-driver").start()
            threading.Thread(target=_kai_closer_loop, daemon=True, name="tvd-kai-closer").start()
        except Exception as _ee:
            print(f"⚠ engine driver failed to start ({_ee}) — tallies need a board tab open", flush=True)

    # v928 — private_mode=False FOR REAL: the comment below claimed it since forever, but
    # the call never passed it. pywebview defaults to private (ephemeral) storage, so every
    # tally/grail state in the app board silently evaporated on quit.
    # v1248 — hold the window-presence lock for this window's lifetime (takeover guard);
    # cleared on close/crash so a second launch knows whether a real window is already open.
    _window_lock_write()
    try:
        import atexit as _atexit
        _atexit.register(_window_lock_clear)
    except Exception:
        pass
    try:
        try:
            webview.start(debug=False, private_mode=False)
        except TypeError:
            # older pywebview without private_mode — ephemeral storage beats no window
            print("⚠ pywebview too old for private_mode=False — board storage is EPHEMERAL this run (tallies/grail reset on quit); pip install -U pywebview")
            try:
                webview.start(debug=False)
            except Exception as e:
                print(f"⚠ pywebview failed ({e}) — browser fallback")
                _open_browser_app_fallback(url)
        except Exception as e:
            print(f"⚠ pywebview failed ({e}) — browser fallback")
            _open_browser_app_fallback(url)
    finally:
        _window_lock_clear()
    # webview.start() returns when the user closes the window — always stop ON AIR
    _console_exit_stop_onair("webview-returned")


def _ejs(w, code, timeout=4.0):
    """v930 — evaluate_js with a hard timeout: pywebview's call BLOCKS FOREVER on a
    suspended/occluded WKWebView (live evidence: driver thread hung on its first probe).
    Runs the call in a scratch thread; timeout → None (treat as engine-not-responding)."""
    import queue as _q
    box = _q.Queue(maxsize=1)
    def _run():
        try:
            box.put(w.evaluate_js(code))
        except Exception as e:
            box.put(e)
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    try:
        r = box.get(timeout=timeout)
    except Exception:
        return None
    if isinstance(r, Exception):
        raise r
    return r


_KAI_STOP3 = frozenset(("the", "and", "for", "you", "are", "was", "not", "all", "any", "can",
                        "get", "has", "his", "her", "its", "our", "out", "off", "per", "via",
                        "new", "old", "one", "two", "six", "ten", "set", "use", "may", "now"))
_KAI_NOISE = ("stash", "inventory", "personal", "shared", "gems", "materials", "runes",
              "create game", "join game", "lobby", "chat", "options", "save and exit",
              "ctrl", "shift", "click", "left", "right", "move", "tab")


# v935 — KAI VOCAB GROUNDING: the closer's item-ish filter used to keep any alpha line, so
# OCR garble ("YwR PRIvATE STAS") landed in the miss ledger as if it were loot. The vocab is
# the item lexicon of the game itself — hardcoded runes/gems + every name token in bible.html.
_RUNE_NAMES = ("el", "eld", "tir", "nef", "eth", "ith", "tal", "ral", "ort", "thul", "amn",
               "sol", "shael", "dol", "hel", "io", "lum", "ko", "fal", "lem", "pul", "um",
               "mal", "ist", "gul", "vex", "ohm", "lo", "sur", "ber", "jah", "cham", "zod")
_GEM_WORDS = ("chipped", "flawed", "flawless", "perfect", "amethyst", "topaz", "sapphire",
              "emerald", "ruby", "diamond", "skull", "gem")


def _kai_add_name_tokens(vocab, full):
    """Tokenize a full item name into the vocab. Also strip Latent/Renewed so
    'Latent Black Cleft' grounds OCR of bare 'Black Cleft' (RotW sunder family)."""
    full = (full or "").strip()
    if not full:
        return
    bare = re.sub(r"^(Latent|Renewed)\s+", "", full, flags=re.I).strip()
    for name in {full, bare}:
        for tok in re.split(r"[^A-Za-z]+", name):
            if len(tok) >= 4 or (len(tok) == 3 and tok not in _KAI_STOP3):
                vocab.add(tok.lower())
            # 2-letter runes already seeded; don't flood with short junk


def _kai_fullnames():
    """v940.1 — full ITEM NAMES (lowercased) from the same bible literals the vocab uses.
    The judge's affix-scorer is for magic/rare; a grail unique scores 0 there and must
    NEVER be ruled a toss (live miscalibration: 'Hellfire Torch -> TOSS score 0')."""
    c = globals().get("_KAI_FULLNAMES")
    if c is not None:
        return c
    names = set()
    rare_combos = set()   # v943.2 — kept SEPARATE: recognized-but-not-grail-gated (see below)
    cased = {}            # FIX C (F3) — lower -> best original casing, for the grounder's display
    try:
        import re as _re
        with open(os.path.join(REPO, "bible.html"), encoding="utf-8", errors="replace") as _bf:
            src = _bf.read()
        pats = (r"(?<![A-Za-z0-9_])(?:name|n)\s*:\s*(['\"])(.*?)\1",          # name:'X' / n:'X'
                r"\"(?:name|n)\"\s*:\s*\"(.*?)\"",                            # JSON "name"/"n": "X"
                r"openDrop\(\s*(['\"])(.*?)\1",                                # v941.2 — RotW tiles (Ars Dul'Mephistos class)
                r"\"([A-Z][A-Za-z'\- ]{2,40})\"\s*:\s*[\[{]")                 # Title-Case JSON keys (drop-odds/grail seed)
        for pat in pats:
            for m in _re.finditer(pat, src):
                v = (m.group(2) if m.lastindex and m.lastindex >= 2 else m.group(1)).strip()
                if 3 <= len(v) <= 48 and not any(ch in v for ch in "<>{}$"):
                    names.add(v.lower())
                    # keep the SHORTEST original-cased spelling as canonical display
                    lo = v.lower()
                    if lo not in cased or len(v) < len(cased[lo]):
                        cased[lo] = v
        # v943.1 — RotW RARE NAME SPACE. A rare item's name is one shared PREFIX word + one
        # slot SUFFIX word (RARE_NAME_PREFIXES × RARE_NAME_POOLS, from the game's
        # RarePrefix/RareSuffix tables): "Beast Noose" = Beast+Noose, "Plague Wing" = Plague+Wing.
        # The eye reads these BARE (no base word), so the curated EXTRA_ITEMS key
        # "Plague Wing Amulet" never matched a read of "Plague Wing". Harvest both pools and
        # generate the combo space — bounded (fixed pools, no user input), every entry a
        # valid two-word rare name so garble like "YwR PRIvATE STAS" can never ground.
        # v943.2 — these go into a SEPARATE set (rare_combos): the register/recognition path
        # wants them known, but the /kai_verdict GRAIL GATE must NOT auto-promote them — a rare
        # amulet CAN be a toss, and blanket-gating 1,254 rare names would gut the Checker's job.
        _mpre = _re.search(r"RARE_NAME_PREFIXES\s*=\s*\[(.*?)\]", src, _re.S)
        _mpool = _re.search(r"RARE_NAME_POOLS\s*=\s*\{(.*?)\}", src, _re.S)
        if _mpre and _mpool:
            _pref = _re.findall(r"'([A-Za-z][A-Za-z'\- ]{1,19})'", _mpre.group(1))
            _suf = _re.findall(r"'([A-Za-z][A-Za-z'\- ]{1,19})'", _mpool.group(1))
            for _p in _pref:
                for _s in _suf:
                    nm = (_p + " " + _s).strip()
                    if 3 <= len(nm) <= 48 and not any(ch in nm for ch in "<>{}$"):
                        rare_combos.add(nm.lower())
        # v943.3 — curated CRAFTED name pool (CRAFT_NAME_EXAMPLES: slot -> ['Bone Winding',
        # 'Brimstone Grip', …]). Same law as the rares: recognized for the register, but NON-
        # shielded — crafted items are exactly what the Checker judges, so they must stay
        # toss-able. Pull names from the array literals only (skip the slot-name keys).
        _mcraft = _re.search(r"CRAFT_NAME_EXAMPLES\s*=\s*\{(.*?)\}", src, _re.S)
        if _mcraft:
            for _arr in _re.findall(r"\[([^\]]*)\]", _mcraft.group(1)):
                for _nm in _re.findall(r"'([A-Za-z][A-Za-z'\- ]{1,30})'", _arr):
                    nm = _nm.strip()
                    if 3 <= len(nm) <= 48 and not any(ch in nm for ch in "<>{}$"):
                        rare_combos.add(nm.lower())
        names |= rare_combos   # full union still returned for register/recognition
    except Exception:
        pass
    globals()["_KAI_RARE_COMBOS"] = rare_combos
    globals()["_KAI_FULLNAMES_CASED"] = cased
    globals()["_KAI_FULLNAMES"] = names
    return names


def _kai_rarenames():
    """v943.2 — the generated RotW rare-name combo space (RARE_NAME_PREFIXES × RARE_NAME_POOLS).
    Subset of _kai_fullnames(): recognized for the register/ledger, but EXCLUDED from the
    /kai_verdict grail gate so the judge may still toss a bad rare amulet/ring/jewel."""
    r = globals().get("_KAI_RARE_COMBOS")
    if r is None:
        _kai_fullnames()   # builds + caches both sets
        r = globals().get("_KAI_RARE_COMBOS") or set()
    return r


def _kai_runewordnames():
    """v948.19 — the RUNEWORD_TIP name space (Spirit/Enigma/Insight/...), lowercased.
    FIX for the Spirit grail/toss split-brain (Grok forensic #6, 2026-07-21 21:05 fast run):
    a bare runeword name like 'Spirit' was in _kai_fullnames() (harvested generically as a
    Title-Case JSON key) but NOT in _kai_rarenames(), so the /kai_verdict grail gate promoted
    it straight to tier='grail' — while bible.html's client-side aicJudgeApply deliberately
    treats runewords as NOT grail (_aicIsGrailName is unique/set-only by design, v948.5), so the
    APPLIED action stayed whatever the affix judge scored (toss, score 0). Two different verdicts
    for the same read = the split-brain.
    RECONCILIATION (both paths, same law): a runeword is REAL FORGED GEAR — never a toss/border —
    but it is NOT a grail item; grail tracking is unique/set only, runewords have their own
    Chronicle (100-runeword progress). So both /kai_verdict (here) and bible.html's aicJudgeApply
    force toss/border → 'keep' for a recognized runeword name, and neither promotes it to 'grail'.
    This set is scoped to JUST the RUNEWORD_TIP object (brace-depth bounded) so it can't
    accidentally swallow unrelated Title-Case keys from other tables."""
    r = globals().get("_KAI_RUNEWORD_NAMES")
    if r is not None:
        return r
    names = set()
    try:
        import re as _re
        with open(os.path.join(REPO, "bible.html"), encoding="utf-8", errors="replace") as _bf:
            src = _bf.read()
        m = _re.search(r"RUNEWORD_TIP\s*=\s*\{", src)
        if m:
            i = m.end()
            depth = 1
            j = i
            while j < len(src) and depth > 0:
                if src[j] == "{":
                    depth += 1
                elif src[j] == "}":
                    depth -= 1
                j += 1
            block = src[i:j]
            for km in _re.finditer(r"\"([A-Z][A-Za-z'\- ]{1,40})\"\s*:\s*\{", block):
                nm = km.group(1).strip()
                if nm:
                    names.add(nm.lower())
    except Exception:
        pass
    globals()["_KAI_RUNEWORD_NAMES"] = names
    return names


def _kai_runeword_bare(name):
    """v1250 — bare lowercased RUNEWORD_TIP key if `name` is a RW or RW+base / base+RW
    read, else ''. Pure. Mirrors bible.html `_rwResolve` intent without BASE_CLASS:
      1. exact match on RUNEWORD_TIP names
      2. longest PREFIX match: name starts with '<rw> '  (RW then base glue)
      3. longest SUFFIX match: name ends with ' <rw>'    (base then RW)
    NEVER first-token alone (that false-positives rares like 'Beast Noose' where
    Beast is a real runeword). Rare/crafted combos are also excluded by name."""
    low = str(name or "").strip().lower()
    if not low:
        return ""
    if low in _kai_rarenames():
        return ""
    rws = _kai_runewordnames()
    if low in rws:
        return low
    best = ""
    for rw in rws:
        if len(rw) <= len(best):
            continue
        if low.startswith(rw + " ") or low.endswith(" " + rw):
            best = rw
    return best


def _kai_is_runeword_name(name):
    """v1250 — True when `_kai_runeword_bare` resolves a known runeword."""
    return bool(_kai_runeword_bare(name))


def _kai_reconcile_applied(tier, app_mode):
    """v1250 — when the server upgrades tier (runeword keep / grail unique), the client's
    aicJudgeApply may already have recorded a weaker applied mode (toss). Journal applied
    must match the authoritative tier so Theatre doesn't show 'KEEP → toss'."""
    tier = str(tier or "").lower()
    app = str(app_mode or "").lower()
    if not app:
        return app_mode
    if tier == "grail" and app in ("toss", "border", "keep"):
        return "grail"
    if tier == "keep" and app in ("toss", "border"):
        return "keep"
    return app_mode


def _kai_vocab():
    """v935 — KAI's item lexicon (cached in a global, built once). Seeds the 33 classic rune
    names + gem words, then harvests alphabetic name tokens (len>=4) from every name:'…' /
    name:"…" literal in bible.html, lowercased and capped ~20k. Also buckets the set by token
    length for O(bucket) edit-distance-1 lookup. Errors swallowed — the rune/gem seed always
    survives so grounding never fully fails open even if bible.html can't be read.

    v939.1 (SuperGrok NIGHT2 open thread #1): also harvest openDrop('…') strings and
    Title-Case JSON object keys (drop-odds / grail seed) so RotW uniques that live as
    keys or onclick labels — Earth Shifter, Herald of Fright, Black Cleft — ground OCR."""
    v = globals().get("_KAI_VOCAB")
    if v is not None:
        return v
    vocab = set(_RUNE_NAMES) | set(_GEM_WORDS)
    try:
        with open(BIBLE, encoding="utf-8", errors="replace") as f:
            txt = f.read()
        # the real item DB (uniques/sets like 'Windforce') lives under the short n: / "n": keys,
        # not just name: — harvest both. The lookbehind stops the bare-n branch from matching the
        # 'n' inside words like min:/gen: (only a boundary or nothing may precede it).
        for pat in (r"""(?<![\w"])(?:name|n)\s*:\s*(['"])(.*?)\1""",
                    r""""(?:name|n)"\s*:\s*(['"])(.*?)\1"""):
            for m in re.finditer(pat, txt):
                _kai_add_name_tokens(vocab, m.group(2))
                if len(vocab) >= 20000:
                    break
            if len(vocab) >= 20000:
                break
        # openDrop('Herald of Fright') / openDrop("Earth Shifter") — RotW tiles + material cards
        if len(vocab) < 20000:
            for m in re.finditer(r"""openDrop\(\s*(['"])(.*?)\1""", txt):
                _kai_add_name_tokens(vocab, m.group(2))
                if len(vocab) >= 20000:
                    break
        # Title-Case JSON keys ("Earth Shifter": 16004764, "Latent Black Cleft": "Jun …")
        # Skip SCREAMING_CODES and single tokens that look like ids (UNI-ARMOR, hellTz).
        if len(vocab) < 20000:
            for m in re.finditer(r'"([A-Z][^"]{2,46})"\s*:', txt):
                key = m.group(1)
                if key.isupper() and " " not in key:
                    continue
                if re.fullmatch(r"[A-Za-z0-9_./+-]+", key) and " " not in key and len(key) < 6:
                    continue
                # must look like a game name: at least one space OR a long capitalised word
                if " " not in key and not re.match(r"^[A-Z][a-z]", key):
                    continue
                _kai_add_name_tokens(vocab, key)
                if len(vocab) >= 20000:
                    break
    except Exception:
        pass
    # never let a UI/noise word (stash, inventory, runes…) ground a loot line: bible.html
    # carries those as name literals too, and 'STAS' would fuzzy-match 'stash' otherwise.
    vocab.difference_update(_KAI_NOISE)
    by_len = {}
    for w in vocab:
        by_len.setdefault(len(w), set()).add(w)
    globals()["_KAI_VOCAB"] = vocab
    globals()["_KAI_VOCAB_BY_LEN"] = by_len
    return vocab


def _edit1(a, b):
    """True if a and b are within Levenshtein distance 1 (equal / one sub / one indel).
    Stdlib-only, short strings — used for fuzzy vocab grounding of noisy OCR tokens."""
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if a == b:
        return True
    if la == lb:                       # single substitution
        return sum(1 for x, y in zip(a, b) if x != y) == 1
    if la > lb:                        # make `a` the shorter — one insertion/deletion
        a, b, la, lb = b, a, lb, la
    i = j = diff = 0
    while i < la and j < lb:
        if a[i] == b[j]:
            i += 1
            j += 1
        else:
            diff += 1
            if diff > 1:
                return False
            j += 1
    return True


def _kai_vocab_hit(tok):
    """v935 — is this OCR token a known item word? Exact membership for any token (so 3-letter
    runes like 'ral'/'amn' pass), plus edit-distance-1 fuzzy against same-length±1 buckets for
    len>=4 (typo tolerance). Empty vocab → fail-open to the old keep-everything behaviour."""
    tok = tok.lower()
    vocab = _kai_vocab()
    if not vocab:
        return True
    if tok in vocab:
        return True
    # short tokens (<=4) are exact-only: at length 4 nearly every OCR garble sits one edit from
    # SOME real 4-letter word, so fuzzy there re-admits noise like 'STAS'. Typo tolerance is for
    # the longer names (len>=5) where an edit-1 neighbour is a real signal, not a coincidence.
    if len(tok) < 5:
        return False
    by_len = globals().get("_KAI_VOCAB_BY_LEN") or {}
    for L in (len(tok) - 1, len(tok), len(tok) + 1):
        for cand in by_len.get(L, ()):
            if _edit1(tok, cand):
                return True
    return False


# ── FIX C (F3, 2026-07-22) 🏷 GRAIL TOOLTIP NAME GROUNDING ─────────────────────
# Root cause (retro-vs-photos audit): legible grail tooltips (Enigma, Harlequin Crest)
# were reduced to garble and left UNNAMED. Two distinct failures:
#   • Harlequin — the NAME line WAS read, but as 'H4RLEQVIN CR': the OCR wrote a leet
#     digit ('4'→A) into the token, so _kai_itemish's `p.isalpha()` tokenizer threw
#     'h4rleqvin' away before it could ever ground, and 'cr' was too short. The real
#     name literally never reached the vocab matcher.
#   • Enigma — roi-fast never captured the gold TITLE lines at all (only the blue stat
#     body), so there is no name token to recover from this frame (honest limitation;
#     the general grounder below still catches Enigma on any frame whose title IS read).
# The grounder de-leets OCR tokens, then matches a DISTINCTIVE signature token (len>=6,
# rare across the DB, never a stat/flavor word) against the real item name lexicon. It is
# deliberately strict — only a strong, near-exact hit on a distinctive item word names a
# frame — so gameplay/stat text can never mint a false item name (verified: 0 false
# grounds across all 142 frames of the real reel).
_KAI_LEET = {"0": "o", "1": "i", "2": "z", "3": "e", "4": "a",
             "5": "s", "6": "g", "7": "t", "8": "b", "9": "g"}
# Words that appear inside real item names (Chance Guards, Hsarus' Defense) BUT also
# dominate stat/flavor lines — never allowed to be the grounding trigger. (_KAI_STAT_WORDS,
# defined later in this file, is also folded in at call time by _kai_ground_index.)
_KAI_GROUND_STOP = frozenset({
    "strength", "defense", "chance", "magic", "attribute", "attributes", "dexterity",
    "energy", "stamina", "vitality", "damage", "poison", "cold", "fire", "lightning",
    "better", "getting", "required", "socketed", "durability", "enhanced", "increase",
    "maximum", "physical", "received", "reduced", "character", "level", "faster",
    "during", "attack", "defence", "resist", "resistance", "replenish", "regenerate"})


def _kai_deleet(tok):
    """Lowercase a raw OCR token and map common digit-for-letter OCR confusions to letters
    ('h4rleqvin' -> 'harleqvin'), dropping any other non-alpha. Pure."""
    return "".join(ch if ch.isalpha() else _KAI_LEET.get(ch, "") for ch in str(tok or "").lower())


def _kai_lev(a, b, cap=2):
    """Levenshtein distance between short strings, early-out once it provably exceeds `cap`."""
    la, lb = len(a), len(b)
    if abs(la - lb) > cap:
        return cap + 1
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        ca = a[i - 1]
        best = cur[0]
        for j in range(1, lb + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (0 if ca == b[j - 1] else 1))
            if cur[j] < best:
                best = cur[j]
        if best > cap:
            return cap + 1
        prev = cur
    return prev[lb]


def _kai_ground_index():
    """v-FIXC — build (cached) the grounding index over the STRICT grail lexicon
    (_kai_fullnames minus the permissive rare/craft combo space): distinctive signature
    tokens (len>=6, document-frequency<=3, non-stat) bucketed by length, plus a
    token->shortest-canonical-name map for display. Pure w.r.t. inputs; cached in a global."""
    idx = globals().get("_KAI_GROUND_INDEX")
    if idx is not None:
        return idx
    fulln = _kai_fullnames()
    rare = _kai_rarenames()
    cased = globals().get("_KAI_FULLNAMES_CASED") or {}
    strict = fulln - rare
    dfreq = {}
    names_by_tok = {}
    for low in strict:
        toks = {t for t in re.split(r"[^a-z]+", low) if len(t) >= 2}
        for t in toks:
            dfreq[t] = dfreq.get(t, 0) + 1
            names_by_tok.setdefault(t, []).append(low)
    sig_by_len = {}
    disp = {}
    for t, d in dfreq.items():
        if len(t) >= 6 and d <= 3 and t not in _KAI_GROUND_STOP \
                and not any(sw and sw in t for sw in _KAI_STAT_WORDS):
            sig_by_len.setdefault(len(t), []).append(t)
            low = sorted(names_by_tok[t], key=lambda x: (len(x), x))[0]
            disp[t] = cased.get(low) or " ".join(w.capitalize() for w in low.split())
    idx = {"sig_by_len": sig_by_len, "disp": disp}
    globals()["_KAI_GROUND_INDEX"] = idx
    return idx


# Tooltip-context markers: an item tooltip ALWAYS carries stat/structure lines
# (Required Strength, Durability, Defense, Character Level, Shift+Click to Unequip…).
# Grounding fires ONLY when the frame shows this context — so gameplay NARRATIVE that
# happens to share a word with a runeword ('Entering the Chaos SANCTUARY' → the Sanctuary
# runeword, 'Words of WISDOM') can never mint a false item name. A tooltip whose stat
# lines are ALL too garbled to show a marker simply stays unnamed (safe failure).
# Deliberately tooltip-SPECIFIC — no bare 'level'/'mana'/'damage' (those leak into
# gameplay level-up/combat narrative). Every word here is overwhelmingly a tooltip line.
_KAI_TOOLTIP_MARKERS = ("character", "durability", "required", "defense", "defence",
                        "socket", "unequip", "strength", "dexter", "attribute", "recovery",
                        "resist", "stamina", "vitality", "requires level", "one-hand",
                        "two-hand", "chance to")


def _kai_tooltip_context(lines):
    """True if the OCR line-set shows item-tooltip structure (stat/marker lines). Pure."""
    blob = " ".join(str(x or "") for x in (lines or [])).lower()
    return any(m in blob for m in _KAI_TOOLTIP_MARKERS)


def _kai_ground_lines(lines):
    """v-FIXC — recover REAL grail item names from garbled tooltip OCR. Fires ONLY on frames
    with item-tooltip context (_kai_tooltip_context). For each line that is NOT a stat/flavor
    line, de-leet its tokens and match any distinctive (len>=6) token against the signature
    lexicon: exact at len 6, edit-1 at len 7-9, edit-2 at len>=10. Returns a dict
    {canonicalDisplayName: matchedSignatureToken}. Empty when nothing grounds (honest —
    never invents a name from stat/gameplay text). Pure."""
    try:
        idx = _kai_ground_index()
    except Exception:
        return {}
    sig_by_len = idx["sig_by_len"]
    disp = idx["disp"]
    if not sig_by_len:
        return {}
    if not _kai_tooltip_context(lines):
        return {}
    found = {}
    for ln in (lines or []):
        low = str(ln or "").lower()
        if not low.strip():
            continue
        # stat/flavor line? (a stat KEYWORD that OCR'd cleanly) — skip; item names live on
        # their own title line and never carry these words.
        if any(sw and sw in low for sw in _KAI_STAT_WORDS):
            continue
        for raw in re.split(r"[^a-z0-9']+", low):
            d = _kai_deleet(raw)
            if len(d) < 6:
                continue
            tol = 1 if len(d) <= 9 else 2
            hit = None
            for L in range(len(d) - tol, len(d) + tol + 1):
                for st in sig_by_len.get(L, ()):
                    if (st == d) if tol == 0 else _kai_lev(d, st, tol) <= tol:
                        hit = st
                        break
                if hit:
                    break
            if hit:
                found[disp[hit]] = hit
    return found


def _kai_line_is_noise(lo):
    """v939.1 — noise must match as a WORD, not a substring.
    Substring noise killed real items: 'left'⊂cleft (Black Cleft), 'shift'⊂shifter
    (Earth Shifter), 'right'⊂fright (Herald of Fright). Multi-word phrases stay
    substring (they already have spaces: 'create game')."""
    import re as _re
    for n in _KAI_NOISE:
        if not n:
            continue
        if " " in n:
            if n in lo:
                return True
        else:
            if _re.search(r"(?<![a-z])" + _re.escape(n) + r"(?![a-z])", lo):
                return True
    return False


def _kai_itemish(s):
    """KAI v1 + v935 vocab grounding — keep item-ish OCR lines only when at least one token is
    a real game item word (exact, or one edit away for len>=4). Mirror of the agent's filter."""
    s = str(s or "").strip()
    lo = s.lower()
    if len(s) < 3:
        # v938.8 — bare 2-letter RUNE labels (El, Io…) are real; everything else short dies
        return len(s) == 2 and lo in _kai_vocab()
    if len(s) > 48:
        return False
    if _kai_line_is_noise(lo):
        return False
    # v938.8 — 'gold' left the noise list (it nuked Goldskin/Goldwrap/Goldstrike Arch):
    # gold PILES are killed by shape instead ("665 gold" / bare "gold").
    import re as _re
    if lo == "gold" or _re.fullmatch(r"\d[\d,\.]*\s*gold", lo):
        return False
    if sum(c.isdigit() for c in s) > max(3, len(s) // 2):
        return False
    # v938.8 — hyphens split like apostrophes (Trang-Oul, Amn-Sol, rune chains), and
    # 2-letter runes (El, Io…) may token (exact-membership still gates them).
    toks = [p for p in lo.replace("'", " ").replace("-", " ").split() if len(p) >= 2 and p.isalpha()]
    if not toks:
        return False
    return any(_kai_vocab_hit(p) for p in toks)


def _tab_from_ocr_lines(lines):
    """v947 pure — RotW tab from OCR; multi-tab chrome is ambiguous (→ '').

    Delegates to stash_eye (mimics intake tab reading without calling intake).
    """
    try:
        from stash_eye import tab_from_ocr_lines as _se_tab
        return _se_tab(lines)
    except Exception:
        blob = " ".join(str(t).lower() for t in (lines or []))
        if not blob.strip():
            return ""
        order = (
            ("materials", "materials"), ("material", "materials"),
            ("runes", "runes"), ("gems", "gems"),
            ("personal", "personal"), ("shared", "shared"),
            ("rune", "runes"), ("gem", "gems"), ("mat", "materials"),
        )
        hits = []
        for key, canon in order:
            if re.search(r"(?<![a-z])" + re.escape(key) + r"(?![a-z])", blob):
                if canon not in hits:
                    hits.append(canon)
        return hits[0] if len(hits) == 1 else ""


def _kai_frame_cls(lines, itemish):
    """v935.11 R5 / v947 — funnel routing class from RAW OCR lines.
      stash-runes|gems|materials|stash  panel open; tally word picks sub-class.
      inventory | tooltip | gameplay
    Multi-tab chrome no longer forces 'materials' (stash_eye tab_from_ocr_lines).
    """
    lo = [str(t).lower() for t in (lines or [])]
    blob = " ".join(lo)
    tab = _tab_from_ocr_lines(lines)
    # tally/vault tab words alone prove a stash panel (even if "stash" word missing — OCR-dark chrome)
    if tab in ("runes", "gems", "materials"):
        return "stash-" + tab
    if tab in ("personal", "shared"):
        return "stash"
    if "personal" in blob or "shared" in blob or "stash" in blob:
        # only promote to tally when a SINGLE tally word is present (not full chrome list)
        has_r = bool(re.search(r"(?<![a-z])runes?(?![a-z])", blob))
        has_g = bool(re.search(r"(?<![a-z])gems?(?![a-z])", blob))
        has_m = bool(re.search(r"(?<![a-z])materials?(?![a-z])", blob))
        tally_n = int(has_r) + int(has_g) + int(has_m)
        if tally_n == 1:
            if has_r:
                return "stash-runes"
            if has_g:
                return "stash-gems"
            if has_m:
                return "stash-materials"
        return "stash"
    if "inventory" in blob:
        return "inventory"
    if itemish:
        return "tooltip"
    return "gameplay"


def _kai_grid_vote_label(eye_tab, eye_sources, raw_grid_label, eye_cls):
    """v1194 ROUTE/GATE fix — the routing-scan build (`_kai_closer_loop`) used to set the
    scan row's gridLabel ('layout' independent class, _ROUTER_INDEP_CLASS) straight from the
    FUSED tab (`stash_eye.analyze_frame`'s `out["tab"]`) whenever it named a tally tab —
    with no check that grid itself actually contributed. `fuse_tab_signals` (stash_eye.py)
    picks OCR's chrome-strip read FIRST when it alone is unambiguous ("1 OCR tally wins"),
    before grid is even consulted; only the accompanying `sources` list says which eyes
    actually agreed. Crediting a purely OCR-driven fused tab as a "grid" vote let ONE real
    signal (chrome OCR) masquerade as TWO independent evidence classes ('chrome' AND
    'layout') — exactly the corruption `_router_conf`'s independent-class quorum exists to
    prevent (a tabstrip+grid pair can clear confidence>=2 on its own, per v947/v949). Now the
    fused-tab branch only fires when 'grid' is actually in the fusion's own agreeing-sources
    list; otherwise this falls back to the RAW pixel-only `gridLabel` (stash_eye's
    `classify_stash_grid`, independent of OCR/journal/model) — a genuinely independent
    signal, not a relabeled echo of one that already voted. Pure."""
    if eye_tab in ("runes", "gems", "materials") and "grid" in (eye_sources or []):
        return "stash-" + eye_tab
    if raw_grid_label in ("stash-runes", "stash-gems", "stash-materials"):
        return raw_grid_label
    if "grid" in (eye_sources or []) and eye_cls == "stash":
        return "stash"
    if raw_grid_label == "stash":
        return "stash"
    return None


def _kai_sticky_tab(ts, stash_times):
    """v946.1 — journal tab for a film timestamp: last deep tab with st<=ts+1.5s,
    held until the next deep tab (or 25s). Fixes gems/materials between sparse deeps."""
    if not stash_times:
        return None
    st_sorted = sorted(stash_times, key=lambda x: int(x[0] or 0))
    ts = int(ts or 0)
    cand = [(int(st), tb) for st, tb in st_sorted if int(st) <= ts + 1500]
    if not cand:
        # frame slightly before the deep stamp lands
        near = [(int(st), tb) for st, tb in st_sorted if abs(int(st) - ts) <= 4000]
        return near[0][1] if near else None
    last_st, last_tb = cand[-1]
    # next deep tab ends this hold
    nxt = next((int(st) for st, _tb in st_sorted if int(st) > last_st), None)
    if nxt is not None and ts >= nxt:
        # should have been in cand — if not, fall through
        pass
    if ts - last_st <= 25_000:
        return last_tb
    if abs(ts - last_st) <= 4000:
        return last_tb
    return None


def _kai_tab_strip_refine(fp, ocr_cls, wp):
    """v947 — intake-style tab chrome + grid fingerprint (does NOT call gemIntake/etc).

    Mimics bible `_tallyPrepImage` crops: upscaled tab band above the left grid +
    pixel fingerprint of the grid itself (rune stones / gem chroma / materials).
    wp = OCR worker (stdin/stdout already open), or None for grid-only.
    Returns refined class or original.
    """
    if ocr_cls in ("stash-runes", "stash-gems", "stash-materials"):
        return ocr_cls
    if not fp or not os.path.isfile(fp):
        return ocr_cls
    try:
        from stash_eye import analyze_frame

        def _wp_read(p):
            if wp is None:
                return {}
            try:
                wp.stdin.write(p + "\n"); wp.stdin.flush()
                line = wp.stdout.readline()
                return json.loads(line) if line else {}
            except Exception:
                return {}

        res = analyze_frame(
            fp,
            ocr_lines=None,
            journal_tab="",
            model_tab="",
            ocr_worker_read=_wp_read if wp is not None else None,
            work_dir=os.path.dirname(fp),
        )
        cls = res.get("cls") or ""
        if cls in ("stash-runes", "stash-gems", "stash-materials"):
            return cls
        if cls == "stash" and (not ocr_cls or ocr_cls == "gameplay"):
            return "stash"
        if res.get("tab") in ("personal", "shared") and (not ocr_cls or ocr_cls == "gameplay"):
            return "stash"
    except Exception:
        pass
    return ocr_cls


# ── v943 AUTO-REGISTER stage 1 — THE REGISTER LEDGER ────────────────────────────
# Konyo's law: "it read it, it analyzed it → it's registered — why not." This is the
# EVIDENCE ledger only (what the eyes witnessed this session); the write-into-Chronicle
# arc with dedup law is a later bible-side stage. Nothing here touches board/grail/chronicle.
_REGISTER_ANCHORS = frozenset((
    "horadric cube", "wirt's leg", "wirts leg", "key", "tome",
))


def _register_is_junk(low):
    """Reuse the KAI word-boundary noise sense, plus gold-shape + potion/scroll consumables.
    Real DB grounding already gates most junk; this catches the always-carried filler."""
    if _kai_line_is_noise(low):
        return True
    if low == "gold" or re.fullmatch(r"\d[\d,\.]*\s*gold", low):
        return True
    for w in ("potion", "rejuvenation", "scroll"):
        if re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", low):
            return True
    return False


def _register_is_anchor(low):
    if low in _REGISTER_ANCHORS:
        return True
    return "tome of" in low   # Tome of Town Portal / Tome of Identify


# ── v948.2 LIVE Item Checker (mid-session Stage-3 twin) ───────────────────────
# Post-seal Stage-3 already judges tooltip reel frames. Live path fires aicJudge as
# soon as a deep read lands with NEW/MOVED (non-echo) names — same subscription brain
# + aicJudgeApply. Stage-3 post-seal skips frames already covered by a near-ts verdict.
def _live_judge_interesting_names(rd):
    """Names that justify a live Item Checker call. Prefer sticky NEW/MOVED; fall back
    to full names for pre-v948 journals. Drops anchors + junk. Pure."""
    if not isinstance(rd, dict):
        return []
    nnew = rd.get("names_new")
    nmoved = rd.get("names_moved") if isinstance(rd.get("names_moved"), list) else []
    if nnew is None:
        cand = list(rd.get("names") or [])
    else:
        cand = list(nnew or []) + list(nmoved or [])
    out, seen = [], set()
    for n in cand:
        s = str(n or "").strip()
        if not s:
            continue
        low = s.lower()
        if low in seen:
            continue
        if _register_is_anchor(low) or _register_is_junk(low):
            continue
        seen.add(low)
        out.append(s)
    return out


def _live_judge_should_queue(rd):
    """v948.2 — True when this deep read should enqueue a live aicJudge.
    Gates: deep lane, non-provisional, frameId, NEW/MOVED interesting names,
    not a pure tally tab (runes/gems/materials), env TV_KAI_JUDGE + TV_KAI_JUDGE_LIVE.
    Pure (no I/O)."""
    if not isinstance(rd, dict):
        return False
    if os.environ.get("TV_KAI_JUDGE", "1") == "0":
        return False
    if os.environ.get("TV_KAI_JUDGE_LIVE", "1") == "0":
        return False
    if str(rd.get("lane") or "") != "deep" or rd.get("provisional"):
        return False
    fid = str(rd.get("frameId") or "").strip()
    if not fid:
        return False
    tab = str(rd.get("stashTab") or "").lower()
    if tab in ("runes", "gems", "materials"):
        return False  # tally lanes — not Item Checker tooltips
    return bool(_live_judge_interesting_names(rd))


def _judge_already_near(rows, ts, window_ms=6000):
    """True if a kai-judge receipt already landed within ±window_ms of ts.
    Prevents live + post-seal double-vision on the same hover. Pure."""
    try:
        ts = int(ts or 0)
    except Exception:
        return False
    if not ts:
        return False
    w = max(0, int(window_ms or 0))
    for r in rows or []:
        if r.get("lane") != "kai" or r.get("mode") != "kai-judge":
            continue
        try:
            jt = int(r.get("ts") or r.get("captureTs") or 0)
        except Exception:
            continue
        if jt and abs(jt - ts) <= w:
            return True
    return False


def _fire_aic_judge_js(hist_path, sid, frame_id, fts, live=False, tag=None):
    """Shared evaluate_js payload: aicJudge → aicJudgeApply → /kai_verdict.
    live=True tags the body so journals/notes distinguish mid-session vs post-seal.
    v949.x — optional `tag` (e.g. 'super') rides through to /kai_verdict as res.tag so a
    caller (SUPER-ANALYZE KAI) can identify its OWN verdicts in the journal afterward,
    without changing behavior for existing callers (tag=None is a no-op, omitted from
    the POST body entirely)."""
    return (
        "(function(){try{var F=document.getElementById('tvd-eng');if(!F||!F.contentWindow)return 0;var W=F.contentWindow;"
        "if(typeof W.aicJudge!=='function')return 0;"
        "fetch(%s+'?'+Date.now()).then(function(r){if(!r.ok)throw 0;return r.blob()}).then(function(b){"
        "return W.aicJudge(new W.File([b],'kai-judge.jpg',{type:'image/jpeg'}))}).then(function(res){"
        "res=res||{};res.sid=%s;res.frameId=%s;res.fts=%s;res.live=%s;%s"
        "try{if(res.ok&&typeof W.aicJudgeApply==='function'){"
        "res.applied=W.aicJudgeApply(res,{sid:res.sid,frameId:res.frameId,fts:res.fts})||null"
        "}}catch(_ae){res.applied={ok:false,why:String(_ae&&_ae.message||_ae)}}"
        "fetch('/kai_verdict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(res)}).catch(function(){})"
        "}).catch(function(){});return 1}catch(e){return 0}})()"
    ) % (json.dumps(hist_path), json.dumps(sid or ""), json.dumps(frame_id or ""),
         json.dumps(int(fts or 0)), "true" if live else "false",
         ("res.tag=" + json.dumps(str(tag)) + ";") if tag else "")


# v944.7 (Fable forensic recalibration) — the KAI "missed" ledger over-counted: it flagged a
# frame missed if ANY OCR line was new, so a tooltip's STAT/FLAVOR lines ("Required Level 75",
# "Level 30 Hydra", "Keep in Inventory") flagged a frame as missed even when the item NAME itself
# was already read/registered (Hellfire Torch false positive). A real miss is an unread ITEM NAME,
# not unread flavor text. _kai_nameish keeps only name-shaped lines so genuine misses (a hovered
# Jade Jewel never registered) still surface while flavor-only frames stop crying wolf.
_KAI_STAT_WORDS = (
    "required", "resist", "click", "insert", "charge", "attribute", "skill", "defen",
    "damage", "durab", "level", "socket", "bonus", "keep in", "chance", "faster", "enhanced",
    "block", "strength", "dexter", "energy", "vital", "mana", "life", "radius", "cast", "warlock",
    "resistance", "move to", "unequip", "gain", "hit recovery", "attack rating", "magic item",
    "gold from", "vendor", "replenish", "regenerat", "absorb", "pierce", "leech", "freeze",
)


def _kai_nameish(text):
    """True if an OCR line looks like an ITEM NAME (the flag-worthy part of a tooltip), not a
    stat/flavor line. Names carry no +/%/digit stat punctuation and no stat keyword."""
    s = (text or "").strip()
    low = s.lower()
    if not (3 <= len(s) <= 40):
        return False
    if any(ch.isdigit() for ch in s) or "%" in s or "+" in s:
        return False
    if any(w in low for w in _KAI_STAT_WORDS):
        return False
    # a name has letters and isn't a bare UI word
    return any(ch.isalpha() for ch in s) and low not in ("stash", "inventory", "personal",
                                                          "shared", "gems", "materials", "runes")


_KAI_TIER_RANK = {"grail": 3, "keep": 2, "border": 1}   # v1193 — see _kai_compile_register


def _kai_compile_register(sess_rows):
    """v943 — the session's REGISTERABLE ITEMS: union of every deep-read name and every
    KAI judge verdict tiered grail/keep/border, filtered to real DB items (_kai_fullnames)
    minus anchors + noise. One record per unique name, earliest sighting wins.
    Record: {name, firstSeenTs, frameId, loc, tier}. Pure — no side effects."""
    fulln = _kai_fullnames()
    reg = {}   # name.lower() -> record

    def _consider(name, ts, frame_id, loc, tier):
        nm = str(name or "").strip()
        if not nm:
            return
        low = nm.lower()
        # v1250 — glued RW reads ('Spirit Monarch') are NOT in fullnames (only bare
        # RUNEWORD_TIP keys are). Canonicalize to the bare RW so the register + Chronicle
        # inbox still see the forged word, instead of silently dropping the deep name.
        if low not in fulln:
            bare = _kai_runeword_bare(nm)
            if bare and bare in fulln:
                low = bare
                # prefer original casing when the deep already said the bare word; else
                # title-case the bare key (good enough for single-token RWs like Spirit;
                # multi-word keys keep their harvested lower form title-cased).
                nm = nm if nm.lower() == bare else " ".join(w.capitalize() for w in bare.split())
            else:
                return
        if _register_is_anchor(low) or _register_is_junk(low):
            return
        ts = int(ts or 0)
        cur = reg.get(low)
        if cur is None:
            reg[low] = {"name": nm, "firstSeenTs": ts, "frameId": frame_id or "",
                        "loc": loc, "tier": (tier or None)}
            return
        # earliest sighting wins the frame/ts/loc (a factual "when was it first seen" —
        # first really is best there). TIER is a QUALITY verdict, not a timestamp — sess_rows
        # is walked in chronological order, so "first non-blank tier wins" (the old rule) meant
        # an early low-confidence 'border' guess froze the register forever, even after a LATER,
        # more authoritative same-session re-read (e.g. super-analyze, which this file's own
        # _kai_reconcile ranks ABOVE a first-pass read) proved it 'grail'. v1193 — BEST tier
        # wins instead (rank grail>keep>border, mirrors the never-zero/max-verified-total-wins
        # law already applied to counts, now applied to tier): a later, better verdict can
        # upgrade a stale one, but a proven grail can never be silently buried back under a
        # weaker border/keep guess that happens to land afterward.
        if ts and (not cur["firstSeenTs"] or ts < cur["firstSeenTs"]):
            cur["firstSeenTs"] = ts
            cur["frameId"] = frame_id or cur["frameId"]
            if loc is not None:
                cur["loc"] = loc
        if loc is not None and cur.get("loc") is None:
            cur["loc"] = loc
        if tier and _KAI_TIER_RANK.get(tier, 0) > _KAI_TIER_RANK.get(cur.get("tier") or "", 0):
            cur["tier"] = tier

    for r in sess_rows:
        ts = int(r.get("ts") or r.get("captureTs") or 0)
        fid = str(r.get("frameId") or "")
        nl = r.get("names_loc") if isinstance(r.get("names_loc"), dict) else {}
        if r.get("lane") == "deep":
            # v948 — prefer names_new (session sticky); fall back to full names for old journals
            _reg_names = r.get("names_new") if isinstance(r.get("names_new"), list) and r.get("names_new") is not None else None
            if _reg_names is None:
                _reg_names = r.get("names") or []
            # always include moved (location change = newsworthy)
            if isinstance(r.get("names_moved"), list):
                for _m in r.get("names_moved") or []:
                    if _m not in _reg_names:
                        _reg_names = list(_reg_names) + [_m]
            for nm in (_reg_names or []):
                _consider(nm, ts, fid, nl.get(nm), None)
        if r.get("lane") == "kai":
            k = r.get("kai")
            j = k.get("judge") if isinstance(k, dict) else None
            if isinstance(j, dict):
                tier = str(j.get("tier") or "").lower()
                if tier in ("grail", "keep", "border"):
                    _consider(j.get("name"), ts, fid, nl.get(j.get("name")), tier)
            # FIX C (F3) — names the KAI closer GROUNDED from garbled tooltip OCR (a legible
            # grail whose read was leet-mangled, e.g. 'H4RLEQVIN CR' -> 'Harlequin Crest').
            # Already _kai_fullnames-verified by the grounder; tier stays None (a factual
            # sighting, not a judge quality verdict) so it registers without inventing a grade.
            if isinstance(k, dict) and isinstance(k.get("grounded"), list):
                for gm in k.get("grounded") or []:
                    _consider(gm, ts, fid, nl.get(gm), None)
    return sorted(reg.values(), key=lambda x: (x["firstSeenTs"] or 0, x["name"].lower()))


# ── v944/v944.1 🚦 THE KAI ROUTER
# Stage 1 — LABEL TABLE (evidence): per-frame votes + route intent + what actually fired.
# Stage 2 — QUORUM GATE (v944.1): sources that AGREE on the final label only count;
#           confidence = agreement count; <2 → no route (🟡); multi-brain disagreement
#           without a ≥2 winner → skipReason "disagreement".
# Stage 3 — lanes OBEY the ledger: funnel/judge fire only rows the ledger marked fireable.
def _kai_retro_promote_tally(routing_scan):
    """v948.7 — promote plain-stash film clusters to stash-runes|gems|materials.

    Pure: walks routing_scan (pre-quorum evidence rows), uses gridLabel/tabstripLabel
    majority vote over consecutive stash-ish frames. Theatre has the stills; this is
    the recheck before Stage-3 funnel. Does not invent tallies on pure gameplay."""
    if not routing_scan:
        return routing_scan
    # cluster consecutive non-gameplay stash-ish frames
    i = 0
    n = len(routing_scan)
    while i < n:
        s = routing_scan[i]
        lab = str(s.get("label") or "")
        if lab not in ("stash", "stash-runes", "stash-gems", "stash-materials") and not (
                s.get("gridLabel") or s.get("tabstripLabel")):
            i += 1
            continue
        j = i
        votes = {"runes": 0, "gems": 0, "materials": 0}
        while j < n:
            s2 = routing_scan[j]
            lab2 = str(s2.get("label") or "")
            gl = str(s2.get("gridLabel") or "")
            tl = str(s2.get("tabstripLabel") or "")
            if lab2 == "gameplay" and not gl and not tl:
                break
            if lab2 not in ("stash", "stash-runes", "stash-gems", "stash-materials",
                            "gameplay", "") and not gl.startswith("stash"):
                break
            for src in (gl, tl, lab2):
                if src in ("stash-runes", "stash-gems", "stash-materials"):
                    votes[src.split("-", 1)[1]] += 1
            j += 1
        # majority tally label in cluster
        best_tab, best_n = None, 0
        for t, c in votes.items():
            if c > best_n:
                best_tab, best_n = t, c
        if best_tab and best_n >= 2:
            prom = "stash-" + best_tab
            for k in range(i, j):
                s3 = routing_scan[k]
                gl3 = str(s3.get("gridLabel") or "")
                tl3 = str(s3.get("tabstripLabel") or "")
                # only rewrite frames that already look like stash or already that tally
                if str(s3.get("label") or "") in ("stash", prom, "gameplay") or gl3.startswith("stash") or tl3.startswith("stash"):
                    if str(s3.get("label") or "") in ("stash", "gameplay", ""):
                        s3["label"] = prom
                    # v1198 — do NOT synthesize grid=True/gridLabel here for a frame that has
                    # no gridLabel of its own. The old code stamped a fabricated "grid" vote
                    # onto every gridLabel-less frame in the cluster from the CLUSTER's
                    # majority tally — `_kai_build_routing`/`_router_conf` then counted that
                    # as a genuinely independent 'layout' witness (grid actually looked at
                    # THIS frame's pixels), when in truth no grid classifier ever touched it.
                    # A frame with its own single real vote (e.g. tabstrip alone) could then
                    # clear the 2-independent-class quorum on a borrowed, mislabeled witness —
                    # the same false-independence class the v1194 grid-vote fix closed one
                    # layer downstream. The label rewrite above already carries the cluster's
                    # majority context honestly (as the frame's display class); routing/gate
                    # correctness for THIS frame must still rest on its own real evidence —
                    # other frames in the cluster that DO have genuine 2-class evidence are
                    # what actually clears quorum for the tab (Stage 3 fires per-TAB, not
                    # per-frame, "newest frame wins").
        i = max(j, i + 1)
    return routing_scan


def _kai_stage3_gap_funnels(routing, sess_rows):
    """v948.7 — funnel jobs for tally tabs eyes labeled on the reel but Stage-3
    quorum never selected (or conf was 1). Photo on film = must recheck + SET intake.
    One best frame per unreceipted tab."""
    receipted = set()
    for r in sess_rows or []:
        ik = r.get("intake")
        if isinstance(ik, dict) and _intake_is_real(ik):
            t = str(ik.get("tab") or "").lower()
            if t in ("runes", "gems", "materials"):
                receipted.add(t)
    best = {}  # tab -> {tab,f,ts,conf}
    for r in routing or []:
        lab = str(r.get("label") or "")
        if not lab.startswith("stash-"):
            # also accept grid/tabstrip evidence even when final label stayed vault-stash
            for key in ("gridLabel", "tabstripLabel", "ocrLabel"):
                v = str(r.get(key) or "")
                if v.startswith("stash-") and v.split("-", 1)[-1] in ("runes", "gems", "materials"):
                    lab = v
                    break
            else:
                continue
        tab = lab.split("-", 1)[-1]
        if tab not in ("runes", "gems", "materials") or tab in receipted:
            continue
        conf = int(r.get("confidence") or 0)
        # accept conf>=1, or any frame with grid/tabstrip tally evidence
        has_eye = False
        for key in ("gridLabel", "tabstripLabel", "ocrLabel"):
            v = str(r.get(key) or "")
            if v == "stash-" + tab:
                has_eye = True
        if conf < 1 and not has_eye and lab != "stash-" + tab:
            continue
        if conf < 1 and lab == "stash-" + tab:
            conf = 1  # eye-labeled on scan
        prev = best.get(tab)
        ts = int(r.get("ts") or 0)
        if prev is None or conf > int(prev.get("conf") or 0) or (
                conf == int(prev.get("conf") or 0) and ts >= int(prev.get("ts") or 0)):
            best[tab] = {"tab": tab, "f": r.get("f"), "ts": ts, "route": "tally:" + tab,
                         "conf": conf, "gap": True}
    return list(best.values())


def _kai_stage3_select(routing):
    """v944.6/v946 Stage 3 pure selector — funnel / judge / vault lanes.

    Fireable contract (pre-receipt):
      • confidence >= 2 (Stage 2 quorum already cleared)
      • route set (tally:* | judge | vault)
      • not already routed
      • skipReason is the would-fire marker:
          tally gap  → "not-selected"
          judge slot → "cap"
          vault gap  → "not-selected" (v946; was no-vault-fire forever)
    Returns (funnel_jobs, judge_jobs, vault_jobs):
      funnel_jobs: one {tab,f,ts,route} per tally tab (newest frame wins)
      judge_jobs:  {f,ts} list in timestamp order (caller applies TV_KAI_JUDGE_MAX cap)
      vault_jobs:  one {f,ts,label} for newest inventory/stash vault candidate
    """
    funnel_by_tab = {}
    judges = []
    vault_best = None
    for r in routing or []:
        if int(r.get("confidence") or 0) < 2:
            continue
        if r.get("routed"):
            continue
        route = str(r.get("route") or "")
        skip = r.get("skipReason")
        if route.startswith("tally:") and skip == "not-selected":
            tab = route.split(":", 1)[1]
            prev = funnel_by_tab.get(tab)
            if prev is None or int(r.get("ts") or 0) >= int(prev.get("ts") or 0):
                funnel_by_tab[tab] = {"tab": tab, "f": r.get("f"), "ts": r.get("ts"),
                                      "route": route}
        elif route == "judge" and skip == "cap":
            judges.append({"f": r.get("f"), "ts": r.get("ts")})
        elif route == "vault" and skip in ("not-selected", "no-vault-fire"):
            # v946 — vault lane open (lease protects dual-fire). Newest conf≥2 panel wins.
            if vault_best is None or int(r.get("ts") or 0) >= int(vault_best.get("ts") or 0):
                vault_best = {"f": r.get("f"), "ts": r.get("ts"),
                              "label": r.get("label") or "stash"}
    judges.sort(key=lambda x: int(x.get("ts") or 0))
    return list(funnel_by_tab.values()), judges, ([vault_best] if vault_best else [])


_GATE_COUNT_CACHE = {"reel": None, "mtime": 0.0, "val": None}


def _newest_gate_count():
    """v948.12 — {proven, held} from the newest sealed reel's routing (accuracy-gate verdicts
    are post-seal). Cached by reel+mtime so /api/status polling never re-parses a hot report."""
    try:
        hist = HIST_DIR
        reels = sorted((d for d in os.listdir(hist)
                        if d.startswith("reel_") and os.path.isfile(os.path.join(hist, d, "kai_report.json"))),
                       reverse=True)
        if not reels:
            return None
        rp = os.path.join(hist, reels[0], "kai_report.json")
        mt = os.path.getmtime(rp)
        if _GATE_COUNT_CACHE["reel"] == reels[0] and _GATE_COUNT_CACHE["mtime"] == mt:
            return _GATE_COUNT_CACHE["val"]
        rt = (json.load(open(rp, encoding="utf-8")) or {}).get("routing") or []
        prov = sum(1 for r in rt if r.get("gatePass") is True)
        held = sum(1 for r in rt if r.get("gatePass") is False)
        val = {"proven": prov, "held": held} if (prov or held) else None
        _GATE_COUNT_CACHE.update(reel=reels[0], mtime=mt, val=val)
        return val
    except Exception:
        return None


def _session_health_from_rows(rows, leases=None, driver=None):
    """v946 — one-glance session truth for the console health strip.
    Pure: tabs (best real intake), leases, driver pulse, overall verdict."""
    tabs = {}
    story = []
    for r in rows or []:
        ik = r.get("intake") if isinstance(r.get("intake"), dict) else None
        if ik:
            tab = str(ik.get("tab") or ik.get("kind") or "").lower()
            if not tab:
                continue
            tot = int(ik.get("total") or 0)
            ok = bool(ik.get("ok", True)) and tot > 0
            cur = tabs.get(tab)
            if ok and (cur is None or tot >= int(cur.get("total") or 0)):
                tabs[tab] = {"status": "read", "total": tot, "ok": True}
            elif cur is None or not cur.get("ok"):
                tabs[tab] = {"status": "miss" if not ok else "read",
                             "total": tot if ok else 0, "ok": ok}
        if r.get("lane") == "deep" and (r.get("stashTab") or r.get("names")):
            st = str(r.get("stashTab") or "")
            nms = r.get("names") or []
            if st:
                story.append("visited " + st)
            elif nms:
                story.append("named " + ", ".join(str(x) for x in nms[:2]))
        if r.get("lane") == "kai" and isinstance(r.get("kai"), dict):
            k = r["kai"]
            if "missedFrames" in k:
                story.append("KAI closed · " + str(k.get("missedFrames") or 0) + " missed-text")
            if isinstance(k.get("register"), dict):
                story.append("register " + str(k["register"].get("count") or 0))
            if isinstance(k.get("judge"), dict) and k["judge"].get("name"):
                story.append("judge " + str(k["judge"].get("name"))[:28])
    # de-dupe story preserving order, keep last 8
    seen_s, uniq = set(), []
    for s in story:
        if s in seen_s:
            continue
        seen_s.add(s)
        uniq.append(s)
    uniq = uniq[-8:]
    misses = [t for t, v in tabs.items() if not v.get("ok")]
    reads = [t for t, v in tabs.items() if v.get("ok")]
    verdict = "ok"
    if misses and not reads:
        verdict = "miss"
    elif misses:
        verdict = "partial"
    elif not tabs:
        verdict = "idle"
    drv = driver or {}
    return {
        "tabs": tabs,
        "leases": leases or {},
        "refires": int(drv.get("refire") or drv.get("refires") or 0),
        "driverFired": int(drv.get("fired") or 0),
        "verdict": verdict,
        "story": uniq,
        "tabSummary": {t: ("×" + str(v["total"])) if v.get("ok") else "MISS"
                       for t, v in tabs.items()},
    }


def _kai_frame_sig(path):
    """v944 — cheap sampled-bytes fingerprint of a reel JPEG for routing dedupe (frame_sig-style).
    Returns (size, ~2k sampled bytes): the size is the fast first-pass key, the samples confirm
    identity. stdlib only, defensive (None on any error → that frame never dedupe-chains)."""
    try:
        sz = os.path.getsize(path)
        with open(path, "rb") as _f:
            data = _f.read()
        step = max(1, len(data) // 2048)
        return (sz, bytes(data[::step][:2048]))
    except Exception:
        return None


# v944.2 Stage 2 hardening — QUORUM SOURCE INDEPENDENCE. Confidence must count independent
# EVIDENCE CLASSES, not raw votes: 'read' (a deep read named an item on this frame) and 'judge'
# (a verdict on THAT SAME item) are one tooltip witnessed twice, not two brains agreeing. A
# tooltip read-then-judged is one 'content' signal; it clears the ≥2 gate only when a genuinely
# independent brain (pixel OCR / time-map journal) also lands on it.
# v947 — tabstrip (intake-style chrome OCR) + grid (pixel fingerprint) are independent
# of full-frame OCR and of journal time-map → conf≥2 without a deep read.
_ROUTER_INDEP_CLASS = {
    "ocr": "pixel",
    "journal": "time",
    "read": "content",
    "judge": "content",
    "tabstrip": "chrome",
    "grid": "layout",
}


def _router_conf(sources):
    """Independent-class confidence: distinct evidence classes among the agreeing brains."""
    return len({_ROUTER_INDEP_CLASS.get(b, b) for b in (sources or [])})


def _kai_route_for_label(label):
    """Which funnel WOULD take a frame with this label (route intent, not a fire)."""
    if label in ("stash-runes", "stash-gems", "stash-materials"):
        return "tally:" + label[len("stash-"):]
    if label == "tooltip":
        return "judge"
    if label in ("stash", "inventory"):
        return "vault"
    return None


def _kai_quorum_label(votes):
    """v944.1 Stage 2 — pick the final label from per-brain votes + who agrees.

    votes: dict brain → label (omit silent brains). Policy (stash screens are OCR-dark):
      1) journal stash-* / stash always wins when present (time-map is ground truth for panels)
      2) else majority vote among non-gameplay labels
      3) else any single non-gameplay vote
      4) else gameplay
    Returns (label, sources_list, skip_disagreement_or_None).
    sources_list = brains whose vote equals the chosen label (honest quorum).
    skip_disagreement = 'disagreement' when ≥2 distinct non-gameplay labels and no ≥2 winner.
    """
    # drop empties / normalize
    clean = {b: (lb or "gameplay") for b, lb in (votes or {}).items() if b and lb}
    if not clean:
        return "gameplay", [], None
    # 1) journal panel truth
    jv = clean.get("journal")
    if jv and jv != "gameplay" and (jv == "stash" or str(jv).startswith("stash-")):
        agree = sorted(b for b, lb in clean.items() if lb == jv)
        return jv, agree, None
    # tally non-gameplay votes
    from collections import Counter
    ng = {b: lb for b, lb in clean.items() if lb != "gameplay"}
    if not ng:
        agree = sorted(clean.keys())  # all said gameplay
        return "gameplay", agree, None
    counts = Counter(ng.values())
    top_label, top_n = counts.most_common(1)[0]
    # v1186 — a genuine TIE (2+ distinct labels sharing the top count, e.g. 2-vs-2 or 3-vs-3)
    # must ALSO be disagreement, not just a weak top_n<2. Counter.most_common only breaks ties
    # by first-seen insertion order — that's an iteration-order artifact, not evidence, and
    # was silently picking a winner between two EQUALLY-backed tally tabs (each side can even
    # clear independent-class quorum on its own) with no trace the other side ever voted.
    tied_leaders = sum(1 for n in counts.values() if n == top_n)
    # disagreement: 2+ distinct non-gameplay labels and no clean ≥2 winner (either the top
    # count itself is weak, or 2+ labels are tied for the top spot)
    if len(counts) >= 2 and (top_n < 2 or tied_leaders > 1):
        # no clean agreement — flag, keep top as display label, sources empty for gate
        return top_label, [], "disagreement"
    agree = sorted(b for b, lb in clean.items() if lb == top_label)
    return top_label, agree, None


# ── v949 🚦🛡 THE ACCURACY GATE (§3.5, ENGINE_ARCHITECTURE.md) — Konyo's law: "weed out
# bugs, incorrect reads, and inaccuracy of any kind" BEFORE a frame reaches a funnel cell.
# Sits between the router (_kai_build_routing's quorum/route) and the funnels (Stage 3
# fire loops). Three ordered checks a routing-ledger row must PASS; fail any → ping-pong
# (re-read a fresher/re-cropped frame) instead of routing garbage. Pure, zero I/O.
_GATE_CHROME_HARD = frozenset(("tabstrip", "grid", "ocr"))            # tab-strip word / panel chrome
_GATE_PANEL_HARD = frozenset(("tabstrip", "grid", "ocr", "journal"))  # vault panel: time-map ok too


def _kai_gate_name_hit(names, fullnames=None):
    """Gate check 1c — hardcoded DB-name membership (deterministic, zero AI cost). Garbage
    OCR ('IA Lla', 'Ii') matches no name in the ~1400-item DB harvested from bible.html and
    dies here. Reuses _kai_fullnames() — no second item list to maintain."""
    fn = fullnames if fullnames is not None else _kai_fullnames()
    for n in (names or []):
        if str(n or "").strip().lower() in fn:
            return True
    return False


def _kai_gate_check(label, sources, confidence, route, chrome_votes=None, name_hit=None,
                    grid_solo_ok=False):
    """THE ACCURACY GATE — three ordered checks a routing-ledger row must PASS before its
    funnel may fire:

      1) HARDCODED FILTER (deterministic, first, zero AI cost) — the label must have a
         matching hard signal. A tally tab (stash-runes/gems/materials) needs a tab-strip-word
         or panel-chrome witness (ocr/tabstrip/grid) — journal (time-map) ALONE never clears
         it; a sticky-tab guess with no visual confirmation is exactly the class that produced
         the vault-0 / materials false-positive bugs. A tooltip label needs its nearby
         read/judge name to be a real ~1400-item DB name (_kai_fullnames) whenever name
         evidence was supplied — garbage OCR matches no name and dies here.
      2) BRAIN QUORUM (AI, only if check 1 passes) — builds on the router's own math
         (_router_conf / _kai_quorum_label); RE-ASSERTS confidence>=2 rather than
         re-deriving it (disagreement already collapses confidence to 0, so it is caught
         here too, not duplicated as a separate branch).
         v1259 SANCTIONED GRID-SOLO EXCEPTION — a lone grid fingerprint is honestly ONE
         witness (_router_conf(['grid'])==1); it must NEVER fake a 2nd class (the phantom-ocr
         defect this fix removes upstream). But for a TALLY tab whose only real signal is the
         grid layout (the RotW 5-label tab strip is OCR-illegible, so grid legitimately IS the
         sole signal), an EXPLICITLY sanctioned single-signal route clears check 2 at conf 1 —
         gated behind its OWN tighter grid bar (grid_solo_ok: a definite gems/runes/materials
         pick on a panel-open dark-cell lattice, computed by the closer from gridDetail). True
         gems still route to tally:*; a false/low-confidence/uncorroborated grid read does not.
      3) CELL-CORRECTNESS — the route must be the ONE cell _kai_route_for_label says this
         label owns, AND no chrome-class brain (tabstrip/grid) may have voted a DIFFERENT
         label — a lone dissenting chrome witness vetoes the fire even when it lost the
         router's majority vote (the exact wrong-tab->wrong-cell class Konyo flagged).

    Pure. Returns {"pass": bool, "reason": str|None}; reason set on fail:
      'no-label' | 'no-hard-signal' | 'name-not-in-db' | 'quorum<2' | 'wrong-cell'."""
    if not label or label == "gameplay":
        return {"pass": False, "reason": "no-label"}
    src = set(sources or [])
    # ---- check 1: hardcoded filter ----
    if label.startswith("stash-") and label != "stash":
        if not (_GATE_CHROME_HARD & src):
            return {"pass": False, "reason": "no-hard-signal"}
    elif label in ("stash", "inventory"):
        if not (_GATE_PANEL_HARD & src):
            return {"pass": False, "reason": "no-hard-signal"}
    elif label == "tooltip":
        if name_hit is False:
            return {"pass": False, "reason": "name-not-in-db"}
    else:
        return {"pass": False, "reason": "no-hard-signal"}
    # ---- check 2: brain quorum (re-assert, don't duplicate the router) ----
    if int(confidence or 0) < 2:
        # v1259 SANCTIONED GRID-SOLO — grid is the ONLY witness (never a faked pair) AND the
        # closer's tighter grid bar cleared (grid_solo_ok) AND the label is a tally tab: an
        # honest one-detector, one-witness route. Anything else at conf<2 is held.
        if grid_solo_ok and src == {"grid"} and label in (
                "stash-runes", "stash-gems", "stash-materials"):
            pass  # sanctioned single-signal tally route — fall through to cell-correctness
        else:
            return {"pass": False, "reason": "quorum<2"}
    # ---- check 3: cell-correctness ----
    want = _kai_route_for_label(label)
    if not want or route != want:
        return {"pass": False, "reason": "wrong-cell"}
    for _b, _lb in (chrome_votes or {}).items():
        if _lb and _lb != label:
            return {"pass": False, "reason": "wrong-cell"}
    return {"pass": True, "reason": None}


def _kai_gate_pingpong(tries, gate_passed, max_tries=3):
    """THE ACCURACY GATE's ping-pong — bounded re-read decision for a gate-failed frame.
    Deliberately mirrors _drv_empty_refire_plan's tries/max_tries contract (the SAME
    never-zero shape, generalized to gate failures instead of empty intakes): on fail,
    re-read a fresher frame up to max_tries; beyond that, record an HONEST MISS rather
    than ever routing a guess. Pure. Returns ('done', None) | ('pingpong', next_tries) |
    ('honest-miss', None)."""
    if gate_passed:
        return ("done", None)
    tries = int(tries or 0) + 1
    if tries < max_tries:
        return ("pingpong", tries)
    return ("honest-miss", None)


def _kai_gate_pingpong_plan(routing, tries_state, max_tries=3):
    """v948.13 — wires _kai_gate_pingpong into a routing ledger pass. Conservative by
    design: only JUDGE-route rows the gate HELD (skipReason 'gate:<reason>') are eligible.
    A fresh aicJudge call is a genuinely independent second brain (the gate's own check 2
    demands ≥2 independent evidence classes), unlike a tally/vault re-fire which risks
    double-counting inventory already on the board — those stay out of scope here.

    tries_state: {f: tries} persisted across closer passes (the reel's gate_pingpong.json).
    A row already at/above max_tries (from a prior pass) is treated as already pinned and
    is re-confirmed as such, not retried again — the never-zero doctrine's honest-miss,
    made permanent.

    Pure. Returns (retry_rows, pinned_fs, new_tries_state):
      retry_rows      — routing rows to re-queue for one more judge read this pass
      pinned_fs       — frame names whose tries just maxed out (or already had) — honest
                        miss, never retried again
      new_tries_state — tries_state with this pass's increments folded in (persist this)."""
    retry, pinned = [], []
    new_tries = dict(tries_state or {})
    for r in (routing or []):
        f = r.get("f")
        if not f or r.get("route") != "judge":
            continue
        if not str(r.get("skipReason") or "").startswith("gate:"):
            continue
        act, nxt = _kai_gate_pingpong(int(new_tries.get(f, 0)), False, max_tries=max_tries)
        if act == "pingpong":
            new_tries[f] = nxt
            retry.append(r)
        else:   # honest-miss — pin: tries maxed, never retried again
            new_tries[f] = max_tries
            pinned.append(f)
    return retry, pinned, new_tries


def _kai_build_routing(scan, sess_rows, sid, journal_rows):
    """v944/v944.1/v949 — THE ROUTING LEDGER. One row per scanned frame:
    {f, ts, label, sources, confidence, route, routed, skipReason, gatePass, gateReason,
    gateSources}.

    sources = brains whose VOTE equals the final label (Stage 2 honest quorum), not merely
    'any evidence on the frame'. Brains:
      'ocr'     OCR classed the frame (non-gameplay cls),
      'journal' stash time-map placed the frame on an open tab,
      'read'    a deep read named an item within ±4s → votes tooltip,
      'judge'   a judge verdict landed on this frame → votes tooltip.

    confidence = len(sources). Stage 2 gate: confidence < 2 → no fire intent (skip confidence<2
    or disagreement). route = funnel that WOULD take it; routed = what actually fired (receipts).

    v949 — THE ACCURACY GATE (§3.5) rides the same pass: gatePass/gateReason/gateSources are
    the per-frame verdict from _kai_gate_check (auditable — the theatre can show WHY a frame
    was held). A row that would otherwise fire (skipReason in not-selected/no-gap/cap) but
    fails the gate gets its skipReason rewritten to 'gate:<reason>' and route cleared — Stage 3
    (_kai_stage3_select) already only selects not-selected/cap rows, so a gate-failed row is
    automatically excluded from firing with NO change needed to Stage 3 itself. Frames that
    fail purely on router-side quorum (quorum<2/no-label) are left as the router already
    marked them — the gate only ADDS a veto, it never overrides a already-informative skip.
    Pure — no side effects."""
    read_ts = [int(r.get("captureTs") or r.get("ts") or 0)
               for r in sess_rows
               if r.get("lane") == "deep" and (r.get("names") or [])]
    # v949 — same deep-read rows, but keeping the NAMES (not just ts) so the gate can check
    # a nearby tooltip read's item name against the DB (_kai_gate_name_hit).
    read_names_ts = []
    for r in sess_rows:
        if r.get("lane") == "deep":
            _nms = r.get("names") or []
            if _nms:
                _rt = int(r.get("captureTs") or r.get("ts") or 0)
                for _nm in _nms:
                    read_names_ts.append((_rt, _nm))
    receipted = set()   # tabs that receipted normally this session (tally route + receipt = no gap)
    for r in sess_rows:
        ik = r.get("intake")
        # v944.6 — only a REAL (ok + total>0) tally counts; empty 0-shots must not seal the gap
        if isinstance(ik, dict) and _intake_is_real(ik):
            t = str(ik.get("tab") or "").lower()
            if t:
                receipted.add(t)
    funnel_by_fid = {}   # reel frameId -> intake kind the funnel wrote
    judge_fids = set()   # reel frameIds a judge verdict landed on
    judge_name_by_fid = {}   # v949 — the judged item's name, for the gate's DB check
    for r in journal_rows:
        fid = str(r.get("frameId") or "")
        if not fid:
            continue
        ik = r.get("intake")
        # v1197 — `routed` means "a REAL funnel receipt landed for this frame", not merely
        # "a funnel attempt happened". The Stage-3 kai-funnel fire (control_app.py ~4045/4053,
        # the v1185 honest-miss-on-rejection fix + the pre-existing guardHeld block) can and
        # DOES land an ok:false receipt (a genuine rejection, or the never-zero guard holding)
        # for kind:'kai-funnel' — that's the whole point of posting it (an honest miss, not a
        # silent drop). But this loop used to mark `funnel_by_fid[fid]` on ANY kai-funnel
        # receipt regardless of `ok`, so a FAILED attempt still made `routed` truthy for that
        # frame. Two knock-on effects: (1) _kai_reconcile's stash-* narration then claimed
        # "funnel receipt landed ... its tally count is the accepted read" for a read that
        # never actually applied — an honest ok:false receipt getting reinterpreted as a
        # success one layer up; (2) _kai_stage3_select's `if r.get("routed"): continue` row
        # dedup permanently skipped re-selecting that exact frame, even though nothing real
        # ever landed on it. Gate on ok so only a genuine success marks the frame routed.
        if isinstance(ik, dict) and str(ik.get("kind") or "") == "kai-funnel" and ik.get("ok"):
            funnel_by_fid[fid] = "kai-funnel"
        if r.get("lane") == "kai" and r.get("mode") == "kai-judge":
            judge_fids.add(fid)
            try:
                _jn = ((r.get("kai") or {}).get("judge") or {}).get("name")
            except Exception:
                _jn = None
            if _jn:
                judge_name_by_fid[fid] = _jn
    out = []
    _prev_sig = None
    _run_first = None   # the f that opened the current visual run
    # v944.6 — label+time near-dup window (routing-only). Same label within N ms of the
    # cluster head collapses to one logical event; film/ledger rows stay intact.
    _NEAR_DUP_MS = 3000
    _label_last = {}    # label -> (ts, f) of the cluster head
    for s in scan:
        f = str(s.get("f") or "")
        ts = int(s.get("ts") or 0)
        fid = ("reel_" + sid + "/" + f.replace(".jpg", "")) if f else ""
        # ── per-brain VOTES (Stage 2 + v947 intake-mimic eyes) ──
        votes = {}
        ocr_lb = s.get("ocrLabel") or (s.get("label") if s.get("ocr") else None)
        if s.get("ocr") and ocr_lb and ocr_lb != "gameplay":
            votes["ocr"] = ocr_lb
        j_lb = s.get("journalLabel")
        gr_lb = s.get("gridLabel")
        ts_lb = s.get("tabstripLabel")
        # v948.7 — vault sticky (plain "stash") must NOT veto tally grid/tabstrip votes.
        # Live deep often only named personal/shared; film still shows gems/materials later.
        if s.get("journal"):
            _jl = j_lb or s.get("label") or "stash"
            _tally_eye = (str(gr_lb or "").startswith("stash-") and str(gr_lb) != "stash") or (
                str(ts_lb or "").startswith("stash-") and str(ts_lb) != "stash")
            if _jl in ("stash", "inventory", "gameplay") and _tally_eye:
                pass  # skip weak journal vote
            else:
                votes["journal"] = _jl
        # v947 — tabstrip (upscaled chrome OCR) + grid fingerprint (intake crop layout)
        if s.get("tabstrip") and ts_lb and ts_lb != "gameplay":
            votes["tabstrip"] = ts_lb
        if s.get("grid") and gr_lb and gr_lb != "gameplay":
            votes["grid"] = gr_lb
        if any(abs(rt - ts) <= 4000 for rt in read_ts):
            votes["read"] = "tooltip"   # a named deep read near this frame ⇒ item floating
        judged = fid in judge_fids
        if judged:
            votes["judge"] = "tooltip"
        # legacy scan rows without ocrLabel/journalLabel still work via booleans + label
        if not votes and (s.get("ocr") or s.get("journal")):
            if s.get("ocr"):
                votes["ocr"] = s.get("label") or "gameplay"
            if s.get("journal"):
                votes["journal"] = s.get("label") or "stash"
        label, sources, disagree = _kai_quorum_label(votes)
        # v947 — when quorum is weak but intake-mimic eyes agree on a tally tab, promote display
        if (not label or label == "gameplay" or label == "stash") and ts_lb and gr_lb and ts_lb == gr_lb:
            if str(ts_lb).startswith("stash-"):
                # v1180 gate fix — the OLD sources belonged to the label being overridden
                # (gameplay/stash); blindly unioning them into the promoted label's sources
                # falsely counted a DISSENTING brain (e.g. ocr that actually voted "gameplay")
                # as agreeing with "stash-runes", inflating confidence/gateSources with a
                # contradiction. Only keep a prior brain here if it actually voted ts_lb.
                agree = {b for b, lb in votes.items() if lb == ts_lb}
                label, sources, disagree = ts_lb, sorted(agree | {"tabstrip", "grid"}), None
        conf = _router_conf(sources)   # v944.2 — independent evidence classes, not raw votes
        route = _kai_route_for_label(label)
        routed = funnel_by_fid.get(fid) or ("kai-judge" if judged else None)
        skip = None
        # Stage 2 gate — no fire intent without quorum (even if a receipt already exists,
        # skipReason stays null when routed is set; the gate applies to would-fire path)
        if routed is None:
            if disagree:
                skip = "disagreement"
                route = None   # do not advertise a route when brains fight
            elif conf < 2:
                skip = "confidence<2"
                # keep route for drilldown (what WOULD fire if a second brain agreed)
            elif route is None:
                skip = "no-route"
            elif route.startswith("tally:"):
                skip = "no-gap" if route.split(":", 1)[1] in receipted else "not-selected"
            elif route == "judge":
                skip = "cap"
            elif route == "vault":
                # v946 — vault is a real Stage-3 lane (was forever no-vault-fire).
                # "not-selected" = fireable; legacy reports may still say no-vault-fire.
                skip = "not-selected"
            else:
                skip = "no-route"
        # v949 🚦🛡 THE ACCURACY GATE — re-verify a would-fire row before it's allowed to
        # advertise a route. Only vetoes rows the router itself judged fireable this pass
        # (not-selected/no-gap/cap); a router-side quorum/label failure is left as the
        # router already marked it (no double-messaging the same failure).
        chrome_votes = {b: lb for b, lb in votes.items() if b in ("tabstrip", "grid")}
        name_hit = None
        if label == "tooltip":
            _pool = [nm for (rt, nm) in read_names_ts if abs(rt - ts) <= 4000]
            _jn = judge_name_by_fid.get(fid)
            if _jn:
                _pool = _pool + [_jn]
            if _pool:
                name_hit = _kai_gate_name_hit(_pool)
        # v1259 — sanctioned grid-solo: the closer flags a frame `gridSolo` only when grid
        # alone (no OCR/journal) made a DEFINITE tally pick on a panel-open dark-cell lattice
        # (its own tighter grid bar). Honored by the gate ONLY when grid really is the sole
        # agreeing witness for this label — never a shortcut around a genuine 2-witness quorum.
        grid_solo_ok = bool(s.get("gridSolo")) and sources == ["grid"]
        gate = _kai_gate_check(label, sources, conf, route,
                                chrome_votes=chrome_votes, name_hit=name_hit,
                                grid_solo_ok=grid_solo_ok)
        if routed is None and skip in ("not-selected", "no-gap", "cap") and not gate["pass"] \
                and gate["reason"] not in ("quorum<2", "no-label"):
            skip = "gate:" + gate["reason"]
            route = None
        # v944 DEDUPE LAW (routing-only, Konyo explicit) — consecutive frames with an identical
        # cheap signature are a visual run: the FIRST keeps its label+route, each later duplicate
        # keeps its label but is un-routed with a chain ref. The reel/film is NEVER trimmed —
        # every frame stays in the ledger, so the replay is complete.
        # v1189 — guarded by `routed is None` (mirrors the near-dup branch below, v944.6):
        # `routed` is a HISTORICAL FACT (a funnel/judge receipt already landed on THIS
        # frame's own fid), not a routing decision — nulling it unconditionally erased a
        # real receipt whenever the receipted frame happened to be pixel-identical to its
        # predecessor (e.g. Stage 3's "newest frame wins" firing against the LAST frame of a
        # static-panel run). That made _kai_reconcile (and any 'routed' count/audit) report a
        # false 'miss' for a frame that genuinely fired.
        _sig = s.get("sig")
        _is_dup = _sig is not None and _sig == _prev_sig
        if _is_dup and routed is None:
            route = None
            skip = "dup-of:" + (_run_first or "")
        else:
            _run_first = f
            # v944.6 label+time near-dup (Claude deferred this from pixel fuzzy): same non-gameplay
            # label within _NEAR_DUP_MS of the cluster head → one logical event. Exact-sig dups
            # already handled above; this catches near-identical stash-sitting frames whose JPEG
            # bytes diverge (cursor/glow) but are the same panel moment. Film never trimmed.
            if label and label != "gameplay":
                _prev_lt = _label_last.get(label)
                if _prev_lt and 0 <= (ts - _prev_lt[0]) <= _NEAR_DUP_MS:
                    if routed is None:
                        route = None
                        skip = "near-dup-of:" + (_prev_lt[1] or "")
                    # keep cluster head — don't advance last
                else:
                    _label_last[label] = (ts, f)
        _prev_sig = _sig
        out.append({"f": f, "ts": ts, "label": label, "sources": sources,
                    "confidence": conf, "voteCount": len(sources), "route": route,
                    "routed": routed, "skipReason": skip,
                    "gatePass": gate["pass"], "gateReason": gate["reason"],
                    "gateSources": sorted(set(sources) | set(chrome_votes.keys()))})
    return out


# ── v949.x 🧠🔬 SUPER-ANALYZE KAI — Phase B, THE 4TH ORGAN (ENGINE_ARCHITECTURE.md "MASTER
# BRAIN" layer 4; ARCH_PINGPONG §Q1-hybrid). The closer's OCR sweep + gate only PROVES a frame
# is real tooltip/item content; it never independently re-reads it. A fast-hovered item whose
# live read AND OCR both garbled ("IA Lla") stays unread forever under the old pipeline — this
# is the deep retro pass that closes that gap: every gate-PROVEN frame the session never named
# a real DB item on gets ONE bounded, independent aicJudge re-read of the archived film still.
# Pure selection (no I/O); the firing/waiting loop lives in _kai_closer_loop.
def _kai_super_already_named(sess_rows, ts, fullnames=None, window_ms=4000):
    """True if a nearby (±window_ms) deep read or kai-judge verdict already named a REAL
    DB item (_kai_fullnames) around this frame's ts — i.e. this frame's content is already
    registered and does NOT need a super-analyze re-read. Pure. Mirrors the ±4000ms window
    _kai_build_routing already uses to associate a read/judge with a tooltip frame."""
    fn = fullnames if fullnames is not None else _kai_fullnames()
    try:
        ts = int(ts or 0)
    except Exception:
        return False
    w = max(0, int(window_ms or 0))
    for r in sess_rows or []:
        try:
            rt = int(r.get("captureTs") or r.get("ts") or 0)
        except Exception:
            continue
        if not rt or abs(rt - ts) > w:
            continue
        if r.get("lane") == "deep":
            for nm in (r.get("names") or []):
                if str(nm or "").strip().lower() in fn:
                    return True
        if r.get("lane") == "kai" and isinstance(r.get("kai"), dict):
            j = r["kai"].get("judge")
            if isinstance(j, dict) and str(j.get("tier") or "").lower() in ("grail", "keep", "border"):
                nm = str(j.get("name") or "").strip().lower()
                if nm and nm in fn:
                    return True
    return False


def _kai_super_select(routing, sess_rows, fullnames=None, cap=None):
    """THE SUPER-ANALYZE SELECTOR — pure. Picks which gate-proven frames earn a full,
    independent deep re-read this pass.

    Eligible: gatePass is True (the accuracy gate already weeded the garbage — LAW: never
    re-reads a frame the gate didn't prove), label is 'tooltip' or a 'stash-*' tally panel
    (an item/text frame — never gameplay/boot), and _kai_super_already_named says NO real
    DB item is already registered near this frame (no wasted calls on already-solved reads).

    Highest-value first: 'tooltip' frames (direct item-name text) before 'stash-*' panels,
    then by router confidence descending (more independent brains already agreeing on SOMETHING
    on this frame is a stronger signal there's real recoverable text), then chronological.

    CAP: env TV_KAI_SUPER_MAX (default 10, the 8-12 budget) — a hard ceiling per reel so this
    organ can never run away. Returns the capped, ordered candidate routing rows."""
    fn = fullnames if fullnames is not None else _kai_fullnames()
    if cap is None:
        try:
            cap = max(0, int(os.environ.get("TV_KAI_SUPER_MAX", "10")))
        except Exception:
            cap = 10
    cands = []
    for r in routing or []:
        if r.get("gatePass") is not True:
            continue
        f = r.get("f")
        if not f:
            continue
        label = str(r.get("label") or "")
        if label != "tooltip" and not label.startswith("stash-"):
            continue
        ts = int(r.get("ts") or 0)
        if _kai_super_already_named(sess_rows, ts, fn):
            continue
        cands.append(r)
    cands.sort(key=lambda r: (0 if r.get("label") == "tooltip" else 1,
                               -int(r.get("confidence") or 0),
                               int(r.get("ts") or 0)))
    return cands[:cap]


# ═══════════════════════════════════════════════════════════════════════════════════
# v949.x 🥷🧠 THE MASTER-BRAIN RECONCILER — Phase C (ENGINE_ARCHITECTURE.md "MASTER BRAIN
# KAI"; ARCH_PINGPONG_NINJA_ENGINE_ROOM.md §4 + §6-Q2 SETTLED). ONE pure fn, ZERO new
# threads (Q2 was explicit: a 3rd always-on thread would revive the race the
# _agent_mode/_agent_alive() gate killed at v937.3). Called from the TWO threads that
# already exist: _kai_closer_loop (authoritative, post-seal — see _kai_build_engine_frames
# below) and _engine_driver (provisional live guess — see _kai_live_routing_row / the
# _ENGINE_FRAMES_LIVE deque near the bottom of _engine_driver's 2s loop).
# ═══════════════════════════════════════════════════════════════════════════════════
def _kai_reconcile(routing, register, sess_rows):
    """THE reconciler — pure, no I/O, no threads. For each routing row (one per scanned
    frame) decides the OWNER — which layer's read is the ACCEPTED truth for that
    frame/item — and the VERDICT, in priority order (Q4 §4, Konyo's settled ranking):

        super-analyze deep-read  >  live named  >  kai-retro named  >  OCR-only

    A deliberate, unhurried re-read (super) outranks a time-pressured live pass; a
    DB-verified name always outranks a bare label with no name behind it. Every accepted
    read carries WHICH layer owned it + WHY (`why`) — the audit trail the Engine Room
    cockpit renders (ARCH_PINGPONG §2's `owner` field).

    DB-verification: `register` (from _kai_compile_register) is ALREADY _kai_fullnames-
    filtered + anchor/junk-stripped, so its name set doubles as "names this session proved
    real" without a second DB lookup here (keeps this fn to its 3 given args — no vocab
    I/O). When `register` is non-empty it gates live-read names (only a DB-verified nearby
    name counts as 'live named'). When `register` is EMPTY — the _engine_driver provisional
    live call, which has no time to compile a register every 2s — verification is skipped
    and a raw deep-read name is trusted as a live GUESS (explicitly provisional; the
    sealed pass below always re-runs this with a real register and a real routing/gate
    pass, and per the settled law that sealed pass always wins — see
    _kai_engine_frame_effective). This is the one place 'confidence' folds into priority:
    within the live layer, a DB-verified name (register present) is preferred outright over
    an unverified guess (register absent) simply by which mode is calling.

    LAW (never let a captured item die unread, ARCH_PINGPONG §4/§1): a 'tooltip' frame with
    no owning layer is an honest MISS, not a silent drop — flagged so the super-analyze
    organ's own independent selection (_kai_super_select) has a matching account of the
    same gap. LAW (never let a thin funnel clobber a good tally, v948.18 generalized): for
    'stash-*' tally-panel frames this fn does NOT invent a competing count — a landed
    funnel receipt (`routed`) is simply reported as the owner; the max-verified-total logic
    stays where it already lives (Stage 3 / the funnels), this fn only narrates it.

    Returns one dict per routing row: {f, ts, owner, verdict, why, scene, tab, area}.
    v1253 R1 (DIABLO-LANGUAGE) — scene/tab/area are ADDITIVE: the read's TRUE Diablo scene
    (town|stash|inventory|loot|gameplay|transition), its stashTab, and its area, carried
    through faithfully from the nearest deep read (±4s) so a portal/loading frame surfaces
    as scene='transition' (NOT collapsed to 'gameplay / near black screen') and a stash
    frame keeps scene='stash' + tab=<its read tab>. This NEVER changes owner/verdict/why —
    it only threads the already-produced scene out to the session summary + retro. Honest:
    no nearby read produced a scene ⇒ scene/tab/area stay None (never invented).
    owner  ∈ {'super','live','kai','ocr', None}
    verdict ∈ {'grail','keep','border','toss', None, 'miss'} — None means "a name landed
              but no judge tier has scored it yet" (a real, non-miss state); 'miss' means
              nothing named it at all; verdict is always None for non-item frames (labels
              other than 'tooltip'/'stash-*') since keep/toss quality judgments don't apply
              to gameplay/boot frames or (by design, see above) to tally-panel counts."""
    known_names = {str(e.get("name") or "").strip().lower() for e in (register or []) if e.get("name")}
    reg_tier_by_name = {str(e.get("name") or "").strip().lower(): str(e.get("tier") or "").lower()
                         for e in (register or []) if e.get("name") and e.get("tier")}
    verify_db = bool(known_names)   # sealed pass (real register) verifies; live guess doesn't

    # index sess_rows ONCE — live deep-read names by ts, judge verdicts by frame filename
    # suffix. Routing rows only carry the bare filename 'f' (not the full reel_<sid>/<f>
    # frameId) — matching on frameId's SUFFIX sidesteps needing sid as a 4th arg here.
    deep_names_ts = []
    for r in sess_rows or []:
        if r.get("lane") != "deep":
            continue
        names = [str(n) for n in (r.get("names") or []) if str(n or "").strip()]
        if not names:
            continue
        rt = int(r.get("captureTs") or r.get("ts") or 0)
        if rt:
            deep_names_ts.append((rt, names))

    judge_by_fsuffix = {}
    for r in sess_rows or []:
        if r.get("lane") != "kai" or r.get("mode") != "kai-judge":
            continue
        fid = str(r.get("frameId") or "")
        suf = fid.rsplit("/", 1)[-1] if fid else ""
        if not suf:
            continue
        j = (r.get("kai") or {}).get("judge") or {}
        # last-landed wins — a re-judge (rare, e.g. a priority reclose) is the freshest
        # verdict for this frame.
        judge_by_fsuffix[suf] = {
            "name": str(j.get("name") or "").strip(),
            "tier": (str(j.get("tier") or "").lower() or None),
            "live": bool(j.get("live")),
            "tag": j.get("tag"),
        }

    _WIN = 4000   # ±4s tooltip-association window — mirrors _kai_build_routing/_kai_super_already_named

    # v1253 R1 (DIABLO-LANGUAGE) — index EVERY deep read that produced a scene, names or
    # not. `deep_names_ts` above deliberately drops name-less reads, but a portal/loading
    # frame reads scene='transition' with EMPTY names — that is exactly the frame that was
    # collapsing to "gameplay / near black screen". Carry the read's own scene/tab/area onto
    # each routing row (nearest read within ±_WIN) so downstream renders the true Diablo
    # scene. ADDITIVE + honest: tab-detection ACCURACY (the read that misnames the tab) is a
    # later round's job — R1 only transports whatever the read faithfully said.
    deep_scene_ts = []
    for r in sess_rows or []:
        if r.get("lane") != "deep":
            continue
        sc = str(r.get("scene") or "").strip().lower()
        tb = str(r.get("stashTab") or "").strip().lower()
        ar = str(r.get("area") or "").strip()
        if not (sc or tb or ar):
            continue
        rt = int(r.get("captureTs") or r.get("ts") or 0)
        if rt:
            deep_scene_ts.append((rt, sc, tb, ar))

    def _nearest_scene(ts):
        best, best_d = None, _WIN + 1
        for rt, sc, tb, ar in deep_scene_ts:
            d = abs(rt - ts)
            if d <= _WIN and d < best_d:
                best, best_d = (sc, tb, ar), d
        return best

    out = []
    for row in routing or []:
        f = str(row.get("f") or "")
        ts = int(row.get("ts") or 0)
        label = str(row.get("label") or "")
        owner, verdict, why = None, None, "not an item/tally frame (label=" + (label or "gameplay") + ")"

        if label == "tooltip":
            suf = f.replace(".jpg", "") if f else ""
            jinfo = judge_by_fsuffix.get(suf)
            sup = row.get("super") if isinstance(row.get("super"), dict) else None
            sup_names = [n for n in (sup.get("deepNames") or []) if n] if sup else []

            live_names = []
            for rt, names in deep_names_ts:
                if abs(rt - ts) <= _WIN:
                    for nm in names:
                        if not verify_db or nm.strip().lower() in known_names:
                            live_names.append(nm)
            live_judge = jinfo if (jinfo and jinfo.get("live")) else None
            kai_judge = jinfo if (jinfo and not jinfo.get("live") and jinfo.get("tag") != "super"
                                   and jinfo.get("name")) else None

            if sup_names:
                nm = sup_names[0]
                owner = "super"
                verdict = sup.get("tier") or reg_tier_by_name.get(nm.strip().lower())
                why = ("super-analyze deep re-read named '%s' — a deliberate, unhurried "
                       "re-read outranks a time-pressured live pass" % nm)
            elif live_names or live_judge:
                nm = live_names[0] if live_names else live_judge.get("name")
                owner = "live"
                verdict = ((live_judge or {}).get("tier")) or reg_tier_by_name.get((nm or "").strip().lower())
                why = "live eye named '%s' in real time (first pass)" % (nm or "?")
            elif kai_judge:
                nm = kai_judge.get("name")
                owner = "kai"
                verdict = kai_judge.get("tier") or reg_tier_by_name.get((nm or "").strip().lower())
                why = ("kai-retro OCR sweep + judge named '%s' post-seal "
                       "(live and second eye missed it)" % nm)
            else:
                owner = "ocr" if row.get("sources") else None
                verdict = "miss"
                why = ("tooltip frame seen but no reader landed a DB-verified name — "
                       "never-zero law: a candidate for the next super-analyze pass")
        elif label.startswith("stash-"):
            if row.get("routed"):
                owner = "funnel"
                why = "funnel receipt landed for %s — its tally count is the accepted read" % row.get("routed")
            elif row.get("sources"):
                owner = "ocr"
                verdict = "miss"
                why = "tab/tally evidence seen but no funnel receipt has landed yet"
            else:
                owner = None
                verdict = "miss"
                why = "tally panel frame with no reader evidence and no receipt — never-zero: re-fire, not a zero"

        _sc = _nearest_scene(ts)
        out.append({"f": f, "ts": ts, "owner": owner, "verdict": verdict, "why": why,
                    "scene": (_sc[0] or None) if _sc else None,
                    "tab": (_sc[1] or None) if _sc else None,
                    "area": (_sc[2] or None) if _sc else None})
    return out


def _kai_engine_frame_effective(sealed_engine_frames, live_ring, kai_ver=None):
    """Pure. THE SEALED-WINS LAW (ARCH_PINGPONG §6-Q2, settled): 'Sealed owner (kaiVer≥3)
    ALWAYS wins over the live provisional guess.' A reel's sealed engineFrames (materialized
    at seal by _kai_build_engine_frames, kaiVer>=3) are authoritative for every frame they
    cover; the live provisional deque (_engine_driver's guess, pre-seal) never overrides a
    sealed frame — it only fills in frames the seal hasn't covered yet (a session still on
    air with no kai_report yet, or one below kaiVer 3). Every returned row carries an honest
    `sealed` bool so a reader (the future Engine Room) never confuses a guess for a fact."""
    if kai_ver is not None and int(kai_ver) < 3:
        sealed_engine_frames = []
    sealed_fs = {row.get("f") for row in (sealed_engine_frames or [])}
    merged = [dict(row, sealed=True) for row in (sealed_engine_frames or [])]
    for row in (live_ring or []):
        if row.get("f") in sealed_fs:
            continue
        merged.append(dict(row, sealed=False))
    return merged


def _kai_engine_frame_maps(routing, register, sess_rows):
    """Pure. Builds the small per-frame aux indices _kai_build_engine_frames needs beyond
    routing/register/super_reads themselves: the owner/verdict decision from _kai_reconcile
    (called here ONCE so the seal-time materializer and any other caller share the exact
    same reconciliation logic — never a second decision tree), plus nearest-ts lookups into
    the live/second/kai layers (deep reads, second-eye verify rows, kai-missed-text + judge
    rows) keyed by routing row 'f'. Window = 4000ms, mirroring the ±4s tooltip-association
    window _kai_build_routing/_kai_super_already_named already use."""
    _WIN = 4000
    rec_by_f = {r["f"]: r for r in _kai_reconcile(routing, register, sess_rows) if r.get("f")}

    deep_pts, verify_pts, kai_pts = [], [], []
    for r in sess_rows or []:
        rt = int(r.get("captureTs") or r.get("ts") or 0)
        if not rt:
            continue
        if r.get("lane") == "deep" and (r.get("names") or []):
            deep_pts.append((rt, [str(n) for n in r.get("names") or []]))
        elif r.get("lane") == "verify" and isinstance(r.get("verify"), dict):
            v = r["verify"]
            verify_pts.append((rt, {
                "conf": v.get("conf"),
                "confirmNames": list(v.get("confirm") or [])[:6],
                "correctedNames": list(v.get("not_present") or [])[:6],
                "missedNames": list(v.get("missed") or [])[:6],
            }))
        elif r.get("lane") == "kai" and isinstance(r.get("kai"), dict) and r["kai"].get("texts"):
            kai_pts.append((rt, list(r["kai"].get("texts") or [])[:6]))

    judge_by_fsuffix = {}
    for r in sess_rows or []:
        if r.get("lane") == "kai" and r.get("mode") == "kai-judge":
            fid = str(r.get("frameId") or "")
            suf = fid.rsplit("/", 1)[-1] if fid else ""
            if suf:
                j = (r.get("kai") or {}).get("judge") or {}
                judge_by_fsuffix[suf] = {"name": j.get("name"), "tier": j.get("tier")}

    def _nearest(ts, pts):
        best, best_d = None, _WIN + 1
        for rt, val in pts:
            d = abs(rt - ts)
            if d <= _WIN and d < best_d:
                best, best_d = val, d
        return best

    live_by_f, second_by_f, kai_by_f = {}, {}, {}
    for row in routing or []:
        f = row.get("f")
        if not f:
            continue
        ts = int(row.get("ts") or 0)
        names = _nearest(ts, deep_pts)
        if names:
            live_by_f[f] = {"names": names}
        v = _nearest(ts, verify_pts)
        if v:
            second_by_f[f] = v
        texts = _nearest(ts, kai_pts)
        j = judge_by_fsuffix.get(str(f).replace(".jpg", ""))
        if texts or j:
            kai_by_f[f] = {"missedTexts": texts or [],
                            "judgeName": (j or {}).get("name"),
                            "judgeTier": (j or {}).get("tier")}

    return {"reconcile": rec_by_f, "live": live_by_f, "second": second_by_f, "kai": kai_by_f}


def _kai_build_engine_frames(routing, register, super_reads, maps):
    """v949.x — Q1-HYBRID materialization (ARCH_PINGPONG §2 / §6-Q1, SETTLED): the
    *semantic* reconciliation (owner/verdict/per-layer) is written into kai_report.json AT
    SEAL, beside routing/register — presentation strings + the live cursor stay derived
    on-read (the Engine Room cockpit renders them; this never precomputes HTML/labels).

    One EngineFrame per routing row — layers{live,second,kai,super,router,gate,funnel} +
    owner + verdict + why, per the data model in ARCH_PINGPONG §2. `super_reads` is the
    closer's own per-frame super-analyze record ({f: {reread, deepNames, tier}}, i.e.
    `_super_recovered`) — read directly here (falling back to routing row `.super` when a
    frame is missing from it) so a frame keeps its super layer even if the stamp step were
    ever skipped (additive/defensive, the gate/HD-art light-up pattern). `maps` is
    _kai_engine_frame_maps(routing, register, sess_rows)'s output — kept as a separate
    argument (not sess_rows) so this fn stays a pure shape-assembler with no ts-matching
    logic of its own. `kai.state` is always 'swept' here because this only ever runs
    post-seal, after the closer's full-reel OCR sweep already walked every frame — 'pending'
    would only apply to a not-yet-closed reel, which never reaches this fn."""
    maps = maps or {}
    rec_by_f = maps.get("reconcile") or {}
    live_by_f = maps.get("live") or {}
    second_by_f = maps.get("second") or {}
    kai_by_f = maps.get("kai") or {}
    super_reads = super_reads or {}

    out = []
    for row in routing or []:
        f = str(row.get("f") or "")
        if not f:
            continue
        label = str(row.get("label") or "")
        sources = row.get("sources") or []
        sup = super_reads.get(f)
        if sup is None and isinstance(row.get("super"), dict):
            sup = row.get("super")
        live_info = live_by_f.get(f)
        second_info = second_by_f.get(f)
        kai_info = kai_by_f.get(f)
        rec = rec_by_f.get(f) or {}

        layers = {
            "live": {"state": "named" if live_info else "idle",
                     "names": (live_info or {}).get("names") or []},
            "second": {"state": "drained" if second_info else "idle",
                       "confirmNames": (second_info or {}).get("confirmNames") or [],
                       "correctedNames": (second_info or {}).get("correctedNames") or [],
                       "missedNames": (second_info or {}).get("missedNames") or []},
            "kai": {"state": "swept",
                    "missedTexts": (kai_info or {}).get("missedTexts") or [],
                    "caughtNames": [kai_info["judgeName"]] if (kai_info and kai_info.get("judgeName")) else []},
            "super": {"state": "reread" if (sup and sup.get("reread")) else "—",
                      "deepNames": (sup or {}).get("deepNames") or []},
            "router": {"label": label,
                       "quorumVotes": {b: (b in sources) for b in
                                       ("ocr", "journal", "tabstrip", "grid", "read", "judge")},
                       "confidence": row.get("confidence")},
            "gate": {"gatePass": row.get("gatePass"), "gateReason": row.get("gateReason"),
                     "gateSources": row.get("gateSources") or []},
            "funnel": {"fired": bool(row.get("routed")), "kind": row.get("routed"),
                       "route": row.get("route")},
        }
        out.append({"f": f, "ts": int(row.get("ts") or 0), "label": label, "layers": layers,
                    "owner": rec.get("owner"), "verdict": rec.get("verdict"),
                    "why": rec.get("why"),
                    # v1253 R1 (DIABLO-LANGUAGE) — the read's TRUE Diablo scene, materialized
                    # into kai_report.json beside owner/verdict so the sealed reel carries it
                    # out to the Theatre (portal frame = 'transition', not collapsed gameplay).
                    "scene": rec.get("scene"), "tab": rec.get("tab"), "area": rec.get("area")})
    return out


def _kai_live_routing_row(rd):
    """Pure. Shapes ONE live bridge read (from /state 'reads', lane=='deep') into a
    routing-row-compatible dict so _engine_driver's 2s loop can hand the SAME
    _kai_reconcile() the closer uses a lightweight live guess — no second decision tree,
    no OCR sweep, no gate recheck (those only exist post-seal). This is deliberately the
    cheapest possible shape: real routing rows carry gate/route/sources built from a full
    reel walk, which a 2s poll cannot afford — a live row only ever advertises what it
    directly knows (did a name land, was the tab a tally tab)."""
    names = rd.get("names") or []
    scene = str(rd.get("scene") or "")
    tab = str(rd.get("stashTab") or "").lower()
    if scene == "stash" and tab in ("runes", "gems", "materials"):
        label = "stash-" + tab
    elif scene == "stash":
        label = "stash"
    elif names:
        label = "tooltip"
    else:
        label = "gameplay"
    fid = str(rd.get("frameId") or "")
    f = (fid.rsplit("/", 1)[-1] + ".jpg") if fid else ""
    # v1203 — sources/confidence must track the LABEL THAT ACTUALLY WON, not raw `names`
    # presence. scene=='stash' is checked first above, so a read row that is on a stash tab
    # AND happens to carry a (stale/co-reported) `names` field used to come out with
    # label='stash-runes' but sources=['read'] anyway — 'read' is only ever a real witness
    # for a 'tooltip' label everywhere else in the routing model (_kai_build_routing).
    # _kai_reconcile then narrated that as owner='ocr' for the stash-* row (matching
    # `elif row.get("sources"): owner="ocr"`), a real evidence class that never actually
    # looked at this frame — the same borrowed/mislabeled-witness class the v1194/v1198
    # fixes closed elsewhere. This dict is documented as 'routing-row-compatible', so it
    # must honor the same 'sources = brains whose vote equals the final label' contract.
    is_tooltip = label == "tooltip"
    return {"f": f, "ts": int(rd.get("captureTs") or rd.get("ts") or 0), "label": label,
            "sources": ["read"] if is_tooltip else [], "confidence": (1 if is_tooltip else 0),
            "super": None, "gatePass": None, "gateReason": None, "gateSources": [],
            "routed": None, "route": None}


# ── v948.13 🎞🔗 FILM ↔ REGISTRATION COMPLETENESS (ENGINE_ARCHITECTURE.md target #2) —
# Konyo's law: "every item I hover should produce a read AND a reel frame — screenshots
# are missing from the film." This is the DIAGNOSTIC: cross-reference the reel (film,
# ground truth) against the deep reads to find dropped captures, distinct from KAI's
# already-honest "text seen, never read" ledger.
_COMPLETENESS_TOL_MS = 1500   # ~1.5x FOOTAGE_INTERVAL_S default (1fps archive) — jitter slack


def _session_completeness(sess_rows, reel_frames, tol_ms=_COMPLETENESS_TOL_MS):
    """Pure. Two independent gap classes, both real signal, only one a bug:

      'unread'       — KAI's retro reel sweep saw item text with no deep read anywhere near
                        it (rides sess_rows as lane=='kai' per-item rows, frameId set, from
                        _kai_closer_loop's `missed[]`). The moment WAS filmed — a reel frame
                        backs every one of these by construction (KAI only scans real reel
                        frames) — it just went unread. Honest, already-caught. NOT a drop.
      'read-no-film' — a deep read landed (an item WAS read, hover→read worked) but no reel
                        frame exists within tol_ms of its captureTs. This IS a capture drop:
                        the film thread didn't archive a still near that moment.

    sess_rows: this session's journal rows (already filtered to one sessionId).
    reel_frames: the sealed reel's index.json 'frames' list [{"f":.., "ts":..}, ...] —
    the film's ground truth of what was actually archived to hist_dir.

    Returns {hovers_estimated, reads, reel_frames, gaps: [...], unread, dropped, coveragePct}.
    hovers_estimated = reads + unread — the best estimate available of "moments item text
    appeared" (no raw hover-event stream exists to count directly; the retro OCR ledger is
    the closest ground-truth proxy, per Konyo's instruction to use kai_report.missed[]).
    coveragePct = reads / hovers_estimated * 100 — the read-side registration rate."""
    reads = [r for r in (sess_rows or []) if r.get("lane") == "deep" and (r.get("names") or [])]
    kai_item_rows = [r for r in (sess_rows or [])
                      if r.get("lane") == "kai" and r.get("frameId")
                      and isinstance(r.get("kai"), dict)]
    frame_ts = sorted(int(f.get("ts") or 0) for f in (reel_frames or []) if f.get("ts") is not None)

    def _nearest_gap_ms(ts):
        if not frame_ts:
            return None
        i = bisect.bisect_left(frame_ts, ts)
        best = None
        if i < len(frame_ts):
            best = frame_ts[i] - ts
        if i > 0:
            d = ts - frame_ts[i - 1]
            best = d if best is None else min(best, d)
        return best

    gaps = []
    for r in kai_item_rows:
        texts = (r.get("kai") or {}).get("texts") or []
        gaps.append({"ts": int(r.get("ts") or 0), "kind": "unread", "frameId": r.get("frameId"),
                     "note": "text seen, never read: " + ", ".join(str(t) for t in texts[:3])})
    dropped = 0
    for r in reads:
        ts = int(r.get("captureTs") or r.get("ts") or 0)
        gap = _nearest_gap_ms(ts)
        if gap is None or gap > tol_ms:
            dropped += 1
            gaps.append({"ts": ts, "kind": "read-no-film", "frameId": r.get("frameId"),
                         "note": "read landed, no reel frame within %dms (nearest %s)" %
                                 (tol_ms, "none" if gap is None else str(gap) + "ms")})
    gaps.sort(key=lambda g: g["ts"])
    n_reads = len(reads)
    n_unread = len(kai_item_rows)
    hovers_estimated = n_reads + n_unread
    coverage_pct = round(100.0 * n_reads / hovers_estimated, 1) if hovers_estimated else 100.0
    return {
        "hovers_estimated": hovers_estimated,
        "reads": n_reads,
        "reel_frames": len(reel_frames or []),
        "gaps": gaps,
        "unread": n_unread,
        "dropped": dropped,
        "coveragePct": coverage_pct,
    }


_COMPLETENESS_CACHE = {"reel": None, "mtime": 0.0, "val": None}
_REEL_REPORT_CACHE = {}


def _reel_report_cached(reel_dir):
    """v1276 (D5 engine) — memoized read of a sealed reel's kai_report.json, keyed by
    path+mtime so the /api/sessions poll (~12s) never re-parses a hot report. Returns the
    parsed dict, or None when the reel has no report (unsealed / old / live reels) — the
    caller then leaves coverage + classFrames absent so the UI honestly hides both."""
    try:
        rp = os.path.join(reel_dir, "kai_report.json")
        mt = os.path.getmtime(rp)
        c = _REEL_REPORT_CACHE.get(reel_dir)
        if c and c[0] == mt:
            return c[1]
        with open(rp) as fh:
            val = json.load(fh)
        _REEL_REPORT_CACHE[reel_dir] = (mt, val)
        return val
    except Exception:
        return None


def _newest_completeness():
    """{reads, film, coverage%} from the newest sealed reel's completeness stat (post-seal;
    ENGINE_ARCHITECTURE.md target #2). Cached by reel+mtime like _newest_gate_count so
    /api/status polling never re-parses a hot report."""
    try:
        hist = HIST_DIR
        reels = sorted((d for d in os.listdir(hist)
                        if d.startswith("reel_") and os.path.isfile(os.path.join(hist, d, "kai_report.json"))),
                       reverse=True)
        if not reels:
            return None
        rp = os.path.join(hist, reels[0], "kai_report.json")
        mt = os.path.getmtime(rp)
        if _COMPLETENESS_CACHE["reel"] == reels[0] and _COMPLETENESS_CACHE["mtime"] == mt:
            return _COMPLETENESS_CACHE["val"]
        c = (json.load(open(rp, encoding="utf-8")) or {}).get("completeness")
        val = c if isinstance(c, dict) and c.get("reads") is not None else None
        _COMPLETENESS_CACHE.update(reel=reels[0], mtime=mt, val=val)
        return val
    except Exception:
        return None


def _kai_write_report_atomic(path, report):
    """v948.17 — Grok P0-3 (2026-07-21 fast-run soak): kai_report.json is the durable artifact
    the Theatre/accuracy-gate audits (routing/register/gate/completeness all read it back from
    disk — see `_newest_gate_count`, `_newest_completeness`). Before this fix it was written
    with a plain `open(...,'w') + json.dump`, TWICE: once scan-only right after the reel sweep,
    then again after register/routing/completeness were computed. If ANYTHING raised between
    those two writes (or the process died mid-`json.dump`), the on-disk file silently stayed at
    the scan-only shape forever — a 'sealed' report with no routing/register/gate, which is
    exactly what the forensic soak caught. Write to a tmp file in the SAME directory (same
    filesystem → os.replace is atomic) and swap it in — a reader never sees a half-written or
    stale-partial file, and a crash mid-write leaves the OLD (still-complete) report intact
    rather than a truncated new one."""
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(report, f)
        os.replace(tmp, path)
        return True
    except Exception as e:
        print(f"⚠ KAI report atomic write failed ({path}): {e}", flush=True)
        try:
            os.remove(tmp)
        except Exception:
            pass
        return False


def _kai_closer_loop():
    """v934 — 🧠 KAI THE CLOSER (layer 3, v1). After a session seals, walk its ENTIRE reel
    with the local OCR worker (no time pressure, nice'd), diff every frame's item-ish text
    against what the session's reads actually caught, and journal a `lane: kai` ledger:
    the frames whose text NO eye read — the ground truth of what was missed. v2 escalates
    misses into deep reads + auto-register + the mule/throw-out regret funnel."""
    if os.environ.get("TV_KAI", "1") == "0":
        return
    ocr_bin = os.path.join(HERE, "bin", "ocr_mac")
    if not (os.path.isfile(ocr_bin) and os.access(ocr_bin, os.X_OK)):
        return
    time.sleep(20.0)
    hist = HIST_DIR
    while True:
        try:
            time.sleep(30.0)
            if not os.path.isdir(hist):
                continue
            # v937.3 (Grok gate #1/#2) — KAI works ONLY between sessions: closing a reel
            # while a NEW session is ON AIR races the funnel's SET wrapper against the live
            # store and fights the game for CPU. Reels wait; they aren't going anywhere.
            if _agent_mode != "off" or _agent_alive():
                continue
            # v947/v948.7 — re-close reels under kaiVer < N (retro grid-solo + gap funnel)
            # v1259 — bump target to 4 so ALREADY-SEALED reels re-sweep to pick up v1254 scene
            # carry-through, v1256 gems detection, the v1258 panel-open guard, and the v1259
            # honest gate. The two wallpaper reels re-seal as gameplay (0 gems) via the guard.
            _KAIVER_TARGET = 4
            reels = []
            for d in sorted(os.listdir(hist)):
                if not (d.startswith("reel_") and os.path.isdir(os.path.join(hist, d))):
                    continue
                if not os.path.isfile(os.path.join(hist, d, "index.json")):
                    continue
                kr = os.path.join(hist, d, "kai_report.json")
                if not os.path.isfile(kr):
                    reels.append(d)
                    continue
                try:
                    with open(kr, encoding="utf-8") as _kf:
                        _kv = int((json.load(_kf) or {}).get("kaiVer") or 1)
                    if _kv < _KAIVER_TARGET:
                        reels.append(d)
                except Exception:
                    reels.append(d)
            if not reels:
                continue
            # v948.8 — PRIORITY RECLOSE: an explicit POST /api/kai_reclose drops a
            # ".kai_priority" marker in the reel dir. Without this, a debugger-requested
            # reclose sits behind the ENTIRE kaiVer<3 backlog (sorted-oldest-first) —
            # after the v948.7 kaiVer bump that backlog can be dozens of reels deep, so
            # the endpoint's "closer will re-scan within ~30s" promise was false. Priority
            # reels jump the queue; normal sweep order is unchanged otherwise.
            _priority = [d for d in reels if os.path.isfile(os.path.join(hist, d, ".kai_priority"))]
            if _priority:
                reels = _priority + [d for d in reels if d not in _priority]
            rd = os.path.join(hist, reels[0])
            sid = reels[0][len("reel_"):]
            try:
                os.remove(os.path.join(rd, ".kai_priority"))
            except Exception:
                pass
            frames = []
            try:
                with open(os.path.join(rd, "index.json"), encoding="utf-8") as f:
                    frames = (json.load(f) or {}).get("frames") or []
            except Exception:
                pass
            # what the session's eyes actually read (deep + ocr + verify lanes)
            read_text = set()
            try:
                sess_rows = [r for r in _kai_journal_rows() if r.get("sessionId") == sid]
            except Exception:
                sess_rows = []
            for r in sess_rows:
                for nm in (r.get("names") or []) + (r.get("ocr_names") or []):
                    read_text.add(str(nm).strip().lower())
            # v941.3 — STASH TIME-MAP: stash screens are OCR-dark (icon grids, ornate tab
            # labels Vision can't read at footage res — run-3 proof: OCR [] on runes-tab
            # frames). The JOURNAL knows when each tab was open; frames inherit the class.
            stash_times = []
            for r in sess_rows:
                if r.get("lane") == "deep" and str(r.get("scene") or "") == "stash":
                    tb = str(r.get("stashTab") or "").lower()
                    if tb:
                        stash_times.append((int(r.get("captureTs") or r.get("ts") or 0), tb))
            print(f"🧠 KAI: closing {sid} — {len(frames)} frames, {len(read_text)} known texts", flush=True)
            # OCR worker: one warm process, stdin path → stdout JSON line
            import queue as _q
            try:
                wp = subprocess.Popen([ocr_bin, "--worker"], stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE, text=True, bufsize=1,
                                      preexec_fn=(lambda: os.nice(15)) if not IS_WIN else None)
            except Exception as e:
                print(f"🧠 KAI: worker spawn failed ({e}) — skipping reel"); continue
            missed = []
            grounded_reads = []        # FIX C (F3) — {f, ts, names[]} grail names recovered from garbled tooltip OCR
            classes = {}
            class_frames = {}          # v935.11 R5 — {cls: count} over every line-producing frame
            routing_scan = []          # v944 🚦 — per-scanned-frame label evidence (routing ledger)
            scanned = textframes = 0
            # v1207 — WORKER-ORPHAN-LEAK class (funnel/closer side, same vein as v1206's
            # core _WORKER/_OCR fix): `wp` (the ocr_mac --worker subprocess) was only
            # terminated by a plain sequential statement AFTER this for-loop — if ANYTHING
            # in 120+ lines of per-frame processing raised an exception this loop's own
            # inner try/excepts don't already catch, execution jumped straight past the
            # cleanup to the closer's outer per-reel except (below), leaving `wp` running
            # forever — and since the closer just sleeps and moves to the NEXT reel, each
            # such failure spawns ANOTHER orphaned worker on top of the last. try/finally
            # guarantees the worker is always reaped, however this pass ends.
            try:
                for it in frames:
                    fp = os.path.join(rd, it.get("f") or "")
                    if not os.path.isfile(fp):
                        continue
                    try:
                        wp.stdin.write(fp + "\n"); wp.stdin.flush()
                        line = wp.stdout.readline()
                        j = json.loads(line) if line else {}
                    except Exception:
                        break
                    scanned += 1
                    raw = j.get("lines") or []
                    texts = [t for t in raw if _kai_itemish(t)]
                    # FIX C (F3) — GRAIL TOOLTIP NAME GROUNDING. Try to recover a real item name
                    # from the RAW lines (not just the itemish survivors — the actual name line is
                    # often the one leet-garble drops, e.g. 'H4RLEQVIN CR'). A grounded name is
                    # _kai_fullnames-verified; it promotes this frame from missed→named (register).
                    _grounded = []
                    try:
                        _grounded = list(_kai_ground_lines(raw).keys())
                    except Exception:
                        _grounded = []
                    if _grounded:
                        grounded_reads.append({"f": it.get("f"), "ts": it.get("ts"), "names": _grounded[:4]})
                    # R5 — classify every frame that produced OCR lines, before the missed decision.
                    _ocr_cls = _kai_frame_cls(raw, texts) if raw else None   # v944 — OCR's own verdict
                    # v947 — EVERY film still gets intake-style eyes (tab chrome + grid fingerprint).
                    # Does NOT call gemIntake/runeIntake/materialIntake — only mimics their crops.
                    _fts5 = int(it.get("ts") or 0)
                    _near = _kai_sticky_tab(_fts5, stash_times)
                    _eye = {}
                    try:
                        from stash_eye import analyze_frame as _se_analyze

                        def _wp_read(p):
                            try:
                                wp.stdin.write(p + "\n"); wp.stdin.flush()
                                line = wp.stdout.readline()
                                return json.loads(line) if line else {}
                            except Exception:
                                return {}

                        # v948.7 — allow_grid_solo: film stills rechecked without live deep sticky
                        _eye = _se_analyze(
                            fp,
                            ocr_lines=raw,
                            journal_tab=str(_near or ""),
                            model_tab="",
                            ocr_worker_read=_wp_read,
                            work_dir=rd,
                            allow_grid_solo=True,
                        )
                    except Exception:
                        _eye = {}
                    _eye_cls = str((_eye or {}).get("cls") or "")
                    _eye_tab = str((_eye or {}).get("tab") or "")
                    _eye_src = list((_eye or {}).get("sources") or [])
                    _ocr_tab = str((_eye or {}).get("ocrTab") or "")
                    # fused eye tally only (never raw grid alone — invents materials on loading)
                    # v1259 PHANTOM-OCR FIX — only credit the eye's tally cls to `_ocr_cls`
                    # (which becomes the scan row's `ocr`/`ocrLabel` = the 'pixel'/'ocr' witness
                    # in _kai_build_routing) when OCR ACTUALLY contributed to the eye's tab
                    # decision ('ocr' in the fusion's own sources). A grid-DERIVED eye cls (grid
                    # fingerprint, no readable chrome — the RotW gems case) must NOT masquerade
                    # as a 2nd 'ocr' vote alongside its real 'grid' vote: that faked ONE physical
                    # detector into two independent classes → conf 2 → self-certified the gate.
                    # It now rides ONLY its genuine grid vote (gridLabel, below); the display
                    # class still comes through via `_eye_tab`, so nothing visible regresses.
                    if _eye_cls in ("stash-runes", "stash-gems", "stash-materials") and "ocr" in _eye_src:
                        _ocr_cls = _eye_cls
                    elif _ocr_cls in (None, "gameplay", "stash", "tooltip"):
                        _ocr_cls = _kai_tab_strip_refine(fp, _ocr_cls, wp) or _ocr_cls
                    cls = _ocr_cls
                    if _eye_tab in ("runes", "gems", "materials"):
                        _scls = "stash-" + _eye_tab
                        class_frames[_scls] = {"f": it.get("f"), "ts": it.get("ts")}
                        cls = _scls
                    elif _near:
                        _scls = ("stash-" + _near) if _near in ("runes", "gems", "materials") else "stash"
                        class_frames[_scls] = {"f": it.get("f"), "ts": it.get("ts")}
                        if not cls or cls in ("gameplay", "stash"):
                            cls = _scls
                        elif _near in ("runes", "gems", "materials") and cls == "stash":
                            cls = _scls
                    elif _eye_cls == "stash":
                        cls = "stash"
                    if cls:
                        classes[cls] = classes.get(cls, 0) + 1
                        class_frames[cls] = {"f": it.get("f"), "ts": it.get("ts")}
                    if texts:
                        textframes += 1
                        new = [t for t in texts if t.strip().lower() not in read_text]
                        name_new = [t for t in new if _kai_nameish(t)]
                        # FIX C (F3) — a frame whose tooltip we GROUNDED to a real name is read,
                        # not missed: don't cry "unread text" over its garbled stat lines.
                        if name_new and not _grounded:
                            missed.append({"f": it.get("f"), "ts": it.get("ts"),
                                           "texts": name_new[:6], "cls": cls})
                    # v944/v947/v948.7 🚦 — votes from fused eyes
                    # Vault sticky (personal/shared) must NOT veto tally grid/tabstrip on the
                    # same film still — that blocked materials retro-funnel when live deep
                    # only named shared/personal.
                    _jlab = None
                    if _near in ("runes", "gems", "materials"):
                        _jlab = "stash-" + _near
                    elif _near in ("personal", "shared"):
                        _jlab = "stash"   # weak: panel open only, not a tally veto
                    elif _near:
                        _jlab = "stash"
                    _ts_lab = ("stash-" + _ocr_tab) if _ocr_tab in ("runes", "gems", "materials") else (
                        "stash" if _ocr_tab in ("personal", "shared") else None)
                    # grid vote — v1194: only from the fused tab when grid ITSELF corroborated
                    # it (else that's OCR's own chrome-strip read double-counted as a second
                    # "independent" class); else the raw pixel-only gridLabel (solo materials/
                    # gems/runes). See _kai_grid_vote_label.
                    _raw_gl = str((_eye or {}).get("gridLabel") or "")
                    _gr_lab = _kai_grid_vote_label(_eye_tab, _eye_src, _raw_gl, _eye_cls)
                    # v1259 SANCTIONED GRID-SOLO flag — the tighter grid-confidence bar for a
                    # single-signal tally route: grid named a DEFINITE tally tab AND the panel-
                    # open dark-cell lattice (v1258 A1 geometry) confirmed a real stash panel,
                    # AND no OCR chrome corroborated it (grid genuinely IS the sole witness). The
                    # gate honors this at conf 1; a low-confidence/uncorroborated grid read (no
                    # panel_open, or a plain-stash pick) is NOT flagged and cannot self-certify.
                    _grid_solo = bool(
                        _gr_lab in ("stash-runes", "stash-gems", "stash-materials")
                        and ((_eye or {}).get("gridDetail") or {}).get("panel_open")
                        and "ocr" not in _eye_src
                    )
                    _disp = cls or "gameplay"
                    if _eye_cls in ("stash-runes", "stash-gems", "stash-materials"):
                        _disp = _eye_cls
                    elif _gr_lab in ("stash-runes", "stash-gems", "stash-materials"):
                        _disp = _gr_lab
                    elif _ocr_cls in ("stash-runes", "stash-gems", "stash-materials"):
                        _disp = _ocr_cls
                    elif _jlab and _jlab.startswith("stash-") and _jlab != "stash":
                        _disp = _jlab
                    elif _jlab:
                        _disp = _jlab if not (cls and str(cls).startswith("stash-")) else cls
                    routing_scan.append({
                        "f": it.get("f"), "ts": int(it.get("ts") or 0),
                        "ocr": bool(_ocr_cls and _ocr_cls != "gameplay"),
                        "ocrLabel": _ocr_cls if (_ocr_cls and _ocr_cls != "gameplay") else None,
                        "journal": bool(_near),
                        "journalLabel": _jlab,
                        "tabstrip": bool(_ts_lab),
                        "tabstripLabel": _ts_lab,
                        "grid": bool(_gr_lab),
                        "gridLabel": _gr_lab,
                        "gridSolo": _grid_solo,
                        "stashTab": _eye_tab or (_near or ""),
                        "label": _disp or "gameplay",
                        "sig": _kai_frame_sig(fp),
                        "eyeSources": _eye_src,
                    })
                    time.sleep(0.08)   # peaceful — slightly faster; intake-style crops are small
            finally:
                try:
                    wp.stdin.close(); wp.terminate()
                except Exception:
                    pass
            # v948.7 RETRO CLUSTER PROMOTE — consecutive plain-stash stills get majority
            # grid/tabstrip tally vote so materials/gems/runes on film funnel even when
            # live deep never named that tab (Theatre has the pixels = recheck).
            try:
                routing_scan = _kai_retro_promote_tally(routing_scan)
            except Exception as _rpe:
                print(f"⚠ KAI retro promote: {_rpe}", flush=True)
            report = {"sid": sid, "scanned": scanned, "textFrames": textframes,
                      "classFrames": class_frames,
                      "missedFrames": len(missed), "missed": missed[:40],
                      "grounded": grounded_reads[:40],   # FIX C (F3) — grail names recovered from garble
                      "classes": classes,
                      "closedAt": int(time.time() * 1000), "kaiVer": 4,
                      "eyeNote": "v1259 honest gate (grid-solo sanctioned, phantom-ocr removed) "
                                 "+ v1258 panel-open guard + v948.7 retro grid-solo/gap funnel"}
            _kai_write_report_atomic(os.path.join(rd, "kai_report.json"), report)
            # journal the ledger onto the session's timeline (🧠 gold in SIM).
            # v934.1 — GHOST-PROOF: split_sessions sorts by ts and cuts on sid change, so
            # ts=now rows appended after newer sessions would spawn a ghost block (the
            # bak_ghost_purge class). Journal law is ts == captureTs: misses land AT their
            # frame's true moment inside the session span; the summary lands at seal+1ms.
            now_ms = int(time.time() * 1000)
            _sess_last = max((int(r.get("ts") or 0) for r in sess_rows), default=now_ms)
            rows = []
            for m in missed[:20]:
                _fts = int(m.get("ts") or _sess_last)
                rows.append({"ts": _fts, "captureTs": _fts,
                             "completedTs": now_ms, "lane": "kai", "mode": "kai",
                             "scene": "kai", "names": [], "sessionId": sid,
                             "frameId": "reel_" + sid + "/" + str(m.get("f") or "").replace(".jpg", ""),
                             "kai": {"texts": m.get("texts") or [], "cls": m.get("cls")},
                             "note": "🧠 unread text: " + ", ".join((m.get("texts") or [])[:3])})
            # FIX C (F3) — journal GROUNDED grail reads so _kai_compile_register (re-read below)
            # registers them: a legible grail tooltip whose OCR was leet-garbled now lands its
            # REAL name in the register/Chronicle-inbox instead of dying in missed[].
            for g in grounded_reads[:20]:
                _gts = int(g.get("ts") or _sess_last)
                _gn = list(g.get("names") or [])
                rows.append({"ts": _gts, "captureTs": _gts, "completedTs": now_ms,
                             "lane": "kai", "mode": "kai", "scene": "kai", "names": [],
                             "sessionId": sid,
                             "frameId": "reel_" + sid + "/" + str(g.get("f") or "").replace(".jpg", ""),
                             "kai": {"grounded": _gn},
                             "note": "🏷 grail grounded from garbled OCR: " + ", ".join(_gn[:3])})
            rows.append({"ts": _sess_last + 1, "captureTs": _sess_last + 1, "completedTs": now_ms,
                         "lane": "kai", "mode": "kai", "scene": "kai", "names": [],
                         "sessionId": sid, "frameId": "",
                         "kai": {**{k: report[k] for k in ("scanned", "textFrames", "missedFrames")},
                                 "classes": classes},
                         "note": f"🧠 KAI closed the session — {scanned} frames swept · "
                                 f"{len(missed)} frames held text no eye read"})
            try:
                with open(os.path.join(HERE, "sessions.jsonl"), "a", encoding="utf-8") as f:
                    for r in rows:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
            except Exception as e:
                print(f"🧠 KAI: journal append failed ({e})", flush=True)
            print(f"🧠 KAI report sealed for {sid}: {scanned} swept, {len(missed)} missed-text frames", flush=True)
            # v935 — 🚨 WATCHDOG rides the same reel-close moment (sess_rows already loaded)
            try:
                _watchdog_check(sid, sess_rows)

                # ── v944.6/v946 Stage 3 📸/🔬/🏦 lanes OBEY the ledger ──
                # PRE-fire plan → funnel/judge/vault fire ONLY ledger-fireable rows.
                # After receipts land, final rebuild writes `routed` back.
                # v949.x 🧠🔬 SUPER-ANALYZE KAI accumulators — declared BEFORE the Stage-3 try so
                # they always exist (empty) even if the try below raises early; populated inside
                # the try, read back by the register/routing block further down (same function
                # scope, no closures needed).
                _super_recovered = {}   # f -> {"reread": True, "deepNames": [...], "tier": ...}
                _super_attempted = []
                try:
                    _plan = _kai_build_routing(routing_scan, sess_rows, sid, sess_rows)
                    _funnel_jobs, _judge_jobs, _vault_jobs = _kai_stage3_select(_plan)
                    # v948.7 — gap funnels from reel eyes (materials etc. never sticky-deeped)
                    # v948.17 (Grok P0-1) — re-read the journal FRESH here: `sess_rows` was
                    # cached before the ~153-frame OCR sweep above, which can easily take long
                    # enough for a live tally to land afterward (this soak: runes 404 landed
                    # AFTER seal, during the sweep). A stale `receipted` set would queue a
                    # gap-funnel for a tab that already has a real receipt by now.
                    try:
                        _gap_rows = [r for r in _kai_journal_rows() if r.get("sessionId") == sid]
                    except Exception:
                        _gap_rows = sess_rows
                    try:
                        _gaps = _kai_stage3_gap_funnels(_plan + routing_scan, _gap_rows)
                        _have = {str(j.get("tab") or "") for j in _funnel_jobs}
                        for _g in _gaps:
                            if str(_g.get("tab") or "") not in _have:
                                _funnel_jobs.append(_g)
                                _have.add(str(_g.get("tab") or ""))
                                print(f"📸 KAI gap-funnel: queue {_g.get('tab')} from {_g.get('f')} "
                                      f"(reel recheck, conf={_g.get('conf')})", flush=True)
                    except Exception as _gfe:
                        print(f"⚠ KAI gap-funnel select: {_gfe}", flush=True)
                    w2 = globals().get("_MAIN_WIN")
                    # 📸 FUNNEL — one shot per ledger-selected tally tab (newest frame), SET-wrapper
                    for _fj in _funnel_jobs:
                        if w2 is None or os.environ.get("TV_KAI_FUNNEL", "1") == "0":
                            break
                        t3 = str(_fj.get("tab") or "")
                        _ff = str(_fj.get("f") or "")
                        if not t3 or not _ff:
                            continue
                        # v948.17 (Grok P0-1) — NEVER-ZERO WRITE GUARD. Re-check the FRESH
                        # journal right before firing (this loop can span minutes — each prior
                        # job waits up to 120s for its receipt — so even the _gap_rows snapshot
                        # above can be stale by the time THIS tab's turn comes). A real receipt
                        # already on the books for this tab means: don't even fire — a thin
                        # reel-recheck photo has no business overwriting a good tally.
                        try:
                            _fresh_t3 = [r for r in _kai_journal_rows() if r.get("sessionId") == sid]
                        except Exception:
                            _fresh_t3 = sess_rows
                        _prev_best_t3 = _tab_best_total(_fresh_t3, t3)
                        if _prev_best_t3 > 0:
                            print(f"⛔ KAI funnel guard: skip {t3} — real tally already total="
                                  f"{_prev_best_t3} (never-zero write law, Grok P0-1)", flush=True)
                            continue
                        _histp = "/hist/reel_" + sid + "/" + _ff
                        _fid3 = "reel_" + sid + "/" + _ff.replace(".jpg", "")
                        # v948.17 — PREV (the best real total known at fire time) rides into the
                        # JS itself as a second, defense-in-depth guard: even if a receipt lands
                        # in the brief window between the Python check above and this fetch
                        # resolving, the SET-style ADJ-subtract (which otherwise clobbers matched
                        # keys down to the new read's count — the literal 404→4 mechanism) only
                        # applies when the new total is not a regression vs PREV. A blocked
                        # write still journals an honest (non-SET) receipt, never a silent drop.
                        _js = ("(function(){try{var F=document.getElementById('tvd-eng');if(!F||!F.contentWindow)return 0;var W=F.contentWindow;"
                               "if(W._stashShutter)return 2;var FN={runes:'runeIntake',gems:'gemIntake',materials:'materialIntake'}[%s];if(typeof W[FN]!=='function')return 0;"
                               "var LSK={runes:'d2r_runeStash',gems:'d2r_gemStash',materials:'d2r_materialStash'}[%s];"
                               "var ADJ={runes:'adjustRuneStash',gems:'adjustGemStash',materials:'adjustMaterialStash'}[%s];"
                               "var PREV=%s;"
                               "var prev={};try{var st0=JSON.parse(W.LSR.getItem(LSK)||'{}');Object.keys(st0).forEach(function(k){prev[k]=parseInt(st0[k],10)||0})}catch(e){}"
                               "fetch(%s+'?'+Date.now()).then(function(r){if(!r.ok)throw 0;return r.blob()}).then(function(b){"
                               "return W[FN]([new W.File([b],'kai-funnel.jpg',{type:'image/jpeg'})])}).then(function(res){"
                               "var newTotal=(res&&res.total)||0;var applied=false;"
                               "try{if(res&&res.ok&&(PREV<=0||newTotal>=PREV)){Object.keys(res.added||{}).forEach(function(k){var was=prev[k]||0;if(was>0&&typeof W[ADJ]==='function')W[ADJ](k,-was)});applied=true}}catch(e){}"
                               "try{fetch('/intake_result',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ts:Date.now(),tab:%s,kind:'kai-funnel',ok:!!(res&&res.ok)&&applied,counts:(applied?((res&&res.added)||{}):{}),total:(applied?newTotal:PREV),errors:(res&&res.errors)||0,frameId:%s,guardHeld:!applied})}).catch(function(){})}catch(e){}"
                               # v948.17 (Grok P0-2, 2026-07-21 fast-run soak) — the gems funnel
                               # fired (this control-log print ran) but NO /intake_result receipt
                               # ever journaled: the promise chain (fetch the frame → gemIntake →
                               # …) rejected somewhere and the OLD catch here was silent (`function(){}`
                               # — no receipt, no note, nothing). An honest-miss receipt now lands
                               # even on a hard failure, so the theatre shows a real ERROR instead
                               # of a gap that looks like nothing ran.
                               "}).catch(function(_e3){try{fetch('/intake_result',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ts:Date.now(),tab:%s,kind:'kai-funnel',ok:false,counts:{},total:0,errors:1,frameId:%s,err:String(_e3&&_e3.message||_e3||'funnel fetch/intake rejected')})}).catch(function(){})}catch(e4){}});"
                               "return 1}catch(e){return 0}})()") % (
                                  json.dumps(t3), json.dumps(t3), json.dumps(t3), json.dumps(_prev_best_t3),
                                  json.dumps(_histp), json.dumps(t3), json.dumps(_fid3),
                                  json.dumps(t3), json.dumps(_fid3))
                        try:
                            _ejs(w2, _js, timeout=5.0)
                            print(f"📸 KAI funnel (ledger): fired {t3} from {_ff} (prevBest={_prev_best_t3})", flush=True)
                        except Exception as _fe:
                            print(f"⚠ KAI funnel fire failed ({t3}): {_fe}", flush=True)
                            continue
                        # v1201 — CLOCK-SKEW class (same sweep as engine-capture v1199 /
                        # engine-read v1200): this 120s bounded wait used ONE wall-clock
                        # anchor (`_t0f`) for BOTH the pacing deadline (`time.time() - _t0f`)
                        # AND the journal cutoff (`completedTs >= _t0f*1000`, line below). The
                        # journal cutoff MUST stay wall-clock (completedTs is a persisted
                        # wall-clock timestamp — comparing it against anything else would be
                        # wrong). But a pacing deadline built on the SAME wall clock means a
                        # backward NTP/sleep-wake jump mid-wait makes `time.time() - _t0f` go
                        # negative, so the loop keeps polling until REAL wall time claws back
                        # past the original 120s window PLUS the jump size — a multi-minute
                        # stall of the closer's ENTIRE post-seal pass (this loop is serial;
                        # everything after it — other tabs' gap-funnels, judge ping-pong,
                        # kai_report — waits behind it). Split the two: `_t0f` stays wall-clock
                        # for the journal comparison; `_t0f_mono` (monotonic, immune to clock
                        # jumps) drives the deadline.
                        _t0f = time.time()
                        _t0f_mono = time.monotonic()
                        while time.monotonic() - _t0f_mono < 120.0:
                            time.sleep(6.0)
                            try:
                                if any(r3.get("lane") == "intake" and (r3.get("intake") or {}).get("kind") == "kai-funnel"
                                       and (r3.get("intake") or {}).get("tab") == t3
                                       and int(r3.get("completedTs") or 0) >= int(_t0f * 1000)
                                       for r3 in _kai_journal_rows()[-40:]):
                                    print(f"📸 KAI funnel: {t3} receipt journaled ✓", flush=True)
                                    try:
                                        _res = {"ts": _sess_last + 40, "captureTs": _sess_last + 40,
                                                "completedTs": int(time.time() * 1000), "lane": "watchdog",
                                                "mode": "watchdog", "scene": "watchdog", "names": [],
                                                "sessionId": sid, "frameId": "",
                                                "watchdog": {"rule": "resolved-by-kai-funnel", "tab": t3},
                                                "note": f"✅ WATCHDOG resolved — KAI funnel receipted {t3} from the reel"}
                                        with open(os.path.join(HERE, "sessions.jsonl"), "a", encoding="utf-8") as _rf:
                                            _rf.write(json.dumps(_res, ensure_ascii=False) + "\n")
                                        _wl = globals().get("_WATCHDOG_LAST")
                                        if isinstance(_wl, dict) and _wl.get("sid") == sid and _wl.get("violations"):
                                            _wl["violations"] = max(0, int(_wl["violations"]) - 1)
                                    except Exception:
                                        pass
                                    break
                            except Exception:
                                pass
                    # v948.13 🏓 THE ACCURACY GATE PING-PONG (§3.5) wired live — a judge-route
                    # row the gate HELD gets a bounded re-read (a fresh, independent aicJudge
                    # call) before conceding an honest miss. Persisted tries + a pin on disk
                    # (gate_pingpong.json) so a reel never retries forever; conservative —
                    # judge-route only, appended AFTER the ledger's own selection so it never
                    # crowds out an already-fireable row within the judge cap.
                    try:
                        _pp_path = os.path.join(rd, "gate_pingpong.json")
                        try:
                            with open(_pp_path, encoding="utf-8") as _ppf:
                                _pp_tries = json.load(_ppf) or {}
                        except Exception:
                            _pp_tries = {}
                        _pp_retry, _pp_pinned, _pp_next = _kai_gate_pingpong_plan(_plan, _pp_tries)
                        if _pp_next != _pp_tries:
                            # v1209 — TORN-WRITE class (same fix as _kai_write_report_atomic /
                            # v948.17 Grok P0-3, applied to this sibling persisted file): this
                            # used to be a plain `open(...,'w') + json.dump` — a crash or
                            # exception mid-write leaves gate_pingpong.json truncated. The read
                            # side already swallows a bad parse into `_pp_tries = {}` (silently
                            # forgetting how many tries every held frame has already used), which
                            # defeats the WHOLE POINT of persisting this file (the docstring's own
                            # law: "a reel never retries forever") — a torn write lets an already-
                            # pinned "honest miss, tries maxed" frame get re-queued and re-tried
                            # past its cap after a crash. Reuse the existing atomic helper (it's
                            # generic — any path, any JSON dict) instead of a second bespoke
                            # torn-write bug.
                            _kai_write_report_atomic(_pp_path, _pp_next)
                        if _pp_retry:
                            _have_j = {str(j.get("f") or "") for j in _judge_jobs}
                            for _rj in _pp_retry:
                                _rf = str(_rj.get("f") or "")
                                if _rf and _rf not in _have_j:
                                    _judge_jobs.append({"f": _rj.get("f"), "ts": _rj.get("ts")})
                                    _have_j.add(_rf)
                        if _pp_retry or _pp_pinned:
                            print(f"🏓 KAI gate ping-pong: {len(_pp_retry)} held frame(s) re-queued "
                                  f"for a fresh judge read · {len(_pp_pinned)} pinned (honest miss, "
                                  f"tries maxed)", flush=True)
                    except Exception as _ppe:
                        print(f"⚠ KAI gate ping-pong failed: {_ppe}", flush=True)
                    # 🔬 JUDGE — only ledger-selected tooltip rows (cap applied here)
                    # v946 — default cap 16 (Fable soak: rarely hit 12; fat tooltip reels need headroom)
                    try:
                        _jcap = max(0, int(os.environ.get("TV_KAI_JUDGE_MAX", "16")))
                    except Exception:
                        _jcap = 16
                    # v948.2 — re-read journal so live mid-session judges already posted
                    # are visible; Stage-3 skips ±6s windows already covered (no double vision).
                    try:
                        _post_live_rows = [r for r in _kai_journal_rows() if r.get("sessionId") == sid]
                    except Exception:
                        _post_live_rows = sess_rows
                    for m4 in _judge_jobs[:_jcap]:
                        if w2 is None or os.environ.get("TV_KAI_JUDGE", "1") == "0":
                            break
                        _ff4 = str(m4.get("f") or "")
                        if not _ff4:
                            continue
                        _hp4 = "/hist/reel_" + sid + "/" + _ff4
                        _fid4 = "reel_" + sid + "/" + _ff4.replace(".jpg", "")
                        _fts4 = int(m4.get("ts") or 0)
                        if _judge_already_near(_post_live_rows, _fts4, window_ms=6000):
                            print(f"🔬 KAI judge (ledger): skip {_ff4} — live verdict already near", flush=True)
                            continue
                        # v948.1/v948.2 — aicJudge → aicJudgeApply → /kai_verdict (shared JS)
                        _js4 = _fire_aic_judge_js(_hp4, sid, _fid4, _fts4, live=False)
                        try:
                            _ejs(w2, _js4, timeout=5.0)
                            print(f"🔬 KAI judge (ledger): fired on {_ff4}", flush=True)
                            time.sleep(20.0)   # gentle pacing — the judge is a full vision read
                        except Exception as _je:
                            print(f"⚠ KAI judge fire failed: {_je}", flush=True)
                    # 🏦 VAULT — off by default (v946.7): same icon-grid problem as live driver.
                    # Opt-in TV_KAI_VAULT=1 only when feeding tooltip frames, not raw grids.
                    for _vj in _vault_jobs[:1]:
                        if w2 is None or os.environ.get("TV_KAI_VAULT", "0") == "0":
                            break
                        _ffv = str(_vj.get("f") or "")
                        if not _ffv:
                            continue
                        _hpv = "/hist/reel_" + sid + "/" + _ffv
                        _fidv = "reel_" + sid + "/" + _ffv.replace(".jpg", "")
                        _tabv = "personal"  # vaultIntake is tab-agnostic; journal tab for receipt
                        _jsv = ("(function(){try{var F=document.getElementById('tvd-eng');if(!F||!F.contentWindow)return 0;var W=F.contentWindow;"
                                "if(typeof W.vaultIntake!=='function')return 0;"
                                "fetch(%s+'?'+Date.now()).then(function(r){if(!r.ok)throw 0;return r.blob()}).then(function(b){"
                                "return W.vaultIntake([new W.File([b],'kai-vault.jpg',{type:'image/jpeg'})],{fromTv:true})}).then(function(res){"
                                "try{fetch('/intake_result',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ts:Date.now(),tab:%s,kind:'kai-vault',ok:!!(res&&res.ok),counts:(res&&res.added)||{},total:(res&&res.total)||0,errors:(res&&res.errors)||0,frameId:%s})}).catch(function(){})}catch(e){}"
                                # v948.17 (Grok P0-2 class) — same silent-catch fix as the tally
                                # funnel: a fetch/vaultIntake rejection used to vanish with no
                                # receipt at all. Now an honest error lands.
                                "}).catch(function(_e5){try{fetch('/intake_result',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ts:Date.now(),tab:%s,kind:'kai-vault',ok:false,counts:{},total:0,errors:1,frameId:%s,err:String(_e5&&_e5.message||_e5||'vault fetch/intake rejected')})}).catch(function(){})}catch(e6){}});"
                                "return 1}catch(e){return 0}})()"
                                ) % (json.dumps(_hpv), json.dumps(_tabv), json.dumps(_fidv),
                                     json.dumps(_tabv), json.dumps(_fidv))
                        try:
                            _ejs(w2, _jsv, timeout=5.0)
                            print(f"🏦 KAI vault (ledger): fired {_ffv}", flush=True)
                            time.sleep(8.0)
                        except Exception as _ve:
                            print(f"⚠ KAI vault fire failed: {_ve}", flush=True)
                    # ── v949.x 🧠🔬 SUPER-ANALYZE KAI — Phase B, THE 4TH ORGAN ──
                    # (ENGINE_ARCHITECTURE.md "MASTER BRAIN" layer 4 / ARCH_PINGPONG Q1-hybrid).
                    # Runs LAST in Stage 3, after funnel/judge/vault have had their normal shot —
                    # so "already named" below only fires on frames genuinely nobody named yet.
                    # Reuses the SAME aicJudge→aicJudgeApply→/kai_verdict machinery as the judge
                    # lane (_fire_aic_judge_js) — this is a deep re-read, never a new reader.
                    # LAW: only gate-PROVEN frames (_kai_super_select requires gatePass is True —
                    # the gate already weeded the garbage); never gameplay/boot frames; capped by
                    # TV_KAI_SUPER_MAX so it can never run away.
                    try:
                        if os.environ.get("TV_KAI_SUPER", "1") != "0":
                            try:
                                _super_sess_rows = [r for r in _kai_journal_rows() if r.get("sessionId") == sid]
                            except Exception:
                                _super_sess_rows = sess_rows
                            _fn_super = _kai_fullnames()
                            _super_cands = _kai_super_select(_plan, _super_sess_rows, fullnames=_fn_super)
                            if _super_cands:
                                print(f"🧠🔬 SUPER-ANALYZE: {len(_super_cands)} gate-proven "
                                      f"unread frame(s) queued for a deep re-read "
                                      f"(cap={os.environ.get('TV_KAI_SUPER_MAX', '10')})", flush=True)
                            for _sc in _super_cands:
                                if w2 is None:
                                    break
                                _fs = str(_sc.get("f") or "")
                                if not _fs:
                                    continue
                                _hps = "/hist/reel_" + sid + "/" + _fs
                                _fids = "reel_" + sid + "/" + _fs.replace(".jpg", "")
                                _tss = int(_sc.get("ts") or 0)
                                _t0s = int(time.time() * 1000)
                                _super_attempted.append(_fs)
                                _jss = _fire_aic_judge_js(_hps, sid, _fids, _tss, live=False, tag="super")
                                try:
                                    _ejs(w2, _jss, timeout=5.0)
                                    print(f"🧠🔬 SUPER-ANALYZE: fired deep re-read on {_fs} "
                                          f"(label={_sc.get('label')})", flush=True)
                                except Exception as _sfe:
                                    print(f"⚠ SUPER-ANALYZE fire failed ({_fs}): {_sfe}", flush=True)
                                    continue
                                # bounded wait for the verdict to journal — a real vision read;
                                # never blocks forever (mirrors the funnel receipt-wait shape).
                                # v1201 — CLOCK-SKEW class (same sweep as v1199/v1200): `_t0w`
                                # is used ONLY for this pacing deadline (the journal comparison
                                # a few lines below uses `_t0s`, a separate wall-clock anchor
                                # captured before the fire — untouched, must stay wall-clock).
                                # A clean swap to monotonic: immune to a backward NTP/sleep-wake
                                # jump turning this bounded 40s wait into a multi-minute stall.
                                _landed = None
                                _t0w = time.monotonic()
                                while time.monotonic() - _t0w < 40.0:
                                    time.sleep(5.0)
                                    try:
                                        for _rw in reversed(_kai_journal_rows()[-80:]):
                                            if (_rw.get("lane") == "kai" and _rw.get("mode") == "kai-judge"
                                                    and _rw.get("frameId") == _fids
                                                    and int(_rw.get("completedTs") or 0) >= _t0s):
                                                _landed = _rw
                                                break
                                    except Exception:
                                        _landed = None
                                    if _landed:
                                        break
                                if _landed:
                                    _jd = (_landed.get("kai") or {}).get("judge") or {}
                                    _nm = str(_jd.get("name") or "").strip()
                                    _tier = str(_jd.get("tier") or "") or None
                                    _names = [_nm] if (_nm and _nm.lower() in _fn_super) else []
                                    _super_recovered[_fs] = {"reread": True, "deepNames": _names, "tier": _tier}
                                    print(f"🧠🔬 SUPER-ANALYZE recovered: {_fs} → "
                                          f"{_nm or '(unreadable)'} [{_tier or '?'}]", flush=True)
                                else:
                                    _super_recovered[_fs] = {"reread": True, "deepNames": []}
                                    print(f"🧠🔬 SUPER-ANALYZE: no verdict landed for {_fs} "
                                          f"within budget — honest miss", flush=True)
                    except Exception as _sae:
                        print(f"⚠ SUPER-ANALYZE stage error: {_sae}", flush=True)
                except Exception as _kfe:
                    print(f"⚠ KAI funnel stage error: {_kfe}", flush=True)

                # ── v943 📖 THE REGISTER LEDGER — after watchdog/funnel/judge, compile what the
                # session WITNESSED. Re-read the journal so the judge verdicts that posted during
                # the tooltip stage are counted. Evidence only — no board/grail/chronicle writes.
                # v948.17 (Grok P0-3, 2026-07-21 fast-run soak) — each sub-stage below gets its
                # OWN try/except so one failure (e.g. routing build) can't blank out a sibling
                # that already succeeded (e.g. register), and the report write happens in a
                # `finally` so it ALWAYS runs — whatever subset of register/routing/completeness
                # got computed is what lands on disk, atomically. Before this fix, a raise
                # ANYWHERE in this block skipped the write entirely, leaving the pre-Stage-3
                # scan-only kai_report.json (no routing/register/gate) as the permanent "sealed"
                # artifact — exactly what the forensic soak caught (kai_report missing routing).
                _reg_rows = sess_rows
                _register, _routing, _completeness = [], [], None
                _rcounts, _routed_n = {}, 0
                try:
                    try:
                        _reg_rows = [r for r in _kai_journal_rows() if r.get("sessionId") == sid]
                    except Exception as _rre:
                        print(f"⚠ KAI register re-read failed: {_rre}", flush=True)
                    try:
                        _register = _kai_compile_register(_reg_rows)
                        report["register"] = _register
                    except Exception as _rce:
                        print(f"⚠ KAI register compile failed: {_rce}", flush=True)
                    # v946 — CHRONICLE INBOX propose (review gate; never silent grail write)
                    try:
                        if w2 is not None and _register and os.environ.get("TV_CHRONICLE_PROPOSE", "1") != "0":
                            _items = [{"name": x.get("name"), "firstSeenTs": x.get("firstSeenTs"),
                                       "frameId": x.get("frameId"), "tier": x.get("tier"),
                                       "sessionId": sid, "loc": x.get("loc")}
                                      for x in (_register or [])[:40]]
                            _cjs = ("(function(){try{var F=document.getElementById('tvd-eng');"
                                    "if(!F||!F.contentWindow||typeof F.contentWindow.kaiChroniclePropose!=='function')return 0;"
                                    "var r=F.contentWindow.kaiChroniclePropose(%s);return (r&&r.queued)||0}catch(e){return -1}})()"
                                    ) % json.dumps(_items)
                            _cq = _ejs(w2, _cjs, timeout=4.0)
                            print(f"📖 Chronicle propose: queued={_cq} from {len(_items)} register items", flush=True)
                    except Exception as _cpe:
                        print(f"⚠ Chronicle propose failed: {_cpe}", flush=True)
                    # v944 🚦 — the ROUTING LEDGER rides the same re-read (funnel/judge receipts
                    # are now in the journal, so 'routed' is truthful). Evidence only — no firing.
                    try:
                        _routing = _kai_build_routing(routing_scan, sess_rows, sid, _reg_rows)
                        # v949.x 🧠🔬 SUPER-ANALYZE — stamp the per-frame verdict this organ
                        # produced (Q1-hybrid materialization: EngineFrame.super, written into
                        # kai_report via the atomic writer below). Only rows this pass actually
                        # attempted carry the field — additive/defensive, the gate/HD-art
                        # light-up pattern; every other row is untouched.
                        for _rr in _routing:
                            _sup = _super_recovered.get(str(_rr.get("f") or ""))
                            if _sup is not None:
                                _rr["super"] = _sup
                        report["routing"] = _routing
                        for _rr in _routing:
                            _rcounts[_rr["label"]] = _rcounts.get(_rr["label"], 0) + 1
                        _routed_n = sum(1 for _rr in _routing if _rr.get("routed"))
                    except Exception as _rte:
                        print(f"⚠ KAI routing build failed: {_rte}", flush=True)
                    _super_recovered_names = sorted({nm for _v in _super_recovered.values()
                                                     for nm in (_v.get("deepNames") or [])})
                    if _super_attempted:
                        print(f"🧠🔬 SUPER-ANALYZE: {len(_super_attempted)} deep re-read(s) "
                              f"attempted · {len(_super_recovered_names)} real item(s) recovered "
                              f"({', '.join(_super_recovered_names[:5])})", flush=True)
                    # v948.13 🎞🔗 — FILM ↔ REGISTRATION COMPLETENESS (target #2). _reg_rows is
                    # the freshest re-read of this session's journal, so it already carries the
                    # KAI per-item 'unread' rows appended earlier this same seal pass.
                    try:
                        _completeness = _session_completeness(_reg_rows, frames)
                        report["completeness"] = _completeness
                        print(f"🎞 KAI completeness: {_completeness['reads']} reads · "
                              f"{_completeness['reel_frames']} reel frames · "
                              f"{_completeness['coveragePct']}% covered · "
                              f"{_completeness['dropped']} film drops · "
                              f"{_completeness['unread']} unread", flush=True)
                    except Exception as _cme:
                        _completeness = None
                        print(f"⚠ KAI completeness failed: {_cme}", flush=True)
                    # v949.x 🥷🧠 THE MASTER-BRAIN RECONCILER — Phase C (ARCH_PINGPONG §4 /
                    # §6-Q1-hybrid/Q2-SETTLED). AUTHORITATIVE materialization: _kai_reconcile
                    # is pure (routing/register/sess_rows only); ridden here via
                    # _kai_engine_frame_maps → _kai_build_engine_frames so kai_report.json
                    # carries the per-frame owner/verdict/layers[] array the Engine Room will
                    # render (Phase D/E). Own try/except — a failure here must never blank out
                    # the routing/register/completeness fields the finally below already secured.
                    try:
                        _efmaps = _kai_engine_frame_maps(_routing, _register, _reg_rows)
                        report["engineFrames"] = _kai_build_engine_frames(
                            _routing, _register, _super_recovered, _efmaps)
                        print(f"🥷🧠 KAI reconciler: {len(report['engineFrames'])} engineFrames "
                              f"materialized for {sid}", flush=True)
                    except Exception as _efe:
                        print(f"⚠ KAI engineFrames build failed: {_efe}", flush=True)
                finally:
                    # ATOMIC — always persist whatever fields succeeded above (never nothing).
                    _kai_write_report_atomic(os.path.join(rd, "kai_report.json"), report)
                try:
                    _reg_row = {"ts": _sess_last + 60, "captureTs": _sess_last + 60,
                                "completedTs": int(time.time() * 1000),
                                "lane": "kai", "mode": "kai", "scene": "kai", "names": [],
                                "sessionId": sid, "frameId": "",
                                "kai": {"register": {"count": len(_register),
                                                     "items": _register[:40]},
                                        "routing": {"counts": _rcounts, "routedCount": _routed_n},
                                        **({"completeness": _completeness} if _completeness else {}),
                                        **({"super": {"attempted": len(_super_attempted),
                                                       "recovered": len(_super_recovered_names)}}
                                           if _super_attempted else {})},
                                "note": f"📖 KAI register ledger — {len(_register)} items witnessed · "
                                        f"🚦 {len(_routing)} frames routed-labelled ({_routed_n} fired)"
                                        + (f" · 🎞 {_completeness['coveragePct']}% film-complete "
                                           f"({_completeness['dropped']} drops)" if _completeness else "")
                                        + (f" · 🧠🔬 super-analyze recovered {len(_super_recovered_names)}/"
                                           f"{len(_super_attempted)}" if _super_attempted else "")}
                    with open(os.path.join(HERE, "sessions.jsonl"), "a", encoding="utf-8") as _rf3:
                        _rf3.write(json.dumps(_reg_row, ensure_ascii=False) + "\n")
                    print(f"📖 KAI register: {len(_register)} witnessed · 🚦 routing: {len(_routing)} frames, "
                          f"{_routed_n} fired in {sid}", flush=True)
                except Exception as _rge:
                    print(f"⚠ KAI register/routing stage error: {_rge}", flush=True)
            except Exception as _we:
                print(f"🚨 watchdog: check raised ({_we})", flush=True)
        except Exception:
            time.sleep(10.0)


def _kai_journal_rows():
    """Fresh journal rows for KAI (module-level read; the handler cache is instance-side)."""
    rows = []
    try:
        with open(os.path.join(HERE, "sessions.jsonl"), encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    try:
                        rows.append(json.loads(ln))
                    except Exception:
                        pass
    except Exception:
        pass
    return rows


def _watchdog_check(sid, sess_rows):
    """v935 — 🚨 WATCHDOG v1 (Konyo: 'hardcoded Diablo II safeguards — expected vs happened').
    After a reel seals, assert the session's ground truths and journal a lane:'watchdog' row for
    every breach. GHOST-PROOF like the KAI rows: ts == captureTs, anchored just past the session's
    last row so violations land INSIDE the session span (split_sessions cuts on sid change + ts).
    Rules:
      1) tally-tab-visited-needs-receipt — a tally tab (runes/gems/materials) seen as stashTab on a
         deep read, but NO intake receipt (row with intake.tab == that tab) landed this session.
      2) stash-open-no-tab-reads — a deep read had scene=='stash', yet not one row carried a
         non-empty stashTab (the stash opened but no tab was ever actually read)."""
    rows = sess_rows or []
    now_ms = int(time.time() * 1000)
    _sess_last = max((int(r.get("ts") or 0) for r in rows), default=now_ms)

    visited = set()
    for r in rows:
        if r.get("lane") == "deep":
            tab = str(r.get("stashTab") or "").lower()
            if tab in ("runes", "gems", "materials"):
                visited.add(tab)
    receipts = set()
    for r in rows:
        ik = r.get("intake")
        if isinstance(ik, dict) and ik.get("ok", True):   # v938.3 — a FAILED shot satisfies nothing
            rt = str(ik.get("tab") or "").lower()
            if rt:
                receipts.add(rt)

    violations = []
    for tab in ("runes", "gems", "materials"):
        if tab in visited and tab not in receipts:
            violations.append({
                "rule": "tally-tab-visited-needs-receipt", "tab": tab,
                "note": "🚨 WATCHDOG: %s tab was visited but NO tally receipt landed" % tab})

    stash_opened = any(r.get("lane") == "deep" and str(r.get("scene") or "") == "stash"
                       for r in rows)
    any_tab_read = any(str(r.get("stashTab") or "").strip() for r in rows)
    # v936.2 — rule 3: TEXT-EYE LIVENESS. A busy session (>=6 deep reads) with ZERO
    # text-eye trigger beats means the tooltip lane was dead the whole run — the
    # "20 items shown, 4 reads" class regressing silently. (Trigger beats journal as
    # kind:skip why:'text-eye' since v936.1.)
    _deep_n = sum(1 for r in rows if r.get("lane") == "deep")
    _te_n = sum(1 for r in rows
                if str(r.get("why") or r.get("skip") or "") == "text-eye"
                or "text-eye" in str(r.get("note") or ""))
    _deep_named = any(r.get("lane") == "deep" and (r.get("names") or []) for r in rows)
    if _deep_n >= 6 and _deep_named and _te_n == 0:
        violations.append({
            "rule": "text-eye-silent-all-session", "tab": "",
            "note": "🚨 WATCHDOG: %d reads but the text eye never triggered once — tooltip lane may be dead" % _deep_n})
    if stash_opened and not any_tab_read:
        violations.append({
            "rule": "stash-open-no-tab-reads", "tab": "",
            "note": "🚨 WATCHDOG: stash was opened but no stash tab was ever read"})

    out_rows = []
    for i, v in enumerate(violations):
        _ts = _sess_last + 2 + i
        out_rows.append({"ts": _ts, "captureTs": _ts, "completedTs": now_ms,
                         "lane": "watchdog", "mode": "watchdog", "scene": "watchdog",
                         "names": [], "sessionId": sid, "frameId": "",
                         "watchdog": {"rule": v["rule"], "tab": v["tab"]},
                         "note": v["note"]})
    if out_rows:
        try:
            with open(os.path.join(HERE, "sessions.jsonl"), "a", encoding="utf-8") as f:
                for r in out_rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"🚨 watchdog: journal append failed ({e})", flush=True)

    globals()["_WATCHDOG_LAST"] = {"sid": sid, "violations": len(out_rows)}
    if out_rows:
        print(f"🚨 watchdog: {len(out_rows)} violation(s) for {sid}", flush=True)
    else:
        print(f"🛡 watchdog: clean session {sid}", flush=True)
    return out_rows


# ── v943.4 ENGINE SELF-HEALING (Grok's engine-liveness deferral) ────────────────
# The off-screen engine iframe can wedge (WKWebView occlusion, a JS fault) so every
# liveness probe comes back dead. Rather than sit dark forever, count consecutive dead
# probes and, at the threshold, kick the iframe by re-assigning its own src (a cheap
# reload). Give up loudly after a few tries so a truly dead engine is visible, not looped.
_ENGINE_REVIVE_AT = 5     # consecutive dead probes before a revive attempt
_ENGINE_REVIVE_MAX = 3    # revive attempts per process before declaring hard-dead


def _engine_selfheal(alive, w):
    """Pure counter transition for engine self-healing. A live probe clears the streak;
    a dead one (probe non-1/2 or _ejs None) advances it. At _ENGINE_REVIVE_AT consecutive
    dead probes: revive the iframe once (src=src) and drop the counter to a half-way value
    so a dead revive re-arms after a settle gap, not on the very next loop. After
    _ENGINE_REVIVE_MAX revives: set _ENGINE_DEAD_HARD once and shout to restart the app.
    Testable with w=None (skips the JS kick, keeps the counter/flag logic)."""
    if alive:
        globals()["_ENG_FAILS"] = 0
        return
    fails = globals().get("_ENG_FAILS", 0) + 1
    globals()["_ENG_FAILS"] = fails
    if fails < _ENGINE_REVIVE_AT:
        return
    revives = globals().get("_ENG_REVIVES", 0)
    if revives < _ENGINE_REVIVE_MAX:
        globals()["_ENG_REVIVES"] = revives + 1
        if w is not None:
            try:
                _ejs(w, "(function(){var f=document.getElementById('tvd-eng'); "
                        "if(f){f.src=f.src;return 1} return 0})()", timeout=3.0)
            except Exception:
                pass
        print("🔌 engine revive attempted", flush=True)
        globals()["_ENG_FAILS"] = _ENGINE_REVIVE_AT // 2   # half-way — settle before re-arming
        globals()["_EJS_STUCK"] = 0                         # let the next loop actually re-probe
    elif not globals().get("_ENGINE_DEAD_HARD"):
        globals()["_ENGINE_DEAD_HARD"] = True
        print("🔌 engine DEAD — restart the app", flush=True)


def _engine_driver():
    """v929.2 — control-side auto-intake driver. The off-screen engine window's JS timers
    suspend under WKWebView occlusion, so control watches the bridge itself: on a deep
    stash read with a tally tab (runes/gems/materials → tvStashAutoIntake; personal/shared
    → tvVaultAutoIntake), fire the engine page's LOCKED pipeline via evaluate_js. One shot
    per tab per stash visit (visit resets on a deep non-stash read) — mirrors bible.html's
    own gate. Also a liveness probe every loop so the ENGINE lamp tells the truth.

    v948.2 — LIVE Item Checker queue: deep reads with NEW/MOVED (non-echo, non-tally-tab)
    enqueue aicJudge → aicJudgeApply on the archived hist frame (subscription). Serialized
    with tally fires; paced so post-seal Stage-3 can skip near-ts duplicates."""
    time.sleep(8.0)   # let the window boot + board JS attach
    # v930.2 (Grok r2 P0) — start the cursor at NOW: a cold driver walking the /state ring
    # fired HISTORICAL stash tabs against the CURRENT eye frame (intake always shoots live).
    seen_ts = int(time.time() * 1000)
    visit_done = {}
    fire_q = []       # v931.1 — serialized intake queue (busy-burn fix)
    inflight = None   # the one job whose journal receipt we await
    # v948.2 live judge state
    judge_q = []          # [{fid, ts, sid, names}]
    live_judged = set()   # frameIds already fired (or queued)
    last_judge_ms = 0
    live_judge_n = 0
    try:
        _jlive_max = max(0, int(os.environ.get("TV_KAI_JUDGE_LIVE_MAX", "24")))
    except Exception:
        _jlive_max = 24
    try:
        _jlive_gap = max(5, int(os.environ.get("TV_KAI_JUDGE_LIVE_GAP_S", "18")))
    except Exception:
        _jlive_gap = 18
    _probes_out = 0
    while True:
        try:
            time.sleep(2.0)
            w = globals().get("_MAIN_WIN")
            if w is None:
                continue
            # liveness probe — evaluate_js runs even when timers are throttled
            alive = False
            if globals().get("_EJS_STUCK", 0) >= 3:
                # v930.2 (Grok r2 P0) — leak guard: each timed-out probe leaves a scratch
                # thread blocked in native evaluate_js; a suspended tile must not spawn an
                # unbounded pile. 3 strikes → stop probing until a fire attempt resets.
                globals()["_ENGINE_ALIVE"] = False
                globals()["_ENGINE_READY"] = False
                globals()["_EJS_STUCK"] = max(0, globals()["_EJS_STUCK"] - 0.05)  # slow decay → occasional retry
                _engine_selfheal(False, w)   # v943.4 — a wedged ejs is still a dead probe; keep the revive streak alive
                continue
            try:
                _pv = _ejs(w, "(function(){var f=document.getElementById('tvd-eng');return (f&&f.contentWindow&&f.contentWindow.tvStashAutoIntake)?2:1})()")
                if _pv is None:
                    globals()["_EJS_STUCK"] = globals().get("_EJS_STUCK", 0) + 1
                else:
                    globals()["_EJS_STUCK"] = 0
                alive = _pv in (1, 2, "1", "2")
                globals()["_ENGINE_READY"] = str(_ejs(w, "(function(){var f=document.getElementById('tvd-eng');return (f&&f.contentWindow&&typeof f.contentWindow.tvStashAutoIntake==='function')?1:0})()")) == "1"
                if not alive and globals().get("_ENG_ERR") != repr(_pv):
                    globals()["_ENG_ERR"] = repr(_pv)
                    print(f"🔌 engine probe returned {_pv!r}", flush=True)
            except Exception as _pe:
                globals()["_ENGINE_READY"] = False
                if globals().get("_ENG_ERR") != str(_pe):
                    globals()["_ENG_ERR"] = str(_pe)
                    print(f"🔌 engine probe error: {_pe}", flush=True)
            globals()["_ENGINE_ALIVE"] = bool(alive)
            _engine_selfheal(bool(alive), w)   # v943.4 — engine self-healing streak/revive
            if not alive:
                continue
            try:
                req = urllib.request.Request("http://127.0.0.1:17771/state")
                with urllib.request.urlopen(req, timeout=3) as r:
                    st = json.loads(r.read().decode("utf-8", "replace"))
            except Exception:
                st = {}   # bridge down (agent off / sealed) — no reads, but the inflight
                          # confirm below MUST still run: post-seal receipts land via the
                          # control /intake_result route into the JOURNAL (Grok shell-verdict P0)
            reads = st.get("reads") or []
            # v949.x 🥷🧠 THE MASTER-BRAIN RECONCILER — Phase C, PROVISIONAL LIVE COPY
            # (ARCH_PINGPONG §6-Q2 SETTLED: "provisional live in _engine_driver's 2s loop
            # into an in-memory deque"). Mirrors the _WATCHDOG_LAST/_ENGINE_ALIVE pattern —
            # a bare globals()[...] deque, no new thread, no top-level declaration. This is
            # the CHEAP live guess (_kai_live_routing_row, no OCR sweep/gate); the closer's
            # sealed pass always supersedes it once a reel closes — see
            # _kai_engine_frame_effective (sealed-wins law).
            try:
                _live_deep = [r for r in reads if r.get("lane") == "deep"][-16:]
                if _live_deep:
                    _live_routing = [_kai_live_routing_row(r) for r in _live_deep]
                    _live_rec = {r["f"]: r for r in _kai_reconcile(_live_routing, [], _live_deep)}
                    _efl = globals().get("_ENGINE_FRAMES_LIVE")
                    if _efl is None:
                        _efl = collections.deque(maxlen=16)
                        globals()["_ENGINE_FRAMES_LIVE"] = _efl
                    for _lr in _live_routing:
                        _rc = _live_rec.get(_lr["f"]) or {}
                        _efl.append({"f": _lr["f"], "ts": _lr["ts"], "label": _lr["label"],
                                     "owner": _rc.get("owner"), "verdict": _rc.get("verdict"),
                                     "why": _rc.get("why"), "sealed": False})
            except Exception:
                pass   # provisional guess only — never let it disturb the real driver loop
            for rd in reads:
                ts = max(int(rd.get("completedTs") or 0), int(rd.get("ts") or 0))
                if ts <= seen_ts or rd.get("lane") != "deep" or rd.get("provisional"):
                    continue
                seen_ts = max(seen_ts, ts)
                globals()["_DRV_SEEN"] = globals().get("_DRV_SEEN", 0) + 1
                scene = str(rd.get("scene") or "")
                tab = str(rd.get("stashTab") or "").lower()
                # ── v948.2 LIVE Item Checker — BEFORE stash-only gate ──
                # Inventory / ground / stash tooltips with NEW/MOVED names all queue.
                # Pure tally tabs (runes/gems/materials) are filtered by _live_judge_should_queue.
                if _live_judge_should_queue(rd):
                    _jfid = str(rd.get("frameId") or "").strip()
                    if (_jfid and _jfid not in live_judged
                            and live_judge_n < _jlive_max
                            and len(judge_q) < 16
                            and not any(j.get("fid") == _jfid for j in judge_q)):
                        judge_q.append({
                            "fid": _jfid,
                            "ts": int(rd.get("captureTs") or rd.get("ts") or ts or 0),
                            "sid": str(rd.get("sessionId") or "")[:48],
                            "names": _live_judge_interesting_names(rd)[:8],
                        })
                        # v1205 — reserve so we never double-queue. Bounded (see
                        # _drv_live_judged_reserve) — unbounded growth here is the FUNNEL
                        # analog of engine-read's worker-orphan leak.
                        _drv_live_judged_reserve(live_judged, _jfid)
                        globals()["_DRV_JUDGE_Q"] = globals().get("_DRV_JUDGE_Q", 0) + 1
                if scene != "stash":
                    if visit_done:
                        visit_done = {}
                        fire_q = []   # stale visit's queued shots die with the visit (inflight may still confirm)
                        try:
                            _ejs(w, "(function(){var f=document.getElementById('tvd-eng');if(f&&f.contentWindow){f.contentWindow._vaultAutoDone=false;f.contentWindow._vaultAutoBusy=false}return 1})()", timeout=2.0)
                        except Exception:
                            pass
                    continue
                fid = str(rd.get("frameId") or "")
                # v931.1 (materials busy-burn, Grok r2 called it) — QUEUE, don't burn:
                # a second tab read while an intake holds the page shutter used to eat
                # the visit slot on a silent 'busy'. Tabs now queue and fire one at a
                # time; a slot is marked done only when its result JOURNALS (or after
                # 2 attempts). visit_done value: 'queued' | 'inflight' | True (done).
                key = None
                _vnames = rd.get("names") or []
                if tab in ("runes", "gems", "materials"):
                    key = tab
                elif tab in ("personal", "shared"):
                    # v946.8 — ICON GRID → vaultGridCount (occupied slots), NOT vaultIntake.
                    # Identity vault stays manual/tooltip-only (locked reader untouched).
                    # One count shot per tab per visit (visit_done on vaultcount_<tab>).
                    key = "vaultcount_" + tab
                if key and not visit_done.get(key):
                    visit_done[key] = "queued"
                    fire_q.append({
                        "key": key, "tab": tab, "fid": fid, "tries": 0,
                        "has_names": False,  # count path; identity auto disabled
                        "sid": str(rd.get("sessionId") or ""),  # v1182 — scope the
                        # never-zero PREV lookup to THIS session (mirrors Stage-3's
                        # sessionId filter): his stash persists across sessions, so a
                        # genuine spend-down in a NEW session must still be able to land,
                        # not get stuck forever under a stale prior-session peak.
                    })
                    globals()["_DRV_QUEUED"] = globals().get("_DRV_QUEUED", 0) + 1

            # ── serialized fire loop: one intake in flight, confirm via journal ──
            now_ms = int(time.time() * 1000)
            intk = st.get("intakes") or []
            if inflight:
                # v944.6 — capture the landed intake BODY (not just a bool) so we can
                # decide never-zero re-fire: total==0 / ok==false is a failure signal.
                _tabs = (inflight["tab"],
                         inflight["key"].replace("vaultcount_", "").replace("vault_", ""))
                landed_ik = None
                for i in intk:
                    ik0 = i.get("intake") or {}
                    if (int(i.get("ts") or 0) >= inflight["fired_ms"] - 2000
                            and ik0.get("tab") in _tabs):
                        # prefer matching kind for count jobs
                        if inflight["key"].startswith("vaultcount_") and ik0.get("kind") not in (
                                "vault-count", "vaultcount", None, ""):
                            if ik0.get("kind") == "vault":
                                continue
                        landed_ik = ik0
                        break
                if landed_ik is None:
                    # bridge-blind confirm: receipts that arrived via control's /intake_result
                    try:
                        for r in _kai_journal_rows()[-80:]:
                            ik0 = r.get("intake") or {}
                            if (r.get("lane") == "intake"
                                    and int(r.get("ts") or 0) >= inflight["fired_ms"] - 2000
                                    and ik0.get("tab") in _tabs):
                                if inflight["key"].startswith("vaultcount_") and ik0.get("kind") == "vault":
                                    continue
                                landed_ik = ik0
                                break
                    except Exception:
                        pass
                if landed_ik is not None:
                    # pick the freshest archived frame for this tab (updated picture)
                    try:
                        _fresh = _drv_freshest_tab_fid(
                            inflight["tab"], reads=reads,
                            journal_rows=_kai_journal_rows()[-120:],
                            fallback=inflight.get("fid") or "")
                    except Exception:
                        _fresh = inflight.get("fid") or ""
                    _act, _job = _drv_empty_refire_plan(inflight, landed_ik, _fresh, max_tries=3)
                    if _act == "done":
                        visit_done[inflight["key"]] = True
                        _tot = int((landed_ik or {}).get("total") or 0)
                        print(f"🧰 engine-driver: {inflight['key']} intake journaled ✓ total={_tot}", flush=True)
                        try:
                            _intake_lease_release(inflight.get("key") or "",
                                                 inflight.get("lease_owner") or "engine-driver")
                        except Exception:
                            pass
                        inflight = None
                    elif _act == "refire":
                        # keep the lease across re-fire (same owner renews on next fire claim)
                        fire_q.insert(0, _job)
                        print(f"🚫0️⃣ engine-driver: {inflight['key']} empty/error "
                              f"(ok={landed_ik.get('ok')} total={landed_ik.get('total')}) — "
                              f"re-fire try {_job['tries'] + 1} on frame {_job.get('fid')}", flush=True)
                        globals()["_DRV_REFIRE"] = globals().get("_DRV_REFIRE", 0) + 1
                        inflight = None
                    else:  # giveup
                        visit_done[inflight["key"]] = True
                        print(f"⚠ engine-driver: {inflight['key']} still 0 after "
                              f"{int(inflight.get('tries') or 0) + 1} empty shots — giving up this visit",
                              flush=True)
                        try:
                            _intake_lease_release(inflight.get("key") or "",
                                                 inflight.get("lease_owner") or "engine-driver")
                        except Exception:
                            pass
                        inflight = None
                elif now_ms - inflight["fired_ms"] > 110_000:
                    if inflight["tries"] < 2:
                        inflight["tries"] += 1
                        fire_q.insert(0, inflight)   # retry once
                        print(f"🧰 engine-driver: {inflight['key']} no journal in 110s — retrying", flush=True)
                    else:
                        visit_done[inflight["key"]] = True   # give up, don't loop forever
                        print(f"⚠ engine-driver: {inflight['key']} failed twice — giving up this visit", flush=True)
                        try:
                            _intake_lease_release(inflight.get("key") or "",
                                                 inflight.get("lease_owner") or "engine-driver")
                        except Exception:
                            pass
                    inflight = None
            if not inflight and fire_q:
                job = fire_q.pop(0)
                # v945.6 — claim the tab lease before firing so an open board can't dual-fire
                _owner = "engine-driver"
                # v945.7 (Fable review) — claim by KEY, not tab: the board claims vault as
                # 'vault_<tab>' while the driver's tab is bare 'personal' — mismatched keys made
                # the lease a no-op for vault dual-fire. key is 'vault_personal' / 'runes' — the
                # SAME scheme the board uses, so the lease actually cross-blocks now.
                _cl = _intake_lease_claim(job.get("key") or job.get("tab") or "", _owner)
                if not _cl.get("ok"):
                    # someone else holds it — re-queue later (don't burn the visit)
                    job["tries"] = int(job.get("tries") or 0)
                    fire_q.append(job)
                    print(f"🧰 engine-driver: {job.get('key')} lease held by "
                          f"{_cl.get('holder')} — defer", flush=True)
                    time.sleep(1.0)
                    continue
                job["lease_owner"] = _owner
                # v941.4 (run-3: vault shot ok:false, 0 read) — shots photograph the READ'S
                # ARCHIVED FRAME (/hist/<fid>.jpg), never the live eye: by fire time the
                # player has moved on and a live shot sees gameplay. Same law as the funnel.
                _histp5 = "/hist/" + job["fid"] + ".jpg"
                if job["key"].startswith("vaultcount_"):
                    # v946.8 — COUNT occupied slots via vaultGridCount (kind:gridcount / vault-count)
                    # v1185 — the outer .catch() used to be bare: a rejected promise (network
                    # hiccup on the /hist fetch, vaultGridCount throwing synchronously) vanished
                    # with NO /intake_result POST at all — no honest-miss, no refire signal for
                    # _drv_empty_refire_plan, just gone. Mirrors the Stage-3 KAI funnel's Grok
                    # P0-2 hardening (v948.17): post an honest ok:false receipt on rejection so a
                    # real failure can refire, same as any other empty/error shot.
                    js = ("(function(){try{var F=document.getElementById('tvd-eng');if(!F||!F.contentWindow)return 0;var W=F.contentWindow;"
                          "if(typeof W.vaultGridCount!=='function')return 0;"
                          "fetch(%s+'?'+Date.now()).then(function(r){if(!r.ok)throw 0;return r.blob()}).then(function(b){"
                          "return W.vaultGridCount([new W.File([b],'drv-vault-grid.jpg',{type:'image/jpeg'})],{tab:%s,fromTv:true})}).then(function(res){"
                          "try{fetch('/intake_result',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ts:Date.now(),tab:%s,kind:'vault-count',ok:!!(res&&res.ok),counts:(res&&(res.counts||res.added))||{},total:(res&&res.total)||0,errors:(res&&res.errors)||0,frameId:%s})}).catch(function(){})}catch(e){}"
                          "}).catch(function(_e5){try{fetch('/intake_result',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ts:Date.now(),tab:%s,kind:'vault-count',ok:false,counts:{},total:0,errors:1,frameId:%s,err:String(_e5&&_e5.message||_e5||'vault-count fetch/intake rejected')})}).catch(function(){})}catch(e6){}});"
                          "return 1}catch(e){return 0}})()"
                          ) % (json.dumps(_histp5), json.dumps(job["tab"]), json.dumps(job["tab"]), json.dumps(job["fid"]),
                               json.dumps(job["tab"]), json.dumps(job["fid"]))
                elif job["key"].startswith("vault_"):
                    # identity path (manual/tooltip) — rarely queued by auto now
                    # v1185 — honest-miss receipt on promise rejection (see vaultcount_ above)
                    js = ("(function(){try{var F=document.getElementById('tvd-eng');if(!F||!F.contentWindow)return 0;var W=F.contentWindow;"
                          "if(typeof W.vaultIntake!=='function')return 0;"
                          "fetch(%s+'?'+Date.now()).then(function(r){if(!r.ok)throw 0;return r.blob()}).then(function(b){"
                          "return W.vaultIntake([new W.File([b],'drv-vault.jpg',{type:'image/jpeg'})],{fromTv:true})}).then(function(res){"
                          "try{fetch('/intake_result',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ts:Date.now(),tab:%s,kind:'vault',ok:!!(res&&res.ok),counts:(res&&res.added)||{},total:(res&&res.total)||0,errors:(res&&res.errors)||0,frameId:%s})}).catch(function(){})}catch(e){}"
                          "}).catch(function(_e5){try{fetch('/intake_result',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ts:Date.now(),tab:%s,kind:'vault',ok:false,counts:{},total:0,errors:1,frameId:%s,err:String(_e5&&_e5.message||_e5||'vault fetch/intake rejected')})}).catch(function(){})}catch(e6){}});"
                          "return 1}catch(e){return 0}})()"
                          ) % (json.dumps(_histp5), json.dumps(job["tab"]), json.dumps(job["fid"]),
                               json.dumps(job["tab"]), json.dumps(job["fid"]))
                else:
                    # v1182 — NEVER-ZERO WRITE GUARD, live path. Stage-3's post-seal KAI
                    # funnel (see _tab_best_total / "Grok P0-1" above) got this protection at
                    # v948.17, but THIS fire — the engine-driver's own live tally shot, which
                    # runs on every stash-tab visit during actual play, not just post-seal gap
                    # fill — never did. Its ADJ-subtract is the same SET-style write (subtract
                    # the old count, so the tab ends up AT res.total), so a thin/partial live
                    # photo (tab opened but not fully hovered) landing ok:true with a small
                    # total was free to stomp an already-larger verified tally — the exact
                    # '404 then a funnel says 4' regression Konyo's law forbids, just on the
                    # live path instead of the closer's. Fetch the best REAL total already on
                    # the books for this tab and only let the apply-block run when the fresh
                    # read isn't a regression; a blocked apply still journals an honest receipt
                    # (ok:true, total held at PREV, guardHeld:true) so the driver's own
                    # never-zero re-fire ladder (_drv_empty_refire_plan) sees a real total and
                    # marks the visit done instead of burning retries on a read that was never
                    # going to be applied. PREV is scoped to THIS session (job["sid"], set at
                    # queue time) — mirrors Stage-3's sessionId filter — so a genuine spend-down
                    # in a fresh session isn't stuck forever under a stale prior-session peak.
                    try:
                        _sid5 = str(job.get("sid") or "")
                        _rows5 = ([r for r in _kai_journal_rows() if r.get("sessionId") == _sid5]
                                  if _sid5 else _kai_journal_rows())
                        _prevBestDrv = _tab_best_total(_rows5, job["tab"])
                    except Exception:
                        _prevBestDrv = 0
                    js = ("(function(){try{var F=document.getElementById('tvd-eng');if(!F||!F.contentWindow)return 0;var W=F.contentWindow;"
                          "if(W._stashShutter)return 2;var FN={runes:'runeIntake',gems:'gemIntake',materials:'materialIntake'}[%s];if(typeof W[FN]!=='function')return 0;"
                          "var LSK={runes:'d2r_runeStash',gems:'d2r_gemStash',materials:'d2r_materialStash'}[%s];"
                          "var ADJ={runes:'adjustRuneStash',gems:'adjustGemStash',materials:'adjustMaterialStash'}[%s];"
                          "var PREV=%s;"
                          "var prev={};try{var st0=JSON.parse(W.LSR.getItem(LSK)||'{}');Object.keys(st0).forEach(function(k){prev[k]=parseInt(st0[k],10)||0})}catch(e){}"
                          "fetch(%s+'?'+Date.now()).then(function(r){if(!r.ok)throw 0;return r.blob()}).then(function(b){"
                          "return W[FN]([new W.File([b],'drv-tally.jpg',{type:'image/jpeg'})])}).then(function(res){"
                          "var newTotal=(res&&res.total)||0;var applied=false;"
                          "try{if(res&&res.ok&&(PREV<=0||newTotal>=PREV)){Object.keys(res.added||{}).forEach(function(k){var was=prev[k]||0;if(was>0&&typeof W[ADJ]==='function')W[ADJ](k,-was)});applied=true}}catch(e){}"
                          "try{fetch('/intake_result',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ts:Date.now(),tab:%s,kind:'tally',ok:applied?true:!!(res&&res.ok&&PREV>0),counts:(applied?((res&&res.added)||{}):{}),total:(applied?newTotal:PREV),errors:(res&&res.errors)||0,frameId:%s,guardHeld:!applied&&PREV>0})}).catch(function(){})}catch(e){}"
                          # v1185 — same honest-miss-on-rejection hardening as vaultcount_/vault_
                          # above: a bare .catch() here vanished a rejected fetch/intake with no
                          # /intake_result POST at all — no refire signal, just gone.
                          "}).catch(function(_e5){try{fetch('/intake_result',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ts:Date.now(),tab:%s,kind:'tally',ok:false,counts:{},total:0,errors:1,frameId:%s,err:String(_e5&&_e5.message||_e5||'tally fetch/intake rejected')})}).catch(function(){})}catch(e6){}});"
                          "return 1}catch(e){return 0}})()"
                          ) % (json.dumps(job["tab"]), json.dumps(job["tab"]), json.dumps(job["tab"]),
                               json.dumps(_prevBestDrv), json.dumps(_histp5), json.dumps(job["tab"]), json.dumps(job["fid"]),
                               json.dumps(job["tab"]), json.dumps(job["fid"]))
                try:
                    _ejs(w, js, timeout=4.0)
                    job["fired_ms"] = now_ms
                    visit_done[job["key"]] = "inflight"
                    inflight = job
                    globals()["_DRV_FIRED"] = globals().get("_DRV_FIRED", 0) + 1
                    print(f"🧰 engine-driver: fired {job['key']} (frame {job['fid']}, try {job['tries'] + 1})", flush=True)
                except Exception as e:
                    # v934.3 — a failed fire RE-QUEUES (was popped and lost forever)
                    job["tries"] += 1
                    if job["tries"] < 3:
                        fire_q.append(job)
                    else:
                        visit_done[job["key"]] = True
                        try:
                            _intake_lease_release(job.get("key") or "",
                                                 job.get("lease_owner") or "engine-driver")
                        except Exception:
                            pass
                    print(f"⚠ engine-driver fire failed (try {job['tries']}): {e}", flush=True)
            # ── v948.2/v948.4 LIVE Item Checker fire ──
            # v948.4 — do NOT wait for tally/vaultcount inflight: a slow vaultGridCount
            # was starving live-judge for 1–2min (live soak 18:28). Judges are fire-and-
            # forget on the engine (separate from intake lease); only pace vs last_judge_ms.
            # Stage-3 still skips near-ts duplicates.
            if (judge_q and live_judge_n < _jlive_max
                    and (now_ms - last_judge_ms) >= (_jlive_gap * 1000)
                    and os.environ.get("TV_KAI_JUDGE", "1") != "0"
                    and os.environ.get("TV_KAI_JUDGE_LIVE", "1") != "0"):
                jjob = judge_q.pop(0)
                _jfid2 = str(jjob.get("fid") or "")
                _rel = _hist_frame_rel(_jfid2)
                if not _rel:
                    # frame not archived yet — requeue once briefly
                    jjob["wait"] = int(jjob.get("wait") or 0) + 1
                    if jjob["wait"] < 8:
                        judge_q.append(jjob)
                    else:
                        print(f"🔬 live-judge: drop {_jfid2} — no hist frame", flush=True)
                else:
                    _hpj = "/hist/" + _rel
                    _jsj = _fire_aic_judge_js(
                        _hpj, jjob.get("sid") or "", _jfid2,
                        int(jjob.get("ts") or 0), live=True)
                    try:
                        _ejs(w, _jsj, timeout=5.0)
                        last_judge_ms = now_ms
                        live_judge_n += 1
                        globals()["_DRV_JUDGE_FIRE"] = globals().get("_DRV_JUDGE_FIRE", 0) + 1
                        _nms = ",".join(str(x) for x in (jjob.get("names") or [])[:3])
                        print(f"🔬 live-judge: fired {_jfid2}"
                              + (f" · {_nms}" if _nms else ""), flush=True)
                    except Exception as _lje:
                        print(f"⚠ live-judge fire failed: {_lje}", flush=True)
                        # allow re-queue of same frame once
                        if int(jjob.get("tries") or 0) < 1:
                            jjob["tries"] = 1
                            live_judged.discard(_jfid2)
                            judge_q.append(jjob)
        except Exception as _de:
            globals()["_DRV_ERR"] = str(_de)[:120]   # v934.3 — loop crashes become visible
            time.sleep(3.0)




def _eyes_pulse():
    """v935.11 — truthful badge data: when did the 🔵 verify lane and 🧠 KAI actually
    last act? Derived from the journal (mtime-cached); badges must never claim activity
    they can't prove (Grok shell-verdict #4)."""
    try:
        key = os.path.getmtime(os.path.join(HERE, "sessions.jsonl"))
    except Exception:
        key = None
    c = globals().get("_EYES_CACHE")
    if c and c[0] == key:
        return c[1]
    out = {"verifyTs": 0, "kaiTs": 0, "kaiMissed": None}
    try:
        for r in _kai_journal_rows()[-400:]:
            ln = r.get("lane")
            if ln == "verify":
                out["verifyTs"] = max(out["verifyTs"], int(r.get("completedTs") or r.get("ts") or 0))
            elif ln == "kai":
                out["kaiTs"] = max(out["kaiTs"], int(r.get("completedTs") or r.get("ts") or 0))
                if isinstance(r.get("kai"), dict) and "missedFrames" in r["kai"]:
                    out["kaiMissed"] = r["kai"].get("missedFrames")
    except Exception:
        pass
    globals()["_EYES_CACHE"] = (key, out)
    return out

# ── v948.26 🥷🧠 PHASE D — SURFACE THE LIVE RING (ARCH_PINGPONG §6-Q4 SETTLED) ────────
# The _ENGINE_FRAMES_LIVE deque (filled provisionally by _engine_driver's 2s loop via
# _kai_reconcile — the CHEAP live guess, no OCR sweep/gate) is the console's NOW-CURSOR.
# status_payload() projects it as `liveRing`; the sealed reel's engineFrames always win in
# retro (sealed-wins law, _kai_engine_frame_effective) so the ring is the live cursor ONLY.
_LIVE_RING_TEXT_CAP = 160   # SETTLED Q4 — any raw text (why/OCR/rawHead) HARD-CAPPED; keep the ~1.8s poll lean


def _project_live_ring():
    """Pure/defensive projection of _ENGINE_FRAMES_LIVE for /api/status.

    The deque may not exist yet (cold boot / no deep read has landed) → []. Each live
    EngineFrame is {f, ts, label, owner, verdict, why, sealed:False}; project it as-is and
    HARD-CAP any raw text at _LIVE_RING_TEXT_CAP chars (the settled cap — don't bloat the
    poll). `layers`/rawHead/ocrRaw are absent on the live guess today but capped here too so
    a richer future live frame can't sneak an uncapped blob into the poll. Cheap: the deque
    is already in memory (NOT re-derived from the 897KB journal, per Q4)."""
    dq = globals().get("_ENGINE_FRAMES_LIVE")
    if not dq:
        return []

    def _cap(v):
        return v[:_LIVE_RING_TEXT_CAP] if (isinstance(v, str) and len(v) > _LIVE_RING_TEXT_CAP) else v

    out = []
    for fr in list(dq):
        if not isinstance(fr, dict):
            continue
        row = {"ts": fr.get("ts"), "f": fr.get("f"), "label": fr.get("label"),
               "owner": fr.get("owner"), "verdict": fr.get("verdict"),
               "why": _cap(fr.get("why")), "sealed": bool(fr.get("sealed"))}
        if isinstance(fr.get("layers"), dict):
            row["layers"] = fr["layers"]
        for _k in ("rawHead", "ocrRaw"):
            if fr.get(_k) is not None:
                row[_k] = _cap(fr.get(_k))
        out.append(row)
    return out


def status_payload():
    # v872 (Konyo live: 'STANDBY keeps jumping at me mid session') — one slow ping under game
    # load flipped the whole console to STANDBY/IDLE for a beat. STICKY BRIDGE: a live agent
    # process with a bridge seen in the last 10s stays ON; only a truly dead bridge drops it.
    # v946.2 — NEVER sticky-bridge when the agent process is dead. Stale _BR_CACHE (≤6s) after
    # End Session kept bridge=True → UI stuck on "End Session"/ON AIR until the cache aged out.
    _alive = _agent_alive()
    bridge_now = bool(_BR_CACHE["ping"]) and (time.time() - _BR_CACHE["ts"]) < 6.0 and _alive
    bridge = bool(_alive and (
        bridge_now or (time.time() - globals().get("_BRIDGE_LAST_OK", 0.0)) < 10.0))
    st = _BR_CACHE["st"] if bridge_now else None
    mode = _agent_mode
    if bridge and mode == "off":
        mode = "live"
    # v926.2 SELF-HEAL — never a ghost ON AIR: if the agent process is gone AND the bridge is
    # dead, the session is over regardless of the stale _agent_mode (crash / external kill).
    if not _alive:
        mode = "off"
        bridge = False
        st = None
    if mode != "off" and not bridge and not _alive:
        mode = "off"
    beat = (st or {}).get("beat") or {}
    events = (st or {}).get("events") or []
    tail = []
    for e in events[-8:]:
        tail.append(
            {
                "k": e.get("k", ""),
                "t": (e.get("t") or "")[:100],
                "ts": e.get("ts"),
            }
        )
    # v946 — session health + mind story (journal tail + leases + driver pulse)
    try:
        _jtail = _kai_journal_rows()[-200:]
        _sid_now = ""
        for _r in reversed(_jtail):
            if _r.get("sessionId"):
                _sid_now = str(_r.get("sessionId"))
                break
        _sess_tail = [r for r in _jtail if not _sid_now or r.get("sessionId") == _sid_now][-80:]
        _drv = {"seen": globals().get("_DRV_SEEN", 0), "queued": globals().get("_DRV_QUEUED", 0),
                "fired": globals().get("_DRV_FIRED", 0), "refire": globals().get("_DRV_REFIRE", 0),
                "err": globals().get("_DRV_ERR")}
        _sess_h = _session_health_from_rows(_sess_tail, leases=_intake_lease_status(), driver=_drv)
        _gc = _newest_gate_count()   # v948.12 — accuracy-gate proven/held for the FUNNELS organ
        if _gc:
            _sess_h["gate"] = _gc
        _cn = _newest_completeness()   # v948.13 — film↔registration coverage% (target #2)
        if _cn:
            _sess_h["completeness"] = _cn
    except Exception:
        _sess_h = {"tabs": {}, "leases": {}, "verdict": "idle", "story": [], "tabSummary": {}}
        _drv = {"seen": 0, "queued": 0, "fired": 0, "refire": 0}
    return {
        "ok": True,
        "ver": "v1286",
        "engineAlive": globals().get("_ENGINE_ALIVE"),   # v929.2 — driver-probed truth, not a LS stamp
        "engineReady": globals().get("_ENGINE_READY"),
        "driver": {"seen": _drv.get("seen", 0), "queued": _drv.get("queued", 0),
                   "fired": _drv.get("fired", 0), "refire": _drv.get("refire", 0),
                   "judgeQ": globals().get("_DRV_JUDGE_Q", 0),
                   "judgeFire": globals().get("_DRV_JUDGE_FIRE", 0),
                   "err": globals().get("_DRV_ERR"),
                   "engineDeadHard": bool(globals().get("_ENGINE_DEAD_HARD"))},
        "watchdog": globals().get("_WATCHDOG_LAST"),
        "liveRing": _project_live_ring(),   # v948.26 🥷🧠 Phase D — Master-Brain NOW-CURSOR (provisional; sealed reel engineFrames win in retro)
        "eyes": _eyes_pulse(),
        "sessionHealth": _sess_h,   # v946 — one-glance tabs/lease/verdict/story
        "mindStory": (_sess_h.get("story") or [])[-6:],
        "journalMB": (lambda: round(os.path.getsize(os.path.join(HERE, "sessions.jsonl")) / 1e6, 1) if os.path.isfile(os.path.join(HERE, "sessions.jsonl")) else 0.0)(),
        "platform": "windows" if IS_WIN else ("mac" if sys.platform == "darwin" else sys.platform),
        "shell": "pywebview",
        "mode": ("stopping" if _stop_inflight else mode),
        "agent": mode != "off" and bridge,
        "bridge": bridge,
        "stopping": bool(_stop_inflight),
        "pid": _pid_cached(),
        "capture": bool(IS_WIN and (_read_pid(CAP_PID_PATH) and _pid_alive(_read_pid(CAP_PID_PATH)))),
        "intakeRing": ((st or {}).get("intakes") or [])[-12:],
        "readCount": (
            (st or {}).get("readCount")
            if (st or {}).get("readCount") is not None
            else len((st or {}).get("reads") or [])
        ),
        "area": beat.get("area") or (st or {}).get("area") or "",
        "scene": beat.get("scene") or "",
        "phase": beat.get("phase") or ("live" if bridge else "off"),
        "motion": beat.get("motion"),
        "interest": beat.get("interest") or (st or {}).get("interest"),
        "model": (st or {}).get("model") or "",
        "events": tail,
        "logPath": LOG_PATH,
        "agentPort": AGENT_PORT,
        "controlPort": CONTROL_PORT,
        "captureTarget": (st or {}).get("captureTarget") or {},
        "eyeAgeMs": (st or {}).get("eyeAgeMs", -1),
        "health": (st or {}).get("health") or {},
        "gameOk": (st or {}).get("gameOk", True) if st else True,
        "aiPaused": bool((st or {}).get("aiPaused") or ((st or {}).get("health") or {}).get("aiPaused")),
        "gameMsg": (st or {}).get("gameMsg") or ((st or {}).get("health") or {}).get("gameMsg") or "",
        "captureProc": _capture_health(),
        "bibleVer": _bible_ver(),
        "agentVer": _agent_disk_ver(),  # v1251 — triple-lamp disk stamp
    }


def _agent_disk_ver():
    """v1251 — tv_diablo.VERSION on disk (cheap, ~4KB read)."""
    try:
        with open(os.path.join(HERE, "tv_diablo.py"), encoding="utf-8", errors="replace") as f:
            head = f.read(5000)
        m = re.search(r'VERSION\s*=\s*"(v[\d.]+)"', head)
        return m.group(1) if m else ""
    except Exception:
        return ""


# ── DOCTOR (v801, Grok R7) ─────────────────────────────────────────────────────
# Windows self-diagnosis. Read-mostly, cross-platform, MUST return <2s, and NEVER
# spawns the Claude CLI (claude_probe is a stub). ok == no severity-'block' failure.
# D2R / the agent never have to be running for ok — pin & frame issues are 'warn'.

_BIBLE_VER_CACHE = {"t": 0.0, "v": ""}
def _bible_ver():
    """v816 (Grok R8 #9) — the board's D2R_BUILD id, cached 30s (34k-line file, cheap regex)."""
    now = time.time()
    if now - _BIBLE_VER_CACHE["t"] < 30:
        return _BIBLE_VER_CACHE["v"]
    v = ""
    try:
        with open(os.path.join(REPO, "bible.html"), encoding="utf-8") as f:
            for line in f:
                if "window.D2R_BUILD" in line:
                    m = re.search(r"id:'(v[\d.]+)'", line)
                    if m:
                        v = m.group(1)
                        break   # v816.1 — first MATCHING line, not first mention
    except Exception:
        pass
    _BIBLE_VER_CACHE["t"] = now; _BIBLE_VER_CACHE["v"] = v
    return v


def _app_ver():
    """Doctor's ver mirrors status_payload's stamp (parity-locked to tv_diablo.VERSION)
    so it can never drift from the ship tag — read the literal, spawn nothing."""
    try:
        m = re.search(r'"ver": "(v[\d.]+)"', inspect.getsource(status_payload))
        return m.group(1) if m else "v?"
    except Exception:
        return "v?"


def _sock_open(port, host="127.0.0.1", timeout=0.35):
    """True if something is LISTENING on host:port (localhost, fast, never blocks)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, int(port)))
        return True
    except Exception:
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass


def _chk(cid, ok, severity, detail, fix=None):
    d = {"id": cid, "ok": bool(ok), "severity": severity, "detail": detail}
    if fix and not ok:
        d["fix"] = fix
    return d


def farmgate_payload():
    """GET /api/farmgate (v924, Grok FARM GATE): the ONE-BUTTON acceptance-day preflight.
    Read-only except ONE cheap subscription-lane CLI ping (the only check the default doctor
    is forbidden to run). Contract: {ok, verdict:'GO'|'WARN'|'NO-GO', checks:[...], vers}.
    Never touches capture/prompt/pool — plumbing truth only."""
    import re as _re
    checks = []
    here = os.path.dirname(os.path.abspath(__file__))

    def _stamp(path, pattern):
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                m = _re.search(pattern, f.read())
            return m.group(1) if m else None
        except Exception:
            return None

    # 1) ver_match — RUNNING control ≡ disk control ≡ agent ≡ board. The runtime constant is
    # the only thing that catches an un-restarted app (Grok R4: disk stamps false-green it).
    try:
        vr = status_payload().get("ver")
    except Exception:
        vr = None
    vc = _stamp(os.path.abspath(__file__), r'"ver": "(v[\d.]+)"')
    va = _stamp(os.path.join(here, "tv_diablo.py"), r'VERSION = "(v[\d.]+)"')
    vb = _stamp(os.path.join(os.path.dirname(here), "bible.html"), r"id:'(v[\d.]+)'")
    vers = {"running": vr, "control": vc, "agent": va, "board": vb}
    same = vr is not None and vr == vc == va == vb
    fix1 = ("RESTART the console app (running %s, disk %s)" % (vr, vc)) if (vr and vc and vr != vc)         else "git pull, restart the console app, and ⌘⇧R any open site tab (stale ?cb= kills nights)"
    checks.append(_chk(
        "ver_match", same, "block",
        ("one truth: %s" % vr) if same else "SKEW running=%s disk=%s agent=%s board=%s" % (vr, vc, va, vb),
        fix1))

    # 2) claude CLI present
    env = _env_clean()
    exe = shutil.which("claude", path=env.get("PATH")) or shutil.which("claude")
    checks.append(_chk("claude_cli", bool(exe), "block",
                       exe or "claude CLI not found on PATH",
                       "npm i -g @anthropic-ai/claude-code, then sign in once in a Terminal"))

    # 3) claude AUTH — the one live ping (subscription lane, tiny, hard-capped).
    # v924-R4 (Grok): during ON AIR the live readers already prove the lane — never stack a
    # second `claude -p` on top of a warm pool; the gate belongs BEFORE air.
    if exe and _sock_open(AGENT_PORT):
        checks.append(_chk("claude_auth", True, "warn",
                           "skipped during ON AIR — the live readers already prove the lane (press the gate before air next time)"))
    elif exe:
        try:
            penv = dict(env)
            penv.pop("ANTHROPIC_API_KEY", None)
            penv.pop("ANTHROPIC_AUTH_TOKEN", None)
            pr = subprocess.run([exe, "-p", "reply with only: ok"],
                                capture_output=True, timeout=60, env=penv)
            out = (pr.stdout or b"").decode("utf-8", "replace").strip().lower()
            authed = pr.returncode == 0 and "ok" in out[:40]
            checks.append(_chk("claude_auth", authed, "block",
                               "subscription lane answered" if authed
                               else "CLI answered oddly: %s" % ((pr.stderr or pr.stdout or b"")[-160:].decode("utf-8", "replace")),
                               "run `claude` once in a bare Terminal and finish login"))
        except subprocess.TimeoutExpired:
            checks.append(_chk("claude_auth", False, "block", "CLI ping timed out (60s)",
                               "run `claude` in a bare Terminal — first run may need login/consent"))
        except Exception as e:
            checks.append(_chk("claude_auth", False, "block", "ping error: %s" % str(e)[:120],
                               "run `claude` once in a bare Terminal"))
    else:
        checks.append(_chk("claude_auth", False, "block", "skipped — no CLI", "install the CLI first"))

    # 4) disk — hist flood protection
    try:
        free_gb = shutil.disk_usage(here).free / (1024 ** 3)
        ok_d = free_gb >= 2
        checks.append(_chk("disk", ok_d, "block" if free_gb < 2 else "warn",
                           ("%.1f GB free" % free_gb) if ok_d else ("only %.1f GB free" % free_gb),
                           "clear space — the film + hist need room for a night"))
        if ok_d and free_gb < 8:
            checks.append(_chk("disk_low", False, "warn", "%.1f GB free — fine for one night, watch it" % free_gb))
    except Exception:
        checks.append(_chk("disk", True, "warn", "disk usage unreadable"))

    # 5) D2R process — warn only (he may press the gate before launching the game)
    try:
        pr = subprocess.run(["pgrep", "-if", r"D2R\.exe"], capture_output=True, timeout=5)
        running = pr.returncode == 0 and (pr.stdout or b"").strip()
        checks.append(_chk("d2r_window", bool(running), "warn",
                           "D2R.exe is running" if running else "D2R.exe not running yet",
                           "launch D2R, then press the gate again for a clean GO"))
    except Exception:
        checks.append(_chk("d2r_window", False, "warn", "process check unavailable",
                           "launch D2R before ON AIR"))

    # 6) handshake — only meaningful when the agent is live
    ap = _sock_open(AGENT_PORT)
    if ap:
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/state" % AGENT_PORT, timeout=3) as r:
                okb = r.status == 200
            checks.append(_chk("handshake", okb, "block",
                               "agent bridge answers /state" if okb else "bridge port open but /state failed",
                               "restart ON AIR"))
        except Exception as e:
            checks.append(_chk("handshake", False, "block", "bridge stuck: %s" % str(e)[:80], "restart ON AIR"))
    else:
        checks.append(_chk("handshake", True, "warn", "agent OFF — normal before ON AIR"))

    blocked = [c for c in checks if not c["ok"] and c["severity"] == "block"]
    warned = [c for c in checks if not c["ok"] and c["severity"] == "warn"]
    verdict = "NO-GO" if blocked else ("WARN" if warned else "GO")
    return {"ok": True, "verdict": verdict, "vers": vers, "checks": checks}


def doctor_payload():
    """GET /api/doctor contract: {ok, platform, checks:[{id,ok,severity,detail,fix?}],
    logTail, logPath, ver}. See the DOCTOR banner above for the invariants."""
    checks = []

    # 1) claude CLI on the SAME cleaned PATH the agent boots with
    env = _env_clean()
    exe = shutil.which("claude", path=env.get("PATH")) or shutil.which("claude")
    checks.append(_chk(
        "claude_cli", bool(exe), "block",
        exe or "claude CLI not found on PATH",
        "Install Claude Code CLI and put it on PATH (npm i -g @anthropic-ai/claude-code)"))

    # 2) claude probe — deliberately NOT run: the doctor must never spawn the CLI
    checks.append(_chk("claude_probe", True, "warn",
                       "not probed (doctor never spawns the CLI)"))

    # 3) agent bridge port — OFF is normal, so warn only
    ap = _sock_open(AGENT_PORT)
    checks.append(_chk(
        "port_agent", ap, "warn",
        "listening on 127.0.0.1:%d" % AGENT_PORT if ap
        else "no listener on 127.0.0.1:%d (agent OFF is normal)" % AGENT_PORT))

    # 4) control port — we are answering this very request, so it is up by definition
    checks.append(_chk("port_control", True, "block",
                       "control server up on 127.0.0.1:%d" % CONTROL_PORT))

    # 5) python — reject the Windows Store stub (its python.exe alias breaks child spawns)
    pexe = sys.executable or ""
    pver = "%d.%d.%d" % sys.version_info[:3]
    stub = "WindowsApps" in pexe
    checks.append(_chk(
        "python", bool(pexe) and not stub, "block",
        ("Windows Store stub python: %s" % pexe) if stub
        else "%s (%s)" % (pexe or "unknown", pver),
        "Install real Python from python.org and turn OFF the python.exe 'App execution alias'"))

    # 6) WebView2 runtime (Windows app window). Mac = native WKWebView, always fine.
    if not IS_WIN:
        checks.append(_chk("webview2", True, "block", "n/a (mac uses native WKWebView)"))
    else:
        pv = None
        try:
            import winreg
            key = (r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients"
                   r"\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}")
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key) as k:
                pv, _ = winreg.QueryValueEx(k, "pv")
        except Exception:
            pv = None
        checks.append(_chk(
            "webview2", bool(pv), "block",
            "WebView2 runtime %s" % pv if pv else "WebView2 runtime not found",
            "Install the Microsoft Edge WebView2 Runtime (Evergreen)"))

    # 7) capture loop lamp (Windows only) — reuse the live health probe
    if not IS_WIN:
        checks.append(_chk("capture_proc", True, "warn", "n/a (Windows-only capture loop)"))
    else:
        h = _capture_health()
        checks.append(_chk(
            "capture_proc", h in ("", "LINKED", "RESTARTED"), "warn",
            h or "idle (agent off)",
            "Press RESTART; if it recurs, check capture_win.ps1 and the D2R window"))

    # 8) live frames — freshness only MATTERS (blocks) when we claim to be LIVE
    live = (_agent_mode == "live")
    now = time.time()
    newest, ages = None, []
    for label in ("eye.jpg", "live.bmp"):
        fp = os.path.join(HERE, "frames", label)
        if os.path.isfile(fp):
            age = now - os.path.getmtime(fp)
            ages.append("%s=%.1fs" % (label, age))
            newest = age if newest is None else min(newest, age)
    fresh = newest is not None and newest <= 10
    if live and not fresh:
        checks.append(_chk(
            "live_frames", False, "block",
            ("frames stale: %s" % ", ".join(ages)) if ages else "no eye.jpg / live.bmp while LIVE",
            "Capture is frozen — check the D2R window and capture_win.ps1"))
    else:
        checks.append(_chk(
            "live_frames", True, "warn",
            ", ".join(ages) if ages else "no frames yet (agent off)"))

    # 9) agent bridge heartbeat — OFF is normal, so warn only
    bp = _bridge_ping()
    checks.append(_chk(
        "bridge", bp is not None, "warn",
        "agent bridge responding on :%d" % AGENT_PORT if bp is not None
        else "agent bridge silent (agent OFF is normal)"))

    # 10) stale pid files whose recorded pid is already dead
    stale = []
    for label, p in (("control_agent.pid", PID_PATH), ("control_capture.pid", CAP_PID_PATH)):
        pid = _read_pid(p)
        if pid is not None and not _pid_alive(pid):
            stale.append("%s->pid %d dead" % (label, pid))
    checks.append(_chk(
        "pid_files", not stale, "warn",
        "; ".join(stale) if stale else "no stale pid files",
        "Harmless — STOP then ON rewrites them"))

    # v815 (Grok R8 #8) — can this night be REPLAYED? Frame coverage + id sanity on the
    # journal tail (last ~200 rows): % beats whose hist frame exists, sessionId coverage.
    try:
        _jl = os.environ.get("TV_SESSIONS") or os.path.join(HERE, "sessions.jsonl")   # v877
        _hist = os.path.join(HERE, "frames", "hist")
        rows = []
        if os.path.isfile(_jl):
            with open(_jl, encoding="utf-8") as f:
                for line in f.readlines()[-200:]:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        pass
        if rows:
            with_fid = [r for r in rows if r.get("frameId")]
            have = sum(1 for r in with_fid
                       if os.path.isfile(os.path.join(_hist, str(r["frameId"]) + ".jpg")))
            sid_cov = sum(1 for r in rows if r.get("sessionId"))
            pct = int(100 * have / max(1, len(with_fid)))
            # v840 — always warn-severity so agent OFF nights don't fail the doctor (TestDoctor);
            # detail still shouts missing count. Live ON nights: user sees amber lamp on the UI.
            checks.append(_chk(
                "session_integrity", pct >= 40, "warn",
                "frames %d%% of %d reads · sessionId %d/%d · missing %d" % (
                    pct, len(with_fid), sid_cov, len(rows), max(0, len(with_fid) - have)),
                "v840 journal-shield protects NEW frames; prior nights may stay hollow after the footage flood"))
        else:
            checks.append(_chk("session_integrity", True, "warn", "no journal rows yet"))
    except Exception:
        pass

    # v811 (Grok R8 #6) — journal generation truth: how many rotated nights exist
    try:
        _jroot = os.path.join(HERE, "sessions")
        _gens = [g for g in range(1, 6) if os.path.isfile(_jroot + ".%d.jsonl" % g)]
        _live = os.path.isfile(_jroot + ".jsonl")
        checks.append(_chk("journal_gens", True, "warn",
                           "live=%s gens=%s" % ("yes" if _live else "no",
                                                (",".join(str(g) for g in _gens) or "none"))))
    except Exception:
        pass

    ok = not any((not c["ok"]) and c["severity"] == "block" for c in checks)

    try:
        with open(LOG_PATH, "rb") as f:
            log_tail = f.read()[-2048:].decode("utf-8", "replace")
    except Exception:
        log_tail = "(no log yet)"

    return {
        "ok": ok,
        "platform": "windows" if IS_WIN else ("mac" if sys.platform == "darwin" else sys.platform),
        "checks": checks,
        "logTail": log_tail,
        "logPath": LOG_PATH,
        "ver": _app_ver(),
    }


# ── HTTP ─────────────────────────────────────────────────────────────────────

def _read_ui():
    if os.path.isfile(UI_PATH):
        with open(UI_PATH, "rb") as f:
            return f.read()
    return b"<h1>TV DIABLO control_ui.html missing</h1>"


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"   # v877 (army B#7) — keep-alive: no new TCP+thread per poll
    def log_message(self, fmt, *args):
        pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_art(self, name):
        from urllib.parse import unquote

        rel = unquote(name).split("?", 1)[0].split("#", 1)[0]
        target = os.path.realpath(os.path.join(ART_DIR, rel))
        if not (target == ART_DIR or target.startswith(ART_DIR + os.sep)):
            self._json(403, {"ok": False, "msg": "forbidden"})
            return
        if not os.path.isfile(target):
            self._json(404, {"ok": False, "msg": "not found"})
            return
        ext = os.path.splitext(target)[1].lower()
        ctype = _ART_MIME.get(ext)
        if ctype is None:
            self._json(415, {"ok": False, "msg": "unsupported"})
            return
        try:
            with open(target, "rb") as f:
                data = f.read()
        except Exception as e:
            self._json(500, {"ok": False, "msg": str(e)})
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "public, max-age=86400")
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def _load_journal_cached(self):
        """v879 (army B#5) — theatre endpoints re-parsed every generation file per call.
        Control never appends, so an mtime key is honest HERE (unlike the agent side)."""
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        import replay as _rp
        try:
            d = os.path.dirname(_rp.JOURNAL) or "."
            base = os.path.basename(_rp.JOURNAL)
            key = tuple(sorted(
                (n, os.path.getmtime(os.path.join(d, n)))
                for n in os.listdir(d)
                if n.startswith(base) or (n.startswith("sessions") and n.endswith(".jsonl"))))
        except Exception:
            key = None
        c = globals().setdefault("_JRNL_CACHE", {"key": object(), "rows": None})
        if key is not None and key == c["key"] and c["rows"] is not None:
            return c["rows"]
        rows = _rp.load_journal()
        c["key"], c["rows"] = key, rows
        return rows

    def _theatre_sessions(self):
        """v765 — REPLAY THEATRE: list journaled sessions (newest first) from tv/sessions.jsonl."""
        try:
            if HERE not in sys.path:
                sys.path.insert(0, HERE)
            import replay as _rp
            sessions = _rp.split_sessions(self._load_journal_cached())
            out = []
            for i, sess in enumerate(sessions, 1):
                frames = [r for r in sess if r.get("frameId")
                          and os.path.isfile(os.path.join(HIST_DIR, r["frameId"] + ".jpg"))]
                areas = []
                for r in sess:
                    a = r.get("area")
                    if a and a not in areas:
                        areas.append(a)
                sid = next((r.get("sessionId") for r in sess if r.get("sessionId")), "")
                want = sum(1 for r in sess if r.get("frameId"))
                miss = max(0, want - len(frames))
                _reeln = 0
                _thumb = ""
                try:
                    _rd2 = os.path.join(HIST_DIR, "reel_" + str(sess[0].get("sessionId") or ""))
                    if os.path.isdir(_rd2):
                        # v947.3 — count ONLY film stills f_*.jpg (not tab-crop helpers /
                        # .stash_eye_tab.jpg / other analysis JPEGs that inflated shelf +1)
                        _rfs = sorted(f2 for f2 in os.listdir(_rd2)
                                      if f2.startswith("f_") and f2.endswith(".jpg"))
                        _reeln = len(_rfs)
                        if _rfs:
                            # v890 — the card's art IS the run: its middle frame, 160px lane
                            _thumb = "reel_" + str(sess[0].get("sessionId") or "") + "/" + _rfs[len(_rfs) // 2]
                    elif i == 1 and not any(r3.get("sessionEnd") for r3 in sess):   # v930.1 — `n` was a NameError (loop var is i): the LIVE card silently lost its thumb+count every call
                        # v908 (Grok P1) — the LIVE card pins its thumb to the FIRST loose frame
                        # (a mid frame churns every refresh = flicker)
                        try:
                            _lf = sorted(f4 for f4 in os.listdir(HIST_DIR)
                                         if f4.startswith("f_") and f4.endswith(".jpg"))
                            if _lf:
                                _reeln = len(_lf)
                                _thumb = _lf[0]
                        except Exception:
                            pass
                except Exception:
                    pass
                # v937 — the session's STORY fields: verdicts at a glance (shelf + home digest)
                _wd = sum(1 for r2 in sess if r2.get("lane") == "watchdog")
                _tl = sum(1 for r2 in sess if r2.get("lane") == "intake")
                _km, _kc = None, None
                _thrown = set()
                _keepers = []
                _keeper_info = {}   # v1280 (D7 engine) — lowered-name → {name, frameId, ts} for regret chips
                _registered = None   # v943 — 📖 how many items KAI witnessed this session
                _finds = None        # v1254 R1 — 📖 the ACTUAL items KAI witnessed (card-facing, capped)
                _topFind = None      # v1254 R1 — the single best find (grail else newest) for the shelf teaser
                for r2 in sess:
                    if r2.get("lane") == "kai" and isinstance(r2.get("kai"), dict) and "missedFrames" in r2["kai"]:
                        _km = r2["kai"].get("missedFrames"); _kc = r2["kai"].get("classes")
                    if r2.get("lane") == "kai" and isinstance(r2.get("kai"), dict) and isinstance(r2["kai"].get("register"), dict):
                        _reg = r2["kai"]["register"]
                        _registered = _reg.get("count")
                        # v1254 R1 (WHAT I FOUND) — surface the register ITEMS as premium-card
                        # finds. TRUTHFUL: register only exists on SEALED reels (kaiVer>=3/4);
                        # unswept/old reels have no register dict, so _finds stays null — we NEVER
                        # fabricate. LIGHT: cap at 16 (the /api/sessions payload is polled ~12s;
                        # the total lives in `registered`, so the UI can show "+N more"). Sort
                        # grail/tier-first then newest firstSeenTs so the teaser shows the best.
                        _ritems = _reg.get("items")
                        if isinstance(_ritems, list) and _ritems:
                            _srt = sorted(
                                _ritems,
                                key=lambda it: (-_KAI_TIER_RANK.get((it.get("tier") or ""), 0),
                                                -(it.get("firstSeenTs") or 0)))
                            _finds = [{"name": it.get("name"), "tier": it.get("tier"),
                                       "loc": it.get("loc"), "frameId": it.get("frameId"),
                                       "ts": it.get("firstSeenTs")}
                                      for it in _srt[:16]]
                            _tf = _srt[0]
                            _topFind = {"name": _tf.get("name"), "tier": _tf.get("tier")}
                    for nm2 in (r2.get("thrown_names") or []):
                        _thrown.add(str(nm2).strip().lower())
                    _jd = (r2.get("kai") or {}).get("judge") if isinstance(r2.get("kai"), dict) else None
                    if isinstance(_jd, dict) and _jd.get("tier") == "keep" and _jd.get("name"):
                        _kn = str(_jd["name"]).strip()
                        _keepers.append(_kn.lower())
                        # v1280 (D7 engine) — remember where this keeper was seen (for the regret jump chip)
                        _keeper_info.setdefault(_kn.lower(), {"name": _kn, "frameId": r2.get("frameId"), "ts": r2.get("ts")})
                # v940 💔 — a REGRET = the judge ruled KEEP on something this session threw out
                _regrets = sum(1 for k2 in _keepers if k2 in _thrown)
                # v1280 (D7 engine) — the regret SPOTLIGHT items: each thrown-then-judged-KEEP name, named +
                # frame-located for the jump chip. TRUTHFUL: only names that were BOTH thrown AND ruled keep;
                # dormant (None) when there are no regrets — which is every current session (no thrown_names
                # in the journal yet), so it stays honestly empty until a real regret occurs.
                _regret_items = [_keeper_info[k2] for k2 in dict.fromkeys(_keepers) if k2 in _thrown and k2 in _keeper_info] or None
                # v1253 R1 (DIABLO-LANGUAGE) — richer scene breakdown ALONGSIDE kaiClasses
                # (which collapses to stash/gameplay/tooltip). This tallies the READS' OWN
                # Diablo scene + stashTab straight from the journal, so the shelf/fingerprint
                # can say "transition ×N · stash ×M · gems ×K" in true Diablo language.
                # Additive: kaiClasses stays untouched. Honest: only counts scenes reads made.
                _scene_reads, _tab_reads = {}, {}
                for r2 in sess:
                    if r2.get("lane") != "deep":
                        continue
                    _sc2 = str(r2.get("scene") or "").strip().lower()
                    if _sc2:
                        _scene_reads[_sc2] = _scene_reads.get(_sc2, 0) + 1
                    _tb2 = str(r2.get("stashTab") or "").strip().lower()
                    if _tb2:
                        _tab_reads[_tb2] = _tab_reads.get(_tb2, 0) + 1
                # v1276 (D5 engine) — feed the DECISION-STORY coverage meter + classFrames montage
                # (polish-ui-2's two fields) from the sealed reel's OWN kai_report.json — the reconciled
                # ground truth built at seal time — NOT the journal. Why the report: (a) its `completeness`
                # already matches reads↔film across the two frame namespaces (deep reads reference loose
                # capture frames; the reel archives f_*.jpg stills — a raw journal ratio mixes them and lies);
                # (b) its `classFrames` picks one representative REEL still per real scene, servable in the
                # exact `/hist/reel_<sid>/f_*.jpg` form the shelf thumb already uses. Sealed-reels-ONLY:
                # unswept / live reels have no report → both stay None → the UI's honest-absent contract
                # hides the meter + montage (no fake zeros). coverage = {read, total(=text moments KAI saw),
                # gaps(=text seen-but-unread)} so read/total is the real read-completeness %; omitted when
                # the reel had no item text at all (nothing to report).
                _coverage, _class_frames = None, None
                _super_recovery, _missed_frames = None, None   # v1278 (D6 engine)
                _seal_ms = None   # v1280 (D7 engine)
                _rreport = _reel_report_cached(
                    os.path.join(HIST_DIR, "reel_" + str(sess[0].get("sessionId") or "")))
                if _rreport:
                    _cmp = _rreport.get("completeness")
                    if isinstance(_cmp, dict) and _cmp.get("hovers_estimated"):
                        _cg = _cmp.get("gaps")
                        _coverage = {"read": int(_cmp.get("reads") or 0),
                                     "total": int(_cmp.get("hovers_estimated") or 0),
                                     "gaps": (len(_cg) if isinstance(_cg, list) else int(_cg or 0))}
                    _cfd = _rreport.get("classFrames")
                    if isinstance(_cfd, dict) and _cfd:
                        _sidr = str(sess[0].get("sessionId") or "")
                        _cf = []
                        for _scn, _fr in _cfd.items():
                            if not isinstance(_fr, dict) or not _fr.get("f"):
                                continue
                            _cf.append({"scene": str(_scn).strip().lower(),
                                        "thumb": "reel_" + _sidr + "/" + _fr["f"],
                                        "frameId": str(_fr["f"]).rsplit(".", 1)[0],
                                        "ts": _fr.get("ts")})
                            if len(_cf) >= 6:
                                break
                        _class_frames = _cf or None
                    # v1278 (D6 engine) — super-recovery badge + missed-text drill, from the SAME cached
                    # report (no extra read). A "recovery" = a deeper pass rescued item text the first pass
                    # missed: kai.caughtNames (retro sweep), super.deepNames (deep re-read),
                    # second.correctedNames (second-eye correction). The report `missed` ledger is the text
                    # that stayed UNREAD (final gaps) — disjoint from recoveries. So total-missed (the badge's
                    # M) = recovered + still-unread, and recovered/M is the true rescue rate. missedFrames =
                    # ≤24 rows for the drill: recovered frames carry their rescued name as `label`; still-
                    # unread frames omit `label` (UI shows "— unreadable text —"). frameId+ts power jump.
                    _mf_list, _recov = [], 0
                    _eframes = _rreport.get("engineFrames")
                    if isinstance(_eframes, list):
                        for _ef in _eframes:
                            _lay = _ef.get("layers") or {}
                            _rescued = [n for n in (
                                list(((_lay.get("kai") or {}).get("caughtNames")) or [])
                                + list(((_lay.get("super") or {}).get("deepNames")) or [])
                                + list(((_lay.get("second") or {}).get("correctedNames")) or [])) if n]
                            if _rescued:
                                _recov += 1
                                if len(_mf_list) < 24:
                                    _mf_list.append({"frameId": str(_ef.get("f") or "").rsplit(".", 1)[0],
                                                     "ts": _ef.get("ts"), "label": _rescued[0]})
                    _missed = _rreport.get("missed")
                    _still = len(_missed) if isinstance(_missed, list) else 0
                    if isinstance(_missed, list):
                        for _ms in _missed:
                            if len(_mf_list) >= 24:
                                break
                            _mf_list.append({"frameId": str(_ms.get("f") or "").rsplit(".", 1)[0],
                                             "ts": _ms.get("ts")})
                    _total_missed = _recov + _still
                    if _total_missed > 0:
                        _super_recovery = {"recovered": _recov, "missed": _total_missed}
                    if _mf_list:
                        _mf_list.sort(key=lambda x: x.get("ts") or 0)
                        _missed_frames = _mf_list[:24]
                    # v1280 (D7 engine) — seal-latency: closedAt − run-end. TRUTHFUL guard: a re-swept reel's
                    # closedAt lands hours/days after the run (a reseal, NOT a seal latency), so only emit when
                    # the gap is plausibly a real seal (>0 and ≤30min); otherwise leave it absent (the chip hides).
                    _ca = _rreport.get("closedAt")
                    if isinstance(_ca, (int, float)):
                        _rend = None
                        if isinstance(_eframes, list) and _eframes:
                            _rend = max((f.get("ts") or 0) for f in _eframes)
                        if not _rend:
                            _rend = sess[-1].get("ts")
                        if _rend:
                            _dlt = int(_ca) - int(_rend)
                            if 0 < _dlt <= 30 * 60 * 1000:
                                _seal_ms = _dlt
                out.append({"watchdogViolations": _wd, "tallies": _tl, "kaiMissed": _km, "kaiClasses": _kc,
                            "sceneReads": _scene_reads or None, "tabReads": _tab_reads or None,
                            "judged": len(_keepers), "regrets": _regrets, "registered": _registered,
                            "finds": _finds, "topFind": _topFind,   # v1254 R1 — 📖 what KAI witnessed this session
                            "coverage": _coverage, "classFrames": (_class_frames or None),   # v1276 (D5 engine) — decision-story meter + montage
                            "superRecovery": _super_recovery, "missedFrames": _missed_frames,   # v1278 (D6 engine) — recovery badge + missed-text drill
                            "sealMs": _seal_ms, "regretItems": _regret_items,   # v1280 (D7 engine) — seal-latency chip + regret spotlight
                            "n": i, "t0": sess[0].get("ts"), "t1": sess[-1].get("ts"),
                            "reads": len([r2 for r2 in sess if not r2.get("sessionEnd") and r2.get("scene") != "session_end" and r2.get("mode") != "session_end" and r2.get("kind") != "skip" and r2.get("lane") not in ("kai", "verify", "intake")]), "frames": len(frames),
                            "named": sum(1 for r in sess if r.get("names")),
                            "areas": areas[:6], "stub": (len([r2 for r2 in sess if not r2.get("sessionEnd") and r2.get("scene") != "session_end" and r2.get("mode") != "session_end" and r2.get("kind") != "skip"]) < 3
                             and _reeln == 0),   # v885 (Grok #1) — a 1-read ghost never poses as a run
                    "footageN": _reeln,   # v883 — the shelf tells the truth about video
                    "intakes": len([r2 for r2 in sess if r2.get("lane") == "intake"]),   # v902
                    "thumb": _thumb,      # v890 — HD filmstrip art from the run itself
                    "sessionId": sid,
                            # v840 — SIM honesty: how much of the night is still replayable
                            "frameWant": want, "frameMissing": miss,
                            "archiveOk": miss == 0 and len(frames) > 0})
            return out
        except Exception as e:
            return {"error": str(e)}

    def _thin_footage_beats(self, beats, step_ms=400, near_ms=3000):
        """v894 — server-side film thin: keep all AI reads; quiet film ~2.5fps wall; dense near reads.
        This is the SIM engine fix — not a client 2× button."""
        if len(beats) < 50:
            return beats
        read_ts = sorted(
            int(b.get("ts") or 0)
            for b in beats
            if not b.get("footage") and not b.get("skip")
        )
        def _near(ts):
            for rt in read_ts:
                if abs(rt - ts) <= near_ms:
                    return True
                if rt > ts + near_ms:
                    break
            return False
        out, last_f = [], -10**15
        for b in beats:
            if not b.get("footage"):
                out.append(b)
                continue
            ts = int(b.get("ts") or 0)
            if _near(ts) or (ts - last_f) >= step_ms:
                out.append(b)
                last_f = ts
        return out if len(out) >= 2 else beats

    def _prewarm_session_frames(self, beats, limit=48, width="960"):
        """v894 — build theatre derivatives in the background so play doesn't block on sips."""
        if IS_WIN:
            return
        paths = []
        for b in beats:
            fr = b.get("frame") or ""
            if fr and fr.endswith(".jpg"):
                paths.append(fr)
            if len(paths) >= limit:
                break
        if not paths:
            return

        def _run():
            cache_dir = os.path.join(HIST_DIR, "cache" + width)
            try:
                os.makedirs(cache_dir, exist_ok=True)
            except Exception:
                return
            for fr in paths:
                try:
                    src = os.path.join(HIST_DIR, fr)
                    # reel_ paths are under HIST_DIR
                    if not os.path.isfile(src):
                        continue
                    base = os.path.basename(fr)
                    cached = os.path.join(cache_dir, base)
                    if os.path.isfile(cached):
                        continue
                    subprocess.run(
                        ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "68",
                         "--resampleHeightWidthMax", width, src, "--out", cached],
                        capture_output=True, timeout=8,
                    )
                except Exception:
                    pass
        threading.Thread(target=_run, daemon=True, name="tvd-prewarm-sess").start()

    def _theatre_session(self, n, pack="debug"):
        """v895 — personal visual debugger for one ON AIR session.
        pack=debug|raw: every footage frame + every AI read, capture-clock ordered (default).
        pack=fast: server-thinned quiet film (optional zip mode — not the debugger default)."""
        try:
            if HERE not in sys.path:
                sys.path.insert(0, HERE)
            import replay as _rp
            sessions = _rp.split_sessions(self._load_journal_cached())
            if n < 1 or n > len(sessions):
                return {"error": "no such session"}
            sess = sessions[n - 1]
            beats = []
            for r in sess:
                if r.get("lane") == "intake":
                    # v902 — 📸 intake beat: the library shows what the locked pipeline did,
                    # time-synced to the frame the shot came from
                    _ifid = str(r.get("frameId") or "")
                    _ifr = _hist_frame_rel(_ifid)   # v940.4 — resolve #v / reel paths
                    beats.append({"ts": int(r.get("ts") or 0), "captureTs": int(r.get("ts") or 0),
                                  "intakeBeat": True, "intake": r.get("intake") or {},
                                  "note": r.get("note") or "", "frameId": _ifid,
                                  "frame": _ifr, "frameOk": bool(_ifr),   # v908-R6 — the film paints the SHOT
                                  "names": [], "scene": "intake", "area": "", "lane": "intake"})
                    continue
                if r.get("kind") == "skip":
                    beats.append({"ts": int(r.get("ts") or 0), "captureTs": int(r.get("ts") or 0),
                                  "skip": True, "why": r.get("why") or "", "note": r.get("note") or "",
                                  "names": [], "scene": "", "area": "", "lane": "skip"})
                    continue
                if r.get("scene") == "session_end" or r.get("mode") == "session_end":
                    continue   # v894 — seal rows are not playable beats
                fid = r.get("frameId") or ""
                # v940.4 — frameOk must resolve verify suffix (#v) and reel-relative ids.
                # Exact fid+'.jpg' lied "photo pruned" for every second-eye beat.
                _frel = _hist_frame_rel(fid)
                has = bool(_frel)
                fts = None
                if fid and "_" in str(fid):
                    try:
                        fts = int(str(fid).split("#", 1)[0].rsplit("_", 1)[-1])
                    except Exception:
                        fts = None
                if r.get("captureTs"):
                    cap_ts = int(r["captureTs"])
                elif fts is not None:
                    raw_ts = int(r.get("ts") or 0)
                    if raw_ts and abs(raw_ts - fts) > 2000:
                        cap_ts = fts
                    else:
                        cap_ts = raw_ts or fts
                else:
                    cap_ts = r.get("ts")
                done_ts = r.get("completedTs") or r.get("ts") or cap_ts
                # v894 — lean beat only (forensics via /api/beat). Smaller JSON = faster open.
                beats.append({
                    "ts": cap_ts,
                    "captureTs": cap_ts,
                    "completedTs": done_ts,
                    "n": r.get("n"), "scene": r.get("scene", ""),
                    "area": r.get("area", ""), "names": r.get("names", []),
                    "note": (r.get("note") or "")[:120],
                    "frame": _frel if has else "",
                    "frameId": fid,
                    "frameOk": has,
                    "sessionId": r.get("sessionId") or "",
                    "ms": r.get("ms", 0), "lane": r.get("lane", ""),
                    "model": r.get("model", ""),
                    "vault_names": r.get("vault_names") or [],
                    "pending_names": r.get("pending_names") or [],
                    "thrown_names": r.get("thrown_names") or [],
                    "discovered_names": r.get("discovered_names") or [],
                    "intent": r.get("intent", ""), "stashTab": r.get("stashTab", ""),
                    "farewell": bool(r.get("farewell")),
                    "ocr_names": r.get("ocr_names") or [],
                    "ocr_ms": r.get("ocr_ms") or 0,
                    "names_loc": r.get("names_loc") or {},
                    "sockets": r.get("sockets") or {},   # v946.5 — per-item socket count for the theatre
                    "equipped_names": r.get("equipped_names") or [],
                    "lean": True,
                    "dispatch": {k: (r.get("dispatch") or {}).get(k)
                                 for k in ("origin", "readerId")
                                 if (r.get("dispatch") or {}).get(k) is not None},
                    "confirmed_names": r.get("confirmed_names") or [],
                    "ocr_seeded": r.get("ocr_seeded") or [],
                    "conf": r.get("conf"),
                    "sim": bool(r.get("sim")),
                })
            # Footage interleave — prefer sealed reel; never double-scan loose hist when reel exists
            try:
                _sid0 = str(sess[0].get("sessionId") or "")
                try:
                    _boot_ms = int(_sid0.split("_")[1]) if _sid0.startswith("s_") else 0
                except Exception:
                    _boot_ms = 0
                t0f = (_boot_ms or (sess[0].get("ts") or 0)) - 2000
                _sealed = any(
                    r2.get("sessionEnd")
                    or r2.get("scene") == "session_end"
                    or r2.get("mode") == "session_end"
                    for r2 in sess
                )
                _is_newest = (n == 1)
                t1f = int(time.time() * 1000) if (not _sealed and _is_newest) else ((sess[-1].get("ts") or 0) + 2000)
                hist_dir = HIST_DIR
                sid_here = (sess[0].get("sessionId") or "")
                _reel_dir = os.path.join(hist_dir, "reel_" + sid_here) if sid_here else ""
                _reel_ok = _reel_dir and os.path.isdir(_reel_dir)
                _foot = []
                if _reel_ok:
                    # v894 — index.json first (O(n) no re-stat name parse thrash when present)
                    _idxp = os.path.join(_reel_dir, "index.json")
                    _frames = None
                    if os.path.isfile(_idxp):
                        try:
                            with open(_idxp, encoding="utf-8") as _jf:
                                _frames = (json.load(_jf) or {}).get("frames") or []
                        except Exception:
                            _frames = None
                    if _frames is None:
                        _frames = []
                        for fn in os.listdir(_reel_dir):
                            if fn.startswith("f_") and fn.endswith(".jpg"):
                                try:
                                    _frames.append({"f": fn, "ts": int(fn[2:-4])})
                                except Exception:
                                    pass
                        _frames.sort(key=lambda x: x.get("ts") or 0)
                    pref = "reel_" + sid_here + "/"
                    # v944/v947.2 🚦 — full routing row + KAI missed texts onto each film still
                    _routemap = {}   # f -> full routing dict
                    _kai_miss = {}   # f -> texts[]
                    _engmap = {}     # v948.26 🥷🧠 f -> materialized EngineFrame (owner/verdict/why/layers)
                    try:
                        _krp = os.path.join(_reel_dir, "kai_report.json")
                        if os.path.isfile(_krp):
                            with open(_krp, encoding="utf-8") as _krf:
                                _krep = json.load(_krf) or {}
                            for _rr in (_krep.get("routing") or []):
                                _routemap[str(_rr.get("f") or "")] = _rr
                            for _mm in (_krep.get("missed") or []):
                                _kai_miss[str(_mm.get("f") or "")] = list(_mm.get("texts") or [])[:8]
                            # v948.26 🥷🧠 PHASE D — the Master-Brain reconciler's SEALED verdict.
                            # engineFrames rides kai_report only on reels sealed by a Phase-C+
                            # closer; older reels have no `engineFrames` key → _engmap stays {}
                            # → beats carry no `engineFrame` → the UI no-ops (gate/HD-art
                            # light-up pattern). This is what swaps the Engine Room drill-down's
                            # "owns the final read" from INFERRED to AUTHORITATIVE.
                            for _ef in (_krep.get("engineFrames") or []):
                                _engmap[str(_ef.get("f") or "")] = _ef
                    except Exception:
                        _routemap, _kai_miss, _engmap = {}, {}, {}
                    # sticky journal tab on every film beat
                    _stash_times = []
                    for _r3 in sess:
                        if _r3.get("lane") == "deep" and _r3.get("stashTab"):
                            try:
                                _stash_times.append((int(_r3.get("captureTs") or _r3.get("ts") or 0),
                                                     str(_r3.get("stashTab") or "").lower()))
                            except Exception:
                                pass
                    for it in _frames:
                        fn = it.get("f") or ""
                        fts = int(it.get("ts") or 0)
                        if not fn:
                            continue
                        _rr = _routemap.get(fn) or {}
                        _lbl = _rr.get("label")
                        _rv = _rr.get("routed") or _rr.get("skipReason")
                        _stab = _kai_sticky_tab(fts, _stash_times) or _rr.get("stashTab") or ""
                        if not _lbl or _lbl in ("gameplay", "stash"):
                            if _stab in ("runes", "gems", "materials"):
                                _lbl = "stash-" + _stab
                            elif _stab in ("personal", "shared") and not _lbl:
                                _lbl = "stash"
                        _fid_reel = pref + fn[:-4]
                        # v948.26 🥷🧠 PHASE D — attach the SEALED EngineFrame verdict, keyed by
                        # the same bare `f` routing/engineFrames use. `sealed:True` is the
                        # honest sealed-wins mark (mirrors _kai_engine_frame_effective): a
                        # materialized reel EngineFrame is AUTHORITATIVE for its frame; the live
                        # ring (status_payload) never reaches a retro beat — it's the now-cursor
                        # only. Present only when engineFrames covers this frame; absent-safe.
                        _efb = _engmap.get(fn)
                        _engine_frame = None
                        if _efb:
                            _engine_frame = {"owner": _efb.get("owner"), "verdict": _efb.get("verdict"),
                                             "why": _efb.get("why"), "layers": _efb.get("layers"),
                                             # v1253 R1 — the read's true Diablo scene rides the
                                             # sealed EngineFrame out to the Theatre (retro sync).
                                             "scene": _efb.get("scene"), "tab": _efb.get("tab"),
                                             "area": _efb.get("area"),
                                             "sealed": True}
                        # pre-seed KAI miss texts into maps via beat fields for dossier
                        _foot.append({
                            "ts": fts, "captureTs": fts, "footage": True,
                            "frame": pref + fn, "frameId": _fid_reel,
                            "names": [],
                            # v1253 R1 (DIABLO-LANGUAGE) — a film still had no scene of its own
                            # (only the collapsed routing label), so a portal/loading beat read
                            # as blank. Prefer the sealed EngineFrame's TRUE read scene/area
                            # (transition/town/loot/…); fall back to the old label-derived stash
                            # hint only when no read scene covers this frame. Additive + honest.
                            "scene": (_efb.get("scene") if _efb and _efb.get("scene")
                                      else ("stash" if str(_lbl or "").startswith("stash") else "")),
                            "tab": (_efb.get("tab") if _efb else None),
                            "area": (_efb.get("area") if _efb and _efb.get("area") else ""),
                            "lane": "footage",
                            "label": _lbl, "routeVerdict": _rv,
                            "route": _rr.get("route"),
                            "routed": _rr.get("routed"),
                            "routeSources": list(_rr.get("sources") or []),
                            "routeConf": _rr.get("confidence"),
                            # v948.12 — accuracy-gate verdict rides the beat so the theatre can
                            # show WHY a frame was routed or held (the mirror closes the gate loop)
                            "gatePass": _rr.get("gatePass"),
                            "gateReason": _rr.get("gateReason"),
                            "gateSources": list(_rr.get("gateSources") or []),
                            "eyeSources": list(_rr.get("eyeSources") or []),
                            "stashTab": _stab or "",
                            "kaiMissTexts": _kai_miss.get(fn) or [],
                            **({"engineFrame": _engine_frame} if _engine_frame else {}),
                        })
                elif os.path.isdir(hist_dir):
                    # live/unsealed fallback only
                    for fn in os.listdir(hist_dir):
                        if not (fn.startswith("f_") and fn.endswith(".jpg")):
                            continue
                        try:
                            fts = int(fn[2:-4])
                        except Exception:
                            continue
                        if t0f <= fts <= t1f:
                            _foot.append({"ts": fts, "captureTs": fts, "footage": True,
                                          "frame": fn, "frameId": fn[:-4], "names": [],
                                          "scene": "", "area": "", "lane": "footage"})
                beats.extend(_foot)
            except Exception:
                pass

            def _photo_clock(b):
                fid = b.get("frameId") or ""
                if "_" in str(fid):
                    try:
                        return int(str(fid).rsplit("_", 1)[1])
                    except Exception:
                        pass
                return b.get("ts") or 0
            for b in beats:
                pc = _photo_clock(b)
                if pc and abs(pc - (b.get("ts") or 0)) > 1500:
                    b["ts"] = pc
            # v895 — capture-clock order; same-ms: film first then AI read (annotation sits on that moment)
            beats.sort(key=lambda b: (
                _photo_clock(b),
                0 if b.get("footage") else (1 if not b.get("skip") else 2),
                b.get("n") or 0,
            ))
            # v895 — DEBUGGER default keeps every frame. Only pack=fast thins quiet film.
            if pack == "fast":
                beats = self._thin_footage_beats(beats, step_ms=400, near_ms=3000)
            # v941 THE DOSSIER — hang all three eyes on each read/footage beat.
            # Maps built ONCE from this session's rows; join is O(1)/O(log n) per beat.
            try:
                _dmaps = _build_dossier_maps(sess)
                for b in beats:
                    if b.get("footage") or b.get("lane") == "deep":
                        b["dossier"] = _beat_dossier(_dmaps, b)
            except Exception:
                pass
            sid = next((r.get("sessionId") for r in sess if r.get("sessionId")), "")
            # prewarm early frames (1280 theatre) so scrub/play is not sips-bound
            try:
                self._prewarm_session_frames(beats, limit=80, width="1280")
            except Exception:
                pass
            n_read = sum(1 for b in beats if not b.get("footage") and not b.get("skip"))
            n_foot = sum(1 for b in beats if b.get("footage"))
            return {
                "n": n, "beats": beats, "sessionId": sid,
                "pack": "debug" if pack != "fast" else "fast",
                "modeHint": "real",   # client: wall-clock debugger default
                "stats": {"reads": n_read, "footage": n_foot, "beats": len(beats)},
                "t0": beats[0].get("ts") if beats else sess[0].get("ts"),
                "t1": beats[-1].get("ts") if beats else sess[-1].get("ts"),
            }
        except Exception as e:
            return {"error": str(e)}

    def _serve_hist(self, name):
        """Serve an archived session frame (tv/frames/hist) — path-safe, jpg only.
        v799 (Grok R6 trap 2) — ?w=1280 serves a disk-cached theatre derivative: a decoded
        2560px JPEG is ~14MB RGBA in the WebView; playback at 4x on full frames = memory death.
        Full 2560 stays one click away (forensics 'open original')."""
        from urllib.parse import unquote, urlparse, parse_qs
        # v820 — the do_GET router strips "?" before routing; the query lives on self.path
        qs = parse_qs(urlparse(self.path).query or "")
        rel = unquote(name).split("?", 1)[0].split("#", 1)[0]
        target = os.path.realpath(os.path.join(HIST_DIR, rel))
        if not target.startswith(os.path.realpath(HIST_DIR) + os.sep) or not target.endswith(".jpg"):
            self._json(403, {"ok": False}); return
        if not os.path.isfile(target):
            self._json(404, {"ok": False}); return
        want_w = (qs.get("w") or [""])[0]
        if want_w in ("1280", "160") and not IS_WIN:   # v802 — 160 = scrub thumbnails
            cache_dir = os.path.join(HIST_DIR, "cache" + want_w)
            cached = os.path.join(cache_dir, os.path.basename(target))
            try:
                if not os.path.isfile(cached):
                    os.makedirs(cache_dir, exist_ok=True)
                    r = subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "72",
                                        "--resampleHeightWidthMax", want_w, target, "--out", cached],
                                       capture_output=True, timeout=10)
                    if r.returncode != 0 or not os.path.isfile(cached):
                        cached = target
                target = cached
            except Exception:
                pass
        try:
            with open(target, "rb") as f:
                data = f.read()
        except Exception:
            self._json(500, {"ok": False}); return
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "public, max-age=31536000, immutable")   # v799 — frameId is content-addressed
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html", "/ui"):
            body = _read_ui()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/api/status":
            self._json(200, status_payload())
            return
        if path.startswith("/art/"):
            self._serve_art(path[len("/art/") :])
            return
        if path in ("/board", "/board/"):
            # v774 🌙 — THE APP HOSTS THE BOARD: serve the local bible.html same-origin so the
            # native window lives on ONE http origin (no more file:// localStorage split for
            # app users). Engines are never forked — this IS the board.
            try:
                with open(BIBLE, "rb") as f:
                    body = f.read()
            except Exception:
                self._json(404, {"ok": False, "msg": "bible.html missing"})
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body)
            return
        if path.startswith("/tv/frames/hist/"):
            # the board's theatre fallback path resolves same-origin too
            self._serve_hist(path[len("/tv/frames/hist/"):])
            return
        if path == "/api/sessions":
            self._json(200, {"sessions": self._theatre_sessions()})
            return
        if path == "/api/reel_path":
            # v946.2 — physical film folder for a theatre session (Finder open + path toast)
            try:
                from urllib.parse import parse_qs, urlparse
                q = parse_qs(urlparse(self.path).query)
                sid = (q.get("sid") or [""])[0].strip()
                n = 1
                try:
                    n = max(1, int((q.get("n") or ["1"])[0]))
                except Exception:
                    n = 1
                if not sid:
                    sess = self._theatre_sessions()
                    if 1 <= n <= len(sess):
                        sid = str(sess[n - 1].get("sessionId") or "")
                if not sid:
                    self._json(200, {"ok": False, "msg": "no session id"})
                    return
                # reel_s_<sid> or reel_<sid>
                cand = [
                    os.path.join(HIST_DIR, "reel_" + sid),
                    os.path.join(HIST_DIR, "reel_s_" + sid) if not sid.startswith("s_") else "",
                    os.path.join(HIST_DIR, "reel_" + sid.lstrip("s_")),
                ]
                # common form: reel_s_1784612879156_96017 when sid is s_1784612879156_96017
                if sid.startswith("s_"):
                    cand.insert(0, os.path.join(HIST_DIR, "reel_" + sid))
                path_out = ""
                for c in cand:
                    if c and os.path.isdir(c):
                        path_out = os.path.realpath(c)
                        break
                if not path_out:
                    # scan hist for reel_* containing sid digits
                    try:
                        for name in os.listdir(HIST_DIR):
                            if name.startswith("reel_") and sid.replace("s_", "") in name:
                                p = os.path.join(HIST_DIR, name)
                                if os.path.isdir(p):
                                    path_out = os.path.realpath(p)
                                    break
                    except Exception:
                        pass
                if not path_out:
                    self._json(200, {"ok": False, "msg": "reel folder not found for " + sid[:40],
                                    "sid": sid, "hist": HIST_DIR})
                    return
                opened = False
                try:
                    if sys.platform == "darwin":
                        subprocess.Popen(["open", path_out], stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL)
                        opened = True
                    elif IS_WIN:
                        os.startfile(path_out)  # type: ignore[attr-defined]
                        opened = True
                    else:
                        subprocess.Popen(["xdg-open", path_out], stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL)
                        opened = True
                except Exception:
                    opened = False
                n_frames = 0
                try:
                    n_frames = sum(1 for f in os.listdir(path_out) if f.endswith(".jpg") and f.startswith("f_"))
                except Exception:
                    pass
                self._json(200, {"ok": True, "path": path_out, "sid": sid, "opened": opened,
                                "frames": n_frames, "hist": os.path.realpath(HIST_DIR)})
            except Exception as e:
                self._json(200, {"ok": False, "msg": str(e)[:160]})
            return
        if path == "/api/tz":
            # v944 tracker heal — /api/tz is a Cloudflare Pages function; it only
            # exists on the live deploy. The in-app shell serves the board from
            # THIS server, so the Terror Zone tracker 404'd ("tracker is down").
            # Proxy the live endpoint through the site's HTTP-Basic gate, 90s cache.
            self._json(*_tz_proxy())
            return
        if path == "/api/tallies":
            # v929 (Konyo: "I want to see what EXACTLY was tallied — RUNES for runes, GEMS
            # for gems, MATERIALS for materials") — every intake shot from the journal,
            # newest first, with per-key counts + the frame photo it was counted from.
            try:
                shots = []
                for r in self._load_journal_cached():
                    ik = r.get("intake")
                    if not isinstance(ik, dict):
                        continue
                    shots.append({
                        "ts": r.get("ts") or r.get("captureTs") or 0,
                        "tab": ik.get("tab") or ik.get("kind") or "",
                        "kind": ik.get("kind") or "",
                        "ok": bool(ik.get("ok", True)),
                        "counts": ik.get("counts") if isinstance(ik.get("counts"), dict) else {},
                        "total": int(ik.get("total") or 0),
                        "errors": int(ik.get("errors") or 0),
                        "frameId": r.get("frameId") or "",
                        "sessionId": r.get("sessionId") or "",
                    })
                shots.sort(key=lambda s: s["ts"], reverse=True)
                self._json(200, {"ok": True, "shots": shots[:200]})
            except Exception as e:
                self._json(200, {"ok": False, "msg": str(e)[:160], "shots": []})
            return
        if path == "/api/intake_log":
            # v944.4 (Konyo: "a separate log for the backend side of these intakes getting
            # received — like a log") — the raw plumbing view: every intake receipt the journal
            # recorded, newest first, with the transport truth (kind, ok, totals, errors, the
            # frame it came from, session). This is the RECEIPT LEDGER, distinct from /api/tallies
            # (which is the item counts) — here you watch receipts LAND and spot the 0-total misses.
            try:
                rows = []
                for r in self._load_journal_cached():
                    ik = r.get("intake")
                    if not isinstance(ik, dict):
                        continue
                    _tot = int(ik.get("total") or 0)
                    _ok = bool(ik.get("ok", True))
                    rows.append({
                        "ts": r.get("ts") or r.get("captureTs") or 0,
                        "tab": ik.get("tab") or ik.get("kind") or "",
                        "kind": ik.get("kind") or "",
                        "ok": _ok,
                        "total": _tot,
                        "errors": int(ik.get("errors") or 0),
                        "types": len(ik.get("counts") or {}) if isinstance(ik.get("counts"), dict) else 0,
                        "frameId": r.get("frameId") or "",
                        "sessionId": r.get("sessionId") or "",
                        "lane": r.get("lane") or "",
                        # the plumbing verdict: landed-empty misses vs real receipts vs errors
                        "status": ("error" if not _ok else ("empty" if _tot == 0 else "ok")),
                    })
                rows.sort(key=lambda s: s["ts"], reverse=True)
                _empty = sum(1 for r in rows if r["status"] == "empty")
                _err = sum(1 for r in rows if r["status"] == "error")
                self._json(200, {"ok": True, "rows": rows[:400],
                                 "summary": {"total": len(rows), "empty": _empty, "error": _err}})
            except Exception as e:
                self._json(200, {"ok": False, "msg": str(e)[:160], "rows": []})
            return
        if path.startswith("/api/beat"):
            # v879 (Grok B) — the READ CARD's forensic blob, one beat at a time
            try:
                from urllib.parse import urlparse as _up, parse_qs as _pq
                q = _pq(_up(self.path).query or "")
                sid = (q.get("id") or [""])[0]
                bn = int((q.get("n") or ["0"])[0])
                if HERE not in sys.path:
                    sys.path.insert(0, HERE)
                import replay as _rp
                _jr = self._load_journal_cached()
                row = None
                for r in _jr:
                    if (r.get("sessionId") or "") == sid and int(r.get("n") or -1) == bn:
                        row = r
                if row is None:
                    self._json(404, {"ok": False, "msg": "no such beat"})
                    return
                # v941 THE DOSSIER — same three-eye join as the pack, one beat.
                try:
                    _srows = [r for r in _jr if (r.get("sessionId") or "") == sid]
                    _dossier = _beat_dossier(_build_dossier_maps(_srows), row)
                except Exception:
                    _dossier = {"tally": None, "verify": None, "kai": None}
                self._json(200, {"ok": True,
                                 "dossier": _dossier,
                                 "raw": row.get("raw") or "",
                                 "dispatch": row.get("dispatch") or {},
                                 "promptVer": row.get("promptVer") or "",
                                 "parse": row.get("parse") or {},
                                 "decisions": row.get("decisions") or {},
                                 "pre": row.get("pre") or [],
                                 "chain": row.get("chain") or {},
                                 "ocr_raw": row.get("ocr_raw") or [],
                                 "ocr_seeded": row.get("ocr_seeded") or [],
                                 "equipped_names": row.get("equipped_names") or [],
                                 "board": row.get("board") or {},       # v883 — A2.5 feeds the river's BOARD stage
                                 "vision": row.get("vision") or {}})
            except Exception as e:
                self._json(500, {"ok": False, "msg": str(e)})
            return
        if path.startswith("/api/session"):
            from urllib.parse import parse_qs, urlparse
            q = parse_qs(urlparse(self.path).query)
            try:
                num = int((q.get("n") or ["1"])[0])
            except Exception:
                num = 1
            # v895 — default pack=debug (every fps frame + every AI read). pack=fast is optional zip.
            pack = (q.get("pack") or ["debug"])[0].strip().lower()
            if pack not in ("debug", "raw", "fast"):
                pack = "debug"
            self._json(200, self._theatre_session(num, pack=pack))
            return
        if path.startswith("/hist/"):
            self._serve_hist(path[len("/hist/"):])
            return
        if path == "/api/log":
            try:
                with open(LOG_PATH, "rb") as f:
                    data = f.read()[-12000:]
                text = data.decode("utf-8", "replace")
            except Exception:
                text = "(no log yet)"
            self._json(200, {"ok": True, "log": text})
            return
        if path == "/api/update":
            # v817 (Grok R8 #2) — ops truth: how far behind origin is this install?
            # Cousins are git clones (installer does git clone/pull) — fetch is cheap + safe.
            try:
                subprocess.run(["git", "fetch", "origin", "main", "--quiet"],
                               cwd=REPO, capture_output=True, timeout=20)
                r = subprocess.run(["git", "rev-list", "HEAD..origin/main", "--count"],
                                   cwd=REPO, capture_output=True, timeout=10, text=True)
                behind = int((r.stdout or "0").strip() or 0)
                subj = ""
                if behind:
                    r2 = subprocess.run(["git", "log", "origin/main", "-1", "--format=%s"],
                                        cwd=REPO, capture_output=True, timeout=10, text=True)
                    subj = (r2.stdout or "").strip()[:120]
                self._json(200, {"ok": True, "behind": behind, "latest": subj,
                                 "howTo": ("git pull, then relaunch TV DIABLO" if behind else "")})
            except Exception as e:
                self._json(200, {"ok": False, "msg": "update check failed: %s" % e})
            return
        if path == "/api/doctor":
            # v801 (Grok R7) — Windows self-diagnosis: fast, read-only, never spawns the CLI.
            self._json(200, doctor_payload())
            return
        if path == "/api/farmgate":
            # v924 — FARM DAY gate: one button, one verdict (the only endpoint allowed a CLI ping)
            self._json(200, farmgate_payload())
            return
        if path.startswith("/api/export"):
            # v809 (Grok R7 wow #3) — 📼 NIGHT CARD: write the session recap to the Desktop.
            # User-triggered only (theatre button); JSON (full beats) + recap.md (CUT story).
            from urllib.parse import urlparse, parse_qs
            q = parse_qs(urlparse(self.path).query or "")
            try:
                n = int((q.get("n") or ["1"])[0])
            except Exception:
                n = 1
            sess = self._theatre_session(n)
            if not isinstance(sess, dict) or not sess.get("beats"):
                self._json(404, {"ok": False, "msg": "no such session"})
                return
            sid = (sess.get("sessionId") or ("session%d" % n)).replace("/", "_")[:40]
            desk = os.path.expanduser("~/Desktop")
            base = os.path.join(desk, "TVDIABLO_" + sid)
            try:
                # v812 (Grok R8 sleeper sibling) — the Night Card claims FULL: include the RAW
                # journal rows (farmed/unvault/gone_candidates/ocr_ms/interest/mode/tz/…), not
                # just the theatre projection. Filter by sessionId, else by capture-ts range.
                raw_rows = []
                try:
                    want_sid = sess.get("sessionId") or ""
                    t0r = (sess.get("t0") or 0) - 5000
                    t1r = (sess.get("t1") or 0) + 5000
                    _root = os.path.join(HERE, "sessions")
                    _paths = [_root + ".%d.jsonl" % g for g in range(5, 0, -1)] + [_root + ".jsonl"]
                    for _p in _paths:
                        if not os.path.isfile(_p):
                            continue
                        with open(_p, encoding="utf-8") as jf:
                            for line in jf:
                                line = line.strip()
                                if not line:
                                    continue
                                try:
                                    row = json.loads(line)
                                except Exception:
                                    continue
                                if want_sid:
                                    if row.get("sessionId") == want_sid:
                                        raw_rows.append(row)
                                elif t0r <= (row.get("ts") or 0) <= t1r:
                                    raw_rows.append(row)
                except Exception:
                    raw_rows = []
                sess = dict(sess)
                sess["raw"] = raw_rows
                with open(base + ".json", "w", encoding="utf-8") as f:
                    json.dump(sess, f, indent=1)
                beats = sess.get("beats") or []
                t0 = sess.get("t0") or (beats[0].get("ts") if beats else 0)
                lines = ["# 📼 TV DIABLO — Night Card · session %d" % n,
                         "_%s · %d reads_" % (time.strftime("%Y-%m-%d %H:%M", time.localtime((t0 or 0) / 1000)), len(beats)), ""]
                for b in beats:
                    keep = (b.get("vault_names") or b.get("discovered_names")
                            or b.get("thrown_names") or b.get("names") or b.get("farewell"))
                    if not keep:
                        continue
                    rel = max(0, (b.get("ts") or 0) - (t0 or 0))
                    stamp = "T+%d:%02d" % (rel // 60000, (rel % 60000) // 1000)
                    bits = []
                    for nm in (b.get("vault_names") or []):
                        bits.append("🏦 **" + nm + "**")
                    for nm in (b.get("discovered_names") or []):
                        bits.append("💬🏆 " + nm)
                    for nm in (b.get("thrown_names") or []):
                        bits.append("🗑 " + nm)
                    for nm in (b.get("pending_names") or []):
                        bits.append("⏳ " + nm)   # v812 — holds are part of the story
                    if not bits:
                        bits = [", ".join((b.get("names") or [])[:5]) or ("👋 farewell" if b.get("farewell") else "")]
                    lines.append("- `%s` · %s%s%s" % (stamp, (b.get("area") or "?"),
                                 (" · " + b.get("scene")) if b.get("scene") else "",
                                 (" — " + " · ".join(bits)) if any(bits) else ""))
                with open(base + ".md", "w", encoding="utf-8") as f:
                    f.write("\n".join(lines) + "\n")
                self._json(200, {"ok": True, "json": base + ".json", "md": base + ".md",
                                 "beats": len(beats)})
            except Exception as e:
                self._json(500, {"ok": False, "msg": str(e)})
            return
        self._json(404, {"ok": False, "msg": "not found"})

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        length = int(self.headers.get("Content-Length") or 0)
        body = {}
        if length:
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            except Exception:
                body = {}

        if path == "/kai_verdict":
            # v940 🔬 — KAI's judge receipts: the engine iframe POSTs aicJudge results here.
            # Ghost-proof journaling: ts == captureTs == the FRAME's moment (passed as fts).
            try:
                _fts = int(body.get("fts") or 0) or int(time.time() * 1000)
                _vname = str(body.get("name") or "")[:60]
                _tier = str(((body.get("verdict") or {}).get("tier")) or "")[:12]
                # v940.1 GRAIL GATE — a known unique/set name is never a toss/border.
                # v943.2 — but EXCLUDE the generated rare-name combos: a rare "Beast Noose" is
                # recognized (register) yet CAN genuinely be a toss, so it must not auto-promote.
                # v948.19 — SPLIT-BRAIN FIX (Grok forensic #6, 'Spirit' grail-vs-toss): a bare
                # RUNEWORD name (e.g. "Spirit") was falling into _kai_fullnames() (harvested
                # generically as a Title-Case JSON key) but NOT into _kai_rarenames(), so it got
                # promoted straight to 'grail' HERE while bible.html's client-side aicJudgeApply
                # (unique/set-only gate by design, v948.5) left the APPLIED action as whatever the
                # affix judge scored — toss. Same read, two disagreeing verdicts. Reconciled: a
                # runeword is real forged gear (never toss/border) but it is NOT a grail item —
                # grail is unique/set only; runewords track in their own Chronicle. So a runeword
                # name forces 'keep' here, matching the mirrored fix in bible.html's
                # aicJudgeApply (_rwResolve/findRuneword force-to-keep). Only a true unique/set
                # name still promotes to 'grail'.
                # v1250 — RW FIRST, independent of fullnames membership. Live deeps often read
                # the forged word WITH its base glued on ("Spirit Monarch", "Insight Thresher",
                # "Chains of Honor Dusk Shroud") — those strings are NOT in _kai_fullnames()
                # (only bare RUNEWORD_TIP keys are), so the old outer fullnames guard SKIPPED
                # the entire gate and left tier=grail/toss split intact for the exact forensic
                # case. _kai_is_runeword_name handles bare + multi-word + glued-base forms and
                # excludes rare combos (Beast Noose). Applied mode is then reconciled so the
                # journal never shows "KEEP → toss".
                _vlow = _vname.lower()
                if _vname and _kai_is_runeword_name(_vname):
                    if _tier in ("toss", "border", "grail"):
                        _tier = "keep"
                elif (_vname and _vlow in _kai_fullnames() and _vlow not in _kai_rarenames()
                      and _tier in ("toss", "border")):
                    _tier = "grail"
                # v948.1/v948.2 — applied route from aicJudgeApply; live=true = mid-session
                _applied = body.get("applied") if isinstance(body.get("applied"), dict) else None
                _app_mode = str((_applied or {}).get("mode") or "")[:16]
                _app_mode = _kai_reconcile_applied(_tier, _app_mode) or _app_mode
                _app_acts = (_applied or {}).get("actions") if isinstance((_applied or {}).get("actions"), list) else []
                _live = bool(body.get("live"))
                # v949.x — SUPER-ANALYZE KAI (Phase B, 4th organ) tags its own deep re-reads
                # so the closer can identify+mark them afterward (routing row 'super' field)
                # without a second reader/endpoint — same aicJudge/aicJudgeApply/kai_verdict
                # machinery as the ordinary judge lane, just a provenance breadcrumb.
                _tag = str(body.get("tag") or "")[:16] or None
                _note = ("🔬 " + ("live-" if _live else ("super-" if _tag == "super" else ""))
                         + "judge " + (_vname or "a tooltip") + " — " + (_tier.upper() or "UNREADABLE"))
                if _app_mode:
                    _note += " → " + _app_mode
                rec = {"ts": _fts, "captureTs": _fts, "completedTs": int(time.time() * 1000),
                       "n": 0, "scene": "kai", "lane": "kai", "mode": "kai-judge", "names": [],
                       "area": "", "sessionId": str(body.get("sid") or "")[:48],
                       "frameId": str(body.get("frameId") or "")[:64],
                       "kai": {"judge": {"name": _vname, "base": str(body.get("base") or "")[:40],
                                          "q": str(body.get("q") or "")[:12], "tier": _tier,
                                          "score": int((body.get("verdict") or {}).get("score") or 0),
                                          "ok": bool(body.get("ok", False)),
                                          "why": str(body.get("why") or "")[:120],
                                          "applied": _app_mode or None,
                                          "live": _live,
                                          "tag": _tag,
                                          "actions": [str(a)[:24] for a in (_app_acts or [])[:8]]}},
                       "note": _note[:100]}
                with open(os.path.join(HERE, "sessions.jsonl"), "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                self._json(200, {"ok": True})
            except Exception as e:
                self._json(200, {"ok": False, "msg": str(e)[:120]})
            return
        if path == "/intake_claim":
            # v945.6 — tab intake lease: engine vs open board, one owner at a time
            try:
                r = _intake_lease_claim(body.get("tab"), body.get("owner") or "board",
                                       ttl_ms=body.get("ttlMs") or body.get("ttl_ms"))
                self._json(200, r)
            except Exception as e:
                self._json(200, {"ok": False, "why": str(e)[:120]})
            return
        if path == "/intake_release":
            try:
                r = _intake_lease_release(body.get("tab"), body.get("owner") or "board")
                self._json(200, r)
            except Exception as e:
                self._json(200, {"ok": False, "why": str(e)[:120]})
            return
        if path == "/intake_result":
            # v935 (Konyo P0: 'tallies silently vanishing') — the board POSTs each auto-intake
            # RESULT to the agent bridge (:17771), but the bridge DIES at session end, so a tally
            # that completes AFTER END SESSION loses its receipt forever (driver proved fired=1,
            # intakes journaled=0). Control's HTTP server outlives the agent — accept the receipt
            # here and journal it in the SAME shape tv_diablo.bridge() do_POST does, tagged to the
            # latest known sessionId from the journal. Dedupe so a receipt landing on BOTH bridges
            # (agent still up) is only journaled once.
            try:
                now_ms = int(time.time() * 1000)
                _ts = int(body.get("ts") or now_ms)
                _tab = str(body.get("tab") or "")[:24]
                _fid = str(body.get("frameId") or "")[:48]
                # A0 fix (2026-07-21, arch panel Q5 blocker): captureTs must be the FRAME's
                # capture ms, not `_ts` (the receipt-landing time) — retro joins on captureTs,
                # never ts, so a receipt stamped with receipt time desyncs from the frame it
                # describes on the scrub. Only fall back to `_ts` when no frameId was sent
                # (can't do better); capSrc flags which happened so retro readers know honestly.
                _cap_from_frame = _capture_ts_from_frame_id(_fid)
                _cap_ts = _cap_from_frame if _cap_from_frame is not None else _ts
                _cap_src = "frame" if _cap_from_frame is not None else "receipt-fallback"
                try:
                    _rows = _kai_journal_rows()
                except Exception:
                    _rows = []
                # v1208 — RECEIPT-BOUNDARY fix: frameId encodes its OWNING session directly
                # (reel_<sid>/<n>_<capturems> — the shape every funnel/closer/driver fire in
                # this file uses, e.g. control_app.py:4034 and the Stage-3/driver JS bodies).
                # Extracting sid straight from frameId is the frame's OWN ground truth,
                # immune to the race the OLD "latest sessionId anywhere in the journal" guess
                # had: that heuristic blindly wins even if a NEW session has already started
                # (logged its own rows) by the time a SLOW/late receipt from the PREVIOUS
                # session finally lands — precisely the bridge-death late-arrival case this
                # whole route exists for (see the route's own opening comment), now compounded
                # by Konyo starting another short farming session before the straggler
                # resolves. Mis-tagging the stale receipt onto the NEW session's reel makes
                # `_kai_build_routing`'s receipted-tab check wrongly treat a tab the new
                # session never actually photographed as already covered — suppressing a real
                # gap-funnel for it. Only fall back to the journal-scan guess when frameId
                # doesn't carry a session (e.g. bible.html's own board-side vault/tally calls,
                # which don't always pass a reel-relative frameId) — unchanged from before.
                _sid = ""
                _sid_m = re.match(r"^reel_(.+?)/", _fid) if _fid else None
                if _sid_m:
                    _sid = _sid_m.group(1)
                else:
                    for r in _rows:
                        s = r.get("sessionId")
                        if s:
                            _sid = s   # latest sessionId wins (rows are append-ordered)
                # v935.11 R3 (Grok dedupe verdict) — the ±5min frame+tab dedupe was too greedy:
                # (a) an empty frameId carries no identity, so those receipts must ALWAYS journal
                #     (never collapse two anonymous shots into one); (b) a re-tally of the SAME
                #     frame+tab with DIFFERENT counts is a genuine correction, not a dup, so the
                #     match now also requires an identical counts signature. Only the exact triple
                #     (frameId, tab, counts-sig) within ±5min is a true duplicate.
                _counts = body.get("counts") if isinstance(body.get("counts"), dict) else {}
                _csig = json.dumps([_counts, bool(body.get("ok", True)), int(body.get("total") or 0), int(body.get("errors") or 0)], sort_keys=True)   # v936 Grok: fail↔zero-read flips must journal
                if _fid:
                    for r in _rows:
                        if (r.get("lane") == "intake"
                                and str(r.get("frameId") or "") == _fid
                                and str((r.get("intake") or {}).get("tab") or "") == _tab
                                and json.dumps([(r.get("intake") or {}).get("counts") or {},
                                                bool((r.get("intake") or {}).get("ok", True)),
                                                int((r.get("intake") or {}).get("total") or 0),
                                                int((r.get("intake") or {}).get("errors") or 0)],
                                               sort_keys=True) == _csig   # v938.7 — SAME SHAPE both sides (test-routes caught the dead compare)
                                and abs(int(r.get("ts") or 0) - _ts) <= 300_000):
                            self._json(200, {"ok": True, "dup": True})
                            return
                rec = {
                    "ts": _ts, "captureTs": _cap_ts, "completedTs": now_ms,
                    "n": 0, "scene": "intake", "lane": "intake", "mode": "intake",
                    "names": [], "area": "", "sessionId": _sid,
                    "intake": {
                        "tab": _tab,
                        "kind": str(body.get("kind") or "")[:16],
                        "counts": _counts,
                        "total": int(body.get("total") or 0),
                        "errors": int(body.get("errors") or 0),
                        "items": (body.get("items") or [])[:60],
                        "ok": bool(body.get("ok", True)),
                    },
                    "frameId": _fid,
                    "capSrc": _cap_src,
                    "note": ("📸 intake · " + str(body.get("tab") or body.get("kind") or "shot"))[:80],
                }
                with open(os.path.join(HERE, "sessions.jsonl"), "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                self._json(200, {"ok": True})
            except Exception as e:
                self._json(500, {"ok": False, "msg": str(e)[:160]})
            return

        if path in ("/api/intake", "/api/ask"):
            # v874 (Konyo: 'Forge image AI intake uploads broken in the app console') — the board
            # posts to a RELATIVE /api/intake, which only exists as a Cloudflare function on the
            # live site. In-app (Mac AND Windows) that hit this server and 404'd. Proxy to
            # production with the site's Basic gate (password-only check, username free).
            # v874 — SUBSCRIPTION LANE FIRST (Konyo: 'use the subscription, not API tokens'):
            # tv/intake_local.mjs runs the REAL intake.js/ask.js with a fetch shim that rides
            # the locally-authorized `claude` CLI. Website proxy = fallback only.
            _runner = os.path.join(os.path.dirname(os.path.abspath(__file__)), "intake_local.mjs")
            # v919 (Grok REAL EYES R1) — STRICT mode: a silent local-lane failure falling
            # through to the website proxy can fake-green a "real subscription" run on the
            # website's key. TV_INTAKE_LOCAL_STRICT=1 → answer 502 honestly, never fall back.
            _strict = os.environ.get("TV_INTAKE_LOCAL_STRICT") == "1"
            if os.environ.get("TV_INTAKE_LOCAL", "1") != "0" and os.path.isfile(_runner):
                try:
                    _nice_kw = ({"creationflags": 0x4000 | _WIN_CREATE} if IS_WIN
                                else {"preexec_fn": (lambda: os.nice(10))})   # v879 — intake yields to the game
                    _pr = subprocess.run(
                        ["node", _runner],
                        input=json.dumps({"path": path, "body": body}).encode("utf-8"),
                        capture_output=True, timeout=150, **_nice_kw)
                    if _pr.returncode == 0 and _pr.stdout:
                        _out = json.loads(_pr.stdout.decode("utf-8", "replace"))
                        _pl = (_out.get("body") or "").encode("utf-8")
                        self.send_response(int(_out.get("status") or 200))
                        self.send_header("Content-Type", "application/json")
                        self.send_header("X-Intake-Lane", "subscription")
                        self.send_header("Content-Length", str(len(_pl)))
                        self.end_headers()
                        self.wfile.write(_pl)
                        return
                    if _strict:
                        _err = (_pr.stderr or b"").decode("utf-8", "replace")[-300:]
                        self._json(502, {"ok": False, "lane": "subscription-failed",
                                         "msg": "local intake runner failed (strict: no website fallback)",
                                         "detail": _err})
                        return
                except Exception as _ex:
                    if _strict:
                        self._json(502, {"ok": False, "lane": "subscription-failed",
                                         "msg": "local intake runner error (strict): " + str(_ex)[:200]})
                        return
                    pass   # any local failure → website proxy below
            elif _strict:
                self._json(502, {"ok": False, "lane": "subscription-failed",
                                 "msg": "local intake lane disabled/missing (strict: no website fallback)"})
                return
            try:
                # do_POST already consumed rfile into `body` — a second read blocks forever
                body_in = json.dumps(body).encode("utf-8")
                import base64 as _b64
                req = urllib.request.Request(
                    "https://bull-4-u.com" + path,
                    data=body_in,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "TVD-Console/1.0",   # CF WAF 403s python-urllib's default UA
                        "Authorization": "Basic " + _b64.b64encode(b"app:DeanDiablo").decode(),
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=120) as r:
                    out = r.read()
                    self.send_response(r.status)
                    self.send_header("Content-Type", r.headers.get("Content-Type") or "application/json")
                    self.send_header("Content-Length", str(len(out)))
                    self.end_headers()
                    self.wfile.write(out)
            except urllib.error.HTTPError as e:
                out = e.read() if hasattr(e, "read") else b'{"ok":false}'
                self._json(e.code, {"ok": False, "msg": "intake upstream %d" % e.code,
                                    "detail": out.decode("utf-8", "replace")[:300]})
            except Exception as e:
                self._json(502, {"ok": False, "msg": "intake proxy failed — is the Mac online? " + str(e)[:200]})
            return
        if path == "/api/session/delete":
            # v834 (Konyo: 'an option to delete a session if i want to') — POST {n} removes that
            # session's journal rows (across the generation ring) + its hist frames + footage in
            # its window. User-initiated, session-scoped, never touches other reels.
            try:
                n = int(body.get("n") or 0)
                sess = self._theatre_session(n)
                if not isinstance(sess, dict) or not sess.get("beats"):
                    self._json(404, {"ok": False, "msg": "no such session"})
                    return
                sid = sess.get("sessionId") or ""
                t0d = (sess.get("t0") or 0) - 2000
                t1d = (sess.get("t1") or 0) + 2000
                _root = os.path.join(HERE, "sessions")
                removed = 0
                fids = set()
                for _p in [_root + ".%d.jsonl" % g for g in range(5, 0, -1)] + [_root + ".jsonl"]:
                    if not os.path.isfile(_p):
                        continue
                    keep_lines = []
                    with open(_p, encoding="utf-8") as jf:
                        for line in jf:
                            raw_l = line.rstrip("\n")
                            if not raw_l.strip():
                                continue
                            try:
                                row = json.loads(raw_l)
                            except Exception:
                                keep_lines.append(raw_l)
                                continue
                            mine = (sid and row.get("sessionId") == sid) or \
                                   ((not sid) and t0d <= (row.get("ts") or 0) <= t1d)
                            if mine:
                                removed += 1
                                if row.get("frameId"):
                                    fids.add(str(row["frameId"]))
                            else:
                                keep_lines.append(raw_l)
                    tmp_p = _p + ".tmp"
                    with open(tmp_p, "w", encoding="utf-8") as jf:
                        jf.write("\n".join(keep_lines) + ("\n" if keep_lines else ""))
                    os.replace(tmp_p, _p)
                # frames: read frames by id + footage frames inside the window
                hist_dir = HIST_DIR
                killed_frames = 0
                if os.path.isdir(hist_dir):
                    for fn in os.listdir(hist_dir):
                        if not fn.endswith(".jpg"):
                            continue
                        base = fn[:-4]
                        kill = base in fids
                        if not kill and fn.startswith("f_"):
                            try:
                                kill = t0d <= int(base[2:]) <= t1d
                            except Exception:
                                kill = False
                        if kill:
                            for sub in ("", "cache1280", "cache160"):
                                try:
                                    os.remove(os.path.join(hist_dir, sub, fn) if sub else os.path.join(hist_dir, fn))
                                    if not sub:
                                        killed_frames += 1
                                except Exception:
                                    pass
                self._json(200, {"ok": True, "removedReads": removed, "removedFrames": killed_frames,
                                 "sessionId": sid})
            except Exception as e:
                self._json(500, {"ok": False, "msg": str(e)})
            return
        if path == "/api/kai_reclose":
            # v948.7 — force KAI to re-scan a reel (drop kai_report → closer re-picks it).
            # Debugger: Theatre has stills; reclose re-labels + gap-funnels materials/gems/runes.
            try:
                sid = str(body.get("sessionId") or body.get("sid") or "").strip()
                if not sid and body.get("n"):
                    try:
                        _ts = self._theatre_session(int(body.get("n")))
                        if isinstance(_ts, dict):
                            sid = str(_ts.get("sessionId") or "")
                    except Exception:
                        sid = ""
                if not sid:
                    self._json(400, {"ok": False, "msg": "need sessionId or n"})
                    return
                if _agent_mode != "off" or _agent_alive():
                    self._json(200, {"ok": False, "msg": "agent ON AIR — reclose only between sessions",
                                     "sessionId": sid})
                    return
                rd = os.path.join(HIST_DIR, "reel_" + sid)
                kr = os.path.join(rd, "kai_report.json")
                if not os.path.isdir(rd):
                    self._json(404, {"ok": False, "msg": "no reel for session", "sessionId": sid})
                    return
                # rename not delete — keep last report for forensics
                if os.path.isfile(kr):
                    bak = kr + ".bak_" + str(int(time.time()))
                    try:
                        os.replace(kr, bak)
                    except Exception:
                        try:
                            os.remove(kr)
                        except Exception:
                            pass
                # v948.8 — priority marker: jump this reel to the front of the closer's
                # queue instead of waiting behind the whole kaiVer<3 backlog sweep.
                try:
                    open(os.path.join(rd, ".kai_priority"), "w").close()
                except Exception:
                    pass
                self._json(200, {"ok": True, "msg": "kai_report cleared — closer will re-scan within ~30s (priority)",
                                 "sessionId": sid, "reel": "reel_" + sid, "kaiVerTarget": 4})
            except Exception as e:
                self._json(500, {"ok": False, "msg": str(e)[:160]})
            return
        if path == "/api/on":
            # v891 (Grok C3) — DISK PREFLIGHT: below the floor the reaper can't keep a reel
            # alive; refuse loudly with the exact ask instead of recording a doomed session.
            try:
                import shutil as _shd
                _free = _shd.disk_usage(HIST_DIR).free / 1e9
                if _free < 8.0:
                    self._json(200, {"ok": False, "mode": "off",
                                     "error": "DISK TOO FULL to record — %.1fGB free, need 8GB. Free ~%.0fGB and press ON AIR again." % (_free, 9 - _free)})
                    return
            except Exception:
                pass
            if _stop_inflight:
                # v899 — if the agent is already dead, clear the latch and allow ON
                if not _agent_alive() and _port_listener_pid() is None:
                    globals()["_stop_inflight"] = False
                    # Must use globals() — bare assign makes _agent_mode local to all of
                    # do_POST (UnboundLocalError on any later read; module mode never clears).
                    globals()["_agent_mode"] = "off"
                else:
                    self._json(200, {"ok": False, "msg": "still shutting down — session saving; try ON again in a moment",
                                     "mode": "stopping", "error": "still stopping"})
                    return
            r = start_agent(sim=False, test=bool(body.get("test")))
            _console_beacon_async("onair")   # v875 — the dashboard flips 🔴 within seconds
            self._json(200, r)   # v778-pre — ON opens NOTHING (one-window world)
            return
        if path == "/api/sim":
            if _stop_inflight:
                self._json(200, {
                    "ok": False,
                    "msg": "still shutting down — try again in a moment",
                    "mode": "stopping",
                })
                return
            if _agent_alive():
                stop_agent(farewell=False)
                time.sleep(0.4)
            r = start_agent(sim=True)
            self._json(200, r)
            return
        if path == "/api/off":
            # v847 — OFF seals the session (session_end) WITHOUT long farewell vision, then kills.
            # v926.2 — ALWAYS answer with JSON: a raised stop must never leave END SESSION with an
            # empty response (the real "i cant end session" bug — stop_agent threw, the handler
            # wrote nothing, the board hung). On any failure, hard-kill and report honestly.
            try:
                r = stop_agent(farewell=False)
            except Exception as _e:
                r = _force_kill_all_agents("off (stop_agent raised: %s)" % str(_e)[:120])
            _console_beacon_async("off")   # v875
            self._json(200, r)
            return
        if path == "/api/stop":
            try:
                r = stop_agent(farewell=False)   # v926 LIGHT — never a farewell vision read on End Session
            except Exception as _e:
                r = _force_kill_all_agents("stop (stop_agent raised: %s)" % str(_e)[:120])
            self._json(200, r)
            return
        if path == "/api/restart":
            if _stop_inflight:
                self._json(200, {"ok": False, "msg": "still shutting down — try again in a moment", "mode": "stopping"})
                return
            stop_agent(farewell=False)
            time.sleep(0.4)
            r = start_agent(sim=False)
            self._json(200, r)
            return
        if path == "/api/board":
            # v781 — ONE WINDOW by default: return a same-origin nav target. The UI navigates
            # THIS pywebview to /board?app=1#tab. Spawning a second native window is opt-in
            # only (?popout=1) for the rare explicit pop-out case — never for console buttons.
            from urllib.parse import parse_qs, urlparse
            q = parse_qs(urlparse(self.path).query)
            tab = (q.get("tab") or ["session"])[0]
            # v904 (Konyo: 'TV·D is a smooth TOGGLE') — an EXPLICIT #tvd opens the live view;
            # only the legacy on/off aliases land on SESSIONS
            if tab in ("tvd-on", "tvd-off"):
                tab = "session"
            if tab not in ("session", "tools", "forge", "funi", "fsets", "tvd"):
                tab = "session"
            popout = (q.get("popout") or ["0"])[0] in ("1", "true", "yes")
            if popout:
                self._json(200, open_board(auto_on=True, tab=tab))
                return
            self._json(200, {
                "ok": True,
                "msg": "same-window nav",
                "nav": "/board?app=1#%s" % tab,
                "tab": tab,
                "spawned": False,
            })
            return
        if path == "/api/quit":
            threading.Thread(
                target=lambda: (time.sleep(0.3), os._exit(0)), daemon=True
            ).start()
            self._json(200, {"ok": True, "msg": "control quitting"})
            return
        self._json(404, {"ok": False, "msg": "not found"})


def _loud_fail(title, msg):
    """v770 — pythonw has no console: a native-window failure must SHOUT, not vanish."""
    try:
        if IS_WIN:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, msg, title, 0x10)   # MB_ICONERROR
        elif sys.platform == "darwin":
            subprocess.run(["osascript", "-e",
                            f'display alert "{title}" message "{msg}" as critical'],
                           capture_output=True, timeout=10)
    except Exception:
        pass


def board_window():
    """v767.1 — dedicated native window for the LOCAL board (file:// bible.html#tvd).
    v773.2 — orphan guard: if the control server disappears for ~60s, this window self-closes
    (the REG-020 swarm can never rebuild from forgotten windows).
    v1176 — this is a SECONDARY window process (spawned with --board-window); it must never
    be trigger-happy about self-killing on a transient hiccup (a self-hosted watchdog killing
    itself is the opposite of stability). Widened the tolerance (5s timeout · 5 misses ≈ 100s)
    and it now says why before it exits, instead of vanishing silently."""
    def _orphan_watch():
        misses = 0
        while True:
            time.sleep(20)
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{CONTROL_PORT}/api/status", timeout=5):
                    misses = 0
            except Exception:
                misses += 1
                if misses >= 5:
                    print(f"📺 board window: control server unreachable for ~{misses * 20}s — "
                          f"self-closing (orphan guard).", flush=True)
                    os._exit(0)
    threading.Thread(target=_orphan_watch, daemon=True).start()
    # v774 🌙 — same-origin host + deep-link hash (--hash=forge etc.)
    tab = "session"
    for a in sys.argv:
        if a.startswith("--hash="):
            tab = a.split("=", 1)[1] or "session"
    if tab in ("tvd", "tvd-on", "tvd-off"):
        tab = "session"
    url = "http://127.0.0.1:%d/board#%s" % (CONTROL_PORT, tab)
    try:
        import webview
        webview.create_window(
            "TV DIABLO — Board",
            url=url,
            width=1500,
            height=980,
            min_size=(1080, 700),
            background_color="#060504",
        )
        webview.start()
    except Exception as e:
        _loud_fail(
            "TV DIABLO",
            f"Native board window crashed: {e}\n\n"
            f"Opening in your browser instead.\nLog: {LOG_PATH}",
        )
        _open_browser_app_fallback(url)


def main():
    if "--board-window" in sys.argv:
        board_window()
        return
    open_ui = "--open" in sys.argv or "-o" in sys.argv
    no_open = "--no-open" in sys.argv
    # --window-only: attach a native window to an already-running control server
    window_only = "--window-only" in sys.argv

    if window_only:
        # Secondary attach: do NOT kill ON AIR when this window closes (primary owns it).
        globals()["_WINDOW_ONLY"] = True
        open_control_window()
        return

    try:
        srv = ThreadingHTTPServer(("127.0.0.1", CONTROL_PORT), Handler)
    except OSError as e:
        # v1248 — TAKEOVER (Konyo: "it says already open"). The port is held, usually by the
        # supervisor's always-up HEADLESS console (--no-open, no window).
        # v1251 — LIVE-SCAN RECLAIM: a window-only attach left the headless process as the
        # primary that SPAWNS the agent. Headless has NO Screen Recording TCC → ON AIR
        # window-pin fails → full-screen fallback shows the DESKTOP. When --open wants a
        # window and none is live, RECLAIM the port (pause supervisor + kill --no-open)
        # and become PRIMARY so the agent inherits this process's TCC chain.
        if open_ui and not _window_present():
            print(f"📺 TV DIABLO already serving on :{CONTROL_PORT} (headless) — "
                  f"reclaiming for live scan (TCC-correct primary, not window-only)…",
                  flush=True)
            try:
                _reclaim_headless_for_scan()
            except Exception as _re:
                print(f"⚠ reclaim failed: {_re}", flush=True)
            try:
                srv = ThreadingHTTPServer(("127.0.0.1", CONTROL_PORT), Handler)
            except OSError as e2:
                # last resort: attach a window so the user still sees something (capture
                # may stay desktop-only until they run tvd-scan.sh / grant TCC).
                print(f"📺 reclaim bind still failed ({e2}) — attaching window-only "
                      f"(Screen Recording may be missing on the headless primary)…",
                      flush=True)
                globals()["_WINDOW_ONLY"] = True
                open_control_window()
                return
            # reclaimed — fall through as PRIMARY (do not return)
        else:
            # v781 — a REAL window already exists → refuse a second one, point at the existing.
            print(
                f"📺 TV DIABLO window is already open on :{CONTROL_PORT} — not opening a second one.\n"
                f"   Use the existing window (or STOP/quit it first).\n   ({e})"
            )
            try:
                if sys.platform == "darwin":
                    subprocess.run(
                        ["osascript", "-e",
                         'display notification "TV DIABLO is already open — use the existing window." '
                         'with title "TV DIABLO"'],
                        capture_output=True, timeout=5,
                    )
            except Exception:
                pass
            sys.exit(0)

    plat = "windows" if IS_WIN else ("mac" if sys.platform == "darwin" else sys.platform)
    # v948.8 — was a hardcoded "v935.8" literal, frozen ~13 versions ago (drift
    # spotted auditing the closer log during the materials retro round); _app_ver()
    # mirrors status_payload's stamp so this banner can never drift from ship again.
    print(f"📺 TV DIABLO Control {_app_ver()} · {plat} · native window · http://127.0.0.1:{CONTROL_PORT}/", flush=True)
    print(f"   agent bridge :{AGENT_PORT} · log {LOG_PATH}", flush=True)
    if IS_WIN:
        print("   Windows ON = capture_win.ps1 (hidden) + tv_diablo.py --watch", flush=True)
    print("   close the app window → auto-stops ON AIR (exit safeguard · same as tvd stop).", flush=True)

    # v935.8 — reclaim orphans left by a prior crash/close (the "always on" feeling)
    try:
        if _port_listener_pid() is not None or _agent_alive():
            print("📺 reclaiming orphan ON AIR from a previous session…", flush=True)
            _force_kill_all_agents("boot-orphan-reclaim")
    except Exception as _oe:
        print(f"⚠ orphan reclaim skipped: {_oe}", flush=True)

    # v935.8 — process-level safeguards (window path also wired in open_control_window)
    import atexit
    atexit.register(lambda: _console_exit_stop_onair("atexit"))

    def _sig_exit(signum, _frame):
        try:
            name = signal.Signals(signum).name
        except Exception:
            name = str(signum)
        _console_exit_stop_onair("signal-%s" % name)
        try:
            srv.shutdown()
        except Exception:
            pass
        # 0 = clean; avoid re-entrant signal handlers looping
        os._exit(0)

    try:
        signal.signal(signal.SIGTERM, _sig_exit)
        signal.signal(signal.SIGINT, _sig_exit)
    except Exception:
        pass

    threading.Thread(target=_bridge_prober, daemon=True, name="tvd-prober").start()   # v872
    threading.Thread(target=_console_beacon_loop, daemon=True, name="tvd-beacon").start()   # v875
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    time.sleep(0.2)

    if open_ui and not no_open:
        # Blocks until the native window is closed; open_control_window stops ON AIR on return.
        open_control_window()
        _console_exit_stop_onair("main-after-window")
        # v1176 — a closed window (deliberate close OR a flaky WKWebView self-close) used
        # to take the WHOLE control server down with it: srv.shutdown()+return here killed
        # the daemon serve_forever thread, and with nothing non-daemon left alive the
        # process exited right behind it — :17772 then sat HTTP-000-dead until someone
        # noticed and relaunched by hand (recurring crash, evidence: control_app.log shows
        # repeated "window-closed" exits with no relaunch). Serving the console is not
        # actually coupled to a window being open, so just drop into headless mode below —
        # :17772 stays answerable; reopen a window anytime with --window-only.
        print(f"📺 native window closed — control server stays up headless on "
              f"http://127.0.0.1:{CONTROL_PORT}/ (·/api/quit to exit · --window-only to "
              f"reopen a window)", flush=True)

    # headless server mode (tests / --no-open / window closed above)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n📺 control UI server stopping — exit safeguard cuts ON AIR.")
        _console_exit_stop_onair("keyboard-interrupt")
        srv.shutdown()


if __name__ == "__main__":
    main()
