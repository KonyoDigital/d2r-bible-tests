#!/usr/bin/env python3
"""ONE CLASSIFIER, AND NOTHING MAY CLAIM A NAME IT DOES NOT RECOGNISE.  (A21a)

Konyo, 2026-09-02, with a screenshot of the Sets chronicle: "rotting fissure is a sunder charm
related to the uniques chronicle and not the SETS chornicle fix it also."

⚠ FOURTH SHIPMENT OF ONE DEFECT CLASS. v664 walked 62 mod-chronicle uniques into d2r_setPieces;
v1692 routed a find into the physical vault; v1913 put Blood Crescent — a unique Scimitar — on the
Sets bar. v1913 diagnosed it exactly right ("A list of exceptions is not a classifier") and its own
comment PROMISED the cure:

    "⚠ AND `else -> set` IS GONE. A name neither side recognises is claimed by NEITHER bar,
     which is the honest answer: an undo button that cannot undo is worse than no button."

THE CODE NEVER DID IT. `var isS = (rar==='set') || (!listU && rar==='')` kept the catch-all alive
for two hundred versions while the comment above it said otherwise. The comment is the thing people
read, which is why nobody caught it until an item landed on the wrong tab.

MEASURED before the fix, by reading ITEM_CODEX rather than guessing:
    "Latent Rotting Fissure"   IS in the codex   rarity: unique
    "Rotting Fissure"          NOT in the codex  -> _artRarity '' -> claimed by the SETS bar
    and the same for Renewed variants and all six charms.

These are SOURCE checks on bible.html. That is a real limit and it is stated: _undoBar is
closure-scoped and cannot be called from a probe, so the routing half is pinned by reading the
code. The classifier half was measured on the live page (window._artRarity is exported) and is
recorded in the docstring of the case that pins it. [[source-reading-guard]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BIBLE = os.path.join(ROOT, "bible.html")


def _strip_comments(src):
    """JS and HTML comments removed. A guard that reads its own prose is judging the wrong text —
    this repo has paid for that three times today alone."""
    out, i, n = [], 0, len(src)
    while i < n:
        if src.startswith("<!--", i):
            j = src.find("-->", i); i = n if j < 0 else j + 3
        elif src.startswith("/*", i):
            j = src.find("*/", i); i = n if j < 0 else j + 2
        elif src.startswith("//", i) and not src.startswith("://", i - 1):
            j = src.find("\n", i); i = n if j < 0 else j
        else:
            out.append(src[i]); i += 1
    return "".join(out)


class TestNeitherBarClaimsAnUnrecognisedName(unittest.TestCase):
    """★ THE CLASS FIX. Everything else here is a specific case of this one rule."""

    def setUp(self):
        self.code = _strip_comments(io.open(BIBLE, encoding="utf-8").read())

    def test_the_sets_bucket_has_no_catch_all(self):
        m = re.search(r"var\s+isS\s*=\s*([^;]+);", self.code)
        self.assertIsNotNone(m, "the sets-bucket test could not be found — this guard cannot "
                                "answer, which is not the same as passing")
        expr = m.group(1)
        self.assertNotIn("rar===''", expr.replace(" ", ""),
                         "the sets bucket claims names the classifier has no opinion about: %r. "
                         "That is the exact clause v1913's comment says it deleted, and it is how "
                         "a unique lands on the Sets tab with an undo that does nothing." % expr)
        self.assertIn("set", expr, "the sets bucket no longer tests for 'set' at all")

    def test_the_promise_in_the_comment_matches_the_code(self):
        """v1913's comment and v1913's code disagreed for two hundred versions. If a comment
        claims the catch-all is gone, the catch-all must actually be gone."""
        raw = io.open(BIBLE, encoding="utf-8").read()
        claims = "`else -> set` IS GONE" in raw or "else -> set` IS GONE" in raw
        if claims:
            m = re.search(r"var\s+isS\s*=\s*([^;]+);", self.code)
            self.assertNotIn("rar===''", (m.group(1) if m else "").replace(" ", ""),
                             "a comment in this file states the catch-all is gone and the code "
                             "still has it. The comment is the thing people read")


class TestTheSunderCharmsAreUniques(unittest.TestCase):
    """MEASURED ON THE LIVE PAGE after the fix (file:// at the repo root, window._artRarity
    reachable, waited for):

        Rotting Fissure          unique      Cold Rupture           unique
        Latent Rotting Fissure   unique      Flame Rift             unique
        Renewed Rotting Fissure  unique      Black Cleft            unique
        Bone Break               unique      Crack of the Heavens   unique

    with the controls still correct: Aldur's Deception -> set, Blood Crescent -> unique (v1913's
    case), Shako -> basic (claimed by neither bar). Sabotaged by removing the clause: every sunder
    name fell back to '' — the defect, reproduced.
    """

    def setUp(self):
        self.code = _strip_comments(io.open(BIBLE, encoding="utf-8").read())

    def test_the_classifier_consults_the_sunder_roster(self):
        self.assertRegex(
            self.code, r"if\s*\(\s*!r\s*&&\s*typeof\s+SUNDER_CHARMS",
            "_artRarity does not consult SUNDER_CHARMS. ITEM_CODEX carries only the 'Latent …' "
            "form, so every bare and 'Renewed …' sunder name falls through the whole chain to '' "
            "and is claimed by whichever bucket takes unknowns")

    def test_it_reads_the_EXISTING_roster_and_does_not_add_a_new_list(self):
        """v1913's lesson, kept enforceable: 'A list of exceptions is not a classifier.' The six
        names must come from the roster the feature already maintains, not from a fifth hand-kept
        copy that will drift the way _UNI_EXTRA did."""
        i = self.code.find("typeof SUNDER_CHARMS")
        self.assertGreater(i, 0)
        window = self.code[i:i + 400]
        for name in ("Rotting Fissure", "Cold Rupture", "Flame Rift", "Bone Break"):
            self.assertNotIn(name, window,
                             "the classifier hardcodes %r instead of reading SUNDER_CHARMS. A "
                             "second copy of a roster is the defect this whole file is about"
                             % name)

    def test_the_roster_still_holds_all_six(self):
        """If the roster shrinks, the classifier silently stops recognising whatever left it — and
        that name goes straight back to being claimed by nobody."""
        m = re.search(r"const\s+SUNDER_CHARMS\s*=\s*\[(.*?)\n\];", self.code, re.S)
        self.assertIsNotNone(m, "the SUNDER_CHARMS roster could not be found")
        names = re.findall(r'n\s*:\s*"([^"]+)"', m.group(1))
        self.assertEqual(len(names), 6,
                         "the sunder roster holds %d entries, not 6: %s" % (len(names), names))
        self.assertIn("Rotting Fissure", names)

    def test_the_variant_prefixes_are_stripped_before_the_lookup(self):
        """The codex holds 'Latent Rotting Fissure'; the ledger and the bar both see bare and
        'Renewed …' forms. A lookup that does not strip the prefix recognises one form in three."""
        i = self.code.find("typeof SUNDER_CHARMS")
        window = self.code[i:i + 400]
        self.assertRegex(window, r"Latent\|Renewed",
                         "the sunder lookup does not strip the Latent/Renewed prefix, so it "
                         "recognises only the bare form and the other two fall through")


if __name__ == "__main__":
    try:
        import console_safe as _cs
        _cs.enable()
    except Exception:
        pass
    unittest.main(verbosity=1)
