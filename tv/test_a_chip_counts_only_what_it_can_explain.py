# -*- coding: utf-8 -*-
"""A CHIP MAY ONLY COUNT ROWS WHOSE ABSENCE OF FILM IT CAN EXPLAIN.

⚠⚠ THE DEFECT THIS EXISTS FOR WAS MINE, AND IT SHIPPED IN THE COMMIT THAT ARGUED AGAINST IT.

v3092 dropped shelf rows with no film into two chips — `retired to history` and `no film and no
record` — and put that split ABOVE the stub check. A STUB is a run with under three real rows and
no reel: it never HAD film. But a stub also has `footageN == 0`, so every one of them fell into the
no-film branch first and was labelled as though its film had been retired after giving up its
information.

MEASURED on his live console, 2,894 rows:

    chip                      would show     truth     stubs swept in
    retired to history              450        266               184
    no film and no record         2,424        138             2,286   <- 17x overstatement

The ❓ chip would have claimed **2,424** when the answer is **138**. And the commit that shipped it
carries a comment insisting the two states be kept apart *"because collapsing them would throw away
the only fact that says whether the river finished or stalled"*. The reasoning was right, the branch
order was wrong, and prose in a commit is not evidence about behaviour.

⚠ AND THE NUMBERS I REPORTED WERE MEASURED BEFORE THE CODE, NEVER AGAINST IT. I told him 266/138 —
correct for the data, describing a program I had not yet written. That is the same shape as claiming
a gold accent "lit on 10 cards" without reading the CSS: a figure derived from intent rather than
from the artifact. [[label-outlived-referent]] [[zero-needs-a-denominator]]

THE RULE: every drop branch must come AFTER the branches whose rows it would otherwise absorb. A
stub is not a retired reel, and a chip that cannot explain why a row has no film must not count it.
"""
import io
import os
import re
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))


def _build_block():
    """The shelf card build, anchored at both ends — never a fixed-size window."""
    with io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
        src = fh.read()
    a = src.find("var cards = (TH.sessions || []).map(function(sm, i){")
    assert a > 0, "the shelf card build is gone"
    b = src.find("var n = sm.n || (i + 1);", a)
    assert b > a, "the build block has no end anchor"
    return src[a:b]


class TestAChipCountsOnlyWhatItCanExplain(unittest.TestCase):

    def test_the_stub_check_precedes_the_no_film_split(self):
        """The whole defect, in one ordering."""
        block = _build_block()
        code = "\n".join(l.split("//", 1)[0] for l in block.splitlines())
        i_stub = code.find("sm.stub")
        i_film = code.find("sm.footageN")
        self.assertGreater(i_stub, 0, "the stub branch is gone from the card build")
        self.assertGreater(i_film, 0, "the no-film branch is gone from the card build")
        self.assertLess(
            i_stub, i_film,
            "the no-film split runs BEFORE the stub check, so every stub — a run that never had "
            "film — is counted as a reel whose film was retired. Measured on his console that put "
            "2,286 stubs into the 'no film and no record' chip, making it read 2,424 against a "
            "true 138")
        print("build order: stub check at %d, no-film split at %d — stub first" % (i_stub, i_film))

    def test_both_chips_exist_and_count_separately(self):
        block = _build_block()
        for var in ("_shRetiredN", "_shUnknownN"):
            self.assertIn(var, block, "%s is gone — the two kinds of absence collapsed" % var)
        self.assertNotEqual(
            block.count("_shRetiredN++"), 0, "nothing increments the retired counter")
        self.assertNotEqual(
            block.count("_shUnknownN++"), 0, "nothing increments the unknown counter")
        print("two counters, incremented separately")

    def test_the_two_states_are_not_folded_into_one_branch(self):
        """`retired` and `unknown` must stay distinguishable — one is a finished story."""
        block = _build_block()
        self.assertIn("'retired'", block, "the retired state is no longer tested by name")
        self.assertIn("'unknown'", block, "the unknown state is no longer tested by name")
        print("retired and unknown are still separate branches")

    def test_the_ordering_holds_against_his_real_shape(self):
        """A pure replication of the branch order over synthetic rows of each kind.

        No console, no footage — so it cannot go blind on CI.
        """
        rows = [
            {"fixture": True},                                                  # dropped first
            {"stub": True, "footageN": 0, "footageState": "unknown"},           # a stub, NOT unknown
            {"stub": True, "footageN": 0, "footageState": "retired"},           # a stub, NOT retired
            {"footageN": 0, "footageState": "retired"},                         # truly retired
            {"footageN": 0, "footageState": "unknown"},                         # truly unknown
            {"footageN": 7, "footageState": "none"},                            # a real card
        ]
        fx = st = ret = unk = built = 0
        for sm in rows:                       # the order this law pins
            if sm.get("fixture"):
                fx += 1; continue
            if sm.get("stub"):
                st += 1; continue
            if not sm.get("footageN"):
                s = sm.get("footageState")
                if s == "retired":
                    ret += 1; continue
                if s == "unknown":
                    unk += 1; continue
            built += 1
        self.assertEqual((fx, st, ret, unk, built), (1, 2, 1, 1, 1),
                         "the branch order does not separate a stub from a retired reel")
        print("replication: fixtures %d · stubs %d · retired %d · unknown %d · built %d"
              % (fx, st, ret, unk, built))


RED_PROOF = [
    {
        "why": "the no-film split moves back above the stub check, so every stub — a run that never "
               "had film — is counted as a reel whose film was retired after giving up its "
               "information. On his console that made the chip read 2,424 against a true 138",
        "file": "control_ui.html",
        "find": "      if (!_shBuildGhosts && sm && sm.stub) return '';\n      if (sm && !(sm.footageN || 0) && !_shBuildGhosts){",
        "replace": "      if (sm && !(sm.footageN || 0) && !_shBuildGhosts){",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
