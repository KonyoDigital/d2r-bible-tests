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
  5. v3541 REG-1656 (the #231 seat on 9aa61081) - the caller threw the redo's result away, so a partial redo was silent,
     and a door missing from the page read like a refusal (no vault door said "another removal came after the
     un-tick"). Now: a full redo says nothing; every part that did not come back is named with its OWN reason; a game
     date a later read wrote is never written over; the note lands on the last-tick marker of THIS item only, and the
     last-found bar renders it (the helper driven here, the bar's join read from its code, the pixels looked at).
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
    {"why": "REG-1886 - the un-tick keeps no row, so a misclick re-tick turns the reader's find into a hand tick (The Cat's Eye)",
     "file": "bible.html",
     "find": "        if (fb) r.foundBy = fb; } catch(e){}\n",
     "replace": "        void fb; } catch(e){}\n", "matches": 1},
    {"why": "REG-1886 - the redo writes its old row over a tick made since",
     "file": "bible.html",
     "find": "  if (!m || !k || !row || typeof row !== 'object' || Object.prototype.hasOwnProperty.call(m, k)) return false;\n",
     "replace": "  if (!m || !k || !row || typeof row !== 'object') return false;\n", "matches": 1},
    {"why": "REG-1886 - a row is invented for a caller that named nobody",
     "file": "bible.html",
     "find": "  if (!k || !src) return null;\n",
     "replace": "  if (!k) return null; src = src || 'hand';\n", "matches": 1},
    {"why": "REG-1886 - the found-date sentence never says who ticked it",
     "file": "bible.html",
     "find": "    try { who = (typeof window._foundBySay === 'function') ? window._foundBySay(window._foundByOf(name)) : ''; } catch(e){}\n",
     "replace": "", "matches": 1},
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
     "find": "        out.vault = (last && last.ts === r.vaultTs)\n",
     "replace": "        out.vault = (last)\n", "matches": 1},
    {"why": "REG-1638 - the evidence door writes over a row a later read wrote",
     "file": "bible.html",
     "find": "      if (Object.prototype.hasOwnProperty.call(map, name)) return false;\n      map[name] = row;\n",
     "replace": "      map[name] = row;\n", "matches": 1},
    {"why": "REG-1638 - toggleOwned never asks for the redo: the helpers exist and the tick still stamps a new date",
     "file": "bible.html",
     "find": "      else if ((_rdt = window._tickRedoTake ? window._tickRedoTake(name) : null) && _rdt.found) fl[name] = _rdt.found;   // REG-1638\n",
     "replace": "", "matches": 1},
    {"why": "REG-1656 - the caller throws the redo's result away again: a partial redo is silent",
     "file": "bible.html",
     "find": "        try { window._tickRedoNote(name, _rdOut); } catch(e){} }   // REG-1656 - a partial redo is said on the bar, never silent\n",
     "replace": "        }\n", "matches": 1},
    {"why": "REG-1656 - a vault door missing from the page reads like a refusal again",
     "file": "bible.html",
     "find": "      if (typeof window.vaultRemovalLog !== 'function' || typeof window.vaultRestoreLast !== 'function'){\n"
             "        out.vault = { restored: 0, why: 'the vault door is not on this page' };\n",
     "replace": "      if (false){\n", "matches": 1},
    {"why": "REG-1656 - the redo writes its old game date over one a later read wrote",
     "file": "bible.html",
     "find": "      else if (Object.prototype.hasOwnProperty.call(gm, name)) miss('the game date', 'a later read wrote one - kept');\n",
     "replace": "", "matches": 1},
    {"why": "REG-1656 - the note lands on no marker: the bar has nothing to say",
     "file": "bible.html",
     "find": "    if (say) lt.redo = say; else delete lt.redo;\n",
     "replace": "    void say;\n", "matches": 1},
    {"why": "REG-1656 - the bar says one item's partial redo under another item's name",
     "file": "bible.html",
     "find": "  if (!lt || lt.n !== last || lt.k !== kind || !lt.redo) return '';\n",
     "replace": "  if (!lt || !lt.redo) return '';\n", "matches": 1},
    {"why": "REG-1656 - the last-found bar never renders the note it was handed",
     "file": "bible.html",
     "find": "      +_rdHtml\n",
     "replace": "\n", "matches": 1},
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
window._ownedProvSourceSay = function(s){   // the vault door's own words, two of them (its map is the page's, not this law's)
  return ({ hand: "your hand", "inbox-auto": "the live reader (auto-accepted)" })[s] || s; };
window.gameFoundFor = function(n){ try { return (JSON.parse(STORE.d2r_gameFound || "{}") || {})[n] || null; } catch(e){ return null; } };
window._gameStampToLedger = function(at){ return at ? String(at) : ""; };
const esc = function(x){ return String(x).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); };
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
// 5. REG-1656 - what did not come back is said, with its own reason
function untick(){
  g = JSON.parse(STORE.d2r_gameFound); delete g[N]; STORE.d2r_gameFound = JSON.stringify(g);
  e = JSON.parse(STORE.d2r_foundEvidence); delete e[N]; STORE.d2r_foundEvidence = JSON.stringify(e);
}
seed();
r = window._tickRedoKeep(N, "Sep 30, 2026 · 01:13", T0); r.vaultTs = 777; JOURNAL.push({ ts: 777, names: [N] }); untick();
rest = window._tickRedoRestore(N, window._tickRedoTake(N, T0 + 3000));
out({ case: "full-say", missed: rest.missed, say: window._tickRedoSay(rest) });
seed();
r = window._tickRedoKeep(N, "x", T0); r.vaultTs = 777;
JOURNAL.push({ ts: 777, names: [N] }); JOURNAL.push({ ts: 900, names: ["Shako"] }); untick();
rest = window._tickRedoRestore(N, window._tickRedoTake(N, T0 + 3000));
out({ case: "other-say", missed: rest.missed, say: window._tickRedoSay(rest) });
seed();
r = window._tickRedoKeep(N, "x", T0); r.vaultTs = 777; JOURNAL.push({ ts: 777, names: [N] }); untick();
const _vrl = window.vaultRestoreLast; delete window.vaultRestoreLast;
rest = window._tickRedoRestore(N, window._tickRedoTake(N, T0 + 3000));
window.vaultRestoreLast = _vrl;
out({ case: "no-door", missed: rest.missed, restored: RESTORED });
seed();
r = window._tickRedoKeep(N, "x", T0); untick();
STORE.d2r_gameFound = JSON.stringify({ [N]: { at: "Oct 1, 2026", by: "a later read", n: 1 } });
rest = window._tickRedoRestore(N, window._tickRedoTake(N, T0 + 3000));
out({ case: "later-game", missed: rest.missed, game: JSON.parse(STORE.d2r_gameFound)[N] });
seed();
STORE.d2r_lastTick = JSON.stringify({ n: N, k: "uni", ms: 1 });
const other = { missed: [{ what: "the vault entry", why: "another removal came after the un-tick - put it back from the vault removal list" }] };
const n1 = window._tickRedoNote(N, other), m1 = JSON.parse(STORE.d2r_lastTick);
const n2 = window._tickRedoNote("Shako", other), m2 = JSON.parse(STORE.d2r_lastTick);
const n3 = window._tickRedoNote(N, { missed: [] }), m3 = JSON.parse(STORE.d2r_lastTick);
out({ case: "note", n1: n1, m1: m1, n2: n2, m2: m2, n3: n3, m3: m3,
      html: window._tickRedoMissHtml(m1, N, "uni", esc), htmlOther: window._tickRedoMissHtml(m1, "Shako", "uni", esc),
      htmlSet: window._tickRedoMissHtml(m1, N, "set", esc), htmlClean: window._tickRedoMissHtml(m3, N, "uni", esc) });
// 6. REG-1886 (#118) - who made the tick: kept by the un-tick, put back by the redo, never over a later tick's row
const READER = { source: "inbox-auto", by: "tvVaultRegister", at: 1 };
seed();
STORE.d2r_foundBy = JSON.stringify({ [N]: READER });
r = window._tickRedoKeep(N, "Sep 30, 2026 · 01:13", T0); window._foundByDrop(N); untick();
rest = window._tickRedoRestore(N, window._tickRedoTake(N, T0 + 3000));
out({ case: "who-redo", rest: rest, row: window._foundByOf(N) });
seed();
STORE.d2r_foundBy = JSON.stringify({ [N]: READER });
r = window._tickRedoKeep(N, "x", T0); window._foundByDrop(N); untick();
window._foundByMark(N, { source: "hand", by: "toggleOwned", where: "the item card tick" }, T0 + 2000);
rest = window._tickRedoRestore(N, window._tickRedoTake(N, T0 + 3000));
out({ case: "who-later", missed: rest.missed, row: window._foundByOf(N) });
seed();
const noOne = window._foundByMark(N, {}, T0), noRow = STORE.d2r_foundBy === undefined;
STORE.d2r_foundBy = "{not json";
const badStore = window._foundByMark(N, { source: "hand" }, T0);
out({ case: "who-mark", noOne: noOne, noRow: noRow, badStore: badStore, raw: STORE.d2r_foundBy });
seed();
STORE.d2r_foundBy = JSON.stringify({ [N]: { source: "hand", by: "the Forge", where: "his tick in the Forge", at: 5 } });
const longSay = window._chipFoundDate(N, "Sep 30, 2026 · 23:15", true);
const chipSay = window._chipFoundDate(N, "Sep 30, 2026 · 23:15", false);
STORE.d2r_gameFound = JSON.stringify({});
const longNoGame = window._chipFoundDate(N, "Sep 30, 2026 · 23:15", true);
const chipNoGame = window._chipFoundDate(N, "Sep 30, 2026 · 23:15", false);
STORE.d2r_foundBy = JSON.stringify({});
const nobody = window._chipFoundDate(N, "Sep 30, 2026 · 23:15", true);
out({ case: "who-say", longSay: longSay, chipSay: chipSay, longNoGame: longNoGame, chipNoGame: chipNoGame, nobody: nobody,
      say: window._foundBySay({ source: "inbox-auto", by: "tvVaultRegister" }) });
"""


@unittest.skipIf(NODE is None, "node is not on this PC - the page code cannot be driven here: UNMEASURED, not a pass")
class AnUntickThenARetickIsOneMisclick(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src = _src()
        code = "\n".join([_between(src, "/* ⟦FOUND BY BEGIN⟧", "/* ⟦FOUND BY END⟧ */"),
                          _between(src, "/* ⟦TICK REDO BEGIN⟧", "/* ⟦TICK REDO END⟧ */"),
                          _cut_fn(src, "  window._chipFoundDate = function(name, ledgerStamp, long){"),
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


    # ── REG-1656 — a partial redo is said, with each part's own reason ─────────────────────────────────────────────

    def test_a_full_redo_says_nothing(self):
        o = self.rows["full-say"]
        self.assertEqual(o["missed"], [], "a redo that put everything back still listed a miss")
        self.assertEqual(o["say"], "")

    def test_a_vault_part_that_could_not_come_back_is_said(self):
        o = self.rows["other-say"]
        self.assertEqual(o["missed"], [{"what": "the vault entry", "why": "another removal came after the un-tick",
                                        "do": "put it back from the vault removal list"}], "the refusal was not carried out")
        # the Grok eye on its pixels: the thing to DO is its own sentence, never buried in the reason's parenthesis
        self.assertEqual(o["say"], "not put back: the vault entry (another removal came after the un-tick). "
                                   "Put it back from the vault removal list.", o["say"])

    def test_a_missing_door_is_said_as_a_missing_door(self):
        o = self.rows["no-door"]
        self.assertEqual(o["restored"], 0)
        self.assertEqual([m["why"] for m in o["missed"]], ["the vault door is not on this page"],
                         "a door missing from the page was said as something else: %r" % o["missed"])

    def test_the_redo_never_writes_over_a_later_game_date(self):
        o = self.rows["later-game"]
        self.assertEqual((o["game"] or {}).get("at"), "Oct 1, 2026", "the redo wrote its old date over a later read's")
        self.assertEqual(o["missed"], [{"what": "the game date", "why": "a later read wrote one - kept"}])

    def test_the_note_lands_on_its_own_items_marker_and_the_bar_says_it(self):
        o = self.rows["note"]
        self.assertTrue(o["n1"])
        self.assertTrue(str(o["m1"].get("redo", "")).startswith("not put back: the vault entry"), o["m1"])
        self.assertFalse(o["n2"], "another item's tick took this item's note")
        self.assertEqual(o["m2"], o["m1"], "a note for another item changed this item's marker")
        self.assertFalse(o["n3"])
        self.assertNotIn("redo", o["m3"], "a full redo left the old note standing")
        self.assertIn("gf-redo-miss", o["html"])
        self.assertIn("vault removal list", o["html"])
        for k in ("htmlOther", "htmlSet", "htmlClean"):
            self.assertEqual(o[k], "", "the bar would say a note it does not own: %s" % k)


    # ── REG-1886 (#118) — the tick records who made it ─────────────────────────────────────────────────────────────

    def test_the_redo_puts_back_who_found_it(self):
        """The Cat's Eye: read by the live reader at 01:13; un-ticked and re-ticked inside the window. The reader's row
        comes back with the date - the misclick does not become a hand tick."""
        o = self.rows["who-redo"]
        self.assertEqual(o["row"], {"source": "inbox-auto", "by": "tvVaultRegister", "at": 1})
        self.assertTrue(o["rest"]["foundBy"])
        self.assertEqual(o["rest"]["missed"], [])

    def test_a_later_ticks_row_is_kept_and_the_miss_is_said(self):
        o = self.rows["who-later"]
        self.assertEqual(o["row"]["source"], "hand", "the redo wrote its old row over a tick made since")
        self.assertEqual(o["missed"], [{"what": "who found it", "why": "a later tick wrote it - kept"}])

    def test_no_row_is_invented_and_a_broken_store_is_not_written_over(self):
        o = self.rows["who-mark"]
        self.assertIsNone(o["noOne"], "a caller that named nobody got a row anyway")
        self.assertTrue(o["noRow"], "a row was written for a caller that named nobody")
        self.assertIsNone(o["badStore"])
        self.assertEqual(o["raw"], "{not json", "a store that would not parse was written over")

    def test_the_found_date_sentence_says_who(self):
        o = self.rows["who-say"]
        self.assertIn("ticked by your hand (the Forge)", o["longSay"], "the bar does not say who ticked it")
        self.assertIn("ticked by your hand (the Forge)", o["chipSay"], "the chip's hover does not say who")
        self.assertNotIn("ticked by", re.sub(r'title="[^"]*"', "", o["chipSay"]),
                         "the chip printed who in its few characters, not its hover")
        self.assertIn("by your hand (the Forge)", o["longNoGame"])
        self.assertIn('title="ticked by your hand (the Forge)"', o["chipNoGame"])
        self.assertNotIn("ticked by", o["nobody"], "an older tick with no row was given a who")
        self.assertEqual(o["say"], "the live reader (auto-accepted) (tvVaultRegister)")


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
                            ("stamp", "else { fl[name] = window._grailStamp ? window._grailStamp() : new Date().toLocaleString();"),
                            ("write", "window.LSR.setItem('d2r_foundLog', JSON.stringify(fl));"),
                            ("restore", "window._tickRedoRestore(name, _rdt)"),
                            ("said", "window._tickRedoNote(name, _rdOut)")):
            self.assertEqual(body.count(needle), 1, "the uniques branch no longer does this once, in code: %s" % needle)
            at[key] = body.index(needle)
        self.assertLess(at["keep"], at["delete"], "the un-tick deletes before it keeps")
        self.assertLess(at["take"], at["stamp"], "the tick stamps a new date before it asks for the redo")
        self.assertLess(at["write"], at["restore"], "the redo restores before the found date is written")
        self.assertIn("_rdOut = window._tickRedoRestore(name, _rdt)", body, "the redo's result is thrown away (REG-1656)")
        self.assertLess(at["restore"], at["said"], "the note is written before the redo it reports")
        self.assertTrue(re.search(r"_vrUT = window\.vaultRemove\(\[name\][^\n]*\n[^\n]*\n\s*if \(_rdo && _vrUT && _vrUT\.ts\)", body),
                        "the un-tick does not note its OWN removal right after making it")
        # REG-1886 - the un-tick takes the row after keeping it; only a FRESH stamp writes one, never the redo branch
        self.assertEqual(body.count("window._foundByDrop(name)"), 1, "the un-tick never takes who found it (REG-1886)")
        self.assertEqual(body.count("window._foundByMark(name, (prov && prov.source) ? prov :"), 1,
                         "a fresh tick never says who made it (REG-1886)")
        drop = body.index("window._foundByDrop(name)")
        mark = body.index("window._foundByMark(name, (prov && prov.source) ? prov :")
        self.assertLess(at["keep"], drop, "the un-tick drops who found it before the redo keeps it")
        self.assertLess(at["stamp"], mark, "who is written outside the fresh-stamp branch (the redo would be overwritten)")
        self.assertLess(mark, at["write"])


class TheLastFoundBarSaysIt(unittest.TestCase):
    """REG-1656 — the bar asks the helper for its note and renders it (the bar needs the whole page to run)."""

    def test_the_bar_renders_the_helpers_note(self):
        src = _src()
        a = src.index("var _gfLine = window._chipFoundDate(last, fl[last], true);")
        b = src.index("+'</div>';", a)
        bar = src[a:b]
        self.assertEqual(bar.count("window._tickRedoMissHtml(window._lastTick && window._lastTick(), last, kind, esc)"), 1,
                         "the bar never asks for the redo's note")
        self.assertEqual(bar.count("+_rdHtml"), 1, "the bar computes the note and never renders it")


if __name__ == "__main__":
    unittest.main(verbosity=2)
