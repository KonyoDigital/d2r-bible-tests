# -*- coding: utf-8 -*-
"""#259 (REG-2016) - A FILE OVER THE EYE'S SNAPSHOT LIMIT GOES IN AS THE BLOCKS AROUND ITS HUNKS, NEVER AS NOTHING.

MEASURED 2026-10-07: tv/control_ui.html (2.2 MB) and tv/control_app.py (2.7 MB) are both over the second eye's 2 MB
snapshot limit, so every console change reached Grok as bare hunks. v3607's look answered cannot-tell ("I could not see
the caller that concatenates the version word onto the lag span"), and v3608's push was refused early until a re-ask.
Now an over-limit file is written into the eye's folder as `<file>.EXCERPT.txt`: each changed line's enclosing top-level
def/class (Python) or a window either side (anything else), numbered as in the file, merged, bounded, and NAMED in the
prompt as an excerpt. ⚠ The first dry run on a real commit cut the WRONG lines: `_changes(sha, "-U0", "--", path)` put
the path before the sha, so git read the sha as a second path and diffed HEAD. The integration case below would catch it.
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock as mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import second_eye_run as E  # noqa: E402

PY = "\n".join(["import os", "", "", "def first():", "    return 1", "", "", "def second(x):", "    y = x + 1",
                "    return y * 2", "", "", "class Third(object):", "    def m(self):", "        return 3", ""])


def _rm_readonly(path):
    """eye_snapshot makes its folder read-only (0o444 / 0o555); give write back so the cleanup really removes it."""
    for root, dirs, files in os.walk(path):
        for x in dirs + files:
            try:
                os.chmod(os.path.join(root, x), 0o755)
            except Exception:
                pass
    shutil.rmtree(path, True)


def _git(repo, *a):
    return subprocess.run(["git"] + list(a), cwd=repo, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", check=True).stdout.strip()


class TheEyeSeesTheBlocksAroundABigFilesHunks(unittest.TestCase):

    def test_a_python_hunk_gets_its_whole_enclosing_def_and_nothing_else(self):
        out = E.excerpt_blocks(PY, [9], True)
        self.assertIn("def second(x):", out)
        self.assertIn("return y * 2", out)
        self.assertNotIn("def first", out, "the excerpt reached past the enclosing def")
        self.assertNotIn("class Third", out)
        self.assertIn("     9:     y = x + 1", out, "the excerpt is not numbered as in the file")

    def test_other_files_get_a_window_and_overlapping_blocks_merge(self):
        text = "\n".join("line %d" % i for i in range(1, 201))
        out = E.excerpt_blocks(text, [50, 55], False, window=10)
        self.assertEqual(out.count("--- lines "), 1, "two overlapping windows were not merged")
        self.assertIn("    40: line 40", out)
        self.assertNotIn("    39: line 39", out)
        self.assertEqual(E.excerpt_blocks(text, [], False), "", "no changed line still produced an excerpt")

    def test_the_excerpt_is_bounded(self):
        text = "\n".join("x" * 100 for _ in range(5000))
        out = E.excerpt_blocks(text, [100, 2000, 4000], False, window=50, max_chars=12000)
        self.assertLessEqual(len(out), 12000 + 200)
        self.assertIn("(cut: the excerpt reached", out, "a cut excerpt does not say it was cut")

    def test_a_module_level_edit_is_not_glued_to_the_previous_def(self):
        """REG-2018 (the #231 eye on v3614)."""
        text = "def first():\n    return 1\n\nLIMIT = 5\n\ndef second():\n    return 2\n"
        out = E.excerpt_blocks(text, [4], True, window=1)
        self.assertIn("LIMIT = 5", out)
        self.assertNotIn("return 1", out, "a module-level edit was excerpted as part of the def above it")

    def test_a_decorator_edit_carries_the_function_it_decorates(self):
        text = "import x\n\n\n@cache\ndef f():\n    return 1\n\n\ndef g():\n    return 2\n"
        out = E.excerpt_blocks(text, [4], True)
        self.assertIn("def f():", out, "a decorator-only hunk excerpted the decorator alone")
        self.assertIn("return 1", out)
        self.assertNotIn("def g", out)

    def test_a_first_block_over_the_cap_still_carries_code(self):
        text = "def big():\n" + "\n".join("    v%d = '%s'" % (k, "x" * 200) for k in range(300)) + "\n"
        out = E.excerpt_blocks(text, [150], True, max_chars=5000)
        self.assertIn("this block alone passed", out, "the cut is not said")
        self.assertIn(": def big():", out, "an over-cap first block reached the eye as a banner with no code (REG-2018)")

    def test_a_real_snapshot_excerpts_the_big_file_around_its_own_commit(self):
        repo = tempfile.mkdtemp(prefix="eyeexcerpt_")
        cwd = tempfile.mkdtemp(prefix="eyecwd_")
        self.addCleanup(shutil.rmtree, repo, True)
        self.addCleanup(_rm_readonly, cwd)
        _git(repo, "init", "-q")
        os.makedirs(os.path.join(repo, "tv"))
        big = PY + "\n" + "\n".join("# filler %d" % i for i in range(400))
        with io.open(os.path.join(repo, "tv", "big.py"), "w", encoding="utf-8") as fh:
            fh.write(big)
        _git(repo, "add", "-A")
        _git(repo, "-c", "user.email=l@x", "-c", "user.name=l", "commit", "-q", "-m", "one")
        with io.open(os.path.join(repo, "tv", "big.py"), "w", encoding="utf-8") as fh:
            fh.write(big.replace("    y = x + 1", "    y = x + 41"))
        _git(repo, "-c", "user.email=l@x", "-c", "user.name=l", "commit", "-q", "-am", "two")
        sha = _git(repo, "rev-parse", "HEAD")
        with io.open(os.path.join(repo, "tv", "other.txt"), "w", encoding="utf-8") as fh:   # a later commit at HEAD:
            fh.write("unrelated\n")                                                            # a wrong diff would show
        _git(repo, "add", "-A")                                                                # THIS, not `sha`
        _git(repo, "-c", "user.email=l@x", "-c", "user.name=l", "commit", "-q", "-m", "three")
        with mock.patch.object(E, "REPO", repo), mock.patch.object(E, "EYE_CWD", cwd), \
                mock.patch.object(E, "REVIEW_BASE", None), mock.patch.object(E, "_eye_cwd_ready", lambda: None):
            snap = E.eye_snapshot(sha, max_bytes=200)
        self.assertTrue(snap.get("ok"), snap)
        self.assertIn("tv/big.py.EXCERPT.txt", snap.get("included") or [], "the big file was left out, not excerpted")
        with io.open(os.path.join(cwd, "tv", "big.py.EXCERPT.txt"), encoding="utf-8") as fh:
            ex = fh.read()
        self.assertIn("y = x + 41", ex, "the excerpt is not the reviewed commit's block (wrong diff or wrong bytes)")
        self.assertIn("def second(x):", ex)
        self.assertNotIn("def first", ex)
        self.assertIn("EXCERPT.txt", E.snapshot_note(snap), "the prompt does not name the excerpt")


RED_PROOF = [
    {"why": "REG-2018 - a module-level edit is glued to the previous def again",
     "file": "tv/second_eye_run.py",
     "find": "        if is_py and not _module_level:\n",
     "replace": "        if is_py:\n",
     "matches": 1},
    {"why": "REG-2018 - a decorator-only hunk excerpts the decorator alone again",
     "file": "tv/second_eye_run.py",
     "find": '            if src[i].startswith("@"):\n',
     "replace": "            if False:\n",
     "matches": 1},
    {"why": "REG-2018 - an over-cap first block reaches the eye as a banner with no code again",
     "file": "tv/second_eye_run.py",
     "find": "            if not out:\n                # REG-2018",
     "replace": "            if False:\n                # REG-2018",
     "matches": 1},
    {"why": "#259 - an over-limit file is dropped again, so the eye judges console changes from bare hunks",
     "file": "tv/second_eye_run.py",
     "find": "            excerpts.append(ex)\n",
     "replace": "            pass\n",
     "matches": 1},
    {"why": "#259 - the hunk diff puts the path before the sha again, so the excerpt cuts HEAD's lines",
     "file": "tv/second_eye_run.py",
     "find": '    d, _w = _sh(_changes(sha, "-U0") + ["--", path], timeout=60)\n',
     "replace": '    d, _w = _sh(_changes(sha, "-U0", "--", path), timeout=60)\n',
     "matches": 1},
    {"why": "#259 - a Python hunk gets a fixed window instead of its enclosing def",
     "file": "tv/second_eye_run.py",
     "find": "        if is_py and not _module_level:\n",
     "replace": "        if False:\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
