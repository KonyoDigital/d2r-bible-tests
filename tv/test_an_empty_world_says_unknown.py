# -*- coding: utf-8 -*-
"""v3297 — AN EMPTY WORLD SAYS UNKNOWN. IT DOES NOT MANUFACTURE A CONFIDENT ZERO.

Four readers, one defect shape, all four measured on 2026-09-18 against a GUEST board whose world
is structurally JOURNAL-RICH AND LEDGER-EMPTY. Every durable "what was DONE" store is gitignored —
capture_doors.json, vault_swept.json, retro_triage.json, chronicle_swept.json, vault_accum.json,
river_stamp.jsonl and the rest — while the journal SEED is TRACKED. So a fresh clone inherits his
testimony about what HAPPENED and has no record of what was DONE, and every reader that coerced
that absence into `0` reported a defect that did not exist:

  1. THE ABSENT CAPTURE LEDGER — `_capture_door_load` swallows a missing file into `{}` and the
     report coerces each door to `int 0`. The invariant's UNKNOWN arm fires only on a NON-INT, a
     condition a missing FILE can never reach. It manufactured "journal says 56, ledger says 0"
     on a board that had never opened a door — the 56 being HIS imported journal.
  2. THE PRINTER-REACH DOCTOR — `printer_reach` already returns state=UNKNOWN with the honest
     sentence *"a filter that rejected NOTHING is not a filter that rejected EVERYTHING"*. The
     doctor branched on COUNTS ONLY and re-manufactured the populated-case confession over an
     empty world. The honest text existed upstream and was thrown away.
  3. THE SWEEP VERDICT — `stash_screen_open` returns None when its imports break and
     `panel_density` returns 0.0 for an unreadable reel, so a DEAD OCR TOOLCHAIN and a shelf with
     NO STASH PANELS printed the identical sentence. `gate_failures()` is the truth channel built
     for exactly this in v1854 and this verdict was never joined to it.
  4. THE ROUTE LANE — `runs == 0` conflated THREE OPPOSITE FACTS: a lane the roster stood down by
     design, a process younger than the sleep-first 90s tick, and a tick that raises upstream of
     the counter every round for ever. A deliberate absence, a young process and a failing loop
     are different findings and must not share a sentence.

⚠ WHY THIS IS ONE LAW AND NOT FOUR. Each fix is small and none is interesting alone; the SHAPE is
the finding, and a shape needs a guard that fails when any instance of it returns. A reader that
turns "nobody looked" into "I looked and found nothing" is the single most expensive bug class in
this repo, because the output is indistinguishable from a real measurement and nothing downstream
can recover the difference. [[zero-needs-a-denominator]] [[unknown-stays-unknown]]
[[a-wrong-answer-skips-the-fallback]]

⚠ THIS LAW IS BEHAVIOURAL WHERE IT CAN BE. Three of the four are exercised by CALLING the reader
against a world that is genuinely empty, rather than by asserting a name appears — because a
presence-law would go green over any of these fixes being deleted. The fourth (the route lane's
three-way split) is checked structurally AND by driving the state, since its inputs are module
globals a test can set. [[presence-law-vs-reachability-law]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

# Its docstrings and failure messages carry non-ASCII, and a unittest failure PRINTS them. On a
# cp1255 console that crash happens while REPORTING, so a clean tree exits non-zero for a reason
# that has nothing to do with the law. Caught by test_control's encoding-safety gate.
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()


class TestAnEmptyWorldSaysUnknown(unittest.TestCase):

    def test_an_absent_capture_ledger_reads_as_UNKNOWN_not_zero(self):
        """BEHAVIOURAL: point the ledger path at a file that does not exist and read the arm."""
        import unittest.mock as mock
        import control_app as ca
        import corroborate as co

        missing = os.path.join(HERE, ".no_such_capture_doors_%d.json" % os.getpid())
        self.assertFalse(os.path.exists(missing), "fixture path unexpectedly exists")

        # ⚠ THE INVARIANT RETURNS CALLABLES, NOT READINGS. My first cut scanned the tuple for a
        # None and failed on a tree whose fix is correct — the tuple holds `left`/`right` FUNCTIONS
        # and the numbers do not exist until they are called. Suspect the guard first: the code was
        # right and the test had the contract wrong. [[source-reading-guard]]
        with mock.patch.object(ca, "_capture_doors_path", lambda: missing):
            row = co._inv_every_door_counts_the_reels_it_opened()
            sides = [v for v in row if callable(v)]
            self.assertEqual(
                len(sides), 2,
                "the invariant no longer exposes exactly two callable sides (got %d); this law "
                "reads the RIGHT side by calling it, so a shape change makes it inert rather "
                "than wrong. [[the-unjoined-end]]" % len(sides))
            right_reading = sides[-1]()

        self.assertIsNone(
            right_reading,
            "with NO capture_doors.json on disk the ledger side read %r instead of None. An "
            "absent ledger became a measured number — that is how the 56-vs-0 disagreement was "
            "manufactured against a world that had never opened a door." % (right_reading,))

    def test_the_printer_row_passes_upstreams_UNKNOWN_through(self):
        """BEHAVIOURAL: upstream already says 'the contract was never asked'. Do not overwrite it."""
        import unittest.mock as mock
        import console_doctor as cd
        import printer_reach as pr

        honest = ("there is no seal store to read - 0 seals, so the contract was never asked to "
                  "admit anything")
        # ⚠⚠ THE SHAPE MATTERS AND MY FIRST FIXTURE HAD IT WRONG. report() returns its numbers
        # under `counts`; a flat dict trips the EARLIER `not r.get("counts")` arm, which also
        # returns UNKNOWN with r["why"] — so the test passed while never reaching the branch it
        # names, and the red-proof came back BLIND. The sabotage was fine; the FIXTURE could not
        # distinguish. [[regression-guard]] §5a question 2: does the test's own path reach the
        # line you broke?
        payload = {"state": "UNKNOWN", "why": honest,
                   "counts": {"seals": 0, "sealsSatisfyingContract": 0, "reels": 12, "joined": 0}}
        with mock.patch.object(pr, "report", lambda *a, **k: payload):
            state, why = cd._check_the_printer_can_reach_the_corpus()

        self.assertEqual(
            state, cd.UNKNOWN,
            "with 0 seals and upstream reporting UNKNOWN the doctor returned %r, not UNKNOWN. "
            "It is re-manufacturing the populated-case sentence over an empty world — the false "
            "confession 'NOT ONE of 0 seal(s) ... refused everything'." % (state,))
        self.assertIn(
            "never asked", why,
            "the doctor returned UNKNOWN but discarded upstream's own sentence. The honest text "
            "already exists in printer_reach; pass it through rather than inventing one. Got: %r"
            % (why,))

    def test_a_failing_stash_gate_is_an_answer_about_the_instrument(self):
        """BEHAVIOURAL: zero panels WHILE the gate was failing must not read as 'no panels'.

        ⚠⚠ v3300 — THE FIRST CUT OF THIS TEST HAD AN INERT MOCK AND PASSED FOR THE WRONG REASON.
        It patched `cd._hist_dirs` with create=True. MEASURED: `git grep _hist_dirs` over the whole
        tracked repo returns ONE match — that mock line. The name exists nowhere else, and an AST
        walk of `_check_the_sweep_would_find_something` shows its reachable calls are
        os.path.isdir / os.path.join / cr.reel_dirs / ca.gate_failures / vr.panel_density /
        vr.rank_by_panel. **The mock created an attribute nothing reads.**
        So the check ran against HIS REAL tv/frames/hist (gitignored; 799 entries on his Mac, 0
        tracked) and the test passed on his machine while FAILING ON CI — where the function returns
        at its first guard with "no frames/hist on this machine" and never reaches the INSTRUMENT
        branch at all. A fixture that exists on one machine. [[regression-guard]] [[test-venue]]

        THE FIX IS A REAL TREE, NOT A BIGGER MOCK: `hist` is derived as
        os.path.join(HERE, "frames", "hist"), so pointing cd.HERE at a temp dir drives the genuine
        path — os.path.isdir passes on a real directory, cr.reel_dirs lists real reel_* dirs, and
        load_index rebuilds an index from the frame names (which is why the fixture writes actual
        f_*.jpg bytes rather than empty dirs).
        """
        import shutil
        import tempfile
        import unittest.mock as mock
        import console_doctor as cd
        import control_app as ca
        import vault_retro as vr

        root = tempfile.mkdtemp(prefix="sweep_gate_")
        self.addCleanup(shutil.rmtree, root, True)
        hist = os.path.join(root, "frames", "hist")
        for reel in ("reel_a", "reel_b"):
            d = os.path.join(hist, reel)
            os.makedirs(d)
            # real bytes: reel_dirs drops a directory whose index cannot be rebuilt from frames
            with io.open(os.path.join(d, "f_1780000000000.jpg"), "wb") as fh:
                fh.write(b"\xff\xd8\xff\xe0" + b"0" * 64)

        bumps = iter([0, 3])          # gate_failures moved by 3 across the density pass
        with mock.patch.object(cd, "HERE", root), \
             mock.patch.object(ca, "gate_failures", lambda *a, **k: next(bumps)), \
             mock.patch.object(vr, "panel_density", lambda *a, **k: 0.0):
            state, why = cd._check_the_sweep_would_find_something()

        # ⚠ NO skipTest ESCAPE. The previous cut swallowed any exception into a skip, so a rename
        # would have made the whole case vanish silently — a skip is not a pass, and an escape
        # hatch on a law is a law that can stop existing without anyone noticing.

        self.assertEqual(
            state, cd.UNKNOWN,
            "every reel read density 0.0 WHILE the stash gate failed 3 times, and the check "
            "returned %r. A dead OCR toolchain and a shelf with no stash panels are opposite "
            "facts; only gate_failures() can tell them apart." % (state,))
        self.assertIn(
            "INSTRUMENT", (why or "").upper(),
            "the check went UNKNOWN but does not say the zero is about the instrument: %r" % (why,))

    def test_runs_zero_no_longer_conflates_three_opposite_facts(self):
        """The route lane must distinguish stood-down / young / failing. Driven, not grepped."""
        import control_app as ca

        # The three facts must each be REPRESENTABLE — a vocabulary that cannot say them is the
        # defect, one layer below the sentence.
        self.assertTrue(
            hasattr(ca, "_LANES_STOOD_DOWN"),
            "control_app exposes no _LANES_STOOD_DOWN, so a doctor row cannot tell a lane the "
            "roster deliberately skipped from a lane that died.")
        self.assertTrue(
            hasattr(ca, "_TRIAGE_TICK"),
            "control_app exposes no _TRIAGE_TICK, so 'the loop has not reached its first tick' "
            "and 'the loop raises every tick' are the same observation: runs == 0.")
        tick = getattr(ca, "_TRIAGE_TICK") or {}
        for field in ("attempts", "raised"):
            self.assertIn(
                field, tick,
                "_TRIAGE_TICK carries no %r. The doctor row reads it to separate a young process "
                "from a failing one; a missing field makes that branch unreachable and the row "
                "silently falls back to 'HAS NEVER RUN'." % field)

        # ATTEMPTS must be stamped BEFORE the tick runs, or a tick that raises never counts and
        # the failing case stays invisible — the exact hole this fix exists to close.
        import re
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            src = fh.read()
        i = src.find('_TRIAGE_TICK.get("attempts")')
        j = src.find("r = retro_triage_tick()", i if i > -1 else 0)
        self.assertGreater(i, -1, "nothing increments _TRIAGE_TICK['attempts'] at all")
        self.assertGreater(
            j, i,
            "the attempts counter is incremented AFTER retro_triage_tick() rather than before it. "
            "A tick that raises then never counts as an attempt, so a loop failing every 90s "
            "still reads as 'never ran' — the conflation this fix removes.")

        # ⚠ ORDER ALONE IS NOT ENOUGH, AND A SABOTAGE PROVED IT. Replacing `... or 0) + 1` with
        # `int(0 * (... or 0))` keeps the searched string, keeps it before the tick, and makes the
        # counter permanently 0 — the assertion above stayed GREEN through its own defeat. So EVAL
        # the expression against a known prior value and require it to actually rise.
        # [[regression-guard]] §5a: when a sabotage stays green, the test may simply be too weak.
        bol = src.rfind("\n", 0, i) + 1
        eol = src.find("\n", i)
        expr_line = src[bol:eol]
        k = expr_line.find('"attempts":')
        self.assertGreater(k, -1, "could not find the attempts expression on its own line: %r"
                                  % expr_line[:120])
        expr = expr_line[k + len('"attempts":'):].rstrip().rstrip(",")
        prior = 7
        got = eval(expr, {"int": int}, {"_TRIAGE_TICK": {"attempts": prior}})   # noqa: S307
        self.assertEqual(
            got, prior + 1,
            "the attempts expression computed %r from a prior of %d — it must INCREMENT. A counter "
            "that is stamped in the right place and never rises cannot separate 'the loop has not "
            "ticked yet' from 'the loop raises every tick', which is the whole point of the field. "
            "Expression: %s" % (got, prior, expr))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "deleting the absent-file guard lets a missing ledger read as a confident int 0",
        "file": "tv/corroborate.py",
        "find": "            if not os.path.exists(ca._capture_doors_path()):\n                return None\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "branching on counts alone re-manufactures the refused-everything sentence",
        "file": "tv/console_doctor.py",
        "find": '    if str(r.get("state") or "") == "UNKNOWN" or not seals:',
        "replace": '    if False:',
        "matches": 1,
    },
    {
        "why": "dropping the gate_failures check makes a dead OCR toolchain read as empty footage",
        "file": "tv/console_doctor.py",
        "find": "    if not withpanel and _gb:",
        "replace": "    if False:",
        "matches": 1,
    },
    {
        "why": "stamping the attempt AFTER the tick hides a loop that raises every round",
        "file": "tv/control_app.py",
        "find": '            globals()["_TRIAGE_TICK"] = {"attempts": int(_TRIAGE_TICK.get("attempts") or 0) + 1,',
        "replace": '            globals()["_TRIAGE_TICK"] = {"attempts": int(0 * (_TRIAGE_TICK.get("attempts") or 0)),',
        "matches": 1,
    },
]
