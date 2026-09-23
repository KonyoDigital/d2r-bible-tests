# -*- coding: utf-8 -*-
"""A FASTER PROVE THAT CHANGES ONE VERDICT IS NOT A SPEEDUP, IT IS A BROKEN GATE.

`heart2.py --prove` was doubly serial — per gate, then per proof — and one proof is "sabotage a
file → run that gate in a subprocess → restore". MEASURED on his pushes: that step was ~24 min of
a 38m42s push and ~26 min of a 41m25s one, 60%+ of every push, with ONE child process alive at a
time and load ~2.2 on a 10-core machine. It was never CPU-bound; it was serialised, and it grows
with every law added.

⚠⚠⚠ THE OBVIOUS SPLIT — one worker per GATE inside ONE SHARED sandbox — IS UNSAFE, and the
measurement is what says so. Taken 2026-09-23 over the whole registry:

    537 gate files readable · 497 declare a red-proof · 1,302 declared proofs
    149 distinct tampered files once resolved · 67 of them claimed by MORE THAN ONE gate
    446 of 497 gates (90%) tamper a file that another gate also tampers
    control_app.py alone: 124 gates tamper it, and a further 110 gates NAME it without
    tampering it — so they would read a neighbour's sabotage and go red for it

Two lanes in one sandbox is a false verdict in BOTH directions. A neighbour's sabotage reddens an
innocent gate, which then reports UNPROVABLE — "it is ALREADY RED untampered" — a sentence that
would simply be untrue. And a neighbour's restore can hand a gate CLEAN bytes at the moment it is
supposed to be judging tampered ones, which reads as PROVEN: a gate credited with catching a
defect it was never shown. Grouping by tampered FILE does not fix it either, because a gate reads
far more than it tampers; that is what the 110 measures.

So the shape is ONE THROWAWAY SANDBOX PER LANE, gates pulled from a shared queue, every proof of
one gate run serially inside the single lane that owns it. This file is the law that the shape
survives: the lanes and the old serial loop must return the SAME verdicts, proof by proof — not
merely "both green" — every gate must come back with a row even when its lane dies, and the
subject file must be byte-exact afterwards, including when the run raises.

⚠ THE SCAR THIS RUNS TOWARD: test_control takes 19.5s idle and 565.9s under concurrent load, a
29x slowdown that once produced a FALSE RED and refused a legitimate push. Parallel proving
manufactures that load on purpose, so the lane count is a named constant that can be turned DOWN
with HEART2_PROVE_WORKERS and never requires an edit on a machine that is already struggling.

[[the-unjoined-end]] [[unknown-stays-unknown]] [[zero-needs-a-denominator]] [[regression-guard]]
"""
import hashlib
import io
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import heart2 as H  # noqa: E402


def _quiet(*_a, **_k):
    pass


# ── fixtures ─────────────────────────────────────────────────────────────────────────────────
def _fixture_gates(n_gates=9):
    """A fake `have` list: [(name, filename, [proof, ...])] with a varying proof count.

    The proofs are opaque to the dispatcher — only `len()` of them is read there and by the fake
    prover — so the fixture exercises the dispatch and never the tamper logic, which has its own
    law further down against a REAL sandbox.
    """
    out = []
    for i in range(n_gates):
        k = 1 + (i % 4)
        out.append(("gate-%02d" % i, "test_gate_%02d.py" % i,
                    [{"file": "subject.py", "find": "x", "replace": "y", "matches": 1}] * k))
    return out


_VERDICT_CYCLE = (H.PROVEN, H.PROVEN, H.BLIND, H.PROVEN, H.UNPROVABLE, H.PROVEN, H.INVALID)


def _verdict_for(name, idx):
    """A DETERMINISTIC verdict per (gate, proof index) — the same answer in either path.

    ⚠ It has to cover more than PROVEN, or the comparison would only ever be green-against-green
    and could not see a roll-up that reordered its own precedence. [[regression-guard]]
    """
    return _VERDICT_CYCLE[(sum(ord(c) for c in name) + idx) % len(_VERDICT_CYCLE)]


