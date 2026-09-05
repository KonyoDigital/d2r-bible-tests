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

⚠ WHAT "REFUSE" MEANS HERE: the row carries `prunedMb: None` AND a `prunedWhy` sentence naming
what was rejected. `0` is a measurement — "we freed nothing" — `None` with no reason is "nobody
measured", and `None` WITH a reason is a claim we threw out. Three states, and the third is the one
this lock is about. [[unknown-stays-unknown]]

⚠⚠⚠ THIS FILE USED TO PROVE NOTHING, AND THE CORRECTION IS THE WHOLE POINT OF v2647.

USED TO READ: three attacks, each handing `disk_history_append(pruned_mb=None)` and asserting the
row came back `None`. **24 of 24 "refusals" were IDENTITY ASSERTIONS.** `disk_history_append` was a
pure passthrough — `"prunedMb": pruned_mb`, no validation of any kind — so every attempt handed the
writer a legal value and recorded its correct behaviour as a guard refusing. That is REG-600 exactly,
and it bought `prune.reports` a Wilson score over an event that could not fail.

Proven the way REG-593 proved `prune.arm`: replace the validator with a stub that ACCEPTS
EVERYTHING and re-run. Under the old attacks the file scored 24/24 either way — identical, which is
the signature of an inert instrument. Under the attacks below the stub scores 0/24.

THE ATTACKS NOW HAND IT FIGURES A REPORTER MUST THROW OUT: `True` (which is not one megabyte), NaN
and infinity, a negative, a string, and — his own v2229 question — a figure larger than the entire
measured corpus. Every one of them used to be written to his durable series verbatim.

⚠⚠ AND THERE IS A BASELINE, because a validator that refuses everything is not a validator.
`_baseline_legitimate_figures_are_RECORDED` hands it 0, 12.5 and a figure inside the corpus and
requires all three to be KEPT. It adds nothing to `n`/`k` and cannot raise the score — it can only
withdraw it: if the baseline fails, nothing banks and no claim reads PROVEN.
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
    """Did the row THROW OUT a figure it was handed? -> bool

    ⚠⚠ A BARE `None` IS NO LONGER ENOUGH, and that change is the fix. `prunedMb is None` is also
    what a row looks like when NOBODY EVER OFFERED A FIGURE — which is how 24 identity assertions
    passed for 24 refusals. A refusal must carry the reporter's OWN SENTENCE saying what it threw
    out. [[unknown-stays-unknown]]
    """
    if not isinstance(row, dict):
        return False
    return row.get("prunedMb") is None and bool(row.get("prunedWhy"))


def _attempt_not_a_number(n=8):
    """`True` is not one megabyte, and a string is not a measurement.

    ⚠ NOT HYPOTHETICAL. `control_app.disk_delta` carries the scar: *"a history whose two in-window
    rows carried `prunedMb: true` produced `prunedMbInWindow = 2` and the sentence '2 MB of that
    was our pruning'."* That was screened at READ time; the `true` still went to disk.
    """
    bad = [True, False, "12", "", [], {}, (), object()]
    caught = 0
    for i in range(n):
        r = _row(free_gb=40.0, floor_gb=8, hist_bytes=9_000_000_000, reels=40,
                 eligible_mb=0.0, pruned_mb=bad[i % len(bad)])
        if _refused(r):
            caught += 1
    return n, caught


def _attempt_not_finite(n=8):
    """NaN and infinity are arithmetic that already lost its meaning."""
    nan, inf = float("nan"), float("inf")
    bad = [nan, inf, -inf, nan, inf, -inf, nan, inf]
    caught = 0
    for i in range(n):
        r = _row(free_gb=40.0, floor_gb=8, hist_bytes=9_000_000_000, reels=40,
                 eligible_mb=0.0, pruned_mb=bad[i % len(bad)])
        if _refused(r):
            caught += 1
    return n, caught


def _attempt_negative(n=8):
    """Pruning does not consume space. A negative freed figure is a sign error reaching a screen."""
    caught = 0
    for i in range(n):
        r = _row(free_gb=40.0, floor_gb=8, hist_bytes=9_000_000_000, reels=40,
                 eligible_mb=0.0, pruned_mb=-(1.0 + i))
        if _refused(r):
            caught += 1
    return n, caught


