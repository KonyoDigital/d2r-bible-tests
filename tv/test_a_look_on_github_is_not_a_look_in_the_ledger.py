# -*- coding: utf-8 -*-
"""#180 — a look posted to #231 must become a ledger row, and must not become TWO.

⚠⚠ WHAT THIS COST BEFORE IT EXISTED, measured 2026-09-23: the #231 seat reviewed v3449 at
181,141 chars and named BOTH defects that were later rediscovered by a fresh Grok call and shipped
as v3452 — the verdict arm that still says GATES RED when `red` is false, and the no-spec patience
callers with their "18 of 20" denominator. It sat unread on GitHub. Both halves were built and
never joined. [[the-unjoined-end]]

RED_PROOF cases live in tv/heart2.py's registry; this file is the law.
"""
import io
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import second_eye_drain as D            # noqa: E402
import second_eye_ledger as L           # noqa: E402


_REAL = """SECOND-EYE

version: v3449
sha: 6d1b25f0a1f9096adc59ea99e2f0ca5c15f5c244
verdict: findings
model: grok-4.7
chars: 181141
reach: tv/render_check.py 24944/24944, absent: none
not shown: tests were not executed, no runner was watched, and pixels were not opened.
findings: The per-target row passes spec, but the abort summary and .render_verdict.json call
_declared_page_patience() with no spec, so both still use the registry maximum, 30s.
"""

_NO_VERSION = _REAL.replace("version: v3449", "version: unknown")


