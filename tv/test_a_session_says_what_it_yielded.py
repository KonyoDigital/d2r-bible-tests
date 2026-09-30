# -*- coding: utf-8 -*-
"""A session says what it yielded - the Ledger 3.0 per-session extraction record, driven end to end.

HIS ORDER 2026-09-28 (#58, handoff §33): "i want to see the reels n shelf great we have that now the
extraction and tallying and counting and proof of ledgers to all need that same visual rendering so i
can see that it was tallied properly and counted correctly. and where it was seen.."

THE DEFECT (LEDGER3_DESIGN.md, measured read-only 2026-09-28/29): no door answered "what did reel X
yield". /api/session is keyed by POSITION (n=), /api/forensics dies once a reel is released, the river
stamps carry a COUNT of names and never the names, and the three stores that know one reel spell it
three ways (the journal's sessionId, the chronicle's reel, the vault's session) - 3,914 of 8,517
chronicle sightings are the same row under two spellings. Nothing joined them.

WHAT THIS LAW DRIVES, with no browser and no live store:
  1. tv/ledger3.session_record over fixture stores handed in as objects - the journal rows, the
     chronicle book, the vault ledger, a temp shelf, river stamps, a survey and a tombstone;
  2. the two GET doors THE ROUTE SERVES - control_app.Handler.do_GET for /api/ledger3/session?id=
     and /api/ledger3/sessions, in-process, with every path authority pointed at the temp root
     (HIST_DIR, VAULT_LEDGER_PATH, _CHRON_EVIDENCE_PATH, replay.JOURNAL, TV_HIST);
  3. the doctor's 'ledger3 sessions' row over the same fixture stores.

Fixtures only. His journal, book and ledger are never opened: every path is a temp dir, and the
TV_HIST env is set for the duration so river_stamp / retro_triage / the tombstones resolve there.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import unittest.mock as mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except ImportError:
    _enable = None

import ledger3 as L3

# real-shaped ids: tombstone_view excludes anything that is not s_<13 digits>_<n>
A = "s_1790000000000_1"          # the reel with reads, a book entry and vault witnesses
B = "s_1790000000000_2"          # OCR-only, later
C = "s_1790000000000_3"          # sealed on the shelf, NO journal rows - the lost trail
D = "s_1790000000000_4"          # released: a tombstone, no folder
NOBODY = "s_1790000000000_9"     # no store knows it


def _journal_rows():
    """His journal's own shapes (keys measured on 1,493 live rows 2026-09-29), for A and B."""
    fa = "reel_%s/f_1" % A
    return [
        {"ts": 1790000001000, "lane": "system", "scene": "session_start", "sessionId": A, "door": "shadow",
         "ver": "vTEST", "names": [], "n": 0},
        {"ts": 1790000002000, "lane": "deep-owed", "frameId": "f_owed_1", "sessionId": A, "door": "shadow",
         "why": "committed to the deep reader"},
        {"ts": 1790000003000, "lane": "deep", "mode": "g5-primary", "model": "grok-subscription-cli",
         "scene": "stash", "names": ["Shako", "Horadric Cube"], "names_loc": {"Shako": "stash",
                                                                            "Horadric Cube": "inventory"},
         "lifecycle_tags": {"Shako": "farmed"}, "vault_names": ["Shako"], "thrown_names": [],
         "pending_names": ["Horadric Cube"], "farmed_names": [], "unvault_names": [],
         "frameId": fa, "sessionId": A, "conf": 0.9, "provisional": False, "door": "shadow"},
        {"ts": 1790000004000, "lane": "ocr", "model": "ocr-mac", "scene": "loot",
         "names": ["Yur Gamlng Rlg"], "provisional": True, "frameId": "4_1790000004000",
         "lifecycle_tags": {"Yur Gamlng Rlg": "ocr"}, "sessionId": A, "door": "shadow"},
        {"ts": 1790000005000, "lane": "deep", "mode": "g5-primary", "model": "grok-subscription-cli",
         "scene": "stash", "names": ["Shako"], "names_loc": {"Shako": "stash"}, "frameId": "reel_%s/f_2" % A,
         "sessionId": A, "conf": 0.88, "provisional": False, "door": "shadow"},
        {"ts": 1790000006000, "lane": "verify", "mode": "verify", "names": [], "frameId": "5_1790000006000#v",
         "verify": {"confirm": ["Shako"], "missed": [], "not_present": []}, "sessionId": A, "door": "shadow"},
        {"ts": 1790000007000, "lane": "kai", "mode": "kai", "names": [], "sessionId": A, "frameId": "",
         "kai": {"register": {"count": 1, "items": [{"name": "Shako", "tier": "unique", "loc": "stash",
                                                       "frameId": "f_1.jpg", "firstSeenTs": 1790000003000}]}}},
        {"ts": 1790000008000, "lane": "intake", "mode": "intake", "names": [], "sessionId": A,
         "intake": {"tab": "runes", "kind": "kai-vault", "counts": {"Ist": 1}, "total": 1, "ok": True},
         "frameId": "reel_%s/f_2" % A, "door": "shadow"},
        {"ts": 1790000009000, "lane": "system", "scene": "session_end", "sessionId": A, "door": "shadow",
         "names": [], "n": 0},
        # B: later, OCR only
        {"ts": 1790000101000, "lane": "ocr", "model": "ocr-mac", "names": ["Sp1rit"], "provisional": True,
         "frameId": "1_1790000101000", "sessionId": B, "door": "live"},
        # an unstamped pre-v780 row: nothing to key on, never a reel
        {"ts": 1780000000000, "lane": "ocr", "names": ["old"], "frameId": "x"},
    ]


