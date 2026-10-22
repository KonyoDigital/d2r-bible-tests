# -*- coding: utf-8 -*-
"""REG-2440 (#147 R1) - A PROOF BANKED BY WHAT ITS RUNS READ IS NEVER SERVED WHERE ANY OF IT MOVED.

MEASURED (#147): a proof's static key digests every tracked file its law's import closure NAMES - every heart2/prover law
in the machine's cache keyed 1,217-1,259 inputs, so any test-file edit re-proved them all - and a law that lists a folder
itself has no static key at all, so it re-proves on every push and every census. heart2 now traces each proof run in its
sandbox (track trace-facts' gate_trace: bytes read, stats, absences, listings, env reads, imports) and banks a PROVEN by
those facts too; a later run serves it only where gate_ledger.facts_hold says every fact still holds. A key built from
reads is only safe if it is NEVER NARROWER than what the runs read - a read only the TAMPERED run made is a read too.

Driven through the REAL prove path (_prove_gates / _prove_push, lanes, _prove_gate_census / _prove_gate_push, _prove_one,
_run_gate, the real trace and gate_ledger) over a throwaway fixture tree heart2 tracks as a sandbox; the verdict cache
(and the facts beside it) is this law's own file, the red memory this law's own or closed:
  1. a fixture law statically UNKEYABLE (it lists a folder) whose tampered branch makes one read only it makes - opens a
     file, imports a module, stats an absent path, lists a folder - is banked by its facts and served on the same bytes;
     move THAT one read's input and only that proof runs again. Its tampered branch importing sqlite3 (strict), starting
     `python -I` or a shell untraces the proof: never banked by facts, run every time;
  2. a push that narrowed every proof (the red memory) has no FULL clean run with facts: a proof with a static key is
     banked by it only; one with none pays one full clean run and is banked by its facts;
  3. a path the runs both read and wrote (its time put back, so only that rule can tell), and a read of a file an
     earlier gate in the same sandbox changed, are banked by their static key only - never by facts;
  4. facts that are missing, or that are not the bytes their name says, are never served;
  5. a tree with no .git reachable is answered UNKNOWN without asking git (a sandbox has none), so a law that builds a
     verdict cache is not untraceable for a `git ls-files` child; a tree with a .git above it is still asked.
RED_PROOF below.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2 as H  # noqa: E402

#: the fixture law. Its subject says "fine"; a proof replaces that word, and the tampered run then takes ONE branch -
#: the read only it makes - and fails. Every run is logged: full | subset, and the word it found.
_LAW = r'''
import io, os, subprocess, sys, unittest
here = os.path.dirname(os.path.abspath(__file__))
EDITION = 1


def _subject():
    with io.open(os.path.join(here, "sub" + "ject.txt"), encoding="utf-8") as fh:
        return fh.read().strip()


def _branch(word):
    if word == "OPEN":
        with io.open(os.path.join(here, "branch" + "_data.txt"), encoding="utf-8") as fh:
            fh.read()
    elif word == "IMPORT":
        import t_branch_helper  # noqa: F401
    elif word == "ABSENT":
        os.path.exists(os.path.join(here, "branch" + "_flag"))
    elif word == "LIST":
        os.listdir(os.path.join(here, "branch" + "_dir"))
    elif word == "ROOTLIST":
        os.stat(os.path.dirname(here))
        os.listdir(os.path.dirname(here))
    elif word == "SQLITE":
        import sqlite3  # noqa: F401
    elif word == "PYI":
        subprocess.run([sys.executable, "-I", "-c", "pass"], check=True)
    elif word == "SHELL":
        subprocess.run(["cmd", "/c", "exit 0"] if os.name == "nt" else ["/bin/sh", "-c", "true"], check=True)
    elif word == "RW":
        p = os.path.join(here, "branch" + "_state.txt")
        st = os.stat(p)
        with io.open(p, encoding="utf-8") as fh:
            n = int(fh.read().strip() or 0)
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write("%d\n" % ((n + 1) % 10))
        os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns))


class Law(unittest.TestCase):
    def test_subject_is_fine(self):
        word = _subject()
        if word != "fine":
            _branch(word)
        self.assertEqual(word, "fine")


if __name__ == "__main__":
    log = os.environ.get("TRACED_LAW_LOG")
    if log:
        with io.open(log, "a", encoding="utf-8") as fh:
            fh.write("%s|%s\n" % ("subset" if len(sys.argv) > 1 else "full", _subject()))
    unittest.main()
'''
#: a law with a static key: it reads its subject and the shared file by name, lists nothing
_PLAIN = r'''
import io, os, sys, unittest
here = os.path.dirname(os.path.abspath(__file__))


class Law(unittest.TestCase):
    def test_subject_is_fine(self):
        with io.open(os.path.join(here, "plain_subject.txt"), encoding="utf-8") as fh:
            word = fh.read().strip()
        with io.open(os.path.join(here, "shared.txt"), encoding="utf-8") as fh:
            fh.read()
        self.assertEqual(word, "fine")


if __name__ == "__main__":
    log = os.environ.get("TRACED_LAW_LOG")
    if log:
        with io.open(log, "a", encoding="utf-8") as fh:
            fh.write("%s|plain\n" % ("subset" if len(sys.argv) > 1 else "full"))
    unittest.main()
'''
#: a law that changes a file another gate reads, in the same lane's sandbox
_CHANGER = r'''
import io, os, unittest
here = os.path.dirname(os.path.abspath(__file__))


class Law(unittest.TestCase):
    def test_subject_is_fine(self):
        with io.open(os.path.join(here, "shared" + ".txt"), "w", encoding="utf-8") as fh:
            fh.write("changed by another gate, and longer than before\n")
        with io.open(os.path.join(here, "changer_subject.txt"), encoding="utf-8") as fh:
            self.assertEqual(fh.read().strip(), "fine")


if __name__ == "__main__":
    unittest.main()
'''
_GATE, _FILE = "traced-key-fixture", "t_traced_key_law.py"
_PGATE, _PFILE = "traced-plain-fixture", "t_traced_plain_law.py"
_CGATE, _CFILE = "traced-changer-fixture", "t_traced_changer_law.py"
CAUGHT = "Law.test_subject_is_fine"
TRACED = ("OPEN", "IMPORT", "ABSENT", "LIST", "ROOTLIST")
UNTRACED = ("SQLITE", "PYI", "SHELL")


def _proof(word, target="subject.txt"):
    return {"why": word, "file": target, "find": "fine", "replace": word, "matches": 1}


def _no_facts(have, say):
    return None, dict((n, list(range(len(p)))) for n, _f, p in have), [n for n, _f, _p in have], \
        {"anchor": 0, "entry": 0, "target": 0}


class _Patch(object):
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


class _Case(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="traced_key_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.cache_path = os.path.join(self.d, ".heart2_cache.json")
        self.memory = os.path.join(self.d, ".heart2_red.json")
        self.log = os.path.join(self.d, "runs.log")
        self.files = {"tv/control_app.py": "# sandbox marker\n", "tv/" + _FILE: _LAW, "tv/subject.txt": "fine\n",
                      "tv/t_branch_helper.py": "VALUE = 1\n", "tv/branch_data.txt": "data 1\n",
                      "tv/branch_dir/a.txt": "a\n", "tv/branch_state.txt": "1\n", "tv/" + _PFILE: _PLAIN,
                      "tv/plain_subject.txt": "fine\n", "tv/shared.txt": "as copied\n", "tv/" + _CFILE: _CHANGER,
                      "tv/changer_subject.txt": "fine\n"}
        self.roots = []
        e = _Env(HEART2_TRACE="1", HEART2_PROVE_WORKERS="1", HEART2_AUDIT_K="0", HEART2_RED_MEMORY=None,
                 HEART2_RED_PATH=None, TV_LAW_WIDTHS=None, TRACED_LAW_LOG=self.log)
        e.__enter__()
        self.addCleanup(e.__exit__)
        p = _Patch(RED_MEMORY=self.memory, _RED_USED={}, _RED={"path": None, "sig": None, "entries": None,
                                                              "folded": True})
        p.__enter__()
        self.addCleanup(p.__exit__)
        self.addCleanup(lambda: [H._SANDBOXES.discard(r) for r in self.roots])

    def make(self, say=print):
        """make_sandbox's stand-in: a REAL copy heart2 tracks as its sandbox, with its copy-time manifest."""
        root = H._track_sandbox(tempfile.mkdtemp(prefix="tracedbox.", dir=self.d))
        self.roots.append(root)
        repo = os.path.join(root, "repo")
        for rel, text in self.files.items():
            p = os.path.join(repo, *rel.split("/"))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with io.open(p, "w", encoding="utf-8") as fh:
                fh.write(text)
        H._take_manifest(root, repo, say)
        return os.path.join(repo, "tv"), root

    def runs(self):
        if not os.path.exists(self.log):
            return []
        with io.open(self.log, encoding="utf-8") as fh:
            out = [l.strip() for l in fh if l.strip()]
        os.remove(self.log)
        return out

    def entries(self):
        if not os.path.exists(self.cache_path):
            return {}
        with io.open(self.cache_path, encoding="utf-8") as fh:
            return json.load(fh)["entries"]

    def traced(self, gate=_GATE):
        """{proof index: entry} of the traced entries banked for `gate`"""
        return dict((e["proof"], e) for e in self.entries().values() if e.get("kind") == "traced" and e["gate"] == gate)

    def census(self, have):
        said = []
        cache = H._VerdictCache(path=self.cache_path, say=said.append)
        with _Patch(make_sandbox=self.make, _CENSUS=H._CensusRun(cache=cache, red=False)):
            results, _per = H._prove_gates(have, said.append, workers=1)
        return results, self.runs(), said, cache

    def push(self, have):
        said, stopped = [], []
        cache = H._VerdictCache(path=self.cache_path, say=said.append)
        with _Patch(make_sandbox=self.make, _push_facts=_no_facts):
            results, _per = H._prove_push(have, said.append, stopped, cache=cache)
        return results, self.runs(), said, cache


