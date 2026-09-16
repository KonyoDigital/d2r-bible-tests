# -*- coding: utf-8 -*-
"""AN UNREADABLE JOURNAL IS UNKNOWN — AND THE OLD GATE PROVED THE PATH THAT CANNOT HAPPEN.

`_kai_journal_rows()` wrapped its whole read in `except Exception: pass` and returned `[]`. Six
call sites depend on it, and `status_payload` turns an empty tail into
`sessionHealth.verdict = "idle"`. So an absent, unreadable or permission-denied journal was
indistinguishable from a quiet night — a dead reader that looks healthy.

⚠⚠ THE GUARD FOR EXACTLY THIS WAS ALREADY WRITTEN, CORRECT, AND UNREACHABLE. `status_payload`
carries an `except` block whose own comment says it: *"a thrown journal walk is NOT an idle night.
idle + zeros is indistinguishable from nothing happened and that is how a dead reader looks
healthy. Unknown stays unknown."* Nothing could throw into it.

⚠⚠ AND ITS TEST PROVED THE UNREACHABLE HALF. `TestV1704UnknownStaysUnknown` mocks
`_kai_journal_rows` with `side_effect=RuntimeError` and asserts `verdict == "unknown"` — green
forever, over a live defect, because production never throws there. That test is not wrong and is
not deleted; it simply guards a path that only a mock can reach. THIS file guards the path that
real disks take. [[feedback-blind-fixture-green-gate]] [[regression-guard]]

⚠ A MISSING JOURNAL IS NOT AN UNREADABLE ONE, and collapsing them would be the opposite error: a
console that has never recorded HAS no journal, and `[]` is the measured truth there. Reporting
UNKNOWN for that would make every fresh install look broken. FileNotFoundError -> empty and
honest; anything else -> UNKNOWN. [[unknown-stays-unknown]]
"""
import io
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

os.environ.setdefault("TV_STUB", "1")
import control_app as ca


class ADeadJournalReaderSaysSo(unittest.TestCase):

    # ── the reader itself ────────────────────────────────────────────────────────────────
    def test_an_unreadable_journal_returns_a_REASON(self):
        with mock.patch("builtins.open", side_effect=PermissionError("denied")):
            rows, why = ca._kai_journal_rows(want_why=True)
        self.assertEqual([], rows)
        self.assertTrue(why, "an unreadable journal returned no reason, so the caller cannot tell "
                             "it from a quiet night — which is the whole defect")
        self.assertIn("PermissionError", why)

    def test_a_MISSING_journal_is_empty_and_honest(self):
        """the opposite error: a console that never recorded must not read as broken."""
        with mock.patch("builtins.open", side_effect=FileNotFoundError("nope")):
            rows, why = ca._kai_journal_rows(want_why=True)
        self.assertEqual([], rows)
        self.assertIsNone(why,
                          "a journal that was never written is being reported as UNREADABLE, so "
                          "every fresh install would publish UNKNOWN")

    def test_one_bad_LINE_is_not_an_unreadable_journal(self):
        data = '{"sessionId":"s1"}\nnot json at all\n{"sessionId":"s2"}\n'
        with mock.patch("builtins.open", mock.mock_open(read_data=data)):
            rows, why = ca._kai_journal_rows(want_why=True)
        self.assertIsNone(why, "a single unparseable line was reported as an unreadable journal")
        self.assertEqual(2, len(rows), "the good rows either side of a bad line were dropped")

    def test_the_default_shape_is_unchanged(self):
        """five other call sites read this as a bare list and must stay untouched."""
        with mock.patch("builtins.open", mock.mock_open(read_data='{"a":1}\n')):
            got = ca._kai_journal_rows()
        self.assertIsInstance(got, list, "the default return shape changed under the other callers")

    # ── the join: does the reason actually reach the verdict? ────────────────────────────
    def test_an_unreadable_journal_reaches_the_UNKNOWN_guard(self):
        """[[the-unjoined-end]] — the guard existed for versions and nothing could trigger it."""
        saved = ca.__dict__.get("_STATUS_JOURNAL_CACHE")
        try:
            ca._STATUS_JOURNAL_CACHE = None
            with mock.patch.object(ca, "_kai_journal_rows",
                                   side_effect=lambda want_why=False:
                                   ([], "PermissionError: denied") if want_why else []):
                st = ca.status_payload()
            sh = st.get("sessionHealth") or {}
            self.assertEqual("unknown", sh.get("verdict"),
                             "an unreadable journal still publishes %r — a dead reader wearing a "
                             "healthy verdict, which is exactly what the guard below it was "
                             "written to prevent" % sh.get("verdict"))
            self.assertNotEqual("idle", sh.get("verdict"))
        finally:
            ca._STATUS_JOURNAL_CACHE = saved

    def test_a_QUIET_night_still_reads_quiet(self):
        """the honesty check in the other direction: readable-and-empty is not UNKNOWN."""
        saved = ca.__dict__.get("_STATUS_JOURNAL_CACHE")
        try:
            ca._STATUS_JOURNAL_CACHE = None
            with mock.patch.object(ca, "_kai_journal_rows",
                                   side_effect=lambda want_why=False:
                                   ([], None) if want_why else []):
                st = ca.status_payload()
            sh = st.get("sessionHealth") or {}
            self.assertNotEqual("unknown", sh.get("verdict"),
                               "a journal that was READ and held nothing is being reported as "
                               "UNKNOWN — that makes a quiet console look broken")
        finally:
            ca._STATUS_JOURNAL_CACHE = saved


RED_PROOF = [
    ("control_app.py", "    except Exception as exc:\n        why = \"%s: %s\"",
     "    except Exception as exc:\n        why = None or \"\"  #",
     "test_an_unreadable_journal_returns_a_REASON"),
    ("control_app.py", 'raise RuntimeError("journal unread: %s" % _jwhy)',
     'pass  # was: raise',
     "test_an_unreadable_journal_reaches_the_UNKNOWN_guard"),
    ("control_app.py", "    except FileNotFoundError:\n        why = None",
     "    except FileNotFoundError:\n        why = 'FileNotFoundError'",
     "test_a_MISSING_journal_is_empty_and_honest"),
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
