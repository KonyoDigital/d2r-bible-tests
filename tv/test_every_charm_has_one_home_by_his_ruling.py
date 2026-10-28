# -*- coding: utf-8 -*-
"""REG-2895 (ACT-4, his ruling 2026-10-28 ~20:00-20:10) - EVERY CHARM HAS ONE HOME, BY ONE RULE, READ AT EVERY DOOR.

His words, in order: charms live "in shared stash/war stash"; "no gheeds no... MF no... those go to charms mmule
dedicated"; "skillers also to the dedicated charm mule"; "grand charms attack rating and resistance charms and faster hit
recovery should be in war stash/share stash also small charms"; large charms "go to the dedicated mule or thrown out
depending on them and the ai item checker logic coded".

Measured on the whole page in node before the fix: a rolled charm routed to MAGIC & RARE ("rolled-name keepers"), a
curated one and Gheed's to UNI-SMALL ("charm/skiller"), and every Magic & Rare register keeper - charms included - was
listed and counted on MAGIC & RARE. No CHARMS locker existed (the "charm mule" in the code was only a comment).

  * the SHARED STASH: an AR, a resist and an FHR grand charm, a resist and a vita small charm, Annihilus, Hellfire Torch;
  * the CHARMS mule (a new core locker, after MAGIC & RARE, put back on a stored roster): Gheed's Fortune, a skiller
    (Lion Branded, Chaotic), a magic-find small (of Good Luck) and grand (Lucky), a curated skiller card, and a large
    charm the AI Item Checker keeps;
  * THROW OUT: a large charm the checker threw (its thrown log); a QUESTION: a large charm it never judged or called
    borderline, a charm whose affix the game's tables do not name for its size, and any charm while the affix table is
    not on the page (UNKNOWN, never a miss);
  * MAGIC & RARE lists no charm; a register charm is listed on the locker the rule homes it on; the checker's keep is
    written onto its keeper; the notes say where charms live; footprints 1x1 / 1x2 / 1x3.
Magic find and skiller are read off the game's affix rows (CB_DB .af), never a typed list.

Driven on the whole page in node (vault_page_node), fixtures only. RED_PROOF below.
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

OLD_ROSTER = [
    {"id": "sets-major", "name": "SETS-TAL-IK", "icon": "x", "note": "a"}, {"id": "sets-rest", "name": "SETS-REST", "icon": "x", "note": "b"},
    {"id": "uni-weap", "name": "UNI-WEAPONS", "icon": "x", "note": "c"}, {"id": "uni-armor", "name": "UNI-ARMOR", "icon": "x", "note": "d"},
    {"id": "uni-small", "name": "UNI-SMALL", "icon": "x", "note": "rings · amulets · jewels · charms"},
    {"id": "runewords", "name": "RUNEWORDS", "icon": "x", "note": "e"}, {"id": "bases", "name": "SOCKETED", "icon": "x", "note": "f"},
    {"id": "magic-rare", "name": "MAGIC & RARE", "icon": "x",
     "note": "skillers · magic / rare charms · jewels · rings · amulets · crafts (rolled-name keepers)"},
    {"id": "shared", "name": "SHARED STASH", "icon": "x", "note": "g"}, {"id": "dupes", "name": "GRAIL-DUPES", "icon": "x", "note": "h"},
    {"id": "wip", "name": "WIP", "icon": "x", "note": "i"},
]
KEEPERS = {
    "Serpent's Large Charm of Vita": {"q": "magic", "base": "Large Charm", "mods": ["+17 to Mana", "+30 to Life"], "verdict": "keep"},
    "Coral Large Charm of Vita": {"q": "magic", "base": "Large Charm", "mods": ["Lightning Resist +7%"], "border": True},
    "Fine Small Charm of Vita": {"q": "magic", "base": "Small Charm", "mods": []},
    "Lion Branded Grand Charm": {"q": "magic", "base": "Grand Charm", "mods": []},
    "Viper Eye": {"q": "rare", "base": "Jewel", "mods": []},
}
SEED = ("localStorage.setItem('d2r_ownerClaim', '*');\n"
        "localStorage.setItem('d2r_muleRoster', %s);\n"
        "localStorage.setItem('d2r_magicFinds', %s);\n"
        "localStorage.setItem('d2r_aicThrownLog', %s);\n") % (
    json.dumps(json.dumps(OLD_ROSTER)), json.dumps(json.dumps(KEEPERS)),
    json.dumps(json.dumps([{"name": "Steel Large Charm", "base": "Large Charm", "q": "magic", "verdict": "toss"}])))
SHARED = ["Steel Grand Charm", "Shimmering Grand Charm", "Grand Charm of Balance", "Shimmering Small Charm", "Small Charm of Vita",
          "Annihilus", "Hellfire Torch", "Small Charm of Vita (20 Life)"]
CHARMS = ["Gheed's Fortune", "Lion Branded Grand Charm", "Chaotic Grand Charm of Greed", "Small Charm of Good Luck",
          "Lucky Grand Charm", "Paladin Combat Skiller (GC)", "Small Charm of Good Luck (7% MF)", "Serpent's Large Charm of Vita"]
ASKED = ["Bronze Large Charm", "Coral Large Charm of Vita", "Glorious Small Charm", "Lucky Small Charm"]
BODY = r"""
(function(){
var W = window;
function ask(n, o){ var s = W.suggestMule(n, o); return s ? [s.id, !!s.unsorted, s.why || ''] : null; }
OUT.r = {};
__NAMES__.forEach(function(n){ OUT.r[n] = ask(n); });
OUT.forcedMule = ask('Annihilus', { _shareForceOut: true });
OUT.sunder = ask('Latent Cold Rupture');
OUT.rare = ask('Viper Eye');
OUT.cells = {};
['Small Charm of Vita', 'Serpent\'s Large Charm of Vita', 'Steel Grand Charm'].forEach(function(n){ var c = W._itemCells(n); OUT.cells[n] = [c.w, c.h]; });
OUT.lists = {};
['magic-rare', 'shared', 'charms', 'uni-small'].forEach(function(id){ OUT.lists[id] = { names: W._muleNamesFor(id), items: W._vaultLockerItems(id) }; });
OUT.roster = JSON.parse(H.RAW.get('d2r_muleRoster') || '[]').map(function(m){ return [m.id, m.note]; });
OUT.charmsEntry = JSON.parse(H.RAW.get('d2r_muleRoster') || '[]').filter(function(m){ return m.id === W.CHARM_MULE; })[0] || null;
OUT.charmMule = W.CHARM_MULE;
OUT.where = W._vaultWhereIs('Lion Branded Grand Charm');
/* the AI Item Checker keeps a large charm: its keeper carries the verdict, and its home is the CHARMS mule */
var j = W.aicJudgeApply({ ok: true, name: 'Garnet Large Charm', base: 'Large Charm', q: 'magic', mods: ['Fire Resist +7%'],
                          verdict: { tier: 'keep', score: 15 } }, { sid: 'law', frameId: 'law' });
OUT.judged = { mule: j && j.mule, verdict: magicFinds['Garnet Large Charm'] && magicFinds['Garnet Large Charm'].verdict };
/* the affix table not on the page: UNKNOWN, never a miss */
var keepDb = W._cbDb; _CHARM_AF = null; W._cbDb = function(){ return null; };
try { OUT.unread = W._charmHome('Shimmering Small Charm'); } catch (e) { OUT.unread = 'THREW ' + e.message; }
W._cbDb = keepDb; _CHARM_AF = null;
})();
""".replace("__NAMES__", json.dumps(SHARED + CHARMS + ASKED + ["Steel Large Charm"]))


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class EveryCharmHasOneHomeByHisRuling(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run(BODY, prelude=SEED, timeout=300)
        cls.r = cls.o["r"]

    def test_the_page_booted(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])

    def test_the_shared_stash_takes_every_other_charm(self):
        for n in SHARED:
            self.assertEqual(self.r[n][0], "shared", "%s did not go to the shared stash: %r" % (n, self.r[n]))
        self.assertIsNone(self.o["sunder"], "a Sunder charm left the shared-stash answer: %r" % self.o["sunder"])

    def test_the_charms_mule_takes_gheeds_mf_skillers_and_kept_large_charms(self):
        for n in CHARMS:
            self.assertEqual(self.r[n][0], "charms", "%s did not go to the CHARMS mule: %r" % (n, self.r[n]))
            self.assertIn("2026-10-28 ruling", self.r[n][2], self.r[n])
        self.assertEqual(self.o["forcedMule"][0], "charms", "a forced-out Annihilus did not reach the one charm mule: %r" % self.o["forcedMule"])

    def test_a_large_charm_follows_the_checker_or_is_asked(self):
        self.assertEqual(self.r["Steel Large Charm"][0], "__throwout", "a large charm the checker threw: %r" % self.r["Steel Large Charm"])
        for n in ASKED:
            self.assertIsNone(self.r[n][0], "%s was given a home by a guess: %r" % (n, self.r[n]))
            self.assertTrue(self.r[n][1], self.r[n])
        self.assertIn("AI Item Checker", self.r["Bronze Large Charm"][2])
        self.assertIn("borderline", self.r["Coral Large Charm of Vita"][2])
        self.assertIn("UNKNOWN", self.r["Glorious Small Charm"][2])
        self.assertEqual(self.o["judged"], {"mule": "charms", "verdict": "keep"}, "the checker's keep did not home its large charm: %r" % self.o["judged"])
        u = self.o["unread"]
        self.assertIsInstance(u, dict, "an unread affix table threw: %r" % u)
        self.assertTrue(u.get("unknown") and u.get("id") is None, "an unread affix table guessed a home: %r" % u)

    def test_magic_and_rare_holds_no_charm(self):
        mr = self.o["lists"]["magic-rare"]
        self.assertEqual(mr["names"], ["Viper Eye"], "MAGIC & RARE still lists a charm: %r" % mr)
        self.assertEqual(self.o["rare"][0], "magic-rare", "a rare jewel left MAGIC & RARE: %r" % self.o["rare"])
        self.assertIn("Fine Small Charm of Vita", self.o["lists"]["shared"]["names"])
        self.assertEqual(sorted(self.o["lists"]["charms"]["names"]),
                         ["Lion Branded Grand Charm", "Serpent's Large Charm of Vita"], self.o["lists"]["charms"])
        self.assertEqual(self.o["lists"]["uni-small"]["names"], [])
        self.assertEqual(self.o["where"]["mule"], "charms", "FIND names a different home: %r" % self.o["where"])

    def test_the_charms_locker_and_the_notes(self):
        ids = [m[0] for m in self.o["roster"]]
        self.assertIn("charms", ids, "a stored roster did not get the CHARMS locker back: %r" % ids)
        self.assertEqual(ids.index("charms"), ids.index("magic-rare") + 1, ids)
        notes = dict(self.o["roster"])
        self.assertIn("no charms", notes["magic-rare"], notes["magic-rare"])
        self.assertNotIn("charms", notes["uni-small"], notes["uni-small"])
        self.assertEqual(notes["charms"], "Gheed\u2019s, magic-find charms, skillers, kept large charms", notes["charms"])
        self.assertEqual(self.o["charmMule"], "charms", "the charm-mule constant is not the CHARMS locker")
        e = self.o["charmsEntry"] or {}
        self.assertTrue(e.get("auto") and e["auto"].get("why") and e["auto"].get("at"),
                        "the put-back CHARMS mule carries no make record, so no 'Create mule CHARMS' task: %r" % e)

    def test_footprints(self):
        self.assertEqual(self.o["cells"], {"Small Charm of Vita": [1, 1], "Serpent's Large Charm of Vita": [1, 2],
                                           "Steel Grand Charm": [1, 3]})


RED_PROOF = [
    {"why": "REG-2895 - the router never asks the charm rule (a rolled charm back to MAGIC & RARE)",
     "file": "bible.html",
     "find": "      var _ch = (typeof _charmHome === 'function') ? _charmHome(name) : null;\n",
     "replace": "      var _ch = null;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2895 - magic find is not read off the affix rows (of Good Luck to the shared stash)",
     "file": "bible.html",
     "find": "    if (e.mods['mag%']) out.mf = true;\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2895 - skillers are not read off the affix rows (Chaotic / Lion Branded to the shared stash)",
     "file": "bible.html",
     "find": "    if (e.mods.skilltab) out.skiller = true;\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2895 - a large charm skips the checker and lands in the shared stash",
     "file": "bible.html",
     "find": "  if (k.kind === 'large'){\n",
     "replace": "  if (false){\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2895 - an affix the tables do not name for that size is guessed a home",
     "file": "bible.html",
     "find": "    if (!e || !e.its[ity]){ out.read = false; if (!out.unknown) out.unknown = String(pw[1]); return; }\n",
     "replace": "    if (!e || !e.its[ity]) return;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2895 - an unread affix table reads as a miss and throws",
     "file": "bible.html",
     "find": "    if (!af){ out.read = false; out.tableUnread = true; return; }",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2895 - the register's keepers all list on MAGIC & RARE again",
     "file": "bible.html",
     "find": "      Object.keys(magicFinds).sort().forEach(function(n){ if ((typeof _mfKeeperHome === 'function' ? _mfKeeperHome(n) : 'magic-rare') === muleId && names.indexOf(n) < 0) names.push(n); });\n",
     "replace": "      Object.keys(magicFinds).sort().forEach(function(n){ if (muleId === 'magic-rare' && names.indexOf(n) < 0) names.push(n); });\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2895 - the checker's keep is not written onto its keeper (a kept large charm becomes a question)",
     "file": "bible.html",
     "find": "                               at: meta.fts || meta.firstSeenTs || Date.now(), verdict: 'keep' };",
     "replace": "                               at: meta.fts || meta.firstSeenTs || Date.now() };",
     "matches": 1, "needs": "node"},
    {"why": "REG-2895 - the charm-mule side points at UNI-SMALL, not the new CHARMS mule",
     "file": "bible.html",
     "find": "var CHARM_MULE = 'charms';\n",
     "replace": "var CHARM_MULE = 'uni-small';\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2895 - the CHARMS mule carries no make record, so he is never tasked to create it in the game",
     "file": "bible.html",
     "find": "     auto:{by:'the board', why:'his 2026-10-28 ruling: the dedicated charm mule for Gheed\\u2019s, magic-find charms, skillers and kept large charms'}},\n",
     "replace": "     },\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2895 - there is no CHARMS core locker",
     "file": "bible.html",
     "find": ("    {id:'charms',     name:'CHARMS',      icon:'💠', note:CHARMS_NOTE,\n"
              "     auto:{by:'the board', why:'his 2026-10-28 ruling: the dedicated charm mule for Gheed\\u2019s, magic-find charms, skillers and kept large charms'}},\n"),
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2895 - a stored MAGIC & RARE note that names charms is kept",
     "file": "bible.html",
     "find": "                        'magic-rare': ['skillers · magic / rare charms · jewels · rings · amulets · crafts (rolled-name keepers)', MAGIC_RARE_NOTE],\n",
     "replace": "",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
