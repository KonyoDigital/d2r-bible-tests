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
        # 2026-09-28 (Ledger fix, finding 1) — FLIPPED. This asserted both were HELD, i.e. un-filed
        # on his next reset. His ruling (§34.2) is "Keep filed, flag 'retro: WATCHED'": they come
        # back at their TRUE tier, WATCHED, unlocked, with the flag — never HARDENED again.
        self.assertEqual(["Radiance", "Horadric Cube"], [r["name"] for r in plan["rebuilt"]],
                         "a retro-flagged still screen was un-filed by the reset")
        self.assertEqual([], plan["held"])
        self.assertEqual({(2, 2)}, {(r["successes"], r["trials"]) for r in plan["rebuilt"]})
        self.assertEqual({(VE.WATCHED, False, "retro: WATCHED", True)},
                         {(r["tier"], r["locked"], r["flag"], r["keepFiled"]) for r in plan["rebuilt"]},
                         "a still screen came back above its visits, or without his flag")
        with io.open(path, "rb") as fh:
            self.assertEqual(blob, fh.read())


    # ══ 2026-09-28 (Ledger fix, finding 5) — successes fold on their own, as gate() does ══════
    def test_a_bare_prior_that_saw_it_beside_its_own_bucket_that_did_not_is_one_success(self):
        # gate() folds the qualifying looks SEPARATELY from all looks. _measure folded all first,
        # dropped the bare "s1" for "s1#0", found no success in "s1#0" and read 0 — gate read 1.
        looks = [{"session": "s1", "frame": "a1.jpg", "conf": 0.9, "lane": "stash"},
                 {"session": "s1", "witness": "s1#0", "frame": None, "conf": 0.0, "lane": "stash"}]
        live = VR.gate(looks)
        self.assertEqual((1, 1), (live["witnesses"], live["looksSeen"]),
                         "baseline: the live gate reads ONE qualifying look out of ONE")
        got = VE._measure([{"name": "S", "witnesses": looks}], _floor())
        self.assertEqual((1, 1), (got[0], got[1]),
                         "the tier table read %d success(es) where the live gate reads 1" % got[0])

    # ══ 2026-09-28 (Ledger fix, finding 7) — one reel, two spellings, is ONE look in BOTH ═════
    def test_one_reel_spelled_two_ways_is_one_look_in_both_engines(self):
        # vault_retro mints sid from sessionId OR basename(reel_dir), so one reel can arrive as
        # "reel_s1" and "s1". chronicle_retro._reel_key calls them one reel; so must the look id.
        import chronicle_retro as CR
        self.assertEqual(CR._reel_key("reel_s1#0"), CR._reel_key("s1#0"),
                         "baseline: the reel key already calls these one reel")
        looks = [{"session": "reel_s1", "witness": "reel_s1#0", "frame": "a.jpg", "conf": 0.9,
                  "lane": "stash"},
                 {"session": "s1", "witness": "s1#0", "frame": "b.jpg", "conf": 0.9, "lane": "stash"}]
        live = VR.gate(looks)
        self.assertEqual((1, 1), (live["witnesses"], live["looksSeen"]),
                         "the live gate counted one reel's two spellings as %d looks" % live["looksSeen"])
        got = VE._measure([{"name": "R", "witnesses": looks}], _floor())
        self.assertEqual((1, 1), (got[0], got[1]),
                         "the tier table counted one reel's two spellings as %d visits" % got[1])
        self.assertEqual(VE._visit_of(looks[0]), VE._visit_of(looks[1]))

    # ══ 2026-09-28 (Ledger fix round 2, finding D) — "a look that saw it" is ONE definition ═════
    # gate()._qualifies rejected a bool/string conf and ignored `saw`/`hit`; vault_evidence's
    # _is_success accepted True / "0.9" through float() and rejected a miss. So the keep bar and the
    # tier table disagreed about the SAME look. Each odd look below sits beside one plain good look
    # in a different visit: both engines must count the good one and refuse the odd one alike.
    ODD_LOOKS = (
        ("a bool conf", {"conf": True}),
        ("a numeric-string conf", {"conf": "0.9"}),
        ("a NaN conf", {"conf": float("nan")}),
        ("a blank frame", {"frame": "   "}),
        ("a look that says it saw a miss", {"saw": "miss"}),
        ("a look that says it saw an empty cell", {"saw": "empty"}),
        ("a look marked hit False", {"hit": False}),
    )

    def test_a_look_that_saw_it_is_one_definition_in_both_engines(self):
        good = {"session": "sG", "witness": "sG#0", "frame": "good.jpg", "conf": 0.9, "lane": "stash"}
        self.assertEqual((1, 1), (VR.gate([good])["witnesses"],
                                  VE._measure([{"name": "G", "witnesses": [good]}], _floor())[0]),
                         "baseline: both engines count the plain good look")
        for label, patch in self.ODD_LOOKS:
            odd = {"session": "sO", "witness": "sO#0", "frame": "odd.jpg", "conf": 0.9, "lane": "stash"}
            odd.update(patch)
            live = VR.gate([good, odd])["witnesses"]
            tier = VE._measure([{"name": "O", "witnesses": [good, odd]}], _floor())[0]
            self.assertEqual(live, tier,
                             "%s: the keep gate counts %d look(s) that saw it and the tier table %d — "
                             "two definitions of one look" % (label, live, tier))
            self.assertEqual(1, live, "%s counted as a look that saw it" % label)

    @staticmethod
    def _names(fn):
        """Every global/attribute name a function's code references, nested comprehensions included
        (a comprehension is its own code object before Python 3.12)."""
        out, todo = set(), [fn.__code__]
        while todo:
            co = todo.pop()
            out.update(co.co_names)
            todo.extend(c for c in co.co_consts if hasattr(c, "co_names"))
        return out

    def test_every_counter_calls_the_one_definition(self):
        # the compiler, not the text: each counter REFERENCES look_saw_it (source-reading-guard §1)
        self.assertTrue(callable(getattr(VR, "look_saw_it", None)), "there is no one definition to call")
        self.assertIn("look_saw_it", self._names(VR.gate), "gate() keeps its own copy")
        self.assertIn("look_saw_it", self._names(VR.gate_shadow), "gate_shadow keeps its own copy")
        self.assertIn("look_saw_it", self._names(VE._is_success), "_is_success keeps its own copy")
        self.assertIs(True, VR.look_saw_it({"frame": "f.jpg", "conf": 0.55}),
                      "baseline: a framed look AT the floor saw it")
        self.assertIs(False, VR.look_saw_it({"frame": "f.jpg", "conf": 0.54}))


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

    def test_the_joint_is_per_item_so_two_wrong_items_cannot_balance(self):
        # ══ 2026-09-28 (Ledger fix, finding 4) ══ StillScreen: 1 visit x 25 frames. TenLooks: 10
        # re-look buckets, 5 of them unsure. With the frame math back, StillScreen reads HARDENED
        # on 1 look and TenLooks stays WATCHED 5/10 with 10 gate looks — a COUNT compare read 1 vs 1.
        import unittest.mock as mock
        ten = []
        for b in range(10):
            ten += _still("s_ten", b, 1, "ten%02d" % b, conf=0.9 if b < 5 else 0.2)
        doc = {"owned": [
            {"name": "StillScreen", "lane": "stash", "kind": "item",
             "witnesses": _still("s_still", 0, 25, "still")},
            {"name": "TenLooks", "lane": "stash", "kind": "item", "witnesses": ten}]}
        with io.open(self.path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        self.assertEqual(10, VR.gate(ten)["looksSeen"], "baseline: the gate sees TenLooks' 10 looks")
        orig = VE._measure

        def frame_math(rows, floor):
            got = orig(rows, floor)
            if got is None:
                return None
            return (got[5]["successes"], got[5]["trials"]) + tuple(got[2:])

        with mock.patch.object(VE, "_measure", frame_math):
            census = VE.tier_census(self.path)
            row = self._row()
        self.assertEqual((1, 1), (census["proven"] + census["hardened"], census["watched"]),
                         "baseline: the frame math files exactly one item PROVEN+ and one WATCHED")
        self.assertEqual(self.C.DISAGREE, row["state"],
                         "a PROVEN+ item with 1 gate look was paid for by a different item's 10: %r"
                         % (row,))
        self.assertEqual((1, 0), (row["left"]["value"], row["right"]["value"]))
        self.assertEqual(["StillScreen"], census["provenNames"],
                         "the census does not name WHICH item it files PROVEN+")
        honest = self._row()
        self.assertEqual(self.C.AGREE, honest["state"], honest)

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
        "file": "vault_retro.py",
        "find": "    raw = e.get(witness_field) or e.get(\"session\")\n",
        "replace": "    raw = e.get(\"session\")\n",
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
        "find": "                   if vr.gate(piles.get(name, [])).get(\"looksSeen\", 0) >= ve.TRIALS_PROVEN)\n",
        "replace": "                   if len(piles.get(name, [])) >= ve.TRIALS_PROVEN)\n",
        "matches": 1,
    },
    {
        "why": "the heart joint compares COUNTS over the whole ledger again, so a PROVEN+ item with "
               "one look is paid for by a different item's ten (finding 4)",
        "file": "corroborate.py",
        "find": "        return sum(1 for name in names\n",
        "replace": "        return sum(1 for name in piles\n",
        "matches": 1,
    },
    {
        "why": "the tier table folds every visit before asking for a success, so a bare prior that saw "
               "it reads 0 where the live gate reads 1 (finding 5)",
        "file": "vault_evidence.py",
        "find": "    success_ids = set(fold(won))\n",
        "replace": "    success_ids = visits & set(won)\n",
        "matches": 1,
    },
    {
        "why": "the look id reads the raw string, so one reel spelled two ways is two looks (finding 7)",
        "file": "vault_retro.py",
        "find": "    return _cr._reel_key(str(raw)) if raw else \"\"\n",
        "replace": "    return str(raw) if raw else \"\"\n",
        "matches": 1,
    },
    {
        "why": "the live gate stops asking look_id and keys on the raw spelling again (finding 7)",
        "file": "vault_retro.py",
        "find": "    seen_all = _fold_bare_sessions({look_id(e, witness_field) for e in ev})\n",
        "replace": ("    seen_all = _fold_bare_sessions({str(e.get(witness_field) or e.get(\"session\")) "
                    "for e in ev if (e.get(witness_field) or e.get(\"session\"))})\n"),
        "matches": 1,
    },
    {
        "why": "the tier table keeps its own copy of the look id, so the two engines drift (finding 7)",
        "file": "vault_evidence.py",
        "find": "    return VR.look_id(look, \"witness\")\n",
        "replace": "    return str(look.get(\"witness\") or look.get(\"session\") or \"\")\n",
        "matches": 1,
    },
    {
        "why": "the tier table keeps its own float() copy of 'a look that saw it', so a bool conf is a success there and not at the gate (finding D)",
        "file": "vault_evidence.py",
        "find": "    return VR.look_saw_it(look, floor)\n",
        "replace": ("    try:\n        return float(look.get(\"conf\")) >= floor and bool(str(look.get(\"frame\") or \"\").strip())"
                    " and str(look.get(\"saw\") or \"\").strip().lower() not in VR.MISS_SAWS and look.get(\"hit\") is not False\n"
                    "    except (TypeError, ValueError):\n        return False\n"),
        "matches": 1,
    },
    {
        "why": "the one definition drops the miss check, so a look that says it saw an empty cell counts (finding D)",
        "file": "vault_retro.py",
        "find": "    if str(e.get(\"saw\") or \"\").strip().lower() in MISS_SAWS or e.get(\"hit\") is False:\n        return False\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "the one definition takes a string or bool conf through float() again (finding D)",
        "file": "vault_retro.py",
        "find": "    if isinstance(c, bool) or not isinstance(c, (int, float)):\n        return False\n    if c != c",
        "replace": "    try:\n        c = float(c)\n    except (TypeError, ValueError):\n        return False\n    if c != c",
        "matches": 1,
    },
    {
        "why": "the one definition accepts a blank frame, a picture nobody can open (finding D)",
        "file": "vault_retro.py",
        "find": "    if not str(e.get(\"frame\") or \"\").strip():\n        return False\n",
        "replace": "    if not e.get(\"frame\"):\n        return False\n",
        "matches": 1,
    },
    {
        "why": "a retro-flagged still screen is held by the plan, so his next reset un-files it (finding 1)",
        "file": "vault_evidence.py",
        "find": "        elif got[\"tier\"] == WATCHED and not kept and not retro:\n",
        "replace": "        elif got[\"tier\"] == WATCHED and not kept:\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
