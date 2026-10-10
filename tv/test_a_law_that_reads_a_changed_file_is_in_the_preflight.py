"""REG-2148 - a law that reads a changed file is named, and the hook's own set stays the test files.

gates_for_tests maps a changed tv/test_*.py onto its gate. A law that scans bible.html or
control_app.py is not in that set, so the Mac never runs it and CI goes red one version later.
laws_that_read is the other question. A basename that is too short to be a file name answers
nothing, because it would match inside unrelated words.
"""
import os
import unittest

import heart2


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SET_TILE = "test_a_set_piece_tile_says_the_name_the_game_shows"
STATUS = "test_the_status_breakdown_covers_what_it_bills"


class ALawThatReadsAChangedFileIsInThePreflight(unittest.TestCase):

    def test_a_short_name_and_an_unknown_file_select_nothing(self):
        self.assertEqual(heart2.laws_that_read([]), [])
        self.assertEqual(heart2.laws_that_read(["id", "a.py", "ver"]), [])
        # Built, not written whole: the probe string must not occur in this file, or the
        # selector honestly names this law and the assertion argues with itself.
        self.assertEqual(heart2.laws_that_read(["zz-not-a-file" + ".qqqq"]), [])

    def test_a_bible_edit_names_the_law_that_reads_the_bible(self):
        got = heart2.laws_that_read(["bible.html"])
        self.assertIn(SET_TILE, got)
        self.assertIn("test_the_bible_text_agrees_with_its_own_cards", got)
        with open(os.path.join(ROOT, "tv", SET_TILE + ".py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertNotIn("WINDOWS_SHIP.json", src)
        ship = heart2.laws_that_read(["tv/WINDOWS_SHIP.json"])
        self.assertNotIn(SET_TILE, ship)

    def test_a_control_edit_names_the_status_law_and_the_hook_set_stays_the_test_file(self):
        got = heart2.laws_that_read(["tv/control_app.py"])
        self.assertIn(STATUS, got)
        hook = heart2.gates_for_tests(["tv/" + SET_TILE + ".py"])
        self.assertEqual(hook, [SET_TILE])


if __name__ == "__main__":
    unittest.main()


RED_PROOF = [
    {"why": "REG-2148 - a changed file selects no law again, so the scan runs for the first time on CI",
     "file": "heart2.py",
     "find": "    return sorted(set(out))  # REG-2148 readers\n",
     "replace": "    return []  # REG-2148 readers\n",
     "matches": 1},
]
