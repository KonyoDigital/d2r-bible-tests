# -*- coding: utf-8 -*-
"""#211 (GrokBot, the ALT's 45 learned characters) - SPELLING VARIANTS OF ONE CHARACTER ARE ONE CHARACTER.

The reader misspells a name now and then. Every spelling folded to its own key, and each that reached 2 visits became its
own learned character (Konylock, Konyblock beside Konyolock), while the visits a variant was read under counted as MISSES
against the real one. learned() now merges at READ time - the ledger is never rewritten - when the chronicle's own
near-name rule (chronicle_resolve.canonical) names a more-visited head, both carry the same winning class, and no visit
ever read both (two names on one screen are two characters). The merged row names its variants (`aliases`), and the
board finds a build linked to a variant.

Driven on char_select itself, and the board's own _cbSections in node.
RED_PROOF below.
"""
import copy
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
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import char_select as CS  # noqa: E402
import vault_page_node as VPN  # noqa: E402

T0 = 1792800000000


def _ch(name, cls, visits, level=96):
    return {"name": name, "forms": {name: len(visits)}, "cls": {cls: list(visits)},
            "visitLevel": {v: level for v in visits}, "titles": {}, "firstTs": T0, "lastTs": T0 + 9}


def _ledger():
    vids = ["v%d" % i for i in range(1, 11)]
    return {"visits": {v: {"ts": T0 + i, "partial": False} for i, v in enumerate(vids)},
            "chars": {
                "konyolock": _ch("Konyolock", "Warlock", ["v1", "v2", "v3", "v4"]),
                "konylock": _ch("Konylock", "Warlock", ["v5", "v6"]),
                "konyblock": _ch("Konyblock", "Warlock", ["v7", "v8"]),
                "konyodin": _ch("Konyodin", "Paladin", ["v1", "v2", "v3"]),
                "konyossin": _ch("Konyossin", "Assassin", ["v4", "v5"]),
                "testlock": _ch("Testlock", "Warlock", ["v9", "v10"], level=12),
                "testlocks": _ch("Testlocks", "Warlock", ["v9", "v10"], level=11),
                # near names (0.95 alike), different classes: a Barbarian and a Druid are two characters
                "konyobarb": _ch("Konyobarb", "Barbarian", ["v1", "v2", "v3"], level=90),
                "konyobarbs": _ch("Konyobarbs", "Druid", ["v6", "v7"], level=80),
            }}


class SpellingVariantsAreOneCharacter(unittest.TestCase):

    def test_variants_merge_into_the_most_seen_spelling(self):
        d = _ledger()
        before = copy.deepcopy(d)
        rows = {r["name"]: r for r in CS.learned(d)}
        self.assertIn("Konyolock", rows)
        self.assertNotIn("Konylock", rows, "a misspelling is its own character (#211): %r" % sorted(rows))
        self.assertNotIn("Konyblock", rows)
        k = rows["Konyolock"]
        self.assertEqual(k["visits"], 8)
        # v9 and v10 are whole lists that showed only Testlock(s): 2 real misses. Unmerged it was 6 (v5-v8 counted too).
        self.assertEqual(k["misses"], 2, "a visit read under a variant counted as a MISS against the real one: %r" % k)
        self.assertEqual(sorted(a["name"] for a in k["aliases"]), ["Konyblock", "Konylock"])
        self.assertEqual(d, before, "the read rewrote the ledger")

    def test_different_classes_and_one_screen_stay_apart(self):
        rows = {r["name"]: r for r in CS.learned(_ledger())}
        self.assertIn("Konyodin", rows)
        self.assertIn("Konyossin", rows)
        self.assertIn("Konyobarbs", rows, "two near-named characters of different classes were merged into one")
        self.assertIn("Testlock", rows)
        self.assertIn("Testlocks", rows, "two names read on the same screens were merged into one")
        self.assertNotIn("aliases", rows["Konyodin"])

    def test_a_visit_reading_both_splits_the_variant_back_out(self):
        d = _ledger()
        d["chars"]["konylock"]["visitLevel"]["v4"] = 96          # one screen showed Konyolock AND Konylock
        d["chars"]["konylock"]["cls"]["Warlock"].append("v4")
        rows = {r["name"]: r for r in CS.learned(d)}
        self.assertIn("Konylock", rows, "a name read beside the head on one screen was merged into it")


BOARD = r"""
(function(){
var W = window;
W._cbLearnedTakeForLaw({ ok: true, chars: [{ name: 'Konyolock', cls: 'Warlock', level: 96, visits: 8,
  aliases: [{ key: 'konylock', name: 'Konylock', visits: 2 }] }] });
var S = W._cbSections({ b1: { name: 'Konylock build', cls: 'Warlock', from: 'seen:konylock' } }, ['b1']);
OUT.ingame = (S.ingame || []).map(function(g){ return { key: g.t.key, ids: g.ids }; });
OUT.sim = S.sim;
})();
"""


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class ABuildLinkedToAVariantStillFindsItsCharacter(unittest.TestCase):

    def test_the_build_sits_under_the_merged_character(self):
        o = VPN.run(BOARD, prelude="localStorage.setItem('d2r_ownerClaim', '*');", timeout=300)
        self.assertEqual(o["__boot"]["errors"], [], o["__boot"])
        self.assertEqual(o["ingame"], [{"key": "seen:konyolock", "ids": ["b1"]}],
                         "a build made from a merged spelling fell out of its character: %r" % o)
        self.assertEqual(o["sim"], [], "the build dropped into SIMULATION: %r" % o)


RED_PROOF = [
    {"why": "#211 - every spelling is its own character again",
     "file": "tv/char_select.py",
     "find": "    _groups = _merge_groups(d)\n",
     "replace": "    _groups = {k: [k] for k in _chars}\n", "matches": 1},
    {"why": "#211 - two names read on one screen are merged into one",
     "file": "tv/char_select.py",
     "find": "        if h and h != k and _cls_winner(chars[h]) == kc and not (mine & seen_by[h]):\n",
     "replace": "        if h and h != k and _cls_winner(chars[h]) == kc:\n", "matches": 1},
    {"why": "#211 - two classes are merged into one character",
     "file": "tv/char_select.py",
     "find": "        if h and h != k and _cls_winner(chars[h]) == kc and not (mine & seen_by[h]):\n",
     "replace": "        if h and h != k and not (mine & seen_by[h]):\n", "matches": 1},
    {"why": "#211 - a build linked to a merged spelling drops into SIMULATION",
     "file": "bible.html",
     "find": "      if (!g && b.from) groups.forEach(function(x){ if (!g && (x.t.alias || []).indexOf(b.from) >= 0) g = x; });   /* #211 */\n",
     "replace": "", "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
