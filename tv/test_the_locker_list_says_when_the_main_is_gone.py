# -*- coding: utf-8 -*-
"""#41 rank 20 review (REG-1554, 2026-09-30) — THE LOCKER'S CHARACTER LIST SAYS WHEN THE MAIN IS GONE.

The skeptic pass over rank 20 (REG-1534): the Characters room learned to say a dangling MAIN (a d2r_cbMain naming
no saved build) and its reader, window._charsList, learned to carry `mainDangling` "so a room asking here can say
UNKNOWN instead of 'no MAIN'". MEASURED on the branch: the ONE room that asks — the mule window's locker list
(_mpBindChars, #253) — copied `rows` and never read `mainDangling`. So under a dangling MAIN the list marked no row
★ MAIN and said nothing, exactly like no MAIN set: the defect rank 20 named, standing in the second room, behind a
field that was written and never read. [[the-unjoined-end]]

WHAT THIS LAW DRIVES, in the SHIPPED mule window + the Characters room's own reader (the edit-panel law's stand-in,
one copy — never re-typed here):
  · A DANGLING MAIN IS SAID: the open list carries a note (data-state="main-dangling") naming the id and calling the
    MAIN UNKNOWN; no row wears ★ MAIN; the rows still list every build and a bind still works.
  · THE TWO HONEST STATES STAY QUIET: a MAIN that names a build wears ★ MAIN and draws no note; no MAIN at all draws
    no note and marks nothing.
  · THE READER'S WORD IS CARRIED, NOT RE-DERIVED: _mpBindChars().mainDangling is what window._charsList said.
RED_PROOF below.
"""
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable; enable()

from test_the_edit_panel_shows_the_base_and_the_locker_binds_his_character import NODE, _bind, _store   # one harness

NOTE_RX = r'<div class="mp-bind-none[^"]*" data-state="main-dangling"[^>]*>([\s\S]*?)</div>'

SCENARIO = r"""
  window.openMuleCard('uni-armor');
  press(ctl().onclick);
  out.opened = !!listHtml(); out.list = listHtml() || '';
  var m = /__NOTE__/.exec(out.list);
  out.note = m ? unesc(m[1].replace(/<[^>]+>/g, '')).replace(/\s+/g, ' ').trim() : null;
  out.ids = opts().filter(function(o){ return o.src === 'build'; }).map(function(o){ return o.id; });
  out.mains = opts().filter(function(o){ return /★ MAIN/.test(o.text); }).map(function(o){ return o.id; });
  out.reader = window._charsList();
  out.bound = pick('build', 'b2');
  out.roster = JSON.parse(STORE['d2r_muleRoster'] || 'null');
""".replace("__NOTE__", NOTE_RX.replace("/", r"\/"))


def _drive(main):
    return _bind(SCENARIO, store=_store(main=main))


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class TheLockerListSaysWhenTheMainIsGone(unittest.TestCase):

    def test_a_dangling_main_is_said_above_the_rows_and_marks_none_of_them(self):
        out = _drive("bGONE")
        self.assertTrue(out["opened"], "the list did not open — the case measures nothing")
        self.assertEqual("bGONE", out["reader"]["mainDangling"], "the Characters room's reader does not say the MAIN dangles")
        self.assertIsNotNone(out["note"], "a dangling MAIN reads exactly like no MAIN in the locker list: %r" % out["list"][:300])
        self.assertIn("bGONE", out["note"], "the note does not name the dangling id")
        self.assertIn("UNKNOWN", out["note"])
        self.assertEqual([], out["mains"], "a dangling MAIN put ★ MAIN on a row")
        self.assertEqual(["b1", "b2", "b3"], sorted(out["ids"]), "the rows stopped listing his builds under a dangling MAIN")
        self.assertIs(True, out["bound"], "a bind no longer works under a dangling MAIN")
        self.assertEqual({"src": "build", "id": "b2", "name": "Hammerdin"},
                         {k: out["roster"][0]["boundChar"][k] for k in ("src", "id", "name")})
        self.assertLess(out["list"].index('data-state="main-dangling"'), out["list"].index('data-src="build"'),
                        "the note sits under the rows, where a list of three hides it")

    def test_a_main_that_names_a_build_and_no_main_at_all_stay_quiet(self):
        out = _drive("b1")
        self.assertIsNone(out["note"], "a MAIN that names a saved build drew the dangling note")
        self.assertEqual(["b1"], out["mains"], "the MAIN he set does not wear ★ MAIN")
        self.assertIsNone(out["reader"]["mainDangling"])
        out = _drive(None)
        self.assertIsNone(out["note"], "no MAIN at all is not a dangling MAIN")
        self.assertEqual([], out["mains"])
        self.assertIsNone(out["reader"]["mainDangling"])

    def test_the_note_is_the_readers_word_and_the_two_sites_are_the_ones_measured(self):
        """the join, pinned at both ends: the list CARRIES what the reader said (never a second read of d2r_cbMain),
        and the note is drawn from that field — a comment can name either, so the exact expressions are graded"""
        import io
        with io.open(os.path.join(os.path.dirname(HERE), "bible.html"), encoding="utf-8") as fh:
            src = fh.read()
        code = re.sub(r"/\*.{0,4000}?\*/", "", src, flags=re.S)
        self.assertEqual(1, code.count("if (out.ok) out.mainDangling = r.mainDangling == null ? null : String(r.mainDangling);"),
                         "_mpBindChars no longer carries the reader's mainDangling")
        self.assertEqual(1, code.count("if (L.ok && L.mainDangling) h += '<div class=\"mp-bind-none\" data-state=\"main-dangling\""),
                         "the locker list no longer draws the dangling-MAIN note from the carried field")


RED_PROOF = [
    {
        "why": "#41 rank 20 review (REG-1554) - the locker list stops carrying the reader's mainDangling: a dangling MAIN reads like no MAIN again",
        "file": "../bible.html",
        "find": "    if (out.ok) out.mainDangling = r.mainDangling == null ? null : String(r.mainDangling);\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#41 rank 20 review (REG-1554) - the field is carried and the list never draws it: the unjoined end, back",
        "file": "../bible.html",
        "find": "    if (L.ok && L.mainDangling) h += '<div class=\"mp-bind-none\" data-state=\"main-dangling\"",
        "replace": "    if (false) h += '<div class=\"mp-bind-none\" data-state=\"main-dangling\"",
        "matches": 1,
    },
]


if __name__ == "__main__":
    if NODE is None:
        sys.stderr.write("⚪ SKIP — node is not on this machine, so the locker list was not driven. UNMEASURED, declared (77).\n")
        raise SystemExit(77)
    unittest.main(verbosity=2)
