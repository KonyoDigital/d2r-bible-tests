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


def _live(**kw):
    """A ledgerBackup payload from a loop that IS alive.

    ⚠ v2736 — the four message-classification laws below predate `lastTryMs` and went UNKNOWN the
    moment liveness was checked, because they described a loop with no attempt time. Their subject
    is how a MESSAGE is graded, so they must hand over a running loop or they quietly stop testing
    the thing they are named for. [[feedback-suspect-the-instrument]]
    """
    import time as _t
    row = {"lastTryMs": int((_t.time() - 60) * 1000)}
    row.update(kw)
    return row


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
        st, say = _verdict({"ok": True, "ledgerBackup": _live(
            writes=0, why="Can't find variable: dump", last="", counts=None)})
        self.assertEqual(D.MISSING, st,
                         "the exact live state of his console — 0 writes and a JS ReferenceError — "
                         "was not graded as a failure")
        self.assertIn("Can't find variable: dump", say,
                      "the refusal is not quoted. 'the backup is failing' sends someone reading "
                      "the loop; the message names the one line that is wrong.")

    def test_a_write_is_OK(self):
        st, _ = _verdict({"ok": True, "ledgerBackup": _live(
            writes=7, why="wrote ledger_2026-09-06_1830.json")})
        self.assertEqual(D.OK, st)

    def test_an_UNCHANGED_skip_is_OK_not_a_failure(self):
        """The loop deliberately skips when the counts have not moved. Grading a working dedupe as
        an outage would make this row cry wolf, and a row that cries wolf gets ignored — which is a
        slower way to have no watcher. [[sabotage-is-usually-the-wrong-one]]"""
        st, _ = _verdict({"ok": True, "ledgerBackup": _live(
            writes=3, why='unchanged since the last snapshot ({"foundLog": 419})')})
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
        st, _ = _verdict({"ok": True, "ledgerBackup": _live(writes=0, why="")})
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
        st, _ = _verdict({"ok": True, "ledgerBackup": _live(
            writes=2, why="some brand new message nobody has ever seen")})
        self.assertEqual(D.MISSING, st,
                         "an unrecognised message was treated as benign. The allowlist must be of "
                         "what is ALLOWED, never of what is known to be broken.")

    # ── ⚠⚠ v2736 — THE DEFECT A DIFFERENT MODEL FAMILY FOUND IN THIS VERY CHECK ───────────────
    def test_a_loop_that_DIED_after_one_write_is_not_OK(self):
        """`why` is STICKY. Nothing clears it, and the loop swallows every exception by design so
        one bad read cannot end it — so the last benign message outlives the loop that wrote it.

        REPRODUCED before the fix: writes=1, why="wrote ledger_2026-09-03_010101.json", the loop
        gone for three days -> this row graded **OK**.

        ⚠ THAT IS [[stale-reading]] COMMITTED INSIDE THE WATCHER BUILT TO CATCH A SILENT FAILURE —
        the age of the THING, not the age of the fetch. The message was fresh; the act was not.
        The fix is `lastTryMs`, stamped every ITERATION rather than every write, which is what
        separates a loop that is alive and legitimately skipping from a loop that is gone.
        """
        import time as _t
        st, say = _verdict({"ok": True, "ledgerBackup": {
            "writes": 1, "why": "wrote ledger_2026-09-03_010101.json",
            "lastTryMs": int((_t.time() - 3 * 86400) * 1000)}})
        self.assertEqual(D.MISSING, st,
                         "a loop dead for three days graded OK because its last message was benign")
        self.assertIn("not running", say)

    def test_a_loop_that_is_alive_and_SKIPPING_is_still_OK(self):
        """⚠ THE OTHER DIRECTION, AND IT MATTERS AS MUCH. The loop deliberately skips while the
        counts have not moved. If liveness were inferred from WRITES rather than attempts, a quiet
        board would read as a dead loop and this row would cry wolf every night."""
        import time as _t
        st, _ = _verdict({"ok": True, "ledgerBackup": {
            "writes": 3, "why": "unchanged since the last snapshot ({})",
            "lastTryMs": int((_t.time() - 60) * 1000)}})
        self.assertEqual(D.OK, st)

    def test_no_last_attempt_time_is_UNKNOWN_not_OK(self):
        """An older console publishes no lastTryMs. Its liveness is then unmeasured, and a sticky
        `why` cannot answer the question — so the honest verdict is UNKNOWN."""
        st, say = _verdict({"ok": True, "ledgerBackup": {"writes": 5, "why": "wrote x.json"}})
        self.assertEqual(D.UNKNOWN, st)
        self.assertIn("UNMEASURED", say)

    def test_the_loop_stamps_its_attempt_EVERY_ITERATION_not_every_write(self):
        """⚠ Pinned at the source, because the whole fix rests on it. Stamped on writes only, the
        field would be exactly as stale as the `why` it was added to replace."""
        import os as _o
        src = io.open(_o.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        blk = src.split("def _ledger_backup_loop(")[1].split("def ")[0]
        self.assertIn('_LEDGER_BACKUP_STATE["lastTryMs"] = int(time.time() * 1000)', blk,
                      "the loop no longer stamps its attempt time, so the liveness check above "
                      "is grading a field nobody writes")
        self.assertLess(blk.index('lastTryMs'), blk.index('_ledger_snapshot_once()'),
                        "the stamp must happen BEFORE the snapshot is attempted — stamped after, "
                        "a snapshot that hangs or throws would leave the loop looking dead")

    def test_the_timeout_is_long_enough_for_a_COLD_status(self):
        """MEASURED: /api/status takes 11.6s cold, 0.26s warm. At the 4s default this check reported
        'the console is not answering' against a console that was answering — a false UNKNOWN
        blaming the wrong thing, and how a real red gets dismissed as flakiness."""
        st, _ = _verdict({"ok": True, "ledgerBackup": _live(writes=1, why="wrote x.json")})
        fn = dict(D.CHECKS)["backup loop"]
        spy = _Answer({"ok": True, "ledgerBackup": _live(writes=1, why="wrote x.json")})
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
