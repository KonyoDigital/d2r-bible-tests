#!/usr/bin/env python3
"""THE FLEET cross-reference carries BITS, and the bits must never lie about which items they mean.

Konyo: "for me and my cuzin alone it should cross reference eachother based on what set items he has
that i dont... so its not messy."

The dangerous failure here is not a crash. It is a confident, wrong list: decode a mask against a
roster it was not built for and every bit lands on a neighbouring item, so the box tells him to go
farm things his cousin already has. That failure is silent and looks exactly like the feature
working, which is why the fingerprint tests below matter more than the arithmetic ones.
"""

import io
import json
import os
import re
import shutil
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import console_safe  # noqa: F401,E402
import fleet_mask as fm  # noqa: E402


class TestTheMaskRoundTrips(unittest.TestCase):

    def setUp(self):
        self.roster, self.fp = fm.load_roster()
        self.assertTrue(self.roster, "tv/set_roster.json did not load — every test below would be "
                                     "measuring an empty roster and passing for that reason")

    def test_his_real_roster_is_the_shape_the_feature_assumes(self):
        self.assertEqual(len(self.roster), 135, "the set roster is no longer 135 pieces; the "
                                                "fingerprint should have changed with it")
        self.assertEqual(len(self.fp), fm.FINGERPRINT_LEN)
        self.assertEqual(len(self.roster), len(set(self.roster)),
                         "a duplicate piece name means two bits claim the same item")

    def test_what_goes_in_comes_out(self):
        mine = self.roster[:120]
        got, why = fm.decode(fm.encode(mine, self.roster, self.fp), self.roster, self.fp)
        self.assertIsNone(why)
        self.assertEqual(got, mine)

    def test_the_whole_roster_and_none_of_it(self):
        for owned in ([], list(self.roster)):
            got, why = fm.decode(fm.encode(owned, self.roster, self.fp), self.roster, self.fp)
            self.assertIsNone(why)
            self.assertEqual(sorted(got), sorted(owned))

    def test_a_name_the_roster_does_not_have_is_ignored_not_crashed(self):
        m = fm.encode(["Not A Real Piece"] + self.roster[:3], self.roster, self.fp)
        got, _ = fm.decode(m, self.roster, self.fp)
        self.assertEqual(got, self.roster[:3])
        self.assertEqual(m["have"], 3, "`have` counted an item that is not on the roster")

    def test_it_is_small_enough_to_ride_a_heartbeat(self):
        m = fm.encode(self.roster, self.roster, self.fp)
        self.assertLessEqual(len(m["b"]), 32, "135 bits should be ~23 base64 chars; %d means the "
                                              "encoding grew and the beacon carries it every "
                                              "4 minutes" % len(m["b"]))


class TestAWrongRosterIsRefusedNotGuessed(unittest.TestCase):
    """The failure this whole module is shaped around."""

    def setUp(self):
        self.roster, self.fp = fm.load_roster()

    def test_a_different_fingerprint_refuses(self):
        m = fm.encode(self.roster[:10], self.roster, "0123456789ab")
        got, why = fm.decode(m, self.roster, self.fp)
        self.assertIsNone(got, "a mask built against a DIFFERENT roster was decoded anyway. Every "
                               "bit would land on a neighbouring item and the box would name real "
                               "pieces that are simply the wrong ones.")
        self.assertIn("different item roster", why)

    def test_a_mask_that_does_not_say_which_roster_refuses(self):
        m = fm.encode(self.roster[:10], self.roster, self.fp)
        m.pop("v")
        got, why = fm.decode(m, self.roster, self.fp)
        self.assertIsNone(got)
        self.assertIn("does not say which roster", why)

    def test_a_length_mismatch_refuses_rather_than_truncating(self):
        short = self.roster[:100]
        m = fm.encode(short, short, self.fp)          # same fingerprint, FEWER items
        got, why = fm.decode(m, self.roster, self.fp)
        self.assertIsNone(got, "a 100-item mask was read against a 135-item roster. The first 100 "
                               "would look right, which is what makes it dangerous.")
        self.assertIn("refusing rather than truncating", why)

    def test_a_truncated_body_refuses(self):
        m = fm.encode(self.roster, self.roster, self.fp)
        m["b"] = m["b"][:8]
        got, why = fm.decode(m, self.roster, self.fp)
        self.assertIsNone(got)
        self.assertIn("partial read", why)

    def test_an_unreadable_roster_is_not_an_empty_one(self):
        names, fp = fm.load_roster(path=os.path.join(HERE, "no_such_roster.json"))
        self.assertIsNone(names, "a missing roster came back as a LIST — every mask would encode "
                                 "all-zeros and the fleet would report that nobody owns anything")
        self.assertIsNone(fp)


