# -*- coding: utf-8 -*-
"""v2989 — THE STATUS JOURNAL IS RE-READ ONLY WHEN THE FILE CHANGES.

Found by the read-only optimization fleet as its item 1 — the largest measured win in the repo,
and three dimensions reached it independently by three different methods, which is why it is first.

THE DEFECT. The cache guard read `if _live_mode and _jh.get("h") is not None and (now - t) < 3.0`.
`_live_mode` is only true under ON AIR, so OFF AIR the cache never applied and the journal was
walked on EVERY status poll. Measured on his live console:
    ~3.9 of 7.8 percentage-points of one core   (ps delta over 60.0 s) — HALF the idle CPU
    ~20 ms of a 22.4 ms request                 (the payload's own ledger: 29 timed sections sum
                                                 to 2.3 ms, `unattributedMs` 20.1 ms = 90%)
    9.38 GB/hour re-read · 14.8M json.loads/hour at the measured 1.02 req/s
    200 of 4,033 rows used = 5.0%; the journal's mtime was 49.6 h old, so every one of those
    reads returned BYTE-IDENTICAL content
    0 of 26 timed requests came in under 20 ms — the branch was taken every single time

⚠⚠ THE FIX IS (mtime_ns, size) KEYING, NOT A LONGER TIMER, AND THE DIFFERENCE MATTERS. Extending
the 3 s window to the idle path is the version that can MISS a row. A file key cannot: any append
moves both halves, so it is STRICTLY FRESHER than the 3 s staleness the live path already ships
with. The live window is kept underneath it because that path is about smoothness under ON AIR.

⚠ AND A FAILED `stat` MUST NOT READ AS "UNCHANGED". `_jkey` is None then, `_jkey_same` is False,
and the walk happens. An unreadable journal is UNKNOWN, never a cache hit. [[unknown-stays-unknown]]

⚠⚠ THE TIMER IS PART OF THE FIX, NOT DECORATION. The block was UNTIMED, which is exactly why
`timing.slowest` kept naming a 1.9 ms section while 20 ms sat in `unattributedMs` — the console's
own instrument could not see its single largest cost. Measured after: payload 2 reports
`journal 19.3 ms` and payloads 3-4 report no journal section at all, with total falling
820.8 -> 11.4 -> 5.8 ms. Without the timer this fix could not be proven and its regression would
be invisible to the very panel built to catch it. [[zero-needs-a-denominator]]

⚠ SCOPE, STATED HONESTLY: `_kai_journal_rows` has TWENTY call sites. This law covers ONE — the
status path, the one that runs on every poll. The others still walk, and the timer is what makes
them visible next. This is not the class closed; it is the biggest single site closed and measured.
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

SRC = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()


class TheJournalIsReadOncePerChange(unittest.TestCase):

    def test_the_cache_is_keyed_on_the_file_not_on_live_mode(self):
        self.assertIn("_jkey_same", SRC,
                      "the file key is gone — the cache is back to being keyed on _live_mode, so "
                      "OFF AIR it never applies and every status poll walks the whole journal")
        self.assertIn("st_mtime_ns", SRC,
                      "the key no longer reads mtime, so an append cannot invalidate the cache")

    def test_a_failed_stat_is_not_a_cache_hit(self):
        """⚠ THE DIRECTION THAT MATTERS. Unreadable must mean WALK, never 'unchanged'."""
        i = SRC.find("_jkey_same = (")
        self.assertGreater(i, 0, "the key comparison is gone")
        line = SRC[i:SRC.find("\n", i)]
        self.assertIn("_jkey is not None", line,
                      "a failed stat would compare None == None and read as UNCHANGED, so an "
                      "unreadable journal would serve a stale payload for ever: %r" % line)

    def test_the_walk_is_timed_so_it_cannot_hide_again(self):
        self.assertIn('_t("journal", _kai_journal_rows)', SRC,
                      "the journal walk is untimed again — this is how 20 ms of a 22.4 ms request "
                      "sat in unattributedMs while timing.slowest blamed a 1.9 ms section")

    def test_the_live_three_second_window_survives(self):
        """The ON AIR path is about smoothness, not freshness — removing it is a different change."""
        self.assertIn("_live_mode and (_now_j - float(_jh.get(\"t\") or 0)) < 3.0", SRC,
                      "the live 3s window was dropped; under ON AIR the journal appends constantly, "
                      "so a pure file key would walk on every poll exactly when it costs most")

    # ── the round trip ────────────────────────────────────────────────────────────────────────
    def test_two_payloads_walk_the_journal_once(self):
        import control_app as CA
        if not hasattr(CA, "status_payload"):
            self.skipTest("status_payload absent — a skip is NOT a pass")
        CA._STATUS_JOURNAL_CACHE = None
        calls = {"n": 0}
        orig = CA._kai_journal_rows
        def counted():
            calls["n"] += 1
            return orig()
        CA._kai_journal_rows = counted
        try:
            CA.status_payload()
            first = calls["n"]
            CA.status_payload()
            CA.status_payload()
        finally:
            CA._kai_journal_rows = orig
        self.assertEqual(
            calls["n"], first,
            "the journal was walked again on a poll where the file had not changed: %d walks for "
            "3 payloads. ⚠ This counts ALL 20 call sites, so `first` is the baseline and the only "
            "claim here is that the STATUS site adds nothing after the first." % calls["n"])


RED_PROOF = [
    {
        "why": "going back to a _live_mode-only guard is the original defect: off air the cache "
               "never applies and every poll walks 4,033 rows to use 200",
        "file": "control_app.py",
        "find": "        if _jh.get(\"h\") is not None and (_jkey_same or (",
        "replace": "        if _jh.get(\"h\") is not None and (False or (",
        "matches": 1,
    },
    {
        "why": "letting a failed stat compare equal turns an unreadable journal into a permanent "
               "cache hit — a stale payload that can never refresh",
        "file": "control_app.py",
        "find": "        _jkey_same = (_jkey is not None and _jh.get(\"k\") == _jkey)",
        "replace": "        _jkey_same = (_jh.get(\"k\") == _jkey)",
        "matches": 1,
    },
    {
        "why": "un-timing the walk puts 20 ms back into unattributedMs, where the console's own "
               "instrument cannot see its largest cost",
        "file": "control_app.py",
        "find": '_t("journal", _kai_journal_rows)[-200:]',
        "replace": "_kai_journal_rows()[-200:]",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
