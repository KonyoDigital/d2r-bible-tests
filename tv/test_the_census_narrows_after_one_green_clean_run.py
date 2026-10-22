# -*- coding: utf-8 -*-
"""REG-2431 (#186) - THE CENSUS NARROWS, BUT ONLY AFTER ITS ONE GREEN FULL CLEAN RUN, AND IT LEARNS.

MEASURED 2026-10-22 on his Mac: `heart2.py --prove <owed> --slice` ran test_control's proof[11] as a FULL 2,287-case
run, 10+ minutes under load 16, while the machine's red memory remembered all 27 of its proofs (1-6 cases each) - the
census never asked it (heart2.py `_rk = ... if (_PUSH is not None ...)`), and a census proof that went red never taught
it either. The push asks the memory before any clean run because its clean WAVE and closing run bracket the pair; the
census has no wave, so its order is: the gate's ONE full clean run (shared by its proofs, REG-1669), then each proof's
narrowed pair (its remembered cases untampered green, tampered red), then the full tampered run when the pair does not
decide it - which teaches the memory what caught it.

Driven through the REAL _prove_gates / lanes / _prove_gate_census / _prove_one / _prove_narrow / _run_gate and the
REAL red memory, on a file of this law's own (the machine's is never read or written):
  1. a remembered gate of two proofs costs ONE full clean run, two narrowed pairs and the closing run - not four full
     runs - and the record calls both proofs narrow;
  2. a gate RED untampered is UNPROVABLE, and no narrowed pair ran: a narrow PROVEN never stands without the green
     full clean run in the same sandbox;
  3. a full tampered run that goes red teaches the memory the case that caught it, and the next census narrows on it.
RED_PROOF below.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2 as H  # noqa: E402

#: the fixture law: a plain unittest file whose Catches.test_catch is what a tamper reddens; Other.test_other stands for
#: anything else in the suite (CENSUS_RED_HERE makes it red untampered). Every run is logged: full | subset, clean |
#: tampered, and the case ids it was asked for.
_LAW = r'''
import io, os, sys, unittest
here = os.path.dirname(os.path.abspath(__file__))
SUBJECT = os.path.join(here, "sub" + "ject.txt")


def _subject():
    with io.open(SUBJECT, encoding="utf-8") as fh:
        return fh.read()


class Catches(unittest.TestCase):
    def test_catch(self):
        self.assertNotIn("BROKEN", _subject())


class Other(unittest.TestCase):
    def test_other(self):
        import time
        time.sleep(float(os.environ.get("CENSUS_FULL_S") or 0))   # the rest of a big suite: what a narrowed run skips
        self.assertFalse(os.environ.get("CENSUS_RED_HERE"), "red untampered - something else in the suite")


if __name__ == "__main__":
    if [a for a in sys.argv[1:] if not a.startswith("-")] and os.environ.get("CENSUS_SUBSET_S"):
        import time
        time.sleep(float(os.environ["CENSUS_SUBSET_S"]))         # a law whose setup dwarfs its cases
    log = os.environ.get("CENSUS_LAW_LOG")
    if log:
        ids = [a for a in sys.argv[1:] if not a.startswith("-")]
        with io.open(log, "a", encoding="utf-8") as fh:
            fh.write("%s|%s|%s\n" % ("subset" if ids else "full", "tampered" if "BROKEN" in _subject() else "clean",
                                     ",".join(ids)))
    unittest.main()
'''
_GATE, _FILE = "census-narrow-fixture", "t_census_narrow_law.py"
CAUGHT = "Catches.test_catch"
PROOFS = [{"why": "A", "file": "subject.txt", "find": "fine", "replace": "BROKEN", "matches": 1},
          {"why": "B", "file": "subject.txt", "find": "here", "replace": "BROKEN", "matches": 1}]


class _Patch(object):
    """Swap heart2's module globals and always put them back."""

    def __init__(self, **kw):
        self.kw, self.old = kw, {}

    def __enter__(self):
        for k, v in self.kw.items():
            self.old[k] = getattr(H, k)
            setattr(H, k, v)
        return self

    def __exit__(self, *_e):
        for k, v in self.old.items():
            setattr(H, k, v)
        return False


class _Env(object):
    def __init__(self, **kw):
        self.kw, self.old = kw, {}

    def __enter__(self):
        for k, v in self.kw.items():
            self.old[k] = os.environ.get(k)
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return self

    def __exit__(self, *_e):
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return False


