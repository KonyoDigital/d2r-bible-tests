#!/usr/bin/env python3
"""ONE HEALTH ENGINE — red/green flags for the console. IT REPORTS. IT NEVER REPAIRS.

Konyo, 2026-08-29: "not sure we need a live watchdog that FIXES things — might be wrong for the
console and make a bug worse.. but maybe a system that does red/green flag us.. so same here should
be a system working one unit system engine locked in... especially with all the fixes and versions
we shipped it makes things less messy going forward and keeps control"

⚠ REPORT, NEVER REPAIR — and he is right about why. An auto-healer can turn one fault into two and
do it unattended; a flag can only ever be wrong about a colour. Nothing in this module writes,
deletes, restarts or repairs anything, and a test pins that.

⚠ IT IS NOT AN AUTHORITY EITHER. frame_authority owns deletion. chronicle_retro owns grounding.
This engine reports ON them and decides nothing — otherwise two gates drift apart, which is the
exact defect class it exists to surface.

WHY IT EXISTS, in two measurements from the day it was written:

  · THE v2205 VAULT UNDO WAS ARMED ON EVERY BOARD since v2203, and would have dropped 273 of his
    280 owned names. Nothing on his console said so. It was found by reading code, not by any
    watching thing. That is check `armed_migration`, and it is the highest-value check here.

  · REGISTER FAILED FOR DAYS saying "this board build has no chronicleApply". The console's doctor
    rail had ALREADY diagnosed it — "the board is not open in the window" — in a paragraph of prose
    nobody reads. The information existed; the SURFACE did not. That is check `board_join`.

A check returns one of four states and UNKNOWN IS FIRST-CLASS:
    ok       measured, and fine
    warn     measured, and worth his attention
    blocked  measured, and something downstream cannot proceed
    unknown  COULD NOT BE MEASURED — never renders as ok. "The board is not open so its store
             cannot be asked" is not "the store is fine". [[unknown-stays-unknown]]
"""
import io
import json
import os
import re
import time

HERE = os.path.dirname(os.path.abspath(__file__))
OK, WARN, BLOCKED, UNKNOWN = "ok", "warn", "blocked", "unknown"


def _row(cid, state, line, evidence=None, measured_at=None):
    """One flag. `line` is what he reads; `evidence` is what earned it."""
    return {"id": cid, "state": state, "line": line,
            "evidence": list(evidence or []), "measuredAt": measured_at or int(time.time() * 1000)}


def _read_json(path):
    """-> (obj|None, why). None is UNREADABLE, which is never ok."""
    p = path if os.path.isabs(path) else os.path.join(HERE, path)
    if not os.path.exists(p):
        return None, "%s does not exist" % os.path.basename(p)
    try:
        with io.open(p, encoding="utf-8") as fh:
            return json.load(fh), ""
    except Exception as e:
        return None, "%s could not be read: %s" % (os.path.basename(p), e)


# ── CHECK 1 ─────────────────────────────────────────────────────────────────────────────────────
def check_lanes():
    """Are the extraction lanes doing work, and do they agree? Delegates to lane_health (v2272)."""
    try:
        import lane_health as LH
    except Exception as e:
        return _row("lanes", UNKNOWN, "lane health could not be loaded — %s" % e)
    rep = LH.report()
    bad = [l for l in rep["lanes"].values() if l["state"] == "stalled"]
    unk = [l for l in rep["lanes"].values() if l["state"] == "unknown"]
    div = [d for d in rep["divergences"] if d["state"] == "diverged"]
    ev = [l["why"] for l in rep["lanes"].values()] + [d["why"] for d in rep["divergences"]]
    if unk:
        return _row("lanes", UNKNOWN, "a lane's store could not be read", ev)
    if bad or div:
        worst = (bad + div)[0]
        n = len(bad) + len(div)
        return _row("lanes", WARN,
                    "%d lane issue%s — %s" % (n, "" if n == 1 else "s",
                                              (worst.get("lane") or "+".join(worst.get("pair", [])))),
                    ev)
    return _row("lanes", OK, "every extraction lane is fresh and aligned", ev)



