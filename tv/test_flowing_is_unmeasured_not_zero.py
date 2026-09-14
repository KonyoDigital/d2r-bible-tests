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
import ast as _ast
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
        # ⚠⚠ DRIVE THE INPUT, DO NOT WAIT FOR IT. This law used to reach the unscorable branch
        # only when the LIVE census happened to be unscorable. #80 made 8 vessels scorable, the
        # branch went dead, and heart2 caught this law's own red-proof going BLIND — the tamper
        # put the zero back and nothing refused it. So the decision is now a PURE pair and the
        # law drives BOTH sides every run, whatever the live tree looks like.
        # [[gate-blind-to-unexercised-input]]
        _n, _why = heart.flow_or_unmeasured(0, set(), {}, 12)
        self.assertIsNone(_n, "NOT ONE watcher carries a score and the count came back %r. A "
                              "number here is a figure nobody measured." % (_n,))
        self.assertTrue(_why.strip(), "unmeasured and no reason given — an unexplained blank is "
                                      "worse than the zero it replaced.")
        self.assertEqual(
            heart.flow_or_unmeasured(7, {"w"}, {"w": 0.5}, 12), (7, ""),
            "a watcher IS scored, so the real count must pass through untouched and unexplained.")

        # and the joint: vessels() must actually ASK it. A pure function nobody calls is plumbing
        # with no tap. [[the-unjoined-end]]
        _hsrc = io.open(os.path.join(HERE, "heart.py"), encoding="utf-8").read()
        _v = next((n for n in _ast.parse(_hsrc).body
                   if isinstance(n, _ast.FunctionDef) and n.name == "vessels"), None)
        self.assertIsNotNone(_v, "heart.vessels is gone — this law reads the wrong thing")
        _calls = [c for c in _ast.walk(_v) if isinstance(c, _ast.Call)
                  and getattr(c.func, "id", "") == "flow_or_unmeasured"]
        self.assertEqual(len(_calls), 1,
                         "vessels() calls flow_or_unmeasured %d time(s) — the census decides the "
                         "unmeasured case somewhere this law cannot see." % len(_calls))

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
        m = re.search(  # v3049+: the marker's title= and String(d.flowingWhy) now sit on adjacent lines (escaping was added), so the law spans a bounded few lines instead of one
            r"lg-unmeasured[^\n]*title=(?:[^\n]*\n){0,4}[^\n]*flowingWhy", self.src)
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

    def test_the_placeholder_is_never_a_counted_surface(self):
        """⚠⚠ v3144 — A CENSUS-STATE BIT IN A NODE COUNT MAKES THE FLOOR RIGHT FOR ONLY ONE OF TWO
        LEGAL DOMs. The legend renders the FLOWING count as a number when there is one and
        otherwise as `<span class="lg-unmeasured">—</span>`, and the law directly above guards
        that BOTH states stay reachable. So `.hrt-legend span` is 5 unmeasured and 4 measured:

            FLOWING 8      found 95, floor 95   green, tight
            FLOWING None   found 96, floor 95   a ratchet never refuses an INCREASE
            …and in THAT state one real .hrt-row vanishes -> 95 vs 95 -> GREEN

        The placeholder CANCELS a real loss, which is the one thing a ratchet exists to prevent.
        v3143 excluded it so the count is invariant to census state — and nothing locked that,
        because the law above only asserts the selector CONTAINS "hrt-legend". A revert of the
        `:not(...)` clause would reopen the slack with every test still green, which is the gap a
        cross-family review named. [[regression-guard]] [[zero-needs-a-denominator]]"""
        # ⚠ PARSE, NEVER GREP, WHEN A LAW READS SOURCE — and this one proved why on its first
        # run: a regex anchored on "#heart-ov" matched `heart-fan`'s selector, which starts the
        # same way, and the law failed against a target it was not asking about. TARGETS is read
        # from the AST so "the heart target" means the heart target. [[source-reading-guard]]
        _src = io.open(os.path.join(HERE, "render_check.py"), encoding="utf-8").read()
        _tg = next((n for n in _ast.parse(_src).body
                    if isinstance(n, _ast.Assign)
                    and getattr(n.targets[0], "id", "") == "TARGETS"), None)
        self.assertIsNotNone(_tg, "render_check.TARGETS is gone — this law reads the wrong thing")
        sel = ""
        for _k, _v in zip(_tg.value.keys, _tg.value.values):
            if getattr(_k, "value", None) != "heart":
                continue
            for _kk, _vv in zip(_v.keys, _v.values):
                if getattr(_kk, "value", None) == "sel" and isinstance(_vv, _ast.Constant):
                    sel = str(_vv.value)
        self.assertTrue(sel, "the heart target has no `sel` at all")
        self.assertIn("hrt-legend span", sel,
                      "the heart selector stopped counting the legend's spans (%r)" % sel)
        self.assertIn(":not(.lg-unmeasured)", sel,
                      "the heart selector counts `.lg-unmeasured` (%r) — that span exists ONLY "
                      "while the census is unscorable, so the node count changes with the census "
                      "rather than with the surfaces, and one extra placeholder silently cancels "
                      "one genuinely vanished row." % sel)


    def test_the_unmeasured_reason_counts_only_vessels_something_watches(self):
        """The eye on v3144 caught this: `n_watched` was receiving `len(out)`, and the DARK rows
        are appended to that same list. DARK means "it runs and NOTHING watches it", so the reason
        would have said "N vessel(s) are watched" while counting vessels nobody watches.

        ⚠ DRIVEN, BECAUSE DARK IS 0 TODAY. len(out) and the watched count agree on the live tree
        right now, so a law that read the census would pass through the defect and through its own
        sabotage. [[label-outlived-referent]] [[gate-blind-to-unexercised-input]]"""
        rows = [{"watcher": "w1"}, {"watcher": "w2"}, {"watcher": None}, {}]
        self.assertEqual(
            heart.watched_count(rows), 2,
            "counted %r of 4 rows, 2 of which carry no watcher at all — an unwatched vessel must "
            "never be counted as watched." % (heart.watched_count(rows),))
        self.assertEqual(heart.watched_count([]), 0)
        self.assertEqual(heart.watched_count(None), 0)

        # and the joint: vessels() must hand the flow reason THAT number, not the list length.
        _hsrc = io.open(os.path.join(HERE, "heart.py"), encoding="utf-8").read()
        _v = next((n for n in _ast.parse(_hsrc).body
                   if isinstance(n, _ast.FunctionDef) and n.name == "vessels"), None)
        self.assertIsNotNone(_v, "heart.vessels is gone — this law reads the wrong thing")
        _call = next((c for c in _ast.walk(_v) if isinstance(c, _ast.Call)
                      and getattr(c.func, "id", "") == "flow_or_unmeasured"), None)
        self.assertIsNotNone(_call, "vessels() no longer asks flow_or_unmeasured anything")
        _last = _call.args[-1] if _call.args else None
        self.assertTrue(
            isinstance(_last, _ast.Call) and getattr(_last.func, "id", "") == "watched_count",
            "vessels() passes %s as the watched count — the DARK rows are in that list and they "
            "are by definition unwatched."
            % (_ast.dump(_last)[:60] if _last is not None else "nothing"))


RED_PROOF = [
    {
        "why": "counts every row instead of only the watched ones, so the unmeasured-flow reason "
               "says 'N vessel(s) are watched' while counting DARK rows — which this file defines "
               "as the ones NOTHING watches. A right number under a word that stopped being true",
        "file": "heart.py",
        "find": '    return len([r for r in (rows or []) if (r or {}).get("watcher")])',
        "replace": "    return len(rows or [])",
        "matches": 1,
    },

    {
        "why": "the heart selector goes back to counting `.lg-unmeasured` — a span that exists "
               "ONLY while the census is unscorable — so the node count tracks the CENSUS STATE "
               "rather than the surfaces, the floor can be right for only one of two legal DOMs, "
               "and one extra placeholder silently cancels one genuinely vanished .hrt-row",
        "file": "render_check.py",
        "find": '               "#heart-ov .hrt-legend span:not(.lg-unmeasured)",',
        "replace": '               "#heart-ov .hrt-legend span",',
        "matches": 1,
    },
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
        "find": "        return flow_n, \"\"\n    return None, (",
        "replace": "        return flow_n, \"\"\n    return 0, (",
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
