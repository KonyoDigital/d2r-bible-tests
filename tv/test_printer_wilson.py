#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guards for the printer's lock — v2570.

⚠ These assert the SHAPE that makes printer_wilson safe and the WIRING that makes the river real.
They do not re-run the sabotages (printer_wilson does that, and run_gates runs it); they pin the
properties a future edit could quietly remove.
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

SRC = os.path.join(HERE, "printer_wilson.py")


class TheHarnessCannotAct(unittest.TestCase):
    """It exercises a DECISION and never an action. Read from its own source, by AST."""

    @staticmethod
    def _src():
        with io.open(SRC, encoding="utf-8") as fh:
            return fh.read()

    def test_it_never_names_a_destructive_call(self):
        # ⚠ NAMES, not substrings of prose: the docstring deliberately QUOTES the words it must
        # not call ("no os.remove, no apply_plan"), so a text search matches the sentence promising
        # safety. Walk the AST and look at CALLS. [[source-reading-guard]]
        tree = ast.parse(self._src())
        banned = {"remove", "unlink", "rmtree", "apply_plan", "_prune_once", "_prune_loop",
                  "_retention_loop", "rmdir"}
        # ⚠ #123 — the ONE exemption: removing a path THIS function minted with tempfile.mkstemp.
        # That is the harness tidying its own scratch file, not acting on his; anything else named
        # here still refuses. [[feedback-fixtures-never-touch-live-data]]
        own_temp = set()
        for fn in ast.walk(tree):
            if not isinstance(fn, ast.FunctionDef):
                continue
            minted = set()
            for a in ast.walk(fn):
                if (isinstance(a, ast.Assign) and isinstance(a.value, ast.Call)
                        and getattr(a.value.func, "attr", "") == "mkstemp"):
                    for t in a.targets:
                        for x in ast.walk(t):
                            if isinstance(x, ast.Name):
                                minted.add(x.id)
            for c in ast.walk(fn):
                if (isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "remove"
                        and c.args and isinstance(c.args[0], ast.Name) and c.args[0].id in minted):
                    own_temp.add(id(c))
        hits = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and id(node) not in own_temp:
                f = node.func
                name = getattr(f, "attr", None) or getattr(f, "id", None)
                if name in banned:
                    hits.append("%s (line %d)" % (name, getattr(node, "lineno", -1)))
        self.assertEqual(hits, [],
                         "printer_wilson calls something that can act: %s. This harness must "
                         "exercise the DECISION and never the action." % hits)

    def test_it_never_writes_the_prune_switch(self):
        """⚠ THIS GUARD CAUGHT ITSELF ON ITS FIRST RUN, with the defect it exists to warn about.

        The first cut was `assertNotIn("TV_AUTO_PRUNE", source)` — and printer_wilson's own
        docstring PROMISES safety by naming what it does not do ("no `TV_AUTO_PRUNE`"), so the
        guard fired on the sentence recording the fix. That is v2565's scar exactly: a negative
        text match on prose that deliberately quotes what it excludes cannot work.

        So it reads CODE. Docstrings are dropped and the remaining string constants and attribute
        names are searched — prose may say the word, executable text may not.
        [[source-reading-guard]]
        """
        tree = ast.parse(self._src())
        docs = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
                body = getattr(node, "body", None) or []
                if body and isinstance(body[0], ast.Expr) and isinstance(
                        getattr(body[0], "value", None), ast.Constant) and isinstance(
                        body[0].value.value, str):
                    docs.add(id(body[0].value))
        hits = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                    and id(node) not in docs and "TV_AUTO_PRUNE" in node.value:
                hits.append("string at line %d" % getattr(node, "lineno", -1))
        self.assertEqual(hits, [],
                         "printer_wilson names the arming switch in EXECUTABLE text (%s). It "
                         "proves a REPORT layer, and a harness that can arm a deleter is a "
                         "different kind of file." % hits)

    def test_it_calls_exactly_one_printer_entry_point(self):
        """⚠⚠ #123 — v3406 added unit checks of the printer's HELPERS and banked them as door evidence.
        The law is now what it always meant: the only PUBLIC printer entry point driven is stream();
        helper calls are private (`_x`); and an attempt that touches a helper is NEVER banked."""
        tree = ast.parse(self._src())
        called = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if getattr(node.func.value, "id", None) == "P":
                    called.add(node.func.attr)
        public = sorted(c for c in called if not c.startswith("_"))
        self.assertEqual(public, ["stream"],
                         "printer_wilson should drive printer.stream() and no other public printer "
                         "entry point; it calls %s" % public)

    def test_an_attempt_on_a_helper_is_never_banked_as_door_evidence(self):
        """DRIVEN: every row's `door` flag is its own AST, and the banker receives door counts only."""
        sys.path.insert(0, os.path.dirname(SRC))
        import printer_wilson as PW
        rep = PW.prove()
        by = dict((name, fn) for name, fn, _w in PW.ATTEMPTS)
        units = [r for r in rep["rows"] if not r["door"]]
        self.assertTrue(units, "premise: no helper-level attempt exists, so this case judges nothing")
        for r in rep["rows"]:
            calls = PW.printer_calls(by[r["attempt"]])
            self.assertEqual(r["door"], calls == {"stream"},
                             "%s is filed %s but calls %r" % (r["attempt"],
                                                              "DOOR" if r["door"] else "UNIT", calls))
        doors = [r for r in rep["rows"] if r["door"]]
        self.assertEqual((rep["n"], rep["k"]),
                         (sum(r["n"] for r in doors), sum(r["k"] for r in doors)),
                         "the banked counts include attempts that never reached the door")
        import self_arming as SA
        got = {}
        real = SA.bank
        SA.bank = lambda *a, **k: got.update(k) or dict(k, lock=a[0], kind=a[1], src=a[2])
        try:
            PW.bank_into_proof_queue(rep)
        finally:
            SA.bank = real
        self.assertEqual(got.get("attacks"), len(doors),
                         "the lock was told %r distinct attacks; %d reached the door"
                         % (got.get("attacks"), len(doors)))


