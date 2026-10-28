# -*- coding: utf-8 -*-
"""#150 (REG-2942 / REG-2943) - A PUSH KILLED MID-GATE KEEPS WHAT A GREEN CLEAN RUN ALREADY BRACKETED.

A push gate held every PROVEN in _CLEAN.pending until its CLOSING clean run (REG-1988), and _on_fatal_signal removed
the sandboxes and os._exit()ed without banking. So a kill mid-gate - the hook's deadline, a Ctrl-C, a closed terminal -
lost every proof that gate had already proved, and the next push paid for all of them again (test_control: 27 proofs at
~4 min each). His order: prove once, never drop.

Banking each PROVEN the moment it returns is NOT the fix: the proofs share ONE clean run, and a proof can go red because
earlier runs drifted the sandbox rather than because of its tamper - the reason the closing run exists. So the bracket
moves earlier instead: once CHECKPOINT_EVERY PROVENs wait and another proof is about to run, the shared clean run is
asked again; green banks and FLUSHES every waiting PROVEN (each sits between two green clean runs), red banks nothing.
And the fatal-signal handler writes what was already banked before it exits - never a PROVEN still waiting.

Driven through the REAL _prove_gate / _prove_gate_push / _VerdictCache against a real directory, exactly as the REG-1988
law drives them; only the law RUN is a stand-in, answering from the subject file's actual bytes. A kill is a
KeyboardInterrupt from inside a run - it escapes every `except Exception` on the way out, as a signal's exit does.
[[regression-guard]] [[stale-reading]]
RED_PROOF below.
"""
import io
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import heart2 as H  # noqa: E402

GATE = "no-such-registered-gate"
KEYS = ("A", "B", "C", "D", "E", "F")


def _quiet(*a, **k):
    pass


class _Runs(object):
    """A stand-in for heart2._run_gate that reads the subject's real bytes. `red_clean_at` turns the Nth clean run red;
    `kill_at` raises KeyboardInterrupt on the Nth tampered run (a kill landing mid-gate)."""

    def __init__(self, tv, red_clean_at=None, kill_at=None):
        self.tv, self.red_clean_at, self.kill_at = tv, red_clean_at, kill_at
        self.clean = self.tampered = 0

    def __call__(self, sandbox_tv, filename, timeout=180, extra=(), script=None, widths=None):
        with io.open(os.path.join(self.tv, "subject.py"), encoding="utf-8") as fh:
            src = fh.read()
        if "BAD" in src:
            self.tampered += 1
            if self.kill_at is not None and self.tampered == self.kill_at:
                raise KeyboardInterrupt("the push was killed mid-gate")
            return False, "Ran 1 test | FAILED"
        self.clean += 1
        if self.red_clean_at is not None and self.clean == self.red_clean_at:
            return False, "Ran 1 test | FAILED (drifted state)"
        return True, "Ran 1 test | OK"


class AKilledPushKeepsWhatItProved(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="h2kill.")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.tv = os.path.join(self.root, "repo", "tv")
        os.makedirs(self.tv)
        self.good = "".join('%s = "GOOD"\n' % k for k in KEYS)
        self._write(self.good)
        with io.open(os.path.join(self.tv, "fake_gate.py"), "w", encoding="utf-8") as fh:
            fh.write("import sys\nsys.exit(0)\n")
        self.proofs = [{"file": "subject.py", "find": '%s = "GOOD"' % k, "replace": '%s = "BAD"' % k,
                        "matches": 1, "why": k} for k in KEYS]
        self.path = os.path.join(self.root, ".heart2_cache.json")
        p = mock.patch.dict(os.environ, {"HEART2_RED_MEMORY": "0"})   # the sabotage memory is neither read nor written
        p.start()
        self.addCleanup(p.stop)
        self._real = H._run_gate
        self.addCleanup(lambda: setattr(H, "_run_gate", self._real))
        self.addCleanup(lambda: setattr(H, "_PUSH", None))
        self.assertIsNone(H._PUSH, "PREMISE: no push-time run is in progress")
        self.assertGreater(len(KEYS), H.CHECKPOINT_EVERY, "PREMISE: the gate has more proofs than one checkpoint holds")

    def _write(self, text):
        with io.open(os.path.join(self.tv, "subject.py"), "w", encoding="utf-8") as fh:
            fh.write(text)

    def _gate(self, runs):
        """One push-time gate over a cache opened FROM DISK, as each push opens it. -> (verdict, per, cache)"""
        cache = H._VerdictCache(path=self.path, say=_quiet)
        H._run_gate = runs
        H._PUSH = H._PushRun(order={}, browser=(), cache=cache)
        try:
            verdict, per = H._prove_gate(self.tv, GATE, "fake_gate.py", self.proofs, _quiet)
        finally:
            H._PUSH = None
        return verdict, per, cache

    def _killed(self, runs):
        with self.assertRaises(KeyboardInterrupt, msg="PREMISE: the stand-in kill did not land"):
            self._gate(runs)
        self._write(self.good)                  # a real kill leaves this sandbox behind; the next push makes a fresh one

    def _on_disk(self):
        ent, why = H._load_cache(self.path)
        self.assertIsNone(why, "the cache on disk could not be read: %s" % why)
        return ent or {}

    def test_a_kill_after_a_green_checkpoint_leaves_those_proofs_on_disk(self):
        n = H.CHECKPOINT_EVERY
        self._killed(_Runs(self.tv, kill_at=n + 1))
        self.assertEqual(len(self._on_disk()), n,
                         "the push was killed after %d proofs had come back PROVEN and a green clean run bracketed "
                         "them, and the disk holds %d - the next push proves them all again" % (n, len(self._on_disk())))

    def test_the_resumed_push_reuses_what_was_banked_and_proves_only_the_rest(self):
        n = H.CHECKPOINT_EVERY
        self._killed(_Runs(self.tv, kill_at=n + 1))
        runs = _Runs(self.tv)
        verdict, per, cache = self._gate(runs)
        self.assertEqual((verdict, per), (H.PROVEN, [H.PROVEN] * len(KEYS)))
        self.assertEqual(cache.hits, n, "the resumed push re-proved %d proof(s) the killed one had already banked"
                         % (n - cache.hits))
        self.assertEqual(runs.tampered, len(KEYS) - n, "the resumed push ran %d tampered runs; only %d were owed"
                         % (runs.tampered, len(KEYS) - n))
        self.assertEqual(len(self._on_disk()), len(KEYS))

    def test_a_red_checkpoint_banks_nothing(self):
        # clean run 1 is the gate's shared one; run 2 is the checkpoint - red, as a drifted sandbox reads
        self._killed(_Runs(self.tv, red_clean_at=2, kill_at=H.CHECKPOINT_EVERY + 1))
        self.assertEqual(self._on_disk(), {}, "a PROVEN whose checkpoint clean run went RED was banked anyway")

    def test_an_unkilled_gate_pays_one_checkpoint_and_banks_every_proof(self):
        runs = _Runs(self.tv)
        verdict, per, _cache = self._gate(runs)
        self.assertEqual((verdict, per), (H.PROVEN, [H.PROVEN] * len(KEYS)))
        self.assertEqual(len(self._on_disk()), len(KEYS))
        self.assertEqual(runs.clean, 3, "six proofs should pay the shared clean run, one checkpoint and the closing "
                                        "run - %d clean runs were paid" % runs.clean)


