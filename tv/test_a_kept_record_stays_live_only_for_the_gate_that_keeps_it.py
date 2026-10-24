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
import fixture_tmp      # noqa: E402

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

    def test_a_body_written_while_kept_never_reaches_the_next_gate(self):
        sb, keeper, other = self.lane()
        rec = os.path.join(sb, *VERDICT.split("/"))
        self.reset(sb, heart2._gate_keeps(keeper))
        base._write(rec, u'{"abortedAt": "the keeping gate wrote this"}\n')
        self.reset(sb, heart2._gate_keeps(other))
        self.assertFalse(os.path.lexists(rec), "a body the keeping gate wrote reached a gate that never kept it")

    def test_nothing_is_removed_through_a_link_out_of_the_sandbox(self):
        sb, _k, other = self.lane()
        outside = os.path.join(self.root, "outside_tv")
        os.makedirs(outside)
        real = os.path.join(outside, ".render_verdict.json")
        base._write(real, u'{"live": "the real tree"}\n')
        tv = os.path.join(sb, "tv")
        os.rename(tv, tv + "_moved")
        if not fixture_tmp.link_dir(outside, tv):   # a symlink, or a junction on Windows (proofs say "dir-link")
            os.rename(tv + "_moved", tv)
            self.skipTest("this PC will not make a directory link")
        self.addCleanup(lambda: (fixture_tmp.unlink_dir_link(tv), os.rename(tv + "_moved", tv)))
        heart2._reset_lane_records(tv, lambda *a, **k: None, heart2._gate_keeps(other))
        self.assertTrue(os.path.exists(real), "a reset removed a record outside the sandbox through a link")

    def test_a_record_swapped_for_a_link_out_is_unlinked_never_followed(self):
        # review r6: a gate replaces its record itself with a link out of the sandbox
        sb, _k, other = self.lane()
        outside = os.path.join(self.root, "outside_rec")
        os.makedirs(outside)
        real = os.path.join(outside, "keep.txt")
        base._write(real, u"the real tree\n")
        rec = os.path.join(sb, *VERDICT.split("/"))
        os.remove(rec)
        if not fixture_tmp.link_dir(outside, rec):
            self.skipTest("this PC will not make a directory link")
        self.addCleanup(lambda: os.path.lexists(rec) and fixture_tmp.unlink_dir_link(rec))
        self.reset(sb, heart2._gate_keeps(other))
        self.assertTrue(os.path.exists(real), "a reset followed a link out of the sandbox")
        self.assertFalse(os.path.lexists(rec), "the link out of the sandbox reached the next gate")

    def test_an_unkept_tracked_record_reads_as_checkout_writes_it(self):
        # review r6: --filters - the bytes `git checkout` writes (EOL conversion), not the raw blob
        sb, _k, _o = self.lane()
        base._write(os.path.join(sb, ".gitattributes"), u"%s text eol=crlf\n" % base.TRACKED)
        got = heart2._unkept_records(sb, {base.TRACKED})
        self.assertEqual(got.get(base.TRACKED), base.COMMITTED.replace(u"\n", u"\r\n").encode("utf-8"),
                         "an unkept tracked record is the raw blob, not what checkout writes")

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
        "why": "#182(3) - review r5/r6: an unkept record is touched though its folder is outside the sandbox",
        "file": "heart2.py",
        "find": "            if not _inside(root, os.path.dirname(p)):\n",
        "replace": "            if False:\n",
        "matches": 1,
        "needs": "dir-link",
    },
    {
        "why": "#182(3) - review r6: a link at the record is followed, not unlinked",
        "file": "heart2.py",
        "find": "            if _is_link(p):\n                moved.append(rel)\n                _unlink_link(p)\n",
        "replace": "",
        "matches": 1,
        "needs": "dir-link",
    },
    {
        "why": "#182(3) - review r6: the unkept bytes are the raw blob, not what checkout writes",
        "file": "heart2.py",
        "find": "[\"cat-file\", \"--filters\", \"HEAD:\" + rel]",
        "replace": "[\"cat-file\", \"blob\", \"HEAD:\" + rel]",
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
