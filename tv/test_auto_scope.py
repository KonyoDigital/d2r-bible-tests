#!/usr/bin/env python3
"""Guards for the scope registry. A promise about code is only worth the check behind it."""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import auto_scope as AS  # noqa: E402


class TestEveryAutomATICLaneIsDeclared(unittest.TestCase):
    """★ A lane nobody declared is a lane he cannot be told about — and the whole point is that he
    was told CANNOT TELL when a different model family was asked what these things touch."""

    def _roster_names(self):
        """The loop names control_app actually starts, read from the source rather than listed
        here — a hand-kept copy would drift the moment a loop is added, which is the one case this
        guard exists for."""
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            src = fh.read()
        end = src.index("for name, fn in roster:")
        start = src.rindex("roster = [", 0, end)
        seg = src[start:end]
        # v2293 — this used to slice a fixed 1,600 chars back from the loop, and the roster's own
        # comments outgrew it: the FIRST lane, tvd-chron-autoread, fell off the top and the guard
        # reported it as declared-but-not-running. A window measured in characters is a guard whose
        # reach shrinks every time someone documents a lane. [[source-reading-guard]]
        return set(re.findall(r'\("(tvd-[a-z0-9\-]+)"\s*,\s*_[a-z_]+\)', seg))

    def test_every_started_loop_has_a_scope(self):
        started = self._roster_names()
        self.assertTrue(started, "the roster could not be read — re-point this guard rather than "
                                 "leaving it green over nothing")
        missing = sorted(started - set(AS.LANES))
        self.assertEqual(missing, [], "these loops run without him and declare NO scope, so what "
                                      "they touch is unknowable from the console: %s" % missing)

    def test_no_scope_describes_a_loop_that_does_not_run(self):
        started = self._roster_names()
        ghosts = sorted(set(AS.LANES) - started)
        self.assertEqual(ghosts, [], "these lanes are declared but not in the roster — a promise "
                                     "about something that does not run is noise: %s" % ghosts)

    def test_every_lane_names_a_function(self):
        missing = sorted(set(AS.LANES) - set(AS.LANE_FN))
        self.assertEqual(missing, [], "declared with no function to check against: %s" % missing)


class TestThePromisesAreCHECKEDNotJustWritten(unittest.TestCase):
    def _ca(self):
        import importlib
        return importlib.import_module("control_app")

    def test_the_tree_is_clean_today(self):
        self.assertEqual(AS.check_declarations(self._ca()), [],
                         "a lane's own body contradicts its declared scope")

    def test_the_checker_CAN_FAIL_on_a_false_promise(self):
        """⚠ THE LAW THAT MAKES THE REST WORTH ANYTHING. A checker that cannot fail is decoration
        with a green tick — and this one WAS, at first: reading only the loop's own body, making
        the retention lane promise 'never deletes' produced no break at all. [[regression-guard]]"""
        ca = self._ca()
        old = dict(AS.LANES["tvd-eagle-watch"])
        AS.LANES["tvd-eagle-watch"] = dict(old, forbids=["delete"])
        AS.FORBIDDEN_CALLS["delete"] = AS.FORBIDDEN_CALLS["delete"] + ("_eagle_once",)
        try:
            bad = AS.check_declarations(ca)
        finally:
            AS.LANES["tvd-eagle-watch"] = old
            AS.FORBIDDEN_CALLS["delete"] = tuple(
                c for c in AS.FORBIDDEN_CALLS["delete"] if c != "_eagle_once")
        self.assertTrue(bad, "a lane promising it never does something its own body plainly does "
                             "produced no break — the checker is decoration")

    def test_a_declaration_pointing_at_MISSING_code_is_a_break(self):
        ca = self._ca()
        old = AS.LANE_FN["tvd-retention"]
        AS.LANE_FN["tvd-retention"] = "_no_such_loop_anywhere"
        try:
            bad = AS.check_declarations(ca)
        finally:
            AS.LANE_FN["tvd-retention"] = old
        self.assertTrue(any("does not exist" in b for b in bad),
                        "a promise about code nobody can find passed as a promise")


