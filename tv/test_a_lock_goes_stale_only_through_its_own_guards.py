# -*- coding: utf-8 -*-
"""#156 (REG-2750, his ruling 2026-10-28) - A LOCK GOES STALE ONLY THROUGH ITS OWN GUARD LAWS.

"do whatever is needed.. if needs to be rep-proving and build-per lock then do it." The old rule closed every lock on one
fact about the whole tree: any gate file changed since the census ran. So any law edited anywhere shut frame.release -
the river's lock, an act with no undo - on every PC until a full re-prove (#193). When the global rule calls the census
STALE, a lock that declares its door (self_arming.LOCK_DOORS) now answers from the gates that guard IT - those whose
source names the lock or directly imports or opens its door module or the lock machinery. A guard owed a proof makes it
STALE (the reason is the global one plus which of its guards are owed; the v3042 rule still decides what STALE permits).
Anything else in the tree does not decide it.

⚠ BLIND IS NOT STALE (his 2026-09-12 ruling, test_a_stale_prover_is_not_a_safety_verdict): a recorded BLIND closes every
lock, per-lock or not. The first cut of this law let an unrelated BLIND open the river; CI caught the contradiction.
A lock with no declared door, every route, an unreadable census, a global refusal that is not STALE, and a law that
seats the global answer all keep the global rule.

Driven on a fixture census (TV_HEART_CENSUS) built from the gate files on disk, so his census is never read. RED_PROOF below.
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import fixture_tmp as _fx  # noqa: E402
_fx.contain()
import heart2 as H  # noqa: E402
import self_arming as SA  # noqa: E402

FILES = dict(H.gate_files())
SHAS = H.gate_shas()


def _text(name):
    f = FILES[name]
    with open(f if os.path.isabs(f) else os.path.join(H.HERE, f), encoding="utf-8") as fh:
        return fh.read()


def _guards(lock):
    return set(n for n in FILES if SA._guards_lock(_text(n), lock, SA.LOCK_DOORS[lock]))


DECLARING = set(n for n in FILES if H.red_proofs_in(FILES[n]))
PRINTER, ROUTE, FRAME = "printer.stream", "reel.route", "frame.release"
G_PRINTER, G_ROUTE, G_FRAME = _guards(PRINTER), _guards(ROUTE), _guards(FRAME)
ONLY_PRINTER = sorted((G_PRINTER - G_ROUTE - G_FRAME) & DECLARING)
ONLY_ROUTE = sorted((G_ROUTE - G_PRINTER - G_FRAME) & DECLARING)
NEITHER = sorted(DECLARING - G_PRINTER - G_ROUTE - G_FRAME)


class ALockGoesStaleOnlyThroughItsOwnGuards(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="per_lock_")
        self.path = os.path.join(self.d, ".heart2.json")
        self._env = os.environ.get("TV_HEART_CENSUS")
        os.environ["TV_HEART_CENSUS"] = self.path
        SA._LOCK_MEMO.update(key=None)

    def tearDown(self):
        if self._env is None:
            os.environ.pop("TV_HEART_CENSUS", None)
        else:
            os.environ["TV_HEART_CENSUS"] = self._env
        SA._LOCK_MEMO.update(key=None)

    def census(self, owed=(), blind=(), current=False):
        """Every gate proven against the files on disk, with `owed` given a sha that no longer matches and `blind` filed
        BLIND. current=False stamps a fingerprint the tree does not have (the global rule reads STALE); current=True
        stamps the tree's own, so a BLIND is the global answer - and BLIND never softens, which is what lets a case
        see whether may() asked the lock's own guards."""
        shas = dict(SHAS)
        for n in owed:
            shas[n] = "0" * 16
        st = {"gatesFingerprint": (H.gates_fingerprint() if current else "f" * 32), "gateShas": shas, "provedGates": sorted(FILES), "blind": list(blind),
              "proved": len(FILES), "declared": len(DECLARING), "total": len(FILES), "sliceOwed": len(owed)}
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(st, fh)
        SA._LOCK_MEMO.update(key=None)

    def test_the_premise_two_locks_with_their_own_guards(self):
        self.assertTrue(ONLY_PRINTER and ONLY_ROUTE and NEITHER,
                        "PREMISE: the tree has no gate that guards one lock and not the other: %d / %d / %d"
                        % (len(ONLY_PRINTER), len(ONLY_ROUTE), len(NEITHER)))
        self.census()
        ok, why = SA._heart_says_watched()
        self.assertFalse(ok, "PREMISE: the fixture census is not stale to the global rule: %r" % why)

    def test_a_change_elsewhere_leaves_a_lock_watched(self):
        self.census(owed=NEITHER[:5])
        for lock in (PRINTER, ROUTE, FRAME):
            ok, why = SA._lock_heart(lock)
            self.assertTrue(ok, "%s closed over gates that do not guard it: %s" % (lock, why))

    def test_may_asks_the_rivers_lock_its_own_guards(self):
        """frame.release has no undo, so a STALE answer refuses it outright (v3042): it is the case that shows whether
        may() took the per-lock answer or the global one."""
        self.assertTrue(SA.LOCKS[FRAME].get("destructive"), "PREMISE: frame.release is no longer an act with no undo")
        self.census(owed=NEITHER[:5])
        self.assertNotIn(SA._HEART_STALE_PHRASE, SA.may(FRAME)[1],
                         "may() still refuses the river's lock over gates that do not guard it")

    def test_a_BLIND_anywhere_still_closes_every_lock(self):
        """His 2026-09-12 ruling: BLIND is not STALE. Per-lock narrows STALE only."""
        for current in (True, False):
            self.census(owed=NEITHER[:3], blind=NEITHER[3:4], current=current)
            for lock in (PRINTER, ROUTE, FRAME):
                self.assertIsNone(SA._lock_heart(lock), "a recorded BLIND was answered per lock (%s, current=%s)"
                                  % (lock, current))
            self.assertFalse(SA.may(FRAME)[0], "the river's lock opened beside a recorded BLIND (current=%s)" % current)

    def test_its_own_guard_owed_makes_only_that_lock_stale(self):
        self.census(owed=[ONLY_PRINTER[0]])
        ok, why = SA._lock_heart(PRINTER)
        self.assertFalse(ok, "a changed guard of printer.stream left it watched")
        self.assertEqual(SA.heart_block_kind(why), "stale", why)
        self.assertIn(ONLY_PRINTER[0], why, "the reason does not name the guard that changed")
        self.assertIn("PROOF census is STALE (not the Heart panel's live census)", why,
                      "the per-lock reason lost the global words its readers match on (REG-2073)")
        self.assertTrue(SA._lock_heart(ROUTE)[0], "a guard of printer.stream made reel.route stale too")

    def test_the_padlock_reads_what_the_act_reads(self):
        self.census(owed=NEITHER[:5])
        rows = {r["lock"]: r for r in SA.report().get("locks", [])}
        self.assertNotIn(SA._HEART_STALE_PHRASE, rows[FRAME].get("permittedWhy") or "",
                         "the report refused frame.release over gates that do not guard it while may() did not")

    def test_a_lock_with_no_declared_door_keeps_the_global_rule(self):
        self.census(owed=NEITHER[:1])
        undeclared = [k for k in list(SA.LOCKS) + list(SA.ROUTES) if k not in SA.LOCK_DOORS]
        self.assertTrue(undeclared, "PREMISE: every lock and route declares a door")
        self.assertIsNone(SA._lock_heart(undeclared[0]))

    def test_an_unreadable_census_gives_no_per_lock_answer(self):
        with open(self.path, "w") as fh:
            fh.write("{not json")
        SA._LOCK_MEMO.update(key=None)
        self.assertIsNone(SA._lock_heart(PRINTER), "a census that will not parse opened a lock")

    def test_a_law_that_seats_the_global_answer_gets_the_global_rule(self):
        self.census(owed=NEITHER[:1])
        real = SA._heart_says_watched
        try:
            SA._heart_says_watched = lambda: (False, "the heart2 PROOF census is STALE (not the Heart panel's live census)"
                                                     ": the gate files have changed (x != y).")
            self.assertIsNone(SA._lock_heart(FRAME), "a law that seated the global answer was answered per lock")
            self.assertIn(SA._HEART_STALE_PHRASE, SA.may(FRAME)[1])
        finally:
            SA._heart_says_watched = real


