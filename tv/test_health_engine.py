#!/usr/bin/env python3
"""Guards for the health engine. It REPORTS and never repairs, and UNKNOWN is never ok."""
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import health_engine as HE


class TestItReportsAndNeverRepairs(unittest.TestCase):
    """His rule, and the reason for it: an auto-healer can turn one fault into two, unattended."""

    def test_the_module_writes_nothing(self):
        import inspect
        src = inspect.getsource(HE)
        for forbidden in ("os.remove", "unlink", "rmtree", "subprocess", "kill", '"w"', "'w'"):
            self.assertNotIn(forbidden, src,
                             "health_engine must stay a reader; found %r" % forbidden)

    def test_every_check_returns_a_state_the_surface_can_render(self):
        rep = HE.report()
        self.assertTrue(rep["rows"], "no checks ran at all")
        for r in rep["rows"]:
            self.assertIn(r["state"], (HE.OK, HE.WARN, HE.BLOCKED, HE.UNKNOWN))
            self.assertTrue(r["line"], "%s produced no line for him to read" % r["id"])
            self.assertTrue(r["measuredAt"], "%s carries no measurement time" % r["id"])


class TestUnknownIsNeverOk(unittest.TestCase):
    """⚠ THE WHOLE POINT. "the board is not open so its store cannot be asked" is not "fine"."""

    def test_an_unoffered_board_is_UNKNOWN_not_ok(self):
        r = HE.check_board_join(None)
        self.assertEqual(r["state"], HE.UNKNOWN)
        self.assertIn("not the same as", r["line"])

    def test_a_board_that_does_not_answer_is_UNKNOWN(self):
        def boom(_js):
            raise RuntimeError("window is gone")
        self.assertEqual(HE.check_board_join(boom)["state"], HE.UNKNOWN)

    def test_an_unreadable_answer_is_UNKNOWN(self):
        self.assertEqual(HE.check_board_join(lambda _js: "not json")["state"], HE.UNKNOWN)

    def test_a_check_that_RAISES_is_UNKNOWN_not_dropped(self):
        # a check that throws must not vanish from the report — silence would read as ok
        def explode():
            raise ValueError("boom")
        old = HE.CHECKS[:]
        HE.CHECKS.append(explode)
        try:
            rep = HE.report()
            hit = [r for r in rep["rows"] if r["state"] == HE.UNKNOWN and "raised" in r["line"]]
            self.assertTrue(hit, "a raising check disappeared from the report instead of reporting UNKNOWN")
        finally:
            HE.CHECKS[:] = old

    def test_UNKNOWN_alone_stops_the_whole_report_being_ok(self):
        rep = HE.report()          # board_join is unknown with no evaluate injected
        self.assertNotEqual(rep["state"], HE.OK)


class TestTheBoardJoinCheck(unittest.TestCase):
    """The check the register failure needed. The console asking ITSELF must read BLOCKED."""

    def test_the_console_asking_itself_is_BLOCKED_and_says_so(self):
        r = HE.check_board_join(lambda _js: '{"p":"/","has":false}')
        self.assertEqual(r["state"], HE.BLOCKED)
        self.assertIn("CONSOLE, not the board", r["line"])

    def test_a_reachable_board_is_ok(self):
        r = HE.check_board_join(lambda _js: '{"p":"/board","has":true}')
        self.assertEqual(r["state"], HE.OK)


class TestTheBoardJoinPayloadPath(unittest.TestCase):
    """⚠ THE PATH THAT ACTUALLY RUNS. Nothing on the console holds a window handle to hand this
    module, so the `evaluate` door was a tap nobody could open and this flag was UNKNOWN for ever.
    A flag that can only ever say one thing is furniture. [[plumbing-with-no-tap]]"""

    def test_a_reachable_board_is_ok(self):
        r = HE.check_board_join(payload={"ok": True, "hasChronicleApply": True, "path": "/board"})
        self.assertEqual(r["state"], HE.OK)
        self.assertIn("/board", r["line"])

    def test_the_console_answering_for_the_board_is_BLOCKED_and_names_the_page(self):
        r = HE.check_board_join(payload={"ok": True, "hasChronicleApply": False, "path": "/"})
        self.assertEqual(r["state"], HE.BLOCKED)
        self.assertIn("CONSOLE, not the board", r["line"])

    def test_a_console_build_too_old_to_answer_is_UNKNOWN_not_ok(self):
        # his RUNNING console serves the code it booted with; a build without the field must not
        # read as a healthy join. Measured live 2026-08-29 — this is the real state today.
        r = HE.check_board_join(payload={"ok": True, "boardLoaded": True})
        self.assertEqual(r["state"], HE.UNKNOWN)
        self.assertIn("nobody asked", r["line"])

    def test_a_refusing_or_absent_board_is_UNKNOWN(self):
        for p in ({"ok": False, "why": "the board window is not open"}, None, "junk"):
            if p is None:
                continue                       # None means "no payload offered" — the other path
            self.assertEqual(HE.check_board_join(payload=p)["state"], HE.UNKNOWN)

    def test_the_payload_beats_the_evaluate_door_when_both_are_offered(self):
        # one answer, not two that can disagree
        r = HE.check_board_join(evaluate=lambda _js: '{"p":"/","has":false}',
                                payload={"ok": True, "hasChronicleApply": True, "path": "/board"})
        self.assertEqual(r["state"], HE.OK)

    def test_report_threads_the_payload_through(self):
        rep = HE.report(board={"ok": True, "hasChronicleApply": True, "path": "/board"})
        row = [r for r in rep["rows"] if r["id"] == "board_join"][0]
        self.assertEqual(row["state"], HE.OK,
                         "report() dropped the board payload on the floor, so the console rail "
                         "would go on reporting UNKNOWN whatever the board said")


