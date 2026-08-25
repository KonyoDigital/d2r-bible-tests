"""v2001 — the retention planner's five bars, and the proof it can actually select and delete.

A deleter nobody has watched select anything is worse than none: on his real tree it correctly
reports ZERO candidates today, so without these the "safe" answer and a broken one are the same
output. Every case here runs against a TEMP fixture — never his frames.
[[feedback-fixtures-never-touch-live-data]] [[feedback-blind-fixture-green-gate]]
"""
import json
import os
import shutil
import sys
import tempfile
# ⚠ v2122 (#32) — THE BASE EPOCH IS 14000000000xx ON PURPOSE, DO NOT MOVE IT BACK TO 10000000000xx.
# reel_retention holds any reel whose id appears as a LITERAL in a tv/test_*.py file (v2069: a real
# prune deleted three reels tv/test_control.py names, turning real checks into permanent skips).
# tv/test_control.py contains the literal `reel_s_1000000000000_1`, and this suite CONSTRUCTED that
# same id — so the fixture-protection rule claimed this suite's own fixture and eight cases here
# asserted deletions that could never happen. The rule was right; the id collided.
# [[gate-blind-to-unexercised-input]] [[feedback-blind-fixture-green-gate]]
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import console_safe  # noqa: F401,E402 — this file's own docstring carries 🔓, and a suite that
                     # crashes while REPORTING makes a clean tree exit non-zero
console_safe.enable()

import reel_retention as rr  # noqa: E402


