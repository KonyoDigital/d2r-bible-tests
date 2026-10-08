# -*- coding: utf-8 -*-
"""#42 — A PUSH PROVES EACH RED-PROOF WHERE ITS DEFECT SHOWS, THE LIKELIEST FAILURE FIRST, ONE BROWSER AT A TIME -
AND A WRONG DECLARATION CAN NEVER READ PROVEN.

His order, 2026-09-28: "do #42 right after v3522 lands" - pushes take too long. MEASURED on the v3522 push: heart2 gives
each lane its own sandbox but runs ALL proofs of one gate serially in the lane that owns it, so the character builder's
width law (41 red-proofs, each a clean AND a tampered run of a law that renders ~33 viewports, 98 s a run on his Mac) was
ONE ~105-minute thread, the mule window's (25 proofs, ~110 s a run) the other long pole, and the push gate took ~2h50m.
Attempt 1 of the same push ran 159 min and was refused on ONE blind proof that a targeted run finds in ~3 min.

`heart2.py --prove NAMES --push` (hooks/pre-push passes the flag; nothing else does) now:
  · runs a proof that declares "widths" - its clean AND its tampered run - with TV_LAW_WIDTHS naming them, so a width
    law measures only there (tv/law_widths.py); a proof that declares none runs at every width, never skipped;
  · FAILS CLOSED: a declared width at which the tamper stays green is BLIND (the push refuses as always); an UNPROVABLE
    at the declared widths is re-proved at EVERY width and that verdict stands;
  · proves the likeliest failures FIRST (an anchor that no longer matches, an entry new or changed since @{push} /
    origin/main, a proof whose tampered file changed) and STOPS at the first BLIND / INVALID / clean-run red, printing
    it at once - every proof it did not reach is NOT RUN, never banked, and the exit is 1;
  · proves a gate that starts a browser ONE AT A TIME whatever the lane count (four parallel Chrome lanes drove his Mac
    to load 100 on 2026-09-28) - and "starts a browser" is its IMPORT CLOSURE (REG-1442): a gate that reaches
    render_check / playwright through any number of helpers holds the lock, as test_the_rails_fold_is_a_chevron_not_a_dot
    does through the builder's width law; a helper nobody can parse puts its gates under the lock, named;
  · names a declared-restriction skip in a BLIND line as the declaration's, never as the law opting out (REG-1443).
Without the flag nothing changes, and run_gates / CI never set the variable, so the full sweep stays the verdict of
record.

EVERYTHING HERE IS A FIXTURE: a throwaway sandbox holding a ten-line "width law" whose defect shows at ONE viewport, and
stub provers for the ordering / stop / browser cases. No browser starts, the real tree is never copied, nothing of his
is read or written - except the cases that READ the real registry (hooks/pre-push, run_gates.py, the workflows, the
width laws' declarations, the rails fold law's imports) because that is where the wiring lives.
[[regression-guard]] [[unknown-stays-unknown]] [[the-unjoined-end]] [[zero-needs-a-denominator]]
RED_PROOF below.
"""
import ast
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import heart2 as H  # noqa: E402
import law_widths as LW  # noqa: E402

#: the fixture law: its defect ("BROKEN" in its subject) shows ONLY at 1280x800; at 99x99 it is red untampered. It
#: logs every run - the restriction it was handed and whether its subject was tampered - to the file named by its env.
_LAW = r'''
import io, os, sys
here = os.path.dirname(os.path.abspath(__file__))
raw = os.environ.get("TV_LAW_WIDTHS")
measured = {"1280x800", "375x812"} if raw is None else set(raw.split(","))
with io.open(os.path.join(here, "subject.txt"), encoding="utf-8") as fh:
    subject = fh.read()
with io.open(os.environ["H42_LOG"], "a", encoding="utf-8") as fh:
    fh.write("%s|%s\n" % (raw if raw is not None else "ALL", "tampered" if "BROKEN" in subject else "clean"))
red = ("BROKEN" in subject and "1280x800" in measured) or "99x99" in measured
# two cases, as a width law has many: under a restriction the one measured at the other viewport is a declared SKIP
print("Ran 2 tests in 0.001s")
print("")
print("FAILED (failures=1)" if red else ("OK (skipped=1)" if raw is not None else "OK"))
sys.exit(1 if red else 0)
'''
_GATE, _FILE = "h42-fixture-law", "t_h42_law.py"


def _quiet(*_a, **_k):
    pass


def _proof(**kw):
    pr = {"why": "the fixture's defect", "file": "subject.txt", "find": "fine", "replace": "BROKEN", "matches": 1}
    pr.update(kw)
    return pr


class _Patch(object):
    """Swap heart2's module globals and always put them back."""

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


class _Sandboxes(object):
    """make_sandbox stand-in: a REAL throwaway repo copy holding only the fixture law and its subject."""

    def __init__(self):
        self.made, self.lock = [], threading.Lock()

    def make(self, say=print):
        root = tempfile.mkdtemp(prefix="h42law.")
        tv = os.path.join(root, "repo", "tv")
        os.makedirs(tv)
        for name, text in (("control_app.py", "# sandbox marker\n"), (_FILE, _LAW), ("subject.txt", "all fine here\n")):
            with io.open(os.path.join(tv, name), "w", encoding="utf-8") as fh:
                fh.write(text)
        with self.lock:
            self.made.append(root)
        return tv, root


