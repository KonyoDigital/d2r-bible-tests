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


def _stmt_and_block(callee):
    """-> the source of the statement calling `callee` PLUS the block that follows it, or "".

    ⚠ A REAL BOUNDARY, PARSED. A fixed-size window is a guess about how far a subject reaches, and
    the subject grows every time somebody documents it — which is how this law came to read 700 of
    the 1,856 chars it is about. ast knows where the statement ends; nothing else does.

    ⚠ IT RETURNS "" ONLY WHEN IT GENUINELY CANNOT BOUND THE REGION, and every caller must treat
    that as UNKNOWN and fail, never as an empty region that satisfies a negative assertion. An
    empty string passes `assertNotIn` for anything at all — that is the same silence this helper
    exists to remove, one level up. [[unknown-stays-unknown]]
    """
    import ast as _ast
    import re as _re
    with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
        raw = fh.read()
    try:
        tree = _ast.parse(raw)
    except SyntaxError:
        return ""
    # ⚠⚠ v3351 — AMBIGUITY IS REFUSED, NOT RESOLVED BY ARRIVAL ORDER. The cross-family eye found
    # both of these on v3350, latent: `ast.walk` yields DFS order, NOT source order, so taking the
    # FIRST matching Call picks an arbitrary site the moment `callee` is called twice — and the
    # window would then describe a different call than the one under test, handing a NEGATIVE
    # assertion a clean region and shipping the bug it exists to catch. Measured when it was
    # written: corroborate_location has exactly ONE call site, so nothing was live; the second
    # call added by anybody would have made it live and silent.
    # Refusing beats guessing here: "" makes the caller fail loudly and say which name is
    # ambiguous, which is the state this helper already documents for every other failure.
    # [[unknown-stays-unknown]] [[source-reading-guard]] §2 — anchor on something UNIQUE.
    hits = [n for n in _ast.walk(tree)
            if isinstance(n, _ast.Call) and getattr(n.func, "attr", "") == callee]
    if len(hits) != 1:
        return ""
    hit = hits[0]
    # ⚠ THE SAME RULE ONE LEVEL DOWN. A statement belongs to exactly one body, but a ONE-LINE
    # construct (`if cond: call()`) puts the `if` and the call on the same lineno, so two bodies
    # can match and the first one visited wins — truncating before the assignment or swallowing
    # unrelated later code. Collect every candidate and refuse unless there is exactly one.
    cands = []
    for parent in _ast.walk(tree):
        body = getattr(parent, "body", None)
        if not isinstance(body, list):
            continue
        for k, st in enumerate(body):
            if getattr(st, "lineno", None) == hit.lineno:
                cands.append((body, k, st))
    if len(cands) != 1:
        return ""
    for body, k, st in cands:
        if True:
            end = getattr(st, "end_lineno", st.lineno)
            if k + 1 < len(body):
                end = max(end, getattr(body[k + 1], "end_lineno", end))
            # ⚠⚠ SLICE THE RAW SOURCE, NEVER THE STRIPPED ONE. My first cut sliced what `_src()`
            # returns, on the stated assumption that blanking comment LINES preserves numbering.
            # MEASURED: it does not. `_src()` uses `^\s*#.*$` and `\s` MATCHES NEWLINES, so a run
            # of blank lines before a comment is absorbed into one space — control_app.py goes
            # 35,484 lines to 35,172, losing 312. Every line number past the first comment is off,
            # and the window silently lands on unrelated code: the first run of this helper handed
            # back a slice of gameplay-filter logic and the law failed on an innocent region.
            # ast's line numbers describe the RAW file, so the slice must too.
            seg = "\n".join(raw.split("\n")[st.lineno - 1:end])
            # comments out of the SLICE, with a pattern that cannot cross a line boundary
            return _re.sub(r"(?m)^[ \t]*#.*$", " ", seg)
    return ""


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
        # ⚠⚠ v3350 — THE END IS THE STATEMENT'S OWN END, NOT A BYTE COUNT. This read
        # `src[i:i + 700]` under a NEGATIVE assertion. MEASURED, and the direction is the OPPOSITE
        # of what I first wrote: the real region — the call plus the `if _cons:` block it guards,
        # control_app.py 8136-8162 — is 1,856 raw chars but only 499 once comments are stripped,
        # which is what this law reads. So 700 did not run SHORT of the subject, it ran 200 chars
        # PAST it, into code the law says nothing about. Either direction is the same defect: a
        # byte count is a guess about where a subject ends, and under assertNotIn an over-reach
        # can fail on innocent neighbouring code while an under-reach reports an absence it never
        # looked for. My 38%-of-its-subject claim counted comments the reader never sees.
        # ⚠ ASK THE COMPILER, NOT THE TEXT. ast gives the exact end_lineno of the statement and of
        # the block that follows it, and `_src()` substitutes comment LINES with a space rather
        # than deleting them, so line numbers survive the strip and the mapping is exact.
        # [[source-reading-guard]] §1, §3
        window = _stmt_and_block("corroborate_location")
        self.assertTrue(window, "could not bound the corroboration statement from the parse tree, "
                                "so there is no region to judge — refusing to report an absence "
                                "measured over nothing")
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


