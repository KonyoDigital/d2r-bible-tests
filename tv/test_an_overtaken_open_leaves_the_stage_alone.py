# -*- coding: utf-8 -*-
"""v3305 (#59) — AN OVERTAKEN THEATRE OPEN MUST NOT TOUCH THE STAGE IT LOST.

HIS REPORT, five times: the theatre fails to open — and it is ALWAYS THE REOPEN AFTER A CLOSE,
never the first open. That pattern is the entire diagnosis.

THE MECHANISM, read out of tv/control_ui.html:

  · `thOpen()` sets `TH.open = true` BEFORE awaiting /api/sessions. That is deliberate (v859,
    "pixels BEFORE network"), and the wait is bounded at 8s by v2228.
  · For those 8 seconds `TH.open` is true, and the toggle is `if (TH.open) { thClose(); return; }`
    — so a SECOND CLICK IN THAT WINDOW closes the half-opened stage. Correct and desirable.
  · The still-pending `thOpen()` then resolves and UNCONDITIONALLY re-runs
    `TH.open = true; $('theatre').hidden = false; classList.add('theatre-open')` — re-showing a
    stage whose state `thClose()` has already torn down. Open, closed, then re-opened empty.

⚠⚠ AND THE MIRROR, which is easy to miss: the CATCH branch is just as unguarded. An open that
times out at 8s tears the stage down — even if the user has since closed it and opened it again
successfully. The abandoned attempt closes a stage belonging to a LATER open.

⚠ A BARE `if (TH.opening) return` IS NOT THE FIX. It makes the second click do nothing at all,
which is a different wrong behaviour: the close the user asked for is silently dropped. A
GENERATION counter keeps every click meaningful and silences only the loser.

⚠ THIS LAW READS SOURCE, so it obeys the rules that territory keeps teaching: comments stripped
before any assertion (the prose above the fix NAMES every symbol it looks for), both ends of every
slice anchored on real structure, and each assertion aimed at a LIVE EXPRESSION rather than at an
identifier that survives the feature being deleted.
[[source-reading-guard]] [[presence-law-vs-reachability-law]] [[the-unjoined-end]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

from frame_authority import _executable_only             # noqa: E402

UI = os.path.join(HERE, "control_ui.html")


def _code():
    with io.open(UI, encoding="utf-8") as fh:
        src = fh.read()
    return _executable_only(src, ".js")


def _between(body, start, end, who):
    i = body.find(start)
    assert i > -1, "could not find the start of %s" % who
    j = body.find(end, i + len(start))
    assert j > i, "could not find the end of %s — refusing to judge a slice whose far end is a guess"
    return body[i:j]


class TestAnOvertakenOpenLeavesTheStageAlone(unittest.TestCase):

    def setUp(self):
        self.code = _code()
        self.assertGreater(
            len(self.code), 200000,
            "the comment strip returned only %d chars of control_ui.html — it ran away, so every "
            "assertion below would be judging a fragment. [[zero-needs-a-denominator]]"
            % len(self.code))

    def test_the_open_captures_a_generation_before_it_waits(self):
        fn = _between(self.code, "async function thOpen()", "function thClose()", "thOpen")
        m = re.search(r"var\s+_thGen\s*=\s*\(\s*TH\.gen\s*=\s*\(\s*TH\.gen\s*\|\s*0\s*\)\s*\+\s*1\s*\)", fn)
        self.assertIsNotNone(
            m, "thOpen() does not claim a generation on entry. Without one there is no way for a "
               "resolved-but-overtaken attempt to know it lost, so it re-shows a torn-down stage.")
        wait = fn.find("await fetch('/api/sessions'")
        self.assertGreater(wait, -1, "thOpen no longer awaits /api/sessions")
        self.assertLess(
            m.start(), wait,
            "the generation is claimed AFTER the wait begins, so an open that is overtaken during "
            "the wait captures the winner's generation and believes it won.")

    def test_both_exits_after_the_wait_stand_down_when_overtaken(self):
        """⚠ BOTH. The happy path re-shows a dead stage; the catch tears down a live one."""
        fn = _between(self.code, "async function thOpen()", "function thClose()", "thOpen")
        guards = re.findall(r"if\s*\(\s*_thGen\s*!==\s*TH\.gen\s*\)\s*return\s*;", fn)
        self.assertGreaterEqual(
            len(guards), 2,
            "only %d stand-down guard(s) in thOpen; BOTH post-wait exits need one. The happy path "
            "re-shows a stage thClose() already tore down, and the catch closes a stage that "
            "belongs to a LATER open — the same defect arriving from the error path." % len(guards))

        # the happy-path guard must sit BEFORE anything that touches TH or the DOM
        after = fn[fn.find("j = await r.json();"):]
        g = after.find("if (_thGen !== TH.gen) return;")
        paint = after.find("TH.sessions =")
        self.assertGreater(g, -1, "no stand-down guard after the response is parsed")
        self.assertTrue(
            0 <= g < paint or paint == -1,
            "the guard sits AFTER the code that starts writing TH state, so an overtaken open has "
            "already changed the world before it stands down.")

    def test_the_close_invalidates_an_open_still_in_flight(self):
        fn = _between(self.code, "function thClose()", "function thLit()", "thClose")
        self.assertIsNotNone(
            re.search(r"TH\.gen\s*=\s*\(\s*TH\.gen\s*\|\s*0\s*\)\s*\+\s*1\s*;", fn),
            "thClose() does not bump the generation, so an open still in flight keeps the "
            "generation it captured, believes it won, and re-shows the stage after the teardown. "
            "That IS the reopen-after-close failure he reported five times.")
        # and it must happen BEFORE the teardown, or a resolve racing between the two still wins
        bump = fn.find("TH.gen = (TH.gen | 0) + 1;")
        shut = fn.find("TH.open = false")
        self.assertTrue(
            bump > -1 and shut > bump,
            "thClose() tears the stage down BEFORE invalidating the in-flight open, leaving a "
            "window in which a resolving open still believes it is the current one.")

    def test_the_fix_is_not_a_bare_busy_flag(self):
        """A busy flag drops the close the user asked for — a different wrong behaviour."""
        fn = _between(self.code, "async function thOpen()", "function thClose()", "thOpen")
        self.assertIsNone(
            re.search(r"if\s*\(\s*TH\.(opening|busy)\s*\)\s*return", fn),
            "thOpen() returns early on a bare busy flag. That silences the SECOND CLICK entirely, "
            "so the close he asked for never happens — the generation counter exists precisely so "
            "every click keeps its meaning and only the losing async attempt stands down.")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "without the close bumping the generation, the pending open re-shows a dead stage",
        "file": "tv/control_ui.html",
        "find": "    TH.gen = (TH.gen | 0) + 1;\n    TH.open = false; clearTimeout(TH.timer); TH.playing = false;",
        "replace": "    TH.open = false; clearTimeout(TH.timer); TH.playing = false;",
        "matches": 1,
    },
    {
        "why": "dropping the catch-side guard lets an abandoned open close a LATER open's stage",
        "file": "tv/control_ui.html",
        "find": "      if (_thGen !== TH.gen) return;\n      try {\n        TH.open = false;",
        "replace": "      try {\n        TH.open = false;",
        "matches": 1,
    },
    {
        "why": "claiming the generation after the wait means an overtaken open believes it won",
        "file": "tv/control_ui.html",
        "find": "    var _thGen = (TH.gen = (TH.gen | 0) + 1);",
        "replace": "    var _thGen = 0;",
        "matches": 1,
    },
]
