# -*- coding: utf-8 -*-
"""REG-2434 (#186 f) - A REUSED PROVEN IS AUDITED: REUSE MUST NEVER BE THE ONLY WITNESS.

Before #186 the census re-proved every proof, so a PROVEN wrongly banked by a push was found at the next census. Once the
census reuses what the cache holds (REG-2433), nothing would ever look at a banked verdict again - one bad entry (an
under-wide proof, a key that missed an input) would stand for as long as its bytes do. So every run - census and push -
re-proves the HEART2_AUDIT_K (default 2) SERVED PROVENs with the OLDEST provedAt, over the bytes it served them for:
narrowed where the red memory names the cases, else in full.

Driven through the REAL prove() / _prove_push / _prove_gates / _prove_gate_census / audit_served / _prove_one over a
throwaway fixture tree; the verdict cache is this law's file and the red memory is closed:
  1. a planted PROVEN for a proof whose law is BLIND is served, audited, found BLIND: the entry leaves the store FILE,
     a ⚠ line names it, the census's verdict for the gate is BLIND and its record counts the contradiction;
  2. a sound served PROVEN is audited PROVEN and kept - auditedCount 1, no contradiction;
  3. HEART2_AUDIT_K=0 audits nothing and SAYS "not audited" - a 0 never reads as clean;
  4. the K picked are the OLDEST served, and bytes that moved since the serve are not an audit;
  5. a push that serves the planted entry is refused on its audit.
RED_PROOF below.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2 as H  # noqa: E402
import prove_record as PR  # noqa: E402

#: the fixture law: Catches.test_catch reddens on "BROKEN"; nothing in it looks at the word "here", so a proof that
#: tampers "here" is BLIND - the planted under-wide entry claims PROVEN for exactly that one.
_LAW = r'''
import io, os, sys, unittest
here = os.path.dirname(os.path.abspath(__file__))
SUBJECT = os.path.join(here, "sub" + "ject.txt")


def _subject():
    with io.open(SUBJECT, encoding="utf-8") as fh:
        return fh.read()


class Catches(unittest.TestCase):
    def test_catch(self):
        self.assertNotIn("BROKEN", _subject())


if __name__ == "__main__":
    log = os.environ.get("AUDIT_LAW_LOG")
    if log:
        with io.open(log, "a", encoding="utf-8") as fh:
            fh.write("run\n")
    unittest.main()
'''
_GATE, _FILE = "audit-fixture", "t_audit_law.py"
SOUND = {"why": "sound", "file": "subject.txt", "find": "fine", "replace": "BROKEN", "matches": 1}
BLIND_ONE = {"why": "under-wide", "file": "subject.txt", "find": "here", "replace": "THERE", "matches": 1}


def _quiet(*a, **k):
    pass


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
        self.d = tempfile.mkdtemp(prefix="audit_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.cache_path = os.path.join(self.d, ".heart2_cache.json")
        self.log = os.path.join(self.d, "runs.log")
        self.subject = "all fine here\n"
        self.audit_subject = None                 # the bytes the AUDIT's sandbox gets (None: the same)
        self.made = 0
        e = _Env(HEART2_RED_MEMORY="0", HEART2_PROVE_WORKERS="1", TV_LAW_WIDTHS=None, AUDIT_LAW_LOG=self.log,
                 HEART2_AUDIT_K=None)
        e.__enter__()
        self.addCleanup(e.__exit__)

    def make(self, say=print):
        self.made += 1
        root = tempfile.mkdtemp(prefix="auditbox.", dir=self.d)
        repo = os.path.join(root, "repo")
        subject = self.audit_subject if (self.audit_subject and self.made > 1) else self.subject
        for rel, text in (("tv/control_app.py", "# sandbox marker\n"), ("tv/" + _FILE, _LAW),
                          ("tv/subject.txt", subject)):
            p = os.path.join(repo, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with io.open(p, "w", encoding="utf-8") as fh:
                fh.write(text)
        return os.path.join(repo, "tv"), root

    def plant(self, proofs, ages_h=None):
        """Bank a stamped every-width PROVEN for each proof, as a push would have - aged `ages_h` hours."""
        tv, _root = self.make()
        self.made = 0
        c = H._VerdictCache(path=self.cache_path, say=_quiet)
        keys = []
        for i, pr in enumerate(proofs):
            k, _rels, why = c.key_for(tv, _GATE, _FILE, pr)
            self.assertIsNotNone(k, "PREMISE: the fixture is not keyable: %s" % why)
            at = int((time.time() - 3600 * ((ages_h or {}).get(i, 1))) * 1000)
            c.store(k, {"verdict": H.PROVEN, "gate": _GATE, "proof": i, "why": pr["why"], "at": "",
                        "mode": "every-width", "by": "push", "provedAt": at, "target": "subject.txt", "tree": H.TREE_ID})
            keys.append(k)
        self.assertTrue(c.flush(), "PREMISE: the planted entries were not written")
        return keys

    def entries(self):
        with io.open(self.cache_path, encoding="utf-8") as fh:
            return json.load(fh)["entries"]

    def runs(self):
        if not os.path.exists(self.log):
            return 0
        with io.open(self.log, encoding="utf-8") as fh:
            n = len([l for l in fh if l.strip()])
        os.remove(self.log)
        return n

    def census(self, proofs):
        """prove() as a census with this law's cache handed in (the audit and the record run at its end)."""
        said = []
        self.made = 0                               # the lane's sandbox is the first one built; the audit's comes after
        cache = H._VerdictCache(path=self.cache_path, say=said.append)
        with _Patch(gate_files=lambda say=None: [(_GATE, _FILE)], red_proofs_in=lambda f: list(proofs),
                    red_proof_unreadable=lambda f: False, make_sandbox=self.make, _write_state=lambda *a, **k: None,
                    _census_snapshot=lambda gates=None: None):
            results = H.prove(only={_GATE}, say=said.append, stamp=False, stores={"cache": cache, "red": False})
        return results, cache, said, H._PUSH_RECORD.get("record")


