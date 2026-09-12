#!/usr/bin/env python3
"""v2996 (#58/#34) — A DOM CAN BE FULLY BUILT INSIDE A CONTAINER THAT OCCUPIES NO PIXELS.

GROKBOT, 2026-09-12, with `ver` and `liveVer` BOTH v2988: the shelf stage is an EMPTY DARK PANEL —
no cards, no `INTAKE`/`PRINTER`/`CAPTURE`/`ROUTED`/`TOMBSTONE` headings, OCR on the full window and
on a boosted stage crop returned nothing. Two stage crops 5s apart are BYTE-IDENTICAL, so it is not
a slow paint that a screenshot caught early.

At that same moment the console's own beat said `filled=true, cards~535, ink=true`, and my headless
Chrome probe against the same live server built 530 cards / 15 groups with no JS error and
`uiFaults` empty. BOTH READINGS ARE HONEST. The beat published a FILL and never a RECT, so nothing
in it could ever contradict his eyes — the one question never asked was WHERE the container is.

★ THE PAIR IS THE POINT. `cards > 0` together with a state that is not `shown` is a built DOM
nobody can see. Neither half alone says anything: a rect with no fill cannot tell an empty shelf
from a hidden one, and a fill with no rect is exactly the blind spot that let this run for days.
[[the-unjoined-end]]

⚠ THE SHELF IS DELIBERATELY NOT A ROW IN THE `panels` ROSTER. Those four are panels that belong on
their own view, so the `hidden` attribute earns the name DARK — "has rows and is NOT on screen. The
fault, and only this." The shelf is an ON-DEMAND OVERLAY, closed almost all the time. A roster entry
would publish DARK forever, and a signal that is always red is one he stops reading.
[[feedback-threshold-above-the-ceiling]]

⚠ THIS GATE EXECUTES THE SHIPPED BLOCK. Asserting that text is PRESENT is how a law stays green
through its own defeat — measured on this repo four times in one session.
[[source-reading-guard]] [[feedback-blind-fixture-green-gate]]
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
UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()

OPEN_ANCHOR = "(function(){\n                var ov = document.getElementById('th-shelfov');"
CLOSE_ANCHOR = "})();"

HARNESS = r"""
function node(o){
  return {
    hidden: !!o.hidden,
    getBoundingClientRect: function(){ return o.rect || {height:0,width:0,top:0,bottom:0,left:0,right:0}; },
    getClientRects: o.noRects ? undefined : function(){ return new Array(o.boxes === undefined ? 1 : o.boxes); },
    querySelectorAll: function(){ return new Array(o.cards === undefined ? 0 : o.cards); }
  };
}
var CASE = %s;
var ov = CASE.absent ? null : node(CASE);
var document = { getElementById: function(id){ return id === 'th-shelfov' ? ov : null; } };
var window = { innerHeight: CASE.vh === undefined ? 800 : CASE.vh,
               innerWidth:  CASE.vw === undefined ? 1120 : CASE.vw };
