#!/usr/bin/env python3
"""v3006 (#77) — THE 15 "WAITING ON YOU" NEVER REACHED HIS INBOX.

The console's watchdog has carried them for months (`/api/status` -> eagle.rows, needsYou = 12
measured live), the console UI shows the chip — and bible.html, where the INBOX lives (242 inbox
refs), had never heard of the field. Two halves each built right, never joined.
[[the-unjoined-end]]

⚠ EVERY LAW EXECUTES THE SHIPPED CODE in node. The painter and the fetch classifier are extracted
from bible.html and driven through their states; text-presence checks are how a law stays green
through its own defeat. ⚠ An unreachable console must read UNKNOWN, never "nothing waiting" —
zero is a measurement and an absence is not. [[unknown-stays-unknown]]
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
REPO = os.path.dirname(HERE)
BIBLE = io.open(os.path.join(REPO, "bible.html"), encoding="utf-8").read()

OPEN_ANCHOR = "  var _eagleNY = { st: 'unknown'"
CLOSE_ANCHOR = "\n  try {\n    _eagleNYPaint();"


def _block():
    a = BIBLE.find(OPEN_ANCHOR)
    if a < 0:
        return None
    b = BIBLE.find(CLOSE_ANCHOR, a)
    if b < a:
        return None
    return BIBLE[a:b]


class TheWaitingOnYouReachesTheInbox(unittest.TestCase):

    def _run(self, host, state=None, post="", protocol="http:"):
        """Execute the shipped painter/fetch in node. -> {html, hidden, cache}"""
        blk = _block()
        if blk is None:
            self.fail("the needs-you block moved in bible.html — this law is grading nothing, "
                      "which is not a pass")
        js = ("var _host = { hidden: true, innerHTML: '' };\n"
              "var document = { getElementById: function(id){ "
              "return id === 'ibx-needsyou' ? _host : null; } };\n"
              "var location = { host: %s, protocol: %s };\n"
              "var setInterval = function(){};\n"
              % (json.dumps(host), json.dumps(protocol))) + blk + "\n"
        if state is not None:
            js += "_eagleNY = %s;\n" % json.dumps(state)
        js += "_eagleNYPaint();\n" + post + (
            "\nconsole.log(JSON.stringify({html: _host.innerHTML, hidden: _host.hidden, "
            "cache: _eagleNY}));")
        d = tempfile.mkdtemp(prefix="needsyou_")
        self.addCleanup(shutil.rmtree, d, True)
        f = os.path.join(d, "t.js")
        io.open(f, "w", encoding="utf-8").write(js)
        try:
            r = subprocess.run(["node", f], capture_output=True, text=True, timeout=60)
        except Exception:
            self.fail("node is REQUIRED by this gate and is not on PATH — a law that does not "
                      "run is not a pass")
        if r.returncode != 0:
            self.fail("the shipped needs-you block would not execute: %s" % (r.stderr or "")[:300])
        return json.loads(r.stdout.strip().splitlines()[-1])

    CONSOLE = "127.0.0.1:17772"

    # ── the join carries the rows ─────────────────────────────────────────────────────────────
    def test_the_waiting_rows_render_with_their_names_and_whys(self):
        got = self._run(self.CONSOLE, state={
            "st": "rows", "why": "", "needsYou": 2, "unknown": 9, "say": "",
            "rows": [{"check": "screen still painting", "state": "missing", "why": "frozen"},
                     {"check": "the river", "state": "missing", "why": "outlet dry"}], "at": 1})
        self.assertFalse(got["hidden"])
        for frag in ("WAITING ON YOU", "screen still painting", "the river", "frozen",
                     "(+9 not measured)"):
            self.assertIn(frag, got["html"],
                          "the inbox section must carry %r — a join that drops the content is "
                          "the unjoined end with extra steps" % frag)

    # ── absence is never zero ─────────────────────────────────────────────────────────────────
    def test_off_console_reads_unknown_not_nothing_waiting(self):
        got = self._run("bull-4-u.com")
        self.assertIn("UNKNOWN", got["html"])
        self.assertIn("not connected", got["html"])
        self.assertNotIn("none", got["html"].lower().replace("not connected", ""),
                         "off the console there is no watchdog to ask; 'none' would be a zero "
                         "nobody measured")

    def test_an_unreachable_console_reads_unknown_with_the_reason(self):
        got = self._run(self.CONSOLE, state={"st": "unreachable", "why": "fetch failed",
                                             "needsYou": None, "unknown": None, "rows": [],
                                             "say": "", "at": 1})
        self.assertIn("UNKNOWN", got["html"])
        self.assertIn("did not answer", got["html"])
        self.assertIn("Not zero", got["html"])

    def test_an_unmeasured_eagle_reads_unknown_not_clear(self):
        got = self._run(self.CONSOLE, state={"st": "unmeasured", "why": "", "needsYou": None,
                                             "unknown": None, "rows": [], "say": "", "at": 1})
        self.assertIn("not looked yet", got["html"])
        self.assertIn("UNKNOWN", got["html"])

    def test_all_clear_carries_its_denominator(self):
        """[[zero-needs-a-denominator]] — 'none' beside WHAT was measured, or the zero is bare."""
        got = self._run(self.CONSOLE, state={"st": "clear", "why": "", "needsYou": 0,
                                             "unknown": 0, "rows": [],
                                             "say": "all clear across 57 check(s)", "at": 1})
        self.assertIn("none", got["html"])
        self.assertIn("57", got["html"], "the denominator must ride with the zero")

    # ── the classifier ────────────────────────────────────────────────────────────────────────
    def test_the_fetch_classifier_states(self):
        post = """
