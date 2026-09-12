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
    scrollHeight: o.scrollH === undefined ? 0 : o.scrollH,
    clientHeight: o.clientH === undefined ? 0 : o.clientH,
    scrollTop: o.scrollTop === undefined ? 0 : o.scrollTop,
    getBoundingClientRect: function(){ return o.rect || {height:0,width:0,top:0,bottom:0,left:0,right:0}; },
    getClientRects: o.noRects ? undefined : function(){ return new Array(o.boxes === undefined ? 1 : o.boxes); },
    /* ⚠ CARDS ARE MODELLED WITH A `style.display`, because _shFilter hides filtered-out cards
       that way and the shipped block now filters on it. A stub of bare array slots could not tell
       a hidden card from a shown one, which is exactly the blind spot that let a negative
       firstCardTop ship. `hidden` = how many of the cards are display:none. */
    querySelectorAll: function(sel){
      var n = o.cards === undefined ? 0 : o.cards;
      var hid = o.hiddenCards === undefined ? 0 : o.hiddenCards;
      var base = (o.rect && o.rect.top) || 0;
      var out = [];
      for (var i = 0; i < n; i++){
        out.push({
          style: { display: i < hid ? 'none' : '' },
          getBoundingClientRect: (function(idx){ return function(){
            /* a display:none node reports an all-zero rect in a real browser */
            if (idx < hid) return { top: 0, height: 0, width: 0 };
            var ft = (o.firstCardTop === undefined || o.firstCardTop === null) ? 0 : o.firstCardTop;
            return { top: base + ft };
          }; })(i)
        });
      }
      return out;
    },
    querySelector: function(sel){
      if (String(sel).indexOf('sh-empty-hero') >= 0) return o.emptyHero ? {} : null;
      return null;
    }
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

    def test_a_filtered_card_is_not_counted_as_on_screen(self):
        """⚠⚠ THE DEFECT THIS PINS. `_shFilter` sets `display:none` on filtered-out cards, and a
        hidden node reports an ALL-ZERO rect — so taking the first `.sh-card` blindly produced
        `firstCardTop = 0 - 102 + 0 = -102`, which is less than any clientH, so the
        OPENS-ON-NOTHING check silently could not fire for as long as a filter was on. A shelf
        showing him zero reels read as healthy."""
        o = self._run(rect=self.BIG, boxes=1, cards=535, hiddenCards=535,
                      preShelf=dict(self.PRE), scrollH=21000, clientH=361, scrollTop=0,
                      firstCardTop=957)
        got = sh(o)
        self.assertEqual(got.get("gridCards"), 535, "they are still BUILT")
        self.assertEqual(got.get("visibleCards"), 0, "and none of them is on screen")
        self.assertIsNone(got.get("firstCardTop"),
                          "with no visible card there is no first card top — and it must be null, "
                          "never a negative number that quietly satisfies every threshold")

    def test_the_empty_hero_is_reported_so_no_runs_yet_is_not_a_fault(self):
        """`filled` is always true while open (the overlay ships its own chrome, and _txt > 40),
        so the doctor cannot use it to tell an honestly-empty shelf from a broken one."""
        o = self._run(rect=self.BIG, boxes=1, cards=0, emptyHero=True, preShelf=dict(self.PRE),
                      clientH=361, scrollTop=0)
        self.assertIs(sh(o).get("emptyHero"), True,
                      "a console with no runs yet renders the empty hero, and that is a correct "
                      "state the heart must not call a fault")

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

    def test_the_scroll_geometry_reaches_the_wire(self):
        """⚠ GROKBOT'S SCROLL ATTEMPT MOVED THE PAGE BEHIND, NOT THE OVERLAY, so "are the cards
        merely below the fold" came back UNKNOWN from his eyes. A scroll container knows its own
        content height; this question never needed eyes, and nothing was asking it."""
        o = self._run(rect=self.BIG, boxes=1, cards=535, preShelf=dict(self.PRE),
                      scrollH=21000, clientH=361, scrollTop=0, firstCardTop=957)
        got = sh(o)
        self.assertEqual(got.get("visibleCards"), 535,
                         "with no filter active every built card is visible")
        self.assertEqual(got.get("scrollH"), 21000)
        self.assertEqual(got.get("clientH"), 361)
        self.assertEqual(got.get("firstCardTop"), 957,
                         "the first card's offset INSIDE the scroller is the one number that tells "
                         "a furniture problem from a paint failure")
        self.assertEqual(got.get("belowFoldPx"), 21000 - 361,
                         "and how much content is reachable only by scrolling")

    # ── the reading must carry what makes it checkable ────────────────────────────────────────
    def test_the_viewport_travels_with_the_rect(self):
        """A top of 900 is a defect at 800px tall and fine at 1600. A number whose meaning needs a
        second number nobody published cannot be checked later. [[stale-reading]]"""
        o = self._run(rect=self.BIG, boxes=1, vh=777, preShelf=dict(self.PRE))
        self.assertEqual(sh(o).get("vh"), 777)
        self.assertIn("top", sh(o))
        self.assertIn("h", sh(o))


    def test_the_card_count_counts_CARDS_and_not_card_parts(self):
        """⚠⚠ MEASURED ON HIS LIVE CONSOLE, 2026-09-12. Grok Bot read this beat and published
        `cards:535 · gridCards:1208`. Both numbers were correct; one was answering a different
        question than its name. 1208 = 535 x 2.26, because the first selector asked for
        `.shc-hero, .shc-sess, .shc-area` — 2-3 elements PER CARD (the hero is one per card,
        .shc-sess sits INSIDE the hero, .shc-area is optional).

        It was lifted from render_check's `shelf-cards` target, where it is exactly right because
        those are the elements that can CLIP. It is not a card count anywhere. A number under a
        word naming another quantity is the defect that produced six ships in one console arc.
        [[label-outlived-referent]] [[unknown-stays-unknown]]

        ⚠ PARSED FROM THE SHIPPED LINE, anchored at both ends — not a fixed window, which reads as
        ABSENT past the region and invents a finding. [[source-window-shortcut]]
        """
        blk = _block()
        if blk is None:
            self.skipTest("the shelf geometry block moved — a skip is NOT a pass")
        key = "var _all = [].slice.call(ov.querySelectorAll("
        a = blk.find(key)
        self.assertGreater(a, -1, "the grid card list is no longer built from a querySelectorAll")
        b = blk.find(")", a + len(key))
        self.assertGreater(b, a, "the gridCards selector is unterminated")
        sel = blk[a + len(key):b].strip().strip("'\"")
        self.assertIn(".sh-card", sel,
                      "a count called gridCards must target the CARD WRAPPER (.sh-card); the "
                      "selector is %r" % sel)
        for part in (".shc-hero", ".shc-sess", ".shc-area", ".shc-when", ".shc-foot"):
            self.assertNotIn(part, sel,
                             "%s occurs 1-3 times PER CARD, so counting it inflates a 'cards' "
                             "number by ~2.26x — exactly the 535 vs 1208 his console published. "
                             "Selector is %r" % (part, sel))


