#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REG-1277 (#221) — A LIVE WITNESS IS NOT AN EXTRACTION.

His ruling on #221 was DIG. What the dig found, MEASURED read-only 2026-09-25:

  · Every one of the 18 unexplained tombstones was written by his console's OWN retention lane. Its
    stdout (control_app.log) prints "CONSOLE BOOT v2875" at 01:36:21 on 2026-09-10 and, one second
    later, "freed 3565 MB by removing 7 reel(s)"; five more passes that day took 11 more (6 of them
    one second after the v2878 boot at 03:26:18). No gate and no fixture - hypothesis (B) is refuted.
  · v2875's own commit measured the plan that did it: "7 candidates (3,565 MB) ... all 7 survivors:
    panels on film AND rows durable". The console ran exactly that plan.
  · 13 of the 18 had a FULL survey with panels (1 to 123) and a vault seal with rows 0, and
    `_panels_never_banked` released them because it asked only "is this session in the durable
    stores" - and one or two items the LIVE lane read while filming put it there.
    reel_s_1787523300658_1: 2,385 frames, 3,002.9 MB, 18 panels, ONE durable row.
  · end_routes refused every one of them ("extracted rows before the tombstone"). The deleter and
    the end-route doors disagreed, and nothing compared them.

  · DRIVEN on a fixture shelf through the real plan(): panels + a seal with rows 0 + a live witness
    -> HELD as panels-never-banked, never a candidate.
  · DRIVEN: an examined-empty seal still releases (the v3074 exit is not closed), and a seal with
    rows that became durable is not held by this rule (a rule that holds everything is not a filter).
  · DRIVEN: end_routes.deleter_disagrees names a reel the deleter offers while every door refused
    it; report() carries it; the doctor's end-routes row leads with it.
