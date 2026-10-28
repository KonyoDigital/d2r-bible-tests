# -*- coding: utf-8 -*-
"""#36 (REG-2911) - THE GEAR LEDGER NAMES A SESSION FROM THE ONE SPAN SOURCE: CHARACTER SELECT, THE LOBBY AND THE C PANEL.

The lead on the #36 report: equipped_ledger bound worn gear by character-select logins only, while the vault's looks read
char_select.session_characters (REG-2906/2908). Two answers to "whose was this session" - one logic was the ruling. Measured
over a fixture journal before the fix: a reel with no login whose lobby named the character filed its worn items
UNATTRIBUTED, and a login span in which the lobby then named a second character filed its gear under the login's name -
the doubt the vault holds UNKNOWN.
Now game_sessions asks `named_at` (char_select.session_span_at over session_characters' map, built with no `carried` - the
rollover chain stays the ledger's own) for every span: a span the map names takes that character, said in `named`; a span
the map holds UNKNOWN files nothing; a span it does not name keeps the login and the chain. A reel filed with no character
before is filed again once the map names it (the #234 refile). No second fold: the names come through the learner's.
Pure, over a scratch journal and a fixture ledger - never his. RED_PROOF below.
"""
import io
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
import char_select as CS  # noqa: E402
import equipped_ledger as E  # noqa: E402

T0 = 1792800000000


def _row(sid, ts, scene="inventory", **kw):
    r = {"ts": ts, "captureTs": ts, "sessionId": sid, "scene": scene, "names": [], "lane": "deep", "door": "shadow", "n": 1}
    r.update(kw)
    return r


def _worn(sid, ts, frame, item):
    return _row(sid, ts, frameId=frame, names=[item], names_loc={item: "equipped"}, names_slot={}, names_xy={})


def _seal(sid, ts):
    return {"ts": ts, "sessionId": sid, "scene": "session_end", "names": [], "lane": "system", "n": 0,
            "mode": "session_end", "door": "shadow"}


ROWS = [_row("s_A", T0 + 1000), _worn("s_A", T0 + 10000, "f_%d" % (T0 + 10000), "Shako"), _seal("s_A", T0 + 3600000),
        _row("s_B", T0 + 3900000), _worn("s_B", T0 + 4050000, "f_%d" % (T0 + 4050000), "Enigma"), _seal("s_B", T0 + 7200000)]


def _cs():
    """s_A: no login, the lobby names Hammerdin. s_B: a login as Hammerdin, then the lobby names Frostnova in that span."""
    def ch(name, witnesses):
        return {"name": name, "cls": {}, "visitLevel": {}, "titles": {}, "firstTs": T0, "lastTs": T0, "witnesses": witnesses}
    return {"visits": {"L": {"reel": "reel_s_B", "ts": T0 + 4000000,
                             "sel": [{"name": "Hammerdin", "ts": T0 + 4000000, "reader": "vision"}]}},
            "reels": {},
            "chars": {"hammerdin": ch("Hammerdin", [{"kind": "lobby", "image": "f_%d.jpg" % (T0 + 20000), "name": "Hammerdin",
                                                     "ts": T0 + 20000, "reel": "reel_s_A"}]),
                      "frostnova": ch("Frostnova", [{"kind": "lobby", "image": "f_%d.jpg" % (T0 + 4100000), "name": "Frostnova",
                                                     "ts": T0 + 4100000, "reel": "reel_s_B"}])}}


