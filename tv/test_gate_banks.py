"""v2464 — A2 · the gate must BANK what it scores, not only print it.

⚠ THE DEFECT THIS EXISTS FOR, and it was one of my own shipped claims. The board has said since
v2444 that "the sabotages BANK, first lock opened itself". Measured on the live console months
later: **open 0 of 5, every lock n=0, and tv/.self_arming.jsonl did not exist.**

v2444 put banking in `hover_wilson.main()` only, so that importing the module — or a test calling
`score()` — could not write his ledger. That rule is right. But the GATE also imports and calls
`score()`, so every push measured 55 sabotage attempts and fed the proof queue with NONE of them.
The only path from evidence to the queue was a human typing `python3 tv/hover_wilson.py`, and the
proof decayed to nothing with nothing saying so.

⚠ THIS READS THE STRING THE GATE ACTUALLY EXECUTES, not the file around it. `run_gates.py` now
carries a long comment explaining the fix, and that comment names `bank_into_proof_queue` — a scan
over the file would be satisfied by the prose describing the bug. The verdict script is a string
constant; reading only that is reading code. [[source-reading-guard]]

⚠ NOTHING HERE TOUCHES HIS LEDGER. The banking test points self_arming.LEDGER at a temp file.
[[feedback-fixtures-never-touch-live-data]]
"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


class TheGateBanksWhatItScores(unittest.TestCase):

    def test_the_verdict_script_feeds_the_proof_queue(self):
        import run_gates
        src = getattr(run_gates, "_HOVER_WILSON_VERDICT", None)
        self.assertIsInstance(src, str, "the hover-wilson verdict script is gone or renamed — this "
                                        "guard would then pass forever while measuring nothing")
        self.assertIn("HW.score()", src, "the verdict no longer scores — the extractor is broken, "
                                         "not the gate")
        self.assertIn("bank_into_proof_queue", src,
                      "the gate SCORES the sabotages and banks none of them. That is exactly the "
                      "state that left all five locks UNPROVEN with n=0 while the board said "
                      "miniauto.run had opened itself: evidence measured on every push and fed to "
                      "nothing.")

    def test_a_banking_failure_is_said_out_loud_and_not_swallowed(self):
        """A lock silently ceasing to be fed is how this defect survived. If banking raises, the
        gate must SAY so — a bare `except: pass` here would recreate the bug with a comment."""
        import re
        import run_gates
        src = run_gates._HOVER_WILSON_VERDICT
        self.assertIn("bank_into_proof_queue", src)
        # ⚠ MY FIRST VERSION OF THIS ASSERTION WAS GREEN FOR THE WRONG REASON, and my own sabotage
        # caught it: it looked for "print" anywhere in a 700-character window after the bank call,
        # and the SUCCESS branch prints right there. Replacing the error print with `pass` left it
        # passing. A window is not a scope. This reads the except BLOCK — the lines indented under
        # `except ... :` — and nothing else. [[sabotage-is-usually-the-wrong-one]]
        m = re.search(r"(?m)^(\s*)except\b[^\n]*:\n((?:\1[ \t]+[^\n]*\n|\s*\n)+)", src)
        self.assertIsNotNone(m, "banking is unguarded — a raise inside it would fail the whole "
                                "gate, so a transient banking error would block a push")
        body = m.group(2)
        self.assertIn("print", body,
                      "the except block swallows a banking failure silently. A lock quietly "
                      "ceasing to be fed is exactly how this defect survived from v2444 to now, "
                      "and a bare `pass` here recreates it wearing a try/except:\n%r" % body[:200])


class BankingIsIdempotent(unittest.TestCase):
    """Three runs must not read as three times the evidence. The gate now banks on EVERY push, so
    a non-folding bank would inflate n without a single new sabotage being attempted — and Wilson
    would climb on repetition alone, which is the one thing the denominator rule forbids."""

    def setUp(self):
        import self_arming
        self.sa = self_arming
        self._orig = self_arming.LEDGER
        self.tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        self.tmp.close()
        self_arming.LEDGER = self.tmp.name

    def tearDown(self):
        self.sa.LEDGER = self._orig
        try:
            os.unlink(self.tmp.name)
        except OSError:
            pass

    def test_banking_the_same_evidence_three_times_is_still_one_measurement(self):
        for _ in range(3):
            self.sa.bank("miniauto.run", "sabotage", "hover_wilson", n=48, k=48, ref="coordinate")
        # ⚠ self_arming has no state(); the folded view is score(lock). My first version of this
        # test called a function that does not exist and reported it as a FAILURE OF THE CODE. A
        # test that cannot find its own subject fails for its own reason, and reads exactly like a
        # real defect. [[feedback-suspect-the-instrument]]
        got = self.sa.score("miniauto.run")
        self.assertEqual(got["n"], 48,
                         "three identical runs banked as %s attempts — repetition became evidence, "
                         "which is the one thing the denominator rule forbids" % got["n"])
        self.assertEqual(got["k"], 48)

    def test_an_undeclared_source_is_refused(self):
        """A lock must never open on somebody else's proof."""
        with self.assertRaises(ValueError):
            self.sa.bank("miniauto.run", "sabotage", "some_other_harness", n=9, k=9, ref="x")



