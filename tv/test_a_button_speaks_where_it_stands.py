#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2798 — A BUTTON THAT MOVED SEAT LEFT ITS VOICE BEHIND, AND HE READ THAT AS A DEAD BUTTON.

⚠⚠ WHAT IT COST, 2026-09-08. He pressed MINI AUTO and reported *"nothing happens when i click mini
automatic"*. Nothing was broken. Driving the endpoint directly answered in one call:

    POST /api/mini_auto {"on":true,"container":"stash"}
      -> {"ok": false, "why": "the newest frame is 3124s old - MINI will not hover off a stale
          screen"}

A correct refusal, with the exact reason, from a working button. He never saw it, because the
handler writes into `#eagle-out` — and v2381 had moved the CARD out of TOOLS to sit beside MINI
while the BOX stayed behind. Its own comment claims *"same id, same handler, same state readout;
only the seat moved."* The id was the same. The readout was left in the other room.

MEASURED across every button handler in the console — the gap between a button and the box it
writes into:

    btn-eagle      -> #eagle-out      21 lines
    btn-ledger     -> #eagle-out       8
    btn-hoverchk   -> #eagle-out      15
    btn-farmgate   -> #farmgate-out   17
    btn-repair     -> #restore-out    42
    ...every other one 2 to 46...
    btn-miniauto   -> #eagle-out     275   <- alone by an order of magnitude

⛔ THE FIX IS v2446'S, FOR v2446'S REASON, quoted from the shelf door it was written for: *"a
message only visible when the thing works is not an error message."* A toast lives outside the
panels and is visible wherever he is standing. The box keeps its copy — this adds a VOICE, it does
not move the RECORD.

★ THE LAW IS GENERAL, NOT ABOUT ONE BUTTON. Any handler whose only reply lands far from the control
that was pressed must also speak. Otherwise the next card that moves seat repeats this exactly, and
the symptom — "nothing happens" — points at the wrong thing every time.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.join(HERE, "control_ui.html")

#: how far a reply may sit from its button before the button must ALSO speak out loud.
#: Every healthy pairing measured 2-46; the defect measured 275. 80 sits well clear of both, so
#: this fires on a card that has genuinely left its panel, not on ordinary layout drift.
MAX_QUIET_GAP = 80


def _src():
    return io.open(UI, encoding="utf-8").read()


def _line_of(src, needle):
    i = src.find(needle)
    return (src.count("\n", 0, i) + 1) if i >= 0 else None


def _handlers(src):
    """-> [(button_id, handler_source)] — PARSED by both-ends anchoring, never a byte window.

    A fixed slice past the end of a handler reads as absent and this law would grade nothing.
    [[source-reading-guard]]
    """
    out = []
    for m in re.finditer(r"\$\('(btn-[a-z0-9\-]+)'\)\.onclick\s*=\s*", src):
        start = m.end()
        end = src.find("\n  };", start)
        if end < 0:
            continue
        out.append((m.group(1), src[start:end]))
    return out


class AButtonSpeaksWhereItStands(unittest.TestCase):

    def test_the_scanner_finds_the_handlers(self):
        """⚠ THE COUNT IS THE TELL. A scanner that finds nothing passes everything."""
        hs = _handlers(_src())
        self.assertGreaterEqual(len(hs), 10,
                                "only %d button handlers found; there were 19 on 2026-09-08. "
                                "Suspect the instrument before the console." % len(hs))
        # v2856 — WAS `btn-miniauto`, REMOVED BY HIS RULING. The law is "the scanner really finds
        # handlers"; it needs a button that certainly exists, and re-pointing it to the primary
        # control keeps that meaning instead of quietly asserting about a different subject.
        self.assertIn("btn-on", [h[0] for h in hs],
                      "the scanner cannot even find the primary ON AIR handler — suspect the "
                      "instrument before the console")

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────
    def test_a_reply_that_lands_far_away_is_ALSO_spoken(self):
        """★★★ The defect, generalised. A handler may write into a distant box — but if that box
        is not where he is looking, it must also toast."""
        src = _src()
        bad = []
        for btn, body in _handlers(src):
            boxes = set(re.findall(r"\$\('([a-z0-9\-]*out[a-z0-9\-]*)'\)", body))
            if not boxes:
                continue
            bl = _line_of(src, 'id="%s"' % btn)
            if bl is None:
                continue
            far = []
            for box in boxes:
                ol = _line_of(src, 'id="%s"' % box)
                if ol is None:
                    continue
                if abs(ol - bl) > MAX_QUIET_GAP:
                    far.append((box, abs(ol - bl)))
            if far and "toast(" not in body:
                bad.append((btn, far))
        self.assertEqual(
            bad, [],
            "these buttons answer into a box more than %d lines away and NEVER speak out loud, so "
            "a refusal renders in a panel he is not looking at and the button reads as dead: %s. "
            "Add a toast — the box keeps its copy, this adds a voice." % (MAX_QUIET_GAP, bad))




    # ══ v2856 — TWO LAWS RETIRED, THEIR SUBJECT WAS REMOVED BY RULING ══════════════════════
    # Konyo, 2026-09-09: "i decided MINI automatic isnt needed.. the whole button surgically
    # remvoe it" / "the blocked/hover mode hide it block it surgically remove it".
    #   test_MINI_AUTO_speaks_on_the_path_that_actually_refused
    #   test_the_record_is_not_MOVED_only_joined
    # Both read `_handlers(_src())["btn-miniauto"]`, and that handler no longer exists. They are
    # DELETED rather than re-pointed at #btn-mini: those two laws were written about the refusal
    # path of the AUTOMATIC sweep specifically (REG-46x, "nothing happens" written 275 lines away),
    # and aiming them at a different button would keep the name while changing what is proven —
    # the exact defect this repo calls a label outliving its referent.
    # The surviving laws still cover the principle for every button that remains.
    # [[label-outlived-referent]] [[the-unjoined-end]]


RED_PROOF = [
    {
        'why': 'The gate protects tv/control_ui.html: any button handler whose only reply lands in a box more than MAX_QUIET_GAP=80 lines from the button must ALSO toast, or a refusal renders in a room he is not looking at and the button reads as dead (the MINI AUTO defect, 275 lines). No surviving handler currently carries a toast(), so the only edit that produces the exact defect class is to repoint a handler\'s reply at a box that lives far from its button. btn-eagle sits at line 7393 and answers into #eagle-out at 7408 (gap 15, healthy). Repointing that single write to #ct-out — an existing box at line 7003 — makes the gap 390 with no voice, which is precisely the regression the law exists to catch. The anchor is the LIVE JS write, not a comment or a message string: it is the one and only occurrence of $(\'eagle-out\') in the file, and the button\'s own id line is untouched, so only one side of the pairing moves (no shared-constant, no both-sides-shrink trap). ⚠ The obvious-looking alternative is a trap I checked and rejected: renaming the box element id (id="eagle-out" -> something else) makes _line_of return None, the box is silently skipped, and the gate stays GREEN.  MEASURED: untampered python3 tv/test_a_button_speaks_where_it_stands.py -> Ran 2 tests, OK (green). Handler sca; tampered (all 1) After replacing all 1 occurrence: Ran 2 tests, FAILED (failures=1). test_the_scanner_finds; reddened law test_a_reply_that_lands_far_away_is_ALSO_spoken (AButtonSpeaksWhereItS; ALONE python3 -m unittest test_a_button_speaks_where_it_stands.AButtonSpeaksWhereItStands.test_a_reply_that_lands_fa.',
        'file': 'control_ui.html',
        'find': "$('eagle-out')",
        'replace': "$('ct-out')",
        'matches': 1,
    },
]


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
