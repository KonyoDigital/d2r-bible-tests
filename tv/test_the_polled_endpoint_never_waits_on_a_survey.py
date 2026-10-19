"""/api/status IS POLLED ONCE A SECOND, SO NOTHING IN IT MAY WAIT ON A DISK SURVEY.

⚠⚠ THE MEASUREMENT THIS LAW EXISTS FOR (#28, REG-895). The console keeps the slowest request it
has ever served, entire, in tv/.status_worst.json. That record:

    totalMs        612,893.2 ms      (10 minutes 13 seconds)
    vaultAutoread  603,443.2 ms      98.5% of it
    capture=False · mode=off · agent=False · lockWaitDelta 0 · ver v2846

NO recording session, NO agent, NO lock contention. The task this closes was called "/api/status
degrades under a recording session" for weeks; the kept record says it was never that. `/api/status`
is polled about once a second, the vault-autoread lamp had a 3-second TTL, and every miss ran
`reel_retention.plan()` over his footage SYNCHRONOUSLY inside the handler, with no deadline.

⚠ THE 603-SECOND TRIGGER IS UNKNOWN AND THIS LAW DOES NOT PRETEND OTHERWISE. plan() measures 0.067s
warm on the same tree (three consecutive runs), so that was not the ordinary path. What is provable
is the SHAPE — an unbounded synchronous call in a polled endpoint — and the shape is what is pinned
here, because bounding it fixes the request whatever made the survey slow that day.
[[unknown-stays-unknown]] [[poll-slower-than-its-interval]] [[stale-reading]]

⚠ NO FOOTAGE. The survey is replaced by a stand-in that sleeps, so this measures the same thing on
his Mac and on a CI runner with no reels. [[feedback-blind-fixture-green-gate]]
"""
import os
import sys
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app as CA   # noqa: E402

#: How long the stand-in survey blocks. Comfortably longer than the TTL and the poll interval, so a
#: blocking implementation cannot pass by being lucky.
SLOW_S = 3.0

#: The handler must stay far below the poll interval. 250 ms is ~1/4 of one poll and still four
#: orders of magnitude under the 603 s it is written for — a bound that is neither generous enough
#: to admit the defect nor tight enough to flake on a loaded runner.
BUDGET_MS = 250.0


