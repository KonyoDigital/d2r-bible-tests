#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GATE-EYE — THE RENDER GATE REPORTED CLEAN ON A PAGE WITH VISIBLE CLIPPING.

⚠⚠ HOW IT WAS FOUND, and it was the second-eye gate that produced it. The pre-push hook REFUSED a
push because the previous ship had never been looked at by a different model family. So the console
was rendered at five widths, LOOKED AT, and three shots handed to another family COLD — no
statement of what the app is, what it should show, or what I thought was wrong with it.

It came back naming, at 375px: `ON AIR` and `MINI` stacked with text cut off, the reads bar
rendering **"appea / here"**, `"Failed to fetch"` sliced mid-word, and a clipped header. **Every
one confirmed by looking at the PNG.** And `render_check` reported, at that exact width:

    375x800   painted 1/1 · clipped 0 · off 0 · covered 0

⚠⚠ THE STRUCTURAL REASON, and it is checkable without trusting either of us. **All ELEVEN targets
were named subtrees** — `console` is `sel: "#btn-mini, #btn-miniauto"`, so `painted 1/1` measured
ONE BUTTON. "clipped 0" was never a claim about the page, and every defect above sat outside every
selector and was therefore invisible by construction. [[regression-guard]]'s SAMPLE ≠ VERDICT,
landing on the visual gate itself. [[visual-regression-detector]]

WHAT WAS ADDED: a `page` target measuring the whole document, REUSING `_PROBE` rather than asking
its own question. A hand-rolled page sweep written for this finding counted 14 cut elements at
every width and was **not published**, because it honoured none of the recovery paths the real
probe already knows — the scroller exclusion, `title` recovery, `inert()`, and the fixed-position
escape with its re-anchoring rules. A second implementation of a measurement is a second thing to
be wrong. [[copy-drift]]

⚠⚠⚠ AND BUILDING IT EXPOSED TWO FAULTS IN THE SHARED SETTLE, BOTH OF WHICH WOULD HAVE MADE THE NEW
TARGET LIE:

  1. **I SET `settles: False` BY COPYING `console`.** That target skips the settle because its two
     named buttons re-time their own labels. `_settled`'s own docstring says why that is fatal for
     a document-wide probe: *"a partial page reports zero clipping, zero overflow and zero covers,
     which is the exact false green this file exists to refuse."* Copying a flag without asking
     whether its reason applies is how a new instrument inherits an old one's exemption.
  2. **THEN IT COULD NEVER SETTLE AT ALL.** The predicate requires `innerHTML.length` to repeat —
     impossible on a page carrying a live clock — and a rendered `.tab[data-tab]` row, which is a
     liveness proxy for `bible.html` and is **ZERO on `control_ui.html` for ever**. Measured: the
     document's shape reached `11814 elements / 2399 images / 46 complete` at t=4s and repeated
     unchanged for the remaining 20s, while the settle went on answering "never settled" about a
     count that page does not have. A permanently-UNKNOWN target is furniture in exactly the way a
     permanently-red one is. `shape=True` asks what layout actually depends on.

⚠⚠ THE OPEN UNKNOWN IS NOW CLOSED, AND IT WAS A THIRD COPIED FLAG. Through the harness the page
reported `imgs 12/12 broken` while the same probe against the page served another way reported
`imgs 2399` of which 4 were broken — two orders of magnitude apart, so it was published as UNKNOWN
rather than as a defect. **The cause was the ORIGIN.** I copied `console`'s `file://` page as well
as its settle flag; over `file://` every root-absolute `/art/...` src resolves to `file:///art/...`,
cannot load, and several tags run an `onerror` that REMOVES the element. `broken` is a REFUSAL
field, so the origin alone would have turned this target permanently red on twelve images that are
fine. Six other console targets already set `serve: True` for exactly this reason. **Three flags
copied from `console`, three of them wrong for a document-wide probe.**

⚠⚠⚠ AND SERVED, THE REAL NUMBERS ARE MUCH LARGER — 54 clipped at 375px, 5 at 901, 1 at the wide
widths. `render_check` is wired into `hooks/pre-push`, where a red target sets `_px_fail=1` and
`exit 1`, so a new instrument finding an old backlog would have BLOCKED EVERY VISUAL PUSH. The
counts are DECLARED per width, printed in full every run, and refuse only on a RISE — see
`ADeclaredFloorReportsAndDoesNotBLOCK`. Fixing the 54 is its own task with its own pixels and its
own second eye, not something to smuggle into whatever else is shipping.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import render_check as RC  # noqa: E402


