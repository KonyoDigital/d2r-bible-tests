# -*- coding: utf-8 -*-
"""v2843 — THE FLEET FAILED ON HIS SCREEN AND THE HEART HAD NEVER HEARD THE WORD.

Konyo, 2026-09-09 11:07, with a photograph of his own console: *"FLEET unreachable... connect it
to the heart of the console regression and doctor and watchdoggs and eagle eyr all are suppose to
catch this."*

=== 1. THE LANE HAD NO SUPERVISION, NOT FAILING SUPERVISION ===
MEASURED at that moment:

    grep -c fleet tv/heart.py         ->  0
    grep -c fleet tv/lane_census.py   ->  0
    a fleet row in console_doctor.CHECKS  ->  none

The card said `fleet unreachable — <urlopen error _ssl.c:1112: The handshake operation timed out>`
while the heart's own footer two inches below said `♥ 8 dark` — and not one of those 8 was the
fleet. The heart was not wrong about its 8; the fleet was simply outside the vocabulary it
supervises. That is the registered-vs-existing gap (21 threads, 11 registered) with a name on it,
and it is the first of the unregistered ten to fail somewhere he could see it.
[[the-unjoined-end]] [[unknown-stays-unknown]]

=== 2. THE PANEL ALREADY HELD THE ANSWER AND WAS NEVER GIVEN IT ===
`fleet_presence_last_good()` was built in v2815 for exactly this moment — "who did we last see,
and when" kept as a SEPARATE question from "did the fetch work", because v2814 folded the two
together, flipped `ok` to True and made an unreachable console claim machines were online.

MEASURED: `grep -c lastGood control_ui.html` -> **0**. One server-side caller, no consumer. The
console was holding a three-machine roster from minutes earlier and rendered a C source location
instead. Built on both ends, never joined. [[plumbing-with-no-tap]]

=== 3. WHY THE HELPERS' SCRIPT BLOCK IS PART OF THE LAW ===
control_ui.html has TWO script blocks and a call across the boundary is a dead render that throws
at call time and paints nothing — four regressions have been spent on it. A fix to this panel that
declared `_fleetBlame` in the other block would restore the exact blank card this task exists to
end, and every hand-check would pass. So colocation is asserted, not assumed.
[[console-ui-two-script-blocks]]
"""
import io, os, re, sys, time, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _blocks(src):
    """(start, end, body) for every <script> block, in document order."""
    return [(m.start(), m.end(), m.group(1))
            for m in re.finditer(r"<script\b[^>]*>(.*?)</script>", src, re.S)]


def _block_of(blocks, idx):
    for i, (a, b, _body) in enumerate(blocks):
        if a <= idx < b:
            return i
    return None


