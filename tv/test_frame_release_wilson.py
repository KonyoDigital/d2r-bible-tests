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
        """⚠⚠ THIS LAW USED TO BAN `sealed_sessions`, WHICH IS A READER, AND IT WAS RED ON CI FOR
        TWO SHIPS (v2723 and v2724, same failure both times).

        It was CORRECT when written: the harness fed hand-built dictionaries to a pure predicate
        and touched nothing of his. It became wrong when `live()` was added ON PURPOSE, to run the
        gate against his real 31 seals — `frame_authority.sealed_sessions()` is
        `def sealed_sessions(root=None)` at frame_authority.py:143, a read, and live()'s own first
        line says "Reads; writes nothing."

        That addition was not an accident to be reverted. Measured 2026-09-06: four locks sit at
        confluence exactly 1.00, meaning every attack banked against them is the same KIND, and the
        hard bar reads confluence. No quantity of sabotage moves a kinds gap — only live, ci or
        cross-family evidence does. A law forbidding the harness to read his data forbids the only
        mechanism that closes them. [[regression-guard]] GATE_MOVES_WITH_PRODUCT.

        So the property is kept and stated properly: this harness must not WRITE. Reading is how it
        witnesses; writing beside a deletion gate is what must be impossible.
        """
        code = _code()
        #: every way this file could put a byte on disk. Named individually, because "does not
        #: write" is a claim about primitives and not about intent.
        WRITERS = ("json.dump", "json.dumps(", ".write(", "os.replace", "os.rename",
                   "shutil.copy", "shutil.move", "_vault_swept_save", "vault_ledger_save",
                   "SEAL_STORE")
        for bad in WRITERS:
            self.assertNotIn(
                bad, code,
                "frame_release_wilson references %r. It runs beside the gate that decides whether "
                "his footage may be released, and a harness that can write is a harness that can "
                "change the evidence it is measuring. The shape is the guarantee, not the comment."
                % bad
            )
        self.assertNotIn('open(', code.replace("io.open", ""),
                         "the harness opens a file; it should touch nothing on disk")

    def test_its_only_reach_into_his_data_is_a_declared_READ(self):
        """⚠ The read is allowed, so it must be a read AND THE ONLY ONE. An allowance nobody
        bounds is how "it may read one store" becomes "it may reach anywhere"."""
        import ast
        code = _code()
        tree = ast.parse(code)
        reached = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if node.value.id == "FA":
                    reached.add(node.attr)
        #: what the harness is permitted to ask frame_authority for. All readers/predicates.
        ALLOWED = {"sealed_sessions", "seal_releases_frames", "seal_verdict",
                   "seal_covers_extraction", "EXTRACTION_CONTRACT", "frame_verdict"}
        stray = sorted(reached - ALLOWED)
        self.assertEqual(
            [], stray,
            "the harness calls frame_authority.%s, which is not in its declared read set. Each name "
            "here must be checked to be a READ before it is added: the live pass exists to witness "
            "his seals, not to act on them." % stray
        )
        self.assertIn(
            "sealed_sessions", reached,
            "the harness no longer reads his seals at all, so `live()` cannot be producing "
            "live-kind evidence. If that read was removed, the `live` bank in main() is now "
            "banking a witness that never looked — which is worse than not banking it. "
            "[[feedback-silence-is-not-evidence]]"
        )

    def test_every_attack_is_a_DISTINCT_idea(self):
        """⚠ The A2 census counts `attacks`, and wilsonByAttack exists because 80 of
        printer.stream's 83 were two functions over 40 reels. Five spellings of one idea is ONE
        attack. This pins that no two declared attacks are the same input."""
        seen = []
        for name, row, must, why in FRW.ATTACKS:
            # ⚠ a non-dict row is a legitimate attack (a corrupt store hands the gate anything),
            # so the identity key must survive one. `row.items()` raised on the None case — the
            # test could not describe an input the harness deliberately includes.
            key = (tuple(sorted((k, str(v)) for k, v in row.items()))
                   if isinstance(row, dict) else ("<non-dict>", repr(row)))
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
