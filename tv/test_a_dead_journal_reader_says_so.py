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
import shutil
import sys
import tempfile
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

    def setUp(self):
        # REG-1824 — the one reader stats the file before it opens it, so a test that mocks open()
        # must hand it a file that is THERE. These used to ride whatever journal the host had (his,
        # on his Mac), and on a host with none the stat answered first and open() was never asked.
        d = tempfile.mkdtemp(prefix="journal_present_")
        self.addCleanup(shutil.rmtree, d, True)
        self.present = os.path.join(d, "sessions.jsonl")
        with open(self.present, "w", encoding="utf-8") as fh:
            fh.write("{}\n")
        p = mock.patch.object(ca, "_journal_path", lambda: self.present)
        p.start()
        self.addCleanup(p.stop)

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

    def test_a_blank_journal_is_still_a_quiet_read(self):
        d = tempfile.mkdtemp(prefix="journal_blank_")
        self.addCleanup(shutil.rmtree, d, True)
        path = os.path.join(d, "sessions.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n\n   \n")
        with mock.patch.object(ca, "_journal_path", lambda: path):
            rows, why = ca._kai_journal_rows(want_why=True)
        self.assertEqual([], rows)
        self.assertIsNone(why, "a blank journal is being reported as unreadable: %r" % why)

    def test_a_journal_of_only_bad_lines_is_not_a_quiet_night(self):
        d = tempfile.mkdtemp(prefix="journal_torn_")
        self.addCleanup(shutil.rmtree, d, True)
        path = os.path.join(d, "sessions.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("not json\n{also not\n42\n")
        with mock.patch.object(ca, "_journal_path", lambda: path):
            rows, why = ca._kai_journal_rows(want_why=True)
            bare = ca._kai_journal_rows()
        self.assertEqual([], rows)
        self.assertIsInstance(bare, list)
        self.assertEqual([], bare)
        self.assertTrue(why, "a journal of only bad lines returned no reason, so it reads as a quiet night")
        self.assertIn("none of its 3 line(s) parsed", why)

    def test_the_default_shape_is_unchanged(self):
        """five other call sites read this as a bare list and must stay untouched."""
        with mock.patch("builtins.open", mock.mock_open(read_data='{"a":1}\n')):
            got = ca._kai_journal_rows()
        self.assertIsInstance(got, list, "the default return shape changed under the other callers")

    # ── REG-1928: a bad byte is a bad LINE; a short tail is UNKNOWN, not empty ─────────────
    def _file(self, data):
        d = tempfile.mkdtemp(prefix="journal_bytes_")
        self.addCleanup(shutil.rmtree, d, True)
        path = os.path.join(d, "sessions.jsonl")
        with open(path, "wb") as fh:
            fh.write(data)
        return path

    def test_a_torn_utf8_byte_costs_its_line_not_the_journal(self):
        """REG-1928 - one write cut mid-character turned every beat in the file into UNKNOWN."""
        good = b'{"lane": "deep", "ts": 1}\n'
        torn = b'{"lane": "deep", "say": "a \xe2\x80'          # an em dash cut after 2 of its 3 bytes
        stray = b'{"lane": "deep", "say": "a \xff b"}\n'      # valid JSON around a byte that is not UTF-8
        path = self._file(good + torn + good + stray + good)
        with mock.patch.object(ca, "_journal_path", lambda: path):
            whole = ca._journal_read()
            tail = ca._journal_read(tail_bytes=600000)
        for name, got in (("whole", whole), ("tail", tail)):
            self.assertIsNone(got["why"], "%s: one bad byte made the whole journal UNKNOWN: %r" % (name, got["why"]))
            self.assertEqual(len(got["rows"]), 2, "%s: the beats beside a torn byte were dropped: %r" % (name, got))
            self.assertEqual(got["torn"], 2, "%s: a line with a byte that is not UTF-8 was kept as a beat" % name)

    def test_a_line_separator_inside_a_beat_does_not_split_it(self):
        """REG-1928 - str.splitlines cut a beat at U+2028, and both halves were counted torn."""
        beat = ('{"lane": "deep", "ts": 2, "say": "one two\u0085three"}\n').encode("utf-8")
        path = self._file(beat + b'{"lane": "deep", "ts": 3}\n')
        with mock.patch.object(ca, "_journal_path", lambda: path):
            got = ca._journal_read()
        self.assertEqual(got["torn"], 0, got)
        self.assertEqual([r.get("ts") for r in got["rows"]], [2, 3], "a beat holding U+2028 was cut in two")

    def test_a_tail_too_short_for_the_newest_row_is_not_an_empty_journal(self):
        """REG-1928 - the newest row was longer than the window, and the tail answered rows [] with no reason."""
        big = ('{"lane": "deep", "ts": 4, "frames": [%s]}\n'
               % ", ".join('"f_%d"' % i for i in range(3000))).encode("utf-8")
        path = self._file(b'{"lane": "deep", "ts": 1}\n' * 3 + big)
        self.assertGreater(len(big), 8192)
        with mock.patch.object(ca, "_journal_path", lambda: path):
            short = ca._journal_read(tail_bytes=8192)
            wide = ca._journal_read(tail_bytes=len(big) + 30)
            tail_rows = ca._journal_tail_rows(max_bytes=8192)
        self.assertEqual(short["rows"], [])
        self.assertTrue(short["why"], "a tail with no whole row read as a measured empty journal")
        self.assertIn("8192-byte tail", short["why"])
        self.assertIsNone(tail_rows, "the reader lamp was handed [] - 'no reads' - off a window too short to hold one")
        self.assertIsNone(wide["why"], wide["why"])
        self.assertEqual(wide["rows"][-1].get("ts"), 4, "a window wide enough lost the newest row")

    def test_a_tail_of_a_small_journal_is_still_its_rows(self):
        """the other direction: a file shorter than the window is read whole, and a blank tail is still empty."""
        path = self._file(b'{"lane": "deep", "ts": 1}\n{"lane": "deep", "ts": 2}\n')
        with mock.patch.object(ca, "_journal_path", lambda: path):
            got = ca._journal_read(tail_bytes=8192)
            lines = ca._journal_read(tail_lines=1)
        self.assertIsNone(got["why"])
        self.assertEqual([r["ts"] for r in got["rows"]], [1, 2])
        self.assertEqual([r["ts"] for r in lines["rows"]], [2], "tail_lines=1 counted the closing newline as a line")
        blank = self._file(b"\n\n\n\n")        # the window holds whole lines, and they are blank
        with mock.patch.object(ca, "_journal_path", lambda: blank):
            self.assertEqual(ca._journal_read(tail_bytes=2), {"rows": [], "why": None, "lines": 0, "torn": 0})

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

    def test_a_torn_journal_reaches_the_UNKNOWN_guard(self):
        """The reason has to arrive at the verdict. A stubbed why already does. This is the file."""
        d = tempfile.mkdtemp(prefix="journal_torn_status_")
        self.addCleanup(shutil.rmtree, d, True)
        path = os.path.join(d, "sessions.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("not json\n{also not\n")
        saved = ca.__dict__.get("_STATUS_JOURNAL_CACHE")
        try:
            ca._STATUS_JOURNAL_CACHE = None
            with mock.patch.object(ca, "_journal_path", lambda: path):
                st = ca.status_payload()
            sh = st.get("sessionHealth") or {}
            self.assertEqual("unknown", sh.get("verdict"),
                             "a journal of only bad lines still publishes %r" % sh.get("verdict"))
            self.assertNotEqual("idle", sh.get("verdict"))
        finally:
            ca._STATUS_JOURNAL_CACHE = saved


RED_PROOF = [
    {"why": "test_an_unreadable_journal_returns_a_REASON - a failed read hands back no reason (REG-1824: "
            "re-anchored onto _journal_read, the one reader)",
     "file": "control_app.py",
     "find": "    except Exception as exc:\n"
             "        return {\"rows\": [], \"why\": _why_of(exc), \"lines\": 0, \"torn\": 0}\n",
     "replace": "    except Exception as exc:\n"
                "        return {\"rows\": [], \"why\": None, \"lines\": 0, \"torn\": 0}\n",
     "matches": 1},
    ("control_app.py", 'raise RuntimeError("journal unread: %s" % _jwhy)',
     'pass  # was: raise',
     "test_an_unreadable_journal_reaches_the_UNKNOWN_guard"),
    {"why": "test_a_MISSING_journal_is_empty_and_honest - a journal that was never written reads as unreadable "
            "(REG-1824: re-anchored onto _journal_read, the one reader)",
     "file": "control_app.py",
     "find": "    except FileNotFoundError:\n"
             "        return {\"rows\": [], \"why\": None, \"lines\": 0, \"torn\": 0}   # gone between stat and open\n",
     "replace": "    except FileNotFoundError:\n"
                "        return {\"rows\": [], \"why\": \"FileNotFoundError\", \"lines\": 0, \"torn\": 0}\n",
     "matches": 1},
    {"why": "REG-1791 - a journal of only bad lines reads as a quiet night",
     "file": "control_app.py",
     "find": "    if out[\"lines\"] and not out[\"rows\"]:\n",
     "replace": "    if False and out[\"lines\"] and not out[\"rows\"]:\n",
     "matches": 1},
    {"why": "REG-1928 - the whole file is decoded strictly again, so one torn UTF-8 byte makes every beat UNKNOWN",
     "file": "control_app.py",
     "find": "            with open(path, encoding=\"utf-8\", errors=\"surrogateescape\") as fh:\n",
     "replace": "            with open(path, encoding=\"utf-8\") as fh:\n",
     "matches": 1},
    {"why": "REG-1928 - the tail window is decoded strictly again, so one torn UTF-8 byte makes the tail UNKNOWN",
     "file": "control_app.py",
     "find": "            text = data.decode(\"utf-8\", \"surrogateescape\")\n",
     "replace": "            text = data.decode(\"utf-8\")\n",
     "matches": 1},
    {"why": "REG-1928 - a line holding a byte that is not UTF-8 is kept as a beat",
     "file": "control_app.py",
     "find": "                ln.encode(\"utf-8\")             # a byte that was not UTF-8 makes THIS line torn, not the file\n",
     "replace": "                pass\n",
     "matches": 1},
    {"why": "REG-1928 - lines are cut by str.splitlines again, so a beat holding U+2028 becomes two torn halves",
     "file": "control_app.py",
     "find": "        lines = text.split(\"\\n\")\n        if lines and lines[-1] == \"\":\n",
     "replace": "        lines = text.splitlines()\n        if lines and lines[-1] == \"\":\n",
     "matches": 1},
    {"why": "REG-1928 - a tail window too short for the newest row reads as a measured empty journal",
     "file": "control_app.py",
     "find": "    elif _short:\n",
     "replace": "    elif False:\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
