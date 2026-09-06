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

    def _banks(self):
        """Every bank() call in the harness, parsed. -> [{kind, attacks, n, k, src}]

        ⚠⚠ THIS USED TO REGEX THE FIRST `.bank(` AND GRADE IT AS THOUGH IT WERE THE ONLY ONE.
        v2727 added a second, legitimate bank — a LIVE witness beside the sabotage one — and both
        laws below failed instantly, pointing at the new call while describing the old. The laws
        were right about honesty and wrong about arity: there is no reason a harness may bank only
        once, and grading "the first one found" is a rule about text order, not about evidence.
        Parsed with AST so a call spanning lines, or a third one added later, is graded too.
        """
        import ast
        tree = ast.parse(_code())
        out = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            if not (isinstance(fn, ast.Attribute) and fn.attr == "bank"):
                continue
            pos = [a.value if isinstance(a, ast.Constant) else None for a in node.args]
            kw = {k.arg: (k.value.value if isinstance(k.value, ast.Constant)
                          else (k.value.id if isinstance(k.value, ast.Name) else None))
                  for k in node.keywords}
            out.append({"lock": pos[0] if len(pos) > 0 else None,
                        "kind": pos[1] if len(pos) > 1 else kw.get("kind"),
                        "src":  pos[2] if len(pos) > 2 else kw.get("src"),
                        "attacks": kw.get("attacks"), "n": kw.get("n"), "k": kw.get("k")})
        return out

    def test_EVERY_bank_declares_a_breadth_that_matches_its_kind(self):
        """⚠ `attacks=N` is self-declared and bank() never checks it is TRUE of the evidence.

        The honest breadth differs BY KIND, which is the whole reason this is graded per call:
          sabotage — N distinct ideas, so `attacks` must be the measured attempt count `n`
          live     — one question asked of his whole shelf, so `attacks` must be the literal 1
        Forty reels through one coherence check is ONE IDEA REPEATED FORTY TIMES. Declaring 40
        there is the 83/83 illusion, which is the precise thing wilsonByAttack exists to refuse.
        """
        banks = self._banks()
        self.assertTrue(banks, "no bank() call was found, so this harness generates no evidence")
        for b in banks:
            if b["kind"] == "sabotage":
                self.assertEqual(
                    "n", b["attacks"],
                    "the sabotage bank declares attacks=%r instead of the measured attempt count "
                    "`n`. A literal keeps claiming the old breadth after an attack is added or "
                    "removed." % (b["attacks"],))
                self.assertEqual("n", b["n"], "sabotage bank: n is not the measured attempt count")
                self.assertEqual("ok", b["k"], "sabotage bank: k is not the measured correct count")
            elif b["kind"] == "live":
                self.assertEqual(
                    1, b["attacks"],
                    "the live bank declares attacks=%r. A live pass asks ONE question of his whole "
                    "shelf however many reels it covers; anything above 1 counts repetition as "
                    "breadth and inflates the lock on evidence that never diversified."
                    % (b["attacks"],))
                self.assertEqual("ln", b["n"], "live bank: n is not the live check count")
                self.assertEqual("lok", b["k"], "live bank: k is not the live agreed count")
            elif b["kind"] == "cross-family":
                # ⚠ v2734 — ONE PASS IS ONE WITNESS, however many probes the other family reports.
                # The grok read listed SEVEN attempted probes; an LLM's self-reported breadth is not
                # verifiable breadth, and banking 7 would inflate the lock on its own say-so. The
                # VALUE of this bank is the KIND — a different model family looked — not the count.
                self.assertEqual(
                    1, b["attacks"],
                    "the cross-family bank declares attacks=%r. One pass by another model family "
                    "is ONE witness; counting its self-reported probe list as breadth takes its "
                    "word for the thing the bank exists to establish independently."
                    % (b["attacks"],))
                self.assertEqual(1, b["n"], "cross-family bank: n must be the single pass")
                self.assertEqual(1, b["k"], "cross-family bank: k must be the single pass")
            else:
                self.fail("a bank declares kind=%r, which this law has not been taught to grade. "
                          "An ungraded kind is an ungraded breadth claim." % (b["kind"],))

    def test_the_cross_family_mode_REFUSES_without_a_recorded_verdict(self):
        """⚠⚠ A MODE THAT BANKS ON BEING INVOKED MANUFACTURES A WITNESS ON DEMAND.

        `--xfam` exists because CI was right that a source with no owning harness is "evidence
        nobody can re-derive". But an entry point that banks merely because someone typed it would
        be strictly worse than the shell call it replaced — a button that mints cross-family
        evidence, which is the precise cheat `_hardening_gap` names by name.

        So it must refuse three ways: no path, unreadable path, empty file. Each refusal has to
        RETURN before any bank is reached, and this pins the structure rather than trusting that a
        hand-run once printed the right words.
        ⚠ The block was also UNREACHABLE on its first writing — anchored inside `if "--bank" in
        argv:` — so it printed a normal run instead of refusing. A guard that cannot be reached is
        not lenient, it is absent. [[the-unjoined-end]]
        """
        code = _code()
        self.assertIn("--xfam", code,
                      "the cross-family mode is gone, but PROVES still declares its source — that "
                      "is back to evidence nobody can re-derive")
        blk = code[code.index("--xfam"):]
        # ⚠ ast.unparse NORMALISES QUOTES, and my first anchor used double ones — the law errored
        # instead of grading. A source-reading guard has to match the text it is actually handed.
        # [[source-reading-guard]]
        import re as _re
        _m = _re.search(r"SA\.bank\([^)]*cross-family", blk)
        self.assertIsNotNone(_m, "the cross-family bank is not inside the --xfam branch")
        blk = blk[:_m.start()]
        for guard, what in ((("if not _vf", "_vf is None", "not _vf"), "a missing path"),
                            (("except", "could not read"), "an unreadable file"),
                            (("if not _txt", "not _txt", "_txt =="), "an empty verdict")):
            self.assertTrue(
                any(g in blk for g in guard),
                "nothing between the --xfam branch and its bank refuses %s. Without it the mode "
                "banks a cross-family witness that nobody produced." % what
            )
        # ⚠ THREE REFUSALS, THREE RETURNS. The first cut asked for >= 2, so deleting one refusal's
        # return left two and the law stayed green while that path warned and banked anyway —
        # exactly the "warns and banks" shape this file already pins for the sabotage path. A
        # threshold below the number of things it guards is an off-by-one that reads as coverage.
        self.assertGreaterEqual(
            blk.count("return 1"), 3,
            "the --xfam refusals do not RETURN before the bank is reached, so they warn and bank "
            "anyway — the same shape as banking a run you failed."
        )

    def test_no_two_banks_share_a_source_name(self):
        """`_fold` keeps the newest row per (lock, kind, src). Two banks sharing a src would
        silently overwrite each other and one witness would vanish without a word."""
        srcs = [b["src"] for b in self._banks()]
        self.assertEqual(len(srcs), len(set(srcs)),
                         "two bank() calls share a src (%s); one is overwriting the other" % srcs)

    def test_the_kinds_are_TRUE_of_what_the_code_ACTUALLY_DOES(self):
        """⚠⚠ THE CHEAT THIS FILE EXISTS FOR. bank() checks only that `kind` is a legal enum
        value, never that it is true of the evidence. `_hardening_gap` says it outright: "calling a
        fixture `live`, or an agreement a `sabotage`, would clear this gap on paper and prove
        nothing." So each kind is checked against the SHAPE of the function that produced it.
        """
        import ast
        code = _code()
        tree = ast.parse(code)
        fns = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}

        kinds = {b["kind"] for b in self._banks()}
        self.assertIn("sabotage", kinds,
                      "the in-process attacks are no longer banked as sabotage, which is what they "
                      "are: dictionaries handed to pure functions")

        if "live" in kinds:
            self.assertIn("live", fns, "a `live` kind is banked but there is no live() to produce it")
            src = ast.unparse(fns["live"])
            # a live witness must actually reach his data, or the word is a label on a fixture
            self.assertRegex(
                src, r"reel_story|reel_retention|frame_authority|one_funnel",
                "live() banks `live` without importing any module that reads his stores. A check "
                "that would pass identically on an empty machine is a FIXTURE, and calling it live "
                "raises confluence on evidence that never diversified.")
            # and it must refuse where his data is absent, or CI banks a vacuous pass forever
            self.assertRegex(
                src, r"if not reels|not reels",
                "live() does not refuse on an empty shelf. On CI there are no reels, and a live "
                "pass that returns a clean zero there would bank a witness that never looked — "
                "permanently, and in the direction that opens a lock. "
                "[[zero-needs-a-denominator]]")

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
