# -*- coding: utf-8 -*-
"""REG-2352 (#42 R11) + REG-2353 (#42 R16) - NO SILENT PROVE-NOTHING, AND EVERY PUSH RECORDS WHAT IT EXPECTED AND DID.

R11. `heart2.py --prove NAME[5]` matched no gate, printed "nothing to prove" and exited 0: a typo, or a proof index nobody
can ask for, read as a proof that held. hooks/pre-push deletes its prove log the moment heart2 exits 0, so a push that
PASSED left no account of what it proved, reused or re-ran.
R16. `--forecast NAMES` prints, BEFORE any proving, a "#42 FORECAST" block: per law, what the verdict cache will serve
(hit), what the red memory will narrow, what runs in full, and what can never be banked and why (UNKEYABLE) - and never
fails. Every --push run appends a record, per proof the path forecast before it ran beside the path it took, its
verdict and seconds, to a per-machine file outside every work tree (`--pushes` reads it). A proof whose key the cache
would serve when the run began, and that ran anyway, is a PROVE-ONCE VIOLATION in the record.

DRIVEN:
  1. unmatched_names / prove / main: an unmatched name and a `NAME[k]` are said and exit 2, also beside a name that
     matched; a matched run still exits 0.
  2. forecast() over a fixture tree and a fixture verdict cache: a banked proof is a hit, a remembered one narrow, the
     rest full, a law that lists a directory UNKEYABLE with its reason; a cache or a sandbox that raises is UNKNOWN, never
     a raise; `--forecast` exits 0 whatever happens.
  3. the REAL push path (_prove_gate with _PUSH set, a stand-in law run): the record says hit / narrow / full for the
     three proofs, what was banked, and why each ran; a seeded wrongful eviction is a prove-once violation; the seams
     are in it.
  4. main() writes the record with its exit through prove_record, and `--pushes` reads it back after; the writer
     refuses a file not named like its own, trims past its cap, skips a line it cannot parse, resolves a worktree to
     git's common dir, and holds a lock another writer waits on.
  5. ROUND 3 (the review of T2): prove(), the forecast and unmatched_names select gates by ONE predicate, so a root-level
     gate (`--prove visual_lock_invariant.py`) is proven, never silently skipped; and nothing the forecast or the
     run's servable set asks marks an entry used - they ask peek() / _red_peek(), the predicates the serving reads
     lookup() / _red_recall() answer with, never the serving reads themselves (under R4 those stamp usedAt).
RED_PROOF below. [[unknown-stays-unknown]] [[stale-reading]]
"""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
from console_safe import enable as _console_safe_enable  # noqa: E402  (its red-proofs carry non-ASCII)
_console_safe_enable()
import heart2 as H  # noqa: E402
import prove_record as PR  # noqa: E402

GATE = "no-such-registered-gate"
LINES = []


def _say(*a, **k):
    LINES.append(" ".join(str(x) for x in a))


def _run_main(argv, **patches):
    """main(argv) with its machine-wide side doors closed. -> (exit, printed)"""
    base = dict(install_sandbox_cleanup=lambda: [], sweep_stale_sandboxes=lambda *a, **k: [],
                propose=lambda *a, **k: os.devnull)
    base.update(patches)
    out = io.StringIO()
    with contextlib.ExitStack() as st:
        for k, v in base.items():
            st.enter_context(mock.patch.object(H, k, v))
        with contextlib.redirect_stdout(out):
            code = H.main(argv)
    return code, out.getvalue()


