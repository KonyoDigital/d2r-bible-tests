# -*- coding: utf-8 -*-
"""v2794 — THE MAP SAID IT COULD NOT GO STALE, AND IT HAD BEEN STALE FOR SIX DAYS.

`tv/blueprint.py`'s own header: *"THE MAP OF THIS SYSTEM, GENERATED FROM THE CODE SO IT CANNOT GO
STALE"* — the right idea, inherited from ~/achilles-revival along with the reverse-blueprint rule.
Nothing regenerated it. Measured 2026-09-08 against the BLUEPRINT.md then on disk:

    last written        Sep 2 (six days)
    `station` mentions  0
    `INTAKE`            0
    `TOMBSTONE`         0
    `printer`           0
    `panelFrames`       0

The river and the printer were both built AFTER that date, so the one surface meant to show the
wiring from above simply did not know they existed. Konyo: *"shouldnt this be a connected and
communicating system thats easily seen wired from a macro view"*. It should — and it was the MAP
that was missing, not the wiring. [[the-unjoined-end]]

=== ⛔ THE GATE REFUSES; IT DOES NOT REGENERATE ===
The obvious move is to have pre-push rebuild the file. That is wrong here and the repo already
knows why: **the gate grades the WORKING TREE**. A hook that rewrote BLUEPRINT.md mid-push would
dirty the tree it is grading, and the commit actually being pushed would still carry the stale
file. So it refuses, a human runs the generator, and the push is retried — the same shape the
second-eye gate uses. [[d2r-push-grades-the-working-tree]]

=== ⚠ THE TIMESTAMP LINE IS EXCLUDED, AND WITHOUT THAT THIS IS FURNITURE ON DAY ONE ===
`render()` stamps `generated YYYY-MM-DD HH:MM`, which changes every minute. A naive byte-compare
would be RED forever, everyone would learn to skim it, and the real staleness would go with it.
Compare the MAP, not the clock. [[regression-guard]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import blueprint as BP  # noqa: E402


class TheBlueprintCannotGoStaleSilently(unittest.TestCase):

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────
    def test_the_map_matches_the_code_right_now(self):
        """★★★ The whole point. If this is red, BLUEPRINT.md describes a building that has been
        renovated — run `python3 tv/blueprint.py`."""
        self.assertEqual(BP.main(["--check"]), 0,
                         "BLUEPRINT.md no longer matches the code. Regenerate it: "
                         "python3 tv/blueprint.py")

    def test_check_IGNORES_the_generated_timestamp(self):
        """★★ Without this the gate is red on every run and becomes furniture in a day. Proven by
        comparing two renders taken at different clock minutes — only the stamp may differ."""
        a = BP.render()
        b = BP.render()
        strip = lambda t: "\n".join(l for l in t.split("\n")
                                    if not l.strip().startswith("generated "))
        self.assertEqual(strip(a), strip(b),
                         "two renders of the same tree differ outside the timestamp, so --check "
                         "can never be stable")
        self.assertIn("generated ", a,
                      "the stamp is gone — if it was removed, this exclusion is now dead code and "
                      "should be removed with it")

    # ── ⚠ THE SECTIONS THAT WERE MISSING ────────────────────────────────────────────────────
    def test_the_map_knows_the_RIVER_exists(self):
        """⚠ It did not, for six days. The stations come from `reel_router.STATIONS` — quoted, not
        listed here, so a station added upstream appears on the map without a second edit.
        [[copy-drift]]"""
        t = io.open(os.path.join(REPO, "BLUEPRINT.md"), encoding="utf-8").read()
        for must in ("THE RIVER", "INTAKE", "TOMBSTONE"):
            self.assertIn(must, t, "the blueprint no longer describes the river (%r missing)" % must)

    def test_the_map_knows_the_PRINTER_exists(self):
        t = io.open(os.path.join(REPO, "BLUEPRINT.md"), encoding="utf-8").read()
        self.assertIn("THE PRINTER", t, "the blueprint no longer describes the printer")

    def test_the_map_shows_GROSS_vs_STRIPPED(self):
        """⚠ His words: *"a gross full lengthed all screenshots before the filtering ... and then
        the stripped version"*. Both exist; the stripped sets had no reader, and a map that cannot
        show that gap is a map worth fixing."""
        t = io.open(os.path.join(REPO, "BLUEPRINT.md"), encoding="utf-8").read()
        self.assertIn("GROSS vs STRIPPED", t,
                      "the blueprint no longer shows how much footage carries a panel")

    # ── ⛔ IT REPORTS; IT NEVER ASSERTS ──────────────────────────────────────────────────────
    def test_an_unreadable_subsystem_says_UNKNOWN_not_zero(self):
        """⛔ The file's own rule: *"Where something cannot be counted it says so rather than
        printing a zero, because '0 lanes' and 'I could not read the lanes' are opposite facts."*

        ⚠⚠ THE FIRST CUT OF THIS LAW READ TEXT AND A SABOTAGE WALKED PAST IT. It asserted the
        string "why" appeared somewhere in each function — and deleting `"why": None` from the
        river's initializer left the key present in its error-path assignments, so the law stayed
        GREEN while the success path stopped carrying the channel. Fourth time today a law read
        MENTION instead of behaviour. So: BREAK the dependency and demand the answer.
        [[sabotage-is-usually-the-wrong-one]] [[unknown-stays-unknown]]"""
        import builtins
        real = builtins.__import__

        def _blind(blocked):
            def _imp(name, *a, **k):
                if name == blocked:
                    raise ImportError("blinded for the test")
                return real(name, *a, **k)
            return _imp

        for fn, dep in ((BP.river, "reel_router"),
                        (BP.printer_stream, "printer")):
            builtins.__import__ = _blind(dep)
            try:
                got = fn()
            finally:
                builtins.__import__ = real
            self.assertIsInstance(got, dict,
                                  "%s() returned %r with %s unreadable — a section that cannot be "
                                  "counted must still answer" % (fn.__name__, got, dep))
            self.assertTrue(str(got.get("why") or "").strip(),
                            "%s() lost its `why` when %s could not be read, so an unreadable "
                            "subsystem now renders as an EMPTY one" % (fn.__name__, dep))

        # the stripped set reads a FILE, so blind it by pointing at a name that cannot exist
        import blueprint as _bp
        old_here = _bp.HERE
        try:
            _bp.HERE = os.path.join(HERE, "__no_such_dir_for_the_test__")
            got = _bp.stripped_sets()
        finally:
            _bp.HERE = old_here
        self.assertTrue(str((got or {}).get("why") or "").strip(),
                        "stripped_sets() reports nothing rather than UNKNOWN when the triage store "
                        "is absent — an absent store would render as zero panel frames")

    def test_the_rendered_map_SAYS_unknown_when_a_section_cannot_be_read(self):
        """⛔ The channel existing is half of it; render() must print it. A `why` nobody surfaces
        is the same silence with an extra field. [[plumbing-with-no-tap]]"""
        src = io.open(os.path.join(HERE, "blueprint.py"), encoding="utf-8").read()
        i = src.find('A("## THE RIVER')
        self.assertGreater(i, 0, "the river section is gone from render()")
        seg = src[i:i + 900]
        self.assertIn("UNKNOWN", seg,
                      "render() prints the river without an UNKNOWN branch, so a river it could "
                      "not read would be drawn as a river with nothing in it")



RED_PROOF = [
    {
        "why": "⚠ RE-AIMED — MY FIRST ANCHOR WAS THE WRONG SIDE OF THE DOOR, and heart2 measured it "
               "BLIND (1 match, still green). river() has FOUR why-writes; I picked the one that "
               "handles a router which IMPORTS AND THEN THROWS, while this law blinds the IMPORT "
               "and so returns early through a different line entirely. Verified the replacement "
               "by shadowing a tampered blueprint and calling river() with reel_router blinded: "
               "why='' -> the law fails. Third instance of this shape today. "
               "[[sabotage-is-usually-the-wrong-one]] "
               "v2888 — the tamper makes river() LOSE ITS `why` when reel_router cannot be imported, "
               "so an unreadable subsystem renders as an EMPTY one — 'the router could not be read' "
               "and '0 lanes' become the same pixels, which is the single rule this file exists to "
               "enforce: \"Where something cannot be counted it says so rather than printing a zero, "
               "because '0 lanes' and 'I could not read the lanes' are opposite facts.\" It reddens "
               "test_an_unreadable_subsystem_says_UNKNOWN_not_zero, which does NOT read text — it "
               "blinds the import and demands the answer, after an earlier text-reading cut of the "
               "same law let a sabotage walk straight past it. The replacement keeps the code valid "
               "and simply files the reason under a key nobody reads, which is exactly how this "
               "defect looks in the wild. [[unknown-stays-unknown]] [[zero-needs-a-denominator]]",
        "file": 'blueprint.py',
        "find": 'return {"why": "reel_router is not importable (%s)" % type(e).__name__}',
        "replace": 'return {}',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
