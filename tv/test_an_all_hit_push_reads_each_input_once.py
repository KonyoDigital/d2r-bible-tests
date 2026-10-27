# -*- coding: utf-8 -*-
"""REG-2631 — A PUSH WHOSE EVERY PROOF IS SERVED FROM THE CACHE READS EACH INPUT ONCE, NEVER ONCE PER PROOF.

⚠ WHAT IT IS FOR. v3792's hook on his Mac served 303 of 303 proofs from the cache and still spent 2m39 proving. MEASURED
on the box with 19 gates / 226 proofs all served: 563,770 file reads (~1,250 inputs for each of 452 keys - the clean
wave's peek and the main pass's lookup each key every proof), each one under the cache's one lock, and a clean wave
that built and deleted a sandbox per lane to run 0 clean runs.

⚠ THE DEFECTS THIS GUARDS:
  · a digest is served after the tree may have changed: the keyer's memo is valid only within a QUIET STRETCH, which
    every law run and every tamper write ends (_run_gate and _prove_one are wrapped). A digest taken before such a call
    and served after it would key a tampered or rewritten file with the bytes from before;
  · a same-size rewrite whose mtime was put back is served from the memo - the inode-change time is in the memo's key;
  · the memo is never asked, so every proof re-reads every input (the cost this exists to remove);
  · the clean wave runs over a gate the cache serves whole on this tree's keys (sandboxes for nothing), or it leaves
    out a gate with a miss or one that owes a clean run here (REG-2599) - the wave would stop being fail-fast.
RED_PROOF below.
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
from console_safe import enable as _console_safe_enable  # noqa: E402  (it prints non-ASCII)
_console_safe_enable()
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2        # noqa: E402

RED_PROOF = [
    {
        "why": "REG-2631 - a law run does not end the quiet stretch, so a digest from before it is served after it",
        "file": "heart2.py",
        "find": "        _quiet_bump()\n        try:\n            return fn(*a, **k)\n        finally:\n            _quiet_bump()\n",
        "replace": "        return fn(*a, **k)\n",
        "matches": 1,
    },
    {
        "why": "REG-2631 - the memo key drops the inode-change time, so a same-size rewrite with its mtime put back is served",
        "file": "heart2.py",
        "find": "st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_ino, gen)",
        "replace": "st.st_size, st.st_mtime_ns, st.st_ino, gen)",
        "matches": 1,
        # #193 (his ALT, 2026-10-27) - the only case that catches this tamper skips where "this filesystem's ctime did
        # not move", and on Windows st_ctime is the CREATION time, so it never moves: the proof read BLIND there, and
        # one BLIND shut every lock on the PC. It is judged where ctime is the inode-change time (POSIX), ELSEWHERE here.
        "needs": "posix",
    },
    {
        "why": "REG-2631 - the memo is never asked, so every proof re-reads every input",
        "file": "heart2.py",
        "find": "    d = memo.get(k)\n    if d is None:\n        d = _sha_file(path)\n",
        "replace": "    d = None\n    if d is None:\n        d = _sha_file(path)\n",
        "matches": 1,
    },
    {
        "why": "REG-2631 - the wave runs every gate again, served or not",
        "file": "heart2.py",
        "find": "        if not served:\n            out.append(n)\n",
        "replace": "        out.append(n)\n",
        "matches": 1,
    },
    {
        "why": "REG-2631 - the wave leaves out a gate whose proof another tree banked though the push changes its law",
        "file": "heart2.py",
        "find": "            if hit is None or (hit.get(\"tree\") != TREE_ID and _owes_here(run, n)):\n                served = False\n",
        "replace": "            if hit is None:\n                served = False\n",
        "matches": 1,
    },
]


class _Tmp(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="quiet.")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.p = os.path.join(self.d, "f.txt")
        self.write("one\n")
        self.memo = {}

    def write(self, text):
        with io.open(self.p, "w", encoding="utf-8") as fh:
            fh.write(text)

    def reads(self, fn):
        n = []
        real = heart2._sha_file

        def counting(path, memo=None):
            n.append(path)
            return real(path, memo)
        with mock.patch.object(heart2, "_sha_file", counting):
            out = fn()
        return out, len(n)


class ADigestIsServedOnlyWithinAQuietStretch(_Tmp):
    def test_a_quiet_stretch_reads_a_file_once(self):
        (a, b), n = self.reads(lambda: (heart2._sha_quiet(self.p, self.memo), heart2._sha_quiet(self.p, self.memo)))
        self.assertEqual(a, b)
        self.assertEqual(n, 1, "the second key of the same bytes read the file again")

    def test_a_law_run_ends_the_stretch(self):
        first = heart2._sha_quiet(self.p, self.memo)
        st = os.stat(self.p)

        def law_run(*a, **k):                 # what a tamper does: rewrite, same size, mtime put back
            self.write("two\n")
            os.utime(self.p, ns=(st.st_atime_ns, st.st_mtime_ns))
            return True, ""
        heart2._quiet_stretch(law_run)()
        self.assertNotEqual(heart2._sha_quiet(self.p, self.memo), first, "a digest from before a law run was served")

    def test_the_real_law_runners_end_the_stretch(self):
        for fn in (heart2._run_gate, heart2._prove_one):
            self.assertTrue(getattr(fn, "__wrapped__", None) is not None, "%s does not end the quiet stretch" % fn.__name__)

    def test_a_wrapped_call_bumps_on_entry_and_exit_even_when_it_raises(self):
        g = heart2._QUIET["gen"]

        def boom():
            raise RuntimeError("x")
        with self.assertRaises(RuntimeError):
            heart2._quiet_stretch(boom)()
        self.assertEqual(heart2._QUIET["gen"], g + 2)

    def test_a_same_size_rewrite_with_its_mtime_put_back_is_read_again_without_a_bump(self):
        """nothing in the prover writes outside a law run, but the inode-change time still catches one that did"""
        first = heart2._sha_quiet(self.p, self.memo)
        st = os.stat(self.p)
        time.sleep(0.01)
        self.write("two\n")
        os.utime(self.p, ns=(st.st_atime_ns, st.st_mtime_ns))
        if os.stat(self.p).st_ctime_ns == st.st_ctime_ns:
            self.skipTest("this filesystem's ctime did not move")
        self.assertNotEqual(heart2._sha_quiet(self.p, self.memo), first)

    def test_a_missing_file_is_none(self):
        self.assertIsNone(heart2._sha_quiet(os.path.join(self.d, "missing"), self.memo))


class _Run(object):
    def __init__(self, cache, direct=None):
        self.cache, self.direct, self.order = cache, direct, {}


class _Cache(object):
    def __init__(self, entries):
        self.entries = entries

    def key_for(self, sandbox, name, filename, pr):
        return ("%s:%s" % (name, pr["i"]), [], None)

    def peek(self, key):
        return self.entries.get(key)


class TheWaveRunsOnlyWhatItWouldRun(unittest.TestCase):
    def setUp(self):
        self.by = {"g": ("g", "g.py", [{"i": 0}, {"i": 1}]), "h": ("h", "h.py", [{"i": 0}])}
        self.gates = ["g", "h"]

    def test_a_gate_served_whole_on_this_trees_keys_is_left_out(self):
        c = _Cache({"g:0": {"tree": heart2.TREE_ID}, "g:1": {"tree": heart2.TREE_ID}})
        self.assertEqual(heart2._wave_owed(self.gates, self.by, _Run(c, direct=set())), ["h"])

    def test_a_gate_with_one_miss_stays(self):
        c = _Cache({"g:0": {"tree": heart2.TREE_ID}, "h:0": {"tree": heart2.TREE_ID}})
        self.assertEqual(heart2._wave_owed(self.gates, self.by, _Run(c, direct=set())), ["g"])

    def test_a_foreign_proof_whose_law_the_push_changes_stays(self):
        c = _Cache({"g:0": {"tree": "/box"}, "g:1": {"tree": "/box"}, "h:0": {"tree": "/box"}})
        self.assertEqual(heart2._wave_owed(self.gates, self.by, _Run(c, direct={"g"})), ["g"])
        self.assertEqual(heart2._wave_owed(self.gates, self.by, _Run(c, direct=None)), ["g", "h"],
                         "when what the push changes is unknown, every foreign-served gate owes its clean run")

    def test_no_cache_means_every_gate(self):
        self.assertEqual(heart2._wave_owed(self.gates, self.by, _Run(None)), ["g", "h"])

    def test_a_keyer_that_raises_keeps_the_gate(self):
        c = _Cache({})
        c.key_for = mock.Mock(side_effect=OSError("x"))
        self.assertEqual(heart2._wave_owed(self.gates, self.by, _Run(c)), ["g", "h"])


if __name__ == "__main__":
    unittest.main()
