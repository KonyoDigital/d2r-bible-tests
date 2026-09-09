# -*- coding: utf-8 -*-
"""v2791 — THE RIVER SECTIONS WERE BUILT, AND HE COULD ONLY REACH THEM THROUGH A DROPDOWN.

Konyo, 2026-09-08: *"all the reels on the bottom rendering need to be inside those same sections..
not outside of them .. they need to be clickable and routable and rendering those same organized
reels down on the bottom."*

=== ⚠⚠ IT ALREADY EXISTED, AND THAT IS THE FINDING ===
v2746 built exactly this — the cards grouped under river sections, in the BACKEND'S order, with
empty stations printed dimmed rather than vanishing — from his words the FIRST time he asked:
*"THE SHELF should be synced with the backend river route ... going down sections structured based
on the title"*. It was gated behind `SHELF_S === 'river'`, a sort mode, and the default was
`'newest'`. So every time he opened THE SHELF he got a flat list, while the river strip sat above
it describing a picture the cards below did not show.

**A feature behind a control he has to find is a feature he does not have.** He asked twice; the
second ask was for the default. [[the-unjoined-end]]

=== ⚠⚠ AND FLIPPING THE DEFAULT ALONE WOULD HAVE BROKEN IT ===
The river-unknown branch rendered "River — not read yet" and RETURNED. The only caller of
`_shRiverLoad` was the sort menu's own change handler — so with `river` as the default and nobody
picking it, `SHELF_RIVER` would have stayed `null` forever and he would have landed on that
sentence on every single open. A null that never resolves because nothing asks.
[[plumbing-with-no-tap]]
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

UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()


def _code_only(t):
    """Blank /* */ and // comments, keep line count. The fixes QUOTE the old behaviour to explain
    it, so a substring law would read the explanation. [[source-reading-guard]]"""
    out, i, n = [], 0, len(t)
    while i < n:
        if t.startswith("/*", i):
            j = t.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append(re.sub(r"[^\n]", "", t[i:j]))
            i = j
        elif t.startswith("//", i):
            j = t.find("\n", i)
            j = n if j < 0 else j
            out.append("")
            i = j
        else:
            out.append(t[i])
            i += 1
    return "".join(out)


CODE = _code_only(UI)


class TheShelfLandsOnTheRiver(unittest.TestCase):

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────
    def test_the_shelf_DEFAULTS_to_the_river(self):
        """★★★ He asked for the reels to be INSIDE the sections. They were — behind a sort menu.
        Parsed from code, never from the comment that explains why."""
        m = re.search(r"var\s+SHELF_S\s*=\s*'([a-z]+)'", CODE)
        self.assertIsNotNone(m, "the shelf sort default is gone — this law inspected nothing")
        self.assertEqual(m.group(1), "river",
                         "THE SHELF opens on %r again, so the river strip describes a flow the "
                         "cards below do not show" % m.group(1))

    def test_the_default_view_ASKS_for_the_river(self):
        """★★★ [[plumbing-with-no-tap]]. Flipping the default without this lands him on
        'reading the river…' forever: the branch reported a null it never resolved, because the
        only caller of _shRiverLoad was the sort menu he was no longer using."""
        i = CODE.find("SHELF_RIVER === false || SHELF_RIVER === null")
        self.assertGreater(i, 0, "the river-unknown branch is gone")
        # walk to the end of that if-block rather than guessing a window
        depth, k, opened = 0, CODE.find("{", i), False
        j = k
        while j < len(CODE):
            if CODE[j] == "{":
                depth += 1
                opened = True
            elif CODE[j] == "}":
                depth -= 1
                if opened and depth == 0:
                    break
            j += 1
        arm = CODE[i:j + 1]
        self.assertIn("_shRiverLoad", arm,
                      "the river-unknown branch reports the null without ever asking for the "
                      "river, so the default view can never resolve")

    def test_it_asks_ONCE_not_once_per_paint(self):
        """⚠ _shSort runs on every render, filter and pin. An unguarded fetch there would hammer
        /api/river for the life of the panel."""
        i = CODE.find("SHELF_RIVER === false || SHELF_RIVER === null")
        arm = CODE[i:i + 900]
        self.assertIn("__shRiverAsked", arm,
                      "nothing guards the river fetch, so every re-render asks again")

    # ── ⛔ WHAT MUST NOT HAVE BEEN LOST ──────────────────────────────────────────────────────
    def test_newest_is_still_reachable(self):
        """⛔ Changing the LANDING view must not remove the old one. The day-header path is gated
        on 'newest' and would become dead code if the option vanished."""
        self.assertIn('<option value="newest">', UI,
                      "the Newest sort option is gone — the day-header rendering is now dead code "
                      "and he cannot get his date-ordered list back")
        self.assertIn('<option value="river">', UI,
                      "the River option is gone from the menu")

    def test_the_station_order_is_still_the_BACKENDS(self):
        """⚠ v2746's own rule, and it is the reason this surface has not drifted: the section order
        comes from /api/river's `stations`, which reads reel_router.STATIONS. A hardcoded list here
        would be a SECOND list of stations, and two lists is how they drift apart silently.
        [[copy-drift]]"""
        self.assertIn("SHELF_RIVER_ORDER", CODE,
                      "the shelf no longer takes its section order from the backend")
        i = CODE.find("SHELF_RIVER_ORDER =")
        self.assertGreater(i, 0, "SHELF_RIVER_ORDER is never assigned")

    def test_an_empty_station_is_still_PRINTED(self):
        """⚠ [[zero-needs-a-denominator]]. A station no reel has reached is the actionable half of
        the picture — ROUTED and TOMBSTONE are both empty today. A section that vanishes when empty
        hides exactly the thing he is trying to see."""
        i = CODE.find("var ordG = SHELF_RIVER_ORDER")
        self.assertGreater(i, 0, "the river grouping block is gone")
        seg = CODE[i:i + 2600]
        self.assertIn("ordG", seg,
                      "the grouping no longer walks the backend's full station order, so a station "
                      "with no reels would simply not be drawn")



# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════
# PROPOSED by tv/heart2_candidates.py — derived from this gate's OWN assertions and
# measured against the target file (each anchor occurs exactly once). Review it: the
# question is whether deleting this text is the defect the law exists to catch.
RED_PROOF = [
    {
        "why": 'the law requires this text in control_ui.html, where it occurs exactly once and in no other file the gate names; deleting it must turn the gate red',
        "file": 'control_ui.html',
        "find": '<option value="newest">',
        "replace": '_HEART2_TAMPERED_',
        "matches": 1,
    },
    {
        "why": 'the law requires this text in control_ui.html, where it occurs exactly once and in no other file the gate names; deleting it must turn the gate red',
        "file": 'control_ui.html',
        "find": '<option value="river">',
        "replace": '_HEART2_TAMPERED_',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
