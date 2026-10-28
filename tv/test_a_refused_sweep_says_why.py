# -*- coding: utf-8 -*-
"""#97 (reviewers) - A REFUSED SWEEP SAYS WHY, WITH ITS AGE, AND A STARTED ONE CLEARS IT.

The chronicle sweep's run thread wrote _CHRON_JOB.lastRefusal (GROK ONLY is the reader, or since REG-2713 the switch could not
be read) and nothing read it: "run it again" pressed into the same wall in silence. The refusal now carries its own time, a
sweep that starts clears it (it is the LAST run's word, never older), and the console's sweep panel says it on the button's
hover and in its note - including the note a shown result rewrites.

Driven on the real _chron_sweep_run (its reader door refusing) and the shipped _chronRefusalSay in node. RED_PROOF below.
"""
import json
import os
import subprocess
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
os.environ["TVD_NO_BEACON"] = "1"
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import control_app as CA  # noqa: E402
from cb_node_harness import NODE  # noqa: E402

UI = os.path.join(HERE, "control_ui.html")


class ARefusedSweepSaysWhy(unittest.TestCase):

    def setUp(self):
        keep = dict(CA._CHRON_JOB)
        self.addCleanup(lambda: (CA._CHRON_JOB.clear(), CA._CHRON_JOB.update(keep)))

    def test_the_refusal_carries_its_time_and_a_start_clears_it(self):
        refusal = {"ok": False, "grokOnly": True, "why": "GROK ONLY is the reader on this PC"}
        with mock.patch.object(CA, "_sweep_skipped_because_reader_is_grok", lambda: dict(refusal)):
            CA._chron_sweep_run(None, 1)
        lr = CA._CHRON_JOB.get("lastRefusal") or {}
        self.assertEqual(lr.get("why"), refusal["why"])
        self.assertIsInstance(lr.get("at"), int, "the refusal has no time, so it reads as current forever: %r" % lr)
        src = open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        self.assertEqual(src.count('                           "lastRefusal": None,\n'), 1,
                         "a sweep that starts no longer clears the last run's refusal")

    @unittest.skipUnless(NODE, "node is absent - UNMEASURED here, never a pass")
    def test_the_panel_says_it_with_its_age(self):
        ui = open(UI, encoding="utf-8").read()
        start = "  function _chronRefusalSay(st, now){\n"
        self.assertEqual(ui.count(start), 1)
        i = ui.index(start)
        fn = ui[i:ui.index("\n  }\n", i) + 4]
        js = fn + r"""
var now = 1800000000000;
console.log(JSON.stringify({
  said: _chronRefusalSay({ lastRefusal: { why: 'GROK ONLY is the reader', at: now - 5 * 60000 } }, now),
  none: _chronRefusalSay({}, now), undated: _chronRefusalSay({ lastRefusal: { why: 'x' } }, now) }));
"""
        r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr[-600:])
        o = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual(o["said"], "the last sweep did not start (5 min ago): GROK ONLY is the reader")
        self.assertEqual(o["none"], "")
        self.assertEqual(o["undated"], "the last sweep did not start: x")
        self.assertEqual(ui.count("    var _lrSay = _chronRefusalSay(st, Date.now());"), 1, "the sweep panel never asks")
        self.assertEqual(ui.count("' + (_lrSay ? ' · ⚠ ' + _lrSay : '');"), 2,
                         "a shown result's note still rewrites the refusal away")


RED_PROOF = [
    {"why": "#97 - the refusal is written with no time again",
     "file": "tv/control_app.py",
     "find": "                _CHRON_JOB[\"lastRefusal\"] = dict(_skip, at=int(time.time() * 1000))   # #97 - its own time\n",
     "replace": "                _CHRON_JOB[\"lastRefusal\"] = _skip\n",
     "matches": 2},
    {"why": "#97 - the sweep panel stops saying why the last sweep did not start",
     "file": "tv/control_ui.html",
     "find": "    if (!lr || !lr.why) return '';\n",
     "replace": "    return '';\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
