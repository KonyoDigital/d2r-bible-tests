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
  3. REG-2435 (#186 g): it is NOT throttled - every finished gate is banked, a slice and a FULL run alike (a full run
     installed no banker and wrote once at its end; a throttled slice lost every gate it finished inside the minute
     before a kill), from facts read once per run - and a bank that finds another bank writing WAITS and banks after
     it, never skips; a push still banks once, at its end.
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

    def _hook(self, fn):
        H._GATE_HOOK["fn"] = fn
        self.addCleanup(H._GATE_HOOK.__setitem__, "fn", None)

    def test_the_lane_hands_each_finished_gate_to_the_banker(self):
        seen = []
        self._hook(lambda out, lock: seen.append(sorted(out)))
        results, _per = H._prove_gates(self.have, _quiet, workers=1, blank=set())
        self.assertEqual(results, {n: H.PROVEN for n in GATES})
        self.assertEqual(len(seen), len(GATES), "the banker was not handed every finished gate: %r" % seen)
        self.assertEqual(seen[-1], sorted(GATES))

    def test_a_banker_that_raises_never_kills_the_lane(self):
        def boom(out, lock):
            raise IOError("disk full")
        self._hook(boom)
        results, _per = H._prove_gates(self.have, _quiet, workers=1, blank=set())
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

    def test_every_gate_banks_and_every_census_run_wires_it(self):
        """REG-2435 - no throttle: two gates, two banks; a slice AND a full run wire the banker; a push does not."""
        calls = []
        with mock.patch.object(H, "_write_state", lambda results, **k: calls.append(sorted(results))):
            bank = H._slice_banker(set(), _quiet)
            lock = threading.Lock()
            bank({GATES[0]: (H.PROVEN, [H.PROVEN])}, lock)
            bank({GATES[0]: (H.PROVEN, [H.PROVEN]), GATES[1]: (H.PROVEN, [H.PROVEN])}, lock)
        self.assertEqual(calls, [[GATES[0]], sorted(GATES)],
                         "the banker skipped a finished gate - a kill before the next bank loses it: %r" % calls)
        wired = {}

        def fake_gates(have, say=print, workers=None, blank=None):
            wired["on_gate"] = H._GATE_HOOK.get("fn")
            return {n: H.PROVEN for n, _f, _p in have}, {n: [H.PROVEN] for n, _f, _p in have}

        def fake_push(have, say, stopped=None, cache=None, blank=None):
            wired["on_gate"] = H._GATE_HOOK.get("fn")
            return {n: H.PROVEN for n, _f, _p in have}, {n: [H.PROVEN] for n, _f, _p in have}
        with mock.patch.object(H, "_prove_gates", fake_gates), mock.patch.object(H, "_prove_push", fake_push), \
                mock.patch.object(H, "_write_state", lambda *a, **k: None), \
                mock.patch.object(H, "_census_snapshot", lambda gates=None: None), \
                mock.patch.object(H, "open_cache", lambda say=print: None):
            H.prove(only=list(GATES), say=_quiet, stamp=False)
            self.assertTrue(callable(wired.get("on_gate")), "a SLICE ran without banking as it goes")
            wired.clear()
            H.prove(only=list(GATES), say=_quiet, stamp=True)
            self.assertTrue(callable(wired.get("on_gate")), "a FULL census banks only at its end - a kill loses it all")
            wired.clear()
            H.prove(only=list(GATES), say=_quiet, push=True, stopped=[])
            self.assertIsNone(wired.get("on_gate"), "a push banks mid-run through the census's banker")
        self.assertIsNone(H._GATE_HOOK.get("fn"), "the census's banker outlived its run into the next one")

    def test_a_bank_that_finds_another_writing_waits_and_banks_after_it(self):
        """REG-2435 - two lanes finish at once: the second bank must not be skipped while the first writes."""
        calls, first_in, release = [], threading.Event(), threading.Event()

        def slow_write(results, **k):
            calls.append(sorted(results))
            if len(calls) == 1:
                first_in.set()
                release.wait(10)
        with mock.patch.object(H, "_write_state", slow_write):
            bank = H._slice_banker(set(), _quiet)
            lock = threading.Lock()
            out = {GATES[0]: (H.PROVEN, [H.PROVEN])}
            t = threading.Thread(target=bank, args=(dict(out), lock))
            t.start()
            self.assertTrue(first_in.wait(10), "PREMISE: the first bank never wrote")
            out[GATES[1]] = (H.PROVEN, [H.PROVEN])
            t2 = threading.Thread(target=bank, args=(dict(out), lock))
            t2.start()
            t2.join(0.5)
            release.set()
            t.join(10)
            t2.join(10)
        self.assertEqual(calls, [[GATES[0]], sorted(GATES)],
                         "the second lane's bank was skipped while the first wrote - its gate is lost to a kill: %r"
                         % calls)


RED_PROOF = [
    {"why": "REG-1676 - the lane never hands a finished gate to the banker: a stand-aside throws the slice away again",
     "file": "heart2.py",
     "find": "            _hook = _GATE_HOOK.get(\"fn\")\n",
     "replace": "            _hook = None\n",
     "matches": 1},
    {"why": "REG-1676 - a failed bank kills the lane and turns the gates it proved BLIND",
     "file": "heart2.py",
     "find": "                    _hook(out, lock)\n                except Exception as _be:\n",
     "replace": "                    _hook(out, lock)\n                except ZeroDivisionError as _be:\n",
     "matches": 1},
    {"why": "REG-1676 - the banker writes nothing: the census learns a slice's verdicts only at its end",
     "file": "heart2.py",
     "find": "                _write_state(snap, stamp=False, unmeasured=unm, measured=measured(snap) if measured else None)\n",
     "replace": "                pass\n",
     "matches": 1},
    {"why": "REG-2435 - the 60 s throttle is back: the second of two gates finished inside a minute is not banked",
     "file": "heart2.py",
     "find": "SLICE_BANK_EVERY_S = 0\n",
     "replace": "SLICE_BANK_EVERY_S = 60\n",
     "matches": 1},
    {"why": "REG-2435 - a bank that finds another writing skips: a gate two lanes finish at once is lost to a kill",
     "file": "heart2.py",
     "find": "        with st[\"lk\"]:                              # REG-2435 - wait for a bank in flight, then bank what is "
             "done now\n",
     "replace": "        if not st[\"lk\"].acquire(False):\n            return\n        with _HeldLock(st[\"lk\"]):\n",
     "matches": 1},
    {"why": "REG-1676 / REG-2435 - a census is run without the banker",
     "file": "heart2.py",
     "find": "        _GATE_HOOK[\"fn\"] = _slice_banker(_blank, say, measured=",
     "replace": "        _GATE_HOOK[\"fn\"] = None and _slice_banker(_blank, say, measured=",
     "matches": 1},
    {"why": "REG-2435 - a FULL census installs no banker again: it writes once at its end, and a kill loses every gate",
     "file": "heart2.py",
     "find": "        _GATE_HOOK[\"fn\"] = _slice_banker(_blank, say, measured=",
     "replace": "        _GATE_HOOK[\"fn\"] = None if stamp else _slice_banker(_blank, say, measured=",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
