# -*- coding: utf-8 -*-
"""2026-09-27 — A SHADOW SESSION ROLLS OVER EVERY HOUR, AND THE NEXT ONE FOLLOWS WITHIN SECONDS.

HIS ASK: "each session shadow reader should automatically be hourly like lets say console is on for two
hours.. it should be 1 hour and the session closes and continue another session but instantly.. like
just so they can be processed and its not stacking up.."

MEASURED before this: nothing rotated a session. shadow_watch_tick returned at "a reel is already
rolling" and never looked at the reel again, so a shadow reel ran until END SESSION or a dead console -
and the seal, the fold and the river all start when a reel ENDS (stop_agent -> the agent's session_end
row -> after_session_ended). A three-hour evening was one reel nothing could process until it was over.
And because the watcher wrote nothing while any reel rolled, `lookedAt` aged through every ON AIR
session: the heart called a working watcher "not running" after 10 minutes.

WHAT THIS LAW DRIVES - the SHIPPED shadow_watch_tick, with only the edges stubbed (start_agent,
stop_agent, _agent_alive, the clock, the window finder, the agent's session id), on a TV_HIST fixture:
  · a 61-minute SHADOW reel is closed through stop_agent(farewell=False) - the call /api/off makes -
    and the NEXT look opens a new shadow reel while the window is seen;
  · a 59-minute shadow reel is left alone, and the look is noted with what is rolling and since when;
  · an ON AIR or MINI reel of 3 hours is never touched;
  · game gone -> closed and NOT reopened;
  · a stuck 90-minute shadow reel (a stop that did not take) fires the doctor row, and is not counted;
  · a shadow reel whose start cannot be read, or one this console did not open, is never cut and
    reads UNKNOWN at the doctor;
  · start_agent stamps WHEN beside WHO, under one lock; the limit is one hour and a law can move it;
  · the loop looks again seconds after a rollover, not a whole period later;
  · the lane answers on / worked / lastTs / owed.

⚠ NOTHING REAL IS TOUCHED. start_agent, stop_agent and _force_kill_all_agents would spawn or KILL his
agent (ports are machine-wide, a sandbox does not isolate them), and _mini_sid would GET his live
bridge - every one is stubbed in setUp before any tick runs, and the store path is asserted to sit in
the fixture before anything is written.

REG-1675 (his ruling, 2026-10-01): "should be an hourly session.. starting from 00:00 so its always round", and "if the
game isnt open for like 3 minutes ... and maybe some other safegaurd thats inteligent". MEASURED on his ALT: 13 shadow
reels in 80 minutes, each cut by a 60 s away-seal while the agent's log said the game window was "grab black and not
focused" - the game was running. Now (class TheShadowHourIsTheClockHour, the REAL hour function and probe):
  · a reel begun at 14:40 closes at 15:00, the next runs 15:00 -> 16:00;
  · a window gone while the game RUNS is a pause - the hour stays open; an unanswered probe never cuts;
  · the game truly gone seals after 3 minutes, not before; an hour already cut twice closes only on the clock;
  · every open and close is journalled with its reason (shadow_seals.jsonl), and the doctor warns when an hour fragments.
The cases above keep their meaning with the hour boundary stubbed to "start + 60 min" and the game probe to "gone" -
so none of them depends on the wall clock or on what is running on the machine that runs them. RED_PROOF below.
"""
import ast
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

# the fixture world is declared BEFORE control_app is imported, so nothing resolved at import time
# can describe his tree
_WORLD = tempfile.mkdtemp(prefix="shadow_rollover_")
os.environ["TV_HIST"] = _WORLD

import control_app as ca  # noqa: E402
import health_engine as HE  # noqa: E402
import tv_diablo as tv  # noqa: E402

MIN = 60 * 1000
SID = "s_1789000000000_4242"
GAME = (2002, "Diablo II: Resurrected")


class _Proc(object):
    """An agent child as start_agent leaves it: poll() is None while it runs."""
    pid = 4242

    def __init__(self):
        self.dead = False

    def poll(self):
        return 0 if self.dead else None


