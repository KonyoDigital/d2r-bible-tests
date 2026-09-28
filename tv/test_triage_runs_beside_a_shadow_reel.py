# -*- coding: utf-8 -*-
"""2026-09-28 — TRIAGE RUNS BESIDE A SHADOW REEL, AND A LANE THAT REFUSES SAYS SO.

MEASURED over SSH on his Windows ALT (plays D2R through Boosteroid, shadow reader ON, the hourly
rollover live — 10 rotations overnight): 7 of its 10 reels sat in TRIAGE — "the template is known and
retro_triage has not walked its frames, so whether it holds a panel is UNSURVEYED" — and 3 at PRINTER.
Nothing reached TOMBSTONE, so the FIFO drain correctly released nothing.

THE CAUSE, read in control_app.retro_triage_tick. It backed off on
  (a) _d2r_process_alive()  — False on Boosteroid, there is no local D2R.exe;
  (b) os.getloadavg()       — DOES NOT EXIST ON WINDOWS; the except swallowed it, so the ALT had no
                              load guard at all;
  (c) _capture_is_live()    — with shadow rolling continuously (a ~2 s gap between hourly reels) this
                              refused ~every 90 s tick, for ever.
And the loop printed only on success; _TRIAGE_LANE {surveyed, panels, lastTs, lastReel, skips} was
never published and `skips` was never filled — a lane refusing for ever read like one with nothing to do.

HIS WORDS: "this needs to be automated flow", "not stacking up", "regardless of room.. to flow through
the river". The docstring's POLITENESS rule stays: triage must not compete with HIS sessions.

WHAT THIS LAW DRIVES — the SHIPPED retro_triage_tick, the SHIPPED doctor row and the SHIPPED CPU helper,
with only the edges stubbed (_capture_is_live, the agent's door, _cpu_busy_pct, _d2r_process_alive,
the survey call, the sealed-session read, the paid-sweep state) on a TV_HIST fixture world:
  · a SHADOW capture + CPU 20%     -> it reaches the survey;
  · an ON AIR / MINI capture       -> refuses "never compete with the camera", before the CPU is asked;
  · a capture whose door is unread -> refuses (an unknown reel is his, never the console's);
  · SHADOW + CPU unmeasurable      -> refuses and names it; SHADOW + CPU 90% -> refuses;
  · no capture: the SAME helper guards a saturated machine and an unmeasurable one (no silent no-guard);
  · every refusal is RECORDED (lastWhy, lastSkipTs, skips[key] counted) and a raise too;
  · a reel still being folded, and a reel with no frame, never park the lane; a walk that walked
    nothing does not stamp lastTs;
  · the lane is PUBLISHED on /api/river, and its last walk survives a relaunch via the store;
  · the doctor row 'triage starved' reads MISSING / UNKNOWN / OK (and UNMEASURED when stood down),
    including off the exact state the console publishes — the join, not two halves;
  · _cpu_busy_pct: the Windows GetSystemTimes arithmetic (kernel INCLUDES idle), and the load-average
    path capped at 100 with None when unmeasurable.

⚠ NOTHING REAL IS TOUCHED. The survey is stubbed before any tick runs, the store path is asserted to sit
in the fixture before anything is read, and no console, bridge or agent is contacted. RED_PROOF below.
[[heart-first]] [[unknown-stays-unknown]] [[the-unjoined-end]] [[regression-guard]]
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
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

# the fixture world is declared BEFORE control_app is imported, so nothing resolved at import time can
# describe his tree
_WORLD = tempfile.mkdtemp(prefix="triage_shadow_")
os.environ["TV_HIST"] = _WORLD

import control_app as ca  # noqa: E402
import console_doctor as CD  # noqa: E402
import corroborate as CO  # noqa: E402
import frame_authority as FA  # noqa: E402
import retro_triage as RT  # noqa: E402
import tv_diablo as TVD  # noqa: E402

HOUR = 3600.0


class _Proc(object):
    """An agent child as start_agent leaves it: poll() is None while it runs."""
    pid = 4242

    def poll(self):
        return None


def _fresh_lane():
    return {"surveyed": 0, "panels": 0, "lastTs": None, "lastReel": None, "skips": {},
            "ticks": 0, "idle": 0, "lastKey": None, "lastWhy": None, "lastAt": None,
            "lastSkipKey": None, "lastSkipWhy": None, "lastSkipTs": None,
            "backlog": None, "backlogAt": None, "upSince": int(time.time() * 1000)}


class _Base(unittest.TestCase):

    STUBS = ("_capture_is_live", "_agent_origin", "_agent_proc", "_cpu_busy_pct",
             "vault_sweep_state", "_CHRON_JOB", "HIST_DIR", "_TRIAGE_ON", "_TRIAGE_LANE",
             "_TRIAGE_STORE_SEED")

    def setUp(self):
        self.world = tempfile.mkdtemp(prefix="triage_shadow_case_")
        self.addCleanup(shutil.rmtree, self.world, True)
        self._env = {k: os.environ.get(k) for k in ("TV_HIST", "TV_TRIAGE_SHADOW_MAX_CPU")}
        os.environ["TV_HIST"] = self.world
        os.environ.pop("TV_TRIAGE_SHADOW_MAX_CPU", None)
        self._saved = {k: getattr(ca, k) for k in self.STUBS}
        self._edges = (TVD._d2r_process_alive, RT.survey, FA.sealed_sessions)
        self.addCleanup(self._restore)
        self.assertTrue(os.path.realpath(RT._store_path()).startswith(os.path.realpath(self.world)),
                        "TV_HIST was not honoured by the survey store (%s) - REFUSING to run against "
                        "a real store" % RT._store_path())

        self.cpu = 20.0
        self.cpu_asks = 0
        self.surveyed = []
        self.walks = 1
        ca.HIST_DIR = self.world
        ca._TRIAGE_ON = True
        ca._TRIAGE_LANE = _fresh_lane()
        ca._TRIAGE_STORE_SEED = {"read": False, "ts": None, "why": ""}
        ca._capture_is_live = lambda: False
        ca._agent_proc, ca._agent_origin = None, "hand"
        ca._cpu_busy_pct = self._cpu
        ca.vault_sweep_state = lambda: {"running": False}
        ca._CHRON_JOB = {}
        TVD._d2r_process_alive = lambda *a, **k: False
        RT.survey = self._survey
        FA.sealed_sessions = lambda *a, **k: ({}, True)

    def _restore(self):
        for k, v in self._saved.items():
            setattr(ca, k, v)
        TVD._d2r_process_alive, RT.survey, FA.sealed_sessions = self._edges
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    # ── the edges ─────────────────────────────────────────────────────────────────────────────
    def _cpu(self, *a, **k):
        self.cpu_asks += 1
        return self.cpu

    def _survey(self, reels, gate, **k):
        self.surveyed.append([os.path.basename(r) for r in reels])
        return {"reels": self.walks, "frames": 3 if self.walks else 0, "panels": 0,
                "stoppedEarly": False, "say": "stub survey"}

    def reel(self, name="reel_s_1789000000000_1", frames=3, age_s=HOUR):
        """A folded reel on the fixture shelf, last modified `age_s` ago."""
        d = os.path.join(self.world, name)
        os.makedirs(d, exist_ok=True)
        for i in range(frames):
            with io.open(os.path.join(d, "f_%d.jpg" % (1789000000000 + i)), "wb") as fh:
                fh.write(b"\xff\xd8\xff")
        t = time.time() - age_s
        os.utime(d, (t, t))
        return d

    def rolling(self, origin):
        """A capture is live, opened by THIS console through `origin`'s door."""
        ca._capture_is_live = lambda: True
        ca._agent_proc = _Proc()
        ca._agent_origin = origin

    def tick(self):
        return ca.retro_triage_tick()


