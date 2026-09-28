# -*- coding: utf-8 -*-
"""A drop in his published progress is ONE episode, opened once and closed on recovery.

MEASURED on his board_tally.json (read-only, 2026-09-28): all 40 rows of `drops` were ONE event,
sets 134 -> 0. board_tally_merge appended a drop on EVERY tally while a lane sat below its
high-water mark, the mark only rises, and the board posts about once a minute — so one fall
filled the rolling record in 40 minutes and evicted every earlier drop it had ever seen.

ledger_restore already owns what a drop IS and its lifecycle (step_episodes: open once, close
when the count is back) — the backup watcher runs it once per snapshot. board_tally_merge now
runs the same function once per tally, from the lane's high-water mark. One definition, two
callers. [[copy-drift]] [[the-unjoined-end]]

Fixtures only: _board_tally_path is pointed at a temp dir; his board_tally.json is never opened.
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

import control_app as CA
import ledger_restore as LR

OWNER = {"id": "0wner00000000000000000000000000a", "p": "main", "pfx": ""}
GUEST = {"id": "9uest00000000000000000000000000b", "p": "main", "pfx": "I-9uest000-"}


class ADropIsAnEpisode(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="drop-episode-")
        self._orig = CA._board_tally_path
        CA._board_tally_path = lambda: os.path.join(self.d, "board_tally.json")
        self.addCleanup(setattr, CA, "_board_tally_path", self._orig)
        self.addCleanup(shutil.rmtree, self.d, True)

    def _post(self, who, sets, uni, at, rw=99):
        return CA.board_tally_merge({"v": 2, "who": who, "route": who, "at": at,
                                     "sets": {"have": sets, "total": 135},
                                     "uniques": {"have": uni, "total": 403},
                                     "runewords": {"have": rw, "total": 99}})

    def _doc(self):
        with open(os.path.join(self.d, "board_tally.json"), encoding="utf-8") as fh:
            return json.load(fh)

    def _eps(self, lane, who=OWNER):
        rk = CA._route_key(who)
        return [e for e in self._doc()["drops"]
                if isinstance(e, dict) and e.get("lane") == lane and e.get("routeKey") == rk]

    def test_sitting_at_zero_for_an_hour_is_one_drop_not_sixty(self):
        self._post(OWNER, 134, 280, 1000)
        for i in range(60):                           # an hour of tallies at 0
            self._post(OWNER, 0, 280, 2000 + i * 60000)
        eps = self._eps("sets")
        self.assertEqual(1, len(eps), "one fall was filed %d times — the 40-slot defect" % len(eps))
        self.assertEqual((134, 0, True), (eps[0]["from"], eps[0]["to"], eps[0]["open"]))
        self.assertEqual(2000, eps[0]["at"], "the episode is dated by the tally that fell")

    def test_a_recovery_closes_the_episode_and_a_new_fall_opens_a_new_one(self):
        self._post(OWNER, 134, 280, 1000)
        self._post(OWNER, 0, 280, 2000)
        self._post(OWNER, 0, 280, 3000)
        self._post(OWNER, 134, 280, 4000)
        eps = self._eps("sets")
        self.assertEqual(1, len(eps))
        self.assertFalse(eps[0]["open"], "the count came back and the episode stayed open")
        self.assertEqual((4000, 134), (eps[0]["closedAt"], eps[0]["closedCount"]))
        self._post(OWNER, 20, 280, 5000)
        eps = self._eps("sets")
        self.assertEqual(2, len(eps), "a second, separate fall was not its own episode")
        self.assertEqual([False, True], [e["open"] for e in eps])

    def test_the_drop_line_is_ledger_restores(self):
        # PIN THE LAW, NOT THE NUMBER: whatever ledger_restore calls a drop is what opens one here.
        def blob(n):
            return {"ledger": {}, "counts": {"setPieces": n}}
        # baseline first: both counts are READ (not UNKNOWN), or `small == []` would be vacuous
        self.assertEqual(134, LR.store_count(blob(134), "setPieces"))
        small = LR.drops_between(blob(134), blob(130))
        big = LR.drops_between(blob(134), blob(60))
        self.assertEqual([], small)
        self.assertEqual(1, len(big))
        self._post(OWNER, 134, 280, 1000)
        self._post(OWNER, 130, 280, 2000)
        self.assertEqual([], self._eps("sets"), "a fall ledger_restore does not call a drop opened one")
        self.assertEqual(134, self._doc()["high"][CA._route_key(OWNER)]["sets"]["have"],
                         "the mark must still hold, so the watchdog still says the number is low")
        self._post(OWNER, 60, 280, 3000)
        eps = self._eps("sets")
        self.assertEqual([(big[0]["from"], big[0]["to"])], [(e["from"], e["to"]) for e in eps])

    def test_an_open_episode_outlives_the_rolling_cap(self):
        self._post(OWNER, 134, 280, 1000)
        self._post(OWNER, 0, 280, 2000)               # sets falls and STAYS down
        at = 3000
        for _ in range(45):                           # 45 separate uniques falls, each recovered
            self._post(OWNER, 0, 100, at)
            self._post(OWNER, 0, 280, at + 1)
            at += 10
        sets = self._eps("sets")
        self.assertEqual(1, len(sets), "the open sets episode was evicted by later closed ones")
        self.assertTrue(sets[0]["open"])
        closed = [e for e in self._doc()["drops"] if isinstance(e, dict) and not e.get("open")]
        self.assertEqual(40, len(closed), "the closed record is still a rolling 40")

    def test_another_world_cannot_close_his_episode(self):
        self._post(OWNER, 134, 280, 1000)
        self._post(OWNER, 0, 280, 2000)
        self._post(GUEST, 134, 280, 3000)
        self.assertTrue(self._eps("sets")[0]["open"],
                        "a guest world's number closed a drop in his world")

    def test_the_doctor_names_the_episode_as_his_last_fall(self):
        import console_doctor as CD
        orig = CD.HERE
        CD.HERE = self.d
        self.addCleanup(setattr, CD, "HERE", orig)
        self._post(OWNER, 134, 280, 1000)
        for i in range(5):
            self._post(OWNER, 0, 280, 2000 + i)
        st, why = CD._check_his_progress_number_has_not_been_overwritten()
        self.assertEqual(CD.MISSING, st, why)
        self.assertIn("sets 134 -> 0", why, "the doctor could not read the episode as a fall")


RED_PROOF = [
    {
        "why": "a lane sitting low re-files a drop on every tally — the 40-slot defect",
        "file": "control_app.py",
        "find": "        _before = {_ck[s]: was for s, was, _now in _seen if s not in _open_stores}\n",
        "replace": "        _before = {_ck[s]: was for s, was, _now in _seen}\n",
        "matches": 1,
    },
    {
        "why": "a recovery never reaches the episode, so it stays open forever",
        "file": "control_app.py",
        "find": "        _after = {_ck[s]: now for s, _was, now in _seen}\n",
        "replace": "        _after = {_ck[s]: now for s, _was, now in _seen if s not in _open_stores}\n",
        "matches": 1,
    },
    {
        "why": "the rolling cap evicts an OPEN episode, so a drop still in progress is forgotten",
        "file": "control_app.py",
        "find": ("    doc[\"drops\"] = [d for d in doc[\"drops\"]\n"
                 "                    if id(d) in _keep_ids or (isinstance(d, dict) and d.get(\"open\"))]\n"),
        "replace": "    doc[\"drops\"] = doc[\"drops\"][-40:]\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
