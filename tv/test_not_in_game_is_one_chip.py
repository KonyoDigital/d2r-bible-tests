# -*- coding: utf-8 -*-
"""v3848 (Elad 00:59 / 01:00) - 'NOT IN GAME YET' IS ONE CHIP FROM ONE HELPER.

The Vault's CHARMS locker said "made by the board · not in the game yet" in an inline-styled tag that crowded the title.
Now one CSS class (.nig-chip, one line, nowrap) and one JS helper (_notInGameChip over _vaultMuleNotInGame) serve every
locker and the MOVE TASKS make row; the status is rename-safe (a sighting under the mule's prevName or an alias is still
this mule); "made by the board" is not said on a chip or a task line.
"""
import os, re, subprocess, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from console_safe import enable; enable()

HERE = os.path.dirname(os.path.abspath(__file__))
BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")
SRC = open(BIBLE, encoding="utf-8").read()


def _fn(name):
    i = SRC.index("  function %s(" % name)
    j = SRC.index("\n  }\n", i)
    return SRC[i:j + 4]


class NotInGameIsOneChip(unittest.TestCase):
    def test_one_css_class_one_line(self):
        rules = re.findall(r"\n\.nig-chip\{([^}]*)\}", SRC)
        self.assertEqual(len(rules), 1, "the chip needs exactly one CSS rule")
        self.assertIn("white-space:nowrap", rules[0])

    def test_every_surface_asks_the_helper(self):
        self.assertEqual(SRC.count('class="nig-chip"'), 1, "the chip markup is built in more than one place")
        self.assertGreaterEqual(SRC.count("_notInGameChip(m"), 2, "a locker or MOVE TASKS builds its own chip")
        self.assertNotIn("not in the game yet</span>", SRC)
        self.assertNotIn("made by the board · not in the game yet", SRC)
        self.assertNotIn("in the game — the board made it", SRC)

    def test_a_renamed_mule_is_still_seen(self):
        js = (_fn("_vaultMuleNames") + _fn("_vaultMuleSeenInGame") +
              "var recs=[{sight:{holder:'OldName'}}];"
              "console.log(JSON.stringify([_vaultMuleSeenInGame({name:'NewName',prevName:'OldName'},recs),"
              "_vaultMuleSeenInGame({name:'NewName',aliases:[{name:'oldname'}]},recs),"
              "_vaultMuleSeenInGame({name:'NewName'},recs)]));")
        out = subprocess.run(["node", "-"], input=js, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        self.assertEqual(out.stdout.strip(), "[true,true,false]", out.stderr[-400:])


RED_PROOF = [
    {"why": "v3848 - a rename turns the chip back on (prevName not read)",
     "file": "../bible.html",
     "find": "    [m && m.name, m && m.prevName].concat(",
     "replace": "    [m && m.name].concat(",
     "matches": 1},
    {"why": "v3848 - the chip wraps under the title again",
     "file": "../bible.html",
     "find": ".nig-chip{display:inline-block;white-space:nowrap;",
     "replace": ".nig-chip{display:inline-block;",
     "matches": 1},
    {"why": "v3848 - MOVE TASKS says 'the board made it' again",
     "file": "../bible.html",
     "find": "'</b> in the game (' + esc(why) + ')",
     "replace": "'</b> in the game — the board made it (' + esc(why) + ')",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
