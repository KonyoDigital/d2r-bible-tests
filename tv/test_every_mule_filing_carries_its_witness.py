# -*- coding: utf-8 -*-
"""#246 L6 — EVERY MULE FILING CARRIES ITS WITNESS, AND THERE IS ONE DOOR.

His words, 2026-09-26: the vault "should still be doing it job.. meaning locking the items and reading it whenever
it can after witnessed verify it it can automatically tag it in to the mule account", and "all the items getting
vaulted and vaulted by AI READERS or manually should be to the dedicated mules alone".

THE DEFECT: the mule map (d2r_muleAssign) stored a bare string per item and had about forty writers, none of which
asked for a witness. The only record of who filed what was a 400-row, name-keyed ledger whose `source` field is
overwritten in place — 10 of the 173 had already lost their author. "From what picture is this here?" had no
answer on the store.

WHAT THIS LAW HOLDS:
  · NODE HALF — window.vaultFile, CUT from bible.html between its own markers and run in node (never re-typed):
      a call with no witness files nothing; a manual declaration {by:'hand', at, where} files; a .d2s read files
      only when it verified; a stash sighting files only with VAULT_WITNESS_MIN distinct looks each carrying its
      OWN frame and conf ≥ VAULT_WITNESS_FLOOR (one look, a frameless look, an unsure look, two frames of one
      session, a bare session folded into its own re-look, and a gate that held it — all refused); an
      equipment / inventory / belt / cube sighting is refused as the MAIN's (main:true); a MAIN-locked name is
      refused even by hand; a home he chose is never overridden except by his hand naming a home; a MOVE carries
      the row it has. After every call, EVERY key in the map has a d2r_vaultProv row, and every row carries
      mule, main, holder, source, at, sessions, looks, by and ver.
  · #246 review — A HAND SAYS WHEN. {by:'hand', at:'not a date'} was filed with at = 'not a date', and a hand with
    no `at` was stamped with the door's own clock; both are refused now, and a real time is kept. The row carries
    the spec's `main` — the MAIN he declared at the moment of filing, null (UNKNOWN) when he has not.
  · THE TAG (W5) — window._vaultProvSay reads d2r_vaultProv in MP_SRC_SAY's words: "placed by hand (where)",
    "witnessed in your stash × 2 looks", "from a .d2s (char)", and a filing with no row says NO WITNESS, loudly.
  · THE BARS ARE HIS, ONCE — the board's VAULT_WITNESS_FLOOR / VAULT_WITNESS_MIN equal vault_retro's
    KEEP_CONF_FLOOR / KEEP_MIN_WITNESSES (his 2-look ruling of 2026-09-07). A second copy that drifted would
    let the board file what the sweep refused.
  · SOURCE HALF — outside the vaultFile block there is NO `assign[...] =` anywhere in bible.html's code (comments
    stripped, bounded), and every wholesale `assign =` is on a NAMED exception list with its reason.
RED_PROOF below.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
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
BEGIN = "⟦#246 VAULTFILE BEGIN⟧"
END = "⟦#246 VAULTFILE END⟧"
SAY_START = "  var MP_SRC_SAY = { manual: 'placed by hand'"

#: wholesale re-binds of the map, each with its reason. Anything else that assigns the map is a second door.
WHOLESALE_OK = {
    "var assign = load(AK, {});": "the boot read of the store itself — the map as it was saved, not a filing",
    "assign={}; try { _provWrite({}); } catch(e){} saveA(); renderVault();":
        "vaultReset — his confirmed click clears every filing AND every witness row; a removal, never a filing",
}


def _src():
    with io.open(BIBLE, encoding="utf-8") as f:
        return f.read()


def _door(s):
    assert s.count(BEGIN) == 1 and s.count(END) == 1, "the vaultFile markers are not unique (%d, %d)" % (
        s.count(BEGIN), s.count(END))
    i = s.rfind("\n", 0, s.index(BEGIN)) + 1
    j = s.index("\n", s.index(END)) + 1
    return s[i:j]


def _say_line(s):
    assert s.count(SAY_START) == 1, "MP_SRC_SAY is not where this law cuts it (%d)" % s.count(SAY_START)
    i = s.index(SAY_START)
    return s[i:s.index("};\n", i) + 3]


HARNESS = r"""
var window = globalThis, STORE = {};
window.LSR = { getItem: function(k){ return Object.prototype.hasOwnProperty.call(STORE, k) ? STORE[k] : null; },
               setItem: function(k, v){ STORE[k] = String(v); }, removeItem: function(k){ delete STORE[k]; } };
