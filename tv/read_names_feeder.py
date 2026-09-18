# -*- coding: utf-8 -*-
"""THE FEEDER THE AUTO LANE NEVER HAD — hands autoOwed to the EXISTING vault_apply door.

read_names_lane.split() already judges every journal-ring PANEL name through the REAL gate
(vault_retro.gate, 0.55 conf / 2 witnesses) and separates HELD from OWED. NOTHING called it to
write — its own header says so: "the accumulator has no other feeder... they were never judged."
This module is that caller, and it invents NO judgement of its own:

    split().autoOwed  ->  rows shaped by vault_retro._owned_row  ->  control_app.vault_apply
                          (the door re-gates EVERY row at the write — v1595/v3066/v3067 —
                           and the board's own vaultAccumApply does the landing: dated,
                           merge-max, undoable, the same tick his hand uses)

⚠⚠ WHAT THIS DELIBERATELY DOES NOT TOUCH:
  · reel_retention's `rows-not-banked` hold stays INDEPENDENT. Banking through the board is
    what legitimately releases footage for pruning; this module never reads or writes any
    retention store, and never touches vault_accum.json — that stays the paid sweep's
    (write_census.py:55). [[the-unjoined-end]]
  · autoHeld, the 96 panel names, floor and chronicle sightings are OUT OF SCOPE — held is
    his call, floor/chronicle can never name a cell. This consumes autoOwed ONLY.

⚠ THE DOOR'S REFUSAL IS A RESULT, NOT AN ERROR. vault_apply saying no (gate refusal, board
closed, timeout) comes back verbatim in `why` and ok stays False — a feeder that swallowed a
refusal would be the unjoined end wearing a wire. [[feedback-verify-not-proxy]]

⚠ A name whose container is UNPLACED or disagreed (split row `container` is None) is DECLINED
with its reason, never guessed — the board's lane field would be a coin-flip.
[[unknown-stays-unknown]]
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable
    enable()
except Exception:
    pass

#: unattended writer -> per-tick cap, same doctrine as reel_route_lane's 8 (control_app:23429).
MAX_PER_TICK = 4


def plan(sp=None):
    """Which owed names CAN be handed to the door right now, and which decline. -> dict
    Writes nothing. UNKNOWN stays UNKNOWN: a lane that could not measure plans nothing."""
    out = {"ok": False, "bankable": [], "declined": [], "why": ""}
    try:
        import read_names_lane as RNL
    except Exception as e:
        out["why"] = "read_names_lane would not import (%s)" % type(e).__name__
        return out
    sp = sp if sp is not None else RNL.split()
    if not (isinstance(sp, dict) and sp.get("ok")):
        out["why"] = "the split could not measure: %s" % str((sp or {}).get("why"))[:120]
        return out
    owed = sp.get("autoOwed")
    if owed is None:
        out["why"] = ("the rosters could not be read (%s) — owed is UNKNOWN, not empty"
                      % str(sp.get("rosterWhy") or "")[:90])
        return out
    rows_by_name = {r.get("name"): r for r in (sp.get("auto") or [])}
    for nm in owed:
        r = rows_by_name.get(nm) or {}
        if r.get("container") and r.get("containerAgreed"):
            out["bankable"].append({"name": nm, "lane": r["container"]})
        else:
            out["declined"].append({"name": nm,
                                    "why": r.get("containerWhy")
                                           or "no agreed container — the board's lane "
                                              "field would be a guess"})
    out["ok"] = True
    out["why"] = "%d bankable, %d declined" % (len(out["bankable"]), len(out["declined"]))
    return out


def apply(by, sp=None, limit=None):
    """Hand each bankable owed name to control_app.vault_apply. -> dict

    ⚠ `by` IS REQUIRED, exactly as reel_route_lane.apply requires it.
    ⚠⚠ ASKS may("vault.apply") — the lock exists (self_arming.py:147, destructive, bar 0.722)
    and until now NOTHING automated consulted it; his hand on /api/vault_apply stays ungated.
    An unreadable lock fails CLOSED with its reason kept.
    """
    out = {"ok": False, "banked": 0, "refused": 0, "declined": 0,
           "names": [], "by": str(by or "").strip(), "why": ""}
    if not out["by"]:
        out["why"] = "apply() needs a `by` — a write that cannot say what fed it is a write "
        return out
    try:
        import self_arming as _sa
        _ok, _lw = _sa.may("vault.apply")
    except Exception as _e:
        _ok, _lw = False, ("the lock could not be read (%s), which is UNKNOWN and fails closed"
                           % type(_e).__name__)
    if not _ok:
        out["why"] = "vault.apply is LOCKED — %s" % _lw
        return out
    p = plan(sp)
    if not p["ok"]:
        out["why"] = p["why"]
        return out
    out["declined"] = len(p["declined"])
    if not p["bankable"]:
        out["ok"] = True
        out["why"] = "no owed name is bankable this tick (%s)" % p["why"]
        return out
    try:
        import read_names_lane as RNL
        import vault_retro as VR
        import control_app as CA
    except Exception as e:
        out["why"] = "a module would not import (%s)" % type(e).__name__
        return out
    ev, _ewhy = RNL.evidence()
    if ev is None:
        out["why"] = "the journal ring vanished between judge and write (%s)" % _ewhy
        return out
    todo = p["bankable"] if limit is None else p["bankable"][:max(0, int(limit))]
    rows = []
    for b in todo:
        pile = ev.get(b["name"]) or []
        row = VR._owned_row((b["name"], b["lane"]), pile)   # witnesses WITH conf — v1786
        row["evidence"] = pile                              # the door re-gates on this
        rows.append(row)
    prop = {"ok": True, "owned": rows, "unsure": [], "throwOut": [],
            "sessionsRead": sorted({e.get("session") for r in rows
                                    for e in (r.get("evidence") or []) if e.get("session")}),
            "generatedTs": int(time.time() * 1000), "source": "read-names-feeder",
            "by": out["by"]}
    v = CA.vault_apply(prop)   # THE ONE DOOR. Its refusal comes back verbatim.
    if isinstance(v, dict) and v.get("ok"):
        out["ok"] = True
        out["banked"] = len(rows)
        out["names"] = [r["name"] for r in rows]
        out["why"] = "banked %d owed name(s) through the board's own tick" % len(rows)
    else:
        out["refused"] = len(rows)
        out["names"] = [r["name"] for r in rows]
        out["why"] = ("the door refused: %s"
                      % str((v or {}).get("why") or "no reason given")[:200])
    return out


if __name__ == "__main__":
    r = apply(by="cli:read_names_feeder")
    print(u"%s — %s" % ("OK" if r["ok"] else "NO", r["why"]))
    sys.exit(0 if r["ok"] else 1)
