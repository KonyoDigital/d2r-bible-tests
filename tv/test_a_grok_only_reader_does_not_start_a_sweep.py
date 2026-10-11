# -*- coding: utf-8 -*-
"""REG-2159. A GROK ONLY reader does not start a console sweep.

The vault door and the chronicle door treated "claude_chronicle_read exists" as
"Claude will read". On GROK ONLY the function exists and every page goes to a
grok one-shot, which times out and holds the relaunch lock. These sweeps run
only when Claude is the reader. A skip is not a read, not a seal, and not a try.

Nothing here spends a paid read. threading.Thread is stubbed, the lock is held
open, and every store path points at a temp directory.
"""
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app as ca  # noqa: E402
import g5_grok_eyes as g5  # noqa: E402
import self_arming as sa  # noqa: E402


_WHY = "GROK ONLY is the reader"
_NOT_CLAUDE = "the primary (Claude) lane is unavailable"


class _StoppedThread(object):
    spawned = []

    def __init__(self, *a, **k):
        _StoppedThread.spawned.append(self)
        self.started = False

    def start(self):
        self.started = True


def _reader(who):
    def _r():
        if who == "raise":
            raise RuntimeError("switch unreadable")
        return who
    return _r


class _Door(unittest.TestCase):
    """The two doors. A legal Claude call must still start, or a jammed door looks like a refusal."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="grok-skip-")
        self._env = {k: os.environ.get(k) for k in ("TV_HIST", "TV_SWEEP_LOCK", "TV_CHRON_SWEPT")}
        os.environ["TV_HIST"] = self.tmp
        os.environ["TV_SWEEP_LOCK"] = os.path.join(self.tmp, ".sweep.lock")
        os.environ["TV_CHRON_SWEPT"] = os.path.join(self.tmp, "chronicle_swept.json")
        self._vault = dict(ca._VAULT_JOB)
        self._chron = dict(ca._CHRON_JOB)
        self._may = sa.may
        self._thread = threading.Thread
        self._reader = g5.reader
        ca._VAULT_JOB["running"] = False
        ca._CHRON_JOB["running"] = False
        sa.may = lambda lock: (True, "REG-2159: the lock is open so the door is under test")
        threading.Thread = _StoppedThread
        _StoppedThread.spawned = []

    def tearDown(self):
        sa.may = self._may
        threading.Thread = self._thread
        g5.reader = self._reader
        ca._VAULT_JOB.clear()
        ca._VAULT_JOB.update(self._vault)
        ca._CHRON_JOB.clear()
        ca._CHRON_JOB.update(self._chron)
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _vault_start(self, who):
        g5.reader = _reader(who)
        _StoppedThread.spawned = []
        ca._VAULT_JOB["running"] = False
        return ca.vault_sweep_start(limit=1)

    def _chron_start(self, who):
        g5.reader = _reader(who)
        _StoppedThread.spawned = []
        ca._CHRON_JOB["running"] = False
        return ca.chronicle_sweep_start(hist_dir=self.tmp, limit=1)

    def test_claude_and_both_still_start_and_grok_does_not(self):
        for who in ("claude", "both"):
            vault = self._vault_start(who)
            self.assertIs(vault.get("ok"), True, vault)
            self.assertIs(vault.get("started"), True, vault)
            self.assertEqual(len(_StoppedThread.spawned), 1, who)
            chron = self._chron_start(who)
            self.assertIs(chron.get("ok"), True, chron)
            self.assertIs(chron.get("started"), True, chron)
            self.assertEqual(len(_StoppedThread.spawned), 1, chron)

        vault = self._vault_start("grok")
        self.assertIs(vault.get("ok"), False, vault)
        self.assertIs(vault.get("laneMissing"), True, vault)
        self.assertIs(vault.get("grokOnly"), True, vault)
        self.assertIn(_WHY, vault.get("why") or "")
        self.assertIn("unswept", vault.get("why") or "")
        self.assertNotIn(_NOT_CLAUDE, vault.get("why") or "")
        self.assertIs(ca._VAULT_JOB.get("running"), False, ca._VAULT_JOB)
        self.assertEqual(_StoppedThread.spawned, [], "a grok reader spawned a vault thread")

        chron = self._chron_start("grok")
        self.assertIs(chron.get("ok"), False, chron)
        self.assertIs(chron.get("laneMissing"), True, chron)
        self.assertIs(chron.get("grokOnly"), True, chron)
        self.assertIn(_WHY, chron.get("why") or "")
        self.assertNotIn(_NOT_CLAUDE, chron.get("why") or "")
        self.assertIs(ca._CHRON_JOB.get("running"), False, ca._CHRON_JOB)
        self.assertEqual(_StoppedThread.spawned, [], "a grok reader spawned a chronicle thread")
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "chronicle_swept.json")))

    def test_an_unreadable_switch_is_not_called_a_grok_skip(self):
        vault = self._vault_start("raise")
        self.assertIs(vault.get("ok"), True, vault)
        self.assertNotIn(_WHY, str(vault.get("why") or ""))
        chron = self._chron_start("raise")
        self.assertIs(chron.get("ok"), True, chron)
        self.assertNotIn(_WHY, str(chron.get("why") or ""))

    def test_a_running_sweep_does_not_read_when_the_reader_is_grok(self):
        g5.reader = _reader("grok")
        retro = []
        real_retro = ca._vault_retro

        def _boom():
            retro.append("retro")
            raise AssertionError("the vault sweep continued")

        ca._vault_retro = _boom
        try:
            ca._vault_sweep_run(self.tmp, 1, False, None)
        finally:
            ca._vault_retro = real_retro
        self.assertEqual(retro, [])
        self.assertIs(ca._VAULT_JOB.get("running"), False)
        self.assertEqual(ca._VAULT_JOB.get("phase"), "idle")
        self.assertIs((ca._VAULT_JOB.get("lastRefusal") or {}).get("grokOnly"), True)

        import chronicle_retro as cr
        dirs = []
        real_dirs = cr.reel_dirs

        def _dirs(*a, **k):
            dirs.append("dirs")
            return []

        cr.reel_dirs = _dirs
        try:
            ca._chron_sweep_run(self.tmp, 1, False, None)
        finally:
            cr.reel_dirs = real_dirs
        self.assertEqual(dirs, [])
        self.assertIs((ca._CHRON_JOB.get("lastRefusal") or {}).get("grokOnly"), True)
        self.assertIs(ca._CHRON_JOB.get("running"), False)

        visits = []
        real_visits = ca.chronicle_visits

        def _visits(*a, **k):
            visits.append("visit")
            return {"ok": True, "visits": []}

        ca.chronicle_visits = _visits
        try:
            ca._chron_visit_run(1700000000000)
        finally:
            ca.chronicle_visits = real_visits
        self.assertEqual(visits, [])
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "chronicle_swept.json")))


class _Ticks(unittest.TestCase):
    """The auto ticks. A skip must not burn a try and must not retire the reel."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="grok-tick-")
        self.rid = "reel_s_grok_skip"
        self.reel = os.path.join(self.tmp, self.rid)
        os.makedirs(self.reel)
        frame = os.path.join(self.reel, "f_1.jpg")
        with open(frame, "wb") as fh:
            fh.write(b"\xff\xd8\xff\xd9")
        old = time.time() - 3600
        os.utime(frame, (old, old))
        os.utime(self.reel, (old, old))
        self._env = {k: os.environ.get(k) for k in (
            "TV_HIST", "TV_SWEEP_LOCK", "TV_CHRON_SWEPT")}
        os.environ["TV_HIST"] = self.tmp
        os.environ["TV_SWEEP_LOCK"] = os.path.join(self.tmp, ".sweep.lock")
        os.environ["TV_CHRON_SWEPT"] = os.path.join(self.tmp, "chronicle_swept.json")
        self._chron_path = ca._CHRON_AUTOREAD_PATH
        self._chron = dict(ca._CHRON_AUTOREAD)
        self._on = ca._CHRON_AUTOREEL_ON
        self._owes = ca._chron_reel_owes_a_read
        self._state = ca.chronicle_sweep_state
        self._alive = ca._agent_alive
        self._visits = ca.chronicle_visits
        self._vault_path = ca._VAULT_AUTOREAD_PATH
        self._seals = ca._VAULT_SWEPT_PATH
        self._vault = dict(ca._VAULT_AUTOREAD)
        self._store = dict(ca._VAULT_AUTOREAD_STORE)
        self._grow = ca._reel_is_growing
        self._owed = ca._vault_owed_reels
        self._vstate = ca.vault_sweep_state
        self._may = sa.may
        self._thread = threading.Thread
        self._reader = g5.reader
        self._job_v = dict(ca._VAULT_JOB)
        self._job_c = dict(ca._CHRON_JOB)
        ca._CHRON_AUTOREAD_PATH = os.path.join(self.tmp, "chron_autoread.json")
        ca._VAULT_AUTOREAD_PATH = os.path.join(self.tmp, ".vault_autoread.json")
        ca._VAULT_SWEPT_PATH = os.path.join(self.tmp, "vault_swept.json")
        ca._CHRON_AUTOREEL_ON = True
        ca._CHRON_AUTOREAD.clear()
        ca._CHRON_AUTOREAD.update({
            "done": set(), "reels": set(), "lastTs": 0, "reads": 0,
            "skipped": {}, "tries": {}, "retired": {}})
        ca._VAULT_AUTOREAD.clear()
        ca._VAULT_AUTOREAD.update({
            "tries": {}, "skipped": {}, "reads": 0, "lastTs": 0,
            "retired": {}, "lastWhy": {}, "reextract": {}, "joinQueued": {}, "joinTried": {}})
        ca._VAULT_AUTOREAD_STORE.clear()
        ca._VAULT_AUTOREAD_STORE.update({"tried": False, "readable": None})
        ca._chron_reel_owes_a_read = lambda rid, mem=None, prompt_ver=None: rid == self.rid
        ca.chronicle_sweep_state = lambda *a, **k: {"running": False}
        ca.vault_sweep_state = lambda *a, **k: {"running": False}
        ca._agent_alive = lambda *a, **k: False
        ca._reel_is_growing = lambda *a, **k: False
        ca._vault_owed_reels = lambda hist=None: [self.reel]
        ca._VAULT_JOB["running"] = False
        ca._CHRON_JOB["running"] = False
        sa.may = lambda lock: (True, "REG-2159: the lock is open so the tick is under test")
        threading.Thread = _StoppedThread
        g5.reader = _reader("grok")
        _StoppedThread.spawned = []

    def tearDown(self):
        sa.may = self._may
        threading.Thread = self._thread
        g5.reader = self._reader
        ca._CHRON_AUTOREAD_PATH = self._chron_path
        ca._CHRON_AUTOREEL_ON = self._on
        ca._chron_reel_owes_a_read = self._owes
        ca.chronicle_sweep_state = self._state
        ca._agent_alive = self._alive
        ca.chronicle_visits = self._visits
        ca._VAULT_AUTOREAD_PATH = self._vault_path
        ca._VAULT_SWEPT_PATH = self._seals
        ca._reel_is_growing = self._grow
        ca._vault_owed_reels = self._owed
        ca.vault_sweep_state = self._vstate
        ca._CHRON_AUTOREAD.clear()
        ca._CHRON_AUTOREAD.update(self._chron)
        ca._VAULT_AUTOREAD.clear()
        ca._VAULT_AUTOREAD.update(self._vault)
        ca._VAULT_AUTOREAD_STORE.clear()
        ca._VAULT_AUTOREAD_STORE.update(self._store)
        ca._VAULT_JOB.clear()
        ca._VAULT_JOB.update(self._job_v)
        ca._CHRON_JOB.clear()
        ca._CHRON_JOB.update(self._job_c)
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_the_chronicle_reel_tick_does_not_count_a_grok_skip(self):
        for _ in range(ca._CHRON_AUTOREAD_MAX_TRIES + 3):
            out = ca.chronicle_autoreel_tick()
            self.assertTrue(out.get("triesUnchanged"), out)
            self.assertTrue(out.get("laneMissing"), out)
            self.assertIn(_WHY, out.get("why") or "")
        self.assertEqual(ca._CHRON_AUTOREAD["tries"].get(self.rid, 0), 0)
        self.assertNotIn(self.rid, ca._CHRON_AUTOREAD.get("retired") or {})
        self.assertEqual(_StoppedThread.spawned, [])
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "chronicle_swept.json")))

    def test_the_visit_tick_does_not_mark_a_skipped_visit_read(self):
        ts = 1700000000000
        ca.chronicle_visits = lambda limit=12: {"ok": True, "visits": [{
            "ts": ts, "ledger": "uniques", "frames": ["f_1"], "n": 1}]}
        for _ in range(ca._CHRON_AUTOREAD_MAX_TRIES + 3):
            out = ca.chronicle_autoread_tick()
            self.assertTrue(out.get("triesUnchanged"), out)
            self.assertTrue(out.get("laneMissing"), out)
            self.assertIn("NOT counted", out.get("why") or "")
        self.assertEqual(ca._CHRON_AUTOREAD["tries"].get(str(ts), 0), 0)
        self.assertNotIn(ts, ca._CHRON_AUTOREAD.get("done") or set())
        self.assertEqual(_StoppedThread.spawned, [])

    def test_the_vault_tick_does_not_retire_a_reel_it_did_not_read(self):
        for _ in range(ca._VAULT_AUTOREAD_MAX_TRIES + 3):
            out = ca.vault_autoreel_tick()
            self.assertTrue(out.get("triesUnchanged"), out)
            self.assertTrue(out.get("laneMissing"), out)
            self.assertIn(_WHY, out.get("why") or "")
        self.assertEqual(ca._VAULT_AUTOREAD["tries"].get(self.rid, 0), 0)
        self.assertNotIn(self.rid, ca._VAULT_AUTOREAD.get("retired") or {})
        self.assertEqual(_StoppedThread.spawned, [])
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "vault_swept.json")))


RED_PROOF = [
    {
        "why": "REG-2159 - GROK ONLY is no longer a reason to skip, so the sweep starts and calls grok",
        "file": "tv/control_app.py",
        "find": "    if who != \"grok\":\n        return None\n",
        "replace": "    if True:\n        return None\n",
        "matches": 1,
    },
    {
        "why": "REG-2159 - the skip no longer says the lane is missing, so the tick counts it and retires the reel",
        "file": "tv/control_app.py",
        "find": "    return {\"ok\": False, \"laneMissing\": True, \"grokOnly\": True,\n",
        "replace": "    return {\"ok\": False, \"grokOnly\": True,\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