def _no_facts(have, say):
    """_push_facts without git: RED_PROOF order, nothing ranked (the ranking has its own case)."""
    return None, dict((n, list(range(len(p)))) for n, _f, p in have), [n for n, _f, _p in have], \
        {"anchor": 0, "entry": 0, "target": 0}


def _push_run(proofs, workers="1"):
    """The REAL push-time path (_prove_push -> _prove_gates -> lanes -> _prove_gate_push -> _prove_push_one ->
    _prove_one -> _run_gate) over the fixture law. -> (results, per_proof, stopped, runs logged, lines said)"""
    fd, log = tempfile.mkstemp(prefix="h42log.")
    os.close(fd)
    said, stopped = [], []
    try:
        with _Env(H42_LOG=log, HEART2_PROVE_WORKERS=workers, TV_LAW_WIDTHS=None), \
                _Patch(make_sandbox=_Sandboxes().make, _push_facts=_no_facts):
            results, per = H._prove_push([(_GATE, _FILE, proofs)], said.append, stopped)
        with io.open(log, encoding="utf-8") as fh:
            runs = [l.strip().split("|") for l in fh if l.strip()]
    finally:
        os.remove(log)
    return results, per, stopped, runs, said


class APushProofRunsOnlyWhereItsDefectShows(unittest.TestCase):

    def test_a_proof_with_widths_runs_its_clean_and_tampered_runs_only_there(self):
        """★ the clean run AND the tampered run are both handed exactly the declared viewports, and it is PROVEN"""
        results, per, stopped, runs, said = _push_run([_proof(widths=["1280x800"])])
        self.assertEqual(runs, [["1280x800", "clean"], ["1280x800", "tampered"]],
                         "the push-time proof did not run its clean and tampered runs at its declared widths only: %s" % runs)
        self.assertEqual((results, per[_GATE], stopped), ({_GATE: H.PROVEN}, [H.PROVEN], []), "\n".join(said))
        self.assertTrue(any("PROVEN" in l and "at 1280x800" in l for l in said),
                        "the verdict line does not say where it was proven: %s" % said)

    def test_a_proof_that_declares_none_runs_at_every_width(self):
        """★ no declaration = the full law, clean and tampered - never skipped, never sampled"""
        results, per, stopped, runs, said = _push_run([_proof()])
        self.assertEqual(runs, [["ALL", "clean"], ["ALL", "tampered"]], "a proof with no widths did not run at every width: %s" % runs)
        self.assertEqual(results, {_GATE: H.PROVEN}, "\n".join(said))

    def test_a_wrong_declaration_is_blind_never_proven_and_the_push_refuses(self):
        """★ FAIL CLOSED: the defect shows at 1280x800 only, the proof declares 375x812 - the tamper stays green there,
        and that is BLIND (the push refuses), never PROVEN and never quietly re-run somewhere it would pass"""
        results, per, stopped, runs, said = _push_run([_proof(widths=["375x812"])])
        self.assertEqual(runs, [["375x812", "clean"], ["375x812", "tampered"]], runs)
        self.assertEqual(results, {_GATE: H.BLIND}, "a declaration where the defect does not show read %s:\n%s" % (results, "\n".join(said)))
        self.assertEqual([s[:3] for s in stopped], [(_GATE, 0, H.BLIND)], "the blind proof did not stop and refuse the run")
        self.assertTrue(any("#42" in l and "DECLARED widths" in l for l in said), "the BLIND line does not name the declaration: %s" % said)
        blind = [l for l in said if "stayed GREEN through its own defeat" in l]
        self.assertEqual(len(blind), 1, "PREMISE: no single BLIND line was said: %s" % said)
        self.assertIn("DECLARED restriction to 375x812", blind[0],
                      "the restricted run's skip is not named as the declaration's: %s" % blind[0])
        self.assertNotIn("Both jobs", blind[0], "a declared-restriction skip read as the law opting out: %s" % blind[0])

    def test_an_unprovable_at_its_widths_is_reproved_at_every_width_and_that_verdict_stands(self):
        """the fixture is red untampered at 99x99: a sample that cannot judge the proof hands it to the full law, whose
        verdict stands (an UNPROVABLE is not failed, so keeping it would wave through a proof the full run might find
        BLIND)"""
        results, per, stopped, runs, said = _push_run([_proof(widths=["99x99"])])
        self.assertEqual(runs, [["99x99", "clean"], ["ALL", "clean"], ["ALL", "tampered"]], runs)
        self.assertEqual((results, stopped), ({_GATE: H.PROVEN}, []), "\n".join(said))

    def test_without_the_flag_nothing_changes_and_a_stray_value_never_reaches_a_gate(self):
        """★ the non-push path ignores "widths" (the full law, both runs) and _run_gate REMOVES a TV_LAW_WIDTHS left in
        the environment, so a shell's leftover can never turn a verdict into a sample"""
        fd, log = tempfile.mkstemp(prefix="h42log.")
        os.close(fd)
        try:
            with _Env(H42_LOG=log, HEART2_PROVE_WORKERS="1", TV_LAW_WIDTHS="375x812"), \
                    _Patch(make_sandbox=_Sandboxes().make):
                results, per = H._prove_gates([(_GATE, _FILE, [_proof(widths=["375x812"])])], _quiet)
            with io.open(log, encoding="utf-8") as fh:
                runs = [l.strip().split("|") for l in fh if l.strip()]
        finally:
            os.remove(log)
        self.assertEqual(runs, [["ALL", "clean"], ["ALL", "tampered"]],
                         "without --push a run was restricted (by the declaration or by the environment): %s" % runs)
        self.assertEqual(results, {_GATE: H.PROVEN})


