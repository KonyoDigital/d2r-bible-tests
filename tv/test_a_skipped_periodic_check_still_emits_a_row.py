# -*- coding: utf-8 -*-
"""#35 — THE BEHAVIOURAL LAW: a PERIODIC check skipped this tick EMITS a not-asked row.

Before v3298, run() `continue`d over a skipped PERIODIC check — no row at all, so 'engines
corroborate' (the SOLE caller of corroborate.verdict()) was absent from the world 5 of 6
ticks and every consumer read absence as fine. These laws pin the fix's three halves: the
row exists with the honest vocabulary, the sidecar merge never forgets a SLOW reading, and
a placeholder never persists as a measurement. Runs against a stubbed roster and a temp
sidecar — no real checks execute, no live file is touched.
"""
import json
import os
import sys as _fx_sys
_fx_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixture_ledgers as _fx_ledgers  # noqa: E402  v3470 — never HIS eagle ledgers
_fx_ledgers.redirect()
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import console_doctor as cd


class TestSkippedTickEmitsARow(unittest.TestCase):
    def setUp(self):
        self._checks, self._slow, self._per = cd.CHECKS, cd.SLOW, cd.PERIODIC
        self._sidecar = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self._env = os.environ.get("TV_EAGLE_SLOW")
        os.environ["TV_EAGLE_SLOW"] = self._sidecar
        cd.CHECKS = [("fast one", lambda: (cd.OK, "fine")),
                     ("periodic one", lambda: (cd.OK, "measured"))]
        cd.SLOW = ()
        cd.PERIODIC = ("periodic one",)

    def tearDown(self):
        cd.CHECKS, cd.SLOW, cd.PERIODIC = self._checks, self._slow, self._per
        if self._env is None:
            os.environ.pop("TV_EAGLE_SLOW", None)
        else:
            os.environ["TV_EAGLE_SLOW"] = self._env
        try:
            os.remove(self._sidecar)
        except OSError:
            pass

    def test_a_skipped_periodic_check_is_a_row_not_a_silence(self):
        rows = cd.run(include_slow=False, include_periodic=False, tick=3)
        by = {r["check"]: r for r in rows}
        self.assertIn("periodic one", by,
                      "the skipped check vanished from the pass — the 5-of-6-ticks blindness")
        r = by["periodic one"]
        self.assertEqual(r["state"], cd.UNMEASURED)
        self.assertTrue(r.get("notAsked"), "the row must say it was NOT ASKED, not NEVER")
        self.assertIn("not asked this tick", r["why"])
        self.assertIn("next ask in %d tick(s)" % (cd.PERIODIC_EVERY - 3), r["why"],
                      "the cadence arithmetic is wrong or the tick was dropped")

    def test_without_a_tick_the_next_ask_stays_UNKNOWN(self):
        rows = cd.run(include_slow=False, include_periodic=False)
        r = {x["check"]: x for x in rows}["periodic one"]
        self.assertIn("UNKNOWN", r["why"], "a next-ask nobody can compute was guessed")

    def test_the_placeholder_quotes_the_last_asked_reading_with_its_age(self):
        cd.run(include_slow=False, include_periodic=True, tick=6)   # measures + persists
        rows = cd.run(include_slow=False, include_periodic=False, tick=7)
        r = {x["check"]: x for x in rows}["periodic one"]
        self.assertIn("last asked", r["why"])
        self.assertIn("last state ok", r["why"])

    def test_a_placeholder_never_persists_as_a_measurement(self):
        cd.run(include_slow=False, include_periodic=False, tick=2)
        blob = json.load(open(self._sidecar)) if os.path.getsize(self._sidecar) else {}
        for row in (blob.get("rows") or []):
            self.assertFalse(row.get("notAsked"),
                             "a row about NOT looking was banked as a reading — the sidecar "
                             "would then age a measurement nobody took")

    def test_the_merge_keeps_a_SLOW_reading_a_periodic_pass_never_carried(self):
        json.dump({"at": 111, "rows": [{"check": "the other doctors", "state": "ok",
                                        "why": "old full pass", "at": 111}]},
                  open(self._sidecar, "w"))
        cd.run(include_slow=False, include_periodic=True, tick=6)
        blob = json.load(open(self._sidecar))
        names = [r.get("check") for r in blob.get("rows") or []]
        self.assertIn("the other doctors", names,
                      "the periodic pass CLOBBERED the SLOW reading — the sidecar forgot "
                      "what it was built to keep")
        self.assertEqual(blob.get("at"), 111,
                         "the top-level at moved without a SLOW row being measured — "
                         "slow_surface would claim a full pass that never ran")


RED_PROOF = [
    {"why": "restoring the bare continue makes a skipped PERIODIC check vanish again — "
            "supervision downtime wearing the shape of a clean board",
     "file": "console_doctor.py",
     "find": '                rows.append({"check": name, "state": UNMEASURED, "why": _why,',
     "replace": '                continue\n                rows.append({"check": name, "state": UNMEASURED, "why": _why,',
     "matches": 1},
]


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
