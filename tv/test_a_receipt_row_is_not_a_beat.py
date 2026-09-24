# -*- coding: utf-8 -*-
"""#238 — A RECEIPT ROW IS NOT A BEAT, AND EVERY JOURNAL ROW CARRIES ITS OWN TIME.

Found by the full local gate run: test_roundtrip_sim errored `'<' not supported between 'int' and 'NoneType'`
on a beat {frameId: snap_0_1.jpg, ts: None} - but only where tv/frames exists (CI's runner has none, so it
stayed green there for as long as it existed). The row was `lane: "deep-owed"`: a RECEIPT that a deep read
was committed to a frame, written with no ts. The theatre session builder emitted it as a playable beat,
and its capture clock fell back to 0 - so it sorted as 1970, ahead of every real frame.

  · DRIVEN: the REAL `_theatre_session` over a crafted journal holding a LEGACY deep-owed row (no ts, as the
    rows already on his disk are) emits no beat for it, and every beat it emits carries a ts.
  · COMPILER: the one writer of deep-owed rows (tv_diablo) stamps "ts" in the dict it journals.
  · PREMISE: the same builder DOES emit ordinary read rows, so the case can fail.
RED_PROOF below.
"""
import ast
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import control_app as ca  # noqa: E402

ROWS = [
    {"ts": 1790000000000, "sessionId": "s1", "scene": "stash", "n": 1, "frameId": "f_1790000000000.jpg", "names": []},
    {"lane": "deep-owed", "frameId": "snap_0_1.jpg", "sessionId": "s1", "why": "committed to the deep reader"},
    {"ts": 1790000005000, "sessionId": "s1", "scene": "stash", "n": 2, "frameId": "f_1790000005000.jpg", "names": []},
]


class AReceiptRowIsNotABeat(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="receipt-beat-")
        self._hist = ca.HIST_DIR
        ca.HIST_DIR = self.d                      # never his live footage
        h = ca.Handler.__new__(ca.Handler)
        h._load_journal_cached = lambda: [dict(r) for r in ROWS]
        h._prewarm_session_frames = lambda *a, **k: None
        self.out = h._theatre_session(1)

    def tearDown(self):
        ca.HIST_DIR = self._hist
        shutil.rmtree(self.d, ignore_errors=True)

    def test_premise_the_read_rows_become_beats(self):
        self.assertIsNone(self.out.get("error"), self.out)
        self.assertEqual([b.get("frameId") for b in self.out["beats"]],
                         ["f_1790000000000.jpg", "f_1790000005000.jpg"])

    def test_a_legacy_receipt_is_not_emitted_as_a_beat(self):
        fids = [b.get("frameId") for b in self.out.get("beats") or []]
        self.assertNotIn("snap_0_1.jpg", fids, "a deep-owed receipt was emitted as a playable beat (it sorts as 1970)")

    def test_every_beat_carries_a_time(self):
        self.assertEqual([b.get("frameId") for b in self.out.get("beats") or [] if b.get("ts") is None], [],
                         "a beat with no ts reached the sort")


class TheReceiptWriterStampsTheTime(unittest.TestCase):

    def test_the_deep_owed_row_carries_ts(self):
        with io.open(os.path.join(HERE, "tv_diablo.py"), encoding="utf-8") as f:
            tree = ast.parse(f.read())
        dicts = [n for n in ast.walk(tree) if isinstance(n, ast.Dict)
                 and any(isinstance(k, ast.Constant) and k.value == "lane" and isinstance(v, ast.Constant)
                         and v.value == "deep-owed" for k, v in zip(n.keys, n.values))]
        self.assertEqual(len(dicts), 1, "premise: exactly one deep-owed writer (found %d)" % len(dicts))
        keys = {k.value for k in dicts[0].keys if isinstance(k, ast.Constant)}
        self.assertIn("ts", keys, "the deep-owed receipt is journaled with no time of its own")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#238 - a deep-owed receipt becomes a playable beat again and sorts as 1970 ahead of every frame",
        "file": "control_app.py",
        "find": "                if r.get(\"lane\") == \"deep-owed\":\n                    continue\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#238 - the deep-owed receipt is journaled with no time of its own again",
        "file": "tv_diablo.py",
        "find": "                              \"ts\": int(time.time() * 1000),\n                              \"frameId\": os.path.basename(str(snap_path or \"\")),\n",
        "replace": "                              \"frameId\": os.path.basename(str(snap_path or \"\")),\n",
        "matches": 1,
    },
]
