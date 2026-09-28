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

    def test_a_missing_receipt_is_unknown_and_a_changed_store_is_named(self):
        st, why = CD._check_the_vault_reset()
        self.assertEqual(CD.UNKNOWN, st, why)
        self.assertIn("UNKNOWN", why)
        self.assertIn("not 0", why)
        self.assertNotIn("rebuilt 0", why)
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
        "find": "        return UNKNOWN, (\"no reset receipt has been handed to this console, so cleared, \"\n                         \"rebuilt and held are UNKNOWN, not 0\")\n",
        "replace": "        return OK, (\"rebuilt 0 · held 0\")\n",
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