class ThePolledEndpointNeverWaitsOnASurvey(unittest.TestCase):

    def setUp(self):
        self._real = CA._vault_autoread_state
        self.calls = []
        CA._VAULT_AUTOREAD_CACHE["t"], CA._VAULT_AUTOREAD_CACHE["d"] = 0.0, None

    def tearDown(self):
        CA._vault_autoread_state = self._real
        CA._VAULT_AUTOREAD_CACHE["t"], CA._VAULT_AUTOREAD_CACHE["d"] = 0.0, None
        # ⚠ let any in-flight stand-in finish, or its late write lands in the NEXT test's cache —
        # the leak REG-865 logged when a fixture had no tearDown.
        for _ in range(80):
            if not CA._VAULT_AUTOREAD_REFRESH.get("running"):
                break
            time.sleep(0.1)

    def _slow(self, ms_holder=None):
        def _fn():
            self.calls.append(time.time())
            time.sleep(SLOW_S)
            return {"on": True, "why": "measured by the slow stand-in"}
        return _fn

    def test_the_handler_returns_while_the_survey_is_still_running(self):
        CA._vault_autoread_state = self._slow()
        worst, n = 0.0, 6
        for _ in range(n):
            t = time.time()
            CA._vault_autoread_state_cached()
            worst = max(worst, (time.time() - t) * 1000.0)
            time.sleep(0.25)
        self.assertTrue(self.calls, "the survey never ran at all, so this law measured NOTHING — "
                                    "a green here would say nothing about blocking")
        self.assertLess(worst, BUDGET_MS,
                        "the polled endpoint waited %.0f ms on a %.0f ms survey. This is the "
                        "612,893 ms request from tv/.status_worst.json, in miniature: the handler "
                        "is polled once a second and must never carry a survey's cost"
                        % (worst, SLOW_S * 1000))

    def test_one_survey_at_a_time_not_one_per_poll(self):
        """⚠ A slow survey plus a once-a-second poll spawns a thread per poll unless something
        says no — 600 of them for the record above. [[poll-slower-than-its-interval]]"""
        CA._vault_autoread_state = self._slow()
        for _ in range(6):
            CA._vault_autoread_state_cached()
            time.sleep(0.25)
        self.assertEqual(len(self.calls), 1,
                         "%d surveys were started in 1.5s of polling — the refresh is not held to "
                         "one at a time, so a slow survey multiplies instead of being absorbed"
                         % len(self.calls))
        alive = [t for t in threading.enumerate() if t.name == "tvd-vault-lamp"]
        self.assertLessEqual(len(alive), 1,
                             "%d refresh threads alive at once" % len(alive))
        stolen = [t for t in threading.enumerate() if t.name == "tvd-vault-autoread"]
        self.assertEqual(stolen, [],
                         "the lamp refresh wore the vault loop's name, so the roster "
                         "will skip the loop for the life of this process")

    def test_before_the_first_survey_the_lamp_is_UNKNOWN_not_off(self):
        """`{}` or on:False would say the lane is idle when nobody has looked yet."""
        CA._vault_autoread_state = self._slow()
        r = CA._vault_autoread_state_cached()
        self.assertIsInstance(r, dict, "the lamp stopped being a dict")
        self.assertIsNone(r.get("on"),
                          "before the first survey finishes the lamp reads %r — an unmeasured lane "
                          "rendered as a measured one" % (r.get("on"),))
        self.assertTrue(str(r.get("why") or ""),
                        "UNKNOWN with no reason attached is not an answer")

    def test_a_served_answer_carries_its_own_age(self):
        """A cached lamp with no age cannot be told from one measured this instant."""
        CA._vault_autoread_state = lambda: {"on": True, "why": "instant stand-in"}
        CA._vault_autoread_state_cached()
        for _ in range(40):
            if CA._VAULT_AUTOREAD_CACHE["d"] is not None:
                break
            time.sleep(0.05)
        self.assertIsNotNone(CA._VAULT_AUTOREAD_CACHE["d"], "the refresh never landed")
        r = CA._vault_autoread_state_cached()
        self.assertIn("ageMs", r, "the served lamp carries no age, so a stale reading and a fresh "
                                  "one are indistinguishable")
        self.assertIsInstance(r.get("ageMs"), int, "ageMs is %r, not a number" % (r.get("ageMs"),))

    def test_the_lamp_refresh_does_not_wear_the_loops_name(self):
        """The server accepts status before the roster starts. A refresh thread
        named tvd-vault-autoread makes that roster skip the real loop."""
        import inspect
        kick = inspect.getsource(CA._vault_autoread_kick)
        self.assertIn('name="tvd-vault-lamp"', kick)
        self.assertNotIn('name="tvd-vault-autoread"', kick)
        roster = inspect.getsource(CA.start_background_watchers)
        self.assertIn('("tvd-vault-autoread", _vault_autoread_loop)', roster)


class TheLockCensusNeverBlocksStatus(unittest.TestCase):
    """The rinse console measured this on v3771: one /api/status spent 6,419 ms in
    selfArming while the rest of that request was milliseconds. The spec aborts at
    3 s, and the boot poll aborts at 900 ms, so the same stall is reported as
    "rinse control server never came up"."""

    def setUp(self):
        self._real = CA._self_arming_state
        self.calls = []
        CA._SELF_ARM_CACHE["t"], CA._SELF_ARM_CACHE["d"] = 0.0, None
        CA._SELF_ARM_REFRESH["running"] = False

    def tearDown(self):
        CA._self_arming_state = self._real
        CA._SELF_ARM_CACHE["t"], CA._SELF_ARM_CACHE["d"] = 0.0, None
        for _ in range(80):
            if not CA._SELF_ARM_REFRESH.get("running"):
                break
            time.sleep(0.1)

    def _slow(self):
        def _fn():
            self.calls.append(time.time())
            time.sleep(SLOW_S)
            return {"ok": True, "open": 1, "total": 1, "locks": [{"lock": "x", "state": "OPEN"}],
                    "why": "measured by the slow stand-in"}
        return _fn

    def test_the_handler_returns_while_the_lock_census_is_still_running(self):
        CA._self_arming_state = self._slow()
        worst, n = 0.0, 6
        for _ in range(n):
            t = time.time()
            CA._self_arming_state_cached()
            worst = max(worst, (time.time() - t) * 1000.0)
            time.sleep(0.25)
        self.assertTrue(self.calls, "the lock census never ran, so this law measured NOTHING")
        self.assertLess(worst, BUDGET_MS,
                        "the polled endpoint waited %.0f ms on a %.0f ms lock census"
                        % (worst, SLOW_S * 1000))

    def test_one_census_at_a_time_not_one_per_poll(self):
        CA._self_arming_state = self._slow()
        for _ in range(6):
            CA._self_arming_state_cached()
            time.sleep(0.25)
        self.assertEqual(len(self.calls), 1,
                         "%d censuses started in 1.5s of polling" % len(self.calls))
        alive = [t for t in threading.enumerate() if t.name == "tvd-self-arm-lamp"]
        self.assertLessEqual(len(alive), 1, "%d census threads alive at once" % len(alive))

    def test_before_the_first_census_the_badge_is_LOCKED_not_open(self):
        CA._self_arming_state = self._slow()
        r = CA._self_arming_state_cached()
        self.assertFalse(r.get("ok"), r)
        self.assertEqual(r.get("open"), 0, r)
        self.assertEqual(r.get("locks"), [], r)
        self.assertIn("not open", str(r.get("why") or ""))

    def test_status_asks_the_cached_census(self):
        import inspect
        src = inspect.getsource(CA.status_payload)
        self.assertIn('_t("selfArming", _self_arming_state_cached)', src)
        self.assertNotIn('_t("selfArming", _self_arming_state),', src)