class TestTheComparisonIsTheFeature(unittest.TestCase):

    def setUp(self):
        self.roster, self.fp = fm.load_roster()
        self.mine = self.roster[:120]          # his own 120/135
        self.theirs = self.roster[10:126]      # his cousin's 116/135

    def _m(self, owned):
        return fm.encode(owned, self.roster, self.fp)

    def test_his_own_numbers(self):
        c = fm.compare(self._m(self.mine), self._m(self.theirs), self.roster, self.fp)
        self.assertTrue(c["ok"])
        self.assertEqual(c["mineN"], 120)
        self.assertEqual(c["theirsN"], 116)
        self.assertEqual(len(c["theyHaveIDont"]), 6)
        self.assertEqual(len(c["iHaveTheyDont"]), 10)
        self.assertEqual(c["both"], 110)
        # "so its not messy" is the requirement: nothing they BOTH own may appear
        both = set(self.mine) & set(self.theirs)
        self.assertFalse(both & set(c["theyHaveIDont"]),
                         "an item they both own is listed as something to chase")
        self.assertFalse(both & set(c["iHaveTheyDont"]))

    def test_the_two_directions_are_not_the_same_list(self):
        c = fm.compare(self._m(self.mine), self._m(self.theirs), self.roster, self.fp)
        self.assertFalse(set(c["theyHaveIDont"]) & set(c["iHaveTheyDont"]),
                         "the same piece appears on both sides of the trade")

    def test_it_is_a_mirror(self):
        a = fm.compare(self._m(self.mine), self._m(self.theirs), self.roster, self.fp)
        b = fm.compare(self._m(self.theirs), self._m(self.mine), self.roster, self.fp)
        self.assertEqual(a["theyHaveIDont"], b["iHaveTheyDont"],
                         "the comparison is not symmetric, so the two of them would see different "
                         "answers to the same question")
        self.assertEqual(a["both"], b["both"])

    def test_a_machine_that_never_reported_is_UNKNOWN_not_ZERO(self):
        """The first time he opens the box, before his cousin has ever logged in."""
        c = fm.compare(self._m(self.mine), None, self.roster, self.fp)
        self.assertFalse(c["ok"], "a machine that has never reported was treated as owning "
                                  "nothing, so the box would say his cousin is missing all 135")
        self.assertIn("no mask", c["why"])
        # ⚠ v2456 — THIS USED TO PIN THE SENTENCE AND NOW PINS THE LAW. It asserted the literal
        # string "no mask reported", which held while the refusal blamed "that machine" for a
        # silence on EITHER side. Konyo's cousin read that message about his own missing mask and
        # concluded the other console was broken; both of them did. A test pinned to the wording
        # would have gone red on the fix and green on the defect. [[regression-guard]]
        self.assertIn("THEIR", c["why"], "a refusal must name WHICH side is silent — a message "
                                         "that does not is indistinguishable from a hang")

    def test_a_refusal_names_the_side_that_is_actually_silent(self):
        """Both directions, because the whole defect was that one noun served both."""
        mine_missing = fm.compare(None, self._m(self.theirs), self.roster, self.fp)
        self.assertFalse(mine_missing["ok"])
        self.assertIn("YOUR", mine_missing["why"])
        self.assertNotIn("THEIR", mine_missing["why"],
                         "the local side was silent and the message still accused the other one")
        theirs_missing = fm.compare(self._m(self.mine), None, self.roster, self.fp)
        self.assertFalse(theirs_missing["ok"])
        self.assertIn("THEIR", theirs_missing["why"])
        self.assertNotIn("YOUR side is", theirs_missing["why"])

    def test_either_side_unknown_makes_the_ANSWER_unknown(self):
        bad = self._m(self.theirs)
        bad["v"] = "ffffffffffff"
        for args in ((bad, self._m(self.theirs)), (self._m(self.mine), bad)):
            c = fm.compare(args[0], args[1], self.roster, self.fp)
            self.assertFalse(c["ok"], "one unreadable side still produced a complete answer — "
                                      "every item on the readable side would look like something "
                                      "the other is missing")
            self.assertTrue(c["why"])

    def test_identical_ledgers_produce_an_empty_box_not_an_error(self):
        c = fm.compare(self._m(self.mine), self._m(self.mine), self.roster, self.fp)
        self.assertTrue(c["ok"])
        self.assertEqual(c["theyHaveIDont"], [])
        self.assertEqual(c["iHaveTheyDont"], [])
        self.assertEqual(c["both"], 120)


