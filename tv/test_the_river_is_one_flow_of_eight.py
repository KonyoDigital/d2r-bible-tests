# -*- coding: utf-8 -*-
"""v3176 (#97) — THE RIVER IS ONE FLOW, NEWEST FIRST, FIFO — AND THE WINDOW IS THE CONSOLE'S.

HIS ORDER, 2026-09-15, with four screenshots of this very view: *"all these anyways need to end up
unified in one section after being extracted one step behind deleted after flowing from top to
bottom.. its still in sections each reel in a diffrent place"* — and, asked directly whether older
runs stay scrollable below: *"no only the last 8 sessions stay and the one coming in pushes the
last one out of those 8 sections"*.

⚠ THIS SUPERSEDES v2746, WHICH WAS ALSO HIS. That ruling asked for the opposite — sections down
the page, intake to tombstone — and was built faithfully. He watched it run and ruled the other
way. The station is NOT lost: `.shc-river` has stamped it onto each card since v2746. What goes is
the GROUPING, not the information.

★★ 2026-09-29 — THE EIGHT IS HISTORY; THE WINDOW IS SIXTEEN AND IT IS NOT WRITTEN IN THE PAGE.
His ruling (REG-1433): *"8 sessions 8 hours long? if its less than 8 double the amount to 16
reels.. FIFO same style just that instead of 8 last reels it reads 16"*. That moved
reel_retention / frame_authority / journal_retention to 16 — and THE SHELF kept `RIVER_KEEP = 8`,
a fourth copy pinned by four laws written for the old ruling (REG-1444), so his shelf showed eight
over a floor that kept sixteen. REG-1480: /api/river now publishes `riverKeep`
(reel_retention.KEEP_RECENT, the ONE source), the page reads it into SHELF_RIVER_KEEP, and the
block keeps only a FALLBACK for a console that answered WITHOUT a numeric `riverKeep` (one that
predates the field, or `_river_keep()` -> None) — which this law pins to that same constant. ⚠ The
fallback is NOT for the seconds before the river answers: `_shGroups` returns the "reading the
river…" header while SHELF_RIVER is null and the block is never reached; the reader that sets
SHELF_RIVER sets SHELF_RIVER_KEEP in the same call (the second eye on REG-1480 corrected the first
cut's prose here). The file keeps its name: "of eight" is the ruling it was born under, and a
renamed law is a law whose history nobody can grep. [[copy-drift]] [[the-unjoined-end]]

★ WHAT THIS PINS, by DRIVING the shipped block in node against stub cards:
  1. newest first, so top-to-bottom is downstream;
  2. exactly KEEP_RECENT flow — the next and older are marked data-river-out and hidden — where
     KEEP_RECENT is read from reel_retention, never typed here (the fixtures are SIZED from it);
  3. A PIN IS NEVER PUSHED OUT. He pins deliberately; hiding one to honour a count he set for the
     FLOW would be the console overruling him;
  4. ONE header, not one per station;
  5. the TOMBSTONE mouth figure survives the section that used to carry it — a closed-out reel
     leaves the disk and becomes a retention-ledger row, which is why its section could only ever
     read 0 cards. Dropping it would re-tell the lie v2963 fixed: 410 finished journeys reading as
     "nothing ever finished";
  6. the window is the CONSOLE'S when published, his ruling's number when not, and the two ends
     of that join — the route's dict literal and the page's reader — are both present.
  7. REG-1813 — and WHICH runs fill it is the console's too: `riverKept` (reel_retention.recent_shield,
     in recent_order) decides the set and the order, so the shelf's sixteen are the deleter's sixteen.
"""
import ast
import io
import re
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

import reel_retention as _RR   # noqa: E402  — the ONE source of the window; side-effect free at import

#: his number, read from the module that owns it. The fixtures below are sized from THIS, so the
#: day the ruling moves again this law moves with it instead of pinning yesterday's literal.
#: [[regression-guard]] — pin the LAW, not the number.
KEEP = int(_RR.KEEP_RECENT)

UI = os.path.join(HERE, "control_ui.html")
# ⚠ A PREFIX, on purpose: the line's tail is the window expression and the fallback literal, both
# of which the red-proofs below tamper. Anchoring on the whole line would make every such tamper
# fail here as "the river block is gone" — red for the wrong reason. The count is asserted to be 1.
START = "      var RIVER_KEEP = "
# v3185 — the mouth fix wrapped this call across two lines; the anchor follows the code.
END = "             ' sh-rivergroup' + (_mouthHasRows ? ' sh-rivermouth' : ''));"
#: the shipped line, in full — what the block must say to read the console's window and fall back
RIVER_LINE = ("var RIVER_KEEP = (typeof SHELF_RIVER_KEEP === 'number' && SHELF_RIVER_KEEP >= 1) "
              "? SHELF_RIVER_KEEP : %d;")


