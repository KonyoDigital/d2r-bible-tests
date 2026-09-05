#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A7·ROUTE — can the router REFUSE to let the keep-reason decide the read-fate?

⚠⚠ WHAT THIS ATTACKS, AND WHY IT IS A LOCK RATHER THAN A TEST. `reel_story._stage_of(tag)` derives
a reel's STAGE from its RETENTION TAG, and `printer.stream()`'s route field is literally the tag
glued to the verdict (`"test-fixture@releasable"`). Measured on his shelf 2026-09-05: all 40 reels
sat at TWO of six stages, four permanently empty, and 29 had never been read at all — because
`vault-owes` is the LAST first-match-wins rule and matched **0 of 40**.

That is one question doing two jobs. *Do we keep these bytes* and *where is this reel in the river*
are different questions, and while they share a value the keep-reason silently decides whether a
reel is ever read. `reel_router` splits them; this proves it stays split, because the coupling is
the kind that returns quietly during a later edit and reads as a tidy simplification.

⚠⚠ EVERY ATTEMPT IS A REFUSAL THIS MODULE MUST MAKE. Nothing here reads his shelf, starts a sweep,
spends a token or deletes a byte: each case builds a synthetic decider or evidence dict and asks
whether the router's own guard catches it. **The prune stays OFF and no paid read is armed.**

⚠ ONE ROW IS ONE ATTACK; `n` is how many times it was applied (REG-598). Banking `n` as `attacks`
would be repetition wearing confluence's clothes — the 83/83 that was really two attacks over 40
reels. [[build-the-heart-and-census-everywhere]]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def _caught(fn, forbidden):
    """Does the AST walk see the coupling in `fn`? -> bool"""
    import reel_router as RR
    try:
        seen = RR._string_keys_read_by(fn)
    except Exception:
        return False
    return bool(set(forbidden) & seen)


def _attempt_decider_reads_the_tag(n=8):
    """THE ORIGINAL DEFECT: the station decided by the keep-reason."""
    import reel_router as RR
    caught = 0
    for i in range(n):
        def _coupled(ev, _i=i):
            if ev.get("tag") == "zero-pages":
                return "STATION", "retention says so"
            return "JOIN", ""
        if _caught(_coupled, RR.RETENTION_FIELDS):
            caught += 1
    return n, caught


def _attempt_evidence_smuggles_the_tag(n=8):
    """The decider stays spotless and the dict it is handed carries the keep-reason. Same
    coupling, one function upstream — the hole a guard aimed only at the decider leaves open."""
    caught = 0
    for i in range(n):
        def _smuggler(hist=None, _i=i):
            row = {}
            return {"r": {"sealed": row.get("funnel"), "names": row.get("route")}}, ""
        if _caught(_smuggler, ("funnel", "route", "tag", "held", "holdKind")):
            caught += 1
    return n, caught


def _attempt_a_blind_walk_passes(n=8):
    """⚠ A guard that inspects nothing reports clean forever, which is indistinguishable from a
    guard that works. Seeing ZERO field reads must be an instrument failure, never a pass.

    ⚠⚠ THIS AXIS USED TO PROVE NOTHING — REG-600, corrected in v2647. It called
    `_string_keys_read_by` on a decider that reads no fields and counted `== set()` as a catch.
    That is an OBSERVATION being graded, not a refusal: it recorded that a helper correctly saw an
    empty set, and never once asked `assert_independent_of_retention` whether it would REFUSE that
    reading. The comment beside it even said *"the caller must refuse it"* — and the caller was
    never called.

    It now BLINDS THE REAL WALKER and requires the real assertion to fail, naming the instrument.
    """
    import reel_router as RR
    caught = 0
    _real = RR._string_keys_read_by
    try:
        for i in range(n):
            # blind the walker itself, so the assertion is looking through a dead instrument
            RR._string_keys_read_by = lambda fn, _i=i: set()
            try:
                ok, findings = RR.assert_independent_of_retention()
            except Exception:
                continue
            # a refusal, and it must name the instrument rather than report a clean tree
            if (not ok) and any("instrument failure" in str(f) for f in findings):
                caught += 1
    finally:
        RR._string_keys_read_by = _real
    return n, caught


def _attempt_a_clockless_reel_jumps_the_queue(n=8):
    """0 is 1970. Coercing an unreadable clock to zero puts an unmeasured reel at the HEAD of a
    FIFO queue, ahead of every reel whose age is actually known."""
    import tempfile
    import reel_router as RR
    caught = 0
    d = tempfile.mkdtemp(prefix="rrw_")
    os.makedirs(os.path.join(d, "reel_nameless"), exist_ok=True)
    for _ in range(n):
        ms, src = RR._captured_ms("reel_nameless", d)
        if ms is None and src is None:
            caught += 1
    return n, caught