class AServedProvenIsAudited(_Case):

    def test_a_planted_under_wide_proven_is_caught_evicted_and_named(self):
        (k,) = self.plant([BLIND_ONE])
        results, cache, said, rec = self.census([BLIND_ONE])
        self.assertEqual(results, {_GATE: H.BLIND},
                         "a served PROVEN whose law is BLIND stood - reuse was the only witness:\n%s" % "\n".join(said))
        self.assertNotIn(k, self.entries(), "the contradicted entry is still in the store file - the next run serves it")
        self.assertTrue(any("⚠" in l and "AUDIT CONTRADICTION" in l and "%s[0]" % _GATE in l for l in said),
                        "the contradiction was not said with a ⚠ line naming the proof: %s" % said)
        self.assertEqual(rec and rec.get("cacheContradictions"), [[_GATE, 0, H.BLIND]],
                         "the census record does not count the contradiction: %s" % (rec,))
        self.assertEqual(rec.get("auditedCount"), 1)
        self.assertEqual(rec.get("mode"), "census")
        row = [r for r in rec["perProof"] if r["g"] == _GATE][0]
        self.assertEqual((row.get("a"), (row.get("audit") or {}).get("v")), ("hit", H.BLIND),
                         "an audit is filed as the served proof's re-proof, never as a run of it: %s" % row)
        self.assertEqual(rec.get("proveOnceViolations"), [], "an audit was counted as a prove-once violation")

    def test_a_sound_served_proven_is_audited_and_kept(self):
        (k,) = self.plant([SOUND])
        results, cache, said, rec = self.census([SOUND])
        self.assertEqual(results, {_GATE: H.PROVEN}, "\n".join(said))
        self.assertIn(k, self.entries(), "a corroborated entry was evicted")
        self.assertEqual((rec.get("auditedCount"), rec.get("cacheContradictions")), (1, []), rec)
        self.assertGreaterEqual(self.runs(), 2, "PREMISE: the audit ran nothing")

    def test_an_audit_of_zero_says_not_audited_never_clean(self):
        self.plant([SOUND])
        with _Env(HEART2_AUDIT_K="0"):
            results, cache, said, rec = self.census([SOUND])
        self.assertEqual(self.runs(), 0, "HEART2_AUDIT_K=0 still re-proved a served proof")
        self.assertTrue(any("NOT AUDITED" in l for l in said), "an audit of none was not said as NOT AUDITED: %s" % said)
        self.assertEqual(rec.get("auditedCount"), 0)
        line = PR.table([rec])[1]
        self.assertNotIn(" 0/0 ", line, "the record table reads a run that audited nothing as audited and clean: %s"
                         % line)

    def test_the_oldest_served_are_picked_and_moved_bytes_are_no_audit(self):
        keys = self.plant([SOUND, BLIND_ONE], ages_h={0: 48, 1: 1})
        with _Env(HEART2_AUDIT_K="1"):
            results, cache, said, rec = self.census([SOUND, BLIND_ONE])
        self.assertEqual(results, {_GATE: H.PROVEN}, "with K=1 only the OLDEST (sound) proof is re-proved: %s"
                         % "\n".join(said))
        self.assertEqual(rec.get("auditedCount"), 1, rec)
        self.assertIn(keys[1], self.entries())
        self.audit_subject = "all fine here!\n"
        results, cache, said, rec = self.census([SOUND, BLIND_ONE])
        self.assertTrue(any("bytes moved since it was served - not audited" in l for l in said), said)
        self.assertEqual(rec.get("auditedCount"), 0, "an audit over other bytes was counted: %s" % rec)