class ATracedKeyIsNeverNarrower(_Case):

    def test_each_read_only_the_tampered_run_makes_moves_its_key_or_untraces_it(self):
        proofs = [_proof(w) for w in TRACED + UNTRACED]
        have = [(_GATE, _FILE, proofs)]
        results, runs, said, cache = self.census(have)
        self.assertEqual(results, {_GATE: H.PROVEN}, "PREMISE: the fixture was not proven:\n%s" % "\n".join(said))
        self.assertTrue(any("not cacheable" in l for l in said), "PREMISE: the fixture law has a static key, so this "
                                                                 "case would not measure the facts alone: %s" % said)
        got = self.traced()
        self.assertEqual(sorted(got), list(range(len(TRACED))), "the proofs banked by their facts are not the ones "
                         "whose runs were all traced: %s\n%s" % (sorted(got), "\n".join(said)))
        for w in UNTRACED:
            self.assertIn("full|%s" % w, runs, "PREMISE: the %s proof's tampered run did not happen: %s" % (w, runs))
        # the same bytes: the traced ones are served, the three untraced ones run again
        results, runs, said, cache = self.census(have)
        self.assertEqual(results, {_GATE: H.PROVEN}, "\n".join(said))
        for w in TRACED:
            self.assertNotIn("full|%s" % w, runs, "a proof banked by its facts ran again over the same bytes: %s\n%s"
                             % (w, "\n".join(said)))
            self.assertTrue(any("%s[%d]" % (_GATE, TRACED.index(w)) in l and "traced" in l and "not re-run" in l
                                for l in said), "the served %s proof does not say it was served by its facts" % w)
        for w in UNTRACED:
            self.assertIn("full|%s" % w, runs, "an UNTRACED proof was served - a read the trace cannot follow was "
                                               "treated as no read: %s" % w)
        self.assertEqual(cache.traced_hits, len(TRACED))
        # move each tampered-branch-only read in turn: that proof - and only that one - runs again
        moves = (("OPEN", "tv/branch_data.txt", "data 2\n"), ("IMPORT", "tv/t_branch_helper.py", "VALUE = 2\n"),
                 ("ABSENT", "tv/branch_flag", "now here\n"), ("LIST", "tv/branch_dir/b.txt", "b\n"),
                 ("ROOTLIST", "rootfile.txt", "the repo copy's root holds one more name\n"))
        for word, rel, text in moves:
            self.files[rel] = text
            results, runs, said, cache = self.census(have)
            self.assertEqual(results, {_GATE: H.PROVEN}, "\n".join(said))
            self.assertIn("full|%s" % word, runs, "moving %s - read only by the %s proof's TAMPERED run - did not move "
                                                  "its key: it was served over a tree it never ran on\n%s"
                          % (rel, word, "\n".join(said)))
            for other in TRACED:
                if other != word:
                    self.assertNotIn("full|%s" % other, runs, "moving %s re-ran the %s proof, which never read it"
                                     % (rel, other))