window.D2R_BUILD = { id: 'vLAW' };
var assign = {}, owned = new Set();
function saveA(){ window.LSR.setItem('d2r_muleAssign', JSON.stringify(assign)); }
function persistOwned(){ window.LSR.setItem('d2r_owned', JSON.stringify(Array.from(owned))); }
var ROSTER = { 'uni-armor': { id: 'uni-armor', name: 'UNI-ARMOR' }, 'uni-small': { id: 'uni-small', name: 'UNI-SMALL' },
               'shared': { id: 'shared', name: 'SHARED STASH' } };
function muleById(id){ return ROSTER[id] || null; }
function suggestMule(n){ return { id: 'uni-armor', why: 'the law routes everything to UNI-ARMOR' }; }
function isSharedStash(n){ return false; }
function ownedPool(){ return Array.from(owned); }
var LOCKS = {};
window._laneLocked = function(n){ return LOCKS[n] || ''; };
window._mainTag = function(){ return 'MAIN (name UNKNOWN)'; };
"""

BODY = r"""
var OUT = { calls: [], bad: [] };
var L2 = [{ session: 's_a', frame: 'f_a.jpg', conf: 0.9 }, { session: 's_b', frame: 'f_b.jpg', conf: 0.85 }];
function call(label, name, w, o){
  var before = JSON.stringify(assign);
  var r = window.vaultFile(name, w, o);
  var prov = JSON.parse(window.LSR.getItem('d2r_vaultProv') || '{}');
  Object.keys(assign).forEach(function(k){ if (!prov[k]) OUT.bad.push(label + ': ' + k + ' is filed with NO witness row'); });
  Object.keys(prov).forEach(function(k){
    var row = prov[k];
    ['mule', 'main', 'holder', 'source', 'at', 'sessions', 'looks', 'by', 'ver'].forEach(function(f){
      if (!Object.prototype.hasOwnProperty.call(row, f)) OUT.bad.push(label + ': ' + k + '\'s row has no ' + f); });
  });
  OUT.calls.push({ label: label, ok: !!(r && r.ok), mode: r && r.mode, refused: r && r.refused, main: !!(r && r.main),
                   why: r && r.why, changed: before !== JSON.stringify(assign), mule: assign[name] || null });
  return r;
}
call('no witness', 'A', null);
call('an empty object', 'A', {});
call('hand, no where', 'A', { by: 'hand', at: '2026-09-26T00:00:00Z' });
call('hand, a time that is no date', 'H1', { by: 'hand', at: 'not a date', where: 'the mule window' });
call('hand, no time', 'H1', { by: 'hand', where: 'the mule window' });
call('hand', 'B', { by: 'hand', at: '2026-09-26T00:00:00Z', where: 'the mule window' });
call('d2s unverified', 'C', { source: 'd2s', file: 'x.d2s', char: 'Hero', verify: { ok: false } });
call('d2s', 'C', { source: 'd2s', file: 'x.d2s', char: 'Hero', verify: { ok: true } });
call('stash, one look', 'D', { lane: 'stash', sessions: [L2[0]] });
call('stash, a frameless look', 'D', { lane: 'stash', sessions: [L2[0], { session: 's_c', frame: null, conf: 0.9 }] });
call('stash, an unsure look', 'D', { lane: 'stash', sessions: [L2[0], { session: 's_c', frame: 'f_c.jpg', conf: 0.0 }] });
call('stash, a look with no conf', 'D', { lane: 'stash', sessions: [L2[0], { session: 's_c', frame: 'f_c.jpg' }] });
call('stash, two frames of ONE session', 'D', { lane: 'stash', sessions: [L2[0], { session: 's_a', frame: 'f_a2.jpg', conf: 0.9 }] });
call('stash, a bare session folded into its re-look', 'D', { lane: 'stash', sessions: [
  { session: 's_a', witness: 's_a#0', frame: 'f_a.jpg', conf: 0.9 }, { session: 's_a', frame: 'f_a3.jpg', conf: 0.9 }] });