var _done;
var P = new Promise(function(res){ _done = res; });
var fetch = function(){ return Promise.resolve({ json: function(){ return Promise.resolve({
  eagle: { needsYou: 1, unknown: 3,
           rows: [ {check: 'a', state: 'ok', why: ''},
                   {check: 'b', state: 'missing', why: 'w'},
                   {check: 'c', state: 'unknown', why: ''} ] } }); } }); };
_eagleNYFetch();
setTimeout(function(){
  var first = JSON.parse(JSON.stringify(_eagleNY));
  fetch = function(){ return Promise.resolve({ json: function(){ return Promise.resolve({
    eagle: { needsYou: null, rows: [] } }); } }); };
  _eagleNYFetch();
  setTimeout(function(){
    console.log(JSON.stringify({html: _host.innerHTML, hidden: _host.hidden,
                                cache: {first: first, second: _eagleNY}}));
  }, 30);
}, 30);
"""
        blk = _block()
        js = ("var _host = { hidden: true, innerHTML: '' };\n"
              "var document = { getElementById: function(id){ "
              "return id === 'ibx-needsyou' ? _host : null; } };\n"
              "var location = { host: '127.0.0.1:17772' };\n"
              "var setInterval = function(){};\n") + blk + post
        d = tempfile.mkdtemp(prefix="needsyou2_")
        self.addCleanup(shutil.rmtree, d, True)
        f = os.path.join(d, "t.js")
        io.open(f, "w", encoding="utf-8").write(js)
        try:
            r = subprocess.run(["node", f], capture_output=True, text=True, timeout=60)
        except Exception:
            self.fail("node is REQUIRED by this gate and is not on PATH")
        if r.returncode != 0:
            self.fail("the fetch classifier would not execute: %s" % (r.stderr or "")[:300])
        got = json.loads(r.stdout.strip().splitlines()[-1])
        first, second = got["cache"]["first"], got["cache"]["second"]
        self.assertEqual(first["st"], "rows")
        self.assertEqual([x["check"] for x in first["rows"]], ["b"],
                         "only state==='missing' rows are WAITING — an 'ok' or 'unknown' row in "
                         "the pile teaches him the pile lies")
        self.assertEqual(second["st"], "unmeasured",
                         "needsYou null is the eagle never having looked — unmeasured, not clear")

    def test_my_own_defects_are_never_billed_to_him(self):
        """⚠⚠ v3010 — THE MINE PARTITION IS THE SERVER'S CONTRACT. needsYou excludes rows owned by
        Claude (the v2284 rule), and v3006 counted every missing row — measured live: the chip
        said 11 while the section would have painted 13, the two extra being MY defects he cannot
        act on. Re-billing him for my bugs is how the pile stops being believed."""
        post = """
