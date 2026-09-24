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


def _attempt_just_over_the_slack(n=4):
    """The 15 GB attack still fails if the slack is widened to 2x. This one does not."""
    corpus = 1024 * 1024
    caught = 0
    for i in range(n):
        r = _row(free_gb=40.0, floor_gb=8, hist_bytes=corpus, reels=1, eligible_mb=0.0,
                 pruned_mb=1.02 + i * 0.01)
        if _refused(r) and "corpus" in str(r.get("prunedWhy") or ""):
            caught += 1
    return n, caught


def _attempt_lock_shut(n=2):
    import self_arming as SA
    real = SA.may
    SA.may = lambda lock: (False, "sabotage: the lock is shut")
    try:
        caught = 0
        for _ in range(n):
            r = _row(free_gb=40.0, floor_gb=8, hist_bytes=9_000_000_000, reels=1,
                     eligible_mb=0.0, pruned_mb=12.5)
            if (_refused(r) and "LOCKED" in str(r.get("prunedWhy") or "")
                    and r.get("freeGb") == 40.0):
                caught += 1
        return n, caught
    finally:
        SA.may = real


def _attempt_lock_unreadable(n=2):
    import self_arming as SA
    real = SA.may
    def _boom(lock):
        raise RuntimeError("the lock could not be read")
    SA.may = _boom
    try:
        caught = 0
        for _ in range(n):
            r = _row(free_gb=40.0, floor_gb=8, hist_bytes=9_000_000_000, reels=1,
                     eligible_mb=0.0, pruned_mb=12.5)
            if _refused(r) and r.get("freeGb") == 40.0:
                caught += 1
        return n, caught
    finally:
        SA.may = real


def _attempt_delta_ignores_a_refused_figure(n=2):
    import control_app as ca
    caught = 0
    for _ in range(n):
        d = tempfile.mkdtemp(prefix="diskrep_")
        p = os.path.join(d, "h.jsonl")
        ca.disk_history_append(free_gb=40.0, floor_gb=8, hist_bytes=9_000_000_000,
                               reels=1, eligible_mb=0.0, pruned_mb=True, path=p)
        delta = ca.disk_delta(hours=24, path=p)
        if delta.get("prunedMbInWindow") is None:
            caught += 1
    return n, caught


def _attempt_a_good_row_does_not_inherit_a_refusal(n=2):
    import control_app as ca
    caught = 0
    for _ in range(n):
        d = tempfile.mkdtemp(prefix="diskrep_")
        p = os.path.join(d, "h.jsonl")
        ca.disk_history_append(free_gb=40.0, floor_gb=8, hist_bytes=9_000_000_000,
                               reels=1, eligible_mb=0.0, pruned_mb=True, path=p)
        ca.disk_history_append(free_gb=40.0, floor_gb=8, hist_bytes=9_000_000_000,
                               reels=1, eligible_mb=0.0, pruned_mb=12.5, path=p)
        with io.open(p, encoding="utf-8") as fh:
            rows = [json.loads(l) for l in fh.read().splitlines() if l.strip()]
        if len(rows) >= 2 and rows[-1].get("prunedMb") == 12.5 and not rows[-1].get("prunedWhy"):
            caught += 1
    return n, caught


def _kept(hist_bytes):
    r = _row(free_gb=40.0, floor_gb=8, hist_bytes=hist_bytes, reels=1, eligible_mb=0.0,
             pruned_mb=12.5)
    return isinstance(r, dict) and r.get("prunedMb") == 12.5 and not r.get("prunedWhy")


def _attempt_a_negative_corpus_does_not_veto(n=2):
    return n, sum(1 for _ in range(n) if _kept(-1))


def _attempt_a_bool_corpus_does_not_veto(n=2):
    return n, sum(1 for _ in range(n) if _kept(True))


def _attempt_a_string_corpus_does_not_veto(n=2):
    return n, sum(1 for _ in range(n) if _kept("9000000000"))


def _attempt_a_nan_corpus_does_not_veto(n=2):
    return n, sum(1 for _ in range(n) if _kept(float("nan")))


def _attempt_a_list_corpus_does_not_veto(n=2):
    return n, sum(1 for _ in range(n) if _kept([1024, 1024]))


def _one(**kw):
    base = dict(free_gb=40.0, floor_gb=8, hist_bytes=9_000_000_000, reels=1, eligible_mb=0.0)
    base.update(kw)
    return _row(**base)


def _attempt_nobody_measured(n=2):
    caught = 0
    for _ in range(n):
        r = _one(pruned_mb=None)
        if isinstance(r, dict) and r.get("prunedMb") is None and not r.get("prunedWhy"):
            caught += 1
    return n, caught


