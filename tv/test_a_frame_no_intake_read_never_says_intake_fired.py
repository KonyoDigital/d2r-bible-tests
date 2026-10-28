# -*- coding: utf-8 -*-
"""REG-2960 (#55, GrokBot ticks 416-421) - "MISS - INTAKE FIRED BUT READ NOTHING" NEEDS AN INTAKE THAT FIRED.

GrokBot, on Sessions 30, 41, 46, 48 and 53: frames tagged "STASH tab · 0 counted ⚠ MISS - intake fired but read nothing",
a "Press Any Key" title screen among them. The dossier (_beat_dossier) gave a frame the router called a stash tab the MISS
status whenever that tab had no real read anywhere in the session - with an intake receipt for the tab, or with none at
all - and the Theatre printed "intake fired" for both. Measured on the fixtures below before the fix: a reel with NO
intake receipt for the gems tab reported kind "miss", counted 0, and the line said intake fired.

Now a miss needs an intake receipt for that tab this session (it fired and read nothing - unchanged); with none the frame
is UNREAD: counted UNKNOWN (None, never 0), the line says "not read - no intake ran on this tab this session", the flag
says NOT READ, and the legend names it. A real read and a superseded zero are unchanged.

This does not explain why Session 46's legible Flame Rift tooltip was never read - that frame is his footage and was not
opened here. It removes the sentence that claimed an intake ran on frames where none did.

Fixtures only: journal rows built here, the shipped dossier builder and the shipped Theatre lines cut and run in node.
RED_PROOF below.
"""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
from cb_node_harness import NODE  # noqa: E402
import control_app as ca  # noqa: E402

UI = os.path.join(HERE, "control_ui.html")
CUTS = [("  function thReadStatus(b, full){", "\n  // v946 — forensic flags"),
        ("  function thForensicFlags(b){", "\n  // v944.7 (Konyo: \"it says FAILED")]


def _status(rows, beat):
    return ca._beat_dossier(ca._build_dossier_maps(rows), beat)["readStatus"]


GEMS0 = {"lane": "intake", "ts": 5000, "intake": {"tab": "gems", "kind": "tally", "ok": True, "total": 0, "counts": {}}}
RUNES = {"lane": "intake", "ts": 1000, "intake": {"tab": "runes", "kind": "tally", "ok": True, "total": 12,
                                                  "counts": {"El": 12}}}


def _beat(label):
    return {"frameId": "reel_fx/f_5000", "captureTs": 5000, "footage": True, "label": label}


def _ui(statuses):
    if NODE is None:
        raise AssertionError("node is not on this machine - this law does not skip")
    with open(UI, encoding="utf-8") as f:
        s = f.read()
    code = []
    for a, b in CUTS:
        if s.count(a) != 1:
            raise AssertionError("anchor %r matched %d times - re-point this law" % (a, s.count(a)))
        i = s.index(a)
        code.append(s[i:s.index(b, i)])
    prog = ("function esc(x){ return String(x); } function thTabIcon(){ return '#'; } function thTallyChips(){ return ''; }\n"
            + "\n".join(code)
            + "\nvar S = %s; console.log(JSON.stringify(S.map(function(rs){ var b = { dossier: { readStatus: rs } };"
              " return [thReadStatus(b, false), thForensicFlags(b)]; })));" % json.dumps(statuses))
    r = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=60)
    if r.returncode != 0:
        raise AssertionError("the shipped Theatre lines did not run in node: %s" % (r.stderr or r.stdout)[-1200:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class AFrameNoIntakeReadNeverSaysIntakeFired(unittest.TestCase):

    def test_no_receipt_for_the_tab_is_unread_never_a_miss(self):
        rs = _status([RUNES], _beat("stash-gems"))
        self.assertEqual(rs["kind"], "unread", "a tab no intake ever read was called a miss: %r" % rs)
        self.assertIsNone(rs["counted"], "nobody counted, so the count is UNKNOWN, not 0: %r" % rs)
        self.assertEqual(rs["tab"], "gems")

    def test_a_stash_frame_with_no_tab_and_no_receipt_is_unread(self):
        rs = _status([], _beat("stash"))
        self.assertEqual((rs["kind"], rs["counted"]), ("unread", None), rs)

    def test_a_receipt_that_read_nothing_is_still_a_miss_and_a_real_read_is_a_read(self):
        rs = _status([RUNES, GEMS0], _beat("stash-gems"))
        self.assertEqual((rs["kind"], rs["counted"]), ("miss", 0), "intake fired on gems and read nothing: %r" % rs)
        rr = _status([RUNES, GEMS0], _beat("stash-runes"))
        self.assertEqual((rr["kind"], rr["counted"]), ("read", 12), rr)

    def test_the_theatre_says_not_read_and_never_that_intake_fired(self):
        unread, miss = _ui([{"kind": "unread", "tab": "gems", "counted": None},
                            {"kind": "miss", "tab": "gems", "counted": 0}])
        self.assertIn("not read", unread[0])
        self.assertIn("no intake ran on this tab this session", unread[0])
        self.assertNotIn("intake fired", unread[0], "an unread frame still claims an intake fired: %r" % unread[0])
        self.assertNotIn("0 counted", unread[0], "an unread frame prints a count nobody made: %r" % unread[0])
        self.assertIn("NOT READ", unread[1])
        self.assertNotIn(">MISS<", unread[1])
        self.assertIn("intake fired but read nothing", miss[0], "a real miss lost its words")
        self.assertIn(">MISS<", miss[1])

    def test_the_legend_names_it(self):
        with open(UI, encoding="utf-8") as f:
            s = f.read()
        self.assertEqual(s.count("'not read', 'the frame shows a stash tab, and no intake ran on that tab this session"), 1)


RED_PROOF = [
    {"why": "REG-2960 - every stash frame with no real read is a miss again, receipt or none",
     "file": "tv/control_app.py",
     "find": "        elif (maps.get(\"tab_receipts\") or {}).get(_tab.lower()):\n",
     "replace": "        elif True:\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2960 - an unread frame counts 0 instead of UNKNOWN",
     "file": "tv/control_app.py",
     "find": "            read_status = {\"kind\": \"unread\", \"tab\": _tab, \"counted\": None}\n",
     "replace": "            read_status = {\"kind\": \"unread\", \"tab\": _tab, \"counted\": 0}\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2960 - the Theatre line says intake fired on an unread frame",
     "file": "tv/control_ui.html",
     "find": "' tab · <b>not read</b> ⚠ no intake ran on this tab this session</span>';",
     "replace": "' tab · <b>0 counted</b> ⚠ MISS — intake fired but read nothing</span>';",
     "matches": 1, "needs": "node"},
    {"why": "REG-2960 - an unread frame carries no flag",
     "file": "tv/control_ui.html",
     "find": "    if (rs && rs.kind === 'unread') flags.push(",
     "replace": "    if (false) flags.push(",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main()
