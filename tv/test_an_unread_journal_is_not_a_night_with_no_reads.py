# -*- coding: utf-8 -*-
"""REG-1799 — AN UNREAD JOURNAL IS NOT A NIGHT WITH NO READS.

The receipt stream asked for journal rows and dropped the reason. An empty list
is also a console that has never recorded a read, and the screen says the reads
stream here when live. A missing file is still an empty list. A real read is
still a receipt. A raise is not cached as no reads.

Nothing here reads his live journal, and nothing starts a sweep.
RED_PROOF below. [[unknown-stays-unknown]]
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app as ca  # noqa: E402

_WHY = "PermissionError: denied"
_MISSING = object()
_ROW = {
    "lane": "deep", "scene": "stash", "area": "Harrogath",
    "names": ["Harlequin Crest"], "sessionId": "s1", "frameId": "f1",
    "ts": 1, "completedTs": 10, "gatePass": True,
}


def _names(rows):
    return [(r.get("refs") or {}).get("itemName") for r in rows]


class AnUnreadJournalIsNotANightWithNoReads(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rcpt1799_")
        self.journal = os.path.join(self.tmp, "sessions.jsonl")
        with io.open(self.journal, "w", encoding="utf-8") as fh:
            fh.write("")
        self.old = os.environ.get("TV_SESSIONS")
        os.environ["TV_SESSIONS"] = self.journal
        self.saved = ca.__dict__.get("_RECEIPTS_CACHE", _MISSING)
        ca.__dict__.pop("_RECEIPTS_CACHE", None)

    def tearDown(self):
        if self.old is None:
            os.environ.pop("TV_SESSIONS", None)
        else:
            os.environ["TV_SESSIONS"] = self.old
        if self.saved is _MISSING:
            ca.__dict__.pop("_RECEIPTS_CACHE", None)
        else:
            ca._RECEIPTS_CACHE = self.saved
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _call(self, got=None, exc=None, journal=None):
        if exc is not None:
            patch = mock.patch.object(ca, "_kai_journal_rows", side_effect=exc)
        elif journal is not None:
            patch = mock.patch.object(ca, "_kai_journal_rows", journal)
        else:
            patch = mock.patch.object(ca, "_kai_journal_rows", return_value=got)
        with patch:
            out = ca._receipts_stream()
            cached = "_RECEIPTS_CACHE" in ca.__dict__
        return out, cached

    def _write(self, text):
        with io.open(self.journal, "w", encoding="utf-8") as fh:
            fh.write(text)
        ca.__dict__.pop("_RECEIPTS_CACHE", None)

    def test_a_reason_is_not_a_night_with_no_reads(self):
        got, cached = self._call(([], _WHY))
        self.assertIsInstance(got, dict, got)
        self.assertEqual(got.get("why"), _WHY)
        self.assertEqual(got.get("rows"), [])
        self.assertFalse(cached, "a failed read was cached as no reads")

    def test_a_missing_file_is_still_an_empty_list(self):
        os.environ["TV_SESSIONS"] = os.path.join(self.tmp, "missing.jsonl")
        ca.__dict__.pop("_RECEIPTS_CACHE", None)
        got = ca._receipts_stream()
        self.assertEqual(got, [])
        self.assertIsInstance(got, list)

    def test_a_blank_file_is_still_an_empty_list(self):
        got = ca._receipts_stream()
        self.assertEqual(got, [])

    def test_a_real_read_is_still_a_receipt(self):
        self._write(json.dumps(_ROW) + "\n")
        got = ca._receipts_stream()
        self.assertIsInstance(got, list, got)
        self.assertIn("Harlequin Crest", _names(got))

    def test_one_bad_line_beside_a_read_is_still_that_read(self):
        self._write("not json\n" + json.dumps(_ROW) + "\n")
        got = ca._receipts_stream()
        self.assertIsInstance(got, list, got)
        self.assertIn("Harlequin Crest", _names(got))

    def test_a_journal_of_only_bad_lines_is_not_an_empty_night(self):
        self._write("not json\n{not a beat\n")
        got = ca._receipts_stream()
        self.assertIsInstance(got, dict, got)
        self.assertIn("parsed", got.get("why") or "")
        self.assertNotIn("_RECEIPTS_CACHE", ca.__dict__)

    def test_the_stream_asks_the_reader_for_its_reason(self):
        """REG-1824 — this was 'a bare list from an older stand-in', and production carried a
        TypeError fallback and a shape shim for it: test-only code on the receipts path. The
        reader always answers (rows, why) when asked, so the law is that the stream ASKS."""
        asked = []

        def reader(want_why=False):
            asked.append(want_why)
            return ([_ROW], None) if want_why else [_ROW]

        got, _cached = self._call(journal=reader)
        self.assertEqual(asked, [True], "the stream read the journal without asking why")
        self.assertIsInstance(got, list, got)
        self.assertIn("Harlequin Crest", _names(got))

    def test_a_raise_is_not_a_night_with_no_reads(self):
        got, cached = self._call(exc=RuntimeError("boom"))
        self.assertIsInstance(got, dict, got)
        self.assertIn("RuntimeError", got.get("why") or "")
        self.assertIn("boom", got.get("why") or "")
        self.assertFalse(cached, "a raised read was cached as no reads")

    def test_a_failed_read_does_not_stick_for_the_next_poll(self):
        with mock.patch.object(ca, "_kai_journal_rows", return_value=([], _WHY)):
            first = ca._receipts_stream()
        self.assertIsInstance(first, dict, first)
        with mock.patch.object(ca, "_kai_journal_rows", return_value=([_ROW], None)):
            second = ca._receipts_stream()
        self.assertIsInstance(second, list, second)
        self.assertIn("Harlequin Crest", _names(second))

    def test_a_failed_stat_does_not_reuse_an_empty_night(self):
        ca._RECEIPTS_CACHE = (None, [{"id": "stale"}])
        missing = os.path.join(self.tmp, "missing.jsonl")
        with mock.patch.object(ca, "_journal_path", return_value=missing), \
             mock.patch.object(ca, "_kai_journal_rows", return_value=([], _WHY)):
            got = ca._receipts_stream()
        self.assertIsInstance(got, dict, got)
        self.assertEqual(got.get("why"), _WHY)

    def test_the_wire_omits_an_unread_stream(self):
        rows, why = ca._receipts_for_wire({"ok": False, "rows": [], "why": _WHY})
        self.assertIsNone(rows)
        self.assertIn("PermissionError", why)

    def test_a_quiet_list_is_still_a_list_on_the_wire(self):
        rows, why = ca._receipts_for_wire([])
        self.assertEqual(rows, [])
        self.assertIsNone(why)

    def test_a_real_list_stays_on_the_wire(self):
        rows, why = ca._receipts_for_wire([{"id": "a"}])
        self.assertEqual(rows, [{"id": "a"}])
        self.assertIsNone(why)

    def test_a_stream_that_is_not_a_list_is_not_measured(self):
        rows, why = ca._receipts_for_wire(None)
        self.assertIsNone(rows)
        self.assertIn("not measured", why)

    def test_status_publishes_the_wire(self):
        with io.open(ca.__file__, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("_rc_rows, _rc_why = _receipts_for_wire(_rc_raw)", src)
        self.assertIn('"receipts": _rc_rows', src)
        self.assertIn('"receiptsWhy": _rc_why', src)

    def test_the_screen_does_not_call_an_unread_journal_a_quiet_night(self):
        with io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
            ui = fh.read()
        start = ui.find("if (window.__mindMode === 'receipts')")
        self.assertGreater(start, 0)
        window = ui[start:start + 1400]
        self.assertIn("var rcWhy = st.receiptsWhy;", window)
        why_at = window.find("not a night with no reads")
        rest_at = window.find("reads stream here when live")
        self.assertGreater(why_at, 0)
        self.assertGreater(rest_at, why_at)
        self.assertIn("rcWhy", window[why_at - 120:why_at])


RED_PROOF = [
    {
        "why": "REG-1799 - a journal reason is dropped and the receipt stream comes back empty",
        "file": "control_app.py",
        "find": "        # REG-1799 — an unreadable journal is not a night where no read landed.\n"
                "        if _rj_why:\n"
                "            return {\"ok\": False, \"rows\": [], \"why\": _rj_why}\n",
        "replace": "        # REG-1799 — an unreadable journal is not a night where no read landed.\n"
                   "        if False:\n"
                   "            return {\"ok\": False, \"rows\": [], \"why\": _rj_why}\n",
        "matches": 1,
    },
    {
        "why": "REG-1799 - a raise is handed back as a night with no reads",
        "file": "control_app.py",
        "find": "        # REG-1799 — a raise is not a night with no reads. Do not cache it.\n"
                "        return {\"ok\": False, \"rows\": [], \"why\": _why_of(exc)}\n",
        "replace": "        # REG-1799 — a raise is not a night with no reads. Do not cache it.\n"
                   "        return []\n",
        "matches": 1,
    },
    {
        "why": "REG-1799 - a failed stat reuses a cached empty night",
        "file": "control_app.py",
        "find": "    # REG-1799 — a failed stat is not a cached empty night. None must not hit it.\n"
                "    if key is not None and c and c[0] == key:\n"
                "        return c[1]\n",
        "replace": "    # REG-1799 — a failed stat is not a cached empty night. None must not hit it.\n"
                   "    if c and c[0] == key:\n"
                   "        return c[1]\n",
        "matches": 1,
    },
    {
        "why": "REG-1799 - the wire publishes an unread stream as a measured night",
        "file": "control_app.py",
        "find": "    if isinstance(raw, dict) and raw.get(\"why\"):\n"
                "        return None, str(raw.get(\"why\"))[:200]\n",
        "replace": "    if False and isinstance(raw, dict) and raw.get(\"why\"):\n"
                   "        return None, str(raw.get(\"why\"))[:200]\n",
        "matches": 1,
    },
    {
        "why": "REG-1799 - the screen calls an unread journal a quiet night again",
        "file": "control_ui.html",
        "find": "        : (rcWhy\n"
                "          ? '<div class=\"empty\">UNMEASURED: the journal was not read (' + esc(rcWhy) + ') — not a night with no reads</div>'\n"
                "          : '<div class=\"empty\">— the AI\\'s reads stream here when live · click one to jump to it · hover for its frame —</div>');\n",
        "replace": "        : '<div class=\"empty\">— the AI\\'s reads stream here when live · click one to jump to it · hover for its frame —</div>';\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
