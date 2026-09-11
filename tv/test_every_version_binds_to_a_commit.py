#!/usr/bin/env python3
"""A version row that cannot name its commit is a ship nobody can find again.

⚠⚠ THE MEASURED STATE, 2026-09-11: **249 of 278 rows** in the TASKS.md version table carried the
literal `(this commit)`. `bump_version.py` writes it because the commit does not exist at bump
time, and nothing ever came back. Grok Bot raised it three ticks running (GB-B-403/404/405) as a
refutable claim — *"a next model restoring status from the version table alone will not bind v2924
to `d2ec0fcd`"* — and it was right. This is the failure CLAUDE.md §3 exists after: a list that
survives only in a session is not a list.
"""
import ast
import io
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
import stamp_versions as SV  # noqa: E402

TASKS = os.path.join(os.path.dirname(HERE), "TASKS.md")


def _table(rows, foreign=()):
    """A version table, optionally with a FOREIGN table above it. -> path (caller unlinks)

    ⚠⚠ v2930 — `foreign` EXISTS BECAUSE ITS ABSENCE COST A REGRESSION. v2929's fixtures held one
    table, so nothing could express the situation that actually broke: TASKS.md also carries a
    `| ship | what it closed |` table whose rows START WITH A BOLD vNNNN and have two columns BY
    DESIGN. A reader that matches on the row shape alone eats them.
    """
    body = ""
    if foreign:
        body += "| ship | what it closed |\n|---|---|\n" + "".join(
            "| **%s** | %s closed something |\n" % (v, v) for v in foreign) + "\n"
    body += SV.TABLE_HEAD + "\n|---|---|---|\n" + "".join(
        "| **%s** | %s | %s — a note |\n" % (v, c, v) for v, c in rows)
    f = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
    f.write(body)
    f.close()
    return f.name


