# -*- coding: utf-8 -*-
"""Intake design P1 (REG-2816, his ruling Q1-Q4, #230 6473846977) - THE COPY READOUT SAYS WHERE EACH LOCKER ROW'S COPIES CAME
FROM AND WHEN IT WAS LAST SEEN.

The design's first phase is the instrument: before any behaviour changes, the copy readout (window._vaultCopyAudit,
REG-2760/2778/2779) counts the copies by source and dates the last-seen, so every later phase can be checked against it.
MEASURED on his store 2026-10-28 (a read-only copy, deleted after): 22 provenance rows - 16 receipts (source aic-judge 11,
kai-register 5; 9 carry a measured read time, and their 12 looks an `at`) and 6 filing rows (kept/evidence 4, hand/hand 1,
stash/kai-register 1; their 20 looks carry no time); 13 persisted records, each carrying its name's one source. The store
keeps ONE source per name, not per copy, and capture times only where a read recorded one.

So per locker row: `sources` = its records under the class its provenance row records (hand / auto / sweep / photo /
chronicle - bible.html _ownedProvSourceClass, one vocabulary beside _ownedProvSourceSay - else unknown, never a guess),
`sourceRaw` = the recorded source/by, `seenFirst` / `seenLast` = the oldest and newest capture time that row records (a
measured receipt time, a look's `at`), null when none is. Overall: `bySource`, `lastSeenOldest` / `lastSeenNewest`, and
`lastSeenNone` (rows with no capture time, counted apart). A filing's own time is when it was filed, and a receipt with no
measured flag cannot be told from the wall clock: neither is a capture time. The console banks the new fields shaped.

Driven: the board's half on the whole page in node (vault_page_node, fixture stores), the console's half on control_app.
RED_PROOF below.
"""
import datetime
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

T = 1793000000000   # 2026-10-26


def _iso(ms):
    return datetime.datetime.utcfromtimestamp(ms / 1000).strftime("%Y-%m-%dT%H:%M:%S.000Z")


PROV = {
    # the live reader on frames: a measured read time and two looks with their own times
    "Griswold's Edge": {"kind": "owned", "source": "kai-register", "by": "tvVaultRegister", "ts": T + 1000, "tsMeasured": True,
                        "at": _iso(T + 1000), "looks": [{"id": "s_1", "frame": "1_1", "at": _iso(T - 86400000)},
                                                        {"id": "s_2", "frame": "2_2", "at": _iso(T + 5000)}]},
    # his hand: a filing row - its `at` is when he filed it, not a sighting
    "Lightsabre": {"source": "hand", "by": "hand", "at": _iso(T + 9000), "looks": [], "sessions": []},
    # the reset rebuild from the sweep's evidence: looks with no time
    "War Traveler": {"source": "kept", "by": "evidence", "at": _iso(T + 9000),
                        "looks": [{"id": "s_3", "frame": "3_3", "holder": "Mule", "cell": "stash:c0r0"}]},
    # a receipt written before tsMeasured: its ts cannot be told from the wall clock
    "The Oculus": {"kind": "owned", "source": "aic-judge", "by": "aicJudgeApply (keep)", "ts": T + 7000, "looks": []},
    # a folder photo, measured
    "Arachnid Mesh": {"kind": "owned", "source": "folder-photo", "by": "vault intake", "ts": T + 3000, "tsMeasured": True,
                      "looks": []},
    # a door this table does not name
    "Andariel's Visage": {"kind": "owned", "source": "mystery-door", "by": "someone", "looks": []},
    # "Nagelring" has no provenance row at all
}
ASSIGN = {"Griswold's Edge": "uni-weap", "Lightsabre": "uni-weap", "War Traveler": "uni-armor", "The Oculus": "uni-armor",
          "Arachnid Mesh": "uni-armor", "Andariel's Visage": "uni-armor", "Nagelring": "uni-small"}

