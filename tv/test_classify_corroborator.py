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
import ast
import inspect
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


import reel_segments as rs


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



class BothLogicsIntertwined(unittest.TestCase):
    """v2578 — A5. HIS RULING: *"the templates should sort of decide for it... if no inventory is
    there or a stash template open.. then it can classify it accordingly"*, then *"BOTH logics
    intertwined... not just one rules out"*.

    `lane_at` asks only whether a read CONTAINS the moment, and segments are the INSTANTS of reads
    rather than the intervals between them. Measured on his store: containment answers a
    mid-session moment for 7 of 2,771 sessions. The earlier proposal — inherit the NEAREST read's
    lane — was refused because proximity is not evidence about content. The template IS, and the
    two compose: 335 of 2,771 settle, of which 325 are the sound NEGATIVE.
    """

    def _segs(self, sid, acts):
        return [{"sid": sid, "activity": a, "start": lo, "end": hi, "reads": 1}
                for a, lo, hi in acts]

    def test_containment_still_wins_and_is_still_called_contained(self):
        segs = self._segs("s1", [("stash", 1000, 2000)])
        lane, why, grade = rs.lane_at_graded(segs, "s1", 1500)
        self.assertEqual(grade, rs.CONTAINED)
        self.assertEqual(lane, "stash", why)

    def test_a_reel_that_never_opened_a_container_is_RULED_OUT_not_unknown(self):
        """The sound negative, and 325 of his sessions are exactly this."""
        segs = self._segs("s1", [("gameplay", 1000, 2000), ("town", 3000, 4000)])
        lane, why, grade = rs.lane_at_graded(segs, "s1", 2500)
        self.assertEqual(grade, rs.RULED_OUT,
                         "a reel with no stash and no inventory anywhere cannot contain a "
                         "possession moment; that is a NEGATIVE, not an unknown: %s" % why)
        self.assertIsNone(lane)

    def test_an_uncontained_moment_inside_a_container_span_is_INHERITED_not_CONTAINED(self):
        """It is real evidence AND weaker evidence, so it must not wear containment's word.

        ⚠ THE FIRST VERSION OF THIS TEST WAS INERT and the sabotage said so: it accepted either
        CONTAINED or INHERITED, so dressing INHERITED up as CONTAINED passed. It must pin ONE.
        Two stash segments with a real gap between them; the moment sits in the gap, inside the
        outer span, covered by neither read.
        """
        segs = self._segs("s1", [("stash", 1000, 1200), ("stash", 8000, 8200)])
        lane, why, grade = rs.lane_at_graded(segs, "s1", 5000)
        self.assertEqual(grade, rs.INHERITED,
                         "a moment between two stash reads, inside the span the reel spent in "
                         "the stash, must be INHERITED — real evidence and weaker evidence, "
                         "never containment's word: got %s (%s)" % (grade, why))
        self.assertEqual(lane, "stash", why)


    def test_a_covered_moment_that_is_deliberately_NOT_possession_stays_CONTAINED(self):
        """⚠ THE DISTINCTION THE FIRST CUT LOST, and a sabotage proved the guard for it missing.

        lane_at returns None for TWO reasons: no read covers the moment, and a read DOES cover it
        but that activity is not possession (a Chronicle page; an inventory, which is holding
        rather than owning). Branching on `lane` being falsy conflates them, and then a considered
        refusal gets re-graded as a template inference — losing the reason lane_at had given.

        Measured consequence on his real store: with the wrong branch, 326 covered moments were
        reported as ruled-out-by-template. The grade must key on COVERAGE, not on the lane.
        """
        segs = self._segs("s1", [("inventory", 1000, 2000)])
        lane, why, grade = rs.lane_at_graded(segs, "s1", 1500)
        self.assertEqual(grade, rs.CONTAINED,
                         "a read covers this moment, so the answer is containment's — even "
                         "though the lane is deliberately None: %s" % why)
        self.assertIsNone(lane)
        self.assertIn("holding", why.lower(),
                      "lane_at's own reason was discarded: %s" % why)

    def test_no_segments_at_all_stays_UNSETTLED(self):
        lane, why, grade = rs.lane_at_graded([], "s1", 1000)
        self.assertEqual(grade, rs.UNSETTLED)
        self.assertIsNone(lane)

    def test_the_strict_door_is_NOT_widened(self):
        """⚠ Every existing caller — including the vault door that refuses claims — was written
        against lane_at's containment answer. A grade nobody asked for must not silently open a
        door that was closed."""
        segs = self._segs("s1", [("gameplay", 1000, 2000)])
        lane, why = rs.lane_at(segs, "s1", 9999)
        self.assertIsNone(lane, "lane_at started answering for an uncovered moment: %s" % why)

    def test_every_branch_returns_the_same_SHAPE(self):
        """⚠ The first cut had one branch returning a 2-tuple because a paren grouped the string
        with the grade — a shape that changes with the verdict, REG-547 one module over. The
        unpack raised on the first real call, which is luck; this checks it."""
        tree = ast.parse(inspect.getsource(rs.lane_at_graded).lstrip())
        bad = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Return)
               and not (isinstance(n.value, ast.Tuple) and len(n.value.elts) == 3)]
        self.assertEqual(bad, [], "lane_at_graded has returns that are not 3-tuples, at %s" % bad)


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
