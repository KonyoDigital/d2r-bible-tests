# -*- coding: utf-8 -*-
"""REG-2535 - A SOCKETED WARLOCK TOME IS A RUNEWORD BASE, NEVER INVENTORY FURNITURE: A PERFECT ONE FILES TO SOCKETED.

The V1 round-3 review of REG-2532 (reproduced on ed832f3d9, the whole page in node): the Warlock's Tome (wa2), Dark Tome
(wa7) and Occult Tome (wac) take 2 sockets and make Rhyme, Splendor and Vigilance. _cbPerfectBaseMule names a 2os one a
perfect base and suggestMule routes it to SOCKETED ('bases') - its own _keepHome already takes 'tome' out of the kit list
- but window.vaultFile refused every one as MAIN inventory furniture: the furniture law matches the WORD 'tome', so
_laneLocked('Tome (2os)') = 'inventory'. The review's sweep of all 1,506 perfect-base candidates in his world: 1,495 filed,
the 11 refused were all tomes - #185's ruling still left them unfiled. [[the-unjoined-end]]

THE RULE: furniture is never socketed. A name carrying the board's own socket label - "(2os)", "(3os low base)", "(Larzuk
base)", the label _ensureSocketBaseEntry registers - is a socketed or Larzuk base, on both copies of the law: bible.html's
_furnitureLocked and tv/inventory_law.is_locked (which the console doctor's MAIN-lock arm asks about the board's own
filings, so a filed tome is not "a MAIN item sitting in a mule" there either). A bare Tome, the Tome of Town Portal, the
Tome of Identify, the Cube and a Key stay furniture.

Driven on the WHOLE page in node (tv/vault_page_node.py) in his world (the owner world: his Chronicle, 99 runewords
forged), real doors:
  * the board's furniture predicate and the MAIN lock answer the socket labels as bases and the kit as kit, and the
    Python law answers every name the same way, from the same pattern (pinned equal, character for character);
  * a planner pick of a 2os Tome, a 2os Dark Tome, an eth 2os Occult Tome and an eth unsocketed Occult Tome files each
    to SOCKETED, owned on disk and in ownedPool, and every filing survives the planner's draw on close;
  * the vault audit does not call a filed socketed tome "kit in a mule" (its safe fix would unfile it).
RED_PROOF below: the board's exemption removed refuses the tomes again; the Python law's removed parts the two copies.
"""
import json
import os
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

import vault_page_node as VPN  # noqa: E402  (the whole page in node)

#: the world a Playwright spec runs in, and the one his own board is: the owner world, his Chronicle seeded
AUTOMATED = r"""
Object.defineProperty(navigator, 'webdriver', { get: function(){ return true; }, configurable: true });
location.protocol = 'file:'; location.href = 'file:///spec/bible.html'; location.origin = 'null'; location.host = ''; location.hostname = '';
"""

#: socket labels (bases) and kit (furniture) - each copy of the law must answer every one the same way
BASES = ("Tome (2os)", "Tome (1os)", "Dark Tome (2os)", "Superior Dark Tome (2os)", "Eth Occult Tome (2os)",
         "Eth Occult Tome (Larzuk base)", "Occult Tome (2os low base)", "Monarch (4os)")
KIT = ("Tome", "Tome of Town Portal", "Tome of Identify", "Horadric Cube", "Key", "Key (3)", "12 Keys", "Wirt's Leg")

BODY = r"""
(function(){
var W = window;
function disk(k){ try { return JSON.parse(W.LSR.getItem(k) || 'null'); } catch (e) { return 'UNREADABLE'; } }
OUT.pattern = W._FURNITURE_SOCKET_LABEL ? W._FURNITURE_SOCKET_LABEL.source : null;
OUT.furn = {}; OUT.lane = {};
__NAMES__.forEach(function(n){ OUT.furn[n] = W._furnitureLocked(n); OUT.lane[n] = W._laneLocked(n); });
function entryOf(code, sockets, eth){
  var d = W._cbDb();
  if (!d.b[code]) throw new Error('no base ' + code + ' in the catalogue');
  var e = W._cbEntryFor(W._cbItem('b:' + code));
  e.sockets = sockets; e.eth = !!eth;
  return e;
}
W._vaultPlannerOn = true;
OUT.forged = Object.keys(disk('d2r_rwMade') || {}).length;
OUT.roster = (W._vaultRosterNow() || []).map(function(m){ return m.id; });
var res = [];
[['wa2', 2, false, 'tok-tome'], ['wa7', 2, false, 'tok-dark'], ['wac', 2, true, 'tok-occult'], ['wac', 0, true, 'tok-occult-0']].forEach(function(x){
  var e = entryOf(x[0], x[1], x[2]);
  var h = W._cbPerfectBaseMule(e);
  var r = W.vaultPlannerFile(e, x[3]);
  var nm = (h && h.name) || null, a = disk('d2r_muleAssign') || {}, ow = disk('d2r_owned') || [];
  res.push({ code: x[0], helper: nm, ok: !!(r && r.ok), filed: !!(r && r.filed), mode: (r && r.mode) || null, mule: (r && r.mule) || null,
             why: (r && r.why) || '', home: nm ? (a[nm] || null) : null, ownedDisk: nm ? ow.indexOf(nm) >= 0 : false,
             inPool: nm ? W.ownedPool().indexOf(nm) >= 0 : false });
});
OUT.res = res;
/* the planner closes: its one deferred draw runs (renderVault and its prunes), counted, never assumed */
var _rv = W.renderVault, DRAWN = 0;
if (typeof _rv === 'function') W.renderVault = function(){ DRAWN++; return _rv.apply(this, arguments); };
W._vaultPlannerDirty = true;
W.vaultPlannerClose();
H.flush();
OUT.drawn = DRAWN;
var a9 = disk('d2r_muleAssign') || {}, o9 = disk('d2r_owned') || [];
OUT.after = res.filter(function(x){ return x.helper; }).map(function(x){
  return { name: x.helper, home: a9[x.helper] || null, ownedDisk: o9.indexOf(x.helper) >= 0, inPool: W.ownedPool().indexOf(x.helper) >= 0 };
});
var au = W._vaultAudit();
OUT.kitInMule = (au && au.findings || []).filter(function(f){ return f.kind === 'kit-in-mule'; }).map(function(f){ return f.item; });
})();
"""