class AFullCleanRunIsWhatFactsStandOn(_Case):

    def seed(self, gate, proofs):
        for i, pr in enumerate(proofs):
            H._red_remember(H._red_key(gate, i, pr), gate, i, [CAUGHT])

    def test_a_push_that_narrowed_every_proof_banks_by_facts_only_where_a_full_clean_run_paid_for_them(self):
        plain = [_proof("BROKEN", "plain_subject.txt")]
        self.seed(_PGATE, plain)
        results, runs, said, cache = self.push([(_PGATE, _PFILE, plain)])
        self.assertEqual(results, {_PGATE: H.PROVEN}, "\n".join(said))
        self.assertIn("subset|plain", runs, "PREMISE: the push did not narrow the proof: %s" % runs)
        self.assertEqual(self.traced(_PGATE), {}, "a proof with no FULL clean run's facts in its sandbox was banked by "
                                                  "its facts:\n%s" % "\n".join(said))
        self.assertTrue([k for k, e in self.entries().items() if e.get("kind", "static") == "static"
                         and e["gate"] == _PGATE], "the narrowed proof lost its static key")
        self.assertTrue(any("narrowed" in w for w in cache.traced_why), "why it is static only was not counted: %s"
                        % cache.traced_why)
        unkeyable = [_proof("OPEN")]
        self.seed(_GATE, unkeyable)
        results, runs, said, cache = self.push([(_GATE, _FILE, unkeyable)])
        self.assertEqual(results, {_GATE: H.PROVEN}, "\n".join(said))
        self.assertIn("subset|OPEN", runs, "PREMISE: the push did not narrow the proof: %s" % runs)
        self.assertEqual(sorted(self.traced()), [0], "a narrowed proof with no static key was not banked by its facts "
                                                     "after its one full clean run:\n%s" % "\n".join(said))
        self.assertIn("full|fine", runs[runs.index("subset|OPEN"):], "no FULL clean run was paid after the narrowed "
                                                                       "pair - its facts stand on nothing: %s" % runs)


