"""REG-2271 — THE RIVER DRAIN: a FROZEN grouping is skipped in seconds, a SLOW one is never skipped.

His owed vault/chronicle backlog drains through a FIFO river. The cost of a reel is its GROUPING
(measure) phase: the vault lane pays a 36-tile tooltip-OCR locate per frame, the chronicle lane a
jpeg_sig decode per frame. Until REG-2271 the ONLY thing that recovered a FROZEN grouping was
control_app's 240s river watchdog — so the backlog drained one 240s stall per frozen reel — AND
that watchdog's progress signature was FROZEN during grouping (it only moves per-reel or on a paid
read), so it also FALSE-KILLED a grouping that was merely SLOW. A false-kill discards his vault
footage, which is THE hard constraint this must never do.

THE FIX, and what these tests pin:

  * A per-reel NO-PROGRESS deadline bounds ONLY the grouping. The window RESETS on every COMPLETED
    tile (vault) / frame (chronicle), and fires ONLY when NOTHING completes for the budget. So a
    reel that keeps completing units — however slowly, however far past 240s — is NEVER skipped
    (footage-safe BY CONSTRUCTION). Only a genuinely frozen reel trips it, in ~budget seconds.
  * The vault poll fires from the per-TILE callback and raises a BaseException (chronicle_retro.
    ReelDeadline) — NOT an Exception — so it escapes still_runs' `except Exception` (which turns a
    failed look into a run-break) and can interrupt a frozen frame MID-tile-loop. The chronicle poll
    is per-frame inside sig_of, whose raise already escapes still_runs today.
  * On a fire the vault lane HOLDS + QUARANTINEs the reel (the SAME in-memory store the river
    watchdog writes, which the autoreel picker and the start door both skip) and reads PAST it; the
    chronicle lane returns note="deadline" and the seal loop SKIPS it so the reel stays OWED (a
    frozen reel look-stamped "nothing here" would hide footage). Either way the sweep RETURNS, so
    running clears via the done-path WITHOUT the 240s wait.
  * The per-tile/frame grouping-progress count is threaded UP to _VAULT_JOB/_CHRON_JOB and ADDED to
    the river watchdog's sig, so a progressing grouping keeps changing the sig and is never
    false-killed at 240s; a truly frozen one still trips.

VENUE: pure stdlib + Pillow. These tests drive the SHIPPED vault_retro.sweep / chronicle_retro.
read_reel / sweep_hist / control_app watchdog on SYNTHETIC tempdir reels (never his footage, never
his stores — sweep writes nothing). A FAKE monotonic clock lets the no-progress window be exercised
deterministically PAST 240s without any real wait, and a fake OCR / sig stub removes the vision
model. No browser, no Playwright.

RED-PROOF (each sabotage turns a named test red, then reverts byte-identical):
  * ReelDeadline(BaseException) -> (Exception): the per-tile raise is swallowed by still_runs'
    except Exception, so the frozen vault reel is never quarantined.
  * the vault per-tile poll / the chronicle per-frame poll -> beat-only: nothing fires.
  * the on_reel_timeout JOIN -> neutered: the frozen reel is not quarantined.
  * the seal-loop skip drops "deadline": a frozen chronicle reel is sealed and its footage hidden.
  * the watchdog sig drops groupTiles / groupFrames: a slow-but-progressing grouping is
    false-killed at 240s.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# Isolate every live-state file this suite could otherwise reach into (the sweep lock especially —
# run_gates reads it to decide whether a sweep is live, so stamping his real one would blind a gate).
_ISO = tempfile.mkdtemp(prefix="reg2271-iso-")
os.environ.setdefault("TV_HIST", os.path.join(_ISO, "hist"))
os.environ.setdefault("TV_SWEEP_LOCK", os.path.join(_ISO, ".sweep.lock"))
os.makedirs(os.environ["TV_HIST"], exist_ok=True)

from console_safe import enable  # noqa: E402 — needs HERE on sys.path first

enable()   # these messages carry em-dashes; a non-UTF-8 console must not crash while REPORTING

import chronicle_retro as cr   # noqa: E402
import tooltip_find as tf      # noqa: E402
import vault_retro as vr       # noqa: E402


# ── a FAKE monotonic clock, shared by the guard (patched into chronicle_retro.time) and whatever
# advances "time" (the fake OCR, the sig stub). Frozen except where a unit of work advances it, so
# the no-progress window can be driven past 240s instantly and deterministically. ──────────────────
class FakeClock(object):
    def __init__(self, t0=1000.0):
        self.t = float(t0)

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += float(dt)


def _build_reel(d, n=6):
    """A synthetic reel: n tiny VALID JPEGs + an index.json. Never his footage."""
    from PIL import Image
    os.makedirs(d, exist_ok=True)
    frames = []
    for i in range(n):
        fn = "f%02d_%d.jpg" % (i, 1790000000000 + i * 1000)
        Image.new("RGB", (72, 72), (10, 10, 10)).save(os.path.join(d, fn), "JPEG")
        frames.append({"f": fn, "ts": 1790000000000 + i * 1000})
    with open(os.path.join(d, "index.json"), "w") as fh:
        json.dump({"sessionId": os.path.basename(d).replace("reel_", "", 1), "frames": frames}, fh)
    return d


def _sig_grouped(p):
    """A per-frame fingerprint that groups 3-at-a-time (same shape test_vault_resume_seal uses)."""
    i = int(os.path.basename(p).split("_")[0][1:])
    return [float((i // 3) * 100)] * 64


class _FakeOCR(object):
    """Stands in for the real tv_diablo OCR worker inside tooltip_find.density, with NO model and NO
    real sleep: each tile 'takes' `per_tile` fake seconds (and the first tile optionally `first_jump`
    seconds, to simulate a single frozen tile). Returns enough lines to look like a tooltip."""

    def __init__(self, clock, per_tile=0.0, first_jump=None):
        self.clock = clock
        self.per_tile = per_tile
        self.first_jump = first_jump
        self.calls = 0

    def read(self, p, timeout=None):
        jump = self.first_jump if (self.calls == 0 and self.first_jump is not None) else self.per_tile
        self.clock.advance(jump)
        self.calls += 1
        return {"lines": ["Crescent Moon", "One-Handed Sword",
                          "+180% Enhanced Damage", "Required Level 47"]}


class TestReelDeadlineGuardNoProgress(unittest.TestCase):
    """The shared guard's NO-PROGRESS math, deterministic on a fake clock. This is the mechanism that
    would discard footage if it were cumulative instead of no-progress, so it is proven here first."""

    def test_a_progressing_reel_never_fires_even_far_past_the_240s_watchdog(self):
        # FOOTAGE-SAFE: a unit completes every (budget - 1)s for a total FAR past 240s. Because beat()
        # resets the window on each, the guard must NEVER fire, no matter how long the reel runs.
        clk = FakeClock()
        budget = 20
        g = cr.reel_deadline("slow", budget, clock=clk)
        total = 0
        for _ in range(100):                 # 100 * 19 = 1900 fake seconds, ~8x the 240s watchdog
            clk.advance(budget - 1)
            total += budget - 1
            g.check()                        # must not raise — a completed unit is coming
            g.beat()                         # the unit completed -> reset the window
        self.assertGreater(total, 240,
                           "PREMISE: the simulated run must exceed the 240s watchdog to be meaningful")
        # one more poll without a beat, still under budget: a cold sweep would be long dead; this one lives
        clk.advance(budget - 1)
        g.check()

    def test_no_progress_for_the_budget_fires(self):
        # a SINGLE unit that never completes for the whole budget -> the window is not reset -> fire.
        clk = FakeClock()
        g = cr.reel_deadline("frozen", 20, clock=clk)
        clk.advance(5)
        g.check()                            # 5s < 20s — not yet
        clk.advance(20)                      # now 25s with no beat
        with self.assertRaises(cr.ReelDeadline):
            g.check()

    def test_the_deadline_is_a_baseexception_not_an_exception(self):
        # THE SHARP CORRECTION: still_runs wraps its tooltip_of call in `except Exception`, so a plain
        # Exception raised from a tile would be SWALLOWED into a run-break. A BaseException escapes.
        self.assertTrue(issubclass(cr.ReelDeadline, BaseException))
        self.assertFalse(issubclass(cr.ReelDeadline, Exception),
                         "ReelDeadline must NOT be an Exception, or still_runs' except Exception "
                         "swallows the per-tile raise and the frozen reel is never skipped")

    def test_zero_or_unknown_budget_never_kills_a_reel(self):
        clk = FakeClock()
        g = cr.reel_deadline("x", 0, clock=clk)      # 0 disables entirely
        clk.advance(10 ** 6)
        g.check()                                    # must not raise
        g2 = cr.reel_deadline("x", 20, clock=clk)
        g2.disarm()                                  # disarmed before the paid read stage
        clk.advance(10 ** 6)
        g2.check()                                   # must not raise

    def test_budget_is_resolved_at_call_time_and_clamped_under_the_watchdog(self):
        # resolved at CALL time (not frozen at import) and clamped strictly under the 240s watchdog,
        # and strictly above the 4.0s single-tile OCR cap.
        for budget_fn in (vr._reel_deadline_budget, cr._chron_reel_deadline_budget):
            self.assertGreater(budget_fn(), 4.0, "the budget must sit above the 4.0s single-tile cap")
            self.assertLess(budget_fn(), 240, "the budget must sit under the 240s river watchdog")
            with mock.patch.dict(os.environ, {"TV_VAULT_HANG_DEADLINE_S": "240",
                                              "TV_VAULT_REEL_DEADLINE_S": "999",
                                              "TV_CHRON_REEL_DEADLINE_S": "999"}):
                self.assertEqual(budget_fn(), 239,
                                 "a budget >= the watchdog must be clamped to watchdog-1")


class TestVaultGroupingDeadline(unittest.TestCase):
    """Drive the SHIPPED vault_retro.sweep. A reel whose tiles keep completing (however slowly) is
    NEVER skipped; a reel with a frozen tile is HELD + QUARANTINEd fast, and the sweep RETURNS."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="reg2271-vault-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        vr._TOOLTIP_MEMO.clear()                    # module-scoped; never let one test seed another
        self.addCleanup(vr._TOOLTIP_MEMO.clear)
        self.clk = FakeClock()

    def _sweep(self, ocr, budget, on_tile, on_reel_timeout, reel="reel_s_1500000000000_V"):
        reel_dir = _build_reel(os.path.join(self.tmp, reel))
        with mock.patch.object(cr.time, "monotonic", self.clk), \
                mock.patch.object(tf, "_ocr", lambda: ocr):
            prop = vr.sweep([reel_dir], sig=_sig_grouped,
                            reader=lambda p, s: {"items": [], "conf": 0.0, "note": None},
                            classify=lambda p: None, reel_deadline_s=budget,
                            on_tile=on_tile, on_reel_timeout=on_reel_timeout)
        return prop

    def test_a_slow_but_completing_reel_is_not_skipped_past_240s(self):
        # Each tile 'takes' 9 fake seconds, under the 10s budget. 6 frames x 36 tiles = 216 tiles ->
        # ~1944 fake seconds, far past the 240s watchdog. NOT ONE tile stalls past budget, so the reel
        # MUST survive: no on_reel_timeout, no quarantine, sweep returns a proposal.
        tiles = [0]
        timeouts = []
        prop = self._sweep(_FakeOCR(self.clk, per_tile=9.0), budget=10,
                           on_tile=lambda: tiles.__setitem__(0, tiles[0] + 1),
                           on_reel_timeout=lambda rid, why: timeouts.append((rid, why)))
        self.assertGreater(tiles[0], 100,
                           "PREMISE: the tooltip tile loop must actually have run (on_tile fired %d "
                           "times) — a vacuous pass proves nothing" % tiles[0])
        self.assertGreater(self.clk.t - 1000, 240,
                           "PREMISE: the simulated grouping must exceed the 240s watchdog")
        self.assertEqual(timeouts, [],
                         "FOOTAGE DISCARDED: a slow-but-PROGRESSING reel was skipped — the window did "
                         "not reset on completed tiles")
        self.assertTrue(prop.get("ok"))

    def test_a_frozen_tile_is_held_and_quarantined_fast_and_the_sweep_returns(self):
        # The first tile 'takes' 15 fake seconds, over the 10s budget, then the rest are instant. The
        # per-tile poll must fire on that tile (a BaseException that escapes still_runs), the reel is
        # HELD with a REG-2271 reason and handed to on_reel_timeout to QUARANTINE, and the sweep
        # RETURNS (it did not hang) so the lane drains on without the 240s watchdog.
        timeouts = []
        prop = self._sweep(_FakeOCR(self.clk, per_tile=0.0, first_jump=15.0), budget=10,
                           on_tile=lambda: None,
                           on_reel_timeout=lambda rid, why: timeouts.append((rid, why)),
                           reel="reel_s_1500000000000_FROZEN")
        self.assertLess(self.clk.t - 1000, 240,
                        "the frozen reel must be caught FAST (well under the 240s watchdog)")
        self.assertTrue(prop.get("ok"), "the sweep must RETURN, not hang")
        self.assertEqual(len(timeouts), 1, "the frozen reel was not handed to on_reel_timeout")
        self.assertEqual(timeouts[0][0], "reel_s_1500000000000_FROZEN",
                         "on_reel_timeout named the wrong reel")
        self.assertTrue(any("REG-2271" in (h.get("why") or "") for h in (prop.get("held") or [])),
                        "the frozen reel was not HELD with a REG-2271 reason")
        # NOTHING partial was banked: the reel never reached a paid read
        self.assertEqual(int((prop.get("totals") or {}).get("pagesRead") or 0), 0)

    def test_a_single_frozen_frame_is_caught_only_by_the_per_tile_baseexception(self):
        # THE SHARP CORRECTION, proven. A reel of ONE frame whose first tile stalls past budget: the
        # per-frame sig_of backstop already ran (before the tile) and there is NO next frame for it to
        # fire on, so the ONLY thing that can catch this reel is the per-TILE raise escaping still_runs
        # MID-tile-loop. That requires a BaseException: were ReelDeadline an Exception, still_runs'
        # `except Exception` would swallow the tile raise into a run-break, the loop would end, and the
        # frozen reel would sail through UNCAUGHT (its footage then stalls to the 240s watchdog). So
        # this test goes RED the instant the deadline stops being a BaseException. [[the-unjoined-end]]
        reel_dir = _build_reel(os.path.join(self.tmp, "reel_s_1500000000000_1FRAME"), n=1)
        timeouts = []
        with mock.patch.object(cr.time, "monotonic", self.clk), \
                mock.patch.object(tf, "_ocr", lambda: _FakeOCR(self.clk, per_tile=0.0, first_jump=15.0)):
            prop = vr.sweep([reel_dir], sig=_sig_grouped,
                            reader=lambda p, s: {"items": [], "conf": 0.0, "note": None},
                            classify=lambda p: None, reel_deadline_s=10,
                            on_tile=lambda: None,
                            on_reel_timeout=lambda rid, why: timeouts.append((rid, why)))
        self.assertTrue(prop.get("ok"), "the sweep must RETURN, not hang")
        self.assertEqual(len(timeouts), 1,
                         "a single frozen frame was NOT caught — the per-tile raise did not escape "
                         "still_runs (is ReelDeadline still a BaseException?)")
        self.assertEqual(timeouts[0][0], "reel_s_1500000000000_1FRAME")

    def test_the_quarantine_join_reaches_control_apps_real_store_and_door(self):
        # The on_reel_timeout control_app wires writes _VAULT_SWEEP_QUARANTINE, which the start DOOR
        # refuses on. Prove the JOIN end-to-end against the real store + door (the-unjoined-end).
        import control_app as ca
        rid = "reel_s_1500000000000_QJOIN"
        self.addCleanup(ca._VAULT_SWEEP_QUARANTINE.pop, rid, None)
        ca._VAULT_SWEEP_QUARANTINE.pop(rid, None)
        ca._vault_quarantine_reel(os.path.join(self.tmp, rid),
                                  "reel made no grouping progress for 15.00s")
        self.assertIn(rid, ca._VAULT_SWEEP_QUARANTINE, "the sweep-side quarantine writer did not join")
        out = ca.vault_sweep_start(reel_dir=os.path.join(self.tmp, rid))
        self.assertTrue(out.get("quarantined"),
                        "the start door did not skip a quarantined reel — %r" % out)

    def test_a_primed_tooltip_memo_does_not_false_kill_a_slow_but_completing_reel(self):
        # ── THE FOOTAGE-LOSS REFUTATION (FIX A) ──────────────────────────────────────────────────
        # vault_scan_cost primes _TOOLTIP_MEMO across his WHOLE corpus, so a later real sweep finds
        # every _tip_of a cache HIT — and a cache hit returns WITHOUT calling locate(), so the per-TILE
        # heartbeat (_tile_progress -> beat + on_tile) NEVER fires on a primed reel. If a cache hit did
        # not itself beat, the per-reel no-progress window would degrade to CUMULATIVE over the whole
        # grouping and FALSE-KILL a HEALTHY large reel whose per-frame work merely sums past the budget
        # — discarding his vault footage, THE hard constraint of this arc.
        #
        # ⚠ THIS TEST PRIMES THE MEMO ON PURPOSE AND MUST NOT CLEAR IT between the two sweeps (the class
        # setUp clears it ONCE, before this runs; priming happens inside the test). It asserts BOTH
        # footage-safety invariants on a primed reel: (a) the IN-THREAD window is still beaten per frame
        # (the cache-hit beat), so a slow-but-completing primed reel is NEVER handed to on_reel_timeout;
        # and (b) per-frame grouping progress is still surfaced UP (sig_of -> on_tile), so _VAULT_JOB's
        # groupTiles keeps advancing and the control_app phase-scoped watchdog cannot false-kill it
        # out-of-thread either. [[heart-first]] [[regression-guard]]
        reel = "reel_s_1500000000000_PRIMED"
        reel_dir = _build_reel(os.path.join(self.tmp, reel), n=8)

        def slow_sig(p):
            # a per-DISTINCT-frame cost UNDER the 10s budget (9s), but 8x9=72s cumulatively — ~7x the
            # budget, so an un-beaten (cumulative) window would fire after ~2 frames.
            self.clk.advance(9.0)
            return _sig_grouped(p)

        timeouts = []
        tiles = [0]
        ocr = _FakeOCR(self.clk, per_tile=0.0)   # instant tiles: the PRIMING pass populates the memo
        with mock.patch.object(cr.time, "monotonic", self.clk), \
                mock.patch.object(tf, "_ocr", lambda: ocr):
            # PRIME — the first sweep does a real locate() per frame (cache MISS) and fills _TOOLTIP_MEMO
            vr.sweep([reel_dir], sig=slow_sig,
                     reader=lambda p, s: {"items": [], "conf": 0.0, "note": None},
                     classify=lambda p: None, reel_deadline_s=10,
                     on_tile=lambda: None,
                     on_reel_timeout=lambda rid, why: timeouts.append(("PRIME", rid, why)))
            self.assertEqual(timeouts, [], "PREMISE: the priming sweep (tiles beat) must not itself fire")
            self.assertTrue(vr._TOOLTIP_MEMO, "PREMISE: the first sweep must have PRIMED the tooltip memo")
            # NOW the primed sweep — every _tip_of is a cache HIT, so _tile_progress NEVER fires. Count
            # on_tile to prove per-frame grouping progress is still surfaced from sig_of.
            t_start = self.clk.t
            prop = vr.sweep([reel_dir], sig=slow_sig,
                            reader=lambda p, s: {"items": [], "conf": 0.0, "note": None},
                            classify=lambda p: None, reel_deadline_s=10,
                            on_tile=lambda: tiles.__setitem__(0, tiles[0] + 1),
                            on_reel_timeout=lambda rid, why: timeouts.append(("PRIMED", rid, why)))
        # (a) IN-THREAD footage-safety — the cache-hit beat kept the no-progress window resetting, so a
        #     slow-but-completing primed reel is NEVER handed to on_reel_timeout. (Asserted FIRST: when
        #     the cache-hit beat is removed the reel is false-killed and ABORTS early, so this is the
        #     true red — the cumulative-clock PREMISE below would then also fail, but later.)
        self.assertEqual(timeouts, [],
                         "FOOTAGE DISCARDED: a PRIMED tooltip memo degraded the no-progress window to "
                         "cumulative and false-killed a healthy reel (the _tip_of cache-HIT beat is missing?)")
        self.assertTrue(prop.get("ok"), "the primed sweep must RETURN a proposal, not hold/hang")
        # (b) OUT-OF-THREAD footage-safety — groupTiles still advances on cache-HIT frames, so the
        #     phase-scoped river watchdog sees a PROGRESSING grouping and cannot false-kill it. On a
        #     primed reel ONLY sig_of surfaces on_tile (no _tile_progress), so a positive count proves it.
        self.assertGreater(tiles[0], 0,
                           "WATCHDOG BLINDED: no per-frame grouping progress was surfaced on a PRIMED "
                           "reel — groupTiles would FREEZE and the phase-scoped watchdog would false-kill "
                           "a healthy grouping (sig_of's on_tile surfacing is missing?)")
        # PREMISE (meaningfulness, last): the primed grouping summed FAR past the budget cumulatively, so
        # an un-beaten window WOULD have fired — i.e. the green above is not vacuous.
        self.assertGreater(self.clk.t - t_start, 10 * 3,
                           "PREMISE: the primed grouping must sum FAR past the 10s budget cumulatively")


