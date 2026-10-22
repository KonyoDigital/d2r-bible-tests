# -*- coding: utf-8 -*-
"""#106 (REG-2500) - A POST THE BOARD MAY ALREADY HOLD IS NEVER SHOWN AS UNSENT.

The D2JSP room has two send paths: one item (the Post button on a card) and the list (Post the list). Each kept
its own copy of the reason map, and both fell back to "The board did not confirm the post, so nothing was
posted." for every reason they did not name. The console now answers MAYBE-SENT when the submit was clicked and
no receipt came back, and a send lock answers busy. Shown as "Not sent ... nothing was posted", a post that may
be live invites the second click, and the second click is the duplicate topic (GrokBot's two live Post attempts
read as failures).

This law runs the room's own code in node, never a browser:
  * sendWords (cut between its markers) gives every reason in the console's contract its own words. A maybe is
    headed "Maybe sent", links the board so he can look, and never says nothing was posted. An answer the page
    does not know is a maybe, never a no.
  * Both send paths are driven end to end through the room's click handler with a stubbed /api/d2jsp_send: the
    receipt they paint is read back, so a path that kept its own map goes red.
  * AN ANSWER THAT NEVER ARRIVES IS A MAYBE TOO. Once the request has left the page the console may already have
    clicked submit, and its re-send record lives only in that process (a restart forgets it). So a dropped
    connection (fetch rejects: the console restarted or crashed mid-send) and an answer that is not JSON (a 5xx
    page) are headed "Maybe sent" and link the board, on both paths. Only a 404 with no contract reason proves the
    send never ran (this console has no post route), and only that one says nothing was posted.

THE CONTRACT below is the list in T1's brief (tv/d2jsp_chrome.py). After T1 merges, the integrator adds one
assertion that it equals d2jsp_chrome.SEND_REASONS.
"""
from __future__ import annotations

import json
import os
import re
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

CONTRACT = (
    "submitted", "already-posted", "maybe-sent", "maybe-sent-recently", "busy", "not-posted", "unread",
    "chrome-start", "chrome-unread", "need-login", "form-unknown", "wrong-board", "no-price", "title", "long",
    "origin",
)
NO = re.compile(r"nothing (?:new )?was posted|not posted|was not sent", re.I)


def _read():
    with open(BIBLE, encoding="utf-8") as fh:
        return fh.read()


def _between(src, start, end):
    i = src.index(start)
    j = src.index(end, i + len(start))
    return src[i + len(start):j]


def _node(prog):
    r = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("node failed: " + (r.stderr or r.stdout)[-2500:])
    return json.loads(r.stdout.strip().splitlines()[-1])


