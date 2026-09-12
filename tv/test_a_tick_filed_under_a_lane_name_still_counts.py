# -*- coding: utf-8 -*-
"""THREE VESSELS REPORTED "NO TICK HAS BEEN STAMPED UNDER THIS NAME" WHILE STAMPING PERFECTLY WELL.

MEASURED on his live console 2026-09-12, stable across two consecutive samples (zero drift):

    FLOWING 13 · DORMANT 3 · UNKNOWN 3 · UNTIMED 1
    UNKNOWN in both: _console_beacon_loop, _retro_triage_loop, _warden_loop

All three call `_lane_tick`. Two of them file it under the LANE's name rather than the FUNCTION's:

    _retro_triage_loop  ->  _lane_tick('tvd-retro-triage', ...)
    _warden_loop        ->  _lane_tick('tvd-space-warden', ...)

`_live_of` looked up `watcher` and then `name`, and neither of those is `tvd-retro-triage`. So the
lookup missed, and a MISS was rendered as "no tick has been stamped under this name. It may be
switched off, or never started" — a sentence about a lane that was in fact beating. The ticks were
there the whole time, filed under a name nobody asked for. [[the-unjoined-end]]

⚠ THE LANES ARE DERIVED FROM EACH FUNCTION'S OWN BODY, not declared beside it. 21 functions stamp
lanes today; a table would have to be remembered into every time one is added or renamed. Parsed
with ast, so a lane named in a comment or docstring cannot satisfy it. [[source-reading-guard]]

⚠ AND THE FIRST CUT OF THAT READER RETURNED [] FOR EVERYTHING, SILENTLY. `heart.py` imports only
`os` and `sys`, the reader called `io.open`, the NameError was swallowed by a broad `except`, and
every function read as stamping no lanes — indistinguishable from a measured absence. The cache
now keeps the failure REASON so a broken reader can never again look like an empty one.
[[zero-needs-a-denominator]]
"""
import os
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


class TestATickFiledUnderALaneNameStillCounts(unittest.TestCase):

    def setUp(self):
        heart.__dict__.pop("_STAMPS_CACHE", None)

    def test_the_reader_finds_the_lanes_each_function_stamps(self):
        """Derived, and it must actually derive something — an empty map would make every lookup
        below pass for the wrong reason."""
        heart._stamps_of("_warden_loop")
        cache = {k: v for k, v in (getattr(heart, "_STAMPS_CACHE", {}) or {}).items()
                 if k != "__failed__"}
        self.assertIsNone(
            (getattr(heart, "_STAMPS_CACHE", {}) or {}).get("__failed__"),
            "the lane reader FAILED and said so — good, but it is reading nothing: %r"
            % (getattr(heart, "_STAMPS_CACHE", {}) or {}).get("__failed__"))
        self.assertGreater(
            len(cache), 10,
            "only %d function(s) were found to stamp a lane. control_app stamps from ~21; a "
            "number this low means the reader stopped matching the file, and every lookup that "
            "follows would miss for a reason nobody measured." % len(cache))
        self.assertIn("tvd-retro-triage", heart._stamps_of("_retro_triage_loop"),
                      "_retro_triage_loop's lane is no longer derived from its body")

    def test_a_tick_under_the_lane_name_is_found(self):
        """THE LAW, driven: stamp under the LANE, ask under the FUNCTION, get the beat."""
        import lane_liveness as LL
        real = LL.rows
        LL.rows = lambda *a, **k: [{"lane": "tvd-retro-triage", "state": "FLOWING",
                                    "why": "beat 3s ago", "tickAgeS": 3.0}]
        try:
            got = heart._live_of("_retro_triage_loop", "_retro_triage_loop")
        finally:
            LL.rows = real
        self.assertEqual(
            got.get("state"), "FLOWING",
            "a lane beating under `tvd-retro-triage` still reads %r for _retro_triage_loop. The "
            "tick exists and the census cannot see it — which it then reports as 'never started'."
            % got.get("state"))

    def test_a_genuinely_absent_tick_is_still_a_miss(self):
        """The half that must NOT soften: a lane nobody stamps stays UNKNOWN, or this fix would
        turn every silent thread green."""
        import lane_liveness as LL
        real = LL.rows
        LL.rows = lambda *a, **k: [{"lane": "some-other-lane", "state": "FLOWING",
                                    "why": "beat", "tickAgeS": 1.0}]
        try:
            got = heart._live_of("_retro_triage_loop", "_retro_triage_loop")
        finally:
            LL.rows = real
        self.assertEqual(
            got.get("state"), "UNKNOWN",
            "a vessel whose lanes are NOT beating reported %r. Finding a tick that belongs to "
            "someone else would make an unwatched thread read as alive." % got.get("state"))

    def test_the_freshest_lane_wins_when_a_function_owns_several(self):
        """No function owns two lanes today (measured: 0 of 21), but nothing stops one, and the
        newest beat is the honest answer to 'did this run'."""
        import lane_liveness as LL
        real_rows, real_stamps = LL.rows, heart._stamps_of
        LL.rows = lambda *a, **k: [
            {"lane": "lane-old", "state": "DORMANT", "why": "old", "tickAgeS": 900.0},
            {"lane": "lane-new", "state": "FLOWING", "why": "new", "tickAgeS": 2.0}]
        heart._stamps_of = lambda n: ["lane-old", "lane-new"] if n == "_fake" else []
        try:
            got = heart._live_of("_fake", "_fake")
        finally:
            LL.rows, heart._stamps_of = real_rows, real_stamps
        self.assertEqual(got.get("state"), "FLOWING",
                         "the stale lane won over the fresh one: %r" % got)


RED_PROOF = [
    {
        "why": "removes the lane-name lookup, so a vessel ticking under its LANE's name reports "
               "'no tick has been stamped' — a sentence about a lane that is beating",
        "file": "heart.py",
        "find": "        for _lane in _stamps_of(name) + _stamps_of(watcher):",
        "replace": "        for _lane in []:",
        "matches": 1,
    },
    {
        "why": "makes the lane reader swallow its own failure again and return an empty map, so "
               "every function reads as stamping nothing and a broken reader looks like absence",
        "file": "heart.py",
        "find": '            src = _io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()',
        "replace": '            src = _io.open(os.path.join(HERE, "no_such_file.py"), encoding="utf-8").read()',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
