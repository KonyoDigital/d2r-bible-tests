#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#84 — THE DRAIN'S GREEN THAT LIES (REG-1517): a drain that counts only its own stage says CLEAR
over a river that is not moving.

MEASURED ON THE ALT, 2026-09-29: 126 reels, river EMPTY 91 / PRINTER 33 — all unsealed, the
`reel.route` lock CLOSED ("the heart has never run here") — and retention.drain said
    {state: CLEAR, owed: 0, why: "drained — every reel that cleared every bar and is older than
     the newest 16 has been released; nothing is owed"}
reel_retention.drain_owed() counts the plan's CANDIDATES; a reel held at EMPTY or PRINTER is not
one; so the drain counted the reels that had reached ITS stage and called the other 110 nothing.
Every word was true of the mouth and false of the river, and the doctor row read OK over it.

WHAT THIS LAW DRIVES:
  · the pure reading — reel_retention.blocked_upstream over the river's own last stamps and the
    pass's plan: the ALT's shape reads "blocked upstream: N reel(s) older than the newest 16 are
    waiting at EMPTY x, PRINTER y behind <the owning lane's own reason>", N is exactly the older
    reels at owned stations, the newest KEEP_RECENT and the suite's fixtures are never counted,
    CAPTURE (by design, REG-340) and the mouth are counted BESIDE n, a reel the river never placed
    makes the count a FLOOR, and an unreadable river is None — UNKNOWN, never an empty river;
  · the drain's verdict — drain_state: n > 0 is BLOCKED with owed = n (+ the mouth's own), STOPPED
    stays STOPPED, a measured-empty river keeps CLEAR, and a river that was not read, could not be
    read, or is a floor of 0 turns CLEAR into UNKNOWN — never CLEAR;
  · the console, end to end — the SHIPPED control_app._retention_once on a temp shelf (twenty unsealed
    reels the river places at EMPTY behind a closed reel.route lock, the route lane's own word set):
    the wire says BLOCKED, owed 4 (20 - 16), the lock named; nothing is deleted; the river is read
    from THIS console's own tree; a store that will not read is UNKNOWN on the wire;
  · the doctor row, reading the wire — MISSING when the longest wait is past the console's declared
    bar (RIVER_STUCK_AFTER_S, 6 h, from the river's own arrival stamps), OK inside it, UNKNOWN when
    the wait cannot be read.

⚠ No reel id is written literally here (test_no_pinned_footage); ids are minted from a 2017 stamp.
⚠ Nothing touches his tree: the harness is test_the_river_drains_every_pass's, whose import-time
redirect lands every store in a scratch world. RED_PROOF below.
[[heart-first]] [[unknown-stays-unknown]] [[stale-reading]] [[regression-guard]]
"""
import copy
import os
import shutil
import sys
import unittest
import unittest.mock as mock

import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import console_safe  # noqa: E402
console_safe.enable()

import test_the_river_drains_every_pass as D  # noqa: E402  (its world, clock and pass harness)

RR, CA, CD = D.RR, D.CA, D.CD
H = 3600
NOW = D.BASE_MS + 400 * D.HOUR_MS
OWNED = tuple(CA._RIVER_OWNER)              # the console's own "a lane moves reels out of here" set
LOCK_WHY = "reel.route is LOCKED — the heart has never run here, so nothing has shown that the gates hold"


def _names(n):
    return ["reel_s_%d_%d" % (D.BASE_MS + i * D.HOUR_MS, 100 + i) for i in range(n)]


def _row(station, ago_s):
    return {"station": station, "at": NOW - int(ago_s * 1000)}


def _plan(names, tag="never-chronicle-swept", fixtures=(), candidates=()):
    return {"ok": True,
            "candidates": [{"reel": n, "tag": "eligible"} for n in names if n in candidates],
            "kept": [{"reel": n, "tag": ("test-fixture" if n in fixtures else tag)}
                     for n in names if n not in candidates]}


def _why_of(station):
    return {"EMPTY": "route lane: " + LOCK_WHY,
            "PRINTER": "vault lane: owes UNKNOWN, 0 read(s) on record"}.get(station, "no lane has moved these on")


class TheUpstreamReading(unittest.TestCase):
    """The pure half — reel_retention.blocked_upstream over the river's last stamps and a plan."""

    def _alt(self, keep=RR.KEEP_RECENT):
        """The ALT's shape: 126 held reels, the 33 oldest at PRINTER, the rest at EMPTY, all 40 h in place."""
        names = _names(126)
        last = dict((n, _row("PRINTER" if i < 33 else "EMPTY", 40 * H)) for i, n in enumerate(names))
        up = RR.blocked_upstream(last, _plan(names), upstream=OWNED, why_of=_why_of, keep_recent=keep,
                                 now_ms=NOW, after_s=CA.RIVER_STUCK_AFTER_S)
        return names, up

    def test_the_alts_shape_is_named_with_the_lock_behind_it(self):
        names, up = self._alt()
        self.assertEqual(up["n"], 126 - RR.KEEP_RECENT, up)
        self.assertEqual(up["stations"], {"EMPTY": 126 - 33 - RR.KEEP_RECENT, "PRINTER": 33}, up)
        self.assertEqual(up["oldestS"], 40 * H, "the wait is not the river's own arrival stamp")
        self.assertEqual(up["afterS"], CA.RIVER_STUCK_AFTER_S, "the bar is not carried for the doctor")
        self.assertTrue(up["complete"])
        self.assertIn("blocked upstream: %d reel(s) older than the newest %d are waiting at EMPTY %d, PRINTER 33 behind "
                      % (126 - RR.KEEP_RECENT, RR.KEEP_RECENT, 126 - 33 - RR.KEEP_RECENT), up["why"])
        self.assertIn(LOCK_WHY, up["why"], "the sentence does not name the lock the reels are behind")
        self.assertIn("PRINTER: vault lane", up["why"])
        self.assertEqual(sorted(up["reasons"]), ["EMPTY", "PRINTER"])

    def test_the_drain_reads_BLOCKED_with_owed_n_over_a_drained_mouth(self):
        _names_, up = self._alt()
        st = RR.drain_state([{"owed": 0}], beat={"works": 0}, now_ms=NOW, upstream=up)
        self.assertEqual(st["state"], "BLOCKED", st)
        self.assertEqual(st["owed"], 126 - RR.KEEP_RECENT)
        self.assertEqual(st["owedAtMouth"], 0, "the mouth's own count is not kept beside the total")
        self.assertIn("blocked upstream", st["why"])
        self.assertNotIn("nothing is owed", st["why"], "the CLEAR sentence survived inside BLOCKED: %s" % st["why"])
        self.assertIs(st["upstream"], up, "the reading is not published on the row")

    def test_the_keep_window_is_the_pass_s_own_not_the_constant(self):
        _n, up8 = self._alt(keep=RR.KEEP_RECENT_UNDER_PRESSURE)
        self.assertEqual(up8["n"], 126 - RR.KEEP_RECENT_UNDER_PRESSURE)
        self.assertEqual(up8["keepRecent"], RR.KEEP_RECENT_UNDER_PRESSURE)

    def test_an_unreadable_river_is_UNKNOWN_never_clear(self):
        up = RR.blocked_upstream(None, _plan(_names(20)), upstream=OWNED, now_ms=NOW, river_why="the store would not read")
        self.assertIsNone(up["n"])
        self.assertIn("UNKNOWN", up["why"])
        self.assertIn("the store would not read", up["why"])
        st = RR.drain_state([{"owed": 0}], beat={"works": 0}, now_ms=NOW, upstream=up)
        self.assertEqual(st["state"], "UNKNOWN", st)
        self.assertIsNone(st["owed"], "an unread river published a confident owed")
        self.assertIn("never CLEAR", st["why"])

    def test_a_river_that_was_never_asked_is_UNKNOWN_and_stopped_stays_stopped(self):
        st = RR.drain_state([{"owed": 0}], beat={"works": 0}, now_ms=NOW)
        self.assertEqual(st["state"], "UNKNOWN", "a mouth read with no river certified the river")
        self.assertIsNone(st["owed"])
        self.assertIsNone(st["upstream"])
        bar = RR.DRAIN_STOPPED_AFTER_PASSES
        st = RR.drain_state([{"owed": 2}] * bar, beat={"works": 0}, now_ms=NOW)
        self.assertEqual((st["state"], st["owed"]), ("STOPPED", 2), "a stall at the mouth lost its verdict")
        self.assertIn("UNKNOWN", st["why"])

    def test_a_shelf_that_could_not_be_planned_is_UNKNOWN(self):
        up = RR.blocked_upstream({}, {"ok": False, "candidates": [], "kept": []}, upstream=OWNED, now_ms=NOW)
        self.assertIsNone(up["n"])
        up = RR.blocked_upstream({}, None, upstream=OWNED, now_ms=NOW)
        self.assertIsNone(up["n"])

    def test_a_never_placed_older_reel_makes_the_count_a_floor(self):
        names = _names(RR.KEEP_RECENT + 4)
        older = names[:4]
        last = dict((n, _row("EMPTY", 10 * H)) for n in older[:3])      # one older reel never stamped
        up = RR.blocked_upstream(last, _plan(names), upstream=OWNED, why_of=_why_of, now_ms=NOW)
        self.assertEqual((up["n"], up["unplaced"], up["complete"]), (3, 1, False), up)
        self.assertIn("FLOOR", up["why"])
        st = RR.drain_state([{"owed": 0}], beat={"works": 0}, now_ms=NOW, upstream=up)
        self.assertEqual((st["state"], st["owed"]), ("BLOCKED", 3))
        # and a floor of ZERO is not a CLEAR
        up0 = RR.blocked_upstream({}, _plan(names), upstream=OWNED, now_ms=NOW)
        self.assertEqual((up0["n"], up0["unplaced"], up0["complete"]), (0, 4, False), up0)
        st0 = RR.drain_state([{"owed": 0}], beat={"works": 0}, now_ms=NOW, upstream=up0)
        self.assertEqual(st0["state"], "UNKNOWN", "a river that never placed the older reels certified them: %s" % st0)
        self.assertIsNone(st0["owed"])
        # a reel stamped UNKNOWN is the same floor
        upu = RR.blocked_upstream(dict((n, _row("UNKNOWN", 10 * H)) for n in older), _plan(names),
                                  upstream=OWNED, now_ms=NOW)
        self.assertEqual((upu["n"], upu["unknown"], upu["complete"]), (0, 4, False), upu)

    def test_the_shield_the_fixtures_the_mouth_and_by_design_are_beside_n(self):
        names = _names(RR.KEEP_RECENT + 5)
        older = names[:5]
        last = dict((n, _row("EMPTY", 20 * H)) for n in names)          # EVERY reel at EMPTY, the newest too
        last[older[0]] = _row("ROUTED", 20 * H)                          # at the mouth: the deleter's own
        last[older[1]] = _row("CAPTURE", 20 * H)                         # waits on a capture change by design
        up = RR.blocked_upstream(last, _plan(names, fixtures={older[2]}), upstream=OWNED, why_of=_why_of,
                                 now_ms=NOW)
        self.assertEqual(up["n"], 2, "the shield, the fixture, the mouth or CAPTURE leaked into n: %r" % up)
        self.assertEqual(up["stations"], {"EMPTY": 2})
        self.assertEqual(up["atMouth"], 1)
        self.assertEqual(up["byDesign"], {"CAPTURE": 1})
        self.assertEqual(up["older"], 4, "the pinned fixture counted as an older reel")
        self.assertIn("CAPTURE 1 wait by design", up["why"])
        # with no exemption list, CAPTURE is upstream of the mouth like any station before ROUTED
        up_all = RR.blocked_upstream(last, _plan(names, fixtures={older[2]}), now_ms=NOW)
        self.assertEqual(up_all["stations"], {"EMPTY": 2, "CAPTURE": 1})
        self.assertEqual(up_all["byDesign"], {})

    def test_a_measured_empty_river_keeps_CLEAR_with_the_measurement_beside_it(self):
        names = _names(RR.KEEP_RECENT + 2)
        last = dict((n, _row("ROUTED", 1 * H)) for n in names)
        up = RR.blocked_upstream(last, _plan(names), upstream=OWNED, now_ms=NOW)
        self.assertEqual((up["n"], up["complete"], up["atMouth"]), (0, True, 2))
        st = RR.drain_state([{"owed": 2}, {"released": 2}], beat={"works": 2}, now_ms=NOW, upstream=up)
        self.assertEqual((st["state"], st["owed"], st["owedAtMouth"]), ("CLEAR", 0, 0), st)
        self.assertIn("measured over 2 older reel(s)", st["why"])

    def test_STOPPED_at_the_mouth_stays_STOPPED_and_owed_adds_both(self):
        names, up = self._alt()
        bar = RR.DRAIN_STOPPED_AFTER_PASSES
        st = RR.drain_state([{"owed": 2}] * bar, beat={"works": 0}, now_ms=NOW, upstream=up)
        self.assertEqual(st["state"], "STOPPED", st)
        self.assertEqual(st["owed"], 2 + up["n"])
        self.assertEqual(st["owedAtMouth"], 2)
        self.assertIn("blocked upstream", st["why"])
        # the by-design holds (DORMANT / DEFERRED) are overridden: the river's wait is the larger fact
        for kw in ({"on": False}, {"stop_why": None}):
            s2 = RR.drain_state([{"owed": 2}, {"held": "the console is ON AIR (live) — you are filming"}],
                                beat={"works": 0}, now_ms=NOW, upstream=up, **kw)
            self.assertEqual(s2["state"], "BLOCKED", s2)
            self.assertIn("at the mouth:", s2["why"])

    def test_a_lane_that_raises_when_asked_is_named_not_swallowed(self):
        names, _ = self._alt()
        last = dict((n, _row("EMPTY", 40 * H)) for n in names)

        def _boom(_st):
            raise RuntimeError("fixture")
        up = RR.blocked_upstream(last, _plan(names), upstream=OWNED, why_of=_boom, now_ms=NOW)
        self.assertIn("could not be asked (RuntimeError)", up["reasons"]["EMPTY"])
        up = RR.blocked_upstream(last, _plan(names), upstream=OWNED, why_of=None, now_ms=NOW)
        self.assertIn("behind a reason no lane has given", up["why"])

    def test_the_wait_is_unknown_when_no_stamp_carries_a_time(self):
        names = _names(RR.KEEP_RECENT + 2)
        last = dict((n, {"station": "EMPTY"}) for n in names)
        up = RR.blocked_upstream(last, _plan(names), upstream=OWNED, now_ms=NOW)
        self.assertEqual(up["n"], 2)
        self.assertIsNone(up["oldestS"], "a wait nobody stamped read as a number")


class TheConsoleSaysItOnTheWire(D._Base):
    """End to end — the SHIPPED _retention_once on a temp shelf shaped like the ALT."""

    def setUp(self):
        D._Base.setUp(self)
        self.setUpClock()
        self.w = D._World(self, n_finished=0)
        # twenty reels, none sealed (held `vault-owes`), the river placing each at EMPTY 40 h+ ago
        for i in range(RR.KEEP_RECENT + 4):
            self.w.add(sealed=False, at_ms=D.BASE_MS + i * D.HOUR_MS, station="EMPTY")
        self.w.write_ledgers()
        self._bind(self.w)
        # the route lane's own last word, as the console holds it (globals()["_ROUTE_LANE"] = ...)
        self.addCleanup(setattr, CA, "_ROUTE_LANE", CA._ROUTE_LANE)
        CA._ROUTE_LANE = dict(CA._ROUTE_LANE, why=LOCK_WHY)

    def test_the_alts_shape_reads_BLOCKED_with_the_lock_named_and_nothing_deleted(self):
        before = self.w.on_disk()
        r, st = self._pass(free_gb=500.0)
        dr = st["drain"]
        self.assertEqual(self.w.on_disk(), before, "a blocked river lost footage")
        self.assertEqual(dr["state"], "BLOCKED", dr)
        self.assertEqual(dr["owed"], 4, "owed is not the reels older than the newest %d: %r" % (RR.KEEP_RECENT, dr))
        self.assertEqual(dr["owedAtMouth"], 0)
        self.assertEqual(dr["upstream"]["stations"], {"EMPTY": 4})
        self.assertIn("blocked upstream: 4 reel(s) older than the newest %d are waiting at EMPTY 4 behind EMPTY: "
                      "route lane: %s" % (RR.KEEP_RECENT, LOCK_WHY), dr["why"])
        self.assertEqual(dr["upstream"]["afterS"], CA.RIVER_STUCK_AFTER_S)
        self.assertGreater(dr["upstream"]["oldestS"], CA.RIVER_STUCK_AFTER_S, "premise: the wait is past the bar")
        for k in ("on", "worked", "lastTs", "owed"):
            self.assertIn(k, dr, "the drain does not answer %r" % k)
        verdict, why = self._doctor(st)
        self.assertEqual(verdict, "missing", "the doctor read a river blocked for %.0fh as %r: %s"
                         % (dr["upstream"]["oldestS"] / 3600.0, verdict, why))
        self.assertIn("past the %.0fh bar" % (CA.RIVER_STUCK_AFTER_S / 3600.0), why)

    def test_a_young_block_is_OK_and_an_unreadable_wait_is_UNKNOWN(self):
        r, st = self._pass(free_gb=500.0)
        self.assertEqual(st["drain"]["state"], "BLOCKED", "premise")
        young = copy.deepcopy(st)
        young["drain"]["upstream"]["oldestS"] = CA.RIVER_STUCK_AFTER_S - 1
        verdict, why = self._doctor(young)
        self.assertEqual(verdict, "ok", "a river blocked for under the bar went red: %s" % why)
        self.assertIn("inside the", why)
        unread = copy.deepcopy(st)
        unread["drain"]["upstream"]["oldestS"] = None
        verdict, why = self._doctor(unread)
        self.assertEqual(verdict, "unknown", "a wait that could not be read was graded: %s" % why)
        nobar = copy.deepcopy(st)
        nobar["drain"]["upstream"]["afterS"] = None
        self.assertEqual(self._doctor(nobar)[0], "unknown", "a console that declared no bar was graded")

    def test_a_young_block_end_to_end_is_OK(self):
        # the same shelf, the river placing every reel one hour ago
        w = D._World(self, n_finished=0)
        for i in range(RR.KEEP_RECENT + 2):
            w.add(sealed=False, at_ms=D.BASE_MS + i * D.HOUR_MS, station="EMPTY",
                  stamp_at=int(self.clock.t * 1000) - 1 * H * 1000)
        w.write_ledgers()
        self._bind(w)
        r, st = self._pass(free_gb=500.0)
        dr = st["drain"]
        self.assertEqual((dr["state"], dr["owed"]), ("BLOCKED", 2), dr)
        self.assertLess(dr["upstream"]["oldestS"], CA.RIVER_STUCK_AFTER_S)
        self.assertEqual(self._doctor(st)[0], "ok", dr)

    def test_the_river_is_read_from_THIS_consoles_own_tree(self):
        import river_stamp as RS
        # realpath both sides: the fixture root is resolved through realpath (/private/var vs /var on a Mac)
        self.assertEqual(os.path.realpath(RS._store_path()), os.path.realpath(self.w.river),
                         "the drain would read a river outside this console's tree")
        self.assertNotEqual(os.path.dirname(RS._store_path()), HERE, "premise: the world is not tv/")

    def test_an_unreadable_river_is_UNKNOWN_on_the_wire_never_CLEAR(self):
        os.remove(self.w.river)
        os.makedirs(self.w.river)                    # a directory where the store should be: open() raises
        r, st = self._pass(free_gb=500.0)
        dr = st["drain"]
        self.assertEqual(dr["state"], "UNKNOWN", dr)
        self.assertIsNone(dr["owed"], "an unreadable river published a confident owed")
        self.assertIsNone(dr["upstream"]["n"])
        self.assertIn("never CLEAR", dr["why"])
        self.assertEqual(self._doctor(st)[0], "unknown")

    def test_a_drained_mouth_over_a_placed_shelf_is_CLEAR(self):
        """The baseline the law needs to distinguish: finished reels the river placed at ROUTED drain, and
        with nothing older than the shield left upstream the drain is CLEAR and the doctor OK."""
        w = D._World(self, n_finished=RR.KEEP_RECENT + 2)
        self._bind(w)
        r, st = self._pass(free_gb=500.0)
        self.assertEqual(len(r.get("removed") or []), 2, "premise: the two old finished reels drained")
        dr = st["drain"]
        self.assertEqual((dr["state"], dr["owed"], dr["owedAtMouth"]), ("CLEAR", 0, 0), dr)
        self.assertEqual(dr["upstream"]["n"], 0)
        self.assertTrue(dr["upstream"]["complete"])
        self.assertEqual(self._doctor(st)[0], "ok")


RED_PROOF = [
    {
        "why": "2026-09-29 #84 (REG-1517) - reels waiting upstream of the mouth no longer make the drain BLOCKED; "
               "the ALT's 110 read CLEAR again",
        "file": "reel_retention.py",
        "find": "    if n > 0:\n        mouth = out[\"owed\"]\n",
        "replace": "    if False:\n        mouth = out[\"owed\"]\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 #84 (REG-1517) - a river that never placed the older reels certifies them (a floor of 0 "
               "reads CLEAR)",
        "file": "reel_retention.py",
        "find": "            out[\"why\"] = \"the deleter owes nothing at the mouth, but %s\" % up.get(\"why\")\n",
        "replace": "            out[\"state\"] = DRAIN_CLEAR\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 #84 (REG-1517) - the console stops handing the river's reading to the drain (the two "
               "halves unjoined: the wire can never say BLOCKED)",
        "file": "control_app.py",
        "find": "every_s=_RETENTION_EVERY_S, upstream=_up)",
        "replace": "every_s=_RETENTION_EVERY_S, upstream=None)",
        "matches": 1,
    },
    {
        "why": "2026-09-29 #84 (REG-1517) - the console declares no bar, so the doctor can never call a blocked "
               "river MISSING",
        "file": "control_app.py",
        "find": "            after_s=RIVER_STUCK_AFTER_S, river_why=_lwhy)",
        "replace": "            after_s=None, river_why=_lwhy)",
        "matches": 1,
    },
    {
        "why": "2026-09-29 #84 (REG-1517) - the doctor row no longer reads BLOCKED, so a river stuck for days is "
               "UNKNOWN on his screen instead of MISSING",
        "file": "console_doctor.py",
        "find": "    if state == \"BLOCKED\":\n",
        "replace": "    if state == \"BLOCKED\" and False:\n",
        "matches": 1,
    },
]


def tearDownModule():
    D.tearDownModule()


if __name__ == "__main__":
    unittest.main(verbosity=2)
