# -*- coding: utf-8 -*-
"""#69 — THE STORE THAT DECIDES *EMPTY* ON THE RIVER MUST SAY WHAT PRODUCED ITS VERDICTS.

MEASURED 2026-09-11 by `verdict_provenance.py` against the live tree:

    44 stores · ANSWERS 6 · PARTIAL 4 · SILENT 16 · REFERENCE 17 · UNKNOWN 1

`retro_triage.json` was SILENT across 437 rows while being the store that decides EMPTY on the
river. It already carried `gateVer` — WHICH classifier — which is a different question from WHAT
WROTE THIS. A verdict with no producer cannot be INVALIDATED: improve the classifier tomorrow and
nothing can name the rows that predate the improvement, so a stale NO survives every later pass
looking exactly like a fresh one. On this river a stale NO means footage is never read again.

⚠ ADDITIVE ONLY, AND THAT IS A STANDING RULING, NOT A SHORTCUT. `verdict_provenance` says it in as
many words: back-filling a producer onto 437 existing rows "would invent provenance for verdicts
nobody can now attribute". Rows written before the stamp stay UNKNOWN. This law pins BOTH halves —
a new row carries it, and an old row is not rewritten. [[unknown-stays-unknown]]

⚠ THE TASK'S HEADLINE FIGURE WAS STALE. "#69: 37 of 43 stores" predates the census gaining a
REFERENCE class — a roster or lookup table has no clock, so the question does not apply to it. The
actionable set is the 16 SILENT, not 37. The census's own docstring carries the same lesson about
its first cut ("18 of 21 and 24 UNKNOWNs — both were the instrument").
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

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app as CA     # noqa: E402
import provenance as PV      # noqa: E402
import retro_triage as RT    # noqa: E402


class ANewVerdictNamesItsProducer(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="prov_law_")
        self.addCleanup(shutil.rmtree, self.d, True)

    def _remember(self):
        reel = os.path.join(self.d, "reel_s_1_2")
        os.makedirs(reel, exist_ok=True)
        ok = RT.remember(reel, hits=3, frames=10, kinds={"stash": 3}, root=self.d)
        self.assertTrue(ok, "remember() refused to write, so nothing here is measured")
        blob, read_ok = RT.load(root=self.d)
        self.assertTrue(read_ok, "the store could not be read back")
        return blob.get("reel_s_1_2") or {}

    def test_the_row_says_what_wrote_it(self):
        pr = PV.read(self._remember())
        self.assertEqual("retro_triage", getattr(pr, "by", None),
                         "a new triage verdict does not name its producer, so it cannot be "
                         "invalidated when the classifier improves — a stale NO would outlive "
                         "every future pass looking exactly like a fresh one")

    def test_the_stamp_carries_a_real_clock(self):
        """[[stale-reading]] — a producer with no time cannot be compared against an improvement."""
        pr = PV.read(self._remember())
        at = getattr(pr, "at", None)
        self.assertIsInstance(at, int, "the stamp carries no epoch-ms clock (at=%r)" % (at,))
        self.assertGreater(at, 1e11,
                           "at=%r looks like epoch SECONDS, not milliseconds — the unit collision "
                           "that dates every row to 1970" % (at,))

    def test_the_verdict_itself_is_unharmed(self):
        """[[sweep-dont-ask]] — the stamp is a label on the verdict, never a replacement for it."""
        row = self._remember()
        for k in ("panels", "frames", "kinds", "ts", "full"):
            self.assertIn(k, row, "stamping dropped %r from the verdict" % k)
        self.assertEqual(3, row.get("panels"))
        self.assertEqual(10, row.get("frames"))

    def test_a_store_that_cannot_be_stamped_is_still_written(self):
        """A diagnostic that can refuse the write would trade a labelled verdict for no verdict."""
        src = io.open(os.path.join(HERE, "retro_triage.py"), encoding="utf-8").read()
        i = src.find("import provenance as _PV")
        self.assertGreater(i, 0, "the stamp call is gone — this law lost its target")
        tail = src[i:i + 260]
        self.assertIn("except Exception:", tail,
                      "the provenance stamp is not swallowed, so a failure in the LABEL would "
                      "cost the VERDICT — the expensive thing this store exists to keep")


class TheStampIsNeverAFakeReel(unittest.TestCase):
    """⚠⚠ THE HAZARD THE CODEBASE NAMES BY NAME, in reel_retention._tombstone: "NEVER do this to a
    ROW-KEYED store (retro_triage, chron_hunt_memory, main_character, capture_doors): a top-level
    `_prov` there becomes a FAKE ROW that blueprint.py publishes as a reel count of 456 and
    printer_reach admits as a reel."

    `retro_triage.json` is keyed BY REEL at the top level, so the stamp must go INSIDE each row.
    A store-level stamp — the right move for the flat `{reels, updatedTs}` tombstone file — would
    here add one phantom reel to every count that enumerates the top level. Same module, same
    helper, opposite correct answer, decided by the store's SHAPE.
    [[zero-needs-a-denominator]] [[label-outlived-referent]]"""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="prov_shape_")
        self.addCleanup(shutil.rmtree, self.d, True)
        for name in ("reel_s_1_2", "reel_s_3_4"):
            os.makedirs(os.path.join(self.d, name), exist_ok=True)
            RT.remember(os.path.join(self.d, name), hits=1, frames=5, kinds={}, root=self.d)
        self.blob, ok = RT.load(root=self.d)
        self.assertTrue(ok, "the store could not be read back")

    def test_the_top_level_gains_no_phantom_reel(self):
        self.assertNotIn("_prov", self.blob,
                         "the provenance block landed at the TOP LEVEL of a reel-keyed store, so "
                         "every reader that enumerates it now counts one reel that does not "
                         "exist — blueprint.py publishes it and printer_reach admits it")
        self.assertEqual(2, len(self.blob),
                         "two reels were surveyed but the store holds %d top-level key(s): %s"
                         % (len(self.blob), sorted(self.blob)))

    def test_each_row_carries_it_instead(self):
        for k, row in self.blob.items():
            self.assertEqual("retro_triage", getattr(PV.read(row), "by", None),
                             "row %r does not name its producer" % k)


class ThePastIsNotRewritten(unittest.TestCase):
    """The standing ruling: stamping rows nobody can attribute would INVENT provenance."""

    def test_an_existing_unstamped_row_survives_a_load(self):
        d = tempfile.mkdtemp(prefix="prov_old_")
        self.addCleanup(shutil.rmtree, d, True)
        p = os.path.join(d, "retro_triage.json")
        old = {"reel_s_old_1": {"panels": 0, "frames": 99, "kinds": {}, "ts": 1, "full": True}}
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(old))
        blob, ok = RT.load(root=d)
        self.assertTrue(ok)
        row = blob.get("reel_s_old_1") or {}
        pr = PV.read(row)
        self.assertIsNone(getattr(pr, "by", None),
                          "an existing unstamped row came back carrying a producer — the past was "
                          "back-filled, which invents provenance for a verdict nobody can now "
                          "attribute")


class ADoorKeyedStoreStampsItsDoors(unittest.TestCase):
    """#69 / v2976 — capture_doors.json is keyed BY DOOR at the top level, and
    `blueprint.capture_doors()` enumerates that top level. reel_retention._tombstone names this
    exact store in its warning: a top-level `_prov` here "becomes a FAKE ROW that blueprint.py
    publishes as a reel count". So the stamp goes INSIDE each door, exactly like retro_triage.

    Each door carries a per-door Wilson ledger — reels opened vs reels that held film — so a tally
    accumulated under an older crediting rule is precisely what a later rule must be able to
    re-judge. [[zero-needs-a-denominator]]"""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="prov_doors_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.p = os.path.join(self.d, "capture_doors.json")
        self._was = CA._capture_doors_path
        CA._capture_doors_path = lambda: self.p
        self.addCleanup(setattr, CA, "_capture_doors_path", self._was)
        self.live = {"mini": {"blank": 2, "filmed": 1}, "onair": {"blank": 19, "filmed": 1},
                     "shadow": {"blank": 263, "filmed": 181}}
        self.before = json.loads(json.dumps(self.live))
        CA._capture_door_save(self.live)
        self.blob = json.load(io.open(self.p, encoding="utf-8"))

    def test_no_phantom_door_appears(self):
        self.assertNotIn("_prov", self.blob,
                         "the stamp landed at the TOP LEVEL of a door-keyed store, so "
                         "blueprint.capture_doors() now counts a door that does not exist")
        self.assertEqual(3, len(self.blob),
                         "three doors were saved but the store holds %d top-level key(s): %s"
                         % (len(self.blob), sorted(self.blob)))

    def test_every_door_names_its_producer(self):
        for k, row in self.blob.items():
            self.assertEqual("control_app", getattr(PV.read(row), "by", None),
                             "door %r does not name its producer" % k)

    def test_the_door_tallies_are_unharmed(self):
        self.assertEqual(263, self.blob["shadow"].get("blank"))
        self.assertEqual(181, self.blob["shadow"].get("filmed"))

    def test_the_callers_live_dict_is_not_mutated(self):
        """The door dict is live state the console keeps using after the save."""
        self.assertEqual(self.before, self.live,
                         "saving mutated the caller's door dict, so _prov travels to every other "
                         "reader of the live state")


RED_PROOF = [
    {
        "why": "stamping the BLOB instead of each door is the hazard reel_retention names for this "
               "very store: blueprint.capture_doors() enumerates the top level, so a _prov key "
               "there is published as a fourth door that does not exist",
        "file": "control_app.py",
        "find": '        d = dict((_k, (_PV.stamp_row(_v, by="control_app", extra={"store": "capture_doors"})\n                       if isinstance(_v, dict) else _v))\n                 for _k, _v in (d or {}).items())\n',
        "replace": '        d = _PV.stamp(d, by="control_app", extra={"store": "capture_doors"})\n',
        "matches": 1,
    },
    {
        "why": "stamping the BLOB instead of the ROW is the exact hazard reel_retention names: a "
               "reel-keyed store gains a top-level _prov, and every reader that enumerates it "
               "counts one reel that does not exist",
        "file": "retro_triage.py",
        "find": '        row = _PV.stamp_row(row, by="retro_triage")',
        "replace": '        blob = _PV.stamp(blob, by="retro_triage")',
        "matches": 1,
    },
    {
        "why": "removing the stamp call puts the store back to SILENT: a new triage verdict that "
               "cannot be invalidated when the classifier improves, over the store that decides "
               "EMPTY on the river",
        "file": "retro_triage.py",
        "find": '        row = _PV.stamp_row(row, by="retro_triage")\n',
        "replace": "",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
