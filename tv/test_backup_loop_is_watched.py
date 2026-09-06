# -*- coding: utf-8 -*-
"""v2735 — THE WATCHER FOR THE LOOP THAT FAILED SILENTLY FOR A DAY.

Konyo, on being shown the restore wire: *"and all connected to the heart of the console obviously
right? is it needed? you tell me whatever you recommend"*.

The answer was yes, and the check went RED against his live console the moment it existed:

    backup loop -> MISSING
    the backup loop is REFUSING every snapshot: "Can't find variable: dump". It has written 0
    file(s) this run, and it retries every 10 minutes, so this repeats silently.

That is not a hypothetical the check was designed around — it is the state his machine was already
in, all day, with every gate green. `test_ledger_backup_covers_every_store` graded the SOURCE and
passed correctly; source is not a running board. The refusal lived in one string published at
`/api/status.ledgerBackup` that nothing read. [[the-unjoined-end]] [[feedback-verify-not-proxy]]

⚠ THIS FILE GRADES THE WATCHER, NOT THE LOOP. A watcher that quietly starts returning OK for every
input is worse than no watcher, because the row on his screen keeps saying the backup is fine.
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

import console_doctor as D  # noqa: E402

SRC = io.open(os.path.join(HERE, "console_doctor.py"), encoding="utf-8").read()


class _Answer(object):
    """Stands in for /api/status so every verdict can be forced without a live console."""

    def __init__(self, payload):
        self.payload = payload
        self.asked = []

    def __call__(self, path, timeout=4):
        self.asked.append((path, timeout))
        return self.payload


def _verdict(payload):
    fn = dict(D.CHECKS)["backup loop"]
    real, D._get = D._get, _Answer(payload)
    try:
        return fn()
    finally:
        D._get = real


class TheBackupLoopIsWatched(unittest.TestCase):

    def test_the_check_is_REGISTERED_not_merely_defined(self):
        """⚠ A doctor check that exists and is not in CHECKS runs never and grades nothing — this
        repo's most repeated defect, in its smallest form. [[the-unjoined-end]]"""
        self.assertIn("backup loop", dict(D.CHECKS),
                      "the backup-loop check is not registered in CHECKS, so it never runs")

    # ── ⚠⚠ THE VERDICT THAT ACTUALLY HAPPENED ─────────────────────────────────────────────────
    def test_a_refusing_loop_is_MISSING_and_QUOTES_the_refusal(self):
        st, say = _verdict({"ok": True, "ledgerBackup": {
            "writes": 0, "why": "Can't find variable: dump", "last": "", "counts": None}})
        self.assertEqual(D.MISSING, st,
                         "the exact live state of his console — 0 writes and a JS ReferenceError — "
                         "was not graded as a failure")
        self.assertIn("Can't find variable: dump", say,
                      "the refusal is not quoted. 'the backup is failing' sends someone reading "
                      "the loop; the message names the one line that is wrong.")

    def test_a_write_is_OK(self):
        st, _ = _verdict({"ok": True, "ledgerBackup": {
            "writes": 7, "why": "wrote ledger_2026-09-06_1830.json"}})
        self.assertEqual(D.OK, st)

    def test_an_UNCHANGED_skip_is_OK_not_a_failure(self):
        """The loop deliberately skips when the counts have not moved. Grading a working dedupe as
        an outage would make this row cry wolf, and a row that cries wolf gets ignored — which is a
        slower way to have no watcher. [[sabotage-is-usually-the-wrong-one]]"""
        st, _ = _verdict({"ok": True, "ledgerBackup": {
            "writes": 3, "why": 'unchanged since the last snapshot ({"foundLog": 419})'}})
        self.assertEqual(D.OK, st)

    # ── ⚠ UNKNOWN IS NEVER COLLAPSED INTO OK ──────────────────────────────────────────────────
    def test_a_console_that_did_not_answer_is_UNKNOWN(self):
        st, say = _verdict(None)
        self.assertEqual(D.UNKNOWN, st)
        self.assertIn("not the same as healthy", say,
                      "an unreachable console must not read as a passing backup")

    def test_a_loop_that_has_not_run_YET_is_UNKNOWN_not_OK(self):
        """The first snapshot comes 45s after boot. Grading that window as OK would make a
        freshly-restarted console always look healthy at the one moment it is least proven."""
        st, _ = _verdict({"ok": True, "ledgerBackup": {"writes": 0, "why": ""}})
        self.assertEqual(D.UNKNOWN, st,
                         "a loop that has reported nothing yet was graded as working")

    def test_a_status_with_NO_ledgerBackup_key_is_MISSING(self):
        """If /api/status stops publishing it, the only window onto the loop's refusals is gone.
        That is a blinding, and a blinded watcher must say so rather than pass."""
        st, say = _verdict({"ok": True})
        self.assertEqual(D.MISSING, st)
        self.assertIn("blind", say)

    def test_an_UNRECOGNISED_message_is_a_refusal_not_a_pass(self):
        """⚠ THE LOAD-BEARING DIRECTION. `_BACKUP_BENIGN` is a closed allowlist of what the loop is
        allowed to have done. Had it been a list of KNOWN ERRORS instead, "Can't find variable:
        dump" — an error nobody predicted — would have fallen through as healthy, which is exactly
        how this defect survived a day."""
        st, _ = _verdict({"ok": True, "ledgerBackup": {
            "writes": 2, "why": "some brand new message nobody has ever seen"}})
        self.assertEqual(D.MISSING, st,
                         "an unrecognised message was treated as benign. The allowlist must be of "
                         "what is ALLOWED, never of what is known to be broken.")

    def test_the_timeout_is_long_enough_for_a_COLD_status(self):
        """MEASURED: /api/status takes 11.6s cold, 0.26s warm. At the 4s default this check reported
        'the console is not answering' against a console that was answering — a false UNKNOWN
        blaming the wrong thing, and how a real red gets dismissed as flakiness."""
        st, _ = _verdict({"ok": True, "ledgerBackup": {"writes": 1, "why": "wrote x.json"}})
        fn = dict(D.CHECKS)["backup loop"]
        spy = _Answer({"ok": True, "ledgerBackup": {"writes": 1, "why": "wrote x.json"}})
        real, D._get = D._get, spy
        try:
            fn()
        finally:
            D._get = real
        self.assertTrue(spy.asked, "the check never asked the console anything")
        self.assertGreaterEqual(
            spy.asked[0][1], 12,
            "the check asks /api/status with a %ss timeout. Cold status is 11.6s, so it would "
            "report the console as unreachable on the first look after a relaunch."
            % spy.asked[0][1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