var o = CASE.preShelf === undefined ? {} : { shelf: CASE.preShelf };
%s
console.log(JSON.stringify(o));
"""


def _block():
    """-> the shipped shelf-geometry IIFE, or None if it moved.

    ⚠ ANCHORED AT BOTH ENDS. A fixed-size window past the region reads as ABSENT and invents a
    finding; that cost four false reads in one session. [[source-reading-guard]]
    """
    a = UI.find(OPEN_ANCHOR)
    if a < 0:
        return None
    b = UI.find(CLOSE_ANCHOR, a)
    if b < 0:
        return None
    return UI[a:b + len(CLOSE_ANCHOR)]


def sh(o):
    """-> the shelf object as a dict, or an empty one so a missing key fails loudly not weirdly."""
    v = o.get("shelf")
    return v if isinstance(v, dict) else {}


class TheShelfPublishesWhereItIsNotJustThatItIsFull(unittest.TestCase):

    def _run(self, **case):
        blk = _block()
        if blk is None:
            self.skipTest("the shelf geometry block moved — a skip is NOT a pass")
        d = tempfile.mkdtemp(prefix="shelfrect_")
        self.addCleanup(shutil.rmtree, d, True)
        f = os.path.join(d, "t.js")
        io.open(f, "w", encoding="utf-8").write(HARNESS % (json.dumps(case), blk))
        try:
            r = subprocess.run(["node", f], capture_output=True, text=True, timeout=60)
        except Exception:
            self.skipTest("node unavailable — a skip is NOT a pass")
        if r.returncode != 0:
            self.fail("the shipped shelf block would not execute: %s" % (r.stderr or "")[:300])
        return json.loads(r.stdout.strip().splitlines()[-1])

    BIG = {"height": 600, "width": 1000, "top": 10, "bottom": 610, "left": 0, "right": 1000}
    #: what the block ~56 lines above already put on o.shelf. The geometry EXTENDS this.
    PRE = {"open": True, "filled": True, "cards": 535, "why": None}

    # ── the state the blank stage would produce ───────────────────────────────────────────────
    def test_a_built_shelf_with_no_layout_boxes_is_off_view(self):
        """An ancestor with display:none generates NO boxes at all. This is the state that
        explains 535 cards and an empty screen at the same moment."""
        o = self._run(rect=self.BIG, boxes=0, cards=535, preShelf=dict(self.PRE))
        self.assertEqual(sh(o).get("box"), "OFF-VIEW",
                         "an open overlay generating zero layout boxes is OFF-VIEW; got %r"
                         % sh(o).get("box"))
        self.assertEqual(sh(o).get("gridCards"), 535,
                         "and the fill must travel WITH it, or the two halves can never "
                         "contradict each other")

    def test_a_collapsed_shelf_is_zero_height_not_off_view(self):
        """Laid out but collapsed is a DIFFERENT fault from not laid out at all, and they have
        different fixes."""
        o = self._run(rect={"height": 0, "width": 1000, "top": 10, "bottom": 10,
                            "left": 0, "right": 1000}, boxes=1, preShelf=dict(self.PRE))
        self.assertEqual(sh(o).get("box"), "ZERO-HEIGHT")

    def test_a_shelf_below_the_window_is_not_shown(self):
        o = self._run(rect={"height": 600, "width": 1000, "top": 900, "bottom": 1500,
                            "left": 0, "right": 1000}, boxes=1, vh=800, preShelf=dict(self.PRE))
        self.assertEqual(sh(o).get("box"), "BELOW-FOLD")

    def test_a_shelf_off_the_side_is_not_shown(self):
        o = self._run(rect={"height": 600, "width": 100, "top": 10, "bottom": 610,
                            "left": 1200, "right": 1300}, boxes=1, vw=1120, preShelf=dict(self.PRE))
        self.assertEqual(sh(o).get("box"), "OFF-SIDE")

    def test_a_shelf_on_screen_is_shown(self):
        o = self._run(rect=self.BIG, boxes=1, cards=535, preShelf=dict(self.PRE))
        self.assertEqual(sh(o).get("box"), "shown")

    # ── the false red it must never produce ───────────────────────────────────────────────────
    def test_a_closed_shelf_is_not_a_fault(self):
        """⚠ THE TRAP. The `panels` roster calls a hidden panel DARK — "the fault, and only this".
        The shelf is an on-demand overlay and is closed nearly always; borrowing that name would
        publish a fault forever, and a signal that is always red stops being read."""
        o = self._run(hidden=True, rect=self.BIG, cards=535)
        self.assertEqual(sh(o).get("box"), "closed",
                         "a shut overlay is a fact, not a fault; got %r" % sh(o).get("box"))
        self.assertNotIn(sh(o).get("box"), ("DARK", "OFF-VIEW", "ZERO-HEIGHT"),
                         "closed must never borrow a fault name")

    def test_a_missing_overlay_leaves_the_shelf_null(self):
        """o.shelf is ALREADY null when the overlay is not in this build, and null must stay null.
        ⚠ typeof null === 'object', so a careless guard turns that honest UNKNOWN into an empty
        object that reads as a measured answer. [[unknown-stays-unknown]]"""
        o = self._run(absent=True, preShelf=None)
        self.assertIsNone(o.get("shelf"),
                          "an absent overlay must leave shelf null, got %r" % o.get("shelf"))

    def test_the_geometry_extends_the_fill_it_does_not_replace_it(self):
        """⚠ THE BUG THIS CAUGHT, and it was caught only because the LIVE console answered the new
        doctor row with a dict where a state string was expected. The first cut assigned
        `o.shelf = <state string>` straight over the {open, filled, cards, why} object, whose own
        comment calls that shape deliberate — "SAME SHAPE AS THE THEATRE ON PURPOSE ... so a
        supervisor can ask both surfaces one question in one vocabulary". A field that silently
        changes TYPE keeps every existing reader working right up until the page reloads.
        [[copy-drift]] [[label-outlived-referent]]"""
        o = self._run(rect=self.BIG, boxes=0, cards=535, preShelf=dict(self.PRE))
        got = sh(o)
        self.assertEqual(got.get("box"), "OFF-VIEW")
        for k, v in (("open", True), ("filled", True), ("cards", 535)):
            self.assertEqual(got.get(k), v,
                             "the pre-existing %r field was lost when the rect was added — the "
                             "fill and the rect must travel TOGETHER or neither can contradict "
                             "the other" % k)

    # ── not knowing must never resolve to fine ────────────────────────────────────────────────
    def test_an_unanswerable_off_view_question_falls_through(self):
        """getClientRects unavailable must NOT land on the benign answer. boxes===0 is OFF-VIEW,
        which means 'nothing is wrong here' in the roster's vocabulary; a node that cannot answer
        must fall through to the height test instead. [[unknown-stays-unknown]]"""
        o = self._run(rect=self.BIG, noRects=True, cards=3, preShelf=dict(self.PRE))
        self.assertEqual(sh(o).get("box"), "shown",
                         "an unanswerable off-view question must fall through to the height "
                         "test, not resolve to a state that means fine")
        self.assertEqual(sh(o).get("boxes"), -1,
                         "and it must SAY it could not ask, rather than publishing a 0 that "
                         "reads as measured-and-none")

    # ── the reading must carry what makes it checkable ────────────────────────────────────────
    def test_the_viewport_travels_with_the_rect(self):
        """A top of 900 is a defect at 800px tall and fine at 1600. A number whose meaning needs a
        second number nobody published cannot be checked later. [[stale-reading]]"""
        o = self._run(rect=self.BIG, boxes=1, vh=777, preShelf=dict(self.PRE))
        self.assertEqual(sh(o).get("vh"), 777)
        self.assertIn("top", sh(o))
        self.assertIn("h", sh(o))


RED_PROOF = [
    {
        "why": "removing the zero-box test is exactly the blind spot this closes: an overlay whose "
               "ancestor is display:none goes back to reporting itself as on screen",
        "file": "control_ui.html",
        "find": "                  if (boxes === 0)      st = 'OFF-VIEW';",
        "replace": "                  if (false)           st = 'OFF-VIEW';",
        "matches": 1,
    },
    {
        "why": "dropping the card count leaves a rect with no fill beside it, so the two halves "
               "can never contradict one another and the corroborator pair is gone",
        "file": "control_ui.html",
        "find": "                try { o.shelf.gridCards = ov.querySelectorAll('.shc-hero, .shc-sess, .shc-area').length; }",
        "replace": "                try { o.shelf.gridCardsGONE = 0; }",
        "matches": 1,
    },
    {
        "why": "calling a closed overlay DARK reintroduces the permanent false red that would make "
               "him stop believing this signal",
        "file": "control_ui.html",
        "find": "                  st = 'closed';            /* the overlay is shut. A fact, not a fault. */",
        "replace": "                  st = 'DARK';",
        "matches": 1,
    },
]

if __name__ == "__main__":
    # ⚠ HIS CONSOLE IS cp1255 AND CANNOT ENCODE THE ARROWS AND STARS THIS FILE PRINTS. Without
    # this, a CORRECT tree reports FAILURE because the process dies inside its own print — the
    # dangerous direction, because it teaches people to ignore the tool. [[REG-044/054/077]]
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
