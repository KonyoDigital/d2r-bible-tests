# -*- coding: utf-8 -*-
"""#86 gap audit 34 (REG-1781) — A REEL AT PRINTER IS NOT HELD WHILE THE VAULT OWES IT A READ.

Retention's tag says why a reel is still on disk. The shelf counted a lane's work from that tag
alone. A reel at PRINTER that the tag calls `recent` was held. One it calls `zero-pages` was
the chronicle's. vault_owes_read already said the vault owes both a read, and the sweeper's list
already followed it. The census said the vault lane had nothing owed.

  · DRIVEN: the sweeper's own fixture. The census names the same three reels. `recent` at
    PRINTER is not held. `zero-pages` stays on the chronicle lane as well.
  · DRIVEN: a stamp log that will not read. The vault's number is UNKNOWN, not the tags alone,
    and not idle. The chronicle's count still stands. The sweeper answers None for the same pair.
  · DRIVEN: a seal store that will not read adds nothing through PRINTER. The tag the vault
    already owns is still counted. A fixture at PRINTER stays held.

Nothing here reads his shelf, his stamp log, or his seals. RED_PROOF below.
[[the-unjoined-end]] [[unknown-stays-unknown]]
"""
import os
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import shelf_driver as SD  # noqa: E402


KEPT = [
    {"reel": "reel_s_10_a", "tag": "zero-pages"},     # PRINTER -> vault read, and still chronicle
    {"reel": "reel_s_11_b", "tag": "recent"},         # PRINTER -> vault read, not held
    {"reel": "reel_s_12_c", "tag": "test-fixture"},   # PRINTER -> vetoed
    {"reel": "reel_s_13_d", "tag": "recent"},         # EMPTY   -> held
    {"reel": "reel_s_14_e", "tag": "zero-pages"},     # PRINTER, already sealed
    {"reel": "reel_s_15_f", "tag": "vault-owes"},     # the tag the vault already owns
]
POS = {"reel_s_10_a": "PRINTER", "reel_s_11_b": "PRINTER", "reel_s_12_c": "PRINTER",
       "reel_s_13_d": "EMPTY", "reel_s_14_e": "PRINTER", "reel_s_15_f": "CAPTURE"}
SEALED = {"s_14_e": {"by": "vault"}}
NAMED = ["reel_s_10_a", "reel_s_11_b", "reel_s_15_f"]


def _base(reel):
    return os.path.basename(str(reel or ""))


class AReelTheVaultOwesIsNotHeld(unittest.TestCase):

    def _work(self, kept, pos, seals):
        with mock.patch.object(SD, "plan", lambda h: {
                "ok": True, "kept": [dict(k) for k in kept], "onDisk": 6, "candidates": []}), \
                mock.patch.object(SD, "_proven_empty", lambda r: False):
            return SD.work(hist="fixture-hist", positions=pos, seals=seals)

    def _rows(self, w):
        c = SD.lane_census(work_=w, beats={})
        self.assertTrue(c.get("ok"), c)
        return {r["lane"]: r for r in c["rows"]}

    def _sweeper(self, kept, pos, seals):
        import control_app as ca
        import reel_retention as rr
        with mock.patch.object(rr, "plan", lambda h, **k: {"ok": True, "kept": [dict(x) for x in kept]}), \
                mock.patch.object(ca, "_vault_positions_and_seals", lambda: (pos, seals)), \
                mock.patch.object(SD, "_proven_empty", lambda r: False):
            got = ca._vault_owed_reels(hist=tempfile.gettempdir())
        if got is None:
            return None
        return sorted(_base(g) for g in got)

    def _vault(self, w):
        return sorted(_base(r.get("reel")) for r in (w.get("owed") or [])
                      if "vault" in SD._lanes_of(r))

    def test_the_census_names_the_reels_the_sweeper_names(self):
        w = self._work(KEPT, POS, SEALED)
        rows = self._rows(w)
        self.assertEqual(self._vault(w), NAMED,
                         "the shelf's vault count is not the read the rule already owes: %r" % self._vault(w))
        self.assertEqual(rows["vault"]["owed"], len(NAMED), rows["vault"])
        self.assertIs(w.get("vaultKnown"), True)
        held = sorted(_base(r.get("reel")) for r in w["held"])
        self.assertEqual(held, ["reel_s_12_c", "reel_s_13_d"],
                         "a reel at PRINTER the vault owes was still held: %r" % held)
        chron = sorted(_base(r.get("reel")) for r in w["owed"] if r.get("lane") == "chronicle")
        self.assertEqual(chron, ["reel_s_10_a", "reel_s_14_e"],
                         "a zero-pages reel left the chronicle lane when the vault's read was added: %r" % chron)
        self.assertEqual(rows["chronicle"]["owed"], 2, rows["chronicle"])
        self.assertEqual(self._sweeper(KEPT, POS, SEALED), NAMED,
                         "the sweeper's list moved, so agreeing with it would no longer be the rule")

    def test_an_unreadable_river_is_unknown_not_idle(self):
        kept = [{"reel": "reel_s_10_a", "tag": "zero-pages"},
                {"reel": "reel_s_11_b", "tag": "recent"}]
        w = self._work(kept, None, {})
        rows = self._rows(w)
        self.assertIs(w.get("vaultKnown"), False, w.get("vaultWhy"))
        self.assertIsNone(rows["vault"]["owed"], rows["vault"])
        self.assertEqual(rows["vault"]["state"], SD.UNKNOWN, rows["vault"])
        self.assertNotEqual(rows["vault"]["state"], SD.IDLE, rows["vault"])
        self.assertIn("UNKNOWN", rows["vault"]["why"])
        self.assertEqual(rows["chronicle"]["owed"], 1,
                         "an unreadable river also blanked the chronicle count: %r" % rows["chronicle"])
        self.assertIsNone(self._sweeper(kept, None, {}),
                          "the sweeper still published a list when the river could not be read")

    def test_an_unreadable_seal_store_adds_nothing_through_printer(self):
        w = self._work(KEPT, POS, None)
        rows = self._rows(w)
        self.assertEqual(self._vault(w), ["reel_s_15_f"],
                         "a seal store that would not read still bought a PRINTER reel: %r" % self._vault(w))
        self.assertEqual(rows["vault"]["owed"], 1, rows["vault"])
        held = sorted(_base(r.get("reel")) for r in w["held"])
        self.assertIn("reel_s_11_b", held)
        self.assertIn("reel_s_12_c", held)
        self.assertEqual(self._sweeper(KEPT, POS, None), ["reel_s_15_f"])


RED_PROOF = [
    {"why": "REG-1781 - the shelf stops asking the vault's own rule, so a reel at PRINTER is held again",
     "file": "shelf_driver.py",
     "find": "    if not reel or not vault_owes_read(tag, station, reel):\n"
             "        return None\n"
             "    if tag in lane_read_tags(\"vault\"):\n"
             "        return \"vault\"\n"
             "    if not isinstance(seals, dict):\n"
             "        return None\n"
             "    import reel_retention as _rr\n"
             "    if _rr.lookup_either_way(seals, reel) is not None:\n"
             "        return None\n"
             "    return \"vault\"\n",
     "replace": "    return None\n",
     "matches": 1},
    {"why": "REG-1781 - an unreadable stamp log falls through to the tag count, and that count reads as idle",
     "file": "shelf_driver.py",
     "find": "        elif lane == \"vault\" and w.get(\"vaultKnown\") is False:\n",
     "replace": "        elif lane == \"vault\" and False:\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
