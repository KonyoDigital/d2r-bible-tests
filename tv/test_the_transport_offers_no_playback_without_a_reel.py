# -*- coding: utf-8 -*-
"""THE TRANSPORT MAY NOT OFFER PLAYBACK FOR A REEL HE HAS NOT OPENED.

Konyo, 2026-09-13, scrolling THE SHELF with no session open:
*"its like showing me buttons for a video on the bottom left ... but i still havent clicked a
session im not in one yet ... it should be like separated it might also be bugged because its
confusing"*.

MEASURED — deliberate geometry, not a render fault:

    #th-shelfov { position:absolute; top:0; bottom: clamp(54px,9vh,72px); z-index:14 }
    .th-strip   { position:absolute; bottom:0;                            z-index:6  }

The overlay stops 54-72px short of the bottom so the strip stays reachable, and its own
padding-bottom exists so "tall cards scroll fully clear of the transport" (v1275). The
reservation is correct. WHAT SITS IN IT was not: while the shelf is a PICKER, play/pause, step,
the timeline, mode, speed and fullscreen act on nothing, and hovering one fires
"Next screenshot (→) — steps every real photo" over a reel that was never opened.

⚠ THE SHELF TOGGLE AND THE SESSION STEPPERS STAY. Removing the 📚 he is mid-gesture toward
would be its own defect; only controls that need a LOADED REEL are hidden.

⚠ KEYED OFF THE OVERLAY, NOT A HAND-MAINTAINED CLASS. The shelf is opened and closed from
several call sites, and a body class would drift on whichever path someone forgot — invisibly,
until he saw the buttons again. [[the-unjoined-end]] [[label-outlived-referent]]
"""
import io
import os
import re
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))
UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()

#: need a loaded reel — meaningless while the shelf is a picker
PLAYBACK = ("th-prev-b", "th-next-b", "th-play", "th-timeline", "th-mode", "th-speed", "th-fs")
#: must survive, or he loses the control he is reaching for
KEPT = ("th-shelf", "th-prev-s", "th-next-s")


def _css(src):
    """The stylesheet with comments stripped — prose must never satisfy this law.
    [[source-reading-guard]] [[feedback-comments-vs-code]]"""
    return re.sub(r"/\*.*?\*/", "", src, flags=re.S)


class TestTheTransportOffersNoPlaybackWithoutAReel(unittest.TestCase):

    def test_every_playback_control_is_hidden_while_the_shelf_is_open(self):
        css = _css(UI)
        missing, found = [], 0
        for cid in PLAYBACK:
            pat = r"body:has\(#th-shelfov:not\(\[hidden\]\)\)[^,{]*#%s\b" % re.escape(cid)
            if re.search(pat, css):
                found += 1
            else:
                missing.append(cid)
        print("playback controls hidden while the shelf is open: %d of %d" % (found, len(PLAYBACK)))
        self.assertEqual([], missing,
                         "these still offer playback over a reel he never opened: %r" % (missing,))

    def test_the_rule_keys_off_the_overlay_not_a_hand_set_class(self):
        css = _css(UI)
        has_rules = re.findall(r"body:has\(#th-shelfov:not\(\[hidden\]\)\)", css)
        stale = re.findall(r"body\.shelf-open\b", css)
        print("overlay-keyed rules: %d · hand-set-class rules: %d" % (len(has_rules), len(stale)))
        self.assertGreaterEqual(len(has_rules), len(PLAYBACK),
                                "each hidden control must read the overlay's REAL state")
        self.assertEqual(0, len(stale),
                         "a class somebody must remember to set WILL drift on the call site they "
                         "forget — and the drift is invisible until he sees the buttons again")

    def test_the_controls_he_still_needs_are_never_hidden(self):
        css = _css(UI)
        wrong = []
        for cid in KEPT:
            if re.search(r"body:has\(#th-shelfov:not\(\[hidden\]\)\)[^,{]*#%s\b" % re.escape(cid), css):
                wrong.append(cid)
        print("controls kept visible: %d of %d" % (len(KEPT) - len(wrong), len(KEPT)))
        self.assertEqual([], wrong,
                         "hiding %r would take away the control he is mid-gesture toward" % (wrong,))

    def test_the_strip_still_exists_at_all(self):
        """A rule that hid the whole strip would pass the law above and break the console."""
        n = len(re.findall(r'class="th-strip"', UI))
        print("th-strip elements in the document: %d" % n)
        self.assertEqual(1, n, "the transport itself must still be in the page")


RED_PROOF = [
    {
        "why": "play/pause goes back to being offered over a reel he never opened — the exact "
               "confusion he reported while scrolling the shelf",
        "file": "control_ui.html",
        "find": "  body:has(#th-shelfov:not([hidden])) .th-strip #th-play,\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "the rule stops reading the overlay's real state and depends on a class a call "
               "site must remember to set — the drift this law exists to refuse",
        "file": "control_ui.html",
        "find": "  body:has(#th-shelfov:not([hidden])) .th-strip #th-prev-b,",
        "replace": "  body.shelf-open .th-strip #th-prev-b,",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
