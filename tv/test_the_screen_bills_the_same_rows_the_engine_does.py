# -*- coding: utf-8 -*-
"""v3309 — THE SCREEN BILLS THE SAME ROWS THE ENGINE DOES, AND SAYS NEVER ONLY WHEN IT MEANS IT.

⚠⚠ BOTH HALVES WERE VISIBLE IN HIS OWN SCREENSHOT, which is the point: these are not theoretical.

HALF 1 — THE PANEL WAS THE FIFTH COPY OF THE PARTITION.
His console, v3307: *"9 thing(s) are waiting on YOU ... ⚠ the counter and this panel disagree
(you 9 vs 11 shown) — a row was counted that this panel did not draw"*. The arithmetic names it:
**11 − 9 = 2, the two BY_DESIGN rows**. v3307 taught the ENGINE that a row ruled NOT-A-DEFECT stops
billing him; v3308 taught the ROUTE; the panel still bucketed by its own rule and knew only
`mineWhat`, so it swept them into WAITING ON YOU.

⚠ THE DISAGREEMENT WARNING IS THE SYSTEM WORKING, NOT THE DEFECT. v3284 added it precisely so a
headline and a list could not diverge in silence, and it caught this within minutes of the ship.
Silencing the warning instead of closing the gap would have been the real failure.

⚠ AND THEY MUST STAY ON SCREEN. A BY_DESIGN row MOVES to its own heading; it does not vanish. A row
that leaves his count with nothing showing where it went is silencing by another name — the one
thing the MINE roster's own comment forbids.

HALF 2 — "NEVER" WAS PRINTED ABOUT A ROW ASKED TWO MINUTES AGO.
Same screenshot: *"ENGINES CORROBORATE **NEVER** — not asked this tick (PERIODIC — every 6 eagle
ticks; next ask in 2) · last asked 2m ago, last state missing"*. The SENTENCE was right and the
WORD was wrong: the panel mapped `unmeasured` to NEVER unconditionally, because the payload gave it
no way to tell two different facts apart —

    everAsked False -> genuinely never asked since the sidecar began
    everAsked True  -> asked before, simply NOT ON THIS TICK; carries its last verdict and age,
                       and does NOT bill him (his #35 standing rule)

The engine now PERSISTS that distinction instead of leaving the screen to recover it from prose.
A reader that must parse a sentence to recover a fact the writer already knew is the defect
heart-first rule 6 names. [[copy-drift]] [[label-outlived-referent]] [[unknown-stays-unknown]]
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


def _ui():
    with io.open(UI, encoding="utf-8") as fh:
        src = fh.read()
    # ".js" IS correct here — control_ui.html is JS/HTML and the branch strips // and /* */.
    # (It is WRONG for a .py file, which is a separate scar; see test_failure_attribution.)
    return _executable_only(src, ".js")


class TestTheScreenBillsTheSameRowsTheEngineDoes(unittest.TestCase):

    def setUp(self):
        self.code = _ui()
        self.assertGreater(
            len(self.code), 200000,
            "the comment strip returned only %d chars of control_ui.html — it ran away, so every "
            "assertion below would judge a fragment. [[zero-needs-a-denominator]]" % len(self.code))

    # ── HALF 1 ───────────────────────────────────────────────────────────────────────────────
    def test_the_panel_buckets_by_design_rows_out_of_waiting_on_you(self):
        self.assertIn(
            "e.byDesignWhat", self.code,
            "the panel never reads byDesignWhat, so a row the ENGINE ruled not-a-defect is still "
            "bucketed as WAITING ON YOU. That is his 9-vs-11: the counter excluded 2 rows and the "
            "panel drew them anyway.")
        self.assertIn(
            "designRows.push(h)", self.code,
            "there is no by-design bucket; byDesignWhat is read and then thrown away.")
        # ⚠ ORDER MATTERS: the design test must come BEFORE the youRows fallback, or the rows
        # still land in his count no matter what is read.
        # ⚠ v3335 — RE-ANCHORED. v3326 hoisted the name out: `_designWhat[String(r && r.check)]`
        # became `_designWhat[_nm]`. The refactor is an improvement; this find() went
        # stale with it and the gate has been red in CI ever since, while the pre-push
        # hook (a SUBSET) printed green. [[regression-guard]] §4 — pin the LAW.
        i = self.code.find("_designWhat[_nm]")
        j = self.code.find("else youRows.push(h)")
        self.assertGreater(i, -1, "the by-design test is gone from the bucketing")
        self.assertTrue(
            0 <= i < j,
            "the by-design test sits AFTER the youRows fallback, so every by-design row reaches "
            "his count first and the bucket below can never be entered.")

    def test_a_by_design_row_is_still_DRAWN_under_its_own_heading(self):
        """⚠ MOVED, NOT HIDDEN. A row that vanishes is silencing by another name."""
        self.assertIn(
            "RED ON PURPOSE", self.code,
            "there is no heading for the by-design rows, so they leave WAITING ON YOU and appear "
            "nowhere at all — the count drops and he is shown nothing explaining where they went.")
        m = re.search(r"_vxSection\('RED ON PURPOSE[^']*',\s*designRows\)", self.code)
        self.assertIsNotNone(
            m, "the RED ON PURPOSE heading exists but is not rendered with designRows, so the "
               "section is a label over the wrong list (or over nothing).")

    def test_the_fourth_bucket_has_a_gap_check_like_the_other_three(self):
        """A bucket nobody counts is the next place a row goes missing unnoticed."""
        self.assertIn(
            "by-design ' + _nDesign + ' vs ' + designRows.length", self.code,
            "the by-design bucket has no counter-vs-drawn check, while you/code/not-measured all "
            "have one. That asymmetry is exactly how this defect hid: the gap warning is what "
            "caught it, so the new bucket must be watched the same way.")

    # ── HALF 2 ───────────────────────────────────────────────────────────────────────────────
    def test_never_and_not_this_tick_are_different_words(self):
        self.assertIn(
            "r.everAsked ? 'NOT THIS TICK' : 'NEVER'", self.code,
            "the panel still maps `unmeasured` to NEVER unconditionally. His screen said NEVER "
            "about a check asked TWO MINUTES earlier, directly above a sentence saying so — the "
            "word contradicting the line under it.")

    def test_the_engine_persists_the_distinction_rather_than_leaving_it_in_prose(self):
        """BEHAVIOURAL. A panel that had to parse the why-sentence would be re-deriving a fact
        the writer already had — heart-first rule 6."""
        import console_doctor as cd
        rows = cd.run(include_slow=False, include_periodic=False, tick=2)
        rows = rows.get("checks") if isinstance(rows, dict) else rows
        skipped = [r for r in rows if isinstance(r, dict) and r.get("notAsked")]
        self.assertTrue(
            skipped,
            "no PERIODIC row was skipped on a non-periodic pass, so this case measured nothing. "
            "[[zero-needs-a-denominator]]")
        for r in skipped:
            self.assertIn(
                "everAsked", r,
                "a skipped periodic row carries no `everAsked`, so the screen cannot tell "
                "genuinely-NEVER from not-asked-this-tick and must guess: %r" % (r.get("check"),))
            if r.get("everAsked"):
                self.assertIsNotNone(
                    r.get("lastState"),
                    "%r says it HAS been asked before but carries no lastState, so the verdict it "
                    "is supposed to be holding onto is gone. A stale reading must carry what it "
                    "last read. [[stale-reading]]" % (r.get("check"),))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "without the by-design bucket the panel bills him for rows the engine excluded (his 9 vs 11)",
        "file": "tv/control_ui.html",
        "find": "      else if (_designWhat[_nm]) designRows.push(h);\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "dropping the heading makes the rows vanish instead of move - silencing by another name",
        "file": "tv/control_ui.html",
        "find": "         + _vxSection('RED ON PURPOSE \\u2014 ruled not a defect, nothing for you to do', designRows)\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "mapping unmeasured to NEVER unconditionally says NEVER about a row asked 2 minutes ago",
        "file": "tv/control_ui.html",
        "find": "               : r.state === 'unmeasured' ? (r.everAsked ? 'NOT THIS TICK' : 'NEVER')",
        "replace": "               : r.state === 'unmeasured' ? 'NEVER'",
        "matches": 1,
    },
    {
        "why": "an engine that does not persist everAsked forces the screen to parse prose for it",
        "file": "tv/console_doctor.py",
        "find": '                             "everAsked": bool(_prev),',
        "replace": "",
        "matches": 1,
    },
]
