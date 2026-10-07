# -*- coding: utf-8 -*-
"""#42 lever 1 (REG-1710) - A PROOF REMEMBERS WHICH CASES CAUGHT IT, AND THE MEMORY CAN ONLY SAVE TIME.

His question, 2026-10-02: "all these pushs are so long taking hours each ... we had pushes that were 17 minutes average.
now they are each an hour plus". MEASURED: every batch touched tv/test_control.py, and each of its 6 sabotages re-ran all
2,259 cases (8-14 min apiece) to learn what one or two cases already said - 99-101 min of proofs per push.

At push time a tampered run that goes red now records WHICH cases failed; the next push asks only those, untampered
(must be green) and tampered (must be red). Every other outcome falls back to the full proof.

What this law drives - the REAL _prove_one and the REAL _run_gate, against a real two-class unittest law in a sandbox:
  * a first proof runs in full and learns the case that caught it; the second runs only that case and is PROVEN
  * a stale memory (a case that does not catch it) falls back to the full proof, which re-learns
  * a BLIND law is never called PROVEN by its memory - narrowed green, full green, BLIND
  * a remembered name that no longer exists cannot fake a red: the narrowed CLEAN run must be green first
  * outside push time, and with HEART2_RED_MEMORY=0, every proof runs in full
RED_PROOF below.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2 as H  # noqa: E402

LAW = '''import unittest
import subject


class Catches(unittest.TestCase):
    def test_value_is_one(self):
        self.assertEqual(subject.VALUE, 1)


class Bystander(unittest.TestCase):
    def test_true(self):
        self.assertTrue(True)

    def test_other(self):
        self.assertEqual(subject.OTHER, 2)


if "__main__" == __name__:     # reversed on purpose: TestNoOrphanSuite anchors on the real guard
    unittest.main()
'''

BLIND_LAW = '''import unittest
import subject


class Bystander(unittest.TestCase):
    def test_other(self):
        self.assertEqual(subject.OTHER, 2)


if "__main__" == __name__:     # reversed on purpose: TestNoOrphanSuite anchors on the real guard
    unittest.main()
'''

PROOF = {"why": "fixture", "file": "subject.py", "find": "VALUE = 1", "replace": "VALUE = 2", "matches": 1}


class _Push(object):
    pass


class ARedMemory(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="h2red.")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.tv = os.path.join(self.root, "repo", "tv")
        os.makedirs(self.tv)
        with io.open(os.path.join(self.tv, "subject.py"), "w", encoding="utf-8") as fh:
            fh.write("VALUE = 1\nOTHER = 2\n")
        with io.open(os.path.join(self.tv, "law_fixture.py"), "w", encoding="utf-8") as fh:
            fh.write(LAW)
        with io.open(os.path.join(self.tv, "blind_fixture.py"), "w", encoding="utf-8") as fh:
            fh.write(BLIND_LAW)
        saved = (H.RED_MEMORY, H._PUSH, H._run_gate, os.environ.get("HEART2_RED_MEMORY"))

        def _restore():
            H.RED_MEMORY, H._PUSH, H._run_gate = saved[0], saved[1], saved[2]
            if saved[3] is None:
                os.environ.pop("HEART2_RED_MEMORY", None)
            else:
                os.environ["HEART2_RED_MEMORY"] = saved[3]
        self.addCleanup(_restore)
        os.environ.pop("HEART2_RED_MEMORY", None)
        H.RED_MEMORY = os.path.join(self.root, ".heart2_red.json")
        H._PUSH = _Push()
        self.calls, real = [], saved[2]

        def spy(sandbox_tv, filename, timeout=180, extra=(), script=None, widths=None):
            self.calls.append(list(extra or ()))
            return real(sandbox_tv, filename, timeout=timeout, extra=extra, script=script, widths=widths)
        H._run_gate = spy
        self.said = []

    def say(self, *a, **k):
        self.said.append(" ".join(str(x) for x in a))

    def prove(self, law="law_fixture.py", name="red-memory-fixture"):
        self.calls[:] = []
        return H._prove_one(self.tv, name, law, dict(PROOF), 0, self.say)

    def memory(self):
        if not os.path.exists(H.RED_MEMORY):
            return {}
        with io.open(H.RED_MEMORY, encoding="utf-8") as fh:
            return json.load(fh)

    def plant(self, ids, name="red-memory-fixture"):
        with io.open(H.RED_MEMORY, "w", encoding="utf-8") as fh:
            json.dump({H._red_key(name, 0, PROOF): {"gate": name, "proof": 0, "ids": ids, "at": 1}}, fh)

    def test_the_parser_reads_both_unittest_shapes_and_drops_class_errors(self):
        got = H._red_ids(["FAIL: test_a (__main__.Klass)", "ERROR: test_b (__main__.Other.test_b)",
                          "ERROR: setUpClass (__main__.Klass)", "FAIL: test_c (pkg.mod.Thing)", "noise"])
        self.assertEqual(got, ["Klass.test_a", "Other.test_b"])

    def test_a_first_proof_learns_and_the_second_asks_only_what_caught_it(self):
        self.assertEqual(self.prove(), H.PROVEN)
        self.assertEqual(self.calls, [[], []], "the first proof must run the law in full, clean then tampered")
        ids = [e["ids"] for e in self.memory().values()]
        self.assertEqual(ids, [["Catches.test_value_is_one"]])
        self.assertEqual(self.prove(), H.PROVEN)
        self.assertEqual(self.calls, [["Catches.test_value_is_one"], ["Catches.test_value_is_one"]],
                         "the second proof did not ask only the remembered case: %r" % self.calls)
        self.assertTrue(any("that caught it before" in s for s in self.said), self.said)

    def test_a_stale_memory_falls_back_to_the_full_proof_and_relearns(self):
        self.plant(["Bystander.test_true"])
        self.assertEqual(self.prove(), H.PROVEN)
        self.assertIn([], self.calls, "a stale memory was trusted - the full proof never ran: %r" % self.calls)
        self.assertEqual([e["ids"] for e in self.memory().values()], [["Catches.test_value_is_one"]])

    def test_a_blind_law_is_never_proven_by_its_memory(self):
        self.plant(["Bystander.test_other"])
        self.assertEqual(self.prove(law="blind_fixture.py"), H.BLIND)

    def test_a_name_that_no_longer_exists_cannot_fake_a_red(self):
        self.plant(["Nope.test_gone"])
        self.assertEqual(self.prove(law="blind_fixture.py"), H.BLIND,
                         "a remembered case that does not exist errored red and was credited as a proof")

    def test_outside_push_time_every_proof_runs_in_full(self):
        self.plant(["Catches.test_value_is_one"])
        H._PUSH = None
        self.assertEqual(self.prove(), H.PROVEN)
        self.assertEqual(self.calls, [[], []])

    def test_a_closed_memory_neither_narrows_nor_learns(self):
        os.environ["HEART2_RED_MEMORY"] = "0"
        self.assertEqual(self.prove(), H.PROVEN)
        self.assertEqual(self.calls, [[], []])
        self.assertEqual(self.memory(), {})


RED_PROOF = [
    {
        "why": "REG-1710 - a narrowed tampered run that stays GREEN is credited as a proof: a blind law reads PROVEN",
        "file": "heart2.py",
        "find": "    if ok_t is False:\n        say(",
        "replace": "    if True:\n        say(",
        "matches": 1,
    },
    {
        "why": "REG-1710 - the narrowed clean run is not required green, so a vanished case errors red and is credited",
        "file": "heart2.py",
        "find": "    if ok_c is not True:\n        return None\n",
        "replace": "    if False:\n        return None\n",
        "matches": 1,
    },
    {
        "why": "REG-1710 - a red full proof stops teaching the memory, so every push pays the full run again",
        "file": "heart2.py",
        "find": "        _red_remember(_rk, name, idx, _LAST_RED.pop(threading.get_ident(), None))",
        "replace": "        pass",
        "matches": 1,
    },
    {
        "why": "REG-1710 - the memory is consulted outside push time too",
        "file": "heart2.py",
        "find": "    _rk = _red_key(name, idx, pr) if (_PUSH is not None and not _script and not _extra and not clean_only) else None\n",
        "replace": "    _rk = _red_key(name, idx, pr) if (not _script and not _extra and not clean_only) else None\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
