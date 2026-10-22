# -*- coding: utf-8 -*-
"""#42 lever 1 (REG-1710) - A PROOF REMEMBERS WHICH CASES CAUGHT IT, AND THE MEMORY CAN ONLY SAVE TIME.

His question, 2026-10-02: "all these pushs are so long taking hours each ... we had pushes that were 17 minutes average.
now they are each an hour plus". MEASURED: every batch touched tv/test_control.py, and each of its 6 sabotages re-ran all
2,259 cases (8-14 min apiece) to learn what one or two cases already said - 99-101 min of proofs per push.

At push time a tampered run that goes red now records WHICH cases failed; the next push asks only those, untampered
(must be green) and tampered (must be red). Every other outcome falls back to the full proof.

What this law drives - the REAL _prove_one and the REAL _run_gate, against a real two-class unittest law in a sandbox:
  * a first proof runs in full and learns the case that caught it; the second runs only that case and is PROVEN
  * a stale memory (a case that does not catch it) falls back to the full proof, which re-learns
  * a BLIND law is never called PROVEN by its memory - narrowed green, full green, BLIND
  * a remembered name that no longer exists cannot fake a red: the narrowed CLEAN run must be green first
  * outside push time, and with HEART2_RED_MEMORY=0, every proof runs in full

R2 (REG-2342, 2026-10-21) - ONE MEMORY PER MACHINE. MEASURED on the v3783 push: the memory was per checkout, so a fresh
worktree's push ran test_control's 27 tampered proofs in full (187-227 s each) while main's memory held all 27. Now:
  * it lives beside the verdict cache - git's common dir - from main and from every worktree alike;
  * it is keyed by the sabotage (gate, file, find, replace) with NO idx: a proof inserted above keeps every recall;
  * a key from before R2 (with its idx) is still recalled, and re-filed under the new key;
  * at the cap (20,000) an entry no gate file declares leaves first, then the least recently USED or learned;
  * an unreadable memory is kept aside, never written over;
  * a push folds every checkout's own pre-R2 memory in (newest 'at' wins) - and never into a law's fixture memory.
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
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2 as H  # noqa: E402

LAW = '''import unittest
import subject


class Catches(unittest.TestCase):
    def test_value_is_one(self):
        self.assertEqual(subject.VALUE, 1)


class Bystander(unittest.TestCase):
    def test_true(self):
        self.assertTrue(True)

    def test_other(self):
        self.assertEqual(subject.OTHER, 2)


if "__main__" == __name__:     # reversed on purpose: TestNoOrphanSuite anchors on the real guard
    unittest.main()
'''

BLIND_LAW = '''import unittest
import subject


class Bystander(unittest.TestCase):
    def test_other(self):
        self.assertEqual(subject.OTHER, 2)


if "__main__" == __name__:     # reversed on purpose: TestNoOrphanSuite anchors on the real guard
    unittest.main()
'''

PROOF = {"why": "fixture", "file": "subject.py", "find": "VALUE = 1", "replace": "VALUE = 2", "matches": 1}


class _Push(object):
    pass


class ARedMemory(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="h2red.")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.tv = os.path.join(self.root, "repo", "tv")
        os.makedirs(self.tv)
        with io.open(os.path.join(self.tv, "subject.py"), "w", encoding="utf-8") as fh:
            fh.write("VALUE = 1\nOTHER = 2\n")
        with io.open(os.path.join(self.tv, "law_fixture.py"), "w", encoding="utf-8") as fh:
            fh.write(LAW)
        with io.open(os.path.join(self.tv, "blind_fixture.py"), "w", encoding="utf-8") as fh:
            fh.write(BLIND_LAW)
        saved = (H.RED_MEMORY, H._PUSH, H._run_gate, os.environ.get("HEART2_RED_MEMORY"))

        def _restore():
            H.RED_MEMORY, H._PUSH, H._run_gate = saved[0], saved[1], saved[2]
            if saved[3] is None:
                os.environ.pop("HEART2_RED_MEMORY", None)
            else:
                os.environ["HEART2_RED_MEMORY"] = saved[3]
        self.addCleanup(_restore)
        os.environ.pop("HEART2_RED_MEMORY", None)
        H.RED_MEMORY = os.path.join(self.root, ".heart2_red.json")
        H._PUSH = _Push()
        self.calls, real = [], saved[2]

        def spy(sandbox_tv, filename, timeout=180, extra=(), script=None, widths=None):
            self.calls.append(list(extra or ()))
            return real(sandbox_tv, filename, timeout=timeout, extra=extra, script=script, widths=widths)
        H._run_gate = spy
        self.said = []

    def say(self, *a, **k):
        self.said.append(" ".join(str(x) for x in a))

    def prove(self, law="law_fixture.py", name="red-memory-fixture"):
        self.calls[:] = []
        return H._prove_one(self.tv, name, law, dict(PROOF), 0, self.say)

    def memory(self):
        if not os.path.exists(H.RED_MEMORY):
            return {}
        with io.open(H.RED_MEMORY, encoding="utf-8") as fh:
            return json.load(fh)["entries"]

    def plant(self, ids, name="red-memory-fixture", key=None, at=1):
        """A memory on disk holding one entry - written beside and renamed in, as the store's own writer does."""
        tmp = H.RED_MEMORY + ".plant"
        with io.open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"format": 2, "entries": {str(key or H._red_key(name, 0, PROOF)):
                                                {"gate": name, "proof": 0, "ids": ids, "at": at}}}, fh)
        os.replace(tmp, H.RED_MEMORY)

    def test_the_parser_reads_both_unittest_shapes_and_drops_class_errors(self):
        got = H._red_ids(["FAIL: test_a (__main__.Klass)", "ERROR: test_b (__main__.Other.test_b)",
                          "ERROR: setUpClass (__main__.Klass)", "FAIL: test_c (pkg.mod.Thing)", "noise"])
        self.assertEqual(got, ["Klass.test_a", "Other.test_b"])

    def test_a_first_proof_learns_and_the_second_asks_only_what_caught_it(self):
        self.assertEqual(self.prove(), H.PROVEN)
        self.assertEqual(self.calls, [[], []], "the first proof must run the law in full, clean then tampered")
        ids = [e["ids"] for e in self.memory().values()]
        self.assertEqual(ids, [["Catches.test_value_is_one"]])
        self.assertEqual(self.prove(), H.PROVEN)
        self.assertEqual(self.calls, [["Catches.test_value_is_one"], ["Catches.test_value_is_one"]],
                         "the second proof did not ask only the remembered case: %r" % self.calls)
        self.assertTrue(any("that caught it before" in s for s in self.said), self.said)

    def test_a_stale_memory_falls_back_to_the_full_proof_and_relearns(self):
        self.plant(["Bystander.test_true"])
        self.assertEqual(self.prove(), H.PROVEN)
        self.assertIn([], self.calls, "a stale memory was trusted - the full proof never ran: %r" % self.calls)
        self.assertEqual([e["ids"] for e in self.memory().values()], [["Catches.test_value_is_one"]])

    def test_a_blind_law_is_never_proven_by_its_memory(self):
        self.plant(["Bystander.test_other"])
        self.assertEqual(self.prove(law="blind_fixture.py"), H.BLIND)

    def test_a_name_that_no_longer_exists_cannot_fake_a_red(self):
        self.plant(["Nope.test_gone"])
        self.assertEqual(self.prove(law="blind_fixture.py"), H.BLIND,
                         "a remembered case that does not exist errored red and was credited as a proof")

    def test_outside_push_time_every_proof_runs_in_full(self):
        self.plant(["Catches.test_value_is_one"])
        H._PUSH = None
        self.assertEqual(self.prove(), H.PROVEN)
        self.assertEqual(self.calls, [[], []])

    def test_a_closed_memory_neither_narrows_nor_learns(self):
        os.environ["HEART2_RED_MEMORY"] = "0"
        self.assertEqual(self.prove(), H.PROVEN)
        self.assertEqual(self.calls, [[], []])
        self.assertEqual(self.memory(), {})

    # ── R2 (REG-2342) — one memory per machine ─────────────────────────────────────────────────────────────────────────
    def test_the_memory_is_the_machines_beside_the_verdict_cache(self):
        """★ from a worktree and from main alike: <git common dir>/heart2/.heart2_red.json; HEART2_RED_PATH is a seam"""
        main = os.path.join(self.root, "main")
        wt = os.path.join(self.root, "wt")
        gd = os.path.join(main, ".git", "worktrees", "wt")
        for d in (os.path.join(main, "tv"), gd, os.path.join(wt, "tv")):
            os.makedirs(d)
        with io.open(os.path.join(gd, "commondir"), "w", encoding="utf-8") as fh:
            fh.write("../..\n")
        with io.open(os.path.join(wt, ".git"), "w", encoding="utf-8") as fh:
            fh.write("gitdir: %s\n" % gd)
        want = os.path.join(main, ".git", "heart2", ".heart2_red.json")
        for tree in (wt, main):
            cache = H._shared_cache_path(here=os.path.join(tree, "tv"), repo=tree, env={})
            self.assertEqual(H._red_memory_path(cache=cache, env={}), want,
                             "the red memory is a checkout's own again - what a worktree learns dies with it")
        self.assertEqual(H._red_memory_path(env={"HEART2_RED_PATH": "/x/.heart2_red.json"}), "/x/.heart2_red.json")
        if not os.environ.get("HEART2_RED_PATH"):              # (a seam names its own file)
            self.assertEqual(os.path.dirname(H._RED_DEFAULT), os.path.dirname(H._CACHE_DEFAULT),
                             "this process's red memory is not beside its verdict cache")

    def test_a_proof_inserted_above_keeps_its_recall(self):
        """★ the key holds no idx: proof 0 learns; the same sabotage, now proof 1 (a proof was inserted above it), is
        asked only of the case that caught it"""
        self.assertEqual(self.prove(), H.PROVEN)
        self.assertEqual(self.calls, [[], []], "PREMISE: the first proof did not run in full")
        self.calls[:] = []
        self.assertEqual(H._prove_one(self.tv, "red-memory-fixture", "law_fixture.py", dict(PROOF), 1, self.say),
                         H.PROVEN)
        self.assertEqual(self.calls, [["Catches.test_value_is_one"], ["Catches.test_value_is_one"]],
                         "moving the proof from idx 0 to 1 lost its memory: %r" % self.calls)

    def test_a_key_from_before_r2_is_recalled_and_refiled(self):
        """★ an entry under the pre-R2 key (gate, IDX, file, find, replace) narrows the proof, and the next write files it
        under the new key and marks the old one re-filed (so it leaves first at the cap)"""
        key = H._red_key("red-memory-fixture", 0, PROOF)
        self.plant(["Catches.test_value_is_one"], key=key.legacy, at=7)
        self.assertEqual(self.prove(), H.PROVEN)
        self.assertEqual(self.calls, [["Catches.test_value_is_one"], ["Catches.test_value_is_one"]],
                         "a pre-R2 key was not recalled: %r" % self.calls)
        H._red_flush()
        mem = self.memory()
        self.assertEqual((mem.get(str(key)) or {}).get("ids"), ["Catches.test_value_is_one"],
                         "the recalled entry was not re-filed under the new key: %s" % sorted(mem))
        self.assertEqual(mem[key.legacy].get("refiled"), str(key), "the old key is not marked re-filed")

    def test_at_the_cap_a_dead_entry_leaves_first_then_the_least_used(self):
        """★ eviction is by USE: an entry no gate declares leaves first; then a newer entry nobody used leaves before an
        old one a push recalled yesterday"""
        ent = {"used": {"at": 1, "usedAt": 100, "ids": ["A.test_a"]}, "idle": {"at": 50, "ids": ["B.test_b"]},
               "dead": {"at": 200, "usedAt": 200, "ids": ["C.test_c"]}}
        live = {"used", "idle"}
        e = dict(ent)
        H._red_evict(e, 2, live=live)
        self.assertEqual(sorted(e), ["idle", "used"], "an entry no gate declares outlived live ones: %s" % sorted(e))
        H._red_evict(e, 1, live=live)
        self.assertEqual(sorted(e), ["used"], "the used entry left before the idle one - eviction by learn time")

    def test_a_corrupt_stamp_never_blocks_a_write(self):
        """★ an entry whose 'at' is not a number (a hand edit, a bad merge) is read as the oldest - it never raises inside
        the merge, where it would block every later write of the memory"""
        key = H._red_key("red-memory-fixture", 0, PROOF)
        tmp = H.RED_MEMORY + ".plant"
        with io.open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"format": 2, "entries": {str(key): {"gate": "g", "proof": 0, "ids": ["Old.test_x"],
                                                           "at": "yesterday", "usedAt": "never"}}}, fh)
        os.replace(tmp, H.RED_MEMORY)
        H._red_remember(key, "red-memory-fixture", 0, ["Catches.test_value_is_one"])
        self.assertEqual(self.memory()[str(key)]["ids"], ["Catches.test_value_is_one"],
                         "a corrupt stamp on disk blocked the write of what this push learned")

    def test_an_unreadable_memory_is_kept_aside_not_written_over(self):
        """★ a memory that will not parse is said, and the next write renames it aside - its bytes are never lost"""
        with io.open(H.RED_MEMORY, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        self.assertEqual(self.prove(), H.PROVEN)             # learns -> a write over the unreadable memory
        aside = [n for n in os.listdir(self.root) if n.startswith(".heart2_red.json.unreadable-")]
        self.assertEqual(len(aside), 1, "the unreadable memory was written over: %s" % os.listdir(self.root))
        with io.open(os.path.join(self.root, aside[0]), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "{not json")
        self.assertEqual([e["ids"] for e in self.memory().values()], [["Catches.test_value_is_one"]])

    def test_every_checkouts_own_memory_is_folded_in_and_never_into_a_fixture(self):
        """★ main's and every live worktree's pre-R2 tv/.heart2_red.json are found from git's common dir and folded in,
        newest 'at' winning; a push's automatic fold never reaches a law's fixture memory"""
        main = os.path.join(self.root, "m")
        wt = os.path.join(self.root, "w")
        gd = os.path.join(main, ".git", "worktrees", "w")
        for d in (os.path.join(main, "tv"), gd, os.path.join(wt, "tv")):
            os.makedirs(d)
        with io.open(os.path.join(gd, "commondir"), "w", encoding="utf-8") as fh:
            fh.write("../..\n")
        with io.open(os.path.join(gd, "gitdir"), "w", encoding="utf-8") as fh:
            fh.write(os.path.join(wt, ".git") + "\n")
        with io.open(os.path.join(wt, ".git"), "w", encoding="utf-8") as fh:
            fh.write("gitdir: %s\n" % gd)
        for tree, body in ((main, {"ka": {"gate": "g", "proof": 0, "ids": ["A.test_a"], "at": 1}}),
                           (wt, {"ka": {"gate": "g", "proof": 0, "ids": ["A.test_new"], "at": 5},
                                 "kb": {"gate": "g", "proof": 1, "ids": ["B.test_b"], "at": 2}})):
            with io.open(os.path.join(tree, "tv", ".heart2_red.json"), "w", encoding="utf-8") as fh:
                json.dump(body, fh)
        found = H._red_v1_sources(repo=main)
        self.assertEqual(sorted(os.path.realpath(p) for p in found),
                         sorted(os.path.realpath(os.path.join(t, "tv", ".heart2_red.json")) for t in (main, wt)),
                         "a checkout's own memory was not found from main: %s" % found)
        real = (H._red_v1_sources, H._RED["folded"], H._RED_DEFAULT, H._CACHE_DEFAULT, sys.argv[0])
        seams = dict((k, os.environ.pop(k)) for k in ("HEART2_RED_PATH", "HEART2_CACHE_PATH") if k in os.environ)
        H._red_v1_sources = lambda repo=None: found
        try:
            # 1. a law driving prove(push=True) in-process never folds - even into what it takes for the machine's own
            H._RED["folded"], H._RED_DEFAULT, H._CACHE_DEFAULT = False, H.RED_MEMORY, H.CACHE
            self.assertEqual(H._red_fold_checkouts(self.say), 0, "a law driving the prover in-process folded his "
                                                                 "checkouts' memories")
            # 2. the prover's own process never folds into a fixture memory
            H._RED["folded"], H._RED_DEFAULT, H._CACHE_DEFAULT = False, real[2], real[3]
            sys.argv[0] = os.path.join(HERE, "heart2.py")
            self.assertEqual(H._red_fold_checkouts(self.say), 0, "a push's fold reached a law's fixture memory")
        finally:
            H._red_v1_sources, H._RED["folded"], H._RED_DEFAULT, H._CACHE_DEFAULT, sys.argv[0] = real
            os.environ.update(seams)
        self.assertEqual(self.memory(), {}, "a push's fold wrote a law's fixture memory")
        self.assertEqual(H._red_fold(found, self.say), 2)
        mem = self.memory()
        self.assertEqual(mem["ka"]["ids"], ["A.test_new"], "the newer 'at' did not win")
        self.assertEqual(mem["kb"]["ids"], ["B.test_b"])


RED_PROOF = [
    {
        "why": "REG-1710 - a narrowed tampered run that stays GREEN is credited as a proof: a blind law reads PROVEN",
        "file": "heart2.py",
        "find": "    if ok_t is False:\n        say(",
        "replace": "    if True:\n        say(",
        "matches": 1,
    },
    {
        "why": "REG-1710 - the narrowed clean run is not required green, so a vanished case errors red and is credited",
        "file": "heart2.py",
        "find": "    if ok_c is not True:\n        return None\n",
        "replace": "    if False:\n        return None\n",
        "matches": 1,
    },
    {
        "why": "REG-1710 - a red full proof stops teaching the memory, so every push pays the full run again",
        "file": "heart2.py",
        "find": "        _red_remember(_rk, name, idx, _LAST_RED.pop(threading.get_ident(), None))",
        "replace": "        pass",
        "matches": 1,
    },
    {
        "why": "R2 - the red memory is a checkout's own again (HERE), and what a worktree learns dies with it",
        "file": "heart2.py",
        "find": "    return os.path.join(os.path.dirname(CACHE if cache is None else cache), _RED_NAME)\n",
        "replace": "    return os.path.join(HERE, _RED_NAME)\n",
        "matches": 1,
    },
    {
        "why": "R2 - idx is back in the key: a proof inserted above re-keys every proof below it",
        "file": "heart2.py",
        "find": "        blob = json.dumps([str(name), f, fi, rp], ensure_ascii=False)\n",
        "replace": "        blob = json.dumps([str(name), int(idx), f, fi, rp], ensure_ascii=False)\n",
        "matches": 1,
    },
    {
        "why": "R2 - no fallback to the pre-R2 key: everything learned before R2 is lost at once",
        "file": "heart2.py",
        "find": "        old = getattr(key, \"legacy\", None)\n",
        "replace": "        old = None\n",
        "matches": 1,
    },
    {
        "why": "R2 - eviction by learn time: a sabotage recalled every push leaves before one nobody has asked for",
        "file": "heart2.py",
        "find": "                max(_num(e.get(\"at\")), _num(e.get(\"usedAt\"))))\n",
        "replace": "                _num(e.get(\"at\")))\n",
        "matches": 1,
    },
    {
        "why": "R2 - a corrupt stamp raises inside the merge, and the memory can never be written again",
        "file": "heart2.py",
        "find": "        if cur is None or _num(e.get(\"at\")) > _num(cur.get(\"at\")):\n",
        "replace": "        if cur is None or (e.get(\"at\") or 0) > (cur.get(\"at\") or 0):\n",
        "matches": 1,
    },
    {
        "why": "R2 - an entry no gate declares any more is kept ahead of live ones",
        "file": "heart2.py",
        "find": "                0 if (live is not None and k not in live) else 1,\n",
        "replace": "                1,\n",
        "matches": 1,
    },
    {
        "why": "R2/R4 - an unreadable memory is written over, and every sabotage it held is lost",
        "file": "heart2.py",
        "find": "    try:\n        os.replace(path, aside)\n    except FileNotFoundError:\n",
        "replace": "    try:\n        pass\n    except FileNotFoundError:\n",
        "matches": 1,
    },
    {
        "why": "R2 - a worktree's own memory is never found, so what it learned before R2 is never folded in",
        "file": "heart2.py",
        "find": "            names = sorted(os.listdir(wt))\n",
        "replace": "            names = []\n",
        "matches": 1,
    },
    {
        "why": "R2 - a law that drives prove(push=True) in-process folds his checkouts' memories",
        "file": "heart2.py",
        "find": "    if not _is_prover_process():\n        return 0\n",
        "replace": "    if False:\n        return 0\n",
        "matches": 1,
    },
    {
        "why": "R2 - a push's automatic fold reaches a law's fixture memory (his checkouts' memories leak into a test)",
        "file": "heart2.py",
        "find": "    if (os.environ.get(\"HEART2_RED_PATH\") or os.environ.get(\"HEART2_CACHE_PATH\") or RED_MEMORY != _RED_DEFAULT\n",
        "replace": "    if (os.environ.get(\"HEART2_RED_PATH\") or os.environ.get(\"HEART2_CACHE_PATH\")\n",
        "matches": 1,
    },
    {
        "why": "REG-1710 - the memory is consulted outside push time too",
        "file": "heart2.py",
        "find": "    _rk = _red_key(name, idx, pr) if (_PUSH is not None and not _script and not _extra and not clean_only) else None\n",
        "replace": "    _rk = _red_key(name, idx, pr) if (not _script and not _extra and not clean_only) else None\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