class TheDoctorActuallyReadsBothHalves(unittest.TestCase):
    """⚠⚠ v2998 — THE GATE TESTED THE PAGE AND NEVER THE DOCTOR, and the doctor was where the
    corroborator quietly failed to exist. All three original red-proofs targeted control_ui.html
    alone, so removing the CHECKS row left every test green with the rect on the wire and nobody
    reading it. Worse, `box == "shown"` returned OK WHATEVER the fill said — so an overlay that is
    open, on screen and EMPTY (the failure he photographed) read as healthy, while the page had
    already written the verdict into `why` and this file had zero readers of it. A corroborator
    whose second half never reaches the verdict is one half wearing the name of two.
    [[the-unjoined-end]] [[plumbing-with-no-tap]]"""

    ROW = "shelf is where it says"

    def test_the_doctor_carries_a_shelf_row(self):
        import console_doctor as cd
        names = [n for n, _fn in cd.CHECKS]
        self.assertEqual(names.count(self.ROW), 1,
                         "console_doctor.CHECKS must carry exactly one %r row; it carries %d"
                         % (self.ROW, names.count(self.ROW)))

    def _verdict(self, shelf):
        import console_doctor as cd
        real = cd._get
        cd._get = lambda path, *a, **k: (
            {"uiBeat": {"n": 7, "panels": {"shelf": shelf}}} if path == "/api/status" else real(path))
        try:
            return cd._check_the_shelf_is_where_it_says_it_is()
        finally:
            cd._get = real

    def test_an_open_on_screen_shelf_that_carries_nothing_is_not_OK(self):
        """⚠ THE HOLE. A real rect proves the box exists; it cannot prove anything was put in it.
        `#th-shelfov` paints its own near-opaque background, so an empty overlay is a perfectly
        real 811x361 box — exactly the reading his console gave while his eyes saw a dark panel."""
        state, why = self._verdict({"open": True, "filled": False, "cards": 0, "gridCards": 0,
                                    "why": "the shelf overlay is open and carries no cards and no "
                                           "text",
                                    "box": "shown", "boxes": 1, "w": 811, "h": 361, "top": 102,
                                    "vh": 628})
        self.assertEqual(state, "missing",
                         "an open, on-screen, EMPTY shelf must not read as healthy just because "
                         "its rectangle is real; got %s — %s" % (state, why))

    def test_a_shelf_whose_every_card_is_below_its_own_fold_is_not_OK(self):
        """⚠⚠ THE FAULT HE PHOTOGRAPHED, finally named from data. The box is real and the cards
        are built, so both halves of the v2996 pair read healthy — and he opens THE SHELF and sees
        furniture. Measured on his window: first card 957px down a 361px scroller."""
        state, why = self._verdict({"open": True, "filled": True, "cards": 535, "gridCards": 535,
                                    "why": None, "box": "shown", "boxes": 1, "w": 811, "h": 361,
                                    "top": 102, "vh": 628, "scrollH": 21000, "clientH": 361,
                                    "scrollTop": 0, "belowFoldPx": 20639, "firstCardTop": 957})
        self.assertEqual(state, "missing",
                         "every card below the fold at rest is the fault, not a clean bill; "
                         "got %s — %s" % (state, why))
        self.assertIn("LAYOUT fault", why,
                      "and it must say the cards ARE there, so nobody hunts a paint failure")

    def test_a_shelf_scrolled_down_is_not_reported_as_opening_on_nothing(self):
        """The state is about what he sees AT REST. Once scrolled, below-fold content is normal."""
        state, _why = self._verdict({"open": True, "filled": True, "cards": 535, "gridCards": 535,
                                     "why": None, "box": "shown", "boxes": 1, "w": 811, "h": 361,
                                     "top": 102, "vh": 628, "scrollH": 21000, "clientH": 361,
                                     "scrollTop": 1200, "belowFoldPx": 19439, "firstCardTop": 957})
        self.assertEqual(state, "ok")

    def test_a_full_on_screen_shelf_is_OK(self):
        state, _why = self._verdict({"open": True, "filled": True, "cards": 535, "gridCards": 535,
                                     "why": None, "box": "shown", "boxes": 1, "w": 811, "h": 361,
                                     "top": 102, "vh": 628, "clientH": 361, "scrollTop": 0,
                                     "firstCardTop": 12})
        self.assertEqual(state, "ok")

    def test_a_closed_shelf_is_OK(self):
        state, _why = self._verdict({"open": False, "filled": None, "cards": None, "why": None,
                                     "box": "closed", "h": 361})
        self.assertEqual(state, "ok", "a shut overlay is a fact, not a fault")


