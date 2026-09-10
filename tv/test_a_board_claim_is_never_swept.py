"""HIS CLAIM IS NEVER MINE TO REMOVE, AND A RULE WITHOUT ITS CONDITION IS HOW IT GETS REMOVED.

⚠⚠ MEASURED 2026-09-11, and the defect was me following the rule exactly. The standing instruction
read: *"AFTER ANY RENDER/CDP SESSION: `rm -f tv/.board_identity.json` before pushing — a CDP load
writes a GUEST record and five TestV2072 tests then fail with a drift reason that names none of it."*
Every word of that is true. It is missing its condition.

After a clean render I ran it and deleted a record reading:

    owner: true · id e07a5fe180a8414287f30dcc2589c52d · seenCount 1458

That is HIS CLAIM. `tv/.board_identity.json` is gitignored (.gitignore:68), so `git checkout` could
not restore it. It came back on two accidents: a file in `~/d2r_board_backups/` that happened to
carry the same id, and my having PRINTED the id before removing it. That backup was **stale by 677
sightings** (781 against the live 1458). Lose the claim for real and his board renders as an empty
stranger's world — 0 of 403, with a claim button that imports nothing.

⚠ SO THE CONDITION LIVES IN CODE NOW. A rule whose safety depends on the reader being careful at 2am
is a rule that will be followed carelessly once. `board_claim_guard` asks OWNER FIRST and reuses the
three states `control_app.board_identity_drift()` already names, so the tool and the console describe
the same world in the same words:

    owner is True   -> ok       HIS CLAIM. Nothing is removed, ever.
    owner is False  -> drift    the CDP-minted guest record the rule exists for. Backed up, removed.
    anything else   -> unknown  unreadable, malformed or absent. Nothing is removed.

[[board-claim-pinned-to-a-mutable-id]] [[unknown-stays-unknown]] [[stale-reading]]
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

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import board_claim_guard as BG  # noqa: E402


class _Bench(object):
    """A record and a backup dir, both throwaway. His real files are never touched."""

    def __init__(self, rec):
        self.dir = tempfile.mkdtemp(prefix="claimguard_")
        self.rec = os.path.join(self.dir, ".board_identity.json")
        self.backups = os.path.join(self.dir, "backups")
        if rec is not None:
            io.open(self.rec, "w", encoding="utf-8").write(json.dumps(rec))

    def sweep(self, act=True):
        return BG.sweep(path=self.rec, backups=self.backups, act=act)

    def exists(self):
        return os.path.exists(self.rec)

    def backups_written(self):
        return sorted(os.listdir(self.backups)) if os.path.isdir(self.backups) else []

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)


HIS = {"owner": True, "id": "e07a5fe180a8414287f30dcc2589c52d", "pfx": "", "seenCount": 1458}
GUEST = {"owner": False, "id": "g7abc", "pfx": "g7", "profile": "main"}


class ABoardClaimIsNeverSwept(unittest.TestCase):

    def test_HIS_CLAIM_is_never_removed(self):
        """⚠⚠ THE HEADLINE, AND THE ONE I BROKE BY HAND. owner=true is his claim. There is no flag,
        no force, and no code path here that removes it."""
        b = _Bench(HIS)
        try:
            r = b.sweep()
            self.assertEqual(r["state"], "ok", "his claim must read ok: %r" % r)
            self.assertFalse(r["removed"], "his claim was REMOVED — this is the exact defect: %r" % r)
            self.assertTrue(b.exists(), "the record file is gone; it is gitignored and unrecoverable")
        finally:
            b.close()

    def test_a_GUEST_record_is_removed_and_backed_up_FIRST(self):
        """The state the rule exists for. It is removed — and a copy is taken before it goes."""
        b = _Bench(GUEST)
        try:
            r = b.sweep()
            self.assertEqual(r["state"], "drift", "a guest record must read drift: %r" % r)
            self.assertTrue(r["removed"], "the guest record was not removed: %r" % r)
            self.assertFalse(b.exists(), "the guest record is still on disk")
            self.assertTrue(r["backup"] and os.path.exists(r["backup"]),
                            "no backup was written before removal: %r" % r)
        finally:
            b.close()

    def test_the_backup_is_taken_at_REMOVAL_TIME_not_trusted_from_the_past(self):
        """⚠ THE ONE THAT SAVED ME WAS 677 SIGHTINGS STALE (781 against a live 1458). A snapshot that
        is only sometimes current is a safety net with a hole in it, so the copy must be of the bytes
        being deleted — not of whatever a previous run happened to leave. [[stale-reading]]"""
        b = _Bench(GUEST)
        try:
            r = b.sweep()
            self.assertTrue(r["backup"], "no backup path returned: %r" % r)
            saved = json.load(io.open(r["backup"], encoding="utf-8"))
            self.assertEqual(saved, GUEST,
                             "the backup is not a copy of the record that was deleted: %r" % saved)
        finally:
            b.close()

    def test_a_record_it_cannot_COPY_is_a_record_it_does_not_REMOVE(self):
        """⚠ If the backup cannot be written, nothing is deleted. A removal whose undo failed is a
        removal with no undo, which is the whole fault this file exists about."""
        b = _Bench(GUEST)
        try:
            # a FILE where the backup directory must go, so makedirs/copy cannot succeed
            io.open(b.backups, "w", encoding="utf-8").write("not a directory")
            r = b.sweep()
            self.assertFalse(r["removed"],
                             "it removed the record after failing to back it up: %r" % r)
            self.assertTrue(b.exists(), "the record was deleted with no copy taken")
        finally:
            b.close()

    def test_an_UNREADABLE_or_ODD_owner_is_UNKNOWN_and_UNKNOWN_is_not_permission(self):
        """owner must be exactly True or exactly False. Anything else — None, a string, a missing
        key — is UNKNOWN, and nothing is removed on an UNKNOWN."""
        for odd in (None, "yes", 1, 0, "false"):
            b = _Bench({"owner": odd, "id": "x"})
            try:
                r = b.sweep()
                self.assertEqual(r["state"], "unknown",
                                 "owner=%r must read unknown, not %r" % (odd, r["state"]))
                self.assertFalse(r["removed"], "owner=%r was treated as permission: %r" % (odd, r))
                self.assertTrue(b.exists(), "owner=%r had its record removed" % (odd,))
            finally:
                b.close()

    def test_a_missing_owner_KEY_is_UNKNOWN_too(self):
        """A record with no `owner` at all is not a guest record."""
        b = _Bench({"id": "x", "pfx": "g7"})
        try:
            r = b.sweep()
            self.assertEqual(r["state"], "unknown", "%r" % r)
            self.assertFalse(r["removed"], "%r" % r)
        finally:
            b.close()

    def test_ABSENT_is_not_a_guest_record(self):
        """Nothing on disk is nothing to remove — and it must not report as a successful sweep."""
        b = _Bench(None)
        try:
            r = b.sweep()
            self.assertEqual(r["state"], "unknown", "%r" % r)
            self.assertFalse(r["removed"], "%r" % r)
        finally:
            b.close()

    def test_check_only_never_removes_anything(self):
        """⚠ READING THE STATE MUST NOT CHANGE IT — the defect #75 was opened about, one system over,
        where a read-only audit banked three rows into a lock ledger."""
        b = _Bench(GUEST)
        try:
            r = b.sweep(act=False)
            self.assertEqual(r["state"], "drift", "it must still SAY drift: %r" % r)
            self.assertFalse(r["removed"], "--check removed the record: %r" % r)
            self.assertTrue(b.exists(), "--check deleted the file")
        finally:
            b.close()

    def test_it_speaks_the_same_three_states_as_the_console(self):
        """⚠ ONE VOCABULARY. `control_app.board_identity_drift()` already names ok / drift / unknown.
        A tool that invented a fourth word would make two surfaces describe one world differently —
        the defect this repo has paid for repeatedly. [[copy-drift]]"""
        import ast
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        node = None
        for n in ast.walk(ast.parse(src)):
            if isinstance(n, ast.FunctionDef) and n.name == "board_identity_drift":
                node = n
        self.assertIsNotNone(node, "board_identity_drift() is gone — this law must be re-derived")
        theirs = set()
        for m in ast.walk(node):
            if isinstance(m, ast.Dict):
                for k, v in zip(m.keys, m.values):
                    if isinstance(k, ast.Constant) and k.value == "state" and isinstance(v, ast.Constant):
                        theirs.add(v.value)
        mine = set()
        for rec in (HIS, GUEST, {"owner": None}):
            b = _Bench(rec)
            try:
                mine.add(b.sweep(act=False)["state"])
            finally:
                b.close()
        self.assertTrue(mine <= theirs,
                        "the guard speaks state(s) the console never names: %s vs %s"
                        % (sorted(mine - theirs), sorted(theirs)))


RED_PROOF = [
    {
        "why": "deleting the owner-is-True refusal is the exact defect: the guard would then fall through and sweep HIS CLAIM, which is gitignored and unrecoverable.",
        "file": "board_claim_guard.py",
        "find": "    if own is True:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "treating any non-False owner as a guest record turns UNKNOWN into permission \u2014 a malformed record would be swept.",
        "file": "board_claim_guard.py",
        "find": "    if own is False:\n",
        "replace": "    if own is not True:\n",
        "matches": 1,
    },
    {
        "why": "removing the record before the backup is taken restores 'a removal whose undo failed'. The EARLY RETURN is what prevents it, so the sabotage drops the return \u2014 an earlier version edited only the message and came back BLIND, because a sabotage that changes prose defeats nothing.",
        "file": "board_claim_guard.py",
        "find": "        out[\"why\"] = (\"could not take a fresh backup (%s) \u2014 refusing to remove a record I cannot \"\n                      \"first copy\" % type(exc).__name__)\n        return out\n",
        "replace": "        out[\"why\"] = (\"could not take a fresh backup (%s) \u2014 refusing to remove a record I cannot \"\n                      \"first copy\" % type(exc).__name__)\n        pass\n",
        "matches": 1,
    },
    {
        "why": "letting --check act makes reading the state change it \u2014 the same defect #75 found in the lock ledger, where a read-only audit banked three rows.",
        "file": "board_claim_guard.py",
        "find": "    if state != \"drift\" or not act:\n",
        "replace": "    if state != \"drift\":\n",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
