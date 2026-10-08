# -*- coding: utf-8 -*-
"""#274 (REG-2045) - A SENTENCE THAT SAYS "PRESS X" NAMES A BUTTON THE PAGE ACTUALLY HAS.

GrokBot tick 415 (#230, console v3621): the Vault's bottom line read "nothing loose — but some filed items sit in the
wrong locker: see VAULT INTEGRITY, or press Auto-Sort ✦" - and no button is called Auto-Sort. The button is
"⚖️ Auto-assign unsorted" (vaultAutoSortByHand), which since #269 also moves what sits in the wrong locker. Two more
sentences (the unsorted row's "would go to … — press Auto-Sort to file it" and the organizer header) named the same
missing control; the integrity "Fix" and "Fix all safe" buttons had no tooltip.

The law reads the shipped bible.html: every "press <Name>" phrase whose name is not a key (Esc, Enter, …) must be the
text of a <button> on the page.
"""
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

KEYS = {"ESC", "Esc", "Enter", "Tab", "Space", "Escape", "ON"}
# the browser's own confirm() dialog buttons - "press Cancel" in a confirm() message names one of these, not page markup
DIALOG = {"Cancel", "OK"}


def _page():
    with open(os.path.join(os.path.dirname(HERE), "bible.html"), encoding="utf-8") as f:
        return f.read()


def _button_labels(src):
    return {re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m)).strip() for m in re.findall(r"<button\b[^>]*>(.*?)</button>", src, re.S)}


class ASentenceNamesOnlyButtonsThePageHas(unittest.TestCase):

    def test_every_vault_press_names_the_real_auto_assign_button(self):
        src = _page()
        labels = _button_labels(src)
        self.assertIn("⚖️ Auto-assign unsorted", labels, "the Auto-assign button itself is gone - re-point this law")
        named = re.findall(r"press (⚖️ [A-Za-z][A-Za-z \-]*?)(?= to | to$|\)|\"|<|$)", src)
        self.assertGreaterEqual(len(named), 3, "the three vault sentences no longer name a button: %r" % named)
        for n in named:
            self.assertIn(n.strip(), labels, "a sentence tells him to press %r and no button has that name" % n)

    def test_no_capitalised_press_names_a_missing_control(self):
        src = _page()
        labels = _button_labels(src)
        bad = []
        for n in re.findall(r"press (?:the )?([A-Z][A-Za-z\-]+(?: [A-Z][A-Za-z\-]+){0,2})(?: ✦)?", src):
            if n in KEYS or n.split(" ")[0] in KEYS or n in DIALOG:
                continue
            if not any(n == l or l.endswith(" " + n) or l.startswith(n) for l in labels):
                bad.append(n)
        self.assertEqual(bad, [], "sentences name controls the page does not have: %r" % sorted(set(bad)))

    def test_the_integrity_fix_buttons_say_what_they_do(self):
        src = _page()
        self.assertEqual(src.count('<button class="va-fix" title="fix this one now: \'+esc(f.detail)+\'"'), 1)
        self.assertEqual(src.count('<button class="va-fixall" title="apply every auto-fixable row above at once'), 1)


RED_PROOF = [
    {"why": "REG-2045 - a vault sentence tells him to press Auto-Sort again, a button the page does not have",
     "file": "bible.html",
     "find": "see VAULT INTEGRITY, or press ⚖️ Auto-assign unsorted\"}",
     "replace": "see VAULT INTEGRITY, or press Auto-Sort ✦\"}",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
