# -*- coding: utf-8 -*-
"""#103 step C — AN IN-GAME DRAFT WEARS THE GEAR THE REELS SHOWED.

Opening a learned character that is not saved yet puts each witnessed item on its
slot when that name is exactly one item in the tables. A name that matches none,
or more than one, stays off the doll and is said. An item whose slot was not told
is not given a slot. A character with no gear on file says so. A console that has
not sent the gear ledger is UNKNOWN. A saved simulation build is not filled from
the ledger. Nothing is written until he changes the draft.

Drives the shipped planner through the #103 room harness. A missing node raises.
"""
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

import test_the_builder_keeps_in_game_apart_from_simulation as SIM  # noqa: E402


def _run(body):
    if SIM.NODE is None:
        raise AssertionError("node is not on this machine — this gate does not skip")
    return SIM._run(body)


GEAR = r"""
function gearAnswer(){
  var A = JSON.parse(JSON.stringify(ROSTER));
  var slots = ['helm','amulet','weapon','torso','off-hand','gloves','ring1','belt','ring2','boots'].map(function(s){
    if (s === 'helm') return { slot: s, item: 'Harlequin Crest', sightings: 4, tier: 'PROVEN' };
    if (s === 'weapon') return { slot: s, item: 'Grief', sightings: 1, tier: 'WATCHED' };
    if (s === 'torso') return { slot: s, item: 'Enigma', sightings: 7, tier: 'HARDENED' };
    if (s === 'amulet') return { slot: s, item: 'Crescent Moon', sightings: 2, tier: 'WATCHED' };
    if (s === 'belt') return { slot: s, item: 'Not A Real Item', sightings: 1, tier: 'WATCHED' };
    return { slot: s, item: null, sightings: 0, tier: null };
  });
  A.gear = { frostnova: { name: 'Frostnova', slots: slots,
    unplaced: [{ item: 'String of Ears', sightings: 2, why: 'slot not told' }], reels: 2 } };
  return A;
}
function doll(){ return ELS['cb-win']._html; }
function say(){ var m = /id="cb-doll-say"[^>]*>([^<]*)</.exec(doll()); return m ? m[1] : ''; }
function aria(slot){ var m = new RegExp('data-slot="' + slot + '"[^>]*aria-label="([^"]*)"').exec(doll()); return m ? m[1] : ''; }
"""


class AnInGameDraftWearsTheGearTheReelsShowed(unittest.TestCase):

    def test_a_single_match_is_worn_and_the_rest_are_said(self):
        out = _run(GEAR + r"""
          seed(null); LEARNED_ANSWER = gearAnswer(); window._cbLearnedFetch(); window.openCharBuilder();
          var beforeBuilds = RAW['d2r_charBuilds'], beforeOwned = RAW['d2r_owned'];
          window._cbPickBuild('tpl:seen:frostnova');
          OUT.helm = aria('head'); OUT.neck = aria('neck'); OUT.weapon = aria('rarm'); OUT.torso = aria('tors');
          OUT.belt = aria('belt'); OUT.boots = aria('feet'); OUT.off = aria('larm');
          OUT.say = say();
          OUT.draft = /a template — it saves the moment you change it/.test(doll());
          OUT.sameBuilds = RAW['d2r_charBuilds'] === beforeBuilds;
          OUT.sameOwned = RAW['d2r_owned'] === beforeOwned;
          OUT.earsOnDoll = /: String of Ears/.test(doll());
        """)
        self.assertIn("Helm: Harlequin Crest", out["helm"])
        self.assertIn("Weapon: Grief", out["weapon"])
        self.assertIn("Body Armor: Enigma", out["torso"])
        self.assertIn("Amulet — empty", out["neck"])
        self.assertIn("Belt — empty", out["belt"])
        self.assertIn("Boots — empty", out["boots"])
        self.assertIn("Shield / Off-hand — empty", out["off"])
        self.assertIn("Crescent Moon — the name matches 2 items", out["say"])
        self.assertIn("Not A Real Item — not in the item tables", out["say"])
        self.assertIn("String of Ears — slot not told", out["say"])
        self.assertFalse(out["earsOnDoll"], "an item whose slot was not told was equipped")
        self.assertTrue(out["draft"], "the draft was saved before he changed it")
        self.assertTrue(out["sameBuilds"] and out["sameOwned"], "opening the draft wrote a store")

    def test_no_gear_ledger_is_unknown_and_no_row_says_none(self):
        out = _run(GEAR + r"""
          seed(null); LEARNED_ANSWER = ROSTER; window._cbLearnedFetch(); window.openCharBuilder();
          window._cbPickBuild('tpl:seen:frostnova');
          OUT.unknown = say(); OUT.helm = aria('head');
          LEARNED_ANSWER = gearAnswer(); window._cbLearnedFetch();
          window._cbPickBuild('tpl:seen:mulebox');
          OUT.none = say(); OUT.muleHelm = aria('head');
        """)
        self.assertIn("UNKNOWN", out["unknown"])
        self.assertIn("Helm — empty", out["helm"])
        self.assertIn("No reel has shown what this character wears yet", out["none"])
        self.assertIn("Helm — empty", out["muleHelm"])

    def test_a_saved_build_is_not_filled_from_the_ledger(self):
        out = _run(GEAR + r"""
          seed('bSORC'); LEARNED_ANSWER = gearAnswer(); window._cbLearnedFetch(); window.openCharBuilder('bHAM');
          OUT.say = say();
        """)
        self.assertNotIn("Not placed", out["say"])
        self.assertNotIn("Crescent Moon", out["say"])
        self.assertNotIn("String of Ears", out["say"])
        self.assertNotIn("What the reels saw", out["say"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
