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
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app as CA     # noqa: E402
import main_character as MC  # noqa: E402
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


class TheHuntMemoryDoesNotFoolItsOwnCorroborator(unittest.TestCase):
    """#69 / v2977 — chron_hunt_memory.json is keyed BY ITEM, and a blob stamp here would DEFEAT A
    LIVE CORROBORATOR rather than merely look untidy.

    `corroborate.py`'s `hunt-remembers` invariant is literally `return len(d)` against a right() of
    0. It exists because the hunt once re-bought the same 8 names for eight hours — 1,717 sightings
    that "looked exactly like healthy activity". A top-level `_prov` makes an EMPTY memory report
    1, so the one instrument watching for that spend would report the memory fine while nothing is
    remembered. [[zero-needs-a-denominator]]"""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="prov_hunt_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.p = os.path.join(self.d, "chron_hunt_memory.json")
        was = CA._chron_reads_path
        CA._chron_reads_path = lambda: self.p
        self.addCleanup(setattr, CA, "_chron_reads_path", was)

    def _save(self, rec):
        CA._chron_reads_save(rec)
        return json.load(io.open(self.p, encoding="utf-8"))

    def test_the_corroborators_count_is_unmoved(self):
        blob = self._save({"sets|A": {"empty": True, "ts": 1}, "sets|B": {"empty": False, "ts": 2}})
        self.assertEqual(2, len(blob),
                         "two names were remembered but len(d) is %d — corroborate.hunt-remembers "
                         "reads exactly this number" % len(blob))
        self.assertNotIn("_prov", blob,
                         "a top-level _prov inflates the hunt memory's count, which is the number "
                         "the corroborator compares against zero")

    def test_an_empty_memory_still_counts_zero(self):
        """The state the invariant exists to catch: reads being spent while nothing is remembered."""
        blob = self._save({})
        self.assertEqual(0, len(blob),
                         "an EMPTY hunt memory reports %d, so the corroborator would say the "
                         "memory is fine while the hunt re-buys the same names" % len(blob))

    def test_every_remembered_name_carries_its_producer(self):
        blob = self._save({"sets|A": {"empty": True, "ts": 1}})
        for k, row in blob.items():
            self.assertEqual("control_app", getattr(PV.read(row), "by", None),
                             "remembered name %r does not name its producer" % k)

    def test_the_callers_live_record_is_not_mutated(self):
        live = {"sets|A": {"empty": True, "ts": 1}}
        before = json.loads(json.dumps(live))
        self._save(live)
        self.assertEqual(before, live,
                         "saving mutated the caller's record, so _prov travels to every other "
                         "reader of the live hunt memory")


class TheCharacterLedgerKeepsItsTrackedCount(unittest.TestCase):
    """#69 / v2978 — main_character.json is keyed BY ITEM NAME, and the module COUNTS ITS OWN STORE:

        tracked = len(_load() or {})        (main_character.py:212 and :235)
        print("  tracked items: %d …")      (:254)

    So a top-level `_prov` adds one phantom item to a number he reads. Third store in a row where
    the READERS, not the shape, decided how bad a blob stamp would have been: blueprint publishing
    a row count (REG-972), a corroborator comparing len() against zero (REG-980), and here a
    visible tally. [[zero-needs-a-denominator]]"""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="prov_mc_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self._was = MC.LEDGER
        MC.LEDGER = os.path.join(self.d, "main_character.json")
        self.addCleanup(setattr, MC, "LEDGER", self._was)

    def test_the_tracked_count_is_unmoved(self):
        MC._save({"dwarf star": {"slot": "ring"}, "war traveler": {"slot": "boots"}})
        blob = json.load(io.open(MC.LEDGER, encoding="utf-8"))
        self.assertNotIn("_prov", blob,
                         "the stamp landed at the TOP LEVEL of an item-keyed ledger, so the "
                         "tracked count he reads gained an item that does not exist")
        self.assertEqual(2, len(MC._load() or {}),
                         "two items were saved but tracked reads %d" % len(MC._load() or {}))

    def test_an_empty_ledger_still_tracks_zero(self):
        MC._save({})
        self.assertEqual(0, len(MC._load() or {}),
                         "an EMPTY ledger reports %d tracked item(s)" % len(MC._load() or {}))

    def test_every_item_names_its_producer(self):
        MC._save({"dwarf star": {"slot": "ring"}})
        blob = json.load(io.open(MC.LEDGER, encoding="utf-8"))
        for k, row in blob.items():
            self.assertEqual("main_character", getattr(PV.read(row), "by", None),
                             "item %r does not name its producer" % k)

    def test_the_callers_ledger_is_not_mutated(self):
        live = {"dwarf star": {"slot": "ring"}}
        before = json.loads(json.dumps(live))
        MC._save(live)
        self.assertEqual(before, live, "saving mutated the caller's ledger")


