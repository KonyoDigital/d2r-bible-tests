# -*- coding: utf-8 -*-
"""A DIFFERENT WORLD'S 60 s HAND-OVER OVERWROTE HIS BANKED VAULT (#110, MED #3).

Reproduced: POST {stores:{d2r_owned:[Harlequin Crest, Griffon's Eye]}} banks fine; a SECOND
hand-over from another world (another PC / a guest tab / a raw POST) then REPLACES board_stores.json
wholesale, and board_mask() publishes the stranger's items as HIS d2r_owned - self-correcting only
~60 s later when his own board re-posts.

WHY IT IS THE SAME DEFECT THE COUNTS ALREADY FIXED. board_tally_merge was written on his machine
2026-08-28 for exactly this ("a second page in a different world ... posted 117/266 and REPLACED
his 120/280"): it banks PER WORLD (byRoute) and publishes only the OWNER world, identified by
board_own_route_id - the board's OWN store - because "empty prefix means owner" turned out to be a
coincidence (two worlds posted pfx ""). accept_handed_stores, added in the SAME v3379, kept a single
global slot keyed by nothing. The cure existed one function over and was never carried across.
[[copy-drift]] [[the-unjoined-end]]

THE FIX veils the WRITE, never the reader (his 10-04 shadow-reader ruling: the hand-over must keep
running): a hand-over from a different world than the one on record may replace it only when it is
this board's own owner. Same-world updates and the first write are untouched.

REG-2273 (#139): "owner id unknown, so nobody else may write" also refused the owner. A main↔ladder
switch is the same install and is allowed with the owner id unread. An owner-shaped write (pfx "" or
L·) may reclaim a slot a guest posted first (pfx I· / IL·). Two owner-shaped installs stay apart when
the owner id is unknown — that is still the 2026-08-28 hole — and that refusal does not promise a
re-post this function would drop. [[unknown-stays-unknown]]

Fixtures only: _board_stores_path is pointed at a temp dir and board_own_route_id is stubbed, so his
real board_stores.json and WebKit store are never opened. [[test-venue]] (pure python, no browser)
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# ⚠ cp1255 operator console: make stdout survive non-ASCII before anything prints, or a clean tree
# dies inside the print that reports it (REG-044/054/077, the same bug three times).
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app as CA  # noqa: E402

# his real board vs a stranger: different install ids, both owner-SHAPED (empty prefix) - precisely
# the 2026-08-28 case where the prefix alone could not tell them apart.
OWNER = {"id": "c5c2c92d", "p": "main", "pfx": ""}
OTHER = {"id": "77f64154", "p": "main", "pfx": ""}
HIS_VAULT = ["Harlequin Crest", "Griffon's Eye"]
THEIR_VAULT = ["Stormshield", "Andariel's Visage"]


class AForeignWorldDoesNotOverwriteBankedStores(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="foreignstores_")
        self._old_path = CA._board_stores_path
        CA._board_stores_path = lambda: os.path.join(self.d, "board_stores.json")
        # DETERMINISTIC: the owner is UNKNOWN by default (no WebKit store on the venue - the Windows
        # reality), the case that proves a stranger still cannot flip the record.
        self._old_own = CA.board_own_route_id
        CA.board_own_route_id = lambda: None

    def tearDown(self):
        CA._board_stores_path = self._old_path
        CA.board_own_route_id = self._old_own
        shutil.rmtree(self.d, ignore_errors=True)

    def _owned(self):
        doc = CA.board_stores_load() or {}
        return (doc.get("stores") or {}).get("d2r_owned")

    # -- THE DEFECT, end to end --------------------------------------------------------------
    def test_a_different_world_cannot_replace_the_owner_vault(self):
        first, _ = CA.accept_handed_stores({"stores": {"d2r_owned": HIS_VAULT}}, OWNER)
        self.assertEqual(first, 1, "his own first hand-over did not bank")
        self.assertEqual(self._owned(), HIS_VAULT)

        saved, why = CA.accept_handed_stores({"stores": {"d2r_owned": THEIR_VAULT}}, OTHER)
        self.assertEqual(saved, 0,
                         "a different world's hand-over was banked over his vault (%s)" % why)
        self.assertIn("different world", (why or ""),
                      "the refusal does not say WHY the stores were kept")
        self.assertNotIn("re-posts", (why or ""),
                         "the owner id is unknown, so a promise that the owner can re-post is a lie: "
                         "that re-post takes this same branch")
        self.assertIn("unknown", (why or "").lower(),
                      "the refusal must say the owner id is unknown, not that the owner was identified")
        self.assertEqual(self._owned(), HIS_VAULT,
                         "board_stores.json now holds the other PC's items as his d2r_owned - "
                         "board_mask would publish the stranger's vault as his")

    # -- his own board keeps updating (the fix must not freeze the 60 s sync) ----------------
    def test_the_same_world_still_updates_its_own_stores(self):
        CA.accept_handed_stores({"stores": {"d2r_owned": HIS_VAULT}}, OWNER)
        grew = HIS_VAULT + ["The Stone of Jordan"]
        saved, why = CA.accept_handed_stores({"stores": {"d2r_owned": grew}}, OWNER)
        self.assertEqual(saved, 1, "his own board could not update its banked stores (%s)" % why)
        self.assertEqual(self._owned(), grew)

    # -- a main<->ladder profile switch is the SAME owner, never a stranger ------------------
    def test_a_profile_switch_on_his_install_is_not_blocked(self):
        CA.accept_handed_stores({"stores": {"d2r_owned": HIS_VAULT}}, OWNER)
        ladder = {"id": OWNER["id"], "p": "ladder", "pfx": "L·"}
        ladder_vault = ["Death's Web"]
        CA.board_own_route_id = lambda: OWNER["id"]   # his install is known; a profile is his world
        saved, why = CA.accept_handed_stores({"stores": {"d2r_owned": ladder_vault}}, ladder)
        self.assertEqual(saved, 1,
                         "his own ladder profile was refused as if it were another PC (%s)" % why)
        self.assertEqual(self._owned(), ladder_vault)

    # -- the owner reclaims from a guest that happened to post first -------------------------
    def test_the_owner_reclaims_from_a_guest_that_posted_first(self):
        CA.accept_handed_stores({"stores": {"d2r_owned": THEIR_VAULT}}, OTHER)
        self.assertEqual(self._owned(), THEIR_VAULT)
        # the board's own store now names the owner; his post takes it back on IDENTITY
        # (board_own_route_id), never on the prefix - both worlds carry pfx "".
        CA.board_own_route_id = lambda: OWNER["id"]
        saved, why = CA.accept_handed_stores({"stores": {"d2r_owned": HIS_VAULT}}, OWNER)
        self.assertEqual(saved, 1, "the owner could not reclaim its own bank (%s)" % why)
        self.assertEqual(self._owned(), HIS_VAULT)

    # -- the first write is untouched --------------------------------------------------------
    def test_the_first_hand_over_is_untouched(self):
        saved, _ = CA.accept_handed_stores({"stores": {"d2r_owned": HIS_VAULT}}, OWNER)
        self.assertEqual(saved, 1)
        self.assertEqual(self._owned(), HIS_VAULT)

    # -- REG-2273: same install, owner id unread, is a profile switch not a stranger --------
    def test_a_profile_switch_is_allowed_when_the_owner_id_is_unknown(self):
        CA.accept_handed_stores({"stores": {"d2r_owned": HIS_VAULT}}, OWNER)
        ladder = {"id": OWNER["id"], "p": "ladder", "pfx": "L·"}
        saved, why = CA.accept_handed_stores({"stores": {"d2r_owned": ["Death's Web"]}}, ladder)
        self.assertEqual(saved, 1,
                         "his own ladder profile was refused because the owner id could not be "
                         "read (%s)" % why)
        self.assertEqual(self._owned(), ["Death's Web"])

    # -- REG-2273: a guest prefix is proven not the owner; an owner-shaped write takes it back
    def test_an_owner_shaped_write_reclaims_a_guest_when_the_owner_id_is_unknown(self):
        guest = {"id": OTHER["id"], "p": "main", "pfx": "I·77f64154·"}
        CA.accept_handed_stores({"stores": {"d2r_owned": THEIR_VAULT}}, guest)
        self.assertEqual(self._owned(), THEIR_VAULT)
        saved, why = CA.accept_handed_stores({"stores": {"d2r_owned": HIS_VAULT}}, OWNER)
        self.assertEqual(saved, 1,
                         "an owner-shaped board could not reclaim a guest that posted first (%s)"
                         % why)
        self.assertEqual(self._owned(), HIS_VAULT)

    def test_a_guest_cannot_replace_an_owner_shaped_bank_when_the_owner_id_is_unknown(self):
        CA.accept_handed_stores({"stores": {"d2r_owned": HIS_VAULT}}, OWNER)
        guest = {"id": OTHER["id"], "p": "main", "pfx": "I·77f64154·"}
        saved, why = CA.accept_handed_stores({"stores": {"d2r_owned": THEIR_VAULT}}, guest)
        self.assertEqual(saved, 0, "a guest replaced the owner-shaped bank (%s)" % why)
        self.assertEqual(self._owned(), HIS_VAULT)

    def test_a_known_owner_still_names_the_re_post(self):
        CA.board_own_route_id = lambda: OWNER["id"]
        CA.accept_handed_stores({"stores": {"d2r_owned": HIS_VAULT}}, OWNER)
        saved, why = CA.accept_handed_stores({"stores": {"d2r_owned": THEIR_VAULT}}, OTHER)
        self.assertEqual(saved, 0)
        self.assertIn("re-posts", why or "",
                      "once the owner id is known, the refusal may say the owner can re-post, "
                      "because that re-post matches the id and is accepted")
        self.assertEqual(self._owned(), HIS_VAULT)


RED_PROOF = [
    {
        'why': 'THE WHOLE DEFECT: neuter the owner-gate and a different world\'s 60 s hand-over '
               'replaces his banked vault again - board_mask then publishes the other PC\'s items '
               'as his d2r_owned. test_a_different_world_cannot_replace_the_owner_vault must fail.',
        'file': 'control_app.py',
        'find': '            if not (_same_install or _owner_match or _reclaim_guest):',
        'replace': '            if False:',
        'matches': 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
