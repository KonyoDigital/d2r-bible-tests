# -*- coding: utf-8 -*-
"""REG-2465 (#167) — THE CONSOLE ASKS FOR NODE AT BOOT ON WINDOWS, AND A DOOR THAT CANNOT ANSWER IS UNKNOWN.

His ruling 2026-10-21 (#167): "BOTH" - the installer and the console's own dependency step fetch Node on every PC, so
the next new PC never needs SSH. Measured on Dean's PC before Node was put there by hand (2026-10-22): every node-only
law skipped (heart2 asks PATH), the eagle's 'their tooltip rows' read "node absent" for 14 days, and the intake lane
(which spawns a bare `node`) never ran - reads went to the hosted site. A self-updated console never re-runs an
installer, so the console asks for itself, like Pillow and numpy (REG-1719).

The work is tv/node_runtime.py's (ensure(blocking=False, why) -> {ok, node, fetched, onPath, why}, never raises; it
resolves, or fetches the pinned zip on a background thread, and prepends its folder to this process's PATH). This law
pins the console's half with a STAND-IN node_runtime in sys.modules - the real one is never imported or run here:
  · on Windows the boot step asks it exactly once, not blocking, and keeps its answer;
  · off Windows, and on a scratch console, it asks nothing;
  · a node_runtime that cannot be imported, or that raises, or answers no record is UNKNOWN - and boot goes on;
  · main() starts the step in its own thread.
RED_PROOF below. [[unknown-stays-unknown]] [[the-unjoined-end]]
"""
import os
import sys
import types
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import control_app as CA  # noqa: E402
import win_relaunch as WR  # noqa: E402


class _Door(unittest.TestCase):

    def setUp(self):
        self.asked = []
        stub = types.ModuleType("node_runtime")

        def ensure(blocking=True, why=""):
            self.asked.append({"blocking": blocking, "why": why})
            return {"ok": None, "node": None, "fetched": False, "onPath": False,
                    "why": "fetching the pinned Node zip in the background"}
        stub.ensure = ensure
        stub.status = lambda: {"ok": None, "node": None, "fetched": False, "onPath": False, "why": "stand-in"}
        self.stub = stub
        for p in (mock.patch.dict(sys.modules, {"node_runtime": stub}),
                  mock.patch.object(CA, "IS_WIN", True),
                  mock.patch.object(WR, "scratch_console", lambda *a, **k: False),
                  mock.patch.object(CA, "NODE_BOOT", None)):
            p.start()
            self.addCleanup(p.stop)


class TheConsoleAsksForNodeOnWindows(_Door):

    def test_on_windows_it_asks_once_without_waiting_and_keeps_the_answer(self):
        rec = CA._ensure_node_at_boot()
        self.assertEqual(self.asked, [{"blocking": False, "why": "console boot"}],
                         "the boot step did not ask node_runtime exactly once, off the boot thread")
        self.assertIs(CA.NODE_BOOT, rec)
        self.assertEqual((rec["ok"], rec["fetched"], rec["onPath"]), (None, False, False))
        self.assertIn("fetching the pinned Node zip", rec["why"])

    def test_off_windows_it_asks_nothing(self):
        with mock.patch.object(CA, "IS_WIN", False):
            self.assertIsNone(CA._ensure_node_at_boot())
        self.assertEqual(self.asked, [], "a Mac console asked to fetch Node")

    def test_a_scratch_console_asks_nothing(self):
        with mock.patch.object(WR, "scratch_console", lambda *a, **k: True):
            self.assertIsNone(CA._ensure_node_at_boot())
        self.assertEqual(self.asked, [], "a scratch console would fetch Node into a real home")


class ADoorThatCannotAnswerIsUnknown(_Door):

    def test_an_import_failure_is_unknown_and_boot_goes_on(self):
        with mock.patch.dict(sys.modules, {"node_runtime": None}):
            rec = CA._ensure_node_at_boot()
        self.assertIsNone(rec["ok"], "an unimportable node_runtime was read as an answer")
        self.assertTrue(rec["why"].startswith("UNKNOWN"), rec["why"])

    def test_a_raise_is_unknown_and_boot_goes_on(self):
        def boom(blocking=True, why=""):
            raise OSError("the disk said no")
        self.stub.ensure = boom
        rec = CA._ensure_node_at_boot()
        self.assertIsNone(rec["ok"])
        self.assertIn("UNKNOWN", rec["why"])
        self.assertIn("the disk said no", rec["why"])

    def test_an_answer_that_is_not_a_record_is_unknown(self):
        self.stub.ensure = lambda blocking=True, why="": True
        rec = CA._ensure_node_at_boot()
        self.assertIsNone(rec["ok"], "a bare True was read as 'node is here'")
        self.assertIn("UNKNOWN", rec["why"])


class BootStartsTheStep(unittest.TestCase):

    def test_main_starts_the_node_step(self):
        self.assertIn("_ensure_node_at_boot", CA.main.__code__.co_names,
                      "main() never starts the boot node step - a self-updated Windows PC never gets Node")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-2465 - the boot step never asks node_runtime: a self-updated Windows PC never gets Node, and the "
               "intake lane and every node-only law stay dark there",
        "file": "control_app.py",
        "find": "        got = _nr.ensure(blocking=False, why=\"console boot\")\n",
        "replace": "        got = {}\n",
        "matches": 1,
    },
    {
        "why": "REG-2465 - main() stops starting the node step",
        "file": "control_app.py",
        "find": "    threading.Thread(target=_ensure_node_at_boot, daemon=True, name=\"tvd-node\").start()     # REG-2465\n",
        "replace": "",
        "matches": 1,
    },
]
