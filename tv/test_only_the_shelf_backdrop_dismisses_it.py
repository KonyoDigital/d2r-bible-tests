# -*- coding: utf-8 -*-
"""REG-2708 (#86, GrokBot's 02:05 pass on v3816) - ONLY THE SHELF'S BACKDROP DISMISSES IT.

REG-2681 kept the chart, the head and the live strip from closing the Shelf by naming them before the click-outside
dismiss. GrokBot then clicked FILTERS - the filter fold's summary - and the Shelf closed (2/2): every block not on that list
(the fold, a group header, a stat tile) still read as "outside a card". The handler's own comment states the rule: only
the backdrop and the X dismiss. The backdrop is the overlay itself, or the bare gap of the card grid.

Drives the SHIPPED overlay click handler (ov.onclick, cut from control_ui.html) in node over targets that know their
ancestors, and the old one-line rule is a red-proof. RED_PROOF below.
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
START = "    ov.onclick = function(e){\n"
END = "\n    };\n    };   // end _paintShelf"

PROGRAM = r"""
var LOG = [];
var ov = { hidden: false, id: 'th-shelfov', classList: { contains: function(){ return false; } } };
function el(cls, parent){ return { cls: cls, parent: parent || ov, dataset: {},
  classList: { contains: function(c){ return cls.split(' ').indexOf(c) >= 0; } },
  closest: function(sel){ var n = this; while (n && n !== ov) { if (sel.split(',').some(function(s){ s = s.trim();
      return s[0] === '#' ? n.id === s.slice(1) : n.cls && n.cls.split(' ').indexOf(s.slice(1)) >= 0; })) return n; n = n.parent; }
    return null; } }; }
ov.closest = function(){ return null; };
function _shPressWasRepainted(){ return false; }
function _thShelfWasTheDoor(){ return true; }
function thClose(){ LOG.push('close'); }
function _shToggleFilter(f){ LOG.push('filter:' + f); }
function _sesPinToggle(){ LOG.push('pin'); }
function thShelf(){ LOG.push('shelf'); }
function _sessionDossier(n){ LOG.push('dossier:' + n); }
%s
function click(t){ ov.hidden = false; LOG = []; ov.onclick({ target: t }); return { closed: ov.hidden, log: LOG.slice() }; }
var fold = el('sh-filterfold'), sum = el('sh-filtersum', fold), lab = el('sh-fsum-lab', sum);
var grid = el('sh-grid'), card = el('sh-card', grid); card.dataset.n = '7';
var group = el('sh-lanes'), groupHead = el('shr-head', group), tile = el('shs-tile', el('sh-story'));
console.log(JSON.stringify({
  filters: click(lab), foldBody: click(el('sh-fbody', fold)), group: click(groupHead), tile: click(tile),
  card: click(card), gap: click(grid), backdrop: click(ov), x: click(el('x', null)) }));
"""


def _run():
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    with open(UI, encoding="utf-8") as fh:
        s = fh.read()
    if s.count(START) != 1:
        raise AssertionError("PREMISE: the shelf overlay's click handler moved (%d)" % s.count(START))
    i = s.index(START)
    handler = s[i:s.index(END, i) + len("\n    };")]
    r = subprocess.run([NODE, "-"], input=PROGRAM % handler, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut handler did not run in node: %s" % r.stderr[-800:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class OnlyTheShelfBackdropDismissesIt(unittest.TestCase):

    def test_a_click_inside_any_block_keeps_the_shelf(self):
        o = _run()
        for k in ("filters", "foldBody", "group", "tile"):
            self.assertFalse(o[k]["closed"], "a click on %s closed the Shelf (GrokBot 02:05): %r" % (k, o[k]))

    def test_the_backdrop_and_the_grid_gap_still_dismiss_and_a_card_opens(self):
        o = _run()
        self.assertTrue(o["backdrop"]["closed"], "the backdrop no longer dismisses the Shelf: %r" % o["backdrop"])
        self.assertIn("close", o["backdrop"]["log"], "the backdrop did not leave the way he came in (the shelf was the door)")
        self.assertTrue(o["gap"]["closed"], "the bare gap between cards no longer dismisses")
        self.assertEqual(o["card"], {"closed": False, "log": ["dossier:7"]}, o["card"])


RED_PROOF = [
    {"why": "REG-2708 - every block not on the named list dismisses again (FILTERS closes the Shelf)",
     "file": "tv/control_ui.html",
     "find": "      if (!c){ if (e.target === ov || (e.target.classList && e.target.classList.contains('sh-grid'))) _shDismiss(); return; }\n",
     "replace": "      if (!c){ _shDismiss(); return; }\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2708 - the backdrop no longer dismisses at all",
     "file": "tv/control_ui.html",
     "find": "      if (!c){ if (e.target === ov || (e.target.classList && e.target.classList.contains('sh-grid'))) _shDismiss(); return; }\n",
     "replace": "      if (!c){ return; }\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