class _Recorder(object):
    """Who proved what, where, and on which thread."""

    def __init__(self, raise_on=None, dwell=0.02):
        self.calls, self.lock, self.raise_on, self.dwell = [], threading.Lock(), raise_on, dwell

    def prove_one(self, sandbox, name, filename, pr, idx, say):
        time.sleep(self.dwell)          # long enough for lanes to genuinely overlap
        with self.lock:
            self.calls.append({"name": name, "idx": idx, "sandbox": sandbox,
                               "thread": threading.current_thread().ident})
        if self.raise_on and name == self.raise_on:
            raise RuntimeError("a deliberately exploding proof")
        return _verdict_for(name, idx)


class _Sandboxes(object):
    """make_sandbox stand-in — a REAL directory per call, so cleanup can be checked on disk."""

    def __init__(self):
        self.made, self.lock = [], threading.Lock()

    def make(self, say=print):
        root = tempfile.mkdtemp(prefix="h2lanelaw.")
        tv = os.path.join(root, "repo", "tv")
        os.makedirs(tv)
        with io.open(os.path.join(tv, "control_app.py"), "w", encoding="utf-8") as fh:
            fh.write("# a sandbox marker, so the directory is not merely empty\n")
        with self.lock:
            self.made.append((tv, root))
        return tv, root


class _Patch(object):
    """Swap module globals and always put them back."""

    def __init__(self, **kw):
        self.kw, self.old = kw, {}

    def __enter__(self):
        for k, v in self.kw.items():
            self.old[k] = getattr(H, k)
            setattr(H, k, v)
        return self

    def __exit__(self, *_e):
        for k, v in self.old.items():
            setattr(H, k, v)
        return False


class _Env(object):
    def __init__(self, **kw):
        self.kw, self.old = kw, {}

    def __enter__(self):
        for k, v in self.kw.items():
            self.old[k] = os.environ.get(k)
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return self

    def __exit__(self, *_e):
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return False


