# -*- coding: utf-8 -*-
"""A CARD WITH NO FILM MUST SAY SO, AND "RETIRED" MUST NEVER WEAR "UNKNOWN"'S BADGE.

MEASURED 2026-09-13 by GROKBOT on his live console (1470x923, pid 46822, after a CG click opened
the shelf): the top INTAKE/TRIAGE cards paint chrome, titles, dates and READS/FOUND rows, and
their thumbnail slot is CONTINUOUS BLACK. Deeper ANALYZE/STATION cards show real thumbnails —
stash grids, a dungeon frame, a portal — so it is not a render fault. Those runs have no film.

⚠⚠ EVERY INSTRUMENT CALLED THE SHELF GREEN. GET reported `shelf.open true · cards 430 ·
gridCards 425 · visibleCards 425 · filled true · emptyHero false`, and the theatre's own
`painted`/`ink` were true. Only EYES could see the black. A card that is present, measurable and
empty is exactly the shape a GET-based check cannot fail on. [[zero-needs-a-denominator]]

THE JOIN THAT WAS MISSING: /api/sessions has always carried a per-run `footageState`
("retired" | "unknown") and a `footageWhy` sentence. MEASURED: the word `footageState` appeared
in ZERO html files. The server knew, and the screen never asked. [[the-unjoined-end]]

⚠⚠ AND THE TWO STATES ARE NOT ONE FACT:
    retired  the film gave up its information and was THEN released — the lifecycle that WORKED.
             449 of his 2,893 runs are in it.
    unknown  no film and no retention record at all — an absence of evidence, not a completed
             lifecycle. 2,423 runs, of which 2,334 say "no film and no retention record".
Collapsing them would let a run that was never filmed wear the badge of one that finished
properly, which is the same class of lie as a label that outlived its referent.
"""
import io
import os
import re
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.join(HERE, "control_ui.html")


def _between(src, start, end):
    i = src.find(start)
    if i < 0:
        return ""
    j = src.find(end, i + len(start))
    return src[i:j] if j > i else ""


