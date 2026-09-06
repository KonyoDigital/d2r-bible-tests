# -*- coding: utf-8 -*-
"""v2731 — A BACKUP THAT RUNS EVERY TEN MINUTES AND HAS NEVER COPIED TWO OF HIS SIX LEDGERS.

MEASURED across all 60 of his real backup files, 2026-09-06 — every single one:
    foundLog   419  ✅        rwMade      —  ❌ ABSENT   (his 99 runewords)
    owned      169  ✅        gameFound   —  ❌ ABSENT   (his 29 in-game records)
    setPieces  123  ✅        route/profile — ❌ NOT RECORDED

His instruction was explicit: *"i want it no wiped · i want that saved · and being able to be
restored · indefinitely"*. Two of the six stores had no automatic copy at all.

⚠⚠ AND IT BLINDED A WATCHER, WHICH IS THE WORSE HALF. `tv/ledger_highwater.py` ratchets
KEYS = (foundLog, setPieces, rwMade, owned) against each key's historic maximum — and since no
snapshot has ever carried `rwMade`, that column can only ever read UNKNOWN. An UNKNOWN column looks
exactly like a column with nothing wrong. A loop that runs every ten minutes and writes a plausible
14 KB file is the most convincing kind of gap there is. [[unknown-stays-unknown]] [[the-unjoined-end]]

=== WHY THE TWO STORES NEEDED DIFFERENT FIXES, AND WHY THE FIRST ATTEMPT WAS WRONG ===
They looked identical and were not:
  · `gameFound` was ALREADY being returned in full (`var gameFound=...raw('d2r_gameFound')`,
    emitted top-level). Pure plumbing: nobody folded it into the backed-up ledger.
  · `rwMade` existed only as a COUNT — `Object.keys(m).length` — so it could be counted and never
    copied. It needed fetching, not plumbing.
⚠ MY FIRST PATCH ASSUMED THEY WERE THE SAME and added fresh reads for both plus a second
`gameFound:` key into the same JS object literal, where the later key silently wins. It was
reverted before it ran. The lesson is the ordinary one: read the literal, then patch it.

=== WHAT THIS PINS ===
The load-bearing law is `test_gameFound_is_NOT_graded_for_truncation`. The truncation check compares
a copy against a count the board reports INDEPENDENTLY. `counts.runewordsMade` is such a count, so
rwMade is graded. There is no independent count for gameFound, so the only comparison available is
the copy against its own length — which cannot fail, and a check that cannot fail is worse than no
check because it reads as coverage. It is skipped, deliberately, and this file says so.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

SRC = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()


def _between(src, start, end, whence=0):
    """Anchored at BOTH ends — never a fixed window. [[source-reading-guard]]"""
    i = src.find(start, whence)
    if i < 0:
        return None
    j = src.find(end, i + len(start))
    return None if j < 0 else src[i:j + len(end)]


class LedgerBackupCoversEveryStore(unittest.TestCase):

    def test_the_guard_can_find_the_snapshot_at_all(self):
        """⚠ A law that finds nothing to grade passes having examined ZERO candidates."""
        self.assertIn("_ledger_snapshot_once", SRC,
                      "the backup writer is gone or renamed — fix this guard before trusting it")
        self.assertIn("board_ownership", SRC, "the snapshot no longer asks the board")

    # ── the two stores are actually fetched ───────────────────────────────────────────────────
    def test_rwMade_CONTENTS_are_fetched_not_only_counted(self):
        """`rwMade` was a COUNT for its whole life — countable, never copyable."""
        self.assertRegex(
            SRC, r"raw\('d2r_rwMade'\)\s*;\s*if\s*\(_rmf",
            "nothing fetches the CONTENTS of d2r_rwMade. The pre-existing `var rwMade=` is "
            "Object.keys(m).length — a count. His 99 runewords could be counted and never copied, "
            "which is exactly how they stayed out of 60 consecutive backups."
        )
        self.assertIn("rwMadeFull:(dump?rwFull:null)", SRC,
                      "the fetched contents are never emitted, so the fetch is dead code")

    def test_both_stores_reach_the_BACKED_UP_ledger(self):
        blk = _between(SRC, 'led = dict(got.get("sample") or {})', "_TRUNC")
        self.assertIsNotNone(blk, "could not read the block that assembles the backed-up ledger")
        self.assertIn('led["gameFound"] = got["gameFound"]', blk,
                      "gameFound is returned in full by the board and STILL not folded into the "
                      "ledger being written — the plumbing half of this defect")
        self.assertIn('led["rwMade"] = got["rwMadeFull"]', blk,
                      "the fetched rwMade contents never reach the file")

    # ── the file says whose ledgers it holds ──────────────────────────────────────────────────
    def test_the_snapshot_records_its_ROUTE(self):
        blk = _between(SRC, 'json.dump({"takenAt": stamp', "ensure_ascii=False)")
        self.assertIsNotNone(blk, "could not read the snapshot write")
        self.assertIn(
            '"route": got.get("route")', blk,
            "the snapshot records no route. restore_ledger.py restores into whatever board is "
            "showing and picks a file by heuristic, so a snapshot of one profile could be restored "
            "into another and nothing in the file would contradict it. board_ownership ALREADY "
            "fetches the route — not recording it is dropping it on the floor."
        )

    # ── ⚠ THE LOAD-BEARING LAW ────────────────────────────────────────────────────────────────
    def test_gameFound_is_NOT_graded_for_truncation(self):
        """A check that cannot fail is worse than no check, because it reads as coverage.

        Truncation is graded by comparing a copy against a count the BOARD reports independently.
        `counts.runewordsMade` is such a count. There is none for gameFound, so the only available
        comparison is the copy against its own length — circular by construction.
        """
        blk = _between(SRC, "_TRUNC = (", "for k, _ck in _TRUNC:")
        self.assertIsNotNone(blk, "the truncation table is gone")
        self.assertNotIn(
            "gameFound", blk,
            "gameFound is in the truncation table. The board publishes no independent count for "
            "it, so it would be compared against its own length and could never fail — coverage "
            "in appearance only. [[unknown-stays-unknown]]"
        )
        self.assertIn('("rwMade", "runewordsMade")', blk,
                      "rwMade is not graded against counts.runewordsMade, which the board DOES "
                      "report independently — so the one new store that CAN be checked is not")

    def test_an_absent_count_is_skipped_not_treated_as_zero(self):
        blk = _between(SRC, "for k, _ck in _TRUNC:", "if not force and")
        self.assertIsNotNone(blk, "could not read the truncation loop")
        self.assertRegex(
            blk, r"if\s+_want\s+is\s+None\s*:\s*\n\s*continue",
            "a missing count is not skipped. `int(None or 0)` is 0 and `n < 0` never fires, so an "
            "unanswerable store would pass silently as though it had been checked."
        )

    # ── the refusals that make the loop trustworthy must not have moved ───────────────────────
    def test_the_EMPTINESS_refusal_still_counts_only_the_original_three(self):
        """⚠ A board can honestly hold zero runewords. Folding the new stores into the emptiness
        total would let a TRUE state refuse every snapshot forever — a fact turned into an outage.
        """
        m = re.search(r'total = sum\(int\(counts\.get\(k\) or 0\) for k in \(([^)]*)\)\)', SRC)
        self.assertIsNotNone(m, "the emptiness total is gone")
        got = m.group(1)
        for bad in ("rwMade", "gameFound", "runewordsMade"):
            self.assertNotIn(bad, got,
                             "%s joined the EMPTINESS total. Zero runewords is a legitimate board "
                             "state, and refusing every snapshot over it converts a true reading "
                             "into a permanent backup outage." % bad)

    def test_the_truncation_refusal_still_refuses(self):
        self.assertIn("a partial ledger is not a backup", SRC,
                      "the truncation refusal is gone — a short read could overwrite a good backup")


if __name__ == "__main__":
    unittest.main(verbosity=2)
