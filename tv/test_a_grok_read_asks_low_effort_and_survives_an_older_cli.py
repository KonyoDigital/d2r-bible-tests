# -*- coding: utf-8 -*-
"""#239 (REG-2040) - A G5 GROK READ ASKS FOR LOW REASONING EFFORT, AND AN OLDER CLI THAT REFUSES THE FLAG LOSES NO READS.

MEASURED 2026-10-08 on his Mac: 3,608 of the console's 7,832 Grok reads (46%) ended "grok -p timeout 140s". The same
call on one real Chronicle page took 115.4 s and 123.4 s at the CLI's default effort (82-88% of the timeout on an idle
machine) and 26.5 s and 37.2 s with --effort low, with the same names. So the read asks for low effort - and a PC whose
Grok CLI predates the flag would refuse EVERY read, so a refusal of the flag itself is retried once without it and the
flag is not sent again for that process (published as effortRefused).
"""
import os
import sys
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

import g5_grok_eyes as G5  # noqa: E402


class _R(object):
    def __init__(self, rc, out="", err=""):
        self.returncode, self.stdout, self.stderr = rc, out, err


class AGrokReadAsksLowEffort(unittest.TestCase):

    def setUp(self):
        self._eff, self._st = G5._EFFORT, dict(G5._EFFORT_STATE)
        self.addCleanup(self._restore)
        # ⚠ HIS LIVE BUDGET AND STATS NEVER MOVE: a read's budget and stats writes go to a temp dir (G5_BUDGET_PATH /
        # G5_STATS_PATH are read at call time). Run in main by the push gate, this law would otherwise spend his budget.
        import tempfile
        self.tmp = tempfile.mkdtemp(prefix="g5-effort-law-")
        env = mock.patch.dict(os.environ, {"G5_BUDGET_PATH": os.path.join(self.tmp, "budget.json"),
                                           "G5_STATS_PATH": os.path.join(self.tmp, "stats.json")})
        env.start()
        self.addCleanup(env.stop)
        import shutil
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _restore(self):
        G5._EFFORT = self._eff
        G5._EFFORT_STATE.clear()
        G5._EFFORT_STATE.update(self._st)

    def test_the_read_asks_for_low_effort(self):
        G5._EFFORT_STATE["refused"] = None
        a = G5._vision_args("/bin/grok", "P", "/w")
        self.assertEqual(a[-2:], ["--effort", "low"], a)
        G5._EFFORT = ""
        self.assertNotIn("--effort", G5._vision_args("/bin/grok", "P", "/w"), "G5_GROK_EFFORT='' must restore the default")

    def test_an_older_cli_that_refuses_the_flag_is_retried_without_it(self):
        G5._EFFORT_STATE["refused"] = None
        seen = []

        def fake_run(args, **kw):
            seen.append(list(args))
            if "--effort" in args:
                return _R(2, "", "error: unexpected argument '--effort' found")
            return _R(0, '{"ledger":"uniques","found":["Djinn Slayer"]}', "")

        img = os.path.join(HERE, "__nope__.jpg")
        with mock.patch.object(G5.subprocess, "run", fake_run), \
                mock.patch.object(G5, "_grok_bin", lambda: "/bin/grok"), \
                mock.patch.object(G5, "_stats_flush", lambda *a, **k: None), \
                mock.patch.dict(G5._STATS, {"calls": 0, "errors": 0}), \
                mock.patch.object(G5.os.path, "isfile", lambda p: True), \
                mock.patch.object(G5.os.path, "exists", lambda p: True):
            try:
                G5.g5_vision_read(img, prompt="P {path}", force=True)
            except Exception as e:  # a refusal later in the read is not this law's subject
                pass
        self.assertGreaterEqual(len(seen), 2, "the refused flag was not retried: %r" % seen)
        self.assertIn("--effort", seen[0])
        self.assertNotIn("--effort", seen[1], "the retry still sent the flag the CLI refused")
        self.assertTrue(G5._EFFORT_STATE.get("refused"), "the refusal was not kept for the doctor")
        self.assertNotIn("--effort", G5._vision_args("/bin/grok", "P", "/w"), "the flag is sent again after a refusal")

    def test_a_failed_read_is_not_mistaken_for_a_refused_flag(self):
        self.assertFalse(G5._effort_refused(["grok", "--effort", "low"], "API error (status 402 Payment Required)"))
        self.assertFalse(G5._effort_refused(["grok"], "error: unexpected argument '--effort' found"))
        self.assertTrue(G5._effort_refused(["grok", "--effort", "low"], "error: unexpected argument '--effort' found"))


RED_PROOF = [
    {"why": "REG-2040 - the G5 read stops asking for low effort",
     "file": "g5_grok_eyes.py",
     "find": "    if _EFFORT and not _EFFORT_STATE.get(\"refused\"):\n        args += [\"--effort\", _EFFORT]\n",
     "replace": "    if False:\n        args += [\"--effort\", _EFFORT]\n",
     "matches": 1},
    {"why": "REG-2040 - an older CLI that refuses --effort loses every read again",
     "file": "g5_grok_eyes.py",
     "find": "        if r.returncode != 0 and not (r.stdout or \"\").strip() and _effort_refused(args, r.stderr):\n",
     "replace": "        if False:\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