# ── the laws ─────────────────────────────────────────────────────────────────────────────────
class LanesAgreeWithTheSerialLoop(unittest.TestCase):

    def _run(self, have, workers, raise_on=None):
        rec, sbs = _Recorder(raise_on=raise_on), _Sandboxes()
        with _Patch(make_sandbox=sbs.make, _prove_one=rec.prove_one):
            res, det = H._prove_gates(have, say=_quiet, workers=workers)
        return res, det, rec, sbs

    def test_the_lanes_return_the_same_verdicts_proof_by_proof(self):
        """⚠ "BOTH GREEN" IS NOT "THE SAME ANSWER", AND ONLY ONE OF THEM IS THE SAFETY CLAIM.

        The whole risk of proving in parallel is a verdict that MOVES — a gate credited PROVEN
        because a neighbour restored the bytes it was supposed to be judging, or reported
        UNPROVABLE because a neighbour's sabotage reddened it. Comparing pass/fail cannot see
        either one. This compares the per-PROOF verdict lists, in order, and the per-gate roll-up.
        """
        have = _fixture_gates()
        total = sum(len(p) for _n, _f, p in have)

        res_s, det_s, rec_s, sb_s = self._run(have, 1)
        res_p, det_p, rec_p, sb_p = self._run(have, 4)

        # ── THE PREMISES FIRST. A comparison of two runs that did not happen is green for free.
        self.assertEqual(len(rec_s.calls), total,
                         "the SERIAL leg proved %d of %d declared proofs, so the comparison below "
                         "is about a run that did not happen" % (len(rec_s.calls), total))
        self.assertEqual(len(rec_p.calls), total,
                         "the PARALLEL leg proved %d of %d declared proofs — a faster run that "
                         "skipped work is not a speedup" % (len(rec_p.calls), total))
        self.assertEqual(len(sb_s.made), 1,
                         "the one-lane path built %d sandboxes; it is supposed to be exactly the "
                         "old single-sandbox loop" % len(sb_s.made))
        self.assertGreaterEqual(
            len(sb_p.made), 2,
            "the PARALLEL leg built %d sandbox(es) — it ran as one lane, so this law compared the "
            "serial loop against itself and would stay green over any concurrency defect"
            % len(sb_p.made))
        self.assertGreaterEqual(
            len(set(c["thread"] for c in rec_p.calls)), 2,
            "every proof in the PARALLEL leg ran on ONE thread, so nothing was actually proved "
            "concurrently and this comparison is vacuous")

        # ── AND NOW THE CLAIM.
        self.assertEqual(res_s, res_p,
                         "the per-gate verdicts differ between one lane and four:\n  serial:   %r\n"
                         "  parallel: %r" % (sorted(res_s.items()), sorted(res_p.items())))
        self.assertEqual(det_s, det_p,
                         "the per-PROOF verdicts differ between one lane and four:\n  serial:   %r"
                         "\n  parallel: %r" % (sorted(det_s.items()), sorted(det_p.items())))
        for name, _fn, proofs in have:
            self.assertEqual(det_p.get(name), [_verdict_for(name, i) for i in range(len(proofs))],
                             "%s came back with verdicts the fixture did not produce" % name)

    def test_a_gate_is_proved_inside_one_sandbox_and_never_a_neighbours(self):
        """⚠⚠ THE COLLISION IS THE WHOLE REASON THIS IS NOT A PER-GATE SPLIT. 446 of 497 gates
        tamper a file another gate also tampers; control_app.py is tampered by 124 of them and
        read by 110 more. Two lanes sharing one sandbox is a lost update between sabotages, and
        it produces confident wrong verdicts in both directions. This law is what a future
        "let's build one sandbox, it is faster" has to get past.
        """
        have = _fixture_gates()
        res, _det, rec, sbs = self._run(have, 4)

        self.assertGreaterEqual(len(sbs.made), 2, "only one sandbox was built — nothing to isolate")
        self.assertEqual(len(rec.calls), sum(len(p) for _n, _f, p in have))

        paths = [tv for tv, _root in sbs.made]
        self.assertEqual(len(set(paths)), len(paths),
                         "two lanes were handed the SAME sandbox path (%r) — their sabotages land "
                         "on one another's subject files" % paths)
        by_gate = {}
        for c in rec.calls:
            by_gate.setdefault(c["name"], set()).add(c["sandbox"])
        for name, boxes in sorted(by_gate.items()):
            self.assertEqual(len(boxes), 1,
                             "%s had its proofs applied in %d different sandboxes (%r) — the "
                             "restore of one proof would not undo the tamper of the next"
                             % (name, len(boxes), sorted(boxes)))
        for c in rec.calls:
            self.assertIn(c["sandbox"], set(paths),
                          "a proof ran somewhere that is not one of the sandboxes this run built "
                          "(%r) — the real tree is one such place" % c["sandbox"])
        self.assertEqual(set(res), set(n for n, _f, _p in have))

    def test_a_proof_that_explodes_is_blind_and_the_run_carries_on(self):
        """v3292's scar, kept alive across the restructure: an inert or exploding red-proof may
        never report success, and it may never take the run with it either. A swallowed exception
        would leave the gate ABSENT from the census, which reads as nothing to see.
        """
        have = _fixture_gates()
        res, det, rec, sbs = self._run(have, 4, raise_on="gate-03")

        self.assertTrue(any(c["name"] == "gate-03" for c in rec.calls),
                        "the exploding gate was never reached, so this law proved nothing")
        self.assertEqual(set(res), set(n for n, _f, _p in have),
                         "a gate vanished from the results when a proof raised")
        self.assertEqual(res.get("gate-03"), H.BLIND,
                         "a proof that RAISED came back %r — an error is not a demonstration"
                         % res.get("gate-03"))
        self.assertEqual(det.get("gate-03"), [H.BLIND] * len(have[3][2]))
        code, broken, _idle = H.prove_exit_code(res)
        self.assertEqual(code, 1, "a run containing a raising proof exited 0")
        self.assertIn("gate-03", broken)
        for name, _fn, proofs in have:
            if name == "gate-03":
                continue
            self.assertEqual(det.get(name), [_verdict_for(name, i) for i in range(len(proofs))],
                             "%s's verdicts changed because a DIFFERENT gate raised" % name)
        for _tv, root in sbs.made:
            self.assertFalse(os.path.exists(root),
                             "a lane left its sandbox %r behind after a proof raised — each one "
                             "is ~384 MB of real disk" % root)

    def test_no_gate_may_vanish_when_a_lane_never_reaches_it(self):
        """⚠ AN ABSENT ROW READS AS "NOTHING TO SEE", AND THIS FILE'S WHOLE PREMISE FORBIDS THAT.
        v2882 already cost the heart a "0 blind of 278" that was really 279 gates with one never
        asked about. A lane that dies holding work must not shorten the census.
        """
        have = _fixture_gates(6)
        drained = {"n": 0}

        def _lazy_lane(lane, work, out, lock, sink, built, buffered=True):
            built.append(True)
            try:
                name, _fn, proofs = work.get_nowait()
            except Exception:
                return
            with lock:
                out[name] = (H.PROVEN, [H.PROVEN] * len(proofs))
                drained["n"] += 1

        with _Patch(_prove_lane=_lazy_lane):
            res, det = H._prove_gates(have, say=_quiet, workers=2)

        self.assertGreaterEqual(drained["n"], 1, "no lane ran at all, so nothing was left behind")
        self.assertLess(drained["n"], len(have),
                        "every gate was drained, so no row was missing and the sweep this law "
                        "exists for was never exercised")
        self.assertEqual(set(res), set(n for n, _f, _p in have),
                         "%d of %d gates vanished from the results" % (len(have) - len(res),
                                                                       len(have)))
        for name, _fn, proofs in have:
            self.assertEqual(len(det.get(name) or []), len(proofs),
                             "%s came back with a per-proof list of the wrong length" % name)
        code, _broken, _idle = H.prove_exit_code(res)
        self.assertEqual(code, 1,
                         "gates nobody reached were filled in with something that exits 0 — an "
                         "unproven law reported as a clean one")

    def test_no_lane_means_nothing_proved_rather_than_everything_clean(self):
        """make_sandbox refuses below 4 GB free and when safe_copy declines. The old loop returned
        {} and banked no state; the lanes must reach the same answer rather than inventing rows.
        """
        have = _fixture_gates(4)
        with _Patch(make_sandbox=lambda say=print: (None, None)):
            res, det = H._prove_gates(have, say=_quiet, workers=3)
        self.assertIsNone(res, "a run with NO sandbox returned verdicts: %r" % (res,))
        self.assertIsNone(det)