class NoSilentProveNothing(unittest.TestCase):
    """1 - R11"""

    def setUp(self):
        self.gates = [("g1", "test_g1.py"), ("g2", "test_g2.py")]
        self.patches = dict(gate_files=lambda say=print: list(self.gates), red_proofs_in=lambda f: [{"why": "x"}],
                            red_proof_unreadable=lambda f: False,
                            _prove_gates=lambda have, say=print, workers=None, blank=None: (
                                dict((n, H.PROVEN) for n, _f, _p in have), dict((n, [H.PROVEN]) for n, _f, _p in have)),
                            _write_state=lambda *a, **k: None)

    def test_the_names_that_match_nothing_and_why(self):
        got = dict(H.unmatched_names({"NOPE", "g1", "test_g2.py", "g1[3]", "zz[2]"}, self.gates))
        self.assertEqual(sorted(got), ["NOPE", "g1[3]", "zz[2]"], "the unmatched set is wrong: %s" % got)
        self.assertIn("`--prove g1` proves every proof of that gate", got["g1[3]"])
        self.assertIn("there is none", got["zz[2]"])

    def test_a_name_that_matches_nothing_exits_2_and_is_named(self):
        code, out = _run_main(["--prove", "NOPE"], **self.patches)
        self.assertEqual(code, 2, "a --prove name that matched no gate exited %s:\n%s" % (code, out))
        self.assertIn("NOPE", out)
        code, out = _run_main(["--prove", "g1[3]"], **self.patches)
        self.assertEqual(code, 2, "--prove NAME[k] exited %s - a proof index read as a pass" % code)
        self.assertIn("a proof index is not a gate name", out)

    def test_beside_a_name_that_matched_it_still_cannot_pass(self):
        code, out = _run_main(["--prove", "NOPE", "g1"], **self.patches)
        self.assertEqual(code, 2, "a run that proved g1 and nothing for NOPE exited %s:\n%s" % (code, out))
        code, out = _run_main(["--prove", "g1"], **self.patches)
        self.assertEqual(code, 0, "PREMISE: a matched run that proved its gate exits 0:\n%s" % out)

    def test_a_root_level_gate_is_named_by_one_predicate_everywhere(self):
        """REG-2352 (round 3) - a root-level gate's file is "../visual_lock_invariant.py" in gate_files(). unmatched_names
        took its basename as a match while prove() did not, so `--prove visual_lock_invariant.py` proved nothing, named
        nothing and exited 0. prove(), the forecast and unmatched_names now ask one predicate."""
        self.gates.append(("visual-lock", "../visual_lock_invariant.py"))
        seen = []

        def proving(have, say=print, workers=None, blank=None):
            seen.extend(n for n, _f, _p in have)
            return dict((n, H.PROVEN) for n, _f, _p in have), dict((n, [H.PROVEN]) for n, _f, _p in have)
        code, out = _run_main(["--prove", "visual_lock_invariant.py"], **dict(self.patches, _prove_gates=proving))
        self.assertEqual((code, seen), (0, ["visual-lock"]), "`--prove visual_lock_invariant.py` did not prove the "
                                                             "root-level gate (exit %s, proved %s):\n%s" % (code, seen, out))
        for want in ("visual_lock_invariant.py", "../visual_lock_invariant.py", "visual-lock"):
            self.assertEqual(H.unmatched_names({want}, self.gates), [], "%r selects a gate and was called unmatched" % want)
            self.assertEqual(H.gates_named({want}, self.gates), [("visual-lock", "../visual_lock_invariant.py")], want)
        asked = []
        code, out = _run_main(["--forecast", "visual_lock_invariant.py"], gate_files=lambda say=print: list(self.gates),
                              red_proofs_in=lambda f: [{"why": "x"}],
                              forecast=lambda have, say=print, sandbox=None, cache=None, unmatched=(): asked.append(
                                  ([n for n, _f, _p in have], list(unmatched))) or {})
        self.assertEqual(asked, [(["visual-lock"], [])], "the forecast selected another set than prove(): %s" % asked)


class _MarkingCache(H._VerdictCache):
    """A verdict cache whose SERVING read (lookup) records every key it is asked for: under R4 that read stamps the entry
    used (usedAt), and the store evicts by use. Everything else is the real cache."""

    def __init__(self, *a, **k):
        super(_MarkingCache, self).__init__(*a, **k)
        self.marked = []

    def lookup(self, key):
        self.marked.append(key)
        return super(_MarkingCache, self).lookup(key)


