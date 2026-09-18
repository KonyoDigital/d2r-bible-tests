# -*- coding: utf-8 -*-
"""v3294 — AN INDEX OF RULINGS MUST NAME ITS OWN BLIND SPOT, OR IT IS WORSE THAN NONE.

Three times in one session a recorded ruling stopped me shipping the obvious fix, and each time I
found it by luck of grep. The ask was to make that a lookup.

⚠⚠ EXTRACTION WAS TRIED FIRST AND MEASURED DEAD. Four designs, one acceptance test - does it find
the three that actually stopped me?

    ⚠⚠ marker + prohibition language ...  223 entries, finds 0 of 3
    prohibition language, any marker ...  13,974 hits (2,547 even restricted to DO NOT / NEVER)
    topic + prohibition ...............  usable counts, finds v2397, MISSES v1631
    topic + comment blocks, no filter .  noisier (36 for "forge tab"), misses more

The reasons are structural: the warning marker is not a reliable key (v1631 carries none at all),
and the language is not distinctive - v1631's constraint is a plain fact in his own words with no
prohibition word in it. **A 223-row index that omits every ruling that matters is worse than no
index, because it reads as complete.**

⚠ AND THE FIRST MARKER COLLIDED. A plain `RULING:` matched NINE existing places on its first run -
comments quoting him with "HIS RULING:" - so the index would have opened with nine phantom
entries. `@@RULING` occurs zero times in the repo. A marker that can collide is not a marker.

⚠ THE SIGIL IS ASCII ON PURPOSE. A non-ASCII one inside a python entry point would trip the
encoding rule shipped one version earlier, which is a silly way to make a guard fight a guard.

So this file pins the two things that make the tool honest rather than decorative: it FINDS the
rulings that were seeded, and it always SAYS what it cannot see.
[[zero-needs-a-denominator]] [[unknown-stays-unknown]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import rulings  # noqa: E402


class TestARulingIndexAdmitsWhatItCannotSee(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = rulings.scan(ROOT)
        cls.text = " || ".join(r["text"] for r in cls.rows)

    def test_the_marker_cannot_collide_with_prose(self):
        """`RULING:` matched 9 places before this was measured; `@@RULING` matches only marks."""
        self.assertIn("@@RULING", rulings.MARK.pattern,
                      "the sigil was weakened to something prose can match, so the index will "
                      "open with phantom entries it presents as rulings")

    def test_it_finds_every_ruling_that_was_seeded(self):
        """Usefulness, not shape. An index that returns nothing passes every structural law."""
        self.assertGreaterEqual(len(self.rows), 4,
                                "fewer marked rulings than were seeded - one lost its marker")
        for needle, why in (
            ("a TAB is a label for a ROOM", "v1631: the Forge tab wears the rune colour"),
            ("the footer bar carries the VERSION AND NOTHING ELSE", "v2397: do not re-add the wall"),
            ("stay BELOW the reel list", "v2985: the river strip and pipeline board"),
            ("RIVER STRIP IS NOT THE DEFECT", "the lane-count ruling"),
        ):
            self.assertIn(needle, self.text, "the index lost %s" % why)

    def test_every_answer_says_what_it_cannot_see(self):
        """The half that keeps it honest: absence here is not permission."""
        import io as _io
        src = _io.open(os.path.join(ROOT, "tv", "rulings.py"), encoding="utf-8").read()
        self.assertIn("absence from this", src,
                      "the output no longer warns that an UNMARKED ruling is invisible, so an "
                      "empty result reads as a clearance")
        self.assertIn("is not permission", src,
                      "the strongest words in that sentence are gone - it is the whole reason "
                      "this index is safe to publish at all")
        # and it must be printed on BOTH paths, hits and no-hits
        self.assertEqual(src.count("_limit_sentence("), 3,
                         "the limit sentence must be defined once and printed on BOTH the "
                         "no-match path and the match path")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "weakening the sigil to prose-matchable re-opens the nine phantom entries",
        "file": "tv/rulings.py",
        "find": 'MARK = re.compile(r"@@RULING\\s*(v\\d{3,4})?\\s*:\\s*(.+?)(?=\\n\\s*\\n|\\*/|$)", re.S)',
        "replace": 'MARK = re.compile(r"RULING\\s*(v\\d{3,4})?\\s*:\\s*(.+?)(?=\\n\\s*\\n|\\*/|$)", re.S)',
        "matches": 1,
    },
    {
        "why": "dropping the blind-spot sentence lets an empty result read as a clearance",
        "file": "tv/rulings.py",
        "find": '            "list is not permission - it means nobody has marked it yet. BUGS.md holds the long "',
        "replace": '            "list is fine. "',
        "matches": 1,
    },
    {
        "why": "un-marking a seeded ruling is exactly the drift this index exists to prevent",
        "file": "tv/control_ui.html",
        "find": "    /* @@RULING v1631: a TAB is a label for a ROOM, an item NAME obeys the game.",
        "replace": "    /* v1631 note: a TAB is a label for a ROOM, an item NAME obeys the game.",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