class TestTheFleetLaneReachesTheHeart(unittest.TestCase):

    # ── LAW 1 — the heart knows the word ────────────────────────────────────────────────────
    def test_the_doctor_carries_a_fleet_row(self):
        """⚠ IMPORTED AND READ AS DATA, NOT GREPPED. The word 'fleet' appears in prose all over
        console_doctor.py; a text search would have passed on a comment. CHECKS is a list of
        (name, callable) and that is what the runner consumes, so that is what this reads.
        [[source-reading-guard]]"""
        import console_doctor as cd
        names = [n for n, _fn in cd.CHECKS]
        self.assertEqual(
            names.count("fleet reachable"), 1,
            "console_doctor.CHECKS must carry exactly one 'fleet reachable' row; it carries "
            "%d. Rows present: %s" % (names.count("fleet reachable"), ", ".join(sorted(names))))
        row = [fn for n, fn in cd.CHECKS if n == "fleet reachable"][0]
        self.assertTrue(callable(row), "the fleet row must be callable, got %r" % (row,))

    # ── LAW 2 — it distinguishes four states, and never calls a failure OK ──────────────────
    def test_the_fleet_row_never_reads_ok_while_the_fetch_is_failing(self):
        """The defect in one sentence: a lane that is down must not be green. Seeded through the
        SAME cache /api/fleet serves the panel from, so the row and the card cannot disagree —
        his complaint was that they did, two inches apart."""
        import console_doctor as cd
        import control_app as ca

        C = ca._FLEET_PRESENCE_CACHE
        keep = dict(C)
        try:
            now = time.time()
            GOOD = {"ok": True,
                    "online": [{"machine": "Dean"}, {"machine": "Konyo"}],
                    "offline": [{"machine": "Wife PC"}]}
            ERR = {"ok": False, "online": [], "offline": [],
                   "error": "<urlopen error _ssl.c:1112: The handshake operation timed out>"}

            C.update({"d": None, "t": 0.0, "goodD": None, "goodT": 0.0})
            st_never, why_never = cd._check_the_fleet_lane_is_reachable()
            self.assertEqual(st_never, cd.UNMEASURED,
                             "a console that has never asked must be UNMEASURED, not %r — "
                             "green here would mean the row reads well for the whole window in "
                             "which it is most blind" % st_never)

            C.update({"d": GOOD, "t": now - 3, "goodD": GOOD, "goodT": now - 3})
            st_ok, why_ok = cd._check_the_fleet_lane_is_reachable()
            self.assertEqual(st_ok, cd.OK, "a live roster must read OK, got %r (%s)"
                             % (st_ok, why_ok))
            # ⚠ THE COUNT, NOT THE SUBSTRING. "3" occurs in an age, a version and a timestamp;
            # asserting it appears somewhere would pass on any of them. [[zero-needs-a-denominator]]
            self.assertIn("2 online, 1 offline, 3 machine(s) known", why_ok,
                          "the OK line must publish the split AND the total, got: %s" % why_ok)

            C.update({"d": ERR, "t": now, "goodD": GOOD, "goodT": now - 412})
            st_deg, why_deg = cd._check_the_fleet_lane_is_reachable()
            self.assertEqual(st_deg, cd.MISSING,
                             "an unreachable fleet must NOT read ok — this is the exact state in "
                             "his 11:07 screenshot, and it read green because no row existed. "
                             "got %r (%s)" % (st_deg, why_deg))

            C.update({"d": ERR, "t": now, "goodD": None, "goodT": 0.0})
            st_bare, why_bare = cd._check_the_fleet_lane_is_reachable()
            self.assertEqual(st_bare, cd.MISSING,
                             "unreachable with nothing remembered must also be MISSING, got %r"
                             % st_bare)

            # the two failures are DIFFERENT facts: one can still render a stale list, one cannot.
            self.assertNotEqual(
                why_deg, why_bare,
                "unreachable-with-a-roster and unreachable-with-nothing must not share a "
                "sentence — the second is the only case with no honest fallback, and collapsing "
                "them hides it")
            self.assertEqual(len({st_never, st_ok}), 2,
                             "never-asked and reachable must not collapse to one state")
        finally:
            C.clear()
            C.update(keep)

    # ── LAW 3 — two questions, two answers, and the honesty law still holds ─────────────────
    def test_a_remembered_roster_never_becomes_a_claim_that_anyone_is_online(self):
        """v2814's defect, guarded from the other side. `ok` answers THE FETCH; last-good answers
        THE MEMORY. The panel may render the memory as stale, but the wire must never say online.
        [[unknown-stays-unknown]]"""
        import control_app as ca
        C = ca._FLEET_PRESENCE_CACHE
        keep = dict(C)
        try:
            now = time.time()
            GOOD = {"ok": True, "online": [{"machine": "Dean"}], "offline": [{"machine": "Wife PC"}]}
            ERR = {"ok": False, "online": [], "offline": [], "error": "handshake timed out"}
            C.update({"d": ERR, "t": now, "goodD": GOOD, "goodT": now - 300})

            lg, age = ca.fleet_presence_last_good()
            self.assertIsNotNone(lg, "the remembered roster must survive a failed fetch")
            self.assertEqual(len(lg.get("online") or []), 1,
                             "the remembered roster must keep its rows")
            self.assertIsInstance(age, float, "the memory must carry its AGE, not just its rows")
            self.assertGreater(age, 0.0, "a remembered roster with age 0 is indistinguishable "
                                         "from a live one")

            live = ca.fleet_presence()          # cached failure, must stay honest
            self.assertIs(live.get("ok"), False,
                          "the fetch verdict must stay False while the site is unreachable")
            self.assertEqual(len(live.get("online") or []), 0,
                             "an unreachable console must report ZERO online — %d is v2814's "
                             "defect returning" % len(live.get("online") or []))
        finally:
            C.clear()
            C.update(keep)

    # ── LAW 4 — the panel actually reads it, from a scope where the call resolves ───────────
    def test_the_panel_reads_the_remembered_roster_from_a_live_scope(self):
        """Two halves, and the gate fails on either. `grep -c lastGood` was 0 — the field existed
        and nothing consumed it. And a consumer declared in the wrong script block would throw at
        call time and paint the same blank card, passing every hand-check. [[the-unjoined-end]]"""
        p = os.path.join(HERE, "control_ui.html")
        with io.open(p, encoding="utf-8") as _fh:
            src = _fh.read()
        blocks = _blocks(src)
        self.assertGreaterEqual(len(blocks), 1, "control_ui.html has no script block at all")

        n_lastgood = len(re.findall(r"\.lastGood\b", src))
        self.assertGreaterEqual(
            n_lastgood, 1,
            "the panel must READ j.lastGood — it was shipped on the wire and consumed by nobody, "
            "which is why an unreachable console showed a blank instead of the roster it held. "
            "matches=%d" % n_lastgood)

        for helper in ("_fleetBlame", "_fleetAgo"):
            defs = [m.start() for m in re.finditer(r"var\s+%s\s*=" % helper, src)]
            calls = [m.start() for m in re.finditer(r"(?<![\w$])%s\s*\(" % helper, src)]
            calls = [c for c in calls if c not in defs]
            self.assertEqual(len(defs), 1,
                             "%s must be declared exactly once; found %d" % (helper, len(defs)))
            self.assertGreaterEqual(len(calls), 1,
                                    "%s is declared and never called — dead code in a panel that "
                                    "reported a blank card" % helper)
            dblk = _block_of(blocks, defs[0])
            for c in calls:
                cblk = _block_of(blocks, c)
                self.assertEqual(
                    cblk, dblk,
                    "%s is CALLED in script block %s but DECLARED in block %s. control_ui.html "
                    "has %d blocks and they do not share scope: this throws at call time and the "
                    "fleet panel paints nothing — the exact blank this task was opened to end, "
                    "and the fourth time this shape has shipped."
                    % (helper, cblk, dblk, len(blocks)))


    # ── LAW 5 — the WIRE between them, which nothing was guarding ──────────────────────────
    def test_the_handler_actually_puts_the_remembered_roster_on_the_wire(self):
        """★ THIS LAW EXISTS BECAUSE ITS OWN RED-PROOF CAME BACK BLIND.

        The first cut of this gate guarded both ENDS and neither noticed the middle. Law 3 proves
        `fleet_presence_last_good()` remembers; Law 4 proves `control_ui.html` reads `j.lastGood`.
        Heart 2.0 then renamed the assignment in the HTTP handler — the one line that carries the
        value from the first to the second — and all four tests stayed GREEN:

            test_the_fleet_lane_reaches_the_heart[2]  BLIND ← stayed GREEN through its own
                                                      defeat (1 match(es))

        A producer and a consumer both guarded, with an unguarded wire between them, is the very
        shape this whole task was opened about, one level up. The sabotage was correct and the law
        was absent. [[the-unjoined-end]] [[feedback-blind-fixture-green-gate]]

        ⚠ PARSED, NOT GREPPED. `lastGood` appears in prose in the comment block directly above the
        assignment, in `lastGoodWhy`, and in this file's own docstrings — a text search would go
        green on any of them while the wire stayed cut. This asks the AST for a real subscript
        STORE of the literal key. [[source-reading-guard]]
        """
        import ast
        p = os.path.join(HERE, "control_app.py")
        with io.open(p, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())

        stores = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            for tgt in node.targets:
                if (isinstance(tgt, ast.Subscript)
                        and isinstance(tgt.value, ast.Name)
                        and isinstance(tgt.slice, ast.Constant)
                        and tgt.slice.value == "lastGood"):
                    stores.append((tgt.value.id, getattr(node, "lineno", -1)))

        self.assertEqual(
            len(stores), 1,
            "exactly one place may store the remembered roster onto the fleet payload; the AST "
            "found %d. Without it the field never reaches the browser and the panel falls back to "
            "the blank card, while both ends of the join still test green. found=%r"
            % (len(stores), stores))

        # ⚠ AND ITS AGE TRAVELS WITH IT. A remembered roster with no age is indistinguishable from
        # a live one, which is the confusion the whole lastGood/ok split exists to prevent.
        ages = [t.slice.value
                for n in ast.walk(tree) if isinstance(n, ast.Assign)
                for t in n.targets
                if (isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name)
                    and isinstance(t.slice, ast.Constant) and t.slice.value == "lastGoodAgeS")]
        self.assertEqual(len(ages), 1,
                         "the remembered roster must ship its AGE alongside it; the AST found %d "
                         "assignment(s) of lastGoodAgeS" % len(ages))


