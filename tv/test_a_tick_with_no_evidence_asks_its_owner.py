# -*- coding: utf-8 -*-
"""REG-3009 (#163, his ruling 2026-10-29 Q6) - A TICK WITH NO EVIDENCE ASKS ITS OWNER: CONFIRM OR CLEAR, NEVER ON ITS OWN.

Dean's board (#169): 132 found-log rows, 117 of them set pieces, all stamped Aug 1, 2026 16:57 - one minute, a bulk tick, not the
seed's dates - beside 98 of 99 runewords. His ruling: keep them until Dean confirms them in the console; a tick with no evidence
asks its owner to confirm or clear it. These are the board's doors (the board owns the stores):
  window._unconfirmedTicks() - every set piece, unique and runeword tick that nothing on the board vouches for (no d2r_foundBy
      row, no banked sightings, no game date; on HIS ledger a row still carrying its seed's own date is his own record);
  window._ticksConfirm(items) - his hand into d2r_foundBy (a runeword's row keyed 'rw:<name>');
  window._ticksClear(items)  - each store's own un-tick (toggleSetPiece / toggleOwned / rwToggleMade), so REG-1638's redo holds.
A shadow refuses both. Nothing on boot or on a timer confirms or clears.

Driven on the whole page in node (vault_page_node), two fixture worlds: OTHER (a claimed board with its own ledger, Dean's
shape) and HIS (his ledger, where the chronicle seeds land). RED_PROOF below.
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

import vault_page_node as VPN  # noqa: E402

D = "Aug 1, 2026 · 16:57"
SEED_WIZ = "Jun 3, 2026 · 12:45"      # _GRAIL_SEED's own date for Wizardspike (checked in the premise)
SET_A, SET_B = "Aldur's Advance (boots)", "Aldur's Rhythm (mace)"


def _prelude(ledger, stores):
    st = {"d2r_ownerClaim": "*", "d2r_ledgerName": ledger}
    st.update(stores)
    return "".join("localStorage.setItem(%s, %s);" % (json.dumps(k), json.dumps(v if isinstance(v, str) else json.dumps(v)))
                   for k, v in st.items())


OTHER = _prelude("Deans-Own-Ledger", {
    "d2r_foundLog": {"Wormskull": D, "Wraith Flight": D, "Witherstring": D, "Wizardspike": SEED_WIZ, SET_A: D, SET_B: D},
    "d2r_setPieces": [SET_A, SET_B],
    "d2r_rwMade": {"Authority": D, "Beast": D},
    "d2r_foundBy": {"Wraith Flight": {"source": "reader", "at": 1}, "rw:Beast": {"source": "hand", "at": 1}},
    "d2r_gameFound": {"Witherstring": "Aug 1, 2026"},
    "d2r_foundEvidence": {SET_B: [{"reel": "r1"}]},
})
HIS = _prelude("KonyoEndgame", {"d2r_foundLog": {"Wormskull": D, "Wizardspike": SEED_WIZ}})

BODY_OTHER = r"""
(function(){
function stores(){ return { fl: JSON.parse(LSR.getItem('d2r_foundLog')), sp: JSON.parse(LSR.getItem('d2r_setPieces')), rw: JSON.parse(LSR.getItem('d2r_rwMade')) }; }
OUT.seedWiz = (window._GRAIL_SEED || {})['Wizardspike'];
OUT.seeds = window._seedsBelongHere === true;
H.flush(600000, 8);
OUT.afterBoot = stores();
OUT.list = _unconfirmedTicks();
OUT.confirm = _ticksConfirm([{ name: 'Wormskull', store: 'uniques' }, { name: 'Authority', store: 'runewords' },
  { name: 'Wraith Flight', store: 'uniques' }, { name: 'Nope', store: 'uniques' }, { name: 'Wormskull', store: 'sets' }]);
OUT.fbW = _foundByOf('Wormskull'); OUT.fbA = _foundByOf('rw:Authority'); OUT.fbAbare = _foundByOf('Authority');
OUT.list2 = _unconfirmedTicks();
OUT.clear = _ticksClear([{ name: %(seta)s, store: 'sets' }, { name: 'Wizardspike', store: 'uniques' },
  { name: 'Beast', store: 'runewords' }, { name: 'Wormskull', store: 'uniques' }]);
OUT.afterClear = stores();
OUT.list3 = _unconfirmedTicks();
toggleOwned('Wizardspike');
OUT.redo = stores().fl['Wizardspike'];
rwToggleMade('Authority');
OUT.fbAafter = _foundByOf('rw:Authority');
window._tvdShadow = { owner: 'Dean' };
OUT.shC = _ticksConfirm([{ name: 'Wizardspike', store: 'uniques' }]);
OUT.shX = _ticksClear([{ name: 'Wizardspike', store: 'uniques' }]);
OUT.shRO = _unconfirmedTicks().readOnly;
window._tvdShadow = null;
OUT.afterShadow = stores();
})();
""" % {"seta": json.dumps(SET_A)}

BODY_HIS = r"""
(function(){
H.flush(600000, 8);
OUT.seeds = window._seedsBelongHere === true;
OUT.list = _unconfirmedTicks();
var fl = JSON.parse(LSR.getItem('d2r_foundLog')), seed = window._GRAIL_SEED || {};
OUT.seeded = Object.keys(fl).filter(function(n){ return seed[n] === fl[n]; }).length;
OUT.rwSeeded = Object.keys(JSON.parse(LSR.getItem('d2r_rwMade'))).length;
})();
"""

_RUNS = {}


def page(which):
    if which not in _RUNS:
        _RUNS[which] = VPN.run(BODY_OTHER if which == "other" else BODY_HIS, prelude=OTHER if which == "other" else HIS,
                               timeout=300)
    return _RUNS[which]


def rows(listing):
    return sorted((r["store"], r["name"]) for r in (listing or {}).get("rows") or [])


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class ATickWithNoEvidenceAsksItsOwner(unittest.TestCase):

    def test_the_premise_the_fixture_board_boots_with_every_tick(self):
        o = page("other")
        self.assertEqual(o["__boot"]["errors"], [], o["__boot"])
        self.assertEqual(o["seedWiz"], SEED_WIZ, "PREMISE: Wizardspike's seed date moved")
        self.assertFalse(o["seeds"], "PREMISE: the fixture board reads as his ledger")
        self.assertTrue(o["list"]["ok"], o["list"])

    def test_nothing_clears_or_confirms_a_tick_on_its_own(self):
        b = page("other")["afterBoot"]
        self.assertEqual(sorted(b["fl"]), sorted(["Wormskull", "Wraith Flight", "Witherstring", "Wizardspike", SET_A, SET_B]),
                         "boot and its timers changed the found log: %r" % b["fl"])
        self.assertEqual(sorted(b["sp"]), sorted([SET_A, SET_B]))
        self.assertEqual(sorted(b["rw"]), ["Authority", "Beast"])

    def test_the_list_is_exactly_the_ticks_nothing_vouches_for(self):
        o = page("other")
        self.assertEqual(rows(o["list"]), [("runewords", "Authority"), ("sets", SET_A), ("uniques", "Wizardspike"),
                                           ("uniques", "Wormskull")], o["list"])
        self.assertEqual((o["list"]["total"], o["list"]["evidenced"]), (8, 4), o["list"])
        dates = dict(((r["store"], r["name"]), r["date"]) for r in o["list"]["rows"])
        self.assertEqual(dates[("sets", SET_A)], D, "a row lost the minute it was stamped")

    def test_confirm_writes_his_hand_and_only_for_an_unvouched_tick(self):
        o = page("other")
        self.assertEqual(sorted(o["confirm"]["confirmed"]), ["Authority", "Wormskull"], o["confirm"])
        skipped = dict((s["name"], s["why"]) for s in o["confirm"]["skipped"])
        self.assertIn("evidence", skipped.get("Wraith Flight", ""), skipped)
        self.assertIn("not ticked", skipped.get("Nope", ""), skipped)
        self.assertEqual(o["fbW"]["source"], "hand")
        self.assertEqual(o["fbA"]["source"], "hand", "a runeword's confirm was not keyed rw:<name>")
        self.assertIsNone(o["fbAbare"], "a runeword's confirm landed on the bare name a unique would read")
        self.assertEqual(rows(o["list2"]), [("sets", SET_A), ("uniques", "Wizardspike")])

    def test_clear_presses_each_stores_own_untick_and_never_an_evidenced_one(self):
        o = page("other")
        self.assertEqual(sorted(o["clear"]["cleared"]), sorted([SET_A, "Wizardspike"]), o["clear"])
        skipped = dict((s["name"], s["why"]) for s in o["clear"]["skipped"])
        self.assertIn("evidence", skipped.get("Beast", ""), skipped)
        self.assertIn("evidence", skipped.get("Wormskull", ""), "a confirmed tick was cleared: %r" % skipped)
        a = o["afterClear"]
        self.assertNotIn(SET_A, a["sp"]); self.assertNotIn(SET_A, a["fl"])
        self.assertNotIn("Wizardspike", a["fl"])
        self.assertIn("Beast", a["rw"]); self.assertIn("Wormskull", a["fl"]); self.assertIn(SET_B, a["sp"])
        self.assertEqual(rows(o["list3"]), [])

    def test_a_clear_is_undone_by_the_cards_own_redo(self):
        self.assertEqual(page("other")["redo"], SEED_WIZ, "re-ticking a cleared unique did not put its date back (REG-1638)")

    def test_a_runeword_unmarked_by_hand_drops_its_confirm(self):
        self.assertIsNone(page("other")["fbAafter"])

    def test_a_shadow_never_confirms_or_clears(self):
        o = page("other")
        self.assertFalse(o["shC"]["ok"]); self.assertIn("read only", o["shC"]["why"])
        self.assertFalse(o["shX"]["ok"]); self.assertIn("read only", o["shX"]["why"])
        self.assertTrue(o["shRO"])
        self.assertIn("Wizardspike", o["afterShadow"]["fl"], "a shadow cleared a tick")

    def test_his_seeded_chronicle_is_his_own_record(self):
        h = page("his")
        self.assertTrue(h["seeds"], "PREMISE: not his ledger")
        self.assertGreater(h["seeded"], 100, "PREMISE: his chronicle seeds did not land")
        self.assertGreater(h["rwSeeded"], 50, "PREMISE: his runeword seeds did not land")
        names = [r["name"] for r in h["list"]["rows"]]
        self.assertIn("Wormskull", names, "his tick with a date of its own and no evidence was not asked about")
        self.assertNotIn("Wizardspike", names, "his seed-dated tick was asked about")
        self.assertLess(len(names), 5, "his seeded chronicle reads as unconfirmed: %r" % names[:10])


RED_PROOF = [
    {"why": "REG-3009 - the found-by row no longer counts as evidence",
     "file": "bible.html",
     "find": "  if (_unconfHas(S.fb, name)) return 'found-by';\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-3009 - his seed-dated ticks read as unconfirmed on his own ledger",
     "file": "bible.html",
     "find": "  if (his && seed && _unconfHas(seed, name) && seed[name] === S.fl[name]) return 'his seed';\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-3009 - a runeword's confirm lands on the bare name",
     "file": "bible.html",
     "find": "    var key = r.store === 'runewords' ? window._UNCONF_RW_KEY(n) : n;\n    var row = window._foundByMark(key,",
     "replace": "    var key = n;\n    var row = window._foundByMark(key,",
     "matches": 1, "needs": "node"},
    {"why": "REG-3009 - clear presses the un-tick of a tick that has evidence",
     "file": "bible.html",
     "find": "    if (r.why) { skipped.push({ name: n, why: 'it has evidence (' + r.why + ') - un-tick it on its own card' }); return; }\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-3009 - a shadow may clear",
     "file": "bible.html",
     "find": "  if (_unconfReadOnly()) return { ok: false, why: \"this is another PC's console, read only - it is cleared on that PC\" };\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-3009 - clear deletes the found-log row itself, so the card's redo has nothing to put back",
     "file": "bible.html",
     "find": "      else if (_unconfGrailUnique(n)) window.toggleOwned(n, { source: 'hand', by: 'cleared', where: \"the console's unconfirmed ticks\" });\n",
     "replace": "      else if (_unconfGrailUnique(n)) { var _f = JSON.parse(window.LSR.getItem('d2r_foundLog')); delete _f[n]; window.LSR.setItem('d2r_foundLog', JSON.stringify(_f)); }\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-3009 - a runeword un-marked by hand keeps its confirm",
     "file": "bible.html",
     "find": "    try { if (typeof window._foundByDrop === 'function') window._foundByDrop(window._UNCONF_RW_KEY(name)); } catch(e){}   // #163 REG-3009 - its confirm goes with it\n",
     "replace": "",
     "matches": 1, "needs": "node"},
]


if __name__ == "__main__":
    unittest.main()
