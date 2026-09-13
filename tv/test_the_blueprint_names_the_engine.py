# -*- coding: utf-8 -*-
"""BLUEPRINT.md MUST NAME EVERY MODULE, AND A CONCEPT MUST FIND ITS OWNER IN ONE GREP.

Konyo, 2026-09-13, after I asked him something the tree already answered: *"so why are you not
checkig blueprints before hand :)?"* and then *"make sure the blueprint is updated accordignly so
you dont need to ask these questions in the future and the blueprints speaks for itself."*

This is `test_the_blueprint_cannot_go_stale`'s sibling one rung down. That one keeps the GATES
section honest; this one keeps the CODE section honest — and the code section did not exist until
v3091, while the tree held **178 modules and 1,045 public functions** and this document said what
none of them were.

⚠⚠ MEASURED THE DAY IT WAS BUILT, and this is the whole justification: `footprint` — a function
shipped hours earlier in slot_identity.py that REFUSES an item overhanging the grid rather than
clipping it — scored **ZERO hits** anywhere in BLUEPRINT.md. So did `occupancy`, `names_loc`,
`terror zone`, `lattice` and `slot identity`. Every one was a shipped, tested behaviour that the
map could not find. A count is not knowledge, and 178 filenames with no purposes is the same
failure `gate_index` was written for one rung up. [[verify-before-building-console]]

⚠ THE SPLIT THIS PINS. Derived every render: which modules exist on disk, and which are imported by
another module — those cannot go stale because nothing stores them. Curated in
`tv/engine_index.json`: purpose, territory, gotcha, entry points, because a sentence about what a
module MEANS cannot be re-derived from an AST. The DRIFT between the two is what this law guards:
a module on disk with no entry (UNINDEXED) or an entry whose file is gone (STALE) must be reported,
never quietly dropped. A map that silently omits a module is worse than no map.

⚠ AND `noPyImporter` SAYS ONLY WHAT IT MEASURES. Two scans of mine disagreed 12-vs-15 on a
"deadEnd" flag, and the cause was one of them counting a module's name inside a `why=` PROSE STRING
in run_gates.py as a real reference. A CLI tool, a hook and a routine are all reached without an
import, so "no module imports it" is a question, never a verdict. [[label-outlived-referent]]
"""
import io
import os
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# the concepts a reader would actually reach for, each a shipped behaviour of this tree
CONCEPTS = ["footprint", "lattice", "occupancy", "slot identity", "names_loc", "sockets",
            "terror zone", "deleter", "second eye", "river", "retention", "tombstone",
            "tooltip", "witness", "wilson", "printer", "vault", "chronicle"]


def _blueprint():
    with io.open(os.path.join(REPO, "BLUEPRINT.md"), encoding="utf-8") as fh:
        return fh.read()


