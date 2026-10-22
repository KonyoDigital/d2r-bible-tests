# -*- coding: utf-8 -*-
"""#185 (REG-2532) - A PERFECT BASE PICKED IN THE PLANNER IS FILED, IN HIS WORLD, AND EVERY LATER ONE IS A COPY.

His 2026-10-13 ruling (REG-2250): a socketable base at, or within one of, its max sockets, or an elite ethereal base,
is a keeper that is muled - never left unfiled, never vendored. GrokBot's V0 triage (2026-10-22, v3784, 2/2 headless):
v3746pb:150 x4 - a 4os Monarch, a 4os Archon Plate, a 5os War Scepter and an eth Berserker Axe all came back
"<base> stays unfiled - a white, superior or low base is not given a mule from its name".

MEASURED on the shipped page in node (not the probe's guess): window._cbPerfectBaseMule was never null for them - it
named "Monarch (4os)", "Archon Plate (4os)", "War Scepter (5os)" and "Eth Berserker Axe (Larzuk base)". The planner
then asked the router, and in the world a spec runs in - the owner's seeded Chronicle, 99 runewords forged, which is
HIS world - suggestMule answers every one "nothing left for it: its runewords are forged -> vendor it". _vpRoute
refused on that advice, and vaultPlannerFile threw the reason away and printed the white-base sentence about a perfect
base. REG-2250 had shipped dead in exactly the world it was ruled for. The early return also skipped the copy count,
the ledger row and the deferred draw every other pick gets.

Now the perfect base is ONE name before anything compares names, it walks the same road as every other pick, and when
the router's only objection is throw-out advice his ruling outranks it: the pick is filed to the SOCKETED mule (the
drawer the router itself names for every socketed keeper) and the sentence says the ruling and what the router said.
Driven on the WHOLE page in node (tv/vault_page_node.py):
  * his world (navigator.webdriver, file:, every runeword forged): each of the four is filed to SOCKETED, on disk and
    in ownedPool, the sentence names the ruling; a plain 0-socket Monarch still stays unfiled in the white-base words;
  * a later open of the same perfect base files copy 2, the same open does not; the open planner is marked to draw on
    close, and the filing writes its ledger row;
  * a roster saved without SOCKETED gets that core locker back (REG-2562, track A's fix round) and the base files there;
  * a fresh install (nothing forged) files it to SOCKETED on the router's own answer, with no ruling override said;
  * the later open's pick re-rolled to 0 sockets (a plain white) takes its copy back on disk, the first filing stays;
  * closing the planner runs its one deferred draw (counted), and every filed perfect base is still filed, owned and
    in ownedPool after it.
RED_PROOF below: the override switched off; the label
not registered as a socketed base (v324); the undo's write removed.
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

#: a board whose roster has every default locker but SOCKETED
NO_SOCKETED = r"""
localStorage.setItem('d2r_muleRoster', JSON.stringify([
  { id: 'sets-major', name: 'SETS-TAL-IK' }, { id: 'sets-rest', name: 'SETS-REST' }, { id: 'uni-weap', name: 'UNI-WEAPONS' },
  { id: 'uni-armor', name: 'UNI-ARMOR' }, { id: 'uni-small', name: 'UNI-SMALL' }, { id: 'runewords', name: 'RUNEWORDS' },
  { id: 'magic-rare', name: 'MAGIC & RARE' }, { id: 'shared', name: 'SHARED STASH' }, { id: 'dupes', name: 'GRAIL-DUPES' },
  { id: 'wip', name: 'WIP' } ]));
