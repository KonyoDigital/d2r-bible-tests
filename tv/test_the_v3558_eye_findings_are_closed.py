# -*- coding: utf-8 -*-
"""REG-1735 — THE v3558 SECOND EYE'S FINDINGS: FIVE REAL OF NINE, EACH CLOSED.

The cross-family look at v3558 (Grok CLI, 37,161 chars af202672..305754c0) returned nine. Real, closed here:

  · F1/F9 - the "dead" port was bound to find a free one and then CLOSED, so anything could bind it later and a law's ask
    would reach a stranger; two threads could pick two ports. It is held bound (never listening) for the process's
    life, under one lock.
  · F5/F6 - suite_verdict.inflight trusted a record with no numeric start time, or one dated in the future, while its
    pid lived (a reused pid) - a verdict nobody can age cannot keep a push waiting.
  · F7 - _absorb's JSON round-trip copy RAISED on a non-JSON value and aborted the absorb; it is a real deep copy now.
  · F4 - a self-prove lane that is OFF never refreshes the census, so the heart may not paint WATCHED over it even
    when the lane recorded no census word.
Not real here (BUGS.md REG-1735): F2 (no gate is needs_app, so no filename can collide), F3 (the boot sweep claims
nothing when it reads nothing; the doctor row says UNKNOWN), F8 (a port the caller chose is kept by design).
RED_PROOF below. [[unknown-stays-unknown]]
"""
import datetime
import json
import os
import shutil
import socket
import sys
import tempfile
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import run_gates as RG  # noqa: E402
import suite_verdict as SV  # noqa: E402
import vault_retro as vr  # noqa: E402
import control_app as ca  # noqa: E402
import heart2 as h2  # noqa: E402


class TheDeadPortStaysReserved(unittest.TestCase):

    def test_nothing_else_can_take_the_port_and_nothing_answers_on_it(self):
        port = int(RG.dead_console_port())
        s = socket.socket()
        try:
            with self.assertRaises(OSError, msg="the 'dead' port %d was free for anyone to bind" % port):
                s.bind(("127.0.0.1", port))
        finally:
            s.close()
        c = socket.socket()
        c.settimeout(1)
        try:
            self.assertNotEqual(c.connect_ex(("127.0.0.1", port)), 0, "something ANSWERED on the dead port")
        finally:
            c.close()
        self.assertEqual(RG.dead_console_port(), str(port), "a second ask chose a different port")


class AnUnageableInFlightRecordIsNotInFlight(unittest.TestCase):

    def setUp(self):
        d = tempfile.mkdtemp(prefix="inflight_unaged_")
        self.addCleanup(shutil.rmtree, d, True)
        self.path = os.path.join(d, "suite_verdicts.json")

    def _plant(self, rec):
        with open(self.path, "w") as fh:
            json.dump({"inflight": {"test_agent|k": dict(rec, pid=os.getpid())}}, fh)
        return SV.inflight("test_agent", "k", path=self.path)

    def test_premise_a_young_record_is_in_flight(self):
        self.assertIsNotNone(self._plant({"started": time.time() - 5}))

    def test_a_record_with_no_start_time_is_not_in_flight(self):
        self.assertIsNone(self._plant({}), "a record nobody can age kept a push waiting on a live pid")

    def test_a_record_dated_in_the_future_is_not_in_flight(self):
        self.assertIsNone(self._plant({"started": time.time() + 3600}), "a future-dated record was trusted")


class AnAbsorbCopiesAnyValue(unittest.TestCase):

    def test_a_non_json_value_is_filed_as_a_copy_without_aborting(self):
        have = {}
        base = {"name": "Shako", "lane": "stash", "kind": "item", "count": 1, "conf": 0.9, "lastSeenTs": 1}
        vr._absorb(have, dict(base, witnesses=[{"session": "s1", "frame": "f1", "lane": "stash"}]))
        seen = [datetime.datetime(2026, 10, 2, 19, 0)]
        vr._absorb(have, dict(base, witnesses=[{"session": "s1", "frame": "f1", "lane": "stash", "seenList": seen}]))
        w = have[("Shako", "stash")]["witnesses"][0]
        self.assertEqual(w.get("seenList"), [datetime.datetime(2026, 10, 2, 19, 0)], "PREMISE: the fact was not filed")
        seen.append("moved")
        self.assertEqual(len(w["seenList"]), 1, "the filed fact moved with the caller's list")


class AnOffLaneNeverLetsTheHeartSayWatched(unittest.TestCase):

    def setUp(self):
        d = tempfile.mkdtemp(prefix="h2_off_")
        self.addCleanup(shutil.rmtree, d, True)
        p = os.path.join(d, ".heart2.json")
        with open(p, "w") as fh:
            json.dump({"proved": 700, "unproven": 20, "blind": [], "declared": 720, "verdictAt": {}}, fh)
        patch = mock.patch.object(h2, "STATE", p)
        patch.start()
        self.addCleanup(patch.stop)
        saved = dict(ca._SELF_PROVE)
        self.addCleanup(lambda: (ca._SELF_PROVE.clear(), ca._SELF_PROVE.update(saved)))

    def test_an_off_lane_with_no_census_word_is_unknown(self):
        ca._SELF_PROVE.update(key="off", census=None, say="the self-prove lane is off")
        self.assertEqual(ca._heart2_census()["state"], "UNKNOWN",
                         "the lane is off - nothing will refresh the census - and the heart said WATCHED")

    def test_premise_an_off_lane_over_a_current_census_is_still_watched(self):
        ca._SELF_PROVE.update(key="off", census="current")
        self.assertEqual(ca._heart2_census()["state"], "WATCHED")


RED_PROOF = [
    {"why": "REG-1735 - the dead port is closed after it is chosen again: anything can bind it",
     "file": "run_gates.py",
     "find": "            _DEAD_PORT[\"sock\"] = _s\n",
     "replace": "            _s.close()\n",
     "matches": 1},
    {"why": "REG-1735 - an in-flight record with no start time keeps a push waiting again",
     "file": "suite_verdict.py",
     "find": "    if not isinstance(_st, (int, float)) or isinstance(_st, bool):\n        return None\n",
     "replace": "    if not isinstance(_st, (int, float)) or isinstance(_st, bool):\n        _st = time.time()\n",
     "matches": 1},
    {"why": "REG-1735 - a future-dated in-flight record is trusted again",
     "file": "suite_verdict.py",
     "find": "    if _age > RUN_TIMEOUT_S.get(name, 1500) + 120 or _age < -60:\n",
     "replace": "    if _age > RUN_TIMEOUT_S.get(name, 1500) + 120:\n",
     "matches": 1},
    {"why": "REG-1735 - _absorb copies through JSON again and aborts on a non-JSON value",
     "file": "vault_retro.py",
     "find": "                old[_f] = copy.deepcopy(_v)     # REG-1735 - any type (a JSON round trip raised on a non-JSON value)\n",
     "replace": "                old[_f] = json.loads(json.dumps(_v)) if isinstance(_v, (dict, list)) else _v\n",
     "matches": 1},
    {"why": "REG-1735 - an off lane with no census word lets the heart say WATCHED again",
     "file": "control_app.py",
     "find": "        _h2_off = (_SELF_PROVE or {}).get(\"key\") == \"off\"\n",
     "replace": "        _h2_off = False\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
