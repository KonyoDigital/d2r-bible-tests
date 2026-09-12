# -*- coding: utf-8 -*-
"""THE HEART PRINTED `flowing 0` WHILE EVERY VESSEL ROW SAID NOBODY COULD TELL.

`FLOWING` means something precise in this census: *it runs, something watches it, AND a sabotage
has proven the watcher can refuse*. Not one vessel has ever earned it, and the rows were honest
about why — each carried "watched, and NOTHING CAN SCORE THIS WATCHER". Then the legend rendered
that as:

    ● flowing 0

which a reader takes as "none of them are flowing" rather than "nobody can tell". Those are
opposite facts and only one of them is work owed. [[zero-needs-a-denominator]]

⚠⚠ AND IT CANNOT BE EARNED TODAY BY ANY VESSEL, WHICH IS THE POINT. Measured 2026-09-12: the organ
rows the census scores from carry NO `score` field at all — their keys are `evidence, id, line,
measuredAt, state, surfaces` — so `scored` is `{id: None}` for all seven and no watcher can be
scored by any key. The old comment blamed disjoint vocabularies (organ ids vs watcher names); that
is true and it is not the whole truth, because even a perfect key match would return None. There
is no per-watcher sabotage evidence anywhere in this system to earn FLOWING with. That is a
MISSING MEASUREMENT, not a missing quality, and the count must say so.

⚠ THE PERFUSION WASH CANNOT CARRY THIS. With FLOWING null the gradient simply draws no flowing
stop — visually IDENTICAL to zero flowing. The words in the legend are the only place the
difference can live, which is why this law guards the legend and not the picture.

⚠ AND THE LEGEND WAS PHOTOGRAPHED BY NOTHING until v3044 widened the heart target's selector past
`.hrt-h, .hrt-row`. The contradiction between the rows and the count sat on his screen and no
instrument here could have seen it. [[visual-regression-detector]] [[the-unjoined-end]]
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

import heart  # noqa: E402

UI = os.path.join(HERE, "control_ui.html")


class TestFlowingIsUnmeasuredNotZero(unittest.TestCase):

    def setUp(self):
        self.src = io.open(UI, encoding="utf-8").read()

    def test_the_census_reports_None_not_zero_when_nothing_can_score(self):
        """The data half. If any watcher ever becomes scorable this flips to a real number and the
        law stops applying — which is why it asserts the PAIR, not the value."""
        rep = heart.vessels()
        counts = rep.get("counts") or {}
        got = counts.get("FLOWING")
        vs = rep.get("vessels") or []
        self.assertTrue(vs, "no vessels in the census — UNKNOWN, not clean")
        # ⚠⚠ THE PAIR, NOT THE VALUE. My first cut asserted only that FLOWING was None-or-int, and
        # heart2 called it BLIND: the tamper set it to 0 and the law sailed through, because 0 IS
        # a legitimate answer — WHEN a watcher could have been scored and none flowed. What is
        # never legitimate is a NUMBER produced where nothing could be scored at all. So the law
        # asks the two together. [[feedback-blind-fixture-green-gate]]
        _scorable = any(v.get("scorable") for v in vs)
        if not _scorable:
            self.assertIsNone(
                got,
                "FLOWING is %r while NOT ONE of the %d vessels is scorable. A number here is a "
                "figure nobody measured: it reads as 'none are flowing' when the truth is that "
                "no watcher can be scored at all." % (got, len(vs)))
            self.assertTrue(
                str(rep.get("flowingWhy") or "").strip(),
                "FLOWING is None and no reason was given. An unexplained blank is worse than the "
                "zero it replaced — he cannot act on either, and only one of them admits it.")
        else:
            self.assertIsInstance(
                got, int,
                "a watcher IS scorable, so FLOWING must be a real count, not %r" % (got,))

    def test_the_legend_does_not_flatten_a_missing_count_to_a_number(self):
        """THE LAW, and it guards the line he actually reads. `(c.FLOWING || 0)` is the defect:
        in JS, null || 0 is 0, so an unmeasured census renders as a confident zero."""
        m = re.search(r"lg-flowing[^\n]*?flowing\s*<b>'\s*\+\s*([^\n]+?)\+\s*'</b>", self.src)
        self.assertIsNotNone(
            m, "the flowing legend entry could not be found — this law is reading the wrong "
               "surface, and a law that parses nothing passes everything")
        expr = m.group(1)
        self.assertNotIn(
            "|| 0", expr,
            "the flowing count is rendered as `%s`. `null || 0` is 0 in JS, so an UNMEASURED "
            "census prints as a confident zero — the exact reading this law exists to stop."
            % expr.strip())

    def test_the_unmeasured_marker_carries_its_reason(self):
        """An em-dash with no explanation is a different kind of silence."""
        self.assertIn("lg-unmeasured", self.src,
                      "the unmeasured marker is gone from the legend")
        m = re.search(r"lg-unmeasured[^\n]*title=[^\n]*flowingWhy", self.src)
        self.assertIsNotNone(
            m, "the unmeasured marker no longer carries `flowingWhy` as its title, so the reason "
               "the count is blank reaches nobody")

    def test_the_legend_is_inside_the_render_gate_s_frame(self):
        """It was outside every shot until v3044. A surface no instrument photographs is one he is
        the detector for."""
        rc = io.open(os.path.join(HERE, "render_check.py"), encoding="utf-8").read()
        m = re.search(r'"sel":\s*"([^"]*hrt-h[^"]*)"', rc)
        sel = m.group(1) if m else ""
        if not sel:
            m2 = re.search(r'"sel":\s*"(#heart-ov[^"]*)"\s*\n?\s*"([^"]*)"', rc)
            sel = (m2.group(1) + m2.group(2)) if m2 else ""
        self.assertIn(
            "hrt-legend", sel,
            "the heart target's selector (%r) does not include .hrt-legend, so the line printing "
            "the census counts is outside every shot this gate takes." % sel)


RED_PROOF = [
    {
        "why": "restores `(c.FLOWING || 0)`, so an UNMEASURED census prints as a confident zero on "
               "the one line he reads the numbers from",
        "file": "control_ui.html",
        "find": "+ '<span class=\"lg-flowing\">● flowing <b>' + _flowN + '</b></span>'",
        "replace": "+ '<span class=\"lg-flowing\">● flowing <b>' + (c.FLOWING || 0) + '</b></span>'",
        "matches": 1,
    },
    {
        "why": "makes the census report 0 again instead of None, so the count is a figure nobody "
               "measured",
        "file": "heart.py",
        "find": "    if not _scorable:\n        counts[FLOWING] = None",
        "replace": "    if not _scorable:\n        counts[FLOWING] = 0",
        "matches": 1,
    },
    {
        "why": "narrows the heart target back past the legend, putting the census counts outside "
               "every shot the render gate takes",
        "file": "render_check.py",
        "find": '        "sel": "#heart-ov .hrt-h, #heart-ov .hrt-row, #heart-ov .hrt-legend, "',
        "replace": '        "sel": "#heart-ov .hrt-h, #heart-ov .hrt-row, "',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
