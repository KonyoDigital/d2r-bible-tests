# -*- coding: utf-8 -*-
"""THE SESSION IS ASKED WHERE AN ITEM WAS — AND ITS ANSWER MAY ONLY FLAG, NEVER OVERWRITE.

`retro_gate.corroborate_location` has answered *"what location does the SESSION agree on?"* since
it was written, and NOTHING ever asked it — one of the 26 verdict-shaped functions with no caller.
Its own docstring names the defect it exists for:

    "A single read placing an item on the floor while every other read in the same session says
     stash is contradicted by its own session — which is exactly the 'Rune Grip at loc floor'
     defect, visible only from the clock."

`_kai_compile_register` is where that defect is MINTED: `loc` is stamped EARLIEST-SIGHTING-WINS
with no cross-check, and it travels to rendered API rows downstream. One early misread becomes the
permanent answer.

⚠⚠ THE JOIN MAY ONLY FLAG, AND THAT IS THE FUNCTION'S OWN RULING RATHER THAN MY CAUTION: a split
session is *"worth a second look, not an automatic correction"*. Rewriting `loc` from a majority
would replace one unverified claim with another AND destroy the evidence that they disagreed —
which is the only thing that makes the disagreement findable later. [[unknown-stays-unknown]]

⚠ AND "NOBODY SAID" IS NOT "THEY DISAGREED". A row carrying no loc of its own gets `locAgrees:
None`, never False. Collapsing those would turn silence into a contradiction and put a flag on
rows that never made a claim. [[zero-needs-a-denominator]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

os.environ.setdefault("TV_STUB", "1")
import control_app as ca
import retro_gate as rg


def _src():
    with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
        return re.sub(r"(?m)^\s*#.*$", " ", fh.read())


def _rows(*locs):
    out = []
    for i, l in enumerate(locs):
        r = {"name": "Item%d" % i, "ts": 1000 + i, "frameId": "f%d" % i}
        if l:
            r["loc"] = l
        out.append(r)
    return out


# Three items every D2 player knows, checked against the real DB inside the tests that use them.
MINORITY, A, B = "shako", "vampire gaze", "stone of jordan"


class TheSessionGetsAVoteOnWhere(unittest.TestCase):

    def test_the_compiler_actually_asks(self):
        """[[the-unjoined-end]] — it answered for versions and nobody called it."""
        src = _src()
        self.assertIn("_rg.corroborate_location(", src,
                      "the register compiler no longer asks the session where the item was, so "
                      "an early misread is once again the permanent answer")
        # ⚠⚠ AND IT MUST NOT ASK WITH `sess_rows`. v3212 joined it that way and the call was
        # INERT: `corroborate_location` reads a location off each entry via `retro_gate._loc_of`
        # (loc / where / container / location), and session rows carry none of those at the top
        # level — the locations live in `names_loc`. Every call returned
        # "no read in this session said where it was". Asserting only that the call EXISTS is what
        # let a connected, shipped, dead wire look joined. [[the-unjoined-end]]
        self.assertNotIn("_rg.corroborate_location(sess_rows)", src,
                         "the corroboration is being handed raw session rows again — those carry "
                         "no top-level loc, so it can only ever answer None and the flag can "
                         "never fire")
        self.assertIn("names_loc", src.split("_rg.corroborate_location(")[0][-900:],
                      "nothing builds the per-read list from names_loc before the corroboration, "
                      "so whatever it is being handed is not the session's location reads")

    def test_it_never_overwrites_loc(self):
        """the function's OWN ruling: a second look, not an automatic correction."""
        src = _src()
        i = src.find("_rg.corroborate_location(")
        self.assertGreater(i, 0)
        window = src[i:i + 700]
        self.assertNotIn('_r["loc"] =', window,
                         "the corroboration is WRITING loc — that replaces one unverified claim "
                         "with another and destroys the evidence that they disagreed")
        self.assertIn('_r["locAgrees"]', window, "nothing records whether the row agrees")

    def test_a_row_with_NO_loc_is_None_not_False(self):
        """'nobody said' and 'they disagreed' are different facts — asserted on BEHAVIOUR.

        ⚠ v3215 — this read the source for the literal `None if _rl is None else`, so rewriting
        the same rule as an if/else broke it while the behaviour was unchanged and, in fact,
        improved. A law that pins an EXPRESSION forbids refactors instead of forbidding defects.
        [[source-reading-guard]]
        """
        rows = [
            {"lane": "deep", "ts": 1000, "frameId": "f0",
             "names": [MINORITY], "names_loc": {MINORITY: "stash"}},
            # this one is NAMED but its location is never stated by anybody
            {"lane": "deep", "ts": 1001, "frameId": "f1", "names": [A], "names_loc": {}},
        ]
        by = {r["name"]: r for r in ca._kai_compile_register(rows)}
        quiet = by.get(A)
        self.assertIsNotNone(quiet, "the register lost the row that claimed no location")
        self.assertIsNone(quiet.get("locAgrees"),
                          "a row that never claimed a location is flagged %r — silence is being "
                          "turned into a contradiction" % quiet.get("locAgrees"))

    def test_a_row_the_session_never_voted_on_is_not_a_contradiction(self):
        """⚠ v3215 — `equipped` against a stash consensus is SILENCE, not disagreement.

        `loc` can also come from reel_segments.lane_at, whose only non-None value is 'stash',
        while names_loc carries equipped|inventory|stash|floor. Before this, a permanently-worn
        item read as 'equipped' was filed as contradicting a stash session that had said nothing
        about it. False must mean: another read in THIS session said somewhere else.
        """
        rows = [
            {"lane": "deep", "ts": 1000, "frameId": "f0",
             "names": [MINORITY], "names_loc": {MINORITY: "equipped"}},
            {"lane": "deep", "ts": 1001, "frameId": "f1",
             "names": [A], "names_loc": {A: "stash"}},
            {"lane": "deep", "ts": 1002, "frameId": "f2",
             "names": [B], "names_loc": {B: "stash"}},
        ]
        by = {r["name"]: r for r in ca._kai_compile_register(rows)}
        worn = by.get(MINORITY)
        self.assertIsNotNone(worn, "the register lost the equipped row")
        self.assertIs(False, worn.get("locAgrees"),
                      "'equipped' WAS voted in this session, so disagreeing with a stash "
                      "consensus is a real contradiction and must read False")

    def test_case_and_padding_do_not_manufacture_a_contradiction(self):
        """⚠ v3215 — the consensus is lowercased by retro_gate._loc_of; names_loc is verbatim."""
        rows = [
            {"lane": "deep", "ts": 1000, "frameId": "f0",
             "names": [MINORITY], "names_loc": {MINORITY: "  Stash "}},
            {"lane": "deep", "ts": 1001, "frameId": "f1",
             "names": [A], "names_loc": {A: "stash"}},
        ]
        by = {r["name"]: r for r in ca._kai_compile_register(rows)}
        row = by.get(MINORITY)
        self.assertIsNotNone(row, "the register lost the row")
        self.assertIs(True, row.get("locAgrees"),
                      "a row reading '  Stash ' is flagged %r against a 'stash' consensus it "
                      "helped produce — case and padding are manufacturing disagreement"
                      % row.get("locAgrees"))

    # ── the underlying function still behaves ────────────────────────────────────────────
    def test_a_unanimous_session_agrees(self):
        loc, why = rg.corroborate_location(_rows("stash", "stash", "stash"))
        self.assertEqual("stash", loc)
        self.assertIn("agreed", why)

    def test_a_split_session_leads_but_does_not_convict(self):
        loc, why = rg.corroborate_location(_rows("stash", "stash", "floor"))
        self.assertEqual("stash", loc)
        self.assertIn("second look", why,
                      "a split session no longer says it is worth a second look rather than an "
                      "automatic correction — that phrase IS the rule")

    def test_a_silent_session_says_so(self):
        loc, why = rg.corroborate_location(_rows(None, None))
        self.assertIsNone(loc, "a session where nobody said where is being given a location")
        self.assertIn("no read", why)

    # ── end to end, on the compiler ──────────────────────────────────────────────────────
    def test_the_minority_row_is_flagged_and_its_loc_survives(self):
        # ⚠⚠ THE FIXTURE WAS THE DEFECT, TWICE OVER, AND IT FAILED FOR NEITHER REASON THE LAW
        # IS ABOUT. `_kai_compile_register` reads rows shaped
        # {lane, ts, frameId, names, names_loc} — not {name, loc} — and it drops any name that is
        # not a REAL DB item (`if low not in fulln: return`). So three invented names in the wrong
        # shape produced an EMPTY register and the law reported "the register lost the row
        # entirely" about a compiler that was working correctly.
        # Names are taken from `_kai_fullnames()` at runtime rather than hardcoded: a hardcoded
        # name silently stops being real when the item DB changes, and the law would go green over
        # nothing again. [[feedback-blind-fixture-green-gate]] [[zero-needs-a-denominator]]
        # ⚠ NAMED ITEMS, CHECKED AGAINST THE REAL DB — not `sorted(...)[0:3]`. That slice picked
        # `" + r + "`, `' + r + '` and `1. hide trash gear`: parse artefacts that really are in
        # `_kai_fullnames()` and that `_register_is_junk` does not catch. They would have made this
        # law pass over garbage. Three items every D2 player knows, asserted to exist so the law
        # FAILS LOUDLY if the item DB ever stops carrying them rather than quietly testing nothing.
        minority, a, b = MINORITY, A, B
        _full = ca._kai_fullnames()
        for _n in (minority, a, b):
            self.assertIn(_n, _full,
                          "%r is no longer in the item DB, so this end-to-end case would assert "
                          "over an empty register" % _n)
        rows = [
            {"lane": "deep", "ts": 1000, "frameId": "f0",
             "names": [minority], "names_loc": {minority: "floor"}},
            {"lane": "deep", "ts": 1001, "frameId": "f1",
             "names": [a], "names_loc": {a: "stash"}},
            {"lane": "deep", "ts": 1002, "frameId": "f2",
             "names": [b], "names_loc": {b: "stash"}},
        ]
        reg = ca._kai_compile_register(rows)
        by = {r["name"]: r for r in reg}
        rg_row = by.get(minority)
        self.assertIsNotNone(rg_row, "the register lost the row entirely")
        self.assertEqual("floor", rg_row.get("loc"),
                         "the minority row's own loc was OVERWRITTEN — the evidence that the "
                         "session disagreed is gone")
        self.assertIs(False, rg_row.get("locAgrees"),
                      "the row contradicting its own session is not flagged")
        self.assertEqual("stash", rg_row.get("locSession"))


