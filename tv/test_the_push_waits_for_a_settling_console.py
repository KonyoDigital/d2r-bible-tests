#!/usr/bin/env python3
"""#42c — THE PUSH LETS HIS CONSOLE FINISH MOVING ONTO THE PUSHED CODE BEFORE THE DEMOS DRIVE IT.

v3526 push #1 was REFUSED on a green tree: the fast-forward of main put new code on disk, his console's drift lane re-exec'd
onto it, and the pre-push demos ran 7 s later - j7_shelfStory timed out against a console still booting; 16/16 once it had
settled. tv/console_settle.py now reads /api/status and waits, bounded, while the console runs older code than the file
on disk (its re-exec is coming), relaunched under MIN_AGE_S ago, or says its engine is not ready. A held relaunch, no
answer or the bound running out all go on: the demos decide, and nothing here refuses a push.

Fixture statuses and a fake clock only - his console is never asked. [[stale-reading]] [[source-reading-guard]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import console_settle as CS  # noqa: E402

NOW = 1_790_000_000_000


def _st(stale=False, loaded_s_ago=600, may=None, engine=True, known=True):
    rl = None if may is None else {"may": may, "blocker": None if may else "his-session", "waiting": None if may else
                                   "his session is live"}
    return {"moduleFreshness": {"known": known, "stale": stale, "loadedAtMs": NOW - loaded_s_ago * 1000},
            "drift": {"relaunch": rl}, "engineReady": engine}


class TheVerdict(unittest.TestCase):

    def test_older_code_on_the_console_waits_for_its_reexec(self):
        self.assertEqual(CS.verdict(_st(stale=True), NOW)[0], "wait",
                         "the console runs older code than the file on disk and the demos were let at it - the "
                         "exact v3526 refusal")
        self.assertEqual(CS.verdict(_st(stale=True, may=True), NOW)[0], "wait")

    def test_a_held_relaunch_does_not_wait_for_ever(self):
        state, why = CS.verdict(_st(stale=True, may=False), NOW)
        self.assertEqual(state, "go", "a relaunch his session holds will not come - waiting only burns the gate")
        self.assertIn("held", why)

    def test_a_console_that_just_relaunched_settles_first(self):
        self.assertEqual(CS.verdict(_st(loaded_s_ago=7), NOW)[0], "wait")
        self.assertEqual(CS.verdict(_st(loaded_s_ago=31), NOW)[0], "go")

    def test_an_engine_not_ready_waits(self):
        self.assertEqual(CS.verdict(_st(engine=False), NOW)[0], "wait")

    def test_no_answer_goes_on_and_says_so(self):
        state, why = CS.verdict(None, NOW)
        self.assertEqual(state, "go")
        self.assertIn("did not answer", why)

    def test_an_unmeasured_freshness_is_not_read_as_stale(self):
        self.assertEqual(CS.verdict(_st(stale=True, known=False), NOW)[0], "go")


class TheWait(unittest.TestCase):

    def _clock(self, start=NOW / 1000.0):
        t = {"now": start}
        return t, (lambda: t["now"]), (lambda s: t.__setitem__("now", t["now"] + s))

    def test_it_waits_through_the_reexec_and_the_settle_then_goes(self):
        t, clock, sleep = self._clock()
        t0 = t["now"]
        reexec_at = t0 + 20                      # the drift lane re-execs 20 s into the wait

        def fetch():
            if t["now"] < reexec_at:
                return dict(_st(stale=True), moduleFreshness={"known": True, "stale": True,
                                                               "loadedAtMs": int((t0 - 3600) * 1000)})
            return {"moduleFreshness": {"known": True, "stale": False, "loadedAtMs": int(reexec_at * 1000)},
                    "drift": {"relaunch": None}, "engineReady": True}
        state, why, waited = CS.wait(fetch=fetch, clock=clock, sleep=sleep, max_wait_s=360, min_age_s=30, poll_s=5)
        self.assertEqual(state, "go")
        self.assertGreaterEqual(waited, 50, "the demos were let at a console %.0f s after its re-exec" % (waited - 20))
        self.assertLess(waited, 60)
        self.assertIn("waited", why)

    def test_the_bound_holds(self):
        t, clock, sleep = self._clock()
        state, why, waited = CS.wait(fetch=lambda: _st(stale=True), clock=clock, sleep=sleep, max_wait_s=40, poll_s=5)
        self.assertEqual(state, "timeout")
        self.assertLessEqual(waited, 45, "the wait ran past its bound")

    def test_a_settled_console_costs_nothing(self):
        t, clock, sleep = self._clock()
        state, _why, waited = CS.wait(fetch=lambda: _st(), clock=clock, sleep=sleep)
        self.assertEqual((state, waited), ("go", 0))


class TheHookAsksBeforeTheDemos(unittest.TestCase):

    def test_the_settle_runs_before_the_demos_drive_the_console(self):
        src = io.open(os.path.join(HERE, "..", "hooks", "pre-push"), encoding="utf-8").read()
        settle = src.find('tv/console_settle.py" --wait')
        demos = src.find('gate_run "console-demos"')
        self.assertGreater(settle, 0, "the pre-push hook no longer waits for a settling console")
        self.assertGreater(demos, 0, "the console-demos gate is not where this law expects it")
        self.assertLess(settle, demos, "the settle wait runs AFTER the demos - it protects nothing")


RED_PROOF = [
    {
        "why": "#42c - a console running older code than the file on disk is demoed at once: the v3526 push-1 refusal",
        "file": "console_settle.py",
        "find": "        return \"wait\", \"it runs older code than the file on disk - its re-exec onto the pushed code is coming\"\n",
        "replace": "        return \"go\", \"it runs older code than the file on disk - its re-exec onto the pushed code is coming\"\n",
        "matches": 1,
    },
    {
        "why": "#42c - a console seconds after its re-exec is demoed at once",
        "file": "console_settle.py",
        "find": "        if age < min_age_s:\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        "why": "#42c - the hook stops asking before the demos",
        "file": "hooks/pre-push",
        "find": "      echo \"pre-push: [$(_pp_el)] $(python3 \"$REPO/tv/console_settle.py\" --wait 360",
        "replace": "      echo \"pre-push: [$(_pp_el)] $(python3 \"$REPO/tv/console_settle.py.off\" --off 360",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
