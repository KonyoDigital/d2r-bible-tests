# -*- coding: utf-8 -*-
"""v3310 (#56) — TWO LOOKS ARE TWO ROWS, AND A DISAGREEMENT REACHES THE HEART.

His #56 ruling: *ask the second eye TWICE and keep both; wire the disagreement to the heart.*

⚠⚠ THIS LAW EXISTS BECAUSE I CLAIMED TO BE OBEYING THAT RULING AND WAS NOT. Through the whole
v3301-v3309 arc I reported "asked twice, both looks agree". I was pasting the second look INTO the
first answer's text as a bracketed note, so `record_answer` wrote ONE row carrying both. The ledger
therefore contains no pairs from that arc, nothing can compute agreement from it, and no
disagreement could ever reach the heart.

MEASURED 2026-09-18 on tv/.second_eye.jsonl (817 rows):
    767 versions have a look
     21 have two or more REACHED looks carrying a verdict  (2.7%)
    and v3303 / v3307 / v3308 — the ones I reported as agreeing pairs — read SINGLE.

⚠ IT ALSO REFUTED A SECOND CLAIM OF MINE. I repeatedly cited v3297 as "same payload, opposite
verdicts 18s apart". The store shows THREE looks at v3297, all `findings` — AGREE. I stopped
quoting it. A claim the store cannot show is UNKNOWN, not evidence.

A second opinion that lives inside the first opinion's prose is not data. That is heart-first rule
6 — persist what you knew, not a summary of it — committed inside the mechanism built to catch it.
[[the-unjoined-end]] [[zero-needs-a-denominator]]

FOUR PROPERTIES:
  1. THREE STATES, never two. AGREE / DISAGREE / SINGLE, plus NONE. Collapsing SINGLE into AGREE
     would let one look pass as a corroborated pair, which is the whole defect.
  2. AN EMPTY SEAT IS NOT AN OPINION. reached=False is an unreachable eye — excluded from both
     sides, or two failed calls read as a unanimous verdict. [[unknown-stays-unknown]]
  3. THE CENSUS CARRIES ITS OWN REACH, and states that its rate is an UPPER BOUND — a second ROW
     is not always a second OPINION, because re-files and corrections against one version read as
     DISAGREE. A confident percentage from a 2.7% sample containing artifacts is the exact shape
     this repo keeps learning to distrust.
  4. IT IS MINE, NOT HIS. A SINGLE look is my omission; he cannot act on a look I did not take, so
     the check is named in MINE and never inflates the count he reads — his #35 standing rule.
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import second_eye_ledger as L                            # noqa: E402


def _tmp_ledger(rows):
    """Write a throwaway ledger and hand back its path. Never touches the real store."""
    import json
    import tempfile
    fd, path = tempfile.mkstemp(prefix="eye_", suffix=".jsonl")
    os.close(fd)
    with io.open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return path


class TestTwoLooksAreTwoRows(unittest.TestCase):

    def setUp(self):
        self.paths = []
        self.addCleanup(lambda: [os.unlink(p) for p in self.paths if os.path.exists(p)])

    def _at(self, rows):
        p = _tmp_ledger(rows)
        self.paths.append(p)
        return p

    def test_two_rows_that_differ_are_a_DISAGREEMENT(self):
        p = self._at([{"version": "v9001", "verdict": "clean", "reached": True},
                      {"version": "v9001", "verdict": "findings", "reached": True}])
        a = L.agreement("v9001", p)
        self.assertEqual(
            a["state"], "DISAGREE",
            "two looks at ONE payload returned different verdicts and this did not say DISAGREE. "
            "Which verdict shipped was then decided by timing rather than by the code, and nothing "
            "would ever say so. got=%r" % (a,))
        self.assertIn("INSTRUMENT", a["say"],
                      "the say does not name what the finding is ABOUT: %r" % a["say"])

    def test_two_rows_that_match_are_an_AGREEMENT(self):
        p = self._at([{"version": "v9002", "verdict": "clean", "reached": True},
                      {"version": "v9002", "verdict": "clean", "reached": True}])
        self.assertEqual(L.agreement("v9002", p)["state"], "AGREE")

    def test_ONE_row_is_SINGLE_and_never_AGREE(self):
        """⚠ THE ONE THIS LAW EXISTS FOR. Collapsing SINGLE into AGREE is what I did in prose."""
        p = self._at([{"version": "v9003", "verdict": "clean", "reached": True}])
        a = L.agreement("v9003", p)
        self.assertEqual(
            a["state"], "SINGLE",
            "a version looked at ONCE reported %r. One look cannot show whether the eye is steady "
            "on this payload, and calling it agreement is precisely the claim I made all through "
            "the v3301-v3309 arc without the rows to support it." % a["state"])

    def test_an_EMPTY_SEAT_is_not_an_opinion(self):
        """Two unreachable calls must never read as a unanimous verdict."""
        p = self._at([{"version": "v9004", "verdict": "", "reached": False},
                      {"version": "v9004", "verdict": "", "reached": False}])
        a = L.agreement("v9004", p)
        self.assertEqual(
            a["state"], "NONE",
            "two EMPTY SEATS reported %r. An unreachable eye is never agreement — that is the "
            "founding rule of this ledger, and it is why the push gate reads `reached`." % a["state"])
        self.assertEqual(a["empty"], 2, "the empty seats were not counted separately")

        # and one empty seat beside one real look is still a SINGLE look
        p2 = self._at([{"version": "v9005", "verdict": "", "reached": False},
                       {"version": "v9005", "verdict": "clean", "reached": True}])
        a2 = L.agreement("v9005", p2)
        self.assertEqual(
            a2["state"], "SINGLE",
            "an empty seat was counted as the second opinion, so an unreachable eye silently "
            "satisfied his ask-twice ruling. got=%r" % (a2,))

    def test_the_census_states_that_its_rate_is_an_UPPER_BOUND(self):
        """A rate over a 2.7% sample containing artifacts must not be presented as a measurement."""
        c = L.agreement_census()
        for k in ("versions", "askedTwice", "recent", "disagreed"):
            self.assertIn(k, c, "the census is missing %r, so its reach cannot be read" % k)
        self.assertIn(
            "UPPER BOUND", c["say"],
            "the census reports a disagreement figure without saying it is an upper bound. A "
            "second ROW is not always a second OPINION — re-files and corrections against one "
            "version read as DISAGREE — so an unqualified rate would be a confident number built "
            "from artifacts. [[zero-needs-a-denominator]]")
        self.assertLessEqual(
            c["askedTwice"], c["versions"],
            "more versions were asked twice than exist, so the denominator is wrong")

    def test_the_check_is_MINE_and_never_bills_him(self):
        """His #35 rule: he cannot act on a look I did not take."""
        import console_doctor as cd
        self.assertIn(
            "second eye asked twice", dict(cd.CHECKS),
            "the doctor has no second-eye agreement check, so a disagreement reaches no organ")
        self.assertIn(
            "second eye asked twice", getattr(cd, "MINE", {}) or {},
            "the check is not in MINE, so a look I failed to take would appear in the count HE "
            "acts on. Asking the eye twice is my job; billing him for my omission is exactly what "
            "the MINE roster exists to prevent.")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "collapsing SINGLE into AGREE lets one look pass as a corroborated pair",
        "file": "tv/second_eye_ledger.py",
        "find": '    if len(verdicts) == 1:',
        "replace": '    if False:',
        "matches": 1,
    },
    {
        "why": "counting an empty seat as an opinion makes two failed calls read as unanimous",
        "file": "tv/second_eye_ledger.py",
        "find": '    reached = [r for r in seen if r.get("reached") is not False]',
        "replace": '    reached = list(seen)',
        "matches": 1,
    },
    {
        "why": "a census that drops its upper-bound caveat presents artifacts as a measurement",
        "file": "tv/second_eye_ledger.py",
        # ⚠⚠ RE-ANCHORED v3437. The old anchor quoted ONE WRAPPED LINE of the census print,
        # and a parallel change to second_eye_ledger.py (the ECHO state, board #182) rewrapped
        # that print across different line boundaries. The anchor then matched ZERO and this
        # red-proof silently stopped running — the gate it certifies reading as proven while
        # being unproven. Same class as board #187's four rotted anchors, arriving from a
        # DIFFERENT direction: not a refactor of the subject, but a neighbouring edit to the
        # same file. ONE-OWNER-PER-FILE DOES NOT PROTECT A PROOF WHOSE ANCHOR LIVES IN SOMEONE
        # ELSE'S FILE. Anchored now on the shortest span that carries the LAW ("upper bound"),
        # not on a whole wrapped line, so re-wrapping cannot break it again.
        "find": '⚠ UPPER BOUND: a second ROW is not ',
        "replace": '(',
        "matches": 1,
    },
]