# A fake page the room's script runs in: its own listeners are captured, the draft host keeps what is painted.
FAKES = r"""
var LISTEN = { click: [], input: [], keydown: [] };
function Node(id){ this.id = id; this.attrs = {}; this.hidden = true; this._html = ''; this.textContent = ''; this.title = ''; }
Node.prototype.setAttribute = function(k, v){ this.attrs[k] = String(v); };
Node.prototype.getAttribute = function(k){ return Object.prototype.hasOwnProperty.call(this.attrs, k) ? this.attrs[k] : null; };
Node.prototype.removeAttribute = function(k){ delete this.attrs[k]; };
Node.prototype.querySelector = function(){ return { focus: function(){} }; };
Node.prototype.querySelectorAll = function(){ return []; };
Node.prototype.appendChild = function(){};
Object.defineProperty(Node.prototype, 'innerHTML', { get: function(){ return this._html; }, set: function(v){ this._html = String(v); } });
var list = new Node('d2jsp-list'), statusEl = new Node('d2jsp-status'), lamp = new Node('d2jsp-lamp');
var host = new Node('d2jsp-draft-host'), board = new Node('d2jsp-board'), card = new Node('d2jsp-card');
var VIEW = { textContent: '' }, SUBJECT = { textContent: '' };
var document = {
  documentElement: { classList: { contains: function(){ return false; } } },
  getElementById: function(id){
    return ({ 'd2jsp-list': list, 'd2jsp-status': statusEl, 'd2jsp-lamp': lamp, 'd2jsp-draft-host': host,
              'd2jsp-board': board, 'd2jsp-card': card })[id] || null;
  },
  querySelector: function(sel){
    if (sel === '#d2jsp-draft-host [data-d2jsp-draft-view]') return VIEW;
    if (sel === '#d2jsp-draft-host [data-d2jsp-draft-subject]') return SUBJECT;
    return null;
  },
  querySelectorAll: function(){ return []; },
  addEventListener: function(type, fn){ if (LISTEN[type]) LISTEN[type].push(fn); },
  createElement: function(){ return new Node(''); },
  body: { appendChild: function(){} }
};
var RAW = {};
var localStorage = { getItem: function(k){ return Object.prototype.hasOwnProperty.call(RAW, k) ? RAW[k] : null; },
                     setItem: function(k, v){ RAW[k] = String(v); }, removeItem: function(k){ delete RAW[k]; } };
var location = { hostname: '127.0.0.1' };
var MULE = JSON.stringify({ 'Grief': 'm1' });
var window = { addEventListener: function(){}, LSR: { getItem: function(k){ return k === 'd2r_muleAssign' ? MULE : null; } } };
var ANSWER = null, SENT = [], MODE = '';
function fetch(url, opts){
  var body = null;
  if (String(url) === '/api/d2jsp_send') {
    SENT.push(JSON.parse(opts.body));
    // the request reached the console; what comes back is the transport the scenario names
    if (MODE === 'reset') return Promise.reject(new TypeError('Failed to fetch'));
    if (MODE === 'html500') return Promise.resolve({ status: 500, json: function(){ return Promise.reject(new SyntaxError('Unexpected token <')); } });
    if (MODE === 'route404') return Promise.resolve({ status: 404, json: function(){ return Promise.resolve({ ok: false, msg: 'not found' }); } });
    body = ANSWER;
  }
  else if (String(url).indexOf('d2jsp_login') >= 0) body = { state: 'unknown' };
  else body = { fg: null, reason: 'no prices', n: 0 };
  return Promise.resolve({ status: 200, json: function(){ return Promise.resolve(body); } });
}
function flush(){ return new Promise(function(r){ setTimeout(r, 0); }); }
function button(attrs, selfSel){
  var b = { getAttribute: function(k){ return Object.prototype.hasOwnProperty.call(attrs, k) ? attrs[k] : null; } };
  b.closest = function(sel){ return (sel === '#tab-d2jsp' || selfSel.indexOf(sel) >= 0) ? b : null; };
  return b;
}
"""

