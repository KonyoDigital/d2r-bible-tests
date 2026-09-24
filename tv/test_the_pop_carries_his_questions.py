# -*- coding: utf-8 -*-
"""#223 — THE 📥 POP AND THE SESSIONS STICKY CARRY HIS QUESTIONS.

The 📥 pop is titled "Waiting on you". It carried only the names the readers could not settle, while
the questions that are genuinely his (the console's ASKS) were drawn in the inbox section alone — and
with no names pending it said "Nothing is waiting" over an open question. Now one builder
(_askCardsHtml) is read through window._inboxAskCards by the inbox, the pop and the sticky.

  · DRIVEN (node, the REAL bridge): _inboxAskCards draws every open question with its buttons and
    fingerprints, and draws nothing when the watchdog has not answered.
  · DRIVEN (node, the REAL renderInboxFab, a minimal fake DOM): an open question reaches the pop AND
    the sticky, the badge counts it, and neither "Nothing is waiting" nor "Nothing to rule on" is said
    over it. PREMISE: with no question and no names the empty sentences ARE said.
Pixels: render target `pop-asks` (the adopt -> paint -> pop join, end to end).
RED_PROOF below.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")


def _src():
    with io.open(BIBLE, encoding="utf-8") as f:
        return f.read()


def _between(src, start, end):
    i = src.index(start)
    j = src.index(end, i + len(start))
    return src[i:j + len(end)]


def _node(js):
    r = subprocess.run([shutil.which("node"), "-e", js], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("node could not evaluate the shipped code - UNKNOWN, not passing: %s"
                             % (r.stderr or "")[:600])
    return json.loads(r.stdout.strip().splitlines()[-1])


ASK = {"id": "remaining-page", "kind": "do", "fp": "remaining-page:2026-08-21",
       "q": "Film a new Remaining page so the console can confirm 16 set rows?",
       "why": "Your board has 132 set pieces ticked.",
       "answers": [{"key": "filmed", "label": "I filmed one", "effect": "verify"},
                   {"key": "week", "label": "Remind me in a week", "effect": "snooze"},
                   {"key": "skip", "label": "Not needed", "effect": "ruled"}]}


def _bridge(eagle):
    src = _src()
    cards = _between(src, "  function _askCardsHtml(r, asks, esc){", "\n    return h;\n  }")
    bridge = _between(src, "    window._inboxAskCards = function(){", "      return out;\n    };")
    js = """
    var location = { protocol: 'http:' };
    var window = {};
    var _eagleNY = %s;
    %s
    %s
    console.log(JSON.stringify(window._inboxAskCards()));
    """ % (json.dumps(eagle), cards, bridge)
    return _node(js)


def _fab(asks, pend):
    src = _src()
    fab = _between(src, "  window.renderInboxFab = function(){", "\n  window.inboxPopTog = function(){")
    fab = fab[:fab.rindex("\n  window.inboxPopTog = function(){")]
    js = """
    function El(id){ var me = this; this.id = id; this.innerHTML = ''; this.textContent = ''; this._c = {};
      this.classList = {
        toggle: function(c, on){ if (on === undefined) on = !me._c[c]; if (on) me._c[c] = 1; else delete me._c[c]; return on; },
        add: function(c){ me._c[c] = 1; }, remove: function(c){ delete me._c[c]; },
        contains: function(c){ return !!me._c[c]; } }; }
    var els = {};
    ['inbox-fab', 'inbox-pop', 'inbox-fab-n', 'inbox-sticky'].forEach(function(i){ els[i] = new El(i); });
    var document = { getElementById: function(i){ return els[i] || null; } };
    var ASKS = %s, PEND = %s;
    var window = {
      kaiChronicleResolvePending: function(){ return null; },
      kaiChronicleInbox: function(){ return PEND; },
      kaiChronicleRetiredRecent: function(){ return []; },
      inboxReaderQueue: function(){ return []; },
      d2rInboxEngine: function(){ return null; },
      _inboxAskCards: function(){ return ASKS; }
    };
    %s
    window.renderInboxFab();
    console.log(JSON.stringify({
      pop: els['inbox-pop'].innerHTML, sticky: els['inbox-sticky'].innerHTML,
      stickyHas: els['inbox-sticky'].classList.contains('has'),
      fabHas: els['inbox-fab'].classList.contains('has'), n: els['inbox-fab-n'].textContent }));
    """ % (json.dumps(asks), json.dumps(pend), fab)
    return _node(js)


@unittest.skipIf(shutil.which("node") is None, "node is absent - this law is UNMEASURED, not passing")
class TheBridgeDrawsTheSameCard(unittest.TestCase):

    def test_every_open_question_is_drawn_with_its_buttons(self):
        out = _bridge({"st": "rows", "rows": [{"check": "a fresh remaining page", "why": "w", "openAsks": [ASK]},
                                              {"check": "ledger staleness", "why": "Claude's", "asks": []}]})
        self.assertEqual(out["n"], 1)
        self.assertIn("Film a new Remaining page", out["html"])
        self.assertEqual(out["html"].count('class="ibx-ny-b"'), 3, "the card lost its answer buttons")
        self.assertEqual(out["sig"], ASK["fp"])

    def test_a_watchdog_that_has_not_answered_draws_nothing(self):
        out = _bridge({"st": "unknown", "rows": []})
        self.assertEqual((out["n"], out["html"], out["sig"]), (0, "", ""))


@unittest.skipIf(shutil.which("node") is None, "node is absent - this law is UNMEASURED, not passing")
class ThePopCarriesHisQuestions(unittest.TestCase):
    CARD = '<div class="ibx-ny-ask" data-fp="remaining-page:2026-08-21">FIXTURE QUESTION</div>'

    def test_premise_nothing_waiting_says_so(self):
        out = _fab({"n": 0, "html": "", "sig": ""}, [])
        self.assertIn("Nothing is waiting", out["pop"])
        self.assertFalse(out["fabHas"])

    def test_an_open_question_reaches_the_pop_and_the_sticky(self):
        out = _fab({"n": 1, "html": self.CARD, "sig": "f"}, [])
        self.assertIn("FIXTURE QUESTION", out["pop"], "the pop titled 'Waiting on you' left his question out")
        self.assertTrue(out["stickyHas"], "the Sessions sticky stayed hidden over an open question")
        self.assertIn("FIXTURE QUESTION", out["sticky"])

    def test_the_badge_counts_his_question(self):
        out = _fab({"n": 1, "html": self.CARD, "sig": "f"}, [])
        self.assertTrue(out["fabHas"], "the 📥 badge hid itself over an open question")
        self.assertEqual(out["n"], "1")

    def test_no_empty_sentence_is_said_over_a_question(self):
        out = _fab({"n": 1, "html": self.CARD, "sig": "f"}, [])
        self.assertNotIn("Nothing is waiting", out["pop"])
        self.assertNotIn("Nothing to rule on", out["pop"])


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#223 - the pop titled 'Waiting on you' leaves his questions out again",
        "file": "bible.html",
        "find": "        if (_ak.n) H.push('<div class=\"ibp-asks\">' + _ak.html + '</div>');\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#223 - the 📥 badge stops counting his open questions (it hid itself over one)",
        "file": "bible.html",
        "find": "      var nAll = n + (_ak.n || 0);\n",
        "replace": "      var nAll = n;\n",
        "matches": 1,
    },
    {
        "why": "#223 - the bridge draws an empty card: the inbox and the pop say it two ways again",
        "file": "bible.html",
        "find": "        out.html += _askCardsHtml(r, open, esc);\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#223 - the Sessions sticky stays hidden over an open question",
        "file": "bible.html",
        "find": "            var _any = n > 0 || (_rr && _rr.length) || _ak.n > 0;\n",
        "replace": "            var _any = n > 0 || (_rr && _rr.length);\n",
        "matches": 1,
    },
]
