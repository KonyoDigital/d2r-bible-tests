#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🌊 THE RIVER HAS ONE VOCABULARY — and a fifth list may not quietly appear.

Konyo, 2026-09-11: *"this is a mess.. make it unified and fix whats needed.."*

Every law here PARSES. A station list is code, and a guard that greps prose grades the comment
that explains the defect rather than the defect. [[source-reading-guard]]
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import river_vocab as RV  # noqa: E402


def _module_lists():
    """Every module-level ordered list named STATIONS/STAGES in tv/. -> {'mod.NAME': [names]}"""
    out = {}
    for fn in sorted(os.listdir(HERE)):
        if not fn.endswith(".py") or fn.startswith("test_"):
            continue
        try:
            tree = ast.parse(io.open(os.path.join(HERE, fn), encoding="utf-8").read())
        except Exception:
            continue
        for node in tree.body:                      # module level ONLY
            if not isinstance(node, ast.Assign):
                continue
            for tg in node.targets:
                if not (isinstance(tg, ast.Name) and tg.id in ("STATIONS", "STAGES")):
                    continue
                try:
                    v = ast.literal_eval(node.value)
                except Exception:
                    continue                        # imported/derived, not a restatement
                if isinstance(v, (list, tuple)) and v and all(isinstance(x, str) for x in v):
                    out["%s.%s" % (fn[:-3], tg.id)] = list(v)
    return out


class TheRiverHasOneVocabulary(unittest.TestCase):

    def test_no_two_modules_answer_the_SAME_question(self):
        """The whole defect in one assertion. Three modules each said, in their own comment, that
        they were the order a reel moves through."""
        clashes = {q: o for q, o in RV.questions().items() if len(o) > 1}
        self.assertEqual({}, clashes,
                         "two modules answer one question about the river: %r" % clashes)

    def test_every_ordered_list_about_reels_is_REGISTERED(self):
        """⚠ A FIFTH LIST IS THE FAILURE MODE. Four already existed before anyone noticed; the
        only thing that keeps this closed is a law that fails when an unregistered one appears."""
        found = set(_module_lists())
        unregistered = sorted(found - set(RV.REGISTRY))
        self.assertEqual([], unregistered,
                         "an ordered station/stage list answers no declared question — add it to "
                         "river_vocab.REGISTRY with the question it answers: %r" % unregistered)

    def test_the_registry_names_no_list_that_VANISHED(self):
        """The other direction: a registry entry whose module dropped its list is a label with no
        referent, and it would make the law above pass by describing nothing."""
        found = set(_module_lists())
        gone = sorted(k for k in RV.REGISTRY if k not in found)
        self.assertEqual([], gone,
                         "river_vocab.REGISTRY names a list that no longer exists: %r" % gone)

    def test_the_canonical_river_is_IMPORTED_not_restated(self):
        """⚠ A SECOND COPY OF THE RIVER IS THE DEFECT THIS FILE EXISTS TO END. Parsed: river_vocab
        must not contain a literal tuple of station names of its own. [[copy-drift]]"""
        mine = _module_lists()
        self.assertNotIn("river_vocab.STATIONS", mine,
                         "river_vocab restates the station list as a literal instead of importing "
                         "it from reel_router — that is a second river to drift from the first")
        import reel_router as RR
        self.assertEqual(tuple(RR.STATIONS), RV.STATIONS,
                         "river_vocab.STATIONS and reel_router.STATIONS disagree")

    def test_every_station_in_the_JOURNAL_is_declared(self):
        """⚠ THIS WAS RED WHEN WRITTEN, IN EFFECT: the journal carried `UNKNOWN` rows while no
        module declared the word. It is declared now as a SENTINEL, not as a tenth station, so a
        position nobody established stays sayable. [[unknown-stays-unknown]]"""
        bad, why = RV.undeclared()
        seen, _ = RV.stations_in_journal()
        self.assertTrue(seen or why, "the journal answered nothing AND gave no reason")
        self.assertEqual([], bad,
                         "the journal stamps a station no module declares (%d name(s) seen): %r"
                         % (len(seen), bad))

    def test_the_SENTINEL_is_not_one_of_the_stations(self):
        """If UNKNOWN ever became a real station, 'nobody looked' would render as a place."""
        self.assertNotIn(RV.UNPLACED, RV.STATIONS,
                         "the not-measured sentinel is also a station — a reel could then be "
                         "REPORTED as standing in a place that means nobody looked")
        self.assertEqual(len(RV.STATIONS) + 1, len(set(RV.STAMPABLE)))

    def test_the_two_ENDS_are_the_ones_he_named(self):
        """His river is INTAKE -> TOMBSTONE. If either end moves, the shelf draws a different
        river than the one he asked for."""
        self.assertEqual("INTAKE", RV.SOURCE)
        self.assertEqual("TOMBSTONE", RV.MOUTH)
        self.assertEqual(RV.STATIONS[0], RV.SOURCE)
        self.assertEqual(RV.STATIONS[-1], RV.MOUTH)

    def test_the_printer_pipeline_is_INSIDE_a_station_not_beside_it(self):
        """printer.STATIONS declares its own `tombstone`, which is what made two modules look like
        rivals. It is registered as a sub-pipeline, and the station it runs inside must be real."""
        q = RV.REGISTRY.get("printer.STATIONS") or ""
        self.assertTrue(q.startswith("sub-pipeline:"), "printer.STATIONS is not declared a sub-pipeline")
        self.assertIn(q.split(":", 1)[1], RV.STATIONS,
                      "printer runs inside a station the river does not have")

    def test_it_still_parses(self):
        ast.parse(io.open(os.path.join(HERE, "river_vocab.py"), encoding="utf-8").read())


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════
RED_PROOF = [
    {
        "why": "law: no two modules answer the same question. Pointing river.STAGES at `position` "
               "recreates the exact collision measured on 2026-09-11 — two rivals for one river.",
        "file": "river_vocab.py",
        "find": '"river.STAGES":         "work-ladder",',
        "replace": '"river.STAGES":         "position",',
        "matches": 1,
    },
    {
        "why": "law: the canonical river is IMPORTED, never restated. Replacing the import with a "
               "literal is the second copy this file exists to prevent.",
        "file": "river_vocab.py",
        "find": "STATIONS = tuple(_rr.STATIONS)",
        "replace": 'STATIONS = ("INTAKE", "TRIAGE", "EMPTY", "STATION", "PRINTER", "JOIN",\n              "CAPTURE", "ROUTED", "TOMBSTONE")',
        "matches": 1,
    },
    {
        "why": "law: every station the journal stamps is declared. Dropping the sentinel from "
               "STAMPABLE makes the journal's 20 UNKNOWN-class rows undeclared again.",
        "file": "river_vocab.py",
        "find": "STAMPABLE = STATIONS + (UNPLACED,)",
        "replace": "STAMPABLE = STATIONS",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
