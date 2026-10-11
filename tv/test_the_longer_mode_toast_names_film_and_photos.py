# -*- coding: utf-8 -*-
"""REG-2161 (#252) - the longer mode toast names film and photos.

The 1.6s flash already asks _filmPhotoSay. The longer toast on the same click
still said "N photos" or "N film stills" and never named the other count.
_modePageSay is that toast. It asks _filmPhotoSay. A missing count stays
UNKNOWN and does not borrow the other. A measured 0 still prints.

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
        " return _modePageSay(c[0], c[1], c[2]); })));\n"
    ) % (
        _fn(src, "_filmPhotoSay(film, photos){"),
        _fn(src, "_modePageSay(mode, film, photos){"),
        json.dumps(cases),
    )
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("_modePageSay did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class TheLongerModeToastNamesFilmAndPhotos(unittest.TestCase):

    def test_a_difference_names_both_on_every_mode_and_a_missing_count_does_not_borrow(self):
        real, fast, story, same, zero_film, missing, both_zero, missing_photos = _say([
            ["real", 11, 20],
            ["full", 11, 20],
            ["highlight", 11, 20],
            ["real", 20, 20],
            ["real", 0, 20],
            ["real", None, 20],
            ["real", 0, 0],
            ["full", 11, None],
        ])
        for line in (real, fast, story):
            self.assertIn("film 11 (film-lane stills)", line)
            self.assertIn("photos 20 (every framed beat)", line)
            self.assertNotIn("20 photos", line)
            self.assertNotIn("film stills", line)
        self.assertIn("wall-clock 1:1", real)
        self.assertIn("playback time compressed", fast)
        self.assertIn("AI-reader cut", story)
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

    def test_the_longer_toast_asks_the_one_sentence(self):
        s = _src()
        self.assertEqual(s.count("function _modePageSay(mode, film, photos){"), 1)
        self.assertEqual(s.count("_modePageSay("), 2,
                         "the mode click must ask _modePageSay, and nobody else copies it")
        self.assertIn("toast(_modePageSay(TH.mode, st2.allFoot, st2.allPhoto));", s,
                      "the longer toast went back to a bare photo count")
        self.assertNotIn("framedCount + ' photos", s,
                         "the longer toast still prints a bare photo count")
        self.assertNotIn(" + allFoot + ' film stills'", s,
                         "the longer toast still prints a bare film count")


RED_PROOF = [
    {
        "why": "REG-2161 - the longer toast prints a bare photo count and drops the film count",
        "file": "tv/control_ui.html",
        "find": "    var counts = _filmPhotoSay(film, photos);\n    if (mode === 'highlight')\n      return '🎬 STORY — the AI-reader cut: walks read-to-read, each on the frame the AI read.' + counts;\n",
        "replace": "    var counts = ' · ' + photos + ' photos';\n    if (mode === 'highlight')\n      return '🎬 STORY — the AI-reader cut: walks read-to-read, each on the frame the AI read.' + counts;\n",
        "matches": 1,
    },
    {
        "why": "REG-2161 - the mode click goes back to a bare photo count on the longer toast",
        "file": "tv/control_ui.html",
        "find": "    toast(_modePageSay(TH.mode, st2.allFoot, st2.allPhoto));\n",
        "replace": "    toast('⏱ REAL — all ' + st2.allPhoto + ' photos · wall-clock 1:1 to capture');\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
