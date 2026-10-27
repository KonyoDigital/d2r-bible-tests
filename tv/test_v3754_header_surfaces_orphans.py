# -*- coding: utf-8 -*-
"""#76 INC-1 (v3754) — THE VAULT HEADER SURFACES THE ONE-RECORD CORROBORATOR'S ORPHAN DISAGREEMENT.

The header's "filed to mules" figure is derived by SUBTRACTION (pool - unsorted - carried), which blindly
counts every leftover owned name as filed — INCLUDING a name whose assigned mule does not exist. That
over-count IS his reported "unsorted dock and the mules disagree" (symptom a of #76). _vaultRecords()
resolves each owned name's TRUE home and flags those with no real home as `orphans`; _vaultRecordsHeader()
(built v3747/v3748, REG-2257/2258, but UNCONSUMED until now) returns that count, or null = UNKNOWN when the
dock/mule map would not read.

This law drives the SHIPPED renderer window._vaultPopHtml and asserts it surfaces that count read-only:
  · a number, with the word "disagree", when there is a REAL disagreement (orphans > 0)
  · NOTHING when they agree (orphans 0 or absent)
  · UNKNOWN — never a false 0 — when orphans is null (the map would not read)
  · NO claim at all when the mule map itself is unread (filed === null short-circuits first)

Read-only: _vaultPopHtml writes no store and re-routes nothing (INC-1 is a corroborator, not phase-2's
per-copy routing). A missing node raises — this law does not skip. RED_PROOF below.
[[the-unjoined-end]] [[unknown-stays-unknown]] [[heart-first]]
"""
import json
import os
import re
import shutil
import subprocess
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

BIBLE = os.path.join(HERE, "..", "bible.html")
NODE = os.environ.get("NODE") or shutil.which("node")


def _pop_fn(src):
    m = re.search(r"window\._vaultPopHtml = function\(p\)\{[\s\S]*?\n  \};", src)
    if not m:
        raise AssertionError("could not extract window._vaultPopHtml from bible.html")
    return m.group(0)