class AGitHubLookBecomesALedgerRow(unittest.TestCase):

    def test_a_real_comment_parses_into_every_field_the_gate_needs(self):
        got = D.parse_comment(_REAL)
        self.assertIsNotNone(got, "the shipped #231 format no longer parses — the drain is blind")
        self.assertEqual(got["version"], "v3449")
        self.assertEqual(got["sha"], "6d1b25f0a1f9096adc59ea99e2f0ca5c15f5c244")
        self.assertEqual(got["verdict"], "findings")
        self.assertEqual(got["model"], "grok-4.7")
        self.assertEqual(got["chars"], "181141")
        # ⚠ THE FINDINGS ARE PROSE AND SPAN LINES. A parser that stopped at the first newline
        # would keep the claim and throw away the FAILING SCENARIO, which is the half that makes a
        # finding actionable. That is the exact loss [[heart-first]] §6 is about.
        self.assertIn("registry maximum", got["findings"],
                      "a multi-line findings block was truncated: %r" % (got["findings"],))

    def test_a_comment_that_is_not_a_look_is_not_a_look(self):
        self.assertIsNone(D.parse_comment("just a normal comment about the weather"))
        self.assertIsNone(D.parse_comment(""))
        self.assertIsNone(D.parse_comment(None))

    def test_a_look_naming_no_version_is_REFUSED_not_filed_as_a_version(self):
        """⚠ `version: unknown` is the seat being HONEST about a commit with no stamp.

        norm_version("unknown") is "", and record() falls back to the raw string — so filing it
        would MINT a version called "unknown" that every such look then piles into, and
        agreement("unknown") would report them as several looks at one version.
        """
        got = D.parse_comment(_NO_VERSION)
        self.assertIsNotNone(got, "the comment still parses; it is the FILING that must refuse")
        self.assertEqual(L.norm_version(got["version"]), "",
                         "this test's premise is gone: 'unknown' now normalises to a real version")

        # ⚠⚠ AND IT MUST DRIVE THE DRAIN, NOT JUST THE HELPER. The first cut of this case asserted
        # only what norm_version() returns — so deleting the skip from drain() entirely would have
        # left it GREEN. A test that cannot see the change it is written about is measuring the
        # helper, not the law. [[source-reading-guard]] §4c cause 2 [[a-law-about-a-row-must-drive-the-row]]
        wrote, said = [], []
        real_gh, real_rec = D._handoff._gh, D._led.record
        try:
            D._handoff._gh = lambda *_a, **_k: [{"id": 999000111,
                                                 "created_at": "2026-09-23T00:00:00Z",
                                                 "body": _NO_VERSION}]
            D._led.record = lambda **kw: wrote.append(kw) or {}
            out = D.drain(say=said.append)
        finally:
            D._handoff._gh, D._led.record = real_gh, real_rec
        self.assertEqual(wrote, [],
                         "a look naming NO version was filed anyway — it mints a version called "
                         "'unknown' that every stampless look then piles into, and agreement() "
                         "reads them as several looks at one version")
        self.assertEqual(out.get("noVersion"), 1,
                         "the refusal was not COUNTED, so it reads as 'there were none'")
        self.assertTrue(any("NO version" in t for t in said),
                        "the skip was silent; a silent skip reads as nothing to drain: %r" % (said,))

    def test_the_drain_is_idempotent_because_the_row_names_its_comment(self):
        """A second drain must record NOTHING. The ledger is append-only, so a drainer that could
        double-record would inflate `looks` and turn ONE witness into a false corroboration."""
        # ⚠⚠ v3457 — THIS CASE DID NOT TEST IDEMPOTENCY AND ITS NAME SAID IT DID.
        # Found by the cross-family eye on the SHIPPED v3454 bytes, then REPRODUCED: deleting
        # `if got["_id"] not in seen` from the drain left all 7 cases GREEN. The assertions below
        # read the live ledger (gitignored, so EMPTY on a clean checkout — the first assert would
        # fail there for an unrelated reason) and the mocked half only checked that ONE write
        # carried verdict_from. The skip itself was never exercised.
        # So the skip is now DRIVEN: the same comment is offered TWICE and the second pass must
        # write nothing. [[source-reading-guard]] §4c cause 2 [[a-law-about-a-row-must-drive-the-row]]
        wrote = []
        real_gh, real_rec, real_seen = D._handoff._gh, D._led.record, D.already_recorded
        try:
            D._handoff._gh = lambda *_a, **_k: [{"id": 777001, "created_at": "2026-09-23T00:00:00Z",
                                                 "body": _REAL}]
            D._led.record = lambda **kw: wrote.append(kw) or {}
            D.already_recorded = lambda: set()               # pass 1: nothing filed yet
            D.drain(say=lambda *_a: None)
            self.assertEqual(len(wrote), 1, "the first drain did not file the look at all")
            D.already_recorded = lambda: {"777001"}          # pass 2: it IS filed now
            out2 = D.drain(say=lambda *_a: None)
        finally:
            D._handoff._gh, D._led.record, D.already_recorded = real_gh, real_rec, real_seen
        self.assertEqual(
            len(wrote), 1,
            "the SAME #231 comment was filed twice. The ledger is append-only, so a re-drain then "
            "inflates `looks` and agreement() reads ONE witness as two — a false corroboration, "
            "which is the exact failure #182 was built to end. Wrote %d row(s)." % len(wrote))
        self.assertEqual(out2.get("recorded"), 0,
                         "the second drain reported recording %r rows for an already-filed look"
                         % (out2.get("recorded"),))

        # and the ledger's own history must stay free of duplicates
        ids = [str(r.get("verdictFrom") or "") for r in L._rows()
               if "gh#231 comment" in str(r.get("verdictFrom") or "")]
        self.assertEqual(len(ids), len(set(ids)),
                         "the same #231 comment appears in %d rows, %d distinct"
                         % (len(ids), len(set(ids))))

        # ⚠⚠ AND IT MUST DRIVE A FRESH DRAIN. The assertions above read rows ALREADY WRITTEN, so
        # deleting verdict_from= from the writer leaves them untouched and this case stays GREEN —
        # measured: that exact sabotage passed. History cannot testify about the code path that
        # will write the NEXT row. [[source-reading-guard]] §4c cause 2
        wrote = []
        real_gh, real_rec = D._handoff._gh, D._led.record
        try:
            D._handoff._gh = lambda *_a, **_k: [{"id": 424242, "created_at": "2026-09-23T00:00:00Z",
                                                 "body": _REAL}]
            D._led.record = lambda **kw: wrote.append(kw) or {}
            D.drain(say=lambda *_a: None)
        finally:
            D._handoff._gh, D._led.record = real_gh, real_rec
        self.assertEqual(len(wrote), 1, "the drain filed %d row(s) for one look" % len(wrote))
        self.assertEqual(wrote[0].get("verdict_from"), "gh#231 comment 424242",
                         "a NEWLY drained row does not name the comment it came from, so the next "
                         "drain cannot tell it was already filed and will duplicate every look: %r"
                         % (wrote[0].get("verdict_from"),))

    def test_the_drained_rows_resolve_to_a_family_rather_than_free_text(self):
        """[[heart-first]] §1 — corroboration needs two DIFFERENT engines, so the family must be
        derivable. The drain passes `model` verbatim and lets the ledger decide."""
        self.assertEqual(L.family_of("grok-4.7"), "xai")
        drained = [r for r in L._rows() if "gh#231 comment" in str(r.get("verdictFrom") or "")]
        if drained:
            unknown = [r for r in drained if not r.get("family")]
            self.assertEqual(
                unknown, [],
                "%d drained row(s) carry no family, so agreement() cannot tell a cross-family "
                "corroboration from the same eye asked twice (#182)" % len(unknown))

    def test_an_unreachable_github_is_UNKNOWN_and_never_an_empty_lane(self):
        """[[feedback-silence-is-not-evidence]] — a dead reader must not read like a quiet issue."""
        said = []
        real = D._handoff._gh
        try:
            def _boom(*_a, **_k):
                raise RuntimeError("network is down")
            D._handoff._gh = _boom
            out = D.drain(say=said.append)
        finally:
            D._handoff._gh = real
        self.assertFalse(out.get("ok"), "an unreachable GitHub reported a successful drain")
        self.assertIsNone(out.get("looks"),
                          "an unreachable lane reported a COUNT of looks — that is a measured "
                          "zero standing in for a failure to look")
        self.assertEqual(out.get("recorded"), 0)
        self.assertTrue(any("UNKNOWN" in s for s in said),
                        "the failure was not said out loud: %r" % (said,))

    def test_the_drain_never_moves_the_handoff_watermark(self):
        """One owner per watermark. If this marked #231 read, a HUMAN drain of the same issue
        would silently skip every comment this one consumed."""
        import inspect
        src = inspect.getsource(D)
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        self.assertNotIn(".mark(", code,
                         "the drain moves handoff's watermark; a human drain of #231 will then "
                         "skip whatever this consumed")


