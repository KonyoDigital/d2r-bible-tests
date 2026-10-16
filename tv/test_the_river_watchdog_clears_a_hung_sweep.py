# -*- coding: utf-8 -*-
"""RIVER WATCHDOG — a vault sweep whose guard a HANG left set is cleared, and the reel quarantined.

THE BUG (live 2026-10-17 on his console: vaultAutoread owed=14, lastTick {kind:busy, why:"a vault sweep is
already running"}): _vault_sweep_run releases _VAULT_JOB["running"] only when the synchronous _vr.sweep()
RETURNS or RAISES — its `finally` does NOT clear it. A sweep that HANGS in its measure phase (a frame that
never settles, a hung tooltip locate, a read that never returns) leaves running=True forever, so every 45s
tick refuses "a sweep is already running" and the river stalls on EVERY PC (Mac, GrokBot, ALT). Relaunch
clears it but it RECURS.

_vault_sweep_hang_check() runs on the 10s rescue tick (the only in-process place that can see
_VAULT_JOB["running"]). This law drives the SHIPPED watchdog:
  · a sweep that makes NO forward progress past _VAULT_SWEEP_HANG_DEADLINE_S is cleared (running False,
    phase 'hung') and its reel lands in _VAULT_AUTOREAD['retired'] (hung=True) so the lane reads the rest.
  · a sweep that is making progress is LEFT RUNNING (any change to the progress snapshot resets the clock).
  · a sweep that is not running is a no-op.
A missing `running=False` would leave the stall this exists to end — RED_PROOF below. [[heart-first]]
[[the-unjoined-end]] [[unknown-stays-unknown]]
"""
import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _enable  # noqa: E402
_enable()
import control_app as ca  # noqa: E402

REEL = "/reels/reel_s_17913672099321"
RID = "reel_s_17913672099321"


def _set_sweep(running, stalled_s):
    now = time.time()
    ca._VAULT_SWEEP_QUARANTINE.clear()
    ca._VAULT_JOB.clear()
    ca._VAULT_JOB.update({"running": running, "startedTs": int((now - stalled_s) * 1000),
                          "phase": "reading", "runReelsDone": 0, "classified": 0, "pagesRead": 0,
                          "runReel": "Bad Reel", "runReelDir": REEL})
    sig = (ca._VAULT_JOB["startedTs"], "reading", 0, 0, 0, "Bad Reel")
    ca._VAULT_SWEEP_PROGRESS.clear()
    ca._VAULT_SWEEP_PROGRESS.update({"sig": sig, "ts": now - stalled_s})


class TestRiverWatchdogClearsAHungSweep(unittest.TestCase):
    def test_a_hung_sweep_past_the_deadline_is_cleared_and_its_reel_quarantined(self):
        _set_sweep(running=True, stalled_s=ca._VAULT_SWEEP_HANG_DEADLINE_S + 30)
        acted = ca._vault_sweep_hang_check()
        self.assertTrue(acted, "the watchdog did not act on a sweep stalled past the deadline")
        self.assertFalse(ca._VAULT_JOB.get("running"), "a hung sweep's guard was NOT cleared — the river stays stalled")
        self.assertEqual(ca._VAULT_JOB.get("phase"), "hung")
        self.assertIn(RID, ca._VAULT_SWEEP_QUARANTINE, "the hung reel was not quarantined, so the next sweep re-hangs on it")

    def test_a_sweep_making_progress_is_left_running(self):
        _set_sweep(running=True, stalled_s=1)                    # fresh — not past the deadline
        self.assertFalse(ca._vault_sweep_hang_check(), "the watchdog cleared a sweep that is making progress")
        self.assertTrue(ca._VAULT_JOB.get("running"), "a live, progressing sweep was wrongly cleared")

    def test_a_new_progress_snapshot_resets_the_clock(self):
        _set_sweep(running=True, stalled_s=ca._VAULT_SWEEP_HANG_DEADLINE_S + 30)
        ca._VAULT_JOB["classified"] = 5                          # forward progress since the snapshot
        self.assertFalse(ca._vault_sweep_hang_check(), "a sweep that just advanced must not be cleared")
        self.assertTrue(ca._VAULT_JOB.get("running"))

    def test_not_running_is_a_no_op(self):
        _set_sweep(running=False, stalled_s=ca._VAULT_SWEEP_HANG_DEADLINE_S + 30)
        self.assertFalse(ca._vault_sweep_hang_check())


RED_PROOF = [
    {
        "why": "river watchdog - if the guard clear does not set running False, a hung sweep stays 'running' "
               "forever and every tick refuses busy (the river stall this watchdog exists to end)",
        "file": "control_app.py",
        "find": '                _VAULT_JOB.update({"running": False, "phase": "hung",',
        "replace": '                _VAULT_JOB.update({"running": True, "phase": "hung",',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main()
