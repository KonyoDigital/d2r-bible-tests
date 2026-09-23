# -*- coding: utf-8 -*-
"""v3432 (#179) — A PROCESS MUST NOT GRADE A FILE IT IS NOT RUNNING.

MEASURED 2026-09-23: three pushes of the IDENTICAL tree, minutes apart, read `tv suites green`,
then `test_control FAILED`, then `tv suites green`. The failing traceback named
`test_control.py line 11902 ... assertIn('spec["store"]', fn` — the file on disk has that assertion
at line **11938** using the variable **`helper`**, and the older shape is exactly the PRE-v3427
code. The same run also reported an older second-eye version. Three anomalies in ONE run, none
explicable by the tree, and the full suite then ran 2,238 tests OK on it.

⚠ A SUITE EXECUTING CODE THAT IS NOT ON DISK IS WORSE THAN A RED ONE, because its verdict is about
a file nobody has — and it costs a real push while pointing at a line that does not exist.

⚠ IT CANNOT BE CAUGHT BY COMPARING mtime AND SIZE, which is exactly what CPython already uses to
call a `.pyc` fresh: a check built from the same two inputs agrees with it by construction,
including when they collide. The only witness that survives a collision is the CODE: `co_firstlineno`
comes from the BYTECODE, the source file is read fresh, and a disagreement is decisive.

⚠ AND ON THIS MAC THE CACHE IS NOT IN `__pycache__` — `sys.pycache_prefix` relocates it to
~/Library/Caches/com.apple.python, so "I deleted __pycache__" clears nothing.
[[python-pycache-prefix-mac]]
"""
import io
import os
import sys
import tempfile
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import code_identity as CI  # noqa: E402