def _attempt_unknown_is_folded_into_a_total(n=8):
    """A total that already contains the unmeasured reels lets a caller print one number and never
    say how many it could not place. [[unknown-stays-unknown]]

    ⚠⚠ THIS AXIS USED TO PROVE NOTHING EITHER — REG-600, corrected in v2647. It read
    `if RR.UNKNOWN not in RR.STATIONS: caught += 1`, which compares two MODULE CONSTANTS and can
    never vary: eight identical evaluations of one static fact, banked as eight refusals. Wilson
    counted them and had no way to know.

    It now feeds `route()` a shelf where HALF the reels are unmeasurable and requires the real
    report to keep them OUT of `counts` — the total must not reconcile until UNKNOWN is added back,
    which is what forces a caller to say how many it could not place.
    """
    import reel_router as RR
    caught = 0
    _real = RR._evidence
    try:
        for i in range(n):
            placed = {"reel_s_%d_a" % i: {"sealed": True, "names": 3, "surveyed": True,
                                          "worthReading": True},
                      "reel_s_%d_b" % i: {"sealed": False, "names": 0, "surveyed": True,
                                          "worthReading": False}}
            # ⚠ `sealed=None` is the real UNKNOWN shape — a printer that did not answer. NOT a
            # made-up station string, which would test my fixture instead of the router.
            blind = {"reel_s_%d_c" % i: {"sealed": None, "names": None, "surveyed": True},
                     "reel_s_%d_d" % i: None}
            merged = dict(placed)
            merged.update(blind)
            RR._evidence = lambda h=None, _m=merged: (_m, "")
            try:
                rep = RR.route()
            except Exception:
                continue
            if not rep.get("ok"):
                continue
            counts_total = sum((rep.get("counts") or {}).values())
            # THE REFUSAL: the placed total excludes the unmeasured, the unmeasured are counted
            # and named, and the shelf only reconciles once they are added back.
            if (rep.get("unknown") == 2
                    and counts_total == 2
                    and counts_total != rep.get("shelf")
                    and rep.get("reconciles") is True):
                caught += 1
    finally:
        RR._evidence = _real
    return n, caught


def _attempt_an_empty_reel_enters_the_paid_queue(n=8):
    """★ HIS QUESTION, 2026-09-05. A reel `retro_triage` walked IN FULL and found zero panel
    frames in has nothing an item name could be read from. Routing it to READ buys nothing, and
    a survey verdict flattened into a flag beside the station is how six of thirteen got there."""
    import reel_router as RR
    caught = 0
    for _ in range(n):
        st, _w = RR._station_of({"sealed": False, "names": 0, "worthReading": False,
                                 "surveyed": True})
        if st == "EMPTY":
            caught += 1
    return n, caught


def _attempt_unsurveyed_is_treated_as_empty(n=8):
    """`worth_reading` returns None for an unsurveyed reel and never False, precisely so footage
    nobody looked at cannot be skipped as if it had been looked at and found empty."""
    import reel_router as RR
    caught = 0
    for _ in range(n):
        st, _w = RR._station_of({"sealed": False, "names": 0, "worthReading": None,
                                 "surveyed": True})
        if st == "TRIAGE":
            caught += 1
    return n, caught


CLAIMS = (
    ("coupling", _attempt_decider_reads_the_tag,
     "the station decided by the retention tag — the keep-reason reaching the read-fate"),
    ("smuggle", _attempt_evidence_smuggles_the_tag,
     "the evidence builder copies the keep-reason in, leaving the decider spotless"),
    ("blind", _attempt_a_blind_walk_passes,
     "a walk that inspects nothing must read as an instrument failure, never as clean"),
    ("clock", _attempt_a_clockless_reel_jumps_the_queue,
     "an unreadable capture clock coerced to 0 would head the FIFO queue from 1970"),
    ("unknown", _attempt_unknown_is_folded_into_a_total,
     "UNKNOWN folded into the station totals would hide how many reels could not be placed"),
    ("empty", _attempt_an_empty_reel_enters_the_paid_queue,
     "a reel surveyed in full with zero panel frames must not enter the paid READ queue"),
    ("unsurveyed", _attempt_unsurveyed_is_treated_as_empty,
     "never surveyed must stay distinct from surveyed-and-empty, or footage gets abandoned"),
)


def prove():
    rows, n, k = [], 0, 0
    for claim, fn, what in CLAIMS:
        try:
            an, ak = fn()
        except Exception as e:
            an, ak = 1, 0
            what = "%s — the attempt itself raised (%s)" % (what, str(e)[:60])
        rows.append({"claim": claim, "n": an, "k": ak, "what": what, "leaks": ak < an})
        n += an
        k += ak
    return {"rows": rows, "n": n, "k": k,
            "why": ("%d of %d attempts refused" % (k, n)) if n else "nothing attempted"}


def bank_into_proof_queue(rep):
    import self_arming as SA
    banked = []
    for r in rep["rows"]:
        try:
            # ⚠ ONE ROW = ONE ATTACK; `n` is how many times it was applied. REG-598.
            SA.bank("reel.route", "sabotage", "reel_router_wilson",
                    n=r["n"], k=r["k"], attacks=1,
                    ref=str(r["claim"]), note=str(r["what"])[:200])
            banked.append("%s %d/%d" % (r["claim"], r["k"], r["n"]))
        except ValueError as e:
            banked.append("%s REFUSED (%s)" % (r["claim"], str(e)[:70]))
    return banked


def main(argv):
    rep = prove()
    print("\nA7·ROUTE — can the router refuse to let the keep-reason decide the read-fate?\n")
    for r in rep["rows"]:
        print("  %-12s %d/%d  %s" % (r["claim"], r["k"], r["n"],
                                     "LEAKS" if r["leaks"] else "refused"))
        print("               %s" % r["what"])
    print("\n  %s · %s\n" % ("LEAKS" if rep["k"] < rep["n"] else "PROVEN", rep["why"]))
    if "--bank" in argv:
        for line in bank_into_proof_queue(rep):
            print("  banked: %s" % line)
    return 0 if rep["k"] == rep["n"] else 1


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
