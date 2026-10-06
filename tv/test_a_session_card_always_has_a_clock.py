# -*- coding: utf-8 -*-
"""v3333 (#80) — A SESSION CARD ALWAYS HAS A CLOCK, AND THE FALLBACK IS EVIDENCE.

MEASURED 2026-09-19 against his live console: 2 of 422 sessions carry NO `t0` —

    n=30  s_1789330829280_66296   753 frames   reel dated 13 Sep 23:20
    n=50  s_1788879402448_41906    10 frames   reel dated 08 Sep 17:56

Both hold real footage and both sit in the river. Every card site computed
`d0 = sm.t0 ? new Date(sm.t0) : null`, so those two got `d0 = null`: the date rendered as an
em-dash and the title fell back to "Session N". He reported it as cards that never paint.

THE FALLBACK IS NOT AN INVENTED TIMESTAMP. A session id is `s_<epoch-ms>_<n>`, and on all 12
sessions checked where BOTH exist the embedded ms and `t0` agree to the minute. That is why this
law pins the ID as the fallback and nothing else.

⚠⚠ AND IT PINS THAT mtime IS NEVER USED FOR THIS. Measured the same day: ALL 19 reels on disk
carry an mtime from a single bulk pass on 16 Sep 18:10-20:14, skews 1.8 to 53.1 days. mtime
reports two months of footage as simultaneous, so a "most recent" taken from it is meaningless.
The id is the only sound clock. [[stale-reading]]

⚠ THREE OTHER t0->Date SITES ARE DELIBERATELY EXCLUDED and are named in the helper's own comment:
a day-set builder and a today-filter feed COUNTS, and widening a clock that feeds a count changes
the count. That is a decision, not an oversight, and this law does not demand they change.

⚠ THIS LAW STRIPS COMMENTS BEFORE READING (frame_authority._executable_only). Load-bearing: the
helper's comment block quotes the very expression this law bans, so a law reading raw source would
be satisfied by — or fail on — its own documentation. That is REG-1070.
"""
import io
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

from frame_authority import _executable_only  # noqa: E402

UI = os.path.join(HERE, "control_ui.html")

HELPER = "_shSessionMs"

#: The shape this fix removed. A re-inlined copy is the defect coming back.
RAW_CLOCK = re.compile(r"d0\s*=\s*sm\.t0\s*\?\s*new Date\(sm\.t0\)")


