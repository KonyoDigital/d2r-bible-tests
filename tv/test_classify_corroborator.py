"""A21d — his rule, run over the item classifier: ten agree, one does not, flag it.

Konyo: *"when 10 are the same logic obviously one isnt its flagged.. by corrobarator and all... the
chronicle uniques going forward and the cross reference for THE FLEET"*.

Every member of a roster should classify the same way — a set piece is a set piece, a sunder charm
is a unique. So classify all of them through the ONE resolver and name any member that disagrees
with its siblings.

⚠ WHAT IT FOUND ON ITS FIRST RUN, which is why it exists: 9 of 398 uniques did NOT resolve to
'unique'.
  - FOUR carried a curly apostrophe (U+2019) where every lookup table holds U+0027 — Atma's Scarab,
    Seraph's Hymn, The Cat's Eye, Saracen's Chance. With the straight form each resolved instantly.
    That scar was fixed at the vault in v1958 and never here.
  - FOUR were in no table at all: Harlequin Crest, Hellfire Torch, Gull, The Cranium Basher. Four
    of the most famous uniques in the game, rendering with no rarity.
  - ONE is a genuine dual-name and is DECLARED below rather than fixed.

⚠ THE DECLARED PAIRS ARE NOT AN EXCEPTIONS LIST FOR CONVENIENCE. Each carries the reason it is
ambiguous, and the test still fails if a declared name stops being ambiguous or a new one appears.
Silently excluding an outlier is how a corroborator learns to say nothing.
"""
import json
import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
BIBLE = "file://" + os.path.join(os.path.dirname(HERE), "bible.html")

#: name -> why this ONE name may legitimately classify against its roster's majority.
DUAL_NAMES = {
    "Crescent Moon": "genuinely both — a runeword (Shael + Um + Tir) AND a unique amulet. Which "
                     "answer is right depends on which item is being rendered, so the resolver "
                     "picking 'rw' is one of two defensible answers and must not be silently "
                     "reordered.",
    "Death's Web": "carried in RUNEWORDS with its runes field reading '(unique, not RW)' — the "
                   "page deliberately lists it there while marking it a unique, and findRuneword "
                   "correctly refuses it. The outlier is an artifact of reading that array as a "
                   "roster of runewords.",
}

_PROBE = r"""(function(){
  if (typeof _artRarity !== 'function') return JSON.stringify({ready:false});
  function names(f){ try { return (f()||[]).filter(Boolean).map(String); } catch(e){ return []; } }
  var rosters = {
    'sunder charms': names(function(){ return (typeof SUNDER_CHARMS==='undefined'?[]:SUNDER_CHARMS).map(function(c){return c.n;}); }),
    'runewords':     names(function(){ return (typeof RUNEWORDS==='undefined'?[]:RUNEWORDS).map(function(r){return r.n;}); }),
    'set pieces':    names(function(){ return (typeof window._gSetRoster==='function') ? window._gSetRoster() : []; }),
    'uniques':       names(function(){ return (typeof window._gUniqueRoster==='function') ? window._gUniqueRoster() : []; })
  };
  var out = {};
  Object.keys(rosters).forEach(function(k){
    var tally = {}, by = {};
    rosters[k].forEach(function(n){
      var r; try { r = _artRarity(n) || '(none)'; } catch(e){ r = '(threw)'; }
      tally[r] = (tally[r]||0)+1; (by[r] = by[r]||[]).push(n);
    });
    var kinds = Object.keys(tally).sort(function(a,b){return tally[b]-tally[a];});
    var maj = kinds[0] || null, odd = [];
    for (var i=1;i<kinds.length;i++) by[kinds[i]].forEach(function(n){ odd.push([n, kinds[i]]); });
    out[k] = {n: rosters[k].length, majority: maj, majorityN: maj?tally[maj]:0, outliers: odd};
  });
  return JSON.stringify({ready:true, rosters:out});
})()"""


def _classify():
    import render_check as rc
    if not rc._chrome_up():
        return None
    try:
        tab = rc._Tab(BIBLE)
        time.sleep(8)
        raw = tab.ev(_PROBE)
        tab.close()
        return json.loads(raw) if raw else None
    finally:
        rc._chrome_down()


class TenAgreeAndOneDoesNot(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.d = _classify()

    def setUp(self):
        if not self.d:
            self.skipTest("no headless Chrome — UNKNOWN, never a pass")
        if not self.d.get("ready"):
            self.skipTest("bible.html did not expose _artRarity — UNKNOWN, never a pass")

    def test_the_probe_sees_real_rosters(self):
        """PRINT THE COUNT. A classifier check over empty rosters is green and measures nothing."""
        for k, v in self.d["rosters"].items():
            self.assertGreater(v["n"], 0, "roster %r came back EMPTY — the probe is broken, not "
                                          "the page, and an empty roster passes every rule below" % k)

    def test_every_roster_member_classifies_like_its_siblings(self):
        bad = []
        for roster, v in sorted(self.d["rosters"].items()):
            for name, got in v["outliers"]:
                if name in DUAL_NAMES:
                    continue
                bad.append("%s: %r -> %r (its %d siblings say %r)"
                           % (roster, name, got, v["majorityN"], v["majority"]))
        self.assertEqual(bad, [], "these names disagree with every sibling in their own roster, "
                                  "which is his rule exactly — ten share one logic and these do "
                                  "not:\n  " + "\n  ".join(bad))

    def test_a_declared_dual_name_that_stopped_being_ambiguous_is_reported(self):
        """A declared pair is a claim about the data. If the claim stops being true the declaration
        is stale, and a stale exception is how a corroborator quietly stops finding anything."""
        flagged = {n for v in self.d["rosters"].values() for n, _ in v["outliers"]}
        stale = sorted(set(DUAL_NAMES) - flagged)
        self.assertEqual(stale, [], "these names are declared as legitimately ambiguous and are no "
                                    "longer flagged by anything — the declaration outlived its "
                                    "reason and should be deleted: %s" % stale)


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
