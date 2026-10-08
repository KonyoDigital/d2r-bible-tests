# -*- coding: utf-8 -*-
"""#212 (REG-2036) - A READ SAYS WHAT IT IS, ONCE: an inventory read is KEPT ON YOU, one tooltip is one item, and only
a reel is listed as a reel.

From the 2026-10-07 simulation pass on his real reels (TESTING_SIM_RESULTS.md F13-F15):
  * F13 - the receipt chip said "registered" for an inventory read: 'inventory' is one of vault_retro's
    OWNERSHIP_SURFACES, while his ruling (2026-10-07) is that an inventory read is FOUND + "Kept on you", never a stash
    witness. It now says "kept on you"; a stash read still says registered, a floor read still says seen.
  * F14 - "Dwarf Star" and "Dwarf Star Ring" were both stored from ONE tooltip (frame f_1791058494714): the reader
    joined the unique's name to the base line under it, and the vault fold is exact-only. A name now folds when it is a
    roster item's name followed by THAT item's own base (the game's tables) - still exact, never near; and an earlier
    sighting goes through the same fold.
  * F15 - /api/evidence listed "hist" (a directory) and a bare "s_..." session id as reels.
"""
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app as ca  # noqa: E402
import vault_retro as vr  # noqa: E402

_MISSING = object()


def _row(scene, name, frame):
    return {"lane": "deep", "scene": scene, "area": "Harrogath", "names": [name], "sessionId": "s1",
            "frameId": frame, "ts": 1, "completedTs": 10, "gatePass": True}


class AReadSaysWhatItIsOnce(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rcpt2036_")
        self.journal = os.path.join(self.tmp, "sessions.jsonl")
        open(self.journal, "w").close()
        self.old = os.environ.get("TV_SESSIONS")
        os.environ["TV_SESSIONS"] = self.journal
        self.saved = ca.__dict__.get("_RECEIPTS_CACHE", _MISSING)
        ca.__dict__.pop("_RECEIPTS_CACHE", None)

    def tearDown(self):
        if self.old is None:
            os.environ.pop("TV_SESSIONS", None)
        else:
            os.environ["TV_SESSIONS"] = self.old
        if self.saved is _MISSING:
            ca.__dict__.pop("_RECEIPTS_CACHE", None)
        else:
            ca._RECEIPTS_CACHE = self.saved
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _own_by_frame(self, rows):
        with mock.patch.object(ca, "_kai_journal_rows", return_value=(rows, None)):
            got = ca._receipts_stream()
        out = {}
        for r in (got if isinstance(got, list) else (got or {}).get("rows") or []):
            fr = (r.get("refs") or {}).get("frameId")
            if fr:
                out[fr] = r.get("own") or {}
        return out

    def test_an_inventory_read_is_kept_on_you_not_registered(self):
        own = self._own_by_frame([_row("inventory", "Dwarf Star", "f_inv"), _row("stash", "Shako", "f_st"),
                                  _row("gameplay", "Gull", "f_gp")])
        self.assertEqual(sorted(own), ["f_gp", "f_inv", "f_st"], own)
        self.assertTrue(own["f_inv"].get("kept"), "an inventory read is not 'kept on you': %r" % own["f_inv"])
        self.assertIsNot(own["f_inv"].get("banked"), True, "an inventory read still says registered")
        self.assertIs(own["f_st"].get("banked"), True, "a stash read lost its registered chip")
        self.assertIs(own["f_gp"].get("banked"), False, "a floor read is no longer 'seen'")
        with open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as f:
            ui = f.read()
        self.assertEqual(ui.count("var ownChip = own.kept\n"), 1, "the chip does not say 'kept on you' first")

    def test_a_name_joined_to_its_own_base_folds_and_nothing_else_does(self):
        f = vr._name_folder()
        self.assertEqual(f("Dwarf Star Ring"), "Dwarf Star")
        self.assertEqual(f("Harlequin Crest Shako"), "Harlequin Crest")
        self.assertEqual(f("Dwarf Star"), "Dwarf Star")
        self.assertEqual(f("Dwarf Star Amulet"), "Dwarf Star Amulet", "a name folded onto an item that is not its base")
        self.assertEqual(f("Ral Rune"), "Ral Rune", "a rune was folded")
        self.assertEqual(f("Ice Gorgon Crossbow"), "Ice Gorgon Crossbow", "a runeword was folded onto a guess")

    def test_an_earlier_sighting_goes_through_the_same_fold(self):
        w = {"session": "s_A", "frame": "f_1", "conf": 0.9}
        prop = vr.sweep([], sig=lambda p: None, reader=lambda p, s: {"items": []}, classify=lambda p: None,
                        prior_seen=[{"name": "Dwarf Star Ring", "lane": "stash", "witnesses": [w]}])
        names = {str(r.get("name")) for r in (prop.get("unsure") or []) + (prop.get("owned") or [])}
        self.assertIn("Dwarf Star", names, "an earlier joined-name sighting did not fold: %r" % names)
        self.assertNotIn("Dwarf Star Ring", names, names)

    def test_only_a_reel_is_listed_as_a_reel(self):
        self.assertEqual(ca._evidence_reel_id("reel_s_1786999742937_35523"), "reel_s_1786999742937_35523")
        self.assertEqual(ca._evidence_reel_id("s_1788194356763_27344"), "reel_s_1788194356763_27344")
        self.assertIsNone(ca._evidence_reel_id("hist"))
        self.assertIsNone(ca._evidence_reel_id(None))
        with open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as f:
            src = f.read()
        self.assertEqual(src.count('            r = _evidence_reel_id(sg.get("reel"))\n'), 1,
                         "the evidence route lists a reel field without asking whether it is a reel")


RED_PROOF = [
    {"why": "REG-2036 F13 - an inventory read says 'registered' again",
     "file": "control_app.py",
     "find": "            elif _sl in _KEPT_ON_YOU:\n",
     "replace": "            elif False:\n",
     "matches": 1},
    {"why": "REG-2036 F14 - a name joined to its own base line no longer folds",
     "file": "vault_retro.py",
     "find": "        j = joined.get(k)\n",
     "replace": "        j = None\n",
     "matches": 1},
    {"why": "REG-2036 F14 - an earlier sighting skips the fold again",
     "file": "vault_retro.py",
     "find": "        _nm = _fold(str(_row.get(\"name\") or \"\").strip())\n",
     "replace": "        _nm = str(_row.get(\"name\") or \"\").strip()\n",
     "matches": 1},
    {"why": "REG-2036 F15 - a directory name is listed as a reel again",
     "file": "control_app.py",
     "find": "    return (\"reel_\" + m.group(1)) if m else None\n",
     "replace": "    return (\"reel_\" + m.group(1)) if m else (str(r) if r else None)\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