RED_PROOF = [
    {"why": "REG-2750 - may() never asks the lock's own guards (any law edited shuts the river again)",
     "file": "self_arming.py",
     "find": "        _per = _lock_heart(lock, _hwhy)\n        if _per is not None:\n            _hok, _hwhy = _per\n",
     "replace": "        _per = None\n",
     "matches": 1},
    {"why": "REG-2750 - no gate guards any lock, so a changed guard is ignored",
     "file": "self_arming.py",
     "find": "    if not text:\n        return False\n    if ('\"%s\"' % lock) in text",
     "replace": "    return False\n    if ('\"%s\"' % lock) in text",
     "matches": 1},
    {"why": "REG-2750 - every gate guards every lock (the old global rule wearing per-lock words)",
     "file": "self_arming.py",
     "find": "    if not text:\n        return False\n    if ('\"%s\"' % lock) in text",
     "replace": "    return True\n    if ('\"%s\"' % lock) in text",
     "matches": 1},
    {"why": "REG-2750 - the report's padlock keeps the global answer while may() asks the lock",
     "file": "self_arming.py",
     "find": "    if heart and heart[0]:\n        return heart\n    try:\n        per = _lock_heart(lock, heart[1] if heart else None)",
     "replace": "    if True:\n        return heart\n    try:\n        per = _lock_heart(lock, heart[1] if heart else None)",
     "matches": 1},
    {"why": "REG-2750 - a law that seats the global answer gets a per-lock answer instead",
     "file": "self_arming.py",
     "find": "    if lock not in LOCK_DOORS or _heart_says_watched is not _HEART_SAYS_WATCHED_REAL:",
     "replace": "    if lock not in LOCK_DOORS:",
     "matches": 1},
    {"why": "REG-2750 - a recorded BLIND is answered per lock (his 2026-09-12 ruling: BLIND is not STALE)",
     "file": "self_arming.py",
     "find": "    if owed is None or blind:\n        return None\n",
     "replace": "    if owed is None:\n        return None\n",
     "matches": 1},
    {"why": "REG-2750 - the per-lock reason drops the global words its readers match on",
     "file": "self_arming.py",
     "find": "                       % (str(gwhy).rstrip(), lock, len(g_owed), \", \".join(g_owed[:3])))\n",
     "replace": "                       % (\"stale for this lock.\", lock, len(g_owed), \", \".join(g_owed[:3])))\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
