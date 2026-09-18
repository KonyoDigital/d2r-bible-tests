# -*- coding: utf-8 -*-
"""v3303 (#57) — ONLY NEW FILM BUYS A PAID READ. A SHRINKING REEL BUYS NOTHING.

`_chron_reel_owes_a_read` states its own contract in its docstring:

    "re-owe the moment the reel GROWS, because new frames are new evidence and THAT IS THE ONLY
     THING that makes a re-read worth paying for."

The code disagreed with it, in two places at once:

    if len(_ff) != _at:  return True      # `!=` includes SHRINKAGE
    return _old < _at                     # a look-era frame GONE, i.e. deletion

So a PURE PRUNE — frames deleted, nothing captured — bought a paid read of a reel that now holds
LESS film than when it was last read. It can only find less than last time. That is his money,
spent to re-confirm a smaller version of an answer already recorded.

⚠ v3298 (mine) did not introduce this and did not fix it; it made the second branch explicitly
deletion-triggered while correcting a different defect. The contradiction has stood for versions.

THE FIX IS ONE RULE, and it subsumes both branches without weakening either:

    new film = (frames now) - (look-era frames still present)          re-owe iff new > 0

⚠⚠ THIS LAW IS BEHAVIOURAL AND BUILDS ITS OWN TREE. The function reads a real directory, so a
source-reading guard would pin the expression rather than the behaviour, and a guard that used his
live tv/frames/hist would pass on his Mac and be meaningless on a runner — the exact defect v3300
had to repair. Every case here drives a temp reel through the real code path.
[[regression-guard]] §3 [[test-venue]] [[unknown-stays-unknown]]
"""
import io
import os
import shutil
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()


def _frame(path, when):
    with io.open(path, "wb") as fh:
        fh.write(b"\xff\xd8\xff\xe0" + b"0" * 32)
    os.utime(path, (when, when))


class TestNewFilmBuysAReadNotASmallerReel(unittest.TestCase):

    def setUp(self):
        import unittest.mock as mock
        import control_app as ca
        self.ca, self.mock = ca, mock
        self.root = tempfile.mkdtemp(prefix="reowe_")
        self.addCleanup(shutil.rmtree, self.root, True)

    def _drive(self, look_era, extra_new, deleted):
        """Build a reel as it stood AT THE LOOK, then prune/capture, and ask if it owes a read."""
        rid = "reel_x"
        d = os.path.join(self.root, rid)
        os.makedirs(d)
        at = look_era
        base = time.time() - 600.0
        made = []
        for i in range(at):
            p = os.path.join(d, "f_%d.jpg" % (1780000000000 + i))
            _frame(p, base + i * 0.001)
            made.append(p)
        # the look's stamp: taken AFTER the look-era frames exist
        os.utime(d, (base + 10.0, base + 10.0))
        dm = os.stat(d).st_mtime

        for p in made[:deleted]:
            os.remove(p)
        for k in range(extra_new):
            _frame(os.path.join(d, "f_%d.jpg" % (1790000000000 + k)), dm + 60.0 + k)
        if deleted or extra_new:
            os.utime(d, (dm + 120.0, dm + 120.0))   # any add/remove moves the dir

        mem = {rid: {"looked": True, "framesAtLook": at, "dirMtimeAtLook": dm, "pages": 0}}
        with self.mock.patch.dict(os.environ, {"TV_HIST": self.root}):
            return self.ca._chron_reel_owes_a_read(rid, mem=mem)

    def test_a_reel_that_did_not_move_owes_nothing(self):
        self.assertFalse(self._drive(look_era=10, extra_new=0, deleted=0),
                         "a reel nobody touched since the look was re-owed — every freshly read "
                         "reel would be bought again immediately. [[REG-1111]]")

    def test_new_frames_buy_a_read(self):
        self.assertTrue(self._drive(look_era=10, extra_new=3, deleted=0),
                        "three new frames landed and the reel does NOT owe a read. New film is "
                        "the only new evidence there is; refusing it means the sweep never "
                        "revisits a growing reel.")

    def test_a_PURE_PRUNE_buys_NOTHING(self):
        """⚠⚠ THE ONE THIS LAW EXISTS FOR — and the one row the fix changes."""
        self.assertFalse(
            self._drive(look_era=10, extra_new=0, deleted=3),
            "frames were DELETED and nothing was captured, and the reel was re-owed. A paid read "
            "of a reel holding LESS film than when it was last read can only find less than the "
            "answer already recorded — it is his money spent to re-confirm a smaller version of "
            "what the ledger already says. The function's own docstring: new frames are 'THE ONLY "
            "THING that makes a re-read worth paying for'.")

    def test_prune_then_capture_under_a_STABLE_count_still_buys_a_read(self):
        """The case the strict dir-stamp exists for: count unchanged, film different."""
        self.assertTrue(
            self._drive(look_era=10, extra_new=3, deleted=3),
            "three frames were pruned and three captured, so the census reads 10 both times while "
            "the FILM has changed entirely — and the reel does not owe a read. Churn under a "
            "stable count is exactly what the membership comparison was built to catch. "
            "[[TestV2202]]")

    def test_a_net_shrink_that_still_gained_film_buys_a_read(self):
        """Shrinking overall is not the question; NEW is."""
        self.assertTrue(
            self._drive(look_era=10, extra_new=1, deleted=3),
            "one new frame landed while three were pruned. The reel is smaller, but there IS new "
            "evidence, and new evidence is what buys the read. A rule keyed on the total count "
            "going down would wrongly refuse this.")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "re-owing on a CHANGED census rather than NEW film buys a read of a pruned reel",
        "file": "tv/control_app.py",
        "find": "            return (len(_ff) - _old) > 0  # NEW film bought it; a smaller reel buys nothing",
        "replace": "            return len(_ff) != _at or _old < _at",
        "matches": 1,
    },
    {
        "why": "keying on the total count alone refuses a net shrink that nonetheless gained film",
        "file": "tv/control_app.py",
        "find": "            return (len(_ff) - _old) > 0  # NEW film bought it; a smaller reel buys nothing",
        "replace": "            return len(_ff) > _at",
        "matches": 1,
    },
]
