# -*- coding: utf-8 -*-
"""THE DRAIN MUST COVER EVERY FILE THE JOURNAL IS READ FROM, OR REFUSE TO RUN.

⚠⚠ THIS IS WHY THE RIVER COULD NOT DRAIN, AND IT WAS INVISIBLE FOR SIX VERSIONS. `load_journal`
has read a GENERATION RING since v779 — `.5 … .1` then the live file — while `journal_retention`
asked `tv_diablo.JOURNAL` and got the live file ALONE. So the planner judged the whole journal and
the applier rewrote one file of it. MEASURED on his tree:

    sessions.1.jsonl   7,103 rows   2,483 sessions   <- the applier never touched this
    sessions.jsonl     5,093 rows     357 sessions   <- the only file it rewrote

Every release against a session in the rotated half was a SILENT NO-OP that reported success.
`removedSessions: 324` looked like progress and 2,483 sessions were never reachable.
[[the-unjoined-end]] [[copy-drift]]

⚠ AND A PLAN IS A JUDGEMENT ABOUT A SET OF FILES. Applying it to a different set is how a correct
decision lands on the wrong rows — which is not hypothetical: on 2026-09-14 a plan computed over
the ring was applied to the live file alone, and the only reason nothing was lost is that the
backup was written and verified first. The plan now names the corpus it judged and the apply
refuses when that corpus moved.

⚠ THE BACKUP NAME MUST CARRY THE SOURCE. `sessions.%s.jsonl % stamp` is fine for ONE file and
silently collides the moment two ring generations are backed up in the same second — the second
copy lands on the first, and the earlier file has no backup while the log says it does.
"""
import ast
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import journal_retention as JR      # noqa: E402
import replay as RP                 # noqa: E402

EXTRACTED = JR.EXTRACTED


def _row(sid, t0, **kw):
    r = {"sessionId": sid, "t0": t0, "footageState": EXTRACTED, "footageWhy": "read and sealed"}
    r.update(kw)
    return r