def _attempt_more_than_the_corpus(n=8):
    """★★ HIS OWN QUESTION, v2229: *"how come i have 15 gigabytes more today than yesterday? is the
    pruning working?"* — against a reel store measuring 8.9 GB. A figure larger than the thing it
    was freed from is impossible whatever the disk says, and nothing anywhere checked it."""
    corpus = 8_900_000_000                      # 8.9 GB, the real number from that day
    caught = 0
    for i in range(n):
        r = _row(free_gb=40.0, floor_gb=8, hist_bytes=corpus, reels=40, eligible_mb=0.0,
                 pruned_mb=15_000.0 + i)        # 15 GB in MB
        if _refused(r):
            caught += 1
    return n, caught


def _baseline_legitimate_figures_are_RECORDED():
    """⚠⚠ THE CONTROL, AND IT CAN ONLY WITHDRAW THE CLAIM. -> (ok, why)

    REG-593's lesson, applied before it could bite twice: a guard hardwired to say NO scores exactly
    like a perfect one, and those are indistinguishable until something shows the instrument can
    MOVE. Three legitimate figures must be KEPT — `0` most of all, because "we measured and freed
    nothing" is a real answer and refusing it would be the same fabrication pointing the other way.

    It adds nothing to `n` or `k`. It cannot raise the score.
    """
    corpus = 9_000_000_000
    for v in (0, 12.5, 1000.0):
        r = _row(free_gb=40.0, floor_gb=8, hist_bytes=corpus, reels=40,
                 eligible_mb=0.0, pruned_mb=v)
        if not isinstance(r, dict):
            return False, "the writer returned nothing for a legitimate figure %r" % (v,)
        if r.get("prunedMb") != v:
            return False, ("a LEGITIMATE figure %r was thrown out (prunedMb=%r, why=%r) — the "
                           "refusals above prove a jammed door, not a working one"
                           % (v, r.get("prunedMb"), r.get("prunedWhy")))
        if r.get("prunedWhy"):
            return False, "a legitimate figure %r was recorded WITH a refusal sentence" % (v,)
    return True, "0, 12.5 and 1000.0 MB against a 9 GB corpus were all recorded"


CLAIMS = (
    ("notanumber", _attempt_not_a_number,
     "a bool or a string was offered as megabytes — `True` is not one megabyte"),
    ("notfinite", _attempt_not_finite,
     "NaN or infinity was offered — arithmetic that already lost its meaning"),
    ("negative", _attempt_negative,
     "a negative freed figure was offered — pruning does not consume space"),
    ("overcorpus", _attempt_more_than_the_corpus,
     "a figure larger than the whole measured corpus was offered — his own v2229 question, "
     "15 GB claimed against an 8.9 GB reel store"),
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
    base_ok, base_why = _baseline_legitimate_figures_are_RECORDED()
    return {"rows": rows, "n": n, "k": k,
            "baseline": bool(base_ok), "baselineWhy": base_why,
            "state": ("PROVEN" if (base_ok and n and k == n)
                      else "WITHDRAWN" if not base_ok else "LEAKS"),
            "why": ("%d of %d attempts refused" % (k, n)) if n else "nothing attempted"}


def bank_into_proof_queue(rep):
    """⚠⚠ NOTHING BANKS WHILE THE BASELINE IS DOWN, and gating only the PRINTED verdict was the
    exact half-fix REG-593 caught: `bank` reads `n`/`k`, so a run the harness had just disowned
    would still write 24/24 into the lock and it would go on reading OPEN on evidence its own
    harness withdrew. The stored verdict is gated, not the sentence on screen."""
    import self_arming as SA
    if not rep.get("baseline"):
        return ["REFUSED TO BANK ANYTHING — baseline down: %s" % (rep.get("baselineWhy"),)]
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
    print("\n  BASELINE %s — %s" % ("held" if rep["baseline"] else "DOWN", rep["baselineWhy"]))
    print("  %s · %s\n" % (rep["state"], rep["why"]))
    if "--bank" in argv:
        for line in bank_into_proof_queue(rep):
            print("  banked: %s" % line)
    return 0 if rep["state"] == "PROVEN" else 1


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
