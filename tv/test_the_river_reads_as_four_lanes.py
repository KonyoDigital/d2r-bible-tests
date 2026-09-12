# -*- coding: utf-8 -*-
"""v2987 (#58) — THE SHELF SHOWS THE RIVER'S FOUR LANES, NAMED THE WAY HE NAMES THEM.

HIS WORDS, 2026-09-12, on a screenshot of his own shelf:
  *"i want it a little more synced with the coming in timestamps FIFO ... it should be organzied a
   little more and synced timeline story line like the session 7 is down here but sessions 33 and
   34 are uptop? weird a little and confusing. i want it down a river lane. from top to bottom
   intake/WHATEVER IS REALLY FIRST and then tombstone at the bottom of it all"*
  *"EMPTY and STATION aren't river stages — remove it then.. it is confusing"*
  *"so leave them.. if they are real stages.. but i think we had 4 ... check to se"*
  *"for th elast oone shows tombstone reads deleted.. and for shows station should read analyze
   for intake it should read FRESH"*

HE WAS RIGHT ABOUT FOUR, AND THE DATA ALREADY HAD THEM. /api/river publishes `lanes.lanes` —
INTAKE / PRINTER / CAPTURE / TOMBSTONE, each naming the stations it owns — and the shelf rendered
the NINE stations flat, throwing the lanes away.

⚠ AND THE FLAT ORDER WAS NOT A RIVER. `stations` runs INTAKE,TRIAGE,EMPTY,STATION,PRINTER,JOIN,
CAPTURE,ROUTED,TOMBSTONE while the LANES declare INTAKE[INTAKE,TRIAGE,STATION,EMPTY],
PRINTER[PRINTER], CAPTURE[CAPTURE,JOIN], TOMBSTONE[ROUTED,TOMBSTONE] — two stations transposed in
each of two places, so a lane's own sections were not even adjacent on screen.

⚠⚠ NOTHING WAS REMOVED, AND THAT IS THE LOAD-BEARING PART. His first instinct was to delete EMPTY
and STATION. MEASURED on his river the same minute: STATION held 6 reels and EMPTY is a real stage
("walked IN FULL and found ZERO panel frames"). Deleting them would have orphaned six reels and
left the actual defect — THE SHELF PRINTS THE KEY — untouched. Six of nine keys disagree with the
name in their own OWES text, and the worst of them is ROUTED: its description opens "TOMBSTONE",
it holds 20 reels, and the section he reads as "TOMBSTONE 0 NEVER REACHED" is the AFTER-state for
reels that have left the disk. [[label-outlived-referent]]

THE LAW PINS FOUR THINGS, each of which was separately wrong or absent:
  1. his three names are honoured exactly — FRESH / ANALYZE / DELETED;
  2. every station has a label and no two share one (two sections with one name is the same
     confusion wearing a different hat);
  3. the labels reach the page from the BACKEND — control_ui.html must not grow a second list;
  4. the shelf builds its station order from the LANES, not from the flat list.
"""
import ast
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

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import reel_router as RR   # noqa: E402

UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()


def _no_comments(src):
    """`src` with every /* ... */ block blanked, NEWLINES KEPT. -> str

    ⚠⚠ THIS LAW FAILED ON ITS OWN PROSE THE FIRST TIME IT RAN. Test 3 asserts the page holds no
    second list of station names — and the CSS comment I wrote in the same commit says "INTAKE
    reads FRESH, STATION reads ANALYZE, TOMBSTONE reads DELETED". A law about CODE must read code:
    a name mentioned in a comment is documentation, a name in a string literal is a second list.
    ⚠ Blanked, never deleted, and newlines preserved — a stripper that eats newlines makes every
    line number downstream of it wrong, which has already cost this repo a whole misread region.
    [[source-reading-guard]] [[measured-true-read-wrong]]
    """
    out, i, n = [], 0, len(src)
    while i < n:
        j = src.find("/*", i)
        if j < 0:
            out.append(src[i:]); break
        out.append(src[i:j])
        k = src.find("*/", j + 2)
        if k < 0:
            out.append(" " * (n - j)); break
        out.append("".join(c if c == "\n" else " " for c in src[j:k + 2]))
        i = k + 2
    return "".join(out)


