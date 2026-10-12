# -*- coding: utf-8 -*-
"""The D2JSP room posts a tagged vault item through the login already open
in the browser, and forum gold stays unknown until a public reading returns
a price.

The site cannot attach his d2jsp session from another origin, so the bridge
runs on forums.d2jsp.org. It submits only when that page is board 268 and
the browser is logged in. A challenge page or a page with no fg number does
not become a price.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BIBLE = os.path.join(ROOT, "bible.html")
QUOTE = os.path.join(ROOT, "functions", "api", "d2jsp_quote.js")
UI = os.path.join(HERE, "control_ui.html")
BEACON = os.path.join(ROOT, "functions", "api", "console.js")
NODE = shutil.which("node")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _between(src, start, end):
    i = src.index(start)
    j = src.index(end, i + len(start))
    return src[i + len(start):j]


def _node(prelude, body):
    prog = prelude + "\n;(function(){\n" + body + "\n})();\n"
    r = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("node failed: " + (r.stderr or r.stdout)[-2000:])
    return r.stdout


class TheD2jspDeskReadsAPriceBeforeItPosts(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.bible = _read(BIBLE)
        cls.quote = _read(QUOTE)
        cls.ui = _read(UI)
        cls.desk = _between(cls.bible, "/* ⟦D2JSP DESK BEGIN⟧ */\n", "\n/* ⟦D2JSP DESK END⟧ */")
        cls.parser = _between(cls.quote, "/* ⟦D2JSP QUOTE BEGIN⟧ */\n", "\n/* ⟦D2JSP QUOTE END⟧ */")

    def test_the_room_is_a_workshop_tab_and_not_a_console_door(self):
        ws = _between(self.bible, '<div class="tabs-workshop"', "</div>")
        order = __import__("re").findall(r'data-tab="([a-z0-9]+)"', ws)
        self.assertEqual(order.index("vault") + 1, order.index("d2jsp"), order)
        self.assertEqual(self.bible.count('id="tab-d2jsp"'), 1)
        self.assertIn("never asks for the password", self.bible)
        self.assertIn("Forum gold stays unknown until a public reading", self.bible)
        self.assertIn('data-tab="d2jsp"', _between(
            self.bible, 'body.app-ctx .tabs .tab[data-tab="session"]', "display:inline-flex"))
        pane = _between(self.bible, 'id="tab-d2jsp"', 'id="tab-vault"')
        self.assertNotIn('type="password"', pane)
        nav_at = self.ui.index('id="head-tabs"')
        nav = self.ui[nav_at:self.ui.index("</nav>", nav_at)]
        self.assertNotIn("d2jsp", nav)
        self.assertNotIn("d2jsp", _read(BEACON))

    def test_a_public_reading_with_no_price_stays_unknown(self):
        if NODE is None:
            self.skipTest("node is not on this machine")
        body = r"""
var page = 'Grief Phase Blade\nBump\n\nShako\n20 fg\n';
var prices = d2jspPrices(page, 'Grief');
var none = d2jspRead('Just a moment...', 'Grief', '2026-10-12T20:00:00.000Z');
var empty = d2jspRead(page, 'Grief', '2026-10-12T20:00:00.000Z');
var hit = d2jspRead('Grief Phase Blade 10 fg\n\nGrief 50 fg\n\nGrief 30 fg\n\nShako 200 fg', 'Grief', '2026-10-12T20:01:00.000Z');
process.stdout.write(JSON.stringify({prices: prices, none: none, empty: empty, hit: hit}));
"""
        out = json.loads(_node("var BOARD = 268;\n" + self.parser, body))
        self.assertEqual(out["prices"], [])
        self.assertIsNone(out["none"]["fg"])
        self.assertEqual(out["none"]["reason"], "unread")
        self.assertEqual(out["none"]["readAt"], "2026-10-12T20:00:00.000Z")
        self.assertIsNone(out["empty"]["fg"])
        self.assertEqual(out["empty"]["reason"], "no prices")
        self.assertEqual(out["hit"]["fg"], 30)
        self.assertEqual(out["hit"]["n"], 3)
        self.assertEqual(out["hit"]["reason"], "read")

    def test_a_post_waits_for_a_price_and_the_open_login(self):
        if NODE is None:
            self.skipTest("node is not on this machine")
        body = r"""
var blocked = d2jspDraft('Grief', 'Phase Blade', '+damage', 2, null);
var draft = d2jspDraft('Grief', 'Phase Blade', '+damage', 2, d2jspPriceToSend(30, ''));
var typed = d2jspPriceToSend(30, '40');
var garbage = d2jspPriceToSend(30, 'abc');
var url = d2jspPostUrl(draft);
var clicks = 0;
function el(name){ return { name: name, value: '', click: function(){ clicks++; } }; }
var loggedOut = {
  querySelector: function(sel){
    if (sel.indexOf('subject') >= 0) return el('subject');
    if (sel.indexOf('message') >= 0) return el('message');
    if (sel.indexOf('logout') >= 0) return null;
    if (sel.indexOf('post') >= 0) return el('post');
    return null;
  }
};
var subject = el('subject');
var message = el('message');
var post = el('post');
var loggedIn = {
  querySelector: function(sel){
    if (sel.indexOf('subject') >= 0) return subject;
    if (sel.indexOf('message') >= 0) return message;
    if (sel.indexOf('logout') >= 0) return { href: 'mode=logout' };
    if (sel.indexOf('post') >= 0) return post;
    return null;
  }
};
var hash = url.slice(url.indexOf('#'));
var search = url.slice(url.indexOf('?'), url.indexOf('#'));
var need = d2jspBridgeAct(loggedOut, { hash: hash, search: search }, null);
var sent = d2jspBridgeAct(loggedIn, { hash: hash, search: search }, null);
var wrong = d2jspBridgeAct(loggedIn, { hash: hash, search: '?mode=post&f=271' }, null);
var src = d2jspBridgeSource();
process.stdout.write(JSON.stringify({
  blocked: blocked, draft: draft, typed: typed, garbage: garbage,
  url: url, need: need, sent: sent, wrong: wrong, clicks: clicks,
  subject: subject.value, body: message.value, srcHasPassword: src.indexOf('password') >= 0,
  srcHasLogout: src.indexOf('mode=logout') >= 0
}));
"""
        out = json.loads(_node(self.desk, body))
        self.assertFalse(out["blocked"]["ok"])
        self.assertEqual(out["blocked"]["reason"], "no price")
        self.assertTrue(out["draft"]["ok"])
        self.assertIn("30 fg", out["draft"]["body"])
        self.assertNotIn("password", out["draft"]["body"])
        self.assertEqual(out["draft"]["forum"], 268)
        self.assertEqual(out["typed"], 40)
        self.assertIsNone(out["garbage"])
        self.assertIn("post.php?mode=post&f=268#d2r=", out["url"])
        self.assertEqual(out["need"], "need-login")
        self.assertEqual(out["sent"], "submitted")
        self.assertEqual(out["wrong"], "wrong-board")
        self.assertEqual(out["clicks"], 1)
        self.assertIn("Grief", out["subject"])
        self.assertIn("30 fg", out["body"])
        self.assertFalse(out["srcHasPassword"])
        self.assertTrue(out["srcHasLogout"])


if __name__ == "__main__":
    unittest.main()
