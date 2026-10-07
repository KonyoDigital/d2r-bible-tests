# -*- coding: utf-8 -*-
"""REG-1934 - A THEATRE FLAGGED OPEN WITH NO STAGE UP IS CLOSED, AND SAYS SO.

GrokBot (#230 tick 375): after closing the Shelf, TV.D's hero kept saying "THEATRE . Theatre open . eyes on a
real session..." with no theatre open, and it survived a reopen + close. Every one of the cockpit's theatre
labels - the THEATRE word, the marquee, the kicker, that caption - reads TH.open. The console's own 3 s
self-heal already knew the inconsistent state ("class set, stage hidden") and dropped only the CSS class,
leaving the flag true, so the labels outlived the stage and the theatre button's first click "closed" a
theatre he could not see.

The law, driven in node on the real callback lifted from control_ui.html: a flag true over a hidden (or
missing) stage calls thClose and posts one ui_fault naming it; a flag true over a visible stage and a flag
false over a hidden stage are left alone.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

MARK = "REG-1934 — A THEATRE FLAGGED OPEN WITH NO STAGE UP"


def _callback():
    with io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
        src = fh.read()
    at = src.find(MARK)
    if at < 0:
        return None
    lo = src.rfind("setInterval(function(){", 0, at)
    hi = src.find("}, 3000);", at)
    if lo < 0 or hi < 0:
        return None
    return src[lo + len("setInterval("):hi + 1]


HARNESS = r"""
var cb = %s;
var out = {closed: 0, faults: []};
var state = %s;
var window = {TH: {open: state.open}, thClose: function(){ out.closed++; window.TH.open = false; }};
var TH = window.TH;
var stage = state.stage === 'missing' ? null : {hidden: state.stage === 'hidden',
  querySelector: function(){ return null; }, getBoundingClientRect: function(){ return {width: 0, height: 0}; }};
var document = {getElementById: function(id){ return id === 'theatre' ? stage : null; },
  body: {classList: {contains: function(){ return false; }, remove: function(){}}},
  querySelectorAll: function(){ return []; }};
function fetch(url, o){ out.faults.push({url: url, body: JSON.parse(o.body)}); return {then: function(){ return this; }, catch: function(){}}; }
cb();
out.openAfter = window.TH.open;
process.stdout.write(JSON.stringify(out));
"""


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class ATheatreFlagNeedsAStage(unittest.TestCase):

    def run_cb(self, open_, stage):
        cb = _callback()
        self.assertIsNotNone(cb, "the self-heal's REG-1934 arm is gone from control_ui.html")
        js = HARNESS % (cb, json.dumps({"open": open_, "stage": stage}))
        p = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, p.stderr[-800:])
        return json.loads(p.stdout)

    def test_a_flag_over_a_hidden_stage_is_closed_and_recorded(self):
        out = self.run_cb(True, "hidden")
        self.assertEqual(out["closed"], 1, "a theatre flagged open over a hidden stage was left open (REG-1934)")
        self.assertFalse(out["openAfter"])
        self.assertEqual([f["body"]["kind"] for f in out["faults"]], ["theatre-flag-without-stage"],
                         "the self-heal closed it without saying so: %s" % out["faults"])
        self.assertEqual(out["faults"][0]["url"], "/api/ui_fault")

    def test_a_missing_stage_is_the_same_case(self):
        out = self.run_cb(True, "missing")
        self.assertEqual(out["closed"], 1)
        self.assertIn("missing", out["faults"][0]["body"]["why"])

    def test_a_visible_theatre_is_left_alone(self):
        out = self.run_cb(True, "visible")
        self.assertEqual((out["closed"], out["faults"]), (0, []), "a theatre he is watching was closed")

    def test_a_closed_flag_over_a_hidden_stage_is_left_alone(self):
        out = self.run_cb(False, "hidden")
        self.assertEqual((out["closed"], out["faults"]), (0, []))


RED_PROOF = [
    {
        "why": "REG-1934 - the self-heal stops checking the flag against the stage: TH.open stays true over a "
               "hidden theatre and the cockpit keeps saying THEATRE",
        "file": "tv/control_ui.html",
        "find": "if (window.TH && window.TH.open && (!_thx || _thx.hidden)) {",
        "replace": "if (false) {",
        "matches": 1,
    },
    {
        "why": "REG-1934 - the self-heal closes the desync silently, so the next one is reported by him again",
        "file": "tv/control_ui.html",
        "find": "              body: JSON.stringify({kind: 'theatre-flag-without-stage',",
        "replace": "              body: JSON.stringify({kind: 'ui',",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