call('stash, the gate held it', 'D', { lane: 'stash', sessions: L2, gate: { pass: false, why: 'held' } });
call('equipment', 'D', { lane: 'equipment', sessions: L2 });
call('inventory', 'D', { lane: 'inventory', sessions: L2 });
call('belt', 'D', { lane: 'belt', sessions: L2 });
call('the cube', 'D', { lane: 'cube', sessions: L2 });
call('a lane that is no container', 'D', { lane: 'ground', sessions: L2 });
call('stash, two real looks', 'D', { lane: 'stash', sessions: L2, gate: { pass: true, why: 'two looks', witnesses: 2, wilson: 0.34 } });
LOCKS['E'] = 'equipment';
call('a MAIN-locked name, by hand', 'E', { by: 'hand', at: '2026-09-26T00:00:00Z', where: 'the vault manager' }, { mule: 'uni-small' });
call('his hand re-files', 'B', { by: 'hand', at: '2026-09-26T01:00:00Z', where: 'the vault manager' }, { mule: 'uni-small' });
call('never override his home', 'B', { lane: 'stash', sessions: L2 });
call('a reader never replaces his hand at the same home', 'C2', { by: 'hand', at: '2026-09-26T02:00:00Z', where: 'the mule window' });
call('the reader arrives later', 'C2', { lane: 'stash', sessions: L2 });
call('a move of a filing', 'D', null, { move: true, mule: 'shared' });
call('a move of nothing', 'Q', null, { move: true, mule: 'shared' });
window.mainCharacter = function(){ return { name: 'Lawhero', level: 90 }; };
call('hand, with his MAIN declared', 'M1', { by: 'hand', at: '2026-09-26T03:00:00+03:00', where: 'the vault manager' });
delete window.mainCharacter;
var prov = JSON.parse(window.LSR.getItem('d2r_vaultProv') || '{}');
OUT.prov = prov;
OUT.map = assign;
OUT.say = { B: window._vaultProvSay('B'), C: window._vaultProvSay('C'), D: window._vaultProvSay('D') };
assign['Z'] = 'uni-armor';
OUT.say.Z = window._vaultProvSay('Z');
OUT.say.nothing = window._vaultProvSay('Nothing Filed');
OUT.none = MP_SRC_SAY.none;
var before = JSON.stringify(STORE);
window._vaultWitnessCheck({ lane: 'stash', sessions: L2 });
OUT.checkIsPure = before === JSON.stringify(STORE);
OUT.floor = window.VAULT_WITNESS_FLOOR; OUT.min = window.VAULT_WITNESS_MIN;
process.stdout.write(JSON.stringify(OUT));
"""


def _drive():
    s = _src()
    prog = HARNESS + _say_line(s) + _door(s) + BODY
    r = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise AssertionError("the shipped door would not execute — UNKNOWN, not passing: %s" % (r.stderr or r.stdout)[-800:])
    return json.loads(r.stdout)


def _code_only(s):
    """bible.html's script text with comments removed — BOUNDED block comments (an unbounded /*.*?*/ over a 7 MB
    file once swallowed a sixth of it), and // line comments only where the // is not inside a string's reach
    (a URL). Newlines are kept so a finding carries a real line number. [[source-reading-guard]]"""
    s = re.sub(r"/\*.{0,12000}?\*/", lambda m: "\n" * m.group(0).count("\n"), s, flags=re.S)
    s = re.sub(r"(?m)(^|[^:'\"\\])//[^\n]*", lambda m: m.group(1), s)
    return s


@unittest.skipIf(NODE is None, "node is absent — this law runs the SHIPPED door; UNMEASURED, not passing")
class EveryMuleFilingCarriesItsWitness(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.out = _drive()
        cls.by = dict((c["label"], c) for c in cls.out["calls"])

    def test_no_filing_ever_stands_without_its_witness_row(self):
        self.assertEqual([], self.out["bad"], "a filing stood without its witness row: %s" % self.out["bad"][:4])

    def test_a_call_with_no_witness_files_nothing(self):
        for label in ("no witness", "an empty object", "hand, no where", "d2s unverified",
                      "hand, a time that is no date", "hand, no time"):
            c = self.by[label]
            self.assertFalse(c["ok"], "%s was accepted: %r" % (label, c))
            self.assertFalse(c["changed"], "%s changed the map" % label)
        self.assertNotIn("H1", self.out["prov"], "a hand with no real time left a witness row")

    def test_a_hand_says_when_and_the_row_names_the_main(self):
        """#246 review — the row's `at` is his time (normalised, never invented), and `main` is the MAIN he declared
        when it was filed, or null — UNKNOWN — when he had not."""
        p = self.out["prov"]
        self.assertIn("not a date", self.by["hand, a time that is no date"]["why"])
        self.assertIn("no time", self.by["hand, no time"]["why"])
        self.assertEqual("2026-09-26T02:00:00.000Z", p["C2"]["at"], "his hand's time was not the row's time: %r" % p["C2"])
        self.assertTrue(self.by["hand, with his MAIN declared"]["ok"], self.by["hand, with his MAIN declared"])
        self.assertEqual("2026-09-26T00:00:00.000Z", p["M1"]["at"], "a time with an offset was not read as that instant")
        self.assertEqual("Lawhero", p["M1"]["main"], "the row does not name the MAIN it is kept apart from: %r" % p["M1"])
        self.assertIsNone(p["C"]["main"], "an undeclared MAIN was written as something other than null (UNKNOWN)")

    def test_each_kind_of_witness_files_with_its_row(self):
        p = self.out["prov"]
        self.assertTrue(self.by["hand"]["ok"], self.by["hand"])
        self.assertEqual("hand", p["B"]["source"])
        self.assertTrue(self.by["d2s"]["ok"], self.by["d2s"])
        self.assertEqual(("d2s", "x.d2s", "Hero"), (p["C"]["source"], p["C"]["file"], p["C"]["char"]))
        self.assertTrue(self.by["stash, two real looks"]["ok"], self.by["stash, two real looks"])
        self.assertEqual(2, len(p["D"]["looks"]), "the row does not keep the looks it was filed on: %r" % p["D"])
        self.assertEqual("stash", p["D"]["source"])
        self.assertIs(True, (p["D"].get("gate") or {}).get("pass"), "the gate's verdict was not kept")
        self.assertEqual(0.34, p["D"].get("wilson"), "the confidence bound was not stamped")
        self.assertEqual("vLAW", p["D"]["ver"])

    def test_a_look_counts_only_on_its_own(self):
        for label in ("stash, one look", "stash, a frameless look", "stash, an unsure look",
                      "stash, a look with no conf", "stash, two frames of ONE session",
                      "stash, a bare session folded into its re-look", "stash, the gate held it"):
            c = self.by[label]
            self.assertFalse(c["ok"], "%s FILED: %r" % (label, c))

    def test_what_the_MAIN_carries_is_never_filed(self):
        for label in ("equipment", "inventory", "belt", "the cube"):
            c = self.by[label]
            self.assertFalse(c["ok"], "%s filed: %r" % (label, c))
            self.assertTrue(c["main"], "%s was refused, but not AS the MAIN's: %r" % (label, c))
        self.assertFalse(self.by["a lane that is no container"]["ok"])
        c = self.by["a MAIN-locked name, by hand"]
        self.assertFalse(c["ok"], "a MAIN-locked name was filed by hand: %r" % c)
        self.assertEqual("locked", c["refused"])

    def test_his_home_is_never_overridden_except_by_his_hand(self):
        self.assertTrue(self.by["his hand re-files"]["ok"])
        self.assertEqual("already", self.by["never override his home"]["mode"])
        self.assertEqual("uni-small", self.by["never override his home"]["mule"], "a reader moved a home his hand chose")
        self.assertEqual("uni-small", self.out["map"]["B"])
        self.assertEqual("hand", self.out["prov"]["C2"]["source"],
                         "a reader witness replaced his hand's row at the same home — a manual placement always wins")
        self.assertEqual("moved", self.by["a move of a filing"]["mode"])
        self.assertEqual("shared", self.out["prov"]["D"]["mule"], "a move did not carry its row along")
        self.assertFalse(self.by["a move of nothing"]["ok"])

    def test_the_tag_reads_the_witness_row(self):
        """W5 — the mule window's source words come from d2r_vaultProv, and an unwitnessed filing says so."""
        say = self.out["say"]
        self.assertTrue(say["B"].startswith("placed by hand"), say)
        self.assertIn("(the vault manager)", say["B"])
        self.assertEqual("from a .d2s (Hero)", say["C"])
        self.assertTrue(say["D"].startswith("witnessed in your stash × 2 looks"), say)
        self.assertEqual(self.out["none"], say["Z"], "a filing with no witness row is not called out")
        self.assertIn("NO WITNESS", say["Z"])
        self.assertEqual("", say["nothing"])
        self.assertTrue(self.out["checkIsPure"], "_vaultWitnessCheck wrote a store — a judge that acts")

    def test_the_bars_are_his_one_ruling(self):
        import vault_retro as VR
        self.assertEqual(VR.KEEP_CONF_FLOOR, self.out["floor"], "the board's look floor drifted from vault_retro's")
        self.assertEqual(VR.KEEP_MIN_WITNESSES, self.out["min"], "the board's look count drifted from his ruling")


