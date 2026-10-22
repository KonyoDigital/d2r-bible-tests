# -*- coding: utf-8 -*-
"""REG-2364 — A SANDBOX BUILT FROM A WORKTREE CARRIES A HISTORY OF ITS OWN, AND NO DOOR BACK TO THE REAL REPO.

⚠ WHAT IT COST. heart2 proves a law in a sandbox: a copy of tv/ plus what the gates declare in PROOF_NEEDS, and
`../.git` is declared, so every sandbox carries a git history. From his MAIN checkout `.git` is a directory and comes
across as a private clone. From a LINKED WORKTREE - where every push now starts - `.git` is a one-line pointer into the
real repo, and make_sandbox rightly refuses to copy a pointer (a door), so the sandbox had NO history at all. Nobody
saw it, because git exports GIT_DIR into a pre-push hook from a worktree (MEASURED on git 2.50: from a worktree
GIT_DIR=<main>/.git/worktrees/<name>, from the main checkout none) and the hook passed it on: every git call a law made
in the sandbox answered from - and could write - the real worktree. REG-2360 made the hook unset it. MEASURED on that
branch, a sandbox from the worktree answered `git rev-parse HEAD` with "not a git repository": test_control's
relaunch case (TestV2153) ERRORED, so its clean run is red and a push that proves test_control is refused; and the
version-stamp law's red-proof [7] went BLIND, because its only catcher (RoutineIOnRealHistory) skips without history.

THE FIX (heart2._share_history, called by make_sandbox for a pointer and off the Mac for a directory): a private
`git clone --shared --no-checkout` of that checkout - HEAD is the worktree's HEAD, the objects are borrowed read-only
through alternates, the refs, index and config are the sandbox's own - made with no GIT_* variable in its environment
(a leaked GIT_DIR made its `read-tree HEAD` rewrite the REAL worktree's index, MEASURED on a fixture), and with the
clone's push url pointed at nothing, because its origin IS the real checkout.

These cases build a FIXTURE - a main repo and a linked worktree one commit ahead, with a staged entry in the worktree's
index - and drive heart2.make_sandbox for real with heart2.REPO pointed at it, the registered gates' own declarations,
and GIT_DIR=<the worktree's git dir> in the prover's environment, exactly as a hook leaks it. They read the history in
the sandbox the way the two casualties do (`git -C <root> rev-parse HEAD`, `git cat-file -e <old commit>`), then try
every write a law could make in there and require the fixture to be byte-for-byte what it was.
[[feedback-fixtures-never-touch-live-data]] [[the-unjoined-end]] RED_PROOF below.
"""
import hashlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()       # these print non-ASCII; a cp1255 console must not crash while REPORTING
except Exception:
    pass
import heart2       # noqa: E402

#: the history every sandbox is handed, as the gates declare it (relative to tv/)
HISTORY_NEED = "../.git"
_IDENT = ["-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false",
          "-c", "init.defaultBranch=main"]


def _clean_env(**extra):
    """os.environ without one GIT_* variable, plus `extra`, and never his global or system git config. -> dict"""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0")
    env.update(extra)
    return env


def _run_git(*args):
    """-> CompletedProcess of a fixture-side git call, whatever its exit"""
    return subprocess.run(["git"] + _IDENT + list(args), capture_output=True, text=True, timeout=120,
                          encoding="utf-8", errors="replace", env=_clean_env())


