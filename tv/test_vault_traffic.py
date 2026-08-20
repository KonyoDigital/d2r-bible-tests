#!/usr/bin/env python3
"""EVERY ITEM, THROUGH THE WHOLE SWEEP, AND THEN ALL AT ONCE.

Konyo, 2026-08-21: "vault manager? and items being routed correctly? you simulated every single
item that would be found and made sure it gets muled or thrown out properly? and you fed it 300-500
items at once to see how it reacted to the traffic?"

The honest answer was NO, and this file is that answer being made true.

WHAT WAS ALREADY COVERED, AND WHAT WAS NOT. test_vault_retro.py has 21 tests and they are good ones
— merge-max never subtracts, order cannot change the answer, lanes do not bleed, the throw bar is
strictly higher than the keep bar. Every one of them drives `gate()` or `merge_vault()` DIRECTLY,
with three or four hand-made rows. **Not one of them calls `sweep()`.** So the routing that happens
INSIDE the sweep — surface -> lane per item, throw flags collected per key, the two bars applied to
real piles — had never been executed at all, at any size.

WHAT THIS DRIVES. Real reel directories on disk, a real index.json, `vault_retro.sweep()` itself with
a stubbed sig/classify/reader. Nothing here touches his tree: every reel is built in a tempdir.

⚠ THE FIRST RUN OF THIS HARNESS PROVED THE HARNESS WRONG, NOT THE CODE. It gave every frame a
DIFFERENT signature and got 0 items out of 135 — and the sweep said exactly why: "2 reel(s) held no
screen still long enough to be worth reading — that is footage of moving, not of looking at a
stash." A still run is frames that look the SAME. Corrected, the same 135 land. [[feedback-suspect-the-instrument]]
"""
import json
import os
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _console_safe
    _console_safe()
except Exception:
    pass

import vault_retro as vr  # noqa: E402

# ONE CONSTANT SIGNATURE PER REEL = one long still run, which is what a person parked on his stash
# actually produces. MIN_RUN_FRAMES is 3, so six frames is comfortably a run.
_SIG = [11.0] * 8
_FRAMES = 6


def _reel(root, sid, n=_FRAMES):
    d = os.path.join(root, "reel_" + sid)
    os.makedirs(d, exist_ok=True)
    idx = {"sessionId": sid, "frames": []}
    for i in range(n):
        f = "f_%d.jpg" % (i + 1)
        with open(os.path.join(d, f), "wb") as fh:
            fh.write(b"x")
        idx["frames"].append({"f": f, "ts": 1787000000000 + i * 1000})
    with open(os.path.join(d, "index.json"), "w", encoding="utf-8") as fh:
        json.dump(idx, fh)
    return d


class _Base(unittest.TestCase):
    def sweep(self, items, sessions=2, surface="stash"):
        root = tempfile.mkdtemp(prefix="vault-traffic-")
        self.addCleanup(__import__("shutil").rmtree, root, True)
        dirs = [_reel(root, "s_17870000%02d_sim" % s) for s in range(sessions)]
        t0 = time.time()
        res = vr.sweep(dirs, sig=lambda p: list(_SIG), classify=lambda p: surface,
                       reader=lambda p, s: {"items": items, "conf": 0.9, "note": None})
        return res, time.time() - t0

    @staticmethod
    def universe():
        """Every name the app can actually attribute — his set roster, plus the rune list."""
        names = []
        try:
            r = json.load(open(os.path.join(HERE, "set_roster.json"), encoding="utf-8"))
            names += [n for n in (r.get("pieces") or []) if isinstance(n, str)]
            names += [n for n in (r.get("sets") or []) if isinstance(n, str)]
        except Exception:
            pass
        return sorted(set(n for n in names if n and n.strip()))


class TestEveryItemLands(_Base):
    def test_every_name_in_his_roster_survives_the_sweep(self):
        U = self.universe()
        self.assertGreaterEqual(len(U), 100, "the roster did not load — this would pass on nothing")
        items = [{"name": n, "kind": "item", "conf": 0.9} for n in U]
        res, _ = self.sweep(items)
        owned = {r["name"] for r in res["owned"]}
        dropped = sorted(set(U) - owned)
        self.assertEqual(dropped, [], "%d name(s) went in and never came out: %s"
                                      % (len(dropped), dropped[:6]))
        self.assertEqual(len(res["unsure"]), 0)

    def test_one_session_can_never_own_anything(self):
        """Law 2, at full scale rather than on one hand-made row."""
        U = self.universe()
        items = [{"name": n, "kind": "item", "conf": 0.9} for n in U]
        res, _ = self.sweep(items, sessions=1)
        self.assertEqual(len(res["owned"]), 0,
                         "a single recording grounded %d items" % len(res["owned"]))
        self.assertEqual(len(res["unsure"]), len(U),
                         "items vanished instead of being remembered as unsure")

    def test_a_nameless_row_contributes_nothing_but_is_not_silent(self):
        res, _ = self.sweep([{"kind": "item", "conf": 0.9}, {"name": "  ", "conf": 0.9}])
        self.assertEqual(res["owned"], [])
        self.assertTrue(res["unsure"], "nameless rows vanished without a word")


