"""v2472 — the deleter's harness must never be able to delete, and must be able to go RED.

`prune_wilson` sabotages the ONE door in this tree with no undo. Two things therefore have to be
true of it, and neither may rest on a comment promising them:

  1. IT CANNOT DELETE. Not "does not today" — cannot, by what it calls.
  2. IT CAN GO RED. A harness that reports PROVEN whatever the guard does is measuring nothing,
     and would hand `prune.arm` a perfect record it never earned. [[regression-guard]]

⚠ THE TRAP THIS GUARD WALKED INTO FIRST, and the reason it reads the file the way it does:
`prune_wilson`'s own module docstring NAMES every forbidden call — "It never touches `apply_plan`,
`_prune_once`, `_prune_loop`, `_retention_loop`, `os.remove`, `unlink` or `rmtree`". A plain
`assertNotIn("os.remove", src)` therefore fails on the SENTENCE PROMISING IT DOES NOT DELETE,
which is the purest form of a guard measuring its own reach instead of the code. So the source is
stripped of comments and string literals before any forbidden token is looked for.
[[source-reading-guard]] [[feedback-comments-vs-code]]
"""
import io
import os
import sys
import tokenize
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from console_safe import enable  # noqa: E402

enable()

TARGET = os.path.join(HERE, "prune_wilson.py")

#: Anything here, reached from this harness, could destroy footage.
FORBIDDEN = ("os.remove", "os.unlink", "shutil.rmtree", "rmtree", "unlink",
             "apply_plan", "_prune_once", "_prune_loop", "_retention_loop",
             "start_background_watchers", "_PRUNE_SAFE_TO_RUN =")


