#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REG-1686 - A RED-PROOF THAT NEEDS WHAT THIS PC LACKS IS ELSEWHERE, NEVER BLIND.

MEASURED on his ALT 2026-10-01 ~16:45: the census filed test_the_character_builder_is_their_builder BLIND on proofs [9]
and [10] (20 of 22 PROVEN). Both tamper the builder's generator, and the one case that drives the generator skips on a PC
with no local D2R install - the ALT plays through a cloud client - in the clean run AND the tampered one, so the tampered
run stayed green about nothing. That single BLIND record shut every lock on the ALT (reel.route, printer.stream,
vault.sweep_start, frame.release all answered "1 instrument(s) are BLIND"), so the river stopped again.

Driven through the REAL heart2._prove_one / _prove_gate (only the law runs and the host probe are stand-ins):
  1. a proof that declares `"needs"` a capability this PC lacks is ELSEWHERE and its law is never run here;
  2. where the PC has it, the proof is judged exactly as before (it can still go BLIND);
  3. a capability name no probe knows is INVALID - a typo never excuses a proof;
  4. a gate is PROVEN when its other proofs are and the rest are ELSEWHERE; every proof ELSEWHERE is UNPROVABLE here;
     a BLIND among them stays BLIND;
  5. the builder law's [9] and [10] declare the install; the install probe is the ONE rule _pull itself checks.