PRELUDE = r"""
localStorage.setItem('d2r_ownerClaim', '*');
localStorage.setItem('d2r_owned', JSON.stringify(%s));
localStorage.setItem('d2r_copies', JSON.stringify({"Griswold's Edge": 3}));
localStorage.setItem('d2r_muleAssign', JSON.stringify(%s));
localStorage.setItem('d2r_vaultProv', JSON.stringify(%s));
""" % (json.dumps(sorted(ASSIGN)), json.dumps(ASSIGN), json.dumps(PROV))

BODY = r"""
(function(){
try { window.renderVault(); } catch (e) {}
H.flush(60, 3);
try { OUT.a = window._vaultCopyAudit(); } catch (e) { OUT.err = String(e && e.message || e); }
var C = window._ownedProvSourceClass;
OUT.cls = [C('hand', 'hand'), C('manual'), C('aic-judge', 'x'), C('kai-register'), C('stash', 'kai-register'),
           C('stash', 'evidence'), C('kept', 'evidence'), C('vault-sweep'), C('folder-photo'), C('intake-read'),
           C('chronicle-sweep'), C('ledger-restore', 'the ledger restore'), C(null, null), C('stash', 'nobody')];
})();
"""


def _row(a, name):
    return next((r for r in (a or {}).get("rows") or [] if r.get("name") == name), None)


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - the board's half is UNMEASURED here, never a pass")
class TheBoardSaysWhereCopiesCameFrom(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run(BODY, prelude=PRELUDE, timeout=300)
        cls.a = cls.o.get("a") or {}

    def test_the_page_booted(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])
        self.assertNotIn("err", self.o, self.o.get("err"))
        self.assertTrue(self.a.get("ok"), self.a)

    def test_the_source_classes_read_only_what_is_recorded(self):
        self.assertEqual(self.o["cls"], ["hand", "hand", "auto", "auto", "auto", "sweep", "sweep", "sweep", "photo", "photo",
                                         "chronicle", "unknown", "unknown", "unknown"])

    def test_each_row_says_its_source_and_its_raw_value(self):
        want = {"Griswold's Edge": ({"auto": 3}, "kai-register/tvVaultRegister"),
                "Lightsabre": ({"hand": 1}, "hand/hand"),
                "War Traveler": ({"sweep": 1}, "kept/evidence"),
                "The Oculus": ({"auto": 1}, "aic-judge/aicJudgeApply (keep)"),
                "Arachnid Mesh": ({"photo": 1}, "folder-photo/vault intake"),
                "Andariel's Visage": ({"unknown": 1}, "mystery-door/someone"),
                "Nagelring": ({"unknown": 1}, None)}
        for name, (src, raw) in want.items():
            r = _row(self.a, name)
            self.assertIsNotNone(r, "%s is not a readout row: %r" % (name, self.a.get("rows")))
            self.assertEqual((r.get("sources"), r.get("sourceRaw")), (src, raw), "%s: %r" % (name, r))

    def test_last_seen_is_a_recorded_capture_time_or_null(self):
        g = _row(self.a, "Griswold's Edge")
        self.assertEqual((g["seenFirst"], g["seenLast"]), (T - 86400000, T + 5000), g)
        self.assertEqual(_row(self.a, "Arachnid Mesh")["seenLast"], T + 3000)
        for name in ("Lightsabre", "War Traveler", "The Oculus", "Andariel's Visage", "Nagelring"):
            r = _row(self.a, name)
            self.assertEqual((r["seenFirst"], r["seenLast"]), (None, None),
                             "%s was dated by a time that is not a capture (a filing's own time, an unmeasured ts): %r" % (name, r))

    def test_overall_by_source_and_the_last_seen_span(self):
        self.assertEqual(self.a.get("bySource"), {"auto": 4, "hand": 1, "sweep": 1, "photo": 1, "unknown": 2}, self.a)
        self.assertEqual((self.a.get("lastSeenOldest"), self.a.get("lastSeenNewest"), self.a.get("lastSeenNone")),
                         (T + 3000, T + 5000, 5), self.a)


