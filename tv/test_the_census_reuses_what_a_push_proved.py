# -*- coding: utf-8 -*-
"""REG-2430 / REG-2432 / REG-2433 (#186) - THE CENSUS REUSES WHAT A PUSH PROVED, AND ONLY WHAT IT MAY.

His words, 2026-10-22, watching his heart's last 10 owed laws grind for 90 minutes: "yea this also needs memory maybe?
so it doesnt reprove also everytime". MEASURED that afternoon on his Mac: the census (his console's self-prover,
`heart2.py --prove <owed> --slice`) never read the verdict cache - 706 PROVEN a push had banked for the exact bytes on
disk - and re-proved test_control's 27 proofs in full, ~4 min each, while a push needed seconds for the same bytes.

Driven through the REAL _prove_push / _prove_gates / lanes / _prove_gate_census / _census_served / _prove_one /
_run_gate over a throwaway fixture tree; the verdict cache is this law's own file and the red memory is closed:
  1. a PROVEN a push banked at EVERY width is served to the census with no run, and its verdict line says by whom;
  2. one input byte moved -> the census runs it, banks it (by census), and the next census serves THAT;
  3. an entry proven only at the widths its proof declares is never served to the census, which proves every width;
  4. an entry banked in ANOTHER tree is served, and the gate still pays ONE clean run here; red here, nothing stands;
  5. an entry another prover or environment stamped - or that carries no stamp - is served on NEITHER path;
  6. prove() in a law's process opens no store; heart2's own CLI process opens the machine's (here: seams), stores a
     caller hands in are used, and HEART2_PROVE_CACHE=0 closes the cache and says so.
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

#: the fixture law: a plain unittest file (so a narrowed run can name its cases), its subject reached by a COMPUTED name
#: (so the only way the subject reaches the key is the proof's own target), logging every run it makes:
#: full | subset, clean | tampered, the widths it was asked for. CENSUS_RED_HERE stands for live state outside the key.
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
        self.assertFalse(os.environ.get("CENSUS_RED_HERE"), "red in this tree only - live state no key holds")


if __name__ == "__main__":
    log = os.environ.get("CENSUS_LAW_LOG")
    if log:
        with io.open(log, "a", encoding="utf-8") as fh:
            fh.write("%s|%s|%s\n" % ("subset" if len(sys.argv) > 1 else "full",
                                     "tampered" if "BROKEN" in _subject() else "clean",
                                     os.environ.get("TV_LAW_WIDTHS") or "ALL"))
    unittest.main()
'''
_GATE, _FILE = "census-memory-fixture", "t_census_memory_law.py"
FULL_PAIR = [["full", "clean", "ALL"], ["full", "tampered", "ALL"]]


def _proof(**kw):
    pr = {"why": "the fixture's defect", "file": "subject.txt", "find": "fine", "replace": "BROKEN", "matches": 1}
    pr.update(kw)
    return pr


def _quiet(*a, **k):
    pass


def _no_facts(have, say):
    """_push_facts without git: RED_PROOF order, nothing ranked."""
    return None, dict((n, list(range(len(p)))) for n, _f, p in have), [n for n, _f, _p in have], \
        {"anchor": 0, "entry": 0, "target": 0}


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
    """Set (or, with None, remove) environment variables and always put them back."""

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


class _Tree(object):
    """make_sandbox stand-in: a REAL throwaway repo copy built from `files`; edit `files` to move the tree."""

    def __init__(self, root):
        self.root = root
        self.files = {"tv/control_app.py": "# sandbox marker\n", "tv/" + _FILE: _LAW,
                      "tv/subject.txt": "all fine here\n"}

    def make(self, say=print):
        root = tempfile.mkdtemp(prefix="censusmem.", dir=self.root)
        repo = os.path.join(root, "repo")
        for rel, text in self.files.items():
            p = os.path.join(repo, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with io.open(p, "w", encoding="utf-8") as fh:
                fh.write(text)
        return os.path.join(repo, "tv"), root


class _Case(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="census_reuse_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.tree = _Tree(self.d)
        self.cache_path = os.path.join(self.d, ".heart2_cache.json")
        self.log = os.path.join(self.d, "runs.log")
        # the machine's red memory is never touched: closed for every leg of this law
        e = _Env(HEART2_RED_MEMORY="0", HEART2_PROVE_WORKERS="1", TV_LAW_WIDTHS=None, CENSUS_LAW_LOG=self.log,
                 HEART2_AUDIT_K="0", CENSUS_RED_HERE=None)
        e.__enter__()
        self.addCleanup(e.__exit__)

    def runs(self):
        if not os.path.exists(self.log):
            return []
        with io.open(self.log, encoding="utf-8") as fh:
            out = [l.strip().split("|") for l in fh if l.strip()]
        os.remove(self.log)
        return out

    def entries(self):
        with io.open(self.cache_path, encoding="utf-8") as fh:
            return json.load(fh)["entries"]

    def rewrite(self, fn):
        with io.open(self.cache_path, encoding="utf-8") as fh:
            body = json.load(fh)
        for k in list(body["entries"]):
            body["entries"][k] = fn(dict(body["entries"][k]))
        with io.open(self.cache_path, "w", encoding="utf-8") as fh:
            json.dump(body, fh)

    def push(self, proofs=None):
        """One push-time run over the fixture, its own _VerdictCache on this law's file (a push opens it anew)."""
        said, stopped = [], []
        cache = H._VerdictCache(path=self.cache_path, say=said.append)
        with _Patch(make_sandbox=self.tree.make, _push_facts=_no_facts):
            results, _per = H._prove_push([(_GATE, _FILE, proofs or [_proof()])], said.append, stopped, cache=cache)
        return results, self.runs(), said

    def census(self, proofs=None):
        """One census run with the proof memory (the cache only), as heart2's own process runs one."""
        said = []
        run = H._CensusRun(cache=H._VerdictCache(path=self.cache_path, say=said.append), red=False)
        with _Patch(make_sandbox=self.tree.make, _CENSUS=run):
            results, _per = H._prove_gates([(_GATE, _FILE, proofs or [_proof()])], said.append, workers=1)
        return results, self.runs(), said


