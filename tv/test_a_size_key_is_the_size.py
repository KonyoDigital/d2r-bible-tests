"""REG-2143 — a size-debt key is the size, not the tile text that follows the quote.

style="font-size:26px" has no semicolon. The capture used to run to the end of the
line, so editing the tile's words read as a new raw font-size. A JS expression that
starts with a quote stays the expression.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import visual_lock_invariant as vli


class ASizeKeyIsTheSize(unittest.TestCase):
    def test_the_quote_does_not_swallow_the_tile_text(self):
        fear = '<span style="font-size:26px">Herald of Fear</span>'
        dread = '<span style="font-size:26px">Herald of Dread and more words</span>'
        got = vli._raw_sizes(fear + "\n" + dread)
        self.assertEqual(got["26px"], 2, "the two tiles did not share one size key: %r" % dict(got))
        self.assertFalse(any("Herald" in k or ">" in k for k in got),
                         "a size key still carries the tile text: %r" % dict(got))
        planted = vli._raw_sizes(fear + '\n<div style="font-size:27px">x</div>')
        self.assertEqual(planted.get("27px"), 1, "a new raw 27px was not seen: %r" % dict(planted))
        self.assertNotIn("26px", [k for k in planted if k != "26px" and k.startswith("26px")])

    def test_a_js_expression_stays_the_expression(self):
        line = "font-size:'+(14+Math.round(Math.random()*22))+'px;color:red"
        got = vli._raw_sizes(line)
        self.assertEqual(list(got), ["'+(14+Math.round(Math.random()*22))+'px"],
                         "the JS size was cut at its first quote: %r" % dict(got))


RED_PROOF = [
    {"why": "REG-2143 - an unquoted font-size runs through the attribute quote into the tile text again",
     "file": "visual_lock_invariant.py",
     "find": "        v = re.split(r\"[\\\"'`]\", v, maxsplit=1)[0]\n",
     "replace": "        v = v\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main()
