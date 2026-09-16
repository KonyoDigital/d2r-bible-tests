# -*- coding: utf-8 -*-
"""A FUNCTION THAT ANSWERS A QUESTION NOBODY ASKS IS NOT BUILT — IT IS DECORATION.

#100 bucketed 26 verdict-shaped functions: 6 to JOIN, 12 correctly unjoined, the rest unknown.
These are the last two of the six, and both had exactly ONE reference in the whole tree — their
own test. Written, reasoned, tested, and unreachable.

⚠⚠ AND IN BOTH CASES THE LIVE PATH CARRIED THE DEFECT THE FUNCTION WAS WRITTEN TO PREVENT.

`_chron_lane_detail()` says it in its docstring: *"The lane LIST is what the gate scores; this is
what a human is owed when grok is missing. 'You switched it off' and 'there is no Grok CLI here'
are different facts and only one of them is a problem."* Meanwhile BOTH sweep doors refused with a
flat *"the primary (Claude) lane is unavailable"* — the sentence that sends someone reinstalling a
CLI they had deliberately switched off. Measured on this machine the moment it was joined:
`grok: present=false, why="you switched it off (mode=off)"`.

`story_of(state)` says it too: *"A state this table does not know returns its own name rather than
a default … instead of quietly joining PENDING, which is exactly how a retired item comes back to
life."* Meanwhile the ONLY place states are resolved for the page indexed `_SEC[state]` directly
and raised KeyError.

[[plumbing-with-no-tap]] [[the-unjoined-end]] [[unknown-stays-unknown]]
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass


def _prod_callers(mod_file, fname):
    """Call sites of fname in a PRODUCTION module, excluding its own definition. -> int

    ⚠ COUNTED BY PARSING, not by grepping a name that also appears in prose. Several of these
    functions are named in comments explaining why they exist, and a comment is not a caller —
    that is the whole distinction this file is about. [[source-reading-guard]]
    """
    src = io.open(os.path.join(HERE, mod_file), encoding="utf-8").read()
    n = 0
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Call):
            f = node.func
            name = getattr(f, "id", None) or getattr(f, "attr", None)
            if name == fname:
                n += 1
    return n


class AWrittenAnswerHasAReader(unittest.TestCase):

    def test_the_lane_detail_is_asked_by_production(self):
        n = _prod_callers("control_app.py", "_chron_lane_detail")
        self.assertGreaterEqual(
            n, 2,
            "_chron_lane_detail has %d production call site(s). Both sweep doors refuse when a "
            "lane is missing, and without it that refusal cannot say whether the lane is OFF or "
            "ABSENT — which is the only reason the function exists" % n)

    def test_the_refusal_carries_it(self):
        """Pinned on the refusal itself, because a call somewhere else would not help him."""
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        hits = src.count('"laneDetail": _chron_lane_detail()')
        self.assertEqual(
            2, hits,
            "%d of the 2 lane refusals carry laneDetail — a door that refuses without saying "
            "which kind of absent sends him reinstalling something he turned off" % hits)

    def test_story_of_is_asked_by_production(self):
        n = _prod_callers("board_sync.py", "story_of")
        self.assertGreaterEqual(
            n, 1,
            "story_of has no production caller, so the page resolves states by indexing _SEC "
            "directly — which raises KeyError on an unknown state instead of rendering it as the "
            "odd row a person notices")

    def test_an_unknown_state_is_rendered_not_filed(self):
        import board_sync as B
        title, order = B.story_of("a-state-nobody-added-here")
        self.assertIn("does not know", title,
                      "an unknown state no longer announces itself: %r" % title)
        self.assertNotEqual(-200, order,
                            "an unknown state took PENDING's section order — that is the quiet "
                            "filing this function exists to refuse, and how a retired item comes "
                            "back to life")

    def test_a_known_state_is_unchanged(self):
        """The opposite error: making unknowns loud must not disturb the seven real stages."""
        import board_sync as B
        self.assertEqual(("5 · COMPLETED", -120), B.story_of("done"))
        self.assertEqual(("1 · PENDING", -200), B.story_of("pending"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
