# -*- coding: utf-8 -*-
"""REG-1638 — AN UN-TICK THEN A RE-TICK IS ONE MISCLICK, NOT A NEW FIND.

His question, 2026-09-30, looking at F·Uniques' "last found: The Cat's Eye": "how did this get here? ... is there a
ledger and proof image of this? was it really a chronicle?". MEASURED on a read-only copy of his board the same night:
the Grok reader read The Cat's Eye from his SHARED stash at 01:13:59 (its own frame shows the tooltip), the vault filed
it with that witness, and the Chronicle inbox accepted it. At 23:14:57 it was un-ticked on its item card and at 23:15:00
ticked again. The un-tick did what v1891/v1964 rule it must - the found date, the game date and the sightings went, and
the vault removal door took it out of d2r_owned - and the re-tick three seconds later stamped "found 23:15" with no
evidence and never put it back in the vault. v1964 wrote the cost down itself: "a plain toggle has no redo, so an
accidental un-tick loses a legitimate date with no recovery".

Driven here, on the shipped page code (cut from bible.html by its markers, run in node - never re-typed):
  1. the redo - a re-tick inside TICK_REDO_MS of its own un-tick gets back the FIRST found date, the game date and the
     sightings; the vault removal it made is undone only while that removal is still the newest (nothing else is ever
     undone - another removal in between is said, not reversed).
  2. the old rule stands outside the window - past it, or with no un-tick before it, a re-tick is a new find; one
     un-tick buys one redo.
  3. the evidence door - it puts a row back and never overwrites one a later read wrote; a store that will not parse is
     never written over.
  4. the join - toggleOwned's uniques branch keeps before it deletes, notes its own removal's stamp, takes the redo
     before it stamps, and restores after the found date is written (read from the function's code, in order).
RED_PROOF below. No node = SKIP with a declared reason, never a pass.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

NODE = shutil.which("node")
BIBLE = os.path.join(ROOT, "bible.html")

RED_PROOF = [
    {"why": "REG-1638 - the un-tick keeps nothing: a re-tick three seconds later stamps a new date (The Cat's Eye)",
     "file": "bible.html",
     "find": "  window._TICK_REDO[String(name)] = r;\n",
     "replace": "  void r;\n", "matches": 1},
    {"why": "REG-1638 - the window never closes: a re-tick a day later would bring back a date the read was wrong about",
     "file": "bible.html",
     "find": "  if (((now == null ? Date.now() : now) - r.at) > window.TICK_REDO_MS) return null;   // past the window: a new find\n",
     "replace": "  if (false) return null;\n", "matches": 1},
    {"why": "REG-1638 - the redo undoes the NEWEST removal whatever it was, not the un-tick's own",
     "file": "bible.html",
     "find": "      out.vault = (last && last.ts === r.vaultTs && typeof window.vaultRestoreLast === 'function')\n",
     "replace": "      out.vault = (last && typeof window.vaultRestoreLast === 'function')\n", "matches": 1},
    {"why": "REG-1638 - the evidence door writes over a row a later read wrote",
     "file": "bible.html",
     "find": "      if (Object.prototype.hasOwnProperty.call(map, name)) return false;\n      map[name] = row;\n",
     "replace": "      map[name] = row;\n", "matches": 1},
    {"why": "REG-1638 - toggleOwned never asks for the redo: the helpers exist and the tick still stamps a new date",
     "file": "bible.html",
     "find": "      else if ((_rdt = window._tickRedoTake ? window._tickRedoTake(name) : null) && _rdt.found) fl[name] = _rdt.found;   // REG-1638\n",
     "replace": "", "matches": 1},
]


def _src():
    with io.open(BIBLE, encoding="utf-8") as fh:
        return fh.read()


def _between(src, begin, end):
    i = src.index(begin)
    j = src.index(end, i)
    return src[i:j + len(end)]


def _cut_fn(src, head):
    """A top-level `window.X = function(...){ ... };` by brace depth from its head - the whole function, nothing after."""
    i = src.index(head)
    k = src.index("{", i)
    depth = 0
    for p in range(k, len(src)):
        c = src[p]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[i:p + 1] + ";"
    raise AssertionError("unbalanced function: %s" % head)


HARNESS = r"""
globalThis.window = globalThis;
const STORE = {};
window.LSR = {
  getItem: function(k){ return Object.prototype.hasOwnProperty.call(STORE, k) ? STORE[k] : null; },
  setItem: function(k, v){ STORE[k] = String(v); },
  removeItem: function(k){ delete STORE[k]; }
};
let JOURNAL = [], RESTORED = 0;
window.vaultRemovalLog = function(){ return JOURNAL.slice(); };
window.vaultRestoreLast = function(){ const b = JOURNAL.pop(); RESTORED += 1; return { restored: b ? b.names.length : 0, ts: b && b.ts }; };
__CODE__
function out(x){ process.stdout.write(JSON.stringify(x) + "\n"); }
const N = "The Cat's Eye";
function seed(){
  for (const k of Object.keys(STORE)) delete STORE[k];
  STORE.d2r_gameFound = JSON.stringify({ [N]: { at: "Sep 29, 2026", by: "", n: 0 } });
  STORE.d2r_foundEvidence = JSON.stringify({ [N]: { sightings: [{ reel: "reel_fixture", frame: "f_1.jpg" }] } });
  JOURNAL = []; RESTORED = 0; window._TICK_REDO = {};
}
const T0 = 1000000;
// 1. the misclick: keep at the un-tick (its removal stamped 777), the un-tick deletes, re-tick 3 s later
seed();
let r = window._tickRedoKeep(N, "Sep 30, 2026 · 01:13", T0);
JOURNAL.push({ ts: 777, names: [N] }); r.vaultTs = 777;
let g = JSON.parse(STORE.d2r_gameFound); delete g[N]; STORE.d2r_gameFound = JSON.stringify(g);
let e = JSON.parse(STORE.d2r_foundEvidence); delete e[N]; STORE.d2r_foundEvidence = JSON.stringify(e);
let t = window._tickRedoTake(N, T0 + 3000);
let rest = window._tickRedoRestore(N, t);
out({ case: "redo", found: t && t.found, rest: rest, game: JSON.parse(STORE.d2r_gameFound)[N] || null,
      ev: JSON.parse(STORE.d2r_foundEvidence)[N] || null, restored: RESTORED, again: window._tickRedoTake(N, T0 + 4000) });