def _src():
    with io.open(UI, encoding="utf-8") as fh:
        return fh.read()


def _block():
    """Both ends anchored — a fixed-size window past the region reads as ABSENT and would let
    this law pass on a file that no longer contains the river. [[source-reading-guard]]"""
    src = _src()
    assert src.count(START) == 1, "the river block's opening line occurs %d times" % src.count(START)
    i = src.find(START)
    assert i >= 0, "the river block is gone from control_ui.html"
    j = src.find(END, i)
    assert j > i, "the river block no longer ends with its single mkHead"
    return src[i:j + len(END)]


def _fallback_literal():
    """The number after the colon on the RIVER_KEEP line. -> int. Read off the block, never guessed."""
    m = re.search(r"var RIVER_KEEP = \(typeof SHELF_RIVER_KEEP === 'number' && SHELF_RIVER_KEEP >= 1\) "
                  r"\? SHELF_RIVER_KEEP : (\d+);", _block())
    assert m, "the RIVER_KEEP line no longer reads the console's window and falls back to a literal"
    return int(m.group(1))


VIS_START = "    var vis = [].slice.call(grid.querySelectorAll('.sh-card')).filter(function(c){"
VIS_END = "    });"


def _vis_block():
    """The MEMBERSHIP line, anchored at both ends — a different region from the river block, and
    the river law could not see it: the node harness hands `vis` in ready-made."""
    src = _src()
    i = src.find(VIS_START)
    assert i >= 0, "the shelf's visible-card filter is gone from control_ui.html"
    j = src.find(VIS_END, i)
    assert j > i, "the visible-card filter no longer closes as expected"
    return src[i:j + len(VIS_END)]


VIS_HARNESS = """
function Card(o){
  this.a = {'data-sid': o.sid || ''};
  if (o.out) this.a['data-river-out'] = '1';
  this.style = {display: o.hidden ? 'none' : ''};
}
Card.prototype.getAttribute = function(k){ return (k in this.a) ? this.a[k] : null; };
Card.prototype.setAttribute = function(k, v){ this.a[k] = String(v); };
Card.prototype.removeAttribute = function(k){ delete this.a[k]; };

var _all = %(cards)s.map(function(o){ return new Card(o); });
var grid = { querySelectorAll: function(){ return _all; } };

%(block)s

console.log(JSON.stringify({
  members: vis.map(function(c){ return c.getAttribute('data-sid'); }),
  stillMarked: _all.filter(function(c){ return c.getAttribute('data-river-out'); })
                   .map(function(c){ return c.getAttribute('data-sid'); })
}));
"""


