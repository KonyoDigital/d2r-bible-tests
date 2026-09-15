# -*- coding: utf-8 -*-
"""v3176 (#97) — THE RIVER IS ONE FLOW OF EIGHT, NEWEST FIRST, FIFO.

HIS ORDER, 2026-09-15, with four screenshots of this very view: *"all these anyways need to end up
unified in one section after being extracted one step behind deleted after flowing from top to
bottom.. its still in sections each reel in a diffrent place"* — and, asked directly whether older
runs stay scrollable below: *"no only the last 8 sessions stay and the one coming in pushes the
last one out of those 8 sections"*.

⚠ THIS SUPERSEDES v2746, WHICH WAS ALSO HIS. That ruling asked for the opposite — sections down
the page, intake to tombstone — and was built faithfully. He watched it run and ruled the other
way. The station is NOT lost: `.shc-river` has stamped it onto each card since v2746. What goes is
the GROUPING, not the information.

★ WHAT THIS PINS, by DRIVING the shipped block in node against stub cards:
  1. newest first, so top-to-bottom is downstream;
  2. exactly 8 flow — the 9th and older are marked data-river-out and hidden;
  3. A PIN IS NEVER PUSHED OUT. He pins deliberately; hiding one to honour a count he set for the
     FLOW would be the console overruling him;
  4. ONE header, not one per station;
  5. the TOMBSTONE mouth figure survives the section that used to carry it — a closed-out reel
     leaves the disk and becomes a retention-ledger row, which is why its section could only ever
     read 0 cards. Dropping it would re-tell the lie v2963 fixed: 410 finished journeys reading as
     "nothing ever finished".
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable
    enable()
except Exception:
    pass

UI = os.path.join(HERE, "control_ui.html")
START = "      var RIVER_KEEP = 8;"
END = "      mkHead(lab, keptN + pinN, flow[0], ' sh-rivergroup');"


def _block():
    """Both ends anchored — a fixed-size window past the region reads as ABSENT and would let
    this law pass on a file that no longer contains the river. [[source-reading-guard]]"""
    with io.open(UI, encoding="utf-8") as fh:
        src = fh.read()
    i = src.find(START)
    assert i >= 0, "the river block is gone from control_ui.html"
    j = src.find(END, i)
    assert j > i, "the river block no longer ends with its single mkHead"
    return src[i:j + len(END)]


HARNESS = """
function Card(o){
  this.a = {'data-t0': String(o.t0), 'data-pin': o.pin ? '1' : '0', 'data-sid': o.sid || ''};
  this.style = {display: ''};
}
Card.prototype.getAttribute = function(k){ return (k in this.a) ? this.a[k] : null; };
Card.prototype.setAttribute = function(k, v){ this.a[k] = String(v); };
Card.prototype.removeAttribute = function(k){ delete this.a[k]; };

var vis = %(cards)s.map(function(o){ return new Card(o); });
var appended = [];
var grid = { appendChild: function(c){ appended.push(c); } };
var heads = [];
function mkHead(lab, n, before, cls){ heads.push({lab: lab, n: n, cls: cls}); }
var SHELF_MOUTH = %(mouth)s;

%(block)s