class TriageRunsBesideAShadowReel(_Base):

    def test_a_shadow_capture_and_a_quiet_cpu_reach_the_survey(self):
        self.reel()
        self.rolling("shadow")
        self.cpu = 20.0
        r = self.tick()
        self.assertEqual(self.surveyed, [["reel_s_1789000000000_1"]],
                         "a shadow reel rolling beside a 20%%-busy machine still blocked triage: %r" % r)
        self.assertTrue(r.get("ok"), r)
        self.assertEqual(r.get("key"), "surveyed")
        self.assertTrue(r.get("shadow"), "the tick did not know it ran beside a shadow reel: %r" % r)
        lane = ca._TRIAGE_LANE
        self.assertEqual(lane["surveyed"], 1)
        self.assertIsNotNone(lane["lastTs"], "a walk that happened was not stamped")
        self.assertEqual(lane["lastReel"], "reel_s_1789000000000_1")
        self.assertEqual(lane["backlog"], 0, "the backlog after the only reel was walked must be 0")
        self.assertEqual(lane["skips"], {}, "a successful walk was counted as a refusal")

    def test_an_on_air_capture_refuses_before_the_cpu_is_even_asked(self):
        self.reel()
        self.rolling("hand")
        r = self.tick()
        self.assertFalse(r.get("ok"), r)
        self.assertEqual(r.get("key"), "capture-onair", r)
        self.assertIn("never compete with the camera", r.get("why") or "")
        self.assertIn("ONAIR", r.get("why") or "", "the refusal does not say whose session it is")
        self.assertEqual(self.surveyed, [], "triage walked a reel beside HIS ON AIR session")
        self.assertEqual(self.cpu_asks, 0, "his session is refused on the door alone; sampling the "
                                           "CPU first spends his machine on a question already answered")

    def test_a_mini_capture_refuses_too(self):
        self.reel()
        self.rolling("mini")
        r = self.tick()
        self.assertEqual(r.get("key"), "capture-mini", r)
        self.assertIn("never compete with the camera", r.get("why") or "")
        self.assertEqual(self.surveyed, [])

    def test_a_capture_whose_door_cannot_be_read_is_his_never_the_consoles(self):
        """An orphan agent (not opened by THIS console) carries a stale origin that means nothing."""
        self.reel()
        ca._capture_is_live = lambda: True
        ca._agent_proc, ca._agent_origin = None, "shadow"
        r = self.tick()
        self.assertEqual(r.get("key"), "capture-unowned", r)
        self.assertIn("never compete with the camera", r.get("why") or "")
        self.assertEqual(self.surveyed, [], "an orphan's stale shadow origin was believed")

    def test_shadow_with_an_unmeasurable_cpu_refuses_and_names_it(self):
        self.reel()
        self.rolling("shadow")
        self.cpu = None
        r = self.tick()
        self.assertFalse(r.get("ok"), r)
        self.assertEqual(r.get("key"), "cpu-unmeasured", r)
        self.assertIn("could not be measured", r.get("why") or "")
        self.assertIn("SHADOW", r.get("why") or "")
        self.assertEqual(self.surveyed, [], "an UNKNOWN CPU was read as an idle one")

    def test_shadow_with_a_busy_cpu_refuses(self):
        self.reel()
        self.rolling("shadow")
        self.cpu = 90.0
        r = self.tick()
        self.assertEqual(r.get("key"), "cpu-shadow", r)
        self.assertIn("90%", r.get("why") or "")
        self.assertIn("%.0f%%" % ca._TRIAGE_SHADOW_MAX_CPU, r.get("why") or "")
        self.assertEqual(self.surveyed, [])

    def test_the_shadow_bar_is_the_named_constant_and_a_law_can_move_it(self):
        self.reel()
        self.rolling("shadow")
        bar = ca._TRIAGE_SHADOW_MAX_CPU
        self.cpu = bar + 1
        self.assertEqual(self.tick().get("key"), "cpu-shadow", "one point above the bar was let through")
        self.cpu = bar
        self.assertEqual(self.tick().get("key"), "surveyed", "the bar itself must be allowed")
        self.reel("reel_s_1789000000001_2")
        os.environ["TV_TRIAGE_SHADOW_MAX_CPU"] = "95"
        self.cpu = 90.0
        self.assertEqual(self.tick().get("key"), "surveyed",
                         "TV_TRIAGE_SHADOW_MAX_CPU was not read at call time")

    def test_without_a_capture_the_same_helper_guards_the_machine(self):
        """The ALT's defect was NO guard at all. Every OS now asks _cpu_busy_pct."""
        self.reel()
        self.cpu = ca._TRIAGE_MAX_CPU
        self.assertEqual(self.tick().get("key"), "cpu-loaded")
        self.cpu = None
        r = self.tick()
        self.assertEqual(r.get("key"), "cpu-unmeasured", "an unmeasurable machine ran triage blind")
        self.assertNotIn("SHADOW", r.get("why") or "", "no shadow reel was rolling; the why says one was")
        self.assertEqual(self.surveyed, [])
        self.cpu = 50.0
        self.assertEqual(self.tick().get("key"), "surveyed")

    def test_he_is_playing_still_refuses_first(self):
        self.reel()
        TVD._d2r_process_alive = lambda *a, **k: True
        r = self.tick()
        self.assertEqual(r.get("key"), "playing", r)
        self.assertEqual(self.cpu_asks, 0)


