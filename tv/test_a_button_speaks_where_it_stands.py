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
        self.assertIn("btn-miniauto", [h[0] for h in hs],
                      "the button this law exists for is gone or renamed — re-point it")

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

    def test_MINI_AUTO_speaks_on_the_path_that_actually_refused(self):
        """⛔ NOT MERELY 'a toast exists somewhere in the handler'. The refusal he hit was the
        `ok: false` branch; a toast on the success path only would have changed nothing for him."""
        body = dict(_handlers(_src())).get("btn-miniauto")
        self.assertIsNotNone(body, "the MINI AUTO handler is gone — re-point this law")
        self.assertIn("toast(", body, "MINI AUTO never speaks out loud")
        # ⚠⚠ LOOK INSIDE THE TOAST CALL, NOT THE WHOLE BODY. My first cut asserted the shape
        # `did not start ... j.why` anywhere in the handler — and the #eagle-out write carries the
        # SAME sentence, so the assertion matched the durable record while the toast said nothing.
        # A sabotage that stripped `why` from the toast stayed GREEN. Caught only because the
        # sabotage was run; a law proved red on one arm and never on the other is half a law.
        # [[sabotage-is-usually-the-wrong-one]] [[feedback-suspect-the-instrument]]
        toasts = re.findall(r"toast\(([^;]{0,400}?)\)\s*;", body.replace("\n", " "))
        self.assertTrue(toasts, "no toast call could be parsed out of the handler")
        fail_toasts = [t for t in toasts if "did not start" in t]
        self.assertTrue(fail_toasts,
                        "no toast covers the did-not-start branch — the arm he actually hit")
        self.assertTrue(
            any("j.why" in t for t in fail_toasts),
            "the did-not-start TOAST does not carry the server's own reason (%r). A toast that "
            "omits `why` reproduces the defect with better manners — he still cannot tell a stale "
            "frame from a missing game window." % fail_toasts)

    def test_the_record_is_not_MOVED_only_joined(self):
        """⚠ The box must KEEP its copy. Replacing the written record with a toast that vanishes
        after a few seconds would trade one invisibility for another."""
        body = dict(_handlers(_src())).get("btn-miniauto") or ""
        self.assertIn("eagle-out", body,
                      "MINI AUTO stopped writing its durable record — a toast disappears, and then "
                      "there is nowhere to look afterwards")


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
