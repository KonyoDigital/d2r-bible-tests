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


# ── CHECK 2 — the one that would have caught the loaded gun ─────────────────────────────────────
#: destructive one-shot blocks, and the SHAPE of a record that proves they may fire.
#: Each entry: (id, human name, the flag whose PRESENCE used to be trusted, the file it lives in)
ARMED_MIGRATIONS = [
    ("vault_undo_v2205", "the v2205 vault undo",
     "d2r_vaultBackfill_v2200", "bible.html"),
]


def check_armed_migrations():
    """Is a destructive one-shot able to fire on a board right now?

    ⚠ THIS CHECK IS SOURCE-LEVEL ON PURPOSE. It cannot read his board's localStorage from here —
    that store is pywebview/WebKit, not something this process owns — so it asks the only question
    it can answer honestly: does the SHIPPED CODE still gate a destructive block on a flag that
    something else stamps unconditionally? That is exactly the v2205 defect, and it is checkable
    without touching his data.
    """
    ev = []
    try:
        with io.open(os.path.join(os.path.dirname(HERE), "bible.html"), encoding="utf-8") as fh:
            src = fh.read()
    except Exception as e:
        return _row("armed_migration", UNKNOWN, "bible.html could not be read — %s" % e)
    for mid, name, flag, _f in ARMED_MIGRATIONS:
        # the retired migration stamps the flag; if a gate still trusts its PRESENCE, it is armed
        stamps = ("setItem(DONE" in src) or ("setItem('%s'" % flag in src)
        trusts_presence = ("if (!window.LSR.getItem('%s')) return;" % flag) in src
        ev.append("%s: flag=%s stamped-somewhere=%s gate-trusts-presence=%s"
                  % (name, flag, stamps, trusts_presence))
        if stamps and trusts_presence:
            return _row("armed_migration", BLOCKED,
                        "%s is ARMED — its gate trusts a flag that is stamped on every load" % name,
                        ev)
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


CHECKS = [check_lanes, check_armed_migrations, check_board_join, check_orphans]


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
