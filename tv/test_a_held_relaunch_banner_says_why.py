# -*- coding: utf-8 -*-
"""REG-2177 (#266) - a held relaunch banner says why it waits.

The drift lane already publishes relaunch.may and relaunch.why on
/api/status. armRelaunch painted only "Relaunch to use it", so a hold
for the window he is using looked like a button with no reason. The
banner now appends that why when may is false. A missing why, a blank
why, and a may that is not false stay the old sentence.

Drives _relaunchBannerSay, cut from control_ui.html and run in node.
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
WHY = ("you are using the window (last touched 5s ago) - an update would wait "
       "until it has been still for 60s")
WIRE = ("            if (dr && dr.drift === true && dr.disk)"
        "{ _armHold = dr.relaunch || null; armRelaunch(dr.disk); return; }\n")


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


class HeldRelaunchBannerSaysWhy(unittest.TestCase):

    def test_the_status_drift_hands_its_hold_to_the_banner(self):
        src = _src()
        self.assertEqual(src.count("function _relaunchBannerSay"), 1)
        self.assertEqual(src.count(WIRE), 1, "the status path no longer hands drift.relaunch to the banner")
        self.assertEqual(src.count("      var hold = _armHold; _armHold = null;\n"), 1,
                         "a hold from one arm would leak into the next")

    @unittest.skipUnless(NODE, "no node on this machine - UNMEASURED here, not passing")
    def test_a_false_may_prints_the_why_and_anything_else_does_not(self):
        fn = _fn(_src(), "_relaunchBannerSay")
        prog = fn + """
          var why = %s;
          function pack(ver, relaunch){ return _relaunchBannerSay(ver, relaunch); }
          process.stdout.write(JSON.stringify({
            held: pack('v3672', {may:false, why:why}),
            clear: pack('v3672', {may:true, why:why}),
            missing: pack('v3672', null),
            blank: pack('v3672', {may:false, why:'   '}),
            unknown: pack('v3672', {why:why}),
            unnamed: pack('', {may:false, why:why})
          }));
        """ % json.dumps(WHY)
        run = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)
        out = json.loads(run.stdout)
        self.assertIn("v3672", out["held"])
        self.assertIn("Relaunch to use it.", out["held"])
        self.assertIn("Held: " + WHY, out["held"])
        self.assertNotIn("Held:", out["clear"])
        self.assertNotIn(WHY, out["clear"])
        self.assertIn("Relaunch to use it.", out["clear"])
        self.assertNotIn("Held:", out["missing"])
        self.assertNotIn("Held:", out["blank"])
        self.assertNotIn("Held:", out["unknown"])
        self.assertNotIn(WHY, out["unknown"])
        self.assertIn("a newer console", out["unnamed"])
        self.assertIn("Held: " + WHY, out["unnamed"])


RED_PROOF = [
    {"why": "REG-2177 - a held relaunch banner drops the reason again",
     "file": "tv/control_ui.html",
     "find": "      if (!why) return head;\n      return head + ' Held: ' + why;\n",
     "replace": "      return head;\n",
     "matches": 1},
    {"why": "REG-2177 - the status path stops handing the hold to the banner",
     "file": "tv/control_ui.html",
     "find": "            if (dr && dr.drift === true && dr.disk){ _armHold = dr.relaunch || null; armRelaunch(dr.disk); return; }\n",
     "replace": "            if (dr && dr.drift === true && dr.disk){ _armHold = null; armRelaunch(dr.disk); return; }\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