class TestTheBlueprintNamesTheEngine(unittest.TestCase):

    def test_every_module_on_disk_is_named(self):
        import blueprint as B
        rows, drift = B.engine_index()
        self.assertIsNotNone(rows, "tv/engine_index.json could not be read at all")
        print("engine index: %d module(s) · %d unindexed · %d stale"
              % (len(rows), len(drift["unindexed"]), len(drift["stale"])))
        # ⚠⚠ ASSERTING "unindexed IS EMPTY" WENT BLIND, and the drill caught it: a sabotage that
        # hardcodes `"unindexed": []` silences the whole drift report and the assertion passes
        # MORE easily. A law must check the answer is COMPUTED, not that it is convenient. So the
        # difference is re-derived here, independently, and the two must agree.
        # [[sabotage-is-usually-the-wrong-one]]
        self.assertEqual(drift["unindexed"], [],
                         "module(s) on disk with no entry, so the map does NOT describe them: %s"
                         % drift["unindexed"])
        # ⚠⚠ AND PROVE THE REPORT IS COMPUTED, NOT MERELY EMPTY. Two earlier drafts went BLIND in
        # the red-proof drill for the same reason: a sabotage that hardcodes `"unindexed": []`
        # SILENCES the whole drift report, and an assertion that the list is empty then passes MORE
        # easily than before. Re-deriving the set difference in the test did not help either —
        # with a fully indexed tree both sides are empty, so the comparison cannot tell a working
        # report from a disabled one.
        #
        # The only thing that can: put a module on disk that the index does not know about, and
        # require it to be NAMED. Cleaned up in `finally`, so a failure here cannot leave a stray
        # module in his tree. [[sabotage-is-usually-the-wrong-one]] [[feedback-blind-fixture-green-gate]]
        canary = os.path.join(HERE, "zz_drift_canary_delete_me.py")
        try:
            with io.open(canary, "w", encoding="utf-8") as fh:
                fh.write("# temporary: proves engine_index() actually reports drift\n")
            _rows2, drift2 = B.engine_index()
            self.assertIn("zz_drift_canary_delete_me.py", drift2["unindexed"],
                          "a module was added to the tree and the drift report did not name it — "
                          "the report is not derived from the tree, so an UNINDEXED module would "
                          "be dropped from the map in silence, which is the whole failure this "
                          "law exists to prevent")
            print("drift proven live: an unknown module on disk is reported UNINDEXED")
        finally:
            try:
                os.remove(canary)
            except OSError:
                pass
        self.assertFalse(os.path.exists(canary), "the canary module was left in his tree")
        self.assertEqual(drift["stale"], [],
                         "entr(ies) whose file is gone — the map describes code that is not here: %s"
                         % drift["stale"])
        on_disk = [f for f in os.listdir(HERE)
                   if f.endswith(".py") and not f.startswith("test_")]
        self.assertEqual(len(rows), len(on_disk),
                         "%d rows for %d modules on disk" % (len(rows), len(on_disk)))

    def test_a_concept_finds_its_owner_in_one_grep(self):
        """The whole job. Each of these was a shipped behaviour the map could not find.

        ⚠ Grades what render() PRODUCES, not the committed BLUEPRINT.md. Reading the file went
        BLIND: a sabotage that stops emitting the section leaves the checked-in document intact,
        so the law passed while the generator had been gutted. The file is checked too, because a
        reader greps the file — but the generator is the thing under test.
        """
        import blueprint as B
        doc = (B.render() + "\n" + _blueprint()).lower()
        missing = [c for c in CONCEPTS if c not in doc]
        for c in CONCEPTS[:6]:
            print("   %-16s %d hit(s)" % (c, doc.count(c)))
        self.assertEqual(missing, [],
                         "BLUEPRINT.md cannot answer %s — a reader greps the concept, finds "
                         "nothing, and concludes it does not exist. That is the mistake this "
                         "section was built to stop." % missing)

    def test_the_engine_section_is_actually_rendered(self):
        import blueprint as B
        doc = B.render()          # the GENERATOR, not the possibly-stale committed file
        self.assertIn("## THE ENGINE", doc,
                      "render() no longer emits the engine section — BLUEPRINT.md would go back "
                      "to naming zero of the 178 modules on the next regeneration")
        self.assertIn("## THE ENGINE", _blueprint(),
                      "the committed BLUEPRINT.md has no engine section — regenerate it")
        rows, _ = B.engine_index()
        absent = [r["module"] for r in rows if ("**%s**" % r["module"]) not in doc]
        self.assertEqual(absent, [],
                         "%d module(s) are in the index but not rendered into the document: %s"
                         % (len(absent), absent[:6]))
        print("all %d modules rendered as entries" % len(rows))

    def test_a_purpose_may_not_be_a_shrug(self):
        import blueprint as B
        rows, _ = B.engine_index()
        vague = [r["module"] for r in rows
                 if len((r["purpose"] or "").split()) < 5
                 or (r["purpose"] or "").strip().lower() in ("helpers", "utilities", "misc")]
        self.assertEqual(vague, [],
                         "purpose(s) that say nothing: %s. A filename restated is not a purpose, "
                         "and 'helpers' is how a module becomes invisible to the next reader."
                         % vague)
        noaim = [r["module"] for r in rows if not r["purpose"]]
        self.assertEqual(noaim, [], "module(s) with an empty purpose: %s" % noaim)
        print("%d purposes, none empty, none under 5 words" % len(rows))

    def test_the_document_is_deterministic(self):
        """Two renders must differ only in their generated-at line, or the pre-push staleness
        check refuses a tree nobody changed."""
        import blueprint as B
        a, b = B.render(), B.render()
        strip = lambda t: "\n".join(l for l in t.splitlines()
                                    if not l.startswith("GENERATED") and "generated " not in l)
        self.assertEqual(strip(a), strip(b),
                         "render() is not deterministic — a clock or an unsorted dict is leaking "
                         "into the document, and every run would look like a stale blueprint")
        print("render() deterministic over %d bytes" % len(a))


RED_PROOF = [
    {
        "why": "the drift report is silenced, so a module on disk with no entry is dropped from "
               "the map without a word — the exact silent omission this law exists to prevent",
        "file": "blueprint.py",
        "find": '    drift = {"unindexed": sorted(set(on_disk) - set(curated)),',
        "replace": '    drift = {"unindexed": [],',
        "matches": 1,
    },
    {
        "why": "the engine section stops being rendered, so BLUEPRINT.md goes back to naming zero "
               "of the 178 modules and a reader greps a concept and concludes it does not exist",
        "file": "blueprint.py",
        "find": '    A("## THE ENGINE — every module, what it does, and what a reader gets wrong")',
        "replace": '    A("## (the engine section was removed)")',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
