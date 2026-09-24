# -*- coding: utf-8 -*-
"""#230 — THE CHRONICLE INBOX, PORTED FROM GROK'S MAILBOX STUDY, ASKS ON THE PAGE AND SHOWS THE ITEM.

His ask, 2026-09-24: "harness what you can from what grok built ... integrate it into the widget mail
too". The study (~/tv-diablo-mailbox, a static demo) restyled the console's own chassis. Ported:
  · the chronicle tome on the rail pill and the window header (art/ui_chronicle.png);
  · the item's own game art, 112px on a lit plate — and an empty plate SAYS "no picture";
  · the three destructive questions (promote all, clear all, dismiss a session) drawn ON THE PAGE:
    a native confirm() blocks the whole window and some embedded webviews answer it NO unseen;
  · the chips' dim/danger variants styled everywhere, not only in the footer (a cross-family look
    found "Junk" and the session dismiss reading as disabled), and the dismiss says "Dismiss".
Pixels: render_check's `ch-inbox` target. This law pins the source shape. RED_PROOF below.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()


def _blocks():
    return [m.group(1) for m in re.finditer(r"<script>(.*?)</script>", UI, flags=re.S)]


def _code(js):
    js = re.sub(r"/\*.{0,6000}?\*/", " ", js, flags=re.S)
    return "\n".join(l.split("//", 1)[0] if l.lstrip().startswith("//") else l for l in js.split("\n"))


class TheInboxAsksOnThePage(unittest.TestCase):

    def test_no_native_dialog_is_left_in_the_inbox(self):
        code = "\n".join(_code(b) for b in _blocks())
        for q in ("Promote ALL", "Clear all", "Dismiss ALL pending"):
            self.assertNotRegex(code, r"window\.confirm\(\s*'" + q,
                                "the inbox still asks '%s' in a native dialog" % q)
        self.assertEqual(code.count("chAsk("), 4, "premise: chAsk is defined once and asked three times")

    def test_the_asker_lives_in_the_block_that_calls_it(self):
        owner = [b for b in _blocks() if "function chAsk(" in b]
        self.assertEqual(len(owner), 1, "chAsk is defined in no block, or in two")
        for caller in ("function chAcceptAllConfirm(", "function chClearAllConfirm(", "ch-sess-dismiss"):
            self.assertIn(caller, owner[0], "%s sits in another script block - a call across the IIFE is a dead render" % caller)

    def test_the_tome_and_the_plate(self):
        self.assertEqual(UI.count('<img class="ch-tome" src="/art/ui_chronicle.png"'), 2, "the pill or the header lost the tome")
        self.assertIn("+ '<div class=\"ch-art-plate\">' + chArtHtml(nm) + '</div>'", UI)
        self.assertIn(".ch-art-plate:empty::after { content: 'no picture';", UI)

    def test_the_chip_variants_are_styled_outside_the_footer(self):
        self.assertIn("  .ch-btn.danger { color: #ffb0a0;", UI)
        self.assertIn("  .ch-btn.dim { color: #c9b88a;", UI)
        self.assertEqual(UI.count(">✕ Dismiss</button>'"), 2, "a session dismiss reads 'All' again")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#230 - 'clear all' asks in a native dialog again: it blocks the window, and some webviews answer NO unseen",
        "file": "control_ui.html",
        "find": "    chAsk('Clear all ' + n + ' pending inbox item'",
        "replace": "    if (!window.confirm('Clear all ' + n + ' pending inbox item')) return; ('Clear all ' + n + ' pending inbox item'",
        "matches": 1,
    },
    {
        "why": "#230 - the session chips' danger variant is footer-only again: the session dismiss reads as disabled",
        "file": "control_ui.html",
        "find": "  .ch-btn.danger { color: #ffb0a0; background: rgba(70,26,20,.5); border-color: rgba(255,120,90,.45); }\n",
        "replace": "",
        "matches": 1,
    },
]
