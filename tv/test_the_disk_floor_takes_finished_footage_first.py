#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REG-1678 - THE DISK FLOOR TAKES FOOTAGE THE RIVER HAS FINISHED BEFORE FOOTAGE IT STILL OWES A READ.

His chain, 2026-10-01: *"make sure it gets ledgered and extracted properly and then tombstoned and obviously then
deleted"*. The recorder's disk-floor reaper is the one deleter outside that chain: under MIN_FREE_GB, with the loose
pool empty, it takes a whole reel. REG-1361 taught it to spare cited pictures and to take a pinned reel last - and
it still chose by AGE alone, so the oldest reel went whether the river had read it or not. MEASURED on his Mac
(reel_reaps.jsonl): the 09-28 02:43 reaps took the two oldest of 20 reels with nothing on the row saying what the
river had them at - so nothing could say afterwards whether a read was lost.

Driven through the REAL _reel_reap_pick / _reap_record / reel_custody over temp shelves (never his):
  1. inside each pin tier, a reel at one of reel_router.READ_DONE goes before a reel still owed - or never stamped,
     which is not finished; oldest first within each; the pin tier stays outermost (REG-1361 holds);
  2. an owed reel still goes when nothing finished may (a full disk stops recording) and the answer says readOwed;
  3. a river that could not be asked keeps the old order and says readOwed None - UNKNOWN, never "finished";
  4. "finished" is the router's list, imported - a second copy would drift from the vocabulary owner;
  5. the reap row carries riverStation + readOwed; the loose-film eviction (no river asked) writes neither;
  6. the recorder's emergency branch asks the river when it picks;
  7. a reel reaped while a read was owed is a named custody contradiction the doctor says (MISSING), counted even
     though it is on neither the shelf nor the ledger; a row from before the field raises nothing.
RED_PROOF below.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

import tv_diablo as T  # noqa: E402
import reel_custody as RC  # noqa: E402
import reel_router as RR  # noqa: E402

# synthetic ids from the 2017 epoch: no recording can carry one, so no footage is ever pinned by these
A, B, C, D = ("reel_s_150000000000%d_%d" % (n, n) for n in (1, 2, 3, 4))


def _shelf(test, reels):
    hist = tempfile.mkdtemp(prefix="floor_river_")
    test.addCleanup(shutil.rmtree, hist, True)
    for r in reels:
        os.makedirs(os.path.join(hist, r))
        with open(os.path.join(hist, r, "f_1500000000000.jpg"), "wb") as fh:
            fh.write(b"\xff\xd8\xff\xd9")
    return hist


def _ev():
    return {"sessions": set(), "frames": set(), "reels": set(), "reads": set(), "readReels": set()}