class TestChronicleGroupingDeadline(unittest.TestCase):
    """Drive the SHIPPED chronicle_retro.read_reel / sweep_hist. A reel whose frames keep completing
    is read normally; a frozen frame returns note='deadline' so the reel stays OWED, never sealed."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="reg2271-chron-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.clk = FakeClock()

    def test_slow_but_completing_frames_are_not_marked_deadline_past_240s(self):
        reel = _build_reel(os.path.join(self.tmp, "reel_s_1600000000000_CA"), n=40)
        seen = [0]

        def sig_of(n):
            self.clk.advance(9.0)            # each frame 'takes' 9s, under the 10s budget
            seen[0] += 1
            return [0.0] * 64

        with mock.patch.object(cr.time, "monotonic", self.clk):
            r = cr.read_reel(reel, lambda p: None, lambda p, k: {},
                             sig_of=sig_of, reel_deadline_s=10)
        self.assertGreater(seen[0], 20, "PREMISE: the frames must actually have been fingerprinted")
        self.assertGreater(self.clk.t - 1000, 240,
                           "PREMISE: the grouping must exceed the 240s watchdog to be meaningful")
        self.assertNotEqual(r.get("note"), "deadline",
                            "FOOTAGE DISCARDED: a slow-but-PROGRESSING chronicle reel was skipped")

    def test_a_frozen_frame_returns_note_deadline(self):
        reel = _build_reel(os.path.join(self.tmp, "reel_s_1600000000000_CB"), n=6)
        st = {"c": 0}

        def sig_of(n):
            self.clk.advance(15.0 if st["c"] == 0 else 0.0)   # first frame stalls past the 10s budget
            st["c"] += 1
            return [0.0] * 64

        with mock.patch.object(cr.time, "monotonic", self.clk):
            r = cr.read_reel(reel, lambda p: None, lambda p, k: {},
                             sig_of=sig_of, reel_deadline_s=10)
        self.assertEqual(r.get("note"), "deadline",
                         "a frozen chronicle frame must return note='deadline' so the reel stays owed")
        self.assertLess(self.clk.t - 1000, 240, "the frozen frame must be caught well under 240s")

    def test_sweep_hist_surfaces_the_deadline_note_with_a_blankruns_key(self):
        # ⚠ sweep_hist's stat comprehension ALWAYS adds a `blankRuns` key, so the seal loop's
        # did_read/`_looked` guard would read a deadline row as a real walk and SEAL it. Prove both:
        # the note propagates through sweep_hist AND the blankRuns key is present — which is why the
        # seal loop MUST skip on the note (see TestChronicleDeadlineStaysOwed). [[regression-guard]]
        histroot = os.path.join(self.tmp, "histB")
        _build_reel(os.path.join(histroot, "reel_s_1600000000000_CH"), n=6)
        st = {"c": 0}

        def sig_of(n):
            self.clk.advance(15.0 if st["c"] == 0 else 0.0)
            st["c"] += 1
            return [0.0] * 64

        with mock.patch.object(cr.time, "monotonic", self.clk):
            res = cr.sweep_hist(histroot, lambda p: None, lambda p, k: {},
                                sig_of=sig_of, reel_deadline_s=10)
        rows = [r for r in res["reels"] if r.get("reel") == "s_1600000000000_CH"]
        self.assertEqual(len(rows), 1, "the reel was not swept")
        self.assertEqual(rows[0].get("note"), "deadline")
        self.assertIn("blankRuns", rows[0],
                      "PREMISE for the seal-loop skip: the stat carries a blankRuns KEY, so the "
                      "did_read/_looked guard cannot tell a deadline row from a real walk")


class TestChronicleDeadlineStaysOwed(unittest.TestCase):
    """The chronicle seal loop must SKIP a note='deadline' row, exactly like 'already-swept', so the
    frozen reel stays OWED (never look-stamped 'nothing here', which would hide footage)."""

    def test_the_seal_loop_skips_a_deadline_row(self):
        # A source-reading guard (source-reading-guard): grade CODE, not prose, and anchor on the FULL
        # unique condition. The behavioural half is TestChronicleGroupingDeadline +
        # test_sweep_hist_surfaces_the_deadline_note_with_a_blankruns_key, which together prove a
        # deadline row reaches this loop carrying a blankRuns key.
        with open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as _fh:
            src = _fh.read()
        code = "\n".join(ln.split("#", 1)[0] for ln in src.split("\n"))
        anchor = 'if st.get("note") in ("already-swept", "deadline") or not st.get("reel"):'
        self.assertEqual(code.count(anchor), 1,
                         "the chronicle seal-loop skip for a deadline row is missing or not unique — "
                         "a frozen reel would be SEALED and its footage hidden")


class TestRiverWatchdogSigIncludesGroupingProgress(unittest.TestCase):
    """control_app's river watchdog must NOT false-kill a grouping that is making tile/frame progress.
    Its sig now carries groupTiles (vault) / groupFrames (chronicle); a progressing grouping keeps
    changing the sig so the no-progress clock resets, while a truly frozen one still trips at 240s."""

    @classmethod
    def setUpClass(cls):
        import control_app as ca
        cls.ca = ca

    def setUp(self):
        import time
        self.time = time
        ca = self.ca
        self._vjob = dict(ca._VAULT_JOB)
        self._cjob = dict(ca._CHRON_JOB)
        self._vprog = dict(ca._VAULT_SWEEP_PROGRESS)
        self._cprog = dict(ca._CHRON_SWEEP_PROGRESS)
        self._vq = dict(ca._VAULT_SWEEP_QUARANTINE)

        def _restore():
            ca._VAULT_JOB.clear(); ca._VAULT_JOB.update(self._vjob)
            ca._CHRON_JOB.clear(); ca._CHRON_JOB.update(self._cjob)
            ca._VAULT_SWEEP_PROGRESS.clear(); ca._VAULT_SWEEP_PROGRESS.update(self._vprog)
            ca._CHRON_SWEEP_PROGRESS.clear(); ca._CHRON_SWEEP_PROGRESS.update(self._cprog)
            ca._VAULT_SWEEP_QUARANTINE.clear(); ca._VAULT_SWEEP_QUARANTINE.update(self._vq)
        self.addCleanup(_restore)

    def _stalled_ts(self):
        return self.time.time() - (self.ca._VAULT_SWEEP_HANG_DEADLINE_S + 60)

    def test_vault_a_progressing_grouping_is_not_false_killed_at_the_watchdog(self):
        ca = self.ca
        ca._VAULT_SWEEP_PROGRESS.clear()
        ca._VAULT_JOB.update({"running": True, "startedTs": 1, "phase": "grouping",
                              "runReelsDone": 0, "classified": 0, "pagesRead": 0,
                              "runReel": "r", "runReelDir": "/x/reel_r", "groupTiles": 0})
        self.assertFalse(ca._vault_sweep_hang_check(), "first tick only records the sig")
        # a long stall, BUT the grouping advanced its per-tile count since the snapshot
        ca._VAULT_SWEEP_PROGRESS["ts"] = self._stalled_ts()
        ca._VAULT_JOB["groupTiles"] = 4242
        self.assertFalse(ca._vault_sweep_hang_check(),
                         "FALSE-KILL: a grouping making tile progress was declared hung at 240s — "
                         "its footage would be discarded (groupTiles missing from the watchdog sig?)")
        self.assertTrue(ca._VAULT_JOB["running"], "the progressing sweep must still be running")
        self.assertNotIn("reel_r", ca._VAULT_SWEEP_QUARANTINE)
        # CONTRAST: FROZEN (groupTiles unchanged) past the deadline -> genuinely hung -> cleared
        ca._VAULT_SWEEP_PROGRESS["ts"] = self._stalled_ts()
        self.assertTrue(ca._vault_sweep_hang_check(),
                        "a genuinely frozen grouping must still trip the watchdog")
        self.assertFalse(ca._VAULT_JOB["running"])

    def test_chron_a_progressing_grouping_is_not_false_killed_at_the_watchdog(self):
        ca = self.ca
        ca._CHRON_SWEEP_PROGRESS.clear()
        ca._CHRON_JOB.update({"running": True, "startedTs": 1, "phase": "grouping",
                              "reelsDone": 0, "classified": 0, "pagesRead": 0, "groupFrames": 0})
        self.assertFalse(ca._chron_sweep_hang_check(), "first tick only records the sig")
        ca._CHRON_SWEEP_PROGRESS["ts"] = self._stalled_ts()
        ca._CHRON_JOB["groupFrames"] = 777
        self.assertFalse(ca._chron_sweep_hang_check(),
                         "FALSE-KILL: a chronicle grouping making frame progress was declared hung "
                         "(groupFrames missing from the watchdog sig?)")
        self.assertTrue(ca._CHRON_JOB["running"])
        ca._CHRON_SWEEP_PROGRESS["ts"] = self._stalled_ts()
        self.assertTrue(ca._chron_sweep_hang_check(),
                        "a genuinely frozen chronicle grouping must still trip the watchdog")

    # ── FIX B PRIMARY — the PHASE-SCOPED bound discriminates grouping (fast) from reading (240s) ──────
    def test_vault_a_frozen_grouping_is_quarantined_at_the_budget_not_240s(self):
        # A FROZEN grouping stalled LONGER than the per-reel budget but FAR UNDER 240s must be cleared +
        # quarantined NOW (an uninterruptible grouping tile drains ~12x faster). The SAME stall in the
        # paid READING phase must NOT be touched — one model read is legitimately long, and cutting it
        # at the grouping budget would false-kill a healthy reel. This proves the scope DISCRIMINATES;
        # the existing progressing/frozen tests above use a 300s stall that would trip either bound.
        ca = self.ca
        budget = ca._vault_retro()._reel_deadline_budget()
        self.assertLess(budget, ca._VAULT_SWEEP_HANG_DEADLINE_S,
                        "PREMISE: the grouping budget must be under the 240s backstop")
        mid = (budget + ca._VAULT_SWEEP_HANG_DEADLINE_S) / 2.0   # > budget, < 240s
        # (A) GROUPING -> cleared + quarantined at ~budget
        ca._VAULT_SWEEP_PROGRESS.clear()
        ca._VAULT_SWEEP_QUARANTINE.pop("reel_g", None)
        ca._VAULT_JOB.update({"running": True, "startedTs": 1, "phase": "grouping",
                              "runReelsDone": 0, "classified": 0, "pagesRead": 0,
                              "runReel": "g", "runReelDir": "/x/reel_g", "groupTiles": 9})
        self.assertFalse(ca._vault_sweep_hang_check(), "first tick records the sig")
        ca._VAULT_SWEEP_PROGRESS["ts"] = self.time.time() - mid
        self.assertTrue(ca._vault_sweep_hang_check(),
                        "a FROZEN grouping stalled past the per-reel budget must clear at ~budget, NOT "
                        "be held to 240s (the phase-scoped grouping bound is missing or not applied)")
        self.assertFalse(ca._VAULT_JOB["running"])
        self.assertIn("reel_g", ca._VAULT_SWEEP_QUARANTINE)
        # (B) READING -> the SAME stall must NOT trip
        ca._VAULT_SWEEP_PROGRESS.clear()
        ca._VAULT_SWEEP_QUARANTINE.pop("reel_r2", None)
        ca._VAULT_JOB.update({"running": True, "startedTs": 2, "phase": "reading",
                              "runReelsDone": 0, "classified": 0, "pagesRead": 0,
                              "runReel": "r2", "runReelDir": "/x/reel_r2", "groupTiles": 9})
        self.assertFalse(ca._vault_sweep_hang_check(), "first tick records the sig")
        ca._VAULT_SWEEP_PROGRESS["ts"] = self.time.time() - mid
        self.assertFalse(ca._vault_sweep_hang_check(),
                         "FALSE-KILL: a paid READ stalled only %ds (< 240s) was quarantined — the short "
                         "grouping budget must NOT apply to the reading phase" % int(mid))
        self.assertTrue(ca._VAULT_JOB["running"])
        self.assertNotIn("reel_r2", ca._VAULT_SWEEP_QUARANTINE)

    def test_chron_a_frozen_grouping_clears_at_the_budget_not_240s(self):
        ca = self.ca
        import chronicle_retro as _cr
        budget = _cr._chron_reel_deadline_budget()
        mid = (budget + ca._VAULT_SWEEP_HANG_DEADLINE_S) / 2.0
        # (A) GROUPING -> cleared at ~budget
        ca._CHRON_SWEEP_PROGRESS.clear()
        ca._CHRON_JOB.update({"running": True, "startedTs": 1, "phase": "grouping",
                              "reelsDone": 0, "classified": 0, "pagesRead": 0, "groupFrames": 3})
        self.assertFalse(ca._chron_sweep_hang_check(), "first tick records the sig")
        ca._CHRON_SWEEP_PROGRESS["ts"] = self.time.time() - mid
        self.assertTrue(ca._chron_sweep_hang_check(),
                        "a frozen chronicle grouping past the budget must clear at ~budget, not 240s")
        self.assertFalse(ca._CHRON_JOB["running"])
        # (B) READING -> the SAME stall must NOT trip
        ca._CHRON_SWEEP_PROGRESS.clear()
        ca._CHRON_JOB.update({"running": True, "startedTs": 2, "phase": "reading",
                              "reelsDone": 0, "classified": 0, "pagesRead": 0, "groupFrames": 3})
        self.assertFalse(ca._chron_sweep_hang_check(), "first tick records the sig")
        ca._CHRON_SWEEP_PROGRESS["ts"] = self.time.time() - mid
        self.assertFalse(ca._chron_sweep_hang_check(),
                         "FALSE-KILL: a paid chronicle read stalled < 240s was cleared by the grouping budget")
        self.assertTrue(ca._CHRON_JOB["running"])


class TestWedgedGroupingIsRecoveredOutOfThread(unittest.TestCase):
    """FIX B, end-to-end: a sweep whose OCR read NEVER returns (an UNINTERRUPTIBLE grouping freeze the
    in-thread per-reel deadline cannot fire on — its check() never runs) is recovered by the
    phase-scoped river watchdog from ANOTHER thread, within ~budget, NOT the 240s backstop. Drives the
    SHIPPED vr.sweep in a daemon thread against the REAL _VAULT_JOB + watchdog + quarantine store."""

    def setUp(self):
        import control_app as ca
        self.ca = ca
        self.tmp = tempfile.mkdtemp(prefix="reg2271-thread-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        vr._TOOLTIP_MEMO.clear()
        self.addCleanup(vr._TOOLTIP_MEMO.clear)
        self._saved = (dict(ca._VAULT_JOB), dict(ca._VAULT_SWEEP_PROGRESS),
                       dict(ca._VAULT_SWEEP_QUARANTINE))

    def _restore_job(self):
        ca = self.ca
        ca._VAULT_JOB.clear(); ca._VAULT_JOB.update(self._saved[0])
        ca._VAULT_SWEEP_PROGRESS.clear(); ca._VAULT_SWEEP_PROGRESS.update(self._saved[1])
        ca._VAULT_SWEEP_QUARANTINE.clear(); ca._VAULT_SWEEP_QUARANTINE.update(self._saved[2])

    def test_a_never_returning_ocr_read_is_quarantined_within_budget_not_240s(self):
        import threading
        import time as _time
        ca = self.ca
        budget = ca._vault_retro()._reel_deadline_budget()
        rid = "reel_s_1500000000000_WEDGE"
        reel_dir = _build_reel(os.path.join(self.tmp, rid), n=6)
        released = threading.Event()
        entered = threading.Event()

        class _WedgedOCR(object):
            # read() NEVER returns until teardown releases it — the uninterruptible freeze stand-in.
            def read(self, p, timeout=None):
                entered.set()
                released.wait(30)
                return {"lines": []}

        # mirror control_app's real _on_reel / _on_tile wiring onto the REAL _VAULT_JOB
        def on_reel(i, total, name):
            with ca._VAULT_LOCK:
                ca._VAULT_JOB["phase"] = "grouping"
                ca._VAULT_JOB["runReel"] = name
                ca._VAULT_JOB["runReelDir"] = reel_dir

        def on_tile():
            with ca._VAULT_LOCK:
                ca._VAULT_JOB["groupTiles"] = int(ca._VAULT_JOB.get("groupTiles") or 0) + 1

        ca._VAULT_SWEEP_PROGRESS.clear()
        ca._VAULT_SWEEP_QUARANTINE.pop(rid, None)
        ca._VAULT_JOB.clear()
        ca._VAULT_JOB.update({"running": True, "startedTs": int(_time.time() * 1000), "phase": "idle",
                              "runReel": None, "runReelDir": None, "groupTiles": 0,
                              "runReelsDone": 0, "classified": 0, "pagesRead": 0})

        def _run():
            frozen = FakeClock()   # a FROZEN clock: even if an in-thread check() ran it could not fire
            with mock.patch.object(cr.time, "monotonic", frozen), \
                    mock.patch.object(tf, "_ocr", lambda: _WedgedOCR()):
                try:
                    vr.sweep([reel_dir], sig=_sig_grouped,
                             reader=lambda p, s: {"items": [], "conf": 0.0, "note": None},
                             classify=lambda p: None, reel_deadline_s=budget,
                             on_reel=on_reel, on_tile=on_tile, on_reel_timeout=lambda r, w: None)
                except BaseException:
                    pass

        th = threading.Thread(target=_run, daemon=True, name="reg2271-wedge")
        th.start()

        def _cleanup():
            released.set()
            th.join(5)
            self._restore_job()
        self.addCleanup(_cleanup)

        self.assertTrue(entered.wait(10), "PREMISE: the sweep thread must have reached the wedged OCR read")
        self.assertTrue(th.is_alive(), "PREMISE: the sweep thread must be BLOCKED (uninterruptible)")
        self.assertEqual(ca._VAULT_JOB.get("phase"), "grouping",
                         "the sweep must have entered the GROUPING sub-phase before wedging")
        # the watchdog, on ANOTHER thread (here, the test thread), recovers it. First tick records the
        # frozen sig; then simulate ~budget of no-progress (FAR under 240s) and it must quarantine.
        self.assertFalse(ca._vault_sweep_hang_check(), "first tick only records the (frozen) sig")
        stall = budget + 5
        self.assertLess(stall, ca._VAULT_SWEEP_HANG_DEADLINE_S / 4.0,
                        "PREMISE: the recovery stall must be FAR under the 240s backstop to be meaningful")
        ca._VAULT_SWEEP_PROGRESS["ts"] = _time.time() - stall
        self.assertTrue(ca._vault_sweep_hang_check(),
                        "the wedged grouping was NOT recovered within ~budget out-of-thread "
                        "(phase-scoped watchdog missing?) — the river would stall to 240s")
        self.assertFalse(ca._VAULT_JOB.get("running"), "the hung guard was not cleared")
        self.assertIn(rid, ca._VAULT_SWEEP_QUARANTINE, "the wedged reel was not quarantined")
        # proof the recovery was genuinely OUT-OF-THREAD: the sweep thread is still wedged in the OCR read
        self.assertTrue(th.is_alive(), "recovery must be out-of-thread: the sweep thread is still wedged")


class TestOcrWorkerLockIsBounded(unittest.TestCase):
    """FIX B COMPLEMENT — OcrWorker.read bounds its lock ACQUIRE, so a wedged holder (its pipe stuck
    while it holds the lock) cannot make a SECOND caller — a sweep's grouping tile sharing the module
    _OCR singleton with the live text-eye lane — block UNINTERRUPTIBLY. A contended read returns None
    (an honest miss), so on_tile fires and the frame can be interrupted in ~budget instead of 240s."""

    def test_a_wedged_lock_holder_does_not_block_a_second_read_forever(self):
        import tv_diablo as _td
        import threading
        import time as _time
        w = _td.OcrWorker()
        holding = threading.Event()
        release = threading.Event()

        def _hold():
            with w.lock:
                holding.set()
                release.wait(8)       # hold the lock; a finite ceiling so a sabotage reds (not hangs)

        th = threading.Thread(target=_hold, daemon=True, name="reg2271-lockhold")
        th.start()
        self.addCleanup(lambda: (release.set(), th.join(5)))
        self.assertTrue(holding.wait(5), "PREMISE: the background holder must have taken the lock")
        t0 = _time.monotonic()
        out = w.read("/nonexistent/reg2271/frame.jpg", timeout=1.0)
        dt = _time.monotonic() - t0
        self.assertIsNone(out, "a read that could not get the lock in time must return None (honest miss)")
        self.assertLess(dt, 5.0,
                        "the read blocked ~%.1fs on a HELD lock — the acquire timeout is missing, so a "
                        "wedged holder would hang the whole fast lane / sweep uninterruptibly" % dt)


class TestGroupingSubPhaseIsWired(unittest.TestCase):
    """THE JOIN (the-unjoined-end): the deterministic watchdog tests above set phase manually, so they
    cannot prove PRODUCTION ever enters the 'grouping' sub-phase. This source guard pins that the sweep
    wiring actually sets it: _on_reel -> phase 'grouping', the paid _tick -> phase 'reading', the
    chronicle _tick -> 'grouping' on a frame / 'reading' on a read, and the watchdog scopes on it. A
    source-reading-guard: grade CODE not prose, anchor on the FULL unique assignment, count == 1."""

    def _code(self):
        with open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            src = fh.read()
        return "\n".join(ln.split("#", 1)[0] for ln in src.split("\n"))

    def test_the_sweep_wiring_sets_the_grouping_and_reading_subphases(self):
        code = self._code()
        # ⚠ anchors are the FULL unique form (source-reading-guard §2): a bare `if "classified"...` is a
        # SUBSTRING of the chronicle lane's `elif "classified"...`, and a bare `_VAULT_JOB["phase"] =
        # "reading"` also appears at the pre-sweep set — so the paid-work flips anchor on the 2-line block.
        for anchor, why in (
            ('_VAULT_JOB["phase"] = "grouping"',
             "vault _on_reel must mark the GROUPING sub-phase or the phase-scoped watchdog never bites"),
            ('                if "classified" in kw or "pagesRead" in kw:\n'
             '                    _VAULT_JOB["phase"] = "reading"',
             "vault _tick must flip to READING on paid work so a long read keeps the 240s bound"),
            ('                if "groupFrames" in kw:\n'
             '                    _CHRON_JOB["phase"] = "grouping"',
             "chronicle _tick must mark GROUPING on a grouping frame"),
            ('                elif "classified" in kw or "pagesRead" in kw:\n'
             '                    _CHRON_JOB["phase"] = "reading"',
             "chronicle _tick must flip to READING on paid work"),
            ('str(st.get("phase")) == "grouping"',
             "the watchdog must phase-scope its no-progress bound on the grouping sub-phase"),
        ):
            self.assertEqual(code.count(anchor), 1,
                             "%s — anchor %r found %d times (need exactly 1)"
                             % (why, anchor, code.count(anchor)))


RED_PROOF = [
    {
        "why": "FIX A (footage) - a tooltip cache HIT must beat the per-reel no-progress window, or a "
               "PRIMED _TOOLTIP_MEMO degrades it to cumulative and false-kills a healthy large reel",
        "file": "vault_retro.py",
        "find": "                _dl.beat()\n                return _TOOLTIP_MEMO[key]",
        "replace": "                return _TOOLTIP_MEMO[key]",
        "matches": 1,
        "test": "TestVaultGroupingDeadline.test_a_primed_tooltip_memo_does_not_false_kill_a_slow_but_completing_reel",
    },
    {
        "why": "FIX A (watchdog footage-safety) - sig_of must surface per-frame grouping progress UP so "
               "groupTiles advances on a cache-HIT frame; else a primed grouping freezes the watchdog sig",
        "file": "vault_retro.py",
        "find": ("            if on_tile is not None:\n                try:\n                    on_tile()"
                 "\n                except Exception:\n                    pass\n            return _sig_memo[n]"),
        "replace": "            return _sig_memo[n]",
        "matches": 1,
        "test": "TestVaultGroupingDeadline.test_a_primed_tooltip_memo_does_not_false_kill_a_slow_but_completing_reel",
    },
    {
        "why": "FIX B PRIMARY - the watchdog must use the SHORT per-reel budget during GROUPING; if the "
               "phase scope never matches, a frozen grouping is held to 240s not ~budget",
        "file": "control_app.py",
        "find": 'if grouping_deadline_fn is not None and str(st.get("phase")) == "grouping":',
        "replace": 'if grouping_deadline_fn is not None and str(st.get("phase")) == "__never__":',
        "matches": 1,
        "test": "TestRiverWatchdogSigIncludesGroupingProgress.test_vault_a_frozen_grouping_is_quarantined_at_the_budget_not_240s",
    },
    {
        "why": "FIX B JOIN - vault _on_reel must set the 'grouping' sub-phase in production, or the "
               "phase-scoped watchdog never bites on a real sweep (the-unjoined-end)",
        "file": "control_app.py",
        "find": '_VAULT_JOB["phase"] = "grouping"',
        "replace": '_VAULT_JOB["phase"] = "idle"',
        "matches": 1,
        "test": "TestGroupingSubPhaseIsWired.test_the_sweep_wiring_sets_the_grouping_and_reading_subphases",
    },
    {
        "why": "FIX B COMPLEMENT - OcrWorker.read must bound its lock acquire, or a wedged holder blocks "
               "a second read uninterruptibly (the whole fast lane / sweep hangs to the 240s watchdog)",
        "file": "tv_diablo.py",
        "find": "        if not self.lock.acquire(timeout=max(1.0, timeout)):",
        "replace": "        if not self.lock.acquire():",
        "matches": 1,
        "test": "TestOcrWorkerLockIsBounded.test_a_wedged_lock_holder_does_not_block_a_second_read_forever",
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
