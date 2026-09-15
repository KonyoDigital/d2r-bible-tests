#!/usr/bin/env python3
"""THE GUEST SEAT IS GROK, NOT KONYO — and the mirror carries none of his machine.

HIS BRIEF, 2026-09-15 (GB-CLAUDE-GROK-PROFILE-SYNC): a real Grok actor for the guest seat on the
box, *"rewrite so Konyo is never the live actor"*, and *"No install ids, hostnames, tokens, or
home paths in replies"* — because this repo is PUBLIC and the guest's evidence screenshots get
posted to a public issue.

⚠ WHY THIS IS A PRIVACY GATE AND NOT A COSMETIC ONE. The guest renders a mirror of his live
console. His `/api/status` carries an install id, a `.local` hostname, a unix user and absolute
home paths; the board HTML carries them too. MEASURED on the very first sync run: the raw board
came back with FOUR of his identifiers still in it, and the leak gate refused the copy. Without
that refusal they would have gone to the box, into the fixture packs built from it, and into any
screenshot posted to #180.

⚠ AND FAIL CLOSED. His brief: *"fail closed on unreadable stores (no false HOLDS / empty wipe)"*.
An endpoint that does not answer must leave an explicit `unreadable` record. On the guest an
empty vault and an unread vault look identical, and only one of them means he owns nothing —
which is exactly what his screenshot showed before the mirror existed: every locker reading
"0 · empty locker" because there was no mirror at all. [[zero-needs-a-denominator]]
"""
import io
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import guest_profile as gp

# A stand-in for his machine. Deliberately NOT his real values — a law that hard-codes the very
# identifiers it protects would be the leak it exists to prevent.
FAKE_LIVE = {
    "id": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
    "computer": "someone-2.local",
    "user": "someone",
    "platform": "mac",
    "nickname": "Konyo",
}


class TheGuestSeatIsGrokNotKonyo(unittest.TestCase):

    def test_the_actor_is_grok_on_grok_bot(self):
        p = gp.profile()
        print("   profile: %s" % json.dumps(p))
        self.assertEqual(p["nickname"], "Grok")
        self.assertEqual(p["computer"], "grok-bot")
        self.assertIs(p["guest"], True, "the box doctor asserts guest:true")

    def test_the_id_is_stable_across_runs(self):
        """A per-run id would mint a fresh empty world on every look, and the seat would report
        an empty SHELF forever."""
        a, b = gp.profile()["id"], gp.profile()["id"]
        print("   id stable: %s" % (a == b))
        self.assertEqual(a, b)
        self.assertTrue(len(a) >= 16, "an identity the board keys stores by cannot be a stub")

    def test_status_reports_grok_and_keeps_nothing_of_his(self):
        payload = {
            "identity": dict(FAKE_LIVE),
            "ver": "v3185",
            "reelPath": "/Users/someone/d2r/reels",
            "note": "Konyo owns this board",
            "nested": [{"someone-2.local": {"home": "/Users/someone"}}],
        }
        out = gp.rewrite_status(payload, FAKE_LIVE)
        print("   identity after: %s" % json.dumps(out["identity"]))
        self.assertEqual(out["identity"]["nickname"], "Grok")
        self.assertIs(out["guest"], True)
        leaked = gp.leaks(out, FAKE_LIVE)
        print("   leaks remaining: %r" % (leaked,))
        self.assertEqual(leaked, [],
                         "the mirror still carries his machine's identifiers: %r" % (leaked,))
        # ⚠⚠ AND A LITERAL CHECK, BECAUSE leaks() CANNOT SEE A SECRET IT FORGOT. The detector and
        # the scrub read the SAME pair list, so deleting a pair blinds both at once and the
        # assertion above goes green over a mirror that still says his name. Proven: a sabotage
        # removing the Konyo pair passed the leaks() check and was caught only here. A detector
        # must not be its own witness. [[feedback-blind-fixture-green-gate]]
        blob = json.dumps(out, ensure_ascii=False)
        for literal in ("Konyo", "someone-2", "/Users/someone"):
            self.assertNotIn(literal, blob,
                             "%r survived the scrub into the guest mirror" % literal)

    def test_the_scrub_reaches_dict_KEYS_not_only_values(self):
        """Per-session dumps are KEYED by path. A scrub that walked only values would leave the
        keys intact and leak the whole home directory one filename at a time."""
        obj = {"/Users/someone/reels/r1": {"ok": True}}
        out = gp.scrub(obj, FAKE_LIVE)
        print("   keys after: %r" % (list(out),))
        self.assertEqual(gp.leaks(out, FAKE_LIVE), [],
                         "a dict KEY carried his home path through the scrub")

    def test_the_identity_is_replaced_not_merged(self):
        """A merge keeps any key of his the scrub did not know about."""
        payload = {"identity": dict(FAKE_LIVE, secretField="someone-2.local")}
        out = gp.rewrite_status(payload, FAKE_LIVE)
        self.assertNotIn("secretField", out["identity"],
                         "the identity was patched rather than replaced, so an unknown key of "
                         "his survived into the guest")

    def test_an_unreadable_store_is_never_an_empty_one(self):
        u = gp.unreadable("api/vault_ledger", "the live console did not answer")
        print("   unreadable record: %s" % json.dumps(u))
        self.assertTrue(gp.is_unreadable(u))
        self.assertIs(u["ok"], False)
        self.assertTrue(u.get("why"), "an unreadable store that cannot say why is a silent zero")
        self.assertNotEqual(u, {}, "an unread vault must not be shaped like an empty one")

    def test_the_leak_detector_can_actually_find_a_leak(self):
        """⚠ A detector that never fires is indistinguishable from a clean tree. This proves the
        gate itself works before any clean result from it is believed.
        [[feedback-blind-fixture-green-gate]]"""
        dirty = {"path": "/Users/someone/d2r", "host": "someone-2.local"}
        found = gp.leaks(dirty, FAKE_LIVE)
        print("   leaks found in a deliberately dirty object: %r" % (found,))
        self.assertTrue(found, "the leak detector reported clean on an object that is not")

    def test_the_sync_script_ships_no_mutating_endpoint(self):
        """His brief puts 'mutating vault possession from guest smokes' out of scope. A mirror
        that carried a write door would let an eyes-loop change what he owns."""
        p = os.path.join(HERE, "sync_guest_api.sh")
        self.assertTrue(os.path.exists(p), "the one command does not exist")
        src = io.open(p, encoding="utf-8").read()
        i = src.find("READ_ONLY=(")
        j = src.find(")", i)
        self.assertGreater(i, 0, "the allowlist is gone")
        allow = src[i:j]
        banned = ["board_tick", "chronicle_apply", "vault_apply", "vault_forget",
                  "session/delete", "relaunch", "restart", "quit", "api/update", "api/off",
                  "api/on", "api/stop"]
        hit = [b for b in banned if b in allow]
        print("   mutating endpoints inside the allowlist: %r" % (hit,))
        self.assertEqual(hit, [],
                         "the guest mirror would carry a write door: %r" % (hit,))


if __name__ == "__main__":
    unittest.main(verbosity=2)