class _Base(unittest.TestCase):

    STUBS = ("_shadow_state", "_agent_alive", "mini_state", "start_agent", "stop_agent",
             "_force_kill_all_agents", "_mini_sid", "_shadow_now_ms", "_screen_recording_ok_quick",
             "ON_AIR_FLOOR_GB", "_agent_proc", "_agent_origin", "_agent_since_ms", "_stop_inflight",
             "_shadow_hour_end_ms", "_game_running")

    def setUp(self):
        self.world = tempfile.mkdtemp(prefix="shadow_rollover_case_")
        self.addCleanup(shutil.rmtree, self.world, True)
        self._env = {k: os.environ.get(k) for k in ("TV_HIST", "TV_CAPTURE", "TV_SHADOW_ROTATE_S")}
        os.environ["TV_HIST"] = self.world
        os.environ["TV_CAPTURE"] = "auto"
        os.environ.pop("TV_SHADOW_ROTATE_S", None)
        self._saved = {k: getattr(ca, k) for k in self.STUBS}
        self._finders = (tv.find_d2r_window_mac, tv.find_d2r_window_win)
        self.addCleanup(self._restore)

        self.now = int(time.time() * 1000)     # near the real clock: the health row ages lookedAt by it
        self.alive = False
        self.window = GAME
        self.stop_takes = True
        self.starts, self.stops, self.kills = [], [], []
        ca._shadow_state = lambda: {"on": True, "available": True, "recording": self.alive}
        ca._agent_alive = lambda: self.alive
        ca.mini_state = lambda: {"running": False}
        ca._shadow_now_ms = lambda: self.now
        ca._screen_recording_ok_quick = lambda: True
        ca.ON_AIR_FLOOR_GB = 0
        ca._mini_sid = lambda: SID
        ca._stop_inflight = False
        ca._agent_proc, ca._agent_origin, ca._agent_since_ms = None, "hand", None
        # REG-1675 - the cases below this class's own keep the hour as "start + 60 min" and the game as GONE, so they
        # never depend on the wall clock or on what runs on this machine; TheShadowHourIsTheClockHour uses the real ones
        self.running = False
        ca._shadow_hour_end_ms = lambda since: int(since) + 60 * MIN
        ca._game_running = lambda: self.running
        ca.start_agent = self._start
        ca.stop_agent = self._stop
        ca._force_kill_all_agents = lambda *a, **k: (self.kills.append(a) or
                                                     {"ok": True, "msg": "stub kill"})
        tv.find_d2r_window_mac = lambda *a, **k: self.window
        tv.find_d2r_window_win = lambda *a, **k: self.window
        self.path = ca._shadow_watch_path()
        self.assertTrue(os.path.realpath(self.path).startswith(os.path.realpath(self.world)),
                        "TV_HIST was not honoured (%s) - REFUSING to run against a real store" % self.path)

    def _restore(self):
        for k, v in self._saved.items():
            setattr(ca, k, v)
        tv.find_d2r_window_mac, tv.find_d2r_window_win = self._finders
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    # ── the edges, doing what the real ones do to the state the rollover reads ───────────────
    def _start(self, *a, **k):
        """start_agent as the rollover sees it: a child it owns, WHO asked, and WHEN."""
        self.starts.append(dict(k))
        self.begin(k.get("origin", "hand"), self.now)
        return {"ok": True, "msg": "started", "origin": k.get("origin", "hand")}

    def _stop(self, *a, **k):
        self.stops.append(dict(k))
        if self.stop_takes:
            self.alive = False
            if ca._agent_proc is not None:
                ca._agent_proc.dead = True
            return {"ok": True, "msg": "session saved · off", "sessionSaved": True}
        return {"ok": True, "msg": "stop requested · forcing", "bridgeDown": False}

    def begin(self, origin, since):
        """A reel rolling, opened by THIS console through `origin`, confirmed at `since`."""
        ca._agent_proc = _Proc()
        ca._agent_origin = origin
        ca._agent_since_ms = since
        self.alive = True

    def record(self):
        with io.open(self.path, encoding="utf-8") as fh:
            return json.load(fh)

    def doctor(self):
        return HE.check_shadow_watch()


