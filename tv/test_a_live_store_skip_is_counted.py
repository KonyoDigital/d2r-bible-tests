# -*- coding: utf-8 -*-
"""A GATE THAT STANDS DOWN FOR WANT OF HIS DATA MUST BE COUNTED, NOT SILENT.

Eleven gates were RED on origin and GREEN on his Mac, and neither verdict was about the shipped
code: they read stores that exist only on his machine.

    tv/chron_evidence.json   2,210,553 bytes locally · NOT tracked -> absent in CI
    tv/vault_accum.json         96,485 bytes locally · NOT tracked -> absent in CI
    ~/d2r_ledger_backups/           73 files         · outside the repo entirely

In CI those reads return None or 0 and the gate fails with `None != 100.0`, `the vault bank holds
no named rows`, `no ledger backup exists yet` — sentences that read as product defects and are
statements about a runner having no data. They cannot simply be committed: `chron_evidence.json`
is 2.2 MB of HIS ledger evidence and this repo is PUBLIC.

⚠⚠ SO THE SKIP MUST BE LOUD. A bare `return` would turn eleven reds into silence, which is the
failure this repo has a scar for — *"a gate that always skips is the same defect as one that is
always green"*. `live_store.require()` skips with `LIVE_STORE_MARK`, and this law globs for that
mark and PRINTS the population, so the number stands on a screen instead of dissolving into a
green run.

It is deliberately the same shape as `node unavailable — a skip is NOT a pass`, which this repo
already uses for the node venue: one venue, one mark, one counter. [[regression-guard]]
[[unknown-stays-unknown]] [[copy-drift]]
"""
import glob
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import live_store as LS


def _gates_that_stand_down():
    """Every gate file that can skip for want of his data. -> sorted [basename]"""
    out = []
    for p in sorted(glob.glob(os.path.join(HERE, "test_*.py"))):
        if os.path.basename(p) == os.path.basename(__file__):
            continue
        try:
            with io.open(p, encoding="utf-8") as fh:
                src = fh.read()
        except Exception:
            continue
        if "live_store" in src and ("require(" in src or LS.LIVE_STORE_MARK in src):
            out.append(os.path.basename(p))
    return out


class TestALiveStoreSkipIsCounted(unittest.TestCase):

    def test_the_population_is_named_not_merely_counted(self):
        """★ The number and the names both, so a growing set cannot hide as one line."""
        gates = _gates_that_stand_down()
        here = LS.missing("chron_evidence.json", "vault_accum.json")
        print("   %d gate(s) can stand down for want of his data; missing here: %s"
              % (len(gates), ", ".join(here) or "none — this venue HAS his stores"))
        for g in gates:
            print("     · %s" % g)
        self.assertIsInstance(gates, list)

    def test_the_mark_is_one_string_everywhere(self):
        """⚠ A second spelling uncounts every skip that uses it, silently."""
        strays = []
        for p in sorted(glob.glob(os.path.join(HERE, "test_*.py"))):
            if os.path.basename(p) == os.path.basename(__file__):
                continue
            with io.open(p, encoding="utf-8") as fh:
                src = fh.read()
            if "live store is absent" in src and "live_store" not in src:
                strays.append(os.path.basename(p))
        self.assertEqual(strays, [],
                         "these carry the mark's words without importing the helper, so the "
                         "counter cannot see them and the spelling can drift: %s" % strays)

    def test_the_helper_refuses_to_excuse_a_venue_that_HAS_the_data(self):
        """★ THE HALF THAT KEEPS IT HONEST. A skip taken where the store exists would destroy the
        only distinction this is for: 'nobody could look' versus 'it looked and was wrong'."""
        class _Case(unittest.TestCase):
            def runTest(self):
                pass
        c = _Case()
        # a file that certainly exists — the helper must NOT skip
        LS.require(c, "live_store.py")
        with self.assertRaises(unittest.SkipTest):
            LS.require(c, "definitely_not_here_%d.json" % os.getpid())

    def test_the_skip_says_why_and_names_the_file(self):
        class _Case(unittest.TestCase):
            def runTest(self):
                pass
        c = _Case()
        with self.assertRaises(unittest.SkipTest) as cm:
            LS.require(c, "missing_%d.json" % os.getpid(), why="it holds his banked rows")
        msg = str(cm.exception)
        self.assertIn(LS.LIVE_STORE_MARK, msg, "the counter's mark is absent: %r" % msg)
        self.assertIn("missing_", msg, "the skip does not name the file: %r" % msg)
        self.assertIn("a skip is NOT a pass", msg, "the sentence lost its warning: %r" % msg)
        self.assertIn("banked rows", msg, "the caller's reason was dropped: %r" % msg)


if __name__ == "__main__":
    unittest.main(verbosity=2)