class TheCensusServesWhatAPushBanked(_Case):

    def test_a_push_banked_every_width_proven_is_served_with_no_run(self):
        results, runs, said = self.push()
        self.assertEqual((results, runs), ({_GATE: H.PROVEN}, FULL_PAIR), "PREMISE: the push did not prove it: %s"
                         % "\n".join(said))
        (e,) = self.entries().values()
        self.assertEqual((e.get("mode"), e.get("by"), e.get("at")), ("every-width", "push", ""),
                         "a push's banked entry does not say how wide it was proven and by whom: %s" % e)
        self.assertEqual((e.get("proverSha"), e.get("envFp")), H.prover_stamp(),
                         "a banked entry does not carry this prover's stamp: %s" % e)
        results, runs, said = self.census()
        self.assertEqual(runs, [], "the census RAN a proof a push banked for these exact bytes: %s\n%s"
                         % (runs, "\n".join(said)))
        self.assertEqual(results, {_GATE: H.PROVEN})
        self.assertTrue(any("PROVEN (cached by push" in l and "not re-run" in l for l in said),
                        "the census's verdict line does not say it was reused, and from whom: %s" % said)

    def test_one_input_byte_moved_runs_it_and_the_census_banks_its_own(self):
        self.push()
        self.tree.files["tv/subject.txt"] = "all fine here!\n"
        results, runs, said = self.census()
        self.assertEqual((results, runs), ({_GATE: H.PROVEN}, FULL_PAIR),
                         "a proof whose tampered target moved was served, not run: %s\n%s" % (runs, "\n".join(said)))
        mine = [e for e in self.entries().values() if e.get("by") == "census"]
        self.assertEqual(len(mine), 1, "the census did not bank what it proved: %s" % self.entries())
        self.assertEqual((mine[0].get("mode"), mine[0].get("at")), ("every-width", ""))
        results, runs, said = self.census()
        self.assertEqual(runs, [], "the census re-ran what it banked itself: %s" % runs)
        self.assertTrue(any("PROVEN (cached by census" in l for l in said), said)

    def test_a_declared_widths_entry_is_never_served_to_the_census(self):
        pr = _proof(widths=["1280x800"])
        results, runs, said = self.push([pr])
        self.assertEqual(runs, [["full", "clean", "1280x800"], ["full", "tampered", "1280x800"]],
                         "PREMISE: the push did not prove it at its declared widths: %s" % runs)
        (e,) = self.entries().values()
        self.assertEqual((e.get("mode"), e.get("at")), ("declared-widths", "1280x800"), e)
        results, runs, said = self.census([pr])
        self.assertEqual(runs, FULL_PAIR, "the census took a proof made at ONE width as its every-width verdict: %s\n%s"
                         % (runs, "\n".join(said)))
        self.assertEqual(results, {_GATE: H.PROVEN})

    def test_a_proof_banked_in_another_tree_still_owes_one_clean_run_here(self):
        self.push()
        self.rewrite(lambda e: dict(e, tree="/another/worktree"))
        results, runs, said = self.census()
        self.assertEqual(runs, [["full", "clean", "ALL"]],
                         "a gate served from another tree must pay exactly ONE clean run here: %s\n%s"
                         % (runs, "\n".join(said)))
        self.assertEqual(results, {_GATE: H.PROVEN})
        with _Env(CENSUS_RED_HERE="1"):
            results, runs, said = self.census()
        self.assertEqual(runs[:1], [["full", "clean", "ALL"]], runs)
        self.assertEqual(results, {_GATE: H.UNPROVABLE},
                         "a law RED here was called PROVEN on another tree's proof: %s" % "\n".join(said))

    def test_another_provers_stamp_or_none_is_served_on_neither_path(self):
        self.push()
        for label, fn in (("another prover", lambda e: dict(e, proverSha="0" * 24)),
                          ("another environment", lambda e: dict(e, envFp="0" * 24)),
                          ("no stamp at all", lambda e: dict((k, v) for k, v in e.items()
                                                             if k not in ("proverSha", "envFp")))):
            self.rewrite(fn)
            results, runs, said = self.census()
            self.assertEqual(runs, FULL_PAIR, "the census served an entry stamped by %s: %s" % (label, runs))
            self.rewrite(fn)                             # the census banked over it: plant it again
            results, runs, said = self.push()
            self.assertEqual(runs, FULL_PAIR, "a push served an entry stamped by %s: %s" % (label, runs))
            if label == "no stamp at all":
                self.assertTrue(any("carry no prover/environment stamp" in l for l in said),
                                "unstamped entries are not said at the open: %s" % said[:6])