def _chron_book():
    """The chronicle book: Shako from reel A under BOTH spellings (the same row twice), plus a
    second frame by the other lane, plus a sighting from another reel. Sets: nothing from A."""
    return {"uniques": {
        "Shako": [
            {"reel": "reel_" + A, "frame": "f_1.jpg", "witness": "none", "conf": 0.9, "lane": "claude"},
            {"reel": "s_1790000000000_1", "frame": "f_2.jpg", "witness": "none", "conf": 0.8, "lane": "grok"},
            {"reel": "reel_" + A, "frame": "f_2.jpg", "witness": "none", "conf": 0.8, "lane": "grok"},
            {"reel": "reel_s_1500000000000_7", "frame": "f_9.jpg", "witness": "none", "conf": 0.7, "lane": "claude"},
        ],
        "Tal Rasha's Horadric Crest": [
            {"reel": "reel_s_1500000000000_7", "frame": "f_3.jpg", "witness": "none", "conf": 0.7, "lane": "claude"},
        ]}, "sets": {}}


def _vault_doc():
    """The vault ledger: Shako witnessed in reel A on ONE still screen held for 12 frames (one
    re-look bucket) and once more in a second bucket, plus one visit from another session."""
    w = []
    for i in range(12):
        w.append({"session": A, "witness": "%s#0" % A, "frame": "f_%03d.jpg" % i, "conf": 0.9, "lane": "stash"})
    w.append({"session": A, "witness": "%s#1" % A, "frame": "f_100.jpg", "conf": 0.9, "lane": "stash"})
    w.append({"session": "s_1780000000000_7", "witness": "s_1780000000000_7#0", "frame": "f_9.jpg",
              "conf": 0.9, "lane": "stash"})
    return {"owned": [
        {"name": "Shako", "lane": "stash", "kind": "item", "count": None, "conf": 0.9, "witnesses": w,
         "lastSeenTs": 1790000005000},
        {"name": "Chance Guards", "lane": "stash", "kind": "item", "count": None, "conf": 0.9,
         "witnesses": [{"session": "s_1780000000000_7", "witness": "s_1780000000000_7#0",
                        "frame": "f_8.jpg", "conf": 0.9, "lane": "stash"}], "lastSeenTs": 1780000000000},
    ]}


def _shelf(root):
    """A temp shelf: A sealed with two stills, C sealed with NO journal rows, nothing for D."""
    hist = os.path.join(root, "hist")
    for sid, sealed, stills in ((A, True, 2), (C, True, 1)):
        rd = os.path.join(hist, "reel_" + sid)
        os.makedirs(rd)
        for i in range(stills):
            io.open(os.path.join(rd, "f_%d.jpg" % (i + 1)), "wb").close()
        if sealed:
            _write(os.path.join(rd, "kai_report.json"), "{}")
        _write(os.path.join(rd, "index.json"), json.dumps({"sessionId": sid, "n": stills, "frames": []}))
    return hist


def _write(path, text):
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _stores(root, **over):
    st = {"journal": _journal_rows(), "chron": _chron_book(), "vault": _vault_doc(),
          "hist": _shelf(root) if not os.path.isdir(os.path.join(root, "hist")) else os.path.join(root, "hist"),
          "stamps": {"ok": True, "rows": [
              {"reel": "reel_" + A, "station": "TRIAGE", "by": "loop:tvd-retro-triage", "at": 1},
              {"reel": "reel_" + A, "station": "ROUTED", "by": "loop:tvd-retro-triage", "at": 2}]},
          "triage": {"reel_" + A: {"panels": 1, "frames": 2, "kinds": {"stash": 1}, "ts": 5, "full": True}},
          "tombstones": [{"reel": "reel_" + D, "session": D, "mb": 9.5, "pages": 3, "frames": 40,
                          "why": "read and sealed by BOTH lanes", "deletedTs": 1790000200000}],
          "unknown": []}
    st.update(over)
    return st


