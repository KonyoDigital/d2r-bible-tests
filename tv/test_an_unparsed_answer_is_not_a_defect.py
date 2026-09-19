# -*- coding: utf-8 -*-
"""v3346 (#101) — AN UNPARSED ANSWER IS `cannot-tell`, NEVER A DEFECT.

MEASURED 2026-09-19 on four real looks taken the same day:

    version  _declares_none  structure  claims_defect   verdict BEFORE
    v3341    True            False      False           clean
    v3342    True            False      False           clean
    v3343    FALSE           False      False           findings   <- the defect
    v3344    True            False      False           clean

v3343's answer says, in plain words: *"The diff is correct. No defects, races, contract mismatches,
leaks, or unreachable states are present in the shown changes."* It was filed verdict=findings,
findings=1 — and the single "finding" was THE WHOLE ANSWER, REACH line and clean verdict included.

THE CAUSE IS THE PARSER, NOT THE DECLARATION. `_findings_from` starts a new block only on a numbered
or bulleted line and joins everything else onto the block above, so an answer with no such line comes
back as ONE block containing everything. That is not a defect the eye reported; it is a parse that
found no structure, relabelled as the worse of the two.

⛔ _declares_none IS NOT WIDENED, AND MUST NOT BE. The phrasing that slipped past it is a comma-tail
between "No defects" and "are present" — exactly the widening #76 measured and REFUSED, because
`_claims_a_defect` covers only 103 of 628 findings-rows, so the narrow declaration IS the safety.
That ruling stands. This law exists because the fix belongs somewhere else entirely.

=== THE BLAST RADIUS WAS MEASURED, AND THE FIRST DESIGN WAS REFUTED BY IT ===
My first cut fired on structure-absence alone. Against the real ledger that would have reclassified
**172 of 637** findings-rows — including v2180 *"FINDING 1: Saved OFF is overruled by an env ON —
auto-relaunch still arms"*, a real defect with no bullet at line start. That is precisely the "wrong
in both directions" trap `_verdict_for` has already fallen into twice (v2808, v3198), and the
measurement killed it before it shipped. [[regression-guard]] §5a

With the phrase test added the radius is **8 of 637**, and reading them they are the SAME defect
being corrected: v2805 "No defects found", v2850/v2851/v3207/v3266 "The diff is correct as shown",
v3147 "No concrete defects found". ⚠ ONE is a genuine wrong flip — v2837, "real hazard, cache never
cleared" — and it lands on `cannot-tell`, NOT on `clean`, so nothing is cleared and a re-read is
prompted. That is the safe direction this function's own docstring names: over-reporting costs a
re-read, under-reporting ships a defect with a clean stamp.

⚠ `cannot-tell` is not a new word — it is already in PARSER_VERDICTS and 13 rows use it.
[[unknown-stays-unknown]]
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

import second_eye_run as R  # noqa: E402
import second_eye_ledger as L  # noqa: E402

#: v3343's answer, verbatim — the row that exists because of it is in his ledger.
V3343 = (
    "REACH 5/5 files (control_app.py, test_*.py, tv_diablo.py, bible.html, control_ui.html) fully "
    "shown and judged; no truncation or missing named files.\n\n"
    "The diff is correct. No defects, races, contract mismatches, leaks, or unreachable states are "
    "present in the shown changes.\n")

#: a real findings answer as this eye actually writes them — numbered, so it HAS structure
NUMBERED = (
    "REACH: 100% of the diff.\n\n"
    "**Finding 1 (high, PROVEN)** `_cap` is read before assignment, so every call raises NameError.\n"
    "**Finding 2 (medium, PROVEN)** the retry loop never decrements and spins forever.\n")


def _verdict(answer):
    return R._verdict_for(answer, R._findings_from(answer))[0]


class TestAnUnparsedAnswerIsNotADefect(unittest.TestCase):

    def test_the_v3343_answer_is_cannot_tell_not_findings(self):
        """⚠⚠ THE CASE. A look that says the diff is correct must never be filed as a defect."""
        self.assertEqual(
            _verdict(V3343), "cannot-tell",
            "v3343's answer says 'The diff is correct. No defects ... are present' and is filed as "
            "%r. The single finding is the WHOLE ANSWER — a parse that found no structure, not "
            "something the eye reported." % _verdict(V3343))

    def test_a_numbered_findings_answer_is_untouched(self):
        """⚠ THE BASELINE. Real findings from this eye are numbered, so they HAVE structure and must
        take the existing path. Without this the law would pass over an arm that swallows everything.
        [[regression-guard]] §5"""
        self.assertTrue(R._has_finding_structure(NUMBERED),
                        "a numbered findings answer reports no structure — the start pattern has "
                        "stopped recognising how this eye actually writes findings")
        self.assertEqual(
            _verdict(NUMBERED), "findings",
            "a numbered list of two PROVEN defects came back %r. The arm must never reach an answer "
            "that parsed." % _verdict(NUMBERED))

    def test_a_structureless_answer_that_CLAIMS_a_defect_is_not_downgraded(self):
        """⚠ The dangerous direction. Prose that asserts a defect stays `findings`."""
        prose = ("The diff introduces a defect: the retry loop never decrements its counter, so a "
                 "failed call spins forever. This is a bug and it is reachable from the only caller "
                 "shown.\n")
        self.assertNotEqual(
            _verdict(prose), "cannot-tell",
            "a prose answer asserting a defect was downgraded to cannot-tell. The arm requires BOTH "
            "no defect claim AND a no-defect phrase; if this fires, one of those guards is gone.")

    def test_the_arm_never_produces_clean(self):
        """⛔ #76's ruling, pinned structurally. The phrase test may DOWNGRADE findings to
        cannot-tell; it may never CLEAR anything. _declares_none stays the only route to clean."""
        src = io.open(os.path.join(HERE, "second_eye_run.py"), encoding="utf-8").read()
        code = "\n".join(re.sub(r"#.*$", "", l) for l in src.split("\n"))
        i = code.find("_SAYS_NO_DEFECT_RX.search")
        self.assertGreater(i, -1, "the phrase test is no longer consulted at all")
        # ⚠ ANCHOR BOTH ENDS. A fixed byte window here ran past the guarded statement into the very
        # next line — `return ("findings" if findings else "clean"), findings` — and this law failed
        # on a `clean` that was never inside the arm. The region is "up to and including the first
        # return", not a byte count. [[source-reading-guard]] §3
        j = code.find("\n", code.find("return", i))
        self.assertGreater(j, i, "could not bound the guarded statement; refusing to judge a slice "
                                 "whose far end is a guess")
        seg = code[i:j]
        self.assertIn(
            '"cannot-tell"', seg,
            "the phrase test now guards something other than the cannot-tell return. It must never "
            "be able to produce `clean` — that is the whole reason it is allowed to exist beside "
            "the narrow _declares_none that #76 refused to widen.")
        self.assertNotIn(
            '"clean"', seg,
            "the phrase test can reach a `clean` return. That IS widening _declares_none by another "
            "name, and #76 measured that it cannot be made safe.")

    def test_one_definition_of_what_starts_a_finding(self):
        """[[copy-drift]] — the splitter and the structure test must ask the same question."""
        src = io.open(os.path.join(HERE, "second_eye_run.py"), encoding="utf-8").read()
        code = "\n".join(re.sub(r"#.*$", "", l) for l in src.split("\n"))
        self.assertEqual(
            code.count("_FINDING_START_RX = re.compile"), 1,
            "the finding-start pattern is defined more than once; two copies disagree the day one "
            "is edited.")
        self.assertGreaterEqual(
            code.count("_FINDING_START_RX"), 3,
            "the shared pattern is defined but not used by both the splitter and the structure "
            "test, so one of them still carries its own copy.")

    def test_the_blast_radius_on_his_real_ledger_stays_small(self):
        """⚠⚠ THE ONE THAT WOULD HAVE CAUGHT MY FIRST DESIGN. It flipped 172 of 637; this pins that
        a future loosening cannot quietly re-open that. Measured today: 8."""
        if not os.path.exists(L.LEDGER_PATH):
            self.skipTest("no ledger on this machine — the radius cannot be measured here")
        import json
        rows = []
        with io.open(L.LEDGER_PATH, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        pass
        fr = [r for r in rows
              if str(r.get("verdict")) == "findings" and str(r.get("answerHead") or "").strip()]
        if len(fr) < 50:
            self.skipTest("only %d findings-rows here; too few to size the radius" % len(fr))
        flip = [r for r in fr if _verdict(str(r.get("answerHead"))) == "cannot-tell"]
        self.assertLessEqual(
            len(flip), 20,
            "%d of %d findings-rows would be reclassified as cannot-tell. Measured at 8 when this "
            "law was written; the first design flipped 172 and was refused for it. A jump here means "
            "the arm has been loosened and is now reaching real findings."
            % (len(flip), len(fr)))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "removing the arm files a look that says the diff is correct as a defect again",
        "file": "tv/second_eye_run.py",
        "find": '            return "cannot-tell", []',
        "replace": '            pass',
        "matches": 1,
    },
    {
        "why": "dropping the phrase test widens the arm to 172 rows and swallows real findings",
        "file": "tv/second_eye_run.py",
        "find": "                and _SAYS_NO_DEFECT_RX.search(answer):",
        "replace": "                and True:",
        "matches": 1,
    },
    {
        "why": "a structure test that always answers True stops the arm firing on the case it exists for",
        "file": "tv/second_eye_run.py",
        "find": "    for ln in (answer or \"\").splitlines():\n        if _FINDING_START_RX.match(ln.strip()):\n            return True\n    return False",
        "replace": "    return True",
        "matches": 1,
    },
]
