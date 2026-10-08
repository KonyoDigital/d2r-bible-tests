# -*- coding: utf-8 -*-
"""#239 (REG-2039) - A WAITING BUILD STOPS THE CHRONICLE SWEEP AT ITS NEXT BANKED PAGE; THE REEL RESUMES WHERE IT WAS.

MEASURED 2026-10-07 on his Mac's fleet row: "may false - a chronicle sweep is reading footage", the sweep at '5 of 293
frames - about 804 min left' (Grok reads timing out at 140 s). Every new build waited up to ~13 h, because the sweep
lock is released only when the whole run ends.

  * only the callers that relaunch next ask (the drift loop with a build waiting) - and only when the blocker IS the
    sweep and a chronicle sweep is running in this process; a status read never stops one;
  * asked, the sweep banks the page it just read and every page since its last checkpoint, records the frames it read
    per reel (with the prompt version), seals nothing, and ends - the finally releases the lock;
  * the reel's next pass is handed those frames and does not pay for them again (the engine counts them as
    resumedFrames); a record from another prompt version is ignored (a new prompt reopening a reel is deliberate);
  * for _CHRON_STOP_HOLD_S after a stop, no new sweep starts, so the relaunch is not held again by the next one.
Nothing here reads his reels or writes his stores: every store the runner touches is a temp file or a stub.
"""
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

import chronicle_retro as cr  # noqa: E402
import control_app as ca  # noqa: E402
import tv_diablo as tv  # noqa: E402

REEL = "reel_s_law_resume"   # synthetic - a law never names one of his real reels (test_no_pinned_footage)


class TheEngineSkipsWhatAStoppedPassBanked(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="resume-engine-")
        self.addCleanup(shutil.rmtree, self.d, True)
        rd = os.path.join(self.d, REEL)
        os.makedirs(rd)
        with open(os.path.join(rd, "index.json"), "w", encoding="utf-8") as fh:
            json.dump({"sessionId": REEL[5:], "frames": [{"f": "f%d.jpg" % k, "ts": k} for k in range(6)]}, fh)

    def _sweep(self, skip_read=None):
        read = []
        res = cr.sweep_hist(self.d, lambda p: "chronicle-uniques",
                            lambda p, k: read.append(os.path.basename(p)) or {"ledger": "uniques", "found": []},
                            sig_of=lambda n: (30,) * 16, skip_read=skip_read)
        return read, res["reels"][0]

    def test_frames_a_stopped_pass_read_are_not_paid_for_again(self):
        first, st1 = self._sweep()
        self.assertTrue(first, "premise: the fixture reel has pages to read")
        self.assertEqual(st1.get("resumedFrames"), 0)
        again, st2 = self._sweep(skip_read={REEL: set(first)})
        self.assertEqual(again, [], "a frame the stopped pass banked was paid for again")
        self.assertEqual(st2.get("resumedFrames"), len(first), st2)


