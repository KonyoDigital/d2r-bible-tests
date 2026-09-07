# -*- coding: utf-8 -*-
"""A SUCCESSFUL WALK THAT FOUND NOTHING SAID NOTHING, SO A STILL RIVER AND A DEAD LOOP LOOKED ALIKE.

Konyo, 2026-09-07, asking for the shelf drawn as the river: *"honest and accurate and pinpointed of
course.. i want it visually synced to the backend"*. Before that view can be honest, the thing it
draws has to be measurable — and it was not.

`_retro_triage_loop` already walked the river every tick, and already reported TWO of the three
outcomes:
    ok and moved      -> prints each transition
    not ok            -> prints "river: NOT WALKED - <why>"
    ok and nothing    -> printed NOTHING and stored NOTHING          <- the hole

MEASURED before this shipped, on his real store:
    40 stamps · every one `by: claude:first-wiring` · newest 12.8h old · 0 of 40 carrying a `from`
**Not one row had ever been written by `loop:tvd-retro-triage`.**

⚠⚠ AND THAT IS CONSISTENT WITH TWO OPPOSITE FACTS: the river is genuinely still, or the loop never
runs. Nothing in the tree could separate them. A river view built on that would show "no movement"
and neither he nor I could say which it meant — an instrument whose whole purpose is telling him
something is wrong, unable to tell him the instrument itself stopped.
[[feedback-silence-is-not-evidence]] [[unknown-stays-unknown]] [[zero-needs-a-denominator]]

⇒ The walk now records that it RAN — when, how many reels it compared, how many moved INCLUDING
ZERO — and publishes it on /api/status. `moved: 0` beside `at: 2s ago` is a measurement. Silence
is not.

⛔ AND THE ROW DOES NOT REDDEN ON A CALM RIVER. Most ticks find nothing, by design. It reddens when
the WATCHING stops. A row that fires on the normal case is a row he stops reading.
"""
import ast
import io
import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import console_doctor as D  # noqa: E402
import control_app as CA  # noqa: E402

SRC = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()


def _fn(name, src=None):
    s = src if src is not None else SRC
    i = s.find("def %s(" % name)
    if i < 0:
        return None
    j = s.find("\ndef ", i + 1)
    return s[i:j if j > i else len(s)]


def _row():
    return dict(D.CHECKS)["river walk"]()


def _with(**kw):
    """Force a walk state and read the doctor row."""
    real = dict(CA._RIVER_WALK)
    CA._RIVER_WALK.update(kw)
    try:
        return _row()
    finally:
        CA._RIVER_WALK.clear()
        CA._RIVER_WALK.update(real)


class TheRiverWalkSaysItWalked(unittest.TestCase):

    def test_the_row_is_registered(self):
        self.assertIn("river walk", dict(D.CHECKS),
                      "the row is defined and not registered, so it never runs")

    # ── ⚠⚠ THE LAW THAT IS THE ACTUAL FIX ─────────────────────────────────────────────────────
    def test_the_loop_records_on_EVERY_outcome_not_only_the_two_it_printed(self):
        """The defect was that a successful walk finding nothing wrote no state. Pinning this from
        the loop's own source, because the behaviour only happens on a live tick."""
        blk = _fn("_retro_triage_loop")
        self.assertIsNotNone(blk, "the loop is gone or renamed — fix this guard first")
        i = blk.find("_rvs.run(")
        self.assertGreater(i, 0, "the loop no longer walks the river")
        after = blk[i:i + 1200]
        self.assertIn('_RIVER_WALK["at"] = time.time()', after,
                      "the walk's result is not recorded before it is reported, so a successful "
                      "walk that found nothing still leaves no trace")
        # ⚠ recorded BEFORE the `if moved` branch, or it only ever records the interesting case
        self.assertLess(after.find('_RIVER_WALK["at"]'), after.find('if _rv.get("ok") and'),
                        "the state is written INSIDE the moved-branch, so a quiet tick records "
                        "nothing — which is the whole defect")

    def test_a_walk_that_RAISED_does_not_leave_a_stale_success(self):
        """The except path must update the state too. Leaving the previous tick's numbers makes a
        crashed walk read as a healthy one that found nothing."""
        blk = _fn("_retro_triage_loop")
        i = blk.find("except Exception as _rve")
        self.assertGreater(i, 0, "the walk's own except arm is gone")
        self.assertIn('_RIVER_WALK["ok"] = False', blk[i:i + 700],
                      "a raised walk leaves the previous tick's state in place")

    # ── ⚠ UNKNOWN IS NEVER A STILL RIVER ──────────────────────────────────────────────────────
    def test_never_walked_is_UNKNOWN_not_OK(self):
        st, say = _with(at=None, ok=None, reels=None, moved=None, walks=0)
        self.assertEqual(D.UNKNOWN, st, "a walk that never ran was graded: %s" % say)
        self.assertIn("not a still river", say,
                      "the message does not distinguish 'nobody looked' from 'nothing moved'")

    # ── ⛔ IT MUST NOT CRY WOLF ON THE NORMAL CASE ─────────────────────────────────────────────
    def test_a_fresh_walk_that_found_NOTHING_is_OK(self):
        """Most ticks find nothing. A row that reddens on that is a row he stops reading."""
        st, say = _with(at=time.time(), ok=True, reels=40, moved=0, walks=7)
        self.assertEqual(D.OK, st, "a calm river was graded as a fault: %s" % say)
        self.assertIn("40", say, "the message does not carry the denominator it compared")

    # ── ⚠⚠ IT MUST GO RED WHEN THE WATCHING STOPS ─────────────────────────────────────────────
    def test_a_STALE_walk_is_a_finding(self):
        st, say = _with(at=time.time() - 3600, ok=True, reels=40, moved=0, walks=7)
        self.assertEqual(D.MISSING, st, "the watcher stopped an hour ago and nothing said so")
        self.assertIn("WATCHER", say.upper(),
                      "the message blames the river rather than the watcher")

    def test_a_FAILED_walk_is_a_finding(self):
        st, say = _with(at=time.time(), ok=False, reels=None, moved=None, why="simulated")
        self.assertEqual(D.MISSING, st, "a failed walk was graded fine: %s" % say)

    # ── it must reach a surface a supervisor reads ────────────────────────────────────────────
    def test_the_state_is_PUBLISHED_not_only_recorded(self):
        """⚠ Recording it in a module global and shipping nothing to a surface is the exact defect
        control_app's own v2457 note describes: 'I recorded the paint witness ... and shipped
        nothing to the surface a supervisor reads'."""
        blk = _fn("status_payload")
        self.assertIsNotNone(blk, "status_payload is gone")
        self.assertIn('"riverWalk": river_walk_state()', blk,
                      "the river walk heartbeat is recorded but never published, so no supervisor "
                      "and no view can read it")

    def test_the_state_reports_its_own_age(self):
        d = CA.river_walk_state()
        self.assertIn("ageS", d, "the state carries no age, so staleness cannot be judged")
        self.assertIsNone(d.get("ageS") if d.get("at") is None else 0,
                          "ageS must be None when nothing has walked, never a number")

    def test_it_still_parses(self):
        ast.parse(SRC)


if __name__ == "__main__":
    unittest.main(verbosity=2)