var _done;
var fetch = function(){ return Promise.resolve({ json: function(){ return Promise.resolve({
  eagle: { needsYou: 1, unknown: 2, mine: 1, mineWhat: ['extraction lanes'],
           rows: [ {check: 'extraction lanes', state: 'missing', why: 'mine'},
                   {check: 'the river', state: 'missing', why: 'his'} ] } }); } }); };
_eagleNYFetch();
setTimeout(function(){
  console.log(JSON.stringify({html: _host.innerHTML, hidden: _host.hidden, cache: _eagleNY}));
}, 30);
"""
        got = self._run(self.CONSOLE, post=post)
        self.assertEqual([r["check"] for r in got["cache"]["rows"]], ["the river"],
                         "a Claude-owned missing row must be held OUT of his pile")
        self.assertIn("held out", got["html"], "and the hold is SAID, not silent")
        self.assertIn("the river", got["html"])
        self.assertNotIn("extraction lanes</b>", got["html"])

    def test_only_what_the_server_says_asks_him_reaches_his_pile(self):
        """#226 -- his ruling: "it should only really be waiting on me if its something i need to
        do". The server names the rows that ASK him something (needsYouWhat); the pile draws those
        and nothing else -- not a red row with no question, not a by-design one. Measured before:
        this pile billed 7 where the console billed 5, because it re-decided ownership here."""
        post = """
var fetch = function(){ return Promise.resolve({ json: function(){ return Promise.resolve({
  eagle: { needsYou: 1, unknown: 0, mine: 1, mineWhat: ['ledger staleness'],
           byDesignWhat: ['the river'], needsYouWhat: ['shadow gate'],
           noQuestionWhat: ['ledger staleness', 'handoff lanes drained'],
           rows: [ {check: 'ledger staleness', state: 'missing', why: 'a bake owed'},
                   {check: 'handoff lanes drained', state: 'missing', why: 'asks him nothing'},
                   {check: 'the river', state: 'missing', why: 'by design'},
                   {check: 'shadow gate', state: 'missing', why: 'your call'} ] } }); } }); };
_eagleNYFetch();
setTimeout(function(){
  console.log(JSON.stringify({html: _host.innerHTML, hidden: _host.hidden, cache: _eagleNY}));
}, 30);
"""
        # `handoff lanes drained` is in NO list the pile could re-derive from (not mineWhat, not
        # byDesignWhat) -- only the server's needsYouWhat leaves it out, so this case can tell
        # "reads the server" from "re-decides locally" (heart2 caught the first cut BLIND).
        got = self._run(self.CONSOLE, post=post)
        self.assertEqual([r["check"] for r in got["cache"]["rows"]], ["shadow gate"],
                         "a row that asks him nothing, or is red by design, reached his pile")

    def test_an_older_payload_still_holds_the_by_design_rows_out(self):
        post = """
var fetch = function(){ return Promise.resolve({ json: function(){ return Promise.resolve({
  eagle: { needsYou: 1, unknown: 0, mine: 0, mineWhat: [], byDesignWhat: ['the river'],
           rows: [ {check: 'the river', state: 'missing', why: 'by design'},
                   {check: 'shadow gate', state: 'missing', why: 'your call'} ] } }); } }); };
