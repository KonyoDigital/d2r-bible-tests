# -*- coding: utf-8 -*-
"""REG-2351 (#42 R7) - A CLOSING CLEAN RUN THAT COULD NOT FINISH IS ASKED ONCE MORE BEFORE A GATE'S PROOFS ARE DROPPED.

A gate's proofs share one clean run (REG-1669) and a CLOSING clean run after the last proof must still be green, or no
PROVEN of the gate is kept. _closing_clean treated UNKNOWN - a deadline, a run a signal ended (REG-2350), a raise - like
RED, so one closing run that could not finish discarded every proof the gate had just earned: test_control's 27 proofs
are ~92 minutes of runs. Now an UNKNOWN closing run is asked once more; a RED one is never asked again (red is a
finding), and a second UNKNOWN discards as before. A retry that comes back green is still a green clean run after the
last proof, so the REG-1988 bracket holds.

Driven through the REAL _prove_gate (census path) and _prove_gate_push (push path, with a fixture verdict cache); only
the law RUN is a stand-in, which answers from the subject file's actual bytes and, for its clean runs, from a script.
RED_PROOF below. [[unknown-stays-unknown]]
"""
import io
import os
import shutil
import sys
import tempfile
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

GATE = "no-such-registered-gate"
LINES = []


def _say(*a, **k):
    LINES.append(" ".join(str(x) for x in a))


class _Runs(object):
    """A stand-in for heart2._run_gate. Tampered (the subject reads BAD) it is red; its Nth CLEAN run answers
    `clean[N-1]` - True, False (red), None (could not finish) or "raise" - and True once the script runs out."""

    def __init__(self, tv, clean):
        self.tv, self.script = tv, list(clean)
        self.clean, self.tampered = 0, 0

    def __call__(self, sandbox_tv, filename, timeout=180, extra=(), script=None, widths=None):
        with io.open(os.path.join(self.tv, "subject.py"), encoding="utf-8") as fh:
            if "BAD" in fh.read():
                self.tampered += 1
                return False, "Ran 1 test | FAILED"
        self.clean += 1
        a = self.script[self.clean - 1] if self.clean <= len(self.script) else True
        if a == "raise":
            raise OSError("the sandbox file is locked")
        return a, {True: "Ran 1 test | OK", False: "Ran 1 test | FAILED (drifted)"}.get(a, "timed out after 120s")


class _Gate(unittest.TestCase):

    def setUp(self):
        del LINES[:]
        self.root = tempfile.mkdtemp(prefix="h2closing.")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.tv = os.path.join(self.root, "repo", "tv")
        os.makedirs(self.tv)
        with io.open(os.path.join(self.tv, "subject.py"), "w", encoding="utf-8") as fh:
            fh.write('A = "GOOD"\nB = "GOOD"\nC = "GOOD"\n')
        with io.open(os.path.join(self.tv, "fake_gate.py"), "w", encoding="utf-8") as fh:
            fh.write("import sys\nsys.exit(0)\n")
        self.proofs = [{"file": "subject.py", "find": '%s = "GOOD"' % k, "replace": '%s = "BAD"' % k,
                        "matches": 1, "why": k} for k in ("A", "B", "C")]
        p = mock.patch.object(H, "_run_gate", None)
        p.start()
        self.addCleanup(p.stop)
        self.assertIsNone(H._PUSH, "PREMISE: no push-time run is in progress")

    def gate(self, clean):
        self.runs = _Runs(self.tv, clean)
        H._run_gate = self.runs
        return H._prove_gate(self.tv, GATE, "fake_gate.py", self.proofs, _say)


