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


RED_PROOF = [
    {
        "why": 'the law requires this text in run_gates.py, where it occurs exactly once and in no other file the gate names; deleting it must turn the gate red',
        "file": 'run_gates.py',
        "find": 'HW.score()',
        "replace": '_HEART2_TAMPERED_',
        "matches": 1,
    },
    {
        "why": "v2940/H — restores unconditional banking in hover_wilson.main(), so merely LOOKING at the numbers writes evidence into his self-arming ledger. MEASURED: his ledger held 333 rows across 18 axes, roughly twenty of that day's pushes contributing. Reading is not evidence until someone decides it is.",
        "file": 'hover_wilson.py',
        "find": '    _bank = bank_into_proof_queue(rows) if "--bank" in argv else {"banked": [], "skipped": ["not banked: pass --bank to write evidence. An audit that writes is not an audit."]}\n',
        "replace": '    _bank = bank_into_proof_queue(rows)\n',
        "matches": 1,
    },
    {
        "why": "v2940/V — restores unconditional banking in vault_wilson.main(), so merely LOOKING at the numbers writes evidence into his self-arming ledger. MEASURED: his ledger held 333 rows across 18 axes, roughly twenty of that day's pushes contributing. Reading is not evidence until someone decides it is.",
        "file": 'vault_wilson.py',
        "find": '    b = bank_into_proof_queue(rows) if "--bank" in argv else {"banked": [], "skipped": ["not banked: pass --bank to write evidence. An audit that writes is not an audit."]}\n',
        "replace": '    b = bank_into_proof_queue(rows)\n',
        "matches": 1,
    },
    {
        "why": 'v2940/L — removes the SECOND door. vault_wilson has a live-witness bank besides the shared one, and guarding only the shared call left three CLI audits still moving the ledger 333 -> 334. Count the bank CALLS, not the files.',
        "file": 'vault_wilson.py',
        "find": '    elif "--bank" not in argv:\n        # ⚠⚠ v2940 (#75) — THE SECOND DOOR, and the first fix missed it. Guarding\n        # bank_into_proof_queue() alone still left this LIVE-witness bank writing on every plain\n        # `python3 tv/vault_wilson.py`. MEASURED: three CLI audits after that fix still moved the\n        # ledger 333 -> 334, and the row that landed was exactly `vault.apply / live / vault_live`.\n        # Counting the bank CALLS per file (4/2/3/1) and guarding only the shared one is how a\n        # sweep misses the sibling — the same shape as REG-942. [[sweep-dont-ask]]\n        live_note = ("a LIVE witness was read but NOT banked — pass --bank to write it. "\n                     "Reading is not evidence until someone decides it is.")\n',
        "replace": '',
        "matches": 1,
    },
]

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

    def test_a_PLAIN_CLI_AUDIT_banks_NOTHING(self):
        """⚠⚠ THE OTHER HALF OF THIS FILE'S RULE, AND IT MUST NOT BE CONFUSED WITH IT (#75).
        This file exists because THE GATE MUST BANK — v2464 measured `open 0 of 5, every lock n=0`
        when it did not. That stays true and is asserted above: the gate's verdict script calls
        `bank_into_proof_queue` directly, and nothing here weakens it.

        What was ALSO true, and wrong: all four wilson harnesses banked unconditionally from
        `main()`, so merely LOOKING at the numbers wrote evidence. MEASURED 2026-09-11 — his ledger
        held 333 rows across 18 axes, and roughly twenty of that day's pushes had contributed.
        Reading is not evidence until someone decides it is.

        ⚠ Guarding the shared `bank_into_proof_queue` call alone was NOT enough: vault_wilson has a
        SECOND, live-witness bank, and three CLI audits after the first fix still moved the ledger
        333 -> 334. Count the bank CALLS per file, not the files. [[sweep-dont-ask]]"""
        import subprocess
        for name in ("vault_wilson", "sweep_wilson", "prune_wilson", "hover_wilson"):
            d = tempfile.mkdtemp()
            led = os.path.join(d, "ledger.jsonl")
            env = dict(os.environ, TV_SELF_ARMING_LEDGER=led, TV_STUB="1")
            subprocess.run([sys.executable, os.path.join(HERE, name + ".py")],
                           env=env, cwd=HERE, capture_output=True, timeout=300)
            wrote = os.path.getsize(led) if os.path.exists(led) else 0
            self.assertEqual(0, wrote,
                             "%s wrote %d bytes of evidence on a plain audit run — reading is not "
                             "evidence until someone decides it is" % (name, wrote))

    def test_the_SAME_harness_DOES_bank_when_it_is_ASKED(self):
        """★ The other direction, or the law above is satisfied by a harness that can never bank at
        all — which would re-create the v2464 defect this file was written for."""
        import subprocess
        d = tempfile.mkdtemp()
        led = os.path.join(d, "ledger.jsonl")
        env = dict(os.environ, TV_SELF_ARMING_LEDGER=led, TV_STUB="1")
        subprocess.run([sys.executable, os.path.join(HERE, "hover_wilson.py"), "--bank"],
                       env=env, cwd=HERE, capture_output=True, timeout=300)
        wrote = os.path.getsize(led) if os.path.exists(led) else 0
        self.assertGreater(wrote, 0,
                           "hover_wilson --bank wrote nothing — a harness that can never bank "
                           "re-creates the exact state v2464 measured: every lock n=0")

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
                     "# ⚠ ON CI THIS RUNS INSIDE AN OUTER run_gates, WHICH ALREADY HOLDS THE\n"
                     "# TREE LOCK, so main() answered 'REFUSED - another gate run already\n"
                     "# holds this tree (pid 3000)' and every assertion here read that\n"
                     "# refusal instead of a verdict. The lock is real and correct; this\n"
                     "# synthetic harness is simply not a second claimant on the tree.\n"
                     "rg._claim_the_tree = lambda *a, **k: None\n"
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
                     "# ⚠ ON CI THIS RUNS INSIDE AN OUTER run_gates, WHICH ALREADY HOLDS THE\n"
                     "# TREE LOCK, so main() answered 'REFUSED - another gate run already\n"
                     "# holds this tree (pid 3000)' and every assertion here read that\n"
                     "# refusal instead of a verdict. The lock is real and correct; this\n"
                     "# synthetic harness is simply not a second claimant on the tree.\n"
                     "rg._claim_the_tree = lambda *a, **k: None\n"
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
                     "# ⚠ ON CI THIS RUNS INSIDE AN OUTER run_gates, WHICH ALREADY HOLDS THE\n"
                     "# TREE LOCK, so main() answered 'REFUSED - another gate run already\n"
                     "# holds this tree (pid 3000)' and every assertion here read that\n"
                     "# refusal instead of a verdict. The lock is real and correct; this\n"
                     "# synthetic harness is simply not a second claimant on the tree.\n"
                     "rg._claim_the_tree = lambda *a, **k: None\n"
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