class TheDoorIsShownNeverAssumed(unittest.TestCase):
    """The second eye on v3488 (grok-cli), both findings reproduced before fixing."""

    def _pw(self):
        sys.path.insert(0, os.path.dirname(SRC))
        import printer_wilson as PW
        return PW

    def test_a_helper_handed_the_printer_is_followed(self):
        PW = self._pw()
        by = dict((name, fn) for name, fn, _w in PW.ATTEMPTS)
        for name in ("templates", "routes", "gap"):
            self.assertEqual(PW.printer_calls(by[name]), {"stream"},
                             "%s reaches the door through _station_refused and must SHOW it" % name)

    def test_an_attempt_that_never_touches_the_printer_is_not_a_door(self):
        PW = self._pw()
        self.assertEqual(PW.printer_calls(PW._refused), set())
        rep_rows = []
        real = PW.ATTEMPTS
        PW.ATTEMPTS = (("no-printer", PW._refused, "never touches P"),)
        try:
            import contextlib
            with contextlib.redirect_stdout(io.StringIO()):
                rep = PW.prove()
        finally:
            PW.ATTEMPTS = real
        self.assertFalse(rep["rows"][0]["door"], "an attempt with no printer call was filed DOOR")
        self.assertEqual(rep["doorAttacks"], 0)

    def test_a_leaking_unit_check_is_LEAKS_even_with_no_door_attempt(self):
        PW = self._pw()
        real = PW.ATTEMPTS

        def _leaks(P):
            P._tombstone_census(None)
            return 1, 0
        PW.ATTEMPTS = (("unit-leak", _leaks, "a helper check that leaks"),)
        try:
            import contextlib
            with contextlib.redirect_stdout(io.StringIO()):
                rep = PW.prove()
        finally:
            PW.ATTEMPTS = real
        self.assertFalse(rep["ok"])
        self.assertEqual(rep["state"], "LEAKS", "a unit leak with n == 0 read %r" % rep["state"])
        self.assertIn("0 of 1 unit", rep["why"])