class WhatARunChangedIsNoFact(_Case):

    def test_a_path_read_and_written_and_a_file_another_gate_changed_are_static_only(self):
        results, runs, said, cache = self.census([(_GATE, _FILE, [_proof("RW")])])
        self.assertEqual(results, {_GATE: H.PROVEN}, "\n".join(said))
        self.assertEqual(self.traced(), {}, "a proof whose run read and wrote one path was banked by its facts")
        self.assertTrue(any("read and wrote" in w for w in cache.traced_why), cache.traced_why)
        changer = [{"why": "C", "file": "changer_subject.txt", "find": "fine", "replace": "BROKEN", "matches": 1}]
        plain = [_proof("BROKEN", "plain_subject.txt")]
        results, runs, said, cache = self.census([(_CGATE, _CFILE, changer), (_PGATE, _PFILE, plain)])
        self.assertEqual(results, {_CGATE: H.PROVEN, _PGATE: H.PROVEN}, "\n".join(said))
        self.assertEqual(self.traced(_PGATE), {}, "a proof that read a file an earlier gate changed in its sandbox was "
                                                  "banked by facts no copied tree holds:\n%s" % "\n".join(said))
        self.assertTrue(any("not as the sandbox was copied" in w for w in cache.traced_why), cache.traced_why)
        self.assertTrue([e for e in self.entries().values() if e["gate"] == _PGATE], "it lost its static key")


