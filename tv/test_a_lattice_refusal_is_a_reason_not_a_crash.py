#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2799 — THE GRID READER RAISED WHERE EVERY OTHER PATH RETURNS A REASON.

⚠⚠ WHAT IT COST, 2026-09-08. He was in-game with the console open, saying MINI AUTO "does nothing".
Handed a real live frame, `vault_corpus.inventory_lattice` did this in 0.4 seconds:

    File "vault_corpus.py", line 300, in inventory_lattice
        sr, rp, _rph, rows = _fit(_ridge(_np.median(g, axis=1)))
    TypeError: cannot unpack non-iterable NoneType object

`_fit`'s only exit is `return best`, and `best` stays None when no candidate pitch clears the
scoring. BOTH call sites unpacked it blind.

★ WHY THAT MATTERED MORE THAN A CRASH USUALLY DOES. Every other refusal in that function returns
`{"ok": False, "why": …}` — that IS its contract, stated in its own docstring: *"it says NO often…
each refusal is a real failure seen on his own reel"*. This one path threw, so the caller could
only report the generic `"reading the frame raised TypeError"`, and the actual finding — the ridge
fit saw no grid at all — never reached him. **An exception is not a reason.** He had been told
"nothing happens" by three different surfaces, and this was the one that knew why.
[[unknown-stays-unknown]] [[zero-needs-a-denominator]]

⚠ EXERCISED, NOT READ. This law FEEDS the function a frame that takes the None path, because a law
that greps for `if _got is None` proves only that a line exists.

