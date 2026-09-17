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
        # ⚠⚠ v3216 — THIS FIXTURE WAS UNREACHABLE AND THE GATE HAS BEEN RED ON ORIGIN BECAUSE OF
        # IT. It handed `findings=["one folded block"]` — a placeholder that does NOT contain the
        # declaration — while the rule deliberately requires the clean declaration to be
        # `findings[0]`. That requirement is the safe half: a declaration ANYWHERE plus one listed
        # P1 was once filed CLEAN, which is the direction this whole file exists to prevent, so
        # `opens_clean` reads the FIRST block on purpose. `_findings_from` always puts the opening
        # sentence first, so the real shape is the one asserted here.
        # A/B'd against HEAD before touching it: HEAD returns "findings" too — this is a
        # pre-existing red, not a regression. [[ab-against-head-before-blaming-the-room]]
        clean = "**No defects found.** The change is consistent with its callers."
        v, f = R._verdict_for(clean, [clean])
        self.assertEqual(v, "clean", "a 'no defects found' answer filed as findings")
        self.assertEqual(f, [], "a clean answer still carries findings")

    def test_naming_a_defect_class_it_looked_for_is_filed_as_findings_ON_PURPOSE(self):
        """⚠ A KNOWN, DELIBERATE OVER-REPORT — recorded so nobody "fixes" it into a hole.

        `_claims_a_defect` strips NEGATED spans and then looks for defect vocabulary. It cannot
        tell *"Reviewed for races and leaks"* — a statement about the SEARCH — from *"there is a
        race"*. So a clean answer that lists what it looked FOR is filed `findings`.

        That is the SAFE direction and it stays. Teaching the stripper to swallow
        "reviewed for X" risks swallowing "reviewed for races AND FOUND ONE", and this detector
        exists to never miss a claim. The cost is a noisy row; the cost of the other error is a
        real P1 filed as clean, which this file was written after. [[unknown-stays-unknown]]
        """
        mixed = "**No defects found.** Reviewed for races and leaks. Nothing real."
        v, _ = R._verdict_for(mixed, [mixed])
        self.assertEqual("findings", v,
                         "the claim detector stopped seeing defect vocabulary outside a negated "
                         "span — check what else it stopped seeing before calling that a fix")

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
        # ⚠⚠ EVERY WRITE SHAPE, NOT JUST THE TIDY ONE. The Codex eye on v3164: this checked only a
        # top-level `NAME = ...`, while the form that CAUSED the bug was
        # `globals()["LAST_SHIP_TABLE_OK"] = _ship_ok` — a Subscript target, invisible to that
        # check and reachable from inside any function. A law that rejects the shape nobody wrote
        # and admits the shape that broke it is worse than none. Verified: the old check saw
        # {'AUTHOR_FAMILY'} and returned False on exactly that line.
        # ⚠⚠ v3193 — THE WALKER PROVES ITSELF FIRST, BECAUSE THE SUBJECT CANNOT PROVE IT.
        # The heart caught this one BLIND: deleting the tuple-flattening below changed nothing,
        # because second_eye_ledger.py happens to contain no tuple-target assignment today. The
        # branch guarding the exact shape that caused the bug was therefore unexercised — a
        # detector nobody can tell from a broken one. So the walk runs on a SYNTHETIC source
        # carrying every write shape it claims to see, and must find all of them, before it is
        # trusted on the real file. [[gate-blind-to-unexercised-input]]
        _PROBE = (
            "PLAIN = 1\n"
            "globals()['SUBSCRIPT'] = 2\n"
            "globals()['IN_TUPLE'], _x = 3, None\n"
            "[IN_LIST, _y] = [4, None]\n"
        )

        def _walk(source):
            out = set()
            for node in _ast.walk(_ast.parse(source)):
                targets = []
                if isinstance(node, _ast.Assign):
                    targets = list(node.targets)
                elif isinstance(node, (_ast.AugAssign, _ast.AnnAssign)):
                    targets = [node.target]
                flat = []
                for t2 in targets:
                    if isinstance(t2, (_ast.Tuple, _ast.List)):
                        flat.extend(t2.elts)
                    else:
                        flat.append(t2)
                for t2 in flat:
                    if isinstance(t2, _ast.Name):
                        out.add(t2.id)
                    elif isinstance(t2, _ast.Subscript):
                        k = t2.slice
                        if isinstance(k, getattr(_ast, "Index", ())):
                            k = k.value
                        if isinstance(k, _ast.Constant) and isinstance(k.value, str):
                            out.add(k.value)
            return out

        _seen = _walk(_PROBE)
        print("   walker self-test found: %s" % sorted(_seen))
        for shape in ("PLAIN", "SUBSCRIPT", "IN_TUPLE", "IN_LIST"):
            self.assertIn(shape, _seen,
                          "the walker cannot see a %s target, so every verdict it gives about "
                          "the real file below is worth nothing" % shape)

        written = set()
        for node in _ast.walk(_ast.parse(src)):
            targets = []
            if isinstance(node, _ast.Assign):
                targets = list(node.targets)
            elif isinstance(node, (_ast.AugAssign, _ast.AnnAssign)):
                targets = [node.target]
            # ⚠ FLATTEN TUPLE AND LIST TARGETS. Found by the Codex eye on v3166:
            # `globals()["LAST_SHIP_TABLE_OK"], _ = _ship_ok, None` restores the race while a
            # check that only looks at direct Name/Subscript targets stays green.
            flat = []
            for t2 in targets:
                if isinstance(t2, (_ast.Tuple, _ast.List)):
                    flat.extend(t2.elts)
                else:
                    flat.append(t2)
            for t2 in flat:
                if isinstance(t2, _ast.Name):
                    written.add(t2.id)
                elif isinstance(t2, _ast.Subscript):
                    # ⚠ `getattr(slice, "value", slice)` was WRONG and green: on an ast.Constant
                    # that returns the constant's STRING, so the isinstance(Constant) below never
                    # matched and the check still missed globals()["X"] = ... . Driving it against
                    # the historical line is the only reason I know — it printed False.
                    # ⚠ ONLY A globals() SUBSCRIPT IS A MODULE GLOBAL. Its other finding: this
                    # treated EVERY obj["LAST_SHIP_TABLE_OK"] as global, so a correct per-call
                    # `state["LAST_SHIP_TABLE_OK"] = v` would fail this law on the strength of the
                    # field NAME alone — blocking the very shape the fix is built on.
                    _base = t2.value
                    _is_globals = (isinstance(_base, _ast.Call)
                                   and getattr(_base.func, "id", "") == "globals")
                    if not _is_globals:
                        continue
                    k = t2.slice
                    if k.__class__.__name__ == "Index":          # py < 3.9
                        k = k.value
                    if isinstance(k, _ast.Constant) and isinstance(k.value, str):
                        written.add(k.value)
        self.assertNotIn(
            "LAST_SHIP_TABLE_OK", written,
            "the ship-table verdict is written to a module global again (as a bare assignment, an "
            "annotated one, or through globals()[...]), so two concurrent audits can overwrite "
            "each other's answer and the warning that keeps rowless versions visible lands on the "
            "wrong run or is lost")

    def test_the_guard_sees_a_TUPLE_target_and_spares_per_call_state(self):
        """Both from the Codex eye on v3166. A guard that only looks at direct Name/Subscript
        targets is walked around by `globals()["X"], _ = v, None`; a guard that treats EVERY
        obj["X"] as global fails a correct `state["X"] = v` on the strength of the field NAME."""
        import ast as _ast

        def _written(src):
            out = set()
            for node in _ast.walk(_ast.parse(src)):
                targets = []
                if isinstance(node, _ast.Assign):
                    targets = list(node.targets)
                elif isinstance(node, (_ast.AugAssign, _ast.AnnAssign)):
                    targets = [node.target]
                flat = []
                for t2 in targets:
                    if isinstance(t2, (_ast.Tuple, _ast.List)):
                        flat.extend(t2.elts)
                    else:
                        flat.append(t2)
                for t2 in flat:
                    if isinstance(t2, _ast.Name):
                        out.add(t2.id)
                    elif isinstance(t2, _ast.Subscript):
                        b = t2.value
                        if not (isinstance(b, _ast.Call)
                                and getattr(b.func, "id", "") == "globals"):
                            continue
                        k = t2.slice
                        if k.__class__.__name__ == "Index":
                            k = k.value
                        if isinstance(k, _ast.Constant) and isinstance(k.value, str):
                            out.add(k.value)
            return out

        N = "LAST_SHIP_TABLE_OK"
        self.assertIn(N, _written('def f():\n    globals()["%s"], _ = 1, 2\n' % N),
                      "a TUPLE target walked around the guard and the race came back green")
        self.assertIn(N, _written('def f():\n    globals()["%s"] = 1\n' % N))
        self.assertIn(N, _written('%s = 1\n' % N))
        self.assertNotIn(N, _written('def f(state):\n    state["%s"] = 1\n' % N),
                         "a correct PER-CALL state dict was rejected because of the field name — "
                         "the guard would block the very shape the fix is built on")