def _code_only(path):
    """The file's CODE, with every comment and string literal blanked out.

    Blanked rather than deleted so line numbers survive, which makes a failure message point at
    the real line. A guard that reports the wrong line sends the next reader to the wrong place.
    """
    out = []
    with io.open(path, "rb") as fh:
        for tok in tokenize.tokenize(fh.readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                out.append((tok.start, tok.end, ""))
            else:
                out.append((tok.start, tok.end, tok.string))
    lines = io.open(path, encoding="utf-8").read().split("\n")
    keep = [[" "] * len(l) for l in lines]
    for (srow, scol), (erow, ecol), text in out:
        if not text:
            continue
        if srow == erow:
            for i, ch in enumerate(text):
                if scol + i < len(keep[srow - 1]):
                    keep[srow - 1][scol + i] = ch
    return "\n".join("".join(r) for r in keep)


class TheHarnessCannotDelete(unittest.TestCase):

    def test_the_stripper_actually_strips(self):
        """Prove the instrument before trusting what it reports — the docstring names them all."""
        raw = io.open(TARGET, encoding="utf-8").read()
        self.assertIn("os.remove", raw,
                      "the docstring no longer names the forbidden calls; this guard's whole "
                      "premise (that a naive grep would hit the comment) needs re-deriving")
        code = _code_only(TARGET)
        self.assertNotIn("os.remove", code,
                         "the comment/string stripper is not working — every result below would "
                         "then be about prose rather than code")

    def test_no_destructive_call_in_the_code(self):
        code = _code_only(TARGET)
        for bad in FORBIDDEN:
            self.assertNotIn(
                bad, code,
                "prune_wilson reaches %s in CODE. This harness sabotages the one door with no "
                "undo; it may call nothing that can act." % bad)

    def test_it_calls_exactly_one_console_function(self):
        """The safety argument is 'it only calls a decider'. Check that, do not assume it."""
        import ast
        tree = ast.parse(io.open(TARGET, encoding="utf-8").read())
        called = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                base = node.func.value
                if isinstance(base, ast.Name) and base.id == "ca":
                    called.add(node.func.attr)
        self.assertEqual(
            called, {"retention_may_act"},
            "prune_wilson calls %s on the console module. Its safety rests on calling ONLY "
            "retention_may_act, whose own docstring is 'Decides; never acts.'" % sorted(called))

    def test_every_switch_value_it_writes_is_a_spelling_of_off(self):
        """It writes TV_AUTO_PRUNE. Every value must be OFF or empty — never an arming one."""
        import prune_wilson as pw
        allowed = set(pw.OFF_SPELLINGS) | {"", None}
        import ast
        tree = ast.parse(io.open(TARGET, encoding="utf-8").read())
        literals = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                    and node.func.id == "_Env":
                for a in node.args:
                    if isinstance(a, ast.Constant):
                        literals.add(a.value)
                    else:
                        literals.add("<non-literal>")
        self.assertTrue(literals, "no _Env(...) call found — has the switch handling moved?")
        stray = sorted(str(x) for x in literals - allowed if x != "<non-literal>")
        self.assertEqual(
            stray, [],
            "prune_wilson sets TV_AUTO_PRUNE to %s, which is not a spelling of OFF. Writing an "
            "arming value would be this harness arming the deleter it is testing." % stray)

    def test_a_NON_LITERAL_switch_value_is_refused_at_write_time(self):
        """The static check above cannot settle a variable — so the harness enforces it itself.

        This is the half that actually protects: call sites pass `spelling` from a loop, so no
        amount of source reading proves the value. `_Env.__enter__` refuses anything that is not a
        spelling of OFF, and refusing is what makes the harness unable to arm the deleter rather
        than merely unlikely to.
        """
        import prune_wilson as pw
        had, was = "TV_AUTO_PRUNE" in os.environ, os.environ.get("TV_AUTO_PRUNE")
        try:
            for arming in ("1", "on", "true", "yes", "TRUE", "enabled"):
                with self.assertRaises(ValueError, msg="%r was accepted" % arming):
                    with pw._Env(arming):
                        pass
                self.assertNotEqual(
                    os.environ.get("TV_AUTO_PRUNE"), arming,
                    "%r reached the switch before being refused — the check must run BEFORE the "
                    "write, not after" % arming)
            # and the allowed ones still work
            with pw._Env("off"):
                self.assertEqual(os.environ.get("TV_AUTO_PRUNE"), "off")
            with pw._Env(""):
                self.assertEqual(os.environ.get("TV_AUTO_PRUNE"), "")
        finally:
            if had:
                os.environ["TV_AUTO_PRUNE"] = was
            else:
                os.environ.pop("TV_AUTO_PRUNE", None)

    def test_the_off_spellings_still_include_the_ones_that_once_armed_it(self):
        """v2082: only the byte '0' held; off/false/no/OFF and '0 ' all ARMED the deleter."""
        import prune_wilson as pw
        for spelling in ("0", "off", "false", "no", "OFF", " 0 "):
            self.assertIn(spelling, pw.OFF_SPELLINGS,
                          "%r was one of the spellings that armed an unattended deleter in v2082 "
                          "and it is no longer attempted" % spelling)


class TheHarnessCanGoRed(unittest.TestCase):

    def test_a_deleter_that_permits_everything_is_reported_as_LEAKS(self):
        """The red proof, in-process. Without it a perfect record proves only that it ran."""
        try:
            import control_app as ca
            import prune_wilson as pw
        except Exception as e:
            self.skipTest("console module would not import: %s" % str(e)[:80])
        orig = ca.retention_may_act
        try:
            ca.retention_may_act = lambda *a, **k: (True, "sabotage: permits anything")
            rows = pw.score()
        finally:
            ca.retention_may_act = orig
        self.assertTrue(rows, "score() returned nothing")
        leaked = [r for r in rows if r["state"] == "LEAKS"]
        self.assertEqual(
            len(leaked), len(rows),
            "with the deleter permitting EVERY sabotaged state, only %d of %d claims reported "
            "LEAKS. The rest are measuring nothing." % (len(leaked), len(rows)))

    def test_a_bare_False_with_no_reason_does_not_count_as_a_refusal(self):
        """The console must be able to say WHY it did not delete."""
        import prune_wilson as pw
        self.assertFalse(pw._refused((False, "")), "a refusal with no reason was counted")
        self.assertFalse(pw._refused((False, None)), "a refusal with no reason was counted")
        self.assertFalse(pw._refused(False), "a bare False, not the (ok, why) pair, was counted")
        self.assertTrue(pw._refused((False, "because the world is unconfirmed")))

    def test_it_restores_the_switch_even_when_the_attempt_raises(self):
        """A crash mid-attempt must not leave TV_AUTO_PRUNE holding a sabotage value."""
        import prune_wilson as pw
        had, was = "TV_AUTO_PRUNE" in os.environ, os.environ.get("TV_AUTO_PRUNE")
        try:
            with self.assertRaises(RuntimeError):
                with pw._Env("off"):
                    raise RuntimeError("boom")
            self.assertEqual("TV_AUTO_PRUNE" in os.environ, had,
                             "the switch's presence was not restored after a raise")
            self.assertEqual(os.environ.get("TV_AUTO_PRUNE"), was,
                             "the switch's value was not restored after a raise")
        finally:
            if had:
                os.environ["TV_AUTO_PRUNE"] = was
            else:
                os.environ.pop("TV_AUTO_PRUNE", None)


class ItIsDeclaredForOneLockOnly(unittest.TestCase):

    def test_PROVES_binds_prune_wilson_to_prune_arm_alone(self):
        import self_arming as sa
        self.assertEqual(
            sa.PROVES.get("prune_wilson"), ("prune.arm",),
            "prune_wilson's evidence bears on the deleter and nothing else. Banking it elsewhere "
            "would let another lock open on the deleter's proof.")

    def test_sabotage_alone_cannot_open_the_deleter(self):
        """The bar, not the harness, is what keeps this shut — pin it so a tune-down is visible."""
        import self_arming as sa
        bar = sa.LOCKS["prune.arm"]["kinds_bar"]
        self.assertGreater(
            bar, sa.KINDS["sabotage"],
            "prune.arm's kinds_bar (%s) no longer exceeds the weight of a single sabotage (%s), so "
            "one kind of look could open the door with no undo." % (bar, sa.KINDS["sabotage"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