class EveryVersionBindsToACommit(unittest.TestCase):

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────────
    def test_the_live_table_has_no_unbound_row(self):
        """★★ THE HEADLINE, against the real file. 249 rows once read `(this commit)`.

        ⚠ EXACTLY ONE ROW MAY BE PENDING, AND IT MUST BE THE NEWEST. The first cut of this law
        demanded ZERO and went red the moment v2927 was bumped — correctly, and the LAW was the
        wrong one, not the table: at bump time the commit genuinely does not exist yet, so
        `(this commit)` is the honest cell for the row being written. A law stricter than the
        truth teaches you to edit the data to satisfy it. [[ab-against-head-before-blaming-the-room]]
        """
        src = io.open(TASKS, encoding="utf-8").read()
        # ⚠⚠ v2930 — SCOPED TO THE TABLE, AND THE LAW HAD THE SAME BUG THE TOOL DID. The v2929
        # form counted `VROW` over the WHOLE FILE (331) against `ROW` (281) and read the 50 rows
        # of the separate `| ship | what it closed |` table as version rows missing a cell. The
        # comparison is only meaningful inside the version table's own region.
        span = SV.table_region(src)
        self.assertIsNotNone(span, "the version table header is gone — re-derive this law")
        body = src[span[0]:span[1]]
        rows = SV.ROW.findall(body)
        self.assertEqual(len(SV.VROW.findall(body)), len(rows),
                         "%d row(s) in the version table but only %d carry a SHA cell — the rest "
                         "cannot bind a version to a commit and this law would not have noticed"
                         % (len(SV.VROW.findall(body)), len(rows)))
        pending = [v for v, cell in rows if cell == "`(this commit)`"]
        self.assertLessEqual(len(pending), 1,
                             "%d version row(s) cannot name the commit that shipped them (%s) — "
                             "only the newest may be pending. Run `python3 tv/stamp_versions.py`"
                             % (len(pending), ", ".join(pending[:6])))
        if pending:
            self.assertEqual(rows[0][0], pending[0],
                             "the pending row is %s but the newest row is %s — an OLD row lost "
                             "its binding, which is not the same as one not yet earned"
                             % (pending[0], rows[0][0]))
        self.assertGreater(len(rows), 250,
                           "the table reader matched only %d rows, which is fewer than the "
                           "history it is supposed to cover — suspect the regex, not the table"
                           % len(rows))

    def test_a_row_OUTSIDE_the_version_table_is_never_touched(self):
        """⚠⚠ THE REGRESSION I SHIPPED IN v2929, made into the law that would have caught it.

        TASKS.md carries a second table headed `| ship | what it closed |` whose rows also start
        with a bold vNNNN and have TWO columns by design. v2929 matched on the row shape alone,
        decided 50 of them were "legacy version rows missing a SHA cell", and inserted one into
        every last one — producing three-cell rows under a two-column header, in the file this
        tool exists to keep honest. v2927's narrower reader had been RIGHT to skip them.

        **A row is a version row because of the TABLE IT IS IN**, not because of how it starts.
        [[regression-guard]] [[ab-against-head-before-blaming-the-room]]"""
        p = _table([("v9002", "`(this commit)`")], foreign=("v9001", "v9000"))
        before = io.open(p, encoding="utf-8").read()
        try:
            SV.stamp(path=p, known={"v9002": "cccccccccccc", "v9001": "dddddddddddd",
                                    "v9000": "eeeeeeeeeeee"})
            after = io.open(p, encoding="utf-8").read()
        finally:
            os.unlink(p)
        for v in ("v9001", "v9000"):
            row_b = [l for l in before.splitlines() if l.startswith("| **%s**" % v)][0]
            row_a = [l for l in after.splitlines() if l.startswith("| **%s**" % v)][0]
            self.assertEqual(row_b, row_a,
                             "a row in ANOTHER table was rewritten:\n  before %s\n  after  %s"
                             % (row_b, row_a))
        self.assertNotIn("dddddddd", after, "a foreign row was given a commit it never asked for")

    def test_the_NEWEST_row_is_the_highest_number_not_the_first_line(self):
        """⚠ v2929 took `all_rows[0]` as the newest and got v2435 — a row from a different table
        that merely appeared earlier in the file. File order is not version order."""
        p = _table([("v9001", "`(this commit)`"), ("v9003", "`(this commit)`")])
        try:
            r = SV.stamp(path=p, known={})       # nothing bindable: only the NEWEST may be pending
            got = io.open(p, encoding="utf-8").read()
        finally:
            os.unlink(p)
        self.assertEqual(1, r["counts"]["pending"],
                         "%r — the newest row was not identified by number" % (r["counts"],))
        self.assertIn("| **v9003** | `(this commit)`", got,
                      "v9003 is the highest version and should be the pending one:\n%s" % got)

    def test_a_cell_that_ALREADY_names_a_commit_is_never_rewritten(self):
        """⚠⚠ THE LAUNDERING GUARD. A backfill that can overwrite an existing SHA is a backfill
        that can quietly replace a right answer with a derived one. It may only ever fill a blank."""
        p = _table([("v9001", "`deadbeef`"), ("v9000", "`(this commit)`")])
        try:
            SV.stamp(path=p, known={"v9000": "aaaaaaaaaaaa", "v9001": "bbbbbbbbbbbb"})
            got = io.open(p, encoding="utf-8").read()
        finally:
            os.unlink(p)
        self.assertIn("`deadbeef`", got,
                      "an existing SHA was rewritten by the backfill:\n%s" % got)
        self.assertNotIn("bbbbbbbb", got,
                         "the tool replaced a recorded commit with its own derivation")

    def test_a_CARRIED_version_is_not_dressed_up_as_a_BOUND_one(self):
        """⚠⚠ THE DISTINCTION THAT MUST SURVIVE. Versions batch 3-4 per push, so an intermediate
        version's VERSION line never appears alone in any commit — it was CARRIED into the commit
        that stamps the top of its batch. MEASURED: 230 of 249 bind directly, 19 are carried.
        Printing a carried row as a plain SHA asserts a precision that does not exist.
        [[unknown-stays-unknown]] [[label-outlived-referent]]"""
        p = _table([("v9002", "`(this commit)`"), ("v9001", "`(this commit)`")])
        try:
            r = SV.stamp(path=p, known={"v9002": "cccccccccccc"})   # v9001 has no stamp of its own
            got = io.open(p, encoding="utf-8").read()
        finally:
            os.unlink(p)
        self.assertEqual(1, r["counts"]["bound"], "v9002 did not bind: %r" % (r["counts"],))
        self.assertEqual(1, r["counts"]["carried"], "v9001 was not marked carried: %r" % (r["counts"],))
        self.assertIn("in the v9002 commit", got,
                      "the carried row does not say which commit actually carried it:\n%s" % got)

    def test_the_AUDIT_can_re_read_everything_the_STAMP_wrote(self):
        """⚠⚠ THE DEFECT THIS TOOL SHIPPED AND CAUGHT ON ITSELF, made into a law. The first ROW
        regex required a cell to END at its closing backtick, so the moment the stamper wrote a
        carried row its own reader stopped matching it: the stamp run counted 278 rows and the
        audit that followed counted 259, with nothing said about the 19 that vanished.
        A backfill whose audit cannot re-read its own output is one nobody can check.
        [[zero-needs-a-denominator]] [[feedback-suspect-the-instrument]]"""
        p = _table([("v9002", "`(this commit)`"), ("v9001", "`(this commit)`")])
        try:
            before = len(SV.ROW.findall(io.open(p, encoding="utf-8").read()))
            SV.stamp(path=p, known={"v9002": "cccccccccccc"})
            after = len(SV.ROW.findall(io.open(p, encoding="utf-8").read()))
        finally:
            os.unlink(p)
        self.assertEqual(before, after,
                         "the table reader saw %d rows before the stamp and %d after — the "
                         "instrument cannot re-read its own output" % (before, after))

    def test_a_version_that_binds_to_NOTHING_reads_UNKNOWN_and_not_a_guess(self):
        """★ An unbindable row must say so. Inventing the nearest SHA is worse than a blank,
        because a wrong provenance is acted on and a blank is questioned."""
        # ⚠ TWO ROWS ON PURPOSE. The first cut used one, and it failed — correctly: a single-row
        # table's only row IS the newest, so `pending` is the right answer and the fixture was
        # asking the wrong question. The law is about an OLDER row that binds to nothing.
        # [[sabotage-is-usually-the-wrong-one]] — the same lesson, arriving through a red law.
        p = _table([("v9002", "`(this commit)`"), ("v9001", "`(this commit)`")])
        try:
            r = SV.stamp(path=p, known={})          # nothing known at all
            got = io.open(p, encoding="utf-8").read()
        finally:
            os.unlink(p)
        self.assertEqual(1, r["counts"]["pending"],
                         "the NEWEST row must stay `(this commit)` — its commit does not exist "
                         "yet, and that is honest: %r" % (r["counts"],))
        self.assertEqual(1, r["counts"]["unknown"], "an unbindable row was bound anyway: %r" % (r["counts"],))
        self.assertIn("UNKNOWN", got, "the unbindable row does not say UNKNOWN:\n%s" % got)

    def test_bump_version_actually_CALLS_the_stamper(self):
        """⚠ THE JOIN. A backfill nobody runs is the same grave in a better location — and this
        repo's single most repeated defect is two halves each built right and never joined.
        STRUCTURAL: parse for a real call, do not match the prose that mentions it.
        [[the-unjoined-end]] [[source-reading-guard]]"""
        tree = ast.parse(io.open(os.path.join(HERE, "bump_version.py"), encoding="utf-8").read())
        imports = [n for n in ast.walk(tree)
                   if isinstance(n, ast.Import)
                   and any(al.name == "stamp_versions" for al in n.names)]
        self.assertTrue(imports, "bump_version.py never imports the stamper")
        calls = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute) and n.func.attr == "stamp"]
        self.assertTrue(calls,
                        "bump_version.py imports the stamper and never calls stamp() — plumbing "
                        "with no tap")

        # ⚠⚠ v2930 — AND THE CALL MUST COME AFTER THE WRITE, WHICH IS WHERE THIS LAW WAS HOLLOW.
        # v2927 called stamp() BEFORE `io.open(p, "w").write(...)`. TASKS.md is read into `s` at
        # the top of that function; the stamper wrote the file; then the stale `s` was written
        # straight back over it. MEASURED: the v2928 bump printed "bound 1 version row(s)" and
        # commit 6442cfe5 still carries `| **v2927** | `(this commit)` |`. The backfill ran,
        # was correct, and was clobbered in the same breath.
        # Asserting the call EXISTS proved the tap was plumbed, never that water came out — the
        # exact defect this law names in the line above. [[plumbing-with-no-tap]]
        src = io.open(os.path.join(HERE, "bump_version.py"), encoding="utf-8").read()
        writes = [n for n in ast.walk(tree)
                  if isinstance(n, ast.Call)
                  and isinstance(n.func, ast.Attribute) and n.func.attr == "write"
                  and "head + row" in (ast.get_source_segment(src, n) or "")]
        self.assertTrue(writes, "the TASKS.md row write is gone — re-derive this law")
        self.assertGreater(min(c.lineno for c in calls), max(w.lineno for w in writes),
                           "stamp() is called at line %d, BEFORE the TASKS.md write at line %d — "
                           "the backfill will be overwritten by the stale in-memory copy, which "
                           "is exactly what shipped in v2927"
                           % (min(c.lineno for c in calls), max(w.lineno for w in writes)))


