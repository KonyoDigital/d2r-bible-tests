# -*- coding: utf-8 -*-
"""REG-1676 - A SLICE BANKS WHAT IT HAS PROVED AS IT GOES, SO A STAND-ASIDE NEVER THROWS IT AWAY.

MEASURED on his ALT 2026-10-01: a 27-gate census slice proved four once-BLIND gates PROVEN (frame_index, keep_floors,
armed_prune, drain_ring: 30 of 30 proofs red), then stood aside at "only 972 MB of memory left" before its end. A slice
wrote the census only at its end, so the verdicts were thrown away, the BLIND records stood, and every lock on that PC -
the river - stayed shut for another hour. His words that day: "its been 0% for hours".

Driven through the REAL _prove_gates / _prove_lane / _slice_banker / _write_state; only the sandbox and the law runs are
stand-ins, and the census is written to a temp file, never his:
  1. every finished gate is handed to the banker, and a banker that raises never kills the lane;
  2. the banker writes the verdicts so far into the census, so the gates it banked are no longer owed;
  3. it is throttled (the gate scan costs seconds on the ALT), and a slice wires it while a full run does not.
RED_PROOF below.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2 as H  # noqa: E402

#: two REAL registered gates that declare red-proofs, so _write_state (which reads the real registry) keeps them
GATES = ("test_one_clean_run_serves_a_gates_proofs", "test_a_silent_prover_is_ended_and_said")


def _quiet(*a, **k):
    pass


def _have():
    files = dict(H.gate_files(say=_quiet))
    out = []
    for n in GATES:
        f = files.get(n)
        if f:
            out.append((n, f, H.red_proofs_in(f)))
    return out


class _Census(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="slice_bank_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.state = os.path.join(self.d, ".heart2.json")
        p = mock.patch.object(H, "STATE", self.state)
        p.start()
        self.addCleanup(p.stop)
        self.have = _have()
        self.assertEqual(len(self.have), len(GATES), "PREMISE: the fixture gates are not in the registry: %r"
                         % [h[0] for h in self.have])

    def census(self):
        with io.open(self.state, encoding="utf-8") as fh:
            return json.load(fh)


class EveryFinishedGateIsHandedToTheBanker(_Census):

    def setUp(self):
        super().setUp()
        self.box = tempfile.mkdtemp(prefix="slice_bank_box_")
        for name, fake in (("make_sandbox", lambda say=None: (self.box, None)),
                           ("_prove_gate", lambda sandbox, name, filename, proofs, say: (H.PROVEN, [H.PROVEN] * len(proofs)))):
            p = mock.patch.object(H, name, fake)
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(shutil.rmtree, self.box, True)

    def test_the_lane_hands_each_finished_gate_to_the_banker(self):
        seen = []
        results, _per = H._prove_gates(self.have, _quiet, workers=1, blank=set(),
                                       on_gate=lambda out, lock: seen.append(sorted(out)))
        self.assertEqual(results, {n: H.PROVEN for n in GATES})
        self.assertEqual(len(seen), len(GATES), "the banker was not handed every finished gate: %r" % seen)
        self.assertEqual(seen[-1], sorted(GATES))

    def test_a_banker_that_raises_never_kills_the_lane(self):
        def boom(out, lock):
            raise IOError("disk full")
        results, _per = H._prove_gates(self.have, _quiet, workers=1, blank=set(), on_gate=boom)
        self.assertEqual(results, {n: H.PROVEN for n in GATES},
                         "a failed bank killed the lane and turned proved gates BLIND: %r" % results)


class TheBankerBanksTheVerdictsSoFar(_Census):

    def test_a_banked_gate_is_no_longer_owed(self):
        bank = H._slice_banker(set(), _quiet, every_s=0)
        out = {GATES[0]: (H.PROVEN, [H.PROVEN])}
        bank(out, threading.Lock())
        st = self.census()
        self.assertIn(GATES[0], st.get("provedGates") or [], "the banked gate is not in the census: %r"
                      % sorted(st))
        owed = [n for n, _k in H.slice_owed(state=st)["owed"]]
        self.assertNotIn(GATES[0], owed, "a gate the slice banked is still owed - a stand-aside would throw it away")
        self.assertIn(GATES[1], owed, "PREMISE: a gate the slice has not reached must stay owed")

    def test_it_is_throttled_and_a_slice_wires_it_while_a_full_run_does_not(self):
        calls = []
        with mock.patch.object(H, "_write_state", lambda results, **k: calls.append(sorted(results))):
            bank = H._slice_banker(set(), _quiet, every_s=3600)
            lock = threading.Lock()
            bank({GATES[0]: (H.PROVEN, [H.PROVEN])}, lock)
            bank({GATES[0]: (H.PROVEN, [H.PROVEN]), GATES[1]: (H.PROVEN, [H.PROVEN])}, lock)
        self.assertEqual(calls, [[GATES[0]]], "the banker wrote the census on every gate (seconds each on the ALT): %r"
                         % calls)
        wired = {}

        def fake_gates(have, say=print, workers=None, blank=None, on_gate=None):
            wired["on_gate"] = on_gate
            return {n: H.PROVEN for n, _f, _p in have}, {n: [H.PROVEN] for n, _f, _p in have}
        with mock.patch.object(H, "_prove_gates", fake_gates), mock.patch.object(H, "_write_state", lambda *a, **k: None):
            H.prove(only=list(GATES), say=_quiet, stamp=False)
            self.assertTrue(callable(wired.get("on_gate")), "a SLICE ran without banking as it goes")
            H.prove(only=list(GATES), say=_quiet, stamp=True)
            self.assertIsNone(wired.get("on_gate"), "a full run banks mid-run - its one write at the end is the rule")


RED_PROOF = [
    {"why": "REG-1676 - the lane never hands a finished gate to the banker: a stand-aside throws the slice away again",
     "file": "heart2.py",
     "find": "            if on_gate is not None:\n                try:\n                    on_gate(out, lock)\n",
     "replace": "            if False:\n                try:\n                    on_gate(out, lock)\n",
     "matches": 1},
    {"why": "REG-1676 - a failed bank kills the lane and turns the gates it proved BLIND",
     "file": "heart2.py",
     "find": "                try:\n                    on_gate(out, lock)\n                except Exception as _be:\n",
     "replace": "                try:\n                    on_gate(out, lock)\n                except ZeroDivisionError as _be:\n",
     "matches": 1},
    {"why": "REG-1676 - the banker writes nothing: the census learns a slice's verdicts only at its end",
     "file": "heart2.py",
     "find": "                _write_state(snap, stamp=False, unmeasured=unm)\n",
     "replace": "                pass\n",
     "matches": 1},
    {"why": "REG-1676 - the banker is not throttled: a gate scan per gate costs minutes per slice on the ALT",
     "file": "heart2.py",
     "find": "            if now - st[\"last\"] < every:\n",
     "replace": "            if False:\n",
     "matches": 1},
    {"why": "REG-1676 - a slice is run without the banker",
     "file": "heart2.py",
     "find": "                                          on_gate=(None if stamp else _slice_banker(_blank, say)))\n",
     "replace": "                                          on_gate=None)\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
