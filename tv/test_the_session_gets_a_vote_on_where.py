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
        """'nobody said' and 'they disagreed' are different facts."""
        src = _src()
        i = src.find('_r["locAgrees"]')
        self.assertGreater(i, 0)
        self.assertIn("None if _rl is None else", src[i:i + 120],
                      "a row that never claimed a location is being flagged as DISAGREEING, which "
                      "turns silence into a contradiction")

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
        minority, a, b = "shako", "vampire gaze", "stone of jordan"
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
    ("control_app.py", "_r[\"locAgrees\"] = None if _rl is None else (_rl == _cons)",
     "_r[\"locAgrees\"] = (_rl == _cons)",
     "test_a_row_with_NO_loc_is_None_not_False"),
    ("control_app.py", "import retro_gate as _rg\n        _cons, _cwhy = _rg.corroborate_location(sess_rows)",
     "import retro_gate as _rg\n        _cons, _cwhy = (None, '')",
     "test_the_compiler_actually_asks"),
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
