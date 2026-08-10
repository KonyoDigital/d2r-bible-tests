#!/usr/bin/env python3
# 🛑 v1689 — THE CHRONICLE ROUTE GUARD (tv/control_app.py).
#
# THE DEFECT THIS PINS. _kai_frame_cls() (control_app.py ~4232) has NO 'chronicle' class: its
# whole vocabulary is stash-runes|stash-gems|stash-materials|stash|inventory|tooltip|gameplay.
# An in-game Chronicle page is a LIST OF ITEM NAMES → 'itemish' → 'tooltip'. The Claude vision
# lane, on the SAME footage, called those frames scene='chronicle' (session
# s_1786385768689_67392: 8 deep rows, chronicleTab='uniques', conf 0.60→0.95). Nothing
# reconciled the two, so a kai-vault intake FIRED on the Chronicle frame
# reel_s_1786385768689_67392/f_1786385778600 and errored ok:false total:0.
#
# THE FIXTURE IS HIS JOURNAL, NOT A RECONSTRUCTION. DEEP_REAL below is EVERY deep read of that
# session that carries a scene — all 9 of them, captureTs / scene / stashTab / chronicleTab
# copied verbatim out of tv/sessions.jsonl. Nothing is moved, dropped or invented.
# ⚠ THE ROW THAT DECIDES THE OUTCOME IS THE GAMEPLAY ONE. This suite's first shape placed it
# 60 s away, outside the window, and so it "proved" a guard that did not actually catch the one
# incident it was built for. Reality: gameplay at −791 ms, the first chronicle read at +4089 ms.
# NEAREST-READ-WINS therefore hands the frame to the vault reader. A chronicle is READ BY
# SCROLLING, so the frames between vision reads read as 'gameplay' — an ABSENCE of a claim, not
# a rebuttal. Hence the rule this file pins: any chronicle read in the ±12 s window refuses,
# unless a strictly NEARER read positively NAMES A STASH TAB. (±4 s, the tooltip-association
# window used elsewhere in the file, would also miss the incident — by 89 ms.)
#
# NOTHING HERE TOUCHES LIVE DATA: every check patches _journal_path() to a temp file and passes
# its own `rows` fixture. His journal, his foundLog and his running console are never read or
# written by this suite.
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# Never point the module globals at the LIVE console (test_control.py's v1462 courtesy —
# control_app reads these at import time and 17772 is Konyo's running app).
os.environ["TV_CONTROL_PORT"] = "17972"
os.environ["TV_PORT"] = "17971"
import control_app as ca  # noqa: E402

SID = "s_1786385768689_67392"
# EVERY scened deep read of that session, verbatim: (captureTs, scene, stashTab, chronicleTab).
DEEP_REAL = [
    (1786385777809, "gameplay", "", ""),
    (1786385782689, "chronicle", "", "uniques"),
    (1786385790213, "chronicle", "", "uniques"),
    (1786385797924, "chronicle", "", "uniques"),
    (1786385807604, "chronicle", "", "uniques"),
    (1786385814341, "chronicle", "", "uniques"),
    (1786385822222, "chronicle", "", "uniques"),
    (1786385826830, "chronicle", "", "uniques"),
    (1786385852302, "chronicle", "", "uniques"),
]
# The 8 real chronicle reads of that session (captureTs, ms) — gaps 4.6s … 25.5s.
CHRON_TS = [t for (t, sc, _st, _ct) in DEEP_REAL if sc == "chronicle"]
GAMEPLAY_TS = 1786385777809        # the read that is NEAREST to the offending frame (−791 ms)
VAULT_FRAME_TS = 1786385778600     # the frame the kai-vault intake actually fired on
VAULT_FID = "reel_" + SID + "/f_" + str(VAULT_FRAME_TS)


def _chron_row(ts, tab="uniques"):
    return {"lane": "deep", "scene": "chronicle", "sessionId": SID, "captureTs": ts, "ts": ts,
            "stashTab": "", "raw": json.dumps({"scene": "chronicle", "chronicleTab": tab,
                                               "names": ["Andariel's Visage"]})}