class SomethingMeasuresTheWholePage(unittest.TestCase):
    """★ The capability. Before this, nothing did."""

    def test_a_page_target_exists(self):
        self.assertIn("page", RC.TARGETS,
                      "no target measures the document — every defect between the named subtrees "
                      "is invisible to this gate by construction")

    def test_its_selector_is_not_a_handful_of_named_nodes(self):
        """⚠ Graded on the SHAPE OF THE SELECTOR, because that is the defect: an id or a class
        selector can only ever reach what someone remembered to name."""
        sel = RC.TARGETS["page"]["sel"]
        self.assertNotIn("#", sel, "the page target names an id — that is a subtree again")
        self.assertTrue(sel.startswith("body >"),
                        "the page target no longer starts from the document body: %r" % sel)

    def test_it_walks_from_the_TOP_LEVEL_and_not_from_every_element(self):
        """⚠ `body *` would be O(n^2): the probe expands each match to `[e] + e.querySelectorAll('*')`,
        so matching every element re-walks every subtree once per ancestor. On an 11,806-node
        document that is not a slow test, it is a hung one."""
        self.assertNotIn("body *", RC.TARGETS["page"]["sel"])

    def test_every_OTHER_target_is_still_a_named_subtree(self):
        """⚠⚠ THE BASELINE, and it is what makes the page target worth having. If the others ever
        become page-wide this test should be re-read rather than deleted — but today the count is
        the whole argument: 11 named subtrees, and the parts between them measured by nobody."""
        named = [k for k, v in RC.TARGETS.items()
                 if k != "page" and ("#" in (v.get("sel") or "") or "." in (v.get("sel") or "")
                                     or "[" in (v.get("sel") or ""))]
        self.assertGreaterEqual(len(named), 8,
                                "most targets are no longer named subtrees — re-read this file's "
                                "premise before trusting it")


class ThePageTargetMustSettleBeforeItMeasures(unittest.TestCase):
    """★★ The half that would have made it lie. An unsettled document reports zero of everything."""

    def test_it_declares_that_it_settles(self):
        self.assertTrue(RC.TARGETS["page"].get("settles"),
                        "the page target measures without waiting for the document to finish "
                        "assembling — `_settled`'s own docstring calls that the exact false green "
                        "this file exists to refuse")

    def test_it_uses_the_SHAPE_predicate_not_the_byte_length_one(self):
        self.assertTrue(RC.TARGETS["page"].get("settle_shape"),
                        "it settles on innerHTML.length, which never repeats on a page with a live "
                        "clock — the target would sit UNKNOWN for the whole budget on every run")

    def test_the_shape_branch_does_not_require_a_tab_row(self):
        """★ RED PROOF for fault 2, driven rather than read. `.tab[data-tab]` is zero on
        `control_ui.html` for ever; requiring it makes settling impossible there."""
        import inspect
        src = inspect.getsource(RC._settled)
        self.assertIn("shape or int(parts[2]", src,
                      "the shape branch still demands a rendered tab row, which the console page "
                      "does not have and never will")

    def test_the_byte_length_branch_is_UNCHANGED_for_every_other_target(self):
        """⚠ The fix must not quietly loosen the eleven targets that were already settling
        correctly — that would trade one blindness for eleven."""
        import inspect
        src = inspect.getsource(RC._settled)
        self.assertIn("document.body.innerHTML.length", src,
                      "the original predicate was replaced rather than added to")

    def test_a_settle_FAILURE_still_refuses_rather_than_measuring(self):
        """⚠⚠ THE BASELINE. If the shape never stills, the answer must be a refusal — not a clean
        sweep of a half-built page."""
        import inspect
        src = inspect.getsource(RC._settled)
        self.assertIn("never settled", src)
        self.assertIn("return (", src, "the budget-exhausted path no longer returns a reason")


