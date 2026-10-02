# -*- coding: utf-8 -*-
"""REG-1753 (#160) - A VERSION STAMP IS NOT A PAGE CHANGE, AND ANYTHING ELSE STILL IS.

Every bump rewrites one line of bible.html (window.D2R_BUILD). The pre-push hook keyed its render (3-5 min) and its
Playwright smoke (~2 min) on the file NAME, so every console-only ship re-graded an unchanged page: measured on the
last 80 commits that touched bible.html, 46 changed nothing but that line. tv/page_delta.py now answers "changed
beyond its stamp?" for both triggers, and fails CLOSED.

This law holds four things:
  * a stamp-only commit is not a page change; a real page change, a stamp with code smuggled onto its line, and a
    change in the same commit beside the stamp all ARE (a real git repo, not a hand-built diff);
  * anything unreadable - a bad range - answers "changed", so the gates run;
  * the pattern matches the stamp line bump_version actually wrote into this tree (the join to the writer);
  * the hook asks page_delta for BOTH the render and the smoke trigger, and bible.html left the name-only lists.
RED_PROOF below. [[the-unjoined-end]] [[unknown-stays-unknown]] [[source-reading-guard]]
"""
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import page_delta as P  # noqa: E402

STAMP = "  window.D2R_BUILD = { id:'%s', name:'%s - a ship', date:'2017-07-14', note:'%s' };\n"
BODY = "<html>\n<script>\n(function(){\n%s  var x = 1;\n})();\n</script>\n</html>\n"


def _git(repo, *args):
    r = subprocess.run(["git"] + list(args), cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError("git %s failed: %s" % (" ".join(args), r.stderr.strip()))
    return r.stdout.strip()


class _Repo(unittest.TestCase):

    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="page_delta_law_")
        self.addCleanup(shutil.rmtree, self.repo, True)
        _git(self.repo, "init", "-q")
        _git(self.repo, "config", "user.email", "law@example.invalid")
        _git(self.repo, "config", "user.name", "law")
        _git(self.repo, "config", "commit.gpgsign", "false")
        self.base = self.commit(BODY % (STAMP % ("v100", "v100", "first")))

    def commit(self, page_text, other=None):
        io.open(os.path.join(self.repo, "bible.html"), "w", encoding="utf-8").write(page_text)
        if other:
            io.open(os.path.join(self.repo, "other.txt"), "w", encoding="utf-8").write(other)
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", "c", "--allow-empty")
        return _git(self.repo, "rev-parse", "HEAD")

    def changed(self, head):
        return P.page_changed(["%s..%s" % (self.base, head)], repo=self.repo)[0]


class AStampIsNotAPageChange(_Repo):

    def test_baseline_the_name_alone_says_the_page_changed(self):
        # PREMISE: the old trigger (the file's NAME in the diff) fires on a stamp-only bump - the cost this law removes
        head = self.commit(BODY % (STAMP % ("v101", "v101", "second")))
        names = _git(self.repo, "diff", "--name-only", "%s..%s" % (self.base, head))
        self.assertIn("bible.html", names.split())

    def test_a_stamp_only_bump_is_not_a_page_change(self):
        head = self.commit(BODY % (STAMP % ("v101", "v101", "a note with an escaped \\' quote")))
        self.assertFalse(self.changed(head))

    def test_two_bumps_in_one_range_are_still_only_the_stamp(self):
        self.commit(BODY % (STAMP % ("v101", "v101", "second")))
        head = self.commit(BODY % (STAMP % ("v102", "v102", "third")))
        self.assertFalse(self.changed(head))

    def test_an_untouched_page_is_not_a_page_change(self):
        head = self.commit(BODY % (STAMP % ("v100", "v100", "first")), other="console only")
        self.assertFalse(self.changed(head))


