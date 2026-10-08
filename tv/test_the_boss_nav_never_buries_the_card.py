# -*- coding: utf-8 -*-
"""REG-2081 - THE BOSS NAV STICKS ONLY WHILE IT FITS, AND A CARD SCROLLED TO LANDS BELOW WHATEVER IS STUCK.

GrokBot tick 425 on #230 (K09/K10): on Hell Mephisto's boss card, "↓ SCROLL TO FULL FILTERABLE DROP TABLE" left only the
search bar, "PICK A BOSS · CLICK ANY CHIP FOR FULL DETAIL", an empty band and the footer - and "the wheel scrolls
nothing". MEASURED in headless Chrome: the sticky boss nav is 359 px of a 900 px window at 1440, 494 of 660 at his
1120x660, 640 of 900 at 901 and 1420 of 800 at 375 - stuck at top:64px it covered 40-178% of the viewport. The button
opened the card at y=273, UNDER the nav (64..558) and the fixed dock (528..660); a probe 40 px into the card hit a boss
chip at 1440, 1120 and 901. After: the nav scrolls with the page past 35% of the window, the aligner clears a stuck nav
as well as the header, and both scroll-to-table buttons align through it - the same probe hits the card's own name.

Drives the SHIPPED _bossNavFit and __alignCard, cut from bible.html and run in node. A missing node raises.
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

PAGE = os.path.join(os.path.dirname(HERE), "bible.html")
FIT = ("window._bossNavFit = function(){\n", "\n  return tall;\n};\n")
ALIGN = ("window.__alignCard = function(sel){\n", "\n  setTimeout(go, 80); setTimeout(go, 420); setTimeout(go, 900);\n};\n")
BUTTON = "(window.__alignCard?window.__alignCard('#'+el.id):el.scrollIntoView({behavior:'smooth',block:'start'}));"


def _src():
    with open(PAGE, encoding="utf-8") as f:
        return f.read()


def _cut(s, pair):
    start, end = pair
    if s.count(start) != 1:
        raise AssertionError("anchor %r matched %d times - re-point this law" % (start.strip()[:40], s.count(start)))
    i = s.index(start)
    fn = s[i:s.index(end, i) + len(end)]
    if fn.count("{") != fn.count("}"):
        raise AssertionError("the cut %r is not a whole function" % start.strip()[:40])
    return fn


def _node(body):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    s = _src()
    js = """
var window = { innerHeight: 660, scrollY: 1000 }, SCROLLED = [], TIMERS = [];
function setTimeout(f){ TIMERS.push(f); }
window.scrollTo = function(o){ SCROLLED.push(o.top); };
function Nav(h, pos, top){ this.offsetHeight = h; this._pos = pos; this._top = top; var c = {}; this.classList = {
  toggle: function(k, on){ if (on) c[k] = 1; else delete c[k]; }, contains: function(k){ return !!c[k]; } }; }
var NAV = null, HDR = { getBoundingClientRect: function(){ return { height: 245 }; } }, CARD = null;
var document = { querySelector: function(q){ return q === '.boss-nav-sticky' ? NAV : (q === '.header' ? HDR : (q === '#mephisto' ? CARD : null)); },
                 getElementById: function(){ return null; } };
function getComputedStyle(e){ return { position: e._pos, top: e._top }; }
%s
%s
var OUT = {};
%s
console.log(JSON.stringify(OUT));
""" % (_cut(s, FIT), _cut(s, ALIGN), body)
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut functions did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class TheBossNavNeverBuriesTheCard(unittest.TestCase):

    def test_a_nav_too_tall_for_the_window_scrolls_with_the_page(self):
        out = _node("""
          NAV = new Nav(494, 'sticky', '64px'); OUT.his = window._bossNavFit(); OUT.hisCls = NAV.classList.contains('bn-unstick');
          window.innerHeight = 1600; NAV = new Nav(359, 'sticky', '64px'); OUT.tall = window._bossNavFit(); OUT.tallCls = NAV.classList.contains('bn-unstick');
          NAV = new Nav(0, 'sticky', '64px'); OUT.hidden = window._bossNavFit();
        """)
        self.assertEqual((out["his"], out["hisCls"]), (True, True), "a 494 px nav in a 660 px window still sticks")
        self.assertEqual((out["tall"], out["tallCls"]), (False, False), "a nav that fits (22%%) was unstuck: %r" % out)
        self.assertIsNone(out["hidden"], "a hidden tab's nav (no height) was judged")

    def test_a_card_is_aligned_below_a_stuck_nav_not_only_the_header(self):
        out = _node("""
          NAV = new Nav(300, 'sticky', '64px'); CARD = { getBoundingClientRect: function(){ return { top: 800 }; } };
          window.__alignCard('#mephisto'); TIMERS[0](); OUT.stuck = SCROLLED[0];
          NAV = new Nav(300, 'relative', 'auto'); SCROLLED = []; TIMERS = [];
          window.__alignCard('#mephisto'); TIMERS[0](); OUT.flow = SCROLLED[0];
        """)
        self.assertEqual(out["stuck"], 1000 + 800 - (64 + 300 + 14), "a stuck nav was not cleared: %r" % out)
        self.assertEqual(out["flow"], 1000 + 800 - (245 + 14), "a nav in the flow was cleared as if it were stuck: %r" % out)

    def test_both_scroll_to_table_buttons_align_through_it(self):
        self.assertEqual(_src().count(BUTTON), 2, "a scroll-to-table button scrolls bare again (under the sticky stack)")


RED_PROOF = [
    {"why": "REG-2081 - a nav taller than a third of the window sticks again and buries the card",
     "file": "bible.html",
     "find": "  var tall = h > vh * 0.35;\n",
     "replace": "  var tall = false;\n",
     "matches": 1},
    {"why": "REG-2081 - the aligner forgets a stuck nav and lands the card under it",
     "file": "bible.html",
     "find": "        if (_bnB > off) off = _bnB;\n",
     "replace": "",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
