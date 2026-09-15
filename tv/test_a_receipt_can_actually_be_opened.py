#!/usr/bin/env python3
"""A RECEIPT CAN ACTUALLY BE OPENED — presence of a button is not a working feature.

HIS ASK behind #96: he wanted to see the evidence, not be told it exists — *"i want to be able
to see the evedice too"*. The vault row grew a receipt eye (◉) that fetches /api/evidence and
opens the strongest sighting's frame.

⚠⚠ IT SHIPPED DEAD, AND EVERY INSTRUMENT SAID IT WAS FINE. Measured 2026-09-15: the receipt
resolved **4 of 450** banked best-frames, and those four were coincidences. The handler had the
reel on the sighting, built a FLAT frame id one line before it was needed, and threw the reel
away; both legs of the viewer's fallback chain then addressed `hist/<ms>.jpg` while every banked
evidence frame lives at `hist/reel_<sid>/f_<ms>.jpg`. Every click opened "frame missing (agent
off + no archive)". After the fix: **126 of 450** — the remaining 324 are genuinely pruned
footage, which is honest absence.

THE HEALTH ORGAN WAS GREEN THROUGHOUT, and that is the more important half. `check_vault_receipts`
asked whether the row markup CONTAINS a receipt hook. It did. Presence and resolution are
different questions, and only one of them is the feature. A check that cannot tell them apart
certifies a dead lane forever. [[the-green-that-lies]] [[the-unjoined-end]]

WHAT THIS PINS:
  1. the handler keeps the reel and addresses a reel-scoped path
  2. the viewer tries a caller-supplied exact path before its own guesses
  3. the organ MEASURES resolution, and goes WARN when nothing resolves
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _console_safe_enable
    _console_safe_enable()
except Exception:
    pass
BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")


def _bible():
    with io.open(BIBLE, encoding="utf-8") as fh:
        return fh.read()


def _between(src, start, end, what):
    """Both ends anchored. A fixed-size window past the region reads as ABSENT and would let
    this law pass on a file that no longer contains the handler. [[source-reading-guard]]"""
    i = src.find(start)
    assert i >= 0, "%s: opening anchor is gone" % what
    j = src.find(end, i)
    assert j > i, "%s: closing anchor is gone" % what
    return src[i:j + len(end)]


class AReceiptCanActuallyBeOpened(unittest.TestCase):

    def test_the_handler_keeps_the_reel(self):
        """The reel is on the sighting. Dropping it makes the frame unaddressable."""
        h = _between(_bible(), "var fid = String(best.frame)",
                     "window._tvdOpenFrame(fid,", "the receipt handler")
        # strip JS comments so the claim cannot be satisfied by the prose that explains it
        code = re.sub(r"/\*.*?\*/", " ", h, flags=re.S)
        uses = len(re.findall(r"best\.reel", code))
        print("   best.reel uses in the handler (comments stripped): %d" % uses)
        self.assertTrue(uses, "the handler drops the reel, so every frame it asks for is "
                              "addressed flat and cannot resolve")
        self.assertIn("frames/hist/", code,
                      "the handler must build a reel-scoped frame path")

    def test_the_viewer_tries_the_exact_path_first(self):
        """A caller that knows the path should not have to guess through a chain built for a
        different addressing scheme."""
        v = _between(_bible(), "window._tvdOpenFrame = function", "img.src = _chain[0];",
                     "the frame viewer")
        code = re.sub(r"/\*.*?\*/", " ", v, flags=re.S)
        code = re.sub(r"(?m)^\s*//.*$", " ", code)
        print("   viewer reads meta.src: %s | builds a chain: %s"
              % ("meta.src" in code, "_chain" in code))
        self.assertIn("meta.src", code,
                      "the viewer ignores a caller-supplied exact path, so a caller that KNOWS "
                      "where the frame lives cannot say so")
        self.assertIn("_chain", code, "the fallback chain is gone")

    def test_the_organ_measures_resolution_not_presence(self):
        """The check that was green over a join which never once worked."""
        import health_engine as he
        self.assertTrue(hasattr(he, "_receipts_resolve"),
                        "the organ has no way to ask whether a receipt resolves")
        got, tested = he._receipts_resolve()
        print("   receipts resolve: %d of %d" % (got, tested))
        self.assertGreater(tested, 0,
                           "the resolver could not read the evidence bank, so it reported a "
                           "clean-looking zero - the exact wrong-zero it exists to prevent")
        self.assertGreater(got, 0,
                           "not one banked best-frame resolves: the receipt is wired to an "
                           "address nothing lives at")

    def test_the_organ_goes_warn_when_nothing_resolves(self):
        """A resolution of 0 out of many is a broken address, not pruned footage: pruning takes
        frames one at a time and never lands on exactly all of them."""
        import health_engine as he
        real = he._receipts_resolve
        try:
            he._receipts_resolve = lambda *a, **k: (0, 450)
            row = he.check_vault_receipts()
            print("   with 0-of-450 resolving -> state=%r" % row.get("state"))
            self.assertEqual(row.get("state"), "warn",
                             "the organ still reports healthy while no receipt can be opened")
            self.assertIn("NOT ONE", row.get("line") or "",
                          "the row must SAY the receipts cannot open, not merely rank itself")
        finally:
            he._receipts_resolve = real

    def test_a_pruned_frame_is_not_called_broken(self):
        """324 of his 450 best-frames are pruned. That is honest absence and must not read as a
        defect, or the row cries wolf on a healthy system. [[unknown-stays-unknown]]"""
        import health_engine as he
        real = he._receipts_resolve
        try:
            he._receipts_resolve = lambda *a, **k: (126, 450)
            row = he.check_vault_receipts()
            print("   with 126-of-450 resolving -> state=%r" % row.get("state"))
            self.assertNotEqual(row.get("state"), "warn",
                                "partial resolution is the normal state of a pruned archive")
            self.assertIn("pruned", row.get("line") or "",
                          "the row must name pruning as the reason the rest are absent")
        finally:
            he._receipts_resolve = real


if __name__ == "__main__":
    unittest.main(verbosity=2)