class TestTheCodeRunningIsTheCodeOnDisk(unittest.TestCase):

    def _module_from(self, body, name):
        """Write a module, import it, hand back (module, path)."""
        d = tempfile.mkdtemp(prefix="codeid_")
        self.addCleanup(__import__("shutil").rmtree, d, True)
        p = os.path.join(d, name + ".py")
        io.open(p, "w", encoding="utf-8").write(textwrap.dedent(body))
        sys.path.insert(0, d)
        self.addCleanup(lambda: sys.path.remove(d) if d in sys.path else None)
        mod = __import__(name)
        self.addCleanup(sys.modules.pop, name, None)
        return mod, p

    # ---- the defect, CREATED rather than described ---------------------------------------

    def test_a_source_that_MOVED_under_the_loaded_code_is_caught(self):
        """THE WHOLE POINT. Import a module, then rewrite its file so the function sits somewhere
        else. The bytecode in memory is now describing a file that no longer says that — which is
        the shape that cost a push."""
        mod, p = self._module_from("""
            def alpha():
                return 1
            """, "codeid_moved")
        checked, bad, why = CI.drift(mod)
        self.assertEqual(bad, [], "a freshly imported module already disagreed with its own file")
        self.assertGreaterEqual(checked, 1, "nothing was compared, so this case measures nothing")
        # now push the function down the file WITHOUT re-importing
        io.open(p, "w", encoding="utf-8").write(
            "# a comment\n" * 40 + textwrap.dedent("""
            def alpha():
                return 1
            """))
        checked2, bad2, _w = CI.drift(mod)
        self.assertTrue(bad2,
                        "the source moved 40 lines under the loaded code and the check said "
                        "nothing — it cannot tell a running image from its file")
        self.assertEqual(bad2[0][0], "alpha", "it flagged the wrong function: %r" % (bad2,))

    def test_a_clean_module_reports_no_drift(self):
        mod, _p = self._module_from("""
            def beta():
                return 2

            def gamma():
                return 3
            """, "codeid_clean")
        checked, bad, why = CI.drift(mod)
        self.assertEqual(bad, [], "a module that matches its file was reported as drifted: %r" % (bad,))
        self.assertEqual(checked, 2, "expected to compare both functions, compared %d" % checked)

    # ---- the instrument bug this check SHIPPED WITH, pinned -------------------------------

    def test_a_contextmanager_wrapper_is_NOT_a_false_positive(self):
        """⚠ THE FIRST CUT REPORTED `tick_caches` AND `_lock_briefly` AS DRIFTED, BOTH AT LINE 242 —
        the same line in two unrelated modules, which is the tell that the instrument was wrong and
        not the code. `@contextmanager` uses functools.wraps, which copies `__module__` onto a
        wrapper whose `__code__` lives in contextlib.py; line 242 there is the generic `helper`.
        Unwrapped, the real functions sit at 7437 and 3592 of their own files.
        [[feedback-suspect-the-instrument]]"""
        mod, _p = self._module_from("""
            import contextlib

            @contextlib.contextmanager
            def held():
                yield 1
            """, "codeid_ctx")
        checked, bad, why = CI.drift(mod)
        self.assertEqual(bad, [],
                         "a @contextmanager wrapper was reported as drifted — the check is reading "
                         "contextlib's line numbers as if they were this module's: %r" % (bad,))
        # ⚠ v3434 — AND IT MUST HAVE COMPARED SOMETHING. The eye pointed out that a TOTAL SKIP of
        # the decorated function also produces `bad == []`, so this passed whether the check looked
        # or not. A green with no denominator is not a green. [[zero-needs-a-denominator]]
        self.assertGreaterEqual(checked, 1, "nothing in this module was compared at all")

    def test_a_SAME_FILE_wraps_decorator_is_NOT_a_false_positive(self):
        """⚠⚠ THE CASE THE FIRST PROOF ATTEMPT EXPOSED AS MISSING. The contextlib case above is
        carried entirely by the `co_filename` guard — the wrapper lives in contextlib.py, so it is
        skipped as foreign before `unwrap` matters. Tampering the unwrap therefore left that case
        GREEN: the red-proof came back BLIND at match count 1, which is the tell that the LAW was
        weak, not the sabotage wrong.

        `unwrap` earns its line HERE: a decorator defined in the SAME module produces a wrapper
        whose `co_filename` IS this file, so the foreign-file guard waves it through and only
        unwrapping finds the real `def`. Without it the wrapper's line points at the decorator's
        inner function and every decorated function in the repo reads as drifted."""
        mod, _p = self._module_from("""
            import functools

            def deco(f):
                @functools.wraps(f)
                def inner(*a, **k):
                    return f(*a, **k)
                return inner

            @deco
            def epsilon():
                return 5
            """, "codeid_localdeco")
        checked, bad, why = CI.drift(mod)
        self.assertEqual(bad, [],
                         "a function decorated by a SAME-FILE functools.wraps decorator was "
                         "reported as drifted — the check is reading the wrapper's line number "
                         "instead of the function's: %r" % (bad,))
        self.assertGreaterEqual(checked, 1, "nothing was compared, so this case measures nothing")

    def test_a_BLANK_line_appearing_at_the_def_is_caught(self):
        """⚠ v3434 — THE MISS THE SECOND EYE FOUND. The old line-walk skipped blank lines, so a
        blank appearing exactly where the function used to start let it stroll down and re-find the
        `def` — a genuinely stale function read CLEAN. Comments were caught; blanks were not."""
        mod, p = self._module_from("""
            def zeta():
                return 1
            """, "codeid_blank")
        self.assertEqual(CI.drift(mod)[1], [], "clean module already disagreed with its file")
        io.open(p, "w", encoding="utf-8").write("\n" + textwrap.dedent("""
            def zeta():
                return 1
            """))
        checked, bad, _w = CI.drift(mod)
        self.assertTrue(bad, "a blank line moved the function and the check said nothing")

    def test_a_MULTI_LINE_decorator_is_NOT_a_false_positive(self):
        """⚠ v3434 — ORDINARY PYTHON THAT THE OLD WALK CALLED DRIFT. `@deco(\n "arg",\n)` stopped
        the walk on `"arg",`, so a function loaded correctly from disk was reported MISSING. A
        check that cries wolf on ordinary formatting is one nobody leaves switched on."""
        mod, _p = self._module_from("""
            def deco(*a, **k):
                def wrap(f):
                    return f
                return wrap

            @deco(
                "arg",
            )
            def eta():
                return 7
            """, "codeid_multideco")
        checked, bad, _w = CI.drift(mod)
        self.assertEqual(bad, [], "a multi-line decorator was reported as drift: %r" % (bad,))
        self.assertGreaterEqual(checked, 1, "nothing was compared, so this case measures nothing")

    def test_a_module_level_LAMBDA_is_not_mistaken_for_a_drifted_def(self):
        """⚠ v3434 — its `co_name` is `<lambda>`, which no `def` line can match. The old check
        compared the DICT KEY and flagged it."""
        mod, _p = self._module_from("""
            normalize = lambda s: s.strip()

            def theta():
                return 8
            """, "codeid_lambda")
        checked, bad, _w = CI.drift(mod)
        self.assertEqual(bad, [], "a module-level lambda was reported as drift: %r" % (bad,))
        self.assertGreaterEqual(checked, 1, "nothing was compared, so this case measures nothing")

    def test_an_ALIAS_resolves_to_the_function_that_was_compiled(self):
        """⚠ v3434 — `public = _real` has a dict key that is not the `def` name. Comparing
        `co_name` instead of the key is what makes the alias resolve."""
        # ⚠⚠ THE `del` IS LOAD-BEARING AND A BLIND RED-PROOF IS WHY. With `_real` still bound,
        # comparing the DICT KEY merely SKIPS the alias while `_real` itself still gets compared —
        # so `bad == []` and `checked >= 1` both hold either way and the proof came back BLIND at
        # match count 1. Deleting `_real` makes the alias the ONLY binding, so the key-vs-co_name
        # choice decides whether anything is compared at all. A case that does not exercise the
        # line cannot pin it. [[matches-once-can-still-prove-nothing]]
        mod, _p = self._module_from("""
            def _real():
                return 9

            public = _real
            del _real
            """, "codeid_alias")
        checked, bad, _w = CI.drift(mod)
        self.assertEqual(bad, [], "an alias was reported as drift: %r" % (bad,))
        self.assertGreaterEqual(checked, 1,
                                "the alias was SKIPPED rather than resolved — comparing the dict "
                                "key instead of co_name means an aliased function is never checked "
                                "at all, which is a silent hole rather than a false alarm")

    def test_a_MIXED_look_is_UNMEASURED_not_a_clean_bill(self):
        """⚠ v3434 — THE FALSE CLEAN. `say()` returned True whenever anything matched and nothing
        mismatched, DROPPING every reason a module could not be compared — so one healthy module
        could carry a verdict over a population that had quietly shrunk. The all-unmeasured branch
        was already honest; the MIXED branch was not, which is the harder half to notice."""
        __import__("code_identity")
        ok, text = CI.say(["code_identity", "a_module_that_is_definitely_not_imported"])
        self.assertIsNone(ok, "a partial look was reported as agreement: %s" % text)
        self.assertIn("UNMEASURED", text.upper())

    # ---- unmeasured is not agreement -----------------------------------------------------

    def test_a_module_with_no_readable_source_is_UNMEASURED(self):
        mod, p = self._module_from("""
            def delta():
                return 4
            """, "codeid_gone")
        os.remove(p)
        checked, bad, why = CI.drift(mod)
        self.assertTrue(why, "an unreadable source produced a verdict instead of an UNKNOWN")
        self.assertEqual(bad, [], "it invented a mismatch from a file it could not read")

    def test_say_with_nothing_imported_is_UNMEASURED_not_OK(self):
        ok, text = CI.say(["a_module_that_is_not_imported_anywhere"])
        self.assertIsNone(ok, "nothing was compared and it answered %r — a zero with no "
                              "denominator: %s" % (ok, text))
        self.assertIn("UNMEASURED", text.upper())

    def test_this_very_process_agrees_with_its_own_files(self):
        """The live reading, on the interpreter running this gate."""
        for m in ("code_identity", "console_safe"):
            __import__(m)
        ok, text = CI.say(["code_identity", "console_safe"])
        self.assertTrue(ok, "the process running this gate is executing code that is not on "
                            "disk: %s" % text)


