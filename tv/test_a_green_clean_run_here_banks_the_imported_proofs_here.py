# -*- coding: utf-8 -*-
"""REG-2589 - AFTER A GREEN CLEAN RUN HERE, ANOTHER TREE'S PROVENS ARE BANKED UNDER THIS TREE.

REG-2587 closed #242 on the small push: a gate whose proofs the cache served from ANOTHER tree (a CI shard, another
worktree) runs its law clean HERE once before those PROVENs are kept. But a green run banked nothing, so the entries kept
the foreign tree and EVERY later push over the same bytes asked the same clean run again. MEASURED in the proof-keys e2e
(2026-10-23): push 2 and push 3 of test_gate_banks over identical bytes each paid one clean run. Now:

  1. green clean run here (REG-2587's own, the wave's, or a run this pass shared) -> each served foreign PROVEN still
     PROVEN after the closing run is banked again under THIS tree, provedAt unchanged, provedIn naming where; the next
     push over these bytes runs NO clean run;
  2. RED, UNKNOWN, or no clean run asked (ELSEWHERE, unreadable widths) -> nothing is rebanked; the foreign tree stays;
  3. a proof served from THIS tree is never rewritten.
Drives the REAL _prove_gate push path over a temp gate and a temp cache file, and reads the file back.
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
sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402  (its docstrings carry non-ASCII)
_console_safe_enable()
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2 as H  # noqa: E402

GATE = "no-such-registered-gate"
FOREIGN = "/home/runner/work/x/x"
LINES = []


def _say(*a, **k):
    LINES.append(" ".join(str(x) for x in a))


class _Runs(object):
    """heart2._run_gate's stand-in: a tampered run is red; the Nth CLEAN run answers clean[N-1] (default green)."""

    def __init__(self, tv, clean):
        self.tv, self.script, self.clean = tv, list(clean), 0

    def __call__(self, sandbox_tv, filename, timeout=180, extra=(), script=None, widths=None):
        with io.open(os.path.join(self.tv, "subject.py"), encoding="utf-8") as fh:
            if "BAD" in fh.read():
                return False, "Ran 1 test | FAILED"
        self.clean += 1
        a = self.script[self.clean - 1] if self.clean <= len(self.script) else True
        return a, {True: "Ran 1 test | OK", False: "Ran 1 test | FAILED (red here)"}.get(a, "timed out after 120s")


