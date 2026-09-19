# -*- coding: utf-8 -*-
"""v3363 (#114) — A FILE CAN ARRIVE AND STILL BE UNREAD.

`absent_from` asks whether a changed file reached the payload AT ALL, and it answers by looking
for that file's `diff --git` header. Truncation cuts MID-FILE. So a file whose header arrived and
whose body was chopped is `absent`-clean, `blind_to`-clean, and unread — and every reach check
built before this version says it was seen.

MEASURED 2026-09-19 by rebuilding the payload per commit over 16 versions. 67 files ARRIVED; 8 of
them arrived under half their bytes:

    v3356  bible.html                                        259 /  8,629    3.0%
    v3349  test_a_partial_look_is_not_agreement.py           428 / 11,337    3.8%
    v3350  test_the_shelf_tabs_are_the_real_sessions.py      196 /  3,406    5.8%
    v3358  test_the_shelf_shows_reels_before_analysis.py   1,224 / 12,586    9.7%
    v3348  visual_lock_invariant.py                           64 /    516   12.4%
    v3352  test_the_shelf_tabs_are_the_real_sessions.py    1,464 /  5,915   24.8%
    v3347  prune_wilson.py                                 8,318 / 27,748   30.0%
    v3354  second_eye_ledger.py                            3,499 /  7,200   48.6%

⚠⚠ AND THE FIRST CUT OF THIS COUNTER WAS 71% NOISE — caught by pointing it at his real history
rather than at the fixture. It flagged 41 of 100 files, 33 of them at exactly 0.0%: files that did
not arrive SHORT, they did not arrive at all, and every one was already named in the row's
`absent` list. That is the v3354 defect — a warning that fires on most rows is furniture — which I
had fixed two versions earlier and re-created here. A fixture built to show a half-cut file
contains no wholly-cut file, so it could never have caught it. [[regression-guard]] §5

⚠⚠ v3354 IS THE ROW THAT SETTLES IT, because it is self-incriminating. `second_eye_ledger.py` is
the file v3354 exists to change — the version whose whole subject was teaching this ledger to tell
a stamp from a blind spot. Its header arrived, so the row was filed `absent: [...]` without it,
`blind_to: []`, `verdict: clean`. The eye held under half of its own subject and nothing in the
system could say so.

v3361 repeated it in the loudest possible way: the eye's answer OPENED with *"REACH: 19/92
hunks"*, naming the pre-push hook and the scoped walk — the entire version — as unjudgeable, and
the row still read `clean` with `blind_to: []`.

=== WHY THE FRACTION AND NOT A FLAG ===
The obvious store is `truncatedFiles: ["a.py"]`, computed against a baked bar like 50%. That bar
would be a number nobody measured and nobody can move — the same shape as the $5 he corrected me
on ("it can be 1-2$ too it depends") and as the 0.22 threshold that sat above a signal maxing at
0.133, where the branch simply never ran. `got`/`total` per file is the measurement; the bar is a
reader's decision and can be tuned once there are rows to tune it against.
[[feedback-threshold-above-the-ceiling]] [[heart-first]] §6 — persist what you KNEW.

⚠ AND IT IS MEASURED AGAINST THE PRE-TRUNCATION BODY, not the raw `git show`. The comment strip
and the ship-note strip are deliberate, declared, and exist to BUY the eye more reach; charging
them here would report the fix for this problem as the problem.

⚠ `absent` AND `reach` ARE DIFFERENT QUESTIONS AND BOTH ARE KEPT. A file that never arrived is
not a file that arrived short, the remedies differ (ask for it vs raise the cap), and collapsing
them would lose the distinction #97 and #104 were built to create.
"""
import inspect
import re
import io
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import second_eye_ledger as L  # noqa: E402
import second_eye_run as R  # noqa: E402


def _defs(src):
    """-> every top-level function name in `src`, in file order."""
    return re.findall(r"(?m)^def (\w+)\(", src)


def _fn_src(src, name):
    """-> one function's own text, bounded by the NEXT top-level def rather than a byte count.

    ⚠ A fixed window here would read whichever neighbour happened to follow, which is how four
    guards in one session graded the wrong block. [[source-reading-guard]] §3
    """
    i = src.find("def %s(" % name)
    if i < 0:
        return ""
    j = src.find("\ndef ", i + 5)
    return src[i:j if j > i else len(src)]


def _tmp():
    return os.path.join(tempfile.mkdtemp(), "ledger.jsonl")


def _diff(*pairs):
    """Build a diff whose per-file byte sizes are known exactly."""
    out = []
    for path, body in pairs:
        out.append("diff --git a/%s b/%s\n--- a/%s\n+++ b/%s\n%s" % (path, path, path, path, body))
    return "".join(out)


