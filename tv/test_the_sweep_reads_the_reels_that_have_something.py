# -*- coding: utf-8 -*-
"""v3171 (#96) — THE SWEEP MUST READ THE REELS THAT ACTUALLY SHOW A STASH.

MEASURED on his machine 2026-09-15, and it is the whole reason the vault has no receipts:

    45 sessions swept · 36 of them (80%) took NOTHING · 39 rows banked in total
    the THREE best stash-panel reels — one at 100% density — had NEVER BEEN SWEPT
    stash bank: 12 accumulator keys      chronicle bank: 8517 sightings over 324 names

The sweeper took reels in DIRECTORY ORDER filtered only by "not already sealed". The ranking it
needed already existed — vault_retro.panel_density, whose own docstring says it is free precisely
so "the sweep can afford to ask it about every reel before paying to read any of them" — and was
computed ONLY inside a doctor row that PRINTS it. Chooser built, sweeper built, never joined.
[[the-unjoined-end]] [[plumbing-with-no-tap]]

★ WHAT THIS PINS
  1. rank_by_panel orders by density, highest first;
  2. a reel whose gate RAISES sorts last, never first — "I could not measure it" must never be
     promoted over "I measured it and it is good";
  3. ties keep their original order, so ranking only ever reorders by evidence;
  4. the SWEEPER actually calls it (parsed from the function body, not grepped at file scope);
  5. the doctor and the sweeper use ONE ranker, so the console cannot hold two answers to
     "which reel next";
  6. vault_bank reports UNKNOWN rather than zero when a bank cannot be read.
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable
    enable()
except Exception:
    pass


def _fn_node(path, name):
    """The named function's AST node. -> (node, source_segment)"""
    with io.open(path, encoding="utf-8") as fh:
        src = fh.read()
    tree = ast.parse(src)
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n, (ast.get_source_segment(src, n) or "")
    raise AssertionError("function %r is gone from %s" % (name, os.path.basename(path)))


def _fn_src(path, name):
    return _fn_node(path, name)[1]


def _calls(path, name):
    """Every function NAME this function actually CALLS. -> set

    ⚠ PARSED, NOT GREPPED, AND THIS LAW WENT BLIND WITHOUT IT. The first cut asserted
    `"rank_by_panel" in <function source>` — and the explanatory COMMENT above the call says
    rank_by_panel, so deleting the real call left the law green. A red-proof caught it; a reader
    never would. Konyo's rule, and the reason it is a rule: parse, never grep, when a law reads
    source. [[source-reading-guard]] [[sabotage-is-usually-the-wrong-one]]
    """
    node, _ = _fn_node(path, name)
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                out.add(f.id)
            elif isinstance(f, ast.Attribute):
                out.add(f.attr)
    return out


class TheRankerOrders(unittest.TestCase):

    def setUp(self):
        import vault_retro
        self.vr = vault_retro

    def test_it_orders_by_density_highest_first(self):
        dens = {"a": 0.1, "b": 0.9, "c": 0.5}
        # drive the REAL rank_by_panel with a stubbed density, so the ordering under test is the
        # shipped one and only the measurement is faked
        real = self.vr.panel_density
        try:
            self.vr.panel_density = lambda d, g, sample_every=8, cap=24: dens[d]
            out = self.vr.rank_by_panel(["a", "b", "c"], object())
        finally:
            self.vr.panel_density = real
        self.assertEqual([d for d, _ in out], ["b", "c", "a"])

    def test_a_reel_whose_gate_raises_sorts_last(self):
        def boom(d, g, sample_every=8, cap=24):
            if d == "bad":
                raise RuntimeError("gate died")
            return 0.4
        real = self.vr.panel_density
        try:
            self.vr.panel_density = boom
            out = self.vr.rank_by_panel(["bad", "good"], object())
        finally:
            self.vr.panel_density = real
        self.assertEqual(out[-1][0], "bad",
                         "a reel we could not measure must never outrank one we could")
        self.assertEqual(out[-1][1], 0.0)

    def test_ties_keep_their_original_order(self):
        real = self.vr.panel_density
        try:
            self.vr.panel_density = lambda d, g, sample_every=8, cap=24: 0.5
            out = self.vr.rank_by_panel(["x", "y", "z"], object())
        finally:
            self.vr.panel_density = real
        self.assertEqual([d for d, _ in out], ["x", "y", "z"],
                         "ranking may reorder by evidence and must never invent one")


