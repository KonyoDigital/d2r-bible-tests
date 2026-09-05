#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""THE SECOND KIND FOR `prune.reports` — attacks a different model family designed, COLD.

⚠⚠ WHY A SECOND FAMILY AND NOT MORE OF MY OWN ATTACKS. Wilson counts how many looks agreed and has
no way to know whether they were the same look repeated (REG-598). `confluence` is the term that
does, and it only moves on genuinely independent KINDS. My four sabotage axes and a fifth of mine
would be one instrument in a new hat. So `credible_pruned_mb` was handed to a non-Anthropic model
with its body, its caller, and the contract in the author's words — and **nothing about what I
thought was strong or weak in it.** Same play that took `vault.apply` to HARDENED in v2641.

**IT LANDED THREE OF FIVE, AND ALL THREE WERE MINE.**

  1. **NEGATIVE ZERO**, which it ranked first. `-0.0 < 0` is **False** in Python, so the negative
     check let it straight through and the row published `prunedMb: -0.0`. It is numerically zero
     and must be KEPT — measured-and-zero is a real answer — but a freed figure must never reach
     his dashboard wearing a minus sign.
  2. **0.9 MB against a 0-BYTE corpus.** My tolerance was a flat `+ 1.0 MB`, so an empty corpus
     licensed almost a megabyte of claimed pruning.
  3. **2.0 MB against a 1 MiB corpus** — exactly double the whole thing, through the same slack.
     An ABSOLUTE tolerance is largest, relatively, precisely where the corpus is smallest: the
     wrong way round. It is proportional now (1%, for byte↔megabyte rounding), and against an
     empty corpus it admits nothing but zero.

**AND ONE IT LANDED THAT IS NOT FIXED, ON PURPOSE.** `credible_pruned_mb(10**30)` with no corpus is
PUBLISHED. With no corpus reading there is nothing here to bound a magnitude against, and every
ceiling I could invent would be a constant of mine rather than a measurement. `free_gb` is not a
sound bound either — the recorder can write footage between the prune and the reading, so
freed > free is legitimately possible, and refusing on it would throw out real measurements. So it
stays UNKNOWN rather than being resolved by a number I made up, and this file ATTEMPTS it and
records the miss rather than quietly dropping the axis. [[unknown-stays-unknown]]

⚠ TWO IT REFUTED ITSELF, banked anyway so a tried-and-failed axis is on the record: a subnormal
`1e-200` ("still a measurement, just a very precise one") and 100 MB against a 200 MiB corpus.
Both measured, both correctly published. A second family earns its place by attacking along axes I
do not — not by being right more often.

⚠⚠ ANTI-REG-600, because this could so easily have become theatre. `_refused()` counts ONLY a row
whose `prunedMb` is None AND whose `prunedWhy` carries the reporter's own sentence — never a bare
None, which is also what a row nobody offered a figure to looks like. And it REFUSES TO BANK AT ALL
unless the baseline holds: legitimate figures must still be RECORDED, or the refusals prove a
jammed door rather than a working one.

