# -*- coding: utf-8 -*-
"""A cached d2jsp reading is not asked for again while it is still fresh.

Opening the trade room used to call ask() for every filed name, every time.
A reading younger than D2JSP_QUOTE_TTL_MS stays on the card and is not fetched.
A reading that has reached that age is asked again. A caller that passes force
still asks. The stamp is _ts on the cached object. The price sentence and the
fg a post would send do not change.

Runs the page's own ask / refreshQuotes / quoteFresh in node. No browser.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable
enable()

ROOT = os.path.dirname(HERE)
BIBLE = os.path.join(ROOT, "bible.html")
NODE = shutil.which("node")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _js_fn(src, signature):
    """The function whose source starts at this signature. Brace-matched, strings skipped."""
    n = src.count(signature)
    if n != 1:
        raise AssertionError("%r occurs %d times" % (signature, n))
    i = src.index(signature)
    k = src.index("{", i)
    depth = 0
    quote = None
    escape = False
    line_comment = False
    block_comment = False
    end = len(src)
    while k < end:
        c = src[k]
        nxt = src[k + 1] if k + 1 < end else ""
        if line_comment:
            if c == "\n":
                line_comment = False
            k += 1
            continue
        if block_comment:
            if c == "*" and nxt == "/":
                block_comment = False
                k += 2
                continue
            k += 1
            continue
        if quote:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == quote:
                quote = None
            k += 1
            continue
        if c in ("'", '"', "`"):
            quote = c
            k += 1
            continue
        if c == "/" and nxt == "/":
            line_comment = True
            k += 2
            continue
        if c == "/" and nxt == "*":
            block_comment = True
            k += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[i:k + 1]
        k += 1
    raise AssertionError("unclosed " + signature)


def _run(prog):
    r = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("node failed: " + (r.stderr or r.stdout)[-2000:])
    return r.stdout


class AFreshD2jspQuoteIsNotAskedAgain(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.bible = _read(BIBLE)

    def test_the_ttl_is_one_named_window_and_filing_asks_through_it(self):
        src = self.bible
        self.assertEqual(src.count("var D2JSP_QUOTE_TTL_MS = "), 1)
        line = [ln for ln in src.splitlines() if "var D2JSP_QUOTE_TTL_MS = " in ln]
        self.assertEqual(len(line), 1, line)
        import re
        m = re.fullmatch(r"  var D2JSP_QUOTE_TTL_MS = (\d+) \* (\d+) \* (\d+);", line[0])
        self.assertIsNotNone(m, line[0])
        ttl = int(m.group(1)) * int(m.group(2)) * int(m.group(3))
        self.assertGreaterEqual(ttl, 10 * 60 * 1000)
        self.assertLessEqual(ttl, 30 * 60 * 1000)
        filed = _js_fn(src, "function fileGear(entry)")
        self.assertIn("\n    ask(sh.name);\n", filed)
        ask = _js_fn(src, "function ask(name, done, force)")
        self.assertIn("quoteFresh(name)", ask)
        self.assertIn("quoted[name]._ts = Date.now();", ask)
        loop = _js_fn(src, "function refreshQuotes(force)")
        self.assertIn("if (!force && quoteFresh(name)) continue;", loop)
        self.assertIn("!!force", loop)

    def test_a_second_ask_inside_the_ttl_is_skipped_and_a_stale_one_is_not(self):
        if NODE is None:
            self.fail("node is not on this machine")
        src = self.bible
        price = _js_fn(src, "function d2jspPriceLine(q)")
        send = _js_fn(src, "function d2jspPriceToSend(quoted, typed)")
        fresh = _js_fn(src, "function quoteFresh(name)")
        ask = _js_fn(src, "function ask(name, done, force)")
        loop = _js_fn(src, "function refreshQuotes(force)")
        ttl_line = [ln.strip() for ln in src.splitlines() if "var D2JSP_QUOTE_TTL_MS = " in ln][0]
        prog = "\n".join([
            "var quoted = {};",
            "var pending = {};",
            "var reading = false;",
            "var flight = 0;",
            "var fetches = [];",
            "var nowMs = 1700000000000;",
            "Date.now = function(){ return nowMs; };",
            "function paintPrices(){}",
            "function say(){}",
            "var listed = ['Shako'];",
            "function listedNames(){ return listed.slice(); }",
            "var document = { getElementById: function(){ return { textContent: '' }; } };",
            "function fetch(url){",
            "  fetches.push(String(url));",
            "  return Promise.resolve({ json: function(){ return Promise.resolve(",
            "    { fg: 40, low: 40, high: 40, n: 1, readAt: '2026-10-15T00:00:00.000Z', reason: 'read' }); } });",
            "}",
            price, send, ttl_line, fresh, ask, loop,
            r"""