# ── the order and the stop (stub provers: only the dispatch is under test here) ───────────────────────────────────
class _Stub(object):
    """_prove_push_one stand-in: a verdict per (gate, index), a dwell, and a record of every call."""

    def __init__(self, verdicts=None, red=(), dwell=0.0):
        self.verdicts, self.red, self.dwell = dict(verdicts or {}), set(red), dwell
        self.calls, self.spans, self.lock = [], [], threading.Lock()

    def __call__(self, sandbox, name, filename, pr, idx, say, why):
        t0 = time.time()
        time.sleep(self.dwell)
        with self.lock:
            self.calls.append((name, idx))
            self.spans.append((name, t0, time.time()))
        if (name, idx) in self.red:
            why["red"] = True
        return self.verdicts.get((name, idx), H.PROVEN)


class _Dirs(object):
    """make_sandbox stand-in for the stub cases: an empty marked directory per lane."""

    def make(self, say=print):
        root = tempfile.mkdtemp(prefix="h42lane.")
        tv = os.path.join(root, "repo", "tv")
        os.makedirs(tv)
        return tv, root


def _have(n_gates=3, n_proofs=3, widths=False):
    pr = {"file": "subject.txt", "find": "x", "replace": "y", "matches": 1}
    if widths:
        pr = dict(pr, widths=["1280x800"])
    return [("gate-%d" % g, "test_gate_%d.py" % g, [dict(pr, why="proof %d" % i) for i in range(n_proofs)])
            for g in range(n_gates)]


def _stub_run(have, stub, facts=_no_facts, lanes=1):
    """(the lane count is pinned by patching prove_workers, so free disk on the machine cannot quietly make it 1)"""
    said, stopped = [], []
    with _Patch(make_sandbox=_Dirs().make, _push_facts=facts, _prove_push_one=stub,
                prove_workers=lambda n=None, say=None: max(1, min(lanes, n or lanes))):
        results, per = H._prove_push(have, said.append, stopped)
    return results, per, stopped, said