class TestTheServerNeverLearnsAnItemName(unittest.TestCase):
    """functions/api/console.js states the boundary this preserves: "No item names ever cross this
    boundary — a roster says how many, never which." A mask keeps that true."""

    def setUp(self):
        self.roster, self.fp = fm.load_roster()

    def test_the_wire_shape_carries_no_names(self):
        m = fm.encode(self.roster[:50], self.roster, self.fp)
        w = fm.sanitize_for_wire(m)
        self.assertEqual(set(w), {"v", "n", "b", "have"})
        blob = repr(w)
        for name in self.roster[:50]:
            self.assertNotIn(name, blob, "an item name reached the wire shape")

    def test_it_refuses_anything_oversized_or_strange(self):
        good = fm.encode(self.roster, self.roster, self.fp)
        self.assertIsNotNone(fm.sanitize_for_wire(good))
        for bad in (None, {}, "x", {"v": "", "n": 135, "b": "AA"},
                    {"v": "a", "n": 0, "b": "AA"},
                    {"v": "a", "n": fm.MAX_BITS + 1, "b": "AA"},
                    {"v": "a", "n": 135, "b": "A" * 5000},
                    {"v": "a", "n": 135, "b": "not base64!!"},
                    {"v": "a", "n": 135, "b": ""}):
            self.assertIsNone(fm.sanitize_for_wire(bad),
                              "the wire accepted %r" % (bad,))

    def test_a_lying_have_count_is_dropped_not_stored(self):
        m = fm.encode(self.roster[:10], self.roster, self.fp)
        m["have"] = 9999
        w = fm.sanitize_for_wire(m)
        self.assertNotIn("have", w, "a `have` larger than the roster was stored as fact")


