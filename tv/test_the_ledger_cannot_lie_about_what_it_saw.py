#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2808 — THREE WAYS THE SECOND-EYE LEDGER MISREPORTED ITS OWN LOOKS.

This ledger exists for one reason: so a thin look can never be filed as a thorough one. Measured
tonight, it was failing at that in three independent ways at once, and each hid the next.

1. THE CALLER AND THE LEDGER DISAGREED ABOUT `sent`. `second_eye_run` computes
   `sent = code_was_transmitted(prompt)` — already a measurement — and `record()` re-measured that
   DICT, which carries no code fence, producing {"chars": 0, "fences": 0}. That is BYTE-IDENTICAL
   to what `sent=None` produces, and `sent=None` is defined by the docstring as "NOBODY CHECKED".
   So "the whole diff was transmitted" and "nobody passed the prompt in" became the same row.
   Ledger census: 417 rows, 20 with a sentCode, 9 of them zero — every look taken through the real
   path — and the 11 healthy ones ALL written by the test, which passes a raw fence. The gate was
   green because it exercised a shape production never used.

2. THE UNSENT DETECTOR FIRED ON EVERY DIFF. Its seam patterns let `\\s*` cross a newline, and in a
   unified diff every added line begins with `+`. So an added docstring reads as `+\"\"\"` and a
   docstring above an added line reads as `\"\"\"\\n+import os`. Measured on the v2807 payload: 24
   hits, ALL ordinary Python docstrings beside a diff marker, ZERO genuine seams. A non-empty
   `unsent` RETRACTS the row, and a version cannot ship while the previous one has never been
   looked at — so this would have deadlocked the repo shut. It was invisible only because defect 1
   was reporting zero fences; fixing that fired it immediately.

3. A CLEAN LOOK WAS FILED AS ONE THAT FOUND DEFECTS. `_findings_from` folds an unenumerated answer
   into a single block, so "No defects found." was recorded as findings=[<the whole answer>] with
   verdict="findings" — the ledger reporting the opposite of what the other family concluded.

★ THE ORDER MATTERS AND IS THE LESSON. Defect 1 masked defect 2 completely. A fix that "worked"
would have shipped a repo that could never ship again. [[two-fixes-broke-each-other]]
[[feedback-suspect-the-instrument]] [[feedback-blind-fixture-green-gate]]
"""
import io
import json
import os
import shutil
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import second_eye_ledger as L  # noqa: E402
import second_eye_run as R  # noqa: E402

# ⚠⚠ THE LEDGER PATH IS REDIRECTED BEFORE ANY TEST RUNS, AND THIS IS NOT OPTIONAL.
# `record()` APPENDS. The first run of this file wrote three v0000 rows straight into the real
# `.second_eye.jsonl` — a fixture writing into live evidence, inside the gate written to make that
# evidence trustworthy. Caught by counting the rows afterwards, which is the only reason it did not
# ship. Guard the FIXTURE, not the call site. [[feedback-fixtures-never-touch-live-data]]
import tempfile  # noqa: E402

_TMP = tempfile.mkdtemp(prefix="second_eye_gate.")
L.LEDGER_PATH = os.path.join(_TMP, "ledger.jsonl")
assert not os.path.exists(L.LEDGER_PATH), "the scratch ledger already exists"

# A real unified-diff fence: added lines carry '+', docstrings are ordinary Python.
DIFF_FENCE = (
    "review this\n```diff\n"
    '+"""v2807 - a module docstring on an added line.\n'
    '+"""\n'
    "+import os\n"
    "+\n"
    "+def f():\n"
    '+    """-> [(file, line)] every call in production code."""\n'
    "+    return []\n"
    "```\n"
)

# The defect the detector exists for: a fence holding the EXPRESSION, not the file.
REAL_SEAM = (
    "review this\n```python\n"
    'PROMPT = """header\n""" + open("control_app.py").read() + """footer"""\n'
    "```\n"
)


