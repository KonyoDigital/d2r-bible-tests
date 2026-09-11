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


RED_PROOF = [
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