class _Fixture(unittest.TestCase):
    """A sandbox-shaped tree: one gate with three proofs (A, B, C) over subject.py, and one law that lists a directory."""

    def setUp(self):
        del LINES[:]
        self.root = tempfile.mkdtemp(prefix="h2record.")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.tv = os.path.join(self.root, "repo", "tv")
        os.makedirs(self.tv)
        for fn, body in (("subject.py", 'A = "GOOD"\nB = "GOOD"\nC = "GOOD"\n'),
                         ("fake_gate.py", "import subject\nimport sys\nsys.exit(0)\n"),
                         ("lister_gate.py", "import os\nNAMES = os.listdir('.')\n")):
            with io.open(os.path.join(self.tv, fn), "w", encoding="utf-8") as fh:
                fh.write(body)
        self.proofs = [{"file": "subject.py", "find": '%s = "GOOD"' % k, "replace": '%s = "BAD"' % k,
                        "matches": 1, "why": k} for k in ("A", "B", "C")]
        self.cache = _MarkingCache(path=os.path.join(self.root, ".heart2_cache.json"), say=_say)
        # the red memory remembers proof B only - keyed by the proof's own why, whatever _red_key's signature becomes.
        # _red_peek is the one read: the forecast asks it, and the push's _red_recall answers with it
        for name, value in (("_red_key", lambda *a, **k: "|".join(str(x.get("why")) for x in a if isinstance(x, dict))),
                            ("_red_peek", lambda key: ["T.test_x"] if key == "B" else None),
                            ("_red_remember", lambda *a, **k: None)):
            p = mock.patch.object(H, name, value)
            p.start()
            self.addCleanup(p.stop)

    def key(self, i):
        k, _r, why = self.cache.key_for(self.tv, GATE, "fake_gate.py", self.proofs[i])
        self.assertIsNotNone(k, "PREMISE: the fixture proof is keyable: %s" % why)
        return k

    def bank(self, i, at=None):
        k = self.key(i)
        self.cache.store(k, {"verdict": H.PROVEN, "gate": GATE, "proof": i, "why": self.proofs[i]["why"],
                             "target": "subject.py", "provedAt": at or int((time.time() - 3600) * 1000)})
        return k


class TheForecastSaysWhatThePushWillDo(_Fixture):
    """2 - R16 forecast"""

    def test_hit_narrow_full_and_unkeyable_with_its_reason(self):
        self.bank(0)
        fc = H.forecast([(GATE, "fake_gate.py", self.proofs), ("lister", "lister_gate.py", self.proofs[:1])],
                        say=_say, sandbox=self.tv, cache=self.cache)
        row = dict((r["gate"], r) for r in fc["laws"])
        self.assertEqual((row[GATE]["hit"], row[GATE]["narrow"], row[GATE]["full"]), (1, 1, 1),
                         "the forecast did not tell the banked, the remembered and the rest apart: %s" % row[GATE])
        self.assertEqual(row[GATE]["runs"], 2 + 1 + 2, "a narrowed proof is 2 runs; a full one 1 + clean + closing")
        self.assertEqual(row["lister"]["unkeyable"], 1, "a law that lists a directory was not called UNKEYABLE")
        self.assertIn("lists a directory", row["lister"]["why"])
        self.assertEqual((fc["proofs"], fc["hit"], fc["narrow"], fc["full"], fc["unkeyable"]), (4, 1, 1, 2, 1))
        self.assertTrue(any(ln.lstrip().startswith("#42 FORECAST") for ln in LINES), LINES)
        self.assertTrue(any("lister" in ln and "UNKEYABLE - " in ln and "lists a directory" in ln for ln in LINES), LINES)

    def test_a_law_it_cannot_judge_is_unknown_never_a_raise(self):
        bad = mock.Mock(wraps=self.cache)
        bad.key_for.side_effect = lambda *a, **k: ("k", [], None)
        bad.peek.side_effect = RuntimeError("the store went away")
        fc = H.forecast([(GATE, "fake_gate.py", self.proofs)], say=_say, sandbox=self.tv, cache=bad)
        self.assertIn("unknown", fc["laws"][0], "a law the forecast could not judge was given numbers: %s" % fc)
        self.assertTrue(any("UNKNOWN" in ln and GATE in ln for ln in LINES), LINES)
        with mock.patch.object(H, "make_sandbox", mock.Mock(side_effect=OSError("no disk"))):
            fc = H.forecast([(GATE, "fake_gate.py", self.proofs)], say=_say, cache=self.cache)
        self.assertIn("OSError", fc["why"] or "", "a forecast that could not build its sandbox raised or said nothing")
        self.assertTrue(any(ln.lstrip().startswith("#42 FORECAST: UNKNOWN") for ln in LINES), LINES)

    def test_the_forecast_and_the_servable_set_mark_nothing(self):
        """REG-2353 (round 3) - asked through lookup() and _red_recall(), the serving reads that record a use, the forecast
        and the push record's servable set stamped every entry they looked at as used at push start, before one proof
        ran: eviction by use then kept nothing it meant. They ask peek() and _red_peek(), which mark nothing."""
        k0 = self.bank(0)
        recalled = []
        with mock.patch.object(H, "_red_recall", lambda key: recalled.append(key) or ["T.test_x"]):
            self.assertIn(k0, H._servable_keys(self.cache), "PREMISE: the banked proof is servable")
            fc = H.forecast([(GATE, "fake_gate.py", self.proofs)], say=_say, sandbox=self.tv, cache=self.cache)
        self.assertEqual((fc["hit"], fc["narrow"], fc["full"]), (1, 1, 1), "the forecast no longer tells the banked, the "
                                                                          "remembered and the rest apart: %s" % fc)
        self.assertEqual(self.cache.marked, [], "the servable set or the forecast asked the cache's SERVING read, which "
                                                "marks an entry used: %s" % self.cache.marked)
        self.assertEqual(recalled, [], "the forecast asked the red memory's recall, which marks a sabotage used")

    def test_lookup_answers_with_peek_the_one_predicate(self):
        """REG-2353 (round 3) - peek() is the predicate a banked verdict passes to be served; lookup() answers with it."""
        now = int(time.time() * 1000)
        shapes = {"proven": {"verdict": H.PROVEN, "provedAt": now}, "undated": {"verdict": H.PROVEN},
                  "dated-by-a-bool": {"verdict": H.PROVEN, "provedAt": True}, "blind": {"verdict": H.BLIND, "provedAt": now},
                  "not-a-dict": "PROVEN"}
        self.cache.entries.update(shapes)
        for k in list(shapes) + ["absent"]:
            self.assertIs(self.cache.lookup(k), self.cache.peek(k), "lookup() and peek() disagree on %r" % k)
        self.assertEqual([k for k in sorted(shapes) if self.cache.peek(k) is not None], ["proven"])
        self.assertEqual(H._servable_keys(self.cache), frozenset(["proven"]))

    def test_the_cli_always_exits_0(self):
        code, out = _run_main(["--forecast", "NOPE"], gate_files=lambda say=print: [])
        self.assertEqual(code, 0)
        self.assertIn("#42 FORECAST", out)
        self.assertIn("NOPE", out, "a forecast name that matched no gate was not said")
        code, out = _run_main(["--forecast", "g1"], gate_files=mock.Mock(side_effect=RuntimeError("boom")))
        self.assertEqual(code, 0, "--forecast refused (exit %s) - a forecast never fails a push" % code)
        self.assertIn("#42 FORECAST: UNKNOWN", out)


