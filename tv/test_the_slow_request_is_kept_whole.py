# -*- coding: utf-8 -*-
"""#28 — THE SLOWEST REQUEST IS KEPT WHOLE, AND IT SAYS WHETHER A SESSION WAS FILMING.

`/api/status` once took **52 seconds** while an ON AIR agent was recording, against ~24 ms idle.
Two things stopped that from ever being answerable:

1. **`worstSinceBoot` is a request that never happened.** It is the per-section MAXIMUM, each taken
   from a DIFFERENT call, so it sums to a total nothing ever spent. Measured on his live console:
   the maxima sum to **3,031 ms** while the last request took 244 ms. A reader chasing a 52-second
   event against that table is chasing a composite. [[zero-needs-a-denominator]]

2. **Every slow request was overwritten by the next ordinary one.** `last` holds only the most
   recent, and his console had already logged **6 requests over the 750 ms bar** with not one of
   their breakdowns surviving. The event this task exists to explain had happened repeatedly and
   left no record.

Now the slowest request is kept ENTIRE — its sections, its unattributed remainder, its slowest
component — persisted across a restart, and stamped with `capture`/`mode`/`agent` read from the
SAME payload the sections were measured in. That last part is not decoration: the whole question is
what the request spends 52 seconds on *while ON AIR films*, and a breakdown that cannot say whether
the capture was running answers half of it. [[stale-reading]]

FIRST CATCH, immediately on wiring: **4,449.3 ms**, `vaultAutoread` **3,426.8 ms — 77% of it** —
with `capture=False mode=off agent=False`. So a multi-second status request happens with NO session
at all, which narrows #28 before he ever presses record.
"""
import io
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

APP = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()


class TheCompositeIsLabelledAsOne(unittest.TestCase):

    def test_worst_since_boot_admits_it_is_not_a_request(self):
        self.assertIn('"worstSinceBootIsComposite": True', APP,
                      "worstSinceBoot is published without saying it is a per-section maximum "
                      "across DIFFERENT requests. Unlabelled, a reader sums it and chases a "
                      "request that never happened")

    def test_a_real_slowest_request_is_published_beside_it(self):
        self.assertIn('"worstRequest"', APP,
                      "only the composite is published; the slowest request that actually happened "
                      "is still overwritten by the next ordinary one")


class TheRecordCanAnswerTheQuestion(unittest.TestCase):
    """A breakdown that cannot say whether ON AIR was filming answers half of #28."""

    def setUp(self):
        i = APP.find('_STATUS_TIMING["worstRequest"] = _rec')
        self.assertGreater(i, 0, "the worst-request record is not written anywhere")
        j = APP.rfind("_rec = {", 0, i)
        self.assertGreater(j, 0, "could not find the record being built")
        self.blk = APP[j:i]

    def test_it_carries_the_recording_context(self):
        for field in ('"capture"', '"mode"', '"agent"'):
            self.assertIn(field, self.blk,
                          "the record drops %s, so it cannot say whether a session was filming — "
                          "which is the entire question #28 asks" % field)

    def test_the_context_comes_from_the_same_payload(self):
        """[[stale-reading]] — re-reading the state later describes a different moment."""
        for field in ("capture", "mode", "agent"):
            self.assertIn('_out.get("%s")' % field, self.blk,
                          "%r is not read from the payload this request just built, so it "
                          "describes whenever it was re-read rather than the moment the sections "
                          "were measured" % field)

    def test_it_carries_the_whole_breakdown_not_a_summary(self):
        for field in ('"sections"', '"unattributedMs"', '"slowest"', '"totalMs"'):
            self.assertIn(field, self.blk,
                          "the record drops %s — a slow request summarised is a slow request that "
                          "still cannot be diagnosed" % field)

    def test_it_stamps_when_and_which_version(self):
        for field in ('"atMs"', '"ver"'):
            self.assertIn(field, self.blk,
                          "the record drops %s, so a breakdown found on disk cannot be placed in "
                          "time or against the code that produced it" % field)


class ItSurvivesAndDoesNotChurn(unittest.TestCase):

    def test_it_is_persisted(self):
        self.assertIn("_status_worst_save(_rec)", APP,
                      "the slowest request lives only in memory, so the restart that follows a "
                      "wedged console takes the evidence with it")
        self.assertIn("_STATUS_WORST_PATH", APP, "no path is defined for the persisted record")

    def test_only_a_strictly_slower_request_replaces_it(self):
        i = APP.find('_prev = _STATUS_TIMING.get("worstRequest") or _status_worst_load()')
        self.assertGreater(i, 0, "the previous worst is not consulted before overwriting")
        blk = APP[i:i + 400]
        self.assertIn("_total > float((_prev or {}).get(\"totalMs\") or 0.0)", blk,
                      "the record is replaced without comparing against the previous worst, so an "
                      "ordinary request overwrites the 52-second one — exactly the defect that "
                      "lost the first six")

    def test_it_only_records_above_the_bar(self):
        i = APP.find('_prev = _STATUS_TIMING.get("worstRequest")')
        blk = APP[i:i + 400]
        self.assertIn("_total >= _STATUS_SLOW_MS", blk,
                      "every request is written to disk, not just the slow ones — a poll running "
                      "once a second would write a file once a second")

    def test_an_unreadable_record_is_none_not_a_fast_console(self):
        i = APP.find("def _status_worst_load")
        self.assertGreater(i, 0)
        blk = APP[i:APP.find("\ndef ", i + 10)]
        self.assertIn("return None", blk,
                      "a missing or unreadable record does not come back as None, so 'nothing has "
                      "ever been slow here' and 'the file would not load' read the same")
        self.assertNotIn("return {}", blk,
                         "an empty dict reads as a request with no sections rather than as an "
                         "absence")

    def test_saving_never_raises_into_the_request(self):
        i = APP.find("def _status_worst_save")
        self.assertGreater(i, 0)
        blk = APP[i:APP.find("\ndef ", i + 10)]
        self.assertIn("except Exception:", blk,
                      "a disk failure while recording a diagnostic would take down the status poll "
                      "the diagnostic exists to explain")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "dropping the capture context returns the record to answering half the question — "
               "a 52-second breakdown that cannot say whether ON AIR was filming",
        "file": "control_app.py",
        "find": '                "capture": _out.get("capture"),',
        "replace": '                "captureXX": None,',
        "matches": 1,
    },
    {
        "why": "replacing without comparing against the previous worst is the defect that lost the "
               "first six slow requests — an ordinary poll overwrites the slow one",
        "file": "control_app.py",
        "find": 'if _total >= _STATUS_SLOW_MS and _total > float((_prev or {}).get("totalMs") or 0.0):',
        "replace": 'if _total >= _STATUS_SLOW_MS:',
        "matches": 1,
    },
    {
        "why": "un-labelling the composite lets a reader sum per-section maxima from different "
               "requests and chase a request that never happened",
        "file": "control_app.py",
        "find": '            "worstSinceBootIsComposite": True,',
        "replace": '            "worstSinceBootIsCompositeXX": True,',
        "matches": 1,
    },
    {
        "why": "not persisting it means the restart that follows a wedged console takes the "
               "evidence with it — which is how this event stayed unexplained",
        "file": "control_app.py",
        "find": "            _status_worst_save(_rec)",
        "replace": "            pass",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
