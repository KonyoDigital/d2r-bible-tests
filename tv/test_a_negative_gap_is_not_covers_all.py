"""MORE STAMPS THAN THE CENSUS COUNTED MEANS THE CENSUS IS STALE — NEVER THAT IT COVERS EVERYTHING.

⚠⚠ MEASURED ON HIS LIVE CONSOLE 2026-09-10, GET /api/heart:

    instruments.proved        = 285      ->  _iCensus  = 285
    instruments.unproven      = 0
    instruments.provenAtCount = 289      ->  _iStamped = 289
                                             _iGap     = -4   ->  `_iGap > 0` is FALSE

`_iDenom` had exactly two arms below the UNKNOWN case: a FLOOR arm for `_iGap > 0`, and everything
else fell through to "and it covers all N gate(s) that carry a proof stamp". So with four MORE
stamps than the census counted, the panel asserted completeness — over the larger number — three
lines under a header reading `285 proven`. Two figures about gates, and the copy claimed all of them.

⚠ THE TWO FIGURES AGE INDEPENDENTLY, WHICH IS WHY THIS IS REACHABLE AND NOT A FREAK STATE.
`proved` moves only on a FULL census run. `provenAtCount` is the size of the per-gate `verdictAt`
map and grows on EVERY targeted `--prove`. Four targeted proves in one evening added four stamps
without moving the census, and the subtraction went negative. Any session that proves a handful of
gates reproduces it. [[stale-reading]] [[zero-needs-a-denominator]] [[label-outlived-referent]]

⚠ THE LAW IS BEHAVIOURAL. A gate that greps for `_iGap < 0` passes the day someone writes
`_iGap < -1` or reorders the arms. This one extracts the REAL expression and runs it under node
against the four states, then reads the sentence that comes out. [[source-reading-guard]]
"""
import io
import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.join(HERE, "control_ui.html")

if HERE not in sys.path:
    sys.path.insert(0, HERE)

# ⚠ verbosity=2 prints every docstring here and all of them open with a warning sign; on a cp1255
# console that is a crash WHILE REPORTING. This refusal blocked a push on 2026-09-10.
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()


def _between(src, start, end):
    """Text between two anchors, BOTH required. A fixed-size window reads a moved region as
    ABSENT, which is how this repo has lost measurements before. [[source-window-shortcut]]"""
    i = src.index(start)
    j = src.index(end, i + len(start))
    return src[i:j + len(end)]


def _denom_source():
    src = io.open(UI, encoding="utf-8").read()
    return _between(src, "var _iCensus = ((typeof d.proved === 'number')",
                    "gate(s) that carry a proof stamp') : '')));")