class TheLikeliestFailureRunsFirstAndStopsTheRun(unittest.TestCase):

    def test_the_order_puts_what_changed_first(self):
        """★ P2: an anchor that no longer matches, then an entry new or changed since the base, then a proof whose
        tampered file changed - ties keep RED_PROOF order, and gates go by their best proof"""
        a = {"file": "a.txt", "find": "1", "replace": "2"}
        b = {"file": "b.txt", "find": "1", "replace": "2"}
        c = {"file": "c.txt", "find": "rotted", "replace": "2"}
        have = [("g-quiet", "q.py", [a, a]), ("g-mixed", "m.py", [a, b, dict(a, why="new"), c])]
        base = {"q.py": [a, a], "m.py": [a, b, c]}
        changed = {H._proof_target_rel(b)}
        order, gates, counts = H.push_order(have, base, changed, lambda pr: pr.get("find") == "rotted")
        self.assertEqual(order["g-mixed"], [3, 2, 1, 0], "the likeliest failures are not first: %s" % order)
        self.assertEqual(order["g-quiet"], [0, 1], "an untouched gate lost its RED_PROOF order: %s" % order)
        self.assertEqual(gates, ["g-mixed", "g-quiet"], "the gate holding the likeliest failure is not proved first")
        self.assertEqual(counts, {"anchor": 1, "entry": 1, "target": 1}, "PRINT THE DENOMINATOR: %s" % counts)
        _o, _g, none = H.push_order(have, None, None, None)
        self.assertEqual((_o["g-mixed"], none), ([0, 1, 2, 3], {"anchor": 0, "entry": 0, "target": 0}),
                         "an UNKNOWN base ranked something as changed")
        _o, _g, fresh = H.push_order(have, {"q.py": [a, a], "m.py": []}, set(), None)
        self.assertEqual(fresh["entry"], 4, "a gate file the base does not have did not count every entry NEW")

    def test_a_blind_proof_among_many_is_reported_first_and_the_run_stops(self):
        """★ the changed proof is proved first; it is BLIND; nothing after it runs, every other gate is NOT RUN (never
        banked, never PROVEN), and the stop is the LAST thing said - where the hook's tail shows it"""
        have = _have(3, 3)
        stub = _Stub({("gate-2", 1): H.BLIND})

        def facts(hv, say):
            base, order, gates, counts = _no_facts(hv, say)
            order["gate-2"] = [1, 0, 2]
            return "origin/main", order, ["gate-2", "gate-0", "gate-1"], dict(counts, entry=1)

        results, per, stopped, said = _stub_run(have, stub, facts)
        self.assertEqual(stub.calls, [("gate-2", 1)], "the run did not stop at the first failure: %s" % stub.calls)
        self.assertEqual(results, {"gate-2": H.BLIND}, "a gate the stop never reached was banked: %s" % results)
        self.assertEqual(per["gate-2"], [None, H.BLIND, None])
        self.assertEqual([s[:3] for s in stopped], [("gate-2", 1, H.BLIND)])
        self.assertTrue(any("stopped before 2 gate(s) were reached" in l for l in said),
                        "a stopped run's lane went on taking gates: %s" % said)
        fail = [i for i, l in enumerate(said) if "FAIL FAST" in l]
        self.assertTrue(fail and fail[0] < len(said) - 1, "the failure was not printed the moment it was found: %s" % said)
        tail = " ".join(said[-3:])
        self.assertIn("STOPPED", tail, "the stop is not the last thing said: %s" % said[-3:])
        self.assertIn("8 of 9 proof(s) NOT RUN", tail, "PRINT THE DENOMINATOR: %s" % said[-3:])

    def test_with_no_failure_every_proof_still_runs(self):
        """★ fail fast may only cut a run SHORT on a failure - a clean push proves every proof of every gate"""
        have = _have(3, 3)
        stub = _Stub()
        results, per, stopped, said = _stub_run(have, stub)
        self.assertEqual(sorted(stub.calls), sorted((g, i) for g in ("gate-0", "gate-1", "gate-2") for i in range(3)))
        self.assertEqual((results, stopped), (dict((g, H.PROVEN) for g in ("gate-0", "gate-1", "gate-2")), []))

    def test_a_clean_run_red_stops_the_run_but_a_run_that_could_not_judge_does_not(self):
        """ALREADY RED untampered stops the run (it is UNPROVABLE, which is not failed - so the stop itself must refuse);
        an UNPROVABLE that is a deadline or a missing file is named and the run goes on, as it always did"""
        have = _have(2, 2)
        stub = _Stub({("gate-0", 0): H.UNPROVABLE}, red=[("gate-0", 0)])
        results, per, stopped, said = _stub_run(have, stub)
        self.assertEqual((stub.calls, [s[:3] for s in stopped]), ([("gate-0", 0)], [("gate-0", 0, H.UNPROVABLE)]))
        self.assertEqual(results, {}, "a gate cut short by the stop was banked: %s" % results)
        stub = _Stub({("gate-0", 0): H.UNPROVABLE})
        results, per, stopped, said = _stub_run(have, stub)
        self.assertEqual((len(stub.calls), stopped), (4, []), "a run that could not judge one proof stopped the push")
        self.assertEqual(results, {"gate-0": H.UNPROVABLE, "gate-1": H.PROVEN})

    def test_a_gate_cut_short_never_reads_proven(self):
        self.assertEqual(H._push_gate_verdict([H.PROVEN, None]), H.NOT_RUN)
        self.assertEqual(H._push_gate_verdict([H.PROVEN, H.BLIND, None]), H.BLIND)
        self.assertEqual(H._push_gate_verdict([None, H.INVALID]), H.INVALID)
        self.assertEqual(H._push_gate_verdict([H.PROVEN, H.UNPROVABLE]), H.UNPROVABLE)
        self.assertEqual(H._push_gate_verdict([H.PROVEN, H.PROVEN]), H.PROVEN)

    def test_a_stop_before_any_gate_finished_never_writes_the_census(self):
        """★ _write_state reads an EMPTY result as a full run that proved nothing and would wipe every standing proof -
        so a push-time run stopped before any gate was judged to the end writes nothing at all"""
        wrote = []

        def stopped_run(have, say, stopped, cache=None, blank=None):      # P3: prove(push=True) hands the cache in by keyword
            stopped.append(("g", 0, H.UNPROVABLE, "the law is ALREADY RED untampered"))
            return {}, {"g": [H.UNPROVABLE, None]}

        with _Patch(gate_files=lambda say=None: [("g", "test_g.py")],
                    red_proofs_in=lambda f: [_proof(), _proof()], red_proof_unreadable=lambda f: False,
                    _prove_push=stopped_run, _write_state=lambda r, measured=None, unmeasured=None: wrote.append(r)):
            got = H.prove(only={"g"}, say=_quiet, push=True, stopped=[])
        self.assertEqual((got, wrote), ({}, []), "a stopped run with nothing judged wrote the census: %s" % wrote)

    def test_main_refuses_a_stopped_run_and_passes_the_flag_only_with_push(self):
        """★ main() exits 1 on a stop even when what stopped it is UNPROVABLE; without --push, prove() is called exactly
        as it always was"""
        seen = []

        def fake_prove(only=None, **kw):
            seen.append(kw)
            if kw.get("stopped") is not None:
                kw["stopped"].append(("g", 0, H.UNPROVABLE, "the law is ALREADY RED untampered"))
            return {"g": H.UNPROVABLE} if kw.get("push") else {"g": H.PROVEN}

        with _Patch(prove=fake_prove, propose=lambda *a, **k: os.devnull,
                    sweep_stale_sandboxes=lambda *a, **k: [], install_sandbox_cleanup=lambda: []):
            import contextlib
            with contextlib.redirect_stdout(io.StringIO()):
                code_push = H.main(["--prove", "g", "--push"])
                code_plain = H.main(["--prove", "g"])
        self.assertEqual(code_push, 1, "a stopped push-time run exited 0 - the proofs after the stop pass unseen")
        self.assertEqual(code_plain, 0)
        self.assertEqual([sorted(k) for k in seen], [["push", "stopped"], []],
                         "prove() was not called with the flag at push time, or WAS called with it without: %s" % seen)