class TheStatusPollDoesNotWaitOnGitFetch(unittest.TestCase):
    """main() calls status_payload() before it binds. That call's fleet row used to
    run `git fetch origin main` with a 25s timeout, and the rinse boot poll gives
    up at 20s. Routine I 39209490488: the child was still alive, nothing was
    listening, and the boot log had not one line from the console."""

    def setUp(self):
        self._real = CA._git_run
        self._cache = dict(CA._FLEET_CACHE)
        self._last = CA._FLEET_LAST_FETCH
        self.fetches = []
        CA._FLEET_CACHE["val"] = None
        CA._FLEET_CACHE["t"] = 0.0
        CA._FLEET_LAST_FETCH = 0.0
        CA._FLEET_FETCHING["on"] = False

    def tearDown(self):
        CA._git_run = self._real
        for _ in range(80):
            if not CA._FLEET_FETCHING.get("on"):
                break
            time.sleep(0.1)
        CA._FLEET_CACHE.clear()
        CA._FLEET_CACHE.update(self._cache)
        CA._FLEET_LAST_FETCH = self._last
        CA._FLEET_FETCHING["on"] = False

    def _slow_git(self):
        def _fn(argv, **kw):
            class R:
                returncode = 0
                stdout = "0\n"
                stderr = ""
            if isinstance(argv, (list, tuple)) and "fetch" in argv:
                self.fetches.append(time.time())
                time.sleep(SLOW_S)
                return R()
            # The other git questions are not what this law measures. A sandbox with no
            # origin makes them sit on their timeouts, and that would paint a fast fetch
            # as a slow status.
            return R()
        return _fn

    def test_a_slow_fetch_does_not_hold_the_status_answer(self):
        CA._git_run = self._slow_git()
        t = time.time()
        fl = CA.fleet_origin_status(force_fetch=False)
        waited = (time.time() - t) * 1000.0
        for _ in range(40):
            if self.fetches:
                break
            time.sleep(0.01)
        self.assertTrue(self.fetches, "no fetch was started, so this law measured nothing")
        self.assertLess(waited, BUDGET_MS,
                        "fleet_origin_status waited %.0f ms on a %.0f ms git fetch. "
                        "The headless boot calls this before it binds, and the rinse "
                        "poll gives that boot 20s against a 25s fetch timeout"
                        % (waited, SLOW_S * 1000))
        self.assertIn("behind", fl)
        alive = [th for th in threading.enumerate() if th.name == "tvd-fleet-fetch"]
        self.assertLessEqual(len(alive), 1, "%d fetch threads alive" % len(alive))

    def test_an_update_request_still_waits_for_the_fetch(self):
        """/api/update exists to return the count after the fetch, not before it."""
        CA._git_run = self._slow_git()
        t = time.time()
        CA.fleet_origin_status(force_fetch=True)
        waited = (time.time() - t) * 1000.0
        self.assertGreaterEqual(waited, SLOW_S * 1000.0 * 0.9,
                                "force_fetch returned in %.0f ms — /api/update no longer waits"
                                % waited)

    def test_an_update_joins_the_fetch_already_in_flight(self):
        """Two git fetches at once is how /api/update sat for 29s on Routine I
        39213642558. The boot kicks one fetch. The page's GET /api/update then
        started a second and waited out the 25s timeout on the lock. The film
        jpeg stayed queued, the theatre heal closed the stage, and Space did
        nothing. One fetch, and the update waits for that one."""
        CA._git_run = self._slow_git()
        self.assertTrue(CA._fleet_fetch_kick(), "the boot fetch did not start")
        CA.fleet_origin_status(force_fetch=True)
        self.assertEqual(len(self.fetches), 1,
                         "%d git fetches ran — /api/update started its own beside the one already in flight"
                         % len(self.fetches))