RED_PROOF below.
"""
import io
import os
import shutil
import sys
import tempfile
import types
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
from console_safe import enable as _console_safe_enable  # noqa: E402  (its red-proofs carry non-ASCII)
_console_safe_enable()
import heart2 as H  # noqa: E402

LINES = []


def _say(*a):
    LINES.append(" ".join(str(x) for x in a))


class _Sandbox(unittest.TestCase):

    def setUp(self):
        del LINES[:]
        root = tempfile.mkdtemp(prefix="elsewhere_")
        self.addCleanup(shutil.rmtree, root, True)
        self.tv = os.path.join(root, "tv")
        os.makedirs(self.tv)
        with io.open(os.path.join(self.tv, "subject.py"), "w", encoding="utf-8") as fh:
            fh.write("ANCHOR = 1\n")
        with io.open(os.path.join(self.tv, "test_law.py"), "w", encoding="utf-8") as fh:
            fh.write("pass\n")
        self.runs = []

    def proof(self, needs=None):
        pr = {"why": "a stand-in", "file": "subject.py", "find": "ANCHOR = 1\n", "replace": "ANCHOR = 2\n",
              "matches": 1}
        if needs is not None:
            pr["needs"] = needs
        return pr

    def judge(self, pr, lacks, tampered_red=True):
        def run_gate(sandbox_tv, filename, timeout=180, extra=(), script=None, widths=None):
            with io.open(os.path.join(sandbox_tv, "subject.py"), encoding="utf-8") as fh:
                tampered = "ANCHOR = 2" in fh.read()
            self.runs.append("tampered" if tampered else "clean")
            if tampered:
                return (not tampered_red), ("Ran 3 tests\nFAILED" if tampered_red else "Ran 3 tests\nOK")
            return True, "Ran 3 tests\nOK"
        probe = {"d2r-install": ("_elsewhere_probe", "have", "the D2R install")}
        sys.modules["_elsewhere_probe"] = types.SimpleNamespace(have=lambda: not lacks)
        self.addCleanup(sys.modules.pop, "_elsewhere_probe", None)
        with mock.patch.object(H, "_run_gate", run_gate), mock.patch.object(H, "PROOF_NEEDS_HOST", probe):
            return H._prove_one(self.tv, "test_law", "test_law.py", pr, 0, _say)


class AProofThatNeedsWhatThisPcLacks(_Sandbox):

    def test_it_is_elsewhere_and_its_law_never_runs_here(self):
        v = self.judge(self.proof("d2r-install"), lacks=True, tampered_red=False)
        self.assertEqual(v, H.ELSEWHERE, "a proof this PC cannot judge was filed %s" % v)
        self.assertEqual(self.runs, [], "the law was run for a proof this PC cannot judge: %r" % self.runs)
        self.assertTrue(any("ELSEWHERE" in l and "the D2R install" in l for l in LINES), LINES)

    def test_where_the_pc_has_it_it_is_judged_as_before(self):
        v = self.judge(self.proof("d2r-install"), lacks=False, tampered_red=True)
        self.assertEqual(v, H.PROVEN)
        self.assertIn("tampered", self.runs)
        v2 = self.judge(self.proof("d2r-install"), lacks=False, tampered_red=False)
        self.assertEqual(v2, H.BLIND, "a declared need softened a real BLIND on a PC that HAS the capability")

    def test_an_undeclared_capability_is_invalid(self):
        v = self.judge(self.proof("d2r-instal"), lacks=True, tampered_red=False)
        self.assertEqual(v, H.INVALID, "a mistyped capability excused a proof")

    def test_a_proof_with_no_need_is_untouched(self):
        v = self.judge(self.proof(), lacks=True, tampered_red=False)
        self.assertEqual(v, H.BLIND, "a proof that declared nothing was excused")


class TheGateCountsWhatWasJudgedHere(unittest.TestCase):

    def gate(self, verdicts):
        with mock.patch.object(H, "_prove_gate_proofs", lambda *a, **k: list(verdicts)), \
                mock.patch.object(H, "_closing_clean", lambda name, v, say: v), \
                mock.patch.object(H, "_PUSH", None):
            return H._prove_gate("sb", "g", "g.py", [{}] * len(verdicts), _say)[0]

    def test_proven_with_the_rest_elsewhere_is_proven(self):
        self.assertEqual(self.gate([H.PROVEN, H.ELSEWHERE, H.PROVEN]), H.PROVEN)

    def test_every_proof_elsewhere_is_unprovable_here(self):
        self.assertEqual(self.gate([H.ELSEWHERE, H.ELSEWHERE]), H.UNPROVABLE,
                         "a gate with nothing judged on this PC was filed PROVEN")

    def test_a_blind_among_them_stays_blind(self):
        self.assertEqual(self.gate([H.BLIND, H.ELSEWHERE]), H.BLIND)


class TheBuilderDeclaresItsInstall(unittest.TestCase):

    def test_the_two_generator_proofs_declare_the_install(self):
        proofs = H.red_proofs_in(os.path.join(HERE, "test_the_character_builder_is_their_builder.py"))
        gen = [i for i, p in enumerate(proofs) if p.get("file") == "char_builder_db.py"
               and "generator" in str(p.get("why"))]
        self.assertGreaterEqual(len(gen), 2, "PREMISE: the generator proofs are not where they were")
        for i in gen:
            self.assertEqual(proofs[i].get("needs"), "d2r-install",
                             "builder proof [%d] tampers the generator but does not declare the install" % i)

    def test_the_install_probe_is_the_one_rule_pull_checks(self):
        import affix_lexicon as AL
        self.assertIn("install_present", AL._pull.__code__.co_names,
                      "_pull checks the install with its own copy of the rule, not install_present")
        self.assertEqual(H.PROOF_NEEDS_HOST["d2r-install"][:2], ("affix_lexicon", "install_present"))


RED_PROOF = [
    {"why": "REG-1686 - a proof this PC cannot judge is run anyway and files BLIND (the ALT's shut river)",
     "file": "heart2.py",
     "find": "        if _lacks:\n            say(\"     %-52s %s — it needs %s, which this PC does not have; it is proven on a PC that does\"\n",
     "replace": "        if False:\n            say(\"     %-52s %s — it needs %s, which this PC does not have; it is proven on a PC that does\"\n",
     "matches": 1},
    {"why": "REG-1686 - a mistyped capability excuses a proof",
     "file": "heart2.py",
     "find": "        if _lacks is None and _words.startswith(\"an undeclared capability\"):\n",
     "replace": "        if False:\n",
     "matches": 1},
    {"why": "REG-1686 - a gate with nothing judged here is filed PROVEN",
     "file": "heart2.py",
     "find": "    if verdicts and all(v == ELSEWHERE for v in verdicts):\n",
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "REG-1686 - _pull keeps its own copy of the install rule",
     "file": "affix_lexicon.py",
     "find": "    if not install_present():\n        return None\n",
     "replace": "    if not (os.path.exists(EXTRACT) and os.path.isdir(os.path.join(D2R, \"Data\"))):\n        return None\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
