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

    def _run(self, host, state=None, post=""):
        """Execute the shipped painter/fetch in node. -> {html, hidden, cache}"""
        blk = _block()
        if blk is None:
            self.fail("the needs-you block moved in bible.html — this law is grading nothing, "
                      "which is not a pass")
        js = ("var _host = { hidden: true, innerHTML: '' };\n"
              "var document = { getElementById: function(id){ "
              "return id === 'ibx-needsyou' ? _host : null; } };\n"
              "var location = { host: %s };\n"
              "var setInterval = function(){};\n"
              % json.dumps(host)) + blk + "\n"
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
        "why": "dropping the off-console branch makes the public site paint the on-console "
               "states about a console it cannot reach — 'nothing waiting' told to strangers",
        "file": "bible.html",
        "find": "    if (!onConsole){\n      /* off the console",
        "replace": "    if (false){\n      /* off the console",
        "matches": 1,
    },
    {
        "why": "counting every row as waiting puts 'ok' checks in his pile, and a pile that lies "
               "is one he stops reading",
        "file": "bible.html",
        "find": "              if (rows[i] && rows[i].state === 'missing') bad.push(rows[i]);",
        "replace": "              if (rows[i]) bad.push(rows[i]);",
        "matches": 1,
    },
    {
        "why": "dropping the null check folds 'the eagle never looked' into 'all clear' — the "
               "exact absence-reads-as-healthy this section exists to refuse",
        "file": "bible.html",
        "find": "          if (e.needsYou == null){",
        "replace": "          if (false){",
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
