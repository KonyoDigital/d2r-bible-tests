# -*- coding: utf-8 -*-
"""ESCAPE ANSWERS THE QUESTION "NO" — IT NEVER QUITS THE CONSOLE.

The second eye on v3497 (grok-4.7, 1b9b7248), confirmed in the code: the inbox's capture-phase Escape
listener ran BEFORE the in-page question's own and stopped the event, so Escape with a question up
("Promote ALL 5 ...?") closed the INBOX and left the question on screen with its yes button armed; the
NEXT Escape reached the empty-page handler, which did not know #ch-ask existed, and POSTed /api/quit -
his console closed.

  · DRIVEN (node, the REAL handlers from control_ui.html through a capture/bubble dispatcher): Escape
    with the question up hides the question and leaves the inbox open; a second Escape closes the inbox;
    NO /api/quit at any step.
  · DRIVEN: closing the inbox with a question up hides the question AND disarms its yes button.
  · PREMISE: with the inbox closed and nothing open, Escape DOES quit - so the no-quit cases can fail.
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

UI = os.path.join(HERE, "control_ui.html")


def _between(src, start, end):
    i = src.index(start)
    j = src.index(end, i + len(start))
    return src[i:j + len(end)]


def _handlers():
    with io.open(UI, encoding="utf-8") as f:
        src = f.read()
    return "\n".join([
        _between(src, "  function chModalClose(){", "\n  }"),
        _between(src, "  function chAsk(text, yesLabel, onYes){", "\n  }\n  window._chAsk = chAsk;"),
        _between(src, "    document.addEventListener('keydown', function(e){\n      if (!CH.open) return;", "    }, true);"),
        _between(src, "  document.addEventListener('keydown', function(e){\n    if (e.key !== 'Escape') return;\n    if (e.defaultPrevented) return;",
                 "  }, false);"),
    ])


DOM = r"""
function El(tag){ this.tagName = (tag||'div').toUpperCase(); this.id = ''; this.hidden = false; this.parent = null;
  this.children = []; this.L = {cap: [], bub: []}; this.onclick = null; this.textContent = '';
  var me = this; this.classList = { _c: {}, contains: function(c){ return !!me.classList._c[c]; } }; }