_eagleNYFetch();
setTimeout(function(){
  console.log(JSON.stringify({html: _host.innerHTML, hidden: _host.hidden, cache: _eagleNY}));
}, 30);
"""
        got = self._run(self.CONSOLE, post=post)
        self.assertEqual([r["check"] for r in got["cache"]["rows"]], ["shadow gate"])

    ASK = {"id": "shadow-gate", "kind": "decide", "fp": "shadow-gate:wouldHold",
           "q": "Should the console be stricter before it ticks a grail item by itself?",
           "answers": [{"key": "keep", "label": "Keep it as it is", "effect": "ruled"},
                       {"key": "stricter", "label": "Be stricter (Wilson)", "effect": "handoff"},
                       {"key": "week", "label": "Ask me in a week", "effect": "snooze"}]}

    def _ask_state(self, **kw):
        st = {"st": "rows", "why": "", "needsYou": 1, "unknown": 0, "mine": 3, "say": "", "at": 1,
              "rows": [{"check": "shadow gate", "state": "missing", "why": "57 of 451 names differ",
                        "asks": [self.ASK], "openAsks": [self.ASK]}], "answered": []}
        st.update(kw)
        return st

    def test_a_question_is_drawn_with_its_answers(self):
        """#223 -- his ask: "if need something done of me what exactly and ... the option there to
        tally it off". The row he owes is drawn as its QUESTION with one button per answer, each
        carrying the question's fingerprint so an old card cannot answer a changed question."""
        got = self._run(self.CONSOLE, state=self._ask_state())
        h = got["html"]
        self.assertIn("YOUR CALL", h)
        self.assertIn("Should the console be stricter", h, "the question itself is not on the card")
        for key in ("keep", "stricter", "week"):
            self.assertIn('data-key="%s"' % key, h, "the %r answer has no button" % key)
        self.assertIn('data-fp="shadow-gate:wouldHold"', h)
        self.assertIn("_askAnswer", h, "the buttons answer nothing")

    def test_a_console_on_another_port_still_draws_the_question(self):
        """A board served by a console on any loopback port (a second console, a box on another
        port, the render harness) is connected. The port test alone painted 'not connected'."""
        got = self._run("127.0.0.1:18123", state=self._ask_state())
        self.assertNotIn("not connected", got["html"])
        self.assertIn('data-key="keep"', got["html"])

    def test_a_board_off_disk_says_where_to_answer_instead(self):
        """A file:// board sends Origin null, which the console refuses; a button that can only
        fail is worse than a sentence saying where the answer goes."""
        got = self._run(self.CONSOLE, state=self._ask_state(), protocol="file:")
        self.assertIn("Opened from disk", got["html"])
        self.assertNotIn('data-key="keep"', got["html"], "a board off disk offered a button that cannot work")

    def test_what_he_answered_is_drawn_and_can_be_changed(self):
        ans = {"askId": "shadow-gate", "key": "keep", "label": "Keep it as it is", "effect": "ruled",
               "fp": "shadow-gate:wouldHold", "at": 1790000000000, "until": 1792592000000}
        st = self._ask_state(st="clear", rows=[], needsYou=0,
                             answered=[{"check": "shadow gate", "state": "missing", "answered": [ans]}])
        got = self._run(self.CONSOLE, state=st)
        self.assertIn("ANSWERED BY YOU", got["html"], "his answer vanished instead of being shown")
        self.assertIn("you: Keep it as it is", got["html"])
        self.assertIn("_askWithdraw", got["html"], "he cannot change his answer")

    def test_the_answered_rows_come_from_the_servers_list(self):
        post = """
var fetch = function(){ return Promise.resolve({ json: function(){ return Promise.resolve({
  eagle: { needsYou: 0, unknown: 0, mine: 1, mineWhat: ['ledger staleness'], needsYouWhat: [],
           answeredWhat: ['shadow gate'],
           rows: [ {check: 'ledger staleness', state: 'missing', why: 'a bake owed'},
                   {check: 'shadow gate', state: 'missing', why: 'your call',
                    answered: [{askId: 'shadow-gate', key: 'keep', label: 'Keep it as it is'}]} ] } }); } }); };
_eagleNYFetch();
setTimeout(function(){
  console.log(JSON.stringify({html: _host.innerHTML, hidden: _host.hidden, cache: _eagleNY}));
}, 30);
"""
        got = self._run(self.CONSOLE, post=post)
        self.assertEqual(got["cache"]["st"], "clear")
        self.assertEqual([r["check"] for r in got["cache"]["answered"]], ["shadow gate"])
        self.assertIn("you: Keep it as it is", got["html"])

    def test_a_crashed_watchdog_is_not_dressed_as_a_young_one(self):
        """needsYou:null covers never-ran AND ran-and-crashed; the server's say tells them apart
        and the painter must too. [[unknown-stays-unknown]]"""
        got = self._run(self.CONSOLE, state={"st": "unmeasured",
                                             "why": "the eagle could not run: boom",
                                             "needsYou": None, "unknown": None, "mine": None,
                                             "rows": [], "say": "the eagle could not run: boom",
                                             "at": 1})
        self.assertIn("FAULT OF ITS OWN", got["html"])
        self.assertIn("boom", got["html"])
        got2 = self._run(self.CONSOLE, state={"st": "unmeasured", "why": "", "needsYou": None,
                                              "unknown": None, "mine": None, "rows": [],
                                              "say": "", "at": 1})
        self.assertIn("not looked yet", got2["html"])

    def test_an_unknown_not_measured_count_says_unknown_not_zero(self):
        got = self._run(self.CONSOLE, state={"st": "rows", "why": "", "needsYou": 1,
                                             "unknown": None, "mine": None,
                                             "rows": [{"check": "a", "state": "missing",
                                                       "why": "w"}], "say": "", "at": 1})
        self.assertIn("not-measured count UNKNOWN", got["html"],
                      "an absent count folded into a quiet nothing is a manufactured zero")

    def test_a_capped_list_says_what_it_elided(self):
        rows = [{"check": "c%02d" % i, "state": "missing", "why": "w"} for i in range(25)]
        got = self._run(self.CONSOLE, state={"st": "rows", "why": "", "needsYou": 25,
                                             "unknown": 0, "mine": None, "rows": rows,
                                             "say": "", "at": 1})
        self.assertIn("and 5 more", got["html"],
                      "a header of 25 above 20 visible rows is a number under a list of a "
                      "different size — the elision must be said")

    def test_a_file_board_probes_the_loopback_and_https_does_not(self):
        """⚠ v3010 — the console's no-webview fallback opens this same file as file://; v3006
        painted 'not connected' FOREVER on a board one absolute URL from its own console. A
        file:// page probes the loopback; the PUBLIC site still never probes a laptop that is
        not there."""
        # ⚠ the harness appends its own final print of {html, hidden, cache:_eagleNY} and _run
        # parses the LAST line — so the probe result rides IN the cache rather than in a print of
        # this law's own that would be superseded.
        got = self._run("", state=None, protocol="file:",
                        post="_eagleNY.base = _eagleNYBase();")
        self.assertEqual(got["cache"].get("base"), "http://127.0.0.1:17772",
                         "a file:// board must probe the loopback console")
        got2 = self._run("bull-4-u.com", state=None, protocol="https:",
                         post="_eagleNY.base = _eagleNYBase();")
        self.assertIsNone(got2["cache"].get("base"),
                          "the public site must never probe a laptop that is not there")

    def test_the_boot_tap_actually_fires_and_repeats(self):
        """⚠⚠ THE REVIEW'S OWN WORDS: the boot _eagleNYFetch() and the 120s interval 'sit outside
        every law and RED_PROOF — the gate built to close an unjoined end cannot see its own join
        point'. This EXECUTES the boot block with counting stubs."""
        a = BIBLE.find(OPEN_ANCHOR)
        b = BIBLE.find(CLOSE_ANCHOR, a)
        c = BIBLE.find("  } catch(e){}", b)
        self.assertTrue(a >= 0 and b > a and c > b, "the boot block moved")
        boot = BIBLE[b:c + len("  } catch(e){}")]
        js = ("var paints = 0, fetches = 0, intervals = [];\n"
              "var _eagleNYPaint = function(){ paints++; };\n"
              "var _eagleNYFetch = function(){ fetches++; };\n"
              "var setInterval = function(fn, ms){ "
              "intervals.push({same: fn === _eagleNYFetch, ms: ms}); };\n"
              + boot +
              "\nconsole.log(JSON.stringify({paints: paints, fetches: fetches, "
              "intervals: intervals}));")
        d = tempfile.mkdtemp(prefix="boottap_")
        self.addCleanup(shutil.rmtree, d, True)
        f = os.path.join(d, "t.js")
        io.open(f, "w", encoding="utf-8").write(js)
        try:
            r = subprocess.run(["node", f], capture_output=True, text=True, timeout=60)
        except Exception:
            self.fail("node is REQUIRED and is not on PATH")
        if r.returncode != 0:
            self.fail("the boot block would not execute: %s" % (r.stderr or "")[:200])
        got = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertGreaterEqual(got["fetches"], 1, "the join point never asks the console once")
        self.assertEqual([iv for iv in got["intervals"] if iv["same"] and iv["ms"] == 120000],
                         [{"same": True, "ms": 120000}],
                         "the repeat is the tap; without it the section paints once and rots")

    def test_the_badge_punches_the_collapse_with_the_eagle_count(self):
        """⚠⚠ v3010 — the card ships COLLAPSED and the body is display:none; the badge is the one
        element that punches through, and v3006 never fed it — 12 waiting rows changed NOTHING on
        screen. EXECUTES the shipped badge."""
        a = BIBLE.find("  window.renderInboxBadge = function(){")
        self.assertGreater(a, 0, "the badge painter moved")
        b = BIBLE.find("    return n;\n  };", a)
        self.assertGreater(b, a, "the badge painter's close moved")
        block = BIBLE[a:b + len("    return n;\n  };")]
        js = ("var _el = { hidden: true, textContent: '', title: '' };\n"
              "var document = { getElementById: function(){ return _el; } };\n"
              "var window = { kaiChronicleInbox: function(){ return [1, 2]; } };\n"
              "var _eagleNY = { st: 'rows', rows: [{}, {}, {}] };\n"
              + block +
              "\nwindow.renderInboxBadge();"
              "\nconsole.log(JSON.stringify(_el));")
        d = tempfile.mkdtemp(prefix="badge_")
        self.addCleanup(shutil.rmtree, d, True)
        f = os.path.join(d, "t.js")
        io.open(f, "w", encoding="utf-8").write(js)
        try:
            r = subprocess.run(["node", f], capture_output=True, text=True, timeout=60)
        except Exception:
            self.fail("node is REQUIRED and is not on PATH")
        if r.returncode != 0:
            self.fail("the badge would not execute: %s" % (r.stderr or "")[:200])
        el = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertFalse(el["hidden"])
        self.assertIn("2 waiting", el["textContent"])
        self.assertIn("3 need you", el["textContent"],
                      "the collapsed card must SAY the watchdog rows are inside, or the join "
                      "ends at a wall he cannot see through")

    # ── the seams ─────────────────────────────────────────────────────────────────────────────
    def test_the_container_is_a_sibling_of_the_panel_not_a_child(self):
        """renderInbox writes #inbox-panel's innerHTML wholesale; a child would be clobbered on
        every repaint — v2219's exact class of bug."""
        i = BIBLE.find('<div id="ibx-needsyou" hidden></div>')
        j = BIBLE.find('<div id="inbox-panel"></div>')
        self.assertGreater(i, 0, "the needs-you container is gone from the static HTML")
        self.assertGreater(j, i, "it must sit BEFORE #inbox-panel as a sibling")
        self.assertLess(j - i, 120, "and adjacent to it, not somewhere else entirely")

    def test_the_section_has_css(self):
        """A class with no rule renders as bare text — how .ftts-unsynced shipped unstyled."""
        self.assertIn("#ibx-needsyou .ibx-ny{", BIBLE)
        self.assertIn("#ibx-needsyou .ibx-ny-warn{", BIBLE)