@unittest.skipUnless(H._host_has_posix_signals(), "a signal sent to itself is a POSIX act - declared, never a pass")
class TheFatalSignalWritesWhatWasBanked(unittest.TestCase):
    """REG-2943 - a SIGTERM mid-push writes what store() already banked before the handler exits."""

    def test_a_sigterm_writes_the_banked_entry_and_never_a_waiting_one(self):
        d = tempfile.mkdtemp(prefix="h2sig.")
        self.addCleanup(shutil.rmtree, d, True)
        path = os.path.join(d, ".heart2_cache.json")
        child = (
            "import os, signal, sys, time\n"
            "sys.path.insert(0, %r)\n"
            "import heart2 as H\n"
            "c = H._VerdictCache(path=%r, say=lambda *a, **k: None)\n"
            "H._PUSH = H._PushRun(order={}, browser=(), cache=c)\n"
            "c.store('banked', {'verdict': H.PROVEN, 'provedAt': 1})\n"
            "H._CLEAN.pending = [(0, 'waiting', {'verdict': H.PROVEN, 'provedAt': 1})]\n"
            "H.install_sandbox_cleanup()\n"
            "os.kill(os.getpid(), signal.SIGTERM)\n"
            "time.sleep(30)\n" % (HERE, path))
        env = dict(os.environ, HEART2_RED_MEMORY="0")
        r = subprocess.run([sys.executable, "-c", child], capture_output=True, text=True, timeout=120, env=env)
        self.assertEqual(r.returncode, 128 + int(signal.SIGTERM),
                         "PREMISE: the child did not exit the way the signal meant (%r): %s" % (r.returncode,
                                                                                              r.stderr[-400:]))
        ent, why = H._load_cache(path)
        self.assertIsNone(why, "the cache the handler wrote cannot be read: %s" % why)
        self.assertIn("banked", ent or {}, "a SIGTERM exited without writing what the push had already banked")
        self.assertNotIn("waiting", ent or {}, "the handler banked a PROVEN that no green clean run bracketed")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {"why": "#150 - no checkpoint: every PROVEN waits for the closing run, and a kill mid-gate loses them all",
     "file": "heart2.py",
     "find": "                _ckpt[\"on\"] = _checkpoint_bank(name, got, say, run)",
     "replace": "                _ckpt[\"on\"] = False",
     "matches": 1},
    {"why": "#150 - a checkpoint banks without asking the clean run again, so a drift-red PROVEN is stored",
     "file": "heart2.py",
     "find": "    for r in [r for r in (getattr(_CLEAN, \"runs\", None) or {}).values() if r.get(\"reused\")]:\n        try:\n            ok, tail = r[\"again\"]()",
     "replace": "    for r in []:\n        try:\n            ok, tail = r[\"again\"]()",
     "matches": 1},
    {"why": "#150 - the checkpoint banks in memory only, so the kill still loses it (nothing written until the gate ends)",
     "file": "heart2.py",
     "find": "    _CLEAN.pending = keep\n    run.cache.flush()\n",
     "replace": "    _CLEAN.pending = keep\n",
     "matches": 1},
    {"why": "#150 - a checkpoint leaves what it banked waiting, so every later proof asks another checkpoint clean "
            "run - REG-1988's run per proof, back",
     "file": "heart2.py",
     "find": "    _CLEAN.pending = keep\n",
     "replace": "    pass\n",
     "matches": 1},
    {"why": "REG-2943 - the fatal-signal handler exits without writing what the push had already banked",
     "file": "heart2.py",
     "find": "    _flush_on_kill()\n    _remove_all_sandboxes()\n",
     "replace": "    _remove_all_sandboxes()\n",
     "matches": 1,
     "needs": "posix-signals"},
]
