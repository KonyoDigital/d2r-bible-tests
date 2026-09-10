# -*- coding: utf-8 -*-
"""#72 — THE COVERAGE RATCHET WAS SKIPPED ENTIRELY ON A SUBSET RUN, AND ITS FLOOR WAS STALE.

Two compounding facts, both read out of tv/render_check.py rather than guessed:

  (a) the floor only RISES on `--bless`, and `--bless` refuses unless the run reported EVERY
      target (`_coverage_bless(results, _full and not bad and not unknown, _say)` -> "refusing to
      bless: this run did not report every target"). So a subset run can never refresh it.

  (b) the ratchet was SKIPPED WHOLESALE on a subset run. The shipped code was:

          _full = (len(targets) == len(TARGETS))
          ...
          cov_missing = 0
          if _full:
              cov_missing = _coverage_check(results, _say)
          elif _coverage_floor() is not None:
              _say("     (i) coverage ratchet skipped - this run asked for %d of %d targets, and a
                    subset cannot tell a deliberate filter from a surface that vanished.")

      That reason is TRUE OF THE SET AND FALSE OF THE MEMBERS. A subset run cannot speak for the
      targets it did not render. It has exactly as much evidence as a full run about the ones it
      DID: it rendered them, it counted their nodes, and the floor for those targets is right
      there in the file. `render_check.py heart-stored` could lose a node and exit 0.

And the floor is stale where it matters most. MEASURED on this tree by parsing, not grepping:

      tv/render_coverage.json  floor["heart-stored"] = 9 at every one of the five widths
      TARGETS["heart-stored"]["sel"] has SIX clauses since v2905/v2910:
          #hrt-instruments .hrt-k, .hrt-s, .hrt-w, .hrt-hn, .hrt-nw, .hrt-w > i

  `_hrtInstruments()` in tv/control_ui.html builds that section, so the count is arithmetic:
      .hrt-hn      1
      .hrt-nw      3   (lineBits = 2 clauses; `_weld` emits 1 span for a <=3-word clause and 2
                        for a longer one -> 1 + 2)
      .hrt-w > i   2   (both <i> live in the first row's .hrt-w)
      .hrt-k/.hrt-s/.hrt-w   3 x (2 + blind.length)
      => 6 + 3*blind  under the OLD three-clause selector   -> 9 with one blind gate
      => 12 + 3*blind under the SIX-clause selector          -> 15 with one blind gate

  So the floor of 9 IS the pre-v2905 selector, and a clean run now photographs 15. Six nodes of
  slack: those six could vanish tomorrow, coverage would fall 15 -> 9, still be >= the floor, and
  the run would be GREEN. A ratchet that cannot fire inside its own slack is measuring nothing
  there. [[regression-guard]] [[stale-reading]] [[zero-needs-a-denominator]]

WHAT THIS FILE PINS

  * a subset run RATCHETS THE TARGETS IT RAN — a lost node is RED, not a skipped line;
  * a subset run does NOT refuse the targets it did not ask for, and SAYS they are UNKNOWN;
  * a floor naming a target TARGETS no longer defines is refused without rendering anything;
  * a stale floor is a LOUD, per-target, per-width fact carrying floor / measured / STALE by N;
  * ...and is NOT by itself a refusal, because a gate that is only ever red gets switched off;
  * ...and is never silently truncated, because a truncated list of blind spots is a blind spot;
  * ...and is RECORDED in .render_verdict.json, so the heart supervises it, not the scrollback;
  * `--bless` STILL refuses a subset run. A partial run raising the floor would bless coverage it
    never fully measured — the same class of lie, one layer down. That is the one thing this fix
    must not buy.

⚠ EVERY LAW BELOW HAS A NAMED SABOTAGE IN RED_PROOF. A gate never seen red is measuring nothing.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402

_console_safe_enable()

# ⚠ THE VENUE MUST NOT DECIDE THE VERDICT. main() exits 2 with "the websocket client is not
# installed" before it reaches a single line of ratchet code, and `assertNotEqual(rc, 0)` would
# then pass for a reason that has nothing to do with coverage — a green wearing a skip.
# So the import is satisfied with an inert stub when it is missing, and every law that expects a
# refusal also asserts on the TEXT of that refusal. [[feedback-blind-fixture-green-gate]]
try:
    import websocket  # noqa: F401
except Exception:                                        # pragma: no cover - venue-dependent
    import types
    sys.modules["websocket"] = types.ModuleType("websocket")

import render_check as R  # noqa: E402


RED_PROOF = [
    {
        "why": "the ratchet goes back to being SKIPPED on a subset run. `render_check.py vault` "
               "loses a node and exits 0 with an informational line about it — the whole of #72",
        "file": "render_check.py",
        "find": "    cov_missing = _coverage_check(results, _say, scope=set(targets), out=_cov)",
        "replace": "    cov_missing = (_coverage_check(results, _say, scope=set(targets), "
                   "out=_cov) if _full else 0)",
        "matches": 1,
    },
    {
        "why": "the scope branch is removed, so a subset run refuses every target it deliberately "
               "did not ask for. Over-correction is its own false verdict: a gate that is red for "
               "asking a narrow question teaches people to stop asking",
        "file": "render_check.py",
        "find": "        if name not in scope:",
        "replace": "        if False and name not in scope:",
        "matches": 1,
    },
    {
        "why": "a floor naming a target TARGETS no longer defines is filed as merely NOT CHECKED. "
               "A surface that stopped being registered is unmeasured for ever, and this is the "
               "one form of coverage loss a subset run can judge with no browser at all",
        "file": "render_check.py",
        "find": "            if name not in TARGETS:",
        "replace": "            if False and name not in TARGETS:",
        "matches": 1,
    },
    {
        "why": "the per-width STALE line is never printed, so a floor of 9 under a measurement of "
               "15 is silent again and the ratchet's own blind spot is invisible",
        "file": "render_check.py",
        "find": "    for n, k, is_, was in sorted(grew):\n        say(\"     \U0001f7e0 coverage ",
        "replace": "    for n, k, is_, was in sorted(grew)[:0]:\n        say(\"     \U0001f7e0 "
                   "coverage ",
        "matches": 1,
    },
    {
        "why": "a stale floor becomes a REFUSAL. Raising a floor needs a full clean run and a "
               "browser, so this makes the gate red on every subset run until someone finds one — "
               "and a gate that is only ever red is switched off inside a week",
        "file": "render_check.py",
        "find": "    rep[\"stale\"] = [[n, k, was, is_] for n, k, is_, was in sorted(grew)]",
        "replace": "    rep[\"stale\"] = [[n, k, was, is_] for n, k, is_, was in sorted(grew)]\n"
                   "    bad += len(grew)",
        "matches": 1,
    },
    {
        "why": "the six-row cap comes back. Six blind spots are named and the rest are dropped "
               "with no count — a truncated list of the gate's blind spots is itself a blind spot",
        "file": "render_check.py",
        "find": "    for n, k, is_, was in sorted(grew):\n        say(\"     \U0001f7e0 coverage ",
        "replace": "    for n, k, is_, was in sorted(grew)[:6]:\n        say(\"     \U0001f7e0 "
                   "coverage ",
        "matches": 1,
    },
    {
        "why": "the recorded slack is hard-coded to 0, so the durable record says the ratchet has "
               "no blind spot while the terminal says it has six. 0 must be a measurement here, "
               "never a placeholder",
        "file": "render_check.py",
        "find": "              \"coverageStaleNodes\": int(_cov.get(\"staleNodes\") or 0),",
        "replace": "              \"coverageStaleNodes\": 0,",
        "matches": 1,
    },
    {
        "why": "--bless stops refusing a partial run, so a subset can raise the floor from "
               "coverage it never fully measured. That is #72's own defect one layer down, and it "
               "is the thing this fix must not buy",
        "file": "render_check.py",
        "find": "    if not complete:",
        "replace": "    if False and not complete:",
        "matches": 1,
    },
    {
        "why": "putting the heart back to how v2916 shipped it: the slack is RECORDED and the "
               "heart does not read it, which is the exact state the cross-family eye caught - "
               "30 watched nodes could vanish and every supervisor still read clean.",
        "file": "heart2.py",
        "find": "            \"coverageStaleNodes\": (int(v[\"coverageStaleNodes\"])\n                                   if isinstance(v.get(\"coverageStaleNodes\"), int) else None),",
        "replace": "            \"_staleNodesRemovedByHeart2\": None,",
        "matches": 1,
    },
    {
        "why": "dropping the sentence leaves a bare integer. A number with no words is a number "
               "nobody acts on - the reader cannot tell 30 from 0 without being told what 30 means.",
        "file": "heart2.py",
        "find": "            \"coverageStaleSay\": _stale_say(v),",
        "replace": "            \"_staleSayRemoved\": None,",
        "matches": 1,
    },
    {
        "why": "making an ABSENT slack field read as a measured zero. An older render verdict never "
               "measured slack at all, and reporting that as 'no slack' answers a question nobody "
               "asked. [[unknown-stays-unknown]]",
        "file": "heart2.py",
        "find": "    if not isinstance(n, int):",
        "replace": "    if False:",
        "matches": 1,
    },
]


def _run(**widths):
    """A fake per-target result in the shape main() accumulates."""
    return {"ok": True, "why": "(fixture)", "refusals": [],
            "widths": {k: {"found": v, "painted": v} for k, v in widths.items()}}


class _Bench(unittest.TestCase):
    """A render_check with no browser, no repo writes and a floor this test owns."""

    def setUp(self):
        self._real = (R.COVERAGE, R.HERE, R._chrome_up, R._chrome_down, R.check)
        self.tmp = tempfile.mkdtemp(prefix="ratchet72-")
        R.COVERAGE = os.path.join(self.tmp, "render_coverage.json")
        # ⚠ HERE IS REDIRECTED SO THIS GATE CANNOT CLOBBER tv/.render_verdict.json — that file is
        # the last real run's record, and a test that overwrites it makes the heart report this
        # fixture as the state of his console. A harness must not edit the evidence.
        R.HERE = self.tmp
        R._chrome_up = lambda *a, **k: True
        R._chrome_down = lambda *a, **k: None

    def tearDown(self):
        R.COVERAGE, R.HERE, R._chrome_up, R._chrome_down, R.check = self._real
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ── bench helpers ──────────────────────────────────────────────────────────────
    def floor(self, d):
        with io.open(R.COVERAGE, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"floor": d}))

    def measure(self, per_target):
        """per_target: {name: {width: found}} -> patches check() to report exactly that."""
        R.check = lambda name, spec, _m=per_target: _run(**_m[name])

    def main(self, argv):
        import builtins
        out, real = [], builtins.print
        builtins.print = lambda *a, **k: out.append(" ".join(str(x) for x in a))
        try:
            rc = R.main(list(argv))
        finally:
            builtins.print = real
        text = "\n".join(out)
        # a venue failure must never be read as a verdict about coverage
        self.assertNotIn("websocket client is not installed", text)
        self.assertNotIn("no headless Chrome", text)
        return rc, text

    def verdict(self):
        p = os.path.join(self.tmp, ".render_verdict.json")
        self.assertTrue(os.path.exists(p), "main() wrote no verdict record at all")
        with io.open(p, encoding="utf-8") as fh:
            return json.load(fh)

    def a_real_target(self, n=0):
        return sorted(R.TARGETS)[n]


class ASubsetRunRatchetsWhatItActuallyRan(_Bench):

    def test_a_subset_run_that_LOSES_a_node_goes_RED_and_names_both_numbers(self):
        """LAW 1 — the headline. `render_check.py <one target>` losing a node must not exit 0."""
        t = self.a_real_target()
        self.floor({t: {"1120x628": 11}})
        self.measure({t: {"1120x628": 10}})
        rc, text = self.main([t])
        self.assertNotEqual(rc, 0,
                            "a SUBSET run measured 10 nodes against a floor of 11 and exited 0 — "
                            "the ratchet was skipped for a target this run actually rendered, so "
                            "a lost surface reads as clean.\n%s" % text[-900:])
        hit = [ln for ln in text.split("\n")
               if t in ln and "1120x628" in ln and "10" in ln and "11" in ln]
        self.assertTrue(hit,
                        "the drop was not reported with the target, the width and BOTH numbers, "
                        "so nobody can tell what was lost:\n%s" % text[-900:])

    def test_a_subset_run_does_NOT_refuse_the_targets_it_did_not_ASK_for(self):
        """LAW 2 — and it says they are UNKNOWN rather than saying nothing.

        The anti-over-correction law. Refusing every unasked target would make `--target` unusable
        and is a different false verdict, not a stricter one.
        """
        t, other = self.a_real_target(0), self.a_real_target(1)
        self.floor({t: {"1120x628": 11}, other: {"1120x628": 3}})
        self.measure({t: {"1120x628": 11}})
        rc, text = self.main([t])
        self.assertEqual(rc, 0,
                         "a subset run was refused for a target it deliberately did not ask for — "
                         "a narrow question is not a defect.\n%s" % text[-900:])
        self.assertIn("NOT CHECKED", text,
                      "the unasked target was passed over in silence. Not measured is UNKNOWN, "
                      "not clean, and silence is how it reads as clean.\n%s" % text[-900:])
        self.assertIn(other, text, "the unasked target was not named: %s" % text[-900:])

    def test_a_floor_naming_a_target_TARGETS_no_longer_defines_is_REFUSED(self):
        """LAW 3 — the one coverage loss judgeable with no browser at all."""
        t = self.a_real_target()
        self.floor({t: {"1120x628": 11}, "a_target_that_was_deleted": {"1120x628": 4}})
        self.measure({t: {"1120x628": 11}})
        rc, text = self.main([t])
        self.assertNotEqual(rc, 0,
                            "the floor names `a_target_that_was_deleted`, TARGETS does not define "
                            "it, and the run was green. A surface that stopped being registered "
                            "is unmeasured for ever.\n%s" % text[-900:])
        self.assertIn("a_target_that_was_deleted", text)
        self.assertIn("no longer defines", text)


class AStaleFloorIsALoudFactNotASilentPass(_Bench):

    STALE = {"w%02d" % i: i for i in range(1, 13)}          # floor 1..12
    GROWN = {"w%02d" % i: i + 2 for i in range(1, 13)}      # measured floor+2 -> 24 nodes of slack

    #: what `_stale_run` actually leaves on the floor: one target, every width, GROWN - STALE.
    #: Derived from the bench's own constants so the law can never drift from the fixture.
    @property
    def STALE_NODES(self):
        return sum(max(0, self.GROWN[k] - self.STALE[k]) for k in self.STALE)

    def _stale_run(self):
        t = self.a_real_target()
        self.floor({t: dict(self.STALE)})
        self.measure({t: dict(self.GROWN)})
        return (t,) + self.main([t])

    def test_a_stale_floor_prints_the_floor_the_measurement_and_the_GAP(self):
        """LAW 4 — 'floor 9, measured 15, STALE by 6' is the whole point of #72."""
        t, _rc, text = self._stale_run()
        self.assertIn("STALE", text,
                      "a floor 2 nodes under what was measured said nothing about being stale, so "
                      "the ratchet's own blind spot is invisible.\n%s" % text[-900:])
        want = [ln for ln in text.split("\n")
                if "w03" in ln and "floor 3" in ln and "measured 5" in ln and "STALE by 2" in ln]
        self.assertTrue(want,
                        "no line carried floor, measurement AND the gap together. A number "
                        "without its counterpart cannot be acted on.\n%s" % text[-1500:])

    def test_a_stale_floor_does_NOT_by_itself_fail_the_run(self):
        """LAW 5 — loud, not blocking. Raising a floor needs a full clean run and a browser."""
        _t, rc, text = self._stale_run()
        self.assertEqual(rc, 0,
                         "a stale floor failed the run. Every subset run would be red until "
                         "somebody found a browser to --bless with, and a gate that is only ever "
                         "red is switched off inside a week.\n%s" % text[-900:])

    def test_no_stale_row_is_SILENTLY_truncated(self):
        """LAW 6 — a truncated list of the gate's blind spots is itself a blind spot."""
        _t, _rc, text = self._stale_run()
        missing = [w for w in self.STALE if not any(w in ln and "STALE" in ln
                                                    for ln in text.split("\n"))]
        self.assertEqual(missing, [],
                         "these stale floors were never named and nothing said how many were "
                         "dropped: %s\n%s" % (missing, text[-1500:]))

    def test_the_slack_is_RECORDED_so_it_outlives_the_terminal(self):
        """LAW 7 — [[join-gate-heart]]: a verdict nobody records is a verdict nobody supervises.

        ⚠⚠ v2917 — AND THIS LAW TESTED THE HALF I DID WHILE ASSERTING THE HALF I DROPPED. v2916
        recorded the slack into .render_verdict.json, dropped the heart join because `surfaces` had
        no consumer, and then claimed in FOUR places that the heart supervises the fact. The
        cross-family eye caught it twenty minutes after it shipped. MEASURED: the file carried
        `coverageStaleNodes: 30` while `heart2.surface_verdict()` returned state OK with no such
        key, and a grep for a consumer outside render_check and this file returned ZERO.

        A law that only checks the WRITER can never notice that recording is not supervising — it
        passes precisely because the value is on disk. So this now asserts the READER: the heart
        must carry the number AND say what it means. [[the-unjoined-end]] [[plumbing-with-no-tap]        """
        _t, _rc, _text = self._stale_run()
        v = self.verdict()
        self.assertIn("coverageStaleNodes", v,
                      "the render verdict does not carry the ratchet's blind spot at all, so the "
                      "only witness is scrollback: %s" % sorted(v))
        self.assertEqual(v["coverageStaleNodes"], 24,
                         "the recorded slack is %r, measured 12 widths x 2 nodes = 24. A wrong "
                         "number here is worse than none." % v["coverageStaleNodes"])
        self.assertEqual(len(v.get("coverageStale") or []), 12,
                         "the per-width rows were not recorded: %r" % (v.get("coverageStale"),))

    def test_the_HEART_carries_the_slack_and_says_what_it_means(self):
        """⚠ THE CONSUMER, NOT THE WRITER. `heart2.surface_verdict()` is what an automated
        supervisor reads. If the slack is not in ITS answer, then 30 watched nodes can vanish and
        every supervisor still reads clean — which is the state v2916 shipped while claiming the
        opposite in four places.

        ⚠⚠ v2919 — AND THIS LAW READ THE MACHINE'S OWN FILE, NOT THE FIXTURE. Caught by the
        cross-family eye on v2917. It called `surface_verdict()` with NO path, so it read the live
        gitignored `tv/.render_verdict.json` while the bench wrote its 24-node fixture to
        `self.tmp`. The two never met. MEASURED: on an absent file `surface_verdict()` returns only
        ['state', 'why'], so the law is RED UNTAMPERED on a fresh clone, in CI, or inside a prove
        sandbox — which marks the WHOLE gate UNPROVABLE, the eight original ratchet laws included.
        It passed here solely because this Mac had rendered. That is v2871's scar in the sibling
        file, repeated: a law that grades the machine's own verdict can only pass on a machine that
        just ran. `path=` exists so a law can ask the real question without touching his files.
        [[feedback-blind-fixture-green-gate]] [[feedback-fixtures-never-touch-live-data]]
        """
        import heart2
        t, rc, text = self._stale_run()
        v = heart2.surface_verdict(os.path.join(self.tmp, ".render_verdict.json"))
        # ⚠ THE VALUE, NOT THE KEY. `assertIn("coverageStaleNodes", v)` passes on a None, and any
        # sentence over 20 characters satisfied the old check — including a sentence saying the
        # slack is UNKNOWN. Both were true of a verdict that measured nothing.
        self.assertEqual(v.get("coverageStaleNodes"), self.STALE_NODES,
                         "the heart must carry the MEASURED slack (%d), not %r — a key whose value "
                         "is None is a number nobody can act on"
                         % (self.STALE_NODES, v.get("coverageStaleNodes")))
        say = str(v.get("coverageStaleSay") or "")
        self.assertIn(str(self.STALE_NODES), say,
                      "the sentence must name the number it is about: %r" % say)
        self.assertNotIn("UNKNOWN", say,
                         "the slack was MEASURED here, so the heart must not report it unknown: %r"
                         % say)

    def test_an_older_verdict_reads_UNKNOWN_and_never_a_quiet_zero(self):
        """⚠ ABSENT IS NOT ZERO. A render verdict written before v2916 has no slack field at all.
        Reporting that as 0 would say 'no slack' about a question nobody asked.
        [[unknown-stays-unknown]] [[zero-needs-a-denominator]]"""
        import heart2, tempfile, json as _j, os as _os
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            _j.dump({"full": True, "totalTargets": 2, "reported": ["a", "b"],
                     "coverageMissing": 0, "renderFailures": 0}, fh)
            old_path = fh.name
        try:
            v = heart2.surface_verdict(old_path)
            self.assertIsNone(v.get("coverageStaleNodes"),
                              "an older verdict with no slack field must read UNKNOWN, not 0: %r"
                              % v.get("coverageStaleNodes"))
            self.assertIn("UNKNOWN", str(v.get("coverageStaleSay") or ""),
                          "and it must SAY unknown: %r" % v.get("coverageStaleSay"))
        finally:
            _os.unlink(old_path)


class ASubsetMayNeverRaiseTheFloor(_Bench):

    def test_bless_still_REFUSES_a_subset_run_and_writes_nothing(self):
        """LAW 8 — the thing this fix must not buy. Blessing coverage never fully measured is
        #72's own defect one layer down."""
        t = self.a_real_target()
        self.floor({t: {"1120x628": 11}})
        with io.open(R.COVERAGE, encoding="utf-8") as fh:
            before = fh.read()
        self.measure({t: {"1120x628": 40}})
        rc, text = self.main([t, "--bless"])
        self.assertEqual(rc, 2,
                         "a SUBSET run was allowed to bless. It measured one target and would "
                         "write a floor speaking for all of them.\n%s" % text[-900:])
        with io.open(R.COVERAGE, encoding="utf-8") as fh:
            after = fh.read()
        self.assertEqual(after, before, "a refused bless still rewrote the floor file")


if __name__ == "__main__":
    unittest.main(verbosity=2)