class TheLaneCountIsMeasuredAndTurnableDown(unittest.TestCase):

    def test_the_lane_count_can_be_turned_down_without_an_edit(self):
        """⚠ THE REASON TO TURN IT DOWN IS A MACHINE THAT IS ALREADY LOADED — the condition under
        which editing a file and re-running is worst. test_control takes 19.5s idle and 565.9s
        under concurrent load; the escape hatch is the difference between a false red and a push.
        """
        with _Env(HEART2_PROVE_WORKERS="1"):
            self.assertEqual(H.prove_workers(50), 1,
                             "HEART2_PROVE_WORKERS=1 did not give the single-lane loop back")
        with _Env(HEART2_PROVE_WORKERS="0"):
            self.assertEqual(H.prove_workers(50), 1, "a lane count below 1 must floor at 1, never 0")
        with _Env(HEART2_PROVE_WORKERS="-4"):
            self.assertEqual(H.prove_workers(50), 1)
        with _Env(HEART2_PROVE_WORKERS="not-a-number"):
            n = H.prove_workers(50)
            # a disk cap may legitimately reduce it, so the bound is one-sided ON PURPOSE: a law
            # that demanded the exact default would cry wolf on a full machine, and a row that
            # cries wolf gets silenced. [[a-gate-can-perturb-what-it-measures]]
            self.assertTrue(1 <= n <= H.PROVE_WORKERS,
                            "an unreadable HEART2_PROVE_WORKERS gave %r rather than falling back "
                            "inside 1..%d" % (n, H.PROVE_WORKERS))
        with _Env(HEART2_PROVE_WORKERS=None):
            self.assertEqual(H.prove_workers(1), 1,
                             "one gate in scope must never build more than one sandbox")
            self.assertTrue(1 <= H.prove_workers(50) <= H.PROVE_WORKERS)

    def test_the_setting_actually_reaches_the_lanes(self):
        """⚠ PLUMBING WITH NO TAP IS THIS REPO'S MOST REPEATED DEFECT. A constant nothing consults
        and an env var nothing reads would both read exactly like a working dial.
        """
        have = _fixture_gates(6)
        with _Env(HEART2_PROVE_WORKERS="1"):
            sbs, rec = _Sandboxes(), _Recorder(dwell=0)
            with _Patch(make_sandbox=sbs.make, _prove_one=rec.prove_one):
                H._prove_gates(have, say=_quiet)         # workers=None -> ask prove_workers()
            self.assertEqual(len(sbs.made), 1,
                             "HEART2_PROVE_WORKERS=1 still built %d sandboxes, so the dial is not "
                             "joined to the lanes" % len(sbs.made))
            self.assertEqual(len(rec.calls), sum(len(p) for _n, _f, p in have))
        with _Env(HEART2_PROVE_WORKERS="3"):
            want = H.prove_workers(len(have))
            sbs, rec = _Sandboxes(), _Recorder(dwell=0)
            with _Patch(make_sandbox=sbs.make, _prove_one=rec.prove_one):
                H._prove_gates(have, say=_quiet)
            self.assertEqual(len(sbs.made), want,
                             "prove_workers() chose %d lane(s) and %d sandbox(es) were built"
                             % (want, len(sbs.made)))


