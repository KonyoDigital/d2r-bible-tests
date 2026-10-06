# -*- coding: utf-8 -*-
"""REG-1798 — AN UNREAD JOURNAL IS NOT A NIGHT WITH NO EYE.

The eye pulse asked for journal rows and dropped the reason. Zero timestamps
are also a console that has never seen an eye. The fleet then said no frame
yet. The lamps said off-air, no verify beat, and armed between sessions. A
missing file is still no eye yet. A real beat is still a timestamp. The closer
being unplugged is still that fact.

Nothing here reads his live journal, and nothing starts a sweep.
RED_PROOF below. [[unknown-stays-unknown]]
"""
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app as ca  # noqa: E402

_WHY = "PermissionError: denied"
_DEEP = {"lane": "deep", "completedTs": 50}
_ROWS = [
    _DEEP,
    {"lane": "verify", "ts": 40},
    {"lane": "kai", "completedTs": 30, "kai": {"missedFrames": 2}},
]
_MISSING = object()


class AnUnreadJournalIsNotANightWithNoEye(unittest.TestCase):

    def _pulse(self, got=None, exc=None):
        saved = ca.__dict__.get("_EYES_CACHE", _MISSING)
        ca.__dict__.pop("_EYES_CACHE", None)
        try:
            if exc is not None:
                patch = mock.patch.object(ca, "_kai_journal_rows", side_effect=exc)
            else:
                patch = mock.patch.object(ca, "_kai_journal_rows", return_value=got)
            with patch:
                out = ca._eyes_pulse()
                cached = "_EYES_CACHE" in ca.__dict__
            return out, cached
        finally:
            if saved is _MISSING:
                ca.__dict__.pop("_EYES_CACHE", None)
            else:
                ca._EYES_CACHE = saved

    def test_a_reason_is_not_a_night_with_no_eye(self):
        got, cached = self._pulse(([], _WHY))
        self.assertEqual(got.get("why"), _WHY)
        self.assertEqual(got.get("liveTs"), 0)
        self.assertFalse(cached, "a failed read was cached as no eye")

    def test_a_missing_journal_is_still_no_eye_yet(self):
        got, _cached = self._pulse(([], None))
        self.assertFalse(got.get("why"))
        self.assertEqual(got.get("liveTs"), 0)
        self.assertEqual(got.get("verifyTs"), 0)
        self.assertEqual(got.get("kaiTs"), 0)

    def test_a_real_beat_is_still_a_timestamp(self):
        got, _cached = self._pulse((_ROWS, None))
        self.assertFalse(got.get("why"))
        self.assertEqual(got.get("liveTs"), 50)
        self.assertEqual(got.get("verifyTs"), 40)
        self.assertEqual(got.get("kaiTs"), 30)
        self.assertEqual(got.get("kaiMissed"), 2)

    def test_a_bare_list_from_an_older_stand_in_is_still_the_rows(self):
        got, _cached = self._pulse(_ROWS)
        self.assertFalse(got.get("why"))
        self.assertEqual(got.get("liveTs"), 50)

    def test_a_raise_is_not_a_night_with_no_eye(self):
        got, cached = self._pulse(exc=RuntimeError("boom"))
        self.assertIn("RuntimeError", got.get("why") or "")
        self.assertIn("boom", got.get("why") or "")
        self.assertFalse(cached, "a raised read was cached as no eye")

    def test_a_failed_read_does_not_stick_for_the_next_beat(self):
        saved = ca.__dict__.get("_EYES_CACHE", _MISSING)
        ca.__dict__.pop("_EYES_CACHE", None)
        try:
            with mock.patch.object(ca, "_kai_journal_rows", return_value=([], _WHY)):
                first = ca._eyes_pulse()
            self.assertIn("PermissionError", first.get("why") or "")
            with mock.patch.object(ca, "_kai_journal_rows", return_value=([_DEEP], None)):
                second = ca._eyes_pulse()
            self.assertEqual(second.get("liveTs"), 50, second)
            self.assertFalse(second.get("why"))
        finally:
            if saved is _MISSING:
                ca.__dict__.pop("_EYES_CACHE", None)
            else:
                ca._EYES_CACHE = saved

    def test_the_fleet_does_not_say_no_frame_yet(self):
        with mock.patch.object(ca, "_eyes_pulse",
                               return_value={"liveTs": 0, "verifyTs": 0, "kaiTs": 0, "why": _WHY}):
            self.assertIsNone(ca._eye_for_wire())

    def test_a_quiet_readable_journal_is_still_no_frame_yet(self):
        with mock.patch.object(ca, "_eyes_pulse",
                               return_value={"liveTs": 0, "verifyTs": 0, "kaiTs": 0}):
            got = ca._eye_for_wire()
        self.assertIs(got["live"], False, got)
        self.assertIsNone(got["ageMs"])

    def test_the_lamps_do_not_call_an_unread_journal_a_quiet_night(self):
        with mock.patch.object(ca, "_eyes_pulse",
                               return_value={"liveTs": 0, "verifyTs": 0, "kaiTs": 0,
                                             "kaiMissed": None, "why": _WHY}):
            eng = ca._engines_status()
        live = eng["liveEye"]["note"]
        second = eng["secondEye"]["note"]
        kai = eng["kai"]["note"]
        self.assertIn("UNMEASURED", live)
        self.assertIn("PermissionError", live)
        self.assertNotIn("off-air", live)
        self.assertNotIn("between reads", live)
        self.assertIn("UNMEASURED", second)
        self.assertNotIn("no verify beat", second)
        self.assertNotIn("armed between sessions", kai)
        self.assertNotIn("closing / judging", kai)
        self.assertEqual(eng["liveEye"]["state"], "idle")

    def test_a_quiet_readable_journal_still_says_no_verify_beat(self):
        with mock.patch.object(ca, "_eyes_pulse",
                               return_value={"liveTs": 0, "verifyTs": 0, "kaiTs": 0,
                                             "kaiMissed": None}):
            eng = ca._engines_status()
        self.assertNotIn("UNMEASURED", eng["liveEye"]["note"])
        self.assertIn("no verify beat", eng["secondEye"]["note"])
        self.assertNotIn("UNMEASURED", eng["kai"]["note"])