El.prototype.addEventListener = function(t, fn, cap){ if (t === 'keydown') (cap ? this.L.cap : this.L.bub).push(fn); };
El.prototype.appendChild = function(c){ c.parent = this; this.children.push(c); return c; };
El.prototype.focus = function(){ document.activeElement = this; };
Object.defineProperty(El.prototype, 'innerHTML', { set: function(h){
  var re = /<(\w+)[^>]*\sid="([^"]+)"/g, m;
  while ((m = re.exec(h))){ var c = new El(m[1]); c.id = m[2]; this.appendChild(c); }
}});
var body = new El('body');
var document = new El('#document'); document.body = body; body.parent = document;
document.activeElement = body;
document.createElement = function(t){ return new El(t); };
function _find(n, id){ if (n.id === id) return n; for (var i = 0; i < n.children.length; i++){ var r = _find(n.children[i], id); if (r) return r; } return null; }
document.getElementById = function(id){ return _find(body, id); };
function _visible(n){ for (var x = n; x; x = x.parent) if (x.hidden) return false; return true; }
function press(key){
  var t = document.activeElement;
  if (!_visible(t)) { t = body; document.activeElement = body; }      // a hidden element cannot hold focus
  var path = []; for (var x = t; x; x = x.parent) path.unshift(x);    // [document, body, ..., t]
  var ev = { key: key, target: t, defaultPrevented: false, _stop: false,
             preventDefault: function(){ this.defaultPrevented = true; },
             stopPropagation: function(){ this._stop = true; } };
  for (var i = 0; i < path.length - 1 && !ev._stop; i++) path[i].L.cap.forEach(function(f){ f(ev); });
  if (!ev._stop) { t.L.cap.concat(t.L.bub).forEach(function(f){ f(ev); }); }
  for (var j = path.length - 2; j >= 0 && !ev._stop; j--) path[j].L.bub.forEach(function(f){ f(ev); });
}
var modal = new El('div'); modal.id = 'ch-modal'; body.appendChild(modal);
function $(id){ return document.getElementById(id); }
var window = {};
var CH = { open: false }, QUITS = [], YES = 0;
function toast(){}
function fetch(url, opts){ QUITS.push(url); return { catch: function(){} }; }
"""


def _run(script):
    js = DOM + "\n" + _handlers() + "\n" + script
    r = subprocess.run([shutil.which("node"), "-"], input=js, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("node could not run the shipped handlers - UNKNOWN, not passing: %s" % r.stderr[:600])
    return json.loads(r.stdout.strip().splitlines()[-1])


STATE = "console.log(JSON.stringify({open: CH.open, askHidden: $('ch-ask') ? $('ch-ask').hidden : null, quits: QUITS, yes: YES, armed: $('ch-ask-yes') ? !!$('ch-ask-yes').onclick : null}));"


@unittest.skipIf(shutil.which("node") is None, "node is absent - this law is UNMEASURED, not passing")
class EscapeAnswersTheQuestionNo(unittest.TestCase):

    def test_premise_on_an_empty_page_escape_quits(self):
        out = _run("press('Escape');" + STATE)
        self.assertEqual(out["quits"], ["/api/quit"], "premise: the empty-page Escape must quit, or the no-quit cases prove nothing")

    def test_escape_with_a_question_up_answers_no_and_the_inbox_stays(self):
        out = _run("CH.open = true; modal.hidden = false; chAsk('Promote ALL 5?', 'Promote all 5', function(){ YES++; });"
                   "press('Escape');" + STATE)
        self.assertTrue(out["askHidden"], "the question stayed on screen after Escape")
        self.assertTrue(out["open"], "Escape on the question closed the INBOX instead")
        self.assertEqual(out["quits"], [], "Escape on the question quit the console")

    def test_a_second_escape_closes_the_inbox_and_never_quits(self):
        out = _run("CH.open = true; modal.hidden = false; chAsk('Promote ALL 5?', 'Promote all 5', function(){ YES++; });"
                   "press('Escape'); press('Escape');" + STATE)
        self.assertFalse(out["open"])
        self.assertEqual(out["quits"], [], "his console quit two Escapes after a question was asked (the v3497 path)")
        self.assertEqual(out["yes"], 0)

    def test_closing_the_inbox_closes_and_disarms_its_question(self):
        out = _run("CH.open = true; modal.hidden = false; chAsk('Clear all 3?', 'Clear all 3', function(){ YES++; });"
                   "chModalClose();" + STATE)
        self.assertTrue(out["askHidden"], "the question outlived the inbox")
        self.assertFalse(out["armed"], "the question's yes button is still armed after the inbox closed")

    def test_an_open_question_alone_claims_escape(self):
        out = _run("CH.open = true; chAsk('Q?', 'Yes', function(){ YES++; }); CH.open = false;"
                   "document.activeElement = body; press('Escape');" + STATE)
        self.assertEqual(out["quits"], [], "an open question did not claim Escape from the quit handler")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "the second eye on v3497 - the inbox's capture Escape closes the inbox over an open question again (next Escape quits the console)",
        "file": "control_ui.html",
        "find": "      if (_ask && !_ask.hidden){ _ask.hidden = true; return; }\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "the second eye on v3497 - closing the inbox leaves its question on screen with yes armed",
        "file": "control_ui.html",
        "find": "    if (ask){ ask.hidden = true; var y = document.getElementById('ch-ask-yes'); if (y) y.onclick = null; }\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "the second eye on v3497 - the quit handler does not know an open question claims Escape",
        "file": "control_ui.html",
        "find": "      var _ovIds = ['forensics-ov', 'th-dossier-ov', 'ch-ask'];   /* an open question claims Escape */\n",
        "replace": "      var _ovIds = ['forensics-ov', 'th-dossier-ov'];\n",
        "matches": 1,
    },
]
