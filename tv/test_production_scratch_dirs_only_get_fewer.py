# -*- coding: utf-8 -*-
"""#171 item 2 — A PRODUCTION SCRATCH DIRECTORY WITH NO CLEANUP MAY ONLY GET FEWER.

⚠ WHY: 94,478 scratch dirs / 3.77 GB were swept off his disk under three guards (v3422), and the
re-measure behind #171 found where the volume actually comes from: gate runs, not his console. Of
the production modules' `mkdtemp` sites, 24 had no cleanup in the function that made them — 17 of
them Wilson sabotage probes, the rest one-shot `main()`s, conftest, and one doctor probe. The task
said it plainly: "Do NOT solve this with a bigger reaper — the cheapest cleanup is not
accumulating." This freezes the count so it cannot grow, and forces the list DOWN the moment a site
is fixed — the swallowed-reads ratchet, turned on scratch directories.

⚠ READ BY THE PARSER, NEVER BY TEXT. #171's own first count included `console_doctor.py`'s
DOCSTRING about "89,181 bare mkdtemp() calls" as a call site — the scanner reading its own
documentation. Only an `ast.Call` named `mkdtemp` counts; a cleanup is an `ast.Call` named
rmtree / cleanup / addCleanup / register / remove_tree, or anything named *clean*, in the SAME
function (module scope for a module-level site). [[source-reading-guard]]

⚠ WHAT THIS SCAN CANNOT SEE is declared, not silenced: a teardown in a DIFFERENT function (render
check's Chrome profile, removed with the browser). EXPLAINED names it with the reason, and a case
proves the reason is still true. RED_PROOF below.
"""
import ast
import collections
import glob
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

CLEAN_CALLS = frozenset(("rmtree", "cleanup", "addCleanup", "register", "remove_tree"))

#: (file, function) -> how many mkdtemp sites in it have no cleanup. MEASURED 2026-09-24: 24 sites,
#: 24 functions. ⚠ ONLY EVER SHRINKS — fixing one without removing it here fails
#: test_the_list_only_shrinks, so the ceiling falls with the fix.
KNOWN_UNPAIRED = {
    ("conftest.py", "_pin_scar_ledger_away_from_his_tree"): 1,
    ("console_doctor.py", "_check_an_attack_can_still_reach_the_door_it_scores"): 1,
    ("disk_report_wilson.py", "_attempt_a_directory_is_not_a_history"): 1,
    ("disk_report_wilson.py", "_attempt_a_good_row_does_not_inherit_a_refusal"): 1,
    ("disk_report_wilson.py", "_attempt_a_refused_prune_does_not_blank_the_free_space_delta"): 1,
    ("disk_report_wilson.py", "_attempt_delta_ignores_a_refused_figure"): 1,
    ("disk_report_wilson.py", "_attempt_delta_sums_only_what_was_kept"): 1,
    ("disk_report_wilson.py", "_attempt_two_refusals_keep_their_own_reasons"): 1,
    ("disk_report_wilson.py", "_row"): 1,
    ("reel_router_wilson.py", "_attempt_a_clockless_reel_jumps_the_queue"): 1,
    ("robot_smoke.py", "main"): 1,
    ("sabotage_extract_gap_holding.py", "main"): 1,
    ("sweep_wilson.py", "_attempt_a_legal_call_is_not_refused"): 1,
    ("sweep_wilson.py", "_attempt_lanes_is_a_dict"): 1,
    ("sweep_wilson.py", "_attempt_lanes_is_a_string"): 1,
    ("sweep_wilson.py", "_attempt_lanes_none"): 1,
    ("sweep_wilson.py", "_attempt_lanes_raise"): 1,
    ("sweep_wilson.py", "_attempt_lock_raises_does_not_start"): 1,
    ("sweep_wilson.py", "_attempt_lock_shut_does_not_start"): 1,
    ("sweep_wilson.py", "_attempt_symlink_file"): 1,
    ("sweep_wilson.py", "_attempt_symlink_missing"): 1,
    ("sweep_wilson.py", "_attempt_the_second_call_is_busy"): 1,
    ("tv_diablo.py", "_test_state_dir"): 1,
    ("vault_simulate.py", "main"): 1,
}

#: A teardown this function-scoped scan cannot see, with the reason. Each is re-proven below.
EXPLAINED = {
    ("render_check.py", "_chrome_up"): "the Chrome profile is removed with the browser — in a "
                                       "finally, AFTER the kill, keyed on _CHROME_PROFILE",
}


def production_files():
    return sorted(f for f in glob.glob(os.path.join(HERE, "*.py"))
                  if not os.path.basename(f).startswith("test_")
                  and not os.path.basename(f).endswith("_test.py"))


def _call_name(call):
    f = call.func
    return f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else None)


