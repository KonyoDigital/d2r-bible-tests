# -*- coding: utf-8 -*-
"""REG-1933 - THE THEATRE OPENS THE REEL HE CLICKED, BY ITS ID, NOT BY WHERE IT SAT.

GrokBot (#230, tick 371/372) read three counts of "one" session that disagreed: Session 46's dossier said
FILM FRAMES 49 while the theatre opened from it said "film 64"; S74's card said FILM FRAMES 0 beside a
theatre with "film 11 . 3 AI reads"; the same on S30 and S48. Measured on the Mac's console the same
afternoon (GET only): when the card and the theatre load the SAME reel they agree - 102 = 102, 194 = 194,
594 = 594, 3494 = 3494. What differs is WHICH reel: `/api/session?n=` is a position in a newest-first
list, re-split from the journal on every request, so one session started between the shelf's fetch and
the click moves every reel down a place and `?n=46` answers with the reel that was 45. Nothing checked
the sessionId that came back.

The law: given a sid the server finds the reel by its id in the journal as it is now, whatever n says; a
sid the journal no longer holds is refused, never answered with whatever sits at n; with no sid the old
positional answer is unchanged. The page sends the id it was shown, refuses a reel that comes back under
another id, and the dossier hands in its own reel's id.
Fixtures only: the journal is a list in memory and HIST_DIR is an empty temp dir.
"""
import io
import os
import re
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

import control_app as CA  # noqa: E402


def _rows(sid, t0, k=3):
    return [{"ts": t0 + i * 1000, "sessionId": sid, "lane": "deep", "scene": "town", "names": []}
            for i in range(k)]


OLD = _rows("s_1000_1", 1000000) + _rows("s_2000_2", 2000000) + _rows("s_3000_3", 3000000)
NEW = OLD + _rows("s_4000_4", 4000000)      # one more session started after the shelf was drawn


class _Fake(object):
    def __init__(self, journal):
        self.journal = journal

    def _load_journal_cached(self):
        return list(self.journal)

    def _prewarm_session_frames(self, *a, **k):
        return None

    def _thin_footage_beats(self, beats, *a, **k):
        return beats


class AReelOpensByItsId(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="reel_by_id_")
        self.p = mock.patch.object(CA, "HIST_DIR", self.d)
        self.p.start()

    def tearDown(self):
        self.p.stop()
        shutil.rmtree(self.d, ignore_errors=True)

    def open(self, journal, n, sid=None):
        return CA.Handler._theatre_session(_Fake(journal), n, pack="debug", sid=sid)

    def test_the_fixture_reproduces_the_shift(self):
        """Baseline: the case can tell the two answers apart - by place, n=2 is a different reel once a
        new session has started."""
        self.assertEqual(self.open(OLD, 2).get("sessionId"), "s_2000_2")
        self.assertEqual(self.open(NEW, 2).get("sessionId"), "s_3000_3",
                         "the fixture no longer shifts, so the law below would pass over nothing")

    def test_the_id_wins_over_a_stale_place(self):
        j = self.open(NEW, 2, sid="s_2000_2")
        self.assertEqual(j.get("sessionId"), "s_2000_2",
                         "the theatre answered ?n=2&sid=s_2000_2 with another reel (REG-1933): %s"
                         % j.get("sessionId"))
        self.assertEqual(j.get("n"), 3, "the reel's place NOW is not reported back")
        self.assertTrue(j.get("beats"), "the reel was found and carried no beats")

    def test_a_reel_no_longer_in_the_journal_is_refused(self):
        j = self.open(NEW, 2, sid="s_9999_9")
        self.assertIn("error", j, "a vanished reel was answered with whatever sat at n=2: %s" % j.get("sessionId"))
        self.assertNotIn("beats", j)
        self.assertEqual(j.get("sessionId"), "s_9999_9", "the refusal does not say which reel it could not find")

    def test_no_sid_keeps_the_old_answer(self):
        self.assertEqual(self.open(NEW, 1).get("sessionId"), "s_4000_4")
        self.assertIn("error", self.open(NEW, 99))