⚠ NOTHING IS PRUNED AND NOTHING IS ARMED. Every attempt writes one line to a throwaway temp file.
`TV_AUTO_PRUNE` is never touched, no reel is read, and `may()` is never called.
"""
import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

#: 8.9 GB — the real reel-store size from the day he asked "how come i have 15 gigabytes more
#: today than yesterday? is the pruning working?"
CORPUS = 8_900_000_000


def _row(pruned_mb, hist_bytes=CORPUS):
    """Append one row to a THROWAWAY path and read it back. -> dict | None

    ⚠ NEVER his `disk_history.jsonl`. [[feedback-fixtures-never-touch-live-data]]
    """
    import control_app as ca
    d = tempfile.mkdtemp(prefix="diskxf_")
    try:
        p = os.path.join(d, "h.jsonl")
        ca.disk_history_append(free_gb=40.0, floor_gb=8, hist_bytes=hist_bytes, reels=40,
                               eligible_mb=0.0, pruned_mb=pruned_mb, path=p)
        with io.open(p, encoding="utf-8") as fh:
            lines = [l for l in fh.read().splitlines() if l.strip()]
        return json.loads(lines[-1]) if lines else None
    except Exception:
        return None
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _refused(row):
    """Did the row THROW OUT the figure, and SAY SO? -> bool

    ⚠ A bare `None` is not enough. It is also what a row nobody offered a figure to looks like,
    which is exactly how `prune.reports` came to bank 24 identity assertions (REG-600).
    """
    return (isinstance(row, dict) and row.get("prunedMb") is None
            and bool(row.get("prunedWhy")))


def _published_without_a_minus(row):
    """Kept, and not wearing a minus sign. -> bool"""
    if not isinstance(row, dict):
        return False
    v = row.get("prunedMb")
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return False
    # ⚠ `v == 0` is True for -0.0, so equality cannot answer this. The SIGN BIT can.
    import math
    return not math.copysign(1.0, float(v)) < 0


def _attempt_negative_zero(n=8):
    """★ ITS STRONGEST. `-0.0 < 0` is False, so the negative check never saw it."""
    caught = 0
    for _ in range(n):
        if _published_without_a_minus(_row(-0.0)):
            caught += 1
    return n, caught


def _attempt_a_claim_against_an_EMPTY_corpus(n=8):
    """0.9 MB freed from a 0-byte store. My flat `+1.0 MB` tolerance licensed it."""
    caught = 0
    for i in range(n):
        if _refused(_row(0.9 - (i * 0.05), hist_bytes=0)):
            caught += 1
    return n, caught


def _attempt_double_a_tiny_corpus(n=8):
    """2.0 MB against a 1 MiB store — the same slack, and it is largest relatively exactly where
    the corpus is smallest."""
    caught = 0
    for i in range(n):
        if _refused(_row(2.0 + i, hist_bytes=1024 * 1024)):
            caught += 1
    return n, caught


def _attempt_an_unbounded_magnitude_with_NO_corpus(n=8):
    """⚠⚠ THIS AXIS IS EXPECTED TO MISS, AND IT IS RUN ANYWAY.

    `credible_pruned_mb(10**30)` with `hist_bytes=None` is PUBLISHED. There is nothing inside the
    function to bound a magnitude against when the corpus could not be read, and every ceiling I
    could add would be a constant of mine, not a measurement. Dropping the axis would hide the
    gap; running it records the miss and drags the score down honestly. [[unknown-stays-unknown]]
    """
    caught = 0
    for i in range(n):
        if _refused(_row(float(10 ** (25 + (i % 5))), hist_bytes=None)):
            caught += 1
    return n, caught


def _attempt_a_SUBNORMAL_figure(n=8):
    """⚠ REFUTED BY THE FAMILY THAT PROPOSED IT — *"still a measurement, just a very precise
    one"* — and banked anyway so a tried-and-failed axis is on the record rather than quietly
    dropped. The refusal here is the OPPOSITE direction: it must be KEPT."""
    caught = 0
    for _ in range(n):
        r = _row(1e-200)
        if isinstance(r, dict) and r.get("prunedMb") == 1e-200 and not r.get("prunedWhy"):
            caught += 1
    return n, caught


CLAIMS = (
    ("negzero", _attempt_negative_zero,
     "-0.0 slipped past the negative check and published a freed figure wearing a minus sign"),
    ("emptycorpus", _attempt_a_claim_against_an_EMPTY_corpus,
     "0.9 MB claimed as freed from a 0-byte corpus, through a flat +1 MB tolerance"),
    ("tinycorpus", _attempt_double_a_tiny_corpus,
     "2.0 MB claimed against a 1 MiB corpus — double the whole thing, same slack"),
    ("unbounded", _attempt_an_unbounded_magnitude_with_NO_corpus,
     "an absurd magnitude with NO corpus reading is published — a STATED, UNCLOSED limit, run "
     "so the miss is counted rather than hidden"),
    ("subnormal", _attempt_a_SUBNORMAL_figure,
     "a subnormal but real figure must be KEPT — refuted by the family that proposed it, banked "
     "so the tried-and-failed axis is on the record"),
)


#: ⚠⚠ THE AXES THAT ARE EXPECTED TO MISS, AND WHY THAT IS DECLARED RATHER THAN SILENT.
#: `unbounded` cannot be closed from inside `credible_pruned_mb` — with no corpus reading there is
#: nothing to bound a magnitude against, and any ceiling would be a constant of mine rather than a
#: measurement. Dropping the axis would hide the gap; leaving the file permanently red would teach
#: a reader to skip it, which is how a real red goes unnoticed.
#: So the axis RUNS, its miss is BANKED (dragging the Wilson score down honestly), and the gate
#: pins the LAW: the set of missing axes must be exactly this one. A NEW miss goes red immediately.
#: [[regression-guard]] — pin the law, not the number. [[unknown-stays-unknown]]
KNOWN_MISSES = ("unbounded",)


def _baseline_legitimate_figures_are_RECORDED():
    """⚠⚠ THE CONTROL. It cannot raise the score — only withdraw it. -> (ok, why)

    REG-593: a validator hardwired shut scores exactly like a perfect one. `0` most of all must be
    kept, because refusing it would be the same fabrication pointing the other way.
    """
    for v, h in ((0, CORPUS), (0.0, CORPUS), (12.5, CORPUS), (1000.0, CORPUS),
                 (1.0, 1024 * 1024), (100, 200 * 1024 * 1024)):
        r = _row(v, hist_bytes=h)
        if not isinstance(r, dict):
            return False, "the writer returned nothing for a legitimate figure %r" % (v,)
        if r.get("prunedMb") != v or r.get("prunedWhy"):
            return False, ("a LEGITIMATE figure %r against a %r-byte corpus was thrown out "
                           "(prunedMb=%r why=%r) — the refusals above prove a jammed door, not a "
                           "working one" % (v, h, r.get("prunedMb"), r.get("prunedWhy")))
    return True, "0, 0.0, 12.5, 1000.0, 1.0/1MiB and 100/200MiB were all recorded"


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
    base_ok, base_why = _baseline_legitimate_figures_are_RECORDED()
    missing = tuple(sorted(r["claim"] for r in rows if r["leaks"]))
    unexpected = tuple(m for m in missing if m not in KNOWN_MISSES)
    # ⚠ AND THE OTHER DIRECTION, which is the half a "known failures" list usually forgets: an axis
    # that was declared as a known miss and has started REFUSING is also news — it means the gap
    # closed and the declaration is now a stale label. [[label-outlived-referent]]
    closed = tuple(m for m in KNOWN_MISSES if m not in missing)
    return {"rows": rows, "n": n, "k": k, "baseline": bool(base_ok), "baselineWhy": base_why,
            "missing": list(missing), "unexpected": list(unexpected), "closedGaps": list(closed),
            "state": ("WITHDRAWN" if not base_ok
                      else "LEAKS" if unexpected
                      else "STALE-DECLARATION" if closed
                      else "PROVEN" if n else "LEAKS"),
            "why": ("%d of %d attempts refused; missing %s (declared %s)"
                    % (k, n, list(missing) or "none", list(KNOWN_MISSES)))
                   if n else "nothing attempted"}


def bank_into_proof_queue(rep):
    """⚠ Banks under `cross-family`, which is the whole point — a SECOND KIND, not more of the
    same. And nothing banks while the baseline is down (REG-593: gating only the printed verdict
    left the STORED one untouched, so a run the harness had disowned still fed the lock)."""
    import self_arming as SA
    if not rep.get("baseline"):
        return ["REFUSED TO BANK ANYTHING — baseline down: %s" % (rep.get("baselineWhy"),)]
    banked = []
    for r in rep["rows"]:
        try:
            SA.bank("prune.reports", "cross-family", "disk_report_crossfamily",
                    n=r["n"], k=r["k"], attacks=1,
                    ref=str(r["claim"]), note=str(r["what"])[:200])
            banked.append("%s %d/%d" % (r["claim"], r["k"], r["n"]))
        except ValueError as e:
            banked.append("%s REFUSED (%s)" % (r["claim"], str(e)[:70]))
    return banked


def main(argv):
    rep = prove()
    print("\nprune.reports — ATTACKS DESIGNED COLD BY A DIFFERENT MODEL FAMILY\n")
    for r in rep["rows"]:
        print("  %-13s %d/%d  %s" % (r["claim"], r["k"], r["n"],
                                     "MISSES" if r["leaks"] else "refused"))
        print("                %s" % r["what"])
    print("\n  BASELINE %s — %s" % ("held" if rep["baseline"] else "DOWN", rep["baselineWhy"]))
    if rep["unexpected"]:
        print("  ⚠ AXES MISSING THAT WERE NOT DECLARED: %s" % rep["unexpected"])
    if rep["closedGaps"]:
        print("  ⚠ DECLARED AS A KNOWN MISS AND NOW REFUSING — the declaration is stale: %s"
              % rep["closedGaps"])
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
