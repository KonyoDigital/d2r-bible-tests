# -*- coding: utf-8 -*-
"""v3426 (#175) — A HELL-FIRST HEADLINE MUST SAY WHEN SOMEWHERE ELSE IS MATERIALLY QUICKER.

Konyo, 2026-09-23, on COW KING'S HOOVES in MY HUNT: *"the sets cows item is saying i need to do it
in HELL and that its the fastest path to get it. but on the sets tab within the sub tabs quick wins
and best wins it reads normal mode and a different silospen find %... so check why there is a
mismatch and its not synced between each other."*

⚠ THE HELL-FIRST RANKING IS HIS OWN RULING AND IS NOT THE DEFECT. v1555 quotes him: *"prioritized
by HELL then Nightmare then Normal in the hunts... i rather finish off Hell and then the others."*
The headline stays Hell. What that same comment PROMISED is the other half — *"when something
materially quicker exists at a lower difficulty, the source line says so rather than hiding it —
he can still choose, he just is not choosing blind"* — and on the SETS hero it was never built.

⚠⚠ AND v2281 DESCRIBED THIS EXACT DEFECT WHILE FIXING IT ON THE OTHER HERO:

    "the 'quickest anywhere' hint fires only when the fastest is a DIFFERENT ITEM
     (_fastest.name !== top.name). For a piece whose Hell lead and global lead are the SAME ITEM at
     a different difficulty, that test is false and nothing is said. The comparison was
     item-vs-item where it had to be SOURCE-vs-SOURCE."

Cow King's Hooves is that case exactly — the card reads `of 1`, one piece left, so the Hell lead
and the global lead are NECESSARILY the same item. `hubNextGrail` got `_elsewhere` in v2281;
`hubNextSet` got nothing, for 1,145 versions. The named site was fixed and its sibling was never
swept. [[sweep-dont-ask]] §1 [[plumbing-with-no-tap]]

⚠ THIS GATE EVALUATES THE SHIPPED EXPRESSION. The predicate and the tier function are EXTRACTED
FROM control_ui.html and run in node, so the gate cannot drift from the code the way a re-typed
copy would. [[source-reading-guard]]
"""
import io
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

UI = os.path.join(HERE, "control_ui.html")
SRC = io.open(UI, encoding="utf-8", errors="replace").read()

# ⚠⚠ v3429 — BRACE-BALANCED, BECAUSE `[^}]` CANNOT CROSS ONE. The second eye found this reviewing
# v3426 and it was CONFIRMED by measurement: the old pattern `\{[^}]*?\};` matches today's `tier`
# only because that body happens to be one brace-free ternary. A `tier` written with a single
# nested block — `if (t) { return 2; }` — does NOT match (measured: True today, False with one
# block), and setUp would then fail with "the sets hero's tier() is gone" while the function sat
# right there, SILENTLY DISABLING every behavioural case in this file. A gate that dies on ordinary
# reformatting of a function it does not own is measuring the formatting.
_TIER_HEAD = "var tier = function (src) {"


def _extract_tier(src):
    """Cut `tier` out by BALANCING braces from its opening one. -> str or None."""
    i = src.find(_TIER_HEAD)
    if i < 0:
        return None
    j = i + len(_TIER_HEAD) - 1          # sits on the opening brace
    depth = 0
    for k in range(j, len(src)):
        c = src[k]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[i:k + 1] + ";"
    return None
# ⚠⚠ v3426 — THESE CAPTURE WHOLE STATEMENTS, NOT CONDITIONS, AND THAT IS THE WHOLE POINT.
# The first form of this gate extracted only the `if (...)` CONDITION and evaluated that, and
# separately asserted the strings `_elsewhere` and `quicker below Hell` were PRESENT in each hero.
# Both red-proofs then came back **BLIND at match count 1**: `_elsewhere = null` still contains
# `_elsewhere`, and `false ? '... quicker below Hell ...' : ''` still contains the sentence. The
# tampers applied perfectly and the gate never moved. A PRESENCE-LAW IS NOT A REACHABILITY-LAW —
# so what is extracted now is the assignment BLOCK and the render EXPRESSION, and both are
# EXECUTED. [[presence-law-vs-reachability-law]]
_ASSIGN_RE = re.compile(
    r"(if \(_h0\.expectedHours != null.*?\n      \})", re.S)
