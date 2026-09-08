#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""♥♥ HEART 2.0 — the law that the heart can see whether its own instruments still work.

**MEASURED 2026-09-08, and it is the entire argument for this layer.** The heart was GREEN while
12 of 238 gates were red, 8 of those were blind instruments, and the full set had been failing in
CI since 2026-09-07 06:12 — 28 of the last 40 runs. Every check the heart made was working.
Nothing was checking the checkers, so nobody knew. Three of the eight were laws that had silently
STOPPED MEASURING what they claimed while staying green.

    heart v1   is the SYSTEM healthy?   — lanes, routes, stores, the console
    heart v2   are my own INSTRUMENTS   — the gates and locks themselves
               still able to go red?

★ THE NUMBER THAT SETTLES "isn't it basically built?": 246 gates, and before this arc **0** had an
executable red-proof. Each was proven red exactly once, by hand, in a shell, and that proof
survives only as prose in a docstring. It cannot be re-run — so the number of gates that can still
go red was UNKNOWN. Not zero, not fine. Unknown. [[unknown-stays-unknown]]

THIS LAW GUARDS THE LAYER, NOT THE NUMBER. It does not assert how many proofs exist — that is a
ratchet's job and it would fail every honest commit. It asserts that the machinery is joined and
cannot quietly stop working:

  · the census counts something (a 0 here means the parser broke, not that there are no gates —
    which is exactly what happened: the first cut read `g.cmd`, the field is `g.argv`, and it
    printed "0 gates / 0.0%" as though it were a measurement) [[zero-needs-a-denominator]]
  · every declared RED_PROOF is well formed, names a file that exists, and its `find` occurs the
    exact number of times it claims — a tamper that matches nothing proves nothing, and a green
    sabotage is usually the sabotage's fault [[sabotage-is-usually-the-wrong-one]]
  · the heart actually CARRIES the result, so the proving loop is not plumbing with no tap
  · and it proposes rather than repairs — a tool that edits its own guards can talk itself into
    anything [[achilles-self-carving-system]]
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

import heart2  # noqa: E402

APP = os.path.join(HERE, "control_app.py")


def _app():
    with io.open(APP, encoding="utf-8") as fh:
        return fh.read()


class TestHeartSeesItsInstruments(unittest.TestCase):

    def test_the_census_counts_something(self):
        """THE INSTRUMENT FIRST. A 0 here is a broken parser wearing the clothes of a measurement —
        which is precisely what shipped for one run of this file."""
        gates = heart2.gate_files()
        self.assertGreater(len(gates), 100,
                           "the census found %d gate(s). run_gates registers hundreds, so this is "
                           "the parser failing, not a clean tree" % len(gates))
        print("\n   census: %d gate(s) with a python file" % len(gates))

    def test_every_declared_red_proof_is_well_formed(self):
        bad = []
        checked = 0
        for name, fn in heart2.gate_files():
            proofs = heart2.red_proofs_in(fn)
            if not proofs:
                continue
            for i, pr in enumerate(proofs):
                checked += 1
                label = "%s[%d]" % (name, i)
                if not isinstance(pr, dict):
                    bad.append("%s is not a dict" % label)
                    continue
                for k in ("why", "file", "find", "replace", "matches"):
                    if k not in pr:
                        bad.append("%s has no %r" % (label, k))
                tgt = os.path.join(HERE, str(pr.get("file") or ""))
                if not os.path.isfile(tgt):
                    bad.append("%s names a file that does not exist: %r" % (label, pr.get("file")))
                    continue
                with io.open(tgt, encoding="utf-8") as fh:
                    src = fh.read()
                got = src.count(str(pr.get("find") or ""))
                want = int(pr.get("matches") or 0)
                if got != want:
                    bad.append("%s: the tamper matches %d time(s), it declares %d — a sabotage "
                               "that changes nothing proves nothing" % (label, got, want))
                if str(pr.get("find")) == str(pr.get("replace")):
                    bad.append("%s: find and replace are identical — it tampers with nothing"
                               % label)
        self.assertEqual(bad, [], "malformed red-proofs:\n  " + "\n  ".join(bad))
        print("   %d red-proof(s) declared, all well formed" % checked)

    def test_the_heart_carries_the_instrument_census(self):
        """The proving loop and the heart must be JOINED. Two halves each built right and never
        joined is this repo's single most repeated defect."""
        src = _app()
        self.assertIn("def _heart2_census(", src,
                      "control_app.py has no instrument census to report")
        self.assertIn('"instruments": _heart2_census()', src,
                      "heart_state() does not carry the instruments — the proving loop would "
                      "measure and nothing would ever read it")
        import control_app as CA
        got = CA._heart2_census()
        self.assertIsInstance(got, dict)
        for k in ("state", "why"):
            self.assertIn(k, got)
        self.assertIn(got["state"], ("WATCHED", "DARK", "UNKNOWN"),
                      "the census reported an unknown state word: %r" % got.get("state"))
        print("   heart carries: %s — %s" % (got.get("state"), str(got.get("why"))[:70]))

    def test_an_absent_state_file_reads_UNKNOWN_not_clean(self):
        """The commonest lie a supervision layer tells is that never-measured means fine."""
        import control_app as CA
        real = heart2.STATE
        moved = real + ".lawtest"
        had = os.path.exists(real)
        if had:
            os.rename(real, moved)
        try:
            got = CA._heart2_census()
            self.assertEqual(got.get("state"), "UNKNOWN",
                             "with no state file the heart reported %r — never-measured must "
                             "never read as healthy" % got.get("state"))
            self.assertIsNone(got.get("proved"),
                              "an absent measurement produced a number: %r" % got.get("proved"))
        finally:
            if had:
                os.rename(moved, real)

    def test_it_proposes_and_never_edits_a_guard(self):
        """Achilles' reason, verbatim: 'In one night working this tree I introduced three defects
        while fixing others, and I can read a diff.' A repairer of its own instruments is a tool
        that can talk itself into anything."""
        with io.open(os.path.join(HERE, "heart2.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        writes = []
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "open":
                mode = ""
                if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                    mode = str(n.args[1].value)
                for kw in n.keywords:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                        mode = str(kw.value.value)
                if "w" in mode or "a" in mode:
                    writes.append(n.lineno)
        # every write must be to the state file, the proposals file, or inside the sandbox
        with io.open(os.path.join(HERE, "heart2.py"), encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        for ln in writes:
            ctx = "\n".join(lines[max(0, ln - 6):ln + 1])
            self.assertTrue(("STATE" in ctx) or ("PROPOSALS" in ctx) or ("tgt" in ctx),
                            "heart2.py writes at line %d to something that is neither its state "
                            "file, its proposals file, nor a sandbox target:\n%s" % (ln, ctx))


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
# The law that demands re-runnable proofs carries one. Cutting the join is the defect: the proving
# loop would keep measuring perfectly and the heart would never carry a word of it.
RED_PROOF = [{
    "why": "unjoining the census from heart_state makes the whole proving loop plumbing with no tap",
    "file": "control_app.py",
    "find": '        "instruments": _heart2_census(),',
    "replace": '        "instrumentsUNJOINED": _heart2_census(),',
    "matches": 1,
}]


if __name__ == "__main__":
    unittest.main(verbosity=2)