def _git(*args):
    r = _run_git(*args)
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
    """A repo standing in for HIS: a main checkout with tv/control_app.py (make_sandbox requires it), two commits, and a
    linked worktree one commit ahead with a STAGED entry in its index - the state a build must never disturb."""

    def __init__(self, root):
        self.main = os.path.join(root, "main")
        self.wt = os.path.join(root, "wt")
        os.makedirs(os.path.join(self.main, "tv"))
        _git("init", "-q", self.main)
        with io.open(os.path.join(self.main, "tv", "control_app.py"), "w", encoding="utf-8") as fh:
            fh.write(u"# fixture\n")
        _git("-C", self.main, "add", "-A")
        _git("-C", self.main, "commit", "-q", "-m", "the first commit")
        self.first = _git("-C", self.main, "rev-parse", "HEAD")
        _git("-C", self.main, "commit", "-q", "--allow-empty", "-m", "main's second commit")
        self.main_head = _git("-C", self.main, "rev-parse", "HEAD")
        _git("-C", self.main, "worktree", "add", "-q", self.wt, "-b", "wtb")
        _git("-C", self.wt, "commit", "-q", "--allow-empty", "-m", "the worktree's own commit")
        self.wt_head = _git("-C", self.wt, "rev-parse", "HEAD")
        with io.open(os.path.join(self.wt, "staged.txt"), "w", encoding="utf-8") as fh:
            fh.write(u"staged, not committed\n")
        _git("-C", self.wt, "add", "staged.txt")
        self.gitdir = os.path.realpath(_git("-C", self.wt, "rev-parse", "--absolute-git-dir"))
        self.common = os.path.join(self.main, ".git")

    def state(self):
        """Every write a git call could make into the real repo shows here - its refs (a pushed branch, a moved one),
        its objects, both HEADs, both indexes (the staged entry), the common config and core.bare - asked of git and
        read by name, never by listing a directory (a law that lists one cannot be keyed)."""
        return {
            "refs": _git("-C", self.main, "for-each-ref", "--format=%(refname) %(objectname)"),
            "objects": _git("-C", self.main, "count-objects", "-v"),
            "worktrees": _git("-C", self.main, "worktree", "list", "--porcelain"),
            "HEAD": _sha(os.path.join(self.common, "HEAD")),
            "wtHEAD": _sha(os.path.join(self.gitdir, "HEAD")),
            "config": _sha(os.path.join(self.common, "config")),
            "packed-refs": _sha(os.path.join(self.common, "packed-refs")),
            "index": _sha(os.path.join(self.common, "index")),
            "wtIndex": _sha(os.path.join(self.gitdir, "index")),
            "bare": _git("-C", self.main, "config", "--get", "core.bare"),
        }


_DECLARING = []


def _declaring():
    """The registered gates whose PROOF_NEEDS names the history, by absolute path (heart2 resolves a bare gate name
    against REPO, which build() points at the fixture). Read once, after setUp has taken every GIT_* away. -> list"""
    if not _DECLARING:
        with warnings.catch_warnings():     # other gate files' own escape sequences are not this law's finding
            warnings.simplefilter("ignore")
            for n, fn in heart2.gate_files(say=lambda *a, **k: None):
                fn = fn if os.path.isabs(fn) else os.path.join(HERE, fn)
                if HISTORY_NEED in (heart2.proof_needs_in(fn) or []):
                    _DECLARING.append((n, fn))
    return list(_DECLARING)


class _Case(unittest.TestCase):

    def setUp(self):
        # this law builds repos too: under a hook's leak its own fixture git calls must not reach the real one
        _gitenv = {_k: os.environ.pop(_k) for _k in list(os.environ) if _k.startswith("GIT_")}
        self.addCleanup(os.environ.update, _gitenv)
        self.root = tempfile.mkdtemp(prefix="wt_history_")
        self.addCleanup(heart2._rmtree_hard, self.root)
        self.declaring = _declaring()

    def build(self, repo, leak=None):
        """heart2.make_sandbox for real, with REPO = `repo`, the registered gates that declare the history, and
        GIT_DIR=`leak` in the prover's environment. -> (sandbox repo dir, said lines); dropped when the test ends."""
        said = []
        real = (heart2.REPO, heart2.gate_files)
        heart2.REPO = repo
        heart2.gate_files = lambda say=None: list(self.declaring)
        if leak:
            os.environ["GIT_DIR"] = leak
        try:
            tv, root = heart2.make_sandbox(say=lambda *a, **k: said.append(" ".join(str(x) for x in a)))
        finally:
            os.environ.pop("GIT_DIR", None)
            heart2.REPO, heart2.gate_files = real
        self.assertIsNotNone(root, "PREMISE: the fixture sandbox was not built: %s" % said)
        self.addCleanup(heart2._drop_sandbox, root)
        return os.path.dirname(tv), said


