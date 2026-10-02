# -*- coding: utf-8 -*-
"""REG-1747 — A REEL THE TRIAGE PROVED EMPTY OWES THE CHRONICLE NO PAID READ.

MEASURED on the ALT, 2026-10-02: the chronicle autoread paid Grok to classify its reel …14824 three times
- two attempts retired as "the sweep started but never wrote a result", a third 18 minutes in - while retro_triage
had walked all 423 of its frames ("full": true) and found ZERO panels, and the river held it at TOMBSTONE. His words:
"these frames are the ones filtered already by design ... relevant frames stay and get read", and "make sure not to
double build here.. they should just be wired properly together". `_chron_reel_owes_a_read` - the one rule behind
the autoread, its offer list and the "waiting on a sweep" count - never asked the triage.

  · DRIVEN: a FULL triage with no panel -> owes nothing; the same reel with panels, a SAMPLED pass, a reel the store
    does not hold, and no store at all -> still owes (UNKNOWN keeps the read, never skips it).
  · DRIVEN: the count the panel shows drops exactly the proven-empty reel.
  · WIRED, NOT REBUILT: the rule calls reel_retention._proven_empty - retention's own reading of the triage - so the
    two can never disagree about one reel; the law asserts the call by the compiler, not by grep.
RED_PROOF below. [[the-unjoined-end]] [[copy-drift]] [[unknown-stays-unknown]]
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

EMPTY = "reel_s_1500000000001_14824"      # synthetic (2017 epoch) - the ALT's reel by its shape only
FULL_OF_PANELS = "reel_s_1500000000002_00001"
SAMPLED = "reel_s_1500000000003_00002"
UNSURVEYED = "reel_s_1500000000004_00003"


def _ca():
    import control_app as ca
    return ca


class _World(unittest.TestCase):

    def setUp(self):
        self.hist = tempfile.mkdtemp(prefix="triage_join_")
        self.addCleanup(shutil.rmtree, self.hist, True)
        env = mock.patch.dict(os.environ, {"TV_HIST": self.hist})
        env.start()
        self.addCleanup(env.stop)

    def store(self, rows):
        with io.open(os.path.join(self.hist, "retro_triage.json"), "w", encoding="utf-8") as fh:
            json.dump(rows, fh)

    def owes(self, rid):
        return _ca()._chron_reel_owes_a_read(rid, {})        # never swept: owes, unless the triage says otherwise


def _row(panels, full=True):
    return {"panels": panels, "frames": 423, "full": full, "kinds": {}}


class TheTriageDecides(_World):

    def test_baseline_with_no_store_a_never_swept_reel_owes(self):
        self.assertTrue(self.owes(EMPTY), "PREMISE: with no triage at all a never-swept reel must owe a read")

    def test_a_full_survey_with_no_panel_owes_nothing(self):
        self.store({EMPTY: _row(0)})
        self.assertFalse(self.owes(EMPTY), "a reel the triage walked in full and found no panel on still owes a "
                                           "paid chronicle read - the ALT's 423-frame reel, read three times")

    def test_a_reel_with_panels_still_owes(self):
        self.store({FULL_OF_PANELS: _row(5)})
        self.assertTrue(self.owes(FULL_OF_PANELS))

    def test_a_sampled_pass_proves_nothing(self):
        self.store({SAMPLED: _row(0, full=False)})
        self.assertTrue(self.owes(SAMPLED), "a SAMPLED triage was taken as proof the reel is empty")

    def test_a_reel_the_store_does_not_hold_still_owes(self):
        self.store({EMPTY: _row(0)})
        self.assertTrue(self.owes(UNSURVEYED), "a reel nobody surveyed was skipped as if it had been")

    def test_the_count_he_sees_drops_only_the_proven_empty_reel(self):
        self.store({EMPTY: _row(0), FULL_OF_PANELS: _row(5)})
        ca = _ca()
        dirs = [os.path.join(self.hist, n) for n in (EMPTY, FULL_OF_PANELS, UNSURVEYED)]
        import chronicle_retro
        with mock.patch.object(chronicle_retro, "reel_dirs", lambda *a, **k: list(dirs)), \
                mock.patch.object(ca, "_chron_swept_mem", lambda: {}):
            n = ca._chron_owed_count(self.hist)
        self.assertEqual(n, 2, "the 'waiting on a sweep' count is %r - it should hold the reel with panels and the "
                               "unsurveyed one, never the reel the triage proved empty" % (n,))
        self.assertEqual(ca._TRIAGE_RULED_EMPTY.get("chronicle"), 1,
                         "REG-1751: the chronicle lane skipped 1 triage-proven reel and its count says %r - the heart "
                         "cannot see the join" % (ca._TRIAGE_RULED_EMPTY.get("chronicle"),))


class ItIsWiredNotRebuilt(unittest.TestCase):

    def test_the_rule_calls_retentions_reading(self):
        fn = _ca()._chron_reel_owes_a_read
        self.assertIn("_proven_empty", fn.__code__.co_names,
                      "the owes-a-read rule does not call reel_retention._proven_empty - a second copy of the "
                      "triage rule would drift from retention's")


RED_PROOF = [
    {"why": "REG-1747 - the owes-a-read rule stops asking the triage: a proven-empty reel is paid for again",
     "file": "control_app.py",
     "find": "        if _rr._proven_empty(str(rid)):\n            return False\n",
     "replace": "        if False:\n            return False\n",
     "matches": 1},
    {"why": "REG-1747 - the triage answer is taken as 'nothing owed' for every reel it holds",
     "file": "reel_retention.py",
     "find": "        return bool(rec.get(\"full\")) and int(rec.get(\"panels\") or 0) == 0\n",
     "replace": "        return True\n",
     "matches": 1},
    {"why": "REG-1751 - the chronicle lane stops counting the reels the triage ruled empty",
     "file": "control_app.py",
     "find": "        _TRIAGE_RULED_EMPTY[\"chronicle\"] = sum(1 for d in _dirs if _rr._proven_empty(os.path.basename(str(d))))\n",
     "replace": "        _TRIAGE_RULED_EMPTY[\"chronicle\"] = 0\n",
     "matches": 1}
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