class TestACardWithNoFilmSaysSo(unittest.TestCase):

    def setUp(self):
        with io.open(UI, encoding="utf-8") as fh:
            self.src = fh.read()
        self.region = _between(self.src, "var _coverArt = _coverSrc(sm);", "var heroOpen")
        self.assertTrue(self.region, "could not locate the shelf card's cover-art block")

    def test_the_card_reads_the_footage_state_the_server_sends(self):
        code = "\n".join(ln.split("//", 1)[0] for ln in self.region.splitlines())
        self.assertIn("sm.footageState", code,
                      "the card must ask the run what happened to its film; without this the "
                      "no-film case is indistinguishable from a broken image and says nothing")
        print("card reads sm.footageState: yes")

    def test_retired_and_unknown_never_share_a_label(self):
        code = "\n".join(ln.split("//", 1)[0] for ln in self.region.splitlines())
        self.assertIn("'retired'", code, "the completed lifecycle must be recognised by name")
        self.assertIn("'unknown'", code, "the absent-evidence case must be recognised by name")
        labels = re.findall(r"txt:\s*'([^']*)'", code)
        print("no-film labels: %s" % labels)
        self.assertGreaterEqual(len(labels), 2, "expected a label per state, found %d" % len(labels))
        retired = re.search(r"'retired'[^\n]*txt:\s*'([^']*)'", code)
        self.assertTrue(retired, "the retired branch carries no label")
        self.assertNotIn(retired.group(1).lower(), ("no film", "unknown"),
                         "a run whose film was RETIRED after giving up its information must not "
                         "wear the badge of one that was never filmed at all")

    def test_the_no_film_badge_is_actually_emitted_into_the_hero(self):
        hero = _between(self.src, "var heroOpen = _coverArt", "var whenTxt")
        self.assertTrue(hero, "could not locate the hero template")
        self.assertIn("noimg", hero, "the no-image branch must still exist")
        self.assertIn("shc-nofilm", hero,
                      "the badge is never emitted, so the placeholder stays a silent black box")
        self.assertIn("data-fstate", hero,
                      "the state must reach the DOM so an outside reader can measure it rather "
                      "than judging a colour")
        print("badge emitted into the noimg branch: yes")

    def test_the_badge_has_visible_styling_of_its_own(self):
        """A badge with no CSS is the same silent black box wearing a class name."""
        rules = re.findall(r"\.shc-nofilm[^{]*\{([^}]*)\}", self.src)
        self.assertTrue(rules, ".shc-nofilm has no CSS rule at all")
        body = " ".join(" ".join(r.split()) for r in rules)
        for prop in ("color", "background", "border"):
            self.assertIn(prop, body, ".shc-nofilm declares no %s — it would not be legible "
                                      "against the near-black placeholder gradient" % prop)
        self.assertTrue(re.search(r"\.shc-nf-retired[^{]*\{[^}]*color", self.src),
                        "retired has no colour of its own, so the two states look identical "
                        "even though the words differ")
        print("badge CSS present, and retired is styled distinctly")


    def test_the_badge_does_not_share_a_corner_with_the_title_or_the_pin_row(self):
        """The defect GROKBOT found on his live screen, made checkable.

        v3077 placed the badge at top-left "to avoid the session name and the pin row". That was an
        ASSUMPTION, not a measurement, and it was wrong: `.shc-sess` is `top:9px; left:12px` — the
        same corner — so the badge drew ON TOP OF the title and the glyphs mashed, OCR-ing as
        `Sepbletréfired`. Worst-case legibility: poor. `.shc-tr` owns top-right.

        A corner is (vertical anchor, horizontal anchor). Two absolutely-positioned chips sharing
        both anchors inside one `position:relative` hero WILL overlap. [[visual-regression-detector]]
        """
        def corner(sel):
            for m in re.finditer(re.escape(sel) + r"\s*\{([^}]*)\}", self.src):
                body = " ".join(m.group(1).split())
                if "position: absolute" not in body:
                    continue
                v = "top" if re.search(r"(^|;|\s)top:", body) else (
                    "bottom" if re.search(r"(^|;|\s)bottom:", body) else None)
                h = "left" if re.search(r"(^|;|\s)left:", body) else (
                    "right" if re.search(r"(^|;|\s)right:", body) else None)
                if v and h:
                    return (v, h)
            return None

        badge = corner(".shc-nofilm")
        self.assertIsNotNone(badge, ".shc-nofilm is not absolutely positioned in the hero")
        print("corners — badge %s · title %s · pin-row %s"
              % (badge, corner(".shc-sess"), corner(".shc-tr")))
        for other in (".shc-sess", ".shc-tr"):
            c = corner(other)
            if c is None:
                continue
            self.assertNotEqual(
                badge, c,
                "the no-film badge shares the %s-%s corner with %s. Both are absolute inside the "
                "same hero, so they overlap and the text mashes — which is what shipped in v3077 "
                "and what his own eyes caught" % (badge[0], badge[1], other))


RED_PROOF = [
    {
        "why": "the badge goes back to the corner it shipped in — the same top-left the session "
               "title occupies — so the two absolute chips overlap inside one hero and the glyphs "
               "mash, exactly as his eyes caught on the live console",
        "file": "control_ui.html",
        "find": "  .shc-nofilm { position: absolute; bottom: 8px; left: 8px; z-index: 3;",
        "replace": "  .shc-nofilm { position: absolute; top: 8px; left: 8px; z-index: 3;",
        "matches": 1,
    },
    {
        "why": "the card stops reading footageState, so a run with no film renders the same "
               "silent near-black rectangle as a broken thumbnail and his shelf goes back to "
               "looking green to every GET while the eyes see black",
        "file": "control_ui.html",
        "find": "      var _fState = String(sm.footageState || '');",
        "replace": "      var _fState = '';",
        "matches": 1,
    },
    {
        "why": "a retired run — the lifecycle that WORKED — starts wearing the badge of one that "
               "was never filmed, collapsing two opposite facts into one word",
        "file": "control_ui.html",
        "find": "        ? { cls: 'retired', icon: '\\u2713', txt: 'film retired' }",
        "replace": "        ? { cls: 'retired', icon: '\\u2014', txt: 'no film' }",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