def _code(path):
    with io.open(path, encoding="utf-8") as fh:
        src = fh.read()
    return re.sub(r"/\*.*?\*/", "", src, flags=re.S)


class ThePageAsksForTheReelItShowed(unittest.TestCase):

    def setUp(self):
        self.ui = _code(os.path.join(HERE, "control_ui.html"))
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            self.app = fh.read()

    def test_the_route_passes_the_id_through(self):
        self.assertEqual(self.app.count("self._theatre_session(num, pack=pack, sid=_sid_q)"), 1,
                         "/api/session drops ?sid=, so the page's id never reaches the lookup")

    def test_the_load_sends_the_id_it_was_shown(self):
        self.assertEqual(self.ui.count("(_wantSid ? '&sid=' + encodeURIComponent(_wantSid) : '')"), 1,
                         "thLoadSession asks by place only")
        self.assertEqual(self.ui.count(
            "var _wantSid = String(sid || ((TH.sessions && TH.sessions[n - 1]) || {}).sessionId || '');"), 1,
            "thLoadSession no longer takes the id from the row he clicked")

    def test_a_reel_under_another_id_is_not_painted(self):
        self.assertEqual(self.ui.count("if (_wantSid && j.sessionId && String(j.sessionId) !== _wantSid){"), 1,
                         "a reel that came back under another id would be painted as the one he chose")

    def test_the_dossier_hands_in_its_own_reel(self):
        self.assertEqual(self.ui.count("thLoadSession(Number(n) || 1, false, DOSSIER.sid)"), 1,
                         "the dossier's ▶ opens by place, not by the reel it describes")

    def test_the_delete_names_the_reel_he_is_watching(self):
        """The delete is the expensive twin: by place, a shifted list removes the journal rows and frames
        of the reel below his. The lookup above decides it, so the route must hand it the id."""
        self.assertEqual(self.app.count("sess = self._theatre_session(n, sid=_sid_d)"), 1,
                         "/api/session/delete finds its reel by place again")
        self.assertEqual(self.app.count('if _sid_d and sess.get("sessionId") != _sid_d:'), 1,
                         "a delete whose reel came back under another id is not refused")
        self.assertEqual(self.ui.count("JSON.stringify({ n: meta.n || TH.sn, sid: TH.sessionId || meta.sessionId || '' })"), 1,
                         "the theatre's delete does not send the id of the reel he is watching")


RED_PROOF = [
    {
        "why": "REG-1933 - the server finds the reel by id and then ignores it: ?n=2&sid=... answers with "
               "whatever reel now sits at 2",
        "file": "tv/control_app.py",
        "find": "                    return {\"error\": \"reel %s is no longer in the journal - nothing else was opened\" % sid,\n"
                "                            \"sessionId\": sid}\n                n = _at\n",
        "replace": "                    return {\"error\": \"reel %s is no longer in the journal - nothing else was opened\" % sid,\n"
                   "                            \"sessionId\": sid}\n                pass\n",
        "matches": 1,
    },
    {
        "why": "REG-1933 - a sid the journal no longer holds falls through to the positional answer",
        "file": "tv/control_app.py",
        "find": "                if not _at:\n                    return {\"error\": \"reel %s is no longer",
        "replace": "                if False:\n                    return {\"error\": \"reel %s is no longer",
        "matches": 1,
    },
    {
        "why": "REG-1933 - the route stops passing ?sid= through",
        "file": "tv/control_app.py",
        "find": "self._theatre_session(num, pack=pack, sid=_sid_q)",
        "replace": "self._theatre_session(num, pack=pack)",
        "matches": 1,
    },
    {
        "why": "REG-1933 - the page stops checking which reel came back, so a shifted shelf paints a neighbour",
        "file": "tv/control_ui.html",
        "find": "if (_wantSid && j.sessionId && String(j.sessionId) !== _wantSid){",
        "replace": "if (false){",
        "matches": 1,
    },
    {
        "why": "REG-1933 - the delete finds its reel by place again: a shifted shelf deletes the reel below his",
        "file": "tv/control_app.py",
        "find": "sess = self._theatre_session(n, sid=_sid_d)",
        "replace": "sess = self._theatre_session(n)",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
