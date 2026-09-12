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


def _loop_context(fn):
    """-> {node: (multiplier, clock_cap, unbounded)} for every sleep call in `fn`."""
    parents = {}
    for n in ast.walk(fn):
        for c in ast.iter_child_nodes(n):
            parents[c] = n
    return parents


def _slice_bound(node):
    """`for x in SEQ[:N]` -> N. Anything else -> None, meaning the count is not knowable here."""
    if isinstance(node, ast.For) and isinstance(node.iter, ast.Subscript):
        sl = node.iter.slice
        if isinstance(sl, ast.Slice) and isinstance(sl.upper, ast.Constant):
            return sl.upper.value
    return None


def _while_seconds(node):
    """`while monotonic() - t0 < T:` -> T, the wall-clock cap on that level."""
    if isinstance(node, ast.While):
        for c in ast.walk(node.test):
            if isinstance(c, ast.Constant) and isinstance(c.value, (int, float)) and c.value >= 1:
                return float(c.value)
    return None


def _worst_sleep_path_in(tree, fname):
    """-> (seconds, unbounded) — how long ONE turn can spend sleeping, and whether that is knowable.

    ⚠⚠ v3001 — THE v2998 VERSION COUNTED EACH `time.sleep()` ONCE AND WAS WRONG BY 6x ON A LIVE
    LANE. Five of `_kai_closer_loop`'s eight sleeps sit INSIDE inner loops: sleep(6.0) runs under
    `while monotonic - t0 < 120.0`, itself inside `for _ff in _frames_q[:4]` — that ONE path is up
    to 480s. Summing the literals gave 99.08s and blessed a 240s bound; loop-aware the derived path
    is 609s, so the law certified a bound that would report a HEALTHY turn as a dead thread. The
    guard's own threshold was smaller than the defect, in the opposite direction from v2998's fix.

    ⚠ AND `unbounded` IS THE LOAD-BEARING HALF. Four of those sleeps are under `for it in frames` /
    `for _sc in _super_cands` — no literal caps them, so there is NO static ceiling to derive. A
    number returned for such a loop would be a guess wearing a measurement's clothes, and the
    caller must refuse to bless any bound at all rather than pick a bigger one.
    [[feedback-threshold-above-the-ceiling]] [[unknown-stays-unknown]]
    """
    for fn in ast.walk(tree):
        if not (isinstance(fn, ast.FunctionDef) and fn.name == fname):
            continue
        parents = _loop_context(fn)
        total, seen, unbounded = 0.0, False, False
        for n in ast.walk(fn):
            if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "sleep" and n.args):
                continue
            vals = _literal_seconds(n.args[0])
            if not vals:
                continue
            seen = True
            contrib, mult, p = max(vals), 1, parents.get(n)
            while p is not None and p is not fn:
                if isinstance(p, ast.While):
                    cap = _while_seconds(p)
                    if cap:
                        contrib = max(contrib, cap)     # the while's clock caps that level
                elif isinstance(p, ast.For):
                    b = _slice_bound(p)
                    if b is None:
                        unbounded = True
                    else:
                        mult *= b
                p = parents.get(p)
            total += contrib * mult
        return (total, unbounded) if seen else (None, False)
    return (None, False)


