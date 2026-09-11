#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2813 — A BLIND `rm -f` WOULD HAVE DELETED HIS LIVE BOARD CLAIM.

The standing routine said: after any render/CDP session, `rm -f tv/.board_identity.json` before
pushing — because a CDP load can leave a GUEST record and five TestV2072 assertions then fail with
a drift reason that names none of it. That scar is real and the removal is right FOR THAT RECORD.

MEASURED 2026-09-09, on the record actually present:

    firstSeen            01:04:20
    his console started  01:04:29      <- NINE SECONDS LATER
    lastSeen             01:25:14   seenCount 28    <- still being written, live
    owner=True  pfx=''  previous=None               -> board_identity_drift() == "ok"

His console's live world record. Not a harness leftover. `board_identity_drift`'s own docstring
says an absent record is `unknown` and deliberately NOT `ok`, "because a world nobody has seen
cannot be shown to be the same one" — so removing this one DEGRADES a healthy state, and the next
write starts a fresh id with `previous: None`, the exact shape that makes a real board read as a
stranger's world.

★ THE RULE IS THE RECORD'S STATE, NOT THE RITUAL. A routine that always removes cannot tell the
world it is protecting from the world it is destroying. [[board-claim-pinned-to-a-mutable-id]]
[[unknown-stays-unknown]] [[borrowed-surface]]
"""
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import board_identity_sweep as BIS  # noqa: E402

OK_REC = {"owner": True, "pfx": "", "id": "aaa", "profile": "main", "previous": None}
GUEST_REC = {"owner": False, "pfx": "g7", "id": "bbb", "profile": "main", "previous": None}
DRIFT_REC = {"owner": True, "pfx": "", "id": "ccc", "profile": "main",
             "previous": {"id": "aaa", "profile": "main"}}


class TestTheSweepKnowsWhoseWorldItIs(unittest.TestCase):

    def setUp(self):
        # ⚠ NEVER his live tv/. A fixture that writes into real evidence is the defect this repo
        # produced tonight in a different gate. [[feedback-fixtures-never-touch-live-data]]
        self.root = tempfile.mkdtemp(prefix="board_sweep_gate.")
        self._real_console = BIS.console_is_running
        BIS.console_is_running = lambda port=None: None   # no live writer in the fixture
        self.assertNotEqual(os.path.realpath(self.root), os.path.realpath(HERE))

    def tearDown(self):
        BIS.console_is_running = self._real_console

    def _write(self, rec):
        p = BIS.path_for(self.root)
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(rec))
        return p

    def test_a_healthy_owner_record_is_KEPT(self):
        """The one that matters. A blind rm here destroys his claim."""
        p = self._write(OK_REC)
        r = BIS.sweep(root=self.root)
        self.assertEqual(r["state"], BIS.OK, r["why"])
        self.assertEqual(r["action"], "kept",
                         "a healthy owner record was swept — that turns ok into unknown and "
                         "starts a fresh install id, which is how a real board reads as a "
                         "stranger's world")
        self.assertTrue(os.path.isfile(p), "his live claim was deleted")

    def test_a_guest_record_IS_swept(self):
        """The scar the routine was written for must still be honoured."""
        p = self._write(GUEST_REC)
        r = BIS.sweep(root=self.root)
        self.assertEqual(r["state"], BIS.GUEST, r["why"])
        self.assertEqual(r["action"], "swept",
                         "the CDP guest record survived — five TestV2072 assertions will fail "
                         "with a drift reason that names none of it")
        self.assertFalse(os.path.isfile(p), "the guest record is still on disk")
        self.assertTrue(os.path.isfile(r["backup"]), "swept without a backup")

    def test_a_drifted_record_IS_swept(self):
        p = self._write(DRIFT_REC)
        r = BIS.sweep(root=self.root)
        self.assertEqual(r["state"], BIS.DRIFTED, r["why"])
        self.assertEqual(r["action"], "swept", "a different install came back and was left in place")
        self.assertFalse(os.path.isfile(p))

    def test_no_record_is_UNKNOWN_and_not_a_clean_sweep(self):
        r = BIS.sweep(root=self.root)
        self.assertEqual(r["state"], BIS.ABSENT,
                         "an absent record reported as something other than ABSENT — a world "
                         "nobody has seen is UNKNOWN, never clean")
        self.assertEqual(r["action"], "none")

    def test_an_unreadable_record_is_never_deleted(self):
        p = BIS.path_for(self.root)
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        r = BIS.sweep(root=self.root)
        self.assertEqual(r["action"], "kept",
                         "an unreadable record was deleted — a file that cannot be parsed is not "
                         "a file proven bad")
        self.assertTrue(os.path.isfile(p))

    def test_it_REFUSES_while_his_console_is_running(self):
        """A live writer owns that file. Sweeping under it races the process."""
        BIS.console_is_running = lambda port=None: 17772
        p = self._write(GUEST_REC)
        r = BIS.sweep(root=self.root)
        self.assertEqual(r["action"], "refused",
                         "swept a record out from under a running console — a half-written record "
                         "reads as neither state")
        self.assertTrue(os.path.isfile(p), "his console's file was removed mid-write")

    # ══ THE JOIN, AND IT IS A MAPPING NOT A VOCABULARY ═══════════════════════════════════════
    #: every shape the writer can actually emit. `_board_identity_of` stores
    #: `bool(payload.get("owner"))` and `payload.get("pfx")` AS-IS, so owner=False with an empty or
    #: missing pfx is a record that really occurs — and it is the row nobody tested.
    JOIN_TABLE = [
        ("a healthy claim",              {"owner": True,  "pfx": "",   "previous": None}),
        ("a claim from another install", {"owner": True,  "pfx": "",   "previous": {"id": "old"}}),
        ("the CDP guest record",         {"owner": False, "pfx": "g7", "previous": None}),
        ("owner false, EMPTY pfx",       {"owner": False, "pfx": "",   "previous": None}),
        ("owner false, NO pfx key",      {"owner": False,              "previous": None}),
        ("no owner key at all",          {"pfx": "",                   "previous": None}),
    ]

    def test_the_sweeper_and_the_CONSOLE_agree_on_every_record_the_writer_can_emit(self):
        """⚠⚠ v2920 — THE LAW THIS SUITE HAS NEVER HAD, AND ITS ABSENCE ALMOST COST HIS CLAIM.

        v2918 shipped a second sweeper that classified on `owner` ALONE. It disagreed with
        `control_app.board_identity_drift()` on THREE of five records — it KEPT what the console
        calls drift, and DELETED what the console calls ok. v2919 deleted that tool, and deleted
        the law that was supposed to have caught it: a check that walked the AST for dict keys
        named "state" and asserted a VOCABULARY SUBSET. Matching words while the mapping differs is
        not a join, and REG-923 named it.

        ⚠ THE DELETION LEFT THE GAP OPEN. Found by the cross-family eye on v2919: this suite tests
        three hand-built fixtures — OK_REC, GUEST_REC, DRIFT_REC — and **never imports control_app
        at all**. `board_identity_drift` appears in it twice, both times in a COMMENT. So the one
        record that made the deleted tool dangerous, `{owner: False, pfx: ""}`, was untested: the
        console calls it **ok, keep**; the deleted guard called it **drift, delete**. Re-introduce
        that rule tomorrow and every law here stays green.

        This asks the CONSOLE, on every shape the writer can emit, and compares the DECISION —
        sweep or keep — not the spelling. [[the-unjoined-end]] [[copy-drift]]
        """
        import control_app as ca
        # ⚠ DRIVE ITS OWN READER, DO NOT RE-IMPLEMENT ITS RULE. `board_identity_drift()` takes no
        # arguments — it reads through `_board_identity_last()`. Swapping that reader feeds the REAL
        # decision function a record; transcribing its `if`s here would create the second rule this
        # law exists to forbid. [[copy-drift]]
        orig_reader = ca._board_identity_last
        wrong = []
        try:
            for label, rec in self.JOIN_TABLE:
                ca._board_identity_last = (lambda _r=rec: dict(_r))
                theirs = ca.board_identity_drift()
                if not isinstance(theirs, dict):
                    self.fail("board_identity_drift() did not answer with a dict for %r: %r"
                              % (label, theirs))
                console_sweeps = str(theirs.get("state")) == "drift"
                mine_sweeps = BIS.classify(rec)[0] in (BIS.GUEST, BIS.DRIFTED)
                if console_sweeps != mine_sweeps:
                    wrong.append("%s: console says %s, the sweeper would %s"
                                 % (label, theirs.get("state"),
                                    "SWEEP" if mine_sweeps else "KEEP"))
        finally:
            ca._board_identity_last = orig_reader
        self.assertEqual(wrong, [],
                         "the sweeper and the console disagree about whether to DELETE:\n  %s"
                         % "\n  ".join(wrong))

    def test_the_join_asks_the_console_ITSELF_and_not_a_copy_of_its_rule(self):
        """⚠ A TRANSCRIBED RULE IS A SECOND RULE. If this suite re-implemented the console's
        decision instead of calling it, the two would drift apart silently — which is the whole
        defect above, one layer up. The law must IMPORT control_app and CALL
        board_identity_drift(). [[copy-drift]]"""
        src = io.open(os.path.join(HERE, "test_the_sweep_knows_whose_world_it_is.py"),
                      encoding="utf-8").read()
        import ast as _ast
        calls = 0
        for n in _ast.walk(_ast.parse(src)):
            if isinstance(n, _ast.Call) and isinstance(n.func, _ast.Attribute) \
               and n.func.attr == "board_identity_drift":
                calls += 1
        self.assertGreaterEqual(calls, 1,
                                "no law here CALLS board_identity_drift() — the join is prose, and "
                                "a suite that only reads fixtures cannot notice the console "
                                "changing its mind")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "removing the OK guard is the blind `rm -f` that would delete his live claim",
        "file": "board_identity_sweep.py",
        "find": "    if state == OK and not force:",
        "replace": "    if False:",
        "matches": 1,
    },
    {
        "why": "dropping the live-console check races the process that owns the file",
        "file": "board_identity_sweep.py",
        "find": "    pid = console_is_running()",
        "replace": "    pid = None",
        "matches": 1,
    },
    {
        "why": "reintroducing the v2918 mistake: classify on `owner` ALONE, ignoring pfx. The console calls owner=false with no pfx OK; this would sweep it. MEASURED red on three records at once - empty pfx, missing pfx key, and no owner key at all.",
        "file": "board_identity_sweep.py",
        "find": "    if (not rec.get(\"owner\")) and rec.get(\"pfx\"):",
        "replace": "    if not rec.get(\"owner\"):",
        "matches": 1,
    },
    {
        "why": "dropping the `previous` check makes a board that came back as a DIFFERENT install read as a healthy claim - the console still calls it drift, so the two decisions split.",
        "file": "board_identity_sweep.py",
        "find": "    if rec.get(\"previous\"):",
        "replace": "    if False:",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