class TestRetentionSelectsAndRefuses(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.hist = os.path.join(self.root, "hist")
        os.makedirs(self.hist)
        self.addCleanup(shutil.rmtree, self.root, True)
        # point the module's ledger lookup at the fixture, never at his tree
        self._real_here = rr.HERE
        rr.HERE = self.root
        self.addCleanup(setattr, rr, "HERE", self._real_here)
        # v2122 (#32) — AND GIVE IT A DURABLE WITNESS STORE, because his tree has one. The reel
        # deleter now holds every reel when `haveIndex` is False, matching frame_authority, which
        # has always refused to delete a single FRAME in that state. A fixture with no durable
        # store was asking this module to release footage the frame deleter would not touch —
        # i.e. asserting the very disagreement #32 exists to close.
        with open(os.path.join(self.root, "vault_accum.json"), "w") as fh:
            json.dump({}, fh)

    def _reel(self, ms, n=1, kb=8):
        name = "reel_s_%d_%d" % (ms, n)
        d = os.path.join(self.hist, name)
        os.makedirs(d)
        with open(os.path.join(d, "f_%d.jpg" % ms), "wb") as fh:
            fh.write(b"\0" * (kb * 1024))
        return name

    def _ledgers(self, chron=None, vault=None):
        with open(os.path.join(self.root, "chronicle_swept.json"), "w") as fh:
            json.dump(chron or {}, fh)
        if vault is not None:
            with open(os.path.join(self.root, "vault_swept.json"), "w") as fh:
                json.dump(vault, fh)

    def test_it_selects_only_a_reel_BOTH_lanes_have_sealed_with_evidence(self):
        good = self._reel(1_400_000_000_000)
        nopages = self._reel(1_400_000_000_001)
        novault = self._reel(1_400_000_000_002)
        never = self._reel(1_400_000_000_003)
        self._ledgers(
            chron={good: {"pages": 12}, nopages: {"pages": 0}, novault: {"pages": 9}},
            vault={good: {"ts": 1}, nopages: {"ts": 1}})
        p = rr.plan(self.hist, keep_recent=0)
        names = [c["reel"] for c in p["candidates"]]
        self.assertEqual(names, [good], "selected %s" % names)
        why = {k["reel"]: k["why"] for k in p["kept"]}
        self.assertIn("0 pages", why[nopages])
        self.assertIn("VAULT", why[novault])
        self.assertIn("never chronicle-swept", why[never])

    def test_a_zero_page_seal_is_never_a_candidate_however_old(self):
        """The bar that matters most: 1166 MB of his footage is sealed with 0 pages, and the engine
        reopens exactly those when the prompt improves."""
        old = self._reel(1_400_000_000_000)
        self._ledgers(chron={old: {"pages": 0}}, vault={old: {"ts": 1}})
        self.assertEqual(rr.plan(self.hist, keep_recent=0)["candidates"], [])

    def test_the_newest_are_kept_whatever_the_ledgers_say(self):
        reels = [self._reel(1_400_000_000_000 + i) for i in range(6)]
        self._ledgers(chron={r: {"pages": 5} for r in reels},
                      vault={r: {"ts": 1} for r in reels})
        p = rr.plan(self.hist, keep_recent=5)
        self.assertEqual([c["reel"] for c in p["candidates"]], [reels[0]],
                         "keep_recent must protect the newest five")

    def test_it_stops_as_soon_as_the_target_is_met(self):
        reels = [self._reel(1_400_000_000_000 + i, kb=1024) for i in range(4)]
        self._ledgers(chron={r: {"pages": 5} for r in reels},
                      vault={r: {"ts": 1} for r in reels})
        p = rr.plan(self.hist, free_mb=1.5, keep_recent=0)
        self.assertLess(len(p["candidates"]), 4, "it emptied the shelf instead of meeting the target")
        self.assertGreaterEqual(p["freeMb"], 1.0)
        self.assertTrue(any("target was already met" in k["why"] for k in p["kept"]))

    def test_oldest_first(self):
        newer = self._reel(1_400_000_000_009)
        older = self._reel(1_400_000_000_000)
        self._ledgers(chron={newer: {"pages": 5}, older: {"pages": 5}},
                      vault={newer: {"ts": 1}, older: {"ts": 1}})
        p = rr.plan(self.hist, keep_recent=0)
        self.assertEqual([c["reel"] for c in p["candidates"]], [older, newer])

    def test_apply_REFUSES_without_yes_and_deletes_nothing(self):
        r1 = self._reel(1_400_000_000_000)
        self._ledgers(chron={r1: {"pages": 5}}, vault={r1: {"ts": 1}})
        p = rr.plan(self.hist, keep_recent=0)
        self.assertEqual(len(p["candidates"]), 1)
        out = rr.apply_plan(p, yes=False)
        self.assertFalse(out["ok"])
        self.assertTrue(os.path.isdir(os.path.join(self.hist, r1)),
                        "it deleted footage without an explicit yes")

    def test_apply_with_yes_actually_removes_it_and_leaves_the_rest(self):
        gone = self._reel(1_400_000_000_000)
        stay = self._reel(1_400_000_000_001)
        self._ledgers(chron={gone: {"pages": 5}, stay: {"pages": 0}},
                      vault={gone: {"ts": 1}, stay: {"ts": 1}})
        p = rr.plan(self.hist, keep_recent=0)
        out = rr.apply_plan(p, yes=True)
        self.assertTrue(out["ok"], out)
        self.assertEqual(out["removed"], [gone])
        self.assertFalse(os.path.isdir(os.path.join(self.hist, gone)))
        self.assertTrue(os.path.isdir(os.path.join(self.hist, stay)),
                        "it took a reel that had given up nothing")

    def test_an_unparseable_reel_name_sorts_NEWEST_so_nobody_deletes_it_first(self):
        odd = "reel_weird_name"
        os.makedirs(os.path.join(self.hist, odd))
        self.assertEqual(rr._reel_ts(odd), float("inf"))

    def test_a_missing_hist_dir_refuses_rather_than_reporting_an_empty_plan(self):
        p = rr.plan(os.path.join(self.root, "nope"))
        self.assertFalse(p["ok"])
        self.assertEqual(p["candidates"], [])


class TestV2042AHoldThatCanNeverBeSatisfiedIsALeak(unittest.TestCase):
    """The vault hold must ask whether the VAULT LANE WILL EVER COME.

    `vault_retro.OWNERSHIP_SURFACES` deliberately excludes 'chronicle', so a reel that DECLARED a
    chronicle focus is never the vault lane's to read. Holding it until the vault sweeps it holds it
    forever. Measured on his tree 2026-08-24: five reels declaring chronicle-uniques /
    chronicle-sets — 185 MB — kept on exactly that reason while the disk sat at 96%, waiting for a
    lane that was never going to come.

    Every case runs against a TEMP fixture, never his frames.
    [[feedback-fixtures-never-touch-live-data]]
    """

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.hist = os.path.join(self.root, "hist")
        os.makedirs(self.hist)
        self.addCleanup(shutil.rmtree, self.root, True)
        self._real_here = rr.HERE
        rr.HERE = self.root
        self.addCleanup(setattr, rr, "HERE", self._real_here)
        # v2122 (#32) — a durable witness store, because his tree has one. Without it the reel
        # deleter now holds everything (matching frame_authority, which has always refused to
        # delete a single FRAME in that state), and these cases are about the LANE holds, not
        # about that one.
        with open(os.path.join(self.root, "vault_accum.json"), "w") as fh:
            json.dump({}, fh)

    def _reel(self, ms, focus="__none__", kb=8):
        name = "reel_s_%d_1" % ms
        d = os.path.join(self.hist, name)
        # exist_ok: _plan_one is called once per focus in a subTest loop with the SAME id, so the
        # second focus raised FileExistsError before it could assert anything.
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "f_%d.jpg" % ms), "wb") as fh:
            fh.write(b"\0" * (kb * 1024))
        if focus != "__no_index__":
            ix = {} if focus == "__none__" else {"focus": focus}
            with open(os.path.join(d, "index.json"), "w") as fh:
                json.dump(ix, fh)
        return name

    def _sweep(self, reels):
        with open(os.path.join(self.root, "chronicle_swept.json"), "w") as fh:
            json.dump({r: {"pages": 12} for r in reels}, fh)
        with open(os.path.join(self.root, "vault_swept.json"), "w") as fh:
            json.dump({}, fh)          # the vault lane has swept NOTHING

    def _why(self, plan, reel):
        for row in (plan.get("candidates") or []) + (plan.get("kept") or []):
            if row.get("reel") == reel or row.get("name") == reel:
                return row.get("why") or ""
        return None

    def _plan_one(self, focus):
        r = self._reel(1_400_000_000_000, focus=focus)
        self._sweep([r])
        p = rr.plan(self.hist, keep_recent=0)
        cands = {row.get("reel") or row.get("name") for row in (p.get("candidates") or [])}
        return r, p, (r in cands)

    def test_a_chronicle_reel_is_not_held_for_a_lane_that_will_never_read_it(self):
        for focus in ("chronicle-uniques", "chronicle-sets"):
            with self.subTest(focus=focus):
                r, p, eligible = self._plan_one(focus)
                self.assertTrue(eligible,
                                "a %s reel is still held for the VAULT lane, which by "
                                "OWNERSHIP_SURFACES will never read it - that reel can never be "
                                "freed. why=%r" % (focus, self._why(p, r)))
                self.setUp()

    def test_a_stash_reel_IS_still_held_until_the_vault_reads_it(self):
        r, p, eligible = self._plan_one("stash")
        self.assertFalse(eligible,
                         "a stash reel the vault lane has never read became deletable - its rows "
                         "would be lost before they were ever banked")
        self.assertIn("VAULT lane", self._why(p, r) or "")

    def test_a_reel_with_NO_declared_focus_is_still_held(self):
        """No focus means the vault lane classifies it, so it may still owe rows."""
        r, p, eligible = self._plan_one("__none__")
        self.assertFalse(eligible, "an unfocused reel became deletable before the vault saw it")

    def test_an_UNREADABLE_index_keeps_the_hold(self):
        """Deleting footage is irreversible. 'I could not tell' must never resolve to 'delete it'."""
        r, p, eligible = self._plan_one("__no_index__")
        self.assertFalse(eligible,
                         "a reel whose index could not be read was selected for deletion - the "
                         "planner guessed in the one direction that cannot be undone")



