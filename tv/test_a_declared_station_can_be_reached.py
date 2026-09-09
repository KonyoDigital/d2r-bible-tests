#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2817 (#36) — TOMBSTONE WAS A DECLARED STATION NO CODE PATH COULD EVER ASSIGN.

MEASURED 2026-09-09. `reel_router.STATIONS` declares nine stations including TOMBSTONE. Nothing in
`_station_of()`/`route()` ever assigns it, so `counts["TOMBSTONE"]` is structurally 0 and
`route()["unreached"]` named it on EVERY run — the module reporting its own gap to nobody for
months. Meanwhile `tv/reel_tombstones.json` held **428 closed-out reels**, with ZERO overlap
against the 41 still on disk.

Consequence: `river_lanes`' TOMBSTONE lane — labelled "closed out — the extraction contract is
satisfied" — could only ever display ROUTED-but-still-present reels. It could never show a reel
that had actually closed out, which is the one thing it exists to show. A vocabulary with an
unreachable word is a label that outlived its referent.

★ THE PER-REEL WALK IS NOT WIDENED, AND THAT IS THE POINT. Every source feeding the router walks
what is on disk; a reel whose directory is gone has no row to derive. Folding 428 ledger entries
into `rows` would silently move `shelf` from 41 to 469 — a number he reads, changed by a refactor.
The closure ledger is published BESIDE the walk with its own denominator and its own source named.
[[label-outlived-referent]] [[zero-needs-a-denominator]] [[unknown-stays-unknown]]
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

import reel_router as RR  # noqa: E402