class AWorktreeSandboxReadsItsOwnHistory(_Case):

    def test_the_gates_still_hand_every_sandbox_the_history(self):
        """the premise both casualties stand on: neither declares the history itself - TestV2153 and
        RoutineIOnRealHistory read it because another registered gate's PROOF_NEEDS brings it into every sandbox"""
        self.assertTrue(self.declaring,
                        "no registered gate declares PROOF_NEEDS %r any more, so NO sandbox carries a git history: "
                        "test_control's relaunch case errors on `git rev-parse HEAD` and the version-stamp law's "
                        "red-proof [7] goes BLIND - declare it where it is read" % HISTORY_NEED)

    def test_a_sandbox_from_a_worktree_answers_from_the_worktrees_history(self):
        """★ the blocker: from a linked worktree, under the hook's leaked GIT_DIR, the sandbox reads that worktree's
        HEAD and its whole history - through a git dir of its own, never the pointer"""
        fx = _Fixture(self.root)
        sbx, said = self.build(fx.wt, leak=fx.gitdir)
        dotgit = os.path.join(sbx, ".git")
        self.assertTrue(os.path.isdir(dotgit),
                        "a sandbox built from a worktree holds no git history of its own (%s) - every law that reads "
                        "HEAD there errors or skips once the hook stops leaking GIT_DIR: %s"
                        % ("a pointer FILE: a door to the real worktree" if os.path.isfile(dotgit) else "none", said))
        r = _run_git("-C", sbx, "rev-parse", "HEAD")      # TestV2153's read, from the sandbox root
        self.assertEqual((r.returncode, (r.stdout or "").strip()), (0, fx.wt_head),
                         "`git rev-parse HEAD` in the sandbox did not answer the worktree's HEAD: %r" % (r.stderr,))
        self.assertEqual(_run_git("-C", os.path.join(sbx, "tv"), "cat-file", "-e", fx.first + "^{commit}").returncode,
                         0, "an old commit is not readable in the sandbox - RoutineIOnRealHistory skips, its proof "
                            "goes BLIND")
        gd = os.path.realpath(_git("-C", sbx, "rev-parse", "--absolute-git-dir"))
        self.assertEqual(gd, os.path.realpath(dotgit), "the sandbox's git calls answer from another git dir: %s" % gd)
        cd = os.path.realpath(os.path.join(sbx, _git("-C", sbx, "rev-parse", "--git-common-dir")))
        self.assertEqual(cd, os.path.realpath(dotgit), "the sandbox's refs live outside it: %s" % cd)
        self.assertIn("tv/control_app.py", _git("-C", sbx, "ls-files").split("\n"),
                      "the sandbox's index is empty - `git ls-files` laws read nothing")
        self.assertTrue(os.path.isfile(os.path.join(dotgit, "objects", "info", "alternates")),
                        "the history was COPIED, not borrowed - on his repo that is gigabytes per sandbox")
        self.assertFalse(os.path.exists(dotgit + ".shared"), "the clone's scratch dir was left in the sandbox")

    def test_a_sandbox_from_the_main_checkout_still_carries_its_history(self):
        """BASELINE: a `.git` directory comes across as before, at the main checkout's HEAD - the case tells the two
        shapes apart and the old one is untouched"""
        fx = _Fixture(self.root)
        sbx, said = self.build(fx.main)
        self.assertTrue(os.path.isdir(os.path.join(sbx, ".git")), "a main checkout's sandbox has no history: %s" % said)
        self.assertEqual(_git("-C", sbx, "rev-parse", "HEAD"), fx.main_head,
                         "the main checkout's sandbox answers some other HEAD")
        self.assertFalse(any("worktree POINTER" in l for l in said),
                         "a .git DIRECTORY was handled as a worktree pointer: %s" % said)


