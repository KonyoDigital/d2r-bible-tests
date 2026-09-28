# -*- coding: utf-8 -*-
"""A still screen is ONE look. A trial is a distinct VISIT, never a frame.

His ruling 2026-09-28 (§34.2): "Keep filed, flag 'retro: WATCHED'" — and the reason the flag is
needed at all: P0 fixes the math, "a look is a distinct visit, never a frame of a still screen."

MEASURED on his real vault_accum.json 2026-09-28, read-only: Radiance held 103 witness rows. 102
of them carried ONE re-look id, `s_…57378#0` — one stash screen held still and photographed 102
times — and the 103rd came from a second recording. vault_evidence._measure did `trials += 1`
per ROW, so Radiance scored HARDENED 103/103 (bound 0.964) on two looks. The Horadric Cube did
the same on 20 + 1 rows. Honest: WATCHED 2/2 each.

THE LAW IS NOT NEW. vault_retro.py already states it beside its own Wilson note: "Wilson runs on
the FOLDED WITNESS LIST, never on raw sightings. Four re-reads of one frozen frame are one eye
looking twice." gate() counts `witness or session` — the re-look bucket the sweep mints at every
REOPEN_GAP_MS gap — folded by _fold_bare_sessions. _measure now counts the same thing, and this
file pins that the two cannot drift apart. [[copy-drift]]

Fixtures only. His stores are read for SHAPE by the note above and never touched here.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable; enable()

import vault_evidence as VE
import vault_retro as VR


def _still(session, bucket, n, frame_prefix, conf=0.91):
    """n frames of ONE held screen: one session, one re-look bucket, n different frame files."""
    return [{"session": session, "witness": "%s#%d" % (session, bucket),
             "frame": "%s_%03d.jpg" % (frame_prefix, i), "conf": conf, "lane": "stash"}
            for i in range(n)]


def _radiance_row():
    # The shape of his real row: 102 frames under one re-look id, one frame from another recording.
    looks = _still("s_rad_A", 0, 1, "radA") + _still("s_rad_B", 0, 102, "radB")
    return {"name": "Radiance", "lane": "stash", "kind": "item", "witnesses": looks}


def _floor():
    return float(VR.KEEP_CONF_FLOOR)


class AStillScreenIsOneLook(unittest.TestCase):

    def test_radiance_shaped_row_is_watched_two_of_two_not_hardened(self):
        got = VE._measure([_radiance_row()], _floor())
        self.assertIsNotNone(got, "a readable row was called unreadable")
        successes, trials = got[0], got[1]
        self.assertEqual((2, 2), (successes, trials),
                         "103 frames from 2 visits were counted as %d/%d trials — a trial is a "
                         "visit, never a frame" % (successes, trials))
        self.assertEqual(VE.WATCHED, VE.tier(successes, trials)["tier"])

    def test_the_frame_count_rides_beside_the_visit_count_never_instead(self):
        got = VE._measure([_radiance_row()], _floor())
        frames = got[5]
        self.assertEqual(103, frames["trials"], "the raw frame count was dropped, so the retro "
                         "plan cannot say what the frame math called this item")
        self.assertEqual(103, frames["successes"])
        self.assertEqual(VE.HARDENED, VE.tier(frames["successes"], frames["trials"])["tier"],
                         "baseline: counted by frames this row IS hardened — the case can tell "
                         "the two maths apart")

    def test_twenty_frames_of_one_screen_stay_watched(self):
        row = {"name": "Horadric Cube", "lane": "stash", "kind": "item",
               "witnesses": _still("s_cube", 0, 20, "cube")}
        got = VE._measure([row], _floor())
        self.assertEqual((1, 1), (got[0], got[1]))
        self.assertEqual(VE.WATCHED, VE.tier(got[0], got[1])["tier"])

    def test_a_re_look_after_the_gap_is_its_own_visit(self):
        # One recording, twelve REOPEN_GAP_MS buckets: twelve times he left the stash and came back.
        # The keep bar counts a re-look (vault_retro v1792), so the tier table does too.
        looks = []
        for b in range(12):
            looks += _still("s_one_reel", b, 3, "relook%02d" % b)
        row = {"name": "Shako", "lane": "stash", "kind": "item", "witnesses": looks}
        got = VE._measure([row], _floor())
        self.assertEqual((12, 12), (got[0], got[1]),
                         "the re-look bucket was ignored, so twelve visits read as one")
        self.assertEqual(VE.PROVEN, VE.tier(got[0], got[1])["tier"])

    def test_a_bare_prior_beside_its_own_bucket_is_one_visit_not_two(self):
        # _fold_bare_sessions: a persisted prior carries no witness id, so "sA" and "sA#0" are one
        # look that the string compare would count twice.
        looks = [{"session": "sA", "frame": "a1.jpg", "conf": 0.9, "lane": "stash"},
                 {"session": "sA", "witness": "sA#0", "frame": "a2.jpg", "conf": 0.9, "lane": "stash"},
                 {"session": "sB", "witness": "sB#0", "frame": "b1.jpg", "conf": 0.9, "lane": "stash"}]
        got = VE._measure([{"name": "X", "witnesses": looks}], _floor())
        self.assertEqual((2, 2), (got[0], got[1]))

    def test_a_visit_that_only_missed_is_a_failed_trial(self):
        looks = (_still("s1", 0, 4, "hit1") + _still("s2", 0, 2, "hit2")
                 + [dict(l, saw="empty") for l in _still("s3", 0, 5, "miss3")])
        got = VE._measure([{"name": "Y", "witnesses": looks}], _floor())
        self.assertEqual((2, 3), (got[0], got[1]),
                         "a visit that saw the cell empty must count against the item once, "
                         "not five times and not zero times")

    def test_the_visit_count_is_the_one_vault_retro_gate_counts(self):
        # The same independence law, two engines: gate()'s distinct looks == _measure's visits.
        looks = (_still("s_rad_A", 0, 1, "radA") + _still("s_rad_B", 0, 102, "radB")
                 + [{"session": "s_old", "frame": "old.jpg", "conf": 0.8, "lane": "stash"}]
                 + _still("s_two", 0, 2, "twoA") + _still("s_two", 1, 2, "twoB"))
        got = VE._measure([{"name": "Z", "witnesses": looks}], _floor())
        live = VR.gate(looks)
        self.assertEqual(live["looksSeen"], got[1],
                         "the tier table and the live gate count different things as a look: "
                         "gate %d vs tier %d" % (live["looksSeen"], got[1]))
        self.assertEqual(live["witnesses"], got[0])

    def test_one_frame_per_visit_is_cited(self):
        tmp = tempfile.mkdtemp(prefix="still-screen-")
        self.addCleanup(shutil.rmtree, tmp, True)
        path = os.path.join(tmp, "witness.json")
        blob = json.dumps({"owned": [_radiance_row()]}).encode("utf-8")
        with io.open(path, "wb") as fh:
            fh.write(blob)
        cited = VE.cited_frames(path)
        self.assertTrue(cited["ok"], cited)
        self.assertEqual(["radA_000.jpg", "radB_000.jpg"], cited["frames"])
        with io.open(path, "rb") as fh:
            self.assertEqual(blob, fh.read(), "citing frames wrote the witness ledger")

    def test_the_census_and_the_plan_both_read_the_visits(self):
        tmp = tempfile.mkdtemp(prefix="still-screen-")
        self.addCleanup(shutil.rmtree, tmp, True)
        path = os.path.join(tmp, "witness.json")
        doc = {"owned": [_radiance_row(),
                         {"name": "Horadric Cube", "lane": "stash", "kind": "item",
                          "witnesses": _still("s_cube_A", 0, 20, "cubeA") + _still("s_cube_B", 0, 1, "cubeB")}]}
        blob = json.dumps(doc).encode("utf-8")
        with io.open(path, "wb") as fh:
            fh.write(blob)
        census = VE.tier_census(path)
        self.assertTrue(census["ok"], census)
        self.assertEqual((2, 0, 0), (census["watched"], census["proven"], census["hardened"]),
                         "one still screen still reads as hardened in the census")
        self.assertEqual([], census["disagree"])
        plan = VE.plan_from_ledger(path)
        self.assertTrue(plan["ok"], plan)
        self.assertEqual([], plan["rebuilt"], "a still screen was rebuilt after a reset")
        self.assertEqual(["Radiance", "Horadric Cube"], [r["name"] for r in plan["held"]])
        self.assertEqual({(2, 2)}, {(r["successes"], r["trials"]) for r in plan["held"]})
        with io.open(path, "rb") as fh:
            self.assertEqual(blob, fh.read())


class TheHeartJointSeesAStillScreen(unittest.TestCase):
    """corroborate's `a-tier-stands-on-its-looks`: the tier table against the live gate's looks."""

    def setUp(self):
        import corroborate as C
        self.C = C
        self.tmp = tempfile.mkdtemp(prefix="still-joint-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.path = os.path.join(self.tmp, "vault_accum.json")
        shako = []
        for i in range(12):
            shako += _still("s_shako_%02d" % i, 0, 1, "shako%02d" % i)
        doc = {"owned": [_radiance_row(),
                         {"name": "Shako", "lane": "stash", "kind": "item", "witnesses": shako}]}
        with io.open(self.path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        self._env = os.environ.get("TV_VAULT_LEDGER")
        os.environ["TV_VAULT_LEDGER"] = self.path
        self.addCleanup(self._restore_env)

    def _restore_env(self):
        if self._env is None:
            os.environ.pop("TV_VAULT_LEDGER", None)
        else:
            os.environ["TV_VAULT_LEDGER"] = self._env

    def _row(self):
        return self.C.check_one(self.C._inv_a_tier_stands_on_the_looks_the_gate_counts)

    def test_the_tier_and_the_gate_agree_on_a_real_question(self):
        row = self._row()
        self.assertEqual(self.C.AGREE, row["state"], row)
        self.assertEqual((1, 1), (row["left"]["value"], row["right"]["value"]),
                         "the joint agreed at 0 vs 0, which cannot tell healthy from inert")

    def test_the_joint_disagrees_when_the_tier_counts_frames(self):
        import unittest.mock as mock
        orig = VE._measure

        def frame_math(rows, floor):
            got = orig(rows, floor)
            if got is None:
                return None
            return (got[5]["successes"], got[5]["trials"]) + tuple(got[2:])

        with mock.patch.object(VE, "_measure", frame_math):
            row = self._row()
        self.assertEqual(self.C.DISAGREE, row["state"], row)
        self.assertEqual((2, 1), (row["left"]["value"], row["right"]["value"]))

    def test_an_unreadable_ledger_is_unknown_not_agreement(self):
        os.environ["TV_VAULT_LEDGER"] = os.path.join(self.tmp, "absent.json")
        row = self._row()
        self.assertEqual(self.C.UNKNOWN, row["state"], row)

    def test_the_doctor_row_is_covered_by_this_joint(self):
        self.assertIn("a-tier-stands-on-its-looks", self.C.COVERED_BY.get("evidence tiers", ()))
        self.assertNotIn("evidence tiers", self.C.NO_JOINT_YET)
        self.assertIn(self.C._inv_a_tier_stands_on_the_looks_the_gate_counts, self.C.BUILDERS)


RED_PROOF = [
    {
        "why": "the tier counts frames again: one still screen photographed 103 times reads HARDENED",
        "file": "vault_evidence.py",
        "find": "    return successes, trials, sessions, cells, witness_sessions, frames\n",
        "replace": ("    return (frames[\"successes\"], frames[\"trials\"], sessions, cells, "
                    "witness_sessions, frames)\n"),
        "matches": 1,
    },
    {
        "why": "the re-look bucket is dropped: twelve visits in one recording read as one",
        "file": "vault_evidence.py",
        "find": "    key = look.get(\"witness\") or look.get(\"session\")\n",
        "replace": "    key = look.get(\"session\")\n",
        "matches": 1,
    },
    {
        "why": "the bare-prior fold is skipped: one look counts as two visits",
        "file": "vault_evidence.py",
        "find": "    visits = set(fold(order))\n",
        "replace": "    visits = set(order)\n",
        "matches": 1,
    },
    {
        "why": "the heart joint counts witness ROWS on its gate side, so a still screen clears it",
        "file": "corroborate.py",
        "find": "                   if vr.gate(ev).get(\"looksSeen\", 0) >= ve.TRIALS_PROVEN)\n",
        "replace": "                   if len(ev) >= ve.TRIALS_PROVEN)\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
