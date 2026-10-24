"""#182(3) / REG-2634 - A RUN RECORD ONE GATE KEEPS STAYS LIVE ONLY FOR THAT GATE.

The sandbox's keep-set is the UNION of every gate's PROOF_NEEDS (heart2.make_sandbox), so a record kept for one gate
stayed live for every law in that lane. Before each gate, _reset_lane_records now gives a record the gate does NOT keep
the state _drop_run_records gives a record nobody keeps (HEAD's blob where tracked, absent where not); the gate that
keeps it still gets it as built. A gate whose PROOF_NEEDS cannot be read keeps the old union (said nothing new).

Fixture repo and sandbox in temp dirs only (the helpers of test_a_sandbox_never_carries_a_run_record, never restated).
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import console_safe     # noqa: E402
console_safe.enable()
import test_a_sandbox_never_carries_a_run_record as base     # noqa: E402
import heart2           # noqa: E402

VERDICT = "tv/.render_verdict.json"


class AKeptRecordStaysLiveOnlyForItsGate(base._Case):

    def lane(self):
        keeper = os.path.join(self.root, "t_keeps_both.py")
        base._write(keeper, u'PROOF_NEEDS = [".render_verdict.json", ".self_arming.jsonl"]\n')
        other = os.path.join(self.root, "t_keeps_nothing.py")
        base._write(other, u'PROOF_NEEDS = []\n')
        sb, said = self.build(base._declaring() + [("t_keeps_both", keeper)])
        self.assertIsNotNone(base._read(os.path.join(sb, *VERDICT.split("/"))),
                             "PREMISE: the kept verdict was not brought across: %s" % said)
        self.assertEqual(base._read(os.path.join(sb, *base.TRACKED.split("/"))), base.COMMITTED + base.LIVE,
                         "PREMISE: the kept ledger is not the live one")
        return sb, keeper, other

    def reset(self, sb, keeps):
        return heart2._reset_lane_records(os.path.join(sb, "tv"), lambda *a, **k: None, keeps)

    def test_a_gate_that_keeps_nothing_reads_neither_live_record(self):
        sb, _k, other = self.lane()
        self.reset(sb, heart2._gate_keeps(other))
        self.assertFalse(os.path.lexists(os.path.join(sb, *VERDICT.split("/"))),
                         "an untracked record another gate keeps is live for a gate that never asked for it")
        self.assertEqual(base._read(os.path.join(sb, *base.TRACKED.split("/"))).replace(u"\r\n", u"\n"),
                         base.COMMITTED, "a tracked record another gate keeps is not HEAD's blob for this gate")

    def test_the_gate_that_keeps_them_gets_them_back_as_built(self):
        sb, keeper, other = self.lane()
        built = base._read(os.path.join(sb, *VERDICT.split("/")))
        self.reset(sb, heart2._gate_keeps(other))
        self.reset(sb, heart2._gate_keeps(keeper))
        self.assertEqual(base._read(os.path.join(sb, *VERDICT.split("/"))), built)
        self.assertEqual(base._read(os.path.join(sb, *base.TRACKED.split("/"))), base.COMMITTED + base.LIVE)

    def test_unreadable_needs_keep_the_old_union(self):
        sb, _k, _o = self.lane()
        self.assertEqual(self.reset(sb, None), [])
        self.assertIsNotNone(base._read(os.path.join(sb, *VERDICT.split("/"))))

    def test_gate_keeps_names_records_as_the_drop_does(self):
        _sb, keeper, other = self.lane()
        self.assertEqual(heart2._gate_keeps(keeper), {VERDICT, base.TRACKED})
        self.assertEqual(heart2._gate_keeps(other), set())


class ProveGatePassesItsOwnKeeps(unittest.TestCase):

    def test_prove_gate_hands_the_reset_the_gates_own_keeps(self):
        import tempfile
        d = tempfile.mkdtemp(prefix="keeps_")
        self.addCleanup(heart2._rmtree_hard, d)
        fn = os.path.join(d, "t_g.py")
        base._write(fn, u'PROOF_NEEDS = [".render_verdict.json"]\n')
        seen = []
        real = (heart2._reset_lane_records, heart2._prove_gate_push, heart2._PUSH)
        heart2._reset_lane_records = lambda sb, say, keeps=None: seen.append(keeps)
        heart2._prove_gate_push = lambda *a: ("PROVEN", [])
        heart2._PUSH = object()
        try:
            heart2._prove_gate("the/lane/tv", "g", fn, [], lambda *a, **k: None)
        finally:
            heart2._reset_lane_records, heart2._prove_gate_push, heart2._PUSH = real
        self.assertEqual(seen, [{VERDICT}])


RED_PROOF = [
    {
        "why": "#182(3) - the union keep-set: a record kept for one gate stays live for every gate",
        "file": "heart2.py",
        "find": "            if rel not in keeps:\n                was[rel] = data\n",
        "replace": "            if False:\n                was[rel] = data\n",
        "matches": 1,
    },
    {
        "why": "#182(3) - _prove_gate never passes the gate's own keeps",
        "file": "heart2.py",
        "find": "_reset_lane_records(sandbox, say, _gate_keeps(filename))",
        "replace": "_reset_lane_records(sandbox, say, None)",
        "matches": 1,
    },
    {
        "why": "#182(3) - an untracked kept record is never marked absent for other gates",
        "file": "heart2.py",
        "find": "            if not r.stdout.strip(b\"\\0\"):\n                out[rel] = None\n",
        "replace": "            if not r.stdout.strip(b\"\\0\"):\n                continue\n",
        "matches": 1,
    },
    {
        "why": "#182(3) - the unkept states are never armed",
        "file": "heart2.py",
        "find": "    _LANE_UNKEPT[root] = _unkept_records(",
        "replace": "    _LANE_UNKEPT[root] = {} if True else _unkept_records(",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main()