class TestTheLedgerCannotLieAboutWhatItSaw(unittest.TestCase):

    # ── 1. the contract ──────────────────────────────────────────────────────────────────────
    def test_a_measured_dict_is_not_the_same_as_nobody_checking(self):
        measured = L.code_was_transmitted(DIFF_FENCE)
        self.assertGreater(measured["chars"], 0, "the fixture carries no code")
        row = L.record(version="v0000", model="t", verdict="clean", findings=[],
                       asked="x", answer_head="y", sent=measured)
        self.assertIsNotNone(row.get("sentCode"),
                             "a measured dict recorded as None — indistinguishable from unchecked")
        self.assertEqual(row["sentCode"]["chars"], measured["chars"],
                         "the ledger re-measured the dict instead of trusting it: %r"
                         % (row["sentCode"],))

    def test_raw_text_still_works(self):
        row = L.record(version="v0000", model="t", verdict="clean", findings=[],
                       asked="x", answer_head="y", sent=DIFF_FENCE)
        self.assertGreater(row["sentCode"]["chars"], 0,
                           "passing the prompt TEXT no longer measures it")

    def test_an_unrecognised_type_is_none_not_zero(self):
        row = L.record(version="v0000", model="t", verdict="clean", findings=[],
                       asked="x", answer_head="y", sent=12345)
        self.assertIsNone(row.get("sentCode"),
                          "an unmeasurable value recorded as a number — a zero with no denominator")

    # ── 2. the detector ──────────────────────────────────────────────────────────────────────
    def test_a_unified_diff_is_not_an_unsent_seam(self):
        m = L.code_was_transmitted(DIFF_FENCE)
        self.assertEqual(m["unsent"], [],
                         "a plain diff trips the unsent detector %r — every code review would be "
                         "RETRACTED, and no version could ship while the previous one is retracted"
                         % (m["unsent"],))

    def test_the_genuine_seam_is_still_caught(self):
        m = L.code_was_transmitted(REAL_SEAM)
        self.assertGreaterEqual(len(m["unsent"]), 2,
                                "the real un-evaluated seam is no longer detected — the fix for "
                                "the false positives went too far and disarmed the check")

    # ── 3. the verdict ───────────────────────────────────────────────────────────────────────
    def test_a_declared_clean_answer_is_recorded_clean(self):
        v, f = R._verdict_for("**No defects found.** Reviewed for races and leaks. Nothing real.",
                              ["one folded block"])
        self.assertEqual(v, "clean", "a 'no defects found' answer filed as findings")
        self.assertEqual(f, [], "a clean answer still carries findings")

    def test_a_declaration_can_never_bury_an_enumerated_list(self):
        v, f = R._verdict_for("No defects found.\n1. a race in x\n2. a leak in y\n3. bad state",
                              ["1. a race in x", "2. a leak in y", "3. bad state"])
        self.assertEqual(v, "findings",
                         "a model that says 'no defects' and then lists three was recorded clean "
                         "— that is a hole a real finding falls through")
        self.assertEqual(len(f), 3, "the enumerated findings were dropped")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════

