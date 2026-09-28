# -*- coding: utf-8 -*-
"""An item filed on a tier its visits never earned is FLAGGED, and it stays filed.

His ruling 2026-09-28 (§34.2), in his words: "Keep filed, flag 'retro: WATCHED'". Radiance and
the Horadric Cube came back HARDENED from the 2026-09-27 reset rebuild only because one still
screen counted as 21 to 103 looks. They stay filed, show their TRUE tier WATCHED 2/2 with a
retro flag, and must earn PROVEN/HARDENED with real looks.

So vault_evidence.retro_plan() names every such item as {name, recordedTier, honestTier, why},
and every row says keepFiled. It never writes and it has no apply half. It is exposed read-only
as the `retro` field of the plan the console already serves (POST /api/vault_rebuild_plan, via
control_app.vault_rebuild_plan). ⚠ The board's reset never reads `retro` — it files `rebuilt` —
so since 2026-09-28 (Ledger fix, finding 1) every flagged row ALSO rides in `rebuilt` at its true
tier with the flag, and is filed back rather than held.

Fixtures only, shaped like his real rows (measured read-only 2026-09-28: Radiance 103 frames
from 2 visits, the Cube 21 frames from 2 visits).
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

import vault_evidence as VE


def _still(session, bucket, n, prefix):
    return [{"session": session, "witness": "%s#%d" % (session, bucket),
             "frame": "%s_%03d.jpg" % (prefix, i), "conf": 0.93, "lane": "stash"}
            for i in range(n)]


def _ledger():
    shako, mesh = [], []
    for i in range(12):
        # twelve real visits, one frame each: PROVEN by visits AND by frames, so no retro
        shako += _still("s_shako_%02d" % i, 0, 1, "shako%02d" % i)
        # twelve real visits, two frames each: the frame math says 24 -> HARDENED, the visits
        # say PROVEN. A retro can land on PROVEN as well as on WATCHED.
        mesh += _still("s_mesh_%02d" % i, 0, 2, "mesh%02d" % i)
    return {"owned": [
        {"name": "Radiance", "lane": "stash", "kind": "item",
         "witnesses": _still("s_rad_A", 0, 1, "radA") + _still("s_rad_B", 0, 102, "radB")},
        {"name": "Horadric Cube", "lane": "stash", "kind": "item",
         "witnesses": _still("s_cube_A", 0, 20, "cubeA") + _still("s_cube_B", 0, 1, "cubeB")},
        {"name": "Shako", "lane": "stash", "kind": "item", "witnesses": shako},
        {"name": "Arachnid Mesh", "lane": "stash", "kind": "item", "witnesses": mesh},
        {"name": "Chance Guards", "lane": "stash", "kind": "item",
         "witnesses": _still("s_cg_A", 0, 1, "cgA") + _still("s_cg_B", 0, 1, "cgB")},
        {"name": "Unread Thing", "lane": "stash", "witnesses": 4},
    ]}


class TheRetroPlanKeepsThemFiled(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="retro-plan-")
        self.path = os.path.join(self.tmp, "witness.json")
        self.blob = json.dumps(_ledger()).encode("utf-8")
        with io.open(self.path, "wb") as fh:
            fh.write(self.blob)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _unchanged(self):
        with io.open(self.path, "rb") as fh:
            self.assertEqual(self.blob, fh.read(), "the retro plan wrote the witness ledger")

    def test_the_two_still_screens_are_named_with_their_true_tier(self):
        got = VE.retro_plan(self.path)
        self.assertTrue(got["ok"], got)
        by = dict((r["name"], r) for r in got["rows"])
        self.assertEqual({"Radiance", "Horadric Cube", "Arachnid Mesh"}, set(by),
                         "the retro plan must name exactly the items filed above their visits")
        self.assertEqual((VE.HARDENED, VE.PROVEN, "retro: PROVEN"),
                         (by["Arachnid Mesh"]["recordedTier"], by["Arachnid Mesh"]["honestTier"],
                          by["Arachnid Mesh"]["flag"]))
        for name in ("Radiance", "Horadric Cube"):
            row = by[name]
            self.assertEqual(VE.HARDENED, row["recordedTier"])
            self.assertEqual(VE.WATCHED, row["honestTier"])
            self.assertEqual("retro: WATCHED", row["flag"])
            self.assertEqual({"successes": 2, "trials": 2}, {k: row["visits"][k] for k in ("successes", "trials")})
            self.assertEqual("frames", row["recordedBy"],
                             "a tier derived from the frame math must say so, never read as the board's")
            self.assertIn("2 visit(s)", row["why"])
        self.assertEqual(103, by["Radiance"]["frames"]["trials"])
        self.assertEqual(21, by["Horadric Cube"]["frames"]["trials"])
        self._unchanged()

    def test_every_row_stays_filed_and_nothing_is_unfiled(self):
        got = VE.retro_plan(self.path)
        self.assertTrue(got["rows"])
        for row in got["rows"]:
            self.assertIs(True, row["keepFiled"], "%s was planned for an unfile" % row["name"])
            self.assertIn("never auto-unfiled", row["why"])
        for key in ("unfile", "apply", "remove", "clear"):
            self.assertNotIn(key, got, "the retro plan grew a %r half" % key)

    def test_an_honest_tier_is_not_flagged(self):
        got = VE.retro_plan(self.path)
        names = got["names"]
        self.assertNotIn("Shako", names, "twelve real visits are PROVEN, which is not a retro")
        self.assertNotIn("Chance Guards", names, "two visits read WATCHED both ways")
        self.assertNotIn("Unread Thing", names)

    def test_the_boards_own_record_is_what_it_compares_when_handed_in(self):
        board = {"Radiance": {"tier": "HARDENED"}, "Shako": "PROVEN",
                 "Chance Guards": "PROVEN", "Ghost Item": "HARDENED", "Unread Thing": "PROVEN"}
        got = VE.retro_plan(self.path, recorded=board)
        self.assertTrue(got["ok"], got)
        self.assertEqual("board", got["recordedBy"])
        by = dict((r["name"], r) for r in got["rows"])
        self.assertEqual({"Radiance", "Chance Guards"}, set(by),
                         "the Cube was never filed on this board, and Shako is honestly PROVEN")
        self.assertEqual("board", by["Chance Guards"]["recordedBy"])
        self.assertEqual(VE.PROVEN, by["Chance Guards"]["recordedTier"])
        self.assertEqual(["Unread Thing", "Ghost Item"], got["unjudged"],
                         "a filing with no readable evidence must be UNJUDGED, never honest")
        self._unchanged()

    def test_an_unreadable_ledger_is_unknown_not_none_flagged(self):
        got = VE.retro_plan(os.path.join(self.tmp, "absent.json"))
        self.assertFalse(got["ok"])
        self.assertIsNone(got["n"])
        self.assertIsNone(got["rows"])
        bad = VE.retro_plan(self.path, recorded="HARDENED")
        self.assertFalse(bad["ok"])
        self.assertIsNone(bad["n"])

    def test_the_console_serves_it_on_the_rebuild_plan(self):
        # 2026-09-28 (Ledger fix, finding 1): the board's reset files `rebuilt` and never reads
        # `retro`, so a flagged row has to BE in `rebuilt` — at its true tier, with the flag — or
        # "keep filed" is a sentence nothing obeys. test_a_reset_keeps_the_retro_rows_filed drives
        # the shipped door over this same shape.
        import control_app as CA
        plan = CA.vault_rebuild_plan(self.path)
        self.assertTrue(plan["ok"], plan)
        self.assertEqual({"Radiance", "Horadric Cube", "Arachnid Mesh"}, set(plan["retro"]["names"]))
        self.assertEqual(["Radiance", "Horadric Cube", "Shako", "Arachnid Mesh"],
                         [r["name"] for r in plan["rebuilt"]],
                         "a retro-flagged item is not in the field the reset files from")
        self.assertEqual([VE.WATCHED, VE.WATCHED, VE.PROVEN, VE.PROVEN],
                         [r["tier"] for r in plan["rebuilt"]],
                         "a retro row came back above the tier its visits earn")
        self.assertEqual(["retro: WATCHED", "retro: WATCHED", None, "retro: PROVEN"],
                         [r.get("flag") for r in plan["rebuilt"]])
        self.assertEqual([False, False, False, False], [r["locked"] for r in plan["rebuilt"]])
        self.assertEqual(["Chance Guards", "Unread Thing"], [r["name"] for r in plan["held"]])
        self._unchanged()


RED_PROOF = [
    {
        "why": "the rank test is inverted: an item filed ABOVE its visits is no longer flagged",
        "file": "vault_evidence.py",
        "find": "    if _TIER_RANK[rec] <= _TIER_RANK[honest[\"tier\"]]:\n",
        "replace": "    if _TIER_RANK[rec] >= _TIER_RANK[honest[\"tier\"]]:\n",
        "matches": 1,
    },
    {
        "why": "a flagged item is planned for an unfile, against his ruling",
        "file": "vault_evidence.py",
        "find": "            \"flag\": \"retro: %s\" % honest[\"tier\"], \"keepFiled\": True, \"recordedBy\": by,\n",
        "replace": "            \"flag\": \"retro: %s\" % honest[\"tier\"], \"keepFiled\": False, \"recordedBy\": by,\n",
        "matches": 1,
    },
    {
        "why": "the plan the console serves drops the retro flags",
        "file": "vault_evidence.py",
        "find": "    plan[\"retro\"] = _retro_answer(retro, \"frames\")\n",
        "replace": "    plan[\"retro\"] = _retro_answer([], \"frames\")\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