class AShadowSessionRollsOverEveryHour(_Base):

    def test_a_61_minute_shadow_reel_is_closed_through_the_stop_path_and_the_next_look_opens_another(self):
        self.begin("shadow", self.now - 61 * MIN)
        r = ca.shadow_watch_tick()
        self.assertTrue(r.get("rotated"), "a 61-minute shadow reel was not rolled over: %r" % (r,))
        self.assertEqual(self.stops, [{"farewell": False}],
                         "the reel was not closed through stop_agent(farewell=False) - the one stop "
                         "/api/off, /api/stop and the MINI sealer use: %r" % self.stops)
        self.assertEqual(self.kills, [], "the rollover ended the session by a second route: %r" % self.kills)
        self.assertEqual(self.starts, [], "the rollover started the next reel itself, skipping the door's "
                                          "preflight (window, disk, grant)")
        self.assertEqual(r.get("closed"), "reel_" + SID, "the closed reel was not named: %r" % (r,))
        rec = self.record()
        self.assertEqual(rec.get("rotations"), 1, "the rollover was not counted: %r" % rec)
        self.assertEqual(rec.get("rotatedAt"), self.now)
        self.assertEqual(rec.get("rotatedReel"), "reel_" + SID)
        self.assertIn("in about %d s" % ca._SHADOW_ROTATE_RELOOK_S, rec.get("why") or "",
                      "the note does not say honestly how soon the next reel comes: %r" % rec.get("why"))

        self.now += ca._SHADOW_ROTATE_RELOOK_S * 1000
        r2 = ca.shadow_watch_tick()
        self.assertTrue(r2.get("started"), "the next look did not open a new reel: %r" % (r2,))
        self.assertEqual(len(self.starts), 1)
        self.assertEqual(self.starts[0].get("origin"), "shadow",
                         "the successor reel was not opened through the SHADOW door: %r" % self.starts)
        self.assertEqual(self.doctor().get("state"), "ok",
                         "a rollover that worked read as a fault: %r" % self.doctor())

    def test_switching_shadow_off_still_closes_the_hour_and_does_not_open_another(self):
        ca._shadow_state = lambda: {"on": False, "available": True, "recording": True}
        self.begin("shadow", self.now - 61 * MIN)
        r = ca.shadow_watch_tick()
        self.assertTrue(r.get("rotated"), "the switch being off left an hour-old shadow reel rolling: %r" % r)
        self.assertEqual(self.starts, [], "switching off opened a successor reel")
        self.now += ca._SHADOW_ROTATE_RELOOK_S * 1000
        r2 = ca.shadow_watch_tick()
        self.assertEqual(self.starts, [], "the next look opened a reel while shadow is off: %r" % r2)
        self.assertIn("switched off", r2.get("why") or "")

    def test_switching_shadow_off_does_not_hide_a_reel_the_stop_did_not_take(self):
        ca._shadow_state = lambda: {"on": False, "available": True, "recording": True}
        self.stop_takes = False
        since = self.now - 90 * MIN
        self.begin("shadow", since)
        r = ca.shadow_watch_tick()
        self.assertEqual(len(self.stops), 1, "the rollover was never attempted with the switch off: %r" % r)
        self.assertFalse(r.get("rotated"), r)
        row = self.doctor()
        self.assertEqual(row.get("state"), "warn",
                         "a 90-minute shadow reel with the switch off read as his choice: %r" % row)
        self.assertNotIn("nothing is watching", row.get("line") or "")

    def test_a_shadow_hour_seals_once_the_game_has_been_gone(self):
        self.begin("shadow", self.now - 10 * MIN)
        self.window = None
        first = ca.shadow_watch_tick()
        self.assertEqual(self.stops, [], "one missed look sealed the hour: %r" % first)
        self.now += (ca._SHADOW_AWAY_GRACE_S + 5) * 1000
        second = ca.shadow_watch_tick()
        self.assertEqual(len(self.stops), 1, "the game stayed gone and the hour kept rolling: %r" % second)
        self.assertIs(self.stops[0].get("farewell"), False)

    def test_his_own_session_is_not_sealed_when_the_window_is_gone(self):
        self.begin("hand", self.now - 10 * MIN)
        self.window = None
        self.now += (ca._SHADOW_AWAY_GRACE_S + 5) * 1000
        # the first look only arms the clock; step far enough that a shadow hour would have sealed
        ca.shadow_watch_tick()
        self.now += (ca._SHADOW_AWAY_GRACE_S + 5) * 1000
        ca.shadow_watch_tick()
        self.assertEqual(self.stops, [], "a session he opened was sealed because the window blipped")

    def test_a_59_minute_shadow_reel_is_left_alone_and_the_look_is_noted(self):
        since = self.now - 59 * MIN
        self.begin("shadow", since)
        r = ca.shadow_watch_tick()
        self.assertEqual(self.stops, [], "a 59-minute shadow reel was cut short")
        self.assertEqual(self.starts, [], "a second reel was started over a rolling one")
        self.assertIn("already rolling", r.get("why") or "")
        rec = self.record()
        self.assertEqual((rec.get("rollingDoor"), rec.get("rollingSince")), ("shadow", since),
                         "the look did not record what is rolling and since when: %r" % rec)
        self.assertEqual(rec.get("rollingAt"), rec.get("lookedAt"),
                         "the rolling facts are not stamped with the look that saw them: %r" % rec)
        self.assertEqual(rec.get("lookedAt"), self.now,
                         "a look while a reel rolls left lookedAt to age - the heart reads that as a "
                         "stopped watcher")
        self.assertEqual(self.doctor().get("state"), "ok", "%r" % self.doctor())

    def test_his_own_reels_are_never_cut_whatever_their_age(self):
        for origin, door in (("hand", "onair"), ("mini", "mini")):
            self.begin(origin, self.now - 180 * MIN)
            r = ca.shadow_watch_tick()
            self.assertEqual(self.stops, [], "a 3-hour %s reel he started himself was cut: %r" % (door, r))
            self.assertEqual(self.starts, [])
            self.assertEqual(self.record().get("rollingDoor"), door)
            self.assertEqual(self.doctor().get("state"), "ok",
                             "his own %s reel read as a stuck rollover: %r" % (door, self.doctor()))

    def test_the_game_gone_closes_it_and_does_not_reopen(self):
        self.window = None
        self.begin("shadow", self.now - 61 * MIN)
        ca.shadow_watch_tick()
        self.assertEqual(self.stops, [{"farewell": False}], "an hour-old shadow reel was kept")
        self.now += ca._SHADOW_ROTATE_RELOOK_S * 1000
        r2 = ca.shadow_watch_tick()
        self.assertEqual(self.starts, [], "a new reel opened with Diablo off screen: %r" % (r2,))
        self.assertIn("not on screen", r2.get("why") or "")

    def test_a_stuck_90_minute_shadow_reel_fires_the_doctor_and_is_not_counted(self):
        self.stop_takes = False                       # the stop did not take: the reel still rolls
        since = self.now - 90 * MIN
        self.begin("shadow", since)
        r = ca.shadow_watch_tick()
        self.assertEqual(len(self.stops), 1, "the rollover was never attempted")
        self.assertFalse(r.get("rotated"), "a stop that did not take was reported as a rollover: %r" % (r,))
        rec = self.record()
        self.assertFalse(rec.get("rotations"), "a rollover that did not happen was counted: %r" % rec)
        self.assertEqual((rec.get("rollingDoor"), rec.get("rollingSince")), ("shadow", since))
        row = self.doctor()
        self.assertEqual(row.get("state"), "warn",
                         "a 90-minute shadow reel did not fire the doctor row: %r" % row)
        self.assertIn("STOPPED WORKING", row.get("line") or "")
        self.assertEqual(ca.shadow_watch_contract()["owed"], 1, "the lane does not say a rollover is owed")

    def test_the_doctor_gives_the_rollover_its_slack(self):
        """Baseline: past the hour but inside the margin is OWED, not yet a fault - so the row above
        is firing on the margin, not on any shadow reel at all."""
        self.stop_takes = False
        self.begin("shadow", self.now - 62 * MIN)
        ca.shadow_watch_tick()
        self.assertEqual(self.doctor().get("state"), "ok", "%r" % self.doctor())
        self.assertEqual(ca.shadow_watch_contract()["owed"], 1)

    def test_an_unreadable_start_is_UNKNOWN_and_never_cut(self):
        self.begin("shadow", None)
        r = ca.shadow_watch_tick()
        self.assertEqual(self.stops, [], "a shadow reel of UNKNOWN age was cut on a guess")
        self.assertTrue(r.get("unknown"), "%r" % (r,))
        row = self.doctor()
        self.assertEqual(row.get("state"), "unknown",
                         "a shadow reel whose start cannot be read did not read UNKNOWN: %r" % row)
        self.assertIsNone(ca.shadow_watch_contract()["owed"], "UNKNOWN owed collapsed to a number")

    def test_a_reel_this_console_did_not_open_is_never_cut(self):
        """An orphan from a previous console: the door and the clock in memory describe nothing."""
        ca._agent_proc, ca._agent_origin, ca._agent_since_ms = None, "shadow", self.now - 61 * MIN
        self.alive = True
        ca.shadow_watch_tick()
        self.assertEqual(self.stops, [], "a reel this console never opened was cut on a stale door")
        self.assertEqual(self.doctor().get("state"), "unknown", "%r" % self.doctor())

    def test_the_limit_is_one_hour_and_a_law_can_move_it(self):
        self.assertEqual(ca._SHADOW_ROTATE_AFTER_S, 60 * 60, "his ruling is one hour")
        self.begin("shadow", self.now - 3 * MIN)
        ca.shadow_watch_tick()
        self.assertEqual(self.stops, [], "a 3-minute shadow reel was cut under the one-hour rule")
        os.environ["TV_SHADOW_ROTATE_S"] = "120"
        ca.shadow_watch_tick()
        self.assertEqual(self.stops, [{"farewell": False}],
                         "TV_SHADOW_ROTATE_S was not honoured at call time")