class TheCaseCensusCarriesItsDenominator(unittest.TestCase):
    """v2668 — a gate that PASSES while every one of its cases skipped must be named as such.

    ⚠ THE DEFECT, measured on CI run 33970973928 (v2666): the verdict read
    `✅ 138 gate(s) passed` and `⚠ 78 CASE(S) DID NOT RUN … test_chronicle_template=12`.
    Twelve looks like a footnote beside 2,783 tests — until you learn that suite HAS twelve
    tests, so it covered NOTHING on that venue and still counted as a passing gate.

    unittest's own summary line is `OK (skipped=26)` and never says how many ran, and
    run_gates drops the full blob for a PASS, so the census had a numerator and no
    denominator. [[zero-needs-a-denominator]] [[regression-guard]]

    This drives the REAL main() over a SYNTHETIC gate rather than reading the source around
    it — a scan for the ⛔ string would be satisfied by the comment that explains it.
    [[source-reading-guard]]
    """

    def _run(self, ran, skipped):
        import subprocess, sys as _s, tempfile, os as _o
        d = tempfile.mkdtemp(prefix="census_")
        fake = _o.path.join(d, "fake_suite.py")
        with open(fake, "w") as fh:
            fh.write("import sys\n"
                     "sys.stderr.write('\\nRan %d tests in 0.001s\\n\\nOK (skipped=%d)\\n')\n"
                     "sys.exit(0)\n" % (ran, skipped))
        drv = _o.path.join(d, "drive.py")
        with open(drv, "w") as fh:
            fh.write(
                "import sys\n"
                "sys.path.insert(0, %r)\n"
                "import run_gates as rg\n"
                     "# the live-state watch is unrelated to what this asserts, and its\n"
                     "# attribution is unreliable while HIS console writes tv/ during the\n"
                     "# run - it blamed the synthetic suite for a console write. Neutralised\n"
                     "# so the test measures the CENSUS and nothing else.\n"
                     "rg._LIVE_STATE = []\n"
                     "rg._NAMED_STATE_FILES = []\n"
                "g = rg.Gate('fake_census', [sys.executable, %r], 60, why='synthetic')\n"
                "rg.GATES = [g]\n"
                "rg.main(['run_gates.py', '--only', 'fake_census'])\n"
                % (HERE, fake))
        out = subprocess.run([_s.executable, drv], capture_output=True, text=True, timeout=180)
        return out.stdout + out.stderr

    def test_a_fully_dark_gate_is_named_not_merely_counted(self):
        txt = self._run(ran=7, skipped=7)
        self.assertIn("skipped=7 of 7", txt,
                      "the per-gate line must carry the denominator; without it 7 is unreadable")
        self.assertIn("COVERING NOTHING", txt,
                      "a gate that passed with 7 of 7 cases skipped is a PASS with an empty "
                      "denominator and must be named, not folded into a total")

    def test_RED_PROOF_a_partly_skipped_gate_is_NOT_called_dark(self):
        """If this fired for a partial skip the loud line would mean nothing."""
        txt = self._run(ran=19, skipped=1)
        self.assertIn("skipped=1 of 19", txt)
        self.assertNotIn("COVERING NOTHING", txt,
                         "1 of 19 is partial coverage, not zero - crying dark here would "
                         "make the verdict noise and it would stop being read")

    def test_the_census_line_itself_carries_the_ratio(self):
        txt = self._run(ran=19, skipped=1)
        self.assertRegex(txt, r"CASE\(S\) DID NOT RUN.*fake_census=1/19",
                         "the census must print skipped/ran, not a bare count")



