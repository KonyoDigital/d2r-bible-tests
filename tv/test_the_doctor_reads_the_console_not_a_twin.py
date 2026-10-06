#!/usr/bin/env python3
"""v3012 (#80) — A DOCTOR ROW MEASURED A DEAD TWIN FOR ITS ENTIRE LIFE.

`_check_the_river_walk_is_walking` did `import control_app` and read a MODULE GLOBAL. The console
runs control_app as its own process entry, so that import builds a SECOND module instance whose
_RIVER_WALK is the empty literal — at=None, in every process, since the row was born. PROVEN by
one payload read two ways at the same instant: /api/status.riverWalk said walks=13, at 15s old,
while the eagle's copy of this row said "has not completed a tick in this process — unaskable for
4d (1468 attempts)". Four days of UNKNOWN about a walk that ran the whole time.

The row now reads THE WIRE — the serving process publishes its own state — and these laws pin
both the verdicts and the mechanism. [[the-unjoined-end]] [[feedback-suspect-the-instrument]]
"""
import ast
import io
import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import console_doctor as CD  # noqa: E402


class TheDoctorReadsTheConsoleNotATwin(unittest.TestCase):

    def _verdict(self, payload):
        real = CD._get
        CD._get = lambda path, *a, **k: (payload if path == "/api/status" else real(path))
        try:
            return CD._check_the_river_walk_is_walking()
        finally:
            CD._get = real

    def test_a_healthy_walk_on_the_wire_reads_ok(self):
        st, why = self._verdict({"riverWalk": {"at": time.time() - 5, "ok": True, "reels": 24,
                                               "moved": 0, "walks": 14, "why": ""}})
        self.assertEqual(st, "ok",
                         "the wire says the walk ran 5s ago; UNKNOWN here is the twin's face")
        self.assertIn("24", why)

    def test_the_twins_exact_face_is_unknown_not_ok(self):
        """at=None is what the dead twin published for four days — it must stay UNKNOWN."""
        st, _w = self._verdict({"riverWalk": {"at": None, "why": "never ticked"}})
        self.assertEqual(st, "unknown")

    def test_no_answer_is_unknown(self):
        st, why = self._verdict({})
        self.assertEqual(st, "unknown")
        self.assertIn("did not answer", why)

    def test_a_failed_walk_is_missing(self):
        st, _w = self._verdict({"riverWalk": {"at": time.time() - 5, "ok": False,
                                              "why": "boom"}})
        self.assertEqual(st, "missing")

    def test_a_stopped_watcher_is_missing(self):
        st, why = self._verdict({"riverWalk": {"at": time.time() - 3600, "ok": True,
                                               "reels": 24, "moved": 0, "walks": 2, "why": ""}})
        self.assertEqual(st, "missing")
        self.assertIn("WATCHER stopping", why)

    def test_the_row_never_imports_the_twin(self):
        """⚠ THE MECHANISM, PINNED BY AST — an `import control_app` inside this check is the
        defect reborn whatever it then reads. Parsed, never grepped: the module's comments name
        control_app in prose. [[source-reading-guard]]"""
        src = io.open(os.path.join(HERE, "console_doctor.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        fn = next(f for f in ast.walk(tree)
                  if isinstance(f, ast.FunctionDef)
                  and f.name == "_check_the_river_walk_is_walking")
        for n in ast.walk(fn):
            if isinstance(n, ast.Import):
                self.assertFalse(any(a.name == "control_app" for a in n.names),
                                 "the row imports control_app again — a second module instance "
                                 "whose globals are the empty literals, the four-day twin")


_NO_WIRE = object()
_NO_FIELD = object()


class TheOutletReadsTheWireNotATwin(unittest.TestCase):
    """The outlet row imported the console and read its route-lane counters. The console is
    __main__, so that import is a second module whose runs and attempts stay 0. A reel waiting
    to be closed out then read as a process too young to have ticked, and the failing-tick and
    never-ran sentences could not be reached."""

    def _outlet(self, pulse, waiting=True, routed=2, shelf=10):
        import reel_route_lane as lane
        import reel_router as rr
        saved = (rr.route, lane.plan, CD._get)
        asked = []

        def _route():
            return {"ok": True, "outletReadable": True,
                    "counts": {"ROUTED": routed}, "shelf": shelf}

        def _plan(_rep):
            return {"ok": True, "route": (["reel_a"] if waiting else []), "declined": []}

        def _get(path, *a, **k):
            asked.append(path)
            if path != "/api/river":
                return None
            if pulse is _NO_WIRE:
                return None
            if pulse is _NO_FIELD:
                return {"ok": True}
            return {"routeLane": pulse}

        rr.route, lane.plan, CD._get = _route, _plan, _get
        try:
            st, why = CD._check_the_river_has_an_outlet()
        finally:
            rr.route, lane.plan, CD._get = saved
        return st, why, asked

    def test_a_running_lane_on_the_wire_is_not_called_young(self):
        st, why, _asked = self._outlet({
            "ok": True, "runs": 4, "at": time.time() - 30, "attempts": 4,
            "raised": None, "stoodDown": False, "everyS": 90, "why": "routed 1"})
        self.assertEqual(st, "missing")
        self.assertIn("last ran", why)
        self.assertIn("routed 1", why)
        self.assertNotIn("process is young", why)
        self.assertNotIn("HAS NEVER RUN", why)

    def test_no_wire_is_unknown_not_the_young_process(self):
        st, why, _asked = self._outlet(_NO_WIRE)
        self.assertEqual(st, "unknown")
        self.assertIn("not on the wire", why)
        self.assertIn("not a young process", why)
        self.assertNotIn("process is young", why)
        self.assertNotIn("HAS NEVER RUN", why)

    def test_a_console_that_predates_the_pulse_is_unknown(self):
        st, why, _asked = self._outlet(_NO_FIELD)
        self.assertEqual(st, "unknown", why)
        self.assertIn("not on the wire", why)

    def test_the_twins_zero_counters_are_the_young_process_only_when_measured(self):
        st, why, _asked = self._outlet({
            "ok": True, "runs": 0, "attempts": 0, "at": None, "raised": None,
            "stoodDown": False, "everyS": 90, "why": ""})
        self.assertEqual(st, "missing")
        self.assertIn("process is young", why)
        self.assertIn("90s", why)

    def test_a_failing_tick_is_not_a_lane_that_never_ran(self):
        st, why, _asked = self._outlet({
            "ok": True, "runs": 0, "attempts": 3, "at": None, "raised": "Boom: upstream",
            "stoodDown": False, "everyS": 90, "why": ""})
        self.assertEqual(st, "missing")
        self.assertIn("RAISED", why)
        self.assertIn("FAILING", why)
        self.assertNotIn("HAS NEVER RUN", why)
        self.assertNotIn("process is young", why)

    def test_attempts_with_no_raise_and_no_run_is_a_lane_that_never_ran(self):
        st, why, _asked = self._outlet({
            "ok": True, "runs": 0, "attempts": 3, "at": None, "raised": None,
            "stoodDown": False, "everyS": 90, "why": ""})
        self.assertEqual(st, "missing")
        self.assertIn("HAS NEVER RUN", why)

    def test_a_stood_down_lane_is_not_a_dead_one(self):
        st, why, _asked = self._outlet({
            "ok": True, "runs": 0, "attempts": 0, "at": None, "raised": None,
            "stoodDown": True, "everyS": 90, "why": ""})
        self.assertEqual(st, "missing")
        self.assertIn("STOOD DOWN", why)
        self.assertNotIn("process is young", why)
        self.assertNotIn("HAS NEVER RUN", why)

    def test_a_quiet_shelf_does_not_ask_the_wire(self):
        st, why, asked = self._outlet(_NO_WIRE, waiting=False, routed=3)
        self.assertEqual(st, "ok", why)
        self.assertEqual(asked, [], "nothing is waiting, so a dead wire must not become the verdict")
        self.assertIn("closed out", why)

    def test_the_outlet_row_never_imports_the_twin(self):
        src = io.open(os.path.join(HERE, "console_doctor.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        fn = next(f for f in ast.walk(tree)
                  if isinstance(f, ast.FunctionDef)
                  and f.name == "_check_the_river_has_an_outlet")
        for n in ast.walk(fn):
            names = []
            if isinstance(n, ast.Import):
                names = [a.name for a in n.names]
            elif isinstance(n, ast.ImportFrom):
                names = [n.module or ""]
            self.assertFalse(any(a == "control_app" or a.endswith(".control_app") for a in names),
                             "the outlet row imports control_app again — a second module whose "
                             "route-lane counters stay at zero")


RED_PROOF = [
    {
        "why": "reading the twin's exact face instead of the wire restores four days of UNKNOWN "
               "about a walk that runs every 90 seconds",
        "file": "console_doctor.py",
        "find": "    st = _stw.get(\"riverWalk\")",
        "replace": "    st = {\"at\": None}",
        "matches": 1,
    },
    {
        "why": "disabling the staleness branch means a stopped watcher reads as a calm river "
               "forever — the row exists to redden on exactly that",
        "file": "console_doctor.py",
        "find": "    if isinstance(age, (int, float)) and age > 900:",
        "replace": "    if False:",
        "matches": 1,
    },
    {
        "why": "reading the twin's empty counters instead of the wire makes a lane that has run "
               "look like a process too young to have ticked",
        "file": "console_doctor.py",
        "find": "        got = riv.get(\"routeLane\") if isinstance(riv, dict) else None",
        "replace": "        got = {\"ok\": True, \"runs\": 0, \"attempts\": 0, \"stoodDown\": False, "
                   "\"raised\": None, \"everyS\": 90, \"at\": None, \"why\": \"\"} "
                   "if isinstance(riv, dict) else None",
        "matches": 1,
    },
]

if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
