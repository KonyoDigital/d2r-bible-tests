# -*- coding: utf-8 -*-
"""v3421 — A FAILURE CLOSING stdin MUST NOT SKIP THE REAP.

The shutdown of the ocr worker was three statements sharing one `try`:

    try:
        wp.stdin.close(); wp.terminate()
        threading.Thread(target=wp.wait, daemon=True, name="tvd-ocr-reap").start()
    except Exception:
        pass

`wp.stdin.close()` raises BrokenPipeError when the worker has **already exited on its own** — and
that is precisely the case that leaves a zombie. One raise and `terminate()` never ran, the reaper
thread never started, and the bare `except` said nothing. **The guard was skipped in exactly the
scenario it was written for, and looked healthy in every other.**

⚠ THE FIX IT REPLACED WAS ITSELF A FIX. The comment at that site already read *"Measured
2026-09-01: 12 defunct children, oldest 16.5h"* — the reap had been added three weeks earlier and
leaked anyway, because of the shared `try` one line above it.

MEASURED 2026-09-23: 14 defunct children of his console. A 95-minute catcher sampling every second
logged 81 children; exactly one later became defunct, and it had been caught ALIVE first —
`tv/bin/ocr_mac --worker`, pid 88160, alive 23:36:21, `<defunct>` 70 minutes later. **A zombie
carries no argv**, so nothing but catching it alive could have named the site; four rounds of
reading the file could not choose between three Popen sites.

⚠ THIS GATE DRIVES THE SHIPPED ROUTINE. `close_ocr_worker` was extracted so the failure can be
handed to it directly — a source check would only prove the text is arranged a certain way, not
that a broken pipe still gets reaped. [[copy-drift]] §7 — one routine, one home, and the other
sites call it.
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

import control_app as CA  # noqa: E402


class _Stdin(object):
    def __init__(self, raises=None):
        self.raises, self.closed = raises, False

    def close(self):
        if self.raises:
            raise self.raises
        self.closed = True


class _Worker(object):
    """A stand-in for the Popen. Records what was actually called on it."""

    def __init__(self, stdin_raises=None, terminate_raises=None, no_stdin=False):
        self.stdin = None if no_stdin else _Stdin(stdin_raises)
        self._terminate_raises = terminate_raises
        self.terminated = False
        self.waited = False

    def terminate(self):
        self.terminated = True
        if self._terminate_raises:
            raise self._terminate_raises

    def wait(self):
        self.waited = True


class TestABrokenPipeMustNotSkipTheReap(unittest.TestCase):

    def setUp(self):
        self._said = []

    def _say(self, m):
        self._said.append(m)

    # ---- baseline: a healthy worker is closed, terminated and reaped ----------------------

    def test_BASELINE_a_healthy_worker_is_closed_terminated_and_reaped(self):
        w = _Worker()
        ok = CA.close_ocr_worker(w, say=self._say)
        self.assertTrue(ok, "the reap thread did not start on a perfectly healthy worker — every "
                            "case below would then pass for the wrong reason")
        self.assertTrue(w.stdin.closed)
        self.assertTrue(w.terminated)
        self.assertEqual(self._said, [], "a healthy shutdown should say nothing")

    # ---- the defect --------------------------------------------------------------------

    def test_a_BROKEN_PIPE_on_stdin_still_terminates_and_still_reaps(self):
        """The worker exited on its own, so the pipe is broken — the zombie case exactly."""
        w = _Worker(stdin_raises=BrokenPipeError("worker already gone"))
        ok = CA.close_ocr_worker(w, say=self._say)
        self.assertTrue(w.terminated,
                        "stdin.close() raised and terminate() was skipped — the shared-try defect")
        self.assertTrue(ok,
                        "stdin.close() raised and the REAP was skipped, which is how this leaked "
                        "one zombie per closer run for three weeks")

    def test_ANY_stdin_failure_still_reaps(self):
        for exc in (BrokenPipeError("gone"), ValueError("closed file"), OSError("errno 9")):
            w = _Worker(stdin_raises=exc)
            self.assertTrue(CA.close_ocr_worker(w, say=self._say),
                            "a %s closing stdin skipped the reap" % type(exc).__name__)

    def test_a_FAILING_terminate_still_reaps(self):
        """It may already be dead; wait() reaps it regardless."""
        w = _Worker(terminate_raises=OSError("no such process"))
        self.assertTrue(CA.close_ocr_worker(w, say=self._say),
                        "terminate() raised and the reap was skipped")

    def test_a_worker_with_NO_stdin_does_not_crash_or_skip(self):
        w = _Worker(no_stdin=True)
        self.assertTrue(CA.close_ocr_worker(w, say=self._say))
        self.assertTrue(w.terminated)

    # ---- and a failed reap is never silent -----------------------------------------------

    def test_a_reap_that_cannot_start_SAYS_SO(self):
        """⚠ The one refusal that says nothing is the one that hides — this exact silence cost
        three weeks. [[feedback-silence-is-not-evidence]]"""
        w = _Worker()
        real = CA.threading.Thread

        class _Boom(object):
            def __init__(self, *a, **k):
                pass

            def start(self):
                raise RuntimeError("can't start new thread")

        CA.threading.Thread = _Boom
        try:
            ok = CA.close_ocr_worker(w, say=self._say)
        finally:
            CA.threading.Thread = real
        self.assertFalse(ok, "a reap that never started reported success")
        self.assertTrue(self._said, "the reap failed and NOTHING was said — silent exactly where "
                                    "it matters")
        self.assertIn("defunct", " ".join(self._said).lower(),
                      "the message does not say what the consequence is")

    # ---- the same class, swept: a timeout handler that kills must also reap -------------

    def test_every_timeout_handler_in_the_eye_REAPS_what_it_kills(self):
        """⚠ SWEPT BECAUSE THE CLASS WAS FOUND, NOT THE INSTANCE. The second eye reviewing v3420
        named this while the ocr-worker leak was being fixed: `communicate()` reaps on the normal
        path and is EXACTLY what raised on the timeout path, so `p.kill()` alone leaves a
        <defunct> child per timeout. Parsed structurally — a grep for 'kill' would match prose,
        and an AST sweep for kill-without-reap already produced 7 hits of which 6 were os.kill and
        the 7th was a false positive on an attribute reference. [[sweep-dont-ask]] §1"""
        import ast
        src = io.open(os.path.join(HERE, "second_eye_run.py"),
                      encoding="utf-8", errors="replace").read()
        tree = ast.parse(src)
        bad = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            names = {getattr(n, "attr", getattr(n, "id", "")) for n in ast.walk(node)
                     if isinstance(n, (ast.Attribute, ast.Name))}
            if "TimeoutExpired" not in str(ast.dump(node.type)) if node.type else True:
                continue
            calls = {n.func.attr for n in ast.walk(node)
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
            if "kill" in calls and not (calls & {"communicate", "wait"}):
                bad.append(node.lineno)
        self.assertEqual(bad, [], "timeout handler(s) at line(s) %r kill a child and never reap "
                                  "it — one <defunct> per timeout, which is the same defect this "
                                  "file was opened for" % (bad,))

    # ---- the call site actually calls it --------------------------------------------------

    def test_the_closer_loop_CALLS_the_routine_rather_than_re_implementing_it(self):
        """[[copy-drift]] §7 — a safety routine that exists twice is the dangerous copy."""
        src = io.open(os.path.join(HERE, "control_app.py"),
                      encoding="utf-8", errors="replace").read()
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        self.assertIn("close_ocr_worker(wp)", code,
                      "the closer loop no longer calls the shared routine")
        self.assertEqual(code.count('name="tvd-ocr-reap"'), 1,
                         "the reap exists in more than one place — the copy-drift shape")


RED_PROOF = [
    {
        "why": "v3421 - THE SHARED try, RESTORED. Closing stdin inside the same try as terminate "
               "means a BrokenPipeError from a worker that already exited skips both the "
               "terminate and the reap - which is the exact case that leaves a zombie, and the "
               "reason this leaked for three weeks after the reap was added.",
        "file": "control_app.py",
        # ⚠ v3421 — SHORT AND EXACT. My first anchor pasted the whole three-step block and
        # matched ZERO times, because the comment carries an em dash and I typed a hyphen.
        # heart2 would have reported INVALID. [[source-reading-guard]] §2 — print the count.
        "find": "        pass                      # already dead or already closed",
        "replace": "        return False  # the shared-try defect: a broken pipe skips everything below",
        "matches": 1,
    },
    {
        "why": "v3421 - THE FAILED REAP MADE SILENT AGAIN. Returning without a word when the "
               "reaper thread cannot start reinstates the silence that hid this defect: the rows "
               "keep arriving, the console keeps working, and the process table fills up.",
        "file": "control_app.py",
        "find": "        (say or (lambda m: print(m, flush=True)))(msg)\n        return False",
        "replace": "        return False",
        "matches": 1,
    },
    {
        "why": "v3421 - A TIMEOUT THAT KILLS AND NEVER REAPS. communicate() reaps on the normal "
               "path and is exactly what raised on the timeout path, so removing the second call "
               "leaves one <defunct> child per timeout - the same defect the ocr worker had, in "
               "the harness that reviews the fix.",
        "file": "second_eye_run.py",
        "find": "            p.communicate(timeout=10)\n        except Exception:\n            pass                      # it may already be gone; the reap is best-effort, not a bet\n",
        "replace": "            pass\n        except Exception:\n            pass\n",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