class TheCensusSaysWhyNotOnlyHowMany(unittest.TestCase):
    """v2669 — the skipped cases must name their REASON, not only their count.

    v2668 gave the census a denominator (12 of 12). It still could not say WHAT stopped
    running, which is CF-3's own complaint one level down: *"a delta of 2 is not actionable,
    two names are"*. `unittest` emits a skip reason only at verbosity=2 and every suite here
    hardcodes `unittest.main(verbosity=1)` — argv wins, so run_gates appends `-v` to unittest
    suites only, parses the reasons out of the captured blob, and prints a short histogram.

    ⚠ The blob is CAPTURED, never streamed, and is dropped for a pass — so the CI log grows by
    a few histogram lines, not by test_control's 2,233 verbose ones.

    This drives the real `main()` with a real skipping suite. [[source-reading-guard]]
    """

    def _run_with_skip(self, reason):
        import subprocess, sys as _s, tempfile, os as _o
        d = tempfile.mkdtemp(prefix="reason_")
        fake = _o.path.join(d, "test_fake_reason.py")
        with open(fake, "w") as fh:
            fh.write("import unittest\n"
                     "class T(unittest.TestCase):\n"
                     "    def test_one(self):\n"
                     "        self.skipTest(%r)\n"
                     "    def test_two(self):\n"
                     "        self.skipTest(%r)\n"
                     "    def test_real(self):\n"
                     "        self.assertTrue(True)\n"
                     "if __name__ == '__main__':\n"
                     "    unittest.main(verbosity=1)\n" % (reason, reason))
        drv = _o.path.join(d, "drive.py")
        with open(drv, "w") as fh:
            fh.write("import sys\n"
                     "sys.path.insert(0, %r)\n"
                     "import run_gates as rg\n"
                     "# the live-state watch is unrelated to what this asserts, and its\n"
                     "# attribution is unreliable while HIS console writes tv/ during the\n"
                     "# run - it blamed the synthetic suite for a console write. Neutralised\n"
                     "# so the test measures the CENSUS and nothing else.\n"
                     "rg._LIVE_STATE = []\n"
                     "rg._NAMED_STATE_FILES = []\n"
                     "g = rg.Gate('fake_reason', [sys.executable, %r], 60, why='synthetic')\n"
                     "rg.GATES = [g]\n"
                     "rg.main(['run_gates.py', '--only', 'fake_reason'])\n" % (HERE, fake))
        out = subprocess.run([_s.executable, drv], capture_output=True, text=True, timeout=180)
        return out.stdout + out.stderr

    def test_the_reason_reaches_the_verdict(self):
        why = "his reels are not on this machine"
        txt = self._run_with_skip(why)
        self.assertIn("WHY THEY SKIPPED", txt,
                      "the census must carry reasons; a count alone is not actionable")
        self.assertIn(why, txt,
                      "the reason the case ITSELF gave must be printed verbatim - a paraphrase "
                      "would be my words standing in for the suite's")
        self.assertIn("2 x", txt, "identical reasons must aggregate, not repeat")

    def test_the_denominator_survives_the_v_flag(self):
        """-v changes unittest's output shape; the skipped=N of M line must still parse."""
        txt = self._run_with_skip("frame missing")
        self.assertIn("skipped=2 of 3", txt,
                      "adding -v must not break the v2668 denominator")

    def test_RED_PROOF_a_suite_with_no_skips_prints_no_histogram(self):
        import subprocess, sys as _s, tempfile, os as _o
        d = tempfile.mkdtemp(prefix="noskip_")
        fake = _o.path.join(d, "test_fake_clean.py")
        with open(fake, "w") as fh:
            fh.write("import unittest\n"
                     "class T(unittest.TestCase):\n"
                     "    def test_real(self):\n"
                     "        self.assertTrue(True)\n"
                     "if __name__ == '__main__':\n"
                     "    unittest.main(verbosity=1)\n")
        drv = _o.path.join(d, "drive.py")
        with open(drv, "w") as fh:
            fh.write("import sys\n"
                     "sys.path.insert(0, %r)\n"
                     "import run_gates as rg\n"
                     "# the live-state watch is unrelated to what this asserts, and its\n"
                     "# attribution is unreliable while HIS console writes tv/ during the\n"
                     "# run - it blamed the synthetic suite for a console write. Neutralised\n"
                     "# so the test measures the CENSUS and nothing else.\n"
                     "rg._LIVE_STATE = []\n"
                     "rg._NAMED_STATE_FILES = []\n"
                     "g = rg.Gate('fake_clean', [sys.executable, %r], 60, why='synthetic')\n"
                     "rg.GATES = [g]\n"
                     "rg.main(['run_gates.py', '--only', 'fake_clean'])\n" % (HERE, fake))
        out = subprocess.run([_s.executable, drv], capture_output=True, text=True, timeout=180)
        txt = out.stdout + out.stderr
        self.assertNotIn("WHY THEY SKIPPED", txt,
                         "a histogram printed for a suite with nothing skipped would be noise, "
                         "and a line that always prints stops being read")


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
