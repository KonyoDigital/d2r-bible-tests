# -*- coding: utf-8 -*-
"""AN ORGAN'S COVERAGE NEVER CROSSES A LANE.

MEASURED 2026-09-13. `organ_matrix` reported `fleet.sets`, `fleet.uniques`, `roster.set` and
`roster.unique` as MISNAMED on BOTH the eagle and the doctor columns — 8 cells, which was 100% of
the MISNAMED in the table. MISNAMED means, in this module's own words, *the organ IS watching that
thing and calls it something else*.

It was not watching them. Asked directly, both organs named exactly two route subjects and nothing
else:

    eagle : lanes["fleet"] = []   lanes["roster"] = []   lanes["chronicle"] = [chronicle.unique, chronicle.set]
    doctor: lanes["fleet"] = []   lanes["roster"] = []   lanes["chronicle"] = [chronicle.unique, chronicle.set]

The cells came from `one_name.same_thing`, which compares the TAIL and is deliberately lane-blind:

    same_thing("fleet.sets", "chronicle.set") -> True
    same_thing("fleet.sets", "roster.set")    -> True

So four surfaces were borrowing chronicle's organs. All six are separately registered in
`surfaces()` with `origin="route"`, so this was never a spelling difference — it was a different
subject wearing a similar tail. A table that claims a watcher it does not have is worse than the
empty table this module was written to replace; that is the module's own stated standard, in its
own docstring.

⚠ This law does NOT say the fleet and roster lanes must be covered. They are honestly ABSENT and
that is a real hole, logged as such. It says the table may never report them as WATCHED by an
organ that cannot name anything in their lane. [[unknown-stays-unknown]] [[the-unjoined-end]]
[[regression-guard]]
"""
import os
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))


def _coverage():
    import organ_matrix as OM
    cov = OM.organ_coverage()
    out = {}
    for organ, got in (cov or {}).items():
        names = got[0] if isinstance(got, tuple) else got
        out[organ] = set(str(n) for n in (names or ()))
    return out


def _lanes(names):
    """lane -> the names that claimed it. A name with no dot claims no lane."""
    out = {}
    for n in names:
        s = n.strip().lower()
        if "." in s:
            out.setdefault(s.split(".")[0], set()).add(s)
    return out


class TestAnOrganNeverCoversALaneItCannotName(unittest.TestCase):

    def test_no_cell_is_covered_or_misnamed_by_a_name_from_another_lane(self):
        """The whole table, every cell, against the organ's own vocabulary."""
        import organ_matrix as OM
        rows, _why = OM.matrix()
        cov = _coverage()
        self.assertTrue(rows, "the matrix returned no rows — nothing was measured")
        checked = 0
        bad = []
        for r in rows:
            surface = r.get("surface") or ""
            if "." not in surface:
                continue                      # no lane claimed: this law has nothing to say
            lane = surface.split(".")[0].lower()
            for organ, state in (r.get("cells") or {}).items():
                if state not in ("COVERED", "MISNAMED"):
                    continue
                checked += 1
                names = cov.get(organ) or set()
                in_lane = _lanes(names).get(lane) or set()
                # a prose name claims no lane and is allowed to stand for anything the tail matches
                prose = set(n for n in names if "." not in n)
                if not in_lane and not prose:
                    bad.append((surface, organ, state))
        print("cells claiming a watcher, checked against that organ's own lanes: %d" % checked)
        print("cells whose organ cannot name ANYTHING in that lane: %d" % len(bad))
        self.assertTrue(checked > 0,
                        "0 cells claimed a watcher — this law measured nothing, which is UNKNOWN "
                        "and not a pass")
        self.assertEqual([], bad,
                         "these cells claim an organ that names nothing in their lane: %r" % (bad,))

    def test_the_guard_itself_refuses_a_cross_lane_name(self):
        """The unit, directly — because the table above could go green by going empty."""
        import organ_matrix as OM
        self.assertFalse(OM._same_lane("fleet.sets", "chronicle.set"),
                         "fleet must not borrow chronicle's organ")
        self.assertFalse(OM._same_lane("roster.unique", "chronicle.unique"),
                         "roster must not borrow chronicle's organ")
        self.assertFalse(OM._same_lane("fleet.sets", "roster.set"),
                         "two non-chronicle lanes must not cover each other either")
        self.assertTrue(OM._same_lane("chronicle.set", "chronicle.set"),
                        "a lane must still cover itself")
        self.assertTrue(OM._same_lane("fleet.sets", "route chronicle · sets"),
                        "a PROSE name claims no lane, so the older tail rule must still decide "
                        "— otherwise this guard would erase real coverage")

    def test_the_four_borrowed_surfaces_are_honestly_absent(self):
        """The specific cells that were wrong, pinned by name so a regression is legible."""
        import organ_matrix as OM
        rows, _why = OM.matrix()
        by = dict((r.get("surface"), r) for r in rows)
        want = ("fleet.sets", "fleet.uniques", "roster.set", "roster.unique")
        # ⚠ #123 — ABSENT means "the organ answered and names nothing here". On a venue where an organ
        # cannot be read at all (every CI runner: no console, no eagle, no doctor report) EVERY one of
        # its cells is UNKNOWN, and that is the matrix being honest — CI went red with 'ABSENT' !=
        # 'UNKNOWN' while this machine passed. An organ UNKNOWN in every row is UNMEASURED here; the
        # defect this pins (a cell reading COVERED by borrowing another lane's names) is judged
        # wherever the organ answered. [[unknown-stays-unknown]]
        readable = dict((o, any((r.get("cells") or {}).get(o) not in (None, "UNKNOWN") for r in rows))
                        for o in ("eagle", "doctor"))
        if not any(readable.values()):
            self.skipTest("UNMEASURED, not a pass: neither the eagle nor the doctor can be read on "
                          "this venue, so every cell is UNKNOWN")
        seen = 0
        for s in want:
            r = by.get(s)
            self.assertIsNotNone(r, "%s is no longer a registered surface" % s)
            for organ in ("eagle", "doctor"):
                cell = (r.get("cells") or {}).get(organ)
                self.assertNotEqual("COVERED", cell,
                                    "%s/%s reads COVERED by borrowing another lane's names — the "
                                    "defect this pins" % (s, organ))
                if not readable[organ]:
                    continue
                seen += 1
                self.assertEqual("ABSENT", cell,
                                 "%s/%s must read ABSENT — neither organ names anything in that "
                                 "lane" % (s, organ))
        print("borrowed cells pinned ABSENT: %d" % seen)
        self.assertEqual(4 * sum(1 for v in readable.values() if v), seen,
                         "expected exactly the borrowed cells of every READABLE organ")


RED_PROOF = [
    {
        "why": "removes the lane guard from the resolver call, restoring the cross-lane match that "
               "let fleet and roster borrow chronicle's eagle and doctor on 8 cells",
        "file": "organ_matrix.py",
        "find": "return any(_on.same_thing(surface, n) and _same_lane(surface, n)\n"
                "                   for n in (names or ()))",
        "replace": "return any(_on.same_thing(surface, n) for n in (names or ()))",
        "matches": 1,
    },
    {
        "why": "makes the lane guard answer True for everything, which is how a guard dies quietly",
        "file": "organ_matrix.py",
        "find": "    a, b = _lane_of(surface), _lane_of(name)\n"
                "    if a is None or b is None:\n"
                "        return True\n"
                "    return a == b",
        "replace": "    return True",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