class TestTheDrainCoversTheWholeJournalRing(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="ring-")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.live = os.path.join(self.d, "sessions.jsonl")
        self.rot = os.path.join(self.d, "sessions.1.jsonl")
        self._jr = RP.JOURNAL
        self._bd = JR.BACKUP_DIR
        self.addCleanup(lambda: setattr(RP, "JOURNAL", self._jr))
        self.addCleanup(lambda: setattr(JR, "BACKUP_DIR", self._bd))
        RP.JOURNAL = self.live
        JR.BACKUP_DIR = os.path.join(self.d, "backups")
        # 12 recent runs in the LIVE file so the "newest 8" hold is never what does the work,
        # and one old run in the ROTATED file — the half the applier could not reach.
        with io.open(self.live, "w", encoding="utf-8") as fh:
            for i in range(12):
                fh.write(json.dumps(_row("s_live_%02d" % i, 1_800_000_000_000 + i)) + "\n")
            fh.write(json.dumps(_row("s_old_live", 1_700_000_000_000)) + "\n")
        with io.open(self.rot, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(_row("s_rotated", 1_700_000_000_001)) + "\n")
            fh.write(json.dumps(_row("s_rotated", 1_700_000_000_002)) + "\n")

    def _ids(self, path):
        out = []
        for line in io.open(path, encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            out.append(str((json.loads(line) or {}).get("sessionId") or ""))
        return out

    # ── 1. the reader exposes the ring once, and uses it ──────────────────────────────────────
    def test_load_journal_asks_journal_paths(self):
        with io.open(os.path.join(HERE, "replay.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "load_journal"), None)
        self.assertIsNotNone(fn, "load_journal is gone")
        calls = [n for n in ast.walk(fn)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                 and n.func.id == "journal_paths"]
        ranges = [n for n in ast.walk(fn)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                  and n.func.id == "range"]
        print("   load_journal: %d journal_paths() call(s) · %d inline range() ring(s)"
              % (len(calls), len(ranges)))
        self.assertEqual(len(calls), 1, "load_journal must ask journal_paths() exactly once")
        self.assertEqual(len(ranges), 0,
                         "load_journal builds the ring inline again — two spellings of 'the "
                         "journal' is the drift this function exists to remove")

    # ── 2. the drainer delegates to the reader ────────────────────────────────────────────────
    def test_the_drainer_delegates_to_the_reader(self):
        with io.open(os.path.join(HERE, "journal_retention.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "_journal_paths"), None)
        self.assertIsNotNone(fn, "_journal_paths is gone")
        calls = [n for n in ast.walk(fn)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "journal_paths"]
        print("   _journal_paths: %d delegate call(s)" % len(calls))
        self.assertEqual(len(calls), 1,
                         "_journal_paths must ask replay.journal_paths(), not re-derive the ring")

    # ── 3. THE DEFECT: a row in the ROTATED half must actually go ─────────────────────────────
    def test_a_released_row_in_the_rotated_half_is_removed(self):
        rows = [_row(sid, t0) for sid, t0 in
                [("s_rotated", 1_700_000_000_001), ("s_old_live", 1_700_000_000_000)]
                ] + [_row("s_live_%02d" % i, 1_800_000_000_000 + i) for i in range(12)]
        p = JR.plan(rows, hist_dir=os.path.join(self.d, "no-frames"))
        rel = {r["sessionId"] for r in p["release"]}
        self.assertIn("s_rotated", rel, "the fixture did not release the rotated run, so this "
                                        "test would prove nothing")
        r = JR.apply_plan(p, yes=True)
        print("   apply over the ring: ok=%s removedRows=%s files=%s"
              % (r.get("ok"), r.get("removedRows"), len(r.get("rewrote") or [])))
        self.assertTrue(r.get("ok"), r.get("why"))
        self.assertNotIn("s_rotated", self._ids(self.rot),
                         "the released session still sits in sessions.1.jsonl — the applier "
                         "rewrote the live file only, which is the silent no-op that kept 2,483 "
                         "of his sessions permanently undrainable")
        self.assertEqual(len(r.get("rewrote") or []), 2,
                         "only %d file(s) were rewritten" % len(r.get("rewrote") or []))

    # ── 4. a corpus that MOVED is refused ─────────────────────────────────────────────────────
    def test_a_moved_corpus_is_refused(self):
        rows = [_row("s_rotated", 1_700_000_000_001)] + \
               [_row("s_live_%02d" % i, 1_800_000_000_000 + i) for i in range(12)]
        p = JR.plan(rows, hist_dir=os.path.join(self.d, "no-frames"))
        self.assertTrue(p["release"], "fixture released nothing")
        with io.open(self.live, "a", encoding="utf-8") as fh:      # the journal moves underneath
            fh.write(json.dumps(_row("s_new_arrival", 1_900_000_000_000)) + "\n")
        r = JR.apply_plan(p, yes=True)
        print("   moved corpus refused: %s" % (not r.get("ok")))
        self.assertFalse(r.get("ok"),
                         "a plan was applied to a journal that changed after it was judged")
        self.assertIn("MOVED", r.get("why", ""))

    # ── 5. two ring backups in one second must not collide ───────────────────────────────────
    def test_ring_backups_do_not_collide(self):
        a, na = JR.backup(self.live, stamp="SAME")
        b, nb = JR.backup(self.rot, stamp="SAME")
        print("   backups: %s · %s" % (os.path.basename(a or ""), os.path.basename(b or "")))
        self.assertTrue(a and b, "a backup did not write: %r %r" % (na, nb))
        self.assertNotEqual(a, b,
                            "both ring files backed up to the SAME path — the second overwrote "
                            "the first, so one generation has no backup while the log says it does")
        self.assertEqual(na, 13)
        self.assertEqual(nb, 2)


    # ── 6. a generation drained to NOTHING must not block every later drain ───────────────────
    def test_an_empty_generation_does_not_block_the_drain(self):
        """⚠⚠ THE RIVER-CANNOT-DRAIN BUG, ONE LAYER DOWN, FOUND BY THE SECOND EYE ON v3106.
        `backup()` refused any 0-row copy — the right guard for "we failed to copy a file that HAD
        rows", the wrong one for a ring generation legitimately drained to nothing. Once
        `sessions.1.jsonl` holds only doomed rows and is rewritten empty, EVERY later apply dies at
        the backup step, before the live file is touched, and the doomed live rows stay forever."""
        io.open(self.rot, "w", encoding="utf-8").close()          # a generation drained to zero
        rows = [_row("s_old_live", 1_700_000_000_000)] + \
               [_row("s_live_%02d" % i, 1_800_000_000_000 + i) for i in range(12)]
        p = JR.plan(rows, hist_dir=os.path.join(self.d, "no-frames"))
        self.assertIn("s_old_live", {r["sessionId"] for r in p["release"]},
                      "fixture released nothing, so this proves nothing")
        r = JR.apply_plan(p, yes=True)
        print("   with an EMPTY generation in the ring: ok=%s why=%r"
              % (r.get("ok"), (r.get("why") or "")[:70]))
        self.assertTrue(r.get("ok"),
                        "an empty ring generation blocked the whole drain: %s" % r.get("why"))
        self.assertNotIn("s_old_live", self._ids(self.live))

    def test_a_backup_of_an_empty_file_is_a_backup(self):
        """The honest question is whether the COPY matches the SOURCE, not whether it is non-zero."""
        io.open(self.rot, "w", encoding="utf-8").close()
        where, n = JR.backup(self.rot, stamp="EMPTY")
        print("   backup of an empty source -> %r rows=%r" % (bool(where), n))
        self.assertTrue(where, "backing up a legitimately empty file was refused: %r" % n)
        self.assertEqual(n, 0)

    # ── 7. the rewrite re-checks its own file, because the ring can rotate mid-apply ──────────
    def test_the_rewrite_rechecks_each_file(self):
        """⚠ STRUCTURAL, AND SAID SO. `tv_diablo._journal_write` rotates with `os.replace` and no
        lock, so a rotation landing between the corpus snapshot and a rewrite leaves this editing
        the OLD paths while the doomed rows moved a generation along — the eye reproduced
        `ok: True` with the doomed generation still in the ring. A test cannot land a rotation
        between two statements without a hook the writer does not offer, so this asserts the
        re-check EXISTS inside the rewrite loop rather than pretending to race it.
        [[unknown-stays-unknown]]"""
        with io.open(os.path.join(HERE, "journal_retention.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "apply_plan"), None)
        self.assertIsNotNone(fn, "apply_plan is gone")
        loops = [n for n in ast.walk(fn) if isinstance(n, ast.For)]
        rewrite = [l for l in loops
                   if any(isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)
                          and x.func.attr == "replace" for x in ast.walk(l))]
        self.assertTrue(rewrite, "no loop in apply_plan performs the atomic replace")
        inner = rewrite[0]
        # ⚠⚠ THE GUARD'S **TEST**, NOT MERELY THE NAME. A first cut asked whether `_want` appeared
        # anywhere in the loop, and the red-proof that replaces the condition with `if False:`
        # came back BLIND — the dead branch still MENTIONS `_want` in its body. A check that a
        # name is present cannot tell reachable code from unreachable code.
        # [[sabotage-is-usually-the-wrong-one]] [[regression-guard]]
        # ⚠ THE OUTER GUARD, NAMED BY BOTH ITS OPERANDS. The block holds TWO ifs testing `_want`
        # — the entry guard and the mismatch check inside it — so a sabotage that kills only the
        # entry guard still leaves one, and the first two cuts of this assertion came back BLIND
        # for exactly that reason. The entry guard is the one that tests `journal_path` too.
        def _tests(n, *names):
            got = {x.id for x in ast.walk(n.test) if isinstance(x, ast.Name)}
            return all(nm in got for nm in names)
        guards = [n for n in ast.walk(inner) if isinstance(n, ast.If)
                  and _tests(n, "_want", "journal_path")]
        print("   rewrite loop: %d entry guard(s) testing _want AND journal_path" % len(guards))
        self.assertEqual(len(guards), 1,
                         "the rewrite loop has %d entry guard(s) re-checking its file against the "
                         "plan — a rotation between the backup and the write is then reported as "
                         "success" % len(guards))

RED_PROOF = [
    {
        "why": "the applier goes back to rewriting the live file only, so every release against a "
               "session in the rotated half is a silent no-op that reports success — 2,483 of his "
               "2,840 sessions permanently undrainable",
        "file": "journal_retention.py",
        "find": "    targets = [journal_path] if journal_path else _journal_paths()",
        "replace": "    targets = [journal_path] if journal_path else [_journal_path()]",
        "matches": 1,
    },
    {
        "why": "the corpus guard is removed, so a plan judged over one set of files is applied to "
               "another — a correct decision landing on the wrong rows",
        "file": "journal_retention.py",
        "find": "        if want != have:",
        "replace": "        if False:",
        "matches": 1,
    },
    {
        "why": "the backup name stops carrying its source, so two ring generations backed up in "
               "the same second collide and one is left with no backup at all",
        "file": "journal_retention.py",
        "find": '    dst = os.path.join(BACKUP_DIR, "%s.%s" % (os.path.basename(src), stamp))',
        "replace": '    dst = os.path.join(BACKUP_DIR, "sessions.%s.jsonl" % stamp)',
        "matches": 1,
    },
    {
        "why": "an empty ring generation is treated as a FAILED backup again, so the moment one "
               "generation drains to nothing every later apply dies at the backup step and the "
               "doomed live rows stay forever — the river-cannot-drain bug one layer down",
        "file": "journal_retention.py",
        "find": "    if n != src_n:",
        "replace": "    if n == 0:",
        "matches": 1,
    },
    {
        "why": "the rewrite stops re-checking its own file, so a ring rotation landing between the "
               "backup and the write is reported as success while the doomed generation is still "
               "in the ring",
        "file": "journal_retention.py",
        "find": "        if not journal_path and t in _want:",
        "replace": "        if False:",
        "matches": 1,
    },
    {
        "why": "the reader builds the ring inline again, so the two ends can drift back apart "
               "silently — which is the original defect",
        "file": "replay.py",
        "find": "    paths = journal_paths(path)",
        "replace": ("    _root, _ext = os.path.splitext(JOURNAL)\n"
                    "    paths = [path] if path is not None else "
                    "[_root + '.%d' % g + _ext for g in range(5, 0, -1)] + [JOURNAL]"),
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
