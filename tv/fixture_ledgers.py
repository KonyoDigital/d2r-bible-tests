# -*- coding: utf-8 -*-
"""v3470 — ONE place that points the two live eagle ledgers somewhere harmless for a TEST process.

⚠⚠ WHAT IT COST BEFORE THIS EXISTED. The doctor suites drive console_doctor and unknown_age with fake
checks ('exploder', 'exploding check', 'costly-one'), and seven of them never redirected either
ledger, so every run appended those rows to HIS live tv/.unknown_age.json and tv/.eagle_slow.json —
MEASURED 2026-09-24: 'exploder' unknownCount 813, 'exploding check' 803, growing by three on each
pre-push. unknown_age.py:21 said "Tests set TV_UNKNOWN_AGE to a tempfile." Seven did not.
[[feedback-fixtures-never-touch-live-data]] — guard the FIXTURE, not the call site.

A test file calls `redirect()` at import. An explicit per-test redirect (setUp) still wins, because
this only fills a variable nobody set. Child processes inherit the environment, so a gate that
spawns the console or a script is covered too. The temp files are removed at exit.
⚠ PRODUCTION CODE MUST NEVER IMPORT THIS. It exists for test processes only.
"""
import atexit
import os
import tempfile

VARS = (("TV_UNKNOWN_AGE", "unknown_age"), ("TV_EAGLE_SLOW", "eagle_slow"),
        # v3475 — the seed baker's receipt: test_bake_seed drives bake() in report AND write
        # modes, so without this every run of it would stamp HIS live receipt.
        ("TV_BAKE_RECEIPT", "bake_seed_receipt"))


def redirect():
    """Point every unset ledger variable at a per-process temp file. -> {var: path}"""
    made = []
    for var, stem in VARS:
        if not os.environ.get(var):
            p = os.path.join(tempfile.gettempdir(), "tvd_fixture_%s_%d.json" % (stem, os.getpid()))
            os.environ[var] = p
            made.append(p)

    def _clean():
        for p in made:
            try:
                os.remove(p)
            except OSError:
                pass

    if made:
        atexit.register(_clean)
    return dict((v, os.environ[v]) for v, _ in VARS)
