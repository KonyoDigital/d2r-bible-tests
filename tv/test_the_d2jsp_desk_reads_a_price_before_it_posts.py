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

    def test_a_post_is_one_line_per_mod_from_the_builder_list(self):
        if NODE is None:
            self.skipTest("node is not on this machine")
        pane = _between(self.bible, 'id="tab-d2jsp"', 'id="tab-vault"')
        self.assertIn('id="d2jsp-add"', pane)
        self.assertIn(">Add an item</button>", pane)
        script = pane.split("<script>", 1)[1].split("</script>", 1)[0]
        lines_at = script.index("function gearLines(")
        shown_at = script.index("function shownOf(", lines_at)
        lines_fn = script[lines_at:shown_at]
        self.assertLess(shown_at - lines_at, 2200)
        self.assertIn("_cbLineHtml", lines_fn)
        self.assertIn("_cbAfText", lines_fn)
        self.assertIn("Ethereal", lines_fn)
        file_at = script.index("function fileGear(")
        open_at = script.index("window._d2jspPlannerOpen = function", file_at)
        filed = script[file_at:open_at]
        self.assertLess(open_at - file_at, 1800)
        self.assertIn("d2r_d2jsp_gear", script[script.index("function gearMap("):lines_at])
        self.assertIn("d2jspIsQuest", filed)
        self.assertNotIn("vaultPlannerFile", filed)
        click_at = script.index("document.addEventListener('click'", open_at)
        opener = script[open_at:click_at]
        self.assertLess(click_at - open_at, 2800)
        self.assertIn("_cbHostOpen", opener)
        self.assertIn("desk: 'd2jsp'", opener)
        self.assertNotIn("vaultPlannerFile", opener)
        self.assertNotIn("vaultHandAdd", opener)
        self.assertNotIn("d2r_charBuilds", opener)
        card_at = script.index("function cardHtml(")
        cards_at = script.index("function currentCards(", card_at)
        card = script[card_at:cards_at]
        self.assertLess(cards_at - card_at, 2200)
        self.assertIn("data-d2jsp-options", card)
        self.assertIn("data-d2jsp-draft", card)
        self.assertNotIn("<textarea", card)
        host = self.bible.index("var foot = (st.host.planner)")
        placed = self.bible.index("window._cbHostPlaced", host)
        self.assertLess(placed - host, 600)
        self.assertIn("st.host.desk === 'd2jsp'", self.bible[host:placed])
        self.assertIn("window._d2jspPlateHtml", self.bible[host:placed])
        note = self.bible.index("The same item list and the same mod list as the character builder.")
        pick = self.bible.rindex("function _cbPickHtml", 0, note)
        filt = self.bible.index("function _cbFiltOpts", note)
        self.assertLess(note - pick, 8000)
        self.assertLess(filt - note, 1600)
        self.assertIn("window._d2jspPlannerOn = true", opener)
        self.assertEqual(self.bible.count("window._d2jspPlannerOn"), 5)
        self.assertEqual(self.bible.count("!window._d2jspPlannerOn"), 2)
        modal_at = self.bible.index("function _cbModal(){")
        self.assertEqual(self.bible.count("function _cbModal(){"), 1)
        modal_end = self.bible.index("window._cbModal = _cbModal;", modal_at)
        self.assertLess(modal_end - modal_at, 1400)
        modal = self.bible[modal_at:modal_end]
        self.assertEqual(modal.count("st.host.desk === 'd2jsp'"), 2)
        self.assertIn("getElementById('d2jsp-planner-host')", modal)
        self.assertIn("st.host && (st.host.planner || st.host.desk === 'd2jsp')", modal)
        rel = modal.index("m.style.position = 'relative'")
        back = modal.index("return;", rel)
        place = modal.index("_cbPlace(m)")
        self.assertLess(rel, back)
        self.assertLess(back, place)
        self.assertNotIn("vaultPlannerFile", modal)
        placed_at = self.bible.index("window._cbHostPlaced = function(){")
        placed_end = self.bible.index("window._cbHostEsc = function(){", placed_at)
        self.assertLess(placed_end - placed_at, 500)
        placed_fn = self.bible[placed_at:placed_end]
        self.assertLess(placed_fn.index("st.host.desk === 'd2jsp'"), placed_fn.index("_cbPlace(m)"))
        open_b = self.bible.index("window.openCharBuilder = function(buildId){")
        open_end = self.bible.index("st.open = true", open_b)
        self.assertLess(open_end - open_b, 2000)
        opened = self.bible[open_b:open_end]
        self.assertLess(opened.index("window._d2jspPlannerClose"), opened.index("window._mpPick"))
        body = r"""
var lines = window._d2jspGearLines({
  id: 'grief', eth: true, rolls: {},
  affixes: [{ id: 'vita', rolls: {} }]
});
var draft = d2jspDraft('Grief', 'Phase Blade', lines.join('\n'), 1, 30);
var blocked = d2jspDraft('Grief', 'Phase Blade', lines.join('\n'), 1, 0);
var thunder = window._d2jspGearLines({ id: 'thunder', eth: false, rolls: {}, affixes: [] });
var sale = d2jspDraft("Guardian's Thunder", 'Colossal Jewel',
  thunder.join('\n') + '\nan effect the game&#39;s tables name Gethit-skill but do not describe\n+10% to Lightning Skill Damage',
  1, 1100);
var quest = (typeof d2jspIsQuest === 'function') && d2jspIsQuest('Horadric Cube');
process.stdout.write(JSON.stringify({lines: lines, draft: draft, blocked: blocked, thunder: thunder, sale: sale, quest: quest}));
"""
        stubs = r"""
var document = {
  documentElement: { classList: { contains: function(){ return false; } } },
  getElementById: function(){ return null; },
  addEventListener: function(){},
  createElement: function(){ return { style: {}, hidden: true, querySelector: function(){ return null; }, setAttribute: function(){} }; },
  body: { appendChild: function(){} }
};
var localStorage = { _m: {}, getItem: function(k){ return this._m[k] || null; }, setItem: function(k, v){ this._m[k] = String(v); } };
var location = { hostname: '127.0.0.1' };
var window = { addEventListener: function(){}, LSR: null };
window._cbItem = function(id){
  if (id === 'grief') return ['grief', 'Grief', 'u', 'pblade', 0, 0, [[0, [[340, 400, 'ed']], 0, 'ed%']]];
  if (id === 'thunder') return ['thunder', "Guardian's Thunder", 'u', 'cjw', 75, 0, [
    [13, [[1, 75, 'ltng']], 0, 'dmg-ltng'],
    [0, [], 0, 2, 'Gethit-skill']
  ]];
  return null;
};
window._cbLineHtml = function(line){
  if (line && line[4] === 'Gethit-skill') return 'an effect the game&#39;s tables name Gethit-skill but do not describe';
  if (line && line[3] === 'dmg-ltng') return 'Adds 1-75 lightning damage';
  return '+340-400% Enhanced Damage';
};
window._cbAf = function(id){ return id === 'vita' ? ['vita'] : null; };
window._cbAfText = function(){ return '+36-40 to Life'; };
window._cbShown = function(){ return { name: 'Grief', base: 'Phase Blade' }; };
"""
        out = json.loads(_node(stubs + script, body))
        self.assertEqual(out["lines"], ["+340-400% Enhanced Damage", "+36-40 to Life", "Ethereal"])
        self.assertEqual(out["draft"]["subject"], "Selling Grief Phase Blade")
        self.assertEqual(
            out["draft"]["body"].split("\n"),
            ["Selling Grief Phase Blade", "+340-400% Enhanced Damage", "+36-40 to Life", "Ethereal", "30 fg"],
        )
        self.assertEqual(out["thunder"], ["Adds 1-75 lightning damage"])
        self.assertEqual(out["sale"]["subject"], "Selling Guardian's Thunder Colossal Jewel")
        self.assertEqual(
            out["sale"]["body"].split("\n"),
            [
                "Selling Guardian's Thunder Colossal Jewel",
                "Adds 1-75 lightning damage",
                "+10% to Lightning Skill Damage",
                "1100 fg",
            ],
        )
        self.assertNotIn("but do not describe", out["sale"]["body"])
        self.assertNotIn("Gethit-skill", out["sale"]["body"])
        self.assertNotIn("&#39;", out["sale"]["body"])
        self.assertEqual(out["draft"]["forum"], 268)
        self.assertFalse(out["blocked"]["ok"])
        self.assertEqual(out["blocked"]["reason"], "no price")
        self.assertTrue(out["quest"])

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
        self.assertIn("reason === 'title'", handler)
        self.assertIn("The board title holds 50 characters, so nothing was posted.", handler)
        gate = handler.index("t.getAttribute('data-d2jsp-send') !== '1'")
        preview_ret = handler.index("return;", gate)
        match = handler.index("shown.textContent !== draft.body")
        again_ret = handler.index("return;", match)
        fetch_at = handler.index("/api/d2jsp_send")
        self.assertLess(gate, preview_ret)
        self.assertLess(preview_ret, match)
        self.assertIn("title.textContent !== draft.subject", handler)
        self.assertLess(match, again_ret)
        self.assertLess(again_ret, fetch_at)
        guard = handler.index("if (posting)")
        self.assertLess(again_ret, guard)
        self.assertLess(guard, fetch_at)
        arm = handler.index("posting = true;")
        shown_while_sending = handler.index("showPosting()", arm)
        self.assertLess(guard, arm)
        self.assertLess(arm, shown_while_sending)
        self.assertLess(shown_while_sending, fetch_at)
        self.assertLess(fetch_at, handler.index("showReceipt('confirmed'"))
        self.assertLess(fetch_at, handler.index("settle();"))
        posting_fn = self.bible.index("function showPosting(")
        self.assertEqual(self.bible.count("function showPosting("), 1)
        posting_box = self.bible[posting_fn:self.bible.index("/* ⟦D2JSP PLANNER ESC BEGIN⟧", posting_fn)]
        self.assertIn("Asking Chrome on this machine to post on board 268.", posting_box)
        self.assertIn("data-d2jsp-draft-close", posting_box)
        self.assertNotIn("data-d2jsp-send", posting_box)
        self.assertNotIn("/api/d2jsp_send", posting_box)
        draft_fn = self.bible.index("function openDraft(")
        self.assertEqual(self.bible.count("function openDraft("), 1)
        draft_end = self.bible.index("function showReceipt(", draft_fn)
        self.assertLess(draft_end - draft_fn, 1400)
        shown_box = self.bible[draft_fn:draft_end]
        self.assertIn("data-d2jsp-draft-view", shown_box)
        self.assertIn("data-d2jsp-draft-subject", shown_box)
        self.assertIn('data-d2jsp-send="1"', shown_box)
        self.assertIn("draft.forum", shown_box)
        self.assertNotIn("/api/d2jsp_send", shown_box)
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
            calls["urls"].append((method, url, data))
            self.assertNotIn("SECRETCOOKIE", url)
            self.assertNotIn("SECRETCOOKIE", data.decode("utf-8") if isinstance(data, bytes) else str(data or ""))
            self.assertEqual(headers.get("Cookie"), "sid=SECRETCOOKIE")
            return 200, {}, page.encode("utf-8")

        def chrome_fetch(item_name, cookie):
            raise AssertionError("a priced page does not need a second browser")

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
            cookie_get=cookie_get, transport=transport, chrome_fetch=chrome_fetch,
        )
        self.assertEqual(code, 200)
        self.assertEqual(out["reason"], "read")
        self.assertEqual(out["fg"], 15)
        self.assertEqual(out["low"], 10)
        self.assertEqual(out["high"], 20)
        self.assertEqual(out["n"], 3)
        self.assertEqual(out["board"], 243)
        self.assertEqual(len(calls["urls"]), 1)
        self.assertEqual(calls["urls"][0][0], "POST")
        self.assertIn("search.php?c=7&f=243&t=0", calls["urls"][0][1])
        self.assertIn(b"stext=Gheeds+Fortune", calls["urls"][0][2])
        self.assertNotIn("SECRETCOOKIE", json.dumps(out))
        self.assertNotIn("Gheeds Fortune gc", json.dumps(out))

    def test_a_challenge_page_is_read_through_a_scratch_chrome(self):
        import d2jsp_chrome as desk
        page = "\n".join([
            "Gheeds Fortune gc 106/35/13 - 20fg",
            "Gheeds Fortune gc 108/31/12 - 15fg",
            "Pcomb plain - 10fg x 1",
            "35MF gheeds",
            "Gheed's Fortune 10 fg",
            "Summon Skill Necro + 26 life - 25fg",
        ])
        seen = []

        def transport(method, url, headers, data):
            self.assertEqual(method, "POST")
            self.assertIn("search.php?c=7&f=243", url)
            return 403, {}, b"<title>Just a moment...</title>"

        def chrome_fetch(item_name, cookie):
            seen.append(item_name)
            self.assertIn("SECRETCOOKIE", cookie)
            self.assertNotIn("SECRETCOOKIE", item_name)
            return page

        code, out = desk.d2jsp_quote(
            "Gheed's Fortune", "http://127.0.0.1:17772", "127.0.0.1:17772", 17772,
            cookie_get=lambda: ("sid=SECRETCOOKIE", "ok"),
            transport=transport, chrome_fetch=chrome_fetch,
        )
        self.assertEqual(code, 200)
        self.assertEqual(seen, ["Gheed's Fortune"])
        self.assertEqual(out["reason"], "read")
        self.assertEqual(out["fg"], 15)
        self.assertEqual(out["low"], 10)
        self.assertEqual(out["high"], 20)
        self.assertEqual(out["n"], 3)
        self.assertEqual(out["board"], 243)
        self.assertNotIn("SECRETCOOKIE", json.dumps(out))

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

        code, out = desk.d2jsp_send(
            {"subject": "ISO Grief", "body": "ISO Grief\n30 fg", "forum": 268},
            None, "127.0.0.1:17772", 17772,
            cookie_get=cookie_get, open_login=open_login,
        )
        self.assertEqual(out["reason"], "no-price")
        self.assertEqual(calls["cookie"], 0)

        def refuse_chrome(subject, text, cookie):
            raise AssertionError("a title past 50 characters must not open Chrome")

        code, out = desk.d2jsp_send(
            {"subject": "WTS " + ("A" * 47), "body": "WTS\n30 fg", "forum": 268},
            "http://127.0.0.1:17772", "127.0.0.1:17772", 17772,
            cookie_get=cookie_get, open_login=open_login, chrome_post=refuse_chrome,
        )
        self.assertFalse(out["ok"])
        self.assertEqual(out["reason"], "title")
        self.assertEqual(len("WTS " + ("A" * 47)), 51)

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
            {"subject": "Selling Grief Phase Blade", "body": "Selling Grief Phase Blade\n+damage\n30 fg", "forum": 268},
            "http://localhost:17772", "localhost:17772", 17772,
            cookie_get=cookie_get, transport=transport_ok, open_login=open_login,
        )
        self.assertTrue(out["ok"])
        self.assertEqual(out["reason"], "submitted")
        self.assertIn("form_token=abc", posted["body"])
        self.assertIn("subject=Selling", posted["body"])
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

    def test_a_challenge_page_is_posted_through_a_scratch_chrome(self):
        import d2jsp_chrome as desk
        seen = {}

        def transport(method, url, headers, data):
            self.assertEqual(method, "GET")
            self.assertEqual(url, desk.COMPOSE_URL)
            return 200, {}, b"<title>Just a moment...</title>"

        def chrome_post(subject, text, cookie):
            seen["subject"] = subject
            seen["text"] = text
            self.assertIn("SECRETCOOKIE", cookie)
            self.assertNotIn("SECRETCOOKIE", subject)
            self.assertNotIn("SECRETCOOKIE", text)
            return "https://forums.d2jsp.org/topic.php?t=9&f=268"

        code, out = desk.d2jsp_send(
            {"subject": "WTS Grief Phase Blade", "body": "WTS Grief Phase Blade\n30 fg", "forum": 268},
            "http://127.0.0.1:17772", "127.0.0.1:17772", 17772,
            cookie_get=lambda: ("sid=SECRETCOOKIE", "ok"),
            transport=transport, open_login=lambda: True, chrome_post=chrome_post,
        )
        self.assertEqual(code, 200)
        self.assertTrue(out["ok"])
        self.assertEqual(out["reason"], "submitted")
        self.assertEqual(out["topic"], "https://forums.d2jsp.org/topic.php?t=9&f=268")
        self.assertEqual(seen["subject"], "WTS Grief Phase Blade")
        self.assertIn("30 fg", seen["text"])
        self.assertNotIn("SECRETCOOKIE", json.dumps(out))

        def chrome_post_login(subject, text, cookie):
            return "https://forums.d2jsp.org/login.php?redirect=post"

        code, out = desk.d2jsp_send(
            {"subject": "WTS Grief Phase Blade", "body": "WTS Grief Phase Blade\n30 fg", "forum": 268},
            "http://127.0.0.1:17772", "127.0.0.1:17772", 17772,
            cookie_get=lambda: ("sid=SECRETCOOKIE", "ok"),
            transport=transport, open_login=lambda: False, chrome_post=chrome_post_login,
        )
        self.assertFalse(out["ok"])
        self.assertEqual(out["reason"], "need-login")
        self.assertNotIn("SECRETCOOKIE", json.dumps(out))

        def chrome_post_stay(subject, text, cookie):
            return "https://forums.d2jsp.org/post.php?mode=post&f=268"

        code, out = desk.d2jsp_send(
            {"subject": "WTS Grief Phase Blade", "body": "WTS Grief Phase Blade\n30 fg", "forum": 268},
            "http://127.0.0.1:17772", "127.0.0.1:17772", 17772,
            cookie_get=lambda: ("sid=SECRETCOOKIE", "ok"),
            transport=transport, open_login=lambda: False, chrome_post=chrome_post_stay,
        )
        self.assertFalse(out["ok"])
        self.assertEqual(out["reason"], "not-posted")

        with open(os.path.join(os.path.dirname(desk.__file__), "d2jsp_chrome.py"), encoding="utf-8") as handle:
            src = handle.read()
        post_fn = src.index("def _chrome_post(")
        post_end = src.index("def d2jsp_quote(", post_fn)
        self.assertLess(post_end - post_fn, 7200)
        box = src[post_fn:post_end]
        self.assertIn("--user-data-dir=%s", box)
        self.assertIn("forum.php?f=", box)
        self.assertIn("New Trade", box)
        self.assertIn('textarea[name="Post"]', box)
        self.assertIn('input[name="ttitle"]', box)
        self.assertIn('input[name="submit"]', box)
        self.assertIn("Selling Item", box)
        self.assertIn("subject.length>50", box)
        self.assertIn("sItalic", box)
        self.assertIn("btn.click()", box)
        self.assertIn("_chrome_bin()", box)
        self.assertNotIn('textarea[name="message"]', box)
        self.assertNotIn("mode=post", box)
        self.assertNotIn("form.submit", box)
        self.assertNotIn("9222", box)
        door = src.index("def _send_through_chrome(")
        door_end = src.index("def d2jsp_send(", door)
        gate = src[door:door_end]
        self.assertIn("_public_topic(landed)", gate)
        self.assertLess(gate.index("_public_topic(landed)"), gate.index('"submitted"'))
        self.assertIn('"topic": public', gate)
        send = src[src.index("def d2jsp_send("):]
        self.assertIn("_send_through_chrome(", send)
        self.assertLess(send.index("transport is None and chrome_post is not False"), send.index('fetch("GET", COMPOSE_URL'))
        self.assertLess(send.index("_challenge_page(raw_text)"), send.index('reason": "not-posted"'))
        receipt = self.bible.index("function showReceipt(")
        receipt_end = self.bible.index("function closeDraft(", receipt)
        self.assertLess(receipt_end - receipt, 1400)
        panel = self.bible[receipt:receipt_end]
        self.assertIn("Confirmed", panel)
        self.assertIn("Not sent", panel)
        self.assertIn("https://forums.d2jsp.org/topic.php", panel)
        self.assertNotIn("window.open", panel)

        def live_post(subject, text, cookie):
            self.assertIn("SECRETCOOKIE", cookie)
            return "https://forums.d2jsp.org/topic.php?t=44&f=268#top"

        code, out = desk.d2jsp_send(
            {"subject": "WTS Grief Phase Blade", "body": "WTS Grief Phase Blade\n30 fg", "forum": 268},
            "http://127.0.0.1:17772", "127.0.0.1:17772", 17772,
            cookie_get=lambda: ("sid=SECRETCOOKIE", "ok"),
            open_login=lambda: False, chrome_post=live_post,
        )
        self.assertTrue(out["ok"])
        self.assertEqual(out["reason"], "submitted")
        self.assertEqual(out["topic"], "https://forums.d2jsp.org/topic.php?t=44&f=268")
        self.assertNotIn("SECRETCOOKIE", json.dumps(out))

        def evil_post(subject, text, cookie):
            return "https://evil.example/topic.php?t=1"

        code, out = desk.d2jsp_send(
            {"subject": "WTS Grief Phase Blade", "body": "WTS Grief Phase Blade\n30 fg", "forum": 268},
            "http://127.0.0.1:17772", "127.0.0.1:17772", 17772,
            cookie_get=lambda: ("sid=SECRETCOOKIE", "ok"),
            open_login=lambda: False, chrome_post=evil_post,
        )
        self.assertFalse(out["ok"])
        self.assertEqual(out["reason"], "not-posted")
        self.assertNotIn("topic", out)

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

    def test_a_chrome_cookie_opens_only_when_its_host_digest_matches(self):
        import hashlib
        import d2jsp_chrome as desk
        host = ".d2jsp.org"
        other = "forums.d2jsp.org"
        prefix = hashlib.sha256(host.encode("utf-8")).digest()
        self.assertEqual(len(prefix), 32)
        self.assertEqual(desk._cookie_text(prefix + b"desk-session", host), "desk-session")
        self.assertIsNone(desk._cookie_text(prefix + b"bad;value", host))
        self.assertEqual(desk._cookie_text(b"roundtrip-value", host), "roundtrip-value")
        password = "test-password"
        blob = desk._seal_v10_raw(password, prefix + b"desk-session")
        if blob is None:
            return
        self.assertEqual(desk.decrypt_v10(blob, password, host), "desk-session")
        self.assertIsNone(desk.decrypt_v10(blob, password, other))
        self.assertIsNone(desk.decrypt_v10(blob, password))
        wrong = desk._seal_v10_raw(password, hashlib.sha256(other.encode("utf-8")).digest() + b"other-session")
        now = 1_700_000_000
        chrome_now = desk._chrome_now(now)
        header, reason = desk.cookie_header_from_rows(
            [(host, "sid", blob, chrome_now + 10**12)],
            password, now_utc=now,
        )
        self.assertEqual(reason, "ok")
        self.assertEqual(header, "sid=desk-session")
        missed, missed_reason = desk.cookie_header_from_rows(
            [(host, "sid", wrong, chrome_now + 10**12)],
            password, now_utc=now,
        )
        self.assertIsNone(missed)
        self.assertEqual(missed_reason, "chrome-unread")

    def test_a_linux_chrome_cookie_opens_with_one_round(self):
        import sqlite3
        import tempfile
        import d2jsp_chrome as desk
        now = 1_700_000_000
        chrome_now = desk._chrome_now(now)
        blob = desk._seal_v10_raw("peanuts", b"desk-session", rounds=1)
        if blob is None:
            return
        self.assertEqual(desk.decrypt_v10(blob, "peanuts", rounds=1), "desk-session")
        self.assertIsNone(desk.decrypt_v10(blob, "peanuts"))
        self.assertIn("X11; Linux x86_64", desk.chrome_user_agent(platform="linux", version="120.0.0.0"))
        self.assertIn("Macintosh", desk.chrome_user_agent(platform="darwin", version="120.0.0.0"))
        self.assertEqual(
            desk._chrome_bin(platform="linux", which=lambda name: "/usr/bin/google-chrome" if name == "google-chrome" else None),
            "/usr/bin/google-chrome",
        )
        self.assertIsNone(desk._chrome_bin(platform="linux", which=lambda name: None))

        class _Proc(object):
            def __init__(self, code, out):
                self.returncode = code
                self.stdout = out

        words = desk._linux_chrome_passwords(
            run=lambda *args, **kwargs: _Proc(0, b"keyring-secret\n"),
            tool="/usr/bin/secret-tool",
        )
        self.assertEqual(words[0], "keyring-secret")
        self.assertEqual(words[-1], "peanuts")
        only = desk._linux_chrome_passwords(
            run=lambda *args, **kwargs: _Proc(1, b""),
            tool="/usr/bin/secret-tool",
        )
        self.assertEqual(only, ["peanuts"])
        live = desk.live_cookie_header
        self.assertIn("linux", live.__code__.co_consts)

        folder = tempfile.mkdtemp(prefix="d2jsp-linux-")
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
            header, reason = desk._linux_cookie_header(
                now_utc=now, paths=[db], passwords=["nope", "peanuts"],
            )
            self.assertEqual(reason, "ok")
            self.assertEqual(header, "sid=desk-session")
            missed, missed_reason = desk._linux_cookie_header(
                now_utc=now, paths=[db], passwords=["nope"],
            )
            self.assertIsNone(missed)
            self.assertEqual(missed_reason, "chrome-unread")
        finally:
            shutil.rmtree(folder, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
