# -*- coding: utf-8 -*-
"""The D2JSP room lists the vault filings and posts one priced item through
the Chrome login on this machine. Forum gold stays unknown until a public
reading returns a price.

The console reads the d2jsp cookie when he clicks Post. It is not stored
and not returned. A missing login, an unreadable cookie, or a board that
does not redirect to the topic does not become a sent post. A challenge
page or a page with no fg number does not become a price.
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
QUOTE = os.path.join(ROOT, "functions", "api", "d2jsp_quote.js")
UI = os.path.join(HERE, "control_ui.html")
BEACON = os.path.join(ROOT, "functions", "api", "console.js")
NODE = shutil.which("node")
# Story quest codes in tv/item_tables.json. Pandemonium keys, organs, essences
# and the token are the trade, so they are not in this tuple.
QUEST_CODES = (
    "ass", "bbb", "bkd", "bks", "box", "d33", "g33", "g34",
    "hdm", "hfh", "hst", "ibk", "ice", "j34", "key", "leg",
    "luv", "msf", "mss", "qbr", "qey", "qhr", "qf1", "qf2",
    "std", "tbk", "tr1", "tr2", "vip", "xyz",
)
QUEST_EXTRA = ("keys", "wirts leg", "tome")


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

    def test_the_room_is_a_workshop_tab_and_a_console_door(self):
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
        self.assertEqual(nav.count('data-tab="d2jsp"'), 1)
        self.assertIn('class="ht-lbl">D2JSP</span>', nav)
        self.assertLess(nav.index('data-tab="vault"'), nav.index('data-tab="d2jsp"'))
        self.assertLess(nav.index('data-tab="d2jsp"'), nav.index('data-tab="tvd"'))
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
var one = d2jspRead('Grief 40 fg', 'Grief', '2026-10-12T20:02:00.000Z');
var gheeds = d2jspRead([
  "Gheeds Fortune gc 106/35/13 - 20fg",
  "Gheeds Fortune gc 108/31/12 - 15fg",
  "Pcomb plain - 10fg x 1",
  "35MF gheeds",
  "Gheed's Fortune 10 fg",
  "Summon Skill Necro + 26 life - 25fg"
].join("\n"), "Gheed's Fortune", '2026-10-12T20:03:00.000Z');
var wall = d2jspRead('You do not have permission to use this feature.', "Gheed's Fortune", '2026-10-12T20:04:00.000Z');
process.stdout.write(JSON.stringify({prices: prices, none: none, empty: empty, hit: hit, one: one, gheeds: gheeds, wall: wall}));
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
        self.assertEqual(out["hit"]["low"], 10)
        self.assertEqual(out["hit"]["high"], 50)
        self.assertEqual(out["hit"]["reason"], "read")
        self.assertEqual(out["one"]["fg"], 40)
        self.assertEqual(out["one"]["n"], 1)
        self.assertEqual(out["one"]["low"], 40)
        self.assertEqual(out["one"]["high"], 40)
        self.assertIsNone(out["empty"]["low"])
        self.assertIsNone(out["empty"]["high"])
        self.assertIsNone(out["none"]["low"])
        self.assertIsNone(out["none"]["high"])
        self.assertEqual(out["hit"]["board"], 243)
        self.assertEqual(out["gheeds"]["fg"], 15)
        self.assertEqual(out["gheeds"]["n"], 3)
        self.assertEqual(out["gheeds"]["low"], 10)
        self.assertEqual(out["gheeds"]["high"], 20)
        self.assertEqual(out["gheeds"]["reason"], "read")
        self.assertIsNone(out["wall"]["fg"])
        self.assertEqual(out["wall"]["reason"], "need-login")
        self.assertEqual(out["wall"]["n"], 0)

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

    def test_the_room_lists_the_vault_and_posts_through_chrome(self):
        pane = _between(self.bible, 'id="tab-d2jsp"', 'id="tab-vault"')
        self.assertNotIn("Copy the bridge", pane)
        self.assertNotIn("d2jsp-bridge", pane)
        self.assertNotIn("cannot save the file", pane)
        self.assertNotIn("Install the bridge", pane)
        self.assertNotIn("Tag for trade", pane)
        room = pane.split("<script>", 1)[0]
        self.assertNotIn("<textarea", room)
        self.assertEqual(room.count('id="d2jsp-find"'), 1)
        self.assertIn('class="d2jsp-scroll"', room)
        self.assertNotIn("Read the public price", pane)
        self.assertNotIn("data-d2jsp-read", pane)
        end = self.bible.index("/* ⟦D2JSP DESK END⟧ */")
        names = self.bible.index("function names(){", end)
        esc_at = self.bible.index("function esc(s){", names)
        self.assertLess(esc_at - names, 1200)
        names_body = self.bible[names:esc_at]
        self.assertIn("d2r_muleAssign", names_body)
        self.assertNotIn("typeof assign", names_body)
        trade = self.bible.index("function tradeNames(){", end)
        find_q = self.bible.index("function findQuery(){", trade)
        self.assertIn("d2jspIsQuest", self.bible[trade:find_q])
        paint = self.bible.index("function paint(){", end)
        show = self.bible.index("window._d2jspShow = function(){", paint)
        self.assertIn("trade = tradeNames()", self.bible[paint:show])
        show_end = self.bible.index("};", show)
        self.assertIn("refreshQuotes()", self.bible[show:show_end])
        post = self.bible.index("t.getAttribute('data-d2jsp-post')")
        handler = self.bible[post:self.bible.index("document.addEventListener('input'", post)]
        self.assertIn("/api/d2jsp_send", handler)
        self.assertNotIn("createObjectURL", handler)
        self.assertNotIn("window.open", handler)
        self.assertNotIn("clipboard", handler)
        self.assertNotIn("d2jspBridgeSource()", handler)
        self.assertIn("nothing was posted", handler)
        app = _read(os.path.join(HERE, "control_app.py"))
        self.assertEqual(app.count('if path == "/api/d2jsp_send":'), 1)
        route = app.index('if path == "/api/d2jsp_send":')
        nxt = app.index('if path == "/api/roster-book":', route)
        block = app[route:nxt]
        self.assertIn("import d2jsp_chrome as _d2jsp", block)
        self.assertIn("_d2jsp.d2jsp_send(", block)
        self.assertEqual(app.count('if path == "/api/d2jsp_quote":'), 1)
        quote_route = app.index('if path == "/api/d2jsp_quote":')
        quote_next = app.index('if path in ("/", "/index.html", "/ui"):', quote_route)
        qblock = app[quote_route:quote_next]
        self.assertIn("import d2jsp_chrome as _d2jsp", qblock)
        self.assertIn("_d2jsp.d2jsp_quote(", qblock)
        self.assertNotIn("d2jsp", _read(BEACON))

    def test_a_quest_item_is_not_a_trade_and_the_range_is_the_reading(self):
        if NODE is None:
            self.skipTest("node is not on this machine")
        with open(os.path.join(ROOT, "tv", "item_tables.json"), encoding="utf-8") as fh:
            tables = json.load(fh)
        names = set()
        for code in QUEST_CODES:
            names.add(tables["items"][code]["name"])
        for row in tables["uniques"].values():
            if isinstance(row, dict) and row.get("code") in QUEST_CODES and row.get("name"):
                names.add(row["name"])

        def fold(text):
            return " ".join(str(text).replace("\u2019", "'").replace("\u2018", "'").lower().split())

        expected = {fold(n) for n in names}
        expected.update(QUEST_EXTRA)
        body = r"""