def check_shadow_watch():
    """Is the thing that is supposed to notice him playing actually looking?

    ★ THE FAILURE THIS EXISTS FOR: he played a whole evening with the shadow switch ON and got ZERO
    reels, because shadow only READ frames another mode had rolled. Nothing said so — the panel
    reported "armed", which is true and implies something false. A watcher that has never looked is
    the same defect wearing a different word. [[label-outlived-referent]]
    """
    try:
        import control_app as _ca
    except Exception as e:
        return _row("shadowWatch", UNKNOWN, "control_app will not import — %s" % str(e)[:70])
    try:
        st = _ca._shadow_state()
        w = _ca.shadow_watch_state()
    except Exception as e:
        return _row("shadowWatch", UNKNOWN, "could not read the watcher: %s" % str(e)[:70])
    if not isinstance(w, dict) or w.get("ok") is False:
        return _row("shadowWatch", UNKNOWN,
                    str((w or {}).get("why") or "the watcher's record is unreadable"))
    if not st.get("on"):
        return _row("shadowWatch", OK, "the shadow reader is switched OFF, so nothing is watching "
                                       "for the game — by his choice")
    looked = w.get("lookedAt")
    if looked is None:
        return _row("shadowWatch", WARN,
                    "the shadow switch is ON and the watcher has NEVER looked for the game — "
                    "playing would produce nothing, which is exactly the evening that was lost")
    import time as _t
    age = (_t.time() * 1000.0 - float(looked)) / 60000.0
    if age > 10:
        return _row("shadowWatch", WARN,
                    "the shadow switch is ON but the watcher last looked %.0f minutes ago — it "
                    "should look every 20 s, so it is not running" % age)
    return _row("shadowWatch", OK,
                "watching for the game every 20 s (last look %.0f s ago) · %s reel(s) started · %s"
                % (age * 60, w.get("starts") or 0, str(w.get("why") or "")[:80]))



def check_readers_agree():
    """Are the two game readers still calibrated to the same screen?

    stash_eye (left-anchored panel) and chronicle_template (centered modal) each carry their own
    calibration film of HIS monitor. The geometry differs for a real reason; the SCREEN does not.
    A recalibration of one is silent in the other, and the symptom is a reader that quietly stops
    finding panels rather than an error anyone sees. [[copy-drift]]
    """
    try:
        import stash_eye as _se
        import chronicle_template as _ct
    except Exception as e:
        return _row("readers", UNKNOWN, "a reader will not import — %s" % str(e)[:70])
    a = getattr(_se, "_CROP_CAL_FILM", None)
    b = getattr(_ct, "_CAL_FILM", None)
    if not a or not b:
        return _row("readers", UNKNOWN,
                    "one reader does not publish its calibration film, so they cannot be compared")
    if tuple(a) != tuple(b):
        return _row("readers", WARN,
                    "the two readers are calibrated to DIFFERENT screens — stash_eye %s vs "
                    "chronicle_template %s. One was re-measured and the other was not; the stale "
                    "one will quietly stop finding its panel." % (tuple(a), tuple(b)))
    return _row("readers", OK,
                "both readers calibrated to the same screen %s (aspect %.4f)"
                % (tuple(a), a[0] / float(a[1])))


# ── CHECK 2 — the one that would have caught the loaded gun ─────────────────────────────────────
#: destructive one-shot blocks, and the SHAPE of a record that proves they may fire.
#: Each entry: (id, human name, the flag whose PRESENCE used to be trusted, the file it lives in)
#: ⚠ v2281 — NO HARDCODED NAMES. The first cut carried ONE tuple naming d2r_vaultBackfill_v2200 by
#: hand, so it caught the v2205 loaded gun only because I already knew the answer — and it would not
#: have caught the next one, which is the only thing a watching check is for.
#:
#: The class IS mechanically findable, and the two polarities are opposites:
#:   `if (LSR.getItem(F)) return;`   — "already done, skip".  SAFE. A stray stamp DISABLES the block.
#:   `if (!LSR.getItem(F)) return;`  — "run ONLY when F is set". ARMED the moment anything else
#:                                     stamps F unconditionally, which is exactly what a RETIREMENT
#:                                     does. That was v2205: a retired migration stamped the flag on
#:                                     every load and a destructive undo trusted its presence.
#: Measured on bible.html 2026-08-30: 4 sites of the safe shape, 0 of the dangerous one. The 4/0
#: split is what makes the zero a measurement rather than a vacuous pass. [[regression-guard]]
#: ⚠ THE GATES USE CONSTANTS, NOT LITERALS. My first reader matched `LSR.getItem('flag')` and found
#: NOTHING, because every real site reads `if (window.LSR.getItem(DONE)) return;` with the flag name
#: bound above as `var DONE = 'd2r_...'`. The check said so out loud — UNKNOWN, "a broken reader,
#: not a clean tree" — instead of reporting a green sweep over zero sites, which is the whole reason
#: that branch exists. [[source-reading-guard]] [[feedback-suspect-the-instrument]]
_GATE_RE = re.compile(
    r"if\s*\(\s*!\s*(?:window\.)?LSR\.getItem\(\s*([A-Za-z0-9_']+)\s*\)\s*\)\s*return")
_SAFE_RE = re.compile(
    r"if\s*\(\s*(?:window\.)?LSR\.getItem\(\s*([A-Za-z0-9_']+)\s*\)\s*\)\s*return")
