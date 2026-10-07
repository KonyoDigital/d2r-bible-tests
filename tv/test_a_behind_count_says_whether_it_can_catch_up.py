# -*- coding: utf-8 -*-
"""REG-1952 - EVERY FLEET ROW THAT PRINTS "N BEHIND" SAYS WHETHER THAT PC CAN CATCH UP.

The #231 eye on 475f672e and db25b884: only the row whose beacon was HEARD carried "not pulling" (a refused pull) and
"pull UNKNOWN" (git could not say); the silent arm (online, beacon past the bar), the roster-refused arm and the offline
arm printed the behind count bare - which reads as a machine that will catch up on its own. Dean's row has read
"v3577 · not pulling · 24 behind" while heard; the same report gone quiet lost the "not pulling".

The law paints the SHIPPED rail (_fleetRefresh in node, the fleet laws' own harness) over a roster with a silent row
whose pull is refused and an offline row whose pull git could not answer, and reads what each row says.
"""
import json
import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import test_the_fleet_card_says_how_each_pc_films_and_drains as F  # noqa: E402  (its node harness)

_REFRESH_END = "  /* ⚠⚠ v3086 — NOBODY EVER ASKED."


def _rail(fx):
    prog = (F.HARNESS + F._cut(F.FLEET_START, _REFRESH_END) + "\n"
            + "ELS['fleet-list'] = { innerHTML: '' };\n"
            + "var fetch = function(){ return Promise.resolve({ json: function(){ return Promise.resolve(%s); } }); };\n"
            % json.dumps(fx)
            + "window._fleetRefresh().then(function(){ process.stdout.write(ELS['fleet-list'].innerHTML); },"
            + " function(e){ process.stdout.write('ERR ' + e); });\n")
    r = F.subprocess.run([F.NODE, "-"], input=prog, capture_output=True, text=True, timeout=60)
    if r.returncode != 0 or r.stdout.startswith("ERR"):
        raise AssertionError("the shipped rail would not paint: %s" % (r.stderr or r.stdout)[-1200:])
    rows = {}
    for c in r.stdout.split('<div class="fleet-row')[1:]:
        i = c.find('data-fleet-machine="')
        if i >= 0:
            rows[c[i + 20:c.index('"', i + 20)]] = c
    return rows


def _fixture():
    fx = F._fixture()
    now = int(time.time() * 1000)
    alt = [m for m in fx["online"] if m["machine"] == "box-b"][0]
    alt["t"] = F._iso(now - 3 * 3600 * 1000)                    # online in the roster, beacon long silent
    alt["pull"] = {"can": False, "behind": 5, "why": "a local edit blocks the pull"}
    wife = fx["offline"][0]
    wife["pull"] = {"can": None, "behind": 9, "why": "git could not be asked"}
    wife["lag"] = {"behind": 27, "of": "v3604"}                # #255 - the lag word beside the version
    return fx


@unittest.skipIf(F.NODE is None, "node is not on this machine - this law RUNS the shipped rail")
class ABehindCountSaysWhetherItCanCatchUp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rows = _rail(_fixture())

    def test_the_rail_painted_both_rows(self):
        self.assertIn("box-b", self.rows, "the silent row was not painted - this case would judge nothing")
        self.assertIn("box-c", self.rows, "the offline row was not painted - this case would judge nothing")

    def test_a_silent_row_with_a_refused_pull_still_says_not_pulling(self):
        self.assertIn("presence UNKNOWN", self.rows["box-b"], "baseline: the row is not the silent arm")
        self.assertIn("not pulling", self.rows["box-b"],
                      "a silent row kept its behind count and lost 'not pulling' (REG-1952)")

    def test_an_offline_row_whose_pull_git_could_not_answer_says_pull_unknown(self):
        self.assertIn("offline", self.rows["box-c"], "baseline: the row is not the offline arm")
        self.assertIn("pull UNKNOWN", self.rows["box-c"],
                      "an offline row printed its behind count with no word on whether it can pull (REG-1952)")


    def test_the_lag_word_keeps_its_space_after_the_version(self):
        """#255 - GrokBot ticks 400/401 read Dean's row as 'v3577\u00b7 27 behind': every caller glues the version
        word straight onto the lag span, so the span carries the space."""
        row = self.rows["box-c"]
        i = row.find("\u00b7 27 behind")
        self.assertGreater(i, 0, "premise: the offline row painted no lag word, so this case judges nothing")
        self.assertEqual(row[i - 1], " ", "the lag word glued onto the version: %r (#255)" % row[i - 12:i + 12])


RED_PROOF = [
    {
        "why": "#255 - the lag word loses its leading space and glues onto the version word",
        "file": "tv/control_ui.html",
        "find": "             + ' \\u00b7 ' + lg.behind + ' behind</span>';",
        "replace": "             + '\\u00b7 ' + lg.behind + ' behind</span>';",
        "matches": 1,
    },
    {
        "why": "REG-1952 - the rows that were not heard print their behind count bare again",
        "file": "tv/control_ui.html",
        "find": "        var _pullTail = escC((stuck ? ' \\u00b7 not pulling' : '') + pullSay);\n",
        "replace": "        var _pullTail = '';\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
