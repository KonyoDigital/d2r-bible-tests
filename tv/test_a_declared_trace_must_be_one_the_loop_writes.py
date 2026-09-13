# -*- coding: utf-8 -*-
"""A LOOP DECLARED TO LEAVE A TRACE MUST ACTUALLY WRITE THE FILE THAT WAS DECLARED.

v3076 gave four loops a second witness by having each record WHAT IT DECIDED through
`lane_trace`, taking ALL FOUR organs from 9 surfaces to 12. Every one of those cells is a
DECLARATION in `loop_corroborate.LOOPS`, and a declaration with nothing behind it is precisely
the coverage v3055 deleted — a resolver that matched on name tails and invented eight cells.

⚠⚠ AND THE FAILURE WOULD BE SILENT. If a declared path and the path `lane_trace` actually writes
ever disagree by one character, `_trace_age` finds no artefact and the row returns **UNKNOWN** for
ever. UNKNOWN is not a red light anywhere — it reads as "not measured yet" — so the organ would
sit there looking reasonable while corroborating nothing at all. A typo would cost a whole column
and announce nothing. [[the-unjoined-end]] [[unknown-stays-unknown]]

So this pins the JOIN from both ends:
  · every lane declared under `.lane_trace/` is one some loop really calls, found by PARSING
    control_app.py rather than by matching a string that might sit in a comment
  · the declared path is EXACTLY `lane_trace.path_of(lane)` — computed, never re-typed
  · the declared period is never SHORTER than the writer's own throttle, or a correctly working
    loop reads as stale inside one window [[feedback-threshold-above-the-ceiling]]
"""
import ast
import io
import os
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))


def _calls(src):
    """Every lane_trace note/note_dormant call, as (func, lane, kwargs). -> list

    PARSED, not grepped: the word `note('tvd-version-drift')` appears in prose in this repo, and a
    law that reads source must not be satisfiable by a comment. [[source-reading-guard]]
    """
    out = []
    for n in ast.walk(ast.parse(src)):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
        if name not in ("note", "note_dormant"):
            continue
        if isinstance(f, ast.Attribute) and not (
                isinstance(f.value, ast.Name) and "lt" in f.value.id.lower()):
            continue
        if not n.args or not isinstance(n.args[0], ast.Constant):
            continue
        kw = {k.arg: k.value for k in n.keywords if k.arg}
        out.append((name, n.args[0].value, kw))
    return out


