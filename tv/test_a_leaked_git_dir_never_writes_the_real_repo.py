# -*- coding: utf-8 -*-
"""REG-2360 — A TEST RUN WITH A LEAKED GIT_DIR NEVER WRITES THE REAL REPO, AND NEVER SETS core.bare.

⚠ WHAT IT COST. Inside a git hook, git exports GIT_DIR - absolute, `<main>/.git/worktrees/<name>` when the push comes
from a linked worktree - and GIT_DIR beats cwd= (and -C) in every git child. On the v3783 pushes (2026-10-21) a law that
builds a temp repo committed two fixture commits onto the push branch, so the commit-stamps law read a half-bumped HEAD
and refused pushes #10 and #11; and a `git init` in a temp dir re-initialised the REAL repo's common config to
core.bare=true - his main checkout answered "this operation must be run in a work tree" to every git command for 2.5 h,
and his console's pull lane failed, before anyone looked. Measured again for this law on a fixture standing in for his
repo: each of the first five laws below, unscrubbed, either moved the worktree branch or set core.bare=true (or both);
the sixth is test_control's grok-seat case, the one that committed onto his push branch that night.

THE CLASS FIX IS THE HOOK. hooks/pre-push reads the one thing it needs from that pointer (the git dir), then unsets
every variable git itself calls local to a repository (`git rev-parse --local-env-vars`, plus GIT_DIR / GIT_WORK_TREE /
GIT_INDEX_FILE by name) before any stage runs. The commit-stamps law reached the pushed commit ONLY through that leak
inside heart2's sandbox (a copy with no .git), so the hook hands it the commit by name instead: TV_PUSHED_GIT_DIR +
TV_PUSHED_COMMIT. And each law that builds a temp repo scrubs GIT_* for its OWN scope (a module-wide strip once made the
commit-stamps law skip), so a run outside the hook - by hand, from another hook, a census - is safe as well.

REG-2394 / REG-2395 (the cross-family review of Push A2, 2026-10-22). The first cut unset GIT_CONFIG_PARAMETERS and
GIT_CONFIG_COUNT with the pointer - git's list names them - and they are how `git -c k=v push` reaches a hook: MEASURED
on a throwaway repo, `git -c push.default=upstream push origin HEAD:main` had @{push} = origin/main before the loop and
"cannot resolve" after it, so every stage after the scrub ran without the push's own options. They carry options, never
a pointer, and they stay. And the tv-suites lane asked `git diff @{push}..` with no fallback and no word: on a branch
whose @{push} does not resolve (his push branches track origin/main and push as HEAD:main) every suite in it was
skipped in silence. The hook now asks the range once, at the top (@{push}, else origin/main), and the lane RUNS when the
range is unknown and names the range it read. Both are driven here: a REAL `git -c` push through a hook built from the
hook's own marked blocks, and the lane's three outcomes on fixture branches shaped like his.

These cases DRIVE all three halves against a FIXTURE repo with a linked worktree, leaked exactly the way git leaks it:
the hook's marked blocks in a real bash, the commit-stamps law on a named fixture commit, and every temp-repo law
run whole under GIT_DIR=<the fixture worktree's git dir>, after which the fixture must be byte-for-byte what it was.
Its reach, stated: the 14 other laws that `git init` a temp dir (test_a_suite_run_is_reused_only_on_identical_bytes,
test_a_version_bump_carries_..., test_the_eye_reads_the_commit_read_only, ...) are covered at push time by the hook's
scrub, not by a scope-scrub of their own - not swept here, because each edit would put a law in a push's proving set.
[[regression-guard]] [[feedback-fixtures-never-touch-live-data]] RED_PROOF below.
"""
import ast
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()       # these print non-ASCII; a cp1255 console must not crash while REPORTING
except Exception:
    pass

#: a literal path, so the heart keys this law on the hook's bytes (a join of "hooks" and "pre-push" names no file)
HOOK_REL = "hooks/pre-push"
HOOK = os.path.join(ROOT, *HOOK_REL.split("/"))