class TestReachabilityIsNEVERReportedAsAVerdict(unittest.TestCase):
    """⚠ THE CORRECTION THAT SHAPED THIS MODULE. A transitive walk said _drift_loop "reaches
    os.remove" after 59 functions. In a module this size nearly everything reaches everything, so
    that is not evidence — and shipping it as a broken promise would have been a false alarm of
    exactly the kind that teaches him to stop reading a warning. The direct body is CHECKED; the
    wider reach is MEASURED AND LABELLED UNVERIFIED, and the two never mix."""

    def _ca(self):
        import importlib
        return importlib.import_module("control_app")

    def test_reach_is_reported_separately_from_the_check(self):
        u = AS.unverified_reach(self._ca(), "tvd-version-drift")
        self.assertTrue(u["checked"])
        self.assertGreater(u["functions"], 1, "the walk found nothing to report")
        self.assertIn("reachability, not behaviour", u["note"])

    def test_reach_does_NOT_appear_in_check_declarations(self):
        ca = self._ca()
        bad = AS.check_declarations(ca)
        self.assertFalse([b for b in bad if "reaches" in b],
                         "reachability leaked back into the verdict — a lane would be reported as "
                         "breaking a promise because something 59 calls away can delete")

    def test_the_cli_says_what_it_did_NOT_audit(self):
        with io.open(os.path.join(HERE, "auto_scope.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("NOT audited", src,
                      "the report no longer says how much was left unchecked, so a partial check "
                      "reads as a whole one")
        self.assertIn("a promise nobody measured is not a promise", src)


class TestItReportsAndNeverActs(unittest.TestCase):
    def test_the_module_cannot_change_anything(self):
        """⚠ READ THE CODE, NOT THE TEXT. My first cut string-matched the file and went red on its
        own docstring and on the FORBIDDEN_CALLS table — the module NAMES os.remove as data it
        looks for, which is the opposite of calling it. A text scan cannot tell a mention from a
        call, and this module is built entirely out of mentions. [[feedback-comments-vs-code]]"""
        import ast
        with io.open(os.path.join(HERE, "auto_scope.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        called = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                f = node.func
                if isinstance(f, ast.Attribute):
                    base = getattr(f.value, "id", None)
                    called.add("%s.%s" % (base, f.attr) if base else f.attr)
                elif isinstance(f, ast.Name):
                    called.add(f.id)
        for forbidden in ("os.remove", "os.unlink", "shutil.rmtree", "open", "run", "Popen"):
            self.assertNotIn(forbidden, called,
                             "auto_scope must only DESCRIBE; it actually calls %r" % forbidden)

    def test_the_reports_only_check_can_itself_fail(self):
        """A guard that cannot go red is decoration — including this one."""
        import ast
        tree = ast.parse("import os\ndef f():\n    os.remove('/tmp/x')\n")
        called = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                base = getattr(node.func.value, "id", None)
                called.add("%s.%s" % (base, node.func.attr) if base else node.func.attr)
        self.assertIn("os.remove", called,
                      "the AST reader cannot even see a plain os.remove call")


class TestTheConsoleCanSayWhatRunsWithoutHim(unittest.TestCase):
    """v2293 — a module and a gate with no console surface is [[the-unjoined-end]]: built on both
    ends, joined to nothing. The cold read asked whether he could tell what the app would do on his
    behalf, so the answer has to reach the ONE surface, not just a test."""

    def _doctor(self):
        import console_doctor
        return console_doctor

    def test_the_check_is_registered_on_the_one_surface(self):
        D = self._doctor()
        names = [n for n, _ in D.CHECKS]
        self.assertIn("what runs without you", names,
                      "the lane scope is measured and never rendered — that is the unjoined end")

    def test_it_reports_MISSING_when_a_lane_contradicts_its_promise(self):
        D = self._doctor()
        real = AS.check_declarations
        try:
            AS.check_declarations = lambda mod: ["tvd-fake promises it never deletes, and calls os.remove("]
            state, msg = D._check_what_runs_without_him()
        finally:
            AS.check_declarations = real
        self.assertEqual(state, D.MISSING,
                         "a lane doing what it promised never to do must not read as ok")
        self.assertIn("tvd-fake", msg)

    def test_an_empty_declaration_set_is_UNKNOWN_not_ok(self):
        D = self._doctor()
        real = AS.LANES
        try:
            AS.LANES = {}
            state, msg = D._check_what_runs_without_him()
        finally:
            AS.LANES = real
        self.assertEqual(state, D.UNKNOWN,
                         "a reader that finds no lanes has failed; it has not found a clean tree")

    def test_it_names_which_lanes_can_delete(self):
        D = self._doctor()
        state, msg = D._check_what_runs_without_him()
        self.assertEqual(state, D.OK)
        self.assertIn("tvd-rolling-prune", msg,
                      "the deletion lane is the one he most needs named, so it may not be a count")


# ⚠ THIS CLASS SITS ABOVE THE `if __name__` GUARD ON PURPOSE, AND IT DID NOT THE FIRST TIME.
# It was appended with `cat >>`, which lands BELOW the runner — so under `python3 test_auto_scope.py`
# the interpreter exits inside unittest.main() and every class beneath it is NEVER DEFINED,
# while the suite still reports OK. The repo's own guard caught it on the push.
#
# ⚠ AND MY HAND-CHECK COULD NOT HAVE CAUGHT IT: `python3 -m unittest tv.test_auto_scope`
# IMPORTS the module rather than executing __main__, so all 20 tests ran and two sabotages went
# red — in a path that is not the one the defect lives in. A verification that cannot fail is
# not a verification. [[append-below-the-runner]]

class TestV2410RotatesIsACheckablePermissionNotAnExemption(unittest.TestCase):
    """⚠ A LANE MAY DELETE ITS OWN ARTEFACTS, BUT IT MUST SAY WHICH ONES AND HOW MANY IT KEEPS.

    `tvd-ledger-backup` declared `touches: "its own backup files"` AND `forbids: ["delete"]`, which
    cannot both be true of a lane that rotates its own backups — and it does: _ledger_snapshot_once
    keeps the newest _LEDGER_BACKUP_KEEP and os.remove()s the rest. The auditor had been reporting
    "something down there can delete" for it from a CLI nothing runs.

    ⚠ THE FIX WAS NOT TO DROP "delete" FROM ITS forbids. That would weaken a real guard to silence
    a TRUE alarm. A `rotates` clause is a PERMISSION WITH A SCOPE — a directory, a glob and a
    keep-count — and this class exists to stop it degenerating into the blanket exemption it was
    written to avoid.
    """

    def _ca(self):
        import control_app
        return control_app

    def test_every_rotates_clause_names_a_dir_a_glob_and_a_keep(self):
        import auto_scope as AS
        for lane, spec in sorted(AS.LANES.items()):
            rot = spec.get("rotates")
            if not rot:
                continue
            for field in ("dir", "glob", "keep", "why"):
                self.assertTrue(str(rot.get(field) or "").strip(),
                                "%s: a rotates clause without %r is a blanket exemption, which is "
                                "exactly what it must not be" % (lane, field))

    def test_a_rotates_clause_names_constants_that_EXIST(self):
        """A promise about code nobody can find is not a promise — the same rule check_declarations
        already applies to LANE_FN. A clause naming _LEDGER_BACKUP_KEEP is only checkable while
        that constant exists; rename it and this must go red rather than quietly permitting
        anything."""
        import auto_scope as AS
        ca = self._ca()
        for lane, spec in sorted(AS.LANES.items()):
            rot = spec.get("rotates") or {}
            for field in ("dir", "keep"):
                name = rot.get(field)
                if not name:
                    continue
                self.assertTrue(hasattr(ca, name),
                                "%s: rotates.%s names %r, which control_app does not define — the "
                                "permission describes something nobody can find" % (lane, field, name))

    def test_the_keep_is_a_POSITIVE_number_not_zero(self):
        """⚠ keep=0 would rotate away every backup, which is deletion wearing the word 'rotate'."""
        import auto_scope as AS
        ca = self._ca()
        for lane, spec in sorted(AS.LANES.items()):
            keep = (spec.get("rotates") or {}).get("keep")
            if not keep:
                continue
            val = getattr(ca, keep, None)
            self.assertIsInstance(val, int, "%s: %s is not an int" % (lane, keep))
            self.assertGreater(val, 0,
                               "%s: %s is %r — a keep of zero is not rotation, it is deletion "
                               "under a friendlier word" % (lane, keep, val))

    def test_only_a_lane_WITH_a_rotates_clause_is_reported_as_permitted(self):
        """The intersection reporter must not hand out permission it was never given."""
        import auto_scope as AS
        rows = AS.undeclared_reach_abilities(self._ca())
        self.assertTrue(rows, "no lane forbids an ability its reach can perform — either the tree "
                              "changed or the reporter stopped working; both need a look")
        for r in rows:
            declared = bool((AS.LANES[r["lane"]].get("rotates")))
            self.assertEqual(r["permitted"], declared,
                             "%s reported permitted=%s with rotates=%s" % (r["lane"], r["permitted"], declared))

    def test_the_reporter_does_NOT_claim_the_unexplained_rows_are_safe(self):
        """⚠ THREE OF FOUR ROWS ARE PROBABLY REACH-NOISE (reach 23, 34 and 71 functions), and the
        reporter must keep saying so rather than rounding them to a verdict. It reports; the
        direct-body check is what refuses. Measured 2026-09-01: 4 rows, 1 permitted, 3 unexplained
        — and tvd-version-drift's 71 is exactly the everything-reaches-everything case the
        direct-body rule exists to avoid."""
        import auto_scope as AS
        rows = AS.undeclared_reach_abilities(self._ca())
        unexplained = [r for r in rows if not r["permitted"]]
        self.assertTrue(all(isinstance(r.get("functions"), int) for r in unexplained),
                        "an unexplained row does not carry its reach size, so a reader cannot tell "
                        "a one-frame contradiction from 71 functions of noise")


if __name__ == "__main__":
    try:
        import console_safe as _cs
        _cs.enable()
    except Exception:
        pass
    unittest.main(verbosity=1)

