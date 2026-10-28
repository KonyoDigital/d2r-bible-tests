# -*- coding: utf-8 -*-
"""#36 (REG-2908) - EVERY VAULT LOOK CARRIES THE CHARACTER ITS SESSION WAS ON, UNLESS THE READ NAMED ITS HOLDER.

His ruling, 2026-10-28 11:30: one logic binds a session's reads, stash cells and witnesses to the character, "so each reel
knows whose stash it filmed". Measured on the whole page in node before this was written: every look of a filed item
read holder null - the stash sweep's sighting has no holder field and the live route names a character only on a login
row - so the copy keys (_vaultSightGroups), the records' sight, the move tasks' "from" and the WAR mule's "seen in the
game" all read UNKNOWN for every look, on every PC.
Now _vaultEvidenceLooks asks _vaultLookHolder once for every reader of the looks: the read's own holder when it named one,
else the character the console says the look's session was on at the look's frame time (_sessionCharacterAt, the twin of
char_select.session_character_at, fed by /api/chars_learned's `sessions`, REG-2907); a session nothing names stays
UNKNOWN. The vault asks the console for that answer once, and repaints when it comes. Driven on the whole page
(tv/vault_page_node.py), the JS twin checked against the python rule over one map.
RED_PROOF below.
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import vault_page_node as VPN  # noqa: E402
import char_select as CS  # noqa: E402

T0 = 1792800000000
SOJ = "The Stone of Jordan"
SESSIONS = {
    "s_A": [{"from": T0 + 1000, "character": "WAR1", "via": "char-select"}],
    "s_B": [{"from": None, "character": "Konyolock", "via": "lobby"},
            {"from": T0 + 3600000 + 5000, "character": "Konyodin", "via": "char-select"}],
    "s_X": [{"from": None, "character": None, "via": None, "why": "two screens in one span named different characters"}],
}


def _look(sid, frame_ms, holder=None, x=0):
    k = {"id": sid, "frame": "f_%d" % frame_ms, "conf": 0.9, "at": "2026-10-28T08:00:00.000Z", "loc": "stash",
         "scene": "stash", "cell": {"x": x, "y": 0, "container": "stash"}}
    if holder:
        k["holder"] = holder
    return k


LOOKS = [_look("s_A", T0 + 5000, x=0),                    # WAR1's session
         _look("s_B", T0 + 3600000 + 2000, x=1),          # s_B before its login: the lobby's Konyolock
         _look("s_B", T0 + 3600000 + 9000, x=2),          # s_B after its login: Konyodin
         _look("s_C", T0 + 7200000, x=3),                 # a session nothing names: UNKNOWN
         _look("s_A", T0 + 6000, holder="MULE1", x=4)]    # the read named its holder: kept
PROV = {SOJ: {"mule": "uni-small", "source": "tv", "by": "tv", "at": "2026-10-28T08:00:00.000Z", "looks": LOOKS,
              "kind": "filing"}}
PRELUDE = ("localStorage.setItem('d2r_ownerClaim', '*');\n"
           "localStorage.setItem('d2r_owned', %s);\n" % json.dumps(json.dumps([SOJ]))
           + "localStorage.setItem('d2r_copies', %s);\n" % json.dumps(json.dumps({SOJ: 5}))
           + "localStorage.setItem('d2r_muleAssign', %s);\n" % json.dumps(json.dumps({SOJ: "uni-small"}))
           + "localStorage.setItem('d2r_vaultProv', %s);\n" % json.dumps(json.dumps(PROV))
           # count what the page asks the console (the harness's fetch never answers)
           + "window.__asked = []; (function(){ var f = window.fetch; window.fetch = function(u){ window.__asked.push(String(u)); "
             "return f ? f.apply(this, arguments) : new Promise(function(){}); }; })();\n")
QUERIES = [["s_A", T0 + 5000], ["s_A", None], ["s_B", T0 + 3600000 + 2000], ["s_B", T0 + 3600000 + 9000], ["s_B", None],
           ["s_C", T0], ["s_X", T0], ["s_A", T0]]

BODY = r"""
(function(){
var W = window, SOJ = %s, SESSIONS = %s, QUERIES = %s;
function holders(){ return W._vaultEvidenceLooks(SOJ).map(function(k){ return [k.holder, k.holderVia || null]; }); }
function groups(){ return (W._vaultSightGroups(SOJ) || []).map(function(g){ return g.holder; }); }
try { W.renderVault(); } catch (e) { OUT.renderErr = String(e && e.message || e); }
H.flush(60, 3);
OUT.before = holders();
try { W.renderVault(); W.renderVault(); } catch (e) {}
OUT.asked = window.__asked.filter(function(u){ return /\/api\/chars_learned/.test(u); }).length;
W._cbLearnedTakeForLaw({ ok: true, chars: [], sessions: SESSIONS });
OUT.after = holders();
OUT.groups = groups();
OUT.twin = QUERIES.map(function(q){ return W._sessionCharacterAt(q[0], q[1]).name; });
W._cbLearnedTakeForLaw({ ok: true, chars: [], sessions: null, sessionsWhy: 'the character-select ledger could not be read' });
OUT.unread = W._sessionCharacterAt('s_A', %d);
OUT.errors = H.errors.slice();
})();
""" % (json.dumps(SOJ), json.dumps(SESSIONS), json.dumps(QUERIES), T0 + 5000)


class ALookCarriesItsSessionsCharacter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not VPN.NODE:
            raise AssertionError("node is not on this machine - this law does not skip")
        cls.o = VPN.run(BODY, prelude=PRELUDE, timeout=300)

    def test_the_page_booted(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])
        self.assertNotIn("renderErr", self.o, self.o.get("renderErr"))
        self.assertEqual(self.o["errors"], [])

    def test_before_the_console_answers_no_look_has_a_guessed_holder(self):
        self.assertEqual(self.o["before"], [[None, None]] * 4 + [["MULE1", None]], self.o["before"])

    def test_each_look_carries_its_sessions_character_at_its_frame_time(self):
        self.assertEqual(self.o["after"], [["WAR1", "session"], ["Konyolock", "session"], ["Konyodin", "session"],
                                           [None, None], ["MULE1", None]], self.o["after"])

    def test_the_copy_keys_read_the_same_holders(self):
        self.assertEqual(self.o["groups"], ["WAR1", "Konyolock", "Konyodin", None, "MULE1"], self.o["groups"])

    def test_the_js_twin_answers_what_the_python_rule_answers(self):
        py = [CS.session_character_at(SESSIONS, q[0], q[1])[0] for q in QUERIES]
        self.assertEqual(self.o["twin"], py, "the page and the console pick different characters for one read")
        self.assertEqual(py, ["WAR1", "WAR1", "Konyolock", "Konyodin", None, None, None, None], py)

    def test_an_unread_session_map_is_unknown_and_says_why(self):
        u = self.o["unread"]
        self.assertIsNone(u.get("name"))
        self.assertIn("could not be read", u.get("why") or "")

    def test_the_vault_asks_the_console_once(self):
        self.assertEqual(self.o["asked"], 1, "the vault asked the console %r times across three paints" % self.o["asked"])


RED_PROOF = [
    {"why": "REG-2908 - a look takes no holder from its session (every look UNKNOWN again)",
     "file": "bible.html",
     "find": "    return { holder: (sc && sc.name) || null, via: (sc && sc.name) ? 'session' : null };   /* REG-2908 session holder */\n",
     "replace": "    return { holder: null, via: null };\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2908 - a read's own holder is overwritten by its session's character",
     "file": "bible.html",
     "find": "    if (own) return { holder: own, via: null };\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2908 - a login is not a boundary on the page (a read takes the session's last span)",
     "file": "bible.html",
     "find": "    spans.forEach(function(s){ if (s && (s.from == null || (typeof s.from === 'number' && s.from <= ts))) pick = s; });\n",
     "replace": "    spans.forEach(function(s){ if (s) pick = s; });\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2908 - the looks' reader does not ask (holders stay the read's own)",
     "file": "bible.html",
     "find": "      var hv = _lookHolder(k, k.id || k.session || null);\n",
     "replace": "      var hv = { holder: k.holder || k.character || null, via: null };\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2908 - the vault never asks the console for the session map",
     "file": "bible.html",
     "find": "        window.__vaultSessionsAsked = 1;\n        window._cbLearnedFetch(function(){ try { renderVault(); } catch (eRv) {} }, { quiet: true });\n",
     "replace": "        window.__vaultSessionsAsked = 1;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2908 - the vault asks on every paint",
     "file": "bible.html",
     "find": "        window.__vaultSessionsAsked = 1;\n",
     "replace": "",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