class AClosingRunThatCouldNotFinishIsAskedOnceMore(_Gate):

    def test_an_unknown_closing_run_then_green_keeps_every_proof(self):
        verdict, per = self.gate([True, None, True])
        self.assertEqual((verdict, per), (H.PROVEN, [H.PROVEN] * 3),
                         "a closing run that could not finish threw away proofs a green retry stood behind")
        self.assertEqual(self.runs.clean, 3, "PREMISE: first clean run, closing run, one retry")
        self.assertTrue(any("REG-2351" in ln and "asked once more" in ln for ln in LINES), LINES)

    def test_a_raising_closing_run_is_unknown_and_asked_once_more(self):
        verdict, per = self.gate([True, "raise", True])
        self.assertEqual(per, [H.PROVEN] * 3, "a closing run that raised was not asked again")

    def test_a_red_closing_run_is_never_asked_again(self):
        verdict, per = self.gate([True, False, True])
        self.assertEqual(per, [H.UNPROVABLE] * 3, "a RED closing run was retried until it read green")
        self.assertEqual(self.runs.clean, 2, "a red closing run was asked again (%d clean runs)" % self.runs.clean)

    def test_it_is_asked_once_more_not_until_it_answers(self):
        verdict, per = self.gate([True, None, None])
        self.assertEqual(per, [H.UNPROVABLE] * 3, "two closing runs that could not finish still banked proofs")
        self.assertEqual(self.runs.clean, 3, "the closing run was asked %d times, not twice" % (self.runs.clean - 1))

    def test_unknown_then_red_discards(self):
        verdict, per = self.gate([True, None, False])
        self.assertEqual(per, [H.UNPROVABLE] * 3)

    def test_a_green_closing_run_is_asked_once(self):
        verdict, per = self.gate([True, True])
        self.assertEqual(per, [H.PROVEN] * 3)
        self.assertEqual(self.runs.clean, 2, "PREMISE: a green closing run needs no retry")


class ThePushPathKeepsWhatTheRetryStoodBehind(_Gate):
    """The same rule where it costs most: a push-time gate banks its proofs only after the closing run."""

    def setUp(self):
        super(ThePushPathKeepsWhatTheRetryStoodBehind, self).setUp()
        p = mock.patch.dict(os.environ, {"HEART2_RED_MEMORY": "0"})   # the sabotage memory is neither read nor written
        p.start()
        self.addCleanup(p.stop)
        self.cache = H._VerdictCache(path=os.path.join(self.root, ".heart2_cache.json"), say=_say)
        self.addCleanup(lambda: setattr(H, "_PUSH", None))

    def gate(self, clean):
        self.runs = _Runs(self.tv, clean)
        H._run_gate = self.runs
        H._PUSH = H._PushRun(order={}, browser=(), cache=self.cache)
        try:
            return H._prove_gate(self.tv, GATE, "fake_gate.py", self.proofs, _say)
        finally:
            H._PUSH = None

    def test_a_green_retry_banks_the_gate(self):
        verdict, per = self.gate([True, None, True])
        self.assertEqual(per, [H.PROVEN] * 3)
        self.assertEqual(len(self.cache.entries), 3, "a push banked %d of the 3 proofs a green retry stood behind"
                         % len(self.cache.entries))

    def test_a_red_closing_run_banks_nothing(self):
        verdict, per = self.gate([True, False, True])
        self.assertEqual(self.cache.entries, {}, "a PROVEN a red closing run took away was banked after a retry")


RED_PROOF = [
    {"why": "REG-2351 - a RED closing run is asked again until it reads green, so a drifted sandbox's PROVEN is banked",
     "file": "heart2.py",
     "find": "            if ok is not None or _ask == 2:              # REG-2351",
     "replace": "            if ok is True or _ask == 2:                  # REG-2351",
     "matches": 1},
    {"why": "REG-2351 - a closing run that could not finish discards the gate's proofs at once, never asked again",
     "file": "heart2.py",
     "find": "        for _ask in (1, 2):\n",
     "replace": "        for _ask in (2,):\n",
     "matches": 1},
    {"why": "REG-2351 - a closing run that cannot finish is asked over and over, never once",
     "file": "heart2.py",
     "find": "        for _ask in (1, 2):\n",
     "replace": "        for _ask in (1, 1, 2):\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
