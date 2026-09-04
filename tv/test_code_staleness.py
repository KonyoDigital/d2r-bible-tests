#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The stale-image watchdog, and the false accusation it exists to stop.

⚠⚠ THE INCIDENT, 2026-09-05. His console booted at 08:43 and served that process image for sixteen
hours, across v2621 → v2633. In that window `reel_router_wilson` was declared in
`self_arming.PROVES` ON DISK and its rows were appended to `.self_arming.jsonl`. The running
console judged those rows against the registry it had loaded at boot and published:

    ".self_arming.jsonl has a row that could not have been banked:
     src 'reel_router_wilson' is not a declared evidence source"

Read under the code on disk, the same ledger is clean — `reel.route` OPEN, 56/56, wilson 0.9358.
The row was fine. The reader was old. And nothing anywhere was watching for that.

His ask, three times: *"stale in-memory so for this a safeguard on it? is that possible just like
we have regression watchdog? so for a stale-in-memory registry safeguard watchdog for it too?"*

⚠ NOTHING HERE TOUCHES HIS LEDGER. Every case drives the module directly or writes to a temp file.
[[feedback-fixtures-never-touch-live-data]]
"""
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import code_staleness as CS  # noqa: E402
import self_arming as SA  # noqa: E402


class ItKnowsWhetherItIsRunningTheFileOnDisk(unittest.TestCase):

    def setUp(self):
        self._saved = dict(CS._SEEN)
        self.addCleanup(lambda: (CS._SEEN.clear(), CS._SEEN.update(self._saved)))

    def test_a_module_never_snapshotted_is_UNKNOWN_not_FRESH(self):
        """★ [[unknown-stays-unknown]] — 'I never checked' must not read as 'it is current'."""
        CS._SEEN.pop("self_arming", None)
        st, why = CS.state("self_arming")
        self.assertEqual(st, CS.UNKNOWN)
        self.assertIn("never established", why)

    def test_an_unchanged_module_is_FRESH(self):
        CS._SEEN.clear()
        self.assertTrue(CS.snapshot("self_arming"), "the module under test was not snapshottable")
        self.assertEqual(CS.state("self_arming")[0], CS.FRESH)

    def test_a_module_that_CHANGED_on_disk_is_STALE(self):
        """RED for its own reason: the baseline is what this process loaded, so a disk edit after
        import is exactly the sixteen-hour drift, compressed."""
        CS._SEEN.clear()
        CS.snapshot("self_arming")
        path, mtime, size = CS._SEEN["self_arming"]
        CS._SEEN["self_arming"] = (path, mtime, size - 1)      # disk now differs from the baseline
        st, why = CS.state("self_arming")
        self.assertEqual(st, CS.STALE, "a changed file still reported as current")
        self.assertIn("OLDER image", why)

    def test_snapshot_REFUSES_to_rebaseline(self):
        """⚠⚠ THE ONE THAT KEEPS IT HONEST. Re-snapshotting adopts whatever is on disk NOW as the
        baseline, which makes STALE unreachable forever — the watchdog would report clean for the
        rest of the process's life and look exactly like a working one."""
        CS._SEEN.clear()
        self.assertTrue(CS.snapshot("self_arming"))
        path, mtime, size = CS._SEEN["self_arming"]
        CS._SEEN["self_arming"] = (path, mtime, size - 1)
        self.assertFalse(CS.snapshot("self_arming"), "it re-baselined and lost the drift")
        self.assertEqual(CS.state("self_arming")[0], CS.STALE)

    def test_it_asks_the_LOADED_module_not_the_directory(self):
        """A guard resolving HERE/<name>.py compares disk against disk and reports FRESH forever
        — the classic instrument that measures itself. [[feedback-suspect-the-instrument]]"""
        import inspect
        src = inspect.getsource(CS._module_path)
        self.assertIn("sys.modules", src,
                      "_module_path does not consult the loaded module, so it cannot detect that "
                      "this PROCESS is behind the file")


class AnOldRegistryMayNotAccuseTheLedger(unittest.TestCase):
    """★★ THE POINT. `self_arming` judges every row against PROVES. When PROVES is stale, an
    unrecognised source is evidence the READER is old — never that the row is forged."""

    def setUp(self):
        self._saved = dict(CS._SEEN)
        self.addCleanup(lambda: (CS._SEEN.clear(), CS._SEEN.update(self._saved)))
        self.row = {"lock": "prune.arm", "kind": "sabotage", "src": "a_source_from_the_future",
                    "n": 8, "k": 8}

    def _go_stale(self):
        CS._SEEN.clear()
        CS.snapshot("self_arming")
        path, mtime, size = CS._SEEN["self_arming"]
        CS._SEEN["self_arming"] = (path, mtime, size - 1)

    def test_a_FRESH_process_still_REFUSES_an_undeclared_source(self):
        """⚠ THE BASELINE, and without it this whole file proves nothing. A softening that fires
        unconditionally excuses every forged row forever while looking careful."""
        CS._SEEN.clear()
        CS.snapshot("self_arming")
        fault = SA._row_fault(self.row)
        self.assertTrue(fault, "an undeclared source passed on a process that is up to date")
        self.assertIn("not a declared evidence source", fault)
        self.assertNotIn("UNKNOWN", fault)

    def test_a_STALE_process_says_UNKNOWN_instead_of_accusing(self):
        self._go_stale()
        fault = SA._row_fault(self.row)
        self.assertTrue(fault, "the row was silently accepted — UNKNOWN is not a pass either")
        self.assertIn("UNKNOWN", fault)
        self.assertIn("Relaunch", fault)
        self.assertNotIn("is not a declared evidence source,", fault)

    def test_the_softening_does_NOT_excuse_a_WRONG_LOCK(self):
        """⚠ Narrow on purpose. A declared source proving a lock it was never allowed to prove is
        a real fault whatever the reader's age — staleness explains an UNRECOGNISED name, and
        explains nothing at all about a name it recognises."""
        self._go_stale()
        src = sorted(SA.PROVES)[0]
        allowed = SA.PROVES[src]
        fault = SA._row_fault({"lock": "a.lock.it.may.not.prove", "kind": "sabotage",
                               "src": src, "n": 4, "k": 4})
        self.assertTrue(fault, "a source proving a lock outside its declaration was excused")
        self.assertIn("does not prove", fault)
        self.assertNotIn("Relaunch", fault)
        self.assertTrue(allowed)


class ItReportsAndNeverActs(unittest.TestCase):
    """A console that silently re-imported itself under him would be far worse than one running
    known-old code and saying so."""

    def test_the_module_never_reloads_restarts_or_execs(self):
        import ast
        import inspect
        called = set()
        for node in ast.walk(ast.parse(inspect.getsource(CS))):
            if isinstance(node, ast.Call):
                f = node.func
                nm = getattr(f, "attr", None) or getattr(f, "id", None)
                if nm:
                    called.add(nm)
        for banned in ("reload", "execv", "execl", "system", "Popen", "_exit", "kill"):
            self.assertNotIn(banned, called,
                             "the watchdog calls %r — it reports, it does not act" % banned)

    def test_report_distinguishes_nothing_stale_from_nothing_measured(self):
        """A bare boolean here would fail exactly the way the thing it watches failed."""
        CS._SEEN.clear()
        rep = CS.report()
        self.assertFalse(rep["anyStale"])
        self.assertEqual(rep["measured"], 0)
        self.assertIn("nothing was measured", rep["why"])


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