RED_PROOF = [
    {
        "why": "REG-1798 - a journal reason is dropped and the eye pulse comes back as no eye",
        "file": "control_app.py",
        "find": "        # REG-1798 — an unreadable journal is not a night where no eye has acted.\n"
                "        if why:\n"
                "            out[\"why\"] = why\n"
                "            return out\n",
        "replace": "        # REG-1798 — an unreadable journal is not a night where no eye has acted.\n"
                   "        if False:\n"
                   "            out[\"why\"] = why\n"
                   "            return out\n",
        "matches": 1,
    },
    {
        "why": "REG-1798 - a raise is cached as a night where no eye has acted",
        "file": "control_app.py",
        "find": "        out[\"why\"] = \"%s: %s\" % (type(exc).__name__, str(exc)[:80])\n"
                "        return out\n",
        "replace": "        out[\"why\"] = None\n"
                   "        return out\n",
        "matches": 1,
    },
    {
        "why": "REG-1798 - the fleet says no frame yet when the journal was not read",
        "file": "control_app.py",
        "find": "    if eyes.get(\"why\"):\n        return None\n",
        "replace": "    if False:\n        return None\n",
        "matches": 1,
    },
    {
        "why": "REG-1798 - the lamps call an unread journal a quiet night again",
        "file": "control_app.py",
        "find": "    if unread:\n"
                "        _un = (\"UNMEASURED: the journal was not read (%s) — not a night with no eye\" % unread)\n",
        "replace": "    if False:\n"
                   "        _un = (\"UNMEASURED: the journal was not read (%s) — not a night with no eye\" % unread)\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
