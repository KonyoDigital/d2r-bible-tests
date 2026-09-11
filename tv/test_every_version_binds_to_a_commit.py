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
    # ⚠ v2935 — `c is None` BUILDS A TWO-COLUMN ROW INSIDE THE VERSION TABLE. v2930 dropped this
    # arm when the foreign-table fixture replaced it, leaving `_fix`'s `legacy = len(cells) < 2`
    # branch with nothing that exercises it — a defensive arm no test could ever turn red.
    body += SV.TABLE_HEAD + "\n|---|---|---|\n" + "".join(
        ("| **%s** | %s — a note |\n" % (v, v)) if c is None else
        ("| **%s** | %s | %s — a note |\n" % (v, c, v)) for v, c in rows)
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
            # ⚠⚠ v2935 — BY NUMBER, NOT BY FILE ORDER. v2930 redefined "newest" inside stamp() as
            # max(version) and left this law reading rows[0], so the two callers in the SAME ship
            # disagreed about the word. On a table that is not newest-first — a backfilled row, a
            # batch recorded out of order — stamp() correctly marks max(version) pending and this
            # law would have gone RED on a correctly stamped table. It does not fire today only
            # because the table happens to be newest-first. [[label-outlived-referent]]
            newest = "v%d" % max(int(v[1:]) for v, _ in rows)
            self.assertEqual(newest, pending[0],
                             "the pending row is %s but the highest version is %s — an OLD row "
                             "lost its binding, which is not the same as one not yet earned"
                             % (pending[0], newest))
        self.assertGreater(len(rows), 250,
                           "the table reader matched only %d rows, which is fewer than the "
                           "history it is supposed to cover — suspect the regex, not the table"
                           % len(rows))

    def test_a_TWO_COLUMN_row_INSIDE_the_version_table_is_given_a_cell(self):
        """⚠ The arm no fixture could reach. `_fix` special-cases `len(cells) < 2` and inserts a
        SHA cell — correct for a hand-edited or genuinely leftover row inside the version table —
        but v2930 removed the only fixture that could build one, so the branch was defensive code
        nothing could turn red. The live table has 0 such rows, so the live law cannot reach it
        either. [[feedback-blind-fixture-green-gate]]"""
        p = _table([("v9003", "`(this commit)`"), ("v9002", None)])
        try:
            r = SV.stamp(path=p, known={"v9003": "c" * 12, "v9002": "d" * 12})
            got = io.open(p, encoding="utf-8").read()
        finally:
            os.unlink(p)
        self.assertEqual(2, r["counts"]["rows"], "the two-column row was not seen: %r" % (r["counts"],))
        self.assertEqual(1, r["counts"]["legacyFilled"],
                         "the in-table two-column row was not given a cell: %r" % (r["counts"],))
        self.assertIn("`dddddddd`", got, "it did not get its commit:\n%s" % got)
        self.assertIn("v9002 — a note", got, "its note was destroyed by the widening:\n%s" % got)

    def test_a_table_whose_RULE_LINE_is_missing_is_UNMEASURED_not_short(self):
        """⚠⚠ MEASURED: written without `|---|---|---|`, the old reader skipped two newlines, the
        second of which ended the first DATA row — so the region began one row late, `rows`
        reported 1 where there were 2, and the NEWEST row stayed pending forever. A reader that
        silently drops a row reports a smaller table rather than an unrecognised one."""
        p = _table([("v9002", "`(this commit)`"), ("v9001", "`(this commit)`")])
        raw = io.open(p, encoding="utf-8").read().replace("|---|---|---|\n", "", 1)
        io.open(p, "w", encoding="utf-8").write(raw)
        try:
            r = SV.stamp(path=p, known={"v9002": "c" * 12, "v9001": "d" * 12})
            after = io.open(p, encoding="utf-8").read()
        finally:
            os.unlink(p)
        self.assertIsNone(r["counts"]["rows"],
                          "a table with no rule line reported %r rows instead of refusing"
                          % (r["counts"]["rows"],))
        self.assertIn("UNMEASURED", r.get("why") or "",
                      "the refusal does not say it is unmeasured: %r" % r.get("why"))
        self.assertEqual(raw, after, "it wrote to a table it could not parse")

    def test_EVERY_refusal_says_UNMEASURED_the_SAME_WAY(self):
        """⚠⚠ TWO REFUSALS IN ONE FUNCTION DISAGREED ABOUT HOW TO SAY "I DID NOT LOOK". v2935 gave
        the no-table arm `rows=None` because zero examined is not zero unbound — and left the
        git-unreadable arm from v2931 reporting `rows=0` with a `why` beside it. MEASURED: a caller
        treating `rows is None` as unmeasured read a broken `git log` as a MEASURED EMPTY TABLE.

        So the law covers ALL refusal paths, not the one that got fixed: anything returning a `why`
        must report None for every count, so no refusal can be mistaken for a measurement.
        Caught by the cross-family eye on v2935. [[zero-needs-a-denominator]] [[regression-guard]]"""
        import tempfile
        cases = []
        d = tempfile.mkdtemp()
        p = os.path.join(d, "T.md")
        io.open(p, "w", encoding="utf-8").write(
            SV.TABLE_HEAD + "\n|---|---|---|\n| **v9001** | `(this commit)` | n |\n")
        cases.append(("git unreadable", SV.stamp(path=p, cwd=d)))
        p2 = _table([("v9002", "`(this commit)`")])
        raw = io.open(p2, encoding="utf-8").read().replace("|---|---|---|\n", "", 1)
        io.open(p2, "w", encoding="utf-8").write(raw)
        try:
            cases.append(("no rule line", SV.stamp(path=p2, known={"v9002": "c" * 12})))
        finally:
            os.unlink(p2)
        p3 = _table([("v9003", "`(this commit)`")])
        io.open(p3, "w", encoding="utf-8").write(
            "| ship | what it closed |\n|---|---|\n| **v9001** | a note |\n")
        try:
            cases.append(("no version table", SV.stamp(path=p3, known={})))
        finally:
            os.unlink(p3)
        self.assertEqual(3, len(cases), "a refusal path went unexercised — UNMEASURED")
        for label, r in cases:
            self.assertTrue(r.get("why"), "%s did not refuse at all: %r" % (label, r["counts"]))
            for key in ("rows", "shaCellsBefore", "shaCellsAfter"):
                self.assertIsNone(r["counts"].get(key),
                                  "%s refused but reported %s=%r — a refusal that hands back a "
                                  "number is indistinguishable from a measurement"
                                  % (label, key, r["counts"].get(key)))

    def test_NO_version_table_makes_audit_REFUSE_not_pass(self):
        """⚠⚠ THE COMMAND WHOSE JOB IS TO REFUSE AN UNBOUND TABLE WAS VACUOUSLY GREEN WHENEVER IT
        COULD NOT FIND THE TABLE. MEASURED: a TASKS.md holding only the ship table printed
        "0 row(s) in the version table" and `--audit` exited 0. Zero examined is not zero
        unbound. [[zero-needs-a-denominator]]"""
        p = _table([], foreign=("v9001",))
        was = SV.TASKS
        buf = io.StringIO()
        try:
            io.open(p, "w", encoding="utf-8").write(
                "| ship | what it closed |\n|---|---|\n| **v9001** | a note |\n")
            SV.TASKS = p
            sys.stdout, real = buf, sys.stdout
            try:
                rc = SV.main(["--audit"])
            finally:
                sys.stdout = real
        finally:
            SV.TASKS = was
            os.unlink(p)
        self.assertEqual(1, rc, "--audit passed with no version table at all:\n%s" % buf.getvalue())
        self.assertIn("UNMEASURED", buf.getvalue(),
                      "the refusal does not say it is unmeasured:\n%s" % buf.getvalue())

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
        # ⚠⚠ ASSERT ON THE STATE, NOT THE CELL. The first cut read the file and came back BLIND:
        # since v2931 an UNKNOWN row also keeps `(this commit)`, so pending and unknown are
        # byte-identical on disk and the law could not tell which row had been called newest.
        # The drill caught it. [[sabotage-is-usually-the-wrong-one]]
        states = {v: st for v, st, _sha in r["changed"]}
        self.assertEqual("pending", states.get("v9003"),
                         "v9003 is the highest version and must be the pending one; states=%r"
                         % (states,))
        self.assertEqual("unknown", states.get("v9001"),
                         "v9001 is not the newest and must not be treated as pending; states=%r"
                         % (states,))
        self.assertEqual(1, r["counts"]["pending"],
                         "%r — the newest row was not identified by number" % (r["counts"],))

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

    def test_a_version_that_binds_to_NOTHING_keeps_the_literal_and_is_REPORTED(self):
        """★ An unbindable row must not be stamped UNKNOWN. That looks more honest and is strictly
        worse: stamp() never overwrites a non-literal cell, so a row that simply has not been
        COMMITTED yet — three bumps batched before a commit, the documented workflow — would be
        frozen as UNKNOWN forever, and the rule protecting real provenance is what keeps the lie.
        Raised by the cross-family eye on v2927. The count is still reported and --audit exits 1."""
        p = _table([("v9002", "`(this commit)`"), ("v9001", "`(this commit)`")])
        try:
            r = SV.stamp(path=p, known={})          # git answered; it simply knows nothing
            got = io.open(p, encoding="utf-8").read()
        finally:
            os.unlink(p)
        self.assertEqual(1, r["counts"]["pending"], "%r" % (r["counts"],))
        self.assertEqual(1, r["counts"]["unknown"], "an unbindable row was bound anyway: %r"
                         % (r["counts"],))
        self.assertNotIn("UNKNOWN", got,
                         "an unresolvable row was STAMPED unknown, which never-overwrite then "
                         "makes permanent:\n%s" % got)

    def test_an_UNREADABLE_git_writes_NOTHING_at_all(self):
        """⚠⚠ THE TOOL LAUNDERED AN INSTRUMENT FAILURE INTO DATA, in the function whose own
        docstring forbids it. MEASURED: in a directory with no history, `version_commits()`
        returned `{}` — indistinguishable from a real empty answer — every row resolved UNKNOWN,
        and the tool WROTE `(UNKNOWN — ...)` over the honest `(this commit)`.
        `{}` and None are different answers. [[unknown-stays-unknown]]"""
        d = tempfile.mkdtemp()
        self.assertIsNone(SV.version_commits(d),
                          "a git that cannot be asked returned a dict, which reads as a real "
                          "answer meaning 'no versions exist'")
        p = os.path.join(d, "T.md")
        io.open(p, "w", encoding="utf-8").write(
            SV.TABLE_HEAD + "\n|---|---|---|\n| **v9002** | `(this commit)` | n |\n"
            "| **v9001** | `(this commit)` | n |\n")
        before = io.open(p, encoding="utf-8").read()
        r = SV.stamp(path=p, cwd=d)
        self.assertFalse(r["wrote"], "the tool wrote to the table with a broken instrument")
        self.assertEqual(before, io.open(p, encoding="utf-8").read(),
                         "the table changed although git could not be read")
        self.assertIn("UNMEASURED", r.get("why") or "",
                      "the refusal does not say it is unmeasured: %r" % r.get("why"))

    def test_every_CALLER_of_the_stamper_consults_its_REFUSAL(self):
        """⚠⚠ THE CLASS. v2931 taught `stamp()` to REFUSE when git cannot be asked, returning a
        `why` instead of raising. `main()` was joined to that; `bump_version.py` was not — and its
        `except` arm cannot help, because a refusal is a RETURN VALUE, not an exception. MEASURED
        with git unreachable: `stamp()` returned a `why`, the bump's `bound or carried or unknown`
        was all zeros, and the bump printed only "recorded vNNNN in TASKS.md". The instrument
        failure v2931 exists to announce was silent on the one path that runs at every bump.

        So the law is per-CALLER, not per-site: anything that calls `stamp()` outside this test
        must read `why` from what it gets back. [[the-unjoined-end]]"""
        # ⚠ PARSED, NOT GREPPED. The first cut of this law was `assertIn('"why"', src)` over the
        # whole file — which the fix's own print string satisfies, so deleting the CHECK would
        # have left it green. A law that reads prose goes green the moment prose mentions the
        # thing; this one walks to the assignment and requires the value to be consulted.
        # [[source-reading-guard]]
        checked = 0
        for mod in ("stamp_versions.py", "bump_version.py"):
            tree = ast.parse(io.open(os.path.join(HERE, mod), encoding="utf-8").read())
            for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
                names = set()
                for asn in ast.walk(fn):
                    if not isinstance(asn, ast.Assign) or not isinstance(asn.value, ast.Call):
                        continue
                    f = asn.value.func
                    if ((isinstance(f, ast.Attribute) and f.attr == "stamp")
                            or (isinstance(f, ast.Name) and f.id == "stamp")):
                        if isinstance(asn.targets[0], ast.Name):
                            names.add(asn.targets[0].id)
                if not names:
                    continue
                checked += 1
                reads = set()
                for nd in ast.walk(fn):
                    base = why = None
                    if isinstance(nd, ast.Call) and isinstance(nd.func, ast.Attribute) \
                       and nd.func.attr == "get" and isinstance(nd.func.value, ast.Name) \
                       and nd.args and isinstance(nd.args[0], ast.Constant):
                        base, why = nd.func.value.id, nd.args[0].value
                    elif isinstance(nd, ast.Subscript) and isinstance(nd.value, ast.Name) \
                            and isinstance(nd.slice, ast.Constant):
                        base, why = nd.value.id, nd.slice.value
                    if base in names and why == "why":
                        reads.add(base)
                self.assertTrue(reads,
                                "%s.%s() calls stamp() and never reads `why` off the result — a "
                                "refusal is a RETURN VALUE, not an exception, so this caller "
                                "reports nothing at all when the instrument fails"
                                % (mod, fn.name))
        self.assertGreaterEqual(checked, 2,
                                "only %d caller(s) of stamp() were found — re-derive this law"
                                % checked)

    def test_every_counts_key_the_CLI_reads_is_one_the_stamper_WRITES(self):
        """⚠⚠ THE CLASS, NOT THE INSTANCE. v2929 renamed `threeColumn` to `shaCellsBefore`/
        `shaCellsAfter`; I changed the key in the CONDITION and not in the line it guards, so the
        one path that reports "this tool cannot speak for these rows" raised `KeyError` instead of
        warning. It never fired, because on the happy path `rows == shaCellsAfter` and the branch
        is dead — **a diagnostic that has never had a green run is one nobody has proven can
        speak.** Caught by the cross-family eye on v2929.

        So the law is not "this key exists": it is every key `main()` reads must be a key `stamp()`
        actually produces. A rename cannot outrun it. [[label-outlived-referent]]"""
        src = io.open(os.path.join(HERE, "stamp_versions.py"), encoding="utf-8").read()
        fn = [n for n in ast.walk(ast.parse(src))
              if isinstance(n, ast.FunctionDef) and n.name == "main"][0]
        read = set()
        for n in ast.walk(fn):
            if (isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name)
                    and n.value.id == "c" and isinstance(n.slice, ast.Constant)
                    and isinstance(n.slice.value, str)):
                read.add(n.slice.value)
        self.assertTrue(read, "main() reads no counts keys at all — re-derive this law")
        p = _table([("v9002", "`(this commit)`"), ("v9001", "`(this commit)`")])
        try:
            produced = set(SV.stamp(path=p, known={})["counts"])
        finally:
            os.unlink(p)
        missing = sorted(read - produced)
        self.assertEqual([], missing,
                         "main() reads %r from counts, and stamp() never writes %s — the CLI "
                         "raises KeyError on whichever branch touches it" % (missing, missing))

    def test_the_cannot_speak_warning_SPEAKS_instead_of_raising(self):
        """★ The residual this warning exists to report, exercised rather than read: a version-table
        row whose SHA cell carries no backticks is seen by VROW and not by ROW, so `rows` and
        `shaCellsAfter` disagree and the branch fires. Before v2933 it raised."""
        p = _table([("v9002", "`(this commit)`"), ("v9001", "deadbeef")])
        was = SV.TASKS
        buf = io.StringIO()
        try:
            SV.TASKS = p
            sys.stdout, real = buf, sys.stdout
            try:
                rc = SV.main(["--dry"])
            finally:
                sys.stdout = real
        finally:
            SV.TASKS = was
            os.unlink(p)
        out = buf.getvalue()
        self.assertEqual(0, rc, "--dry did not exit 0: %r" % out)
        self.assertIn("cannot speak for them", out,
                      "the residual warning never printed, so the branch is still unproven:\n%s" % out)
        self.assertIn("1 row(s)", out, "the warning does not name how many rows: %r" % out)

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
        "why": "v2931/C — a non-zero `git log` becomes an EMPTY answer again, indistinguishable from 'this repo has no versions' — an instrument failure read as a measurement.",
        "file": 'stamp_versions.py',
        "find": '    if r.returncode != 0:\n        return None\n',
        "replace": '    if False:\n        return None\n',
        "matches": 1,
    },
    {
        "why": 'v2931/E — stamps an unresolvable row UNKNOWN; never-overwrite then makes it permanent, so a version merely waiting to be committed is frozen as unknown forever.',
        "file": 'stamp_versions.py',
        "find": '    # ⚠⚠ v2931 — AN UNKNOWN ROW KEEPS `(this commit)` RATHER THAN BEING STAMPED UNKNOWN.\n    # Writing UNKNOWN looks more honest and is strictly worse: `stamp()` never overwrites a cell\n    # that is not the literal, so a row that simply has not been committed YET — three bumps\n    # batched before a commit, which is the documented workflow — would be frozen as UNKNOWN\n    # forever, and the one rule that protects real provenance would be what keeps the lie.\n    # The count is still reported, and --audit still exits 1. [[unknown-stays-unknown]]\n    return "`(this commit)`"\n',
        "replace": '    return "`(UNKNOWN — %s)`" % why\n',
        "matches": 1,
    },
    {
        "why": "v2933 — restores the key that died in the v2929 rename. `threeColumn` was renamed to shaCellsBefore/shaCellsAfter and the CONDITION was updated while the line it guards was not, so the one path reporting 'this tool cannot speak for these rows' raised KeyError instead of warning. It never fired because the branch is dead on the happy path — a diagnostic with no green run is one nobody has proven can speak.",
        "file": 'stamp_versions.py',
        "find": '              % (c["rows"] - c["shaCellsAfter"]))\n',
        "replace": '              % (c["rows"] - c["threeColumn"]))\n',
        "matches": 1,
    },
    {
        "why": 'v2935/A — drops the rule-line requirement, so a table written without |---|---|---| has its region start one row late: the NEWEST row is silently dropped and reported as a smaller table rather than an unrecognised one. MEASURED: rows=1 where there were 2, newest stuck at (this commit) forever.',
        "file": 'stamp_versions.py',
        "find": '    if len(lines) < 2 or not _RULE.match(lines[1]):\n        return None\n',
        "replace": '    if False:\n        return None\n',
        "matches": 1,
    },
    {
        "why": 'v2935/B — restores all-zero counters when the table cannot be found, so `unknown == 0` and the command whose job is to refuse an unbound table is vacuously green whenever it cannot find the table. Zero examined is not zero unbound.',
        "file": 'stamp_versions.py',
        "find": '        return {"counts": dict(counts, rows=None, shaCellsBefore=None, shaCellsAfter=None,\n                               knownVersions=len(known)), "changed": [], "wrote": False,\n                "why": "the version table header was not found (or its |---| rule line is "\n                       "missing), so NOTHING here was examined — this is UNMEASURED, not a table "\n                       "with nothing unbound"}\n',
        "replace": '        return {"counts": dict(counts, rows=0, shaCellsBefore=0, shaCellsAfter=0,\n                               knownVersions=len(known)), "changed": [], "wrote": False}\n',
        "matches": 1,
    },
    {
        "why": 'v2935/C — lets main() print its zeros and exit 0 on a refusal, so the CLI reports success for a run that examined nothing.',
        "file": 'stamp_versions.py',
        "find": '    if r.get("why"):\n        # ⚠ the refusal is the answer. Printed and non-zero, never a quiet success.\n        print("   \\u2717 %s" % r["why"])\n        return 1\n',
        "replace": '    if False:\n        return 1\n',
        "matches": 1,
    },
    {
        "why": "v2936 — unjoins the bump from stamp()'s refusal. A refusal is a RETURN VALUE, not an exception, so the except arm below cannot see it and the bump prints only 'recorded vNNNN' while the instrument is broken. MEASURED with git unreachable: stamp() returned a why and this path said nothing.",
        "file": 'bump_version.py',
        "find": '            if _r.get("why"):\n                print("   \\u26a0 version rows were NOT backfilled: %s" % _r["why"])\n',
        "replace": '            if False:\n                print("   backfill note")\n',
        "matches": 1,
    },
    {
        "why": "v2930/C — restores the v2927 ORDER: the stamper runs and then the TASKS.md write lands on top of it from the stale `s` read at the top of the function. MEASURED: the v2928 bump printed 'bound 1 version row(s)' and 6442cfe5 still carries (this commit) for v2927. ⚠ RE-ANCHORED at v2936 after the refusal-join changed this block — its law still existed, so accepting the stale drop would have left the ordering unproven behind a clean count.",
        "file": 'bump_version.py',
        "find": '        io.open(p, "w", encoding="utf-8").write(s.replace(head, head + row, 1))\n        print("   recorded %s in TASKS.md" % ver)\n        # ⚠⚠ AFTER THE WRITE, NOT BEFORE — AND THAT ORDER IS THE WHOLE FIX.\n        # v2927 put this block ABOVE the write. `s` was read at the top of this function, the\n        # stamper then wrote TASKS.md itself, and the line above wrote STALE `s` straight back over\n        # it. MEASURED 2026-09-11: the v2928 bump printed "bound 1 version row(s)" and commit\n        # 6442cfe5 still carries `| **v2927** | \\u0060(this commit)\\u0060 |`. The backfill was\n        # real, correct, and clobbered in the same breath — a lost update.\n        # ⚠ AND THE LAW WAS HOLLOW. test_bump_version_actually_CALLS_the_stamper asserted the\n        # import and the .stamp() call existed, so it proved the tap was PLUMBED and never that\n        # water came out. It cites [[plumbing-with-no-tap]] in its own docstring.\n        # being written — at bump time the commit genuinely does not exist — but nothing ever came\n        # back to replace it, and MEASURED 2026-09-11 that left 249 of 278 rows unable to bind a\n        # version to a commit at all. Grok Bot raised it three ticks running (GB-B-403/404/405).\n        # The previous version\'s commit DOES exist by now, so every row but the newest can be\n        # bound here. [[the-unjoined-end]] [[plumbing-with-no-tap]]\n        try:\n            import stamp_versions as _sv\n            _r = _sv.stamp()\n            _c = _r["counts"]\n            # ⚠⚠ v2936 — A REFUSAL IS A RETURN VALUE, NOT AN EXCEPTION, AND THE `except` BELOW\n            # CANNOT SEE IT. v2931 taught stamp() to refuse when `git log` cannot be asked; main()\n            # was joined to that and THIS caller was not, so the condition below (all zeros on a\n            # refusal) was False and the bump printed only "recorded vNNNN in TASKS.md".\n            # MEASURED: with git unreachable, stamp() returned a `why` and this path said nothing.\n            # The instrument failure v2931 exists to announce was silent on the one path that runs\n            # at every bump — REG-936\'s own shape, one caller over.\n            # [[the-unjoined-end]] [[feedback-silence-is-not-evidence]]\n            if _r.get("why"):\n                print("   \\u26a0 version rows were NOT backfilled: %s" % _r["why"])\n            elif _c["bound"] or _c["carried"] or _c["unknown"]:\n                print("   bound %d version row(s) to a commit (%d carried, %d UNKNOWN)"\n                      % (_c["bound"], _c["carried"], _c["unknown"]))\n        except Exception as _e:\n            # ⚠ SAY SO. A silent failure here is how the table quietly goes back to 249 unbound\n            # rows with everything looking healthy. [[feedback-silence-is-not-evidence]]\n            print("   ⚠ version rows were NOT backfilled (%s) — run tv/stamp_versions.py by hand"\n                  % type(_e).__name__)\n',
        "replace": '        # ⚠⚠ AFTER THE WRITE, NOT BEFORE — AND THAT ORDER IS THE WHOLE FIX.\n        # v2927 put this block ABOVE the write. `s` was read at the top of this function, the\n        # stamper then wrote TASKS.md itself, and the line above wrote STALE `s` straight back over\n        # it. MEASURED 2026-09-11: the v2928 bump printed "bound 1 version row(s)" and commit\n        # 6442cfe5 still carries `| **v2927** | \\u0060(this commit)\\u0060 |`. The backfill was\n        # real, correct, and clobbered in the same breath — a lost update.\n        # ⚠ AND THE LAW WAS HOLLOW. test_bump_version_actually_CALLS_the_stamper asserted the\n        # import and the .stamp() call existed, so it proved the tap was PLUMBED and never that\n        # water came out. It cites [[plumbing-with-no-tap]] in its own docstring.\n        # being written — at bump time the commit genuinely does not exist — but nothing ever came\n        # back to replace it, and MEASURED 2026-09-11 that left 249 of 278 rows unable to bind a\n        # version to a commit at all. Grok Bot raised it three ticks running (GB-B-403/404/405).\n        # The previous version\'s commit DOES exist by now, so every row but the newest can be\n        # bound here. [[the-unjoined-end]] [[plumbing-with-no-tap]]\n        try:\n            import stamp_versions as _sv\n            _r = _sv.stamp()\n            _c = _r["counts"]\n            # ⚠⚠ v2936 — A REFUSAL IS A RETURN VALUE, NOT AN EXCEPTION, AND THE `except` BELOW\n            # CANNOT SEE IT. v2931 taught stamp() to refuse when `git log` cannot be asked; main()\n            # was joined to that and THIS caller was not, so the condition below (all zeros on a\n            # refusal) was False and the bump printed only "recorded vNNNN in TASKS.md".\n            # MEASURED: with git unreachable, stamp() returned a `why` and this path said nothing.\n            # The instrument failure v2931 exists to announce was silent on the one path that runs\n            # at every bump — REG-936\'s own shape, one caller over.\n            # [[the-unjoined-end]] [[feedback-silence-is-not-evidence]]\n            if _r.get("why"):\n                print("   \\u26a0 version rows were NOT backfilled: %s" % _r["why"])\n            elif _c["bound"] or _c["carried"] or _c["unknown"]:\n                print("   bound %d version row(s) to a commit (%d carried, %d UNKNOWN)"\n                      % (_c["bound"], _c["carried"], _c["unknown"]))\n        except Exception as _e:\n            # ⚠ SAY SO. A silent failure here is how the table quietly goes back to 249 unbound\n            # rows with everything looking healthy. [[feedback-silence-is-not-evidence]]\n            print("   ⚠ version rows were NOT backfilled (%s) — run tv/stamp_versions.py by hand"\n                  % type(_e).__name__)\n        io.open(p, "w", encoding="utf-8").write(s.replace(head, head + row, 1))\n        print("   recorded %s in TASKS.md" % ver)\n',
        "matches": 1,
    },
    {
        "why": "v2939 — puts the git-unreadable refusal back on zeros while the sibling no-table refusal reports None, so the two arms disagree about how to say 'I did not look'. A caller reading `rows is None` as unmeasured then reads a broken git log as a MEASURED EMPTY TABLE — the defect v2935 closed, on the arm it did not touch.",
        "file": 'stamp_versions.py',
        "find": '        return {"counts": dict(counts, rows=None, shaCellsBefore=None, shaCellsAfter=None,\n                               knownVersions=None),\n',
        "replace": '        return {"counts": dict(counts, rows=0, shaCellsBefore=0, shaCellsAfter=0,\n                               knownVersions=None),\n',
        "matches": 1,
    },
    {
        "why": "v2931/D — lets the tool WRITE with a broken instrument, recording the state of a failed `git log` as the provenance of the ship history. ⚠ RE-ANCHORED at v2939 when the refusal's return block changed — its law still existed, so accepting the stale drop would have left 'writes nothing when git is unreadable' unproven behind a clean 15/15.",
        "file": 'stamp_versions.py',
        "find": '    if known is None:\n        # ⚠ REFUSE, LOUDLY. Writing anything here would record the state of a broken `git log`\n        # as the provenance of his ship history.\n        # ⚠⚠ v2939 — `rows=None`, NOT 0, AND THE SIBLING ARM ALREADY KNEW THAT. v2935 taught the\n        # no-table refusal to report None because zero examined is not zero unbound; this arm kept\n        # reporting 0 with a `why` beside it, so a caller reading `rows is None` as UNMEASURED read\n        # a broken `git log` as a MEASURED EMPTY TABLE. Two refusals in one function disagreeing\n        # about how to say "I did not look" is the defect v2935 closed, on the arm it did not\n        # touch. Caught by the cross-family eye on v2935. [[zero-needs-a-denominator]]\n        return {"counts": dict(counts, rows=None, shaCellsBefore=None, shaCellsAfter=None,\n                               knownVersions=None),\n                "changed": [], "wrote": False,\n                "why": "git could not be asked for the version history, so NOTHING was written — "\n                       "this is UNMEASURED, not a table with no bindings"}\n    changed = []\n    span = table_region(src)\n    if span is None:\n        # ⚠⚠ v2935 — NOT FINDING THE TABLE IS NOT FINDING NOTHING WRONG. The first cut returned\n        # all-zero counters here, so `--audit` saw `unknown == 0` and exited 0: the command whose\n        # whole job is to refuse an unbound table was VACUOUSLY GREEN whenever it could not find\n        # the table — a renamed header, a drifted TABLE_HEAD, a truncated file. MEASURED: a\n        # TASKS.md holding only the ship table printed "0 row(s) in the version table" and exited\n        # 0. That is [[zero-needs-a-denominator]] in the tool written to close exactly that shape.\n        return {"counts": dict(counts, rows=None, shaCellsBefore=None, shaCellsAfter=None,\n                               knownVersions=len(known)), "changed": [], "wrote": False,\n                "why": "the version table header was not found (or its |---| rule line is "\n                       "missing), so NOTHING here was examined — this is UNMEASURED, not a table "\n                       "with nothing unbound"}\n',
        "replace": '    if False:\n        return None\n',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
