#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CRUSHED-LEAF - THE CLIP SCAN CALLED A 0px-WIDE LABEL CLEAN (REG-2237, #318 / #70).

REG-2115 (#315) measured the update bar's wait label laid out at 0px wide on his console - the words
"waiting for it to fi..." gone to a sliver - while render_check reported `clipped 0` at that width.
It was closed for that ONE label by lifting it into its own target (`update-wait-say`), where a
target's OWN zero-size `sel` node is a refusal. Every OTHER target kept the blind spot: in the clip
scan the self branch only judges a box with `clientWidth>0`, and the leaf/ancestor branch returns the
instant `cr.width<1`, so a DESCENDANT label squeezed to nothing is never judged. A 0px box shows no
ink and no ellipsis, and no `title` is one hover away from a zero-width strip.
[[visual-regression-detector]]

THE FIX adds a crushed-leaf branch to `_PROBE`: a leaf with real text and a real line box
(`height>=4`) whose WIDTH is under 2px, inside a painted parent, is flagged `clipped [crushed]`
through the shared `flag()` counter - so the declared per-width floors and OK_TRUNC already judge it.

height>=4 is the whole correctness of it. An sr-only label (`.ht-lbl`, `.rs-name`, `.mat-name` -
`width:1px height:1px clip:rect(0 0 0 0)`) is hidden on PURPOSE and is 1px TALL; the smallest real
line in this tree is 13px (`--fs-2xs`). `inert()` cannot tell them apart - clip-hiding sets no
display/visibility/opacity/pointer-events - so without the height floor the probe would flag every
accessibility label in the document. [[regression-guard]]

The probe is a javascript STRING, so there is no AST to walk and no way to drive it without a
browser - the same compromise `test_render_gate_sees_the_page.py` names in
`test_the_shared_probe_still_honours_every_recovery_path`. The red-first class below reads `_PROBE`
for the tokens that would have to be DELETED for the behaviour to vanish; the second class drives the
pure `verdict` to prove a crushed finding actually reaches a block and is not a private counter
nobody judges. [[source-reading-guard]] [[the-unjoined-end]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import render_check as RC  # noqa: E402


class TheClipScanSeesALeafCrushedToZeroWidth(unittest.TestCase):
    """RED-FIRST. Without the crush branch in _PROBE every assertion here fails - that is the #70
    defect, restored."""

    def test_the_probe_flags_a_crushed_leaf(self):
        self.assertIn(
            "flag('crushed')", RC._PROBE,
            "the clip scan has no crushed-leaf branch - a descendant label squeezed to 0px wide "
            "(REG-2115's wait label, and every target after it) is still reported clean")

    def test_a_width_crush_needs_a_real_line_box_so_sr_only_is_spared(self):
        """THE CORRECTNESS GUARD. sr-only labels (.ht-lbl / .rs-name / .mat-name) are width:1px
        HEIGHT:1px and inert() cannot see them; without the height floor the probe would flag every
        one of them across the document. The smallest real line in this tree is 13px (--fs-2xs), so
        height>=4 can never confuse a genuine crush with a 1px accessibility clamp."""
        self.assertIn(
            "cr.width < 2 && cr.height >= 4", RC._PROBE,
            "the crush branch does not require a real line box, so a 1px-tall sr-only clamp is "
            "indistinguishable from a genuine width-crush and the gate goes red on accessibility "
            "labels")

    def test_the_crush_requires_a_painted_parent(self):
        """A crush inside an already-collapsed subtree IS that subtree's collapse - counted once by
        `zero`/`painted` - and must not be counted again here per label."""
        self.assertIn(
            "_crpr", RC._PROBE,
            "the crush branch does not look at its parent, so a label inside a fully collapsed "
            "ancestor is double-counted as crushed")
        self.assertIn(
            "_crpr.width >= 2", RC._PROBE,
            "the parent guard does not require a painted box, so a crush in a 0-width ancestor is "
            "reported as a per-label crush")


class ACrushedFindingIsJUDGEDAndNotJustCounted(unittest.TestCase):
    """THE UNJOINED END. A new finding wired to a private counter that `verdict` never reads would
    be invisible to the gate - green for ever. These pin the crush to the shared, judged path.

    `verdict` is pure, so the cases drive it directly, exactly as ADeclaredFloorReportsAndDoesNotBLOCK
    does in test_render_gate_sees_the_page.py."""

    def test_the_crush_rides_the_shared_clipped_counter(self):
        self.assertIn("flag('crushed')", RC._PROBE)
        self.assertNotIn(
            "crushed++", RC._PROBE,
            "the crush uses a private counter instead of flag()/`clipped`, so the declared floors "
            "and OK_TRUNC never see it and verdict never judges it")

    def test_a_single_crushed_leaf_refuses_when_no_floor_is_declared(self):
        """A crushed label is one `clipped` element; a target with no declared clipped floor refuses
        on ANY, and the `[crushed]` reason must reach the sentence a reader acts on."""
        m = {"found": 3, "painted": 3, "zero": 0, "textLen": 120, "off": 0,
             "clipped": 1, "covered": 0, "broken": 0, "unreachable": 0, "invisible": 0,
             "clippedWhat": ["fbe-say :: waiting for it to fi [crushed]"]}
        v = RC.verdict("1440x1000", m, "#fleet-eta-say")
        self.assertTrue(
            list(v), "a leaf crushed to 0px (clipped=1) with no declared floor did not refuse")
        self.assertIn("crushed", " ".join(v),
                      "the crushed reason never reaches the refusal a reader sees")

    def test_a_declared_floor_still_goes_RED_on_one_more_crush(self):
        """A floor is a ratchet, not an off switch: one crushed leaf more than the blessed count
        must still refuse. [[regression-guard]]"""
        m = {"found": 3, "painted": 3, "zero": 0, "textLen": 120, "off": 0,
             "clipped": 2, "covered": 0, "broken": 0, "unreachable": 0, "invisible": 0,
             "clippedWhat": ["a [crushed]", "b [crushed]"]}
        v = RC.verdict("1440x1000", m, "#fleet-eta-say", {"clipped": 1})
        self.assertTrue(list(v), "a second crushed leaf above a floor of 1 was excused")
        self.assertIn("DECLARED FLOOR IS 1", " ".join(v))


# == THE EXECUTABLE RED-PROOF ==================================================
# Sabotage the anchors the behaviour lives on; the law must go red. Each `find` occurs exactly once
# in render_check.py after the fix (grep -F -c "<find>" render_check.py == 1).
RED_PROOF = [
    {
        "why": "flag('crushed') is the entire crushed-leaf branch; deleting it returns render_check "
               "to the #318/#70 blind spot where a 0px-wide label reads as clipped 0",
        "file": "render_check.py",
        "find": "flag('crushed')",
        "replace": "flag('_CRUSH_TAMPERED_')",
        "matches": 1,
    },
    {
        "why": "height>=4 is what spares the 1px-tall sr-only labels; drop it and the crush branch "
               "cannot tell a width-crush from a both-axes accessibility clamp",
        "file": "render_check.py",
        "find": "cr.width < 2 && cr.height >= 4",
        "replace": "cr.width < 2 && cr.height >= 0",
        "matches": 1,
    },
]

if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