class TheShadowHourIsTheClockHour(_Base):
    """REG-1675 - the real hour function, the real pause rule, the grace, the breaker, the journal, the doctor."""

    def _at(self, hh, mm, ss=0):
        t = time.localtime()
        return int(time.mktime((t.tm_year, t.tm_mon, t.tm_mday, hh, mm, ss, 0, 0, -1)) * 1000)

    def _real_hour(self):
        ca._shadow_hour_end_ms = self._saved["_shadow_hour_end_ms"]

    def test_the_hour_ends_at_the_next_top_of_the_clock(self):
        real = self._saved["_shadow_hour_end_ms"]
        self.assertEqual(real(self._at(14, 40)), self._at(15, 0), "a 14:40 reel's hour does not end at 15:00")
        self.assertEqual(real(self._at(15, 0)), self._at(16, 0))
        self.assertEqual(real(self._at(15, 59, 59)), self._at(16, 0))

    def test_a_reel_begun_at_40_past_closes_at_the_top_of_the_hour(self):
        self._real_hour()
        self.begin("shadow", self._at(14, 40))
        self.now = self._at(14, 59, 30)
        ca.shadow_watch_tick()
        self.assertEqual(self.stops, [], "a reel was closed before its clock hour ended")
        self.now = self._at(15, 0, 5)
        r = ca.shadow_watch_tick()
        self.assertTrue(r.get("rotated"), "a 14:40 reel was not closed at 15:00 - his round hour: %r" % (r,))
        self.assertEqual(self.stops, [{"farewell": False}])

    def test_a_window_gone_while_the_game_runs_is_a_pause_not_an_end(self):
        self.running = True
        self.begin("shadow", self.now - 10 * MIN)
        self.window = None
        for _ in range(4):
            r = ca.shadow_watch_tick()
            self.now += (ca._SHADOW_AWAY_GRACE_S + 5) * 1000
        self.assertEqual(self.stops, [], "the hour was cut while the game still ran (minimized, covered, a menu): %r"
                         % (r,))
        self.assertTrue(r.get("paused"), r)
        self.assertIn("still running", r.get("why") or "")

    def test_an_unanswered_probe_never_cuts(self):
        self.running = None
        self.begin("shadow", self.now - 10 * MIN)
        self.window = None
        for _ in range(3):
            r = ca.shadow_watch_tick()
            self.now += (ca._SHADOW_AWAY_GRACE_S + 5) * 1000
        self.assertEqual(self.stops, [], "a reel was cut on a probe nobody could read: %r" % (r,))
        self.assertIn("cannot be read", r.get("why") or "")

    def test_the_game_truly_gone_seals_after_three_minutes_and_not_before(self):
        self.assertEqual(ca._SHADOW_AWAY_GRACE_S, 180, "his number is three minutes")
        self.begin("shadow", self.now - 10 * MIN)
        self.window = None
        ca.shadow_watch_tick()
        self.now += (ca._SHADOW_AWAY_GRACE_S - 30) * 1000
        ca.shadow_watch_tick()
        self.assertEqual(self.stops, [], "a shadow hour was sealed before the game had been gone three minutes")
        self.now += 60 * 1000
        r = ca.shadow_watch_tick()
        self.assertEqual(len(self.stops), 1, "the game stayed gone past three minutes and the hour kept rolling: %r" % r)
        rec = self.record()
        self.assertEqual((rec.get("awayCutsHour"), rec.get("awayCuts")), (ca._shadow_hour_key(self.now), 1))

    def test_the_breaker_holds_the_rest_of_the_hour(self):
        self.begin("shadow", self.now - 10 * MIN)
        self.window = None
        ca.shadow_watch_tick()
        ca._shadow_watch_note(awayCutsHour=ca._shadow_hour_key(self.now), awayCuts=ca._SHADOW_AWAY_CUTS_PER_HOUR)
        self.now += (ca._SHADOW_AWAY_GRACE_S + 5) * 1000
        r = ca.shadow_watch_tick()
        self.assertEqual(self.stops, [], "an hour already cut %d times was cut again" % ca._SHADOW_AWAY_CUTS_PER_HOUR)
        self.assertIn("only on the clock", r.get("why") or "")

    def test_every_open_and_close_is_journalled_with_its_reason(self):
        path = os.path.join(self.world, "shadow_seals.jsonl")
        self.begin("shadow", self.now - 61 * MIN)
        ca.shadow_watch_tick()                                   # closes on its hour
        self.now += ca._SHADOW_ROTATE_RELOOK_S * 1000
        ca.shadow_watch_tick()                                   # the next look opens a reel
        self.window = None
        ca.shadow_watch_tick()                                   # the game is gone: the clock arms
        self.now += (ca._SHADOW_AWAY_GRACE_S + 5) * 1000
        ca.shadow_watch_tick()                                   # ... and seals
        with io.open(path, encoding="utf-8") as fh:
            rows = [json.loads(l) for l in fh if l.strip()]
        self.assertEqual([(r.get("event"), r.get("reason")) for r in rows],
                         [("close", "clock-hour"), ("open", None), ("close", "game-gone")],
                         "the seal journal does not say what opened and closed, and why: %r" % rows)
        self.assertTrue(all(r.get("ts") and r.get("why") for r in rows), rows)
        self.assertIs(rows[2].get("gameRunning"), False, rows[2])

    def test_the_doctor_warns_when_an_hour_fragments(self):
        for i in range(ca._SHADOW_FRAGMENT_OPENS):
            self.alive = False
            r = ca.shadow_watch_tick()
            self.assertTrue(r.get("started"), r)
            self.now += 5 * 1000
            if i == ca._SHADOW_FRAGMENT_OPENS - 2:
                self.assertNotIn("fragment", (self.doctor().get("line") or ""),
                                 "PREMISE: %d opens already read as fragmented" % (i + 1))
        row = self.doctor()
        self.assertEqual(row.get("state"), "warn", "an hour that opened %d shadow reels read clean: %r"
                         % (ca._SHADOW_FRAGMENT_OPENS, row))
        self.assertIn("shadow_seals.jsonl", row.get("line") or "")