RED_PROOF = [
    {
        "why": 'lets the backfill overwrite a cell that already names a commit, so a recorded provenance can be replaced by a derived one. A tool that can launder history is worse than no tool. ⚠ The v2927 anchor for this went INVALID when stamp() was rewritten for v2929 — caught by the drill, which is the only reason it is not a silent hole.',
        "file": 'stamp_versions.py',
        "find": '        if not legacy and cell != "`(this commit)`":\n            counts["left"] += 1\n            return m.group(0)\n',
        "replace": '        if False:\n            counts["left"] += 1\n            return m.group(0)\n',
        "matches": 1,
    },
    {
        "why": 'prints a CARRIED version as a plain SHA, asserting that its own VERSION stamp landed in that commit when it did not. 19 of the 249 rows are carried, so this mislabels every batched intermediate version.',
        "file": 'stamp_versions.py',
        "find": '    if state == "carried":\n        return "`%s` (%s)" % (sha[:8], why)\n',
        "replace": '    if state == "carried":\n        return "`%s`" % sha[:8]\n',
        "matches": 1,
    },
    {
        "why": 'restores the narrow ROW regex that could not re-read a cell carrying an annotation — the defect this tool shipped and caught on itself, where the stamp counted 278 rows and the audit that followed counted 259 with nothing said about the 19 that vanished.',
        "file": 'stamp_versions.py',
        "find": "ROW = re.compile(r'^\\| \\*\\*(v\\d{4})\\*\\* \\| (`[^`]*`[^|]*?) \\|', re.M)\n",
        "replace": "ROW = re.compile(r'^\\| \\*\\*(v\\d{4})\\*\\* \\| (`[^`]*`) \\|', re.M)\n",
        "matches": 1,
    },
    {
        "why": 'turns an unbindable row into a silent blank instead of an UNKNOWN, so a version with no provenance renders exactly like one that was never checked.',
        "file": 'stamp_versions.py',
        "find": '    return "`(UNKNOWN — %s)`" % why\n',
        "replace": '    return "``"\n',
        "matches": 1,
    },
    {
        "why": 'unjoins the stamper from the bump, which is exactly the state the table was in for 249 versions: a correct tool nothing ever ran.',
        "file": 'bump_version.py',
        "find": '            import stamp_versions as _sv\n',
        "replace": '            import os as _sv\n',
        "matches": 1,
    },
    {
        "why": 'v2930/A — unscopes the substitution so it eats every `| **vNNNN** |` row in the FILE again, including the 50 rows of the separate `| ship | what it closed |` table. That is the regression v2929 shipped: three-cell rows under a two-column header.',
        "file": 'stamp_versions.py',
        "find": '    new_body = VROW.sub(_fix, body)\n    out = head + new_body + tail\n',
        "replace": '    new_body = VROW.sub(_fix, src)\n    out = new_body\n',
        "matches": 1,
    },
    {
        "why": 'v2930/B — takes the FIRST row in file order as the newest instead of the highest number, which is how v2929 decided v2435 was newer than v2929.',
        "file": 'stamp_versions.py',
        "find": '    newest = ("v%d" % max(int(v[1:]) for v, _ in all_rows)) if all_rows else None\n',
        "replace": '    newest = all_rows[0][0] if all_rows else None\n',
        "matches": 1,
    },
    {
        "why": "v2930/C — restores the v2927 ORDER: the stamper runs and then the TASKS.md write lands on top of it, from the stale `s` read at the top of the function. MEASURED: the v2928 bump printed 'bound 1 version row(s)' and commit 6442cfe5 still carries `(this commit)` for v2927. ⚠ The first cut of this tamper only swapped the write with a print and came back BLIND — the write has to move PAST the stamper for the law to have anything to catch.",
        "file": 'bump_version.py',
        "find": '        io.open(p, "w", encoding="utf-8").write(s.replace(head, head + row, 1))\n        print("   recorded %s in TASKS.md" % ver)\n        # ⚠⚠ AFTER THE WRITE, NOT BEFORE — AND THAT ORDER IS THE WHOLE FIX.\n        # v2927 put this block ABOVE the write. `s` was read at the top of this function, the\n        # stamper then wrote TASKS.md itself, and the line above wrote STALE `s` straight back over\n        # it. MEASURED 2026-09-11: the v2928 bump printed "bound 1 version row(s)" and commit\n        # 6442cfe5 still carries `| **v2927** | \\u0060(this commit)\\u0060 |`. The backfill was\n        # real, correct, and clobbered in the same breath — a lost update.\n        # ⚠ AND THE LAW WAS HOLLOW. test_bump_version_actually_CALLS_the_stamper asserted the\n        # import and the .stamp() call existed, so it proved the tap was PLUMBED and never that\n        # water came out. It cites [[plumbing-with-no-tap]] in its own docstring.\n        # being written — at bump time the commit genuinely does not exist — but nothing ever came\n        # back to replace it, and MEASURED 2026-09-11 that left 249 of 278 rows unable to bind a\n        # version to a commit at all. Grok Bot raised it three ticks running (GB-B-403/404/405).\n        # The previous version\'s commit DOES exist by now, so every row but the newest can be\n        # bound here. [[the-unjoined-end]] [[plumbing-with-no-tap]]\n        try:\n            import stamp_versions as _sv\n            _r = _sv.stamp()\n            _c = _r["counts"]\n            if _c["bound"] or _c["carried"] or _c["unknown"]:\n                print("   bound %d version row(s) to a commit (%d carried, %d UNKNOWN)"\n                      % (_c["bound"], _c["carried"], _c["unknown"]))\n        except Exception as _e:\n            # ⚠ SAY SO. A silent failure here is how the table quietly goes back to 249 unbound\n            # rows with everything looking healthy. [[feedback-silence-is-not-evidence]]\n            print("   ⚠ version rows were NOT backfilled (%s) — run tv/stamp_versions.py by hand"\n                  % type(_e).__name__)\n',
        "replace": '        # ⚠⚠ AFTER THE WRITE, NOT BEFORE — AND THAT ORDER IS THE WHOLE FIX.\n        # v2927 put this block ABOVE the write. `s` was read at the top of this function, the\n        # stamper then wrote TASKS.md itself, and the line above wrote STALE `s` straight back over\n        # it. MEASURED 2026-09-11: the v2928 bump printed "bound 1 version row(s)" and commit\n        # 6442cfe5 still carries `| **v2927** | \\u0060(this commit)\\u0060 |`. The backfill was\n        # real, correct, and clobbered in the same breath — a lost update.\n        # ⚠ AND THE LAW WAS HOLLOW. test_bump_version_actually_CALLS_the_stamper asserted the\n        # import and the .stamp() call existed, so it proved the tap was PLUMBED and never that\n        # water came out. It cites [[plumbing-with-no-tap]] in its own docstring.\n        # being written — at bump time the commit genuinely does not exist — but nothing ever came\n        # back to replace it, and MEASURED 2026-09-11 that left 249 of 278 rows unable to bind a\n        # version to a commit at all. Grok Bot raised it three ticks running (GB-B-403/404/405).\n        # The previous version\'s commit DOES exist by now, so every row but the newest can be\n        # bound here. [[the-unjoined-end]] [[plumbing-with-no-tap]]\n        try:\n            import stamp_versions as _sv\n            _r = _sv.stamp()\n            _c = _r["counts"]\n            if _c["bound"] or _c["carried"] or _c["unknown"]:\n                print("   bound %d version row(s) to a commit (%d carried, %d UNKNOWN)"\n                      % (_c["bound"], _c["carried"], _c["unknown"]))\n        except Exception as _e:\n            # ⚠ SAY SO. A silent failure here is how the table quietly goes back to 249 unbound\n            # rows with everything looking healthy. [[feedback-silence-is-not-evidence]]\n            print("   ⚠ version rows were NOT backfilled (%s) — run tv/stamp_versions.py by hand"\n                  % type(_e).__name__)\n        io.open(p, "w", encoding="utf-8").write(s.replace(head, head + row, 1))\n        print("   recorded %s in TASKS.md" % ver)\n',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
