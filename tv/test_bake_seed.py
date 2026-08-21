"""v1947 — THE BAKER MAY NEVER LOSE A NAME, AND MAY NEVER WRITE WITHOUT BEING ASKED.

tv/bake_seed.py rebuilds the shipped _GRAIL_SEED/_SET_SEED from his real board. The seed is his
HISTORY — the record a fresh profile inherits — so the interesting tests here are not "does it add
the new names". They are the four refusals:

  1. REPORT ONLY unless --write.
  2. NEVER SHRINK — every name already shipped survives, whatever the board says today.
  3. NEVER SEED A PIECE THE GAME SAYS HE LACKS (_SET_MISSING), or the boot repair immediately
     removes what the seed just added and the two fight forever.
  4. NEVER SEED A NAME A BOOT ONE-SHOT OWNS — v1692/v1693 apply those with their own dated
     provenance and v1693 refuses a second witness in as many words.

⚠ THE FIXTURE BUILDS ITS OWN SQLITE STORE AND NEVER LOOKS AT HIS. Reading his board means copying
three sqlite files; copying them into ONE directory lets the small ones overwrite the board and the
reader then reports zero — measured, and the reason find_board_store() tests for d2r_foundLog rather
than trusting size alone.
"""
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
import bake_seed  # noqa: E402

_console_safe_enable()   # v1947 — this suite prints non-ASCII too


def _mkstore(root, name, found_log, set_pieces, extra_size=0):
    d = os.path.join(root, name, name, "LocalStorage")
    os.makedirs(d, exist_ok=True)
    db = os.path.join(d, "localstorage.sqlite3")
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE ItemTable (key TEXT UNIQUE ON CONFLICT REPLACE, value BLOB)")
    for k, v in (("d2r_foundLog", json.dumps(found_log)),
                 ("d2r_setPieces", json.dumps(set_pieces))):
        con.execute("INSERT INTO ItemTable VALUES (?,?)", (k, v.encode("utf-16-le")))
    if extra_size:
        con.execute("INSERT INTO ItemTable VALUES (?,?)", ("pad", ("x" * extra_size).encode("utf-16-le")))
    con.commit(); con.close()
    return db


class TestTheBakerRefuses(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="bake_")
        self.bible = bake_seed.BIBLE
        self.backup = os.path.join(self.root, "bible.backup")
        shutil.copy(self.bible, self.backup)

    def tearDown(self):
        shutil.copy(self.backup, self.bible)     # the bible is never left edited by a test
        shutil.rmtree(self.root, ignore_errors=True)

    def _src(self):
        return open(self.bible, encoding="utf-8").read()

    def test_it_finds_the_store_that_HAS_the_board_not_the_biggest(self):
        """A decoy that is LARGER but carries no ledger must not win — that is the bug that made a
        real read report setPieces=0."""
        _mkstore(self.root, "a" * 8, {"Shako": "x"}, ["Shako"])
        _mkstore(self.root, "b" * 8, {}, [], extra_size=200000)
        con = sqlite3.connect(_mkstore(self.root, "c" * 8, {}, []))
        con.execute("DELETE FROM ItemTable WHERE key='d2r_foundLog'"); con.commit(); con.close()
        got = bake_seed.find_board_store(self.root)
        self.assertIsNotNone(got, "found no store at all")
        self.assertIn("a" * 8, got, "picked a store with no d2r_foundLog in it")

    def test_report_only_by_default(self):
        _mkstore(self.root, "d" * 8, {"Totally New Unique": "Jan 1, 2026 · 01:00"}, [])
        before = self._src()
        rc = bake_seed.bake(write=False, root=self.root)
        self.assertEqual(self._src(), before, "a REPORT wrote to bible.html")
        self.assertEqual(rc, 1, "drift must report a non-zero, non-error status")

    def test_it_never_shrinks_the_seed(self):
        """The one failure that is not re-derivable. An EMPTY board must still leave every shipped
        name in place."""
        _mkstore(self.root, "e" * 8, {}, [])
        import re
        before = len(json.loads(re.search(r"const _GRAIL_SEED = (\{.*?\});", self._src(), re.S).group(1)))
        bake_seed.bake(write=True, root=self.root)
        after_src = self._src()
        after = len(json.loads(re.search(r"const _GRAIL_SEED = (\{.*?\});", after_src, re.S).group(1)))
        self.assertGreaterEqual(after, before, "the bake DROPPED shipped names on an empty board")

    def test_it_refuses_a_piece_the_game_says_he_lacks(self):
        src = self._src()
        missing = sorted(bake_seed.game_says_missing(src))
        self.assertTrue(missing, "the game's Remaining list did not load — this test proves nothing")
        target = missing[0]
        _mkstore(self.root, "f" * 8, {target: "Jan 1, 2026 · 01:00"}, [target])
        bake_seed.bake(write=True, root=self.root)
        import re
        seed = json.loads(re.search(r"const _SET_SEED = (\{.*?\});", self._src(), re.S).group(1))
        self.assertNotIn(target, seed,
                         "seeded %r, which the game's own Remaining page lists as missing — the "
                         "boot repair would strip it again on every load" % target)

    def test_it_refuses_a_name_a_one_shot_owns(self):
        src = self._src()
        owned = bake_seed.one_shot_owned(src)
        self.assertIn("The Diggler", owned,
                      "the one-shot scan no longer sees the names it must protect")
        import re
        grail_before = json.loads(re.search(r"const _GRAIL_SEED = (\{.*?\});", src, re.S).group(1))
        target = next((n for n in owned if n not in grail_before), None)
        self.assertIsNotNone(target, "every one-shot name is already seeded — nothing to prove")
        _mkstore(self.root, "g" * 8, {target: "Jan 1, 2026 · 01:00"}, [])
        bake_seed.bake(write=True, root=self.root)
        grail = json.loads(re.search(r"const _GRAIL_SEED = (\{.*?\});", self._src(), re.S).group(1))
        self.assertNotIn(target, grail,
                         "seeded %r, which a boot one-shot applies with its own provenance" % target)

    def test_no_store_is_an_honest_failure_not_a_silent_zero(self):
        rc = bake_seed.bake(write=True, root=os.path.join(self.root, "nothing-here"))
        self.assertEqual(rc, 2, "a missing store must report, not bake an empty seed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