RED_PROOF = [
    {
        "why": 'v3193 — the walker must prove itself before it judges anything. The old anchor '
               'deleted the flattening in the REAL walk, which changed nothing because '
               'second_eye_ledger.py carries no tuple target today: BLIND. Its replacement then '
               'matched TWICE, because this file holds three walkers. This one breaks the '
               "SELF-TEST's walk outright, so the synthetic probe carrying every write shape can "
               'no longer be read and the walker fails before it is trusted',
        "file": 'test_the_ledger_cannot_lie_about_what_it_saw.py',
        # ⚠ MATCHES 2, AND THAT IS CORRECT RATHER THAN SLOPPY. This proof targets its OWN
        # file, so the anchor occurs twice: once in the code it breaks and once inside this
        # declaration, which necessarily quotes it. A proof that pointed at itself and claimed
        # ONE match was rejected as INVALID — rightly, because an uncounted occurrence is an
        # uncontrolled tamper.
        "find": '            for node in _ast.walk(_ast.parse(source)):',
        "replace": '            for node in []:',
        "matches": 2,
    },
    {'why': 'puts the verdict back in a module global in the EXACT historical shape — globals()[...] inside audit() — which the first version of this law could not see at all, so the race returns while the guard stays green', 'file': 'second_eye_ledger.py', 'find': '    if isinstance(state, dict):\n        state["shipTableOk"] = _ship_ok', 'replace': '    globals()["LAST_SHIP_TABLE_OK"] = _ship_ok', 'matches': 1},
    {'why': 'hands the ship-table verdict back through a module global again, so two concurrent audits overwrite each other and the warning that keeps rowless shipped versions visible is attached to the wrong run or lost entirely', 'file': 'second_eye_ledger.py', 'find': '    if isinstance(state, dict):\n        state["shipTableOk"] = _ship_ok', 'replace': '    pass', 'matches': 1},
    {'why': 'an unreadable ship table reports itself READ, so the caller cannot tell it from a genuinely empty one and the audit silently hides every rowless shipped version', 'file': 'second_eye_ledger.py', 'find': '        return set(), False', 'replace': '        return set(), True', 'matches': 1},
    {'why': 'puts the digit ceiling back, so the ship table quietly stops recognising versions at v100000 while its docstring still claims every version ever recorded', 'file': 'second_eye_ledger.py', 'find': '    return set(_re.findall(r"^\\|\\s*\\*\\*(v\\d{3,})\\*\\*\\s*\\|", src, _re.M)), True', 'replace': '    return set(_re.findall(r"^\\|\\s*\\*\\*(v\\d{3,5})\\*\\*\\s*\\|", src, _re.M)), True', 'matches': 1},
    {'why': 'seeds nothing when the ledger is empty, so the one state in which EVERY shipped version owes a look prints the same empty screen as all-clear', 'file': 'second_eye_ledger.py', 'find': '        if _floor is None or _vnum(v) >= _floor:', 'replace': '        if _floor is not None and _vnum(v) >= _floor:', 'matches': 1},
    {'why': "orders the era bound by STRING again, so 'v1000' < 'v999' and every four-digit version silently falls outside the era the moment the counter rolls over", 'file': 'second_eye_ledger.py', 'find': '    _floor = min(_vnum(v) for v in _ledger_versions) if _ledger_versions else None', 'replace': '    _floor = min(_ledger_versions) if _ledger_versions else None', 'matches': 1},
    {'why': "stops seeding audit() from the ship table, so a version nobody ever recorded anything for vanishes from the very screen the gate's refusal message tells him to run — invisible instead of owed, and only one of those can be acted on", 'file': 'second_eye_ledger.py', 'find': '    for v in _shipped:', 'replace': '    for v in []:', 'matches': 1},
    {'why': 'restoring the re-measure makes a full diff and an unchecked look identical again', 'file': 'second_eye_ledger.py', 'find': '    elif isinstance(sent, dict):', 'replace': '    elif isinstance(sent, dict) and False:', 'matches': 1},
    {'why': 'letting the seam pattern cross a newline re-arms the diff false positive', 'file': 'second_eye_ledger.py', 'find': '    (re.compile(r"\\S[ \\t]*\\+[ \\t]*(?:\\\'{3}|\\"{3})"), "a +/triple-quote concatenation seam reached the prompt as text"),', 'replace': '    (re.compile(r"\\+\\s*(?:\\\'{3}|\\"{3})"), "a +/triple-quote concatenation seam reached the prompt as text"),', 'matches': 1},
    {'why': 'without the declaration check a clean look is filed as one that found defects', 'file': 'second_eye_run.py', 'find': '    if not decl_anywhere:', 'replace': '    if False:', 'matches': 1},
    # ⚠ v3240 — the line above was RE-ANCHORED. The clean-look branch was restructured into
    # decl_anywhere / opens_clean, so the old anchor named a line that no longer exists and the
    # tamper matched 0 times. A proof that changes nothing proves nothing — and it sat that way
    # unseen, because heart2 could not read 32 of its siblings and aborted before reaching it.
]

