# -*- coding: utf-8 -*-
"""v3296 — THE INTAKE DOOR HAS ONE DEFINITION, AND A GUEST BOARD MAY NOT WALK THROUGH HIS.

Konyo authorised this on 2026-09-18 while scoping the parallel-test console: *"yea do it
obivously"*.

The endpoint expression was written out BY HAND AT TEN SITES in bible.html — 24312, 26090, 26722,
26960, 27672, 37972, 39894, 46859, 47559, 52952 — each carrying the production URL as its `file://`
fallback. The copies had ALREADY DRIFTED: nine read `localStorage`, one read `window.LSR`. That is
the same shape as the lane work list collapsed in v3295, except a missed copy here posts real data
to a live public door.

⚠⚠ THE SAFETY HALF, AND IT IS THE POINT. Over `file://` the old default was the production endpoint
FOR EVERY BOARD. A guest board — no `d2r_ownerClaim`, which is exactly what the Linux test console
is — would therefore post its intake into HIS REAL INTAKE, silently, and running the two consoles
in parallel is the precise activity that fires it. The test we want to run was the thing that would
contaminate the data we were testing against.

HIS OWN BOARD IS UNCHANGED AND MUST STAY UNCHANGED. An owner on `file://` posting to his own live
door is correct and intended. Breaking that would be far worse than the defect, so the law pins the
owner branch as tightly as it pins the guest one.

TWO HALVES:

  1. ONE DEFINITION — the production host appears EXACTLY ONCE in executable source, inside
     `_d2rIntakeEndpoint`. Any re-inlined copy is a future drift, and ten copies drifted already.

  2. THE GUEST BRANCH CANNOT REACH IT — the production return must sit behind a `_D2R_OWNER` test,
     and the function's last word for a guest must be the relative path. Half 1 alone would go
     green over a helper that hands the public door to everyone, which is the whole defect one
     layer down. [[presence-law-vs-reachability-law]]

⚠ THIS LAW STRIPS COMMENTS BEFORE READING (frame_authority._executable_only). Load-bearing: the
helper's own comment block explains the production/guest split in prose, and a law reading raw
source would be satisfied by the explanation rather than the code. That is REG-1070.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

# Its docstrings and failure messages carry non-ASCII, and a unittest failure PRINTS them. On a
# cp1255 console that crash happens while REPORTING, so a clean tree exits non-zero for a reason
# that has nothing to do with the law. Caught by test_control's encoding-safety gate.
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

from frame_authority import _executable_only  # noqa: E402

BIBLE = os.path.join(ROOT, "bible.html")

#: The live public door. If this string moves, the law must move with it — deliberately, not by
#: accident, which is why it is named once here rather than pattern-matched loosely.
PUBLIC_DOOR = "bull-4-u.com/api/intake"

HELPER = "_d2rIntakeEndpoint"


def _executable_bible():
    with io.open(BIBLE, encoding="utf-8") as fh:
        src = fh.read()
    # ".js" is the idiom for taking the comment-stripping branch — _executable_only dispatches on
    # EXTENSION, and ".html" falls through to the Python branch where ast.parse throws and the
    # source is returned UNSTRIPPED, which would read the very prose this law must ignore.
    return _executable_only(src, ".js")


class TestAGuestMayNotWalkThroughHisDoor(unittest.TestCase):

    def test_the_public_door_is_named_exactly_once(self):
        """ONE DEFINITION: ten hand-copies drifted; a re-inlined eleventh would drift too."""
        body = _executable_bible()

        # A zero needs a denominator: if the strip ate the file, a clean count proves nothing.
        self.assertGreater(
            len(body), 500000,
            "the comment strip returned only %d chars of bible.html — it ran away, so any count "
            "taken from it is meaningless. [[zero-needs-a-denominator]]" % len(body))

        hits = body.count(PUBLIC_DOOR)
        self.assertEqual(
            hits, 1,
            "the live public door is named %d time(s) in executable source; it must appear EXACTLY "
            "once, inside %s(). Ten hand-written copies of this URL is what v3296 removed, and "
            "nine of them had already drifted to a different storage reader than the tenth. "
            "A re-inlined copy is a door that changes in one place and not the others."
            % (hits, HELPER))

    def test_every_caller_goes_through_the_helper(self):
        """The helper existing proves nothing if the call sites still roll their own."""
        body = _executable_bible()

        self.assertIn(
            "window.%s = function" % HELPER, body,
            "%s is not defined in executable source — the single definition is gone and every "
            "caller is reading a name nothing sets." % HELPER)

        # ⚠⚠ THIS COUNT IS TAKEN ON RAW SOURCE, DELIBERATELY, AND HERE IS THE MEASUREMENT.
        # `_executable_only` DROPS A REAL CALL SITE: bible.html L38004,
        # `return window._d2rIntakeEndpoint();` inside `_aicIntakeEndpoint()`, disappears from the
        # stripped text. The two lines above it hold REGEX LITERALS — /[?&]engine=1/ and
        # /:(17772|17771)\b/ — and their slashes are being read as a comment, so live code after
        # them is swallowed. Measured 2026-09-18: raw 10 call sites, stripped 9.
        # Counting on the stripped text would make this law quietly wrong by one, forever.
        # ⚠ The risk raw-counting reintroduces is a COMMENT satisfying the assertion, so each hit
        # is checked to be real code rather than trusted. [[source-reading-guard]]
        with io.open(BIBLE, encoding="utf-8") as fh:
            raw = fh.read()
        calls, commented = 0, 0
        for m in re.finditer(r"_d2rIntakeEndpoint\s*\(\s*\)", raw):
            bol = raw.rfind("\n", 0, m.start()) + 1
            prefix = raw[bol:m.start()]
            if "//" in prefix or "*" == prefix.strip()[:1]:
                commented += 1
                continue
            calls += 1
        self.assertEqual(
            commented, 0,
            "%d mention(s) of %s() sit inside a comment. A law that counted those would be "
            "satisfied by prose describing the helper rather than by code calling it."
            % (commented, HELPER))
        self.assertGreaterEqual(
            calls, 10,
            "only %d executable call site(s) reach %s(); ten were rewritten in v3296, so callers "
            "have been removed or have gone back to inlining the expression." % (calls, HELPER))

    def test_a_guest_cannot_reach_the_public_door(self):
        """THE SAFETY HALF. Structure alone would pass a helper that hands it to everyone."""
        body = _executable_bible()

        i = body.find("window.%s = function" % HELPER)
        self.assertGreater(i, -1, "%s is not defined at all" % HELPER)
        # Anchor BOTH ends — a fixed-size window past the region reads as ABSENT.
        j = body.find("\n};", i)
        self.assertGreater(j, i, "could not find the end of %s — refusing to judge a slice whose "
                                 "far end is a guess. [[source-reading-guard]]" % HELPER)
        fn = body[i:j]

        owner = fn.find("_D2R_OWNER")
        door = fn.find(PUBLIC_DOOR)
        self.assertGreater(
            owner, -1,
            "%s() no longer tests _D2R_OWNER anywhere. Without that test every board — including "
            "an unclaimed guest such as the Linux parallel-test console — resolves to his live "
            "public door on file://, and its intake lands in HIS real intake." % HELPER)
        self.assertGreater(
            door, owner,
            "the public door is returned BEFORE %s() has tested _D2R_OWNER, so a guest reaches it. "
            "The owner branch must gate it." % HELPER)

        # And the guest's actual outcome: the last word of the function is the relative path.
        tail = fn[door:]
        self.assertIn(
            "'/api/intake'", tail,
            "after the owner branch returns the public door, %s() gives a guest no relative "
            "fallback — so a guest board either reaches the public host or gets nothing at all, "
            "and 'nothing at all' is how a silent misdirect starts." % HELPER)

    def test_the_owner_still_has_his_door(self):
        """Breaking HIS intake would be far worse than the defect. Pin it explicitly."""
        body = _executable_bible()
        i = body.find("window.%s = function" % HELPER)
        j = body.find("\n};", i)
        fn = body[i:j]
        self.assertIn(
            PUBLIC_DOOR, fn,
            "%s() no longer returns the production endpoint AT ALL. His own board on file:// must "
            "still reach his own live door — that behaviour is correct and was never the defect." % HELPER)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "re-inlining one call site puts a second copy of the public door back in the source",
        "file": "bible.html",
        "find": "      var endpoint = window._d2rIntakeEndpoint();",
        "replace": ("      var endpoint = localStorage.getItem('d2r_intakeUrl') "
                    "|| (location.protocol==='file:'?'https://bull-4-u.com/api/intake':'/api/intake');"),
        "matches": 1,
    },
    {
        "why": "dropping the owner test hands the live public door to every guest board",
        "file": "bible.html",
        "find": "  if (window._D2R_OWNER) return 'https://bull-4-u.com/api/intake';",
        "replace": "  return 'https://bull-4-u.com/api/intake';",
        "matches": 1,
    },
]
