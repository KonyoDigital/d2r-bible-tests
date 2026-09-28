#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AN EVIDENCE PICTURE IS NEVER LOST TO THE RECORDER'S DISK FLOOR — and a read keeps its picture under it.

His words, 2026-09-28: "how can i see the evidence and picture pixels from the session it was extracted from",
and his order the same day: "evidence pictures are never lost to a reaper or the disk floor".

MEASURED that day (read-only, a copy of his tree): the reads that named String of Ears and seven Chronicle-page
items were taken 02:32-02:42 and NONE of their frames were on disk; the session's reel began at 02:44. In
tv/tv_diablo.py, three doors, none of which asked whether a frame was evidence:
  (a) under MIN_FREE_GB the recorder refused to archive any frame ("disk-full") while the reader kept reading;
  (b) an in-loop reaper deleted up to 600 loose f_*.jpg older than 15 min every 120 s under the floor, with NO
      evidence check (its sibling eviction already protected _journal_frame_ids());
  (c) the disk-floor REEL reaper spared only sessions cited in vault_accum.json — not frame_authority's witness
      index, not chron_evidence's reels — and took reel_s_1786385768689_67392, whose frames chron_evidence cites.

WHAT THIS LAW DRIVES (the SHIPPED recorder functions, on a temp shelf — TV_HIST-style isolation: HIST_DIR and
JOURNAL are repointed, and every ledger is written beside the temp shelf, never his):
  (b) _reap_loose_film spares a frame the journal names and a frame the evidence authority cites, takes the rest
      once they are old, keeps the young, REFUSES when a ledger will not read, and records by name what it took;
  (c) archive_read_frame's own disk-floor block, driven under a patched disk: a reel holding a cited picture
      keeps it and releases the rest; a reel cited whole (its session, no file of it named) is kept whole; a
      reel nothing cites goes whole; the two newest never; every act is in reel_reaps.jsonl with its names;
      an unreadable ledger refuses the reap;
  (a) the same call keeps the read's picture SMALL under the floor, refuses it below the hard floor and when the
      hour's budget is spent — and records each refusal, so "never written" is an answer the doctor can give.
RED_PROOF below.
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

import tv_diablo as T  # noqa: E402
import read_pictures as RP  # noqa: E402

GB = 1e9
NOW_MS = int(time.time() * 1000)
OLD = NOW_MS - 3 * 3600 * 1000          # three hours ago — past the 15-minute youth shield


class _Usage(object):
    def __init__(self, free):
        self.free, self.total, self.used = free, 500 * GB, 500 * GB - free


def _jpg(path, w=2000, h=1200):
    try:
        from PIL import Image
        Image.new("RGB", (w, h), (40, 30, 20)).save(path, "JPEG", quality=80)
    except Exception:
        with open(path, "wb") as fh:            # a minimal real JPEG header — enough for the copy paths
            fh.write(b"\xff\xd8\xff\xe0" + b"\x00" * 5000 + b"\xff\xd9")