class TestAVersionWithNoRowIsOwedByBothCommands(unittest.TestCase):
    """`--audit` walked the LEDGER only, so a version nobody ever recorded anything for did not
    appear at all — while `--check` refuses it by name.

    MEASURED before the fix: --audit listed 5 OWED and NOT v3156, whose own --check says "nothing
    was ever recorded for it". audit() is the command the gate's refusal message tells him to run,
    so the screen he reads WHEN HE IS ALREADY BLOCKED was the one screen that could not show the
    block. The file's own v2145 note records the same two commands contradicting each other in
    both directions, and the test written to close it never called audit().
    [[zero-needs-a-denominator]] [[the-unjoined-end]]"""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)
        # a ledger that knows v1000 and has NEVER heard of v1001
        self.led = os.path.join(self.d, "ledger.jsonl")
        with io.open(self.led, "w", encoding="utf-8") as _fh:
            _fh.write(json.dumps({
            "version": "v1000", "model": "grok-4-1-fast-reasoning", "family": "xai",
            "reached": True, "findings": "a real look", "verdict": "findings",
                "bytes": {"bible": "abc"}}) + "\n")
        self.tasks = os.path.join(self.d, "TASKS.md")
        with io.open(self.tasks, "w", encoding="utf-8") as _fh:
            _fh.write(
            "| version | commit | commit subject |\n|---|---|---|\n"
            "| **v1001** | `(this commit)` | v1001 - shipped and never looked at |\n"
            "| **v1000** | `(this commit)` | v1000 - shipped and looked at |\n")

    def test_the_ship_table_is_parsed_at_all(self):
        got, ok = L._shipped_versions(self.tasks)
        self.assertEqual(got, {"v1000", "v1001"},
                         "the ship table parsed as %r — if this returns nothing the seeding is a "
                         "no-op and every assertion below passes for the wrong reason" % (got,))
        self.assertTrue(ok, "a readable ship table reported itself unreadable")

    def test_a_shipped_version_with_no_row_is_listed_as_OWED(self):
        rows = L.audit(self.led, self.tasks)
        names = dict((r["version"], r) for r in rows)
        self.assertIn("v1001", names,
                      "v1001 shipped and carries NO ledger row, and audit did not list it at all. "
                      "Invisible is worse than owed: only one of them can be acted on. Listed: %r"
                      % (sorted(names),))
        self.assertEqual(names["v1001"]["looks"], 0)
        self.assertEqual(names["v1000"]["looks"], 1, "the real look was lost while adding the gap")

    def test_check_and_audit_agree_on_the_rowless_version(self):
        """The contradiction this file's own v2145 scar is about, asked from BOTH sides."""
        rows = dict((r["version"], r) for r in L.audit(self.led, self.tasks))
        audit_owes = rows.get("v1001", {}).get("looks", 0) == 0
        # looked_at returns the ROWS it found; empty means nobody ever looked.
        check_owes = not L.looked_at("v1001", self.led)
        self.assertEqual(audit_owes, check_owes,
                         "audit says owed=%s and check says owed=%s for a version with no row. "
                         "One rule, asked from both." % (audit_owes, check_owes))
        self.assertTrue(audit_owes, "neither command refused a version nobody ever looked at")


    def test_an_EMPTY_ledger_owes_everything_rather_than_nothing(self):
        """Found by the Codex eye on v3157 — the same defect one level down. A None floor seeded
        NOTHING, so a ledger with no rows listed no versions at all. When nobody has ever looked at
        anything, EVERY shipped version owes a look and the screen must say so."""
        empty = os.path.join(self.d, "empty.jsonl")
        io.open(empty, "w", encoding="utf-8").write("")
        got = sorted(r["version"] for r in L.audit(empty, self.tasks))
        self.assertEqual(got, ["v1000", "v1001"],
                         "an empty ledger listed %r. Zero rows is the state where EVERYTHING is "
                         "owed, and it printed the same screen as 'all clear'." % (got,))

    def test_the_era_bound_orders_versions_by_NUMBER(self):
        """'v1000' >= 'v999' is FALSE as strings, so a four-digit version would be dropped the
        moment the counter rolled past v999 — silently, and only for the newest work."""
        led = os.path.join(self.d, "num.jsonl")
        io.open(led, "w", encoding="utf-8").write(json.dumps({
            "version": "v999", "model": "grok-4-1-fast-reasoning", "family": "xai",
            "reached": True, "findings": "x", "bytes": {"bible": "a"}}) + "\n")
        tasks = os.path.join(self.d, "num.md")
        io.open(tasks, "w", encoding="utf-8").write(
            "| version | commit | commit subject |\n|---|---|---|\n"
            "| **v1000** | `x` | a |\n| **v999** | `x` | b |\n")
        got = sorted(r["version"] for r in L.audit(led, tasks))
        self.assertIn("v1000", got,
                      "v1000 ships AFTER v999 and was dropped from the era: %r. The bound is "
                      "comparing digit strings, not versions." % (got,))

    def test_an_unreadable_ship_table_SAYS_SO_instead_of_seeding_nothing(self):
        """Found by the Codex eye on v3157, and it is the third time in this family. Returning an
        empty set for an unreadable table does not 'hide nothing' — it hides EVERYTHING, because
        audit then emits no row for a shipped version with no ledger data while --check still
        blocks it. A permission error or a bad tasks_path is enough."""
        got, ok = L._shipped_versions(os.path.join(self.d, "no_such_table.md"))
        self.assertEqual(got, set())
        self.assertFalse(ok,
                         "an unreadable ship table reported itself READ. The caller cannot tell "
                         "it apart from a table that is genuinely empty, so it cannot say so.")

    def test_the_ship_table_parser_has_no_digit_ceiling(self):
        """Its contract is 'every version ever recorded'; `v\\d{3,5}` gave it an expiry at
        v100000, after which a shipped version is silently ignored and never owed."""
        p = os.path.join(self.d, "six.md")
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write("| version | commit | commit subject |\n|---|---|---|\n"
                     "| **v100000** | `x` | a |\n")
        got, _ok = L._shipped_versions(p)
        self.assertIn("v100000", got,
                      "a six-digit shipped version parsed as %r — it would never be listed as "
                      "owed, and the contract says every version." % (got,))

    def test_two_audits_cannot_overwrite_each_other_s_ship_table_verdict(self):
        """Found by the Codex eye on v3160. The read status lived in a module global, which two
        concurrent audits race over: A reads an unreadable table and, before its caller prints, B
        reads a good one and flips the flag — so A omits the warning and hides exactly the rowless
        versions the seeding exists to surface. The inverse warns about a table that was fine."""
        empty = os.path.join(self.d, "empty2.jsonl")
        with io.open(empty, "w", encoding="utf-8") as fh:
            fh.write("")
        bad, good = {}, {}
        L.audit(empty, os.path.join(self.d, "no_such_table.md"), state=bad)
        L.audit(empty, self.tasks, state=good)
        self.assertEqual(bad.get("shipTableOk"), False,
                         "the unreadable read did not record itself: %r" % (bad,))
        self.assertEqual(good.get("shipTableOk"), True)
        self.assertEqual(bad.get("shipTableOk"), False,
                         "the SECOND audit overwrote the first one's verdict — that is the race, "
                         "and it silently drops the warning that keeps rowless versions visible")

    def test_no_module_global_carries_the_ship_table_verdict(self):
        """v3162 kept LAST_SHIP_TABLE_OK beside the per-call dict "for older callers". The Codex
        eye pointed out those callers still race; a grep found ZERO of them. A racy global kept for
        nobody is liability with no benefit, and the next caller to reach for it inherits the bug.

        ⚠ PARSED, NOT GREPPED — the module's own comment explains why the global is absent, so a
        substring test would be satisfied by the explanation. [[source-reading-guard]]"""
        import ast as _ast
        src = io.open(os.path.join(HERE, "second_eye_ledger.py"), encoding="utf-8").read()
        assigned = set()
        for node in _ast.parse(src).body:
            if isinstance(node, _ast.Assign):
                for t2 in node.targets:
                    if isinstance(t2, _ast.Name):
                        assigned.add(t2.id)
        self.assertNotIn(
            "LAST_SHIP_TABLE_OK", assigned,
            "the ship-table verdict is back in a module global, so two concurrent audits can "
            "overwrite each other's answer and the warning that keeps rowless versions visible "
            "lands on the wrong run or is lost")