class TheDeadlineGrowsWithTheLoadTheLanesMake(unittest.TestCase):
    """⚠⚠ THE ONE THING THE A/B FOUND, AND IT WAS NOT A LOST UPDATE.

    Proving the same 25 gates (74 proofs) inside a FROZEN copy of the tree — serial versus lanes,
    one snapshot so four other agents editing this tree could not move the bytes underneath:

        serial 1 lane   cold 766.6s · warm 606.3s      2 lanes 286.3s      4 lanes 258.4s
        25 of 25 GATE verdicts identical at every lane count
        0 bytes of tree drift in all four legs (sha256 over every .py/.html/.js, before and after)
        73 of 74 PROOF verdicts identical — and ONE flipped:
            test_a_cached_absence_is_not_an_absence[0]   PROVEN -> UNPROVABLE

    Nothing was corrupted. That gate's CLEAN run takes ~110s against a registered timeout of 120s;
    the SERIAL control measured 230.3s for its clean+tampered pair and already reported its OTHER
    proof UNPROVABLE for the identical timeout reason. It sits on its own deadline, serially, and
    any load tips it. A smaller lane count does not help — 2 lanes flips the same proof, measured.

    ⚠ AND THE FLIP IS NOT HARMLESS: UNPROVABLE makes _write_state DISCARD a standing proof, so a
    deadline expiring because of this prover's own concurrency would quietly delete a proof the
    heart had banked. [[unknown-stays-unknown]] [[label-outlived-referent]]
    """

    def test_the_allowance_is_on_for_lanes_and_off_for_one_lane(self):
        seen = []

        def _watch(sandbox, name, filename, pr, idx, say):
            seen.append(H.DEADLINE_SCALE)
            return H.PROVEN

        have = _fixture_gates(6)
        sbs = _Sandboxes()
        with _Patch(make_sandbox=sbs.make, _prove_one=_watch):
            H._prove_gates(have, say=_quiet, workers=1)
            self.assertTrue(seen, "no proof ran on the single-lane path")
            self.assertEqual(set(seen), {1},
                             "the single-lane path widened its deadline to %r — that path is "
                             "offered as the old loop UNCHANGED" % sorted(set(seen)))
            seen[:] = []
            H._prove_gates(have, say=_quiet, workers=3)
            self.assertTrue(seen, "no proof ran on the lane path")
            self.assertEqual(set(seen), {H.LANE_DEADLINE_SCALE},
                             "with 3 lanes running the deadline allowance read %r rather than x%d, "
                             "so a verdict is still decided by how busy this prover is"
                             % (sorted(set(seen)), H.LANE_DEADLINE_SCALE))
        self.assertEqual(H.DEADLINE_SCALE, 1,
                         "the allowance was left at %r after the run — a module global that does "
                         "not spring back silently widens every later serial deadline in this "
                         "process, and control_app.py keeps this module loaded" % H.DEADLINE_SCALE)

    def test_the_allowance_reaches_the_deadline_the_gate_is_actually_given(self):
        """⚠ A CONSTANT NOTHING MULTIPLIES IN READS EXACTLY LIKE A WORKING ONE. This drives the
        REAL _prove_one and reads the timeout it hands _run_gate. [[plumbing-with-no-tap]]
        """
        root = tempfile.mkdtemp(prefix="h2deadline.")
        self.addCleanup(shutil.rmtree, root, True)
        tv = os.path.join(root, "repo", "tv")
        os.makedirs(tv)
        with io.open(os.path.join(tv, "subject.py"), "w", encoding="utf-8") as fh:
            fh.write('MODE = "GOOD"\n')
        with io.open(os.path.join(tv, "fake_gate.py"), "w", encoding="utf-8") as fh:
            fh.write("import sys\nsys.exit(0)\n")
        proof = {"file": "subject.py", "find": 'MODE = "GOOD"', "replace": 'MODE = "BAD"',
                 "matches": 1, "why": "x"}
        seen = []

        def _spy(sandbox_tv, filename, timeout=180, extra=(), script=None):
            seen.append(timeout)
            return (True, "Ran 1 test | OK") if len(seen) == 1 else (False, "Ran 1 test | FAILED")

        registered = H.gate_spec("no-such-registered-gate")[1]
        self.assertTrue(registered and registered > 0,
                        "gate_spec handed back %r as a timeout, so there is no baseline to scale "
                        "and this law would compare two guesses" % registered)
        with _Patch(_run_gate=_spy, DEADLINE_SCALE=1):
            H._prove_one(tv, "no-such-registered-gate", "fake_gate.py", proof, 0, _quiet)
        self.assertEqual(seen, [registered, registered],
                         "with no allowance the deadline was %r rather than the registered %r"
                         % (seen, registered))
        seen[:] = []
        with _Patch(_run_gate=_spy, DEADLINE_SCALE=H.LANE_DEADLINE_SCALE):
            H._prove_one(tv, "no-such-registered-gate", "fake_gate.py", proof, 0, _quiet)
        self.assertEqual(seen, [registered * H.LANE_DEADLINE_SCALE] * 2,
                         "the allowance never reached the deadline: %r rather than %r — the "
                         "constant is set, read by nothing, and the flip is still live"
                         % (seen, [registered * H.LANE_DEADLINE_SCALE] * 2))


