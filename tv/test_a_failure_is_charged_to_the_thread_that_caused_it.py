# -*- coding: utf-8 -*-
"""v3304 (#55) — A GATE FAILURE IS CHARGED TO THE THREAD THAT CAUSED IT, NEVER TO THE ONE LOOKING.

`_check_the_sweep_would_find_something` measures its own density pass by snapshotting the stash
gate's failure count before and after. v3297 (mine) took that snapshot from `gate_failures()` —
a PROCESS-WIDE counter — and the console gates frames on several threads at once.

REPRODUCED 2026-09-18, not argued: the doctor's window was opened, a separate thread broke exactly
one gate inside it, and the delta the check reads came back **1** while the density pass had broken
nothing. The check then answers:

    UNKNOWN — "the stash gate FAILED 1 time(s) during the density pass"

which is false. ⚠⚠ AND THE HARM IS NOT THE WRONG SENTENCE. Returning UNKNOWN means the genuine
MISSING — *"N reel(s) on disk and NONE shows a stash panel; a vault sweep would read nothing"* — is
NEVER RAISED. A check suppresses the exact finding it exists to produce, and it does so more often
the busier the console is.

⚠ THE LESSON WAS ALREADY CARVED THIRTY LINES AWAY, IN THE SAME FILE. v2191, on the BLIND channel:
*"THE BLIND STATE IS NOW A PER-CALL RECEIPT, NOT A PROCESS COUNTER"* — which Konyo called critical
and asked for first. That fixed `_GATE_SILENT`. The FAILURE channel was left as a process counter,
and v3297 used it in precisely the pattern v2191 removed, with the explanation sitting directly
above the function it called. [[copy-drift]] [[unknown-stays-unknown]]

TWO HALVES:
  1. `gate_failures_here()` is THREAD-LOCAL — another thread's failure never lands on this tally.
  2. `gate_failures()` keeps its process-wide meaning, because a total is a legitimate thing to
     report. The defect was never the counter; it was using a total to ATTRIBUTE.
"""
import os
import sys
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app as ca                                 # noqa: E402


class TestAFailureIsChargedToTheThreadThatCausedIt(unittest.TestCase):

    def test_another_threads_failure_does_not_land_on_my_tally(self):
        """⚠⚠ THE ONE THIS LAW EXISTS FOR — the reproduction, as a permanent law."""
        before = ca.gate_failures_here()
        proc_before = ca.gate_failures()

        done = threading.Event()

        def _other_lane():
            ca._gate_broke("some_other_sweep", RuntimeError("template unreadable"))
            done.set()

        t = threading.Thread(target=_other_lane, name="pretend-vault-sweep")
        t.start()
        self.assertTrue(done.wait(10), "the helper thread never ran; this case measured nothing")
        t.join()

        self.assertEqual(
            ca.gate_failures_here() - before, 0,
            "another thread broke a gate and it was charged to THIS thread. A caller measuring its "
            "own pass would then report UNKNOWN ('the instrument failed') over a footage answer "
            "that was perfectly measured — and because UNKNOWN is not MISSING, the real finding "
            "'no reel shows a stash panel' is never raised. That is a check suppressing the very "
            "thing it exists to produce.")

        # ...and the process total MUST still see it, or the fix has merely blinded the counter.
        self.assertEqual(
            ca.gate_failures() - proc_before, 1,
            "the process-wide counter did not move. gate_failures() is how a status surface reports "
            "a TOTAL; making it thread-local too would hide real failures from every reporter. The "
            "defect was never the counter — it was using a total to ATTRIBUTE.")

    def test_my_own_failure_does_land_on_my_tally(self):
        """A tally that never moves is not attribution, it is an off switch. [[strictness-that-closes-the-lane]]"""
        before = ca.gate_failures_here()
        ca._gate_broke("this_thread", RuntimeError("template unreadable"))
        self.assertEqual(
            ca.gate_failures_here() - before, 1,
            "a failure caused ON THIS THREAD was not counted here, so a caller can never detect "
            "its own broken instrument. A check that can never convict is the same defect as one "
            "that convicts the innocent, pointing the other way.")

    def test_the_doctor_reads_the_attributable_counter(self):
        """A correct helper that nothing reads is the unjoined end this repo keeps re-learning."""
        import io
        import re
        from frame_authority import _executable_only
        with io.open(os.path.join(HERE, "console_doctor.py"), encoding="utf-8") as fh:
            src = fh.read()
        # ⚠⚠ ".py", NOT ".js" — AND THIS LAW CAUGHT ITSELF GETTING IT WRONG.
        # `_executable_only` dispatches on EXTENSION. The ".js" branch strips `//` and `/* */`;
        # it does NOT strip Python `#` comments. This file is Python, and the comment I wrote
        # above the fixed call NAMES `gate_failures_here()` — so with ".js" the count came back
        # 3 instead of 2 and the guard was reading its own commentary. Measured both ways:
        # ".js" leaves 257,462 chars and sees 3; ".py" leaves 194,682 and sees 2.
        # The ".js" idiom IS correct for control_ui.html; it is wrong for a .py that parses.
        # [[source-reading-guard]] [[presence-law-vs-reachability-law]] REG-1070
        code = _executable_only(src, ".py")
        self.assertGreater(len(code), 50000, "the strip ate console_doctor.py — any count from it "
                                             "is meaningless. [[zero-needs-a-denominator]]")
        i = code.find("def _check_the_sweep_would_find_something")
        self.assertGreater(i, -1, "the sweep check is gone")
        j = code.find("\ndef ", i + 10)
        self.assertGreater(j, i, "could not bound the function; refusing to judge a slice whose "
                                 "far end is a guess. [[source-reading-guard]]")
        fn = code[i:j]
        self.assertEqual(
            len(re.findall(r"gate_failures_here\s*\(", fn)), 2,
            "the sweep check does not take BOTH ends of its delta from gate_failures_here(). One "
            "end from the process counter is the same misattribution with extra steps.")
        self.assertNotIn(
            "ca.gate_failures()", fn,
            "the sweep check still reads the PROCESS-WIDE counter. That is the v3297 defect: "
            "another lane's failure is charged to this pass.")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "reading the process counter charges another thread's failure to this pass",
        "file": "tv/console_doctor.py",
        "find": "        _gb0 = int(ca.gate_failures_here())",
        "replace": "        _gb0 = int(ca.gate_failures())",
        "matches": 1,
    },
    {
        "why": "a thread-local tally that never increments is an off switch, not attribution",
        "file": "tv/control_app.py",
        "find": '        _GATE_LAST.broke_here = int(getattr(_GATE_LAST, "broke_here", 0)) + 1',
        "replace": '        _GATE_LAST.broke_here = int(getattr(_GATE_LAST, "broke_here", 0))',
        "matches": 1,
    },
]