RED_PROOF = [
    {
        "why": "restoring the SYNCHRONOUS survey inside the polled handler — the exact code that "
               "produced the 612,893 ms /api/status kept in tv/.status_worst.json",
        "file": "control_app.py",
        "find": "        _vault_autoread_kick()",
        "replace": ("        c[\"t\"], c[\"d\"] = time.time(), _vault_autoread_state()\n"
                    "        fresh = True"),
        "matches": 1,
    },
    {
        "why": "dropping the one-at-a-time flag: a slow survey under a once-a-second poll then "
               "starts a fresh thread every second instead of being absorbed",
        "file": "control_app.py",
        "find": '        if _VAULT_AUTOREAD_REFRESH["running"]:\n            return False',
        "replace": '        if False:\n            return False',
        "matches": 1,
    },
    {
        "why": "reporting the lane as OFF before anything has surveyed it — an unmeasured lamp "
               "rendered as a measured one",
        "file": "control_app.py",
        "find": '        return {"on": None, "ageMs": None, "stale": True,',
        "replace": '        return {"on": False, "ageMs": None, "stale": True,',
        "matches": 1,
    },
    {
        "why": "the lamp refresh takes the vault loop's name, so a status poll before the "
               "roster starts leaves the loop unstarted for the life of the process",
        "file": "control_app.py",
        "find": '    threading.Thread(target=_run, daemon=True, name="tvd-vault-lamp").start()\n',
        "replace": '    threading.Thread(target=_run, daemon=True, name="tvd-vault-autoread").start()\n',
        "matches": 1,
    },
    {
        "why": "running the lock census on the request thread again — the 6,419 ms "
               "selfArming stall the rinse spec reports as the server never coming up",
        "file": "control_app.py",
        "find": "        _self_arming_kick()",
        "replace": "        c[\"t\"], c[\"d\"] = time.time(), _self_arming_state()",
        "matches": 1,
    },
    {
        "why": "the status poll calls the synchronous census again, so a slow report "
               "lands on every /api/status",
        "file": "control_app.py",
        "find": '        "selfArming": _t("selfArming", _self_arming_state_cached),',
        "replace": '        "selfArming": _t("selfArming", _self_arming_state),',
        "matches": 1,
    },
    {
        "why": "dropping the one-at-a-time flag on the lock census, so a slow report "
               "plus a once-a-second poll starts a thread per poll",
        "file": "control_app.py",
        "find": '        if _SELF_ARM_REFRESH["running"]:\n            return False',
        "replace": '        if False:\n            return False',
        "matches": 1,
    },
    {
        "why": "rendering the badge OPEN before the census has been read — an unmeasured "
               "lock shown as an open one",
        "file": "control_app.py",
        "find": ('        return {"ok": False, "open": 0, "total": 0, "locks": [],\n'
                 '                "why": "the lock census has not finished its first read since this "\n'
                 '                       "console started — UNKNOWN, and specifically not open"}'),
        "replace": ('        return {"ok": True, "open": 1, "total": 1, '
                    '"locks": [{"state": "OPEN"}], "why": "open before the census"}'),
        "matches": 1,
    },
    {
        "why": "git fetch back on the status thread — a 25s fetch before bind, which "
               "the 20s rinse boot poll reports as the server never coming up",
        "file": "control_app.py",
        "find": ("        elif (now - _FLEET_LAST_FETCH) >= _FLEET_FETCH_TTL_S:\n"
                 "            _fleet_fetch_kick()"),
        "replace": ("        elif (now - _FLEET_LAST_FETCH) >= _FLEET_FETCH_TTL_S:\n"
                    "            _git_run([\"git\", \"fetch\", \"origin\", \"main\", \"--quiet\"], "
                    "cwd=REPO, capture_output=True, timeout=25)\n"
                    "            _FLEET_LAST_FETCH = now"),
        "matches": 1,
    },
    {
        "why": "/api/update starts a second git fetch beside the one already in flight "
               "and the two sit on the index lock until the 25s timeout",
        "file": "control_app.py",
        "find": "                _fleet_fetch_kick()\n                _fleet_fetch_wait(25)",
        "replace": ("                _git_run([\"git\", \"fetch\", \"origin\", \"main\", \"--quiet\"], "
                    "cwd=REPO, capture_output=True, timeout=25)\n"
                    "                _FLEET_LAST_FETCH = now"),
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
