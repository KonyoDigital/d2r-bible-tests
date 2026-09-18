# -*- coding: utf-8 -*-
"""v3312 (#65/#66) — EVERY SURFACE CAN SAY WHICH DOOR OPENED A REEL, AND UNKNOWN STAYS UNKNOWN.

Konyo: *"the shadow reels that get shadow recorder they too need to be within the river and seen
visually just like the others"*.

⚠⚠ THE FIRST HALF WAS ALREADY TRUE AND IT TOOK THREE WRONG INSTRUMENTS TO ESTABLISH THAT.
Shadow reaches its reel THROUGH `start_agent` (control_app.py:24134), so a shadow reel is an
ordinary reel — same hist dir, same index, same seal — and nothing in shelf_driver / river /
river_walk / reel_retention filters by door. They have always flowed every joint.

WHAT WAS MISSING IS THAT NO SURFACE COULD SAY WHICH ONES THEY WERE. river.py mentioned `door`
ZERO times. So shadow flowed INVISIBLY and "shadow contributed N" had no answer — which is exactly
how an evening of play producing ZERO shadow reels stayed hidden until he noticed the absence
himself (control_app.py:5887, corroborate.py:364).

MEASURED on tv/sessions.jsonl (5,169 rows): shadow 761 · onair 759 · mini 2, with 1,522 rows
carrying BOTH `sessionId` and `door`. Of his 19 reels: onair 7 · shadow 1 · **11 with no door row
at all**, because they predate the stamp.

⚠⚠ THOSE 11 ARE UNKNOWN AND MUST NEVER BECOME "onair". Absence of a record is not evidence of the
common case, and a manufactured provenance is worse than a missing one because nothing can tell it
apart from a real one afterwards. [[unknown-stays-unknown]] [[manual-tally-is-witness]]

⚠ ONE READER, NOT TWO. The river and the shelf both need this and v3308 is the standing lesson: the
eagle partition was written twice, drifted within an hour, and the screen said 9 while the engine
said 7. `reel_door` is the single definition. [[copy-drift]]

── #66, THE SAME THREAD ─────────────────────────────────────────────────────────────────────────
Pressing ON AIR while SHADOW rolls used to answer "already on air" — true about a reel, misleading
about WHOSE, and the reply carried `mode` while omitting the door. There is NO race: shadow refuses
to start on top of anything, and this branch spawns nothing. The defect was the SENTENCE.
⚠ It must keep refusing nothing and killing nothing: the fold runs at seal (v2071), so pre-empting
a rolling reel ORPHANS its frames.
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import reel_door as rd                                   # noqa: E402


class TestAReelSaysWhichDoorOpenedIt(unittest.TestCase):

    # ── the reader ───────────────────────────────────────────────────────────────────────────
    def test_a_doorless_reel_is_UNKNOWN_and_never_the_common_door(self):
        """⚠ THE ONE THAT MATTERS. 11 of his 19 reels predate the stamp."""
        dmap = {"s_1": "shadow", "s_2": "onair"}
        self.assertIsNone(
            rd.door_of("reel_s_999", dmap),
            "a reel with no door row resolved to a door. Absence of a record is not evidence of "
            "the common case, and once invented the provenance cannot be told from a real one.")
        counts = rd.split(["reel_s_1", "reel_s_2", "reel_s_999", "reel_s_998"], dmap)
        self.assertEqual(
            counts.get("unknown"), 2,
            "doorless reels were not counted as unknown: %r. Folding them into a door is "
            "manufacturing provenance." % (counts,))
        self.assertEqual(counts.get("shadow"), 1)
        self.assertEqual(counts.get("onair"), 1)

    def test_an_unreadable_journal_is_UNKNOWN_not_an_empty_map(self):
        """A journal that cannot be read must not read as 'no reel has a door'."""
        m, why = rd.door_map(os.path.join(HERE, "_no_such_journal_.jsonl"))
        self.assertEqual(m, {})
        self.assertTrue(why, "an unreadable journal returned an empty map with NO reason, so the "
                             "caller cannot tell 'nobody recorded a door' from 'nobody could "
                             "look'. [[zero-needs-a-denominator]]")
        self.assertIn("not on this machine", why)

    def test_the_say_line_names_the_unknowns_out_loud(self):
        s = rd.say({"onair": 7, "shadow": 1, "unknown": 11})
        self.assertIn("shadow 1", s)
        self.assertIn("11 UNKNOWN", s,
                      "the summary hides the unattributed reels, so a reader would take 8 as the "
                      "whole population: %r" % s)
        self.assertIn("not assumed onair", s,
                      "the line does not say WHY they are unknown, so the next reader may fill "
                      "them in: %r" % s)

    # ── the river ────────────────────────────────────────────────────────────────────────────
    def test_the_river_reports_the_split_and_never_dies_on_it(self):
        import river
        rows = river.trace()
        cap = [r for r in rows if r.get("joint") == "capture"]
        self.assertTrue(cap, "the river has no capture joint")
        cap = cap[0]
        self.assertIn(
            "doorsSay", cap,
            "the capture joint carries no door split, so the river still cannot say how many "
            "reels came by the shadow door — which is the whole of his ask.")
        self.assertTrue(str(cap.get("doorsSay") or "").strip(),
                        "doorsSay is empty; an empty string is not a reading")
        # ⚠ the split is DECORATION on a joint that graded itself. It must never change the grade.
        self.assertIn(cap["state"], ("carries", "dry", "unbuilt", "unknown", "CARRIES", "DRY",
                                     "UNBUILT", "UNKNOWN"),
                      "the capture joint's state is no longer a known verdict: %r" % cap["state"])

    # ── #66, the reply ───────────────────────────────────────────────────────────────────────
    def test_the_already_rolling_reply_names_the_door(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn(
            '"door": _rolling, "askedFor": _asked, "doorMatches": _same', src,
            "the already-rolling reply does not carry the door, so pressing ON AIR under a SHADOW "
            "reel is answered 'already on air' with nothing explaining why the session is stamped "
            "shadow. The reply carried `mode` and omitted the one field that mattered.")
        self.assertIn(
            "_rolling = _door_of_origin(_agent_origin)", src,
            "the reply maps origin->door inline instead of calling _door_of_origin, whose own "
            "docstring says the two vocabularies are 'joined HERE and nowhere else'. A second "
            "mapping is how the pair drifts until one side grows a fourth value. [[copy-drift]]")
        self.assertNotIn(
            "stop_agent(farewell=False)\n            return {\"ok\": True, \"msg\": \"a %s reel", src,
            "the reply now STOPS a rolling reel. It must refuse nothing and kill nothing: the fold "
            "runs at seal, so pre-empting a rolling reel orphans its frames.")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "resolving a doorless reel to a door manufactures provenance that was never recorded",
        "file": "tv/reel_door.py",
        "find": "    return (dmap or {}).get(sid)",
        "replace": '    return (dmap or {}).get(sid, "onair")',
        "matches": 1,
    },
    {
        "why": "folding unknown into a door hides the 11 reels that predate the stamp",
        "file": "tv/reel_door.py",
        "find": '            out["unknown"] += 1',
        "replace": '            out["onair"] = out.get("onair", 0) + 1',
        "matches": 1,
    },
    {
        "why": "a say line that drops the unknown count lets a reader take 8 as the whole population",
        "file": "tv/reel_door.py",
        "find": '        head += " · %d UNKNOWN (recorded before the door stamp; not assumed onair)" % unk',
        "replace": '        head += ""',
        "matches": 1,
    },
    {
        "why": "dropping the door from the already-rolling reply restores the misleading answer",
        "file": "tv/control_app.py",
        "find": '                    "door": _rolling, "askedFor": _asked, "doorMatches": _same,',
        "replace": "",
        "matches": 1,
    },
]