RED_PROOF = [
    {
        "why": "taking the first card without checking display:none is the defect verbatim: a "
               "filtered-out card reports an all-zero rect, firstCardTop goes NEGATIVE, and the "
               "OPENS-ON-NOTHING check silently cannot fire while any filter is on",
        "file": "control_ui.html",
        "find": "                    if (_cs[_i].style.display !== 'none'){ _fc = _cs[_i]; break; }",
        "replace": "                    if (true){ _fc = _cs[_i]; break; }",
        "matches": 1,
    },
    {
        "why": "removing the CHECKS row puts the rect back on the wire with nobody reading it",
        "file": "console_doctor.py",
        "find": '    ("shelf is where it says", _check_the_shelf_is_where_it_says_it_is),\n',
        "replace": "",
        "matches": 1,
    },
    {
        "why": "dropping the emptiness test restores the hole where an open, on-screen, EMPTY "
               "shelf reads as healthy because its rectangle is real",
        "file": "console_doctor.py",
        "find": "        if _empty:",
        "replace": "        if False:",
        "matches": 1,
    },
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
        "find": "                  var _vis = _all.filter(function(c){ return c.style.display !== 'none'; });",
        "replace": "                  var _vis = _all;",
        "matches": 1,
    },
    {
        "why": "putting the render target's clip-watching selector back makes gridCards count 2-3 "
               "elements per card again — the 535 vs 1208 his console actually published",
        "file": "control_ui.html",
        "find": "                  var _all = [].slice.call(ov.querySelectorAll('.sh-grid .sh-card'));",
        "replace": "                  var _all = [].slice.call(ov.querySelectorAll('.shc-hero, .shc-sess, .shc-area'));",
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