RED_PROOF = [
    # ⚠ v3215 — re-anchored: v3215 rewrote the ternary as an if/else, so the old `find` matched
    # 0 times and heart2 would have filed this gate BLIND.
    ("control_app.py", '_r["locAgrees"] = None\n                else:',
     '_r["locAgrees"] = False\n                else:',
     "test_a_row_with_NO_loc_is_None_not_False"),
    # ⚠⚠ v3215 — THIS ANCHOR NAMED v3212's INERT FORM AND MATCHED 0 TIMES THE MOMENT v3214
    # FIXED IT. heart2._run_gate counts the `find` string in the source: got != want prints
    # "the tamper matched 0 time(s), expected 1. The SABOTAGE is wrong, not the law" and returns
    # INVALID, which revokes the standing proof and files the gate under BLIND. So this
    # brand-new gate would have shipped UNPROVABLE on its first proving run — a red-proof that
    # cannot run is the same nothing as no red-proof. Found by a cross-family review.
    # ⚠ THE TAMPER HAS TO DEFEAT THE LAW, NOT JUST DIFFER FROM IT: replacing the reads with an
    # empty list makes the consensus None, which is exactly what
    # `test_the_minority_row_is_flagged_and_its_loc_survives` refuses.
    ("control_app.py", "_cons, _cwhy = _rg.corroborate_location(_reads)",
     "_cons, _cwhy = _rg.corroborate_location([])",
     "test_the_minority_row_is_flagged_and_its_loc_survives"),
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
