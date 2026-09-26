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
# ⚠⚠ v3431 — PAREN-BALANCED, FOR THE SAME REASON THE tier EXTRACTOR HAD TO BE BRACE-BALANCED.
# The first form stopped at the FIRST `: '')`. v3431 made the render a NESTED ternary, so that cut
# produced an unbalanced expression and node refused it — the gate failed on its own extractor
# while the shipped code was fine. A regex that assumes the shape it was written beside breaks the
# moment the shape grows. [[source-reading-guard]]
_RENDER_HEAD = "(_elsewhere ? '<span class=\"hh-alt\"> · \\u26a1 faster outside Hell"


def _extract_render(src):
    """Cut the disclosure render out by BALANCING parens from its opening one. -> str or None."""
    i = src.find(_RENDER_HEAD)
    if i < 0:
        return None
    depth = 0
    for k in range(i, len(src)):
        c = src[k]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return src[i:k + 1]
    return None


def _node(js):
    r = subprocess.run(["node", "-"], input=js.encode("utf-8"), stdout=subprocess.PIPE,
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
        m = _extract_render(SRC)
        self.assertTrue(m, "the sets hero's disclosure render is gone")
        js = ("var esc = function(s){ return String(s); };\n"
              "var _hubHrs = function(h){ return h + 'h'; };\n"
              "var _elsewhere = { source: 'Normal Cow King', hours: 20 };\n"
              "var _altPiece = null;\n"
              "console.log(String(%s));" % m)
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

    def test_a_hero_that_lost_its_CROSS_ITEM_half_is_caught(self):
        """⚠ v3431 — THE SECOND SURFACE NEEDS ITS OWN DRIVE. Each hero answers two questions, and a
        row watching only the first would have called hubNextSet healthy for 1,145 versions while
        it stayed silent about a piece at a fifth of the hours — which is exactly what happened."""
        import console_doctor as cd
        blinded = SRC.replace("      && _fastestAll.expectedHours <= top.expectedHours * 0.7) ? _fastestAll : null;",
                              "      && false) ? _fastestAll : null;", 1)
        self.assertNotEqual(blinded, SRC, "the sabotage anchor missed — this proves nothing")
        # the assignment is still THERE, so only a reachability-aware row can see this; the point
        # of the case is that the row must not be satisfied by the name alone
        blinded2 = SRC.replace("    var _altPiece = (_fastestAll", "    var _altPieceGONE = (_fastestAll", 1)
        st, say = self._row_against(blinded2)
        self.assertEqual(st, cd.MISSING,
                         "hubNextSet lost its cross-item alternative and the row said fine: %s" % say)
        self.assertIn("cross-item", say, "the row does not name WHICH half went missing")

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


_ALT_RE = re.compile(
    r"(var _altPiece = \(_fastestAll.*?\? _fastestAll : null;)", re.S)


class TestADifferentPieceCanBeQuickerToo(unittest.TestCase):
    """v3431 (#176) — THE SIBLING SWEEP, ONE LEVEL UP FROM v3426.

    The second eye on v3426: `_elsewhere` compares the Hell leader AGAINST ITSELF at another
    difficulty and looks at no other ranked row. So when the Hell-fastest piece is ALSO quickest in
    Hell, and a DIFFERENT piece is far quicker in Normal, the card presented the Hell route and
    said nothing — the same outcome he reported on Cow King's Hooves, across PIECES rather than
    across difficulties of one piece. hubNextGrail has had both since v2281; hubNextSet had one.
    """

    def _fires(self, top_hours, fastest_hours, same_name=False):
        """RUN the shipped `_altPiece` statement."""
        m = _ALT_RE.search(SRC)
        self.assertTrue(m, "the v3431 cross-piece statement is gone from hubNextSet")
        js = ("var data = { ranked: [ {name:%s, expectedHours:%s} ] };\n"
              "var top = { name: 'TopPiece', expectedHours: %s };\n"
              "var _fastestAll = data.ranked[0];\n"
              "var _altPiece = null;\n%s\n"
              "console.log(JSON.stringify(_altPiece));"
              % (json.dumps("TopPiece" if same_name else "OtherPiece"),
                 json.dumps(fastest_hours), json.dumps(top_hours),
                 m.group(1)))
        rc, out = _node(js)
        self.assertEqual(rc, 0, "node refused the shipped statement: %s" % out)
        return json.loads(out) is not None

    def test_a_far_quicker_DIFFERENT_piece_is_named(self):
        self.assertTrue(self._fires(top_hours=84.0, fastest_hours=20.0),
                        "a 20h piece sat beside an 84h headline and the card said nothing — the "
                        "defect he reported, one level up")

    def test_a_MARGINAL_other_piece_is_not_worth_redirecting_him(self):
        self.assertFalse(self._fires(top_hours=84.0, fastest_hours=80.0),
                         "a 5%% gain was reported as worth switching pieces for")

    def test_the_SAME_piece_is_never_offered_as_an_alternative_to_itself(self):
        self.assertFalse(self._fires(top_hours=84.0, fastest_hours=20.0, same_name=True),
                         "it offered the piece he is already hunting as the alternative")

    def test_UNKNOWN_hours_never_redirect_him(self):
        for t, f in ((None, 20.0), (84.0, None), (None, None)):
            self.assertFalse(self._fires(top_hours=t, fastest_hours=f),
                             "a redirect was invented from a missing number (%r/%r)" % (t, f))

    # ---- the precedence, executed ------------------------------------------------------

    def _render(self, elsewhere_js, altpiece_js):
        m = _extract_render(SRC)
        self.assertTrue(m, "the sets disclosure render is gone")
        js = ("var esc=function(s){return String(s);};\n"
              "var _hubHrs=function(h){return h+'h';};\n"
              "var _pieceLabel=function(n){return n;};\n"
              "var _elsewhere=%s; var _altPiece=%s;\n"
              "console.log(String(%s));" % (elsewhere_js, altpiece_js, m))
        rc, out = _node(js)
        self.assertEqual(rc, 0, "node refused the shipped render: %s" % out)
        return out

    def test_when_BOTH_fire_the_same_piece_route_wins(self):
        """⚠ A DELIBERATE CHOICE, NOT AN ACCIDENT OF ORDER. `_elsewhere` names a faster route to
        THE PIECE HE IS ALREADY HUNTING; `_altPiece` sends him after a different item. Printing
        both puts two competing instructions on one line and leaves him to rank them — which is
        the job the card exists to do."""
        out = self._render("{source:'Normal Cow King',hours:20}", "{name:'OtherPiece',expectedHours:5}")
        self.assertIn("faster outside Hell", out,
                      "the same-piece route lost to the cross-piece one: %r" % out)
        self.assertNotIn("quicker below Hell", out,
                         "BOTH disclosures printed on one line: %r" % out)

    def test_the_cross_piece_line_appears_when_elsewhere_is_silent(self):
        out = self._render("null", "{name:'OtherPiece',expectedHours:5}")
        self.assertIn("quicker below Hell", out, "the cross-piece route was computed and not "
                                                 "rendered — built on both ends, not joined: %r" % out)
        self.assertIn("OtherPiece", out, "it named no piece")
        self.assertIn("5h", out, "it named the piece without the time, so he cannot compare it")

    def test_neither_firing_prints_nothing(self):
        out = self._render("null", "null")
        self.assertNotIn("faster outside Hell", out)
        self.assertNotIn("quicker below Hell", out)


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
    {
        "why": "v3431 - THE CROSS-PIECE COMPARISON KILLED. Without it the card shows an 84h Hell "
               "headline while a DIFFERENT piece sits at 20h and says nothing - the same defect he "
               "reported on Cow Kings Hooves, one level up, across pieces instead of across "
               "difficulties of one piece.",
        "file": "control_ui.html",
        "find": "      && _fastestAll.expectedHours <= top.expectedHours * 0.7) ? _fastestAll : null;",
        "replace": "      && false) ? _fastestAll : null;",
        "matches": 1,
    },
    {
        "why": "v3431 - THE PRECEDENCE INVERTED. When both fire, the SAME-PIECE route must win: it "
               "names a faster way to the thing he is already hunting, while the cross-piece line "
               "sends him after a different item. Swapping them quietly re-aims the card.",
        "file": "control_ui.html",
        "find": "        + (_elsewhere ? '<span class=\"hh-alt\"> · \\u26a1 faster outside Hell \\u00b7 <b>'",
        "replace": "        + (false ? '<span class=\"hh-alt\"> · \\u26a1 faster outside Hell \\u00b7 <b>'",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