class AnythingElseStillIs(_Repo):

    def test_a_real_page_change_is_a_page_change(self):
        head = self.commit((BODY % (STAMP % ("v100", "v100", "first"))).replace("var x = 1;", "var x = 2;"))
        self.assertTrue(self.changed(head))

    def test_a_stamp_and_a_page_change_together_are_a_page_change(self):
        head = self.commit((BODY % (STAMP % ("v101", "v101", "second"))).replace("var x = 1;", "var x = 2;"))
        self.assertTrue(self.changed(head))

    def test_code_smuggled_onto_the_stamp_line_is_a_page_change(self):
        smuggled = (STAMP % ("v101", "v101", "second")).rstrip("\n") + " window.evil = 1;\n"
        head = self.commit(BODY % smuggled)
        self.assertTrue(self.changed(head))

    def test_a_range_git_cannot_read_runs_the_gates(self):
        changed, why = P.page_changed(["no-such-ref..also-not"], repo=self.repo)
        self.assertTrue(changed)
        self.assertIn("UNKNOWN", why)

    def test_the_cli_exit_says_changed_on_a_bad_call(self):
        self.assertEqual(P.main([]), 0)


class TheJoinToTheWriter(unittest.TestCase):

    def test_the_pattern_matches_the_stamp_bump_version_wrote_into_this_tree(self):
        src = io.open(os.path.join(REPO, "bible.html"), encoding="utf-8").read()
        lines = [l for l in src.split("\n") if l.startswith("  window.D2R_BUILD = { id:'")]
        self.assertEqual(len(lines), 1, "PREMISE: the stamp line bump_version replaces is not exactly once")
        self.assertTrue(P.STAMP_LINE.match(lines[0]),
                        "the stamp line in this tree no longer matches page_delta.STAMP_LINE - bump_version's "
                        "format moved, so every bump would now read as a page change: %s" % lines[0][:160])


class TheHookAsksIt(unittest.TestCase):

    def setUp(self):
        raw = io.open(os.path.join(REPO, "hooks", "pre-push"), encoding="utf-8").read()
        self.code = "\n".join(l for l in raw.split("\n") if not l.lstrip().startswith("#"))

    def test_the_render_trigger_asks_page_delta_for_the_range_and_the_index(self):
        self.assertEqual(self.code.count('python3 "$REPO/tv/page_delta.py" --range "$_px_range"'), 1)
        self.assertEqual(self.code.count('python3 "$REPO/tv/page_delta.py" --cached'), 1)

    def test_the_smoke_trigger_asks_page_delta_for_each_ref(self):
        self.assertEqual(self.code.count(
            'python3 "$REPO/tv/page_delta.py" --range "$remote_sha..$local_sha" </dev/null'), 1)

    def test_bible_html_left_the_name_only_triggers(self):
        watch = re.findall(r"_px_watch='([^']*)'", self.code)
        self.assertEqual(len(watch), 1, "PREMISE: the render watch list is not declared exactly once")
        self.assertNotIn("bible", watch[0])
        self.assertNotIn("'^(bible\\.html|tests/.*\\.spec\\.ts)$'", self.code)


RED_PROOF = [
    {"why": "REG-1753 - every changed line counted as a stamp: a real page change skips render and smoke",
     "file": "page_delta.py",
     "find": "            if not STAMP_LINE.match(line[1:]):\n                return False\n",
     "replace": "            if False:\n                return False\n",
     "matches": 1},
    {"why": "REG-1753 - a stamp-only bump answered as a page change: the skip never happens",
     "file": "page_delta.py",
     "find": "        if stamp_only(diff.stdout):\n",
     "replace": "        if False:\n",
     "matches": 1},
    {"why": "REG-1753 - a range git cannot read answered as unchanged: the gates skip on an UNKNOWN",
     "file": "page_delta.py",
     "find": "        if names.returncode != 0:\n            return True, ",
     "replace": "        if names.returncode != 0:\n            return False, ",
     "matches": 1},
    {"why": "REG-1753 - the stamp pattern loosened to any D2R_BUILD line: code on the stamp line skips the gates",
     "file": "page_delta.py",
     "find": "    r\"date:'\\d{4}-\\d{2}-\\d{2}', note:'(?:[^'\\\\]|\\\\.)*' \\};\\s*$\")",
     "replace": "    r\"date:'\\d{4}-\\d{2}-\\d{2}', note:'(?:[^'\\\\]|\\\\.)*' \\};\")",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
