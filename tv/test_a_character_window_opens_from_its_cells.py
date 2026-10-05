# -*- coding: utf-8 -*-
"""#146 step 3c — an in-game character opens as a window of the cells a look already named.

The card's Open door calls that window. The window's cells are equipped:helm and the other nine,
the same identity a vault look records. It does not open the planner and it does not write a build.
A character the ledger has not spoken about stays UNKNOWN, with no cell drawn as if it had been
looked at. An inventory or stash cell that is not joined to the character is not drawn empty.
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import test_the_characters_tab_is_manual_and_separate as ROOM  # noqa: E402

CONSOLE = r"""
var location = { protocol: 'http:', search: '', hash: '', href: 'http://127.0.0.1:17999/', pathname: '/' };
var LEARNED_ANSWER = null, FETCHED = [];
function _syncThen(v){ return { then: function(f){ var r; try { r = f(v); } catch (e) { r = undefined; } return _syncThen(r); },
                                catch: function(){ return this; } }; }
function fetch(url){ FETCHED.push(String(url));
  if (LEARNED_ANSWER === 'FAIL') return { then: function(){ return this; }, catch: function(f){ f(new Error('down')); return this; } };
  return _syncThen({ ok: true, json: function(){ return LEARNED_ANSWER; } }); }
"""

ROSTER = r"""
var ROSTER = { ok: true, tierBars: { proven: 10, hardened: 20, wilson: 0.722 }, chars: [
  { name: 'Frostnova', cls: 'Sorceress', level: 71, pendingLevel: null, visits: 11, tier: 'PROVEN', looks: 11, trials: 11,
    title: null, lastTs: NOW - 7200000 },
  { name: 'Mulebox', cls: 'Sorceress', level: 1, pendingLevel: null, visits: 3, tier: 'WATCHED', looks: 3, trials: 3,
    title: null, lastTs: NOW - 86400000 } ] };
"""

GEAR = r"""
function withGear(){
  var A = JSON.parse(JSON.stringify(ROSTER));
  var slots = ['helm','amulet','weapon','torso','off-hand','gloves','ring1','belt','ring2','boots'].map(function(s){
    return s === 'helm' ? {slot: s, item: 'Harlequin Crest', sightings: 4, tier: 'PROVEN'}
                        : {slot: s, item: null, sightings: 0, tier: null}; });
  A.gear = { frostnova: { name: 'Frostnova', slots: slots,
    unplaced: [{item: 'String of Ears', sightings: 2, tier: 'WATCHED'}], reels: 2 } };
  return A;
}
"""


def _run(body):
    return ROOM._run(ROSTER + GEAR + body, raw_patch=CONSOLE)


class ACharacterWindowOpensFromItsCells(unittest.TestCase):

    def test_open_is_the_window_and_not_the_planner(self):
        out = _run(r"""
          seed(null); LEARNED_ANSWER = withGear(); window.renderCharsTab();
          var ing = ELS['chars-list']._html;
          var ghost = (/<article class="chx-card chx-ghost" data-learned="seen:frostnova">([\s\S]*?)<\/article>/.exec(ing) || [])[1] || '';
          OUT.door = /data-act="window" onclick="window\._chxOpen\('seen:frostnova'\)"/.test(ghost);
          OUT.plans = (ing.match(/data-act="plan"/g) || []).length;
          var before = RAW['d2r_charBuilds'];
          window._chxOpen('seen:frostnova');
          OUT.html = ELS['chx-win'] ? ELS['chx-win']._html : '';
          OUT.hidden = ELS['chx-win'] ? ELS['chx-win'].hidden : null;
          OUT.opened = OPENED.slice();
          OUT.wrote = RAW['d2r_charBuilds'] !== before;
        """)
        self.assertTrue(out["door"], "the character card does not open its window")
        self.assertEqual(out["plans"], 0, "an in-game card still offers the planner")
        self.assertFalse(out["hidden"])
        self.assertIn('data-cell="equipped:helm"', out["html"])
        self.assertIn("Harlequin Crest", out["html"])
        self.assertIn('data-cell="equipped:boots"', out["html"])
        self.assertIn('data-slot="boots" data-state="unseen"', out["html"])
        self.assertNotIn('data-cell="inventory:', out["html"])
        self.assertNotIn('data-cell="stash:', out["html"])
        self.assertIn('data-grid="inventory" data-state="unjoined"', out["html"])
        self.assertIn("String of Ears", out["html"])
        self.assertEqual(out["opened"], [], "opening the window opened the planner")
        self.assertFalse(out["wrote"], "opening the window wrote a build")

    def test_a_cell_says_what_was_seen_there(self):
        out = _run(r"""
          seed(null); LEARNED_ANSWER = withGear(); window.renderCharsTab();
          window._chxOpen('seen:frostnova');
          window._chxPick('equipped:helm');
          OUT.say = ELS['chx-win']._html;
          OUT.picked = ELS['chx-win'].getAttribute('data-picked');
          window._chxPick('equipped:boots');
          OUT.boots = ELS['chx-win']._html;
        """)
        self.assertEqual(out["picked"], "equipped:helm")
        self.assertIn("Helm · Harlequin Crest · ✓ PROVEN · 4 looks", out["say"])
        self.assertIn("Boots · not seen yet", out["boots"])

    def test_unknown_and_unseen_draw_no_cell(self):
        out = _run(r"""
          seed(null); LEARNED_ANSWER = ROSTER; window.renderCharsTab();
          window._chxOpen('seen:frostnova');
          OUT.unknown = ELS['chx-win']._html;
          LEARNED_ANSWER = withGear(); window.renderCharsTab();
          window._chxOpen('seen:mulebox');
          OUT.none = ELS['chx-win']._html;
          window._chxClose();
          OUT.hidden = ELS['chx-win'].hidden;
        """)
        self.assertIn('data-state="unknown"', out["unknown"])
        self.assertNotIn("data-cell=", out["unknown"], "an unspoken ledger drew cells")
        self.assertIn('data-state="none"', out["none"])
        self.assertIn("Nothing seen on Mulebox yet", out["none"])
        self.assertNotIn("data-cell=", out["none"], "a character with no gear drew cells")
        self.assertTrue(out["hidden"])


RED_PROOF = [
    {
        "why": "the card must open the character window; sending it to the planner is the door he ruled out",
        "file": "bible.html",
        "find": 'data-act="window" onclick="window._chxOpen(\\\'',
        "replace": 'data-act="plan" onclick="window._charsPlan(\\\'',
        "matches": 1,
    },
    {
        "why": "a slot is addressed by the cell a look records; dropping data-cell leaves a button that is not that cell",
        "file": "bible.html",
        "find": 'data-cell="\' + esc(cell) + \'" data-slot="\'',
        "replace": 'data-slot="\'',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