class TestV2056ReadIsNotBanked(unittest.TestCase):
    """Konyo: "after the sweep ... data needs to be extracted and ledgered and counted for items as
    witnesses so when they get pruned they continue to exist on record."

    MIN_PAGES called it "evidence banked" and meant "at least one page was READ". A sweep produces a
    PROPOSAL; only an apply puts rows in a store that outlives the frames. The night before this
    guard was written, a blocked apply left 7 grounded and 17 unsure sitting in a proposal for hours
    while retention was free to run — and reel s_1787242455315_9654 had rows=7 in vault_swept with
    nothing durable behind it.

    ⚠ ON HIS REAL TREE THIS BRANCH IS CURRENTLY UNEXERCISED: that reel is held by the EARLIER
    chronicle-pages branch, so his data cannot tell a working guard from a broken one. The case is
    therefore built here. [[gate-blind-to-unexercised-input]]
    """

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.hist = os.path.join(self.root, "hist")
        os.makedirs(self.hist)
        self.addCleanup(shutil.rmtree, self.root, True)
        self._real = rr.HERE
        rr.HERE = self.root
        self.addCleanup(setattr, rr, "HERE", self._real)

    def _reel(self, sid, kb=8):
        d = os.path.join(self.hist, "reel_" + sid)
        os.makedirs(d)
        with open(os.path.join(d, "f_1.jpg"), "wb") as fh:
            fh.write(b"\0" * (kb * 1024))
        with open(os.path.join(d, "index.json"), "w") as fh:
            json.dump({"sessionId": sid, "focus": "stash"}, fh)
        return "reel_" + sid

    def _ledgers(self, sid, rows, durable):
        """Both lanes have READ it. `durable` decides whether the rows reached a store."""
        with open(os.path.join(self.root, "chronicle_swept.json"), "w") as fh:
            json.dump({"reel_" + sid: {"pages": 12}}, fh)
        with open(os.path.join(self.root, "vault_swept.json"), "w") as fh:
            json.dump({sid: {"ts": 1, "rows": rows}}, fh)
        acc = {"owned": []}
        if durable:
            acc["owned"] = [{"name": "Enigma", "lane": "stash",
                             "witnesses": [{"session": sid, "frame": "f_1.jpg"}]}]
        with open(os.path.join(self.root, "vault_accum.json"), "w") as fh:
            json.dump(acc, fh)

    def _eligible(self, name):
        p = rr.plan(self.hist, keep_recent=0)
        return name in {r.get("reel") or r.get("name") for r in (p.get("candidates") or [])}, p

    def _why(self, plan, name):
        for row in (plan.get("candidates") or []) + (plan.get("kept") or []):
            if (row.get("reel") or row.get("name")) == name:
                return row.get("why") or ""
        return ""

    def test_rows_read_but_NOT_banked_holds_the_reel(self):
        sid = "s_1400000000000_1"
        name = self._reel(sid)
        self._ledgers(sid, rows=7, durable=False)
        ok, plan = self._eligible(name)
        self.assertFalse(ok, "a reel whose 7 rows exist ONLY in these frames was offered for "
                             "deletion — that destroys the only record of those witnesses")
        self.assertIn("NONE of them are in the ledger", self._why(plan, name))

    def test_the_same_reel_becomes_eligible_ONCE_the_rows_are_banked(self):
        """The mirror. Without it, a guard that holds everything forever would also pass."""
        sid = "s_1400000000000_2"
        name = self._reel(sid)
        self._ledgers(sid, rows=7, durable=True)
        ok, plan = self._eligible(name)
        self.assertTrue(ok, "banked evidence still did not release the reel: %r"
                            % self._why(plan, name))

    def test_vault_seen_counts_as_durable_too(self):
        """v2051's ungrounded sightings outlive the frames just as owned rows do."""
        sid = "s_1400000000000_3"
        name = self._reel(sid)
        self._ledgers(sid, rows=4, durable=False)
        with open(os.path.join(self.root, "vault_seen.json"), "w") as fh:
            json.dump({"rows": [{"name": "Dwarf Star", "lane": "stash",
                                 "witnesses": [{"session": sid, "frame": "f_1.jpg"}]}]}, fh)
        ok, plan = self._eligible(name)
        self.assertTrue(ok, "a sighting durable in vault_seen.json did not release the reel: %r"
                            % self._why(plan, name))

    def test_an_unreadable_ledger_holds_rather_than_releases(self):
        """'I could not read the record' must never resolve to 'delete the record'."""
        sid = "s_1400000000000_4"
        name = self._reel(sid)
        self._ledgers(sid, rows=5, durable=False)
        with open(os.path.join(self.root, "vault_accum.json"), "w") as fh:
            fh.write("{ this is not json")
        ok, plan = self._eligible(name)
        self.assertFalse(ok, "an unreadable ledger released a reel holding un-banked evidence")

    def test_a_reel_that_produced_NO_rows_is_unaffected(self):
        """Nothing was found in it, so there is no record to lose."""
        sid = "s_1400000000000_5"
        name = self._reel(sid)
        self._ledgers(sid, rows=0, durable=False)
        ok, plan = self._eligible(name)
        self.assertTrue(ok, "a reel with no rows was held by the banked check: %r"
                            % self._why(plan, name))