class TestADeclaredTraceMustBeOneTheLoopWrites(unittest.TestCase):

    def setUp(self):
        import loop_corroborate as LC
        import lane_trace as LT
        self.LC, self.LT = LC, LT
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            self.calls = _calls(fh.read())
        self.declared = {v: (lane, pat, every) for v, (lane, pat, every) in LC.LOOPS.items()
                         if os.path.join(HERE, ".lane_trace") in pat}

    def test_every_declared_lane_is_written_by_a_real_call(self):
        lanes = {lane for _f, lane, _k in self.calls}
        print("lane_trace calls parsed out of control_app.py: %d -> %s"
              % (len(self.calls), sorted(lanes)))
        self.assertGreaterEqual(len(self.calls), 4,
                                "only %d lane_trace call(s) parsed — if the calls moved, this "
                                "guard is measuring nothing" % len(self.calls))
        self.assertTrue(self.declared, "no loop declares a .lane_trace artefact — nothing to check")
        for vessel, (lane, _pat, _every) in sorted(self.declared.items()):
            self.assertIn(lane, lanes,
                          "%s declares lane %r but NOTHING in control_app.py writes it — the row "
                          "would read UNKNOWN for ever, which is invisible, not red"
                          % (vessel, lane))

    def test_the_declared_path_is_the_one_lane_trace_writes(self):
        for vessel, (lane, pat, _every) in sorted(self.declared.items()):
            self.assertEqual(os.path.abspath(pat), os.path.abspath(self.LT.path_of(lane)),
                             "%s declares a trace path that lane_trace would never write. One "
                             "character apart is a permanent UNKNOWN, not an error anyone sees"
                             % vessel)
        print("declared paths match lane_trace.path_of for all %d lane(s)" % len(self.declared))

    def test_a_declared_period_is_never_shorter_than_the_loops_own_tick(self):
        """The hole the second eye found in the test BELOW this one.

        The throttle check only inspects `min_gap_s=`. `_drift_loop` has no throttle — it writes
        once per cycle — so its trace period is its TICK period, `_DRIFT_EVERY_S`, which defaults
        to 300. It was declared at 30, making the stale window 30*6 = 180s, and a perfectly healthy
        console read DISAGREE ("running and producing nothing") for the last ~120s of every
        5-minute cycle, flapping for ever. A writer with no throttle was invisible to the guard.
        """
        import ast as _ast
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            tree = _ast.parse(fh.read())
        consts = {}
        for n in tree.body:
            if (isinstance(n, _ast.Assign) and len(n.targets) == 1
                    and getattr(n.targets[0], "id", None)):
                v = n.value
                if isinstance(v, _ast.Constant) and isinstance(v.value, (int, float)):
                    consts[n.targets[0].id] = float(v.value)
                elif isinstance(v, _ast.Call):          # float(os.environ.get(..., "300") or 300)
                    for a in list(v.args) + [k.value for k in v.keywords]:
                        if isinstance(a, _ast.BoolOp):
                            for vv in a.values:
                                if isinstance(vv, _ast.Constant) and isinstance(vv.value, (int, float)):
                                    consts[n.targets[0].id] = float(vv.value)
        ticks = {}
        for n in _ast.walk(tree):
            if (isinstance(n, _ast.Call)
                    and getattr(n.func, "id", getattr(n.func, "attr", None)) == "_lane_tick"
                    and len(n.args) >= 2 and isinstance(n.args[0], _ast.Constant)):
                a = n.args[1]
                if isinstance(a, _ast.Constant) and isinstance(a.value, (int, float)):
                    ticks[n.args[0].value] = float(a.value)
                elif isinstance(a, _ast.Name) and a.id in consts:
                    ticks[n.args[0].value] = consts[a.id]
        print("tick periods parsed: %s" % {k: v for k, v in sorted(ticks.items())})
        self.assertTrue(ticks, "no _lane_tick period could be resolved — measuring nothing")
        for vessel, (lane, _pat, every) in sorted(self.declared.items()):
            t = ticks.get(lane)
            if t is None:
                continue                      # UNKNOWN period, not a violation
            self.assertGreaterEqual(
                float(every), t,
                "%s ticks every %.0fs but declares a %.0fs trace period — its trace can only be as "
                "fresh as its tick, so a healthy loop would read DISAGREE inside one stale window"
                % (vessel, t, every))

    def test_a_declared_period_is_never_shorter_than_the_writers_throttle(self):
        throttle = {}
        for _f, lane, kw in self.calls:
            v = kw.get("min_gap_s")
            if isinstance(v, ast.Constant) and isinstance(v.value, (int, float)):
                throttle[lane] = max(throttle.get(lane, 0.0), float(v.value))
        print("throttles found: %s" % throttle)
        for vessel, (lane, _pat, every) in sorted(self.declared.items()):
            g = throttle.get(lane)
            if g:
                self.assertGreaterEqual(
                    float(every), g,
                    "%s writes at most every %.0fs but declares a %.0fs period — a correctly "
                    "throttled loop would read as stale" % (vessel, g, every))

    def test_surfaces_and_loops_never_drift_apart(self):
        self.assertEqual(sorted(self.LC.SURFACES), sorted(self.LC.LOOPS),
                         "a surface with no LOOPS entry claims an organ nothing can produce; a "
                         "LOOPS entry with no surface is work the census never counts")

    def test_a_dormant_lane_agrees_with_an_absent_tick(self):
        """The case that made his healthiest console read as broken."""
        LC = self.LC
        lane, pat = "gate-dormant-lane", self.LT.path_of("gate-dormant-lane")
        loops = {"gate-dormant": (lane, pat, 30.0)}
        self.assertTrue(self.LT.note_dormant(lane, "no parent pid, by design"))
        try:
            _real = LC._tick_age
            LC._tick_age = lambda _l: None                 # nothing ticked — dormant means that
            row = LC.corroborate(loops)["rows"][0]
            print("dormant + no tick -> %s (%s)" % (row["verdict"], row["why"][:70]))
            self.assertEqual(row["verdict"], "AGREE",
                             "a lane that declared DORMANT and did not tick has TWO witnesses "
                             "agreeing — calling that a failure invents an alarm about a healthy "
                             "machine")
            LC._tick_age = lambda _l: 1.0                  # ...but it IS ticking: a contradiction
            row = LC.corroborate(loops)["rows"][0]
            print("dormant + live tick -> %s" % row["verdict"])
            self.assertEqual(row["verdict"], "DISAGREE",
                             "a lane running while declaring itself dormant is the real defect")
        finally:
            LC._tick_age = _real
            try:
                os.remove(pat)
            except OSError:
                pass


RED_PROOF = [
    {
        # ⚠ THIS TAMPERS THE SOURCE, NOT THE TEST. The first cut edited the assertion in this very
        # file and heart2 called it INVALID at 2 matches — a RED_PROOF's `find` string necessarily
        # appears in the file twice, once in the code and once in the proof itself, so a proof can
        # never anchor on its own test body. Sabotaging the DECLARATION is also the truer drill:
        # it deletes the real thing (a correct path) rather than disabling the check.
        "why": "a declared trace path stops being the one lane_trace actually writes — exactly the "
               "one-character typo that makes the row UNKNOWN for ever while the census goes on "
               "counting the organ as COVERED, with nothing anywhere showing red",
        "file": "loop_corroborate.py",
        "find": 'os.path.join(HERE, ".lane_trace", "tvd-version-drift.json"), 300.0),',
        "replace": 'os.path.join(HERE, ".lane_trace", "tvd-version-drfit.json"), 300.0),',
        "matches": 1,
    },
    {
        "why": "a dormant lane stops agreeing with an absent tick, so `_orphan_exit_loop` — which "
               "is ALWAYS dormant on his own console — reports his healthiest machine as carrying "
               "a dead loop",
        "file": "loop_corroborate.py",
        "find": "        if _state == \"DORMANT\":",
        "replace": "        if False:",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