def _item(rec, name):
    for it in rec["items"]:
        if it["name"] == name:
            return it
    return None


class TheRecordOverFixtureStores(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ledger3-law-")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_one_reel_says_what_it_yielded_who_read_it_and_where(self):
        rec = L3.session_record(A, _stores(self.root))
        self.assertTrue(rec["ok"], rec)
        self.assertEqual(rec["session"], A)
        self.assertEqual(rec["reel"], "reel_" + A)
        self.assertEqual(rec["door"], "shadow")
        self.assertEqual(rec["ver"], "vTEST")
        self.assertEqual(rec["span"], {"t0": 1790000001000, "t1": 1790000009000})
        # WHO read it: the model that answered, else the lane - measured off the read rows only
        self.assertEqual(rec["readers"], {"grok-subscription-cli": 2, "ocr-mac": 1, "lane:verify": 1})
        self.assertEqual(rec["journal"]["reads"], {"answered": 4, "owed": 1, "lost": 1})
        self.assertEqual(rec["journal"]["intakeShots"], 1)
        # what it yielded: 2 real names, the OCR junk apart, never counted as named
        self.assertEqual(rec["yield"]["named"], 2, rec["yield"])
        self.assertEqual(rec["yield"]["provisional"], 1)
        self.assertEqual(rec["yield"]["registered"], 1)
        self.assertEqual(rec["yield"]["chronicle"], 1)
        self.assertEqual(rec["yield"]["vault"], 1)
        self.assertEqual(rec["yield"]["routedVault"], 1)
        self.assertEqual(rec["yield"]["pending"], 1)
        self.assertEqual(rec["yield"]["confirmed"], 1)
        shako = _item(rec, "Shako")
        self.assertIsNotNone(shako)
        j = shako["journal"]
        self.assertEqual(j["reads"], 3)                       # 2 deep + the second look
        self.assertEqual(j["readBy"], ["grok-subscription-cli", "lane:verify"])
        self.assertEqual(j["loc"], "stash")                  # WHERE it was seen, the reader's own word
        self.assertEqual(j["tag"], "farmed")
        self.assertTrue(j["confirmed"])
        self.assertFalse(j["provisional"])
        self.assertEqual(j["routed"], {"vault": True})
        self.assertEqual(j["registered"], {"tier": "unique", "loc": "stash", "frameId": "f_1.jpg"})
        self.assertEqual(j["frames"], ["reel_%s/f_1" % A, "reel_%s/f_2" % A, "5_1790000006000#v"])
        cube = _item(rec, "Horadric Cube")
        self.assertEqual(cube["journal"]["loc"], "inventory")
        self.assertEqual(cube["journal"]["routed"], {"pending": True})
        self.assertIsNone(cube["chronicle"])
        self.assertIsNone(cube["vault"])
        junk = _item(rec, "Yur Gamlng Rlg")
        self.assertTrue(junk["journal"]["provisional"])
        self.assertEqual(junk["journal"]["readBy"], ["ocr-mac"])

    def test_the_chronicle_side_counts_one_reel_once_whichever_way_it_was_spelled(self):
        rec = L3.session_record(A, _stores(self.root))
        c = _item(rec, "Shako")["chronicle"]
        self.assertEqual(c["ledger"], "uniques")
        # f_1 under "reel_s_…", f_2 under BOTH spellings: 2 sightings from this reel, never 1 or 3
        self.assertEqual(c["sightings"], 2, c)
        self.assertEqual(c["frames"], ["f_1.jpg", "f_2.jpg"])
        self.assertEqual(c["lanes"], ["claude", "grok"])
        self.assertEqual(c["independentReels"], 2)          # this reel + the other, not 3 spellings
        self.assertIn("cross-lane", c["witnessTags"])
        self.assertIn("cross-reel", c["witnessTags"])
        self.assertFalse(c["hand"])
        self.assertEqual(rec["evidenceFrames"]["chronicle"], 2)
        # the record is the same whichever spelling is asked for
        rec2 = L3.session_record("reel_" + A, _stores(self.root))
        self.assertEqual(rec2["session"], A)
        self.assertEqual(_item(rec2, "Shako")["chronicle"], c)

    def test_the_vault_side_counts_visits_never_frames(self):
        rec = L3.session_record(A, _stores(self.root))
        v = _item(rec, "Shako")["vault"]
        self.assertEqual(v["witnessesHere"], 13)
        self.assertEqual(v["visitsHere"], 2, v)            # one still screen x12 is ONE visit (§34.2)
        self.assertEqual(v["sawItHere"], 2)
        self.assertEqual(len(v["frames"]), 13)
        self.assertEqual(v["tier"]["tier"], "WATCHED")     # 3 visits in all, under the 10-visit bar
        self.assertEqual(v["tier"]["trials"], 3)
        self.assertEqual(v["tier"]["successes"], 3)
        # 14 frames in 3 visits: the FRAME math would file it PROVEN, the visits say WATCHED - that is
        # exactly the row his §34.2 ruling flags ("Keep filed, flag 'retro: WATCHED'"), and the record says so
        self.assertEqual(v["retro"], "retro: WATCHED")
        self.assertEqual(rec["evidenceFrames"]["vault"], 13)
        # AGREEMENT - the reader's names against the vault's witnesses, side by side, junk left out
        self.assertEqual(rec["agreement"]["both"], ["shako"])
        self.assertEqual(rec["agreement"]["journalOnly"], ["horadric cube"])
        self.assertEqual(rec["agreement"]["vaultOnly"], [])
        self.assertIn("1 provisional", rec["agreement"]["why"])

    def test_the_film_the_station_the_survey_and_the_tombstone_ride_the_record(self):
        st = _stores(self.root)
        rec = L3.session_record(A, st)
        self.assertEqual(rec["film"], {"frames": 2, "onShelf": True, "sealed": True,
                                       "why": "2 film still(s) on the shelf"})
        self.assertEqual(rec["station"]["current"], "ROUTED")
        self.assertEqual(rec["station"]["hops"], 2)
        self.assertEqual(rec["survey"], {"panels": 1, "frames": 2, "full": True, "ts": 5})
        self.assertIsNone(rec["tombstone"])
        self.assertEqual(rec["knownBy"], ["journal", "chronicle", "vault", "shelf", "river", "survey"])
        self.assertEqual(rec["unknown"], [])
        # D: released - the tombstone is the film's account, the journal never had it
        recd = L3.session_record(D, st)
        self.assertTrue(recd["ok"])
        self.assertEqual(recd["film"]["onShelf"], False)
        self.assertEqual(recd["film"]["frames"], 40)
        self.assertIn("released", recd["film"]["why"])
        self.assertEqual(recd["tombstone"]["session"], D)
        self.assertEqual(recd["knownBy"], ["tombstone"])
        self.assertTrue(any("rotated out" in u for u in recd["unknown"]), recd["unknown"])
        self.assertEqual(recd["station"]["hops"], 0)
        self.assertIn("never stamped", recd["station"]["why"])
        self.assertIsNone(recd["survey"])

    def test_a_session_nobody_knows_is_refused_never_an_empty_record(self):
        rec = L3.session_record(NOBODY, _stores(self.root))
        self.assertFalse(rec["ok"])
        self.assertIn("no store knows", rec["why"])
        self.assertNotIn("items", rec)
        self.assertFalse(L3.session_record("", _stores(self.root))["ok"])

    def test_an_unreadable_side_is_unknown_never_zero(self):
        rec = L3.session_record(A, _stores(self.root, vault=None, chron=None, triage=None, stamps=None))
        self.assertTrue(rec["ok"])
        self.assertIsNone(rec["yield"]["vault"])
        self.assertIsNone(rec["yield"]["chronicle"])
        self.assertIsNone(rec["evidenceFrames"]["vault"])
        self.assertIsNone(rec["evidenceFrames"]["chronicle"])
        self.assertIsNone(rec["agreement"])
        self.assertIsNone(_item(rec, "Shako")["vault"])
        self.assertIsNone(_item(rec, "Shako")["chronicle"])
        self.assertIsNone(rec["station"]["hops"])
        self.assertIsNone(rec["survey"])
        joined = " ".join(rec["unknown"])
        for word in ("vault witness ledger", "chronicle book", "structural survey", "river stamps"):
            self.assertIn(word, joined, rec["unknown"])
        # and a journal that cannot be read: the reader's side is UNKNOWN, the book still answers
        rec2 = L3.session_record(A, _stores(self.root, journal=None))
        self.assertTrue(rec2["ok"])
        self.assertIsNone(rec2["journal"])
        self.assertIsNone(rec2["readers"])
        self.assertEqual(rec2["yield"]["named"], 0)
        self.assertEqual(rec2["yield"]["chronicle"], 1)
        self.assertTrue(any("journal could not be read" in u for u in rec2["unknown"]))

    def test_the_list_is_newest_first_cheap_and_honest_about_its_cap(self):
        ls = L3.sessions(_journal_rows())
        self.assertTrue(ls["ok"])
        self.assertEqual([s["session"] for s in ls["sessions"]], [B, A])   # the unstamped row is no reel
        self.assertEqual(ls["total"], 2)
        self.assertEqual(ls["shown"], 2)
        a = ls["sessions"][1]
        self.assertEqual(a["readers"], {"grok-subscription-cli": 2, "ocr-mac": 1, "lane:verify": 1})
        self.assertEqual((a["named"], a["provisional"], a["registered"], a["routedVault"]), (2, 1, 1, 1))
        self.assertEqual(ls["sessions"][0]["door"], "live")
        capped = L3.sessions(_journal_rows(), limit=1)
        self.assertEqual((capped["total"], capped["shown"], len(capped["sessions"])), (2, 1, 1))
        self.assertIn("?limit=", capped["why"])
        self.assertFalse(L3.sessions(None)["ok"])
        self.assertIsNone(L3.sessions(None)["total"])

    def test_the_census_names_the_sealed_reel_whose_trail_is_gone(self):
        st = _stores(self.root)
        got = L3.census(st)
        self.assertTrue(got["ok"], got)
        self.assertEqual(got["trails"], 1)
        self.assertEqual(got["noTrail"], ["reel_" + C])
        self.assertEqual(got["agreement"], {"both": 1, "journalOnly": 1, "vaultOnly": 0})
        self.assertFalse(L3.census(_stores(self.root, journal=None))["ok"])
        self.assertIsNone(L3.census(_stores(self.root, journal=None))["trails"])
        self.assertFalse(L3.census(_stores(self.root, hist=os.path.join(self.root, "nope")))["ok"])


    def test_a_reel_released_in_passes_keeps_every_pass_and_the_latest_act_wins(self):
        """REG-1557 - MEASURED 2026-09-30 on his ledger, read-only: 3 of the 29 reels on his shelf carry
        tombstones, 14 rows between them, every row with a `kept` list (the drain releases FRAMES and leaves
        the evidence stills), one reel alone with FOUR rows - 65, 14, 14, 14 stills before each pass, 13 kept.
        A tombstone is a release EVENT. reel_custody's rule for the same store: the LAST row wins, the count
        beside it."""
        kept = ["f_1.jpg"]
        rows = [{"reel": "reel_" + A, "session": A, "mb": 15.1, "pages": 0, "frames": 65, "kept": kept,
                 "why": "read (0 pages) and sealed by BOTH lanes", "deletedTs": 1790000300000},
                {"reel": "reel_" + A, "session": A, "mb": 3.2, "pages": 0, "frames": 14, "kept": kept,
                 "why": "read (0 pages) and sealed by BOTH lanes", "deletedTs": 1790000400000}]
        rec = L3.session_record(A, _stores(self.root, tombstones=rows))
        self.assertTrue(rec["ok"], rec)
        self.assertEqual(rec["tombstone"]["deletedTs"], 1790000400000)     # the latest act, never the first
        self.assertEqual(rec["releases"], {"n": 2, "lastTs": 1790000400000,
                                           "released": (65 - 1) + (14 - 1), "kept": 1})
        film = rec["film"]
        self.assertEqual((film["frames"], film["onShelf"], film["sealed"]), (2, True, True))
        self.assertEqual(film["released"], rec["releases"])
        self.assertIn("2 release pass(es) took 77 frame(s)", film["why"])
        self.assertIn("kept 1", film["why"])
        for k in ("shelf", "tombstone"):
            self.assertIn(k, rec["knownBy"])
        # the folder gone after two passes: the film is the LAST pass's account, the pass count beside it
        rows_d = [dict(r, reel="reel_" + D, session=D) for r in rows]
        recd = L3.session_record(D, _stores(self.root, tombstones=rows_d))
        self.assertEqual((recd["film"]["frames"], recd["film"]["onShelf"], recd["film"]["releases"]), (14, False, 2))
        self.assertIn("released (2 pass(es))", recd["film"]["why"])
        self.assertEqual(recd["releases"]["n"], 2)
        # a pass whose frame count nobody took leaves `released` UNKNOWN, never a partial sum
        rows_u = [dict(rows[0]), dict(rows[1], frames=None)]
        recu = L3.session_record(A, _stores(self.root, tombstones=rows_u))
        self.assertIsNone(recu["releases"]["released"])
        self.assertEqual(recu["releases"]["n"], 2)
        self.assertIn("UNKNOWN", recu["film"]["why"])
        # no tombstone at all: the record says none, and the film carries no release key
        plain = L3.session_record(A, _stores(self.root))
        self.assertIsNone(plain["releases"])
        self.assertNotIn("released", plain["film"])


class _RouteWorld(unittest.TestCase):
    """The doors' world: the real handler, in-process, with every path authority on the temp root."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ledger3-route-")
        self.hist = _shelf(self.root)
        self.journal = os.path.join(self.root, "sessions.jsonl")
        with io.open(self.journal, "w", encoding="utf-8") as fh:
            for r in _journal_rows():
                fh.write(json.dumps(r) + "\n")
        self.book = os.path.join(self.root, "book.json")
        _write(self.book, json.dumps(_chron_book()))
        self.vault = os.path.join(self.root, "vault.json")
        _write(self.vault, json.dumps(_vault_doc()))
        import control_app as CA
        import replay
        self.CA, self.replay = CA, replay
        self._env = mock.patch.dict(os.environ, {"TV_HIST": self.hist})
        self._env.start()
        self._patches = [
            mock.patch.object(CA, "HIST_DIR", self.hist),
            mock.patch.object(CA, "VAULT_LEDGER_PATH", self.vault),
            mock.patch.object(CA, "_CHRON_EVIDENCE_PATH", self.book),
            mock.patch.object(replay, "JOURNAL", self.journal),
        ]
        for p in self._patches:
            p.start()
        self._cache = CA.__dict__.pop("_JRNL_CACHE", None)

    def tearDown(self):
        for p in reversed(self._patches):
            p.stop()
        self._env.stop()
        self.CA.__dict__.pop("_JRNL_CACHE", None)
        if self._cache is not None:
            self.CA._JRNL_CACHE = self._cache
        shutil.rmtree(self.root, ignore_errors=True)

    def _get(self, raw_path):
        got = []
        h = self.CA.Handler.__new__(self.CA.Handler)
        h.path = raw_path
        h._json = lambda code, obj: got.append((code, json.loads(json.dumps(obj))))
        h.do_GET()
        self.assertEqual(len(got), 1, "PREMISE: the route did not answer exactly once")
        return got[0]


class TheRouteServesIt(_RouteWorld):
    """The two GET doors, driven through the real handler with every path authority on the temp root."""

    def test_the_record_door_answers_by_id_never_by_position(self):
        code, rec = self._get("/api/ledger3/session?id=" + A)
        self.assertEqual(code, 200)
        self.assertTrue(rec["ok"], rec)
        self.assertEqual(rec["session"], A)
        self.assertEqual(rec["readers"], {"grok-subscription-cli": 2, "ocr-mac": 1, "lane:verify": 1})
        self.assertEqual(rec["yield"]["named"], 2)
        self.assertEqual(rec["film"]["frames"], 2)
        shako = _item(rec, "Shako")
        self.assertEqual(shako["chronicle"]["sightings"], 2)
        self.assertEqual(shako["vault"]["visitsHere"], 2)
        self.assertEqual(shako["vault"]["tier"]["tier"], "WATCHED")
        self.assertEqual(rec["agreement"]["both"], ["shako"])
        # the reel folder's spelling opens the same record
        self.assertEqual(self._get("/api/ledger3/session?id=reel_" + A)[1]["session"], A)
        # no id: refused with the ask, never a record
        code, no = self._get("/api/ledger3/session")
        self.assertFalse(no["ok"])
        self.assertIn("id=", no["why"])
        code, nobody = self._get("/api/ledger3/session?id=" + NOBODY)
        self.assertFalse(nobody["ok"])
        self.assertIn("no store knows", nobody["why"])

    def test_the_list_door_is_newest_first_and_honours_its_limit(self):
        code, ls = self._get("/api/ledger3/sessions")
        self.assertEqual(code, 200)
        self.assertTrue(ls["ok"], ls)
        self.assertEqual([s["session"] for s in ls["sessions"]], [B, A])
        self.assertEqual(ls["sessions"][1]["named"], 2)
        code, one = self._get("/api/ledger3/sessions?limit=1")
        self.assertEqual((one["total"], one["shown"]), (2, 1))

    def test_an_unreadable_vault_ledger_leaves_that_side_unknown_on_the_wire(self):
        _write(self.vault, "{not json")
        code, rec = self._get("/api/ledger3/session?id=" + A)
        self.assertTrue(rec["ok"])
        self.assertIsNone(rec["yield"]["vault"])
        self.assertIsNone(_item(rec, "Shako")["vault"])
        self.assertTrue(any("vault witness ledger" in u for u in rec["unknown"]), rec["unknown"])
        os.remove(self.vault)
        code, rec = self._get("/api/ledger3/session?id=" + A)
        self.assertIsNone(rec["yield"]["vault"])
        self.assertTrue(any("measured absent" in u for u in rec["unknown"]), rec["unknown"])

    def test_a_journal_nobody_can_read_makes_the_list_unknown_not_empty(self):
        with mock.patch.object(self.CA.Handler, "_load_journal_cached", lambda self_: (_ for _ in ()).throw(OSError("torn"))), \
                mock.patch.object(self.replay, "load_journal", lambda *a, **k: (_ for _ in ()).throw(OSError("torn"))):
            code, ls = self._get("/api/ledger3/sessions")
            self.assertFalse(ls["ok"])
            self.assertIsNone(ls["total"])
            code, rec = self._get("/api/ledger3/session?id=" + A)
        self.assertTrue(rec["ok"])              # the book and the shelf still answer for A
        self.assertIsNone(rec["journal"])
        self.assertTrue(any("journal" in u for u in rec["unknown"]))

    def test_the_doctor_row_names_the_sealed_reel_whose_trail_is_gone(self):
        import console_doctor as cd
        state, why = cd._check_the_ledger3_trail_can_be_drawn()
        self.assertEqual(state, cd.MISSING, why)
        self.assertIn("reel_" + C, why)
        self.assertIn("both 1 · reader only 1 · vault only 0", why)
        self.assertIn("1 with a trail", why)
        # un-seal C: it is an unfinished recording, not a lost trail
        os.remove(os.path.join(self.hist, "reel_" + C, "kai_report.json"))
        state, why = cd._check_the_ledger3_trail_can_be_drawn()
        self.assertEqual(state, cd.OK, why)
        self.assertIn("1 with a trail", why)
        # a journal nobody can read: UNKNOWN, never "0 trails"
        with mock.patch.object(self.replay, "load_journal", lambda *a, **k: (_ for _ in ()).throw(OSError("torn"))):
            state, why = cd._check_the_ledger3_trail_can_be_drawn()
        self.assertEqual(state, cd.UNKNOWN, why)
        self.assertIn("UNKNOWN", why)
        names = [n for n, _ in cd.CHECKS]
        self.assertIn("ledger3 sessions", names, "the eagle never runs the row")
        self.assertIn("ledger3 sessions", cd.PERIODIC)
        self.assertIn("ledger3 sessions", cd.WATCHES)


class TheDoorsSayUnknownNotNothing(_RouteWorld):
    """REG-1556 - a query a door could not read is UNKNOWN, never a default it dressed as the ask.

    Found by swallow_census --check on the merged branch (control_app.py 28 -> 29): the record door swallowed
    a parse failure to "" and answered "no session id given" to a caller who HAD named a reel; the list door
    turned ?limit=abc into 200 rows as if he had asked for 200."""

    def test_a_query_that_will_not_parse_is_unknown_never_no_id_given(self):
        import urllib.parse as _up

        def _torn(*a, **k):
            raise ValueError("torn query")
        with mock.patch.object(_up, "parse_qs", _torn):
            code, rec = self._get("/api/ledger3/session?id=" + A)
        self.assertEqual(code, 200)
        self.assertFalse(rec["ok"], rec)
        self.assertIn("could not be parsed", rec["why"])
        self.assertIn("UNKNOWN", rec["why"])
        self.assertIn("ValueError", rec["why"])
        self.assertNotIn("no session id given", rec["why"])
        # PREMISE: the same ask answers once the query parses
        self.assertTrue(self._get("/api/ledger3/session?id=" + A)[1]["ok"])

    def test_a_limit_that_is_not_a_number_is_refused_never_answered_in_full(self):
        code, ls = self._get("/api/ledger3/sessions?limit=abc")
        self.assertEqual(code, 200)
        self.assertFalse(ls["ok"], ls)
        self.assertIsNone(ls["total"])
        self.assertEqual(ls["sessions"], [])
        self.assertIn("?limit=", ls["why"])
        self.assertIn("ValueError", ls["why"])
        # PREMISE: a number is honoured, and no limit means the default
        self.assertEqual(self._get("/api/ledger3/sessions?limit=1")[1]["shown"], 1)
        self.assertTrue(self._get("/api/ledger3/sessions")[1]["ok"])


RED_PROOF = [
    {
        "why": "the chronicle side compares the raw reel string, so a sighting under the other spelling is not this reel's",
        "file": "ledger3.py",
        "find": "                if reel_key(s.get(\"reel\")) != key:\n                    continue\n",
        "replace": "                if str(s.get(\"reel\") or \"\") != key:\n                    continue\n",
        "matches": 1,
    },
    {
        "why": "the same sighting under both spellings of the reel is counted twice again",
        "file": "ledger3.py",
        "find": "                k = (s.get(\"frame\"), s.get(\"lane\"), s.get(\"conf\"))\n                if k in seen:\n                    continue\n",
        "replace": "                k = (s.get(\"frame\"), s.get(\"lane\"), s.get(\"conf\"))\n                if False:\n                    continue\n",
        "matches": 1,
    },
    {
        "why": "a visit is a frame again - one still screen held for 12 frames reads as 12 visits (his ruling §34.2)",
        "file": "ledger3.py",
        "find": "        visits = set(fold({_vr.look_id(w) for w in mine if _vr.look_id(w)}))\n",
        "replace": "        visits = set(str(i) for i, _w in enumerate(mine))\n",
        "matches": 1,
    },
    {
        "why": "an OCR-only provisional name is counted as NAMED, so junk inflates the yield and the agreement",
        "file": "ledger3.py",
        "find": "            if not r.get(\"provisional\"):\n                it[\"provisional\"] = False\n",
        "replace": "            it[\"provisional\"] = False\n",
        "matches": 1,
    },
    {
        "why": "an unreadable vault ledger reads as a vault that witnessed nothing - 0 where UNKNOWN belongs",
        "file": "ledger3.py",
        "find": "    if vault_doc is None:\n        return {}, \"the vault witness ledger could not be read, so what it witnessed in this visit is UNKNOWN\"\n",
        "replace": "    if vault_doc is None:\n        return {}, None\n",
        "matches": 1,
    },
    {
        "why": "who read it is the lane again, never the model that answered",
        "file": "ledger3.py",
        "find": "    m = str(row.get(\"model\") or \"\").strip()\n    return m if m else \"lane:%s\" % str(row.get(\"lane\") or \"?\")\n",
        "replace": "    return \"lane:%s\" % str(row.get(\"lane\") or \"?\")\n",
        "matches": 1,
    },
    {
        "why": "a session no store knows comes back as an empty record instead of a refusal",
        "file": "ledger3.py",
        "find": "    if not known_by:\n        return {\"ok\": False, \"v\": V, \"session\": key, \"reel\": \"reel_\" + key,\n",
        "replace": "    if False:\n        return {\"ok\": False, \"v\": V, \"session\": key, \"reel\": \"reel_\" + key,\n",
        "matches": 1,
    },
    {
        "why": "the census stops naming a sealed reel whose journal rows are gone",
        "file": "ledger3.py",
        "find": "        elif sealed:\n            no_trail.append(reel)\n",
        "replace": "        elif False:\n            no_trail.append(reel)\n",
        "matches": 1,
    },
    {
        "why": "the record door drops the id it was asked for, so every ask is refused as 'no session id'",
        "file": "control_app.py",
        "find": "            self._json(200, ledger3_session(_sid_l3, journal_rows=_jr))\n",
        "replace": "            self._json(200, ledger3_session(\"\", journal_rows=_jr))\n",
        "matches": 1,
    },
    {
        "why": "the list door ignores ?limit=, so a capped ask is answered in full",
        "file": "control_app.py",
        "find": "            self._json(200, ledger3_sessions(_jr, limit=_lim_l3))\n",
        "replace": "            self._json(200, ledger3_sessions(_jr))\n",
        "matches": 1,
    },
    {
        "why": "the doctor row reads OK over a sealed reel whose trail is gone",
        "file": "console_doctor.py",
        "find": "    if got.get(\"noTrail\"):\n        return MISSING, (\"%d sealed reel(s) on the shelf have NO journal rows",
        "replace": "    if False:\n        return MISSING, (\"%d sealed reel(s) on the shelf have NO journal rows",
        "matches": 1,
    },
    {
        "why": "REG-1556 - the record door swallows an unparseable query to '' again and answers 'no session id given'",
        "file": "control_app.py",
        "find": "                self._json(200, _ledger3_unparsed_query(\"id\", _e_l3))\n                return\n",
        "replace": "                _sid_l3 = \"\"\n",
        "matches": 1,
    },
    {
        "why": "REG-1556 - the list door answers ?limit=abc in full again, as if he had asked for 200",
        "file": "control_app.py",
        "find": "                self._json(200, _ledger3_unparsed_query(\"limit\", _e_l3))\n                return\n",
        "replace": "                _lim_l3 = 200\n",
        "matches": 1,
    },
    {
        "why": "REG-1557 - the FIRST tombstone row wins again, so a reel released in passes shows its oldest act",
        "file": "ledger3.py",
        "find": "    tomb = tombs[-1] if tombs else None\n",
        "replace": "    tomb = tombs[0] if tombs else None\n",
        "matches": 1,
    },
    {
        "why": "REG-1557 - the film on the shelf hides the release passes again",
        "file": "ledger3.py",
        "find": "        if rel:\n            out[\"released\"] = rel\n",
        "replace": "        if False:\n            out[\"released\"] = rel\n",
        "matches": 1,
    },
    {
        "why": "REG-1557 - a pass nobody counted is skipped and the rest summed as the total",
        "file": "ledger3.py",
        "find": "            released = None          # a pass nobody counted: UNKNOWN, never a partial sum\n            break\n",
        "replace": "            continue\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main()
