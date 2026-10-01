# -*- coding: utf-8 -*-
"""#234 step 1 — A CHARACTER LEARNED LATE STILL GETS ITS GEAR.

His ask, 2026-10-01: the in-game characters fill themselves - "i want to see the items slowly appearing based on the
character they were witnessed in". MEASURED on his Mac that evening, before any build: the character-select learner knew
12 characters (class and level from the pixels) and had 0 LOGINS, so the gear ledger held 0 characters and filed all 19
worn reads (Harlequin Crest, Grief, Call to Arms...) UNATTRIBUTED. Two halves, each built right, never joined again:
  · the learner's 5 visits were filed before v3530 began keeping a visit's last frame and its highlighted row, so the one
    closing read that names the character he entered with was never owed - and the scan cursor was long past them;
  · the gear ledger never looks at an ingested reel again, so a login that arrives later changes nothing.
[[the-unjoined-end]]

This law drives both joints over fixture reels, a stub reader and temp stores (his roster and his gear ledger are never
touched):
  1. an old visit (no last frame, no highlighted row) is given its LAST character-select frame and one closing read; the
     login it names appears; a visit whose reel is gone is closed with that reason; one that already named its row is not
     read again; the hourly cap still decides when;
  2. a reel filed with no character is filed again once a login names one - the unattributed counts come back down by
     exactly what it carried, and a reel already filed under someone is never filed twice.
RED_PROOF below.
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import char_select as CS  # noqa: E402
import equipped_ledger as E  # noqa: E402
from test_a_session_is_bound_to_the_character_he_entered_with import _Reels, T0  # noqa: E402
from test_equipped_items_are_pixel_exact_per_character import _World, _row, _seal, _worn  # noqa: E402


class AnOldVisitGetsItsClosingRead(_Reels):

    def _old_visit(self, reel, frames):
        """A visit filed the way it was before v3530: read, but with no last frame and no highlighted row kept."""
        self.reel(reel, frames)
        r = self.tick(lambda ts: None, T0 + 400000)
        self.assertTrue(r["ok"], r)
        d = CS.load()
        vids = [k for k in d["visits"] if k.startswith(reel + "#")]
        self.assertEqual(len(vids), 1, "PREMISE: the fixture did not make one visit: %r" % sorted(d["visits"]))
        v = d["visits"][vids[0]]
        for k in ("lastFrame", "sel", "closed", "closeOwed"):
            v.pop(k, None)
        CS.save(d)
        self.assertEqual(CS.logins(CS.load()), [], "PREMISE: the old visit already names a login")
        del self.reads[:]
        return vids[0]

    def test_the_old_visit_is_read_at_its_last_frame_and_names_the_login(self):
        self._old_visit("reel_s_7", [(T0 + i * 1000, True) for i in range(2)] + [(T0 + 200000, False)])
        r = self.tick(lambda ts: "Frostnova", T0 + 500000)
        self.assertEqual(self.reads, [T0 + 1000], "the old visit's LAST character-select frame was not the one read")
        self.assertEqual(r.get("closed"), 1, r)
        L = CS.logins(CS.load())
        self.assertEqual([(x["character"], x["sessionId"]) for x in L], [("Frostnova", "s_7")],
                         "a visit filed before v3530 still names no login")

    def test_a_visit_whose_reel_is_gone_is_closed_with_that_reason(self):
        vid = self._old_visit("reel_s_8", [(T0 + i * 1000, True) for i in range(2)] + [(T0 + 200000, False)])
        import shutil
        shutil.rmtree(os.path.join(self.hist, "reel_s_8"))
        self.tick(lambda ts: "Frostnova", T0 + 500000)
        v = CS.load()["visits"][vid]
        self.assertIn("gone", str(v.get("closed")), "a visit with no reel left was not closed with its reason: %r" % v)
        self.assertEqual(self.reads, [])

    def test_a_visit_that_named_its_row_is_not_read_again(self):
        vid = self._old_visit("reel_s_9", [(T0 + i * 1000, True) for i in range(2)] + [(T0 + 200000, False)])
        d = CS.load()
        d["visits"][vid]["sel"] = [{"ts": T0, "name": "Hammerdin", "reader": "vision"}]
        CS.save(d)
        self.tick(lambda ts: "Frostnova", T0 + 500000)
        self.assertEqual(self.reads, [], "a visit that already named its row was read again")

    def test_the_hourly_cap_still_decides_when(self):
        self._old_visit("reel_s_10", [(T0 + i * 1000, True) for i in range(2)] + [(T0 + 200000, False)])
        d = CS.load()
        d["stats"]["readTs"] = [(T0 + 499000) / 1000.0] * CS.READS_PER_HOUR
        CS.save(d)
        self.tick(lambda ts: "Frostnova", T0 + 500000)
        self.assertEqual(self.reads, [], "the back-filled close read past the hourly cap")
        self.assertEqual(CS.logins(CS.load()), [])


class AReelFiledWithNoCharacterIsFiledAgain(_World):

    LOGIN = {"reel": "reel_s_A", "sessionId": "s_A", "ts": T0 + 5000, "character": "Hammerdin",
             "visit": "reel_s_A#%d" % (T0 + 5000), "reader": "vision"}

    def rows(self):
        return [_row("s_A", T0 + 1000), _worn("s_A", T0 + 10000, "reel_s_A/f_1", "Shako"),
                _worn("s_A", T0 + 60000, "reel_s_A/f_2", "Enigma"), _seal("s_A", T0 + 3600000),
                _row("s_C", T0 + 9000000), _worn("s_C", T0 + 9010000, "reel_s_C/f_9", "Wizardspike"),
                _seal("s_C", T0 + 9600000)]

    def test_a_login_that_arrives_later_files_the_reel_under_its_character(self):
        r1, d1 = self.ingest(self.rows(), now_ms=T0 + 9700000, logins=[], cs=None)
        self.assertEqual(sorted(r1["ingested"]), ["s_A", "s_C"])
        self.assertEqual(d1["characters"], {}, "PREMISE: with no login the reel was filed under someone")
        self.assertEqual(d1["unattributed"]["reads"], 3)
        r2, d2 = self.ingest(self.rows(), now_ms=T0 + 9800000, logins=[self.LOGIN], cs=None)
        self.assertEqual(r2.get("refiled"), ["s_A"], "an ingested reel was never looked at again: %r" % r2)
        ham = json.dumps(d2["characters"].get("Hammerdin"))
        self.assertIn("Shako", ham)
        self.assertIn("Enigma", ham)
        u = d2["unattributed"]
        self.assertEqual(u["reads"], 1, "the unattributed count did not come back down by what the reel carried: %r" % u)
        self.assertEqual(sorted(u["names"]), ["Wizardspike"])
        self.assertEqual(u["reels"], ["s_C"])

    def test_a_reel_is_never_filed_twice(self):
        self.ingest(self.rows(), now_ms=T0 + 9700000, logins=[], cs=None)
        self.ingest(self.rows(), now_ms=T0 + 9800000, logins=[self.LOGIN], cs=None)
        r3, d3 = self.ingest(self.rows(), now_ms=T0 + 9900000, logins=[self.LOGIN], cs=None)
        self.assertEqual(r3.get("refiled"), [], "a reel already filed under its character was filed again")
        slot_sightings = [s.get("sightings") for s in (d3["characters"]["Hammerdin"].get("slots") or {}).values()]
        unplaced = [s.get("sightings") for s in (d3["characters"]["Hammerdin"].get("unplaced") or {}).values()]
        self.assertTrue(all(n == 1 for n in slot_sightings + unplaced), "a sighting was counted twice: %r"
                        % d3["characters"]["Hammerdin"])

    def test_a_reel_already_filed_under_its_character_is_not_filed_again(self):
        """A MIXED reel: gear worn before the login stays unattributed, gear after it is the character's - so the reel is
        on the unattributed list AND under a character. It was filed whole the first time; filing it again on every
        ingest is work that never ends and a receipt that lies (heart2 found the first cut of this law BLIND here)."""
        login = dict(self.LOGIN, ts=T0 + 30000, visit="reel_s_A#%d" % (T0 + 30000))
        r1, d1 = self.ingest(self.rows(), now_ms=T0 + 9700000, logins=[login], cs=None)
        self.assertIn("s_A", d1["unattributed"]["reels"], "PREMISE: the reel is not mixed")
        self.assertIn("s_A", d1["characters"]["Hammerdin"]["reels"], "PREMISE: the reel is not mixed")
        r2, _d2 = self.ingest(self.rows(), now_ms=T0 + 9800000, logins=[login], cs=None)
        self.assertEqual(r2.get("refiled"), [], "a reel already filed under its character was filed again")

    def test_a_reel_still_with_no_login_stays_unattributed(self):
        self.ingest(self.rows(), now_ms=T0 + 9700000, logins=[], cs=None)
        r2, d2 = self.ingest(self.rows(), now_ms=T0 + 9800000, logins=[], cs=None)
        self.assertEqual(r2.get("refiled"), [])
        self.assertEqual(d2["unattributed"]["reads"], 3)


class EachCardIsHandedWhatItsCharacterWears(unittest.TestCase):
    """#234 step 2 - what the in-game card is fed: every doll slot in the game's order, a slot nothing showed said as not
    seen (never "empty"), the Vault's own tier words on the Vault's own bars, keyed by the learner's own fold."""

    BARS = {"proven": 3, "hardened": 6}

    def ledger(self):
        d = E._empty()
        d["characters"]["KOnyORush"] = {"name": "KOnyORush", "reels": ["s_1", "s_2"], "lastTs": T0,
                                        "slots": {"helm": {"item": "Harlequin Crest", "sightings": 4, "ts": T0,
                                                           "reel": "s_1"},
                                                  "weapon": {"item": "Grief", "sightings": 1, "ts": T0, "reel": "s_2"},
                                                  "torso": {"item": "Enigma", "sightings": 7, "ts": T0, "reel": "s_2"}},
                                        "unplaced": {"String of Ears": {"sightings": 2, "why": "slot not told"}}}
        return d

    def test_the_doll_is_the_games_ten_slots(self):
        import slot_identity as S
        self.assertEqual(sorted(E.DOLL_ORDER), sorted(set(S.EQUIP_SLOTS) | set(S.UNMEASURED_SLOTS)),
                         "the card's doll and the measured slots name different slots")

    def test_every_slot_is_listed_with_its_tier_or_as_not_seen(self):
        g = E.gear_by_key(self.ledger(), CS._fold, self.BARS)["konyorush"]
        slots = {s["slot"]: s for s in g["slots"]}
        self.assertEqual([s["slot"] for s in g["slots"]], list(E.DOLL_ORDER))
        self.assertEqual((slots["helm"]["item"], slots["helm"]["tier"]), ("Harlequin Crest", "PROVEN"))
        self.assertEqual(slots["weapon"]["tier"], "WATCHED")
        self.assertEqual(slots["torso"]["tier"], "HARDENED")
        self.assertIsNone(slots["boots"]["item"], "a slot nothing showed was given an item")
        self.assertIsNone(slots["boots"]["tier"], "a slot nothing showed was given a tier")
        self.assertEqual([u["item"] for u in g["unplaced"]], ["String of Ears"])
        self.assertEqual(g["reels"], 2)

    def test_no_bars_is_unknown_and_no_ledger_is_unknown(self):
        g = E.gear_by_key(self.ledger(), CS._fold, None)["konyorush"]
        self.assertEqual({s["slot"]: s["tier"] for s in g["slots"]}["helm"], "UNKNOWN")
        self.assertIsNone(E.gear_by_key(None, CS._fold, self.BARS), "an unreadable ledger was handed over as data")


