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

import hashlib
import bisect
import collections
import inspect
import json
import math
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

# v1463 — Windows stdio must speak UTF-8 before ANY print(). This module logs with emoji
# (📺 ⚠ 👋) on its boot and exit paths; under a Hebrew console (cp1255) those raise
# UnicodeEncodeError from inside print(), which surfaced as 4 errors + 2 failures in
# test_control on a plain `python tv/test_control.py`. tv_diablo.py has carried this exact
# block since REG-044; control_app never got it, so "the suite is green" was only ever true
# when the caller happened to export PYTHONIOENCODING/PYTHONUTF8 first.
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")
    for _stream_name in ("stdout", "stderr"):
        _stream = getattr(sys, _stream_name, None)
        try:
            if _stream is not None and hasattr(_stream, "reconfigure"):
                _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = os.path.dirname(os.path.abspath(__file__))

# v1902 — DEFINED HERE, AT THE TOP, because the state paths below need it and one of them did not
# get it. It used to sit 11,000 lines down, after every vault path had already been built from a
# bare HERE. A helper that arrives after its callers is a rule that applies to whoever remembered.


def _fixture_root_for_state():
    """HERE, unless TV_HIST says this is a fixture's world — the v1867/v1869 rule, one call."""
    try:
        import tv_diablo as _tvd
        return _tvd._fixture_root(HERE)
    except Exception:
        return HERE
REPO = os.path.dirname(HERE)


def _journal_path():
    """v1493 — THE ONE JOURNAL PATH. `TV_SESSIONS` existed since v877 but exactly ONE of the eleven
    sessions.jsonl sites honoured it; the other ten hardcoded HERE/sessions.jsonl. So a harness that
    set TV_SESSIONS believed it was isolated while the receipts stream read Konyo's REAL journal —
    caught live: a fixture run with four seeded rows returned 25 receipts of his actual session data.
    Five of those ten sites APPEND, so an isolated-looking test could have written into the record of
    his real farming nights. Every site resolves here now."""
    return os.environ.get("TV_SESSIONS") or os.path.join(HERE, "sessions.jsonl")


def _journal_ring():
    """v1709 — live file + rotated generations, ALL honouring TV_SESSIONS.

    Export and delete used to build `HERE/sessions.jsonl` (+ .1 … .5) even when
    `_journal_path()` pointed at a harness file. The UI listed the isolated journal
    and those two routes mutated the production one. The ring is derived from the
    same resolver so a fixture cannot touch his nights.
    """
    live = _journal_path()
    stem = live[:-6] if live.endswith(".jsonl") else live
    return [stem + ".%d.jsonl" % g for g in range(5, 0, -1)] + [live]

CONTROL_PORT = int(os.environ.get("TV_CONTROL_PORT", "17772"))
AGENT_PORT = int(os.environ.get("TV_PORT", "17771"))
def _log_root():
    """v1869 — his console log, unless TV_HIST says this is a fixture's world.

    This one cost a wrong diagnosis before it was found: test_button_matrix and test_roundtrip_sim
    write `—— control start … mode=sim ——` banners into control_agent.log, and I read a cluster of
    them as Konyo pressing SIM and LIVE at his keyboard. They were my own gate runs.
    Founding rule 4 — suspect the instrument. [[feedback-suspect-the-instrument]]"""
    try:
        import tv_diablo as _tvd
        return _tvd._fixture_root(HERE)
    except Exception:
        return HERE


LOG_PATH = os.path.join(_log_root(), "control_agent.log")
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

# v1418 — FLEET UNITY: how far is this install behind GitHub origin/main?
# Cached so /api/status never blocks on a slow fetch every 12s poll.
_FLEET_CACHE = {"t": 0.0, "val": None}
_FLEET_TTL_S = 120.0  # re-fetch at most every 2 min
_FLEET_FETCH_TTL_S = 300.0  # network fetch at most every 5 min
_FLEET_LAST_FETCH = 0.0


def _git_tracked_dirty():
    """True only when TRACKED files are modified (?? untracked does not count)."""
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO, capture_output=True, text=True, timeout=8,
            creationflags=_WIN_CREATE if IS_WIN else 0,
        )
        for line in (r.stdout or "").splitlines():
            if not line.strip():
                continue
            if line.startswith("??"):
                continue
            return True
        return False
    except Exception:
        return False


def fleet_origin_status(force_fetch=False):
    """v1418 — {behind, latest, head, origin, dirty, ok, howTo, ver}.
    behind = commits on origin/main not in HEAD (0 = unified with fleet channel)."""
    global _FLEET_LAST_FETCH
    now = time.time()
    if (not force_fetch and _FLEET_CACHE["val"] is not None
            and (now - _FLEET_CACHE["t"]) < _FLEET_TTL_S):
        return dict(_FLEET_CACHE["val"])
    out = {
        "ok": True, "behind": 0, "latest": "", "head": "", "origin": "",
        "dirty": False, "howTo": "", "ver": _app_ver() if "_app_ver" in globals() else "",
    }
    try:
        out["dirty"] = _git_tracked_dirty()
        # lightweight rev-parse always
        for key, args in (
            ("head", ["git", "rev-parse", "--short", "HEAD"]),
            ("origin", ["git", "rev-parse", "--short", "origin/main"]),
        ):
            try:
                r = subprocess.run(
                    args, cwd=REPO, capture_output=True, text=True, timeout=5,
                    creationflags=_WIN_CREATE if IS_WIN else 0,
                )
                if r.returncode == 0:
                    out[key] = (r.stdout or "").strip()
            except Exception:
                pass
        # network fetch (throttled)
        if force_fetch or (now - _FLEET_LAST_FETCH) >= _FLEET_FETCH_TTL_S:
            try:
                subprocess.run(
                    ["git", "fetch", "origin", "main", "--quiet"],
                    cwd=REPO, capture_output=True, timeout=25,
                    creationflags=_WIN_CREATE if IS_WIN else 0,
                )
                _FLEET_LAST_FETCH = now
                r = subprocess.run(
                    ["git", "rev-parse", "--short", "origin/main"],
                    cwd=REPO, capture_output=True, text=True, timeout=5,
                    creationflags=_WIN_CREATE if IS_WIN else 0,
                )
                if r.returncode == 0:
                    out["origin"] = (r.stdout or "").strip()
            except Exception:
                pass
        r = subprocess.run(
            ["git", "rev-list", "HEAD..origin/main", "--count"],
            cwd=REPO, capture_output=True, text=True, timeout=10,
            creationflags=_WIN_CREATE if IS_WIN else 0,
        )
        # v1709 — a failed count is NOT "0 behind". Leaving ok=True + behind=0
        # made /api/status and doctor both say "unified with origin/main" when
        # git never answered. Unknown stays unknown.
        if r.returncode != 0:
            out["ok"] = False
            out["howTo"] = "could not count commits vs origin/main"
            _FLEET_CACHE["t"] = now
            _FLEET_CACHE["val"] = dict(out)
            return dict(out)
        out["behind"] = int((r.stdout or "0").strip() or 0)
        if out["behind"] > 0:
            r2 = subprocess.run(
                ["git", "log", "origin/main", "-1", "--format=%s"],
                cwd=REPO, capture_output=True, text=True, timeout=8,
                creationflags=_WIN_CREATE if IS_WIN else 0,
            )
            out["latest"] = (r2.stdout or "").strip()[:120]
            if out["dirty"]:
                out["howTo"] = (
                    "You are %d commit(s) behind GitHub. Local TRACKED edits block auto-pull — "
                    "commit/stash them, then relaunch TV DIABLO (or: git pull)."
                    % out["behind"]
                )
            else:
                out["howTo"] = (
                    "You are %d commit(s) behind GitHub. Relaunch TV DIABLO to auto-pull, "
                    "or run: git pull && relaunch."
                    % out["behind"]
                )
        else:
            out["howTo"] = "unified with origin/main — all devices should match after relaunch"
    except Exception as e:
        out["ok"] = False
        out["howTo"] = "fleet check failed: %s" % str(e)[:80]
    _FLEET_CACHE["t"] = now
    _FLEET_CACHE["val"] = dict(out)
    return dict(out)

_ART_MIME = {
    ".png": "image/png",
    ".gif": "image/gif",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}

# v1402 — MUST be RLock. start_agent holds _lock then calls _start_capture → _pid_alive
# which also takes _lock. A plain Lock deadlocks forever → ON AIR spins, /api/on never
# answers, cousin console looks "stuck". Live evidence 2026-07-26 Hebrew Windows PC.
_lock = threading.RLock()
_agent_proc = None  # type: ignore
_stop_inflight = False   # v768 (Grok R2) — a threaded stop/farewell is running; ON/RESTART must wait
_capture_proc = None  # type: ignore
_agent_mode = "off"  # off | live | sim
_log_fp = None
_EXIT_STOP_DONE = False
_EXIT_STOP_LOCK = threading.Lock()
_WINDOW_ONLY = False   # v935.8 — secondary --window-only attach must NOT kill ON AIR
# v1410 — window liveness for close UX. When the user hits ✕, Cocoa fires close handlers on
# the UI thread; any blocking stop/evaluate_js there freezes the window → Apple hang report
# (Python_*.hang · "unresponsive 35s"). Mark the window gone IMMEDIATELY so the engine driver
# never evaluate_js a dying WKWebView, and run exit-stop off-thread.
_WINDOW_LIVE = False
# v1420 — Force-Quit killer. pywebview Cocoa often leaves webview.start() blocked in select()
# after the red ✕, so main never reaches os._exit and the Dock app beachballs until Force Quit.
# Arm a hard process death once on every real exit surface (✕ / Esc→/api/quit / webview return).
_FORCE_EXIT_ARMED = False
_FORCE_EXIT_LOCK = threading.Lock()
_FORCE_EXIT_DELAY_S = 1.25
_FORCE_EXIT_CANCEL = False   # v1463 — set True to call off an armed force-exit (see _arm_force_exit)


def _find_claude_bin(path_env=None):
    """v1380.4 — locate Claude Code CLI (cousin Windows PATH is often incomplete under pythonw)."""
    import shutil as _sh
    pe = path_env if path_env is not None else os.environ.get("PATH", "")
    hit = _sh.which("claude", path=pe) or _sh.which("claude")
    if hit and os.path.isfile(hit):
        return hit
    # Windows installers scatter the binary; Desktop shortcut PATH is often stripped.
    candidates = []
    if IS_WIN:
        la = os.environ.get("LOCALAPPDATA", "")
        ra = os.environ.get("APPDATA", "")
        home = os.path.expanduser("~")
        for p in (
            os.path.join(home, ".local", "bin", "claude.exe"),
            os.path.join(home, ".local", "bin", "claude.cmd"),
            os.path.join(home, ".local", "bin", "claude"),
            os.path.join(la, "Programs", "claude", "claude.exe"),
            os.path.join(la, "claude", "claude.exe"),
            os.path.join(ra, "npm", "claude.cmd"),
            os.path.join(ra, "npm", "claude"),
            os.path.join(la, "Microsoft", "WinGet", "Links", "claude.exe"),
        ):
            if p and os.path.isfile(p):
                candidates.append(p)
    else:
        for p in (
            os.path.expanduser("~/.local/bin/claude"),
            "/opt/homebrew/bin/claude",
            "/usr/local/bin/claude",
        ):
            if os.path.isfile(p):
                candidates.append(p)
    return candidates[0] if candidates else None


def _agent_python():
    """v1380.4 — never spawn the agent with Windows Store stub / prefer python.exe over pythonw."""
    exe = sys.executable or ""
    if IS_WIN:
        low = exe.replace("/", "\\").lower()
        if "windowsapps" in low:
            # Store alias — try real interpreters on PATH
            import shutil as _sh
            for name in ("python", "py"):
                hit = _sh.which(name)
                if hit and "windowsapps" not in hit.lower():
                    return hit
        # pythonw is fine for GUI but agent logs cleaner under python.exe
        if low.endswith("pythonw.exe"):
            cand = exe[:-len("pythonw.exe")] + "python.exe"
            if os.path.isfile(cand):
                return cand
    return exe


def _env_clean(sim=False):
    env = os.environ.copy()
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("ANTHROPIC_AUTH_TOKEN", None)
    extras = []
    if IS_WIN:
        la = os.environ.get("LOCALAPPDATA", "")
        ra = os.environ.get("APPDATA", "")
        extras = [
            os.path.expandvars(r"%LocalAppData%\Programs\Python\Python312"),
            os.path.expandvars(r"%LocalAppData%\Programs\Python\Python312\Scripts"),
            os.path.expandvars(r"%LocalAppData%\Programs\Python\Python313"),
            os.path.expandvars(r"%LocalAppData%\Programs\Python\Python313\Scripts"),
            os.path.expandvars(r"%LocalAppData%\Programs\Python\Python311"),
            os.path.expandvars(r"%LocalAppData%\Programs\Python\Python311\Scripts"),
            os.path.expandvars(r"%LocalAppData%\Microsoft\WinGet\Links"),
            os.path.expandvars(r"%ProgramFiles%\Git\cmd"),
            os.path.expanduser(r"~\.local\bin"),
            os.path.join(ra, "npm") if ra else "",
            os.path.join(la, "Programs", "claude") if la else "",
            os.path.join(la, "claude") if la else "",
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
    # Pin Claude binary so the agent does not re-search a thin PATH
    claude = _find_claude_bin(env.get("PATH", ""))
    if claude:
        env["TV_CLAUDE_BIN"] = claude
        # ensure its folder is on PATH for any child that shells `claude`
        cdir = os.path.dirname(claude)
        if cdir and cdir not in env.get("PATH", ""):
            env["PATH"] = cdir + os.pathsep + env.get("PATH", "")
    if sim:
        env["TV_STUB"] = "1"
    else:
        env.pop("TV_STUB", None)
    env["TV_PORT"] = str(AGENT_PORT)
    # v784 — Windows capture default AUTO (pin D2R.exe); Mac agent reads TV_CAPTURE itself
    if IS_WIN and not (env.get("TV_CAPTURE") or "").strip():
        env["TV_CAPTURE"] = "auto"
    # v1402 — Hebrew/Windows non-UTF8 consoles (cp1255 etc.): emoji boot prints in
    # tv_diablo.py used to UnicodeEncodeError and kill the agent before :17771 opened.
    if IS_WIN:
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("PYTHONUTF8", "1")
        # v1404 — pin Windows identity so agent/capture never inherit Mac-oriented env
        env["TV_PLATFORM"] = "windows"
        env["TV_OS"] = "windows"
    return env


_BR_CACHE = {"ping": False, "st": None, "ts": 0.0, "st_ts": 0.0}
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


# ── v1597 BEACON HONESTY ─────────────────────────────────────────────────────
# Konyo: "my windows PC i dont see it here logged". He could not tell whether that machine had
# NEVER been switched on or had been FAILING to check in for months — because the beacon below
# swallowed every exception into a bare `except: pass` and left no trace anywhere. Those two
# states looked IDENTICAL from the outside AND from the machine itself. This record is the only
# thing that tells them apart, so the bare-except must never be restored without it.
# Fire-and-forget and non-blocking are UNCHANGED — only the bookkeeping is new.
_BEACON_LOCK = threading.Lock()
# v1869 — per-install, alongside .tvd_identity.json — and per-FIXTURE when TV_HIST says so, by the
# one rule in tv_diablo._fixture_root. A test-spawned console announcing itself into his beacon is
# a test telling his dashboard that a session started. [[feedback-fixtures-never-touch-live-data]]
_BEACON_STATE_PATH = os.path.join(_log_root(), ".tvd_beacon.json")
_BEACON_LAST = {"t": None, "ts": None, "ok": None, "code": None, "err": "", "event": "",
                "okAt": None, "attempts": 0, "failures": 0, "suppressed_by": "", "fleet": None}


def _beacon_now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _beacon_state_save():
    """Persist across restarts — otherwise 'it has never ONCE succeeded' is unanswerable after a
    reboot, which is the actual question about the Windows PC. Own try/except: a read-only or
    full disk must never affect the beacon."""
    try:
        with _BEACON_LOCK:
            data = dict(_BEACON_LAST)
        tmp = _BEACON_STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        os.replace(tmp, _BEACON_STATE_PATH)
    except Exception:
        pass


def _beacon_state_load():
    try:
        with open(_BEACON_STATE_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            with _BEACON_LOCK:
                for k in _BEACON_LAST:
                    if k in data:
                        _BEACON_LAST[k] = data[k]
                _BEACON_LAST["attempts"] = int(_BEACON_LAST.get("attempts") or 0)
                _BEACON_LAST["failures"] = int(_BEACON_LAST.get("failures") or 0)
    except Exception:
        pass


def _beacon_snapshot():
    with _BEACON_LOCK:
        return dict(_BEACON_LAST)


def _beacon_status():
    """v1597 — the honest, UI-facing shape. Additive to status_payload()."""
    s = _beacon_snapshot()
    return {
        "lastAttempt": s.get("t"), "lastOk": s.get("ok"), "lastOkAt": s.get("okAt"),
        "code": s.get("code"), "error": s.get("err") or "",
        "attempts": int(s.get("attempts") or 0), "failures": int(s.get("failures") or 0),
        "suppressedBy": s.get("suppressed_by") or "", "fleet": s.get("fleet"),
    }


_beacon_state_load()   # startup: carry the verdict across restarts


def _console_beacon(event="hb"):
    """v875 (Konyo: 'a tracker so I know whose console is online — like the site visits') —
    phone the presence beacon home. Never blocks a caller; never raises into one.

    v1496 — CI IS NOT A MACHINE OF HIS. Every Routine-I / agent-test job boots this app, so the
    runners were checking in and the fleet answered "who is online" with a GitHub VM in Boydton
    sitting next to his MacBook. A tracker that lists strangers is not answering the question.

    v1597 — HONEST ABOUT ITS OWN FAILURES. This used to end in a bare `except Exception: pass`.
    A machine whose beacon had failed on EVERY attempt for months was indistinguishable from a
    machine that was never switched on — that is the root cause under Konyo's whole "I don't see
    my Windows PC" report. Every outcome (success, failure, deliberate suppression) is now
    recorded in _BEACON_LAST, persisted to disk, and surfaced by BOTH /api/status and /api/doctor.
    The except stays broad and still swallows: only the bookkeeping is new.
    The PRIOR attempt's result also rides upstream as `lastBeacon`, so a beacon that reaches the
    server can report that the previous one did not — the transient/partial failure case that is
    otherwise invisible from either end. Chicken-and-egg is intentional: a machine that NEVER
    reaches the server says so on its own screen (doctor check `console_beacon`), not here."""
    supp = ("CI" if os.environ.get("CI") else
            "GITHUB_ACTIONS" if os.environ.get("GITHUB_ACTIONS") else
            "TVD_NO_BEACON" if os.environ.get("TVD_NO_BEACON") else "")
    if supp:
        # v1597 — the v1496 suppression is CORRECT and stays. But a machine with TVD_NO_BEACON
        # stuck in its environment was permanently absent from the fleet with zero explanation.
        # Record WHICH variable, so status + doctor can say "deliberately not reporting, because X".
        with _BEACON_LOCK:
            _BEACON_LAST["t"] = _beacon_now()
            _BEACON_LAST["ts"] = time.time()
            _BEACON_LAST["ok"] = None
            _BEACON_LAST["code"] = None
            _BEACON_LAST["err"] = ""
            _BEACON_LAST["event"] = event
            _BEACON_LAST["suppressed_by"] = supp
        _beacon_state_save()
        return
    _ts_iso, _ts_epoch = _beacon_now(), time.time()
    with _BEACON_LOCK:
        # snapshot the PRIOR result BEFORE this attempt overwrites it — that is what rides upstream
        prior = {"ok": _BEACON_LAST.get("ok"), "code": _BEACON_LAST.get("code"),
                 "err": (_BEACON_LAST.get("err") or "")[:200], "t": _BEACON_LAST.get("t")}
        _BEACON_LAST["suppressed_by"] = ""
        _BEACON_LAST["attempts"] = int(_BEACON_LAST.get("attempts") or 0) + 1
        _BEACON_LAST["t"] = _ts_iso
        _BEACON_LAST["ts"] = _ts_epoch
        _BEACON_LAST["event"] = event
    try:
        import base64 as _b64, socket as _sock
        st = status_payload()
        body = json.dumps({
            "machine": _sock.gethostname().split(".")[0],
            "platform": st.get("platform"), "ver": st.get("ver"),
            "mode": st.get("mode"), "event": event,
            "user": os.environ.get("TVD_USER", ""),
            "reads": st.get("readCount") or 0,
            # v1496 — the name Konyo gave this machine, so the fleet reads "Konyo's MacBook"
            # instead of konyo-3. The hostname still rides along as the technical fallback.
            "nickname": (st.get("identity") or {}).get("nickname") or "",
            "install": ((st.get("identity") or {}).get("id") or "")[:12],
            # v1597 — the PREVIOUS attempt's verdict. The server stores it defensively and
            # /console renders a failed one red, so a transient failure is visible from the site
            # too, not only on the machine that suffered it.
            "lastBeacon": prior,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://bull-4-u.com/api/console", data=body,
            headers={"Content-Type": "application/json", "User-Agent": "TVD-Console/1.0",
                     "Authorization": "Basic " + _b64.b64encode(b"app:DeanDiablo").decode()},
            method="POST")
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = r.read()
            code = getattr(r, "status", None) or r.getcode()
        # v1597 — the server answers {ok, machine, recorded, stored, fleet}. Parse DEFENSIVELY:
        # a body that is empty, HTML (a captive portal) or a changed shape must never raise here.
        fleet = None
        try:
            _b = json.loads(raw.decode("utf-8", "replace"))
            if isinstance(_b, dict) and isinstance(_b.get("fleet"), (int, float)) and not isinstance(_b.get("fleet"), bool):
                fleet = int(_b["fleet"])
        except Exception:
            fleet = None
        with _BEACON_LOCK:
            _BEACON_LAST["ok"] = True
            _BEACON_LAST["code"] = code
            _BEACON_LAST["err"] = ""
            _BEACON_LAST["okAt"] = _ts_iso
            _BEACON_LAST["fleet"] = fleet
    except Exception as e:
        _c = getattr(e, "code", None)
        with _BEACON_LOCK:
            _BEACON_LAST["ok"] = False
            _BEACON_LAST["t"] = _ts_iso
            _BEACON_LAST["ts"] = _ts_epoch
            _BEACON_LAST["code"] = _c if isinstance(_c, int) else None
            _BEACON_LAST["err"] = type(e).__name__ + ": " + str(e)[:200]
            _BEACON_LAST["failures"] = int(_BEACON_LAST.get("failures") or 0) + 1
        pass   # STILL fire-and-forget — the caller must never learn this failed
    _beacon_state_save()


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
    the console poll went 300ms × (ping 0.6s + state 0.8s + lsof) and choked itself.

    v1424 — STICKY STATE: a failed /state fetch under D2R load must NOT wipe the last good
    snapshot. Live proof: ping ok + state timeout → eyeAgeMs=-1, READS 0, dark film while
    the agent was healthy (reads≥1, eye fresh, pin PrintWindow).

    v1435 — ONE hop: fetch /state first (carries online+eye+reads). Skip separate /ping when
    state succeeds. Half the HTTP traffic under D2R load."""
    while True:
        try:
            now = time.time()
            # v1435 — prefer single /state; fall back to ping-only keepalive
            st_new = _bridge_state()
            if st_new is not None:
                _BR_CACHE["ping"] = True
                _BR_CACHE["st"] = st_new
                _BR_CACHE["st_ts"] = now
                _BR_CACHE["ts"] = now
                globals()["_BRIDGE_LAST_OK"] = now
            else:
                ping = _bridge_ping() is not None
                _BR_CACHE["ping"] = ping
                _BR_CACHE["ts"] = now
                if ping:
                    globals()["_BRIDGE_LAST_OK"] = now
                elif now - float(_BR_CACHE.get("st_ts") or 0) > 12.0:
                    _BR_CACHE["st"] = None
        except Exception:
            pass
        # v1435 — 1.0s on Windows (was 0.9); less thrash, still honest
        time.sleep(1.0 if IS_WIN else 1.2)


def _bridge_ping():
    # v1427 — Windows under D2R: 0.6s was too tight (false STANDBY / empty status)
    _to = 1.2 if IS_WIN else 0.6
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{AGENT_PORT}/ping", timeout=_to
        ) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None


def _bridge_state():
    # v1427 — /state can be large; give Windows room under D2R CPU contention
    # v1440 — ?lite=1 trims fat rings so prober stays smooth under 1920 film + vision
    _to = 1.5 if IS_WIN else 0.8
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{AGENT_PORT}/state?lite=1", timeout=_to
        ) as r:
            got = json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None
    # v1456 HONESTY (audit, v1452 bug class): a degenerate payload — {} or a non-dict — used to be
    # cached as a GOOD snapshot and stamped _BRIDGE_LAST_OK, so the console painted "live" off a
    # body that carried no state at all. Real /state always ships "online" + "now"; anything
    # without them is treated as a miss, so the prober keeps its last good snapshot instead.
    if not isinstance(got, dict) or not ("online" in got or "now" in got):
        return None
    return got


def _disk_eye_age_ms():
    """v1425 — honest film age from frames/eye.jpg when bridge state is mid-fetch."""
    try:
        eye = os.path.join(HERE, "frames", "eye.jpg")
        if not os.path.isfile(eye):
            return -1
        return max(0, int((time.time() - os.path.getmtime(eye)) * 1000))
    except Exception:
        return -1


def _disk_cap_target():
    """v1426 — Windows pin truth from capture_win even when /state is slow."""
    try:
        p = os.path.join(HERE, "frames", "cap_target.json")
        if not os.path.isfile(p):
            return {}
        with open(p, encoding="utf-8-sig") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


_TZ_CACHE = {"ts": 0.0, "code": 0, "body": None}
_TZ_LOCK = threading.Lock()
_TZ_UPSTREAM = os.environ.get("TVD_TZ_UPSTREAM", "https://bull-4-u.com/api/tz")
_TZ_AUTH = base64.b64encode(b"app:DeanDiablo").decode("ascii")
# v1710 — the public function is /api/tz (ungated). /d2r/api/tz is the same
# payload behind SITE_PASS, and a "fixed" upstream that pointed there 401'd
# every relay. Try the public path first; keep the gated cousin as a fallback
# for the day the function moves under /d2r/.
_TZ_UPSTREAMS = []
if _TZ_UPSTREAM:
    _TZ_UPSTREAMS.append(_TZ_UPSTREAM)
for _u in ("https://bull-4-u.com/api/tz", "https://bull-4-u.com/d2r/api/tz"):
    if _u not in _TZ_UPSTREAMS:
        _TZ_UPSTREAMS.append(_u)


def _tz_ssl_context():
    """Windows Python often has no CA bundle; a public TZ JSON is not a secret.

    Prefer certifi, then the platform defaults, then unverified as last resort
    so a missing cert store cannot paint 'could not reach the live site' over
    a rotation that is actually up.
    """
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        try:
            return ssl.create_default_context()
        except Exception:
            return ssl._create_unverified_context()


def _tz_has_payload(body):
    if not isinstance(body, dict):
        return False
    if body.get("current") or body.get("next"):
        return True
    hist = body.get("history")
    return isinstance(hist, list) and len(hist) > 0


def _tz_fetch_one(url, ctx):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) TVDiablo/1710",
        "Accept": "application/json",
    }
    # the public /api/tz path is ungated; Basic on a WRONG password is how
    # /d2r/api/tz used to 401 the whole relay. Only send it on the gated path.
    if "/d2r/" in url:
        headers["Authorization"] = "Basic " + _TZ_AUTH
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=12, context=ctx) as r:
        raw = r.read().decode("utf-8", "replace")
        body = json.loads(raw)
        return getattr(r, "status", 200), body


def _tz_proxy():
    # Terror Zone tracker relay: the board's /api/tz only exists as a Pages
    # function on the live deploy; the shell serves the board locally, so we
    # fetch upstream and cache 90s. Upstream dead → last good rotation flagged
    # stale. An empty `current` WITH history is a live payload, not DOWN.
    with _TZ_LOCK:
        now = time.time()
        # v1813 — THE CACHE MUST NOT OUTLIVE THE SLOT IT DESCRIBES.
        #
        # Konyo, 2026-08-19, screenshot stamped 20:00:32: the panel read "Burial Grounds, Crypt,
        # and Mausoleum" as LIVE NOW and "not published yet" for UP NEXT. Burial Grounds was the
        # 19:30 slot. The turn had happened 32 seconds earlier and the console was showing the
        # previous zone.
        #
        # It was not the poll cadence — v1586/v1587 already fetch six seconds after the boundary
        # and drop to 60s while NEXT is missing. It was THIS cache, one layer down. A body fetched
        # at 19:59:20 stayed servable until 20:00:50, so the console's careful 20:00:06 fetch got
        # the pre-turn answer, and the next poll was a further 60s away. The relay was faithfully
        # serving a reading whose subject had stopped existing.
        #
        # A time-to-live is the wrong instrument for a value that changes on a SCHEDULE rather
        # than by age. 90 seconds is a sensible age for this payload everywhere except across the
        # one instant that makes it wrong. So the cache is valid while it is young AND still
        # inside the slot it was read in; the rotation runs on exact 30-minute UTC boundaries
        # (every slot stamp in the feed's own history divides by 1800000 with no remainder), so
        # the slot index is arithmetic, not a guess. [[stale-reading]]
        _SLOT_S = 1800
        _fresh = _TZ_CACHE["body"] is not None and now - _TZ_CACHE["ts"] < 90
        _same_slot = int(_TZ_CACHE["ts"] // _SLOT_S) == int(now // _SLOT_S)
        if _fresh and _same_slot:
            return _TZ_CACHE["code"], _TZ_CACHE["body"]
        last_err = None
        ctx = _tz_ssl_context()
        for url in _TZ_UPSTREAMS:
            try:
                code, body = _tz_fetch_one(url, ctx)
                if code == 200 and _tz_has_payload(body):
                    body = _tz_mark_turning(body)
                    _TZ_CACHE.update(ts=now, code=200, body=body)
                    return 200, body
                last_err = "http %s no rotation" % code
            except Exception as e:
                last_err = e
                continue
        if _TZ_CACHE["body"] is not None:
            stale = dict(_TZ_CACHE["body"])
            stale["stale"] = True
            # re-derived against NOW: a cached body served later is further behind than when it
            # was fetched, and the flag has to age with it rather than be frozen at fetch time.
            return 200, _tz_mark_turning(stale)
        return 502, {"error": f"tz upstream unreachable: {last_err}"}


def _tz_mark_turning(body, now_ms=None):
    """v1831 — SAY WHEN THE FEED IS BEHIND THE CLOCK, instead of printing its answer as live.

    Konyo asked whether the TZ tracker "should be refreshed maybe also more often". Measured across
    a real boundary on 2026-08-20 rather than guessed, sampling upstream every 45s:

        07:29:59  +1799s | cur=Burial Grounds ...      | next=Kurast Bazaar ...
        07:30:44  +  44s | cur=Burial Grounds ...      | next=Kurast Bazaar ...   <- slot ALREADY turned
        07:31:29  +  89s | cur=Kurast Bazaar ...       | next=Nihlathak's Temple ...

    Forty-four seconds after the rotation, UPSTREAM was still calling the previous zone `current`.
    So the answer to his question is no: polling faster cannot fix this, because the staleness is
    not ours. v1813 already fixed OUR cache (it must not outlive the slot it describes) and the
    board already re-fetches six seconds after the boundary — and gets a payload the feed has not
    updated yet. For up to ~90s the console prints a zone that stopped being live, exactly the
    complaint v1813 answered, arriving through the other door.

    It is derivable with no extra request. Every slot stamp in the feed's own history divides by
    1800000 with no remainder, so "which slot does upstream think it is in" is arithmetic: if its
    newest history slot is older than the slot we are actually in, its `current` describes a zone
    that has already ended. That is reported as a FIELD (`turning`, `slotBehind`) rather than
    patched over — the reading is upstream's to make, and ours to label honestly. [[stale-reading]]

    Additive by construction: no existing key changes value, so a board that has never heard of
    `turning` renders exactly as it did before.
    """
    if not isinstance(body, dict):
        return body
    now_ms = int(time.time() * 1000) if now_ms is None else int(now_ms)
    slot_ms = 1800000
    here = (now_ms // slot_ms) * slot_ms
    newest = None
    for row in (body.get("history") or []):
        if isinstance(row, dict) and isinstance(row.get("slot"), (int, float)):
            v = int(row["slot"])
            if newest is None or v > newest:
                newest = v
    if newest is None:
        # NOT measured is not the same as NOT behind. Nothing is claimed when nothing can be read.
        body["slotBehind"] = None
        body["turning"] = False
        return body
    behind = int((here - newest) // slot_ms)
    body["slotBehind"] = behind
    # Only the ONE-slot case is a turnover. Many slots behind is a broken or frozen feed, which is
    # what `stale` already means, and calling that "turning over" would flatter it.
    body["turning"] = behind == 1
    return body


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
        # v1414 — never shell tasklist (hangs under D2R load → freezes /api/status + UI).
        try:
            import ctypes
            from ctypes import wintypes
            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
            if not handle:
                return False
            try:
                code = wintypes.DWORD()
                if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                    return False
                return int(code.value) == STILL_ACTIVE
            finally:
                kernel32.CloseHandle(handle)
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
        # v1412 — cwd=HERE (tv/) so relative logs are next to the script; pass absolute -File
        # for Hebrew/spaces USERPROFILE. CREATE_NO_WINDOW so Desktop launch stays quiet.
        env2 = dict(env or os.environ)
        env2.setdefault("TV_CAPTURE", os.environ.get("TV_CAPTURE") or "auto")
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
            cwd=HERE,
            env=env2,
            stdout=log_fp,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            creationflags=_WIN_CREATE,
        )
        # v1441 — BelowNormal so D2R + console UI keep the cores
        try:
            import psutil  # optional
            psutil.Process(_capture_proc.pid).nice(psutil.BELOW_NORMAL_PRIORITY_CLASS if IS_WIN else 10)
        except Exception:
            try:
                import ctypes
                handle = ctypes.windll.kernel32.OpenProcess(0x0200 | 0x0400, False, int(_capture_proc.pid))
                if handle:
                    # BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
                    ctypes.windll.kernel32.SetPriorityClass(handle, 0x00004000)
                    ctypes.windll.kernel32.CloseHandle(handle)
            except Exception:
                pass
        _write_pid(CAP_PID_PATH, _capture_proc.pid)
        log_fp.write(f"capture_win.ps1 pid {_capture_proc.pid} file={CAPTURE_PS1}\n")
        log_fp.flush()
        return _capture_proc.pid
    except Exception as e:
        log_fp.write(f"!! capture start failed: {e}\n")
        log_fp.flush()
        return None


_CAP_RESTART_N = 0
_CAP_RESTART_TS = 0.0
_CAP_RESTART_MAX = 5          # v1412 — cousin Windows: capture_win can die; restart more than once
_CAP_RESTART_COOLDOWN_S = 8.0


def _capture_health():
    """v793 (Grok R4 #5a) — Windows capture lamp: LINKED / DEAD / n/a. A dead capture_win.ps1
    used to leave a frozen eye with the lamp still mint. Auto-restart, loudly.

    v1412 — up to 5 restarts with cooldown (was once forever-DEAD). Cousin ON AIR often
    saw 'NO CAPTURE — Windows capture process died' after a single PS crash/exit."""
    global _CAP_RESTART_N, _CAP_RESTART_TS
    if not IS_WIN:
        return ""
    if _agent_mode not in ("live", "sim"):
        _CAP_RESTART_N = 0
        _CAP_RESTART_TS = 0.0
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
    now = time.time()
    if (_CAP_RESTART_N < _CAP_RESTART_MAX
            and (now - _CAP_RESTART_TS) >= _CAP_RESTART_COOLDOWN_S
            and _log_fp):
        _CAP_RESTART_N += 1
        _CAP_RESTART_TS = now
        try:
            _log_fp.write(
                f"!! capture_win.ps1 DIED mid-session — auto-restart "
                f"{_CAP_RESTART_N}/{_CAP_RESTART_MAX}\n")
            _log_fp.flush()
            # clear stale pid so _start_capture does not think a corpse is alive
            try:
                if os.path.isfile(CAP_PID_PATH):
                    os.remove(CAP_PID_PATH)
            except Exception:
                pass
            with _lock:
                globals()["_capture_proc"] = None
            _start_capture(_env_clean(sim=(_agent_mode == "sim")), _log_fp)
            return "RESTARTED"
        except Exception as e:
            try:
                _log_fp.write(f"!! capture restart failed: {e}\n")
                _log_fp.flush()
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


def start_agent(sim=False, test=False, mini=None, focus=None):
    """mini/focus — the ⏱ MINI CAPTURE bound (seconds, already clamped) and the ONE focus name.
    They are appended to the SPAWN ARGV on BOTH platforms so the cousin's Windows box gets the
    identical agent invocation; nothing about the mini branches on platform."""
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
        # v1380.4 — deep hunt for Claude (Desktop shortcut PATH is often incomplete on Windows)
        if not sim and not env.get("TV_STUB"):
            claude_bin = env.get("TV_CLAUDE_BIN") or _find_claude_bin(env.get("PATH", ""))
            if not claude_bin:
                _agent_mode = "off"
                _log_fp.write("!! claude CLI not found (PATH hunt failed) - agent cannot see\n")
                _log_fp.flush()
                return {"ok": False,
                        "error": "Claude Code CLI not found — ON AIR needs Claude to read the game",
                        "fix": ("In PowerShell run:\n  irm https://claude.ai/install.ps1 | iex\n"
                                "Then open a NEW PowerShell, run:  claude\n"
                                "(finish login once), close it, double-click TV DIABLO again."
                                if IS_WIN
                                else "curl -fsSL https://claude.ai/install.sh | bash && claude"),
                        "mode": "off"}
            env["TV_CLAUDE_BIN"] = claude_bin
            _log_fp.write("claude CLI: %s\n" % claude_bin)
            _log_fp.flush()
        # Windows needs the capture half; Mac agent uses screencapture itself
        if IS_WIN:
            cap_pid = _start_capture(env, _log_fp)
            if not cap_pid:
                _log_fp.write("!! Windows capture did not start — frames may be empty\n")
                _log_fp.flush()

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

        py_exe = _agent_python()
        if IS_WIN and "windowsapps" in (py_exe or "").lower():
            _agent_mode = "off"
            msg = ("Windows Store Python stub detected — it cannot spawn the scanner. "
                   "Install real Python from python.org (or winget install Python.Python.3.12), "
                   "turn OFF App execution aliases for python.exe, re-run the TV DIABLO installer.")
            _log_fp.write("!! " + msg + "\n")
            _log_fp.flush()
            return {"ok": False, "error": msg, "mode": "off",
                    "fix": "winget install Python.Python.3.12  then re-run install-tvd.ps1"}

        cmd = [py_exe, os.path.join(HERE, "tv_diablo.py")]
        if IS_WIN:
            cmd.append("--watch")
        # ⏱ MINI CAPTURE — the ONE flag name and the ONE focus name, appended for mac AND
        # windows (the cousin's box must get the identical argv). An agent build that does not
        # know them ignores them and the watchdog still seals on time.
        if mini:
            try:
                cmd.append("%s=%d" % (MINI_FLAG, int(mini)))
                # v1783 — PASS THE FLAG ONLY WHEN HE ACTUALLY CHOSE A FOCUS. It used to be sent
                # every time, filled in with the default, which made "the flag is present" mean
                # nothing — and the reel then carried a declaration he never made. The sweep skips
                # the classifier for a declared focus, so an untouched default labelled town, a
                # fight and a Chronicle page as a stash panel without looking at any of them.
                # tv_diablo still falls back to MINI_FOCUS for its own capture behaviour; what
                # changes is that the reel is no longer stamped as CHOSEN when it was not.
                if focus and str(focus).strip().lower() in MINI_FOCUSES:
                    cmd.append("%s=%s" % (MINI_FOCUS_FLAG, str(focus).strip().lower()))
            except (TypeError, ValueError):
                pass
        _log_fp.write("spawn: %s\n" % " ".join(cmd))
        _log_fp.flush()

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

        try:
            _agent_proc = subprocess.Popen(**popen_kw)
        except Exception as e:
            _agent_mode = "off"
            _log_fp.write("!! Popen failed: %s\n" % e)
            _log_fp.flush()
            return {"ok": False, "error": "failed to start scanner: %s" % e, "mode": "off"}
        _write_pid(PID_PATH, _agent_proc.pid)
        _agent_mode = "sim" if sim else "live"

    for _ in range(50):
        if _bridge_ping() is not None:
            break
        time.sleep(0.15)
    # v786 - a dead-at-boot agent must SAY SO, not leave the lamp spinning (cousin's Windows hang)
    # v1380.4 — ALSO fail if the process is ALIVE but never opened the bridge (hung boot)
    if _bridge_ping() is None:
        with _lock:
            alive = _agent_proc is not None and _agent_proc.poll() is None
            if alive:
                try:
                    _agent_proc.kill()
                except Exception:
                    pass
                try:
                    _agent_proc.wait(timeout=2)
                except Exception:
                    pass
            _agent_mode = "off"
            _agent_proc = None
        tail = ""
        try:
            with open(LOG_PATH, "rb") as _lf:
                tail = _lf.read()[-2000:].decode("utf-8", "replace")
        except Exception:
            pass
        hint = "agent died at boot"
        low = tail.lower()
        if "claude" in low and ("not found" in low or "no such file" in low):
            hint = "Claude CLI missing or not on PATH"
        elif "permission" in low or "access is denied" in low:
            hint = "permission denied starting the scanner"
        elif "address already in use" in low or "10048" in low:
            hint = "port 17771 already in use — close other TV DIABLO / reboot"
        return {"ok": False,
                "error": hint + " — see log / Doctor",
                "logTail": tail,
                "mode": "off",
                "fix": ("Run Doctor in the console, or re-install: irm https://bull-4-u.com/d2r/install-tvd.ps1 | iex"
                        if IS_WIN else "bash tv/install-tvd.sh")}
    with _lock:
        _pid = _agent_proc.pid if _agent_proc else None
        _mode = _agent_mode
    return {
        "ok": True,
        "msg": "started",
        "mode": _mode,
        "pid": _pid,
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


def _mark_window_gone(reason=""):
    """v1410 — drop every live-window handle FIRST so no thread can evaluate_js a dying
    WKWebView (the hang-report class). Safe to call many times; never blocks."""
    globals()["_WINDOW_LIVE"] = False
    globals()["_MAIN_WIN"] = None
    globals()["_ENGINE_ALIVE"] = False
    globals()["_ENGINE_READY"] = False
    if reason:
        print(f"📺 window gone ({reason}) — engine probes disabled", flush=True)


def _arm_force_exit(reason="quit", delay=None):
    """v1420 — hard process death after ✕/Esc, even when Cocoa never returns from
    webview.start(). Idempotent. Never blocks the caller (UI/close thread safe).

    delay defaults to _FORCE_EXIT_DELAY_S (~1.25s): long enough for async stop_agent to
    seal ON AIR; short enough that Force Quit is never the user's only option."""
    global _FORCE_EXIT_ARMED
    if delay is None:
        delay = float(globals().get("_FORCE_EXIT_DELAY_S") or 1.25)
    with _FORCE_EXIT_LOCK:
        if _FORCE_EXIT_ARMED:
            return False
        _FORCE_EXIT_ARMED = True
    def _die():
        try:
            time.sleep(max(0.05, float(delay)))
        except Exception:
            pass
        # v1463 — a disarm switch. Without it this thread is un-cancellable: it resolves
        # os._exit at FIRE time, so anything that temporarily monkeypatches os._exit (the
        # test suite does, to assert arming) gets the REAL one back before the deadline and
        # the runner is killed mid-suite with exit code 0 and no summary line — a false
        # green. A quit that was called off should never still take the process down.
        if globals().get("_FORCE_EXIT_CANCEL"):
            return
        try:
            print(f"📺 force-exit deadline ({reason}) — os._exit(0)", flush=True)
        except Exception:
            pass
        try:
            os._exit(0)
        except Exception:
            pass
    try:
        threading.Thread(target=_die, daemon=True, name="tvd-force-exit").start()
    except Exception:
        try:
            os._exit(0)
        except Exception:
            pass
    return True


def _request_console_exit(reason="quit", hard_delay=None):
    """v1420 — single exit surface for ✕, Esc→/api/quit, and webview-return.

    Order matters:
      1) capture window handle BEFORE mark clears it
      2) mark gone (kill evaluate_js probes)
      3) async stop ON AIR (never on Cocoa UI thread)
      4) arm hard os._exit deadline (Force-Quit killer)
      5) best-effort destroy the native window

    Safe on every thread; never blocks more than a few ms.

    v1576 — RETURNS AN HONEST RECEIPT. Every step here is best-effort try/except, so
    a total failure used to be indistinguishable from a clean exit: /api/quit answered
    {"ok": True, "msg": "control quitting"} while nothing was armed and the process
    stayed up forever. Ground truth for "the process WILL die" is the module flag
    _FORCE_EXIT_ARMED (not _arm_force_exit's return value — that is False on the
    idempotent second call, which is a success, not a failure). Callers that do not
    care may keep ignoring the return."""
    win = globals().get("_MAIN_WIN")
    errs = []
    marked = False
    stop_scheduled = False
    destroyed = False
    try:
        _mark_window_gone(reason)
        marked = True
    except Exception as e:
        errs.append("mark_window_gone: %s" % str(e)[:80])
    try:
        _schedule_exit_stop(reason)
        stop_scheduled = True
    except Exception as e:
        errs.append("schedule_exit_stop: %s" % str(e)[:80])
    try:
        _arm_force_exit(reason, delay=hard_delay)
    except Exception as e:
        errs.append("arm_force_exit: %s" % str(e)[:80])
    armed = bool(globals().get("_FORCE_EXIT_ARMED"))
    if win is not None:
        # v1460 — DESTROY ONLY. The old chain fell back to hide() when destroy() raised,
        # which produced the worst possible state: process alive, still holding :17772, with
        # an SW_HIDE-ed window that no focus path could ever find again (the Desktop icon
        # then did nothing forever). Never hide on the way out — if destroy() fails, the
        # _arm_force_exit deadline above takes the whole process down and the window with it.
        try:
            fn = getattr(win, "destroy", None)
            if callable(fn):
                fn()
                destroyed = True
        except Exception as e:
            errs.append("window_destroy: %s" % str(e)[:80])
            print(f"⚠ window destroy failed ({e}) — force-exit deadline will close it", flush=True)
    return {
        "ok": bool(armed or destroyed),
        "armed": armed,
        "windowDestroyed": destroyed,
        "markedGone": marked,
        "stopScheduled": stop_scheduled,
        "reason": reason,
        "errors": errs,
    }


def _schedule_exit_stop(reason="quit"):
    """v1410 — NEVER run stop_agent on the Cocoa UI/close thread. Fire-and-forget daemon
    so ✕ dismisses the window instantly; ON AIR still gets sealed in the background."""
    def _run():
        try:
            _console_exit_stop_onair(reason)
        except Exception as e:
            print(f"⚠ async exit stop failed ({e})", flush=True)
    try:
        threading.Thread(target=_run, daemon=True, name="tvd-exit-stop").start()
    except Exception:
        # last resort — still try not to raise into Cocoa
        try:
            _console_exit_stop_onair(reason)
        except Exception:
            pass


def _console_exit_stop_onair(reason="quit"):
    """v935.8 — EXIT SAFEGUARD (Konyo: 'exiting the console must stop ON AIR — it's always on').

    Closing the pywebview window used to only `srv.shutdown()` and LEAVE the agent live on
    :17771 (the banner even said 'agent left as-is'). That orphan kept ON AIR forever.
    Now every real exit path — window close, atexit, SIGTERM/SIGINT — seals + stops the
    agent (same as tvd stop /api/stop, farewell OFF so quit is instant). Idempotent.

    v1379.2 — also CLEAR the supervisor pause flag after a primary --open session ends, so
    tvd_supervisor can bring headless :17772 back up. Reclaim writes the pause so Desktop
    can steal the port; without clearing it, the always-up console stays dead forever.

    v1410 — HARD CAP ~3s (force-kill path). Must never run on the UI/close thread (use
    _schedule_exit_stop). Long waits here = beachball + Apple Python_*.hang reports.
    """
    global _EXIT_STOP_DONE
    # Secondary --window-only attach: the primary control process owns the agent.
    if globals().get("_WINDOW_ONLY"):
        return {"ok": True, "msg": "window-only — primary owns ON AIR", "skipped": True}
    with _EXIT_STOP_LOCK:
        if _EXIT_STOP_DONE:
            return {"ok": True, "msg": "exit stop already ran", "skipped": True}
        _EXIT_STOP_DONE = True
    # Always kill window probes first — even if stop is already done elsewhere
    _mark_window_gone(reason)
    print(f"📺 exit safeguard — stopping ON AIR ({reason})…", flush=True)
    result = {"ok": True, "msg": "already off", "farewell": False}
    t0 = time.time()
    try:
        # If nothing is on air, stop_agent is cheap and returns already-off.
        if not _agent_alive() and _port_listener_pid() is None and _agent_mode == "off":
            print("   already off — nothing to stop", flush=True)
        else:
            try:
                r = stop_agent(farewell=False)
                print(f"   stop_agent → {r.get('msg') or r}", flush=True)
                # Belt + suspenders: anything still holding :17771 dies now
                if _port_listener_pid() is not None or _agent_alive():
                    r2 = _force_kill_all_agents(f"exit-safeguard residual ({reason})")
                    print(f"   residual force → {r2.get('msg') or r2}", flush=True)
                    result = r2
                else:
                    result = r
            except Exception as e:
                print(f"   stop_agent raised ({e}) — force kill", flush=True)
                try:
                    result = _force_kill_all_agents(f"exit-safeguard ({reason}): {e}")
                except Exception as e2:
                    print(f"   force kill failed: {e2}", flush=True)
                    result = {"ok": False, "msg": str(e2)}
        # Hard cap: never sit in exit longer than ~3s total (hang-report class)
        if time.time() - t0 > 3.0:
            try:
                _force_kill_all_agents(f"exit-safeguard hardcap ({reason})")
            except Exception:
                pass
            result = dict(result or {}, hardcap=True)
    except Exception:
        pass
    # ── v1609 — THE APP NO LONGER HANDS RECORDING AWAY ON ITS OWN WAY OUT ────────────────
    # This used to os.remove() the supervisor pause flag whenever a windowed session ended,
    # to "resume the always-up headless console". That intent was fine when a headless console
    # could still record. It cannot: a launchd-spawned console holds no Screen Recording grant
    # (VERIFIED 2026-08-03 — TV DIABLO.app granted, headless-from-shell granted,
    # headless-from-launchd NOT granted, even after the python3 binary was granted in System
    # Settings). So clearing the flag here silently swapped a recording-capable console for one
    # that refuses ON AIR, and the supervisor did it within ~20 s.
    #
    # It fired FOUR times in one night. Each time Konyo pressed record and got a black screen,
    # and each time the recovery was a command he had to be told again.
    #
    # v1608 already made tv/tvd-console.sh refuse this by default and demand --force, on exactly
    # this reasoning. Doing the same thing implicitly from an exit handler is the same act with
    # less consent, so it stops here too: the flag STAYS, and the line says what did not happen
    # and how to ask for it deliberately. Handing the port back is now always a choice.
    try:
        pause = os.path.join(HERE, ".tvd_supervisor_pause")
        if os.path.isfile(pause) and not globals().get("_WINDOW_ONLY"):
            print("   supervisor pause KEPT — the always-up headless console was NOT restored, "
                  "because it cannot hold Screen Recording (ON AIR would refuse and nothing "
                  "would record). To hand the port back on purpose: "
                  "bash tv/tvd-console.sh --force", flush=True)
    except Exception as _pe:
        print(f"   pause check skipped: {_pe}", flush=True)
    print(f"   exit stop done in {time.time()-t0:.2f}s", flush=True)
    return result


# ── REEL INDEX — a reel with frames on disk must never render as a BLACK theatre ──────────────
# 2026-08-03: reel_s_1785708285647_38665 held 98 real JPGs and NO index.json, so every reader in
# this file (reel listing, kai closer, mini-seal count, theatre footage) skipped it and Konyo saw a
# black screen and reported "still not recording" — the capture had worked perfectly. The agent
# writes the index at the END of a per-frame blank-detect pass that DECODES every archived JPEG
# (measured 0.076 s/frame on this Mac → ~7.4 s for 98 frames); the console's 2.5 s force-kill landed
# inside that pass. SEAL-1 makes the index durable at the source; these helpers are the console's
# belt: an index rebuilds from the f_<epoch-ms>.jpg filenames, which is exactly what its rows carry.
# The reconstruction READER lives in chronicle_retro (load_index); the WRITER is reel_index.
# ensure_reel_index() (v1608 — chronicle_retro must stay provably write-free). It is NEVER
# duplicated here — one implementation, one truth.


def _cr_index_api():
    """(reel_index.ensure_reel_index, chronicle_retro.load_index), or (None, None).

    Imported lazily and defensively: a chronicle_retro that is missing, unimportable, or older than
    these symbols must degrade the console to its pre-repair behaviour, never break it."""
    try:
        import chronicle_retro as _cr
    except Exception:
        return None, None
    try:
        import reel_index as _ri          # v1608 — the WRITER lives here; chronicle_retro stays read-only
    except Exception:
        _ri = None
    return (getattr(_ri, "ensure_reel_index", None) if _ri else None), getattr(_cr, "load_index", None)


def _reel_jpg_count(reel_dir):
    """Frames actually on disk for this reel. Counted, never estimated: 0 means 0."""
    try:
        return sum(1 for f in os.listdir(reel_dir)
                   if f.startswith("f_") and f.lower().endswith(".jpg"))
    except Exception:
        return 0


def _seal_index_ok(reel_dir):
    try:
        p = os.path.join(reel_dir, "index.json")
        return os.path.isfile(p) and os.path.getsize(p) > 0
    except Exception:
        return False


def _seal_progress(reel_dir):
    """A cheap signature of a seal in flight, or None when there is no reel dir to seal into.
    (index-on-disk, tmp-present, frames archived, index bytes) — any change means the agent is
    still working, so the stop path may extend its patience."""
    if not reel_dir:
        return None
    try:
        names = os.listdir(reel_dir)
    except Exception:
        return None
    idx_sz = 0
    try:
        idx_sz = os.path.getsize(os.path.join(reel_dir, "index.json"))
    except Exception:
        pass
    return (idx_sz > 0,
            any(n.startswith("index.json.") for n in names),
            sum(1 for n in names if n.startswith("f_") and n.lower().endswith(".jpg")),
            idx_sz)


def _seal_sid_hint():
    """The session whose reel is being sealed right now: the bridge knows, then the journal's last
    row, then the newest reel_* dir. "" when unknown — a WRONG sid must never buy grace for a reel
    nobody is writing, so every fallback is evidence off disk, never a guess."""
    try:
        sid = _mini_sid()
        if sid:
            return str(sid)
    except Exception:
        pass
    try:
        with open(_journal_path(), "rb") as fh:
            fh.seek(0, os.SEEK_END)
            back = min(fh.tell(), 8192)
            fh.seek(-back, os.SEEK_END)
            tail = fh.read().decode("utf-8", "replace").splitlines()
        for ln in reversed(tail):
            try:
                sid = (json.loads(ln) or {}).get("sessionId")
            except Exception:
                continue
            if sid:
                return str(sid)
    except Exception:
        pass
    try:
        cands = [d for d in os.listdir(HIST_DIR)
                 if d.startswith("reel_") and os.path.isdir(os.path.join(HIST_DIR, d))]
        if cands:
            newest = max(cands, key=lambda d: os.path.getmtime(os.path.join(HIST_DIR, d)))
            return newest[len("reel_"):]
    except Exception:
        pass
    return ""


def _reel_ensure_index(reel_dir):
    """Guarantee reel_dir has a playable index.json when it holds frames.

    → (playable, rebuilt). Never raises: a repair failure degrades to exactly today's behaviour
    (the reel is treated as it sits on disk) and says so on the console instead of hiding."""
    try:
        had = os.path.isfile(os.path.join(reel_dir, "index.json"))
    except Exception:
        return False, False
    ensure, _load = _cr_index_api()
    if ensure is None:
        return had, False
    try:
        got = ensure(reel_dir)
    except Exception as e:
        print("\u26a0 index repair failed for %s: %s" % (os.path.basename(reel_dir), e), flush=True)
        return had, False
    ok = got is not None
    return ok, bool(ok and not had)


def _reel_index_frames(reel_dir, repair=True):
    """This reel's frame rows [{"f":..., "ts":...}, ...] via chronicle_retro.load_index(), so a reel
    that lost its index still plays. None = genuinely unreadable (callers keep their own fallbacks).
    A repair failure can never raise into an HTTP handler — it degrades and logs."""
    try:
        if repair:
            _reel_ensure_index(reel_dir)
        _ensure, load = _cr_index_api()
        if load is not None:
            try:
                idx = load(reel_dir)
            except Exception as e:
                print("\u26a0 index read failed for %s: %s" % (os.path.basename(reel_dir), e),
                      flush=True)
                idx = None
            if isinstance(idx, dict):
                return idx.get("frames") or []
            if isinstance(idx, list):
                return idx
            if idx is not None:
                return []
        # chronicle_retro too old / unimportable -> the pre-repair read, unchanged
        with open(os.path.join(reel_dir, "index.json"), encoding="utf-8") as _jf:
            return (json.load(_jf) or {}).get("frames") or []
    except Exception:
        return None


def _reels_missing_index(hist=None):
    """[(reel dir name, frames on disk)] for reels holding f_*.jpg with NO index.json — i.e. real
    footage the theatre currently plays as black. Only dirs behind the reel_ guard: cache160 and
    cache1280 are thumbnail caches (24/32 jpgs), not reels, and must never be flagged."""
    hist = hist or HIST_DIR
    out = []
    try:
        names = sorted(os.listdir(hist))
    except Exception:
        return out
    for d in names:
        rd = os.path.join(hist, d)
        if not (d.startswith("reel_") and os.path.isdir(rd)):
            continue
        if os.path.isfile(os.path.join(rd, "index.json")):
            continue
        n = _reel_jpg_count(rd)
        if n > 0:
            out.append((d, n))
    return out


def _reel_sweep_indexes(hist=None, why="boot"):
    """Rebuild every missing reel index under HIST_DIR and SAY IT OUT LOUD — a silently repaired
    reel is the same class of bug as a silently lost one. Prints nothing when the count is 0.
    -> [(reel name, frames)] repaired."""
    fixed = []
    for d, _n in _reels_missing_index(hist):
        rd = os.path.join(hist or HIST_DIR, d)
        _ok, rebuilt = _reel_ensure_index(rd)
        if rebuilt:
            fixed.append((d, _reel_jpg_count(rd)))
    if fixed:
        print("\U0001fa79 rebuilt missing index for %d reel%s [%s]: %s"
              % (len(fixed), "" if len(fixed) == 1 else "s", why,
                 ", ".join("%s (%d frames)" % (d, n) for d, n in fixed)), flush=True)
    return fixed


def stop_agent(farewell=True):
    """v847/v899 — OFF/STOP both SAVE the session (session_end journal via /shutdown).
    STOP: short farewell (hard-cap ~18s, was 95s). OFF: seal only. Then hard-kill orphans.
    Never leave _stop_inflight True if the agent is already dead (unstick ON AIR)."""
    global _agent_proc, _agent_mode, _stop_inflight, _BOARD_OPENED
    # v1578 — ⏱ MINI stands down on EVERY seal path, not just its own deadline. He presses END
    # SESSION by hand at 12s; without this the latch stays up for the remaining 28s (ON AIR
    # refuses "already recording") and the watchdog then fires a SECOND stop that could land on
    # a session he started in between. _mini_seal() clears the flag BEFORE it calls here, so
    # this is a no-op on the timer's own path — no recursion, no double kill.
    try:
        with _MINI_LOCK:
            # "arming" fences the ONE stop_agent() that start_agent() itself may fire to clear a
            # port orphan while the mini is booting. Without the fence that internal stop would
            # stand the watchdog down and the mini would run UNBOUNDED — the exact outcome the
            # button exists to prevent.
            if _MINI["running"] and not _MINI.get("arming"):
                _MINI["running"] = False
                _MINI["sealedTs"] = int(time.time() * 1000)
                _MINI["sealedBy"] = "hand"
    except Exception:
        pass
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

        # 3) Wait for bridge death, then FORCE-KILL.
        #    v946.2 wrote "2.5s max ... seal is already on disk before kill". THAT ASSERTION WAS
        #    FALSE and it cost Konyo a night: the agent's seal ends with a per-frame blank-detect
        #    pass that DECODES every archived JPEG — measured 0.076 s/frame on this Mac, i.e.
        #    ~7.4 s for a 98-frame reel — and the index was written only after it. The 2.5 s kill
        #    landed mid-pass, so reel_s_1785708285647_38665 ended up with 98 real frames and NO
        #    index.json: the theatre skipped it and played BLACK while he was told "session saved".
        #    DIVISION OF LABOUR: SEAL-1 makes the index survive the kill regardless, so this grace
        #    is NOT the load-bearing fix — it only buys the OPTIONAL blank-flag enrichment time to
        #    finish. So the fast 2.5 s stays byte-for-byte for any stop with no reel on disk, and
        #    the deadline extends ONLY while a seal is visibly progressing (reel dir present, index
        #    still unwritten or still changing), hard-capped at 8 s so End Session never feels hung.
        wait_s = 2.5
        cap_s = 8.0
        _t0 = time.time()
        deadline = _t0 + wait_s
        _hard = _t0 + cap_s
        _seal_sid = _seal_sid_hint()
        _seal_reel = os.path.join(HIST_DIR, "reel_" + _seal_sid) if _seal_sid else ""
        _seal_sig = None
        _grace = 0.0
        _dead = False
        while True:
            if _port_listener_pid() is None and not any(_pid_alive(p) for p in (pids or [])):
                _dead = True
                break
            _now = time.time()
            if _now >= deadline:
                _sig = _seal_progress(_seal_reel)
                # extend ONLY on evidence: a reel dir that exists and is still being sealed
                # (index not on disk yet, or the seal's artefacts still changing)
                if _sig is not None and _now < _hard and (_sig != _seal_sig or not _sig[0]):
                    _seal_sig = _sig
                    deadline = min(_now + 1.0, _hard)
                    _grace = deadline - (_t0 + wait_s)
                    continue
                break
            time.sleep(0.15)
        if _grace > 0:
            print("\u23f3 End Session: seal in flight for reel_%s — waited +%.1fs for it (index %s)"
                  % (_seal_sid, _grace,
                     "on disk" if _seal_index_ok(_seal_reel) else "STILL MISSING"), flush=True)
        if not _dead:
            if _seal_reel and not _seal_index_ok(_seal_reel) and _reel_jpg_count(_seal_reel) > 0:
                print("\U0001f6a8 End Session: force-killing the agent after %.1fs with reel_%s "
                      "holding %d frames and NO index.json — the theatre would play this reel "
                      "BLACK. Rebuilding the index from the frame filenames..."
                      % (time.time() - _t0, _seal_sid, _reel_jpg_count(_seal_reel)), flush=True)
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
        # BELT AND BRACES — the agent is gone now. A reel holding frames but no index is
        # invisible to every theatre reader in this file, so rebuild it from the frame filenames
        # and SAY SO. Repair lives in chronicle_retro; a failure here can never break End Session.
        try:
            if _seal_reel and _reel_jpg_count(_seal_reel) > 0:
                _ok, _rebuilt = _reel_ensure_index(_seal_reel)
                if _rebuilt:
                    print("\U0001fa79 rebuilt missing index for 1 reel: reel_%s (%d frames) — the "
                          "seal was cut short by End Session; footage recovered, blank flags fill "
                          "in lazily" % (_seal_sid, _reel_jpg_count(_seal_reel)), flush=True)
                elif not _ok:
                    print("\u26a0 reel_%s holds %d frames and still has no readable index — the "
                          "theatre will skip it. Restarting the console retries the repair."
                          % (_seal_sid, _reel_jpg_count(_seal_reel)), flush=True)
        except Exception as _re:
            print("\u26a0 post-stop index repair skipped: %s" % _re, flush=True)
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
                # v1472 — context manager: a bare open().read() leaks the handle until GC, and on
                # Windows an open handle blocks deleting/replacing the very pid file we manage.
                with open(BOARD_PID_PATH) as _bf:
                    old = int(_bf.read().strip() or 0)
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
        # v1472 — was a bare open().read(). _window_present() runs on EVERY launch and every
        # takeover check, so the leaked handle recurred constantly; on Windows that is also what
        # keeps .tvd_window.pid locked against the cleanup that is supposed to remove it.
        with open(WINDOW_PID_PATH) as _wf:
            pid = int(_wf.read().strip() or 0)
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
    Returns True when a reclaim was attempted (caller should re-bind).

    v1379.1 — ALSO kill whoever is LISTENING on CONTROL_PORT (not only
    `control_app.py --no-open`). Log evidence: reclaim reported killed=0 while bind
    still got Address already in use → fell through to window-only on a STALE primary
    (Desktop double-click never showed the new ship stamp)."""
    pause = os.path.join(HERE, ".tvd_supervisor_pause")
    try:
        with open(pause, "a", encoding="utf-8") as f:
            f.write("scan-reclaim %s\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
    except Exception:
        pass
    me = os.getpid()
    victims = set()
    # 1) known headless launcher argv
    try:
        out = subprocess.run(
            ["pgrep", "-f", "control_app.py"],
            capture_output=True, text=True, timeout=3)
        for line in (out.stdout or "").splitlines():
            try:
                pid = int(line.strip())
            except Exception:
                continue
            if pid == me or pid <= 1:
                continue
            victims.add(pid)
    except Exception:
        pass
    # 2) whoever actually holds the port (covers half-dead / non --no-open leftovers)
    try:
        holder = _port_listener_pid(CONTROL_PORT)
        if holder and holder != me and holder > 1:
            victims.add(int(holder))
    except Exception:
        pass
    killed = 0
    for pid in sorted(victims):
        try:
            os.kill(pid, signal.SIGTERM)
            killed += 1
        except Exception:
            pass
    if killed:
        time.sleep(0.7)
        for pid in sorted(victims):
            try:
                os.kill(pid, 0)  # still alive?
            except Exception:
                continue
            try:
                os.kill(pid, signal.SIGKILL)
            except Exception:
                pass
        time.sleep(0.35)
    # 3) last chance — lsof the port again and SIGKILL
    try:
        holder2 = _port_listener_pid(CONTROL_PORT)
        if holder2 and holder2 != me and holder2 > 1:
            try:
                os.kill(int(holder2), signal.SIGKILL)
                killed += 1
                time.sleep(0.25)
            except Exception:
                pass
    except Exception:
        pass
    print(f"📺 reclaimed :{CONTROL_PORT} for live scan "
          f"(paused supervisor · killed {killed} control process(es)) — "
          f"this process is now PRIMARY with Screen Recording chain", flush=True)
    return True


def _win_find_console_hwnd():
    """v1464 — HWND of OUR console window by exact title, or 0.

    Exact title only (never a prefix): the popout board is "TV DIABLO — Board" and lives in a
    separate process, and a prefix match let it masquerade as the console once already (REG-055).
    """
    if not IS_WIN:
        return 0
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        found = []

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def _cb(hwnd, _lp):
            buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, buf, 256)
            if (buf.value or "") == "TV DIABLO":
                found.append(hwnd)
                return False
            return True

        user32.EnumWindows(_cb, 0)
        return int(found[0]) if found else 0
    except Exception:
        return 0


def _win_nudge_onscreen():
    """v1464 — slide the window fully into the work area. MOVE ONLY, never resize.

    With the shipped height corrected to 660 logical the window is now the right SIZE, but
    pywebview's CenterScreen still placed it at top y=190 physical, so 190+990 = 1180 spilled
    past the 1008 work area and ~172px sat under the taskbar.

    SWP_NOSIZE is the whole safety argument: this call is structurally incapable of changing
    the window's dimensions, so it cannot repeat the earlier collapse-to-158x26. Both rects
    come from the same (now DPI-aware) process at `shown`, so they are directly comparable
    with no scaling maths. If anything is off, we return without touching the window.
    """
    if not IS_WIN:
        return
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32

        class _R(ctypes.Structure):
            _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                        ("right", wintypes.LONG), ("bottom", wintypes.LONG)]

        hwnd = 0
        win = globals().get("_MAIN_WIN")
        try:
            hwnd = int(win.native.Handle.ToInt32())
        except Exception:
            hwnd = _win_find_console_hwnd()
        if not hwnd:
            return
        wa, wr = _R(), _R()
        if not user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(wa), 0):
            return
        if not user32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(wr)):
            return
        w, h = wr.right - wr.left, wr.bottom - wr.top
        if w <= 0 or h <= 0:
            return
        x = min(wr.left, wa.right - w)
        y = min(wr.top, wa.bottom - h)
        x, y = max(x, wa.left), max(y, wa.top)
        if (x, y) == (wr.left, wr.top):
            return                                    # already on screen — touch nothing
        SWP_NOSIZE, SWP_NOZORDER, SWP_NOACTIVATE = 0x0001, 0x0004, 0x0010
        user32.SetWindowPos(wintypes.HWND(hwnd), None, int(x), int(y), 0, 0,
                            SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)
        print(f"📐 window nudged on-screen: ({wr.left},{wr.top}) → ({x},{y}) "
              f"[size {w}x{h} untouched]", flush=True)
    except Exception:
        pass


def _win_tint_caption():
    """v1464 — make the native title bar belong to the console instead of fighting it.

    Konyo's caption renders in the Windows ACCENT colour (measured: AccentColor 0xFFA91AD9 =
    rgb(217,26,169), bright magenta) directly above a #070605 console. pywebview already calls
    DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE), but it keys that off the SYSTEM
    theme — AppsUseLightTheme=1 here, so it asks for a LIGHT caption. And with ColorPrevalence=1
    the accent colour beats immersive dark mode anyway; only DWMWA_CAPTION_COLOR overrides it.

    Runs on the `shown` event: the Form (and therefore the HWND) does not exist until the GUI
    thread builds it inside webview.start(), and this must never sit on the window-creation
    path. On builds < 22000 DWM returns E_INVALIDARG as a RETURN VALUE, not an exception, and
    leaves the window untouched. Wrapped anyway: cosmetics must never cost the window — this
    app has already lost its window to a cosmetic change twice (REG-051, REG-053).
    """
    if not IS_WIN:
        return
    try:
        if sys.getwindowsversion().build < 22000:
            return                                  # Win10: immersive dark mode only, no tint
        hwnd = 0
        win = globals().get("_MAIN_WIN")
        try:
            hwnd = int(win.native.Handle.ToInt32())
        except Exception:
            hwnd = _win_find_console_hwnd()         # fall back to the proven exact-title scan
        if not hwnd:
            return
        import ctypes
        from ctypes import wintypes
        dwm = ctypes.windll.dwmapi

        def _set(attr, value):
            v = ctypes.c_int(value)
            dwm.DwmSetWindowAttribute(wintypes.HWND(hwnd), wintypes.DWORD(attr),
                                      ctypes.byref(v), ctypes.sizeof(v))

        # COLORREF is 0x00BBGGRR (NOT html RGB order).
        _set(20, 1)             # DWMWA_USE_IMMERSIVE_DARK_MODE
        _set(35, 0x00050607)    # DWMWA_CAPTION_COLOR  <- #070605, the console's own black
        _set(36, 0x0060C0F0)    # DWMWA_TEXT_COLOR     <- #f0c060, the console gold
        _set(34, 0x000E1418)    # DWMWA_BORDER_COLOR
    except Exception:
        pass


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

    # v1462 — Windows takes .ico ONLY. Measured on Konyo's box: handing pywebview 6 a .png
    # via start(icon=) makes the WebView2 host window never show — silently, no exception,
    # no log line. That is the v1460 dead-icon failure all over again, and a missing icon is
    # infinitely cheaper than a missing window, so the .png candidates are Mac/Linux-only here.
    _icon_cands = [os.path.join(HERE, "appicon.ico")] if IS_WIN else [
        os.path.join(HERE, "tv_diablo_icon.png"),
        os.path.join(REPO, "art", "diablo_icon.png"),
    ]
    icon = None
    for cand in _icon_cands:
        if os.path.isfile(cand):
            icon = cand
            break

    # ══ v1464 — SHIPPED GEOMETRY MUST FIT A LAPTOP. The old default was 1120x800 LOGICAL px.
    # Konyo's machine is 1920x1080 at 150% DPI, i.e. a 1280x720 logical desktop with ~672
    # logical px of work area — so an 800px-tall window, centred, had its Top clamped to 0 and
    # ~130 logical px of the console sat under the taskbar, unreachable. It was the WINDOW that
    # was off-screen, not the content, so nothing could scroll to it (measured: window bottom
    # y=777 vs work-area bottom y=672).
    #
    # A runtime clamp was tried and REMOVED. SPI_GETWORKAREA reports LOGICAL px while the
    # process is DPI-unaware and PHYSICAL px once it is aware, and which one we are depends on
    # import order — the identical clamp computed a correct 632 under a python.exe foreground
    # run and silently became a no-op under the launcher's pythonw.exe spawn (window came up
    # 737 logical, 174px off-screen). Probing awareness to normalise it was no more reliable.
    # A post-shown SetWindowPos fit was tried too and left the window collapsed to 158x26.
    # So: a deterministic default that fits every common laptop (1366x768 and 1920x1080@150%
    # both give ~672 logical), and the window stays freely resizable for bigger screens. No
    # API guessing on the window-creation path — REG-051 and REG-053 were both cosmetics that
    # cost the window, and this is the same blast radius.
    kwargs = dict(
        title="TV DIABLO",
        url=url,
        width=1120,
        height=660,   # v1464 — fits a 672-logical work area; see the note above
        min_size=(880, 600),
        background_color="#070605",
        text_select=False,
        confirm_close=False,
        easy_drag=False,
    )

    # v1462 — pywebview 6 MOVED icon= off create_window() and onto start(icon=).
    # The old code passed icon= to create_window and caught TypeError into a hardcoded
    # reduced call — so on pywebview >= 6 (6.2.1 is what ships on Konyo's box) every window
    # silently lost its icon AND text_select/confirm_close/easy_drag, which v6 still supports
    # perfectly well. Ask the installed signature instead of guessing: keep every option the
    # local version accepts, and route icon to whichever call owns it.
    _cw_ok, _start_ok = set(), set()
    try:
        import inspect
        _cw_ok = set(inspect.signature(webview.create_window).parameters)
        _start_ok = set(inspect.signature(webview.start).parameters)
    except Exception:
        pass
    icon_for_start = None
    if icon:
        if not _cw_ok or "icon" in _cw_ok:
            kwargs["icon"] = icon            # pywebview <= 5 (or introspection unavailable)
        else:
            icon_for_start = icon            # pywebview >= 6
    if icon_for_start and IS_WIN and not icon_for_start.lower().endswith(".ico"):
        icon_for_start = None            # see the .ico-only note above — never risk the window
    globals()["_ICON_FOR_START"] = icon_for_start if (not _start_ok or "icon" in _start_ok) else None
    if _cw_ok:
        dropped = [k for k in kwargs if k not in _cw_ok]
        if dropped:
            print(f"⚠ pywebview build ignores {', '.join(sorted(dropped))} — continuing without",
                  flush=True)
            kwargs = {k: v for k, v in kwargs.items() if k in _cw_ok}
    try:
        globals()["_MAIN_WIN"] = webview.create_window(**kwargs)
    except TypeError as e:
        # Last resort: the irreducible core every version has taken since v1.
        print(f"⚠ create_window rejected options ({e}) — falling back to the core set", flush=True)
        globals()["_MAIN_WIN"] = webview.create_window(
            title="TV DIABLO",
            url=url,
            width=1120,
            height=800,
            min_size=(880, 600),
            background_color="#070605",
        )

    # v935.8 / v1410 / v1420 — window ✕ UX:
    #   v1410: mark gone FIRST + async stop (no UI-thread stop_agent → hang reports)
    #   v1420: ALSO arm hard os._exit deadline — Cocoa often never returns webview.start()
    #          after red ✕, so main never reaches the post-start os._exit and users Force Quit.
    try:
        win = globals().get("_MAIN_WIN")
        if win is not None and hasattr(win, "events"):
            def _on_win_closing():
                _request_console_exit("window-closing")
                return True  # allow close (pywebview may honor this on some backends)
            def _on_win_closed():
                _request_console_exit("window-closed")
            try:
                win.events.closing += _on_win_closing
            except Exception:
                pass
            try:
                win.events.closed += _on_win_closed
            except Exception:
                pass
            try:
                # v1464 — caption tint ONLY. A post-shown SetWindowPos "fit" was tried here and
                # REMOVED: measured, it never actually resized (1680x948 -> 1680x948, it only
                # nudged the position), yet a run with it wired left the window collapsed to
                # 158x26. The pre-create clamp in open_control_window() already guarantees the
                # geometry fits the work area, verified at 1680x948 fully on screen. Cosmetics
                # do not get to touch window geometry after it is up — REG-051, REG-053.
                win.events.shown += _win_nudge_onscreen   # v1470 — MOVE only, never resize
                win.events.shown += _win_tint_caption
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
            # v1745 — the Chronicle auto-read watchdog. Reads only visits whose LEDGER is known,
            # only when no session is live and no sweep is running, and never applies. See
            # chronicle_autoread_tick.
            threading.Thread(target=_chron_autoread_loop, daemon=True, name="tvd-chron-autoread").start()
        except Exception as _ee:
            print(f"⚠ engine driver failed to start ({_ee}) — tallies need a board tab open", flush=True)

    # v928 — private_mode=False FOR REAL: the comment below claimed it since forever, but
    # the call never passed it. pywebview defaults to private (ephemeral) storage, so every
    # tally/grail state in the app board silently evaporated on quit.
    # v1248 — hold the window-presence lock for this window's lifetime (takeover guard);
    # cleared on close/crash so a second launch knows whether a real window is already open.
    _window_lock_write()
    globals()["_WINDOW_LIVE"] = True
    try:
        import atexit as _atexit
        _atexit.register(_window_lock_clear)
    except Exception:
        pass
    # v1462 — on pywebview >= 6 the window icon is a start() argument (see create_window above).
    _start_kw = dict(debug=False, private_mode=False)
    if globals().get("_ICON_FOR_START"):
        _start_kw["icon"] = globals()["_ICON_FOR_START"]
    try:
        try:
            try:
                webview.start(**_start_kw)
            except Exception:
                # v1463 — the icon must NEVER cost the window. pywebview 6 builds it as
                # `self.Icon = Icon(path)` inside the WinForms Form ctor with no try/except,
                # guarded on our side only by os.path.isfile() — which happily passes for a
                # truncated or half-pulled appicon.ico. A corrupt icon would then throw on the
                # GUI thread and reproduce the v1460 dead-window symptom with a new trigger.
                # Retry once without it; a missing icon is a cosmetic loss, no window is not.
                if "icon" not in _start_kw:
                    raise
                print("⚠ window icon rejected — reopening without it (window > cosmetics)", flush=True)
                _start_kw.pop("icon", None)
                webview.start(**_start_kw)
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
        # v1420 — if Cocoa returned cleanly, still unify on the force-exit path (idempotent).
        # If Cocoa hung, the close-handler already armed the deadline and we never get here.
        try:
            _request_console_exit("webview-finally")
        except Exception:
            try:
                _mark_window_gone("webview-finally")
                _schedule_exit_stop("webview-returned")
            except Exception:
                pass


def _ejs(w, code, timeout=4.0):
    """v930 — evaluate_js with a hard timeout: pywebview's call BLOCKS FOREVER on a
    suspended/occluded WKWebView (live evidence: driver thread hung on its first probe).
    Runs the call in a scratch thread; timeout → None (treat as engine-not-responding).

    v1410 — refuse when the window is gone/closing. evaluate_js on a dying WKWebView
    deadlocks Cocoa and surfaces as Apple Python_*.hang on ✕."""
    if w is None or not globals().get("_WINDOW_LIVE"):
        return None
    import queue as _q
    box = _q.Queue(maxsize=1)
    def _run():
        try:
            # re-check inside the worker — close can race mid-call
            if not globals().get("_WINDOW_LIVE"):
                box.put(None)
                return
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


def _kai_base_sig():
    """v-E1 — distinctive BASE-TYPE tokens (len>=6), length-bucketed, from bible's lf-base-codes
    lexicon (Battle Boots, Archon Plate, …). The SECOND WITNESS for the ground-label grounding
    path. Parsed independently of _kai_fullnames (base names live in the lf-base-codes JSON, whose
    "Name":"code" string values the fullnames name:/n: patterns deliberately skip). Cached."""
    c = globals().get("_KAI_BASE_SIG")
    if c is not None:
        return c
    by_len = {}
    try:
        with open(os.path.join(REPO, "bible.html"), encoding="utf-8", errors="replace") as f:
            m = re.search(r'id="lf-base-codes">(\{.*?\})</script>', f.read(), re.S)
        if m:
            for k in re.findall(r'"([^"]+)"\s*:', m.group(1)):
                for t in re.split(r"[^a-z]+", k.lower()):
                    if len(t) >= 6:
                        by_len.setdefault(len(t), set()).add(t)
    except Exception:
        pass
    globals()["_KAI_BASE_SIG"] = by_len
    return by_len


def _kai_groundlabel_ctx(lines):
    """v-E1 — TWO-WITNESS ground-label context. A grail dropped on the FLOOR shows its gold NAME
    over its BASE type with NO tooltip stat lines, so _kai_tooltip_context can't fire and the name
    was being dropped (real miss: War Traveler read as 'WAA TRAVELIR' / 'BATYLE B**Ys', missed in
    7 frames across 6 real reels). Recognized ONLY when EVERY line is terse (<=3 tokens — ground
    labels are name/base, never prose) AND a distinctive BASE-TYPE token is present (the second
    witness). A distinctive item NAME paired with a real BASE type, tersely, is what chat / loot-
    filter / gameplay garble never produces — verified against 29 reels: grounds all 7 War Traveler
    floor-drops, 0 false grounds (the chat 'Diablo's' -> Ars Al'Diabolos stays blocked: no base
    witness). Pure."""
    base_by_len = _kai_base_sig()
    if not base_by_len:
        return False
    has_base = False
    for ln in (lines or []):
        toks = re.findall(r"[a-z0-9']+", str(ln or "").lower())
        if len(toks) > 3:
            return False   # a prose line — not a ground label
        for raw in toks:
            d = _kai_deleet(raw)
            if len(d) < 6:
                continue
            for L in (len(d) - 1, len(d), len(d) + 1):
                if any(_kai_lev(d, bt, 1) <= 1 for bt in base_by_len.get(L, ())):
                    has_base = True
                    break
    return has_base


def _kai_ground_lines(lines):
    """v-FIXC — recover REAL grail item names from garbled OCR. Fires on TWO honest contexts:
    (1) item-TOOLTIP context (_kai_tooltip_context — stat/marker lines present), or (2) v-E1
    GROUND-LABEL context (_kai_groundlabel_ctx — a terse floor-drop name+base, second-witnessed
    by a distinctive base type). For each non-stat line, de-leet its tokens and match any
    distinctive (len>=6) token against the signature lexicon: edit-1 at len<=9, edit-2 at len>=10.
    Returns {canonicalDisplayName: matchedSignatureToken}. Empty when nothing grounds (honest —
    never invents a name from stat/gameplay/chat text). Pure."""
    try:
        idx = _kai_ground_index()
    except Exception:
        return {}
    sig_by_len = idx["sig_by_len"]
    disp = idx["disp"]
    if not sig_by_len:
        return {}
    if not _kai_tooltip_context(lines) and not _kai_groundlabel_ctx(lines):
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


# ── 🔬 READS FORENSICS (pure read-only PROJECTION) ─────────────────────────────
# Konyo's forensic X-ray, exposed: what the AI read cleanly, what garble it CORRECTED, what it
# recovered via corroboration, what near-misses it correctly REFUSED, what stayed unresolved —
# per item, with the RAW OCR verbatim + a plain-language Diablo-terms synthesis. DETERMINISTIC:
# re-runs the SAME pure grounder/near-miss helpers the closer used, over the already-stored raw
# (report.missed[].texts + register + routing) — no live writes, no drift, works retroactively on
# every existing reel. Honest-absent where a reel stored no raw.

# v1381.1 — common OCR phrase fixes (screen text, not grail uniques). Applied before
# grounder so "GRAMD CHAR" → Grand Charm lands as corrected forensics, not unresolved noise.
_KAI_OCR_PHRASE_FIXES = (
    (re.compile(r"\bgramd\s*char(?:m)?\b", re.I), "Grand Charm"),
    (re.compile(r"\bgr[ao0]nd\s*charr?m?\b", re.I), "Grand Charm"),
    (re.compile(r"\bsm[ao0]ll\s*char(?:m)?\b", re.I), "Small Charm"),
    (re.compile(r"\blarge\s*char(?:m)?\b", re.I), "Large Charm"),
)


def _kai_ocr_phrase_fix(texts):
    """v1381.1 — pure. First matching OCR phrase fix → (canonical, raw_line) or None."""
    for t in (texts or []):
        s = str(t or "")
        if not s.strip():
            continue
        for rx, canon in _KAI_OCR_PHRASE_FIXES:
            if rx.search(s):
                return (canon, s.strip())
    return None


def _kai_forensic_correction(texts):
    """A garbled line that grounds to a REAL grail name → (name, raw_token, edit, via). via =
    'name+base' (E1 ground-label two-witness) or 'de-leet' (tooltip). None if nothing grounds.
    v1381.1 — also returns OCR phrase fixes (Grand Charm etc.) via='ocr-phrase'."""
    phrase = _kai_ocr_phrase_fix(texts)
    if phrase:
        return (phrase[0], phrase[1], 0, "ocr-phrase")
    g = _kai_ground_lines(texts)
    if not g:
        return None
    name, sig = next(iter(g.items()))
    via = "name+base" if (not _kai_tooltip_context(texts) and _kai_groundlabel_ctx(texts)) else "de-leet"
    raw_tok, ed = None, None
    for t in (texts or []):
        for raw in re.split(r"[^a-z0-9']+", str(t).lower()):
            d = _kai_deleet(raw)
            if len(d) >= 6:
                tol = 1 if len(d) <= 9 else 2
                e = _kai_lev(d, sig, tol)
                if e <= tol:
                    raw_tok, ed = raw, e
                    break
        if raw_tok:
            break
    return (name, raw_tok, ed, via)


def _kai_forensic_block(texts):
    """A token that edit-matched a grail signature but the grounder REFUSED (the discipline) →
    {raw, nearest, edit, blockedBy}. The exact inverse of _kai_ground_lines' gate, re-derived
    deterministically. None if nothing near-matched (genuine noise / unresolved)."""
    if _kai_ground_lines(texts):
        return None
    try:
        idx = _kai_ground_index()
    except Exception:
        return None
    sig_by_len, disp = idx["sig_by_len"], idx["disp"]
    terse = all(len(re.findall(r"[a-z0-9']+", str(t).lower())) <= 3 for t in (texts or []))
    for t in (texts or []):
        low = str(t).lower()
        if any(sw and sw in low for sw in _KAI_STAT_WORDS):
            continue
        for raw in re.split(r"[^a-z0-9']+", low):
            d = _kai_deleet(raw)
            if len(d) < 6:
                continue
            tol = 1 if len(d) <= 9 else 2
            for L in range(len(d) - tol, len(d) + tol + 1):
                for st in sig_by_len.get(L, ()):
                    e = _kai_lev(d, st, tol)
                    if e <= tol:
                        by = "no-base-witness" if terse else "no-tooltip-context"
                        return {"raw": raw, "nearest": disp.get(st), "edit": e, "blockedBy": by}
    return None


def _kai_base_names():
    """B9 — the full set of base-type names (lowercased) from bible's lf-base-codes, for the grail
    EXCLUSION (a base like 'Battle Boots' is a name in the flat lexicon but is never a grail).
    Cached; parsed like _kai_base_sig but keeps whole names, not just distinctive tokens."""
    c = globals().get("_KAI_BASE_NAMES")
    if c is not None:
        return c
    names = set()
    try:
        with open(os.path.join(REPO, "bible.html"), encoding="utf-8", errors="replace") as f:
            m = re.search(r'id="lf-base-codes">(\{.*?\})</script>', f.read(), re.S)
        if m:
            for k in re.findall(r'"([^"]+)"\s*:', m.group(1)):
                names.add(k.lower())
    except Exception:
        pass
    globals()["_KAI_BASE_NAMES"] = names
    return names


def _kai_item_class(name, tier=None, grounded=False):
    """B9 — the item rarity CLASS the engine can PROVE, honestly:
      'runeword' — derivable (_kai_runeword_bare).
      'grail'    — grounder-proven (grounded=True) OR register tier=='grail', with BASES EXCLUDED
                   (a base name never becomes 'the grail Battle Boots').
      None       — plain / unknown.
    NEVER fakes unique-vs-set (not derivable engine-side — that's the client's tipOf, per the
    receipt contract). Pure."""
    nm = str(name or "").strip()
    if not nm:
        return None
    if _kai_runeword_bare(nm):
        return "runeword"
    if nm.lower() in _kai_base_names():
        return None   # the Battle Boots guard — a base type is never a grail
    if grounded or str(tier or "").lower() == "grail":
        return "grail"
    return None


def _kai_item_phrase(name, cls):
    """'War Traveler' + 'grail' → 'the grail War Traveler'; None class → the bare name."""
    return ("the " + cls + " " + name) if cls else name


_UNRESOLVED_NONITEM_MARKERS = ("entering", "loading", "waypoint", "create game", "you have",
                               "has joined", "has left", "press", "gold")
_UNRESOLVED_UI_FUZZY = ("socketed", "transmute", "potion", "maximum", "greater", "identify")


def _kai_unresolved_kind(texts):
    """② forensics honesty — classify an UNRESOLVED read (item=None, garble we couldn't resolve):
      'non-item'        — CONFIDENTLY screen text, never loot: a transition banner (ENTERING/
                          loading), a short UI indicator (LIVE/IDLE — no substantial word), pure
                          noise (every long word is _kai_line_is_noise), or a fuzzy hit on a
                          recurring UI/cube/consumable prompt (socketed-items / potion / …).
      'unreadable-item' — garbled text too mangled to classify; honestly left as "couldn't read"
                          (NOT claimed as a grail miss — grailMisses stays a PROVEN 0).
    Deterministic + conservative (ambiguous → unreadable-item, never over-claims non-item). Pure."""
    tx = texts or []
    blob = " ".join(str(t) for t in tx).strip().lower()
    if not blob:
        return "non-item"
    dl = _kai_deleet(blob)
    if any((m in blob) or (_kai_deleet(m) in dl) for m in _UNRESOLVED_NONITEM_MARKERS):
        return "non-item"
    # fuzzy hit on a recurring UI/cube/consumable prompt (the raw is heavily leet-garbled)
    for t in tx:
        for w in re.split(r"[^a-z0-9']+", str(t).lower()):
            d = _kai_deleet(w)
            if len(d) >= 5 and any(abs(len(d) - len(tg)) <= 2 and _kai_lev(d, tg, 2) <= 2
                                   for tg in _UNRESOLVED_UI_FUZZY):
                return "non-item"
    long_words = [w for t in tx for w in re.split(r"[^a-z]+", str(t).lower()) if len(w) >= 5]
    if not long_words:
        return "non-item"                                   # short UI indicators / pure noise
    if all(_kai_line_is_noise(w) for w in long_words):
        return "non-item"
    return "unreadable-item"


_FORENSIC_RIGHT = ("grounded", "resolved-corrected", "recovered-2witness", "recovered-crossframe")


def _kai_forensics_project(report, journal_rows=None, cap=300):
    """🔬 Pure projection → {sid, items:[grouped by item+status], summary}. Reconstructs the
    forensic record from stored raw only. Statuses: grounded (clean DB read) · resolved-corrected
    (garble fixed to the right name) · recovered-2witness (name+base) · recovered-crossframe
    (gate cross-frame proof) · blocked-fp (near-match correctly refused) · unresolved. The first
    four = 'the AI got it right' (corrected:true where a garble was fixed). Diablo-language
    synthesis per record. Deterministic + honest-absent."""
    report = report or {}
    sid = report.get("sid") or ""
    reg = {}
    for r in (report.get("register") or []):
        nm = r.get("name")
        if nm:
            reg[nm.lower()] = {"name": nm, "loc": r.get("loc"), "tier": r.get("tier"),
                               "frameId": r.get("frameId"), "ts": r.get("firstSeenTs")}
    # a per-frame scene/area hint from the routing ledger (for the Diablo-language synthesis)
    scene_by_f = {}
    crossframe_frames = []
    for rr in (report.get("routing") or []):
        f = str(rr.get("f") or "")
        if f:
            scene_by_f[f] = rr.get("label") or ""
        if rr.get("gateReason") == "cross-frame":
            crossframe_frames.append(rr)

    reads = []

    def _syn(where, body):
        lab = _diablo_scene_label(where or "", "")
        tail = (" · " + lab["label"]) if lab.get("kind") != "unclear" else ""
        return body + tail

    # ① CLEAN reads — the register (DB-verified sightings the AI read right)
    for low, r in reg.items():
        _cls = _kai_item_class(r["name"], tier=r.get("tier"), grounded=False)
        reads.append({
            "item": r["name"], "status": "grounded", "corrected": False, "itemClass": _cls,
            "reason": "read cleanly, matched the item database",
            "synthesis": _syn(scene_by_f.get(str(r.get("frameId") or "")),
                              "read " + _kai_item_phrase(r["name"], _cls) + " cleanly"),
            "engine": "liveEye", "sessionId": sid, "ts": r.get("ts"),
            "frames": [{"frameId": r.get("frameId"), "raw": None, "scene": None}],
            "witnesses": {"content": True}, "resolvedFrom": {"frameId": r.get("frameId"), "witness": "read"}})

    # ② cross-frame gate proofs (② quorum) — recovered-crossframe
    for rr in crossframe_frames:
        reads.append({
            "item": None, "status": "recovered-crossframe", "corrected": True, "itemClass": None,
            "reason": "held at quorum<2, proven by a distinct witness across the item's on-screen lifetime",
            "synthesis": _syn(rr.get("label"),
                              "one still was uncertain — a neighbouring frame's independent read confirmed it"),
            "engine": "router", "sessionId": sid, "ts": rr.get("ts"),
            "frames": [{"frameId": str(rr.get("f") or "").rsplit(".", 1)[0], "raw": None, "scene": rr.get("label")}],
            "witnesses": {"crossFrameNeighbors": rr.get("crossFrame") or []},
            "resolvedFrom": {"frameId": str(rr.get("f") or "").rsplit(".", 1)[0], "witness": "cross-frame"}})

    # ③ garbled frames (missed[].texts hold the raw) — correction / block / association / unresolved
    for m in (report.get("missed") or []):
        texts = m.get("texts") or []
        if not texts:
            continue
        fid = str(m.get("f") or "").rsplit(".", 1)[0]
        where = m.get("cls") or scene_by_f.get(str(m.get("f") or "")) or ""
        base = {"engine": "kai", "sessionId": sid, "ts": m.get("ts"),
                "frames": [{"frameId": fid, "raw": " · ".join(str(t) for t in texts)[:240], "scene": where}]}
        corr = _kai_forensic_correction(texts)
        if corr:
            name, raw, ed, via = corr
            st = "recovered-2witness" if via == "name+base" else "resolved-corrected"
            _cls = _kai_item_class(name, grounded=True)   # grounder-proven → grail/runeword
            _phrase = _kai_item_phrase(name, _cls)
            body = ("saw '" + str(raw) + "' garbled" +
                    (", matched the base → grounded " if via == "name+base" else "', de-garbled to ") + _phrase)
            reads.append(dict(base, item=name, status=st, corrected=True, itemClass=_cls,
                              reason=("name+base two-witness" if via == "name+base" else "leet/edit de-garble"),
                              correction={"raw": raw, "resolved": name, "via": via, "edit": ed},
                              synthesis=_syn(where, body),
                              witnesses=({"name": True, "base": True} if via == "name+base" else {"name": True}),
                              resolvedFrom={"frameId": fid, "witness": via}))
            continue
        blk = _kai_forensic_block(texts)
        if blk:
            reads.append(dict(base, item=None, status="blocked-fp", corrected=False, itemClass=None,
                              reason="near-matched " + str(blk.get("nearest")) + " but no witness — refused",
                              block=blk,
                              synthesis=_syn(where, "'" + str(blk.get("raw")) + "' edit-matched " +
                                             str(blk.get("nearest")) + " but had no " +
                                             ("base" if blk.get("blockedBy") == "no-base-witness" else "tooltip") +
                                             " witness — correctly refused"),
                              witnesses={}, resolvedFrom=None))
            continue
        # associate to a CLEAN same-session read (non-grail corrected — potions/bases)
        assoc = None
        for t in texts:
            for raw in re.split(r"[^a-z0-9']+", str(t).lower()):
                d = _kai_deleet(raw)
                if len(d) < 5:
                    continue
                for low, rr in reg.items():
                    for tk in re.split(r"[^a-z]+", low):
                        if len(tk) >= 5 and _kai_lev(d, tk, 2) <= 1:
                            assoc = (raw, rr["name"])
                            break
                    if assoc:
                        break
                if assoc:
                    break
            if assoc:
                break
        if assoc:
            raw, name = assoc
            _cls = _kai_item_class(name, tier=(reg.get(name.lower()) or {}).get("tier"))
            reads.append(dict(base, item=name, status="resolved-corrected", corrected=True, itemClass=_cls,
                              reason="garbled here, read cleanly elsewhere this session — same item",
                              correction={"raw": raw, "resolved": name, "via": "clean-match-nearby", "edit": None},
                              synthesis=_syn(where, "one frame garbled to '" + str(raw) +
                                             "' — same " + _kai_item_phrase(name, _cls) + " read cleanly nearby, corrected"),
                              witnesses={"content": True}, resolvedFrom={"frameId": fid, "witness": "clean-match-nearby"}))
        else:
            _uk = _kai_unresolved_kind(texts)
            _uwhy = ("screen text (UI / transition / noise), never loot"
                     if _uk == "non-item" else "an item read too garbled to resolve")
            reads.append(dict(base, item=None, status="unresolved", corrected=False, itemClass=None,
                              unresolvedKind=_uk,   # ② backward-compatible: status stays 'unresolved'
                              reason="garbled text, no confident resolution",
                              synthesis=_syn(where, "unreadable garble — " + _uwhy),
                              witnesses={}, resolvedFrom=None))

    # deterministic id per read (sid:frameId:status) — stable across polls, for UI keying
    for r in reads:
        _fr = (r.get("frames") or [{}])[0].get("frameId") or "-"
        r["id"] = "%s:%s:%s" % (sid, _fr, r["status"])
    # group by item (unresolved/blocked bucket under a status key) + status
    groups = {}
    for r in reads:
        key = r.get("item") or ("__" + r["status"] + "__")
        g = groups.setdefault(key, {"item": r.get("item"), "statuses": {}, "count": 0,
                                    "firstTs": None, "lastTs": None, "reads": []})
        g["reads"].append(r)
        g["count"] += 1
        g["statuses"][r["status"]] = g["statuses"].get(r["status"], 0) + 1
        ts = r.get("ts") or 0
        g["firstTs"] = ts if g["firstTs"] is None else min(g["firstTs"], ts)
        g["lastTs"] = ts if g["lastTs"] is None else max(g["lastTs"], ts)
    items = sorted(groups.values(), key=lambda x: (x["lastTs"] or 0), reverse=True)[:cap]

    # ② additive honesty counts: split the unresolved bucket + a PROVEN grailMisses headline.
    # grailMisses = 0 by construction: every grail the AI IDENTIFIED (grounder/clean-match) is
    # captured above — an unresolved read has no resolved item, so no identified grail was dropped.
    summary = {"clean": 0, "corrected": 0, "recovered": 0, "blocked": 0, "unresolved": 0,
               "grailMisses": 0, "screenText": 0, "unreadable": 0}
    for r in reads:
        s = r["status"]
        if s == "grounded":
            summary["clean"] += 1
        elif s == "resolved-corrected":
            summary["corrected"] += 1
        elif s in ("recovered-2witness", "recovered-crossframe"):
            summary["recovered"] += 1
        elif s == "blocked-fp":
            summary["blocked"] += 1
        else:
            summary["unresolved"] += 1
            if r.get("unresolvedKind") == "non-item":
                summary["screenText"] += 1
            else:
                summary["unreadable"] += 1
    return {"sid": sid, "items": items, "summary": summary, "total": len(reads)}


_FORENSICS_SUM_CACHE = {"reel": None, "mtime": None, "val": None}


def _newest_forensics_summary():
    """Lean {clean,corrected,recovered,blocked,unresolved} counts from the newest sealed reel —
    the /api/status badge. mtime-cached (the full projection only re-runs when a reel re-seals)."""
    try:
        hist = HIST_DIR
        reels = sorted((d for d in os.listdir(hist)
                        if d.startswith("reel_") and os.path.isfile(os.path.join(hist, d, "kai_report.json"))),
                       reverse=True)
        if not reels:
            return None
        rp = os.path.join(hist, reels[0], "kai_report.json")
        mt = os.path.getmtime(rp)
        if _FORENSICS_SUM_CACHE["reel"] == reels[0] and _FORENSICS_SUM_CACHE["mtime"] == mt:
            return _FORENSICS_SUM_CACHE["val"]
        with open(rp, encoding="utf-8") as fh:
            report = json.load(fh) or {}
        val = _kai_forensics_project(report)["summary"]
        _FORENSICS_SUM_CACHE.update(reel=reels[0], mtime=mt, val=val)
        return val
    except Exception:
        return None


def _forensics_payload(sid=""):
    """🔬 /api/forensics — the reel's full forensic X-ray. sid → reel_<sid>; empty → newest sealed
    reel. Pure read-only projection; honest {ok:False} when there's no reel for that sid."""
    try:
        hist = HIST_DIR
        if sid:
            rp = os.path.join(hist, "reel_" + sid, "kai_report.json")
            if not os.path.isfile(rp):
                return {"ok": False, "err": "no forensics for that session", "sid": sid,
                        "items": [], "summary": {}}
        else:
            reels = sorted((d for d in os.listdir(hist)
                            if d.startswith("reel_") and os.path.isfile(os.path.join(hist, d, "kai_report.json"))),
                           reverse=True)
            if not reels:
                return {"ok": True, "sid": "", "items": [], "summary": {}, "total": 0}
            rp = os.path.join(hist, reels[0], "kai_report.json")
        with open(rp, encoding="utf-8") as fh:
            report = json.load(fh) or {}
        out = _kai_forensics_project(report)
        out["ok"] = True
        return out
    except Exception as e:
        return {"ok": False, "err": str(e)[:120], "items": [], "summary": {}}


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


def _kai_gap_funnel_score(row, tab):
    """v1381.0 — rank a routing row for tally gap-funnel pick. Pure. Higher = better.

    Forensic (s_178498…95276): conf=3 journal+ocr+tabstrip frames were PERSONAL+tooltip
    (gateReason=wrong-cell) while the REAL gems grid sat at conf 0/1. Old ranker preferred
    max conf → fed gemIntake the wrong cell. Accuracy gate already knew; honor it:
      • hard-penalize wrong-cell
      • prefer gatePass
      • prefer grid/tabstrip/ocr eye that names this exact tally tab
      • conf is a tie-break, not the primary key
    """
    tab = str(tab or "").lower().strip()
    if not tab or not isinstance(row, dict):
        return -10 ** 9
    if str(row.get("gateReason") or "") == "wrong-cell":
        return -10 ** 6
    score = 0
    if row.get("gatePass") is True:
        score += 1000
    want = "stash-" + tab
    if str(row.get("gridLabel") or "") == want:
        score += 500
    if str(row.get("tabstripLabel") or "") == want:
        score += 400
    if str(row.get("ocrLabel") or "") == want:
        score += 300
    lab = str(row.get("label") or "")
    if lab == want:
        score += 100
    conf = int(row.get("confidence") or 0)
    if conf < 1 and lab == want:
        conf = 1
    score += conf * 10
    return score


def _kai_stage3_gap_funnel_candidates(routing, sess_rows):
    """v1381.0 — all ranked candidates per unreceipted tally tab (best first). Pure.

    Returns {tab: [job, …]} where job = {tab,f,ts,route,conf,gap,score,gatePass,gateReason}.
    Wrong-cell rows are kept only as last-resort fallback when no viable frame exists.
    """
    receipted = set()
    for r in sess_rows or []:
        ik = r.get("intake")
        if isinstance(ik, dict) and _intake_is_real(ik):
            t = str(ik.get("tab") or "").lower()
            if t in ("runes", "gems", "materials"):
                receipted.add(t)
    by_tab = {}  # tab -> list of (score, ts, row, conf)
    for r in routing or []:
        lab = str(r.get("label") or "")
        if not lab.startswith("stash-"):
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
        has_eye = False
        for key in ("gridLabel", "tabstripLabel", "ocrLabel"):
            if str(r.get(key) or "") == "stash-" + tab:
                has_eye = True
        if conf < 1 and not has_eye and lab != "stash-" + tab:
            continue
        if conf < 1 and lab == "stash-" + tab:
            conf = 1
        sc = _kai_gap_funnel_score(r, tab)
        ts = int(r.get("ts") or 0)
        by_tab.setdefault(tab, []).append((sc, ts, r, conf))
    out = {}
    for tab, rows in by_tab.items():
        viable = [x for x in rows if x[0] > -10 ** 5]
        pool = viable if viable else rows  # last-resort: only wrong-cell left
        pool.sort(key=lambda x: (-x[0], -x[1]))
        jobs = []
        seen_f = set()
        for sc, ts, r, conf in pool:
            f = r.get("f")
            if not f or f in seen_f:
                continue
            seen_f.add(f)
            jobs.append({
                "tab": tab, "f": f, "ts": ts, "route": "tally:" + tab,
                "conf": conf, "gap": True, "score": sc,
                "gatePass": r.get("gatePass"), "gateReason": r.get("gateReason"),
            })
        if jobs:
            out[tab] = jobs
    return out


def _kai_stage3_gap_funnels(routing, sess_rows):
    """v948.7/v1381.0 — funnel jobs for tally tabs eyes labeled on the reel but Stage-3
    quorum never selected (or conf was 1). Photo on film = must recheck + SET intake.
    One best frame per unreceipted tab, plus `alts` (next-best stills) for multi-retry."""
    cands = _kai_stage3_gap_funnel_candidates(routing, sess_rows)
    out = []
    for tab, jobs in cands.items():
        head = dict(jobs[0])
        head["alts"] = [j["f"] for j in jobs[1:5] if j.get("f") and j.get("f") != head.get("f")]
        out.append(head)
    return out


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
        # v1564 — A GAMEPLAY FRAME IS NOT A REFUSED READ.
        # _gate_check returns {"pass": False, "reason": "no-label"} for `not label or label ==
        # "gameplay"` — a frame with no panel on it at all. The badge's own comment calls held
        # "uncertain, refused", and the gate refused nothing: there was nothing to judge. Counting
        # those as held inflates the denominator with every frame of him walking through a level,
        # so the scorecard reports the reader as less accurate the MORE he plays.
        # This is the same honest-absent line the chronicle sweep draws between "nothing to judge"
        # and "everything works" — "I could not look" must never be spent as "I looked and failed".
        # NOTE: unmeasured on his own footage. No readtrail.jsonl exists in any sealed reel yet, so
        # this is fixed on the logic, not on a ratio I watched change. The classification is wrong
        # regardless of how many frames currently land in each bucket.
        prov = sum(1 for r in rt if r.get("gatePass") is True)
        held = sum(1 for r in rt if r.get("gatePass") is False
                   and str(r.get("gateReason") or "") != "no-label")
        skipped = sum(1 for r in rt if r.get("gatePass") is False
                      and str(r.get("gateReason") or "") == "no-label")
        val = {"proven": prov, "held": held, "skipped": skipped} if (prov or held or skipped) else None
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


def _kai_crossframe_quorum(rows, window_idx=3, window_ms=6000):
    """② CROSS-FRAME QUORUM (multi-witness sweep, evidence-backed: 9 genuine tooltip recoveries
    across 29 real reels, 0 new false — the honest number after the correctness guards below, down
    from a 49 raw class-union ceiling: 35 were route-nulled dedup frames the cluster head already
    covers, and stash/inventory are out of scope). The accuracy gate judges each frame in ISOLATION, but a
    tooltip/stash panel LINGERS across several frames and different independent brains catch it on
    different stills. A frame the gate HELD purely at 'quorum<2' is PROVEN when a same-label
    neighbor WITHIN THE ITEM'S ON-SCREEN LIFETIME (±window_idx frames AND ≤window_ms apart)
    contributes a DISTINCT independent evidence class, so the union clears the ≥2-independent-class
    bar. A conservative EXTENSION of _router_conf's per-frame quorum — the SAME discipline, measured
    across the item's screen-lifetime, NOT a loosening:
      · only rows held specifically at 'quorum<2' (check-1 hard-signal already passed);
      · only DISTINCT independent classes count — a same-class neighbor re-firing NEVER clears it
        (the 192 same-class-only holds in the reels stay held);
      · never crosses labels (a different item's frame can't corroborate);
      · re-runs the FULL gate (cell-correctness included) with the frame's own chrome votes, so a
        dissenting chrome witness still vetoes — promotion can only ADD proof the discipline allows.
    Mutates rows in place: sets gatePass=True, gateReason='cross-frame', folds the borrowed classes
    into gateSources, and records `crossFrame` (the borrowed classes) for the drill-down. Never
    fires a funnel (routed is historical) — this is post-hoc PROOF, not a new route. Pure."""
    n = len(rows)
    for i, r in enumerate(rows):
        if r.get("gatePass") is not False or r.get("gateReason") != "quorum<2":
            continue
        lbl = r.get("label")
        # SCOPE: tooltip only. Tooltip witnesses (read=content · ocr=pixel · journal=time) are
        # genuinely independent, so a cross-frame union is honest. Stash/inventory lean on chrome
        # witnesses (tabstrip/grid) whose independence is deliberately guarded (the grid-solo
        # sanction + the phantom-ocr defense) — cross-frame borrowing there risks the exact
        # tabstrip+grid non-independence the per-frame gate carefully avoids, so it stays out.
        if lbl != "tooltip":
            continue
        my_cls = {_ROUTER_INDEP_CLASS.get(b, b) for b in (r.get("sources") or [])}
        if len(my_cls) >= 2:
            continue   # not actually solo — leave the router's own verdict
        ts = int(r.get("ts") or 0)
        union, borrowed = set(my_cls), set()
        for j in range(max(0, i - window_idx), min(n, i + window_idx + 1)):
            if j == i:
                continue
            nb = rows[j]
            if nb.get("label") != lbl:
                continue   # never cross labels — a different item can't corroborate
            if abs(int(nb.get("ts") or 0) - ts) > window_ms:
                continue   # outside the item's on-screen lifetime
            nb_cls = {_ROUTER_INDEP_CLASS.get(b, b) for b in (nb.get("sources") or [])}
            new_cls = nb_cls - union
            if new_cls:
                union |= nb_cls
                borrowed |= new_cls
        if len(union) < 2:
            continue   # no distinct 2nd class across the lifetime — stays honestly held
        # re-run the FULL gate with the cross-frame confidence + THIS frame's own cell inputs
        gate = _kai_gate_check(lbl, r.get("sources") or [], len(union), r.get("route"),
                               chrome_votes=r.get("_cv"), name_hit=r.get("_nh"),
                               grid_solo_ok=bool(r.get("_gs")))
        if gate.get("pass"):
            r["gatePass"] = True
            r["gateReason"] = "cross-frame"
            r["gateSources"] = sorted(set(r.get("gateSources") or []) | union)
            r["crossFrame"] = sorted(borrowed)
    return rows


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
                    "gateSources": sorted(set(sources) | set(chrome_votes.keys())),
                    # ② cross-frame quorum re-check inputs (private; stripped below)
                    "_cv": chrome_votes, "_nh": name_hit, "_gs": grid_solo_ok})
    # ② CROSS-FRAME QUORUM — promote frames held at quorum<2 that a same-label neighbor within the
    # item's on-screen lifetime corroborates with a DISTINCT independent class (union ≥2). Runs on
    # the full ledger (needs every frame's classes), re-runs the full gate, then the private inputs
    # are stripped so the row shape is unchanged (plus an optional `crossFrame` marker).
    _kai_crossframe_quorum(out)
    for _r in out:
        _r.pop("_cv", None)
        _r.pop("_nh", None)
        _r.pop("_gs", None)
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
    re-reads a frame the gate didn't prove), label is 'tooltip' or plain 'stash' (item/text
    frame — never gameplay/boot), and _kai_super_already_named says NO real DB item is already
    registered near this frame (no wasted calls on already-solved reads).

    v1381.1 — stash-runes|gems|materials are EXCLUDED from the item-judge super path. Those
    panels are tally recovery (gap-funnel + gemIntake/runeIntake/materialIntake), not
    aicJudge. Forensic: perfect gem grids were super-judged as tooltips → 429 / "no rare",
    while counts never ran. Tally recovery rides `_kai_stage3_gap_funnels` multi-retry instead.

    Highest-value first: 'tooltip' frames (direct item-name text) before plain 'stash',
    then by router confidence descending, then chronological.

    CAP: env TV_KAI_SUPER_MAX (default 10, the 8-12 budget) — a hard ceiling per reel so this
    organ can never run away. Returns the capped, ordered candidate routing rows."""
    fn = fullnames if fullnames is not None else _kai_fullnames()
    if cap is None:
        try:
            cap = max(0, int(os.environ.get("TV_KAI_SUPER_MAX", "10")))
        except Exception:
            cap = 10
    _TALLY_PANELS = ("stash-runes", "stash-gems", "stash-materials")
    cands = []
    for r in routing or []:
        if r.get("gatePass") is not True:
            continue
        f = r.get("f")
        if not f:
            continue
        label = str(r.get("label") or "")
        if label in _TALLY_PANELS:
            continue  # v1381.1 — tally intake lane, not item judge
        if label != "tooltip" and not label.startswith("stash"):
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

# ── v1325 B4 (engine landed v1324, recorded v1325) — DIABLO-LANGUAGE: game-true scene labels ──────────────────────────
# The reader emits a raw scene (town|stash|inventory|loot|gameplay|transition) + area.
# This DETERMINISTIC layer turns (scene, area) into the label a D2 player would say —
# ENTERING <area> · TOWN <area> · FARMING <area> — and decides TOWN-vs-FARMING (safe vs
# drops) from a fixed town-area list, NOT a model guess (a portal/loading frame that used
# to collapse to "gameplay/near-black" now reads "ENTERING <area>"). Honest: no scene AND
# no area ⇒ "unclear" (never invents a location). Pure — sessions-visual renders the label.
_TOWN_AREAS = (
    "rogue encampment", "lut gholein", "kurast docks", "kurast bazaar",
    "the pandemonium fortress", "pandemonium fortress", "harrogath",
)   # the 5 act-town safe zones (vanilla + RotW share these); substring-matched, case-insensitive


# B10 — canonical AREA → ACT map (fixed D2R/RotW game truth; RotW uses vanilla area names,
# confirmed by the reels). Keys are NORMALIZED: lowercased, leading "the " dropped, and any
# "Level N" / trailing-number suffix stripped (so "Catacombs Level 2" and "The Cave Level 1"
# resolve to their base area). Deterministic, never guessed — same discipline as _TOWN_AREAS.
# Unmapped areas resolve to None → the label degrades gracefully to the plain area (honest, no
# fabricated act). Covers the farmable zone space across all 5 acts.
_AREA_ACT = {
    # ── Act 1 ──
    "rogue encampment": 1, "blood moor": 1, "cold plains": 1, "cave": 1, "stony field": 1,
    "underground passage": 1, "dark wood": 1, "black marsh": 1, "tamoe highland": 1,
    "den of evil": 1, "burial grounds": 1, "crypt": 1, "mausoleum": 1, "forgotten tower": 1,
    "tower cellar": 1, "monastery gate": 1, "outer cloister": 1, "barracks": 1, "jail": 1,
    "inner cloister": 1, "cathedral": 1, "catacombs": 1, "tristram": 1, "moo moo farm": 1,
    "secret cow level": 1, "cow level": 1, "pit": 1, "hole": 1, "pit of the dead": 1,
    # ── Act 2 ──
    "lut gholein": 2, "rocky waste": 2, "sewers": 2, "dry hills": 2, "halls of the dead": 2,
    "far oasis": 2, "lost city": 2, "valley of snakes": 2, "claw viper temple": 2,
    "ancient tunnels": 2, "arcane sanctuary": 2, "palace cellar": 2, "harem": 2,
    "canyon of the magi": 2, "tal rasha's tomb": 2, "tal rasha's tombs": 2,
    "tal rasha's chamber": 2, "maggot lair": 2, "stony tomb": 2,
    # ── Act 3 ──
    "kurast docks": 3, "spider forest": 3, "spider cavern": 3, "great marsh": 3,
    "flayer jungle": 3, "flayer dungeon": 3, "swampy pit": 3, "lower kurast": 3,
    "kurast bazaar": 3, "upper kurast": 3, "kurast causeway": 3, "travincal": 3,
    "disused fane": 3, "forgotten reliquary": 3, "forgotten temple": 3, "ruined temple": 3,
    "disused reliquary": 3, "ruined fane": 3, "arachnid lair": 3, "durance of hate": 3,
    "sewers act 3": 3,
    # ── Act 4 ──
    "pandemonium fortress": 4, "outer steppes": 4, "plains of despair": 4,
    "city of the damned": 4, "river of flame": 4, "chaos sanctuary": 4,
    # ── Act 5 ──
    "harrogath": 5, "bloody foothills": 5, "frigid highlands": 5, "abaddon": 5,
    "arreat plateau": 5, "pit of acheron": 5, "crystalline passage": 5, "frozen river": 5,
    "glacial trail": 5, "drifter cavern": 5, "frozen tundra": 5, "ancients' way": 5,
    "icy cellar": 5, "arreat summit": 5, "nihlathak's temple": 5, "halls of anguish": 5,
    "halls of pain": 5, "halls of vaught": 5, "worldstone keep": 5, "throne of destruction": 5,
    "worldstone chamber": 5,
}


def _area_act(area):
    """Normalized area → act (1-5), or None when unmapped (honest — never a fabricated act)."""
    a = str(area or "").strip().lower()
    if not a:
        return None
    a = re.sub(r"\s+level[s]?\s+[0-9ivx]+$", "", a)   # "catacombs level 2" → "catacombs"
    a = re.sub(r"\s+[0-9]+$", "", a)                    # trailing bare number
    a = re.sub(r"^the\s+", "", a).strip()               # leading "the"
    return _AREA_ACT.get(a)


def _area_with_act(ar):
    """'Frigid Highlands' → 'Act 5 · Frigid Highlands' when mapped; unchanged when not."""
    act = _area_act(ar)
    return ("Act %d · %s" % (act, ar)) if act else ar


def _diablo_scene_label(scene, area, tab=""):
    """v1517 — `tab` names the CHRONICLE ledger (uniques/sets) when the reader knew it. Optional and
    last, so every existing caller is unchanged; a chronicle read without a tab still says the honest
    "📜 THE CHRONICLE" instead of picking a ledger."""
    if tab and str(scene or "").lower() == "chronicle":
        scene = "chronicle-" + str(tab).lower()
    return _diablo_scene_label_inner(scene, area)


def _diablo_scene_label_inner(scene, area):
    """(scene, area) → {kind, label, area, act}. kind ∈ entering|town|farming|menu|unclear.
    TOWN vs FARMING is decided deterministically by _TOWN_AREAS (safe vs drops), never guessed.
    B10 — the label carries the ACT in Diablo terms ("FARMING · Act 1 · Dark Wood") when the area
    is in the canonical _AREA_ACT map; an unmapped area degrades to the plain label (no fabricated
    act), and `unclear` stays unclear. `act` (int|None) rides the dict for structured consumers."""
    sc = str(scene or "").strip().lower()
    ar = str(area or "").strip()
    act = _area_act(ar)
    ara = _area_with_act(ar)   # "Act N · <area>" when mapped, else the plain area
    is_town = bool(ar) and any(t in ar.lower() for t in _TOWN_AREAS)
    if sc in ("transition", "loading"):
        return {"kind": "entering", "area": ar or None, "act": act,
                "label": ("ENTERING " + ara) if ar else "ENTERING (loading)"}
    # v1509 — THE CHRONICLE, in his words. This label is what the receipts feed AND the theatre
    # caption show (v1508 wired theatre to this same function), so the ledger he is looking at is
    # named the way he would say it out loud — not "chronicle-uniques".
    if sc == "chronicle" or sc.startswith("chronicle"):
        tab = sc.split("-", 1)[1] if "-" in sc else ""
        nm = ("🏆 THE CHRONICLE · Holy Grail" if tab == "uniques"
              else "🧩 THE CHRONICLE · Set pieces" if tab == "sets"
              else "📜 THE CHRONICLE")
        return {"kind": "menu", "area": ar or None, "act": act, "label": nm}
    if sc.startswith("stash") or sc in ("inventory", "loot"):
        # an open panel is what's ON SCREEN — it wins over the underlying town/area context.
        # `stash`, `stash-gems`, `stash-runes`, `stash-materials` (tab-classified) all → STASH.
        nm = "INVENTORY" if sc == "inventory" else ("LOOT" if sc == "loot" else "STASH")
        return {"kind": "menu", "area": ar or None, "act": act,
                "label": nm + (" · " + ara if ar else "")}
    if is_town or sc == "town":
        return {"kind": "town", "area": ar or None, "act": act,
                "label": ("TOWN · " + ara) if ar else "TOWN (safe)"}
    if sc == "gameplay":
        return {"kind": "farming", "area": ar or None, "act": act,
                "label": ("FARMING · " + ara) if ar else "FARMING"}
    if ar:   # no scene word, but the read named an area — classify by the town list
        return {"kind": "farming", "area": ar, "act": act, "label": "FARMING · " + ara}
    return {"kind": "unclear", "area": None, "act": None, "label": "unclear"}


def _session_scene_fingerprint(sess_rows):
    """v1326 B8 — a truthful per-session SCENE FINGERPRINT from the deep reads' (scene, area),
    classified through _diablo_scene_label. Real counts ONLY; None when the session read no
    scene/area (honest-absent, like coverage/classFrames). Feeds the shelf/dossier line
    "62% farming · 3 town trips · 2 portals · mostly Dark Wood". Pure, no I/O."""
    kinds, seen_areas, farm_area = [], [], {}
    for r in sess_rows or []:
        if r.get("lane") != "deep":
            continue
        sc = str(r.get("scene") or "").strip().lower()
        ar = str(r.get("area") or "").strip()
        if not (sc or ar):
            continue
        kind = _diablo_scene_label(sc, ar)["kind"]
        kinds.append(kind)
        if ar and ar not in seen_areas:
            seen_areas.append(ar)
        if ar and kind == "farming":
            farm_area[ar] = farm_area.get(ar, 0) + 1
    if not kinds:
        return None
    farming = kinds.count("farming")
    town = kinds.count("town")
    # town TRIPS = distinct town visits = maximal runs of town-kind reads (a town read
    # following a non-town read opens a new trip). Approx but honest (reads, not wall-time).
    # PORTALS = distinct portal/loading EVENTS = maximal runs of 'entering' reads (same run-
    # counting law as trips), NOT the raw 'entering' read count — a single portal's loading
    # screen spans several frames, so the raw count over-counted up to 4× on real sessions
    # ("took 4 portals" when Konyo took 1). Reads, not wall-time; honest + consistent with trips.
    trips, portals, prev = 0, 0, None
    for k in kinds:
        if k == "town" and prev != "town":
            trips += 1
        if k == "entering" and prev != "entering":
            portals += 1
        prev = k
    denom = farming + town   # world-time reads (menus/unclear excluded from the %)
    return {
        "farmingReads": farming, "townReads": town, "portals": portals,
        "townTrips": trips,
        "farmingPct": (round(100 * farming / denom) if denom else None),
        "topArea": (max(farm_area, key=farm_area.get) if farm_area else None),
        "areas": seen_areas[:8],
        "sceneReads": len(kinds),
    }


# ── ⚔ EV-RANK — the flagship's "hunt next" intelligence (engine owns the pure ranking; the
# CLIENT provides each missing grail's best-source odds from its Calculator, so the odds model
# never drifts). Ranks missing grails by expected-HOURS-to-next-find, fastest first. ───────────
def _ev_hours(drop_chance, kills_per_hr, confidence=0.5):
    """Expected HOURS to reach `confidence` probability of finding a grail whose PER-RUN drop
    probability is `drop_chance`, farming at `kills_per_hr`. Matches the Calculator EXACTLY (no
    reimplementation-drift): runs = log(1 - confidence) / log(1 - drop_chance); hours = runs /
    kph. Returns None — honest-absent, NEVER a fabricated EV — when the odds are invalid:
    drop_chance ∉ (0,1), kph ≤ 0, or confidence ∉ (0,1). Pure."""
    try:
        p = float(drop_chance)
        kph = float(kills_per_hr)
        c = float(confidence)
    except (TypeError, ValueError):
        return None
    if not (0.0 < p < 1.0) or kph <= 0 or not (0.0 < c < 1.0):
        return None
    # CEIL the runs (whole runs) to match the bible's Calculator `runsFor` EXACTLY, so the flagship
    # hero and F·Uniques show ONE number for the same grail (Konyo sees both surfaces).
    runs = math.ceil(math.log(1.0 - c) / math.log(1.0 - p))
    return runs / kph


def _ev_rank(items, confidence=0.5):
    """Rank missing grails by expected-hours-to-next-find (ascending = hunt these first). `items`
    = the client's missing grails, each {name, dropChance (per-run prob), killsPerHr, source?}.
    Returns {ranked: [...ascending by expectedHours, name tiebreak...], unranked: [{name, why}],
    confidence}. An item with invalid/unknown odds is honest-absent in `unranked` — never given a
    fabricated rank. Pure + deterministic (stable sort). The engine's intelligence; the client's
    Calculator supplies the honest odds."""
    ranked, unranked = [], []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        name = str(it.get("name") or "").strip()
        if not name:
            continue
        h = _ev_hours(it.get("dropChance"), it.get("killsPerHr"), confidence)
        # v1559 — the same formula, applied to the item's best HELL source when it has one.
        # The client used to export only the globally-fastest source, so a caller wanting "fastest
        # in Hell" could only filter the already-collapsed answer and silently lost every item whose
        # global best happened to be Normal. Ranking both here keeps ONE hours formula: a second
        # implementation in the console is exactly how the hero and the meter drifted apart.
        hh = _ev_hours(it.get("hellDropChance"), it.get("hellKillsPerHr"), confidence)
        if h is None:
            unranked.append({"name": name, "why": "no known farm / odds"})
        else:
            ranked.append({"name": name, "source": it.get("source"),
                           "expectedHours": round(h, 2),
                           "dropChance": it.get("dropChance"), "killsPerHr": it.get("killsPerHr"),
                           # honest-absent: an item with no Hell source carries None, never a copy
                           # of the easier number dressed as a Hell one
                           "hellSource": it.get("hellSource") if hh is not None else None,
                           "hellExpectedHours": round(hh, 2) if hh is not None else None})
    ranked.sort(key=lambda r: (r["expectedHours"], r["name"].lower()))
    return {"ranked": ranked, "unranked": unranked, "confidence": confidence}


def _forward_area_from(ts, area_ts, window=8000):
    """B5 — the zone being ENTERED after a transition/loading frame = the NEXT area-naming read
    within `window` ms FORWARD (loading precedes the zone by a few seconds), NOT the nearest (which
    can be the PREVIOUS zone → "ENTERING <wrong zone>"). `area_ts` = [(readTs, area), …]. Returns
    "" when none — honest-absent → "ENTERING (loading)". Pure. The ONE shared law for both the
    reconciler (engineFrames) and the classFrames ribbon, so both name the entering zone identically."""
    ts = int(ts or 0)
    if not ts:
        return ""
    best, bd = "", int(window) + 1
    for rt, ar in area_ts or []:
        if not ar:
            continue
        fwd = int(rt or 0) - ts
        if 0 < fwd <= window and fwd < bd:
            best, bd = ar, fwd
    return best


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

    # B5 AREA-INFERENCE — a transition/loading frame is a DARK screen with no area of its own, so
    # nearest-read can't name it. The zone being ENTERED is named by the NEXT deep read that has an
    # area (forward-looking, loading precedes the zone by a few seconds) → "ENTERING The Pit".
    # Honest-absent: no forward zone → None → "ENTERING (loading)" unchanged. Never over-claims.
    _FWD_WIN = 8000
    def _forward_area(ts):
        return _forward_area_from(ts, [(rt, ar) for rt, sc, tb, ar in deep_scene_ts], _FWD_WIN)

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
        _scene = (_sc[0] or None) if _sc else None
        _area = (_sc[2] or None) if _sc else None
        # B5 — a transition frame borrows the zone being ENTERED from the next deep read (forward).
        if _scene == "transition" and not _area:
            _fa = _forward_area(ts)
            if _fa:
                _area = _fa
        out.append({"f": f, "ts": ts, "owner": owner, "verdict": verdict, "why": why,
                    "scene": _scene,
                    "tab": (_sc[1] or None) if _sc else None,
                    "area": _area,
                    # v1325 B4 (engine landed v1324, recorded v1325) — game-true label (ENTERING/TOWN/FARMING + area) for the UI
                    "native": _diablo_scene_label(_scene, _area)})
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


def _session_completeness(sess_rows, reel_frames, tol_ms=_COMPLETENESS_TOL_MS, missed=None):
    """Pure. Two independent gap classes, both real signal, only one a bug:

      'unread'       — KAI's retro reel sweep saw item text with no deep read anywhere near
                        it (from kai_report.missed[] when provided, else journal lane=='kai'
                        per-item rows with NON-EMPTY texts — NOT kai-judge rows). The moment
                        WAS filmed — a reel frame backs every one by construction — it just
                        went unread. Honest, already-caught. NOT a drop.
      'read-no-film' — a deep read landed (an item WAS read, hover→read worked) but no reel
                        frame exists within tol_ms of its captureTs. This IS a capture drop:
                        the film thread didn't archive a still near that moment.

    v1408 — kai-judge rows (Super/forensics stamps with frameId + empty texts) used to inflate
    'unread' (e.g. 2 real reads + 14 judges → 12.5% on a fully-swept reel with missedFrames=0).
    Only REAL missed-item text counts. A legitimate 100% is reads>0 and unread=0.

    sess_rows: this session's journal rows (already filtered to one sessionId).
    reel_frames: the sealed reel's index.json 'frames' list [{"f":.., "ts":..}, ...] —
    the film's ground truth of what was actually archived to hist_dir.
    missed: optional list from kai_report.missed[] (authoritative when present).

    Returns {hovers_estimated, reads, reel_frames, gaps: [...], unread, dropped, coveragePct}.
    hovers_estimated = reads + unread — the best estimate available of "moments item text
    appeared" (no raw hover-event stream exists to count directly; the retro OCR ledger is
    the closest ground-truth proxy, per Konyo's instruction to use kai_report.missed[]).
    coveragePct = reads / hovers_estimated * 100 — the read-side registration rate."""
    reads = [r for r in (sess_rows or []) if r.get("lane") == "deep" and (r.get("names") or [])]
    # Authoritative unread: report.missed[] when the closer just built it; else journal rows
    # that are REAL missed-text ledgers (mode kai/empty, non-empty texts) — never kai-judge.
    if isinstance(missed, list):
        kai_item_rows = None
        missed_items = [m for m in missed if (m.get("texts") or [])]
    else:
        missed_items = None
        kai_item_rows = [r for r in (sess_rows or [])
                          if r.get("lane") == "kai"
                          and r.get("mode") != "kai-judge"
                          and r.get("frameId")
                          and isinstance(r.get("kai"), dict)
                          and (r.get("kai") or {}).get("texts")]
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
    if missed_items is not None:
        for m in missed_items:
            texts = m.get("texts") or []
            gaps.append({"ts": int(m.get("ts") or 0), "kind": "unread",
                         "frameId": m.get("f") or m.get("frameId"),
                         "note": "text seen, never read: " + ", ".join(str(t) for t in texts[:3])})
        n_unread = len(missed_items)
    else:
        for r in kai_item_rows:
            texts = (r.get("kai") or {}).get("texts") or []
            gaps.append({"ts": int(r.get("ts") or 0), "kind": "unread", "frameId": r.get("frameId"),
                         "note": "text seen, never read: " + ", ".join(str(t) for t in texts[:3])})
        n_unread = len(kai_item_rows)
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
    hovers_estimated = n_reads + n_unread
    # honest-absent: NO item-moments (0 reads AND 0 unread) → None, never a fabricated 100%
    # ("100% coverage" on a session with nothing to cover is a real over-claim — 4/27 reels). A
    # LEGITIMATE 100% (reads>0, unread=0 = read everything, nothing unread) still computes to 100.
    coverage_pct = round(100.0 * n_reads / hovers_estimated, 1) if hovers_estimated else None
    return {
        "hovers_estimated": hovers_estimated,
        "reads": n_reads,
        "reel_frames": len(reel_frames or []),
        "gaps": gaps,
        "unread": n_unread,
        "dropped": dropped,
        "coveragePct": coverage_pct,
    }


def _coverage_from_report(report):
    """v1408 — Theatre coverage meter from a sealed kai_report, judge-inflation-proof.

    Prefer report.missedFrames (real OCR misses the closer counted) over completeness.unread
    which on pre-v1408 seals included every kai-judge frameId row. When KAI sealed with
    missedFrames=0 and any named deep reads → 100%. Honest-absent when nothing to cover."""
    if not isinstance(report, dict):
        return None
    cmp = report.get("completeness") if isinstance(report.get("completeness"), dict) else {}
    reads = int(cmp.get("reads") or 0)
    if report.get("missedFrames") is not None:
        unread = int(report.get("missedFrames") or 0)
    elif isinstance(report.get("missed"), list):
        unread = sum(1 for m in report["missed"] if (m.get("texts") or []))
    else:
        unread = int(cmp.get("unread") or 0)
    total = reads + unread
    if total <= 0:
        return None
    return {"read": reads, "total": total, "gaps": unread,
            "pct": round(100.0 * reads / total, 1)}


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


# ── G3 auto-route sweep ──────────────────────────────────────────────────────
# READ-ONLY aggregation of what KAI witnessed across every session (reel registers
# + deep-lane journal names + the AI-funnel INTAKE counts) → a de-duped per-tracker
# tally. Powers GET /api/autoroute-sweep, which the bible.html "🔄 Auto-route sweep"
# panel fetches, diffs merge-max against the live trackers, and applies ONLY on an
# explicit in-UI click. This endpoint writes NOTHING. (built by g3-sweep, gated by lead)
#
# Design honesty (from the G3 read-only sweep report):
#  · INTAKE lane is aggregated (the register alone misses the sunders — caveat 6).
#  · Held counts use MAX-of-snapshot, never SUM (the funnel re-reads the same photo).
#  · Stable game constants (runes/gems/sunders/statues/materials) are hardcoded here
#    (robust vs bible.html line drift); runewords come from the live _RWC_SEED list.
#  · UNIQUES are deliberately left to the browser: only the runtime ITEM_REGISTRY
#    (~403, built from BOSSES[].dropTable) is authoritative, so every non-stackable
#    name ships as a `candidate` for the UI to classify against live vocab (caveat 3).
#
# Konyo's routing model (the UI splits `candidates` into 3 outcomes, no dead-end):
#  1) tracked/chronicle item → auto-route into its tracker (the merge-max apply).
#  2) non-chronicle real item (RotW/white bases · rolled magic/rare) → the 🔬 AI Item
#     Checker → vault path (keep-or-toss + mule), NOT auto-tallied.
#  3) genuinely unreadable → a tiny "unclear · needs a look" list.
# The endpoint stays outcome-agnostic: it returns the stackable tallies + the raw
# `candidates`; the browser (which holds ITEM_REGISTRY) does the 3-way routing.

_AUTOROUTE_RUNES = [
    "El", "Eld", "Tir", "Nef", "Eth", "Ith", "Tal", "Ral", "Ort", "Thul", "Amn",
    "Sol", "Shael", "Dol", "Hel", "Io", "Lum", "Ko", "Fal", "Lem", "Pul", "Um",
    "Mal", "Ist", "Gul", "Vex", "Ohm", "Lo", "Sur", "Ber", "Jah", "Cham", "Zod",
]
_AUTOROUTE_GEM_TYPES = ["Amethyst", "Diamond", "Emerald", "Ruby", "Sapphire", "Topaz", "Skull"]
_AUTOROUTE_GEM_QUALS = ["Chipped", "Flawed", "", "Flawless", "Perfect"]  # "" = Normal (bare)
_AUTOROUTE_SUNDER_BASES = [
    "Bone Break", "Black Cleft", "Crack of the Heavens",
    "Cold Rupture", "Flame Rift", "Rotting Fissure",
]
_AUTOROUTE_STATUES = [
    "Talic's Anguish", "Korlic's Pain", "Madawc's Ire",
    "Bul-Kathos' Nightmare", "Worusk's End",
]
# SPECIAL_DROPS materials (non-sunder, non-statue). Essence display-name variants
# (Twisted/Charged/Burning/Festering …) normalize to the raw essence — caveat 5.
_AUTOROUTE_MATERIALS = [
    "Essence of Suffering", "Essence of Hatred", "Essence of Terror", "Essence of Destruction",
    "Token of Absolution", "Key of Terror", "Key of Hate", "Key of Destruction",
    "Diablo's Horn", "Baal's Eye", "Mephisto's Brain",
    "Worldstone Shard (Western)", "Worldstone Shard (Eastern)", "Worldstone Shard (Southern)",
    "Worldstone Shard (Northern)", "Worldstone Shard (Deep)",
    "Full Rejuvenation Potion", "Partial Rejuvenation Potion",
    "Annihilus", "Hellfire Torch", "Wirt's Leg",
    "Colossal Ancient Jewels", "Colossal Ancient Statue",
]
_AUTOROUTE_ESSENCE_ALIAS = {
    "twisted essence of suffering": "Essence of Suffering",
    "charged essence of hatred": "Essence of Hatred",
    "burning essence of terror": "Essence of Terror",
    "festering essence of destruction": "Essence of Destruction",
}


def _autoroute_gem_names():
    out = []
    for t in _AUTOROUTE_GEM_TYPES:
        for q in _AUTOROUTE_GEM_QUALS:
            out.append((q + " " + t).strip() if q else t)
    return out


def _autoroute_norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _autoroute_runewords():
    """Live runeword vocabulary from bible.html's _RWC_SEED map (flat one-liner).
    Memoized by bible.html mtime. Falls back to an empty set if unreadable."""
    try:
        mt = os.path.getmtime(BIBLE)
    except Exception:
        mt = 0.0
    c = globals().setdefault("_AUTOROUTE_RW_CACHE", {"mtime": None, "val": set()})
    if c["mtime"] == mt and c["val"]:
        return c["val"]
    names = set()
    try:
        with open(BIBLE, encoding="utf-8", errors="replace") as fh:
            src = fh.read()
        m = re.search(r"const\s+_RWC_SEED\s*=\s*\{(.*?)\};", src, re.S)
        if m:
            names = set(re.findall(r'"([^"]+)"\s*:', m.group(1)))
        # union RUNEWORD_TIP keys too (some RotW words live only there)
        m2 = re.search(r"const\s+RUNEWORD_TIP\s*=\s*\{(.*?)\};", src, re.S)
        if m2:
            names |= set(re.findall(r'"([^"]+)"\s*:\s*\{', m2.group(1)))
    except Exception:
        names = set()
    c["mtime"], c["val"] = mt, names
    return names


def _autoroute_sunder_family(name):
    n = _autoroute_norm(name)
    n = re.sub(r"\bgrand charm\b", "", n).strip()
    n = re.sub(r"^\s*(latent|renewed)\s+", "", n).strip()
    for b in _AUTOROUTE_SUNDER_BASES:
        if _autoroute_norm(b) == n:
            return b
    return None


def _autoroute_aggregate(rows, reel_reports):
    """Collect every distinct witnessed name → {intake_max, reads, sources}. READ-ONLY."""
    agg = {}

    def bump(name, reads=0, intake=0, source=None):
        if not isinstance(name, str) or not name.strip():
            return
        e = agg.setdefault(name, {"intake": 0, "reads": 0, "sources": set()})
        if intake:
            e["intake"] = max(e["intake"], intake)
        e["reads"] += reads
        if source:
            e["sources"].add(source)

    name_fields = ("names", "names_new", "confirmed_names", "discovered_names",
                   "farmed_names", "vault_names")
    for r in rows or []:
        lane = r.get("lane")
        if lane == "deep":
            for fl in name_fields:
                v = r.get(fl)
                if isinstance(v, list):
                    for x in v:
                        bump(x, reads=1, source="journal")
        elif lane == "intake":
            counts = (r.get("intake") or {}).get("counts") or {}
            for k, v in counts.items():
                if isinstance(v, int) and k != "items":   # "items" = funnel meta total
                    bump(k, intake=v, source="intake")
    for rep in reel_reports or []:
        for it in (rep.get("register") or []):
            bump(it.get("name"), reads=1, source="register")
    return agg


def _autoroute_classify(agg):
    """De-dupe the witnessed aggregate into per-tracker buckets. READ-ONLY, no writes."""
    rune_l = {_autoroute_norm(x): x for x in _AUTOROUTE_RUNES}
    gem_l = {_autoroute_norm(x): x for x in _autoroute_gem_names()}
    mat_l = {_autoroute_norm(x): x for x in _AUTOROUTE_MATERIALS}
    stat_l = {_autoroute_norm(x): x for x in _AUTOROUTE_STATUES}
    rw_l = {_autoroute_norm(x) for x in _autoroute_runewords()}

    sunders, runes, gems, materials, statues = {}, {}, {}, {}, {}
    candidates = {}   # name -> {count, sources}  (non-stackables → UI classifies)
    uniques, runewords, unclear = [], [], []

    for name, e in agg.items():
        # STACKABLE count = the TALLY (intake) — the AI's actual count in the stash panel. A
        # stackable read but NEVER tallied (intake=0) reports 1 ("seen, uncounted"), NEVER the
        # frame-SIGHTING count (reads): sightings ≠ quantity (a rune read 5× is not 5 runes; the
        # audit found "Hellfire Torch ×5" fabricated from 5 sightings). Tallied stackables are
        # unchanged (0 in the data have reads>intake). Non-stackable candidates below keep reads
        # (a unique seen N× may be N distinct drops — UI-classified + reviewed).
        held = e["intake"] if e["intake"] > 0 else 1
        n = _autoroute_norm(name)
        srcs = sorted(e["sources"])

        fam = _autoroute_sunder_family(name)
        if fam:
            sunders[fam] = max(sunders.get(fam, 0), held)
            continue
        base = re.sub(r"\s+rune$", "", n)
        if base in rune_l:
            k = rune_l[base]
            runes[k] = max(runes.get(k, 0), held)
            continue
        if n in gem_l:
            k = gem_l[n]
            gems[k] = max(gems.get(k, 0), held)
            continue
        if n in _AUTOROUTE_ESSENCE_ALIAS:
            k = _AUTOROUTE_ESSENCE_ALIAS[n]
            materials[k] = max(materials.get(k, 0), held)
            continue
        if n in stat_l:
            k = stat_l[n]
            statues[k] = max(statues.get(k, 0), held)
            continue
        if n in mat_l:
            k = mat_l[n]
            materials[k] = max(materials.get(k, 0), held)
            continue
        # non-stackable → candidate for the browser's live-vocab classifier
        candidates[name] = {"count": e["reads"] or 1, "sources": srcs}
        if n in rw_l:
            runewords.append(name)
        else:
            unclear.append(name)   # UI re-buckets vs live ITEM_REGISTRY (uniques/sets)

    # drop the two never-seen sunder families entirely (honesty: never seed them)
    sunders = {k: v for k, v in sunders.items() if v > 0}
    return {
        "sunders": sunders,
        "runes": runes,
        "gems": gems,
        "materials": materials,
        "statues": statues,
        "candidates": candidates,
        "uniques": sorted(uniques),
        "runewords": sorted(runewords),
        "unclear": sorted(unclear),
    }


def _autoroute_sweep_cached(rows, reel_reports, cache_key):
    """Memoized sweep result. Keyed by (bible mtime, journal identity, reels signature)
    so the panel poll never re-aggregates a cold journal. READ-ONLY."""
    c = globals().setdefault("_AUTOROUTE_SWEEP_CACHE", {"key": None, "val": None})
    if c["key"] == cache_key and c["val"] is not None:
        return c["val"]
    out = _autoroute_classify(_autoroute_aggregate(rows, reel_reports))
    out["stats"] = {
        "reels": len(reel_reports),
        "deepRows": sum(1 for r in (rows or []) if r.get("lane") == "deep"),
        "intakeEvents": sum(1 for r in (rows or []) if r.get("lane") == "intake"),
        "distinctNames": (len(out["runes"]) + len(out["gems"]) + len(out["materials"])
                          + len(out["statues"]) + len(out["sunders"]) + len(out["candidates"])),
    }
    c["key"], c["val"] = cache_key, out
    return out


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
        # v1408 — rebuild from full report so judge-inflated pre-v1408 completeness.unread
        # doesn't poison the engine-health "readers" organ (was 2/16=13% on fully-swept reels).
        _rep = json.load(open(rp, encoding="utf-8")) or {}
        c = _rep.get("completeness") if isinstance(_rep.get("completeness"), dict) else None
        if isinstance(c, dict) and c.get("reads") is not None:
            _cf = _coverage_from_report(_rep)
            if _cf:
                c = dict(c)
                c["unread"] = _cf["gaps"]
                c["hovers_estimated"] = _cf["total"]
                c["coveragePct"] = _cf["pct"]
            val = c
        else:
            val = None
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


def _kai_report_needs_reclose(report, target):
    """v1381.0 — pure. True when a sealed kai_report should re-enter the closer queue.
    Stale kaiVer, OR incomplete seal (scanned frames but no routing ledger — window-kill
    mid-closer left Theatre film unlabeled)."""
    if not isinstance(report, dict):
        return True
    try:
        kv = int(report.get("kaiVer") or 1)
    except Exception:
        kv = 1
    if kv < int(target or 0):
        return True
    try:
        sc = int(report.get("scanned") or 0)
    except Exception:
        sc = 0
    rt = report.get("routing")
    if sc > 0 and not rt:
        return True
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
            # E3 — bump target to 5 so kaiVer-4 reels re-sweep to pick up E1 ground-label two-
            # witness grounding (War Traveler etc. → real registers, not just the forensics X-ray)
            # + the ② cross-frame quorum. Additive/merge-max; wallpaper re-seals gameplay
            # (deterministic panel-open guard, verified 0 not_d2r leaks across 29 reels).
            # v1381.0 — bump to 6: gate-aware gap-funnel ranking + multi-retry + real-receipt
            # watchdog + incomplete-seal reclose (scanned>0 but routing missing — window-kill
            # mid-closer left film playable with no per-frame filter chrome).
            _KAIVER_TARGET = 6
            reels = []
            for d in sorted(os.listdir(hist)):
                if not (d.startswith("reel_") and os.path.isdir(os.path.join(hist, d))):
                    continue
                # This `continue` is literally what hid reel_s_1785708285647_38665 (98 frames,
                # no index) from the theatre. Repair FIRST — skip only a reel that truly has
                # nothing playable. The reel_ guard above keeps cache160/cache1280 out.
                if not _reel_ensure_index(os.path.join(hist, d))[0]:
                    continue
                kr = os.path.join(hist, d, "kai_report.json")
                if not os.path.isfile(kr):
                    reels.append(d)
                    continue
                try:
                    with open(kr, encoding="utf-8") as _kf:
                        _rep = json.load(_kf) or {}
                    if _kai_report_needs_reclose(_rep, _KAIVER_TARGET):
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
            frames = _reel_index_frames(rd) or []
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
                      # ⚠️ CONVENTION (E3 lesson): ANY change to seal-time logic (grounding /
                      # gate / routing) MUST bump this kaiVer AND _KAIVER_TARGET above in lockstep,
                      # so already-sealed reels auto-resweep and pick it up. Skip the bump and old
                      # reels silently strand with stale registers (E3 found E1/②/E4 had done exactly
                      # that — 29 reels frozen pre-E1). kaiVer 6 = v1381 gate-aware gap-funnel +
                      # multi-retry + real-receipt watchdog + incomplete-seal reclose.
                      "closedAt": int(time.time() * 1000), "kaiVer": 6,
                      "eyeNote": "E1 ground-label two-witness + ② cross-frame quorum + v1259 honest "
                                 "gate (grid-solo sanctioned) + v1258 panel-open guard + retro gap "
                                 "funnel + v1381 gate-aware multi-retry funnel"}
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
            # v1712 — THE HEADLINE SAID 108 AND THE EVIDENCE SAVED 20.
            # `missed[:20]` above writes one verbose row per frame, carrying its texts for the UI.
            # That cap is reasonable for rows; what was NOT reasonable is that the other 88 frames
            # then existed only as a COUNT. Measured on s_1786385768689_67392: 217 scanned, 158
            # with text, missedFrames=108, and exactly 20 'unread text' rows in sessions.jsonl.
            # So a number that was perfectly honest sat next to evidence that had been thrown away,
            # and nothing downstream — no retro sweep, no re-read, no audit — could ever name the
            # 88 frames it referred to. A silent cap reads as "covered everything" when it did not.
            # The ids are ~20 bytes each; carrying all of them costs ~2KB per session and makes the
            # missed set RECOVERABLE. `missedShown` names the cap out loud so the two numbers can
            # never drift apart again unnoticed.
            _missed_ids = [str(m.get("f") or "") for m in missed if m.get("f")]
            rows.append({"ts": _sess_last + 1, "captureTs": _sess_last + 1, "completedTs": now_ms,
                         "lane": "kai", "mode": "kai", "scene": "kai", "names": [],
                         "sessionId": sid, "frameId": "",
                         "kai": {**{k: report[k] for k in ("scanned", "textFrames", "missedFrames")},
                                 "classes": classes,
                                 "missedIds": _missed_ids,
                                 "missedShown": min(len(missed), 20)},
                         "note": f"🧠 KAI closed the session — {scanned} frames swept · "
                                 f"{len(missed)} frames held text no eye read"
                                 + (f" ({20} detailed, all {len(missed)} named in missedIds)"
                                    if len(missed) > 20 else "")})
            try:
                with open(_journal_path(), "a", encoding="utf-8") as f:
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
                        _cands_by = _kai_stage3_gap_funnel_candidates(_plan + routing_scan, _gap_rows)
                        _have = {str(j.get("tab") or "") for j in _funnel_jobs}
                        for _g in _gaps:
                            if str(_g.get("tab") or "") not in _have:
                                _funnel_jobs.append(_g)
                                _have.add(str(_g.get("tab") or ""))
                                print(f"📸 KAI gap-funnel: queue {_g.get('tab')} from {_g.get('f')} "
                                      f"(reel recheck, conf={_g.get('conf')}, score={_g.get('score')})", flush=True)
                        # v1381.0 — re-rank every funnel job's primary frame + attach alts from
                        # gate-aware candidates (stage-3 "newest conf≥2" alone can pick wrong-cell).
                        for _fj in _funnel_jobs:
                            _tb = str(_fj.get("tab") or "")
                            _ranked = list(_cands_by.get(_tb) or [])
                            if not _ranked:
                                continue
                            _best = _ranked[0]
                            if _best.get("f") and _best.get("f") != _fj.get("f"):
                                print(f"📸 KAI funnel re-rank: {_tb} {_fj.get('f')} → {_best.get('f')} "
                                      f"(score={_best.get('score')})", flush=True)
                                _fj["f"] = _best.get("f")
                                _fj["ts"] = _best.get("ts")
                                _fj["conf"] = _best.get("conf")
                                _fj["score"] = _best.get("score")
                            _fj["alts"] = [j["f"] for j in _ranked[1:5]
                                           if j.get("f") and j.get("f") != _fj.get("f")]
                    except Exception as _gfe:
                        print(f"⚠ KAI gap-funnel select: {_gfe}", flush=True)
                    w2 = globals().get("_MAIN_WIN")
                    # 📸 FUNNEL — up to 4 stills per tally tab (best → alts), SET-wrapper.
                    # v1381.0 multi-retry: wrong-cell / empty reader on shot 1 must not seal the tab.
                    for _fj in _funnel_jobs:
                        if w2 is None or os.environ.get("TV_KAI_FUNNEL", "1") == "0":
                            break
                        t3 = str(_fj.get("tab") or "")
                        if not t3:
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
                        _frames_q = []
                        for _fx in [str(_fj.get("f") or "")] + list(_fj.get("alts") or []):
                            _fx = str(_fx or "")
                            if _fx and _fx not in _frames_q:
                                _frames_q.append(_fx)
                        if not _frames_q:
                            continue
                        _tab_real = False
                        for _ff in _frames_q[:4]:
                            if _tab_real:
                                break
                            # re-check never-zero between retries (a prior alt may have landed)
                            try:
                                _fresh_t3 = [r for r in _kai_journal_rows() if r.get("sessionId") == sid]
                            except Exception:
                                pass
                            if _tab_best_total(_fresh_t3, t3) > 0:
                                _tab_real = True
                                break
                            _histp = "/hist/reel_" + sid + "/" + _ff
                            _fid3 = "reel_" + sid + "/" + _ff.replace(".jpg", "")
                            # v1689 🛑 CHRONICLE ROUTE GUARD — third and last stash/vault/tally
                            # fire in this file (live driver + Stage-3 vault are the other two).
                            # A Chronicle page is not a rune/gem/material tally either; refuse
                            # this alt and let the loop try the next one.
                            if _kai_route_guard_refuse("kai-funnel", _fid3,
                                                       _capture_ts_from_frame_id(_fid3), sid, t3):
                                continue
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
                                   "}).catch(function(_e3){try{fetch('/intake_result',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ts:Date.now(),tab:%s,kind:'kai-funnel',ok:false,counts:{},total:0,errors:1,frameId:%s,err:String(_e3&&_e3.message||_e3||'funnel fetch/intake rejected')})}).catch(function(){})}catch(e4){}});"
                                   "return 1}catch(e){return 0}})()") % (
                                      json.dumps(t3), json.dumps(t3), json.dumps(t3), json.dumps(_prev_best_t3),
                                      json.dumps(_histp), json.dumps(t3), json.dumps(_fid3),
                                      json.dumps(t3), json.dumps(_fid3))
                            try:
                                _ejs(w2, _js, timeout=5.0)
                                print(f"📸 KAI funnel (ledger): fired {t3} from {_ff} "
                                      f"(prevBest={_prev_best_t3}, try {_frames_q.index(_ff)+1}/{min(4,len(_frames_q))})",
                                      flush=True)
                            except Exception as _fe:
                                print(f"⚠ KAI funnel fire failed ({t3} {_ff}): {_fe}", flush=True)
                                continue
                            # v1201 — monotonic deadline; wall-clock journal cutoff (unchanged).
                            # v1381.0 — wait for a REAL receipt (ok+total>0) OR an honest fail
                            # on THIS frameId, then retry next alt on fail.
                            _t0f = time.time()
                            _t0f_mono = time.monotonic()
                            _got_receipt = False
                            while time.monotonic() - _t0f_mono < 120.0:
                                time.sleep(6.0)
                                try:
                                    for r3 in _kai_journal_rows()[-40:]:
                                        if r3.get("lane") != "intake":
                                            continue
                                        ik3 = r3.get("intake") or {}
                                        if str(ik3.get("kind") or "") != "kai-funnel":
                                            continue
                                        if str(ik3.get("tab") or "") != t3:
                                            continue
                                        if int(r3.get("completedTs") or 0) < int(_t0f * 1000):
                                            continue
                                        # prefer matching this attempt's frameId when present
                                        _rfid = str(r3.get("frameId") or "")
                                        if _rfid and _fid3 not in _rfid and _ff.replace(".jpg", "") not in _rfid:
                                            continue
                                        _got_receipt = True
                                        if _intake_is_real(ik3):
                                            _tab_real = True
                                            print(f"📸 KAI funnel: {t3} REAL receipt total="
                                                  f"{ik3.get('total')} from {_ff} ✓", flush=True)
                                            try:
                                                _res = {"ts": _sess_last + 40, "captureTs": _sess_last + 40,
                                                        "completedTs": int(time.time() * 1000), "lane": "watchdog",
                                                        "mode": "watchdog", "scene": "watchdog", "names": [],
                                                        "sessionId": sid, "frameId": "",
                                                        "watchdog": {"rule": "resolved-by-kai-funnel", "tab": t3},
                                                        "note": (f"✅ WATCHDOG resolved — KAI funnel REAL "
                                                                 f"receipted {t3} ×{ik3.get('total')} from the reel")}
                                                with open(_journal_path(), "a",
                                                          encoding="utf-8") as _rf:
                                                    _rf.write(json.dumps(_res, ensure_ascii=False) + "\n")
                                                _wl = globals().get("_WATCHDOG_LAST")
                                                if isinstance(_wl, dict) and _wl.get("sid") == sid and _wl.get("violations"):
                                                    _wl["violations"] = max(0, int(_wl["violations"]) - 1)
                                            except Exception:
                                                pass
                                        else:
                                            print(f"📸 KAI funnel: {t3} empty/error on {_ff} "
                                                  f"(ok={ik3.get('ok')} total={ik3.get('total')}) "
                                                  f"— try next still", flush=True)
                                        break
                                    if _got_receipt:
                                        break
                                except Exception:
                                    pass
                            if not _got_receipt:
                                print(f"⚠ KAI funnel: {t3} no receipt within budget on {_ff}", flush=True)
                        if not _tab_real:
                            print(f"🚨 KAI funnel: {t3} still no REAL tally after "
                                  f"{min(4, len(_frames_q))} still(s) — watchdog stays open", flush=True)
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
                    # 🏦 VAULT — v1381.1 default ON for Stage-3 ledger-selected vault jobs
                    # (conf≥2, not-selected, gate already filtered). Opt-out: TV_KAI_VAULT=0.
                    # Prior default off left 22+ fireable vault candidates never fired (Theatre
                    # playthrough audit s_178498…95276).
                    for _vj in _vault_jobs[:1]:
                        if w2 is None or os.environ.get("TV_KAI_VAULT", "1") == "0":
                            break
                        _ffv = str(_vj.get("f") or "")
                        if not _ffv:
                            continue
                        _hpv = "/hist/reel_" + sid + "/" + _ffv
                        _fidv = "reel_" + sid + "/" + _ffv.replace(".jpg", "")
                        _tabv = "personal"  # vaultIntake is tab-agnostic; journal tab for receipt
                        # v1689 🛑 CHRONICLE ROUTE GUARD — same law on the Stage-3 (post-seal)
                        # vault fire as on the live driver: a frame the vision lane called
                        # 'chronicle' is not vault footage. THIS is the fire that produced the
                        # measured ok:false total:0 on reel_s_1786385768689_67392.
                        if _kai_route_guard_refuse("kai-vault", _fidv, _vj.get("ts"), sid, _tabv):
                            continue
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
                    # G3-LIVE-FORWARD (TV_G3_LIVE, default OFF = byte-identical): when ON, (delta 1)
                    # feed G4's chronicle-disagreement flag into the triage gate so a Grok-doubted grail
                    # HOLDs instead of auto-ticking, and (delta 3) route the session's non-chronicle reads
                    # to the AI-Checker queue. The grounded auto-accept itself is UNCHANGED (already smart).
                    _g3live = os.environ.get("TV_G3_LIVE", "0") == "1"
                    try:
                        if w2 is not None and _register and os.environ.get("TV_CHRONICLE_PROPOSE", "1") != "0":
                            _items = [dict({"name": x.get("name"), "firstSeenTs": x.get("firstSeenTs"),
                                            "frameId": x.get("frameId"), "tier": x.get("tier"),
                                            "sessionId": sid, "loc": x.get("loc")},
                                           **({"g4": x.get("g4")} if (_g3live and x.get("g4")) else {}))
                                      for x in (_register or [])[:40]]
                            _cjs = ("(function(){try{var F=document.getElementById('tvd-eng');"
                                    "if(!F||!F.contentWindow||typeof F.contentWindow.kaiChroniclePropose!=='function')return 0;"
                                    "var r=F.contentWindow.kaiChroniclePropose(%s);return (r&&r.queued)||0}catch(e){return -1}})()"
                                    ) % json.dumps(_items)
                            _cq = _ejs(w2, _cjs, timeout=4.0)
                            print(f"📖 Chronicle propose: queued={_cq} from {len(_items)} register items", flush=True)
                        # G3-LIVE delta 3 — non-chronicle reads → the AI Item Checker queue (live-forward ON only)
                        if w2 is not None and _g3live:
                            _nc = []
                            for _r3 in (sess_rows or []):
                                if _r3.get("lane") == "deep":
                                    for _n3 in (_r3.get("names") or []):
                                        if isinstance(_n3, str) and _n3.strip():
                                            _nc.append(_n3.strip())
                            _nc = list(dict.fromkeys(_nc))[:60]
                            if _nc:
                                _ncjs = ("(function(){try{var F=document.getElementById('tvd-eng');"
                                         "if(!F||!F.contentWindow||typeof F.contentWindow.kaiForwardNonChronicle!=='function')return 0;"
                                         "var r=F.contentWindow.kaiForwardNonChronicle(%s);return (r&&r.queued)||0}catch(e){return -1}})()"
                                         ) % json.dumps(_nc)
                                _ncq = _ejs(w2, _ncjs, timeout=4.0)
                                print(f"🔬 G3-live non-chronicle → checker queue: {_ncq} from {len(_nc)} reads", flush=True)
                    except Exception as _cpe:
                        print(f"⚠ Chronicle propose / G3-live failed: {_cpe}", flush=True)
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
                    # v1408 — pass closer's missed[] so completeness never counts kai-judge stamps.
                    try:
                        _completeness = _session_completeness(_reg_rows, frames, missed=missed)
                        report["completeness"] = _completeness
                        _cp = _completeness.get("coveragePct")
                        _cp_disp = (f"{_cp}%" if _cp is not None else "n/a (no item reads)")
                        print(f"🎞 KAI completeness: {_completeness['reads']} reads · "
                              f"{_completeness['reel_frames']} reel frames · "
                              f"{_cp_disp} covered · "
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
                                           f"({_completeness['dropped']} drops)"
                                           if _completeness and _completeness.get("coveragePct") is not None else "")
                                        + (f" · 🧠🔬 super-analyze recovered {len(_super_recovered_names)}/"
                                           f"{len(_super_attempted)}" if _super_attempted else "")}
                    with open(_journal_path(), "a", encoding="utf-8") as _rf3:
                        _rf3.write(json.dumps(_reg_row, ensure_ascii=False) + "\n")
                    print(f"📖 KAI register: {len(_register)} witnessed · 🚦 routing: {len(_routing)} frames, "
                          f"{_routed_n} fired in {sid}", flush=True)
                except Exception as _rge:
                    print(f"⚠ KAI register/routing stage error: {_rge}", flush=True)
            except Exception as _we:
                print(f"🚨 watchdog: check raised ({_we})", flush=True)
        except Exception:
            time.sleep(10.0)


def _intake_why(body):
    """ONE SENTENCE SAYING WHICH KIND OF NOTHING THIS WAS.

    Four outcomes that used to look identical in the journal and in the AI-READS feed. They are
    different facts and a reader acts differently on each, so they get different words — the same
    rule v1887 applied to a zero count and v1943 to an empty routing.
    """
    try:
        err = int(body.get("errors") or 0)
    except Exception:
        err = 0
    try:
        tot = int(body.get("total") or 0)
    except Exception:
        tot = 0
    ok = bool(body.get("ok", True))
    if body.get("err"):
        return str(body.get("err"))[:200]
    if err:
        return "read failed \u2014 %d image error%s" % (err, "" if err == 1 else "s")
    if body.get("guardHeld"):
        return "held \u2014 the read did not beat the stored count"
    if not ok and not tot:
        return "read fine \u2014 nothing on this screen to count"
    return ""


def _kai_journal_rows():
    """Fresh journal rows for KAI (module-level read; the handler cache is instance-side)."""
    rows = []
    try:
        with open(_journal_path(), encoding="utf-8") as f:
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


# ── v1689 🛑 CHRONICLE ROUTE GUARD — the two classifiers finally reconciled ──────────
# _kai_frame_cls() (this file, ~4232) has NO 'chronicle' class at all: its whole vocabulary is
# stash-runes|stash-gems|stash-materials|stash|inventory|tooltip|gameplay. An in-game Chronicle
# page is a LIST OF ITEM NAMES, so it reads as 'itemish', so it returns 'tooltip'. The Claude
# vision lane, looking at the SAME footage, called those frames scene='chronicle' — measured on
# session s_1786385768689_67392: 8 deep rows, chronicleTab='uniques', conf 0.60→0.95, while the
# close row's own classes read {stash:1, gameplay:53, tooltip:158}. NOTHING reconciled the two.
# The consequence is not cosmetic: a kai-vault intake FIRED on a Chronicle frame
# (reel_s_1786385768689_67392/f_1786385778600) and errored ok:false total:0 — a vault reader
# pointed at a Chronicle page.
# THE GUARD, deliberately narrow: when the vision read for a frame's MOMENT said
# scene=='chronicle', that frame may not be routed into a stash / vault / tally intake. It is
# REFUSED with a NAMED reason, journalled through the same intake-receipt channel every real
# result uses (/intake_result's row shape, ok:false + err), and COUNTED — a silent skip would
# turn a routing fault into a smaller invoice and nothing else (v1543's own lesson). What this
# does NOT do: it does not touch _kai_frame_cls's vocabulary (a 'chronicle' class there is a
# later ship), and it does not touch the grail / chronicle / board writes — the Chronicle's OWN
# lane still receives the frame. Only the stash/vault/tally intake is refused.
# WINDOW: ±12s, not the ±4s tooltip-association window used elsewhere. Measured reason — the
# offending vault frame sat 4089 ms BEFORE the first chronicle read, so ±4000 misses the real
# incident by 89 ms, and his chronicle reads were 4.6–9.7 s apart (a Chronicle is READ by
# scrolling, so the vision lane samples it sparsely).
# THE JOIN IS NOT NEAREST-READ — that was this guard's first shape and it MISSED the one
# incident it was built for. Measured on his real journal, around f_1786385778600: the nearest
# deep read is scene='gameplay' at −791 ms; the chronicle read is at +4089 ms. Nearest-wins
# hands the frame to the vault reader, which is exactly the bug. Reading a Chronicle MEANS
# scrolling it, so the frames between vision reads read as 'gameplay' — 'gameplay' is an
# ABSENCE of a claim about what is on screen, not a rebuttal of one.
# THE RULE: a chronicle read anywhere in the window refuses the frame, UNLESS a read that is
# strictly NEARER positively NAMES A STASH TAB (he shut the Chronicle and opened the stash).
# Only a positive stash claim rebuts a chronicle claim — this is a routing guard, never a
# blanket block, and the live engine driver's own queueing read (stashTab set, delta ≈ 0)
# rebuts by construction, so legitimate stash intakes are untouched.
_CHRON_ROUTE_WIN_MS = 12000
# Intake kinds that photograph a stash/vault GRID or tally a stash tab. Every kind string this
# file POSTs to /intake_result from such a fire is listed here; grail/chronicle/board writes are
# deliberately absent.
_ROUTE_GUARD_INTAKE_KINDS = ("vault", "vault-count", "kai-vault", "gridcount",
                             "tally", "kai-funnel")


def _chronicle_tab_of_row(row):
    """The read's own chronicleTab, from its raw JSON payload ('' when absent — never guessed)."""
    raw = (row or {}).get("raw")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raw = None
    if isinstance(raw, dict):
        return str(raw.get("chronicleTab") or "")[:24]
    return ""


def _kai_deep_scene_near(ts, sid="", rows=None, window_ms=_CHRON_ROUTE_WIN_MS):
    """v1689 — what did the VISION lane call this MOMENT? The NEAREST deep read carrying a
    scene within ±window_ms (the frame an intake photographs is rarely the exact frame a read
    consumed — same nearest-read join _kai_build_routing's _nearest_scene uses). Honest-absent:
    no read in the window → None, never a guess. → {scene, tab, chronicleTab, ts, deltaMs}.
    REPORTING ONLY — the route guard does NOT decide on this (nearest-wins missed the real
    incident); it decides on _kai_chron_claim_near below."""
    try:
        ts = int(ts or 0)
    except Exception:
        ts = 0
    if not ts:
        return None
    if rows is None:
        rows = _kai_journal_rows()
    best, best_d = None, None
    for r in rows or []:
        if not isinstance(r, dict) or r.get("lane") != "deep":
            continue
        sc = str(r.get("scene") or "").strip().lower()
        if not sc:
            continue
        if sid and str(r.get("sessionId") or "") != str(sid):
            continue
        try:
            rt = int(r.get("captureTs") or r.get("ts") or 0)
        except Exception:
            rt = 0
        if not rt:
            continue
        d = abs(rt - ts)
        if d > window_ms:
            continue
        if best_d is None or d < best_d:
            best, best_d = {"scene": sc, "tab": str(r.get("stashTab") or ""),
                            "chronicleTab": _chronicle_tab_of_row(r),
                            "ts": rt, "deltaMs": d}, d
    return best


def _kai_chron_claim_near(ts, sid="", rows=None, window_ms=_CHRON_ROUTE_WIN_MS):
    """v1689 — WHO CLAIMS THIS MOMENT? → (chron, stash): the NEAREST deep read within ±window_ms
    that called the scene 'chronicle', and the NEAREST one that positively NAMES A STASH TAB.
    Either may be None. Two separate scans on purpose: nearest-read-wins was the guard's first
    shape and his own journal refutes it — around f_1786385778600 the nearest read is 'gameplay'
    at −791 ms while the chronicle read is at +4089 ms, so nearest-wins routed a vault reader
    onto a Chronicle page. A scroll-heavy read leaves 'gameplay' frames between vision reads;
    'gameplay' is an absence of a claim, not a rebuttal. Only a stash tab rebuts."""
    try:
        ts = int(ts or 0)
    except Exception:
        ts = 0
    if not ts:
        return None, None
    if rows is None:
        rows = _kai_journal_rows()
    chron = stash = None
    for r in rows or []:
        if not isinstance(r, dict) or r.get("lane") != "deep":
            continue
        sc = str(r.get("scene") or "").strip().lower()
        if not sc:
            continue
        if sid and str(r.get("sessionId") or "") != str(sid):
            continue
        try:
            rt = int(r.get("captureTs") or r.get("ts") or 0)
        except Exception:
            rt = 0
        if not rt:
            continue
        d = abs(rt - ts)
        if d > window_ms:
            continue
        tab = str(r.get("stashTab") or "").strip()
        if sc == "chronicle" and (chron is None or d < chron["deltaMs"]):
            chron = {"scene": sc, "tab": tab, "chronicleTab": _chronicle_tab_of_row(r),
                     "ts": rt, "deltaMs": d}
        if tab and (stash is None or d < stash["deltaMs"]):
            stash = {"scene": sc, "tab": tab, "ts": rt, "deltaMs": d}
    return chron, stash


def _kai_route_guard_reason(kind, ts, sid="", rows=None):
    """'' when this frame may be routed into `kind`; a NAMED, human-readable reason when it
    may not. Only stash/vault/tally intake kinds are guarded — anything else routes untouched.
    Refuses on ANY chronicle read in the window unless a strictly NEARER read names a stash tab
    (see _kai_chron_claim_near for why nearest-read-wins was the wrong policy)."""
    k = str(kind or "").strip().lower()
    if k not in _ROUTE_GUARD_INTAKE_KINDS:
        return ""
    chron, stash = _kai_chron_claim_near(ts, sid, rows)
    if not chron:
        return ""
    if stash and stash["deltaMs"] < chron["deltaMs"]:
        return ""   # he shut the Chronicle and opened the stash — a positive rebuttal
    tab = chron.get("chronicleTab") or ""
    return ("chronicle-frame · the vision read %d ms away called this scene 'chronicle'%s — a "
            "Chronicle page is a LIST OF ITEM NAMES, not a stash/vault grid, so the %s intake "
            "would read the wrong thing (it did: ok:false, total:0). Refused. The Chronicle's "
            "own lane still gets this frame."
            % (int(chron.get("deltaMs") or 0), (" (tab '" + tab + "')") if tab else "", k))


def _kai_route_guard_refuse(kind, fid, ts=None, sid="", tab="", rows=None):
    """THE REFUSAL. '' → route normally. Otherwise: journal an honest receipt in the SAME shape
    /intake_result writes (ok:false, refused:true, err=<the named reason>) so the operator sees
    it on the very channel the real results land on, bump the refusal counter (exposed beside
    fired/refire in /api/status — an in-process counter with exactly the lifetime fired/refire
    have: it resets on restart, and the DURABLE record of a refusal is the journal row written
    above, which is still countable afterwards), print it, and return the reason. Never silent —
    a silent skip is just a smaller invoice."""
    if ts in (None, 0, "", "0"):
        ts = _capture_ts_from_frame_id(fid)
    why = _kai_route_guard_reason(kind, ts, sid, rows)
    if not why:
        return ""
    globals()["_DRV_CHRON_REFUSED"] = globals().get("_DRV_CHRON_REFUSED", 0) + 1
    _sid = str(sid or "")
    if not _sid:
        _m = re.match(r"^reel_(.+?)/", str(fid or ""))
        if _m:
            _sid = _m.group(1)
    try:
        now_ms = int(time.time() * 1000)
        _cap = _capture_ts_from_frame_id(fid)
        if _cap is None:
            try:
                _cap = int(ts or now_ms)
            except Exception:
                _cap = now_ms
        rec = {"ts": now_ms, "captureTs": _cap, "completedTs": now_ms,
               "n": 0, "scene": "intake", "lane": "intake", "mode": "intake",
               "names": [], "area": "", "sessionId": _sid,
               "intake": {"tab": str(tab or "")[:24], "kind": str(kind or "")[:16],
                          "counts": {}, "total": 0, "errors": 0, "items": [],
                          "ok": False, "refused": True, "err": why[:300]},
               "frameId": str(fid or "")[:48],
               "note": ("⛔ intake refused · chronicle · " + str(kind or ""))[:80]}
        with open(_journal_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as _rge:
        print(f"⚠ route guard: refusal journal failed: {_rge}", flush=True)
    print(f"⛔ KAI route guard: {fid} — {why}", flush=True)
    return why


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
            with open(_journal_path(), "a", encoding="utf-8") as f:
                for r in out_rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"🚨 watchdog: journal append failed ({e})", flush=True)

    # 🔌 ENGINE-EXPOSURE — deepen the exposure (engine-reality audit): the console can't paint an honest
    # watchdog dial from a bare count. Surface WHAT tripped (rule names), WHEN (ts), and a
    # clean/violations verdict. Still null until the first seal (honest-absent → no dial yet).
    globals()["_WATCHDOG_LAST"] = {"sid": sid, "violations": len(out_rows),
                                   "rules": [v["rule"] for v in violations],
                                   "ts": now_ms,
                                   "verdict": "violations" if out_rows else "clean"}
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
    # v1379 — was 24 live subscription judges/session @ 18s; that alone could burn dozens
    # of Claude Code sessions (each a full project load). Default now 6 @ 45s; set
    # TV_KAI_JUDGE_LIVE_MAX=0 to disable live judges entirely.
    try:
        _jlive_max = max(0, int(os.environ.get("TV_KAI_JUDGE_LIVE_MAX", "6")))
    except Exception:
        _jlive_max = 6
    try:
        _jlive_gap = max(5, int(os.environ.get("TV_KAI_JUDGE_LIVE_GAP_S", "45")))
    except Exception:
        _jlive_gap = 45
    _probes_out = 0
    while True:
        try:
            time.sleep(2.0)
            # v1410 — window ✕: exit cleanly. Never evaluate_js a dead WKWebView (hang class).
            if not globals().get("_WINDOW_LIVE"):
                print("🔌 engine driver stop — window gone (✕)", flush=True)
                return
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
                globals()["_DRV_BEAT"] = int(time.time() * 1000)   # 🔌 router heartbeat — last time the brain actually routed a read (for engines{} liveness)
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
                # v1689 🛑 CHRONICLE ROUTE GUARD — the ONE choke point every live vault /
                # vault-count / tally fire passes through. Refuse (loudly, counted, journalled)
                # before the lease is claimed, so a Chronicle page never burns a tab lease OR a
                # vault read. Guarded ahead of the lease on purpose: a refused frame that had
                # already claimed the lease would block the board from a real shot.
                _gk = ("vault-count" if str(job.get("key") or "").startswith("vaultcount_")
                       else "vault" if str(job.get("key") or "").startswith("vault_")
                       else "tally")
                if _kai_route_guard_refuse(_gk, job.get("fid") or "", job.get("ts"),
                                           job.get("sid") or "", job.get("tab") or ""):
                    visit_done[job["key"]] = True   # this visit is answered: refused, not pending
                    continue
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
        key = os.path.getmtime(_journal_path())
    except Exception:
        key = None
    c = globals().get("_EYES_CACHE")
    if c and c[0] == key:
        return c[1]
    # 🔌 ENGINE-EXPOSURE — the LIVE EYE (primary reader) joins verify+kai so all three eyes share
    # ONE shape {liveTs, verifyTs, kaiTs}. liveTs = newest deep read's completed ts (journal-derived,
    # same source + cache as the other two). status_payload adds a FRESH liveAgeMs on top (the "now"
    # eye's age matters live, so it's computed per-poll, not frozen in this mtime cache). 0 = no read yet.
    out = {"liveTs": 0, "verifyTs": 0, "kaiTs": 0, "kaiMissed": None}
    try:
        for r in _kai_journal_rows()[-400:]:
            ln = r.get("lane")
            if ln == "deep":
                out["liveTs"] = max(out["liveTs"], int(r.get("completedTs") or r.get("ts") or 0))
            elif ln == "verify":
                out["verifyTs"] = max(out["verifyTs"], int(r.get("completedTs") or r.get("ts") or 0))
            elif ln == "kai":
                out["kaiTs"] = max(out["kaiTs"], int(r.get("completedTs") or r.get("ts") or 0))
                if isinstance(r.get("kai"), dict) and "missedFrames" in r["kai"]:
                    out["kaiMissed"] = r["kai"].get("missedFrames")
    except Exception:
        pass
    globals()["_EYES_CACHE"] = (key, out)
    return out


def _engine_thread_alive(name):
    """True iff a daemon thread with this exact name is alive right now (engine wired + running)."""
    try:
        return any(t.name == name and t.is_alive() for t in threading.enumerate())
    except Exception:
        return False


# 🔌 ENGINE-EXPOSURE — per-engine wired/running/last-beat: the "nothing hidden · a disconnected
# wire must be VISIBLE, never silent" safeguard Konyo demanded. PURE liveness projection off the
# v1349 truths (eyes/driver/watchdog) + thread enumeration — no new bookkeeping beyond the router
# heartbeat. Honest semantics:
#   wired = the machinery is plugged in (thread alive / proven by a real beat / armed in the seal
#           path). wired:false → the UI paints a ⚫ disconnected wire.
#   state = 'live' (a real beat within this engine's cadence) · 'idle' (wired, quiet now) · 'down'
#           (SHOULD run but isn't — wedged eye / dead-hard engine) · 'armed' (watchdog: event-
#           driven, always ready, fires at seal).
#   lastBeatMs = the engine's last real act (null = never — honest-absent, no fake glow).
_ENG_FRESH_FAST = 30000     # reader / verify / router: beat every ~2s when active
_ENG_FRESH_SLOW = 300000    # kai / watchdog: act in post-seal bursts → "recent" = 5 min


def _engines_status():
    now = int(time.time() * 1000)
    eyes = _eyes_pulse()
    alive = _agent_alive()
    onair = (_agent_mode != "off")

    def _fresh(ts, win):
        return bool(ts) and (now - int(ts)) <= win

    # 🔴 LIVE EYE — the reader (agent subprocess). Core, always wired; live while it reads.
    live_ts = int(eyes.get("liveTs") or 0)
    if _fresh(live_ts, _ENG_FRESH_FAST):
        le_state, le_note = "live", "reading"
    elif onair and alive and live_ts and not _fresh(live_ts, _ENG_FRESH_SLOW):
        le_state, le_note = "down", "on-air but no read in 5min — eye may be wedged"
    elif onair and alive:
        le_state, le_note = "idle", "on-air, between reads"
    else:
        le_state, le_note = "idle", "off-air"
    liveEye = {"label": "🔴 Live Eye", "wired": True, "state": le_state,
               "lastBeatMs": live_ts or None, "note": le_note}

    # 🔵 SECOND EYE — the verify lane (agent subprocess). Control can't read the agent's flag, so
    # wired is EVIDENCE-BASED (honest, mirrors the badge doctrine): proven only by a real verify
    # beat. Never seen → ⚫ (deliberately off, or not connected).
    ver_ts = int(eyes.get("verifyTs") or 0)
    se_wired = ver_ts > 0
    if not se_wired:
        se_state, se_note = "idle", "no verify beat ever seen (TV_VERIFY off?)"
    elif _fresh(ver_ts, _ENG_FRESH_FAST):
        se_state, se_note = "live", "verifying"
    else:
        se_state, se_note = "idle", "wired, quiet"
    secondEye = {"label": "🔵 Second Eye", "wired": se_wired, "state": se_state,
                 "lastBeatMs": ver_ts or None, "note": se_note}

    # 🧠 KAI — the closer thread (control) + the live judge. wired = the closer thread alive; it
    # exits early when TV_KAI=0 or bin/ocr_mac is missing → the thread ends → ⚫ "not plugged",
    # the exact disconnected wire Konyo wants surfaced.
    kai_ts = int(eyes.get("kaiTs") or 0)
    kai_on = os.environ.get("TV_KAI", "1") != "0"
    kai_wired = _engine_thread_alive("tvd-kai-closer")
    if not kai_wired:
        kai_state = "down" if kai_on else "idle"
        kai_note = "no OCR bin (ocr_mac) — closer not plugged" if kai_on else "TV_KAI off"
    elif _fresh(kai_ts, _ENG_FRESH_SLOW):
        kai_state, kai_note = "live", "closing / judging"
    else:
        kai_state, kai_note = "idle", "armed between sessions"
    kai = {"label": "🧠 KAI", "wired": kai_wired, "state": kai_state,
           "lastBeatMs": kai_ts or None, "note": kai_note}

    # 🚦 ROUTER / DRIVER — the scanning brain (control daemon). wired = driver thread alive;
    # down = engine declared dead-hard after failed revives. beat = last real route (_DRV_BEAT).
    drv_beat = int(globals().get("_DRV_BEAT") or 0)
    drv_alive = _engine_thread_alive("tvd-engine-driver")
    dead_hard = bool(globals().get("_ENGINE_DEAD_HARD"))
    drv_err = globals().get("_DRV_ERR")
    if dead_hard or not drv_alive:
        rt_state = "down"
        rt_note = "engine dead — restart the app" if dead_hard else "driver thread not running"
    elif _fresh(drv_beat, _ENG_FRESH_FAST):
        rt_state, rt_note = "live", "routing reads"
    else:
        rt_state = "idle"
        rt_note = ("last error: " + str(drv_err)[:60]) if drv_err else "wired, no reads to route"
    router = {"label": "🚦 Router", "wired": drv_alive, "state": rt_state,
              "lastBeatMs": drv_beat or None, "note": rt_note}

    # 🛡 WATCHDOG — event-driven, armed in the seal path (not a loop). beat = the last seal it
    # checked, verdict rides the note.
    # v1456 HONESTY (audit): this lamp was hardcoded wired:True/state:"armed" — a lamp that can
    # NEVER report down is decoration, not instrumentation. It now speaks the same vocabulary as
    # every other lamp: down when the engine is dead-hard (nothing will arm it), live when it just
    # checked a seal, idle when it is armed but has checked nothing yet. "armed" as a permanent
    # state is gone — the note says so instead.
    wl = globals().get("_WATCHDOG_LAST")
    wd_ts = int((wl or {}).get("ts") or 0)
    wd_verdict = (wl or {}).get("verdict") or ""
    if dead_hard:
        wd_state = "down"
        wd_note = "engine dead — no seal will arm the watchdog"
    elif _fresh(wd_ts, _ENG_FRESH_SLOW):
        wd_state = "live"
        wd_note = wd_verdict or "checked a seal"
    else:
        wd_state = "idle"
        wd_note = (("armed · last seal: " + wd_verdict) if wd_verdict
                   else "armed, no seal checked yet")
    watchdog = {"label": "🛡 Watchdog", "wired": not dead_hard, "state": wd_state,
                "lastBeatMs": wd_ts or None, "note": wd_note,
                "verdict": wd_verdict or None,
                "rules": list((wl or {}).get("rules") or [])}

    return {"liveEye": liveEye, "secondEye": secondEye, "kai": kai,
            "router": router, "watchdog": watchdog}


# 🧾 ENGINE-EXPOSURE — the READ-RECEIPT STREAM (Konyo's org backbone). Every real AI read gets a
# canonical, ROUTABLE identity so the bottom-of-TV-D feed can label + click-route + hover-art each
# one. Grounded in refs that already exist (sessionId/frameId on disk); no invented id-space.
#   id       = DETERMINISTIC from real refs ("engine:frameKey:seq") — same journal row → same id
#              every poll, so the streaming feed self-dedupes; only REAL rows get ids.
#   itemName = the item-id (the DB is name-keyed); the CLIENT resolves name→canonical dossier when
#              grounded, else →🔬 Checker (server stays DB-agnostic — no fake dossier links).
#   route    = click target: 'item'→dossier/checker · 'session'→shelf · 'flag'→watchdog panel.
#   diablo.label = game-true WHERE via _diablo_scene_label; null when there's no real scene.
# Read-only DISPLAY projection — NO grail writes. mtime-cached like eyes/gate; empty off-air.
_RECEIPTS_CAP = 30
_RECEIPT_LANE_ENGINE = {
    "deep": ("liveEye", "read"),
    "verify": ("secondEye", "verify"),
    "kai": ("kai", "judge"),
    "intake": ("router", "route"),
    "watchdog": ("watchdog", "flag"),
}


def _receipts_stream():
    try:
        key = os.path.getmtime(_journal_path())
    except Exception:
        key = None
    c = globals().get("_RECEIPTS_CACHE")
    if c and c[0] == key:
        return c[1]
    out = []
    try:
        for r in _kai_journal_rows()[-160:]:   # tail is plenty for ~30 newest receipts
            lane = str(r.get("lane") or "")
            em = _RECEIPT_LANE_ENGINE.get(lane)
            if not em:
                continue
            engine, kind = em
            ts = int(r.get("completedTs") or r.get("ts") or 0)
            sid = str(r.get("sessionId") or "")
            fid = str(r.get("frameId") or "")
            frame_key = fid if fid else (lane + "_" + str(r.get("ts") or ts))
            scene = str(r.get("scene") or "")
            area = str(r.get("area") or "")
            _dl = _diablo_scene_label(scene, area)
            diablo = {"label": _dl["label"]} if _dl.get("kind") != "unclear" else None

            def _refs(**extra):
                base = {"sessionId": sid or None, "frameId": fid or None,
                        "area": area or None, "scene": scene or None}
                base.update(extra)
                return {k: v for k, v in base.items() if v is not None}

            # v1456 HONESTY (audit): the feed listed every read name as if the accuracy gate had
            # blessed it — a gate-REFUSED name (gatePass False, e.g. gateReason=wrong-cell) looked
            # exactly as authoritative as a proven one. Doctrine is SURFACE, never hide: each
            # receipt now carries the gate verdict so the UI can chip a held read as held.
            _gp = r.get("gatePass")
            gate = {"pass": _gp if isinstance(_gp, bool) else None,
                    "reason": (str(r.get("gateReason") or "") or None)}
            held = _gp is False

            # 🛡 watchdog → one flag receipt, routes to the flag panel
            if lane == "watchdog":
                wd = r.get("watchdog") if isinstance(r.get("watchdog"), dict) else {}
                rule = str(wd.get("rule") or "")
                note = str(r.get("note") or "")
                out.append({"id": "%s:%s:0" % (engine, frame_key), "engine": engine, "kind": kind,
                            "ts": ts, "refs": _refs(), "gate": gate, "held": held,
                            "diablo": {"label": ("WATCHDOG: " + (note or rule))[:70]} if (rule or note) else None,
                            "route": {"type": "flag", "target": rule} if rule else ({"type": "session", "target": sid} if sid else None)})
                continue

            # 🚦 intake (router fire) → one route receipt, routes to the session shelf
            if lane == "intake":
                ik = r.get("intake") if isinstance(r.get("intake"), dict) else {}
                tab = str(ik.get("tab") or ik.get("kind") or "")
                tot = int(ik.get("total") or 0)
                if not tot and isinstance(ik.get("counts"), dict):
                    try:
                        tot = int(sum(int(v) for v in ik["counts"].values()))
                    except Exception:
                        tot = 0
                # ── v1943 — A ROUTE THAT CARRIED NOTHING MUST NOT READ LIKE ONE THAT CARRIED
                # SOMETHING. Konyo: "also AI read needs an update", looking at five identical
                # `routed · ROUTED gems` rows.
                #
                # They were not vague — they were EMPTY, and the row could not tell him. MEASURED
                # over his whole journal (4412 rows, 46 intakes, 2026-07-25 -> 2026-08-21 16:52):
                # ONE succeeded and FORTY-FIVE counted nothing. The last eight are all
                # ok=False errors=0 total=0 — the reader ran fine and found nothing to tally — and
                # every one of them rendered exactly like a successful routing.
                #
                # `×N` was already appended when there was an N. The bug is the silence when there
                # is not: `if tot` is falsy at zero, so a routing of nothing printed the same words
                # as a routing of seven. Zero is a MEASUREMENT and it gets said out loud — the same
                # rule v1887 applied to the stash tallies next door. [[unknown-stays-unknown]]
                _ok = bool(ik.get("ok", True))
                _err = int(ik.get("errors") or 0)
                # v1945 — prefer the reason the record actually carries; the derivations below are
                # the fallback for rows written before the handler started keeping it.
                _why = str(ik.get("why") or "").strip()
                if tot:
                    _tail = " \u00d7%d" % tot
                elif _why:
                    _tail = " \u00b7 " + _why
                elif _err:
                    _tail = " \u00b7 read failed (%d image error%s)" % (_err, "" if _err == 1 else "s")
                elif not _ok:
                    _tail = " \u00b7 nothing counted"
                else:
                    _tail = ""
                out.append({"id": "%s:%s:0" % (engine, frame_key), "engine": engine, "kind": kind,
                            "ts": ts, "refs": _refs(), "gate": gate, "held": held,
                            "empty": (not tot),
                            "diablo": {"label": ("ROUTED " + tab + _tail).strip()} if tab else None,
                            "route": {"type": "session", "target": sid} if sid else None})
                continue

            # 🔴🔵🧠 named lanes (deep read / verify / kai judge) → one receipt PER item name
            names = r.get("names") if isinstance(r.get("names"), list) else []
            if lane == "kai" and isinstance(r.get("kai"), dict) and isinstance(r["kai"].get("judge"), dict):
                jn = r["kai"]["judge"].get("name")
                if isinstance(jn, str) and jn.strip() and jn not in names:
                    names = [jn] + list(names)
            names = [str(n).strip() for n in names if isinstance(n, str) and str(n).strip()]
            for i, nm in enumerate(names):
                out.append({"id": "%s:%s:%d" % (engine, frame_key, i), "engine": engine, "kind": kind,
                            "ts": ts, "refs": _refs(itemName=nm), "gate": gate, "held": held,
                            "diablo": diablo,
                            "route": {"type": "item", "target": nm}})   # client grounds name→dossier|checker
    except Exception:
        out = []
    out.sort(key=lambda x: x.get("ts") or 0, reverse=True)
    out = out[:_RECEIPTS_CAP]
    globals()["_RECEIPTS_CACHE"] = (key, out)
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


IDENTITY_PATH = os.path.join(HERE, ".tvd_identity.json")


def set_install_nickname(name):
    """v1496 — name this machine. Konyo: "can it just be more nicknamed? more UX and friendlier."

    The opaque install id stays the identity (two machines can share a hostname and a user, which is
    exactly why v1465 minted a random id); the nickname is only what a human reads. Stored beside it
    in the same gitignored file, so it never travels to another PC."""
    data = install_identity() or {}
    data["nickname"] = str(name or "").strip()[:40]
    try:
        tmp = IDENTITY_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        os.replace(tmp, IDENTITY_PATH)
    except Exception as e:
        print(f"⚠ could not save the machine nickname: {e}", flush=True)
    return data


# NOT _FLEET_CACHE — that name belongs to v1418's fleet_origin_status (git origin vs this PC), and
# reusing it swapped the dict shape out from under it. The suite caught it on the first run.
_FLEET_PRESENCE_CACHE = {"t": 0.0, "d": None}


def _completed_names(applied):
    """v1570 — read completeSets whatever shape it arrives in.

    chronicle_retro.apply_proposal returns a LIST of names; a merge_max result would be a dict with
    "added". Accepting both is not defensive clutter — the two producers genuinely differ, and the
    version that assumed one shape was a live grenade with the pin already out.
    """
    v = (applied or {}).get("completeSets")
    if isinstance(v, dict):
        return list(v.get("added") or [])
    if isinstance(v, (list, tuple, set)):
        return list(v)
    return []

def chronicle_apply(proposal=None):
    # v1763 — a restarted console must still be able to apply what the watchdog found while it was
    # a different process. Without this the answer was "no sweep result to apply — run a sweep
    # first", which is a lie: one HAD run, and its findings were on disk.
    _chron_result_load()
    """v1523 — ask THE BOARD to apply the sweep's gated names. The console never writes the grail.

    The ledger lives in the board (d2r_foundLog / d2r_setPieces) and the board's own
    window.chronicleApply routes through the same tick his hand uses — dated, merge-max, undoable.
    Reaching around it to write localStorage from here would create a second write path into his
    grail, which is a second thing that can drift from the first.

    Returns what the board reports: {applied: {uniques, sets, skipped}}. If the board window is not
    there, it says so — an apply that silently did nothing is the worst possible answer, because the
    proposal still looks unapplied and he will run it again.
    """
    st = chronicle_sweep_state()
    prop = proposal or (st.get("result") if isinstance(st.get("result"), dict) else None)
    if not prop:
        return {"ok": False, "why": "no sweep result to apply — run a sweep first"}
    # v1566 — a proposal whose ONLY content is completeSets is not empty. The guard bounced it and
    # the board never saw the one row worth five.
    _wa = prop.get("wouldAdd") or {}
    # v1759 — HELD NAMES TRAVEL TOO. This refused whenever the gate grounded nothing, which is the
    # COMMON case on a single scrolled panel: one page cannot reach two witnesses (cross-lane alone
    # is one), so a real sweep of his own film grounded 0 and held 5. Those five were then dropped
    # on the floor here — never sent, never queued, never seen. The board's inbox exists for exactly
    # these and was being fed nothing. Refuse only when there is genuinely NOTHING of either kind.
    _held = prop.get("held") or []
    if (not _wa.get("uniques") and not _wa.get("sets") and not _wa.get("completeSets")
            and not _held):
        return {"ok": False, "why": "the sweep found nothing at all — nothing to apply or queue"}
    w = globals().get("_MAIN_WIN")
    if w is None or not globals().get("_WINDOW_LIVE"):
        return {"ok": False, "why": "the board window is not open — open TV DIABLO and try again"}
    # v1923 — AND THE GAME GETS A VETO ON THE WAY OUT. Flagging a row in the panel and then writing
    # it anyway would make the whole counter-ledger decoration: the flag would say "you do not have
    # this" while the button put it on his board regardless. So the withholding happens HERE, on the
    # write path, which is the only place it cannot be bypassed by pressing register.
    #
    # ⚠ ONLY `denied` IS WITHHELD — never `undated`, never `superseded`. `denied` means the game's
    # own Remaining page was shot AFTER the sighting and still lists the piece as missing, which is
    # a genuine contradiction. `superseded` means he found it since, and `undated` means nobody
    # established the order. Withholding either of those would be the safeguard eating real finds on
    # evidence it does not have, which is a worse failure than the one it was built for.
    # [[stale-reading]] [[unknown-stays-unknown]]
    _wa_out = dict(_wa)
    _withheld = []
    try:
        import counter_ledger as _clg
        _sets_rows = list(_wa_out.get("sets") or [])
        _names = {}
        for _r in _sets_rows:
            _nm = _r.get("name") if isinstance(_r, dict) else _r
            if _nm:
                _names.setdefault(_nm, []).extend((_r.get("seen") or []) if isinstance(_r, dict) else [])
        _dn = _clg.denied(_names)
        _bad = {d["name"] for d in (_dn.get("denied") or [])}
        if _bad:
            _wa_out["sets"] = [r for r in _sets_rows
                               if (r.get("name") if isinstance(r, dict) else r) not in _bad]
            _withheld = sorted(_bad)
    except Exception:
        # A veto that cannot be computed must not silently become a veto that passed everything —
        # but it must not block the write either. It is reported, and _withheld stays empty.
        _withheld = []
    payload = json.dumps({"wouldAdd": _wa_out, "held": _held,
                          "lanes": prop.get("lanes") or []})
    js = ("(function(){try{if(typeof window.chronicleApply!=='function')return JSON.stringify("
          "{ok:false,why:'this board build has no chronicleApply (needs v1521+)'});"
          "var r=window.chronicleApply(%s);return JSON.stringify({ok:true,applied:r});}"
          "catch(e){return JSON.stringify({ok:false,why:String(e&&e.message||e)})}})()") % payload
    try:
        raw = _ejs(w, js, timeout=8.0)
    except Exception as e:
        return {"ok": False, "why": "the board refused the apply: %s" % str(e)[:160]}
    if not raw:
        # _ejs returns None on timeout — and a timeout is NOT a success. Saying so is the point:
        # the apply may or may not have landed, and he needs to look rather than be told it worked.
        return {"ok": False, "why": "the board did not answer in time — check the board before retrying"}
    try:
        out = json.loads(raw)
    except Exception:
        return {"ok": False, "why": "the board answered something unreadable"}
    if _withheld and isinstance(out, dict):
        out["withheld"] = _withheld
        out["withheldWhy"] = (
            "%d set piece(s) were NOT written because the game's own Remaining page — shot after "
            "they were seen — still lists them as missing: %s. Nothing about them was lost; record "
            "another Remaining page after you find one and it will stop being denied."
            % (len(_withheld), ", ".join(_withheld)))
    return out


def board_ownership(sample=0):
    """ASK THE BOARD WHAT HE OWNS. The read direction of the channel that already applies.

    Konyo, 2026-08-20, on being told the vault cross-reference needed him to paste a console dump:
    "i neeed to do this in my website browser and not locally on the console? why?" — and then
    "yea try to fix this :)".

    The answer to "why" was real but it was a LIMITATION, not a law. His grail and vault ledgers
    live in localStorage inside bible.html; `vault_ledger_load()` returns 0 entries on disk, because
    the console has never held them. chronicle_apply already reaches into the board window to WRITE
    a tick (v1523: "the console never writes the grail" — it asks the board, which owns it). Only
    the read direction was missing, so answering a question about his own ledger required him to
    copy it out by hand.

    Same window, same evaluator, same refusals — including the one that matters: a TIMEOUT IS NOT AN
    EMPTY LEDGER. If the board does not answer, this says so rather than reporting that he owns
    nothing, because "he has none" and "nobody asked" must never read the same.
    [[unknown-stays-unknown]]

    `sample` returns that many names per store for eyeballing; 0 returns counts only, which is what
    a cross-reference needs and keeps a 300-name payload out of the log.
    """
    w = globals().get("_MAIN_WIN")
    if w is None or not globals().get("_WINDOW_LIVE"):
        return {"ok": False, "why": "the board window is not open — open TV DIABLO and try again"}
    js = ("(function(){try{"
          "var g=function(k){try{var v=(window.LSR?window.LSR.getItem(k):localStorage.getItem(k));"
          "var p=v?JSON.parse(v):null;"
          "if(Array.isArray(p))return p.slice();"
          "if(p&&typeof p==='object')return Object.keys(p);return [];}catch(e){return [];}};"
          "var fl=g('d2r_foundLog'),ow=g('d2r_owned'),sp=g('d2r_setPieces');"
          "var n=%d;"
          "return JSON.stringify({ok:true,counts:{foundLog:fl.length,owned:ow.length,setPieces:sp.length},"
          "sample:{foundLog:fl.slice(0,n),owned:ow.slice(0,n),setPieces:sp.slice(0,n)}});"
          "}catch(e){return JSON.stringify({ok:false,why:String(e&&e.message||e)})}})()") % int(sample or 0)
    try:
        raw = _ejs(w, js, timeout=8.0)
    except Exception as e:
        return {"ok": False, "why": "the board refused the read: %s" % str(e)[:160]}
    if not raw:
        return {"ok": False, "why": "the board did not answer in time — its ledger is UNREAD, "
                                    "which is not the same as empty"}
    try:
        return json.loads(raw)
    except Exception:
        return {"ok": False, "why": "the board answered something unreadable"}


_CHRON_LAST_PROPOSAL = None


def chronicle_regate(conf_floor=None, min_witnesses=None):
    """v1531 — re-run the GATE over the last sweep's evidence at different thresholds. Costs nothing.

    tv/CHRONICLE_ARC.md names this as an open gap in its own words: CONF_FLOOR and MIN_WITNESSES are
    "reasoned, not measured". They cannot be measured without seeing what they actually do to real
    evidence, and that was impossible while tuning them meant paying for the whole sweep again.

    Returns what WOULD ground and what WOULD be held at the asked-for thresholds, beside the current
    ones, so the difference is the answer rather than an opinion about it.
    """
    import chronicle_retro as _cr
    prop = globals().get("_CHRON_LAST_PROPOSAL")
    if not prop:
        return {"ok": False, "why": "no sweep evidence in memory — run a sweep first"}
    try:
        floor = float(conf_floor) if conf_floor is not None else _cr.CONF_FLOOR
        wits = int(min_witnesses) if min_witnesses is not None else _cr.MIN_WITNESSES
    except (TypeError, ValueError):
        return {"ok": False, "why": "thresholds must be numbers"}
    floor = max(0.0, min(1.0, floor))
    wits = max(1, min(4, wits))

    # v1789 — tune against the SAME input the live gate sees. Re-gating raw names while the
    # real path gates folded ones would answer a question he never asked, and the preview
    # would disagree with what actually happens when he lowers the threshold.
    _tune_prop, _ = _chron_fold(prop)

    def run(f, w):
        g = _cr.strict_gate(conf_floor=f, min_witnesses=w)
        out = _cr.apply_proposal(_tune_prop, {"uniques": [], "sets": []}, gate=g)
        return {"uniques": out["uniques"]["added"], "sets": out["sets"]["added"],
                "held": len(out["held"])}
    now = run(_cr.CONF_FLOOR, _cr.MIN_WITNESSES)
    asked = run(floor, wits)
    cur_names = set(now["uniques"]) | set(now["sets"])
    ask_names = set(asked["uniques"]) | set(asked["sets"])
    return {
        "ok": True,
        "current": {"confFloor": _cr.CONF_FLOOR, "minWitnesses": _cr.MIN_WITNESSES,
                    "grounded": len(cur_names), "held": now["held"]},
        "asked": {"confFloor": floor, "minWitnesses": wits,
                  "grounded": len(ask_names), "held": asked["held"]},
        # the two lists that answer the question — what loosening would let in, what tightening
        # would keep out. Named, not counted: a count cannot be argued with.
        "wouldGainNames": sorted(ask_names - cur_names),
        "wouldLoseNames": sorted(cur_names - ask_names),
        "spent": 0,
    }


def reader_health():
    """v1537 — 🔍 WHY DIDN'T IT READ MY STASH, as a route.

    v1536 built the audit as a CLI, and a CLI is the wrong shape for the person who needs it most:
    his cousin is on a Windows box he may never open a terminal on, and Konyo has to relay the
    output by hand. The console is already open in front of both of them.

    Read-only, costs nothing, and it reads THIS machine's journal — which is the machine whose
    reading is in question.
    """
    try:
        import live_miss_audit as lma
    except Exception as e:
        return {"ok": False, "why": "the audit module is unavailable: %s" % str(e)[:100]}
    # v1493's invariant, and its guard caught me writing a second one: EXACTLY ONE site may build
    # the journal path. My "safe" fallback was a hole in TV_SESSIONS isolation — a test pointing the
    # journal elsewhere would have had this route read the real one behind its back.
    path = _journal_path()
    rows = lma.load(path)
    if rows is None:
        return {"ok": False, "why": "could not read this machine's journal at %s" % path}
    res = lma.audit(rows)
    findings = [{"session": a, "tab": b, "verdict": c, "detail": d, "fix": lma._fix_for(c)}
                for a, b, c, d in res["findings"]]
    broken = [f for f in findings if f["verdict"] != lma.E_OK]
    # ★ "no findings" is NOT "everything works" — it is "nothing to judge". Saying the first when
    # you mean the second is how a health panel earns trust it has not got.
    # v1538 — HOW THIS MACHINE IS CROPPING. REG-086 was invisible for as long as it was because
    # nothing ever said which branch a frame took. Konyo asked whether running it on his Windows PC
    # would be enough of a test — it is, but only if the answer is visible, and this is that answer.
    crop = None
    try:
        import stash_eye as _se
        d = _se.last_crop_decision()
        if d.get("aspect"):
            branch = d["branch"]
            crop = {
                "aspect": d["aspect"],
                "branch": branch,
                "size": d.get("size"),
                "says": {
                    "locked-mac": "the LOCKED band measured on Konyo's own film — the calibrated path",
                    "derived": "a band DERIVED for this aspect (v1536). This is the path that was "
                               "broken before REG-086; if the tally below worked, the fix is proven "
                               "on real footage.",
                    "slab-46pct": "⚠ the coarse 46%-of-screen fallback — 5x more diluted than the "
                                  "calibrated band. This is REG-086 still happening.",
                    "no-band-windowed": "no band: the game is not fullscreen, so the panel is not "
                                        "where any calibration expects it. Play fullscreen.",
                }.get(branch, branch),
            }
    except Exception:
        crop = None
    return {
        "ok": True,
        "sessions": res["sessions"],
        "crop": crop,
        "findings": findings,
        "broken": len(broken),
        "verdict": ("nothing to judge — no stash activity in this journal" if not findings
                    else "every tally tab that was opened got a real total" if not broken
                    else "%d broken link(s)" % len(broken)),
        "spent": 0,
    }


def chronicle_visits(limit=8):
    """v1522 — the Chronicle panels he has opened IN GAME, newest first.

    The live agent journals a `chronicle/visit` row when a visit ends (recording is free). This turns
    those rows into an OFFER — "📜 14 frames of the Holy Grail ledger, captured 6 minutes ago" — which
    the console can price and read on demand. Nothing here reads a page or spends anything.
    """
    out = []
    try:
        rows = _kai_journal_rows()
    except Exception:
        rows = []
    for r in reversed(rows or []):
        if r.get("lane") != "chronicle" or r.get("kind") != "visit":
            continue
        out.append({
            "ts": int(r.get("ts") or 0),
            "ledger": r.get("ledger") or "",
            "n": int(r.get("n") or 0),
            "frames": (r.get("frames") or [])[:120],
            # named the way he would say it; "" stays honest rather than picking a ledger
            "label": ("🏆 Holy Grail" if r.get("ledger") == "uniques"
                      else "🧩 Set pieces" if r.get("ledger") == "sets"
                      else "📜 ledger unread"),
        })
        if len(out) >= limit:
            break
    return {"ok": True, "visits": out, "spent": 0}


def chronicle_offer(limit=8):
    """v1820 — EVERYTHING WAITING TO BE READ, in one list, spending nothing.

    Konyo, after recording three Chronicle sessions: "still not changed the sets or the uniques
    number.. ill do another session it should definitely be able to read and tally them". A fourth
    would have changed nothing either, and no screen could have told him why.

    A `chronicle/visit` row is journaled by the LIVE agent watching him open the panel. A MINI
    capture with a CHOSEN chronicle focus produces no such row — it produces a REEL whose index
    says focus=chronicle-uniques/sets with focusChosen true, which is a STRONGER declaration than a
    visit because he picked it himself and nothing was inferred. The reel auto-sweep already knew
    how to read exactly those; the console's offer did not, so three correctly-labelled reels sat on
    disk invisible to every screen while the only thing that would ever read them was a daemon
    inside a console that happened to be closed.

    Kept SEPARATE from chronicle_visits() on purpose: that function is a pure reading of the
    journal, three guards depend on it staying that way, and merging disk state into it made an
    unrelated journal-failure test depend on whatever footage was lying in his frames directory.
    Visits come first — v1762 gives them the cheaper, more targeted job.
    """
    base = chronicle_visits(limit=limit)
    out = list(base.get("visits") or [])
    try:
        seen_ts = {v.get("ts") for v in out}
        for r in _unswept_chron_reels(limit=max(0, limit - len(out))):
            if r["ts"] in seen_ts:
                continue
            out.append(r)
    except Exception:
        pass
    return {"ok": True, "visits": out, "spent": 0}


def _unswept_chron_reels(limit=8):
    """Reels captured with a CHOSEN chronicle focus that no sweep has read yet, newest first.

    Pure and free: a directory listing and each reel's own index.json. It reads no page, spends
    nothing, and deliberately reports only what the reel ITSELF declares — a mini capture focused
    on the stash or the runes returns None from _declared_kind and never appears here.
    """
    out = []
    if limit <= 0:
        return out
    hist = os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")
    try:
        import chronicle_retro as _cr
        dirs = _cr.reel_dirs(hist, newest_first=True) or []
    except Exception:
        return out
    seen = _chron_reels_seen()
    for d in dirs:
        rid = os.path.basename(str(d))
        if rid in seen:
            continue
        try:
            with open(os.path.join(str(d), "index.json"), encoding="utf-8") as fh:
                idx = json.load(fh) or {}
        except Exception:
            continue
        kind = _cr._declared_kind(idx)
        if not kind:
            continue
        ledger = "uniques" if kind == "chronicle-uniques" else "sets"
        try:
            ts = int(str(rid).split("_")[2])
        except Exception:
            ts = 0
        out.append({
            "ts": ts,
            "ledger": ledger,
            "n": int(idx.get("n") or 0),
            "frames": [],
            "reel": rid,          # what the sweep needs to read it: chronicle_sweep_start(reel_id=)
            "source": "reel",     # visits carry no source; the console can tell them apart
            "label": ("🏆 Holy Grail" if ledger == "uniques" else "🧩 Set pieces"),
        })
        if len(out) >= limit:
            break
    return out


# ── v1745 📜🐕 CHRONICLE AUTO-READ — the watchdog, scoped to where reading is FREE ──────────
# Konyo: "where is the coded AI reader that retro analyzes this within the console like a
# watchdog.. i want it automatically synced."
#
# There was none, and that was deliberate: chron_visit_flush's own docstring sets the doctrine —
# "recording is FREE, reading is OFFERED. This journals the visit and says so; it never calls
# claude_chronicle_read / g5_chronicle_read and never spends a classify." chronicle_sweep_start was
# reachable only from the HTTP endpoint, so a session could end with a perfectly good Chronicle
# recording sitting there and nothing would ever look at it.
#
# THE HOLE IN THAT REASONING, AND THE ONLY PLACE THIS FIRES. "Offered, not automatic" is a COST
# argument. It stops being one when the read is free — and v1528 says exactly when that is: a visit
# whose LEDGER is already known is "the cheapest read in the system: he already told us these frames
# are the Chronicle and which ledger was open, so there is no classify stage to pay for." So this
# reads ONLY visits that carry a ledger. A visit without one is left alone, untouched and still
# offered, because sweeping it would have to GUESS which ledger — and a wrong guess writes set
# pieces into his grail (v1528's own words).
#
# Measured on session s_1786922954749_12579: the visit was journalled with ledger='uniques' and 4
# frames, its five deep reads named 13 discovered uniques, and nothing read it. His count sat at
# 249/403 while the evidence to move it was on disk.
#
# WHAT IT DOES NOT DO: it does not APPLY. The sweep produces a PROPOSAL, and the review gate stays
# where v947 put it. Automatic reading, human-gated writing.
# v1902 — THE HIST DECIDES, NOT THE FIXTURE'S MEMORY. These three isolated only when a test
# remembered their own env var, while the swept memo and the reads memo have derived from
# TV_HIST for versions and the vault's three now do too. A rule that half the files follow is
# a rule nobody can rely on: the env override still wins where a test wants a specific file,
# but forgetting it can no longer point a fixture at his real tree.
_CHRON_AUTOREAD_PATH = (os.environ.get("TV_CHRON_AUTOREAD")
                        or os.path.join(_fixture_root_for_state(), "chron_autoread.json"))
_CHRON_AUTOREAD_EVERY_S = 20
_CHRON_AUTOREAD = {"done": None, "reels": None, "lastTs": 0, "reads": 0, "skipped": {}, "tries": {}}
# v1745.1 — Konyo: "i dont want it looping though the same video over and over.. it might loop and
# waste?" He is right, and about the one path that was open. A SUCCESSFUL read is already read-once:
# the visit ts is persisted and never revisited. But a REFUSED sweep marked nothing, so the same
# visit would be retried every 20s for as long as the console ran. Two attempts, then it is retired
# with the reason kept — a third identical refusal teaches nothing and costs the same as the first.
_CHRON_AUTOREAD_MAX_TRIES = 2


def _chron_autoread_done():
    """The visit timestamps already auto-read. Persisted, so a console restart does not re-read a
    visit it has already spent time on. Missing file = nothing read yet, never an error."""
    if _CHRON_AUTOREAD["done"] is None:
        seen = set()
        try:
            with open(_CHRON_AUTOREAD_PATH, encoding="utf-8") as fh:
                seen = set(int(x) for x in (json.load(fh) or {}).get("done") or [])
        except Exception:
            seen = set()
        _CHRON_AUTOREAD["done"] = seen
    return _CHRON_AUTOREAD["done"]


def _chron_autoread_save():
    """THE ONE WRITER of chron_autoread.json — every key, every time.

    v1900 — there were TWO, and this file has already been un-marked TWICE by that fact. v1762: the
    visit writer knew only "done" and wiped "reels", so the watchdog re-walked the whole backlog and
    PAID FOR IT AGAIN. v1784: the same shape again with "skipped", so a reel retired for a named
    reason came back as never-swept. Both were fixed by teaching a writer about a key — which leaves
    the next key to be added exactly as fragile, and the third occurrence of one class is where you
    stop fixing instances. There is one writer now; a new key is added here and both marks get it.

    It MAKES ITS PARENT and it SAYS SO WHEN IT CANNOT (v1899's lesson, one ship earlier): losing
    these marks is not cosmetic, it is re-reading reels that have already been paid for.
    """
    payload = {"done": sorted(_chron_autoread_done()),
               "reels": sorted(_chron_reels_seen()),
               "skipped": dict(_CHRON_AUTOREAD.get("skipped") or {})}
    try:
        try:
            os.makedirs(os.path.dirname(_CHRON_AUTOREAD_PATH) or ".", exist_ok=True)
        except Exception:
            pass
        tmp = _CHRON_AUTOREAD_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        os.replace(tmp, _CHRON_AUTOREAD_PATH)
        return True
    except Exception as e:
        print("   \u26a0 auto-read marks NOT persisted (%s) — reels already read may be swept again"
              % str(e)[:140])
        return False


def _chron_autoread_mark(ts):
    done = _chron_autoread_done()
    done.add(int(ts))
    _chron_autoread_save()

def chronicle_autoread_tick():
    """One pass. Returns what it did, so a silent skip is impossible to mistake for a clean run —
    every refusal carries a NAMED reason (v1543's lesson: a silent skip turns a fault into a smaller
    invoice and nothing else)."""
    if _agent_alive():
        return {"ok": False, "why": "a session is live — a visit is only final once the reel stops growing"}
    try:
        if chronicle_sweep_state().get("running"):
            return {"ok": False, "why": "a sweep is already running"}
    except Exception:
        pass
    try:
        visits = (chronicle_visits(limit=12) or {}).get("visits") or []
    except Exception as e:
        return {"ok": False, "why": "could not read visits: %s" % e}
    done = _chron_autoread_done()
    for v in visits:                      # newest first
        # v1820 — belt and braces. chronicle_visits() is journal-only by design, so a reel cannot
        # reach here; the OFFER that merges reels for the console is chronicle_offer(). If anyone
        # ever points this loop at the merged list, a reel handed to the VISIT runner would look up
        # a journal row that does not exist, fail, spend one of that reel's two tries and retire
        # footage the reel tick would have read correctly. One line to make that impossible.
        if v.get("source") == "reel":
            continue
        ts = int(v.get("ts") or 0)
        if not ts or ts in done:
            continue
        if not v.get("ledger"):
            # NEVER guess a ledger. Counted so "nothing happened" and "we refused" stay different.
            _CHRON_AUTOREAD["skipped"][str(ts)] = "no ledger — offered, never guessed"
            continue
        # v1766 — COUNT THE ATTEMPT BEFORE MAKING IT, and count EVERY attempt. v1745 fixed half of
        # this: a sweep that REFUSED no longer burned the visit. The other half stayed open and its
        # own note said so — "a tick run from a throwaway process started a sweep, the process
        # exited, and the visit was left flagged read with nothing to show for it". That is a sweep
        # that TOOK the job and died, and the mark below used to fire the moment it started, because
        # chronicle_sweep_start spawns a thread and returns immediately. Same defect as the reel
        # path, same fix: the runner marks the visit once its result is durable. The counter now
        # covers deaths as well as refusals, so neither can retry without bound.
        tries = _CHRON_AUTOREAD["tries"].get(str(ts), 0) + 1
        if tries > _CHRON_AUTOREAD_MAX_TRIES:
            _chron_autoread_mark(ts)
            _CHRON_AUTOREAD["skipped"][str(ts)] = ("gave up after %d tries — the sweep started but "
                                                   "never wrote a result" % (tries - 1))
            return {"ok": False, "retired": ts, "tries": tries - 1,
                    "why": "the sweep started but never wrote a result"}
        _CHRON_AUTOREAD["tries"][str(ts)] = tries
        r = chronicle_sweep_start(visit=ts)
        if not (isinstance(r, dict) and r.get("ok")):
            why = (isinstance(r, dict) and r.get("why")) or str(r)
            if tries >= _CHRON_AUTOREAD_MAX_TRIES:
                # RETIRE it, with the reason kept. Not silently: a visit that stopped being tried
                # must be distinguishable from one that was never tried.
                _chron_autoread_mark(ts)
                _CHRON_AUTOREAD["skipped"][str(ts)] = "gave up after %d tries — %s" % (tries, why)
                return {"ok": False, "retired": ts, "tries": tries, "why": why}
            return {"ok": False, "why": "sweep refused the visit (try %d/%d): %s"
                                        % (tries, _CHRON_AUTOREAD_MAX_TRIES, why)}
        # the visit is marked by _chron_visit_run once its result is on disk — never here, where
        # the sweep has only just been handed the job
        _CHRON_AUTOREAD["reads"] += 1
        _CHRON_AUTOREAD["lastTs"] = ts
        return {"ok": True, "read": ts, "ledger": v.get("ledger"), "frames": v.get("n"), "start": r}
    return {"ok": True, "read": None, "why": "no unread visit with a known ledger"}


# v1762 — THE REELS SWEEP THEMSELVES TOO, and this is the half that hid his best footage.
#
# A VISIT is what the live agent journalled while it noticed him in the Chronicle. A REEL is the
# whole recording of that session. Measured on his own film: the Aug 17 visit named FOUR frames,
# while the reel of the same session holds FIFTY-FIVE distinct screens. Every sweep aimed at the
# visit read the 4-frame slice and reported the session as holding nothing, and the 55 screens sat
# unread because nothing swept a reel unless a human pressed a button. He asked the obvious
# question — "i dont understand why the current session there cant be just like analyzed and swept"
# — and the answer was that the automatic half only ever looked at the smaller object.
#
# SCOPED SO IT CANNOT SURPRISE HIM WITH A BILL, because a reel is 20-75 classifies where a visit is
# a handful:
#   * NEW reels only. Everything on disk today was swept once, deliberately, on his say-so; the
#     watchdog starts from that line and never re-walks the backlog.
#   * ONE reel per tick, newest first. A queue that drains slowly is auditable; one that drains at
#     once is an invoice.
#   * Never while a session is live or a sweep is running — the same two refusals the visit path
#     already makes, for the same reason: a growing reel is not a finished one.
#   * Off in one line: TV_CHRON_AUTOREEL=0.
_CHRON_AUTOREEL_ON = os.environ.get("TV_CHRON_AUTOREEL", "1") != "0"


def _chron_reels_seen():
    """Reel ids already swept, persisted beside the visit marks in the same file."""
    if _CHRON_AUTOREAD.get("reels") is None:
        seen = set()
        try:
            with open(_CHRON_AUTOREAD_PATH, encoding="utf-8") as fh:
                seen = set(str(x) for x in (json.load(fh) or {}).get("reels") or [])
        except Exception:
            seen = set()
        _CHRON_AUTOREAD["reels"] = seen
    return _CHRON_AUTOREAD["reels"]


def _chron_reels_mark(reel_id):
    seen = _chron_reels_seen()
    seen.add(str(reel_id))
    _chron_autoread_save()

def _reel_is_growing(reel_dir, quiet_s=90):
    """Is this reel STILL BEING WRITTEN? Measured, not inferred from whether a session exists.

    v1823 — Konyo: "why refused when session is LIVE?" He was right to ask. Both watchdog ticks
    opened with a blanket `if _agent_alive(): refuse`, and the reason given was "a reel is only
    final once it stops growing" — true of the reel being recorded RIGHT NOW, false of every sealed
    reel behind it. He plays with the console capturing, so a session was live almost whenever he
    was at the machine: the sweeper never got a window, and three finished reels sat unread for
    hours while the guard did exactly what it said on the tin.

    The guard was checking the wrong thing. "A session exists" is a proxy; "this directory is still
    receiving frames" is the fact. The refusal therefore moves from the whole tick down to the
    individual reel, and only the one actually growing is skipped.

    Unreadable answers GROWING on purpose: a reel we cannot judge must never be swept, because
    reading a half-written reel spends money on footage that is about to change.
    """
    try:
        newest = os.path.getmtime(reel_dir)
        for n in os.listdir(reel_dir):
            if n.startswith("f_") and n.endswith(".jpg"):
                m = os.path.getmtime(os.path.join(reel_dir, n))
                if m > newest:
                    newest = m
        return (time.time() - newest) < quiet_s
    except Exception:
        return True


def chronicle_autoreel_tick():
    """One pass over the REELS. Returns what it did, and every refusal carries a named reason."""
    if not _CHRON_AUTOREEL_ON:
        return {"ok": False, "why": "reel auto-sweep is off (TV_CHRON_AUTOREEL=0)"}
    # v1823 — NO BLANKET REFUSAL WHILE A SESSION IS LIVE. A live session says nothing about the
    # SEALED reels behind it, and refusing on it meant the sweeper never ran while he was at the
    # machine. The one reel it genuinely protects is skipped individually below.
    try:
        if chronicle_sweep_state().get("running"):
            return {"ok": False, "why": "a sweep is already running"}
    except Exception:
        pass
    hist = os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")
    try:
        import chronicle_retro as _cr
        dirs = _cr.reel_dirs(hist, newest_first=True) or []
    except Exception as e:
        return {"ok": False, "why": "could not list reels: %s" % e}
    seen = _chron_reels_seen()
    for d in dirs:
        rid = os.path.basename(str(d))
        if rid in seen:
            continue
        # the ONE reel a live session actually protects: the one still receiving frames
        if _reel_is_growing(str(d)):
            _CHRON_AUTOREAD["skipped"][rid] = "still growing — not final yet"
            continue
        # MARK BEFORE READING is wrong here for the same reason it was wrong for visits (v1745):
        # a refused sweep would burn the reel. Mark only once the sweep has taken the job.
        # v1766.1 — A RETRY MUST BE BOUNDED OR IT IS A RUNAWAY. Not marking the reel until its
        # result is durable is right, but on its own it means a sweep that ALWAYS dies gets
        # restarted on every single tick, spending a sweep each time and never finishing. This
        # class is called TestReelAutoSweepCannotSurpriseHim and its charter is that the automation
        # must be "provably incapable of running away, not merely intended not to" — an unbounded
        # retry is exactly the runaway it forbids, arrived at while fixing the opposite fault.
        # So: attempts are counted, and after _CHRON_AUTOREAD_MAX_TRIES the reel is RETIRED with
        # its reason kept. Retired is not the same as swept — it is on the record, and it stops.
        tries = _CHRON_AUTOREAD["tries"].get(rid, 0) + 1
        if tries > _CHRON_AUTOREAD_MAX_TRIES:
            _chron_reels_mark(rid)
            _CHRON_AUTOREAD["skipped"][rid] = ("gave up after %d attempts — the sweep started but "
                                               "never wrote a result" % (tries - 1))
            return {"ok": False, "retired": rid, "tries": tries - 1,
                    "why": "the sweep started but never wrote a result, %d times" % (tries - 1)}
        _CHRON_AUTOREAD["tries"][rid] = tries
        r = chronicle_sweep_start(limit=1, reel_id=rid)
        if not (isinstance(r, dict) and r.get("ok")):
            return {"ok": False, "why": "sweep refused the reel: %s"
                                        % ((isinstance(r, dict) and r.get("why")) or r)}
        # v1763 — DO NOT BURN A REEL WHOSE FINDINGS WERE NOT KEPT. The swept marker is durable and
        # the result used to be memory-only, so a sweep could spend, find names, lose them on the
        # next restart, and then decline to read that reel ever again because it was "done". The
        # marker now waits for the result to exist on disk; if it does not, the reel stays unswept
        # and will be tried again, which costs a re-read at worst and loses nothing at best.
        # the sweep marks it once its result is on disk — see _chron_sweep_run. Marking here
        # would burn the reel at START, which is what this comment used to describe and not do.
        return {"ok": True, "swept": rid, "start": r}
    return {"ok": True, "idle": True, "why": "no unswept reel"}


def _chron_autoread_loop():
    while True:
        try:
            time.sleep(_CHRON_AUTOREAD_EVERY_S)
            v = chronicle_autoread_tick()
            # v1762 — a VISIT is cheaper and more targeted, so it always wins the tick. Only when
            # there is no visit left to read does the watchdog look at the bigger object.
            if not (isinstance(v, dict) and v.get("ok") and v.get("read")):
                try:
                    chronicle_autoreel_tick()
                except Exception:
                    pass
        except Exception:
            pass


_CHRON_QUOTE = {"sig": None, "res": None}


def chronicle_scan_cost(hist_dir=None, limit=None, reel_id=None):
    """v1956 — MEMOISED, for the same reason and by the same key as the vault quote.

    MEASURED on his own film: this takes **316 SECONDS** — five and a half minutes — behind a button
    whose label never changes and whose fetch has no timeout. That is the identical defect v1941
    fixed one panel over, and finding it here is only the class sweep the vault one earned: two
    "price it" buttons, two silent five-minute waits, one of them fixed.

    The shape differs in a way worth writing down. The VAULT quote was slow because its probe ran a
    crop+OCR per frame, so memoising the GATE fixed most of it. This probe returns a constant and
    costs nothing — the time is the sweep machinery walking his reels — so a gate cache would buy
    nothing here and only the ANSWER is worth keeping. Same symptom, different cause; the fix that
    worked there is not automatically the fix that works here.

    Keyed on the sealed-reel set, so a new reel re-prices and an unchanged one answers instantly.
    """
    _hist = hist_dir or os.environ.get("TV_HIST") or HIST_DIR
    _sig = None if reel_id else _hist_signature(_hist)     # a single-reel quote is not the same question
    if _sig is not None and _CHRON_QUOTE["sig"] == _sig and _CHRON_QUOTE["res"] is not None:
        _out = dict(_CHRON_QUOTE["res"])
        _out["cached"] = True
        return _out
    _res = _chronicle_scan_cost_inner(hist_dir, limit, reel_id)
    if _sig is not None and isinstance(_res, dict) and _res.get("ok") is not False:
        _CHRON_QUOTE["sig"] = _sig
        _CHRON_QUOTE["res"] = _res
    return _res


def _chronicle_scan_cost_inner(hist_dir=None, limit=None, reel_id=None):
    """v1516 — what a Chronicle retro sweep would cost, computed on HIS film. No model calls.

    Konyo has been told "97% cheaper" — this is the route that lets him verify it instead of
    believing it. It returns the per-reel grouping and the totals, and it cannot spend anything:
    both lanes are local stubs, so no model is ever reached.

    v1596 — THE QUOTE USED TO UNDER-CHARGE ITSELF, and by a lot. The probe returned None, which is
    "not a Chronicle page"; read_reel then SKIPS the read stage for that run. So the free pass
    counted classify calls and literally could not count a single page read — the second and larger
    half of a real sweep's bill. On a two-reel fixture it quoted 2 calls against an actual 6, hiding
    67% of the spend, and told him "83% cheaper" where the truth was 50%.

    THE FIX IS TO PRICE THE WORST CASE, not to add a second copy of the walk. The probe now answers
    a real kind, so the SAME read_reel code path runs the read stage and counts pages for us. That
    makes the number an UPPER BOUND — it prices every candidate run as though it were a readable
    Chronicle page, and a real sweep will classify some of them as a lobby or a stash and read
    nothing. That asymmetry is deliberate and is the only safe direction for a cost quote: quoting
    high costs him a sweep he could have afforded, quoting low spends money he did not agree to.
    """
    try:
        import chronicle_retro as _cr
    except Exception as e:
        return {"ok": False, "why": "chronicle_retro unavailable: %s" % e}
    hist = hist_dir or os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")
    if not os.path.isdir(hist):
        return {"ok": True, "reels": [], "totals": {"reels": 0, "framesSeen": 0, "classified": 0},
                "note": "no sealed reels yet"}
    # v1551 — REMEMBER WHICH FRAMES, not just how many. The classify stub is already called once per
    # candidate run; recording the path costs nothing and turns "11 classifies" into eleven frames he
    # can open. The CLI has printed this since v1541 and the console — the surface he actually uses,
    # and the only one his Windows PC will ever show him — did not.
    picked = []

    def _probe(path):
        picked.append(path)
        # a REAL kind, so the read stage runs and its pages get counted. Costs nothing: the page
        # lane below is a local stub too.
        return "chronicle-uniques"

    # {} is a dict with no "note", which proposal_from_pages counts as a page read and folds in as
    # zero found names — exactly the accounting we want, and zero model calls.
    # v1821 — SAY THAT NOBODY READ ANYTHING. This pass installs a stub read_page that returns {}
    # by construction, so "no names" is guaranteed and means nothing. Without priced_only the
    # verdict landed on `read-nothing` — "N Chronicle pages WERE read and produced no names. This
    # one is the reading itself, not the footage." — which is a confident accusation against his
    # reader, printed on the exact screen he opens to decide whether a sweep is worth paying for.
    # sweep_verdict has had the `not-measured` state for this since v1541 and the CLI has always
    # passed the flag; only this caller, the one HE actually looks at, did not.
    # v1834 — PRICE THE REEL HE NAMED. `limit` slices reel_dirs newest-first, so pricing a reel by
    # name was impossible: `--reel <an old reel>` printed the cost of the NEWEST one instead. On his
    # hist that read "21 page read(s)" for a 483-frame reel whose real count is ~440 — a true number
    # under a word naming a different quantity, printed on the line he uses to decide whether to
    # spend. Same narrowing the sweep itself uses (skip everything else), and skip is applied before
    # the slice, so the target is reached wherever it sits in the ordering. [[label-outlived-referent]]
    _skip = None
    if reel_id:
        try:
            _skip = {os.path.basename(str(d)) for d in _cr.reel_dirs(hist)} - {str(reel_id)}
        except Exception:
            _skip = None
    res = _cr.sweep_hist(hist, classify=_probe, read_page=lambda p, k: {}, limit=limit,
                         skip_reels=_skip, priced_only=True)
    t = res["totals"]
    seen = t.get("framesSeen") or 0
    classifies = t.get("classified") or 0
    pages = t.get("pagesRead") or 0
    calls = classifies + pages            # ★ BOTH lanes. A sweep pays for the read, not just the look.
    return {
        "ok": True,
        "reels": res["reels"],
        "totals": t,
        # stated as a fraction of frames, which is the only honest denominator: reading every frame
        # is the thing this replaces
        "savedPct": round(100.0 * (1 - (calls / seen)), 1) if seen else 0.0,
        "wouldRead": calls,
        # the breakdown, because one number he cannot take apart is one he has to take on faith
        "wouldClassify": classifies,
        "wouldReadPages": pages,
        "upperBound": True,
        "boundWhy": "prices every candidate run as a readable page; a real sweep classifies some as "
                    "lobby/stash and reads nothing for them, so the true bill lands at or under this",
        "insteadOf": seen,
        "spent": 0,          # ★ said out loud: this route cannot cost anything
        # the same two things the CLI prints: WHICH frames, and WHY the answer is what it is
        "frames": [os.path.relpath(p, hist) for p in picked[:40]],
        "verdict": res.get("verdict"),
    }


# ── v1519 THE REAL SWEEP ────────────────────────────────────────────────────────
# A real sweep is minutes, not milliseconds — 11 classifies plus the pages, each a subscription read.
# So it is a background JOB with progress, never a blocking route: a request that hangs for four
# minutes is one he kills, and a sweep he kills halfway is one he never trusts again.
#
# It STILL WRITES NOTHING. The engine's read-only law holds all the way out to the route: this
# produces a proposal and the gate's verdicts, and the apply step is a separate decision he makes.
_CHRON_JOB = {"running": False, "startedTs": 0, "phase": "idle", "reelsDone": 0, "reelsTotal": 0,
              "classified": 0, "pagesRead": 0, "result": None, "error": None, "lanes": []}
_CHRON_LOCK = threading.Lock()


# v1524 — THE SWEEP'S MEMORY. The engine may never write (that is its first law), so the record of
# what has already been read lives out here, with the rest of the console's state. A sealed reel never
# changes: re-reading one buys nothing and costs a subscription read per still-run.
_CHRON_SWEPT_PATH = os.path.join(HERE, "chronicle_swept.json")
# v1835 — how many pages a sweep may hold in memory before banking them. 20 is ~45 minutes of
# reading at his measured two-lane rate, so a death costs under an hour rather than the whole run.
_CHRON_CKPT_PAGES = int(os.environ.get("TV_CHRON_CKPT") or 20)


def _chron_swept_path():
    """v1858 — the LAST of the five live-state files to get an isolation override.

    Four already had one (TV_CHRON_EVIDENCE, TV_CHRON_RESULT, TV_SWEEP_LOCK, TV_CHRON_READS) and
    this one did not — and it is the file that decides whether a reel is ever re-read. Anything but
    a unittest (a probe, an integration run, a one-off script) therefore wrote his REAL memory of
    what has been swept, and marking a throwaway reel swept in his live ledger is the same class of
    damage v1832 fixed for the lock and v1855 for the tracked files.

    Falls back to the module GLOBAL rather than a literal path, deliberately: the sweep tests patch
    `_CHRON_SWEPT_PATH` with mock.patch.object and must keep working exactly as they do.
    """
    # PRECEDENCE: EXPLICIT BEATS AMBIENT. The first cut put TV_HIST above the module global and
    # broke a sweep test that patches the global AND sets TV_HIST to the same tmpdir — it wrote
    # chronicle_swept.json where the test was reading swept.json. Naming a path outright (an env
    # var, or mock.patch.object on the global) is a deliberate instruction; TV_HIST is a statement
    # about the FOOTAGE that only implies where state should live. The deliberate one wins.
    env = os.environ.get("TV_CHRON_SWEPT")
    if env:
        return env
    _default = os.path.join(HERE, "chronicle_swept.json")
    if _CHRON_SWEPT_PATH != _default:
        return _CHRON_SWEPT_PATH          # patched on purpose — honour it
    hist = os.environ.get("TV_HIST")
    if hist:
        return os.path.join(hist, "chronicle_swept.json")
    return _CHRON_SWEPT_PATH


def _chron_swept_load():
    try:
        with open(_chron_swept_path(), encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _chron_swept_save(rec):
    """Torn-write safe, same as every other persisted file here (v1209): a crash mid-write would
    leave a truncated JSON that reads as 'nothing was ever swept' and re-pays for the whole hist."""
    try:
        _p = _chron_swept_path()
        tmp = _p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=1)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, _p)
    except Exception:
        pass


def _sweep_lock_path():
    """v1832 — THE LOCK BELONGS TO THE FOOTAGE, NOT TO THE SOURCE TREE.

    `.sweep.lock` was written at a hardcoded HERE/.sweep.lock, so every test that started a sweep —
    all of them properly isolated behind TV_HIST + TV_STUB, spending nothing — still reached into
    his working tree and stamped the real file. Measured: `python3 -m unittest test_control` moves
    tv/.sweep.lock every run.

    That is not cosmetic, because run_gates._sweep_in_progress() READS this file to decide whether a
    chronicle sweep is live, and treats anything under 900s old as running. So for fifteen minutes
    after any suite run, the gate believed a sweep was in progress and softened its live-state
    verdict accordingly — a guard disarmed by the very suite it runs beside, which is the shape of
    [[feedback-fixtures-never-touch-live-data]] and of the 08-17 fix "the test suite was writing his
    console's live state".

    Derived from TV_HIST rather than bolted to a new env var: the lock answers "is a sweep of THIS
    footage running", so it belongs beside that footage. With TV_HIST unset — production, his real
    reels — the path is byte-identical to what it always was, so run_gates needs no change.
    """
    env = os.environ.get("TV_SWEEP_LOCK")
    if env:
        return env
    hist = os.environ.get("TV_HIST")
    if hist:
        return os.path.join(hist, ".sweep.lock")
    return os.path.join(HERE, ".sweep.lock")


def _sweep_lock_touch(_last=[0.0]):
    """v1832 — MAKE THE HEARTBEAT REAL. run_gates calls this a lock "with a heartbeat" and says a
    sweep "touches it while it runs" — it was written exactly ONCE, at sweep start. Its staleness
    bound is 900s, and a real sweep of his footage takes far longer than that (the reel running
    while this was written: 37 minutes and counting on ONE reel). So the guard went blind partway
    through precisely the long sweeps it exists to notice. Rate-limited to once a minute: the point
    is a fresh mtime, not the write."""
    now = time.time()
    if now - _last[0] < 60:
        return
    _last[0] = now
    try:
        with open(_sweep_lock_path(), "w") as fh:
            fh.write(str(int(now)))
    except Exception:
        pass


def _chron_seal_stands(rec, prompt_ver=None):
    """v1830 — A SEAL THAT READ NOTHING IS ONLY AS GOOD AS THE READER THAT MADE IT.

    `chronicle_swept.json` recorded ts/classified/pages and NOTHING about the reader, so a reel
    written off as "the classifier looked and found no Chronicle page" stayed written off through
    every later fix to the classifier. The comment above the seal calls that a legitimate seal, and
    it is — but only while the instrument that produced it is the instrument you still have.

    WHAT THAT COST, measured 2026-08-20. Eight reels — 1,032 frames — carried `pages: 0`, sealed
    08-17 16:10 and 08-18 00:41. The fixes that landed AFTER those timestamps: v1770 (a slow scroll
    is not walking through town), v1774 (a throttled reader answered empty and every layer believed
    it), v1777 (the subscription cap refused silently and the sweep believed it), v1778 (a capped
    classify must not seal the reel), v1779 (the worst one burning his footage) and v1780 (read the
    list, not the living room). Three of those six are specifically about the sweep believing a
    reader that had stopped answering — which is exactly the shape "classified 43, pages 0" has.

    And the footage was fine. Frame f_1786999985035.jpg out of the 483-frame reel, opened and looked
    at: a Chronicle page on the Unique tab printing `Nature's Peace — 05/23/2026, 01:06`,
    `Nightsmoke — 05/15/2026, 20:17`, `Nightwing's Veil — 05/18/2026, 00:38`, with his 64% meter in
    the corner. Re-read today it returns all three with their stamps at conf 0.80, and the CLASSIFIER
    now calls it `chronicle-uniques` outright. Nothing about that reel was ever unreadable.

    KEYED ON PROMPT_VER, NOT THE SHIP VERSION — deliberately. Voiding zero-page seals on every
    version bump would re-pay for every genuine gameplay reel on every ship, which is a cost bomb
    dressed as caution. `PROMPT_VER` is already documented as the thing to bump when the reader's
    wording changes, and test_agent has asserted for versions that it "gates cache reuse" — a claim
    nothing in the tree implemented until this function. A seal is a cached verdict; this gives it
    the key it always claimed to have. [[the-unjoined-end]] [[feedback-blind-fixture-green-gate]]

    A seal that DID read pages stands forever: those pages are in the evidence ledger, and re-reading
    them buys nothing. Only the "I looked and there was nothing" claim expires.
    """
    if not isinstance(rec, dict):
        return True     # an unreadable record is not a licence to re-spend his subscription
    if (rec.get("pages") or 0) > 0:
        return True     # it found pages; the findings outlive the reader that found them
    want = prompt_ver
    if want is None:
        try:
            import tv_diablo as _tvd
            want = _tvd.PROMPT_VER
        except Exception:
            return True   # cannot tell which reader is current → change nothing
    return str(rec.get("promptVer") or "") == str(want)


def _chron_skip_set(swept, force=False, prompt_ver=None):
    """v1830 — which sealed reels this sweep may skip, and which it is REOPENING.

    Split out of the sweep body so the decision is testable without a vision model: the inline
    version was `set(swept.keys())`, which is the line that made a stale verdict permanent.
    Returns (skip, reopened) — reopened is returned rather than logged in here so the caller owns
    the wording and the function stays pure.
    """
    swept = swept if isinstance(swept, dict) else {}
    if force:
        return set(), []
    skip = {k for k, v in swept.items() if _chron_seal_stands(v, prompt_ver)}
    return skip, sorted(k for k in swept if k not in skip)


def chronicle_forget_swept():
    """Let him re-read everything — after a prompt change, a new lane, or simple doubt. The memory is
    an optimisation, and an optimisation he cannot clear is a cage."""
    _chron_swept_save({})
    return {"ok": True, "forgot": True}


# ═══════════════════════════════════════════════════════════════════════════════════════
# ⏱ MINI CAPTURE + 🗄 VAULT ACCUMULATOR  —  the mini-capture arc
#
# MINI CAPTURE is ON AIR with a bound. He is parked in the stash looking at gems / runes /
# materials, not playing: 10–40 seconds is the whole session. Same start path, same seal
# path, same spawn — the ONLY difference is two argv flags the agent reads and a watchdog
# that seals at the deadline. An unbounded "mini" is the one outcome that makes the button
# worthless, so the timer is armed BEFORE the button ever reports ok.
#
# THE ARGV CONTRACT (one flag name, one focus name — the cousin's Windows box gets the
# IDENTICAL argv; nothing here branches on platform):
#     --mini=<seconds>        the bound, already clamped to [10,40]
#     --mini-focus=stash      the ONE focus name
# Both are appended in start_agent() for mac AND windows. An agent build that does not know
# them ignores them (tv_diablo.py scans sys.argv, it does not argparse) — so a stale agent
# degrades to a normal session that the watchdog still seals on time.
# ═══════════════════════════════════════════════════════════════════════════════════════

MINI_FLAG = "--mini"                 # the ONE flag name
MINI_FOCUS_FLAG = "--mini-focus"     # carries the focus name
MINI_FOCUS = "stash"                 # the DEFAULT focus

# v1603 — MINI GETS A SUBJECT. Konyo: "is this finally focused and understanding of the fact that
# it is reading stash/runes/gems/materials and to look out specifically for this" — and then, for
# the chronicles: "should have either a chronicle focused based click on.. and button for it so its
# focused specifically for each grail chronicle individually and relevant".
#
# Until now `focus` was stamped onto the reel and used for exactly ONE thing: sweeping mini reels
# first. is_mini_reel's own docstring said so — "being wrong here costs ordering, never
# correctness". Nothing told the READER what it was looking at, so a capture he took while parked
# in his rune tab still paid a model call to DISCOVER that, and could still get it wrong.
#
# These are the surfaces a mini can declare. Kept as one list because two lists of the same names
# drift: the console renders its buttons from this, the agent validates against it, and the retro
# sweep decides whether the stamp is trustworthy by membership in it.
MINI_FOCUSES = ("stash", "runes", "gems", "materials", "chronicle-uniques", "chronicle-sets")
MINI_MIN_SECONDS = 10
MINI_MAX_SECONDS = 40
MINI_DEFAULT_SECONDS = 25
# v1744 — A CHRONICLE IS READ BY SCROLLING, SO IT NEEDS LONGER THAN A STASH TAB.
# Konyo: "maybe longer then 25 seconds for it." A stash tab is ONE screen — 25s photographs it
# several times over. A Chronicle is a LIST he scrolls, so the capture has to last as long as the
# scrolling does, and the vision lane samples it sparsely on top of that (the v1689 guard measured
# his chronicle reads 4.6-9.7s apart). Measured on session s_1786922954749_12579: a pass over his
# uniques Chronicle produced five reads and got from "Amulet" to "Jewel" — A-to-J of ~400 names.
# At 25s the cap was the binding constraint, not his scrolling.
#
# ⚠ v1863 — THESE SIX WERE DELETED BY v1853 AND MINI HAS BEEN DEAD EVER SINCE.
# That commit removed `_focus_was_chosen` as dead code, correctly, and took the constants sitting
# beside it. `_mini_bounds` still names all six, so EVERY /api/mini POST raised
# NameError -> 500 -> a non-JSON body -> the console's fetch().json() threw -> the catch printed
# "mini could not start — the console is not reachable". Konyo saw that toast and reported it as a
# SETS problem; it was every focus, for ten versions. Nothing failed loudly, because the only path
# that touches them is an HTTP handler whose exception became a toast about the network.
MINI_CHRONICLE_FOCUSES = ("chronicle-uniques", "chronicle-sets")
MINI_CHRONICLE_MAX_SECONDS = 240
MINI_CHRONICLE_DEFAULT_SECONDS = 75

# v1870 — Konyo: "i just did a MINI sets and its too short.. it needs to be longer like the UNIQUES
# mini". They were ALREADY the same — 75s each, here and in the console's own table — so the
# premise as stated could not be the defect. What is true is the reason underneath it: a SETS row
# is three lines (name · Dropped By · First Found) where a UNIQUES row is one, so the same 75
# seconds of scrolling covers roughly a third as much ledger. Equal numbers, unequal work.
#
# His judgement about his own scrolling outranks my arithmetic, and the ceiling was the binding
# constraint either way: the console sends only {focus} and no duration, so he had no way to ask
# for more. Sets gets double the default, the chronicle ceiling doubles to 240 so there is room
# above both, and the numbers are PUBLISHED (see /api/mini) instead of copied — the console's
# MINI_FOCUS_SECS was a second copy of this table and would have gone on saying 75. [[copy-drift]]
MINI_FOCUS_SECONDS = {"chronicle-sets": 150}


def _mini_focus(v):
    """A focus name, or the default. Never a caller's arbitrary string — it is stamped into a reel
    and later TRUSTED by the sweep in place of a classify call, so an unknown value must not travel."""
    v = str(v or "").strip().lower()
    return v if v in MINI_FOCUSES else MINI_FOCUS


# v1853 — `_focus_was_chosen` lived here and was called by nothing. Its RULE is real and is
# live: vault_retro._declared_surface() enforces it inline ("focusChosen" in idx and not
# idx.get("focusChosen") -> None), which is what actually stops an untouched default focus
# labelling town and a Chronicle page as a stash panel. A second copy of a live rule that
# nothing calls is worse than no copy: the next person edits it, nothing changes, and the
# real rule sits somewhere else untouched. [[copy-drift]]


def _mini_bounds(focus):
    """(default, max) for a focus. One place, because the console prints these numbers and the
    clamp enforces them, and two copies of a bound is how a button starts lying about itself."""
    f = str(focus or "")
    if f in MINI_CHRONICLE_FOCUSES:
        return (MINI_FOCUS_SECONDS.get(f, MINI_CHRONICLE_DEFAULT_SECONDS),
                MINI_CHRONICLE_MAX_SECONDS)
    return MINI_FOCUS_SECONDS.get(f, MINI_DEFAULT_SECONDS), MINI_MAX_SECONDS

_MINI_LOCK = threading.Lock()
_MINI = {"running": False, "seconds": 0, "startedTs": 0, "endsTs": 0,
         "focus": MINI_FOCUS, "token": 0, "sid": None, "sealedTs": 0, "sealedBy": "",
         "sealedFrames": None,
         "arming": False}


def _mini_clamp(seconds, focus=None):
    """Clamp to [10, max-for-this-focus] and report the ASKED value beside it. 5 and 999 come back
    honest — a button that silently rewrites what he typed is a button he stops trusting.
    v1744 — the ceiling now depends on the focus: a Chronicle is scrolled, a stash tab is not."""
    dflt, mx = _mini_bounds(focus)
    try:
        asked = int(seconds)
    except (TypeError, ValueError):
        return dflt, None
    return max(MINI_MIN_SECONDS, min(mx, asked)), asked


def _mini_sid():
    """The live session id, straight from the agent bridge. None when it cannot be read —
    honest-absent beats inventing an id that no reel on disk will ever match."""
    try:
        st = _bridge_state()
    except Exception:
        return None
    if not isinstance(st, dict):
        return None
    for k in ("sessionId", "sid", "session_id"):
        v = st.get(k)
        if v:
            return str(v)
    s = st.get("session")
    if isinstance(s, dict):
        for k in ("id", "sessionId", "sid"):
            if s.get(k):
                return str(s[k])
    return None


def _mini_frames_seen(sid):
    """Frames actually on disk for this reel. Counted, never estimated: 0 means 0."""
    if not sid:
        return 0
    try:
        rd = os.path.join(HIST_DIR, "reel_" + str(sid))
        return sum(1 for f in os.listdir(rd) if f.lower().endswith(".jpg"))
    except Exception:
        return 0


def _mini_seal(token, why="deadline"):
    """Seal a mini through the SAME path /api/stop uses — stop_agent(farewell=False), with the
    same _force_kill_all_agents fallback. Sealing is NOT re-implemented here.

    RE-ENTRANT BY TOKEN: if he already pressed END SESSION by hand, the running flag is down
    (or the token has moved on) and this is a harmless no-op. A watchdog that could fire a
    SECOND kill would take out the next session he started in the meantime."""
    with _MINI_LOCK:
        if not _MINI["running"] or token != _MINI["token"]:
            return {"ok": True, "noop": True, "why": "already sealed by hand — timer stood down"}
        _MINI["running"] = False
        _MINI["sealedTs"] = int(time.time() * 1000)
        _MINI["sealedBy"] = why
    try:
        r = stop_agent(farewell=False)
    except Exception as _e:
        r = _force_kill_all_agents("mini (%s; stop_agent raised: %s)" % (why, str(_e)[:100]))
    if not isinstance(r, dict):
        r = {"ok": True}
    # ── v1605 — DID IT ACTUALLY RECORD ANYTHING? ───────────────────────────────────────────
    # Konyo, on his wife's Windows PC: "i clicked mini and it doesnt record anything."
    #
    # MINI replicates ON AIR everywhere that matters — same start_agent, same disk preflight, same
    # stop path, and MINI_MODE changes NO capture behaviour in the agent (it only stamps the reel).
    # The one thing it adds is a 25-second bound, and that bound is exactly where an honest gap
    # opens: if capture needs longer to warm up than the deadline allows — D2R not running, window
    # not found yet, a cold first grab on a Windows box — the watchdog seals a reel with ZERO frames
    # and reports the same cheerful success as a good one.
    #
    # An empty reel and a full one must not look alike. The count is read off the sealed reel's own
    # index, so it is the reel's word and not the agent's. If the seal was cut short before it
    # wrote one, the index is rebuilt from the frame filenames first — still the reel's own word.
    frames = None
    try:
        _sid = _MINI.get("sid")
        if _sid:
            _rows = _reel_index_frames(os.path.join(HIST_DIR, "reel_" + str(_sid)))
            frames = len(_rows) if _rows is not None else None
    except Exception:
        frames = None          # unreadable is NOT zero — say unknown rather than accuse the capture
    with _MINI_LOCK:
        _MINI["sealedFrames"] = frames
    return dict(r, mini=True, sealedBy=why, frames=frames)


def _mini_watchdog(token, ends_ts):
    """Daemon. Wakes twice a second, seals once, dies. It never extends and never re-arms."""
    while True:
        with _MINI_LOCK:
            if not _MINI["running"] or token != _MINI["token"]:
                return          # sealed by hand / superseded — stand down, do not kill
        if time.time() * 1000 >= ends_ts:
            break
        time.sleep(0.5)
    try:
        _mini_seal(token, why="deadline")
    except Exception:
        pass


def mini_state():
    """GET shape. secondsLeft is clamped at 0 — a negative countdown is a lie about a session
    that is already over."""
    with _MINI_LOCK:
        m = dict(_MINI)
    left = 0
    if m["running"] and m["endsTs"]:
        left = max(0, int(round((m["endsTs"] - time.time() * 1000) / 1000.0)))
    sid = m.get("sid") or (_mini_sid() if m["running"] else None)
    if m["running"] and sid and not m.get("sid"):
        with _MINI_LOCK:
            if _MINI["running"]:
                _MINI["sid"] = sid          # first read that could see it wins; never overwritten
    return {
        "ok": True,
        "running": bool(m["running"]),
        "mode": "mini",
        "focus": m.get("focus") or MINI_FOCUS,
        "seconds": int(m.get("seconds") or 0),
        "secondsLeft": left,
        "endsTs": int(m.get("endsTs") or 0),
        # v1605 — frames in the reel this mini sealed. None = could not read the index (unknown,
        # NOT zero). 0 = it genuinely recorded nothing, which is the case he hit and could not see.
        "sealedFrames": m.get("sealedFrames"),
        "sid": sid,
        "framesSeen": _mini_frames_seen(sid),
        "sealedBy": m.get("sealedBy") or "",
    }


def mini_start(seconds=None, test=False, focus=None):
    """⏱ MINI ON AIR. Same start_agent() as ON AIR — no second spawn path anywhere.

    v1603 — `focus` names WHAT he is parked on, and it is not decoration: the retro sweep trusts it
    in place of a classify call, so it is validated here rather than passed through raw."""
    focus = _mini_focus(focus)
    secs, asked = _mini_clamp(seconds, focus)   # v1744 — focus decides the default AND the ceiling
    # v891 (Grok C3) — DISK PREFLIGHT, copied verbatim from /api/on: below the floor the reaper
    # can't keep a reel alive; refuse loudly with the exact ask instead of recording a doomed
    # session. A mini that records a doomed reel is worse than one that refuses — the whole
    # point of the mini is the RETRO read afterwards, and a reaped reel has nothing to read.
    try:
        import shutil as _shd
        _free = _shd.disk_usage(HIST_DIR).free / 1e9
        if _free < 8.0:
            return {"ok": False, "mode": "off", "seconds": secs, "secondsAsked": asked,
                    "error": "DISK TOO FULL to record — %.1fGB free, need 8GB. Free ~%.0fGB and press MINI again." % (_free, 9 - _free)}
    except Exception:
        pass
    if _stop_inflight:
        # v899 — if the agent is already dead, clear the latch and allow the start
        if not _agent_alive() and _port_listener_pid() is None:
            globals()["_stop_inflight"] = False
            globals()["_agent_mode"] = "off"
        else:
            return {"ok": False, "seconds": secs, "secondsAsked": asked,
                    "msg": "still shutting down — session saving; try MINI again in a moment",
                    "mode": "stopping", "error": "still stopping"}
    # REFUSE LOUDLY, never silently. Two overlapping captures write into one reel and neither
    # read afterwards can be trusted to belong to the session he thinks it does.
    with _MINI_LOCK:
        if _MINI["running"]:
            # secondsLeft computed INLINE. Calling mini_state() here would re-acquire _MINI_LOCK
            # inside the block that already holds it — threading.Lock is not reentrant, so the
            # second press of the button deadlocked the whole HTTP handler thread. Caught by the
            # trace below (the "second press while running" probe never returned).
            _left = max(0, int(round((_MINI["endsTs"] - time.time() * 1000) / 1000.0)))
            return {"ok": False, "seconds": secs, "secondsAsked": asked,
                    "why": "already recording — seal the current session first",
                    "mode": "mini", "secondsLeft": _left}
    if _agent_alive():
        return {"ok": False, "seconds": secs, "secondsAsked": asked,
                "why": "already recording — seal the current session first", "mode": "live"}
    with _MINI_LOCK:
        _MINI["token"] += 1
        token = _MINI["token"]
        now_ms = int(time.time() * 1000)
        _MINI.update({"running": True, "seconds": secs, "startedTs": now_ms,
                      "endsTs": now_ms + secs * 1000, "focus": focus,
                      "sid": None, "sealedTs": 0, "sealedBy": "", "arming": True})
        ends = _MINI["endsTs"]
    # ARM FIRST. If the spawn hangs past the deadline the watchdog still seals it; a timer armed
    # only on success is a timer that is absent exactly when it is needed.
    threading.Thread(target=_mini_watchdog, args=(token, ends), daemon=True,
                     name="tvd-mini-watchdog").start()
    try:
        r = start_agent(sim=False, test=bool(test), mini=secs, focus=focus)
    finally:
        with _MINI_LOCK:
            if _MINI["token"] == token:
                _MINI["arming"] = False      # fence down: from here a hand-stop stands the timer down
    if not isinstance(r, dict):
        r = {"ok": False, "error": "start_agent answered nothing"}
    if not r.get("ok"):
        # the start failed — stand the timer down rather than leaving a phantom mini running
        with _MINI_LOCK:
            if _MINI["token"] == token:
                _MINI["running"] = False
                _MINI["sealedBy"] = "start-failed"
        return dict(r, mode="off", seconds=secs, secondsAsked=asked, mini=False)
    sid = _mini_sid()
    with _MINI_LOCK:
        if _MINI["token"] == token:
            _MINI["sid"] = sid
    _console_beacon_async("onair")   # v875 — the dashboard flips 🔴 within seconds
    return dict(r, mini=True, mode="mini", focus=focus,
                seconds=secs, secondsAsked=asked, secondsLeft=secs,
                endsTs=ends, sid=sid,
                # ★ the clamp said out loud. 5 and 999 come back with what he asked beside what
                # he got, never silently altered.
                msg=("mini capture — %ds%s" % (secs, "" if asked in (None, secs)
                                               else " (asked %s, bound is %d–%ds)"
                                               % (asked, MINI_MIN_SECONDS, _mini_bounds(focus)[1]))))


# ── 🗄 VAULT ACCUMULATOR — the retro half, and the priority half ────────────────────────
# Same shape as the Chronicle sweep, pointed at a different target: read the sealed reels,
# propose, apply through the BOARD with merge-max. Its own job dict + lock so a vault sweep
# and a chronicle sweep cannot corrupt each other's progress or each other's result.
#
# ALL reading / grouping / gating lives in tv/vault_retro.py. This file is the job runner and
# the HTTP surface — it holds NO accumulation logic, so there is exactly one place where the
# merge rules can drift.
#
# THE LEDGER (vault_accum.json) IS EVIDENCE, NOT TRUTH. It is what the readers have SEEN
# across sessions, rebuildable from the reels at any time. The board is the only source of
# truth for what he owns. Merge-max only — a read that saw fewer items than he has must never
# subtract, because an obstructed or half-scrolled stash frame is a NORMAL event, not evidence
# he threw something away.

# v1902 — THE ONE FILE THAT SAYS WHAT HE OWNS DID NOT FOLLOW THE ISOLATION RULE.
#
# Every neighbouring piece of live state takes an isolated TV_HIST along with it — sessions,
# frames, the chronicle's swept memo, its evidence, its reads, its result, and (v1895) the vault's
# own RESULT. These two did not: they were bare `os.path.join(HERE, ...)`, so a sweep driven
# against a fixture hist wrote its swept memo and its OWNED-ITEM LEDGER into his real tv/ tree.
#
# Nothing has hit it, and that is the whole reason to fix it rather than shrug: what stopped it was
# the discipline of every fixture written so far, not the path. The gate that proves his tree is
# byte-identical after a run can only catch this AFTER a test reaches it, and by then the ledger it
# corrupted is the record of what he owns — merge-max, so nothing it gains is ever subtracted.
# Guard the PATH, not the call site. [[feedback-fixtures-never-touch-live-data]]
VAULT_LEDGER_PATH = (os.environ.get("TV_VAULT_LEDGER")
                     or os.path.join(_fixture_root_for_state(), "vault_accum.json"))
_VAULT_SWEPT_PATH = (os.environ.get("TV_VAULT_SWEPT")
                     or os.path.join(_fixture_root_for_state(), "vault_swept.json"))

_VAULT_LOCK = threading.Lock()
_VAULT_JOB = {"running": False, "startedTs": 0, "phase": "idle", "reelsDone": 0, "reelsTotal": 0,
              "classified": 0, "pagesRead": 0, "result": None, "error": None, "lanes": []}


def _vault_retro():
    """Import the reader module, or say exactly which piece is missing. Never a stub that
    pretends to read — an invented count in the vault is an item he throws away."""
    import vault_retro as _vr
    return _vr


def _vault_swept_load():
    try:
        with open(_VAULT_SWEPT_PATH, encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _vault_swept_save(rec):
    """Torn-write safe (v1209 doctrine): a crash mid-write must not read back as
    'nothing was ever swept' and re-pay for the whole hist."""
    _vault_json_save(_VAULT_SWEPT_PATH, rec)


def _vault_json_save(path, rec):
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=1)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        return True
    except Exception:
        return False


def vault_ledger_load():
    try:
        with open(VAULT_LEDGER_PATH, encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def vault_ledger_save(led):
    return _vault_json_save(VAULT_LEDGER_PATH, led if isinstance(led, dict) else {})


_VAULT_QUOTE = {"sig": None, "res": None}


def _hist_signature(hist):
    """Cheap fingerprint of the sealed-reel set: how many, and the newest mtime."""
    try:
        names = sorted(os.listdir(hist))
        newest = 0.0
        for n in names:
            try:
                newest = max(newest, os.stat(os.path.join(hist, n)).st_mtime)
            except OSError:
                pass
        return "%d:%.0f" % (len(names), newest)
    except Exception:
        return None


def vault_scan_cost(hist_dir=None, limit=None):
    """THE QUOTE IS MEMOISED TOO, not just the gate underneath it.

    v1941 — caching the per-frame gate took this from ~7.4 minutes to 82 SECONDS, measured on his
    own film (2699 frames, 1065 reels). Better, and still far past the point where a button with no
    timeout reads as dead — which is exactly what he was looking at. The gate was not the only cost;
    the sweep walks 2155 frames whatever the gate says.

    So the answer itself is kept, keyed on the sealed-reel set (count + newest mtime). Nothing about
    a sealed reel changes after it is sealed, so an unchanged set has an unchanged price, and the
    second tap is instant. Seal a new reel and the signature moves and it re-prices — which is the
    only time the number could differ.
    """
    hist = hist_dir or os.environ.get("TV_HIST") or HIST_DIR
    sig = _hist_signature(hist)
    if sig is not None and _VAULT_QUOTE["sig"] == sig and _VAULT_QUOTE["res"] is not None:
        out = dict(_VAULT_QUOTE["res"])
        out["cached"] = True
        return out
    try:
        res = _vault_scan_cost_inner(hist_dir, limit)
    finally:
        _gate_cache_flush()
    if sig is not None and isinstance(res, dict) and res.get("ok") is not False:
        _VAULT_QUOTE["sig"] = sig
        _VAULT_QUOTE["res"] = res
    return res


def _vault_scan_cost_inner(hist_dir=None, limit=None):
    """THE FREE PASS, vault edition. What a vault retro sweep WOULD cost, computed on HIS film.
    Zero model calls, zero writes — the number he gets to check before agreeing to spend.

    v1596 — same under-quote as the Chronicle pass, same fix. The probe answered None, sweep() read
    that as "unclassifiable", held the run and never reached the reader — so `pagesRead` was
    structurally pinned at 0 and the quote billed only the classify lane. Measured on a fixture:
    quoted 2, actual 6. The probe now answers a real surface so the SAME sweep() code counts the
    pages, which makes this an UPPER BOUND. See chronicle_scan_cost for why high is the only safe
    direction to be wrong in.
    """
    try:
        _vr = _vault_retro()
    except Exception as e:
        return {"ok": False, "why": "vault_retro unavailable: %s" % str(e)[:160]}
    if not hasattr(_vr, "sweep"):
        return {"ok": False, "why": "vault_retro has no sweep() — nothing to price"}
    hist = hist_dir or os.environ.get("TV_HIST") or HIST_DIR
    if not os.path.isdir(hist):
        return {"ok": True, "reels": [], "totals": {"sessionsSeen": 0, "framesSeen": 0,
                                                    "classified": 0, "pagesRead": 0},
                "note": "no sealed reels yet", "spent": 0}
    picked = []

    def _probe(path):
        picked.append(path)
        # v1851 — THE QUOTE ASKS THE SAME GATE THE SWEEP DOES.
        #
        # This answered "stash" for every path on purpose: v1596 made the quote price the WORST
        # CASE, because a probe that answered None skipped the read stage and hid the larger half
        # of the bill. That reasoning stands — but v1850 put a STRUCTURAL gate in front of the real
        # sweep, so the two now disagree by a lot: the quote would price every gameplay frame as a
        # readable stash page while the sweep refuses those for free.
        #
        # The gate costs no model call — a crop and an OCR — so the quote can just ask it, and the
        # number he reads before agreeing to spend describes the run he would actually get. Same
        # rule v1834 applied to the chronicle quote: both halves of a price must name the same
        # thing. A refused frame is still COUNTED as looked at; it is only not priced as a page.
        if stash_screen_open_cached(path) is None:
            return None
        return "stash"

    try:
        import chronicle_retro as _cr
        dirs = _cr.reel_dirs(hist)
        # a dict with NO "note" — sweep() counts it as a page read and finds zero items in it. A
        # {"note": ...} here is a REFUSAL and is exactly what kept pagesRead at 0 before v1596.
        res = _vr.sweep(dirs, sig=_vr.DEFAULT_SIG, classify=_probe,
                        reader=lambda p, s: {"items": []}, limit=limit)
    except Exception as e:
        return {"ok": False, "why": "vault scan failed: %s" % str(e)[:160], "spent": 0}
    t = res.get("totals") or {}
    seen = t.get("framesSeen") or 0
    classifies = t.get("classified") or 0
    pages = t.get("pagesRead") or 0
    calls = classifies + pages            # ★ BOTH lanes, or the quote is not a quote
    return {
        "ok": True,
        "why": res.get("why") or "",
        "reels": [os.path.basename(d) for d in _vr.order_reels(dirs)[:40]],   # mini-first order
        "totals": t,
        "savedPct": round(100.0 * (1 - (calls / seen)), 1) if seen else 0.0,
        "wouldRead": calls,
        "wouldClassify": classifies,
        "wouldReadPages": pages,
        "upperBound": True,
        # v1852 — this sentence stopped being true the moment v1851 gave the probe the structural
        # gate: it no longer prices EVERY candidate run, it prices the ones that prove they are a
        # stash screen. Still an upper bound — a gated-in frame can still turn out unreadable to the
        # model — but for a different reason than the one printed here, and a right number under a
        # stale explanation is the shape this repo keeps paying for. Corrected by the person who
        # invalidated it, an hour later. [[label-outlived-referent]]
        "boundWhy": "prices the candidate runs that PROVE they are an ownership screen (the same "
                    "structural gate the real sweep uses, v1850); a gated-in frame can still turn "
                    "out unreadable, so the true bill lands at or under this",
        "insteadOf": seen,
        "spent": 0,            # ★ said out loud: this route cannot cost anything
        "frames": [os.path.relpath(p, hist) for p in picked[:40]],
    }


def _vault_result_save():
    """Persist the finished vault sweep. Best effort, silent on failure — losing the cache must
    never take down the sweep that produced it. v1895; mirrors _chron_result_save deliberately,
    including the atomic tmp+replace and the refusal to use `default=str` (v1800: it would turn an
    unserializable value into its REPR and reload it as a NAME, silently corrupting the ledger)."""
    try:
        with _VAULT_LOCK:
            res = _VAULT_JOB.get("result")
        if not res:
            return
        payload = {"result": res, "savedTs": int(time.time() * 1000)}
        tmp = _VAULT_RESULT_PATH + ".tmp"
        # v1899 — MAKE THE PARENT. With an isolated TV_HIST pointing at a directory that does not
        # exist yet, the tmp write fails with ENOENT and the proposal is lost. The chronicle's save
        # has the same shape and says so out loud when it happens; mine swallowed it entirely.
        try:
            os.makedirs(os.path.dirname(_VAULT_RESULT_PATH) or ".", exist_ok=True)
        except Exception:
            pass
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
            fh.flush()
            try:
                os.fsync(fh.fileno())
            except Exception:
                pass
        os.replace(tmp, _VAULT_RESULT_PATH)
    except Exception as e:
        # v1899 — A SILENT FAILURE HERE UNDOES v1895 EXACTLY. The whole point of persisting the
        # vault proposal is that the READS THAT PAID FOR IT are spent; losing it quietly means he
        # closes the console and finds nothing, with no way to know why. The chronicle's save has
        # said so for versions ("this sweep will not survive a restart") and mine said nothing —
        # written last night, one ship after fixing the same class in his code.
        # [[feedback-silence-is-not-evidence]]
        print("   \u26a0 vault result NOT persisted (%s) — this sweep will not survive a restart"
              % str(e)[:140])


def _vault_result_load():
    """Restore the last vault proposal into an empty job. Never overwrites a live one."""
    try:
        with _VAULT_LOCK:
            if _VAULT_JOB.get("result") or _VAULT_JOB.get("running"):
                return False
        if not os.path.isfile(_VAULT_RESULT_PATH):
            return False
        with open(_VAULT_RESULT_PATH, encoding="utf-8") as fh:
            payload = json.load(fh) or {}
        res = payload.get("result")
        if not res:
            return False
        with _VAULT_LOCK:
            _VAULT_JOB["result"] = res
            _VAULT_JOB["phase"] = _VAULT_JOB.get("phase") or "done"
            _VAULT_JOB["resultTs"] = payload.get("savedTs")
            _VAULT_JOB["restoredFrom"] = payload.get("savedTs")
        return True
    except Exception:
        return False


def vault_sweep_state():
    # v1895 — a fresh process reports the LAST sweep, not "idle, nothing here". Same reasoning the
    # chronicle has used since v1763, and the same age fields the console renders (v1894), so a
    # proposal from last week cannot read as one made just now. [[stale-reading]]
    _vault_result_load()
    with _VAULT_LOCK:
        st = dict(_VAULT_JOB)
    st["resultTs"] = _VAULT_JOB.get("resultTs")
    st["resultFromDisk"] = bool(_VAULT_JOB.get("restoredFrom"))
    return st


def vault_sweep_start(hist_dir=None, limit=None, force=False):
    """Kick the background vault sweep. Refuses a second one — two sweeps over the same reels
    double the spend and produce two proposals that each look like the whole truth.

    Needs NO live agent. That is the whole point of retro: he plays, seals, and the reading
    happens afterwards against film that is not going to change."""
    try:
        _vr = _vault_retro()
    except Exception as e:
        return {"ok": False, "why": "vault_retro unavailable: %s" % str(e)[:160]}
    for fn in ("sweep", "merge_vault", "apply_payload"):
        if not hasattr(_vr, fn):
            return {"ok": False, "why": "vault_retro has no %s() — this build cannot sweep safely" % fn}
    with _VAULT_LOCK:
        if _VAULT_JOB["running"]:
            return {"ok": False, "why": "a vault sweep is already running", "state": dict(_VAULT_JOB)}
        lanes = _chron_lanes()
        if "claude" not in lanes:
            # Claude is PRIMARY. Without it there is no page for a second opinion to be about.
            return {"ok": False, "why": "the primary (Claude) lane is unavailable — nothing to sweep with"}
        _VAULT_JOB.update({"running": True, "startedTs": int(time.time() * 1000), "phase": "grouping",
                           "reelsDone": 0, "reelsTotal": 0, "classified": 0, "pagesRead": 0,
                           "result": None, "error": None, "lanes": lanes})
    threading.Thread(target=_vault_sweep_run, args=(hist_dir, limit, force),
                     daemon=True, name="tvd-vault-sweep").start()
    return {"ok": True, "started": True, "lanes": lanes}


def _vault_sweep_run(hist_dir, limit, force=False):
    try:
        _vr = _vault_retro()
        import tv_diablo as _tv
        try:
            import g5_grok_eyes as _g5
        except Exception:
            _g5 = None
        import chronicle_retro as _cr
        hist = hist_dir or os.environ.get("TV_HIST") or HIST_DIR
        swept = _vault_swept_load()
        # the swept memory is keyed by whatever sweep() reports in sessionsRead; check the reel
        # basename BOTH ways (reel_<sid> and bare <sid>) so a naming mismatch can only ever cause a
        # re-read — never a silently skipped reel.
        dirs = [d for d in _cr.reel_dirs(hist)
                if force or (os.path.basename(d) not in swept
                             and os.path.basename(d).replace("reel_", "", 1) not in swept)]
        with _VAULT_LOCK:
            _VAULT_JOB["reelsTotal"] = len(dirs)
            _VAULT_JOB["phase"] = "reading"

        def _tick(**kw):
            with _VAULT_LOCK:
                for k, v in kw.items():
                    _VAULT_JOB[k] = _VAULT_JOB.get(k, 0) + v if isinstance(v, int) else v

        # v1577 doctrine — ONE BAD FRAME MUST NOT ABANDON THE WHOLE SWEEP. vault_retro.sweep()
        # calls these lanes directly, so the isolation lives here: a throwing probe answers None
        # (honest-absent — "not read", never a guessed surface) and every later reel is still read.
        # The tick stays INSIDE the lane so "classified" counts probes ATTEMPTED — a probe that
        # died is still money spent and still belongs in the count.
        _not_stash = [0]
        _read_no_names = [0]     # read cleanly, and the panel prints no names to read
        _gate0 = gate_hearing()  # the gate's audibility AT THE START, so the report is this run's

        def _classify(p):
            # ── THE TEMPLATE GATE (2026-08-20, his ask) ──────────────────────────────────────
            # Konyo: "it needs to be hardcoded and safegauded for vault manager to only when maybe
            # i CLICK stash and am in my stash with my inventory open at the same time thats the
            # template it should start knowing to read whats in my inventory and stash".
            #
            # HARDCODED means structural, not a model's opinion. stash_screen_open() reads the stash
            # TAB CHROME out of a fixed band by OCR — no chrome, no stash panel, no vault read. D2R
            # draws the inventory beside the stash whenever it is open, so that chrome IS the
            # "both at the same time" template he described.
            #
            # This is asked BEFORE the paid classify, so a frame that is not a stash costs nothing
            # at all, and it is asked of EVERY frame including those in a declared-focus reel: he
            # told the app what he parked on, not that every frame of the recording is that screen.
            # Which SURFACE it is still comes from the declared focus first (v1603) — the gate only
            # decides whether this frame may speak about ownership at all.
            # the value is deliberately DISCARDED — only "may this frame speak about ownership"
            # is asked here. v1859 proved what happens when the answer is also used as a lane.
            if stash_screen_open(p) is None:
                _not_stash[0] += 1
                return None
            # v1859 — REVERTED: THE TAB IS A GUESS, AND A GUESS MAY NOT NAME A LANE.
            #
            # v1857 returned this tab as the ownership SURFACE, to save a model call. That was
            # wrong, and stash_eye says so in its own docstring, which I did not read closely
            # enough: "Active-tab GUESS from OCR lines. Stash chrome always prints ALL five tab
            # names... 2+ canons → '' (ambiguous chrome; pixel/grid fingerprint decides)."
            #
            # Reading a tab LABEL off the strip proves the stash panel is OPEN — which is all
            # v1850's gate needs, and it remains sound. It does not prove which tab is SELECTED.
            # Proven on his own frame 5_1784984201581.jpg: the strip OCRs as
            # [',WAAITHsrirEP', 'Gems', 'fflATtklAL5'] — a tooltip, plus two labels, one garbled
            # past recognition — so exactly one canon matched and the function answered "gems"
            # while the selected tab is Runes. v1857 then handed "gems" to the reader as the
            # surface, the reader was asked whether a RUNES panel is a gems panel, correctly said
            # no, and returned zero items from a stash full of them.
            #
            # That is precisely the harm this whole arc exists to prevent — vault_retro: "a rune
            # tab misread as 'inventory' files his runes in the wrong lane, which merge-max then
            # makes permanent." Saving a model call is not worth reintroducing it. The paid
            # classify decides the surface again; the free gate still decides admission.
            _tick(classified=1)
            try:
                return _tv.claude_read(p)
            except Exception:
                return None

        # v1853 — THE GATE HAS TO BE ON THE READER TOO, which v1850 got wrong.
        #
        # v1850 put the stash template in front of _classify and its commit note claimed it was
        # "asked of EVERY frame, including inside a declared-focus reel". It is not: vault_retro
        # skips the classifier ENTIRELY for a declared focus (v1603, `if declared: surface =
        # declared`), so the gate never ran on exactly the reels he records on purpose.
        #
        # His ask has no such exception in it — "only when i CLICK stash and am in my stash with my
        # inventory open at the same time thats the template". A mini started while walking to the
        # stash still holds frames that are not the stash, and a name read off one of those lands in
        # the stash lane where merge-max makes it permanent.
        #
        # The READER is the one hook both paths pass through, so the gate belongs here as well. It
        # stays on _classify too, where it saves paying for a classify at all.
        def _reader(p, surface):
            if stash_screen_open(p) is None:
                _not_stash[0] += 1
                return {"note": "not a stash screen — no stash chrome, so nothing here is ownership"}
            _tick(pagesRead=1)
            try:
                # v1785 — THE VAULT READER, at last. This called claude_chronicle_read, whose answer
                # has no `items` key, so vault_retro could never ground a row from it — and because
                # `note` is None on a good chronicle read it did not even count as a refusal: the
                # page counted as read and the reel was marked swept. The seam exists now.
                _r = _tv.claude_vault_read(p, surface)
                # v1861 — "READ FINE, AND THERE IS NOTHING NAMEABLE ON IT" IS A THIRD ANSWER.
                # D2R prints no item names in a stash grid; a name appears only in the HOVER
                # tooltip. So a perfectly good read of a full shelf honestly returns items:[] —
                # measured on his own frames, with the model's raw reply captured:
                #   6_1784984233446 stash     -> {"items":[],"conf":0.0}   (sonnet, 8s, real reply)
                #   5_1784984201581 runes     -> {"items":[],"conf":0.0}
                #   8_1785078207015 materials -> {"items":[],"conf":0.0}
                # Counted separately so the end-of-sweep line can say WHICH of the three happened
                # instead of offering him two possibilities, neither of them the true one.
                if isinstance(_r, dict) and not _r.get("note") and not (_r.get("items") or []):
                    _read_no_names[0] += 1
                return _r
            except Exception:
                return {"note": "the reader failed on this page — not read"}

        prop = _vr.sweep(dirs, sig=_vr.DEFAULT_SIG, classify=_classify, reader=_reader, limit=limit)
        if _not_stash[0]:
            # said out loud, never silently: "the stash was never open on camera" and "the reader
            # found nothing in it" are different answers and only one of them is about his stash
            print("   \U0001f512 %d frame(s) refused by the stash template — no stash chrome, so "
                  "not an ownership screen" % _not_stash[0])
        # v1865 — MEASURE THE RUN, NOT THE PROCESS. This read gate_hearing() raw, and those
        # counters are process-lifetime: in the long-lived console, ONE successful probe ever makes
        # `heard` non-zero forever, so the warning could never fire again no matter how completely
        # the OCR lane died later. A run-level claim built on a lifetime counter — the same defect
        # this whole arc keeps finding, written by me into the fix for it. Deltas now.
        _gs = _GATE_SILENT[0] - _gate0[0]
        _gh = _GATE_HEARD[0] - _gate0[1]
        if _gs and not _gh:
            print("   \U0001f507 the tab-chrome OCR answered NOTHING on all %d probe(s) THIS RUN. "
                  "That is the READER being silent, not a verdict about his stash — nothing here "
                  "says a frame was or was not an ownership screen." % _gs)
        if _read_no_names[0]:
            print("   \U0001f441 %d panel(s) READ CLEANLY and held no readable name. D2R prints "
                  "no names in a stash grid — a name exists only in the HOVER tooltip. This is not "
                  "a failure and not an empty shelf; it is the footage." % _read_no_names[0])
        _tick(reelsDone=int((prop.get("totals") or {}).get("sessionsSeen") or 0))
        # remember ONLY the reels this run actually read — a reel that errored or was skipped stays
        # unread, or one bad run permanently hides footage from every future sweep.
        # v1779 — DO NOT SEAL FOOTAGE A LANE CANNOT READ. The rule stands; the reason below it had
        # gone stale and is corrected here.
        #
        # WHAT v1779 FOUND, and it was real: the vault sweep was wired to the CHRONICLE reader.
        # claude_chronicle_read returns {found, notFound, sets, stateVisible, ...} while vault_retro
        # reads resp["items"], which was never present — and `note` is None on a GOOD chronicle read,
        # so it did not even count as a refusal. The page counted as read, the reel was marked, and
        # no row could ever be produced.
        #
        # ⚠ THAT WAS FIXED IN v1785 AND THIS TEXT WAS NOT. `claude_vault_read` exists, `_reader`
        # calls it, and v1785's own note says "THE VAULT READER, at last... The seam exists now."
        # The comment and the message below kept telling anyone who read them that "the seam was
        # never built" — for seventy-odd versions, and it sent me looking for a seam that was
        # already there during an integration run on 2026-08-20. A right rule under a dead reason
        # is still a lie about the system. [[label-outlived-referent]]
        #
        # THE SAFEGUARD ITSELF IS UNCHANGED AND STILL WANTED: a sweep that grounded nothing seals
        # nothing, so a reel is never written off on the strength of a run that produced no rows —
        # whatever the cause. What changes is that the message now says what is actually known.
        _rows = len((prop.get("uniques") or {})) + len((prop.get("owned") or []))
        if _rows:
            for sess in (prop.get("sessionsRead") or []):
                swept[str(sess)] = {"ts": int(time.time() * 1000)}
            _vault_swept_save(swept)
        else:
            print("   \u26a0 vault sweep produced no rows — sealing nothing, so the footage stays "
                  "readable. The reader ran (v1785's seam). The lines above say which of the three "
                  "it was: refused by the template, read-and-nothing-nameable, or genuinely empty.")

        # ACCUMULATE ACROSS SESSIONS — merge-max only, and the merge itself lives in vault_retro.
        # This ledger is what the readers have SEEN; it is never what he owns.
        led = _vr.merge_vault(vault_ledger_load(), prop)
        if not vault_ledger_save(led):
            # v1779 — the swept marker used to be written BEFORE this, and this return value was
            # discarded: a failed ledger write left the reels marked and their paid reads gone.
            print("   ⚠ vault ledger did not save — the reels stay unswept so nothing is lost")
        # The proposal he presses is the ACCUMULATED picture (every session so far), not just this
        # run's — that is the whole point of an accumulator. throwOut/unsure/held stay from this
        # run's gate, which is the only place they were reasoned about.
        out = dict(prop, owned=led.get("owned") or prop.get("owned") or [],
                   accum={"added": led.get("added") or [], "raised": led.get("raised") or [],
                          "held": led.get("held") or []})
        globals()["_VAULT_LAST_PROPOSAL"] = out
        with _VAULT_LOCK:
            _VAULT_JOB.update({"running": False, "phase": "done", "result": out, "error": None,
                               "resultTs": int(time.time() * 1000), "restoredFrom": None})
        _vault_result_save()
    except Exception as e:
        with _VAULT_LOCK:
            _VAULT_JOB.update({"running": False, "phase": "error", "error": str(e)[:200]})


_VAULT_LAST_PROPOSAL = None


def vault_forget(ledger=False):
    """Let him re-read everything. The swept memory is an optimisation, and an optimisation he
    cannot clear is a cage. ledger=true ALSO drops the accumulated evidence — safe, because the
    ledger is rebuildable from the reels and was never the source of truth for what he owns."""
    _vault_swept_save({})
    if ledger:
        vault_ledger_save({})
    return {"ok": True, "forgot": True, "ledgerCleared": bool(ledger)}


def vault_apply(proposal=None):
    """Ask THE BOARD to apply the vault accumulator's gated rows. The console never writes the
    vault, the grail or localStorage.

    The ledger lives in the board (THE VAULT / d2r_foundLog / the stash tallies) and the board's
    own window.vaultAccumApply routes through the same tick his hand uses — dated, merge-max,
    undoable. Reaching around it to write localStorage from here would create a second write path
    into his vault, which is a second thing that can drift from the first.

    Returns what the board reports. If the board window is not there, it says so — an apply that
    silently did nothing is the worst possible answer, because the proposal still looks unapplied
    and he will just run the sweep again."""
    st = vault_sweep_state()
    # ── v1595 — RE-GATE AT THE WRITE, not only at the sweep. ──────────────────────────────────
    # A caller-supplied proposal used to go straight through: the two-witness / confidence gate
    # runs when the SWEEP builds its result, so a hand-made body posted to this endpoint carried
    # rows nothing had ever corroborated, and they landed in his stash with a single unverified
    # sighting behind them. Localhost-only is not an argument — the board itself is a caller, and
    # a rule enforced in one place is a rule with a door beside it.
    # Grok's third-eye pass on v1594 flagged exactly this, and it was right.
    caller_supplied = proposal is not None
    prop = proposal or (st.get("result") if isinstance(st.get("result"), dict) else None)
    if caller_supplied and isinstance(prop, dict):
        try:
            _vr = _vault_retro()
            _kept, _dropped = [], []
            for _r in (prop.get("owned") or []):
                _ev = _r.get("evidence") or _r.get("witnesses") or []
                _v = _vr.gate(_ev, _vr.KEEP_CONF_FLOOR, _vr.KEEP_MIN_WITNESSES)
                (_kept if _v.get("pass") else _dropped).append(_r)
            if _dropped:
                return {"ok": False,
                        "why": "%d row(s) in that proposal do not clear the gate (%s conf, %s "
                               "witnesses) — a proposal handed in from outside is re-checked here, "
                               "because the gate has to hold where the WRITE happens"
                               % (len(_dropped), _vr.KEEP_CONF_FLOOR, _vr.KEEP_MIN_WITNESSES),
                        "rejected": [str(_r.get("name") or "?") for _r in _dropped][:20]}
        except Exception as _e:
            return {"ok": False, "why": "could not re-gate the supplied proposal: %s" % str(_e)[:120]}
    if not prop:
        return {"ok": False, "why": "no vault sweep result to apply — run a sweep first"}
    owned = prop.get("owned") or []
    unsure = prop.get("unsure") or []
    throw = prop.get("throwOut") or []
    if not owned and not unsure and not throw:
        return {"ok": False, "why": "the sweep grounded nothing — there is nothing to apply"}
    if not owned and not unsure:
        # ★ THE THROW-OUT REFUSAL. Advising him to bin an item is the one irreversible action in
        # this whole app — there is no un-throw in Diablo. A proposal that is ONLY throw-outs has
        # nothing to register, so pressing apply could only ever destroy.
        return {"ok": False, "why": "this proposal is throw-out suggestions only — there is nothing "
                                    "to register, and a throw-out is never applied for you"}
    w = globals().get("_MAIN_WIN")
    if w is None or not globals().get("_WINDOW_LIVE"):
        return {"ok": False, "why": "the board window is not open — open TV DIABLO and try again"}
    # SHAPED BY vault_retro.apply_payload — the module that owns the gating owns the shape too.
    # throwOut ships WITH the payload (as `throwOut` and as apply_payload's `suggestions`, both
    # flagged automatic:false) and the BOARD ignores it by contract — it is shown as a SUGGESTION
    # there and never registered. It is deliberately NOT filtered here as well: filtering in two
    # places is how two places drift, and the board is the one that owns the rule.
    try:
        shaped = _vault_retro().apply_payload(prop)
    except Exception as e:
        return {"ok": False, "why": "could not shape the proposal: %s" % str(e)[:160]}
    payload = json.dumps(dict(shaped, owned=owned, unsure=unsure, throwOut=throw,
                              source="vault-accumulator"))
    js = ("(function(){try{if(typeof window.vaultAccumApply!=='function')return JSON.stringify("
          "{ok:false,why:'this board build has no vaultAccumApply — update the board'});"
          "var r=window.vaultAccumApply(%s);return JSON.stringify({ok:true,applied:r});}"
          "catch(e){return JSON.stringify({ok:false,why:String(e&&e.message||e)})}})()") % payload
    try:
        raw = _ejs(w, js, timeout=8.0)
    except Exception as e:
        return {"ok": False, "why": "the board refused the apply: %s" % str(e)[:160]}
    if not raw:
        # _ejs returns None on timeout — and a timeout is NOT a success. Saying so is the point:
        # the apply may or may not have landed, and he needs to go look rather than be told it worked.
        return {"ok": False, "why": "the board did not answer in time — the apply may or may not have "
                                    "landed; check THE VAULT before retrying"}
    try:
        return json.loads(raw)
    except Exception:
        return {"ok": False, "why": "the board answered something unreadable"}


def _jsq(s):
    """Single-quoted JS string literal — kept single-quoted so the emitted tally JS is
    byte-identical to the two hand-written copies this helper replaced."""
    return "'" + str(s).replace("\\", "\\\\").replace("'", "\\'") + "'"




def _chron_lanes():
    """The readers this machine can actually use, named honestly.

    A lane that is missing is REPORTED missing rather than silently skipped — "claude only" and
    "both lanes agreed" are different confidences, and the gate scores them differently."""
    # v1711 — UNDER TV_STUB THE MANIFEST DECLARES THE LANES, NOT THIS MACHINE.
    # has_subscription() asks whether a Grok CLI is logged in HERE. On Konyo's Mac it is, so the
    # stubbed sweep tests saw a grok lane; on a CI runner it is not, so the same fixture produced
    # no lane, no "cross-lane" witness, and test_the_lane_that_DISAGREED_shows_in_the_witness_list
    # failed with 'cross-lane' not found — green on his machine, red on the runner, with the code
    # innocent both times. A stubbed test whose verdict depends on live machine state is not
    # testing the stub.
    # The manifest already names its lanes explicitly ("*#chronicle" / "*#chronicle-grok"), so in
    # stub mode it is the honest source. This CANNOT weaken the real path: it is fenced behind
    # TV_STUB, and a silent grok lane still reads as silence — never as agreement — which
    # test_a_SILENT_grok_lane_never_reads_as_agreement holds by dropping the key entirely.
    if os.environ.get("TV_STUB") == "1":
        man = {}
        try:
            with open(os.environ.get("TV_STUB_MANIFEST") or "", encoding="utf-8") as fh:
                man = json.load(fh) or {}
        except Exception:
            man = {}
        stub = ["claude"]                       # the primary is what the stub sweep is built on
        if any(str(k).endswith("#chronicle-grok") for k in man):
            stub.append("grok")
        return stub

    lanes = []
    try:
        import tv_diablo as _tv
        if hasattr(_tv, "claude_chronicle_read"):
            lanes.append("claude")
    except Exception:
        pass
    try:
        import g5_grok_eyes as _g5
        if hasattr(_g5, "g5_chronicle_read") and _g5.has_subscription():
            lanes.append("grok")
    except Exception:
        pass
    return lanes


# v1763 — A SWEEP THAT IS NOT WRITTEN DOWN DID NOT HAPPEN.
#
# _CHRON_JOB and _CHRON_LAST_PROPOSAL are module globals, so a completed sweep lived only in the
# memory of the process that ran it. Measured on his own console: the retro sweep read 1070 frames,
# found 30 names, and after a restart the state was {"phase": "idle", "held": 0} and apply answered
# "no sweep result to apply — run a sweep first". The findings were gone.
#
# That is worse than not sweeping, because the SWEPT MARKER is durable while the RESULT was not: the
# reel is recorded as done, is never read again, and the names it held are lost. Automation that can
# spend money, discard the answer, and then decline to look again is not automation.
#
# The result now lands on disk the moment a sweep finishes and is reloaded on demand, so a restart —
# or a console that was never open when the watchdog fired — still has something to apply.
# v1776 — THE EVIDENCE OUTLIVES THE SWEEP THAT FOUND IT.
# _CHRON_JOB["result"] is ONE slot, so every sweep replaced the last one's findings. Konyo watched
# it twice in an hour — a five-reel run wiped by the watchdog's own tick — and named it exactly:
# "the progress is going up and then reversing". The watchdog is not the fault; a single slot is.
# Worse than the display: sightings could only corroborate INSIDE one run, so `cross-reel` (a name
# in two recordings) could not fire unless both reels were in the same sweep. Read one reel tonight
# and another tomorrow and the gate sees two lonely sightings. That is most of why nothing grounded
# without Grok. The vault path has accumulated since v1533; the chronicle path never did.
_CHRON_EVIDENCE_PATH = (os.environ.get("TV_CHRON_EVIDENCE")
                        or os.path.join(_fixture_root_for_state(), "chron_evidence.json"))


def _chron_evidence_load():
    """v1779 — AN UNREADABLE LEDGER IS NOT AN EMPTY ONE. This returned {} on any exception, and
    _chron_evidence_merge then merged the current run into {} and saved THAT as the whole
    accumulated ledger — so one torn read silently deleted every sighting ever collected. His file
    holds 106 names and is the only thing making cross-reel corroboration possible; the reels those
    sightings came from are sealed, so the only way back is a forced re-read of his whole history.
    Found by an adversarial review, reproduced on a truncated file: 2 names/670 pages -> 1 name/3.

    A parse failure now RAISES, so the merge leaves the file alone rather than overwriting it."""
    try:
        with open(_CHRON_EVIDENCE_PATH, encoding="utf-8") as fh:
            return json.load(fh) or {}
    except FileNotFoundError:
        return {}


# v1801 — A LEDGER-WRITE FAILURE IS HISTORY, AND A LATER SUCCESS DOES NOT UNMAKE IT.
# v1800 kept ONE slot and cleared it to None on every success. But _chron_autoread_loop fires visit
# sweeps on a timer, and each one saves: so a retro sweep whose write FAILED — its sightings gone
# for good, because _chron_evidence_merge rebuilds `base` from the file every run and they never
# reached it — was erased from the record seconds later by an unrelated tick that happened to
# succeed. The board would then report evidenceSaved:true and the loss would be unrecorded. The
# failures accumulate instead; only an explicit reset clears them, and nothing calls one. Zero
# failures and "not attempted" stay distinguishable via evidenceWrites. [[unknown-stays-unknown]]
_CHRON_EVIDENCE_FAILS = []     # bounded ring of recent failures: [{"ts": epoch_ms, "err": str}]
_CHRON_EVIDENCE_FAILCOUNT = 0  # v1804 — MONOTONIC. len(the ring) is NOT the count; see below.
_CHRON_EVIDENCE_WRITES = 0     # successful writes, so 0/0 cannot read as "all good"
_CHRON_EVIDENCE_LAST_OK = None # v1801 — did the MOST RECENT attempt succeed? None = none yet.
#
# v1801 — WHY THREE FIELDS AND NOT ONE FLAG. The first version published
# `evidenceSaved = not FAILS`, which can never return to true inside a process because nothing
# resets the list. One transient failure — a momentarily full disk, a .tmp clobbered by a backup,
# an EINTR — would pin a red present-tense "the evidence ledger did not save" on his screen for
# the rest of the daemon's uptime, days, while every subsequent write succeeded. A permanent alarm
# is not a strict alarm; it is furniture, and it teaches him to ignore the next real one, which is
# the same trap as a permanently-red CI gate.
#
# So the HEADLINE tracks the last attempt (present tense, and it can recover) while the HISTORY is
# still append-only (a write that failed lost sightings for good, and that stays on the record).
# The timestamp rides along because a failure with no age is a [[stale-reading]] defect on the one
# surface whose whole job is reporting loss — "it failed" and "it failed three weeks ago" are
# different facts and only one of them is worth acting on tonight.


def _chron_evidence_save(prop):
    """Takes NO lock, and does not need one.

    v1801 — THE OLD DOCSTRING SAID "callers hold _CHRON_LOCK" AND THAT WAS SIMPLY UNTRUE: measured,
    neither call site (_chron_evidence_merge, and the hunt) is inside a `with _CHRON_LOCK` block.
    A false claim about locking is worse than none, because the next person to add a caller reasons
    from it — either taking the lock and deadlocking against a real holder, or omitting it on the
    strength of a guarantee nobody provides. The writes are atomic by tmp+os.replace, which is what
    actually makes concurrent saves safe here.
    """
    global _CHRON_EVIDENCE_WRITES, _CHRON_EVIDENCE_LAST_OK, _CHRON_EVIDENCE_FAILCOUNT
    try:
        # v1900 — MAKE THE PARENT (v1899's class). These are the BANKED PAGES: the most expensive
        # bytes the console holds, because every one of them was paid for by a real read.
        try:
            os.makedirs(os.path.dirname(_CHRON_EVIDENCE_PATH) or ".", exist_ok=True)
        except Exception:
            pass
        tmp = _CHRON_EVIDENCE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(prop, fh)
        os.replace(tmp, _CHRON_EVIDENCE_PATH)
        _CHRON_EVIDENCE_WRITES += 1
        _CHRON_EVIDENCE_LAST_OK = True
        return True
    except Exception as e:
        # v1799 — SAY SO. This returned False into a caller that ignores it, so when v1798 made the
        # merged proposal un-serializable the ledger stopped being written and NOTHING on any surface
        # changed: the sweep reported success, the console showed its findings, and the accumulated
        # evidence silently froze. A write that can fail must be audible even when its return value
        # is dropped — silence is not evidence that it worked.
        # v1800 — AND STDOUT IS NOT A SURFACE HE READS. v1799 made this audible only to a
        # terminal nobody watches, while BOTH call sites still drop the boolean, so the ledger
        # could still freeze with every screen reporting success. The failure now rides on a
        # module global that the sweep result carries to the board, which is the only place the
        # claim "this sweep accumulated" is actually made. [[the-unjoined-end]]
        print("   \u26a0 chronicle evidence NOT saved (%s) \u2014 the ledger did not accumulate this run" % e)
        _CHRON_EVIDENCE_FAILS.append({"ts": int(time.time() * 1000),
                                      "err": str(e) or e.__class__.__name__})
        # v1801 — BOUNDED. A systematic failure (v1798's set-in-the-proposal made EVERY dump raise)
        # plus a 20s autoread tick is ~4,300 records a day, forever. Keep the first few — the ones
        # that say when it started — and a sliding tail, which is every semantic the payload uses.
        # v1804 — THE COUNT AND THE RING ARE DIFFERENT THINGS, and v1801 published len(ring) as
        # the count. The trim caps the ring at ~105 entries, so under the systematic failure this
        # was built for (v1798: every dump raises) with a 20s autoread tick — ~4,300 failures a
        # day — the console would have printed "105 failed writes" as a fact, forever, while the
        # real number climbed past four thousand. The bound is a memory decision; the count is a
        # measurement, and a bound must never silently become the answer.
        _CHRON_EVIDENCE_FAILCOUNT += 1
        if len(_CHRON_EVIDENCE_FAILS) > 200:
            del _CHRON_EVIDENCE_FAILS[5:len(_CHRON_EVIDENCE_FAILS) - 100]
        _CHRON_EVIDENCE_LAST_OK = False
        return False


# ── THE RE-READ CAP ──────────────────────────────────────────────────────────────────────
# Konyo, 2026-08-20: "it shouldnt even re-read them again like after third read it should be
# blocked..? safegaurd?"
#
# He is right, and the A→Z reel is the proof: 16 pages re-read for ONE name not already in the
# ledger. Nothing stopped a frame being read again on every sweep forever, so a reel that has
# given up everything it holds still costs full price each time it is looked at.
#
# WHY THE COUNT LIVES HERE AND NOT IN THE EVIDENCE. A sighting is keyed (reel, frame, lane) and
# DEDUPES, so the evidence cannot tell one read from three — that is v1836's whole point, and it is
# right for evidence. A read COUNT is the opposite kind of number: it must not be idempotent. So it
# is kept in its own small file, incremented when a read actually happens, never merged.
#
# KEYED BY PROMPT_VER, so the cap can never fight v1830. A new reader is the one legitimate reason
# to look at a frame again — the whole reason those eight reels reopened — and a change of prompt
# starts every frame's count from zero.
_CHRON_READ_CAP = int(os.environ.get("TV_CHRON_READ_CAP") or 3)


def _chron_reads_path():
    """THE COUNTER BELONGS TO THE FOOTAGE, exactly like the sweep lock (v1832).

    First cut hardcoded HERE/chron_reads.json and immediately wrote into his live tv/ from the test
    suite — the same defect v1832 fixed for .sweep.lock, repeated by me within the hour of fixing
    it. It also broke four sweep tests outright, because they shared one counter across runs and the
    third run found itself capped.

    That is the argument for deriving state paths from TV_HIST rather than remembering to: a rule
    kept by memory is the rule that already failed. With TV_HIST unset — production, his real reels
    — the path is byte-identical to what it would have been.
    [[feedback-fixtures-never-touch-live-data]]
    """
    env = os.environ.get("TV_CHRON_READS")
    if env:
        return env
    hist = os.environ.get("TV_HIST")
    if hist:
        return os.path.join(hist, "chron_reads.json")
    return os.path.join(HERE, "chron_reads.json")


def _chron_reads_load():
    try:
        with open(_chron_reads_path(), encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _chron_reads_save(rec):
    try:
        _p = _chron_reads_path()
        tmp = _p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(rec, fh)
        os.replace(tmp, _p)
    except Exception:
        pass


def _chron_read_count(reads, prompt_ver, reel, frame):
    return int(((reads or {}).get(str(prompt_ver)) or {}).get("%s|%s" % (reel, frame)) or 0)


def _chron_read_bump(reads, prompt_ver, reel, frame):
    # `reads or {}` would be a BUG here and was one: an empty dict is FALSY, so the very first
    # bump — the case where reads IS {} — setdefault'd into a throwaway and the count stayed 0
    # forever. Caught by its own guard before it shipped, which is the entire reason to write one.
    if reads is None:
        reads = {}
    per = reads.setdefault(str(prompt_ver), {})
    k = "%s|%s" % (reel, frame)
    per[k] = int(per.get(k) or 0) + 1
    return per[k]


def _chron_read_bump_if_read(reads, prompt_ver, reel, frame, out):
    """Spend one of this frame's three looks — but ONLY if the reader actually looked.

    v1861. `_read_one` bumped unconditionally, under a comment that said it did not: "bump only
    when a read was really attempted — a throttled or capped page must not burn one of its three
    looks." The CAPPED case returned early so it was safe; THROTTLED and BUDGET-BLOCKED fell
    through. claude_chronicle_read answers those two with {"note": "reader throttled — not read"}
    and {"note": "not read — <why>"} and reads nothing, so three throttled sweeps would retire a
    page nobody had ever read — and the cap message would then tell him to re-read it "by changing
    the reader", about a page the reader never saw.

    `note` is set by exactly those two refusals (both early returns in tv_diablo.claude_chronicle_read)
    and by nothing a real read produces, so its presence IS "not read". A lane that returns None —
    a dead reader — is also not a read.

    Returns True when a look was spent. Lives at module level, and takes `out` rather than deciding
    inside a closure, so it can be driven by a test; the version that could not be was wrong for
    two ships. [[the-unjoined-end]]
    """
    if out is None or (isinstance(out, dict) and out.get("note")):
        return False
    _chron_read_bump(reads, prompt_ver, reel, frame)
    return True


def _chron_read_capped(reads, prompt_ver, reel, frame, cap=None):
    """Has this frame already been read `cap` times under THIS reader? Returns a refusal note or None.

    A refusal, never a silence: it comes back in the shape chronicle_retro already understands as
    "not read", so the page is reported and counted rather than quietly vanishing. A skip nobody can
    see is the defect this repo keeps re-finding.
    """
    cap = _CHRON_READ_CAP if cap is None else cap
    if cap <= 0:
        return None
    n = _chron_read_count(reads, prompt_ver, reel, frame)
    if n < cap:
        return None
    return {"note": "read-cap — %d reads under %s already, and the reader has not changed since"
                    % (n, prompt_ver)}



_GATE_BROKE = {"n": 0, "said": False}


def _gate_broke(where, exc):
    """The stash gate FAILED rather than refused — say it once, loudly enough to be found.

    v1854 — prep_tab_chrome proved what silence costs here: 310 versions of every caller reading
    "None" as an answer about his footage when it was really an answer about a NameError. The count
    is kept so a status surface can report it; the print fires once so a broken gate cannot drown
    the log it is trying to warn in.
    """
    _GATE_BROKE["n"] += 1
    if not _GATE_BROKE["said"]:
        _GATE_BROKE["said"] = True
        print("   \u26a0 the stash template gate FAILED (%s: %s) — it is refusing frames because it "
              "cannot run, not because they are not stash screens" % (where, str(exc)[:120]))


def gate_failures():
    """How many times the stash gate broke this process. 0 means it ran; it never means 'unknown'."""
    return int(_GATE_BROKE["n"])


# v1864 — how often the tab-chrome OCR came back with NOTHING, against how often it came back with
# something. Two numbers rather than one, because a run where every single probe is silent is an OCR
# lane that is down, and a run where most are silent and some are not is ordinary gameplay footage.
# One number could not separate those and the gate would keep answering "not a stash" either way.
_GATE_SILENT = [0]
_GATE_HEARD = [0]


def gate_hearing():
    """(silent, heard) for this process — the tab-chrome OCR's own audibility, not a verdict."""
    return (_GATE_SILENT[0], _GATE_HEARD[0])


# ── v1941 — THE GATE VERDICT IS CACHED, BECAUSE A SEALED FRAME NEVER CHANGES ──────────────────
#
# Konyo clicked the Vault Accumulator and got "grouping frames…" forever. It is not an infinite
# loop — it is arithmetic. vault_scan_cost() probes EVERY frame through stash_screen_open(), and
# that gate is a crop plus an OCR. MEASURED on his own film, 2026-08-21: 0.118s per call across
# 3749 frames in 1065 sealed reels = ~7.4 MINUTES, single threaded, with no progress and no
# timeout, behind a button whose own label says "tap to price it · costs nothing".
#
# "Costs nothing" was only ever about MONEY. It cost seven minutes of his evening instead.
#
# The frames are sealed reels — immutable by construction — so the verdict for a given file can
# never change, and re-deriving it on every quote is pure waste. Keyed on (size, mtime) as well as
# path so that if a frame ever IS rewritten the memo misses rather than lying: a stale "stash"
# would misroute a real read, and vault_retro says what that costs in its own words — "a rune tab
# misread as 'inventory' files his runes in the wrong lane, which merge-max then makes permanent."
# A cache that can be wrong about THAT is worse than no cache, so the guard is cheap and total.
_GATE_CACHE_PATH = (os.environ.get("TV_GATE_CACHE")
                    or os.path.join(_fixture_root_for_state(), "stash_gate_cache.json"))
_GATE_CACHE = None
_GATE_CACHE_DIRTY = False
_GATE_LOCK = threading.Lock()


def _gate_cache():
    global _GATE_CACHE
    if _GATE_CACHE is None:
        try:
            with open(_GATE_CACHE_PATH, encoding="utf-8") as f:
                _GATE_CACHE = json.load(f)
            if not isinstance(_GATE_CACHE, dict):
                _GATE_CACHE = {}
        except Exception:
            _GATE_CACHE = {}
    return _GATE_CACHE


def _gate_cache_flush():
    """Write only when something changed, and never leave a half file behind."""
    global _GATE_CACHE_DIRTY
    with _GATE_LOCK:
        if not _GATE_CACHE_DIRTY or _GATE_CACHE is None:
            return
        try:
            d = os.path.dirname(_GATE_CACHE_PATH)
            if d and not os.path.isdir(d):
                os.makedirs(d, exist_ok=True)
            tmp = _GATE_CACHE_PATH + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(_GATE_CACHE, f)
            os.replace(tmp, _GATE_CACHE_PATH)
            _GATE_CACHE_DIRTY = False
        except Exception:
            pass


def stash_screen_open_cached(frame_path):
    """stash_screen_open(), memoised on (size, mtime). Same answer, ~0s on a second look."""
    global _GATE_CACHE_DIRTY
    try:
        st = os.stat(frame_path)
        key = frame_path
        sig = [int(st.st_size), int(st.st_mtime)]
    except Exception:
        return stash_screen_open(frame_path)
    c = _gate_cache()
    hit = c.get(key)
    if isinstance(hit, list) and len(hit) == 3 and hit[0] == sig[0] and hit[1] == sig[1]:
        return hit[2]
    val = stash_screen_open(frame_path)
    with _GATE_LOCK:
        c[key] = [sig[0], sig[1], val]
        _GATE_CACHE_DIRTY = True
    return val


def stash_screen_open(frame_path):
    """HARDCODED: is this frame actually the stash, with the panels open? Not a model's opinion.

    Konyo, 2026-08-20: "for vault manager and the items the AI reads from my reels... it needs to be
    hardcoded and safegauded for vault manager to only when maybe i CLICK stash and am in my stash
    with my inventory open at the same time thats the template it should start knowing to read
    whats in my inventory and stash and log it and ledger it accordingly".

    WHY THIS IS THE RIGHT GATE. A reel without a declared focus pays a model to say which ownership
    surface a frame shows, and vault_retro says in its own words what that costs when it is wrong:
    "a rune tab misread as 'inventory' files his runes in the wrong lane, which merge-max then makes
    permanent." Permanent is the operative word — it is why he opened the vault manager and found
    items he does not have. A structural check cannot be talked into an answer.

    The signal is the stash TAB CHROME, read by OCR out of a fixed band (stash_eye._TAB_CHROME) and
    resolved by tab_from_ocr_lines() to one of his real tabs. That chrome only renders when the
    stash panel is open — and D2R draws the inventory beside it whenever it is, which is the
    "both at the same time" template he described. No chrome, no vault read.

    Returns the tab name when the stash is open, or None. None means NOT A STASH FRAME — it does not
    mean an empty stash, and callers must not treat it as one.
    """
    try:
        import tv_diablo as _tvd
        from stash_eye import is_boot_screen
    except Exception as _imp:
        _gate_broke("import", _imp)
        return None
    try:
        # CROP AND UPSCALE FIRST. OCR of the whole frame is noise at this resolution — measured on
        # his own stash frame it returned five junk lines, one of which ("l*vpXYOkY") is INVENTORY
        # mangled. stash_eye exists for exactly this: the tab chrome "only becomes readable via a
        # deliberate crop + 3x upscale" (v947). Reading the full frame is how this gate came back
        # None for genuine stash frames on the first cut — a gate that always refuses.
        from stash_eye import prep_tab_chrome
        import tempfile as _tf
        crop = os.path.join(_tf.gettempdir(), "vault_gate_%d.jpg" % os.getpid())
        if not prep_tab_chrome(str(frame_path), crop):
            return None
        rd = _tvd.ocr_fast(crop) or {}
        lines = list(rd.get("raw_lines") or rd.get("lines") or [])
        if not lines:
            # v1864 — "THE STRIP WAS DARK" AND "THE OCR LANE ANSWERED NOTHING" LOOK IDENTICAL HERE.
            #
            # The crop was made, so there IS a picture; zero lines back means either a genuinely
            # blank strip (gameplay — 61 of his 68 grid-called stash frames, correctly refused) or
            # an OCR lane that could not run. The second is not a verdict about his stash, and it
            # is not hypothetical: this gate's own test went RED once during a run while his live
            # session held the OCR worker, and passed alone seconds later.
            #
            # The frame-level answer cannot tell them apart and stays None, which is the safe
            # direction. What CAN tell them apart is the RUN: if every frame a sweep probes comes
            # back silent, the lane is down, not his footage. So it is counted, and the counter is
            # read out at the end of a sweep. [[feedback-silence-is-not-evidence]]
            _GATE_SILENT[0] += 1
            return None
        _GATE_HEARD[0] += 1
        if is_boot_screen(lines):
            return None          # the reconnect splash is not a stash, however much text it carries
        # v1860 — ADMISSION COUNTS THE LABELS; IT DOES NOT ASK WHICH TAB IS SELECTED.
        #
        # This line was `tab = _tab_from_ocr_lines(lines); return tab or None`, and that asks the
        # WRONG QUESTION. tab_from_ocr_lines abstains on 2+ legible labels — correctly, because the
        # strip prints all five whichever is active — and the gate then read that abstention as
        # "not a stash frame". So the CLEAREST evidence his stash is open (four tab names printed
        # in one strip) refused exactly like an empty frame.
        #
        # MEASURED ON HIS OWN REELS, not reasoned: of 68 frames the grid fingerprint called a stash
        # panel, four had unmistakable chrome — ['$•NAL','SHAkED','% Gems','I mATeRIALS'] and
        # ['S*NAL','SHARED','g Gems','mATeRIALS'] among them — and the gate turned away all four.
        # [[the-unjoined-end]] — a gate built right and joined to the wrong question.
        #
        # The chrome renders ONLY when the panel is open, so one legible label is already proof and
        # four is overwhelming. Which tab is selected is a different question with a different
        # answer, it is a GUESS (v1859), and admission never needed it.
        from stash_eye import stash_chrome_canons, tab_from_gem
        canons = stash_chrome_canons(lines)
        if not canons:
            return None
        # ── v1913 — ONE LEGIBLE LABEL IS NOT A SELECTED TAB ────────────────────────────────────
        #
        # This branch was `if len(canons) == 1: return canons[0]`, and that is the same wrong
        # question v1860 fixed one line below it: the strip prints ALL FIVE labels whichever tab is
        # active, so how MANY of them the OCR happened to read is a fact about the OCR, not about
        # the selection. Reading exactly one means the other four were smudged, occluded or
        # mis-transcribed — nothing more.
        #
        # MEASURED ON HIS OWN HIST, all 883 frames: the gate admits 10, and it took this branch on
        # THREE of them. It was wrong on all three.
        #     5_1784984201581  canons ['gems']   (a WRAITHSTEP tooltip covers the rest) -> PERSONAL
        #     7_1784984245418  canons ['shared']                                        -> PERSONAL
        #     8_1784984208085  canons ['shared']                                        -> PERSONAL
        # All three are unmistakably on PERSONAL: gold box, blue gem, four grey labels beside it.
        #
        # ⚠ IT IS INERT TODAY AND THAT IS NOT A REASON TO LEAVE IT. All three callers test `is None`
        # and discard the value — because v1857 DID use it as a lane and v1859 had to revert that.
        # A function that returns a wrong-by-construction tab is a loaded gun waiting for the next
        # caller who does not read the comment. The value is truthful now instead of the discipline
        # being. [[label-outlived-referent]] [[the-unjoined-end]]
        #
        # THE GEM IS ASKED FIRST because it answers the question actually being asked. It is
        # structural (the game's own selected-state marker), it measured 12/12 on the hand-labelled
        # corpus with zero false tabs, and it ABSTAINS rather than guess — which is why 7_ and 8_
        # above come back "stash" here rather than a confident wrong answer.
        _gem, _gd = tab_from_gem(str(frame_path))
        if _gem:
            return _gem
        return "stash"
    except Exception as _e:
        # v1854 — A GATE THAT CANNOT RUN MUST NOT ANSWER "NO".
        #
        # This function is shaped exactly like prep_tab_chrome was: a bare handler returning a
        # plausible value. That is how prep_tab_chrome stayed dead for 310 versions — every caller
        # read None as "not a stash panel" when the truth was "this never ran". Written by me
        # yesterday, one day after diagnosing that exact failure.
        #
        # The answer stays None, because the safe direction for a gate is to refuse. What changes
        # is that it is no longer SILENT: a gate that is failing rather than refusing says so, once
        # per process, so a permanent breakage cannot look like a quiet stretch of gameplay.
        _gate_broke("read", _e)
        return None


def _stamp_math_broke(where, exc):
    """The find-date arithmetic FAILED rather than found nothing — say so.

    v1855 — REG-200's law applied to code I wrote the same day I filed it: `except Exception:
    _fresh = []` makes a broken comparison indistinguishable from "he found nothing new", which is
    the single thing this feature exists to tell him. Third time in one day I have written the
    silent-plausible-value shape after diagnosing it, which is the argument for saying it out loud
    rather than trusting myself to remember.
    """
    print("   \u26a0 the find-date comparison FAILED (%s: %s) — 'nothing new' below is NOT an "
          "answer about his grail" % (where, str(exc)[:120]))


# v1859 — `_VAULT_TAB_SURFACE` lived here and is GONE. v1857 used it to name the ownership
# surface from the tab the gate had read, saving a model call. stash_eye calls that tab an
# "Active-tab GUESS" in its own docstring, and on his frame 5_1784984201581.jpg it answered
# "gems" for a RUNES panel — so the reader was asked the wrong question and returned zero
# items from a full stash. A guess may gate ADMISSION (v1850, still sound); it may never
# name a LANE. [[label-outlived-referent]]


def _chron_evidence_merge(prop):
    """Fold this sweep's proposal into everything read so far, persist, and return the MERGED view.

    The gate then runs over every sighting ever collected rather than just this run's, which is what
    makes a sweep additive instead of destructive.
    """
    try:
        import chronicle_retro as _cr   # imported per-callsite in this module, not at import time
        base = _chron_evidence_load()
    except Exception as e:
        # the ledger exists but will not parse: keep it, say so, and do NOT overwrite it with a
        # single run's findings dressed up as the whole history
        print("   ⚠ accumulated evidence unreadable (%s) — NOT overwriting it this run" % e)
        return prop or {}
    try:
        merged = _cr.merge_proposals(base, prop or {})
    except Exception:
        return prop or {}
    _chron_evidence_save(merged)
    return merged


def _chron_fold(prop):
    """Fold a proposal's unique names onto the board's own roster BEFORE the gate counts witnesses.

    v1789. Measured on his live ledger the day this shipped: the gate counted witnesses on RAW
    strings, so two spellings of one item never combined and 36 names sat in his inbox awaiting a
    hand-tick. Only SIX were unresolved uniques. Six were OCR slips of items ALREADY grounded
    ("Battlecage" for Rattlecage, "Naglring" for Nagelring, "Heart Garver" for Heart Carver,
    "Twitchthrow" for Twitchthroe, "Gravepalms" for Gravepalm) — the same row read twice, asking him
    to adjudicate a question the ledger had already answered. The other 24 were reader debris: base
    names the Chronicle prints for an UNFOUND row (Bone Visage, Templar Coat, Wrist Sword) and
    tooltip-truncated fragments (Firel..., Natalya's..., "Heavas (partially obscured)").

    Folding is applied HERE, at gate time, and never to the stored evidence. The raw sighting is the
    receipt — what the reader actually said, in the frame it said it — and rewriting it would destroy
    the only record that can be re-judged when the roster or the fold rule changes. So the ledger
    keeps the reader's words and the gate reads the roster's.

    It also repairs a silent miss: a grounded name that is not a ROSTER name can never tick. The
    ledger held "Latent Black Cleft"; the roster holds "Black Cleft"; bible.html's own
    d2rResolveItem returns "Latent Black Cleft" UNCHANGED (verified live over CDP on 2026-08-18).
    The reel found the item, the ledger grounded it, and the board could not count it.

    On any failure this returns the proposal UNTOUCHED. A roster that will not load must degrade to
    the old raw-name behaviour, never to an empty roster — folding against {} would classify every
    name as debris and silently empty his queue, which is the worst outcome wearing the tidiest face.
    """
    try:
        import chronicle_resolve as _res
        roster = _res.load_roster()
        # v1795 — SETS FOLD TOO, against their OWN roster. Uniques got the fold in v1789 and sets got
        # nothing, so a misread set piece stayed a separate name with one witness forever, exactly as
        # "Battlecage" did before the uniques fold. Each ledger is asked of its own catalogue: folding
        # a piece against the unique roster would resolve every one to nothing and silently retire the
        # whole sets ledger as debris.
        try:
            set_roster = _res.load_set_roster()
        except Exception as _se:
            print("   \u26a0 set roster unavailable (%s) \u2014 folding uniques only" % _se)
            set_roster = None
        folded, report = _res.fold_proposal(prop or {}, roster,
                                            ledgers=("uniques", "sets") if set_roster else ("uniques",),
                                            set_roster=set_roster)
    except Exception as e:
        print("   \u26a0 roster fold unavailable (%s) \u2014 gating on raw reader names" % e)
        return prop or {}, {"folded": {}, "retired": [], "kept": 0, "error": str(e)}
    return folded, report


# v1789 — how many held names one sweep may hunt. Bounded on purpose: each name costs up to
# chronicle_hunt.MAX_PER_NAME reads, so an unbounded hunt over a bad sweep could spend hours of his
# subscription chasing reader debris. The fold already retires the debris; this budget is what stops
# the remainder from becoming open-ended.
_CHRON_HUNT_MAX_NAMES = int(os.environ.get("TV_CHRON_HUNT_NAMES") or 8)


def _chron_calibration(reel_dirs):
    """THE SAFEGUARD HE ASKED FOR: put the game's own number beside the board's, every sweep.

    Konyo, 2026-08-21: "and sets.. are you sure its 118/135 how is it 87%? ingame im 85%" — and then
    the harder question — "the AI READERS needs to be doing this automatically ... where is the AI
    intelligence and AI coder that routes and funnels and watchdog even for a safegaurd of this?"

    He was right that it did not exist. Every Chronicle page carries a completion bar, the readers
    have been photographing it for months, and NOTHING ever compared it to the board's tally. Two
    numbers about one collection, computed by different routes, never put side by side — which is
    the single arrangement that turns a silent drift into a finding.

    WHAT IT COST TO NOT HAVE THIS: his board read 118/135 = 87.4% while the game printed 85%. His
    own two sentences settled it — "this is exactly 19 i still have missing" and "meaning i have
    116/135" — 116 + 19 = 135, and 116/135 = 85.9%, which the game truncates to 85. So the board was
    counting TWO pieces he does not have, and had been for long enough that he noticed it by eye
    before any gate did.

    TWO INSTRUMENTS, AND THE SHARP ONE RUNS FIRST. v1920 shipped only the bar reader and made a
    mistake worth carving: it returned early whenever no completion bar was photographed, so the
    EXACT check was skipped because the APPROXIMATE one was unavailable. They are independent —

      counter_ledger  EXACT and it NAMES. Needs a recorded Remaining page and the board; needs no
                      bar, no frames, no model. 116 + 19 = 135 closes the account, and any board row
                      inside the game's own missing list can be named outright.
      chronicle_calibrate  ±1.5 points and anonymous. Needs only frames — so it still speaks when no
                      Remaining page has ever been recorded, which is most of the time.

    Both run. Where they disagree the disagreement IS the finding and is reported as one, rather
    than averaged or resolved in favour of whichever is more convenient.

    ⚠ THE BAR READER IS A WATCHDOG, NOT A COUNTER (±1.5 points; chronicle_calibrate says so in its
    own docstring). It exists to catch a 3-point disagreement, and it must never be quoted as the
    figure. A refusal — no bar on any frame — is reported as UNKNOWN, never as agreement, because
    "the game said nothing" and "the game agreed" are different facts. [[unknown-stays-unknown]]
    """
    out = {"ok": None, "say": "not attempted"}
    total = 0
    try:
        import chronicle_resolve as _res
        total = len(_res.load_set_roster() or {}) or 0
    except Exception:
        total = 0

    # THE BOARD, WITH NAMES. v1920 asked for sample=0 and got counts only, so it could report THAT
    # two rows were wrong and never WHICH — the question he actually asked. The ledger is 135 rows
    # at most; asking for all of them costs one evaluate.
    own, own_why = {}, None
    try:
        own = board_ownership(400) or {}
        if not own.get("ok"):
            own_why = str(own.get("why"))[:110]
            own = {}
    except Exception as e:
        own_why = str(e)[:110]
        own = {}
    board_found = int((own.get("counts") or {}).get("setPieces") or 0) if own else 0
    board_names = ((own.get("sample") or {}).get("setPieces") or []) if own else []

    # 1. THE EXACT ONE.
    exact = None
    try:
        import counter_ledger as _cl
        if own:
            exact = _cl.arithmetic(board_found, total)
            named = _cl.contradicted(board_names)
            if named.get("reading"):
                exact["named"] = named.get("contradicted") or []
                exact["laterFinds"] = named.get("laterFinds") or []
                exact["namedSay"] = named.get("say")
            # ⚠ THE ARITHMETIC AND THE NAMES CAN DISAGREE, and that is informative rather than a
            # bug: the surplus counts rows the board should not hold, while the names find rows the
            # board holds that the game explicitly denies. A surplus with no names means the wrong
            # rows are pieces the game did not list at all — a DIFFERENT defect, and the reader
            # should be told which one it is looking at instead of being handed one number.
            if exact.get("ok") is False and exact.get("surplus", 0) > 0 and not exact.get("named"):
                exact["say"] += (" ⚠ None of them are on the game's missing list, so the surplus is "
                                 "not a piece he was wrongly credited with — it is a row the "
                                 "catalogue itself does not recognise.")
        else:
            r = _cl.load("sets")
            # The phrase "did not answer" is load-bearing: TestTheGameIsAskedItsOwnNumber pins it,
            # because the whole point of this branch is that a board which cannot be asked must be
            # REPORTED as unasked rather than quietly counted as agreeing.
            exact = {"ok": None, "say": (
                "the board did not answer (%s), so the exact check did not run%s"
                % (own_why or "no reason given",
                   "" if r else " — and no Remaining page has ever been recorded either"))}
    except Exception as e:
        exact = {"ok": None, "say": "counter_ledger unavailable: %s" % str(e)[:110]}
    out["exact"] = exact

    # 2. THE APPROXIMATE ONE — independent, and it speaks even with no Remaining page on file.
    fill, n = None, 0
    try:
        import chronicle_calibrate as _cal
        for d in (reel_dirs or []):
            try:
                f, cnt = _cal.read_reel(d)
            except Exception:
                f, cnt = None, 0
            if f is not None:
                fill, n = f, cnt
                break
    except Exception as e:
        out["bar"] = {"ok": None, "say": "chronicle_calibrate unavailable: %s" % str(e)[:110]}
        _cal = None
    if fill is None:
        out.setdefault("bar", {"ok": None, "say": (
            "no completion bar on any swept frame — the game's bar was not asked, which is not the "
            "same as the game agreeing")})
    elif own:
        out["bar"] = _cal.verdict(fill, board_found, total)
        out["bar"]["frames"] = n
        out["gameFill"] = round(fill, 4)
        out["frames"] = n
    else:
        out["bar"] = {"ok": None, "gameFill": round(fill, 4), "frames": n, "say": (
            "the game's bar reads about %.1f%%, and the board did not answer (%s) — so nothing is "
            "compared, and that is reported rather than assumed" % (fill * 100, own_why or "?"))}

    # 3. THE VERDICT — the sharp instrument leads, and a contradiction between them is surfaced.
    ranked = [v for v in (exact, out.get("bar")) if isinstance(v, dict) and v.get("ok") is not None]
    if not ranked:
        out["ok"] = None
        out["say"] = (exact or {}).get("say") or out.get("bar", {}).get("say") or "nothing measured"
        return out
    out["ok"] = all(v.get("ok") for v in ranked)
    parts = [v.get("say") for v in ranked if v.get("say")]
    if (exact or {}).get("ok") is not None and out.get("bar", {}).get("ok") is not None \
            and exact.get("ok") != out["bar"].get("ok"):
        parts.append("⚠ THE TWO INSTRUMENTS DISAGREE — the exact account and the game's own bar do "
                     "not tell the same story, and that disagreement is the finding, not something "
                     "to average away.")
    if (exact or {}).get("named"):
        parts.append("The rows to look at, by name: %s."
                     % ", ".join(h["name"] for h in exact["named"]))
    out["say"] = "  ".join(p for p in parts if p)
    return out



def _chron_hunt_held(prop, applied, hist_dir, read_page):
    """Go back and look again for the names the gate held, then re-gate with whatever came back.

    Konyo: "cant like an extra AI take care of it and cross reference it with specific and focused
    hunts for it to cross reference it here and automatically grail it.. and if it still cant then
    leave it for me to tick off."

    THIS IS THE JOIN. chronicle_hunt could target and read perfectly and still change nothing while
    nothing called it — a module built on both ends and never wired is the failure mode that has cost
    the most time on this project, and it is silent by construction.

    Returns (prop, applied, report). On any failure the ORIGINAL verdict is returned untouched: a
    hunt that breaks must never be able to un-ground a name the sweep already earned.
    """
    report = {"hunted": [], "found": {}, "reads": 0, "skipped": ""}
    try:
        import chronicle_hunt as _ch
        import chronicle_retro as _cr
    except Exception as e:
        report["skipped"] = "chronicle_hunt unavailable: %s" % e
        return prop, applied, report
    # ── v1917 — THE HUNT WAS BLIND TO THE LEDGER WHERE EVERY HELD NAME LIVES ──────────────────
    #
    # This filtered to `ledger == "uniques"`, and his last sweep held FORTY-ONE names of which
    # forty-one are SET PIECES and zero are uniques. So the report read "nothing was held" and the
    # hunt spent 0 reads while 41 corroborated-once pieces — Tancred's Skull at six sightings,
    # Aldur's Rhythm, Sander's Riprap — sat one witness short of grounding.
    #
    # Konyo asked for exactly this and it is what he was told he had: "for F-SETS it should cross
    # reference the items i still dont have ... JUST LIKE UNIQUES i remember we integrated this in
    # some way for it already". The integration existed and covered one of the two ledgers.
    #
    # Both ledgers now, each hunted in its own evidence and read with its own page kind — a sets
    # page is read as `chronicle-sets` or the reader is answering about the wrong list.
    held_by = {"uniques": [], "sets": []}
    for h in (applied.get("held") or []):
        led = h.get("ledger")
        if led in held_by and h.get("name"):
            held_by[led].append(h["name"])
    if not (held_by["uniques"] or held_by["sets"]):
        report["skipped"] = "nothing was held"
        return prop, applied, report
    # The cap is per ledger, not shared: a long uniques list must not starve the sets hunt of every
    # read, which is the shape that made this uniques-only in effect even after it stopped being so
    # in the filter.
    for led in held_by:
        held_by[led] = held_by[led][:_CHRON_HUNT_MAX_NAMES]
    report["hunted"] = held_by["uniques"] + held_by["sets"]
    found_by = {}
    try:
        with _CHRON_LOCK:
            _CHRON_JOB["phase"] = "hunting"
        for led in ("uniques", "sets"):
            if not held_by[led]:
                continue
            kind = "chronicle-sets" if led == "sets" else "chronicle-uniques"
            got = _ch.hunt(held_by[led], prop, hist_dir, read_page, kind=kind,
                           log=lambda m, _l=led: print("   \U0001f50e [%s] %s" % (_l, m)))
            if got:
                found_by[led] = got
    except Exception as e:
        report["skipped"] = "hunt failed: %s" % e
        return prop, applied, report
    if not found_by:
        return prop, applied, report
    # merge_proposals is what makes the new sightings ACCUMULATE rather than replace, and it is the
    # same path a second sweep takes — the hunt earns evidence, it does not get a private door.
    merged = _cr.merge_proposals(prop, found_by)
    _chron_evidence_save(merged)
    merged, _ = _chron_fold(merged)
    regated = _cr.apply_proposal(merged, {"uniques": [], "sets": []}, gate=_cr.strict_gate())
    report["found"] = {led: {k: len(v) for k, v in got.items()} for led, got in found_by.items()}
    return merged, regated, report


_CHRON_RESULT_PATH = (os.environ.get("TV_CHRON_RESULT")
                      or os.path.join(_fixture_root_for_state(), "chron_last_result.json"))
# v1895 — THE VAULT PROPOSAL DID NOT SURVIVE A RESTART, and the chronicle's has for versions.
# _VAULT_JOB is in-memory only: he sweeps his vault, closes the console, and the proposal is gone
# while the READS THAT PAID FOR IT are spent. The chronicle solved this in v1763 for the same
# reason — "a fresh process reports the LAST sweep, not 'idle, nothing here'".
# Same isolation rule as every other live-state file (v1867): an isolated TV_HIST takes it along.
_VAULT_RESULT_PATH = (os.environ.get("TV_VAULT_RESULT")
                      or os.path.join(_fixture_root_for_state(), "vault_last_result.json"))


def _chron_result_save():
    """Persist the finished sweep. Best effort and silent on failure: losing the cache must never
    take down the sweep that produced it.

    ⚠ TAKES NO LOCK, DELIBERATELY. Both call sites are already inside `with _CHRON_LOCK:` — the
    result is written and persisted in one breath so no reader can see a finished sweep that has
    not been saved. threading.Lock is NOT reentrant, so acquiring it here self-deadlocks: measured,
    it hung tv/test_control.py past 600s where it normally finishes in 24. Reading the dict without
    the lock is safe precisely because the caller holds it."""
    try:
        payload = {"result": _CHRON_JOB.get("result"),
                   "proposal": globals().get("_CHRON_LAST_PROPOSAL"),
                   "savedTs": int(time.time() * 1000)}
        if not payload.get("result"):
            return
        tmp = _CHRON_RESULT_PATH + ".tmp"
        # v1899 — MAKE THE PARENT, the same as the vault save. The suite's own output carried
        # "chronicle result NOT persisted ([Errno 2] No such file or directory: .../nodeadlock.json.tmp)"
        # repeatedly: an isolated result path whose directory does not exist means the sweep is not
        # persisted at all. Best-effort, exactly like the rest of this function.
        try:
            os.makedirs(os.path.dirname(_CHRON_RESULT_PATH) or ".", exist_ok=True)
        except Exception:
            pass
        # v1800 — NO `default=str`. It turned an unserializable value into its REPR instead of
        # raising: the exact v1798 defect (a set where a list belonged) would have been written as
        # the string "{'Foo', 'Bar'}" and reloaded as a name, silently corrupting the ledger rather
        # than failing loudly. A serializer that cannot fail cannot warn. [[unknown-stays-unknown]]
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        os.replace(tmp, _CHRON_RESULT_PATH)
    except Exception as e:
        print("   \u26a0 chronicle result NOT persisted (%s) \u2014 this sweep will not survive a restart" % e)


def _chron_result_load():
    """Rehydrate the last sweep into memory when this process has none. Returns True if it did."""
    try:
        if _CHRON_JOB.get("result"):
            return False
        # v1765 — REHYDRATION IS FOR "THIS PROCESS NEVER SWEPT", NEVER "THIS SWEEP FOUND NOTHING".
        # Caught by test_chronicle_chain on CI: a sweep the console REFUSED out loud (a visit whose
        # ledger was never read) left phase=error with no result of its own, so this function
        # helpfully filled it in from disk — handing back a PREVIOUS sweep's proposal under the
        # current sweep's error. The gate's words for it are exact: "a refused sweep must leave NO
        # proposal behind". v1765 wires the board to ADOPT a persisted proposal automatically, which
        # turns that stale read from a confusing status into a wrong write. A job that has run in
        # this process owns its own outcome, empty or not. [[stale-reading]]
        if _CHRON_JOB.get("startedTs") or _CHRON_JOB.get("error") \
           or _CHRON_JOB.get("phase") not in ("idle", "", None) or _CHRON_JOB.get("running"):
            return False
        with open(_CHRON_RESULT_PATH, encoding="utf-8") as fh:
            payload = json.load(fh) or {}
        res = payload.get("result")
        if not res:
            return False
        _CHRON_JOB["result"] = res
        _CHRON_JOB["phase"] = _CHRON_JOB.get("phase") or "done"
        # v1894 — WHEN was this proposal made. `restoredFrom` has been set here for versions and
        # rendered by nothing, so the console shows a proposal with no age at all: one made an hour
        # ago and one made last week look identical, and he acts on both the same way.
        #
        # It cost me an hour tonight in the most direct way possible. I read this file WHILE the
        # sweep that owns it was still running, reported "6 of 13 cleared, 28 sets" to him from the
        # PREVIOUS result, and the real answer — written at 00:47 — was 11 of 13 and 36 sets. A
        # reading carries the age of the thing it measured, not of the fetch. [[stale-reading]]
        _CHRON_JOB["restoredFrom"] = payload.get("savedTs")
        _CHRON_JOB["resultTs"] = payload.get("savedTs")
        if payload.get("proposal"):
            globals()["_CHRON_LAST_PROPOSAL"] = payload["proposal"]
        return True
    except Exception:
        return False


def chronicle_sweep_state():
    # v1763 — a fresh process reports the LAST sweep, not "idle, nothing here". "No sweep has run"
    # and "the process that ran it has restarted" are different facts and only one of them is true.
    _chron_result_load()
    with _CHRON_LOCK:
        st = dict(_CHRON_JOB)
    # v1784 — THE WATCHDOG'S REASONS WERE WRITE-ONLY. Both tick docstrings promise "a silent skip is
    # impossible to mistake for a clean run", and _CHRON_AUTOREAD["skipped"]/["reads"] are filled in
    # at six sites — then read by NOTHING: no route, no payload, no print, never persisted. So the
    # only production caller made a skip exactly what the docstring forbids, and after a restart a
    # visit retired for a named reason was byte-identical to one genuinely swept. Found by an
    # adversarial review of the watchdogs. They ride along here, in the state the console and the
    # board already read.
    try:
        st["autoreadSkipped"] = dict(_CHRON_AUTOREAD.get("skipped") or {})
        # v1844 — which reels a prompt change reopened, so the surface that shows the bill can show
        # the reason for it. Defaults to [] rather than being absent: "none were reopened" and "this
        # build does not report it" must not read the same.
        st["reopenedReels"] = list(_CHRON_JOB.get("reopenedReels") or [])
        # v1894 — the age travels with the result, always. A proposal with no timestamp is one he
        # cannot tell from a fresh one.
        st["resultTs"] = _CHRON_JOB.get("resultTs") or _CHRON_JOB.get("restoredFrom")
        st["resultFromDisk"] = bool(_CHRON_JOB.get("restoredFrom"))
        st["autoreadReads"] = int(_CHRON_AUTOREAD.get("reads") or 0)
        st["autoreadTries"] = dict(_CHRON_AUTOREAD.get("tries") or {})
    except Exception:
        pass
    # v1800 — AND THE LEDGER-WRITE FAILURE RIDES HERE TOO, for exactly the reason above. Both
    # callers of _chron_evidence_save drop its boolean, so a frozen ledger reported success on
    # every screen for an hour (v1798). This is the ONE door the board reads a sweep through, so
    # joining it here covers both the sweep path and the hunt path without a second stamp site
    # that the next path can forget. evidenceSaved is False ONLY after a real failure — never
    # None-as-False, because "not saved" and "not attempted" are different facts.
    # evidenceSaved is about the LAST attempt (so it can recover); evidenceFails is the history
    # (so a loss is never erased). None means no write has been attempted — not "fine".
    st["evidenceSaved"] = _CHRON_EVIDENCE_LAST_OK
    st["evidenceError"] = _CHRON_EVIDENCE_FAILS[-1]["err"] if _CHRON_EVIDENCE_FAILS else None
    st["evidenceFails"] = _CHRON_EVIDENCE_FAILCOUNT     # the measurement, not the ring's length
    st["evidenceWrites"] = _CHRON_EVIDENCE_WRITES
    # v1804 — THE AGE IS COMPUTED HERE, NOT IN THE BROWSER. v1801 shipped a server epoch and let
    # the page difference it against Date.now(). The console is served over HTTP and tv/ ships it
    # to the Windows PC, so any clock skew rendered as a wrong age — and the browser-side
    # Math.max(0, …) clamp turned a NEGATIVE skew into "just now" on the one surface whose entire
    # job is reporting data loss. Two clocks, one subtraction. [[stale-reading]]
    if _CHRON_EVIDENCE_FAILS:
        st["evidenceFailAgeS"] = max(0, int(time.time() - _CHRON_EVIDENCE_FAILS[-1]["ts"] / 1000.0))
    else:
        st["evidenceFailAgeS"] = None
    return st


def chronicle_sweep_start(hist_dir=None, limit=None, force=False, visit=None, reel_id=None):
    """Kick the background sweep. Refuses to start a second one — two sweeps over the same reels
    would double the spend and produce two proposals that each look like the whole truth."""
    with _CHRON_LOCK:
        if _CHRON_JOB["running"]:
            return {"ok": False, "why": "a sweep is already running", "state": dict(_CHRON_JOB)}
        lanes = _chron_lanes()
        if "claude" not in lanes:
            # Claude is PRIMARY. Without it there is no page for a second opinion to be about.
            return {"ok": False, "why": "the primary (Claude) lane is unavailable — nothing to sweep with"}
        _CHRON_JOB.update({"running": True, "startedTs": int(time.time() * 1000), "phase": "grouping",
                           "reelsDone": 0, "reelsTotal": 0, "classified": 0, "pagesRead": 0,
                           "result": None, "error": None, "lanes": lanes})
    if visit:
        threading.Thread(target=_chron_visit_run, args=(int(visit),),
                         daemon=True, name="tvd-chronicle-visit").start()
        return {"ok": True, "started": True, "lanes": lanes, "visit": int(visit)}
    threading.Thread(target=_chron_sweep_run, args=(hist_dir, limit, force, reel_id),
                     daemon=True, name="tvd-chronicle-sweep").start()
    return {"ok": True, "started": True, "lanes": lanes}


def _reel_for_frame_epoch(hist, epoch_ms, _cache={}):
    """Which sealed reel was recording at this instant? "" when it cannot be proven.

    v1825 — VISIT SIGHTINGS WERE ALL FILED UNDER THE REEL ID "hist". _chron_visit_run joins each
    journalled frame id straight onto the hist ROOT (the live agent writes those frames there, not
    into a reel), so sweep_frames' default reel_of — basename(dirname(path)) — returned the name of
    the hist directory itself. 15 sightings in his live ledger carry it.

    That is not cosmetic. witnesses() counts DISTINCT reels, so every visit he has ever swept
    collapses into one pseudo-reel: two genuinely separate sittings of the same item cannot
    corroborate each other, and a name that deserved cross-reel is held instead. It under-counts,
    which is the safe direction, but it is still wrong.

    The obvious repair — key them per visit — would be WORSE, and in the dangerous direction: the
    same frames later swept as a REEL would appear under two different keys and the sitting would
    corroborate ITSELF. That is precisely the fault v1824 closed one field over.

    So the only honest key is the reel that actually holds that moment, matched on the frame's own
    epoch against each reel's span. When no reel covers it the answer is "" and the caller keeps
    the old collapsed behaviour — an unproven independence is not independence.
    """
    key = os.path.abspath(hist)
    spans = _cache.get(key)
    if spans is None:
        spans = []
        try:
            import chronicle_retro as _cr
            for d in (_cr.reel_dirs(hist, newest_first=False) or []):
                idx = _cr.load_index(str(d)) or {}
                ts = [int(f.get("ts") or 0) for f in (idx.get("frames") or []) if f.get("ts")]
                if ts:
                    sid = idx.get("sessionId") or os.path.basename(str(d))
                    spans.append((min(ts), max(ts), sid))
        except Exception:
            spans = []
        _cache[key] = spans
    for lo, hi, sid in spans:
        if lo <= epoch_ms <= hi:
            return sid
    return ""


def _chron_visit_run(visit_ts):
    """v1527 — sweep ONE recorded in-game visit. Cheapest path in the whole arc: no classify stage,
    and only the distinct pages of a panel he already told us he was reading."""
    try:
        import chronicle_retro as _cr
        import tv_diablo as _tv
        try:
            import g5_grok_eyes as _g5
        except Exception:
            _g5 = None
        vis = None
        for v in (chronicle_visits(limit=40).get("visits") or []):
            if int(v.get("ts") or 0) == int(visit_ts):
                vis = v
                break
        if not vis:
            raise RuntimeError("that visit is no longer in the journal")
        if not vis.get("ledger"):
            # ★ the refusal. A visit whose ledger was never read cannot be swept: reading it as the
            # wrong ledger writes set pieces into his grail, and there is no second chance on that.
            raise RuntimeError("that visit's ledger was never read — it cannot be swept safely")
        kind = "chronicle-" + vis["ledger"]
        hist = os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")
        paths = []
        for fid in (vis.get("frames") or []):
            f = str(fid or "")
            p = os.path.join(hist, f if f.endswith(".jpg") else f + ".jpg")
            if os.path.isfile(p):
                paths.append(p)
        if not paths:
            raise RuntimeError("the frames from that visit are no longer on disk")
        # v1825 — give each frame its REAL reel, so a visit stops masquerading as the hist folder
        def _reel_of(path):
            base = os.path.basename(str(path))
            try:
                epoch = int(base.rsplit("_", 1)[-1].split(".")[0])
            except Exception:
                return os.path.basename(os.path.dirname(str(path)))
            sid = _reel_for_frame_epoch(hist, epoch)
            return sid or os.path.basename(os.path.dirname(str(path)))

        grok_lane = None
        if _g5 is not None and "grok" in (_CHRON_JOB.get("lanes") or []):
            grok_lane = lambda p, k: _g5.g5_chronicle_read(p, k)
        # v1779 — THE VISIT PATH HAD NONE OF THE PROTECTION THE REEL PATH GOT. v1774/v1775/v1778
        # gave _chron_sweep_run a breathe-then-refuse loop, a throttled/capped counter, and a rule
        # that such a run seals nothing. This path — the CHEAPER one the watchdog fires every 20s —
        # had none of it, and sweep_frames counts pagesRead as frames OFFERED, not read. Measured by
        # an adversarial review with the throttle open: four refusals came back, the result said
        # "4 pages read", phase done, error None, and _chron_autoread_mark retired the visit forever.
        # A refusal wearing data's clothes, on the path most likely to hit one.
        _v_refused = [0]

        def _visit_read(p, k):
            if _tv._is_throttled() or _tv._sub_budget_check("oneshot"):
                _v_refused[0] += 1
            return _tv.claude_chronicle_read(p, k)

        read_page = _cr.two_lane_reader(_visit_read, grok_lane)
        res = _cr.sweep_frames(paths, kind, read_page, reel_of=_reel_of)
        if _v_refused[0]:
            print("   🚦 %d visit read(s) refused (throttle/cap) — the visit is NOT retired"
                  % _v_refused[0])
        with _CHRON_LOCK:
            _CHRON_JOB["pagesRead"] = res["pagesRead"]
        prop = _cr.proposal_from_pages(res["pages"])
        # v1837 — KEEP THIS RUN'S REFUSALS SEPARATE FROM ALL TIME. `prop` becomes the MERGED,
        # cumulative proposal a line or two below, and the result then published `totals` (this run)
        # beside `refused` (every run, ever) as sibling keys with nothing saying so. Both numbers
        # true, each answering a different question.
        #
        # It cost real time tonight: I read a cumulative refused list as one pass's, concluded
        # v1827 had changed nothing and called a working fix a failure. If it misleads the person
        # who wrote it an hour after writing it, it will mislead him. [[label-outlived-referent]]
        _run_refused = list(prop.get("refused") or [])
        # v1846 — WHAT HE REGISTERED YESTERDAY vs WHAT IS NEW TODAY. Konyo asked for exactly this:
        # "date and timestamp related coding so they know what they registered yesterday and whats
        # new today". The First Found stamps have been captured since v1819 and NOTHING has ever
        # compared two of them, so the ledger knew every find-date and still could not say which
        # were new. Read the high-water mark BEFORE the merge — after it, this run's finds are
        # already folded in and every one of them looks old.
        try:
            _prev_newest = _cr.newest_stamp(_chron_evidence_load())
        except Exception as _se:
            _stamp_math_broke("high-water mark", _se)
            _prev_newest = None
        # v1562 — the LIVE-VISIT path never stored its evidence, so "⚖ tune the gate" appeared
        # (control_ui reveals it on any result) and could only answer "no sweep evidence in memory
        # — run a sweep first". v1550 wired the retro path only.
        # This is the path that needs it MOST: one visit is one reel, often one lane, so it has the
        # fewest witnesses per name and is exactly where names get HELD — and re-gating at
        # minWitnesses=1 is the intended remedy. The one path where the remedy was unreachable.
        # v1776 — GATE OVER EVERYTHING READ SO FAR, not just this run. Merging here is what makes a
        # sweep additive: the next one can only ADD sightings, never wipe the last one's, and a name
        # seen in a reel swept tonight can finally corroborate one seen in a reel swept tomorrow.
        prop = _chron_evidence_merge(prop)
        try:
            _fresh = _cr.newly_dated(prop, _prev_newest)
        except Exception as _se:
            _stamp_math_broke("newly-dated", _se)
            _fresh = []
        if _fresh:
            print("   \U0001f195 %d find(s) newer than anything read before: %s"
                  % (len(_fresh), ", ".join("%s (%s)" % (r["name"], r["foundAt"]) for r in _fresh[:4])))
        globals()["_CHRON_LAST_PROPOSAL"] = prop
        # v1789 — FOLD ONTO THE ROSTER BEFORE THE GATE COUNTS. _CHRON_LAST_PROPOSAL above keeps
        # the reader's RAW words (the receipt); the gate reads the board's canonical names, so
        # two spellings of one item finally corroborate each other instead of each sitting at
        # one witness in his inbox. See _chron_fold.
        prop, _fold_report = _chron_fold(prop)
        gate = _cr.strict_gate()
        applied = _cr.apply_proposal(prop, {"uniques": [], "sets": []}, gate=gate)
        with _CHRON_LOCK:
            _CHRON_JOB.update({
                "running": False, "phase": "done",
                "result": {
                    "totals": {"reels": 1, "framesSeen": res["framesGiven"], "classified": 0,
                               "pagesRead": res["pagesRead"], "skippedReels": 0},
                    "reels": [{"reel": vis.get("label") or "visit", "runs": 1, "candidates": 1,
                               "classified": 0, "pages": res["pagesRead"]}],
                    # v1570 — completeSets must live INSIDE wouldAdd. It was emitted as a SIBLING
                    # of it, and all three consumers read inside: the emptiness guard (_wa.get),
                    # the payload that ships only prop["wouldAdd"], and bible.html's
                    # `var add = proposal.wouldAdd`. So even a populated list was invisible to
                    # every single reader. dict(comprehension, completeSets=...) keeps the existing
                    # per-ledger shape untouched and adds the third key beside it.
                    # v1864 — THE GAME'S OWN FIND DATE TRAVELS WITH THE NAME.
                    # Konyo: "i want the console also updateing me on when it was found timestamped
                    # in the game..(not when the AI READ IT)". His Chronicle prints it per row and
                    # the reader has returned it since p1839; proposal_from_pages hangs it on every
                    # sighting; bible.html has consumed a per-row `date` since v1693 — and this
                    # payload, the only thing between them, never carried one. Plumbing built at
                    # both ends and never joined. [[plumbing-with-no-tap]]
                    # `gameFound` is ABSENT rather than empty when the page did not print a legible
                    # date, so the board can tell "found on this date" from "found, date unknown".
                    "wouldAdd": dict({lg: [dict({"name": n,
                                       "why": (gate.verdicts.get(n) or {}).get("why", ""),
                                       "witnesses": (gate.verdicts.get(n) or {}).get("witnesses", []),
                                       "seen": [{"reel": sg.get("reel"), "frame": sg.get("frame"),
                                                 "lane": sg.get("lane") or "claude"}
                                                for sg in (prop.get(lg, {}).get(n) or [])[:6]]},
                                       **({"gameFound": _cr.in_game_stamp(prop.get(lg, {}).get(n) or [])}
                                          if _cr.in_game_stamp(prop.get(lg, {}).get(n) or []) else {}))
                                      for n in applied[lg]["added"]]
                                 for lg in ("uniques", "sets")},
                                completeSets=[{"name": _cn,
                                               "why": (gate.verdicts.get(_cn) or {}).get("why", "")}
                                     # v1570 — apply_proposal returns completeSets as a plain LIST
                                     # (only uniques/sets go through merge_max, which is what makes
                                     # those dicts). `or {}` swapped a dict in for the EMPTY list,
                                     # so .get worked and CI stayed green — and the FIRST complete
                                     # set to pass the gate would make the list truthy, .get would
                                     # hit a list, AttributeError would fire inside the _CHRON_JOB
                                     # literal, and the except below would discard the WHOLE sweep:
                                     # uniques, sets, held, evidence — on the exact run that found
                                     # the row worth five. Armed by me in v1567, defused here.
                                              for _cn in _completed_names(applied)]),
                    "held": [{"ledger": h["ledger"], "name": h["name"],
                              "why": (gate.verdicts.get(h["name"]) or {}).get("why", ""),
                              "sightings": len(h["sightings"]),
                              "seen": [{"reel": sg.get("reel"), "frame": sg.get("frame"),
                                        "lane": sg.get("lane") or "claude"}
                                       for sg in (h["sightings"] or [])[:6]]}
                             for h in applied["held"]],
                    # THIS RUN — the same scope as `totals` beside it.
                    "refused": _run_refused,
                    # EVERY RUN — the durable ledger's whole list, named so it cannot be read as
                    # the line above.
                    "refusedEver": prop.get("refused") or [],
                    # v1846 — the finds this sweep dated newer than anything read before it
                    "newlyDated": _fresh,
                    # v1789 — the RECEIPT for a queue that got smaller. A name folded onto an
                    # item he already has, or retired as reader debris, must not simply vanish:
                    # "we looked and it was not a grail item" and "nobody looked" have to read
                    # differently, or a tidy inbox becomes indistinguishable from a lost one.
                    "fold": _fold_report,
                    "setGroups": prop.get("setGroups") or {},
                    "lanes": _CHRON_JOB.get("lanes") or [],
                    "fromVisit": int(visit_ts),
                },
            })
            _chron_result_save()   # v1763 — saved in the same breath the result is set
            # v1766 — and only now is the visit spent, for the same reason as the reel: the mark
            # used to fire when the sweep STARTED, so a console that died mid-read left the visit
            # flagged read with nothing written. Marking here is what its own comment always claimed.
            try:
                if not _v_refused[0]:
                    _chron_autoread_mark(int(visit_ts))
                _CHRON_AUTOREAD["tries"].pop(str(int(visit_ts)), None)
            except Exception:
                pass
    except Exception as e:
        with _CHRON_LOCK:
            _CHRON_JOB.update({"running": False, "phase": "error", "error": str(e)[:300]})


def _chron_known_from_journal(limit=500):
    """v1695 — THE FRAMES THE LIVE AGENT ALREADY IDENTIFIED, handed to the retro sweep as marks.

    `sweep_hist(known_chronicle=)` has existed since v1689 and NOTHING HAS EVER PASSED IT. The two
    halves were both built and never joined: the live lane journals a `chronicle/visit` row naming
    the frames it saw, and the sweep's selector will let a named frame through regardless of what
    the cheap classifier thinks of it — but the sweep was called without the argument, so every
    retro run re-derived from scratch what the live agent already knew and paid the classifier to
    disagree.

    Why this had a DEADLINE rather than being ordinary debt: `tv/chronicle_swept.json` does not
    exist on this machine, so no sweep has ever completed here. The first one writes every reel it
    touches into that file, and `skip_reels` (:9758) then hides those reels from every future sweep.
    A first sweep that selects nothing does not merely waste a run — it seals the footage. Wiring
    this before the first sweep is strictly cheaper than wiring it after, because after costs a
    `force` run to undo.

    Shape: a FLAT {frameId: ledgerWord} map, which is what `_reel_known` (:862) and
    `_known_kind` (:279) already accept — frame ids are unique across reels, and a bare "uniques" /
    "sets" is normalised to a kind for us. A visit whose ledger was never read contributes "" ->
    None, which means "this IS a Chronicle frame, tab unknown" — a real state the selector handles,
    and deliberately not the same as being absent.

    Never raises. A journal that cannot be read must degrade the sweep to its old
    classifier-only behaviour, never abort it: these marks make the sweep cheaper and better, and
    nothing downstream is entitled to depend on them.
    """
    known = {}
    try:
        for v in (chronicle_visits(limit=limit) or {}).get("visits") or []:
            ledger = v.get("ledger") or ""
            for fr in v.get("frames") or []:
                if not fr:
                    continue
                # a frame named by two visits keeps the one that actually knew its tab; "" never
                # overwrites a real ledger word.
                if ledger or str(fr) not in known:
                    known[str(fr)] = ledger
    except Exception:
        return {}
    return known


def _chron_live_lane_pages(limit=2000):
    """v1833 — the live agent's own Chronicle sightings, as pages the sweep can witness with.

    Konyo: "we had a AI reader for live too ... make it an extra layer of accuracy its the first
    eyes". His journal holds them already (13 chronicle rows, 10 with discoveries, conf 0.75) and
    nothing has ever read them for the tally. The ledger comes from his generated rosters rather
    than from the row, because his live rows carry chronicleTab:null — see live_pages().

    Degrades to [] on ANY failure, deliberately: this makes a sweep better, and nothing downstream
    is entitled to depend on it. A missing roster must never abort a sweep that would otherwise run.
    """
    try:
        import chronicle_retro as _cr
        import chronicle_resolve as _res
    except Exception:
        return []
    try:
        roster = _res.load_roster()
    except Exception as e:
        print("   \u26a0 live lane off — unique roster unavailable (%s)" % e)
        return []
    try:
        sroster = _res.load_set_roster()
    except Exception:
        sroster = None

    def _ledger_of(n):
        u = _res.canonical(n, roster)
        v = _res.canonical(n, sroster) if sroster else None
        if u and not v:
            return "uniques"
        if v and not u:
            return "sets"
        return None      # in both catalogues, or neither — say nothing rather than pick

    # v1835 — THE JOURNAL MUST DESCRIBE THE FOOTAGE BEING SWEPT. TV_HIST points the sweep at other
    # reels; TV_SESSIONS points the journal at the matching rows. Overriding the first without the
    # second means the live lane would contribute sightings about his REAL sessions to a sweep of
    # somebody else's footage — which is wrong on the merits, and in the suite it meant his actual
    # journal (Baranar's Star, Jalal's Mane, lane "live") landed in fixture evidence within an hour
    # of v1833 shipping. Isolated footage, isolated journal — the same rule v1832 applied to the
    # sweep lock. [[feedback-fixtures-never-touch-live-data]]
    if os.environ.get("TV_HIST") and not os.environ.get("TV_SESSIONS"):
        return []
    try:
        rows = _kai_journal_rows() or []
    except Exception:
        return []
    try:
        return _cr.live_pages(rows[-int(limit):], _ledger_of)
    except Exception as e:
        print("   \u26a0 live lane off — %s" % e)
        return []


def _chron_sweep_run(hist_dir, limit, force=False, reel_id=None):
    try:
        import chronicle_retro as _cr
        import tv_diablo as _tv
        try:
            import g5_grok_eyes as _g5
        except Exception:
            _g5 = None
        hist = hist_dir or os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")
        reels = _cr.reel_dirs(hist)[:limit] if limit else _cr.reel_dirs(hist)
        with _CHRON_LOCK:
            _CHRON_JOB["reelsTotal"] = len(reels)
            _CHRON_JOB["phase"] = "reading"

        def _tick(**kw):
            with _CHRON_LOCK:
                for k, v in kw.items():
                    _CHRON_JOB[k] = _CHRON_JOB.get(k, 0) + v if isinstance(v, int) else v

        # v1577 — ONE BAD FRAME USED TO ABANDON THE WHOLE SWEEP. read_reel() calls classify() bare
        # (chronicle_retro:209) and sweep_hist() calls read_reel() bare (:608), so a transient
        # model/network failure on a SINGLE probe propagated all the way out — and because the caller
        # catches broadly, it surfaced as a short result rather than an error. Every reel after the
        # bad frame was silently never read. cr.classifier() exists to isolate exactly this, is
        # tested, and had NO production caller: this function was a re-implementation of it WITHOUT
        # the try. Proven against the real hist dir with a reader that throws on its 2nd probe —
        # inline: aborted, 0 reels; through classifier(): all 4 reels, 10 classifications.
        # The tick stays INSIDE the reader so "classified" keeps counting probes ATTEMPTED (a probe
        # that died is still money spent and still belongs in the count), matching read_page above.
        # v1774 — COUNT THE READS THAT NEVER HAPPENED. A throttled reader now refuses instead of
        # answering empty (tv_diablo), but the seal rule below reasons "classified > 0 and pages == 0
        # means the classifier looked and correctly found nothing" — which is exactly what a throttle
        # counterfeits. So a run that touched the throttle seals nothing.
        _throttled = [0]
        _capped = [0]     # v1778 — reads the SUBSCRIPTION CAP refused; a capped run seals nothing
        _waited = [0.0]

        def _breathe():
            """v1775 — A RETRO SWEEP SHOULD WAIT OUT A THROTTLE, NOT WALK PAST IT.

            v1774 made the readers refuse while throttled, which stopped a silent empty being
            mistaken for an answer — but a refusal is still a page not read, and a sweep of his
            footage is a BATCH job with nobody waiting on the next frame. The live capture must never
            block (a dropped frame is gone); this must never skip (the reel is right there on disk).
            Same flag, opposite correct behaviour.

            Bounded so a stuck throttle cannot hang the sweep forever: the window is 120s, this
            waits at most 180s per call and then lets the reader refuse as v1774 does.

            v1832 — and it is where the sweep's heartbeat beats, because it is the one hook that
            runs before EVERY page read. run_gates has always described the lock as a heartbeat;
            until now nothing beat it."""
            _sweep_lock_touch()
            import time as _t
            deadline = _t.time() + 180.0
            slept = 0.0
            while _tv._is_throttled() and _t.time() < deadline:
                _t.sleep(2.0)
                slept += 2.0
            if slept:
                _waited[0] += slept
                # v1779 — _tick ACCUMULATES ints, so passing the already-cumulative total made this
                # grow quadratically: his console reported throttleWaitS 27720 (7h42m) inside a
                # sweep that lived 44 minutes — a number self-refuting on its own data. Pass the
                # DELTA and let _tick do the summing it was written to do.
                _tick(throttleWaitS=int(slept))
            return slept

        _tmpl_hits = [0]

        def _classify_one(p):
            # ── THE TEMPLATE READS ITSELF (2026-08-20, his ask) ──────────────────────────────
            # Konyo: "is there a way here to code this more inteligently?" — about having to
            # declare a focus, or pay a model to rediscover which panel a frame shows.
            #
            # There is, and it was already written. chronicle_template.detect() resolves the
            # Chronicle tab from FOUR independent pixel signals (close-X, secondary-gold, the tab
            # markers) and says how many voted. It is structural, it costs nothing, and until now
            # NOTHING outside its own test called it — tv_diablo imports the module only to borrow
            # a crop band. A complete classifier, built and tested, sitting dark while every
            # candidate run paid a model to answer the same question.
            #
            # Measured on his own frames before wiring: a uniques page 4/4, a sets page 4/4, the TV
            # DIABLO console window 1/4, gameplay 1/4, a stash panel 0/4. Perfect discrimination.
            #
            # The MODEL REMAINS THE FALLBACK, deliberately: when the detector abstains (occluded
            # tab, an aspect it was not calibrated on) the old paid path runs exactly as before.
            # This can only remove model calls, never add a wrong answer that was not already
            # reachable. [[unknown-stays-unknown]] — abstaining is an answer here, not a failure.
            try:
                import chronicle_template as _ct
                _tab = (_ct.detect(p) or {}).get("tab")
                _kind = _ct.ledger_kind_for_tab(_tab)
                if _kind:
                    _tmpl_hits[0] += 1
                    # the shape classifier() already understands, so nothing downstream changes
                    return {"scene": "chronicle",
                            "chronicleTab": "uniques" if _kind.endswith("uniques") else "sets",
                            "names": [], "conf": 1.0, "via": "template"}
            except Exception as _te:
                print("   \u26a0 template detect failed (%s) — falling back to the paid classify"
                      % str(_te)[:100])
            _breathe()
            if _tv._is_throttled():
                _throttled[0] += 1
            # v1778 — A CAPPED CLASSIFY MUST NOT SEAL THE REEL. This ticks classified=1 whatever
            # happens, and the seal rule reads "classified > 0 with pages == 0" as "the classifier
            # looked and correctly found no Chronicle page". The throttle has had a guard since
            # v1774; the cap had none, so a cap opening mid-sweep sealed every remaining reel at
            # full price with nothing read. Same loss, other door. Caught by code review.
            if _tv._sub_budget_check("oneshot"):
                _capped[0] += 1
            _tick(classified=1)
            _rd = _tv.claude_read(p)
            # v1779 — A LABELLED MISS IS NOT A VERDICT ABOUT HIS FOOTAGE. claude_read returns
            # EMPTY {"mode": "empty", "scene": "gameplay"} when the warm worker stalls and the
            # one-shot cannot take the gate — the contention the semaphore exists for. That shape
            # is deliberate on the LIVE lane (test_agent pins it: "an honest miss, not a hang and
            # not invented data") and should_learn_dead rejects it, so it poisons nothing there.
            # Here it is different: chronicle_kind reads scene='gameplay' as "not a Chronicle page",
            # the run is skipped, and the reel can still be sealed. Counted as a refusal so the
            # seal brakes apply. Found by an adversarial review of the intake lane.
            if isinstance(_rd, dict) and _rd.get("mode") == "empty":
                _capped[0] += 1
                return None
            return _rd

        _classify = _cr.classifier(_classify_one)

        grok_lane = None
        if _g5 is not None and "grok" in (_CHRON_JOB.get("lanes") or []):
            grok_lane = lambda p, k: _g5.g5_chronicle_read(p, k)
        _reads = _chron_reads_load()
        _capped_frames = [0]
        _unread_not_burned = [0]      # refused by throttle/budget — read never happened, look kept

        def _read_one(p, k):
            _breathe()
            # THE RE-READ CAP (2026-08-20, his ask). Asked BEFORE the throttle and the budget,
            # because this one costs nothing to answer and the other two cost a wait.
            _rl = os.path.basename(os.path.dirname(str(p)))
            _fr = os.path.basename(str(p))
            _cap_note = _chron_read_capped(_reads, _tv.PROMPT_VER, _rl, _fr)
            if _cap_note:
                _capped_frames[0] += 1
                return _cap_note
            if _tv._is_throttled():
                _throttled[0] += 1
            if _tv._sub_budget_check("oneshot"):
                _capped[0] += 1
            _tick(pagesRead=1)
            _out = _tv.claude_chronicle_read(p, k)
            # BUMP ONLY WHEN THE PAGE WAS REALLY READ — a page nobody looked at must not burn one
            # of its three looks.
            #
            # v1861 — this comment said exactly that and the code did not do it. The CAPPED case
            # returns early above, so it was safe; the THROTTLED and BUDGET-BLOCKED cases fell
            # straight through to the bump. claude_chronicle_read answers those two with
            # {"note": "reader throttled — not read"} and {"note": "not read — <why>"} and reads
            # NOTHING, so three throttled sweeps would retire a page that had never been read once
            # — and the cap message would then tell him to "re-read them by changing the reader",
            # about pages the reader never saw. Silent, permanent, and the precise safeguard he
            # asked for. [[the-unjoined-end]] — the early return was joined, these two were not.
            #
            # `note` is only ever set by those two refusals (both early returns in tv_diablo); a
            # page that was actually read carries none. So its presence IS "not read".
            try:
                if not _chron_read_bump_if_read(_reads, _tv.PROMPT_VER, _rl, _fr, _out):
                    _unread_not_burned[0] += 1
            except Exception:
                pass
            return _out

        read_page = _cr.two_lane_reader(_read_one, grok_lane)

        # v1835 — BANK THE EVIDENCE AS IT IS READ, not once at the end.
        #
        # A sweep's findings reached disk in exactly one place: _chron_evidence_merge(), after the
        # LAST page of the LAST reel. Everything before that lived in a list in memory. So a sweep
        # that died — killed, throttled out, the machine sleeping, the CLI's --timeout abandoned,
        # a crash on page 439 — lost every read it had paid for, and the reel was not sealed either,
        # so the whole bill came again.
        #
        # It was affordable while a reel was 21 pages. It is not now: v1834 made his 483-frame
        # browse reachable and priced it at 440 pages — roughly sixteen hours of reading on one
        # all-or-nothing transaction. Nobody should be asked to authorise that.
        #
        # Safe BECAUSE merge_proposals identifies a sighting by (reel, frame, lane) and skips one it
        # already holds, and because every write is tmp+os.replace. So a checkpoint is idempotent:
        # the final merge re-offers pages already banked and they fold to nothing. Partial evidence
        # is honest evidence — the gate still needs two witnesses, and a half-read reel simply has
        # fewer of them.
        _ckpt = {"pages": [], "banked": 0}

        def _read_and_bank(p, k):
            resp = read_page(p, k)
            try:
                _ckpt["pages"].append({"reel": os.path.basename(os.path.dirname(str(p))),
                                       "frame": os.path.basename(str(p)),
                                       "kind": k, "resp": resp or {}})
                if len(_ckpt["pages"]) >= _CHRON_CKPT_PAGES:
                    _chron_evidence_merge(_cr.proposal_from_pages(_ckpt["pages"]))
                    _ckpt["banked"] += len(_ckpt["pages"])
                    _ckpt["pages"] = []
                    print("   \U0001f4be banked %d page(s) of evidence so far" % _ckpt["banked"],
                          flush=True)
            except Exception as _be:
                # a failed checkpoint must never end a sweep that is otherwise working
                print("   \u26a0 checkpoint skipped (%s)" % _be)
            return resp

        # v1780 — DECLARE THE SWEEP. run_gates fingerprints the live state files and cannot tell a
        # legitimate sweep from a test writing his console; a lock with a heartbeat is that signal.
        try:
            with open(_sweep_lock_path(), "w") as _lk:
                _lk.write(str(int(time.time())))
        except Exception:
            pass
        swept = _chron_swept_load()
        known = _chron_known_from_journal()
        _tick(knownFrames=len(known))
        # v1779 — READ THE REEL WE WERE HANDED. chronicle_autoreel_tick picks a specific reel and
        # passes reel_id; without this the sweep just re-read reel_dirs[0] and the picked reel was
        # marked anyway. Narrowing skip_reels to "everything except this one" makes sweep_hist land
        # on it without teaching sweep_hist a new parameter.
        _skip, _reopened = _chron_skip_set(swept, force=force)
        # v1844 — AND THE CONSOLE HAS TO BE ABLE TO SAY WHY THE BILL MOVED.
        #
        # v1830 voids a zero-page seal made by an older reader, and v1839 bumped PROMPT_VER — so
        # eight of his eleven seals reopened at once. That is correct and it is the point, but it
        # changes what one button costs: the console's "run it for real" posts {} , which means
        # limit=None, which means every unswept reel. Those eight are ~808 pages. Before v1830 the
        # same press swept almost nothing.
        #
        # The console prices before it spends, so the NUMBER is honest either way. What was missing
        # is the REASON: this list was printed to stdout, which only a terminal sees, so the UI
        # could show a bill that had grown thirty-fold with nothing on screen explaining it. Same
        # write-only shape v1784 fixed for the watchdog's skip reasons, and its fix is the one
        # copied here — ride along in the state the console and the board already read.
        _tick(reopenedReels=list(_reopened))
        if _reopened:
            print("   \U0001f513 %d reel(s) reopened - sealed with 0 pages by an older reader (now %s): %s"
                  % (len(_reopened), _tv.PROMPT_VER, ", ".join(sorted(_reopened)[:4])))
        if reel_id:
            try:
                _all = {os.path.basename(str(d)) for d in _cr.reel_dirs(hist)}
                _skip = {r for r in _all if r != str(reel_id)}
            except Exception:
                pass
        res = _cr.sweep_hist(hist, _classify, _read_and_bank, limit=limit,
                             skip_reels=_skip,
                             known_chronicle=known,
                             on_reel=lambda st: _tick(reelsDone=1))
        # remember ONLY the reels this run actually read. A reel that errored or was skipped must
        # stay unread, or one bad run would permanently hide footage from every future sweep.
        #
        # v1711 — THAT COMMENT DESCRIBED AN INTENT THE CODE DID NOT IMPLEMENT. The filter excluded
        # exactly two cases (already-swept, no reel name) and sealed everything else, INCLUDING a
        # reel that read nothing at all. `sweep_frames` returns {"classified": 0, "pages": [],
        # "note": "no-index"} (chronicle_retro.py:433) for a reel whose index would not load — zero
        # work done, and the old loop wrote it into the memory anyway. `skip_reels` (:9874) then
        # hides it from EVERY future sweep, and the only way back is a `force` run over his whole
        # history. Footage silently gone, at full price to recover.
        #
        # This is the trap `_chron_known_from_journal` was rushed in ahead of, in its own words:
        # "A first sweep that selects nothing does not merely waste a run — it seals the footage."
        # That half got fixed; this half was the actual sealing mechanism and stayed as written.
        # It is a COUNTDOWN, not debt — chronicle_swept.json does not exist on this machine, so the
        # damage lands on the FIRST press of the button and not before.
        #
        # A reel is sealed only if the run genuinely spent something on it. classified > 0 with
        # pages == 0 IS a legitimate seal: the cheap classifier looked at every frame and correctly
        # found no Chronicle page, and paying it again buys the same answer. Zero of both means
        # nothing was ever looked at.
        # v1774 — a run that hit the throttle proves nothing about his footage, and sealing on it
        # is how a reel is lost at full price. Said out loud, never silently skipped.
        if _waited[0]:
            print("   🐢 waited %ds for the throttle to pass — that is pace, not failure" % int(_waited[0]))
        if _throttled[0]:
            _tick(throttledReads=_throttled[0])
            print("   🐢 %d read(s) refused by the throttle — NOTHING sealed this run" % _throttled[0])
        if _capped[0]:
            _tick(cappedReads=_capped[0])
            print("   🚦 %d read(s) refused by the subscription cap — NOTHING sealed this run"
                  % _capped[0])
        for st in res["reels"]:
            if _throttled[0] or _capped[0]:
                break
            if st.get("note") == "already-swept" or not st.get("reel"):
                continue
            did_read = (st.get("classified") or 0) > 0 or (st.get("pages") or 0) > 0
            if not did_read or st.get("note") == "no-index":
                continue
            swept["reel_" + str(st["reel"])] = {"ts": int(time.time() * 1000),
                                                "classified": st.get("classified") or 0,
                                                "pages": st.get("pages") or 0,
                                                # v1830 — WHICH READER SAID SO. Without this a
                                                # "nothing here" verdict outlives every fix to the
                                                # thing that produced it (see _chron_seal_stands).
                                                "promptVer": _tv.PROMPT_VER,
                                                "agentVer": getattr(_tv, "VERSION", "")}
        _chron_swept_save(swept)
        prop = res["proposal"]
        # v1859 — REPORTED HERE, AFTER THE SWEEP, because that is when the counter has a value.
        # v1856 put this line beside the skip-set, which runs BEFORE sweep_hist — so _tmpl_hits was
        # always 0 and the report could never print. A counter incremented inside the classify
        # closure cannot be read before anything has been classified. Plumbing with no tap, written
        # into the commit that removed some. Caught by an isolated end-to-end run on real frames,
        # not by the unit tests, which never execute this function.
        if _tmpl_hits[0]:
            print("   \U0001f9ed %d run(s) classified by the TEMPLATE, free — no model call"
                  % _tmpl_hits[0])
        _chron_reads_save(_reads)
        if _capped_frames[0]:
            print("   \U0001f6d1 %d page(s) skipped by the re-read cap (%d reads each under %s) "
                  "— re-read them by changing the reader, or TV_CHRON_READ_CAP=0"
                  % (_capped_frames[0], _CHRON_READ_CAP, _tv.PROMPT_VER))
        if _unread_not_burned[0]:
            # said out loud so a throttled stretch cannot look like a quiet one. These pages spent
            # nothing and kept all three of their looks — the opposite of the capped line above.
            print("   ⏸ %d page(s) refused by the throttle or the budget — NOT read, and none "
                  "of their %d looks spent" % (_unread_not_burned[0], _CHRON_READ_CAP))
        # v1837 — KEEP THIS RUN'S REFUSALS SEPARATE FROM ALL TIME. `prop` becomes the MERGED,
        # cumulative proposal a line or two below, and the result then published `totals` (this run)
        # beside `refused` (every run, ever) as sibling keys with nothing saying so. Both numbers
        # true, each answering a different question.
        #
        # It cost real time tonight: I read a cumulative refused list as one pass's, concluded
        # v1827 had changed nothing and called a working fix a failure. If it misleads the person
        # who wrote it an hour after writing it, it will mislead him. [[label-outlived-referent]]
        _run_refused = list((res.get("proposal") or {}).get("refused") or [])
        # v1846 — WHAT HE REGISTERED YESTERDAY vs WHAT IS NEW TODAY. Konyo asked for exactly this:
        # "date and timestamp related coding so they know what they registered yesterday and whats
        # new today". The First Found stamps have been captured since v1819 and NOTHING has ever
        # compared two of them, so the ledger knew every find-date and still could not say which
        # were new. Read the high-water mark BEFORE the merge — after it, this run's finds are
        # already folded in and every one of them looks old.
        try:
            _prev_newest = _cr.newest_stamp(_chron_evidence_load())
        except Exception as _se:
            _stamp_math_broke("high-water mark", _se)
            _prev_newest = None
        # v1833 — THE FIRST EYES JOIN THE PANEL. Merged BEFORE the durable evidence merge so a live
        # sighting accumulates exactly like a read page does, and so it can corroborate a retro read
        # from a later sweep. It cannot ground anything alone: witnesses() counts lanes generically,
        # a live sighting keys to its own session, and the two-witness gate is untouched.
        try:
            _live = _chron_live_lane_pages()
            if _live:
                prop = _cr.merge_proposals(prop, _cr.proposal_from_pages(_live))
                print("   \U0001f441 live lane: %d page(s) the agent read while he played" % len(_live))
        except Exception as _le:
            print("   \u26a0 live lane not merged (%s)" % _le)
        # v1531 — KEEP THE RAW EVIDENCE. Re-running the GATE is free; re-running the READS is not.
        # Without this the only way to ask "what would a stricter floor have held back?" was to pay
        # for the whole sweep again, which means the thresholds would never actually get tuned.
        # v1776 — GATE OVER EVERYTHING READ SO FAR, not just this run. Merging here is what makes a
        # sweep additive: the next one can only ADD sightings, never wipe the last one's, and a name
        # seen in a reel swept tonight can finally corroborate one seen in a reel swept tomorrow.
        prop = _chron_evidence_merge(prop)
        try:
            _fresh = _cr.newly_dated(prop, _prev_newest)
        except Exception as _se:
            _stamp_math_broke("newly-dated", _se)
            _fresh = []
        if _fresh:
            print("   \U0001f195 %d find(s) newer than anything read before: %s"
                  % (len(_fresh), ", ".join("%s (%s)" % (r["name"], r["foundAt"]) for r in _fresh[:4])))
        globals()["_CHRON_LAST_PROPOSAL"] = prop
        # v1789 — FOLD ONTO THE ROSTER BEFORE THE GATE COUNTS. _CHRON_LAST_PROPOSAL above keeps
        # the reader's RAW words (the receipt); the gate reads the board's canonical names, so
        # two spellings of one item finally corroborate each other instead of each sitting at
        # one witness in his inbox. See _chron_fold.
        prop, _fold_report = _chron_fold(prop)
        gate = _cr.strict_gate()
        applied = _cr.apply_proposal(prop, {"uniques": [], "sets": []}, gate=gate)
        # v1789 — THE FOCUSED HUNT, WIRED. Konyo: "cant like an extra AI take care of it and cross
        # reference it with specific and focused hunts for it to cross reference it here and
        # automatically grail it.. and if it still cant then leave it for me to tick off."
        #
        # A held name has ONE independent signal and needs two. The hunt goes and looks for the
        # second in OTHER reels, where a hit earns cross-reel — the tag these names actually need;
        # another frame in the same reel only re-earns cross-frame, which every held name already
        # has. Whatever it finds is merged through merge_proposals and RE-GATED by the same rule as
        # everything else, so nothing reaches his grail on a private path.
        prop, applied, _hunt_report = _chron_hunt_held(prop, applied, hist, read_page)
        # v1920 — and then ask the GAME, from the same frames, and put the two side by side.
        try:
            # ⚠ v1920 — `dirs` DID NOT EXIST HERE and the v1853 scope guard caught it before it
            # shipped. That is the exact class that left MINI dead for ten versions: a name inside a
            # function body resolves only when that line RUNS, so a NameError here would have
            # surfaced as "the sweep crashed at the end" long after the reads were paid for.
            # The reel list in this function is `reels` (line ~11854). [[source-reading-guard]]
            _cal_report = _chron_calibration(reels)
        except Exception as _ce:
            _cal_report = {"ok": None, "say": "calibration failed: %s" % str(_ce)[:120]}
        if _cal_report.get("ok") is False:
            print("   \u2696 %s" % _cal_report.get("say"))
        _con = prop.get("contested") or {}
        _ncon = sum(len(v or []) for v in _con.values())
        if _ncon:
            print("   \u2694 %d name(s) were read BOTH found and not-found — the reader disagreed "
                  "with itself about these, and that is worth your eyes before you register:"
                  % _ncon)
            for _led in ("uniques", "sets"):
                _names = _con.get(_led) or []
                if _names:
                    print("      %-8s %s%s" % (_led, ", ".join(_names[:6]),
                                               " …+%d" % (len(_names) - 6) if len(_names) > 6 else ""))
        # v1923 — AND ASK THE GAME'S OWN MISSING LIST WHETHER IT AGREES WITH THE PROPOSAL.
        # Every other reader in this pipeline reads a FOUND page and proposes an ADDITION, so the
        # whole chain can only push the count up; nothing in it can ever say "you do not have that".
        # The game keeps that list itself — the Chronicle's Remaining filter — and one recording of
        # it falsifies rows no amount of found-page reading could. On 2026-08-21 it caught exactly
        # one, Natalya's Soul (claws), out of 36 proposed set pieces: the row he would otherwise
        # have registered onto his board.
        #
        # ⚠ IT IS TIME-ORDERED, and that is the whole rule rather than a refinement. A Remaining
        # page is a photograph of one moment and he keeps playing, so a denial only bites when the
        # page was shot AFTER the sighting. Without that, a piece found this evening is denied by a
        # page shot this morning and the safeguard begins destroying the finds it exists to protect.
        # counter_ledger.denied splits denied / superseded / undated for exactly that reason, and
        # an order nobody established stays UNKNOWN rather than becoming an accusation.
        # [[stale-reading]] [[unknown-stays-unknown]]
        #
        # It runs AFTER _chron_fold so it sees canonical names. Its own folding is still not
        # redundant: the first cut of this guard compared raw pipeline names against roster names
        # and reported a clean pass on 86 of them, none of which were roster strings.
        try:
            import counter_ledger as _clg
            _denial = _clg.denied((prop.get("sets") or {}))
        except Exception as _de:
            _denial = {"ok": None, "denied": [], "superseded": [], "undated": [],
                       "say": "the game's missing list could not be consulted: %s" % str(_de)[:120]}
        if _denial.get("denied") or _denial.get("undated"):
            print("   \U0001f6a9 %s" % _denial.get("say"))
        # v1932 — a set-group refused because its heading was a PIECE, not a set. Printed rather
        # than only stored: a refusal nobody sees is the same as a group silently dropped, and the
        # whole reason this guard exists is that "one row worth five pieces" must never come from a
        # misread heading. [[unknown-stays-unknown]]
        _rg = prop.get("refusedGroups") or []
        if _rg:
            print("   \u26d4 %d set-group(s) refused — the heading was a PIECE, not a set: %s"
                  % (len(_rg), ", ".join(sorted({str(x.get("set")) for x in _rg})[:6])))
        gate = _cr.strict_gate()
        applied = _cr.apply_proposal(prop, {"uniques": [], "sets": []}, gate=gate)
        with _CHRON_LOCK:
            _CHRON_JOB.update({
                "running": False, "phase": "done",
                "result": {
                    "totals": res["totals"], "reels": res["reels"],
                    # v1541 — WHY IT FOUND WHAT IT FOUND, carried to the UI. An empty sweep that says
                    # nothing is indistinguishable from a broken one, and that is exactly how it read
                    # to Konyo on his Windows PC. sweep_verdict() separates "no Chronicle appeared in
                    # your footage" from "pages were read and yielded nothing" — only the second is
                    # the reader's fault, and sending him to debug a prompt for the first would waste
                    # his evening on a machine that is working.
                    "verdict": res.get("verdict"),
                    # what it WOULD add per ledger, each with the gate's own sentence
                    # v1525 — THE EVIDENCE TRAVELS WITH THE NAME. The engine has always kept each
                    # sighting's reel and frame; until now the route threw them away and left "why
                    # does it think I have Windforce" answerable only in principle. Capped at 6 —
                    # enough to show the corroboration, not enough to bloat the payload.
                    # v1570 — completeSets must live INSIDE wouldAdd. It was emitted as a SIBLING
                    # of it, and all three consumers read inside: the emptiness guard (_wa.get),
                    # the payload that ships only prop["wouldAdd"], and bible.html's
                    # `var add = proposal.wouldAdd`. So even a populated list was invisible to
                    # every single reader. dict(comprehension, completeSets=...) keeps the existing
                    # per-ledger shape untouched and adds the third key beside it.
                    # v1864 — THE GAME'S OWN FIND DATE TRAVELS WITH THE NAME.
                    # Konyo: "i want the console also updateing me on when it was found timestamped
                    # in the game..(not when the AI READ IT)". His Chronicle prints it per row and
                    # the reader has returned it since p1839; proposal_from_pages hangs it on every
                    # sighting; bible.html has consumed a per-row `date` since v1693 — and this
                    # payload, the only thing between them, never carried one. Plumbing built at
                    # both ends and never joined. [[plumbing-with-no-tap]]
                    # `gameFound` is ABSENT rather than empty when the page did not print a legible
                    # date, so the board can tell "found on this date" from "found, date unknown".
                    "wouldAdd": dict({lg: [dict({"name": n,
                                       "why": (gate.verdicts.get(n) or {}).get("why", ""),
                                       "witnesses": (gate.verdicts.get(n) or {}).get("witnesses", []),
                                       "seen": [{"reel": sg.get("reel"), "frame": sg.get("frame"),
                                                 "lane": sg.get("lane") or "claude"}
                                                for sg in (prop.get(lg, {}).get(n) or [])[:6]]},
                                       **({"gameFound": _cr.in_game_stamp(prop.get(lg, {}).get(n) or [])}
                                          if _cr.in_game_stamp(prop.get(lg, {}).get(n) or []) else {}))
                                      for n in applied[lg]["added"]]
                                 for lg in ("uniques", "sets")},
                                completeSets=[{"name": _cn,
                                               "why": (gate.verdicts.get(_cn) or {}).get("why", "")}
                                     # v1570 — apply_proposal returns completeSets as a plain LIST
                                     # (only uniques/sets go through merge_max, which is what makes
                                     # those dicts). `or {}` swapped a dict in for the EMPTY list,
                                     # so .get worked and CI stayed green — and the FIRST complete
                                     # set to pass the gate would make the list truthy, .get would
                                     # hit a list, AttributeError would fire inside the _CHRON_JOB
                                     # literal, and the except below would discard the WHOLE sweep:
                                     # uniques, sets, held, evidence — on the exact run that found
                                     # the row worth five. Armed by me in v1567, defused here.
                                              for _cn in _completed_names(applied)]),
                    "held": [{"ledger": h["ledger"], "name": h["name"],
                              "why": (gate.verdicts.get(h["name"]) or {}).get("why", ""),
                              "sightings": len(h["sightings"]),
                              # a HELD name needs its evidence most of all: this is the row he looks
                              # at to decide whether to trust it by hand
                              "seen": [{"reel": sg.get("reel"), "frame": sg.get("frame"),
                                        "lane": sg.get("lane") or "claude"}
                                       for sg in (h["sightings"] or [])[:6]]}
                             for h in applied["held"]],
                    # THIS RUN — the same scope as `totals` beside it.
                    "refused": _run_refused,
                    # EVERY RUN — the durable ledger's whole list, named so it cannot be read as
                    # the line above.
                    "refusedEver": prop.get("refused") or [],
                    # v1846 — the finds this sweep dated newer than anything read before it
                    "newlyDated": _fresh,
                    # v1789 — the RECEIPT for a queue that got smaller. A name folded onto an
                    # item he already has, or retired as reader debris, must not simply vanish:
                    # "we looked and it was not a grail item" and "nobody looked" have to read
                    # differently, or a tidy inbox becomes indistinguishable from a lost one.
                    "fold": _fold_report,
                    # v1789 — what the focused hunt went looking for, and what came back
                    "hunt": _hunt_report,
                    # v1920 — THE SAFEGUARD RUNS ON EVERY SWEEP, not when someone remembers.
                    # It costs no model call: the game's own completion bar is pixels the sweep
                    # already has. See _chron_calibration for what it cost to not have this.
                    "calibration": _cal_report,
                    # v1923 — the game's own missing list, applied to what this sweep wants to add.
                    # Carried rather than only printed: a finding that lives solely in a log line is
                    # a finding the board cannot show him at the moment he decides to register.
                    "denial": _denial,
                    # v1923 — what this proposal is ALLOWED to conclude from its not-found side.
                    "notFoundDatable": prop.get("notFoundDatable"),
                    # v1930 — `contestedResolved` (the per-name verdict detail) was here and no UI
                    # ever read it. It is DERIVABLE — `contestedExpired` is computed from it in
                    # chronicle_retro — and it drives no decision he makes, so it is dropped from
                    # the payload rather than rendered. The engine keeps it on the proposal, where
                    # a debugger can still reach it.
                    # Shipping an unread key in the very commit that fixed three of them is how a
                    # class survives being fixed. [[plumbing-with-no-tap]]
                    "contestedExpired": prop.get("contestedExpired"),
                    # v1921 — THE NAMES READ BOTH WAYS. A piece the reader saw as FOUND on one page
                    # and NOT FOUND on another is the most informative row in a proposal, and until
                    # now nothing computed it. 26 of them sit in his banked evidence — including
                    # Immortal King's Will, the very item he told me hours ago he does not have.
                    # Reported, never acted on: an older not-found reading is perfectly ordinary
                    # once he has since found the item, and the ordering to tell those apart is not
                    # stored yet. [[feedback-contradiction-is-the-finding]]
                    "contested": prop.get("contested") or {},
                    "setGroups": prop.get("setGroups") or {},
                    "lanes": _CHRON_JOB.get("lanes") or [],
                },
            })
            _chron_result_save()   # v1763 — saved in the same breath the result is set
            # v1765 — AND ONLY NOW IS THE REEL SPENT. The tick used to mark the reel the instant
            # chronicle_sweep_start RETURNED — but that call spawns a daemon thread and returns
            # immediately, so the mark landed while the sweep had barely begun. The comment above it
            # claimed the marker "waits for the result to exist on disk"; it did not, and the failure
            # it described was live the whole time: a console killed mid-sweep, or a sweep that threw,
            # left the reel marked done forever with its findings never written. His recordings are
            # not re-creatable, so a burned reel is a permanent loss of the thing this feature exists
            # to protect. The mark now happens HERE, after the result is durable, which is what the
            # comment always said. [[the-unjoined-end]] [[label-outlived-referent]]
            # v1779 — MARK ONLY WHAT WAS ACTUALLY READ. Two defects met here, both found by an
            # adversarial review and both already fired on his disk:
            #
            #  (a) reel_id was used ONLY to mark. The sweep reads reel_dirs(hist)[:limit] and never
            #      saw reel_id at all, so the watchdog targeted reel N while the sweep re-read the
            #      newest reel — and reel N was retired having never been opened. SEVEN of his reels
            #      were marked swept with no read record anywhere, including the 08-17 reel the
            #      whole feature was built for. Fixed by reading the reel we were handed (below).
            #  (b) this mark sat outside BOTH brakes — the throttle/cap break at the seal loop and
            #      the did_read test — so a run that read nothing still burned the reel in the file
            #      that decides whether it is ever auto-offered again.
            _did_read = any((st.get("classified") or 0) > 0 or (st.get("pages") or 0) > 0
                            for st in (res.get("reels") or []))
            if reel_id and _did_read and not _throttled[0] and not _capped[0]:
                try:
                    _chron_reels_mark(reel_id)
                    # a reel that finished owes nothing: clear its attempt count so an unrelated
                    # failure months later starts from zero rather than inheriting old strikes
                    _CHRON_AUTOREAD["tries"].pop(reel_id, None)
                except Exception:
                    pass
    except Exception as e:
        with _CHRON_LOCK:
            _CHRON_JOB.update({"running": False, "phase": "error", "error": str(e)[:300]})


def fleet_presence(force=False):
    """v1496 — WHO IS ONLINE, AND WHEN WAS EACH MACHINE LAST HERE.

    The presence data lives in the site's KV (fed by _console_beacon since v875) and the browser must
    never hold the site key, so the CONSOLE asks for it server-side with the same Basic credentials
    the beacon already uses. Cached 60s: this is a curiosity panel, not a live wire, and it must never
    slow the status poll or hammer the site."""
    now = time.time()
    if not force and _FLEET_PRESENCE_CACHE["d"] is not None and (now - _FLEET_PRESENCE_CACHE["t"]) < 60:
        return _FLEET_PRESENCE_CACHE["d"]
    out = {"ok": False, "online": [], "offline": [], "error": "not fetched"}
    try:
        import base64 as _b64
        req = urllib.request.Request(
            "https://bull-4-u.com/api/console",
            headers={"User-Agent": "TVD-Console/1.0",
                     "Authorization": "Basic " + _b64.b64encode(b"app:DeanDiablo").decode()})
        with urllib.request.urlopen(req, timeout=6) as r:
            out = json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:
        out = {"ok": False, "online": [], "offline": [], "error": str(e)[:120]}
    _FLEET_PRESENCE_CACHE["t"] = now
    _FLEET_PRESENCE_CACHE["d"] = out
    return out


def install_identity():
    """v1465 — a STABLE, PER-INSTALL identity. Gitignored, so it never travels between PCs.

    Konyo owns four machines that matter (this Windows PC, a second Windows PC, a MacBook, and
    the cousin's PC). The v663 machine switch is a 2x2 — mac|windows x main|ladder — so it
    cannot tell two Windows PCs apart: both land in the same W· world and silently share one
    save. Whose-world (the switch) and which-box (this) are different questions; this answers
    the second, and it is what the console's sigil is derived from.

    The id is random and opaque, minted once per install. Hostname and OS user ride along only
    as human-readable labels — they are NOT the identity, because two people can both be
    "Administrator" on "DESKTOP-PC" and a sigil that collided there would be worse than none.
    """
    try:
        with open(IDENTITY_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict) and data.get("id"):
            return data
    except Exception:
        pass
    try:
        import getpass
        import socket
        import uuid as _uuid
        data = {
            "id": _uuid.uuid4().hex,
            "computer": socket.gethostname() or "?",
            "user": getpass.getuser() or "?",
            "platform": "windows" if IS_WIN else ("mac" if sys.platform == "darwin" else sys.platform),
            "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        tmp = IDENTITY_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        os.replace(tmp, IDENTITY_PATH)
        print(f"🪪 minted install identity {data['id'][:8]} on {data['computer']}", flush=True)
        return data
    except Exception:
        return {"id": "", "computer": "?", "user": "?", "platform": "?", "createdAt": ""}


def status_payload():
    # v872 (Konyo live: 'STANDBY keeps jumping at me mid session') — one slow ping under game
    # load flipped the whole console to STANDBY/IDLE for a beat. STICKY BRIDGE: a live agent
    # process with a bridge seen in the last 10s stays ON; only a truly dead bridge drops it.
    # v946.2 — NEVER sticky-bridge when the agent process is dead. Stale _BR_CACHE (≤6s) after
    # End Session kept bridge=True → UI stuck on "End Session"/ON AIR until the cache aged out.
    # v1424–v1426 live Windows proof: under D2R, /state can miss a poll while ping still works.
    # Keep last-good st for a grace window; disk-fallback eyeAgeMs + cap_target so the UI never
    # paints dark film / READS 0 / empty pin while capture is LINKED and eye.jpg is fresh.
    _alive = _agent_alive()
    _now = time.time()
    bridge_now = bool(_BR_CACHE["ping"]) and (_now - _BR_CACHE["ts"]) < 8.0 and _alive
    bridge = bool(_alive and (
        bridge_now or (_now - globals().get("_BRIDGE_LAST_OK", 0.0)) < 12.0))
    st = None
    if _alive and _BR_CACHE.get("st") is not None:
        # Use last good state if this poll is fresh OR sticky within 15s of a good fetch
        if bridge_now or (_now - float(_BR_CACHE.get("st_ts") or 0)) < 15.0:
            st = _BR_CACHE["st"]
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
    # v1456 HONESTY (audit): the 15s last-good grace above is the right call under D2R load, but the
    # payload said nothing about it — a stale scene / area / health snapshot rode out looking exactly
    # as live as a fresh fetch. stateAgeMs + stateFresh let the UI say "last known 6s ago" instead of
    # implying now. Computed AFTER the self-heal resets so a dead agent reports no state at all.
    state_age_ms = -1
    if st is not None:
        state_age_ms = int(max(0.0, _now - float(_BR_CACHE.get("st_ts") or _now)) * 1000)
    state_fresh = bool(st is not None and bridge_now)
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
    # v1425/v1426 — disk honesty (Windows film + pin never depend solely on a slow /state)
    _disk_eye = _disk_eye_age_ms()
    _eye = (st or {}).get("eyeAgeMs")
    if _eye is None or (isinstance(_eye, (int, float)) and _eye < 0):
        _eye = _disk_eye
    _cap = (st or {}).get("captureTarget") or {}
    if not _cap and IS_WIN:
        _cap = _disk_cap_target()
    _reads = (st or {}).get("readCount")
    if _reads is None:
        _reads = len((st or {}).get("reads") or [])
    # v946 — session health + mind story (journal tail + leases + driver pulse)
    # v1436 — LIVE smoothness: under ON AIR, skip heavy journal re-parse every status poll
    # (was 200-row walk × UI polls → UI hitch under D2R). Recompute at most every 3s live.
    try:
        _live_mode = mode in ("live", "stopping") and bridge
        _now_j = time.time()
        _jh = globals().get("_STATUS_JOURNAL_CACHE") or {"t": 0.0, "h": None, "d": None}
        if _live_mode and _jh.get("h") is not None and (_now_j - float(_jh.get("t") or 0)) < 3.0:
            _sess_h = _jh["h"]
            _drv = _jh.get("d") or {"seen": 0, "queued": 0, "fired": 0, "refire": 0}
        else:
            _jtail = _kai_journal_rows()[-200:]
            _sid_now = ""
            for _r in reversed(_jtail):
                if _r.get("sessionId"):
                    _sid_now = str(_r.get("sessionId"))
                    break
            _sess_tail = [r for r in _jtail if not _sid_now or r.get("sessionId") == _sid_now][-80:]
            _drv = {"seen": globals().get("_DRV_SEEN", 0), "queued": globals().get("_DRV_QUEUED", 0),
                    "fired": globals().get("_DRV_FIRED", 0), "refire": globals().get("_DRV_REFIRE", 0),
                    # v1689 — stash/vault/tally intakes REFUSED because the vision lane called
                    # that moment a Chronicle page. Beside fired/refire on purpose: a refusal is
                    # a routing event, not an absence, and must be as visible as a fire.
                    "chronRefused": globals().get("_DRV_CHRON_REFUSED", 0),
                    "err": globals().get("_DRV_ERR")}
            _sess_h = _session_health_from_rows(_sess_tail, leases=_intake_lease_status(), driver=_drv)
            _gc = _newest_gate_count()   # v948.12 — accuracy-gate proven/held for the FUNNELS organ
            if _gc:
                _sess_h["gate"] = _gc
            _cn = _newest_completeness()   # v948.13 — film↔registration coverage% (target #2)
            if _cn:
                _sess_h["completeness"] = _cn
            globals()["_STATUS_JOURNAL_CACHE"] = {"t": _now_j, "h": _sess_h, "d": _drv}
    except Exception:
        # v1709 — a thrown journal walk is NOT an idle night. idle + zeros is
        # indistinguishable from "nothing happened" and that is how a dead
        # reader looks healthy. Unknown stays unknown.
        _sess_h = {"tabs": {}, "leases": {}, "verdict": "unknown", "story": [],
                   "tabSummary": {}, "error": "journal unread"}
        _drv = {"seen": None, "queued": None, "fired": None, "refire": None,
                "err": "journal unread"}
    # 🔌 ENGINE-EXPOSURE — the eyes object gets a FRESH liveAgeMs (the primary eye's "now" age,
    # computed per-poll so it isn't frozen in _eyes_pulse's mtime cache). null when no read yet.
    _eyes = _eyes_pulse()
    _eyes = dict(_eyes, liveAgeMs=(int(time.time() * 1000) - _eyes["liveTs"]) if _eyes.get("liveTs") else None)
    # v1418 — fleet channel truth (cached; never blocks status on a cold git fetch)
    try:
        _fleet = fleet_origin_status(force_fetch=False)
    except Exception:
        _fleet = {"ok": False, "behind": 0, "howTo": ""}
    try:
        _ident = install_identity()
    except Exception:
        _ident = {"id": "", "computer": "?", "user": "?"}
    return {
        "ok": True,
        "identity": _ident,          # v1465 — per-install; the console renders its sigil
        "ver": "v1988",
        # v1870 — "IS THIS CONSOLE READING FOR REAL?", answerable at a glance.
        #
        # Tonight that question took an hour and three wrong turns. His reel s_1787244002054_15361
        # is unmistakably his — shared stash open at page 1/5, a Raven Frost tooltip under the
        # cursor — and its journal rows say lane=deep mode=stub, so its reads were CANNED. Working
        # out whether that meant he had pressed SIM, or his console had inherited TV_STUB from a
        # shell, meant reading a log that TESTS also write to (v1869) and then inspecting the live
        # process's environment by hand. It ends up settled — `ps eww` on his console shows TV_FILM
        # and TV_OCR and no TV_STUB, so a non-sim start could not have produced canned rows and that
        # session was a SIM — but no surface should require that.
        #
        # `stub` was already in this payload as None, which is the worst of the three answers: it
        # reads like "no" and means "nobody asked". [[unknown-stays-unknown]]
        "stub": bool(os.environ.get("TV_STUB")),
        "readsAreReal": not bool(os.environ.get("TV_STUB")),
        "engineAlive": globals().get("_ENGINE_ALIVE"),   # v929.2 — driver-probed truth, not a LS stamp
        "engineReady": globals().get("_ENGINE_READY"),
        "driver": {"seen": _drv.get("seen", 0), "queued": _drv.get("queued", 0),
                   "fired": _drv.get("fired", 0), "refire": _drv.get("refire", 0),
                   # v1689 — same counter on the /api/status driver block (the two surfaces AGREE:
                   # both read _DRV_CHRON_REFUSED, one via the cached _drv dict above).
                   "chronRefused": _drv.get("chronRefused", globals().get("_DRV_CHRON_REFUSED", 0)),
                   "judgeQ": globals().get("_DRV_JUDGE_Q", 0),
                   "judgeFire": globals().get("_DRV_JUDGE_FIRE", 0),
                   "err": globals().get("_DRV_ERR"),
                   "engineDeadHard": bool(globals().get("_ENGINE_DEAD_HARD"))},
        "watchdog": globals().get("_WATCHDOG_LAST"),
        "liveRing": _project_live_ring(),   # v948.26 🥷🧠 Phase D — Master-Brain NOW-CURSOR (provisional; sealed reel engineFrames win in retro)
        "eyes": _eyes,
        "engines": _engines_status(),   # 🔌 per-engine wired/running/last-beat — nothing hidden; a dead wire renders ⚫
        "receipts": _receipts_stream(),   # 🧾 bounded newest-first read-receipt stream (routable ids); empty off-air
        "forensicsSummary": _newest_forensics_summary(),   # 🔬 lean {clean,corrected,recovered,blocked,unresolved} badge; full detail at /api/forensics
        "fleet": _fleet,   # v1418 — {behind, latest, dirty, howTo} so Mac/Win never silently drift
        # v1597 — ADDITIVE. Whether THIS machine is actually reaching the presence tracker, or
        # has been failing silently. Never remove: it is the only difference between "never on"
        # and "on but unable to check in".
        "beacon": _beacon_status(),

        "sessionHealth": _sess_h,   # v946 — one-glance tabs/lease/verdict/story
        "mindStory": (_sess_h.get("story") or [])[-6:],
        "journalMB": (lambda: round(os.path.getsize(_journal_path()) / 1e6, 1) if os.path.isfile(_journal_path()) else 0.0)(),
        "platform": "windows" if IS_WIN else ("mac" if sys.platform == "darwin" else sys.platform),
        "shipPlatform": (_windows_ship() or {}).get("platform") if IS_WIN else ("mac" if sys.platform == "darwin" else None),
        "shipVer": (_windows_ship() or {}).get("ver") if IS_WIN else None,
        "shipName": (_windows_ship() or {}).get("name") if IS_WIN else None,
        "shell": "pywebview",
        "mode": ("stopping" if _stop_inflight else mode),
        "agent": mode != "off" and bridge,
        "bridge": bridge,
        "stopping": bool(_stop_inflight),
        "pid": _pid_cached(),
        "capture": bool(IS_WIN and (_read_pid(CAP_PID_PATH) and _pid_alive(_read_pid(CAP_PID_PATH)))),
        "intakeRing": ((st or {}).get("intakes") or [])[-12:],
        "readCount": int(_reads or 0),
        "area": beat.get("area") or (st or {}).get("area") or "",
        "scene": beat.get("scene") or "",
        # v1328 B4-LIVE — the LIVE frame's game-true label (ENTERING/TOWN/FARMING + area) for the
        # D24 "recording now" banner. Honest-absent: None when no live scene/area (off / dark frame).
        "native": (_diablo_scene_label(beat.get("scene") or "",
                                       beat.get("area") or (st or {}).get("area") or "")
                   if (beat.get("scene") or beat.get("area") or (st or {}).get("area")) else None),
        "phase": beat.get("phase") or ("live" if bridge else "off"),
        "motion": beat.get("motion"),
        "interest": beat.get("interest") or (st or {}).get("interest"),
        "model": (st or {}).get("model") or "",
        "events": tail,
        "logPath": LOG_PATH,
        "agentPort": AGENT_PORT,
        "controlPort": CONTROL_PORT,
        "captureTarget": _cap if isinstance(_cap, dict) else {},
        "eyeAgeMs": _eye if _eye is not None else -1,
        "diskEyeAgeMs": _disk_eye,  # v1425 — UI can trust film even if bridge mid-miss
        "health": (st or {}).get("health") or {},
        # v1456 HONESTY (audit): gameOk still defaults True (the UI only ever acts on an explicit
        # false), but "no bridge data" is NOT the same claim as "the game is fine" — gameOkKnown
        # says which one this is, and stateAgeMs/stateFresh say how old the answer is.
        "gameOk": (st or {}).get("gameOk", True) if st else True,
        "gameOkKnown": bool(st) and ("gameOk" in st or "gameOk" in ((st or {}).get("health") or {})),
        "stateAgeMs": state_age_ms,
        "stateFresh": state_fresh,
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


_WINDOWS_SHIP_CACHE = {"t": 0.0, "d": None}


def _windows_ship():
    """v1404 — Windows-only ship identity from tv/WINDOWS_SHIP.json.
    Mac never reads this file. Used so install/launcher/doctor cannot mesh platforms."""
    if not IS_WIN:
        return None
    now = time.time()
    if _WINDOWS_SHIP_CACHE["d"] is not None and (now - _WINDOWS_SHIP_CACHE["t"]) < 30:
        return _WINDOWS_SHIP_CACHE["d"]
    path = os.path.join(HERE, "WINDOWS_SHIP.json")
    data = None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            data = None
    except Exception:
        data = None
    _WINDOWS_SHIP_CACHE["t"] = now
    _WINDOWS_SHIP_CACHE["d"] = data
    return data


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

    # 1b) v1418 fleet_origin — this PC vs GitHub main (Mac + Windows product channel)
    try:
        fl = fleet_origin_status(force_fetch=False)
        behind_n = int(fl.get("behind") or 0)
        checks.append(_chk(
            "fleet_origin", behind_n == 0, "warn",
            ("unified with origin/main (%s)" % (fl.get("head") or fl.get("ver") or "?"))
            if behind_n == 0 else
            ("%d commit(s) BEHIND origin — latest: %s" % (behind_n, (fl.get("latest") or "?")[:60])),
            fl.get("howTo") or "relaunch TV DIABLO to auto-pull (or git pull)"))
        vers["fleetBehind"] = behind_n
        vers["fleetHead"] = fl.get("head")
        vers["fleetOrigin"] = fl.get("origin")
    except Exception as _fe:
        checks.append(_chk("fleet_origin", True, "warn", "fleet check skipped: %s" % str(_fe)[:60]))

    # 2) claude CLI present (v1380.4 deep hunt — same as start_agent)
    env = _env_clean()
    exe = env.get("TV_CLAUDE_BIN") or _find_claude_bin(env.get("PATH"))
    # ══ GROK EYES (G5) — doctor soft when primary ══
    _g5_pri = False
    try:
        _g5_pri = bool(_G5 is not None and _G5.is_primary())
    except Exception:
        _g5_pri = False
    # ══ END GROK EYES (G5) ══
    _cli_sev = "warn" if _g5_pri else "block"
    checks.append(_chk("claude_cli", bool(exe) or _g5_pri, _cli_sev,
                       (exe or "claude CLI not found on PATH") if not _g5_pri
                       else (exe or "claude CLI missing — G5 primary covers vision"),
                       ("irm https://claude.ai/install.ps1 | iex   then: claude  (login once)"
                        if IS_WIN else
                        "npm i -g @anthropic-ai/claude-code, then sign in once in a Terminal")
                       if not _g5_pri else "G5 primary ON — Claude optional; set mode off to require Claude again"))

    # 3) claude AUTH — the one live ping (subscription lane, tiny, hard-capped).
    # v924-R4 (Grok): during ON AIR the live readers already prove the lane — never stack a
    # second `claude -p` on top of a warm pool; the gate belongs BEFORE air.
    if _g5_pri:
        checks.append(_chk("claude_auth", True, "warn",
                           "skipped — G5 Grok Eyes primary is ON (Claude auth optional)"))
    elif exe and _sock_open(AGENT_PORT):
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

    # 1) claude CLI on the SAME cleaned PATH the agent boots with (v1380.4 deep hunt)
    env = _env_clean()
    exe = env.get("TV_CLAUDE_BIN") or _find_claude_bin(env.get("PATH"))
    checks.append(_chk(
        "claude_cli", bool(exe), "block",
        exe or "claude CLI not found on PATH",
        ("irm https://claude.ai/install.ps1 | iex   then: claude  (login once)"
         if IS_WIN else
         "Install Claude Code CLI and put it on PATH")))

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

    # 7b) v1418 fleet — same GitHub main for Mac + Windows (never silently drift)
    try:
        fl = fleet_origin_status(force_fetch=False)
        bn = int(fl.get("behind") or 0)
        counted = fl.get("ok") is not False
        checks.append(_chk(
            "fleet_origin", counted and bn == 0, "warn",
            ("could not ask origin") if not counted
            else (("on origin/main · %s" % (fl.get("head") or "?")) if bn == 0
                  else ("%d commit(s) behind origin · %s" % (bn, (fl.get("latest") or "")[:50]))),
            fl.get("howTo") or "relaunch TV DIABLO to auto-pull"))
    except Exception as _fe:
        # v1709 — skipping the check is not a pass. A doctor that stays green
        # when git never ran is the same lie as behind=0 on a failed rev-list.
        checks.append(_chk("fleet_origin", False, "warn",
                           "fleet check failed: %s" % str(_fe)[:80],
                           "git fetch origin && git rev-list HEAD..origin/main --count"))

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
        _jl = _journal_path()   # v877 · v1493 — one resolver for every site
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
        _live_p = _journal_path()
        _stem = _live_p[:-6] if _live_p.endswith(".jsonl") else _live_p
        _gens = [g for g in range(1, 6) if os.path.isfile(_stem + ".%d.jsonl" % g)]
        _live = os.path.isfile(_live_p)
        checks.append(_chk("journal_gens", True, "warn",
                           "live=%s gens=%s" % ("yes" if _live else "no",
                                                (",".join(str(g) for g in _gens) or "none"))))
    except Exception:
        pass

    # v1404 — Windows ship identity check (install must pin platform=windows + matching ver)
    if IS_WIN:
        ship = _windows_ship() or {}
        ship_plat = str(ship.get("platform") or "")
        ship_ver = str(ship.get("ver") or "")
        app_ver = _app_ver()
        agent_ver = _agent_disk_ver()
        bible_ver = _bible_ver()
        win_ok = (
            ship_plat == "windows"
            and bool(ship_ver)
            and ship_ver == app_ver
            and (not agent_ver or agent_ver == ship_ver)
            and (not bible_ver or bible_ver == ship_ver)
        )
        detail = (
            "ship=%s platform=%s control=%s agent=%s bible=%s"
            % (ship_ver or "?", ship_plat or "?", app_ver, agent_ver or "?", bible_ver or "?")
        )
        checks.append(_chk(
            "windows_ship",
            win_ok,
            "block" if ship_plat and ship_plat != "windows" else "warn",
            detail if ship else "WINDOWS_SHIP.json missing — re-run Windows installer",
            fix=(
                "Windows only: git -C $HOME\\d2r_bible_tests pull; "
                "irm https://bull-4-u.com/d2r/install-tvd.ps1 | iex"
                if not win_ok else None
            ),
        ))
        # Required Windows binaries present (no Mac launcher confusion)
        for rel, label in (
            ("start_tvd_win.ps1", "Windows launcher"),
            ("capture_win.ps1", "Windows capture"),
            ("install-tvd.ps1", "Windows installer"),
        ):
            pth = os.path.join(HERE, rel)
            checks.append(_chk(
                "win_file_" + rel.replace(".", "_"),
                os.path.isfile(pth),
                "block",
                ("%s present" % label) if os.path.isfile(pth) else ("%s MISSING" % label),
                fix="Re-run Windows installer (not the Mac .sh)" if not os.path.isfile(pth) else None,
            ))

    # v1597 — CONSOLE BEACON: does this machine actually appear at bull-4-u.com/console?
    # severity is WARN and NEVER block/fail — an offline night must not turn the doctor red
    # (v840 learned that already). It only has to be VISIBLE.
    # ── v1607 — THE ONE THING THAT STOPS RECORDING, AND THE DOCTOR NEVER MENTIONED IT ──────
    # _screen_recording_ok_quick() has existed since v1251 and is used to REFUSE ON AIR. It was
    # never reported as a health fact, so on 2026-08-03 the doctor said "overall ok: True" on a
    # console that could not record at all: no grant → /api/on refuses → the agent never spawns →
    # black Theatre and one-frame reels. Konyo read that as the app being broken and lost an hour.
    #
    # A check that can BLOCK the primary action must be visible BEFORE he presses it, not only as
    # the refusal afterwards. Severity 'block' because that is exactly what it does.
    if sys.platform == "darwin":
        _sr = _screen_recording_ok_quick()
        checks.append(_chk(
            "screen_recording", bool(_sr), "block",
            ("granted to this process — ON AIR can pin the D2R window"
             if _sr else
             "NOT granted to this Python — ON AIR will refuse and NOTHING will record. This "
             "console is running headless; a headless launch does not inherit the grant."),
            None if _sr else
            ("Quit this console, then: bash tv/tvd-scan.sh (or open TV DIABLO.app via Terminal), "
             "and tick Python in System Settings -> Privacy & Security -> Screen Recording")))

    # ── SEAL — reels whose index was lost play as a BLACK theatre, and nothing ever said so ──
    # Severity 'warn', not block: the footage is recoverable (the index rebuilds from the frame
    # filenames), it just is not playable until it is rebuilt.
    _noidx = _reels_missing_index()
    checks.append(_chk(
        "reels_indexed", not _noidx, "warn",
        ("every reel in frames/hist has an index.json — the theatre can play them all"
         if not _noidx else
         "%d reel%s hold frames on disk with NO index.json, so the theatre skips them and plays "
         "BLACK: %s. The footage is NOT lost — an index rebuilds from the frame filenames."
         % (len(_noidx), "" if len(_noidx) == 1 else "s",
            ", ".join("%s (%d frames)" % (n, c) for n, c in _noidx[:6]))),
        None if not _noidx else
        "Restart TV DIABLO — this console rebuilds every missing reel index at boot. Standalone: "
        "`python3 tv/reel_repair.py` to survey, `--apply` to rebuild (idempotent, never "
        "overwrites a usable index)."))

    _bs = _beacon_status()
    _bt = _beacon_snapshot().get("ts")
    _age = (time.time() - _bt) if isinstance(_bt, (int, float)) else None
    _cnt = "%d attempts / %d failed" % (_bs["attempts"], _bs["failures"])
    # v1597.1 — READ THE ENVIRONMENT LIVE, not only what the last attempt happened to record.
    # `suppressedBy` is stamped by _console_beacon() when it returns early, so a console asked
    # "will this machine appear in the fleet?" BEFORE any beacon has run reported the generic
    # "NOT reaching the fleet tracker" — pointing Konyo at his internet connection when the real
    # answer was a variable set in his own shell. The question this check answers is about the
    # CURRENT environment, so it has to look at the current environment.
    _live_supp = ("CI" if os.environ.get("CI") else
                  "GITHUB_ACTIONS" if os.environ.get("GITHUB_ACTIONS") else
                  "TVD_NO_BEACON" if os.environ.get("TVD_NO_BEACON") else "")
    if _live_supp or _bs["suppressedBy"]:
        _bs = dict(_bs, suppressedBy=(_live_supp or _bs["suppressedBy"]))
    if _bs["suppressedBy"]:
        checks.append(_chk(
            "console_beacon", True, "warn",
            "beacon deliberately OFF because %s is set in this environment — this machine will "
            "NOT be listed at bull-4-u.com/console, on purpose (%s)" % (_bs["suppressedBy"], _cnt)))
    elif _bs["lastOk"] and _age is not None and _age <= 900:
        checks.append(_chk(
            "console_beacon", True, "warn",
            "checked in %s (HTTP %s)%s · %s" % (
                _bs["lastOkAt"] or _bs["lastAttempt"],
                _bs["code"] if _bs["code"] is not None else "?",
                (" · fleet %d online" % _bs["fleet"]) if isinstance(_bs["fleet"], int) else "",
                _cnt)))
    elif _bs["lastOk"]:
        checks.append(_chk(
            "console_beacon", False, "warn",
            "last successful check-in %s (%s ago) — the 240s heartbeat loop may be dead · %s" % (
                _bs["lastOkAt"] or _bs["lastAttempt"],
                ("%d min" % (_age / 60)) if _age is not None else "unknown",
                _cnt),
            "Restart TV DIABLO; the beacon heartbeat re-fires on boot and every 240s"))
    else:
        _never = "never once succeeded on this install" if not _bs["lastOkAt"] else (
            "last success %s" % _bs["lastOkAt"])
        checks.append(_chk(
            "console_beacon", False, "warn",
            "NOT reaching the fleet tracker — %s · last attempt %s · %s · %s" % (
                _never, _bs["lastAttempt"] or "none recorded",
                _bs["error"] or "no error recorded (no attempt yet)", _cnt),
            "this machine will NOT appear at /console — check internet access to bull-4-u.com, "
            "the Basic credential, and whether CI / GITHUB_ACTIONS / TVD_NO_BEACON is set in "
            "your environment"))

    ok = not any((not c["ok"]) and c["severity"] == "block" for c in checks)

    try:
        with open(LOG_PATH, "rb") as f:
            log_tail = f.read()[-2048:].decode("utf-8", "replace")
    except Exception:
        log_tail = "(no log yet)"

    ship = _windows_ship() if IS_WIN else None
    return {
        "ok": ok,
        "platform": "windows" if IS_WIN else ("mac" if sys.platform == "darwin" else sys.platform),
        "shipPlatform": (ship or {}).get("platform") if ship else None,
        "shipVer": (ship or {}).get("ver") if ship else None,
        "shipName": (ship or {}).get("name") if ship else None,
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



# ══ GROK EYES (G5) — REMOVABLE ════════════════════════════════════════════════
# Optional parallel/primary vision lane. OFF by default. See tv/G5_GROK_EYES_REMOVAL.md
# TO REMOVE: delete this block + routes /api/g5_* + g5 fences in tv_diablo.py + g5_grok_eyes.py
try:
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import g5_grok_eyes as _G5
except Exception:
    _G5 = None


def _g5_status():
    try:
        return _G5.status() if _G5 is not None else {
            "present": False, "on": False, "mode": "off", "hasKey": False,
        }
    except Exception:
        return {"present": False, "on": False, "mode": "off", "hasKey": False}


def _intake_dual_runners(here, g5_mode, *, local_on=True):
    """Ordered dual subscription intake receivers (Claude + Grok).

    Both lanes are subscription-CLI only (claude -p / grok -p) — never API keys.
    Website proxy is NOT in this list (handler falls through separately).

      off      → Claude only (cousin-safe default; pre-G5 behavior)
      shadow   → Claude first, Grok second (failover; Claude leads)
      primary  → Grok first, Claude second (failover; Grok leads)

    Returns list of (lane_label, mjs_path). Empty when local intake disabled.
    """
    if not local_on:
        return []
    claude = os.path.join(here, "intake_local.mjs")
    grok = os.path.join(here, "intake_grok_sub.mjs")
    mode = (g5_mode or "off").strip().lower()
    out = []
    if mode == "primary" and os.path.isfile(grok):
        out.append(("grok-subscription", grok))
        if os.path.isfile(claude):
            out.append(("subscription", claude))
    elif mode == "shadow":
        if os.path.isfile(claude):
            out.append(("subscription", claude))
        if os.path.isfile(grok):
            out.append(("grok-subscription", grok))
    else:
        # off / unknown: Claude only
        if os.path.isfile(claude):
            out.append(("subscription", claude))
    return out
# ══ END GROK EYES (G5) ════════════════════════════════════════════════════════


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
        # v1898 — THE SAME PATH RULE AS THE ISOLATION ONE, and here it is a 403 guard.
        #
        # ⚠ SAYING WHAT THIS DOES *NOT* FIX, because I nearly wrote the opposite: ART_DIR is ALREADY
        # os.path.realpath'd at its definition, so the symlink half of this hazard does not exist in
        # this repo and never did. I had written a comment claiming it did before checking line 98.
        #
        # What IS real: on his Windows machine a case difference between the resolved target and
        # ART_DIR makes startswith say no, and the traversal guard fails CLOSED on his own art. That
        # is a 403 on every picture, on the machine the suite cannot run on.
        # _under resolves both sides and asks the filesystem (inode identity) before falling back to
        # a case-normalised prefix, so this is exactly as strict as before — normalising both sides
        # identically cannot admit a path outside ART_DIR — and stops refusing legitimate ones.
        # [[dual-machine-setup]]
        try:
            import tv_diablo as _tvd3
            _ok = _tvd3._under(target, ART_DIR)
        except Exception:
            _ok = (target == os.path.realpath(ART_DIR)
                   or target.startswith(os.path.realpath(ART_DIR) + os.sep))
        if not _ok:
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
        # v1638 — A REPAIRED ASSET MUST NOT STAY INVISIBLE FOR A DAY. This sent
        # `public, max-age=86400`, so the webview reused its cached copy for 24h WITHOUT ASKING.
        # art/mephisto_graphic.png was repaired IN PLACE at v1636 (v269 had overwritten it with a
        # soulstone by fuzzy name match) and Konyo still saw the soulstone: same URL, new bytes,
        # and the browser never requested it. `?v=` on the URL was the alternative and it is worse
        # — bible.html builds art URLs in ~60 places (static src= plus artUrl/tzArtFor/
        # _itemArtImg/_runBossArt), so it means touching every site and remembering forever, on
        # exactly the class that has already been one-off patched twice (v284, v287) and never
        # generalised. `no-cache` does NOT mean "do not cache": it means "cache, but revalidate".
        # With the ETag below the revalidation is a bodyless 304, and this server is loopback.
        etag = '"%s"' % hashlib.md5(data).hexdigest()
        if self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", "no-cache")
            self._cors()
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("ETag", etag)
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
                    # v1408 — finds/register: prefer sealed kai_report when journal lacked the
                    # register ledger (split-session / re-pull / incomplete journal append).
                    # Cross-ref real reel so "What I found" + chapters aren't empty when KAI sealed.
                    if _finds is None:
                        _reg2 = _rreport.get("register")
                        _ritems2 = None
                        if isinstance(_reg2, list) and _reg2:
                            _ritems2 = _reg2
                        elif isinstance(_reg2, dict):
                            _ritems2 = _reg2.get("items")
                            if _registered is None and _reg2.get("count") is not None:
                                _registered = _reg2.get("count")
                        if isinstance(_ritems2, list) and _ritems2:
                            _srt2 = sorted(
                                _ritems2,
                                key=lambda it: (-_KAI_TIER_RANK.get((it.get("tier") or ""), 0),
                                                -(it.get("firstSeenTs") or 0)))
                            _finds = [{"name": it.get("name"), "tier": it.get("tier"),
                                       "loc": it.get("loc"), "frameId": it.get("frameId"),
                                       "ts": it.get("firstSeenTs")}
                                      for it in _srt2[:16]]
                            if _registered is None:
                                _registered = len(_ritems2)
                            if _topFind is None and _srt2:
                                _tf2 = _srt2[0]
                                _topFind = {"name": _tf2.get("name"), "tier": _tf2.get("tier")}
                    if _kc is None and isinstance(_rreport.get("classes"), dict):
                        _kc = _rreport.get("classes")
                    if _km is None and _rreport.get("missedFrames") is not None:
                        _km = _rreport.get("missedFrames")
                    # v1408 — judge-proof coverage (missedFrames, not kai-judge-inflated unread)
                    _cov_fix = _coverage_from_report(_rreport)
                    if _cov_fix:
                        _coverage = {"read": _cov_fix["read"], "total": _cov_fix["total"],
                                     "gaps": _cov_fix["gaps"]}
                    _cfd = _rreport.get("classFrames")
                    if isinstance(_cfd, dict) and _cfd:
                        _sidr = str(sess[0].get("sessionId") or "")
                        # v1332 B4 — the reel's classFrame carries only {f, ts}; source each frame's
                        # AREA from the nearest deep read (±5s) so its game-true label can name the zone.
                        _cf_areas = [(int(r2.get("captureTs") or r2.get("ts") or 0), str(r2.get("area") or "").strip())
                                     for r2 in sess if r2.get("lane") == "deep" and str(r2.get("area") or "").strip()]

                        def _cf_nearest_area(ts):
                            if not ts:
                                return ""
                            best, bd = "", 5001
                            for _rt, _ar in _cf_areas:
                                _d = abs(_rt - ts)
                                if _d <= 5000 and _d < bd:
                                    best, bd = _ar, _d
                            return best

                        def _cf_forward_area(ts):
                            # B5 (ribbon consistency) — a transition frame borrows the zone being
                            # ENTERED (the forward law shared with the reconciler), never the nearest
                            # (which can be the PREVIOUS zone). Honest-absent → "ENTERING (loading)".
                            return _forward_area_from(ts, _cf_areas, 8000)

                        _cf = []
                        for _scn, _fr in _cfd.items():
                            if not isinstance(_fr, dict) or not _fr.get("f"):
                                continue
                            _cf_scn = str(_scn).strip().lower()
                            _cf_ts = _fr.get("ts")
                            # v1332 B4 — game-true label on each classFrame so the chapter ribbon
                            # lights up on real reels (was reading a `native` that wasn't here yet).
                            _cf.append({"scene": _cf_scn,
                                        "thumb": "reel_" + _sidr + "/" + _fr["f"],
                                        "frameId": str(_fr["f"]).rsplit(".", 1)[0],
                                        "ts": _cf_ts,
                                        "native": (_diablo_scene_label(_cf_scn,
                                                   _cf_forward_area(_cf_ts) if _cf_scn == "transition"
                                                   else _cf_nearest_area(_cf_ts))
                                                   if _cf_scn else None)})
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
                # v1408 — deep journal names not yet in finds (retro/register gap): surface as finds
                # so dossier "What I found" + chapters stay honest to live deep + sealed register.
                _have_nms = set()
                if isinstance(_finds, list):
                    for _fi in _finds:
                        _n = str((_fi or {}).get("name") or "").strip().lower()
                        if _n:
                            _have_nms.add(_n)
                _extra = []
                for r2 in sess:
                    if r2.get("lane") != "deep":
                        continue
                    for _nm in (r2.get("names") or []):
                        _ns = str(_nm or "").strip()
                        if not _ns or _ns.lower() in _have_nms:
                            continue
                        try:
                            if _register_is_junk(_ns.lower()) or _register_is_anchor(_ns.lower()):
                                continue
                        except Exception:
                            pass
                        _have_nms.add(_ns.lower())
                        _extra.append({"name": _ns, "tier": None,
                                       "loc": r2.get("stashTab") or r2.get("scene"),
                                       "frameId": r2.get("frameId"),
                                       "ts": r2.get("captureTs") or r2.get("ts")})
                if _extra:
                    _finds = (list(_finds or []) + _extra)[:16]
                    if _registered is None:
                        _registered = len(_finds)
                    elif isinstance(_registered, int):
                        _registered = max(int(_registered), len(_have_nms))
                out.append({"watchdogViolations": _wd, "tallies": _tl, "kaiMissed": _km, "kaiClasses": _kc,
                            "sceneReads": _scene_reads or None, "tabReads": _tab_reads or None,
                            "sceneFingerprint": _session_scene_fingerprint(sess),   # v1326 B8 — farming%/townTrips/portals/topArea (Diablo-native, honest)
                            "judged": len(_keepers), "regrets": _regrets, "registered": _registered,
                            "finds": _finds, "topFind": _topFind,   # v1254 R1 — 📖 what KAI witnessed this session
                            "coverage": _coverage, "classFrames": (_class_frames or None),   # v1276 (D5 engine) — decision-story meter + montage
                            "superRecovery": _super_recovery, "missedFrames": _missed_frames,   # v1278 (D6 engine) — recovery badge + missed-text drill
                            "sealMs": _seal_ms, "regretItems": _regret_items,   # v1280 (D7 engine) — seal-latency chip + regret spotlight
                            "n": i, "t0": sess[0].get("ts"), "t1": sess[-1].get("ts"),
                            # v1563 — READ SPAN, not wall-clock. t0..t1 is the session's first row to
                            # its last, which includes idle and any trailing heartbeat. One of his
                            # sessions spans 1798.9 MINUTES around 3.5 minutes of actual reading, and
                            # because the tile sums every session's reads over every session's span,
                            # that one ghost dragged the fleet rate to 1/hr when the honest figure is
                            # 283. A rate whose denominator is "how long the app was open" is not a
                            # reading rate. Measured from the reads' OWN timestamps.
                            "readMs": (lambda _t: (max(_t) - min(_t)) if len(_t) > 1 else 0)(
                                # v1574 — a row with a missing or zero ts must be EXCLUDED, not
                                # counted as the epoch. `or 0` let one null drag min(ts) to 0, so
                                # a two-read session would span max(ts) - 0 = ~56 YEARS and drown
                                # the fleet rate at ~0/hr — the exact ghost-span class v1563 was
                                # written to kill, reintroduced by its own guard.
                                [_t for _t in ((r2.get("ts") or 0) for r2 in sess
                                 if not r2.get("sessionEnd") and r2.get("scene") != "session_end"
                                 and r2.get("mode") != "session_end" and r2.get("kind") != "skip"
                                 and r2.get("lane") not in ("kai", "verify", "intake")) if _t > 0]),
                            "reads": len([r2 for r2 in sess if not r2.get("sessionEnd") and r2.get("scene") != "session_end" and r2.get("mode") != "session_end" and r2.get("kind") != "skip" and r2.get("lane") not in ("kai", "verify", "intake")]), "frames": len(frames),
                            "named": sum(1 for r in sess if r.get("names")),
                            "areas": areas[:6], "stub": (len([r2 for r2 in sess if not r2.get("sessionEnd") and r2.get("scene") != "session_end" and r2.get("mode") != "session_end" and r2.get("kind") != "skip"]) < 3
                             and _reeln == 0),   # v885 (Grok #1) — a 1-read ghost never poses as a run
                            # v1866 — A SIMULATION IS NOT A RUN, and until now it looked exactly
                            # like one. `stub` above means something else entirely (a 1-read ghost
                            # with no footage), so it never excluded a sim session: his six- and
                            # seven-frame SIM sessions passed that filter and were counted as runs
                            # recorded today. Under TV_STUB the deep reader returns canned rows
                            # whose scene defaults to "gameplay", so a Chronicle page open on
                            # screen is journaled as gameplay and the readers look broken when
                            # nothing is wrong with them. Read from the rows themselves: the new
                            # per-row stamp, or the mode the stub branch has always written.
                            "sim": any(bool(r2.get("sim")) or r2.get("mode") == "stub"
                                       for r2 in sess),
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
                    # v1508 — THEATRE SPEAKS DIABLO. Konyo: "the readers and diablo language
                    # obviously in the THEATRE mode also so i can surgically debug whats needed and
                    # not right." Theatre is where he scrubs frames to find what a reader got wrong,
                    # and a caption saying `stash` tells him nothing about what the AI was LOOKING at.
                    # The label comes from _diablo_scene_label — the SAME function the receipts feed
                    # uses — so the two surfaces can never drift into describing one frame two ways
                    # (that split is what REG-076 was made of). The raw scene stays on the beat right
                    # above this, so a bug is still traceable back to the machine word.
                    "diablo": _diablo_scene_label(r.get("scene", ""), r.get("area", ""),
                                                  r.get("chronicleTab", "")),
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
                    # v894 — index.json first (O(n) no re-stat name parse thrash when present),
                    # now via chronicle_retro so a reel whose seal never wrote one is rebuilt from
                    # its filenames instead of falling through as an unindexed frame scan.
                    _frames = _reel_index_frames(_reel_dir)
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
                            # E4 — route the sealed-marking through the ONE tested law
                            # (_kai_engine_frame_effective) instead of an inline copy: it enforces
                            # the kaiVer≥3 gate, so a sub-Phase-C reel yields NO authoritative
                            # frames (honest-absent → the UI shows provisional, never a weak guess
                            # as sealed), and the serve path can never drift from the tested law.
                            # kaiVer-4 reels (all current) → identical _engmap.
                            for _ef in _kai_engine_frame_effective(
                                    _krep.get("engineFrames") or [], [], _krep.get("kaiVer")):
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
        if path == "/api/fleet":
            # v1496 — who is online and when each machine was last here (60s cached, read-only)
            self._json(200, fleet_presence(force=("force=1" in (self.path or ""))))
            return
        if path == "/api/chronicle_sweep":
            # v1519 — progress + result of the REAL sweep. GET never starts one; starting spends
            # money, and a GET that spends money is a GET a page-refresh can fire twice.
            self._json(200, chronicle_sweep_state())
            return
        if path == "/api/chronicle_gate":
            # v1531 — what different thresholds WOULD do to the last sweep. Re-gates, never re-reads.
            import urllib.parse as _up
            q = _up.parse_qs((self.path.split("?", 1) + [""])[1])
            self._json(200, chronicle_regate(
                conf_floor=(q.get("floor") or [None])[0],
                min_witnesses=(q.get("witnesses") or [None])[0]))
            return
        if path == "/api/reader_health":
            # v1537 — which link of the read chain broke, on THIS machine. Free, read-only.
            self._json(200, reader_health())
            return
        if path == "/api/chronicle_visits":
            # v1522 — the Chronicle panels he opened in game, as an offer. Read-only, costs nothing.
            # v1820 — now the MERGED offer: journalled visits AND reels he focused on the Chronicle
            # that no sweep has read. Same payload shape, so the console renders both without a
            # change; a reel row carries source="reel" and the reel id that reads it.
            self._json(200, chronicle_offer())
            return
        if path == "/api/chronicle_scan":
            # v1516 — THE FREE PASS. Groups every sealed reel's frames into still-runs and reports
            # what a real sweep WOULD cost. Zero model calls, zero writes — this is the number he
            # gets to check before agreeing to spend anything.
            self._json(200, chronicle_scan_cost())
            return
        if path == "/api/vault_scan":
            # v1578 — THE FREE PASS, vault edition. Prices a vault retro sweep on HIS film.
            # Zero model calls, zero writes.
            self._json(200, vault_scan_cost())
            return
        if path == "/api/vault_sweep":
            # v1578 — progress + result of the vault sweep. GET never starts one; starting spends
            # money, and a GET that spends money is a GET a page-refresh can fire twice.
            self._json(200, vault_sweep_state())
            return
        if path == "/api/mini":
            # v1578 — ⏱ MINI CAPTURE countdown. Read-only; secondsLeft is clamped at 0.
            # v1603 — ships the focus vocabulary too, so the console renders its buttons from the
            # engine's list instead of holding a second copy that can drift out of step.
            # v1870 — publish the DURATIONS beside the vocabulary. The console kept its own
            # MINI_FOCUS_SECS table, so raising a bound here would have left the button still
            # saying 75s and still asking for it. One source. [[copy-drift]]
            self._json(200, dict(mini_state(), focuses=list(MINI_FOCUSES),
                                 focusSecs={f: _mini_bounds(f)[0] for f in MINI_FOCUSES},
                                 focusMax={f: _mini_bounds(f)[1] for f in MINI_FOCUSES}))
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
        # ══ GROK EYES (G5) — REMOVABLE (delete this stanza) ══
        if path == "/api/g5_status":
            self._json(200, _g5_status())
            return
        # ══ END GROK EYES (G5) ══
        if path == "/api/autoroute-sweep":
            # G3 — read-only de-duped sweep of what KAI witnessed → per-tracker tally.
            # Writes nothing; the bible.html panel diffs merge-max + applies on click.
            try:
                rows = self._load_journal_cached()
                reels = []
                try:
                    for d in sorted(os.listdir(HIST_DIR)):
                        if not d.startswith("reel_"):
                            continue
                        rep = _reel_report_cached(os.path.join(HIST_DIR, d))
                        if isinstance(rep, dict):
                            reels.append(rep)
                except Exception:
                    pass
                try:
                    bmt = os.path.getmtime(BIBLE)
                except Exception:
                    bmt = 0.0
                cache_key = (round(bmt, 3), len(rows), id(rows), len(reels))
                out = _autoroute_sweep_cached(rows, reels, cache_key)
                self._json(200, dict(out, ok=True))
            except Exception as e:
                self._json(500, {"ok": False, "msg": str(e)})
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
        if path == "/api/forensics":
            # 🔬 READS FORENSICS — the per-item forensic X-ray for one reel (sid) or the newest.
            from urllib.parse import parse_qs, urlparse
            q = parse_qs(urlparse(self.path).query)
            sid = (q.get("sid") or [""])[0].strip()
            self._json(200, _forensics_payload(sid))
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
            # v817 / v1418 — fleet unity: force-fetch then report behind-count + howTo.
            try:
                fl = fleet_origin_status(force_fetch=True)
                self._json(200, {
                    "ok": bool(fl.get("ok", True)),
                    "behind": int(fl.get("behind") or 0),
                    "latest": fl.get("latest") or "",
                    "head": fl.get("head") or "",
                    "origin": fl.get("origin") or "",
                    "dirty": bool(fl.get("dirty")),
                    "ver": fl.get("ver") or status_payload().get("ver"),
                    "howTo": fl.get("howTo") or "",
                })
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
                    _paths = _journal_ring()
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

        if path == "/api/chronicle_apply":
            # v1523 — the write. POST only, and it goes through the BOARD, which owns the ledger.
            self._json(200, chronicle_apply(body.get("proposal")))
            return
        if path == "/api/board_ownership":
            # 2026-08-20 — the READ direction of that same channel. The board owns the ledger, so
            # the board is who to ask; the console had only ever been able to tell it to write.
            # POST like its sibling, not because this spends anything (it spends nothing) but
            # because the two halves of one channel should not answer to different verbs.
            self._json(200, board_ownership(sample=body.get("sample") or 0))
            return
        if path == "/api/chronicle_sweep":
            # v1519 — POST starts it, deliberately. This is the call that spends subscription reads,
            # and a GET that spends is a GET a page refresh can fire twice.
            try:
                _lim = int(body.get("limit") or 0) or None
            except (TypeError, ValueError):
                _lim = None
            # v1524 — force=true re-reads reels the memory says are done (after a prompt change,
            # a new lane, or plain doubt). Opt-in, because it re-spends the whole sweep.
            self._json(200, chronicle_sweep_start(limit=_lim, force=bool(body.get("force")),
                                                  visit=body.get("visit")))
            return
        if path == "/api/chronicle_forget":
            self._json(200, chronicle_forget_swept())
            return
        if path == "/api/vault_apply":
            # v1578 — the write. POST only, and it goes through the BOARD, which owns the vault.
            self._json(200, vault_apply(body.get("proposal")))
            return
        if path == "/api/vault_sweep":
            # v1578 — POST starts it, deliberately (this is the call that spends reads).
            # Needs NO live agent: retro reads sealed film.
            try:
                _vlim = int(body.get("limit") or 0) or None
            except (TypeError, ValueError):
                _vlim = None
            self._json(200, vault_sweep_start(limit=_vlim, force=bool(body.get("force"))))
            return
        if path == "/api/vault_forget":
            # {"ledger":true} also drops the accumulated evidence — rebuildable from the reels.
            self._json(200, vault_forget(ledger=bool(body.get("ledger"))))
            return
        if path == "/api/evrank":
            # ⚔ EV-RANK — the client POSTs its MISSING grails + each one's best-source odds/kph
            # (from its Calculator); the engine ranks them by expected-hours-to-next-find. Stateless,
            # honest-absent (invalid odds → unranked, never a fabricated rank).
            try:
                _conf = float(body.get("confidence", 0.5))
            except (TypeError, ValueError):
                _conf = 0.5
            self._json(200, _ev_rank(body.get("items"), _conf))
            return

        # ══ GROK EYES (G5) — REMOVABLE (delete this stanza) ══
        if path == "/api/identity_name":
            # v1496 — {"name": "Konyo's MacBook"} · empty string clears back to the hostname
            data = set_install_nickname(body.get("name"))
            _console_beacon_async("rename")   # the fleet learns the new name immediately
            self._json(200, {"ok": True, "identity": data})
            return
        if path == "/api/g5_toggle":
            # {"mode":"off"|"shadow"|"primary"} or {"on":true} → primary
            if _G5 is None:
                self._json(200, {"present": False, "on": False, "mode": "off", "hasKey": False})
                return
            try:
                if "mode" in body:
                    _G5.set_mode(body.get("mode"))
                elif "on" in body:
                    _G5.set_on(bool(body.get("on")))
            except Exception as e:
                # v1709 — last-known status on a failed toggle is a 200 that
                # looks like the switch took. Name the failure.
                st = dict(_g5_status())
                st["ok"] = False
                st["error"] = str(e)[:160]
                self._json(200, st)
                return
            st = dict(_g5_status())
            st["ok"] = True
            self._json(200, st)
            return
        if path == "/api/g5_login":
            # v1381.2 — ⚡ Authorize Grok: spawn `grok login --oauth` (browser once).
            # No-spam: already-authorized / in-flight short-circuit. Optional setPrimary.
            if _G5 is None:
                self._json(200, {"ok": False, "present": False, "msg": "G5 module missing"})
                return
            try:
                out = _G5.start_login(prefer_oauth=bool(body.get("oauth", True)))
            except Exception as e:
                self._json(200, {"ok": False, "msg": str(e)[:160]})
                return
            # After auth lands, optional auto-PRIMARY (default true when caller asks)
            if out.get("ok") and (out.get("reason") == "already-authorized"
                                  or body.get("setPrimary") or body.get("primary")):
                try:
                    if out.get("hasSubscription") or out.get("reason") == "already-authorized":
                        _G5.set_mode("primary")
                except Exception:
                    pass
            st = _g5_status()
            if isinstance(out, dict):
                out = dict(out)
                out["status"] = st
            self._json(200, out if isinstance(out, dict) else {"ok": False, "status": st})
            return
        # ══ END GROK EYES (G5) ══
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
                with open(_journal_path(), "a", encoding="utf-8") as f:
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
                        # ── v1945 — KEEP THE REASON THE SENDER ALREADY SENT ──────────────────
                        # Konyo: "also AI read needs an update". MEASURED over his journal: 46
                        # intake records, 45 of them ok:false, and not ONE carrying a reason —
                        # every single one `{tab,kind,counts:{},total:0,errors:0,items:[],ok:false}`.
                        # So a deliberate guard hold, a failed read, and a read that honestly found
                        # nothing were indistinguishable in the record, and the feed could only say
                        # "routed".
                        #
                        # The sender was never the problem. The kai-funnel fire has posted
                        # `guardHeld:!applied` since v1197 (control_app.py ~7323) and the route
                        # guard writes `refused`/`err` (~7942). THIS handler built the record from
                        # seven fields and dropped the rest on the floor — the explanation arrived
                        # and was thrown away at the door. [[the-unjoined-end]]
                        **({"guardHeld": True} if body.get("guardHeld") else {}),
                        **({"err": str(body.get("err"))[:200]} if body.get("err") else {}),
                        "why": _intake_why(body),
                    },
                    "frameId": _fid,
                    "capSrc": _cap_src,
                    "note": ("📸 intake · " + str(body.get("tab") or body.get("kind") or "shot"))[:80],
                }
                with open(_journal_path(), "a", encoding="utf-8") as f:
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
            # v1380.1 — DUAL RECEIVER (G5): optional SuperGrok `grok -p` lane (intake_grok_sub.mjs)
            # same contract, NO API keys. Order by G5 mode: off=claude only; shadow=claude then
            # grok; primary=grok then claude. Both are subscription-CLI only.
            # v1379 — server-side gate so a stuck engine driver cannot stampede intake:
            # max 1 in-flight + min gap between starts (also enforced inside intake_local.mjs).
            _now_i = time.time()
            _last_i = float(globals().get("_INTAKE_LAST_TS") or 0)
            _inflight_i = int(globals().get("_INTAKE_INFLIGHT") or 0)
            try:
                _gap_i = float(os.environ.get("TV_INTAKE_MIN_GAP_S", "12") or 12)
            except Exception:
                _gap_i = 12.0
            if _inflight_i > 0 or (_now_i - _last_i) < _gap_i:
                self._json(429, {"ok": False, "lane": "subscription-throttled",
                                 "msg": "intake rate-limited (subscription leak guard)",
                                 "retry_s": max(1, int(_gap_i - (_now_i - _last_i)))})
                return
            _here_i = os.path.dirname(os.path.abspath(__file__))
            # ══ GROK EYES (G5) — dual intake receiver (subscription CLI only) ══
            _g5_mode = "off"
            try:
                if _G5 is not None:
                    _g5_mode = str(_G5.mode() or "off")
            except Exception:
                _g5_mode = "off"
            _runners = _intake_dual_runners(
                _here_i, _g5_mode,
                local_on=(os.environ.get("TV_INTAKE_LOCAL", "1") != "0"),
            )
            # ══ END GROK EYES (G5) ══
            # v919 (Grok REAL EYES R1) — STRICT mode: a silent local-lane failure falling
            # through to the website proxy can fake-green a "real subscription" run on the
            # website's key. TV_INTAKE_LOCAL_STRICT=1 → answer 502 honestly, never fall back.
            _strict = os.environ.get("TV_INTAKE_LOCAL_STRICT") == "1"
            if _runners:
                try:
                    globals()["_INTAKE_INFLIGHT"] = _inflight_i + 1
                    globals()["_INTAKE_LAST_TS"] = _now_i
                    _nice_kw = ({"creationflags": 0x4000 | _WIN_CREATE} if IS_WIN
                                else {"preexec_fn": (lambda: os.nice(10))})   # v879 — intake yields to the game
                    _last_err = ""
                    for _lane_lab, _runner in _runners:
                        try:
                            _pr = subprocess.run(
                                ["node", _runner],
                                input=json.dumps({"path": path, "body": body}).encode("utf-8"),
                                capture_output=True, timeout=150, **_nice_kw)
                            if _pr.returncode == 0 and _pr.stdout:
                                _out = json.loads(_pr.stdout.decode("utf-8", "replace"))
                                _pl = (_out.get("body") or "").encode("utf-8")
                                # Prefer a body that is not an obvious hard error if multiple lanes
                                _ok_body = True
                                try:
                                    _bj = json.loads(_out.get("body") or "{}")
                                    if isinstance(_bj, dict) and _bj.get("error"):
                                        _ok_body = False
                                        _last_err = str(_bj.get("error"))[:200]
                                except Exception:
                                    pass
                                if _ok_body or _lane_lab == _runners[-1][0]:
                                    self.send_response(int(_out.get("status") or 200))
                                    self.send_header("Content-Type", "application/json")
                                    self.send_header("X-Intake-Lane", _lane_lab)
                                    self.send_header("Content-Length", str(len(_pl)))
                                    self.end_headers()
                                    self.wfile.write(_pl)
                                    return
                            else:
                                _last_err = (_pr.stderr or b"").decode("utf-8", "replace")[-300:]
                        except Exception as _lane_ex:
                            _last_err = str(_lane_ex)[:200]
                            continue
                    if _strict:
                        self._json(502, {"ok": False, "lane": "subscription-failed",
                                         "msg": "all local intake runners failed (strict: no website fallback)",
                                         "detail": _last_err})
                        return
                except Exception as _ex:
                    if _strict:
                        self._json(502, {"ok": False, "lane": "subscription-failed",
                                         "msg": "local intake runner error (strict): " + str(_ex)[:200]})
                        return
                    pass   # any local failure → website proxy below
                finally:
                    globals()["_INTAKE_INFLIGHT"] = max(
                        0, int(globals().get("_INTAKE_INFLIGHT") or 1) - 1)
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
                removed = 0
                fids = set()
                for _p in _journal_ring():
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
                                 "sessionId": sid, "reel": "reel_" + sid, "kaiVerTarget": 6})
            except Exception as e:
                self._json(500, {"ok": False, "msg": str(e)[:160]})
            return
        if path == "/api/mini":
            # v1578 — ⏱ MINI CAPTURE: ON AIR with a bound, for the 10–40s he spends parked in
            # the stash on gems / runes / materials. Same start_agent(), same seal path.
            # The clamped value is ECHOED (5 and 999 come back honest, never silently altered).
            self._json(200, mini_start(body.get("seconds"), test=bool(body.get("test")),
                                       focus=body.get("focus")))
            return
        if path == "/api/on":
            # v1578 — REFUSE LOUDLY while a mini is counting down (the mirror of mini_start's
            # refusal for a live session). Silently starting a second capture over the same reel
            # makes every read afterwards unattributable to the session he thinks it came from.
            _mn = mini_state()
            if _mn.get("running"):
                self._json(200, {"ok": False, "mode": "mini",
                                 "why": "already recording — seal the current session first",
                                 "secondsLeft": _mn.get("secondsLeft", 0)})
                return
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
            # v1410/v1420 — Esc empty-stack + programmatic quit: same force-exit path as ✕
            # v1576 — ANSWER HONESTLY. Both this call and its fallback swallowed every
            # failure and the handler then hard-coded {"ok": True, "control quitting"} —
            # a false green: nothing armed, process alive, board told "quitting". Same
            # doctrine as /api/off (v926.2): on failure, report it instead of painting OK.
            r = None
            try:
                r = _request_console_exit("api-quit", hard_delay=0.55)
            except Exception as _e:
                try:
                    _mark_window_gone("api-quit")
                    _schedule_exit_stop("api-quit")
                    _arm_force_exit("api-quit-fallback", delay=0.55)
                except Exception as _e2:
                    _e = _e2
                r = {"ok": bool(globals().get("_FORCE_EXIT_ARMED")),
                     "armed": bool(globals().get("_FORCE_EXIT_ARMED")),
                     "windowDestroyed": False,
                     "errors": ["request_console_exit: %s" % str(_e)[:120]]}
            if not isinstance(r, dict):
                r = {"ok": bool(globals().get("_FORCE_EXIT_ARMED")),
                     "armed": bool(globals().get("_FORCE_EXIT_ARMED")),
                     "windowDestroyed": False, "errors": []}
            if r.get("ok"):
                self._json(200, dict(r, msg="control quitting"))
            else:
                self._json(500, dict(r, ok=False,
                                     msg="quit FAILED — nothing armed, console still up: "
                                         + ("; ".join(r.get("errors") or []) or "unknown")))
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


def _win_primary_mutex():
    """v1406 — Windows single primary instance (Desktop double-click used to spawn 2x --open).
    Returns (handle, is_owner). Non-owner must not bind this port or open a second window.

    v1484 — THE MUTEX IS SCOPED BY PORT. It used to be one machine-wide name, which is a broader
    claim than the problem it was solving: what v1406 actually prevents is two primaries fighting
    over the SAME port and window. A process on a different control port is a different instance by
    definition — and that is exactly what a test harness is.

    The cost of the wider claim was `tv/test_roundtrip_sim.py`, which boots its own control_app on
    :17956. Whenever the real app was open, the harness child exited immediately with
    "already running (primary mutex)", the suite's setUpClass timed out after ~100s, and it
    reported `Ran 0 tests / FAILED (errors=1)`. Since a developer's app is usually open while they
    work, the suite was effectively unrunnable on the machine that needed it most — and its output
    said nothing about mutexes, so it read as a mysterious server-startup failure.

    Scoping by port keeps v1406's protection intact where it matters (:17772 is still strictly
    single-primary, so the desktop icon still cannot spawn two) while letting an isolated harness
    run alongside a live console.
    """
    if not IS_WIN:
        return None, True
    try:
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.windll.kernel32
        kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        kernel32.GetLastError.restype = wintypes.DWORD
        name = "Local\\TV_DIABLO_CONTROL_PRIMARY_v1_p%d" % CONTROL_PORT
        handle = kernel32.CreateMutexW(None, False, name)
        ERROR_ALREADY_EXISTS = 183
        owned = kernel32.GetLastError() != ERROR_ALREADY_EXISTS
        return handle, bool(owned)
    except Exception:
        return None, True


def _win_focus_existing_console():
    """v1417 — bring the existing 'TV DIABLO' pywebview window forward (no second window).

    v1460 — HIDDEN windows count too. The old callback skipped every window that failed
    IsWindowVisible, and only ever restored IsIconic. A window that had been SW_HIDE-ed
    (the ✕ path's old hide() fallback could leave one behind) was therefore invisible to
    every focus attempt: control still answered :17772, so the launcher took its
    "already up - focus and leave" branch, focus found nothing, and the Desktop icon did
    nothing forever. Collect visible AND hidden matches, prefer visible, SW_SHOW a hidden
    one before restoring/raising it."""
    if not IS_WIN:
        return False
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        EnumWindows = user32.EnumWindows
        GetWindowTextW = user32.GetWindowTextW
        IsWindowVisible = user32.IsWindowVisible
        SetForegroundWindow = user32.SetForegroundWindow
        ShowWindow = user32.ShowWindow
        IsIconic = user32.IsIconic
        SW_SHOW, SW_RESTORE = 5, 9
        vis, hidden = [], []

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def _cb(hwnd, _lp):
            buf = ctypes.create_unicode_buffer(256)
            GetWindowTextW(hwnd, buf, 256)
            title = buf.value or ""
            # v1463 — EXACT title only. The old prefix rule also matched the popout board
            # window "TV DIABLO — Board" (a separate --board-window process), so a visible
            # board could be reported as "the console window is up" while the real console
            # stayed hidden — defeating the v1460 fix's own proof. The console window is
            # created with the literal title "TV DIABLO" and never renamed at runtime.
            if title == "TV DIABLO":
                (vis if IsWindowVisible(hwnd) else hidden).append(hwnd)
                if IsWindowVisible(hwnd):
                    return False          # a visible window is the best case — stop early
            return True

        EnumWindows(_cb, 0)
        if not vis and not hidden:
            return False
        was_hidden = not vis
        hwnd = (vis or hidden)[0]
        if was_hidden:
            ShowWindow(hwnd, SW_SHOW)
        if IsIconic(hwnd):
            ShowWindow(hwnd, SW_RESTORE)
        raised = bool(SetForegroundWindow(hwnd))
        now_visible = bool(IsWindowVisible(hwnd))
        # v1460 Law 9 — report what is TRUE, and only claim success when the window is
        # actually visible. A cross-process ShowWindow does not reliably un-hide a WinForms
        # window that was born SW_HIDE, so "found it" is not "the human can see it".
        print(
            "📺 focused existing TV DIABLO window (refused second instance) "
            f"[{'un-hid' if was_hidden else 'visible'} hwnd={hwnd} raised={raised} "
            f"visible={now_visible}]",
            flush=True,
        )
        return now_visible
    except Exception as e:
        print(f"⚠ focus existing: {e}", flush=True)
        return False


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

    # v1406 — single primary on Windows before bind race (second process exits quiet, no dialog)
    _mtx, _mtx_owner = _win_primary_mutex()
    if IS_WIN and not _mtx_owner:
        # Port may already be serving; never open a second primary window.
        print("TV DIABLO already running on :%d (primary mutex) — not opening a second instance. "
              "A harness wanting its own server should set TV_CONTROL_PORT to a free port; the "
              "mutex is scoped per port." % CONTROL_PORT, flush=True)
        if open_ui:
            _win_focus_existing_console()
        sys.exit(0)

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
        # v1406 Windows: if a window is already up OR doctor is answering, never reclaim /
        # never open a second WebView — quiet exit (Desktop double-click race).
        if IS_WIN and open_ui:
            already = _window_present() or _sock_open(CONTROL_PORT)
            if already:
                print(
                    f"TV DIABLO already open on :{CONTROL_PORT} — not opening a second window.\n"
                    f"   ({e})",
                    flush=True,
                )
                _win_focus_existing_console()
                sys.exit(0)
        if open_ui and not _window_present():
            print(f"TV DIABLO already serving on :{CONTROL_PORT} (headless) — "
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
                print(f"TV DIABLO reclaim bind still failed ({e2}) — attaching window-only "
                      f"(Screen Recording may be missing on the headless primary)…",
                      flush=True)
                globals()["_WINDOW_ONLY"] = True
                open_control_window()
                return
            # reclaimed — fall through as PRIMARY (do not return)
        else:
            # v781 — a REAL window already exists → refuse a second one, point at the existing.
            print(
                f"TV DIABLO window is already open on :{CONTROL_PORT} — not opening a second one.\n"
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

    # SEAL — anything an earlier kill left index-less is playable again the next time he starts
    # the app, with no action from him. Prints only when it actually repaired something.
    try:
        _reel_sweep_indexes(why="console boot")
    except Exception as _se:
        print("\u26a0 boot index sweep skipped: %s" % _se, flush=True)

    threading.Thread(target=_bridge_prober, daemon=True, name="tvd-prober").start()   # v872
    threading.Thread(target=_console_beacon_loop, daemon=True, name="tvd-beacon").start()   # v875
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    time.sleep(0.2)

    if open_ui and not no_open:
        # Blocks until the native window is closed; close handlers already armed force-exit.
        open_control_window()
        # v1410/v1420 UX — ✕ means QUIT. If Cocoa returned from webview.start(), finish cleanly
        # here. If Cocoa hung, the force-exit deadline from the close handler already killed us.
        try:
            _request_console_exit("main-after-window", hard_delay=0.4)
        except Exception:
            _mark_window_gone("main-after-window")
            _schedule_exit_stop("main-after-window")
            _arm_force_exit("main-after-window", delay=0.4)
        print("📺 native window closed — quitting cleanly (✕ = exit). "
              f"Supervisor/Desktop can relaunch headless on :{CONTROL_PORT}.", flush=True)
        # Brief settle so session seal / agent SIGTERM can land before we die
        try:
            time.sleep(0.35)
        except Exception:
            pass
        try:
            srv.shutdown()
        except Exception:
            pass
        os._exit(0)

    # headless server mode (tests / --no-open)
    # v1761 — THE WATCHDOG LIVES HERE TOO, OR HEADLESS HAS NO WATCHDOG AT ALL.
    #
    # v1745 started tvd-chron-autoread inside open_control_window(), beside the engine driver and
    # the closer. Those two genuinely need the window — they drive the board tab. The chronicle
    # watchdog does not: it reads recorded frames and starts sweeps, and never touches a window.
    #
    # Measured, and it is why "why is it not automatically synced" stayed true even with a console
    # running: started with --no-open, the console served every API correctly for 2h45m, reported
    # three unread visits, answered _agent_alive() False and "no sweep running" — and
    # tv/chron_autoread.json never appeared, because the thread that writes it was never started.
    # Every lamp green, the job simply absent. A background job attached to a WINDOW is a background
    # job that vanishes the moment you run without one. [[the-unjoined-end]]
    if not globals().get("_WINDOW_ONLY"):
        try:
            threading.Thread(target=_chron_autoread_loop, daemon=True,
                             name="tvd-chron-autoread").start()
            print("   chronicle watchdog armed (headless) — unread visits sweep themselves")
        except Exception as _ae:
            print("⚠ chronicle watchdog failed to start (%s) — visits will need the read button" % _ae)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n📺 control UI server stopping — exit safeguard cuts ON AIR.")
        _console_exit_stop_onair("keyboard-interrupt")
        srv.shutdown()


if __name__ == "__main__":
    main()
