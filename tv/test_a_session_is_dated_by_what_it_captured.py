# -*- coding: utf-8 -*-
"""REG-2736 (#86) - A SESSION IS ORDERED AND DATED BY WHAT IT CAPTURED, NOT BY WHEN SOMETHING WAS LAST WRITTEN ABOUT IT.

MEASURED on his journal 2026-10-28: the Shelf's first eight rows were September and October reels, and its LAST SESSION
digest named an October 10 reel - the KAI closer had re-closed them all morning (the REG-2728 loop) and each re-close
wrote rows with ts = today: kai-funnel receipts (with the frame's captureTs), the KAI closer's "closed the session" note
(ts and captureTs both today, dated from the session's newest row - the previous note - so 59 re-closes walked one
September reel to today) and the watchdog's verdict. split_sessions ordered sessions by their newest ts, and the row
took t0/t1 from the first and last ts, so one reel read a 17-day span (readMs 1,490,631,272).

A row's moment is its frame's capture time when it carries one (replay.row_moment); the KAI ledger and the watchdog
annotate a session after it and are left out of its moments (POST_HOC_LANES), every row counting only when nothing else
is there. Driven on replay.split_sessions and the real Handler._theatre_sessions over a fixture journal and reel tree.
RED_PROOF below.
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
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import replay as RP  # noqa: E402

OLD, NEW = "s_1790000000000_11", "s_1793000000000_22"
T_OLD = 1790000060000            # the old reel's reads, a minute of them
T_NEW = 1793000060000            # the new reel's reads, two minutes of them
T_LATE = T_NEW + 3600000         # an hour after the new reel ended, the old one is re-read


def _rows():
    rows = []
    for k in range(3):                                   # the old reel: three reads over 60 s
        t = T_OLD + k * 30000
        rows.append({"ts": t, "captureTs": t, "frameId": "%d_%d" % (k + 1, t), "n": k + 1, "names": [],
                     "sessionId": OLD, "scene": "gameplay"})
    for k in range(3):                                   # the new reel: three reads over 120 s
        t = T_NEW + k * 60000
        rows.append({"ts": t, "captureTs": t, "frameId": "%d_%d" % (k + 1, t), "n": k + 1, "names": [],
                     "sessionId": NEW, "scene": "gameplay"})
    # the re-read of the OLD reel, written after the new one ended
    rows.append({"ts": T_LATE, "captureTs": T_OLD + 30000, "completedTs": T_LATE, "lane": "intake", "sessionId": OLD,
                 "intake": {"kind": "kai-funnel", "ok": False, "total": 0, "errors": 1}, "frameId": "2_%d" % (T_OLD + 30000)})
    rows.append({"ts": T_LATE + 1, "captureTs": T_LATE + 1, "lane": "kai", "mode": "kai", "scene": "kai", "sessionId": OLD,
                 "note": "KAI closed the session"})
    rows.append({"ts": T_LATE + 2, "captureTs": T_LATE + 2, "lane": "watchdog", "sessionId": OLD})
    rows.sort(key=lambda r: r["ts"])
    return rows


def _ids(groups):
    return [next((r.get("sessionId") for r in g if r.get("sessionId")), None) for g in groups]


class ASessionIsOrderedByWhatItCaptured(unittest.TestCase):

    def test_a_reel_re_read_later_keeps_its_place(self):
        rows = _rows()
        self.assertGreater(max(r["ts"] for r in rows if r["sessionId"] == OLD),
                           max(r["ts"] for r in rows if r["sessionId"] == NEW),
                           "PREMISE: the old reel was not written to after the new one ended")
        self.assertEqual(_ids(RP.split_sessions(rows)), [NEW, OLD],
                         "a re-read of an old reel moved it above the newer session")

    def test_a_row_moment_is_its_capture_time(self):
        self.assertEqual(RP.row_moment({"ts": 9, "captureTs": 3}), 3)
        self.assertEqual(RP.row_moment({"ts": 9}), 9)
        self.assertEqual(RP.row_moment({"ts": 9, "captureTs": True}), 9, "a boolean is not a time")

    def test_post_hoc_notes_are_left_out_unless_nothing_else_is_there(self):
        g = [{"ts": 5, "captureTs": 5}, {"lane": "kai", "ts": 99, "captureTs": 99}, {"lane": "watchdog", "ts": 98}]
        self.assertEqual(RP.session_moments(g), [5])
        self.assertEqual(RP.session_moments([{"lane": "kai", "ts": 7, "captureTs": 7}]), [7],
                         "a session holding only a KAI note lost its only moment")

    def test_a_re_read_counts_only_through_its_capture_time(self):
        """REG-2744 (the v3821 second eye) - a verify or intake row with no capture time is when the re-read WROTE."""
        live = {"ts": 5, "captureTs": 5}
        self.assertEqual(RP.session_moments([live, {"lane": "verify", "ts": 999}]), [5],
                         "a verify row with no capture time dated the session by when it was written")
        self.assertEqual(RP.session_moments([live, {"lane": "intake", "ts": 999}]), [5])
        self.assertEqual(sorted(RP.session_moments([live, {"lane": "intake", "ts": 999, "captureTs": 7}])), [5, 7],
                         "an intake row's own capture time stopped counting")


class TheShelfRowCarriesTheCapturedSpan(unittest.TestCase):

    def test_t0_t1_and_the_read_span_come_from_what_was_captured(self):
        d = tempfile.mkdtemp(prefix="session-dated-")
        self.addCleanup(shutil.rmtree, d, True)
        hist = os.path.join(d, "hist")
        for sid in (OLD, NEW):
            os.makedirs(os.path.join(hist, "reel_" + sid))
        journal = os.path.join(d, "sessions.jsonl")
        with open(journal, "w", encoding="utf-8") as fh:
            for r in _rows():
                fh.write(json.dumps(r) + "\n")
        import control_app as ca
        keep = (ca.HIST_DIR, RP.JOURNAL)
        ca.HIST_DIR, RP.JOURNAL = hist, journal
        cached = ca.__dict__.pop("_JRNL_CACHE", None)
        try:
            h = ca.Handler.__new__(ca.Handler)
            out = ca.Handler._theatre_sessions(h)
        finally:
            ca.HIST_DIR, RP.JOURNAL = keep
            ca.__dict__.pop("_JRNL_CACHE", None)
            if cached is not None:
                ca._JRNL_CACHE = cached
        self.assertIsInstance(out, list, "the shelf answered an error: %r" % (out,))
        by = dict((r.get("sessionId"), r) for r in out)
        self.assertEqual([r.get("sessionId") for r in out][:2], [NEW, OLD], "the Shelf put the re-read reel first")
        old = by[OLD]
        self.assertEqual((old.get("t0"), old.get("t1")), (T_OLD, T_OLD + 60000),
                         "the old reel is dated by when it was last written about: %r" % ({k: old.get(k) for k in ("t0", "t1")},))
        self.assertEqual(old.get("readMs"), 60000, "the read span stretched to the re-read: %r" % old.get("readMs"))
        self.assertEqual(old.get("reads"), 3, "REG-2744 - the watchdog's verdict was counted as a read: %r" % old.get("reads"))
        self.assertEqual((by[NEW].get("t0"), by[NEW].get("t1")), (T_NEW, T_NEW + 120000))

    def test_a_run_with_film_spans_its_film(self):
        """REG-2748 (GrokBot's v3821 pass) - a card read "0m00s" beside "3127 frames · full video": one read, an hour of
        film. The footage stills are captures of the session (f_<capture ms>.jpg), so the span covers them."""
        d = tempfile.mkdtemp(prefix="session-film-")
        self.addCleanup(shutil.rmtree, d, True)
        hist = os.path.join(d, "hist")
        for sid in (OLD, NEW):
            os.makedirs(os.path.join(hist, "reel_" + sid))
        for ts in (T_NEW - 30000, T_NEW + 60000, T_NEW + 600000):
            open(os.path.join(hist, "reel_" + NEW, "f_%d.jpg" % ts), "wb").close()
        journal = os.path.join(d, "sessions.jsonl")
        with open(journal, "w", encoding="utf-8") as fh:
            for r in _rows():
                fh.write(json.dumps(r) + "\n")
        import control_app as ca
        keep = (ca.HIST_DIR, RP.JOURNAL)
        ca.HIST_DIR, RP.JOURNAL = hist, journal
        cached = ca.__dict__.pop("_JRNL_CACHE", None)
        try:
            out = ca.Handler._theatre_sessions(ca.Handler.__new__(ca.Handler))
        finally:
            ca.HIST_DIR, RP.JOURNAL = keep
            ca.__dict__.pop("_JRNL_CACHE", None)
            if cached is not None:
                ca._JRNL_CACHE = cached
        by = dict((r.get("sessionId"), r) for r in out)
        self.assertEqual(by[NEW].get("footageN"), 3, "PREMISE: the film stills were not counted: %r" % by[NEW].get("footageN"))
        self.assertEqual((by[NEW].get("t0"), by[NEW].get("t1")), (T_NEW - 30000, T_NEW + 600000),
                         "the run is dated by its reads alone, not its film: %r" % ({k: by[NEW].get(k) for k in ("t0", "t1")},))
        self.assertEqual((by[OLD].get("t0"), by[OLD].get("t1")), (T_OLD, T_OLD + 60000), "a reel with no film moved")


RED_PROOF = [
    {"why": "REG-2748 - a run with film is dated by its reads alone again (0m00s beside an hour of footage)",
     "file": "control_app.py",
     "find": "                                    _foot_span.append(_fts)\n",
     "replace": "                                    pass\n",
     "matches": 1},
    {"why": "REG-2744 - a re-read row with no capture time dates the session by when it wrote",
     "file": "replay.py",
     "find": "        return int(cap) if isinstance(cap, (int, float)) and not isinstance(cap, bool) and cap > 0 else 0\n",
     "replace": "        return row_moment(r)\n",
     "matches": 1},
    {"why": "REG-2744 - the read count keeps its own lane list and counts the watchdog's verdict",
     "file": "control_app.py",
     "find": "                            \"reads\": len([r2 for r2 in sess if _is_a_live_read(r2)]),",
     "replace": "                            \"reads\": len([r2 for r2 in sess if _is_a_live_read(r2) or r2.get(\"lane\") == \"watchdog\"]),",
     "matches": 1},
    {"why": "REG-2736 - sessions are ordered by their newest WRITTEN row again (a re-read reel jumps to the top)",
     "file": "tv/replay.py",
     "find": "    sessions.sort(key=lambda g: max(session_moments(g) or [0]))\n",
     "replace": "    sessions.sort(key=lambda g: max((r.get(\"ts\") or 0) for r in g))\n",
     "matches": 1},
    {"why": "REG-2736 - a row's moment ignores its capture time",
     "file": "tv/replay.py",
     "find": "    c = (r or {}).get(\"captureTs\")\n    if isinstance(c, (int, float)) and not isinstance(c, bool) and c > 0:\n",
     "replace": "    c = None\n    if isinstance(c, (int, float)) and not isinstance(c, bool) and c > 0:\n",
     "matches": 1},
    {"why": "REG-2736 - the KAI ledger and the watchdog date the session again",
     "file": "tv/replay.py",
     "find": "POST_HOC_LANES = (\"kai\", \"watchdog\")\n",
     "replace": "POST_HOC_LANES = ()\n",
     "matches": 1},
    {"why": "REG-2736 - the Shelf row's t1 is its last written row again",
     "file": "tv/control_app.py",
     "find": "                            \"t1\": max((_rp.session_moments(sess) or []) + _foot_span or [0]) or sess[-1].get(\"ts\"),\n",
     "replace": "                            \"t1\": sess[-1].get(\"ts\"),\n",
     "matches": 1},
    {"why": "REG-2736 - the watchdog's verdict counts as a read and stretches the read span",
     "file": "tv/control_app.py",
     "find": "            and r2.get(\"kind\") != \"skip\" and r2.get(\"lane\") not in (\"kai\", \"verify\", \"intake\", \"watchdog\"))\n",
     "replace": "            and r2.get(\"kind\") != \"skip\" and r2.get(\"lane\") not in (\"kai\", \"verify\", \"intake\"))\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
