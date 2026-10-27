# -*- coding: utf-8 -*-
"""GrokBot's 22:07 pass (MED) - LEAVING A SHADOW GOES BACK TO THE TAB IT LIGHTS.

Repro on v3812: own console -> Vault -> Fleet -> see the ALT -> Leave. The header lit VAULT (the tab _shadowRemember
kept) and the board showed CHARACTERS, because the board's leave handler called paint() = switchTab('chars')
unconditionally while _shadowLeave only re-lit the remembered tab.

Two ends, both driven or pinned exactly:
  - the board's backTo(tab), cut from bible.html and run in node: a board tab it has is switched to and answered true;
    a console-native view (tvd, session), no tab, or a tab the board does not have answers false (the old paint stays);
  - the leave handler asks backTo before paint, and _shadowLeave sends the remembered tab with the leave message.
RED_PROOF below.
"""
import io
import json
import os
import shutil
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
NODE = shutil.which("node")


def _read(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


BIBLE = _read(os.path.join(REPO, "bible.html"))
UI = _read(os.path.join(HERE, "control_ui.html"))
START = "  function backTo(tab) {\n"
END = "    return false;\n  }\n"


class LeavingAShadowGoesBackToTheTabItLights(unittest.TestCase):

    def test_the_board_goes_back_to_a_tab_it_has(self):
        if not NODE:
            raise AssertionError("node is absent - this law cannot run here, so it is UNMEASURED")
        self.assertEqual(BIBLE.count(START), 1)
        i = BIBLE.index(START)
        fn = BIBLE[i:BIBLE.index(END, i) + len(END)]
        js = ("var switched = []; var ids = {'tab-vault':1, 'tab-forge':1, 'tab-chars':1, 'tab-session':1};\n"
              "var document = { getElementById: function (id) { return ids[id] ? {} : null; } };\n"
              "function switchTab(t) { switched.push(t); }\n" + fn +
              "\nvar got = ['vault', 'forge', 'tvd', 'session', '', null, 'nosuchtab'].map(backTo);\n"
              "console.log(JSON.stringify({ got: got, switched: switched }));\n")
        r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr[-800:])
        out = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual(out["got"], [True, True, False, False, False, False, False], out)
        self.assertEqual(out["switched"], ["vault", "forge"], "the board did not go back to the lit tab: %r" % out)

    def test_leave_asks_for_the_tab_before_it_paints_and_the_console_sends_it(self):
        self.assertEqual(BIBLE.count("    if (data.leave) { disarm(); if (!backTo(data.tab)) paint(); return; }\n"), 1,
                         "the board's leave paints Characters whatever the console lit")
        self.assertEqual(UI.count("    var _backTab = document.body.getAttribute('data-shadow-tab') || '';"), 1)
        self.assertEqual(UI.count("postMessage({ type: 'tvd-shadow', leave: true, tab: _backTab }, window.location.origin);"),
                         1, "the console's Leave does not send the tab it lights")


RED_PROOF = [
    {"why": "GrokBot 22:07 - the board's leave paints Characters again whatever tab the console lit",
     "file": "bible.html",
     "find": "    if (data.leave) { disarm(); if (!backTo(data.tab)) paint(); return; }\n",
     "replace": "    if (data.leave) { disarm(); paint(); return; }\n", "matches": 1},
    {"why": "GrokBot 22:07 - the back-route answers yes without switching, so the board stays where it was",
     "file": "bible.html",
     "find": "    try { if (typeof switchTab === 'function') { switchTab(t); return true; } } catch (e) {}\n",
     "replace": "    return true;\n", "matches": 1, "needs": "node"},
    {"why": "GrokBot 22:07 - Leave no longer sends the remembered tab",
     "file": "tv/control_ui.html",
     "find": "postMessage({ type: 'tvd-shadow', leave: true, tab: _backTab }, window.location.origin);",
     "replace": "postMessage({ type: 'tvd-shadow', leave: true }, window.location.origin);", "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
