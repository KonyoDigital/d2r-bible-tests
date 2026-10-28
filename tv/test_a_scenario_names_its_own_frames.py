# -*- coding: utf-8 -*-
"""#22 (REG-2764, his rulings 2026-10-28) - A HAND-TEST SCENARIO NAMES THE FRAMES OF HIS THAT TEST IT.

"if you can take my sessions and frames and reels and do the tests your self scenario by scenario then great" ...
"sync each scenario to each visual frame related" ... "make sure to join anything needed to be joined for that logic".

tv/scenario_frames.py joins each TESTING_PHASE scenario to its items (only names a roster or a recorded read knows), each
item to the frames whose reads named it, each frame to its own picture (<frameId>.jpg; a triage frame is a reel still),
and REC-03 to its check (every deep read of the newest long session warm, every commitment answered). A scenario with no
declared screens is NOT WIRED, never dropped; a base read beside a runeword is that runeword's base, never a white-base
control (looked at on his frame 14_1791910969555.jpg: Spirit's "Monarch" line).

Driven on a fixture TESTING_PHASE, fixture journals, a fixture triage and a fixture reel root - never his stores.
RED_PROOF below.
"""
import io
import json
import os
import shutil
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
import scenario_frames as SF  # noqa: E402

DOC = """# TESTING PHASE

## Index

| ☐ | [REC-03](#rec-03) | workers | TV·D | 6 | x |
| ☐ | [MR-01](#mr-01) | tags | Chronicle | 5 | x |
| ☐ | [ZZZ-99](#zzz-99) | an unwired one | x | 1 | x |

## 1 · scenarios

### REC-03 — workers answer every read

**Items:**
- Dwarf Star and Raven Frost: two rings.
- Goldwrap: a belt.

**Steps:**
1. read them.

### MR-01 — a stash read tags classes

**Items:**
- Monarch (white base): the BASE control.
- Raven Claw (unique Long Bow): the discriminator.
- Words that are not items: never join.

**Steps:**
1. read them.
"""

ROSTERS = {"dwarf star", "raven frost", "goldwrap", "raven claw", "spirit"}
S1, S2 = "s_1790000000000_1", "s_1791000000000_2"


def _rows():
    t = 1791000000000
    rows = []
    for k, (nm, scene) in enumerate((("Dwarf Star", "stash"), ("Raven Frost", "stash"), ("Goldwrap", "inventory"),
                                     ("Spirit", "stash"))):
        c = t + 1000 * (k + 1)
        names = [nm] + (["Monarch"] if nm == "Spirit" else [])
        rows.append({"lane": "deep-owed", "ts": c + 5, "frameId": "snap_0_%d.jpg" % k, "sessionId": S2})
        rows.append({"lane": "deep", "ts": c, "captureTs": c, "frameId": "%d_%d" % (k + 1, c), "sessionId": S2,
                     "scene": scene, "mode": "warm", "names": names})
    for k in range(5):                                    # enough deep reads to cross the respawn
        c = t + 100000 + k
        rows.append({"lane": "deep-owed", "ts": c + 5, "frameId": "snap_1_%d.jpg" % k, "sessionId": S2})
        rows.append({"lane": "deep", "ts": c, "captureTs": c, "frameId": "%d_%d" % (k + 9, c), "sessionId": S2,
                     "scene": "town", "mode": "warm", "names": []})
    # a KAI note about the Dwarf Star stash frame (its own capture time, as his notes carry) - a note, never a read
    rows.append({"lane": "kai", "ts": t + 90000, "captureTs": t + 1000, "sessionId": S2, "names": ["Raven Claw"]})
    return rows