class EveryOutcomeIsRecorded(_Base):

    def test_each_refusal_is_recorded_and_counted_by_reason(self):
        self.reel()
        self.rolling("hand")
        self.tick()
        self.tick()
        self.rolling("shadow")
        self.cpu = 90.0
        r = self.tick()
        lane = ca._TRIAGE_LANE
        self.assertEqual(lane["skips"], {"capture-onair": 2, "cpu-shadow": 1},
                         "refusals were not counted by reason: %r" % lane["skips"])
        self.assertEqual(lane["ticks"], 3)
        self.assertEqual(lane["lastKey"], "cpu-shadow")
        self.assertEqual(lane["lastWhy"], r["why"])
        self.assertEqual(lane["lastSkipWhy"], r["why"])
        self.assertEqual(lane["lastSkipKey"], "cpu-shadow")
        self.assertIsInstance(lane["lastSkipTs"], int)
        self.assertIsNone(lane["lastTs"], "no reel was walked, yet the lane says one was")

    def test_a_raise_is_recorded_before_it_propagates(self):
        self.reel()

        def _boom(*a, **k):
            raise RuntimeError("survey exploded")
        RT.survey = _boom
        with self.assertRaises(RuntimeError):
            self.tick()
        lane = ca._TRIAGE_LANE
        self.assertEqual(lane["skips"].get("raised"), 1, lane)
        self.assertIn("survey exploded", lane["lastSkipWhy"] or "")

    def test_nothing_owed_is_recorded_as_idle_not_as_a_refusal(self):
        r = self.tick()
        self.assertTrue(r.get("done"), r)
        lane = ca._TRIAGE_LANE
        self.assertEqual(lane["idle"], 1)
        self.assertEqual(lane["skips"], {})
        self.assertEqual(lane["backlog"], 0)
        self.assertEqual(lane["lastKey"], "done")

    def test_a_reel_still_being_folded_is_not_walked(self):
        self.reel(age_s=5)
        r = self.tick()
        self.assertEqual(self.surveyed, [], "a reel folded 5 s ago was walked - its frames may still "
                                            "be arriving, and it would be remembered as walked IN FULL")
        self.assertEqual(r.get("key"), "unworkable", r)
        self.assertEqual(r.get("settling"), 1)
        self.assertEqual(ca._TRIAGE_LANE["backlog"], 1, "a settling reel is still OWED")

    def test_a_frameless_reel_does_not_park_the_lane(self):
        self.reel("reel_s_1789000000000_0", frames=0)
        self.reel("reel_s_1789000000001_1", frames=4)
        r = self.tick()
        self.assertEqual(self.surveyed, [["reel_s_1789000000001_1"]],
                         "smallest-first picked the reel with NO frame, which survey() skips without "
                         "remembering - the lane would pick it again every tick for ever")
        self.assertEqual(r.get("frameless"), 1)
        self.assertEqual(r.get("backlog"), 1, "the frameless reel is still owed and must be counted")

    def test_a_walk_that_walked_nothing_does_not_stamp_lastTs(self):
        self.reel()
        self.walks = 0
        r = self.tick()
        self.assertFalse(r.get("ok"), r)
        self.assertEqual(r.get("key"), "walked-nothing")
        self.assertIsNone(ca._TRIAGE_LANE["lastTs"],
                          "a tick that walked no reel stamped lastTs, so a parked lane reads as busy")


