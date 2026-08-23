"""v2013 — the doctor must be able to reach all three of its answers, and say which.

`vault_doctor` exists because an empty `vault_accum.json` has three causes needing three different
actions — no footage · footage but no stash panels · panels but no readable names — and an empty file
looks identical whichever one it is. **A diagnostic that cannot tell them apart is worse than none:
it sends him to fix the wrong thing with confidence.**

On his real tree it reports one of those three. That is exactly when a gate must be asked whether it
can report the others, so every case here is driven on a TEMP fixture through TV_HIST — never his
frames. [[feedback-fixtures-never-touch-live-data]] [[feedback-blind-fixture-green-gate]]
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import console_safe  # noqa: F401,E402 — the report prints glyphs
console_safe.enable()

import vault_doctor as vd  # noqa: E402


class TestTheDoctorCanReachEachAnswer(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)
        self._old = os.environ.get("TV_HIST")
        os.environ["TV_HIST"] = self.root
        vd._CACHE.clear()                      # the measure pass is cached; each case measures fresh
        self.addCleanup(vd._CACHE.clear)
        if self._old is None:
            self.addCleanup(os.environ.pop, "TV_HIST", None)
        else:
            self.addCleanup(os.environ.__setitem__, "TV_HIST", self._old)

    @staticmethod
    def _state(d, name):
        for r in d["checks"]:
            if r["name"] == name:
                return r["state"], r["detail"]
        raise AssertionError("no check named %r — the report shape changed" % name)

    def test_no_footage_says_record_a_reel(self):
        d = vd.diagnose()
        st, why = self._state(d, "footage")
        self.assertEqual(st, vd.MISSING)
        self.assertIn("record one", why)
        self.assertFalse(d["ready"], "with no footage there is nothing to read")

    def test_footage_with_no_stash_panel_says_open_your_stash(self):
        reel = os.path.join(self.root, "reel_s_1_1")
        os.makedirs(reel)
        for i in range(20):                    # real files, but not stash panels
            with open(os.path.join(reel, "f_%d.jpg" % (1000 + i)), "wb") as fh:
                fh.write(b"\xff\xd8\xff\xdb" + b"\0" * 64)
        d = vd.diagnose()
        self.assertEqual(self._state(d, "footage")[0], vd.OK)
        st, why = self._state(d, "stash panels")
        self.assertEqual(st, vd.MISSING, why)
        self.assertIn("open your stash", why.lower())

    def test_the_tooltip_answer_fires_when_cells_are_full_and_nothing_is_named(self):
        """THE answer on his machine: 220 occupied cells, zero names. Driven here without his film
        by handing the measure pass the numbers it would have produced."""
        vd._CACHE.update({"sampled": 155, "gated": 10, "measured": 10,
                          "occupied": 220, "free": 180, "refused": 0, "frames": []})
        # an empty ledger beside those cells is the case that must produce the tooltip sentence
        led = os.path.join(vd.HERE, "vault_accum.json")
        self.assertTrue(os.path.isfile(led), "vault_accum.json is missing — this check reads it")
        st, why = self._state(vd.diagnose(), "readable names")
        self.assertEqual(st, vd.MISSING)
        self.assertIn("HOVER TOOLTIP", why)
        self.assertIn("220", why, "the answer must carry the count he can act on")

    def test_a_measured_EMPTY_stash_is_not_reported_as_a_problem(self):
        """The mirror case, and the one a careless doctor gets wrong: cells measured and all empty
        means his stash really is empty. That is an OK, not a MISSING."""
        vd._CACHE.update({"sampled": 40, "gated": 4, "measured": 4,
                          "occupied": 0, "free": 160, "refused": 0, "frames": []})
        st, why = self._state(vd.diagnose(), "anything there")
        self.assertEqual(st, vd.OK, why)
        self.assertIn("really is empty", why)

    def test_it_never_reports_a_verdict_it_could_not_measure(self):
        """UNKNOWN and MISSING are different sentences. With nothing gated, the downstream checks
        must say 'could not check', never 'broken'."""
        vd._CACHE.update({"sampled": 30, "gated": 0, "measured": 0,
                          "occupied": 0, "free": 0, "refused": 0, "frames": []})
        d = vd.diagnose()
        self.assertEqual(self._state(d, "panels measure")[0], vd.UNKNOWN)
        self.assertEqual(self._state(d, "anything there")[0], vd.UNKNOWN)

    def test_the_sample_is_MID_reel(self):
        """Sampling the first frames of a reel found ZERO stash panels on footage that had ten —
        loading screens. A biased sample nearly produced 'your film has no stash in it'."""
        reel = os.path.join(self.root, "reel_s_2_2")
        os.makedirs(reel)
        for i in range(60):
            with open(os.path.join(reel, "f_%04d.jpg" % i), "wb") as fh:
                fh.write(b"\0")
        picked = [os.path.basename(p) for p in vd._frames()]
        self.assertTrue(picked, "no frames sampled at all")
        self.assertNotEqual(picked[0], "f_0000.jpg",
                            "the sample starts at frame 0 — that is the loading screen bias")


if __name__ == "__main__":
    unittest.main(verbosity=2)