function flush(){ return new Promise(function(r){ setTimeout(r, 0); }); }
function asked(){ return fetches.map(function(u){ return decodeURIComponent(String(u).split('item=')[1] || ''); }); }
(async function(){
  var report = {};
  report.ttl = D2JSP_QUOTE_TTL_MS;
  var p1 = new Promise(function(res){ ask('Shako', res); });
  var p2 = new Promise(function(res){ ask('Shako', res); });
  await Promise.all([p1, p2]);
  await flush();
  report.coalesce = fetches.length;
  quoted.Shako.kept = 1;
  var n = fetches.length;
  await new Promise(function(res){ ask('Shako', res); });
  report.within = fetches.length - n;
  report.kept = quoted.Shako.kept === 1;
  report.fg = quoted.Shako.fg;
  var bare = { reason: 'read', fg: 40, n: 1, low: 40, high: 40, readAt: '2026-10-15T00:00:00.000Z' };
  report.line = d2jspPriceLine(quoted.Shako);
  report.lineKnown = d2jspPriceLine(bare);
  report.lineSame = report.line === report.lineKnown;
  report.send = d2jspPriceToSend(quoted.Shako.fg, '');
  report.sendSame = report.send === d2jspPriceToSend(bare.fg, '');
  nowMs += D2JSP_QUOTE_TTL_MS - 1;
  n = fetches.length;
  await new Promise(function(res){ ask('Shako', res); });
  report.edge = fetches.length - n;
  report.keptEdge = quoted.Shako.kept === 1;
  nowMs += 1;
  n = fetches.length;
  await new Promise(function(res){ ask('Shako', res); });
  await flush();
  report.after = fetches.length - n;
  report.replaced = quoted.Shako.kept !== 1;
  report.tsAfter = quoted.Shako._ts === nowMs;
  n = fetches.length;
  await new Promise(function(res){ ask('Shako', res, true); });
  await flush();
  report.forced = fetches.length - n;
  listed = ['Shako', 'Grief'];
  n = fetches.length;
  refreshQuotes();
  await flush();
  report.loopGap = fetches.length - n;
  report.loopGapNames = asked().slice(n);
  n = fetches.length;
  refreshQuotes();
  await flush();
  report.loopFresh = fetches.length - n;
  report.readingClear = reading === false;
  nowMs += D2JSP_QUOTE_TTL_MS;
  n = fetches.length;
  refreshQuotes();
  await flush();
  report.loopStale = fetches.length - n;
  report.loopStaleNames = asked().slice(n);
  report.readingClearAfter = reading === false;
  nowMs += 1000;
  n = fetches.length;
  refreshQuotes(true);
  await flush();
  report.loopForced = fetches.length - n;
  report.loopForcedNames = asked().slice(n);
  process.stdout.write(JSON.stringify(report));
})().catch(function(e){ process.stderr.write(String(e && e.stack || e)); process.exit(1); });
""",
        ])
        out = json.loads(_run(prog))
        self.assertGreaterEqual(out["ttl"], 10 * 60 * 1000, out)
        self.assertLessEqual(out["ttl"], 30 * 60 * 1000, out)
        self.assertEqual(out["coalesce"], 1, out)
        self.assertEqual(out["within"], 0, out)
        self.assertTrue(out["kept"], out)
        self.assertEqual(out["fg"], 40, out)
        self.assertTrue(out["lineSame"], out)
        self.assertEqual(out["line"], out["lineKnown"], out)
        self.assertIn("40", out["line"])
        self.assertTrue(out["sendSame"], out)
        self.assertEqual(out["send"], 40, out)
        self.assertEqual(out["edge"], 0, out)
        self.assertTrue(out["keptEdge"], out)
        self.assertEqual(out["after"], 1, out)
        self.assertTrue(out["replaced"], out)
        self.assertTrue(out["tsAfter"], out)
        self.assertEqual(out["forced"], 1, out)
        self.assertEqual(out["loopGap"], 1, out)
        self.assertEqual(out["loopGapNames"], ["Grief"], out)
        self.assertEqual(out["loopFresh"], 0, out)
        self.assertTrue(out["readingClear"], out)
        self.assertEqual(out["loopStale"], 2, out)
        self.assertEqual(out["loopStaleNames"], ["Shako", "Grief"], out)
        self.assertTrue(out["readingClearAfter"], out)
        self.assertEqual(out["loopForced"], 2, out)
        self.assertEqual(out["loopForcedNames"], ["Shako", "Grief"], out)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#107 - a fresh d2jsp reading is asked again inside the TTL, so the cache does not spare the lookup",
        "file": "bible.html",
        "find": "    return (Date.now() - ts) < D2JSP_QUOTE_TTL_MS;\n",
        "replace": "    return false;\n",
        "matches": 1,
    },
    {
        "why": "#107 - a d2jsp reading past the TTL is never asked again, so a stale price stays on the card",
        "file": "bible.html",
        "find": "    return (Date.now() - ts) < D2JSP_QUOTE_TTL_MS;\n",
        "replace": "    return true;\n",
        "matches": 1,
    },
    {
        "why": "#107 - a stored d2jsp reading carries no time, so the next ask cannot tell that it is fresh",
        "file": "bible.html",
        "find": "        quoted[name] = j;\n        quoted[name]._ts = Date.now();\n",
        "replace": "        quoted[name] = j;\n",
        "matches": 1,
    },
]