SCENARIO = r"""
RAW['d2r_d2jsp_fg'] = JSON.stringify({ 'Grief': '55' });
var shown = d2jspDraft('Grief', '', '', 1, 55);
async function one(answer){
  ANSWER = answer; host._html = ''; statusEl.textContent = '';
  VIEW.textContent = shown.body; SUBJECT.textContent = shown.subject;
  LISTEN.click[0]({ target: button({ 'data-d2jsp-post': 'Grief', 'data-d2jsp-send': '1' }, []), preventDefault: function(){} });
  for (var i = 0; i < 6; i++) await flush();
  return { receipt: host._html, status: statusEl.textContent };
}
async function shop(answer){
  ANSWER = answer; host._html = ''; statusEl.textContent = '';
  var draft = d2jspShopDraft([{ name: 'Grief', base: '', mods: '', copies: 1, fg: 55, sold: false }]);
  VIEW.textContent = draft.body; SUBJECT.textContent = draft.subject;
  LISTEN.click[0]({ target: button({ 'data-d2jsp-shop': '1', 'data-d2jsp-send': '1' }, ['[data-d2jsp-shop]']), preventDefault: function(){} });
  for (var i = 0; i < 6; i++) await flush();
  return { receipt: host._html, status: statusEl.textContent };
}
(async function(){
  var out = { reasons: D2JSP_SEND_REASONS, words: {}, sent: 0 };
  var fixture = {
    'submitted': { ok: true, reason: 'submitted', topic: 'https://forums.d2jsp.org/topic.php?t=9&f=268' },
    'already-posted': { ok: false, reason: 'already-posted', topic: 'https://forums.d2jsp.org/topic.php?t=9&f=268', at: '2026-10-22 13:40' },
    'maybe-sent': { ok: false, reason: 'maybe-sent', board: 268, at: '2026-10-22 13:41' },
    'maybe-sent-recently': { ok: false, reason: 'maybe-sent-recently', at: '2026-10-22 13:42' },
    'chrome-start': { ok: false, reason: 'chrome-start', why: 'no Chrome binary' },
    'need-login': { ok: false, reason: 'need-login', opened: true }
  };
  D2JSP_SEND_REASONS.concat(['gremlin', '']).forEach(function(r){
    var j = fixture[r] || { ok: false, reason: r };
    out.words[r] = sendWords(j, 268, false);
  });
  out.ladderMaybe = sendWords({ ok: false, reason: 'maybe-sent', board: 271 }, 271, false);
  out.updating = sendWords({ ok: false, reason: 'not-posted' }, 268, true);
  out.oneMaybe = await one(fixture['maybe-sent']);
  out.oneRecent = await one(fixture['maybe-sent-recently']);
  out.oneBusy = await one({ ok: false, reason: 'busy' });
  out.oneNot = await one({ ok: false, reason: 'not-posted' });
  out.oneOk = await one(fixture['submitted']);
  out.shopMaybe = await shop(fixture['maybe-sent']);
  out.shopAlready = await shop(fixture['already-posted']);
  out.shopUnknown = await shop({ ok: false, reason: 'gremlin' });
  out.topicSaved = RAW['d2r_d2jsp_topic'] || '';
  // the transport: an answer that never arrives, one that is not JSON, and a console with no post route
  for (var mi = 0, modes = ['reset', 'html500', 'route404']; mi < modes.length; mi++) {
    MODE = modes[mi];
    out['one_' + MODE] = await one(null);
    out['shop_' + MODE] = await shop(null);
    MODE = '';
  }
  out.lost271 = answerWords(0, undefined, 271, false);
  out.unread502 = answerWords(502, null, 268, false);
  out.noRoute = answerWords(404, null, 268, false);
  out.maybeOn404 = answerWords(404, { ok: false, reason: 'maybe-sent', board: 268, at: 'x' }, 268, false);
  out.sent = SENT.length;
  process.stdout.write(JSON.stringify(out));
})().catch(function(e){ process.stderr.write(String(e && e.stack || e)); process.exit(1); });
"""


