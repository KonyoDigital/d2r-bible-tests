# -*- coding: utf-8 -*-
"""REG-1647 — "WERE THIS REEL'S PANELS EVER BANKED?" HAS ONE ANSWER, WHENEVER IT IS ASKED.

reel_retention._panels_never_banked asked `not in _DURABLE`, a module global that only plan() filled - so a
caller that asked BEFORE any plan() in its process was told every surveyed reel with panels had never been
banked. MEASURED on his Mac 2026-10-01, same reel, same process, a minute apart:
    reel_s_1789330829280_66296   before plan(): never_banked True   after plan(): False (in durable)
The console's boot re-entry (vault_reentry_sweep) asks first, so every relaunch re-admitted the two reels the
vault lane had retired; the lane paid 2 passes of ~30 panel reads on each and its retire path - asking after
plan() - retired them again: 9 relaunches since 2026-09-30 10:18, about 1,000 reads that could never seal.

  · DRIVEN, a fresh module (no plan): a banked reel reads banked, an unbanked one reads held - the same answers
    the plan path gives - and the set it loaded is the durable index, not an empty default.
  · DRIVEN: an unreadable durable index RAISES DurableUnknown and is not cached; plan() leaves the global None on
    a failed load and publishes the set on a good one.
  · DRIVEN in a fixture world: the vault re-entry keeps a banked retired reel retired on its very first ask, and
    leaves a reel alone ("cannot ask -> never guess") when the index is unreadable.
  · v3540 REG-1658, DRIVEN: a retirement made BLIND (no reason recorded - the REG-1649 gap, judged by the REG-1648
    blind lattice) is re-judged ONCE, by ONE attempt, at most _VAULT_REJUDGE_PER_BOOT per boot; one that carries its
    reason stays retired.
RED_PROOF below. [[unknown-stays-unknown]] [[copy-drift]]
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

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

_WORLD = tempfile.mkdtemp(prefix="durable_asked_")
os.environ["TV_HIST"] = _WORLD
os.environ["TV_SESSIONS"] = os.path.join(_WORLD, "sessions.jsonl")

import reel_retention as RR  # noqa: E402
import retro_triage as RT  # noqa: E402
import frame_authority as FA  # noqa: E402

BANKED = "reel_s_1500000000001_16471"
UNBANKED = "reel_s_1500000000002_16472"
SURVEY = {r: {"full": True, "panels": 4, "frames": 40} for r in (BANKED, UNBANKED)}


class _World(unittest.TestCase):
    """A survey that says both reels carry panels, no seal for either, and a durable index naming only BANKED."""

    def setUp(self):
        fd, self.store = tempfile.mkstemp(prefix="durable_asked_triage_", suffix=".json")
        with os.fdopen(fd, "w") as fh:
            fh.write("{}")
        self.addCleanup(lambda: os.path.exists(self.store) and os.remove(self.store))
        saved = {"sp": RT._store_path, "cache": dict(RR._TRIAGE_CACHE), "dur": RR._DURABLE,
                 "ds": RR._durable_sessions, "seals": FA.sealed_sessions}
        RT._store_path = lambda *a, **k: self.store
        RR._TRIAGE_CACHE["store"] = dict(SURVEY)
        RR._TRIAGE_CACHE["at"] = (self.store, os.path.getmtime(self.store))
        FA.sealed_sessions = lambda root=None: ({}, True)
        self.index_ok = True
        self.asked = []

        def _ds(here=None):
            self.asked.append(here)
            if not self.index_ok:
                return set(), False, "vault_seen.json will not parse"
            return {RR._reel_ts_key(BANKED)}, True, None
        RR._durable_sessions = _ds
        RR._DURABLE = None                       # a process in which no plan() has run yet

        def _restore():
            RT._store_path = saved["sp"]
            RR._TRIAGE_CACHE.clear()
            RR._TRIAGE_CACHE.update(saved["cache"])
            RR._DURABLE = saved["dur"]
            RR._durable_sessions = saved["ds"]
            FA.sealed_sessions = saved["seals"]
        self.addCleanup(_restore)


class TheAnswerDoesNotDependOnWhoAskedFirst(_World):

    def test_a_banked_reel_reads_banked_before_any_plan(self):
        self.assertFalse(RR._panels_never_banked(BANKED),
                         "a reel whose panels ARE in the durable index read 'never banked' because no plan() had "
                         "run in this process - the boot re-entry re-admits it on that answer")
        self.assertTrue(self.asked, "PREMISE: the durable index was never consulted")

    def test_an_unbanked_reel_still_holds(self):
        self.assertTrue(RR._panels_never_banked(UNBANKED), "the rule stopped holding what was never banked")

    def test_the_lazy_answer_is_the_plan_answer(self):
        lazy = (RR._panels_never_banked(BANKED), RR._panels_never_banked(UNBANKED))
        RR._DURABLE = {RR._reel_ts_key(BANKED)}           # what plan() publishes from the same index
        self.assertEqual(lazy, (RR._panels_never_banked(BANKED), RR._panels_never_banked(UNBANKED)))

    def test_an_unreadable_index_is_unknown_and_is_not_cached(self):
        self.index_ok = False
        with self.assertRaises(RR.DurableUnknown):
            RR._panels_never_banked(BANKED)
        self.assertIsNone(RR._DURABLE, "a failed load was cached - 'nothing is durable' for the console's life")
        self.index_ok = True
        self.assertFalse(RR._panels_never_banked(BANKED), "a readable index on the next ask was not read")


class PlanPublishesOnlyWhatItRead(_World):

    def _plan(self):
        hist = tempfile.mkdtemp(prefix="durable_asked_hist_")
        self.addCleanup(shutil.rmtree, hist, True)
        return RR.plan(hist_dir=hist, _fresh=True)

    def test_a_failed_load_leaves_the_global_unknown(self):
        self.index_ok = False
        self._plan()
        self.assertTrue(self.asked, "PREMISE: plan() never asked the durable index")
        self.assertIsNone(RR._DURABLE, "plan() published an empty set for an index it could not read")

    def test_a_good_load_is_published(self):
        self._plan()
        self.assertEqual(RR._DURABLE, {RR._reel_ts_key(BANKED)})


class TheVaultReentryAsksTheSameQuestion(_World):

    def setUp(self):
        super().setUp()
        import control_app as ca
        self.ca = ca
        self.assertTrue(os.path.realpath(ca._vault_autoread_path()).startswith(os.path.realpath(_WORLD)),
                        "PREMISE: the lane's store is not in this law's world")
        saved = {"ret": dict(ca._VAULT_AUTOREAD.get("retired") or {}), "tries": dict(ca._VAULT_AUTOREAD.get("tries") or {}),
                 "rej": dict(ca._VAULT_AUTOREAD.get("rejudged") or {}), "load": ca._vault_autoread_load}
        ca._vault_autoread_load = lambda: True
        ca._VAULT_AUTOREAD["retired"] = {r: {"why": "x", "tries": 2, "at": 1} for r in (BANKED, UNBANKED)}
        ca._VAULT_AUTOREAD["rejudged"] = {}

        def _restore():
            ca._VAULT_AUTOREAD["retired"] = saved["ret"]
            ca._VAULT_AUTOREAD["tries"] = saved["tries"]
            ca._VAULT_AUTOREAD["rejudged"] = saved["rej"]
            ca._vault_autoread_load = saved["load"]
        self.addCleanup(_restore)

    def test_a_banked_retired_reel_stays_retired_on_the_first_ask(self):
        out = self.ca.vault_reentry_sweep(dry=True)
        self.assertIn(BANKED, out["kept"], "the first ask in a fresh process re-admitted a banked reel: %r" % out)
        self.assertIn(UNBANKED, out["readmitted"], "a reel genuinely never banked must still come back: %r" % out)

    def test_an_unreadable_index_leaves_every_retirement_alone(self):
        self.index_ok = False
        out = self.ca.vault_reentry_sweep(dry=True)
        self.assertEqual(out["readmitted"], [], "re-admitted on an index nobody could read: %r" % out)


    # ── REG-1658 — a retirement made BLIND is re-judged once, by one attempt, a few per boot ──────────────────────
    BLIND = {"why": "2 attempt(s) ran and this reel is STILL owed afterwards — and no attempt left a reason, so WHY is "
                    "UNKNOWN, not diagnosed", "lastWhy": None, "tries": 2, "at": 1}
    REASONED = {"why": "2 attempt(s) ran and this reel is STILL owed afterwards — the last one said: 28 of 28 read "
                       "frame(s) were never cross-checked", "lastWhy": "28 of 28 read frame(s) were never cross-checked",
                "tries": 2, "at": 1}

    def test_a_blind_retirement_gets_one_more_attempt(self):
        self.ca._VAULT_AUTOREAD["retired"] = {BANKED: dict(self.BLIND)}
        out = self.ca.vault_reentry_sweep(dry=False)
        self.assertEqual(out["rejudged"], [BANKED], "a retirement judged by a blind instrument was left standing: %r" % out)
        self.assertNotIn(BANKED, self.ca._VAULT_AUTOREAD["retired"])
        self.assertEqual(self.ca._VAULT_AUTOREAD["tries"].get(BANKED), self.ca._VAULT_AUTOREAD_MAX_TRIES - 1,
                         "the re-judge bought more than ONE attempt")

    def test_a_reel_is_re_judged_once_ever_even_if_it_retires_blind_again(self):
        """REG-1663 — the v3540 eye: an attempt that dies before leaving a reason retires the reel blind again."""
        self.ca._VAULT_AUTOREAD["retired"] = {BANKED: dict(self.BLIND)}
        self.ca.vault_reentry_sweep(dry=False)
        self.assertIn(BANKED, self.ca._VAULT_AUTOREAD.get("rejudged") or {}, "the re-judge left no durable mark")
        self.ca._VAULT_AUTOREAD["retired"] = {BANKED: dict(self.BLIND)}       # its one attempt died blind
        out = self.ca.vault_reentry_sweep(dry=False)
        self.assertEqual(out["rejudged"], [], "a reel was re-judged a second time: %r" % out)
        self.assertIn(BANKED, self.ca._VAULT_AUTOREAD["retired"])

    def test_the_mark_is_persisted_with_the_store(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            src = fh.read()
        save = src[src.index("def _vault_autoread_save():"):src.index("def ", src.index("def _vault_autoread_save():") + 10)]
        self.assertIn('"rejudged": _VAULT_AUTOREAD.get("rejudged")', save, "the re-judge mark is not saved")
        load = src[src.index("def _vault_autoread_load():"):src.index("def ", src.index("def _vault_autoread_load():") + 10)]
        self.assertIn('"rejudged"', load, "the re-judge mark is not loaded")

    def test_a_reasoned_retirement_stays_retired(self):
        self.ca._VAULT_AUTOREAD["retired"] = {BANKED: dict(self.REASONED)}
        out = self.ca.vault_reentry_sweep(dry=True)
        self.assertEqual(out["rejudged"], [], "a retirement that carries its reason was re-bought: %r" % out)
        self.assertIn(BANKED, out["kept"])

    def test_a_boot_rejudges_only_a_few(self):
        names = ["reel_s_15000000001%02d_165%02d" % (i, i) for i in range(5)]
        real = RR._durable_sessions
        RR._durable_sessions = lambda here=None: ({RR._reel_ts_key(n) for n in names}, True, None)
        RR._DURABLE = None
        try:
            self.ca._VAULT_AUTOREAD["retired"] = {n: dict(self.BLIND) for n in names}
            SURVEY.update({n: {"full": True, "panels": 4, "frames": 40} for n in names})
            RR._TRIAGE_CACHE["store"] = dict(SURVEY)
            out = self.ca.vault_reentry_sweep(dry=True)
        finally:
            RR._durable_sessions = real
            for n in names:
                SURVEY.pop(n, None)
        self.assertEqual(len(out["rejudged"]), self.ca._VAULT_REJUDGE_PER_BOOT,
                         "a boot re-bought %d blind retirements at once" % len(out["rejudged"]))
        self.assertEqual(len(out["kept"]), 5 - self.ca._VAULT_REJUDGE_PER_BOOT)


def tearDownModule():
    shutil.rmtree(_WORLD, ignore_errors=True)


RED_PROOF = [
    {"why": "REG-1663 - a reel is re-judged again every boot when its one attempt died blind",
     "file": "control_app.py",
     "find": "            if (_vault_retired_blind(retired.get(rid)) and rid not in done\n",
     "replace": "            if (_vault_retired_blind(retired.get(rid))\n",
     "matches": 1},
    {"why": "REG-1663 - the re-judge mark lives only in memory: a restart re-buys the reel",
     "file": "control_app.py",
     "find": "               \"rejudged\": _VAULT_AUTOREAD.get(\"rejudged\") or {},      # REG-1663\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-1658 - a retirement judged blind is never looked at again (his two reels stay retired for ever)",
     "file": "control_app.py",
     "find": "            if (_vault_retired_blind(retired.get(rid)) and rid not in done\n",          # REG-1663 re-anchor
     "replace": "            if (False and rid not in done\n",
     "matches": 1},
    {"why": "REG-1658 - the re-judge is unbounded: one relaunch re-buys a whole backlog of blind retirements",
     "file": "control_app.py",
     "find": " and len(out[\"rejudged\"]) < _VAULT_REJUDGE_PER_BOOT):\n",                          # REG-1663 re-anchor
     "replace": "):\n",
     "matches": 1},
    {"why": "REG-1658 - the re-judge buys the full try budget instead of one attempt",
     "file": "control_app.py",
     "find": "                        _VAULT_AUTOREAD[\"tries\"][rid] = max(0, _VAULT_AUTOREAD_MAX_TRIES - 1)   # ONE attempt left\n",
     "replace": "                        _VAULT_AUTOREAD[\"tries\"][rid] = 0\n",
     "matches": 1},
    {"why": "REG-1647 - the predicate asks the unloaded global again: before any plan() every reel reads 'never banked'",
     "file": "reel_retention.py",
     "find": "        return _reel_ts_key(reel) not in _durable_loaded()     # REG-1647 — never the unloaded global\n",
     "replace": "        return _reel_ts_key(reel) not in (_DURABLE or set())\n",
     "matches": 1},
    {"why": "REG-1647 - an unreadable index collapses to 'not held' instead of travelling as UNKNOWN",
     "file": "reel_retention.py",
     "find": "    except DurableUnknown:\n        raise                             # REG-1647 — UNKNOWN travels; each caller prices it itself\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-1647 - plan() publishes an empty set for an index it could not read",
     "file": "reel_retention.py",
     "find": "    _DURABLE = set(_dur_set) if _durable_ok else None\n",
     "replace": "    _DURABLE = set(_dur_set)\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
