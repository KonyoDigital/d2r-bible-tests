# -*- coding: utf-8 -*-
"""#86 (REG-2757, GrokBot's v3821 pass) - THE LAST SESSION DIGEST SAYS WHEN ITS RUN WAS CAPTURED.

The home page's 📼 LAST SESSION line read "session 74 · 1h 12m · 611 reads" - which run, from when, it did not say, and
the Shelf card beside it carries the date. It now leads with the run's own capture date (_lsWhenSay from t0, the date
REG-2736 gives a session from what it captured). A run with no t0 gets no date: REG-2752 makes such a run UNKNOWN, and
UNKNOWN is never printed as today.

Driven: _lsWhenSay cut out of control_ui.html and run in node with a fixed time zone; the digest's use of it is read from
the one-line site. RED_PROOF below.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

NODE = shutil.which("node")
UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()
START = "  function _lsWhenSay(t0){"


def _fn():
    if UI.count(START) != 1:
        raise AssertionError("_lsWhenSay is gone or defined twice")
    i = UI.find(START)
    return UI[i:UI.find("\n  }\n", i) + 4]


@unittest.skipUnless(NODE, "node is absent - the digest's date is UNMEASURED here, never a pass")
class TheDigestSaysWhen(unittest.TestCase):

    def say(self, values):
        d = tempfile.mkdtemp(prefix="ls_when_")
        try:
            h, c = os.path.join(d, "h.mjs"), os.path.join(d, "cfg.json")
            io.open(h, "w", encoding="utf-8").write(r"""
import { readFileSync } from 'node:fs';
const CFG = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const f = new Function(CFG.fn + '\nreturn _lsWhenSay;')();
process.stdout.write(JSON.stringify(CFG.values.map(v => f(v))));
""")
            io.open(c, "w", encoding="utf-8").write(json.dumps({"fn": _fn(), "values": values}))
            env = dict(os.environ, TZ="UTC", LANG="en_US.UTF-8")
            r = subprocess.run([NODE, h, c], capture_output=True, text=True, encoding="utf-8", errors="replace",
                               timeout=60, env=env)
        finally:
            shutil.rmtree(d, True)
        if r.returncode != 0:
            raise AssertionError("node failed: %s" % r.stderr[-800:])
        return json.loads(r.stdout)

    def test_a_captured_run_is_dated(self):
        got = self.say([1793000060000])[0]          # 2026-10-26 07:34 UTC
        self.assertIn("Oct 26", got, "the digest's run is not dated: %r" % got)
        self.assertRegex(got, r"\d{1,2}:\d{2}", "the digest's date carries no time: %r" % got)

    def test_no_capture_time_is_no_date(self):
        self.assertEqual(self.say([None, 0, -5, "1793000060000", True]), ["", "", "", "", ""],
                         "a run with no capture time was given a date")


class TheDigestUsesIt(unittest.TestCase):

    def test_the_digest_leads_with_it(self):
        self.assertIn("      var _lsWhen = _lsWhenSay(t.t0);   /* REG-2757 */\n      if (_lsWhen) parts.push(_lsWhen);\n"
                      "      parts.push(_runSpanSay(t.t0, t.t1) || 'UNKNOWN');", UI,
                      "the LAST SESSION digest does not lead with when its run was captured")


RED_PROOF = [
    {"why": "REG-2757 - the digest says no date again",
     "file": "control_ui.html",
     "find": "      if (_lsWhen) parts.push(_lsWhen);\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2757 - a run with no capture time is dated (as the epoch or as now)",
     "file": "control_ui.html",
     "find": "    var d = (typeof t0 === 'number' && t0 > 0) ? new Date(t0) : null;\n",
     "replace": "    var d = new Date(+t0 || Date.now());\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