class TheRowNamesWhoActuallyLooked(unittest.TestCase):
    """⚠⚠ THREE OPENAI LOOKS WERE FILED AS family=xai, AND THE ECHO WAS COUNTED AS FINDINGS.

    This file's own premise is that `family` is derived from the model id rather than asserted,
    "because a same-family agent writing plausible strings must never be mistakable for a
    cross-family look". The derivation was right and its INPUT was a guess: `--answer-in` recorded
    `model=EYE_MODEL`, which is the configured GROK default, no matter who produced the answer.
    MEASURED 2026-09-16 — v3214, v3215 and v3216 were all answered by `gpt-5.6-terra` and all three
    rows said **family=xai**. The ledger was asserting a Grok seat that was never occupied.

    And the same path counted the tool's PROMPT ECHO as findings: `codex exec` prints the whole
    payload, diff included, before replying, so every handoff row carried exactly **12** findings
    (the cap) reading `'--- a/tv/control_app.py'`, and a reply of *"No concrete functional defect
    is evident"* was filed `verdict=findings`. A constant is not a measurement.
    [[unknown-stays-unknown]] [[zero-needs-a-denominator]] [[feedback-suspect-the-instrument]]
    """

    def test_the_model_is_read_from_the_answer_not_the_config(self):
        import second_eye_run as S
        got = S._model_from_answer("workdir: /x\nmodel: gpt-5.6-terra\nprovider: openai\n")
        self.assertEqual("gpt-5.6-terra", got,
                         "the model the tool NAMED in its own output is not being read, so the "
                         "row inherits whatever THIRD_EYE_MODEL happens to be")

    def test_an_unattributable_answer_does_not_claim_a_family(self):
        import second_eye_run as S
        self.assertIsNone(S._model_from_answer("here is my review, I found two things"),
                          "a model id is being invented for an answer that never named one — an "
                          "unattributable look must not discharge a cross-family debt")

    def test_the_echoed_prompt_is_not_counted_as_findings(self):
        import second_eye_run as S
        prompt = "Code review. Judge only what is shown.\n```diff\n--- a/tv/control_app.py\n```"
        answer = prompt + "\n\ncodex\nNo defects are evident in this diff."
        out = S._strip_echo(answer, prompt)
        self.assertNotIn("--- a/tv/control_app.py", out,
                         "the echoed diff survives into the answer, so its lines get split into "
                         "findings and the count becomes the cap rather than a measurement")
        self.assertTrue(out.startswith("No defects"),
                        "the reply is not what remains after stripping: %r" % out[:60])

    def test_ansi_does_not_hide_a_clean_declaration(self):
        import second_eye_run as S
        prompt = "Code review."
        answer = prompt + "\n\x1b[35m\x1b[3mcodex\x1b[0m\nNo concrete functional defect is evident here."
        out = S._strip_echo(answer, prompt)
        self.assertTrue(S._NO_DEFECT_RX.search(out),
                        "a clean declaration behind terminal colour bytes is unreadable, so a "
                        "clean answer is filed as findings: %r" % out[:70])

    def test_a_real_finding_is_still_not_clean(self):
        """The direction that must never break: over-reporting is survivable, this is not."""
        import second_eye_run as S
        bad = ["1. **High** — the endpoint uses bool(), so a body saying false authorises a write.",
               "2. **Medium** — names has no type validation and a string is iterated per character."]
        verdict, kept = S._verdict_for("I found two concrete regressions. " + " ".join(bad), bad)
        self.assertEqual("findings", verdict,
                         "two enumerated defects were filed as CLEAN — that is the direction this "
                         "whole file exists to prevent")
        self.assertEqual(2, len(kept))