class AScenarioNamesItsOwnFrames(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.d = tempfile.mkdtemp(prefix="scenario_frames_")
        cls.doc = os.path.join(cls.d, "TESTING_PHASE.md")
        io.open(cls.doc, "w", encoding="utf-8").write(DOC)
        cls.jr = os.path.join(cls.d, "sessions.jsonl")
        with io.open(cls.jr, "w", encoding="utf-8") as fh:
            for r in _rows():
                fh.write(json.dumps(r) + "\n")
        cls.tri = os.path.join(cls.d, "retro_triage.json")
        io.open(cls.tri, "w", encoding="utf-8").write(json.dumps(
            {"reel_" + S1: {"panelFrames": {"f_1790000005000.jpg": "shared", "f_1790000006000.jpg": "runes"}}}))
        cls.hist = os.path.join(cls.d, "hist")
        os.makedirs(cls.hist)
        open(os.path.join(cls.hist, "1_1791000001000.jpg"), "wb").close()     # Dwarf Star's picture is kept
        cls.rows = {r["id"]: r for r in SF.report(doc_path=cls.doc, paths=[cls.jr], triage=cls.tri, hist=cls.hist,
                                                   rosters=ROSTERS)}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.d, True)

    def test_every_scenario_in_the_index_is_reported(self):
        self.assertEqual(sorted(self.rows), ["MR-01", "REC-03", "ZZZ-99"])
        self.assertEqual(self.rows["ZZZ-99"]["verdict"], "NOT WIRED", "an undeclared scenario was dropped or guessed")

    def test_items_join_only_when_a_roster_or_a_read_knows_them(self):
        self.assertEqual(self.rows["REC-03"]["items"], ["dwarf star", "raven frost", "goldwrap"])
        self.assertEqual(self.rows["MR-01"]["items"], ["monarch", "raven claw"],
                         "a prose word joined as an item, or a known one was lost: %r" % self.rows["MR-01"]["items"])

    def test_an_item_names_the_frames_whose_reads_named_it(self):
        r = self.rows["REC-03"]
        self.assertEqual(r["itemsRead"], ["dwarf star", "raven frost", "goldwrap"])
        self.assertEqual(r["itemFrames"], 3, "the scenario's own frames were not the ones its items were read on: %r" % r)

    def test_a_runewords_base_is_not_a_white_base_control_and_a_note_is_not_a_read(self):
        r = self.rows["MR-01"]
        self.assertEqual((r["itemFrames"], r["itemsRead"]), (0, []),
                         "Spirit's 'Monarch' line, or a KAI note naming Raven Claw, joined as MR-01's own frame: %r" % r)
        self.assertEqual(r["itemsNever"], ["monarch", "raven claw"])

    def test_a_frame_names_its_own_picture_or_says_it_is_gone(self):
        r = self.rows["REC-03"]
        self.assertIn("1_1791000001000.jpg", r["sample"], "the frame was not joined to its own picture: %r" % r["sample"])
        self.assertEqual(r["onDisk"], 1)
        self.assertTrue(any("picture not on disk" in s for s in r["sample"]), "a pruned picture was not said: %r" % r)

    def test_the_triage_labels_older_reels_stash_frames(self):
        frames, _ = SF.load_frames([self.jr], self.tri)
        self.assertEqual(frames[(S1, 1790000005000)]["screens"], {"stash"})
        self.assertIn("reel_%s/f_1790000005000.jpg" % S1, frames[(S1, 1790000005000)]["pics"])

    def test_an_unread_document_is_unknown_never_no_scenarios(self):
        rows = SF.report(doc_path=os.path.join(self.d, "no_such.md"), paths=[self.jr], triage=self.tri, hist=self.hist,
                         rosters=ROSTERS)
        self.assertEqual([r["verdict"] for r in rows], ["UNKNOWN"], "an unread TESTING_PHASE read as no scenarios: %r" % rows)

    def test_rec03_is_judged_on_its_record(self):
        r = self.rows["REC-03"]
        self.assertEqual(r["verdict"], "PASS", r["why"])
        frames, deep = SF.load_frames([self.jr], self.tri)
        bad = dict(deep)
        bad[S2] = [dict(x, mode="oneshot") if x.get("lane") == "deep" and x["frameId"].startswith("9_") else x
                   for x in deep[S2]]
        self.assertEqual(SF.check_rec03({S2}, bad)[0], "FAIL", "a oneshot read in the newest long session passed")
        self.assertEqual(SF.check_rec03(set(), deep)[0], "UNKNOWN", "no long session was read as a pass")

    def test_rec03_passes_only_on_reads_proven_warm(self):
        """REG-2784 (the v3828 second eye) - only oneshot failed, so 9 stub or mode-less reads passed REC-03."""
        def sess(mode, n=9, t=1793000000000, empty=0):
            return ([{"lane": "deep", "mode": mode, "ts": t + i} for i in range(n)]
                    + [{"lane": "deep", "mode": "empty", "ts": t + 100 + i} for i in range(empty)])
        self.assertEqual(SF.check_rec03({"s_1"}, {"s_1": sess("warm", empty=4)})[0], "PASS")
        for mode, want in (("stub", "UNKNOWN"), ("None", "UNKNOWN"), ("g5-only", "UNKNOWN"),
                           ("g5-backup", "FAIL"), ("timeout", "FAIL")):
            rows = sess("warm", 8) + [{"lane": "deep", "mode": (None if mode == "None" else mode), "ts": 1793000000050}]
            self.assertEqual(SF.check_rec03({"s_1"}, {"s_1": rows})[0], want, "a %s read in REC-03's session" % mode)
        self.assertEqual(SF.check_rec03({"s_1"}, {"s_1": sess("warm", 5, empty=9)})[0], "UNKNOWN",
                         "frames with nothing to read were counted as worker reads across the respawn")

    def test_rec03_newest_session_is_its_latest_read_and_a_timeless_row_never_drags_it(self):
        """REG-2784 - the newest session was picked by its EARLIEST ts, and one row with ts 0 sank it."""
        old = [{"lane": "deep", "mode": "oneshot", "ts": 1793000000000 + i} for i in range(9)]
        new = [{"lane": "deep", "mode": "warm", "ts": 1792000000000}] + \
              [{"lane": "deep", "mode": "warm", "ts": 1794000000000 + i} for i in range(8)] + [{"lane": "deep", "mode": "warm"}]
        v, why = SF.check_rec03({"s_old", "s_new"}, {"s_old": old, "s_new": new})
        self.assertEqual((v, "s_new" in why), ("PASS", True), "the session with the latest reads did not decide: %s" % why)

    def test_scenario_items_without_the_known_names_keeps_none(self):
        """REG-2784 - the default kept every prose word, the opposite of the function's own rule."""
        self.assertIsNone(SF.scenario_items("REC-03", self.doc), "no known names, and prose words joined anyway")