class TestTheConsoleRailIsTheONLYSurface(unittest.TestCase):
    """He asked for \"one unit system engine locked in\". This machine already had FOUR things
    implementing report-never-repair; a fifth parallel surface would be [[copy-drift]] exactly."""

    def test_the_eagle_eye_carries_every_health_check(self):
        import console_doctor as CD
        names = [n for n, _ in CD.CHECKS]
        for want in ("armed migration", "extraction lanes", "board join", "stray processes"):
            self.assertIn(want, names,
                          "%r is not on the eagle-eye rail, so it is a flag nobody sees" % want)

    def test_the_rail_maps_UNKNOWN_to_UNKNOWN(self):
        # the one distinction that may never be lost in the state map
        import console_doctor as CD
        state, detail = CD._health("board_join")()
        self.assertIn(state, (CD.OK, CD.MISSING, CD.UNKNOWN))
        self.assertTrue(detail)

    def test_one_tick_reads_HIS_BOARD_once_not_three_times(self):
        """/api/board_ownership EVALUATES JAVASCRIPT IN THE WINDOW HE IS LOOKING AT. Three checks
        need it now and two of those predate this fold, so the rail was already poking his live
        board twice every ten minutes with nothing saying so. [[borrowed-surface]]"""
        import console_doctor as CD
        calls, real = [], CD._post
        CD._post = lambda p, b=None, timeout=20: (calls.append(p),
                                                  {"ok": True, "boardLoaded": False})[1]
        try:
            CD.run(include_slow=False)
        finally:
            CD._post = real
        self.assertEqual(calls.count("/api/board_ownership"), 1,
                         "one rail tick asked his board %d times"
                         % calls.count("/api/board_ownership"))

    def test_OUTSIDE_a_tick_every_check_reads_fresh(self):
        """⚠ THE PROPERTY MY FIRST CUT BROKE. A 5-second module-level memo swallowed the `_post`
        stub and served the previous test's answer — EIGHT existing guards failed at once, which is
        a shape mistake, not eight defects. [[feedback-suspect-the-instrument]]"""
        import console_doctor as CD
        calls, real = [], CD._post
        CD._post = lambda p, b=None, timeout=20: (calls.append(p), {"ok": True})[1]
        try:
            CD._board_read(); CD._board_read()
        finally:
            CD._post = real
        self.assertEqual(len(calls), 2,
                         "a check called on its own reused a cached answer, so any guard that "
                         "stubs _post is now measuring the previous test")

    def test_a_check_that_disappears_reads_UNKNOWN_not_ok(self):
        import console_doctor as CD
        # the tick must be OPEN for the injected report to be the one consulted — outside a tick
        # every check reads fresh, which is the property that keeps stubbed guards working
        CD._health_cache["active"] = True
        CD._health_cache["rep"] = {"rows": [], "state": "ok", "why": ""}
        try:
            state, detail = CD._health("armed_migration")()
        finally:
            CD._health_cache["active"] = False
            CD._health_cache["rep"] = None
        self.assertEqual(state, CD.UNKNOWN)
        self.assertIn("no longer reports", detail)


class TestTheArmedMigrationCheck(unittest.TestCase):
    """⚠ THE CHECK THAT WOULD HAVE CAUGHT THE LOADED GUN. The v2205 undo was armed on every board
    since v2203 and would have dropped 273 of his 280 owned names, and nothing watched for it."""

    def test_it_is_GREEN_on_the_current_tree(self):
        self.assertEqual(HE.check_armed_migrations()["state"], HE.OK)

    def test_it_WOULD_HAVE_GONE_RED_on_the_pre_fix_code(self):
        # ⚠ A CHECK NOBODY HAS SEEN FIRE IS NOT A CHECK. Rebuild the exact pre-v2275 shape — a
        # retirement that stamps the flag, and a gate that trusts the flag's PRESENCE — and prove
        # this check calls it ARMED. [[regression-guard]]
        import tempfile, shutil
        root = tempfile.mkdtemp(prefix="armed-")
        self.addCleanup(shutil.rmtree, root, True)
        os.makedirs(os.path.join(root, "tv"))
        with io.open(os.path.join(root, "bible.html"), "w", encoding="utf-8") as fh:
            fh.write("var DONE='d2r_vaultBackfill_v2200';\n"
                     "window.LSR.setItem(DONE, JSON.stringify({retired:'v2203'}));\n"
                     "if (!window.LSR.getItem('d2r_vaultBackfill_v2200')) return;   // it never ran here\n")
        old_here = HE.HERE
        HE.HERE = os.path.join(root, "tv")
        try:
            r = HE.check_armed_migrations()
        finally:
            HE.HERE = old_here
        self.assertEqual(r["state"], HE.BLOCKED,
                         "the pre-fix code did NOT read as armed — this check would have watched "
                         "the v2205 undo sit loaded and said nothing")
        self.assertIn("ARMED", r["line"])


if __name__ == "__main__":
    try:
        import console_safe as _cs
        _cs.enable()
    except Exception:
        pass
    unittest.main(verbosity=1)
