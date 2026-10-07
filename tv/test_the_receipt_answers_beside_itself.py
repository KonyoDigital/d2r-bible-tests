# -*- coding: utf-8 -*-
"""REG-1936 - THE VAULT'S ◉ ANSWERS BESIDE ITSELF, NOT IN A LINE AT THE TOP OF THE PANE.

GrokBot (#230 C10, v3600, his live console): the Vault REGISTERED row's ◉ "why is this here? - show the frame
that witnessed it" opened NO picture and the page shifted ~20 px. Measured the same night: /api/evidence?name=
Bone Visor answered ok:false "nothing banked ... no look at it either" - the ◉ refused HONESTLY, into
#vault-status, a line at the top of the pane that shows for 4.2 s and pushes the layout down. The reason was
right and was not where his eye was.

The law, driven in node on the real click handler lifted from bible.html: every refusal (no console, nothing
banked, no frame kept, no answer) writes its reason on a line right under the ◉'s row, puts the whole sentence on
the ◉'s title and dims it, and no longer writes the status line; a second refusal reuses the span.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

MARK = "REG-1936 — SAY IT WHERE HE IS LOOKING"
OPEN = "document.addEventListener('click', function (e) {"


def _handler():
    with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
        src = fh.read()
    at = src.find(MARK)
    if at < 0:
        return None
    lo = src.rfind(OPEN, 0, at)
    hi = src.find("}, true);", at)
    if lo < 0 or hi < 0:
        return None
    return src[lo:hi + len("}, true);")]


HARNESS = r"""
function El(tag, cls){ this.tag = tag; this.className = cls || ''; this.kids = []; this.attrs = {}; this.title = '';
  this.textContent = ''; var self = this;
  this.classList = {contains: function(c){ return (' ' + self.className + ' ').indexOf(' ' + c + ' ') >= 0; },
                    add: function(c){ if (!this.contains(c)) self.className += ' ' + c; }}; }
El.prototype.getAttribute = function(k){ return this.attrs[k] == null ? null : this.attrs[k]; };
El.prototype.setAttribute = function(k, v){ this.attrs[k] = String(v); };
El.prototype.insertBefore = function(n, ref){ var i = this.kids.indexOf(ref); n.parentNode = this;
  if (i < 0) this.kids.push(n); else this.kids.splice(i, 0, n); };
Object.defineProperty(El.prototype, 'nextElementSibling', {get: function(){
  var p = this.parentNode; if (!p) return null; var i = p.kids.indexOf(this); return p.kids[i + 1] || null; }});
Object.defineProperty(El.prototype, 'nextSibling', {get: function(){ return this.nextElementSibling; }});
El.prototype.querySelector = function(sel){ var c = sel.replace(/^\./, '');
  for (var i = 0; i < this.kids.length; i++) if (this.kids[i].classList.contains(c)) return this.kids[i]; return null; };
var cfg = %s;
var statusCalls = [];
function status(m){ statusCalls.push(m); }
var location = {protocol: cfg.protocol};
var handler = null;
var document = {addEventListener: function(type, fn){ handler = fn; },
                createElement: function(tag){ return new El(tag); }};
function fetch(){ if (cfg.reject) return Promise.reject({name: 'TypeError'});
  return Promise.resolve({json: function(){ return cfg.answer; }}); }
%s
var col = new El('div', 'vrg-col-body'), row = new El('div', 'vrg-row'), btn = new El('button', 'vrg-rcpt'),
    nextRow = new El('div', 'vrg-row');
