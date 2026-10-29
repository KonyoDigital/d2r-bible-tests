# -*- coding: utf-8 -*-
"""#218 (REG-3037, GrokBot #230 6485639332) - THE ROSTER ROW'S AGE NAMES THE ROW, FROM THE ROW'S OWN STAMP.

GrokBot 03:31: "the owners list and the profile snapshot run on separate clocks". ALT: list 03:00:34, ?profile= 02:28:01.
Mac: list 22:00:41, so Fleet said "stale", while its profile was 02:18:54. Dean: list 01:35:07, profile 01:51:08. So
Fleet's age and the shadow's age disagreed in either direction. They are three doors on three clocks:
  - the roster row is change-only (roster_publish.due posts an unchanged row only at boot, and roster.js answers an
    unchanged post "unchanged" and writes nothing), so the row's `t` is its last STORE - the Mac's board-derived row did
    not change from 22:00 until 03:57, and its 03:00 boot post wrote nothing;
  - the board snapshot (?profile=) is change-only too and waits out its own 75 min gap, a boot included
    (console_snapshot.MIN_GAP_MS, REG-2684): the ALT's 03:00 restart was 32 min after its 02:28 board, so the next went
    up at 03:43:39 (measured on the site);
  - the sessions digest has its own 3 h door (REG-3034 names that one).
The panel said "<owner> · stale" or "· published" with no age, and the no-board shadow bar "<owner> · published", so an
age of one record read as the owner's. Now every surface that dates the row says "roster row stored N ago" from the row's
own `t` (roster_publish.row_age_words, handed on by panel_words as row["ageWords"]), the board says "board uploaded N
ago" (REG-3034), and neither borrows the other's clock.

Driven: roster_publish in Python on fixture rows; the panel's and the bar's two expressions cut out of control_ui.html
and run in node. RED_PROOF below.
"""
import io
import json
import os
import shutil
import subprocess
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
import fixture_tmp as _fx  # noqa: E402
_fx.contain()
import console_snapshot as CS  # noqa: E402
import roster_publish as RP  # noqa: E402

NODE = shutil.which("node")
with io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as _fh:
    UI = _fh.read()
MAC = "Konyo · Mac"
NOW = 1793237460000                          # 03:31 IDT, GrokBot's look
ROW_T = NOW - (5 * 3600 + 30 * 60 + 19) * 1000   # the Mac's row, stored 22:00:41
BOARD_T = NOW - (72 * 60 + 6) * 1000             # the Mac's board, uploaded 02:18:54
PANEL = ("        var age = row && row.published === true\n", "          : 'not published';\n")
BAR = ("      var rowAge = (row && typeof row.ageWords === 'string' && row.ageWords) ? row.ageWords\n",
       "      if (!row || row.published !== true) say = owner + ' has not published a console · read only';\n")


def _cut(start, end):
    if UI.count(start) != 1:
        raise AssertionError("%r occurs %d times - this law cannot see its subject" % (start[:60], UI.count(start)))
    i = UI.index(start)
    return UI[i:UI.index(end, i) + len(end)]


def _row(t=ROW_T):
    sections = {"characters": {"asOf": t, "counts": 1, "rows": [{"name": "Shako"}]}}
    return {"owner": MAC, "published": True, "corrupt": False, "t": t,
            "hash": RP.hash_of(RP.packed(RP.for_hash(sections))), "sections": sections}


def _served(rows, now=NOW):
    d = tempfile.mkdtemp(prefix="roster_ages_")
    try:
        RP.write_cache(d, RP.view_of(rows, now))
        return RP.panel_words(RP.read_cache(d, now))
    finally:
        shutil.rmtree(d, True)


