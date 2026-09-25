# -*- coding: utf-8 -*-
"""REG-1284 (#165) — THE THEATRE NEVER WAITS ON THE FIXTURE SCAN.

frame_authority.test_referenced_reels() reads every test file whenever their size/mtime key changes - on a
fresh world, and on his console after EVERY ship. The theatre called it inside /api/sessions, and the page aborts
that fetch at 8 s and closes the stage ("could not reach the console"). MEASURED on a scratch console: the first
/api/sessions took 9.03 s, then 0.01 s; a stack dump two seconds in sat inside this scan. It is why v877 was red
in every Routine I run. After: 0.08 s cold, and the theatre shows its film ~1 s after the click.

  · DRIVEN (the real Handler._theatre_sessions over a fixture journal, the scan made to take 5 s): it answers
    in under a second and marks nothing - "cannot tell yet" is "mark nothing, show everything", as its own
    except path already says.
  · DRIVEN: test_referenced_reels_nowait() does not block, and returns the set once the scan has finished.
  · JOINED: the theatre asks the non-blocking accessor, never the scan itself; the console warms it at boot.
RED_PROOF below.
"""
import json
import os
import shutil
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

import frame_authority as FA  # noqa: E402


def _slow(seconds, result):
    def f(*a, **k):
        time.sleep(seconds)
        return set(result)
    return f


class TheTheatreNeverWaitsOnTheFixtureScan(unittest.TestCase):

    def setUp(self):
        self._real = FA.test_referenced_reels
        FA._FIXTURE_BG.update(thread=None, last=None)

    def tearDown(self):
        FA.test_referenced_reels = self._real
        th = FA._FIXTURE_BG.get("thread")
        if th is not None:
            th.join(timeout=10)
        FA._FIXTURE_BG.update(thread=None, last=None)

    def test_the_accessor_never_blocks_and_answers_once_ready(self):
        FA.test_referenced_reels = _slow(1.5, {"reel_s_1784984019250_95276"})
        t = time.time()
        first = FA.test_referenced_reels_nowait()
        self.assertLess(time.time() - t, 0.5, "the accessor waited on the scan")
        self.assertIsNone(first, "a set nobody has computed yet came back as an answer")
        FA._FIXTURE_BG["thread"].join(timeout=10)
        self.assertEqual(FA.test_referenced_reels_nowait(), {"reel_s_1784984019250_95276"})

    def test_the_theatre_answers_while_the_scan_runs(self):
        d = tempfile.mkdtemp(prefix="theatre-scan-")
        self.addCleanup(shutil.rmtree, d, True)
        hist = os.path.join(d, "hist")
        os.makedirs(os.path.join(hist, "reel_s_1784984019250_95276"))
        journal = os.path.join(d, "sessions.jsonl")
        with open(journal, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": 1784984019300, "frameId": "1_1784984019300", "n": 1, "names": [],
                                 "sessionId": "s_1784984019250_95276"}) + "\n")
        import control_app as ca
        import replay as rp
        keep = (ca.HIST_DIR, rp.JOURNAL)
        ca.HIST_DIR, rp.JOURNAL = hist, journal
        globals_keep = ca.__dict__.pop("_JRNL_CACHE", None)
        try:
            FA.test_referenced_reels = _slow(5.0, {"reel_s_1784984019250_95276"})
            h = ca.Handler.__new__(ca.Handler)
            t = time.time()
            out = ca.Handler._theatre_sessions(h)
            took = time.time() - t
        finally:
            ca.HIST_DIR, rp.JOURNAL = keep
            ca.__dict__.pop("_JRNL_CACHE", None)
            if globals_keep is not None:
                ca._JRNL_CACHE = globals_keep
        self.assertIsInstance(out, list, "the theatre answered an error: %r" % (out,))
        self.assertTrue(out, "premise: the fixture journal produced a session")
        self.assertLess(took, 1.0, "the theatre waited %.1fs on the fixture scan" % took)
        self.assertFalse(any(r.get("fixture") for r in out), "a set nobody has computed yet marked rows")

    def test_the_theatre_asks_the_accessor_and_the_console_warms_it(self):
        import control_app as ca
        names = ca.Handler._theatre_sessions.__code__.co_names
        self.assertIn("test_referenced_reels_nowait", names)
        self.assertNotIn("test_referenced_reels", names, "the theatre calls the blocking scan again")
        src = open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        self.assertEqual(src.count("_fa_warm.test_referenced_reels_nowait()"), 1, "the boot warm-up is gone")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-1284 - the theatre runs the 9-second fixture scan on the request path again; the first open after a ship aborts",
        "file": "control_app.py",
        "find": "                _ready = _fa.test_referenced_reels_nowait()\n",
        "replace": "                _ready = set(_fa.test_referenced_reels() or ())\n",
        "matches": 1,
    },
    {
        "why": "REG-1284 - the accessor waits for the scan instead of answering 'not yet'",
        "file": "frame_authority.py",
        "find": "        th.start()\n    last = _FIXTURE_BG[\"last\"]\n",
        "replace": "        th.start()\n    th.join()\n    last = _FIXTURE_BG[\"last\"]\n",
        "matches": 1,
    },
]
