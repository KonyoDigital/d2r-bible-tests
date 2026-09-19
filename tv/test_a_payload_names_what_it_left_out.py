# -*- coding: utf-8 -*-
"""v3341 (#97) — A PAYLOAD NAMES THE FILES IT LEFT OUT, NOT JUST HOW MANY CHARACTERS IT CUT.

`payload_for(sha)` declared its truncation as a CHARACTER COUNT — "truncated to 8142 of 16736 diff
chars at a line boundary". True, and unusable. A char count cannot tell the eye WHICH FILES are
missing, so the eye answers "the diff is correct as shown" in perfect good faith about a payload
that contains none of the change under review.

MEASURED 2026-09-19 by rebuilding this function for every version v3300-v3340 and diffing what it
would send against what the commit actually changed (version stamps excluded — they carry no logic):

    versions examined with code changes                36
    versions where a code file NEVER reached the eye   22   (61%)

AND IN SEVERAL, THE DROPPED FILE IS THE VERSION'S ENTIRE SUBJECT:

    v3330  dropped tv/tree_busy.py          the module that version exists to create
    v3315  dropped tv/second_eye_run.py     the file that version exists to change
    v3333  dropped tv/control_ui.html AND tv/test_a_session_card_always_has_a_clock.py
    v3339  dropped its own law

⚠ THE ROSTER MUST COME FROM GIT, NEVER FROM WHAT WAS FETCHED. payload_for asks for *.py first and
appends *.html only if the budget is not already spent, so when the python diff alone exceeds the
cap the html show is NEVER RUN. A dropped .html is therefore not missing from any buffer that could
be compared — it is missing from the QUESTION. Deriving the absent set from the fetched text would
report a confident 0 for exactly the v3333 case that prompted this law. That is why
`absent_from()` shells to `git show --name-only` instead of parsing what it already has.

THREE STATES, AND COLLAPSING ANY TWO IS THE DEFECT:
    a LIST  -> these changed files never reached the eye at all
    []      -> MEASURED AND NONE — every changed code file is in the payload
    None    -> the roster could not be read: UNKNOWN, and NEVER "nothing was missed"

⚠ THIS DOES NOT WIDEN THE PAYLOAD, AND DELIBERATELY SO. v3299 ruled that closing the coverage gap
means a bigger payload, which costs money and is HIS call. That law pinned instead that the runner
STATES ITS OWN REACH. This is the same move one level down: the payload now states which files it
could not carry. [[unknown-stays-unknown]] [[the-unjoined-end]] [[zero-needs-a-denominator]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import second_eye_run as R  # noqa: E402


class TestAPayloadNamesWhatItLeftOut(unittest.TestCase):

    def setUp(self):
        if not os.path.isdir(os.path.join(ROOT, ".git")):
            self.skipTest("no git checkout here — the changed-file roster cannot be asked for")

    # ── the helper ────────────────────────────────────────────────────────────────────────────
    def test_a_file_that_never_reached_the_payload_is_named(self):
        """BEHAVIOURAL. An empty body means nothing arrived, so every changed file is absent."""
        absent, why = R.absent_from("HEAD", "")
        self.assertIsNotNone(
            absent, "absent_from returned UNKNOWN for HEAD in a real checkout (%s); the roster IS "
                    "readable here, so the caller is told UNKNOWN when the answer was available."
                    % (why or "no reason given"))
        self.assertGreaterEqual(
            len(absent), 1,
            "HEAD changed %d code file(s) and none was reported absent from an EMPTY payload. A "
            "payload containing nothing cannot have carried anything." % len(absent))

    def test_a_complete_payload_reports_MEASURED_AND_NONE(self):
        """⚠ THE BASELINE. A law that only ever sees files named proves nothing about the [] case —
        it would pass over a helper that returns every file every time. [[regression-guard]] §5"""
        names, _ = R._sh(["git", "show", "--format=", "--name-only", "HEAD",
                          "--", "*.py", "*.mjs", "*.sh", "*.html"])
        self.assertIsNotNone(names, "could not read HEAD's changed files; refusing to judge")
        body = "\n".join("diff --git a/%s b/%s" % (f, f) for f in names.split())
        absent, _why = R.absent_from("HEAD", body)
        self.assertEqual(
            absent, [],
            "a payload carrying every changed file still reported %r absent. A warning that fires "
            "when nothing is wrong is an off switch — it teaches the reader to skip the line that "
            "matters. [[strictness-that-closes-the-lane]]" % (absent,))

    def test_an_unreadable_roster_is_UNKNOWN_and_never_an_empty_list(self):
        """⚠⚠ THE ONE THAT MATTERS. [] is read by the caller as MEASURED-AND-NONE, so a failed git
        call would print nothing and the operator would conclude the payload was complete."""
        absent, why = R.absent_from("deadbeefdeadbeefdeadbeefdeadbeefdeadbeef", "")
        self.assertIsNone(
            absent,
            "an unresolvable sha returned %r instead of None. An empty list means 'every changed "
            "file reached the eye' — that would be a confident zero manufactured from an error, "
            "which is the exact defect this whole law exists to remove." % (absent,))
        self.assertTrue(
            (why or "").strip(),
            "UNKNOWN was returned with no reason, so nothing can say WHY the roster is unreadable.")

    def test_the_roster_comes_from_git_not_from_the_fetched_text(self):
        """⚠ LOAD-BEARING. Deriving the absent set from the payload text cannot see a file the
        payload never asked for — and *.html is exactly that file whenever the cap is already
        spent. This is the difference between catching v3333 and reporting 0 for it."""
        src = _code(os.path.join(HERE, "second_eye_run.py"))
        i = src.find("def absent_from(")
        self.assertGreater(i, -1, "absent_from() is gone; the roster has no single definition")
        j = src.find("\ndef ", i + 1)
        self.assertGreater(j, i, "could not bound absent_from — refusing to judge a slice whose "
                                 "far end is a guess. [[source-reading-guard]]")
        fn = src[i:j]
        self.assertIn(
            "--name-only", fn,
            "absent_from no longer asks git for the changed-file roster. Any roster derived from "
            "the fetched diff is blind to a file that was never fetched, which is the majority of "
            "this defect's population.")
        for pat in ('"*.py"', '"*.html"'):
            self.assertIn(
                pat, fn,
                "absent_from no longer asks git about %s, so a dropped %s file cannot be named."
                % (pat, pat))

    # ── the join: a correct helper nobody reads fixes nothing ─────────────────────────────────
    def test_the_payload_prints_the_names_it_was_given(self):
        """[[the-unjoined-end]] — the helper being right is worthless if payload_for drops it."""
        real = R.absent_from
        R.absent_from = lambda sha, body: (["tv/PLANTED_ABSENT_FILE.py"], "")
        try:
            prompt, dropped, _absent, _reach = R.payload_for("HEAD")
        finally:
            R.absent_from = real
        self.assertIsNotNone(prompt, "payload_for returned nothing for HEAD")
        self.assertIn(
            "tv/PLANTED_ABSENT_FILE.py", prompt,
            "the payload did not NAME the absent file in the prompt, so the eye is told a count and "
            "left to assume the rest of the commit was unchanged.")
        self.assertIn(
            "tv/PLANTED_ABSENT_FILE.py", dropped or "",
            "the absent file is missing from the `dropped` note, so the LEDGER ROW will not carry "
            "it either — and a later reader sees a clean verdict with no way to know its reach "
            "without rebuilding the payload by hand. That is how this went unnoticed for 22 ships.")

    def test_an_unknown_roster_reaches_the_prompt_as_UNKNOWN(self):
        """None and [] must not print the same thing, or a failed roster reads as full coverage."""
        real = R.absent_from
        R.absent_from = lambda sha, body: (None, "planted: the roster could not be read")
        try:
            prompt, dropped, _absent, _reach = R.payload_for("HEAD")
        finally:
            R.absent_from = real
        self.assertIn(
            "UNKNOWN", prompt,
            "an unreadable roster did not reach the prompt as UNKNOWN, so the eye cannot tell a "
            "complete payload from one whose coverage nobody could establish.")
        self.assertIn(
            "UNKNOWN", dropped or "",
            "the row will not record that the payload's reach was UNKNOWN.")

    def test_the_caller_branches_on_None_rather_than_collapsing_it(self):
        """A caller writing `if absent:` alone folds UNKNOWN into MEASURED-AND-NONE silently."""
        src = _code(os.path.join(HERE, "second_eye_run.py"))
        i = src.find("def payload_for(")
        self.assertGreater(i, -1, "payload_for is gone")
        j = src.find("\ndef ", i + 1)
        blk = src[i:j] if j > i else src[i:]
        self.assertIn(
            "absent is None", blk,
            "payload_for does not branch on `absent is None`. Comments are stripped before this "
            "check, because the prose above it explains exactly this distinction. [[REG-1070]]")


def _code(path):
    """Source with comments removed — this law's subject documents the very shapes it bans."""
    with io.open(path, encoding="utf-8") as fh:
        raw = fh.read()
    return "\n".join(re.sub(r"#.*$", "", l) for l in raw.split("\n"))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "hardcoding an empty absent set puts every dropped file back out of sight",
        "file": "tv/second_eye_run.py",
        "find": "    absent, _nwhy = absent_from(sha, body)",
        "replace": "    absent, _nwhy = [], \"\"",
        "matches": 1,
    },
    {
        "why": "returning [] for an unreadable roster turns a failed git call into full coverage",
        "file": "tv/second_eye_run.py",
        "find": '        return None, (why or "the changed-file roster could not be read")',
        "replace": '        return [], (why or "the changed-file roster could not be read")',
        "matches": 1,
    },
    {
        "why": "dropping *.html from the roster makes control_ui.html invisible again - the v3333 case",
        "file": "tv/second_eye_run.py",
        "find": '                      "--", "*.py", "*.mjs", "*.sh", "*.html"], timeout=90)',
        "replace": '                      "--", "*.py", "*.mjs", "*.sh"], timeout=90)',
        "matches": 1,
    },
    {
        "why": "not naming the files in the prompt leaves the eye with a char count it cannot use",
        "file": "tv/second_eye_run.py",
        "find": '                 % ", ".join(absent))',
        "replace": '                 % len(absent))',
        "matches": 1,
    },
]