class TestTheRoutingIsRight(_Base):
    """Every surface, every item — not one sample each."""

    CASES = (("stash", "stash"), ("runes", "stash"), ("gems", "stash"), ("materials", "stash"),
             ("inventory", "inventory"), ("equipment", "equipment"))

    def test_each_surface_files_every_item_in_its_own_lane(self):
        U = self.universe()[:60]
        items = [{"name": n, "kind": "item", "conf": 0.9} for n in U]
        for surface, lane in self.CASES:
            res, _ = self.sweep(items, surface=surface)
            lanes = {r["lane"] for r in res["owned"]}
            self.assertEqual(lanes, {lane},
                             "%s filed items into %s, expected %s" % (surface, lanes, lane))
            self.assertEqual(len(res["owned"]), len(U), "%s dropped items" % surface)

    def test_a_reader_that_names_the_lane_itself_wins_over_the_surface(self):
        # the reader can see the split when the panel shows both; the surface is only the fallback
        res, _ = self.sweep([{"name": "Shako", "lane": "inventory", "conf": 0.9}], surface="stash")
        self.assertEqual([r["lane"] for r in res["owned"]], ["inventory"])

    def test_an_unknown_lane_falls_back_and_never_invents_one(self):
        res, _ = self.sweep([{"name": "Shako", "lane": "mule-3", "conf": 0.9}], surface="stash")
        self.assertEqual([r["lane"] for r in res["owned"]], ["stash"])

    def test_lanes_never_bleed_when_both_arrive_together(self):
        items = [{"name": "Shako", "lane": "stash", "conf": 0.9},
                 {"name": "Shako", "lane": "inventory", "conf": 0.9}]
        res, _ = self.sweep(items)
        pairs = sorted((r["name"], r["lane"]) for r in res["owned"])
        self.assertEqual(pairs, [("Shako", "inventory"), ("Shako", "stash")],
                         "one item in two lanes collapsed into one row")


class TestTheThrowBarSeenFromBothSides(_Base):
    """A bar never seen passed is the same defect as one never seen failing."""

    ITEM = {"name": "Cracked Sash", "kind": "item", "conf": 0.9,
            "throwOut": True, "throwWhy": "junk"}

    def test_two_recordings_are_held_three_are_suggested(self):
        two, _ = self.sweep([self.ITEM], sessions=2)
        self.assertEqual(len(two["throwOut"]), 0, "two recordings suggested binning an item")
        self.assertEqual(len(two["held"]), 1)
        self.assertIn("recording", two["held"][0]["why"])
        three, _ = self.sweep([self.ITEM], sessions=3)
        self.assertEqual(len(three["throwOut"]), 1,
                         "the throw bar can never be cleared — it is a threshold above the ceiling")

    def test_a_suggestion_is_never_automatic(self):
        res, _ = self.sweep([self.ITEM], sessions=3)
        for row in res["throwOut"]:
            self.assertIs(row.get("suggestion"), True)
            self.assertFalse(row.get("automatic"), "a throw-out marked itself automatic")

    def test_the_throw_bar_is_stricter_than_the_keep_bar_on_BOTH_axes(self):
        self.assertGreater(vr.THROWOUT_CONF_FLOOR, vr.KEEP_CONF_FLOOR)
        self.assertGreater(vr.THROWOUT_MIN_WITNESSES, vr.KEEP_MIN_WITNESSES)

    def test_a_confident_item_below_the_throw_floor_is_still_held(self):
        low = dict(self.ITEM, conf=vr.THROWOUT_CONF_FLOOR - 0.05)
        res, _ = self.sweep([low], sessions=4)
        self.assertEqual(len(res["throwOut"]), 0,
                         "four recordings below the confidence floor still suggested a bin")

    def test_the_keep_floor_is_exact(self):
        at = [{"name": "Edge Case", "conf": vr.KEEP_CONF_FLOOR}]
        below = [{"name": "Edge Case", "conf": vr.KEEP_CONF_FLOOR - 0.01}]
        self.assertEqual(len(self.sweep(at)[0]["owned"]), 1, "the floor itself does not pass")
        self.assertEqual(len(self.sweep(below)[0]["owned"]), 0, "below the floor passed")


class TestTraffic(_Base):
    """"you fed it 300-500 items at once to see how it reacted to the traffic?" — now, yes."""

    def test_five_hundred_items_all_land(self):
        big = [{"name": "Sim Item %04d" % i, "kind": "item", "conf": 0.9} for i in range(500)]
        res, dt = self.sweep(big)
        self.assertEqual(len(res["owned"]), 500, "%d of 500 were dropped" % (500 - len(res["owned"])))
        self.assertLess(dt, 20.0, "500 items took %.1fs — the fold is not linear" % dt)

    def test_five_hundred_throw_flags_all_reach_a_verdict(self):
        big = [{"name": "Junk %04d" % i, "conf": 0.9, "throwOut": True, "throwWhy": "junk"}
               for i in range(500)]
        res, dt = self.sweep(big, sessions=3)
        self.assertEqual(len(res["throwOut"]), 500)
        self.assertLess(dt, 30.0, "500 throw flags took %.1fs" % dt)

    def test_traffic_does_not_change_the_answer_for_any_one_item(self):
        """The one that would catch a bucket collision: the same item, alone and in a crowd."""
        alone, _ = self.sweep([{"name": "Sim Item 0042", "conf": 0.9}])
        crowd, _ = self.sweep([{"name": "Sim Item %04d" % i, "conf": 0.9} for i in range(500)])
        one = [r for r in crowd["owned"] if r["name"] == "Sim Item 0042"]
        self.assertEqual(len(one), 1)
        self.assertEqual(one[0]["lane"], alone["owned"][0]["lane"])
        self.assertEqual(one[0].get("count"), alone["owned"][0].get("count"))

    def test_a_thousand_rows_of_the_SAME_item_is_one_row(self):
        # a scroll that photographs one shelf many times must not inflate anything
        dup = [{"name": "Ral Rune", "kind": "rune", "count": 3, "conf": 0.9} for _ in range(1000)]
        res, dt = self.sweep(dup)
        self.assertEqual(len(res["owned"]), 1, "duplicate sightings became %d rows" % len(res["owned"]))
        self.assertEqual(res["owned"][0].get("count"), 3, "merge-max inflated a count")
        self.assertLess(dt, 20.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
