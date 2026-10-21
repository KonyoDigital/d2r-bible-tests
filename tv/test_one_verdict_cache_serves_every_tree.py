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

R10 (REG-2340, 2026-10-21) - THE SHARED PATH RESOLVES EVERY WORKTREE SHAPE, AND SAYS WHEN IT CANNOT. The store is now
<git common dir>/heart2/, read from the files git itself reads: a relative gitdir is joined to the CHECKOUT (the first
cut normalised it against the cwd), the gitdir's `commondir` names the common dir (so a bare repository's worktree
resolves too), and a real `git worktree add` - absolute and relative - lands exactly where `git rev-parse
--git-common-dir` says. A pointer that will not read falls back to this checkout's own tv/.heart2_v2/, and the store's
opener SAYS so. REG-2343: the gate ledger is the machine's too - the main checkout's tv/, found the same way - while its
input map stays the checkout's. REG-2344: on that one ledger a FAIL in any tree takes the gate's PASS out whatever a
lookup could say at the time - a FAIL recorded while git cannot answer never leaves a PASS that carries on the very
bytes that just failed.
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
import gate_ledger as GL  # noqa: E402

HOOK = os.path.join(os.path.dirname(HERE), "hooks", "pre-push")


def _quiet(*a, **k):
    pass


class _NoGitEnv(object):
    """A temp repo's git must never answer for another tree: a hook's leaked GIT_DIR flipped his live repo to
    core.bare=true on 2026-10-21. Every GIT_* variable leaves os.environ for the block (the ledger's own git calls run
    inside it), and so do the seams that would steer the ledger - then all of it is put back."""
    STEER = ("GITHUB_ACTIONS", "GATE_LEDGER", "TV_GATE_LEDGER", "TV_GATE_LEDGER_SHA")

    def __enter__(self):
        self.old = dict((k, v) for k, v in os.environ.items() if k.startswith("GIT_") or k in self.STEER)
        for k in self.old:
            os.environ.pop(k, None)
        return self

    def __exit__(self, *_e):
        for k in [k for k in os.environ if k.startswith("GIT_") or k in self.STEER]:
            os.environ.pop(k, None)
        os.environ.update(self.old)
        return False


def _git(cwd, *args):
    env = dict((k, v) for k, v in os.environ.items() if not k.startswith("GIT_"))
    p = subprocess.run(["git", "-C", cwd] + list(args), capture_output=True, text=True, env=env, timeout=60)
    if p.returncode != 0:
        raise RuntimeError("git %s: %s" % (" ".join(args), (p.stderr or p.stdout).strip()[-300:]))
    return p.stdout.strip()


def _repo(root, files):
    """A real throwaway repository with one commit holding `files` (repo-relative). -> its root"""
    os.makedirs(root)
    for rel, text in files.items():
        os.makedirs(os.path.dirname(os.path.join(root, rel)), exist_ok=True)
        with io.open(os.path.join(root, rel), "w", encoding="utf-8") as fh:
            fh.write(text)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "law@example.com")
    _git(root, "config", "user.name", "law")
    _git(root, "config", "commit.gpgsign", "false")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "base")
    return root


def _worktree_shape(root, name="wt1", relative=False):
    """A main checkout and one linked worktree, laid out as git lays them out. -> (main, worktree)"""
    main = os.path.join(root, "main")
    wt = os.path.join(root, name)
    gd = os.path.join(main, ".git", "worktrees", name)
    for d in (os.path.join(main, "tv"), gd, os.path.join(wt, "tv")):
        os.makedirs(d)
    with io.open(os.path.join(gd, "commondir"), "w", encoding="utf-8") as fh:
        fh.write("../..\n")
    with io.open(os.path.join(wt, ".git"), "w", encoding="utf-8") as fh:
        fh.write("gitdir: %s\n" % (os.path.relpath(gd, wt) if relative else gd))
    return main, wt