class OneBrowserAtATime(unittest.TestCase):

    def test_browser_gates_never_overlap_and_other_gates_keep_their_lanes(self):
        """★ two lanes, two gates each: the width-law gates (they declare widths) never run at the same time; two plain
        gates DO overlap in the same fixture - so the lanes are real and the lock is what serializes the browsers"""
        def overlaps(spans, a, b):
            sa = [(t0, t1) for n, t0, t1 in spans if n == a]
            sb = [(t0, t1) for n, t0, t1 in spans if n == b]
            return any(x0 < y1 - 0.02 and y0 < x1 - 0.02 for x0, x1 in sa for y0, y1 in sb)

        stub = _Stub(dwell=0.25)
        _stub_run(_have(2, 2, widths=True), stub, lanes=2)
        self.assertEqual(len(stub.calls), 4)
        self.assertFalse(overlaps(stub.spans, "gate-0", "gate-1"), "two browser gates ran at once: %s" % stub.spans)
        stub = _Stub(dwell=0.25)
        _stub_run(_have(2, 2, widths=False), stub, lanes=2)
        self.assertTrue(overlaps(stub.spans, "gate-0", "gate-1"),
                        "PREMISE: two plain gates did not overlap in two lanes, so the case above measured nothing")

    #: fixture tv/ for the closure: name -> source. render_check here is a stub; nothing in it ever runs.
    _TREE = {
        "render_check.py": "CHROME = '/nowhere'\n",
        "helper_one.py": "import render_check as RC\n",
        "helper_two.py": "import helper_one\n",
        "helper_pw.py": "from playwright.sync_api import sync_playwright\n",
        "helper_plain.py": "import json\nimport os\n",
        "cyc_a.py": "import cyc_b\n",
        "cyc_b.py": "import cyc_a\nimport helper_plain\n",
        "helper_broken.py": "def (:\n",
        "t_direct.py": "import render_check\n",
        "t_one.py": "import helper_one as H1\nRC = H1.RC\n",
        "t_two.py": "import helper_two\n",
        "t_pw.py": "from helper_pw import sync_playwright\n",
        "t_lazy.py": "def later():\n    import helper_one\n",
        "t_dyn.py": "import importlib\nM = importlib.import_module('helper_two')\n",
        "t_plain.py": "import json\nimport helper_plain\nimport cyc_a\nNOTE = 'render_check is only named here'\n",
        "t_unk.py": "import helper_broken\n",
    }

    def test_a_gate_that_reaches_the_renderer_through_helpers_holds_the_lock(self):
        """★ the lock set is the IMPORT CLOSURE: a gate reaching render_check / playwright through one helper, through two,
        lazily inside a function, or by a literal import_module is in it; a gate importing neither (through a cycle and a
        prose mention of the name) is not; a helper nobody can parse is UNKNOWN and goes under the lock, named"""
        d = tempfile.mkdtemp(prefix="h42graph.")
        try:
            for name, text in self._TREE.items():
                with io.open(os.path.join(d, name), "w", encoding="utf-8") as fh:
                    fh.write(text)
            gates = [(f[:-3], f) for f in sorted(self._TREE) if f.startswith("t_")]
            direct = H.pixel_gates([(n, os.path.join(d, f)) for n, f in gates])
            self.assertEqual(direct, {"t_direct"},
                             "PREMISE: the one-file read should see only the direct import, or this measured nothing: %s"
                             % sorted(direct))
            unk = []
            # t_gone.py is never written: an ABSENT gate runs nothing, so it is neither locked nor unknown
            got = H.browser_gates(gates + [("t_gone", "t_gone.py")], tv_dir=d, unclassified=unk)
            # a tv/ nobody can LIST is not an empty tree: the gate's helpers are unknown, so it is locked and named
            unk2 = []
            blind = H.browser_gates([("t_one", os.path.join(d, "t_one.py"))], tv_dir=os.path.join(d, "unlistable"),
                                    unclassified=unk2)
        finally:
            import shutil
            shutil.rmtree(d, ignore_errors=True)
        self.assertEqual(got, {"t_direct", "t_one", "t_two", "t_pw", "t_lazy", "t_dyn", "t_unk"},
                         "the lock set is not the import closure: %s" % sorted(got))
        self.assertEqual(unk, ["t_unk"], "a gate whose helper cannot be parsed was not NAMED as unknown: %s" % unk)
        self.assertEqual((blind, unk2), ({"t_one"}, ["t_one"]),
                         "a tv/ that could not be listed read as a tree with no helpers: the gate left the lock")

    def test_the_real_rails_fold_law_is_in_the_lock_set(self):
        """★ the review's own example: it starts Chrome as FT.RC._chrome_up() through the builder's width law"""
        got = H.browser_gates([("rails", "test_the_rails_fold_is_a_chevron_not_a_dot.py")])
        self.assertEqual(got, {"rails"}, "test_the_rails_fold_is_a_chevron_not_a_dot is not under the one-browser lock")

    def test_the_push_run_locks_what_the_closure_finds(self):
        """★ the join: _prove_push hands the CLOSURE to the lock - the real rails fold law is held by it, and this law
        (heart2, law_widths, no browser anywhere under it) keeps its lane"""
        seen = []

        def stub(sandbox, name, filename, pr, idx, say, why):
            seen.append(set(H._PUSH.browser))
            return H.PROVEN

        pr = {"file": "subject.txt", "find": "x", "replace": "y", "matches": 1}
        _stub_run([("rails", "test_the_rails_fold_is_a_chevron_not_a_dot.py", [pr]),
                   ("plain", os.path.basename(__file__), [pr])], stub)
        self.assertTrue(seen, "PREMISE: the stub prover was never called")
        self.assertIn("rails", seen[0], "the push-time lock does not hold a gate that starts Chrome through a helper")
        self.assertNotIn("plain", seen[0], "a gate that reaches no browser was put under the lock: %s" % seen[0])

    def test_a_declared_restriction_skip_never_reads_as_the_law_opting_out(self):
        """★ under a DECLARED restriction a width law skips every case measured elsewhere by design: the BLIND line names
        those skips as the restriction's and points at the declaration - never "some laws opted out" / "fix the SKIP".
        Without a restriction the same tail reads exactly as it always did (the baseline)"""
        tail = "Ran 23 tests in 15.0s | OK (skipped=12)"
        plain = H.blind_reason("w", 1, tail)
        self.assertIn("Both jobs", plain, "PREMISE: the unrestricted mixed-skip sentence changed - re-anchor this case")
        got = H.blind_reason("w", 1, tail, widths=((1280, 800),))
        self.assertIn("12 of 23 law(s) SKIPPED under the proof's DECLARED restriction to 1280x800", got, got)
        for wrong in ("Both jobs", "opted out", "Fix the SKIP"):
            self.assertNotIn(wrong, got, "a declared-restriction skip read as the law opting out: %s" % got)
        every = H.blind_reason("w", 1, "Ran 5 tests in 1.0s | OK (skipped=5)", widths=((375, 812),))
        self.assertIn("ALL 5 law(s) SKIPPED under the proof's DECLARED restriction to 375x812", every, every)
        self.assertIn("the declaration measured nothing", every, every)
        self.assertNotIn("Fix the SKIP", every, every)
        self.assertEqual(H.blind_reason("w", 1, "Ran 5 tests | OK", widths=((375, 812),)),
                         H.blind_reason("w", 1, "Ran 5 tests | OK"), "a restricted run with NO skip grew a skip clause")