class ADeclaredFloorReportsAndDoesNotBLOCK(unittest.TestCase):
    """★★ v2651. THE NEW INSTRUMENT FOUND AN OLD BACKLOG, AND A GATE THAT BLOCKS ON IT IS THE ONE
    PEOPLE SWITCH OFF.

    Pointed at the whole document for the first time, the page target reports **54 clipped elements
    at 375px** on the served console — real, pre-existing, and nothing to do with whatever is being
    pushed. `render_check` is wired into `hooks/pre-push`, where a red target sets `_px_fail=1` and
    `exit 1`. With no floor this would have BLOCKED EVERY VISUAL PUSH on a backlog it did not
    create — and this file's own subject is that a gate which cries wolf stops being read.

    So the counts are DECLARED per width, printed in full on every run, and refuse only on a RISE.
    Same instrument as `render_coverage.json` and the same shape as `KNOWN_MISSES`: pin the LAW,
    not the number. `verdict` is pure, so every case below drives it directly.
    """

    KNOWN = {"clipped": 54, "broken": None, "zero": 5}
    BASE = {"found": 8, "painted": 3, "zero": 5, "textLen": 500, "clipped": 54,
            "broken": 4, "off": 0, "covered": 0, "unreachable": 0, "clippedWhat": []}

    def _split(self, **over):
        """-> (every line, the refusals only)

        ⚠⚠ IT ASKS THE STRUCTURE, NOT THE PROSE. My first cut of this helper — and of the caller
        it was guarding — separated the two kinds by looking for a `ⓘ` inside the message, so a
        gate's block-or-allow decision rested on detecting a character in a sentence. Found while
        reviewing my own pushed bytes. `verdict` returns the refusals AS the list and hangs the
        report on `.notes`, so a caller that treats the return as "the refusals" is simply right.
        [[source-reading-guard]]
        """
        m = dict(self.BASE)
        m.update(over)
        v = RC.verdict("375x800", m, "body > *", self.KNOWN)
        return list(v) + list(v.notes), list(v)

    def test_at_the_floor_it_REPORTS_and_does_not_refuse(self):
        lines, hurt = self._split()
        self.assertEqual(hurt, [], "the declared backlog is being treated as a refusal, which "
                                   "blocks every visual push on a pre-existing defect")
        self.assertTrue(lines, "the backlog is not printed at all — a silent floor is an "
                               "exemption, not a ratchet")

    def test_ONE_MORE_goes_RED(self):
        """★ The whole point. A floor that cannot go red is an exemption."""
        _, hurt = self._split(clipped=55)
        self.assertTrue(hurt, "55 clipped against a floor of 54 did not refuse")
        self.assertIn("DECLARED FLOOR IS 54", hurt[0])

    def test_an_IMPROVEMENT_is_reported_so_the_floor_gets_LOWERED(self):
        """⚠ A stale floor is a label that outlived its referent — it would go on excusing work
        somebody already did."""
        lines, hurt = self._split(clipped=40)
        self.assertEqual(hurt, [], "fixing 14 defects made the gate red")
        self.assertTrue(any("were FIXED" in x for x in lines),
                        "an improvement is silent, so the floor never gets lowered")

    def test_the_floor_CANNOT_excuse_a_WHOLE_collapse(self):
        """⚠⚠ THE ONE CASE A ZERO FLOOR MUST NEVER SWALLOW. Five closed modals are design; a page
        where NOTHING painted is the false green this whole file exists to refuse, and that branch
        returns before the floor is consulted."""
        _, hurt = self._split(painted=0, zero=8)
        self.assertTrue(hurt, "a fully collapsed page passed under the zero floor")
        self.assertIn("every one of", hurt[0])

    def test_a_SIXTH_collapsed_node_goes_RED(self):
        _, hurt = self._split(zero=6)
        self.assertTrue(hurt, "a sixth top-level node collapsing was excused by the floor")

    def test_a_field_with_NO_floor_still_refuses_on_ANY(self):
        """⚠ The floor is per-field and per-width. `covered` has none, so one is news."""
        _, hurt = self._split(covered=2, coveredWhat=["x"])
        self.assertTrue(hurt, "a covered element passed with no declared floor")

    def test_a_MOVING_count_is_reported_and_never_judged(self):
        """`broken` is declared None because it measures the load race, not the page: two runs of
        the same tree minutes apart gave 11 and 4, since only ~46 of 2,399 images are `complete`
        when the document's shape stills. Ratcheting that would pin noise; a floor high enough to
        absorb the swing would be an exemption wearing a number."""
        lines, hurt = self._split(broken=30)
        self.assertEqual(hurt, [], "a count that moves between runs is failing the gate")
        self.assertTrue(any("NOT JUDGED" in x for x in lines),
                        "the moving count is silent, so a reader cannot tell it was not judged")

    def test_the_refusals_are_the_LIST_and_the_report_rides_on_notes(self):
        """★ THE STRUCTURAL SPLIT ITSELF. A caller that does `if verdict(...)` must block on real
        refusals only, with no string inspection anywhere in the decision."""
        m = dict(self.BASE)
        v = RC.verdict("375x800", m, "body > *", self.KNOWN)
        self.assertEqual(list(v), [], "a width at its declared floor is being treated as failing")
        self.assertTrue(v.notes, "the declared backlog is not reported at all")
        m2 = dict(self.BASE, clipped=55)
        v2 = RC.verdict("375x800", m2, "body > *", self.KNOWN)
        self.assertTrue(list(v2), "a rise above the floor did not land in the refusal list")

    def test_it_stays_a_LIST_so_every_existing_caller_still_works(self):
        """⚠ `test_control` asserts `== []`, `len(...)` and iterates. A bespoke return type would
        have broken eight guards that were already correct."""
        v = RC.verdict("1440x1000", {"found": 3, "painted": 3, "textLen": 42, "off": 0,
                                     "clipped": 0, "covered": 0, "broken": 0}, "#s")
        self.assertIsInstance(v, list)
        self.assertEqual(v, [])
        self.assertEqual(len(v), 0)

    def test_EVERY_return_path_carries_the_structure(self):
        """★★ RED PROOF for the one that bit me: a single untagged `return [...]` gives back a
        plain list, and `.notes` raises AttributeError at the call site. Walked by AST, because a
        path I did not think to drive is exactly the one that would be bare."""
        import ast
        import inspect
        import textwrap
        tree = ast.parse(textwrap.dedent(inspect.getsource(RC.verdict)))
        fn = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "verdict"][0]
        bare = []
        for r in ast.walk(fn):
            if not isinstance(r, ast.Return) or r.value is None:
                continue
            if isinstance(r.value, ast.Name):          # `return v` inside the _tag helper
                continue
            if not (isinstance(r.value, ast.Call)
                    and getattr(r.value.func, "id", "") == "_tag"):
                bare.append(r.lineno)
        self.assertEqual(bare, [],
                         "return path(s) at %s hand back a plain list, so `.notes` raises at the "
                         "call site and the report is lost" % bare)

    def test_the_declared_floor_is_ON_the_target_and_covers_every_width(self):
        known = RC.TARGETS["page"].get("known") or {}
        self.assertTrue(known, "the page target declares no floor, so it blocks on the backlog")
        for w, h in RC.WIDTHS:
            self.assertIn("%dx%d" % (w, h), known,
                          "no floor declared for %dx%d — that width blocks the push" % (w, h))