class TheGearLedgerReadsTheOneSpanSource(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="gear-span-")
        self.hist = os.path.join(self.d, "hist")
        os.makedirs(self.hist)
        self.journal = os.path.join(self.d, "sessions.jsonl")
        self.store = os.path.join(self.d, "equipped_ledger.json")
        with io.open(self.journal, "w", encoding="utf-8") as fh:
            for r in ROWS:
                fh.write(json.dumps(r) + "\n")

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def ingest(self, now, **kw):
        cs = _cs()
        r = E.ingest([self.journal], self.hist, now_ms=now, store=self.store, logins=CS.logins(cs), cs=cs, **kw)
        d, why = E.load(self.store)
        self.assertIsNotNone(d, why)
        return r, d

    @staticmethod
    def _holds(d, who, item):
        return item in json.dumps((d.get("characters") or {}).get(who) or {})

    def test_the_premise_a_login_alone_leaves_the_lobby_unread(self):
        r, d = self.ingest(T0 + 9000000, sessions=None)
        self.assertIn("Shako", (d["unattributed"].get("names") or {}), "PREMISE: a reel with no login filed its gear: %r" % d)
        self.assertTrue(self._holds(d, "Hammerdin", "Enigma"), "PREMISE: the login span did not file its gear")

    def test_a_reel_the_lobby_names_files_its_gear_under_that_character(self):
        r, d = self.ingest(T0 + 9000000)
        self.assertTrue(self._holds(d, "Hammerdin", "Shako"), "the lobby named s_A and its gear stayed unattributed: %r" % d)
        gs = [g for g in d["gameSessions"].values() if "s_A" in (g.get("reels") or [])]
        self.assertEqual([(g.get("character"), g.get("characterVia")) for g in gs], [("Hammerdin", "lobby")], gs)

    def test_a_span_two_screens_disagree_on_files_nothing(self):
        r, d = self.ingest(T0 + 9000000)
        self.assertFalse(self._holds(d, "Hammerdin", "Enigma"), "gear was filed under the login's name over the doubt")
        self.assertFalse(self._holds(d, "Frostnova", "Enigma"), "gear was filed under the newer name")
        self.assertIn("Enigma", d["unattributed"].get("names") or {}, d["unattributed"])
        g = d["gameSessions"].get("g_s_B_%d" % (T0 + 4000000)) or {}
        self.assertTrue(g.get("character") is None and "different characters" in str(g.get("why")),
                        "the login's game session does not say the doubt: %r" % g)

    def test_a_reel_filed_with_no_character_is_filed_again_once_the_map_names_it(self):
        self.ingest(T0 + 9000000, sessions=None)
        r, d = self.ingest(T0 + 9100000)
        self.assertIn("s_A", r.get("refiled") or [], r)
        self.assertTrue(self._holds(d, "Hammerdin", "Shako"))
        self.assertNotIn("Shako", d["unattributed"].get("names") or {}, d["unattributed"])

    def test_the_ledger_has_no_fold_of_its_own(self):
        src = io.open(os.path.join(HERE, "equipped_ledger.py"), encoding="utf-8").read()
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        self.assertEqual(code.count("_cs.session_span_at(sessions, _sid, _ts)"), 1)
        self.assertNotIn("_merge_groups(", code, "the gear ledger folds names on its own - a second fold")


RED_PROOF = [
    {"why": "REG-2911 - the gear ledger does not ask the span source (a lobby-named reel stays unattributed)",
     "file": "equipped_ledger.py",
     "find": "            _named = lambda _sid, _ts: _cs.session_span_at(sessions, _sid, _ts)   # REG-2911 the one span source\n",
     "replace": "            _named = None\n",
     "matches": 1},
    {"why": "REG-2911 - a span the map holds UNKNOWN keeps the login's name (gear filed over the doubt)",
     "file": "equipped_ledger.py",
     "find": "                if not (isinstance(ns, dict) and (ns.get(\"character\") or ns.get(\"conflict\"))):\n",
     "replace": "                if not (isinstance(ns, dict) and ns.get(\"character\")):\n",
     "matches": 1},
    {"why": "REG-2911 - the named span does not name its game session (the chain carries nothing)",
     "file": "equipped_ledger.py",
     "find": "                if sp[\"via\"] == \"char-select\" or not cur.get(\"character\"):\n",
     "replace": "                if False:\n",
     "matches": 1},
    {"why": "REG-2911 - the map is never built from the learner's ledger",
     "file": "equipped_ledger.py",
     "find": "            sessions = _cs.session_characters(cs, reel_of=_cs.reel_of_frame(hist_dir)) if isinstance(cs, dict) else None\n",
     "replace": "            sessions = None\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
