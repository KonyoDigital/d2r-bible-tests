#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2815 (#45) — THE PROOF RULE HAS SHIPPED SINCE v2364 AND NOTHING EVER CALLED IT.

`frame_ref` states the rule in its own docstring: "a frame cited by a row that NAMED an item is
PROOF of that claim and may not be deleted while the claim stands." AST-confirmed 2026-09-09: the
only callers of cited_frames/prunable/Index were frame_ref itself and one test. `reel_retention`
did not even import frame_ref — and its apply_plan() does shutil.rmtree() on the WHOLE reel
directory once any row from that reel reaches the vault ledger.

MEASURED on his tree the same day: of 10,318 citations across uniques+sets, **739 cited frames
already resolve to nothing on disk**. The proof for those claims is gone. 9 reels still hold proof;
3 of them are among the 41 on disk.

★★ THE ADAPTER IS THE WHOLE FIX, AND WITHOUT IT THIS GUARD PROTECTS NOTHING.
`cited_frames()` decides a row is proof via `r.get("items") or r.get("names")`. chron_evidence.json
does not store it that way — the item name is the KEY:

    {"uniques": {"Djinn Slayer": [{"reel": ..., "frame": ...}, ...]}}

Wire the guard straight onto that and every row falls through to `other` (fair game), `named` comes
back EMPTY, and the deleter keeps deleting proof while carrying a protection that reads correct.
That is the failure this file exists to make impossible. [[the-unjoined-end]]
[[feedback-blind-fixture-green-gate]]

⚠ STATED LIMIT: on his tree today candidates=0 (everything is held by other rules), so this proves
the rule RUNS (coverage=3) and cannot yet prove on live data that it PREVENTS a deletion. The
fixture below supplies the case his data does not. [[gate-blind-to-unexercised-input]]
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

import reel_retention as RR  # noqa: E402
import frame_ref as FR  # noqa: E402


