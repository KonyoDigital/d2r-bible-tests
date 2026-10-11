# -*- coding: utf-8 -*-
"""REG-2158 (#252) - a film count is not a photo count.

film is the film-lane stills. photos is every beat that kept a frame. The theatre
printed one beside the other with no words for which was which (film 11, all 20
photos). A missing count stays UNKNOWN and does not borrow the other. A measured
0 still prints when the other count differs. Both zero stays reads-only.

Drives the shipped _filmPhotoSay, cut from control_ui.html and run in node.
"""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
from cb_node_harness import NODE  # noqa: E402

UI = os.path.join(HERE, "control_ui.html")


def _src():
    with open(UI, encoding="utf-8") as f:
        return f.read()


def _fn(src):
    start = src.find("function _filmPhotoSay(film, photos){")
    if start < 0:
        raise AssertionError("_filmPhotoSay is gone - film and photos have no one home")
    if src.find("function _filmPhotoSay(film, photos){", start + 1) != -1:
        raise AssertionError("_filmPhotoSay is declared more than once")
    i = src.find("{", start)
    depth = 0
    for j in range(i, len(src)):
        ch = src[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return src[start:j + 1]
    raise AssertionError("_filmPhotoSay never closed")


def _say(cases):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    fn = _fn(_src())
    js = (
        "%s\nconsole.log(JSON.stringify(%s.map(function(c){ return _filmPhotoSay(c[0], c[1]); })));\n"
    ) % (fn, json.dumps(cases))
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("_filmPhotoSay did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class AFilmCountIsNotThePhotoCount(unittest.TestCase):

    def test_a_difference_names_both_and_a_missing_count_does_not_borrow(self):
        same, differ, zero_film, missing, both_zero, missing_photos = _say([
            [20, 20],
            [11, 20],
            [0, 20],
            [None, 20],
            [0, 0],
            [11, None],
        ])
        self.assertIn("the same frames as the photos", same)
        self.assertNotIn("film-lane", same)
        self.assertIn("film 11 (film-lane stills)", differ)
        self.assertIn("photos 20 (every framed beat)", differ)
        self.assertNotIn("the same frames", differ)
        self.assertIn("film 0 (film-lane stills)", zero_film)
        self.assertIn("photos 20 (every framed beat)", zero_film)
        self.assertNotIn("reads-only", zero_film)
        self.assertIn("film UNKNOWN", missing)
        self.assertNotIn("film 20", missing)
        self.assertNotIn("film None", missing)
        self.assertEqual(both_zero.strip(), "· reads-only")
        self.assertIn("photos UNKNOWN", missing_photos)
        self.assertNotIn("photos 11", missing_photos)

    def test_the_footer_and_the_mode_pill_ask_the_one_sentence(self):
        s = _src()
        self.assertEqual(s.count("function _filmPhotoSay(film, photos){"), 1)
        self.assertEqual(s.count("_filmPhotoSay("), 3,
                         "the footer and the mode pill must both ask _filmPhotoSay, and nobody else copies it")
        self.assertIn("+ _filmPhotoSay(_st.allFoot, _st.allPhoto)", s,
                      "the theatre footer prints a bare film count again")
        self.assertIn("_filmPhotoSay(st.allFoot, st.allPhoto)", s,
                      "the mode pill can say all N photos while film is a different number")
        self.assertNotIn("📹 film ' + _st.allFoot", s,
                         "the footer still prints the film number with no photo words")


RED_PROOF = [
    {
        "why": "REG-2158 - a different film count is printed as the photo count",
        "file": "tv/control_ui.html",
        "find": "    return ' · 📹 film ' + film + ' (film-lane stills) · photos ' + photos + ' (every framed beat)';\n",
        "replace": "    return ' · 📹 film ' + photos + ' (film-lane stills) · photos ' + photos + ' (every framed beat)';\n",
        "matches": 1,
    },
    {
        "why": "REG-2158 - a missing film count borrows the photo count",
        "file": "tv/control_ui.html",
        "find": "    if (!filmKnown) return ' · 📹 film UNKNOWN · photos ' + photos + ' (every framed beat)';\n",
        "replace": "    if (!filmKnown) return ' · 📹 film ' + photos + ' (film-lane stills) · photos ' + photos + ' (every framed beat)';\n",
        "matches": 1,
    },
    {
        "why": "REG-2158 - the footer goes back to a bare film count, so a different photo count sits unexplained",
        "file": "tv/control_ui.html",
        "find": "      + _filmPhotoSay(_st.allFoot, _st.allPhoto)\n",
        "replace": "      + (_st.allFoot ? ' · 📹 film ' + _st.allFoot : ' · reads-only')\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
