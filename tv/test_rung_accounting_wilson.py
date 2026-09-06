# -*- coding: utf-8 -*-
"""v2725 — THE HARNESS THAT BANKS EVIDENCE MUST BE UNABLE TO BANK THE WRONG EVIDENCE.

`rung_accounting_wilson` writes into `self_arming`, and what it writes moves a lock toward opening.
That makes it a different kind of file from a test: a test that is wrong goes red, but a BANKING
harness that is wrong goes green and leaves a number behind that outlives the run.

The failure this file exists to make impossible is named in `_hardening_gap`'s own docstring:

    "Calling a fixture `live`, or an agreement a `sabotage`, would clear this gap on paper and
     prove nothing."

and [[join-gate-heart]] restates it as the step most easily turned into cheating. `bank()` accepts
a self-declared `attacks=N` and only checks that `kind` is a legal enum value — never that it is
TRUE of the evidence. So the honesty of the count has to be asserted from the harness's own source
and behaviour, which is what these laws do.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import rung_accounting_wilson as RAW  # noqa: E402

SRC = io.open(os.path.join(HERE, "rung_accounting_wilson.py"), encoding="utf-8").read()


def _code():
    """The file's source with comments and docstrings stripped.

    ⚠ A sabotage placed in a COMMENT is not a sabotage, and a law that greps raw source cannot
    tell the two apart — this repo has made that mistake in both directions. [[source-reading-guard]]
    """
    import ast
    tree = ast.parse(SRC)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                node.body = node.body[1:] or [ast.Pass()]
    return ast.unparse(tree)


class RungAccountingHarnessIsHonest(unittest.TestCase):

    # ── it may only bank against the lock it actually attacks ─────────────────────────────────
    def test_it_banks_against_reel_route_AND_NOTHING_ELSE(self):
        code = _code()
        banks = re.findall(r"\.bank\(\s*([\"'])([^\"']+)\1", code)
        self.assertTrue(banks, "no bank() call was found, so this harness generates no evidence")
        for _q, lock in banks:
            self.assertEqual(
                "reel.route", lock,
                "this harness banks against %r. Its attacks are about whether the rung accounting "
                "can admit it cannot establish a rung — that is reel.route's subject and no other "
                "lock's. Evidence about one surface is not evidence about another, and filing it "
                "elsewhere moves a counter while proving nothing." % lock
            )

    def test_self_arming_agrees_that_this_source_proves_that_lock(self):
        """⚠ Two registries, and a harness trusted by one and unknown to the other is a leak."""
        import self_arming as SA
        allowed = SA.PROVES.get("rung_accounting_wilson")
        self.assertIsNotNone(
            allowed,
            "self_arming.PROVES does not declare `rung_accounting_wilson`. An undeclared source is "
            "how a lock opens on somebody else's proof — bank() refuses it, and this law makes the "
            "refusal visible at gate time rather than at bank time."
        )
        self.assertEqual(("reel.route",), tuple(allowed))

    # ── it may not bank a run it failed ───────────────────────────────────────────────────────
    def test_it_REFUSES_to_bank_when_an_attack_was_answered_wrongly(self):
        code = _code()
        m = re.search(r"if\s+ok\s*!=\s*n\s*:", code)
        self.assertIsNotNone(
            m,
            "there is no `if ok != n:` guard before the bank. A harness that banks its own "
            "failures is not measuring anything — it is recording that it ran."
        )
        # and the guard must RETURN before reaching bank(), not merely print
        tail = code[m.end():]
        ret = tail.find("return")
        bank = tail.find(".bank(")
        self.assertTrue(ret >= 0 and (bank < 0 or ret < bank),
                        "the failure guard does not return before bank() is reached, so it warns "
                        "and banks anyway")

    # ── the attacks must be breadth, not repetition ───────────────────────────────────────────
    def test_no_two_attacks_are_the_same_idea(self):
        n, ok, rows = RAW.run()
        names = [r["attack"] for r in rows]
        self.assertEqual(len(names), len(set(names)),
                         "two attacks share a name, so at least one is a duplicate counted as "
                         "breadth. wilsonByAttack exists precisely to refuse that: 80 of "
                         "printer.stream's 83 were two functions applied to 40 reels each.")
        self.assertEqual(n, len(rows), "the reported attempt count does not match the rows")

    def test_the_banked_attack_count_is_the_number_actually_RUN(self):
        """⚠ `attacks=N` is self-declared and unchecked by bank(). Pin it to the real thing."""
        code = _code()
        m = re.search(r"\.bank\((?:[^()]|\([^()]*\))*\)", code, re.S)
        self.assertIsNotNone(m, "no bank() call to read")
        call = m.group(0)
        self.assertRegex(
            call, r"attacks\s*=\s*n\b",
            "the banked `attacks` is not the harness's own attempt count `n` (%s...). A literal "
            "here would keep claiming the old breadth after an attack is added or removed."
            % call[:90].replace("\n", " ")
        )
        self.assertRegex(call, r"\bn\s*=\s*n\b", "n is not the measured attempt count")
        self.assertRegex(call, r"\bk\s*=\s*ok\b", "k is not the measured correct count")

    def test_the_kind_is_sabotage_because_that_is_what_these_ARE(self):
        code = _code()
        m = re.search(r"\.bank\(\s*[\"']reel\.route[\"']\s*,\s*[\"']([^\"']+)[\"']", code)
        self.assertIsNotNone(m, "could not read the banked kind")
        self.assertEqual(
            "sabotage", m.group(1),
            "these attacks are code sabotages run in-process. Banking them as `live` or "
            "`cross-family` would raise CONFLUENCE — the score that measures whether evidence "
            "comes from different KINDS of witness — on evidence that is all one kind."
        )

    # ── a wall would score perfectly and prove nothing ────────────────────────────────────────
    def test_at_least_one_attack_must_be_ANSWERED_not_refused(self):
        """A verdict that only ever says UNKNOWN scores a perfect Wilson and has no judgement."""
        n, ok, rows = RAW.run()
        answered = [r for r in rows if r["expected"] not in ("UNKNOWN",)]
        self.assertTrue(
            answered,
            "every attack expects UNKNOWN, so a function that returned UNKNOWN unconditionally "
            "would score 100%%. The success path has to be in the table or the harness cannot "
            "tell a careful verdict from a stuck one."
        )
        self.assertTrue(any(r["expected"] == "OBSERVED" for r in rows),
                        "no attack expects OBSERVED — the state his shelf is actually in")

    # ── it is pure ────────────────────────────────────────────────────────────────────────────
    def test_it_cannot_write_delete_or_arm_anything(self):
        code = _code()
        for bad in ("os.remove", "os.unlink", "rmtree", "shutil.move", "TV_AUTO_PRUNE",
                    "apply_plan", "_prune_once"):
            self.assertNotIn(
                bad, code,
                "the harness references %r. It attacks a REPORTING path and must not be able to "
                "touch footage or arm anything; a comment promising that is not the same as being "
                "unable to." % bad
            )
        opens = re.findall(r"open\([^)]*[\"']([wa]\+?)[\"']", code)
        self.assertEqual([], opens, "the harness opens a file for writing (%s)" % opens)

    def test_it_restores_every_module_attribute_it_swaps(self):
        """⚠ A harness that leaves reel_story.story monkeypatched poisons every later gate."""
        import reel_story as RS
        before = RS.story
        RAW.run()
        self.assertIs(RS.story, before,
                      "reel_story.story was not restored after the run. A patched module outlives "
                      "the harness and every gate after it in the same process would be measuring "
                      "a stub.")

    def test_the_run_is_clean_on_this_tree(self):
        n, ok, rows = RAW.run()
        wrong = [r["attack"] for r in rows if not r["correct"]]
        self.assertEqual([], wrong,
                         "%d of %d attack(s) were answered wrongly: %s" % (len(wrong), n, wrong))


if __name__ == "__main__":
    unittest.main(verbosity=2)
