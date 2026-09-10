# -*- coding: utf-8 -*-
"""v2790 — THE v2228 FIX WAS NEVER SWEPT TO ITS SIBLING ELEVEN LINES AWAY.

v2228 bounded `await fetch('/api/sessions')` inside `thOpen()` with an AbortController and an 8s
timeout, and its comment states the failure exactly:

    "When the auto-relaunch replaces the server process mid-fetch, the promise never settles, the
     function never reaches the code that fills the stage, and the black stays up."

`thLoadSession()` — which `thOpen()` AWAITS — opened `/api/session?n=` with **no AbortController,
no timeout and no catch**. Identical shape, identical consequence, on the more expensive route:
`/api/session` defaults to `pack=debug` ("every fps frame + every AI read"), and this repo has
already measured its archive siblings at ~4s alone and **41.6s under contention**. [[sweep-dont-ask]]

=== ⚠⚠ THIS IS NOT WHAT HE WAS SEEING, AND SAYING SO MATTERS ===
A different model family put live eyes on his console on 2026-09-08 and **THE SHELF opened, painted
its reels, and stayed open past 15 seconds**. REG-708 as written is REFUTED; the empty overlay and
the 12s self-close were an artifact of a sandboxed console with no sessions and no film. This is a
latent hazard fixed on its merits. A fix sold as curing something it never caused is how the real
cause stops being looked for. [[unknown-stays-unknown]]

=== ⚠ WHY THIS LAW IS NARROW, AND WHY THAT IS THE POINT ===
Measured across the whole console UI: **71 `await fetch(` calls in code, 4 bounded, 67 not.**
Bounding all 67 would be a sweeping change to a hot path with no measurement behind it, and a law
that failed on 67 sites would be furniture on the day it shipped. What makes THIS chain different
is that a hang here leaves a BLACK STAGE with no account of it — every other call is a click-driven
panel load whose failure is visible and local. The law guards the chain, not the file.

=== ⚠ THE CENSUS ITSELF READ A COMMENT AS CODE, AND I ALMOST REPORTED THE WRONG NUMBER ===
First pass said 68 unbounded — because the fix's own comment QUOTES the defective line to explain
it, and a line-wise search counted the explanation. Comments are stripped before counting here.
Same trap, ~13th time this session. [[source-reading-guard]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

UI = os.path.join(HERE, "control_ui.html")
RAW = io.open(UI, encoding="utf-8").read()


def _strip_comments(t):
    """Blank out /* */ and // comments, preserving line numbering and string literals."""
    out, i, n = [], 0, len(t)
    while i < n:
        if t.startswith("/*", i):
            j = t.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append(re.sub(r"[^\n]", "", t[i:j]))
            i = j
        elif t.startswith("//", i):
            j = t.find("\n", i)
            j = n if j < 0 else j
            out.append("")
            i = j
        elif t[i] in "\"'":
            q = t[i]
            j = i + 1
            while j < n and t[j] != q:
                if t[j] == "\\":
                    j += 1
                j += 1
            out.append(t[i:j + 1])
            i = j + 1
        else:
            out.append(t[i])
            i += 1
    return "".join(out)


CODE = _strip_comments(RAW)
LINES = CODE.split("\n")


def _fetch_sites(lo, hi):
    """(lineno, bounded) for every `await fetch(` in CODE between lo and hi."""
    out = []
    for i, l in enumerate(LINES):
        ln = i + 1
        if not (lo <= ln <= hi) or "await fetch(" not in l:
            continue
        # THE CALL ITSELF MUST CARRY THE SIGNAL, not merely sit near a controller. A sabotage
        # that removed only `_sac ? { signal: _sac.signal } : undefined` from the fetch left the
        # AbortController and setTimeout lines untouched two rows above — and a context-window
        # check read that as bounded while the fetch was once again unstoppable. Presence near
        # is not wiring to. [[sabotage-is-usually-the-wrong-one]]
        ctx = "\n".join(LINES[max(0, ln - 10):ln + 2])
        near = "AbortController" in ctx and "setTimeout" in ctx
        wired = "signal" in l
        out.append((ln, near and wired))
    return out


def _span(name):
    """(first_line, last_line) of a function, by brace depth over the STRIPPED code."""
    i = CODE.find(name)
    if i < 0:
        return None
    start = CODE[:i].count("\n") + 1
    depth, j, seen = 0, CODE.find("{", i), False
    k = j
    while k < len(CODE):
        if CODE[k] == "{":
            depth += 1
            seen = True
        elif CODE[k] == "}":
            depth -= 1
            if seen and depth == 0:
                break
        k += 1
    return start, CODE[:k].count("\n") + 1