class TheConsoleBanksTheNewFieldsShaped(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import control_app as ca
        cls.ca = ca

    def setUp(self):
        self.keep = dict(self.ca._COPY_AUDIT)
        self.ca._COPY_AUDIT.update(audit=None, receivedAt=None, who=None, refused=None)

    def tearDown(self):
        self.ca._COPY_AUDIT.clear()
        self.ca._COPY_AUDIT.update(self.keep)

    def test_sources_and_times_are_banked_shaped(self):
        body = {"copyAudit": {"ok": True, "at": T, "rows": [
            {"name": "Shako", "mule": "uni-armor", "records": 2, "sources": {"auto": 2, "evil": 9, "hand": -1, "sweep": True},
             "sourceRaw": "x" * 90, "seenFirst": T - 5, "seenLast": True},
            {"name": "Lightsabre", "mule": "uni-weap", "records": 1, "sources": "hand", "seenFirst": None}],
            "bySource": {"auto": 2, "photo": 1.5, "<script>": 1}, "lastSeenOldest": T - 5, "lastSeenNewest": "soon",
            "lastSeenNone": 1}}
        saved, why = self.ca.accept_handed_copy_audit(body, {"p": "main"}, now_ms=T + 60000)
        self.assertEqual((saved, why), (True, None))
        a = self.ca.copy_audit_payload(now_ms=T + 61000)["audit"]
        s, lsb = a["rows"][0], a["rows"][1]
        self.assertEqual(s["sources"], {"auto": 2, "hand": None, "sweep": None}, "a class outside the six, or a non-count, was kept")
        self.assertEqual(len(s["sourceRaw"]), 48)
        self.assertEqual((s["seenFirst"], s["seenLast"]), (T - 5, None))
        self.assertEqual((lsb["sources"], lsb["sourceRaw"], lsb["seenFirst"]), (None, None, None), "UNKNOWN became a value")
        self.assertEqual(a["bySource"], {"auto": 2, "photo": None})
        self.assertEqual((a["lastSeenOldest"], a["lastSeenNewest"], a["lastSeenNone"]), (T - 5, None, 1))


RED_PROOF = [
    {"why": "REG-2816 - a filing's own time (when it was filed) is read as when the item was last seen",
     "file": "bible.html",
     "find": "    if (row.kind === 'owned' && row.tsMeasured === true && typeof row.ts === 'number' && row.ts > 0) t.push(row.ts);\n",
     "replace": "    if (typeof row.ts === 'number' && row.ts > 0) t.push(row.ts);\n    if (typeof row.at === 'string' && Date.parse(row.at) > 0) t.push(Date.parse(row.at));\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2816 - a filing row's lane ('stash', 'kept') is never read past to who filed it (its `by`)",
     "file": "bible.html",
     "find": "    return Object.prototype.hasOwnProperty.call(_SRC_CLASS, b) ? _SRC_CLASS[b] : 'unknown';\n",
     "replace": "    return 'unknown';\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2816 - a door the table does not name is guessed as hand",
     "file": "bible.html",
     "find": "    return Object.prototype.hasOwnProperty.call(_SRC_CLASS, b) ? _SRC_CLASS[b] : 'unknown';\n",
     "replace": "    return Object.prototype.hasOwnProperty.call(_SRC_CLASS, b) ? _SRC_CLASS[b] : 'hand';\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2816 - a row with no capture time is dated as now",
     "file": "bible.html",
     "find": "          if (ts.length) { seenFirst = Math.min.apply(null, ts); seenLast = Math.max.apply(null, ts); }\n",
     "replace": "          if (!ts.length) ts = [Date.now()]; seenFirst = Math.min.apply(null, ts); seenLast = Math.max.apply(null, ts);\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2816 - the console banks a source class the board's vocabulary does not have",
     "file": "tv/control_app.py",
     "find": "    return {k: _ca_count(n) for k, n in v.items() if k in COPY_AUDIT_SOURCES}\n",
     "replace": "    return {k: _ca_count(n) for k, n in v.items()}\n",
     "matches": 1},
    {"why": "REG-2816 - the console drops the rows' last-seen times",
     "file": "tv/control_app.py",
     "find": "                       \"seenFirst\": _ca_count(r.get(\"seenFirst\")), \"seenLast\": _ca_count(r.get(\"seenLast\"))})",
     "replace": "                       \"seenFirst\": None, \"seenLast\": None})",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
