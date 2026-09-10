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


HIS_LIVE = {"proved": 285, "unproven": 0, "provenAtCount": 289}     # measured 2026-09-10
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
        self.assertTrue("older" in low or "stale" in low,
                        "a negative gap means the census is OLDER than the stamps, and the "
                        "sentence must say so rather than describing coverage: %r" % got)

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
        for name, got in zip(("negative", "floor", "exact", "unknown"),
                             _run([HIS_LIVE, FLOOR, EXACT, NO_COUNT])):
            if not got:
                continue
            self.assertNotIn("· ", got,
                             "the %s arm separates with an ordinary space after the dot, so the "
                             "dot can end a line: %r" % (name, got))


RED_PROOF = [
    {
        "why": "deleting the negative arm's test drops his measured state straight back into "
               "'covers all 289' — the exact sentence measured on his console on 2026-09-10.",
        "file": "control_ui.html",
        "find": "          : (_iGap < 0\n",
        "replace": "          : (false\n",
        "matches": 1,
    },
    {
        "why": "a threshold below every reachable value is an ABSENT branch wearing a condition. "
               "-1000 can never be met by a real drift, so the arm never runs and the negative "
               "state falls through to 'covers all' again. [[feedback-threshold-above-the-ceiling]]",
        "file": "control_ui.html",
        "find": "? (' \u00b7\u00a0and ' + _iStamped + ' gate(s) carry a proof stamp, ' + (-_iGap)",
        "replace": "? (_iGap < -1000 ? (' \u00b7\u00a0and ' + _iStamped + ' gate(s) carry a proof stamp, ') : (' \u00b7\u00a0and it covers all ' + _iStamped + ' gate(s) that carry a proof stamp, ')) + ((-_iGap)",
        "matches": 1,
    },
    {
        "why": "removing the word that names the finding: the sentence still prints both numbers "
               "but no longer says the census is OLDER, so a stale reading reads as a tidy one.",
        "file": "control_ui.html",
        "find": " more than this census counted — the census is OLDER than the stamps",
        "replace": " more than this census counted",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