var line = d2jspPriceLine({reason:'read', fg:30, n:3, low:10, high:50, readAt:'2026-10-12T20:01:00.000Z'});
var one = d2jspPriceLine({reason:'read', fg:40, n:1, low:40, high:40, readAt:'2026-10-12T20:02:00.000Z'});
var same = d2jspPriceLine({reason:'read', fg:15, n:4, low:15, high:15, readAt:'2026-10-12T20:03:00.000Z'});
var none = d2jspPriceLine({reason:'no prices', fg:null, n:0, low:null, high:null, readAt:'2026-10-12T20:04:00.000Z'});
var blank = d2jspPriceLine(null);
var login = d2jspPriceLine({reason:'need-login', fg:null, n:0, low:null, high:null, readAt:'2026-10-12T20:05:00.000Z'});
process.stdout.write(JSON.stringify({
  list: D2JSP_QUEST,
  cube: d2jspIsQuest('Horadric Cube'),
  stack: d2jspIsQuest('2x Horadric Cube'),
  terror: d2jspIsQuest('Key of Terror'),
  black: d2jspIsQuest('Blackhand Key'),
  gheed: d2jspIsQuest("Gheed's Fortune"),
  eye: d2jspIsQuest("Khalim's Eye"),
  baal: d2jspIsQuest("Baal's Eye"),
  token: d2jspIsQuest('Token of Absolution'),
  keys: d2jspIsQuest('Keys'),
  line: line, one: one, same: same, none: none, blank: blank, login: login
}));
"""
        out = json.loads(_node(self.desk, body))
        self.assertEqual(set(out["list"]), expected)
        self.assertTrue(out["cube"])
        self.assertTrue(out["stack"])
        self.assertTrue(out["eye"])
        self.assertTrue(out["keys"])
        self.assertFalse(out["terror"])
        self.assertFalse(out["black"])
        self.assertFalse(out["gheed"])
        self.assertFalse(out["baal"])
        self.assertFalse(out["token"])
        self.assertIn("10", out["line"])
        self.assertIn("50", out["line"])
        self.assertIn("30", out["line"])
        self.assertNotIn("\u2013", out["one"])
        self.assertIn("40 fg", out["one"])
        self.assertNotIn("\u2013", out["same"])
        self.assertIn("15 fg", out["same"])
        self.assertIn("returned no fg number", out["none"])
        self.assertEqual(out["blank"], "Public price unknown.")
        self.assertIn("Chrome login", out["login"])
        self.assertNotIn("fg,", out["login"])

    def test_a_logged_in_search_prices_only_the_lines_that_name_the_item(self):
        import d2jsp_chrome as desk
        calls = {"urls": [], "cookie": 0}

        def cookie_get():
            calls["cookie"] += 1
            return "sid=SECRETCOOKIE", "ok"

        def no_cookie():
            calls["cookie"] += 1
            return None, "need-login"

        page = "\n".join([
            "Gheeds Fortune gc 106/35/13 - 20fg",
            "Gheeds Fortune gc 108/31/12 - 15fg",
            "Pcomb plain - 10fg x 1",
            "35MF gheeds",
            "Gheed's Fortune 10 fg",
            "Summon Skill Necro + 26 life - 25fg",
        ])

        def transport(method, url, headers, data):
            calls["urls"].append(url)
            self.assertNotIn("SECRETCOOKIE", url)
            self.assertEqual(headers.get("Cookie"), "sid=SECRETCOOKIE")
            return 200, {}, page.encode("utf-8")

        code, out = desk.d2jsp_quote(
            "Gheed's Fortune", "http://evil.example", "evil.example", 17772,
            cookie_get=cookie_get, transport=transport,
        )
        self.assertEqual(code, 403)
        self.assertEqual(out["reason"], "origin")
        self.assertIsNone(out["fg"])
        self.assertEqual(calls["cookie"], 0)
        self.assertEqual(calls["urls"], [])

        code, out = desk.d2jsp_quote(
            "Gheed's Fortune", "http://127.0.0.1:17772", "127.0.0.1:17772", 17772,
            cookie_get=no_cookie, transport=transport,
        )
        self.assertEqual(out["reason"], "need-login")
        self.assertIsNone(out["fg"])
        self.assertEqual(calls["urls"], [])
        self.assertNotIn("SECRETCOOKIE", json.dumps(out))

        code, out = desk.d2jsp_quote(
            "Gheed's Fortune", "http://127.0.0.1:17772", "127.0.0.1:17772", 17772,
            cookie_get=cookie_get, transport=transport,
        )
        self.assertEqual(code, 200)
        self.assertEqual(out["reason"], "read")
        self.assertEqual(out["fg"], 15)
        self.assertEqual(out["low"], 10)
        self.assertEqual(out["high"], 20)
        self.assertEqual(out["n"], 3)
        self.assertEqual(out["board"], 243)
        self.assertEqual(len(calls["urls"]), 1)
        self.assertIn("Gheeds%20Fortune", calls["urls"][0])
        self.assertIn("fid%5B%5D=243", calls["urls"][0])
        self.assertNotIn("SECRETCOOKIE", json.dumps(out))
        self.assertNotIn("Gheeds Fortune gc", json.dumps(out))

    def test_chrome_posts_only_a_priced_board_268_draft_from_this_console(self):
        import d2jsp_chrome as desk
        calls = {"cookie": 0, "open": 0, "urls": []}

        def cookie_get():
            calls["cookie"] += 1
            return "sid=SECRETCOOKIE", "ok"

        def open_login():
            calls["open"] += 1
            return True

        def no_cookie():
            calls["cookie"] += 1
            return None, "need-login"

        code, out = desk.d2jsp_send(
            {"subject": "WTS Grief", "body": "WTS Grief\n30 fg", "forum": 268},
            "https://evil.example", "127.0.0.1:17772", 17772,
            cookie_get=cookie_get, open_login=open_login,
        )
        self.assertEqual(code, 403)
        self.assertEqual(out["reason"], "origin")
        self.assertEqual(calls["cookie"], 0)
        self.assertEqual(calls["open"], 0)

        code, out = desk.d2jsp_send(
            {"subject": "WTS Grief", "body": "WTS Grief\n30 fg", "forum": 271},
            "http://127.0.0.1:17772", "127.0.0.1:17772", 17772,
            cookie_get=cookie_get, open_login=open_login,
        )
        self.assertEqual(out["reason"], "wrong-board")
        self.assertEqual(calls["cookie"], 0)

        code, out = desk.d2jsp_send(
            {"subject": "WTS Grief", "body": "WTS Grief", "forum": 268},
            None, "127.0.0.1:17772", 17772,
            cookie_get=cookie_get, open_login=open_login,
        )
        self.assertEqual(out["reason"], "no-price")
        self.assertEqual(calls["cookie"], 0)

        logged_out = "<p>You are not currently logged in.</p>"
        def transport(method, url, headers, data):
            calls["urls"].append((method, url))
            self.assertNotIn("SECRETCOOKIE", url)
            self.assertEqual(url, desk.COMPOSE_URL)
            return 200, {}, logged_out.encode()

        code, out = desk.d2jsp_send(
            {"subject": "WTS Grief Phase Blade", "body": "WTS Grief Phase Blade\n+damage\n30 fg", "forum": 268},
            "http://127.0.0.1:17772", "127.0.0.1:17772", 17772,
            cookie_get=no_cookie, transport=transport, open_login=open_login,
        )
        self.assertEqual(out["reason"], "need-login")
        self.assertTrue(out["opened"])
        self.assertEqual(calls["urls"], [])
        self.assertNotIn("SECRETCOOKIE", json.dumps(out))

        def transport_logged_out(method, url, headers, data):
            calls["urls"].append(method)
            self.assertEqual(method, "GET")
            return 200, {}, logged_out.encode()

        code, out = desk.d2jsp_send(
            {"subject": "WTS Grief Phase Blade", "body": "WTS Grief Phase Blade\n30 fg", "forum": 268},
            "http://127.0.0.1:17772", "127.0.0.1:17772", 17772,
            cookie_get=cookie_get, transport=transport_logged_out, open_login=open_login,
        )
        self.assertEqual(out["reason"], "need-login")
        self.assertTrue(out["opened"])
        self.assertEqual(calls["urls"], ["GET"])
        self.assertEqual(calls["open"], 2)

        form = (
            '<a href="login.php?mode=logout">out</a>'
            '<input type="hidden" name="form_token" value="abc">'
            '<input name="subject">'
            '<textarea name="message"></textarea>'
            '<input type="submit" name="post" value="Submit">'
        )
        posted = {}

        def transport_ok(method, url, headers, data):
            self.assertEqual(url, desk.COMPOSE_URL)
            self.assertIn("Chrome/", headers.get("User-Agent", ""))
            self.assertNotEqual(headers.get("User-Agent"), "Mozilla/5.0")
            self.assertIn("sid=SECRETCOOKIE", headers.get("Cookie", ""))
            if method == "GET":
                return 200, {}, form.encode()
            posted["body"] = data.decode()
            return 302, {"Location": "https://forums.d2jsp.org/topic.php?t=9&f=268"}, b""

        code, out = desk.d2jsp_send(
            {"subject": "WTS Grief Phase Blade", "body": "WTS Grief Phase Blade\n+damage\n30 fg", "forum": 268},
            "http://localhost:17772", "localhost:17772", 17772,
            cookie_get=cookie_get, transport=transport_ok, open_login=open_login,
        )
        self.assertTrue(out["ok"])
        self.assertEqual(out["reason"], "submitted")
        self.assertIn("form_token=abc", posted["body"])
        self.assertIn("subject=WTS", posted["body"])
        self.assertIn("30+fg", posted["body"])
        self.assertNotIn("SECRETCOOKIE", json.dumps(out))
        self.assertEqual(calls["open"], 2)

        def transport_back(method, url, headers, data):
            return 200, {}, form.encode()

        code, out = desk.d2jsp_send(
            {"subject": "WTS Grief Phase Blade", "body": "WTS Grief Phase Blade\n30 fg", "forum": 268},
            "http://127.0.0.1:17772", "127.0.0.1:17772", 17772,
            cookie_get=cookie_get, transport=transport_back, open_login=open_login,
        )
        self.assertFalse(out["ok"])
        self.assertEqual(out["reason"], "not-posted")

        def transport_down(method, url, headers, data):
            raise OSError("down")

        code, out = desk.d2jsp_send(
            {"subject": "WTS Grief Phase Blade", "body": "WTS Grief Phase Blade\n30 fg", "forum": 268},
            "http://127.0.0.1:17772", "127.0.0.1:17772", 17772,
            cookie_get=cookie_get, transport=transport_down, open_login=open_login,
        )
        self.assertFalse(out["ok"])
        self.assertEqual(out["reason"], "unread")
        self.assertNotIn("submitted", out["reason"])

    def test_the_cookie_header_is_only_the_d2jsp_host(self):
        import d2jsp_chrome as desk
        now = 1_700_000_000
        chrome_now = desk._chrome_now(now)
        rows = [
            ("example.com", "session", b"LEAKED", chrome_now + 10**12),
            (".d2jsp.org", "sid", b"desk-session", chrome_now + 10**12),
            ("forums.d2jsp.org", "old", b"stale", chrome_now - 10),
            ("notd2jsp.org", "sid", b"ALSOLEAKED", chrome_now + 10**12),
        ]
        header, reason = desk.cookie_header_from_rows(
            rows, "unused", now_utc=now, decrypt=lambda blob: blob.decode())
        self.assertEqual(reason, "ok")
        self.assertIn("sid=desk-session", header)
        self.assertNotIn("LEAKED", header)
        self.assertNotIn("ALSOLEAKED", header)
        self.assertNotIn("stale", header)
        self.assertIsNone(desk.decrypt_v10(b"v20not-this-format", "pw"))
        self.assertFalse(desk.console_may_post("https://evil.example", "127.0.0.1:17772", 17772))
        self.assertTrue(desk.console_may_post(None, "127.0.0.1:17772", 17772))

        password = "test-password"
        blob = desk.seal_v10(password, "roundtrip-value")
        if blob is None:
            return
        self.assertEqual(desk.decrypt_v10(blob, password), "roundtrip-value")
        import sqlite3
        import tempfile
        folder = tempfile.mkdtemp(prefix="d2jsp cookie ")
        db = os.path.join(folder, "Cookies")
        try:
            con = sqlite3.connect(db)
            con.execute("create table cookies (host_key text, name text, encrypted_value blob, expires_utc integer)")
            con.execute(
                "insert into cookies values (?,?,?,?)",
                (".d2jsp.org", "sid", blob, chrome_now + 10**12),
            )
            con.commit()
            con.close()
            read = desk._read_rows(db)
            self.assertEqual(len(read), 1)
            self.assertEqual(read[0][0], ".d2jsp.org")
            header, reason = desk.cookie_header_from_rows(read, password, now_utc=now)
            self.assertEqual(reason, "ok")
            self.assertEqual(header, "sid=roundtrip-value")
        finally:
            shutil.rmtree(folder, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