RED_PROOF = [
    {"why": "REG-2784 - a stub, mode-less or other-eye read passes REC-03 again",
     "file": "scenario_frames.py",
     "find": "    if other:\n        return \"UNKNOWN\", why",
     "replace": "    if False:\n        return \"UNKNOWN\", why",
     "matches": 1},
    {"why": "REG-2784 - a read the backup answered is no failure again",
     "file": "scenario_frames.py",
     "find": "_REC03_FAIL = frozenset((\"oneshot\", \"error\", \"timeout\", \"g5-backup\"))\n",
     "replace": "_REC03_FAIL = frozenset((\"oneshot\", \"error\", \"timeout\"))\n",
     "matches": 1},
    {"why": "REG-2784 - frames with nothing to read count as worker reads across the respawn",
     "file": "scenario_frames.py",
     "find": "        worker = [r for r in deep if str(r.get(\"mode\")) not in _REC03_NEUTRAL]\n",
     "replace": "        worker = deep\n",
     "matches": 1},
    {"why": "REG-2784 - the newest session is picked by its earliest read again",
     "file": "scenario_frames.py",
     "find": "        t1 = max([t for t in ts if t > 0] or [0])\n",
     "replace": "        t1 = min(ts or [0])\n",
     "matches": 1},
    {"why": "REG-2784 - with no known names every prose word joins again",
     "file": "scenario_frames.py",
     "find": "    if known is None:\n        return None\n    text = _doc(doc_path)\n",
     "replace": "    text = _doc(doc_path)\n",
     "matches": 1},
    {"why": "REG-2764 - an unread TESTING_PHASE reads as no scenarios",
     "file": "scenario_frames.py",
     "find": "        if ids is None:\n            return [{\"id\": None, \"verdict\": \"UNKNOWN\",",
     "replace": "        if ids is None:\n            return []\n            return [{\"id\": None, \"verdict\": \"UNKNOWN\",",
     "matches": 1},
    {"why": "REG-2764 - an undeclared scenario is dropped from the report",
     "file": "scenario_frames.py",
     "find": "        if spec is None:\n            out.append(row)\n            continue\n",
     "replace": "        if spec is None:\n            continue\n",
     "matches": 1},
    {"why": "REG-2764 - a prose word joins as an item",
     "file": "scenario_frames.py",
     "find": "            if n and (known is None or n in known) and n not in out:\n",
     "replace": "            if n and n not in out:\n",
     "matches": 1},
    {"why": "REG-2764 - a runeword's base joins as a white-base control",
     "file": "scenario_frames.py",
     "find": "            if frames[k][\"names\"] & runewords:\n",
     "replace": "            if False:\n",
     "matches": 1},
    {"why": "REG-2764 - a note about a frame is read as a read of it",
     "file": "scenario_frames.py",
     "find": "READ_LANES = (\"deep\", \"ocr\", \"known\", \"intake\", \"verify\")\n",
     "replace": "READ_LANES = (\"deep\", \"ocr\", \"known\", \"intake\", \"verify\", \"kai\")\n",
     "matches": 1},
    {"why": "REG-2764 - a frame is joined to a footage still instead of its own picture",
     "file": "scenario_frames.py",
     "find": "                if isinstance(fid, str) and re.match(r\"^(\\d+_\\d+|reel_s_\\d+_\\d+/f_\\d+)$\", fid):\n",
     "replace": "                if False:\n",
     "matches": 1},
    {"why": "REG-2764 - REC-03 passes whatever its newest long session did",
     "file": "scenario_frames.py",
     "find": "    if any(modes.get(m, 0) for m in _REC03_FAIL) or owed > n:\n        return \"FAIL\", why\n",
     "replace": "    if False:\n        return \"FAIL\", why\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