_FACTOR_RE = re.compile(
    r"_h0\.expectedHours <= _h0\.hellExpectedHours \* ([0-9.]+)")
_RENDER_RE = re.compile(
    r"(\(_elsewhere \? '<span class=\"hh-alt\"> · \\u26a1 faster outside Hell.*?: ''\))", re.S)


def _node(js):
    r = subprocess.run(["node", "-e", js], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=60)
    return r.returncode, r.stdout.decode("utf-8", "replace").strip()


class TestTheHuntSaysWhenSomewhereElseIsQuicker(unittest.TestCase):

    def setUp(self):
        t = _extract_tier(SRC)
        a = _ASSIGN_RE.search(SRC)
        f = _FACTOR_RE.search(SRC)
        self.assertTrue(t, "the sets hero's tier() is gone — this gate is pointed at nothing")
        self.assertTrue(a, "the v3426 source-vs-source BLOCK is gone from hubNextSet, so the Hell "
                           "headline is back to hiding a quicker lower-difficulty route")
        self.assertTrue(f, "the material threshold is gone")
        self.tier_js, self.assign_js, self.factor = t, a.group(1), float(f.group(1))

    def _fires(self, expected, hell, source):
        """RUN the shipped assignment block and report whether it actually set `_elsewhere`.

        ⚠ IT EXECUTES THE STATEMENT, NOT THE CONDITION. Reading the `if` alone is what let
        `_elsewhere = null` pass as a fix — the test agreed with the branch while the branch did
        nothing."""
        js = ("%s\nvar _elsewhere = null;\nvar _h0 = %s;\n%s\n"
              "console.log(JSON.stringify(_elsewhere));"
              % (self.tier_js,
                 json.dumps({"expectedHours": expected, "hellExpectedHours": hell,
                             "source": source}),
                 self.assign_js))
        rc, out = _node(js)
        self.assertEqual(rc, 0, "node refused the shipped block: %s" % out)
        got = json.loads(out)
        if got is not None:
            self.assertEqual(got.get("source"), source,
                             "it disclosed a route that is not the one it measured")
            self.assertEqual(got.get("hours"), expected,
                             "it disclosed hours that are not the ones it measured")
        return got is not None

    # ---- the case he reported -----------------------------------------------------------

    def test_THE_COW_KING_CASE_a_far_quicker_normal_route_is_disclosed(self):
        """One piece left, so Hell lead and global lead are the SAME ITEM — the case an
        item-vs-item test can never fire on."""
        self.assertTrue(self._fires(20.0, 84.0, "Normal Cow King"),
                        "an 84h Hell route with a 20h Normal alternative said nothing — he is "
                        "choosing blind, which is the half v1555 promised and never shipped here")

    def test_when_HELL_is_already_the_quickest_nothing_is_said(self):
        """⚠ THE MIRROR, AND IT MATTERS AS MUCH. A disclosure that fires when Hell is already best
        is noise on every card, and noise is how a real one stops being read."""
        self.assertFalse(self._fires(84.0, 84.0, "Hell Hell Bovines"),
                         "it offered a 'quicker below Hell' route that IS the Hell route")

    def test_a_MARGINAL_gain_is_not_worth_sending_him_somewhere_else(self):
        """80h vs 84h is 5%. The threshold is deliberate: below it, the advice costs him a
        difficulty switch to save nothing."""
        self.assertFalse(self._fires(80.0, 84.0, "Normal Cow King"),
                         "a 5%% gain was reported as materially quicker")

    def test_the_threshold_is_the_SAME_ONE_the_grail_hero_uses(self):
        """⚠ TWO SURFACES ANSWERING ONE QUESTION MUST ANSWER IT WITH ONE RULE. Different cutoffs
        would make them disagree about whether to mention a route at all — a quieter version of
        the very mismatch he reported."""
        grail = re.findall(r"h0\.expectedHours <= h0\.hellExpectedHours \* ([0-9.]+)", SRC)
        self.assertTrue(grail, "the grail hero's threshold is gone — cannot compare")
        for g in grail:
            self.assertEqual(float(g), self.factor,
                             "the sets hero uses %r and the grail hero uses %r" % (self.factor, g))

    def test_UNKNOWN_hours_never_invent_a_recommendation(self):
        for e, h in ((None, 84.0), (20.0, None), (None, None)):
            self.assertFalse(self._fires(e, h, "Normal Cow King"),
                             "a route was recommended from a missing number (%r/%r) — an absent "
                             "hour is not a fast one" % (e, h))

    # ---- the class, so a third hero cannot repeat it -------------------------------------

    def test_BOTH_heroes_carry_a_source_vs_source_disclosure(self):
        """The defect was not that one function was wrong — it was that a fix landed on one of two
        siblings and nobody swept. A law about one hero would have the same reach the fix did."""
        for fn in ("hubNextGrail", "hubNextSet"):
            i = SRC.find("function " + fn)
            self.assertGreater(i, -1, "%s is gone" % fn)
            body = SRC[i:i + 14000]
            self.assertIn("_elsewhere", body,
                          "%s ranks Hell first and never computes a source-vs-source alternative, "
                          "so it can show a slow Hell route while a far quicker one exists and say "
                          "nothing" % fn)

    def test_the_SETS_render_actually_PRINTS_the_alternative(self):
        """⚠ THE HALF THAT WENT BLIND. Asserting the sentence 'quicker below Hell' appears in the
        file passes just as happily when it sits inside `false ? ... : ''` — which is precisely the
        unjoined shape the red-proof simulates. So the render EXPRESSION is extracted and EXECUTED
        with a truthy `_elsewhere`, and the OUTPUT must name the route."""
        m = _RENDER_RE.search(SRC)
        self.assertTrue(m, "the sets hero's disclosure render is gone")
        js = ("var esc = function(s){ return String(s); };\n"
              "var _hubHrs = function(h){ return h + 'h'; };\n"
              "var _elsewhere = { source: 'Normal Cow King', hours: 20 };\n"
              "console.log(String(%s));" % m.group(1))
        rc, out = _node(js)
        self.assertEqual(rc, 0, "node refused the shipped render: %s" % out)
        self.assertIn("Normal Cow King", out,
                      "the card computes a quicker route and prints nothing about it — built on "
                      "both ends and never joined. Rendered: %r" % out)
        self.assertIn("20h", out, "it names the route without the time, so he cannot compare it "
                                  "against the Hell number beside it. Rendered: %r" % out)


