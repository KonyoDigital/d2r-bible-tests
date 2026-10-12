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

    def test_the_room_lists_the_vault_and_posts_through_chrome(self):
        pane = _between(self.bible, 'id="tab-d2jsp"', 'id="tab-vault"')
        self.assertNotIn("Copy the bridge", pane)
        self.assertNotIn("d2jsp-bridge", pane)
        self.assertNotIn("cannot save the file", pane)
        self.assertNotIn("Install the bridge", pane)
        self.assertNotIn("Tag for trade", pane)
        room = pane.split("<script>", 1)[0]
        self.assertNotIn("<textarea", room)
        end = self.bible.index("/* ⟦D2JSP DESK END⟧ */")
        names = self.bible.index("function names(){", end)
        self.assertIn("d2r_muleAssign", self.bible[names:names + 700])
        self.assertNotIn("typeof assign", self.bible[names:names + 700])
        post = self.bible.index("t.getAttribute('data-d2jsp-post')")
        handler = self.bible[post:self.bible.index("document.addEventListener('input'", post)]
        self.assertIn("/api/d2jsp_send", handler)
        self.assertNotIn("createObjectURL", handler)
        self.assertNotIn("window.open", handler)
        self.assertNotIn("clipboard", handler)
        self.assertNotIn("d2jspBridgeSource()", handler)
        self.assertIn("nothing was posted", handler)
        app = _read(os.path.join(HERE, "control_app.py"))
        route = app.index('if path == "/api/d2jsp_send"')
        self.assertIn("d2jsp_chrome", app[route:route + 500])
        self.assertNotIn("d2jsp", _read(BEACON))

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

        try:
            from hashlib import pbkdf2_hmac
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        except Exception:
            return
        password = "test-password"
        key = pbkdf2_hmac("sha1", password.encode(), b"saltysalt", 1003, 16)
        plain = b"roundtrip-value"
        pad = 16 - (len(plain) % 16)
        block = plain + bytes([pad]) * pad
        enc = Cipher(algorithms.AES(key), modes.CBC(b" " * 16)).encryptor()
        blob = b"v10" + enc.update(block) + enc.finalize()
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
