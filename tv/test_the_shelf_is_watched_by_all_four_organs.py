# -*- coding: utf-8 -*-
"""THE SHELF MUST BE WATCHED BY ALL FOUR ORGANS, AND THE CORROBORATOR MUST BE ABLE TO REFUSE.

Konyo, 2026-09-13: *"connect it all to the heart of the console obviously all 4 organs so we have
a census on it"* — and, on why that order matters: *"first heart 2.0 then when you connect
everything to it it should alone flag and alone fix and alone we surgically do whats needed"*.

He was right, and the measurement proves it rather than agreeing with it. Before this, the shelf
had EIGHT of sixteen organ cells and **no corroborator on any surface**:

    shelf-cards     eagle ✅  watchdog ✗  doctor ✅  corroborator ✗
    river-strip     eagle ✅  watchdog ✗  doctor ✅  corroborator ✗
    reel.route      eagle ✅  watchdog ✅  doctor ✅  corroborator ✗
    _engine_driver  eagle ✗   watchdog ✅  doctor ✗   corroborator ✗

That absence is exactly how the shelf could print `19 frames · full video` on a card and
`0 FRAMES` on the dossier for THE SAME REEL and nothing noticed. An eagle watches cheaply, a
watchdog asks whether a thing is alive, a doctor asks whether a check passes — not one of them
compares two witnesses. On its first run the new corroborator reported **52 of 53 reels**
disagreeing, and named the odd witness: `frames` counts JOURNAL ROWS IN A GROUP, not frames of
film. [[label-outlived-referent]] [[the-unjoined-end]]

This file refuses four rots:
  1. the corroborator stops covering the shelf;
  2. the watchdog stops covering it;
  3. the corroborator loses the ability to say NO (a green organ that cannot refuse);
  4. an unwitnessable shelf reports as agreement instead of as unmeasured.
"""
import os
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))
SHELF_SURFACES = ("shelf-cards", "river-strip")


class TestTheShelfIsWatchedByAllFourOrgans(unittest.TestCase):

    def test_every_shelf_surface_carries_all_four_organs(self):
        import organ_matrix as OM
        rows, _why = OM.matrix()
        by = dict((r.get("surface"), r) for r in rows)
        checked = 0
        for s in SHELF_SURFACES:
            r = by.get(s)
            self.assertIsNotNone(r, "%s is no longer a registered surface" % s)
            cells = r.get("cells") or {}
            for organ in OM.ORGANS:
                checked += 1
                self.assertEqual("COVERED", cells.get(organ),
                                 "%s has no %s — the shelf must be watched by all four"
                                 % (s, organ))
        print("shelf organ cells asserted COVERED: %d" % checked)
        self.assertEqual(len(SHELF_SURFACES) * 4, checked)

    def test_the_corroborator_declares_its_surfaces_rather_than_being_guessed(self):
        """v3055 deleted a resolver that matched on the tail and invented 8 cells."""
        import shelf_corroborate as SC
        print("declared surfaces: %d -> %s" % (len(SC.SURFACES), list(SC.SURFACES)))
        for s in SHELF_SURFACES:
            self.assertIn(s, SC.SURFACES,
                          "%s must be DECLARED by the organ, never inferred from its name" % s)

    def test_the_corroborator_can_say_NO(self):
        """The refusal, on fixtures — a green organ nobody has seen refuse measures nothing."""
        import shelf_corroborate as SC
        agree = [{"sessionId": "s_a", "n": 1, "frames": 7, "footageN": 7}]
        differ = [{"sessionId": "s_b", "n": 2, "frames": 0, "footageN": 7}]

        def disk7(_sid, _hist=None):
            return 7
        real = SC._disk_frames
        try:
            SC._disk_frames = disk7
            ok = SC.corroborate(agree)
            bad = SC.corroborate(differ)
        finally:
            SC._disk_frames = real
        print("agreeing fixture  -> checked %s disagreed %s" % (ok["checked"], ok["disagreed"]))
        print("differing fixture -> checked %s disagreed %s" % (bad["checked"], bad["disagreed"]))
        self.assertEqual(1, ok["checked"])
        self.assertEqual(0, ok["disagreed"], "three agreeing witnesses must NOT be a finding")
        self.assertEqual(1, bad["checked"])
        self.assertEqual(1, bad["disagreed"], "a dossier disagreeing with card and disk MUST refuse")

    def test_an_unwitnessable_shelf_is_unmeasured_not_agreement(self):
        import shelf_corroborate as SC
        r = SC.corroborate([])
        print("empty shelf -> ok=%r checked=%s" % (r["ok"], r["checked"]))
        self.assertIsNone(r["ok"], "no witnessable reel must be UNKNOWN, never a clean bill")
        self.assertEqual(0, r["checked"])
        self.assertIn("UNMEASURED", r["say"].upper())

    def test_a_reel_with_no_film_is_not_witnessed_at_all(self):
        """One witness cannot corroborate anything — it must be excluded, not counted as agreeing."""
        import shelf_corroborate as SC
        real = SC._disk_frames
        try:
            SC._disk_frames = (lambda _sid, _hist=None: None)
            r = SC.corroborate([{"sessionId": "s_gone", "n": 3, "frames": 5, "footageN": 5}])
        finally:
            SC._disk_frames = real
        print("filmless reel -> checked %s" % r["checked"])
        self.assertEqual(0, r["checked"],
                         "a reel whose film is gone has ONE witness and must not be counted")

    def test_the_watchdog_row_is_registered_and_names_the_shelf(self):
        import health_engine as HE
        self.assertIn("shelfWitness", HE.WATCHES, "the flag must declare what it watches")
        for s in SHELF_SURFACES:
            self.assertIn(s, HE.WATCHES["shelfWitness"])
        names = [getattr(f, "__name__", "") for f in HE.CHECKS]
        print("watchdog checks registered: %d" % len(names))
        self.assertIn("check_shelf_witnesses", names,
                      "a check nobody runs is an unjoined end")


RED_PROOF = [
    {
        "why": "the corroborator stops covering the shelf, so the surface that printed 19 frames "
               "and 0 FRAMES for one reel goes back to having nothing that compares witnesses",
        "file": "organ_matrix.py",
        "find": "            import shelf_corroborate as _sc\n"
                "            for _s in (_sc.SURFACES or ()):\n"
                "                names.add(str(_s))",
        "replace": "            pass",
        "matches": 1,
    },
    {
        "why": "the watchdog check is unregistered — built at both ends, joined at neither",
        "file": "health_engine.py",
        "find": "          check_shelf_witnesses,",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "the corroborator can no longer refuse: every set of witnesses reads as agreeing, "
               "which is a green organ that measures nothing",
        "file": "shelf_corroborate.py",
        "find": "    return len(set(seen)) > 1",
        "replace": "    return False",
        "matches": 1,
    },
    {
        "why": "an unwitnessable shelf reports ok instead of UNMEASURED — a clean bill with no "
               "denominator behind it",
        "file": "shelf_corroborate.py",
        "find": '        out["ok"] = None',
        "replace": '        out["ok"] = True',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
