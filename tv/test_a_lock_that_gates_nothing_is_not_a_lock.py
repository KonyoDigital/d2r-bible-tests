# -*- coding: utf-8 -*-
"""NINETEEN LOCKS SCORED, DISPLAYED, AND GATED NOTHING.

`self_arming.may(lock)` is the permission check. It was consulted at exactly THREE call sites in
the whole tree — `pixel_witness_wilson.py` and two in `control_app.py`, all three about
`console.pixel_rescue` — while nineteen locks computed Wilson scores, drew padlocks on the heart,
and stopped nothing. The arithmetic was real; the authority was imaginary.

⚠⚠ AND IT COULD NOT SIMPLY BE WIRED, WHICH IS WHY IT SAT THIS LONG. `may()` asks
`_heart_says_watched()` first, and that fails closed when the heart census is STALE — which it
becomes the moment any GATE FILE changes. Measured in one session of writing gates: the census
staled FOUR times and every lock answered may=False with a sentence about the census rather than
about itself. Wiring on top of that means editing a test takes features off his console until a
~38-minute re-prove. v3042's reversibility split is what made this safe: irreversible acts keep
the whole guarantee, ordinary ones refuse on MERIT alone.

THIS LAW PINS THE SEATS, one per lock, at the chokepoint a scouted pass found:

    printer.stream     tv/printer.py        stream()                 ordinary
    reel.route         tv/reel_route_lane   apply()                  ordinary
    vault.sweep_start  tv/control_app.py    chronicle_sweep_start()  DESTRUCTIVE
    prune.reports      tv/control_app.py    disk_history_append()    ordinary, CLAIM only

⚠ EACH SEAT IS THE ONE PLACE STATE CHANGES, not the place a decision is made. reel_router.route()
derives a station and writes nothing; the stamp happens only in apply(). plan() writes nothing.
A guard on a thought is not a guard.

⚠ AND `prune.reports` GATES THE CLAIM, NOT THE FUNCTION. self_arming's own note says it guards the
REPORT while prune.arm guards the deletion, so a row asserting "this much was freed" is gated and
a plain free-space reading is not — otherwise the lock would stop him seeing his own disk.

⚠ PARSED WITH ast, NEVER GREPPED: a lock named in a comment or a docstring must not satisfy a law
about whether the code ASKS. [[source-reading-guard]] [[the-unjoined-end]]
"""
import ast
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

#: lock -> (file, enclosing function, is_destructive)
SEATS = {
    "printer.stream":    ("printer.py",          "stream",                 False),
    "reel.route":        ("reel_route_lane.py",  "apply",                  False),
    "vault.sweep_start": ("control_app.py",      "chronicle_sweep_start",  True),
    "prune.reports":     ("control_app.py",      "disk_history_append",    False),
    "frame.release":     ("reel_retention.py",   "apply_plan",             True),
}


def _fn_node(path, name):
    try:
        tree = ast.parse(io.open(os.path.join(HERE, path), encoding="utf-8").read())
    except Exception:
        return None
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n
    return None


#: ⚠⚠ BOTH DOORS COUNT AS ASKING. v3052 added `self_arming.may_on_merit()` for surfaces that
#: SHOW rather than ACT, and moved `printer.stream()` onto it — because the old seat let nine
#: BLIND instruments, none of which watch the river, blank the river strip on his live console.
#: This reader only knew the name `may`, so from v3052 onward it reported `printer.stream` as a
#: lock "gating NOTHING" while the seat was right there being consulted. A law that pins the
#: SPELLING of a call rather than the fact of the call goes red on a correct fix.
#: [[label-outlived-referent]]
#: ⚠ It is not a loosening: may_on_merit REFUSES outright for any lock marked `destructive`, so a
#: seat on the vault, the prune or the frame release cannot satisfy this law through that door.
_ASK_FNS = ("may", "may_on_merit")


def _locks_asked_in(node):
    """Every lock name passed to a may(...) / may_on_merit(...) call in this function. -> set"""
    out = set()
    for c in ast.walk(node):
        if not isinstance(c, ast.Call):
            continue
        fname = getattr(c.func, "attr", None) or getattr(c.func, "id", None)
        if fname not in _ASK_FNS or not c.args:
            continue
        a0 = c.args[0]
        if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
            out.add(a0.value)
    return out


