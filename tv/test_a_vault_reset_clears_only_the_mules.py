# -*- coding: utf-8 -*-
"""2026-09-27 — A VAULT RESET CLEARS ONLY THE MULES. One declared scope, and both reset doors clear through it.

HIS WORDS, 2026-09-27: "it should have not deleted my sets.. just like it didnt delete my uniques or runewords
chronicle. and also it should not delete my runes/gems/materials either.." / "only the stashed items" / "the
mules" / "make sure this logic is architured and wired properly so when reseting again it doesnt reset those and
stays on the mules and items".

MEASURED: he pressed "Reset everything" (window.vaultClearHistory). It cleared d2r_muleAssign 174 -> 0 (wanted)
AND d2r_owned 223 -> 0 and d2r_setPieces 134 -> 0 (NOT wanted; the set pieces were restored by hand at 13:47). It
also cleared magicFinds, copies and unknownReads. The two doors each carried their OWN list of what to wipe, and
the full door's list had grown to reach his testimony.

WHAT THIS LAW HOLDS — the SHIPPED scope block and BOTH shipped doors, cut from bible.html between their own anchors
(never re-typed) and driven in node over a seeded fake store where every ledger he named is populated:
  · THE SCOPE IS DECLARED ONCE and names exactly: the mule assignments (d2r_muleAssign), their witness rows
    (d2r_vaultProv), the Recently-registered log (d2r_intakeLog), the scan ledger (d2r_intakeSeen) and the linked
    folder (IndexedDB d2r_vault_fs/shotdir). Its `keeps` list covers every ledger he said must stay, and no kept
    store is also a cleared one.
  · "Reset assignments" (vaultReset) empties the mule map and its witness rows — and every other key in the
    store is BYTE-IDENTICAL after, the intake log and scan ledger included; the folder stays linked.
  · "Reset vault" (vaultClearHistory) clears only the scope — every non-scope key is byte-identical after, the
    in-memory owned / set pieces / Magic & Rare / copies / unknown reads / runewords are unchanged, the folder
    is unlinked (v569, tests/v569_intake_wedge_reset.spec.ts B still holds).
  · Cancel moves nothing.
  · THE WORDS HE READS come from the scope: the button titles, the confirm and the status line say what is
    cleared and what stays (with counts on the status line), and the assignments door never claims the log.
  · THE SELF-CHECK (the heart): a kept store that changed during the reset is named in the receipt
    (window._vaultLastReset.touched) and on the status line with a warning — never "kept untouched"; a kept
    store that could not be read is UNKNOWN (ok: null, count "?"), never counted as intact.
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
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except ImportError:
    _enable = None

NODE = shutil.which("node")
BIBLE = os.path.join(ROOT, "bible.html")

SCOPE_BEGIN = "⟦VAULT RESET SCOPE BEGIN⟧"
SCOPE_END = "⟦VAULT RESET SCOPE END⟧"
DOOR_RESET = "  window.vaultReset = async function(){\n"
DOOR_FULL = "  window.vaultClearHistory = async function(){\n"
LINES = (
    "  var RK='d2r_muleRoster', AK='d2r_muleAssign';",
    "  function saveA(){ _guardedSet(AK, JSON.stringify(assign)); }",
    "  var PROV_KEY = 'd2r_vaultProv';",
    "  var JOURNAL_KEY='d2r_intakeLog';",
    "  var FOLDER_DB='d2r_vault_fs', FOLDER_KEY='shotdir', SEEN_KEY='d2r_intakeSeen';",
)
PROV_FROM = "  function _provAll(){\n"
PROV_TO = "  /* a filing taken OUT takes its witness row with it"

#: what a reset may clear, by his ruling — pinned here, not read back from the thing under test
SCOPE_STORES = {"assign": "d2r_muleAssign", "prov": "d2r_vaultProv",
                "journal": "d2r_intakeLog", "seen": "d2r_intakeSeen",
                "owned": "d2r_owned"}
FOLDER_IDB = "d2r_vault_fs/shotdir"
DOORS = {"vaultReset": ["assign", "prov"],
         "vaultClearHistory": ["assign", "prov", "journal", "seen", "folder", "owned"]}
#: what no reset may ever touch. d2r_owned is cleared by the FULL door only (his ruling 2026-09-27).
NEVER = ("d2r_setPieces", "d2r_foundLog", "d2r_rwMade", "d2r_magicFinds", "d2r_copies",
         "d2r_unknownReads", "d2r_tally", "d2r_runeStash", "d2r_gemStash", "d2r_materialStash", "d2r_craftStash",
         "d2r_craftBaseStash", "d2r_statues", "d2r_chronicleInbox", "d2r_grailUnfound", "d2r_muleRoster")
#: his own words for what stays — each must be on the confirm he reads
HIS_WORDS = ("set pieces", "runewords", "chronicle", "runes / gems / materials")


def _src():
    with io.open(BIBLE, encoding="utf-8") as f:
        return f.read()


def _line(s, text):
    """One whole line, found by its full text, exactly once. [[source-reading-guard]]"""
    assert s.count(text + "\n") == 1, "%r is not where this law cuts it (%d)" % (text[:60], s.count(text + "\n"))
    return text + "\n"


def _between(s, a, b):
    assert s.count(a) == 1, "anchor %r matched %d times" % (a[:50], s.count(a))
    i = s.index(a)
    j = s.find(b, i)
    assert j > i, "end anchor %r not found after %r" % (b[:50], a[:50])
    return s[i:j]


def _door(s, head):
    """A door from its head to its own closing `  };` line — bounded by the block, never by a byte count."""
    assert s.count(head) == 1, "door %r matched %d times" % (head.strip()[:50], s.count(head))
    i = s.index(head)
    j = s.index("\n  };\n", i) + len("\n  };\n")
    return s[i:j]


def _scope(s):
    assert s.count(SCOPE_BEGIN) == 1 and s.count(SCOPE_END) == 1, "the scope markers are not unique (%d, %d)" % (
        s.count(SCOPE_BEGIN), s.count(SCOPE_END))
    i = s.rfind("\n", 0, s.index(SCOPE_BEGIN)) + 1
    j = s.index("\n", s.index(SCOPE_END)) + 1
    return s[i:j]


def _guard(s):
    """2026-09-29 - the vault module's unreadable-store guard, cut from the shipped page (saveA now writes through it)."""
    start, end = "  var _muleUnread = {};", "  window._muleStoreUnread = function(k){ return _muleUnread[k || AK] || null; };"
    i = s.rfind("\n", 0, s.index(start)) + 1
    return s[i:s.index(end, i) + len(end)] + "\n"


