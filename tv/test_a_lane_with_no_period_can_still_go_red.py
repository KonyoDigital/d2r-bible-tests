#!/usr/bin/env python3
"""v2994 — A COMPUTED SLEEP IS NOT A LICENCE TO BE UNFALSIFIABLE.

`lane_liveness` had ONE field carrying TWO questions. `every_s` answers *how often does this run*;
it is what prints "against its own 30s period - 2 missed cycles". LATE needs a different question:
*how long may this be silent before the THREAD is dead*. For a fixed-sleep lane the two coincide.
For a loop that picks its sleep per branch they come apart — and there was no way to say "no fixed
period, but certainly dead after 60s", so those loops passed `every_s=None`, became permanently
UNTIMED, and no silence of any length could turn them red.

MEASURED on his console 2026-09-12 over a 90s window: `_bridge_prober` ticked every 1.2s,
`_engine_driver` every 2.0s, `_kai_closer_loop` every 30.0s. All three reported UNTIMED. Three of
twenty lanes, every one alive, every one unfalsifiable.

⚠ THE TEMPTING WRONG FIX IS TO PAD `every_s`. That buys a red path by making the report print a
period the loop does not have — `_bridge_prober` would read "its own 30s period" about a loop that
sleeps 1.2s. The number stays technically defensible, which is the version of
[[label-outlived-referent]] that survives review. test_no_lane_fakes_a_period_to_get_a_bound is
here to refuse it.

⚠ AND A BOUND BELOW THE LOOP'S OWN WORST SLEEP IS WORSE THAN NONE — it cries wolf on a healthy
turn, and a gate he learns to skip is a gate that is not there.
[[feedback-threshold-above-the-ceiling]]
"""
import ast
import io
import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lane_liveness as LL  # noqa: E402

#: the loops that pick their sleep per branch, and therefore cannot answer `every_s`.
COMPUTED_SLEEP_LANES = ("_bridge_prober", "_engine_driver", "_kai_closer_loop")


def _control_tree():
    return ast.parse(io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read())


def _tick_calls(tree):
    """-> {lane: ast.Call} for every _lane_tick(...) with a literal lane name.

    ⚠ PARSED, NEVER GREPPED. A law that reads source by substring passes on a mention in a comment
    and fails on a line break. [[source-reading-guard]]
    """
    out = {}
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        if getattr(n.func, "id", None) != "_lane_tick" or not n.args:
            continue
        a0 = n.args[0]
        if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
            out[a0.value] = n
    return out


def _kw(call, name):
    for k in call.keywords or []:
        if k.arg == name:
            return k.value
    return None