# ── the restriction itself, and where it may never reach ─────────────────────────────────────────────────────────
class TheRestrictionIsAProvingDeviceNeverAVerdict(unittest.TestCase):

    def test_law_widths_reads_unset_and_empty_as_every_width_and_refuses_garbage(self):
        self.assertIsNone(LW.only({}))
        self.assertIsNone(LW.only({LW.ENV: "  "}), "an EMPTY restriction read as 'no width at all' - every case would skip")
        self.assertEqual(LW.only({LW.ENV: "1280x800, 375x812"}), ((1280, 800), (375, 812)))
        for bad in ("1280", "wide", "1280x800,,", "x800"):
            with self.assertRaises(ValueError, msg="%r was read as a restriction" % bad):
                LW.only({LW.ENV: bad})
        self.assertEqual(LW.pick(((2000, 1300), (1280, 800)), ((1280, 800),)), ((1280, 800),))
        self.assertEqual(LW.pick(((2000, 1300), (1280, 800)), None), ((2000, 1300), (1280, 800)))
        self.assertIsNone(LW.declared({"find": "x"}))
        for bad in ([], "1280x800", ["1280"], None):
            with self.assertRaises(ValueError, msg="widths=%r was read" % (bad,)):
                LW.declared({"widths": bad})
        env = {LW.ENV: "1280x800", "OTHER": "1"}
        self.assertEqual((LW.scrub(env), env), ("1280x800", {"OTHER": "1"}))

    def test_run_gates_scrubs_it_before_its_first_gate(self):
        """★ the gate set is the verdict of record: run() removes TV_LAW_WIDTHS (law_widths.scrub) BEFORE its gate loop"""
        with io.open(os.path.join(HERE, "run_gates.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        run = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run"), None)
        self.assertIsNotNone(run, "run_gates.run moved - re-anchor this law")
        scrub_at = loop_at = None
        for i, st in enumerate(run.body):
            for n in ast.walk(st):
                if scrub_at is None and isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "scrub":
                    scrub_at = i
                if loop_at is None and isinstance(st, ast.For) and getattr(st.iter, "id", None) == "GATES":
                    loop_at = i
        self.assertIsNotNone(loop_at, "PREMISE: run() has no `for g in GATES` loop - re-anchor this law")
        self.assertTrue(scrub_at is not None and scrub_at < loop_at,
                        "run() does not scrub TV_LAW_WIDTHS before its first gate (scrub at %s, loop at %s)" % (scrub_at, loop_at))

    def test_ci_and_the_gate_registry_never_set_it(self):
        wf = os.path.join(ROOT, ".github", "workflows")
        names = sorted(os.listdir(wf)) if os.path.isdir(wf) else []
        self.assertTrue(names, "PREMISE: no CI workflow was found to read")
        for n in names:
            with io.open(os.path.join(wf, n), encoding="utf-8", errors="replace") as fh:
                self.assertNotIn(LW.ENV, fh.read(), "the CI workflow %s names %s - CI must measure every width" % (n, LW.ENV))
        import run_gates as RG
        for g in RG.GATES:
            self.assertFalse(any(LW.ENV in str(a) for a in (g.argv or [])), "gate %s passes %s" % (g.name, LW.ENV))

    def test_the_hook_passes_the_flag_only_to_its_prove_call(self):
        """★ hooks/pre-push: exactly one command runs heart2.py, it is the --prove call, and it carries --push; nothing in
        the hook sets TV_LAW_WIDTHS itself"""
        with io.open(os.path.join(ROOT, "hooks", "pre-push"), encoding="utf-8") as fh:
            lines = [l.strip() for l in fh]
        calls = [l for l in lines if "heart2.py" in l and not l.startswith(("#", "echo"))]
        self.assertEqual(len(calls), 1, "PREMISE: the hook runs heart2.py %d times: %s" % (len(calls), calls))
        self.assertIn("--prove", calls[0])
        self.assertIn("--push", calls[0], "the hook's red-proof step does not pass --push: %s" % calls[0])
        self.assertEqual([l for l in lines if LW.ENV in l and not l.startswith("#")], [],
                         "the hook sets %s itself" % LW.ENV)

    def test_every_declared_width_is_one_its_law_measures(self):
        """★ a declaration reaches a law that honours it (the gate imports law_widths), reads cleanly, and names only
        viewports the law measures (its VIEWPORTS) - a viewport it never measures would make the proof BLIND on the day
        of a push instead of here. PRINT THE DENOMINATOR: the two width laws declare, or this measured nothing."""
        decl = {}
        for n, f in H.gate_files(say=_quiet):
            prs = H.red_proofs_in(f) or []
            if H._declares_widths(prs):
                decl[f] = prs
        self.assertTrue({"test_the_character_builder_fits_at_every_width.py",
                         "test_the_mule_window_fits_at_every_width.py"} <= set(decl),
                        "PREMISE: the width laws declare no widths, so this case measured nothing: %s" % sorted(decl))
        bad, n = [], 0
        for f, prs in sorted(decl.items()):
            with io.open(os.path.join(HERE, f), encoding="utf-8") as fh:
                mods = set()
                for x in ast.walk(ast.parse(fh.read())):
                    if isinstance(x, ast.Import):
                        mods.update(a.name for a in x.names)
            if "law_widths" not in mods:
                bad.append("%s declares widths but never imports law_widths, so the restriction cannot reach it" % f)
                continue
            got = subprocess.run([sys.executable, "-c", "import json, sys; sys.path.insert(0, %r); import %s as L; "
                                  "print(json.dumps(L.VIEWPORTS))" % (HERE, f[:-3])],
                                 cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
            if got.returncode != 0:
                bad.append("%s: its VIEWPORTS could not be read: %s" % (f, got.stderr.decode("utf-8", "replace")[-300:]))
                continue
            law = set(tuple(x) for x in json.loads(got.stdout.decode("utf-8").strip().splitlines()[-1]))
            for i, pr in enumerate(prs):
                try:
                    w = LW.declared(pr)
                except ValueError as e:
                    bad.append("%s[%d]: %s" % (f, i, e))
                    continue
                if w is None:
                    continue
                n += 1
                off = [x for x in w if tuple(x) not in law]
                if off:
                    bad.append("%s[%d] declares %s, which the law never measures" % (f, i, LW.label(off)))
        self.assertGreater(n, 0, "PRINT THE DENOMINATOR: no declaration was checked")
        self.assertEqual(bad, [], "\n  ".join(bad))


RED_PROOF = [
    {
        "why": "a push-time proof's declared widths never reach its runs: it measures every width (the push stays slow)",
        "file": "heart2.py",
        "find": "    v = _prove_one(sandbox, name, filename, pr, idx, say, widths=widths, why={})\n",
        "replace": "    v = _prove_one(sandbox, name, filename, pr, idx, say, why={})\n",
        "matches": 1,
    },
    {
        "why": "a TV_LAW_WIDTHS left in the environment reaches every gate heart2 runs, push or not",
        "file": "heart2.py",
        "find": "    env.pop(\"TV_LAW_WIDTHS\", None)\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "a declaration where the defect does not show reads PROVEN instead of BLIND",
        "file": "heart2.py",
        "find": "    if v != UNPROVABLE:\n        return v\n    # ⚠ AN UNPROVABLE AT A SAMPLE IS NOT KEPT",
        "replace": "    if v != UNPROVABLE:\n        return PROVEN if v == BLIND else v\n    # ⚠ AN UNPROVABLE AT A SAMPLE IS NOT KEPT",
        "matches": 1,
    },
    {
        "why": "an UNPROVABLE at the declared widths is kept - never re-proved at every width",
        "file": "heart2.py",
        "find": "    if v != UNPROVABLE:\n        return v\n    # ⚠ AN UNPROVABLE AT A SAMPLE IS NOT KEPT",
        "replace": "    if True:\n        return v\n    # ⚠ AN UNPROVABLE AT A SAMPLE IS NOT KEPT",
        "matches": 1,
    },
    {
        "why": "the non-push path honours a declaration: a verdict run becomes a sample",
        "file": "heart2.py",
        "find": "    if _PUSH is not None:\n        return _prove_gate_push(sandbox, name, filename, proofs, say, _PUSH)\n",
        "replace": "    return _prove_gate_push(sandbox, name, filename, proofs, say, _PUSH or _PushRun())\n",
        "matches": 1,
    },
    {
        "why": "a failure does not stop the run: the other gates still run after a BLIND (v3522: 159 min for one blind proof)",
        "file": "heart2.py",
        "find": "            if run.fail(name, i, got[i], reason):\n",
        "replace": "            if True:\n",
        "matches": 1,
    },
    {
        "why": "a stopped run's lane keeps taking gates",
        "file": "heart2.py",
        "find": "            if _PUSH is not None and _PUSH.stop.is_set():\n                break\n",
        "replace": "            if False:\n                break\n",
        "matches": 1,
    },
    {
        "why": "the proofs are proved in RED_PROOF order: what changed in this push is not first",
        "file": "heart2.py",
        "find": "        order[name] = [i for _s, i in sorted(scores)]\n",
        "replace": "        order[name] = [i for _s, i in scores]\n",
        "matches": 1,
    },
    {
        "why": "a gate the stop cut short reads PROVEN on the proofs that happened to run first",
        "file": "heart2.py",
        "find": "    if len(got) < len(per):\n        return NOT_RUN\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "a run stopped on a law ALREADY RED untampered exits 0: the proofs after it pass unseen",
        "file": "heart2.py",
        "find": "    if _stopped:\n        _n, _i, _v, _why = _stopped[0]\n",
        "replace": "    if False:\n        _n, _i, _v, _why = _stopped[0]\n",
        "matches": 1,
    },
    {
        "why": "a clean-run red does not stop the push-time run",
        "file": "heart2.py",
        "find": "        if got[i] == UNPROVABLE and why.get(\"red\"):\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        "why": "a push-time run stopped before any gate finished writes an EMPTY result: every standing proof is wiped",
        "file": "heart2.py",
        "find": "        if results is not None and not results:\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        # REG-2114 - this proof used to tamper browser_slot(); REG-1989 moved every push lane with a browser gate onto
        # take(), so browser_slot's lock branch is never reached and the proof stayed green through its own defeat
        # (BLIND - it held every river lock shut on his Mac). It now tampers the line the one-browser case drives: two
        # browser gates in two lanes, so the second lane finds the browser busy, nothing else left, and waits on it.
        "why": "two browser gates run at once in two lanes (four parallel Chromes drove his Mac to load 100)",
        "file": "heart2.py",
        "find": "            return self._items.pop(0), self.browser_lock     # only browser gates are left: wait for the one browser\n",
        "replace": "            return self._items.pop(0), contextlib.nullcontext()\n",
        "matches": 1,
    },
    {
        "why": "an EMPTY TV_LAW_WIDTHS reads as a restriction to nothing: every width case skips and the law reads green",
        "file": "law_widths.py",
        "find": "    if raw is None or not str(raw).strip():\n        return None\n    return parse(raw)\n",
        "replace": "    if raw is None:\n        return None\n    return parse(raw) if str(raw).strip() else ()\n",
        "matches": 1,
    },
    {
        "why": "run_gates no longer scrubs TV_LAW_WIDTHS: a shell's leftover turns the verdict of record into a sample",
        "file": "run_gates.py",
        "find": "    _stray_widths = _LW.scrub()\n",
        "replace": "    _stray_widths = None\n",
        "matches": 1,
    },
    {
        "why": "the hook stops passing --push: every width law's proofs run the full sweep again (~2h50m)",
        "file": "hooks/pre-push",
        "find": "    if python3 \"$REPO/tv/heart2.py\" --prove $_gates --push > \"$_prove_log\" 2>&1; then\n",
        "replace": "    if python3 \"$REPO/tv/heart2.py\" --prove $_gates > \"$_prove_log\" 2>&1; then\n",
        "matches": 1,
    },
    {
        "why": "REG-1442 - the lock set stops at the gate's own imports: a gate that starts Chrome through a helper (the "
               "rails fold law, through the builder's width law) runs a second browser beside a width law",
        "file": "heart2.py",
        "find": "                stack.append((dep, None))\n",
        "replace": "                pass\n",
        "matches": 1,
    },
    {
        "why": "REG-1442 - _prove_push builds its lock from the one-file read again, not the import closure",
        "file": "heart2.py",
        "find": "    browser = browser_gates([(n, f) for n, f, _p in have], unclassified=_unk) | set(\n",
        "replace": "    browser = pixel_gates([(n, f) for n, f, _p in have]) | set(\n",
        "matches": 1,
    },
    {
        "why": "REG-1442 - a helper nobody can parse reads as 'no browser': its gates leave the lock and nobody is told",
        "file": "heart2.py",
        "find": "                verdict = \"unknown\"\n",
        "replace": "                verdict = False\n",
        "matches": 1,
    },
    {
        "why": "REG-1442 - a tv/ that cannot be listed reads as a tree with no helpers: every helper-reached browser "
               "leaves the lock",
        "file": "heart2.py",
        "find": "        seen, stack, verdict = set(), [(start, path)], (False if local is not None else \"unknown\")\n",
        "replace": "        seen, stack, verdict = set(), [(start, path)], False\n        local = local or set()\n",
        "matches": 1,
    },
    {
        "why": "REG-1442 - a literal importlib.import_module / __import__ of a helper is not followed",
        "file": "heart2.py",
        "find": "            if called in (\"__import__\", \"import_module\"):\n",
        "replace": "            if False:\n",
        "matches": 1,
    },
    {
        "why": "REG-1443 - a BLIND line reads a declared-restriction skip as the law opting out ('fix the SKIP')",
        "file": "heart2.py",
        "find": "    if widths:\n        import law_widths as _LW\n        _at = _LW.label(widths)\n",
        "replace": "    if False:\n        import law_widths as _LW\n        _at = _LW.label(widths)\n",
        "matches": 1,
    },
    {
        "why": "REG-1443 - the prover never hands its restriction to blind_reason, so the fix is correct and unreachable",
        "file": "heart2.py",
        "find": "blind_reason(pr.get(\"why\"), got, tail2, widths=widths)",
        "replace": "blind_reason(pr.get(\"why\"), got, tail2)",
        "matches": 1,
    },
    {
        "why": "a declaration names a viewport its law never measures (it would read BLIND on the day of a push)",
        "file": "test_the_character_builder_fits_at_every_width.py",
        "find": "        \"widths\": [\"1024x768\"],",
        "replace": "        \"widths\": [\"1024x769\"],",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
