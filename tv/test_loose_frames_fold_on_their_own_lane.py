# -*- coding: utf-8 -*-
"""REG-2463 (#168) — LOOSE FRAMES FOLD ON THEIR OWN LANE, AND WHAT THE LANE LEAVES LOOSE IS NAMED.

His ruling 2026-10-21 (#168): "FOLD + LANE". A session that dies before it seals leaves its f_<ms>.jpg frames loose in
hist/, where no lane and no deleter can see them - MEASURED on Dean's PC: 67,925 frames (2.53 GB) in no reel; a fold
by hand moved 65,457 into 18 reels and left 2,468 loose in 18 clusters an existing reel overlaps. Nothing folded on its
own on any PC: console_healer's remedy runs only with TV_AUTO_HEAL=1 (unset everywhere), and armed, its still-red rule
would disarm it for good after one fold, because the doctor's row stays MISSING on the frames an overlap refuses.

THE LAW, on a fixture hist in this law's own scratch (fixture_tmp.contain(); every path is NAMED, nothing is listed):
  · one pass of the lane (orphan_fold.run_once) folds a finished cluster no reel covers into reel_s_<t0>_1 with its
    index, and says what it did;
  · a cluster an existing reel overlaps (a second session id for one recording) and one whose newest frame is still
    inside the gap (it may still be filming) stay loose, frame for frame, and are NAMED with their reasons; the one
    still filming is owed, the overlap is not;
  · the lane asks what is in flight FIRST: a refusal moves nothing and says why; nobody to ask is not permission;
  · one fold at a time: while another fold holds the fold lock, the lane moves nothing and says so;
  · the console's roster starts the lane under its own name, the loop stamps that name, and it is started on a
    cadence orphan_fold states.
RED_PROOF below. [[unknown-stays-unknown]] [[the-unjoined-end]]
"""
import ast
import io
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import fixture_tmp  # noqa: E402

fixture_tmp.contain()

import orphan_fold as OF  # noqa: E402

LANE = "tvd-orphan-fold"


def _frame(d, t):
    p = os.path.join(d, "f_%d.jpg" % t)
    with open(p, "wb") as fh:
        fh.write(b"\xff\xd8 frame %d" % t)
    return p


class _Hist(unittest.TestCase):
    """A hist dir holding: FINISHED - five frames two hours ago, no reel near them; OVERLAP - three loose frames ten
    seconds after an existing reel's window six hours ago (the reel holds three frames); GROWING - three frames, the
    newest twenty seconds old."""

    def setUp(self):
        self.hist = tempfile.mkdtemp(prefix="orphan-lane-")
        self.addCleanup(shutil.rmtree, self.hist, True)
        now = int(time.time() * 1000)
        self.finished = [now - 7200000 + 1000 * i for i in range(5)]
        self.sealed = [now - 21600000 + 1000 * i for i in range(3)]
        self.overlap = [now - 21600000 + 10000 + 1000 * i for i in range(3)]
        self.growing = [now - 22000 + 1000 * i for i in range(3)]
        self.reel = os.path.join(self.hist, "reel_s_%d_1" % self.sealed[0])
        os.makedirs(self.reel)
        for t in self.sealed:
            _frame(self.reel, t)
        for t in self.finished + self.overlap + self.growing:
            _frame(self.hist, t)
        self.made = os.path.join(self.hist, "reel_s_%d_1" % self.finished[0])

    def loose(self, ts):
        return [t for t in ts if os.path.isfile(os.path.join(self.hist, "f_%d.jpg" % t))]

    def asked(self, ok=True, why=""):
        self.questions = []

        def in_flight():
            self.questions.append(1)
            return ok, why
        return in_flight


class TheLaneFoldsOnlyWhatIsFinishedAndSeparate(_Hist):

    def test_a_finished_cluster_no_reel_covers_is_folded_with_its_index(self):
        r = OF.run_once(self.hist, in_flight=self.asked())
        self.assertEqual(self.questions, [1], "the lane did not ask what is in flight")
        self.assertEqual(self.loose(self.finished), [], "a finished cluster no reel covers was left loose: %s" % r["why"])
        for t in self.finished:
            self.assertTrue(os.path.isfile(os.path.join(self.made, "f_%d.jpg" % t)),
                            "frame %d is not in the reel its own stamp names" % t)
        self.assertTrue(os.path.isfile(os.path.join(self.made, "index.json")), "the folded reel has no index - no lane can read it")
        with io.open(os.path.join(self.made, "index.json"), encoding="utf-8") as fh:
            self.assertEqual(len(json.load(fh).get("frames") or []), len(self.finished))
        self.assertEqual((r["on"], r["worked"], r["folded"]), (True, len(self.finished), len(self.finished)), r)
        self.assertEqual(r["reels"], [os.path.basename(self.made)])
        self.assertIn("folded %d loose frame(s) into 1 reel(s)" % len(self.finished), r["why"])

    def test_an_overlapping_and_a_still_filming_cluster_stay_loose_and_are_named(self):
        r = OF.run_once(self.hist, in_flight=self.asked())
        self.assertEqual(self.loose(self.overlap), self.overlap,
                         "frames a sealed reel's window covers were folded - a second session id for one recording")
        self.assertEqual(self.loose(self.growing), self.growing,
                         "frames of a recording that may still be filming were folded")
        for t in self.sealed:
            self.assertTrue(os.path.isfile(os.path.join(self.reel, "f_%d.jpg" % t)), "the sealed reel lost a frame")
        named = {(c["kind"], c["t0"], c["frames"]) for c in r["refused"]}
        self.assertEqual(named, {("overlap", self.overlap[0], 3), ("growing", self.growing[0], 3)},
                         "what the lane left loose is not named: %r" % r["refused"])
        for c in r["refused"]:
            self.assertTrue(c.get("why"), "a cluster left loose without its reason")
        self.assertEqual(r["owed"], 1, "only the cluster that may still be filming is this lane's to fold later")
        self.assertIn("a person decides", r["why"])
        self.assertIn("may still be filming", r["why"])