def _attempt_measured_zero(n=2):
    caught = 0
    for _ in range(n):
        r = _one(pruned_mb=0)
        if isinstance(r, dict) and r.get("prunedMb") == 0 and isinstance(r.get("prunedMb"), int) and not r.get("prunedWhy"):
            caught += 1
    return n, caught


def _attempt_zero_on_an_empty_corpus(n=2):
    caught = 0
    for _ in range(n):
        r = _one(hist_bytes=0, pruned_mb=0)
        if isinstance(r, dict) and r.get("prunedMb") == 0 and not r.get("prunedWhy"):
            caught += 1
    return n, caught


def _attempt_the_slack_boundary_is_kept(n=2):
    corpus = 1024 * 1024
    caught = 0
    for _ in range(n):
        r = _one(hist_bytes=corpus, pruned_mb=1.01)
        if isinstance(r, dict) and r.get("prunedMb") == 1.01 and not r.get("prunedWhy"):
            caught += 1
    return n, caught


def _attempt_why_does_not_collapse(n=2):
    caught = 0
    for _ in range(n):
        r = _one(hist_bytes=0, pruned_mb=1e-9)
        why = str((r or {}).get("prunedWhy") or "")
        if _refused(r) and "0.0 exceeds" not in why and "1e-09" in why:
            caught += 1
    return n, caught


def _attempt_the_four_refusals_read_differently(n=2):
    caught = 0
    for _ in range(n):
        rows = [
            _one(pruned_mb=True),
            _one(pruned_mb=float("nan")),
            _one(pruned_mb=-1),
            _one(hist_bytes=1024 * 1024, pruned_mb=50),
        ]
        whys = [str((r or {}).get("prunedWhy") or "") for r in rows]
        if all(whys) and len(set(whys)) == 4:
            caught += 1
    return n, caught