RED_PROOF = [
    {"why": "#234 - an old visit is never given its last frame, so its closing read never runs and no login appears",
     "file": "char_select.py",
     "find": "        v[\"lastFrame\"] = {\"reel\": reel, \"frame\": last[0], \"ts\": last[1]}\n",
     "replace": "        pass\n",
     "matches": 1},
    {"why": "#234 - a back-filled visit whose two frames are close together owes no close (the old gap rule alone)",
     "file": "char_select.py",
     "find": "    if v.get(\"closeOwed\"):\n        return True",
     "replace": "    if False:\n        return True",
     "matches": 1},
    {"why": "#234 - the back-fill reads the visit's FIRST frame, not its last",
     "file": "char_select.py",
     "find": "            if hit:\n                last = (os.path.basename(p), ts)\n",
     "replace": "            if hit and last is None:\n                last = (os.path.basename(p), ts)\n",
     "matches": 1},
    {"why": "#234 - an ingested reel is never filed again when a login arrives later",
     "file": "equipped_ledger.py",
     "find": "            if not _refile_due(d, reel):\n                continue\n",
     "replace": "            continue\n",
     "matches": 1},
    {"why": "#234 - a re-filed reel leaves its old unattributed counts behind (counted twice)",
     "file": "equipped_ledger.py",
     "find": "            _unfile_unattributed(d, reel, hist_dir)        # #234 - a login now names this reel's character\n",
     "replace": "            pass\n",
     "matches": 1},
    {"why": "#234 - a reel already filed under a character is filed again",
     "file": "equipped_ledger.py",
     "find": "    return not any(reel[\"sid\"] in (rec.get(\"reels\") or []) for rec in (d.get(\"characters\") or {}).values())\n",
     "replace": "    return True\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
