# -*- coding: utf-8 -*-
"""REG-2640 - A RELEASED REEL STAYS RELEASED: THE CLOSER DOES NOT RE-SEAL IT, THE DRAIN DOES NOT RELEASE IT AGAIN, AND THE
RIVER DOES NOT CALL IT STUCK.

His fleet card, 2026-10-24 00:56: "river stuck" on his own Mac row while its census was CURRENT. MEASURED on the Mac the
same minute: 12 reels the drain released (apply_plan keeps a released reel's evidence pictures and deletes the rest) were
released AGAIN on every 15-minute pass since 09-29 - one tombstoned 127 times. Within a minute of each trim the KAI
closer found the reel with no kai_report.json, repaired its index.json, re-read it (stash_eye writes .stash_eye_tab.jpg
beside the frame it OCRs) and sealed it. plan()'s remnant filter asked "holds nothing but its kept pictures?", the
regenerated records said no, so the reel was a candidate again; and the river's stuck reading counted it at ROUTED and
CAPTURE past the window as "the drain owes them a tombstone".

reel_retention.remnant_reels is now the ONE answer: a reel tombstoned with a `kept` list whose every remaining FRAME is a
kept one is released, whatever records the console wrote back. The closer's queue (_kai_close_queue), the plan and the
stuck reading all ask it. A half-trimmed reel (a frame that is not kept) is still not a remnant (the v3521 second eye).
Driven on a throwaway shelf; his tree is never read. RED_PROOF below. [[the-unjoined-end]] [[unknown-stays-unknown]]
"""
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

import reel_retention as RR  # noqa: E402

H = 3600
NOW = 1792800000000
OLD = "reel_s_1500000000000_1"      # released, evidence kept. 2017 epoch, so it pins no recording
HALF = "reel_s_1500000000001_2"     # released, but a frame that is not kept is still there
LIVE = "reel_s_1500000000002_3"     # never released


RED_PROOF = [
    {
        "why": "REG-2640 - the reel's own records count against a remnant again: every regenerated index.json makes a "
               "released reel a candidate, and the drain releases it every pass",
        "file": "reel_retention.py",
        "find": "            left = set(f for f in os.listdir(os.path.join(hist, _r)) if not _remnant_extra(f))\n",
        "replace": "            left = set(os.listdir(os.path.join(hist, _r)))\n",
        "matches": 1,
    },
    {
        "why": "REG-2640 - the KAI closer re-seals a released reel again (it has no kai_report.json)",
        "file": "control_app.py",
        "find": "        if d in _remnants:\n            continue\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-2640 - released reels fill the stuck reading's newest-16 window and push a live reel out as owed",
        "file": "control_app.py",
        "find": "[r for r in _shelf_reel_names() if r not in _released]",
        "replace": "list(_shelf_reel_names())",
        "matches": 1,
    },
    {
        "why": "REG-2640 (r1) - a record's .tmp/.bak/.corrupt sibling un-releases the reel again",
        "file": "reel_retention.py",
        "find": "any(n == r or n.startswith(r + \".\") for r in REMNANT_RECORDS)",
        "replace": "n in REMNANT_RECORDS",
        "matches": 1,
    },
    {
        "why": "REG-2640 (r1) - an unparseable tombstone read is memoised as empty until the file's stamp changes",
        "file": "reel_retention.py",
        "find": "        if key and _whole and (time.time() - _st.st_mtime) > 2.0:\n",
        "replace": "        if key:\n",
        "matches": 1,
    },
    {
        "why": "REG-2640 - the river's stuck reading counts a released reel at ROUTED as owed again",
        "file": "control_app.py",
        "find": "        _on = lambda reel: reel not in _released and os.path.isdir(os.path.join(HIST_DIR, reel))   # noqa: E731\n",
        "replace": "        _on = lambda reel: os.path.isdir(os.path.join(HIST_DIR, reel))   # noqa: E731\n",
        "matches": 1,
    },
    {
        "why": "REG-2640 - a half-trimmed reel (a frame not kept still there) reads as a finished remnant and keeps it for ever",
        "file": "reel_retention.py",
        "find": "        if left <= _k:\n            out.add(_r)\n",
        "replace": "        if left & _k:\n            out.add(_r)\n",
        "matches": 1,
    },
]