class AbsentFactsAreAMiss(_Case):

    def test_missing_or_wrong_facts_are_never_served(self):
        have = [(_GATE, _FILE, [_proof("OPEN")])]
        self.census(have)
        (e,) = self.traced().values()
        facts = os.path.join(self.d, ".heart2_facts.%s.json" % e["factsRef"])
        self.assertTrue(os.path.isfile(facts), "PREMISE: no facts record beside the cache")
        results, runs, said, cache = self.census(have)
        self.assertNotIn("full|OPEN", runs, "PREMISE: the traced entry was not served on the same bytes")
        os.remove(facts)
        results, runs, said, cache = self.census(have)
        self.assertIn("full|OPEN", runs, "a traced entry whose facts are MISSING was served")
        self.assertTrue(os.path.isfile(facts), "PREMISE: the re-proof did not bank its facts again")
        # a record that is not the bytes its name says: it lost the fact about the law's own file - and the law is then
        # edited (same size), so only the record's name can tell that it no longer covers what the run read
        with io.open(facts, encoding="utf-8") as fh:
            body = json.load(fh)
        self.assertIn("tv/" + _FILE, body["facts"]["R"], "PREMISE: the shared facts do not hold the law's own bytes")
        body["facts"]["R"].pop("tv/" + _FILE)
        with io.open(facts, "w", encoding="utf-8") as fh:
            json.dump(body, fh)
        self.files["tv/" + _FILE] = _LAW.replace("EDITION = 1", "EDITION = 2")
        results, runs, said, cache = self.census(have)
        self.assertIn("full|OPEN", runs, "a traced entry whose facts are not the bytes their name says was served - "
                                         "over a law edited since:\n%s" % "\n".join(said))


class AGitLessTreeAsksGitNothing(unittest.TestCase):

    def test_a_tree_with_no_git_reachable_is_unknown_without_a_git_child(self):
        """★ a heart2 sandbox has no .git, and every law that builds a verdict cache asked `git ls-files` there: a traced
        run can only note that child as a fact no git-less tree can measure, so not one such law was ever banked by its
        facts. Where no .git is reachable the answer is UNKNOWN (None) without the child; where one is, git is asked"""
        calls = []
        real = H.subprocess.run

        def spy(cmd, *a, **k):
            calls.append(list(cmd) if isinstance(cmd, (list, tuple)) else [cmd])
            return real(cmd, *a, **k)

        d = tempfile.mkdtemp(prefix="gitless_")
        self.addCleanup(shutil.rmtree, d, True)
        H.subprocess.run = spy
        try:
            self.assertIsNone(H._tracked_files(d), "a git-less tree read as one git lists")
            self.assertEqual([c for c in calls if c[:1] == ["git"]], [], "a tree with no .git reachable was asked by git")
            os.makedirs(os.path.join(d, "sub"))
            with io.open(os.path.join(d, ".git"), "w", encoding="utf-8") as fh:
                fh.write("gitdir: %s\n" % os.path.join(d, "nowhere"))         # a .git ABOVE the tree: git's discovery
            H._tracked_files(os.path.join(d, "sub"))
        finally:
            H.subprocess.run = real
        self.assertTrue([c for c in calls if c[:1] == ["git"]], "a tree with a .git above it was never asked - the "
                                                                "check is not where git's own discovery looks")