class TheSweeperActuallyUsesIt(unittest.TestCase):

    def test_the_sweep_calls_the_ranker_in_its_own_body(self):
        self.assertIn("rank_by_panel",
                      _calls(os.path.join(HERE, "control_app.py"), "_vault_sweep_run"),
                      "the sweeper picks reels in directory order again — 36 of 45 sweeps took "
                      "nothing while the best stash-panel reels went unread")

    def test_it_asks_the_routing_system_too_not_only_the_footage(self):
        """TWO SIGNALS, AND THEY DISAGREE. `_vault_owed_reels()` is the routing system's answer
        (the ledger says this reel owes the vault a read); panel_density is the footage's answer
        (this reel visibly shows stash panels). MEASURED 2026-09-15: the router named 5 owed
        reels and NOT ONE was the 100%-density reel — an untriaged reel carries no tag and is
        invisible to the owed list. Either signal alone misses half the work."""
        self.assertIn("_vault_owed_reels",
                      _calls(os.path.join(HERE, "control_app.py"), "_vault_sweep_run"),
                      "the sweep orders only by footage and ignores what the ledger says it owes")

    def test_a_ranker_failure_does_not_cancel_the_sweep(self):
        body = _fn_src(os.path.join(HERE, "control_app.py"), "_vault_sweep_run")
        i = body.find("rank_by_panel")
        self.assertGreater(i, 0)
        self.assertIn("except", body[i:i + 1400],
                      "a ranker that raises must fall back to directory order, not kill the lane")

    def test_the_doctor_and_the_sweeper_share_one_ranker(self):
        self.assertIn("rank_by_panel",
                      _calls(os.path.join(HERE, "console_doctor.py"),
                             "_check_the_sweep_would_find_something"),
                      "the doctor sorted inline while the sweeper used another rule — two answers "
                      "to 'which reel next', and the sweeper's was the wrong one")


class TheBankNeverReadsEmptyWhenItIsUnknown(unittest.TestCase):

    def test_an_unreadable_bank_is_unknown_not_zero(self):
        import vault_bank
        real = vault_bank._load
        try:
            vault_bank._load = lambda n: (None, "%s would not parse" % n)
            word, line = vault_bank.headline()
        finally:
            vault_bank._load = real
        self.assertEqual(word, "UNKNOWN")
        self.assertIn("UNKNOWN", line)

    def test_both_empty_wordings_fold_to_one_and_the_fold_is_reported(self):
        import vault_bank
        self.assertTrue(vault_bank._is_empty_why("nothing was taken"))
        self.assertTrue(vault_bank._is_empty_why(
            "examined and there was nothing to take - recorded as a fact"))
        self.assertFalse(vault_bank._is_empty_why(None),
                         "a sweep with NO reason is UNKNOWN, never honestly empty")
        self.assertEqual(len(vault_bank.state()["whyFolded"]), 2,
                         "the fold must be declared, or two labels silently become one")


class AllFourOrgansWatchIt(unittest.TestCase):

    def test_the_doctor_registers_it(self):
        import console_doctor
        self.assertTrue(any(n == "stash bank" for n, _ in console_doctor.CHECKS))

    def test_the_heart_registers_it(self):
        import health_engine
        self.assertTrue(any(f.__name__ == "check_stash_bank" for f in health_engine.CHECKS))

    def test_the_watchdog_declares_what_it_watches(self):
        import health_engine
        self.assertIn("stashBank", health_engine.WATCHES,
                      "a row absent from WATCHES fails the coverage gate")

    def test_the_eagle_gets_it_by_calling_the_doctor(self):
        """The eagle's contract is 'call the other doctors rather than re-implement them', so a
        check registered with the doctor is on the eagle by construction. This pins the contract,
        because a future eagle that hand-lists rows would silently drop this one."""
        import console_doctor
        self.assertTrue(hasattr(console_doctor, "run"),
                        "console_doctor.run() is what /api/eagle calls")
        src = _fn_src(os.path.join(HERE, "console_doctor.py"), "run")
        self.assertIn("CHECKS", src,
                      "run() must enumerate CHECKS, or a registered organ never reaches the eagle")


if __name__ == "__main__":
    unittest.main(verbosity=2)
