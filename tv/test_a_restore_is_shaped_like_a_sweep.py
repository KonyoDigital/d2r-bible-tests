# -*- coding: utf-8 -*-
"""A RESTORE PROPOSAL MUST BE SHAPED LIKE A SWEEP — THIS DOOR HAD NEVER APPLIED ANYTHING.

`ledger_restore.proposal_from()` built `add[half][name] = []` — a DICT keyed by name. The board's
`chronicleApply` in bible.html does `(add.uniques || []).forEach(...)`, and a plain object has no
`forEach`. So every restore that ever reached the board died with
*"(add.uniques || []).forEach is not a function"* and wrote NOTHING.

MEASURED 2026-09-16 on his live board, restoring 85 uniques + 50 sets after an install-id change
wiped his visible ledger: the call REACHED bible.html — the TypeError quotes bible.html's own
v2690 comment back — and every count was unchanged afterwards. With the shape corrected, the same
proposal moved foundLog 363 -> 445, setPieces 83 -> 133, chronFound 280 -> 309.

⚠⚠ WHY NOTHING CAUGHT IT FOR 478 VERSIONS. `plan()` is read-only and its counts were always
correct, so the dry run, the plan endpoint and every test of them looked right. The only half that
was wrong was the half that crosses into the board, and nothing on the Python side of that boundary
could see it. Two halves, each correct on its own, joined at neither. [[the-unjoined-end]]

⚠ THE SHAPE IS NOT INVENTED HERE. A real sweep already ships `"wouldAdd": {lg: [{"name": n, ...}]}`
at two call sites in control_app.py, and `proposal_from`'s own docstring promises "the same
vocabulary a sweep uses". It said so and did the other thing — so this pins the PROMISE, not a
number. [[regression-guard]] [[source-reading-guard]]
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

import ledger_restore as LR


def _plan(uni, sets):
    return {"ok": True, "file": "ledger_test.json",
            "stores": {"foundLog": {"half": "uniques", "missing": list(uni)},
                       "setPieces": {"half": "sets", "missing": list(sets)}}}


class TestARestoreIsShapedLikeASweep(unittest.TestCase):

    def test_each_half_is_a_list_the_board_can_forEach(self):
        """The defect exactly: an object has no forEach, so the board threw and wrote nothing."""
        wa = (LR.proposal_from(_plan(["Shako", "Mara's Kaleidoscope"], ["Tal Rasha's Fine-Spun Cloth"]))
              or {}).get("wouldAdd") or {}
        self.assertTrue(wa, "proposal_from returned nothing for a plan with two real gaps")
        for half in ("uniques", "sets"):
            self.assertIn(half, wa, "the %s half vanished from the proposal" % half)
            self.assertIsInstance(
                wa[half], list,
                "wouldAdd.%s is %s, not a list — bible.html calls .forEach on it and a plain "
                "object has none, which is the live defect this pins"
                % (half, type(wa[half]).__name__))

    def test_every_row_carries_a_name_the_board_reads(self):
        """bible.html reads `row && (row.name || row)`. A row with neither is a silent skip."""
        wa = (LR.proposal_from(_plan(["Shako"], ["Angelic Halo (ring)"])) or {}).get("wouldAdd") or {}
        seen = 0
        for half, rows in wa.items():
            for row in rows:
                seen += 1
                name = row.get("name") if isinstance(row, dict) else row
                self.assertTrue(
                    isinstance(name, str) and name.strip(),
                    "a %s row carries no readable name (%r) — the board would skip it in silence"
                    % (half, row))
        # ⚠ a denominator, so a vacuous pass cannot wear a green tick [[zero-needs-a-denominator]]
        self.assertEqual(seen, 2, "expected 2 rows to inspect, inspected %d" % seen)

    def test_it_survives_json_round_trip_to_the_board(self):
        """The proposal crosses into JS as JSON. A shape that only holds in Python is no shape."""
        prop = LR.proposal_from(_plan(["Shako"], []))
        rt = json.loads(json.dumps(prop))
        self.assertIsInstance(rt["wouldAdd"]["uniques"], list)
        self.assertEqual(rt["wouldAdd"]["uniques"][0]["name"], "Shako")

    def test_no_gap_still_means_no_proposal(self):
        """The opposite error: a restore with nothing to add must stay None, not ship an empty add."""
        self.assertIsNone(LR.proposal_from(_plan([], [])),
                          "a plan with no missing names produced a proposal — that would ask the "
                          "board to apply nothing and report it as a restore")


if __name__ == "__main__":
    unittest.main(verbosity=2)