class _Runs(object):
    """A stand-in law run: red once the subject reads BAD, green otherwise - narrowed or not."""

    def __call__(self, sandbox_tv, filename, timeout=180, extra=(), script=None, widths=None):
        with io.open(os.path.join(sandbox_tv, "subject.py"), encoding="utf-8") as fh:
            red = "BAD" in fh.read()
        time.sleep(0.01)
        return (False, "Ran 1 test | FAILED") if red else (True, "Ran 1 test | OK")


class ThePushRecordsWhatItDid(_Fixture):
    """3 - the record, from the REAL push path"""

    def setUp(self):
        super(ThePushRecordsWhatItDid, self).setUp()
        p = mock.patch.object(H, "_run_gate", _Runs())
        p.start()
        self.addCleanup(p.stop)
        self.addCleanup(lambda: setattr(H, "_PUSH", None))

    def push(self):
        run = H._PUSH = H._PushRun(order={}, browser=(), cache=self.cache)
        try:
            v, per = H._prove_gate(self.tv, GATE, "fake_gate.py", self.proofs, _say)
        finally:
            H._PUSH = None
        have = [(GATE, "fake_gate.py", self.proofs)]
        return H._push_record(run, have, self.cache, 3, {GATE: v}), per

    def test_each_proof_says_its_forecast_path_and_what_it_did(self):
        self.bank(0)
        with mock.patch.dict(os.environ, {"HEART2_SEAM_FOR_THE_RECORD": "1"}):
            rec, per = self.push()
        self.assertEqual(per, [H.PROVEN] * 3)
        rows = dict((r["i"], r) for r in rec["perProof"])
        self.assertEqual([(rows[i]["f"], rows[i]["a"]) for i in range(3)],
                         [("hit", "hit"), ("narrow", "narrow"), ("full", "full")],
                         "the record does not say each proof's forecast and taken path: %s" % rec["perProof"])
        self.assertEqual((rec["forecast"]["hit"], rec["forecast"]["narrow"], rec["forecast"]["full"]), (1, 1, 1))
        self.assertEqual((rec["actual"]["hit"], rec["actual"]["narrow"], rec["actual"]["full"], rec["actual"]["notRun"]),
                         (1, 1, 1, 0))
        self.assertTrue(rows[2]["b"] and rows[1]["b"], "what the push banked is not in the record: %s" % rows)
        self.assertFalse(rows[0]["b"], "a reused proof was recorded as banked again")
        self.assertEqual(rows[2]["missWhy"], "never banked on this machine")
        for i in range(3):
            self.assertIsInstance(rows[i]["s"], float, "a proof's seconds are missing: %s" % rows[i])
        self.assertEqual(rec["proveOnceViolations"], [], "a clean run reported a prove-once violation")
        self.assertEqual(rec["seams"].get("HEART2_SEAM_FOR_THE_RECORD"), "1", "an inherited seam is not in the record")
        self.assertIsNotNone(rec["wallS"])
        json.dumps(rec)

    def test_a_seeded_wrongful_eviction_is_a_prove_once_violation(self):
        k2 = self.bank(2)
        run_keys = H._servable_keys(self.cache)
        self.assertIn(k2, run_keys, "PREMISE: the cache would serve proof C when the run begins")
        real_init = H._PushRun.__init__

        def evicting_init(run, *a, **k):
            real_init(run, *a, **k)
            self.cache.entries.pop(k2, None)            # the eviction: gone from memory after the run began
        with mock.patch.object(H._PushRun, "__init__", evicting_init):
            rec, per = self.push()
        rows = dict((r["i"], r) for r in rec["perProof"])
        self.assertEqual(rows[2]["a"], "full", "PREMISE: the evicted proof ran")
        self.assertEqual([(v["g"], v["i"]) for v in rec["proveOnceViolations"]], [(GATE, 2)],
                         "a proof banked for the same bytes was re-run and the record called it clean: %s" % rec)
        self.assertIn("PROVE-ONCE VIOLATION", rows[2]["missWhy"])

    def test_the_waves_all_hit_check_marks_nothing(self):
        """REG-2353 (round 3) - the clean wave asks whether EVERY proof of a gate would be served, to skip its clean run.
        A question, not a use: the main pass's lookup() marks what it serves."""
        for i in range(3):
            k = self.bank(i)
            self.cache.entries[k]["tree"] = H.TREE_ID
        run = H._PushRun(order={}, browser=(), cache=self.cache)
        got = H._wave_gate(self.tv, GATE, "fake_gate.py", self.proofs, _say, run)
        self.assertEqual(got[0], H.NOT_RUN, "PREMISE: a gate whose every proof is banked in this tree is not run")
        self.assertEqual(self.cache.marked, [], "the wave's all-hit check asked the serving read: %s" % self.cache.marked)

    def test_the_push_marks_only_what_it_served(self):
        """REG-2353 (round 3) - PREMISE of the two above: the push's own serving read is still lookup(), so the hit it
        reused is asked there (and marked used under R4); the run's servable set, taken at its start, asked nothing."""
        k0 = self.bank(0)
        rec, per = self.push()
        self.assertEqual(per, [H.PROVEN] * 3)
        self.assertIn(k0, self.cache.marked, "the push reused a banked proof without asking the serving read")
        self.assertEqual(rec["proveOnceViolations"], [])

    def test_a_proof_banked_under_other_bytes_says_so(self):
        self.cache.store("an-older-key", {"verdict": H.PROVEN, "gate": GATE, "proof": 2, "why": "C",
                                          "target": "subject.py", "provedAt": int((time.time() - 7200) * 1000)})
        rec, _per = self.push()
        rows = dict((r["i"], r) for r in rec["perProof"])
        self.assertIn("under other bytes", rows[2]["missWhy"], rows[2])