class ADrainedLookKeepsItsReach(unittest.TestCase):
    """v3464 — the cross-family eye on the SHIPPED v3457 bytes named four holes on this path, and
    every one of them survived this file: "deleting the reach parser leaves the suite green".
    These cases DRIVE the drain and the ledger's reader; none of them reads source text.
    [[a-law-about-a-row-must-drive-the-row]]"""

    def _drain_one(self, reach_line):
        wrote = []
        body = _REAL.replace("reach: tv/render_check.py 24944/24944, absent: none",
                             "reach: " + reach_line)
        real_gh, real_rec, real_seen = D._handoff._gh, D._led.record, D.already_recorded
        try:
            D._handoff._gh = lambda *_a, **_k: [{"id": 990001, "created_at": "2026-09-24T00:00:00Z",
                                                 "body": body}]
            D._led.record = lambda **kw: wrote.append(kw) or {}
            D.already_recorded = lambda: set()
            D.drain(say=lambda *_a: None)
        finally:
            D._handoff._gh, D._led.record, D.already_recorded = real_gh, real_rec, real_seen
        self.assertEqual(len(wrote), 1, "the drain did not file the look")
        return wrote[0]

    def test_a_partial_file_reaches_the_ledger_as_got_and_total(self):
        kw = self._drain_one("tv/x.py 810/23523, tv/y.py 40/40, absent: none")
        reach = kw.get("reach") or {}
        self.assertEqual(reach.get("tv/x.py"), {"got": 810, "total": 23523},
                         "the seat said it held 810 of 23,523 bytes of tv/x.py and the row does not "
                         "carry that as a size agreement() can read: %r" % (reach,))
        self.assertEqual(reach.get("tv/y.py"), {"got": 40, "total": 40})

    def test_every_file_after_absent_stays_absent(self):
        kw = self._drain_one("tv/a.py 5/5, absent: tv/b.py, tv/c.py")
        self.assertEqual(kw.get("absent"), ["tv/b.py", "tv/c.py"],
                         "the seat named two files it never saw and the row kept %r"
                         % (kw.get("absent"),))
        self.assertNotIn("tv/c.py", kw.get("reach") or {},
                         "a file the seat said was ABSENT was filed as one it read")

    def test_absent_none_is_measured_and_silence_is_unknown(self):
        self.assertEqual(self._drain_one("tv/a.py 5/5, absent: none").get("absent"), [],
                         "`absent: none` is a measurement — the seat looked and nothing was missing")
        self.assertIsNone(self._drain_one("tv/a.py 5/5").get("absent"),
                          "a reach line that never mentions absent is UNKNOWN, not 'nothing missing'")

    def test_a_drained_partial_look_is_seen_by_agreement(self):
        import tempfile
        d = tempfile.mkdtemp(prefix="se-reach-")
        try:
            led = os.path.join(d, "ledger.jsonl")
            reach, absent = L.reach_from_line("tv/x.py 810/23523, absent: none")
            L.record(version="v9901", model="grok-4.7", verdict="clean", findings=[],
                     sha=None, reached=True, reach=reach, absent=absent, path=led)
            got = L.agreement("v9901", path=led)
        finally:
            import shutil
            shutil.rmtree(d, ignore_errors=True)
        self.assertEqual(got.get("cut"), 1,
                         "a look that held 3.4%% of the file it reviewed was not counted as cut: %r"
                         % (got,))

    def test_a_row_drained_before_the_parser_is_still_read_for_cuts(self):
        """The ledger is append-only and the drain is idempotent, so a writer-only fix would leave
        the 41 existing rows — v3449's 3.4% look among them — invisible forever."""
        import tempfile
        d = tempfile.mkdtemp(prefix="se-legacy-")
        try:
            led = os.path.join(d, "ledger.jsonl")
            L.record(version="v9902", model="grok-4.7", verdict="clean", findings=[], sha=None,
                     reached=True, reach={"line": "tv/x.py 810/23523, absent: none"}, path=led)
            got = L.agreement("v9902", path=led)
        finally:
            import shutil
            shutil.rmtree(d, ignore_errors=True)
        self.assertEqual(got.get("cut"), 1, "a legacy drained row's cut stayed invisible: %r" % (got,))
        self.assertEqual(got.get("reachUnknown"), 0,
                         "its own line says `absent: none` and the row still reads reach-UNKNOWN")

    def test_refused_looks_are_not_called_a_measured_zero(self):
        said = []
        real_gh, real_seen = D._handoff._gh, D.already_recorded
        try:
            D._handoff._gh = lambda *_a, **_k: [{"id": 990002, "created_at": "2026-09-24T00:00:00Z",
                                                 "body": _NO_VERSION}]
            D.already_recorded = lambda: set()
            D.drain(say=said.append)
        finally:
            D._handoff._gh, D.already_recorded = real_gh, real_seen
        self.assertFalse(any("measured zero —" in s for s in said),
                         "a REFUSED look was reported as 'already filed, a measured zero': %r"
                         % (said,))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "v3464 — back to storing the LINE only: per-file sizes invisible to agreement()",
        "file": "tv/second_eye_drain.py",
        "find": "        reach, absent = _led.reach_from_line(_reach_line)\n",
        "replace": "        reach, absent = ({\"line\": _reach_line} if _reach_line else None), None\n",
        "matches": 1,
    },
    {
        "why": "v3464 — drop absent= from the record call: blind_to() None on every drained look",
        "file": "tv/second_eye_drain.py",
        "find": "            absent=absent,\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "v3464 — the comma split: every file after the first in `absent: a, b` filed as read",
        "file": "tv/second_eye_ledger.py",
        "find": "[p.strip() for p in re.split(r\"[,\\n]\", tail) if p.strip()])",
        "replace": "[tail.split(\",\")[0].strip()])",
        "matches": 1,
    },
    {
        "why": "v3464 — legacy rows not structured: v3449's 3.4% look stays filed as agreement",
        "file": "tv/second_eye_ledger.py",
        "find": "        if _rc.get(\"line\") and not any(isinstance(v, dict) for v in _rc.values()):\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        "why": "v3464 — a refused look called 'already filed, a measured zero'",
        "file": "tv/second_eye_drain.py",
        "find": "        if looks and _filed == len(looks):\n",
        "replace": "        if True:\n",
        "matches": 1,
    },
]
