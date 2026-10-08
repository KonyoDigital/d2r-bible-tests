# -*- coding: utf-8 -*-
"""#252 (REG-2049) - TWO COUNTS NEVER SHARE ONE WORD ON A SESSION CARD.

GrokBot tick 415 (v3621), Session 175: "1 READS" beside "0 of 3 item reads". Both true: the first is the AI read CALLS
the session paid for (the theatre says "1 AI reads"), the second the item-text MOMENTS that were read. One word for two
quantities read as a contradiction. The tile now says "AI reads" and the coverage line "item moments read".
Read from the shipped control_ui.html by the full expressions (never a fragment a comment could satisfy).
"""
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


class TwoCountsNeverShareOneWord(unittest.TestCase):

    def test_the_session_card_names_each_count(self):
        with open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as f:
            ui = f.read()
        self.assertEqual(ui.count("var stats = tile('AI reads', (sm.reads != null ? sm.reads : '—'))"), 1,
                         "the paid-read tile is no longer called 'AI reads'")
        self.assertEqual(ui.count("? ' item moments read · full coverage' : ' item moments read';"), 1,
                         "the coverage line no longer says it counts item moments")


RED_PROOF = [
    {"why": "REG-2049 - the session card calls two different counts 'reads' again",
     "file": "control_ui.html",
     "find": "var stats = tile('AI reads', (sm.reads != null ? sm.reads : '—'))",
     "replace": "var stats = tile('reads', (sm.reads != null ? sm.reads : '—'))",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
