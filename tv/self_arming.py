#!/usr/bin/env python3
"""A LOCK THAT UNLOCKS ITSELF — and cannot be opened by hand.

Konyo, 2026-09-02:

    "wilson scores all over.. once that's integrated anywhere and anyplace it can be, the system
     proves itself. START AT THE PRINTER AND REELS WITH THE WILSON SCORE FIRST so that can be done
     beforehand in order, and then once wilson score proves itself within the processing of reels —
     meaning THEATRE MODE AND THE SHELF... so if wilson score eventually proves itself within the
     optimizing and templated and routing down the river stream we mentioned, for each reel a
     unified logic, then it should work and THEN ARM ITSELF. arithmetic as you see.. A LOCK UNTIL
     IT AUTOMATICALLY UNLOCKS WITH A QUEUE FOR WILSON SCORE. this can be used in a bunch of places
     not yet built if we have them too."

This replaces "Konyo flips `_PRUNE_SAFE_TO_RUN` by hand". He does not want to be the arming
mechanism; he wants the system to EARN its permission and then take it.

═══ THE ONE THING THAT WOULD MAKE THIS A LIE ═══════════════════════════════════════════════════

**k and n count SABOTAGES, never agreements.** [[heart-first]] §5, and it is the whole risk:

    an invariant that always agrees may be perfect, or INERT, and those are indistinguishable.

A lock fed by an agreement-rate opens *because nobody ever tested it* — the exact failure the lock
exists to prevent, wearing the lock's own uniform. So:

    n = deliberate sabotages ATTEMPTED against this surface's guards
    k = times a guard REFUSED (went red) for its own reason

A guard that has never been sabotaged contributes NOTHING. `n == 0` is UNPROVEN, and unproven is
not failing — a low score names work to do, and a gate that turns amber at its own newest checks
is ignored within a week. [[heart-first]] again, and it is why `state()` has four values.

═══ WHY WILSON AND CONFLUENCE, BOTH ═══════════════════════════════════════════════════════════

`tv/confidence.py` is THE home for this maths and says why in its own words: "Wilson measures how
many looks agreed, never whether the looks were INDEPENDENT... The two run TOGETHER or neither
means anything." Four re-runs of one sabotage by one harness is one proof wearing four hats.

So a lock opens only when BOTH clear:

    wilson_lower(k, n) >= bar        how much evidence, honest about small n
    confluence(kinds)  >= kinds_bar  how many INDEPENDENT KINDS of evidence

⚠ This module CALLS confidence.py. It does not restate the maths. A second copy of a safety
routine is [[copy-drift]]'s worst case, because the two diverge and only one gets tuned.

═══ THE ORDER IS PART OF THE LOCK ═════════════════════════════════════════════════════════════

He gave a dependency chain, and a lock late in it cannot open early no matter how good its own
score is — proving the deleter in isolation proves nothing about the river feeding it:

    printer + reels  ->  theatre + shelf  ->  routing / the river  ->  the deleter

`after` encodes that. A lock whose prerequisite is not OPEN reports LOCKED with the prerequisite
named, never with its own score, so nobody reads a high number as "nearly there".

═══ WHAT THIS MODULE WILL NOT DO ═══════════════════════════════════════════════════════════════

It DECIDES and REPORTS. It never performs the action, never writes an unlock flag, and has no
override parameter — an override is the hand-arming this replaces. An unreadable ledger is
UNKNOWN, and UNKNOWN is LOCKED: fail closed, and say which of the two it is.
"""

import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from confidence import wilson_lower, confluence   # noqa: E402  — one home for the maths

#: runtime record of DECISIONS, like .console_scars.json and .second_eye.jsonl — untracked.
#: THE DEFAULT ONLY. Deliberately NOT `os.environ.get(...) or ...` at module level.
LEDGER = os.path.join(HERE, ".self_arming.jsonl")