_OUT = {}


def measured():
    if "o" not in _OUT:
        _OUT["o"] = VPN.run(BODY.replace("__NAMES__", json.dumps(list(BASES) + list(KIT))), prelude=AUTOMATED, timeout=300)
    return _OUT["o"]


def _row(o, code, sockets_tok):
    for r in o.get("res") or []:
        if r.get("code") == code and (r.get("helper") or "").endswith(sockets_tok):
            return r
    raise AssertionError("no %s pick ending %r in %r" % (code, sockets_tok, o.get("res")))


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class ASocketedTomeFilesAsABase(unittest.TestCase):

    def test_0_premise_his_world_and_the_socketed_mule(self):
        o = measured()
        self.assertEqual(o["__boot"]["errors"], [], "a page script did not run in node: %r" % o["__boot"])
        self.assertGreater(o["forged"], 50, "PREMISE: the seeded Chronicle is not forged here - this is not his world")
        self.assertIn("bases", o["roster"], "PREMISE: the default board has no SOCKETED mule")
        self.assertEqual(len(o["res"]), 4)
        for r in o["res"]:
            self.assertIsNotNone(r["helper"], "PREMISE: the perfect-base helper did not name a tome keeper: %r" % r)

    def test_1_the_board_answers_a_socket_label_as_a_base_and_kit_as_kit(self):
        o = measured()
        for n in BASES:
            self.assertFalse(o["furn"][n], "%s - a socketed / Larzuk base - is inventory furniture on the board" % n)
            self.assertEqual(o["lane"][n], "", "%s is locked to his MAIN on the board: %r" % (n, o["lane"][n]))
        for n in KIT:
            self.assertTrue(o["furn"][n], "%s is no longer furniture on the board" % n)
            self.assertEqual(o["lane"][n], "inventory", "%s is no longer locked to his MAIN inventory" % n)

    def test_2_the_python_law_answers_every_name_the_same_from_the_same_pattern(self):
        import inventory_law as IL
        o = measured()
        self.assertEqual(o["pattern"], IL.SOCKET_LABEL.pattern,
                         "the board's socket-label pattern and inventory_law.SOCKET_LABEL drifted apart")
        for n in BASES + KIT:
            self.assertEqual(IL.is_locked(n), o["furn"][n],
                             "%s: inventory_law says %r and the board says %r - one law, two answers" % (n, IL.is_locked(n), o["furn"][n]))

    def test_3_a_perfect_tome_pick_files_to_socketed(self):
        o = measured()
        for code, tok in (("wa2", "(2os)"), ("wa7", "(2os)"), ("wac", "(2os)"), ("wac", "(Larzuk base)")):
            r = _row(o, code, tok)
            self.assertTrue(r["ok"] and r["filed"], "a perfect %s was not filed: %r" % (r["helper"], r))
            self.assertNotIn("locked to your MAIN", r["why"], "the door refused a socketed tome as furniture: %r" % r)
            self.assertEqual(r["mule"], "bases", r)
            self.assertEqual(r["home"], "bases", "the filing did not reach the mule map on disk: %r" % r)
            self.assertTrue(r["ownedDisk"], "the filed tome is not in d2r_owned: %r" % r)
            self.assertTrue(r["inPool"], "the filed tome is pruned by ownedPool (v324): %r" % r)

    def test_4_every_filing_survives_the_draw_on_close_and_no_audit_unfiles_it(self):
        o = measured()
        self.assertGreaterEqual(o.get("drawn", 0), 1, "PREMISE: closing the planner drew nothing - this law would grade no draw")
        self.assertEqual(len(o["after"]), 4, o["after"])
        for x in o["after"]:
            self.assertEqual(x["home"], "bases", "the draw on close moved or unfiled a socketed tome: %r" % x)
            self.assertTrue(x["ownedDisk"] and x["inPool"], "the draw on close dropped a socketed tome: %r" % x)
        tomes = [x["name"] for x in o["after"]]
        self.assertEqual([n for n in o["kitInMule"] if n in tomes], [],
                         "the vault audit calls a filed socketed tome kit in a mule - its safe fix would unfile it: %r" % o["kitInMule"])


RED_PROOF = [
    {"why": "REG-2535 - a socketed Warlock tome is inventory furniture on the board again, so the door refuses every perfect one",
     "file": "bible.html",
     "find": "  if (_FURNITURE_SOCKET_LABEL.test(low)) return false;   /* REG-2535 — a socketed or Larzuk base is never furniture */\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2535 - inventory_law locks a socketed tome as furniture again: the console and the board answer one name two ways",
     "file": "inventory_law.py",
     "find": "    if SOCKET_LABEL.search(low):\n        return False    # REG-2535 — a socketed or Larzuk base (\"Tome (2os)\") is never furniture\n",
     "replace": "",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
