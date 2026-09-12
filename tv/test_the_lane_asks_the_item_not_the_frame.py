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

    def test_an_EVENLY_SPLIT_name_states_neither(self):
        """⚠ v3031 — RENAMED from test_a_name_seen_in_two_containers_states_neither, because that
        name stopped being true. Two containers no longer means silence: a majority that proves
        itself now names the item. What still states neither is a CLOSE split, which this fixture
        is — 1 vs 1 — and it is the case the rename makes explicit rather than incidental.
        [[label-outlived-referent]]"""
        c = L._containers([{"scene": "stash", "loc": "inventory"},
                           {"scene": "inventory", "loc": "equipped"}])
        self.assertIsNone(c.get("container"),
                          "a name whose sightings disagree EVENLY was flattened into one confident "
                          "container — 'it moved' and 'the reader is unsure' are different facts")
        self.assertEqual(c.get("containers"), {"inventory": 1, "equipped": 1},
                         "the split must remain legible")

    def test_a_majority_that_PROVES_ITSELF_names_the_container(self):
        """⚠⚠ v3031 — HIS RULING, 2026-09-12, on being shown Tome of Town Portal reading
        {inventory: 15, equipped: 1}: *"a logic of like winning just like the wilson score it
        should prove itself.. in this case it proves itself more to inventory so by default it
        should choose this"*.

        Until now ANY disagreement silenced the name, so one misread out of sixteen threw away
        fifteen agreeing sightings. MEASURED over his live evidence: 41 of 42 located names were
        unanimous, and the ONE exception is exactly the name he ruled on.

        ⚠ The minority is never deleted — `containers` still carries the full tally, so what was
        outvoted stays visible. A winner published without its count is a fact nobody can argue
        with. [[the-contradiction-is-the-finding]]"""
        c = L._containers([{"loc": "inventory"}] * 15 + [{"loc": "equipped"}])
        self.assertEqual(c.get("container"), "inventory",
                         "15 sightings against 1 did not name the container — his ruling is that "
                         "it proves itself")
        self.assertIs(c.get("containerAgreed"), False,
                      "a majority win must NOT be reported as unanimous agreement")
        self.assertEqual(c.get("containers"), {"inventory": 15, "equipped": 1},
                         "the outvoted reading was deleted rather than kept legible")
        self.assertIn("15", str(c.get("containerWhy") or ""),
                      "the reason does not carry the numbers it decided on")

    def test_a_BARE_majority_is_not_evidence_and_still_states_neither(self):
        """⚠ THE OTHER SIDE, and the one that keeps the rule honest. 8 vs 7 is a real contradiction,
        not a winner. The bar is the majority carrying at least TWICE the runner-up, stated rather
        than felt — without it 'majority wins' quietly becomes 'whoever is ahead wins'."""
        c = L._containers([{"loc": "inventory"}] * 8 + [{"loc": "stash"}] * 7)
        self.assertIsNone(c.get("container"),
                          "8 vs 7 named a container — a bare plurality was treated as proof")
        self.assertIn("too close", str(c.get("containerWhy") or "").lower(),
                      "a refused near-tie does not say why: %r" % c.get("containerWhy"))

    def test_a_UNANIMOUS_name_is_reported_as_agreed_not_merely_as_a_winner(self):
        """⚠ 'every sighting agrees' and 'the majority won' are different confidences, and the
        reader must be able to tell them apart. [[unknown-stays-unknown]]"""
        c = L._containers([{"loc": "inventory"}] * 5)
        self.assertEqual(c.get("container"), "inventory")
        self.assertIs(c.get("containerAgreed"), True,
                      "a unanimous reading was not reported as agreed, so it reads like a contested "
                      "win")

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
        #: ⚠ THE MARGIN IS THE WHOLE RULE. Dropping it to a bare plurality makes 8-vs-7 name a
        #: container, so "majority wins" silently becomes "whoever is ahead wins" and a coin-flip
        #: disagreement is published as a placement.
        "why": "a bare plurality is not evidence; without the twice-the-runner-up bar a 8-vs-7 "
               "split names a container and a genuine contradiction is reported as a fact",
        "file": "read_names_lane.py",
        "find": "        if _n >= 2 * _second:",
        "replace": "        if _n > _second:",
        "matches": 1,
    },
    {
        #: ⚠ AND THE OUTVOTED READING MUST SURVIVE. Publishing the winner while dropping the tally
        #: leaves a placement nobody can argue with.
        "why": "emptying the containers tally hides what was outvoted, so a 15-to-1 majority and a "
               "unanimous reading become indistinguishable on the surface",
        "file": "read_names_lane.py",
        "find": '            "containers": locs, "placed": placed, "unplaced": unplaced,',
        "replace": '            "containers": {}, "placed": placed, "unplaced": unplaced,',
        "matches": 1,
    },
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
        #: ⚠⚠ v3031 — RE-ANCHORED, AND THE INTENT IS PRESERVED RATHER THAN THE STRING. This
        #: tampered `"container": (list(locs)[0] if len(locs) == 1 else None)`, which the majority
        #: rule replaced — heart2 measured it INVALID (matched 0) the moment that line changed.
        #: Its point was "a disagreement must not be flattened into one confident word", and the
        #: new shape of that defect is a TIE taking the unanimous branch: widening `== 1` to `>= 1`
        #: makes 1-vs-1 name whichever loc happens to be first in the dict.
        #: ⚠ The margin proof above does NOT cover this — a bare-plurality tamper still leaves
        #: 1 > 1 false, so a tie stays None under it. Two different defects, two proofs.
        "find": "    if len(locs) == 1:",
        "replace": "    if len(locs) >= 1:",
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
