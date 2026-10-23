# -*- coding: utf-8 -*-
"""REG-2615 - /api/status NEVER WAITS ON THE DISK FOR THE FORENSICS BADGE.

The ALT's status call took about 30 s, almost all of it in forensicsSummary; Dean's measured 423 ms of a 432 ms call
there (worst 38.8 s, task 172). It asked the disk about EVERY reel_* (an isfile each) on every status call, then
took the newest. Now the scan stops at the newest reel that has a report, and runs on one background thread at most
once per FORENSICS_SUM_TTL_S; the status call only ever reads the last answer.

  · DRIVEN: a status call while the disk hangs returns at once; one refresh is started, never two at a time.
  · DRIVEN: inside the TTL no refresh is started; after it, one is.
  · DRIVEN: the scan asks the disk once for a fresh newest reel, not once per reel; it still finds the newest
    reel that HAS a report when the newest has none yet, and /api/forensics reads the same reel.
RED_PROOF below.
"""
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
import control_app as ca  # noqa: E402


def _report():
    return {"items": [], "reads": []}


class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="fsum-")
        self.addCleanup(shutil.rmtree, self.d, True)
        p = mock.patch.object(ca, "HIST_DIR", self.d)
        p.start()
        self.addCleanup(p.stop)
        saved = dict(ca._FORENSICS_SUM_CACHE)
        ca._FORENSICS_SUM_CACHE.update(reel=None, mtime=None, val=None, at=None)
        ca._FORENSICS_SUM_BUSY["on"] = False
        self.addCleanup(ca._FORENSICS_SUM_CACHE.update, saved)
        self.addCleanup(ca._FORENSICS_SUM_BUSY.update, {"on": False})

    def reel(self, sid, report=True):
        os.makedirs(os.path.join(self.d, "reel_" + sid), exist_ok=True)
        if report:
            with open(os.path.join(self.d, "reel_" + sid, "kai_report.json"), "w") as fh:
                json.dump(_report(), fh)


class NeverWaits(Base):
    def test_a_hung_disk_does_not_hold_the_status_call(self):
        self.reel("20261023_120000")
        gate = threading.Event()
        real = os.listdir

        def hung(p):
            gate.wait(10)
            return real(p)
        with mock.patch.object(ca.os, "listdir", side_effect=hung):
            t0 = time.time()
            self.assertIsNone(ca._newest_forensics_summary())
            self.assertIsNone(ca._newest_forensics_summary())
            self.assertLess(time.time() - t0, 1.0, "the status call waited on the disk")
            self.assertTrue(ca._FORENSICS_SUM_BUSY["on"])
            gate.set()
            for _ in range(200):
                if not ca._FORENSICS_SUM_BUSY["on"]:
                    break
                time.sleep(0.02)
        self.assertIsNotNone(ca._newest_forensics_summary(), "the next poll has the badge")

    def test_one_refresh_at_a_time_and_once_per_ttl(self):
        started = []
        ca._newest_forensics_summary(now=1000.0, start=started.append)
        ca._newest_forensics_summary(now=1000.5, start=started.append)
        self.assertEqual(len(started), 1, "a second refresh started while one runs")
        self.reel("20261023_120000")
        started[0]()
        at = ca._FORENSICS_SUM_CACHE["at"]
        ca._newest_forensics_summary(now=at + 1, start=started.append)
        self.assertEqual(len(started), 1, "a refresh inside the TTL")
        ca._newest_forensics_summary(now=at + ca.FORENSICS_SUM_TTL_S + 1, start=started.append)
        self.assertEqual(len(started), 2)
        self.assertLessEqual(ca.FORENSICS_SUM_TTL_S, 120)


class Scan(Base):
    def test_one_disk_question_for_a_fresh_newest_reel(self):
        for i in range(300):
            self.reel("20260101_%06d" % i, report=False)
        self.reel("20261023_235959")
        real = os.path.isfile
        asked = []
        with mock.patch.object(ca.os.path, "isfile", side_effect=lambda p: asked.append(p) or real(p)):
            reel, rp = ca._newest_sealed_reel(self.d)
        self.assertEqual(reel, "reel_20261023_235959")
        self.assertEqual(len(asked), 1, "asked the disk about %d reels" % len(asked))

    def test_the_newest_reel_with_a_report_wins(self):
        self.reel("20261022_100000")
        self.reel("20261023_100000", report=False)
        self.assertEqual(ca._newest_sealed_reel(self.d)[0], "reel_20261022_100000")
        ca._refresh_forensics_summary()
        self.assertEqual(ca._FORENSICS_SUM_CACHE["reel"], "reel_20261022_100000")
        out = ca._forensics_payload("")
        self.assertTrue(out.get("ok"), out)

    def test_no_reels_is_none(self):
        self.assertIsNone(ca._refresh_forensics_summary())
        self.assertEqual(ca._forensics_payload("").get("total"), 0)


RED_PROOF = [
    {"matches": 1, "file": "control_app.py",
     "find": "                (start or (lambda fn: threading.Thread(target=fn, name=\"forensics-summary\", daemon=True).start()))(\n                    _refresh_forensics_summary)",
     "replace": "                _refresh_forensics_summary()",
     "why": "the refresh runs on the status call's own thread - a hung disk holds /api/status"},
    {"matches": 1, "file": "control_app.py", "find": "            go = not _FORENSICS_SUM_BUSY[\"on\"]\n",
     "replace": "            go = True\n", "why": "every status call starts another refresh while one runs"},
    {"matches": 1, "file": "control_app.py", "find": "    if at is None or not (0 <= now - at < FORENSICS_SUM_TTL_S):\n",
     "replace": "    if True:\n", "why": "no TTL: a refresh per status call"},
    {"matches": 1, "file": "control_app.py",
     "find": "    for d in sorted((d for d in os.listdir(hist) if d.startswith(\"reel_\")), reverse=True):\n        rp = os.path.join(hist, d, \"kai_report.json\")\n        if os.path.isfile(rp):\n            return d, rp\n    return None, None",
     "replace": "    found = [d for d in sorted((d for d in os.listdir(hist) if d.startswith(\"reel_\")), reverse=True)\n             if os.path.isfile(os.path.join(hist, d, \"kai_report.json\"))]\n    return (found[0], os.path.join(hist, found[0], \"kai_report.json\")) if found else (None, None)",
     "why": "the old scan: the disk is asked about every reel"},
    {"matches": 1, "file": "control_app.py", "find": "        _FORENSICS_SUM_BUSY[\"on\"] = False\n\n\ndef _newest_forensics_summary",
     "replace": "        pass\n\n\ndef _newest_forensics_summary", "why": "a finished refresh never frees the slot: the badge freezes"},
]


if __name__ == "__main__":
    unittest.main()