RED_PROOF = [
    {"why": "REG-2440 - the key is taken from the gate's clean runs only: a read only the tampered run made is no fact",
     "file": "heart2.py",
     "find": "    own = [r[\"rec\"] for r in p.runs] + [{\"v\": shared[\"v\"], \"R\": {p.tgt_rel: p.clean_sha}}]   # "
             "the target's clean bytes\n",
     "replace": "    own = [{\"v\": shared[\"v\"], \"R\": {p.tgt_rel: p.clean_sha}}]   # the target's clean bytes\n",
     "matches": 1},
    {"why": "REG-2440 - a run the trace could not follow (a U line, an untraced child) is accepted as one that read "
            "nothing more",
     "file": "heart2.py",
     "find": "        sink.bad = sink.bad or ((info or {}).get(\"why\") or \"a run was not traced\")\n",
     "replace": "        pass\n",
     "matches": 1},
    {"why": "REG-2440 - a proof is banked by its facts with no FULL clean run's facts under them",
     "file": "heart2.py",
     "find": "    if why is None and not g.clean:\n        why = _trace_full_clean(g, say, unkeyable)               # "
             "TRACED-NEEDS-A-FULL-CLEAN-RUN\n    if why is None and not g.clean:\n        why = \"no full clean run "
             "of its gate gave facts\"\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2440 - a traced entry whose facts are missing or unreadable is served anyway",
     "file": "heart2.py",
     "find": "        if shared is None or not isinstance(own, dict):          # TRACED-ABSENT-FACTS-MISS\n"
             "            continue\n",
     "replace": "        if shared is None or not isinstance(own, dict):          # TRACED-ABSENT-FACTS-MISS\n"
                "            return k, e\n",
     "matches": 1},
    {"why": "REG-2440 - a facts record is read without checking its bytes against its name",
     "file": "heart2.py",
     "find": "    if not isinstance(rec, dict) or _facts_ref(rec) != ref:     # FACTS-NAMED-BY-THEIR-BYTES\n",
     "replace": "    if not isinstance(rec, dict):     # FACTS-NAMED-BY-THEIR-BYTES\n",
     "matches": 1},
    {"why": "REG-2440 - a path the runs read AND wrote is banked as a fact",
     "file": "heart2.py",
     "find": "    why = _read_and_written(full, written) or _not_as_copied(g, full)\n",
     "replace": "    why = _not_as_copied(g, full)\n",
     "matches": 1},
    {"why": "REG-2440 - a fact measured on a file an earlier gate changed in the sandbox is banked",
     "file": "heart2.py",
     "find": "    why = _read_and_written(full, written) or _not_as_copied(g, full)\n",
     "replace": "    why = _read_and_written(full, written)\n",
     "matches": 1},
    {"why": "REG-2440 - the repo copy's root is no entry of the copy-time manifest: a fact on it reads as a changed tree",
     "file": "heart2.py",
     "find": "        out[\"\"] = _mkind(os.lstat(repo)) + (os.lstat(repo).st_mtime_ns,)    # the root itself: facts name it "
             "as \"\"\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2440 - the root counts itself among its own names: a listing of it never matches the copy",
     "file": "heart2.py",
     "find": "            if rel and leaf != \"__pycache__\":                     # \"\" is the root itself, never a row "
             "of it\n",
     "replace": "            if leaf != \"__pycache__\":                     # \"\" is the root itself, never a row "
                "of it\n",
     "matches": 1},
    {"why": "REG-2440 - a git-less tree asks git anyway: every law building a verdict cache gets a fact no sandbox can "
            "measure, and none of them is ever banked by its facts",
     "file": "heart2.py",
     "find": "    if not _git_reachable(repo):\n",
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "REG-2440 - a tampered run is filed as a clean one: the target's tampered bytes become the gate's fact",
     "file": "heart2.py",
     "find": "    tampered = False\n    if p is not None and p.tgt and p.clean_sha:\n",
     "replace": "    tampered = False\n    if False:\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
