# -*- coding: utf-8 -*-
"""v2721 — THE HARNESS THAT PROVES THE DELETION GATE MUST ITSELF BE UNABLE TO DELETE.

`frame_release_wilson` attacks `frame_authority.seal_releases_frames` — the per-frame authority
that `frame_verdict` asks before letting any pixels go. A harness that exercises a deletion gate is
the last place a stray write belongs, so its inertness is asserted from its own SOURCE rather than
promised in a comment. This is the same shape `tv/test_prune_wilson.py` uses for prune_wilson, and
it exists for the same reason.

⚠ AND IT PINS THAT THE LOCK CANNOT PASS BY REFUSING EVERYTHING. A gate that says no to every input
is not a judgement, it is a wall — and it would score a perfect Wilson. Two of the eight attacks
MUST RELEASE (a declared examined-empty seal, and a fully covered one), so a wall fails this
harness. That is the difference between measuring a decision and measuring a reflex.
[[regression-guard]] [[feedback-blind-fixture-green-gate]]
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

import frame_release_wilson as FRW

SRC = os.path.join(HERE, "frame_release_wilson.py")


def _code():
    s = io.open(SRC, encoding="utf-8").read()
    s = re.sub(r'"""(?:.|\n)*?"""', " ", s)      # judge the CODE, not the prose about it
    return re.sub(r"(?m)#.*$", " ", s)


class FrameReleaseWilsonIsInert(unittest.TestCase):

    def test_it_cannot_delete_anything(self):
        code = _code()
        for bad in ("os.remove", "unlink", "rmtree", "shutil.move", "apply_plan",
                    "_prune_once", "_prune_loop", "TV_AUTO_PRUNE"):
            self.assertNotIn(
                bad, code,
                "frame_release_wilson references %r. A harness that exercises the gate before a "
                "deletion must not be able to perform one — the shape is the guarantee, not the "
                "comment." % bad)

    def test_it_never_writes_to_the_seal_store(self):
        code = _code()
        self.assertNotIn("sealed_sessions", code,
                         "the harness reads his real seal store. It must run on rows it builds in "
                         "memory, or it measures his data instead of the predicate")
        self.assertNotIn('open(', code.replace("io.open", ""),
                         "the harness opens a file; it should touch nothing on disk")

    def test_every_attack_is_a_DISTINCT_idea(self):
        """⚠ The A2 census counts `attacks`, and wilsonByAttack exists because 80 of
        printer.stream's 83 were two functions over 40 reels. Five spellings of one idea is ONE
        attack. This pins that no two declared attacks are the same input."""
        seen = []
        for name, row, must, why in FRW.ATTACKS:
            key = tuple(sorted((k, str(v)) for k, v in row.items()))
            self.assertNotIn(key, seen,
                             "attack %r is byte-identical to an earlier one — that is repetition "
                             "counted as breadth, which is the illusion wilsonByAttack exists to "
                             "refuse" % name)
            seen.append(key)
        self.assertGreaterEqual(len(FRW.ATTACKS), 6,
                                "too few distinct states to mean anything")

    def test_the_lock_CANNOT_pass_by_refusing_everything(self):
        """A wall scores a perfect Wilson and decides nothing."""
        must_release = [a for a in FRW.ATTACKS if a[2] is True]
        self.assertGreaterEqual(
            len(must_release), 2,
            "fewer than two attacks require a RELEASE. A gate that refuses every input would "
            "score 100%% here and prove nothing about judgement — the whole point is that it says "
            "yes when his ruling says yes")

    def test_it_refuses_to_bank_a_failing_run(self):
        """Evidence from a harness that failed its own attempts is worse than none."""
        code = _code()
        # ⚠ the window must clear the refusal MESSAGE between the guard and the return — a
        # {0,80} cut mid-sentence and failed on correct code. Anchor on both ends, not on a
        # guessed distance. [[source-window-shortcut]]
        self.assertRegex(code.replace("\n", " "), r"if ok != n:\s*.{0,220}?return 1",
                         "the harness would bank a run in which an attack was answered wrongly")

    def test_it_actually_passes_right_now(self):
        """Anti-vacuity: every law above is source-shaped, so one must EXECUTE."""
        n, ok, rows = FRW.run()
        self.assertEqual(ok, n, "the gate answered %d of %d states wrongly: %s"
                         % (n - ok, n, [r["attack"] for r in rows if not r["correct"]]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