class ThereIsOneDoorIntoTheMap(unittest.TestCase):

    def test_no_map_write_outside_the_door(self):
        s = _src()
        d = _door(s)
        rest = s.replace(d, "\n" * d.count("\n"))
        code = _code_only(rest)
        hits = []
        for m in re.finditer(r"\bassign\s*\[[^\]\n]+\]\s*=(?!=)", code):
            ln = code.count("\n", 0, m.start()) + 1
            hits.append("bible.html:%d %s" % (ln, code[m.start():m.start() + 80].split("\n")[0]))
        self.assertEqual([], hits, "a map write outside window.vaultFile — a second door with no witness: %s" % hits[:5])

    def test_every_wholesale_rebind_is_named(self):
        s = _src()
        code = _code_only(s.replace(_door(s), ""))
        found = []
        for m in re.finditer(r"(?<![\w.$])(?:var\s+)?assign\s*=(?![=>])[^\n]*", code):
            line = m.group(0).strip()
            if not any(line.startswith(k) for k in WHOLESALE_OK):
                found.append(line[:120])
        # the unrelated local in a stats function (`var assign=[], outliers=0`) is an ARRAY of its own — named here
        found = [f for f in found if not f.startswith("var assign=[]")]
        self.assertEqual([], found, "an unnamed wholesale re-bind of the mule map: %s" % found[:4])
        for k in WHOLESALE_OK:
            self.assertEqual(1, code.count(k), "a named exception no longer exists — prune WHOLESALE_OK: %r" % k)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#246 W1 - the door writes a filing with no witness row beside it",
        "file": "bible.html",
        "find": "    var pa = _provAll(); pa[nm] = row; _provWrite(pa);\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#246 W1 - a second door: his hand writes the map directly again, around the witness",
        "file": "bible.html",
        "find": "    var _vf = window.vaultFile(name, { by: 'hand', at: new Date().toISOString(), where: 'the vault manager' }, { mule: muleId });\n",
        "replace": "    assign[name]=muleId; saveA(); var _vf = { ok: true };\n",
        "matches": 1,
    },
    {
        "why": "#246 W5 - the tag stops reading the witness row and calls every filing unwitnessed",
        "file": "bible.html",
        "find": "    var r = _provAll()[nm];\n    var S = (typeof MP_SRC_SAY === 'object' && MP_SRC_SAY) ? MP_SRC_SAY : {};\n",
        "replace": "    var r = null;\n    var S = (typeof MP_SRC_SAY === 'object' && MP_SRC_SAY) ? MP_SRC_SAY : {};\n",
        "matches": 1,
    },
    {
        "why": "#246 review - a hand's time is stored unchecked again: 'not a date' becomes the filing's time",
        "file": "bible.html",
        "find": ("      if (!isFinite(atMs)) return { ok: false, why: 'a manual declaration must say WHEN it was made — '\n"
                 "        + (atS ? ('\"' + atS.slice(0, 40) + '\" is not a date') : 'it carried no time') };\n"
                 "      return { ok: true, kind: 'hand', where: wh, at: new Date(atMs).toISOString() };\n"),
        "replace": "      return { ok: true, kind: 'hand', where: wh, at: w.at || null };\n",
        "matches": 1,
    },
    {
        "why": "#246 review - the witness row loses the spec's `main` field (the MAIN the filing is kept apart from)",
        "file": "bible.html",
        "find": "      mule: home, main: _vMainName(), holder: _vHomeName(home),\n",
        "replace": "      mule: home, holder: _vHomeName(home),\n",
        "matches": 1,
    },
    {
        "why": "#246 W3 - the board's look bar drifts from his 2-look ruling",
        "file": "bible.html",
        "find": "  var VAULT_WITNESS_MIN = 2;",
        "replace": "  var VAULT_WITNESS_MIN = 1;",
        "matches": 1,
    },
]