_CONST_RE = re.compile(r"(?:var|let|const)\s+([A-Za-z0-9_]+)\s*=\s*'([A-Za-z0-9_]+)'\s*;")


def _flag_of(token, src):
    """A gate names either the flag itself or a const bound to it. -> (flag, how) or (None, why)."""
    t = token.strip()
    if t.startswith("'"):
        return t.strip("'"), "literal"
    for name, val in _CONST_RE.findall(src):
        if name == t:
            return val, "const %s" % t
    return None, "the gate reads %s and nothing binds it — UNRESOLVED" % t


def armed_flags(src):
    """Every flag gated in the DANGEROUS polarity that something else also stamps. -> list of dicts.

    Pure, so it can be tested against a reconstruction of the pre-v2275 bytes without a browser.
    """
    out = []
    for m in _GATE_RE.finditer(src):
        flag, how = _flag_of(m.group(1), src)
        if not flag:
            # ⚠ an unresolvable gate is NOT a safe gate. Report it so it cannot pass silently.
            out.append({"flag": m.group(1), "stamps": -1, "retiredStamp": 0, "how": how,
                        "unresolved": True, "at": m.start()})
            continue
        stamped = len(re.findall(r"setItem\(\s*'%s'" % re.escape(flag), src))
        # the DONE-const form: `setItem(DONE, ...)` where DONE binds this flag
        for name, val in _CONST_RE.findall(src):
            if val == flag:
                stamped += len(re.findall(r"setItem\(\s*%s\s*," % re.escape(name), src))
        retired = len(re.findall(
            r"setItem\([^)]{0,40}?JSON\.stringify\(\s*\{\s*retired", src))
        if stamped:
            out.append({"flag": flag, "stamps": stamped, "retiredStamp": retired, "how": how,
                        "unresolved": False, "at": m.start()})
    return out


def check_armed_migrations():
    """Is a destructive one-shot able to fire on a board right now?

    ⚠ SOURCE-LEVEL ON PURPOSE. It cannot read his board's localStorage from here — that store is
    pywebview/WebKit and this process does not own it — so it asks the only question it can answer
    honestly: does the SHIPPED CODE still gate a destructive block on a flag that something else
    stamps unconditionally? That is exactly the v2205 defect and it is checkable without touching
    his data.
    """
    try:
        with io.open(os.path.join(os.path.dirname(HERE), "bible.html"), encoding="utf-8") as fh:
            src = fh.read()
    except Exception as e:
        return _row("armed_migration", UNKNOWN, "bible.html could not be read — %s" % e)
    armed = armed_flags(src)
    safe = len(_SAFE_RE.findall(src))
    ev = ["%d gate(s) in the safe polarity (already-done, skip)" % safe,
          "%d gate(s) in the v2205 polarity (runs ONLY when the flag is set)"
          % len(_GATE_RE.findall(src))]
    if armed:
        a = armed[0]
        ev = [("%s: UNRESOLVED — %s" % (x["flag"], x["how"])) if x.get("unresolved")
              else ("%s (%s): stamped %d×%s" % (x["flag"], x["how"], x["stamps"],
                    ", RETIREMENT stamp present" if x["retiredStamp"] else ""))
              for x in armed] + ev
        return _row("armed_migration", BLOCKED,
                    "%d destructive one-shot(s) ARMED — %s gates on a flag that is stamped "
                    "elsewhere" % (len(armed), a["flag"]), ev)
    # ⚠ a zero here is only a measurement because the SAFE polarity is found too. If neither shape
    # is found the reader is broken, not the code, and that must not read as clean.
    if not safe and not _GATE_RE.findall(src):
        return _row("armed_migration", UNKNOWN,
                    "no one-shot gate of EITHER polarity was found, so this check matched nothing "
                    "at all — that is a broken reader, not a clean tree", ev)
    return _row("armed_migration", OK,
                "no destructive one-shot gates on a flag that is stamped unconditionally", ev)


