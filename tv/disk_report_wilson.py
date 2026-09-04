#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""154 — CAN THE DISK ROW REFUSE TO CLAIM SPACE IT DID NOT FREE?

⚠⚠ WHY THIS EXISTS, AND WHY IT IS THE REPORTER AND NOT THE PRUNER. Task 154's original framing was
that `prunedMb: 0` across 7,009 rows meant the prune had never freed a byte. **That framing was
RETRACTED**: `pruned_mb=0` was HARDCODED at the only call site, so the zero was a fact about the
CALLER, not about the disk. The real defect was that the field could never report anything at all.

Half of that is fixed — the call site passes `None` now, and his live store shows the cut-over
exactly: **8,270 rows carrying `0` and 280 carrying `None`**. The remainder is that nothing has
ever passed a real number, and 154 sits blocked behind 155, which is HIS MONEY.

His instruction, 2026-09-04: *"fix it to the hardening and wilsons and to the heart so it proves
itself before its unlocked."* So the claim gets a lock and has to earn it.

⚠⚠ THIS HARNESS NEVER PRUNES, AND CANNOT. Every attempt is a state in which the disk row MUST
REFUSE to name a freed figure, and the only thing counted is whether it refused. `prune_once` is
never called, `TV_AUTO_PRUNE` is never touched, and no file is ever deleted. **The prune stays
OFF.** A harness for a reporter that could itself free space would be measuring its own footprint.

⚠ WHAT "REFUSE" MEANS HERE: the row carries `prunedMb: None`. `0` is a measurement — "we freed
nothing" — and `None` is "nobody measured". A reporter that answers 0 when it did not look is the
exact fabrication this lock exists to refuse. [[unknown-stays-unknown]]
"""
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def _row(**kw):
    """Append one disk-history row to a THROWAWAY path and read it back. -> dict | None

    ⚠ NEVER his `disk_history.jsonl`. A harness that writes into the store it grades would put
    its own fixtures into the series he makes storage decisions from.
    [[feedback-fixtures-never-touch-live-data]]
    """
    import control_app as ca
    d = tempfile.mkdtemp(prefix="diskrep_")
    p = os.path.join(d, "h.jsonl")
    try:
        ca.disk_history_append(path=p, **kw)
        with io.open(p, encoding="utf-8") as fh:
            lines = [l for l in fh.read().splitlines() if l.strip()]
        return json.loads(lines[-1]) if lines else None
    except Exception:
        return None


def _refused(row):
    """Did the row decline to name a freed figure? -> bool

    `prunedMb` absent or None is a refusal. Any number — including 0 — is a claim.
    """
    if not isinstance(row, dict):
        return False
    return row.get("prunedMb") is None


def _attempt_no_prune_ran(n=8):
    """Nothing pruned. The row must not say 0 — that is a measurement nobody took."""
    caught = 0
    for i in range(n):
        r = _row(free_gb=40.0 + i, floor_gb=8, hist_bytes=1234, reels=40,
                 eligible_mb=0.0, pruned_mb=None)
        if _refused(r):
            caught += 1
    return n, caught


def _attempt_unreadable_hist(n=8):
    """The corpus size could not be read. A freed figure derived from it cannot exist."""
    caught = 0
    for i in range(n):
        r = _row(free_gb=40.0, floor_gb=8, hist_bytes=None, reels=None,
                 eligible_mb=None, pruned_mb=None)
        if _refused(r):
            caught += 1
    return n, caught


def _attempt_disk_shrank(n=8):
    """Free space went DOWN between samples. Whatever happened, we did not free anything, and a
    reporter that turns a negative delta into a positive claim is the fabrication in reverse."""
    caught = 0
    for i in range(n):
        r = _row(free_gb=10.0, floor_gb=8, hist_bytes=9_000_000_000, reels=40,
                 eligible_mb=0.0, pruned_mb=None)
        if _refused(r):
            caught += 1
    return n, caught


CLAIMS = (
    ("noprune", _attempt_no_prune_ran,
     "nothing pruned — the row must not answer 0, which is a measurement nobody took"),
    ("unreadable", _attempt_unreadable_hist,
     "the corpus size could not be read, so a freed figure derived from it cannot exist"),
    ("shrank", _attempt_disk_shrank,
     "free space fell between samples — a negative delta must never become a positive claim"),
)


def prove():
    rows, n, k = [], 0, 0
    for claim, fn, what in CLAIMS:
        try:
            an, ak = fn()
        except Exception as e:
            an, ak = 1, 0
            what = "%s — the attempt itself raised (%s)" % (what, str(e)[:60])
        rows.append({"claim": claim, "n": an, "k": ak, "what": what,
                     "leaks": ak < an})
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
            SA.bank("prune.reports", "sabotage", "disk_report_wilson",
                    n=r["n"], k=r["k"], attacks=1,
                    ref=str(r["claim"]), note=str(r["what"])[:200])
            banked.append("%s %d/%d" % (r["claim"], r["k"], r["n"]))
        except ValueError as e:
            banked.append("%s REFUSED (%s)" % (r["claim"], str(e)[:70]))
    return banked


def main(argv):
    rep = prove()
    print("\n154 — CAN THE DISK ROW REFUSE TO CLAIM SPACE IT DID NOT FREE?\n")
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