def scan(src):
    """-> [(function, paired)] for every mkdtemp CALL in `src`. Raises on unparseable source."""
    tree = ast.parse(src)
    funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

    def owner(node):
        best = None
        for f in funcs:
            if f.lineno <= node.lineno <= (f.end_lineno or f.lineno):
                if best is None or f.lineno > best.lineno:
                    best = f
        return best
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and _call_name(n) == "mkdtemp":
            f = owner(n)
            names = {_call_name(c) for c in ast.walk(f if f is not None else tree)
                     if isinstance(c, ast.Call)} - {None}
            paired = any(x in CLEAN_CALLS or "clean" in x.lower() for x in names)
            out.append((f.name if f is not None else "<module>", paired))
    return out


def unpaired_now():
    """-> (Counter of (file, fn) -> unpaired sites, total sites, unreadable files)."""
    c, total, bad = collections.Counter(), 0, []
    for p in production_files():
        try:
            with io.open(p, encoding="utf-8") as fh:
                rows = scan(fh.read())
        except Exception as e:
            bad.append("%s (%s)" % (os.path.basename(p), type(e).__name__))
            continue
        total += len(rows)
        for fn, paired in rows:
            if not paired:
                c[(os.path.basename(p), fn)] += 1
    return c, total, bad


class ProductionScratchDirsOnlyGetFewer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.now, cls.total, cls.bad = unpaired_now()

    def test_every_production_file_was_read(self):
        """An unparseable file is a skipped file, and a skipped file is not an absent site."""
        self.assertEqual(self.bad, [], "production file(s) could not be parsed: %s" % self.bad)
        self.assertGreater(self.total, 20, "only %d mkdtemp site(s) found — the scan is blind, and "
                                           "a blind ratchet passes for ever" % self.total)

    def test_no_new_scratch_dir_without_a_cleanup(self):
        new = sorted("%s:%s (+%d)" % (k[0], k[1], n - KNOWN_UNPAIRED.get(k, 0))
                     for k, n in self.now.items()
                     if k not in EXPLAINED and n > KNOWN_UNPAIRED.get(k, 0))
        self.assertEqual(new, [], "a production mkdtemp with no cleanup in its own function: %s. "
                                  "Use tempfile.TemporaryDirectory(), or rmtree in a finally. A "
                                  "bigger reaper is not the fix." % "; ".join(new))

    def test_the_list_only_shrinks(self):
        """A fixed site must LEAVE the list, or the ceiling never falls and the next leak hides in
        the slack the fix left behind. [[zero-needs-a-denominator]]"""
        stale = sorted("%s:%s (%d -> %d)" % (k[0], k[1], n, self.now.get(k, 0))
                       for k, n in KNOWN_UNPAIRED.items() if self.now.get(k, 0) < n)
        self.assertEqual(stale, [], "fixed or gone — lower KNOWN_UNPAIRED: %s" % "; ".join(stale))

    def test_every_explained_site_still_is_what_it_claims(self):
        for (fname, fn), why in EXPLAINED.items():
            self.assertIn((fname, fn), self.now, "EXPLAINED names %s:%s, which is no longer an "
                                                 "unpaired site — remove it" % (fname, fn))
        src = io.open(os.path.join(HERE, "render_check.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        teardown = [f.name for f in ast.walk(tree)
                    if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and any(isinstance(n, ast.Global) and "_CHROME_PROFILE" in n.names
                            for n in ast.walk(f))
                    and any(isinstance(c, ast.Call) and _call_name(c) == "rmtree" for c in ast.walk(f))]
        self.assertTrue(teardown, "render_check no longer removes _CHROME_PROFILE anywhere — the "
                                  "EXPLAINED reason is false and _chrome_up is a real leak")

    def test_the_scan_reads_code_not_prose(self):
        cases = {
            "def f():\n    d = tempfile.mkdtemp()\n    return d\n": [("f", False)],
            "def f():\n    d = tempfile.mkdtemp()\n    try:\n        pass\n    finally:\n"
            "        shutil.rmtree(d)\n": [("f", True)],
            "def f():\n    d = mkdtemp(prefix='x')\n    _cleanup(d)\n": [("f", True)],
            'def f():\n    """89,181 bare mkdtemp() calls"""\n    # tempfile.mkdtemp()\n'
            "    return 'mkdtemp()'\n": [],
            "d = tempfile.mkdtemp()\natexit.register(shutil.rmtree, d)\n": [("<module>", True)],
        }
        for src, want in cases.items():
            self.assertEqual(scan(src), want, src)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#171 - a production scratch dir loses its cleanup: write_census's census() makes a wc_ dir per store and no longer removes it",
        "file": "write_census.py",
        "find": "        finally:\n            shutil.rmtree(d, True)\n",
        "replace": "        finally:\n            pass\n",
        "matches": 1,
    },
    {
        "why": "#171 - the scan counts a function's cleanup by NAME only when it is a CALL: a mention of rmtree in prose would pair every site",
        "file": "test_production_scratch_dirs_only_get_fewer.py",
        "find": "            paired = any(x in CLEAN_CALLS or \"clean\" in x.lower() for x in names)\n",
        "replace": "            paired = True\n",
        "matches": 1,
    },
]