class APushIsRefusedOnItsAudit(_Case):

    def test_a_push_serving_a_contradicted_proven_is_refused(self):
        self.plant([BLIND_ONE])
        said, stopped = [], []
        cache = H._VerdictCache(path=self.cache_path, say=said.append)
        with _Patch(make_sandbox=self.make, _push_facts=_no_facts):
            results, _per = H._prove_push([(_GATE, _FILE, [BLIND_ONE])], said.append, stopped, cache=cache)
        self.assertEqual(results, {_GATE: H.BLIND}, "the push passed a served PROVEN its audit found BLIND:\n%s"
                         % "\n".join(said))
        self.assertTrue(stopped, "the push was not refused on its audit's contradiction")
        self.assertEqual(H.prove_exit_code(results)[0], 1)


RED_PROOF = [
    {"why": "REG-2434 - no served PROVEN is ever re-proved: a wrongly banked verdict stands for as long as its bytes",
     "file": "heart2.py",
     "find": "    picks = pool[:k]\n",
     "replace": "    picks = []\n",
     "matches": 1},
    {"why": "REG-2434 - a contradicted entry stays in the store: the next run serves the same false PROVEN",
     "file": "heart2.py",
     "find": "                cache.evict(key, \"%s re-proved %s over the bytes it was banked for\" % (label, v))\n",
     "replace": "                pass\n",
     "matches": 1},
    {"why": "REG-2434 - the audit's BLIND is said but the gate keeps its served PROVEN",
     "file": "heart2.py",
     "find": "                    results[name] = BLIND if BLIND in (v, results.get(name)) else v\n",
     "replace": "                    pass\n",
     "matches": 1},
    {"why": "REG-2434 - the audit picks the NEWEST served proofs: the oldest verdicts are never looked at again",
     "file": "heart2.py",
     "find": "                          for a, n, i, key, f, pr, by in cache.served))\n",
     "replace": "                          for a, n, i, key, f, pr, by in cache.served), reverse=True)\n",
     "matches": 1},
    {"why": "REG-2434 - a push never audits: it serves a BLIND law's banked PROVEN and passes",
     "file": "heart2.py",
     "find": "                for _cn, _ci, _cv in audit_served(cache, results, per_proof, say, run=run):\n",
     "replace": "                for _cn, _ci, _cv in []:\n",
     "matches": 1},
    {"why": "REG-2434 - an audit over bytes that moved since the serve is counted as an audit",
     "file": "heart2.py",
     "find": "            if again != key:\n                say(\"     %-52s   ↳ REG-2434 AUDIT: its bytes moved since it was served",
     "replace": "            if False:\n                say(\"     %-52s   ↳ REG-2434 AUDIT: its bytes moved since it was served",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
