#!/usr/bin/env python3
"""v1532 — THE WHOLE CHAIN, IN ONE TEST.

Every link in the Chronicle arc has its own tests, and every one of them passes. That is not the
same as the chain working: each suite mocks its neighbours, so a contract could drift on BOTH sides
of a seam and every suite would stay green while the thing itself was broken. This walks it end to
end — the live agent sees the panel, the visit is recorded, the visit is swept, the pages are read
on two lanes, the gate judges, and the proposal comes out the far side — with only the VISION
stubbed, because that is the one part that cannot run for free.

It costs nothing (TV_STUB on both lanes) and takes about a second, so it belongs in the gate set
rather than in a document nobody runs.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import console_safe  # noqa: F401,E402  — non-ASCII failure text must survive a non-UTF-8 console
import chronicle_retro as cr  # noqa: E402


def _pillow():
    try:
        from PIL import Image  # noqa: F401
        return True
    except Exception:
        return False



def _screenish(size, seed, shade=None):
    """v1543 — a fixture frame that looks like a SCREEN, not a paint swatch.

    These stood in for captured frames as a single flat colour, which is precisely what
    chronicle_retro.is_dead_frame() now refuses as a blank capture — so every fixture run read as a
    dead one and the sweep stopped being exercised at all. A fixture that could not survive the
    product's own liveness check was never simulating a frame; it was simulating a bug.

    Deterministic, so frames built with the same seed are byte-identical and still group into one
    still run.
    """
    import random
    from PIL import Image
    w, h = size
    rnd = random.Random(seed)
    im = Image.new("RGB", (w, h))
    base = shade if shade is not None else 40
    im.putdata([(rnd.randrange(256), (base + rnd.randrange(120)) % 256, rnd.randrange(256))
                for _ in range(w * h)])
    return im

class TestTheWholeChain(unittest.TestCase):
    """live panel → recorded visit → swept → read on two lanes → gated → proposed."""

    def setUp(self):
        if not _pillow():
            self.skipTest("Pillow absent — the frame grouping needs to decode JPEGs")
        os.environ["TV_PORT"] = "17994"          # never collide with a live agent
        import tv_diablo as tv
        self.tv = tv
        self.d = tempfile.mkdtemp()
        # ── FIXTURES NEVER TOUCH LIVE DATA ──────────────────────────────────────────────────────
        # This setUp isolated the PORT and stopped there. The console's state files were left
        # pointing at the real ones, and this class drives _chron_visit_run directly — so every run
        # of the gates on his Mac overwrote tv/chron_last_result.json, the console's persisted
        # sweep, with THIS fixture: "Harlequin Crest" and "Windforce" seen across reels s_100/200/300.
        # Caught by reading that file expecting his footage and finding the fixture, timestamped to
        # the last gate run.
        #
        # It became dangerous the same day: v1765 wired his board to ADOPT a persisted sweep
        # automatically, and this fixture carries four witnesses, so it would have been applied
        # rather than queued. Neither name is in his grail — both would have been ticked as finds he
        # never made, into the one dataset that is supposed to be his own truth.
        #
        # Redirected here, and enforced by a gate that fails if any suite run mutates the live files.
        import control_app as _ca
        self._live_paths = {}
        for _attr, _name in (("_CHRON_RESULT_PATH", "result.json"),
                             ("_CHRON_AUTOREAD_PATH", "autoread.json"),
                             ("_CHRON_SWEPT_PATH", "swept.json"),
                             ("_CHRON_EVIDENCE_PATH", "evidence.json")):
            if hasattr(_ca, _attr):
                self._live_paths[_attr] = getattr(_ca, _attr)
                setattr(_ca, _attr, os.path.join(self.d, _name))
        self._ca = _ca
        self.reel = os.path.join(self.d, "reel_s_chain")
        os.makedirs(self.reel)
        from PIL import Image
        # 6 frames of one held panel, then 2 of a different one — a real visit's shape
        for n in range(8):
            shade = 30 if n < 6 else 200
            _screenish((64, 48), shade, shade).save(
                os.path.join(self.reel, "f%d.jpg" % n))
        self.man = os.path.join(self.d, "man.json")
        with open(self.man, "w", encoding="utf-8") as fh:
            json.dump({
                # what CLAUDE sees on a chronicle page
                "*#chronicle": {"found": ["Harlequin Crest", "Windforce"],
                                "notFound": ["Stormshield"],
                                "printedFound": 2, "printedTotal": 3, "conf": 0.9},
                # what GROK sees — deliberately DIFFERENT, so the disagreement is exercised
                "*#chronicle-grok": {"found": ["Harlequin Crest"],
                                     "notFound": ["Stormshield", "Windforce"], "conf": 0.85},
            }, fh)
        self._env = {k: os.environ.get(k) for k in ("TV_STUB", "TV_STUB_MANIFEST", "TV_HIST")}
        os.environ.update({"TV_STUB": "1", "TV_STUB_MANIFEST": self.man, "TV_HIST": self.d})
        tv._CHRON_VISIT.update({"open": False, "ledger": "", "since": 0, "last": 0, "frames": []})

    def tearDown(self):
        for _attr, _orig in getattr(self, "_live_paths", {}).items():
            setattr(self._ca, _attr, _orig)
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.d, ignore_errors=True)

    # ── the chain ────────────────────────────────────────────────────────────────────────────
    def _record_a_visit(self):
        """He opens the Chronicle, scrolls, and leaves — exactly what the live loop would see."""
        tv = self.tv
        for n in range(6):
            tv._chron_visit_step("chronicle", "uniques" if n == 0 else "",
                                 frame_id="reel_s_chain/f%d" % n, ts=1000 + n)
        return tv._chron_visit_step("gameplay", "", frame_id=None, ts=1100)

    def test_the_whole_chain_holds(self):
        visit = self._record_a_visit()
        # 1) THE LIVE LANE recorded it, with the ledger stuck across frames that lost the tab
        self.assertEqual(visit["n"], 6)
        self.assertEqual(visit["ledger"], "uniques")

        # 2) THE SWEEP reads that visit — no classify, one page for six held frames
        import g5_grok_eyes as g5
        paths = [os.path.join(self.d, f + ".jpg") for f in visit["frames"]]
        for p in paths:
            self.assertTrue(os.path.isfile(p), "the chain broke at the frame-id → path seam")
        read = cr.two_lane_reader(
            lambda p, k: self.tv.claude_chronicle_read(p, k),
            lambda p, k: g5.g5_chronicle_read(p, k))
        swept = cr.sweep_frames(paths, "chronicle-" + visit["ledger"], read)
        self.assertEqual(swept["classified"], 0)
        self.assertEqual(swept["pagesRead"], 1, "six frames of one held panel is ONE page")

        # 3) BOTH LANES answered, in the same units
        resp = swept["pages"][0]["resp"]
        self.assertEqual(resp["lanesRan"], ["claude", "grok"])
        self.assertEqual(resp["laneAgreement"]["both"], ["Harlequin Crest"])
        self.assertEqual(resp["laneAgreement"]["claudeOnly"], ["Windforce"])

        # 4) THE PROPOSAL keeps one sighting per lane
        prop = cr.proposal_from_pages(swept["pages"])
        self.assertEqual(len(prop["uniques"]["Harlequin Crest"]), 2)
        self.assertEqual(len(prop["uniques"]["Windforce"]), 1)

        # 5) THE GATE grounds what two independent eyes saw and HOLDS what one did
        out = cr.apply_proposal(prop, {"uniques": [], "sets": []}, gate=cr.strict_gate())
        self.assertEqual(out["uniques"]["added"], ["Harlequin Crest"])
        held = [h["name"] for h in out["held"]]
        self.assertIn("Windforce", held)

    def test_a_visit_the_reader_never_identified_dead_ends_SAFELY(self):
        # ★ the whole chain's most dangerous input: frames that ARE a chronicle but whose ledger was
        # never read. Every layer must refuse rather than pick a side.
        tv = self.tv
        for n in range(4):
            tv._chron_visit_step("chronicle", "", frame_id="reel_s_chain/f%d" % n, ts=2000 + n)
        visit = tv._chron_visit_step("town", "", None, 2100)
        self.assertEqual(visit["ledger"], "")
        # the classifier refuses to name a kind...
        self.assertIsNone(cr.chronicle_kind({"scene": "chronicle", "chronicleTab": ""}))
        # ...and the console REFUSES to sweep it, out loud
        import control_app as ca
        from unittest import mock
        with ca._CHRON_LOCK:
            ca._CHRON_JOB.update({"running": False, "phase": "idle", "error": None,
                                  "lanes": ["claude"]})
        rows = [{"ts": 4242, "ledger": "", "n": 4, "frames": visit["frames"], "label": "📜"}]
        with mock.patch.object(ca, "chronicle_visits", return_value={"visits": rows}):
            ca._chron_visit_run(4242)
        st = ca.chronicle_sweep_state()
        self.assertEqual(st["phase"], "error")
        self.assertIn("ledger was never read", st["error"])
        self.assertIsNone(st["result"], "a refused sweep must leave NO proposal behind")

    def test_the_two_lanes_speak_the_SAME_contract_end_to_end(self):
        # a seam that could drift on both sides while every suite stayed green
        import g5_grok_eyes as g5
        p = os.path.join(self.reel, "f0.jpg")
        c = self.tv.claude_chronicle_read(p, "chronicle-uniques")
        g = g5.g5_chronicle_read(p, "chronicle-uniques")
        self.assertIsNotNone(c)
        self.assertIsNotNone(g)
        self.assertEqual(sorted(c.keys()), sorted(g.keys()),
                         "the lanes have drifted apart — cross-lane agreement would be meaningless")
        self.assertEqual(c["ledger"], g["ledger"])
        self.assertNotEqual(c["lane"], g["lane"])

    def test_a_dead_second_lane_never_reads_as_agreement(self):
        # the failure that would quietly inflate every witness count in the system
        read = cr.two_lane_reader(lambda p, k: self.tv.claude_chronicle_read(p, k), None)
        resp = read(os.path.join(self.reel, "f0.jpg"), "chronicle-uniques")
        self.assertEqual(resp["lanesRan"], ["claude"])
        self.assertEqual(resp["laneNote"], "grok-silent")
        prop = cr.proposal_from_pages([{"reel": "s1", "frame": "f0.jpg", "resp": resp}])
        for nm, sightings in prop["uniques"].items():
            self.assertNotIn("cross-lane", cr.witnesses(sightings))



class TestTheDoctorTellsTheTruth(unittest.TestCase):
    """v1533 — a health check that overstates is worse than none: it sends him to fix what is not
    broken, and hides what is."""

    def setUp(self):
        import chronicle_doctor as cd
        self.cd = cd

    def test_it_runs_and_answers_every_check(self):
        d = self.cd.diagnose()
        self.assertEqual(len(d["checks"]), len(self.cd.CHECKS))
        for r in d["checks"]:
            self.assertIn(r["state"], (self.cd.OK, self.cd.MISSING, self.cd.UNKNOWN))
            self.assertTrue(r["detail"], r["name"] + " answered with no reason")

    def test_UNKNOWN_is_never_counted_as_broken(self):
        # ★ "I could not check" and "it is broken" are different sentences. Collapsing them is how a
        # health check starts lying — and it lies in the direction that wastes his time.
        d = self.cd.diagnose()
        for name in d["unknown"]:
            self.assertNotIn(name, d["blocking"])

    def test_a_check_that_CRASHES_is_unknown_not_a_failure(self):
        r = self.cd._check("boom", lambda: 1 / 0)
        self.assertEqual(r["state"], self.cd.UNKNOWN)
        self.assertIn("the check itself failed", r["detail"])

    def test_a_MISSING_check_says_what_to_do_about_it(self):
        # a health check that names a problem without a next step is just an alarm
        for r in self.cd.diagnose()["checks"]:
            if r["state"] == self.cd.MISSING:
                self.assertGreater(len(r["detail"]), 30, r["name"] + " reported missing with no fix")

    def test_a_SILENT_GROK_does_not_block_readiness(self):
        # one eye is a working system — it just scores lower at the gate. Calling that "not ready"
        # would push him to fix something that is not wrong.
        self.assertNotIn("grok lane", self.cd.diagnose()["blocking"])

    def test_the_things_that_DO_block_are_the_things_that_stop_it_working(self):
        import chronicle_doctor as cd
        src = open(cd.__file__, encoding="utf-8").read()
        for name in ("reader prompts", "claude lane", "frame grouping", "board apply"):
            self.assertIn(name, src)


class TestTheSecondEyeReceipt(unittest.TestCase):
    """v1905 — READY IS NOT ASKED, AND ASKED IS NOT ANSWERED.

    The doctor's `grok lane` check reports the lane is AVAILABLE. That is a status lamp, and a lamp
    has been wrong on this exact lane before: G5 sat pinned PRIMARY and silently dark for weeks
    while every honesty surface read clean, because a lane that never attempts never records a
    failure. The receipt check reads the BANKED EVIDENCE — written by the readers themselves — and
    answers the only question that matters: of the names Claude has seen, how many did the second
    eye actually corroborate? [[grok-second-eye]]

    Measured on his own evidence when this was written: uniques 35/298 (12%), sets 34/86 (40%).
    """

    def _with_evidence(self, payload):
        import json as _json
        import shutil
        import tempfile
        from unittest import mock
        import chronicle_doctor as cd
        import control_app as ca
        root = tempfile.mkdtemp(prefix="receipt-")
        self.addCleanup(shutil.rmtree, root, True)
        path = os.path.join(root, "chron_evidence.json")
        if payload is not None:
            with open(path, "w", encoding="utf-8") as fh:
                _json.dump(payload, fh)
        with mock.patch.object(ca, "_CHRON_EVIDENCE_PATH", path):
            return cd._second_eye_receipt()

    def test_a_lane_that_corroborated_nothing_is_not_a_witness(self):
        import chronicle_doctor as cd
        state, detail = self._with_evidence(
            {"uniques": {"Shako": [{"lane": "claude"}], "Ali Baba's": [{"lane": "claude"}]},
             "sets": {}})
        self.assertEqual(state, cd.MISSING,
                         "a second eye that has corroborated nothing reported OK: %r" % detail)
        self.assertIn("corroborated NOTHING", detail)

    def test_corroboration_is_counted_per_ledger(self):
        import chronicle_doctor as cd
        state, detail = self._with_evidence(
            {"uniques": {"Shako": [{"lane": "claude"}, {"lane": "grok"}],
                         "Ali Baba's": [{"lane": "claude"}]},
             "sets": {"Isenhart's Parry": [{"lane": "grok"}]}})
        self.assertEqual(state, cd.OK, detail)
        self.assertIn("uniques 1/2 (50%)", detail)
        self.assertIn("seen only by grok", detail,
                      "a name only the second eye saw is the strongest thing it can report, "
                      "and it was not reported: %r" % detail)

    def test_no_evidence_is_UNKNOWN_never_a_failure(self):
        """'I could not check' and 'it is broken' are different sentences — the doctor's own
        doctrine, and collapsing them is how a health check starts lying."""
        import chronicle_doctor as cd
        state, detail = self._with_evidence(None)
        self.assertEqual(state, cd.UNKNOWN, detail)
        self.assertIn("nothing has been swept", detail)

    def test_the_report_column_is_sized_from_the_data(self):
        """A hardcoded width silently un-aligns the whole report the moment a check has a longer
        name — which is exactly what adding this check did (`second eye receipt` is 18 chars against
        a `%-16s`). The width comes from the longest name now, so the report cannot drift."""
        import subprocess
        import chronicle_doctor as cd
        out = subprocess.run([sys.executable, os.path.join(HERE, "chronicle_doctor.py")],
                             capture_output=True, text=True, timeout=600)
        self.assertEqual(out.returncode, 0, out.stderr[-300:])
        names = [n for n, _fn in cd.CHECKS]
        w = max([len(n) for n in names] + [12])
        for name in names:
            row = [l for l in out.stdout.split("\n") if l.startswith("  ") and name in l]
            self.assertTrue(row, "the report skipped the %r check" % name)
            at = row[0].index(name)
            detail_at = at + w + 1
            self.assertGreater(len(row[0]), detail_at, "%r has no detail" % name)
            self.assertNotEqual(row[0][detail_at], " ",
                                "the detail column does not start where the padding ends for %r "
                                "— the report is un-aligned:\n%s" % (name, row[0]))


class TestANotFoundReceiptSurvivesTheWholeChain(unittest.TestCase):
    """THE JOIN, END TO END, THROUGH THE REAL PERSISTENCE PATH — no mocks.

    v1923 made a not-found reading expire when a later look disagrees, and I told Konyo the receipts
    that make that possible "arrive on the next sweep". That is a PROMISE, and a promise about a
    seam is exactly the shape this file exists to refuse: `proposal_from_pages` writing a receipt
    and `resolve_contested` reading one are two halves that can each be perfect while nothing joins
    them, and the failure would be silent by construction. [[the-unjoined-end]]

    So this walks the real thing: a page that reads a piece NOT FOUND, a later page that reads it
    FOUND, through merge_proposals and through _chron_evidence_save/_load to disk and back, and
    asserts the resolver calls the older not-found EXPIRED rather than a contradiction.

    That is the precise case behind the wrong answer of 2026-08-21 — "12 of your 36 set pieces are
    ones the game shows as not-found", when three of them had been found since and the true number
    was one. If this test ever goes red, that answer becomes possible again.
    """

    def test_the_receipt_is_written_survives_the_merge_and_reaches_the_resolver(self):
        tmp = tempfile.mkdtemp(prefix="receipt-chain-")
        sys.path.insert(0, HERE)
        import chronicle_retro as cr
        import control_app as ca
        import counter_ledger as cl

        # ⚠ THE ENV VAR IS READ ONCE, AT IMPORT. `_CHRON_EVIDENCE_PATH` is a module-level constant
        # bound from TV_CHRON_EVIDENCE when control_app is first imported — which, in a suite, has
        # already happened. Setting the environment here changes NOTHING and the write lands on his
        # real banked evidence.
        #
        # The first draft of this test did exactly that and **truncated tv/chron_evidence.json from
        # 525,187 bytes to 748** — 298 proposed uniques and 86 set pieces across 767 paid-for page
        # reads, replaced by a two-item fixture. It was recovered in full from chron_last_result.json,
        # which holds the same proposal; had that file not existed, the only way back would have been
        # re-reading his entire history at full price.
        #
        # So: patch the ATTRIBUTE, and then ASSERT THE REDIRECT TOOK. Setting up a redirect and never
        # checking it is the whole defect — the fixture looked isolated and was not.
        # [[feedback-fixtures-never-touch-live-data]]
        live = ca._CHRON_EVIDENCE_PATH
        before = os.path.getsize(live) if os.path.isfile(live) else None
        # v1925 — THROUGH THE SHARED HELPER, not by hand. conftest.redirect_module_path patches the
        # ATTRIBUTE and asserts the redirect took; doing it inline here left that helper with zero
        # call sites, so the repo prescribed an API nobody used and the prescription was untested.
        # A helper nothing calls is a helper nothing proves. [[the-unjoined-end]]
        # ⚠ FROM pathguard, NOT conftest. run_gates.py runs this file as a plain script and the
        # agent-tests runner has NO pytest, so importing conftest (which does `import pytest` at
        # module level) turned this into a CI ERROR for nine consecutive runs while every local
        # signal was green. [[test-venue]]
        from pathguard import redirect_module_path
        with redirect_module_path(ca, "_CHRON_EVIDENCE_PATH", os.path.join(tmp, "ev.json")):
            self.assertNotEqual(ca._CHRON_EVIDENCE_PATH, live,
                                "the redirect did not take — refusing to run a write test that "
                                "would land on live data")
            self._chain_body(cr, ca, cl, tmp)
        after = os.path.getsize(live) if os.path.isfile(live) else None
        shutil.rmtree(tmp, ignore_errors=True)
        self.assertEqual(after, before,
                         "THIS TEST WROTE TO THE LIVE BANKED EVIDENCE (%s). Those bytes were paid "
                         "for by real page reads." % live)

    def _chain_body(self, cr, ca, cl, tmp):
        if True:

            older = [{"reel": "s_1787177267889_92273", "frame": "f_1787177277865.jpg",
                      "resp": {"ledger": "sets", "lane": "claude",
                               "found": ["Aldur's Rhythm (mace)"],
                               "notFound": ["Natalya's Soul (claws)"]}}]
            p1 = cr.proposal_from_pages(older)
            seen = (p1.get("notFoundSeen") or {}).get("sets") or {}
            self.assertIn("Natalya's Soul (claws)", seen,
                          "the not-found reading reached the proposal with NO receipt — which is "
                          "the state that made a claim on undatable evidence possible")
            self.assertTrue(seen["Natalya's Soul (claws)"][0].get("frame"),
                            "a receipt with no frame cannot be ordered, so it is not a receipt")

            newer = [{"reel": "s_1787999999999_1", "frame": "f_1787999999999.jpg",
                      "resp": {"ledger": "sets", "lane": "grok",
                               "found": ["Natalya's Soul (claws)"]}}]
            merged = cr.merge_proposals(p1, cr.proposal_from_pages(newer))
            self.assertTrue((merged.get("notFoundSeen") or {}).get("sets"),
                            "merge_proposals dropped the receipts")

            ca._chron_evidence_save(merged)
            back = ca._chron_evidence_load()
            self.assertTrue((back or {}).get("notFoundSeen"),
                            "the receipts did not survive the round trip to disk")

            r = cl.resolve_all(back)
            v = (r.get("sets") or {}).get("Natalya's Soul (claws)")
            self.assertIsNotNone(v, "the resolver never saw the contested name")
            self.assertEqual(v["verdict"], "found",
                             "the not-found look is OLDER than the found one, so it is expired — "
                             "calling this a contradiction is the 12-vs-1 defect")


    def test_the_same_chain_still_reports_a_REAL_contradiction(self):
        """Seen red for its own reason: if the newer look is the not-found one, it must survive as
        a contradiction. A resolver that expires everything is as useless as one that expires
        nothing. [[feedback-blind-fixture-green-gate]]"""
        sys.path.insert(0, HERE)
        import chronicle_retro as cr
        import counter_ledger as cl
        found_first = [{"reel": "s_1787177267889_92273", "frame": "f_1787177277865.jpg",
                        "resp": {"ledger": "sets", "lane": "claude",
                                 "found": ["Natalya's Soul (claws)"]}}]
        nf_later = [{"reel": "s_1787999999999_1", "frame": "f_1787999999999.jpg",
                     "resp": {"ledger": "sets", "lane": "grok",
                              "notFound": ["Natalya's Soul (claws)"]}}]
        merged = cr.merge_proposals(cr.proposal_from_pages(found_first),
                                    cr.proposal_from_pages(nf_later))
        v = (cl.resolve_all(merged).get("sets") or {}).get("Natalya's Soul (claws)")
        self.assertEqual(v["verdict"], "not-found",
                         "the NEWER look says not-found, so this is a real contradiction and must "
                         "not be expired away")



class TestV2150TheMergeAsksTheResolverToo(unittest.TestCase):
    """THE CONTESTED RULE EXISTED TWICE AND ONLY ONE COPY WAS EVER FIXED.

    proposal_from_pages learned to ask resolve_contested whether the NEWEST look says found, and
    to leave such a name out of `contested`. merge_proposals recomputed the same field at its tail
    with the original rule — `if _nm in _nf`, membership only. EVERY SWEEP AFTER THE FIRST goes
    through the merge, so the unfixed copy was the one that wrote his screen.

    Measured on his live chron_last_result.json before this fix:
        contested            64   (uniques 13, sets 51)
        the resolver says    34   (uniques 13, sets 21)
        contestedResolved / contestedExpired / notFoundDatable   ALL ABSENT
    Thirty names, every one a set whose newest reading FOUND it. And because contestedExpired was
    never written by the merge, the console verdict card that reports exactly this population
    ("N were read both ways and the NEWEST look says found") had no field to render from — it
    could not appear on his machine at all. [[copy-drift]] [[the-unjoined-end]]
    """

    OLD_NF = {"reel": "s_1787000000000_1", "frame": "f_1787000000000.jpg",
              "resp": {"ledger": "sets", "lane": "grok", "notFound": ["Natalya's Soul (claws)"]}}
    NEW_FOUND = {"reel": "s_1787999999999_9", "frame": "f_1787999999999.jpg",
                 "resp": {"ledger": "sets", "lane": "claude", "found": ["Natalya's Soul (claws)"]}}
    REAL_NF = {"reel": "s_1788999999999_9", "frame": "f_1788999999999.jpg",
               "resp": {"ledger": "sets", "lane": "grok", "notFound": ["Griswold's Valor"]}}
    OLD_FOUND = {"reel": "s_1787000000000_2", "frame": "f_1787000000001.jpg",
                 "resp": {"ledger": "sets", "lane": "claude", "found": ["Griswold's Valor"]}}

    def _merged(self):
        sys.path.insert(0, HERE)
        import chronicle_retro as cr
        return cr.merge_proposals(
            cr.proposal_from_pages([self.OLD_NF, self.OLD_FOUND]),
            cr.proposal_from_pages([self.NEW_FOUND, self.REAL_NF]))

    def test_an_expired_not_found_is_not_contested_AFTER_A_MERGE(self):
        m = self._merged()
        con = set((m.get("contested") or {}).get("sets") or ())
        self.assertNotIn("Natalya's Soul (claws)", con,
                         "the newest look FOUND this, so the old not-found has expired. Counting "
                         "it is the padding that made 64 out of 34.")

    def test_the_merge_still_reports_a_REAL_contradiction(self):
        """Seen red for its own reason. A merge that expires everything is as useless as one that
        expires nothing. [[feedback-blind-fixture-green-gate]]"""
        m = self._merged()
        con = set((m.get("contested") or {}).get("sets") or ())
        self.assertIn("Griswold's Valor", con,
                      "the NEWER look says not-found — a real contradiction, not an expired one")

    def test_the_merge_writes_the_fields_that_EXPLAIN_the_number(self):
        """A count he cannot audit is worse than no count. contestedExpired is the field the
        console card renders from; absent, the card cannot exist. [[unknown-stays-unknown]]"""
        m = self._merged()
        self.assertIsNotNone(m.get("contestedResolved"), "contestedResolved dropped by the merge")
        self.assertIsNotNone(m.get("notFoundDatable"), "notFoundDatable dropped by the merge")
        exp = m.get("contestedExpired") or {}
        self.assertIn("Natalya's Soul (claws)", set(exp.get("sets") or ()),
                      "the name that left `contested` must REAPPEAR as expired — it is explained, "
                      "not hidden, or the drop from 64 to 34 looks like data loss")

    def test_BOTH_DERIVATIONS_AGREE_which_is_the_whole_point(self):
        """The copy-drift guard. One source, two callers: whatever proposal_from_pages says about
        a body of evidence, merge_proposals must say about the same body. If these two can ever
        disagree, the fixed copy is not the one his screen reads — which is exactly what happened.
        """
        sys.path.insert(0, HERE)
        import chronicle_retro as cr
        pages = [self.OLD_NF, self.OLD_FOUND, self.NEW_FOUND, self.REAL_NF]
        direct = cr.proposal_from_pages(pages)
        merged = cr.merge_proposals(cr.proposal_from_pages(pages), {})
        for field in ("contested", "contestedExpired"):
            self.assertEqual(
                {k: sorted(v) for k, v in (direct.get(field) or {}).items()},
                {k: sorted(v) for k, v in (merged.get(field) or {}).items()},
                "%s disagrees between the direct build and the merged one — the rule has drifted "
                "into two copies again" % field)

if __name__ == "__main__":
    unittest.main(verbosity=2)
