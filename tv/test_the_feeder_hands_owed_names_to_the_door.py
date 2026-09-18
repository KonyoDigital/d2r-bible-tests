# -*- coding: utf-8 -*-
"""#28 — THE MISSING FEEDER, PINNED. split() judged journal names through the REAL gate and
NOTHING called it to write; autoOwed drained only by his hand. The feeder
(tv/read_names_feeder.py) is that caller — these laws pin that an owed name actually reaches
the ONE door, that a refused door is a RED result and never a swallow, that UNKNOWN owed feeds
nothing, and that the lock fails CLOSED. All collaborators are stubbed — no board, no journal,
no money.
"""
import os
import sys
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import read_names_feeder as rf


def _split_fixture():
    return {"ok": True, "autoOwed": ["Shako"],
            "auto": [{"name": "Shako", "container": "inventory", "containerAgreed": True,
                      "ledger": "UNIQUE", "referents": ["UNIQUE"]}],
            "rosterWhy": ""}


def _evidence_fixture():
    pile = [{"session": "s1", "conf": 0.9, "scene": "stash", "ts": 1},
            {"session": "s2", "conf": 0.9, "scene": "stash", "ts": 2}]
    return ({"Shako": pile}, "")


class _Stub(types.ModuleType):
    pass


class TestTheFeeder(unittest.TestCase):
    def setUp(self):
        self._saved = {k: sys.modules.get(k)
                       for k in ("read_names_lane", "vault_retro", "control_app", "self_arming")}
        self.calls = []

        rnl = _Stub("read_names_lane")
        rnl.split = lambda: _split_fixture()
        rnl.evidence = lambda: _evidence_fixture()
        sys.modules["read_names_lane"] = rnl

        vr = _Stub("vault_retro")
        vr._owned_row = lambda pair, pile: {"name": pair[0], "lane": pair[1],
                                            "witnesses": [dict(p) for p in pile]}
        sys.modules["vault_retro"] = vr

        ca = _Stub("control_app")
        ca.vault_apply = lambda prop: (self.calls.append(prop) or {"ok": True})
        sys.modules["control_app"] = ca

        sa = _Stub("self_arming")
        sa.may = lambda surface: (True, "")
        sys.modules["self_arming"] = sa

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v

    def test_an_owed_name_reaches_the_door_with_its_evidence(self):
        r = rf.apply(by="test")
        self.assertTrue(r["ok"], r["why"])
        self.assertEqual(r["banked"], 1)
        self.assertEqual(len(self.calls), 1, "the door was not called exactly once")
        row = self.calls[0]["owned"][0]
        self.assertEqual(row["name"], "Shako")
        self.assertEqual(row["lane"], "inventory")
        self.assertTrue(all("conf" in e for e in row["evidence"]),
                        "a witness row without conf makes the door read bestConf 0.0 and refuse")

    def test_the_per_tick_cap_permits_flow(self):
        """⚠⚠ ADDED AFTER A BLIND SABOTAGE. `MAX_PER_TICK = 4` -> `0` matched exactly once and the
        law stayed GREEN: every case called apply() without a limit, so the cap the CALLER passes
        was never exercised. A correct match count with a green law means the LAW is weak, not the
        sabotage — and a cap of 0 is a feeder that ticks forever and feeds nothing, which is the
        vault_autoreel_tick scar wearing a constant. [[regression-guard]] §4c [[heart-first]] §2"""
        self.assertGreaterEqual(
            rf.MAX_PER_TICK, 1,
            "MAX_PER_TICK is %r — a cap of zero makes every tick bank nothing while the lane "
            "reports itself ON. That is not a throttle, it is an off switch that reads as "
            "healthy." % rf.MAX_PER_TICK)
        r = rf.apply(by="test", limit=rf.MAX_PER_TICK)
        self.assertTrue(r["ok"], r["why"])
        self.assertEqual(
            r["banked"], 1,
            "with the cap the CALLER actually passes, the one owed name in the fixture was not "
            "banked (banked=%r, why=%r). This is the path production takes, and until this case "
            "existed nothing tested it." % (r["banked"], r["why"]))

    def test_a_refused_door_is_a_red_result_not_a_swallow(self):
        """THE SABOTAGE THIS GATE EXISTS FOR."""
        sys.modules["control_app"].vault_apply = \
            lambda prop: {"ok": False, "why": "1 row(s) in that proposal do not clear the gate"}
        r = rf.apply(by="test")
        self.assertFalse(r["ok"], "the feeder reported ok over a refused door")
        self.assertEqual(r["refused"], 1)
        self.assertIn("do not clear the gate", r["why"], "the door's why was not kept verbatim")

    def test_unknown_owed_feeds_nothing(self):
        sp = _split_fixture()
        sp["autoOwed"] = None
        sys.modules["read_names_lane"].split = lambda: sp
        r = rf.apply(by="test")
        self.assertFalse(r["ok"])
        self.assertEqual(len(self.calls), 0, "UNKNOWN owed reached the door anyway")
        self.assertIn("UNKNOWN", r["why"])

    def test_an_unplaced_container_declines_with_its_reason(self):
        sp = _split_fixture()
        sp["auto"][0]["containerAgreed"] = False
        sys.modules["read_names_lane"].split = lambda: sp
        r = rf.apply(by="test")
        self.assertTrue(r["ok"])
        self.assertEqual(r["declined"], 1)
        self.assertEqual(len(self.calls), 0)

    def test_the_lock_fails_closed(self):
        def _boom(surface):
            raise RuntimeError("store gone")
        sys.modules["self_arming"].may = _boom
        r = rf.apply(by="test")
        self.assertFalse(r["ok"])
        self.assertIn("fails closed", r["why"])
        self.assertEqual(len(self.calls), 0)

    def test_a_locked_surface_is_a_loud_refusal(self):
        sys.modules["self_arming"].may = lambda surface: (False, "UNPROVEN 0.56 < 0.72")
        r = rf.apply(by="test")
        self.assertFalse(r["ok"])
        self.assertIn("LOCKED", r["why"])
        self.assertEqual(len(self.calls), 0)



