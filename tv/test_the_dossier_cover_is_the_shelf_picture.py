# -*- coding: utf-8 -*-
"""REG-2163 (#252) - the dossier cover is the picture the shelf already showed.

Session 74's first open painted an empty thumbnail. The picture came seconds
later, and reopen had it at once. The shelf had asked for the frame at one
width. The dossier asked for a second width and marked it lazy, so nothing
was cached. _coverUrl is that one url. _dossierCoverHtml paints it eager.
A missing cover stays the placeholder.

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


def _paint():
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    src = _src()
    js = (
        "%s\n%s\n"
        "var urls = ['', '/hist/reel_s/f_1.jpg', '/hist/reel_s/f_1.jpg?w=440'].map(_coverUrl);\n"
        "var htmls = ['', '/hist/reel_s/f_1.jpg', '/hist/reel_s/f_1.jpg?w=440'].map(_dossierCoverHtml);\n"
        "console.log(JSON.stringify({urls: urls, htmls: htmls}));\n"
    ) % (
        _fn(src, "_coverUrl(src){"),
        _fn(src, "_dossierCoverHtml(src){"),
    )
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("cover helpers did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class TheDossierCoverIsTheShelfPicture(unittest.TestCase):

    def test_one_url_and_an_eager_cover_and_a_missing_cover_stays_a_placeholder(self):
        got = _paint()
        empty, plain, qualified = got["urls"]
        self.assertEqual(empty, "")
        self.assertEqual(plain, "/hist/reel_s/f_1.jpg?w=440")
        self.assertEqual(qualified, "/hist/reel_s/f_1.jpg?w=440")
        self.assertNotIn("?w=440?w=", qualified)
        h_empty, h_plain, h_qual = got["htmls"]
        self.assertIn("dsr-cover-none", h_empty)
        self.assertNotIn("<img", h_empty)
        self.assertIn('src="/hist/reel_s/f_1.jpg?w=440"', h_plain)
        self.assertIn('loading="eager"', h_plain)
        self.assertNotIn('loading="lazy"', h_plain)
        self.assertIn('src="/hist/reel_s/f_1.jpg?w=440"', h_qual)
        self.assertNotIn("?w=440?w=", h_qual)
        self.assertEqual(h_plain, h_qual)

    def test_the_shelf_and_the_dossier_ask_the_one_url(self):
        s = _src()
        self.assertEqual(s.count("function _coverUrl(src){"), 1)
        self.assertEqual(s.count("function _dossierCoverHtml(src){"), 1)
        self.assertEqual(s.count("_coverUrl("), 3,
                         "the shelf hero and the dossier cover must both ask _coverUrl")
        self.assertEqual(s.count("_dossierCoverHtml("), 2,
                         "the dossier must ask _dossierCoverHtml, and nobody else copies it")
        self.assertIn("var cover = _dossierCoverHtml(_dcov);", s)
        self.assertIn("_coverUrl(_coverArt)", s)
        self.assertNotIn("_coverArt + '?w=440'", s)
        self.assertNotIn("?w=420", s)


RED_PROOF = [
    {
        "why": "REG-2163 - the dossier asks for a second width and the first open is empty again",
        "file": "tv/control_ui.html",
        "find": "    return u + '?w=440';\n",
        "replace": "    return u + '?w=420';\n",
        "matches": 1,
    },
    {
        "why": "REG-2163 - the dossier cover is lazy again, so the first open waits",
        "file": "tv/control_ui.html",
        "find": "    return '<img class=\"dsr-cover\" src=\"' + u + '\" alt=\"\" loading=\"eager\" onerror=\"this.src=\\'/art/hd_zod_rune.png\\';this.classList.add(\\'dsr-cover-fb\\')\">';\n",
        "replace": "    return '<img class=\"dsr-cover\" src=\"' + u + '\" alt=\"\" loading=\"lazy\" onerror=\"this.src=\\'/art/hd_zod_rune.png\\';this.classList.add(\\'dsr-cover-fb\\')\">';\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