"""

BODY = r"""
(function(){
var W = window;
function disk(k){ try { return JSON.parse(W.LSR.getItem(k) || 'null'); } catch (e) { return 'UNREADABLE'; } }
var LEDGER = [];
var realRec = W.kaiChronicleRecord;
W.kaiChronicleRecord = function(row){ try { LEDGER.push(row && (row.name + '|' + row.status + '|' + (row.target || ''))); } catch (e) {}
  return (typeof realRec === 'function') ? realRec.apply(this, arguments) : row; };
function entryOf(name, sockets, eth){
  var d = W._cbDb();
  var code = Object.keys(d.b).find(function(c){ return d.b[c][0] === name; });
  if (!code) throw new Error('no base code for ' + name);
  var e = W._cbEntryFor(W._cbItem('b:' + code));
  e.sockets = sockets; e.eth = !!eth;
  return e;
}
function file(label, e, tok, watch){
  var h = W._cbPerfectBaseMule(e);
  W._vaultPlannerDirty = false;
  var r = W.vaultPlannerFile(e, tok);
  var a = disk('d2r_muleAssign') || {}, c = disk('d2r_copies') || {}, ow = disk('d2r_owned') || [];
  var hn = (h && h.name) || watch || null;   /* `watch` - the keeper label a plain re-roll must still be read under */
  return { label: label, helper: (h && h.name) || null, mode: (r && r.mode) || null, filed: !!(r && r.filed), mule: (r && r.mule) || null,
           why: (r && r.why) || '', home: hn ? (a[hn] || null) : null, copies: hn ? (c[hn] == null ? null : c[hn]) : null,
           copiesMem: hn ? (copies[hn] == null ? null : copies[hn]) : null,
           ownedDisk: hn ? (ow.indexOf(hn) >= 0) : false, inPool: hn ? (W.ownedPool().indexOf(hn) >= 0) : false,
           dirty: W._vaultPlannerDirty === true };
}
W._vaultPlannerOn = true;
OUT.roster = (W._vaultRosterNow() || []).map(function(m){ return m.id; });
OUT.forged = Object.keys(disk('d2r_rwMade') || {}).length;
var res = [];
var S_ = __SCENARIO__;
if (S_ === 'four'){
  res.push(file('4os Monarch', entryOf('Monarch', 4, false), 'tok-a'));
  res.push(file('4os Archon Plate', entryOf('Archon Plate', 4, false), 'tok-b'));
  res.push(file('5os War Scepter', entryOf('War Scepter', 5, false), 'tok-c'));
  res.push(file('eth Berserker Axe', entryOf('Berserker Axe', 0, true), 'tok-d'));
  res.push(file('plain Monarch', entryOf('Monarch', 0, false), 'tok-e'));
} else if (S_ === 'copies'){
  res.push(file('first', entryOf('Monarch', 4, false), 'tok-1'));
  res.push(file('same open', entryOf('Monarch', 4, false), 'tok-1'));
  res.push(file('later open', entryOf('Monarch', 4, false), 'tok-2'));
  /* the later open's pick re-rolled to 0 sockets: the same pick is now a plain white and stops at its sentence */
  res.push(file('later open re-rolled plain', entryOf('Monarch', 0, false), 'tok-2', 'Monarch (4os)'));
} else if (S_ === 'one'){
  res.push(file('4os Monarch', entryOf('Monarch', 4, false), 'tok-a'));
}
OUT.res = res;
OUT.ledger = LEDGER;
/* the planner closes: its one deferred draw runs (renderVault and its prunes), and the filings must still stand. Each
   pick above reset the dirty mark it read, so it is put back as the picks left it; the draw is counted, never assumed. */
W._vaultPlannerDirty = res.some(function(x){ return x.dirty; });
var _rv = W.renderVault, DRAWN = 0;
if (typeof _rv === 'function') W.renderVault = function(){ DRAWN++; return _rv.apply(this, arguments); };
W.vaultPlannerClose();
H.flush();
OUT.drawn = DRAWN;
var a9 = disk('d2r_muleAssign') || {}, o9 = disk('d2r_owned') || [];
OUT.afterClose = res.filter(function(x){ return x.filed; }).map(function(x){
  return { label: x.label, name: x.helper, home: a9[x.helper] || null, ownedDisk: o9.indexOf(x.helper) >= 0,
           inPool: W.ownedPool().indexOf(x.helper) >= 0 };
});
})();
"""

_RUNS = {}


def run(world, scenario):
    key = (world, scenario)
    if key not in _RUNS:
        pre = {"his": AUTOMATED, "no-socketed": AUTOMATED + NO_SOCKETED, "fresh": ""}[world]
        _RUNS[key] = VPN.run(BODY.replace("__SCENARIO__", json.dumps(scenario)), prelude=pre, timeout=300)
    return _RUNS[key]


def row(o, label):
    for r in o.get("res") or []:
        if r.get("label") == label:
            return r
    raise AssertionError("no row %r in %r" % (label, o.get("res")))


RULING = "never vendored"
WHITE = "white, superior or low base"


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class APerfectBaseFilesFromThePlanner(unittest.TestCase):

    def test_0_premise_his_world_has_every_runeword_forged_and_a_socketed_mule(self):
        o = run("his", "four")
        self.assertEqual(o["__boot"]["errors"], [], "a page script did not run in node: %r" % o["__boot"])
        self.assertGreater(o["forged"], 50, "PREMISE: the seeded Chronicle is not forged here - this is not his world")
        self.assertIn("bases", o["roster"], "PREMISE: the default board has no SOCKETED mule")

    def test_1_the_four_perfect_bases_are_filed_to_socketed(self):
        """v3746pb:150 x4 - the spec's own four"""
        o = run("his", "four")
        for label, name in (("4os Monarch", "Monarch (4os)"), ("4os Archon Plate", "Archon Plate (4os)"),
                            ("5os War Scepter", "War Scepter (5os)"), ("eth Berserker Axe", "Eth Berserker Axe (Larzuk base)")):
            r = row(o, label)
            self.assertEqual(r["helper"], name, "the perfect-base helper did not name the keeper: %r" % r)
            self.assertTrue(r["filed"], "a %s is a perfect base and was not filed: %r" % (label, r))
            self.assertEqual(r["mule"], "bases", r)
            self.assertEqual(r["home"], "bases", "the filing did not reach the mule map on disk: %r" % r)
            self.assertTrue(r["ownedDisk"], "the filed perfect base is not in d2r_owned: %r" % r)
            self.assertTrue(r["inPool"], "the filed perfect base is pruned by ownedPool (v324): %r" % r)
            self.assertIn(RULING, r["why"], "the sentence does not say his ruling outranked the vendor advice: %r" % r)
            self.assertNotIn(WHITE, r["why"])

    def test_2_a_plain_white_still_stays_unfiled(self):
        r = row(run("his", "four"), "plain Monarch")
        self.assertIsNone(r["helper"], r)
        self.assertFalse(r["filed"], r)
        self.assertIn(WHITE, r["why"], "a plain 0-socket white lost its own sentence: %r" % r)

    def test_3_a_later_open_files_the_next_copy_and_the_same_open_does_not(self):
        o = run("his", "copies")
        first, same, later = row(o, "first"), row(o, "same open"), row(o, "later open")
        self.assertTrue(first["filed"], first)
        self.assertEqual(same["mode"], "already", "saving the same open again was not 'already': %r" % same)
        self.assertIsNone(same["copies"], "the same open counted a second copy: %r" % same)
        self.assertEqual(same["home"], "bases", "re-saving the same open moved or unfiled the base: %r" % same)
        self.assertEqual(later["mode"], "copy", "a second perfect Monarch in a later open counted no copy: %r" % later)
        self.assertEqual(later["copies"], 2, later)
        self.assertIn("copy 2", later["why"])

    def test_4_the_open_planner_draws_it_on_close_and_the_ledger_records_it(self):
        o = run("his", "four")
        r = row(o, "4os Monarch")
        self.assertTrue(r["dirty"], "the open planner was not told to draw the filed base on close: %r" % r)
        self.assertIn("Monarch (4os)|filed-by-hand|bases", o["ledger"], "the filing wrote no ledger row: %r" % o["ledger"])

    def test_5_a_roster_saved_without_socketed_gets_it_back_and_the_base_files_there(self):
        """REG-2562 (merged V1 round 3): track A's fix round brings a missing core locker back (the v404/v342.5/v360
        way), so a board with no SOCKETED mule cannot be built by seeding a roster any more; the pick files to SOCKETED"""
        o = run("no-socketed", "one")
        self.assertIn("bases", o["roster"], "a roster saved without SOCKETED did not get its core locker back: %r" % o["roster"])
        r = row(o, "4os Monarch")
        self.assertTrue(r["filed"], r)
        self.assertNotIn(WHITE, r["why"], "a perfect base was called a white base again: %r" % r)
        self.assertEqual(r["home"], "bases", r)
        self.assertTrue(r["ownedDisk"], r)

    def test_6_a_fresh_install_files_it_on_the_routers_own_answer(self):
        o = run("fresh", "one")
        r = row(o, "4os Monarch")
        self.assertEqual(o["forged"], 0, "PREMISE: a fresh install has runewords forged")
        self.assertTrue(r["filed"], r)
        self.assertEqual(r["home"], "bases", r)
        self.assertNotIn(RULING, r["why"], "the ruling was said where the router itself named SOCKETED: %r" % r)

    def test_7_a_later_opens_copy_re_rolled_to_a_plain_white_is_taken_back_on_disk(self):
        """the pick that made copy 2 turned back into a plain white: its copy goes, the first filing stays (REG-2530)"""
        o = run("his", "copies")
        r = row(o, "later open re-rolled plain")
        self.assertIsNone(r["helper"], "PREMISE: a 0-socket Monarch was named a perfect base: %r" % r)
        self.assertIn(WHITE, r["why"], "PREMISE: the re-rolled pick did not stop at the white-base sentence: %r" % r)
        self.assertIsNone(r["copiesMem"], "the re-roll left copy 2 in the live count: %r" % r)
        self.assertIsNone(r["copies"], "the re-roll took copy 2 back in the live count only - d2r_copies keeps it and the "
                                       "next load puts it back: %r" % r)
        self.assertEqual(r["home"], "bases", "the re-roll unfiled the perfect base the first open filed: %r" % r)
        self.assertTrue(r["ownedDisk"], r)

    def test_8_the_filings_survive_the_planners_draw_on_close(self):
        """a perfect base kept in a mule that the next render prunes is not kept at all (v324)"""
        o = run("his", "four")
        self.assertGreaterEqual(o.get("drawn", 0), 1, "PREMISE: closing the planner drew nothing - this law would grade no draw")
        after = o.get("afterClose") or []
        self.assertEqual(sorted(x["name"] for x in after),
                         sorted(["Monarch (4os)", "Archon Plate (4os)", "War Scepter (5os)", "Eth Berserker Axe (Larzuk base)"]),
                         "PREMISE: the four filed perfect bases were not all read after close: %r" % after)
        for x in after:
            self.assertEqual(x["home"], "bases", "the draw on close moved or unfiled a perfect base: %r" % x)
            self.assertTrue(x["ownedDisk"], "the draw on close dropped a perfect base from d2r_owned: %r" % x)
            self.assertTrue(x["inPool"], "the draw on close left a perfect base outside ownedPool: %r" % x)


RED_PROOF = [
    {"why": "#185 (REG-2532) - the router's vendor advice refuses a perfect base again, so the planner leaves it unfiled",
     "file": "bible.html",
     "find": "    if (keeper && keeper.home && sg && sg.id === '__throwout' && !sg.unsorted)\n",
     "replace": "    if (false && keeper && keeper.home && sg && sg.id === '__throwout' && !sg.unsorted)\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2532 (v324) - the perfect base is filed without being registered as the socketed base it is, so ownedPool "
            "and the draw on close leave it out",
     "file": "bible.html",
     "find": "        try { if (typeof window._ensureSocketBaseEntry === 'function') window._ensureSocketBaseEntry(nm); } catch (eEn) {}\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2530 - a later open's copy re-rolled away is taken back in the live count only; d2r_copies keeps it",
     "file": "bible.html",
     "find": "    try { persistOwned(); } catch (eCp) {}\n",
     "replace": "",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
