# -*- coding: utf-8 -*-
"""v3362 (#37) — ONE BANNER, ONE SENTENCE, ONE WRITER, AND IT NEVER CLAIMS A SEPARATE ECONOMY.

HIS RULING: the machine-identity banner may claim *"its own world"* and must NOT claim *"separate
economy"*. One banner, one sentence, one writer.

#37 was blocked all day on a single value only the GrokBot seat could read. It arrived at ~17:25
IDT — `window.D2R_BUILD.id = 'v3360'`, with the banner rendering as **"LINUX — its own world ·
Mac untouched"** — and the value revealed there was nothing to fix. MEASURED in bible.html:

    'its own world'     L3840 COMMENT · L4274 COMMENT · L48984 CODE   -> ONE code writer
    'Mac untouched'     L48984 CODE                                    -> the same one
    'separate economy'  L42631 COMMENT · L42653 · L42749 · L48928      -> ALL FOUR are the LADDER

So the ruling is already kept, and this law exists so it cannot quietly stop being kept.

=== ⚠⚠ THE LADDER RIBBON IS NOT THIS BANNER AND MUST NOT BE SWEPT INTO IT ===
`ladder-ribbon` says "🪜 LADDER ACCOUNT — separate economy · your main account is untouched", and
that claim is TRUE of the ladder: items forged on a ladder character genuinely do not sync to main.
A law that banned the phrase file-wide would delete a correct sentence about a different subject —
the four-in-one-file trap where one phrase serves two features. This law pins the MACHINE banner by
its own writer and leaves the ladder alone, and a case below proves it leaves it alone.

⚠ COMMENTS ARE NOT CLAIMS. Two of the three 'its own world' hits are prose explaining the feature.
Grading them as writers would make the law red on documentation, which is the defect
[[source-reading-guard]] §4 exists for and which has cost this repo five versions.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

BIBLE = os.path.join(ROOT, "bible.html")

#: the machine banner's own writer — the only line that composes the sentence he reads
WRITER = "' — its own world · Mac untouched'"
#: the ladder's ribbon, a DIFFERENT feature whose "separate economy" claim is correct
LADDER = "id='ladder-ribbon'"


def _code():
    """bible.html with `//` comments stripped — claims only, never the prose about them."""
    with io.open(BIBLE, encoding="utf-8") as fh:
        raw = fh.read()
    out = []
    for line in raw.split("\n"):
        t = line.lstrip()
        out.append("" if t.startswith("//") else line)
    return "\n".join(out), raw


class TheMachineBannerIsOneSentence(unittest.TestCase):

    def setUp(self):
        self.code, self.raw = _code()

    def test_exactly_one_writer(self):
        """⚠⚠ THE CASE. ONE banner, ONE sentence, ONE writer — his words."""
        n = self.code.count(WRITER)
        self.assertEqual(
            n, 1,
            "the machine banner is composed in %d place(s). His ruling is ONE writer: two writers "
            "drift the day one is edited, and the reader cannot tell which sentence he is looking "
            "at." % n)

    def test_it_never_claims_a_separate_economy(self):
        """⚠ THE FORBIDDEN CLAIM, checked on the BANNER, not on the file."""
        i = self.code.find(WRITER)
        self.assertGreater(i, -1, "the machine banner's writer is gone — this law lost its target")
        a = self.code.rfind("\n", 0, max(0, i - 400))
        b = self.code.find("\n", i)
        seg = self.code[a if a > 0 else 0:b if b > i else i + 200]
        self.assertNotIn(
            "separate economy", seg,
            "the machine banner claims a SEPARATE ECONOMY. His ruling permits 'its own world' and "
            "forbids that: a second machine having its own storage is not a second economy, and "
            "saying so would tell him his items live somewhere they do not.")

    def test_it_still_makes_the_permitted_claim(self):
        """⚠ THE BASELINE. Without it the law passes on a banner that says nothing at all.
        [[regression-guard]] §5"""
        self.assertIn(
            "its own world", self.code,
            "the banner no longer claims 'its own world' — the one thing his ruling permits it to "
            "say. A banner that says nothing is not compliance, it is an empty surface.")

    def test_the_ladder_ribbon_is_left_alone(self):
        """⚠⚠ THE SAFETY, and it is the reason this law is narrow. 'separate economy' is TRUE of
        the ladder: items forged on a ladder character do not sync to main. A file-wide ban would
        delete a correct sentence about a different feature."""
        self.assertIn(LADDER, self.raw,
                      "the ladder ribbon is gone — if that was deliberate this law's safety case "
                      "has lost its subject and should be retired on purpose, not left passing")
        i = self.raw.find(LADDER)
        seg = self.raw[i:i + 400]
        self.assertIn(
            "separate economy", seg,
            "the ladder ribbon stopped saying 'separate economy'. That claim is CORRECT there and "
            "this law must never be the reason it was removed — it pins the machine banner only.")

    def test_the_two_are_not_the_same_element(self):
        """A single element serving both claims would make every assertion above ambiguous."""
        i, j = self.code.find(WRITER), self.raw.find(LADDER)
        self.assertGreater(i, -1)
        self.assertGreater(j, -1)
        self.assertGreater(
            abs(i - j), 200,
            "the machine banner and the ladder ribbon are composed within 200 chars of each other, "
            "so 'the banner' and 'the ribbon' may no longer be separable by position and this "
            "law's windows cannot be trusted to grade the right one.")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "a second writer for the same banner is exactly what his ONE WRITER ruling forbids; "
               "two copies disagree the day one is edited",
        "file": "bible.html",
        "find": "_wt.className='cr-txt'; _wt.textContent=' ' + _wm.w + ' — its own world · Mac untouched';",
        "replace": "_wt.className='cr-txt'; _wt.textContent=' ' + _wm.w + ' — its own world · Mac untouched';\n  var _wt2=' ' + _wm.w + ' — its own world · Mac untouched';",
        "matches": 1,
    },
    {
        "why": "making the machine banner claim a separate economy is the one thing his ruling "
               "forbids it to say",
        "file": "bible.html",
        "find": " — its own world · Mac untouched'",
        "replace": " — its own world · separate economy · Mac untouched'",
        "matches": 1,
    },
    {
        "why": "dropping the permitted claim leaves an empty banner, which is not compliance",
        "file": "bible.html",
        "find": "' — its own world · Mac untouched'",
        "replace": "''",
        "matches": 1,
    },
]
