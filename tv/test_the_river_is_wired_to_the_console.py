# -*- coding: utf-8 -*-
"""v2746 — THE RIVER IS READ BY THE CONSOLE, AND WALKED BY A TICK.

Konyo: *"something needs to run that river"*, and then: *"the reels going through and getting
filtered and plumbed through the processing system 3d and 4 printer and routes already contructed
just need wiring"*.

=== THE JOINT THIS PINS, AND IT WAS MEASURED AT ZERO ===
    grep -c reel_router tv/control_app.py   ->  0      (before)
`reel_router` assigns one station per reel — the whole stamp — and was read by NO console code.
Built, correct, covered by its own suite, invisible to every surface. That is this repo's single
most repeated defect. [[the-unjoined-end]] [[plumbing-with-no-tap]]

THREE MODULES, THREE QUESTIONS, AND ONLY ONE THAT REMEMBERS:
    reel_router   WHERE IS IT NOW     recomputed every call, stored nowhere
    river_walk    WHO WOULD MOVE IT   the gate -> lane map, read-only
    river_stamp   WHERE HAS IT BEEN   the only one that writes
So a reel had a POSITION and never a JOURNEY. The first walk stamped all 40:
    EMPTY 6 · STATION 7 · PRINTER 11 · JOIN 4 · CAPTURE 12
    NEVER REACHED BY ANY REEL: INTAKE · TRIAGE · ROUTED · TOMBSTONE

⚠⚠ AND THE ROUTE I FIRST WROTE WOULD HAVE SERVED AN EMPTY SHELF. It read
`_cen.get("reelIds")` — A KEY census() DOES NOT HAVE. The real keys are counts/visits/reels/stamps/
unparsed/unreached/everStamped/ok/why/unknown. A missing key read as absent yields a clean-looking
`[]`, so the console would have rendered "no reels" over a store holding forty, and every test that
merely asserted the route returns 200 would have passed. The reel ids must come from the STORE'S OWN
ROWS. [[zero-needs-a-denominator]] [[unknown-stays-unknown]]

⚠ THE WALK RIDES THE **FREE** TICK ON PURPOSE. `tvd-retro-triage` is the free filter;
`tvd-reel-retention` DELETES. river_stamp.run() reads no footage, calls no model and moves no reel —
it records where the router already said each reel was — so it is safe on a 90s tick, and quiet:
stamp() refuses a row identical to the reel's current station, so a still river writes zero bytes.
"""
import ast
import io
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

SRC = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()


def _between(src, start, end):
    """Anchored at BOTH ends. [[source-reading-guard]]"""
    i = src.find(start)
    if i < 0:
        return None
    j = src.find(end, i + len(start))
    return None if j < 0 else src[i:j + len(end)]


def _code_only(blk):
    """Strip `#` comment lines. ⚠ THIS EXISTS BECAUSE THE LAW BELOW FAILED ON ITS OWN PROSE.

    The route carries a comment explaining that an earlier draft read `_cen.get("reelIds")`, and a
    text law looking for that string found it IN THE COMMENT and failed a correct file. TASKS.md
    records the identical trap for task 159: *"Grepping the doc for the old wording still returns a
    hit — inside the note recording the fix. My own prose about a fix satisfying my own search for
    the bug."*

    Read comments before judging a MEASUREMENT; ignore them when judging CODE. This is the second
    kind. [[measured-true-read-wrong]] [[source-reading-guard]]
    """
    out = []
    for ln in (blk or "").split("\n"):
        st = ln.lstrip()
        if st.startswith("#"):
            continue
        out.append(ln.split("  # ")[0] if "  # " in ln else ln)
    return "\n".join(out)


def _fn(name):
    i = SRC.find("def %s(" % name)
    if i < 0:
        return None
    j = SRC.find("\ndef ", i + 1)
    return SRC[i:j if j > i else len(SRC)]


