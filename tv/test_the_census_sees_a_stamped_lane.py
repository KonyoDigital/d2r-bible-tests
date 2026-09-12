#!/usr/bin/env python3
"""v3003 (#80) — "SUPERVISED" MEANT "IN THE roster LITERAL", AND THAT STOPPED BEING THE ONLY WAY
TO BE WATCHED AT v2994.

A lane that stamps `_lane_tick` (with a period or a declared silence bound) is watched by
lane_liveness without any roster row — and the census kept calling it unsupervised. MEASURED on
the live source 2026-09-12: 20 rows reported unsupervised, 8 of them stamping a lane tick, and the
number of GENUINELY unwatched loops was ZERO. The instrument #80 uses to report supervision gaps
was inventing eight of them, and my own task text repeated the invented number twice before the
running system corrected it.

⚠ THE STAMPS ARE PARSED, NOT GREPPED. This repo's own docstrings write `_lane_tick('...')` in
prose; a substring search would credit a lane for a comment. One law below plants exactly that
ghost and requires it NOT to be credited. [[source-reading-guard]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lane_census as LC  # noqa: E402

#: a minimal source with every case: a roster lane, a stamped lane, an unwatched loop, and a
#: ghost stamp that lives only in a comment. Valid Python ON PURPOSE — the ast path must be the
#: one exercised, because the regex fallback is exactly what the ghost law defends against.
FIXTURE = '''
import threading, time

def _rostered_loop():
    while True:
        time.sleep(5)

def _stamped_loop():
    while True:
        _lane_tick('_stamped_loop', 5)
        time.sleep(5)

def _tvd_stamper():
    while True:
        _lane_tick('tvd-planted', 5)
        time.sleep(5)

def _elsewhere_loop():
    while True:
        time.sleep(5)

def _unwatched_loop():
    # _lane_tick('_ghost_loop', 5)   <- prose. crediting this is the defect the ghost law pins
    while True:
        time.sleep(5)

def start():
    roster = [
        ("tvd-rostered", _rostered_loop),
    ]
    _lane_dormant('_elsewhere_loop', 'its stamps go to another process by design')
    threading.Thread(target=_rostered_loop).start()
    threading.Thread(target=_stamped_loop).start()
    threading.Thread(target=_tvd_stamper).start()
    threading.Thread(target=_elsewhere_loop).start()
    threading.Thread(target=_unwatched_loop).start()
'''


def _row(rows, fn):
    hit = [r for r in rows if r["fn"] == fn]
    return hit[0] if hit else None


class TheCensusSeesAStampedLane(unittest.TestCase):

    def setUp(self):
        self.rows = LC.census(FIXTURE)

    def test_a_lane_that_stamps_a_tick_is_supervised(self):
        r = _row(self.rows, "_stamped_loop")
        self.assertIsNotNone(r, "the stamped loop vanished from the census entirely")
        self.assertTrue(r["supervised"],
                        "it stamps _lane_tick with its own period, so lane_liveness watches it — "
                        "calling it unsupervised is the invented gap this gate exists to end")
        self.assertEqual(r["lane"], "_stamped_loop",
                         "and its lane name is the name it stamps under")

    def test_the_row_says_which_authority_watches_it(self):
        """Roster rows and stamp rows are watched by DIFFERENT mechanisms, and a reader deciding
        where to look for the tick must be told which. [[the-unjoined-end]]"""
        self.assertEqual(_row(self.rows, "_stamped_loop")["via"], "lane_liveness")
        rost = _row(self.rows, "_rostered_loop")
        self.assertTrue(rost["supervised"])
        self.assertEqual(rost["lane"], "tvd-rostered",
                         "a roster row keeps its roster name, not its function name")

    def test_an_unwatched_loop_is_still_unsupervised(self):
        """The widening must not make everything green — an unwatched loop is the finding."""
        r = _row(self.rows, "_unwatched_loop")
        self.assertFalse(r["supervised"],
                         "nothing watches this loop; reporting it supervised hides the one row "
                         "#80 exists to surface")

    def test_a_stamp_in_a_comment_credits_nobody(self):
        """⚠ THE GHOST. `# _lane_tick('_ghost_loop', 5)` is prose. The regex fallback would credit
        it; the ast path must not. If this goes red, the parse path has silently become a grep."""
        stamped = LC._lane_stamps(FIXTURE)
        self.assertIn("_stamped_loop", stamped["strings"])
        self.assertNotIn("_ghost_loop", stamped["strings"],
                         "a lane name that appears only inside a comment was credited as a real "
                         "stamp — the census is reading prose as code")

    def test_a_loop_stamping_a_name_other_than_its_own_is_credited(self):
        """⚠⚠ v3013 — THE LATENT GAP THE ARMY MEASURED: 11 of 20 live stamp strings are
        roster-style tvd-* names, all rescued today only by roster expansion. A future
        NON-rostered loop stamping 'tvd-foo' read unsupervised under string-equality — the
        invented-gap class reborn one naming convention away. The heartbeat credits its
        ENCLOSING function, under the name it actually stamps."""
        r = _row(self.rows, "_tvd_stamper")
        self.assertIsNotNone(r)
        self.assertTrue(r["supervised"],
                        "it beats _lane_tick('tvd-planted') from its own body — lane_liveness "
                        "watches it under that name whatever the function is called")
        self.assertEqual(r["lane"], "tvd-planted",
                         "the lane name is what lane_liveness watches, not the def's name")
        self.assertEqual(r.get("credit"), "heartbeat")

    def test_a_spawn_site_declaration_is_credited_as_declared_not_heartbeat(self):
        """A _lane_dormant made by the SPAWNER is a claim, not a beat — _orphan_watch's real
        stamps go to another process. Supervised yes; but the evidence class must stay visible,
        because a declaration cannot go LATE. [[unknown-stays-unknown]]"""
        r = _row(self.rows, "_elsewhere_loop")
        self.assertIsNotNone(r)
        self.assertTrue(r["supervised"])
        self.assertEqual(r.get("credit"), "declared",
                         "folding a declaration into the same word as a heartbeat is how "
                         "'watched' quietly loses its meaning")

    def test_the_live_source_has_no_stamping_lane_reported_unsupervised(self):
        """The defect pinned on the REAL source, not just the fixture: every thread target that
        stamps a lane tick must read supervised. Measured at the fix: 8 rows moved."""
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        rows = LC.census(src)
        stamped = LC._lane_stamps(src)
        _watched = set(stamped["tick_by_encloser"]) | stamped["declared"]
        wrong = [r["fn"] for r in rows if r["fn"] in _watched and not r["supervised"]]
        self.assertEqual(wrong, [],
                         "these stamp a lane tick and are still reported unsupervised: %s"
                         % ", ".join(wrong))


RED_PROOF = [
    {
        "why": "narrowing supervised back to the roster literal reinvents the eight gaps the "
               "instrument was reporting about lanes lane_liveness already watches",
        "file": "lane_census.py",
        "find": '        _sup = (n in registered) or (_beat is not None) or _decl',
        "replace": '        _sup = (n in registered)',
        "matches": 1,
    },
    {
        "why": "forcing the regex fallback on parseable source turns the stamp reader into a "
               "grep, and the ghost stamp living in a comment gets credited as a real lane",
        "file": "lane_census.py",
        "find": "        tree = ast.parse(src)",
        "replace": "        raise SyntaxError('forced')",
        "matches": 1,
    },
    {
        "why": "dropping the via field leaves a reader unable to tell WHICH authority watches a "
               "supervised lane — roster and lane_liveness are different places to look for the "
               "tick",
        "file": "lane_census.py",
        "find": '                    "credit": ("roster" if n in registered else',
        "replace": '                    "credit": (None if True else',
        "matches": 1,
    },
]

if __name__ == "__main__":
    # ⚠ his console is cp1255 and cannot encode the arrows above; without this a CORRECT tree
    # reports FAILURE because the process dies inside its own print.
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