HARNESS = """
function Card(o){
  this.a = {'data-t0': String(o.t0), 'data-pin': o.pin ? '1' : '0', 'data-sid': o.sid || ''};
  if (o.t1) this.a['data-t1'] = String(o.t1);
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
/* ⚠⚠ v3359 — SHELF_POP IS A PAGE-LEVEL NAME THE BLOCK ACQUIRED AND THIS HARNESS WAS NEVER TOLD.
   v3279 added `var SHELF_POP = null;` at control_ui.html top level and the river block began
   reading it as `var P = SHELF_POP;`. The block is EXTRACTED and run alone here, so node threw
   `SHELF_POP is not defined` and FOUR cases failed on both venues — about code that is correct on
   the page. Declared at its own shipped initial value, beside SHELF_MOUTH, which is the same
   dependency one version earlier. [[source-reading-guard]] — an extracted region carries its free
   names with it, and a harness that does not declare them measures its own gaps. */
var SHELF_POP = %(pop)s;
/* REG-1480 — the console's window, as /api/river publishes it and the page's reader stores it.
   null = the river has not answered (the block falls back to his ruling); a number = the console's. */
var SHELF_RIVER_KEEP = %(keep)s;
/* REG-1813 — which reels the console keeps, newest first (its `riverKept`); null = it did not say. */
var SHELF_RIVER_KEPT = %(kept)s;

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


def _node(js, prefix):
    fd, p = tempfile.mkstemp(prefix=prefix, suffix=".js", dir=HERE)
    try:
        with io.open(fd, "w", encoding="utf-8") as fh:
            fh.write(js)
        return subprocess.run(["node", p], capture_output=True, text=True, timeout=60,
                              encoding="utf-8", errors="replace")
    finally:
        try:
            os.unlink(p)
        except OSError:
            pass


class TheRiverIsOneFlowOfEight(unittest.TestCase):

    def drive(self, cards, mouth="null", pop="null", keep=None, kept=None):
        """`keep` None = the console's published window (KEEP); "null" = the river has not answered.
        `kept` None = the console named no set (riverKept absent); a list = its riverKept."""
        js = HARNESS % {"cards": json.dumps(cards), "block": _block(), "mouth": mouth,
                        "pop": pop, "keep": (str(KEEP) if keep is None else str(keep)),
                        "kept": ("null" if kept is None else json.dumps(kept))}
        try:
            r = _node(js, ".river_drive_")
        except FileNotFoundError:   # REG-1900 - the ONE skip: no node here. A timeout is the subject's failure
            self.skipTest("node unavailable - a skip is NOT a pass")
        self.assertEqual(r.returncode, 0, "the shipped river block threw:\\n%s" % (r.stderr or "")[-900:])
        return json.loads(r.stdout.strip().splitlines()[-1])

    def _runs(self, n, pin=()):
        # sid 'r01' is the OLDEST; higher number = newer
        return [{"sid": "r%02d" % i, "t0": 1000 + i, "pin": (i in pin)} for i in range(1, n + 1)]

    def drive_vis(self, cards):
        js = VIS_HARNESS % {"cards": json.dumps(cards), "block": _vis_block()}
        try:
            r = _node(js, ".river_vis_")
        except FileNotFoundError:   # REG-1900 - the ONE skip: no node here. A timeout is the subject's failure
            self.skipTest("node unavailable - a skip is NOT a pass")
        self.assertEqual(r.returncode, 0,
                         "the shipped membership filter threw:\\n%s" % (r.stderr or "")[-900:])
        return json.loads(r.stdout.strip().splitlines()[-1])

    def test_a_run_pushed_past_the_window_is_still_a_river_member(self):
        """v3181. The river hides its own overflow with display:none, and the population that
        decides the river was read straight off display — so the moment the grid re-rendered in
        place (he changes the sort dropdown), every evicted run had silently left the river
        ENTIRELY, and switching back to Newest never brought it back until the next poll rebuilt
        the grid from scratch.

        The window is the RIVER's rule, not a filter he applied. A run it pushed past the window
        is still a member of the flow; only a run HE filtered out is not. The marker is therefore
        cleared on every pass and re-decided by the river block below.

        ⚠ The two hidden cards here are hidden for DIFFERENT REASONS and that is the whole test:
        `pushed` carries data-river-out and must come back; `filtered` does not and must stay
        out. A law that only checked the first would pass on a filter that simply returns
        everything. [[sabotage-is-usually-the-wrong-one]]"""
        # ⚠ v3194 — THE FIXTURE FOLLOWS THE MECHANISM. A river-out card is no longer
        # display-hidden (a CSS rule hides it off the attribute), so `pushed` carries the MARK
        # without the display, and `filtered` carries the display without the mark. That is
        # exactly the distinction the two channels now keep apart.
        o = self.drive_vis([
            {"sid": "shown"},
            {"sid": "pushed", "out": True},
            {"sid": "filtered", "hidden": True},
        ])
        self.assertIn("pushed", o["members"],
                      "a run the river pushed past the window was dropped from the river's own "
                      "population — it can never flow back in")
        self.assertIn("shown", o["members"])
        self.assertNotIn("filtered", o["members"],
                         "a card he actually filtered out must stay out")
        # ⚠ v3194 — THE MARK IS NO LONGER CLEARED HERE, AND THAT IS THE FIX. While the river
        # shared `display` with the filter, this pass had to un-hide its overflow to keep it in
        # the population — which also un-hid cards the FILTER had hidden. Now the mark lives on
        # its own attribute, so membership is read off display alone and the river block clears
        # or re-applies the mark itself when it re-decides.
        self.assertIn("pushed", o["stillMarked"],
                      "the vis pass is clearing the river's own mark again, which is how a "
                      "filtered card came back on screen")

    def test_newest_flows_first(self):
        o = self.drive(self._runs(5))
        self.assertEqual(o["order"], ["r05", "r04", "r03", "r02", "r01"],
                         "top-to-bottom must be downstream — newest enters at the top")

    def test_a_fresh_end_flows_ahead_of_a_later_start(self):
        """A run that started earlier and ended later is the fresh one. Start time alone
        put the older activity on top."""
        o = self.drive([
            {"sid": "late-start", "t0": 5000, "t1": 6000},
            {"sid": "fresh-end", "t0": 1000, "t1": 9000},
        ])
        self.assertEqual(o["order"][0], "fresh-end",
                         "the river ordered by start, so a later start with an older end sat on top")
        self.assertEqual(o["order"][1], "late-start")

    def test_exactly_the_window_flows_and_the_next_is_pushed_out(self):
        """Was "exactly eight ... and the ninth" under his 2026-09-15 ruling; the number is now
        reel_retention.KEEP_RECENT (16 on 2026-09-29) and the fixture is KEEP + 4 runs."""
        o = self.drive(self._runs(KEEP + 4))
        self.assertEqual(o["out"], ["r04", "r03", "r02", "r01"],
                         "the %dth and older must leave the river" % (KEEP + 1))
        # ⚠ v3194 — HIDING MOVED OFF `style.display` ON PURPOSE. _shFilter writes display too,
        # so while the river shared that channel its overflow could be un-hidden by the filter
        # pass and vice versa — measured on his shelf as "8 RUNS" in the header with ten cards on
        # screen. The river now marks `data-river-out` and a CSS rule does the hiding, so the two
        # channels cannot be confused. "Stops rendering" is therefore proven by the MARK plus the
        # RULE, and the rule is asserted below so the mark cannot become decorative.
        self.assertEqual(o["hidden"], [],
                         "the river is writing style.display again — that channel belongs to the "
                         "FILTER, and sharing it is what put ten cards under an 8-run header")
        self.assertEqual(len(o["order"]) - len(o["out"]), KEEP, "exactly %d flow" % KEEP)

    def test_the_mark_actually_hides(self):
        """A mark nobody styles is a flag nobody can see. [[plumbing-with-no-tap]]"""
        self.assertIn("[data-river-out] { display: none", _src(),
                      "nothing hides a run the river pushed past the window, so all of them render")

    def test_a_pin_does_not_eat_a_flow_slot(self):
        """He pins a run deliberately. Hiding one to honour a count he set for the FLOW would be
        the console overruling him — and the real effect of the guard is that a pin does not
        CONSUME one of the window's slots, so pinning something never silently shortens the river.

        ⚠ THE FIRST CUT OF THIS LAW WAS GREEN UNDER ITS OWN SABOTAGE. It asserted only that the
        pinned run was not pushed out — which is true either way, because pins sort to the top and
        a single pin is inside the window regardless. A law that holds with the guard deleted
        tests nothing. [[sabotage-is-usually-the-wrong-one]]"""
        o = self.drive(self._runs(KEEP + 4, pin=(1,)))
        self.assertNotIn("r01", o["out"], "a pinned run was pushed out of the river")
        self.assertNotIn("r01", o["hidden"])
        self.assertEqual(o["order"][0], "r01", "pins stay at the top, where their header anchors")
        # KEEP + 4 runs, 1 pinned -> the pin is kept AND KEEP unpinned still flow, so only 3 leave
        self.assertEqual(o["out"], ["r04", "r03", "r02"],
                         "the pin ate one of the %d flow slots, so pinning a run silently "
                         "shortened the river by one" % KEEP)
        self.assertEqual(len(o["order"]) - len(o["out"]), KEEP + 1,
                         "%d flowing plus the pin" % KEEP)

    def test_one_header_not_one_per_station(self):
        o = self.drive(self._runs(KEEP + 4))
        self.assertEqual(len(o["heads"]), 1,
                         "the river is sectioned again — he ruled it must be ONE flow")
        self.assertIn("River", o["heads"][0]["lab"])

    def test_the_header_says_how_many_were_pushed(self):
        o = self.drive(self._runs(KEEP + 4))
        self.assertIn("4 pushed past the %d" % KEEP, o["heads"][0]["lab"],
                      "runs vanished with no denominator — an unexplained disappearance reads "
                      "as data loss")

    def test_the_tombstone_mouth_survives_its_section(self):
        o = self.drive(self._runs(3), mouth='{"ok":true,"n":410,"mb":5768}')
        self.assertIn("410 closed out", o["heads"][0]["lab"],
                      "the retention figure died with the section that carried it — 410 finished "
                      "journeys would read as 'nothing ever finished'")

    def test_an_unread_mouth_says_so_rather_than_zero(self):
        o = self.drive(self._runs(3), mouth="null")
        self.assertIn("not read yet", o["heads"][0]["lab"],
                      "an unread ledger must not render as a confident zero")


class TheWindowIsTheConsoles(unittest.TestCase):
    """★★ REG-1480 — THE SHELF'S WINDOW IS reel_retention.KEEP_RECENT, PUBLISHED, READ, AND FALLEN
    BACK TO — never a fourth copy in the page.

    Three copies of his floor moved 8 -> 16 on 2026-09-29 (REG-1433) and the page's own literal did
    not, because nothing joined it to the source and four laws pinned the stale number. So the join
    is pinned from BOTH ends here — the route's dict literal (AST) and the page's reader (code, not
    prose) — and the block is driven with the window published and unpublished. [[the-unjoined-end]]
    """

    def drive(self, n, keep):
        return TheRiverIsOneFlowOfEight.drive(self, TheRiverIsOneFlowOfEight._runs(self, n), keep=keep)

    def test_published_the_block_honours_the_consoles_window_not_its_own(self):
        """Driven with a window the page does NOT carry, so a block that quietly used its fallback
        (or a literal) cannot pass. [[sabotage-is-usually-the-wrong-one]]"""
        other = KEEP - 3
        self.assertGreaterEqual(other, 1, "KEEP_RECENT is too small for this fixture to discriminate")
        o = self.drive(KEEP + 4, keep=other)
        self.assertEqual(len(o["out"]), 7,
                         "the console published a window of %d and the block kept %d — the page is "
                         "using its own number, which is the fourth copy this law exists to end"
                         % (other, len(o["order"]) - len(o["out"])))
        self.assertEqual(len(o["order"]) - len(o["out"]), other)

    def test_unpublished_the_page_falls_back_to_HIS_number(self):
        """Before /api/river answers, or on a console that predates `riverKeep`, the block falls
        back — and the fallback is his ruling, read off the block and compared with the module."""
        o = self.drive(KEEP + 4, keep="null")
        self.assertEqual(len(o["out"]), 4,
                         "with no published window the block kept %d, not reel_retention's %d — "
                         "the fallback literal has drifted from his ruling"
                         % (len(o["order"]) - len(o["out"]), KEEP))
        self.assertEqual(_fallback_literal(), KEEP,
                         "the page's fallback is %d while reel_retention.KEEP_RECENT is %d: a fifth "
                         "copy of the window, unpinned, is exactly how the fourth went stale"
                         % (_fallback_literal(), KEEP))
        # and a junk publication (0, a string) is not a window — the fallback still holds
        for junk in ("0", "'16'", "-1"):
            o2 = self.drive(KEEP + 4, keep=junk)
            self.assertEqual(len(o2["out"]), 4, "a published %s was honoured as a window" % junk)

    def test_the_console_publishes_the_window_from_the_one_source(self):
        """AST, not grep: the /api/river dict literal that carries `mouth` also carries `riverKeep`,
        its value is a call to `_river_keep`, and that function reads KEEP_RECENT off reel_retention."""
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        carriers = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            keys = [k.value for k in node.keys if isinstance(k, ast.Constant)]
            if "mouth" in keys and "population" in keys:
                carriers.append(node)
        self.assertEqual(len(carriers), 1,
                         "%d dict literal(s) carry both mouth and population — re-anchor this law"
                         % len(carriers))
        d = carriers[0]
        val = None
        for k, v in zip(d.keys, d.values):
            if isinstance(k, ast.Constant) and k.value == "riverKeep":
                val = v
        self.assertIsNotNone(val, "/api/river does not publish `riverKeep` — the page has nothing "
                                  "to read and falls back forever, which is the fourth copy again")
        self.assertTrue(isinstance(val, ast.Call) and isinstance(val.func, ast.Name)
                        and val.func.id == "_river_keep",
                        "riverKeep is not published through _river_keep()")
        fns = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_river_keep"]
        self.assertEqual(len(fns), 1, "_river_keep is defined %d times" % len(fns))
        reads = [n for n in ast.walk(fns[0])
                 if isinstance(n, ast.Attribute) and n.attr == "KEEP_RECENT"]
        self.assertTrue(reads, "_river_keep does not read KEEP_RECENT off reel_retention — it is "
                               "publishing a number from somewhere else")
        print("   /api/river publishes riverKeep = _river_keep() = reel_retention.KEEP_RECENT (%d)" % KEEP)

    def test_the_page_reads_what_the_console_publishes(self):
        """Against CODE, with comments blanked: the declaration comment above the reader says
        exactly what the reader does, and a law that greps prose grades prose. [[source-reading-guard]]"""
        src = _src()
        # ⚠ BLANKED, NEWLINES KEPT — the first cut replaced each comment with same-length spaces and
        # this very assertion caught it (20721 != 29114): a stripper that eats newlines makes every
        # offset downstream wrong. And `^\s*//` spans blank lines, so it is `[ \t]*`. [[source-reading-guard]]
        _keep = lambda m: "".join(c if c == "\n" else " " for c in m.group(0))
        code = re.sub(r"/\*.{0,4000}?\*/", _keep, src, flags=re.S)
        code = re.sub(r"(?m)^[ \t]*//[^\n]*", _keep, code)
        self.assertEqual(code.count("\n"), src.count("\n"), "the comment stripper ate newlines")
        self.assertEqual(code.count("var SHELF_RIVER_KEEP = null;"), 1,
                         "SHELF_RIVER_KEEP is not declared exactly once at its UNKNOWN value")
        self.assertIn("SHELF_RIVER_KEEP = (typeof d.riverKeep === 'number'", code,
                      "the page never reads `riverKeep` off /api/river, so the console's window "
                      "cannot reach the shelf and the block runs on its fallback forever")
        self.assertIn("? Math.floor(d.riverKeep) : null;", code,
                      "a published window that is not a number >= 1 must leave the page on UNKNOWN")


class TheShelfKeepsTheDeletersSixteen(unittest.TestCase):
    """★★ REG-1813 — ONE RULE FOR WHICH SIXTEEN: reel_retention.recent_shield, asked by the console and
    handed to the page as `riverKept`. The page used to sort its cards by a run's END time and keep the
    top sixteen, while the deleter keeps by the epoch in the reel's name. MEASURED on his ALT 2026-10-06:
    13 of 16 in common - 3 runs that started 2026-10-04 and kept writing rows until 10-05 23:00 were on
    screen as kept, and 3 the deleter keeps were hidden as pushed out. Driven end to end: the REAL
    `_river_kept()` over a temp shelf, its list into the SHIPPED block in node. [[the-unjoined-end]]"""

    def _world(self, n_new):
        """KEEP + n_new reels; the n_new OLDEST by name ran long and ended last, and inside the window a
        later start ends EARLIER - so an end-time order differs from the deleter's in the set AND the order."""
        import shutil
        import control_app as ca
        from unittest import mock
        d = tempfile.mkdtemp(prefix="river_kept_")
        self.addCleanup(shutil.rmtree, d, True)
        t = 1791000000000
        cards, names = [], []
        for i in range(KEEP + n_new):
            sid = "s_%d_%d" % (t + i * 3600000, i)
            names.append("reel_" + sid)
            os.makedirs(os.path.join(d, "reel_" + sid))
            t0 = t + i * 3600000 + 5000
            t1 = (t + 900 * 3600000 + i) if i < n_new else (t0 + (KEEP + n_new - i) * 7200000)
            cards.append({"sid": sid, "t0": t0, "t1": t1})
        with mock.patch.object(ca, "HIST_DIR", d):
            kept = ca._river_kept()
        return cards, names, kept

    def test_the_flow_is_the_deleters_sixteen_in_its_order(self):
        cards, names, kept = self._world(3)
        shield = set(r[len("reel_"):] for r in _RR.recent_shield(names, KEEP))
        self.assertEqual(set(kept), shield, "riverKept is not recent_shield's set")
        self.assertEqual(len(kept), KEEP)
        o = self.drive_kept(cards, kept)
        flowing = [x for x in o["order"] if x not in o["out"]]
        self.assertEqual(set(flowing), shield,
                         "the shelf kept a different sixteen than the deleter - the long runs it "
                         "sorted by their end are past the window")
        self.assertEqual(flowing, kept, "the flow is not in the deleter's order, newest first")
        self.assertEqual(sorted(o["out"]), sorted(c["sid"] for c in cards[:3]))

    def test_premise_the_page_order_alone_keeps_the_wrong_runs(self):
        """PREMISE: without the console's list the same cards keep the long runs - the defect this fixes."""
        cards, names, kept = self._world(3)
        o = TheRiverIsOneFlowOfEight.drive(self, cards)
        flowing = set(x for x in o["order"] if x not in o["out"])
        self.assertNotEqual(flowing, set(kept), "the fixture cannot tell the two orders apart")

    def test_a_pin_outside_the_set_is_kept_and_eats_no_slot(self):
        cards, names, kept = self._world(3)
        cards[0]["pin"] = True
        o = self.drive_kept(cards, kept)
        self.assertEqual(o["order"][0], cards[0]["sid"])
        self.assertNotIn(cards[0]["sid"], o["out"])
        self.assertEqual(len([x for x in o["order"] if x not in o["out"]]), KEEP + 1)

    def test_an_unreadable_shelf_names_no_set(self):
        import control_app as ca
        from unittest import mock
        with mock.patch.object(ca, "HIST_DIR", os.path.join(tempfile.gettempdir(), "no_such_shelf_1813")):
            self.assertIsNone(ca._river_kept(), "a shelf that could not be listed named a set")

    def test_the_console_publishes_the_set_from_the_one_order(self):
        """AST: the /api/river literal carries `riverKept` as a call to `_river_kept`, which asks
        reel_retention.recent_order - the order recent_shield is the tail of."""
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        carriers = [n for n in ast.walk(tree) if isinstance(n, ast.Dict)
                    and {"mouth", "population"} <= set(k.value for k in n.keys if isinstance(k, ast.Constant))]
        self.assertEqual(len(carriers), 1)
        val = [v for k, v in zip(carriers[0].keys, carriers[0].values)
               if isinstance(k, ast.Constant) and k.value == "riverKept"]
        self.assertEqual(len(val), 1, "/api/river does not publish riverKept")
        self.assertTrue(isinstance(val[0], ast.Call) and getattr(val[0].func, "id", None) == "_river_kept")
        fn = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_river_kept"]
        self.assertEqual(len(fn), 1)
        asks = [n for n in ast.walk(fn[0]) if isinstance(n, ast.Attribute) and n.attr == "recent_order"]
        self.assertTrue(asks, "_river_kept sorts the shelf itself instead of asking reel_retention")

    def drive_kept(self, cards, kept):
        return TheRiverIsOneFlowOfEight.drive(self, cards, kept=kept)

    def test_the_page_reads_the_set_the_console_publishes(self):
        """Against CODE, comments blanked: the reader that stores riverKeep stores riverKept beside it, and
        only a list is a set - anything else leaves the page on UNKNOWN. [[source-reading-guard]]"""
        src = _src()
        _blank = lambda m: "".join(ch if ch == "\n" else " " for ch in m.group(0))
        code = re.sub(r"/\*.{0,4000}?\*/", _blank, src, flags=re.S)
        code = re.sub(r"(?m)^[ \t]*//[^\n]*", _blank, code)
        self.assertEqual(code.count("var SHELF_RIVER_KEPT = null;"), 1)
        self.assertEqual(code.count(
            "SHELF_RIVER_KEPT = Array.isArray(d.riverKept) ? d.riverKept.map(String) : null;"), 1,
            "the page never stores riverKept, so the block sorts the window itself forever")


