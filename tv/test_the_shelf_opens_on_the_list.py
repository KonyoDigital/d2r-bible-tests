# -*- coding: utf-8 -*-
"""REG-1757 — THE SHELF OPENS ON THE LIST, AND A REEL DOES NOT BORROW ANOTHER.

GrokBot's ALT pass: the shelf's first paint was a theatre session (whichever was opened
last), an empty reel toasted that it had opened a different session and played that one,
and the dossier called journal rows "frames" beside a theatre that counts photos.

The door sets TH.shelfAsDoor and calls thOpen with no argument — the refusal law reads
that exact call. thOpen returns before thLoadSession on that path. Last session, the
button inside the shelf, asks thPickEntrySession, the same pick as the Theatre button,
not whichever dossier happens to be open.

An empty reel stays on the session he asked for. The dossier names film frames or journal
rows. It has a close that dismisses, the same function as the back label. The read panel
and the frame's inset are one width, and the panel does not open itself. The station tabs
touch, so a press between them hits a tab.
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from console_safe import enable
enable()

UI = os.path.join(HERE, "control_ui.html")


def _body(src, sig):
    """The brace-bounded body that starts at the one occurrence of sig."""
    if src.count(sig) != 1:
        raise AssertionError("%r occurs %d times — this guard cannot see its subject"
                             % (sig, src.count(sig)))
    i = src.index(sig)
    b = src.index("{", i)
    depth, j = 0, b
    while j < len(src):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                return src[b:j + 1]
        j += 1
    raise AssertionError("could not bound %r — harness fault, not a pass" % sig)


class TheShelfOpensOnTheList(unittest.TestCase):

    def setUp(self):
        with io.open(UI, encoding="utf-8") as fh:
            self.src = fh.read()

    def test_the_shelf_door_returns_before_a_session(self):
        body = _body(self.src, "async function thOpen(){")
        self.assertIn("TH.shelfAsDoor = false", body,
                      "thOpen does not clear the shelf request, so the next open inherits it")
        door = body.find("if (_shelfDoor)")
        load = body.find("thLoadSession")
        self.assertGreater(door, 0, "the shelf path is gone from thOpen, so the door loads a session")
        self.assertGreater(load, door, "thLoadSession runs before the shelf return")
        self.assertIn("return;", body[door:load])

    def test_the_door_asks_and_still_calls_thOpen(self):
        self.assertEqual(self.src.count("TH.shelfAsDoor = true; await thOpen();"), 1,
                         "the shelf door no longer both asks for the list and calls thOpen()")
        self.assertEqual(self.src.count("if (!TH.open && !openErr) return"), 1)

    def test_last_session_uses_the_theatre_pick(self):
        self.assertEqual(self.src.count('id="sh-last-session"'), 1)
        i = self.src.index('id="sh-last-session"')
        window = self.src[i:i + 90]
        self.assertIn('onclick="window._shelfLastSession()"', window)
        self.assertNotIn("_dossierToTheatre", window)
        body = _body(self.src, "window._shelfLastSession = async function(){")
        self.assertIn("thPickEntrySession", body,
                      "Last session does not ask the Theatre button's pick")
        self.assertNotIn("DOSSIER", body,
                         "Last session follows the open dossier, which is a different session")

    def test_an_empty_reel_stays_itself(self):
        body = _body(self.src, "async function thLoadSession(")
        self.assertIn("has no film yet", body)
        self.assertNotIn("return thLoadSession", body)
        self.assertNotIn("opened session", body)
        self.assertEqual(self.src.count("return thLoadSession"), 0)
        self.assertEqual(self.src.count("opened session"), 0)

    def test_the_dossier_names_the_count(self):
        self.assertEqual(self.src.count("tile(_frameNoun, _frames)"), 1)
        self.assertIn("'film frames'", self.src)
        self.assertIn("'journal rows'", self.src)

    def test_the_dossier_has_a_close(self):
        self.assertEqual(self.src.count('id="dsr-x"'), 1)
        i = self.src.index('id="dsr-x"')
        self.assertIn('onclick="window._dossierClose()"', self.src[i:i + 140])

    def test_the_read_panel_and_the_frame_are_one_width(self):
        self.assertEqual(self.src.count("min(280px, 30%)"), 2,
                         "the drawer and the frame inset drifted apart, or the panel grew back")
        self.assertEqual(self.src.count("width: min(280px, 30%)"), 1)
        self.assertEqual(self.src.count("right: min(280px, 30%)"), 1)
        self.assertEqual(self.src.count("min(380px, 44%)"), 0)

    def test_the_read_panel_does_not_open_itself(self):
        self.assertEqual(self.src.count("else CARD.autoArmed = false;"), 1)
        self.assertEqual(self.src.count("catch (e) { CARD.autoArmed = false; }"), 1)
        self.assertEqual(self.src.count("CARD.autoArmed = true"), 0)
        self.assertNotIn("pref !== 'closed'", self.src)

    def test_a_press_between_station_tabs_hits_a_tab(self):
        self.assertEqual(
            self.src.count(".sh-stationbar { display: flex; align-items: center; flex-wrap: wrap; gap: 0;"),
            1)
        self.assertEqual(self.src.count(".sh-stationbar > .sh-chip { padding: 8px 16px; }"), 1)


RED_PROOF = [
    {"why": "REG-1757 - the shelf door loads a session again",
     "file": "control_ui.html",
     "find": "    if (_shelfDoor) {\n"
             "      try { $('th-caption').textContent = 'the shelf'; } catch (e) {}\n"
             "      thLit();\n"
             "      return;\n"
             "    }\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-1757 - the shelf button opens the theatre without asking for the list",
     "file": "control_ui.html",
     "find": "TH.shelfAsDoor = true; await thOpen();",
     "replace": "await thOpen();",
     "matches": 1},
    {"why": "REG-1757 - an empty reel opens a different session",
     "file": "control_ui.html",
     "find": "    if (!framed){\n"
             "      $('th-caption').textContent = '🎞 session ' + n + ' has no film yet — nothing else was opened';\n"
             "      TH.sn = n; TH.beats = []; TH.allBeats = []; TH.sessionId = j.sessionId || '';\n"
             "      try { thTimeline(); } catch(e){}\n"
             "      return;\n"
             "    }\n",
     "replace": "    if (!framed){\n"
                "      return thLoadSession(alt2, isEntry);\n"
                "    }\n",
     "matches": 1},
    {"why": "REG-1757 - the dossier calls both counts frames",
     "file": "control_ui.html",
     "find": "tile(_frameNoun, _frames)",
     "replace": "tile('frames', _frames)",
     "matches": 1},
    {"why": "REG-1757 - Last session plays the open dossier",
     "file": "control_ui.html",
     "find": 'onclick="window._shelfLastSession()"',
     "replace": 'onclick="window._dossierToTheatre()"',
     "matches": 1},
    {"why": "REG-1757 - the dossier close is gone",
     "file": "control_ui.html",
     "find": "               + (_onShelf ? 'back to the shelf' : 'back') + '</button>'\n"
             "               + '<button type=\"button\" class=\"dsr-x\" id=\"dsr-x\" title=\"close this dossier\" '\n"
             "               + 'onclick=\"window._dossierClose()\">\\u2715</button></div>';\n",
     "replace": "               + (_onShelf ? 'back to the shelf' : 'back') + '</button></div>';\n",
     "matches": 1},
    {"why": "REG-1757 - the read panel grows back and no longer matches the frame",
     "file": "control_ui.html",
     "find": "width: min(280px, 30%);",
     "replace": "width: min(380px, 44%);",
     "matches": 1},
    {"why": "REG-1757 - the frame inset stays wide after the panel was narrowed",
     "file": "control_ui.html",
     "find": "right: min(280px, 30%)",
     "replace": "right: min(380px, 44%)",
     "matches": 1},
    {"why": "REG-1757 - a session with no saved preference opens the read panel on the first named beat",
     "file": "control_ui.html",
     "find": "else CARD.autoArmed = false;",
     "replace": "else CARD.autoArmed = (pref !== 'closed');",
     "matches": 1},
    {"why": "REG-1757 - a failed preference read arms the read panel",
     "file": "control_ui.html",
     "find": "catch (e) { CARD.autoArmed = false; }",
     "replace": "catch (e) { CARD.autoArmed = true; }",
     "matches": 1},
    {"why": "REG-1757 - the gap between station tabs is a miss again",
     "file": "control_ui.html",
     "find": ".sh-stationbar { display: flex; align-items: center; flex-wrap: wrap; gap: 0;",
     "replace": ".sh-stationbar { display: flex; align-items: center; flex-wrap: wrap; gap: 6px;",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
