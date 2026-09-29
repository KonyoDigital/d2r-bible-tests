# -*- coding: utf-8 -*-
"""#41 rank 19 (REG-1533, 2026-09-29) — THE EVIDENCE TIERS ARE A LANE: on · worked · lastTs · owed.

The heart audit (verified list, rank 19): "No lane reports on, worked, lastTs or owed for the tiers.
15 WATCHED items waiting for looks are published nowhere, and the only reader is a row stuck MISSING."
A grep of lane_census for vault_evidence / tier / retro found nothing; WATCHES['evidence tiers'] is ().

WHAT THIS LAW DRIVES, over a witness ledger in a temp dir (never his vault_accum.json):
  · vault_evidence.tiers_watch answers in the shared vocabulary: `owed` is the WATCHED count with a row
    per item saying its gap to the bar (looks short of the 10-look floor, or the Wilson bound under the
    bar once the floor is met); `worked` is LIFETIME — items that EARNED PROVEN/HARDENED by visits;
    `lastTs` is the newest LOOK's own time.
  · UNKNOWN IS NEVER 0: an unreadable ledger leaves every field None; a row that cannot be measured
    makes `owed` None and says what WAS counted (owedAtLeast); no look carrying a time leaves lastTs None.
  · A READ, EMPTY LEDGER MAY SAY 0 — that is a measurement.
  · THE EAGLE LINE: the 'evidence tiers' doctor row carries the owed clause with the item names and the
    age of the newest look — measured from the look, so a fixture look 30 h old reads ~30 h, never
    "just now" — and says UNKNOWN when no look carries a time.
  · THE CONSOLE PUBLISHES IT: control_app.evidence_tiers_state() quotes the same dict on the status
    surface, cached by the ledger's mtime — a rewritten ledger is re-read, an unchanged one is not,
    and an unreadable one is never remembered as an answer.
  · NOTHING WRITES THE LEDGER: its bytes are identical after every read.
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

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable; enable()

import console_doctor as CD
import vault_evidence as VE

H = 3600000


def _looks(frame, n, ts=None):
    """n looks, each its own visit (session), each carrying its own time when ts is given."""
    out = []
    for i in range(n):
        look = {"session": "s%02d" % i, "frame": frame, "conf": 0.91, "lane": "stash"}
        if ts is not None:
            look["ts"] = ts + i * 60000
        out.append(look)
    return out


class TheEvidenceTiersLaneSaysWhatItOwes(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="tiers-lane-")
        self.ledger = os.path.join(self.tmp, "witness.json")
        self.shelf = os.path.join(self.tmp, "shelf")
        os.makedirs(self.shelf)
        for name in ("a.jpg", "b.jpg", "c.jpg", "d.jpg"):     # every cited picture is on the fixture shelf
            with io.open(os.path.join(self.shelf, name), "w", encoding="utf-8") as fh:
                fh.write(name)
        self.now = int(time.time() * 1000)
        self.newest = self.now - 30 * H          # the newest look is 30 h old
        self.doc = {"owned": [
            # PROVEN by 12 visits — lifetime work
            {"name": "Shako", "lane": "stash", "kind": "item", "witnesses": _looks("a.jpg", 12, self.newest - 9 * H)},
            # WATCHED: 2 looks, 8 short of the floor — its LAST look is the newest in the ledger
            {"name": "War Traveler", "lane": "stash", "kind": "item", "witnesses": _looks("b.jpg", 2, self.newest - 60000)},
            # WATCHED: at the floor with misses — the bound sits under the bar
            {"name": "Arachnid Mesh", "lane": "stash", "kind": "item", "misses": 4,
             "witnesses": _looks("c.jpg", 6, self.newest - 50 * H)},
            # HARDENED by 21 visits
            {"name": "Griffon's Eye", "lane": "stash", "kind": "item", "witnesses": _looks("d.jpg", 21, self.newest - 80 * H)},
        ]}
        self._write(self.doc)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, doc):
        self.before = json.dumps(doc).encode("utf-8")
        with io.open(self.ledger, "wb") as fh:
            fh.write(self.before)

    def _unchanged(self):
        with io.open(self.ledger, "rb") as fh:
            self.assertEqual(self.before, fh.read(), "something WROTE the witness ledger")

    # ── the lane ──────────────────────────────────────────────────────────────────────────────────
    def test_owed_is_the_watched_count_with_each_gap_to_the_bar(self):
        lane = VE.tiers_watch(self.ledger)
        self.assertTrue(lane["on"], lane)
        self.assertEqual(2, lane["owed"], lane["say"])
        self.assertEqual(2, lane["owedAtLeast"])
        self.assertEqual(0, lane["unknownRows"])
        by = {w["name"]: w for w in lane["waiting"]}
        self.assertEqual(["War Traveler", "Arachnid Mesh"], [w["name"] for w in lane["waiting"]])
        wt = by["War Traveler"]
        self.assertEqual((2, 2, 8), (wt["successes"], wt["trials"], wt["needLooks"]))
        self.assertIsNone(wt["barGap"], "a row short of the floor has no bar gap yet")
        self.assertIn("8 more to the 10-look floor", wt["why"])
        am = by["Arachnid Mesh"]
        self.assertEqual((6, 10, 0), (am["successes"], am["trials"], am["needLooks"]))
        self.assertIsNotNone(am["barGap"])
        self.assertGreater(am["barGap"], 0.0, "6 of 10 is under the 0.722 bar")
        self.assertIn("under the 0.722 bar", am["why"])
        self.assertIn("owed 2 WATCHED waiting for looks (War Traveler 2/2 looks, 8 more", lane["say"])
        self._unchanged()

    def test_worked_is_lifetime_items_that_earned_their_tier(self):
        lane = VE.tiers_watch(self.ledger)
        self.assertEqual(2, lane["worked"], "Shako (PROVEN) and Griffon's Eye (HARDENED) earned it by visits")

    def test_last_ts_is_the_newest_look_never_the_clock_or_the_file(self):
        lane = VE.tiers_watch(self.ledger)
        self.assertEqual(self.newest, lane["lastTs"], "lastTs is not the newest look's own time")
        self.assertLess(lane["lastTs"], self.now - 29 * H, "lastTs reads as the moment it was asked")
        # the ledger rewritten with the SAME looks: a compaction is not a look
        os.utime(self.ledger, None)
        self.assertEqual(self.newest, VE.tiers_watch(self.ledger)["lastTs"])

    def test_no_look_carrying_a_time_leaves_last_ts_unknown(self):
        self._write({"owned": [{"name": "Shako", "lane": "stash", "kind": "item", "witnesses": _looks("a.jpg", 12)}]})
        lane = VE.tiers_watch(self.ledger)
        self.assertTrue(lane["on"])
        self.assertIsNone(lane["lastTs"])
        self.assertIn("last look UNKNOWN", lane["say"])

    def test_an_owned_rows_last_seen_ts_counts_when_its_looks_carry_none(self):
        self._write({"owned": [{"name": "Shako", "lane": "stash", "kind": "item", "lastSeenTs": self.newest,
                                "witnesses": _looks("a.jpg", 12)}]})
        self.assertEqual(self.newest, VE.tiers_watch(self.ledger)["lastTs"])

    def test_an_unreadable_ledger_is_unknown_on_every_field_never_zero(self):
        with io.open(self.ledger, "wb") as fh:
            fh.write(b"{not json")
        lane = VE.tiers_watch(self.ledger)
        for k in ("on", "worked", "lastTs", "owed", "owedAtLeast", "unknownRows", "waiting"):
            self.assertIsNone(lane[k], "%s read %r on an unreadable ledger" % (k, lane[k]))
        lane = VE.tiers_watch(os.path.join(self.tmp, "absent.json"))
        self.assertIsNone(lane["owed"])
        self.assertIsNone(lane["worked"])

    def test_a_row_that_cannot_be_measured_makes_owed_unknown_and_says_what_was_counted(self):
        doc = json.loads(self.before.decode("utf-8"))
        doc["owned"].append({"name": "Unread Thing", "lane": "stash", "witnesses": 4})
        self._write(doc)
        lane = VE.tiers_watch(self.ledger)
        self.assertTrue(lane["on"])
        self.assertIsNone(lane["owed"], "one unreadable row and owed still claims a number")
        self.assertEqual(2, lane["owedAtLeast"])
        self.assertEqual(1, lane["unknownRows"])
        self.assertIn("owed UNKNOWN", lane["say"])
        self.assertIn("at least 2 WATCHED", lane["say"])
        self.assertEqual(2, lane["worked"])

    def test_a_read_empty_ledger_may_say_zero(self):
        self._write({"owned": []})
        lane = VE.tiers_watch(self.ledger)
        self.assertTrue(lane["on"])
        self.assertEqual(0, lane["owed"])
        self.assertEqual(0, lane["worked"])
        self.assertEqual([], lane["waiting"])
        self.assertIn("owed 0", lane["say"])

    # ── the eagle line ────────────────────────────────────────────────────────────────────────────
    def test_the_doctor_row_carries_owed_and_the_age_of_the_newest_look(self):
        st, why = CD._check_the_evidence_tiers(path=self.ledger, root=self.shelf)
        self.assertEqual(CD.OK, st, why)
        self.assertIn("tiers by visit, never frame: WATCHED 2 · PROVEN 1 · HARDENED 1", why)
        self.assertIn("owed 2 WATCHED waiting for looks (War Traveler 2/2 looks, 8 more to the 10-look floor; "
                      "Arachnid Mesh 6/10 looks, bound", why)
        i = why.index("last look ")
        age = float(why[i + len("last look "):].split("h ago")[0])
        self.assertTrue(29.9 <= age <= 30.5, "the age is not the newest look's: %r" % why[i:i + 40])
        self._unchanged()

    def test_the_doctor_row_says_unknown_when_no_look_carries_a_time(self):
        self._write({"owned": [{"name": "Shako", "lane": "stash", "kind": "item", "witnesses": _looks("a.jpg", 12)}]})
        st, why = CD._check_the_evidence_tiers(path=self.ledger, root=self.shelf)
        self.assertEqual(CD.OK, st, why)
        self.assertIn("owed 0", why)
        self.assertIn("last look UNKNOWN (no look carries a time)", why)

    def test_the_clause_reads_the_lane_and_never_invents_an_age(self):
        self.assertIn("last look UNKNOWN", CD._tiers_lane_clause({"on": True, "owed": 1, "lastTs": None,
                                                                  "say": "owed 1 WATCHED waiting for looks (x) · last look UNKNOWN (no look carries a time)"}))
        self.assertIn("last look UNKNOWN", CD._tiers_lane_clause({"on": True, "lastTs": True, "say": "owed 0"}),
                      "a bool is not a time")
        self.assertIn("owed UNKNOWN", CD._tiers_lane_clause({"on": None, "say": "unread"}))
        self.assertIn("owed UNKNOWN", CD._tiers_lane_clause(None))

    # ── the console publishes it ──────────────────────────────────────────────────────────────────
    def test_the_console_state_quotes_the_lane_and_re_reads_only_a_changed_ledger(self):
        import control_app as CA
        saved = CA.VAULT_LEDGER_PATH
        real = VE.tiers_watch
        calls = []

        def counting(path):
            calls.append(path)
            return real(path)
        CA.VAULT_LEDGER_PATH = self.ledger
        CA._EVIDENCE_TIERS_CACHE.update({"key": None, "lane": None})
        VE.tiers_watch = counting
        try:
            a = CA.evidence_tiers_state()
            self.assertEqual(2, a["owed"])
            self.assertEqual(2, a["worked"])
            self.assertEqual(self.newest, a["lastTs"])
            for k in ("on", "worked", "lastTs", "owed", "say"):
                self.assertIn(k, a)
            b = CA.evidence_tiers_state()
            self.assertEqual(1, len(calls), "an unchanged ledger was walked again")
            self.assertEqual(a, b)
            b["owed"] = 99
            self.assertEqual(2, CA.evidence_tiers_state()["owed"], "the cached dict was handed out by reference")
            # the ledger changes: re-read
            doc = json.loads(self.before.decode("utf-8"))
            doc["owned"] = doc["owned"][:1]
            self._write(doc)
            os.utime(self.ledger, (time.time() + 5, time.time() + 5))
            c = CA.evidence_tiers_state()
            self.assertEqual(2, len(calls), "a changed ledger was not re-read")
            self.assertEqual(0, c["owed"])
            # an unreadable ledger is UNKNOWN and never remembered as an answer
            with io.open(self.ledger, "wb") as fh:
                fh.write(b"{")
            os.utime(self.ledger, (time.time() + 9, time.time() + 9))
            d = CA.evidence_tiers_state()
            self.assertIsNone(d["owed"])
            self.assertIsNone(d["on"])
            CA.evidence_tiers_state()
            self.assertEqual(4, len(calls), "an unreadable ledger was cached as an answer")
            # the status surface carries it under its own key
            self.assertIn('"evidenceTiers": _t("evidenceTiers", evidence_tiers_state)',
                          io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read(),
                          "status_payload does not publish the lane")
        finally:
            VE.tiers_watch = real
            CA.VAULT_LEDGER_PATH = saved
            CA._EVIDENCE_TIERS_CACHE.update({"key": None, "lane": None})


RED_PROOF = [
    {
        "why": "#41 rank 19 - a row that cannot be measured no longer makes owed UNKNOWN: the count is claimed anyway",
        "file": "vault_evidence.py",
        "find": "    owed = len(waiting) if unknown == 0 else None\n",
        "replace": "    owed = len(waiting)\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 19 - lastTs becomes the moment it was asked, not the newest look (stale-reading)",
        "file": "vault_evidence.py",
        "find": "    last = _newest_look_ts(doc[\"owned\"])\n",
        "replace": "    import time as _t; last = int(_t.time() * 1000)\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 19 - the WATCHED rows are counted but the tier that EARNED its place no longer counts as work",
        "file": "vault_evidence.py",
        "find": "        if got[\"tier\"] in (PROVEN, HARDENED):\n            worked += 1\n            continue\n",
        "replace": "        if got[\"tier\"] in (PROVEN, HARDENED):\n            continue\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 19 - the eagle line drops the owed clause: the counts are published, what they owe is not",
        "file": "console_doctor.py",
        "find": "    line += \" · \" + _tiers_lane_clause(_ve.tiers_watch(path if path is not None else _evidence_ledger_path()))\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#41 rank 19 - the console remembers the first answer for ever: a changed ledger is never re-read",
        "file": "control_app.py",
        "find": "        if key is None or _EVIDENCE_TIERS_CACHE[\"key\"] != key:\n",
        "replace": "        if _EVIDENCE_TIERS_CACHE[\"lane\"] is None:\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
