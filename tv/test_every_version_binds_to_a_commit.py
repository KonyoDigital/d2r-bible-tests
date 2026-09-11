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


def _table(rows):
    """A minimal version table. -> path (caller unlinks)"""
    body = "| ver | sha | note |\n|---|---|---|\n" + "".join(
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
        rows = SV.ROW.findall(src)
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
        rows = SV.ROW.findall(src)
        self.assertGreater(len(rows), 250,
                           "the table reader matched only %d rows, which is fewer than the "
                           "history it is supposed to cover — suspect the regex, not the table"
                           % len(rows))

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


RED_PROOF = [
    {
        "why": "lets the backfill overwrite a cell that already names a commit, so a recorded provenance can be replaced by a derived one. A tool that can launder history is worse than no tool.",
        "file": "stamp_versions.py",
        "find": '        if cell != "`(this commit)`":\n            counts["left"] += 1\n            return m.group(0)\n',
        "replace": '        if False:\n            counts["left"] += 1\n            return m.group(0)\n',
        "matches": 1,
    },
    {
        "why": "prints a CARRIED version as a plain SHA, asserting that its own VERSION stamp landed in that commit when it did not. 19 of the 249 rows are carried, so this mislabels every batched intermediate version.",
        "file": "stamp_versions.py",
        "find": '    if state == "carried":\n        return "`%s` (%s)" % (sha[:8], why)\n',
        "replace": '    if state == "carried":\n        return "`%s`" % sha[:8]\n',
        "matches": 1,
    },
    {
        "why": "restores the narrow ROW regex that could not re-read a cell carrying an annotation \u2014 the defect this tool shipped and caught on itself, where the stamp counted 278 rows and the audit that followed counted 259 with nothing said about the 19 that vanished.",
        "file": "stamp_versions.py",
        "find": "ROW = re.compile(r'^\\| \\*\\*(v\\d{4})\\*\\* \\| (`[^`]*`[^|]*?) \\|', re.M)\n",
        "replace": "ROW = re.compile(r'^\\| \\*\\*(v\\d{4})\\*\\* \\| (`[^`]*`) \\|', re.M)\n",
        "matches": 1,
    },
    {
        "why": "turns an unbindable row into a silent blank instead of an UNKNOWN, so a version with no provenance renders exactly like one that was never checked.",
        "file": "stamp_versions.py",
        "find": '    return "`(UNKNOWN — %s)`" % why\n',
        "replace": '    return "``"\n',
        "matches": 1,
    },
    {
        "why": "unjoins the stamper from the bump, which is exactly the state the table was in for 249 versions: a correct tool nothing ever ran.",
        "file": "bump_version.py",
        "find": "            import stamp_versions as _sv\n",
        "replace": "            import os as _sv\n",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