def _pieces(s):
    return (_guard(s) + "".join(_line(s, t) for t in LINES) + _between(s, PROV_FROM, PROV_TO)
            + _scope(s) + _door(s, DOOR_RESET) + _door(s, DOOR_FULL))


HARNESS = r"""
var window = globalThis, STORE = {}, IDB = {}, UNLINKS = 0, CONFIRMS = [], STATUS = [], INFO = [], ANSWER = true, THROW_ON = {};
window.LSR = {
  getItem: function(k){ if (THROW_ON[k]) throw new Error('store unreadable'); return Object.prototype.hasOwnProperty.call(STORE, k) ? STORE[k] : null; },
  setItem: function(k, v){ STORE[k] = String(v); },
  removeItem: function(k){ delete STORE[k]; } };
console.info = function(){ INFO.push(Array.prototype.join.call(arguments, ' ')); };
var BTN = { 'button[onclick="window.vaultReset()"]': { title: 'static' },
            'button[onclick="window.vaultClearHistory()"]': { title: 'static' } };
var REPORT = { hidden: false, innerHTML: 'Last scan: 3 read' };
var document = { querySelector: function(sel){ return BTN[sel] || null; },
                 getElementById: function(id){ return id === 'vault-intake-report' ? REPORT : null; } };
window.document = document;
window.uiConfirm = function(msg){ CONFIRMS.push(msg); return Promise.resolve(ANSWER); };
function status(m){ STATUS.push(m); }
function renderVault(){}
function renderJournal(){}
window.renderRoutingLedger = function(){};
window._repaintOwned = function(){};
window._vUnlinkFolder = async function(){ UNLINKS++; delete IDB['d2r_vault_fs/shotdir']; };
var assign = {}, owned = new Set(), setPieces = new Set(), unknownReads = new Set();
function persistOwned(){
  window.LSR.setItem('d2r_owned', JSON.stringify(Array.from(owned)));
  window.LSR.setItem('d2r_magicFinds', JSON.stringify(magicFinds));
  window.LSR.setItem('d2r_unknownReads', JSON.stringify(Array.from(unknownReads)));
  window.LSR.setItem('d2r_copies', JSON.stringify(copies));
  window.LSR.setItem('d2r_multiKeep', JSON.stringify(multiKeep));
}
var magicFinds = {}, copies = {}, rwMade = {}, multiKeep = {};
"""