class TheRecordOutlivesTheRun(unittest.TestCase):
    """4 - main() writes it with its exit; --pushes reads it; the writer's own rules"""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="h2pushes.")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.where = os.path.join(self.d, PR.NAME)
        p = mock.patch.dict(os.environ, {"HEART2_PUSHES_PATH": self.where})
        p.start()
        self.addCleanup(p.stop)

    def fake_prove(self, only=None, **kw):
        H._PUSH_RECORD["record"] = {"v": 1, "at": 1, "proofs": 1, "gates": sorted(only or ()),
                                    "forecast": {"hit": 1, "narrow": 0, "full": 0}, "actual": {"hit": 1, "notRun": 0},
                                    "proveOnceViolations": [], "signalKilled": 0, "wallS": 1.0}
        return {"g1": H.PROVEN}

    def test_main_writes_the_record_with_its_exit_and_pushes_reads_it(self):
        for _ in range(2):
            code, out = _run_main(["--prove", "g1", "--push"], prove=self.fake_prove)
            self.assertEqual(code, 0, out)
        recs, bad = PR.read(self.where)
        self.assertEqual((len(recs), bad), (2, 0), "a --push run left no record (or a torn one): %s" % (recs,))
        self.assertEqual(recs[-1].get("exit"), 0, "the record does not carry the run's exit")
        self.assertEqual(recs[-1].get("unmatched"), [])
        code, out = _run_main(["--pushes", "5"])
        self.assertEqual(code, 0)
        self.assertIn("#42 PUSH RECORDS: the last 2", out)
        code, out = _run_main(["--prove", "g1"], prove=self.fake_prove)
        self.assertEqual(len(PR.read(self.where)[0]), 2, "a run without --push wrote a push record")

    def test_the_writer_refuses_another_name_and_trims_past_its_cap(self):
        said = []
        other = os.path.join(self.d, "control_app.py")
        self.assertIsNone(PR.append({"x": 1}, where=other, say=said.append))
        self.assertFalse(os.path.exists(other), "the record writer wrote a file named like a guard")
        self.assertTrue(any("refusing" in s for s in said), said)
        with mock.patch.object(PR, "KEEP", 5), mock.patch.object(PR, "_TRIM_AT", 8):
            for i in range(9):
                PR.append({"n": i, "pad": "x" * 600}, where=self.where)
        recs, _bad = PR.read(self.where)
        self.assertEqual([r["n"] for r in recs], [4, 5, 6, 7, 8], "past its cap the record kept %s" % [r["n"] for r in recs])

    def test_an_unparsable_line_is_counted_not_fatal(self):
        PR.append({"n": 1}, where=self.where)
        with io.open(self.where, "a", encoding="utf-8") as fh:
            fh.write("{torn\n")
        PR.append({"n": 2}, where=self.where)
        recs, bad = PR.read(self.where)
        self.assertEqual(([r["n"] for r in recs], bad), ([1, 2], 1))

    def test_a_worktree_records_into_gits_common_dir(self):
        main = os.path.join(self.d, "main")
        wt = os.path.join(self.d, "wt")
        gd = os.path.join(main, ".git", "worktrees", "wt")
        os.makedirs(gd)
        os.makedirs(wt)
        with io.open(os.path.join(wt, ".git"), "w", encoding="utf-8") as fh:
            fh.write("gitdir: %s\n" % gd)
        with io.open(os.path.join(gd, "commondir"), "w", encoding="utf-8") as fh:
            fh.write("../..\n")
        env = {}
        self.assertEqual(os.path.realpath(PR.path(repo=wt, env=env)),
                         os.path.realpath(os.path.join(main, ".git", PR.NAME)),
                         "a worktree's record did not land in the main checkout's git dir")
        self.assertEqual(os.path.realpath(PR.path(repo=main, env=env)),
                         os.path.realpath(os.path.join(main, ".git", PR.NAME)))
        lone = os.path.join(self.d, "lone")
        os.makedirs(lone)
        self.assertEqual(PR.path(repo=lone, cache_path=os.path.join(lone, "tv", ".heart2_cache.json"), env=env),
                         os.path.join(lone, "tv", "." + PR.NAME), "a tree with no git dir did not keep it beside the cache")
        self.assertEqual(PR.path(env={"HEART2_PUSHES_PATH": "/x/" + PR.NAME}), "/x/" + PR.NAME)

    @unittest.skipUnless(os.name == "posix", "flock is the POSIX lock; Windows takes msvcrt's")
    def test_a_second_writer_waits_for_the_lock(self):
        import fcntl
        lock = open(self.where + ".flock", "a+")
        self.addCleanup(lock.close)
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        code = ("import sys; sys.path.insert(0, %r); import prove_record as PR; PR.append({'n': 'second'}, where=%r)"
                % (HERE, self.where))
        p = subprocess.Popen([sys.executable, "-c", code])
        try:
            time.sleep(1.0)
            self.assertIsNone(p.poll(), "a second writer did not wait for the lock")
            self.assertFalse(os.path.exists(self.where) and os.path.getsize(self.where),
                             "a second writer wrote while the lock was held")
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        self.assertEqual(p.wait(timeout=30), 0)
        self.assertEqual([r["n"] for r in PR.read(self.where)[0]], ["second"])


