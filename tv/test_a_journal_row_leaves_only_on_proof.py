# -*- coding: utf-8 -*-
"""A JOURNAL ROW MAY LEAVE ONLY ON A PROOF OF EXTRACTION, AND THE PLANNER MAY NEVER WRITE.

Konyo asked for the whole river to end in tombstone and then deletion — *"after being extracted"*.
That last clause is the whole law. A row is his record of a night he played; there is no un-delete.

MEASURED 2026-09-13. The REEL river is already finished: 20 reels on disk, `ROUTED 20` — which
reel_router's own note calls "the REAL tombstone" — and `TOMBSTONE 0`, meaning none have LEFT THE
DISK. That zero is CORRECT, because the 20 are 8 he keeps + 9 the suite pins + 3 still held. His
shelf nevertheless shows 419 rows, because the shelf lists JOURNAL sessions and a row outlives its
film.

    2,893 journaled · 2,474 hidden as empty · 419 shown · 20 reels
    plan(): 446 releasable · 2,325 held on "unknown" · 89 no id · 15 pinned · 8 recent · 4 with film

⚠⚠ "UNKNOWN" IS NOT "EXTRACTED". 2,325 rows say `footageState: unknown` — no film and no retention
record. That is an absence of evidence in BOTH directions, and treating it as permission would
delete his history on the strength of a blank. Only `retired` counts, because the retention lane
produces that state itself after the film has given up its information.
[[unknown-stays-unknown]]

⚠⚠ AND THE PLANNER WRITES NOTHING. `reel_retention.plan()` says of itself "what may go, oldest
first, and WHY every other reel stays. Writes nothing." This mirrors it exactly. The apply half is
a separate decision and it is HIS.
"""
import ast
import io
import os
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))

#: a row shaped like /api/sessions, one per case the law names
# ⚠⚠ v3113 — THE AMNESTY BOUNDARY IS PINNED HERE, AND THAT IS THE POINT OF THIS BLOCK.
# v3112 gave `plan()` a waiver for runs that started BEFORE the retention ledger's first entry.
# These fixtures used `t0=1000`, which is before ANY real deletion stamp — so on his Mac, where
# `reel_tombstones.json` exists, the waiver fired and every `unknown`/`none`/`""` row was released
# and this law went RED. On CI the ledger is GITIGNORED and absent, `_ledger_began` returns None,
# the waiver is off, and the very same test went GREEN.
#
# **CI would have certified a law that production no longer follows.** A verdict that depends on
# which machine ran it is not a verdict, and an absent fixture file is the quietest way to get one.
# Both halves are fixed: the fixtures now sit AFTER the boundary, so they test the rule rather than
# the waiver, and the boundary itself is patched to a constant so no venue can move it.
# [[feedback-blind-fixture-green-gate]] [[regression-guard]]
BEGAN = 1_787_604_588_927          # the real ledger's first deletion, frozen for fixture arithmetic


def _row(sid, t0=1_700_000_000_000, state="retired", **kw):
    r = {"sessionId": sid, "t0": t0, "footageState": state, "footageWhy": "x"}
    r.update(kw)
    return r