def _ledger_path():
    """Where the proof queue lives, resolved at CALL time. -> str

    ⚠ v2438 — `test_import_bound_paths` CAUGHT THIS AS AN IMPORT-BOUND PATH AND IT WAS RIGHT.
    The first cut read the env var at module level, which freezes whatever the environment was at
    IMPORT: a fixture setting TV_SELF_ARMING_LEDGER afterwards is a silent no-op, and its proof
    rows land in HIS queue. That registry exists because exactly that truncated 525,187 bytes of
    paid page reads to 748. [[feedback-fixtures-never-touch-live-data]]

    Registering it as import-bound would have satisfied the gate. It is resolved at call time
    INSTEAD, because of what this file gates: a fixture that accidentally banks into the real
    queue does not merely corrupt a record — it RAISES A SCORE, and a raised score opens a lock
    that deletes footage. When a mistake's blast radius is his data, the fix goes in the
    fail-safe direction rather than the documented one.

    Both redirects work now: set TV_SELF_ARMING_LEDGER, or patch the module attribute.
    """
    return os.environ.get("TV_SELF_ARMING_LEDGER") or LEDGER

#: What counts as an INDEPENDENT KIND of proof, and what each is worth. Passed to confluence()
#: rather than hardcoded there, because what counts as independent differs per lane.
#: ⚠ An unknown kind scores 0 by design — a kind nobody has weighted is a kind nobody has thought
#: about, and a default would silently pay it as if someone had.
KINDS = {
    "sabotage": 1.0,    # a guard broken on purpose and watched to go red for its OWN reason
    "cross-family": 0.8,  # a different model family refused it on the real artifact
    "live": 0.7,        # measured against his running console, not a fixture
    "ci": 0.6,          # went red on a runner, on the same bytes
    "fixture": 0.3,     # a harness case — real, and the weakest kind on its own
}

#: name -> what it would do · the bar it must clear · what must be OPEN before it may open at all.
#: THE ORDER IS HIS. Nothing here may be reordered to make something arm sooner.
LOCKS = {
    # step 1 — the printer and the reels
    "vault.sweep_start": {
        "surface": "VAULT", "acts": "starts a paid sweep",
        "bar": 0.510, "kinds_bar": 1.0, "after": [],
    },
    # step 1 — the actions that change his ledger
    "vault.apply": {
        "surface": "VAULT", "acts": "mules items between characters",
        "bar": 0.722, "kinds_bar": 1.3, "after": ["vault.sweep_start"],
    },
    "vault.forget": {
        "surface": "VAULT", "acts": "drops the ledger",
        "bar": 0.722, "kinds_bar": 1.3, "after": ["vault.sweep_start"],
    },
    # step 4 — the deleter. Last, and it cannot be reached early.
    "prune.arm": {
        "surface": "THE RIVER", "acts": "deletes footage — there is no undo",
        "bar": 0.839, "kinds_bar": 1.8,
        "after": ["vault.sweep_start", "vault.apply"],
    },
}

# the four states, and they are four on purpose
OPEN = "OPEN"
LOCKED = "LOCKED"          # proven, and it did not clear the bar
UNPROVEN = "UNPROVEN"      # n == 0 — nobody has tested it. NOT a failure, NOT a score.
UNKNOWN = "UNKNOWN"        # the ledger could not be read. Fails closed, and says so.