class TheTheatreOpenChainCannotHang(unittest.TestCase):

    def test_both_functions_are_still_there(self):
        """⚠ THE DENOMINATOR. If either moved, every law below inspects nothing.
        [[zero-needs-a-denominator]]"""
        self.assertIsNotNone(_span("async function thOpen(){"), "thOpen is gone")
        self.assertIsNotNone(_span("async function thLoadSession("), "thLoadSession is gone")

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────
    def test_every_fetch_thOpen_AWAITS_is_bounded(self):
        """★★★ A hang anywhere in this chain leaves a BLACK STAGE with no account of it — v2228's
        own words. thOpen awaits thLoadSession, so the chain is both functions, not just the one
        v2228 happened to fix."""
        bad = []
        for name in ("async function thOpen(){", "async function thLoadSession("):
            lo, hi = _span(name)
            for ln, ok in _fetch_sites(lo, hi):
                if not ok:
                    bad.append("%s line %d" % (name.strip("{"), ln))
        self.assertEqual(bad, [],
                         "an await on the theatre-open chain has no AbortController/timeout, so a "
                         "server replaced mid-fetch parks the promise forever and the stage stays "
                         "black with nothing said: %s" % ", ".join(bad))

    def test_the_chain_actually_HAS_awaited_fetches(self):
        """⛔ The law above passes trivially over zero sites. If the fetches ever move out of these
        functions, this must be re-pointed rather than left green over nothing."""
        total = 0
        for name in ("async function thOpen(){", "async function thLoadSession("):
            lo, hi = _span(name)
            total += len(_fetch_sites(lo, hi))
        self.assertGreaterEqual(total, 2,
                                "only %d awaited fetch(es) found on the theatre-open chain — the "
                                "calls moved and this law is measuring almost nothing" % total)

    def test_the_expensive_route_is_bounded_LOOSER_than_the_cheap_one(self):
        """⚠ /api/session defaults to pack=debug and this repo measured its siblings at 41.6s under
        contention. A bound copied from the lighter /api/sessions would abort reads that were only
        slow — turning a latency problem into a failure. The heavier route must have the larger
        budget."""
        # THE CLASS `[^;]*?` COULD NEVER MATCH, AND THE LAW FAILED ON CORRECT CODE. The
        # real call is setTimeout(function(){ try { _sac && _sac.abort(); } catch(e){} },
        # 12000) — its callback body CONTAINS semicolons, so a class excluding ";" cannot
        # reach the delay argument. Third instrument fault on this one law: an off-by-one
        # slice, a comment counted as code, and a regex that could not match what it was
        # written for. Measure the instrument before blaming the subject.
        # [[feedback-suspect-the-instrument]] [[source-reading-guard]]
        m = re.findall(r"setTimeout\([^\n]*?,\s*(\d{3,6})\)", CODE)
        self.assertTrue(m, "no timeout literals found on the chain at all")
        lo, hi = _span("async function thLoadSession(")
        # ⚠ lo/hi are 1-BASED line numbers; LINES is 0-based. The first cut sliced
        # LINES[lo:hi], which drops the opening line and ends one short — the timeout
        # literal fell outside the window and the law failed on correct code.
        # [[source-window-shortcut]] [[feedback-suspect-the-instrument]]
        seg = "\n".join(LINES[lo - 1:hi])
        got = re.findall(r"setTimeout\([^\n]*?,\s*(\d{3,6})\)", seg)
        self.assertTrue(got, "thLoadSession has no timeout literal")
        self.assertGreaterEqual(int(got[0]), 12000,
                                "the reel read is bounded at %sms — tighter than the ~4s-to-41.6s "
                                "this repo measured for the archive routes, so a merely slow read "
                                "would be aborted" % got[0])

    # ── ⛔ THE FAILURE MUST SPEAK ────────────────────────────────────────────────────────────
    def test_a_timed_out_reel_SAYS_so(self):
        """⛔ v2228's whole complaint was "a black rectangle and no account of it". Bounding the
        wait without reporting it would swap a hang for a silent empty stage."""
        # SCOPE IT TO THE CATCH. `th-caption` appears elsewhere in this function (the j.error
        # branch), so asserting it is merely PRESENT stayed green when the timeout's own reporting
        # was deleted outright. Fourth time today a law read presence instead of behaviour.
        lo, hi = _span("async function thLoadSession(")
        seg = "\n".join(LINES[lo - 1:hi])
        i = seg.find("catch (_se)")
        self.assertGreater(i, 0,
                           "the reel read has no catch arm at all — a rejected fetch now throws "
                           "out of thLoadSession and thOpen never finishes")
        # A FIXED-SIZE WINDOW READS PAST THE REGION, and that is exactly what happened: `seg[i:
        # i+600]` ran off the end of a short catch body into the `j.error` branch below, which ALSO
        # writes th-caption — so deleting the timeout's own reporting stayed green. Walk the braces
        # to the catch's real end instead of guessing a length. [[source-window-shortcut]]
        depth, k, opened = 0, seg.find("{", i), False
        j2 = k
        while j2 < len(seg):
            if seg[j2] == "{":
                depth += 1
                opened = True
            elif seg[j2] == "}":
                depth -= 1
                if opened and depth == 0:
                    break
            j2 += 1
        arm = seg[i:j2 + 1]
        self.assertIn("th-caption", arm,
                      "the timeout CATCH writes nothing to the caption, so a timed-out reel is "
                      "indistinguishable from an empty one — v2228's exact complaint, which was "
                      "'a black rectangle and no account of it'")


RED_PROOF = [
    {
        'why': 'thOpen() AWAITS thLoadSession(), whose /api/session?n= read is the theatre-open chain\'s more expensive hop (pack=debug). v2790 bounded it with an AbortController + a 12s timeout and WIRED the controller into the call via `_sac ? { signal: _sac.signal } : undefined`. This tamper unwires exactly that — the AbortController and setTimeout lines stay two rows above, untouched, so the code still LOOKS bounded — while the fetch itself is once again unstoppable: a server replaced mid-fetch parks the promise forever and the stage stays black with nothing said. It is the precise sabotage the law\'s own comment says a context-window check would have read as green ("presence near is not wiring to"), so it exercises the `wired = "signal" in l` half of the law rather than the `near` half.  MEASURED: untampered GREEN — `python3 tv/test_the_theatre_open_chain_cannot_hang.py` ran 5 tests, OK (exit 0), ; tampered (all 1) RED — full gate: FAILED (failures=1), only test_every_fetch_thOpen_AWAITS_is_bounded faili; reddened law test_every_fetch_thOpen_AWAITS_is_bounded; ALONE FAILS ALONE — 1 test run, 1 failure, identical message to the full-suite run..',
        'file': 'control_ui.html',
        'find': ', _sac ? { signal: _sac.signal } : undefined',
        'replace': ', undefined',
        'matches': 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
