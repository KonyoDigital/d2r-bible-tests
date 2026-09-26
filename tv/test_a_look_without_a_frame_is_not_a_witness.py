# -*- coding: utf-8 -*-
"""#246 L8 — A LOOK WITHOUT A FRAME, OR ONE THE READER DOUBTED, IS NOT A WITNESS.

His rule (2026-09-07): an item grounds on TWO looks agreeing. vault_retro.gate() counted a session from EVERY row
of a pile and tested the confidence floor on the pile's BEST row only. So Magefist — the one stash-witnessed item
in his vault — passed as "corroborated across 2 looks at conf 0.85" on this real pile:

    [{frame null, conf 0.0}, {frame f_…jpg, conf 0.85}]   (the shape; the ids below are invented)

one real look, plus a look nobody can open that the reader itself was not sure of at all. Its confidence lower
bound was 0.095.

WHAT THIS LAW HOLDS (the REAL gate, called):
  · each look qualifies ON ITS OWN — a frame to open AND its own conf ≥ the floor — and only qualifying looks count;
    Magefist's shape no longer passes, and the refusal says how many looks did not count and why;
  · two real framed looks still pass (the positive control — a gate that refuses everything is as broken);
  · the raw look count rides BESIDE the qualifying one (looksSeen), never instead of it;
  · the payload the board receives carries the gate's own verdict and a stamped confidence bound (Wilson,
    qualifying of seen) — STAMPED, never decisive: his 2-look ruling stays the bar, and moving it to Wilson 0.43
    (about three looks) is his call, not this law's.
RED_PROOF below.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import vault_retro as VR  # noqa: E402

#: his real Magefist pile, shape for shape (the session ids are invented, never his)
MAGEFIST = [{"session": "s_first_look", "frame": None, "conf": 0.0, "lane": "stash"},
            {"session": "s_second_look", "witness": "s_second_look#0",
             "frame": "f_second.jpg", "conf": 0.85, "lane": "stash"}]
TWO_REAL = [{"session": "s_a", "frame": "f_a.jpg", "conf": 0.9, "lane": "stash"},
            {"session": "s_b", "frame": "f_b.jpg", "conf": 0.85, "lane": "stash"}]


def _gate(ev):
    return VR.gate(ev, VR.KEEP_CONF_FLOOR, VR.KEEP_MIN_WITNESSES)


class ALookWithoutAFrameIsNotAWitness(unittest.TestCase):

    def test_magefists_real_pile_no_longer_passes(self):
        g = _gate(MAGEFIST)
        self.assertFalse(g["pass"], "one real look and one frameless conf-0.0 look passed as two: %r" % g)
        self.assertEqual(1, g["witnesses"], "the qualifying count is wrong: %r" % g)
        self.assertEqual(2, g["looksSeen"], "the raw look count was dropped instead of kept beside: %r" % g)
        self.assertIn("did not count", g["why"], "the refusal does not say a look was set aside: %s" % g["why"])

    def test_each_look_is_judged_on_its_own(self):
        framed_unsure = [dict(TWO_REAL[0]), dict(TWO_REAL[1], conf=0.3)]
        self.assertFalse(_gate(framed_unsure)["pass"], "an unsure framed look counted as a witness")
        frameless_sure = [dict(TWO_REAL[0]), dict(TWO_REAL[1], frame=None)]
        self.assertFalse(_gate(frameless_sure)["pass"], "a sure look with no frame to open counted as a witness")

    def test_two_real_looks_still_pass(self):
        g = _gate(TWO_REAL)
        self.assertTrue(g["pass"], "two real framed looks were refused — the gate now refuses everything: %r" % g)
        self.assertEqual(2, g["witnesses"])

    def test_the_payload_carries_the_verdict_and_a_stamped_bound(self):
        p = VR.apply_payload({"ok": True, "owned": [
            {"name": "Magefist", "lane": "stash", "kind": "item", "witnesses": MAGEFIST},
            {"name": "Nagelring", "lane": "stash", "kind": "item", "witnesses": TWO_REAL}]})
        items = dict((i["name"], i) for i in p["items"])
        self.assertIs(False, items["Magefist"]["gate"]["pass"])
        self.assertIs(True, items["Nagelring"]["gate"]["pass"])
        self.assertEqual(0.095, items["Magefist"]["gate"]["wilson"], "his measured 0.095 is not what is stamped")
        self.assertEqual(VR.KEEP_MIN_WITNESSES, items["Nagelring"]["gate"]["minLooks"])

    def test_the_bound_is_stamped_never_decisive(self):
        """Two real looks have a Wilson bound of 0.34 — under the 0.43 shadow floor — and still pass: the bar is
        his count, and a score that silently took over would repeal his ruling without asking him."""
        p = VR.apply_payload({"ok": True, "owned": [
            {"name": "Nagelring", "lane": "stash", "kind": "item", "witnesses": TWO_REAL}]})
        g = p["items"][0]["gate"]
        self.assertLess(g["wilson"], VR.KEEP_WILSON_FLOOR, "premise: two looks should sit under the shadow floor")
        self.assertIs(True, g["pass"], "the confidence bound became the bar — that is his call, not this code's")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#246 W3 - a look counts again whatever its own frame and confidence (Magefist passes on a frameless conf-0.0 look)",
        "file": "vault_retro.py",
        "find": "        return bool(e.get(\"frame\")) and _conf_of(e.get(\"conf\")) >= conf_floor\n",
        "replace": "        return True\n",
        "matches": 1,
    },
    {
        "why": "#246 W3 - the payload stops carrying the gate's verdict to the board",
        "file": "vault_retro.py",
        "find": "              \"gate\": _gate_of(r)}\n",
        "replace": "              }\n",
        "matches": 1,
    },
]
