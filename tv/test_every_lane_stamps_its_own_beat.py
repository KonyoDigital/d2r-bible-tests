# -*- coding: utf-8 -*-
"""#80 — a lane that stops stamping its beat goes INVISIBLE, not red.

Every watcher lane in the console is a `while True` loop that sleeps, stamps one beat under its own
name, and does its work inside `except Exception: pass`. The beat is the ONLY thing that makes the
lane visible to `lane_liveness`, and through it to the heart. Delete it and the lane keeps running,
keeps failing silently, and reports as UNKNOWN forever — "nobody looked", which reads as fine.

⚠ WHY THIS FILE EXISTS AT ALL. Twelve lanes had NO sabotage evidence of their own: 163 RED_PROOFs
name control_app.py and only six landed inside a watcher loop. Evidence is credited per DEF SPAN,
so a lane earns a score only from a proof that strikes its own body. Each proof below deletes one
lane's beat, and therefore counts for that lane and no other.

⚠ AND THE SCORES STAY SEPARATE. One beat proven is `wilson_lower(1, 1)` = 0.2065 — real, and low,
which is the honest reading of a single sabotage. The organ publishes per-surface scores so these
do not drag down the lanes that earned more. [[unknown-stays-unknown]]
"""
import ast as _ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import health_engine as HE  # noqa: E402


class TestEveryLaneStampsItsOwnBeat(unittest.TestCase):

    def setUp(self):
        self.spans, self.src = HE._lane_spans()
        self.tree = _ast.parse(self.src)
        self.fns = dict((n.name, n) for n in _ast.walk(self.tree)
                        if isinstance(n, _ast.FunctionDef) and n.name in self.spans)
        self.assertEqual(sorted(self.fns), sorted(self.spans),
                         "a registered lane has no def — this law reads the wrong file")

    def _ticks(self, fn):
        return [c for c in _ast.walk(self.fns[fn]) if isinstance(c, _ast.Call)
                and getattr(c.func, "id", "") == "_lane_tick"]

    def test_every_registered_lane_stamps_exactly_one_beat(self):
        """Zero beats is the dangerous number: the loop still runs, and nothing can tell."""
        bad = []
        for fn, (lane, _a, _b) in sorted(self.spans.items()):
            n = len(self._ticks(fn))
            if n != 1:
                bad.append("%s (%s) stamps %d" % (lane, fn, n))
        self.assertEqual(bad, [],
                         "a lane must stamp its beat exactly once — %s. A lane that stamps nothing "
                         "is UNKNOWN to liveness forever, which reads as fine and is worse."
                         % "; ".join(bad))

    def test_the_name_a_lane_stamps_can_be_resolved_back_to_it(self):
        """`_live_of` looks the beat up by the WATCHER name first and the vessel name second, so a
        literal that is neither is a beat filed where nobody asks for it.

        ⚠ tvd-runaway-watch really does stamp its FUNCTION name, and that is legal by this rule —
        `_stamps_of` exists for exactly that. A law that demanded the lane name would flag correct
        design, which is why it was measured before it was written."""
        bad = []
        for fn, (lane, _a, _b) in sorted(self.spans.items()):
            t = self._ticks(fn)
            if not t or not t[0].args:
                bad.append("%s stamps nothing" % lane)
                continue
            lit = getattr(t[0].args[0], "value", None)
            if not isinstance(lit, str):
                bad.append("%s stamps a non-literal" % lane)
            elif lit not in (lane, fn):
                bad.append("%s stamps %r, which is neither its lane nor its function" % (lane, lit))
        self.assertEqual(bad, [], "; ".join(bad))


