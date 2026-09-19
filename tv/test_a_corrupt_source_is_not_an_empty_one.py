# -*- coding: utf-8 -*-
"""v3370 (#118) — A SOURCE THAT ARRIVED AND WOULD NOT PARSE IS NOT AN EMPTY ONE.

CI's swallow ratchet caught this ON THE DAY v3364 SHIPPED THE FILE, and it was then ignored for
five consecutive versions because nobody read CI:

    3b1d513d  v3363  Routine M  success
    5aaffe75  v3364  Routine M  FAILURE      <- v3364 is where affix_lexicon.py was added
    cb27b990 v3365 · e4c5ebc5 v3366 · 385edfac v3367 · 2a22046d v3368   all failure

    swallow ratchet — RANK 1 (a failed read handed back as DATA)
       baseline 70   now 71
       WHERE IT ROSE:  tv/affix_lexicon.py   0 -> 1  (+1)

THE SITE, and the ratchet's wording is exactly right:
    try:    rows = json.loads((blob or b"").decode("utf-8-sig", "replace"))
    except Exception:  return {}

WHY {} IS A LIE HERE. `build()` ALREADY distinguishes an ABSENT source and says so precisely —
"no source could be pulled — extractor present/MISSING, install present/MISSING". But a source that
ARRIVES AND WILL NOT PARSE became `{}` and sailed straight through: resolve() finds no hits, the
lexicon reports 0 affixes, and classify() answers UNKNOWN for every name in the game. On a screen
that reads as "the game has no such affixes", not as "I could not read the file" — a confident zero
with no author, on the exact 269 magicPrefix / 298 magicSuffix / 690 baseType vocabulary the item
work depends on. [[unknown-stays-unknown]] §1

⚠ THE RATCHET OFFERED TWO WAYS OUT AND ONLY ONE IS HONEST. "Either make the failure report UNKNOWN,
or — if the caller genuinely treats the default as failure — say so in a comment AT THE SITE and
lower the baseline deliberately." The caller does NOT treat {} as failure: it proceeds to build a
lexicon from it. So lowering the baseline to 71 would have been recording a defect as a decision.

⚠ ABSENT AND CORRUPT MUST NOT COLLAPSE INTO EACH OTHER EITHER. An absent blob is already counted in
`absent`; naming it "would not parse" would report the wrong cause and send the next reader hunting
a corrupt file that does not exist. `_blob is not None` is what keeps them apart, and the case below
pins it — a fix that trades one confident wrong answer for another is not a fix.
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402

_console_safe_enable()

import affix_lexicon as al  # noqa: E402

GOOD = b'[{"Key":"Fine","enUS":"Fine"},{"Key":"Sharp","enUS":"Sharp"}]'
EMPTY = b'[]'
CORRUPT = b'{not json at all'


class TestACorruptSourceIsNotAnEmptyOne(unittest.TestCase):

    def test_a_readable_blob_still_parses(self):
        self.assertEqual(al._strings(GOOD), {"fine": "Fine", "sharp": "Sharp"})

    def test_a_blob_that_parses_to_nothing_is_an_empty_dict(self):
        """MEASURED empty. This is a real answer and must NOT become None."""
        self.assertEqual(al._strings(EMPTY), {})

    def test_a_blob_that_will_not_parse_is_None(self):
        self.assertIsNone(al._strings(CORRUPT),
                          "a corrupt source handed back as {} is a failed read wearing a "
                          "measurement's clothes — the caller cannot tell it from an empty file")

    def test_empty_and_corrupt_do_not_compare_equal(self):
        """The whole defect in one line: `{} == {}` made these the same fact."""
        self.assertIsNot(al._strings(EMPTY), al._strings(CORRUPT))

    def test_build_refuses_on_a_corrupt_source_and_names_it(self):
        orig = al._pull
        try:
            al._pull = lambda path, timeout=None: CORRUPT
            lex, why = al.build()
        finally:
            al._pull = orig
        self.assertIsNone(lex, "a lexicon built from an unparseable source would report 0 affixes "
                               "with total confidence")
        self.assertTrue(why, "a refusal with no reason is not actionable")
        self.assertIn("parse", why.lower(),
                      "the reason must name the CAUSE; 'no source could be pulled' would blame the "
                      "extractor for a file that arrived fine")

    def test_every_source_absent_reads_as_absent_not_corrupt(self):
        orig = al._pull
        try:
            al._pull = lambda path, timeout=None: None
            lex, why = al.build()
        finally:
            al._pull = orig
        self.assertIsNone(lex)
        self.assertNotIn("parse", (why or "").lower(),
                         "nothing arrived, so nothing failed to parse — this must read as ABSENT")

    def test_one_absent_source_among_readable_ones_is_not_called_corrupt(self):
        """⚠ THE MIXED CASE IS THE ONLY ONE THAT REACHES THE CHECK.

        Stubbing EVERY source to None returns early on `len(absent) == len(SOURCES)`, so the
        unreadable test below it never runs and a sabotage of it stays green — measured, this case
        was BLIND on its first run for exactly that reason. One absent among readable ones is what
        drives execution through the line that separates ABSENT from CORRUPT.
        """
        paths = dict(al.SOURCES)
        aff = paths.get("nameaffixes")
        self.assertIsNotNone(aff, "SOURCES no longer carries nameaffixes; this case cannot reach "
                                  "its subject, which is a failure of the law")
        orig = al._pull
        try:
            al._pull = lambda path, timeout=None: (None if path == aff else GOOD)
            lex, why = al.build()
        finally:
            al._pull = orig
        self.assertIsNotNone(
            lex, "one ABSENT source was reported as unparseable and the whole build refused: %r. "
                 "Absent is already counted in `absent`; calling it corrupt names the wrong cause "
                 "and sends the next reader hunting a file that is merely missing" % (why,))

    def test_a_good_build_still_succeeds(self):
        orig = al._pull
        try:
            al._pull = lambda path, timeout=None: GOOD
            lex, why = al.build()
        finally:
            al._pull = orig
        self.assertIsNotNone(lex, "a readable source must still produce a lexicon: %r" % (why,))

    def test_verify_calls_a_corrupt_source_UNKNOWN_and_not_STALE(self):
        """THE HEART ROW READS THIS, AND THE OLD ANSWER NAMED THE WRONG CAUSE.

        `item vocabulary` maps verify()'s code to a verdict. Before this fix a corrupt source still
        produced a lexicon, so its sourceHash differed from the stored one and verify returned 1
        STALE — the row then told him "the install has changed since the lexicon was generated"
        when the truth was that a file could not be read. A confident wrong cause is worse than an
        unknown, because it sends him to re-generate against an install that never moved.

        Now build refuses, verify returns SKIP, and the row reads UNKNOWN carrying the real reason.
        ⚠ SKIP IS NOT GREEN — verify's own docstring says so. [[unknown-stays-unknown]]
        """
        orig = al._pull
        try:
            al._pull = lambda path, timeout=None: CORRUPT
            code, say = al.verify()
        finally:
            al._pull = orig
        self.assertEqual(code, al.SKIP,
                         "a source that would not parse must read as cannot-tell, not as STALE: "
                         "%r" % (say,))
        self.assertIn("parse", say.lower(),
                      "the reason must survive to the heart row, or it reads as a bare unknown")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "handing a failed read back as {} is the defect CI caught on the day the file shipped",
        "file": "tv/affix_lexicon.py",
        "find": "    except Exception:\n        return None\n    m = {}",
        "replace": "    except Exception:\n        return {}\n    m = {}",
        "matches": 1,
    },
    {
        "why": "without the check, build() proceeds and reports a lexicon of 0 affixes as though it had measured one",
        "file": "tv/affix_lexicon.py",
        "find": "    if _unreadable:\n        return None, (\"pulled but would not parse: %s",
        "replace": "    if False:\n        return None, (\"pulled but would not parse: %s",
        "matches": 1,
    },
    {
        "why": "dropping the arrived test makes an ABSENT source read as a corrupt one, which names the wrong cause",
        "file": "tv/affix_lexicon.py",
        "find": "                   if _blob is not None and _m is None]",
        "replace": "                   if _m is None]",
        "matches": 1,
    },
]