class TheRiverIsWiredIntoTheDeleter(unittest.TestCase):
    """v2570 — his ask: "build the printer lock and wire the whole river"."""

    def test_the_printer_lock_is_declared(self):
        import self_arming as SA
        self.assertIn("printer.stream", SA.LOCKS,
                      "the printer walks every reel he owns and had no lock at all; fourteen "
                      "locks were declared and not one named the printer, the river or selection")

    def test_the_deleter_lock_is_RETIRED_and_its_evidence_STILL_READS(self):
        """⚠⚠ v3347 — HIS RULING, 2026-09-19: *"leave it off and surgically remove it we need
        pruning"*.

        This case asserted that `prune.arm.after` contained `printer.stream` — his order, "printer
        + reels -> theatre + shelf -> routing -> the deleter". That ordering rule was encoded ONLY
        here and in the lock's own prerequisite list, so retiring the lock removes the only place
        code enforced that the deleter waits for the river. **That is the intended effect of his
        ruling, not an oversight**, and `_PRUNE_SAFE_TO_RUN` (53 sites) is untouched and is the
        actual safety.

        What replaces it is the half that was never his to waive. MEASURED when the ceremony was
        cut: his ledger holds **19 rows** banked by `prune_wilson` against `prune.arm`, and simply
        dropping the PROVES declaration made `_rows()` return None — failing **all nine surviving
        locks CLOSED** on "an unreadable proof queue fails CLOSED". Retired means READABLE, NEVER
        BANKABLE. [[manual-tally-is-witness]] — once witnessed, never un-witnessed."""
        import self_arming as SA
        self.assertNotIn(
            "prune.arm", SA.LOCKS,
            "prune.arm is a live lock again. His ruling was to REMOVE the ceremony, so gating the "
            "deleter on Wilson evidence once more is a decision of his, not a restoration.")
        self.assertIn(
            "prune.arm", SA.RETIRED_LOCKS,
            "prune.arm is neither a live lock nor a declared retirement, so the rows his ledger "
            "already holds for it are accounted for by nothing and the next reader must guess.")
        self.assertIn(
            "prune.arm", SA.PROVES.get("prune_wilson") or (),
            "the retired pair is no longer declared in PROVES. That is not a tidy-up: _row_fault "
            "rejects those 19 rows, _rows() returns None, and EVERY lock fails CLOSED.")
        _rows, _fault = SA._rows()
        self.assertFalse(
            _fault,
            "the ledger no longer reads: %s. A retirement that costs his banked evidence is not a "
            "surgical removal." % _fault)

    def test_an_unproven_printer_actually_holds_the_deleter(self):
        """BEHAVIOURAL, and it is the point: the chain must BITE, not merely be declared."""
        import self_arming as SA
        all_rows = SA._rows()[0] or []
        rows = [r for r in all_rows if r.get("lock") != "printer.stream"]
        self.assertEqual(SA.score("printer.stream", rows)["state"], SA.UNPROVEN)
        # ⚠⚠ THE LAW IS "UNAFFECTED", AND THIS USED TO PIN "OPEN" — a DATUM, not a rule.
        # It asserted `prune.arm` is OPEN/HARDENED after the printer's rows are removed, as a way
        # of showing the hold comes from the CHAIN and not from the lock's own score. That worked
        # only while prune.arm happened to be open, and it went red the moment the deciding figure
        # became `wilsonByAttack` (his ruling: n inflated by repetition is fake confluence) and
        # prune.arm correctly dropped to LOCKED on 0.5655 against its 0.839 bar — a change with
        # nothing whatever to do with the printer.
        # A bar moved and a test pinned to today's reading went red for a reason it was not about.
        # [[regression-guard]] §4 — PIN THE LAW, NOT THE NUMBER.
        #
        # The law, stated so it survives any future state: removing printer.stream's evidence must
        # not move prune.arm's OWN score, whatever that score happens to be.
        before = SA.score("prune.arm", all_rows)
        after = SA.score("prune.arm", rows)
        self.assertEqual(after["state"], before["state"],
                         "prune.arm's OWN score changed when printer.stream's evidence was removed "
                         "(%s -> %s). The hold must come from the CHAIN; conflating the two hides "
                         "which one is failing." % (before["state"], after["state"]))
        self.assertEqual(after.get("wilson"), before.get("wilson"),
                         "the printer's rows moved prune.arm's Wilson bound — evidence about one "
                         "surface is being counted as evidence about another")

    def test_the_fixture_shelf_walks_even_when_the_printer_lock_is_shut(self):
        """#233 — second eye on e24dda62: with printer.stream LOCKED (a runner with no proof queue),
        stream() answered [] before reading the patched river, so every shape law judged an empty
        walk. The shelf opens that one lock for its own walk; two reels in means two rows out."""
        import printer as P
        import printer_wilson as PW
        import self_arming as SA
        real = SA.may_on_merit
        try:
            SA.may_on_merit = lambda lock, *a, **k: (False, "forced shut for this case")
            self.assertEqual(P.stream().get("rows") or [], [],
                             "premise: with the lock shut, stream() must answer nothing")
            rows = PW._fixture_shelf(P.stream).get("rows") or []
            # on his Mac the other owners add his real reels to the walk; on a clean runner there
            # are none. The law is that the TWO FIXTURE reels are walked, whatever else is.
            walked = {r.get("reel") for r in rows}
            self.assertTrue(set(PW._FIXTURE_REELS) <= walked,
                            "behind a shut lock the fixture shelf walked %d row(s) and not its own "
                            "reels %r" % (len(rows), list(PW._FIXTURE_REELS)))
            self.assertEqual(SA.may_on_merit.__name__, "<lambda>", "the shelf did not put the lock back")
        finally:
            SA.may_on_merit = real

    def test_printer_wilson_proves_only_the_printer(self):
        import self_arming as SA
        self.assertEqual(SA.PROVES.get("printer_wilson"), ("printer.stream",),
                         "an evidence source must prove exactly what it looked at — evidence "
                         "about one surface is not evidence about another")