RED_PROOF = [
    {
        "why": "deletes tvd-chron-autoread's beat, so the lane keeps running and keeps failing where no reader "
               "can see it — UNKNOWN to liveness forever, which reads as fine",
        "file": "control_app.py",
        "find": "_lane_tick('tvd-chron-autoread', _CHRON_AUTOREAD_EVERY_S)",
        "replace": "pass",
        "matches": 1,
    },
    {
        "why": "deletes tvd-eagle-watch's beat, so the lane keeps running and keeps failing where no reader "
               "can see it — UNKNOWN to liveness forever, which reads as fine",
        "file": "control_app.py",
        "find": "_lane_tick('tvd-eagle-watch', _EAGLE_EVERY_S)",
        "replace": "pass",
        "matches": 1,
    },
    {
        "why": "deletes tvd-ledger-backup's beat, so the lane keeps running and keeps failing where no reader "
               "can see it — UNKNOWN to liveness forever, which reads as fine",
        "file": "control_app.py",
        "find": "_lane_tick('tvd-ledger-backup', _LEDGER_BACKUP_EVERY_S)",
        "replace": "pass",
        "matches": 1,
    },
    {
        "why": "deletes tvd-retention's beat, so the lane keeps running and keeps failing where no reader "
               "can see it — UNKNOWN to liveness forever, which reads as fine",
        "file": "control_app.py",
        "find": "_lane_tick('tvd-retention', _RETENTION_EVERY_S)",
        "replace": "pass",
        "matches": 1,
    },
    {
        "why": "deletes tvd-retro-triage's beat, so the lane keeps running and keeps failing where no reader "
               "can see it — UNKNOWN to liveness forever, which reads as fine",
        "file": "control_app.py",
        "find": "_lane_tick('tvd-retro-triage', _TRIAGE_EVERY_S)",
        "replace": "pass",
        "matches": 1,
    },
    {
        "why": "deletes tvd-rolling-prune's beat, so the lane keeps running and keeps failing where no reader "
               "can see it — UNKNOWN to liveness forever, which reads as fine",
        "file": "control_app.py",
        "find": "_lane_tick('tvd-rolling-prune', _PRUNE_POLL_S)",
        "replace": "pass",
        "matches": 1,
    },
    {
        "why": "deletes tvd-runaway-watch's beat, so the lane keeps running and keeps failing where no reader "
               "can see it — UNKNOWN to liveness forever, which reads as fine",
        "file": "control_app.py",
        "find": "_lane_tick('_runaway_watch_loop', _RUNAWAY_TICK_S)",
        "replace": "pass",
        "matches": 1,
    },
    {
        "why": "deletes tvd-shadow-watch's beat, so the lane keeps running and keeps failing where no reader "
               "can see it — UNKNOWN to liveness forever, which reads as fine",
        "file": "control_app.py",
        "find": "_lane_tick('tvd-shadow-watch', _SHADOW_WATCH_EVERY_S)",
        "replace": "pass",
        "matches": 1,
    },
    {
        "why": "deletes tvd-space-warden's beat, so the lane keeps running and keeps failing where no reader "
               "can see it — UNKNOWN to liveness forever, which reads as fine",
        "file": "control_app.py",
        "find": "_lane_tick('tvd-space-warden', _WARDEN_EVERY_S)",
        "replace": "pass",
        "matches": 1,
    },
    {
        "why": "deletes tvd-stash-watch's beat, so the lane keeps running and keeps failing where no reader "
               "can see it — UNKNOWN to liveness forever, which reads as fine",
        "file": "control_app.py",
        "find": "_lane_tick('tvd-stash-watch', _STASH_WATCH_POLL_S)",
        "replace": "pass",
        "matches": 1,
    },
    {
        "why": "deletes tvd-vault-autoread's beat, so the lane keeps running and keeps failing where no reader "
               "can see it — UNKNOWN to liveness forever, which reads as fine",
        "file": "control_app.py",
        "find": "_lane_tick('tvd-vault-autoread', _VAULT_AUTOREAD_EVERY_S)",
        "replace": "pass",
        "matches": 1,
    },
    {
        "why": "deletes tvd-version-drift's beat, so the lane keeps running and keeps failing where no reader "
               "can see it — UNKNOWN to liveness forever, which reads as fine",
        "file": "control_app.py",
        "find": "_lane_tick('tvd-version-drift', _DRIFT_EVERY_S)",
        "replace": "pass",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
