# -*- coding: utf-8 -*-
"""2026-09-29 — THE SHELF'S TRIAGE LINE NAMES EVERY REFUSAL, AND NO WRAP LEAVES A MIDDOT ALONE (REG-1441).

Found by the second eye on 60d4e07e (the screens merge in v3522): `_shTriageLine` set a state only for lastKey
playing / surveyed / done (or a lane off / stood down / with no key) and had NO else. A lastKey of raised,
unworkable, cpu-loaded, ... added nothing, and with no lastSkipKey the line then painted "no refusal since this
console started" - over a lane whose last tick WAS a refusal - while the fleet card (`_fleetSysParts`) said "last
refusal: <word>" for the same object. And the refusal bit was "last refusal: <words> · <age>" inside ONE span that
wraps anywhere, which the file's own note says left a middot alone on its line.

DRIVEN: the shipped `_TRIAGE_WORDS` .. `window._shTriageLine` cut from control_ui.html and run in node on the
reviewer's own object and its neighbours. RED_PROOF below.
"""
import io
import json
import os
import shutil
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.join(HERE, "control_ui.html")
NODE = shutil.which("node")
NOW = 1_790_000_000_000


def _line(tri):
    ui = io.open(UI, encoding="utf-8").read()
    i = ui.find("  var _TRIAGE_WORDS = {")
    j = ui.find("  window._shTriageLine = _shTriageLine;", i)
    if i < 0 or j < 0:
        raise AssertionError("_shTriageLine is no longer findable in control_ui.html - this law measures nothing")
    js = ("var window = {};\n"
          "var esc = function(s){ return String(s === undefined ? '' : s).replace(/&/g,'&amp;')"
          ".replace(/</g,'&lt;').replace(/\"/g,'&quot;'); };\n"
          + ui[i:j] + "\nprocess.stdout.write(_shTriageLine(" + json.dumps({"triage": tri}) + ", %d));\n" % NOW)
    r = subprocess.run([NODE, "-e", js], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("the SHIPPED _shTriageLine would not run in node: %s" % (r.stderr or "")[-400:])
    return r.stdout


def _spans(html):
    out, k = [], 0
    while True:
        a = html.find('<span class="shr-tri-b">', k)
        if a < 0:
            return out
        b = html.find('</span>', a)
        # a bit may hold nested spans - take up to the bit's own closing tag
        depth, c = 0, a
        while True:
            o = html.find('<span', c + 1)
            e = html.find('</span>', c + 1)
            if o != -1 and o < e:
                depth, c = depth + 1, o
                continue
            if depth == 0:
                b = e
                break
            depth, c = depth - 1, e
        out.append(html[a:b])
        k = b + 7


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class TheTriageLineNamesEveryRefusal(unittest.TestCase):

    def test_the_reviewers_object_says_raised_not_no_refusal(self):
        got = _line({"ok": True, "on": True, "lastKey": "raised", "ticks": 3, "backlog": 2})
        self.assertIn("last refusal: the tick raised an error", got,
                      "a lane whose last tick RAISED did not say so: %s" % got)
        self.assertNotIn("no refusal since this console started", got,
                         "the line said 'no refusal' over a lane whose last tick was a refusal: %s" % got)

    def test_every_refusal_word_is_named(self):
        for key, word in (("unworkable", "the owed reels cannot be walked yet"), ("cpu-loaded", "the machine is too busy"),
                          ("cpu-shadow", "a shadow reel is rolling and the CPU is busy")):
            got = _line({"ok": True, "on": True, "lastKey": key, "ticks": 5, "backlog": 1})
            self.assertIn("last refusal: " + word, got, "%s was not named: %s" % (key, got))
            self.assertNotIn("no refusal since", got)

    def test_one_refusal_is_said_once(self):
        got = _line({"ok": True, "on": True, "lastKey": "cpu-shadow", "lastSkipKey": "cpu-shadow",
                     "lastSkipTs": NOW - 60000, "ticks": 5, "backlog": 1})
        self.assertEqual(got.count("last refusal:"), 1, "the same refusal was painted twice: %s" % got)

    def test_a_walk_and_a_quiet_lane_still_read_as_before(self):
        got = _line({"ok": True, "on": True, "lastKey": "surveyed", "ticks": 5, "backlog": 0})
        self.assertIn("walking", got)
        self.assertIn("no refusal since this console started", got)
        got = _line({"ok": True, "on": True, "lastKey": "walked-nothing", "ticks": 5, "backlog": 0})
        self.assertIn("walked nothing", got)
        self.assertNotIn("last refusal", got, "a walk that found nothing is not a refusal: %s" % got)

    def test_no_wrap_can_leave_a_middot_alone(self):
        got = _line({"ok": True, "on": True, "lastKey": "surveyed", "lastSkipKey": "cpu-shadow",
                     "lastSkipTs": NOW - 90000, "ticks": 5, "backlog": 1})
        bits = [b for b in _spans(got) if "last refusal" in b]
        self.assertEqual(len(bits), 1, "PREMISE: the older refusal was not painted: %s" % got)
        self.assertNotIn("·", bits[0], "the refusal bit still carries a middot a wrap can strand: %r" % bits[0])
        self.assertRegex(bits[0], r"\(\S+[\s\u00a0]ago\)", "the refusal's age is gone from the bit: %r" % bits[0])


RED_PROOF = [
    {
        "why": "2026-09-29 - a lane whose last tick was a refusal reads 'no refusal since this console started' again",
        "file": "tv/control_ui.html",
        "find": "      lkRefusal = true;\n",
        "replace": "      lkRefusal = false;\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - the refusal bit carries ' · ' again, and a wrap strands the middot on its own line",
        "file": "tv/control_ui.html",
        "find": "              + ' (' + sa + ')</span>');\n",
        "replace": "              + ' · ' + sa + '</span>');\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