RED_PROOF = [
    {
        "why": "#233 - the fixture shelf walks behind a shut printer lock again: stream() answers [] and every shape law files an empty walk as a leak",
        "file": "printer_wilson.py",
        "find": "    with _Patch(RR, \"river\", lambda *a, **k: fake), _Patch(SA, \"may_on_merit\", _open_for_the_shelf):\n",
        "replace": "    with _Patch(RR, \"river\", lambda *a, **k: fake):\n",
        "matches": 1,
    },
    {
        "why": "Puts the retired ceremony back. v3347 removed prune.arm from LOCKS by his ruling - "
               "'leave it off and surgically remove it we need pruning' - and this law is what "
               "keeps that removal honest from the printer's side. ⚠ THE PREVIOUS SABOTAGE HERE "
               "WENT INVALID AT 0 MATCHES AND THE PUSH GATE CAUGHT IT: it anchored on prune.arm's "
               "own `after` list, which went with the lock, so it changed no byte and reported "
               "coverage it did not provide. The sabotage was wrong, not the law. "
               "[[sabotage-is-usually-the-wrong-one]] This one restores the lock at a DIFFERENT "
               "byte from the three proofs in test_a_retired_lock_keeps_its_testimony, so the two "
               "laws are not both riding one edit. MEASURED: untampered -> Ran 7 tests, OK; "
               "tampered -> test_the_deleter_lock_is_RETIRED_and_its_evidence_STILL_READS fails on "
               "assertNotIn(prune.arm, LOCKS).",
        "file": "tv/self_arming.py",
        "find": "RETIRED_LOCKS = {",
        "replace": ('LOCKS["prune.arm"] = dict(surface="THE RIVER", acts="deletes footage",\n'
                    '                          destructive=True, bar=0.839, kinds_bar=1.8,\n'
                    '                          after=["printer.stream"])\n'
                    'RETIRED_LOCKS = {'),
        "matches": 1,
    },
    {
        "why": "#123 - the banker counts every row again: helper-level unit checks are reported to the printer.stream lock as distinct attacks on the door",
        "file": "printer_wilson.py",
        "find": "                   attacks=int(rep.get(\"doorAttacks\") or 0),   # #123 — door attempts only",
        "replace": "                   attacks=len(rep.get(\"rows\") or []),",
        "matches": 1
    },
    {
        "why": "#123 - every attempt filed as DOOR: a check on a helper banks as evidence about a door it never touched",
        "file": "printer_wilson.py",
        # re-anchored for v3488's second eye: the door test is `== {"stream"}` now, same property
        "find": "        door = calls == {\"stream\"}      # ⚠ the empty set is NOT a door: see _printer_calls",
        "replace": "        door = True",
        "matches": 1
    },
    {
        "why": "v3488 second eye [0] - the empty set counts as a door again: an attempt that never touches the printer banks as door evidence",
        "file": "printer_wilson.py",
        "find": "        door = calls == {\"stream\"}      # ⚠ the empty set is NOT a door: see _printer_calls",
        "replace": "        door = calls is not None and calls <= {\"stream\"}",
        "matches": 1
    },
    {
        "why": "v3488 second eye [1] - an empty door outranks a leak again: a leaking unit check reads UNPROVEN, 'nothing attempted'",
        "file": "printer_wilson.py",
        "find": "            \"state\": (\"LEAKS\" if leaks else (\"UNPROVEN\" if n == 0 else \"PROVEN\")),",
        "replace": "            \"state\": (\"UNPROVEN\" if n == 0 else (\"LEAKS\" if leaks else \"PROVEN\")),",
        "matches": 1
    },
]


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=1)
