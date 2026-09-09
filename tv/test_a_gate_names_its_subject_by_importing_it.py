# -*- coding: utf-8 -*-
"""#52 — A GATE THAT IMPORTS ITS SUBJECT HAS NAMED IT, AND THE DERIVER NOW HEARS THAT.

`heart2_candidates.target_files` resolved a gate's subject only from filename string literals
(`"control_app.py"`). MEASURED 2026-09-09: that left **94 of the 238 unproven gates with no
resolvable subject at all** — the single largest refusal bucket — and **every one of those 94
imports a local module**. A gate that says `import reel_router as RR` and then asserts on RR's
behaviour has named its subject perfectly well; it just does not spell it with a `.py`.

After resolving from imports too: `no-target-file` **94 -> 5**, derivable **78 -> 104**.

★ AND THE TRAP THAT MAKES THIS WORSE THAN NO RESOLUTION IF GOT WRONG. **95% of gates import
`console_safe`** — the stdout encoding helper. Resolving a subject to it would derive a tamper
against `console_safe.py`; that tamper WOULD turn the gate red; and the proof would be recorded as
coverage while demonstrating nothing about the law, because every gate importing it goes red
together. A proof that reddens for a reason unrelated to its own subject is the most convincing
kind of green that means nothing. [[feedback-blind-fixture-green-gate]]

So infrastructure is EXCLUDED, and the threshold is COMPUTED rather than hardcoded — measured over
264 gates the distribution is `console_safe` 95%, then a cliff to `control_app` 21% and down, so
`INFRA_SHARE = 0.25` sits in the gap. A module that becomes ubiquitous later is excluded without
anyone noticing it did. [[zero-needs-a-denominator]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import heart2_candidates as HC  # noqa: E402


class TheSubjectIsResolvedFromImports(unittest.TestCase):

    def test_a_gate_that_only_imports_its_subject_resolves(self):
        import ast
        src = ("import os\nimport reel_router as RR\n"
               "def test_x():\n    assert RR.STATIONS\n")
        got = HC.target_files(ast.parse(src), HERE)
        self.assertTrue(any(os.path.basename(p) == "reel_router.py" for p in got),
                        "a gate whose only mention of its subject is `import reel_router` resolves "
                        "to nothing, which is the 94-gate refusal bucket: %s"
                        % [os.path.basename(p) for p in got])

    def test_a_filename_literal_still_resolves(self):
        """The older rule must not be traded away for the new one."""
        import ast
        src = 'def test_x():\n    open("control_app.py").read()\n'
        got = HC.target_files(ast.parse(src), HERE)
        self.assertTrue(any(os.path.basename(p) == "control_app.py" for p in got),
                        "filename resolution regressed: %s" % [os.path.basename(p) for p in got])

    def test_a_stdlib_import_resolves_to_nothing(self):
        import ast
        got = HC.target_files(ast.parse("import os\nimport json\nimport unittest\n"), HERE)
        self.assertEqual([], got,
                         "stdlib imports resolved to files: %s" % [os.path.basename(p) for p in got])


class InfrastructureIsNotASubject(unittest.TestCase):

    def test_the_ubiquitous_import_is_excluded(self):
        """★ The whole reason this can be worse than no resolution."""
        infra = HC.infrastructure(HERE)
        self.assertIn("console_safe", infra,
                      "console_safe is imported by ~95%% of gates and is NOT excluded, so a gate's "
                      "subject can resolve to it. A tamper there reddens every gate that imports "
                      "it — coverage recorded, nothing proven. Excluded set: %s" % sorted(infra))

    def test_importing_only_infrastructure_resolves_to_nothing(self):
        import ast
        src = "from console_safe import enable\nenable()\ndef test_x():\n    assert True\n"
        got = HC.target_files(ast.parse(src), HERE)
        self.assertEqual([], got,
                         "a gate that imports ONLY infrastructure got a subject anyway: %s"
                         % [os.path.basename(p) for p in got])

    def test_a_real_subject_is_not_swept_up_as_infrastructure(self):
        """The exclusion must not be so wide that it eats the subjects. [[zero-needs-a-denominator]]"""
        infra = HC.infrastructure(HERE)
        for real in ("reel_router", "control_app", "reel_retention", "self_arming"):
            self.assertNotIn(real, infra,
                             "%r was classified as infrastructure. control_app is the widest real "
                             "subject at ~21%% and the threshold is %.2f — if it is being swept up, "
                             "the threshold has drifted into the subjects."
                             % (real, HC.INFRA_SHARE))

    def test_the_threshold_sits_in_the_measured_gap(self):
        self.assertGreater(HC.INFRA_SHARE, 0.21,
                           "the threshold is at or below control_app's ~21%% share, so real "
                           "subjects are being excluded")
        self.assertLess(HC.INFRA_SHARE, 0.95,
                        "the threshold is above console_safe's ~95%% share, so the one module that "
                        "must be excluded is not")

    def test_a_tiny_corpus_excludes_nothing(self):
        """A share measured over 3 files is noise, not a finding."""
        import tempfile
        d = tempfile.mkdtemp(prefix="infra-")
        try:
            io.open(os.path.join(d, "console_safe.py"), "w").write("def enable(): pass\n")
            for i in range(3):
                io.open(os.path.join(d, "test_%d.py" % i), "w").write("import console_safe\n")
            self.assertEqual(set(), HC.infrastructure(d),
                             "a 3-file corpus produced an infrastructure verdict; below a real "
                             "denominator the share is noise and nothing should be excluded")
        finally:
            import shutil
            shutil.rmtree(d, ignore_errors=True)


class TheGateIsStillNotItsOwnSubject(unittest.TestCase):
    """The pre-existing rule that a gate may not tamper ITSELF must survive the widening."""

    def test_importing_yourself_is_not_a_subject(self):
        src = io.open(os.path.join(HERE, "heart2_candidates.py"), encoding="utf-8").read()
        self.assertIn("os.path.basename(t) != _self", src,
                      "the self-exclusion is gone — a gate could now derive a tamper against its "
                      "own fixture data, which reddens it and proves nothing")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "dropping the infrastructure exclusion lets a subject resolve to console_safe, "
               "whose tamper reddens every gate that imports it — coverage recorded, nothing proven",
        "file": "heart2_candidates.py",
        "find": "    infra = set() if total < 20 else {m for m, k in counts.items() if k > total * INFRA_SHARE}",
        "replace": "    infra = set()",
        "matches": 1,
    },
    {
        "why": "removing import resolution restores the 94-gate no-target-file bucket, the largest "
               "single reason the suite cannot prove itself",
        "file": "heart2_candidates.py",
        "find": "        if os.path.isfile(os.path.join(here, m + \".py\")):\n            names.append(m + \".py\")",
        "replace": "        if False:\n            names.append(m + \".py\")",
        "matches": 1,
    },
    {
        "why": "a threshold below control_app's measured 21% share sweeps real subjects into the "
               "infrastructure set and silently shrinks what can ever be proven",
        "file": "heart2_candidates.py",
        "find": "INFRA_SHARE = 0.25",
        "replace": "INFRA_SHARE = 0.05",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
