# -*- coding: utf-8 -*-
"""#229 — A WINDOWS CONSOLE ASKS BEFORE IT STARTS ITSELF AT SIGN-IN.

MEASURED 2026-09-20 over SSH on the ALT: zero scheduled tasks, zero startup entries - the console survives
its own relaunch but not a reboot. Starting it at sign-in is a STANDING CHANGE ON HIS PC, so it is his
call: the console asks in his mailbox, and only a "yes" hands the setup to Claude.

  · DRIVEN (stubbed schtasks + a temp Startup folder): no task and no shortcut -> MISSING with one
    well-formed "decide" ask whose yes is a HANDOFF; a task -> OK; a Startup shortcut -> OK; the query
    failing -> UNKNOWN, never "not set up"; not Windows -> UNMEASURED and no question.
  · JOINED: the row is in CHECKS, WATCHES, ASKS and corroborate, and attach_asks puts the ask on the row.
RED_PROOF below.
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import console_doctor as cd  # noqa: E402

NAME = "this console starts at sign-in"


class _R(object):
    def __init__(self, rc):
        self.returncode, self.stdout, self.stderr = rc, "", ""


class AWindowsConsoleAsksBeforeItStartsAtSignIn(unittest.TestCase):

    def setUp(self):
        self.startup = tempfile.mkdtemp(prefix="signin-law-")
        self.calls = []

    def tearDown(self):
        shutil.rmtree(self.startup, ignore_errors=True)

    def _run(self, rc):
        def run(argv, **kw):
            self.calls.append(argv)
            return _R(rc)
        return run

    def test_nothing_set_up_is_missing_and_asks(self):
        r = cd._sign_in_start(run=self._run(1), startup_dir=self.startup, is_win=True)
        self.assertEqual(r["state"], cd.MISSING)
        self.assertEqual(self.calls, [["schtasks", "/Query", "/TN", cd.SIGN_IN_TASK]])
        asks = cd._ask_sign_in_start({"check": NAME, "state": r["state"], "why": r["why"]})
        self.assertEqual(len(asks), 1)
        self.assertEqual(cd.ask_problems(asks[0]), [], "malformed ask: %r" % asks[0])
        self.assertEqual(asks[0]["kind"], "decide")
        eff = dict((a["key"], a["effect"]) for a in asks[0]["answers"])
        self.assertEqual(eff.get("yes"), "handoff", "a yes must hand the setup to Claude, not claim it is done")
        self.assertEqual(eff.get("no"), "ruled", "a no is his ruling and must stand")

    def test_a_task_is_ok_and_asks_nothing(self):
        r = cd._sign_in_start(run=self._run(0), startup_dir=self.startup, is_win=True)
        self.assertEqual(r["state"], cd.OK)
        self.assertEqual(cd._ask_sign_in_start({"state": r["state"]}), [])

    def test_a_startup_shortcut_is_ok_without_asking_windows(self):
        open(os.path.join(self.startup, "TV DIABLO.lnk"), "w").close()
        r = cd._sign_in_start(run=self._run(1), startup_dir=self.startup, is_win=True)
        self.assertEqual(r["state"], cd.OK)
        self.assertEqual(self.calls, [])

    def test_a_failed_query_is_unknown(self):
        def boom(argv, **kw):
            raise OSError("schtasks missing")
        r = cd._sign_in_start(run=boom, startup_dir=self.startup, is_win=True)
        self.assertEqual(r["state"], cd.UNKNOWN, "a query that could not run read as 'not set up'")

    def test_not_windows_asks_nothing(self):
        r = cd._sign_in_start(run=self._run(1), startup_dir=self.startup, is_win=False)
        self.assertEqual(r["state"], cd.UNMEASURED)
        self.assertEqual(self.calls, [])

    def test_the_row_is_joined_everywhere_it_must_be(self):
        import corroborate as co
        self.assertIn(NAME, [c[0] for c in cd.CHECKS])
        self.assertIn(NAME, cd.WATCHES)
        self.assertIs(cd.ASKS.get(NAME), cd._ask_sign_in_start)
        self.assertIn(NAME, co.NO_JOINT_YET)
        real = cd._sign_in_start
        cd._sign_in_start = lambda *a, **k: {"state": cd.MISSING, "how": None, "why": "nothing starts it"}
        try:
            st, why = cd._check_this_console_starts_at_sign_in()
            rows = cd.attach_asks([{"check": NAME, "state": st, "why": why}])
        finally:
            cd._sign_in_start = real
        self.assertTrue(rows[0].get("asks"), "attach_asks did not put the question on the row")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#229 - a failed schtasks query reads as 'not set up' and asks him about a task that may exist",
        "file": "console_doctor.py",
        "find": "        return {\"state\": UNKNOWN, \"how\": None,\n                \"why\": \"could not ask Windows for its scheduled tasks",
        "replace": "        return {\"state\": MISSING, \"how\": None,\n                \"why\": \"could not ask Windows for its scheduled tasks",
        "matches": 1,
    },
    {
        "why": "#229 - a yes claims the setup is done instead of handing it to Claude",
        "file": "console_doctor.py",
        "find": "            {\"key\": \"yes\", \"label\": \"Yes, set it up\", \"effect\": \"handoff\"},\n",
        "replace": "            {\"key\": \"yes\", \"label\": \"Yes, set it up\", \"effect\": \"ruled\"},\n",
        "matches": 1,
    },
]
