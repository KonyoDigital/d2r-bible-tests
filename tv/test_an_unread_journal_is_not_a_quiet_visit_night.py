# -*- coding: utf-8 -*-
"""REG-1797 — AN UNREAD JOURNAL IS NOT A QUIET VISIT NIGHT.

The journal reader returns a reason when the file will not read. The visit
list dropped that reason and handed back []. The tick then said there was no
unread visit. The chronicle doctor said to open the Chronicle. The offer said
ok. A missing file is still an empty list. A real visit is still listed,
read from the file through the one journal reader (REG-1824 - this was a
bare list from an older stand-in, a shim in production for a stub). A raise
is still a list, so a caller that only checks the list does not crash, and
ok is false. Reading one visit says the journal was not read, not that the
visit left it, and the screen says why when the offer is the reels alone.

Nothing here reads his live journal, and nothing starts a sweep.
RED_PROOF below. [[unknown-stays-unknown]]
"""
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

import chronicle_doctor as cd  # noqa: E402
import control_app as ca  # noqa: E402

_VISIT = {"lane": "chronicle", "kind": "visit", "ts": 5, "ledger": "uniques",
          "n": 2, "frames": ["a"]}
_WHY = "PermissionError: denied"


class AnUnreadJournalIsNotAQuietVisitNight(unittest.TestCase):

    def test_a_reason_is_not_an_empty_visit_list(self):
        with mock.patch.object(ca, "_kai_journal_rows", return_value=([], _WHY)):
            got = ca.chronicle_visits()
        self.assertIs(got.get("ok"), False, got)
        self.assertEqual(got.get("visits"), [])
        self.assertIn("PermissionError", got.get("why") or "")

    def test_a_missing_journal_is_still_an_empty_list(self):
        with mock.patch.object(ca, "_kai_journal_rows", return_value=([], None)):
            got = ca.chronicle_visits()
        self.assertIs(got.get("ok"), True, got)
        self.assertEqual(got.get("visits"), [])
        self.assertFalse(got.get("why"))

    def test_a_real_visit_is_still_listed(self):
        with mock.patch.object(ca, "_kai_journal_rows", return_value=([_VISIT], None)):
            got = ca.chronicle_visits()
        self.assertIs(got.get("ok"), True, got)
        self.assertEqual([v["ts"] for v in got["visits"]], [5])

    def _journal(self, text):
        d = tempfile.mkdtemp(prefix="visit1824_")
        self.addCleanup(shutil.rmtree, d, True)
        path = os.path.join(d, "sessions.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return mock.patch.object(ca, "_journal_path", lambda: path)

    def test_a_real_visit_in_the_file_is_still_listed(self):
        with self._journal(json.dumps({"lane": "deep"}) + "\n" + json.dumps(_VISIT) + "\n"):
            got = ca.chronicle_visits()
        self.assertIs(got.get("ok"), True, got)
        self.assertEqual([v["ts"] for v in got["visits"]], [5])

    def test_a_file_of_only_bad_lines_is_not_an_empty_visit_list(self):
        with self._journal("not json\n[1, 2]\n"):
            got = ca.chronicle_visits()
        self.assertIs(got.get("ok"), False, got)
        self.assertIn("parsed", got.get("why") or "")

    def test_reading_one_visit_does_not_say_it_left_the_journal(self):
        """REG-1824 — the sweep's own lookup said 'that visit is no longer in the journal' when the
        journal had not been read at all: REG-1797's sibling, left unswept."""
        saved = dict(ca._CHRON_JOB)
        try:
            with mock.patch.object(ca, "chronicle_visits",
                                   return_value={"ok": False, "visits": [], "why": _WHY, "spent": 0}):
                ca._chron_visit_run(5)
            err = ca._CHRON_JOB.get("error") or ""
        finally:
            ca._CHRON_JOB.clear()
            ca._CHRON_JOB.update(saved)
        self.assertIn("was not read", err)
        self.assertIn("PermissionError", err)
        self.assertNotIn("no longer in the journal", err)

    def test_a_raise_is_still_a_list_and_it_is_not_a_measurement(self):
        with mock.patch.object(ca, "_kai_journal_rows", side_effect=RuntimeError("boom")):
            got = ca.chronicle_visits()
        self.assertEqual(got.get("visits"), [])
        self.assertIs(got.get("ok"), False, got)
        self.assertIn("RuntimeError", got.get("why") or "")

    def _tick(self, payload):
        with mock.patch.object(ca, "_agent_alive", return_value=False), \
                mock.patch.object(ca, "chronicle_sweep_state", return_value={"running": False}), \
                mock.patch.object(ca, "_chron_autoread_done", return_value=set()), \
                mock.patch.object(ca, "chronicle_visits", return_value=payload):
            return ca.chronicle_autoread_tick()

    def test_the_tick_does_not_call_an_unread_journal_a_quiet_night(self):
        got = self._tick({"ok": False, "visits": [], "why": _WHY, "spent": 0})
        self.assertIs(got.get("ok"), False, got)
        self.assertNotIn("no unread visit", got.get("why") or "")
        self.assertIn("PermissionError", got.get("why") or "")

    def test_an_empty_readable_journal_is_still_no_unread_visit(self):
        got = self._tick({"ok": True, "visits": [], "spent": 0})
        self.assertIs(got.get("ok"), True, got)
        self.assertIn("no unread visit", got.get("why") or "")

    def test_the_doctor_does_not_send_him_to_open_the_chronicle(self):
        with mock.patch.object(ca, "chronicle_visits",
                               return_value={"ok": False, "visits": [], "why": _WHY, "spent": 0}):
            state, detail = cd._visits()
        self.assertEqual(state, cd.UNKNOWN, detail)
        self.assertNotIn("no in-game Chronicle visits", detail)
        self.assertIn("UNMEASURED", detail)
        self.assertIn("PermissionError", detail)

    def test_a_readable_empty_journal_still_says_no_visit_was_recorded(self):
        with mock.patch.object(ca, "chronicle_visits",
                               return_value={"ok": True, "visits": [], "spent": 0}):
            state, detail = cd._visits()
        self.assertEqual(state, cd.MISSING, detail)
        self.assertIn("no in-game Chronicle visits", detail)

    def test_a_recorded_visit_is_still_ok(self):
        with mock.patch.object(ca, "chronicle_visits",
                               return_value={"ok": True, "visits": [{"ledger": "uniques", "n": 1}],
                                             "spent": 0}):
            state, detail = cd._visits()
        self.assertEqual(state, cd.OK, detail)

    def test_an_empty_offer_does_not_pass_when_the_journal_was_not_read(self):
        with mock.patch.object(ca, "chronicle_visits",
                               return_value={"ok": False, "visits": [], "why": _WHY, "spent": 0}), \
                mock.patch.object(ca, "_unswept_chron_reels", return_value=[]):
            got = ca.chronicle_offer()
        self.assertIs(got.get("ok"), False, got)
        self.assertEqual(got.get("visits"), [])
        self.assertIn("PermissionError", got.get("why") or "")

    def test_a_focused_reel_is_still_offered_when_the_journal_was_not_read(self):
        reel = {"source": "reel", "ts": 9, "reel": "reel_s_1_1", "ledger": "uniques", "n": 4}
        with mock.patch.object(ca, "chronicle_visits",
                               return_value={"ok": False, "visits": [], "why": _WHY, "spent": 0}), \
                mock.patch.object(ca, "_unswept_chron_reels", return_value=[reel]):
            got = ca.chronicle_offer()
        self.assertIs(got.get("ok"), True, got)
        self.assertEqual(got.get("visits"), [reel])
        self.assertIn("PermissionError", got.get("visitWhy") or "")

    def test_the_offer_screen_does_not_hide_an_unread_journal(self):
        with open(os.path.join(HERE, "control_ui.html"), "rb") as fh:
            data = fh.read()
        needle = b"      if (j && j.ok === false) {\n"
        self.assertEqual(data.count(needle), 1)
        self.assertIn(b"not an empty visit list", data)


RED_PROOF = [
    {
        "why": "REG-1797 - a journal reason is dropped and the visit list comes back ok",
        "file": "control_app.py",
        "find": "    if why:\n        return {\"ok\": False, \"visits\": [], \"spent\": 0, \"why\": why}\n",
        "replace": "    if False:\n        return {\"ok\": False, \"visits\": [], \"spent\": 0, \"why\": why}\n",
        "matches": 1,
    },
    {
        "why": "REG-1797 - the tick treats an unread journal as no unread visit",
        "file": "control_app.py",
        "find": "    if got.get(\"ok\") is False:\n        return {\"ok\": False, \"why\": got.get(\"why\") or \"the journal was not read\"}\n",
        "replace": "    if False:\n        return {\"ok\": False, \"why\": got.get(\"why\") or \"the journal was not read\"}\n",
        "matches": 1,
    },
    {
        "why": "REG-1797 - an empty offer passes again when the journal was not read",
        "file": "control_app.py",
        "find": "    if journal_failed and not out:\n        return {\"ok\": False, \"visits\": [], \"spent\": 0,\n                \"why\": base.get(\"why\") or \"the journal was not read\"}\n",
        "replace": "    if False:\n        return {\"ok\": False, \"visits\": [], \"spent\": 0,\n                \"why\": base.get(\"why\") or \"the journal was not read\"}\n",
        "matches": 1,
    },
    {
        "why": "REG-1797 - the chronicle doctor tells him to open the Chronicle again",
        "file": "chronicle_doctor.py",
        "find": "    if got.get(\"ok\") is False:\n        import unknown_shelf as _us",
        "replace": "    if False:\n        import unknown_shelf as _us",
        "matches": 1,
    },
    {
        "why": "REG-1797 - the offer screen hides an unread journal again",
        "file": "control_ui.html",
        "find": "      if (j && j.ok === false) {\n",
        "replace": "      if (false) {\n",
        "matches": 1,
    },
    {
        "why": "REG-1824 - reading one visit says it left the journal when the journal was not read",
        "file": "control_app.py",
        "find": "        if _vl.get(\"ok\") is False:\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