RED_PROOF = [
    {
        "why": "#223 - a board served by a console on another port reads 'not connected' again and draws no question",
        "file": "bible.html",
        "find": "      if (String(location.protocol || '') === 'http:'\n",
        "replace": "      if (false && String(location.protocol || '') === 'http:'\n",
        "matches": 1,
    },
    {
        "why": "#223 - the row he owes is drawn as a plain line again: the question and its answer buttons are gone",
        "file": "bible.html",
        "find": "        if (_open.length){ h += _askCardsHtml(r, _open, esc); continue; }\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#223 - what he answered is never drawn: his ruling vanishes from the inbox and cannot be changed",
        "file": "bible.html",
        "find": "        + (_ansH ? '<div class=\"ibx-ny\">' + _ansH + '</div>' : '');",
        "replace": "        + '';",
        "matches": 1,
    },
    {
        "why": "#223 - a board off disk offers buttons whose every press is refused (Origin null)",
        "file": "bible.html",
        "find": "      if (disk){\n        h += '<div class=\"ibx-ny-said\">Opened from disk",
        "replace": "      if (false){\n        h += '<div class=\"ibx-ny-said\">Opened from disk",
        "matches": 1,
    },
    {
        "why": "#226 - the pile re-decides ownership again instead of reading the server's list: rows that ask him nothing are billed to him",
        "file": "bible.html",
        "find": "        if (nyW ? nyW.indexOf(rows[i].check) >= 0\n",
        "replace": "        if (false ? nyW.indexOf(rows[i].check) >= 0\n",
        "matches": 1,
    },
    {
        "why": "dropping the no-console branch makes the public site paint the on-console states "
               "about a console it cannot reach — 'nothing waiting' told to strangers",
        "file": "bible.html",
        "find": "    if (_eagleNYBase() === null){",
        "replace": "    if (false){",
        "matches": 1,
    },
    {
        "why": "counting every missing row re-bills him for Claude's own defects — the chip says "
               "11 while the pile paints 13, and a pile that lies is one he stops reading",
        "file": "bible.html",
        "find": "                : (mineW.indexOf(rows[i].check) < 0 && designW.indexOf(rows[i].check) < 0)) bad.push(rows[i]);",
        "replace": "                : true) bad.push(rows[i]);",
        "matches": 1,
    },
    {
        "why": "an unfed badge behind a collapsed card is 12 waiting rows changing nothing on "
               "screen — the join ending at a wall",
        "file": "bible.html",
        "find": "    try { if (typeof _eagleNY === 'object' && _eagleNY && _eagleNY.st === 'rows')",
        "replace": "    try { if (false)",
        "matches": 1,
    },
    {
        "why": "killing the repeat leaves one paint at boot that rots forever — the join point "
               "the review said no law could see",
        "file": "bible.html",
        "find": "    setInterval(_eagleNYFetch, 120000);",
        "replace": "    void(0);",
        "matches": 1,
    },
    {
        "why": "dropping the null check folds 'the eagle never looked' into 'all clear' — the "
               "exact absence-reads-as-healthy this section exists to refuse",
        "file": "bible.html",
        "find": "    if (e.needsYou == null){",
        "replace": "    if (false){",
        "matches": 1,
    },
]

if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
