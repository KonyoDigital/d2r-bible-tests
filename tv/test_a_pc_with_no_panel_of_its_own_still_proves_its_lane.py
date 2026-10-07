# -*- coding: utf-8 -*-
"""REG-1959 - A PC THAT NEVER SAW A STASH PANEL STILL PROVES ITS VAULT LANE LIVE, WITH THE SHIPPED CANARY.

His question 2026-10-07 ("make sure the Windows alt pc isnt stuck or LOOPING reads on something that should be
tombstoned and extracted and then deleted"), measured over SSH: the ALT's vault lane gave every reel the same reason -
"the lane could not be proven live, so 'no stash here' is UNKNOWN" - tried each twice, retired 15 un-extracted, and
sealed nothing the river could release. Its tv/stash_gate_cache.json does not exist (it films the Boosteroid launcher,
the lobby and gameplay; 0 stash tabs in its session health), so LaneCanary.known_good_frame() had nothing to offer and
the proof could never pass. A tracked stash-panel frame now stands in, its identity the pinned sha256.

Fixtures only: the gate cache is stubbed empty or with a fixture row; the frames are the repo's own fixture pack.
"""
import io
import os
import shutil
import sys
import tempfile
import unittest
import unittest.mock as mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

_T = tempfile.mkdtemp(prefix="canary_law_")
os.environ.setdefault("TV_GATE_CACHE", os.path.join(_T, "gate_cache.json"))
import control_app as CA  # noqa: E402

ROOT = os.path.dirname(HERE)
PACK = os.path.join(ROOT, "fixtures", "pack-stash-001", "reels", "reel_s_1784984019250_fxstash001")


class APcWithNoPanelOfItsOwnStillProvesItsLane(unittest.TestCase):

    def test_an_empty_gate_cache_falls_back_to_the_shipped_canary(self):
        with mock.patch.object(CA, "_gate_cache", lambda: {}):
            got = CA.LaneCanary().known_good_frame()
        self.assertIsNotNone(got, "a PC with no panel of its own has no canary (REG-1959)")
        self.assertEqual(os.path.basename(got), "f_1784984191754.jpg")

    def test_the_shipped_canary_proves_the_lane_live(self):
        with mock.patch.object(CA, "_gate_cache", lambda: {}):
            cn = CA.LaneCanary()
            self.assertTrue(cn.probe(cn.known_good_frame()),
                            "the shipped canary did not prove a live lane - the ALT's reels stay UNKNOWN for ever")

    def test_a_tampered_copy_is_never_the_canary(self):
        d = tempfile.mkdtemp(prefix="canary_tamper_")
        try:
            for rel, _sha in CA.SHIPPED_CANARY_FRAMES:
                dst = os.path.join(d, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(os.path.join(ROOT, rel), "rb") as fh:
                    data = fh.read()
                with open(dst, "wb") as fh:
                    fh.write(data[:-16] + b"\x00" * 16)
            self.assertIsNone(CA._shipped_canary(root=d), "a frame whose bytes changed was taken as the canary")
            self.assertIsNotNone(CA._shipped_canary(root=ROOT), "baseline: the real fixture is not recognised")
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_a_pc_with_its_own_panel_keeps_using_it(self):
        own = os.path.join(PACK, "f_1784984211738.jpg")
        st = os.stat(own)
        with mock.patch.object(CA, "_gate_cache", lambda: {own: [int(st.st_size), int(st.st_mtime), "stash"]}):
            got = CA.LaneCanary().known_good_frame()
        self.assertEqual(got, own, "a PC's own known-good frame was passed over for the shipped one")


def tearDownModule():
    shutil.rmtree(_T, ignore_errors=True)


RED_PROOF = [
    {
        "why": "REG-1959 - no fallback: a PC that never saw a panel can never prove its vault lane live",
        "file": "tv/control_app.py",
        "find": "        return _shipped_canary()   # REG-1959",
        "replace": "        return None   # REG-1959",
        "matches": 1,
    },
    {
        "why": "REG-1959 - the pinned hash is not checked: any file at that path becomes the canary",
        "file": "tv/control_app.py",
        "find": "                if _hl.sha256(fh.read()).hexdigest() == want:\n",
        "replace": "                if True:\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
