# -*- coding: utf-8 -*-
"""REG-1909 - A SIGHTING THAT GROUNDED LEAVES THE SEEN BANK, PRIOR ROWS INCLUDED.

vault_seen.json keeps UNGROUNDED sightings so a later session can corroborate them. Its writer unioned the prior bank
with this sweep's unsure rows, and its docstring said "Rows that have since GROUNDED are dropped by the caller" - but
the caller filtered only the rows it was handing in, so a row banked in an earlier sweep stayed for ever after it
grounded. The testing-phase pre-run found it on his store: Storm Scarab in owned AND seen, and in the sim Grand Charm
of Vita and Death Loop grounded and were still banked.

The law: `grounded` drops a (name, lane) from the prior rows and the new ones; the lane is part of the identity; with
no `grounded` nothing is dropped (the old contract); and the sweep hands its grounded set in.
Fixtures only: the bank path points at a temp file.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import unittest.mock as mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import control_app as CA  # noqa: E402


def _row(name, lane="stash", sess="s_1"):
    return {"name": name, "lane": lane, "kind": "item", "conf": 0.8, "lastSeenTs": 1,
            "witnesses": [{"session": sess, "frame": "f_%d.jpg" % (1000 + len(name)), "lane": lane, "conf": 0.8}]}


class AGroundedSightingLeavesTheSeenBank(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="vault_seen_law_")
        self.path = os.path.join(self.d, "vault_seen.json")
        with io.open(self.path, "w", encoding="utf-8") as fh:
            json.dump({"rows": [_row("Storm Scarab"), _row("Death Loop")], "ts": 1}, fh)
        self.p = mock.patch.object(CA, "_VAULT_SEEN_PATH", self.path)
        self.p.start()

    def tearDown(self):
        self.p.stop()
        shutil.rmtree(self.d, ignore_errors=True)

    def names(self):
        with io.open(self.path, encoding="utf-8") as fh:
            return sorted((r["name"], r["lane"]) for r in json.load(fh)["rows"])

    def test_a_prior_row_that_grounded_is_dropped(self):
        n = CA.vault_seen_save([_row("Grand Charm of Vita", sess="s_2")], grounded={("Storm Scarab", "stash")})
        self.assertEqual(n, 2)
        self.assertEqual(self.names(), [("Death Loop", "stash"), ("Grand Charm of Vita", "stash")],
                         "a sighting that grounded was kept in the seen bank (REG-1909)")

    def test_the_lane_is_part_of_the_identity(self):
        CA.vault_seen_save([], grounded={("Storm Scarab", "inventory")})
        self.assertIn(("Storm Scarab", "stash"), self.names(), "a grounding in another lane dropped this one")

    def test_no_grounded_set_drops_nothing(self):
        CA.vault_seen_save([_row("Grand Charm of Vita", sess="s_2")])
        self.assertEqual(len(self.names()), 3, "with nothing grounded, a banked sighting was forgotten")

    def test_the_sweep_hands_its_grounded_set_in(self):
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        self.assertEqual(src.count("_n = vault_seen_save(_keep, grounded=_now_owned)"), 1,
                         "the sweep no longer tells the bank what grounded, so prior rows stay for ever")


RED_PROOF = [
    {
        "why": "REG-1909 - the writer stops dropping grounded rows: a sighting that grounded stays banked for ever",
        "file": "tv/control_app.py",
        "find": "        if (name, lane) in _grounded:\n            continue        # REG-1909",
        "replace": "        if False:\n            continue        # REG-1909",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