class FinishedFootageGoesFirst(unittest.TestCase):

    def setUp(self):
        self.hist = _shelf(self, (A, B, C, D))

    def pick(self, cands, river, pinned=()):
        return T._reel_reap_pick(self.hist, list(cands), _ev(), set(pinned), river=river)

    def test_a_finished_reel_goes_before_an_older_owed_one(self):
        p = self.pick((A, B, C), {A: "STATION", B: "EMPTY", C: "PRINTER"})
        self.assertEqual((p["reel"], p["station"], p["readOwed"]), (B, "EMPTY", False),
                         "the floor took the oldest reel while the river still owed it a read and a finished one "
                         "could go: %r" % p)

    def test_every_READ_DONE_station_counts_as_finished(self):
        for st in RR.READ_DONE:
            p = self.pick((A, B), {A: "STATION", B: st})
            self.assertEqual(p["reel"], B, "a reel at %s was not treated as finished" % st)

    def test_a_reel_never_stamped_is_not_finished(self):
        p = self.pick((A, B), {B: "CAPTURE"})
        self.assertEqual((p["reel"], p["readOwed"]), (B, False),
                         "a reel the river never walked was taken as though it had nothing left to give")

    def test_an_owed_reel_still_goes_when_nothing_finished_may_and_says_so(self):
        p = self.pick((A, B), {A: "PRINTER", B: "STATION"})
        self.assertEqual((p["reel"], p["station"], p["readOwed"]), (A, "PRINTER", True),
                         "a full disk stops recording - the emergency must still take the oldest, and say a read "
                         "was owed: %r" % p)

    def test_the_pin_tier_stays_outermost(self):
        p = self.pick((A, B), {A: "STATION", B: "EMPTY"}, pinned=(B,))
        self.assertEqual((p["reel"], p["pinned"]), (A, False),
                         "a pinned finished reel went before an unpinned owed one - REG-1361's order was broken")
        p = self.pick((A, B, C), {A: "STATION", B: "EMPTY", C: "EMPTY"}, pinned=(A, B, C))
        self.assertEqual((p["reel"], p["pinned"], p["readOwed"]), (B, True, False),
                         "inside the pinned tier the finished reel did not go first: %r" % p)

    def test_a_river_that_could_not_be_asked_keeps_the_old_order_and_says_UNKNOWN(self):
        p = self.pick((A, B), None)
        self.assertEqual((p["reel"], p["station"], p["readOwed"]), (A, None, None),
                         "an unreadable stamp store was read as an answer: %r" % p)

    def test_finished_is_the_routers_list_not_a_copy(self):
        with mock.patch.object(RR, "READ_DONE", ("STATION",)):
            p = self.pick((A, B), {A: "EMPTY", B: "STATION"})
        self.assertEqual(p["reel"], B, "the reaper carries its own idea of a finished station - it did not follow "
                                       "reel_router.READ_DONE")


class TheReapRowSaysWhatTheRiverSaid(unittest.TestCase):

    def setUp(self):
        root = tempfile.mkdtemp(prefix="floor_row_")
        self.addCleanup(shutil.rmtree, root, True)
        hist = os.path.join(root, "tv", "frames", "hist")
        os.makedirs(hist)
        p = mock.patch.object(T, "HIST_DIR", hist)
        p.start()
        self.addCleanup(p.stop)
        self.log = T._reap_log_path()
        self.assertTrue(self.log.startswith(root), "PREMISE: the reap log is not under the temp shelf: %s" % self.log)

    def rows(self):
        with io.open(self.log, encoding="utf-8") as fh:
            return [json.loads(x) for x in fh if x.strip()]

    def test_a_reel_reap_records_the_station_and_whether_a_read_was_owed(self):
        T._reap_record(A, 3, True, 4, names=["f_1.jpg"], river={"station": "PRINTER", "readOwed": True})
        T._reap_record(B, 3, True, 4, names=["f_1.jpg"], river={"station": None, "readOwed": None})
        a, b = self.rows()
        self.assertEqual((a.get("riverStation"), a.get("readOwed")), ("PRINTER", True))
        self.assertIn("readOwed", b, "an unasked river was left off the row instead of said as null")
        self.assertIsNone(b["readOwed"])

    def test_a_loose_film_eviction_writes_no_river_fields(self):
        T._reap_record("loose", 2, True, -1, by="recorder-read-eviction", names=["f_1.jpg"])
        (r,) = self.rows()
        self.assertNotIn("readOwed", r, "a loose-film eviction claimed a river answer it never asked for")

    def test_the_emergency_branch_asks_the_river(self):
        import inspect
        src = inspect.getsource(T.archive_read_frame)
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        self.assertEqual(code.count("river=_river_positions())"), 1,
                         "the disk floor picks a reel without asking the river where it is")
        self.assertEqual(code.count("names=_pick[\"gone\"], river=_rv)"), 1, "a whole-reel reap drops the river")
        self.assertEqual(code.count("kept=_pick[\"kept\"], river=_rv)"), 1, "a partial reap drops the river")


