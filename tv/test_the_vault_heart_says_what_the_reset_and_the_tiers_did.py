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


class TheVaultHeartSaysWhatTheResetAndTheTiersDid(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="vault-heart-")
        self.ledger = os.path.join(self.tmp, "witness.json")
        self.doc = {"owned": [
            {"name": "Shako", "lane": "stash", "kind": "item", "witnesses": _looks("cited.jpg", 12)},
            {"name": "War Traveler", "lane": "stash", "kind": "item", "witnesses": _looks("watch.jpg", 2)},
            {"name": "Arachnid Mesh", "lane": "stash", "kind": "item", "witnesses": _looks("hard.jpg", 21)},
            {"name": "Unread Thing", "lane": "stash", "witnesses": 4},
        ]}
        self.before = json.dumps(self.doc).encode("utf-8")
        with io.open(self.ledger, "wb") as fh:
            fh.write(self.before)
        self.shelf = os.path.join(self.tmp, "shelf")
        os.makedirs(self.shelf)
        for name in ("cited.jpg", "watch.jpg", "hard.jpg"):
            with io.open(os.path.join(self.shelf, name), "w", encoding="utf-8") as fh:
                fh.write(name)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_the_tiers_agree_with_the_plan_and_name_a_missing_picture(self):
        got = VE.tier_census(self.ledger)
        self.assertTrue(got["ok"], got)
        self.assertEqual(1, got["watched"])
        self.assertEqual(1, got["proven"])
        self.assertEqual(1, got["hardened"])
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
        clean = VE.reset_receipt({"rebuilt": ["Shako"], "held": ["War Traveler"], "touched": []},
                                 same, dict(same))
        self.assertTrue(clean["ok"], clean)
        self.assertEqual(1, clean["rebuilt"])
        self.assertEqual(1, clean["held"])
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
]