class TheWalkIsShared(unittest.TestCase):
    """[[copy-drift]] — one boundary rule, two readers."""

    def test_one_definition_of_where_a_file_section_starts(self):
        """⚠⚠ THIS CASE WAS BLIND ON ITS FIRST PROOF AND THE MATCH COUNT SAID SO.

        It counted the literal string `re.finditer(r"(?m)^diff --git a/(\\S+)"` — the DOUBLE-quoted
        spelling. The sabotage re-inlined the walk with SINGLE quotes, the count stayed 1, and the
        law passed through its own defeat. A guard that can be dodged by a quote character is
        measuring punctuation, not structure. [[source-reading-guard]] §2

        So the law is now structural and quote-agnostic: exactly ONE function in this module may
        contain a `diff --git` scan, and it must be `_file_sections`. Any other function growing
        its own copy is the copy-drift this share exists to prevent, however it is spelled.
        """
        src = io.open(os.path.join(HERE, "second_eye_run.py"), encoding="utf-8").read()
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        scan = re.compile(r"re\.finditer\(\s*r?[\"']\(\?m\)\^diff --git")
        owners = sorted(f for f in _defs(code) if scan.search(_fn_src(code, f)))
        self.assertEqual(
            owners, ["_file_sections"],
            "the diff-header scan lives in %r. Exactly one function may own this boundary rule, "
            "and it must be _file_sections — the rule is subtle (a section ends at the NEXT "
            "header's LINE START, and the last runs to EOF) and two copies disagree the day one "
            "is edited. [[copy-drift]]" % (owners,))
        for reader in ("_strip_ship_notes", "reach_of"):
            self.assertIn(
                "_file_sections(", _fn_src(code, reader),
                "%s no longer calls the shared walk, so it is carrying its own boundary rule "
                "again" % reader)

    def test_stripping_ship_notes_still_works_after_the_refactor(self):
        """⚠ THE BASELINE. Sharing the walk must not change what the strip does."""
        d = _diff(("tv/run_gates.py", '+    Gate("a", [], 90, why="a note"),\n'),
                  ("tv/other.py", '+    send(why="a live message string")\n'))
        out = R._strip_ship_notes(d)
        self.assertIn("<ship note stripped for the eye>", out,
                      "the run_gates.py ship note is no longer stripped")
        self.assertIn('why="a live message string"', out,
                      "the strip reached OUTSIDE run_gates.py and ate a live message string — "
                      "that is v3360's shipped defect, re-created by sharing the walk")


class ReachIsMeasuredPerFile(unittest.TestCase):

    def test_a_file_cut_in_half_is_reported_as_half(self):
        """⚠⚠ THE CASE. Header present, body chopped — clean under every earlier check."""
        full = _diff(("tv/a.py", "+" + "x" * 400 + "\n"), ("tv/subject.py", "+" + "y" * 600 + "\n"))
        cut = full[: full.find("y" * 600) + 100]
        got = R.reach_of(full, cut)
        self.assertIsInstance(got, dict, "reach_of did not measure at all")
        self.assertIn("tv/subject.py", got,
                      "the file whose body was cut is not in the reach map, so a reader cannot "
                      "ask about the one file that matters")
        s = got["tv/subject.py"]
        self.assertLess(
            s["got"], s["total"],
            "a file cut mid-body reports got == total (%r). Its `diff --git` header arrived, which "
            "is exactly why every check built before this one calls it seen." % s)
        self.assertEqual(got["tv/a.py"]["got"], got["tv/a.py"]["total"],
                         "a file that arrived WHOLE is being reported as cut — the baseline, "
                         "without which this law would fire on everything and mean nothing")

    def test_a_file_that_NEVER_ARRIVED_is_not_a_reach_fact(self):
        """⚠⚠ THE ONE THAT KILLED THE FIRST CUT, and only real data could raise it.

        A file cut away entirely has got == 0. That is not "arrived short" — it is `absent`, and
        the row already names it. Counting it here flagged 41 of 100 files over 16 versions with
        33 sitting at exactly 0.0%, which is a warning that fires on most rows: furniture, and the
        same defect v3354 exists to have fixed. The two questions have different remedies (ask for
        the file vs raise the cap), so they stay apart. [[regression-guard]] §5
        """
        full = _diff(("tv/here.py", "+" + "x" * 300 + "\n"),
                     ("tv/gone.py", "+" + "z" * 800 + "\n"))
        final = full[: full.find("diff --git a/tv/gone.py")]
        got = R.reach_of(full, final)
        self.assertIn("tv/here.py", got, "the file that DID arrive is missing from the map")
        self.assertNotIn(
            "tv/gone.py", got,
            "a file with ZERO bytes in the payload is being reported as a reach fact. It did not "
            "arrive short, it did not arrive — `absent_from` names it, and double-counting it "
            "here is what made the first cut of this counter 71%% noise.")

    def test_measured_and_none_arrived_is_not_the_same_as_unmeasurable(self):
        """{} = measured, nothing arrived (and `absent` carries them). None = nobody could ask."""
        full = _diff(("tv/gone.py", "+" + "z" * 400 + "\n"))
        self.assertEqual(
            R.reach_of(full, ""), {},
            "a payload where nothing arrived must MEASURE to an empty map, not collapse to None")
        self.assertIsNone(R.reach_of(None, None))

    def test_it_stores_the_fraction_not_a_verdict(self):
        """⛔ NO BAKED BAR. Store got/total; the reader decides."""
        full = _diff(("tv/a.py", "+" + "x" * 900 + "\n"))
        got = R.reach_of(full, full[:200])
        v = got["tv/a.py"]
        self.assertIsInstance(v, dict,
                              "reach is stored as %r, not a measurement. A boolean against a "
                              "constant nobody measured is the shape of the $5 bar and of the "
                              "0.22 threshold above a 0.133 signal." % type(v).__name__)
        self.assertIn("got", v)
        self.assertIn("total", v)
        for k in ("got", "total"):
            self.assertIsInstance(v[k], int, "%s is not a number" % k)
        self.assertGreater(v["total"], 0, "a zero denominator makes every fraction meaningless")

    def test_an_unestablished_body_is_None_never_an_empty_map(self):
        """[[unknown-stays-unknown]] — {} would read as 'measured, nothing cut'."""
        self.assertIsNone(R.reach_of(None, "x"), "a missing full body returned a measurement")
        self.assertIsNone(R.reach_of("x", None), "a missing final body returned a measurement")
        self.assertIsNone(R.reach_of("no diff headers here at all", "same"),
                          "a body with no file headers returned a measurement rather than "
                          "UNKNOWN — there is nothing to measure against")