class TestADeclaredStationCanBeReached(unittest.TestCase):
    """⚠⚠ THIS GATE BUILDS ITS OWN WORLD, AND THE FIRST CUT DID NOT.

    The first version read his LIVE tree — 41 reels on disk, 428 in the ledger — and Heart 2.0
    reported both red-proofs UNPROVABLE: "it is ALREADY RED untampered in the sandbox". Of course
    it was. The sandbox is a copy of the repo WITHOUT his 5.8 GB of footage, so the walk found no
    reels and the assertions had nothing to stand on. A law that can only pass on one machine's
    data can never be proven anywhere, which makes it exactly the kind of gate this repo counts as
    UNKNOWN rather than green. [[feedback-fixtures-never-touch-live-data]]
    """

    def setUp(self):
        # ⚠ TV_HIST, NOT a hist= ARGUMENT. route() refuses a mismatched pair outright:
        # "refusing to mix shelves: hist=... was passed, but printer.stream() reads ... and takes
        # no shelf argument. Set TV_HIST instead — answering anyway would join this fixture's
        # clocks to the live shelf's evidence." That refusal is correct and this fixture obeys it
        # rather than working around it. [[feedback-fixtures-never-touch-live-data]]
        self.root = tempfile.mkdtemp(prefix="station_gate.")
        for r in ("reel_s_1", "reel_s_2"):
            os.makedirs(os.path.join(self.root, r))
        self._tv = os.environ.get("TV_HIST")
        os.environ["TV_HIST"] = self.root

    def tearDown(self):
        if self._tv is None:
            os.environ.pop("TV_HIST", None)
        else:
            os.environ["TV_HIST"] = self._tv
        shutil.rmtree(self.root, ignore_errors=True)

    def _ledger(self, reels):
        with io.open(os.path.join(self.root, "reel_tombstones.json"), "w",
                     encoding="utf-8") as fh:
            json.dump({"reels": {r: {"at": 1} for r in reels}, "updatedTs": 1}, fh)

    def test_the_closure_ledger_is_published_with_its_denominator(self):
        self._ledger(["gone_1", "gone_2", "gone_3"])
        rep = RR.route()
        self.assertIn("closed", rep,
                      "route() publishes no closure count, so every consumer of the TOMBSTONE "
                      "lane must derive it from a walk that structurally cannot see it")
        c = rep["closed"]
        for k in ("n", "readable", "why"):
            self.assertIn(k, c, "the closure report has no %r — a bare number with no denominator "
                                "and no source is the shape this repo keeps rediscovering" % k)
        self.assertEqual(c["n"], 3, "the closure count does not match the ledger")

    def test_TOMBSTONE_is_not_unreached_while_the_ledger_holds_reels(self):
        """The decisive law: a station backed by records is reached — by a source this walk does
        not own, which is a different fact from 'nothing gets there'."""
        # ⚠ THROUGH THE SHARED FUNCTION route() ITSELF USES. Asserting on route()'s report alone
        # was VACUOUS here: on an UNKNOWN walk `rep.get("unreached") or []` is [], and assertNotIn
        # passes against an empty list without testing anything. A green that cannot fail is the
        # thing this repo calls a blind gate.
        counts = {st: 0 for st in RR.STATIONS}
        self.assertNotIn("TOMBSTONE", RR.unreached_stations(counts, 2),
                         "TOMBSTONE is still named unreached while 2 reel(s) have closed out — "
                         "the module is reporting a gap that has been filled")
        self._ledger(["gone_1", "gone_2"])
        self.assertNotIn("TOMBSTONE", RR.route().get("unreached") or [],
                         "the router does not apply its own rule")

    def test_an_EMPTY_ledger_leaves_TOMBSTONE_honestly_unreached(self):
        """The guard must not silence a real emptiness — that trades one lie for another."""
        counts = {st: 0 for st in RR.STATIONS}
        self.assertIn("TOMBSTONE", RR.unreached_stations(counts, 0),
                      "nothing has closed and TOMBSTONE is not reported unreached — a real "
                      "emptiness hidden by the fix meant to stop a false one")
        self._ledger([])
        rep = RR.route()
        self.assertIn("TOMBSTONE", rep.get("unreached") or [],
                      "nothing has closed out and TOMBSTONE is NOT reported unreached — a real "
                      "emptiness has been hidden by the very fix meant to stop a false one")

    def test_the_shelf_count_does_not_absorb_the_closed_reels(self):
        """He reads `shelf`. A refactor must not move it."""
        self._ledger(["gone_1", "gone_2", "gone_3", "gone_4"])
        rep = RR.route()
        shelf = rep.get("shelf")
        walked = len(rep.get("reels") or [])
        self.assertEqual(shelf, walked,
                         "shelf (%s) no longer equals the reels this walk saw (%d) — the closure "
                         "ledger has leaked into the walk and a number he reads has silently "
                         "changed meaning" % (shelf, walked))
        self.assertNotEqual(shelf, walked + 4,
                            "shelf now counts the closed reels too — the silent inflation this "
                            "design exists to avoid")

    def test_an_unreadable_ledger_is_UNKNOWN_not_zero(self):
        """'Nothing closed' and 'I could not tell' are opposite facts; only one is good news."""
        io.open(os.path.join(self.root, "reel_tombstones.json"), "w",
                encoding="utf-8").write("{not json")
        c = RR._closed_ledger()
        self.assertIs(c["readable"], False, "an unparseable ledger reported as readable")
        self.assertIsNone(c["n"],
                          "an unparseable ledger returned a NUMBER (%r) — a confident 0 here reads "
                          "as 'nothing has closed', the opposite of the truth when the file is "
                          "simply broken" % (c["n"],))


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "removing the exception returns TOMBSTONE to being named unreached beside 428 records",
        "file": "reel_router.py",
        "find": '            if counts.get(st, 0) == 0 and not (st == "TOMBSTONE" and n > 0)]',
        "replace": '            if counts.get(st, 0) == 0]',
        "matches": 1,
    },
    {
        "why": "turning an unreadable ledger into a confident 0 is the zero-with-no-denominator defect",
        "file": "reel_router.py",
        "find": '        return {"n": None, "readable": False,\n                "why": "the closure ledger could not be read (%s)" % type(e).__name__}',
        "replace": '        return {"n": 0, "readable": True,\n                "why": "the closure ledger could not be read (%s)" % type(e).__name__}',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