class TheHeaderCountsWhatIsONSCREEN(unittest.TestCase):
    """★ HIS HEADER SAID 13 OF 13 OVER EIGHT CARDS.

    Konyo: *"IN TOTAL i want to see only 8 reel session ... thats all 16 in total"*. He was right
    and the CARDS were right — the river cap works, eight were visible. The NUMBER was wrong,
    because TWO mechanisms hide a card and the counter knew only one:

        the FILTER     hides with `c.style.display = 'none'`    -> counted by `shown`
        the RIVER CAP  hides with `data-river-out` + a CSS rule -> invisible to `shown`

    ⚠⚠ AND THE FIX TOOK THREE PLACEMENTS, WHICH IS WHY THIS LAW PINS POSITION AND NOT PRESENCE.
    End of `_shFilter`: dead, the cap had not run yet. End of `_shGroups`: dead, the river branch
    RETURNS before reaching it. Both times the code was present, correct, and never executed —
    the same shape as the two presence-laws this session that went green over dead features.
    It belongs beside the numbers the cap just produced. [[the-unjoined-end]]
    """

    def _river_branch(self):
        """START -> the branch's own `return;`. Both ends anchored, and the END is the RETURN
        rather than the mkHead, because everything after that return is unreachable from here."""
        src = _src()
        i = src.find(START)
        self.assertGreater(i, -1, "the river block is gone from control_ui.html")
        e = src.find(END, i)
        self.assertGreater(e, i, "the river block no longer ends with its single mkHead")
        r = src.find("return;", e)
        self.assertGreater(r, e, "the river branch no longer returns — re-anchor this law")
        # ⚠⚠ THE SLICE IS mkHead -> RETURN, NOT RIVER_KEEP -> RETURN, and that is the whole law.
        # The wider slice made every assertion below satisfiable by an UNRELATED occurrence: three
        # sabotages came back GREEN because `keptN + pinN` also appears in the mkHead call and
        # `pushedN` in the banner text further up. The names were present, the refresh was gutted.
        # FOURTH presence-law-where-a-reachability-law-was-needed in one session.
        # [[source-reading-guard]] [[sabotage-is-usually-the-wrong-one]]
        blk = src[e + len(END):r]
        # ⚠⚠⚠ AND THE COMMENTS COME OUT, BECAUSE MY OWN PROSE WAS SATISFYING THESE ASSERTIONS.
        # Measured: with comments in, THREE sabotages came back green — deleting the refresh
        # outright, re-walking the DOM, and dropping the overflow — because the explanatory block
        # above the code says "`keptN + pinN` is what is on screen; `pushedN` is NAMED rather than
        # silently subtracted". The law was reading its own commentary. That is `source-reading-
        # guard`'s carved scar (grepping prose) landing inside the law I wrote to fix the LAST
        # scar. Strip first, assert second, always. [[source-reading-guard]]
        blk = re.sub(r"/\*.*?\*/", " ", blk, flags=re.S)
        return re.sub(r"(?m)^\s*//.*$", " ", blk)

    def test_the_count_is_REFRESHED_inside_the_river_branch(self):
        blk = self._river_branch()
        self.assertIn("sh-search-count", blk,
                      "nothing refreshes the shelf's count inside the river branch, so the header "
                      "keeps reporting filter-matches while the cap decides what is on screen — "
                      "his 13 of 13 over eight cards")

    def test_it_counts_the_CAPPED_numbers_not_a_re_walk(self):
        """`keptN + pinN` is what the cap just decided is on screen. Re-deriving it from the DOM
        would be a second answer to a question already answered one line up, and the two can
        disagree — which is the whole defect, one level in."""
        blk = self._river_branch()
        self.assertIn("keptN + pinN", blk,
                      "the refreshed count is not built from the numbers the cap produced")
        self.assertIn("pushedN", blk,
                      "the overflow is not NAMED, so the difference between what he can see and "
                      "what is on the shelf is silently subtracted instead of explained")

    def test_the_refresh_is_BEFORE_the_branch_returns(self):
        """★ THE ONE THAT WOULD HAVE CAUGHT TWO OF MY THREE PLACEMENTS. Presence is not reach."""
        blk = self._river_branch()
        self.assertIn("sh-search-count", blk,
                      "the refresh is not inside the river branch at all — if it sits after the "
                      "branch's return it is unreachable, which is exactly where it sat twice")