class TheLaneIsPublished(_Base):

    def _river_payload_dicts(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        out = []
        for n in ast.walk(tree):
            if isinstance(n, ast.Dict):
                keys = {k.value for k in n.keys if isinstance(k, ast.Constant)}
                if {"mouth", "population", "detail"} <= keys:
                    out.append(("ok", n))
                elif {"stations", "counts", "reels", "why"} <= keys and len(keys) <= 6:
                    out.append(("failed", n))
        return out

    def test_the_river_payload_carries_the_lane_on_both_answers(self):
        found = self._river_payload_dicts()
        kinds = sorted(k for k, _ in found)
        self.assertEqual(kinds, ["failed", "ok"],
                         "premise: the /api/river payload dicts were not found as expected (%r)" % kinds)
        for kind, d in found:
            vals = {k.value: v for k, v in zip(d.keys, d.values) if isinstance(k, ast.Constant)}
            v = vals.get("triage")
            self.assertTrue(isinstance(v, ast.Call) and isinstance(v.func, ast.Name)
                            and v.func.id == "triage_lane_state",
                            "the %s /api/river payload does not publish triage_lane_state() - the "
                            "doctor runs in another process and cannot see the lane" % kind)

    def test_the_published_state_says_never_and_up_not_zero(self):
        s = ca.triage_lane_state()
        self.assertTrue(s["ok"], s)
        self.assertIsNone(s["lastSurveyTs"])
        self.assertIsNone(s["sinceSurveyS"], "a lane that never walked a reel read as recent")
        self.assertIsInstance(s["upS"], float)
        self.assertIsNone(s["owed"], "no tick has counted the backlog; owed must be UNKNOWN, not 0")
        self.assertEqual(s["shadowMaxCpu"], ca._TRIAGE_SHADOW_MAX_CPU)

    def test_the_last_walk_survives_a_relaunch_via_the_store(self):
        ts = int((time.time() - 5 * HOUR) * 1000)
        with io.open(RT._store_path(), "w", encoding="utf-8") as fh:
            json.dump({"reel_s_1": {"panels": 0, "frames": 3, "ts": ts, "full": True},
                       "reel_s_2": {"panels": 1, "frames": 3, "ts": ts + 999, "full": False}}, fh)
        s = ca.triage_lane_state()
        self.assertEqual(s["lastSurveyTs"], ts, "the newest FULL store row was not the seed: %r" % s)
        self.assertEqual(s["lastSurveySource"], "the survey store")
        self.assertGreater(s["sinceSurveyS"], 4.9 * HOUR)
        self.reel()
        self.tick()
        s2 = ca.triage_lane_state()
        self.assertEqual(s2["lastSurveySource"], "this process",
                         "a walk in this process did not supersede the older store row")
        self.assertLess(s2["sinceSurveyS"], 60)


def _river(triage=7, ok=True):
    return {"ok": True, "lanes": {"ok": ok, "lanes": [
        {"name": "INTAKE", "byStation": {"INTAKE": 0, "TRIAGE": triage, "STATION": 0, "EMPTY": 0}},
        {"name": "PRINTER", "byStation": {"PRINTER": 3, "JOIN": 0}}]}}


class TheDoctorRow(unittest.TestCase):

    def verdict(self, payload):
        real = CD._get
        CD._get = lambda path, *a, **k: (payload if path == "/api/river" else None)
        try:
            st, why = CD._check_triage_is_not_starved()
        finally:
            CD._get = real
        return st, (why[0] if isinstance(why, tuple) else why)

    def lane(self, **kw):
        s = {"ok": True, "stoodDown": False, "skips": {"cpu-shadow": 140, "capture-onair": 3},
             "lastSkipKey": "cpu-shadow", "lastSkipWhy": "a SHADOW reel is rolling and the CPU is 88% busy",
             "lastWhy": "a SHADOW reel is rolling and the CPU is 88% busy",
             "backlog": 7, "lastSurveyTs": 1, "lastReel": "reel_x", "lastSurveySource": "the survey store",
             "sinceSurveyS": 4 * HOUR, "upS": 9 * HOUR}
        s.update(kw)
        return s

    def test_missing_when_triage_holds_reels_and_nothing_was_walked_for_three_hours(self):
        p = _river(7)
        p["triage"] = self.lane()
        st, why = self.verdict(p)
        self.assertEqual(st, CD.MISSING, why)
        self.assertIn("7 reel(s) wait in TRIAGE", why)
        self.assertIn("88% busy", why, "the row does not name the lane's last refusal")
        self.assertIn("cpu-shadow", why)
        self.assertIn("Backlog: 7", why)

    def test_missing_when_the_lane_never_walked_in_a_long_lived_process(self):
        p = _river(2)
        p["triage"] = self.lane(lastSurveyTs=None, sinceSurveyS=None, upS=5 * HOUR,
                                lastSkipWhy=None, lastWhy=None, skips={})
        st, why = self.verdict(p)
        self.assertEqual(st, CD.MISSING, why)
        self.assertIn("NEVER walked", why)
        self.assertIn("NONE RECORDED", why, "a lane with no tick at all must say the loop may be dead")

    def test_ok_inside_the_bar_and_ok_when_nothing_waits(self):
        p = _river(7)
        p["triage"] = self.lane(sinceSurveyS=HOUR)
        self.assertEqual(self.verdict(p)[0], CD.OK)
        p = _river(0)
        p["triage"] = self.lane()
        st, why = self.verdict(p)
        self.assertEqual(st, CD.OK, why)
        self.assertIn("no reel waits in TRIAGE", why)

    def test_unknown_when_the_lane_state_cannot_be_read(self):
        self.assertEqual(self.verdict(None)[0], CD.UNKNOWN, "no answer must be UNKNOWN")
        self.assertEqual(self.verdict(_river(7))[0], CD.UNKNOWN,
                         "a console that publishes no triage field must be UNKNOWN, not clean")
        p = _river(7)
        p["triage"] = {"ok": False, "why": "boom"}
        self.assertEqual(self.verdict(p)[0], CD.UNKNOWN)

    def test_unknown_when_the_river_cannot_count_triage(self):
        p = _river(7, ok=False)
        p["triage"] = self.lane()
        self.assertEqual(self.verdict(p)[0], CD.UNKNOWN)
        p = {"ok": True, "lanes": {"ok": True, "lanes": [{"name": "PRINTER", "byStation": {"PRINTER": 1}}]}}
        p["triage"] = self.lane()
        st, why = self.verdict(p)
        self.assertEqual(st, CD.UNKNOWN, "no lane carried a TRIAGE count and it was read as zero: %s" % why)

    def test_a_stood_down_lane_is_unmeasured_not_starved(self):
        p = _river(7)
        p["triage"] = self.lane(stoodDown=True)
        self.assertEqual(self.verdict(p)[0], CD.UNMEASURED)

    def test_the_row_never_imports_the_twin(self):
        import inspect
        src = inspect.getsource(CD._check_triage_is_not_starved)
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        body = code.split('"""')[-1]
        self.assertNotIn("import control_app", body,
                         "the row imported control_app, whose _TRIAGE_LANE is the empty literal")
        self.assertIn('_get("/api/river"', body)

    def test_it_is_registered_explained_declared_and_periodic(self):
        self.assertIn("triage starved", [n for n, _ in CD.CHECKS])
        self.assertIn("triage starved", CD.PERIODIC)
        self.assertIn("triage starved", CD.WATCHES)
        self.assertIn("triage starved", CO.NO_JOINT_YET)


class TheJoin(_Base):
    """The state the console PUBLISHES is the shape the doctor READS — driven end to end."""

    def _doctor_over(self, n_triage):
        p = _river(n_triage)
        p["triage"] = ca.triage_lane_state()
        real = CD._get
        CD._get = lambda path, *a, **k: (p if path == "/api/river" else None)
        try:
            st, why = CD._check_triage_is_not_starved()
        finally:
            CD._get = real
        return st, (why[0] if isinstance(why, tuple) else why)

    def test_a_lane_refusing_beside_his_session_for_four_hours_reads_missing(self):
        self.reel()
        self.rolling("hand")
        self.tick()
        ca._TRIAGE_LANE["upSince"] -= int(4 * HOUR * 1000)
        st, why = self._doctor_over(1)
        self.assertEqual(st, CD.MISSING, why)
        self.assertIn("never compete with the camera", why)
        self.assertIn("capture-onair", why)

    def test_the_same_lane_after_a_walk_reads_ok(self):
        self.reel()
        self.rolling("shadow")
        self.tick()
        ca._TRIAGE_LANE["upSince"] -= int(4 * HOUR * 1000)
        st, why = self._doctor_over(1)
        self.assertEqual(st, CD.OK, why)


class TheCpuHelper(unittest.TestCase):

    def setUp(self):
        self._saved = (ca.IS_WIN, ca._system_times)
        self.addCleanup(self._restore)

    def _restore(self):
        ca.IS_WIN, ca._system_times = self._saved

    def test_windows_busy_is_kernel_plus_user_minus_idle_over_kernel_plus_user(self):
        # kernel INCLUDES idle: 100 kernel (80 of it idle) + 100 user -> 120 busy of 200 = 60%
        self.assertEqual(ca._cpu_busy_from_times((0, 0, 0), (80, 100, 100)), 60.0)
        self.assertEqual(ca._cpu_busy_from_times((10, 10, 10), (10, 10, 10)), None,
                         "a clock that did not move is UNMEASURED, not 0% busy")
        self.assertIsNone(ca._cpu_busy_from_times(None, (1, 2, 3)))

    def test_the_windows_path_samples_system_times_twice(self):
        seq = iter([(1000, 2000, 3000), (1080, 2100, 3100)])
        ca.IS_WIN = True
        ca._system_times = lambda: next(seq)
        # as on Windows: there IS no load average, so a path that still asks for one reads None
        with mock.patch.object(ca.os, "getloadavg", create=True, side_effect=AttributeError("windows")):
            self.assertEqual(ca._cpu_busy_pct(sample_s=0), 60.0,
                             "the Windows path did not answer from GetSystemTimes")
            ca._system_times = lambda: None
            self.assertIsNone(ca._cpu_busy_pct(sample_s=0), "an unreadable GetSystemTimes must be None")

    def test_elsewhere_it_is_the_load_average_over_the_cores_capped_and_unknown_when_absent(self):
        ca.IS_WIN = False
        with mock.patch.object(ca.os, "getloadavg", create=True, return_value=(5.0, 1, 1)), \
                mock.patch.object(ca.os, "cpu_count", return_value=10):
            self.assertEqual(ca._cpu_busy_pct(), 50.0)
        with mock.patch.object(ca.os, "getloadavg", create=True, return_value=(30.0, 1, 1)), \
                mock.patch.object(ca.os, "cpu_count", return_value=10):
            self.assertEqual(ca._cpu_busy_pct(), 100.0)
        with mock.patch.object(ca.os, "getloadavg", create=True, side_effect=AttributeError("windows")):
            self.assertIsNone(ca._cpu_busy_pct(), "no load average must be UNKNOWN, never 0")
        with mock.patch.object(ca.os, "getloadavg", create=True, return_value=(5.0, 1, 1)), \
                mock.patch.object(ca.os, "cpu_count", return_value=None):
            self.assertIsNone(ca._cpu_busy_pct(), "an unknown core count must not be guessed as 4")


RED_PROOF = [
    {
        "why": "2026-09-28 - the old behaviour: any live capture refuses, so a continuously rolling shadow "
               "reel starves triage and reels stack up in TRIAGE",
        "file": "control_app.py",
        "find": "        if door == \"shadow\":\n            shadow = True\n",
        "replace": "        if False:\n            shadow = True\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - triage competes with HIS ON AIR / MINI session",
        "file": "control_app.py",
        "find": "        if door == \"shadow\":\n            shadow = True\n",
        "replace": "        if door in (\"shadow\", \"onair\", \"mini\"):\n            shadow = True\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - an orphan agent's stale shadow origin is believed, so an unknown reel is "
               "treated as the console's",
        "file": "control_app.py",
        "find": "        door = (_rolling_reel() or {}).get(\"door\")\n",
        "replace": "        door = _door_of_origin(_agent_origin)\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - an UNMEASURABLE CPU is read as an idle machine and triage runs blind",
        "file": "control_app.py",
        "find": "    cpu = _cpu_busy_pct()\n",
        "replace": "    cpu = _cpu_busy_pct()\n    cpu = 0.0 if cpu is None else cpu\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - beside a shadow reel triage runs whatever the CPU is doing",
        "file": "control_app.py",
        "find": "    if shadow and cpu > _triage_shadow_max_cpu():\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - the shadow bar is read once at import, so his override silently does not take",
        "file": "control_app.py",
        "find": "    raw = (os.environ.get(\"TV_TRIAGE_SHADOW_MAX_CPU\") or \"\").strip()\n",
        "replace": "    raw = \"\"\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - no outcome is recorded: a lane refusing for ever reads like one with nothing to do",
        "file": "control_app.py",
        "find": "    _triage_record(r)\n    return r\n",
        "replace": "    return r\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - refusals are recorded but not COUNTED by reason",
        "file": "control_app.py",
        "find": "        sk[key] = int(sk.get(key) or 0) + 1\n",
        "replace": "        sk[key] = 1\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - a tick that raises leaves no trace in the lane",
        "file": "control_app.py",
        "find": "        _triage_record({\"ok\": False, \"key\": \"raised\",\n",
        "replace": "        (lambda _x: None)({\"ok\": False, \"key\": \"raised\",\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - the lane is never published, so the doctor (another process) cannot see it",
        "file": "control_app.py",
        "find": "                    \"triage\": triage_lane_state(),\n                    \"walked\": _walked,",
        "replace": "                    \"walked\": _walked,",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - a relaunch resets the lane's last walk to never (every ship re-execs the console)",
        "file": "control_app.py",
        "find": "        if stored is not None and (last is None or stored > last):\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - a tick that walked nothing stamps lastTs, so a parked lane reads as busy",
        "file": "control_app.py",
        "find": "    if walked:\n        _TRIAGE_LANE[\"lastTs\"] = int(time.time() * 1000)\n",
        "replace": "    if True:\n        _TRIAGE_LANE[\"lastTs\"] = int(time.time() * 1000)\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - a reel still being folded is walked and remembered as walked IN FULL",
        "file": "control_app.py",
        "find": "            return (_now_s - os.path.getmtime(p)) < _TRIAGE_SETTLE_S\n",
        "replace": "            return False\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - a reel with no frame sorts first and parks the lane for ever",
        "file": "control_app.py",
        "find": "    frameless = [d for d in owed if d not in settling and _n_frames(d) == 0]\n",
        "replace": "    frameless = []\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - the Windows path is skipped and getloadavg (absent on Windows) is asked instead",
        "file": "control_app.py",
        "find": "    if IS_WIN:\n        a = _system_times()\n",
        "replace": "    if False:\n        a = _system_times()\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - GetSystemTimes idle counted twice: a pegged machine reads ~half busy",
        "file": "control_app.py",
        "find": "        total = (int(after[1]) - int(before[1])) + (int(after[2]) - int(before[2]))\n",
        "replace": "        total = (int(after[1]) - int(before[1])) + (int(after[2]) - int(before[2])) + di\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - an unknown core count is guessed, so an unmeasurable load reads as a number",
        "file": "control_app.py",
        "find": "    cpus = os.cpu_count()\n    if not cpus:\n        return None\n",
        "replace": "    cpus = os.cpu_count() or 4\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - the doctor is blind to a lane starved past the bar",
        "file": "console_doctor.py",
        "find": "    if age_s > TRIAGE_STARVED_AFTER_S:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - a console that publishes no lane state reads as a healthy lane",
        "file": "console_doctor.py",
        "find": "    tri = riv.get(\"triage\")\n    if not isinstance(tri, dict):\n        return UNKNOWN,",
        "replace": "    tri = riv.get(\"triage\")\n    if not isinstance(tri, dict):\n        return OK,",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - a river that cannot count TRIAGE is read as holding none",
        "file": "console_doctor.py",
        "find": "    return n if seen else None\n",
        "replace": "    return n if seen else 0\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