def _literal_seconds(node):
    """-> [float] every constant this sleep argument could evaluate to, or [] if undecidable.

    ⚠ `_bridge_prober` sleeps `1.0 if IS_WIN else 1.2` — a platform choice, not a constant. A
    reader that only understands ast.Constant returns nothing for it, and "I could not read this"
    must never be allowed to look like "there is no sleep here". Both branches are literals, so
    both are real candidates and the larger one is the one a ceiling has to clear.
    [[source-reading-guard]]
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return [float(node.value)]
    if isinstance(node, ast.IfExp):
        return _literal_seconds(node.body) + _literal_seconds(node.orelse)
    return []


def _worst_sleep_path_in(tree, fname):
    """-> an upper bound on how long ONE turn of this loop can spend sleeping, or None.

    ⚠⚠ v2998 — THIS TOOK THE LARGEST SINGLE `time.sleep()` AND THAT IS NOT THE QUANTITY THE LAW
    NEEDS. control_app.py's own v2994 comment says `_kai_closer_loop` has "eight sleeps, 0.08s to
    30.0s; a single turn taking the slow branches is ~79s of sleeping alone" — while the largest
    single literal is 30.0. So a bound of 31 would have PASSED this law and then reported a
    perfectly healthy 79s turn as a dead thread: the exact false-LATE the law exists to refuse,
    admitted by the law itself. The guard's threshold was smaller than the defect it guards.

    SEPARATE STATEMENTS ADD; the branches of one IfExp are exclusive, so those take the larger.
    That over-counts a turn that cannot reach every sleep, which is the safe direction for a
    CEILING — a bound must clear the worst case, and over-estimating the worst case only ever
    makes the law stricter. None means it could not be read, which the caller treats as a refusal
    rather than a pass. [[feedback-threshold-above-the-ceiling]] [[source-reading-guard]]
    """
    for fn in ast.walk(tree):
        if isinstance(fn, ast.FunctionDef) and fn.name == fname:
            total = 0.0
            seen = False
            for n in ast.walk(fn):
                if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                        and n.func.attr == "sleep" and n.args):
                    vals = _literal_seconds(n.args[0])
                    if vals:
                        seen = True
                        total += max(vals)      # one call contributes once, at its largest branch
            return total if seen else None
    return None


class ALaneWithNoPeriodCanStillGoRed(unittest.TestCase):

    def setUp(self):
        LL.forget_all_for_tests()

    def _state(self, lane, at):
        return [r for r in LL.rows(now=at) if r["lane"] == lane][0]

    # ── the mechanism ─────────────────────────────────────────────────────────────────────────
    def test_a_declared_bound_turns_red(self):
        """The whole point: silence past a declared bound is LATE, with no period in sight."""
        now = time.monotonic()
        LL.tick("computed", None, 60)
        r = self._state("computed", now + 61)
        self.assertEqual(r["state"], LL.LATE,
                         "a lane that declared a 60s silence bound and has been quiet 61s must be "
                         "LATE; got %s. A lane that cannot go red is not being watched." % r["state"])
        self.assertIsNone(r["everyS"],
                          "it must go red WITHOUT acquiring a period it does not have")

    def test_a_declared_bound_is_not_late_before_it(self):
        now = time.monotonic()
        LL.tick("computed", None, 60)
        r = self._state("computed", now + 59)
        self.assertEqual(r["state"], LL.FLOWING,
                         "59s against a 60s bound must not be LATE; got %s" % r["state"])

    def test_the_bound_is_reported_so_a_reader_can_check_it(self):
        """[[zero-needs-a-denominator]] — a verdict whose threshold is invisible cannot be argued
        with, and this one is a judgement call that deserves arguing with."""
        now = time.monotonic()
        LL.tick("computed", None, 60)
        r = self._state("computed", now + 1)
        self.assertEqual(r["boundS"], 60.0, "the bound must be published on the row")
        self.assertEqual(r["deadAfterS"], 60.0, "and it must be distinguishable from a period")

    # ── the floor it must NOT overwrite ───────────────────────────────────────────────────────
    def test_a_lane_with_neither_stays_untimed_forever(self):
        """UNKNOWN stays UNKNOWN. A lane that declares no period AND no bound is genuinely
        undecidable, and inventing a default here would be a verdict with no author.
        [[unknown-stays-unknown]]"""
        now = time.monotonic()
        LL.tick("periodless", None, None)
        r = self._state("periodless", now + 9999)
        self.assertEqual(r["state"], LL.UNTIMED,
                         "with no period and no bound the honest answer is UNTIMED, not a guess")
        self.assertIsNone(r["boundS"], "and it must not publish a bound it never declared")

    def test_a_period_lane_is_unchanged(self):
        now = time.monotonic()
        LL.tick("fixed", 20, None)
        self.assertEqual(self._state("fixed", now + 10)["state"], LL.FLOWING)
        r = self._state("fixed", now + 70)
        self.assertEqual(r["state"], LL.LATE)
        self.assertEqual(r["boundS"], 20 * LL.STALE_SLACK,
                         "a period still implies period x slack, untouched by the new field")

    # ── the console's own three ───────────────────────────────────────────────────────────────
    def test_the_computed_sleep_lanes_each_declare_a_bound(self):
        calls = _tick_calls(_control_tree())
        missing = []
        for lane in COMPUTED_SLEEP_LANES:
            self.assertIn(lane, calls, "%s no longer stamps a tick at all" % lane)
            v = _kw(calls[lane], "dead_after_s")
            if not (isinstance(v, ast.Constant) and isinstance(v.value, (int, float))
                    and v.value > 0):
                missing.append(lane)
        self.assertEqual(missing, [],
                         "these lanes pick their sleep per branch, so they cannot declare a "
                         "period — without dead_after_s they are UNTIMED, which can never go "
                         "red: %s" % ", ".join(missing))

    def test_no_lane_fakes_a_period_to_get_a_bound(self):
        """Padding every_s would buy the red path by printing a period the loop does not have."""
        calls = _tick_calls(_control_tree())
        for lane in COMPUTED_SLEEP_LANES:
            c = calls[lane]
            every = c.args[1] if len(c.args) > 1 else _kw(c, "every_s")
            self.assertTrue(every is None or (isinstance(every, ast.Constant)
                                              and every.value is None),
                            "%s must keep every_s=None — its sleep is chosen per branch, so any "
                            "number here is a period it does not have" % lane)

    def test_each_bound_is_above_its_own_loops_worst_sleep(self):
        """A bound under the loop's own sleep fires on a healthy turn, and a gate that cries wolf
        is one he learns to skip. [[feedback-threshold-above-the-ceiling]]"""
        tree = _control_tree()
        calls = _tick_calls(tree)
        bad = []
        for lane in COMPUTED_SLEEP_LANES:
            bound = _kw(calls[lane], "dead_after_s")
            bound = bound.value if isinstance(bound, ast.Constant) else None
            worst = _worst_sleep_path_in(tree, lane)
            if bound is None or worst is None or bound <= worst:
                bad.append("%s: bound=%s worst sleep PATH=%s" % (lane, bound, worst))
        self.assertEqual(bad, [],
                         "a silence bound must exceed the longest a single turn can spend "
                         "SLEEPING — not merely its largest single sleep — or it reports a healthy "
                         "slow turn as a dead thread: %s" % "; ".join(bad))


RED_PROOF = [
    {
        "why": "disabling the bounded path returns these lanes to UNTIMED, which is exactly the "
               "hole this gate exists to close: silence of any length stops being decidable",
        "file": "lane_liveness.py",
        "find": "        if dead is not None:",
        "replace": "        if False:",
        "matches": 1,
    },
    {
        "why": "removing the bound from a real call site leaves that lane unfalsifiable again",
        "file": "control_app.py",
        "find": ", dead_after_s=30)",
        "replace": ")",
        "matches": 1,
    },
    {
        "why": "a bound BELOW the loop's own 30.0s sleep would report a perfectly healthy turn as "
               "a dead thread; the ceiling law must catch it",
        "file": "control_app.py",
        "find": "dead_after_s=240)",
        "replace": "dead_after_s=1)",
        "matches": 1,
    },
]

if __name__ == "__main__":
    # ⚠ HIS CONSOLE IS cp1255 AND CANNOT ENCODE THE ARROWS AND STARS THIS FILE PRINTS. Without
    # this, a CORRECT tree reports FAILURE because the process dies inside its own print — the
    # dangerous direction, because it teaches people to ignore the tool. [[REG-044/054/077]]
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