class TheDoorStampsWhenAReelBegan(unittest.TestCase):

    def test_start_agent_stamps_WHEN_beside_WHO_under_one_lock(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            src = fh.read()
        fn = next(n for n in ast.parse(src).body
                  if isinstance(n, ast.FunctionDef) and n.name == "start_agent")

        def assigns(node, name):
            return any(isinstance(t, ast.Name) and t.id == name
                       for a in ast.walk(node) if isinstance(a, ast.Assign) for t in a.targets)

        blocks = [w for w in ast.walk(fn) if isinstance(w, ast.With) and assigns(w, "_agent_origin")]
        self.assertEqual(len(blocks), 1, "the origin is no longer set in one locked block")
        self.assertTrue(assigns(blocks[0], "_agent_since_ms"),
                        "start_agent records WHO opened the reel but not WHEN, so the rollover can never "
                        "judge its age (or pairs a new door with an old clock)")


class TheNextLookComesSecondsAfterARollover(unittest.TestCase):

    def _drive(self, script):
        import lane_trace as LT

        class _Stop(BaseException):
            pass

        slept, ticks = [], list(script)

        class _Clock(object):
            def __getattr__(self, n):
                return getattr(time, n)

            def sleep(self, s):
                slept.append(s)
                if len(slept) > 3:
                    raise _Stop()

        saved = (ca.time, ca.shadow_watch_tick, ca._lane_tick, LT.note)
        ca.time = _Clock()
        ca.shadow_watch_tick = lambda: (ticks.pop(0) if ticks else {"ok": True})
        ca._lane_tick = lambda *a, **k: None
        LT.note = lambda *a, **k: True
        try:
            ca._shadow_watch_loop()
        except _Stop:
            pass
        finally:
            ca.time, ca.shadow_watch_tick, ca._lane_tick, LT.note = saved
        return slept

    def test_a_rollover_brings_the_next_look_forward(self):
        slept = self._drive([{"ok": True, "rotated": True, "why": "rolled over"},
                             {"ok": True, "started": True, "why": "started"}])
        self.assertEqual(slept[:3], [ca._SHADOW_WATCH_EVERY_S, ca._SHADOW_ROTATE_RELOOK_S,
                                     ca._SHADOW_WATCH_EVERY_S],
                         "after a rollover the next look waited %r - not 'instantly'" % slept)
        self.assertLess(ca._SHADOW_ROTATE_RELOOK_S, ca._SHADOW_WATCH_EVERY_S)

    def test_premise_without_a_rollover_it_keeps_its_period(self):
        slept = self._drive([{"ok": True, "why": "not on screen"}, {"ok": True}, {"ok": True}])
        self.assertEqual(slept[:3], [ca._SHADOW_WATCH_EVERY_S] * 3, "%r" % slept)


class TheLaneSpeaksTheSharedVocabulary(_Base):

    def test_on_worked_lastTs_owed(self):
        self.begin("shadow", self.now - 61 * MIN)
        ca.shadow_watch_tick()
        self.now += 2000
        ca.shadow_watch_tick()
        c = ca.shadow_watch_contract()
        self.assertEqual((c["on"], c["worked"], c["owed"]), (True, 2, 0),
                         "one start and one rollover are two pieces of LIFETIME work: %r" % c)
        self.assertEqual(c["lastTs"], self.now)

    def test_an_unreadable_record_is_UNKNOWN_not_idle(self):
        with io.open(self.path, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        c = ca.shadow_watch_contract()
        self.assertIsNone(c["worked"])
        self.assertIsNone(c["owed"])


RED_PROOF = [
    {"why": "REG-1675 - the hour counts 60 min from the reel's start again, not the clock: 14:40 runs to 15:40",
     "file": "control_app.py", "find": "    if now < _hour_end and age_s < limit:\n",
     "replace": "    if age_s < limit:\n", "matches": 1},
    {"why": "REG-1675 - the hour function returns start + 60 min instead of the next top of the clock",
     "file": "control_app.py", "find": "    return int((top + 3600) * 1000)\n",
     "replace": "    return int(float(since_ms) + 3600 * 1000)\n", "matches": 1},
    {"why": "REG-1675 - a window gone while the game RUNS (minimized, covered) seals the hour - the morning's 13 cuts",
     "file": "control_app.py",
     "find": "                if _run is not False or _cuts >= _SHADOW_AWAY_CUTS_PER_HOUR:\n",
     "replace": "                if _cuts >= _SHADOW_AWAY_CUTS_PER_HOUR:\n", "matches": 1},
    {"why": "REG-1675 - no breaker: an hour cut twice is cut again and again",
     "file": "control_app.py",
     "find": "                if _run is not False or _cuts >= _SHADOW_AWAY_CUTS_PER_HOUR:\n",
     "replace": "                if _run is not False:\n", "matches": 1},
    {"why": "REG-1675 - the away grace is 60 s again, not his three minutes",
     "file": "control_app.py", "find": "_SHADOW_AWAY_GRACE_S = 180   #",
     "replace": "_SHADOW_AWAY_GRACE_S = 60   #", "matches": 1},
    {"why": "REG-1675 - the game-gone seal writes no journal row: nobody can say afterwards why the reel closed",
     "file": "control_app.py", "find": "                    _shadow_seal_log(\"close\", reason=\"game-gone\",",
     "replace": "                    (lambda *a, **k: None)(\"close\", reason=\"game-gone\",", "matches": 1},
    {"why": "REG-1675 - the doctor reads a fragmented hour as clean",
     "file": "health_engine.py", "find": "    if _fr.get(\"state\") == WARN:\n",
     "replace": "    if False:\n", "matches": 1},
    {"why": "REG-1675 - opens are not counted per clock hour, so no hour can ever read as fragmented",
     "file": "control_app.py",
     "find": "    _opens = (int(cur.get(\"opensThisHour\") or 0) if cur.get(\"opensHour\") == _hk else 0) + (1 if ok else 0)\n",
     "replace": "    _opens = 1\n", "matches": 1},
    {
        "why": "2026-09-27 - switching shadow off excuses a reel already rolling, so the evening stacks up",
        "file": "control_app.py",
        "find": "    st = _shadow_state()\n    if _agent_alive():\n",
        "replace": "    st = _shadow_state()\n    if False:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - the doctor calls a stuck shadow reel fine because the switch is off",
        "file": "health_engine.py",
        "find": "        if _off.get(\"state\") in (WARN, UNKNOWN):\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - the rollover never fires: an evening stacks up in one unprocessed shadow reel",
        "file": "control_app.py",
        "find": "    if now < _hour_end and age_s < limit:\n",     # REG-1675 re-anchor
        "replace": "    if True:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - the rollover cuts reels he opened himself (ON AIR / MINI)",
        "file": "control_app.py",
        "find": "    if door != \"shadow\":\n        why = \"a reel is already rolling",
        "replace": "    if door is None:\n        why = \"a reel is already rolling",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - the rollover ends the session by a second route instead of the stop /api/off uses",
        "file": "control_app.py",
        "find": "        r = stop_agent(farewell=False)\n    except Exception as _e:\n        r = _force_kill_all_agents(\"shadow rollover",
        "replace": "        r = _force_kill_all_agents(\"shadow rollover\")\n    except Exception as _e:\n        r = _force_kill_all_agents(\"shadow rollover",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - the rollover reopens the next reel itself, past the door's window check, so a closed "
               "game gets a new reel",
        "file": "control_app.py",
        "find": "        n = int(_rec.get(\"rotations\") or 0) + 1\n",
        "replace": "        start_agent(sim=False, origin=\"shadow\")\n        n = int(_rec.get(\"rotations\") or 0) + 1\n",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - a stop that did not take is counted as a rollover, and the stuck reel vanishes "
               "from the doctor",
        "file": "control_app.py",
        "find": "    if still is False:\n",
        "replace": "    if True:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - the doctor is blind to a shadow reel stuck past its hour",
        "file": "control_app.py",
        "find": "    if age_s > limit + _SHADOW_ROTATE_MARGIN_S:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - a shadow reel whose start cannot be read reads as a clean row, not UNKNOWN",
        "file": "control_app.py",
        "find": "        return {\"state\": \"unknown\", \"owed\": None, \"ageS\": None,\n"
                "                \"line\": \"a shadow reel is rolling and when it began cannot be read",
        "replace": "        return {\"state\": \"ok\", \"owed\": 0, \"ageS\": None,\n"
                   "                \"line\": \"a shadow reel is rolling and when it began cannot be read",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - an orphan agent's stale door is believed, so a reel this console never opened is cut",
        "file": "control_app.py",
        "find": "    if not _owned:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - start_agent stops stamping WHEN a reel began, so no reel's age can be judged",
        "file": "control_app.py",
        "find": "        _agent_since_ms = int(time.time() * 1000)\n",
        "replace": "        pass\n",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - a look while a reel rolls is not stamped current, so the doctor cannot see it",
        "file": "control_app.py",
        "find": "    facts = dict(lookedAt=now, rollingAt=now,",
        "replace": "    facts = dict(lookedAt=now, rollingAt=None,",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - the next reel waits a whole watch period after a rollover instead of seconds",
        "file": "control_app.py",
        "find": "                time.sleep(_SHADOW_ROTATE_RELOOK_S)   # the sealed reel's successor, seconds later\n",
        "replace": "                time.sleep(_SHADOW_WATCH_EVERY_S)\n",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - the limit is fixed at import, so a law (or his override) cannot move it",
        "file": "control_app.py",
        "find": "    raw = (os.environ.get(\"TV_SHADOW_ROTATE_S\") or \"\").strip()\n",
        "replace": "    raw = \"\"\n",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - the health row never asks the rollover, so a stuck shadow reel reads green",
        "file": "health_engine.py",
        "find": "    if _rv.get(\"state\") in (WARN, UNKNOWN):\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
