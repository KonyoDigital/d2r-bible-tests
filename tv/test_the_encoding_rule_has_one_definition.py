# -*- coding: utf-8 -*-
"""v3293 — THE ENCODING RULE IS ONE DEFINITION, AND IT ANSWERS IN A SECOND.

A test I wrote this session printed non-ASCII and never called `console_safe.enable()`. On his
cp1255 Windows console that crashes WHILE REPORTING a failure, so a clean tree exits non-zero for a
reason that has nothing to do with what was being checked.

⚠ THE RULE WAS NEVER THE PROBLEM — IT WORKED. It refused mine, and three files in tv/ carry
comments saying it refused them too on their first run (lane_census.py:474,
rung_accounting_wilson.py:603, render_check.py:55). The defect was WHEN you learn: it lived inside
test_control, which runs at push time after ~500s of suite. That is the most expensive possible
moment to discover a missing one-line import.

So the rule moved to `console_safe.audit()` — beside the `enable()` it tells you to call — and:

    tv/console_safe.py          the definition, plus a CLI that answers in under a second
    tv/test_control.py          calls audit() instead of keeping a second copy of the loop
    hooks/pre-push              runs the CLI EARLY, before the expensive gates

One definition, three callers. A second copy of a rule is how two rules begin to disagree, and
this file exists to make that impossible rather than merely unlikely. [[copy-drift]]
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import console_safe  # noqa: E402


class TestTheEncodingRuleHasOneDefinition(unittest.TestCase):
    def test_the_rule_lives_in_console_safe(self):
        self.assertTrue(callable(getattr(console_safe, "audit", None)),
                        "console_safe.audit() is the single definition and it is gone")
        self.assertTrue(callable(getattr(console_safe, "scripts", None)),
                        "the file list must be shared too, or the suite and the CLI can disagree "
                        "about WHICH scripts the rule covers")

    def test_the_suite_calls_it_instead_of_keeping_a_copy(self):
        src = io.open(os.path.join(ROOT, "tv", "test_control.py"), encoding="utf-8").read()
        self.assertIn("console_safe.audit(self.REPO)", src,
                      "test_control kept its own loop, so there are two rules that can drift")

    def test_it_CATCHES_an_unsafe_script_and_spares_a_safe_one(self):
        """Behavioural, on fixtures — a rule that only ever returns [] passes every source law."""
        tmp = tempfile.mkdtemp(prefix="enc-audit-")
        try:
            tv = os.path.join(tmp, "tv")
            os.makedirs(tv)
            # prints non-ASCII from an entry point, never made safe -> MUST be caught
            io.open(os.path.join(tv, "bad_cli.py"), "w", encoding="utf-8").write(
                u'if __name__ == "__main__":\n    print("⚠ warning")\n')
            # the same, but it imports console_safe -> exempt
            io.open(os.path.join(tv, "good_cli.py"), "w", encoding="utf-8").write(
                u'from console_safe import enable\nif __name__ == "__main__":\n'
                u'    print("⚠ warning")\n')
            # pure ASCII entry point -> cannot hit this at all
            io.open(os.path.join(tv, "ascii_cli.py"), "w", encoding="utf-8").write(
                u'if __name__ == "__main__":\n    print("plain")\n')
            # an importable module with non-ASCII and no __main__ -> not an entry point
            io.open(os.path.join(tv, "just_a_module.py"), "w", encoding="utf-8").write(
                u'X = "⚠"\n')
            bad = console_safe.audit(tmp)
            self.assertIn(os.path.join("tv", "bad_cli.py"), bad,
                          "an entry point printing non-ASCII with no enable() was NOT caught")
            for spared in ("good_cli.py", "ascii_cli.py", "just_a_module.py"):
                self.assertNotIn(os.path.join("tv", spared), bad,
                                 "%s was flagged and should not be - a rule that flags everything "
                                 "is as useless as one that flags nothing" % spared)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_CLI_exits_non_zero_when_something_is_unsafe(self):
        """The hook reads the exit code, so the verdict must be RETURNED, not only printed.

        ⚠ THIS TEST WAS WEAK AND THE PROVER SAID SO. Its first cut only ran the CLI against the
        real tree — which is CLEAN — so flipping `exit(1)` to `exit(0)` changed nothing it could
        see, and the red-proof came back BLIND at a match count of 1. A correct match count with a
        green law means the LAW is weak, not the sabotage. It now exercises the FAILING path on a
        fixture, which is the only way the exit code is ever observed going non-zero.
        """
        tmp = tempfile.mkdtemp(prefix="enc-cli-")
        try:
            os.makedirs(os.path.join(tmp, "tv"))
            io.open(os.path.join(tmp, "tv", "bad_cli.py"), "w", encoding="utf-8").write(
                u'if __name__ == "__main__":\n    print("⚠ warning")\n')
            bad = subprocess.run([sys.executable, os.path.join(ROOT, "tv", "console_safe.py"), tmp],
                                 capture_output=True, text=True, timeout=120)
            self.assertEqual(bad.returncode, 1,
                             "an unsafe script was found and the CLI still reported success - the "
                             "hook reads this code, so a printed finding with exit 0 is invisible")
            self.assertIn("bad_cli.py", bad.stdout,
                          "it must NAME the file; a count alone leaves him grepping for it")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

        r = subprocess.run([sys.executable, os.path.join(ROOT, "tv", "console_safe.py")],
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0,
                         "the tree is clean today, so the CLI must succeed: %s" % r.stdout[-300:])
        self.assertIn("encoding-safe", r.stdout,
                      "a silent success tells the reader nothing about what was checked")
        self.assertRegex(r.stdout, r"\d+ entry point",
                         "it must say HOW MANY it checked - a pass with no denominator is a "
                         "claim, not a measurement")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "an audit that always returns [] passes every source law and catches nothing",
        "file": "tv/console_safe.py",
        "find": "        bad.append(_os.path.relpath(path, repo))",
        "replace": "        pass",
        "matches": 1,
    },
    {
        "why": "dropping the import exemption flags files that ARE safe, which trains people to ignore it",
        "file": "tv/console_safe.py",
        "find": "        if \"reconfigure\" in src or _VIA_IMPORT.search(src):",
        "replace": "        if \"reconfigure\" in src:",
        "matches": 1,
    },
    {
        "why": "a CLI that prints the finding and exits 0 is the defect this whole file replaces",
        "file": "tv/console_safe.py",
        "find": "        _sys.exit(1)",
        "replace": "        _sys.exit(0)",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
