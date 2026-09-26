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
import json
import shutil
import subprocess

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


def _between(src, start, end):
    i = src.index(start)
    j = src.index(end, i + len(start))
    return src[i:j + len(end)]


@unittest.skipIf(shutil.which("node") is None, "node is absent - this law is UNMEASURED, not passing")
class AnAnswerActsOnTheQueueItWasAskedAbout(unittest.TestCase):
    """#230 — the second eye on v3497 (grok-4.7): an in-page question does not freeze the page the way
    window.confirm did, so a poll could change the queue between the question and the click and
    'Promote ALL 5' would promote 7. DRIVEN in node: the REAL confirm functions, a stub asker."""

    def _run(self, grow):
        src = UI
        code = (_between(src, "  function _chQueueSig(){", "\n  }")
                + "\n" + _between(src, "  function _chIfUnchanged(sig, again, act){", "\n    };\n  }")
                + "\n" + _between(src, "  function chAcceptAllConfirm(){", "\n  }"))
        js = """
        var CH = { items: [{name:'a'},{name:'b'},{name:'c'},{name:'d'},{name:'e'}] };
        var asked = [], promoted = 0, toasts = [];
        function chAsk(text, label, onYes){ asked.push(label); window.__yes = onYes; }
        function chAcceptAllNow(){ promoted = CH.items.length; }
        function toast(m){ toasts.push(m); }
        var window = {};
        %s
        chAcceptAllConfirm();
        if (%s) CH.items.push({name:'f'}, {name:'g'});
        window.__yes();
        console.log(JSON.stringify({asked: asked, promoted: promoted, toasts: toasts}));
        """ % (code, "true" if grow else "false")
        r = subprocess.run([shutil.which("node"), "-"], input=js, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise AssertionError("node could not run the confirm - UNKNOWN, not passing: %s" % r.stderr[:500])
        return json.loads(r.stdout.strip().splitlines()[-1])

    def test_premise_an_unchanged_queue_is_promoted(self):
        out = self._run(grow=False)
        self.assertEqual(out["promoted"], 5)
        self.assertEqual(out["asked"], ["Promote all 5"])

    def test_a_queue_that_grew_is_asked_again_not_promoted(self):
        out = self._run(grow=True)
        self.assertEqual(out["promoted"], 0, "'Promote ALL 5' promoted a queue of 7")
        self.assertEqual(out["asked"], ["Promote all 5", "Promote all 7"],
                         "the answer did not re-ask with the new count: %r" % out["asked"])


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#230 - an answer acts on a queue that changed after it was asked again (second eye on v3497: 'Promote ALL 5' promotes 7)",
        "file": "control_ui.html",
        "find": "      if (_chQueueSig() !== sig){ toast('The inbox changed while you were deciding - asking again'); again(); return; }\n",
        "replace": "",
        "matches": 1,
    },
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
