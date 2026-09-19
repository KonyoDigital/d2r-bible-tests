# -*- coding: utf-8 -*-
"""v3371 (#116) — THE EYE'S BUDGET IS SHARED, NOT SPENT ALPHABETICALLY.

MEASURED on v3368 and verified as an exact prefix match: the admitted set was
sorted(changed files minus the always-changing six)[:5]. Nothing weighed relevance, size or risk —
git's default sort decided who got reviewed.

    diff 63,329 chars · cap admitted 8,934 (14%)
    reached : console_doctor · control_app · corroborate · run_gates · test_a_bare_name_...
    dropped : tv/tv_diablo.py · tv/vault_retro.py · bible.html   <- v3368's ENTIRE subject

The eye said so itself, unprompted, when asked to review v3368: "the only consumer of the three new
fields is the new doctor check; its producer lives in the missing files." It had been shown the
READER and never the WRITER, so it could not have found the dropped join that a hand inspection
found minutes earlier.

TWENTY-THREE engine files sort behind all 460 tv/test_*.py and are therefore structurally last in
every payload — the whole vault lane, plus tree_busy, tv_diablo, unknown_age, verdict_provenance,
window_visibility, write_census, write_witness.

⚠ THE FEEDBACK LOOP: the standing order is JOIN -> GATE -> HEART -> BANK, so nearly every version
adds a large new tv/test_*.py. Alphabetically that lands AHEAD of the engine it protects and pushes
it past the cap. THE LAW CROWDED OUT ITS OWN SUBJECT.

CORROBORATED BY A RECORD WRITTEN BEFORE THE DIAGNOSIS EXISTED: 16 of the 19 ledger rows carrying an
`absent` list (84%) lost a .py file, tv_diablo.py alone 9 times — and #97 logged "v3330 lost
tree_busy.py, its own subject". tree_busy.py is one of the 23.

=== THE DESIGN WAS CHOSEN BY MEASUREMENT, over 30 real versions / 182 changed code files ===
    alphabetical prefix (before)    68/182  37.4%   median cov   -    slivers <15%:  0
    engine-first ordering           74/182  40.7%                     <- FIRST INSTINCT, REFUTED
    fair share, no floor           182/182 100.0%   median cov  66%   slivers <15%: 26
    fair share, floor 1500         151/182  83.0%   median cov 100%   slivers <15%:  1   <- SHIPPED

⚠⚠ THE NO-FLOOR VARIANT IS A TRAP AND second_eye_run.py ALREADY RECORDS WHY, TWICE. v2803: the
payload ended at `+    return ` and the eye returned TWO high-severity defects about a function
whose last two characters the cap had removed. v2850: `drift` reported as "referenced but never
declared", when its declaration sat above the first changed line. A sliver does not merely fail to
help — IT MANUFACTURES FINDINGS, and a false one costs more than a missed one because it has to be
chased and refuted by hand. So a file gets a USEFUL slice or none, and the ones that get none are
named by the v3341 mechanism that is already there.

=== THREE DEFECTS THIS FIX HAD BEFORE IT SHIPPED, ALL FOUND BY RUNNING IT ON A REAL DIFF ===
1. A SLICE CUT *BEFORE* ITS TRAILING NEWLINE MERGES TWO FILES. `seg[:c]` left the next file's
   `diff --git` header appended to a half-line, so it was no longer at line start: the second file
   became INVISIBLE to the eye and to every parser downstream, INCLUDING the absent-file
   accounting. The note claimed "tv/vault_retro.py 45%" while re-parsing the function's own output
   could not find vault_retro.py at all. That is the exact defect this version exists to remove,
   reintroduced by its own fix — and the only reason it was caught is that the output was re-parsed
   instead of trusted. `test_every_file_named_in_the_note_is_reparseable` is that check, kept.
2. A LINE-BOUNDARY CUT CAN COLLAPSE. WINDOWS_SHIP.json is one long line, so the cut landed at 6% of
   it — a sliver, which is what the floor exists to prevent. The floor must be judged on the slice
   AFTER the cut, never on the share that was allocated.
3. The first design ordered engine files first. Measured 37.4% -> 40.7% and dropped.
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402

_console_safe_enable()

import second_eye_run as SER  # noqa: E402


def _diff(*pairs):
    """Build a diff whose sections are exactly the (path, line-count) pairs given."""
    out = []
    for path, lines in pairs:
        out.append("diff --git a/%s b/%s\n--- a/%s\n+++ b/%s\n" % (path, path, path, path))
        out.append("".join("+line %04d of %s\n" % (i, path) for i in range(lines)))
    return "".join(out)


class TestTheBudgetIsSharedNotSpentAlphabetically(unittest.TestCase):

    def setUp(self):
        self.cap = 9000
        # three files: one small enough to complete, two that must be cut
        self.body = _diff(("tv/aaa_small.py", 20), ("tv/mmm_big.py", 600), ("tv/zzz_last.py", 600))

    def _share(self):
        return SER._share_the_budget(self.body, self.cap)

    def test_the_last_file_alphabetically_still_reaches_the_eye(self):
        """The whole point. Under the old prefix cut zzz_last.py could never arrive."""
        out, _note, _absent = self._share()
        seen = [p for p, _a, _b in SER._file_sections(out)]
        self.assertIn("tv/zzz_last.py", seen,
                      "a file at the end of the alphabet is not a file of lower value")

    def test_the_body_never_exceeds_the_cap(self):
        out, _n, _a = self._share()
        self.assertLessEqual(len(out), self.cap)

    def test_every_emitted_slice_ends_on_a_line_boundary(self):
        """A mid-statement cut manufactures findings — v2803 returned two from one."""
        out, _n, _a = self._share()
        for p, a, b in SER._file_sections(out):
            seg = out[a:b]
            self.assertTrue(seg.endswith("\n"), "%s does not end on a line boundary" % p)

    def test_every_file_named_in_the_note_is_reparseable(self):
        """THE DEFECT THIS FIX HAD: the note said 45% for a file the output had swallowed."""
        out, note, _a = self._share()
        seen = set(p for p, _a2, _b2 in SER._file_sections(out))
        for chunk in (note or "").replace("shown in part: ", "").split(", "):
            name = chunk.strip().rsplit(" ", 1)[0].strip()
            if not name:
                continue
            self.assertIn(name, seen,
                          "the note claims %r was shown, but re-parsing the output cannot find it "
                          "— which is how two files merge into one and the second disappears" % name)

    def test_no_cut_slice_is_a_sliver(self):
        """Judged AFTER the cut: a long-line file can collapse well below its allocated share.

        ⚠ ONLY THE CUT FILES. A SMALL COMPLETE FILE IS NOT A SLIVER — it is the whole diff, and the
        eye can reason about it perfectly. The first version of this case asserted the floor on
        every emitted section and failed on a complete 20-line file at 691 chars, which is the
        instrument conflating "short" with "truncated". The note names exactly the files that were
        cut, so that is the population to judge. [[regression-guard]] §5a — suspect the instrument.
        """
        out, note, _a = self._share()
        cut_names = set()
        for chunk in (note or "").replace("shown in part: ", "").split(", "):
            nm = chunk.strip().rsplit(" ", 1)[0].strip()
            if nm:
                cut_names.add(nm)
        self.assertTrue(cut_names, "this fixture must produce at least one cut file or it is "
                                   "measuring nothing")
        for p, a, b in SER._file_sections(out):
            if p not in cut_names:
                continue
            self.assertGreaterEqual(
                b - a, SER.MIN_USEFUL_SLICE // 2,
                "%s was CUT down to %d chars — too small to reason about, and a sliver "
                "manufactures findings" % (p, b - a))

    def test_a_file_that_gets_nothing_is_named(self):
        tight = SER._share_the_budget(self.body, SER.MIN_USEFUL_SLICE + 200)
        out, _note, absent = tight
        seen = set(p for p, _a, _b in SER._file_sections(out))
        for p, _a, _b in SER._file_sections(self.body):
            if p not in seen:
                self.assertIn(p, absent,
                              "%s was dropped silently — an unnamed omission reads as coverage" % p)

    def test_a_single_file_diff_still_cuts_simply(self):
        one = _diff(("tv/only.py", 900))
        out, _n, absent = SER._share_the_budget(one, 500)
        self.assertLessEqual(len(out), 500)
        self.assertEqual(absent, [], "there is nothing to share with, so nothing is absent")

    def test_allocation_does_not_depend_on_file_order(self):
        rev = _diff(("tv/zzz_last.py", 600), ("tv/mmm_big.py", 600), ("tv/aaa_small.py", 20))
        a_seen = set(p for p, _x, _y in SER._file_sections(self._share()[0]))
        b_seen = set(p for p, _x, _y in SER._file_sections(SER._share_the_budget(rev, self.cap)[0]))
        self.assertEqual(a_seen, b_seen,
                         "who gets reviewed must not depend on the order git happened to print")

    def test_no_file_is_emitted_twice(self):
        out, _n, _a = self._share()
        seen = [p for p, _x, _y in SER._file_sections(out)]
        self.assertEqual(len(seen), len(set(seen)), "a duplicated section spends the cap twice")

    def test_the_truncation_path_actually_calls_the_allocator(self):
        """⚠ A TESTED HELPER WITH AN UNTESTED JOIN IS THIS REPO's MOST REPEATED DEFECT.

        Every other case here calls `_share_the_budget` directly, so reverting the CALL SITE to the
        old alphabetical prefix left them all green — measured, that red-proof was BLIND on its
        first run. The helper being correct says nothing about the payload using it.
        [[the-unjoined-end]]
        """
        import ast
        src = io.open(os.path.join(HERE, "second_eye_run.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        callers = 0
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef) or node.name == "_share_the_budget":
                continue
            for inner in ast.walk(node):
                if (isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name)
                        and inner.func.id == "_share_the_budget"):
                    callers += 1
        self.assertGreaterEqual(
            callers, 1,
            "_share_the_budget has no production caller — the budget is being spent by whatever "
            "code replaced it, and every other case in this file would still pass")

    def test_a_single_enormous_line_is_dropped_not_slivered(self):
        """⚠ THE FLOOR CANNOT FIRE IN A FIXTURE OF SHORT LINES, AND MINE WAS ONE.

        Removing the post-cut floor left every case green because nothing in the fixture could
        collapse — measured, BLIND on its first run. WINDOWS_SHIP.json is one long line and cut to
        6% of itself in the real run, which is what this reproduces: a line-boundary cut inside a
        12,000-character line lands back at the header, so the slice must be DROPPED AND NAMED
        rather than emitted as a few bytes of header the eye would reason about.
        """
        big = "diff --git a/tv/one.py b/tv/one.py\n--- a/tv/one.py\n+++ b/tv/one.py\n"
        big += "+" + ("x" * 12000) + "\n"
        small = _diff(("tv/two.py", 600))
        out, _note, absent = SER._share_the_budget(big + small, 9000)
        seen = dict((p, b - a) for p, a, b in SER._file_sections(out))
        self.assertNotIn(
            "tv/one.py", [p for p, n in seen.items() if n < SER.MIN_USEFUL_SLICE],
            "one.py came through as a sliver of %d chars — that is a header and no code, and a "
            "sliver manufactures findings" % seen.get("tv/one.py", 0))
        self.assertIn("tv/one.py", absent,
                      "it was dropped without being named, which reads as coverage it never had")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "the alphabetical prefix is the defect: it reviewed by filename, so the end of the alphabet was never reviewed",
        "file": "tv/second_eye_run.py",
        "find": "        body, _cut_note, _cut_absent = _share_the_budget(body, _cap())",
        "replace": "        _c = body.rfind(\"\\n\", 0, _cap())\n        body, _cut_note, _cut_absent = body[:_c if _c > 0 else _cap()], None, []",
        "matches": 1,
    },
    {
        "why": "cutting before the trailing newline merges two files and makes the second invisible",
        "file": "tv/second_eye_run.py",
        "find": "            seg = seg[:c + 1] if c > 0 else seg[:want]",
        "replace": "            seg = seg[:c] if c > 0 else seg[:want]",
        "matches": 1,
    },
    {
        "why": "without the post-cut floor a long-line file collapses to a sliver, and a sliver manufactures findings",
        "file": "tv/second_eye_run.py",
        "find": "            if len(seg) < MIN_USEFUL_SLICE:\n                absent.append(p); continue",
        "replace": "            if False:\n                absent.append(p); continue",
        "matches": 1,
    },
    {
        "why": "a file dropped without being named reads as coverage it never had",
        "file": "tv/second_eye_run.py",
        "find": "        if want <= 0:\n            absent.append(p); continue",
        "replace": "        if want <= 0:\n            continue",
        "matches": 1,
    },
]