class AGreenCleanRunHereBanksHere(unittest.TestCase):

    def setUp(self):
        del LINES[:]
        self.root = tempfile.mkdtemp(prefix="h2rebank.")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.tv = os.path.join(self.root, "repo", "tv")
        os.makedirs(self.tv)
        with io.open(os.path.join(self.tv, "subject.py"), "w", encoding="utf-8") as fh:
            fh.write('A = "GOOD"\nB = "GOOD"\n')
        with io.open(os.path.join(self.tv, "fake_gate.py"), "w", encoding="utf-8") as fh:
            fh.write("import sys\nsys.exit(0)\n")
        self.proofs = [{"file": "subject.py", "find": '%s = "GOOD"' % k, "replace": '%s = "BAD"' % k,
                        "matches": 1, "why": k} for k in ("A", "B")]
        for p in (mock.patch.object(H, "_run_gate", None),
                  mock.patch.dict(os.environ, {"HEART2_RED_MEMORY": "0"})):
            p.start()
            self.addCleanup(p.stop)
        self.assertIsNone(H._PUSH, "PREMISE: no push-time run is in progress")
        self.addCleanup(lambda: setattr(H, "_PUSH", None))
        self.path = os.path.join(self.root, ".heart2_cache.json")
        self.keys = []

    def bank(self, tree, only=None):
        """The cache file as an import leaves it: each proof (or the first `only`) PROVEN, measured at 1000, in `tree`."""
        c = H._VerdictCache(path=self.path, say=_say)
        self.keys = []
        for i, pr in enumerate(self.proofs[:only]):
            key, _r, why = c.key_for(self.tv, GATE, "fake_gate.py", pr)
            self.assertIsNotNone(key, "PREMISE: the fixture law cannot be keyed: %s" % why)
            self.keys.append(key)
            c.store(key, {"verdict": H.PROVEN, "provedAt": 1000, "gate": GATE, "proof": i, "tree": tree})
        self.assertTrue(c.flush(), "PREMISE: the fixture cache could not be written")

    def push(self, clean, wave=None, hits=2):
        """One push-time prove of the gate over a cache freshly read from disk. -> (run, per, clean runs, cache)"""
        c = H._VerdictCache(path=self.path, say=_say)
        runs = _Runs(self.tv, clean)
        H._run_gate = runs
        H._PUSH = run = H._PushRun(order={}, browser=(), cache=c)
        if wave:
            run.clean_wave.update(wave)
        try:
            _v, per = H._prove_gate(self.tv, GATE, "fake_gate.py", self.proofs, _say)
        finally:
            H._PUSH = None
        self.assertEqual(c.hits, hits, "PREMISE: %d proof(s) served by the cache, want %d" % (c.hits, hits))
        return run, per, runs.clean

    def disk(self):
        with io.open(self.path, encoding="utf-8") as fh:
            ent = json.load(fh)["entries"]
        return [ent[k] for k in self.keys]

    def test_a_green_clean_run_banks_them_here_and_the_next_push_asks_nothing(self):
        self.bank(FOREIGN)
        run, per, n = self.push([True])
        self.assertEqual((per, n), ([H.PROVEN] * 2, 1), "PREMISE: REG-2587 asks one green clean run here")
        for e in self.disk():
            self.assertEqual(e.get("tree"), H.TREE_ID, "a green clean run here left the entry in %r" % e.get("tree"))
            self.assertEqual(e.get("provedIn"), FOREIGN, "the rebanked entry forgot where it was proved")
            self.assertEqual(e.get("provedAt"), 1000, "rebanking moved the age the proof was MEASURED at")
        self.assertTrue(any("REG-2589" in ln for ln in LINES), LINES)
        run, per, n = self.push([False])          # a second clean run would be RED: it must not be asked at all
        self.assertEqual((per, n), ([H.PROVEN] * 2, 0), "the next push over the same bytes ran the clean run again")

    def test_an_entry_with_no_tree_is_banked_here_too(self):
        self.bank(None)
        self.push([True])
        self.assertEqual([e.get("tree") for e in self.disk()], [H.TREE_ID] * 2)

    def test_a_red_clean_run_rebanks_nothing(self):
        self.bank(FOREIGN)
        run, per, n = self.push([False])
        self.assertEqual(per, [H.UNPROVABLE] * 2)
        self.assertEqual([e.get("tree") for e in self.disk()], [FOREIGN] * 2, "a law RED here was banked here")

    def test_a_clean_run_that_cannot_finish_rebanks_nothing(self):
        self.bank(FOREIGN)
        self.push([None])
        self.assertEqual([e.get("tree") for e in self.disk()], [FOREIGN] * 2, "an UNKNOWN clean run was banked here")

    def test_no_clean_run_asked_rebanks_nothing(self):
        for pr in self.proofs:
            pr["widths"] = "not a width"
        self.bank(FOREIGN)
        run, per, n = self.push([True])
        self.assertEqual(n, 0)
        self.assertEqual([e.get("tree") for e in self.disk()], [FOREIGN] * 2, "nothing ran here and it was banked here")

    def test_the_waves_green_run_banks_them_here(self):
        self.bank(FOREIGN)
        run, per, n = self.push([False], wave={("fake_gate.py", "[]", "None", "", 180): (True, "Ran 1 test | OK")})
        self.assertEqual((per, n), ([H.PROVEN] * 2, 0), "PREMISE: the wave's green run is reused (REG-2587)")
        self.assertEqual([e.get("tree") for e in self.disk()], [H.TREE_ID] * 2, "the wave's green run banked nothing")

    def test_a_wave_row_of_another_gate_on_the_same_file_proves_nothing(self):
        """second eye - two gates may share a law file with other argv; only THIS gate's clean-run row counts"""
        self.bank(FOREIGN)
        run, per, n = self.push([False], wave={("fake_gate.py", "['--other']", "None", "", 180): (True, "OK")})
        self.assertEqual(n, 1, "another gate's green wave row stood in for this gate's clean run here")
        self.assertEqual(per, [H.UNPROVABLE] * 2)
        self.assertEqual([e.get("tree") for e in self.disk()], [FOREIGN] * 2, "another gate's run banked these here")

    def test_kept_with_no_clean_run_here_rebanks_nothing(self):
        """REG-2587 keeps the served PROVENs of a gate no proof of which can run on this PC (ELSEWHERE) - kept, never
        judged here, so never banked as this tree's"""
        real = H._prove_one

        def elsewhere(*a, **k):
            return H.ELSEWHERE if k.get("clean_only") else real(*a, **k)
        self.bank(FOREIGN)
        with mock.patch.object(H, "_prove_one", elsewhere):
            run, per, n = self.push([True])
        self.assertEqual(per, [H.PROVEN] * 2, "PREMISE: REG-2587 keeps an ELSEWHERE gate's served PROVENs")
        self.assertEqual([e.get("tree") for e in self.disk()], [FOREIGN] * 2, "a gate never run here was banked here")

    def test_a_proof_the_closing_run_takes_away_is_not_rebanked(self):
        """one proof served from another tree, two run here on one shared clean run, the CLOSING run red: the shared
        run WAS green here, but nothing survives the closing run, so nothing is banked as this tree's"""
        self.proofs.append({"file": "subject.py", "find": 'B = "GOOD"', "replace": 'B = "BAD!"', "matches": 1,
                            "why": "B2"})
        self.bank(FOREIGN, only=1)
        run, per, n = self.push([True, False], hits=1)
        self.assertEqual(n, 2, "PREMISE: one shared clean run and one closing run, got %d clean run(s)" % n)
        self.assertEqual(per, [H.UNPROVABLE] * 3, "PREMISE: a red closing run keeps no PROVEN of the gate")
        self.assertEqual([e.get("tree") for e in self.disk()], [FOREIGN], "the closing run's loss was banked here")

    def test_a_proof_proved_here_is_never_rewritten(self):
        self.bank(H.TREE_ID)
        strip = lambda es: [dict((k, v) for k, v in e.items() if k != "usedAt") for e in es]   # noqa: E731 - R4 use
        before = strip(self.disk())
        self.push([])
        self.assertEqual(strip(self.disk()), before, "an entry already of this tree was rewritten")
        self.assertFalse(any("REG-2589" in ln for ln in LINES), LINES)