class TestTheWholeChainAgreesWithItself(unittest.TestCase):
    """THE JOINT, not the two ends. The mask is encoded in the BOARD (JavaScript), validated in the
    WORKER (JavaScript), and decoded in the CONSOLE (Python). Three languages, one bit order — and
    every one of them can be individually correct while the chain still produces a confident wrong
    list of items. [[the-unjoined-end]]

    These run the SHIPPED JavaScript out of the shipped files rather than a copy: the worker's
    sanitiser is sliced from functions/api/console.js and the board's encoder from control_app.py.
    A test that reimplements either one would agree with itself forever.
    """

    def setUp(self):
        self.roster, self.fp = fm.load_roster()
        if not shutil.which("node"):
            self.skipTest("node is not installed — the JS halves of the chain cannot be run")

    def _node(self, script):
        import subprocess
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False, encoding="utf-8") as fh:
            fh.write(script)
            path = fh.name
        try:
            out = subprocess.run(["node", path], capture_output=True, text=True, timeout=60)
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
        self.assertEqual(out.returncode, 0, "node refused the shipped code: %s" % out.stderr[:400])
        return json.loads(out.stdout)

    def test_the_board_encoder_and_the_python_encoder_produce_the_SAME_BITS(self):
        """If these two ever disagree, the console decodes his cousin's mask with a shifted bit
        order and names real pieces that are simply the wrong ones."""
        # v2329 — the anchors follow the code. board_set_mask() became board_mask(ledger) when the
        # cross-reference grew a second ledger, and _mask_cached() gained a parameter, so BOTH
        # anchors here named signatures that no longer exist and this case died on
        # "substring not found" rather than on anything about bit order. Anchored on the function
        # NAMES now, not on their argument lists, which is the part that was never the point.
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        i = src.index("def board_mask(")
        body = src[i:src.index("def _mask_cached(", i)]
        m = re.search(r"js = \((.*?)\n          % \(json\.dumps\(roster\)", body, re.S)
        self.assertIsNotNone(m, "the board encoder moved — this test is reading the wrong lines")
        # the JS now takes (roster, storeKey); the bit order is what this case is about, so the
        # store name is fed a placeholder and only the roster half is exercised.
        js = eval("(" + m.group(1) + ")") % (json.dumps(self.roster), '"d2r_setPieces"')  # noqa: S307

        # ⚠ A CONTIGUOUS PREFIX CANNOT TELL TWO BIT ORDERS APART, and my first version of this test
        # used one. roster[:120] sets every bit of bytes 0-14, so each byte is 0xFF whichever end
        # you fill from — I flipped the board encoder to MSB-first and this test stayed GREEN on the
        # single most dangerous defect the chain has. The pattern below is deliberately ragged so
        # the byte values differ under any reordering. [[feedback-blind-fixture-green-gate]]
        owned = [n for i, n in enumerate(self.roster) if (i * 7 + 3) % 11 < 4]
        self.assertTrue(4 < len(owned) < len(self.roster) - 4,
                        "the fixture owns %d of %d — too near an extreme to distinguish bit orders"
                        % (len(owned), len(self.roster)))
        got = self._node(
            "globalThis.localStorage={getItem:(k)=>k==='d2r_setPieces'?%s:null};\n"
            "globalThis.window={};\n"
            "globalThis.btoa=(s)=>Buffer.from(s,'binary').toString('base64');\n"
            "console.log(%s);" % (json.dumps(json.dumps(owned)), js))
        mine = fm.encode(owned, self.roster, self.fp)
        self.assertEqual(got["b"], mine["b"],
                         "the board and the console disagree about the BIT ORDER. Every decoded "
                         "name would be a neighbour of the right one.")
        self.assertEqual(got["have"], mine["have"])
        self.assertEqual(got["n"], mine["n"])

    def _worker(self, masks):
        src = io.open(os.path.join(HERE, "..", "functions", "api", "console.js"),
                      encoding="utf-8").read()
        start = src.index("(function (m) {", src.index("masks: "))
        fn = src[start:src.index("})(body.masks)", start) + 2]
        return self._node("const f = %s;\nconsole.log(JSON.stringify(%s.map(f)));"
                          % (fn, json.dumps(masks)))

    def test_the_worker_stores_a_good_mask_and_drops_every_bad_one(self):
        good = fm.encode(self.roster[:116], self.roster, self.fp)
        out = self._worker([
            {"sets": good},
            {"sets": dict(good, b="A" * 5000)},          # oversized
            None,                                        # absent
            {"sets": {"v": "x", "n": 135, "b": "!!"}},   # not base64url
            {"sets": {"v": "x", "n": 99999, "b": "AA"}},  # absurd length
            {"sets": dict(good, v="")},                  # no roster fingerprint
        ])
        self.assertTrue(out[0], "the worker DROPPED a valid mask — the feature would report 'no "
                                "mask reported yet' forever, politely and permanently")
        for i, bad in enumerate(out[1:], start=1):
            self.assertIsNone(bad, "the worker stored malformed mask #%d" % i)

    def test_a_mask_survives_the_worker_unchanged_in_MEANING(self):
        mine = fm.encode(self.roster[:120], self.roster, self.fp)
        theirs = fm.encode(self.roster[10:126], self.roster, self.fp)
        stored = self._worker([{"sets": theirs}])[0]["sets"]
        c = fm.compare(mine, stored, self.roster, self.fp)
        self.assertTrue(c["ok"])
        self.assertEqual((len(c["theyHaveIDont"]), len(c["iHaveTheyDont"]), c["both"]),
                         (6, 10, 110),
                         "the comparison changed after a round trip through the worker")

    def test_no_item_name_reaches_the_stored_record(self):
        """functions/api/console.js declares this boundary in its own words; a mask must not be the
        thing that quietly crosses it."""
        stored = self._worker([{"sets": fm.encode(self.roster, self.roster, self.fp)}])[0]
        blob = json.dumps(stored)
        for name in self.roster:
            self.assertNotIn(name, blob, "%r reached the server record" % name)
        self.assertEqual(set(stored["sets"]), {"v", "n", "b", "have"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