row.parentNode = col; nextRow.parentNode = col; col.kids.push(row); col.kids.push(nextRow);
btn.attrs['data-rcpt'] = 'Bone Visor'; btn.parentNode = row; row.kids.push(btn);
function click(){ handler({target: btn, preventDefault: function(){}, stopPropagation: function(){}}); }
click();
setTimeout(function(){
  if (cfg.twice) click();
  setTimeout(function(){
    var spans = col.kids.filter(function(k){ return k.classList.contains('vrg-rcpt-why'); });
    process.stdout.write(JSON.stringify({
      spans: spans.length, after: col.kids.indexOf(spans[0]) === col.kids.indexOf(row) + 1,
      short: spans[0] ? spans[0].textContent : null, spanTitle: spans[0] ? spans[0].title : null,
      title: btn.title, dim: btn.classList.contains('vrg-rcpt-none'), aria: btn.getAttribute('aria-label'),
      status: statusCalls}));
  }, 20);
}, 20);
"""


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class TheReceiptAnswersBesideItself(unittest.TestCase):

    def run_click(self, **cfg):
        h = _handler()
        self.assertIsNotNone(h, "the ◉ click handler's REG-1936 block is gone from bible.html")
        base = {"protocol": "http:", "answer": None, "reject": False, "twice": False}
        base.update(cfg)
        p = subprocess.run(["node", "-"], input=HARNESS % (json.dumps(base), h), capture_output=True, text=True,
                           timeout=30)
        self.assertEqual(p.returncode, 0, p.stderr[-800:])
        return json.loads(p.stdout)

    def assert_beside(self, out, short, why_part):
        self.assertEqual(out["spans"], 1, "the ◉'s answer did not land under its row (REG-1936): %s" % out)
        self.assertTrue(out["after"], "the answer is in the list but not right under the ◉'s row")
        self.assertTrue(out["short"].startswith("\u25c9 " + short + " \u2014 "), out["short"])
        self.assertIn(why_part, out["short"], "the line under the row does not carry the reason")
        self.assertIn(why_part, out["title"], "the ◉'s title does not carry the whole reason")
        self.assertIn(why_part, out["spanTitle"])
        self.assertTrue(out["dim"], "a ◉ with nothing to show still looks like it has a frame")
        self.assertEqual(out["status"], [], "the refusal still went to the status line at the top of the pane")

    def test_nothing_banked_says_so_beside_the_button(self):
        out = self.run_click(answer={"ok": False, "why": "nothing banked - no look at it either"})
        self.assert_beside(out, "nothing banked", "no look at it either")
        self.assertIn("Bone Visor", out["title"])

    def test_sightings_without_a_frame(self):
        out = self.run_click(answer={"ok": True, "sightings": [{"conf": 0.9}, {"conf": 0.5}]})
        self.assert_beside(out, "no frame kept", "2 sighting(s) banked, but none kept a frame")

    def test_a_board_opened_as_a_file(self):
        self.assert_beside(self.run_click(protocol="file:"), "no console", "open as a file")

    def test_a_console_that_does_not_answer(self):
        self.assert_beside(self.run_click(reject=True), "no answer", "TypeError")

    def test_the_listener_binds_once_however_often_the_vault_renders(self):
        """The binding sits inside renderVaultRegistered, which runs on every vault render; each run used to add
        another capture listener, so one click sent one /api/evidence request per render so far."""
        with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
            src = fh.read()
        lo = src.find("      if (!window.__vrgRcptBound) {")
        self.assertGreaterEqual(lo, 0, "the ◉ listener is bound on every render again")
        hi = src.find("      }, true);\n      }\n", lo)
        self.assertGreater(hi, lo, "the bind-once block cannot be bounded")
        block = src[lo:hi + len("      }, true);\n      }\n")]
        js = ("var n = 0; var window = {}; var document = {addEventListener: function(){ n++; }};\n"
              "function render(){\n" + block + "}\nrender(); render(); render();\n"
              "process.stdout.write(String(n));")
        p = subprocess.run(["node", "-"], input=js, capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, p.stderr[-600:])
        self.assertEqual(p.stdout.strip(), "1", "three vault renders bound %s ◉ listeners (REG-1936)" % p.stdout)

    def test_a_second_refusal_reuses_the_note(self):
        out = self.run_click(answer={"ok": False, "why": "nothing banked"}, twice=True)
        self.assertEqual(out["spans"], 1, "a second click stacked a second note")


RED_PROOF = [
    {
        "why": "REG-1936 - the ◉ listener is bound on every vault render again: one click, one request per render",
        "file": "bible.html",
        "find": "      if (!window.__vrgRcptBound) {\n      window.__vrgRcptBound = true;\n",
        "replace": "      if (true) {\n",
        "matches": 1,
    },
    {
        "why": "REG-1936 - the ◉'s answer is no longer placed beside it: the reason is computed and shown nowhere",
        "file": "bible.html",
        "find": "              _row.parentNode.insertBefore(_w, _row.nextSibling);",
        "replace": "              _w = null;",
        "matches": 1,
    },
    {
        "why": "REG-1936 - 'nothing banked' goes back to the status line at the top of the pane",
        "file": "bible.html",
        "find": "              _say('nothing banked', nm + ' — ' + ((d && d.why) || 'nothing banked for this name'));",
        "replace": "              try { status('\\u25c9 ' + nm + ' — ' + ((d && d.why) || 'nothing banked for this name')); } catch (_) {}",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
