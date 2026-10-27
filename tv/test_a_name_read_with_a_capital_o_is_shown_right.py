# -*- coding: utf-8 -*-
"""GrokBot bug 11 (2026-10-27) - A NAME READ WITH A CAPITAL O IS SHOWN RIGHT, AND NOTHING IS REFUSED FOR IT.

The Mac's learned characters showed "KOnyORush", "SOcket", "ArmOr", "WeapOn" and "SetOnami". Both reader prompts say to
write the font's O as the letter O, so a mixed-case answer carries a capital O inside a word, and _clean_name kept mixed
case as read. A tie in the spelling vote then went to the capital-O form, because save() writes with sort_keys and 'O'
sorts before 'o'. Socket, Armor and Weapon are his real level-1 mules (this module's own SOCKET example), so the fix is
the SPELLING - a denylist of "UI words" would have refused his mules.

Driven on char_select itself:
  - _clean_name turns a capital O inside a word into o, keeps a leading O, and still title-cases an all-caps answer;
  - a ledger that stored forms {"SOcket": 2, "Socket": 2} and was saved and loaded shows "Socket" - nothing rewritten;
  - the KEY never moved (_fold was always case-free).
RED_PROOF below.
"""
import copy
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

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


def _char(name, forms, cls="Amazon", visits=("v1", "v2")):
    return {"name": name, "forms": dict(forms), "cls": {cls: list(visits)},
            "visitLevel": {v: 1 for v in visits}, "titles": {}, "firstTs": 1, "lastTs": 2}


class ANameReadWithACapitalOIsShownRight(unittest.TestCase):

    def test_a_capital_o_inside_a_word_is_a_small_o(self):
        got = {n: CS._clean_name(n) for n in ("KOnyORush", "SOcket", "ArmOr", "WeapOn", "SetOnami",
                                              "OsenbeiChan", "MuleBox", "KonyoLock", "RUNEWORDER")}
        self.assertEqual(got, {"KOnyORush": "KonyoRush", "SOcket": "Socket", "ArmOr": "Armor", "WeapOn": "Weapon",
                               "SetOnami": "Setonami", "OsenbeiChan": "OsenbeiChan", "MuleBox": "MuleBox",
                               "KonyoLock": "KonyoLock", "RUNEWORDER": "Runeworder"})
        self.assertEqual(CS._fold("SOcket"), "socket", "the key moved - every gear and build link would break")

    def test_a_stored_tie_reads_as_the_plain_spelling_after_a_save_and_a_load(self):
        d = {"chars": {"socket": _char("SOcket", {"SOcket": 2, "Socket": 2})}}
        before = copy.deepcopy(d)
        tmp = tempfile.mkdtemp(prefix="tvd_charname_")
        path = os.path.join(tmp, ".char_roster.json")
        with mock.patch.dict(os.environ, {"TV_CHARS_LEARNED": path}):
            CS.save(d)
            back = CS.load()
        self.assertIsNotNone(back, "PREMISE: the saved ledger did not load")
        rows = CS.learned(back)
        self.assertEqual([r["name"] for r in rows], ["Socket"], rows)
        self.assertEqual(back["chars"]["socket"]["forms"], {"SOcket": 2, "Socket": 2},
                         "the read rewrote the stored spellings - nothing may be rewritten")
        self.assertEqual(d, before)

    def test_a_character_is_never_refused_for_its_spelling(self):
        d = {"chars": {k: _char(n, {n: 2}) for k, n in (("armor", "ArmOr"), ("weapon", "WeapOn"), ("socket", "SOcket"))}}
        self.assertEqual(sorted(r["name"] for r in CS.learned(d)), ["Armor", "Socket", "Weapon"])


RED_PROOF = [
    {"why": "bug 11 - a mixed-case answer keeps its capital O again (KOnyORush, SOcket)",
     "file": "tv/char_select.py",
     "find": "    return s.title() if s.isupper() else _o_case(s)\n",
     "replace": "    return s.title() if s.isupper() else s\n",
     "matches": 1},
    {"why": "bug 11 - the shown name is the stored one again, so a tie saved as SOcket shows SOcket",
     "file": "tv/char_select.py",
     # REG-2692 (#211) built the row in a local before appending it; the shown name is still read in one place
     "find": "        row = {\"name\": _shown(c), \"key\": key,",
     "replace": "        row = {\"name\": c.get(\"name\"), \"key\": key,",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
