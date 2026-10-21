# -*- coding: utf-8 -*-
"""v1480 — A TOOL WHOSE VERDICT IS ITS EXIT CODE MUST NOT DIE REPORTING IT. Moved out of test_control (REG-2362).

The rule is console_safe.audit() (v3293: one definition; tv/console_safe.py's CLI answers in under a second and
hooks/pre-push runs it before anything expensive). This case lived inside test_control beside a `_scripts()` folder
glob nobody called - and that glob alone made the whole of test_control a law that LISTS A DIRECTORY ITSELF, which
heart2 cannot key, so none of test_control's 27 proofs was ever saved (~4 min each, every push of the v3783 series).
Here the glob has a job: it is the denominator the audit cannot supply for itself. This law lists tv/ on purpose, so it
is unkeyable on purpose - in tv/unkeyable_laws.json, cheap, and run at the top of every push by the hook's own
`python3 tv/console_safe.py` step. [[copy-drift]] [[zero-needs-a-denominator]]
"""
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()       # this file prints non-ASCII; a cp1255 console must not crash while REPORTING
except Exception:
    pass


class TestToolsCanReportTheirVerdict(unittest.TestCase):
    """v1480 — a tool whose verdict is its exit code must not die reporting it.

    Fourth instance of one bug: REG-044 (tv_diablo could not print its status lines), REG-054 (both
    suites were only green because PYTHONIOENCODING was set by hand off-screen — a plain run went
    red AND corrupted a tracked fixture), REG-077 (visual_lock_invariant and js_syntax_gate each
    PASSED, reached the success branch, then died inside `print("✅ …")`).

    This machine's console is Hebrew (cp1255) and cannot encode the check marks, arrows and box
    characters the tooling prints everywhere. The failure always lands in the dangerous direction:
    a CORRECT tree reports FAILURE, which teaches people to ignore the tool, and then the next real
    failure is ignored too. `tv/test_button_matrix.py` proves the cost — it died on encoding, and
    hidden underneath was a `^v8\\d\\d` version assertion that had been wrong since v900.

    So: any CLI script that prints non-ASCII must make its own output encoding-safe, rather than
    inherit safety from the operator's shell.
    """

    TV = os.path.dirname(os.path.abspath(__file__))
    REPO = os.path.dirname(TV)
    # These get their safety from a module they import, which installs it at import time.
    VIA_IMPORT = re.compile(r"^\s*(?:import|from)\s+(control_app|tv_diablo|console_safe)\b", re.M)

    def _scripts(self):
        import glob
        out = list(glob.glob(os.path.join(self.TV, "*.py")))
        out.append(os.path.join(self.REPO, "visual_lock_invariant.py"))
        return sorted(out)

    def test_the_rule_reads_every_entry_point_the_folder_holds(self):
        """REG-2362 - THE DENOMINATOR. `_scripts()` lived in test_control unused; it moved here with the rule and now
        asks the one question an audit cannot ask of itself: did it read everything? The audit walks
        console_safe.scripts(); this lists the folder itself, so a scripts() that lost tv/ or visual_lock_invariant.py
        - an audit of nothing that reports nothing unsafe - goes red here."""
        sys.path.insert(0, self.TV)
        import console_safe
        got = sorted(console_safe.scripts(self.REPO))
        self.assertGreater(len(got), 100, "console_safe.scripts() returned %d entry points - the audit reads almost "
                                          "nothing, so its empty verdict is a reader failing, not a clean tree" % len(got))
        self.assertEqual(got, self._scripts(), "the audit's population is not the folder's: %s"
                         % sorted(set(got) ^ set(self._scripts()))[:6])

    def test_every_cli_that_prints_non_ascii_is_encoding_safe(self):
        # ⚠ v3293 — THE RULE MOVED TO console_safe.audit() AND THIS CALLS IT. It used to be
        # spelled out here, which made it reachable only by running a ~500s suite at push time —
        # the most expensive moment to learn that a one-line import is missing. It now also has a
        # CLI (`python3 tv/console_safe.py`) that answers in under a second, and the pre-push hook
        # runs that first. Keeping a second copy of the rule here is how two rules begin to
        # disagree, so this asserts on the SAME function the fast path calls. [[copy-drift]]
        sys.path.insert(0, self.TV)
        import console_safe
        unsafe = console_safe.audit(self.REPO)
        self.assertEqual(
            unsafe, [],
            "these print non-ASCII but never make stdout encoding-safe, so on a non-UTF-8 console "
            "they crash while REPORTING and a clean tree exits non-zero:\n  " + "\n  ".join(unsafe)
            + "\nAdd `from console_safe import enable; enable()` (see tv/console_safe.py).")

    def test_console_safe_never_raises(self):
        """The helper's whole job is to stop crashes, so it must not become a new source of them —
        including on stream objects that cannot be reconfigured at all."""
        sys.path.insert(0, self.TV)
        import console_safe
        import io as _io
        self.assertTrue(console_safe.enable(_io.TextIOWrapper(_io.BytesIO())))
        # a stream with no reconfigure(): reports False, raises nothing
        class Dumb:
            pass
        self.assertFalse(console_safe.enable(Dumb()))
        self.assertFalse(console_safe.enable(_io.StringIO()))
        console_safe.enable(None)          # tolerated, no exception


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-2362 - the audit's population loses visual_lock_invariant.py: an entry point nobody audits again",
        "file": "console_safe.py",
        "find": "    out.append(_os.path.join(repo, \"visual_lock_invariant.py\"))\n",
        "replace": "    pass\n",
        "matches": 1,
    },
    {
        "why": "v1480 - a CLI that prints non-ASCII loses the import that makes its stdout safe: on his cp1255 console it "
               "crashes while REPORTING, so a clean tree exits non-zero",
        "file": "page_delta.py",
        "find": "from console_safe import enable as _console_safe_enable\n",
        "replace": "_console_safe_enable = lambda: None\n",
        "matches": 1,
    },
]
