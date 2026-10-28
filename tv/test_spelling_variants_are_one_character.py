# -*- coding: utf-8 -*-
"""#211 (GrokBot, the ALT's 45 learned characters) - SPELLING VARIANTS OF ONE CHARACTER ARE ONE CHARACTER.

The reader misspells a name now and then. Every spelling folded to its own key, and each that reached 2 visits became its
own learned character (Konylock, Konyblock beside Konyolock), while the visits a variant was read under counted as MISSES
against the real one. learned() now merges at READ time - the ledger is never rewritten - when the chronicle's own
near-name rule (chronicle_resolve.canonical) names a more-visited head, both carry the same winning class, and no READ
ever saw both (two names on one screen are two characters). The merged row names its variants (`aliases`), and the
board finds a build linked to a variant.

GrokBot's v3817 pass: the first cut refused on a shared VISIT. A visit is several frames of one lobby and the reader spells
one row two ways across them, so Konylock (11 visits shared with Konyolock) stayed its own card - the ALT's roster
learned 40 characters for a 9-row lobby. record() now keeps which names each read saw (onFrame), and an older visit
proves one screen only by one read, by names that fit its largest read, or by a name read on every read it was in.

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
    vs = {v: {"ts": T0 + i, "partial": False} for i, v in enumerate(vids)}
    for v in ("v9", "v10"):     # one read of each of these screens showed Testlock AND Testlocks
        vs[v].update({"reads": 2, "rows": 2, "onFrame": [["testlock", "testlocks"], ["testlock"]]})
    return {"visits": vs,
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

    def _shared_v4(self, **visit):
        d = _ledger()
        d["chars"]["konylock"]["visitLevel"]["v4"] = 96          # Konylock was read in a visit Konyolock was read in
        d["chars"]["konylock"]["cls"]["Warlock"].append("v4")
        d["visits"]["v4"].update(visit)
        return {r["name"]: r for r in CS.learned(d)}

    def test_a_read_that_saw_both_splits_the_variant_back_out(self):
        rows = self._shared_v4(reads=2, rows=3, onFrame=[["konylock", "konyolock", "konyossin"], ["konyolock"]])
        self.assertIn("Konylock", rows, "a name read beside the head on one screen was merged into it")

    def test_two_frames_of_one_visit_read_one_name_two_ways(self):
        """GrokBot v3817 - the visit is shared, no single read saw both: one character"""
        rows = self._shared_v4(reads=3, rows=2, onFrame=[["konyolock", "konyossin"], ["konylock", "konyossin"],
                                                         ["konyolock"]])
        self.assertNotIn("Konylock", rows, "a shared VISIT split a misspelling off its character (#211, v3817)")
        self.assertIn("Konylock", [a["name"] for a in rows["Konyolock"]["aliases"]])

    def test_an_older_visit_that_cannot_say_is_not_a_read_of_both(self):
        """no per-read lists, 3 reads, more names (3) than its largest read (2), nobody read on every read: UNKNOWN"""
        rows = self._shared_v4(reads=3, rows=2)
        self.assertNotIn("Konylock", rows, "a visit that cannot say which read saw which name split the variant")

    def test_an_older_visit_still_proves_one_screen_three_ways(self):
        self.assertIn("Konylock", self._shared_v4(reads=1), "a visit read ONCE saw both names on that read")
        self.assertIn("Konylock", self._shared_v4(reads=3, rows=3),
                      "the visit's 3 names fit in its largest read of 3 rows, so that read held both")
        d = _ledger()
        for v in ("v1", "v2", "v3"):
            d["visits"][v]["reads"] = 1
        d["visits"]["v4"]["reads"] = 3                               # Konyolock read on all 6 reads of its 4 visits
        d["chars"]["konyolock"]["forms"] = {"Konyolock": 6}
        d["chars"]["konylock"]["visitLevel"]["v4"] = 96
        d["chars"]["konylock"]["cls"]["Warlock"].append("v4")
        rows = {r["name"]: r for r in CS.learned(d)}
        self.assertIn("Konylock", rows, "a name read on every read of v4 sat beside Konylock on the read that saw it")


class ARecordKeepsWhichNamesOneReadSaw(unittest.TestCase):

    def test_a_new_visit_keeps_one_list_per_read_and_an_older_one_starts_none(self):
        d = {"visits": {"old#1": {"reads": 2, "rows": 3}}, "chars": {}}
        CS.record(d, "new#1", [{"key": "konyolock", "name": "Konyolock"}, {"key": "konyodin", "name": "Konyodin"}])
        CS.record(d, "new#1", [{"key": "konylock", "name": "Konylock"}])
        CS.record(d, "new#1", [])
        self.assertEqual(d["visits"]["new#1"]["reads"], 3)
        self.assertEqual(d["visits"]["new#1"]["onFrame"], [["konyodin", "konyolock"], ["konylock"], []],
                         "a read's names were not kept beside it")
        CS.record(d, "old#1", [{"key": "konyolock", "name": "Konyolock"}])
        self.assertNotIn("onFrame", d["visits"]["old#1"], "an older visit grew a list that is missing its first reads")
        rows = {r["name"]: r for r in CS.learned(d, min_visits=1)}
        self.assertNotIn("Konylock", rows, "two reads of one new visit were taken for one screen: %r" % sorted(rows))


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
     "find": "                _read_together(d, v, set(groups[h]), {k}, keys_in, always, visits_of) is True for v in (mine & seen_by[h])):\n",
     "replace": "                False for v in (mine & seen_by[h])):\n", "matches": 1},
    {"why": "#211 - two classes are merged into one character",
     "file": "tv/char_select.py",
     "find": "        if h and h != k and _cls_winner(chars[h]) == kc and not any(\n",
     "replace": "        if h and h != k and not any(\n", "matches": 1},
    {"why": "#211 v3817 - a visit that cannot say which read saw which name splits a misspelling off again",
     "file": "tv/char_select.py",
     "find": "    return None\n\n\ndef _always_read(",
     "replace": "    return True\n\n\ndef _always_read(", "matches": 1},
    {"why": "#211 v3817 - a shared visit refuses although no read saw both (the per-read lists are not asked)",
     "file": "tv/char_select.py",
     "find": "        return any((set(f) & a) and (set(f) & b) for f in on)\n",
     "replace": "        return True\n", "matches": 1},
    {"why": "#211 v3817 - a read's names are not kept beside it",
     "file": "tv/char_select.py",
     "find": "        v[\"onFrame\"].append(sorted({r[\"key\"] for r in rows or [] if r.get(\"key\")}))\n",
     "replace": "        pass\n", "matches": 1},
    {"why": "#211 v3817 - a visit read once no longer proves its names shared that read",
     "file": "tv/char_select.py",
     "find": "    if reads == 1:\n        return True\n",
     "replace": "    if False:\n        return True\n", "matches": 1},
    {"why": "#211 v3817 - names that fit in the visit's largest read no longer prove one screen",
     "file": "tv/char_select.py",
     "find": "and len(keys_in.get(vid) or ()) <= rows:\n",
     "replace": "and len(keys_in.get(vid) or ()) < 0:\n", "matches": 1},
    {"why": "#211 v3817 - a name read on every read of its visits no longer proves it sat beside the other",
     "file": "tv/char_select.py",
     "find": "        if n >= sum(rs):\n",
     "replace": "        if False:\n", "matches": 1},
    {"why": "#211 - a build linked to a merged spelling drops into SIMULATION",
     "file": "bible.html",
     "find": "      if (!g && b.from) groups.forEach(function(x){ if (!g && (x.t.alias || []).indexOf(b.from) >= 0) g = x; });   /* #211 */\n",
     "replace": "", "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
