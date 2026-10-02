# -*- coding: utf-8 -*-
"""REG-1745 — A FINISHED SWEEP FREES THE RELAUNCH; ONLY A SWEEP THAT IS READING HOLDS IT.

MEASURED on the ALT, 2026-10-02: v3563 was on disk and the console stayed on v3562, refusing with "a sweep is
reading footage (the lock was touched 456s ago)". No sweep was reading: the chronicle sweep that touched
.sweep.lock at 23:26:06 had written its result at 23:28:27 and stopped, and both in-process jobs were idle. The
lock only went COLD (900 s), never free, and the chronicle autoread lane starts its next sweep about every 14
minutes - 23:40:02 re-armed it 64 s before it would have gone cold. A relaunch checked every 5 minutes kept
landing on a fresh lock, and he read "no sweep has run" (the vault meter) beside a console that would not update.

  · DRIVEN: a sweep that ends - on its success path or a raise - writes "released" on the lock (both runners).
  · DRIVEN: drift_may_relaunch lets a released lock through when no sweep in this process is running, and still
    refuses, naming the lane, when one is - a released label never outranks a live read.
  · DRIVEN: release refuses while either lane runs (two lanes, one lock), and keeps the mtime fresh, so
    run_gates' grace for state files the sweep just wrote is unchanged.
  · DRIVEN: an unreleased fresh lock with nothing running still refuses, and says that no sweep is running
    instead of claiming one is reading.
  · DRIVEN: after a release, the next sweep's first heartbeat re-holds the lock at once (the 60 s rate limit
    would otherwise leave "released" on a running sweep).
RED_PROOF below. [[the-unjoined-end]] [[stale-reading]] [[unknown-stays-unknown]]
"""
import io
import os
import shutil
import sys
import tempfile
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()


def _ca():
    import control_app as ca
    return ca


