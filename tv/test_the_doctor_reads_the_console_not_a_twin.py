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
]

if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
