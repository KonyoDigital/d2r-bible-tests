# -*- coding: utf-8 -*-
"""v3316 — A LOOK IS RECORDED AGAINST THE COMMIT IT ACTUALLY READ.

`payload_for(sha)` resolves a commit, builds the diff from it, hands it to the eye — and the sha
was then THROWN AWAY. Measured 2026-09-18 across all 824 rows written before this: there is no
sha key at all. So the ledger could answer *"was this VERSION looked at"* and could not answer
*"was this COMMIT looked at"* — and the second question is the one that matters, because this repo
batches 3-4 versions per commit on purpose to pay the gate once.

MEASURED, and it is why this is not cosmetic: `0bf8cb6d` is titled **"v3304-v3307"** and ships
FOUR versions. Asking the eye once per version sends the SAME 10,016-byte payload four times —
four paid looks at one set of bytes, filed as four independent reviews. That is n inflated by
REPETITION, which is fake confluence, and it is the error this field exists to prevent. One look,
one sha, credited to every version that commit shipped.

⚠ AND THE HYPHEN RANGE IS INVISIBLE TO THE BACKLOG TOOL. `_VER_LEADING_RUN` accepts `+`, `,` and
`&` between versions but NOT `-`, so "v3304-v3307" registers as v3304 alone and v3305/v3306/v3307
are invisible to `versions_in_history()`. That is the v2862 scar — which added the `+` form for
exactly this reason — repeating with a new separator. Measured over 200 subjects on origin/main:
1 hyphen range, hiding 3 versions.

⚠ `looked_at_commit` RETURNS None, NEVER False, WHEN NO ROW CARRIES A SHA. Every row written
before v3316 is unstamped; answering False for them would make the entire 824-row history read as
"never looked at" and demand it all be bought again. UNKNOWN is the honest answer and it is
pinned below. [[unknown-stays-unknown]] [[heart-first]] §6 — persist what you KNEW.
"""
import os
import re
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# Its docstrings and failure messages carry non-ASCII, and a unittest failure PRINTS them. On a
# cp1255 console that crash happens while REPORTING, so a clean tree exits non-zero for a reason
# that has nothing to do with the law. Caught by test_control's encoding-safety gate.
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import second_eye_ledger as L       # noqa: E402
import second_eye_run as R          # noqa: E402