class TheRowCarriesIt(unittest.TestCase):

    def test_record_accepts_and_stores_reach(self):
        self.assertIn("reach", inspect.signature(L.record).parameters,
                      "the ledger has no slot for per-file reach, so it dies with the payload")
        p = _tmp()
        L.record(version="v9101", model="m", verdict="clean", answer_head="x", path=p,
                 reach={"tv/a.py": {"got": 10, "total": 100}})
        row = L._rows(p)[-1]
        self.assertIsInstance(row.get("reach"), dict,
                              "reach is stored as %r — a per-FILE fact needs a per-file container"
                              % type(row.get("reach")).__name__)
        self.assertEqual(row["reach"]["tv/a.py"]["total"], 100)

    def test_a_row_with_no_reach_is_UNKNOWN_not_complete(self):
        """Every row before v3363 has none. Calling them complete assumes the thing this version
        exists because nobody knew."""
        p = _tmp()
        L.record(version="v9102", model="m", verdict="clean", answer_head="x", path=p)
        self.assertIsNone(L._rows(p)[-1].get("reach"),
                          "a look whose per-file reach was never measured is being stored as "
                          "something other than UNKNOWN")

    def test_the_join_is_made_at_the_recording_call(self):
        """[[the-unjoined-end]] — computed, used, and dropped before the row is this repo's most
        repeated defect, and #104 is the same wire one field along."""
        src = io.open(os.path.join(HERE, "second_eye_run.py"), encoding="utf-8").read()
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        self.assertIn(
            "sha=sha, absent=absent, reach=reach)", code,
            "the LOOKED path records without the reach map. Computing it and dropping it before "
            "the row is precisely what v3341 did with the absent list for 8 versions.")
        self.assertIn("reach", inspect.signature(R.record_answer).parameters,
                      "record_answer cannot accept the map, so it cannot forward it")


class HisRealLedgerIsNotBackFilled(unittest.TestCase):

    def test_old_rows_do_not_sprout_a_measurement(self):
        if not os.path.exists(L.LEDGER_PATH):
            self.skipTest("no ledger on this machine")
        rows = L._rows()
        if len(rows) < 50:
            self.skipTest("only %d rows here; too few to say anything" % len(rows))
        with_field = [r for r in rows if r.get("reach") is not None]
        self.assertLess(
            len(with_field), len(rows),
            "every row already carries `reach`, which cannot be true of rows written before this "
            "version — if it is, the field is being back-filled with a guess rather than measured.")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "dropping the map at the record call puts the row back to knowing nothing about "
               "how much of each arrived file the eye actually got",
        "file": "tv/second_eye_run.py",
        "find": "               sha=sha, absent=absent, reach=reach)",
        "replace": "               sha=sha, absent=absent)",
        "matches": 1,
    },
    {
        "why": "storing a bool instead of got/total bakes in a bar nobody measured and cannot tune",
        "file": "tv/second_eye_ledger.py",
        "find": '        "reach": (dict(reach) if isinstance(reach, dict) else None),',
        "replace": '        "reach": (bool(reach) if reach is not None else None),',
        "matches": 1,
    },
    {
        "why": "returning an empty map for an unmeasurable body makes UNKNOWN read as nothing-cut",
        "file": "tv/second_eye_run.py",
        "find": "    if not full:\n        return None",
        "replace": "    if not full:\n        return {}",
        "matches": 1,
    },
    {
        "why": "re-inlining the header walk restores the two-copy boundary rule the share removed",
        "file": "tv/second_eye_run.py",
        "find": "    for path, a, b in _file_sections(d):",
        "replace": "    for path, a, b in [(m.group(1), m.start(), len(d)) for m in "
                   "re.finditer(r'(?m)^diff --git a/(\\S+)', d)]:",
        "matches": 1,
    },
]