class _Lock(unittest.TestCase):
    """A private lock file, neutral world, and both job dicts restored afterwards."""

    def setUp(self):
        ca = _ca()
        self.d = tempfile.mkdtemp(prefix="sweep_release_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.lock = os.path.join(self.d, ".sweep.lock")
        env = mock.patch.dict(os.environ, {"TV_SWEEP_LOCK": self.lock})
        env.start()
        self.addCleanup(env.stop)
        for name in ("board_identity_drift",):
            p = mock.patch.object(ca, name, lambda *a, **k: None)
            p.start()
            self.addCleanup(p.stop)
        self.chron = dict(ca._CHRON_JOB)
        self.vault = dict(ca._VAULT_JOB)
        self.addCleanup(self._restore)
        ca._CHRON_JOB["running"] = False
        ca._VAULT_JOB["running"] = False

    def _restore(self):
        ca = _ca()
        ca._CHRON_JOB.clear()
        ca._CHRON_JOB.update(self.chron)
        ca._VAULT_JOB.clear()
        ca._VAULT_JOB.update(self.vault)

    def _write(self, text, age=5):
        with io.open(self.lock, "w", encoding="utf-8") as fh:
            fh.write(text)
        t = time.time() - age
        os.utime(self.lock, (t, t))

    def _read(self):
        with io.open(self.lock, encoding="utf-8") as fh:
            return fh.read()

    def _decide(self):
        dd = {}
        ok, why = _ca().drift_may_relaunch(detail=dd)
        return ok, why or "", dd.get("blocker")


class TheGateReadsTheRelease(_Lock):

    def test_baseline_an_unreleased_fresh_lock_with_nothing_running_still_refuses(self):
        self._write("%d" % int(time.time()))
        ok, why, blocker = self._decide()
        self.assertFalse(ok)
        self.assertEqual(blocker, "work", why)
        self.assertIn("no sweep is running", why,
                      "nothing is reading, and the refusal still claims a sweep is: %r" % why)

    def test_a_released_lock_with_nothing_running_does_not_hold_the_relaunch(self):
        self._write("%d released" % int(time.time()))
        ok, why, blocker = self._decide()
        self.assertNotEqual(blocker, "work",
                            "a sweep that banked its reads still blocks the relaunch: %r" % why)
        self.assertNotIn("sweep lock was touched", why)

    def test_a_released_label_never_outranks_a_live_read(self):
        # THE LOCK LAYER ALONE. nothing_in_flight() also refuses a running job, so with it live this case
        # cannot tell whether the lock layer itself held - heart2 measured exactly that (the sabotage that
        # trusts 'released' over a live lane stayed green). Both later layers answer "go" here.
        ca = _ca()
        for name, val in (("nothing_in_flight", (True, "law: nothing else")), ("_tree_is_mid_edit", (False, ""))):
            p = mock.patch.object(ca, name, lambda *a, _v=val, **k: _v)
            p.start()
            self.addCleanup(p.stop)
        self._write("%d released" % int(time.time()))
        ca._CHRON_JOB["running"] = True
        ok, why, blocker = self._decide()
        self.assertFalse(ok, "a running chronicle sweep was relaunched out from under")
        self.assertEqual(blocker, "work", why)
        self.assertIn("chronicle sweep is reading", why)


class TheSweepReleasesWhatItHeld(_Lock):

    def test_release_marks_the_lock_and_keeps_it_fresh_for_run_gates(self):
        self._write("123", age=600)
        self.assertTrue(_ca()._sweep_lock_release())
        self.assertIn("released", self._read())
        self.assertLess(time.time() - os.path.getmtime(self.lock), 60,
                        "the release left an old mtime, so run_gates loses its grace for the state files "
                        "this sweep just wrote")

    def test_release_refuses_while_either_lane_runs(self):
        for job in ("_CHRON_JOB", "_VAULT_JOB"):
            self._write("123")
            getattr(_ca(), job)["running"] = True
            try:
                self.assertFalse(_ca()._sweep_lock_release(), "%s running and the lock was freed" % job)
                self.assertEqual(self._read(), "123")
            finally:
                getattr(_ca(), job)["running"] = False

    def test_the_next_heartbeat_re_holds_the_lock_at_once(self):
        ca = _ca()
        ca._sweep_lock_touch()                        # a sweep's beat, inside the 60 s limit afterwards
        self._write("%d" % int(time.time()))
        self.assertTrue(ca._sweep_lock_release())
        ca._sweep_lock_touch()
        self.assertNotIn("released", self._read(),
                         "the first heartbeat after a release was rate-limited away - a running sweep "
                         "would sit under a 'released' lock for up to a minute")

    def test_the_chronicle_sweep_releases_on_its_way_out(self):
        import chronicle_retro
        self._write("%d" % int(time.time()))
        with mock.patch.object(chronicle_retro, "reel_dirs", side_effect=RuntimeError("law")):
            _ca()._chron_sweep_run(self.d, 1)
        self.assertIn("released", self._read(), "a chronicle sweep ended and left the relaunch held")

    def test_the_vault_sweep_releases_on_its_way_out(self):
        ca = _ca()
        self._write("%d" % int(time.time()))
        with mock.patch.object(ca, "_vault_retro", side_effect=RuntimeError("law")):
            ca._vault_sweep_run(self.d, 1)
        self.assertIn("released", self._read(), "a vault sweep ended and left the relaunch held")


RED_PROOF = [
    {"why": "REG-1745 - the chronicle sweep ends without releasing, so a banked sweep holds the relaunch 15 minutes",
     "file": "control_app.py",
     "find": "    finally:\n        _sweep_lock_release()                  # REG-1745\n",
     "replace": "    finally:\n        pass\n",
     "matches": 1},
    {"why": "REG-1745 - the vault sweep ends without releasing",
     "file": "control_app.py",
     "find": "        _vault_lane_note_outcome(reel_dir)     # REG-1649\n        _sweep_lock_release()                  # REG-1745\n",
     "replace": "        _vault_lane_note_outcome(reel_dir)     # REG-1649\n",
     "matches": 1},
    {"why": "REG-1745 - the relaunch gate never reads the release, so a finished sweep still blocks it",
     "file": "control_app.py",
     "find": "                        _released = _SWEEP_LOCK_RELEASED in _fh.read(64)\n",
     "replace": "                        _released = False\n",
     "matches": 1},
    {"why": "REG-1745 - the gate believes 'released' while a lane is reading",
     "file": "control_app.py",
     "find": "            _released = False\n            if not _lane:\n",
     "replace": "            _released = False\n            if True:\n",
     "matches": 1},
    {"why": "REG-1745 - one lane's end frees the lock the other lane is still reading under",
     "file": "control_app.py",
     "find": "        if (_CHRON_JOB or {}).get(\"running\") or (_VAULT_JOB or {}).get(\"running\"):\n"
             "            return False\n        p = _sweep_lock_path()\n",
     "replace": "        p = _sweep_lock_path()\n",
     "matches": 1},
    {"why": "REG-1745 - the heartbeat after a release stays rate-limited, leaving 'released' on a running sweep",
     "file": "control_app.py",
     "find": "        _sweep_lock_touch.__defaults__[0][0] = 0.0\n",
     "replace": "        pass\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
