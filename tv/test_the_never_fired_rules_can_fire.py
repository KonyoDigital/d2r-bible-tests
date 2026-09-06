# -*- coding: utf-8 -*-
"""v2750 — FIVE RETENTION RULES HAD NEVER RUN, AND NOBODY COULD SAY WHETHER THEY WORKED.

`reel_retention.plan()` over his 40 reels reports its own blind spot, in its own words:

    "5 rule(s) were NEVER REACHED on these 40 reel(s) — no-witness-index, never-chronicle-swept,
     rows-not-banked, vault-owes, eligible. That is UNMEASURED, not fine and not broken: nothing in
     this footage gets far enough down the chain to test them."

MEASURED keep tags on his shelf: zero-pages 27 · test-fixture 8 · recent 5. `zero-pages` catches 27
of 40, and A PAID READ IS EXACTLY WHAT CLEARS IT.

=== THE CIRCLE THIS FILE BREAKS, AND WHY IT WAS WORTH BREAKING FOR FREE ===
His money ruling (2026-09-04) is AFFIRMATIVE — *"money needs to be spent... more focused reads where
needed"* — with a condition and a sequencing:
    "a paid pass may run AFTER the path that consumes it is proven, never as the thing that proves it"
But the path below `zero-pages` could not be proven WITHOUT pages, and pages cost money. That circle
— not his decision, which he gave in writing and re-affirmed — is why this had not moved.
A synthetic reel that HAS pages walks the same chooser and settles it for nothing. If the rules below
`zero-pages` had refused it, the money would have bought a step that dead-ends anyway: the "not
looped" half of his condition, and [[paid-work-with-no-memory]] exactly — 3,434 paid reads for 2
sightings, looking like healthy activity.

⚠ REG-570 IS WHAT MAKES THIS HONEST. Before it, `plan(hist_dir=<scratch>)` read Konyo's LIVE
chronicle_swept (401 entries) and ignored the caller's, so "every sabotage ever aimed at this chooser
was graded against live data it could not control". A fixture that cannot control what the chooser
sees measures the chooser's opinion of HIS footage, not of the fixture.
[[feedback-fixtures-never-touch-live-data]]

⚠ keep_recent=0 IS DELIBERATE AND IS ALSO A LIMIT. `recent` and `test-fixture` sit ABOVE the rules
under test and would catch every fixture reel first — a probe that never reaches its subject grades
nothing. The cost is that this file proves FIVE rules, not eight, and says so rather than implying
the chain is wholly exercised.
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import io  # noqa: E402
import json  # noqa: E402

import reel_retention as RR  # noqa: E402

#: reel -> the ONE rule it is shaped to land on
SHAPES = {
    "reel_s_9000001_1": "never-chronicle-swept",   # no chronicle entry at all
    "reel_s_9000002_2": "zero-pages",              # swept, read nothing
    "reel_s_9000003_3": "rows-not-banked",         # vault rows exist, none durable
    "reel_s_9000004_4": "vault-owes",              # no vault entry, lane still owes
    "reel_s_9000005_5": "eligible",                # pages read, nothing owed
}


def _build(hist):
    for reel in SHAPES:
        d = os.path.join(hist, reel)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "f0001.jpg"), "wb") as fh:
            fh.write(b"\x00" * (2 * 1024 * 1024))
    chron = {"reel_s_9000002_2": {"pages": 0},
             "reel_s_9000003_3": {"pages": 3},
             "reel_s_9000004_4": {"pages": 3},
             "reel_s_9000005_5": {"pages": 3}}
    vault = {"reel_s_9000002_2": {"rows": 0},
             "reel_s_9000003_3": {"rows": 4},
             "reel_s_9000005_5": {"rows": 0},
             "reel_s_9000001_1": {"rows": 0}}
    io.open(os.path.join(hist, "chronicle_swept.json"), "w", encoding="utf-8").write(json.dumps(chron))
    io.open(os.path.join(hist, "vault_swept.json"), "w", encoding="utf-8").write(json.dumps(vault))


def _tags(hist):
    p = RR.plan(hist_dir=hist, keep_recent=0)
    got = {}
    for r in (p.get("kept") or []):
        got[r.get("reel")] = r.get("tag")
    for r in (p.get("candidates") or []):
        got[r.get("reel")] = r.get("tag") or "eligible"
    return p, got


class TheNeverFiredRulesCanFire(unittest.TestCase):

    def setUp(self):
        self.hist = tempfile.mkdtemp(prefix="never_fired_")
        _build(self.hist)

    def tearDown(self):
        shutil.rmtree(self.hist, ignore_errors=True)

    # ── ⚠ THE PROBE MUST REACH ITS SUBJECT ────────────────────────────────────────────────────
    def test_the_fixture_actually_reaches_the_chooser(self):
        """A probe whose reels never enter the plan grades nothing and reports clean."""
        p, got = _tags(self.hist)
        self.assertTrue(p.get("ok"), "plan() refused the fixture: %s" % str(p.get("say"))[:140])
        self.assertEqual(set(SHAPES), set(got),
                         "the fixture's reels did not all reach the chooser — missing %s"
                         % sorted(set(SHAPES) - set(got)))

    def test_the_fixture_controls_the_LEDGERS_not_just_the_frames(self):
        """⚠ REG-570. If the caller's ledgers are ignored, every verdict below is about HIS 401
        chronicle entries rather than the four written here, and the file proves nothing."""
        p, got = _tags(self.hist)
        self.assertEqual("zero-pages", got.get("reel_s_9000002_2"),
                         "a reel this fixture recorded as pages=0 did not land on zero-pages — the "
                         "scratch ledger is being ignored, so the chooser is reading somebody "
                         "else's data (REG-570)")

    # ── ⚠⚠ THE LAW: each rule fires on the shape built for it ─────────────────────────────────
    def test_each_of_the_five_rules_fires_on_its_own_shape(self):
        _, got = _tags(self.hist)
        wrong = [(reel, want, got.get(reel)) for reel, want in SHAPES.items()
                 if got.get(reel) != want]
        self.assertEqual([], wrong,
                         "a rule that has NEVER fired on his footage also does not fire on a reel "
                         "built for it — so the chain below zero-pages is broken, not merely "
                         "unreached, and a paid read would buy a step that dead-ends: %r" % wrong)

    def test_a_clean_reel_becomes_ELIGIBLE_rather_than_being_held_forever(self):
        """The load-bearing one for the money question: a reel that HAS pages and owes nothing must
        come out the far end. If it does not, no read can ever finish a reel."""
        _, got = _tags(self.hist)
        self.assertEqual("eligible", got.get("reel_s_9000005_5"),
                         "a fully-read, nothing-owed reel was still held (%r). No paid read could "
                         "ever finish a reel, and the spend would be pure loss."
                         % got.get("reel_s_9000005_5"))

    # ── ⚠ WHAT THIS FILE DOES NOT CLAIM ───────────────────────────────────────────────────────
    def test_it_does_not_pretend_to_exercise_the_whole_chain(self):
        """`recent` and `test-fixture` sit ABOVE these rules and are bypassed with keep_recent=0 so
        the subject is reachable at all. Claiming the chain is wholly proven would be false, and a
        green wider than its evidence is the thing this repo keeps paying for."""
        p, _ = _tags(self.hist)
        never = set(p.get("neverFired") or [])
        for still in ("test-fixture", "recent"):
            self.assertIn(still, never,
                          "%r now reports as fired, which means keep_recent=0 stopped bypassing it "
                          "and the five rules under test may no longer be what is being graded"
                          % still)

    def test_the_live_shelf_still_reports_its_own_blind_spot(self):
        """⚠ THE PREMISE. If his footage ever DOES reach these rules, this file's reason for
        existing changes and someone should re-read it rather than trust its green. [[stale-reading]]"""
        p = RR.plan()
        never = set(p.get("neverFired") or [])
        self.assertTrue(never & {"never-chronicle-swept", "rows-not-banked", "vault-owes", "eligible"},
                        "his live shelf no longer reports these rules as never-reached, so the "
                        "circumstance this fixture stands in for has changed — re-read the premise "
                        "before trusting this suite. neverFired=%r" % sorted(never))


if __name__ == "__main__":
    unittest.main(verbosity=2)