class TheProbeIsREUSEDAndNotReimplemented(unittest.TestCase):
    """⚠ The recovery paths are why the number is trustworthy, and re-deriving them would be a
    second thing to be wrong."""

    def test_the_page_target_carries_no_probe_of_its_own(self):
        for k in ("probe", "sweep", "measure", "js"):
            self.assertNotIn(k, RC.TARGETS["page"],
                             "the page target defines its own %r instead of using _PROBE" % k)

    def test_the_shared_probe_still_honours_every_recovery_path(self):
        """★★ These four are what separate a real cut from a false red, and a page-wide target
        multiplies any one of them being absent across the whole document.

        ⚠ This reads the probe SOURCE, and that is a compromise I am naming rather than hiding: the
        probe is a javascript string, so there is no AST to walk and no way to drive it without a
        browser. The tokens chosen are the ones that would have to be DELETED for the behaviour to
        go away, not prose describing it. [[source-reading-guard]]
        """
        for token, why in (
                ("scrollsY", "the scroller exclusion — ink one flick away is not destroyed"),
                ("_recoverable", "the `title` recovery — the full string is still reachable"),
                ("inert(", "the inert check — an opacity-0 control cannot be visibly cut"),
                ("reAnchors", "the fixed-position escape and its re-anchoring rules")):
            self.assertIn(token, RC._PROBE,
                          "the probe lost %s. A page-wide target multiplies that omission across "
                          "the whole document — 31 false reds came from this one being missing "
                          "before." % why)

    def test_OK_TRUNC_is_still_per_target_and_not_global(self):
        """A page-wide allowlist would excuse a class everywhere it appears."""
        self.assertNotIn("truncation_ok", RC.TARGETS["page"],
                         "the page target carries a truncation allowlist, which would excuse a "
                         "class across the whole document rather than in one panel")


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