class TestV2122TheTwoDeletersAgreeAboutTheSameFootage(unittest.TestCase):
    """frame_authority refuses to delete a single FRAME while `haveIndex` is False — nothing there
    can prove a frame is not the only record of what it saw. reel_retention deletes the WHOLE REEL
    those frames live in, and never asked: `haveIndex` appeared ZERO times in that module.

    MEASURED before the fix, on a tree with both swept ledgers and no durable witness store:

        haveIndex False   frames offered 0   reels offered 8

    Two authorities, opposite answers, same footage — and footage has no un-delete.
    [[feedback-contradiction-is-the-finding]] [[unknown-stays-unknown]]
    """

    def _tree(self, durable):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        hist = os.path.join(root, "hist")
        os.makedirs(hist)
        chron, vault = {}, {}
        for i in range(4):
            name = "reel_s_%d_1" % (1_400_000_000_100 + i)
            d = os.path.join(hist, name)
            os.makedirs(d)
            with open(os.path.join(d, "f_%d.jpg" % (1_400_000_000_100 + i)), "wb") as fh:
                fh.write(b"\0" * 200 * 1024)
            with open(os.path.join(d, "index.json"), "w") as fh:
                json.dump({"frames": [{"ts": 1_400_000_000_100 + i}]}, fh)
            chron[name] = {"pages": 9}      # swept with real pages
            vault[name] = {"rows": 0}       # the vault lane sealed it and owes nothing
        for fn, data in (("chronicle_swept.json", chron), ("vault_swept.json", vault)):
            with open(os.path.join(root, fn), "w") as fh:
                json.dump(data, fh)
        if durable:
            with open(os.path.join(root, "vault_accum.json"), "w") as fh:
                json.dump({}, fh)
        return root, hist

    def _plan(self, root, hist):
        real = rr.HERE
        rr.HERE = root
        try:
            return rr.plan(hist_dir=hist, free_mb=5000, keep_recent=0)
        finally:
            rr.HERE = real

    def _frame_plan(self, root, hist):
        """v2122 (#143) — ASK THE OTHER DELETER TOO, or this is not an agreement test.

        The first cut of this class asked reel_retention alone: it proved "the reel deleter holds",
        never "the two deleters agree". frame_authority could start OFFERING frames in this state
        and nothing here would notice — which is the same one-sidedness the original #32 report
        called out in the test it replaced."""
        import frame_authority as fa
        real = fa.HERE
        fa.HERE = root
        try:
            return fa.plan_frames(hist, root=root, keep=0)
        finally:
            fa.HERE = real

    def test_the_two_deleters_give_the_SAME_answer_with_no_index(self):
        """The actual invariant. Neither may release footage the other is protecting."""
        root, hist = self._tree(durable=False)
        frames = self._frame_plan(root, hist)
        reels = self._plan(root, hist)
        self.assertEqual(frames.get("prunable"), [],
                         "the FRAME deleter offered frames with no durable witness index — the "
                         "premise this whole agreement rests on has changed")
        self.assertEqual(reels.get("candidates"), [],
                         "the REEL deleter offered footage the frame deleter refuses to touch: "
                         "two authorities, opposite answers, and footage has no un-delete")

    def test_no_durable_index_holds_every_reel(self):
        root, hist = self._tree(durable=False)
        p = self._plan(root, hist)
        self.assertEqual(p.get("candidates"), [],
                         "the reel deleter offered footage the FRAME deleter refuses to touch — "
                         "two authorities, opposite answers, and footage has no un-delete")
        self.assertEqual((p.get("coverage") or {}).get("no-witness-index"), 4,
                         "the reels were held, but not for this reason — a right hold with the "
                         "wrong reason sends him to fix the wrong thing")

    def test_it_is_NOT_a_blanket_refusal_once_the_index_exists(self):
        """The mirror, and it is the half that matters: a rule that holds everything forever is
        the same defect wearing a helmet. With a durable store present the other rules decide.
        [[feedback-blind-fixture-green-gate]]"""
        root, hist = self._tree(durable=True)
        p = self._plan(root, hist)
        self.assertEqual((p.get("coverage") or {}).get("no-witness-index"), 0,
                         "the new hold fires even when a durable witness store EXISTS — it would "
                         "quietly become a permanent refusal to prune anything")
        self.assertTrue(p.get("candidates"),
                        "nothing is eligible even with both lanes sealed and a durable store — "
                        "this guard can no longer tell the hold from a dead planner")


if __name__ == "__main__":
    unittest.main(verbosity=2)