class _Shelf(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="evid_reap_")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.hist = os.path.join(self.root, "frames", "hist")
        os.makedirs(self.hist)
        self.journal = os.path.join(self.root, "sessions.jsonl")
        io.open(self.journal, "w", encoding="utf-8").close()
        for name, val in (("HIST_DIR", self.hist), ("JOURNAL", self.journal)):
            saved = getattr(T, name)
            setattr(T, name, val)
            self.addCleanup(setattr, T, name, saved)
        saved_state = dict(T._JFID_STATE)
        T._JFID_STATE.update({"path": None, "ids": None})
        self.addCleanup(lambda: (T._JFID_STATE.clear(), T._JFID_STATE.update(saved_state)))
        # the footage door provisions whatever TV_HIST names — point it at THIS shelf, never his
        env = mock.patch.dict(os.environ, {"TV_HIST": self.hist})
        env.start()
        self.addCleanup(env.stop)
        for g in ("_FOOTAGE_ESTABLISHED", "_FOOTAGE_BROKEN_KEY"):
            self.addCleanup(T.__dict__.__setitem__, g, T.__dict__.get(g))
            T.__dict__[g] = None
        saved_due = T.__dict__.get("_ORPHAN_DUE")
        T._ORPHAN_DUE = 0.0
        self.addCleanup(lambda: T.__dict__.__setitem__("_ORPHAN_DUE", saved_due or 0.0))

    def ledgers(self, accum=None, chron=None):
        for fn, val in (("vault_accum.json", accum), ("chron_evidence.json", chron)):
            if val is not None:
                with io.open(os.path.join(self.root, fn), "w", encoding="utf-8") as fh:
                    fh.write(val if isinstance(val, str) else json.dumps(val))

    def journal_rows(self, rows):
        with io.open(self.journal, "a", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        T._JFID_STATE.update({"path": None, "ids": None})

    def reaps(self):
        return RP.load_jsonl(os.path.join(self.root, RP.REAPS)) or []

    def refusals(self):
        return RP.load_jsonl(os.path.join(self.root, RP.REFUSALS)) or []


class TheLooseFilmReaperAsksFirst(_Shelf):
    """(b)"""

    def _film(self):
        names = {"cited": "f_%d.jpg" % (OLD + 1), "read": "f_%d.jpg" % (OLD + 2), "free": "f_%d.jpg" % (OLD + 3),
                 "young": "f_%d.jpg" % (NOW_MS - 60 * 1000)}
        for n in names.values():
            _jpg(os.path.join(self.hist, n), 40, 30)
        return names

    def test_it_spares_a_read_bearing_and_a_cited_frame_and_takes_the_rest(self):
        n = self._film()
        self.ledgers(accum={"owned": [{"name": "Nagelring", "lane": "stash", "kind": "item",
                                       "witnesses": [{"session": "s_1", "frame": n["cited"], "conf": 0.9}]}]})
        self.journal_rows([{"lane": "deep", "frameId": "reel_s_9/" + n["read"][:-4], "names": ["Shako"], "ts": OLD + 2}])
        got = T._reap_loose_film(self.hist, now_s=NOW_MS / 1000.0)
        left = sorted(os.listdir(self.hist))
        self.assertIn(n["cited"], left, "a frame the vault ledger cites was reaped")
        self.assertIn(n["read"], left, "a frame a read was taken from was reaped")
        self.assertIn(n["young"], left, "the youth shield was broken")
        self.assertNotIn(n["free"], left, "BASELINE: an uncited old frame must go, or this case proves nothing")
        self.assertEqual((1, 2, None), (got["removed"], got["spared"], got["refused"]))
        rec = [r for r in self.reaps() if r.get("by") == "recorder-loose-floor"]
        self.assertEqual([[n["free"]]], [r.get("names") for r in rec], "the reaper did not record what it took, by name")

    def test_an_unreadable_ledger_deletes_nothing(self):
        n = self._film()
        self.ledgers(accum="{")
        got = T._reap_loose_film(self.hist, now_s=NOW_MS / 1000.0)
        self.assertEqual(sorted(n.values()), sorted(os.listdir(self.hist)))
        self.assertTrue(got["refused"])
        self.assertEqual(0, got["removed"])

    def test_the_recorder_loop_calls_it(self):
        import inspect
        src = inspect.getsource(T)
        i = src.index("# reap old film if disk tight")
        blk = src[i:src.index("# Retina polish for live stage", i)]
        code = "\n".join(l.split("#", 1)[0] for l in blk.split("\n"))
        self.assertIn("_reap_loose_film(hist_dir)", code, "the in-loop reaper no longer asks before it deletes")
        self.assertNotIn("os.remove(", code, "the in-loop reaper deletes on its own again")


class TheReelReaperKeepsTheEvidence(_Shelf):
    """(c) and (a), through the SHIPPED archive_read_frame under a patched disk."""

    R = ["reel_s_1784000000001_1", "reel_s_1784000000002_2", "reel_s_1784000000003_3",
         "reel_s_1784000000004_4", "reel_s_1784000000005_5", "reel_s_1784000000006_6"]

    def _reels(self):
        for i, r in enumerate(self.R):
            d = os.path.join(self.hist, r)
            os.makedirs(d)
            for k in range(3):
                _jpg(os.path.join(d, "f_17840000%02d%03d.jpg" % (i + 1, k)), 40, 30)
        self.ledgers(
            accum={"owned": [
                {"name": "Nagelring", "lane": "stash", "kind": "item",
                 "witnesses": [{"session": "s_1784000000001_1", "frame": "f_1784000001000.jpg", "conf": 0.9}]},
                {"name": "Magefist", "lane": "stash", "kind": "item",
                 "witnesses": [{"session": "s_1784000000003_3", "frame": "f_elsewhere.jpg", "conf": 0.9}]}]},
            chron={"uniques": {"Stormshield": [{"reel": "reel_s_1784000000002_2", "frame": "f_1784000002001.jpg",
                                                "conf": 0.9}]}, "sets": {}})
        self.src = os.path.join(self.root, "live.jpg")
        _jpg(self.src)

    def _press(self, free_gb=5.0, n=1):
        with mock.patch("shutil.disk_usage", return_value=_Usage(free_gb * GB)):
            T._ORPHAN_DUE = 0.0
            return T.archive_read_frame(self.src, n, NOW_MS + n)

    def _files(self, reel):
        d = os.path.join(self.hist, reel)
        return sorted(os.listdir(d)) if os.path.isdir(d) else None

    def test_each_pass_takes_only_what_nothing_cites(self):
        self._reels()
        self._press(n=1)
        self.assertEqual(["f_1784000001000.jpg"], self._files(self.R[0]),
                         "pass 1: the reel holding a vault-cited picture did not keep exactly that picture")
        self._press(n=2)
        self.assertEqual(["f_1784000002001.jpg"], self._files(self.R[1]),
                         "pass 2: the reel holding a chron_evidence-cited picture did not keep exactly that picture")
        self._press(n=3)
        self.assertEqual(3, len(self._files(self.R[2]) or []), "a reel cited WHOLE (its session) lost frames")
        self.assertIsNone(self._files(self.R[3]), "BASELINE: the reel nothing cites must go, or this proves nothing")
        self._press(n=4)
        for r in self.R[4:]:
            self.assertEqual(3, len(self._files(r) or []), "one of the two newest reels was touched: %s" % r)
        rows = [r for r in self.reaps() if r.get("by") == "recorder-disk-floor"]
        self.assertEqual([self.R[0], self.R[1], self.R[3]], [r["reel"] for r in rows])
        self.assertEqual(["f_1784000001000.jpg"], rows[0].get("kept"))
        self.assertEqual(2, len(rows[0].get("names") or []), "the partial release did not record what it took")
        self.assertEqual(3, len(rows[2].get("names") or []))

    def test_an_unreadable_ledger_refuses_every_reel(self):
        self._reels()
        self.ledgers(chron="{")
        self._press()
        for r in self.R:
            self.assertEqual(3, len(self._files(r) or []), "a reel was reaped while the evidence could not be read")

    def test_a_read_keeps_a_small_picture_under_the_floor(self):
        self._reels()
        fid = self._press(free_gb=5.0, n=7)
        self.assertTrue(fid, "no picture was kept for a read under the floor")
        p = os.path.join(self.hist, fid + ".jpg")
        self.assertTrue(os.path.isfile(p))
        try:
            from PIL import Image
            with Image.open(p) as im:
                self.assertLessEqual(max(im.size), RP.FLOOR_MAX_PX, "the floor-time picture was not kept small")
        except ImportError:
            pass
        spent = [r for r in self.refusals() if r.get("why") == "saved-small"]
        self.assertEqual([fid], [r["frameId"] for r in spent], "the budget's own ledger did not record the picture")

    def test_below_the_hard_floor_it_is_refused_and_recorded(self):
        self._reels()
        fid = self._press(free_gb=0.5, n=8)
        self.assertEqual("", fid)
        ref = [r for r in self.refusals() if r.get("why") == "hard-floor"]
        self.assertEqual(1, len(ref), "a refused picture left no record")
        self.assertTrue(ref[0]["frameId"].startswith("8_"))
        for r in self.R:
            self.assertEqual(3, len(self._files(r) or []), "a refused read still ran the eviction")

    def test_a_spent_budget_refuses_and_says_so(self):
        self._reels()
        with io.open(os.path.join(self.root, RP.REFUSALS), "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": NOW_MS - 1000, "frameId": "1_1", "why": "saved-small",
                                 "mb": RP.FLOOR_BUDGET_MB_PER_HOUR + 1}) + "\n")
        fid = self._press(free_gb=5.0, n=9)
        self.assertEqual("", fid)
        self.assertTrue(any(r.get("why") == "floor-budget-spent" for r in self.refusals()))

    def test_a_healthy_disk_keeps_the_full_picture(self):
        self._reels()
        fid = self._press(free_gb=50.0, n=10)
        self.assertTrue(fid)
        self.assertFalse(any(r.get("why") == "saved-small" for r in self.refusals()),
                         "a healthy disk was charged against the floor budget")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "(b) the loose-film reaper deletes read-bearing and cited frames again",
        "file": "tv_diablo.py",
        "find": "        if dead in protected:\n            spared += 1\n            continue\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "(b) an unreadable ledger reads as 'nothing is cited' and the reaper deletes",
        "file": "tv_diablo.py",
        "find": "    ev = _reel_evidence(hist_dir)\n    if ev is None:\n",
        "replace": "    ev = _reel_evidence(hist_dir) or {\"frames\": set(), \"sessions\": set(), \"reels\": set()}\n    if ev is None:\n",
        "matches": 1,
    },
    {
        "why": "(c) the reel reaper takes a reel whole although it holds a cited picture",
        "file": "tv_diablo.py",
        "find": "        cited = [f for f in jpgs if f in ev[\"frames\"]]\n",
        "replace": "        cited = []\n",
        "matches": 1,
    },
    {
        "why": "(c) the reel reaper asks vault_accum only again — chron_evidence's receipts are not evidence",
        "file": "tv_diablo.py",
        "find": "        rows, _why = _rr.evidence_rows_at(root)\n",
        "replace": "        rows, _why = [], ''\n",
        "matches": 1,
    },
    {
        "why": "(c) a reel cited whole (its session) is taken",
        "file": "tv_diablo.py",
        "find": "        if sid in ev[\"sessions\"] or cand in ev[\"reels\"]:\n            continue\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "(a) below the hard floor the refusal leaves no record — a missing picture with no reason",
        "file": "tv_diablo.py",
        "find": "                _rpr.record_refusal(HIST_DIR, fid, _pwhy, _pfree, SESSION_ID)\n",
        "replace": "                pass\n",
        "matches": 1,
    },
    {
        "why": "(a) under the floor the read's picture is written at full size (no budget, no downscale)",
        "file": "tv_diablo.py",
        "find": "        if _pmode == \"small\":\n            try:\n                import read_pictures as _rps\n",
        "replace": "        if False:\n            try:\n                import read_pictures as _rps\n",
        "matches": 1,
    },
]
