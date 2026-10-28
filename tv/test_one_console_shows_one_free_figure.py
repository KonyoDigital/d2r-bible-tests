# -*- coding: utf-8 -*-
"""#151 (REG-2753, GrokBot's v3823 pass) - ONE CONSOLE SHOWS ONE "FREE NOW" FOR ONE DISK.

GrokBot read the Mac's disk sign at 11.9 GB (Finder: 11.91) and a chip on the same console at 12.3 GB. Three readings
reach the page from three moments: the disk sign's (read at the status call itself, through disk_room), the last
retention pass's (up to 15 min old - v2397 measured it saying 4.7 GB while the disk had 8.3) and the agent's health blob
(only while the agent runs). Each surface picked its own. window._diskFreeNow is now the one answer - the sign's figure,
else the retention pass's, else the agent's, else UNKNOWN - and the home chip, the status line's two clauses, the
drawer's free row and the shadow's floor sentence all ask it. The agent's own DISK FULL fault keeps the agent's figure:
it reports what the agent decided on.

Driven: _diskFreeNow cut out of control_ui.html and run in node. The readers are checked by parsing the one-line sites.
RED_PROOF below.
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
START = "  window._diskFreeNow = function(st){"


def _fn():
    i = UI.find(START)
    if i < 0 or UI.count(START) != 1:
        raise AssertionError("_diskFreeNow is gone or defined twice")
    j = UI.find("\n  };\n", i)
    return UI[i:j + 5]


@unittest.skipUnless(NODE, "node is absent - the helper is UNMEASURED here, never a pass")
class TheOneAnswer(unittest.TestCase):

    def ask(self, cases):
        d = tempfile.mkdtemp(prefix="free_now_")
        try:
            h, c = os.path.join(d, "h.mjs"), os.path.join(d, "cfg.json")
            io.open(h, "w", encoding="utf-8").write(r"""
import { readFileSync } from 'node:fs';
const CFG = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const window = {};
new Function('window', CFG.fn)(window);
process.stdout.write(JSON.stringify(CFG.cases.map(st => window._diskFreeNow(st))));
""")
            io.open(c, "w", encoding="utf-8").write(json.dumps({"fn": _fn(), "cases": cases}))
            r = subprocess.run([NODE, h, c], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        finally:
            shutil.rmtree(d, True)
        if r.returncode != 0:
            raise AssertionError("node failed: %s" % r.stderr[-800:])
        return json.loads(r.stdout)

    def test_the_sign_read_now_wins_over_older_readings(self):
        got = self.ask([{"diskSign": {"freeGb": 11.9}, "retention": {"freeGb": 12.3, "checked": 5}, "health": {"freeGB": 12.4}}])
        self.assertEqual((got[0]["gb"], got[0]["src"]), (11.9, "sign"),
                         "the console printed an older reading beside the sign's: %r" % got)

    def test_each_older_reading_only_when_nothing_newer_is_there(self):
        got = self.ask([{"retention": {"freeGb": 12.3, "checked": 5}, "health": {"freeGB": 12.4}},
                        {"diskSign": {"freeGb": None}, "health": {"freeGB": 12.4}},
                        {"diskSign": {"level": "unknown"}, "retention": {}, "health": {}},
                        None])
        self.assertEqual([(g["gb"], g["src"]) for g in got],
                         [(12.3, "retention"), (12.4, "agent"), (None, None), (None, None)])
        self.assertEqual(got[0]["at"], 5, "the retention reading lost its own age")


class EveryReaderAsksIt(unittest.TestCase):

    def test_every_reader_asks_it_and_none_reads_past_it(self):
        """Five surfaces, four calls: the status line's two clauses share one."""
        self.assertEqual(UI.count("window._diskFreeNow(st)") + UI.count("window._diskFreeNow(s2)"), 4,
                         "a surface that says how much is free stopped asking the one answer")
        for stale in ("💾 ' + (H.freeGB != null ? H.freeGB + 'GB free'",
                      "' · \\ud83d\\udcbe ' + (_rt.freeGb != null ? _rt.freeGb + 'GB'",
                      "var free = h.freeGb, floor",
                      "_rt.checked && typeof _rt.freeGb === 'number' && _rt.freeGb < (_rt.floorGb || 8)"):
            self.assertNotIn(stale, UI, "a free figure is read past the one answer again: %r" % stale)
        self.assertIn("if (_fNd.src === 'sign') dRows.push(_vxRow('free', _fNd.gb + 'GB'", UI,
                      "the drawer's free row prints the retention pass's older figure while the sign has one")

    def test_the_drawer_prints_the_agents_figure_when_it_is_the_only_one(self):
        """REG-2776 (the v3826 second eye) - the chip printed the agent's GB while the drawer said 'not reported'."""
        self.assertIn("else if (_fNd.src === 'agent') dRows.push(_vxRow('free', _fNd.gb + 'GB',", UI,
                      "the drawer says 'not reported' while the home chip prints the agent's figure")

    def test_the_agents_own_fault_keeps_the_agents_figure(self):
        self.assertIn("fault = 'DISK FULL — ' + H.freeGB + 'GB free", UI,
                      "PREMISE: the agent's DISK FULL fault moved - it reports what the AGENT decided on")


RED_PROOF = [
    {"why": "REG-2776 - the drawer drops the agent's figure the home chip prints",
     "file": "control_ui.html",
     "find": "    else if (_fNd.src === 'agent') dRows.push(",
     "replace": "    else if (false) dRows.push(",
     "matches": 1},
    {"why": "REG-2753 - the older retention reading wins over the sign read now",
     "file": "control_ui.html",
     "find": "    if (d && typeof d.freeGb === 'number') return { gb: d.freeGb, src: 'sign', at: null };\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2753 - the home chip reads the agent's figure again",
     "file": "control_ui.html",
     "find": "        (function(){ var _f = window._diskFreeNow(st).gb,",
     "replace": "        (function(){ var _f = H.freeGB,",
     "matches": 1},
    {"why": "REG-2753 - the drawer's free row prints the retention pass's figure beside the sign",
     "file": "control_ui.html",
     "find": "    if (_fNd.src === 'sign') dRows.push(_vxRow('free', _fNd.gb + 'GB', 'on the volume holding the reels · read just now'));\n    else if",
     "replace": "    if",
     "matches": 1},
    {"why": "REG-2753 - the status line's trend prints the retention pass's figure",
     "file": "control_ui.html",
     "find": "      _lbl += ' · \\ud83d\\udcbe ' + (_fN.gb != null ? _fN.gb + 'GB' : '?')",
     "replace": "      _lbl += ' · \\ud83d\\udcbe ' + (_rt.freeGb != null ? _rt.freeGb + 'GB' : '?')",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
