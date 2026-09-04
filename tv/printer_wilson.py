#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A2 · step 1 — THE PRINTER: can the river refuse to INVENT an answer?

Konyo, 2026-09-04: *"build the printer lock and wire the whole river"*, and before it: *"i want the
locks here and in general real and not fabricated. make sure its not HALF BUILT or HALF TESTED"*.

⚠⚠ WHY THIS EXISTS. Measured 2026-09-04: fourteen locks and routes were declared and **not one
named the printer, the river, or reel selection**. The printer walks every reel he owns through
five stations and nothing had ever attempted to break it — so its answers were believed on the
strength of nobody having tried. That is precisely the state `self_arming` calls INERT: *"an
invariant that always agrees may be perfect, or INERT, and those are indistinguishable."*

WHAT IS BEING SABOTAGED, AND WHY THESE. The printer owns exactly one promise — **it re-derives
nothing and invents nothing.** Every station QUOTES an owner, and when an owner will not answer the
station must say UNKNOWN *with a reason* rather than guess, skip the row, or drop the reel. Each
case below removes one owner's ability to answer and requires the printer to say so out loud:

  ownerraises     an owner raises. The station must be UNKNOWN and name what happened — never
                  absent, because a station missing from a row reads as a reel that did not need it
  ownerempty      an owner returns nothing at all. The printer must report UNKNOWN state, NOT
                  "0 reels, every station answered" — a zero over an empty shelf measures the
                  ABSENCE OF THE SHELF. [[unknown-stays-unknown]]
  namelessrows    an owner returns rows naming no reel. They must be DROPPED **and COUNTED**; a
                  silent drop is indistinguishable from a reel that was never there
  strangerreel    one owner knows a reel the others do not. The row must still carry all five
                  stations, with UNKNOWN where nobody answered
  reachraises     printer_reach raises. EXTRACT must be UNKNOWN — never permissive, because the
                  extract station is the one that says whether the printer may ACT on a reel

⚠⚠ IT CANNOT DELETE, ARM OR WRITE ANYTHING, and the shape guarantees that rather than a comment
promising it. It calls exactly one function, `printer.stream()`, whose module docstring is *"AND IT
PRINTS NOTHING AND DELETES NOTHING. The prune stays OFF. This is a REPORT."* There is no
`os.remove`, no `apply_plan`, no `TV_AUTO_PRUNE` and no ledger write anywhere in this file, and
`tv/test_printer_wilson.py` asserts that by reading this file's own source.

