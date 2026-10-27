# -*- coding: utf-8 -*-
"""REG-2160 (#252) - the 1.6s mode flash names film and photos.

The footer and the mode pill already ask _filmPhotoSay. The flash by the mode
pill still said "N photos" alone, so film 11 and photos 20 looked like one
number that had slipped. _modeFlashSay is that flash. It asks _filmPhotoSay.
A missing count stays UNKNOWN and does not borrow the other. A measured 0
still prints. plays is the film length already worded, or UNKNOWN.

Drives the shipped functions, cut from control_ui.html and run in node.
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


def _fn(src, name):
    needle = "function %s" % name
    start = src.find(needle)
    if start < 0:
        raise AssertionError("%s is gone" % name)
    if src.find(needle, start + 1) != -1:
        raise AssertionError("%s is declared more than once" % name)
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
    raise AssertionError("%s never closed" % name)


def _say(cases):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    src = _src()
    js = (
        "%s\n%s\nconsole.log(JSON.stringify(%s.map(function(c){"
        " return _modeFlashSay(c[0], c[1], c[2], c[3], c[4]); })));\n"
    ) % (_fn(src, "_filmPhotoSay(film, photos){"), _fn(src, "_modeFlashSay(mode, film, photos, plays, speed){"), json.dumps(cases))
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("_modeFlashSay did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class TheModeToastNamesFilmAndPhotos(unittest.TestCase):

    def test_a_difference_names_both_on_every_mode_and_a_missing_count_does_not_borrow(self):
        real, fast, story, same, zero_film, missing, both_zero, missing_photos = _say([
            ["real", 11, 20, "12m00s"],
            ["full", 11, 20, "3m00s"],
            ["highlight", 11, 20, "1m00s"],
            ["real", 20, 20, "4m00s"],
            ["real", 0, 20, "1m00s"],
            ["real", None, 20, "1m00s"],
            ["real", 0, 0, "0m00s"],
            ["real", 11, None, None],
        ])
        for line in (real, fast, story):
            self.assertIn("film 11 (film-lane stills)", line)
            self.assertIn("photos 20 (every framed beat)", line)
            self.assertNotIn("20 photos", line)
        self.assertIn("REAL 1:1", real)
        self.assertIn("plays 12m00s", real)
        self.assertIn("FAST", fast)
        self.assertIn("STORY", story)
        self.assertIn("the same frames as the photos", same)
        self.assertNotIn("film-lane", same)
        self.assertIn("film 0 (film-lane stills)", zero_film)
        self.assertIn("photos 20 (every framed beat)", zero_film)
        self.assertIn("film UNKNOWN", missing)
        self.assertNotIn("film 20", missing)
        self.assertIn("reads-only", both_zero)
        self.assertNotIn("0 photos", both_zero)
        self.assertIn("photos UNKNOWN", missing_photos)
        self.assertNotIn("photos 11", missing_photos)
        self.assertIn("plays UNKNOWN", missing_photos)

    def test_fast_says_its_speed_when_it_is_known(self):
        """#97(b) - FAST lost its ' @N x' in REG-2160 (a13b91afa)"""
        with_speed, no_speed = _say([["full", 11, 20, "3m00s", 8], ["full", 11, 20, "3m00s", None]])
        self.assertIn("@8\u00d7", with_speed, with_speed)
        self.assertNotIn("@", no_speed, "an unknown speed was printed: %r" % no_speed)

    def test_the_flash_asks_the_one_sentence(self):
        s = _src()
        self.assertEqual(s.count("function _modeFlashSay(mode, film, photos, plays, speed){"), 1)
        self.assertEqual(s.count("_modeFlashSay("), 2,
                         "the mode click must ask _modeFlashSay, and nobody else copies it")
        self.assertIn("var counts = _filmPhotoSay(film, photos);", s)
        self.assertIn("var msg = _modeFlashSay(TH.mode, _cut ? st2.curFoot : st2.allFoot, _cut ? st2.curPhoto : st2.allPhoto, _wallTxt, TH.speed);", s,
                      "the 1.6s flash went back to a bare photo count, or STORY counts the whole session (#97b)")
        self.assertNotIn("⏱ REAL 1:1 · ' + framedCount + ' photos", s,
                         "the flash still prints a bare photo count")


RED_PROOF = [
    {"why": "#97(b) - FAST drops the speed it plays at again",
     "file": "tv/control_ui.html",
     "find": "    if (mode === 'full') return '\u23e9 FAST \u00b7 time-zipped ~' + play + _spd + counts;\n",
     "replace": "    if (mode === 'full') return '\u23e9 FAST \u00b7 time-zipped ~' + play + counts;\n",
     "matches": 1, "needs": "node"},
    {
        "why": "REG-2160 - the flash prints a bare photo count and drops the film count",
        "file": "tv/control_ui.html",
        "find": "    var counts = _filmPhotoSay(film, photos);\n    var play = (plays == null || plays === '') ? 'UNKNOWN' : String(plays);\n",
        "replace": "    var counts = ' · ' + photos + ' photos';\n    var play = (plays == null || plays === '') ? 'UNKNOWN' : String(plays);\n",
        "matches": 1,
    },
    {
        "why": "REG-2160 - the mode click goes back to a bare photo count",
        "file": "tv/control_ui.html",
        "find": "    var msg = _modeFlashSay(TH.mode, _cut ? st2.curFoot : st2.allFoot, _cut ? st2.curPhoto : st2.allPhoto, _wallTxt, TH.speed);\n",
        "replace": "    var msg = '⏱ REAL 1:1 · ' + st2.allPhoto + ' photos · plays ' + _wallTxt;\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
