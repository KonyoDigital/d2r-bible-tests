# -*- coding: utf-8 -*-
"""REG-1912 - A TIP NEVER QUOTES A RETIRED TOTAL.

GrokBot, tick 371 (#230): the Vault tip for Storm Scarab said "Outside the 312 grail" while every fleet tip counts
UNIQUES out of 403. 312 was the curated grail at v304; `_extraTipHtml` had carried the number as a literal ever since.
The law reads the function's CODE (comments stripped, so the explanation of the fix cannot satisfy or trip it) and
requires the grail line to say what is true of every EXTRA_ITEMS row with no number in it.
"""
import io
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(os.path.dirname(HERE), "bible.html")


def _body():
    s = io.open(PAGE, encoding="utf-8").read()
    i = s.find("function _extraTipHtml(nm){")
    j = s.find("\n}\n", i)
    assert i >= 0 and j > i, "the tip builder _extraTipHtml is gone - the law has no subject"
    code = s[i:j]
    code = re.sub(r"/\*.{0,4000}?\*/", "", code, flags=re.S)
    return "\n".join(l for l in code.split("\n") if not l.strip().startswith("//"))


class ATipNeverQuotesARetiredTotal(unittest.TestCase):

    def test_the_grail_line_carries_no_number(self):
        b = _body()
        self.assertEqual(b.count("Not a grail item: the chronicle does not count it."), 1,
                         "the grail line moved or went - the case below would be grading nothing")
        self.assertNotIn("312", b, "the tip quotes the v304 grail total again (REG-1912)")


RED_PROOF = [
    {
        "why": "REG-1912 - the tip quotes the retired 312 grail again beside the chronicle's 403",
        "file": "bible.html",
        "find": "Not a grail item: the chronicle does not count it.</div>';",
        "replace": "Not a grail item: the chronicle does not count it. Outside the 312 grail.</div>';",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
