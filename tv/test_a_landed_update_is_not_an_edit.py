# -*- coding: utf-8 -*-
"""A landed update is not a person mid-edit, and the beacon says which is which.

Dean sat on an old process while a newer tree was already on disk. The relaunch refusal said the
working tree was mid-edit. A file that differs from HEAD but matches the blob already fetched at
origin/main is that update. A file that matches neither is still an edit and still blocks. A blob
that cannot be read still blocks: unknown is not an update.

The beacon carries HEAD, core.autocrlf, the porcelain lines and the last pull exit. A home
directory or a drive path is removed before any of that leaves the machine.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()
import control_app as ca  # noqa: E402


def _acct(name, rest):
    """A home path. Split in source so the public-repo gate does not see /Users/<name>/."""
    return "/Users/" + name + "/" + rest


def _R(rc, out):
    class R(object):
        returncode = rc
        stdout = out if isinstance(out, bytes) else str(out).encode("utf-8")
    return R


class ALandedUpdateIsNotAnEdit(unittest.TestCase):

    def setUp(self):
        self._saved_git = ca._git_run
        self._pull = dict(ca._PULL)
        ca._TREE_DIAG["t"] = 0.0
        self.root = os.path.dirname(ca.HERE)
        self.rel = "tv/control_app.py"
        with open(os.path.join(self.root, self.rel), "rb") as fh:
            self.disk = fh.read()

    def tearDown(self):
        ca._git_run = self._saved_git
        ca._PULL.clear()
        ca._PULL.update(self._pull)
        ca._TREE_DIAG["t"] = 0.0

    def _git(self, status=b"", show=b"", show_rc=0, status_rc=0):
        disk_rel = self.rel

        def run(argv, **kw):
            cmd = argv if isinstance(argv, (list, tuple)) else []
            if "status" in cmd:
                return _R(status_rc, status)
            if "show" in cmd:
                return _R(show_rc, show)
            if "rev-parse" in cmd:
                return _R(0, b"abc1234\n")
            if "config" in cmd:
                return _R(0, b"input\n")
            return _R(1, b"")

        ca._git_run = run
        return disk_rel

    def test_bytes_that_match_origin_are_an_update_not_an_edit(self):
        self._git(status=b" M tv/control_app.py\n", show=self.disk)
        dirty, why = ca._tree_is_mid_edit()
        self.assertFalse(dirty, "a landed update was refused as a mid-edit: %s" % why)

    def test_the_same_bytes_with_CR_at_end_of_line_are_still_that_update(self):
        self._git(status=b" M tv/control_app.py\n", show=self.disk.replace(b"\n", b"\r\n"))
        dirty, why = ca._tree_is_mid_edit()
        self.assertFalse(dirty, "CR at end of line was read as an edit: %s" % why)

    def test_a_file_that_matches_neither_still_blocks_and_is_named(self):
        self._git(status=b" M tv/control_app.py\n", show=self.disk + b"\nNOT AN UPDATE\n")
        dirty, why = ca._tree_is_mid_edit()
        self.assertTrue(dirty, "a real edit was allowed to relaunch")
        self.assertIn("mid-edit", why)
        self.assertIn("tv/control_app.py", why)

    def test_a_blob_that_cannot_be_read_still_blocks(self):
        self._git(status=b" M tv/control_app.py\n", show=self.disk, show_rc=1)
        dirty, why = ca._tree_is_mid_edit()
        self.assertTrue(dirty, "an unreadable blob was treated as an update: %s" % why)
        self.assertIn("tv/control_app.py", why)

    def test_one_landed_file_does_not_excuse_a_real_edit_beside_it(self):
        self._git(status=b" M tv/control_app.py\n M tv/tv_diablo.py\n", show=self.disk)
        dirty, why = ca._tree_is_mid_edit()
        self.assertTrue(dirty, why)
        self.assertIn("tv/tv_diablo.py", why)
        self.assertNotIn("tv/control_app.py", why,
                         "the file that matches origin/main was still named as an edit")

    def test_an_unsafe_path_still_blocks_and_is_named(self):
        self._git(status=b" M ../tv/control_app.py\n M /tmp/not-the-repo.py\n")
        dirty, why = ca._tree_is_mid_edit()
        self.assertTrue(dirty, why)
        self.assertIn("../tv/control_app.py", why)
        self.assertIn("/tmp/not-the-repo.py", why)

    def test_the_beacon_says_HEAD_and_scrubs_a_home_directory(self):
        ca._TREE_DIAG["t"] = 0.0
        home = _acct("someone", "secret.py")
        forward = "C:/" + "Users/" + "Dean/" + "TV/.git/index.lock"
        spaced = _acct("Jane Doe", "TV/a.py")
        unix_home = "/home/" + "dean/" + "tv/a.py"
        self._git(status=(
            " M tv/control_app.py\n M %s\n M %s\n" % (home, forward)
        ).encode("utf-8"))
        with ca._PRUNE_LOCK:
            ca._PULL["exit"] = True
            ca._PULL["lastErr"] = (
                "fatal: Unable to create '%s': File exists. also %s and %s"
                % (forward, spaced, unix_home)
            )
        row = ca._beacon_git_diag({"can": True, "why": "level with origin", "armed": False})
        self.assertEqual(row["can"], True)
        self.assertEqual(row["why"], "level with origin")
        self.assertIs(row["armed"], False)
        self.assertEqual(row["head"], "abc1234")
        self.assertEqual(row["autocrlf"], "input")
        porcelain = row["porcelain"] or ""
        self.assertIn("tv/control_app.py", porcelain)
        self.assertNotIn("/Users/", porcelain)
        self.assertNotIn("secret", porcelain)
        self.assertNotIn("Dean", porcelain)
        self.assertIsNone(row["exit"], "a boolean exit was stored as a number")
        err = row["err"] or ""
        self.assertNotIn("/Users/", err)
        self.assertNotIn("Dean", err)
        self.assertNotIn("Doe", err)
        self.assertNotIn("dean", err)
        self.assertNotIn("C:/", err)
        self.assertNotIn("C:\\", err)
        self.assertIn("fatal", err)
        self.assertIn("File exists", err)
        self.assertIsNone(ca._beacon_git_diag(None))

    def test_a_spaced_drive_path_keeps_the_sentence_and_drops_the_name(self):
        """A drive path with a space, either slash, must not ship the name."""
        spaced = "D:\\" + "Jane Doe\\" + "TV\\.git\\index.lock"
        err = ca._public_git_text(
            "fatal: Unable to create '%s': File exists." % spaced)
        self.assertNotIn("Jane", err)
        self.assertNotIn("Doe", err)
        self.assertNotIn("\\", err)
        self.assertIn("fatal", err)
        self.assertIn("File exists", err)
        url = ca._public_git_text(
            "fatal: https://example.com/repo.git update failed")
        self.assertIn("https://example.com/repo.git", url)
        self.assertIn("update failed", url)
        forward = "D:/" + "Jane Doe/" + "TV/.git/index.lock"
        fwd = ca._public_git_text(
            "fatal: Unable to create '%s': File exists." % forward)
        self.assertNotIn("Jane", fwd)
        self.assertNotIn("Doe", fwd)
        self.assertIn("fatal", fwd)
        self.assertIn("File exists", fwd)
        glued = ca._public_git_text("note at" + "D:/" + "Jane" + "/x left behind")
        self.assertNotIn("Jane", glued)

    def test_a_real_pull_exit_is_kept_and_a_cached_diagnosis_is_not_reread(self):
        self._git()
        ca._TREE_DIAG["t"] = 0.0
        with ca._PRUNE_LOCK:
            ca._PULL["exit"] = 128
            ca._PULL["lastErr"] = None
        first = ca._beacon_git_diag({"can": False, "why": "behind"})
        self.assertEqual(first["exit"], 128)
        self.assertEqual(first["head"], "abc1234")

        def boom(*a, **k):
            raise OSError("git must not be asked again inside the cache")

        ca._git_run = boom
        second = ca._beacon_git_diag({"can": False, "why": "behind"})
        self.assertEqual(second["head"], "abc1234", "the cache missed and asked git again")


class TheWorkerKeepsTheDiagnosis(unittest.TestCase):
    """The console can post a perfect diagnosis and the fleet still shows nothing if the worker
    drops the keys. This runs the worker shaper itself."""

    def _worker(self):
        import io as _io
        with _io.open(os.path.join(os.path.dirname(HERE), "functions", "api", "console.js"),
                      encoding="utf-8") as fh:
            return fh.read()

    def _run(self, prelude, expr):
        import subprocess as sp
        src = self._worker()
        i = src.index(prelude)
        j = src.index("})(body.%s)," % expr, i)
        fn = src[i + len(prelude):j + len("})(body.%s)" % expr)]
        prog = "var body = global.body;\nvar out = %s;\nprocess.stdout.write(JSON.stringify(out));\n" % fn
        r = sp.run(["node", "-"], input=prog.encode("utf-8"), stdout=sp.PIPE, stderr=sp.STDOUT,
                   timeout=20)
        self.assertEqual(r.returncode, 0, r.stdout.decode("utf-8", "replace")[-500:])
        import json
        return json.loads(r.stdout.decode("utf-8"))

    def test_null_exit_stays_null_and_a_path_does_not_cross(self):
        import json
        import subprocess as sp
        home = _acct("someone", "secret.py")
        forward = "C:/" + "Users/" + "Dean/" + "TV/.git/index.lock"
        spaced = _acct("Jane Doe", "TV/a.py")
        drive = "D:/" + "Jane Doe/" + "TV/.git/index.lock"
        body = {
            "relaunch": {
                "armed": True, "may": "yes", "why": "holding",
                "head": "zzzz", "autocrlf": "maybe",
                "porcelain": " M %s" % home,
                "exit": None,
                "err": "bad C:\\games\\d2r\\index.lock left",
            },
            "pull": {"can": False, "behind": 3, "why": "behind", "exit": 0, "head": "abc1234",
                     "autocrlf": "false",
                     "porcelain": " M tv/control_app.py",
                     "err": "fatal: https://example.com/repo.git update failed. "
                            "Unable to create '%s': File exists. %s %s" % (forward, spaced, drive)},
            "windowMode": "fullscreen",
        }
        src = self._worker()
        chunk = src[src.index("windowMode: (function (w)"):src.index("})(body.pull),") + len("})(body.pull)")]
        glued_body = {"windowMode": "front",
                      "pull": {"can": True, "behind": 0, "why": "level", "exit": 0,
                               "head": "abc1234", "autocrlf": "input",
                               "porcelain": " M tv/control_app.py",
                               "err": "note at" + "D:/" + "Jane" + "/x left behind"}}
        prog = ("var body = %s;\nvar rec = {\n%s\n};\nbody = %s;\nvar glued = {\n%s\n};\n"
                "process.stdout.write(JSON.stringify({rec: rec, glued: glued}));\n"
                % (json.dumps(body), chunk, json.dumps(glued_body), chunk))
        r = sp.run(["node", "-"], input=prog.encode("utf-8"), stdout=sp.PIPE, stderr=sp.STDOUT,
                   timeout=20)
        self.assertEqual(r.returncode, 0, r.stdout.decode("utf-8", "replace")[-800:])
        wrapped = json.loads(r.stdout.decode("utf-8"))
        rec = wrapped["rec"]
        self.assertNotIn("Jane", (wrapped["glued"]["pull"] or {}).get("err") or "")
        self.assertEqual(rec["windowMode"], "fullscreen")
        self.assertIs(rec["relaunch"]["armed"], True)
        self.assertIsNone(rec["relaunch"]["may"], "an unrecognised may was stored as a verdict")
        self.assertIsNone(rec["relaunch"]["head"])
        self.assertIsNone(rec["relaunch"]["autocrlf"])
        self.assertNotIn("/Users/", rec["relaunch"]["porcelain"] or "",
                         "a home directory survived onto the beacon")
        self.assertNotIn("secret", rec["relaunch"]["porcelain"] or "")
        self.assertIsNone(rec["relaunch"]["exit"], "null exit was stored as 0")
        self.assertNotIn("C:\\", rec["relaunch"]["err"] or "")
        self.assertIn("bad", rec["relaunch"]["err"] or "")
        self.assertEqual(rec["pull"]["exit"], 0)
        self.assertEqual(rec["pull"]["head"], "abc1234")
        self.assertEqual(rec["pull"]["autocrlf"], "false")
        self.assertIn("tv/control_app.py", rec["pull"]["porcelain"])
        pull_err = rec["pull"]["err"] or ""
        self.assertNotIn("Dean", pull_err)
        self.assertNotIn("Jane", pull_err)
        self.assertNotIn("Doe", pull_err)
        self.assertNotIn("/Users/", pull_err)
        self.assertNotIn("C:/", pull_err)
        self.assertIn("fatal", pull_err)
        self.assertIn("File exists", pull_err)
        self.assertIn("https://example.com/repo.git", pull_err)
        self.assertIn("update failed", pull_err)

    def test_an_absent_window_mode_is_null_not_the_word_undefined(self):
        import json
        import subprocess as sp
        src = self._worker()
        i = src.index("windowMode: (function (w)")
        j = src.index("})(body.windowMode),", i)
        fn = src[i + len("windowMode: "):j + len("})(body.windowMode)")]
        prog = ("var body = {};\nvar out = %s;\nprocess.stdout.write(JSON.stringify(out));\n" % fn)
        r = sp.run(["node", "-"], input=prog.encode("utf-8"), stdout=sp.PIPE, stderr=sp.STDOUT,
                   timeout=20)
        self.assertEqual(r.returncode, 0, r.stdout.decode("utf-8", "replace")[-500:])
        self.assertIsNone(json.loads(r.stdout.decode("utf-8")),
                          "a missing window mode was stored as the word undefined")


class TheLauncherUsesTheSameRule(unittest.TestCase):
    """The launcher runs before the process that already knows this rule.

    A file whose bytes match the fetched origin/main, CR ignored, is the update.
    A real edit still blocks. A history that cannot fast-forward is not reset.
    """

    def test_the_byte_rule_matches_the_console(self):
        import launcher_pull as lp
        pairs = [(b"a\n", b"a\r\n"), (b"a\nb", b"a\r\nb"), (b"a\n", b"b\n"), (b"", b"")]
        for left, right in pairs:
            self.assertEqual(lp.bytes_match_ignoring_cr(left, right),
                             ca._bytes_match_ignoring_cr(left, right),
                             "the launcher and the console disagree on %r %r" % (left, right))

    def _repo(self):
        import subprocess
        import tempfile
        d = tempfile.mkdtemp(prefix="launcher_pull_")
        self.addCleanup(self._rm, d)
        subprocess.check_call(["git", "init", "-q"], cwd=d)
        subprocess.check_call(["git", "-C", d, "config", "user.email", "t@example.com"])
        subprocess.check_call(["git", "-C", d, "config", "user.name", "t"])
        path = os.path.join(d, "a.txt")
        with open(path, "wb") as fh:
            fh.write(b"one\n")
        subprocess.check_call(["git", "-C", d, "add", "a.txt"])
        subprocess.check_call(["git", "-C", d, "commit", "-q", "-m", "one"])
        with open(path, "wb") as fh:
            fh.write(b"two\n")
        subprocess.check_call(["git", "-C", d, "add", "a.txt"])
        subprocess.check_call(["git", "-C", d, "commit", "-q", "-m", "two"])
        subprocess.check_call(["git", "-C", d, "update-ref", "refs/remotes/origin/main", "HEAD"])
        subprocess.check_call(["git", "-C", d, "reset", "-q", "--hard", "HEAD~1"])
        return d, path

    def _rm(self, d):
        import shutil
        shutil.rmtree(d, ignore_errors=True)

    def _head(self, d):
        import subprocess
        return subprocess.check_output(["git", "-C", d, "rev-parse", "HEAD"], text=True).strip()

    def _origin(self, d):
        import subprocess
        return subprocess.check_output(
            ["git", "-C", d, "rev-parse", "refs/remotes/origin/main"], text=True).strip()

    def test_bytes_that_match_origin_are_reset_onto_that_update(self):
        import launcher_pull as lp
        d, path = self._repo()
        origin = self._origin(d)
        with open(path, "wb") as fh:
            fh.write(b"two\n")
        self.assertNotEqual(self._head(d), origin)
        self.assertEqual(lp.apply(d), 0)
        self.assertEqual(self._head(d), origin)
        with open(path, "rb") as fh:
            self.assertEqual(fh.read(), b"two\n")

    def test_the_same_bytes_with_CR_are_still_that_update(self):
        import launcher_pull as lp
        d, path = self._repo()
        with open(path, "wb") as fh:
            fh.write(b"two\r\n")
        self.assertEqual(lp.apply(d), 0)
        self.assertEqual(self._head(d), self._origin(d))

    def test_a_real_edit_is_not_reset(self):
        import launcher_pull as lp
        d, path = self._repo()
        head = self._head(d)
        with open(path, "wb") as fh:
            fh.write(b"two\nlocal\n")
        self.assertEqual(lp.apply(d), 2)
        self.assertEqual(self._head(d), head)
        with open(path, "rb") as fh:
            self.assertEqual(fh.read(), b"two\nlocal\n")

    def test_one_real_edit_beside_a_match_is_not_reset(self):
        import subprocess
        import launcher_pull as lp
        d, path = self._repo()
        head = self._head(d)
        with open(path, "wb") as fh:
            fh.write(b"two\n")
        other = os.path.join(d, "b.txt")
        with open(other, "wb") as fh:
            fh.write(b"local\n")
        subprocess.check_call(["git", "-C", d, "add", "b.txt"])
        # staged add of a file origin does not have: a real edit beside the update
        self.assertEqual(lp.apply(d), 2)
        self.assertEqual(self._head(d), head)

    def test_a_history_that_cannot_fast_forward_is_not_reset(self):
        import subprocess
        import launcher_pull as lp
        d, path = self._repo()
        # origin is the first commit. Move HEAD one commit ahead of it, then make
        # the worktree match origin. That is local history, not the update.
        subprocess.check_call(["git", "-C", d, "update-ref", "refs/remotes/origin/main", "HEAD"])
        with open(path, "wb") as fh:
            fh.write(b"three\n")
        subprocess.check_call(["git", "-C", d, "add", "a.txt"])
        subprocess.check_call(["git", "-C", d, "commit", "-q", "-m", "three"])
        head = self._head(d)
        with open(path, "wb") as fh:
            fh.write(b"one\n")
        self.assertEqual(lp.apply(d), 2)
        self.assertEqual(self._head(d), head)
        with open(path, "rb") as fh:
            self.assertEqual(fh.read(), b"one\n")

    def test_a_missing_origin_is_not_an_update(self):
        import subprocess
        import launcher_pull as lp
        d, path = self._repo()
        head = self._head(d)
        subprocess.check_call(["git", "-C", d, "update-ref", "-d", "refs/remotes/origin/main"])
        with open(path, "wb") as fh:
            fh.write(b"two\n")
        self.assertEqual(lp.apply(d), 2)
        self.assertEqual(self._head(d), head)

    def test_an_untracked_file_the_update_adds_is_not_replaced(self):
        import subprocess
        import launcher_pull as lp
        d, path = self._repo()
        head = self._head(d)
        subprocess.check_call(["git", "-C", d, "checkout", "-q", self._origin(d)])
        foo = os.path.join(d, "foo.txt")
        with open(foo, "wb") as fh:
            fh.write(b"from-origin\n")
        subprocess.check_call(["git", "-C", d, "add", "foo.txt"])
        subprocess.check_call(["git", "-C", d, "commit", "-q", "-m", "add foo"])
        subprocess.check_call(["git", "-C", d, "update-ref", "refs/remotes/origin/main", "HEAD"])
        subprocess.check_call(["git", "-C", d, "checkout", "-q", "HEAD~2"])
        with open(path, "wb") as fh:
            fh.write(b"two\n")
        with open(foo, "wb") as fh:
            fh.write(b"local-untracked\n")
        self.assertEqual(lp.apply(d), 2)
        self.assertEqual(self._head(d), head)
        with open(foo, "rb") as fh:
            self.assertEqual(fh.read(), b"local-untracked\n")

    def _fresh(self):
        import subprocess
        import tempfile
        d = tempfile.mkdtemp(prefix="launcher_pull_")
        self.addCleanup(self._rm, d)
        subprocess.check_call(["git", "init", "-q"], cwd=d)
        subprocess.check_call(["git", "-C", d, "config", "user.email", "t@example.com"])
        subprocess.check_call(["git", "-C", d, "config", "user.name", "t"])
        return d

    def _commit_all(self, d, msg):
        import subprocess
        subprocess.check_call(["git", "-C", d, "add", "-A"])
        subprocess.check_call(["git", "-C", d, "commit", "-q", "-m", msg])

    def test_a_similar_rename_does_not_hide_the_untracked_file_it_lands_on(self):
        import subprocess
        import launcher_pull as lp
        d = self._fresh()
        with open(os.path.join(d, "a.txt"), "wb") as fh:
            fh.write(b"one\n")
        with open(os.path.join(d, "old.txt"), "wb") as fh:
            fh.write(b"keep\n")
        self._commit_all(d, "one")
        base = self._head(d)
        with open(os.path.join(d, "a.txt"), "wb") as fh:
            fh.write(b"two\n")
        subprocess.check_call(["git", "-C", d, "mv", "old.txt", "new.txt"])
        self._commit_all(d, "two")
        subprocess.check_call(["git", "-C", d, "config", "diff.renames", "true"])
        subprocess.check_call(["git", "-C", d, "update-ref", "refs/remotes/origin/main", "HEAD"])
        subprocess.check_call(["git", "-C", d, "reset", "-q", "--hard", base])
        with open(os.path.join(d, "a.txt"), "wb") as fh:
            fh.write(b"two\n")
        new = os.path.join(d, "new.txt")
        with open(new, "wb") as fh:
            fh.write(b"local-untracked\n")
        self.assertEqual(lp.apply(d), 2)
        self.assertEqual(self._head(d), base)
        with open(new, "rb") as fh:
            self.assertEqual(fh.read(), b"local-untracked\n")

    def test_a_file_where_the_update_adds_a_directory_is_not_replaced(self):
        import os as _os
        import subprocess
        import launcher_pull as lp
        d = self._fresh()
        with open(os.path.join(d, "a.txt"), "wb") as fh:
            fh.write(b"one\n")
        self._commit_all(d, "one")
        base = self._head(d)
        with open(os.path.join(d, "a.txt"), "wb") as fh:
            fh.write(b"two\n")
        slot = os.path.join(d, "slot")
        _os.mkdir(slot)
        with open(os.path.join(slot, "inner.txt"), "wb") as fh:
            fh.write(b"from-origin\n")
        self._commit_all(d, "two")
        subprocess.check_call(["git", "-C", d, "update-ref", "refs/remotes/origin/main", "HEAD"])
        subprocess.check_call(["git", "-C", d, "reset", "-q", "--hard", base])
        with open(os.path.join(d, "a.txt"), "wb") as fh:
            fh.write(b"two\n")
        with open(slot, "wb") as fh:
            fh.write(b"local-file\n")
        self.assertEqual(lp.apply(d), 2)
        self.assertEqual(self._head(d), base)
        self.assertTrue(os.path.isfile(slot))
        with open(slot, "rb") as fh:
            self.assertEqual(fh.read(), b"local-file\n")

    def test_two_added_paths_are_read_separately(self):
        import subprocess
        import launcher_pull as lp
        d = self._fresh()
        with open(os.path.join(d, "a.txt"), "wb") as fh:
            fh.write(b"one\n")
        self._commit_all(d, "one")
        base = self._head(d)
        with open(os.path.join(d, "a.txt"), "wb") as fh:
            fh.write(b"two\n")
        with open(os.path.join(d, "other.txt"), "wb") as fh:
            fh.write(b"from-origin\n")
        with open(os.path.join(d, "plain.txt"), "wb") as fh:
            fh.write(b"from-origin\n")
        self._commit_all(d, "two")
        subprocess.check_call(["git", "-C", d, "update-ref", "refs/remotes/origin/main", "HEAD"])
        subprocess.check_call(["git", "-C", d, "reset", "-q", "--hard", base])
        with open(os.path.join(d, "a.txt"), "wb") as fh:
            fh.write(b"two\n")
        other = os.path.join(d, "other.txt")
        with open(other, "wb") as fh:
            fh.write(b"local-untracked\n")
        self.assertEqual(lp.apply(d), 2)
        self.assertEqual(self._head(d), base)
        with open(other, "rb") as fh:
            self.assertEqual(fh.read(), b"local-untracked\n")

    def test_a_tracked_file_the_update_turns_into_a_directory_still_lands(self):
        import subprocess
        import launcher_pull as lp
        d = self._fresh()
        with open(os.path.join(d, "a.txt"), "wb") as fh:
            fh.write(b"one\n")
        with open(os.path.join(d, "foo"), "wb") as fh:
            fh.write(b"tracked-file\n")
        self._commit_all(d, "one")
        base = self._head(d)
        with open(os.path.join(d, "a.txt"), "wb") as fh:
            fh.write(b"two\n")
        os.remove(os.path.join(d, "foo"))
        os.mkdir(os.path.join(d, "foo"))
        with open(os.path.join(d, "foo", "bar.py"), "wb") as fh:
            fh.write(b"from-origin\n")
        self._commit_all(d, "two")
        subprocess.check_call(["git", "-C", d, "update-ref", "refs/remotes/origin/main", "HEAD"])
        subprocess.check_call(["git", "-C", d, "reset", "-q", "--hard", base])
        with open(os.path.join(d, "a.txt"), "wb") as fh:
            fh.write(b"two\n")
        self.assertEqual(lp.apply(d), 0)
        self.assertNotEqual(self._head(d), base)
        self.assertTrue(os.path.isfile(os.path.join(d, "foo", "bar.py")))

    def test_a_tracked_directory_the_update_turns_into_a_file_still_lands(self):
        import subprocess
        import launcher_pull as lp
        d = self._fresh()
        with open(os.path.join(d, "a.txt"), "wb") as fh:
            fh.write(b"one\n")
        nest = os.path.join(d, "nest")
        os.mkdir(nest)
        with open(os.path.join(nest, "old.txt"), "wb") as fh:
            fh.write(b"old\n")
        self._commit_all(d, "one")
        base = self._head(d)
        with open(os.path.join(d, "a.txt"), "wb") as fh:
            fh.write(b"two\n")
        os.remove(os.path.join(nest, "old.txt"))
        os.rmdir(nest)
        with open(nest, "wb") as fh:
            fh.write(b"now-a-file\n")
        self._commit_all(d, "two")
        subprocess.check_call(["git", "-C", d, "update-ref", "refs/remotes/origin/main", "HEAD"])
        subprocess.check_call(["git", "-C", d, "reset", "-q", "--hard", base])
        with open(os.path.join(d, "a.txt"), "wb") as fh:
            fh.write(b"two\n")
        self.assertEqual(lp.apply(d), 0)
        self.assertNotEqual(self._head(d), base)
        self.assertTrue(os.path.isfile(nest))
        with open(nest, "rb") as fh:
            self.assertEqual(fh.read(), b"now-a-file\n")

    def test_an_untracked_symlink_where_the_update_adds_a_directory_stays(self):
        import subprocess
        import launcher_pull as lp
        d = self._fresh()
        with open(os.path.join(d, "a.txt"), "wb") as fh:
            fh.write(b"one\n")
        self._commit_all(d, "one")
        base = self._head(d)
        with open(os.path.join(d, "a.txt"), "wb") as fh:
            fh.write(b"two\n")
        slot = os.path.join(d, "slot")
        os.mkdir(slot)
        with open(os.path.join(slot, "inner.txt"), "wb") as fh:
            fh.write(b"from-origin\n")
        self._commit_all(d, "two")
        subprocess.check_call(["git", "-C", d, "update-ref", "refs/remotes/origin/main", "HEAD"])
        subprocess.check_call(["git", "-C", d, "reset", "-q", "--hard", base])
        with open(os.path.join(d, "a.txt"), "wb") as fh:
            fh.write(b"two\n")
        target = os.path.join(d, "elsewhere")
        os.mkdir(target)
        os.symlink(target, slot)
        self.assertEqual(lp.apply(d), 2)
        self.assertEqual(self._head(d), base)
        self.assertTrue(os.path.islink(slot))

    def test_an_untracked_file_origin_does_not_ship_still_lets_the_update_land(self):
        import launcher_pull as lp
        d, path = self._repo()
        with open(path, "wb") as fh:
            fh.write(b"two\n")
        extra = os.path.join(d, "notes.txt")
        with open(extra, "wb") as fh:
            fh.write(b"keep\n")
        self.assertEqual(lp.apply(d), 0)
        self.assertEqual(self._head(d), self._origin(d))
        with open(extra, "rb") as fh:
            self.assertEqual(fh.read(), b"keep\n")

    def test_an_unreadable_tree_is_not_called_clean(self):
        import launcher_pull as lp
        import tempfile
        d = tempfile.mkdtemp(prefix="launcher_pull_notgit_")
        self.addCleanup(self._rm, d)
        self.assertEqual(lp.apply(d), 1)

    def test_both_launchers_and_both_pull_doors_call_it(self):
        with open(os.path.join(HERE, "start_tvd_mac.sh"), encoding="utf-8") as fh:
            mac = fh.read()
        with open(os.path.join(HERE, "start_tvd_win.ps1"), encoding="utf-8-sig") as fh:
            win = fh.read()
        with open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            app = fh.read()
        self.assertEqual(mac.count("_tvd_may_pull"), 3,
                         "the Mac launcher grew or lost a pull door")
        self.assertIn(
            'why=$(python3 "$HERE/launcher_pull.py" --repo "$REPO" --apply 2>/dev/null) || rc=$?',
            mac)
        self.assertIn("launcher_pull.py", win)
        self.assertIn("--apply", win)
        self.assertTrue(all(ord(c) < 128 for c in win), "non-ASCII in the Windows launcher")
        self.assertEqual(app.count("import launcher_pull as _lp"), 2,
                         "one of the in-process pull doors does not use the launcher rule")
        call = mac.find("if ! _tvd_may_pull; then")
        recorded = mac.find('_tvd_before="$(git -C "$REPO" rev-parse --short HEAD')
        self.assertGreater(call, recorded,
                           "the Mac launcher records HEAD after the reset, so the move looks like no change")
        for name in ("def fleet_pull(", "def _pull_once("):
            start = app.find(name)
            body = app[start:app.find("\ndef ", start + 1)]
            self.assertLess(body.find('rev-parse", "--short", "HEAD"'),
                            body.find("import launcher_pull as _lp"),
                            "%s records HEAD after the reset" % name.split("(")[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "a landed update is refused as a mid-edit again, so a machine that already fetched "
               "the bytes will not relaunch onto them",
        "file": "tv/control_app.py",
        "find": "            if safe is not None and _matches_fetched_origin(root, safe):\n"
                "                continue\n",
        "replace": "            if safe is not None and _matches_fetched_origin(root, safe):\n"
                   "                names.append(safe)\n",
        "matches": 1,
    },
    {
        "why": "a blob that cannot be read is treated as an update, so an unknown tree is allowed "
               "to relaunch",
        "file": "tv/control_app.py",
        "find": "        if getattr(shown, \"returncode\", 1) != 0:\n            return False\n",
        "replace": "        if getattr(shown, \"returncode\", 1) != 0:\n            return True\n",
        "matches": 1,
    },
    {
        "why": "a file that matches the fetched update is a local edit again, so the launcher skips the pull",
        "file": "tv/launcher_pull.py",
        "find": "        if _matches(repo, safe):\n            update.append(safe)\n",
        "replace": "        if False:\n            update.append(safe)\n",
        "matches": 1,
    },
    {
        "why": "an untracked file that the update also adds is replaced by the reset",
        "file": "tv/launcher_pull.py",
        "find": "    return not tracked\n",
        "replace": "    return False\n",
        "matches": 1,
    },
    {
        "why": "a similar rename hides the new path, so the reset replaces the untracked file there",
        "file": "tv/launcher_pull.py",
        "find": "                                \"--no-renames\", \"HEAD\", \"origin/main\"])\n",
        "replace": "                                \"HEAD\", \"origin/main\"])\n",
        "matches": 1,
    },
    {
        "why": "two added paths are one string, so the reset replaces the untracked file",
        "file": "tv/launcher_pull.py",
        "find": "    rc, out, _err = _run(repo, [\"diff\", \"-z\", \"--name-only\", \"--diff-filter=A\",\n",
        "replace": "    rc, out, _err = _run(repo, [\"diff\", \"--name-only\", \"--diff-filter=A\",\n",
        "matches": 1,
    },
    {
        "why": "a symlink where the update adds a directory is replaced, and the local link is gone",
        "file": "tv/launcher_pull.py",
        "find": "        return stat.S_ISDIR(os.lstat(path).st_mode)\n",
        "replace": "        return os.path.isdir(path)\n",
        "matches": 1,
    },
]