# ── CHECK 3 — the one the doctor rail already knew and could not say ────────────────────────────
def check_board_join(evaluate=None, payload=None):
    """Is the console able to reach the BOARD, or is it about to ask itself?

    `evaluate` is an injected callable (page_js) -> value, so this stays testable and so this module
    never reaches for a window itself. Absent, the answer is UNKNOWN — not ok.
    """
    # v2277 — THE PAYLOAD PATH IS THE ONE THAT ACTUALLY RUNS. Nothing on the console holds a
    # window handle it can hand this module, so the `evaluate` door was a tap nobody could open and
    # the flag sat UNKNOWN forever. board_ownership already reaches into the board and now reports
    # `hasChronicleApply`, so the console rail answers from a real read of the real window.
    # [[plumbing-with-no-tap]]
    if payload is not None:
        if not isinstance(payload, dict) or not payload.get("ok"):
            why = (payload or {}).get("why") if isinstance(payload, dict) else None
            return _row("board_join", UNKNOWN,
                        "the board did not answer, so whether registering can work is unmeasured"
                        "%s" % ((" — %s" % str(why)[:80]) if why else ""))
        if "hasChronicleApply" not in payload:
            return _row("board_join", UNKNOWN,
                        "this console build does not report hasChronicleApply — nobody asked, "
                        "which is not the same as 'it is fine'")
        path = str(payload.get("path") or "?")
        if payload.get("hasChronicleApply"):
            return _row("board_join", OK, "the board is reachable at %s" % path,
                        ["chronicleApply present"])
        return _row("board_join", BLOCKED,
                    "the window that answered is %s and has no chronicleApply — registering "
                    "cannot work from here%s" % (path,
                    " (that path is the CONSOLE, not the board)" if path in ("/", "") else ""),
                    ["path=%s" % path, "chronicleApply absent"])
    if evaluate is None:
        return _row("board_join", UNKNOWN,
                    "the board window was not offered to this check, so whether the console can "
                    "reach it is unmeasured — that is not the same as 'it is fine'")
    try:
        raw = evaluate("(function(){return JSON.stringify({p:location.pathname,"
                       "has:typeof window.chronicleApply==='function'})})()")
        got = json.loads(raw) if isinstance(raw, str) else (raw or {})
    except Exception as e:
        return _row("board_join", UNKNOWN, "the board window did not answer — %s" % e)
    if not isinstance(got, dict) or "has" not in got:
        return _row("board_join", UNKNOWN, "the board window answered something unreadable")
    path = str(got.get("p") or "?")
    if got.get("has"):
        return _row("board_join", OK, "the board is reachable at %s" % path, ["chronicleApply present"])
    return _row("board_join", BLOCKED,
                "the window answered from %s and has no chronicleApply — registering cannot work "
                "from here%s" % (path, " (that path is the CONSOLE, not the board)" if path in ("/", "") else ""),
                ["location.pathname=%s" % path, "chronicleApply absent"])


# ── CHECK 4 ─────────────────────────────────────────────────────────────────────────────────────
def check_orphans():
    """Anything of ours busy AND old — the 28-hour core-burner class."""
    try:
        import my_orphans as MO
    except Exception as e:
        return _row("orphans", UNKNOWN, "the orphan sweep could not be loaded — %s" % e)
    rows = MO.suspects()
    if not rows:
        return _row("orphans", OK, "nothing of ours is both busy and old")
    ev = ["pid %s %.0f%% CPU %.0f min — %s" % (r.get("pid"), r.get("cpu", 0), r.get("minutes", 0),
                                               str(r.get("cmd"))[:70]) for r in rows]
    return _row("orphans", WARN, "%d process(es) busy and old" % len(rows), ev)


CHECKS = [check_lanes, check_armed_migrations, check_board_join, check_orphans,
          check_shadow_watch, check_readers_agree]


def report(evaluate=None, board=None):
    """Every flag, in one object. `board` is a /api/board_ownership payload. -> dict"""
    rows = []
    for fn in CHECKS:
        try:
            rows.append(fn(evaluate, board) if fn is check_board_join else fn())
        except Exception as e:                                   # a check that throws is UNKNOWN
            rows.append(_row(getattr(fn, "__name__", "?"), UNKNOWN,
                             "this check raised and therefore measured nothing — %s" % e))
    worst = OK
    for r in rows:
        if r["state"] == BLOCKED:
            worst = BLOCKED; break
        if r["state"] in (WARN, UNKNOWN) and worst == OK:
            worst = r["state"]
    return {"state": worst, "rows": rows,
            "why": "; ".join(r["line"] for r in rows if r["state"] != OK) or "everything measured is fine"}


GLYPH = {OK: "🟢", WARN: "🟡", BLOCKED: "🔴", UNKNOWN: "⚪"}


def say(rep):
    return ["%s %-18s %s" % (GLYPH.get(r["state"], "·"), r["id"], r["line"]) for r in rep["rows"]]


def main(argv=None):
    rep = report()
    for line in say(rep):
        print("   " + line)
    print()
    print({OK: "🟢 nothing is asking for you.",
           WARN: "🟡 something wants a look.",
           BLOCKED: "🔴 something downstream cannot proceed.",
           UNKNOWN: "⚪ something could not be measured — that is not the same as fine."}[rep["state"]])
    return 0 if rep["state"] == OK else 1


if __name__ == "__main__":
    import sys
    try:
        sys.path.insert(0, HERE)
        import console_safe as _cs
        _cs.enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