RED_PROOF below.
"""
import collections
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import console_safe  # noqa: E402
console_safe.enable()

import reel_retention as RR  # noqa: E402
import end_routes as ER      # noqa: E402
import console_doctor as CD  # noqa: E402

SEAL_TOOK_NOTHING = {"rows": 0, "extracted": [], "extractedWhy": "nothing was taken",
                     "agentVer": "fixture", "promptVer": 1}
SEAL_EXAMINED_EMPTY = {"rows": 0, "extracted": [], "examinedEmpty": True,
                       "extractedWhy": "examined and there was nothing to take",
                       "agentVer": "fixture", "promptVer": 1}
SEAL_SEVEN_ROWS = {"rows": 7, "agentVer": "fixture", "promptVer": 1}


def _plan(subject_seal, subject_durable, panels=49):
    """One old reel under test plus KEEP_RECENT newer fillers, on a shelf of our own. -> (tag, plan)

    The witness index is stubbed (plan() reads it from HERE, not from the caller's hist - the same
    reason test_a_seal_is_not_an_extraction stubs it), and it is the ONLY way a live witness can be
    placed: `sessions` is exactly what one live-lane row naming the reel contributes.
    """
    tmp = tempfile.mkdtemp(prefix="livewitness_")
    hist = os.path.join(tmp, "hist")
    os.makedirs(hist)
    now = int(time.time() * 1000)
    rows = [(90, panels)] + [(d, 0) for d in range(30, 30 - RR.KEEP_RECENT, -1)]
    survey, chron, vault, names = {}, {}, {}, []
    for i, (age, p) in enumerate(rows):
        nm = "reel_s_%d_%03d" % (now - int(age * 86400000), i)
        names.append(nm)
        d = os.path.join(hist, nm)
        os.makedirs(d)
        for f in range(3):
            io.open(os.path.join(d, "f_%d.jpg" % (1700000000 + f)), "w").write("x")
        survey[nm] = {"full": True, "panels": p, "frames": 3, "kinds": ({"stash": p} if p else {})}
        chron[nm] = {"ts": now, "classified": 1, "pages": 0, "looked": True,
                     "framesAtLook": 3, "why": "fixture"}
    if subject_seal is not None:
        vault[names[0]] = dict(subject_seal, ts=now)
    io.open(os.path.join(hist, "chronicle_swept.json"), "w", encoding="utf-8").write(json.dumps(chron))
    io.open(os.path.join(hist, "vault_swept.json"), "w", encoding="utf-8").write(json.dumps(vault))
    sessions = {names[0][len("reel_"):]} if subject_durable else set()
    old = os.environ.get("TV_HIST")
    os.environ["TV_HIST"] = hist
    import frame_authority as _fa
    _real_wi = _fa.witness_index
    _fa.witness_index = lambda *a, **k: {"haveIndex": True, "ok": True, "frames": set(),
                                         "sessions": set(sessions), "perStore": {}}
    try:
        import retro_triage as rt
        io.open(rt._store_path(), "w", encoding="utf-8").write(json.dumps(survey))
        RR._TRIAGE_CACHE["at"] = None
        plan = RR.plan(hist)
    finally:
        _fa.witness_index = _real_wi
        if old is None:
            os.environ.pop("TV_HIST", None)
        else:
            os.environ["TV_HIST"] = old
        RR._TRIAGE_CACHE["at"] = None
        shutil.rmtree(tmp, ignore_errors=True)
    tag = None
    for k in (plan.get("kept") or []) + list(plan.get("candidates") or []):
        if isinstance(k, dict) and str(k.get("reel", "")).endswith(names[0]):
            tag = k.get("tag")
    return tag, plan


class ALiveWitnessIsNotAnExtraction(unittest.TestCase):

    def test_the_221_shape_is_held(self):
        """★★ Panels on film, a seal that took 0 rows, and ONE live-lane row naming the session:
        exactly what released 13 reels on 2026-09-10. It must be HELD, never offered."""
        tag, plan = _plan(SEAL_TOOK_NOTHING, subject_durable=True)
        self.assertTrue(plan.get("ok"), "the fixture shelf did not plan: %r" % plan.get("why"))
        self.assertEqual(tag, "panels-never-banked",
                         "a reel with 49 panels whose seal took NOTHING was released because a live "
                         "witness names its session (tag %r) - that is how 13 reels left" % tag)

    def test_an_examined_empty_seal_still_releases(self):
        """★ The v3074 exit stays open: a seal that read every panel and cross-checked them is a
        complete answer, and holding it would be a hold no run can lift."""
        tag, plan = _plan(SEAL_EXAMINED_EMPTY, subject_durable=True)
        self.assertTrue(plan.get("ok"))
        self.assertIsNotNone(tag, "premise: the subject reel is on the plan")
        self.assertNotEqual(tag, "panels-never-banked",
                            "an examined-empty seal was held - the v3074 exit is closed again")

    def test_rows_that_became_durable_are_not_held_by_this_rule(self):
        """★ The other half: a seal with rows, and those rows durable, is what extraction looks like."""
        tag, plan = _plan(SEAL_SEVEN_ROWS, subject_durable=True)
        self.assertTrue(plan.get("ok"))
        self.assertIsNotNone(tag, "premise: the subject reel is on the plan")
        self.assertNotEqual(tag, "panels-never-banked",
                            "a reel whose seven rows reached a durable store was held as unbanked")


class TheTwoAuthoritiesAreCompared(unittest.TestCase):

    def test_a_reel_offered_while_every_door_refused_is_named(self):
        rows = [{"reel": "reel_a", "say": "HELD", "safetyHold": "eligible"},
                {"reel": "reel_b", "say": "HELD", "safetyHold": "recent"},
                {"reel": "reel_c", "say": "QUALIFIED", "safetyHold": "eligible"},
                {"reel": "reel_d", "say": "UNKNOWN", "safetyHold": "eligible"}]
        self.assertEqual(ER.deleter_disagrees(rows), ["reel_a"])
        self.assertEqual(ER.deleter_disagrees(None), [])

    def test_the_report_carries_it(self):
        self.assertIn("deleter_disagrees", ER.report.__code__.co_names,
                      "report() never asks whether the deleter agrees - the comparison is unjoined")

    def _row(self, rep):
        real = ER.report
        ER.report = lambda *a, **k: rep
        try:
            return CD._check_every_reel_can_still_reach_an_end_route()
        finally:
            ER.report = real

    def test_the_doctor_leads_with_it(self):
        state, why = self._row({"ok": True, "walked": 3, "deadEnded": 1, "finishedWaiting": 0,
                                "rows": [], "deleterWouldRelease": ["reel_s_1_1"]})
        self.assertEqual(state, CD.MISSING, why)
        self.assertIn("would RELEASE 1 reel(s)", why)
        self.assertIn("reel_s_1_1", why)

    def test_agreement_and_unknown_do_not_fire_it(self):
        for rel in ([], None):
            state, why = self._row({"ok": True, "walked": 3, "deadEnded": 0, "finishedWaiting": 3,
                                    "rows": [], "deleterWouldRelease": rel})
            self.assertEqual(state, CD.OK, "%r -> %s" % (rel, why))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-1277 - a live witness counts as an extraction again: panels on film with a seal "
               "that took 0 rows are released, which is how 13 reels were tombstoned on 2026-09-10",
        "file": "reel_retention.py",
        "find": "            if isinstance(_n, bool) or not isinstance(_n, int) or _n <= 0:\n",
        "replace": "            if False:\n",
        "matches": 1,
    },
    {
        "why": "REG-1277 - the comparison names nothing: the deleter and the end-route doors can "
               "disagree in silence again",
        "file": "end_routes.py",
        "find": "if isinstance(x, dict) and x.get(\"say\") == \"HELD\" and x.get(\"safetyHold\") == \"eligible\")",
        "replace": "if isinstance(x, dict) and False)",
        "matches": 1,
    },
    {
        "why": "REG-1277 - the report stops carrying the disagreement: computed, read by nothing",
        "file": "end_routes.py",
        "find": "            \"deleterWouldRelease\": (deleter_disagrees(rows) if tags is not None else None),\n",
        "replace": "            \"deleterWouldRelease\": None,\n",
        "matches": 1,
    },
    {
        "why": "REG-1277 - the doctor's row stops leading with a release every door refused",
        "file": "console_doctor.py",
        "find": "    if _released_unextracted:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
]
