# -*- coding: utf-8 -*-
"""2026-09-27 — THE LANE COUNTED GROKBOT'S ACTS AS "NO LEAD VERB", SO THE HOOK SAID NOTHING WAS OWED.

HIS ORDER: "also make sure to optimize the #230 and #231 comments".

MEASURED: handoff._classify read the verb from the FIRST meaningful line. CLAUDE.md §4 makes the FIRST line the seat
tag ("the TAG ON THE FIRST LINE is the only thing that identifies a seat"), so every GrokBot comment - which opens
"GB-L" - was filed "pre-v2 (no lead verb)". On 2026-09-27 the LANES hook printed "0 ACT/ASK owed" on every prompt
while two ACTs for Claude sat on #230 (5854814442 at 09:51, 5855160685 at 10:46).

DRIVEN on the body shapes the lane actually carries (taken from #230's own history): a tag then an ACT, a tag then a
LOOKED tick, an emoji-led LOOKED, an emoji-led STATE, a bare FYI, a routing header then an ASK, and an unknown shape
that must STAY unknown. RED_PROOF below.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import handoff as H  # noqa: E402

TODAYS_ACT = ("GB-L\n**ACT** — Close inventory-grid parity gap vs Maxroll D2 planner (charms / Anni / sunders). "
              "Evidence: GB-L pack `inv-grid-verify-20260927T103001Z`.\n\n### Required behavior\n1. Click empty cell")
TODAYS_ACT_2 = ("GB-L\n**ACT** · for Claude · pack `cl174-verify-20260927T093412Z` · v3517 HEAD `1abddaf2` · Elad: perfect "
                "inventory charms")
STANDING_TICK = ("GB-L\n**LOOKED** · pack `visual-pass-20260927T100757Z-NATIVE` · seat **GB-L** · DISPLAY **:4**\n\n"
                 "### ASK digests\n- **#37 board_build** · ...")


class TheLaneCountsWhatGrokBotOwes(unittest.TestCase):

    def test_a_tagged_act_is_an_act(self):
        for body in (TODAYS_ACT, TODAYS_ACT_2):
            verb, line = H._classify(body)
            self.assertEqual(verb, "ACT", "GrokBot's ACT for Claude read as %r - the hook says nothing is owed" % verb)
            self.assertTrue(line.startswith("ACT"), line)

    def test_a_routing_header_then_an_ask_is_an_ask(self):
        self.assertEqual(H._classify("# GB-L-n — GrokBot (Linux native) → Claude\n\nASK — which store holds sets?")[0],
                         "ASK")

    def test_the_other_seats_tags_are_not_the_verb(self):
        # Measured on #230 after the GB-L fix shipped: these two openers are the tags Claude and
        # the Mac code seat actually write, and both were still filed pre-v2, so the ACT under
        # them never counted.
        self.assertEqual(H._classify("CLAUDE → GB-L\nACT — verify v3519 live")[0], "ACT")
        self.assertEqual(H._classify("GROK → GB-L\nACT — read the live console")[0], "ACT")
        self.assertEqual(H._classify("CLAUDE → GB-L\nFYI — received")[0], "FYI")
        self.assertEqual(H._classify("GROK → GB-L\nFYI — looked")[0], "FYI")
        self.assertEqual(H._classify("GROK is the model and this line is prose")[0], "?",
                         "a sentence that merely starts with GROK was skipped as a seat tag")

    def test_a_standing_tick_owes_nothing(self):
        for body in (STANDING_TICK, "👀 LOOKED · NATIVE · 2026-09-18 ~22:45 IDT", "📍 STATE — GrokBot (Linux native)",
                     "FYI — Mac TV DIABLO white well cleared this tick."):
            self.assertEqual(H._classify(body)[0], "FYI", "an observation was counted as %r" % H._classify(body)[0])

    def test_an_unknown_shape_stays_unknown(self):
        self.assertEqual(H._classify("## The role of this seat — what is true today")[0], "?",
                         "a body with no verb was given a priority it never declared")
        self.assertEqual(H._classify("")[0], "?")
        self.assertEqual(H._classify("GB-L\n\nACTUALLY this is prose")[0], "?",
                         "'ACTUALLY' was read as the verb ACT")

    def test_the_hook_line_counts_it(self):
        rows = [{"body": TODAYS_ACT}, {"body": STANDING_TICK}]
        verbs = [H._classify(r["body"])[0] for r in rows]
        self.assertEqual(sum(1 for v in verbs if v in H.OWED), 1, "the owed count the hook prints is wrong: %r" % verbs)


RED_PROOF = [
    {
        "why": "2026-09-27 - the seat tag is read as the lead line again: every GrokBot ACT is 'pre-v2', the hook says 0 owed",
        "file": "handoff.py",
        "find": "        if skipped < 2 and _SEAT_TAG_RX.match(line):\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - a standing LOOKED/STATE tick is 'pre-v2' again, so real ACTs drown among 30 unknowns a day",
        "file": "handoff.py",
        "find": "_OBSERVED = (\"LOOKED\", \"STATE\")\n",
        "replace": "_OBSERVED = ()\n",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - a word that merely STARTS with a verb ('ACTUALLY') is read as the verb",
        "file": "handoff.py",
        "find": "            if head.startswith(verb) and not head[len(verb):len(verb) + 1].isalnum():\n",
        "replace": "            if head.startswith(verb):\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
