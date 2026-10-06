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

    def test_a_visit_never_takes_the_next_visits_screen(self):
        """the v3548 eye: with no select frame near the visit's start (its own frames thinned away) the walk ran on through
        the reel and took a LATER visit's screen - and so its login - as this visit's"""
        vid = self._old_visit("reel_s_11", [(T0 + i * 1000, True) for i in range(2)] + [(T0 + 200000, False)])
        rd = os.path.join(self.hist, "reel_s_11")
        for ts in (T0, T0 + 1000):                                # its own frames no longer show the screen
            with open(os.path.join(rd, "f_%d.jpg" % ts), "wb") as f:
                f.write(b"no")
        self.reel("reel_s_11", [(T0 + 300000 + i * 1000, True) for i in range(2)])   # a LATER visit, same reel
        self.tick(lambda ts: "Frostnova", T0 + 700000)
        v = CS.load()["visits"][vid]
        self.assertNotEqual((v.get("lastFrame") or {}).get("ts"), T0 + 301000,
                            "the old visit took the next visit's screen as its own")
        self.assertIn("no character-select frame", str(v.get("closed")), v)

    def test_a_walk_cut_by_the_budget_resumes_where_it_stopped(self):
        """the v3548 eye: a cut walk restarted the reel from its first frame on every tick, so one long old visit held
        the closing reads and the live scan behind it for ever"""
        self._old_visit("reel_s_12", [(T0 + i * 1000, True) for i in range(2)] + [(T0 + 200000, False)])
        self.reel("reel_s_12", [(T0 + 2000 + i * 1000, True) for i in range(20)])     # the visit ran on: 22 frames in all
        seen = []
        real_stats = self.stats

        def stats(p):
            seen.append(CS._frame_ts(p))
            return real_stats(p)
        tick = [0.0]

        def clock():
            tick[0] += 1.0
            return tick[0]
        for _ in range(12):
            CS.tick(root=self.hist, stats=stats, reader=self.reader_for(lambda ts: "Frostnova"),
                    now=(T0 + 900000) / 1000.0, budget_s=6.0, clock=clock)
            if CS.logins(CS.load()):
                break
        self.assertEqual([x["character"] for x in CS.logins(CS.load())], ["Frostnova"], "the cut walk never finished")
        self.assertIn(T0 + 21000, self.reads, "the closing read was not the visit's LAST frame")
        walked = [t for t in seen if t is not None and t <= T0 + 21000]
        self.assertLess(len(walked), 2 * 22, "the walk started over after every cut (%d frame looks for 22 frames)"
                        % len(walked))

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
        # REG-1893 - an empty pair of lists holds no double count either: the reel's Shako and Enigma must be there
        self.assertGreaterEqual(len(slot_sightings + unplaced), 2, "Hammerdin carries %d sighting(s), so 'none counted "
                                "twice' would be about nothing: %r" % (len(slot_sightings + unplaced),
                                                                       d3["characters"]["Hammerdin"]))
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

    def test_a_reel_that_waits_for_the_learner_loses_nothing(self):
        """the v3548 eye: the reel was taken back off the unattributed list BEFORE the learner's wait, so a waiting reel
        lost its worn items from both the character and the unattributed count for good."""
        self.ingest(self.rows(), now_ms=T0 + 9700000, logins=[], cs=None)
        os.makedirs(os.path.join(self.hist, "reel_s_A"), exist_ok=True)
        cs = CS._empty()
        cs["reels"] = {"reel_s_A": {"pos": 1, "frames": 50}}          # the learner has not walked it yet
        r2, d2 = self.ingest(self.rows(), now_ms=T0 + 9800000, logins=[self.LOGIN], cs=cs)
        self.assertEqual(r2.get("refiled"), [], "a reel was filed again while the learner had not walked it")
        self.assertEqual(d2["unattributed"]["reads"], 3, "a waiting reel's worn items left the unattributed count")
        self.assertIn("s_A", d2["unattributed"]["reels"])
        cs["reels"]["reel_s_A"]["pos"] = 50
        r3, d3 = self.ingest(self.rows(), now_ms=T0 + 9900000, logins=[self.LOGIN], cs=cs)
        self.assertEqual(r3.get("refiled"), ["s_A"])
        self.assertIn("Enigma", json.dumps(d3["characters"].get("Hammerdin")))

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

    def test_the_console_hands_each_card_its_gear(self):
        """the route the in-game room asks (/api/chars_learned) carries the gear map built by THIS rule, keyed by the
        learner's own fold - read as code, comments dropped"""
        import io
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        self.assertEqual(code.count("_gear = _el.gear_by_key(_gd, _cs._fold, _cs.tier_bars())"), 1,
                         "/api/chars_learned does not build the cards' gear with gear_by_key and the learner's fold")
        self.assertEqual(code.count('"gear": _gear, "gearWhy": _gwhy})'), 1, "the gear never reaches the room")

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
     "find": "        if _refile and not _refile_due(d, reel):\n            continue\n",
     "replace": "        if _refile:\n            continue\n",
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
    {"why": "#234 - the room's route stops carrying the cards' gear",
     "file": "control_app.py",
     "find": "                                 \"gear\": _gear, \"gearWhy\": _gwhy})\n",
     "replace": "                                 })\n",
     "matches": 1},
    {"why": "#234 (the v3548 eye) - the reel is taken back BEFORE the learner's wait, so a waiting reel loses its items",
     "file": "equipped_ledger.py",
     "find": "        if cs_waits(cs, reel, hist_dir, now):\n            waiting.append(reel[\"sid\"])\n            continue\n        if _refile:\n",
     "replace": "        if _refile and _unfile_unattributed(d, reel, hist_dir) is None and cs_waits(cs, reel, hist_dir, now):\n            waiting.append(reel[\"sid\"])\n            continue\n        if _refile:\n",
     "matches": 1},
    {"why": "#234 (the v3548 eye) - with no select frame near its start the walk runs on and takes the next visit's screen",
     "file": "char_select.py",
     "find": "            if ts - (last[1] if last else first) > VISIT_GAP_S * 1000:\n",
     "replace": "            if last is not None and ts - last[1] > VISIT_GAP_S * 1000:\n",
     "matches": 1},
    {"why": "#234 (the v3548 eye) - a walk cut by the budget restarts from the visit's first frame every tick",
     "file": "char_select.py",
     "find": "                v[\"bf\"] = {\"pos\": ts, \"last\": list(last) if last else None}\n",
     "replace": "                pass\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
