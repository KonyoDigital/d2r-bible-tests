# -*- coding: utf-8 -*-
"""v2748 — THE DERIVED END-ROUTE PREDICATE WAS BUILT, GATED, AND READ BY NOTHING.

MEASURED before a line of this was written:

    grep -c end_routes  tv/control_app.py      0
                        tv/console_doctor.py   0
                        tv/corroborate.py      0
                        tv/control_ui.html     0
                        tv/run_gates.py        2   <- its own registration, and nothing else

Built, correct, covered by 27 of its own tests, and invisible to every surface and every
supervision layer. That is the SAME defect this heart caught in `reel_router` ONE VERSION AGO — I
fixed the river's unjoined end and left its sibling running, which is precisely what sweep-dont-ask
exists to prevent. [[the-unjoined-end]] [[sweep-dont-ask]] [[plumbing-with-no-tap]]

=== WHY THE ROW SPLITS DEAD-ENDED FROM FINISHED-WAITING ===
Konyo's ruling settled the DESTINATION and named the METHOD: *"reverse engineeer it if needed the
ones that are working"*. The predicate came off the 410 reels that already reached the end route —
99.27% coverage against a declared 95% floor — and it separates two states that look identical from
outside:
  · DEAD-ENDED       every door refused, with numbers. THIS is what his ruling forbids.
  · FINISHED-WAITING a door OPENED; only circumstance holds it. His ruling does not forbid it.
Counting both would make the row read 40 of 40 — true, useless, and ignored within a week. A
distrusted instrument is a switched-off one.

⚠ RED TODAY AT 32 OF 40, ON PURPOSE. A check that could only ever be green measures nothing. This
file therefore asserts the row CAN fail and CAN pass, never that it currently passes.
⛔ AND NO WILSON LOCK: "these reels cannot reach an end route" is a READING. A score belongs on a
claim attacks can refute; manufacturing attacks to give a state a number is the inflation
`_hardening_gap` refuses.
"""
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

import console_doctor as D  # noqa: E402


def _verdict(payload):
    """Force any report through the real check without touching his shelf."""
    import end_routes as ER
    fn = dict(D.CHECKS)["end routes reachable"]
    real = ER.report
    ER.report = lambda *a, **k: payload
    try:
        return fn()
    finally:
        ER.report = real


def _rep(dead=0, waiting=0, walked=0, rows=None, ok=True):
    return {"ok": ok, "deadEnded": dead, "finishedWaiting": waiting, "walked": walked,
            "rows": rows if rows is not None else [], "why": "forced"}


def _row(dead, *lacks):
    return {"deadEnded": dead, "missing": [{"what": w} for w in lacks]}


class TheEndRouteIsWatched(unittest.TestCase):

    # ── ⚠ THE JOINT ───────────────────────────────────────────────────────────────────────────
    def test_the_row_is_REGISTERED(self):
        """A check defined and not in CHECKS runs NEVER — this repo's most repeated defect in its
        smallest form, and the reason this file exists at all."""
        self.assertIn("end routes reachable", dict(D.CHECKS),
                      "the end-route row is not registered, so it never runs")

    def test_the_module_is_actually_READ_by_the_console(self):
        """The measured defect was literally zero references outside its own gate line."""
        doc = io.open(os.path.join(HERE, "console_doctor.py"), encoding="utf-8").read()
        self.assertIn("import end_routes", doc,
                      "console_doctor no longer reads end_routes, so the derived predicate is back "
                      "to being built and unread")

    # ── ⚠⚠ IT MUST BE ABLE TO FAIL, AND TO PASS ───────────────────────────────────────────────
    def test_a_dead_ended_reel_is_MISSING_and_names_WHAT_IT_LACKS(self):
        st, say = _verdict(_rep(dead=2, waiting=1, walked=3,
                                rows=[_row(True, "panels read", "chronicle pages"),
                                      _row(True, "panels read", "a vault seal"),
                                      _row(False)]))
        self.assertEqual(D.MISSING, st, "dead-ended reels were graded as fine")
        self.assertIn("2 of 3", say)
        self.assertIn("panels read", say,
                      "the message does not name WHAT the reels lack — a count alone is not "
                      "actionable, and '32 reels are stuck' is what nobody can act on")

    def test_no_dead_ends_is_OK(self):
        """The other direction, and it matters as much: a row that can only be red is as useless as
        one that can only be green."""
        st, _ = _verdict(_rep(dead=0, waiting=8, walked=40))
        self.assertEqual(D.OK, st, "a shelf with no dead-ended reel was still graded as stuck")

    # ── ⚠ THE SPLIT ───────────────────────────────────────────────────────────────────────────
    def test_FINISHED_WAITING_is_not_counted_as_dead_ended(self):
        """A door that OPENED and is held by circumstance is not what his ruling forbids. Counting
        it makes the row read 40 of 40 — true, useless, ignored."""
        st, say = _verdict(_rep(dead=0, waiting=8, walked=40))
        self.assertEqual(D.OK, st, "finished-waiting reels were counted as dead-ended: %s" % say)

    def test_the_message_reports_the_waiting_count_TOO(self):
        """Both numbers travel, each under its own name. One number doing two jobs is how 42 rows
        were once claimed over a pass that produced 7."""
        st, say = _verdict(_rep(dead=1, waiting=7, walked=8, rows=[_row(True, "panels read")]))
        self.assertIn("7", say, "the finished-waiting count is no longer reported beside the "
                                "dead-ended one")

    # ── UNKNOWN is never collapsed into OK ────────────────────────────────────────────────────
    def test_an_unreadable_report_is_UNKNOWN_not_OK(self):
        for bad in ({"ok": False, "why": "simulated"}, None, {}):
            st, _ = _verdict(bad)
            self.assertEqual(D.UNKNOWN, st,
                             "a report of %r was treated as a measurement" % (bad,))

    def test_a_MISSING_count_is_UNKNOWN_not_zero(self):
        """⚠ `deadEnded: None` means nobody counted. Reading it as 0 would publish 'no reel is
        dead-ended' over a shelf nobody looked at. [[unknown-stays-unknown]]"""
        st, say = _verdict({"ok": True, "deadEnded": None, "finishedWaiting": None,
                            "walked": None, "rows": []})
        self.assertEqual(D.UNKNOWN, st,
                         "an uncounted shelf was graded %r instead of UNKNOWN" % st)

    # ── ⛔ NO WILSON LOCK ON A STATE ───────────────────────────────────────────────────────────
    def test_no_wilson_lock_was_invented_for_this_state(self):
        try:
            import self_arming as SA
        except Exception:
            self.skipTest("self_arming unavailable")
        proves = getattr(SA, "PROVES", {}) or {}
        for bad in ("end.route", "end_routes", "route.reachable", "endroute.reachable"):
            self.assertNotIn(bad, proves,
                             "%s was declared as a lock. Whether a reel can reach an end route is a "
                             "READING the doctor takes, not a claim attacks can refute." % bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
