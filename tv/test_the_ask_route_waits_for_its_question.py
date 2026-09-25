# -*- coding: utf-8 -*-
"""#25 — "CHOOSE IN INBOX" NEVER COUNTS A NOT-YET-LAID-OUT QUESTION AS LANDED.

His report, 2026-09-25: the state panel's YOUR CALL — CHOOSE IN INBOX → button took him to the Tools tab with a BLACK
page body and the scrollbar mid-page. Not reproduced in headless Chrome (fresh load, collapsed dock, from a page
scrolled to the bottom - it lands every time) and GrokBot's WebKit seat had no question to click. Hardened against the
one mechanism that yields exactly that picture: the board's d2rOpenAsk scrolled to a card whose pane had not laid out
yet (a ZERO-SIZE rect), landed in empty space, and reported landed. Now a zero-size target answers retry:true, and the
console's route keeps polling inside its existing 40 x 80 ms budget instead of stopping there.

  · DRIVEN (node, the SHIPPED d2rOpenAsk cut from bible.html): a zero-size card -> retry, no scroll; a laid-out card
    -> landed, scrolled once.
  · DRIVEN (node, the SHIPPED window._hubGoAsk cut from control_ui.html): two retries then a landing -> three asks and
    no toast; a card that never lays out -> the budget ends in the honest toast, never a silent stop.
RED_PROOF below.
"""
import io
import json
import os
import shutil
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NODE = shutil.which("node")


def _cut(path, start, end_marker):
    with io.open(path, encoding="utf-8") as fh:
        s = fh.read()
    assert s.count(start) == 1, "%s: the cut start is not unique (%d)" % (path, s.count(start))
    i = s.index(start)
    return s[i:s.index(end_marker, i) + len(end_marker)]


def _open_ask():
    return _cut(os.path.join(ROOT, "bible.html"), "  function d2rOpenAsk(id){\n",
                "    } catch(e){ return { landed: null, why: 'could not open the question: ' + (e && e.message) }; }\n  }\n")


def _hub_go_ask():
    return _cut(os.path.join(HERE, "control_ui.html"), "  window._hubGoAsk = function(id){\n",
                "    } catch (e) { /* routing must never throw into the panel that called it */ }\n  };\n")


def _node(js):
    r = subprocess.run([NODE, "-e", js], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("node could not run the shipped code - UNKNOWN, not passing: %s" % r.stderr[:500])
    return json.loads(r.stdout.strip().splitlines()[-1])


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class TheAskRouteWaitsForItsQuestion(unittest.TestCase):

    def _board(self, w, h):
        js = r"""
var scrolled = 0;
var target = { getBoundingClientRect: function(){ return {width:%d, height:%d, top:400, bottom:400+%d}; },
  scrollIntoView: function(){ scrolled++; }, classList: { remove: function(){}, add: function(){} }, offsetWidth: 1,
  querySelector: function(){ return null; } };
var document = { getElementById: function(id){ return id === 'inbox-card' ? { classList: { contains: function(){ return false; }, remove: function(){} } } : null; },
  querySelector: function(sel){ return sel.indexOf('data-ask') >= 0 ? target : null; } };
var window = { innerHeight: 900, scrollBy: function(){} };
%s
var got = d2rOpenAsk('shadow-gate');
console.log(JSON.stringify({ got: got, scrolled: scrolled }));
""" % (w, h, h, _open_ask())
        return _node(js)

    def test_a_zero_size_question_is_not_a_landing(self):
        out = self._board(0, 0)
        self.assertTrue(out["got"].get("retry"), "a card with no layout was reported as landed: %r" % out)
        self.assertIsNone(out["got"].get("landed"))
        self.assertEqual(out["scrolled"], 0, "it scrolled to a card that has no position yet")

    def test_a_laid_out_question_lands(self):
        out = self._board(600, 109)
        self.assertTrue(out["got"].get("landed"), out)
        self.assertEqual(out["scrolled"], 1)

    def _route(self, retries_before_landing):
        js = r"""
var asks = 0, toasts = [], ticks = 0;
var board = { d2rOpenAsk: function(){ asks++; return asks <= %d ? { landed: null, retry: true, why: 'not laid out' }
                                                               : { landed: { top: 400, height: 109 }, why: '' }; } };
var document = { getElementById: function(id){ return id === 'tvd-eng' ? { contentWindow: board } : null; } };
var window = {};
function shellOpen(){}
function toast(m){ toasts.push(m); }
var _live = null;
function setInterval(fn){ _live = fn; return 1; }
function clearInterval(){ _live = null; }
%s
window._hubGoAsk('shadow-gate');
while (_live && ticks < 200) { ticks++; _live(); }
console.log(JSON.stringify({ asks: asks, toasts: toasts, stillPolling: !!_live }));
""" % (retries_before_landing, _hub_go_ask())
        return _node(js)

    def test_the_route_keeps_asking_until_the_question_lands(self):
        out = self._route(2)
        self.assertEqual(out["asks"], 3, "the route stopped at the first not-laid-out answer: %r" % out)
        self.assertEqual(out["toasts"], [], "a question that did land was reported as a failure")
        self.assertFalse(out["stillPolling"])

    def test_a_question_that_never_lays_out_ends_in_the_honest_toast(self):
        out = self._route(10000)
        self.assertFalse(out["stillPolling"], "the route polls forever")
        self.assertEqual(len(out["toasts"]), 1, "a question that never landed ended silently: %r" % out)
        self.assertLessEqual(out["asks"], 42, "the retry budget grew past its 40 x 80 ms bound")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#25 - a zero-size question is reported as landed again: the route leaves him on a blank page",
        "file": "bible.html",
        "find": "      if (!_r00.width && !_r00.height) return { landed: null, retry: true, why: 'the question is not laid out yet' };\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#25 - the route stops at the first not-laid-out answer instead of waiting for the pane",
        "file": "control_ui.html",
        "find": "            if (got && got.retry && n <= 40) return;\n",
        "replace": "",
        "matches": 1,
    },
]
