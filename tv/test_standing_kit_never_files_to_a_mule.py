# -*- coding: utf-8 -*-
"""REG-2028 - THE CUBE, THE TOMES, WIRT'S LEG AND KEYS NEVER FILE TO A MULE. #211.

MEASURED on the shipped page: suggestMule('Horadric Cube') -> uni-weap ("the register would file the Cube into the weapons
mule"), and GrokBot saw "Tome of Identify ⚠ filed in UNI-WEAPONS" on his v3614 board. They are standing kit - §29, the
furniture law (_FURNITURE_WORDS / _FURNITURE_WHOLE, pinned to tv/inventory_law.py by test_main_gear_never_files_to_a_mule) -
and ride on his character. The router now asks that ONE list on the exact name and answers __keep. The list's bare 'tome'
word is NOT used for routing (it would also match a real off-hand), so a name that only CONTAINS 'tome' keeps its route.
NO CHROME AT ALL = a declared skip, never a pass.
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import test_a_sweep_never_reticks_what_he_unticked as H  # noqa: E402  (its Board drives the shipped page)

_B = {}
KIT = ("Horadric Cube", "Tome of Identify", "Tome of Town Portal", "Wirt's Leg", "Key")


def board():
    if "b" not in _B:
        _B["b"] = H.Board().open()
    return _B["b"]


def tearDownModule():
    b = _B.pop("b", None)
    if b is not None:
        b.close()


@unittest.skipUnless(os.path.exists(H.RC.CHROME), "no Chrome/Chromium on this machine - UNMEASURED here, not passing")
class StandingKitNeverFilesToAMule(unittest.TestCase):

    def test_kit_is_kept_on_his_character_and_real_items_keep_their_route(self):
        o = board().run("OUT.r = {}; %s.forEach(function(n){ var s = window.suggestMule(n); OUT.r[n] = s ? s.id : null; });"
                        % json.dumps(list(KIT) + ["Nokozan Relic", "Grief"]))["r"]
        for n in KIT:
            self.assertEqual(o[n], "__keep", "%s - standing kit - was routed to %r" % (n, o[n]))
        self.assertEqual(o["Nokozan Relic"], "uni-small", "the control: a unique amulet lost its mule")
        self.assertEqual(o["Grief"], "shared", "the control: war gear lost the shared stash")


RED_PROOF = [
    {"why": "REG-2028 - the Horadric Cube and the tomes are filed into the weapons mule again",
     "file": "bible.html",
     "find": "      if (_kitF && _kitL.indexOf(_kitF) >= 0)\n",
     "replace": "      if (false)\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