BODY = r"""
function names(p, n){ var a = []; for (var i = 0; i < n; i++) a.push(p + ' ' + i); return a; }
function obj(list, f){ var o = {}; list.forEach(function(n, i){ o[n] = f(n, i); }); return o; }
function seed(){
  Object.keys(STORE).forEach(function(k){ delete STORE[k]; });
  var filed = names('Filed Unique', 174);
  assign = obj(filed, function(n, i){ return i % 2 ? 'uni-armor' : 'uni-weap'; });
  owned = new Set(names('Owned Unique', 223));
  setPieces = new Set(names('Set Piece', 134));
  unknownReads = new Set(names('Unread', 5));
  magicFinds = obj(names('Magic Keeper', 9), function(){ return { at: '2026-09-20' }; });
  copies = obj(names('Owned Unique', 7), function(){ return 2; });
  rwMade = obj(['Enigma', 'Spirit', 'Insight'], function(){ return 1; });
  multiKeep = { 'Owned Unique 1': 2 };
  STORE['d2r_muleAssign'] = JSON.stringify(assign);
  STORE['d2r_vaultProv'] = JSON.stringify(obj(filed, function(){ return { mule: 'uni-armor', source: 'hand', by: 'hand' }; }));
  STORE['d2r_intakeLog'] = JSON.stringify(names('session', 12).map(function(s, i){ return { ts: i, items: [s] }; }));
  STORE['d2r_intakeSeen'] = JSON.stringify(obj(names('Screenshot', 40), function(){ return 1; }));
  STORE['d2r_owned'] = JSON.stringify(Array.from(owned));
  STORE['d2r_setPieces'] = JSON.stringify(Array.from(setPieces));
  STORE['d2r_unknownReads'] = JSON.stringify(Array.from(unknownReads));
  STORE['d2r_magicFinds'] = JSON.stringify(magicFinds);
  STORE['d2r_copies'] = JSON.stringify(copies);
  STORE['d2r_rwMade'] = JSON.stringify(rwMade);
  STORE['d2r_multiKeep'] = JSON.stringify(multiKeep);
  STORE['d2r_foundLog'] = JSON.stringify(obj(names('Owned Unique', 223), function(){ return '2026-09-01'; }));
  STORE['d2r_grailUnfound'] = JSON.stringify(names('Unticked', 9));
  STORE['d2r_chronicleInbox'] = JSON.stringify([{ name: 'Tyrael\'s Might', status: 'pending' }]);
  STORE['d2r_chronicleInboxLog'] = JSON.stringify([{ name: 'Arachnid Mesh', status: 'applied' }]);
  STORE['d2r_craftMade'] = JSON.stringify([{ recipe: 'Blood Ring', at: '2026-09-10' }]);
  STORE['d2r_runeStash'] = JSON.stringify({ Ber: 2, Jah: 1, Ist: 7 });
  STORE['d2r_gemStash'] = JSON.stringify({ 'Perfect Amethyst': 4 });
  STORE['d2r_materialStash'] = JSON.stringify({ 'Worldstone Shard': 3 });
  STORE['d2r_craftStash'] = JSON.stringify({ 'Blood Ring': 1 });
  STORE['d2r_craftBaseStash'] = JSON.stringify({ 'Ring': 2 });
  STORE['d2r_statues'] = JSON.stringify(['Statue of Rathma']);
  STORE['d2r_tally'] = JSON.stringify({ runs: 412, found: 31 });
  STORE['d2r_tvdTallyLog'] = JSON.stringify([{ ts: 1, n: 3 }]);
  STORE['d2r_muleRoster'] = JSON.stringify([{ id: 'uni-armor', name: 'UNI-ARMOR' }, { id: 'uni-weap', name: 'UNI-WEAPONS' }]);
  STORE['d2r_mulePos'] = JSON.stringify({ 'Filed Unique 3': { x: 1, y: 2 } });
  STORE['d2r_muleEquip'] = JSON.stringify({ 'uni-armor': ['Shako'] });
  STORE['d2r_laneLock'] = JSON.stringify({ 'War Traveler': { lane: 'equipment', sessions: ['a', 'b', 'c'] } });
  STORE['d2r_mainCharacter'] = JSON.stringify({ name: 'Lawhero', source: 'declared' });
  STORE['d2r_vaultRemoved'] = JSON.stringify([{ ts: 5, names: ['Gone Unique'] }]);
  STORE['d2r_gameFound'] = JSON.stringify(['Owned Unique 2']);
  STORE['d2r_wishlist'] = JSON.stringify(['Griffon\'s Eye']);
  STORE['d2r_aLedgerNobodyListedYet'] = '{"future":true}';
  IDB['d2r_vault_fs/shotdir'] = { fake: 'handle' };
  UNLINKS = 0; CONFIRMS.length = 0; STATUS.length = 0; REPORT.hidden = false;
  window._vaultLastReset = undefined;
}
function mem(){
  return { owned: Array.from(owned), setPieces: Array.from(setPieces), unknownReads: Array.from(unknownReads),
           magicFinds: magicFinds, copies: copies, rwMade: rwMade, multiKeep: multiKeep };
}
function snap(){ return { store: JSON.parse(JSON.stringify(STORE)), mem: JSON.parse(JSON.stringify(mem())), idb: Object.keys(IDB) }; }
function run(label, door){
  seed(); var before = snap();
  return window[door]().then(function(){
    return { before: before, after: snap(), assignLeft: Object.keys(assign).length, unlinks: UNLINKS,
             receipt: window._vaultLastReset || null, confirm: CONFIRMS[0] || null,
             status: STATUS.length ? STATUS[STATUS.length - 1] : null, reportHidden: REPORT.hidden };
  });
}
(async function(){
  var OUT = {}, S = window._VAULT_RESET_SCOPE;
  OUT.scope = { clears: {}, doors: JSON.parse(JSON.stringify(S.doors)), keeps: S.keeps.map(function(k){ return k.store; }),
                frozen: Object.isFrozen(S) && Object.isFrozen(S.clears) && Object.isFrozen(S.doors) };
  Object.keys(S.clears).forEach(function(p){ var c = S.clears[p];
    OUT.scope.clears[p] = { store: c.store || null, idb: c.idb || null, later: !!c.later, say: c.say }; });
  OUT.keepSays = S.keeps.map(function(k){ return k.say; });
  OUT.titles = { vaultReset: BTN['button[onclick="window.vaultReset()"]'].title,
                 vaultClearHistory: BTN['button[onclick="window.vaultClearHistory()"]'].title };

  seed(); ANSWER = false; var c0 = snap();
  await window.vaultReset(); await window.vaultClearHistory();
  OUT.cancel = { before: c0, after: snap(), unlinks: UNLINKS, receipt: window._vaultLastReset || null, confirms: CONFIRMS.length };
  ANSWER = true;

  OUT.reset = await run('reset', 'vaultReset');
  OUT.full = await run('full', 'vaultClearHistory');

  /* the corroborator: a writer that reaches a kept store during the reset is NAMED, never read as clean */
  var _realSaveA = saveA;
  saveA = function(){ _realSaveA(); STORE['d2r_setPieces'] = '[]'; };
  OUT.touched = await run('touched', 'vaultReset');
  saveA = _realSaveA;

  /* a kept store that cannot be read is UNKNOWN, never intact */
  THROW_ON['d2r_setPieces'] = 1;
  OUT.unknown = await run('unknown', 'vaultReset');
  delete THROW_ON['d2r_setPieces'];

  OUT.info = INFO.length;
  process.stdout.write(JSON.stringify(OUT));
})().catch(function(e){ process.stderr.write(String((e && e.stack) || e)); process.exit(3); });
"""


