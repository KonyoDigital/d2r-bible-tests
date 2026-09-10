# -*- coding: utf-8 -*-
"""v2692 — THE TWO DISK CACHES MUST NEVER OUTLIVE THEIR EVIDENCE.

frame_authority.test_referenced_reels() and chronicle_routes.routes() each persist their answer to
disk so a FRESH process does not re-derive it. That took /api/heart cold from 19.54s to 5.54s, which
is what let the render gate open the heart panel inside its 12s activate poll again.

⚠ THE RISK THIS GUARDS. A cache that answers from a key it did not verify is [[stale-reading]] with
a speedup attached — and both of these decide things that matter: which reels the TEST SUITE names
(a fixture reel is HELD from pruning) and which chronicle routes exist. A stale "this reel is a
fixture" holds footage forever; a stale "it is not" is worse.

The rule both follow: the disk key is the SAME key the in-memory memo already trusted — the fixture
files' (path,size,mtime) for one, newest-mtime + file-count for the other. So these tests do not
invent a freshness rule; they prove the stored one is actually CHECKED rather than assumed.
"""
import json
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


class _CacheContract(object):
    """Shared body: a wrong key must be REFUSED, not served."""

    path = None      # set by subclass
    poison = None    # a value the real derivation could never produce

    def _call(self):
        raise NotImplementedError

    def _drop_memo(self):
        raise NotImplementedError

    def setUp(self):
        """⚠⚠ EACH LAW STARTS FROM NOTHING, OR IT CAN GO RED FOR THE PREVIOUS LAW'S REASON.

        There was no setUp and no tearDown, and unittest runs WRONG_key before corrupt. Measured
        2026-09-10 with the key comparison removed from frame_authority.py:

            test_a_cache_with_the_WRONG_key_is_never_served, ALONE -> FAILED   (its own subject)
            test_a_corrupt_cache_fails_OPEN,                 ALONE -> OK       (never reddens)
            both in sequence                                       -> FAILED (failures=2)

        The second red was leftover state: WRONG_key writes a poison blob, the weakened serve path
        returns it early and never rewrites the good cache, and the memo — keyed on the test file's
        (size, mtime), not on the cache file — carries that poison into the next test, which calls
        _call() BEFORE _drop_memo(). Corrupt JSON still dies in json.load and still fails open; the
        key comparison is never reached on that path.

        A gate that reddens for the wrong reason is the mirror of a green sabotage: it looks like
        coverage and is not. Dropping BOTH the memo and the cache file gives every law a clean
        slate, so a red here means that law's own subject broke.
        [[feedback-fixtures-never-touch-live-data]] [[sabotage-is-usually-the-wrong-one]]
        """
        self._drop_memo()
        try:
            if self.path and os.path.exists(self.path):
                os.remove(self.path)
        except OSError:
            pass                      # unwritable venue: the laws below skip on their own

    def test_a_cache_with_the_WRONG_key_is_never_served(self):
        real = self._call()          # populates memo + disk with the correct key
        self.assertTrue(real, "the derivation returned nothing — this test measures NOTHING")
        try:
            with open(self.path, "w", encoding="utf-8") as fh:
                json.dump({"key": "not-the-current-key", **self.poison}, fh)
        except OSError as e:
            self.skipTest("cache path not writable here: %s" % e)
        self._drop_memo()
        again = self._call()
        self.assertEqual(again, real,
                         "a cache file carrying a key that does not match the tree was SERVED — "
                         "that is a stale answer with a speedup attached, and both of these "
                         "decide what may be deleted")

    def test_the_cache_it_writes_carries_a_key(self):
        self._call()
        self.assertTrue(os.path.isfile(self.path), "nothing was written, so nothing is cached")
        with open(self.path, encoding="utf-8") as fh:
            blob = json.load(fh)
        self.assertTrue(str(blob.get("key") or ""),
                        "the cache was written WITHOUT a key — it could then never be invalidated")

    def test_a_corrupt_cache_fails_OPEN(self):
        """A cache that can break the answer is worse than no cache."""
        real = self._call()
        try:
            with open(self.path, "w", encoding="utf-8") as fh:
                fh.write("{ this is not json")
        except OSError as e:
            self.skipTest("cache path not writable here: %s" % e)
        self._drop_memo()
        self.assertEqual(self._call(), real,
                         "a corrupt cache changed the answer instead of being ignored")


class FixtureReelsCache(_CacheContract, unittest.TestCase):
    path = os.path.join(HERE, ".fixture_reels_cache.json")
    poison = {"reels": ["reel_s_0000000000_0"]}

    def _call(self):
        import frame_authority as FA
        return FA.test_referenced_reels()

    def _drop_memo(self):
        import frame_authority as FA
        FA.__dict__.pop("_FIXTURE_CACHE", None)


class ChronicleRoutesCache(_CacheContract, unittest.TestCase):
    path = os.path.join(HERE, ".chronicle_routes_cache.json")
    poison = {"val": {"ok": True, "why": "", "routes": [], "counts": {}, "flags": []}}

    def _call(self):
        import chronicle_routes as CR
        return CR.routes()

    def _drop_memo(self):
        import chronicle_routes as CR
        CR._MEMO["key"] = None
        CR._MEMO["val"] = None


RED_PROOF = [
    {
        'why': 'dropping the key comparison serves a disk cache whose key no longer matches the tree — a stale answer with a speedup attached, from a cache that decides what may be DELETED. Verified: untampered OK, tampered FAILED, reddened law test_a_cache_with_the_WRONG_key_is_never_served. ⚠⚠ THE FIRST WORDING OF THIS why WAS WRONG AND A CROSS-FAMILY REVIEW CAUGHT IT. It claimed BOTH FixtureReelsCache laws reddened. Measured by running each ALONE under the same tamper: the wrong-key law FAILED, the corrupt law came back OK. test_a_corrupt_cache_fails_OPEN reddens only IN SEQUENCE — with the key check gone the wrong-key test serves the poison blob and returns early, never rewriting the good cache and leaving _FIXTURE_CACHE poisoned; there is no tearDown, and the corrupt test calls _call() BEFORE _drop_memo(), so it reads that poison. Corrupt JSON still dies in json.load and still fails open — the key comparison is never reached. That second red is leftover process state, not the fail-open law catching anything, and naming it was the mis-attribution this discipline exists to prevent. FIXED in the same version: _CacheContract.setUp now drops the memo AND removes the cache file, so every law starts from nothing. Re-measured under the same tamper — failures went 2 -> 1 and the only reddened law is test_a_cache_with_the_WRONG_key_is_never_served.',
        'file': 'frame_authority.py',
        'find': '_blob.get("key") == _ckey and ',
        'replace': '',
        'matches': 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