class _Case(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="census_narrow_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.log = os.path.join(self.d, "runs.log")
        self.memory = os.path.join(self.d, ".heart2_red.json")
        # a full run of the fixture costs 1 s more than a narrowed one, as a big suite's does (REG-2431: a census narrows
        # only while a pair costs less than the gate's full run)
        e = _Env(HEART2_RED_MEMORY=None, HEART2_RED_PATH=None, HEART2_PROVE_WORKERS="1", TV_LAW_WIDTHS=None,
                 CENSUS_LAW_LOG=self.log, CENSUS_RED_HERE=None, CENSUS_FULL_S="1", CENSUS_SUBSET_S=None)
        e.__enter__()
        self.addCleanup(e.__exit__)
        # the red memory is THIS law's file, read and written through the real memory code - and the module's memory
        # state is this law's too, so nothing of the machine's is ever read, marked or written
        p = _Patch(RED_MEMORY=self.memory, _RED_USED={},
                   _RED={"path": None, "sig": None, "entries": None, "folded": True})
        p.__enter__()
        self.addCleanup(p.__exit__)

    def make(self, say=print):
        root = tempfile.mkdtemp(prefix="censusnarrow.", dir=self.d)
        repo = os.path.join(root, "repo")
        for rel, text in (("tv/control_app.py", "# sandbox marker\n"), ("tv/" + _FILE, _LAW),
                          ("tv/subject.txt", "all fine here\n")):
            p = os.path.join(repo, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with io.open(p, "w", encoding="utf-8") as fh:
                fh.write(text)
        return os.path.join(repo, "tv"), root

    def seed(self):
        """The memory remembers both proofs, as a push or an earlier census taught it."""
        for i, pr in enumerate(PROOFS):
            H._red_remember(H._red_key(_GATE, i, pr), _GATE, i, [CAUGHT])
        self.assertEqual(sorted(e["ids"] for e in self.remembered().values()), [[CAUGHT], [CAUGHT]], "PREMISE: no seed")

    def remembered(self):
        if not os.path.exists(self.memory):
            return {}
        with io.open(self.memory, encoding="utf-8") as fh:
            return json.load(fh).get("entries") or {}

    def census(self, spec=None):
        said = []
        run = H._CensusRun(cache=None, red=True)
        extra = {"gate_spec": (lambda name: spec)} if spec else {}
        with _Patch(make_sandbox=self.make, _CENSUS=run, **extra):
            results, per = H._prove_gates([(_GATE, _FILE, PROOFS)], said.append, workers=1)
        runs = []
        if os.path.exists(self.log):
            with io.open(self.log, encoding="utf-8") as fh:
                runs = [l.rstrip("\n").split("|") for l in fh if l.strip()]
            os.remove(self.log)
        return results, per, runs, said, run


class TheCensusNarrowsAfterItsCleanRun(_Case):

    def test_a_remembered_gate_costs_one_full_clean_run_and_narrowed_pairs(self):
        self.seed()
        results, per, runs, said, run = self.census()
        self.assertEqual((results, per), ({_GATE: H.PROVEN}, {_GATE: [H.PROVEN, H.PROVEN]}), "\n".join(said))
        self.assertEqual(runs, [["full", "clean", ""],
                                ["subset", "clean", CAUGHT], ["subset", "tampered", CAUGHT],
                                ["subset", "clean", CAUGHT], ["subset", "tampered", CAUGHT],
                                ["full", "clean", ""]],
                         "a remembered gate did not cost ONE full clean run, a narrowed pair per proof and the closing "
                         "run: %s\n%s" % (runs, "\n".join(said)))
        self.assertEqual([(run.proofs[(_GATE, i)].get("f"), run.proofs[(_GATE, i)].get("a")) for i in (0, 1)],
                         [("narrow", "narrow"), ("narrow", "narrow")], "the census record misnames the path taken")

    def test_a_gate_red_untampered_is_unprovable_and_no_narrowed_pair_ran(self):
        self.seed()
        with _Env(CENSUS_RED_HERE="1"):
            results, per, runs, said, _run = self.census()
        self.assertEqual(results, {_GATE: H.UNPROVABLE},
                         "a gate RED untampered was called %s - a narrowed pair stood without a green clean run: %s"
                         % (results.get(_GATE), "\n".join(said)))
        self.assertEqual([r for r in runs if r[0] == "subset"], [],
                         "a narrowed pair ran before (or without) the gate's green full clean run: %s" % runs)
        self.assertEqual(runs, [["full", "clean", ""]], "the red clean run was not the one run: %s" % runs)

    def test_a_full_red_teaches_the_memory_and_the_next_census_narrows(self):
        self.assertEqual(self.remembered(), {}, "PREMISE: the memory is not empty")
        results, per, runs, said, run = self.census()
        self.assertEqual(results, {_GATE: H.PROVEN}, "\n".join(said))
        self.assertEqual([r[:2] for r in runs], [["full", "clean"], ["full", "tampered"], ["full", "tampered"],
                                                 ["full", "clean"]],
                         "PREMISE: a cold census is one clean run, a full tampered run per proof and the closing run: %s"
                         % runs)
        got = dict((e.get("why") or e.get("proof"), e.get("ids")) for e in self.remembered().values())
        self.assertEqual(sorted(e.get("ids") for e in self.remembered().values()), [[CAUGHT], [CAUGHT]],
                         "a census full proof that went red did not teach the memory what caught it: %s" % got)
        results, per, runs, said, run = self.census()
        self.assertEqual(len([r for r in runs if r[0] == "full"]), 2,
                         "the next census did not narrow on what it learned: %s" % runs)

    def test_a_gate_whose_pair_costs_more_than_its_full_run_stops_narrowing(self):
        """MEASURED 2026-10-22: test_a_killed_run_is_never_a_red narrowed all 34 proofs and its census took 241.7 s against
        225.3 s in full - a pair is two runs, each paying the law's setup. Once a pair costs more than the gate's measured
        full clean run, the gate's other proofs run in full, and the line says why."""
        self.seed()
        with _Env(CENSUS_FULL_S="0", CENSUS_SUBSET_S="1"):
            results, per, runs, said, run = self.census()
        self.assertEqual(results, {_GATE: H.PROVEN}, "\n".join(said))
        self.assertEqual([r[:2] for r in runs], [["full", "clean"], ["subset", "clean"], ["subset", "tampered"],
                                                 ["full", "tampered"], ["full", "clean"]],
                         "a gate whose narrowed pair cost more than its full run kept narrowing: %s" % runs)
        self.assertTrue(any("more than this gate's full run" in l for l in said), said)

    def test_a_gate_run_with_an_argv_tail_is_never_narrowed(self):
        """The narrowed pair hands the law its case ids as its only arguments: a gate registered with its own argv tail
        (or a -c script) would run something else entirely, so it is asked in full, whatever the memory says."""
        self.seed()
        results, per, runs, said, _run = self.census(spec=(["-v"], 180, None))
        self.assertEqual(results, {_GATE: H.PROVEN}, "\n".join(said))
        self.assertEqual([r for r in runs if r[0] == "subset"], [],
                         "a gate with an argv tail was narrowed - its case ids replaced its own arguments: %s" % runs)


RED_PROOF = [
    {"why": "REG-2431 - the census asks the red memory BEFORE its full clean run: a narrowed PROVEN stands for a law that "
            "is red untampered",
     "file": "heart2.py",
     "find": "    _rids = _red_recall(_rk) if _rk else None\n",
     "replace": "    _rids = _red_recall(_rk or _crk) if (_rk or _crk) else None\n",
     "matches": 1},
    {"why": "REG-2431 - a census full proof that goes red never teaches the memory: every census pays it in full again",
     "file": "heart2.py",
     "find": "        _rk = _crk                                         # the full run below teaches the memory what caught it\n",
     "replace": "        pass\n",
     "matches": 1},
    {"why": "REG-2431 - the census never asks the red memory: test_control's 27 proofs run in full again",
     "file": "heart2.py",
     "find": "        _crids = _red_recall(_crk)\n",
     "replace": "        _crids = None\n",
     "matches": 1},
    {"why": "REG-2431 - a gate whose narrowed pair costs more than its full run keeps narrowing (241.7 s vs 225.3 s)",
     "file": "heart2.py",
     "find": "        if _cs.get(\"pairS\") is not None and _cs.get(\"s\") is not None and _cs[\"pairS\"] > _cs[\"s\"]:  "
             "# NARROW-PAYS\n",
     "replace": "        if False:  # NARROW-PAYS\n",
     "matches": 1},
    {"why": "REG-2431 - the census's narrowed pair is asked when the proof's run has an argv tail or a -c script",
     "file": "heart2.py",
     "find": "    _crk = (_red_key(name, idx, pr) if (_PUSH is None and _census_asks_red() and not _script and not _extra\n",
     "replace": "    _crk = (_red_key(name, idx, pr) if (_PUSH is None and _census_asks_red()\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