RED_PROOF = [
    {
        "why": "REG-1813 - the block ignores the console's set and keeps the sixteen its own end-time sort picks",
        "file": "control_ui.html",
        "find": "      if (Array.isArray(SHELF_RIVER_KEPT)) {\n",
        "replace": "      if (false) {\n",
        "matches": 1,
    },
    {
        "why": "REG-1813 - the flow keeps the console's set but not its order, so the bottom card is not the next to go",
        "file": "control_ui.html",
        "find": "          if (ra >= 0) return ra - rb;\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-1813 - the reader drops riverKept, so the console's set never reaches the block",
        "file": "control_ui.html",
        "find": "        SHELF_RIVER_KEPT = Array.isArray(d.riverKept) ? d.riverKept.map(String) : null;\n",
        "replace": "        SHELF_RIVER_KEPT = null;\n",
        "matches": 1,
    },
    {
        "why": "REG-1813 - the console publishes the OLDEST sixteen, a set the deleter does not keep",
        "file": "control_app.py",
        "find": "        order = _rr.recent_order(_shelf_reel_names())\n",
        "replace": "        order = list(reversed(_rr.recent_order(_shelf_reel_names())))\n",
        "matches": 1,
    },
    {
        "why": "REG-1480 — the page's fallback drifts from his ruling (a fifth copy of the window): "
               "with the river unanswered the shelf shows eight over a floor that keeps sixteen",
        "file": "control_ui.html",
        "find": "? SHELF_RIVER_KEEP : 16;",
        "replace": "? SHELF_RIVER_KEEP : 8;",
        "matches": 1,
    },
    {
        "why": "REG-1480 — the block stops reading the console's window and keeps its own literal, "
               "which is the fourth copy that went stale for fourteen days",
        "file": "control_ui.html",
        "find": "var RIVER_KEEP = (typeof SHELF_RIVER_KEEP === 'number' && SHELF_RIVER_KEEP >= 1) "
                "? SHELF_RIVER_KEEP : 16;",
        "replace": "var RIVER_KEEP = 16;",
        "matches": 1,
    },
    {
        "why": "REG-1480 — /api/river stops publishing the window: the page has nothing to read and "
               "falls back forever, and the next move of the ruling never reaches the shelf",
        "file": "control_app.py",
        "find": '                    "riverKeep": _river_keep(),\n',
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-1480 — the page stops reading `riverKeep`: the route publishes into a void and the "
               "join is plumbing with no tap",
        "file": "control_ui.html",
        "find": "        SHELF_RIVER_KEEP = (typeof d.riverKeep === 'number' && isFinite(d.riverKeep) "
                "&& d.riverKeep >= 1) ? Math.floor(d.riverKeep) : null;\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "v3176 — the cap stops capping: every run flows, nothing is pushed, and his shelf grows "
               "without bound",
        "file": "control_ui.html",
        "find": "        if (_keptAt ? _rank(c) >= 0 : keptN < RIVER_KEEP) { c.removeAttribute('data-river-out'); keptN++; return; }\n",
        "replace": "        if (true) { c.removeAttribute('data-river-out'); keptN++; return; }\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