@unittest.skipUnless(NODE, "node is required to run the room's own code")
class AMaybeSentPostIsNeverShownAsUnsent(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.src = _read()
        pane = _between(cls.src, 'id="tab-d2jsp"', 'id="tab-vault"')
        cls.script = pane.split("<script>", 1)[1].split("</script>", 1)[0]
        cls.words_fn = _between(cls.src, "/* ⟦D2JSP SEND WORDS BEGIN⟧ */", "/* ⟦D2JSP SEND WORDS END⟧ */")
        # the room's script runs whole (its desk block is top level); sendWords is cut out again so the scenario can
        # read its answers directly, beside the click handler that uses the same function
        cls.o = _node(FAKES + cls.script + "\n" + cls.words_fn + "\n" + SCENARIO)

    def test_the_room_names_the_whole_contract(self):
        self.assertEqual(tuple(self.o["reasons"]), CONTRACT,
                         "the room's list of console answers is not the console's contract")
        w = self.o["words"]
        texts = {}
        for r in CONTRACT:
            self.assertIn(r, w, r)
            self.assertTrue(w[r].get("text"), "%s has no words" % r)
            self.assertIn(w[r]["kind"], ("confirmed", "maybe", "missed"), r)
            texts.setdefault(w[r]["text"], []).append(r)
        shared = {t: rs for t, rs in texts.items() if len(rs) > 1}
        self.assertEqual(shared, {}, "two contract reasons share one sentence, so one of them has no words of its own")
        generic = "The board did not confirm the post, so nothing was posted."
        self.assertEqual([r for r in CONTRACT if w[r]["text"] == generic], ["not-posted"],
                         "the old fallback sentence answers a reason that is not a plain not-posted")

    def test_a_maybe_is_never_called_unsent_and_links_the_board(self):
        w = self.o["words"]
        for r in ("maybe-sent", "maybe-sent-recently"):
            self.assertEqual(w[r]["kind"], "maybe", r)
            self.assertIsNone(NO.search(w[r]["text"]), "%s says it was not posted: %r" % (r, w[r]["text"]))
            self.assertIn("may", w[r]["text"])
            self.assertIn("Check board 268", w[r]["text"])
            self.assertEqual(w[r]["link"], "https://forums.d2jsp.org/forum.php?f=268", r)
        self.assertIn("13:41", w["maybe-sent"]["text"], "the console's time of the send is not shown")
        self.assertEqual(self.o["ladderMaybe"]["link"], "https://forums.d2jsp.org/forum.php?f=271")
        for r in ("gremlin", ""):
            self.assertEqual(w[r]["kind"], "maybe", "an answer the page does not know is called a no: %r" % r)
            self.assertIsNone(NO.search(w[r]["text"]), r)

    def test_each_reason_says_what_happened(self):
        w = self.o["words"]
        self.assertEqual(w["submitted"]["kind"], "confirmed")
        self.assertEqual(w["already-posted"]["kind"], "confirmed")
        self.assertEqual(w["already-posted"]["topic"], "https://forums.d2jsp.org/topic.php?t=9&f=268")
        self.assertIn("posted nothing new", w["already-posted"]["text"])
        self.assertIn("This click started no second post.", w["busy"]["text"])
        self.assertIsNone(NO.search(w["busy"]["text"]), "busy says nothing was posted while another send runs")
        self.assertIn("before the post was submitted", w["unread"]["text"])
        self.assertIn("did not start", w["chrome-start"]["text"])
        self.assertIn("no Chrome binary", w["chrome-start"]["text"])
        self.assertIn("login page is open", w["need-login"]["text"])
        self.assertEqual(w["title"]["text"], "The board title holds 50 characters, so nothing was posted.")
        self.assertIn("own page", w["origin"]["text"])
        self.assertEqual(self.o["updating"]["text"], "The saved topic could not be updated, so nothing new was posted.")
        for r in ("not-posted", "unread", "chrome-start", "chrome-unread", "need-login", "form-unknown",
                  "wrong-board", "no-price", "title", "long", "origin", "busy"):
            self.assertEqual(w[r]["kind"], "missed", r)

    def test_the_one_item_path_paints_the_contract(self):
        m = self.o["oneMaybe"]
        self.assertIn(">Maybe sent<", m["receipt"])
        self.assertIn("https://forums.d2jsp.org/forum.php?f=268", m["receipt"])
        self.assertIsNone(NO.search(m["receipt"]), "the one-item receipt calls a maybe unsent")
        self.assertIsNone(NO.search(m["status"]))
        self.assertIn(">Maybe sent<", self.o["oneRecent"]["receipt"])
        self.assertIn("started no second post", self.o["oneBusy"]["receipt"])
        self.assertIn(">Not sent<", self.o["oneNot"]["receipt"])
        self.assertIn("nothing was posted", self.o["oneNot"]["receipt"])
        self.assertIn(">Confirmed<", self.o["oneOk"]["receipt"])
        self.assertIn("topic.php?t=9&amp;f=268", self.o["oneOk"]["receipt"])

    def test_the_list_path_paints_the_same_contract(self):
        m = self.o["shopMaybe"]
        self.assertIn(">Maybe sent<", m["receipt"], "the list path kept its own reason map")
        self.assertIn("https://forums.d2jsp.org/forum.php?f=268", m["receipt"])
        self.assertIsNone(NO.search(m["receipt"]))
        a = self.o["shopAlready"]
        self.assertIn(">Confirmed<", a["receipt"])
        self.assertEqual(self.o["topicSaved"], "https://forums.d2jsp.org/topic.php?t=9&f=268",
                         "an already-posted list topic is not kept, so the next list post starts another")
        u = self.o["shopUnknown"]
        self.assertIn(">Maybe sent<", u["receipt"])
        self.assertIsNone(NO.search(u["receipt"]))
        self.assertEqual(self.o["sent"], 14, "every click reached the stubbed console exactly once")

    def test_an_answer_that_never_arrives_is_a_maybe_on_both_paths(self):
        for path in ("one", "shop"):
            for mode in ("reset", "html500"):
                r = self.o["%s_%s" % (path, mode)]
                self.assertIn(">Maybe sent<", r["receipt"],
                              "%s path: a %s after the request left is headed Not sent" % (path, mode))
                self.assertIn("https://forums.d2jsp.org/forum.php?f=268", r["receipt"], "%s %s" % (path, mode))
                self.assertIsNone(NO.search(r["receipt"]), "%s path: a %s says nothing was posted" % (path, mode))
                self.assertIsNone(NO.search(r["status"]), "%s %s" % (path, mode))
                self.assertIn("Check board 268 before you post again.", r["status"])
            self.assertIn("did not answer", self.o["%s_reset" % path]["status"])
            self.assertIn("HTTP 500", self.o["%s_html500" % path]["status"])
            gone = self.o["%s_route404" % path]
            self.assertIn(">Not sent<", gone["receipt"], "%s path: a console with no post route is a maybe" % path)
            self.assertIn("no post route", gone["receipt"])
        self.assertEqual(self.o["lost271"]["kind"], "maybe")
        self.assertEqual(self.o["lost271"]["link"], "https://forums.d2jsp.org/forum.php?f=271")
        self.assertIn("Check board 271", self.o["lost271"]["text"])
        self.assertEqual(self.o["unread502"]["kind"], "maybe")
        self.assertIn("HTTP 502", self.o["unread502"]["text"])
        self.assertEqual(self.o["noRoute"]["kind"], "missed")
        self.assertEqual(self.o["maybeOn404"]["kind"], "maybe", "a contract reason did not speak for itself")

    def test_one_map_serves_both_paths(self):
        handler = self.src[self.src.index("t.getAttribute('data-d2jsp-post')"):self.src.index("function draftHost()")]
        post = self.src[self.src.index("function postDraft("):self.src.index("window.addEventListener('message'")]
        self.assertIn("answerWords(got.code, got.j, draft.forum, false)", handler)
        self.assertIn("answerWords(got.code, got.j, draft.forum, !!payload.topic)", post)
        self.assertIn("answerWords(0, undefined, draft.forum, false)", handler, "the one-item path calls a lost answer a no")
        self.assertIn("answerWords(0, undefined, draft.forum, !!payload.topic)", post, "the list path calls a lost answer a no")
        self.assertNotIn("This console has not loaded the Chrome connection", self.src,
                         "the old transport sentence (nothing was posted, for an answer that never came) is back")
        for body in (handler.replace(self.words_fn, ""), post):
            self.assertNotIn("reason === 'need-login'", body, "a send path keeps its own copy of the reason map")
        self.assertEqual(self.src.count("The board did not confirm the post, so nothing was posted."), 1)


RED_PROOF = [
    {"why": "#106 - a clicked post the board may hold is headed Not sent again (the maybe-sent answer becomes a no)",
     "file": "bible.html",
     "find": "    if (reason === 'maybe-sent') return { kind: 'maybe',",
     "replace": "    if (reason === 'maybe-sent') return { kind: 'missed',",
     "matches": 1},
    {"why": "#106 - the recent maybe-sent answer is called a no again",
     "file": "bible.html",
     "find": "    if (reason === 'maybe-sent-recently') return { kind: 'maybe',",
     "replace": "    if (reason === 'maybe-sent-recently') return { kind: 'missed',",
     "matches": 1},
    {"why": "#106 - an answer the page does not know falls back to nothing was posted again",
     "file": "bible.html",
     "find": "    return { kind: 'maybe', text: 'The console answered ' + (reason ?",
     "replace": "    return { kind: 'missed', text: 'The board did not confirm the post, so nothing was posted.', x: (reason ?",
     "matches": 1},
    {"why": "#106 - the busy answer says nothing was posted while another send is running",
     "file": "bible.html",
     "find": "'Another post from this console is still being sent. This click started no second post.'",
     "replace": "'The board did not confirm the post, so nothing was posted.'",
     "matches": 1},
    {"why": "#106 - the receipt heads a maybe as Not sent",
     "file": "bible.html",
     "find": "(kind === 'maybe' ? 'Maybe sent' : 'Not sent')",
     "replace": "'Not sent'",
     "matches": 1},
    {"why": "#106 - a maybe receipt drops the board link he checks before a second click",
     "file": "bible.html",
     "find": "    if (kind === 'maybe' && url && (url === d2jspForumUrl(D2JSP_BOARD) || url === d2jspForumUrl(D2JSP_LADDER_BOARD))) safe = url;\n",
     "replace": "",
     "matches": 1},
    {"why": "#106 - the list path keeps its own reason map, which calls a maybe unsent",
     "file": "bible.html",
     "find": "      var w = answerWords(got.code, got.j, draft.forum, !!payload.topic);\n",
     "replace": "      var j = got.j || {}; var w = (j.ok && j.reason === 'submitted') ? answerWords(got.code, j, draft.forum, !!payload.topic) : { kind: 'missed', text: 'The board did not confirm the post, so nothing was posted.' };\n",
     "matches": 1},
    {"why": "#106 - the one-item path keeps its own reason map, which calls a maybe unsent",
     "file": "bible.html",
     "find": "        var w = answerWords(got.code, got.j, draft.forum, false);\n",
     "replace": "        var j = got.j || {}; var w = (j.ok && j.reason === 'submitted') ? answerWords(got.code, j, draft.forum, false) : { kind: 'missed', text: 'The board did not confirm the post, so nothing was posted.' };\n",
     "matches": 1},
    {"why": "#106 - an answer that never arrives (the connection dropped mid-send) is called Not sent again",
     "file": "bible.html",
     "find": "    return { kind: 'maybe', text: heard + ', so the post may be up. Check board ' + n + ' before you post again.', link: d2jspForumUrl(n) };\n",
     "replace": "    return { kind: 'missed', text: 'This console has not loaded the Chrome connection, so nothing was posted.' };\n",
     "matches": 1},
    {"why": "#106 - the one-item path calls an unreadable answer (a 5xx page) unsent again",
     "file": "bible.html",
     "find": "        var w = answerWords(got.code, got.j, draft.forum, false);\n",
     "replace": "        var w = got.j ? answerWords(got.code, got.j, draft.forum, false) : { kind: 'missed', text: 'This console has not loaded the Chrome connection, so nothing was posted.' };\n",
     "matches": 1},
    {"why": "#106 - the list path calls an unreadable answer (a 5xx page) unsent again",
     "file": "bible.html",
     "find": "      var w = answerWords(got.code, got.j, draft.forum, !!payload.topic);\n",
     "replace": "      var w = got.j ? answerWords(got.code, got.j, draft.forum, !!payload.topic) : { kind: 'missed', text: 'This console has not loaded the Chrome connection, so nothing was posted.' };\n",
     "matches": 1},
    {"why": "#106 - the one-item path calls a dropped connection unsent again",
     "file": "bible.html",
     "find": "        var lost = answerWords(0, undefined, draft.forum, false);\n",
     "replace": "        var lost = { kind: 'missed', text: 'This console has not loaded the Chrome connection, so nothing was posted.' };\n",
     "matches": 1},
    {"why": "#106 - the list path calls a dropped connection unsent again",
     "file": "bible.html",
     "find": "      var lost = answerWords(0, undefined, draft.forum, !!payload.topic);\n",
     "replace": "      var lost = { kind: 'missed', text: 'This console has not loaded the Chrome connection, so nothing was posted.' };\n",
     "matches": 1},
    {"why": "#106 - a console with no post route (404) is called a maybe, so the one answer that proves no send is lost",
     "file": "bible.html",
     "find": "    if (code === 404) return { kind: 'missed', text: 'This console has no post route (it answered 404), so nothing was posted.' };\n",
     "replace": "",
     "matches": 1},
    {"why": "#106 - an already-posted list topic is not kept, so the next list post starts a second topic",
     "file": "bible.html",
     "find": "        if (draft.shop && w.topic) writeTopic(w.topic);\n",
     "replace": "",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
