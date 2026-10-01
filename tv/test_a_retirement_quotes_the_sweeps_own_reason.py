# -*- coding: utf-8 -*-
"""REG-1649 — WHEN THE VAULT LANE RETIRES A REEL, IT SAYS WHAT THE SWEEP ITSELF FOUND.

The lane retires a reel after two attempts that leave it still owed, and quotes `lastWhy[reel]` - which was
written only when vault_sweep_start refused SYNCHRONOUSLY. A sweep that started, read every panel and then could
not seal said why on stdout and in _VAULT_JOB, and the lane never heard it. MEASURED on his console 2026-10-01:
both reels retired at 03:12 with "2 attempt(s) ran and this reel is STILL owed afterwards — and no attempt left a
reason, so WHY is UNKNOWN, not diagnosed", directly under four lines reading "read 28 panel(s) but the seal
cannot be definitive: 28 frame(s) were READ but only 0 were cross-checked" (the cause: REG-1648).

  · DRIVEN: a run aimed at one reel that ends without a seal writes ITS reason to lastWhy[reel] and saves it - the
    raised error first, then the INCOMPLETE reason, then the not-definitive one; and a run with no reason at all
    says THAT in words rather than leaving the field empty.
  · DRIVEN: a reel the run sealed, and a sweep of everything (no reel), write nothing.
  · DRIVEN: the real _vault_sweep_run notes its outcome on EVERY exit path - including a raise.
  · DRIVEN: a start clears the last run's reasons, so a clean run never inherits an old one.
  · DRIVEN end to end: the retirement then quotes the sweep's sentence, and "WHY is UNKNOWN" is not said.
RED_PROOF below. [[the-unjoined-end]] [[unknown-stays-unknown]]
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

_WORLD = tempfile.mkdtemp(prefix="retire_quotes_")
os.environ["TV_HIST"] = _WORLD
os.environ["TV_SESSIONS"] = os.path.join(_WORLD, "sessions.jsonl")

import control_app as ca  # noqa: E402

REEL = os.path.join(_WORLD, "reel_s_1700000000000_00077")
RID = os.path.basename(REEL)
NOT_X = "28 of 28 read frame(s) were never cross-checked"


class _Lane(unittest.TestCase):

    def setUp(self):
        self.assertTrue(os.path.realpath(ca._vault_autoread_path()).startswith(os.path.realpath(_WORLD)),
                        "PREMISE: the lane's store is not in this law's world")
        self.job = dict(ca._VAULT_JOB)
        self.mem = json.loads(json.dumps({k: ca._VAULT_AUTOREAD.get(k) for k in ("retired", "tries", "lastWhy")}))
        self.load = ca._vault_autoread_load
        ca._vault_autoread_load = lambda: True
        ca._VAULT_AUTOREAD_STORE.update({"tried": True, "readable": True})
        ca._VAULT_AUTOREAD["lastWhy"] = {}

        def _restore():
            ca._VAULT_JOB.clear()
            ca._VAULT_JOB.update(self.job)
            for k, v in self.mem.items():
                ca._VAULT_AUTOREAD[k] = v if v is not None else {}
            ca._vault_autoread_load = self.load
        self.addCleanup(_restore)

    def _job(self, **kw):
        for k in ("error", "incompleteWhy", "notDefinitiveWhy"):
            ca._VAULT_JOB[k] = kw.get(k)

    def _on_disk(self):
        with open(ca._vault_autoread_path(), encoding="utf-8") as fh:
            return (json.load(fh).get("lastWhy") or {}).get(RID)


class TheRunThatKnowsWritesIt(_Lane):

    def test_an_incomplete_run_leaves_its_reason_for_that_reel(self):
        self._job(incompleteWhy=NOT_X)
        self.assertEqual(ca._vault_lane_note_outcome(REEL, swept={}), NOT_X)
        self.assertEqual(ca._VAULT_AUTOREAD["lastWhy"].get(RID), NOT_X)
        self.assertEqual(self._on_disk(), NOT_X, "the reason was never saved - a relaunch would lose it")

    def test_the_most_specific_reason_wins(self):
        self._job(error="boom", incompleteWhy=NOT_X, notDefinitiveWhy="nd")
        self.assertIn("raised: boom", ca._vault_lane_note_outcome(REEL, swept={}))
        self._job(incompleteWhy=NOT_X, notDefinitiveWhy="nd")
        self.assertEqual(ca._vault_lane_note_outcome(REEL, swept={}), NOT_X)
        self._job(notDefinitiveWhy="nd")
        self.assertEqual(ca._vault_lane_note_outcome(REEL, swept={}), "nd")

    def test_no_reason_at_all_is_said_in_words(self):
        self._job()
        why = ca._vault_lane_note_outcome(REEL, swept={})
        self.assertTrue(why and "gave no reason" in why, "an empty field reads as UNKNOWN at retirement: %r" % why)

    def test_a_sealed_reel_and_a_sweep_of_everything_write_nothing(self):
        self._job(incompleteWhy=NOT_X)
        self.assertIsNone(ca._vault_lane_note_outcome(REEL, swept={RID.replace("reel_", "", 1): {"rows": 3}}))
        self.assertIsNone(ca._vault_lane_note_outcome(None, swept={}))
        self.assertNotIn(RID, ca._VAULT_AUTOREAD["lastWhy"])


class EveryExitNotes(_Lane):

    def test_a_run_that_raises_still_notes_why(self):
        real = ca._vault_retro

        def _boom():
            raise RuntimeError("the reader would not import")
        ca._vault_retro = _boom
        try:
            ca._vault_sweep_run(None, 1, False, REEL)
        finally:
            ca._vault_retro = real
        got = ca._VAULT_AUTOREAD["lastWhy"].get(RID)
        self.assertTrue(got and "would not import" in got, "a sweep that raised left the lane no reason: %r" % got)

    def test_a_start_clears_the_last_runs_reasons(self):
        lanes, run = ca._chron_lanes, ca._vault_sweep_run
        ca._chron_lanes = lambda *a, **k: ["claude"]
        ca._vault_sweep_run = lambda *a, **k: None
        ca._VAULT_JOB.update({"running": False, "notDefinitiveWhy": "an old run's reason", "incompleteWhy": "old"})
        try:
            r = ca.vault_sweep_start(limit=1)
            self.assertTrue(r.get("ok"), "PREMISE: the start did not start: %r" % r)
            self.assertIsNone(ca._VAULT_JOB.get("notDefinitiveWhy"), "a new run inherited the last run's reason")
            self.assertIsNone(ca._VAULT_JOB.get("incompleteWhy"))
        finally:
            ca._chron_lanes, ca._vault_sweep_run = lanes, run
            ca._VAULT_JOB["running"] = False


class TheRetirementQuotesIt(_Lane):

    def test_the_retirement_says_what_the_sweep_found(self):
        import reel_retention as RR
        saved = {"owed": ca._vault_owed_reels, "grow": ca._reel_is_growing, "state": ca.vault_sweep_state,
                 "pnb": RR._panels_never_banked}
        ca._vault_owed_reels = lambda *a, **k: [REEL]
        ca._reel_is_growing = lambda p: False
        ca.vault_sweep_state = lambda: {"running": False}
        RR._panels_never_banked = lambda *a, **k: False       # banked: this reel may be retired
        ca._VAULT_AUTOREAD.setdefault("retired", {}).pop(RID, None)
        ca._VAULT_AUTOREAD.setdefault("tries", {})[RID] = ca._VAULT_AUTOREAD_MAX_TRIES
        self._job(incompleteWhy=NOT_X)
        ca._vault_lane_note_outcome(REEL, swept={})           # the second attempt's run ended like his did
        try:
            r = ca.vault_autoreel_tick()
        finally:
            ca._vault_owed_reels, ca._reel_is_growing = saved["owed"], saved["grow"]
            ca.vault_sweep_state, RR._panels_never_banked = saved["state"], saved["pnb"]
            ca._VAULT_AUTOREAD["retired"].pop(RID, None)
            ca._VAULT_AUTOREAD["tries"].pop(RID, None)
        self.assertEqual(r.get("retired"), RID, "PREMISE: the tick did not retire: %r" % r)
        self.assertIn(NOT_X, r.get("why", ""), "the retirement did not quote the sweep: %r" % r.get("why"))
        self.assertNotIn("WHY is UNKNOWN", r.get("why", ""))


def tearDownModule():
    shutil.rmtree(_WORLD, ignore_errors=True)


RED_PROOF = [
    {"why": "REG-1649 - the run stops telling the lane: every retirement says WHY is UNKNOWN again",
     "file": "control_app.py",
     "find": "    finally:\n        _vault_lane_note_outcome(reel_dir)     # REG-1649\n",
     "replace": "    finally:\n        pass\n",
     "matches": 1},
    {"why": "REG-1649 - a start keeps the last run's reason: a clean run can be blamed for an old one",
     "file": "control_app.py",
     "find": "                           \"notDefinitiveWhy\": None, \"incompleteWhy\": None})\n",
     "replace": "                           })\n",
     "matches": 1},
    {"why": "REG-1649 - a reel the run sealed is still handed a failure reason",
     "file": "control_app.py",
     "find": "            return None                  # sealed by this run (or before it) — nothing is owed\n",
     "replace": "            pass\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