#: the laws that build a temp repo, with the unittest selection each is driven through: the first five were each
#: MEASURED writing the fixture when unscrubbed, the sixth wrote his real push branch on the v3783 pushes. File names
#: are literals so the heart keys this law on their bytes.
TEMP_REPO_LAWS = (
    ("test_the_author_is_read_from_the_stamp.py", "test_the_author_is_read_from_the_stamp"),
    ("test_a_landed_update_is_not_an_edit.py", "test_a_landed_update_is_not_an_edit.TheLauncherUsesTheSameRule"),
    ("test_a_proven_verdict_is_reused_only_on_identical_bytes.py",
     "test_a_proven_verdict_is_reused_only_on_identical_bytes.TheKeyNamesEveryInput"
     ".test_a_named_file_git_does_not_track_is_not_a_key_input"),
    ("test_every_pc_proves_itself.py", "test_every_pc_proves_itself.TheTreeIsToldApart"),
    ("test_a_stale_git_lock_is_cleared_and_said.py", "test_a_stale_git_lock_is_cleared_and_said"),
    ("test_control.py", "test_control.TestV2143TheSecondEyeCannotBeSkippedQuietly"
                        ".test_a_claude_look_counts_when_the_commit_is_the_grok_seat"),
)
#: the variables a hook must not hand a stage (git's own list is asked at run time; these three by name)
POINTERS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE")
#: REG-2394 - on git's list, but they carry the push's own `git -c` options, never a pointer: the scrub keeps them
CARRIERS = ("GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT")
#: the fixture's git never reads his global or system config (a push.default there would decide @{push} for it)
_HERMETIC = {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_TERMINAL_PROMPT": "0"}
_IDENT = ["-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false",
          "-c", "init.defaultBranch=main"]


def _clean_env(**extra):
    """os.environ without one GIT_* variable, plus `extra` - a child run gets exactly the leak it is handed. -> dict"""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(extra)
    return env


def _git(*args, **kw):
    """the fixture's own git: never his global or system config, never a prompt"""
    r = subprocess.run(["git"] + _IDENT + list(args), capture_output=True, text=True, timeout=60,
                       env=_clean_env(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0"),
                       **kw)
    if r.returncode != 0:
        raise AssertionError("fixture git %s failed: %s" % (" ".join(args), (r.stderr or "").strip()[-300:]))
    return (r.stdout or "").strip()


def _sha(path):
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        return None


class _Fixture(object):
    """A repo standing in for HIS: one commit, and a linked worktree whose git dir is what the hook would leak."""

    def __init__(self, root):
        self.real = os.path.join(root, "real")
        self.wt = os.path.join(root, "wt")
        os.makedirs(self.real)
        _git("init", "-q", self.real)
        with io.open(os.path.join(self.real, "f.txt"), "w", encoding="utf-8") as fh:
            fh.write(u"one\n")
        _git("-C", self.real, "add", "f.txt")
        _git("-C", self.real, "commit", "-q", "-m", "one")
        _git("-C", self.real, "worktree", "add", "-q", self.wt, "-b", "wtb")
        self.gitdir = os.path.realpath(_git("-C", self.wt, "rev-parse", "--absolute-git-dir"))

    def state(self):
        """Every write a fixture git call could make shows here: refs, objects, the common config, both indexes."""
        return {
            "refs": _git("-C", self.real, "for-each-ref", "--format=%(refname) %(objectname)"),
            "objects": _git("-C", self.real, "count-objects", "-v"),
            "wtHEAD": _git("--git-dir=" + self.gitdir, "rev-parse", "HEAD"),
            "bare": _git("-C", self.real, "config", "--get", "core.bare"),
            "config": _sha(os.path.join(self.real, ".git", "config")),
            "index": _sha(os.path.join(self.real, ".git", "index")),
            "wtIndex": _sha(os.path.join(self.gitdir, "index")),
        }


class _PushFixture(object):
    """REG-2395 - a repo standing in for HIS with a bare remote standing in for GitHub (main pushed there), and a linked
    worktree on a branch that TRACKS origin/main - his push branches' shape: under push.default=simple its @{push} does
    not resolve ("cannot resolve 'simple' push to a single destination"). remote=False: no remote at all."""

    def __init__(self, root, remote=True):
        self.real = os.path.join(root, "real")
        self.wt = os.path.join(root, "wt")
        self.remote = os.path.join(root, "remote.git") if remote else None
        os.makedirs(self.real)
        _git("init", "-q", self.real)
        with io.open(os.path.join(self.real, "f.txt"), "w", encoding="utf-8") as fh:
            fh.write(u"one\n")
        _git("-C", self.real, "add", "f.txt")
        _git("-C", self.real, "commit", "-q", "-m", "one")
        if remote:
            _git("init", "-q", "--bare", self.remote)
            _git("-C", self.real, "remote", "add", "origin", self.remote)
            _git("-C", self.real, "push", "-q", "origin", "main")
            _git("-C", self.real, "fetch", "-q", "origin")
        _git("-C", self.real, "worktree", "add", "-q", self.wt, "-b", "wtb")
        if remote:
            _git("-C", self.wt, "branch", "-q", "--set-upstream-to=origin/main")

    def commit(self, rel):
        """one commit on the worktree branch that changes `rel` (repo-relative)"""
        p = os.path.join(self.wt, *rel.split("/"))
        if not os.path.isdir(os.path.dirname(p)):
            os.makedirs(os.path.dirname(p))
        with io.open(p, "a", encoding="utf-8") as fh:
            fh.write(u"x\n")
        _git("-C", self.wt, "add", rel)
        _git("-C", self.wt, "commit", "-q", "-m", "change " + rel)


def _bash():
    import posix_shell as _PS   # REG-1642 - a real POSIX bash; on a Windows PC `bash` is the WSL launcher
    return _PS.bash()


def _block(name):
    with io.open(HOOK, encoding="utf-8") as fh:
        src = fh.read()
    i = src.index("# >>> %s\n" % name)
    j = src.index("# <<< %s\n" % name, i)
    return src[i:j], src[:i].count("\n")


class _Case(unittest.TestCase):

    def setUp(self):
        # this law builds repos too: under a hook's leak its own fixture git calls must not reach the real one
        _gitenv = {_k: os.environ.pop(_k) for _k in list(os.environ) if _k.startswith("GIT_")}
        self.addCleanup(os.environ.update, _gitenv)
        self.root = tempfile.mkdtemp(prefix="leaked_gitdir_")
        self.addCleanup(shutil.rmtree, self.root, True)


class ATempRepoLawNeverWritesTheRealRepo(_Case):

    def test_every_temp_repo_law_passes_under_a_leaked_git_dir_and_leaves_the_repo_as_it_was(self):
        """★ each law, run WHOLE under GIT_DIR=<the fixture worktree's git dir>: green, and the fixture unchanged -
        no commit on the branch, no object, no index write, and core.bare still false"""
        for fname, selection in TEMP_REPO_LAWS:
            with self.subTest(law=fname):
                self.assertTrue(os.path.isfile(os.path.join(HERE, fname)), "PREMISE: %s is gone" % fname)
                fx = _Fixture(os.path.join(self.root, fname[:-3]))
                before = fx.state()
                self.assertEqual(before["bare"], "false", "PREMISE: the fixture repo starts bare")
                r = subprocess.run([sys.executable, "-B", "-m", "unittest", selection], cwd=HERE,
                                   capture_output=True, text=True, timeout=600, encoding="utf-8", errors="replace",
                                   env=_clean_env(GIT_DIR=fx.gitdir))
                after = fx.state()
                moved = sorted(k for k in before if before[k] != after[k])
                self.assertEqual(moved, [], "%s WROTE the repo its leaked GIT_DIR points at (%s moved; core.bare is "
                                            "now %r) - in a push that is his live checkout:\n%s"
                                 % (fname, ", ".join(moved), after["bare"], (r.stderr or "")[-1500:]))
                self.assertEqual(r.returncode, 0, "%s is RED under a leaked GIT_DIR (a git answer about its temp "
                                                  "dir came from the real repo):\n%s" % (fname, (r.stderr or "")[-2000:]))
                self.assertRegex(r.stderr or "", r"Ran [1-9]\d* tests?",
                                 "%s ran nothing - a selection that matches no test proves nothing" % fname)

    def test_each_scrub_is_scoped_to_a_test_never_the_module(self):
        """a module-wide strip of GIT_* made the commit-stamps law skip inside heart2's sandbox (push #12); each scrub
        sits in a function and is put back by addCleanup"""
        for fname, _sel in TEMP_REPO_LAWS:
            with io.open(os.path.join(HERE, fname), encoding="utf-8") as fh:
                src = fh.read()
            with warnings.catch_warnings():          # test_control's own escape sequences are not this law's finding
                warnings.simplefilter("ignore")
                tree = ast.parse(src)
            scoped, loose = 0, []
            for node in tree.body:
                funcs = [n for n in ast.walk(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                if not funcs:
                    if "startswith" in ast.dump(node) and "'GIT_'" in ast.dump(node):
                        loose.append(getattr(node, "lineno", 0))
                    continue
                for f in funcs:
                    body = ast.dump(f)
                    if "'GIT_'" in body and "attr='pop'" in body and "addCleanup" in body:
                        scoped += 1
            self.assertEqual(loose, [], "%s strips GIT_* at MODULE level (line %s)" % (fname, loose))
            self.assertGreaterEqual(scoped, 1, "%s builds a temp repo and scrubs GIT_* in no test's scope" % fname)


class TheHookUnsetsThePointerBeforeAnyStage(_Case):

    def test_the_scrub_block_unsets_every_pointer_and_names_the_git_dir(self):
        bash = _bash()
        if bash is None:
            self.skipTest("no real POSIX bash on this PC - the hook's scrub is UNMEASURED, not passing")
        fx = _Fixture(self.root)
        block, _line = _block("scrub-git-env")
        script = block + '\nenv | grep "^GIT_" || true\necho "TV_PUSHED_GIT_DIR=$TV_PUSHED_GIT_DIR"\n'
        r = subprocess.run([bash, "-c", "set -u\n" + script], cwd=fx.wt, capture_output=True, text=True, timeout=60,
                           env=_clean_env(GIT_DIR=fx.gitdir, GIT_WORK_TREE=fx.wt,
                                          GIT_INDEX_FILE=os.path.join(fx.gitdir, "index"),
                                          GIT_COMMON_DIR=os.path.join(fx.real, ".git")))
        self.assertEqual(r.returncode, 0, "the hook's scrub block did not run - UNKNOWN, not passing: %s" % r.stderr)
        left = sorted(set(re.findall(r"^(GIT_[A-Z_]+)=", r.stdout, re.M)))
        local = (set(_git("rev-parse", "--local-env-vars").split()) | set(POINTERS)) - set(CARRIERS)
        self.assertEqual(sorted(set(left) & local), [],
                         "the hook hands its stages a pointer at the real repo: %s" % sorted(set(left) & local))
        m = re.search(r"^TV_PUSHED_GIT_DIR=(.*)$", r.stdout, re.M)
        self.assertTrue(m and m.group(1), "the scrub block names no git dir for the commit-stamps law")
        self.assertEqual(os.path.realpath(m.group(1)), fx.gitdir,
                         "TV_PUSHED_GIT_DIR is not the git dir the push came from")

    def test_the_scrub_comes_before_the_first_stage(self):
        with io.open(HOOK, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        _b, at = _block("scrub-git-env")
        first = next(i for i, l in enumerate(lines)
                     if not l.lstrip().startswith("#") and ("gate_run \"" in l or 'python3 "$REPO/' in l))
        self.assertLess(at, first, "a stage (line %d) runs before the hook unsets git's pointer (line %d)"
                        % (first + 1, at + 1))


class ThePushsOwnOptionsSurviveTheScrub(_Case):
    """REG-2394 - a `git -c` option reaches the hook in GIT_CONFIG_PARAMETERS (the env form in GIT_CONFIG_COUNT with
    GIT_CONFIG_KEY_i / GIT_CONFIG_VALUE_i). git's --local-env-vars names both carriers and the first cut unset them."""

    def test_the_scrub_block_keeps_the_options_and_still_unsets_every_pointer(self):
        bash = _bash()
        if bash is None:
            self.skipTest("no real POSIX bash on this PC - the hook's scrub is UNMEASURED, not passing")
        fx = _Fixture(self.root)
        block, _line = _block("scrub-git-env")
        script = (block + 'echo "PROBE=[$(git config --get tv.probe)]"\n'
                  'echo "COUNTED=[$(git config --get tv.counted)]"\nenv | grep "^GIT_" || true\n')
        r = subprocess.run([bash, "-c", "set -u\n" + script], cwd=fx.wt, capture_output=True, text=True, timeout=60,
                           env=_clean_env(GIT_DIR=fx.gitdir, GIT_INDEX_FILE=os.path.join(fx.gitdir, "index"),
                                          GIT_CONFIG_PARAMETERS="'tv.probe'='kept'", GIT_CONFIG_COUNT="1",
                                          GIT_CONFIG_KEY_0="tv.counted", GIT_CONFIG_VALUE_0="yes", **_HERMETIC))
        self.assertEqual(r.returncode, 0, "the hook's scrub block did not run - UNKNOWN, not passing: %s" % r.stderr)
        self.assertIn("PROBE=[kept]", r.stdout, "a `git -c` option is gone after the scrub - every later stage runs "
                                                "without the push's own options:\n%s" % r.stdout)
        self.assertIn("COUNTED=[yes]", r.stdout, "a GIT_CONFIG_COUNT option is gone after the scrub:\n%s" % r.stdout)
        left = set(re.findall(r"^(GIT_[A-Z0-9_]+)=", r.stdout, re.M))
        self.assertEqual(sorted(left & {"GIT_DIR", "GIT_INDEX_FILE"}), [],
                         "keeping the options let a pointer through: %s" % sorted(left))

    def test_a_real_git_c_push_keeps_its_options_past_the_scrub(self):
        """★ on a throwaway repo: a REAL `git -c push.default=upstream -c tv.probe=kept push origin HEAD:main` (plus
        the env form) from a linked worktree whose branch tracks origin/main, through a hook made of the real hook's
        push-range and scrub blocks - after the scrub git still answers both options, @{push} is origin/main, the push
        base is origin/main's commit, and no pointer is left. The fixture hook refuses, so nothing reaches the remote."""
        if _bash() is None:
            self.skipTest("no real POSIX bash on this PC - git cannot run the hook; UNMEASURED, not passing")
        fx = _PushFixture(self.root)
        fx.commit("tv/x.py")
        hooks = os.path.join(self.root, "hooks")
        os.makedirs(hooks)
        rng, _l1 = _block("push-range")
        scrub, _l2 = _block("scrub-git-env")
        hook = os.path.join(hooks, "pre-push")
        with io.open(hook, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(u"#!/usr/bin/env bash\nset -u\n" + rng + scrub
                     + u'echo "PROBE=[$(git config --get tv.probe)]"\n'
                       u'echo "COUNTED=[$(git config --get tv.counted)]"\n'
                       u"echo \"PUSH=[$(git rev-parse --abbrev-ref '@{push}' 2>&1)]\"\n"
                       u'echo "BASE=[$TV_PUSH_BASE]"\n'
                       u'env | grep "^GIT_" | sed "s/^/LEFT /"\n'
                       u"exit 1\n")
        os.chmod(hook, 0o755)
        _git("-C", fx.real, "config", "core.hooksPath", hooks)
        on_remote = _git("-C", fx.remote, "rev-parse", "main")
        r = subprocess.run(["git", "-c", "push.default=upstream", "-c", "tv.probe=kept", "push", "origin", "HEAD:main"],
                           cwd=fx.wt, capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace",
                           env=_clean_env(GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="tv.counted",
                                          GIT_CONFIG_VALUE_0="yes", **_HERMETIC))
        out = (r.stdout or "") + (r.stderr or "")
        self.assertIn("PROBE=[", out, "PREMISE: git never ran the fixture hook:\n%s" % out[-800:])
        self.assertNotEqual(r.returncode, 0, "PREMISE: the fixture hook refuses every push:\n%s" % out[-800:])
        self.assertIn("PROBE=[kept]", out, "the push's own `git -c` option is gone after the scrub - every stage after "
                                           "it runs without it:\n%s" % out[-1500:])
        self.assertIn("COUNTED=[yes]", out, "the push's GIT_CONFIG_COUNT option is gone after the scrub:\n%s"
                      % out[-1500:])
        self.assertIn("PUSH=[origin/main]", out, "after the scrub @{push} no longer resolves - push.default=upstream "
                                                 "was lost with GIT_CONFIG_PARAMETERS:\n%s" % out[-1500:])
        self.assertIn("BASE=[%s]" % _git("-C", fx.wt, "rev-parse", "origin/main"), out,
                      "the push base is not origin/main's commit:\n%s" % out[-1500:])
        left = set(re.findall(r"^LEFT (GIT_[A-Z0-9_]+)=", out, re.M))
        self.assertIn("GIT_CONFIG_PARAMETERS", left, "PREMISE: git handed this hook no `git -c` options at all")
        local = (set(_git("rev-parse", "--local-env-vars").split()) | set(POINTERS)) - set(CARRIERS)
        self.assertEqual(sorted(left & local), [], "a pointer at the real repo outlived the scrub: %s" % sorted(left))
        self.assertEqual(_git("-C", fx.remote, "rev-parse", "main"), on_remote, "the fixture push reached its remote")


class TheTvLaneReadsAKnownRangeOrRuns(_Case):
    """REG-2395 - the tv-suites lane's trigger was `git diff --name-only @{push}..` alone: no fallback, no word. These
    drive the hook's push-range and tv-lane blocks in bash on fixture branches shaped like his."""

    def _lane(self, cwd):
        bash = _bash()
        if bash is None:
            self.skipTest("no real POSIX bash on this PC - the hook's tv lane is UNMEASURED, not passing")
        rng, _l1 = _block("push-range")
        lane, _l2 = _block("tv-lane")
        script = "set -u\n_pp_el() { printf '0m00s'; }\n" + rng + lane + 'echo "LANE=[$_tv_lane]"\n'
        r = subprocess.run([bash, "-c", script], cwd=cwd, capture_output=True, text=True, timeout=60,
                           encoding="utf-8", errors="replace", env=_clean_env(**_HERMETIC))
        self.assertEqual(r.returncode, 0, "the hook's tv-lane blocks did not run - UNKNOWN, not passing: %s" % r.stderr)
        m = re.search(r"^LANE=\[(.*)\]$", r.stdout, re.M)
        self.assertIsNotNone(m, "the lane decided nothing: %r" % r.stdout)
        return m.group(1), r.stdout

    def test_a_branch_whose_push_does_not_resolve_reads_origin_main(self):
        """★ his push branches' shape: @{push} fails, so the old trigger matched nothing and skipped all six suites"""
        fx = _PushFixture(self.root)
        fx.commit("tv/x.py")
        old = subprocess.run(["git", "-C", fx.wt, "diff", "--name-only", "@{push}.."], capture_output=True, text=True,
                             timeout=60, env=_clean_env(**_HERMETIC))
        self.assertNotEqual(old.returncode, 0, "PREMISE: @{push} resolves in this fixture, so it cannot show the old "
                                               "trigger's silent skip")
        lane, out = self._lane(fx.wt)
        self.assertEqual(lane, "touched", "a tv/*.py change on a branch whose @{push} does not resolve did not run the "
                                          "tv suites from origin/main:\n%s" % out)
        self.assertIn("tv/ python touched in origin/main..HEAD", out, "the lane does not name the range it read:\n%s"
                      % out)

    def test_an_unknown_range_runs_the_lane_and_says_so(self):
        """no @{push} and no origin/main: nobody can tell whether tv/ python changed, so the suites RUN"""
        fx = _PushFixture(self.root, remote=False)
        fx.commit("docs.txt")
        lane, out = self._lane(fx.wt)
        self.assertEqual(lane, "unknown", "an UNKNOWN push range skipped the tv suites:\n%s" % out)
        self.assertIn("UNKNOWN range is never a skip", out, "the lane ran on an unknown range without saying so:\n%s"
                      % out)

    def test_a_known_range_says_whether_the_lane_runs(self):
        """@{push} resolves (push.default=upstream): no tv/*.py in it is a skip SAID with its range; one is a run"""
        fx = _PushFixture(self.root)
        _git("-C", fx.real, "config", "push.default", "upstream")
        fx.commit("docs.txt")
        lane, out = self._lane(fx.wt)
        self.assertEqual(lane, "", "a push with no tv/*.py in a known range ran the tv suites:\n%s" % out)
        self.assertIn("no tv/*.py changed in @{push}..HEAD (@{push} = origin/main)", out,
                      "the lane skipped without a word:\n%s" % out)
        fx.commit("tv/y.py")
        lane, out = self._lane(fx.wt)
        self.assertEqual(lane, "touched", "a tv/*.py change in @{push}..HEAD did not run the tv suites:\n%s" % out)
        self.assertIn("tv/ python touched in @{push}..HEAD", out)


class ThePushedCommitIsHandedOverByName(_Case):

    def _pushed(self, refs, cwd):
        bash = _bash()
        if bash is None:
            self.skipTest("no real POSIX bash on this PC - the hook's pushed-commit block is UNMEASURED, not passing")
        block, _line = _block("pushed-commit")
        script = "_PUSH_REFS=%s\n%s\necho \"TV_PUSHED_COMMIT=$TV_PUSHED_COMMIT\"\n" % (_sq(refs), block)
        r = subprocess.run([bash, "-c", "set -u\n" + script], cwd=cwd, capture_output=True, text=True, timeout=60,
                           env=_clean_env())
        self.assertEqual(r.returncode, 0, "the hook's pushed-commit block did not run: %s" % r.stderr)
        m = re.search(r"^TV_PUSHED_COMMIT=(.*)$", r.stdout, re.M)
        self.assertIsNotNone(m, "the block exported nothing: %r" % r.stdout)
        return m.group(1)

    def test_main_wins_then_the_first_ref_that_ships_then_head(self):
        fx = _Fixture(self.root)
        head = _git("-C", fx.wt, "rev-parse", "HEAD")
        z = "0" * 40
        a, b = "a" * 40, "b" * 40
        self.assertEqual(self._pushed("refs/heads/x %s refs/heads/x %s\nrefs/heads/y %s refs/heads/main %s\n"
                                      % (a, z, b, z), fx.wt), b, "the ref pushed to main is not the pushed commit")
        self.assertEqual(self._pushed("refs/heads/x %s refs/heads/x %s\n" % (a, z), fx.wt), a,
                         "a push with no main ref names no commit")
        self.assertEqual(self._pushed("(delete) %s refs/heads/main %s\nrefs/heads/x %s refs/heads/x %s\n"
                                      % (z, a, a, z), fx.wt), a, "a deletion of main was read as the pushed commit")
        self.assertEqual(self._pushed("(delete) %s refs/heads/main %s\n" % (z, a), fx.wt), head,
                         "a push that ships no bytes does not fall back to HEAD")


def _sq(s):
    return "'" + s.replace("'", "'\"'\"'") + "'"


class TheCommitStampsLawReadsTheNamedCommit(_Case):

    def _commit(self, repo, stamps, msg):
        b, c, t, w = stamps
        os.makedirs(os.path.join(repo, "tv"), exist_ok=True)
        for rel, text in (("bible.html", u"window.D2R_BUILD = {id:'%s', name:'x'};\n" % b),
                          ("tv/control_app.py", u'X = {"ver": "%s"}\n' % c),
                          ("tv/tv_diablo.py", u'VERSION = "%s"\n' % t),
                          ("tv/WINDOWS_SHIP.json", u'{"ver": "%s"}\n' % w)):
            with io.open(os.path.join(repo, rel), "w", encoding="utf-8") as fh:
                fh.write(text)
        _git("-C", repo, "add", "-A")
        _git("-C", repo, "commit", "-q", "-m", msg)
        return _git("-C", repo, "rev-parse", "HEAD")

    def _run(self, gitdir, sha):
        return subprocess.run([sys.executable, "-B", os.path.join(HERE, "test_control.py"),
                               "TestTheStampsAgreeInTheCOMMITNotJustTheWorktree"], cwd=HERE, capture_output=True,
                              text=True, timeout=300, encoding="utf-8", errors="replace",
                              env=_clean_env(TV_PUSHED_GIT_DIR=gitdir, TV_PUSHED_COMMIT=sha))

    def test_a_named_coherent_commit_passes_and_a_named_half_bump_refuses(self):
        repo = os.path.join(self.root, "stamps")
        os.makedirs(repo)
        _git("init", "-q", repo)
        ok = self._commit(repo, ("v0042",) * 4, "coherent")
        half = self._commit(repo, ("v0042", "v0042", "v0042", "v0043"), "half-bumped")
        gd = os.path.join(repo, ".git")
        r = self._run(gd, ok)
        self.assertEqual(r.returncode, 0, "a coherent named commit was refused:\n%s" % r.stderr[-1500:])
        self.assertRegex(r.stderr, r"Ran 2 tests", "the commit-stamps law did not run both of its tests")
        self.assertNotIn("skipped", r.stderr, "the commit-stamps law SKIPPED on a commit it was handed by name")
        r = self._run(gd, half)
        self.assertNotEqual(r.returncode, 0, "a half-bumped commit, handed over by name, passed - the law read "
                                             "something other than the pushed commit")
        self.assertIn("HALF-BUMPED", r.stderr)
        r = self._run(gd, "f" * 40)
        self.assertNotEqual(r.returncode, 0, "a named commit git cannot read was let through")
        self.assertNotIn("skipped", r.stderr, "a named commit git cannot read was a SKIP - the push said which "
                                              "bytes ship, so not reading them is a failure")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-2360 - the hook no longer unsets git's pointer: every stage inherits GIT_DIR pointing at his repo",
        "file": "hooks/pre-push",
        "find": "  unset \"$_pp_v\"\n",
        "replace": "  : \"$_pp_v\"\n",
        "matches": 1,
        "needs": "bash",
    },
    {
        "why": "REG-2360 - the pushed commit is the first ref, not the one pushed to main",
        "file": "hooks/pre-push",
        "find": "  if [ \"$_pc_rr\" = \"refs/heads/main\" ]; then TV_PUSHED_COMMIT=\"$_pc_ls\"; break; fi\n",
        "replace": "",
        "matches": 1,
        "needs": "bash",
    },
    {
        "why": "REG-2360 - the commit-stamps law ignores the commit it was handed and reads HEAD of whatever tree it is in",
        "file": "test_control.py",
        "find": "        if gd and sha:\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        "why": "REG-2360 - the author-stamp law builds its temp repo with the hook's GIT_DIR: commits land on the branch",
        "file": "test_the_author_is_read_from_the_stamp.py",
        "find": "        _gitenv = {_k: os.environ.pop(_k) for _k in list(os.environ) if _k.startswith(\"GIT_\")}\n",
        "replace": "        _gitenv = {}\n",
        "matches": 1,
    },
    {
        "why": "REG-2360 - the stale-lock law's `git init --bare` runs under the leak: core.bare=true on the real config",
        "file": "test_a_stale_git_lock_is_cleared_and_said.py",
        "find": "        _gitenv = {_k: os.environ.pop(_k) for _k in list(os.environ) if _k.startswith(\"GIT_\")}\n",
        "replace": "        _gitenv = {}\n",
        "matches": 1,
    },
    {
        "why": "REG-2360 - TheLauncherUsesTheSameRule builds its repos under the leak (and reads the real repo as its own)",
        "file": "test_a_landed_update_is_not_an_edit.py",
        "find": "        _gitenv = {_k: os.environ.pop(_k) for _k in list(os.environ) if _k.startswith(\"GIT_\")}\n",
        "replace": "        _gitenv = {}\n",
        "matches": 1,
    },
    {
        "why": "REG-2360 - TheTreeIsToldApart's `git init --bare` and commits run under the leak",
        "file": "test_every_pc_proves_itself.py",
        "find": "        _gitenv = {_k: os.environ.pop(_k) for _k in list(os.environ) if _k.startswith(\"GIT_\")}\n",
        "replace": "        _gitenv = {}\n",
        "matches": 1,
    },
    {
        "why": "REG-2360 - the P3 tracked-files case asks git about its throwaway repo under the leak",
        "file": "test_a_proven_verdict_is_reused_only_on_identical_bytes.py",
        "find": "        _gitenv = {_k: os.environ.pop(_k) for _k in list(os.environ) if _k.startswith(\"GIT_\")}\n",
        "replace": "        _gitenv = {}\n",
        "matches": 1,
    },
    {
        "why": "REG-2394 - the scrub unsets the push's own options again: a `git -c` push loses push.default, @{push} "
               "stops resolving, and every stage after the scrub runs without the caller's options",
        "file": "hooks/pre-push",
        "find": "  case \"$_pp_v\" in GIT_CONFIG_PARAMETERS|GIT_CONFIG_COUNT) continue ;; esac\n",
        "replace": "",
        "matches": 1,
        "needs": "bash",
    },
    {
        "why": "REG-2395 - an UNKNOWN push range skips the tv suites again, the way the bare @{push} trigger did",
        "file": "hooks/pre-push",
        "find": "if [ -z \"${TV_PUSH_BASE:-}\" ]; then\n  _tv_lane=\"unknown\"\n",
        "replace": "if [ -z \"${TV_PUSH_BASE:-}\" ]; then\n  _tv_lane=\"\"\n",
        "matches": 1,
        "needs": "bash",
    },
    {
        "why": "REG-2395 - the push range loses its origin/main fallback: a branch whose @{push} does not resolve (his "
               "push branches) reads UNKNOWN instead of the range it ships",
        "file": "hooks/pre-push",
        "find": "elif _pr_b=\"$(git rev-parse --verify --quiet 'origin/main' 2>/dev/null)\" && [ -n \"$_pr_b\" ]; then\n",
        "replace": "elif false; then\n",
        "matches": 1,
        "needs": "bash",
    },
    {
        "why": "REG-2395 - the lane skips in silence again: a push with no tv/*.py says nothing about the six suites",
        "file": "hooks/pre-push",
        "find": "  echo \"pre-push: [$(_pp_el)] \u23ed  no tv/*.py changed in ${TV_PUSH_RANGE:-?} - the tv suites do not run.\"\n",
        "replace": "  :\n",
        "matches": 1,
        "needs": "bash",
    },
]