class TheLaneAsksFirstAndFoldsAlone(_Hist):

    def test_an_in_flight_refusal_moves_nothing_and_says_why(self):
        r = OF.run_once(self.hist, in_flight=self.asked(False, "a vault sweep is reading"))
        self.assertEqual(self.loose(self.finished), self.finished, "frames moved while a sweep was reading")
        self.assertFalse(os.path.exists(self.made))
        self.assertIsNone(r["worked"])
        self.assertIn("a vault sweep is reading", r["why"])

    def test_nobody_to_ask_is_not_permission(self):
        r = OF.run_once(self.hist, in_flight=None)
        self.assertEqual(self.loose(self.finished), self.finished, "frames moved with nobody asked what was in flight")
        self.assertIsNone(r["worked"])
        self.assertIn("not permission", r["why"])

    def test_while_another_fold_holds_the_lock_the_lane_moves_nothing(self):
        held, done = threading.Event(), threading.Event()

        def other_fold():
            with OF._FOLD_LOCK:
                held.set()
                done.wait(5)
        t = threading.Thread(target=other_fold)
        t.start()
        self.addCleanup(t.join, 10)
        self.addCleanup(done.set)
        self.assertTrue(held.wait(5), "PREMISE: the other fold never took the lock")
        r = OF.run_once(self.hist, in_flight=self.asked())
        done.set()
        self.assertEqual(self.loose(self.finished), self.finished, "the lane folded while another fold was moving frames")
        self.assertIsNone(r["worked"])
        self.assertIn("another fold", r["why"])


class TheConsoleRunsTheLane(unittest.TestCase):
    """Real objects where they can be had, the roster parsed where starting it would start every lane."""

    def test_the_roster_starts_the_lane_under_its_own_name(self):
        import health_engine as HE
        spans, src = HE._lane_spans()
        self.assertIn("_orphan_fold_loop", spans, "the loop is not in the console's roster: %s" % sorted(spans))
        self.assertEqual(spans["_orphan_fold_loop"][0], LANE)
        fn = [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == "_orphan_fold_loop"]
        self.assertEqual(len(fn), 1)
        ticks = [c.args[0].value for c in ast.walk(fn[0]) if isinstance(c, ast.Call)
                 and getattr(c.func, "id", "") == "_lane_tick" and c.args and isinstance(c.args[0], ast.Constant)]
        self.assertEqual(ticks, [LANE], "the lane does not stamp its beat under its own name: %r" % ticks)
        calls = [c for c in ast.walk(fn[0]) if isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "run_once"]
        self.assertEqual(len(calls), 1, "the loop never runs a pass")
        self.assertIn("in_flight", [k.arg for k in calls[0].keywords], "the loop runs a pass that asks nothing")
        self.assertEqual(OF.LANE, LANE)

    def test_the_cadence_is_the_one_orphan_fold_states(self):
        import control_app as CA
        self.assertEqual((CA._ORPHAN_FOLD_FIRST_S, CA._ORPHAN_FOLD_EVERY_S), (OF.FIRST_S, OF.EVERY_S))
        self.assertLess(OF.FIRST_S, OF.EVERY_S)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-2463 - the fold stops asking whether a cluster is eligible: a window a sealed reel covers is folded "
               "into a second session id, and a recording that may still be filming is sealed under him",
        "file": "orphan_fold.py",
        "find": "        if not c.get(\"eligible\"):\n            continue                       # never fold a window a reel already covers\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-2463 - the lane stops asking what is in flight and folds frames out from under a sweep or a capture",
        "file": "orphan_fold.py",
        "find": "        if not ok:\n            out[\"why\"] = \"not folding while %s\" % (why or \"something is in flight\")\n            return out\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-2463 - the lane is missing from the console's roster: nothing folds loose frames on its own",
        "file": "control_app.py",
        "find": "        (\"tvd-orphan-fold\", _orphan_fold_loop),\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-2463 - the lane folds while another fold holds the lock: two folds move the same frames at once",
        "file": "orphan_fold.py",
        "find": "        if not _FOLD_LOCK.acquire(blocking=False):\n",
        "replace": "        if not _FOLD_LOCK.acquire(blocking=True, timeout=10):\n",
        "matches": 1,
    },
]
