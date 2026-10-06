# -*- coding: utf-8 -*-
"""#86 gap audit 22 (REG-1777) — A DOCTOR CHECK THAT DID NOT RUN IS NOT A CHECK THAT PASSED.

The replay row and the journal-generation row each sat in `except Exception: pass`. A raise
(_journal_path, an unreadable TV_SESSIONS) appended no row. The tally then saw fewer rows, all
green. A night that could not be read looked like one that passed.

  · DRIVEN: the journal will not read -> both rows are present, not ok, and say they could not
    be measured. The doctor's own payload carries them.
  · DRIVEN: an empty journal is still a measurement ("no journal rows yet", live=no).
  · DRIVEN: a blank file is that same empty measurement.
  · DRIVEN: a tail whose lines will not parse is not an empty journal.
  · DRIVEN: one bad line beside a real beat still names that beat's coverage.
  · DRIVEN: a readable journal names its coverage. 0% is a measured miss, not the unmeasured sentence.
Nothing here reads his journal or his shelf. RED_PROOF below. [[unknown-stays-unknown]]
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

import control_app as ca  # noqa: E402


def _rows(calls):
    return {c["id"]: c for c in calls}


class ADoctorCheckThatDidNotRun(unittest.TestCase):

    def test_an_unreadable_journal_is_not_a_passed_check(self):
        def boom(*_a, **_k):
            raise OSError("sessions unreadable")

        with mock.patch.object(ca, "_journal_path", boom):
            rows = _rows(ca._journal_doctor_rows())
        for cid in ("session_integrity", "journal_gens"):
            self.assertIn(cid, rows, "the %s row vanished, and a missing row reads as a pass" % cid)
            self.assertIs(rows[cid]["ok"], False, rows[cid])
            self.assertEqual(rows[cid]["severity"], "warn")
            self.assertIn("could not be measured", rows[cid]["detail"])
            self.assertIn("sessions unreadable", rows[cid]["detail"])
            self.assertIn("UNKNOWN", rows[cid]["detail"])
        passed = [c for c in rows.values() if c["ok"]]
        self.assertEqual(passed, [], "an unreadable journal still counted as passed: %r" % passed)

    def test_an_empty_journal_is_still_a_measurement(self):
        d = tempfile.mkdtemp(prefix="journal_empty_")
        self.addCleanup(shutil.rmtree, d, True)
        missing = os.path.join(d, "sessions.jsonl")
        with mock.patch.object(ca, "_journal_path", lambda: missing):
            rows = _rows(ca._journal_doctor_rows())
        self.assertIs(rows["session_integrity"]["ok"], True, rows["session_integrity"])
        self.assertIn("no journal rows yet", rows["session_integrity"]["detail"])
        self.assertNotIn("could not be measured", rows["session_integrity"]["detail"])
        self.assertIs(rows["journal_gens"]["ok"], True, rows["journal_gens"])
        self.assertIn("live=no", rows["journal_gens"]["detail"])

    def test_a_blank_journal_file_is_still_empty(self):
        d = tempfile.mkdtemp(prefix="journal_blank_")
        self.addCleanup(shutil.rmtree, d, True)
        path = os.path.join(d, "sessions.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n\n   \n")
        with mock.patch.object(ca, "_journal_path", lambda: path):
            rows = _rows(ca._journal_doctor_rows())
        self.assertIs(rows["session_integrity"]["ok"], True, rows["session_integrity"])
        self.assertIn("no journal rows yet", rows["session_integrity"]["detail"])
        self.assertNotIn("would not parse", rows["session_integrity"]["detail"])

    def test_a_journal_tail_that_will_not_parse_is_not_empty(self):
        d = tempfile.mkdtemp(prefix="journal_torn_")
        self.addCleanup(shutil.rmtree, d, True)
        path = os.path.join(d, "sessions.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("not json\n{also not\n42\n")
        with mock.patch.object(ca, "_journal_path", lambda: path):
            rows = _rows(ca._journal_doctor_rows())
        row = rows["session_integrity"]
        self.assertIs(row["ok"], False, row)
        self.assertEqual(row["severity"], "warn")
        self.assertIn("UNMEASURED", row["detail"])
        self.assertIn("would not parse", row["detail"])
        self.assertIn("3 journal line(s)", row["detail"])
        self.assertNotIn("no journal rows yet", row["detail"])
        self.assertNotIn("could not be measured", row["detail"])

    def test_one_bad_line_does_not_hide_a_real_beat(self):
        d = tempfile.mkdtemp(prefix="journal_mixed_")
        self.addCleanup(shutil.rmtree, d, True)
        path = os.path.join(d, "sessions.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("not json\n")
            fh.write(json.dumps({"frameId": "no_such_frame", "sessionId": "s1"}) + "\n")
        with mock.patch.object(ca, "_journal_path", lambda: path):
            rows = _rows(ca._journal_doctor_rows())
        row = rows["session_integrity"]
        self.assertIs(row["ok"], False, row)
        self.assertIn("frames 0%", row["detail"])
        self.assertNotIn("would not parse", row["detail"])
        self.assertNotIn("no journal rows yet", row["detail"])

    def test_a_readable_journal_names_its_coverage(self):
        d = tempfile.mkdtemp(prefix="journal_row_")
        self.addCleanup(shutil.rmtree, d, True)
        path = os.path.join(d, "sessions.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"frameId": "no_such_frame", "sessionId": "s1"}) + "\n")
        with mock.patch.object(ca, "_journal_path", lambda: path):
            rows = _rows(ca._journal_doctor_rows())
        self.assertIs(rows["session_integrity"]["ok"], False, rows["session_integrity"])
        self.assertIn("frames 0%", rows["session_integrity"]["detail"])
        self.assertNotIn("could not be measured", rows["session_integrity"]["detail"])
        self.assertIs(rows["journal_gens"]["ok"], True, rows["journal_gens"])
        self.assertIn("live=yes", rows["journal_gens"]["detail"])

    def test_the_doctor_payload_carries_the_unmeasured_rows(self):
        """The helper is not a second doctor. The payload he is served asks it."""
        def boom(*_a, **_k):
            raise OSError("sessions unreadable")

        with mock.patch.object(ca, "_journal_path", boom), \
                mock.patch.object(ca, "fleet_origin_status",
                                  lambda force_fetch=False: {"ok": True, "behind": 0, "head": "x", "howTo": ""}), \
                mock.patch.object(ca, "_reels_missing_index", lambda hist=None: []), \
                mock.patch.object(ca, "_screen_recording_ok_quick", lambda: True), \
                mock.patch.object(ca, "_one_capture_check",
                                  lambda alive=None: ca._chk("one_capture", True, "warn", "stub")), \
                mock.patch.object(ca, "_one_of_each_check",
                                  lambda: ca._chk("one_of_each", True, "warn", "stub")), \
                mock.patch.object(ca, "_extract_moving_facts",
                                  lambda: {"owed": 0, "memory": "absent", "ageKnown": True}):
            got = ca.doctor_payload()
        rows = _rows(got["checks"])
        for cid in ("session_integrity", "journal_gens"):
            self.assertIn(cid, rows, "the payload dropped %s" % cid)
            self.assertIs(rows[cid]["ok"], False, rows[cid])
            self.assertIn("could not be measured", rows[cid]["detail"])


RED_PROOF = [
    {"why": "REG-1777 - a journal that will not read drops the replay row, and a missing row reads as a pass",
     "file": "control_app.py",
     "find": "    except Exception as e:\n"
             "        checks.append(_chk(\n"
             "            \"session_integrity\", False, \"warn\",\n"
             "            \"could not be measured: %s - UNKNOWN, not a night that replayed\" % e))\n",
     "replace": "    except Exception:\n        pass\n",
     "matches": 1},
    {"why": "REG-1777 - a journal that will not read drops the generation row, and a missing row reads as a pass",
     "file": "control_app.py",
     "find": "    except Exception as e:\n"
             "        checks.append(_chk(\n"
             "            \"journal_gens\", False, \"warn\",\n"
             "            \"could not be measured: %s - UNKNOWN, not a journal that was read\" % e))\n",
     "replace": "    except Exception:\n        pass\n",
     "matches": 1},
    {"why": "REG-1790 - a journal tail that will not parse reads as a night that has not started",
     "file": "control_app.py",
     "find": "        if not rows and torn:\n"
             "            checks.append(_chk(\n"
             "                \"session_integrity\", False, \"warn\",\n"
             "                \"UNMEASURED: %d journal line(s) in the tail would not parse - not an empty journal\"\n"
             "                % torn))\n",
     "replace": "        if not rows and torn:\n"
               "            checks.append(_chk(\n"
               "                \"session_integrity\", True, \"warn\",\n"
               "                \"UNMEASURED: %d journal line(s) in the tail would not parse - not an empty journal\"\n"
               "                % torn))\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