class AProviderRefusalIsAnEmptySeat(unittest.TestCase):
    """⚠⚠⚠ AN EMPTY SEAT SIGNED THE REGISTER, AND THE PUSH GATE READS `reached`.

    v3216 taught `record_answer` to strip the tool's echoed prompt and left the emptiness guard
    ABOVE the strip, reading raw bytes. `codex exec` prints the whole payload before replying, so a
    run whose ONLY reply was **"ERROR: You've hit your usage limit … try again at Oct 12th"**
    arrived as ~10,000 characters and sailed past `len(answer) < 40`. v3217 and v3218 were both
    filed as **LOOKED**. The ledger's whole premise is that an unreachable eye is an EMPTY SEAT and
    never agreement — and `pre-push` blocks on `reached`, so a false LOOKED opens a gate that
    should have stayed shut.

    ⚠ AND THE FIX HAD A TWIN IT DID NOT COVER: `run_one`'s CLI door recorded inline and never
    called `record_answer`, so the same false LOOKED stayed live on the DEFAULT door until v3221
    routed both through one guard. Found by the Grok seat reviewing the very version that fixed
    the other half. [[copy-drift]] [[unknown-stays-unknown]]
    """

    def setUp(self):
        sys.path.insert(0, HERE)
        import second_eye_run as S
        self.S = S

    def test_a_usage_limit_reply_is_not_a_look(self):
        S = self.S
        prompt = "Code review. Judge only what is shown.\n```diff\n--- a/tv/x.py\n```"
        answer = prompt + ("\nERROR: You've hit your usage limit. Upgrade to Plus to continue "
                           "using Codex (https://chatgpt.com/explore/plus), or try again at "
                           "Oct 12th, 2026 4:36 PM")
        reply = S._strip_echo(answer, prompt)
        self.assertTrue(S._PROVIDER_ERROR_RX.search(reply[:400]),
                        "a usage-limit refusal is not recognised as a provider error, so it will "
                        "be recorded as a LOOK and discharge a cross-family debt nobody paid: %r"
                        % reply[:90])

    def test_the_length_test_alone_cannot_catch_it(self):
        """The reason a size guard is not enough — this is why it must run AFTER the strip."""
        S = self.S
        prompt = "x" * 9000
        answer = prompt + "\nERROR: You've hit your usage limit."
        self.assertGreater(len(answer), 40,
                           "the fixture no longer reproduces the shape: the whole point is that "
                           "the RAW answer is long while the REPLY is a refusal")
        self.assertLess(len(S._strip_echo(answer, prompt)), 200,
                        "the echo is not being stripped, so the guard still judges the prompt")

    def test_auth_and_unsupported_model_refusals_count_too(self):
        S = self.S
        for body in ("ERROR: The 'gpt-6-astra' model is not supported when using Codex with a "
                     "ChatGPT account.",
                     "error: rate-limited, try later",
                     "Please sign in to continue"):
            self.assertTrue(S._PROVIDER_ERROR_RX.search(body),
                            "%r is not recognised as a provider refusal" % body[:60])

    def test_a_real_review_is_still_a_look(self):
        """⚠⚠ THE DIRECTION THAT MUST NOT BREAK, AND MY FIRST FIXTURE DODGED IT.

        v3220 matched "quota" / "unauthor" / "authentication" / "rate-limit" ANYWHERE in the reply,
        so a genuine review saying *"authentication is not checked"* would be discarded as a
        provider refusal. A cross-family look named it and pointed out that a review OF THAT VERY
        DIFF would trip it — my fixture passed only because it happened to avoid the words.
        Over-refusing is the worse of the two errors: a false LOOKED is visible in the ledger, a
        real look thrown away is not. The fixture now USES the vocabulary on purpose.
        """
        S = self.S
        for good in (
            "I found two concrete defects. 1. **High** — authentication is not checked on the "
            "endpoint, so an unauthorised caller can write. 2. **Medium** — the quota is never "
            "decremented and the rate-limit path is dead code no test exercises.",
            "No concrete functional defect is evident in this diff.",
            "The rate-limit handler never decrements the quota.",
        ):
            self.assertIsNone(S._PROVIDER_ERROR_RX.match(good.lstrip()),
                              "a genuine review is read as a provider refusal, so a real look is "
                              "discarded and the debt looks unpaid: %r" % good[:70])

    def test_the_recorder_itself_files_a_refusal_as_unreached(self):
        """⚠ DRIVE `record_answer`, not its helpers. The other tests call `_strip_echo` and the
        regex directly; if the RECORDER stopped consulting them, every one would stay green.
        Named by the same cross-family look. [[the-unjoined-end]]"""
        S = self.S
        rows = []
        real = S.SEL.record
        try:
            S.SEL.record = lambda **kw: rows.append(kw)
            prompt = "Code review. Judge only what is shown.\n```diff\n--- a/tv/x.py\n```"
            answer = prompt + "\nERROR: You've hit your usage limit. Try again Oct 12th."
            out = S.record_answer("v9999", answer, sent=1, prompt_text=prompt)
        finally:
            S.SEL.record = real
        self.assertFalse(out, "record_answer reported a LOOK over a provider refusal")
        self.assertEqual(1, len(rows), "the recorder wrote %d rows, expected exactly 1" % len(rows))
        self.assertIs(False, rows[0].get("reached"),
                      "a provider refusal was recorded with reached=%r — the push gate reads that "
                      "field, so this opens a gate that should stay shut" % rows[0].get("reached"))
        self.assertEqual([], rows[0].get("findings") or [],
                         "a refusal was recorded WITH findings, which is the echo being counted")

    def test_the_recorder_files_a_real_review_as_a_look(self):
        """The mirror, driven through the recorder for the same reason."""
        S = self.S
        rows = []
        real = S.SEL.record
        try:
            S.SEL.record = lambda **kw: rows.append(kw)
            prompt = "Code review.\n```diff\n--- a/tv/x.py\n```"
            answer = (prompt + "\nI found one defect. 1. **High** — authentication is not checked, "
                      "so an unauthorised caller can write past the quota.")
            out = S.record_answer("v9999", answer, sent=1, prompt_text=prompt)
        finally:
            S.SEL.record = real
        self.assertTrue(out, "a genuine review was filed as an empty seat")
        self.assertIs(True, rows[0].get("reached"),
                      "a real look was recorded unreached, so its cross-family debt stays unpaid")

    def test_both_doors_use_the_one_recorder(self):
        """copy-drift: v3220 fixed record_answer while the CLI door recorded inline."""
        import inspect
        src = inspect.getsource(self.S.run_one)
        self.assertNotIn("reached=True", src,
                         "run_one records a LOOK inline again, bypassing the echo strip and the "
                         "provider-error check that live in record_answer")
        self.assertGreaterEqual(src.count("record_answer("), 2,
                                "the CLI door no longer routes through record_answer, so the two "
                                "paths can drift apart again")


if __name__ == "__main__":
    unittest.main(verbosity=2)