# ══ THE EXECUTABLE RED-PROOFS ════════════════════════════════════════════════════════════════
# Heart 2.0 re-runs each of these in a sandbox and DISTRUSTS the law if it stays green. Each
# deletes the REAL thing the law is about, never a decoration beside it.
RED_PROOF = [
    {
        "why": "removing the CHECKS row returns the fleet to a lane the heart has never heard of "
               "— the original defect, verbatim",
        "file": "console_doctor.py",
        "find": '    ("fleet reachable", _check_the_fleet_lane_is_reachable),\n',
        "replace": "",
        "matches": 1,
    },
    {
        "why": "grading an unreachable fleet as OK is the green that lied on his screen",
        "file": "console_doctor.py",
        "find": '    why = str(last.get("error") or "no reason given")[:90]',
        "replace": '    return OK, "tampered"\n    why = str(last.get("error") or "no reason given")[:90]',
        "matches": 1,
    },
    {
        "why": "dropping lastGood from the wire is the unjoined end this task closed",
        "file": "control_app.py",
        "find": '                    _fl["lastGood"] = _lg',
        "replace": '                    _fl["_tamperedLastGood"] = _lg',
        "matches": 1,
    },
    {
        "why": "moving the helper out of the caller's script block is the dead render that has "
               "shipped four times; the panel goes blank and every hand-check passes",
        "file": "control_ui.html",
        "find": "  var _fleetBlame = function (raw) {",
        "replace": "  var _fleetBlameMOVED = function (raw) {",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
