# -*- coding: utf-8 -*-
"""v2988 — A STORE THAT LOST ITS CONTENTS MUST NOT BE PAPERED OVER WITH SEEDS.

HIS RULING, 2026-09-12: *"for vault the items should not be seeded like the chronicles are.. it
should be able to be saved. or it gets auto saved daily in a ledger just incase if needed to
restore."* And, on the risk this law exists to bound: *"make sure though like when i login to the
console it doesnt start fresh with 0 items everytime... it starts with how i recently left it. as
long as nothing reset it.. or i deleted or did something to it"*.

THE DEFECT, at bible.html ~20718-20745. The detector was already GOOD — it tells a store that
STARTED empty (a new install) from one that BECAME empty, using bare keys no new install has ever
written (`d2r_pieceAlias_v2` / `d2r_chronSyncMerged_v1` / `d2r_installIdCache`). It recorded the
event to `d2r_storeEmptied`, WITH the restore command, and warned the console.
⚠ AND THEN THE SEED FLOOR RAN ANYWAY. Its own comment: "the seed floor below is about to refill it
from the built-in seeds. Anything you had that is in no seed will NOT come back on its own."
Detected-then-overwritten is WORSE than undetected: once the seeds land the store looks FULL, so
the hole is invisible. Measured consequence — 17 uniques and 3 set pieces gone, and the emptying
(`d2r_storeEmptied.at` = 2026-09-08 06:28 UTC) was not noticed for days.

⚠⚠ THE 20 ARE NOT RECOVERABLE, which is why this is a law and not a note. The ledger backups are
excellent — 60 snapshots, every ~5 minutes, 76 d2r_* stores each, with restore_ledger.py — but the
OLDEST is 2026-09-11 03:33 UTC, sixty-nine hours AFTER the loss. A backup that begins after the
incident is not a backup of the incident.

★ WHAT THIS LAW PINS, and the second clause is as important as the first:
  1. the seed floor does NOT run when the store BECAME empty (`_emptiedLoss`);
  2. it DOES still run for a genuine fresh install — otherwise the fix would trade a silent data
     loss for a silently broken first-run, and his "it doesnt start fresh with 0 items everytime"
     is exactly that fear. `_emptiedLoss` can only be true when `_hadRun` is true, and `_hadRun`
     reads keys a new install has never written, so the two cases cannot be confused.
  3. the flag is RAISED where the loss is detected — a clause guarding a variable nobody sets is
     the same as no clause at all. [[plumbing-with-no-tap]]
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

BIBLE = io.open(os.path.join(os.path.dirname(HERE), "bible.html"), encoding="utf-8").read()

#: the live seed-floor condition, anchored at BOTH ends
_COND = re.compile(r"if \(!_rwFreshFlag && ([^)]*?) && window\.D2R_PROFILE !== 'ladder'")


class ALostStoreIsNeverSeededOver(unittest.TestCase):

    def test_the_seed_floor_is_still_findable(self):
        """⚠ A law that cannot find its subject passes having examined nothing."""
        self.assertTrue(_COND.search(BIBLE),
                        "the seed-floor condition moved or was rewritten — this law has no subject")

    def test_the_floor_refuses_a_store_that_became_empty(self):
        m = _COND.search(BIBLE)
        self.assertIn("!_emptiedLoss", m.group(1),
                      "the seed floor no longer consults _emptiedLoss, so a store that LOST its "
                      "contents is refilled from built-in seeds and then looks full — the exact "
                      "shape in which 17 uniques and 3 set pieces went missing")

    def test_the_flag_is_raised_where_the_loss_is_detected(self):
        i = BIBLE.find("the found ledger was EMPTY on a load that had already")
        self.assertGreater(i, 0, "the emptied-store detector is gone")
        near = BIBLE[max(0, i - 600):i + 900]
        self.assertIn("_emptiedLoss = true", near,
                      "nothing SETS _emptiedLoss at the detection site, so the clause guards a "
                      "variable that is never raised — a guard with no tap")

    # ── the round trip: fresh install seeds, lost store does not ──────────────────────────────
    def _floor_runs(self, was_empty, had_run):
        """Execute the SHIPPED condition in node. -> bool | None"""
        m = _COND.search(BIBLE)
        if not m:
            return None
        cond = m.group(0)[len("if ("):]
        js = """
        var _rwFreshFlag = false;
        var _emptiedLoss = %s;
        var window = { D2R_PROFILE: 'main', _isCousinShell: false, _D2R_LEDGER: 'L' };
        var _GRAIL_SEED_LEDGER = 'L';
        var ran = false;
        if (%s && window._D2R_LEDGER === _GRAIL_SEED_LEDGER) { ran = true; }
        console.log(JSON.stringify({ran: ran}));
        """ % ("true" if (was_empty and had_run) else "false", cond)
        d = tempfile.mkdtemp(prefix="seed_law_")
        self.addCleanup(shutil.rmtree, d, True)
        f = os.path.join(d, "t.js")
        io.open(f, "w", encoding="utf-8").write(js)
        try:
            r = subprocess.run(["node", f], capture_output=True, text=True, timeout=60)
        except Exception:
            return None
        if r.returncode != 0:
            return {"__err": (r.stderr or "")[:300]}
        return json.loads(r.stdout.strip().splitlines()[-1]).get("ran")

    def test_a_FRESH_INSTALL_still_gets_its_seeds(self):
        """⚠ HIS FEAR, PINNED. 'it doesnt start fresh with 0 items everytime' — a fix that stopped
        seeding a NEW install would trade a silent loss for a silently empty first run."""
        got = self._floor_runs(was_empty=True, had_run=False)
        if got is None:
            self.skipTest("node unavailable — a skip is NOT a pass")
        self.assertTrue(got, "a genuine fresh install no longer receives the seed floor")

    def test_a_LOST_STORE_is_left_alone(self):
        got = self._floor_runs(was_empty=True, had_run=True)
        if got is None:
            self.skipTest("node unavailable — a skip is NOT a pass")
        self.assertFalse(got, "the seed floor still runs over a store that BECAME empty")

    def test_a_NORMAL_LOGIN_is_untouched(self):
        """His store today: foundLog 432, setPieces 129 — _wasEmpty is False, so nothing changes."""
        got = self._floor_runs(was_empty=False, had_run=True)
        if got is None:
            self.skipTest("node unavailable — a skip is NOT a pass")
        self.assertTrue(got, "an ordinary login stopped reaching the floor, which is a different "
                             "defect from the one this law was written for")


RED_PROOF = [
    {
        "why": "dropping the clause restores the exact behaviour that destroyed 17 uniques and 3 "
               "set pieces — the floor seeding over a store that lost its contents",
        "file": "bible.html",
        "find": "if (!_rwFreshFlag && !_emptiedLoss && window.D2R_PROFILE !== 'ladder'",
        "replace": "if (!_rwFreshFlag && window.D2R_PROFILE !== 'ladder'",
        "matches": 1,
    },
    {
        "why": "leaving the clause but never raising the flag is a guard with no tap: it reads "
               "correct and can never fire",
        "file": "bible.html",
        "find": "        _emptiedLoss = true;   // v2988 — the seed floor MUST NOT run over this",
        "replace": "        /* not raised */",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