class OneVerdictCacheServesEveryTree(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="h2share.")
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_a_worktree_resolves_its_main_checkouts_cache(self):
        main, wt = _worktree_shape(self.root)
        store = os.path.join(main, ".git", "heart2", ".heart2_cache.json")
        got = H._shared_cache_path(here=os.path.join(wt, "tv"), repo=wt, env={})
        self.assertEqual(got, store, "a worktree banks into its own cache again, where the push in main never reads")
        own = H._shared_cache_path(here=os.path.join(main, "tv"), repo=main, env={})
        self.assertEqual(own, store, "the main checkout lost the machine's cache")
        self.assertEqual(H._shared_cache_path(here=os.path.join(wt, "tv"), repo=wt,
                                              env={"HEART2_CACHE_PATH": "/x/.heart2_cache.json"}), "/x/.heart2_cache.json")

    def test_a_relative_gitdir_resolves_from_the_checkout_not_the_cwd(self):
        """★ R10 - `gitdir: ../main/.git/worktrees/wt2` (git's worktree.useRelativePaths) is relative to the checkout;
        read from any other cwd it still finds main's store"""
        main, wt = _worktree_shape(self.root, "wt2", relative=True)
        cwd = os.getcwd()
        os.chdir(os.path.dirname(os.path.abspath(HERE)))       # anywhere but the worktree's parent
        try:
            got = H._shared_store(here=os.path.join(wt, "tv"), repo=wt)
        finally:
            os.chdir(cwd)
        self.assertEqual(got, (os.path.join(main, ".git", "heart2"), None),
                         "a relative gitdir was read against the cwd, not the checkout: %r" % (got,))

    def test_every_worktree_git_makes_lands_where_git_says_its_common_dir_is(self):
        """★ R10 - a REAL repository and two REAL worktrees (absolute and relative pointers): heart2's common dir is git's
        own `rev-parse --git-common-dir`, and every one of them resolves the one store"""
        with _NoGitEnv():
            main = _repo(os.path.join(self.root, "real"), {"tv/x.py": "X = 1\n"})
            _git(main, "worktree", "add", "-q", "-b", "a", os.path.join(self.root, "wtA"))
            wtb = os.path.join(self.root, "wtB")
            try:
                _git(main, "worktree", "add", "-q", "--relative-paths", "-b", "b", wtb)
            except RuntimeError:                       # a git before 2.48: write the relative pointer by hand
                _git(main, "worktree", "add", "-q", "-b", "b", wtb)
                with io.open(os.path.join(wtb, ".git"), encoding="utf-8") as fh:
                    gd = fh.read().split(":", 1)[1].strip()
                with io.open(os.path.join(wtb, ".git"), "w", encoding="utf-8") as fh:
                    fh.write("gitdir: %s\n" % os.path.relpath(gd, wtb))
            for tree in (main, os.path.join(self.root, "wtA"), wtb):
                said = _git(tree, "rev-parse", "--git-common-dir")
                gits = os.path.realpath(said if os.path.isabs(said) else os.path.join(tree, said))
                common, why = H._git_common_dir(tree)
                self.assertIsNone(why, "%s: %s" % (tree, why))
                self.assertEqual(os.path.realpath(common), gits, "%s: heart2 and git disagree on the common dir" % tree)
                self.assertEqual(os.path.realpath(H._shared_store(repo=tree)[0]), os.path.join(gits, "heart2"))

    def test_a_bare_repositorys_worktree_resolves_and_an_unreadable_pointer_is_said(self):
        """★ R10 - a worktree of a BARE repository resolves through its commondir; a pointer that will not read falls
        back to the checkout's own tv/.heart2_v2/ and the cache's opener SAYS so - a store that dies with its checkout is
        never silent"""
        bare = os.path.join(self.root, "b.git")
        gd = os.path.join(bare, "worktrees", "wtc")
        wtc = os.path.join(self.root, "wtc")
        for d in (gd, os.path.join(wtc, "tv")):
            os.makedirs(d)
        with io.open(os.path.join(gd, "commondir"), "w", encoding="utf-8") as fh:
            fh.write("../..\n")
        with io.open(os.path.join(wtc, ".git"), "w", encoding="utf-8") as fh:
            fh.write("gitdir: %s\n" % gd)
        self.assertEqual(H._shared_store(here=os.path.join(wtc, "tv"), repo=wtc), (os.path.join(bare, "heart2"), None))
        broken = os.path.join(self.root, "broken")
        os.makedirs(os.path.join(broken, "tv"))
        with io.open(os.path.join(broken, ".git"), "w", encoding="utf-8") as fh:
            fh.write("this is not a pointer\n")
        where, why = H._shared_store(here=os.path.join(broken, "tv"), repo=broken)
        self.assertEqual(where, os.path.join(broken, "tv", ".heart2_v2"))
        self.assertIn("not a gitdir pointer", why or "", "the reason the store is the checkout's own is not given")
        said = []
        own = os.path.join(where, ".heart2_cache.json")
        real = (H.CACHE, H.CACHE_WHY)
        H.CACHE, H.CACHE_WHY = own, why
        try:
            H._VerdictCache(say=said.append)
        finally:
            H.CACHE, H.CACHE_WHY = real
        self.assertTrue(any("was not found" in l and "not a gitdir pointer" in l and "dies with the checkout" in l
                            for l in said), "the fallback to this checkout's own store is silent: %s" % said)

    def test_the_gate_ledger_is_the_machines_and_its_input_map_stays_the_checkouts(self):
        """★ REG-2343 - from main and from its worktree, one ledger: main's tv/.gate_ledger.json; a bare repository's
        worktree has no checkout to hold it and says so; the input map is this checkout's own"""
        main, wt = _worktree_shape(self.root)
        want = (os.path.join(main, "tv", ".gate_ledger.json"), None)
        self.assertEqual(GL.ledger_where(root=wt), want, "a worktree's ledger is its own again - it dies with it")
        self.assertEqual(GL.ledger_where(root=main), want)
        bare = os.path.join(self.root, "b.git")
        gd = os.path.join(bare, "worktrees", "w")
        wb = os.path.join(self.root, "wb")
        for d in (gd, os.path.join(wb, "tv")):
            os.makedirs(d)
        with io.open(os.path.join(gd, "commondir"), "w", encoding="utf-8") as fh:
            fh.write("../..\n")
        with io.open(os.path.join(wb, ".git"), "w", encoding="utf-8") as fh:
            fh.write("gitdir: %s\n" % gd)
        path, why = GL.ledger_where(root=wb)
        self.assertEqual(path, os.path.join(GL.HERE, ".gate_ledger.json"))
        self.assertIn("bare repository", why or "")
        real = GL.ledger_where
        GL.ledger_where = lambda root=None: (os.path.join(main, "tv", ".gate_ledger.json"), None)
        try:
            with _NoGitEnv():
                book = GL.Ledger()
        finally:
            GL.ledger_where = real
        self.assertEqual(book.path, os.path.join(main, "tv", ".gate_ledger.json"))
        self.assertEqual(book._map_file(), os.path.join(GL.HERE, ".gate_inputs.json"),
                         "the input map followed the shared ledger - two trees would rebuild it on every alternation")

    def test_a_fail_drops_the_pass_even_while_git_cannot_answer(self):
        """★ REG-2344 - REAL git, one machine ledger shared by main and a worktree. A FAIL takes the gate's PASS out
        whatever a lookup could say at that moment: recorded while `git cat-file` fails (what _git returns on a timeout
        or a fork error - lookup reads 'the proven sha cannot be diffed'), an untraced FAIL and a traced one each leave
        no PASS that carries once git answers again - on the very bytes that just failed. (The T1 review measured the
        first cut keeping the row on every lookup miss, and carrying it on the failed bytes on the next healthy run.)"""
        law = "import helper_x\nimport sys\nsys.exit(0)\n"
        probes = {"python": "3.9.9", "node": "v20.0.0", "playwright": "1.40.0"}
        facts = {"R": set(), "W": set(), "S": set(), "L": set(), "I": set()}
        arm = os.path.join(self.root, "arm.json")
        with _NoGitEnv():
            os.environ["TV_SELF_ARMING_LEDGER"] = arm
            try:
                main = _repo(os.path.join(self.root, "lm"), {"tv/t_x.py": law, "tv/helper_x.py": "SALT = 1\n",
                                                             ".gitignore": ".gate_ledger.json\n.gate_inputs.json\n"
                                                                           "*.tmp\n.gate_ledger.json.*\n"})
                wt = os.path.join(self.root, "lw")
                _git(main, "worktree", "add", "-q", "-b", "side", wt)
                led, why = GL.ledger_where(root=wt)
                there, why2 = GL.ledger_where(root=main)
                self.assertEqual((os.path.realpath(led), why), (os.path.realpath(there), why2),
                                 "PREMISE: the two trees do not share a ledger")
                self.assertEqual(os.path.realpath(led), os.path.realpath(os.path.join(main, "tv", ".gate_ledger.json")))

                class _G(object):
                    def __init__(self, root):
                        self.name, self.timeout, self.cwd = "x-law", 30, root
                        self.argv = [sys.executable, os.path.join(root, "tv", "t_x.py")]
                        self.needs_app, self.skip_ok = False, ()

                gw = _G(wt)
                real_git = GL._git

                def no_cat_file(root, args):
                    return None if (args and args[0] == "cat-file") else real_git(root, args)

                for how, trace in (("an untraced", None), ("a traced", facts)):
                    self.assertTrue(GL.Ledger(path=led, probes=probes).record(gw, True, trace=dict(facts)),
                                    "PREMISE: the worktree's PASS was not stored")
                    entry, why = GL.Ledger(path=led, probes=probes).lookup(gw)
                    self.assertIsNotNone(entry, "PREMISE: the stored PASS does not carry on its own bytes: %s" % why)
                    book = GL.Ledger(path=led, probes=probes)
                    GL._git = no_cat_file
                    try:
                        self.assertEqual(book.lookup(gw)[1], "the proven sha cannot be diffed",
                                         "PREMISE: the failing git is not what lookup saw")
                        book.record(gw, False, trace=dict(trace) if trace else None)
                    finally:
                        GL._git = real_git
                    entry, why = GL.Ledger(path=led, probes=probes).lookup(gw)
                    self.assertIsNone(entry, "%s FAIL recorded while git could not answer left the PASS standing - it "
                                             "now carries on the bytes that just FAILED: %s" % (how, entry and
                                                                                              entry.get("line")))
                    entries, lwhy = GL.load(led)
                    self.assertNotIn("x-law", entries or {}, "%s FAIL left the PASS row in the ledger" % how)
            finally:
                GL._git = real_git
                os.environ.pop("TV_SELF_ARMING_LEDGER", None)

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
     "find": "        return os.path.join(common, \"heart2\"), None\n",
     "replace": "        return os.path.join(here, \".heart2_v2\"), None\n",
     "matches": 1},
    {"why": "#242 - a cache write overwrites what another prover banked since it loaded",
     "file": "heart2.py",
     "find": "    out = dict((k, v) for k, v in (disk or {}).items() if isinstance(v, dict))\n    for k, e in (mine or {}).items():\n",
     "replace": "    out = {}\n    for k, e in (mine or {}).items():\n",
     "matches": 1},
    {"why": "R10 - a relative gitdir is read against the cwd again, and a worktree misses main's store",
     "file": "heart2.py",
     "find": "                gitdir = os.path.join(repo, gitdir)          # R10 - relative to the checkout, never the cwd\n",
     "replace": "                gitdir = os.path.abspath(gitdir)\n",
     "matches": 1},
    {"why": "R10 - the gitdir's commondir is ignored: a worktree's store is its own admin dir, never the machine's",
     "file": "heart2.py",
     "find": "            common = os.path.normpath(rel if os.path.isabs(rel) else os.path.join(gitdir, rel))\n",
     "replace": "            common = gitdir\n",
     "matches": 1},
    {"why": "R10 - a store that falls back to this checkout's own is silent about it",
     "file": "heart2.py",
     "find": "        if self.path == CACHE and CACHE_WHY:\n",
     "replace": "        if False:\n",
     "matches": 1},
    {"why": "REG-2343 - the gate ledger is per checkout again: a fresh worktree carries nothing, its PASSes die with it",
     "file": "gate_ledger.py",
     "find": "    if common and os.path.basename(common) == \".git\":\n",
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "REG-2343 - the input map follows the shared ledger, so two trees rebuild it on every alternation",
     "file": "gate_ledger.py",
     "find": "        return os.path.join(self._map_dir or os.path.dirname(self.path) or \".\", MAP_NAME)\n",
     "replace": "        return os.path.join(os.path.dirname(self.path) or \".\", MAP_NAME)\n",
     "matches": 1},
    {"why": "REG-2344 - a FAIL drops the PASS only when lookup says it would carry: a traced FAIL recorded while git "
            "cannot answer leaves the PASS, which then carries on the bytes that just failed",
     "file": "gate_ledger.py",
     "find": "            self._drop(name)  # LEDGER-NO-FAIL: a FAIL never stays a PASS row\n",
     "replace": "            self._drop(name) if self.lookup(gate)[0] is not None else None  # LEDGER-NO-FAIL\n",
     "matches": 1},
    {"why": "REG-2344 - a drop takes nothing out of the machine's ledger, so every FAIL leaves its PASS standing",
     "file": "gate_ledger.py",
     "find": "        self.entries.pop(name, None)  # LEDGER-DROP-FAIL\n",
     "replace": "        self.entries.get(name, None)  # LEDGER-DROP-FAIL\n",
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