class TestV3754HeaderSurfacesOrphans(unittest.TestCase):
    def test_the_header_surfaces_the_orphan_disagreement(self):
        if not NODE:
            raise AssertionError("node is not on this machine — this law does not skip")
        with open(BIBLE, encoding="utf-8") as f:
            src = f.read()
        prog = "var window = globalThis;\n" + _pop_fn(src) + r"""
var base = { owned:10, shared:0, filed:5, carried:0, loose:3, sp:0 };
function with_(o){ var r = {}; for (var k in base) r[k] = base[k]; for (var k2 in o) r[k2] = o[k2]; return r; }
var out = {
  orphan2:   window._vaultPopHtml(with_({ orphans:2 })),
  zero:      window._vaultPopHtml(with_({ orphans:0 })),
  absent:    window._vaultPopHtml(with_({})),
  unknown:   window._vaultPopHtml(with_({ orphans:null })),
  mapUnread: window._vaultPopHtml({ owned:10, filed:null }),
  carriedUnkOrph: window._vaultPopHtml(with_({ carried:null, orphans:2 })),
  carriedUnkUnk:  window._vaultPopHtml(with_({ carried:null, orphans:null })),
  allNoHome: window._vaultPopHtml(with_({ orphans:5, orphansNoHome:5 })),
  mixed:     window._vaultPopHtml(with_({ orphans:3, orphansNoHome:1 }))
};
process.stdout.write(JSON.stringify(out));
"""
        p = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, (p.stderr or p.stdout)[-2000:])
        o = json.loads(p.stdout)
        # a REAL disagreement is surfaced, with its count
        self.assertIn("disagree", o["orphan2"], "a real orphan disagreement must be surfaced")
        self.assertIn("<b>2</b>", o["orphan2"], "the orphan count is shown")
        # orphans:0 is MEASURED agreement -> stays silent (never a false UNKNOWN); the == null fix keeps 0 out of it
        self.assertNotIn("disagree", o["zero"], "no disagreement line when orphans == 0")
        self.assertNotIn("agreement", o["zero"], "orphans:0 is measured agreement -> silent, never a false UNKNOWN")
        # v3757 (#231 eye on v3756): the SOLE caller passes orphans:undefined when _vaultRecords FAILS (_rh76 null).
        # == null catches undefined too, so a records failure reads agreement UNKNOWN — never a silent false-agree.
        self.assertNotIn("disagree", o["absent"], "records-failed (orphans undefined) is not a disagreement")
        self.assertIn("agreement", o["absent"], "orphans undefined (records failed) must read agreement UNKNOWN, not silent")
        self.assertIn("UNKNOWN", o["absent"])
        # UNKNOWN, never a false 0
        self.assertIn("UNKNOWN", o["unknown"], "orphans null must read UNKNOWN, never a false 0")
        self.assertIn("agreement", o["unknown"])
        self.assertNotIn("disagree", o["unknown"], "UNKNOWN is not a disagreement claim")
        # the mule map unread short-circuits before any orphan claim
        self.assertNotIn("disagree", o["mapUnread"], "mule map unread -> no orphan claim")
        self.assertNotIn("agreement", o["mapUnread"])
        # v3756 / REG-2268 (the #231 eye on v3755): orphans must surface even when CARRIED is UNKNOWN. The orphan
        # check now sits ABOVE the carried-null early return, derived from _vaultRecordsHeader (dock+mule map), not
        # the carried strip — so a readable mule map + an unread carried strip still shows the disagreement.
        self.assertIn("disagree", o["carriedUnkOrph"], "orphans must surface even when carried is UNKNOWN (was dropped pre-v3756)")
        self.assertIn("UNKNOWN", o["carriedUnkUnk"], "orphans null + carried UNKNOWN -> agreement UNKNOWN, never dropped")
        self.assertIn("agreement", o["carriedUnkUnk"])
        # #204 (GrokBot, 2026-10-27) - an orphan with NO mule at all is "no home", never "filed to a mule the board can't
        # find": 5 of the ALT's and 5 of the Mac's had mule=null. Split when known; unknown split keeps the old line.
        self.assertIn("<b>5</b> with no home", o["allNoHome"], o["allNoHome"])
        self.assertNotIn("can\u2019t find", o["allNoHome"], "a never-filed item was called filed to a lost mule")
        self.assertIn("<b>1</b> with no home", o["mixed"], o["mixed"])
        self.assertIn("<b>2</b> filed to a mule the board can\u2019t find", o["mixed"], o["mixed"])
        self.assertIn("<b>2</b> filed to a mule the board can\u2019t find", o["orphan2"], "no split known: the old line stays")


RED_PROOF = [
    {
        "why": "#76 INC-1 - removing the orphan line makes the unsorted/mules disagreement (symptom a) invisible again",
        "file": "bible.html",
        "find": "      if (_lost > 0) bits.push('\\u26a0 ' + n(_lost) + ' filed to a mule the board can\\u2019t find <i>(unsorted and the mules disagree)</i>');\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#76 v3757 (#231 eye on v3756) - reverting == null to === null makes orphans:undefined (records "
               "FAILED, the sole caller's value when _rh76 is null) render SILENT instead of agreement UNKNOWN - a "
               "records failure reading as a false agree",
        "file": "bible.html",
        "find": "if (p.orphans == null) bits.push('mule/unsorted agreement <b>UNKNOWN</b>');",
        "replace": "if (p.orphans === null) bits.push('mule/unsorted agreement <b>UNKNOWN</b>');",
        "matches": 1,
    },
    {
        "why": "#204 - a never-filed orphan is called 'filed to a mule the board can't find' again",
        "file": "bible.html",
        "find": "      var _lost = (_noHome == null) ? p.orphans : (p.orphans - _noHome);\n",
        "replace": "      var _lost = p.orphans;\n",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main()