class TestTheLiveRowSeesABlindedHero(unittest.TestCase):
    """v3429 — THE DOCTOR ROW, DRIVEN. It had no red-proof, which means it measured nothing: a row
    that has never been seen refuse is indistinguishable from one that cannot.

    ⚠ IT READS THE FILE THE CONSOLE SERVES, so it is driven by pointing `console_doctor.HERE` at a
    temp directory holding a doctored copy — the real file is never touched."""

    def _row_against(self, ui_text):
        import shutil, tempfile
        import console_doctor as cd
        d = tempfile.mkdtemp(prefix="huntrow_")
        try:
            io.open(os.path.join(d, "control_ui.html"), "w", encoding="utf-8").write(ui_text)
            old = cd.HERE
            try:
                cd.HERE = d
                return dict(cd.CHECKS)["the hunt names a quicker route"]()
            finally:
                cd.HERE = old
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_the_real_file_reads_OK(self):
        import console_doctor as cd
        st, say = self._row_against(SRC)
        self.assertEqual(st, cd.OK, "the shipped file did not satisfy its own row: %s" % say)

    def test_a_hero_whose_ASSIGNMENT_is_gone_is_caught(self):
        import console_doctor as cd
        blinded = SRC.replace("_elsewhere = { source: _h0.source, hours: _h0.expectedHours };",
                              "_elsewhere = null;", 1)
        self.assertNotEqual(blinded, SRC, "the sabotage anchor missed — this proves nothing")
        st, say = self._row_against(blinded)
        self.assertEqual(st, cd.MISSING,
                         "the sets hero stopped computing an alternative and the row said fine: %s"
                         % say)
        self.assertIn("hubNextSet", say, "the row does not name WHICH card went blind")

    def test_a_hero_whose_RENDER_is_degated_is_caught(self):
        """⚠ THE HALF THAT MATTERS MOST: the sentence stays in the file, so anything looking for
        the words still finds them. Only the gate on the VALUE distinguishes them."""
        import console_doctor as cd
        degated = SRC.replace("+ (_elsewhere ? '<span class=\"hh-alt\"> · \\u26a1 faster outside Hell",
                              "+ (false ? '<span class=\"hh-alt\"> · \\u26a1 faster outside Hell", 1)
        self.assertNotEqual(degated, SRC, "the sabotage anchor missed — this proves nothing")
        st, say = self._row_against(degated)
        self.assertEqual(st, cd.MISSING,
                         "the disclosure was computed and never rendered, and the row called that "
                         "healthy: %s" % say)

    def test_a_MISSING_hero_is_a_finding_not_a_pass(self):
        import console_doctor as cd
        gone = SRC.replace("function hubNextSet", "function hubNextSetRENAMED", 1)
        st, say = self._row_against(gone)
        self.assertEqual(st, cd.MISSING,
                         "a hero that is not in the served file read as fine: %s" % say)

    def test_an_unreadable_file_is_UNKNOWN_not_clean(self):
        import console_doctor as cd
        import shutil, tempfile
        d = tempfile.mkdtemp(prefix="huntrow_empty_")
        try:
            old = cd.HERE
            try:
                cd.HERE = d          # no control_ui.html here at all
                st, say = dict(cd.CHECKS)["the hunt names a quicker route"]()
            finally:
                cd.HERE = old
        finally:
            shutil.rmtree(d, ignore_errors=True)
        self.assertEqual(st, cd.UNKNOWN,
                         "a file it could not read was reported as a verdict: %s" % say)