UI_CODE = _no_comments(UI)


class TheRiverReadsAsFourLanes(unittest.TestCase):

    # ── 1. his words ──────────────────────────────────────────────────────────────────────────
    def test_his_three_names_are_exactly_what_he_said(self):
        L = RR.labels()
        for key, said in (("INTAKE", "FRESH"), ("STATION", "ANALYZE"), ("TOMBSTONE", "DELETED")):
            self.assertEqual(
                L.get(key), said,
                "he named %s %r on his own screen; the shelf would print %r"
                % (key, said, L.get(key)))

    def test_the_mouth_is_named_for_what_it_holds(self):
        """ROUTED is the real tombstone — 20 reels — and read as 'ROUTED' on his screen."""
        self.assertEqual(RR.labels().get("ROUTED"), "TOMBSTONE",
                         "the station that actually holds the finished reels is not named "
                         "TOMBSTONE, so the river appears to end nowhere")

    # ── 2. every station named, exactly once ──────────────────────────────────────────────────
    def test_every_station_has_a_label_and_none_collide(self):
        L = RR.labels()
        missing = [s for s in RR.STATIONS if not str(L.get(s) or "").strip()]
        self.assertEqual(missing, [], "station(s) with no label: %r" % missing)
        names = [L[s] for s in RR.STATIONS]
        dupes = sorted({n for n in names if names.count(n) > 1})
        self.assertEqual(dupes, [],
                         "two stations would print the SAME heading (%r), which is the confusion "
                         "this change exists to end" % dupes)

    def test_no_station_was_dropped_to_tidy_the_picture(self):
        """⚠ HIS FIRST INSTINCT WAS TO DELETE TWO OF THESE. STATION held 6 reels."""
        for s in ("EMPTY", "STATION"):
            self.assertIn(s, RR.STATIONS,
                          "%r was removed from the river rather than renamed — the reels stationed "
                          "there have nowhere to be" % s)

    # ── 3. ONE list, on the backend ───────────────────────────────────────────────────────────
    def test_the_page_does_not_keep_a_second_list_of_names(self):
        """[[copy-drift]] — STATIONS already carries this warning; a label list is the same hazard."""
        self.assertEqual(UI_CODE.count("\n"), UI.count("\n"),
                         "the comment stripper changed the line count, so it is eating newlines "
                         "and every offset measured through it is wrong")
        # ⚠⚠ THE FIRST CUT OF THIS TEST WAS WRONG AND THE CODE WAS RIGHT. It searched the page for
        # the words FRESH/ANALYZE/SEAL/TOMBSTONE and went red on THREE false positives: `vr.state
        # !== 'FRESH'` is a version-report state with no connection to the river, and the three
        # 'TOMBSTONE' hits are comparisons against the station KEY, which are legitimate and must
        # keep working. A law that forbids a WORD forbids the wrong thing; the property that
        # matters is where the MAP comes from. [[sabotage-is-usually-the-wrong-one]]
        import re as _re
        asn = _re.findall(r"SHELF_RIVER_LABELS\s*=\s*([^;]+);", UI_CODE)
        self.assertTrue(asn, "nothing assigns SHELF_RIVER_LABELS any more")
        for rhs in asn:
            self.assertTrue(
                ("d.labels" in rhs) or rhs.strip() in ("null", "d.labels || null"),
                "SHELF_RIVER_LABELS is assigned from %r — it must come from /api/river's own "
                "`labels` (reel_router.labels()) or be null. A literal map here is a SECOND list "
                "of names, and two lists is how they drift apart silently." % rhs.strip()[:70])

    # ── 4. the order is the LANES' ────────────────────────────────────────────────────────────
    def _run_order(self, lanes, flat):
        """Execute the SHIPPED ordering block in node. -> list | None

        ⚠⚠ THIS TEST WAS BLIND ON ITS FIRST DRILL. It asserted only that the text
        `SHELF_RIVER_LANES[_li]` was PRESENT, so the tamper that turns `ordG = []` into
        `ordG = null` — which breaks the flattening outright — sailed straight through it. heart2
        said so: "stayed GREEN through its own defeat". A law about an ORDER has to produce one.
        [[source-reading-guard]] [[feedback-blind-fixture-green-gate]]
        """
        a = UI.find("      var ordG = null;")
        b = UI.find("if (!ordG || !ordG.length) ordG = SHELF_RIVER_ORDER || [];")
        if a < 0 or b < a:
            return None
        block = UI[a:b + len("if (!ordG || !ordG.length) ordG = SHELF_RIVER_ORDER || [];")]
        js = ("var SHELF_RIVER_LANES = %s, SHELF_RIVER_ORDER = %s;\n%s\nconsole.log(JSON.stringify(ordG));"
              % (json.dumps(lanes), json.dumps(flat), block))
        d = tempfile.mkdtemp(prefix="lane_ord_")
        self.addCleanup(shutil.rmtree, d, True)
        f = os.path.join(d, "t.js")
        io.open(f, "w", encoding="utf-8").write(js)
        try:
            r = subprocess.run(["node", f], capture_output=True, text=True, timeout=60)
        except Exception:
            return None
        if r.returncode != 0:
            return {"__err": (r.stderr or "")[:300]}
        return json.loads(r.stdout.strip().splitlines()[-1])

    def test_the_shelf_orders_its_sections_by_lane(self):
        LANES = [{"name": "INTAKE", "stations": ["INTAKE", "TRIAGE", "STATION", "EMPTY"]},
                 {"name": "PRINTER", "stations": ["PRINTER"]},
                 {"name": "CAPTURE", "stations": ["CAPTURE", "JOIN"]},
                 {"name": "TOMBSTONE", "stations": ["ROUTED", "TOMBSTONE"]}]
        FLAT = ["INTAKE", "TRIAGE", "EMPTY", "STATION", "PRINTER", "JOIN", "CAPTURE",
                "ROUTED", "TOMBSTONE"]
        got = self._run_order(LANES, FLAT)
        if got is None:
            self.skipTest("node unavailable, or the ordering block moved — a skip is NOT a pass")
        if isinstance(got, dict):
            self.fail("the shipped ordering block would not execute: %s" % got.get("__err"))
        self.assertEqual(
            got, ["INTAKE", "TRIAGE", "STATION", "EMPTY", "PRINTER", "CAPTURE", "JOIN",
                  "ROUTED", "TOMBSTONE"],
            "the section order is not the LANES' order. The flat list transposes STATION/EMPTY and "
            "JOIN/CAPTURE, which is why a lane's own sections were not adjacent on his screen.")

    def test_the_flat_list_is_only_a_fallback(self):
        FLAT = ["INTAKE", "TRIAGE", "EMPTY", "STATION"]
        got = self._run_order(None, FLAT)
        if got is None:
            self.skipTest("node unavailable — a skip is NOT a pass")
        self.assertEqual(got, FLAT,
                         "with no lanes the shelf must still render from the flat station list; "
                         "an older console or a river that answered without lanes would go blank")

    def test_the_label_is_printed_and_the_key_is_kept(self):
        self.assertIn("SHELF_RIVER_LABELS[st]) || st", UI,
                      "the header no longer falls back to the KEY when the map is absent — an "
                      "unnamed station would render blank instead of honestly as its key")
        self.assertIn("shg-key", UI,
                      "the dim key was dropped from the heading; his screen and his logs would "
                      "then disagree about the name of the same thing")


RED_PROOF = [
    {
        "why": "renaming his own word for the stage puts the confusion he reported straight back",
        "file": "reel_router.py",
        "find": '"INTAKE": "FRESH"',
        "replace": '"INTAKE": "SURVEY"',
        "matches": 1,
    },
    {
        "why": "dropping the lane flattening returns the shelf to nine flat sections in an order "
               "whose stations are not even adjacent",
        "file": "control_ui.html",
        "find": "        ordG = [];",
        "replace": "        ordG = null;",
        "matches": 1,
    },
    {
        "why": "removing EMPTY/STATION is what he first asked for, and it orphans the six reels "
               "stationed at STATION",
        "file": "reel_router.py",
        "find": 'STATIONS = ("INTAKE", "TRIAGE", "EMPTY", "STATION", "PRINTER", "JOIN", "CAPTURE",',
        "replace": 'STATIONS = ("INTAKE", "TRIAGE", "PRINTER", "JOIN", "CAPTURE",',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