def _drive():
    prog = HARNESS + _pieces(_src()) + BODY
    r = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise AssertionError("the shipped reset would not execute - UNKNOWN, not passing: %s"
                             % (r.stderr or r.stdout)[-900:])
    return json.loads(r.stdout)


def _changed(before, after, allowed):
    """Keys whose bytes moved, or that appeared or vanished, outside `allowed`. -> [key]"""
    keys = set(before) | set(after)
    return sorted(k for k in keys if k not in allowed and before.get(k) != after.get(k))


@unittest.skipIf(NODE is None, "node is absent - this law runs the SHIPPED doors; UNMEASURED, not passing")
class AVaultResetClearsOnlyTheMules(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = _drive()

    def test_the_scope_is_declared_once_and_names_exactly_the_mules_and_the_intake_records(self):
        sc = self.o["scope"]
        self.assertEqual(SCOPE_STORES, dict((p, c["store"]) for p, c in sc["clears"].items() if c["store"]),
                         "the reset scope names a store his ruling does not allow: %r" % sc["clears"])
        self.assertEqual({"assign", "prov", "journal", "seen", "folder", "owned"}, set(sc["clears"]))
        self.assertEqual(FOLDER_IDB, sc["clears"]["folder"]["idb"])
        self.assertTrue(sc["clears"]["folder"]["later"], "the folder unlink is not the async step after the check")
        self.assertEqual(DOORS, sc["doors"], "a door clears a different part of the scope than declared")
        self.assertTrue(sc["frozen"], "the scope can be widened at runtime")
        missing = [k for k in NEVER if k not in sc["keeps"]]
        self.assertEqual([], missing, "the self-check does not watch a ledger he said must stay: %s" % missing)
        both = sorted(set(sc["keeps"]) & set(SCOPE_STORES.values()))
        self.assertEqual([], both, "a store is both kept and cleared: %s" % both)

    def test_he_cancels_and_nothing_moves(self):
        c = self.o["cancel"]
        self.assertEqual(2, c["confirms"], "a reset ran without asking him")
        self.assertEqual([], _changed(c["before"]["store"], c["after"]["store"], ()), "a cancelled reset wrote")
        self.assertEqual(c["before"]["mem"], c["after"]["mem"])
        self.assertEqual(0, c["unlinks"])
        self.assertIsNone(c["receipt"], "a cancelled reset left a receipt")

    def test_reset_assignments_clears_only_the_filings(self):
        r = self.o["reset"]
        allowed = ("d2r_muleAssign", "d2r_vaultProv")
        self.assertEqual([], _changed(r["before"]["store"], r["after"]["store"], allowed),
                         "Reset assignments changed a store outside its scope")
        self.assertEqual("{}", r["after"]["store"].get("d2r_muleAssign"), "the mule assignments were not cleared")
        self.assertEqual(0, r["assignLeft"], "the in-memory mule map still holds filings")
        self.assertEqual("{}", r["after"]["store"].get("d2r_vaultProv"), "the witness rows outlived their filings")
        self.assertEqual(r["before"]["mem"], r["after"]["mem"], "Reset assignments reached his in-memory ledgers")
        self.assertEqual(0, r["unlinks"], "Reset assignments unlinked his screenshot folder")
        self.assertIn(FOLDER_IDB, r["after"]["idb"])
        rc = r["receipt"] or {}
        self.assertEqual("vaultReset", rc.get("door"), "the door did not clear through the scope's runner: %r" % rc)
        self.assertIs(True, rc.get("ok"), rc)
        self.assertEqual({"assign": 174, "prov": 174}, rc.get("cleared"))
        self.assertEqual(134, rc["kept"]["d2r_setPieces"])
        self.assertNotIn("d2r_owned", rc.get("cleared") or {}, "Reset assignments cleared the owned list")
        self.assertEqual(r["before"]["store"].get("d2r_owned"), r["after"]["store"].get("d2r_owned"))

    def test_the_vault_reset_clears_only_the_mules_and_the_intake_records(self):
        f = self.o["full"]
        allowed = tuple(SCOPE_STORES.values())
        self.assertEqual([], _changed(f["before"]["store"], f["after"]["store"], allowed),
                         "the vault reset changed a store outside its scope - his sets, uniques, chronicle or stashes")
        a = f["after"]["store"]
        self.assertEqual(("{}", "{}"), (a.get("d2r_muleAssign"), a.get("d2r_vaultProv")))
        self.assertNotIn("d2r_intakeLog", a, "the Recently-registered log survived the vault reset")
        self.assertNotIn("d2r_intakeSeen", a, "the scan ledger survived the vault reset")
        self.assertEqual(0, f["assignLeft"])
        m0, m1 = f["before"]["mem"], f["after"]["mem"]
        for k in ("setPieces", "magicFinds", "copies", "unknownReads", "rwMade", "multiKeep"):
            self.assertEqual(m0[k], m1[k], "the vault reset emptied his in-memory %s" % k)
        self.assertEqual([], m1["owned"], "the full reset left him marked as holding items")
        self.assertEqual("[]", a.get("d2r_owned"), "d2r_owned survived the full reset")
        self.assertEqual(134, len(m1["setPieces"]))
        self.assertEqual(1, f["unlinks"], "the vault reset no longer unlinks the folder (v569)")
        self.assertNotIn(FOLDER_IDB, f["after"]["idb"])
        self.assertTrue(f["reportHidden"], "the last intake report still shows after the reset")
        rc = f["receipt"] or {}
        self.assertEqual("vaultClearHistory", rc.get("door"), rc)
        self.assertIs(True, rc.get("ok"), rc)
        self.assertEqual({"assign": 174, "prov": 174, "journal": 12, "seen": 40, "folder": True,
                          "owned": 223}, rc.get("cleared"))

    def test_the_words_he_reads_say_what_is_cleared_and_what_stays(self):
        says = self.o["scope"]["clears"]
        for door, key in (("vaultReset", "reset"), ("vaultClearHistory", "full")):
            conf = self.o[key]["confirm"] or ""
            title = self.o["titles"][door]
            self.assertNotEqual("static", title, "the %s button's title is not built from the scope" % door)
            for text, where in ((conf, "confirm"), (title, "title")):
                self.assertIn("Clears ONLY: ", text, "%s %s: %r" % (door, where, text))
                for p in DOORS[door]:
                    self.assertIn(says[p]["say"], text, "the %s %s does not say it clears %s" % (door, where, p))
                for w in HIS_WORDS:
                    self.assertIn(w, text.split("Clears ONLY: ", 1)[1].split("Stays untouched: ", 1)[-1],
                                  "the %s %s does not say %r stays" % (door, where, w))
        rconf = self.o["reset"]["confirm"] or ""
        self.assertNotIn(says["journal"]["say"], rconf.split("Stays untouched: ")[0],
                         "Reset assignments claims to clear the intake log")
        self.assertNotIn(says["folder"]["say"], rconf, "Reset assignments claims to unlink the folder")
        st = self.o["full"]["status"] or ""
        for bit in ("mule assignments (174)", "the scan ledger (40)", "kept untouched: ",
                    "✓ owned items (223)", "set pieces (134)", "runes / gems / materials"):
            self.assertIn(bit, st, "the status line after the vault reset does not say %r: %r" % (bit, st))
        stays = st.split("kept untouched: ", 1)[-1]
        self.assertNotIn("✓ owned", stays, "the full reset says the owned list stayed: %r" % st)
        self.assertIn("✓ owned", (self.o["reset"]["confirm"] or "").split("Stays untouched: ", 1)[-1],
                      "Reset assignments no longer says the owned list stays")
        self.assertIn("mule assignments (174)", self.o["reset"]["status"] or "")

    def test_a_kept_store_that_changes_is_named_never_read_as_clean(self):
        t = self.o["touched"]
        rc = t["receipt"] or {}
        self.assertIn("d2r_setPieces", rc.get("touched") or [], "the self-check read a clobbered set list as intact: %r" % rc)
        self.assertIs(False, rc.get("ok"), rc)
        st = t["status"] or ""
        self.assertTrue(st.startswith("⚠"), "a reset that changed a kept store did not warn: %r" % st)
        self.assertIn("d2r_setPieces", st)
        self.assertNotIn("kept untouched", st, "the status line called a changed store untouched")

    def test_a_kept_store_that_cannot_be_read_is_unknown_never_intact(self):
        u = self.o["unknown"]
        rc = u["receipt"] or {}
        self.assertIn("d2r_setPieces", rc.get("unknown") or [], "an unreadable kept store was not called UNKNOWN: %r" % rc)
        self.assertIsNone(rc.get("ok"), "a reset that could not re-read a kept store claimed ok=%r" % rc.get("ok"))
        self.assertIsNone(rc["kept"]["d2r_setPieces"], "an unreadable store was counted as a number")
        st = u["status"] or ""
        self.assertIn("UNKNOWN", st)
        self.assertIn("set pieces (?)", st, "an unreadable count was shown as a number: %r" % st)
        self.assertNotIn("kept untouched", st)
        self.assertEqual("{}", u["after"]["store"].get("d2r_muleAssign"), "an unreadable kept store stopped the reset")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "2026-09-27 - the vault reset empties his set pieces again (setPieces.clear() re-added)",
        "file": "bible.html",
        "find": "    var R = await _vaultResetRun('vaultClearHistory');\n",
        "replace": ("    try { if (typeof setPieces !== 'undefined') setPieces.clear(); } catch(e){}\n"
                    "    var R = await _vaultResetRun('vaultClearHistory');\n"),
        "matches": 1,
    },
    {
        "why": "2026-09-27 - the full reset no longer clears what he is marked as holding",
        "file": "bible.html",
        "find": "      vaultClearHistory: Object.freeze(['assign', 'prov', 'journal', 'seen', 'folder', 'owned'])\n",
        "replace": "      vaultClearHistory: Object.freeze(['assign', 'prov', 'journal', 'seen', 'folder'])\n",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - Reset assignments goes around the scope with its own list again",
        "file": "bible.html",
        "find": "    var R = await _vaultResetRun('vaultReset');\n",
        "replace": "    assign={}; try { _provWrite({}); } catch(e){} saveA(); var R = null;\n",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - the vault reset wipes Magic & Rare again",
        "file": "bible.html",
        "find": "    var R = await _vaultResetRun('vaultClearHistory');\n",
        "replace": ("    try { magicFinds = {}; window.LSR.removeItem('d2r_magicFinds'); } catch(e){}\n"
                    "    var R = await _vaultResetRun('vaultClearHistory');\n"),
        "matches": 1,
    },
    {
        "why": "2026-09-27 - Reset assignments reaches past the filings into the intake log",
        "file": "bible.html",
        "find": "      vaultReset:        Object.freeze(['assign', 'prov']),\n",
        "replace": "      vaultReset:        Object.freeze(['assign', 'prov', 'journal']),\n",
        "matches": 1,
    },
    {
        "why": "v569 - the vault reset leaves the screenshot folder linked",
        "file": "bible.html",
        "find": "      vaultClearHistory: Object.freeze(['assign', 'prov', 'journal', 'seen', 'folder', 'owned'])\n",
        "replace": "      vaultClearHistory: Object.freeze(['assign', 'prov', 'journal', 'seen', 'owned'])\n",
        "matches": 1,
    },
    {
        "why": "the heart - the self-check goes blind: a kept store changed by the reset reads as untouched",
        "file": "bible.html",
        "find": "      else if (now !== was) R.touched.push(k.store);\n",
        "replace": "      else if (false) R.touched.push(k.store);\n",
        "matches": 1,
    },
    {
        "why": "the heart - a kept store that could not be read is reported intact instead of UNKNOWN",
        "file": "bible.html",
        "find": "      if (was === undefined || now === undefined) R.unknown.push(k.store);\n",
        "replace": "      if (false) R.unknown.push(k.store);\n",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - the confirm stops telling him what stays",
        "file": "bible.html",
        "find": "      + '\\n\\nStays untouched: ' + w.keeps.join(' · ') + '.'\n",
        "replace": "",
        "matches": 1,
    },
]