class TestAJournalRowLeavesOnlyOnProof(unittest.TestCase):

    def setUp(self):
        # the venue may not decide the verdict: freeze the boundary for every case below
        # ⚠ imported HERE because this file imports the planner inside its test methods, not at
        # module scope — a setUp that assumed otherwise raised UnboundLocalError on all five.
        import journal_retention as JR
        self._began = JR._ledger_began
        self.addCleanup(lambda _m=JR, _v=self._began: setattr(_m, "_ledger_began", _v))
        JR._ledger_began = lambda: (BEGAN, None)

        import journal_retention as JR
        self.JR = JR

    def test_only_a_retired_row_is_releasable(self):
        rows = [_row("s_old_%d" % i, t0=BEGAN + 1000 + i, state=s)
                for i, s in enumerate(("retired", "unknown", "none", "", "RETIRED"))]
        # 8 newer rows so none of the above are protected by the recent window
        rows += [_row("s_new_%d" % i, t0=BEGAN + 9_000_000 + i) for i in range(8)]
        p = self.JR.plan(rows, hist_dir=os.path.join(HERE, "__no_such_dir__"))
        got = {r["sessionId"] for r in p["release"]}
        print("releasable: %s" % sorted(got))
        self.assertIn("s_old_0", got, "a `retired` row carries the system's own proof and may go")
        for bad, label in (("s_old_1", "unknown"), ("s_old_2", "none"), ("s_old_3", "empty")):
            self.assertNotIn(bad, got,
                             "a %r row was released — no film is NOT the same fact as extracted, "
                             "and an absence of evidence is not a proof" % label)
        self.assertNotIn("s_old_4", got,
                         "state matching must not be case-folded into a pass; 'RETIRED' is not the "
                         "value the retention lane writes")

    def test_the_newest_are_never_releasable_whatever_their_state(self):
        rows = [_row("s_%d" % i, t0=1_000_000 + i) for i in range(20)]   # all retired
        p = self.JR.plan(rows, hist_dir=os.path.join(HERE, "__no_such_dir__"))
        got = {r["sessionId"] for r in p["release"]}
        keep_n = p["keepRecent"]
        newest = {"s_%d" % i for i in range(20 - keep_n, 20)}
        print("keepRecent=%d · newest held: %d" % (keep_n, len(newest & {k['sessionId'] for k in p['keep']})))
        for sid in newest:
            self.assertNotIn(sid, got, "%s is inside the newest %d and must never be released" % (sid, keep_n))

    def test_an_undateable_row_is_held_not_guessed(self):
        rows = [_row("s_a", t0=None), _row("s_b"), _row("", t0=5)]
        rows += [_row("s_n%d" % i, t0=9_000_000 + i) for i in range(8)]
        p = self.JR.plan(rows, hist_dir=os.path.join(HERE, "__no_such_dir__"))
        got = {r["sessionId"] for r in p["release"]}
        self.assertNotIn("s_a", got, "a row with no t0 cannot be ordered, so 'newest 8' is meaningless")
        self.assertNotIn("", got, "a row with no session id can be neither dated nor matched to film")
        print("undateable and id-less rows both held")

    def test_the_keep_floor_is_imported_not_retyped(self):
        """Two copies of a retention floor is how the halves of one river disagree."""
        import reel_retention as RR
        self.assertEqual(self.JR.KEEP_RECENT, RR.KEEP_RECENT,
                         "the journal planner keeps a different number of runs than the reel "
                         "planner — one river, two floors")
        src = io.open(os.path.join(HERE, "journal_retention.py"), encoding="utf-8").read()
        code = "\n".join(ln.split("#", 1)[0] for ln in src.splitlines())
        self.assertIn("from reel_retention import KEEP_RECENT", code,
                      "the floor must be imported from the reel planner, never re-typed")
        print("KEEP_RECENT imported, both planners agree: %d" % self.JR.KEEP_RECENT)

    def test_the_planner_cannot_write_anything(self):
        """PARSED, not trusted: no open-for-write, no remove, no rename, anywhere in the module."""
        src = io.open(os.path.join(HERE, "journal_retention.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        banned = {"remove", "unlink", "rmtree", "rename", "replace", "rmdir", "truncate"}
        hits = []
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                nm = getattr(n.func, "attr", getattr(n.func, "id", None))
                if nm in banned:
                    hits.append("%s (line %d)" % (nm, n.lineno))
                if nm == "open":
                    for a in list(n.args[1:2]) + [k.value for k in n.keywords if k.arg == "mode"]:
                        if isinstance(a, ast.Constant) and isinstance(a.value, str) and \
                                any(c in a.value for c in "wax+"):
                            hits.append("open(mode=%r) line %d" % (a.value, n.lineno))
        print("write-capable calls found: %s" % (hits or "none"))
        self.assertEqual(hits, [],
                         "the journal PLANNER can write. It exists to classify and explain; the "
                         "apply half is a separate decision and it is his. There is no un-delete")


RED_PROOF = [
    {
        "why": "an 'unknown' row becomes releasable — 2,325 of his rows say exactly that, and it "
               "means no film AND no retention record, which is an absence of evidence in both "
               "directions rather than a proof that anything was extracted",
        "file": "journal_retention.py",
        "find": '            elif str(s.get("footageState") or "") != EXTRACTED:',
        "replace": '            elif False:',
        "matches": 1,
    },
    {
        "why": "the newest runs stop being protected, so the 8 he explicitly asked to keep become "
               "deletable the moment their film is retired",
        "file": "journal_retention.py",
        "find": "        elif sid in newest:",
        "replace": "        elif False:",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
