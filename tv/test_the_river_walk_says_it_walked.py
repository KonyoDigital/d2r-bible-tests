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


RED_PROOF = [
    {
        "why": 'the law requires this text in control_app.py, where it occurs exactly once and in no other file the gate names; deleting it must turn the gate red',
        "file": 'control_app.py',
        "find": '_RIVER_WALK["ok"] = False',
        "replace": '_HEART2_TAMPERED_',
        "matches": 1,
    },
]

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
        # ⚠⚠ ANCHORED AT BOTH ENDS, NEVER A FIXED WINDOW. This read `blk[i:i+1200]` and broke the
        # moment a comment was added above the branch: the target slid past 1200 chars, `find`
        # returned -1, and the law reported the exact defect it exists to catch — about code that
        # was correct. A fixed-size window measures my guess at the region, not the region.
        # [[source-window-shortcut]] [[source-reading-guard]]
        j = blk.find('except Exception as _rve', i)
        self.assertGreater(j, i, "the walk block's own except arm is gone — cannot bound the region")
        after = blk[i:j]
        self.assertIn('_RIVER_WALK["at"] = time.time()', after,
                      "the walk's result is not recorded before it is reported, so a successful "
                      "walk that found nothing still leaves no trace")
        # ⚠ recorded BEFORE the `if moved` branch, or it only ever records the interesting case
        at_at = after.find('_RIVER_WALK["at"]')
        at_if = after.find('if _rv.get("ok") and')
        self.assertGreater(at_if, 0, "the moved-branch is gone from the walk block")
        self.assertLess(at_at, at_if,
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
        # ⚠⚠ v2839 — THIS PINNED THE CALL'S SPELLING AND I BROKE IT MYSELF ON v2826. REG-779
        # wrapped sixteen producers as `_t("section", producer)` so their cost lands in a named
        # section instead of `unattributedMs`; behaviour identical, and the text
        # `"riverWalk": river_walk_state()` is gone. REG-783 fixed three laws of exactly this shape
        # and I did not SWEEP for the rest, so this one sat RED on his tree for thirteen versions.
        # The law never changed: the walk's heartbeat must still be PUBLISHED. So it now asks the
        # parsed tree whether the producer is reached for that key, which survives wrapping,
        # aliasing and renaming a section while a DELETED producer still turns it red.
        # [[source-reading-guard]] [[sweep-dont-ask]]
        import ast as _ast
        _src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        _fns = [n for n in _ast.walk(_ast.parse(_src))
                if isinstance(n, _ast.FunctionDef) and n.name == "status_payload"]
        self.assertEqual(1, len(_fns), "status_payload is not a single top-level function")
        _reached = False
        for _d in _ast.walk(_fns[0]):
            if not isinstance(_d, _ast.Dict):
                continue
            for _k, _v in zip(_d.keys, _d.values):
                if not (isinstance(_k, _ast.Constant) and _k.value == "riverWalk"):
                    continue
                for _c in _ast.walk(_v):
                    if isinstance(_c, _ast.Call):
                        _f = _c.func
                        if isinstance(_f, _ast.Name) and _f.id == "river_walk_state":
                            _reached = True
                        if isinstance(_f, _ast.Name) and _f.id == "_t":
                            for _a in _c.args[1:]:
                                if isinstance(_a, _ast.Name) and _a.id == "river_walk_state":
                                    _reached = True
        self.assertTrue(_reached,
                        "the river walk heartbeat is recorded but never published under the "
                        "`riverWalk` key, so no supervisor and no view can read it")

    def test_the_state_reports_its_own_age(self):
        d = CA.river_walk_state()
        self.assertIn("ageS", d, "the state carries no age, so staleness cannot be judged")
        self.assertIsNone(d.get("ageS") if d.get("at") is None else 0,
                          "ageS must be None when nothing has walked, never a number")

    def test_every_key_the_heartbeat_READS_is_a_key_run_RETURNS(self):
        """⚠⚠ THE WRONG-KEY NULL, CAUGHT ON HIS LIVE CONSOLE. The first cut recorded
        `_rv.get("reels")` — and `river_stamp.run()` has NO `reels` key. It returns
        {ok, moved, unchanged, refused, shelf, why, transitions, refusals}. So the heartbeat stored
        None, and the doctor row printed it as "not measured" while the denominator sat three words
        away in the `why` string: "40 were already where the store said".

        A null produced by asking the wrong question is INDISTINGUISHABLE from a null nobody
        measured, which is the most expensive shape [[unknown-stays-unknown]] takes. This was the
        fourth wrong-key read of the session and the only one in fresh code — found because the
        LIVE console published it, not because anything failed.

        So this law does not pin one key. It compares EVERY key the loop reads off the walk result
        against the keys `run()` actually returns, and fails on any that cannot exist.
        [[zero-needs-a-denominator]] [[feedback-suspect-the-instrument]]
        """
        import re
        import river_stamp as RVS
        blk = _fn("_retro_triage_loop")
        self.assertIsNotNone(blk, "the loop is gone")
        read = set(re.findall(r'_rv\.get\(["\']([A-Za-z_]+)["\']\)', blk))
        self.assertTrue(read, "the loop reads nothing off the walk result — has it stopped walking?")
        real = RVS.run(by="test:key-contract")
        self.assertIsInstance(real, dict, "run() did not return a dict")
        missing = sorted(k for k in read if k not in real)
        self.assertEqual([], missing,
                         "the loop reads %r off the walk result, and run() returns no such key(s) "
                         "— every one of those silently stores None and renders as 'not measured'. "
                         "run() actually returns: %s" % (missing, sorted(real.keys())))

    def test_the_denominator_is_a_FIELD_not_only_prose(self):
        """`moved: 0` beside `reels: null` is a zero with no denominator, even when the number is
        present in the `why` sentence. A consumer cannot parse prose."""
        blk = _fn("_retro_triage_loop")
        self.assertIn('_RIVER_WALK["reels"] = _rv.get("shelf")', blk,
                      "the shelf size is not recorded, so `moved` has no denominator as a field")

    def test_it_still_parses(self):
        ast.parse(SRC)



if __name__ == "__main__":
    unittest.main(verbosity=2)
