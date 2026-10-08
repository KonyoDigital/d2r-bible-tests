# -*- coding: utf-8 -*-
"""#203 (REG-2042) - AN EXAMINED-EMPTY SEAL RELEASES A REEL ONLY WHEN IT PROBED EVERY STASH PANEL TRIAGE SAW.

HIS RULING 2026-10-07 ("probe every panel" - stricter than the half I recommended): a seal releases a reel's frames only
when it probed every panel triage saw; otherwise keep the reel and say why. Reel ...39108 was deleted on 2026-09-28 on
an examinedEmpty seal that probed ONE frame while triage had counted 268 stash panels in it. MEASURED on his store
2026-10-08: 33 examined-empty seals - 8 contradict a full triage pass, 9 sit on reels triage proved panel-free, 16 were
never triaged.

  * the seal carries the denominator: triagePanels (a FULL triage pass's count) and probedPanels;
  * missing either (an older seal, a reel never fully triaged) KEEPS the reel, saying why;
  * a full triage pass that saw zero panels is re-derivable proof that there was nothing to probe, so an older seal on
    such a reel gets triagePanels 0 / probedPanels 0 and keeps releasing; a partial pass stamps nothing.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import frame_authority as FA  # noqa: E402

_SEAL = {"ts": 1, "rows": 0, "examinedEmpty": True, "extracted": [],
         "extractedWhy": "examined and there was nothing to take"}


class AnExaminedSealReleasesOnlyWhenEveryPanelWasProbed(unittest.TestCase):

    def test_his_39108_case_is_kept(self):
        row = dict(_SEAL, triagePanels=268, probedPanels=1)
        ok, why = FA.seal_releases_frames(row)
        self.assertFalse(ok, "1 probe against 268 triage panels released the reel: %s" % why)
        self.assertIn("1 of the 268", why)

    def test_a_seal_without_the_denominator_is_kept(self):
        ok, why = FA.seal_releases_frames(dict(_SEAL))
        self.assertFalse(ok, why)
        self.assertIn("every panel", why)
        ok, why = FA.seal_releases_frames(dict(_SEAL, triagePanels=6))
        self.assertFalse(ok, "panels triage saw but the seal never probed released the reel")

    def test_every_panel_probed_releases(self):
        self.assertTrue(FA.seal_releases_frames(dict(_SEAL, triagePanels=6, probedPanels=6))[0])
        self.assertTrue(FA.seal_releases_frames(dict(_SEAL, triagePanels=0, probedPanels=0))[0])

    def test_a_panel_free_triage_pass_backfills_an_older_seal_and_nothing_else_does(self):
        row, ch = FA.stamp_examined_from_triage(dict(_SEAL), {"panels": 0, "frames": 40, "full": True})
        self.assertTrue(ch)
        self.assertEqual((row.get("triagePanels"), row.get("probedPanels")), (0, 0))
        self.assertTrue(FA.seal_releases_frames(row)[0], "a reel triage proved panel-free stopped releasing")
        row, ch = FA.stamp_examined_from_triage(dict(_SEAL), {"panels": 268, "full": True})
        self.assertEqual(row.get("triagePanels"), 268)
        self.assertNotIn("probedPanels", row, "probes were invented for panels the seal never looked at")
        self.assertFalse(FA.seal_releases_frames(row)[0])
        row, ch = FA.stamp_examined_from_triage(dict(_SEAL), {"panels": 0, "full": False})
        self.assertFalse(ch, "a PARTIAL triage pass was taken as proof there was nothing to probe")
        row, ch = FA.stamp_examined_from_triage(dict(_SEAL), None)
        self.assertFalse(ch)

    def test_a_covered_seal_is_untouched(self):
        ok, _ = FA.seal_releases_frames({"extracted": list(FA.EXTRACTION_CONTRACT), "rows": 3})
        self.assertTrue(ok, "a COVERED seal is not this rule's subject and must still release")


class TheConsoleBackfillsOnlyWhatTriageProves(unittest.TestCase):

    def test_the_backfill_stamps_a_panel_free_reel_and_holds_the_rest(self):
        from unittest import mock
        import control_app as ca
        import retro_triage as rt
        store = {"s_1_1": dict(_SEAL), "s_2_2": dict(_SEAL), "s_3_3": dict(_SEAL), "s_4_4": {"rows": 2, "extracted": []}}
        triage = {"reel_s_1_1": {"panels": 0, "full": True}, "reel_s_2_2": {"panels": 268, "full": True},
                  "reel_s_3_3": {"panels": 0, "full": False}}
        saved = {}
        with mock.patch.object(ca, "_vault_swept_load", lambda: dict(store)), \
                mock.patch.object(ca, "_vault_swept_save", lambda rec: saved.update(rec)), \
                mock.patch.object(rt, "load", lambda root=None: (triage, True)), \
                mock.patch.dict(ca._EXAMINED_BACKFILL, {"done": False}):
            n = ca._examined_seals_backfill()
            again = ca._examined_seals_backfill()
        self.assertEqual(n, 2, "only full-triage reels are stamped: %r" % saved)
        self.assertEqual(again, 0, "the backfill ran twice in one process")
        self.assertTrue(FA.seal_releases_frames(saved["s_1_1"])[0], "a reel triage proved panel-free stopped releasing")
        self.assertFalse(FA.seal_releases_frames(saved["s_2_2"])[0], "268 unprobed panels released the reel")
        self.assertNotIn("triagePanels", saved["s_3_3"], "a partial triage pass was written as proof")
        self.assertEqual(saved["s_4_4"], {"rows": 2, "extracted": []}, "a seal that is not examined-empty was touched")


RED_PROOF = [
    {"why": "REG-2042 - an examined-empty seal releases on one probe again",
     "file": "frame_authority.py",
     "find": "        return probed_every_panel(row)\n",
     "replace": "        return True, why\n",
     "matches": 1},
    {"why": "REG-2042 - fewer probes than triage panels release the reel again",
     "file": "frame_authority.py",
     "find": "    if pp < tp:\n",
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "REG-2042 - a partial triage pass backfills a release",
     "file": "frame_authority.py",
     "find": "    if not isinstance(triage_row, dict) or not triage_row.get(\"full\"):\n",
     "replace": "    if not isinstance(triage_row, dict):\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