RED_PROOF = [
    {"why": "REG-2352 - an unmatched --prove name is never noticed: a typo exits 0 having proven nothing",
     "file": "heart2.py",
     "find": "    _PROVE_UNMATCHED[:] = unmatched_names(only, gates) if only else []\n",
     "replace": "    _PROVE_UNMATCHED[:] = []\n",
     "matches": 1},
    {"why": "REG-2352 - an unmatched name is said and the run still exits 0",
     "file": "heart2.py",
     "find": "    if a.prove is not None and _PROVE_UNMATCHED:\n",
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "REG-2352 - NAME[k] gets no hint: a proof index reads as a gate nobody registered",
     "file": "heart2.py",
     "find": "        m = _INDEXED_NAME.match(str(n))\n",
     "replace": "        m = None\n",
     "matches": 1},
    {"why": "REG-2353 - the forecast never calls a banked proof a hit",
     "file": "heart2.py",
     "find": "        if key is not None and cache.peek(key) is not None:\n            return \"hit\", None\n",
     "replace": "        if False:\n            return \"hit\", None\n",
     "matches": 1},
    {"why": "REG-2353 - the forecast never calls a remembered proof narrow",
     "file": "heart2.py",
     "find": "    if not _extra and not _script and _red_peek(_red_key(name, idx, pr)):\n",
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "REG-2353 - the forecast stops counting what can never be banked",
     "file": "heart2.py",
     "find": "                        row[\"unkeyable\"] += 1\n",
     "replace": "                        pass\n",
     "matches": 1},
    {"why": "REG-2353 - a law the forecast cannot judge raises the whole forecast instead of reading UNKNOWN",
     "file": "heart2.py",
     "find": "            except Exception as _fe:\n                row[\"unknown\"]",
     "replace": "            except ZeroDivisionError as _fe:\n                row[\"unknown\"]",
     "matches": 1},
    {"why": "REG-2353 - a forecast that cannot build its sandbox raises into the hook instead of reading UNKNOWN",
     "file": "heart2.py",
     "find": "    except Exception as _e:\n        out[\"why\"] = ",
     "replace": "    except ZeroDivisionError as _e:\n        out[\"why\"] = ",
     "matches": 1},
    {"why": "REG-2353 - `--forecast` fails (non-zero, a traceback) when the forecast cannot be made",
     "file": "heart2.py",
     "find": "    except Exception as e:\n        print(\"  #42 FORECAST: UNKNOWN - %s: %s\"",
     "replace": "    except ZeroDivisionError as e:\n        print(\"  #42 FORECAST: UNKNOWN - %s: %s\"",
     "matches": 1},
    {"why": "REG-2353 - a proof served by the cache is not recorded as forecast and taken: hit",
     "file": "heart2.py",
     "find": "                _mark(f=\"hit\", a=\"hit\")",
     "replace": "                _mark()",
     "matches": 1},
    {"why": "REG-2353 - the path a proof was forecast to take is never recorded",
     "file": "heart2.py",
     "find": "    _mark(once=True, f=\"narrow\" if _rids else \"full\")",
     "replace": "    _mark(once=True)",
     "matches": 1},
    {"why": "REG-2353 - a proof the red memory decided is not recorded as narrow",
     "file": "heart2.py",
     "find": "        _mark(a=\"narrow\")",
     "replace": "        _mark()",
     "matches": 1},
    {"why": "REG-2353 - what a push banked is not in its record",
     "file": "heart2.py",
     "find": "                        run.proofs.setdefault((name, _i), {})[\"b\"] = True",
     "replace": "                        pass",
     "matches": 1},
    {"why": "REG-2353 - a banked proof re-run for the same bytes (a wrongful eviction) is recorded clean",
     "file": "heart2.py",
     "find": "                elif key and key in run.keys0:\n",
     "replace": "                elif False:\n",
     "matches": 1},
    {"why": "REG-2352 - the inherited HEART2_* seams are not in the record",
     "file": "heart2.py",
     "find": "        \"seams\": _heart2_seams(),\n",
     "replace": "        \"seams\": {},\n",
     "matches": 1},
    {"why": "REG-2353 - main() never writes the record, so a passing push leaves no account once the hook deletes its log",
     "file": "heart2.py",
     "find": "                _at = _PR.append(_rec, where=_PR.path(cache_path=CACHE), say=print)\n",
     "replace": "                _at = None\n",
     "matches": 1},
    {"why": "REG-2353 - the record writer writes any file it is pointed at (a guard among them)",
     "file": "prove_record.py",
     "find": "    if os.path.basename(where) not in (NAME, \".\" + NAME):\n",
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "REG-2353 - the record grows for ever past its cap",
     "file": "prove_record.py",
     "find": "        if len(lines) <= _TRIM_AT:\n            return\n",
     "replace": "        if True:\n            return\n",
     "matches": 1},
    {"why": "REG-2353 - a worktree's record lands in the worktree's own git dir and dies with it",
     "file": "prove_record.py",
     "find": "        cd = os.path.join(gd, \"commondir\")\n",
     "replace": "        cd = os.path.join(gd, \"no-commondir\")\n",
     "matches": 1},
    {"why": "REG-2353 - two writers append and trim the record at once",
     "file": "prove_record.py",
     "find": "        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)\n",
     "replace": "        pass\n",
     # REG-2357 - its one catching case is POSIX-only (flock): on Windows the case skips in both runs and this proof
     # filed BLIND there. Judged where POSIX is.
     "matches": 1, "needs": "posix"},
    # REG-2352 (round 3) - one predicate names a gate for prove(), the forecast and unmatched_names
    {"why": "REG-2352 - prove() matches by name or file only: `--prove visual_lock_invariant.py` proves nothing and exits 0",
     "file": "heart2.py",
     "find": "    todo = gates_named(only, gates)                      # REG-2352 - the one predicate unmatched_names asks too\n",
     "replace": "    todo = [(n, f) for n, f in gates if (not only or n in only or f in only)]\n",
     "matches": 1},
    {"why": "REG-2352 - the predicate forgets a root-level gate's basename: `--prove visual_lock_invariant.py` proves "
            "nothing",
     "file": "heart2.py",
     "find": "    return bool(w) and w in (str(name), str(filename), os.path.basename(str(filename)))\n",
     "replace": "    return bool(w) and w in (str(name), str(filename))\n",
     "matches": 1},
    {"why": "REG-2352 - the forecast selects its gates by another rule than prove()",
     "file": "heart2.py",
     "find": "        todo = gates_named(want, gates) if want else []      # REG-2352 - the one predicate prove() and unmatched ask\n",
     "replace": "        todo = [(n, f) for n, f in gates if n in want or f in want]\n",
     "matches": 1},
    {"why": "REG-2352 - unmatched_names judges names by another rule than prove(), so a root-level gate is named unmatched",
     "file": "heart2.py",
     "find": "        if any(gate_named(n, gn, gf) for gn, gf in gates):  # UNMATCHED-BY-THE-ONE-PREDICATE\n",
     "replace": "        if any(n in (gn, gf) for gn, gf in gates):  # UNMATCHED-BY-THE-ONE-PREDICATE\n",
     "matches": 1},
    # REG-2353 (round 3) - nothing the forecast or the servable set asks marks an entry used
    {"why": "REG-2353 - the push record's servable set asks the serving read: every entry reads used at push start",
     "file": "heart2.py",
     "find": "        return frozenset(k for k in list(cache.entries) if cache.peek(k) is not None)  # SERVABLE-BY-PEEK\n",
     "replace": "        return frozenset(k for k in list(cache.entries) if cache.lookup(k) is not None)  # SERVABLE-BY-PEEK\n",
     "matches": 1},
    {"why": "REG-2353 - the forecast asks the cache's serving read, marking every proof it forecasts as used",
     "file": "heart2.py",
     "find": "        if key is not None and cache.peek(key) is not None:\n            return \"hit\", None\n",
     "replace": "        if key is not None and cache.lookup(key) is not None:\n            return \"hit\", None\n",
     "matches": 1},
    {"why": "REG-2353 - the forecast asks the red memory's recall, marking every sabotage it forecasts as used",
     "file": "heart2.py",
     "find": "    if not _extra and not _script and _red_peek(_red_key(name, idx, pr)):\n",
     "replace": "    if not _extra and not _script and _red_recall(_red_key(name, idx, pr)):\n",
     "matches": 1},
    {"why": "REG-2353 - lookup() stops answering with peek(): what the forecast calls a hit and what the push serves part",
     "file": "heart2.py",
     "find": "        return self.peek(key)\n",
     "replace": "        return self.entries.get(key)\n",
     "matches": 1},
    {"why": "REG-2353 - the clean wave's all-hit check asks the serving read and marks a gate's every proof used",
     "file": "heart2.py",
     "find": "                _hit = cache.peek(key) if key is not None else None   # REG-2353 - asked, not served: marks nothing\n",
     "replace": "                _hit = cache.lookup(key) if key is not None else None   # REG-2353 - asked, not served: marks nothing\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