def _attempt_delta_sums_only_what_was_kept(n=2):
    import control_app as ca
    import time as _time
    caught = 0
    for _ in range(n):
        d = tempfile.mkdtemp(prefix="diskrep_")
        p = os.path.join(d, "h.jsonl")
        now = int(_time.time() * 1000)
        old = now - 25 * 3600 * 1000
        rows = [
            {"at": old, "freeGb": 40.0, "prunedMb": 1},
            {"at": now, "freeGb": 39.0, "prunedMb": 12.5},
            {"at": now, "freeGb": 39.0, "prunedMb": True},
        ]
        with io.open(p, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        delta = ca.disk_delta(hours=24, path=p)
        if delta.get("prunedMbInWindow") == 12.5:
            caught += 1
    return n, caught


def _attempt_a_refused_prune_does_not_blank_the_free_space_delta(n=2):
    import control_app as ca
    caught = 0
    for _ in range(n):
        d = tempfile.mkdtemp(prefix="diskrep_")
        p = os.path.join(d, "h.jsonl")
        ca.disk_history_append(free_gb=40.0, floor_gb=8, hist_bytes=9_000_000_000,
                               reels=1, eligible_mb=0.0, pruned_mb=True, path=p)
        ca.disk_history_append(free_gb=30.0, floor_gb=8, hist_bytes=9_000_000_000,
                               reels=1, eligible_mb=0.0, pruned_mb=True, path=p)
        # The series does not reach back 24h, so a 24h delta is UNKNOWN. Ask across 0 hours
        # by reading the two freeGb values the rows actually stored.
        with io.open(p, encoding="utf-8") as fh:
            rows = [json.loads(l) for l in fh if l.strip()]
        if [r.get("freeGb") for r in rows] == [40.0, 30.0] and all(r.get("prunedMb") is None for r in rows):
            caught += 1
    return n, caught


def _attempt_an_infinite_corpus_does_not_veto(n=2):
    return n, sum(1 for v in (float("inf"), float("-inf")) if _kept(v))


def _attempt_no_corpus_does_not_invent_a_ceiling(n=2):
    caught = 0
    for _ in range(n):
        r = _one(hist_bytes=None, pruned_mb=5000)
        if isinstance(r, dict) and r.get("prunedMb") == 5000 and not r.get("prunedWhy"):
            caught += 1
    return n, caught


def _attempt_free_space_is_not_a_bound(n=2):
    caught = 0
    for _ in range(n):
        r = _one(free_gb=1.0, pruned_mb=100)
        if isinstance(r, dict) and r.get("prunedMb") == 100 and not r.get("prunedWhy"):
            caught += 1
    return n, caught


def _attempt_eligible_is_not_a_bound(n=2):
    caught = 0
    for _ in range(n):
        r = _one(eligible_mb=-5, pruned_mb=12.5)
        if isinstance(r, dict) and r.get("prunedMb") == 12.5 and not r.get("prunedWhy"):
            caught += 1
    return n, caught


def _attempt_a_tiny_real_figure_is_kept(n=2):
    caught = 0
    for _ in range(n):
        r = _one(pruned_mb=1e-10)
        if isinstance(r, dict) and r.get("prunedMb") == 1e-10 and not r.get("prunedWhy"):
            caught += 1
    return n, caught


def _attempt_a_directory_is_not_a_history(n=2):
    import control_app as ca
    caught = 0
    for _ in range(n):
        d = tempfile.mkdtemp(prefix="diskrep_")
        got = ca.disk_history_append(free_gb=40.0, floor_gb=8, pruned_mb=-5, path=d)
        if got is None and not os.path.isfile(d):
            caught += 1
    return n, caught


def _attempt_a_refusal_still_says_when(n=2):
    caught = 0
    for _ in range(n):
        r = _one(pruned_mb=-3)
        if _refused(r) and isinstance(r.get("at"), int) and r.get("at") > 0:
            caught += 1
    return n, caught


def _attempt_two_refusals_keep_their_own_reasons(n=2):
    import control_app as ca
    caught = 0
    for _ in range(n):
        d = tempfile.mkdtemp(prefix="diskrep_")
        p = os.path.join(d, "h.jsonl")
        ca.disk_history_append(free_gb=40.0, floor_gb=8, hist_bytes=9_000_000_000,
                               reels=1, eligible_mb=0.0, pruned_mb=-2, path=p)
        ca.disk_history_append(free_gb=40.0, floor_gb=8, hist_bytes=1024 * 1024,
                               reels=1, eligible_mb=0.0, pruned_mb=80, path=p)
        with io.open(p, encoding="utf-8") as fh:
            rows = [json.loads(l) for l in fh if l.strip()]
        if (len(rows) == 2 and "negative" in str(rows[0].get("prunedWhy"))
                and "corpus" in str(rows[1].get("prunedWhy"))
                and rows[0].get("prunedWhy") != rows[1].get("prunedWhy")):
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
    ("slack", _attempt_just_over_the_slack,
     "1.02 MB against a 1 MB corpus — pins the 1% slack, which a 15 GB claim does not"),
    ("lockshut", _attempt_lock_shut,
     "a credible figure is refused when prune.reports may() says no, and the free-space reading stays"),
    ("lockblind", _attempt_lock_unreadable,
     "a may() that raises fails closed — the figure is not published as if the lock had agreed"),
    ("deltajoin", _attempt_delta_ignores_a_refused_figure,
     "a refused figure does not come back as megabytes from disk_delta"),
    ("nocarry", _attempt_a_good_row_does_not_inherit_a_refusal,
     "a legitimate figure written after a refused one is recorded clean"),
    ("negcorpus", _attempt_a_negative_corpus_does_not_veto,
     "a negative hist_bytes is not a corpus, so it must not veto a real measurement"),
    ("boolcorpus", _attempt_a_bool_corpus_does_not_veto,
     "True is not one byte of corpus"),
    ("strcorpus", _attempt_a_string_corpus_does_not_veto,
     "a numeric string is not a measured corpus"),
    ("nancorpus", _attempt_a_nan_corpus_does_not_veto,
     "NaN corpus must not veto and must not be treated as a bound"),
    ("listcorpus", _attempt_a_list_corpus_does_not_veto,
     "a list of sizes is not a measured corpus and must not veto a real figure"),
    ("nobody", _attempt_nobody_measured,
     "pruned_mb None is nobody-measured, and must not wear a refusal sentence"),
    ("zero", _attempt_measured_zero,
     "integer 0 is a measurement that freed nothing, kept as an int"),
    ("zeroempty", _attempt_zero_on_an_empty_corpus,
     "freeing nothing from an empty corpus is a real zero, not an over-corpus claim"),
    ("boundary", _attempt_the_slack_boundary_is_kept,
     "a figure exactly at the 1% slack is kept; only past it is refused"),
    ("whycollapse", _attempt_why_does_not_collapse,
     "a tiny figure against a 0-byte corpus must not read as 0.0 exceeds 0.0"),
    ("fourwhys", _attempt_the_four_refusals_read_differently,
     "bool, NaN, negative and over-corpus each name a different reason"),
    ("deltasum", _attempt_delta_sums_only_what_was_kept,
     "disk_delta adds the kept figures and drops the refused ones"),
    ("deltagb", _attempt_a_refused_prune_does_not_blank_the_free_space_delta,
     "refusing the prune figure leaves the free-space readings in the series"),
    ("infcorpus", _attempt_an_infinite_corpus_does_not_veto,
     "an infinite corpus is not a bound, in either direction"),
    ("noceiling", _attempt_no_corpus_does_not_invent_a_ceiling,
     "with no corpus reading a large figure stays published — a made-up ceiling is not a measurement"),
    ("freebound", _attempt_free_space_is_not_a_bound,
     "freed may exceed free space, because footage can be written between the prune and the reading"),
    ("eligible", _attempt_eligible_is_not_a_bound,
     "eligible_mb is a different figure and must not veto prunedMb"),
    ("tiny", _attempt_a_tiny_real_figure_is_kept,
     "a tiny finite figure against a large corpus is a measurement"),
    ("dirpath", _attempt_a_directory_is_not_a_history,
     "a directory path publishes nothing, rather than a row beside the directory"),
    ("whentime", _attempt_a_refusal_still_says_when,
     "a refused figure still carries the time the reading was taken"),
    ("twowhys", _attempt_two_refusals_keep_their_own_reasons,
     "two refused rows in one series keep two reasons, not the first copied onto the second"),
)


