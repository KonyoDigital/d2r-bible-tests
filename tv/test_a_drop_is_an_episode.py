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

2026-09-28 (Ledger fix, findings 2 and 2b):
  · an OPEN episode kept its lane out of "before" entirely, so a later, bigger fall — even to 0 —
    was never recorded. Its "before" is now the lowest `to` among its open episodes.
  · the P0 build had switched the board to ledger_restore's drop line (to 0 or >= max(10, 25%)),
    so a 3-set fall or one un-tick stopped writing any row. His decision: keep what was recorded
    before. drops_between takes a threshold whose default IS ledger_restore's line; the board
    passes ANY_FALL. The doctor never prints "? None -> None" for a fall nobody recorded.

2026-09-28 (Ledger fix round 2, finding C): HIS RULE, "EVERY fall is recorded, as before". Round 1
measured from the lowest open `to`, so a fall after a partial recovery that stayed above the open
low (134 -> 60, up to 90, down to 70) was never written, and a law here pinned it. A fall is now
measured from the lane's PREVIOUS reading: each fall is its own episode, sitting still files
nothing, a fall to 0 is always a fall. ledger_restore's own line is untouched.

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

    def test_ledger_restores_own_drop_line_is_unchanged_by_the_threshold(self):
        # PIN THE LAW, NOT THE NUMBER: the default is ledger_restore's line, exactly as it was.
        def blob(n):
            return {"ledger": {}, "counts": {"setPieces": n}}
        # baseline first: both counts are READ (not UNKNOWN), or `small == []` would be vacuous
        self.assertEqual(134, LR.store_count(blob(134), "setPieces"))
        self.assertEqual([], LR.drops_between(blob(134), blob(130)),
                         "the backup watcher's own line moved: a 4-row fall of 134 is not its drop")
        self.assertEqual([], LR.drops_between(blob(134), blob(130), None))
        self.assertEqual(1, len(LR.drops_between(blob(134), blob(60))))
        self.assertEqual(1, len(LR.drops_between(blob(30), blob(0))), "a fall to 0 is always a drop")
        self.assertEqual([{"store": "setPieces", "from": 134, "to": 133}],
                         LR.drops_between(blob(134), blob(133), LR.ANY_FALL))
        self.assertEqual([], LR.drops_between(blob(134), blob(134), LR.ANY_FALL))
        for bad in (0, -1, True, 1.5, "1"):
            with self.assertRaises(ValueError, msg="threshold %r was accepted" % (bad,)):
                LR.drops_between(blob(134), blob(130), bad)

    def test_every_fall_on_the_board_is_recorded_as_before(self):
        # his decision (2b): keep what was recorded before — a 3-set fall and one un-tick are rows
        self._post(OWNER, 134, 280, 1000)
        self._post(OWNER, 131, 280, 2000)
        eps = self._eps("sets")
        self.assertEqual([(134, 131, True)], [(e["from"], e["to"], e["open"]) for e in eps],
                         "a 3-set fall below the mark was not recorded at all")
        self.assertEqual(134, self._doc()["high"][CA._route_key(OWNER)]["sets"]["have"],
                         "the mark must still hold, so the watchdog still says the number is low")
        self._post(OWNER, 131, 279, 3000)
        uni = self._eps("uniques")
        self.assertEqual([(280, 279)], [(e["from"], e["to"]) for e in uni],
                         "a single un-tick wrote no drop row")

    def test_a_fall_a_partial_recovery_and_a_fall_to_zero_are_two_episodes(self):
        self._post(OWNER, 134, 280, 1000)
        self._post(OWNER, 60, 280, 2000)          # falls: episode 1 opens (134 -> 60)
        self._post(OWNER, 100, 280, 3000)         # comes part of the way back: still below 134
        self._post(OWNER, 0, 280, 4000)           # falls again, to zero — from its last reading
        eps = self._eps("sets")
        self.assertEqual(2, len(eps), "the fall to zero behind an open episode was never recorded: %r"
                         % [(e["from"], e["to"]) for e in eps])
        self.assertEqual([(134, 60, True, 2000), (100, 0, True, 4000)],
                         [(e["from"], e["to"], e["open"], e["at"]) for e in eps])

    def test_sitting_at_the_same_value_files_nothing(self):
        self._post(OWNER, 134, 280, 1000)
        self._post(OWNER, 60, 280, 2000)
        for i in range(20):
            self._post(OWNER, 60, 280, 3000 + i)
        self.assertEqual(1, len(self._eps("sets")), "sitting at the same value re-filed the fall")
        self._post(OWNER, 90, 280, 4000)
        for i in range(20):
            self._post(OWNER, 90, 280, 4001 + i)  # a partial recovery, held: still nothing new
        self.assertEqual(1, len(self._eps("sets")), "sitting after a partial recovery filed a fall")

    def test_a_fall_after_a_partial_recovery_is_recorded(self):
        # 2026-09-28 (Ledger fix round 2, finding C). HIS RULE: "EVERY fall is recorded, as before".
        # Round 1 measured from the LOWEST open `to`, so 90 -> 70 — a real fall, above the open low
        # of 60 — was never written, and a law pinned that. Each fall is measured from the lane's
        # PREVIOUS reading instead.
        self._post(OWNER, 134, 280, 1000)
        self._post(OWNER, 60, 280, 2000)          # falls (134 -> 60)
        self._post(OWNER, 90, 280, 3000)          # partial recovery, still below 134
        self._post(OWNER, 70, 280, 4000)          # falls again — ABOVE the open low of 60
        self._post(OWNER, 70, 280, 4500)          # sits: nothing
        self._post(OWNER, 80, 280, 5000)
        self._post(OWNER, 75, 280, 6000)          # and again
        eps = self._eps("sets")
        self.assertEqual([(134, 60, 2000), (90, 70, 4000), (80, 75, 6000)],
                         [(e["from"], e["to"], e["at"]) for e in eps],
                         "a fall after a partial recovery was not recorded: %r"
                         % [(e["from"], e["to"]) for e in eps])
        self.assertEqual([True, True, True], [e["open"] for e in eps])
        self.assertEqual(134, self._doc()["high"][CA._route_key(OWNER)]["sets"]["have"],
                         "the mark must still hold while the lane is below it")
        self._post(OWNER, 90, 280, 7000)          # back to 90: closes the two falls that started <= 90
        self.assertEqual([True, False, False], [e["open"] for e in self._eps("sets")])
        self._post(OWNER, 134, 280, 8000)         # back to the mark: every episode is closed
        self.assertEqual([False, False, False], [e["open"] for e in self._eps("sets")])

    def test_a_fall_to_zero_is_always_recorded(self):
        self._post(OWNER, 3, 280, 1000)
        self._post(OWNER, 0, 280, 2000)
        self.assertEqual([(3, 0)], [(e["from"], e["to"]) for e in self._eps("sets")])
        self._post(OWNER, 1, 280, 3000)
        self._post(OWNER, 0, 280, 4000)           # from 1, below every earlier low but equal to it
        self.assertEqual([(3, 0), (1, 0)], [(e["from"], e["to"]) for e in self._eps("sets")],
                         "a second fall to 0 after a one-set recovery was not recorded")

    def test_the_doctor_says_plainly_when_no_episode_is_recorded(self):
        import console_doctor as CD
        orig = CD.HERE
        CD.HERE = self.d
        self.addCleanup(setattr, CD, "HERE", orig)
        rk = CA._route_key(OWNER)
        doc = {"v": 2, "ownerId": OWNER["id"],
               "byRoute": {rk: {"who": OWNER, "route": OWNER, "at": 1000,
                                "sets": {"have": 100, "total": 135}}},
               "sets": {"have": 100, "total": 135},
               "high": {rk: {"sets": {"have": 134, "total": 135, "at": 500}}},
               "drops": []}
        with open(os.path.join(self.d, "board_tally.json"), "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        st, why = CD._check_his_progress_number_has_not_been_overwritten()
        self.assertEqual(CD.MISSING, st, why)
        self.assertIn("sets 100 (best 134)", why, "baseline: the doctor saw the lane below its mark")
        self.assertNotIn("None -> None", why, "an unrecorded fall was printed as a reading: %s" % why)
        self.assertNotIn("? ", why)
        self.assertIn("No drop episode is recorded", why)

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
        "find": "        _before = {_ck[s]: was for s, was, _now in _seen}     # the last reading\n",
        "replace": "        _before = {_ck[s]: hi[_lane_of[s][0]][\"have\"] for s, was, _now in _seen}\n",
        "matches": 1,
    },
    {
        "why": "a recovery never reaches the episode, so it stays open forever",
        "file": "control_app.py",
        "find": "        _after = {_ck[s]: now for s, _was, now in _seen}\n",
        "replace": "        _after = {_ck[s]: min(now, _was) for s, _was, now in _seen}\n",
        "matches": 1,
    },
    {
        "why": "a fall is measured from the lowest open low again, so a fall after a partial recovery is never recorded (finding C)",
        "file": "control_app.py",
        "find": "        _was = _lp.get(\"have\")\n",
        "replace": ("        _was = min([prev[\"have\"]] + [d.get(\"to\") for d in doc[\"drops\"] if isinstance(d, dict)"
                    " and d.get(\"open\") and d.get(\"routeKey\") == key and d.get(\"store\") == store])\n"),
        "matches": 1,
    },
    {
        "why": "the last reading is overwritten before it is read, so every fall is measured from the tally itself and none is recorded (finding C)",
        "file": "control_app.py",
        "find": "    _last = doc[\"byRoute\"].get(key) if isinstance(doc[\"byRoute\"].get(key), dict) else {}\n    doc[\"byRoute\"][key] = ",
        "replace": "    doc[\"byRoute\"][key] = _last = ",
        "matches": 1,
    },
    {
        "why": "the board uses ledger_restore's drop line again, so a 3-set fall or an un-tick writes nothing (finding 2b)",
        "file": "control_app.py",
        "find": "            route_key=key, at_ms=t.get(\"at\"), threshold=_lr.ANY_FALL)\n",
        "replace": "            route_key=key, at_ms=t.get(\"at\"))\n",
        "matches": 1,
    },
    {
        "why": "the threshold's default stops being ledger_restore's own line, so the backup watcher drifts",
        "file": "ledger_restore.py",
        "find": "        if b == 0 or (a - b) >= max(DROP_MIN, DROP_FRAC * a):\n",
        "replace": "        if b < a:\n",
        "matches": 1,
    },
    {
        "why": "the doctor prints '? None -> None' for a fall nobody recorded",
        "file": "console_doctor.py",
        "find": ("            _last = (\"No drop episode is recorded for his world, so when and how far it fell is \"\n"
                 "                     \"UNKNOWN.\")\n"),
        "replace": ("            _last = \"The last recorded fall was %s %s -> %s.\" % (\n"
                    "                recent.get(\"lane\") or \"?\", _from, _to)\n"),
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