// 2. past the window
seed();
window._tickRedoKeep(N, "Sep 30, 2026 · 01:13", T0);
out({ case: "late", take: window._tickRedoTake(N, T0 + window.TICK_REDO_MS + 1) });
// 2b. never un-ticked
seed();
out({ case: "none", take: window._tickRedoTake(N, T0) });
// 3. another removal came after the un-tick's own
seed();
r = window._tickRedoKeep(N, "Sep 30, 2026 · 01:13", T0); r.vaultTs = 777;
JOURNAL.push({ ts: 777, names: [N] }); JOURNAL.push({ ts: 900, names: ["Shako"] });
t = window._tickRedoTake(N, T0 + 3000);
rest = window._tickRedoRestore(N, t);
out({ case: "other-removal", vault: rest.vault, restored: RESTORED, journal: JOURNAL.map(function(b){ return b.ts; }) });
// 4. the evidence door
seed();
STORE.d2r_foundEvidence = JSON.stringify({ [N]: { sightings: [{ reel: "later_read" }] } });
const kept = window._foundEvidencePut(N, { sightings: [{ reel: "old" }] });
const after = JSON.parse(STORE.d2r_foundEvidence)[N];
STORE.d2r_foundEvidence = "{not json";
const junk = window._foundEvidencePut(N, { sightings: [] });
out({ case: "put", kept: kept, after: after, junk: junk, raw: STORE.d2r_foundEvidence });
"""


@unittest.skipIf(NODE is None, "node is not on this PC - the page code cannot be driven here: UNMEASURED, not a pass")
class AnUntickThenARetickIsOneMisclick(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src = _src()
        code = "\n".join([_between(src, "/* ⟦TICK REDO BEGIN⟧", "/* ⟦TICK REDO END⟧ */"),
                          _cut_fn(src, "  window._gameFoundSet = function(name, g){"),
                          _between(src, "  /* ⟦FOUND EVIDENCE PUT BEGIN⟧", "  /* ⟦FOUND EVIDENCE PUT END⟧ */")])
        d = tempfile.mkdtemp(prefix="tick_redo_")
        try:
            js = os.path.join(d, "h.js")
            with io.open(js, "w", encoding="utf-8") as fh:
                fh.write(HARNESS.replace("__CODE__", code))
            r = subprocess.run([NODE, js], capture_output=True, text=True, encoding="utf-8", timeout=60)
        finally:
            shutil.rmtree(d, True)
        if r.returncode != 0:
            raise AssertionError("the page code would not run in node - UNKNOWN, not passing: %s" % r.stderr[-600:])
        cls.rows = {}
        for ln in r.stdout.splitlines():
            o = json.loads(ln)
            cls.rows[o["case"]] = o

    def test_a_retick_in_the_window_gets_back_everything_the_untick_took(self):
        o = self.rows["redo"]
        self.assertEqual(o["found"], "Sep 30, 2026 · 01:13", "the re-tick did not get back the FIRST found date")
        self.assertEqual((o["game"] or {}).get("at"), "Sep 29, 2026", "the game date the un-tick took did not come back")
        self.assertEqual(((o["ev"] or {}).get("sightings") or [{}])[0].get("reel"), "reel_fixture",
                         "the sightings the un-tick took did not come back")
        self.assertEqual(o["restored"], 1, "the vault removal the un-tick made was not undone")
        self.assertIsNone(o["again"], "one un-tick bought two redos")

    def test_outside_the_window_a_retick_is_a_new_find(self):
        self.assertIsNone(self.rows["late"]["take"], "a re-tick past the window brought back a date the read may have been wrong about")
        self.assertIsNone(self.rows["none"]["take"], "a tick with no un-tick before it was treated as a redo")

    def test_only_the_unticks_own_removal_is_ever_undone(self):
        o = self.rows["other-removal"]
        self.assertEqual(o["restored"], 0, "the redo undid a removal that was not the un-tick's own")
        self.assertEqual(o["journal"], [777, 900], "the removal journal was changed")
        self.assertIn("another removal", (o["vault"] or {}).get("why", ""), "the vault part of the redo was skipped in silence")

    def test_the_evidence_door_never_writes_over(self):
        o = self.rows["put"]
        self.assertFalse(o["kept"], "the door reported writing over a row a later read wrote")
        self.assertEqual(o["after"], {"sightings": [{"reel": "later_read"}]}, "a later read's sightings were overwritten")
        self.assertFalse(o["junk"])
        self.assertEqual(o["raw"], "{not json", "a store that would not parse was written over")


class TheTickHandlerIsJoinedToTheRedo(unittest.TestCase):
    """toggleOwned's uniques branch, read from its code in order (the 140-line handler cannot run outside the page)."""

    def test_keep_before_delete_take_before_stamp_restore_after_write(self):
        src = _src()
        i = src.index("function toggleOwned(name, prov) {")
        j = src.index("  } else {\n    /* 2026-08-20 — THIS BRANCH IS DELIBERATELY UNGUARDED.", i)
        body = "\n".join(ln for ln in src[i:j].split("\n") if not ln.lstrip().startswith(("//", "/*", "*")))
        at = {}
        for key, needle in (("keep", "window._tickRedoKeep(name, fl[name])"),
                            ("delete", "delete fl[name];"),
                            ("note", "_rdo.vaultTs = _vrUT.ts"),
                            ("take", "_rdt = window._tickRedoTake ? window._tickRedoTake(name) : null"),
                            ("stamp", "else fl[name] = window._grailStamp ? window._grailStamp() : new Date().toLocaleString();"),
                            ("write", "window.LSR.setItem('d2r_foundLog', JSON.stringify(fl));"),
                            ("restore", "window._tickRedoRestore(name, _rdt)")):
            self.assertEqual(body.count(needle), 1, "the uniques branch no longer does this once, in code: %s" % needle)
            at[key] = body.index(needle)
        self.assertLess(at["keep"], at["delete"], "the un-tick deletes before it keeps")
        self.assertLess(at["take"], at["stamp"], "the tick stamps a new date before it asks for the redo")
        self.assertLess(at["write"], at["restore"], "the redo restores before the found date is written")
        self.assertTrue(re.search(r"_vrUT = window\.vaultRemove\(\[name\][^\n]*\n[^\n]*\n\s*if \(_rdo && _vrUT && _vrUT\.ts\)", body),
                        "the un-tick does not note its OWN removal right after making it")


if __name__ == "__main__":
    unittest.main(verbosity=2)
