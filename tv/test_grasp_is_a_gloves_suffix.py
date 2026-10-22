# -*- coding: utf-8 -*-
"""REG-2402 (#162 item 4) - "GRASP" IS A GLOVES SUFFIX: THE ROLLED-NAME GRAMMAR CARRIES THE GLOVES ROW.

GrokBot #230 (v3783): "Wraith Grasp" routed with the sentence "Wraith + Grasp: ring" - the rolled-name grammar
(RARE_NAME_POOLS, v332) had Amulet, Ring and Jewel rows only, and filed Grasp, Grip, Hold, Touch and Finger under Ring
alone. The game's own RareSuffix table (RotW raresuffix.txt, the itype columns) says otherwise:

    hand, clutches, knuckle          glov
    fist, claw                       glov  h2h
    grip, grasp, hold, touch, finger glov  ring

So the grammar now has a Gloves row with exactly the game's glov words, and a word the game gives BOTH gloves and ring
reads "gloves / ring" - a rolled "Wraith Grasp" is gloves or a ring, and its name alone cannot say which. The brief said
"not a ring"; the table says ring too, and this law pins the table, not the brief. Routing is unchanged: every rolled
name still lands in MAGIC & RARE.

Drives the SHIPPED tables, _rolledQuality and _rolledRoute cut from bible.html, in node. A missing node raises.
"""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
from cb_node_harness import NODE  # noqa: E402

PAGE = os.path.join(os.path.dirname(HERE), "bible.html")
TABLES = ("const RARE_NAME_POOLS = {", "\nwindow.RARE_NAME_POOLS = RARE_NAME_POOLS;")
HELPER = ("var _MAGIC_SMALL_RE = ", "\nwindow._rolledQuality = _rolledQuality;\n")
ROUTE = ("function _rolledRoute(rq){", "\nwindow._rolledRoute = _rolledRoute;\n")

#: the game's RareSuffix rows whose itype columns name gloves (RotW raresuffix.txt), and which of them also name ring
GAME_GLOVES = {"Hand", "Fist", "Claw", "Clutches", "Grip", "Grasp", "Hold", "Touch", "Finger", "Knuckle"}
GAME_GLOVES_AND_RING = {"Grip", "Grasp", "Hold", "Touch", "Finger"}


def _src():
    with open(PAGE, encoding="utf-8") as f:
        return f.read()


def _cut(s, pair):
    start, end = pair
    if s.count(start) != 1:
        raise AssertionError("anchor %r matched %d times - re-point this law" % (start[:50], s.count(start)))
    i = s.index(start)
    return s[i:s.index(end, i) + len(end)]


def _node(body):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    s = _src()
    js = """
var window = {};
function d2rItemLookup(){ return null; }
%s
%s
%s
%s
""" % (_cut(s, TABLES), _cut(s, HELPER), _cut(s, ROUTE), body)
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut grammar did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class GraspIsAGlovesSuffix(unittest.TestCase):

    def test_wraith_grasp_reads_gloves_or_ring_and_still_files_to_magic_and_rare(self):
        got = _node("var q = _rolledQuality('Wraith Grasp'); console.log(JSON.stringify({ q: q, r: _rolledRoute(q) }));")
        self.assertEqual(got["q"]["q"], "rare")
        self.assertIn("Gloves", got["q"]["slots"], "Wraith Grasp is still read as a ring only: %r" % got["q"]["slots"])
        self.assertEqual(got["q"]["slots"], ["Gloves", "Ring"], got["q"]["slots"])
        self.assertIn("gloves / ring", got["r"]["why"], "the route sentence does not say gloves: %r" % got["r"]["why"])
        self.assertEqual(got["r"]["id"], "magic-rare", "a rolled gloves name no longer files to MAGIC & RARE")

    def test_the_gloves_row_is_the_games_and_ring_only_words_stay_ring(self):
        got = _node("var o = {}; ['Death Loop', 'Havoc Finger', 'Doom Fist', 'Bone Knuckle', 'Storm Scarab'].forEach("
                    "function(n){ var q = _rolledQuality(n); o[n] = q && q.slots; });"
                    "console.log(JSON.stringify({ pools: RARE_NAME_POOLS, o: o }));")
        pools = got["pools"]
        self.assertEqual(set(pools.get("Gloves") or []), GAME_GLOVES, "the Gloves row is not the game's glov rows")
        self.assertEqual(set(pools["Gloves"]) & set(pools["Ring"]), GAME_GLOVES_AND_RING,
                         "a word the game gives gloves AND ring is not in both rows")
        self.assertEqual(got["o"]["Death Loop"], ["Ring"], "Loop is a ring-only suffix")
        self.assertEqual(got["o"]["Havoc Finger"], ["Gloves", "Ring"])
        self.assertEqual(got["o"]["Doom Fist"], ["Gloves"])
        self.assertEqual(got["o"]["Bone Knuckle"], ["Gloves"])
        self.assertEqual(got["o"]["Storm Scarab"], ["Amulet", "Jewel"], "an amulet / jewel word moved")


RED_PROOF = [
    {"why": "REG-2402 - the rolled-name grammar has no gloves row again (Wraith Grasp reads 'ring')",
     "file": "bible.html",
     "find": "  Gloves: ['Hand','Fist','Claw','Clutches','Grip','Grasp','Hold','Touch','Finger','Knuckle'],\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2402 - Grasp is a ring suffix only again",
     "file": "bible.html",
     "find": "  Gloves: ['Hand','Fist','Claw','Clutches','Grip','Grasp','Hold','Touch','Finger','Knuckle'],\n",
     "replace": "  Gloves: ['Hand','Fist','Claw','Clutches','Grip','Hold','Touch','Finger','Knuckle'],\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
