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
