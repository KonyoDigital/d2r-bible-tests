# -*- coding: utf-8 -*-
"""REG-2155 (#277) - a missing run length is not a dash, and a measured zero still prints.

GrokBot: the dossier said "ran —" beside "sealed in 10m18s" and the theatre said
"plays 0m26s". Those are three clocks. ran is t0 to t1. A missing end was printed
as an em dash, the same mark as a zero-length run. sealed-in and plays stay their
own sentences.

Drives the shipped _runSpanSay, cut from control_ui.html and run in node.
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
    start = src.find("function _runSpanSay(t0, t1){")
    if start < 0:
        raise AssertionError("_runSpanSay is gone - ran has no one home")
    if src.find("function _runSpanSay(t0, t1){", start + 1) != -1:
        raise AssertionError("_runSpanSay is declared more than once")
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
    raise AssertionError("_runSpanSay never closed")


def _say(cases):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    fn = _fn(_src())
    js = (
        "%s\nconsole.log(JSON.stringify(%s.map(function(c){ return _runSpanSay(c[0], c[1]); })));\n"
    ) % (fn, json.dumps(cases))
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("_runSpanSay did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class AMissingRunLengthIsNotADash(unittest.TestCase):

    def test_a_missing_end_is_unknown_and_a_measured_zero_prints(self):
        missing_t0, missing_t1, zero, ten = _say([
            [None, 1700000618000],
            [1700000000000, None],
            [1700000000000, 1700000000000],
            [1700000000000, 1700000618000],
        ])
        self.assertIsNone(missing_t0)
        self.assertIsNone(missing_t1)
        self.assertEqual(zero, "0m00s")
        self.assertEqual(ten, "10m18s")

    def test_the_ran_lines_ask_the_helper_and_name_a_missing_clock(self):
        s = _src()
        self.assertEqual(s.count("function _runSpanSay(t0, t1){"), 1)
        self.assertIn(
            "'  ·  ran ' + esc(dur == null ? 'UNKNOWN' : dur)",
            s,
            "the dossier ran line no longer says UNKNOWN when the clock is missing")
        self.assertIn(
            "'  ·  ran ' + (dur == null ? 'UNKNOWN' : dur)",
            s,
            "the recap ran line no longer says UNKNOWN when the clock is missing")
        self.assertIn(
            "' · ran ' + (spanSay == null ? 'UNKNOWN' : spanSay)",
            s,
            "the theatre ran line no longer says UNKNOWN when the clock is missing")
        self.assertIn(
            "parts.push(_runSpanSay(t.t0, t.t1) || 'UNKNOWN')",
            s,
            "the last-session digest prints a dash for a missing run again")
        self.assertIn("var durTxt = _runSpanSay(sm.t0, sm.t1) || '';", s,
                      "the shelf card formats its own run length again")
        self.assertNotIn("var dur = spanS ?", s, "a ran line still turns a missing span into a dash")

    def test_sealed_in_and_plays_stay_their_own_clocks(self):
        s = _src()
        seal = s.find("function _dossierSealLatency(sm){")
        nxt = s.find("function _dossierRegret(sm){", seal)
        body = s[seal:nxt]
        self.assertNotIn("_runSpanSay", body, "sealed-in was folded into the run length")
        self.assertIn("sealed in ", body)
        self.assertIn(" · plays ", s)
        self.assertNotIn("plays ' + (spanSay", s)


RED_PROOF = [
    {
        "why": "REG-2155 - a missing t0 or t1 prints 0m00s again, so an unknown run looks measured",
        "file": "tv/control_ui.html",
        "find": "    if (!(t0 && t1)) return null;\n",
        "replace": "    if (!(t0 && t1)) return '0m00s';\n",
        "matches": 1,
    },
    {
        "why": "REG-2155 - a measured zero-length run is hidden as if the clock were missing",
        "file": "tv/control_ui.html",
        "find": "    var spanS = Math.max(0, Math.round((+t1 - +t0) / 1000));\n    return Math.floor(spanS / 60) + 'm' + ('0' + (spanS % 60)).slice(-2) + 's';\n",
        "replace": "    var spanS = Math.max(0, Math.round((+t1 - +t0) / 1000));\n    if (!spanS) return null;\n    return Math.floor(spanS / 60) + 'm' + ('0' + (spanS % 60)).slice(-2) + 's';\n",
        "matches": 1,
    },
    {
        "why": "REG-2155 - the dossier ran line uses a dash for a missing clock again",
        "file": "tv/control_ui.html",
        "find": "'  ·  ran ' + esc(dur == null ? 'UNKNOWN' : dur)",
        "replace": "'  ·  ran ' + esc(dur || '—')",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