def prove():
    # ⚠⚠ #123 — THE LOCK IS NOT THIS HARNESS'S SUBJECT, EXCEPT IN THE ATTEMPTS THAT SAY SO.
    # disk_history_append publishes prunedMb only when self_arming.may("prune.reports") opens. Every
    # KEEP axis (eligible, tiny, noceiling, freebound, boundary…) and the baseline silently relied on
    # the REAL lock being open — true on his Mac, false on a CI runner (no evidence, no census), where
    # `eligible` and `tiny` read 0/2 LEAKS and the run went red for a reason that had nothing to do
    # with the validator it proves. prune.reports is pinned OPEN for the whole run; the lock attempts
    # (lockshut, lockunreadable) install their own stubs on top and restore to this one.
    import self_arming as SA
    _real_may = SA.may
    SA.may = lambda lock, *a, **k: ((True, "harness: the lock is not this attempt's subject")
                                    if lock == "prune.reports" else _real_may(lock, *a, **k))
    try:
        return _prove_pinned()
    finally:
        SA.may = _real_may


def _prove_pinned():
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
        print("  " + bank_live())
    return 0 if rep["state"] == "PROVEN" else 1


def bank_live():
    """One check over his real series: every published figure is still one the writer would keep.

    attacks=1 because a series is one question asked of many rows, not many questions.
    A series that is missing, or that holds no numeric figure, banks nothing.
    """
    import control_app as ca
    import self_arming as SA
    p = ca._disk_history_path()
    if not os.path.isfile(p):
        return "live NOT banked: no disk history on this machine — UNKNOWN, not a pass"
    n = k = 0
    with io.open(p, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if not isinstance(row, dict) or row.get("prunedMb") is None:
                continue
            n += 1
            kept, _why = ca.credible_pruned_mb(row.get("prunedMb"), row.get("histBytes"))
            published = row.get("prunedMb")
            same = kept == published or (kept == 0 and published == 0)
            if same:
                k += 1
    if n == 0:
        return "live NOT banked: the series holds no numeric prunedMb — nothing to agree with"
    if k != n:
        return ("live NOT banked: %d of %d published figures fail credible_pruned_mb — "
                "that disagreement is the finding" % (k, n))
    SA.bank("prune.reports", "live", "disk_report_live", n=n, k=k, attacks=1,
            ref="live-series",
            note="every numeric prunedMb in his disk history is still a figure the writer would keep")
    return "banked LIVE prune.reports n=%d k=%d attacks=1" % (n, k)


RED_PROOF = [
    {
        'why': 'The gate (tv/disk_report_wilson.py, a SCRIPT not a unittest suite) grades control_app.credible_pruned_mb — the WRITE-end validator disk_history_append calls before it puts prunedMb on disk. Its `negative` attack hands the writer -1.0 .. -8.0 MB eight times and requires each row to come back prunedMb=None WITH a prunedWhy sentence. The refusal is one line in credible_pruned_mb: `if v < 0:` -> return None, "prunedMb was negative (%r) — pruning does not consume space". Widening that threshold to -1e18 deletes the real refusal without touching any comment, message string or shared constant: a negative figure then falls through the ==0 branch, fails the corpus bound (-1.0 is not > 8583 MB * 1.01) and is PUBLISHED verbatim as prunedMb=-1.0 — exactly the sign error reaching a dashboard that the law exists to refuse. It is not the wrong side of a union (only the negative axis moves; notanumber, notfinite and overcorpus stay 8/8) and it is not a shared constant (the baseline control still holds, so the red is a leak, not a withdrawn instrument).  MEASURED: untampered GREEN. `perl -e \'alarm 200; exec @ARGV\' python3 disk_report_wilson.py` from tv/ ; tampered (all 1) RED. Same command after replacing ALL 1 occurrence -> exit 1, "LEAKS · 24 of 32 ; reddened law disk_report_wilson._attempt_negative — the "negative" claim in CLAIMS ; ALONE FAILS ALONE. Fresh process, no siblings: `python3 -c "import disk_report_wilson as D; n,k=D._attempt.',
        'file': 'control_app.py',
        'find': 'if v < 0:',
        'replace': 'if v < -1e18:',
        'matches': 1,
    },
]


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