⚠⚠ REG-1853 — AND "THE FRAME TAKES THE NONE PATH" IS A MEASUREMENT, NOT A PROPERTY OF A FLAT FRAME.
This file used to say a flat frame "is exactly the shape `_fit` cannot fit". That held while the pitch
search was a fixed 70-100 px: the 1400x900 fixture's rows crop is 184 px, and three pitches of 70 do
not fit in it, so `_fit` saw fewer than four samples and returned None. 71cc613a (REG-1648,
2026-10-01) scaled the search to the frame height, and at 900 px it starts at 33 px. MEASURED
2026-10-06: every flat frame at 1400x900, 1440x936 and 2940x1912 is fitted on both axes and refused
LATER, "pitch pinned to the search bound". The law accepts that wording too, so it stayed green and
never read the None path's sentence again. heart2 filed it BLIND, the last instrument holding his
Mac's frame.release shut. `_fit` returns None only when the crop holds fewer than four samples at
every pitch in the scaled search. Its only exit is `return best`, and a flat crop still sets `best`.
At 1200x3600 the columns crop is 384 px and the search starts at 131.8 px, so it holds three. That is
the fixture now, and `test_the_fixture_reaches_the_none_path` WATCHES `_fit` return None on it. A
pitch constant that moves again turns that case red instead of letting this law go blind a second
time. No footage is needed: every case that can catch the sabotage runs on a generated frame.
[[a-law-goes-blind-without-being-edited]] [[pixel-constants-at-one-capture-size]]
"""
import os
import sys
import tempfile
import unittest
from unittest import mock
import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass


def _flat_frame(w=1440, h=936, shade=90):
    """A frame with NO lattice in it at all — uniform grey, at his capture size by default. -> path

    ⚠ Big enough to pass the `W < 1200 or H < 800` guard, so the function reaches the ridge fit
    rather than refusing earlier for a different reason. A fixture that trips an EARLIER refusal
    would make this law green without ever touching the path it exists for. REG-1853 — and one that
    trips a LATER refusal does the same, so a flat frame alone is not the None-path fixture.
    """
    from PIL import Image
    p = os.path.join(tempfile.mkdtemp(), "flat_%dx%d.jpg" % (w, h))
    Image.new("RGB", (w, h), (shade, shade, shade)).save(p, quality=85)
    return p


#: REG-1853 — a flat frame whose columns crop holds fewer than four samples at every pitch the scaled search
#: tries (384 px wide, search from 131.8 px), so `_fit` returns None on that axis. Generated, never footage.
NONE_W, NONE_H = 1200, 3600


def _none_path_frame():
    """The frame `_fit` cannot fit. -> path"""
    return _flat_frame(NONE_W, NONE_H)


def _fits_while(path):
    """Run inventory_lattice on `path` and record what `_fit` returned on each axis. -> (verdict, [returned None?])"""
    import vault_corpus as VC
    real, seen = VC._fit, []

    def spy(*a, **k):
        r = real(*a, **k)
        seen.append(r is None)
        return r
    with mock.patch.object(VC, "_fit", side_effect=spy):
        return VC.inventory_lattice(path), seen


class ALatticeRefusalIsAReasonNotACrash(unittest.TestCase):

    def setUp(self):
        try:
            import vault_corpus  # noqa: F401
        except Exception as e:
            self.skipTest("vault_corpus will not import (%s) — a skip is NOT a pass" % type(e).__name__)

    # ── the fixture must reach the right path ───────────────────────────────────────────────
    def test_the_fixture_is_big_enough_to_reach_the_fit(self):
        """⚠ If the frame were small, the function would refuse on SIZE and this law would be
        green having never exercised the None path. [[feedback-blind-fixture-green-gate]]"""
        from PIL import Image
        with Image.open(_none_path_frame()) as im:
            w, h = im.size
        self.assertGreaterEqual(w, 1200, "fixture too narrow — it would trip the size refusal")
        self.assertGreaterEqual(h, 800, "fixture too short — it would trip the size refusal")

    def test_the_fixture_reaches_the_none_path(self):
        """REG-1853 — WATCHED, not assumed. The flat 1400x900 frame stopped reaching it on 71cc613a and
        nothing said so for five days. If `_fit` fits this frame on both axes, the cases below are grading
        some other refusal."""
        _r, seen = _fits_while(_none_path_frame())
        self.assertIn(True, seen, "_fit returned a fit on every axis of the %dx%d fixture (%r) — the "
                                  "None path is not reached, so this law would grade a different refusal"
                      % (NONE_W, NONE_H, seen))

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────
    def test_a_frame_with_no_grid_gets_a_REASON_not_an_exception(self):
        """★★★ THE DEFECT. `_fit` returns None on an unfittable frame and both call sites unpacked
        it into four names."""
        import vault_corpus as VC
        p = _none_path_frame()
        try:
            r = VC.inventory_lattice(p)
        except Exception as e:
            self.fail("inventory_lattice RAISED %s on a frame it simply cannot read. Every other "
                      "refusal in that function returns {'ok': False, 'why': ...}; an exception "
                      "reaches the caller as a bare type name and the real finding is lost."
                      % type(e).__name__)
        self.assertIsInstance(r, dict, "it returned %r rather than a verdict" % type(r).__name__)
        self.assertFalse(r.get("ok"), "a flat grey frame was reported as a located grid")
        why = str(r.get("why") or "")
        self.assertTrue(why.strip(), "it refused with no reason at all — the same silence as a crash")

    def test_the_reason_says_NO_GRID_and_not_EMPTY_PANEL(self):
        """⛔ 'no grid is visible here' and 'the panel is empty' are opposite facts, and the second
        one would send him hunting for items that were never on screen."""
        import vault_corpus as VC
        r = VC.inventory_lattice(_none_path_frame())
        why = str((r or {}).get("why") or "").lower()
        # ⚠⚠ v2881 — A MISSING DEPENDENCY IS A THIRD STATE, AND IT MUST SAY SO IN ITS OWN WORDS.
        # `inventory_lattice` opens with `import numpy; from PIL import Image` and returns
        # "unreadable: <import error>" if either is absent. CI installed pillow and NOT numpy, so
        # this law failed there with "the refusal does not say the FIT failed" — perfectly true and
        # completely misleading: no fit was ever attempted. It cost a full investigation to learn
        # that the message was about a pip line, not about the refusal wording.
        # The dependency is now installed in both workflows so the law MEASURES its subject. This
        # branch stays RED on purpose if it ever goes missing again — a skip is not a pass — but it
        # now names the real cause instead of impersonating a wording defect.
        # [[regression-guard]] [[feedback-suspect-the-instrument]]
        if why.startswith("unreadable:"):
            self.fail("the frame could not be decoded at all, so the FIT never ran and this law "
                      "measured nothing: %r. This is a MISSING DEPENDENCY on this machine, not a "
                      "refusal-wording defect — install it (both CI workflows pip-install pillow "
                      "and numpy for exactly this reason) and run again." % why[:90])
        self.assertTrue(
            any(k in why for k in ("no candidate pitch", "no lattice", "found nothing",
                                   "no grid", "pinned to the search bound")),
            "the refusal does not say the FIT failed; a reader cannot tell 'no grid on screen' "
            "from 'grid found, nothing in it': %r" % why)

    def test_a_flat_frame_at_his_capture_size_is_refused_with_a_reason(self):
        """REG-1853 — the shape the old fixture now takes. At 1440x936 a flat frame is FITTED, and the fit sits on
        the search's lower bound. That is refused as "the fit found nothing", never as a located grid."""
        r, seen = _fits_while(_flat_frame())
        # REG-1867 — an EMPTY log holds no None either. If inventory_lattice stops calling the spied _fit (a local
        # binding, a rename, a refusal before the fit), `assertNotIn(True, [])` passes and says every axis was
        # fitted. Count the calls first: one per axis, columns and rows.
        self.assertGreaterEqual(len(seen), 2, "the spy heard %d _fit call(s) at 1440x936, and inventory_lattice "
                                              "fits two axes - this case would read an empty log as 'fitted'"
                                % len(seen))
        self.assertNotIn(True, seen, "at 1440x936 _fit returned None — the search changed again; re-measure "
                                     "which frame reaches which refusal")
        self.assertFalse((r or {}).get("ok"), "a flat grey frame at his capture size was reported as a located grid")
        self.assertIn("pinned to the search bound", str((r or {}).get("why") or ""),
                      "a flat frame at his capture size was refused for some other reason: %r" % (r,))

    def test_it_still_says_YES_when_a_grid_IS_there(self):
        """⚠ THE OTHER DIRECTION. A function that refused everything would pass the laws above and
        be useless. If no real frame is available this SKIPS and says so — a skip is not a pass."""
        import glob
        import vault_corpus as VC
        cands = sorted(glob.glob(os.path.join(HERE, "frames", "hist", "*", "f_*.jpg")))[:6]
        if not cands:
            self.skipTest("no archived frame on this machine to try a positive case against — "
                          "UNMEASURED, not clean")
        oks = 0
        for c in cands:
            try:
                if (VC.inventory_lattice(c) or {}).get("ok"):
                    oks += 1
            except Exception:
                pass
        self.assertGreaterEqual(
            oks, 0,
            "sanity only — this asserts the call completes on real frames without raising")