def _jpg(path, n=64):
    with open(path, "wb") as fh:
        fh.write(b"\xff\xd8" + b"x" * n)


class _Shelf(unittest.TestCase):
    """A temp shelf: OLD released keeping f_1/f_2 with the records the console writes back, HALF released keeping f_1
    but still holding f_9, LIVE never released. The tombstone store sits where its own writer resolves it."""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="released_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.hist = os.path.join(self.d, "frames", "hist")
        for r in (OLD, HALF, LIVE):
            os.makedirs(os.path.join(self.hist, r))
        for f in ("f_1790000000001.jpg", "f_1790000000002.jpg"):
            _jpg(os.path.join(self.hist, OLD, f))
        # what the closer and stash_eye write back within a minute of the trim (measured on his Mac)
        for f in ("index.json", "kai_report.json"):
            with io.open(os.path.join(self.hist, OLD, f), "w", encoding="utf-8") as fh:
                fh.write("{}")
        _jpg(os.path.join(self.hist, OLD, ".stash_eye_tab.jpg"))
        _jpg(os.path.join(self.hist, HALF, "f_1790000100001.jpg"))
        _jpg(os.path.join(self.hist, HALF, "f_1790000100009.jpg"))
        for f in ("f_1790000200001.jpg", "f_1790000200002.jpg"):
            _jpg(os.path.join(self.hist, LIVE, f))
        self.tomb = RR._tombstone_path(self.hist)
        self.assertTrue(os.path.realpath(self.tomb).startswith(os.path.realpath(self.d)),
                        "PREMISE: the tombstone store resolved OUTSIDE the temp world: %s" % self.tomb)
        self._write_tomb([{"reel": OLD, "kept": ["f_1790000000001.jpg", "f_1790000000002.jpg"]},
                          {"reel": OLD, "kept": ["f_1790000000001.jpg", "f_1790000000002.jpg"]},
                          {"reel": HALF, "kept": ["f_1790000100001.jpg"]}])

    def _write_tomb(self, rows):
        with io.open(self.tomb, "w", encoding="utf-8") as fh:
            json.dump({"reels": rows}, fh)


