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
        """⚠⚠ v3215 — THIS PINNED A CALL FORM, AND v3208 CHANGED THE FORM WITHOUT TOUCHING THE
        MEANING. It asserted the literal `_t("journal", _kai_journal_rows)`; v3208 needed the
        `why` out of the reader, so the site became
        `_t("journal", lambda: _kai_journal_rows(want_why=True))` — still timed, still one walk,
        and this law went RED and stayed red on the shipped tree. Worse, its RED_PROOF anchor
        matched 0 times too, so heart2 filed the whole gate as INVALID/BLIND and revoked its
        standing proof.

        The claim was never about the spelling of the call. It is that the journal walk happens
        INSIDE the `_t("journal", ...)` timer, so its cost is attributed instead of landing in
        unattributedMs. That is what is asserted now. [[source-reading-guard]] [[label-outlived-referent]]
        """
        i = SRC.find('_t("journal"')
        self.assertGreater(i, 0,
                           "the journal walk is untimed again — this is how 20 ms of a 22.4 ms "
                           "request sat in unattributedMs while timing.slowest blamed a 1.9 ms "
                           "section")
        # the timed region, by paren-matching — not a fixed window, which is how the last one broke
        d, j = 0, SRC.index("(", i)
        k = j
        while k < len(SRC):
            if SRC[k] == "(":
                d += 1
            elif SRC[k] == ")":
                d -= 1
                if d == 0:
                    break
            k += 1
        timed = SRC[j:k + 1]
        self.assertLess(len(timed), 400,
                        "the _t(\"journal\", ...) call is %d chars — that is not one call, so "
                        "this is reading past it" % len(timed))
        self.assertIn("_kai_journal_rows", timed,
                      "the journal reader is no longer called inside its own timer, so its cost "
                      "goes back to unattributedMs: %r" % timed)

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
        # ⚠ #123 — the claim is about a poll "where the file had not CHANGED", and the cache keys on
        # the journal FILE (mtime, size). On a venue with no journal (every CI runner) there is no
        # file to be unchanged: CI counted 5 walks for 3 payloads and went red while this machine
        # passed. That is ABSENCE of the premise, reported UNMEASURED — not a pass, not a failure.
        try:
            _jp = CA._journal_path()
        except Exception:
            _jp = None
        if not (_jp and os.path.isfile(_jp)):
            self.skipTest("UNMEASURED, not a pass: this venue has no session journal, so 'the file "
                          "had not changed' cannot be established")
        CA._STATUS_JOURNAL_CACHE = None
        calls = {"n": 0}
        orig = CA._kai_journal_rows
        # ⚠⚠ v3215 — THIS TOOK NO ARGUMENTS, AND THE CALL SITE STARTED PASSING ONE.
        # v3208 made the status site call `_kai_journal_rows(want_why=True)`. This stub accepted
        # no kwargs, so every call raised TypeError INSIDE status_payload's broad `except
        # Exception`, the counter never moved, and `assertEqual(0, 0)` passed. The law went on
        # reporting success while measuring nothing at all — which is worse than the red one
        # above it, because nothing looked wrong. [[zero-needs-a-denominator]]
        def counted(*a, **kw):
            calls["n"] += 1
            return orig(*a, **kw)
        CA._kai_journal_rows = counted
        try:
            CA.status_payload()
            first = calls["n"]
            # ⚠ IF THE READER WAS NEVER CALLED, THIS LAW IS MEASURING NOTHING — say so rather
            # than compare 0 with 0 and call it a pass. That is exactly how it survived v3208.
            self.assertGreater(first, 0,
                               "status_payload never reached _kai_journal_rows at all, so "
                               "'walked once' is unmeasured — not satisfied")
            CA.status_payload()
            CA.status_payload()
        finally:
            CA._kai_journal_rows = orig
        self.assertEqual(
            calls["n"], first,
            "the journal was walked again on a poll where the file had not changed: %d walks for "
            "3 payloads. ⚠ This counts ALL 20 call sites, so `first` is the baseline and the only "
            "claim here is that the STATUS site adds nothing after the first." % calls["n"])

    def test_one_poll_walks_the_journal_once_for_all_three_readers(self):
        """REG-1824 — status_payload, _eyes_pulse and _receipts_stream each walked the WHOLE journal
        on the same poll whenever it had changed. MEASURED on a 50-row fixture: 3 whole-file opens
        per changed poll before (plus the reader lamp's 600 KB tail), 1 after. They share one read
        through _journal_read's per-poll memo, keyed on the file itself (ino, size, mtime_ns,
        ctime_ns), so an append or a chmod between polls is a new read, and a read that FAILED is
        never shared. A fixture journal; his is never opened."""
        import builtins
        import json
        import shutil
        import tempfile
        import control_app as CA
        d = tempfile.mkdtemp(prefix="poll1824_")
        self.addCleanup(shutil.rmtree, d, True)
        path = os.path.join(d, "sessions.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            for i in range(50):
                fh.write(json.dumps({"lane": "deep", "ts": i, "completedTs": i, "sessionId": "s1",
                                     "names": ["Canary %d" % i]}) + "\n")
        real = builtins.open
        opens = {"n": 0}

        def counting(f, *a, **k):
            mode = a[0] if a else k.get("mode", "r")
            if str(f) == path and "b" not in mode and "a" not in mode and "w" not in mode:
                opens["n"] += 1
            return real(f, *a, **k)

        saved = {k: CA.__dict__.get(k) for k in ("_STATUS_JOURNAL_CACHE", "_EYES_CACHE", "_RECEIPTS_CACHE")}
        old_env = os.environ.get("TV_SESSIONS")
        os.environ["TV_SESSIONS"] = path
        try:
            for k in saved:
                CA.__dict__.pop(k, None)
            builtins.open = counting
            try:
                st = CA.status_payload()
                first = opens["n"]
                opens["n"] = 0
                CA.status_payload()          # the file has not changed
                again = opens["n"]
            finally:
                builtins.open = real
        finally:
            if old_env is None:
                os.environ.pop("TV_SESSIONS", None)
            else:
                os.environ["TV_SESSIONS"] = old_env
            for k, v in saved.items():
                if v is None:
                    CA.__dict__.pop(k, None)
                else:
                    CA.__dict__[k] = v
        # all three readers did read it, or "once" is about nothing
        self.assertEqual((st.get("eyes") or {}).get("liveTs"), 49, st.get("eyes"))
        self.assertTrue(st.get("receipts"), "the receipts never read the fixture")
        self.assertEqual(st.get("journal"), {"read": True, "why": None})
        self.assertEqual(first, 1,
                         "one poll walked the whole journal %d times — the three readers stopped "
                         "sharing one read" % first)
        # ⚠ and the v2989 claim on a venue WITH a journal (this fixture), so it is measured on every
        # machine: test_two_payloads_walk_the_journal_once skips where there is no journal of his,
        # which left its own red-proof BLIND in every sandbox.
        self.assertEqual(again, 0,
                         "a poll over an UNCHANGED journal walked it %d time(s) — the status cache is "
                         "no longer keyed on the file" % again)
        self.assertIsNone(getattr(CA._JOURNAL_POLL, "memo", None),
                          "the poll's memo outlived the poll, so the next caller on this thread "
                          "would be served from it")


RED_PROOF = [
    {
        "why": "REG-1824 - the three status readers each walk the whole journal again on one poll",
        "file": "control_app.py",
        "find": "    _JOURNAL_POLL.memo = {}   # REG-1824",
        "replace": "    _JOURNAL_POLL.memo = None   # REG-1824",
        "matches": 1,
    },
    {
        "why": "REG-1824 - the poll's memo outlives the poll",
        "file": "control_app.py",
        "find": "    _JOURNAL_POLL.memo = None\n    return _out\n",
        "replace": "    return _out\n",
        "matches": 1,
    },
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
        # ⚠⚠ v3215 — RE-ANCHORED. This named the pre-v3208 call form and matched 0 times from
        # the moment the site became a lambda, so heart2 returned INVALID, revoked the standing
        # proof, and filed this gate as BLIND — while the law above it was also red. A gate can be
        # wrong in two independent ways at once, and neither was visible from the green tree.
        "find": '_t("journal", lambda: _kai_journal_rows(want_why=True))',
        "replace": "_kai_journal_rows(want_why=True)",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
