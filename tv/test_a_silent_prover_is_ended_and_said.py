# -*- coding: utf-8 -*-
"""REG-1674 - A PROVER THAT HAS GONE SILENT IS ENDED, AND SAYS SO; ITS LOG IS A HEARTBEAT.

MEASURED on his ALT 2026-10-01: the self-prove lane's log did not move from 13:13 to 14:25 while 15 gates were proved -
the prover's output went to a FILE, so Python held it in 8 KB blocks, and a working prover looked exactly like a hung
one. His words: "make sure its all wired and connected to where its needed and a stale safegaurd for this so it doesnt
happen future wise", then "connect it to the heart of the conosle".

Driven through the REAL self_prove.tick (only the machine is faked: which pid is ours, the kill, the spawn):
  1. the log is unbuffered, so its age is a heartbeat (spawn's env);
  2. a log still past this slice's HONEST bound (silent_bound_s: three runs at their deadline) ends the prover through
     the lane's one kill door, keeps its gates owed and proves them AFTER the others; the lane's key says "silent";
  3. a log still writing is left alone, and the lane reports how long ago it moved; an unreadable log is UNKNOWN,
     never silent;
  4. the console doctor reads "silent" as a warning - it is not on the healthy list - and the fleet beacon carries
     the key, so the stall is seen where the heart looks.
RED_PROOF below.
"""
import ast
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
from console_safe import enable as _console_safe_enable  # noqa: E402  (its red-proofs carry non-ASCII)
_console_safe_enable()
import self_prove as SP  # noqa: E402

PID, BIRTH = 4242, 1234.5
INSTALLED = ("installed", "a clean installed tree")


def _census(owed, fp="fp1"):
    return {"state": "stale", "why": "fixture", "fingerprint": fp, "owed": len(owed),
            "owedGates": [(n, 1) for n in owed], "owedWhy": "fixture: %d owed" % len(owed)}