RED_PROOF = [
    {
        "why": "v3434 - THE COMPARISON ITSELF DEFEATED. If a function whose source moved is not "
               "reported, the module answers the one question it exists for with silence, and a "
               "silent check here is indistinguishable from a healthy process.",
        "file": "code_identity.py",
        "find": "        if code.co_firstlineno != expected:",
        "replace": "        if False:",
        "matches": 1,
    },
    {
        "why": "v3434 - THE DICT KEY INSTEAD OF co_name. `public = _real` and every import alias "
               "then compare a key that no `def` line carries, so a module that agrees perfectly "
               "with its file is reported as drifted. That false alarm is how a check gets turned "
               "off.",
        "file": "code_identity.py",
        "find": "        expected = table.get(code.co_name)",
        "replace": "        expected = table.get(_key)",
        "matches": 1,
    },
    {
        "why": "v3434 - THE UNWRAP REMOVED. A same-file functools.wraps decorator produces a "
               "wrapper whose co_filename IS this module, so the foreign-file guard waves it "
               "through and only unwrapping finds the real def. Without it every decorated "
               "function in the repo reads as drifted.",
        "file": "code_identity.py",
        "find": "            fn = inspect.unwrap(obj)",
        "replace": "            fn = obj",
        "matches": 1,
    },
    {
        "why": "v3434 - THE MIXED BRANCH REMOVED, WHICH IS THE FALSE CLEAN. One healthy module "
               "would again carry a confident verdict over a population that had quietly shrunk, "
               "dropping every reason another module could not be compared at all.",
        "file": "code_identity.py",
        "find": "    if why:\n        return None, (\"%d function(s) matched, but %d of %d module(s) could not be compared at all \"",
        "replace": "    if False:\n        return None, (\"%d function(s) matched, but %d of %d module(s) could not be compared at all \"",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
