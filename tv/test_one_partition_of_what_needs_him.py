# -*- coding: utf-8 -*-
"""v3308 — THERE IS ONE PARTITION OF "WHAT NEEDS HIM", AND EVERY SURFACE QUOTES THAT ONE.

⚠⚠ THIS LAW EXISTS BECAUSE I DRIFTED THE RULE MYSELF, WITHIN AN HOUR OF SHIPPING IT.

v3307 taught the watchdog's `_EAGLE` partition about `BY_DESIGN`, so rows already ruled NOT-DEFECTS
(#29 `end routes reachable`, #30 `the river`) stop billing him — his #35 standing rule: *"WAITING
ON YOU MEANS ACTION IS NEEDED FROM HIM RIGHT NOW."*

The `/api/eagle` ROUTE — the one his console actually reads — kept its own copy and knew only about
`MINE`. MEASURED on his live console minutes after the ship: the engine partitioned to **7** and
the route still answered **needsYou=9**, with `byDesign` absent entirely. Two surfaces, one
question, a number he acts on.

⚠ AND THE ROUTE'S COMMENT SAID IT WAS FINE. Verbatim: *"the SAME rule as the _EAGLE partition, and
the only one any surface may quote from here on."* True when written; my change made it false. That
is exactly how a copy drifts — **nobody edits the comment when they change the other copy**. Prose
cannot hold two copies in step. One definition can.

Same shape, third time in this arc: v3295 (`lane_read_tags`, three copies of a lane's work list),
v3301/REG-1115 (`/api/relaunch`'s third busy list, which had drifted into deadlocking the button),
and now this. [[copy-drift]] [[the-unjoined-end]]

TWO HALVES, failing for different reasons on purpose:
  1. STRUCTURAL — no production module partitions doctor rows by hand. `eagle_partition()` is the
     single definition, and hand-rolled membership tests against MINE/BY_DESIGN are banned outright
     rather than checked caller-by-caller: the third copy here was found by a grep, not by the
     investigation that started this.
  2. BEHAVIOURAL — the partition actually keeps a BY_DESIGN row out of `bad` and still SHOWS it.
     Structure alone would pass a function that returned the wrong sets, which is the same defect
     one layer down. [[presence-law-vs-reachability-law]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

from frame_authority import _executable_only             # noqa: E402

APP = os.path.join(HERE, "control_app.py")

#: A hand-rolled partition of doctor rows. This is the shape that drifted.
BY_HAND = re.compile(r'get\("check"\)\s+(?:not\s+)?in\s+_?(?:mine_names|design_names|not_his)')


class TestOnePartitionOfWhatNeedsHim(unittest.TestCase):

    def test_no_module_partitions_the_rows_by_hand(self):
        """STRUCTURAL: one definition, or the copies disagree about a number he acts on."""
        with io.open(APP, encoding="utf-8") as fh:
            src = fh.read()
        # ⚠ ".py", NOT ".js" — _executable_only dispatches on EXTENSION and the .js branch does
        # not strip Python `#` comments. The prose above the fixed call NAMES these very symbols,
        # so a .js strip would have this law reading its own commentary. Measured the hard way in
        # v3304's sibling law. [[source-reading-guard]] REG-1070
        code = _executable_only(src, ".py")
        self.assertGreater(
            len(code), 200000,
            "the comment strip returned only %d chars of control_app.py — it ran away, so a clean "
            "count from it proves nothing. [[zero-needs-a-denominator]]" % len(code))

        # ⚠ THE DEFINITION IS EXEMPT — it is the one place the rule is ALLOWED to be written,
        # and a law that bans its own subject everywhere flags the fix as the defect. Measured:
        # the first cut reported 3 hits, all three INSIDE eagle_partition. Same exemption shape
        # as test_a_lane_has_one_work_list, which excludes shelf_driver — the map's owner.
        # Print the match count and investigate: 3 hits, all in the owner => the LAW was wrong.
        i = code.find("def eagle_partition(")
        self.assertGreater(i, -1, "the single definition is gone, so there is nothing to exempt")
        j = code.find("\ndef ", i + 10)
        self.assertGreater(j, i, "could not bound eagle_partition — refusing to judge a slice "
                                 "whose far end is a guess. [[source-reading-guard]]")
        owner_span = (i, j)

        hits = []
        for m in BY_HAND.finditer(code):
            if owner_span[0] <= m.start() < owner_span[1]:
                continue                      # the owner may write the rule; that is the point
            line = code[:m.start()].count("\n") + 1
            hits.append("stripped line %d" % line)
        self.assertEqual(
            hits, [],
            "%d site(s) partition doctor rows by hand instead of calling eagle_partition(): %s. "
            "That is the copy that drifted in v3308 — the /api/eagle route knew only about MINE, "
            "so the ENGINE said needsYou=7 and the SCREEN HE READS said 9."
            % (len(hits), ", ".join(hits)))

    def test_the_route_and_the_watchdog_both_call_it(self):
        """A single definition nothing calls is the unjoined end this is about."""
        with io.open(APP, encoding="utf-8") as fh:
            src = fh.read()
        code = _executable_only(src, ".py")
        self.assertIn("def eagle_partition(", code, "the single definition is gone")
        calls = 0
        for m in re.finditer(r"eagle_partition\s*\(", code):
            bol = code.rfind("\n", 0, m.start()) + 1
            if code[bol:m.start()].lstrip().startswith("def "):
                continue                      # the definition is not a call
            calls += 1
        self.assertGreaterEqual(
            calls, 2,
            "eagle_partition() has %d caller(s); BOTH the watchdog pass and the /api/eagle route "
            "must use it. One of them recomputing is how the screen and the engine came to "
            "disagree in the first place." % calls)

    def test_a_BY_DESIGN_row_is_kept_out_of_needsYou_but_still_SHOWN(self):
        """BEHAVIOURAL, and the second half matters as much as the first."""
        import control_app as ca
        rows = [
            {"check": "end routes reachable", "state": "missing"},   # BY_DESIGN
            {"check": "the river",            "state": "missing"},   # BY_DESIGN
            {"check": "ledger staleness",     "state": "missing"},   # genuinely his
            {"check": "board join",           "state": "missing"},   # MINE
            {"check": "tooltip finder",       "state": "unknown"},
            {"check": "engines corroborate",  "state": "unmeasured"},
        ]
        p = ca.eagle_partition(rows)
        his = {r["check"] for r in p["bad"]}
        self.assertEqual(
            his, {"ledger staleness"},
            "the partition bills him for %s. Only rows that need action FROM HIM RIGHT NOW belong "
            "in that count — his #35 ruling, verbatim: 'If nothing is actually required of him, it "
            "does not belong in the count he acts on.'" % sorted(his))
        self.assertEqual(
            {r["check"] for r in p["byDesign"]}, {"end routes reachable", "the river"},
            "a BY_DESIGN row VANISHED instead of moving buckets. That is silencing by another "
            "name: the rows would leave his count with nothing showing where they went.")
        self.assertEqual({r["check"] for r in p["mine"]}, {"board join"})
        self.assertEqual(
            {r["check"] for r in p["unk"]}, {"tooltip finder", "engines corroborate"},
            "UNMEASURED must land in UNKNOWN beside unknown — a periodic not asked this tick "
            "carries its last verdict and does NOT bill him.")

    def test_an_unreadable_roster_BILLS_rather_than_silences(self):
        """⚠ THE DIRECTION OF THE FAILURE. A roster that will not load must never shrink his count."""
        import unittest.mock as mock
        import control_app as ca
        import console_doctor as cd
        rows = [{"check": "end routes reachable", "state": "missing"},
                {"check": "ledger staleness", "state": "missing"}]

        # ⚠⚠ IT MUST BE TRUTHY, AND THE FIRST CUT WAS NOT — caught by red-proof [2] coming back
        # BLIND at a match count of 1, which is the tell that the LAW is weak rather than the
        # sabotage. `eagle_partition` reads `getattr(cd, "BY_DESIGN", {}) or {}`, so an EMPTY dict
        # short-circuits to `{}` and is never iterated: the exception never fired and the except
        # branch the proof sabotages was never reached. A mock that cannot raise tests nothing.
        # [[sabotage-is-usually-the-wrong-one]] [[regression-guard]] §5
        class _Boom(dict):
            def __init__(self):
                dict.__init__(self, {"_present_so_this_is_truthy": 1})

            def __iter__(self):
                raise RuntimeError("roster unreadable")

        with mock.patch.object(cd, "BY_DESIGN", _Boom()):
            p = ca.eagle_partition(rows)
        self.assertEqual(
            len(p["bad"]), 2,
            "an unreadable BY_DESIGN roster SILENCED a row. A roster nobody can load is UNKNOWN, "
            "and the safe direction is to bill him and be wrong noisily — not to quietly shrink "
            "the number he acts on for a reason no surface shows. [[unknown-stays-unknown]]")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "the route recomputing the partition is exactly the drift that said 9 while the engine said 7",
        "file": "tv/control_app.py",
        "find": '                _p = eagle_partition(_rows)',
        "replace": ('                _mine_names = set(getattr(_cd, "MINE", {}) or {})\n'
                    '                _miss = [r for r in _rows if r.get("check") not in _mine_names]\n'
                    '                _p = {"bad": _miss, "mine": [], "byDesign": [], "unk": []}'),
        "matches": 1,
    },
    {
        "why": "dropping BY_DESIGN from the partition puts rows ruled NOT-DEFECTS back on his count",
        "file": "tv/control_app.py",
        "find": '        "bad":      [r for r in miss if r.get("check") not in not_his],',
        "replace": '        "bad":      [r for r in miss if r.get("check") not in mine_names],',
        "matches": 1,
    },
    {
        "why": "an unreadable roster that silences instead of billing shrinks his count invisibly",
        "file": "tv/control_app.py",
        "find": '''    except Exception:
        design_names = set()''',
        "replace": '''    except Exception:
        design_names = {"end routes reachable", "the river", "ledger staleness"}''',
        "matches": 1,
    },
]