class AWaitingBuildStopsTheSweep(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="resume-console-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        rd = os.path.join(self.tmp, "hist", REEL)
        os.makedirs(rd)
        with open(os.path.join(rd, "index.json"), "w", encoding="utf-8") as fh:
            json.dump({"sessionId": REEL[5:], "frames": [{"f": "f1.jpg", "ts": 1}]}, fh)
        self.hist = os.path.dirname(rd)
        self._path, self._auto = ca._CHRON_AUTOREAD_PATH, dict(ca._CHRON_AUTOREAD)
        self._job, self._hold = dict(ca._CHRON_JOB), dict(ca._CHRON_STOP_FOR_RELAUNCH)
        ca._CHRON_AUTOREAD_PATH = os.path.join(self.tmp, "chron_autoread.json")
        ca._CHRON_AUTOREAD["resume"] = {}
        self.merged = []
        self.patches = [
            mock.patch.dict(os.environ, {"TV_SWEEP_LOCK": os.path.join(self.tmp, ".sweep.lock"),
                                         "TV_HIST": self.hist}),
            mock.patch.object(ca, "_chron_reads_load", lambda *a, **k: {}),
            mock.patch.object(ca, "_chron_read_capped", lambda *a, **k: None),
            mock.patch.object(ca, "_chron_read_bump_if_read", lambda *a, **k: True),
            mock.patch.object(ca, "_chron_evidence_merge", lambda prop: self.merged.append(prop)),
            mock.patch.object(ca, "_chron_swept_load", lambda *a, **k: {}),
            mock.patch.object(ca, "_chron_swept_save", lambda *a, **k: None),
            mock.patch.object(ca, "_chron_known_from_journal", lambda *a, **k: {}),
            mock.patch.object(ca, "_chron_result_save", lambda *a, **k: None),
            mock.patch.object(tv, "_is_throttled", lambda *a, **k: False),
            mock.patch.object(tv, "_sub_budget_check", lambda *a, **k: False),
            mock.patch.object(tv, "claude_chronicle_read", lambda p, k: {"ledger": "uniques", "found": ["Windforce"]}),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self._restore)

    def _restore(self):
        ca._CHRON_AUTOREAD_PATH = self._path
        ca._CHRON_AUTOREAD.clear()
        ca._CHRON_AUTOREAD.update(self._auto)
        ca._CHRON_JOB.clear()
        ca._CHRON_JOB.update(self._job)
        ca._CHRON_STOP_FOR_RELAUNCH.clear()
        ca._CHRON_STOP_FOR_RELAUNCH.update(self._hold)

    def test_only_a_waiting_build_held_by_a_running_sweep_asks(self):
        ca._CHRON_JOB.update({"running": True, "stopAsk": None})
        self.assertFalse(ca._chron_ask_stop_for_relaunch({"blocker": "mid-edit"}))
        self.assertIsNone(ca._CHRON_JOB.get("stopAsk"), "a relaunch held by something else stopped the sweep")
        ca._CHRON_JOB.update({"running": False})
        self.assertFalse(ca._chron_ask_stop_for_relaunch({"blocker": "work"}))
        ca._CHRON_JOB.update({"running": True})
        self.assertTrue(ca._chron_ask_stop_for_relaunch({"blocker": "work"}))
        self.assertTrue(ca._CHRON_JOB.get("stopAsk"))

    def test_asked_the_sweep_banks_records_and_ends_without_sealing(self):
        seen = {}

        def fake_sweep(hist, classify, read_page, **kw):
            seen["skip"] = kw.get("skip_read")
            read_page(os.path.join(hist, REEL, "f1.jpg"), "chronicle-uniques")
            raise AssertionError("the run went on after the stop was asked")

        ca._CHRON_JOB.update({"running": True, "stopAsk": 1, "lanes": ["claude"]})
        with mock.patch.object(cr, "sweep_hist", fake_sweep):
            ca._chron_sweep_run(self.hist, None)
        self.assertEqual(ca._CHRON_JOB.get("phase"), "stopped", ca._CHRON_JOB.get("error") or ca._CHRON_JOB)
        self.assertFalse(ca._CHRON_JOB.get("running"))
        self.assertEqual(len(self.merged), 1, "the page read before the stop was not banked")
        with open(ca._CHRON_AUTOREAD_PATH, encoding="utf-8") as fh:
            rec = (json.load(fh).get("resume") or {}).get(REEL)
        self.assertEqual((rec or {}).get("frames"), ["f1.jpg"], "the stop did not record what it read: %r" % rec)
        self.assertEqual(rec.get("promptVer"), tv.PROMPT_VER)

    def test_the_next_pass_is_handed_what_the_stopped_one_read(self):
        ca._CHRON_AUTOREAD["resume"] = {REEL: {"frames": ["f1.jpg"], "promptVer": tv.PROMPT_VER, "ts": 1},
                                        "reel_s_other": {"frames": ["f9.jpg"], "promptVer": "vOLD", "ts": 1}}
        seen = {}

        def fake_sweep(hist, classify, read_page, **kw):
            seen["skip"] = kw.get("skip_read")
            raise RuntimeError("law: stop here")

        ca._CHRON_JOB.update({"running": True, "stopAsk": None, "lanes": ["claude"]})
        with mock.patch.object(cr, "sweep_hist", fake_sweep):
            ca._chron_sweep_run(self.hist, None)
        self.assertEqual(seen.get("skip"), {REEL: {"f1.jpg"}},
                         "the next pass was not handed the banked frames (or took another prompt's)")

    def test_no_new_sweep_starts_while_the_relaunch_is_pending(self):
        ca._CHRON_STOP_FOR_RELAUNCH["ts"] = __import__("time").time()
        with mock.patch.object(ca.threading, "Thread", side_effect=AssertionError("a sweep was started")):
            out = ca.chronicle_sweep_start(self.hist)
        self.assertFalse(out.get("ok"), out)
        self.assertIn("waiting build could relaunch", str(out.get("why")), out)


RED_PROOF = [
    {"why": "REG-2039 - a frame a stopped pass banked is paid for again",
     "file": "chronicle_retro.py",
     "find": "                if skip_read and name in skip_read:\n",
     "replace": "                if False:\n",
     "matches": 1},
    {"why": "REG-2039 - an asked sweep reads on to the end of its run",
     "file": "control_app.py",
     "find": "            if _CHRON_JOB.get(\"stopAsk\"):\n                # REG-2039 - A WAITING BUILD ASKED.",
     "replace": "            if False:\n                # REG-2039 - A WAITING BUILD ASKED.",
     "matches": 1},
    {"why": "REG-2039 - the next sweep starts the moment one stopped for a relaunch",
     "file": "control_app.py",
     "find": "        if _sa and (time.time() - _sa) < _CHRON_STOP_HOLD_S:\n",
     "replace": "        if False:\n",
     "matches": 1},
    {"why": "REG-2039 - a status read stops the sweep",
     "file": "control_app.py",
     "find": "        if (detail or {}).get(\"blocker\") != \"work\":\n            return False\n",
     "replace": "        if False:\n            return False\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
