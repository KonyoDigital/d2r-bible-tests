# -*- coding: utf-8 -*-
"""v3326 — THE STATUS WORD SAYS WHOSE ROW IT IS, INSTEAD OF SAYING MISSING FOUR TIMES.

His #35 ruling gives WAITING ON YOU a precise meaning, and v3321 built the sections for it. What
v3321 did not touch was the WORD inside them. MEASURED on his console at v3323 — he sent the
screenshots — every row in three different sections read MISSING:

    END ROUTES REACHABLE   MISSING   under a heading reading
                                     "RED ON PURPOSE — RULED NOT A DEFECT, NOTHING FOR YOU TO DO"
    THE RIVER              MISSING   same heading
    CONSOLE UI FAULTS      MISSING   its own sentence: "the console healed itself from 3 fault(s)
                                     in 24h ... It recovered"
    LEDGER PROVENANCE      MISSING   under "WAITING ON CODE — NOT YOURS TO FIX"

Absent, ruled-fine, already-recovered and owed-by-Claude are four different facts. One word for all
of them is the same collapse as a 0 standing in for UNKNOWN, one layer up in the vocabulary.

⚠ THIS IS A JOIN, NOT A NEW JUDGEMENT. `_sortRow` already computes the bucket from `mineWhat` and
`byDesignWhat` — the server has named the owner of every row since v3307. It simply did it on the
line AFTER the word was chosen, so the word could not see it. Nothing here decides ownership; it
only reads it one line earlier. [[the-unjoined-end]]

⚠ THE unmeasured/unknown WORDS ARE DELIBERATELY UNTOUCHED. CAN'T ASK / NEVER / NOT THIS TICK
already say the right thing, each with a reason and an age, and v3309 earned that distinction after
his screen said NEVER about a row asked two minutes earlier.

⚠⚠ AND THE BASELINE IS THE HALF THAT MATTERS. The cheap way to calm this panel is to stop saying
MISSING at all. A row that is genuinely his and genuinely absent must still read MISSING, in the
warn tone — pinned below, because a quieter panel that has stopped reporting is worse than a noisy
one.

⚠ IT STRIPS COMMENTS BEFORE READING. Load-bearing: the block explaining this change contains the
literal words BY DESIGN, CLAUDE OWES and MISSING, so a law reading raw source would be satisfied by
its own commentary — REG-1070, four times over. [[source-reading-guard]] §4b
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

from frame_authority import _executable_only  # noqa: E402

UI = os.path.join(HERE, "control_ui.html")


def _code():
    with io.open(UI, encoding="utf-8") as fh:
        src = fh.read()
    # ".js" takes the comment-stripping branch — _executable_only dispatches on EXTENSION.
    return _executable_only(src, ".js")


def _between(s, a, b):
    i = s.find(a)
    assert i > -1, "could not find %r" % a
    j = s.find(b, i + len(a))
    assert j > i, "could not find the end anchor %r after %r" % (b, a)
    return s[i:j]


class TestTheWordSaysWhoseRowItIs(unittest.TestCase):

    def setUp(self):
        self.code = _code()
        # A zero needs a denominator: a runaway strip makes every count meaningless.
        self.assertGreater(
            len(self.code), 200000,
            "the comment strip returned only %d chars of control_ui.html — it ran away, so any "
            "finding from it is meaningless. [[zero-needs-a-denominator]]" % len(self.code))

    def _fn(self):
        return _between(self.code, "function _vxHealthRow(", "function ")

    def test_the_word_can_see_the_bucket(self):
        self.assertIn(
            "function _vxHealthRow(r, bucket)", self.code,
            "_vxHealthRow does not take the bucket, so it cannot tell a ruling from a fault. The "
            "bucket is computed one line later in _sortRow and was simply never passed.")

    def test_a_ruled_row_and_a_claude_row_say_so(self):
        fn = self._fn()
        for want, why in (
            ("BY DESIGN", "a row under 'RULED NOT A DEFECT, NOTHING FOR YOU TO DO' still reads as "
                          "something absent"),
            ("CLAUDE OWES", "a row under 'WAITING ON CODE — NOT YOURS TO FIX' does not say whose "
                            "work it is"),
        ):
            self.assertIn(want, fn, "%s — expected the word %r in the chain" % (why, want))

    def test_a_row_that_is_genuinely_his_STILL_says_MISSING(self):
        """⚠ THE BASELINE. Quieting the panel by dropping the word would be worse than the noise."""
        fn = self._fn()
        self.assertIn(
            "'MISSING'", fn,
            "MISSING is gone entirely. A row that is his and genuinely absent must still say so — "
            "a panel that has stopped reporting is worse than one that reports bluntly.")
        self.assertTrue(
            re.search(r"r\.state === 'missing' \? 'MISSING'", fn),
            "the missing branch no longer yields MISSING for an unbucketed row.")

    def test_the_warn_tone_is_for_a_fault_he_must_act_on(self):
        fn = self._fn()
        self.assertTrue(
            re.search(r"tone\s*=\s*\(r\.state === 'missing' && !bucket\)", fn),
            "the warn tone is not conditioned on the bucket, so a ruling he has already closed "
            "and a backlog that is mine still shout at him in the fault colour.")

    def test_the_unmeasured_words_are_untouched(self):
        """v3309 earned these; this change must not disturb them."""
        fn = self._fn()
        for want in ("NOT THIS TICK", "NEVER", "CAN"):
            self.assertIn(want, fn, "the unmeasured/unknown vocabulary lost %r — those words were "
                                    "already correct and are not this change's business" % want)

    def test_the_bucket_is_decided_BEFORE_the_word(self):
        """Ordering is the whole defect: the bucket existed, one line too late."""
        blk = _between(self.code, "var _sortRow = function (r)", "(e.rows || []).forEach")
        i_bk = blk.find("_bk =")
        i_call = blk.find("_vxHealthRow(")
        self.assertGreater(i_bk, -1, "the bucket is no longer computed in _sortRow")
        self.assertGreater(i_call, -1, "_sortRow no longer builds a row")
        self.assertLess(
            i_bk, i_call,
            "the bucket is computed AFTER _vxHealthRow is called, which is exactly the v3323 "
            "state: the answer existed and arrived one line too late to be used.")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "dropping the bucket from the word chain sends every row back to MISSING",
        "file": "tv/control_ui.html",
        "find": "      var word = bucket === 'design' ? 'BY DESIGN'\n               : bucket === 'mine' ? 'CLAUDE OWES'\n",
        "replace": "      var word = ",
        "matches": 1,
    },
    {
        "why": "an unconditional warn tone makes a closed ruling shout in the fault colour",
        "file": "tv/control_ui.html",
        "find": "      var tone = (r.state === 'missing' && !bucket) ? 'warn' : '';",
        "replace": "      var tone = r.state === 'missing' ? 'warn' : '';",
        "matches": 1,
    },
    {
        "why": "computing the bucket after the call restores the exact v3323 ordering defect",
        "file": "tv/control_ui.html",
        # re-anchored #223: the ask-row branch now sits between the bucket and the call, so the
        # span is four lines; the tamper is the original one — the bucket moves BELOW the call
        "find": "      var _bk = _mineWhat[_nm] ? 'mine' : (_designWhat[_nm] ? 'design' : null);\n      var _open = (r && (r.openAsks || r.asks)) || [];\n      if (!_bk && _nyWhat && _nyWhat[_nm] && _open.length) { youRows.push(_vxAskRow(r, _open)); return; }\n      var h = _vxHealthRow(r, _bk); if (!h) return;",
        "replace": "      var _open = (r && (r.openAsks || r.asks)) || [];\n      if (!_bk && _nyWhat && _nyWhat[_nm] && _open.length) { youRows.push(_vxAskRow(r, _open)); return; }\n      var h = _vxHealthRow(r, _bk); if (!h) return;\n      var _bk = _mineWhat[_nm] ? 'mine' : (_designWhat[_nm] ? 'design' : null);",
        "matches": 1,
    },
]
