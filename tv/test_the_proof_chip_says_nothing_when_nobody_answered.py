# -*- coding: utf-8 -*-
"""THE VAULT'S PROOF CHIP MUST BE ABSENT WHEN NOBODY ANSWERED — NOT ZERO.

Konyo, looking at the Vault: *"stlll the vault"*. His lockers show 165 items; the vault ledger
proves 14. #105 established *only ledger+proof enters* and the bar could never reach this surface,
because the lockers are built from `owned` + `d2r_muleAssign` and **bible.html has no proof store
at all** — the only `d2r_vault*` keys are Backfill, BackfillUndo, EvidenceRestore, Removed and
RerouteDone. The witnesses live in the console's `vault_accum.json`. [[the-unjoined-end]]

⚠⚠ IT MARKS AND DOES NOT FILTER, and the names are why. The 14 that clear the bar are
Full Rejuvenation Potion, Super Mana Potion, Horadric Cube, Radiance (103 witnesses), six Grand
Charms, Bone Break, Magefist, Heart of the Oak, Renewed Black Cleft — every one a consumable, a
charm or the Cube, and not one a unique or set piece his vault holds. They cleared the bar because
an OCR sweep sees a rejuv potion in every stash frame and a Shako in one. Hiding the unproven
would empty his vault of every real keeper and leave the potions.

⚠⚠ AND THIS PAGE IS ALSO THE PUBLIC SITE, where no console exists and the ask always fails. A
chip reading "⚖ 0" there would be a claim about his vault manufactured from a failed fetch, shown
to strangers. Absent is the only honest rendering of "nobody could look".
[[unknown-stays-unknown]] [[zero-needs-a-denominator]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

BIBLE = os.path.join(REPO, "bible.html")


def _between(src, start, end):
    i = src.find(start)
    if i < 0:
        return None
    j = src.find(end, i + len(start))
    return src[i:j] if j > 0 else None


class TestTheProofChipSaysNothingWhenNobodyAnswered(unittest.TestCase):

    def setUp(self):
        with io.open(BIBLE, encoding="utf-8", errors="replace") as f:
            self.src = f.read()

    # ── UNKNOWN IS NOT ZERO ──────────────────────────────────────────────────────────────────
    def test_the_store_starts_as_nobody_answered(self):
        self.assertIn("window.VAULT_PROVEN = null;", self.src,
                      "VAULT_PROVEN does not start as null, so 'nobody asked' and 'asked and "
                      "found none' are the same value before the first fetch")

    def test_a_failed_ask_leaves_it_null(self):
        """★ The public site has no console. Every ask there fails."""
        fn = _between(self.src, "function _vaultAskProven(", "window._vaultAskProven")
        self.assertIsNotNone(fn, "the asker is gone — re-anchor this gate")
        self.assertNotIn("VAULT_PROVEN = {}", fn,
                         "a failed ask installs an empty map, which renders as '0 proven' — a "
                         "claim about his vault made from a failed fetch")
        self.assertNotIn("VAULT_PROVEN = []", fn, "same, as a list")
        self.assertIn("!Array.isArray(d.proven)", fn,
                      "the asker accepts whatever shape came back; a refusal carrying proven:null "
                      "would be installed as the answer")

    def test_the_chip_is_absent_when_nobody_answered(self):
        """★ THE LAW HE WOULD SEE BROKEN: '⚖ 0' on a page that never reached a console."""
        chip = _between(self.src, "var P = window.VAULT_PROVEN;", "})()")
        self.assertIsNotNone(chip, "the proof chip is gone — re-anchor this gate")
        self.assertIn("if (!P) return '';", chip,
                      "the chip renders even when nobody answered, so the public site would show "
                      "a proof count for his vault that no console ever produced: %s" % chip[:300])

    # ── THE DENOMINATOR BESIDE IT ───────────────────────────────────────────────────────────
    def test_it_counts_the_same_population_the_total_counts(self):
        """The header's `total` is items.length + magicItems.length."""
        chip = _between(self.src, "var P = window.VAULT_PROVEN;", "})()")
        self.assertIn("(items || [])", chip, "the chip does not count the items list")
        self.assertIn("magicItems", chip,
                      "the chip counts `items` alone while the total beside it counts items + "
                      "magicItems — a numerator over one list under a denominator over two")

    # ── BOUNDED, BECAUSE REG-713 WAS THREE UNBOUNDED FETCHES ON THIS PAGE ───────────────────
    def test_the_ask_cannot_hang_forever(self):
        fn = _between(self.src, "function _vaultAskProven(", "window._vaultAskProven")
        self.assertIn("AbortController", fn,
                      "the fetch has no abort, and a fetch that HANGS never rejects — the .catch "
                      "below it is cover, not a guard (REG-713, three times on this page)")
        self.assertIn("setTimeout", fn, "nothing ever fires the abort")
        self.assertIn("__vaultProvenAsked = 0", fn,
                      "the one-shot flag is never cleared on failure, so a console that comes up "
                      "later can never be asked again")

    # ── A CLASS NOBODY STYLES IS A FLAG NOBODY CAN SEE ──────────────────────────────────────
    def test_the_chip_has_a_css_rule_of_its_own(self):
        i = self.src.find(".vm-proven{")
        self.assertGreater(i, 0,
                           "the chip's class is set by the builder and has NO rule, so it renders "
                           "as unstyled text — the exact shape sh-chip-st and sh-chip-stunk both "
                           "shipped in [[plumbing-with-no-tap]]")
        rule = self.src[i:self.src.find("}", i) + 1]
        self.assertTrue(re.search(r"(color|opacity)", rule),
                        "the rule exists but sets nothing visible: %s" % rule)

    # ── AND IT MUST NOT QUIETLY BECOME A FILTER ─────────────────────────────────────────────
    def test_nothing_is_hidden_on_the_strength_of_the_bar(self):
        """★ The 14 are potions and charms. A filter here removes his real vault."""
        chip = _between(self.src, "var P = window.VAULT_PROVEN;", "})()")
        # ⚠ BAN THE BEHAVIOUR, NOT A WORD. The first cut banned the bare token "hidden" and
        # matched the chip's OWN tooltip — "Nothing is hidden by this chip" — so a law about
        # filtering failed on the sentence promising not to filter. Third time today that prose
        # has blinded a guard of mine. [[feedback-comments-vs-code]] [[source-reading-guard]]
        for banned in (".filter(", "display:none", "display: none", "hidden = true",
                       "hidden=true", ".remove()"):
            self.assertNotIn(banned, chip,
                             "the chip block contains %r — it marks, it does not hide. The names "
                             "that clear this bar are consumables and charms, so filtering on it "
                             "would empty his vault of every keeper." % banned)


if __name__ == "__main__":
    unittest.main(verbosity=2)
