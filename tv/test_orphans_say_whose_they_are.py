# -*- coding: utf-8 -*-
"""v2744 — THE STRAY-PROCESS ROW SAID "NOTHING OF OURS" HAVING TESTED NOTHING, AND FLAGGED PID 1.

`my_orphans.suspects()` shelled `ps` over the WHOLE MACHINE and kept every row above 20% CPU and
20 minutes that did not contain one of 30 hardcoded substrings. That was the complete definition of
"ours". `ppid` was parsed into the output dict and NEVER READ.

MEASURED against real command lines:
    /usr/sbin/coreaudiod           -> FLAGGED     /sbin/launchd (PID 1) -> FLAGGED
    .../MacOS/ControlCenter        -> FLAGGED
and `tv/.console_scars.json.corrupt` records eight earlier false positives of the same kind —
launchd at 28% CPU for 19,040 minutes among them. coreaudiod was the ninth, not the first.
⚠ AND WARN MAPS TO MISSING ON THE RAIL, so a system daemon rendered as the row's FAILURE state.

⚠⚠ WRONG IN BOTH DIRECTIONS. `any(k in cmd for k in KNOWN)` is a bare substring over the FULL
command line INCLUDING ARGUMENTS, and KNOWN holds "bird", "Terminal", "cloudd", "control_app.py":
    python3 /Users/konyo/blackbird/scan.py --forever  -> EXEMPT by ['bird']
    python3 crawl.py --title Terminal                 -> EXEMPT by ['Terminal']
So it flagged launchd while silently exempting a runaway of mine whose argv merely contained one of
those words. Growing the list makes the second class strictly worse.

=== WHY THIS IS NOT A SWAP TO A POSITIVE RULE, WHICH IS WHAT I FIRST INTENDED ===
The obvious fix is run_gates.py's rule — identity, not exclusion: ours if REGISTERED in the spawn
ledger, or NAMING THIS TREE, or HOLDING one of our ports.
⚠ MEASURED, AND IT WOULD HAVE MISSED THE ONE THAT MATTERED. On 2026-09-06 a runaway of mine pinned
a core at 100% for 52 minutes: `python3 -c "import io,re; ..."` over bible.html. NOT in the ledger
(53 rows, last written the previous day), did NOT name the tree (an inline -c script), held NO
port. All three positive witnesses fail on it. THE EXCLUSION RULE CAUGHT IT — it was the only
genuine suspect on the machine.

⇒ THE FIX IS A THIRD STATE, NOT A REPLACEMENT:
    OURS          -> WARN     something I started is burning a core; actionable, and mine
    UNATTRIBUTED  -> UNKNOWN  busy and old and nobody can say whose — genuinely unknown
    (exempt)      known system substring
[[unknown-stays-unknown]] [[i-own-everything-i-start]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import health_engine as H  # noqa: E402
import my_orphans as MO  # noqa: E402


def _row(rows):
    real = MO.suspects
    MO.suspects = lambda *a, **k: rows
    try:
        return H.check_orphans()
    finally:
        MO.suspects = real


def _p(pid="1", cpu=98.0, mins=52, cmd="python3 -c ...", ours=None):
    return {"pid": pid, "ppid": "1", "cpu": cpu, "minutes": mins, "cmd": cmd, "ours": ours}


class OrphansSayWhoseTheyAre(unittest.TestCase):

    # ── attribution itself ────────────────────────────────────────────────────────────────────
    def test_a_system_daemon_is_never_called_OURS(self):
        """coreaudiod, launchd and ControlCenter each matched only because they contain none of 30
        substrings. None of them is ours and nothing ever said so."""
        for cmd in ("/usr/sbin/coreaudiod", "/sbin/launchd",
                    "/System/Library/CoreServices/ControlCenter.app/Contents/MacOS/ControlCenter"):
            own, why = MO._attribute("99999", cmd)
            self.assertIsNot(own, True, "%s was attributed to us" % cmd)
            self.assertTrue(why, "the attribution carries no reason")

    def test_a_process_naming_THIS_TREE_is_ours(self):
        own, why = MO._attribute("99999",
                                 "python3 %s/control_app.py --open" % HERE)
        self.assertTrue(own, "a process running this repo's own code was not attributed to us")
        self.assertIn("tree", why)

    def test_an_UNATTRIBUTABLE_process_is_None_not_False(self):
        """⚠ THE DISTINCTION THE WHOLE FIX RESTS ON. False would mean 'measured, not ours' — a
        claim nothing here can make. None means nobody can say, and today's real 52-minute runaway
        was exactly that: no ledger row, no tree path, no port."""
        own, why = MO._attribute("99999", "python3 -c import io,re;s=io.open('x')")
        self.assertIsNone(own, "an unattributable process was given a definite answer")
        self.assertIn("nothing can say whose it is", why)

    # ── ⚠⚠ THE GRADING, WHICH IS WHERE THE FALSE ALARM ACTUALLY LANDED ────────────────────────
    def test_something_OF_OURS_busy_and_old_is_a_WARN(self):
        r = _row([_p(ours=True, cmd="python3 runaway.py")])
        self.assertEqual(H.WARN, r.get("state"),
                         "a process WE started, busy and old, must be actionable — that is the "
                         "28-hour core-burner class this sweep exists for")

    def test_an_UNATTRIBUTED_process_is_UNKNOWN_not_the_failure_state(self):
        """⚠ WARN maps to MISSING on the rail, so before this a system daemon rendered as the row's
        FAILURE state. UNKNOWN is what this repo has for 'nobody could say', and that is the true
        answer here."""
        r = _row([_p(ours=None, cmd="/usr/sbin/coreaudiod", cpu=30.0)])
        self.assertEqual(H.UNKNOWN, r.get("state"),
                         "an unattributable process still renders as a failure of ours")

    def test_an_UNATTRIBUTED_process_is_still_REPORTED(self):
        """⚠ NOT DISMISSED. The 52-minute runaway failed all three positive witnesses; a rule that
        only reported positive ownership would have said nothing about it at all."""
        r = _row([_p(ours=None, cmd="python3 -c ...", cpu=100.0, mins=52)])
        self.assertNotEqual(H.OK, r.get("state"),
                            "a process burning a core for 52 minutes was graded OK because nobody "
                            "could prove it was ours")
        # ⚠ the row's message field is `line` — `say` and `detail` do not exist on it, and
        # reading a key that is always absent makes an assertion that can never fail.
        self.assertIn("nothing can say whose", str(r.get("line") or ""))

    def test_OURS_takes_priority_when_both_are_present(self):
        r = _row([_p(ours=True, cmd="python3 mine.py"), _p(ours=None, cmd="coreaudiod")])
        self.assertEqual(H.WARN, r.get("state"),
                         "a real orphan of ours was downgraded because an unattributable process "
                         "was in the same list")

    def test_an_empty_sweep_no_longer_claims_something_it_never_tested(self):
        r = _row([])
        self.assertEqual(H.OK, r.get("state"))
        self.assertNotIn("of ours", str(r.get("line") or ""),
                         "the OK line still claims 'nothing of OURS', which is a statement about "
                         "ownership that the sweep does not establish")


if __name__ == "__main__":
    unittest.main(verbosity=2)