RED_PROOF = [
    {"why": "REG-2589 - a green clean run here banks nothing: every push asks the same clean run again",
     "file": "heart2.py",
     "find": "            _rebank_here(run.cache, name, per, say)      # REG-2589",
     "replace": "            pass  # ",
     "matches": 1},
    {"why": "REG-2589 - a gate kept with NO clean run here (ELSEWHERE) is banked as this tree's",
     "file": "heart2.py",
     "find": "    if cache is None or not getattr(_CLEAN, \"green_here\", False):\n",
     "replace": "    if cache is None:\n",
     "matches": 1},
    {"why": "REG-2589 - rebanked before the closing run judged them: a PROVEN it takes away is banked here",
     "file": "heart2.py",
     "find": "or per[_s[0]] != PROVEN:\n",
     "replace": ":\n",
     "matches": 1},
    {"why": "REG-2589 - the rebanked entry is stamped with this run's clock, not the age it was measured at",
     "file": "heart2.py",
     "find": "        cache.store(_s[2], dict(_s[3], tree=TREE_ID, provedIn=_s[1], cleanHereAt=now))\n",
     "replace": "        cache.store(_s[2], dict(_s[3], tree=TREE_ID, provedIn=_s[1], cleanHereAt=now, provedAt=now))\n",
     "matches": 1},
    {"why": "REG-2589 - the wave's green run is not counted, so a big push rebanks nothing",
     "file": "heart2.py",
     "find": "        _CLEAN.green_here = True\n        return per                                       # the wave ran it",
     "replace": "        return per                                       # the wave ran it",
     "matches": 1},
    {"why": "REG-2589 - a green wave row of ANOTHER gate on the same file stands in for this gate's clean run",
     "file": "heart2.py",
     "find": "             if ck[0] == filename and ck[1] == repr(_ex) and ck[2] == repr(_sc) and ck[4] == _to]\n",
     "replace": "             if ck[0] == filename]\n",
     "matches": 1},
    {"why": "REG-2589 - the rebanked entry keeps the foreign tree, so the next push asks again",
     "file": "heart2.py",
     "find": "dict(_s[3], tree=TREE_ID, provedIn=",
     "replace": "dict(_s[3], provedIn=",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
