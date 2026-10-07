# -*- coding: utf-8 -*-
"""#242 / REG-1996 - ONE VERDICT CACHE PER MACHINE, EVERY ENTRY NAMES ITS TREE, AND A PRE-FLIGHT PROVES THE HOOK'S SET.

MEASURED on the v3602 pushes: every pre-prove run in a worktree banked into that worktree's own tv/.heart2_cache.json,
and the push in main read main's, so the 136 laws the hook proved were proved from nothing while their worktree proofs
sat one directory over. And the pre-prove itself named 17 laws where the hook proved 136. Three rules, each driven here:

  1. a worktree's cache is its MAIN checkout's tv/.heart2_cache.json (found from the worktree's .git pointer file);
  2. every banked entry carries the TREE it was proved in, and the clean wave (REG-1992) skips a gate only when all its
     proofs were banked in the tree being proved - a law reading live state only main holds still gets its clean run;
  3. `heart2.py --changed` / gates_for_tests() answer exactly what the hook's own inline script answers, file for file;
  plus: a cache write MERGES what another prover banked since it loaded, so two provers never erase each other.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2 as H  # noqa: E402

HOOK = os.path.join(os.path.dirname(HERE), "hooks", "pre-push")


def _quiet(*a, **k):
    pass


class OneVerdictCacheServesEveryTree(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="h2share.")
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_a_worktree_resolves_its_main_checkouts_cache(self):
        main = os.path.join(self.root, "main")
        wt = os.path.join(main, ".claude", "worktrees", "wt1")
        os.makedirs(os.path.join(main, "tv"))
        os.makedirs(os.path.join(main, ".git", "worktrees", "wt1"))
        os.makedirs(os.path.join(wt, "tv"))
        with io.open(os.path.join(wt, ".git"), "w", encoding="utf-8") as fh:
            fh.write("gitdir: %s\n" % os.path.join(main, ".git", "worktrees", "wt1"))
        got = H._shared_cache_path(here=os.path.join(wt, "tv"), repo=wt, env={})
        self.assertEqual(got, os.path.join(main, "tv", ".heart2_cache.json"),
                         "a worktree banks into its own cache again, where the push in main never reads")
        own = H._shared_cache_path(here=os.path.join(main, "tv"), repo=main, env={})
        self.assertEqual(own, os.path.join(main, "tv", ".heart2_cache.json"), "the main checkout lost its own cache")
        self.assertEqual(H._shared_cache_path(here=os.path.join(wt, "tv"), repo=wt,
                                              env={"HEART2_CACHE_PATH": "/x/.heart2_cache.json"}), "/x/.heart2_cache.json")

    def test_two_provers_writing_one_cache_never_erase_each_other(self):
        path = os.path.join(self.root, ".heart2_cache.json")
        a = H._VerdictCache(path=path, say=_quiet)
        b = H._VerdictCache(path=path, say=_quiet)          # both loaded the same (empty) file
        a.store("ka", {"verdict": H.PROVEN, "provedAt": 1, "tree": "A"})
        a.flush()
        b.store("kb", {"verdict": H.PROVEN, "provedAt": 2, "tree": "B"})
        b.flush()                                           # the later writer merges what A banked since B loaded
        with io.open(path, encoding="utf-8") as fh:
            ent = json.load(fh)["entries"]
        self.assertEqual(sorted(ent), ["ka", "kb"], "the second prover's write erased the first's entries")

    def test_a_banked_entry_names_its_tree(self):
        src = io.open(os.path.join(HERE, "heart2.py"), encoding="utf-8").read()
        self.assertEqual(src.count('"inputs": rels, "tree": TREE_ID}'), 1, "a banked PROVEN no longer names its tree")
        self.assertEqual(H.TREE_ID, os.path.realpath(H.REPO))

    def test_the_wave_runs_a_gate_whose_proofs_were_banked_in_another_tree(self):
        """Drives the REAL _wave_gate: one gate, its one proof cached - from THIS tree (skipped) and from ANOTHER (run)."""
        tv = os.path.join(self.root, "repo", "tv")
        os.makedirs(tv)
        with io.open(os.path.join(tv, "subject.py"), "w", encoding="utf-8") as fh:
            fh.write('A = "GOOD"\n')
        with io.open(os.path.join(tv, "fake_gate.py"), "w", encoding="utf-8") as fh:
            fh.write("import sys\nsys.exit(0)\n")
        pr = {"file": "subject.py", "find": 'A = "GOOD"', "replace": 'A = "BAD"', "matches": 1, "why": "A"}
        cache = H._VerdictCache(path=os.path.join(self.root, ".heart2_cache.json"), say=_quiet)
        key, _rels, why = cache.key_for(tv, "no-such-gate", "fake_gate.py", pr)
        self.assertIsNotNone(key, "the fixture law cannot be keyed: %s" % why)
        runs = []

        def _run(sandbox_tv, filename, timeout=180, extra=(), script=None, widths=None):
            runs.append(filename)
            return True, "Ran 1 test | OK"

        real = H._run_gate
        self.addCleanup(lambda: setattr(H, "_run_gate", real))
        H._run_gate = _run
        for tree, want in ((H.TREE_ID, 0), ("/some/other/worktree", 1), (None, 1)):
            entry = {"verdict": H.PROVEN, "provedAt": 1}
            if tree is not None:
                entry["tree"] = tree
            cache.entries = {key: entry}
            runs[:] = []
            run = H._PushRun(order={}, browser=(), cache=cache)
            H._wave_gate(tv, "no-such-gate", "fake_gate.py", [pr], _quiet, run)
            self.assertEqual(len(runs), want, "banked in %r: the wave asked %d clean run(s), want %d"
                             % (tree, len(runs), want))

    def test_the_preflight_set_is_the_hooks_own_set(self):
        hook = io.open(HOOK, encoding="utf-8").read()
        i = hook.find("<<'PYGATE'")
        i = hook.find("\n", i) + 1 if i > 0 else -1          # the script starts on the line after the heredoc marker
        j = hook.find("\nPYGATE\n", i)
        self.assertTrue(i > 0 and j > i, "the hook's changed-gate script is gone - the pre-flight has nothing to agree with")
        script = hook[i:j]
        files = ["tv/test_control.py", "tv/test_a_red_law_refuses_before_any_tamper.py",
                 "tv/test_one_clean_run_serves_a_gates_proofs.py", "tv/test_no_such_law_anywhere.py"]
        p = subprocess.run([sys.executable, "-c", script] + files, cwd=os.path.dirname(HERE), capture_output=True,
                           text=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr[-400:])
        hook_set = sorted(p.stdout.split())
        self.assertEqual(H.gates_for_tests(files), hook_set,
                         "heart2 --changed and the hook disagree about which laws a push proves")
        self.assertIn("test_control", hook_set)


RED_PROOF = [
    {"why": "#242 - a worktree banks into its own cache again; the push in main proves from nothing",
     "file": "heart2.py",
     "find": "                    if os.path.isdir(os.path.join(main, \"tv\")):\n",
     "replace": "                    if False:\n",
     "matches": 1},
    {"why": "#242 - a cache write overwrites what another prover banked since it loaded",
     "file": "heart2.py",
     "find": "                    if _k not in self.entries and isinstance(_v, dict) and _v.get(\"verdict\") == PROVEN:\n",
     "replace": "                    if False:\n",
     "matches": 1},
    {"why": "#242 - the wave skips a gate whose proofs were banked in ANOTHER tree, so a main-only red is never run",
     "file": "heart2.py",
     "find": "                if _hit is None or _hit.get(\"tree\") != TREE_ID:\n",
     "replace": "                if _hit is None:\n",
     "matches": 1},
    {"why": "#242 - the pre-flight matches whole paths where the hook matches basenames, and proves a different set",
     "file": "heart2.py",
     "find": "    changed = set(os.path.basename(str(p)) for p in (paths or []))\n",
     "replace": "    changed = set(str(p) for p in (paths or []))\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
