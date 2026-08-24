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
    def sweep(self, items, sessions=None, surface="stash"):
        # v2073 — DEFAULT TRACKS THE LAW, NOT A NUMBER. These helpers hardcoded sessions=2, so
        # when his ruling moved KEEP_MIN_WITNESSES to 3 every "this grounds" case in this file was
        # silently testing a bar that no longer exists — 19 of them went red at once on CI while
        # the local run I was doing (test_control only) stayed green.
        if sessions is None:
            sessions = vr.KEEP_MIN_WITNESSES
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

    def test_below_the_throw_bar_is_HELD_and_at_it_is_SUGGESTED(self):
        """v2073 — named for the LAW, not a number. It used to be
        `test_two_recordings_are_held_three_are_suggested`, which stopped being true the moment his
        3-read ruling pushed THROWOUT_MIN_WITNESSES to 4. Both halves are still checked: one short
        of the bar must be HELD with a recording-shaped reason, and exactly at the bar it must be
        SUGGESTED — a bar nothing can ever clear is a threshold above the ceiling."""
        bar = vr.THROWOUT_MIN_WITNESSES
        short, _ = self.sweep([self.ITEM], sessions=bar - 1)
        self.assertEqual(len(short["throwOut"]), 0,
                         "%d recordings suggested binning an item, one short of the bar" % (bar - 1))
        self.assertEqual(len(short["held"]), 1)
        self.assertIn("recording", short["held"][0]["why"])
        at, _ = self.sweep([self.ITEM], sessions=bar)
        self.assertEqual(len(at["throwOut"]), 1,
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


class TestOneReelManyPanels(_Base):
    """He does not park on one panel. He opens the stash, clicks through Personal → Runes → Gems,
    then looks at his inventory — all inside ONE recording.

    Every earlier test in this file used a single surface for a whole sweep, so the case that
    actually happens had never been driven: several still-runs in one reel, each classified
    separately, each read against its own surface, all folding into one proposal."""

    RUNS = ((6, 10.0), (6, 60.0), (6, 110.0))          # three panels, six frames each
    SURF = {10.0: "stash", 60.0: "runes", 110.0: "inventory"}
    ITEMS = {"stash": [{"name": "Shako", "conf": 0.9}],
             "runes": [{"name": "Ral Rune", "kind": "rune", "count": 3, "conf": 0.9}],
             "inventory": [{"name": "Tome of Town Portal", "conf": 0.9}]}

    def _mixed(self, items=None, sessions=None):
        # v2073 — DEFAULT TRACKS THE LAW, NOT A NUMBER. These helpers hardcoded sessions=2, so
        # when his ruling moved KEEP_MIN_WITNESSES to 3 every "this grounds" case in this file was
        # silently testing a bar that no longer exists — 19 of them went red at once on CI while
        # the local run I was doing (test_control only) stayed green.
        if sessions is None:
            sessions = vr.KEEP_MIN_WITNESSES
        import shutil
        items = items or self.ITEMS
        root = tempfile.mkdtemp(prefix="vault-mixed-")
        self.addCleanup(shutil.rmtree, root, True)
        sigmap, dirs = {}, []
        for sn in range(sessions):
            sid = "s_17870000%02d_sim" % sn
            d = os.path.join(root, "reel_" + sid)
            os.makedirs(d, exist_ok=True)
            idx, i = {"sessionId": sid, "frames": []}, 0
            for n, sv in self.RUNS:
                for _ in range(n):
                    f = "f_%03d.jpg" % i
                    with open(os.path.join(d, f), "wb") as fh:
                        fh.write(b"x")
                    idx["frames"].append({"f": f, "ts": 1787000000000 + i * 1000})
                    sigmap[os.path.join(d, f)] = sv
                    i += 1
            with open(os.path.join(d, "index.json"), "w", encoding="utf-8") as fh:
                json.dump(idx, fh)
            dirs.append(d)
        return vr.sweep(dirs,
                        sig=lambda p: [sigmap[p]] * 8,
                        classify=lambda p: self.SURF[sigmap[p]],
                        reader=lambda p, surf: {"items": items[surf], "conf": 0.9, "note": None})

    def test_each_panel_is_classified_and_read_on_its_own(self):
        res = self._mixed()
        self.assertTrue(res["ok"], res.get("why"))
        # 3 panels per recording; the session count now tracks KEEP_MIN_WITNESSES rather than a
        # hardcoded 2, so the expectation has to be derived or it pins yesterday's bar.
        self.assertEqual(res["totals"]["classified"], 3 * vr.KEEP_MIN_WITNESSES,
                         "panels were not classified one by one")
        # all 3 panels per recording are ownership surfaces here, so pagesRead == classified
        self.assertEqual(res["totals"]["pagesRead"], 3 * vr.KEEP_MIN_WITNESSES)

    def test_every_item_lands_in_the_lane_of_the_panel_it_was_seen_on(self):
        res = self._mixed()
        got = {r["name"]: (r["lane"], r.get("kind"), r.get("count")) for r in res["owned"]}
        self.assertEqual(got.get("Shako"), ("stash", "item", None))
        self.assertEqual(got.get("Ral Rune"), ("stash", "rune", 3),
                         "the runes TAB is a stash tab; its items are stash items")
        self.assertEqual(got.get("Tome of Town Portal"), ("inventory", "item", None))
        self.assertEqual(len(res["unsure"]), 0)

    def test_the_same_item_on_two_panels_is_two_rows(self):
        """His Shako is in the stash AND one is in his inventory — that is two facts, not one."""
        items = dict(self.ITEMS)
        items["inventory"] = [{"name": "Shako", "conf": 0.9}]
        res = self._mixed(items)
        pairs = sorted((r["name"], r["lane"]) for r in res["owned"] if r["name"] == "Shako")
        self.assertEqual(pairs, [("Shako", "inventory"), ("Shako", "stash")],
                         "two panels collapsed into one row: %s" % pairs)

    def test_a_panel_that_is_NOT_an_ownership_surface_costs_nothing(self):
        """He walks through town between panels. Gameplay must not be read at all."""
        surf = dict(self.SURF)
        surf[60.0] = "gameplay"
        keep = self.SURF
        self.SURF = surf
        try:
            res = self._mixed()
        finally:
            self.SURF = keep
        # 2 of the 3 panels per recording are ownership surfaces once one is made gameplay
        self.assertEqual(res["totals"]["pagesRead"], 2 * vr.KEEP_MIN_WITNESSES,
                         "a non-ownership panel was paid for")
        self.assertEqual(sorted(r["name"] for r in res["owned"]),
                         ["Shako", "Tome of Town Portal"])


class TestAMisreadDoesNotBecomeAGhost(_Base):
    """v1885 — the vault lane had NO name fold, and the chronicle lane has had one for versions.

    Measured with the exact corrections his chronicle sweep made on 2026-08-20 — 53 in one reel —
    pushed at the vault instead:

        pushed   Atma's Scarab · Battlecage · Saracen's Chance
        owned    Atma's Scarab · Battlecage · Saracen's Chance      (verbatim)
        both spellings together -> SIX owned rows for THREE real items

    And merge-max never subtracts, so every one of those is PERMANENT. The two-witness keep bar does
    not save it either: a SYSTEMATIC misread is exactly the kind that repeats, as this repo's own
    law-3 note says — "reading 'Ral' as 'Ort' a second time is exactly as likely as the first time".

    ⚠ THE HALF THAT MATTERS MORE IS WHAT IT MUST NOT TOUCH. The chronicle fold may call an
    unfoldable name debris, because a Chronicle page holds nothing but grail items. A STASH holds
    runes, gems, materials, bases, charms and jewels. `canonical("Ral Rune")` is None and that is a
    real thing he owns."""

    # EXACT folds only — the apostrophe class, which is the common one and the one his own sweep
    # hit. "Battlecage" -> "Rattlecage" needs a NEAR match and is deliberately NOT folded here; see
    # test_a_near_match_is_refused_because_it_can_rename_one_item_into_another.
    PAIRS = (("Atma's Scarab", "Atma’s Scarab"),
             ("Saracen's Chance", "Saracen’s Chance"))

    def test_two_spellings_of_one_item_become_one_row(self):
        items = []
        for raw, _canon in self.PAIRS:
            items += [{"name": raw, "conf": 0.9}, {"name": _canon, "conf": 0.9}]
        res, _ = self.sweep(items)
        names = sorted(r["name"] for r in res["owned"])
        self.assertEqual(names, sorted(c for _r, c in self.PAIRS),
                         "the misread survived as its own row: %s" % names)

    def test_a_misread_alone_is_recorded_under_its_real_name(self):
        res, _ = self.sweep([{"name": raw, "conf": 0.9} for raw, _c in self.PAIRS])
        self.assertEqual(sorted(r["name"] for r in res["owned"]),
                         sorted(c for _r, c in self.PAIRS))

    def test_it_NEVER_renames_something_that_is_not_a_grail_item(self):
        """The safety half. A stash is mostly things the roster has never heard of."""
        raw = ["Ral Rune", "Perfect Ruby", "Cracked Sash", "Chipped Skull", "Tome of Town Portal",
               "Small Charm", "Jewel", "Key of Terror", "Wirt's Leg"]
        res, _ = self.sweep([{"name": n, "conf": 0.9} for n in raw])
        self.assertEqual(sorted(r["name"] for r in res["owned"]), sorted(raw),
                         "the fold rewrote a name it had no business touching")

    def test_a_near_match_is_refused_because_it_can_rename_one_item_into_another(self):
        """The defect my own fold shipped for one minute, before this test caught it.

        canonical() near-matched "Isenhart's Armory (set)" — a SET AGGREGATE — onto "Isenhart's
        Parry (shield)", a specific piece. Not a correction: a find he never made. The chronicle
        lane can afford near matches because a Chronicle page is a CLOSED list of grail names; a
        stash is an open universe of runes, gems, bases, charms and aggregates."""
        for n in ("Isenhart's Armory (set)", "Battlecage"):
            res, _ = self.sweep([{"name": n, "conf": 0.9}])
            self.assertEqual([r["name"] for r in res["owned"]], [n],
                             "%r was near-matched onto a different item" % n)

    def test_the_fold_can_be_switched_off_and_then_the_ghost_returns(self):
        """Seen RED for its own reason: with the fold off, both spellings survive as two rows —
        which is precisely the state the vault was in before v1885."""
        both = [{"name": "Atma's Scarab", "conf": 0.9}, {"name": "Atma’s Scarab", "conf": 0.9}]
        off, _ = self.sweep_with_resolve(both, lambda n: n)
        self.assertEqual(len(off["owned"]), 2, "the fold is not actually doing the work")
        on, _ = self.sweep(both)
        self.assertEqual(len(on["owned"]), 1)

    def sweep_with_resolve(self, items, resolve, sessions=None, surface="stash"):
        # v2073 — DEFAULT TRACKS THE LAW, NOT A NUMBER. These helpers hardcoded sessions=2, so
        # when his ruling moved KEEP_MIN_WITNESSES to 3 every "this grounds" case in this file was
        # silently testing a bar that no longer exists — 19 of them went red at once on CI while
        # the local run I was doing (test_control only) stayed green.
        if sessions is None:
            sessions = vr.KEEP_MIN_WITNESSES
        import shutil
        root = tempfile.mkdtemp(prefix="vault-fold-")
        self.addCleanup(shutil.rmtree, root, True)
        dirs = [_reel(root, "s_17870000%02d_sim" % s) for s in range(sessions)]
        res = vr.sweep(dirs, sig=lambda p: list(_SIG), classify=lambda p: surface,
                       reader=lambda p, s: {"items": items, "conf": 0.9, "note": None},
                       resolve=resolve)
        return res, 0.0

    def test_a_fold_that_cannot_load_says_so_rather_than_failing_silent(self):
        import inspect
        src = inspect.getsource(vr._name_folder)
        self.assertIn("gating on RAW reader names", src,
                      "a missing resolver would now be silent, and a misread permanent")


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
        res, dt = self.sweep(big, sessions=vr.THROWOUT_MIN_WITNESSES)
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


class TestNoGrailNameIsEverAThrowOut(_Base):
    """v1903 — every guard on the throw lane was about HOW MUCH evidence a throw needs. None was
    about WHAT MAY BE THROWN, and "is this junk" was the vision reader's opinion alone.

    Worse, the reader was never ASKED. `throwOut` appeared exactly once in VAULT_READ_PROMPT —
    inside the JSON template, printed as `false` — with no definition, no criteria, and no mention
    of `throwWhy` at all, while vault_retro consumed both, gated them behind a higher confidence
    floor and three separate recordings, and rode them out to him as suggestions. An elaborate
    safety mechanism fed by a field nobody was ever asked to fill. [[the-unjoined-end]]

    Law 3 of vault_retro: there is no un-throw in Diablo. So this is settled in code, not left to
    the reader: a name on his grail roster is refused at ANY confidence, from ANY number of
    recordings."""

    def _flagged(self, name, sessions=4):
        items = [{"name": name, "kind": "item", "count": None,
                  "throwOut": True, "throwWhy": "white base, no sockets"}]
        return self.sweep(items, sessions=sessions)[0]

    def test_a_unique_flagged_by_a_certain_reader_is_refused(self):
        res = self._flagged("Harlequin Crest")
        names = [t["name"] for t in res["throwOut"]]
        self.assertNotIn("Harlequin Crest", names,
                         "the sweep suggested binning a grail unique")
        why = " ".join(h["why"] for h in res["held"] if h["name"] == "Harlequin Crest")
        self.assertIn("GRAIL ROSTER", why, "it was withheld, but not for the right reason: %r" % why)

    def test_a_set_piece_too(self):
        """⚠ ASSERT ON THE LANE BEING EMPTY, NOT ON THE SPELLING. The first version of this test
        checked `"Isenhart's Parry" not in names` and passed with the backstop switched OFF — the
        fold rewrites the straight apostrophe to his roster's curly one, so the name it was looking
        for was never going to be in that list either way. A test whose subject is renamed before
        it looks is a green light measuring nothing. [[feedback-blind-fixture-green-gate]]"""
        res = self._flagged("Isenhart's Parry")
        self.assertEqual(res["throwOut"], [],
                         "a set piece reached the throw lane: %r" % (res["throwOut"],))
        self.assertTrue(any("GRAIL ROSTER" in h["why"] for h in res["held"]),
                        "nothing was withheld for being on his roster: %r" % (res["held"],))

    def test_a_genuine_white_base_still_reaches_him(self):
        """The backstop must not swallow the lane it protects. A base name is not on the roster."""
        res = self._flagged("Cracked Sash")
        self.assertIn("Cracked Sash", [t["name"] for t in res["throwOut"]],
                      "the backstop refused an item that is not a grail name — it now blocks "
                      "everything, which is the same defect wearing the opposite coat")

    def test_the_reader_is_actually_asked_for_what_the_sweep_consumes(self):
        """THE CLASS, not the instance: every field normalize_item() reads off a reader's row has
        to appear in the prompt the reader is given. `throwOut` and `throwWhy` did not."""
        import tv_diablo as td
        prompt = td.VAULT_READ_PROMPT
        for field in ("name", "kind", "count", "conf", "throwOut", "throwWhy"):
            self.assertIn(field, prompt,
                          "vault_retro consumes %r and the prompt never mentions it — a field "
                          "nobody is asked to fill" % field)


if __name__ == "__main__":
    unittest.main(verbosity=2)