class OnlyTheRowsThisWriteChangedAreStamped(unittest.TestCase):
    """★ THE SECOND EYE'S FINDING on v2976, and it was shipped THREE TIMES before this law existed.

    `stamp_row` REPLACES any existing block, so mapping it over a whole store relabels every
    sibling on every save. Two distinct lies, both of which the eye named:

      BACK-FILL   first save after the upgrade: rows that are months of tallies nobody in this
                  process wrote would claim `by=control_app` at that instant — the exact thing
                  `ThePastIsNotRewritten`, in this same file, exists to forbid.
      CHURN       `after_session_ended` credits ONE door and persists the blob; every other door
                  gets a fresh at/ver, so "which tallies predate v3000?" answers "none of them".

    So a row is stamped when and only when THIS write changed it. An untouched row keeps whatever
    block it had — including keeping NONE. [[unknown-stays-unknown]]"""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="prov_chg_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.p = os.path.join(self.d, "capture_doors.json")
        was = CA._capture_doors_path
        CA._capture_doors_path = lambda: self.p
        self.addCleanup(setattr, CA, "_capture_doors_path", was)
        # a LEGACY store: real tallies, no stamps anywhere
        io.open(self.p, "w", encoding="utf-8").write(json.dumps(
            {"mini": {"blank": 2, "filmed": 1}, "onair": {"blank": 19, "filmed": 1},
             "shadow": {"blank": 263, "filmed": 181}}))

    def _save_touching_onair(self):
        cur = json.load(io.open(self.p, encoding="utf-8"))
        cur["onair"]["blank"] = 20
        CA._capture_door_save(cur)
        return json.load(io.open(self.p, encoding="utf-8"))

    def test_the_row_we_changed_is_stamped(self):
        blob = self._save_touching_onair()
        self.assertEqual("control_app", getattr(PV.read(blob["onair"]), "by", None),
                         "the door this write actually changed does not name its producer")

    def test_untouched_legacy_rows_are_not_back_filled(self):
        blob = self._save_touching_onair()
        for k in ("mini", "shadow"):
            self.assertIsNone(getattr(PV.read(blob[k]), "by", None),
                              "%r was BACK-FILLED: a tally nobody in this process wrote now "
                              "claims us as its producer, which invents provenance" % k)

    def test_untouched_rows_keep_their_tallies(self):
        blob = self._save_touching_onair()
        self.assertEqual(263, blob["shadow"].get("blank"))
        self.assertEqual(3, len(blob), "the door count moved: %s" % sorted(blob))

    def test_a_no_op_save_does_not_churn_the_stamps(self):
        """Scenario A: one door credited, the blob persisted, nothing else changed."""
        blob = self._save_touching_onair()
        at1 = getattr(PV.read(blob["onair"]), "at", None)
        self.assertIsNotNone(at1)
        time.sleep(0.02)
        CA._capture_door_save(json.load(io.open(self.p, encoding="utf-8")))
        blob2 = json.load(io.open(self.p, encoding="utf-8"))
        self.assertEqual(at1, getattr(PV.read(blob2["onair"]), "at", None),
                         "a save that changed nothing moved the stamp's clock, so `at` tracks "
                         "'last time any row was persisted', not 'last time THIS row was written'")

    def test_a_row_that_changes_later_is_restamped(self):
        """The other half: keeping an old block must not mean freezing it forever."""
        self._save_touching_onair()
        cur = json.load(io.open(self.p, encoding="utf-8"))
        cur["mini"]["blank"] = 99
        CA._capture_door_save(cur)
        blob = json.load(io.open(self.p, encoding="utf-8"))
        self.assertEqual("control_app", getattr(PV.read(blob["mini"]), "by", None),
                         "a row that DID change kept its old (absent) block, so the stamp can "
                         "never catch up with the data")


RED_PROOF = [
    {
        "why": 'restoring the blanket comprehension relabels every sibling row on every save - the BACK-FILL and CHURN the second eye found in v2976, shipped three times',
        "file": 'control_app.py',
        "find": '        d = _PV.stamp_changed_rows(d, _capture_door_load(), by="control_app",\n                                   extra={"store": "capture_doors"})\n',
        "replace": '        d = dict((_k, (_PV.stamp_row(_v, by="control_app", extra={"store": "capture_doors"})\n                       if isinstance(_v, dict) else _v))\n                 for _k, _v in (d or {}).items())\n',
        "matches": 1,
    },
    {
        "why": 'stamping the BLOB instead of the ROW is the exact hazard reel_retention names: a reel-keyed store gains a top-level _prov, and every reader that enumerates it counts one reel that does not exist',
        "file": 'retro_triage.py',
        "find": '        row = _PV.stamp_row(row, by="retro_triage")',
        "replace": '        blob = _PV.stamp(blob, by="retro_triage")',
        "matches": 1,
    },
    {
        "why": 'removing the stamp call puts the store back to SILENT: a new triage verdict that cannot be invalidated when the classifier improves, over the store that decides EMPTY on the river',
        "file": 'retro_triage.py',
        "find": '        row = _PV.stamp_row(row, by="retro_triage")\n',
        "replace": '',
        "matches": 1,
    },
    {
        "why": 'stamping the BLOB adds a phantom door that blueprint.capture_doors() publishes as a row',
        "file": 'control_app.py',
        "find": '        d = _PV.stamp_changed_rows(d, _capture_door_load(), by="control_app",\n                                   extra={"store": "capture_doors"})\n',
        "replace": '        d = _PV.stamp(d, by="control_app", extra={"store": "capture_doors"})\n',
        "matches": 1,
    },
    {
        "why": 'stamping the BLOB inflates len(d), which corroborate.hunt-remembers compares against zero - an EMPTY memory would report 1',
        "file": 'control_app.py',
        "find": '        rec = _PV.stamp_changed_rows(rec, _prior, by="control_app",\n                                     extra={"store": "chron_hunt_memory"})\n',
        "replace": '        rec = _PV.stamp(rec, by="control_app", extra={"store": "chron_hunt_memory"})\n',
        "matches": 1,
    },
    {
        "why": 'stamping the BLOB adds a phantom item to `tracked = len(_load())`, a number he reads',
        "file": 'main_character.py',
        "find": '        d = _PV.stamp_changed_rows(d, _load(), by="main_character",\n                                   extra={"store": "main_character"})\n',
        "replace": '        d = _PV.stamp(d, by="main_character", extra={"store": "main_character"})\n',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