class TestALockThatGatesNothingIsNotALock(unittest.TestCase):

    def test_every_wired_lock_is_actually_asked_at_its_seat(self):
        """THE LAW. Parsed, so a mention in prose cannot satisfy it."""
        missing = []
        for lock, (path, fn, _d) in sorted(SEATS.items()):
            node = _fn_node(path, fn)
            if node is None:
                missing.append("%s: %s() not found in %s" % (lock, fn, path))
                continue
            if lock not in _locks_asked_in(node):
                missing.append("%s: %s() does not ask may(%r)" % (lock, fn, lock))
        self.assertEqual(
            missing, [],
            "%d lock(s) are declared, scored and drawn while gating NOTHING:\n  %s"
            % (len(missing), "\n  ".join(missing)))

    def test_the_seats_are_the_places_that_change_state(self):
        """A guard on a decision is not a guard. reel_router derives a station and writes nothing;
        the stamp happens in reel_route_lane.apply, which is where the seat is."""
        node = _fn_node("reel_router.py", "route")
        if node is not None:
            self.assertNotIn(
                "reel.route", _locks_asked_in(node),
                "reel_router.route() asks the lock, but it WRITES NOTHING — it derives a station. "
                "A refusal there stops a thought, not an act, while the real writer "
                "(reel_route_lane.apply) would stay open.")

    def test_prune_reports_gates_the_claim_and_not_the_reading(self):
        """It guards the REPORT; prune.arm guards the deletion. A guard on the whole function
        would stop him seeing his own free space."""
        node = _fn_node("control_app.py", "disk_history_append")
        self.assertIsNotNone(node, "disk_history_append is gone")
        src = ast.dump(node)
        self.assertIn("prune.reports", src, "disk_history_append no longer asks the lock")
        # the ask must sit under a test on the pruned figure, not at function entry
        # ⚠⚠ "INSIDE A CONDITIONAL" IS NOT ENOUGH, and heart2 proved it: the tamper turned
        # `if _pruned is not None:` into `if True:` and this law sailed straight through, because
        # `if True:` IS an If node. A guard whose condition is a constant gates everything, which
        # is the exact defect the tamper describes. The condition has to TEST THE CLAIM.
        # [[feedback-blind-fixture-green-gate]]
        tests_the_claim = False
        for n in ast.walk(node):
            if not isinstance(n, ast.If) or "prune.reports" not in ast.dump(n):
                continue
            names = {x.id for x in ast.walk(n.test) if isinstance(x, ast.Name)}
            if isinstance(n.test, ast.Constant):
                continue                      # `if True:` — a guard that guards nothing
            if names & {"_pruned", "pruned_mb"}:
                tests_the_claim = True
        self.assertTrue(
            tests_the_claim,
            "the prune.reports ask is not conditioned on the pruned figure. Either it is at "
            "function entry, or its condition is a constant — both gate EVERY row, including "
            "plain free-space readings that make no claim about what was freed, which is the one "
            "thing this lock was never about.")

    def test_the_deleter_is_gated_BEFORE_it_records_the_deletion(self):
        """v2069 writes the tombstone FIRST on purpose — a crash halfway then over-records rather
        than under-records. A refusal must therefore land before it, or a locked door writes a
        record for footage nobody touched and the ledger claims deletions that never happened."""
        node = _fn_node("reel_retention.py", "apply_plan")
        self.assertIsNotNone(node, "apply_plan is gone")
        ask = tomb = rm = None
        for n in ast.walk(node):
            if isinstance(n, ast.Call):
                nm = getattr(n.func, "attr", None) or getattr(n.func, "id", None)
                if nm == "may" and ask is None:
                    ask = n.lineno
                if nm == "_tombstone" and tomb is None:
                    tomb = n.lineno
                if nm == "rmtree" and rm is None:
                    rm = n.lineno
        self.assertIsNotNone(ask, "apply_plan does not ask may() at all — the deleter is ungated")
        self.assertIsNotNone(rm, "apply_plan no longer deletes; this law is reading the wrong thing")
        # ⚠⚠ ASKING IS NOT REFUSING, and heart2 proved it: a tamper that wrapped the refusal in
        # `if False:` left the may() call exactly where it was, so an order-only check sailed
        # through while the guard could no longer stop anything. What must precede the tombstone
        # is a REACHABLE RETURN, not a question. [[feedback-blind-fixture-green-gate]]
        refusal = None
        for n in ast.walk(node):
            if not isinstance(n, ast.If):
                continue
            if isinstance(n.test, ast.Constant) and not n.test.value:
                continue                       # `if False:` — dead code, guards nothing
            dump = ast.dump(n)
            if "frame.release is LOCKED" not in dump:
                continue
            if any(isinstance(x, ast.Return) for x in ast.walk(n)):
                refusal = n.lineno if refusal is None else min(refusal, n.lineno)
        self.assertIsNotNone(
            refusal,
            "apply_plan asks may() but no REACHABLE refusal returns on it. A guard that asks and "
            "carries on is not a guard — the rmtree below runs either way.")
        if tomb is not None:
            self.assertLess(refusal, tomb,
                            "the refusal returns at line %s, AFTER the tombstone at %s — a locked "
                            "door would record a deletion it never made" % (refusal, tomb))
        self.assertLess(refusal, rm,
                        "the refusal returns at line %s, AFTER the rmtree at %s" % (refusal, rm))

    def test_a_destructive_seat_refuses_without_the_busy_shape(self):
        """vault.sweep_start's refusal must not wear `busy`: callers treat that as contention and
        RETRY, so a locked door in that shape is retried forever."""
        node = _fn_node("control_app.py", "chronicle_sweep_start")
        self.assertIsNotNone(node, "chronicle_sweep_start is gone")
        for n in ast.walk(node):
            if not isinstance(n, ast.If) or "vault.sweep_start" not in ast.dump(n):
                continue
            self.assertNotIn(
                '"busy"', ast.dump(n),
                "the vault.sweep_start refusal carries a `busy` key. Callers retry on busy, so a "
                "locked door would be retried forever instead of reported.")


RED_PROOF = [
    {
        "why": "moves the frame.release refusal AFTER the tombstone, so a locked door still "
               "records a deletion it never made — v2069 writes the record first on purpose, and "
               "a guard behind it would make the ledger claim footage that was never touched",
        "file": "reel_retention.py",
        "find": '        return {"ok": False, "why": "frame.release is LOCKED',
        "replace": '        pass\n    if False:\n        return {"ok": False, "why": "frame.release is LOCKED',
        "matches": 1,
    },
    {
        "why": "removes the seat from the one place reels are stamped, so reel.route scores and "
               "draws a padlock while gating nothing — the state this whole law exists to end",
        "file": "reel_route_lane.py",
        "find": '        _ok, _lw = _sa.may("reel.route")',
        "replace": '        _ok, _lw = True, "ungated"',
        "matches": 1,
    },
    {
        "why": "moves the prune.reports ask out from under the claim test, so it gates every row "
               "and a plain free-space reading is refused along with the claim",
        "file": "control_app.py",
        "find": "    if _pruned is not None:\n        try:\n            import self_arming as _sa_pr",
        "replace": "    if True:\n        try:\n            import self_arming as _sa_pr",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