class TheRestoreHolds(unittest.TestCase):
    """The tamper is a WRITE. Everything below runs the REAL _prove_one against a REAL directory
    with REAL subprocesses, because a restore checked with a fake writer checks nothing."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="h2restore.")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.tv = os.path.join(self.root, "repo", "tv")
        os.makedirs(self.tv)
        self.subject = os.path.join(self.tv, "subject.py")
        with io.open(self.subject, "w", encoding="utf-8") as fh:
            fh.write('MODE = "GOOD"\nVALUE = 41 + 1\n')
        with io.open(os.path.join(self.tv, "fake_gate.py"), "w", encoding="utf-8") as fh:
            fh.write("import io, os, sys\n"
                     "src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),\n"
                     "              'subject.py'), encoding='utf-8').read()\n"
                     "print('Ran 1 test in 0.0s')\n"
                     "print('OK' if 'GOOD' in src else 'FAILED (failures=1)')\n"
                     "sys.exit(0 if 'GOOD' in src else 1)\n")
        self.proof = {"why": "the subject stopped being GOOD", "file": "subject.py",
                      "find": 'MODE = "GOOD"', "replace": 'MODE = "BAD"', "matches": 1}
        self.sha = self._sha()

    def _sha(self):
        with io.open(self.subject, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()

    def test_the_premise_a_real_tamper_really_runs_here(self):
        """⚠ PROVE THE PREMISE OR THE CASES BELOW PASS VACUOUSLY. Measured last batch: a case
        whose module was absent went green in 0.75s over a live defect, because the ImportError
        satisfied both assertions. If the interpreter, the subject or the anchor is not what this
        file assumes, that is UNMEASURED and it has to say so here rather than read as fine.
        """
        self.assertTrue(os.path.exists(sys.executable),
                        "there is no interpreter to run a gate with — UNMEASURED, not fine")
        with io.open(self.subject, encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(src.count(self.proof["find"]), 1,
                         "the fixture's own anchor matches %d time(s), so its sabotage would be "
                         "inert and every verdict below meaningless"
                         % src.count(self.proof["find"]))
        ok, tail = H._run_gate(self.tv, "fake_gate.py", timeout=60)
        self.assertTrue(ok, "the fixture gate is red before anything was tampered (%s)" % tail)

    def test_a_real_proof_restores_the_subject_byte_exact(self):
        v = H._prove_one(self.tv, "no-such-registered-gate", "fake_gate.py", self.proof, 0, _quiet)
        self.assertEqual(v, H.PROVEN,
                         "the fixture gate did not go red for its own sabotage (%s) — the restore "
                         "check below would then be about a tamper that never happened" % v)
        self.assertEqual(self._sha(), self.sha,
                         "the subject file was not restored byte-exact after a completed proof")

    def test_the_restore_holds_when_the_tampered_run_raises(self):
        """⚠⚠ A CRASHED PROOF THAT LEAVES A SABOTAGE BEHIND CORRUPTS EVERY GATE AFTER IT. Inside
        a lane that is the rest of that lane's work; the restore lives in a `finally` and this is
        what keeps it honest. It also checks the exploding proof is recorded BLIND rather than
        swallowed — an error is not a demonstration. [[exit-status-of-the-block]]
        """
        calls = {"n": 0}
        real = H._run_gate

        def _boom(sandbox_tv, filename, timeout=180, extra=(), script=None):
            calls["n"] += 1
            if calls["n"] == 1:
                return real(sandbox_tv, filename, timeout=timeout, extra=extra, script=script)
            raise RuntimeError("the tampered run died the way a killed push dies")

        with _Patch(_run_gate=_boom):
            with self.assertRaises(RuntimeError):
                H._prove_one(self.tv, "no-such-registered-gate", "fake_gate.py",
                             self.proof, 0, _quiet)
            self.assertEqual(calls["n"], 2,
                             "the clean run never got as far as the tampered one, so nothing was "
                             "ever written and this law watched an empty room")
            self.assertEqual(self._sha(), self.sha,
                             "the subject was left SABOTAGED after the run raised — every gate "
                             "that reads it afterwards is judging corrupted bytes")
            calls["n"] = 0
            verdict, per = H._prove_gate(self.tv, "no-such-registered-gate", "fake_gate.py",
                                         [self.proof], _quiet)
        self.assertEqual(verdict, H.BLIND, "a proof that raised was rolled up as %r" % verdict)
        self.assertEqual(per, [H.BLIND])
        self.assertEqual(self._sha(), self.sha, "the subject was not restored after the roll-up")


RED_PROOF = [
    {
        "why": "restoring the single-lane clamp makes --prove serial again while this file still "
               "reports it parallel — the speedup vanishes and the comparison silently becomes "
               "the serial loop against itself",
        "file": "heart2.py",
        "find": "    n = max(1, min(n, len(have)))",
        "replace": "    n = 1",
        "matches": 1,
    },
    {
        "why": "dropping the missing-row sweep lets a gate whose lane died VANISH from the "
               "census, and a shorter census reads as nothing to see — v2882's defect exactly",
        "file": "heart2.py",
        "find": "        for nm, prs in missing:\n            out[nm] = (BLIND, [BLIND] * len(prs))",
        "replace": "        for nm, prs in missing:\n            continue",
        "matches": 1,
    },
    {
        "why": "removing the restore leaves a sabotaged subject behind whenever the tampered run "
               "raises, and every later proof in that lane then judges corrupted bytes",
        "file": "heart2.py",
        "find": "    finally:\n        with io.open(tgt, \"w\", encoding=\"utf-8\") as fh:\n"
                "            fh.write(original)",
        "replace": "    finally:\n        pass",
        "matches": 1,
    },
    {
        "why": "dropping the deadline allowance restores the one verdict the A/B measured moving: "
               "test_a_cached_absence_is_not_an_absence[0] goes PROVEN -> UNPROVABLE under lanes, "
               "and UNPROVABLE makes _write_state DISCARD a standing proof",
        "file": "heart2.py",
        "find": "    _to = int(_to * DEADLINE_SCALE) if _to else _to",
        "replace": "    _to = _to",
        "matches": 1,
    },
    {
        "why": "leaving the allowance ON after the run widens every later single-lane deadline in "
               "a process that keeps heart2 loaded — control_app.py does exactly that",
        "file": "heart2.py",
        "find": "    finally:\n        DEADLINE_SCALE = _prev_scale",
        "replace": "    finally:\n        pass",
        "matches": 1,
    },
    {
        "why": "crediting a proof that RAISED as PROVEN is v3292's defect restored: an error is "
               "not a demonstration, and the gate would report coverage it does not have",
        "file": "heart2.py",
        "find": "            v = BLIND",
        "replace": "            v = PROVEN",
        "matches": 1,
    },
    {
        "why": "treating a run in which NOT ONE lane could build a sandbox as a completed run "
               "banks verdicts about tampering that never happened — a refusal read as success",
        "file": "heart2.py",
        "find": "    if built and not any(built):",
        "replace": "    if False:",
        "matches": 1,
    },
    {
        "why": "a lane count nobody can turn down is the false-red scar with no escape hatch: "
               "test_control goes 19.5s -> 565.9s under load and once refused a legitimate push",
        "file": "heart2.py",
        "find": '    raw = os.environ.get("HEART2_PROVE_WORKERS")',
        "replace": "    raw = None",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
