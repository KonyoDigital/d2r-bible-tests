# -*- coding: utf-8 -*-
"""v3404 — A MACHINE THAT IS NOT LAUNCHED BY A LAUNCHER MUST STILL UPDATE ITSELF.

His report, 2026-09-20: the KONYO ALT TEST console read CHILIAD 395 while his Mac read 401,
"moving even further away and still not being updated automatically".

MEASURED over SSH minutes after origin moved: HEAD bad246d (v3395), origin dbb92b6, BEHIND 5,
dirty 0, ZERO scheduled tasks matching d2r/claude/konyo/pull/bible/tv, ZERO startup entries, and
both consoles running as raw `pythonw`. Every automatic pull in this codebase lives in a LAUNCHER
(start_tvd_mac.sh:126, start_tvd_win.ps1:254), so a machine started any other way bypasses all of
them. It was current only because a human kept pulling by hand.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

SRC = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
DOC = io.open(os.path.join(HERE, "console_doctor.py"), encoding="utf-8").read()


def _code(src):
    """python with # comments AND docstrings stripped, so a guard never grades its own prose.

    ⚠⚠ THE DOCSTRING HALF IS NOT OPTIONAL, AND I LEARNED IT HERE. The first cut stripped only
    `#` comments, and `test_it_does_NOT_add_a_SECOND_re_exec_path` then went RED on the word
    "execv" inside `_pull_once`'s OWN DOCSTRING, which says it deliberately does not execv. A
    negative assertion that reads its own explanation accuses correct code. [[source-reading-guard]] 4

    ⚠⚠ #227 — AND THE STRIPPER ITSELF WENT BLIND, ON A ONE-LINE DOCSTRING. It cut every line at its
    first `#` and THEN paired triple quotes. control_app gained a one-line docstring that OPENS with a
    task tag (#223 — his answers ...): the cut took the closing quotes with it, every pair after that line flipped, and the stripped text
    kept prose and dropped code - 983,212 of 2,155,462 chars, the drift beat's `_pull_once()` among
    them. CI went red on a lane that was joined all along. The TOKENIZER knows what a comment and a
    string are; a regex over text that was already cut does not. Spans are BLANKED in place (newlines
    kept), so every offset, indent and next-def bound below means what it meant.
    [[source-reading-guard]] [[suspect-the-instrument]]
    """
    import tokenize
    lines = src.splitlines(True)
    off = [0]
    for l in lines:
        off.append(off[-1] + len(l))
    buf = list(src)
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT or (tok.type == tokenize.STRING and
                                                tok.string.lstrip("rRbBuUfF")[:3] in ('"""', "'''")):
                a = off[tok.start[0] - 1] + tok.start[1]
                b = off[tok.end[0] - 1] + tok.end[1]
                for k in range(a, b):
                    if buf[k] != "\n":
                        buf[k] = " "
    except (tokenize.TokenError, IndentationError, SyntaxError) as e:
        raise AssertionError("the source did not tokenize (%s) - UNKNOWN, not a pass" % e)
    return "".join(buf)


RED_PROOF = [
    {
        "why": "#227 - the stripper stops blanking prose: a guard reading control_app grades docstrings as code again",
        "file": "test_a_machine_pulls_itself_current.py",
        "find": "            if tok.type == tokenize.COMMENT or (tok.type == tokenize.STRING and\n",
        "replace": "            if tok.type == tokenize.COMMENT and (tok.type == tokenize.STRING and\n",
        "matches": 1,
    },
    {
        "why": "without the dirty-tree refusal the console pulls over work in progress - and HIS "
               "console execs the working tree, so on his Mac that lands on top of whatever is "
               "being edited right now",
        "file": "tv/control_app.py",
        "find": "    if _dirty:",
        "replace": "    if False:",
        "matches": 1,
    },
    {
        "why": "without the call in the drift beat the pull never runs, so the lane can only ever "
               "notice a pull somebody else performed - which on a machine started outside the "
               "launchers is nobody, forever",
        "file": "tv/control_app.py",
        "find": "                _pull_once()",
        "replace": "                pass",
        "matches": 1,
    },
    {
        "why": "without reading `behind` the heart row calls a machine five commits adrift healthy, "
               "which is exactly the state he reported and nothing surfaced",
        "file": "tv/console_doctor.py",
        "find": "    if behind > 0:",
        "replace": "    if False:",
        "matches": 1,
    },
]


class TestAMachinePullsItselfCurrent(unittest.TestCase):

    def test_the_pull_REFUSES_while_the_tree_has_tracked_edits(self):
        """⛔ THE GUARD THAT MATTERS MOST. His console execs the working tree, so an unguarded
        pull on his Mac would land on top of in-progress work. [[execs-the-working-tree]]"""
        code = _code(SRC)
        i = code.find("def _pull_once(")
        self.assertGreater(i, -1, "the pull lane is gone")
        blk = code[i:code.find("\ndef ", i + 1)]
        self.assertIn("--untracked-files=no", blk,
                      "the dirty check counts UNTRACKED files too, so a stray scratch file would "
                      "wedge the pull forever")
        self.assertIn("if _dirty:", blk,
                      "nothing refuses the pull when the tree has local tracked edits")

    def test_it_honours_the_same_switch_BOTH_launchers_obey(self):
        code = _code(SRC)
        i = code.find("def _pull_once(")
        blk = code[i:code.find("\ndef ", i + 1)]
        self.assertIn("TV_NO_AUTO_PULL", blk,
                      "a machine deliberately held back by TV_NO_AUTO_PULL would now be dragged "
                      "forward by this lane, against the switch both launchers honour")

    def test_the_stripper_survives_a_one_line_tagged_docstring(self):
        """#227 — the instrument itself: a docstring OPENING with a task tag must not flip the pairs."""
        q = '"' * 3
        fixture = ("def a():\n    " + q + "#223 a tagged one-liner" + q + "\n    y = 1\n\n"
                   "def b():\n    " + q + "prose" + q + "\n    _pull_once()\n")
        code = _code(fixture)
        self.assertIn("_pull_once()", code, "the stripper dropped code after a tagged one-line docstring")
        self.assertNotIn("prose", code, "the stripper kept a docstring: its pairs flipped")
        self.assertIn("y = 1", code)

    def test_the_pull_IS_JOINED_to_the_drift_beat(self):
        """⚠ [[the-unjoined-end]] — a puller nothing calls is the same defect as no puller."""
        code = _code(SRC)
        # ⚠ ANCHOR ON THE CALL, NEVER THE NAME. `code.find("_pull_once()")` matches `def
        # _pull_once():` first, which put the "join" 21,393 chars from the drift check and failed
        # a correctly joined lane. The call is INDENTED inside the beat; the definition is not.
        calls = [m.start() for m in re.finditer(r"\n\s+_pull_once\(\)", code)]
        self.assertEqual(len(calls), 1,
                         "expected exactly ONE call site for the pull, found %d - two callers "
                         "means two pull cadences and neither is the law" % len(calls))
        i = calls[0]
        j = code.find("d = _drift_once()", i)
        self.assertGreater(j, -1,
                           "the pull does not run in the drift lane, so nothing notices what it "
                           "pulled")
        self.assertLess(j - i, 600,
                        "the pull ran %d chars from the drift check - too far to be the same "
                        "beat" % (j - i))

    def test_it_does_NOT_add_a_SECOND_re_exec_path(self):
        """⚠ the relaunch path is already built and interlocked (drift_may_relaunch refuses
        mid-sweep). A second execv here would be [[copy-drift]] with a restart button on it."""
        code = _code(SRC)
        i = code.find("def _pull_once(")
        blk = code[i:code.find("\ndef ", i + 1)]
        self.assertNotIn("execv", blk,
                         "the pull re-executes the process itself instead of leaving that to "
                         "drift_may_relaunch, which has the sweep interlocks")

    def test_the_heart_row_reports_a_machine_that_is_BEHIND(self):
        code = _code(DOC)
        i = code.find("def _check_this_machine_is_keeping_itself_current(")
        self.assertGreater(i, -1, "the row that would have caught his 395-vs-401 gap is gone")
        blk = code[i:code.find("\ndef ", i + 1)]
        self.assertIn("HEAD..origin/main", blk, "the row no longer measures how far behind it is")
        self.assertIn("if behind > 0:", blk,
                      "the row measures `behind` and never acts on it - a machine five commits "
                      "adrift would read healthy")
        self.assertIn("MISSING", blk, "being behind the fleet is not reported as a fault")

    def test_UNKNOWN_is_kept_apart_from_LEVEL(self):
        """⚠ a failed comparison must never read as up to date. [[unknown-stays-unknown]]"""
        code = _code(DOC)
        i = code.find("def _check_this_machine_is_keeping_itself_current(")
        blk = code[i:code.find("\ndef ", i + 1)]
        self.assertGreaterEqual(blk.count("UNKNOWN"), 3,
                                "the row collapses 'could not ask' into a verdict")
        self.assertIn("never", blk.lower(),
                      "the row does not say out loud that a failed read is not a measured zero")

    def test_the_row_NEVER_fetches_on_an_eagle_tick(self):
        """⚠ [[a-gate-can-perturb-what-it-measures]] — the eagle runs constantly; a network call
        per tick is a new cost on the busiest surface in the console."""
        code = _code(DOC)
        i = code.find("def _check_this_machine_is_keeping_itself_current(")
        blk = code[i:code.find("\ndef ", i + 1)]
        self.assertNotIn('"fetch"', blk, "the heart row fetches from the network on every tick")
        self.assertIn("FETCH_HEAD", blk,
                      "the row does not date its reading, so 'level with origin' could be a "
                      "statement about last week")


if __name__ == "__main__":
    unittest.main(verbosity=2)