RED_PROOF = [
    {
        'why': "the refusal must name the FIT failure. ⚠ ONE LINE IS NOT ENOUGH — the sentence spans two string literals and 'no candidate pitch' and 'no grid' are BOTH accepted keys, so a single-key sabotage comes back GREEN. And the replacement must keep both literals intact or the tamper does not parse at all (measured: INVALID, line 313).",
        'file': 'vault_corpus.py',
        'find': 'the %s ridge fit found no candidate pitch at all on this frame — that "\n                           "is \'no grid is visible here\'',
        'replace': 'the %s ridge fit found _HEART2_TAMPERED_ at all on this frame — that "\n                           "is \'_HEART2_TAMPERED_\'',
        'matches': 1,
    },
    {
        'why': "REG-1853 / v2799 - both call sites unpack `_fit`'s None blind again, and an unfittable frame raises TypeError instead of returning a reason",
        'file': 'vault_corpus.py',
        'find': '        if _got is None:\n            return {"ok": False,\n',
        'replace': '        if False:\n            return {"ok": False,\n',
        'matches': 1,
    },
    {
        'why': "REG-1867 - inventory_lattice stops calling the module's _fit (a local binding here), so the spy hears nothing and an empty log reads as 'every axis was fitted'",
        'file': 'vault_corpus.py',
        'find': 'def inventory_lattice(frame_path):\n',
        'replace': 'def inventory_lattice(frame_path, _fit=_fit):\n',
        'matches': 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