class _Lane(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="silent_prover_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.store = os.path.join(self.d, ".self_prove.json")
        self.log = self.store + ".log"
        self.killed, self.spawned = [], []
        self._started = dict(SP._STARTED)
        SP._STARTED.update(pid=None, birth=None)
        self.addCleanup(lambda: (SP._STARTED.clear(), SP._STARTED.update(self._started)))
        self.alive = {PID}
        for name, fake in (("identity", lambda pid, birth: pid in self.alive),
                           ("_gate_costs", lambda path=None: {})):
            p = mock.patch.object(SP, name, fake)
            p.start()
            self.addCleanup(p.stop)

    def _running(self, gates=("gate_a", "gate_b")):
        with io.open(self.store, "w", encoding="utf-8") as fh:
            json.dump({"pid": PID, "pidBirth": BIRTH, "startedFor": "fp1", "sliceGates": list(gates)}, fh)

    def _log(self, age_s, text="     test_gate_a[0]   PROVEN (1 match(es) tampered -> red)\n"):
        with io.open(self.log, "w", encoding="utf-8") as fh:
            fh.write(text)
        t = time.time() - age_s
        os.utime(self.log, (t, t))

    def _kill(self, pid, birth=None):
        self.killed.append(pid)
        self.alive.discard(pid)
        return True

    def _spawn(self, log_path, names=None):
        self.spawned.append(names)
        return 999_999_3

    def _tick(self, census):
        return SP.tick(now_s=time.time(), busy=3.0, tree=INSTALLED, census=census, path=self.store,
                       spawn_fn=self._spawn, env={}, playing=False, free=8000, kill_fn=self._kill)


class ASilentProverIsEndedAndSaid(_Lane):

    def test_a_prover_silent_past_its_bound_is_ended_and_said(self):
        self._running()
        bound = SP.silent_bound_s(["gate_a", "gate_b"])
        self._log(bound + 120)
        r = self._tick(_census(["gate_a", "gate_b", "gate_c"]))
        self.assertEqual(self.killed, [PID], "a prover silent past its honest bound was left holding the lane: %r" % r)
        self.assertEqual(r.get("key"), "silent", r)
        self.assertIn("heart2 itself was stuck", r.get("say") or "")
        self.assertEqual(r.get("stalled"), 1)
        mem = SP.load(self.store)
        self.assertEqual(mem.get("stalledGates"), ["gate_a", "gate_b"])
        self.assertIsNone(mem.get("pid"), "the ended prover is still tracked")
        self.assertEqual(self.spawned, [], "a slice started in the same tick that said 'silent' - nobody would see it")

    def test_a_prover_still_writing_is_left_alone_and_its_heartbeat_is_reported(self):
        self._running()
        self._log(90)
        r = self._tick(_census(["gate_a", "gate_b"]))
        self.assertEqual(self.killed, [], "a prover that wrote 90 s ago was ended")
        self.assertEqual(r.get("key"), "running", r)
        self.assertLess(r.get("logAgeS"), 120)
        self.assertIn("its log last moved", r.get("say") or "")
        self.assertIn("test_gate_a[0]", r.get("say") or "", "the lane does not say what the prover last wrote")

    def test_an_unreadable_log_is_never_silent(self):
        self._running()
        r = self._tick(_census(["gate_a", "gate_b"]))      # no log file at all
        self.assertEqual(self.killed, [], "a prover was ended on a log nobody could read")
        self.assertIsNone(r.get("logAgeS"))

    def test_the_stalled_gates_are_proved_after_the_others(self):
        self._running()
        self._log(SP.silent_bound_s(["gate_a", "gate_b"]) + 120)
        self._tick(_census(["gate_a", "gate_b", "gate_c"]))
        self._tick(_census(["gate_a", "gate_b", "gate_c"]))            # the next tick: nothing running
        self.assertEqual(self.spawned, [["gate_c"]],
                         "the gates that hung were planned first again, holding every other proof behind them: %r"
                         % self.spawned)

    def test_the_stalled_gates_are_retried_once_nothing_else_is_owed(self):
        self._running()
        self._log(SP.silent_bound_s(["gate_a", "gate_b"]) + 120)
        self._tick(_census(["gate_a", "gate_b"]))
        self._tick(_census(["gate_a", "gate_b"]))
        self.assertEqual(self.spawned, [["gate_a", "gate_b"]], "a stalled gate was dropped instead of retried last")


class TheLogIsAHeartbeat(unittest.TestCase):

    def test_spawn_hands_heart2_an_unbuffered_log_and_the_one_deadline_scale(self):
        seen = {}

        class _P(object):
            pid = 1

        def popen(cmd, **kw):
            seen["env"] = kw.get("env") or {}
            return _P()
        d = tempfile.mkdtemp(prefix="silent_spawn_")
        self.addCleanup(shutil.rmtree, d, True)
        SP.spawn(os.path.join(d, "log"), popen=popen, workers=1, names=["g1"])
        self.assertEqual(seen["env"].get("PYTHONUNBUFFERED"), "1",
                         "the prover's log is block-buffered again: a working prover and a hung one look the same")
        self.assertEqual(seen["env"].get("HEART2_DEADLINE_SCALE"), str(SP.PROVER_DEADLINE_SCALE),
                         "heart2's deadline scale and the silence bound's scale are two numbers again")

    def test_the_bound_covers_three_runs_at_their_deadline(self):
        t = {"slow": 900, "fast": 60}
        self.assertEqual(SP.silent_bound_s(["slow", "fast"], scale=4, timeouts=t), 3 * 4 * 900 + 600)
        self.assertEqual(SP.silent_bound_s(["nobody_knows"], scale=4, timeouts=t), 3 * 4 * 900 + 600,
                         "a gate the registry does not know must be bounded by the widest timeout, not the least")
        self.assertEqual(SP.silent_bound_s(["fast"], scale=1, timeouts=t), SP.PROVER_SILENT_MIN_S)
        self.assertEqual(SP.silent_bound_s(None, scale=4, timeouts=t), 3 * 4 * 900 + 600)


class AMultiLaneLogStillMoves(unittest.TestCase):
    """REG-1683 (the v3544 eye) - with two or more lanes, heart2 holds a gate's lines until the gate ends, so a long
    gate left the log still past silent_bound_s while it worked. A buffered lane now says it is alive, at most once a
    minute, and the gate's own lines still arrive together, in order."""

    def setUp(self):
        import heart2 as H
        import threading
        self.H, self.out, self.t = H, [], [1000.0]
        self.lock = threading.Lock()

    def lane(self, buffered=True):
        return self.H._LaneSay(self.out.append, self.lock, buffered=buffered, clock=lambda: self.t[0])

    def test_a_buffered_lane_says_it_is_alive_as_it_works(self):
        say = self.lane()
        say("     gate_x[0]  PROVEN")
        self.assertEqual(len(self.out), 1, "a buffered lane wrote nothing while its gate worked - the log stood still")
        self.assertNotIn("PROVEN", self.out[0], "the heartbeat let a held verdict out early, out of its gate's block")
        self.t[0] += 30
        say("     gate_x[1]  PROVEN")
        self.assertEqual(len(self.out), 1, "the heartbeat is not throttled - one line per proof floods the log")
        self.t[0] += self.H.LANE_BEAT_EVERY_S
        say("     gate_x[2]  PROVEN")
        self.assertEqual(len(self.out), 2, "a minute later the lane said nothing - a long gate still reads as silent")

    def test_the_gates_lines_still_arrive_together_in_order(self):
        say = self.lane()
        for k in range(3):
            say("     gate_x[%d]  PROVEN" % k)
        say.flush()
        verdicts = [x for x in self.out if "PROVEN" in x]
        self.assertEqual(verdicts, ["     gate_x[%d]  PROVEN" % k for k in range(3)], self.out)

    def test_one_lane_is_unbuffered_and_carries_no_beat(self):
        say = self.lane(buffered=False)
        say("     gate_x[0]  PROVEN")
        self.assertEqual(self.out, ["     gate_x[0]  PROVEN"])

    def test_the_beat_comes_well_inside_the_bound(self):
        self.assertLess(self.H.LANE_BEAT_EVERY_S * 2, SP.PROVER_SILENT_MIN_S,
                        "the heartbeat is slower than the silence bound can tolerate")


class TheHeartSeesIt(unittest.TestCase):
    """The console doctor and the fleet beacon read the lane's key - "silent" must reach both as a warning."""

    def _src(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def test_the_doctor_warns_on_a_silent_prover(self):
        healthy = None
        for n in ast.walk(self._src()):
            if isinstance(n, ast.Assign) and any(getattr(t, "id", None) == "_sp_ok" for t in n.targets):
                healthy = {c.value for c in ast.walk(n.value) if isinstance(c, ast.Constant) and isinstance(c.value, str)}
        self.assertIsNotNone(healthy, "PREMISE: the doctor's self-prove check (_sp_ok) was not found")
        self.assertIn("running", healthy, "PREMISE: the healthy list was not read")
        for k in ("silent", "silent-survived"):
            self.assertNotIn(k, healthy, "the doctor reads a SILENT prover (%s) as healthy" % k)

    def test_the_fleet_beacon_carries_the_lanes_key(self):
        found = False
        for n in ast.walk(self._src()):
            if (isinstance(n, ast.Assign) and any(isinstance(t, ast.Subscript) and getattr(t.slice, "value", None) == "heart"
                                                  for t in n.targets) and isinstance(n.value, ast.Dict)):
                keys = {k.value for k in n.value.keys if isinstance(k, ast.Constant)}
                found = found or "key" in keys
        self.assertTrue(found, "the fleet beacon's heart block no longer carries the self-prove lane's key")


RED_PROOF = [
    {"why": "REG-1674 - a prover silent past its honest bound holds the lane for ever",
     "file": "self_prove.py",
     "find": "    silent = bool(running) and not aside and not finishing and _quiet is not None and _quiet > _bound\n",
     "replace": "    silent = False\n", "matches": 1},
    {"why": "REG-1674 - the prover's log is block-buffered again: a working prover and a hung one look the same",
     "file": "self_prove.py",
     "find": "HEART2_DEADLINE_SCALE=str(PROVER_DEADLINE_SCALE), PYTHONUNBUFFERED=\"1\")",
     "replace": "HEART2_DEADLINE_SCALE=str(PROVER_DEADLINE_SCALE))", "matches": 1},
    {"why": "REG-1674 - the gates that hung are planned first again, holding every other proof behind them",
     "file": "self_prove.py",
     "find": "            _plan = ([t for t in _owed_g if str(t[0]) not in _stuck] or _owed_g) if isinstance(_owed_g, list) else _owed_g\n",
     "replace": "            _plan = _owed_g\n", "matches": 1},
    {"why": "REG-1674 - the bound covers one run, so an honest slow law is killed as 'silent'",
     "file": "self_prove.py",
     "find": "3 * sc * max(per) + 600",
     "replace": "sc * max(per) + 600", "matches": 1},
    {"why": "REG-1674 - an unreadable log reads as silent and a working prover is ended on a reading nobody got",
     "file": "self_prove.py",
     "find": "        age = max(0.0, float(now_s) - os.path.getmtime(log_path))\n    except Exception:\n        return None, None\n",
     "replace": "        age = max(0.0, float(now_s) - os.path.getmtime(log_path))\n    except Exception:\n        return 10.0 ** 9, None\n",
     "matches": 1},
    {"why": "REG-1674 - the console doctor reads a silent prover as healthy",
     "file": "control_app.py",
     "find": "    _sp_ok = (_sp_key in (None, \"current\", \"running\", \"start\", \"dev\", \"off\", \"busy\",\n",
     "replace": "    _sp_ok = (_sp_key in (None, \"current\", \"running\", \"start\", \"dev\", \"off\", \"busy\", \"silent\",\n",
     "matches": 1},
    {"why": "REG-1683 - a buffered lane writes nothing until its gate ends: a long multi-lane gate reads as a silent prover",
     "file": "heart2.py",
     "find": "            self._sink(\"  · a proving lane is working - %d line(s) of its gate held until the gate ends\"\n",
     "replace": "            (lambda *_: None)(\"  · a proving lane is working - %d line(s) of its gate held until the gate ends\"\n",
     "matches": 1},
    {"why": "REG-1683 - the heartbeat is unthrottled: one extra line per proof",
     "file": "heart2.py",
     "find": "        if self._beat is None or now - self._beat >= LANE_BEAT_EVERY_S:\n",
     "replace": "        if True:\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