class TheRiverIsWiredToTheConsole(unittest.TestCase):

    # ── ⚠ SUBJECTS MUST EXIST, or every law below grades nothing ──────────────────────────────
    def test_the_guard_can_find_its_subjects_AT_ALL(self):
        self.assertIsNotNone(_fn("_retro_triage_loop"), "the free triage loop is gone or renamed")
        self.assertIn('if path == "/api/river":', SRC, "the /api/river route is gone")

    # ── ⚠⚠ THE JOINT ──────────────────────────────────────────────────────────────────────────
    def test_the_console_READS_the_river(self):
        """The measured defect was literally zero references."""
        n = SRC.count("river_stamp") + SRC.count("reel_router")
        self.assertGreater(n, 0,
                           "control_app.py references neither river_stamp nor reel_router. The "
                           "river is built and nothing reads it — the exact state this fix closed.")

    def test_the_route_derives_reel_ids_from_THE_STORE_not_a_missing_key(self):
        """⚠ THE BUG THIS FILE EXISTS FOR. `_cen.get("reelIds")` is a key census() does not have,
        and it yields [] silently — a shelf that renders empty over forty reels."""
        blk = _between(SRC, 'if path == "/api/river":', 'if path == "/api/reel_story":')
        self.assertIsNotNone(blk, "could not read the /api/river route")
        self.assertNotIn('_cen.get("reelIds")', _code_only(blk),
                         "the route is reading a census key that DOES NOT EXIST again; it will "
                         "serve an empty detail list over a full store")
        self.assertIn('_RVS.rows()', blk,
                      "the route no longer derives reel ids from the store's own rows")

    def test_the_route_keeps_counts_and_visits_SEPARATE(self):
        """Where reels ARE now, versus how often a station was ever reached. Collapsing them makes
        a busy station indistinguishable from a crowded one."""
        blk = _between(SRC, 'if path == "/api/river":', 'if path == "/api/reel_story":')
        code = _code_only(blk)
        for k in ('"counts"', '"visits"'):
            self.assertIn(k, code, "the route no longer publishes %s" % k)

    def test_the_route_publishes_UNREACHED_stations(self):
        """⚠ NOT an empty list dressed as zero. A station no reel has EVER reached is the
        actionable half — ROUTED and TOMBSTONE are both in it today."""
        blk = _between(SRC, 'if path == "/api/river":', 'if path == "/api/reel_story":')
        self.assertIn('"unreached"', _code_only(blk),
                      "the route stopped publishing which stations no reel has ever reached")

    def test_an_unreadable_river_is_NOT_served_as_an_empty_one(self):
        blk = _between(SRC, 'if path == "/api/river":', 'if path == "/api/reel_story":')
        self.assertIn('"ok": False', _code_only(blk),
                      "the route's failure path no longer marks itself not-ok, so an unreadable "
                      "river would render as a river with nothing in it")

    # ── ⚠⚠ THE DRIVEN HALF, AND IT MUST BE THE FREE TICK ──────────────────────────────────────
    def test_a_tick_actually_WALKS_the_river(self):
        blk = _fn("_retro_triage_loop")
        self.assertIn("river_stamp", blk,
                      "no tick walks the river, so it only ever moves when a human calls the "
                      "route — which is the 'built but never runs' state, one layer up")
        self.assertIn(".run(", blk, "the tick imports river_stamp and never runs a walk")

    def test_the_walk_rides_the_FREE_loop_and_not_the_deleting_one(self):
        """⚠ LOAD-BEARING. tvd-retro-triage is the free filter; the retention pass DELETES. A walk
        on the deleting loop would tie a free observation to an irreversible act."""
        self.assertIn("river_stamp", _fn("_retro_triage_loop"))
        ret = _fn("_retention_once") or ""
        self.assertNotIn("river_stamp", ret,
                         "the river walk was moved onto the RETENTION pass, which deletes footage. "
                         "It belongs on the free triage tick.")

    def test_the_walk_names_ITSELF_as_the_actor(self):
        """river_stamp.run() requires `by` and has no default, so a timer's walk and a person's
        cannot wear the same word. Pin that the loop passes a loop-shaped name."""
        blk = _fn("_retro_triage_loop")
        self.assertIn('by="loop:', blk,
                      "the tick's walk does not name itself as a loop, so the store cannot say "
                      "what moved the river")

    def test_a_failed_walk_is_ANNOUNCED_not_swallowed(self):
        """Silence is not evidence. A river that stops being walkable must say so."""
        blk = _fn("_retro_triage_loop")
        self.assertIn("NOT WALKED", blk,
                      "a river that cannot be walked now fails silently on the tick")

    def test_it_still_parses(self):
        ast.parse(SRC)


if __name__ == "__main__":
    unittest.main(verbosity=2)
