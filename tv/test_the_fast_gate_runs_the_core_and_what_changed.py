# -*- coding: utf-8 -*-
"""v3847 FAST GATE (Elad 2026-10-30 15:29) - a push runs the CORE set plus every gate whose law reads a changed file;
a change to a shared file (bible.html, control_ui.html, control_app.py, the gate machinery) runs EVERY gate; a
run_gates.py change that only adds or edits registry entries runs those entries, never fewer.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fast_gates as fg  # noqa: E402
import run_gates  # noqa: E402

REG = 'X = 1\nGATES = [\n    Gate("a", [1],\n         why="a"),\n    Gate("b", [2]),\n]\nY = 2\n'


class TheFastGate(unittest.TestCase):
    def test_a_shared_file_runs_every_gate(self):
        for f in ("bible.html", "control_ui.html", "tv/control_app.py", "hooks/pre-push", "tv/fast_core.txt"):
            names, why = fg.select(run_gates.GATES, ["tv/x.py", f])
            self.assertIsNone(names, "%s changed and the fast gate still picked a subset: %s" % (f, why))

    def test_the_core_set_always_runs_and_every_core_name_is_a_gate(self):
        known = {g.name for g in run_gates.GATES}
        core = fg.core()
        self.assertGreaterEqual(len(core), 50)
        self.assertEqual([n for n in core if n not in known], [], "a core name no gate has would silently run nothing")
        names, _ = fg.select(run_gates.GATES, ["README.md"])
        self.assertTrue(set(core) <= set(names))

    def test_todays_regression_gates_are_core(self):
        for n in ("test_a_quiet_relaunched_window_takes_keys", "test_a_bump_only_commit_inherits_its_parents_passes",
                  "test_a_plain_gate_run_banks_its_passes", "test_the_d2jsp_reads_compact_roll_columns",
                  "test_a_show_toggle_reads_hide_while_open", "test_a_board_field_takes_keys_after_a_click"):
            self.assertIn(n, fg.core())

    def test_a_changed_module_picks_every_law_that_reads_it(self):
        names, _ = fg.select(run_gates.GATES, ["tv/d2jsp_chrome.py"])
        readers = [g.name for g in run_gates.GATES if any(str(a).endswith(".py") and "d2jsp_chrome" in
                   fg._text(str(a)) for a in g.argv)]
        self.assertTrue(readers)
        self.assertEqual([n for n in readers if n not in names], [])

    def test_a_changed_law_runs_itself(self):
        names, _ = fg.select(run_gates.GATES, ["tv/test_vault_l1_war_stash_overflow.py"])
        self.assertIn("test_vault_l1_war_stash_overflow", names)

    def test_a_registry_only_change_runs_the_added_and_edited_entries(self):
        new = REG.replace('    Gate("b", [2]),\n', '    Gate("b", [3]),\n    Gate("c", [4]),\n')
        self.assertEqual(fg.registry_change(REG, new), {"b", "c"})
        self.assertEqual(fg.registry_change(REG, REG), set())

    def test_a_change_outside_the_registry_or_a_dropped_gate_runs_every_gate(self):
        self.assertIsNone(fg.registry_change(REG, REG.replace("Y = 2", "Y = 3")))
        self.assertIsNone(fg.registry_change(REG, REG.replace('    Gate("b", [2]),\n', "")))
        self.assertIsNone(fg.registry_change("", REG))


RED_PROOF = [
    {"why": "a shared file stops forcing a full run, so a bible.html change ships on a subset",
     "file": "tv/fast_gates.py", "find": '    if hit:\n        return None,', "replace": '    if False:\n        return None,',
     "matches": 1},
    {"why": "a registry edit stops running the edited entry",
     "file": "tv/fast_gates.py", "find": "return {n for n in ne if oe.get(n) != ne[n]}",
     "replace": "return {n for n in ne if n not in oe}", "matches": 1},
]

if __name__ == "__main__":
    unittest.main()