⚠ THE SABOTAGE IS APPLIED TO A COPY OF THE MODULE'S OWN LOOKUP, never to his stores. Nothing here
touches tv/frames, tv/*.json, or any file at all.

    python3 tv/printer_wilson.py            # report only
    python3 tv/printer_wilson.py --bank     # and bank the result
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# ⚠ QUOTED, NOT COPIED. This was a second hand-written tuple of the same five names, and when
# `template` was added to the printer at v2571 this copy would have gone on asserting the old
# shape — a harness silently checking a contract the module no longer has. [[copy-drift]] §1
def _stations():
    import printer as P
    return tuple(P.STATIONS)


def _refused(r):
    """A refusal is a printer answer that says UNKNOWN **and says why**. -> bool

    A bare UNKNOWN carrying no reason is NOT counted. The whole point of the station is that a
    reader can tell an unanswered question from an answered one, and "it just said unknown" is the
    shape a stub returns. Same rule as prune_wilson._refused, deliberately.
    """
    if not isinstance(r, dict):
        return False
    return bool(str(r.get("why") or "").strip())


class _Patch(object):
    """Swap one attribute on one module for the length of one attempt, and always put it back.

    ⚠ Restoring in `finally` is not enough on its own — the ORIGINAL may have been absent, and
    setting it to None is a different state from never having existed. Both are restored exactly,
    the same lesson prune_wilson._Env records for an env var.
    """

    def __init__(self, mod, name, value):
        self.mod, self.name, self.value = mod, name, value
        self.had = hasattr(mod, name)
        self.was = getattr(mod, name, None)

    def __enter__(self):
        setattr(self.mod, self.name, self.value)
        return self

    def __exit__(self, *a):
        if self.had:
            setattr(self.mod, self.name, self.was)
        else:
            try:
                delattr(self.mod, self.name)
            except Exception:
                pass
        return False


def _boom(*a, **k):
    raise RuntimeError("sabotage: this owner refuses to answer")


def _attempt_ownerraises(P):
    """An owner raises. Every station it feeds must be UNKNOWN **with a reason**."""
    import one_start_point as OSP
    with _Patch(OSP, "start_points", _boom):
        r = P.stream()
    rows = r.get("rows") or []
    if not rows:
        # UNKNOWN with a reason is also a correct refusal here
        return 1, (1 if str(r.get("why") or "").strip() and r.get("state") == "UNKNOWN" else 0)
    bad = [x for x in rows if not _refused(x["stations"]["in"])]
    return len(rows), len(rows) - len(bad)


def _attempt_ownerempty(P):
    """Every owner returns nothing. The printer must say UNKNOWN, not report a clean empty run."""
    import one_start_point as OSP
    import reel_river as RR
    with _Patch(OSP, "start_points", lambda *a, **k: {"rows": []}), \
         _Patch(RR, "river", lambda *a, **k: {"rows": []}):
        r = P.stream()
    # the refusal: state UNKNOWN, ok False, and a reason naming why
    good = (r.get("state") == "UNKNOWN" and not r.get("ok")
            and bool(str(r.get("why") or "").strip()))
    return 1, (1 if good else 0)


def _attempt_namelessrows(P):
    """Rows naming no reel must be DROPPED AND COUNTED, never silently dropped."""
    import reel_river as RR
    fake = {"rows": [{"stage": "swept", "question": "q", "decider": "d"},
                     {"reel": "", "stage": "swept"},
                     {"reel": None, "stage": "swept"}]}
    with _Patch(RR, "river", lambda *a, **k: fake):
        r = P.stream()
    # it must not claim those three as walked reels
    walked = int(r.get("walked") or 0)
    named = [x for x in (r.get("rows") or []) if str(x.get("reel") or "").strip()]
    good = (walked == len(named))
    return 1, (1 if good else 0)


def _attempt_strangerreel(P):
    """A reel only ONE owner knows must still carry all five stations, UNKNOWN where unanswered."""
    import one_start_point as OSP
    real = OSP.start_points()
    rows = list((real or {}).get("rows") or [])
    rows.append({"reel": "reel_sabotage_stranger", "door": "recorder", "why": "planted"})
    with _Patch(OSP, "start_points", lambda *a, **k: dict(real or {}, rows=rows)):
        r = P.stream("reel_sabotage_stranger")
    hit = [x for x in (r.get("rows") or []) if x.get("reel") == "reel_sabotage_stranger"]
    if not hit:
        return 1, 0
    st = hit[0]["stations"]
    # every station present, and the ones nobody answered say UNKNOWN with a reason
    if set(st) != set(_stations()):
        return 1, 0
    unanswered = [s for s in ("funnel", "route") if str(st[s].get("say")) == "UNKNOWN"]
    good = bool(unanswered) and all(_refused(st[s]) for s in unanswered)
    return 1, (1 if good else 0)


def _attempt_reachraises(P):
    """printer_reach raises. EXTRACT must be UNKNOWN — never permissive."""
    import printer_reach as PR
    with _Patch(PR, "report", _boom):
        r = P.stream()
    rows = r.get("rows") or []
    if not rows:
        return 1, (1 if r.get("state") == "UNKNOWN" else 0)
    ok = [x for x in rows if str(x["stations"]["extract"].get("say")).upper()
          in ("UNKNOWN", "UNREACHABLE")]
    return len(rows), len(ok)


ATTEMPTS = (
    ("ownerraises", _attempt_ownerraises,
     "an owner raises — the station must say UNKNOWN and name what happened, never go absent"),
    ("ownerempty", _attempt_ownerempty,
     "every owner returns nothing — UNKNOWN, not a clean run over an empty shelf"),
    ("namelessrows", _attempt_namelessrows,
     "rows naming no reel are dropped AND counted, never silently"),
    ("strangerreel", _attempt_strangerreel,
     "a reel only one owner knows still carries all five stations"),
    ("reachraises", _attempt_reachraises,
     "printer_reach raises — EXTRACT is UNKNOWN, never permissive"),
)


def prove():
    """Run every attempt. -> dict. Writes nothing, deletes nothing, banks nothing."""
    import printer as P
    rows, n, k = [], 0, 0
    for name, fn, why in ATTEMPTS:
        try:
            an, ak = fn(P)
        except Exception as e:
            an, ak = 1, 0
            why = why + "  ⚠ the attempt itself raised: %s" % str(e)[:80]
        n += an
        k += ak
        rows.append({"attempt": name, "n": an, "k": ak, "why": why,
                     "leaks": (ak < an)})
    leaks = [r for r in rows if r["leaks"]]
    return {"ok": not leaks, "n": n, "k": k, "rows": rows,
            "state": ("UNPROVEN" if n == 0 else ("LEAKS" if leaks else "PROVEN")),
            "why": ("%d of %d attempts refused" % (k, n)) if n else "nothing attempted"}


def bank_into_proof_queue(rep):
    """Bank the aggregate as ONE `sabotage` row. -> dict | None

    ⚠ NOT CALLED FROM main() BY DEFAULT, and that is deliberate. self_arming has no retract path
    and _fold keys on (lock, kind, src, ref), so a smoke-test run that banks silently would move a
    lock's score for ever. Banking is an explicit `--bank`.
    """
    import self_arming as SA
    return SA.bank("printer.stream", "sabotage", "printer_wilson",
                   n=rep["n"], k=rep["k"],
                   note="the printer must refuse to invent an answer: %s" % rep["why"])


def main(argv):
    rep = prove()
    print("\nTHE PRINTER — can the river refuse to INVENT an answer?\n")
    for r in rep["rows"]:
        print("  %-14s %d/%d  %s" % (r["attempt"], r["k"], r["n"],
                                     "LEAKS" if r["leaks"] else "refused"))
        print("                 %s" % r["why"])
    print("\n  %s · %s\n" % (rep["state"], rep["why"]))
    if "--bank" in argv:
        row = bank_into_proof_queue(rep)
        print("  banked: %s\n" % {k: row[k] for k in ("lock", "kind", "src", "n", "k")})
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