class NothingRunInTheSandboxReachesTheRealRepo(_Case):

    def test_building_it_and_writing_in_it_leave_the_real_repo_byte_identical(self):
        """★ no door: the build itself (under the leaked GIT_DIR), then a commit, a push to origin and core.bare=true
        made INSIDE the sandbox - and the real repo (refs, objects, both HEADs, both indexes with the staged entry, the
        common config) is what it was, and the push failed"""
        fx = _Fixture(self.root)
        before = fx.state()
        self.assertEqual(before["bare"], "false", "PREMISE: the fixture repo starts bare")
        sbx, said = self.build(fx.wt, leak=fx.gitdir)
        self.assertEqual(_run_git("-C", sbx, "rev-parse", "HEAD").returncode, 0,
                         "PREMISE: the sandbox holds no history, so nothing below wrote through it: %s" % said)
        built = fx.state()
        self.assertEqual(sorted(k for k in before if before[k] != built[k]), [],
                         "BUILDING the sandbox wrote the real repo (a leaked GIT_DIR reached a git call)")
        _git("-C", sbx, "commit", "-q", "--allow-empty", "-m", "made inside the sandbox")
        push = _run_git("-C", sbx, "push", "origin", "HEAD:refs/heads/from-the-sandbox")
        _git("-C", sbx, "config", "core.bare", "true")
        after = fx.state()
        moved = sorted(k for k in before if before[k] != after[k])
        self.assertEqual(moved, [], "a write made INSIDE the sandbox reached the real repo (%s moved; core.bare is "
                                    "now %s) - in a push that is his live checkout" % (", ".join(moved), after["bare"]))
        self.assertNotEqual(push.returncode, 0, "a push from the sandbox to its origin - the real checkout - "
                                                "succeeded: %s" % (push.stderr or "").strip()[-300:])


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-2364 - a worktree's sandbox gets no history again: once the hook stops leaking GIT_DIR, "
               "TestV2153 errors and the version-stamp law's [7] goes BLIND",
        "file": "heart2.py",
        "find": "            if ((_dg + os.sep).startswith(os.path.normpath(dest) + os.sep)\n"
                "                    and _share_history(os.path.dirname(_s), _dg, say)):\n",
        "replace": "            if False:\n",
        "matches": 1,
    },
    {
        "why": "REG-2364 - the clone's push url is left on its origin, the real checkout: a push from the sandbox "
               "writes the real repo's refs",
        "file": "heart2.py",
        "find": "[\"git\", \"config\", \"remote.origin.pushurl\", os.path.join(dst, _NO_PUSH)]",
        "replace": "[\"git\", \"config\", \"sandbox.note\", os.path.join(dst, _NO_PUSH)]",
        "matches": 1,
    },
    {
        "why": "REG-2364 - the sandbox history is built with the prover's GIT_* variables: under a hook's leaked "
               "GIT_DIR its read-tree rewrites the real worktree's index and its config the real common config",
        "file": "heart2.py",
        "find": "    env = {k: v for k, v in os.environ.items() if not k.startswith(\"GIT_\")}\n"
                "    env[\"GIT_OPTIONAL_LOCKS\"] = \"0\"\n    tmp = dst + \".shared\"\n",
        "replace": "    env = dict(os.environ, GIT_OPTIONAL_LOCKS=\"0\")\n    tmp = dst + \".shared\"\n",
        "matches": 1,
    },
    {
        "why": "REG-2364 - the 'fix' that copies the worktree's .git POINTER into the sandbox: history again, through "
               "a door to the real worktree",
        "file": "heart2.py",
        "find": "        if os.path.isfile(_s) and os.path.basename(_s) == \".git\":\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
]