class AReapBeforeExtractionIsAContradiction(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="floor_custody_")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.hist = os.path.join(self.tmp, "tv", "frames", "hist")
        os.makedirs(os.path.join(self.hist, A))
        self.stamp = os.path.join(self.tmp, "tv", "river_stamp.jsonl")
        self.w = RC.world(hist=self.hist, stamp_path=self.stamp)
        os.makedirs(os.path.dirname(self.w["reel_tombstones"]), exist_ok=True)
        with io.open(self.w["reel_tombstones"], "w", encoding="utf-8") as fh:
            json.dump({"reels": [], "updatedTs": 1}, fh)

    def reap(self, reel, **extra):
        row = {"ts": 1700000003004, "reel": reel, "frames": 9, "removed": True, "shelfBefore": 5,
               "by": "recorder-disk-floor"}
        row.update(extra)
        with io.open(self.w["reel_reaps"], "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")

    def census(self):
        src = RC.sources(hist=self.hist, stamp_path=self.stamp)
        return src, RC.census(src=src, limit=50)

    def test_a_reel_reaped_while_owed_is_counted_and_named(self):
        self.reap(B, riverStation="STATION", readOwed=True)
        src, c = self.census()
        self.assertIn(B, [r["reel"] for r in c["rows"]],
                      "a reel the floor took before its read is on neither shelf nor ledger, and the census never "
                      "looked at it")
        self.assertEqual(c["byKind"].get("reaped-before-extracted"), 1, c["byKind"])
        st, why = RC.doctor(src=src)
        self.assertEqual(st, RC.MISSING, why)
        self.assertIn("reaped-before-extracted", why)
        rec = RC.custody(B, src=src)
        k = next(x for x in rec["contradictions"] if x["kind"] == "reaped-before-extracted")
        self.assertIn("STATION", k["right"]["says"], "the contradiction does not say where the river had it")

    def test_a_finished_reap_and_a_row_from_before_the_field_raise_nothing(self):
        self.reap(B, riverStation="EMPTY", readOwed=False)
        self.reap(C)
        self.reap(D, riverStation=None, readOwed=None)
        src, c = self.census()
        names = [r["reel"] for r in c["rows"]]
        self.assertNotIn("reaped-before-extracted", c["byKind"], c["byKind"])
        for r in (B, C, D):
            self.assertNotIn(r, names, "%s joined the census though nothing says a read was lost" % r)


RED_PROOF = [
    {"why": "REG-1678 - the floor ranks by age alone again: it takes the oldest reel while a finished one could go",
     "file": "tv_diablo.py",
     "find": "        return (c in pinned, (river.get(c) not in done) if asked else False)\n",
     "replace": "        return (c in pinned, False)\n",
     "matches": 1},
    {"why": "REG-1678 - 'finished' becomes the reaper's own copy instead of the router's list",
     "file": "tv_diablo.py",
     "find": "            done = frozenset(_rtr.READ_DONE)\n",
     "replace": "            done = frozenset((\"EMPTY\", \"CAPTURE\", \"ROUTED\", \"TOMBSTONE\"))\n",
     "matches": 1},
    {"why": "REG-1678 - an unreadable river is read as an answer (every reel 'finished')",
     "file": "tv_diablo.py",
     "find": "    asked = river is not None and done is not None\n",
     "replace": "    asked = True\n    river = river or {}\n    done = done or frozenset()\n",
     "matches": 1},
    {"why": "REG-1678 - the reap row forgets what the river said",
     "file": "tv_diablo.py",
     "find": "            row[\"readOwed\"] = river.get(\"readOwed\")\n",
     "replace": "            pass\n",
     "matches": 1},
    {"why": "REG-1678 - the emergency branch picks without asking the river",
     "file": "tv_diablo.py",
     "find": "                                                    river=_river_positions())\n",
     "replace": "                                                    river=None)\n",
     "matches": 1},
    {"why": "REG-1678 - a reap before extraction is not a custody contradiction",
     "file": "reel_custody.py",
     "find": "    if r.get(\"reapedReadOwed\") is True:\n",
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "REG-1678 - the census never looks at a reel reaped while owed (on neither shelf nor ledger)",
     "file": "reel_custody.py",
     "find": "    names = sorted(set(shelf or ()) | set((tombs or {}).keys()) | reaped_owed)\n",
     "replace": "    names = sorted(set(shelf or ()) | set((tombs or {}).keys()))\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
