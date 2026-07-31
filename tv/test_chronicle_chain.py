#!/usr/bin/env python3
"""v1532 — THE WHOLE CHAIN, IN ONE TEST.

Every link in the Chronicle arc has its own tests, and every one of them passes. That is not the
same as the chain working: each suite mocks its neighbours, so a contract could drift on BOTH sides
of a seam and every suite would stay green while the thing itself was broken. This walks it end to
end — the live agent sees the panel, the visit is recorded, the visit is swept, the pages are read
on two lanes, the gate judges, and the proposal comes out the far side — with only the VISION
stubbed, because that is the one part that cannot run for free.

It costs nothing (TV_STUB on both lanes) and takes about a second, so it belongs in the gate set
rather than in a document nobody runs.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import console_safe  # noqa: F401,E402  — non-ASCII failure text must survive a non-UTF-8 console
import chronicle_retro as cr  # noqa: E402


def _pillow():
    try:
        from PIL import Image  # noqa: F401
        return True
    except Exception:
        return False


class TestTheWholeChain(unittest.TestCase):
    """live panel → recorded visit → swept → read on two lanes → gated → proposed."""

    def setUp(self):
        if not _pillow():
            self.skipTest("Pillow absent — the frame grouping needs to decode JPEGs")
        os.environ["TV_PORT"] = "17994"          # never collide with a live agent
        import tv_diablo as tv
        self.tv = tv
        self.d = tempfile.mkdtemp()
        self.reel = os.path.join(self.d, "reel_s_chain")
        os.makedirs(self.reel)
        from PIL import Image
        # 6 frames of one held panel, then 2 of a different one — a real visit's shape
        for n in range(8):
            shade = 30 if n < 6 else 200
            Image.new("RGB", (64, 48), (shade, shade, shade)).save(
                os.path.join(self.reel, "f%d.jpg" % n))
        self.man = os.path.join(self.d, "man.json")
        with open(self.man, "w", encoding="utf-8") as fh:
            json.dump({
                # what CLAUDE sees on a chronicle page
                "*#chronicle": {"found": ["Harlequin Crest", "Windforce"],
                                "notFound": ["Stormshield"],
                                "printedFound": 2, "printedTotal": 3, "conf": 0.9},
                # what GROK sees — deliberately DIFFERENT, so the disagreement is exercised
                "*#chronicle-grok": {"found": ["Harlequin Crest"],
                                     "notFound": ["Stormshield", "Windforce"], "conf": 0.85},
            }, fh)
        self._env = {k: os.environ.get(k) for k in ("TV_STUB", "TV_STUB_MANIFEST", "TV_HIST")}
        os.environ.update({"TV_STUB": "1", "TV_STUB_MANIFEST": self.man, "TV_HIST": self.d})
        tv._CHRON_VISIT.update({"open": False, "ledger": "", "since": 0, "last": 0, "frames": []})

    def tearDown(self):
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.d, ignore_errors=True)

    # ── the chain ────────────────────────────────────────────────────────────────────────────
    def _record_a_visit(self):
        """He opens the Chronicle, scrolls, and leaves — exactly what the live loop would see."""
        tv = self.tv
        for n in range(6):
            tv._chron_visit_step("chronicle", "uniques" if n == 0 else "",
                                 frame_id="reel_s_chain/f%d" % n, ts=1000 + n)
        return tv._chron_visit_step("gameplay", "", frame_id=None, ts=1100)

    def test_the_whole_chain_holds(self):
        visit = self._record_a_visit()
        # 1) THE LIVE LANE recorded it, with the ledger stuck across frames that lost the tab
        self.assertEqual(visit["n"], 6)
        self.assertEqual(visit["ledger"], "uniques")

        # 2) THE SWEEP reads that visit — no classify, one page for six held frames
        import g5_grok_eyes as g5
        paths = [os.path.join(self.d, f + ".jpg") for f in visit["frames"]]
        for p in paths:
            self.assertTrue(os.path.isfile(p), "the chain broke at the frame-id → path seam")
        read = cr.two_lane_reader(
            lambda p, k: self.tv.claude_chronicle_read(p, k),
            lambda p, k: g5.g5_chronicle_read(p, k))
        swept = cr.sweep_frames(paths, "chronicle-" + visit["ledger"], read)
        self.assertEqual(swept["classified"], 0)
        self.assertEqual(swept["pagesRead"], 1, "six frames of one held panel is ONE page")

        # 3) BOTH LANES answered, in the same units
        resp = swept["pages"][0]["resp"]
        self.assertEqual(resp["lanesRan"], ["claude", "grok"])
        self.assertEqual(resp["laneAgreement"]["both"], ["Harlequin Crest"])
        self.assertEqual(resp["laneAgreement"]["claudeOnly"], ["Windforce"])

        # 4) THE PROPOSAL keeps one sighting per lane
        prop = cr.proposal_from_pages(swept["pages"])
        self.assertEqual(len(prop["uniques"]["Harlequin Crest"]), 2)
        self.assertEqual(len(prop["uniques"]["Windforce"]), 1)

        # 5) THE GATE grounds what two independent eyes saw and HOLDS what one did
        out = cr.apply_proposal(prop, {"uniques": [], "sets": []}, gate=cr.strict_gate())
        self.assertEqual(out["uniques"]["added"], ["Harlequin Crest"])
        held = [h["name"] for h in out["held"]]
        self.assertIn("Windforce", held)

    def test_a_visit_the_reader_never_identified_dead_ends_SAFELY(self):
        # ★ the whole chain's most dangerous input: frames that ARE a chronicle but whose ledger was
        # never read. Every layer must refuse rather than pick a side.
        tv = self.tv
        for n in range(4):
            tv._chron_visit_step("chronicle", "", frame_id="reel_s_chain/f%d" % n, ts=2000 + n)
        visit = tv._chron_visit_step("town", "", None, 2100)
        self.assertEqual(visit["ledger"], "")
        # the classifier refuses to name a kind...
        self.assertIsNone(cr.chronicle_kind({"scene": "chronicle", "chronicleTab": ""}))
        # ...and the console REFUSES to sweep it, out loud
        import control_app as ca
        from unittest import mock
        with ca._CHRON_LOCK:
            ca._CHRON_JOB.update({"running": False, "phase": "idle", "error": None,
                                  "lanes": ["claude"]})
        rows = [{"ts": 4242, "ledger": "", "n": 4, "frames": visit["frames"], "label": "📜"}]
        with mock.patch.object(ca, "chronicle_visits", return_value={"visits": rows}):
            ca._chron_visit_run(4242)
        st = ca.chronicle_sweep_state()
        self.assertEqual(st["phase"], "error")
        self.assertIn("ledger was never read", st["error"])
        self.assertIsNone(st["result"], "a refused sweep must leave NO proposal behind")

    def test_the_two_lanes_speak_the_SAME_contract_end_to_end(self):
        # a seam that could drift on both sides while every suite stayed green
        import g5_grok_eyes as g5
        p = os.path.join(self.reel, "f0.jpg")
        c = self.tv.claude_chronicle_read(p, "chronicle-uniques")
        g = g5.g5_chronicle_read(p, "chronicle-uniques")
        self.assertIsNotNone(c)
        self.assertIsNotNone(g)
        self.assertEqual(sorted(c.keys()), sorted(g.keys()),
                         "the lanes have drifted apart — cross-lane agreement would be meaningless")
        self.assertEqual(c["ledger"], g["ledger"])
        self.assertNotEqual(c["lane"], g["lane"])

    def test_a_dead_second_lane_never_reads_as_agreement(self):
        # the failure that would quietly inflate every witness count in the system
        read = cr.two_lane_reader(lambda p, k: self.tv.claude_chronicle_read(p, k), None)
        resp = read(os.path.join(self.reel, "f0.jpg"), "chronicle-uniques")
        self.assertEqual(resp["lanesRan"], ["claude"])
        self.assertEqual(resp["laneNote"], "grok-silent")
        prop = cr.proposal_from_pages([{"reel": "s1", "frame": "f0.jpg", "resp": resp}])
        for nm, sightings in prop["uniques"].items():
            self.assertNotIn("cross-lane", cr.witnesses(sightings))


if __name__ == "__main__":
    unittest.main(verbosity=2)
