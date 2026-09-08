# -*- coding: utf-8 -*-
"""v2773 — THE ENGINE ROOM HAS ONE HOME, AND IT IS TV·D.

Konyo's ask, the same one that moved the AI READS ticker in v2763: the gameplay home is for
PLAYING. The backend/telemetry surfaces belong on TV·D beside the AI readers.

WHAT MOVED, AND WHY EACH IS BACKEND RATHER THAN GAMEPLAY:
    .signal    the seven engine lamps — Live Eye · Second Eye · Kai · Router · Watchdog ·
               Agent Mind · Master Brain — plus the KAI accuracy gate. Which model families are
               awake is the AI readers' own status.
    #sig-adv   ⚙ ADVANCED: the 👁 WHICH EYES READ three-way provider switch, the util strip and
               the repair box. The engine room itself.

    ⚠⚠ v2775 — THE FLEET IS NO LONGER PART OF IT, and that is HIS correction, not a refactor.
    v2773 moved the whole drawer and he came back with: *"i cant seee advanced seetings. in
    sessions"*, then *"maybe just the FLEET it can be in sessions tab still where it was located
    under on air and mini sections.. instead of the advanced that is not in TV-D, so the FLEET put
    in sessions"*. So `.fleet-box` was MOVED OUT of the drawer to be a sibling of it in the rail.
    The eyes and lamps are the AI readers' own status and belong on TV·D; the fleet is who is
    playing and what they have found, which is a Sessions fact.

=== MEASURED, BEFORE AND AFTER, AT 1440x900 AND AT HIS OWN 1120x660 ===
                                      before      after
    .signal on Sessions               shown       hidden
    ⚙ ADVANCED on Sessions            shown       hidden
    .signal / ADVANCED on a board tab shown       hidden
    Sessions rail overflow @1440      614px       0px
    Sessions rail overflow @375       900px       134px
    THE SHELF button inside the fold  NO          YES  (@1440, @1120, @901)
    ♥ heart chip opens #heart-ov      yes         yes   (all three views)
The rail carried 614px of content past its own bottom on the gameplay home, and THE SHELF — a
gameplay surface, his own reels — was the thing pushed out of reach. Moving the engine room is
what brought it back.

=== THE THREE LAWS ===

  LB1 TWO NEGATIVES, AND `display`.  Only Sessions carries `data-view="sessions"`; `_toTVD()` and
      every board tab REMOVE it, so "not sessions" alone still leaves these under Runewords,
      Crafts, Uniques, Sets, Tools and Vault — measured: before this change they were visible on
      a board tab too. `body.shell-open` marks a board tab. TV·D is the one state that is neither.
      `visibility` would leave the flex boxes and their gaps behind, which is the blank-band class
      of defect this console has already paid for twice.

  LB2 THE HIDE MUST OUTRANK `aside.rail .signal`.  That rule sets `display: flex` and is (0,2,1).
      A bare `body[data-view="sessions"] .signal` is ALSO (0,2,1), and it sits EARLIER in the
      sheet — so it would have lost on source order and done nothing at all while reading as
      perfectly correct. This is the CSS form of the dead-render defect this file has shipped
      six times. The law checks the arithmetic, not the string.
      [[console-ui-two-script-blocks]] [[the-unjoined-end]]

  LB3 IT IS `#sig-adv`, NEVER `.rail-secondary`.  `.rail-secondary` also hosts `#ver-xref` and
      `#heart-ov` — `position: fixed` full-screen overlays — and `#heart-ov` is what the FOOTER's
      ♥ heart chip opens. `display: none` on an ancestor hides a fixed descendant too, so hiding
      the container would have left a live button on the gameplay home opening nothing: both ends
      built, the middle quietly cut. Verified by clicking the chip in all three view states.
      [[the-unjoined-end]]

⚠ EVERY LAW READS EXECUTABLE TEXT WITH COMMENTS STRIPPED — including the paragraphs above and the
ones in control_ui.html, which name `.rail-secondary`, `visibility` and `display: flex` precisely
because they are explaining why those are wrong. [[source-reading-guard]]
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

RAW = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()


def _strip_comments(src):
    src = re.sub(r"<!--.*?-->", " ", src, flags=re.S)
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    return "\n".join("" if ln.lstrip().startswith("//") else ln for ln in src.split("\n"))


CODE = _strip_comments(RAW)


def _specificity(sel):
    """(ids, classes+attrs+pseudo-classes, elements) — enough for the comparison LB2 makes.

    `:not(...)` contributes NOTHING itself and its ARGUMENT counts normally, which is the whole
    reason the shipped selector wins: `body:not([data-view="sessions"])` is one element plus one
    attribute, not one element plus one pseudo-class.
    """
    s = sel.strip()
    # unwrap :not(...) / :is(...) so their arguments are counted, the wrapper is not
    while True:
        m = re.search(r":(?:not|is|where)\(([^()]*)\)", s)
        if not m:
            break
        s = s[:m.start()] + (" " + m.group(1) + " " if m.group(0)[1] != "w" else " ") + s[m.end():]
    ids = len(re.findall(r"#[\w-]+", s))
    cls = len(re.findall(r"\.[\w-]+", s)) + len(re.findall(r"\[[^\]]+\]", s))
    cls += len(re.findall(r"(?<!:):(?!:)[a-z-]+", s))
    s2 = re.sub(r"#[\w-]+|\.[\w-]+|\[[^\]]+\]|::?[a-z-]+", " ", s)
    els = len([t for t in re.split(r"[\s>+~,]+", s2) if t and t != "*"])
    return (ids, cls, els)


def _rules(code):
    """Every flat rule in the sheet as (selector, declarations, index)."""
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", code):
        sel = m.group(1)
        # a selector never spans a previous rule's close or an @media prelude
        cut = max(sel.rfind("}"), sel.rfind("{"))
        yield (sel[cut + 1:].strip(), m.group(2), m.start(2))


def _hide_rule(code):
    """The engine-room hide, found by WHAT IT DOES rather than by how it is spelled.

    ⚠⚠ THIS USED TO ANCHOR ON THE LITERAL SELECTOR, AND THAT MADE LB2 UNFALSIFIABLE. The
    sabotage for LB2 de-specifies the hide and moves it above its rival — exactly the mistake
    a later editor would make — and a lookup keyed to the specific spelling simply stopped
    finding the rule, so LB2 went red saying "the hide is gone" and its specificity arithmetic
    NEVER RAN. A law that only fires on the absence of its own anchor is measuring the anchor.
    Found now by "a rule that hides something, whose selector names .signal and sessions", which
    survives every rewording the law is supposed to judge. [[regression-guard]]
    """
    for sel, decl, i in _rules(code):
        if "sessions" in sel and ".signal" in sel and re.search(r"display|visibility", decl):
            return (sel, decl, i)
    return None


class EngineRoomLaws(unittest.TestCase):

    def test_00_the_surfaces_and_the_rules_are_in_this_file(self):
        for anchor in ('class="signal"', 'id="sig-adv"', 'class="rail-secondary"',
                       'id="heart-ov"', 'id="heart-chip"', "aside.rail .signal"):
            self.assertIn(anchor, CODE,
                          "%r is not in the STRIPPED source — this guard is reading the wrong "
                          "file, or the rail has been restructured and every law below is "
                          "vacuous" % anchor)
        self.assertLess(len(CODE), len(RAW),
                        "the comment stripper removed nothing, so every law below is grading "
                        "prose as well as code")

    def test_LB1_both_negatives_and_display_not_visibility(self):
        r = _hide_rule(CODE)
        self.assertIsNotNone(
            r, "the engine-room hide is gone. `.signal` and ⚙ ADVANCED are backend telemetry and "
               "belong on TV·D beside the AI readers, not on the gameplay home")
        sel, decl, _ = r
        self.assertIn('body[data-view="sessions"]', sel,
                      "the Sessions negative is gone")
        self.assertIn("body.shell-open", sel,
                      "the board-tab negative is gone. `_toTVD()` and every board tab REMOVE "
                      "data-view, so without `shell-open` these leak onto Runewords, Crafts, "
                      "Uniques, Sets, Tools and Vault — measured: that is exactly where they "
                      "were before this change")
        self.assertIn("#sig-adv", sel, "⚙ ADVANCED is no longer covered by the hide")
        self.assertRegex(decl, r"display\s*:\s*none",
                         "the hide no longer uses `display`")
        self.assertNotRegex(
            decl, r"visibility\s*:",
            "`visibility` leaves the flex boxes and their 10px rail gaps behind — that is the "
            "blank-band defect, not a hide")

    def test_LB2_the_hide_outranks_the_rule_that_sets_display_flex(self):
        """`aside.rail .signal { display: flex }` is (0,2,1) and sits EARLIER in the sheet."""
        loser = None
        for sel, decl, i in _rules(CODE):
            if sel.strip().startswith("aside.rail .signal"):
                loser = (sel, decl, i)
                break
        self.assertIsNotNone(loser, "could not find `aside.rail .signal` — its premise has moved")
        _, loser_decl, loser_i = loser
        self.assertRegex(loser_decl, r"display\s*:\s*flex",
                         "`aside.rail .signal` no longer sets display; this law's premise has "
                         "moved and the specificity requirement may be relaxable — re-measure "
                         "before doing so")

        r = _hide_rule(CODE)
        self.assertIsNotNone(r, "the engine-room hide is gone")
        sel, _, hide_i = r
        mine = max(_specificity(p) for p in sel.split(",") if "signal" in p)
        theirs = _specificity("aside.rail .signal")
        self.assertGreaterEqual(
            mine, theirs,
            "the hide is %s and the rule setting `display: flex` is %s. At equal or lower "
            "specificity the hide silently loses and the engine room stays on the gameplay home "
            "while the source reads as if it moved — the CSS form of the dead render this file "
            "has shipped six times" % (mine, theirs))
        if mine == theirs:
            self.assertGreater(
                hide_i, loser_i,
                "the hide ties on specificity and is written EARLIER in the sheet, so source "
                "order hands the win to `display: flex` and the hide does nothing")

    def test_LB3_the_hide_spares_the_container_that_hosts_the_heart_overlay(self):
        """`#heart-ov` is what the footer's ♥ chip opens, and it lives inside `.rail-secondary`."""
        # the premise, checked rather than assumed
        i_rs = CODE.find('class="rail-secondary"')
        i_ho = CODE.find('id="heart-ov"')
        i_adv = CODE.find('id="sig-adv"')
        self.assertGreater(i_ho, i_rs,
                           "#heart-ov no longer sits after .rail-secondary opens — the markup "
                           "moved and this law's premise with it; re-measure before trusting it")
        self.assertGreater(i_adv, i_rs, "#sig-adv is no longer inside .rail-secondary")
        self.assertIn('id="heart-chip"', CODE,
                      "the footer's ♥ chip is gone, so nothing opens #heart-ov and this law is "
                      "about a door that no longer exists")

        r = _hide_rule(CODE)
        self.assertIsNotNone(r, "the engine-room hide is gone")
        sel, _, _ = r
        self.assertNotIn(
            "rail-secondary", sel,
            "the hide reaches `.rail-secondary`, which also hosts #ver-xref and #heart-ov. Those "
            "are position:fixed overlays and `display: none` on an ancestor hides a fixed "
            "descendant too — so the footer's ♥ heart button would still be there, still "
            "clickable, and would open nothing at all. Hide #sig-adv instead")

        # and nothing ELSE may display:none the container under either negative
        for m in re.finditer(r"([^{}]*\.rail-secondary[^{}]*)\{([^}]*)\}", CODE):
            sel2, decl2 = m.group(1), m.group(2)
            if re.search(r'data-view="sessions"|shell-open', sel2) and \
               re.search(r"display\s*:\s*none", decl2):
                self.fail("a rule hides .rail-secondary on the gameplay home: %r — that kills "
                          "#heart-ov, which the footer's ♥ chip opens" % sel2.strip()[:120])


    # ── ⚠⚠ HIS CORRECTION, 2026-09-08 — THE FLEET STAYS REACHABLE FROM SESSIONS ──────────────
    def test_the_fleet_is_NOT_inside_the_advanced_drawer(self):
        """★★ The mechanism, and it is structural rather than a rule. The Sessions hide names
        `.signal` and `#sig-adv`, so ANYTHING left inside that drawer is hidden with it. The fleet
        is only reachable on Sessions because it was moved OUT to be a sibling — no extra CSS keeps
        it visible, and none should be added. Parsed, because `fleet` appears in the drawer's own
        prose and a substring search would be satisfied by the note explaining this move."""
        from html.parser import HTMLParser
        html = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8",
                       errors="replace").read()
        body = re.sub(r"<!--.*?-->", " ", re.sub(r"<(script|style)\b.*?</\1>", " ", html,
                                                 flags=re.S | re.I), flags=re.S)
        void = {"br", "img", "input", "hr", "meta", "link", "source", "use", "path", "circle",
                "rect", "area", "col"}
        chain = {}

        class _P(HTMLParser):
            def __init__(self):
                HTMLParser.__init__(self, convert_charrefs=True)
                self.stack = []

            def handle_starttag(self, tag, attrs):
                d = dict(attrs)
                if tag not in void:
                    self.stack.append((tag, d.get("id"), d.get("class")))
                if d.get("id") == "fleet-list":
                    chain["fleet"] = list(self.stack)

            def handle_endtag(self, tag):
                for k in range(len(self.stack) - 1, -1, -1):
                    if self.stack[k][0] == tag:
                        del self.stack[k:]
                        break

        p = _P()
        p.feed(body)
        self.assertIn("fleet", chain, "#fleet-list is gone from control_ui.html entirely")
        ids = [i for _, i, _ in chain["fleet"]]
        self.assertNotIn("sig-adv", ids,
                         "THE FLEET is back inside the ADVANCED drawer, so the Sessions hide takes "
                         "it with them and he cannot see it from Sessions again — that is the exact "
                         "thing he asked to be undone on 2026-09-08")
        self.assertTrue(any(c and "rail" in c for _, _, c in chain["fleet"]),
                        "the fleet left the rail altogether; it is supposed to sit under ON AIR and "
                        "MINI where he goes looking for it")

    def test_the_fleet_is_MOVED_not_COPIED(self):
        """⛔ Two fleet blocks would be two things that must stay in step and eventually will not.
        [[copy-drift]]"""
        html = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8",
                       errors="replace").read()
        body = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
        self.assertEqual(1, body.count('class="fleet-box"'),
                         "there is more than one fleet block in the markup")
        self.assertEqual(1, body.count('id="fleet-list"'),
                         "there is more than one #fleet-list")

    def test_the_hide_rule_still_names_only_the_engine_room(self):
        """⚠ THE FIXTURE FOR THE LAW ABOVE. Being a sibling only helps while the hide names
        `#sig-adv` and `.signal` specifically. If it ever widens to the rail or to
        `.rail-secondary` with `display:none`, the fleet goes dark again and the structural
        argument silently stops holding."""
        html = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8",
                       errors="replace").read()
        css = re.sub(r"/\*.*?\*/", " ", html, flags=re.S)
        self.assertIn('body[data-view="sessions"] aside.rail #sig-adv', css,
                      "the Sessions hide no longer names #sig-adv")
        self.assertNotIn('body[data-view="sessions"] aside.rail .fleet-box', css,
                         "a rule now hides the fleet on Sessions by name")
        self.assertNotIn('body[data-view="sessions"] aside.rail { display: none',
                         css.replace("\n", " "),
                         "the whole rail is hidden on Sessions, which takes the fleet with it")


if __name__ == "__main__":
    unittest.main(verbosity=2)
