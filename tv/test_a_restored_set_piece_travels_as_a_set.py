# -*- coding: utf-8 -*-
"""#246 L3 — A RESTORED SET PIECE TRAVELS AS A SET, NEVER AS A "UNIQUE".

The 15:28:34 event on 2026-09-16: a ledger restore sent every d2r_foundLog key through the UNIQUES half of the
proposal (tv/ledger_restore.py RESTORABLE = {"foundLog": "uniques", ...}). A backup's found ledger carries every
set piece too — toggleSetPiece writes the found ledger by design — so each piece rode the uniques half, the
board's uniques branch called toggleOwned, and toggleOwned's else-branch dropped the piece into d2r_owned. The
sorter then filed it: 19 set pieces became mule filings that way.

WHAT THIS LAW HOLDS (the REAL module, called; its board half is test_found_ever_never_files_to_a_mule):
  · plan() carries the backup's own set-piece list beside the gaps (setPieceNames);
  · proposal_from() sends a name that list names through `sets` only — once, even when it is missing from both
    stores — and leaves real uniques in `uniques`;
  · the shape is still the one the board accepts: lists of {name} rows.
RED_PROOF below.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

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

import ledger_restore as LR  # noqa: E402

PIECE = "Aldur's Advance (boots)"
PIECE2 = "Tal Rasha's Horadric Crest (helm)"
UNIQUE = "Nagelring"
ROUTE = {"id": "law-route", "p": "main"}


class ARestoredSetPieceTravelsAsASet(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="restore_sets_law_")
        blob = {"route": ROUTE, "takenAt": "2026-09-16T09:26:35Z",
                "ledger": {"foundLog": {UNIQUE: "Aug 1", PIECE: "Aug 2", PIECE2: "Aug 3"},
                           "setPieces": [PIECE, PIECE2]}}
        with io.open(os.path.join(self.tmp, "ledger_2026-09-16_092635.json"), "w", encoding="utf-8") as fh:
            json.dump(blob, fh)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _proposal(self, current):
        plan = LR.plan(ROUTE, current, d=self.tmp)
        self.assertTrue(plan.get("ok"), plan)
        return plan, LR.proposal_from(plan)

    def test_the_plan_carries_the_backups_set_piece_list(self):
        plan, _p = self._proposal({"foundLog": {}, "setPieces": []})
        self.assertEqual(sorted([PIECE, PIECE2]), plan.get("setPieceNames"),
                         "the plan does not say which names the backup holds as set pieces")

    def test_a_piece_missing_everywhere_travels_once_as_a_set(self):
        _plan, p = self._proposal({"foundLog": {}, "setPieces": []})
        uni = [r["name"] for r in p["wouldAdd"].get("uniques", [])]
        sets = [r["name"] for r in p["wouldAdd"].get("sets", [])]
        self.assertEqual([UNIQUE], uni, "a set piece rode the UNIQUES half — the 15:28:34 refill: %r" % uni)
        self.assertEqual(sorted([PIECE, PIECE2]), sorted(sets))
        self.assertEqual(len(sets), len(set(sets)), "a piece travels twice: %r" % sets)

    def test_a_piece_missing_only_from_the_found_ledger_still_travels_as_a_set(self):
        _plan, p = self._proposal({"foundLog": {UNIQUE: "Aug 1"}, "setPieces": [PIECE, PIECE2]})
        wa = p["wouldAdd"]
        self.assertNotIn("uniques", wa, "a set piece was sent as a unique: %r" % wa)
        self.assertEqual(sorted([PIECE, PIECE2]), sorted(r["name"] for r in wa.get("sets", [])))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#246 W0c - a restored set piece rides the UNIQUES half again and falls into d2r_owned on the board",
        "file": "ledger_restore.py",
        "find": "    if _pieces and add.get(\"uniques\"):\n",
        "replace": "    if False and _pieces and add.get(\"uniques\"):\n",
        "matches": 1,
    },
]