def _stash_row(ts, tab="runes"):
    return {"lane": "deep", "scene": "stash", "sessionId": SID, "captureTs": ts, "ts": ts,
            "stashTab": tab, "raw": json.dumps({"scene": "stash", "stashTab": tab})}


def _rows_real():
    """His session exactly as tv/sessions.jsonl holds it — including the gameplay read 791 ms
    from the offending frame, the row that decides this whole case."""
    rows = []
    for ts, sc, stab, ctab in DEEP_REAL:
        if sc == "chronicle":
            rows.append(_chron_row(ts, ctab))
        else:
            rows.append({"lane": "deep", "scene": sc, "sessionId": SID, "captureTs": ts,
                         "ts": ts, "stashTab": stab, "raw": json.dumps({"scene": sc})})
    return rows


class RouteGuardBase(unittest.TestCase):
    def setUp(self):
        fd, self.jpath = tempfile.mkstemp(prefix="rg_journal_", suffix=".jsonl")
        os.close(fd)
        self._p = mock.patch.object(ca, "_journal_path", lambda: self.jpath)
        self._p.start()
        ca.__dict__["_DRV_CHRON_REFUSED"] = 0

    def tearDown(self):
        self._p.stop()
        try:
            os.remove(self.jpath)
        except OSError:
            pass

    def _journal(self):
        out = []
        with open(self.jpath, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    out.append(json.loads(ln))
        return out

    def _counter(self):
        return int(ca.__dict__.get("_DRV_CHRON_REFUSED") or 0)


class TestRefusal(RouteGuardBase):
    def test_vault_intake_on_his_real_chronicle_frame_is_refused(self):
        """THE MEASURED INCIDENT. reel_s_1786385768689_67392/f_1786385778600 → kai-vault."""
        before = self._counter()
        why = ca._kai_route_guard_refuse("kai-vault", VAULT_FID, VAULT_FRAME_TS, SID,
                                         "personal", rows=_rows_real())
        # 1. REFUSED — and not merely falsy/None: a NAMED reason.
        self.assertTrue(why, "the vault intake was NOT refused on a chronicle frame")
        self.assertIsInstance(why, str)
        self.assertIn("chronicle", why.lower(), "the reason must NAME chronicle: " + repr(why))
        self.assertIn("uniques", why, "the reason must carry the read's own chronicleTab")
        self.assertIn("kai-vault", why, "the reason must name the intake it refused")
        # 2. COUNTED — by exactly one.
        self.assertEqual(self._counter(), before + 1, "refusal counter must move by exactly 1")
        # 3. SAID WHY, on the channel the real intake results use.
        rows = self._journal()
        self.assertEqual(len(rows), 1, "exactly one refusal receipt must be journalled")
        rec = rows[0]
        self.assertEqual(rec.get("lane"), "intake")
        self.assertEqual(rec.get("frameId"), VAULT_FID)
        self.assertEqual(rec.get("sessionId"), SID)
        ik = rec.get("intake") or {}
        self.assertEqual(ik.get("kind"), "kai-vault")
        self.assertIs(ik.get("ok"), False)
        self.assertIs(ik.get("refused"), True)
        self.assertTrue(ik.get("err"), "the receipt must carry the reason, not a bare ok:false")
        self.assertIn("chronicle", str(ik.get("err")).lower())
        # captureTs = the FRAME's ms (retro joins on captureTs, never on receipt time)
        self.assertEqual(rec.get("captureTs"), VAULT_FRAME_TS)

    def test_the_nearest_read_is_gameplay_and_the_guard_refuses_anyway(self):
        """THE REGRESSION PIN. The two facts that killed this guard's first shape, asserted
        together: (1) the NEAREST read to the offending frame is 'gameplay' at 791 ms, (2) the
        chronicle read is 4089 ms away — 5.2x further. Nearest-read-wins therefore ROUTES the
        vault reader onto a Chronicle page, which is the measured bug. The guard must refuse
        regardless: 'gameplay' is an absence of a claim, not a rebuttal."""
        rows = _rows_real()
        self.assertEqual(VAULT_FRAME_TS - GAMEPLAY_TS, 791)
        self.assertEqual(CHRON_TS[0] - VAULT_FRAME_TS, 4089)
        near = ca._kai_deep_scene_near(VAULT_FRAME_TS, SID, rows)
        self.assertIsNotNone(near, "no read found near the frame — the join is broken")
        self.assertEqual(near["scene"], "gameplay", "fixture drifted from his real journal")
        self.assertEqual(near["deltaMs"], 791)
        chron, stash = ca._kai_chron_claim_near(VAULT_FRAME_TS, SID, rows)
        self.assertIsNotNone(chron, "the chronicle read in the window must still be seen")
        self.assertEqual(chron["deltaMs"], 4089)
        self.assertEqual(chron["chronicleTab"], "uniques")
        self.assertIsNone(stash, "no read in that window names a stash tab — nothing rebuts")
        self.assertTrue(ca._kai_route_guard_reason("kai-vault", VAULT_FRAME_TS, SID, rows),
                        "the guard let the measured incident through: a nearer 'gameplay' read "
                        "must NOT rebut a chronicle read")

    def test_a_nearer_gameplay_read_does_not_rebut(self):
        """Generalised: scrolling a Chronicle leaves gameplay frames between reads, at ANY gap."""
        for gap in (100, 791, 3000):
            with self.subTest(gap=gap):
                t = 1786386100000
                rows = [_chron_row(t + 5000),
                        {"lane": "deep", "scene": "gameplay", "sessionId": SID,
                         "captureTs": t - gap, "ts": t - gap, "stashTab": "", "raw": "{}"}]
                self.assertTrue(ca._kai_route_guard_reason("kai-vault", t, SID, rows),
                                "gameplay %d ms away wrongly rebutted the chronicle read" % gap)

    def test_tally_and_vault_count_are_guarded_too(self):
        """Same class, all three stash/vault/tally kinds — not just the one that bit."""
        for kind in ("vault", "vault-count", "gridcount", "tally", "kai-funnel"):
            with self.subTest(kind=kind):
                before = self._counter()
                why = ca._kai_route_guard_refuse(kind, VAULT_FID, VAULT_FRAME_TS, SID,
                                                 "runes", rows=_rows_real())
                self.assertTrue(why, kind + " was not refused on a chronicle frame")
                self.assertEqual(self._counter(), before + 1)


class TestNegativeControl(RouteGuardBase):
    """A routing guard must not become a blanket block."""

    def test_non_chronicle_frame_still_routes(self):
        rows = [_stash_row(1786385900000)]
        why = ca._kai_route_guard_refuse("tally", "reel_" + SID + "/f_1786385900100",
                                         1786385900100, SID, "runes", rows=rows)
        self.assertEqual(why, "", "a stash frame must still route into the tally intake")
        self.assertEqual(self._counter(), 0)
        self.assertEqual(os.path.getsize(self.jpath), 0, "no receipt for a frame that was allowed")

    def test_far_from_any_chronicle_read_routes(self):
        """60 s after the last chronicle read: he closed it and went farming."""
        why = ca._kai_route_guard_refuse("vault", "reel_" + SID + "/f_" + str(CHRON_TS[-1] + 60_000),
                                         CHRON_TS[-1] + 60_000, SID, "personal", rows=_rows_real())
        self.assertEqual(why, "")
        self.assertEqual(self._counter(), 0)

    def test_a_nearer_stash_read_rebuts(self):
        """He shut the Chronicle and opened the stash. Only a POSITIVE stash claim rebuts, and
        only when it is strictly nearer: chronicle at T, stash 1s later, frame 1.2s after T."""
        t = 1786386000000
        rows = [_chron_row(t), _stash_row(t + 1000)]
        why = ca._kai_route_guard_refuse("tally", "reel_" + SID + "/f_" + str(t + 1200),
                                         t + 1200, SID, "runes", rows=rows)
        self.assertEqual(why, "", "the nearer stash read must win — this is not a blanket block")
        self.assertEqual(self._counter(), 0)

    def test_the_live_drivers_own_queueing_read_rebuts_by_construction(self):
        """Why the live engine-driver hunk is not a blanket block: a driver job is only queued
        FROM a deep read that reported a stash tab, so that read sits at delta ≈ 0 and is always
        nearer than any chronicle read. Even mid-Chronicle, a real stash shot still routes."""
        rows = _rows_real() + [_stash_row(CHRON_TS[2] + 200, "runes")]
        why = ca._kai_route_guard_refuse("tally", "reel_" + SID + "/f_" + str(CHRON_TS[2] + 250),
                                         CHRON_TS[2] + 250, SID, "runes", rows=rows)
        self.assertEqual(why, "", "a stash read 50 ms away must still win over a chronicle read")
        self.assertEqual(self._counter(), 0)

    def test_other_sessions_chronicle_does_not_refuse(self):
        rows = [dict(_chron_row(VAULT_FRAME_TS), sessionId="s_other_1")]
        why = ca._kai_route_guard_refuse("kai-vault", VAULT_FID, VAULT_FRAME_TS, SID,
                                         "personal", rows=rows)
        self.assertEqual(why, "")

    def test_chronicles_own_lane_is_untouched(self):
        """Only stash/vault/tally intakes are guarded — grail/chronicle/board writes are NOT."""
        for kind in ("chronicle", "grail", "board", "judge", ""):
            with self.subTest(kind=kind):
                self.assertEqual(
                    ca._kai_route_guard_reason(kind, VAULT_FRAME_TS, SID, _rows_real()), "",
                    "kind %r must not be guarded — the Chronicle's own lane still gets the frame"
                    % kind)


class TestEveryFireSiteIsGuarded(unittest.TestCase):
    """SWEEP THE CLASS. Three stash/vault/tally fire sites exist in control_app.py — the live
    engine-driver loop, the Stage-3 post-seal vault fire, and the Stage-3 KAI funnel. All three
    must pass through the guard, or the bug ships twice more."""

    def setUp(self):
        with open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as f:
            self.src = f.read()

    def test_three_fire_sites_call_the_guard(self):
        n = self.src.count("_kai_route_guard_refuse(")
        # 1 definition + 3 call sites
        self.assertGreaterEqual(n, 4, "expected the guard defined once and called at all THREE "
                                      "stash/vault/tally fire sites; found %d mentions" % n)
        for marker in ('_kai_route_guard_refuse(_gk,',                 # live engine-driver
                       '_kai_route_guard_refuse("kai-vault", _fidv,',  # Stage-3 vault
                       '_kai_route_guard_refuse("kai-funnel", _fid3'): # Stage-3 funnel
            self.assertTrue(marker in self.src, "fire site missing its guard: " + marker)

    def test_counter_is_exposed_on_both_status_surfaces(self):
        """MAKE THE SURFACES AGREE — the cached driver block and /api/status both report it."""
        self.assertTrue('"chronRefused": globals().get("_DRV_CHRON_REFUSED", 0)' in self.src,
                        "the cached driver block must report the refusal count")
        self.assertTrue('"chronRefused": _drv.get("chronRefused"' in self.src,
                        "/api/status's driver block must report the SAME count")

    def test_kai_frame_cls_vocabulary_untouched(self):
        """OUT OF SCOPE this ship: adding a 'chronicle' class to the OCR classifier."""
        i = self.src.index("def _kai_frame_cls(")
        body = self.src[i:i + 3000]
        self.assertNotIn('return "chronicle"', body,
                         "_kai_frame_cls's vocabulary must not change in v1689")


if __name__ == "__main__":
    unittest.main(verbosity=1)