def _periodless_tick_lanes(tree):
    """-> {lane: call} for every _lane_tick that passes every_s=None (positionally or by name)."""
    out = {}
    for lane, call in _tick_calls(tree).items():
        every = call.args[1] if len(call.args) > 1 else _kw(call, "every_s")
        if every is None or (isinstance(every, ast.Constant) and every.value is None):
            out[lane] = call
    return out


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
    def test_every_boundable_periodless_lane_declares_a_bound(self):
        """A lane that CAN be bounded and is not is an UNTIMED lane, which can never go red.

        ⚠ "CAN BE" IS DERIVED, NOT ASSUMED. v2994 required a bound from all three periodless lanes
        including `_kai_closer_loop`, whose sleeps run under unbounded `for` loops — so the law
        demanded a number that could only ever be a guess, and the guess it got was 240s against a
        derivable 609s path. A lane is required to declare a bound only where one can be derived.
        """
        tree = _control_tree()
        calls = _tick_calls(tree)
        for lane in COMPUTED_SLEEP_LANES:
            self.assertIn(lane, calls, "%s no longer stamps a tick at all" % lane)
        missing = []
        for lane, call in _periodless_tick_lanes(tree).items():
            worst, unbounded = _worst_sleep_path_in(tree, lane)
            if unbounded or worst is None:
                continue                                  # honestly UNTIMED — the next law pins it
            v = _kw(call, "dead_after_s")
            if not (isinstance(v, ast.Constant) and isinstance(v.value, (int, float))
                    and v.value > 0):
                missing.append("%s (worst path %.2fs, so a bound IS derivable)" % (lane, worst))
        self.assertEqual(missing, [],
                         "these lanes can be bounded and are not, so nothing can ever report them "
                         "late: %s" % ", ".join(missing))

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

    def test_each_bound_clears_its_own_loops_worst_sleep_path(self):
        """⚠ DERIVED, NOT LISTED. Every periodless lane is checked, so a NEW one cannot arrive with
        a guessed bound and no law noticing."""
        tree = _control_tree()
        bad = []
        for lane, call in _periodless_tick_lanes(tree).items():
            bound = _kw(call, "dead_after_s")
            bound = bound.value if isinstance(bound, ast.Constant) else None
            worst, unbounded = _worst_sleep_path_in(tree, lane)
            if bound is None:
                continue                       # the next law governs whether that is allowed
            if unbounded:
                bad.append("%s: declares bound=%s while its worst sleep path is UNBOUNDED" % (lane, bound))
            elif worst is None or bound <= worst:
                bad.append("%s: bound=%s worst sleep PATH=%s" % (lane, bound, worst))
        self.assertEqual(bad, [],
                         "a silence bound must clear the longest a single turn can spend SLEEPING, "
                         "counting sleeps inside INNER loops — %s" % "; ".join(bad))

    def test_the_reader_multiplies_a_sleep_by_its_enclosing_for_slice(self):
        """⚠⚠ GRADED ON A FIXTURE, BECAUSE NO LIVE LANE EXERCISES IT. heart2 called the
        for-slice red-proof BLIND: removing the multiplier changed nothing, since
        `_kai_closer_loop` is UNBOUNDED either way and the other two periodless lanes contain no
        for-slices at all. The law was right and the sabotage was pointing at a path no lane
        walks. A property worth guarding needs a case that exercises it.
        [[sabotage-is-usually-the-wrong-one]] [[gate-blind-to-unexercised-input]]"""
        src = ("import time\n"
               "def _loopy():\n"
               "    while True:\n"
               "        for x in jobs[:5]:\n"
               "            time.sleep(3.0)\n")
        worst, unbounded = _worst_sleep_path_in(ast.parse(src), "_loopy")
        self.assertFalse(unbounded, "jobs[:5] is a literal cap, so this IS derivable")
        self.assertEqual(worst, 15.0,
                         "a 3.0s sleep inside `for x in jobs[:5]` is 15s of sleeping per turn, "
                         "not 3s — counting the call once is the v2998 undercount that blessed a "
                         "240s bound against a 609s path; got %s" % worst)

    def test_the_reader_takes_an_enclosing_while_clock_as_the_cap(self):
        """`while monotonic() - t0 < 120.0: time.sleep(6.0)` sleeps up to 120s, not 6s."""
        src = ("import time\n"
               "def _waity():\n"
               "    while True:\n"
               "        while time.monotonic() - t0 < 120.0:\n"
               "            time.sleep(6.0)\n")
        worst, _u = _worst_sleep_path_in(ast.parse(src), "_waity")
        self.assertEqual(worst, 120.0,
                         "the inner while's own clock caps that level at 120s; got %s" % worst)

    def test_an_unbounded_for_makes_the_path_unknowable(self):
        src = ("import time\n"
               "def _endless():\n"
               "    while True:\n"
               "        for x in everything:\n"
               "            time.sleep(2.0)\n")
        _w, unbounded = _worst_sleep_path_in(ast.parse(src), "_endless")
        self.assertTrue(unbounded,
                        "`for x in everything` has no literal cap, so no ceiling can be derived "
                        "and any bound would be a guess wearing a measurement's clothes")

    def test_a_lane_whose_worst_path_is_unbounded_declares_no_bound(self):
        """⚠⚠ THE v2994 BOUND ON _kai_closer_loop WAS A FALSE RED THAT SHIPPED. Four of its sleeps
        run under unbounded `for` loops, so no static ceiling exists; the 240s it carried was below
        even the DERIVABLE 609s path. A bound that fires on a healthy turn costs more than the red
        path it buys, and UNTIMED is the honest state lane_liveness keeps for exactly this."""
        tree = _control_tree()
        bad = []
        for lane, call in _periodless_tick_lanes(tree).items():
            _w, unbounded = _worst_sleep_path_in(tree, lane)
            if unbounded and _kw(call, "dead_after_s") is not None:
                bad.append(lane)
        self.assertEqual(bad, [],
                         "these lanes sleep inside unbounded loops, so any bound is a guess "
                         "wearing a measurement's clothes: %s" % ", ".join(bad))


RED_PROOF = [
    {
        "why": "restoring the withdrawn 240s bound on _kai_closer_loop is the false red verbatim: "
               "a lane whose derivable sleep path is 609s, with four more paths under unbounded "
               "for loops, reported as a dead thread on a healthy turn",
        "file": "control_app.py",
        "find": "            _lane_tick('_kai_closer_loop', None)",
        "replace": "            _lane_tick('_kai_closer_loop', None, dead_after_s=240)",
        "matches": 1,
    },
    {
        "why": "taking the bound off a lane that CAN be bounded returns it to UNTIMED, where no "
               "silence of any length can turn it red",
        "file": "control_app.py",
        "find": "_lane_tick('_bridge_prober', None, dead_after_s=30)",
        "replace": "_lane_tick('_bridge_prober', None)",
        "matches": 1,
    },
    {
        "why": "ignoring the multiplier from an enclosing for-slice restores the v2998 undercount "
               "that blessed 240s against a 609s path",
        "file": "test_a_lane_with_no_period_can_still_go_red.py",
        "find": "                    else:\n                        mult *= b",
        "replace": "                    else:\n                        mult *= 1",
        "matches": 1,
    },
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
        "why": "a bound BELOW the loop's own worst sleep path would report a perfectly healthy turn "
               "as a dead thread; the ceiling law must catch it. Retargeted at v3001 onto "
               "_engine_driver, because the 240s bound this used to sabotage was itself withdrawn "
               "as a false red — a proof whose anchor no longer exists proves nothing.",
        "file": "control_app.py",
        "find": "dead_after_s=60)",
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