RED_PROOF = [
    {
        "why": "v3426 - THE DISCLOSURE REMOVED FROM THE SETS HERO. This is the state he reported: "
               "an 84h Hell route for Cow King's Hooves with a far quicker Normal one, and nothing "
               "on the card saying so.",
        "file": "control_ui.html",
        "find": "        _elsewhere = { source: _h0.source, hours: _h0.expectedHours };",
        "replace": "        _elsewhere = null;",
        "matches": 1,
    },
    {
        "why": "v3426 - THE RENDER UNJOINED. Computing the alternative and never printing it is "
               "the same defect wearing the other half's clothes - built on both ends, not joined.",
        "file": "control_ui.html",
        "find": "        + (_elsewhere ? '<span class=\"hh-alt\"> · \\u26a1 faster outside Hell",
        "replace": "        + (false ? '<span class=\"hh-alt\"> · \\u26a1 faster outside Hell",
        "matches": 1,
    },
    {
        "why": "v3426 - THE THRESHOLDS PULLED APART. Two surfaces answering one question with two "
               "cutoffs disagree about whether to mention a route at all, which is a quieter form "
               "of the mismatch he reported.",
        "file": "control_ui.html",
        "find": "          && _h0.expectedHours <= _h0.hellExpectedHours * 0.7) {",
        "replace": "          && _h0.expectedHours <= _h0.hellExpectedHours * 0.4) {",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
