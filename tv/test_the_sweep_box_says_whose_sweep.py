# -*- coding: utf-8 -*-
"""REG-1947 - THE RAIL'S SWEEP BOX SAYS WHOSE SWEEP IT IS.

GrokBot (#230 tick 378): "Konyo's STATION tips say 'a sweep is already running' while the rail SWEEP box reads IDLE".
Both were right: the box paints THIS console's chronicle sweep (_swmPaint, fed by this console's own state), and the
tips were Konyo's Mac's. The box sits directly under THE FLEET's list of PCs with a bare "SWEEP" head, so it read as a
fact about the fleet. The law: the head names this PC and its hover says another PC's sweep is told on its own row.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass


class TheSweepBoxSaysWhoseSweep(unittest.TestCase):

    def setUp(self):
        with io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
            self.ui = fh.read()

    def test_the_head_names_this_pc(self):
        m = re.search(r'<div class="fleet-box sweep-box" id="sweep-box" hidden>\s*<div class="fleet-head"([^>]*)>([^<]*)<', self.ui)
        self.assertIsNotNone(m, "the sweep box's head is gone - this law lost its subject")
        self.assertIn("this PC", m.group(2), "the SWEEP box under THE FLEET does not say whose sweep it is (REG-1947)")
        self.assertIn("another PC", m.group(1), "the head's hover does not say where another PC's sweep is told")

    def test_it_still_paints_this_consoles_own_state(self):
        self.assertEqual(self.ui.count("function _swmPaint(st) {"), 1, "the box's painter moved - re-point this law")

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_the_idle_card_names_how_long_and_when(self):
        """REG-1958 - his words: 'it saiys IDLE last read 00:02 ... but then it reads 1 min ago too so its confusing'.
        The big figure is how long the last read TOOK and the small one when it ENDED; each now says which."""
        ui = self.ui
        def cut(start):
            i = ui.find(start)
            self.assertGreaterEqual(i, 0, "%s is gone" % start)
            return ui[i:ui.find("\n  }\n", i) + 4]
        js = ("var NOW = %d; Date.now = function(){ return NOW; };\n" % int(time.time() * 1000)
              + "function escC(s){ return String(s); }\nvar _swmSt = null;\n"
              + "var els = {'sweep-box': {hidden: true}, 'swm-body': {innerHTML: ''}, 'swm-state': {textContent: '', className: ''}};\n"
              + "var document = {getElementById: function(id){ return els[id] || null; }};\n"
              + cut("  function _swmHMS(ms) {") + cut("  function _swmAgo(ms) {") + cut("  function _swmPaint(st) {")
              + "\n_swmPaint({running: false, phase: 'done', lastRunMs: 1732, lastRunEndedTs: NOW - 60000, lastRunReels: 1});\n"
              + "process.stdout.write(JSON.stringify({body: els['swm-body'].innerHTML, state: els['swm-state'].textContent}));")
        p = subprocess.run(["node", "-"], input=js, capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, p.stderr[-600:])
        out = json.loads(p.stdout)
        self.assertEqual(out["state"], "idle")
        self.assertIn("took 0:01", out["body"], "the duration is not named as a duration (REG-1958): %s" % out["body"])
        self.assertIn("ended 1m ago", out["body"], "when the read ended is not named: %s" % out["body"])
        self.assertIn("the last vault read on this PC", out["body"])


RED_PROOF = [
    {
        "why": "REG-1958 - the idle card's big figure is a bare clock again: 0:02 reads as two past midnight",
        "file": "tv/control_ui.html",
        "find": "escC(took ? ('took ' + took) : '\\u2014')",
        "replace": "escC(took || '\\u2014')",
        "matches": 1,
    },
    {
        "why": "REG-1947 - the SWEEP box goes back to a bare head that reads as the whole fleet's sweep",
        "file": "tv/control_ui.html",
        "find": ">🧠 SWEEP · this PC <span",
        "replace": ">🧠 SWEEP <span",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
