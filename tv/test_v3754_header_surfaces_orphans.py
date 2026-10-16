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
  mapUnread: window._vaultPopHtml({ owned:10, filed:null })
};
process.stdout.write(JSON.stringify(out));
"""
        p = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, (p.stderr or p.stdout)[-2000:])
        o = json.loads(p.stdout)
        # a REAL disagreement is surfaced, with its count
        self.assertIn("disagree", o["orphan2"], "a real orphan disagreement must be surfaced")
        self.assertIn("<b>2</b>", o["orphan2"], "the orphan count is shown")
        # nothing claimed when they agree
        self.assertNotIn("disagree", o["zero"], "no disagreement line when orphans == 0")
        self.assertNotIn("disagree", o["absent"], "no disagreement line when the field is absent")
        # UNKNOWN, never a false 0
        self.assertIn("UNKNOWN", o["unknown"], "orphans null must read UNKNOWN, never a false 0")
        self.assertIn("agreement", o["unknown"])
        self.assertNotIn("disagree", o["unknown"], "UNKNOWN is not a disagreement claim")
        # the mule map unread short-circuits before any orphan claim
        self.assertNotIn("disagree", o["mapUnread"], "mule map unread -> no orphan claim")
        self.assertNotIn("agreement", o["mapUnread"])


RED_PROOF = [
    {
        "why": "#76 INC-1 - removing the orphan line makes the unsorted/mules disagreement (symptom a) invisible again",
        "file": "bible.html",
        "find": "    else if (p.orphans > 0) bits.push('\\u26a0 ' + n(p.orphans) + ' filed to a mule the board can\\u2019t find <i>(unsorted and the mules disagree)</i>');\n",
        "replace": "",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main()