RED_PROOF = [
    {
        "why": "puts the racy module global back, so any caller reaching for it inherits the "
               "cross-audit race the per-call dict was introduced to end",
        "file": "second_eye_ledger.py",
        "find": 'AUTHOR_FAMILY = "anthropic"',
        "replace": 'AUTHOR_FAMILY = "anthropic"\nLAST_SHIP_TABLE_OK = True',
        "matches": 1,
    },

    {
        "why": "hands the ship-table verdict back through a module global again, so two concurrent "
               "audits overwrite each other and the warning that keeps rowless shipped versions "
               "visible is attached to the wrong run or lost entirely",
        "file": "second_eye_ledger.py",
        "find": '    if isinstance(state, dict):\n        state["shipTableOk"] = _ship_ok',
        "replace": "    pass",
        "matches": 1,
    },

    {
        'why': 'an unreadable ship table reports itself READ, so the caller cannot tell it from a genuinely empty one and the audit silently hides every rowless shipped version',
        'file': 'second_eye_ledger.py',
        'find': '        return set(), False',
        'replace': '        return set(), True',
        'matches': 1,
    },
    {
        'why': 'puts the digit ceiling back, so the ship table quietly stops recognising versions at v100000 while its docstring still claims every version ever recorded',
        'file': 'second_eye_ledger.py',
        'find': '    return set(_re.findall(r"^\\|\\s*\\*\\*(v\\d{3,})\\*\\*\\s*\\|", src, _re.M)), True',
        'replace': '    return set(_re.findall(r"^\\|\\s*\\*\\*(v\\d{3,5})\\*\\*\\s*\\|", src, _re.M)), True',
        'matches': 1,
    },
    {
        'why': 'seeds nothing when the ledger is empty, so the one state in which EVERY shipped version owes a look prints the same empty screen as all-clear',
        'file': 'second_eye_ledger.py',
        'find': '        if _floor is None or _vnum(v) >= _floor:',
        'replace': '        if _floor is not None and _vnum(v) >= _floor:',
        'matches': 1,
    },
    {
        'why': "orders the era bound by STRING again, so 'v1000' < 'v999' and every four-digit version silently falls outside the era the moment the counter rolls over",
        'file': 'second_eye_ledger.py',
        'find': '    _floor = min(_vnum(v) for v in _ledger_versions) if _ledger_versions else None',
        'replace': '    _floor = min(_ledger_versions) if _ledger_versions else None',
        'matches': 1,
    },
    {
        'why': "stops seeding audit() from the ship table, so a version nobody ever recorded anything for vanishes from the very screen the gate's refusal message tells him to run — invisible instead of owed, and only one of those can be acted on",
        'file': 'second_eye_ledger.py',
        'find': '    for v in _shipped:',
        'replace': '    for v in []:',
        'matches': 1,
    },
    {
        'why': 'restoring the re-measure makes a full diff and an unchecked look identical again',
        'file': 'second_eye_ledger.py',
        'find': '    elif isinstance(sent, dict):',
        'replace': '    elif isinstance(sent, dict) and False:',
        'matches': 1,
    },
    {
        'why': 'letting the seam pattern cross a newline re-arms the diff false positive',
        'file': 'second_eye_ledger.py',
        'find': '    (re.compile(r"\\S[ \\t]*\\+[ \\t]*(?:\\\'{3}|\\"{3})"), "a +/triple-quote concatenation seam reached the prompt as text"),',
        'replace': '    (re.compile(r"\\+\\s*(?:\\\'{3}|\\"{3})"), "a +/triple-quote concatenation seam reached the prompt as text"),',
        'matches': 1,
    },
    {
        'why': 'without the declaration check a clean look is filed as one that found defects',
        'file': 'second_eye_run.py',
        'find': '    if not enumerated and _NO_DEFECT_RX.search(answer or ""):',
        'replace': '    if False:',
        'matches': 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