def _clock(cases):
    """Drive the helper itself with node. -> [ms per case]. The function text is cut from the
    comment-stripped source, bounded at both ends, so it is the code the cards call."""
    body, _raw = _ui()
    i = body.find("function %s(" % HELPER)
    j = body.find("\n  }", i)
    if i < 0 or j < i:
        raise AssertionError("could not bound %s — refusing to drive a guess" % HELPER)
    js = (body[i:j] + "\n  }\n"
          + "process.stdout.write(JSON.stringify(" + json.dumps(cases)
          + ".map(function(sm){ return %s(sm); })));\n" % HELPER)
    got = subprocess.run(["node", "-"], input=js.encode("utf-8"),
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    if got.returncode != 0:
        raise AssertionError(got.stderr.decode("utf-8", "replace")[:800])
    return json.loads(got.stdout.decode("utf-8"))


def _ui():
    with io.open(UI, encoding="utf-8") as fh:
        src = fh.read()
    # ".js" is the idiom for the comment-stripping branch — _executable_only dispatches on
    # EXTENSION, and ".html" falls through to the Python branch where ast.parse throws and the
    # source comes back UNSTRIPPED, which would read the prose this law must ignore.
    return _executable_only(src, ".js"), len(src)


class TestASessionCardAlwaysHasAClock(unittest.TestCase):

    def test_the_helper_is_defined_once(self):
        body, raw = _ui()
        # A zero needs a denominator: if the strip ate the file every count below is meaningless.
        self.assertGreater(
            float(len(body)) / raw, 0.50,
            "the comment strip kept only %.1f%% of control_ui.html (%d of %d chars) — every count "
            "taken from it is meaningless. [[zero-needs-a-denominator]]"
            % (100.0 * len(body) / raw, len(body), raw))
        n = body.count("function %s(" % HELPER)
        self.assertEqual(
            n, 1,
            "%s is defined %d time(s) in executable source; it must be exactly ONE definition. "
            "Four card sites hand-rolled this clock before v3333 and a second copy is how they "
            "drift apart again. [[copy-drift]]" % (HELPER, n))

    def test_no_card_site_rolls_its_own_clock(self):
        """REACHABILITY: the helper existing proves nothing if callers still inline the old form."""
        body, _raw = _ui()
        hits = RAW_CLOCK.findall(body)
        self.assertEqual(
            len(hits), 0,
            "%d card site(s) still compute the clock inline as `d0 = sm.t0 ? new Date(sm.t0)`. "
            "That is the exact expression that gave n=30 and n=50 a null clock — a session with "
            "real footage and no date on screen. Call %s() instead." % (len(hits), HELPER))

    def test_the_helper_falls_back_to_the_reel_id_and_not_to_mtime(self):
        """The fallback must be the id. mtime is measurably useless here and must never appear."""
        body, _raw = _ui()
        i = body.find("function %s(" % HELPER)
        self.assertGreater(i, -1, "%s is not defined at all" % HELPER)
        # Anchor BOTH ends — a fixed-size window past the region reads as ABSENT.
        j = body.find("\n  }", i)
        self.assertGreater(
            j, i, "could not bound %s — refusing to judge a slice whose far end is a guess. "
                  "[[source-reading-guard]]" % HELPER)
        fn = body[i:j]

        self.assertIn(
            "sessionId", fn,
            "%s no longer reads sessionId, so the id-embedded epoch — the ONLY sound clock "
            "measured on this tree — is not the fallback any more." % HELPER)
        self.assertTrue(
            re.search(r"s_\(\\d\{\d+,?\d*\}\)_|s_\(\\\\d", fn) or "s_" in fn,
            "%s does not match the `s_<ms>_<n>` id shape, so it cannot recover a clock from the "
            "id." % HELPER)
        self.assertNotIn(
            "mtime", fn.lower(),
            "%s reaches for mtime. MEASURED: all 19 reels on disk carry an mtime from one bulk "
            "pass on 16 Sep, skews 1.8 to 53.1 days — it reports two months of footage as "
            "simultaneous. A clock that cannot order anything is not a fallback. [[stale-reading]]"
            % HELPER)

    def test_the_card_clock_is_the_start_not_the_end(self):
        """REG-1816 — every card prints this clock beside "ran Xm", so it is the START. 0dcf3131
        returned t1 first and every card, dossier, recap and history tile printed the END. The
        shelf ORDER by last activity reads data-t1 in its own sort, never this helper."""
        T0, T1, SID = 1789000000000, 1789000600000, 1788000000000
        got = _clock([
            {"t0": T0, "t1": T1, "sessionId": "s_%d_1" % SID},
            {"t0": T0, "t1": T1},
            {"t0": T0, "sessionId": "s_%d_1" % SID},
            {"t1": T1, "sessionId": "s_%d_1" % SID},
            {"sessionId": "s_%d_1" % SID},
            {"t1": T1},
            {},
        ])
        self.assertEqual(got[0], T0, "a run with a start and an end printed %r, not its start" % got[0])
        self.assertNotEqual(got[0], T1, "the card prints the END time beside 'ran Xm'")
        self.assertEqual(got[1], T0)
        self.assertEqual(got[2], T0, "the id overrode a real measured start")
        self.assertEqual(got[3], SID, "a run with no t0 must fall back to the id's start, not its end")
        self.assertEqual(got[4], SID)
        self.assertEqual(got[5], 0, "an end alone is not a start; with no t0 and no id the clock is unknown")
        self.assertEqual(got[6], 0)

if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "re-inlining one card site brings back the null clock that left 2 sessions undated",
        "file": "tv/control_ui.html",
        "find": "      var _ms0 = _shSessionMs(sm), d0 = _ms0 ? new Date(_ms0) : null;",
        "replace": "      var d0 = sm.t0 ? new Date(sm.t0) : null;",
        "matches": 1,
    },
    {
        "why": "dropping the id fallback returns a t0-less session to having no clock at all",
        "file": "tv/control_ui.html",
        "find": "    var m = String((sm && sm.sessionId) || '').match(/^s_(\\d{10,})_/);\n    return m ? +m[1] : 0;",
        "replace": "    return 0;",
        "matches": 1,
    },
    {
        "why": "REG-1816 - the card clock returns the END, so every card prints it beside 'ran Xm'",
        "file": "tv/control_ui.html",
        "find": "    var t = (sm && sm.t0) ? +sm.t0 : 0;\n    if (t) return t;\n",
        "replace": "    var t1 = (sm && sm.t1) ? +sm.t1 : 0;\n    if (t1) return t1;\n"
                   "    var t = (sm && sm.t0) ? +sm.t0 : 0;\n    if (t) return t;\n",
        "matches": 1,
    },
]