class TestTheFeederIsActuallyRun(unittest.TestCase):
    """⚠⚠ THE JOIN, AND IT IS THE HALF THAT WAS MISSING FOR A DAY.

    The cases above pin what the feeder DOES when called. Not one asks whether anything CALLS it —
    and on 2026-09-18 the answer was nothing: `grep -rn read_names_feeder tv/*.py` returned zero
    while the module sat complete, correct and unreachable in a scratch directory that deletes with
    the job. A feeder nobody runs is documentation. [[the-unjoined-end]]
    """

    def _code(self):
        """Comments stripped: the prose around this call explains the join in words a grep for its
        own subject would match. [[source-reading-guard]] §4"""
        import io as _io, os as _os
        here = _os.path.dirname(_os.path.abspath(__file__))
        with _io.open(_os.path.join(here, "control_app.py"), encoding="utf-8") as fh:
            raw = fh.read()
        return "\n".join(l.split("#", 1)[0] for l in raw.split("\n"))

    def test_something_actually_calls_the_feeder(self):
        code = self._code()
        self.assertIn(
            "import read_names_feeder", code,
            "NOTHING in control_app imports the feeder — the exact state this module was found in: "
            "151 lines, complete, and called by no one.")
        self.assertIn(
            "_rnf.plan()", code,
            "the feeder is imported and never planned with. An import is not a caller.")

    def test_it_ticks_under_its_OWN_lane_name(self):
        """Sharing vault-autoread's name makes one supervisor row answer for two lanes."""
        self.assertIn(
            "_lane_tick('tvd-read-names-feeder'", self._code(),
            "the feeder registers no lane of its own. The tick it rides SPENDS money on paid "
            "sweeps; this one banks names already read and costs nothing. A supervisor cannot ask "
            "sixteen lanes one question in sixteen vocabularies. [[heart-first]] §3")

    def test_its_lane_state_is_lifetime_and_UNKNOWN_is_not_zero(self):
        """A counter that resets on restart cannot answer 'has this ever worked'."""
        import control_app as CA
        st = getattr(CA, "_RNF_STATE", None)
        self.assertIsInstance(
            st, dict,
            "the feeder has no lane state, so nothing can report whether it has EVER banked a "
            "name — the vault_autoreel_tick scar exactly. [[heart-first]] §2")
        for k in ("runs", "banked", "lastTs", "owed"):
            self.assertIn(k, st,
                          "the lane state is missing %r — the shared vocabulary is "
                          "on / worked / lastTs / owed" % k)
        self.assertIsNone(
            st.get("owed"),
            "owed must START as None. Nobody has measured at import time, and a confident 0 there "
            "reads as 'the lane is clear'. [[unknown-stays-unknown]]")

    def test_the_doors_refusal_is_not_swallowed(self):
        """A feeder that ate a refusal would be the unjoined end wearing a wire."""
        code = self._code()
        i = code.find("import read_names_feeder")
        self.assertGreater(i, -1, "the caller is gone")
        j = code.find("\ndef ", i)
        self.assertGreater(j, i, "could not bound the caller block; refusing to judge a slice "
                                 "whose far end is a guess. [[source-reading-guard]]")
        self.assertIn(
            'if not _fa.get("ok")', code[i:j],
            "the caller never branches on the door's refusal, so vault_apply saying no would pass "
            "silently. The refusal is a RESULT, not an error.")


RED_PROOF = [
    {"why": "swallowing the door's refusal turns the feeder into the unjoined end with a wire "
            "through it — autoOwed nonempty + door refused must be RED",
     "file": "tv/read_names_feeder.py",
     "find": '        out["refused"] = len(rows)',
     "replace": '        out["ok"] = True\n        out["refused"] = len(rows)',
     "matches": 1},
    {"why": "a cap of 0 is a feeder that runs forever and feeds nothing — green with zero flow",
     "file": "tv/read_names_feeder.py",
     "find": "MAX_PER_TICK = 4",
     "replace": "MAX_PER_TICK = 0",
     "matches": 1},
    {"why": "removing the ONE caller puts the feeder back where it was found - complete, correct, run by nobody",
     "file": "tv/control_app.py",
     "find": "                import read_names_feeder as _rnf",
     "replace": "                import json as _rnf  # caller removed",
     "matches": 1},
]


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
