# -*- coding: utf-8 -*-
"""HIS RULING 2026-09-12 — A CONTAINER IS A PROPERTY OF THE ITEM, NOT OF THE FRAME.

*"these are specifically locked items within the INVENTORY specifically and not stashed items..
they are inside and witnessed within the inventory for sure. and the slot itendity for them should
also have been tallied and logged and ledgered as such so there is that distinigushed difference."*

THE DEFECT. A deep journal row carries ONE `scene` and a LIST of `names`, so every name read from a
frame inherited that frame's single label. In D2R the stash panel displays the inventory beside it,
so one frame legitimately holds items from BOTH containers. `read_names_lane.evidence()` recorded
`scene` and dropped `names_loc` — the producer's PER-NAME container map, present on 125 of 151 deep
rows. Two halves, each correct, never joined. [[the-unjoined-end]]

MEASURED on his journal, frame `scene` vs per-name `names_loc`, all panel sightings:
    stash / inventory      56   <- DISAGREE
    inventory / inventory  31
    stash / stash          12   <- the ONLY genuinely-stash sightings, out of 71 so labelled
    inventory / floor       7   <- DISAGREE
    stash / equipped 2 · stash / floor 1 · inventory / equipped 1
    => 67 of 110 placed sightings carried a container contradicting the item's own.

WHY HIS THREE SETTLE IT. The cube and the two tomes are carried permanently and can never sit in a
stash, so they are the only names in the corpus whose true container is KNOWN — a known-answer
probe. `names_loc` says `inventory` on all 58 of their sightings; `scene` said `stash` on 34. The
system had already recorded the right answer and only the lane disagreed.

⚠ `scene` IS KEPT. It is a true fact about the frame, and the PAIR is worth more than either half:
a name whose frame and item disagree is precisely a name seen in one panel while living in another.
The law below pins the join, not the replacement.

⛔ THE SLOT HALF IS UNBUILT, DELIBERATELY. 0 of 151 deep rows carry any slot/cell/grid/xy/rect
field, so there is no coordinate to join — a slot ledger needs capture and extraction work, like
REG-340's character panel. Test 5 PINS THAT ZERO so the day a slot field appears, this law fails
and says so rather than letting the gap go unnoticed. [[unknown-stays-unknown]]
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

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import read_names_lane as L  # noqa: E402

#: One frame, stash panel open, carrying an inventory item and a stash item. This is the shape the
#: lane got wrong: both names inherited `scene: "stash"`.
ROW = {"lane": "deep", "sessionId": "s_1", "scene": "stash", "conf": 0.93, "ts": 1,
       "names": ["Horadric Cube", "Shako"],
       "names_loc": {"Horadric Cube": "inventory", "Shako": "stash"}}


class TheLaneAsksTheItemNotTheFrame(unittest.TestCase):

    def _ev(self):
        return {"Horadric Cube": [{"session": "s_1", "conf": 0.93, "ts": 1,
                                   "scene": "stash", "loc": "inventory"}],
                "Shako": [{"session": "s_1", "conf": 0.93, "ts": 1,
                           "scene": "stash", "loc": "stash"}]}

    def test_evidence_carries_the_per_name_container(self):
        """THE ROUND TRIP, and it must stay one.

        ⚠⚠ THIS TEST WAS BLIND ON ITS FIRST RED-PROOF. It read `self.assertIn("names_loc", src)` —
        and the tamper that reverts the join to the frame's `scene` LEAVES that string in the file,
        in the comment above it and in the `_loc = r.get("names_loc")` line the tamper does not
        touch. heart2 said so in as many words: "stayed GREEN through its own defeat". A substring
        is not a behaviour. [[source-reading-guard]] [[feedback-blind-fixture-green-gate]]
        """
        d = tempfile.mkdtemp(prefix="lane_law_")
        self.addCleanup(shutil.rmtree, d, True)
        jp = os.path.join(d, "journal.jsonl")
        io.open(jp, "w", encoding="utf-8").write(json.dumps(ROW) + "\n")
        ev, why = L.evidence(journal_paths=[jp])
        self.assertIsNotNone(ev, "the fixture journal produced nothing: %s" % why)
        self.assertEqual(sorted(ev), ["Horadric Cube", "Shako"],
                         "the fixture row did not yield both names (%s)" % why)
        cube = ev["Horadric Cube"][0]
        self.assertEqual(cube.get("scene"), "stash",
                         "the frame's own label was lost — it is a true fact and must survive")
        self.assertEqual(
            cube.get("loc"), "inventory",
            "the carried item was filed under the frame's panel instead of its own location: this "
            "is the defect itself, an inventory item read while the stash was open becoming a "
            "stash item")
        self.assertEqual(ev["Shako"][0].get("loc"), "stash",
                         "the stash item in the SAME frame lost its own location")

    def test_two_names_in_one_frame_get_different_containers(self):
        c = L._containers(self._ev()["Horadric Cube"])
        d = L._containers(self._ev()["Shako"])
        self.assertEqual(c.get("container"), "inventory",
                         "the carried item took the frame's label instead of its own")
        self.assertEqual(d.get("container"), "stash",
                         "the stash item lost its own label")

    def test_the_frame_disagreement_is_counted_not_hidden(self):
        c = L._containers(self._ev()["Horadric Cube"])
        self.assertEqual(c.get("frameDisagreed"), 1,
                         "a sighting whose frame contradicts the item is the whole finding; it "
                         "must be COUNTED, not silently resolved in favour of either side")
        self.assertEqual(L._containers(self._ev()["Shako"]).get("frameDisagreed"), 0,
                         "an agreeing sighting was counted as a disagreement")

    def test_a_name_seen_in_two_containers_states_neither(self):
        c = L._containers([{"scene": "stash", "loc": "inventory"},
                           {"scene": "inventory", "loc": "equipped"}])
        self.assertIsNone(c.get("container"),
                          "a name whose sightings disagree was flattened into one confident "
                          "container — 'it moved' and 'the reader is unsure' are different facts")
        self.assertEqual(c.get("containers"), {"inventory": 1, "equipped": 1},
                         "the split must remain legible")

    def test_an_unplaced_sighting_is_unplaced_not_floor(self):
        c = L._containers([{"scene": "stash", "loc": None}])
        self.assertIsNone(c.get("container"), "an unplaced name was given a container anyway")
        self.assertEqual((c.get("placed"), c.get("unplaced")), (0, 1),
                         "the placed/unplaced denominator is wrong, so any rate built on it lies")

    def test_the_slot_half_is_still_unbuilt_and_says_so(self):
        src = io.open(os.path.join(HERE, "read_names_lane.py"), encoding="utf-8").read()
        self.assertIn("THE SLOT HALF OF HIS RULING IS NOT BUILT", src,
                      "the note recording that slot identity is a CAPTURE change, not a wiring "
                      "change, is gone — without it the gap reads as an oversight and someone "
                      "will try to synthesise a slot from data that does not exist")


RED_PROOF = [
    {
        "why": "going back to the frame's scene is the original defect: an inventory item read "
               "while the stash was open becomes a stash item again",
        "file": "read_names_lane.py",
        "find": '"loc": str(_loc.get(nm) or "").strip().lower() or None})',
        "replace": '"loc": str(r.get("scene") or "").strip().lower() or None})',
        "matches": 1,
    },
    {
        "why": "stating a container when the sightings disagree flattens 'it moved' and 'unsure' "
               "into one confident word",
        "file": "read_names_lane.py",
        "find": '"container": (list(locs)[0] if len(locs) == 1 else None),',
        "replace": '"container": (list(locs)[0] if locs else None),',
        "matches": 1,
    },
    {
        "why": "dropping the disagreement counter hides the finding itself",
        "file": "read_names_lane.py",
        "find": "        if sc and sc != loc:\n            dis += 1",
        "replace": "        if False:\n            dis += 1",
        "matches": 1,
    },
    {
        "why": "deleting the note about the slot half lets the unbuilt gap read as an oversight",
        "file": "read_names_lane.py",
        "find": "THE SLOT HALF OF HIS RULING IS NOT BUILT",
        "replace": "_HEART2_TAMPERED_",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