class TestALookRecordsTheCommitItRead(unittest.TestCase):

    def test_a_row_carries_the_commit_the_eye_actually_read(self):
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        try:
            row = L.record(version="v9101", model="grok-4-1-fast-reasoning", verdict="clean",
                           findings=[], answer_head="No defects found.", path=path,
                           sha="0bf8cb6dcafe")
            self.assertEqual(
                row.get("sha"), "0bf8cb6dcafe",
                "the row records sha=%r. Without the commit, one look at a four-version commit "
                "cannot be told from four looks, and the ledger cannot answer the question the "
                "gate needs to ask." % (row.get("sha"),))
        finally:
            os.unlink(path)

    def test_one_look_at_one_commit_answers_for_every_version_it_shipped(self):
        """THE POINT. v3304-v3307 is ONE commit; paying for it four times is fake confluence."""
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        try:
            L.record(version="v3304", model="grok-4-1-fast-reasoning", verdict="clean",
                     findings=[], answer_head="No defects found.", path=path, sha="0bf8cb6d")
            self.assertIs(
                L.looked_at_commit("0bf8cb6d", path), True,
                "the commit was looked at and looked_at_commit says otherwise.")
            # the abbreviated/full forms must not be two different commits
            self.assertIs(
                L.looked_at_commit("0bf8cb6dcafebabe", path), True,
                "a longer form of the SAME sha read as a different commit, so the join would "
                "break on whichever length the caller happens to hold.")
            self.assertIs(
                L.looked_at_commit("deadbeef", path), False,
                "a commit nobody looked at read as looked-at.")
        finally:
            os.unlink(path)

    def test_a_ledger_with_no_sha_anywhere_is_UNKNOWN_and_never_a_denial(self):
        """⚠ 824 rows predate this field. False here would demand the whole history be re-bought."""
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        try:
            L.record(version="v3304", model="m", verdict="clean", findings=[],
                     answer_head="No defects found.", path=path)   # no sha, as every old row
            self.assertIsNone(
                L.looked_at_commit("0bf8cb6d", path),
                "a ledger whose rows carry no sha answered %r about a commit. Nobody recorded "
                "which commit those looks read, so the answer is UNKNOWN — answering False would "
                "declare 824 real looks to have never happened."
                % (L.looked_at_commit("0bf8cb6d", path),))
            self.assertIsNone(
                L.looked_at_commit("", path),
                "an empty sha must be UNKNOWN, not a measured False.")
        finally:
            os.unlink(path)

    def test_an_unbound_version_resolves_to_the_commit_that_SHIPS_it_not_one_that_mentions_it(self):
        """2026-09-26 - with v3511's TASKS.md row still `(this commit)`, commit_for fell back to subjects and took the
        FIRST one naming v3511 anywhere: "ledger: the self-arming rows the v3511 gate set recorded" - the commit after
        the ship - and the eye would have read a 1-character payload. DRIVEN on a fake history, newest first, with no
        bound row: the ledger commit and a merge that mention versions come BEFORE the ship; the ship must win, a range
        still ships its last version, and a version only ever mentioned is UNKNOWN (None), never a guess"""
        log = "\n".join([
            "aaaa1111 ledger: the self-arming rows the v3511 gate set recorded (8)",
            "bbbb2222 merge: #174 v-B3 onto v3508",
            "cccc3333 v3511: the frozen-screen watch never reads an iCloud placeholder",
            "dddd4444 v3304-v3307 — four versions in one ship",
            "eeee5555 fix: two v3494 contract holes the second eye found",
        ])
        real_sh, real_bound = R._sh, R._bound_commit
        R._sh = lambda args, timeout=60: (log, "") if args[:2] == ["git", "log"] else real_sh(args, timeout)
        R._bound_commit = lambda version: None
        try:
            got = dict((v, R.commit_for(v)[0]) for v in ("v3511", "v3307", "v3508", "v3494"))
        finally:
            R._sh, R._bound_commit = real_sh, real_bound
        self.assertEqual(got["v3511"], "cccc3333", "v3511 resolved to %s, not the commit that shipped it" % got["v3511"])
        self.assertEqual(got["v3307"], "dddd4444", "a range's last version lost its ship")
        self.assertIsNone(got["v3508"], "a version only MENTIONED (a merge onto it) was given a commit: %s" % got["v3508"])
        self.assertIsNone(got["v3494"], "a version only mentioned in a fix subject was given a commit: %s" % got["v3494"])

    def test_a_hyphen_range_in_a_commit_subject_is_a_range(self):
        """v3304-v3307 ships FOUR versions; the parser saw one. [[v2862]] with a new separator."""
        got = R.versions_in_run("v3304-v3307 — attribution, the overtaken open, and red-on-purpose")
        self.assertEqual(
            got, ["v3304", "v3305", "v3306", "v3307"],
            "a hyphen range parsed as %r. v2862 added the `+` form because a subject reading "
            "'v2859+v2860' made v2860 INVISIBLE to the queue; the hyphen form does the same thing "
            "to three versions at once, and v3305/v3306 shipped unlooked-at because of it."
            % (got,))

        # the SEPARATOR must not eat the title. "v3312 — the river" is one version and an em-dash.
        self.assertEqual(
            R.versions_in_run("v3312 — the river now prints its doors"), ["v3312"],
            "the title separator was read as a range, so a single-version ship would claim "
            "versions that do not exist.")
        # and a version mentioned LATER in the subject still must not count (v2854's protection)
        self.assertEqual(
            R.versions_in_run("fix: the v2804 row narrated the catcher"), [],
            "a version named mid-subject was registered as a ship. That is the protection the "
            "leading-run anchor exists for and it must survive this widening.")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "2026-09-26 - commit_for takes any subject that MENTIONS the version again: v3511 -> the ledger commit after it",
        "file": "second_eye_run.py",
        "find": "        if version in versions_in_run(subject):\n",
        "replace": "        if re.search(r\"\\b%s\\b\" % re.escape(version), subject):\n",
        "matches": 1,
    },
    {
        "why": "dropping the sha makes one look at a four-version commit unprovable",
        "file": "tv/second_eye_ledger.py",
        "find": '        "sha": (str(sha).strip() or None) if sha else None,',
        "replace": '        "sha": None,',
        "matches": 1,
    },
    {
        "why": "answering False for an unstamped ledger declares 824 real looks never happened",
        "file": "tv/second_eye_ledger.py",
        "find": "    return False if any_stamped else None",
        "replace": "    return False",
        "matches": 1,
    },
]