def _run(cases):
    """Evaluate the REAL _iDenom expression against each case. -> [sentence]"""
    js = """
    var CASES = %s;
    var out = [];
    for (var i = 0; i < CASES.length; i++) {
      var d = CASES[i];
      %s
      out.push(_iDenom);
    }
    console.log(JSON.stringify(out));
    """ % (json.dumps(cases), _denom_source())
    r = subprocess.run([shutil.which("node"), "-e", js],
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("node could not evaluate _iDenom — UNKNOWN, not passing: %s"
                             % (r.stderr or "")[:500])
    return json.loads(r.stdout.strip())


HIS_LIVE = {"proved": 285, "unproven": 0, "provenAtCount": 289}     # measured 2026-09-10, gap -4
TODAY = {"proved": 287, "unproven": 0, "provenAtCount": 291}        # same store after 2 more gates
# ⚠⚠ THE SMALLEST NEGATIVE GAP, AND THE EYE HAD TO ASK FOR IT. v2911 shipped with HIS_LIVE as the
# ONLY negative fixture, gap -4. The cross-family eye rewrote the arm to `_iGap < -1` and ran the
# real expression: HIS_LIVE stayed green while gap -1 rendered "covers all 289" — the original bug,
# with the whole suite passing. A single tested-but-unproven gate is the smallest real form of this
# state, so it is the one the law must pin. [[feedback-threshold-above-the-ceiling]]
NEAR = {"proved": 288, "unproven": 0, "provenAtCount": 289}         # gap -1
EXACT = {"proved": 289, "unproven": 0, "provenAtCount": 289}
FLOOR = {"proved": 285, "unproven": 4, "provenAtCount": 280}
NO_COUNT = {"proved": 285, "unproven": 0}


@unittest.skipIf(shutil.which("node") is None,
                 "node is absent — this law is UNMEASURED, not passing")
class ANegativeGapIsNotCoversAll(unittest.TestCase):

    def test_this_gate_reached_the_expression_it_grades(self):
        """⚠ REACH FIRST. If `_iDenom` were renamed or restructured, every law below would grade an
        empty string and pass for the wrong reason. [[source-reading-guard]]"""
        src = _denom_source()
        self.assertGreater(len(src), 200, "the _iDenom expression came back at %d chars — this "
                                          "gate did not reach its subject" % len(src))
        for token in ("_iCensus", "_iStamped", "_iGap", "_iDenom"):
            self.assertIn(token, src, "%s is gone from the expression this gate grades — the law "
                                      "must be re-derived, not assumed" % token)

    def test_his_measured_state_does_not_claim_to_cover_everything(self):
        """THE ONE THAT MATTERS. 285 counted, 289 stamped: the sentence must report a stale census,
        and must not contain the words that assert completeness."""
        got = _run([HIS_LIVE])[0]
        self.assertNotIn("covers all", got,
                         "with 289 stamps against a census of 285, the panel says %r — it asserts "
                         "completeness over the LARGER number while the header says 285 proven"
                         % got)
        self.assertIn("289", got, "the sentence must still name how many gates carry a stamp: %r" % got)
        self.assertIn("4", got, "the sentence must name the size of the drift (289 - 285 = 4): %r" % got)
        low = got.lower()
        # ⚠⚠ v2913 — THE CAUSE v2911 NAMED WAS WRONG, AND THIS LAW ENFORCED THE WRONG WORD.
        # It asserted the sentence say the census is "OLDER"/"stale". MEASURED on his store:
        # proved 287 · unproven 0 · verdictAt 291, gap -4 = 1 BLIND (test_the_river_has_an_outlet)
        # + 3 tested-but-unproven (test_end_routes, test_render_coverage,
        # test_the_harness_isolates_the_world). `verdictAt` counts every gate TESTED; proved+unproven
        # counts PROVEN plus never-declared. The gap is STRUCTURAL — a full census does not close it,
        # and across four targeted proves proved went 285->287 with verdictAt 289->291 TOGETHER while
        # the gap stayed -4. A right number under a wrong reason sends him to re-run a census he just
        # ran. [[label-outlived-referent]]
        self.assertTrue("tested" in low,
                        "the sentence must name what the extra stamps ACTUALLY are — gates that "
                        "were TESTED and did not come back proven: %r" % got)
        self.assertNotIn("older", low,
                         "the census is NOT older than the stamps; the two count different things "
                         "and the gap is structural. That wording sends him to re-run a census "
                         "that just ran: %r" % got)

    def test_a_gap_of_MINUS_ONE_is_caught_too(self):
        """⚠ THE HOLE THE EYE FOUND. One tested-but-unproven gate is the smallest form of this
        state. v2911's only negative fixture was gap -4, so tightening the arm to `_iGap < -1` left
        the suite fully green while a one-stamp drift rendered `covers all` again. A law with one
        fixture on the arm it exists to protect is a threshold nobody measured."""
        got = _run([NEAR])[0]
        self.assertNotIn("covers all", got,
                         "with 289 tested against 288 proven, the panel says %r — it asserts "
                         "completeness over the larger number for a ONE-gate drift" % got)
        self.assertIn("289", got, "must still name how many were tested: %r" % got)
        self.assertIn("1", got, "must name the size of the drift (289 - 288 = 1): %r" % got)

    def test_todays_reading_of_his_own_store_is_handled(self):
        """The same store two gates later. The gap is STRUCTURAL, so it stayed -4 while both figures
        moved — this fixture exists so a future reader can see that is expected, not drift."""
        got = _run([TODAY])[0]
        self.assertNotIn("covers all", got, "287/0/291 must not claim completeness: %r" % got)
        self.assertIn("291", got, "must name the tested count: %r" % got)
        self.assertIn("4", got, "must name the drift (291 - 287 = 4): %r" % got)

    def test_the_three_other_states_keep_their_own_words(self):
        """⚠ A fix that repairs one arm by breaking its siblings is not a fix. The FLOOR, EXACT and
        UNKNOWN arms must be untouched — this is the regression half of the law."""
        floor, exact, unknown = _run([FLOOR, EXACT, NO_COUNT])
        self.assertIn("FLOOR", floor, "the gap>0 arm lost its FLOOR wording: %r" % floor)
        self.assertIn("covers only 280 of 289", floor,
                      "the FLOOR arm must still name stamped-of-census: %r" % floor)
        self.assertIn("covers all 289", exact,
                      "a gap of exactly 0 genuinely does cover all, and must keep those words: %r"
                      % exact)
        self.assertIn("UNKNOWN", unknown,
                      "with no provenAtCount at all the answer is UNKNOWN, never a number: %r"
                      % unknown)

    def test_every_arm_glues_its_separator_to_the_clause_it_introduces(self):
        """A `·` must never end a line pointing at a clause that wrapped away from it — the v2905
        finding, which this new arm must not reintroduce. [[visual-regression-detector]]"""
        for name, got in zip(("gap-4", "today", "gap-1", "floor", "exact", "unknown"),
                             _run([HIS_LIVE, TODAY, NEAR, FLOOR, EXACT, NO_COUNT])):
            if not got:
                continue
            self.assertNotIn("· ", got,
                             "the %s arm separates with an ordinary space after the dot, so the "
                             "dot can end a line: %r" % (name, got))


RED_PROOF = [
    {
        "why": "deleting the negative arm's test drops his measured state back into 'covers all "
               "289' — the exact sentence measured on his console on 2026-09-10.",
        "file": "control_ui.html",
        "find": "          : (_iGap < 0\n",
        "replace": "          : (false\n",
        "matches": 1,
    },
    {
        "why": "the threshold the EYE actually broke it with. `_iGap < -1` leaves the gap -4 "
               "fixture green while a ONE-gate drift renders 'covers all' again — which is why "
               "this suite now carries a gap -1 fixture. [[feedback-threshold-above-the-ceiling]]",
        "file": "control_ui.html",
        "find": "          : (_iGap < 0\n",
        "replace": "          : (_iGap < -1\n",
        "matches": 1,
    },
    {
        "why": "restoring the WRONG CAUSE. v2911 said the census is 'OLDER than the stamps'; the "
               "gap is structural (tested vs proven), so that wording sends him to re-run a census "
               "that just ran — a right number under a wrong reason.",
        "file": "control_ui.html",
        "find": "more than this census counts as proven \u2014 those were tested and did NOT'",
        "replace": "more than this census counted \u2014 the census is OLDER than the stamps and did NOT'",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
