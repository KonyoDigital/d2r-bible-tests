"""v1941 — THE GATE MEMO MUST BE FAST, AND IT MUST NEVER BE WRONG.

Konyo clicked the Vault Accumulator and got "grouping frames…" that never came back. Not a loop —
arithmetic. vault_scan_cost() probes every frame through stash_screen_open(), a crop plus an OCR.
MEASURED on his own film: 0.118s x 3749 frames across 1065 sealed reels = ~7.4 MINUTES, no progress,
no timeout, behind a button labelled "tap to price it · costs nothing". It cost minutes, not money.

Sealed frames are immutable, so the verdict is memoised. The SPEED half is the easy half. The half
that matters is INVALIDATION: a stale "stash" on a frame that is not one sends the sweep to read a
gameplay screen as a stash page, and vault_retro names that cost itself — "a rune tab misread as
'inventory' files his runes in the wrong lane, which merge-max then makes permanent."

So: keyed on (size, mtime), and a miss must be preferred to a guess in every direction.
"""
import json
import os
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
_TMP = tempfile.mkdtemp(prefix="gatecache_")
# BEFORE the import — the path is bound at module load. A fixture that touches his real cache
# would be the "fixtures never touch live data" scar all over again.
os.environ["TV_GATE_CACHE"] = os.path.join(_TMP, "cache.json")
sys.path.insert(0, HERE)
import control_app as ca  # noqa: E402


class TestGateCache(unittest.TestCase):
    def setUp(self):
        ca._GATE_CACHE = None
        ca._GATE_CACHE_DIRTY = False
        try:
            os.remove(os.environ["TV_GATE_CACHE"])
        except OSError:
            pass

    def _frame(self, body=b"not-an-image"):
        p = os.path.join(_TMP, "f%d.jpg" % time.time_ns())
        with open(p, "wb") as f:
            f.write(body)
        return p

    def test_it_is_isolated_from_his_real_cache(self):
        self.assertTrue(ca._GATE_CACHE_PATH.startswith(_TMP),
                        "the memo path escaped the fixture: %s" % ca._GATE_CACHE_PATH)

    def test_second_look_agrees_with_the_first(self):
        p = self._frame()
        a = ca.stash_screen_open_cached(p)
        b = ca.stash_screen_open_cached(p)
        self.assertEqual(a, b)
        self.assertEqual(a, ca.stash_screen_open(p), "the memo disagrees with the gate itself")

    def test_it_survives_a_restart(self):
        p = self._frame()
        a = ca.stash_screen_open_cached(p)
        ca._gate_cache_flush()
        ca._GATE_CACHE = None                     # a fresh process reads it back off disk
        self.assertEqual(ca.stash_screen_open_cached(p), a)
        with open(ca._GATE_CACHE_PATH, encoding="utf-8") as f:
            self.assertIn(p, json.load(f))

    def test_a_REWRITTEN_frame_misses_rather_than_lying(self):
        """The safety-critical one. A changed file must never serve the old verdict."""
        p = self._frame(b"first")
        ca.stash_screen_open_cached(p)
        ca._gate_cache_flush()
        entry = list(ca._gate_cache()[p])
        # plant a verdict that is WRONG for this file, then change the file underneath it
        ca._gate_cache()[p] = [entry[0], entry[1], "stash"]
        self.assertEqual(ca.stash_screen_open_cached(p), "stash", "the planted verdict was not served")
        time.sleep(0.01)
        with open(p, "wb") as f:
            f.write(b"second-and-longer")        # both size and mtime move
        self.assertNotEqual(ca.stash_screen_open_cached(p), "stash",
                            "a rewritten frame kept its old verdict — this is the misroute that "
                            "merge-max would make permanent")

    def test_a_missing_file_falls_back_and_does_not_explode(self):
        p = os.path.join(_TMP, "gone.jpg")
        self.assertIsNone(ca.stash_screen_open_cached(p))

    def test_the_quote_flushes_what_it_learned(self):
        self.assertTrue(hasattr(ca, "vault_scan_cost"))
        self.assertTrue(hasattr(ca, "_vault_scan_cost_inner"),
                        "the flush wrapper is gone — the memo would be rebuilt on every quote")


if __name__ == "__main__":
    unittest.main(verbosity=2)
