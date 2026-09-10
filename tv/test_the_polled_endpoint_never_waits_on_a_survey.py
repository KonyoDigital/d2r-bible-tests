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
        alive = [t for t in threading.enumerate() if t.name == "tvd-vault-autoread"]
        self.assertLessEqual(len(alive), 1,
                             "%d refresh threads alive at once" % len(alive))

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
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