class TestTheDeleterWillNotDestroyAReceipt(unittest.TestCase):

    def setUp(self):
        # ⚠ never his live tv/ — a fixture that writes into real evidence is a defect this repo
        # produced once already tonight. [[feedback-fixtures-never-touch-live-data]]
        self.root = tempfile.mkdtemp(prefix="proof_gate.")
        self.hist = os.path.join(self.root, "hist")
        os.makedirs(os.path.join(self.hist, "reel_A"))
        os.makedirs(os.path.join(self.hist, "reel_B"))
        io.open(os.path.join(self.hist, "reel_A", "f_1.jpg"), "w").write("x")
        io.open(os.path.join(self.hist, "reel_B", "f_2.jpg"), "w").write("x")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_the_adapter_marks_a_citation_as_NAMED(self):
        """The decisive one — and it must run reel_retention's OWN adapter, not frame_ref directly.

        ⚠ THE FIRST CUT OF THIS TEST WAS BLIND AND HEART 2.0 SAID SO. It called
        FR.cited_frames() with hand-built rows already carrying `items`, so deleting the adapter's
        `"items": [item]` in reel_retention changed nothing it could observe: the gate stayed
        GREEN through its own defeat. A gate that exercises the LIBRARY instead of the WIRING
        proves the library. [[feedback-blind-fixture-green-gate]]
        """
        os.environ["TV_HIST"] = self.root
        try:
            with io.open(os.path.join(self.root, "chron_evidence.json"), "w",
                         encoding="utf-8") as fh:
                json.dump({"uniques": {"Djinn Slayer": [
                    {"reel": "reel_A", "frame": "f_1.jpg", "conf": 0.9}]}}, fh)
            rows, why = RR._evidence_rows()
            self.assertTrue(rows, "the adapter read no rows from the fixture store (%s)" % why)
            self.assertIn("items", rows[0],
                          "the adapter drops the claimed item name, so cited_frames() will file "
                          "every citation as 'fair game' and the deleter takes the proof with it "
                          "— while this guard still reads correct")
            named, other = FR.cited_frames(rows)
            self.assertEqual(named, {"f_1.jpg"}, "the citation did not register as NAMED")
            self.assertEqual(other, set())
        finally:
            os.environ.pop("TV_HIST", None)

    def test_a_row_without_the_item_name_protects_nothing(self):
        """The shape chron_evidence actually has BEFORE the adapter — proof this is not academic."""
        raw = [{"frameId": "f_1.jpg", "reel": "reel_A"}]     # item name is the KEY, not a field
        named, other = FR.cited_frames(raw)
        self.assertEqual(named, set(),
                         "if this ever starts returning a name, the adapter is no longer load "
                         "bearing and this gate's premise must be re-measured")
        self.assertEqual(other, {"f_1.jpg"})

    def test_a_reel_holding_a_cited_frame_is_named_by_proof_reels(self):
        rows = [{"frameId": "f_1.jpg", "reel": "reel_A", "items": ["Djinn Slayer"]}]
        named, _ = FR.cited_frames(rows)
        idx = FR.Index(self.hist)
        held = set()
        for fid in named:
            hit = idx.resolve(fid)
            if hit:
                rel = os.path.relpath(hit, self.hist) if os.path.isabs(hit) else hit
                held.add(str(rel).replace("\\", "/").split("/")[0])
        self.assertIn("reel_A", held,
                      "the reel holding the cited frame was not identified — note resolve() "
                      "returns a path ALREADY RELATIVE to the index root; running relpath over it "
                      "again collapses every hit to '..' and reports one fake reel")
        self.assertNotIn("reel_B", held, "an uncited reel was held — that would stall the prune")

    def test_cannot_tell_means_HOLD_not_delete(self):
        """An unknown must never release a reel. Deletion is the direction with no way back.
        ⚠ STRICTLY None. The first cut asserted `held is None or held == set()`, which is true
        for BOTH outcomes — so the tamper that turns CANNOT TELL into an empty set could not fail
        it, and Heart 2.0 correctly reported the proof BLIND. An empty set means "nothing is
        cited, delete freely"; None means "I could not find out". Conflating them is the whole
        defect. [[unknown-stays-unknown]]
        """
        # ⚠ THE STORE MUST EXIST AND BE UNREADABLE. An ABSENT store is a world with no claims —
        # an empty answer, not an unknown one — and treating it as unknown held every reel in an
        # isolated fixture and made the prune untestable (four gates said so). The genuine unknown
        # is a chronicle that IS there and will not parse: something may be cited and we cannot see
        # it. That is the case this law is about.
        os.environ["TV_HIST"] = self.root
        try:
            with io.open(os.path.join(self.root, "chron_evidence.json"), "w",
                         encoding="utf-8") as fh:
                fh.write("{not json at all")
            held, why = RR.proof_reels(self.hist)
        finally:
            os.environ.pop("TV_HIST", None)
            try:
                os.remove(os.path.join(self.root, "chron_evidence.json"))
            except OSError:
                pass
        self.assertIsNone(held,
                          "an unreadable world returned %r instead of None — an empty set reads "
                          "as 'nothing is cited, delete freely'" % (held,))
        self.assertTrue(why, "CANNOT TELL was returned without saying why")

    def test_the_rule_is_in_the_vocabulary(self):
        """A hold with no rule name cannot appear in coverage/neverFired, so it cannot be audited."""
        self.assertIn("holds-proof", RR.RULES,
                      "holds-proof is not a declared rule, so plan()'s own coverage accounting "
                      "can never report whether it fired")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "dropping the adapter's item name is the silent no-op — named goes empty and the "
               "deleter takes the proof while the guard still reads correct",
        "file": "reel_retention.py",
        "find": '                rows.append({"frameId": fid, "reel": c.get("reel"), "items": [item]})',
        "replace": '                rows.append({"frameId": fid, "reel": c.get("reel")})',
        "matches": 1,
    },
    {
        "why": "turning CANNOT TELL into an empty set deletes on an unknown",
        "file": "reel_retention.py",
        "find": "        return None, why",
        "replace": "        return set(), why",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
