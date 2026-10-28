# -*- coding: utf-8 -*-
"""REG-2894 (intake design P2, #230 c6473846977) - EVERY RECORD SAYS WHEN IT WAS LAST SEEN, BY CAPTURE TIME.

His design: "Every record shows 'last seen <date>'. With no newer full look, an old read can still place an item, but it
says how old it is. Old is never shown as now."

FIND names where each item sits and said nothing about when it was last seen, so a placement read on Oct 6 looked as
current as one read today. Each FIND row now carries "last seen <date>" - the newest capture time the item's witness row
records - through P1's ONE helper, _vaultSeenTimes (REG-2816: a receipt's measured read time and every look's `at`; a
filing row's own `at` is when it was FILED, never a sighting). The helper now also reads the receipt a filing row keeps
(`ownedBy`), so a photo filed by his hand stays dated by when the picture was taken. An item with no capture time says
"no capture time" - never today's date; a witness store that will not read says UNKNOWN. The copy readout reads the same
helper, so the two can never disagree.

Whole page in node (vault_page_node), fixtures only. RED_PROOF below.
"""
import json
import os
import sys
import time
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

T = 1761609600000                 # 2025-10-28T00:00:00Z
ISO = "2025-10-28T00:00:00.000Z"
T2, T3 = T - 2 * 86400000, T + 3600000


def _iso(ms):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ms / 1000.0)) + ".000Z"


PROV = {
    # a receipt measured at its capture time
    "Harlequin Crest (Shako)": {"kind": "owned", "source": "folder-photo", "by": "vault intake", "ts": T, "tsMeasured": True,
                        "at": ISO, "looks": [{"id": "photo:a.png", "frame": "a.png", "at": ISO}]},
    # a receipt the door could not date - its clock is the door's, unmeasured
    "The Stone of Jordan": {"kind": "owned", "source": "folder-photo", "by": "vault intake", "ts": None, "tsMeasured": False,
                        "at": None, "recordedAt": _iso(T3), "looks": [{"id": "photo:b.png", "frame": "b.png", "at": None}]},
    # a filing row: its own `at` is when it was filed; its looks and the receipt it replaced say when it was seen
    "Magefist": {"mule": "uni-armor", "source": "stash", "at": _iso(T3 + 86400000), "by": "reader",
                 "looks": [{"id": "s1", "frame": "f1", "at": _iso(T2)}, {"id": "s2", "frame": "f2"}],
                 "ownedBy": {"kind": "owned", "source": "tv-live", "ts": T3, "tsMeasured": True, "at": _iso(T3), "looks": []}},
}
SEED = ("localStorage.setItem('d2r_ownerClaim', '*');"
        "localStorage.setItem('d2r_owned', %s);"
        "localStorage.setItem('d2r_muleAssign', %s);"
        "localStorage.setItem('d2r_vaultProv', %s);"
        % (json.dumps(json.dumps(sorted(PROV))),
           json.dumps(json.dumps({"Harlequin Crest (Shako)": "uni-armor", "The Stone of Jordan": "uni-small", "Magefist": "uni-armor"})),
           json.dumps(json.dumps(PROV))))

BODY = r"""
var W = window;
OUT.ls = { hc: W._vaultLastSeen('Harlequin Crest (Shako)'), soj: W._vaultLastSeen('The Stone of Jordan'), mf: W._vaultLastSeen('Magefist'),
           none: W._vaultLastSeen('Nagelring') };
function findRow(q){ W.vaultFind(q); var r = document.getElementById('vault-find-results'); return r ? r.innerHTML : null; }
OUT.findHc = findRow('harlequin'); OUT.findSoj = findRow('stone of jordan'); OUT.findMf = findRow('magefist');
var a = null; try { a = W._vaultCopyAudit ? W._vaultCopyAudit() : null; } catch (e) { a = { err: String(e) }; }
OUT.audit = a && a.rows ? a.rows.filter(function(r){ return r.name === 'Magefist'; }).map(function(r){ return r.seenLast; }) : a;
"""


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class EveryRecordSaysWhenItWasLastSeen(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run(BODY, prelude=SEED, timeout=300)
        cls.bad = VPN.run("OUT.ls = window._vaultLastSeen('Harlequin Crest (Shako)');",
                          prelude="localStorage.setItem('d2r_ownerClaim', '*');localStorage.setItem('d2r_vaultProv', '{not json');",
                          timeout=300)

    def test_the_newest_capture_time_is_the_last_seen(self):
        ls = self.o["ls"]
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])
        self.assertEqual(ls["hc"], {"ms": T})
        self.assertEqual(ls["mf"], {"ms": T3}, "a filing row lost the capture time of the receipt it replaced: %r" % ls["mf"])

    def test_no_capture_time_is_said_never_dated_now(self):
        ls = self.o["ls"]
        self.assertEqual(ls["soj"], {"ms": None}, "an undated receipt was given a last-seen time: %r" % ls["soj"])
        self.assertEqual(ls["none"], {"ms": None})
        self.assertEqual(self.bad["ls"], {"ms": None, "unknown": True}, "an unreadable witness store read as 'no capture time'")

    def test_find_names_it_on_every_row(self):
        self.assertIn('data-seen="%s"' % ISO, self.o["findHc"] or "")
        self.assertIn("last seen 2025-10-28", self.o["findHc"] or "")
        self.assertIn("last seen 2025-10-28", self.o["findMf"] or "", "Magefist's row does not carry its last capture")
        self.assertIn('data-seen="none"', self.o["findSoj"] or "")
        self.assertIn("no capture time", self.o["findSoj"] or "")
        today = time.strftime("%Y-%m-%d", time.gmtime())
        self.assertNotIn("last seen " + today, self.o["findSoj"] or "", "an undated item was shown as seen today")

    def test_the_copy_readout_reads_the_same_helper(self):
        self.assertEqual(self.o["audit"], [T3], "the copy readout and FIND disagree about when Magefist was last seen: %r" % self.o["audit"])


RED_PROOF = [
    {"why": "REG-2894 - the FIND row stops saying when the item was last seen",
     "file": "bible.html",
     "find": "+_navHtml+_vaultSeenSpan(n)+'</div>';",
     "replace": "+_navHtml+'</div>';",
     "matches": 1, "needs": "node"},
    {"why": "REG-2894 - an item with no capture time is shown as seen now",
     "file": "bible.html",
     "find": "      if (ls.ms == null) return '<span class=\"vfr-seen\" data-seen=\"none\"",
     "replace": "      if (ls.ms == null) ls = { ms: Date.now() };\n      if (false) return '<span class=\"vfr-seen\" data-seen=\"none\"",
     "matches": 1, "needs": "node"},
    {"why": "REG-2894 - a filing row forgets the capture time of the receipt it replaced",
     "file": "bible.html",
     "find": "    if (row.ownedBy && typeof row.ownedBy === 'object' && row.ownedBy !== row) t = t.concat(_vaultSeenTimes(row.ownedBy));\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2894 - an unreadable witness store reads as 'no capture time'",
     "file": "bible.html",
     "find": "    if (!all || typeof all !== 'object') return { ms: null, unknown: true };\n",
     "replace": "    if (!all || typeof all !== 'object') return { ms: null };\n",
     "matches": 1, "needs": "node"},
]


if __name__ == "__main__":
    unittest.main()