class OnlyHeartsOwnProcessOpensTheMachinesStores(_Case):

    def _prove(self, **kw):
        seen, said = {}, []

        def fake_gates(have, say=print, workers=None, blank=None):
            run = H._CENSUS
            seen["run"] = run
            seen["cache"] = getattr(run, "cache", None) if run is not None else None
            return {n: H.PROVEN for n, _f, _p in have}, {n: [H.PROVEN] for n, _f, _p in have}

        with _Patch(gate_files=lambda say=None: [(_GATE, _FILE)], red_proofs_in=lambda f: [_proof()],
                    red_proof_unreadable=lambda f: False, _prove_gates=fake_gates,
                    _write_state=lambda *a, **k: None, CACHE=self.cache_path,
                    RED_MEMORY=os.path.join(self.d, ".heart2_red.json")):
            H.prove(only={_GATE}, say=said.append, stamp=False, **kw)
        return seen, said

    def test_a_law_driving_prove_in_process_opens_no_store(self):
        seen, said = self._prove()
        self.assertIsNone(seen.get("run"), "prove() in a law's process opened a proof memory: %s" % said)
        self.assertFalse(os.path.exists(self.cache_path), "the census wrote a store in a law's process")

    def test_hearts_own_process_opens_them_and_the_off_switch_is_said(self):
        with _Patch(_is_prover_process=lambda: True), _Env(HEART2_RED_PATH=os.path.join(self.d, ".heart2_red.json"),
                                                            HEART2_PROVE_CACHE=None, HEART2_RED_MEMORY=None):
            seen, said = self._prove()
            self.assertIsNotNone(seen.get("run"), "heart2's own census process opened no proof memory")
            self.assertEqual(getattr(seen.get("cache"), "path", None), self.cache_path)
            self.assertTrue(seen["run"].red, "the census's red memory was not opened")
            with _Env(HEART2_PROVE_CACHE="0", HEART2_RED_MEMORY="0"):
                seen, said = self._prove()
        self.assertIsNone(seen.get("cache"), "HEART2_PROVE_CACHE=0 did not close the census's cache")
        self.assertFalse(seen["run"].red, "HEART2_RED_MEMORY=0 did not close the census's red memory")
        self.assertTrue(any("OFF for this run" in l and "HEART2_PROVE_CACHE=0" in l for l in said), said)
        self.assertTrue(any("red memory is OFF" in l and "HEART2_RED_MEMORY=0" in l for l in said), said)

    def test_stores_a_caller_hands_in_are_the_ones_used(self):
        mine = H._VerdictCache(path=self.cache_path, say=_quiet)
        seen, said = self._prove(stores={"cache": mine, "red": False})
        self.assertIs(seen.get("cache"), mine, "the stores a caller handed in were not the census's")


RED_PROOF = [
    {"why": "REG-2433 - the census takes a proof made at its DECLARED widths as an every-width verdict",
     "file": "heart2.py",
     "find": "        if e is not None and census and not census_servable(e):\n",
     "replace": "        if False:\n",
     "matches": 1},
    {"why": "REG-2430 - a law driving prove() in-process opens the census's proof memory (his machine's stores)",
     "file": "heart2.py",
     "find": "    if stores is None and not prover:\n        return None",
     "replace": "    if False:\n        return None",
     "matches": 1},
    {"why": "#242 / REG-2433 - a gate served from another tree pays no clean run here: a law red here reads PROVEN",
     "file": "heart2.py",
     "find": "        if any(e.get(\"tree\") != TREE_ID for e in served.values()) and not _CLEAN.runs:\n",
     "replace": "        if False:\n",
     "matches": 1},
    {"why": "REG-2432 - another prover's (or no) stamp is served: a verdict measured by other code is reused",
     "file": "heart2.py",
     "find": "        if key in self.unstamped or (_stamped(e) and (e.get(\"proverSha\"), e.get(\"envFp\")) != prover_stamp()):"
             "  # STAMP-MATCH\n",
     "replace": "        if False:  # STAMP-MATCH\n",
     "matches": 1},
    {"why": "REG-2433 - the census never asks the verdict cache: every proof a push banked is re-proved in full",
     "file": "heart2.py",
     "find": "    hit = cache.lookup(key, census=True)\n",
     "replace": "    hit = None\n",
     "matches": 1},
    {"why": "REG-2433 - a census PROVEN is never banked: the next census pays the full proof again",
     "file": "heart2.py",
     "find": "        _held.append((idx, key, _census_entry(name, idx, pr, rels)))",
     "replace": "        pass",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