def _drawn(rows):
    if not NODE:
        raise AssertionError("node is not on this machine - this law does not skip")
    js = ("function panelAge(row){\n" + _cut(*PANEL) + "  return age;\n}\n"
          "function bar(row, owner, signed){\n" + _cut(*BAR) + "  return say;\n}\n"
          "const rows = " + json.dumps(rows) + ";\n"
          "console.log(JSON.stringify(rows.map(function (r) { return { panel: panelAge(r), bar: bar(r, r.owner, ' · SIG') }; })));\n")
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("node failed: %s" % r.stderr[-900:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class TheRowsAgeIsTheRowsStore(unittest.TestCase):

    def test_the_words_name_the_row_from_its_own_stamp(self):
        self.assertEqual(RP.row_age_words(_row(), NOW), "roster row stored 5 hr ago")
        self.assertEqual(RP.row_age_words(_row(NOW - 30000), NOW), "roster row stored under 1 min ago")
        self.assertEqual(RP.row_age_words({"owner": MAC}, NOW), "roster row stored, age UNKNOWN")
        self.assertEqual(RP.row_age_words(_row(NOW + 10 * 60000), NOW), "roster row stored, age UNKNOWN",
                         "a row stamped ahead of now was given an age")

    def test_the_route_hands_every_published_row_its_words_and_nobody_else(self):
        got = {r["owner"]: r.get("ageWords") for r in _served([_row(), {"owner": "Dean", "published": False}])["owners"]}
        self.assertEqual(got[MAC], "roster row stored 5 hr ago")
        self.assertIsNone(got.get("Dean"), "a row nobody published was dated")

    def test_the_roster_page_names_the_row_and_keeps_its_stale_mark(self):
        page = RP.roster_html({"ok": True, "fetched": True, "now": NOW, "owners": [RP.view_one(MAC, _row(), NOW)]})
        self.assertIn("<p>roster row stored 5 hr ago</p>", page)
        self.assertIn("roster-owner roster-stale", page, "a row 5 h past its store lost its stale mark")
        self.assertNotIn("published 5 hr ago", page)


class TheConsoleSaysWhichRecordEachAgeDates(unittest.TestCase):

    def test_the_panel_and_the_bar_print_the_rows_words(self):
        served = _served([_row()])["owners"]
        mac = [r for r in served if r["owner"] == MAC][0]
        old = {"owner": "Dean", "published": True, "age": "stale"}           # a console that sent no words
        nobody = {"owner": "Wife PC", "published": False}
        a, b, c = _drawn([mac, old, nobody])
        self.assertEqual(a, {"panel": "roster row stored 5 hr ago",
                             "bar": MAC + " · roster row stored 5 hr ago · SIG · read only"})
        self.assertEqual(b["panel"], "roster row stored, age UNKNOWN (the console did not say)")
        self.assertNotIn("stale", b["bar"], "a row with no words was called stale from a clock the console never sent")
        self.assertEqual(c, {"panel": "not published", "bar": "Wife PC has not published a console · read only"})

    def test_the_0331_mac_scene_two_records_two_named_ages(self):
        served = _served([_row()])["owners"]
        mac = [r for r in served if r["owner"] == MAC][0]
        stores = {"d2r_api_world": json.dumps({"machine": "mac"}), "d2r_owned": json.dumps(["Shako"])}
        board = CS.view(MAC, {"owner": MAC, "t": BOARD_T, "hash": CS.digest(stores), "stores": stores}, NOW, online=True)
        fleet = _drawn([mac])[0]["panel"]
        self.assertEqual(fleet, "roster row stored 5 hr ago")
        self.assertIn("board uploaded 72 min ago", board["words"])
        for said in (fleet, board["words"]):
            self.assertNotRegex(said, r"(^|· )(stale|published)( ·|$)", "an age that does not say what it dates: %r" % said)


RED_PROOF = [
    {"why": "REG-3037 - the row's age says 'published' and not what it dates",
     "file": "tv/roster_publish.py",
     "find": "    return (\"roster row stored \" + words) if words else \"roster row stored, age UNKNOWN\"\n",
     "replace": "    return (\"published \" + words) if words else \"published, age unknown\"\n",
     "matches": 1},
    {"why": "REG-3037 - the route hands the panel no age for a row",
     "file": "tv/roster_publish.py",
     "find": "            row[\"ageWords\"] = row_age_words(row, payload.get(\"now\"))   # REG-3037 - the panel and the bar print it as given\n",
     "replace": "            pass\n",
     "matches": 1},
    {"why": "REG-3037 - the roster page says 'published N ago stale' again",
     "file": "tv/roster_publish.py",
     "find": "    when = row_age_words(row, now_ms)   # REG-3037 - the row's store, named; \"stale\" no longer calls an unchanged row old\n",
     "replace": "    when = \"published \" + (_age_words(state, _words) or \"age unknown\")\n",
     "matches": 1},
    {"why": "REG-3037 - the panel prints 'stale' / 'published' with no age",
     "file": "tv/control_ui.html",
     "find": "          ? ((typeof row.ageWords === 'string' && row.ageWords) ? row.ageWords : 'roster row stored, age UNKNOWN (the console did not say)')\n",
     "replace": "          ? (row.age === 'stale' ? 'stale' : 'published')\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-3037 - the no-board shadow bar says 'published' and not the row's age",
     "file": "tv/control_ui.html",
     "find": "      var say = owner + ' · ' + rowAge + signed + ' · read only';\n",
     "replace": "      var say = owner + ' · published' + signed + ' · read only';\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