console.log(JSON.stringify({
  heads: heads,
  order: appended.map(function(c){ return c.getAttribute('data-sid'); }),
  out:   appended.filter(function(c){ return c.getAttribute('data-river-out') === '1'; })
                 .map(function(c){ return c.getAttribute('data-sid'); }),
  hidden: appended.filter(function(c){ return c.style.display === 'none'; })
                  .map(function(c){ return c.getAttribute('data-sid'); })
}));
"""


class TheRiverIsOneFlowOfEight(unittest.TestCase):

    def drive(self, cards, mouth="null"):
        js = HARNESS % {"cards": json.dumps(cards), "block": _block(), "mouth": mouth}
        fd, p = tempfile.mkstemp(prefix=".river_drive_", suffix=".js", dir=HERE)
        try:
            with io.open(fd, "w", encoding="utf-8") as fh:
                fh.write(js)
            r = subprocess.run(["node", p], capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            self.skipTest("node unavailable - a skip is NOT a pass")
        finally:
            try:
                os.unlink(p)
            except OSError:
                pass
        self.assertEqual(r.returncode, 0, "the shipped river block threw:\\n%s" % (r.stderr or "")[-900:])
        return json.loads(r.stdout.strip().splitlines()[-1])

    def _runs(self, n, pin=()):
        # sid 'r01' is the OLDEST; higher number = newer
        return [{"sid": "r%02d" % i, "t0": 1000 + i, "pin": (i in pin)} for i in range(1, n + 1)]

    def test_newest_flows_first(self):
        o = self.drive(self._runs(5))
        self.assertEqual(o["order"], ["r05", "r04", "r03", "r02", "r01"],
                         "top-to-bottom must be downstream — newest enters at the top")

    def test_exactly_eight_flow_and_the_ninth_is_pushed_out(self):
        o = self.drive(self._runs(12))
        self.assertEqual(o["out"], ["r04", "r03", "r02", "r01"],
                         "the 9th and older must leave the river")
        self.assertEqual(o["hidden"], o["out"], "a pushed run must also stop rendering")
        self.assertEqual(len(o["order"]) - len(o["out"]), 8, "exactly 8 flow")

    def test_a_pin_does_not_eat_a_flow_slot(self):
        """He pins a run deliberately. Hiding one to honour a count he set for the FLOW would be
        the console overruling him — and the real effect of the guard is that a pin does not
        CONSUME one of the eight, so pinning something never silently shortens the river.

        ⚠ THE FIRST CUT OF THIS LAW WAS GREEN UNDER ITS OWN SABOTAGE. It asserted only that the
        pinned run was not pushed out — which is true either way, because pins sort to the top and
        a single pin is inside the first eight regardless. A law that holds with the guard deleted
        tests nothing. [[sabotage-is-usually-the-wrong-one]]"""
        o = self.drive(self._runs(12, pin=(1,)))
        self.assertNotIn("r01", o["out"], "a pinned run was pushed out of the river")
        self.assertNotIn("r01", o["hidden"])
        self.assertEqual(o["order"][0], "r01", "pins stay at the top, where their header anchors")
        # 12 runs, 1 pinned -> the pin is kept AND eight unpinned still flow, so only 3 leave
        self.assertEqual(o["out"], ["r04", "r03", "r02"],
                         "the pin ate one of the eight flow slots, so pinning a run silently "
                         "shortened the river by one")
        self.assertEqual(len(o["order"]) - len(o["out"]), 9,
                         "eight flowing plus the pin")

    def test_one_header_not_one_per_station(self):
        o = self.drive(self._runs(12))
        self.assertEqual(len(o["heads"]), 1,
                         "the river is sectioned again — he ruled it must be ONE flow")
        self.assertIn("River", o["heads"][0]["lab"])

    def test_the_header_says_how_many_were_pushed(self):
        o = self.drive(self._runs(12))
        self.assertIn("4 pushed past the 8", o["heads"][0]["lab"],
                      "runs vanished with no denominator — an unexplained disappearance reads "
                      "as data loss")

    def test_the_tombstone_mouth_survives_its_section(self):
        o = self.drive(self._runs(3), mouth='{"ok":true,"n":410,"mb":5768}')
        self.assertIn("410 closed out downstream", o["heads"][0]["lab"],
                      "the retention figure died with the section that carried it — 410 finished "
                      "journeys would read as 'nothing ever finished'")

    def test_an_unread_mouth_says_so_rather_than_zero(self):
        o = self.drive(self._runs(3), mouth="null")
        self.assertIn("not read yet", o["heads"][0]["lab"],
                      "an unread ledger must not render as a confident zero")


if __name__ == "__main__":
    unittest.main(verbosity=2)
