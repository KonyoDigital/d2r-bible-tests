#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guards for the printer's lock — v2570.

⚠ These assert the SHAPE that makes printer_wilson safe and the WIRING that makes the river real.
They do not re-run the sabotages (printer_wilson does that, and run_gates runs it); they pin the
properties a future edit could quietly remove.
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

SRC = os.path.join(HERE, "printer_wilson.py")


class TheHarnessCannotAct(unittest.TestCase):
    """It exercises a DECISION and never an action. Read from its own source, by AST."""

    @staticmethod
    def _src():
        with io.open(SRC, encoding="utf-8") as fh:
            return fh.read()

    def test_it_never_names_a_destructive_call(self):
        # ⚠ NAMES, not substrings of prose: the docstring deliberately QUOTES the words it must
        # not call ("no os.remove, no apply_plan"), so a text search matches the sentence promising
        # safety. Walk the AST and look at CALLS. [[source-reading-guard]]
        tree = ast.parse(self._src())
        banned = {"remove", "unlink", "rmtree", "apply_plan", "_prune_once", "_prune_loop",
                  "_retention_loop", "rmdir"}
        hits = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                f = node.func
                name = getattr(f, "attr", None) or getattr(f, "id", None)
                if name in banned:
                    hits.append("%s (line %d)" % (name, getattr(node, "lineno", -1)))
        self.assertEqual(hits, [],
                         "printer_wilson calls something that can act: %s. This harness must "
                         "exercise the DECISION and never the action." % hits)

    def test_it_never_writes_the_prune_switch(self):
        """⚠ THIS GUARD CAUGHT ITSELF ON ITS FIRST RUN, with the defect it exists to warn about.

        The first cut was `assertNotIn("TV_AUTO_PRUNE", source)` — and printer_wilson's own
        docstring PROMISES safety by naming what it does not do ("no `TV_AUTO_PRUNE`"), so the
        guard fired on the sentence recording the fix. That is v2565's scar exactly: a negative
        text match on prose that deliberately quotes what it excludes cannot work.

        So it reads CODE. Docstrings are dropped and the remaining string constants and attribute
        names are searched — prose may say the word, executable text may not.
        [[source-reading-guard]]
        """
        tree = ast.parse(self._src())
        docs = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
                body = getattr(node, "body", None) or []
                if body and isinstance(body[0], ast.Expr) and isinstance(
                        getattr(body[0], "value", None), ast.Constant) and isinstance(
                        body[0].value.value, str):
                    docs.add(id(body[0].value))
        hits = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                    and id(node) not in docs and "TV_AUTO_PRUNE" in node.value:
                hits.append("string at line %d" % getattr(node, "lineno", -1))
        self.assertEqual(hits, [],
                         "printer_wilson names the arming switch in EXECUTABLE text (%s). It "
                         "proves a REPORT layer, and a harness that can arm a deleter is a "
                         "different kind of file." % hits)

    def test_it_calls_exactly_one_printer_entry_point(self):
        tree = ast.parse(self._src())
        called = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if getattr(node.func.value, "id", None) == "P":
                    called.add(node.func.attr)
        self.assertEqual(called, {"stream"},
                         "printer_wilson should drive printer.stream() and nothing else on the "
                         "printer; it calls %s" % sorted(called))


class TheRiverIsWiredIntoTheDeleter(unittest.TestCase):
    """v2570 — his ask: "build the printer lock and wire the whole river"."""

    def test_the_printer_lock_is_declared(self):
        import self_arming as SA
        self.assertIn("printer.stream", SA.LOCKS,
                      "the printer walks every reel he owns and had no lock at all; fourteen "
                      "locks were declared and not one named the printer, the river or selection")

    def test_the_deleter_waits_on_the_river_that_feeds_it(self):
        import self_arming as SA
        after = SA.LOCKS["prune.arm"]["after"]
        self.assertIn("printer.stream", after,
                      "prune.arm must wait on printer.stream. His order is 'printer + reels -> "
                      "theatre + shelf -> routing -> the deleter', and self_arming's own docstring "
                      "says proving the deleter in isolation proves nothing about the river "
                      "feeding it. Without this the deleter waited on the two VAULT locks and on "
                      "NOTHING in the river it deletes from.")

    def test_an_unproven_printer_actually_holds_the_deleter(self):
        """BEHAVIOURAL, and it is the point: the chain must BITE, not merely be declared."""
        import self_arming as SA
        all_rows = SA._rows()[0] or []
        rows = [r for r in all_rows if r.get("lock") != "printer.stream"]
        self.assertEqual(SA.score("printer.stream", rows)["state"], SA.UNPROVEN)
        # ⚠⚠ THE LAW IS "UNAFFECTED", AND THIS USED TO PIN "OPEN" — a DATUM, not a rule.
        # It asserted `prune.arm` is OPEN/HARDENED after the printer's rows are removed, as a way
        # of showing the hold comes from the CHAIN and not from the lock's own score. That worked
        # only while prune.arm happened to be open, and it went red the moment the deciding figure
        # became `wilsonByAttack` (his ruling: n inflated by repetition is fake confluence) and
        # prune.arm correctly dropped to LOCKED on 0.5655 against its 0.839 bar — a change with
        # nothing whatever to do with the printer.
        # A bar moved and a test pinned to today's reading went red for a reason it was not about.
        # [[regression-guard]] §4 — PIN THE LAW, NOT THE NUMBER.
        #
        # The law, stated so it survives any future state: removing printer.stream's evidence must
        # not move prune.arm's OWN score, whatever that score happens to be.
        before = SA.score("prune.arm", all_rows)
        after = SA.score("prune.arm", rows)
        self.assertEqual(after["state"], before["state"],
                         "prune.arm's OWN score changed when printer.stream's evidence was removed "
                         "(%s -> %s). The hold must come from the CHAIN; conflating the two hides "
                         "which one is failing." % (before["state"], after["state"]))
        self.assertEqual(after.get("wilson"), before.get("wilson"),
                         "the printer's rows moved prune.arm's Wilson bound — evidence about one "
                         "surface is being counted as evidence about another")

    def test_printer_wilson_proves_only_the_printer(self):
        import self_arming as SA
        self.assertEqual(SA.PROVES.get("printer_wilson"), ("printer.stream",),
                         "an evidence source must prove exactly what it looked at — evidence "
                         "about one surface is not evidence about another")


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=1)