class TheContradictionReachesASurface(unittest.TestCase):
    """⚠⚠ THE FLAG WAS COMPUTED ON EVERY ROW AND READ BY NOTHING.

    v3214 wired `corroborate_location` correctly and attached `locSession` / `locAgrees` /
    `locWhy` to every register row. A cross-family review then asked the only question that
    mattered: who READS them. Answer — nobody. No UI, no API consumer, no Python caller; a grep
    returned the writer, its own comment, and the gate's `why` text. The join had moved one hop
    downstream instead of closing, which is the same shape as the no-caller problem it was built
    to fix. [[the-unjoined-end]] [[plumbing-with-no-tap]]

    `_kai_forensics_project` is the register's ONLY reader, so that is where the flag surfaces.
    """

    def _reg(self, minority_loc):
        rows = [
            {"lane": "deep", "ts": 1000, "frameId": "f0",
             "names": [MINORITY], "names_loc": {MINORITY: minority_loc}},
            {"lane": "deep", "ts": 1001, "frameId": "f1",
             "names": [A], "names_loc": {A: "stash"}},
            {"lane": "deep", "ts": 1002, "frameId": "f2",
             "names": [B], "names_loc": {B: "stash"}},
        ]
        return ca._kai_compile_register(rows)

    def test_a_contradicted_read_is_counted_where_a_human_can_see_it(self):
        reg = self._reg("floor")
        proj = ca._kai_forensics_project({"sid": "s_t", "register": reg, "routing": []})
        s = (proj or {}).get("summary") or {}
        self.assertEqual(1, s.get("locContested"),
                         "the read placing an item somewhere its own session contradicts never "
                         "reached the forensic record — the flag is computed and unread again")
        self.assertEqual(3, s.get("locChecked"),
                         "the denominator is wrong, so 'contested' has no scale")

    def test_an_agreeing_session_contests_nothing(self):
        reg = self._reg("stash")
        proj = ca._kai_forensics_project({"sid": "s_t", "register": reg, "routing": []})
        s = (proj or {}).get("summary") or {}
        self.assertEqual(0, s.get("locContested"),
                         "a unanimous session is reporting a contradiction — that is an accusation "
                         "out of thin air")

    def test_silence_is_not_counted_as_disagreement(self):
        """⚠ None means nobody said. Counting it would turn silence into an accusation."""
        rows = [{"lane": "deep", "ts": 1000, "frameId": "f0",
                 "names": [MINORITY], "names_loc": {}}]
        proj = ca._kai_forensics_project(
            {"sid": "s_t", "register": ca._kai_compile_register(rows), "routing": []})
        s = (proj or {}).get("summary") or {}
        self.assertEqual(0, s.get("locContested"),
                         "a session where nobody stated a location is reporting contradictions")
        self.assertEqual(0, s.get("locChecked"),
                         "rows nobody could grade are being counted as graded, which gives "
                         "'0 contested' a denominator it did not earn")

    def test_the_projection_carries_the_reason_not_just_the_verdict(self):
        reg = self._reg("floor")
        proj = ca._kai_forensics_project({"sid": "s_t", "register": reg, "routing": []})
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        i = src.find('reg[nm.lower()] = {')
        self.assertGreater(i, 0, "the forensics projection no longer builds its register map")
        self.assertIn("locWhy", src[i:i + 700],
                      "the projection carries the verdict without the sentence that explains it, "
                      "so a reader sees a flag and cannot learn what split the session")


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
