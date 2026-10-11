# -*- coding: utf-8 -*-
"""REG-2156 (#277) - a missing film length is not the run, and a measured zero still prints.

plays is the film. ran is t0 to t1. The theatre footer used the run span when the
film clock was missing, and a missing film clock printed 0m00s. sealed-in stays
its own sentence.

Drives the shipped _playSay, cut from control_ui.html and run in node.
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
    start = src.find("function _playSay(ms){")
    if start < 0:
        raise AssertionError("_playSay is gone - plays has no one home")
    if src.find("function _playSay(ms){", start + 1) != -1:
        raise AssertionError("_playSay is declared more than once")
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
    raise AssertionError("_playSay never closed")


def _say(cases):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    fn = _fn(_src())
    js = (
        "%s\nconsole.log(JSON.stringify(%s.map(function(ms){ return _playSay(ms); })));\n"
    ) % (fn, json.dumps(cases))
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("_playSay did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class AMissingPlayLengthIsNotTheRun(unittest.TestCase):

    def test_a_missing_film_is_unknown_and_a_measured_zero_prints(self):
        missing, zero, twenty_six, ten = _say([None, 0, 26000, 618000])
        self.assertIsNone(missing)
        self.assertEqual(zero, "0m00s")
        self.assertEqual(twenty_six, "0m26s")
        self.assertEqual(ten, "10m18s")

    def test_the_play_lines_ask_the_film_clock_and_not_the_run(self):
        s = _src()
        self.assertEqual(s.count("function _playSay(ms){"), 1)
        self.assertEqual(s.count("function _runSpanSay(t0, t1){"), 1)
        self.assertIn(
            "playSeg = ' · plays ' + (_playTxt == null ? 'UNKNOWN' : _playTxt) + ' · wall-clock 1:1';",
            s,
            "the theatre plays line borrows the run or prints a zero for a missing film")
        self.assertIn("var _wallTxt = _playSay(TH.Tplay) || 'UNKNOWN';", s,
                      "the mode line prints 0m00s when the film clock is missing")
        self.assertNotIn("spanS * 1000", s, "plays still borrows the run length")
        self.assertNotIn("plays ' + (spanSay", s, "plays was folded into the run helper")
        seal = s.find("function _dossierSealLatency(sm){")
        nxt = s.find("function _dossierRegret(sm){", seal)
        body = s[seal:nxt]
        self.assertNotIn("_playSay", body, "sealed-in was folded into the film clock")
        self.assertNotIn("_runSpanSay", body, "sealed-in was folded into the run length")
        self.assertIn("sealed in ", body)


RED_PROOF = [
    {
        "why": "REG-2156 - a missing film clock prints 0m00s again, so an unknown film looks measured",
        "file": "tv/control_ui.html",
        "find": "    if (ms == null || !(ms >= 0)) return null;\n",
        "replace": "    if (ms == null || !(ms >= 0)) return '0m00s';\n",
        "matches": 1,
    },
    {
        "why": "REG-2156 - a measured zero-length film is hidden as if the clock were missing",
        "file": "tv/control_ui.html",
        "find": "    var sec = Math.round(+ms / 1000);\n    return Math.floor(sec / 60) + 'm' + ('0' + (sec % 60)).slice(-2) + 's';\n",
        "replace": "    var sec = Math.round(+ms / 1000);\n    if (!sec) return null;\n    return Math.floor(sec / 60) + 'm' + ('0' + (sec % 60)).slice(-2) + 's';\n",
        "matches": 1,
    },
    {
        "why": "REG-2156 - the theatre plays line borrows the run length again",
        "file": "tv/control_ui.html",
        "find": "      var _playTxt = _playSay(TH.Tplay);\n      playSeg = ' · plays ' + (_playTxt == null ? 'UNKNOWN' : _playTxt) + ' · wall-clock 1:1';\n",
        "replace": "      var _realMs = TH.Tplay || spanS * 1000 || 0;\n      var _rSec = Math.max(0, Math.round(_realMs / 1000));\n      var _rTxt = (Math.floor(_rSec / 60) + 'm' + ('0' + (_rSec % 60)).slice(-2) + 's');\n      playSeg = ' · plays ' + _rTxt + ' · wall-clock 1:1';\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
