# -*- coding: utf-8 -*-
"""v2732 — A REBUILD THAT INVENTS A NUMBER IS WORSE THAN NO REBUILD.

`chronicle_rebuild` derives a chronicle's rows from the OTHER ledger-backed stores, so a lost or
drifted ledger can be reconstructed from independent evidence rather than replayed from a copy.
Konyo asked for it in those terms — *"a rebuild/restore option for each chronicle that is ledger
related"* — and then, when a snapshot was offered instead, *"snap shot is not enough"*.

=== THE THREE THINGS THIS PINS, AND WHY EACH ONE ALMOST WENT WRONG ===

1. IT MUST NOT REPRODUCE THE TALLY. He caught the first cut from the numbers alone: *"make sure to
   read the right one being tallied... 292/403 uniques"*. That version rebuilt over `d2r_owned`
   (169) — VAULT ownership, a different question — and an attempt to reproduce the real uniques
   count landed on 298 against his 292. Six wrong, because `funiScan` folds names with `_regKey`
   and honours the v2680 one-tally-per-sunder ruling, and this module's `_norm` is a different
   fold. A second implementation of the number he reads most, already wrong before shipping.
   So the module rebuilds LEDGER ROWS; the board recomputes the tally. [[copy-drift]]

2. IT MUST NAME WHAT IT CANNOT REACH. "2 items could not be recovered" is not actionable; the two
   NAMES are — they are the list he would have to re-enter by hand, and they are the entire
   argument for a save point existing beside a rebuild. Measured on his tree: "Death Mask" and
   "Black Cleft".

3. IT MUST NOT RESOLVE A CONFLICT SILENTLY. Measured: "Crescent Moon" is Aug 24 2026 in foundLog
   and Jun 22 2026 in rwMade — ticked versus forged, two months apart, both true about different
   events. A rebuild that quietly picks one has invented a history he never had.
   ⚠ AND THE FIRST CONFLICT DETECTOR CRIED WOLF: comparing raw strings reported 21 disagreements,
   of which 20 were one instant in two formats ("Aug 16, 2026 · 01:25" vs "08/16/2026, 01:25").
   A conflict list that is mostly formatting is a list nobody reads — the crying-wolf shape filed
   as its own row an hour before this module reproduced it.

⚠ IT WRITES NOTHING, and that is asserted from its own source here rather than promised in a
docstring. The console never writes the ledger; every existing path asks the BOARD to press its own
door. A rebuild that could write would be a second writer into his chronicle.
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import chronicle_rebuild as CR  # noqa: E402

SRC = io.open(os.path.join(HERE, "chronicle_rebuild.py"), encoding="utf-8").read()


class ChronicleRebuildIsHonest(unittest.TestCase):

    # ── it cannot write ───────────────────────────────────────────────────────────────────────
    def test_it_writes_nothing_AT_ALL(self):
        """⚠⚠ THE FIRST CUT OF THIS LAW WAS DEFEATED BY AN ALIAS, AND THE SABOTAGE FOUND IT.

        It searched the unparsed source for the STRING "json.dump". The sabotage added
        `import json as _j; _j.dump` — which contains no such string — and the law stayed GREEN
        while the module had just been handed a writer.

        An allowlist of IMPORTS cannot be dodged that way. A pure derivation needs almost nothing,
        so anything new is a new capability and has to be argued for rather than slipped in.
        [[source-reading-guard]] [[feedback-suspect-the-instrument]]
        """
        import ast
        tree = ast.parse(SRC)
        ALLOWED = {"unicodedata", "re"}
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    imported.add(a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module.split(".")[0])
        stray = sorted(imported - ALLOWED)
        self.assertEqual(
            [], stray,
            "chronicle_rebuild imports %s. It must be a pure DERIVATION over dicts it is handed — "
            "the console never writes the ledger, and a rebuild that can reach a file, a socket or "
            "a subprocess is a second writer into his chronicle. Anything beyond %s is a new "
            "capability and needs arguing for, not importing." % (stray, sorted(ALLOWED))
        )
        # and no attribute call that writes, whatever it is spelled as
        WRITERS = {"dump", "dumps", "write", "writelines", "setItem", "remove", "replace",
                   "unlink", "rename", "mkdir", "makedirs", "system", "run", "Popen"}
        called = {n.func.attr for n in ast.walk(tree)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        bad = sorted(called & WRITERS)
        # `str.replace` is legitimate string work and is not a write
        bad = [b for b in bad if b != "replace"]
        self.assertEqual([], bad,
                         "chronicle_rebuild calls %s — a write verb, however it is aliased" % bad)
        # ⚠⚠ AND BARE-NAME CALLS TOO — the second miss the sabotage found. `open('/tmp/x','w')` is
        # an ast.Name call, not an ast.Attribute one, so the check above walked straight past a
        # module that had just been handed a file handle. A guard that inspects one call SHAPE is
        # a guard against one spelling. [[feedback-suspect-the-instrument]]
        BARE = {"open", "eval", "exec", "compile", "__import__", "input", "breakpoint"}
        bare_called = {n.func.id for n in ast.walk(tree)
                       if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        stray_bare = sorted(bare_called & BARE)
        self.assertEqual(
            [], stray_bare,
            "chronicle_rebuild calls %s. A pure derivation over dicts it is handed needs no file "
            "handle and no dynamic execution; either is a route to writing his chronicle."
            % stray_bare
        )

    # ── UNKNOWN is never collapsed into empty ─────────────────────────────────────────────────
    def test_no_readable_source_is_UNKNOWN_not_an_empty_rebuild(self):
        r = CR.rebuild(["Anything"], {"foundLog": None, "gameFound": None,
                                      "rwMade": None, "evidence": None})
        self.assertFalse(r["ok"], "with every source unreadable it returned a rebuild anyway")
        self.assertIn("UNKNOWN", r["why"],
                      "it did not say the result is unknown rather than empty")

    def test_an_absent_source_is_not_the_same_as_an_empty_one(self):
        """`None` means nobody could read it; `{}` means it was read and held nothing."""
        absent = CR.rebuild(["X"], {"foundLog": None, "gameFound": None,
                                    "rwMade": None, "evidence": None})
        empty = CR.rebuild(["X"], {"foundLog": {}, "gameFound": {},
                                   "rwMade": {}, "evidence": {}})
        self.assertFalse(absent["ok"], "all-absent must refuse")
        self.assertTrue(empty["ok"],
                        "all-EMPTY is a real reading — the stores were read and held nothing, and "
                        "the honest answer is a rebuild with everything unreachable, not a refusal")
        self.assertEqual(["X"], empty["unreachable"])

    # ── ⚠ IT NAMES WHAT IT CANNOT REACH ───────────────────────────────────────────────────────
    def test_unreachable_names_are_NAMED_never_only_counted(self):
        r = CR.rebuild(["Findable", "Lost One", "Lost Two"],
                       {"foundLog": {"Findable": "May 1, 2026 · 00:00"},
                        "gameFound": {}, "rwMade": {}, "evidence": {}})
        self.assertEqual(["Lost One", "Lost Two"], r["unreachable"],
                         "the unreachable list must carry the NAMES. A count is not actionable; "
                         "these are the rows he would have to re-enter by hand.")

    # ── the joins that were hiding real records ───────────────────────────────────────────────
    def test_a_curly_apostrophe_does_not_hide_a_record(self):
        """MEASURED: owned writes U+0027, three ledgers write U+2019. An exact join lost it."""
        r = CR.rebuild(["Saracen's Chance"],
                       {"foundLog": {u"Saracen’s Chance": "Aug 16, 2026 · 02:26"},
                        "gameFound": {}, "rwMade": {}, "evidence": {}})
        self.assertEqual([], r["unreachable"],
                         "a curly-vs-straight apostrophe hid a record that exists. Both this "
                         "repo's t166 count and my own 'unreachable' count were inflated by "
                         "exactly this.")

    def test_a_disambiguating_qualifier_does_not_hide_a_record(self):
        r = CR.rebuild(["Crescent Moon (amulet)"],
                       {"foundLog": {}, "gameFound": {},
                        "rwMade": {"Crescent Moon": "Jun 22, 2026 · 01:35"}, "evidence": {}})
        self.assertEqual([], r["unreachable"],
                         "the '(amulet)' qualifier lives in d2r_owned to disambiguate for HIM; no "
                         "ledger stores it, so matching on it loses the row it describes")

    # ── ⚠ CONFLICTS ARE REPORTED, AND ONLY REAL ONES ──────────────────────────────────────────
    def test_a_real_date_conflict_is_REPORTED_not_resolved_away(self):
        r = CR.rebuild(["Crescent Moon (amulet)"],
                       {"foundLog": {"Crescent Moon": "Aug 24, 2026 · 10:11"},
                        "gameFound": {}, "rwMade": {"Crescent Moon": "Jun 22, 2026 · 01:35"},
                        "evidence": {}})
        self.assertEqual(1, len(r["conflicts"]),
                         "two months apart — ticked vs forged — and it was not reported. Picking "
                         "one silently invents a history he never had.")
        self.assertEqual("rwMade", r["conflicts"][0]["took"],
                         "a runeword's date is its FORGE record; foundLog's is when it was ticked")

    def test_the_SAME_instant_in_two_formats_is_NOT_a_conflict(self):
        """⚠⚠ THE CRYING-WOLF LAW. The first detector reported 21 conflicts on his tree and 20
        were formatting. A list that is mostly noise is a list nobody reads."""
        r = CR.rebuild(["Blackhand Key"],
                       {"foundLog": {"Blackhand Key": "Aug 16, 2026 · 01:25"},
                        "gameFound": {"Blackhand Key": {"at": "08/16/2026, 01:25"}},
                        "rwMade": {}, "evidence": {}})
        self.assertEqual([], r["conflicts"],
                         "'Aug 16, 2026 · 01:25' and '08/16/2026, 01:25' are the same minute "
                         "written by two stores. Reporting that as a disagreement buries the one "
                         "real conflict among twenty false ones.")

    def test_an_unparseable_date_is_not_treated_as_agreement(self):
        r = CR.rebuild(["Odd"],
                       {"foundLog": {"Odd": "sometime last spring"},
                        "gameFound": {"Odd": {"at": "who knows"}},
                        "rwMade": {}, "evidence": {}})
        self.assertEqual(1, len(r["conflicts"]),
                         "two dates neither of which could be parsed were treated as agreeing. "
                         "Unparseable is UNKNOWN, and two unknowns are not equal.")

    # ── it does not decide what a chronicle IS ────────────────────────────────────────────────
    def test_it_does_not_reimplement_the_tally(self):
        """⚠ He caught the first cut aiming at d2r_owned (169) while his screen read 292/403, and
        an attempt to reproduce 292 landed on 298. This module must not contain that arithmetic."""
        for bad in ("unique_roster", "chronTotal", "403", "funiScan", "_regKey"):
            self.assertNotIn(
                bad, SRC.split('"""', 2)[-1],
                "chronicle_rebuild's CODE references %r. The tally is DERIVED by the board and "
                "reproducing it here ships a second implementation of the number he reads most — "
                "already measured six wrong. Rebuild the ledger rows; let the board count."
                % bad
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