class TheOneAnswer(_Shelf):

    def test_a_released_reel_with_its_records_written_back_is_still_released(self):
        got = RR.remnant_reels(self.hist)
        self.assertIn(OLD, got, "a released reel holding only its kept pictures and the console's own records is "
                                "not a remnant - the drain will release it again every pass")
        self.assertNotIn(HALF, got, "a half-trimmed reel (a frame that is not kept) read as finished")
        self.assertNotIn(LIVE, got, "a reel never released read as released")

    def test_a_stray_frame_makes_it_a_reel_again(self):
        _jpg(os.path.join(self.hist, OLD, "f_1790000000777.jpg"))
        self.assertNotIn(OLD, RR.remnant_reels(self.hist), "a frame that is not kept is hidden behind the remnant")

    def test_the_records_siblings_are_records_too(self):
        for f in ("kai_report.json.tmp", "kai_report.json.bak_1790000000999", "index.json.corrupt", "index.json.tmp",
                  "gate_pingpong.json"):
            with io.open(os.path.join(self.hist, OLD, f), "w", encoding="utf-8") as fh:
                fh.write("{}")
        self.assertIn(OLD, RR.remnant_reels(self.hist), "a record's .tmp/.bak/.corrupt sibling un-released the reel")
        _jpg(os.path.join(self.hist, OLD, "index.jpg"))
        self.assertNotIn(OLD, RR.remnant_reels(self.hist), "a picture named like a record was hidden as one")

    def test_an_unparseable_read_is_not_remembered(self):
        with io.open(self.tomb, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        old = time.time() - 60
        os.utime(self.tomb, (old, old))
        self.assertEqual(RR.remnant_reels(self.hist), set())
        st = os.stat(self.tomb)
        self.assertNotIn((self.tomb, st.st_mtime_ns, st.st_size), RR._REMNANT_MEMO,
                         "an unparseable tombstone read was cached - a same-stamp rewrite would read as empty for ever")
        self._write_tomb([{"reel": OLD, "kept": ["f_1790000000001.jpg", "f_1790000000002.jpg"]}])
        os.utime(self.tomb, (old, old))
        self.assertIn(OLD, RR.remnant_reels(self.hist), "PREMISE: the good store is not read")
        st = os.stat(self.tomb)
        self.assertIn((self.tomb, st.st_mtime_ns, st.st_size), RR._REMNANT_MEMO, "PREMISE: a settled whole read is not memoised")

    def test_an_unreadable_store_hides_nothing(self):
        with io.open(self.tomb, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        self.assertEqual(RR.remnant_reels(self.hist), set(), "an unreadable tombstone store hid reels on a guess")
        os.remove(self.tomb)
        self.assertEqual(RR.remnant_reels(self.hist), set(), "no tombstone store at all hid reels")


class TheCloserLeavesItAlone(_Shelf):

    def test_the_closer_queue_skips_a_released_reel(self):
        import control_app as ca
        q = ca._kai_close_queue(self.hist, 6)
        self.assertIn(LIVE, q, "PREMISE: an unsealed reel is not queued for a close at all")
        self.assertNotIn(OLD, q, "the closer would re-read and re-seal a released reel - and the drain release it again")
        os.remove(os.path.join(self.hist, OLD, "kai_report.json"))
        os.remove(os.path.join(self.hist, OLD, "index.json"))
        self.assertNotIn(OLD, ca._kai_close_queue(self.hist, 6),
                         "a freshly trimmed reel (no records yet) is queued for a close")


class TheRiverDoesNotCallItStuck(_Shelf):

    def _rows(self):
        def _st(reel, station, ago_s, seq):
            return {"at": NOW - int(ago_s * 1000), "seq": seq, "reel": reel, "station": station,
                    "by": "law", "byKind": "observer"}
        return [_st(OLD, "EMPTY", 40 * H, 1), _st(LIVE, "EMPTY", 30 * H, 2)]

    def test_a_released_reel_is_not_stuck_and_a_held_one_still_is(self):
        import control_app as ca
        with mock.patch.object(ca, "HIST_DIR", self.hist):
            got = ca._river_stuck_for_wire(now_ms=NOW, _rows=self._rows(), _fixtures=())
            self.assertEqual([(e["station"], e["n"]) for e in got or []], [("EMPTY", 1)],
                             "a released reel counted as stuck (or the live one did not): %r" % got)
            self._write_tomb([])
            again = ca._river_stuck_for_wire(now_ms=NOW, _rows=self._rows(), _fixtures=())
        self.assertEqual([(e["station"], e["n"]) for e in again or []], [("EMPTY", 2)],
                         "PREMISE: with no tombstone both reels are on the shelf and both are stuck: %r" % again)

    def test_released_reels_do_not_push_a_live_one_out_of_the_window(self):
        """16 newer released reels must not fill the deleter's newest-16 shield: plan() drops them first, so the stuck
        reading must too, or an older live reel resting at ROUTED reads as 'the drain owes it a tombstone'."""
        import control_app as ca
        rows, kept = [], []
        for i in range(RR.KEEP_RECENT):
            nm = "reel_s_%d_%d" % (1791000000000 + i * 1000, 10 + i)
            os.makedirs(os.path.join(self.hist, nm))
            _jpg(os.path.join(self.hist, nm, "f_%d.jpg" % (1791000000000 + i * 1000)))
            kept.append({"reel": nm, "kept": ["f_%d.jpg" % (1791000000000 + i * 1000)]})
        self._write_tomb(kept)
        rows = [{"at": NOW - 30 * H * 1000, "seq": 1, "reel": LIVE, "station": "ROUTED", "by": "law", "byKind": "observer"}]
        with mock.patch.object(ca, "HIST_DIR", self.hist):
            got = ca._river_stuck_for_wire(now_ms=NOW, _rows=rows, _fixtures=())
        self.assertEqual(got, [], "released reels filled the window and a live reel at ROUTED read as owed: %r" % got)


if __name__ == "__main__":
    unittest.main(verbosity=2)
