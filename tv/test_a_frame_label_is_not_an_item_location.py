# -*- coding: utf-8 -*-
"""ONE FRAME LABEL WAS STAMPED ONTO A WHOLE LIST OF ITEMS, AND THAT IS WHY THE WRONG THINGS
REGISTERED.

Konyo, 2026-09-12: *"it was working exactly like that just not registering the right items based
on the routing."* He was right, and the defect was one line in extract_gap:

    sc = str(r.get("scene") or "").strip().lower()
    if sc in PANEL_SCENES:
        cur["panel"] += len(names)          <- every name inherits the FRAME's label

A deep row carries ONE `scene` and a LIST of names. In D2R the stash panel and the inventory are
open together, so a single frame legitimately holds items from BOTH containers — and this counted
all of them as whichever panel the frame was called.

read_names_lane was fixed for exactly this in v2983 and RECORDS the per-item container in
`names_loc`. This module never read it: measured 2026-09-12, `loc` appeared zero times in it and
`scene` once. The producer had the right answer and the classifier ignored it.
[[the-unjoined-end]]

MEASURED on his journal ring — frame `scene` / item `names_loc`:
    stash/inventory 56 · stash/stash 12 · inventory/inventory 31 · inventory/floor 7
    stash/floor 1 · stash/equipped 2 · inventory/equipped 1
    gameplay/floor 199 (agrees) · chronicle/(unplaced) 154
So ELEVEN names that can never be a holding were counted as panel, and FIFTY-SIX inventory items
were filed under stash.

⚠⚠ AND `stash` IS NOT A CONTAINER AN ITEM IS READ IN. His ruling, the same day: *"stash/stash
there is no such thing.. when stash is open the INVENTORY IS OPEN at the same time soo
stash/inventory is when we stash items.. inventory/inventory is just inventory which is sometimes
a place before we stash the item form inventory to the stash"*. Items already sitting in the stash
are not what gets read. A name the producer placed in `stash` contradicts how the panels actually
work, so it is COUNTED AS CONTRADICTED and named — never folded into panel, never silently
dropped. [[feedback-contradiction-is-the-finding]]

MEASURED, before -> after, on his real journal:
    names 472 -> 472   panel 110 -> 87   floor 208 -> 216   chronicle 154 -> 154
    equipped (new) 3   contradicted (new) 12
    87 + 216 + 154 + 3 + 12 = 472 — every name accounted for, none invented.
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import extract_gap as EG  # noqa: E402

#: one frame, scene=stash, holding items from BOTH containers plus a floor item and an equipped
#: one — the exact shape his journal carries 56 times.
ROW = {
    "lane": "deep", "sessionId": "s_test_1",
    "names": ["In Inventory", "In Stash", "On Floor", "Worn", "Unplaced"],
    "scene": "stash",
    "names_loc": {"In Inventory": "inventory", "In Stash": "stash",
                  "On Floor": "floor", "Worn": "equipped"},
}


class TestAFrameLabelIsNotAnItemLocation(unittest.TestCase):

    def _counts(self, row):
        """Drive the real counter over one synthetic row. -> dict"""
        import json
        import tempfile
        d = tempfile.mkdtemp(prefix="framelabel.")
        p = os.path.join(d, "journal.jsonl")
        io.open(p, "w", encoding="utf-8").write(json.dumps(row) + "\n")
        import control_app as CA
        real = CA._journal_ring
        CA._journal_ring = lambda *a, **k: [p]
        try:
            out, _why = EG._named_sessions()
        finally:
            CA._journal_ring = real
        return (out or {}).get("s_test_1") or {}

    def test_each_name_is_counted_by_its_own_container(self):
        """THE LAW. Five names in ONE stash frame must land in five different places."""
        c = self._counts(ROW)
        self.assertEqual(c.get("names"), 5, "the row was not read at all: %r" % (c,))
        self.assertEqual(
            c.get("panel"), 1,
            "panel=%r. Only the INVENTORY item is a holding; if this is 4 or 5 the counter is "
            "still stamping the frame's label onto the whole list." % c.get("panel"))
        self.assertEqual(c.get("floor"), 1,
                         "the floor item was not counted as floor: %r" % (c,))
        self.assertEqual(c.get("equipped"), 1,
                         "the equipped item was not separated: %r" % (c,))

    def test_a_stash_placement_is_counted_as_contradicted_not_as_a_holding(self):
        """His ruling: items already in the stash are not what gets read, so `stash` as an item
        container contradicts how the panels work. It must be named, not absorbed."""
        c = self._counts(ROW)
        self.assertEqual(
            c.get("contradicted"), 1,
            "a name placed in `stash` was not counted as contradicted: %r. Folding it into panel "
            "would register an item the panels cannot have shown." % (c,))

    def test_an_unplaced_name_falls_back_to_the_frame_and_is_not_guessed(self):
        """154 of his 155 unplaced names are chronicle rows, where the frame is all that is known.
        The fallback must survive — and it must not invent a container for a placed name."""
        c = self._counts(ROW)
        self.assertEqual(
            c.get("panel", 0) + c.get("floor", 0) + c.get("equipped", 0)
            + c.get("contradicted", 0) + c.get("chronicle", 0)
            + c.get("unplaced", 0), 5,
            "the five names do not add up to five buckets: %r — a name was dropped or "
            "double-counted" % (c,))
        chron = dict(ROW, scene="chronicle", names=["A", "B"], names_loc={})
        chron["sessionId"] = "s_test_1"
        c2 = self._counts(chron)
        self.assertEqual(
            c2.get("chronicle"), 2,
            "unplaced names in a chronicle frame no longer fall back to the frame: %r. 154 of his "
            "journal's names are exactly this, and they would vanish." % (c2,))

    def test_the_real_journal_still_adds_up(self):
        """His data, not a fixture: every name must land in exactly one bucket."""
        out, why = EG._named_sessions()
        self.assertTrue(out, "no sessions read from the journal ring (%s) — UNKNOWN, not clean" % why)
        tot = {}
        for c in out.values():
            for k, v in c.items():
                tot[k] = tot.get(k, 0) + v
        buckets = sum(tot.get(k, 0) for k in
                      ("panel", "floor", "chronicle", "equipped", "contradicted", "unplaced"))
        self.assertEqual(
            buckets, tot.get("names"),
            "%d names but %d bucketed — a name was dropped or counted twice: %r"
            % (tot.get("names"), buckets, tot))


RED_PROOF = [
    {
        "why": "lets an UNPLACED name in a panel frame fall back to the frame and count as a "
               "holding — a container picked by coin-flip, since a panel frame shows the stash "
               "and the inventory at once",
        "file": "extract_gap.py",
        "find": '                            if sc in PANEL_SCENES:\n                                cur["unplaced"] += 1',
        "replace": '                            if sc in PANEL_SCENES:\n                                cur["panel"] += 1',
        "matches": 1,
    },
    {
        "why": "restores the defect exactly: one frame's label stamped onto the whole list of "
               "names, so floor and equipped items register as holdings again",
        "file": "extract_gap.py",
        "find": '                        elif _own == "inventory":\n                            cur["panel"] += 1',
        "replace": '                        elif _own in ("inventory", "floor", "equipped"):\n                            cur["panel"] += 1',
        "matches": 1,
    },
    {
        "why": "folds a `stash` placement into panel, registering an item the panels cannot have "
               "shown — his ruling says items already in the stash are not what gets read",
        "file": "extract_gap.py",
        "find": '                        elif _own == "stash":\n                            cur["contradicted"] += 1',
        "replace": '                        elif _own == "stash":\n                            cur["panel"] += 1',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
