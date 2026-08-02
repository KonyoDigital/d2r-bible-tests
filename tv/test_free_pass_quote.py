"""v1596 — THE FREE PASS MUST NOT UNDER-QUOTE.

Grok's audit of the console flagged one line: *"FREE PASS under-quotes spend (_probe -> None ->
pagesRead 0)"*. It was right, and the shape of the bug is worth stating because it will grow back
the moment someone "simplifies" the cost probe.

A retro sweep spends on TWO lanes:

    classify(frame)      once per candidate still-run  - "is this screen worth reading?"
    reader(frame, kind)  once per DISTINCT page inside an accepted run - the actual read

The free pass priced the sweep by handing it stub lanes and counting what the stubs were asked to
do. But the classify stub returned None, and None means "not a page I can read" - so both sweeps
correctly skipped the read stage for every single run. `pagesRead` was therefore not merely wrong,
it was STRUCTURALLY PINNED AT ZERO: no footage, however rich, could have produced a non-zero page
count on that route. The quote counted the cheaper lane and printed it as the total.

Measured on the two-reel fixture below before the fix: quoted 2, actual 6. It told him "83% cheaper
than reading every frame" where the truth was 50%, and it did it on the exact panel whose comment
reads *"He was told '97% cheaper'; this is where he checks it rather than believing it."*

WHAT THESE TESTS PIN, and deliberately not more:

  THE DIRECTION, NOT THE NUMBER. The quote is an UPPER BOUND - it prices every candidate run as if
  it were readable, and a real sweep skips the ones that turn out to be a lobby. So the law is
  quote >= actual, asserted against a REAL counted sweep over the same fixture. Pinning an exact
  figure would just re-freeze today's grouping constants and break on every honest re-tune.

  BOTH LANES ARE IN THE HEADLINE. wouldRead == wouldClassify + wouldReadPages. A breakdown that does
  not add up to the number shown is worse than no breakdown.

  PAGES CAN ACTUALLY BE NON-ZERO. The regression test proper. If someone restores `return None`,
  every other assertion here still passes on an empty fixture - so this one insists that footage
  which a real sweep WOULD read is footage the quote charges for.

  STILL FREE. The whole point of the route. If a probe ever reaches a model, the "0 calls spent"
  label on the panel becomes a lie and he stops trusting the number entirely.
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import console_safe  # noqa: F401,E402 - non-ASCII in failure messages must survive a odd console

try:
    from PIL import Image
except Exception:                                    # pragma: no cover - env without Pillow
    Image = None

import chronicle_retro as cr  # noqa: E402
import vault_retro as vr  # noqa: E402
import control_app as ca  # noqa: E402


def _reel(root, sid, frames=6, scrolled=2):
    """One sealed reel of REAL jpegs: a held panel that then scrolls.

    The scroll matters. A held-still page is one page no matter how many frames it spans, so a
    fixture of identical frames would read as a single page and the under-quote would be off by
    one instead of by four - small enough to look like rounding. `scrolled` frames at the end look
    different enough for _distinct() to call them further pages, which is what makes the reader
    lane the BIGGER half of the bill, exactly as it is on his own footage.
    """
    d = os.path.join(root, "reel_" + sid)
    os.makedirs(d, exist_ok=True)
    rows = []
    for i in range(frames):
        im = Image.new("RGB", (64, 64))
        px = im.load()
        shift = 90 if i < frames - scrolled else 10
        for y in range(64):
            for x in range(64):
                px[x, y] = ((x * 3 + shift) % 256, (y * 5) % 256, ((x + y) * 7) % 256)
        nm = "f%03d.jpg" % i
        im.save(os.path.join(d, nm), "JPEG", quality=92)
        rows.append({"f": nm, "ts": 1700000000000 + i * 1000})
    with open(os.path.join(d, "index.json"), "w", encoding="utf-8") as fh:
        json.dump({"sessionId": sid, "frames": rows, "focus": "stash"}, fh)
    return d


@unittest.skipIf(Image is None, "Pillow absent - the sweeps cannot group frames without it")
class FreePassQuoteBase(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.mkdtemp(prefix="freepass_")
        for sid in ("s1", "s2"):
            _reel(self.td, sid)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.td, ignore_errors=True)


class TestVaultFreePass(FreePassQuoteBase):
    def quote(self):
        q = ca.vault_scan_cost(self.td)
        self.assertTrue(q.get("ok"), "the fixture must price: %r" % (q.get("why"),))
        return q

    def actual(self):
        """A REAL sweep over the same reels, with lanes that count instead of spending."""
        n = {"classify": 0, "reader": 0}

        def classify(path):
            n["classify"] += 1
            return {"surface": "stash"}

        def reader(path, surface):
            n["reader"] += 1
            return {"items": [{"name": "Ral Rune", "count": 3, "conf": 0.9}], "conf": 0.9}

        vr.sweep(cr.reel_dirs(self.td), sig=vr.DEFAULT_SIG, classify=classify, reader=reader)
        return n

    def test_the_quote_is_never_below_the_real_spend(self):
        q, n = self.quote(), self.actual()
        real = n["classify"] + n["reader"]
        self.assertGreaterEqual(
            q["wouldRead"], real,
            "THE BUG: the free pass quoted %d model calls for footage a real sweep spends %d on "
            "(%d classify + %d reader). Quoting low spends money he never agreed to - the quote is "
            "the only thing standing between him and a sweep he did not price."
            % (q["wouldRead"], real, n["classify"], n["reader"]))

    def test_the_reader_lane_is_actually_charged_for(self):
        """The regression proper. Restore `return None` in the probe and this is what fails."""
        q, n = self.quote(), self.actual()
        self.assertGreater(n["reader"], 0, "fixture is wrong: a real sweep must read pages here")
        self.assertGreater(
            q["wouldReadPages"], 0,
            "a real sweep reads %d pages on this footage and the quote charged for 0. This is the "
            "v1596 defect exactly: a classify stub answering None makes sweep() skip the read stage, "
            "so pagesRead cannot ever be non-zero no matter how much film he has." % n["reader"])

    def test_the_breakdown_adds_up_to_the_headline(self):
        q = self.quote()
        self.assertEqual(q["wouldRead"], q["wouldClassify"] + q["wouldReadPages"],
                         "a breakdown that does not sum to the number on screen is worse than none")

    def test_it_says_out_loud_that_it_is_a_bound(self):
        q = self.quote()
        self.assertTrue(q.get("upperBound"), "the figure prices every run as readable - say so")
        self.assertTrue(str(q.get("boundWhy") or "").strip(), "and say WHY, in words he can read")

    def test_pricing_still_costs_nothing(self):
        """If this ever fails, the '0 calls spent' label on the panel became a lie."""
        self.assertEqual(self.quote()["spent"], 0)

    def test_the_saving_is_stated_against_the_honest_total(self):
        q = self.quote()
        seen = q["insteadOf"]
        expect = round(100.0 * (1 - (q["wouldRead"] / seen)), 1) if seen else 0.0
        self.assertAlmostEqual(
            q["savedPct"], expect, places=1,
            msg="the headline percentage must be computed from the SAME total it shows; the old "
                "route divided the classify-only count by frames and overstated the saving")


class TestChronicleFreePass(FreePassQuoteBase):
    """The same defect lived in the Chronicle pass. Grok only flagged the vault one; a fix that
    leaves the twin in place is half a fix, and this is the surface he actually looks at most."""

    def quote(self):
        q = ca.chronicle_scan_cost(self.td)
        self.assertTrue(q.get("ok"))
        return q

    def actual(self):
        n = {"classify": 0, "reader": 0}

        def classify(path):
            n["classify"] += 1
            return "chronicle-uniques"

        def read_page(path, kind):
            n["reader"] += 1
            return {"ledger": "uniques", "found": ["Harlequin Crest"], "conf": 0.9}

        cr.sweep_hist(self.td, classify=classify, read_page=read_page)
        return n

    def test_the_quote_is_never_below_the_real_spend(self):
        q, n = self.quote(), self.actual()
        real = n["classify"] + n["reader"]
        self.assertGreaterEqual(q["wouldRead"], real,
                                "quoted %d, a real sweep spends %d (%d classify + %d reader)"
                                % (q["wouldRead"], real, n["classify"], n["reader"]))

    def test_the_reader_lane_is_actually_charged_for(self):
        q, n = self.quote(), self.actual()
        self.assertGreater(n["reader"], 0, "fixture is wrong: a real sweep must read pages here")
        self.assertGreater(q["wouldReadPages"], 0,
                           "a real sweep reads %d pages here and the quote charged for 0" % n["reader"])

    def test_the_breakdown_adds_up_to_the_headline(self):
        q = self.quote()
        self.assertEqual(q["wouldRead"], q["wouldClassify"] + q["wouldReadPages"])

    def test_pricing_still_costs_nothing(self):
        self.assertEqual(self.quote()["spent"], 0)


class TestTheProbesNeverReachAModel(unittest.TestCase):
    """The free pass's one hard promise. Both routes now hand sweep() a classify stub that RETURNS A
    REAL ANSWER, which is what makes the read stage run - so it is worth pinning that neither route
    grew a path to a live reader while we were making them count honestly."""

    def test_neither_cost_route_calls_the_live_reader(self):
        import inspect
        for fn in (ca.vault_scan_cost, ca.chronicle_scan_cost):
            src = inspect.getsource(fn)
            for forbidden in ("claude_read", "claude_chronicle_read", "grok_", "_tv."):
                self.assertNotIn(forbidden, src,
                                 "%s must never reach a model lane - it is the FREE pass, and the "
                                 "panel prints '0 calls spent' on its word" % fn.__name__)


if __name__ == "__main__":
    unittest.main(verbosity=2)
