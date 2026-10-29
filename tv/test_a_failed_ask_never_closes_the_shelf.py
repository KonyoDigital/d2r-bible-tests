# -*- coding: utf-8 -*-
"""#86 (REG-3050, folded #245: "the gallery self-closes 8-10 s after the Shelf button") - A FAILED ASK NEVER CLOSES THE
SHELF HE OPENED, AND NEVER CALLS HIS RUNS ABSENT.

thOpen's catch closed #theatre whenever /api/sessions did not answer - right for the REEL door (v2228: a black stage with
nothing coming), wrong for the Shelf door: #theatre holds the shelf, so a slow or orphaned ask (aborted at 8 s then,
REG-2698's 45 s now) took the open gallery away with no word, and the Shelf button's handler then saw TH.open false and
quietly returned. And thShelf's own refresh, failing with no runs in hand, painted the shelf from nothing - "No runs
recorded yet": his runs called absent because a request failed. Now the Shelf door keeps the theatre and the shelf open
and says UNKNOWN in place, with its own ↻ and ✕; a failed refresh with no runs says UNKNOWN; one with runs keeps the cards
and a line names them the console's last answer and its age. The reel door still closes (v2228).

Driven: thOpen, thShelf, _shelfUnknownPaint, _shelfStaleNote and esc cut out of control_ui.html and run in node over a
mock DOM, the sessions ask made to fail. RED_PROOF below.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
NODE = shutil.which("node")
with io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as _fh:
    UI = _fh.read()
FNS = ["  async function thOpen(){", "  function thShelf(force){", "  function _shelfUnknownPaint(ov, why){",
       "  function _shelfStaleNote(ov, why){", "  function esc(s){"]


def _cut(sig):
    if UI.count(sig) != 1:
        raise AssertionError("%r occurs %d times - this law cannot see its subject" % (sig, UI.count(sig)))
    i = UI.index(sig)
    depth = 0
    for j in range(UI.index("{", i), len(UI)):
        if UI[j] == "{":
            depth += 1
        elif UI[j] == "}":
            depth -= 1
            if depth == 0:
                return UI[i:j + 1]
    raise AssertionError("%r never closed - harness fault, not a pass" % sig)


HARNESS = r"""
const C = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
function mk(id) {
  const e = { id: id, hidden: true, textContent: '', style: {}, kids: [], btn: {}, _h: '' };
  Object.defineProperty(e, 'innerHTML', { get() { return this._h; }, set(v) { this._h = String(v); this.kids = []; this.btn = {}; } });
  Object.defineProperty(e, 'firstChild', { get() { return this.kids[0] || null; } });
  e.querySelector = function (sel) {
    if (sel[0] !== '#') return null;
    const want = sel.slice(1);
    const kid = this.kids.find(function (k) { return k.id === want; });
    if (kid) return kid;
    if (this._h.indexOf('id="' + want + '"') < 0) return null;
    return this.btn[want] || (this.btn[want] = { id: want });
  };
  e.insertBefore = function (n) { this.kids.unshift(n); };
  e.querySelectorAll = function () { return []; };
  return e;
}
async function scene(opts) {
  const els = { 'theatre': mk('theatre'), 'th-shelfov': mk('th-shelfov'), 'th-caption': mk('th-caption') };
  const cls = new Set(), faults = [], closed = [];
  const TH = Object.assign({ gen: 0 }, opts.TH || {});
  const document = { body: { classList: { add: (c) => cls.add(c), remove: (c) => cls.delete(c), contains: (c) => cls.has(c) },
                             getAttribute: () => null },
                     createElement: () => ({ id: '', className: '', textContent: '' }), querySelector: () => null };
  const window = { _sessionsJson: () => Promise.reject(new Error('AbortError: the console did not answer')) };
  const $ = (id) => els[id] || null;
  const stubs = {
    thArtInit() {}, thRibbon() {}, thCoachOnce() {}, thLit() {},
    thSessionsWait() { return Promise.reject(new Error('AbortError: the console did not answer')); },
    thClose() { closed.push(1); TH.open = false; els.theatre.hidden = true; },
    _thShelfWasTheDoor() { return !!TH.shelfIsDoor; },
    fetch(url, init) { faults.push(JSON.parse((init && init.body) || '{}')); return Promise.resolve({}); },
  };
  const names = Object.keys(stubs);
  const make = new Function('document', 'window', '$', 'TH', ...names,
    C.code + '\nreturn { thOpen: thOpen, thShelf: thShelf, stale: _shelfStaleNote };');
  const f = make(document, window, $, TH, ...names.map((n) => stubs[n]));
  const out = {};
  if (opts.open) {
    await f.thOpen();
    out.afterOpen = { open: TH.open, theatreHidden: els.theatre.hidden, shelfHidden: els['th-shelfov'].hidden,
                      html: els['th-shelfov'].innerHTML, caption: els['th-caption'].textContent,
                      theatreOpenClass: cls.has('theatre-open'), faults: faults.map((x) => x.kind) };
    const ov = els['th-shelfov'];
    out.retryBound = !!(ov.btn['sh-unk-retry'] && ov.btn['sh-unk-retry'].onclick);
    out.closeBound = !!(ov.btn['sh-unk-x'] && ov.btn['sh-unk-x'].onclick);
    if (opts.thenShelf) {
      TH.shelfIsDoor = true;
      f.thShelf(true);
      out.loading = els['th-shelfov'].innerHTML;
      await new Promise((r) => setTimeout(r, 20));
      out.afterShelf = els['th-shelfov'].innerHTML;
      const x = els['th-shelfov'].btn['sh-unk-x'];
      if (x && x.onclick) x.onclick({ stopPropagation() {} });
      out.afterX = { shelfHidden: els['th-shelfov'].hidden, closed: closed.length };
    }
  }
  if (opts.shelfOnly) {
    TH.sessions = [];
    els['th-shelfov'].hidden = true;
    f.thShelf(true);
    await new Promise((r) => setTimeout(r, 20));
    out.html = els['th-shelfov'].innerHTML;
    out.hidden = els['th-shelfov'].hidden;
  }
  if (opts.stale) {
    const ov = mk('th-shelfov');
    TH.sessionsAt = opts.stale.at;
    f.stale(ov, 'AbortError');
    out.note = ov.kids.length ? ov.kids[0].textContent : null;
  }
  return out;
}
(async function () {
  const now = Date.now();
  const res = {
    door: await scene({ open: true, thenShelf: true, TH: { shelfAsDoor: true } }),
    reel: await scene({ open: true, TH: { shelfAsDoor: false } }),
    refresh: await scene({ shelfOnly: true }),
    staleAged: await scene({ stale: { at: now - 7 * 60000 } }),
    staleUnknown: await scene({ stale: { at: null } }),
  };
  console.log(JSON.stringify(res));
})().catch(function (e) { console.error(String(e && e.stack || e)); process.exit(3); });
"""


def _drive():
    if not NODE:
        raise AssertionError("node is not on this machine - this law does not skip")
    import tempfile
    d = tempfile.mkdtemp(prefix="shelf_unknown_")
    try:
        h, c = os.path.join(d, "h.js"), os.path.join(d, "c.json")
        with io.open(h, "w", encoding="utf-8") as fh:
            fh.write(HARNESS)
        with io.open(c, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"code": "\n".join(_cut(f) for f in FNS)}))
        r = subprocess.run([NODE, h, c], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    finally:
        shutil.rmtree(d, True)
    if r.returncode != 0:
        raise AssertionError("node failed: %s" % r.stderr[-1200:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class AFailedAskNeverClosesTheShelf(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = _drive()

    def test_the_shelf_door_stays_open_and_says_unknown(self):
        a = self.o["door"]["afterOpen"]
        self.assertTrue(a["open"] and not a["theatreHidden"] and not a["shelfHidden"] and a["theatreOpenClass"],
                        "a failed ask closed the shelf he opened: %r" % {k: a[k] for k in ("open", "theatreHidden", "shelfHidden")})
        self.assertIn("your runs: UNKNOWN", a["html"])
        self.assertIn("UNKNOWN", a["caption"])
        self.assertNotIn("No runs recorded yet", a["html"])
        self.assertTrue(self.o["door"]["retryBound"] and self.o["door"]["closeBound"], "the UNKNOWN shelf has no ↻ or ✕")
        self.assertIn("shelf-open-no-sessions", a["faults"], "the Doctor was not told")

    def test_the_shelf_button_asks_again_and_still_never_says_empty(self):
        d = self.o["door"]
        self.assertIn("asking the console again", d["loading"], "the second ask reads as a plain first load")
        self.assertIn("your runs: UNKNOWN", d["afterShelf"])
        self.assertNotIn("No runs recorded yet", d["afterShelf"])
        self.assertEqual(d["afterX"], {"shelfHidden": True, "closed": 1}, "✕ on the UNKNOWN shelf did not close it")

    def test_the_reel_door_still_closes_its_black_stage(self):
        a = self.o["reel"]["afterOpen"]
        self.assertEqual((a["open"], a["theatreHidden"], a["theatreOpenClass"]), (False, True, False),
                         "the reel door left a black stage up (v2228)")

    def test_a_failed_refresh_with_no_runs_is_unknown_not_empty(self):
        r = self.o["refresh"]
        self.assertFalse(r["hidden"])
        self.assertIn("your runs: UNKNOWN", r["html"])
        self.assertNotIn("No runs recorded yet", r["html"])

    def test_cards_kept_after_a_failed_refresh_say_how_old_they_are(self):
        self.assertEqual(self.o["staleAged"]["note"],
                         "the console did not answer (AbortError) — these runs are its answer from 7 min ago")
        self.assertIn("age is UNKNOWN", self.o["staleUnknown"]["note"])

    def test_a_failed_refresh_with_runs_in_hand_notes_their_age(self):
        catch = UI[UI.index("    }).catch(function(e){\n      /* REG-3050 - NO ANSWER IS NOT AN EMPTY SHELF."):]
        catch = catch[:catch.index("    });\n")]
        self.assertIn("if (!_had) { _shelfUnknownPaint(ov, TH.sessionsFailWhy); return; }", catch)
        self.assertIn("_shelfStaleNote(ov, TH.sessionsFailWhy);", catch)


RED_PROOF = [
    {"why": "REG-3050 - the shelf door's failed ask closes the theatre and the shelf again",
     "file": "tv/control_ui.html",
     "find": "      if (_shelfDoor) {\n        TH.sessionsFailWhy = String(_e).slice(0, 120);\n",
     "replace": "      if (false) {\n        TH.sessionsFailWhy = String(_e).slice(0, 120);\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-3050 - a failed refresh with no runs paints 'No runs recorded yet'",
     "file": "tv/control_ui.html",
     "find": "      if (!_had) { _shelfUnknownPaint(ov, TH.sessionsFailWhy); return; }\n",
     "replace": "      if (!_had) { _paintShelf(); _reopenClear(); return; }\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-3050 - the UNKNOWN shelf has no ✕",
     "file": "tv/control_ui.html",
     "find": "    if (x) x.onclick = function(e){\n",
     "replace": "    if (false) x.onclick = function(e){\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-3050 - the second ask reads as a plain first load",
     "file": "tv/control_ui.html",
     "find": "        + (TH.sessionsFailWhy ? 'asking the console again\\u2026' : 'Loading runs…') + '</div></div>';\n",
     "replace": "        + 'Loading runs…' + '</div></div>';\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-3050 - kept cards do not say how old the answer is",
     "file": "tv/control_ui.html",
     "find": "      age = 'its answer from ' + (m < 1 ? 'under a minute ago' : m < 120 ? m + ' min ago' : Math.round(m / 60) + ' h ago');\n",
     "replace": "",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
