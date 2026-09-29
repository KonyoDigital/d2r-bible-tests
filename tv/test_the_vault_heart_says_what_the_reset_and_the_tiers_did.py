# -*- coding: utf-8 -*-
"""The heart says what a reset rebuilt, and how many items each tier holds.

His order 2026-09-27: the vault reset and the evidence tiers are vessels. An unreadable
ledger and a missing receipt are UNKNOWN, never 0. A kept store that changed is named.
A cited picture that is not on the shelf is named. The tier count and rebuild_plan must agree.
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

import console_doctor as CD
import vault_evidence as VE


def _looks(frame, n):
    return [{"session": "s%02d" % i, "frame": frame, "conf": 0.91, "lane": "stash"} for i in range(n)]


def _still(session, n, frame):
    """n frames of ONE held screen: one recording, one re-look id.

    ⚠ 2026-09-28 (Ledger P0) — _looks above gives EVERY look its own session, and that is why
    this law never saw the bug: frames and visits were the same number on every row it built.
    His real Radiance row is the other shape — 102 frames under one re-look id plus one from a
    second recording — and it scored HARDENED. This builds that shape.
    """
    return [{"session": session, "witness": session + "#0", "frame": frame, "conf": 0.91,
             "lane": "stash"} for _ in range(n)]


class TheVaultHeartSaysWhatTheResetAndTheTiersDid(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="vault-heart-")
        self.ledger = os.path.join(self.tmp, "witness.json")
        self.doc = {"owned": [
            {"name": "Shako", "lane": "stash", "kind": "item", "witnesses": _looks("cited.jpg", 12)},
            {"name": "War Traveler", "lane": "stash", "kind": "item", "witnesses": _looks("watch.jpg", 2)},
            {"name": "Arachnid Mesh", "lane": "stash", "kind": "item", "witnesses": _looks("hard.jpg", 21)},
            {"name": "Unread Thing", "lane": "stash", "witnesses": 4},
            {"name": "Radiance", "lane": "stash", "kind": "item",
             "witnesses": _still("sR1", 1, "still.jpg") + _still("sR2", 20, "still.jpg")},
        ]}
        self.before = json.dumps(self.doc).encode("utf-8")
        with io.open(self.ledger, "wb") as fh:
            fh.write(self.before)
        self.shelf = os.path.join(self.tmp, "shelf")
        os.makedirs(self.shelf)
        for name in ("cited.jpg", "watch.jpg", "hard.jpg", "still.jpg"):
            with io.open(os.path.join(self.shelf, name), "w", encoding="utf-8") as fh:
                fh.write(name)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_the_tiers_agree_with_the_plan_and_name_a_missing_picture(self):
        got = VE.tier_census(self.ledger)
        self.assertTrue(got["ok"], got)
        self.assertEqual(2, got["watched"], "War Traveler and the still screen are both WATCHED")
        self.assertEqual(1, got["proven"])
        self.assertEqual(1, got["hardened"], "a still screen of 21 frames was counted as hardened")
        self.assertEqual(1, got["unknown"])
        self.assertEqual([], got["disagree"])
        with io.open(self.ledger, "rb") as fh:
            self.assertEqual(self.before, fh.read(), "the census wrote the witness ledger")
        pics = VE.pictures_gone(self.ledger, self.shelf)
        self.assertEqual(0, pics["n"])
        os.remove(os.path.join(self.shelf, "cited.jpg"))
        gone = VE.pictures_gone(self.ledger, self.shelf)
        self.assertEqual(["cited.jpg"], gone["gone"])
        st, why = CD._check_the_evidence_tiers(path=self.ledger, root=self.shelf)
        self.assertEqual(CD.MISSING, st, why)
        self.assertIn("cited.jpg", why)
        self.assertIn(("evidence tiers", CD._check_the_evidence_tiers), CD.CHECKS)
        self.assertIn("evidence tiers", CD.WATCHES)

    def test_the_row_the_heart_runs_opens_the_real_shelf(self):
        """The registered call has no arguments. It must read the ledger AND the shelf this console uses, and name
        a cited picture that is gone - not say UNKNOWN because nobody handed it a root (second eye, v3520)."""
        os.remove(os.path.join(self.shelf, "cited.jpg"))
        env = {k: os.environ.get(k) for k in ("TV_VAULT_LEDGER", "TV_HIST")}
        os.environ["TV_VAULT_LEDGER"], os.environ["TV_HIST"] = self.ledger, self.shelf
        try:
            fn = dict(CD.CHECKS)["evidence tiers"]
            st, why = fn()
        finally:
            for k, v in env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        self.assertEqual(CD.MISSING, st, "the live row did not open the shelf: %r" % why)
        self.assertIn("cited.jpg", why)

    def test_the_row_counts_visits_and_names_the_retro_flags(self):
        got = VE.tier_census(self.ledger)
        self.assertEqual(1, got["retro"], "the still screen filed HARDENED by frames is not flagged")
        self.assertEqual(["Radiance"], got["retroNames"])
        st, why = CD._check_the_evidence_tiers(path=self.ledger, root=self.shelf)
        self.assertEqual(CD.OK, st, why)
        self.assertIn("tiers by visit, never frame: WATCHED 2 · PROVEN 1 · HARDENED 1", why)
        self.assertIn("retro flags 1 (Radiance)", why,
                      "the doctor row does not say which items are filed above their visits")
        with io.open(self.ledger, "rb") as fh:
            self.assertEqual(self.before, fh.read(), "the doctor row wrote the witness ledger")

    def test_a_flagged_row_no_visit_saw_is_named_held_not_kept(self):
        # 2026-09-28 (Ledger fix round 2, finding B): a retro-flagged row with ZERO qualifying looks
        # is held by the plan. The heart row must not fold it into "kept filed by his ruling".
        self.doc["owned"].append({"name": "Ghost Charm", "lane": "stash", "kind": "item",
                                  "witnesses": [{"frame": "ghost_%02d.jpg" % i, "conf": 0.92,
                                                 "lane": "stash"} for i in range(15)]})
        with io.open(self.ledger, "wb") as fh:
            fh.write(json.dumps(self.doc).encode("utf-8"))
        got = VE.tier_census(self.ledger)
        self.assertEqual(["Radiance", "Ghost Charm"], got["retroNames"], "baseline: both are flagged")
        self.assertEqual(["Ghost Charm"], got["retroHeldNames"])
        st, why = CD._check_the_evidence_tiers(path=self.ledger, root=None)
        self.assertEqual(CD.OK, st, why)
        self.assertIn("retro flags 2 (Radiance) — filed above what their visits earn, kept filed", why,
                      "a row no visit saw was claimed as kept filed: %s" % why)
        self.assertIn("1 of them held — no visit saw it (Ghost Charm)", why)

    def test_an_unreadable_ledger_is_unknown_not_zero(self):
        missing = os.path.join(self.tmp, "nope.json")
        got = VE.tier_census(missing)
        self.assertFalse(got["ok"])
        self.assertIsNone(got["watched"])
        self.assertIsNone(got["proven"])
        self.assertIsNone(got["hardened"])
        self.assertIsNone(got["unknown"])
        st, why = CD._check_the_evidence_tiers(path=missing, root=self.shelf)
        self.assertEqual(CD.UNKNOWN, st, why)
        self.assertNotIn("WATCHED 0", why)
        shelf = VE.pictures_gone(self.ledger, os.path.join(self.tmp, "no-shelf"))
        self.assertIsNone(shelf["n"])
        self.assertIsNone(shelf["gone"])
        closed = VE.pictures_gone(self.ledger, None)
        self.assertIsNone(closed["n"])
        self.assertIn("UNKNOWN", closed["why"])
        self.assertIn("not 0", closed["why"])

    def test_a_read_empty_ledger_may_say_zero(self):
        empty = os.path.join(self.tmp, "empty.json")
        with io.open(empty, "w", encoding="utf-8") as fh:
            json.dump({"owned": []}, fh)
        got = VE.tier_census(empty)
        self.assertTrue(got["ok"], got)
        self.assertEqual(0, got["watched"])
        self.assertEqual(0, got["proven"])
        self.assertEqual(0, got["hardened"])

    def _board(self, stores):
        """The no-argument row reads the board through the shared read — stubbed here, never his console."""
        real = CD._board_read
        CD._board_read = (lambda: None) if stores is None else (lambda: {"ok": True, "fullStores": stores})
        try:
            return CD._check_the_vault_reset()
        finally:
            CD._board_read = real

    def test_a_missing_receipt_is_unknown_and_a_changed_store_is_named(self):
        st, why = self._board(None)
        self.assertEqual(CD.UNKNOWN, st, why)
        self.assertIn("UNKNOWN", why)
        self.assertIn("not 0", why)
        self.assertNotIn("rebuilt 0", why)
        # #41 rank 2 — a board that holds no receipt is UNKNOWN too, never "rebuilt 0"
        st0, why0 = self._board({"d2r_owned": "[]"})
        self.assertEqual(CD.UNKNOWN, st0, why0)
        self.assertIn("no reset receipt", why0)
        self.assertNotIn("rebuilt 0", why0)
        same = {"d2r_setPieces": b"[1]", "d2r_foundLog": b"{}"}
        clean = VE.reset_receipt({"rebuilt": ["Shako"], "held": ["War Traveler"], "touched": [],
                                  "rebuiltFailed": []},
                                 same, dict(same))
        self.assertTrue(clean["ok"], clean)
        self.assertEqual(1, clean["rebuilt"])
        self.assertEqual(1, clean["held"])
        self.assertEqual(0, clean["refused"])
        dirty_after = dict(same)
        dirty_after["d2r_setPieces"] = b"[]"
        dirty = VE.reset_receipt({"rebuilt": ["Shako"], "held": [], "touched": []}, same, dirty_after)
        self.assertFalse(dirty["ok"], dirty)
        self.assertEqual(["d2r_setPieces"], dirty["touched"])
        st2, why2 = CD._check_the_vault_reset(
            {"rebuilt": ["Shako"], "held": []}, same, dirty_after)
        self.assertEqual(CD.MISSING, st2, why2)
        self.assertIn("d2r_setPieces", why2)
        none = VE.reset_receipt({"held": []}, same, dict(same))
        self.assertIsNone(none["rebuilt"])
        self.assertIn("UNKNOWN", none["why"])
        self.assertIn(("vault reset receipt", CD._check_the_vault_reset), CD.CHECKS)

    def test_a_refused_rebuild_is_named_on_the_heart(self):
        # 2026-09-28 (Ledger fix round 2, finding B): the board's reset wrote R.rebuiltFailed and
        # NOTHING read it, so a plan row the door refused fell silently between "rebuilt" and
        # "held". The doctor's reset row now reads it: each refusal named with the door's why, and
        # a receipt that does not say is UNKNOWN — never a clean OK.
        same = {"d2r_setPieces": b"[1]"}
        refused = {"rebuilt": ["Shako"], "held": [],
                   "rebuiltFailed": [{"name": "Arkaine's Valor", "refused": "witness",
                                      "why": "only 1 qualifying look in your stash — needs 2"}]}
        got = VE.reset_receipt(refused, same, dict(same))
        self.assertFalse(got["ok"], got)
        self.assertEqual(1, got["refused"])
        self.assertEqual("Arkaine's Valor", got["refusedRows"][0]["name"])
        st, why = CD._check_the_vault_reset(refused, same, dict(same))
        self.assertEqual(CD.MISSING, st, "a refused rebuild read %s: %s" % (st, why))
        self.assertIn("Arkaine's Valor", why)
        self.assertIn("only 1 qualifying look", why, "the door's own reason was dropped")
        self.assertIn("REFUSED", why)
        # an older receipt of bare names still names them
        old = VE.reset_receipt({"rebuilt": [], "held": [], "rebuiltFailed": ["Shako"]},
                               same, dict(same))
        self.assertEqual(("Shako", 1), (old["refusedRows"][0]["name"], old["refused"]))
        # a receipt that never says is UNKNOWN on the heart, never OK
        st2, why2 = CD._check_the_vault_reset({"rebuilt": ["Shako"], "held": []}, same, dict(same))
        self.assertEqual(CD.UNKNOWN, st2, why2)
        self.assertIn("UNKNOWN", why2)
        st3, why3 = CD._check_the_vault_reset({"rebuilt": ["Shako"], "held": [], "rebuiltFailed": []},
                                              same, dict(same))
        self.assertEqual(CD.OK, st3, why3)
        self.assertIn("refused 0", why3)

    def test_the_no_argument_row_reads_the_receipt_the_reset_persisted(self):
        """#41 rank 2: registered with no arguments, the row read nothing and was UNKNOWN for ever. It now reads the
        board's d2r_vaultLastReset (the shape bible.html's _vaultResetPersist writes: the receipt plus a digest of every
        kept store before the clears and after the rebuild) through the shared board read, and carries the reset's time."""
        rec = {"door": "vaultClearHistory", "at": "2026-09-29T07:00:00.000Z", "cleared": {"assign": 3}, "failed": [],
               "kept": {}, "touched": [], "unknown": [], "ok": True, "rebuilt": ["Shako"], "held": 1, "rebuiltFailed": [],
               "keepsBefore": {"d2r_setPieces": "3:abc", "d2r_foundLog": "2:def"},
               "keepsAfter": {"d2r_setPieces": "3:abc", "d2r_foundLog": "2:def"}}
        st, why = self._board({"d2r_vaultLastReset": json.dumps(rec)})
        self.assertEqual(CD.OK, st, why)
        self.assertIn("refused 0", why)
        self.assertIn("2026-09-29T07:00:00", why, "the row does not carry the reset's own time")
        # a kept store whose digest moved during the rebuild is named — MISSING, never intact
        dirty = dict(rec, keepsAfter={"d2r_setPieces": "0:0", "d2r_foundLog": "2:def"})
        st2, why2 = self._board({"d2r_vaultLastReset": json.dumps(dirty)})
        self.assertEqual(CD.MISSING, st2, why2)
        self.assertIn("d2r_setPieces", why2)
        # a refusal the door recorded is named off the persisted receipt
        refused = dict(rec, rebuiltFailed=[{"name": "Arkaine's Valor", "refused": "witness", "why": "only 1 qualifying look"}])
        st3, why3 = self._board({"d2r_vaultLastReset": json.dumps(refused)})
        self.assertEqual(CD.MISSING, st3, why3)
        self.assertIn("Arkaine's Valor", why3)
        # a receipt that will not parse is UNKNOWN, not 0
        st4, why4 = self._board({"d2r_vaultLastReset": "{not json"})
        self.assertEqual(CD.UNKNOWN, st4, why4)
        self.assertIn("not 0", why4)
        # Reset assignments never rebuilds: its receipt is judged on the kept stores alone, never "rebuilt UNKNOWN" for ever
        assign_door = {"door": "vaultReset", "at": "2026-09-29T07:30:00.000Z", "keepsBefore": {"d2r_setPieces": "3:abc"},
                       "keepsAfter": {"d2r_setPieces": "3:abc"}}
        st5, why5 = self._board({"d2r_vaultLastReset": json.dumps(assign_door)})
        self.assertEqual(CD.OK, st5, why5)
        self.assertIn("never rebuilds", why5)

    def _stones(self, rows):
        with io.open(os.path.join(self.shelf, "reel_tombstones.json"), "w", encoding="utf-8") as fh:
            json.dump({"reels": rows}, fh)

    def test_a_loss_before_the_keep_is_baseline_and_a_loss_after_it_is_missing_and_named(self):
        """#41 rank 4: the row was permanently MISSING on picture losses nothing can repair (21 of 29 cited frames went with
        reels drained before the keep landed), and the whole Ledger 3.0 report hid inside that red. Now every gone frame is
        dated by its reel's tombstone against vault_evidence.KEEP_LANDED_MS: before = baseline beside an OK, after = MISSING
        naming the item; the tiers and the retro flags are always printed."""
        before, after = VE.KEEP_LANDED_MS - 3600000, VE.KEEP_LANDED_MS + 3600000
        self._stones([{"reel": "reel_s00", "deletedTs": before}, {"reel": "reel_sR1", "deletedTs": after}])
        os.remove(os.path.join(self.shelf, "cited.jpg"))
        os.remove(os.path.join(self.shelf, "watch.jpg"))
        st, why = CD._check_the_evidence_tiers(path=self.ledger, root=self.shelf)
        self.assertEqual(CD.OK, st, "two pictures lost BEFORE the keep landed kept the row red: %s" % why)
        self.assertIn("pictures gone 2 of cited 4", why)
        self.assertIn("2 before the keep landed", why)
        self.assertIn("retro flags 1 (Radiance)", why, "the retro flags no longer reach the eagle beside a baseline loss")
        self.assertIn("WATCHED 2 · PROVEN 1 · HARDENED 1", why)
        losses = VE.picture_losses(self.ledger, self.shelf)
        self.assertEqual(["cited.jpg", "watch.jpg"], sorted(r["frame"] for r in losses["baseline"]))
        self.assertEqual([], losses["after"])
        os.remove(os.path.join(self.shelf, "still.jpg"))
        st2, why2 = CD._check_the_evidence_tiers(path=self.ledger, root=self.shelf)
        self.assertEqual(CD.MISSING, st2, "a picture lost AFTER the keep landed did not go red: %s" % why2)
        self.assertIn("lost AFTER the keep landed", why2)
        self.assertIn("Radiance (still.jpg", why2, "the loss does not name the item it stands on")
        self.assertIn("retro flags 1 (Radiance)", why2, "the red hid the rest of the report again")
        self.assertIn("pictures gone 3 of cited 4", why2)

    def test_a_loss_no_tombstone_dates_is_unknown_when_and_red(self):
        os.remove(os.path.join(self.shelf, "hard.jpg"))
        st, why = CD._check_the_evidence_tiers(path=self.ledger, root=self.shelf)
        self.assertEqual(CD.MISSING, st, why)
        self.assertIn("no tombstone dates the loss", why)
        self.assertIn("Arachnid Mesh (hard.jpg)", why)
        self.assertIn("WATCHED 2 · PROVEN 1 · HARDENED 1", why)

    def _his_layout(self):
        """His tree's shape: the module's dir holds reel_tombstones.json, the shelf is <dir>/frames/hist — and the resolver
        (reel_retention._tombstone_path) is asked with rr.HERE repointed at that dir, TV_HIST unset."""
        import reel_retention as rr
        tv = os.path.join(self.tmp, "tv")
        shelf = os.path.join(tv, "frames", "hist")
        os.makedirs(shelf)
        for name in ("cited.jpg", "watch.jpg", "hard.jpg", "still.jpg"):
            with io.open(os.path.join(shelf, name), "w", encoding="utf-8") as fh:
                fh.write(name)
        return rr, tv, shelf

    def test_his_layout_the_tombstones_beside_the_module_date_the_shelf_under_frames_hist(self):
        """Round-5 review (HIGH, reproduced on his tree): the resolver names tv/reel_tombstones.json beside a shelf at
        tv/frames/hist, and the first guard dropped it (it demanded the file under the shelf's parent) — so all 21 of his
        gone frames read 'undated' and the row was MISSING for ever wearing "no tombstone dates the loss". The resolver's
        answer is trusted; a record in his layout dates the losses."""
        rr, tv, shelf = self._his_layout()
        before = VE.KEEP_LANDED_MS - 3600000
        with io.open(os.path.join(tv, "reel_tombstones.json"), "w", encoding="utf-8") as fh:
            json.dump({"reels": [{"reel": "reel_s00", "deletedTs": before}]}, fh)
        os.remove(os.path.join(shelf, "cited.jpg"))
        here, hist = rr.HERE, os.environ.pop("TV_HIST", None)
        rr.HERE = tv
        try:
            named = rr._tombstone_path(shelf)
            self.assertEqual(os.path.join(tv, "reel_tombstones.json"), named, "PREMISE: the resolver names the module-side record")
            self.assertEqual({"s00": before}, VE._tombstone_times(shelf), "the resolver's own answer was dropped by the guard (round-5 HIGH)")
            losses = VE.picture_losses(self.ledger, shelf)
            self.assertEqual(["cited.jpg"], [r["frame"] for r in losses["baseline"]], losses)
            self.assertEqual([], losses["undated"])
            st, why = CD._check_the_evidence_tiers(path=self.ledger, root=shelf)
            self.assertEqual(CD.OK, st, "a dated baseline loss in his layout kept the row red: %s" % why)
            self.assertIn("1 before the keep landed", why)
            self.assertNotIn("no tombstone dates the loss", why)
        finally:
            rr.HERE = here
            if hist is not None:
                os.environ["TV_HIST"] = hist

    def test_a_fixture_shelf_is_never_dated_by_a_record_outside_its_tree(self):
        """The one refusal that stays: a shelf OUTSIDE HERE's tree (a fixture) is never dated by a record INSIDE it (his
        tombstones) — the resolver's ImportError answer. A loss on such a shelf is UNKNOWN-when, never a baseline."""
        rr, tv, _shelf = self._his_layout()
        with io.open(os.path.join(tv, "reel_tombstones.json"), "w", encoding="utf-8") as fh:
            json.dump({"reels": [{"reel": "reel_s02", "deletedTs": VE.KEEP_LANDED_MS - 3600000}]}, fh)
        os.remove(os.path.join(self.shelf, "hard.jpg"))     # self.shelf is outside `tv`, and holds no record of its own
        here, path_fn = rr.HERE, rr._tombstone_path
        rr.HERE = tv
        rr._tombstone_path = lambda hist=None: os.path.join(rr.HERE, "reel_tombstones.json")   # the ImportError answer: HERE
        try:
            self.assertIsNone(VE._tombstone_times(self.shelf), "a fixture shelf was dated by a record outside its tree")
            losses = VE.picture_losses(self.ledger, self.shelf)
            self.assertEqual(["hard.jpg"], [r["frame"] for r in losses["undated"]], losses)
            self.assertEqual([], losses["baseline"])
        finally:
            rr.HERE, rr._tombstone_path = here, path_fn

    def test_a_loss_after_the_keep_says_the_commit_time_is_a_lower_bound(self):
        """Round-5 review (LOW): the keep reached this machine when he pulled it, later than its commit — the row's words say
        the constant is a lower bound rather than pretending it exact."""
        self._stones([{"reel": "reel_sR1", "deletedTs": VE.KEEP_LANDED_MS + 3600000}])
        os.remove(os.path.join(self.shelf, "still.jpg"))
        st, why = CD._check_the_evidence_tiers(path=self.ledger, root=self.shelf)
        self.assertEqual(CD.MISSING, st, why)
        self.assertIn("lost AFTER the keep landed", why)
        self.assertIn("a lower bound", why, "the row pretends the keep's commit time is when it reached this machine: %s" % why)
        self.assertIn(VE.KEEP_LANDED_WHY, why)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "2026-09-28 - the heart's evidence row never opens the shelf again, so a lost picture reads UNKNOWN for ever",
        "file": "console_doctor.py",
        "find": "    if path is None and root is None:\n        # 2026-09-28 second eye (v3520, 7fcb836c)",
        "replace": "    if False:\n        # 2026-09-28 second eye (v3520, 7fcb836c)",
        "matches": 1,
    },
    {
        "why": "the census stops asking the tier table, so a watched item is called proven",
        "file": "vault_evidence.py",
        "find": "            got_tier = tier(successes, trials)[\"tier\"]\n",
        "replace": "            got_tier = PROVEN\n",
        "matches": 1,
    },
    {
        "why": "a shelf that cannot be read is reported as no broken evidence links",
        "file": "vault_evidence.py",
        "find": "    if not os.path.isdir(root):\n        return {\"ok\": False, \"gone\": None, \"n\": None, \"cited\": None,\n",
        "replace": "    if not os.path.isdir(root):\n        return {\"ok\": False, \"gone\": None, \"n\": 0, \"cited\": None,\n",
        "matches": 1,
    },
    {
        "why": "a kept store the reset changed is treated as untouched",
        "file": "vault_evidence.py",
        "find": "        if before[key] != after[key]:\n",
        "replace": "        if False and before[key] != after[key]:\n",
        "matches": 1,
    },
    {
        "why": "no reset receipt is reported as rebuilt 0",
        "file": "console_doctor.py",
        "find": "        if isinstance(got0[0], str):\n            return UNKNOWN, got0[1]\n",
        "replace": "        if isinstance(got0[0], str):\n            return OK, \"rebuilt 0 · held 0\"\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 2 - the no-argument row stops reading the persisted receipt, so it is UNKNOWN for ever again",
        "file": "console_doctor.py",
        "find": "        got0 = _last_reset_receipt()\n",
        "replace": "        got0 = (\"none\", \"no reset receipt has been handed to this console, so cleared, rebuilt and held are UNKNOWN, not 0\")\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 4 - every gone picture is treated as lost after the keep, so a baseline loss keeps the row red for ever",
        "file": "vault_evidence.py",
        "find": "        elif ts < landed:\n            baseline.append(row)\n",
        "replace": "        elif False:\n            baseline.append(row)\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 4 - a picture lost AFTER the keep landed no longer turns the row red",
        "file": "console_doctor.py",
        "find": "    if bad_pics:\n        return MISSING, bad_pics + \" · \" + line\n",
        "replace": "    if False:\n        return MISSING, bad_pics + \" · \" + line\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 4 - a loss no tombstone dates is folded into the baseline instead of said UNKNOWN-when",
        "file": "vault_evidence.py",
        "find": "        if ts is None:\n            undated.append(row)\n",
        "replace": "        if ts is None:\n            baseline.append(row)\n",
        "matches": 1,
    },
    {
        "why": "round-5 HIGH - the guard demands the record under the shelf's parent again, so his tv/reel_tombstones.json is dropped and every loss is undated",
        "file": "vault_evidence.py",
        "find": "    if named and not (home and not _inside(root, home) and _inside(named, home)):\n        cands.append(named)\n",
        "replace": "    if named and _inside(named, os.path.dirname(os.path.realpath(root))):\n        cands.append(named)\n",
        "matches": 1,
    },
    {
        "why": "round-5 HIGH - the fixture refusal is dropped, so a fixture shelf is dated by his tombstones",
        "file": "vault_evidence.py",
        "find": "    if named and not (home and not _inside(root, home) and _inside(named, home)):\n        cands.append(named)\n",
        "replace": "    if named:\n        cands.append(named)\n",
        "matches": 1,
    },
    {
        "why": "round-5 LOW - the row pretends the keep's commit time is exact",
        "file": "console_doctor.py",
        "find": "            bad_pics = \"%d cited picture(s) lost AFTER the keep landed (%s): %s\" % (\n                len(after), _ve.KEEP_LANDED_WHY,\n",
        "replace": "            bad_pics = \"%d cited picture(s) lost AFTER the keep landed: %s\" % (\n                len(after),\n",
        "matches": 1,
    },
    {
        "why": "the evidence-tier row is dropped from the doctor, so the heart never asks",
        "file": "console_doctor.py",
        "find": "    (\"evidence tiers\", _check_the_evidence_tiers),\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "the census counts frames again, so one still screen reads HARDENED on the heart",
        "file": "vault_evidence.py",
        "find": "            successes, trials = measured[0], measured[1]\n",
        "replace": "            successes, trials = measured[5][\"successes\"], measured[5][\"trials\"]\n",
        "matches": 1,
    },
    {
        "why": "the receipt's rebuiltFailed is read by nothing again, so a refused rebuild is a silent gap (finding B)",
        "file": "vault_evidence.py",
        "find": "    refused_n, refused_rows = _refusals(receipt)\n",
        "replace": "    refused_n, refused_rows = 0, []\n",
        "matches": 1,
    },
    {
        "why": "the doctor reads a refused rebuild as a clean reset (finding B)",
        "file": "console_doctor.py",
        "find": "    if got.get(\"refused\"):\n        return MISSING, got.get(\"why\") or \"the door refused a plan row\"\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "the heart row folds a flagged row no visit saw into 'kept filed' again (finding B)",
        "file": "console_doctor.py",
        "find": "        _kept = [n for n in (got.get(\"retroNames\") or []) if n not in _rheld]\n",
        "replace": "        _kept = list(got.get(\"retroNames\") or [])\n",
        "matches": 1,
    },
    {
        "why": "the census stops naming the retro rows the plan holds (finding B)",
        "file": "vault_evidence.py",
        "find": "                if _flag.get(\"keepFiled\") is not True:\n",
        "replace": "                if False:\n",
        "matches": 1,
    },
    {
        "why": "the doctor row stops naming the retro flags, so the heart says nothing about them",
        "file": "console_doctor.py",
        "find": "    elif got[\"retro\"]:\n",
        "replace": "    elif False:\n",
        "matches": 1,
    },
]