def record(lock, kind, refused, note=""):
    """Append one SABOTAGE ATTEMPT and whether the guard refused. -> dict (the row written)

    `refused` True means the guard went RED for its own reason — that is the SUCCESS here, which
    reads backwards until you remember what is being measured: the ability to say no.
    """
    row = {
        "lock": str(lock), "kind": str(kind), "refused": bool(refused),
        "note": str(note or "")[:400], "ts": int(time.time() * 1000),
    }
    with io.open(_ledger_path(), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def _rows():
    """-> (list|None, why). None means UNREADABLE, which is never 'no proofs'."""
    p = _ledger_path()
    if not os.path.exists(p):
        return [], ""          # absent is legitimately empty: nothing has been proven yet
    out = []
    try:
        with io.open(p, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except ValueError:
                    # a line that will not parse is a hole in the evidence, not a blank one
                    return None, "%s has an unparseable row" % os.path.basename(p)
                if isinstance(r, dict):
                    out.append(r)
    except Exception as e:
        return None, "%s could not be read: %s" % (os.path.basename(p), e)
    return out, ""


def score(lock, rows=None):
    """The arithmetic for ONE lock. -> dict

    Never returns a wilson figure when n == 0. `wilson: None` means nobody looked; `0.0` would be
    a measurement nobody took. [[unknown-stays-unknown]]
    """
    spec = LOCKS.get(lock)
    if not spec:
        return {"lock": lock, "state": UNKNOWN, "why": "no such lock is declared"}
    if rows is None:
        rows, why = _rows()
        if rows is None:
            return {"lock": lock, "state": UNKNOWN, "why": why,
                    "k": None, "n": None, "wilson": None, "kinds": None}
    mine = [r for r in rows if r.get("lock") == lock]
    n = len(mine)
    k = len([r for r in mine if r.get("refused")])
    kinds = sorted({str(r.get("kind")) for r in mine if r.get("refused")})
    conf = confluence(kinds, KINDS)
    out = {"lock": lock, "surface": spec["surface"], "acts": spec["acts"],
           "k": k, "n": n, "kinds": kinds, "confluence": conf,
           "bar": spec["bar"], "kindsBar": spec["kinds_bar"], "after": list(spec["after"])}
    if n == 0:
        out["wilson"] = None
        out["state"] = UNPROVEN
        out["why"] = ("no sabotage has been attempted against this surface's guards, so there is "
                      "no evidence in either direction. That is not a failure.")
        return out
    w = wilson_lower(k, n)
    out["wilson"] = round(w, 4)
    if w < spec["bar"]:
        out["state"] = LOCKED
        out["why"] = ("%d of %d sabotages were refused; the Wilson lower bound is %.3f against a "
                      "bar of %.3f" % (k, n, w, spec["bar"]))
    elif conf < spec["kinds_bar"]:
        out["state"] = LOCKED
        out["why"] = ("the score clears (%.3f) but the evidence is too alike: kinds %s score %.2f "
                      "against %.2f. Wilson counts how many looks agreed, never whether they were "
                      "independent." % (w, kinds or "[]", conf, spec["kinds_bar"]))
    else:
        out["state"] = OPEN
        out["why"] = ("%d of %d sabotages refused · wilson %.3f >= %.3f · kinds %s = %.2f >= %.2f"
                      % (k, n, w, spec["bar"], kinds, conf, spec["kinds_bar"]))
    return out


def may(lock):
    """May this surface act right now? -> (bool, why)

    THE ORDER IS CHECKED FIRST. A lock late in his chain reports its blocked prerequisite rather
    than its own score, so a high number is never mistaken for "nearly there".
    """
    spec = LOCKS.get(lock)
    if not spec:
        return False, "no such lock is declared — an undeclared surface is never permitted"
    rows, why = _rows()
    if rows is None:
        return False, "UNKNOWN: %s. An unreadable proof queue fails CLOSED." % why
    for pre in spec["after"]:
        s = score(pre, rows)
        if s.get("state") != OPEN:
            return False, ("blocked upstream: %s is %s — %s. Proving this surface in isolation "
                           "proves nothing about what feeds it." % (pre, s.get("state"), s.get("why")))
    s = score(lock, rows)
    return (s.get("state") == OPEN), s.get("why")


def report():
    """Every lock, for a surface that must show its work. -> dict"""
    rows, why = _rows()
    if rows is None:
        return {"ok": False, "why": why,
                "locks": [{"lock": k, "state": UNKNOWN, "why": why} for k in sorted(LOCKS)]}
    out = [score(k, rows) for k in sorted(LOCKS)]
    return {"ok": True, "locks": out,
            "open": len([x for x in out if x.get("state") == OPEN]), "total": len(out)}


def main(argv):
    rep = report()
    print("SELF-ARMING LOCKS — %s" % ("%d of %d open" % (rep.get("open", 0), rep.get("total", 0))
                                      if rep.get("ok") else "UNREADABLE: " + rep.get("why", "")))
    for l in rep["locks"]:
        w = l.get("wilson")
        print("  %-9s %-20s %s" % (l.get("state"), l.get("lock"),
                                   ("wilson %.3f/%.3f" % (w, l["bar"])) if w is not None
                                   else "no sabotage attempted"))
        print("            %s" % (l.get("why") or ""))
    # a report is not a verdict: exit 0 always, because "nothing is open yet" is the CORRECT
    # state on a fresh tree and must not read as a broken build.
    return 0


if __name__ == "__main__":
    try:
        import console_safe as _cs
        _cs.enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
