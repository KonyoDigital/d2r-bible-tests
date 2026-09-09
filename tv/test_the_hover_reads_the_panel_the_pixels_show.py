#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2807 — THE CONTAINER WAS ACCEPTED AND DROPPED, AND THAT IS A WRONG-PANEL BUG.

`_mini_cells_from_live_frame(container)` took the argument and used it exactly ONCE — in its own
signature. Measured on the shipped source: one occurrence, zero uses.

That is not merely "inventory does not qualify". It is worse, because the two halves disagree:

    vault_corpus.inventory_lattice(frame_path)      takes NO container — finds a lattice wherever
    vault_corpus.inventory_occupancy(frame, lat)    one is
    hover_mode.start(cells, ..., container=X)       maps those cells through
                                                    slot_identity.panel_box_for(X)

and the panels are nowhere near each other:

    stash      x=281   y=381   w=868   h=869
    inventory  x=1791  y=984   w=868   h=347

So a frame showing the INVENTORY, with the button hardcoded to `container: 'stash'`, produced real
cells read off the inventory grid and hovered them at STASH coordinates — 1,510px away. The
pointer sweeps empty screen, `moved` counts up, and every number says it worked.

★ THE LATTICE ITSELF ANSWERS THE QUESTION, so nothing has to guess. slot_identity.GRIDS holds
stash 10x10, inventory 10x4, cube 3x4 — three distinct shapes. The reader now infers which panel
it read and RETURNS it, the caller hovers THAT one, and a shape matching none of them is REFUSED
rather than assigned to whatever the caller happened to name. [[unknown-stays-unknown]]
"""
import os
import ast
import io
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import slot_identity as SI  # noqa: E402

APP = os.path.join(HERE, "control_app.py")


def _app():
    with io.open(APP, encoding="utf-8") as fh:
        return fh.read()


def _reader():
    for n in ast.walk(ast.parse(_app())):
        if isinstance(n, ast.FunctionDef) and n.name == "_mini_cells_from_live_frame":
            return n
    return None


class TestTheHoverReadsThePanelThePixelsShow(unittest.TestCase):

    def test_the_known_grids_are_distinguishable(self):
        """The whole inference rests on this. If two panels ever share a shape, the reader cannot
        tell them apart and must go back to refusing rather than guessing."""
        shapes = {}
        for name, shape in (SI.GRIDS or {}).items():
            shapes.setdefault(tuple(shape), []).append(name)
        clashes = {k: v for k, v in shapes.items() if len(v) > 1}
        self.assertEqual(clashes, {},
                         "two panels share a grid shape %s — the lattice can no longer say which "
                         "one it read, and inferring would be guessing" % clashes)
        print("\n   grids: %s" % dict(SI.GRIDS))

    def test_every_calibrated_panel_has_a_box(self):
        """A panel in GRIDS with no PANELS entry can be inferred and then not hovered."""
        for name in SI.GRIDS:
            box, why = SI.panel_box_for(2940, 1912, container=name)
            if name in SI.PANELS:
                self.assertIsNotNone(box, "%s is calibrated but panel_box_for refuses it" % name)
            else:
                self.assertIsNone(box, "%s has no measured panel and must be REFUSED, not guessed"
                                       % name)

    def test_the_reader_returns_the_container_it_actually_read(self):
        fn = _reader()
        self.assertIsNotNone(fn, "the live-frame reader is gone")
        rets = [r for r in ast.walk(fn) if isinstance(r, ast.Return)]
        self.assertTrue(rets, "the reader returns nothing")
        for r in rets:
            self.assertIsInstance(r.value, ast.Tuple,
                                  "a return at line %d is not a tuple — every path must say "
                                  "WHICH panel was read, including the refusals" % r.lineno)
            self.assertEqual(len(r.value.elts), 3,
                             "the return at line %d carries %d value(s), not 3 (cells, why, "
                             "container). A path that omits the container silently hands the "
                             "caller's guess back to the hover planner."
                             % (r.lineno, len(r.value.elts)))
        print("   %d return path(s), all 3-tuples" % len(rets))

    # ══ v2865 — LAW RETIRED: ITS SUBJECT WAS DELETED BY RULING ═══════════════════════════════
    #   test_the_hover_uses_what_was_SEEN_not_what_was_ASKED
    # It asserted `container=(_saw or _container)` in control_app.py — the MINI(AUTOMATIC) call
    # site v2857 removed. `_saw` now appears NOWHERE in the tree. The law outlived its referent and
    # was red on CI. The four laws below read slot_identity and are untouched.
    # [[label-outlived-referent]]

    def test_an_unknown_grid_is_refused_not_assigned(self):
        """A shape matching no measured panel must not fall back to the caller's name."""
        src = _app()
        self.assertIn("matches no panel this console has", src,
                      "an unrecognised grid no longer refuses — it would be hovered as whatever "
                      "the button happened to say")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
# Handing the caller's guess back to the hover planner IS the wrong-panel bug: real cells read off
# one grid, swept across the coordinates of another 1,510px away.
RED_PROOF = [
    {
        "why": "RE-POINTED v2865. The block here tampered `container=(_saw or _container)` in "
               "control_app.py — deleted with MINI(AUTOMATIC) in v2857, so it matched 0 times and "
               "turned CI red on the well-formedness law: a sabotage that changes nothing proves "
               "nothing. The surviving laws read slot_identity, so the proof reads it too. Removing "
               "the inventory grid indistinguishable from the stash grid is the defect those laws "
               "exist for: two panels with the same shape cannot be told apart from the lattice, so "
               "a read of one is assigned to the other and a wrong cell is worse than no cell. "
               "MEASURED: 1 match, RED, breaking test_the_known_grids_are_distinguishable.\n"
               "⚠ MY FIRST RE-POINT WAS A NO-OP AND CAME BACK BLIND: `GRIDS = {}` or `{...}` "
               "evaluates to the original dict, because an empty dict is falsy. I authored it "
               "WITHOUT sandbox-verifying first — my own rule, skipped, and the engine caught it. "
               "[[sabotage-is-usually-the-wrong-one]]",
        "file": "slot_identity.py",
        "find": '"inventory": (10, 4)',
        "replace": '"inventory": (10, 10)',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
