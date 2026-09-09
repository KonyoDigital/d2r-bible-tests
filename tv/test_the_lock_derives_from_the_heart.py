#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""♥🔒 A SURFACE MAY NOT ARM ITSELF WHILE ITS INSTRUMENTS ARE BLIND.

Konyo, 2026-09-09: *"the lock and everything still derives from the heart and visually seen"*.
MEASURED when he asked: `self_arming.py` and `hover_wilson.py` held ZERO references to heart2. The
Wilson lock and the heart were two systems that never spoke, so a surface could reach its bar and
ARM ITSELF while the gates that would catch its failure were dark — the lock proving the surface
works, with nothing left able to prove the PROOF works.

A Wilson score says "this refused every attack we made". It cannot say "and we would have noticed
if it had not". That second question is the heart's, and it belongs in the same precondition chain
as the upstream check `may()` already runs: proving a surface in isolation proves nothing about what
feeds it, and an instrument that cannot go red is exactly that kind of missing prerequisite.
[[the-unjoined-end]] [[join-gate-heart]]

MEASURED after the join, on the real lock:
    1 BLIND instrument   -> may(printer.stream) False
    unreadable census    -> False   ("UNKNOWN fails CLOSED")
    absent census        -> False
    restored             -> True    (so it is a gate, not furniture)
"""
import ast
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import console_safe  # noqa: E402  — this file prints ♥ 🔒 ⚠ ★
console_safe.enable()

import self_arming as SA  # noqa: E402
import heart2 as H  # noqa: E402

STATE = os.path.join(H.HERE, ".heart2.json")


class _Census(object):
    """Swap the heart's census for the duration of one law, and always put it back."""

    def __init__(self, payload):
        self.payload = payload
        self.bak = None

    def __enter__(self):
        if os.path.exists(STATE):
            self.bak = STATE + ".lawtest"
            shutil.copy(STATE, self.bak)
        if self.payload is None:
            if os.path.exists(STATE):
                os.unlink(STATE)
        else:
            io.open(STATE, "w", encoding="utf-8").write(self.payload)
        return self

    def __exit__(self, *a):
        if self.bak and os.path.exists(self.bak):
            shutil.move(self.bak, STATE)
        elif os.path.exists(STATE) and not self.bak:
            os.unlink(STATE)
        return False


def _real_census():
    return io.open(STATE, encoding="utf-8").read() if os.path.exists(STATE) else None


RED_PROOF = [
    {
        "why": "un-asking the heart returns the lock to what it was — a surface that can arm itself "
               "while the gates that would catch its failure are blind",
        "file": "self_arming.py",
        "find": "    _hok, _hwhy = _heart_says_watched()\n    if not _hok:\n        return False, _hwhy",
        "replace": "    _hok, _hwhy = _heart_says_watched()",
        "matches": 1,
    },
    {
        "why": "letting a BLIND instrument pass is the defect itself: the lock arming on a Wilson "
               "score while nothing can prove the proof still works",
        "file": "self_arming.py",
        "find": "    if _blind:",
        "replace": "    if False and _blind:",
        "matches": 1,
    },
    {
        "why": "removing the staleness refusal lets a census from before the gates changed read as "
               "authoritative — a proof that no longer speaks for the instruments on disk",
        "file": "self_arming.py",
        "find": "    if _have != _want:",
        "replace": "    if False and _have != _want:",
        "matches": 1,
    },
]


def _skip_if_stale(case):
    """Editing ANY gate file changes the fingerprint and makes the live census stale — including
    edits to THIS file, which is itself a gate. That refusal is CORRECT and has its own law below;
    it must not make every other law here fail. Measured: saving this file turned 3 laws red for no
    reason but the save. [[feedback-blind-fixture-green-gate]]"""
    ok, why = SA._heart_says_watched()
    if not ok and "STALE" in (why or ""):
        case.skipTest("live census is stale (gates changed since the last prove) — re-prove first")


class TheLockDerivesFromTheHeart(unittest.TestCase):

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────
    def test_a_BLIND_instrument_closes_the_lock(self):
        """★★ The whole join. A dark gate is a missing prerequisite, not a detail."""
        _skip_if_stale(self)
        real = _real_census()
        if real is None:
            self.skipTest("no census on this machine — UNMEASURED, not a failure")
        st = json.loads(real)
        st["blind"] = ["test_an_instrument_that_cannot_go_red"]
        with _Census(json.dumps(st)):
            ok, why = SA.may("printer.stream")
        self.assertFalse(ok, "a lock armed itself while an instrument was BLIND — the Wilson score "
                             "proved the surface and nothing was left to prove the proof")
        self.assertIn("BLIND", why)

    def test_an_UNREADABLE_census_fails_CLOSED(self):
        """★★ Matching _rows(): UNKNOWN never arms anything."""
        if _real_census() is None:
            self.skipTest("no census on this machine")
        with _Census("{ this is not json"):
            ok, why = SA.may("printer.stream")
        self.assertFalse(ok, "an unreadable heart census permitted a lock to act")
        self.assertIn("CLOSED", why)

    def test_an_ABSENT_census_fails_CLOSED(self):
        """★ Never run here is not the same as nothing wrong here."""
        if _real_census() is None:
            self.skipTest("no census on this machine")
        with _Census(None):
            ok, why = SA.may("printer.stream")
        self.assertFalse(ok, "a missing heart census permitted a lock to act")
        self.assertIn("CLOSED", why)

    def test_it_is_a_GATE_not_furniture(self):
        """★★ A check that can only say no would be switched off within a week.
        With the real census — 0 blind today — at least one declared lock must still be able to
        act, or this law has proved nothing except that it can refuse. [[feedback-blind-fixture-green-gate]]"""
        if _real_census() is None:
            self.skipTest("no census on this machine")
        # ⚠ STALENESS IS A DIFFERENT, CORRECT REFUSAL. Editing ANY gate file makes the census stale
        # and closes every lock until a re-prove — including edits to THIS file, which is itself a
        # gate. That is the rule working, not furniture, so skip rather than fail: measured when
        # this law first ran and reported 3 failures purely because I had just saved it.
        _skip_if_stale(self)
        opened = [k for k in list(SA.LOCKS) + list(SA.ROUTES) if SA.may(k)[0]]
        self.assertTrue(
            opened,
            "with a healthy heart NOT ONE surface may act. Either every lock is genuinely shut, or "
            "this join refuses unconditionally — and a gate that can only say no is furniture.")

    def test_the_heart_check_runs_BEFORE_the_score(self):
        """★ Order matters: a blind instrument must be reported as the reason, not a Wilson number."""
        _skip_if_stale(self)
        real = _real_census()
        if real is None:
            self.skipTest("no census on this machine")
        st = json.loads(real)
        st["blind"] = ["test_dark"]
        with _Census(json.dumps(st)):
            _, why = SA.may("vault.apply")          # a lock that is ALSO blocked upstream
        self.assertIn("BLIND", why,
                      "a blind heart was masked by another refusal — he would read the downstream "
                      "reason and never learn the instruments were dark: %r" % why)


    def test_a_STALE_census_closes_the_lock(self):
        """★★ v2862 — a cross-family review: "the file still exists with blind=[], so may() returns
        true and a surface can arm itself even though no live supervision has run since".

        ⚠⚠ AND THE FIRST CUT OF THIS RULE USED MTIME, WHICH THE SANDBOX REFUTED. safe_copy, a git
        checkout, CI and the Windows machine all stamp fresh mtimes, so every gate read as newer
        than the census, every lock closed, and --prove reported this very gate UNPROVABLE because
        it was already red in its own copy. A rule that only holds in the tree that wrote it is not
        a rule. The bar is a CONTENT fingerprint, which survives copying. [[stale-reading]]"""
        real = _real_census()
        if real is None:
            self.skipTest("no census on this machine")
        st = json.loads(real)
        st["gatesFingerprint"] = "0" * 32          # a census proved against DIFFERENT instruments
        with _Census(json.dumps(st)):
            ok, why = SA._heart_says_watched()
            locked, lwhy = SA.may("printer.stream")
        self.assertFalse(ok, "a census whose fingerprint does not match the gates on disk still "
                             "read as authoritative")
        self.assertIn("STALE", why)
        self.assertFalse(locked, "the lock armed on a stale census")
        self.assertIn("STALE", lwhy)

    def test_the_staleness_bar_is_CONTENT_not_mtime(self):
        """★★ The portability law. Touching a gate file must NOT make the census stale; changing
        one MUST. Copying a repo resets mtimes, so an mtime rule closes every lock on every fresh
        checkout — which is how the sandbox caught it."""
        _skip_if_stale(self)
        import time
        gates = H.gate_files()
        if not gates or _real_census() is None:
            self.skipTest("no gates or no census on this machine")
        name, path = gates[0]
        st = os.stat(path)
        os.utime(path, (st.st_atime, time.time() + 5))     # mtime only, content untouched
        try:
            ok, why = SA._heart_says_watched()
        finally:
            os.utime(path, (st.st_atime, st.st_mtime))
        self.assertTrue(
            ok, "a TOUCHED gate file (mtime moved, content identical) made the census read as "
                "stale: %r. That rule closes every lock on any copied tree — safe_copy, CI, a "
                "fresh checkout — and it is why the sandbox reported this gate UNPROVABLE." % why)

    def test_the_permit_reason_carries_the_COVERAGE(self):
        """★ blind=[] with 12 of 47 proved means almost nothing was exercised. That is not gated —
        picking a ratio bar would be inventing a law — but it must never be INVISIBLE."""
        _skip_if_stale(self)
        ok, why = SA._heart_says_watched()
        if not ok:
            self.skipTest("the heart is not currently permitting — nothing to read")
        self.assertIn("proved", why,
                      "the permit says the instruments are watched and does not say how much was "
                      "actually proved: %r" % why)

    def test_an_UNREADABLE_gate_does_not_hash_like_an_EMPTY_one(self):
        """★★ v2864 — a cross-family review found the collapse: _read_text returns None for an
        unreadable file and the digest folded that in as "", so EVERY unreadable file hashed
        identically to every empty one. The set of readable gates could change while the
        fingerprint held still, and the lock would call a stale proof current.
        [[unknown-stays-unknown]]"""
        import tempfile, shutil
        d = tempfile.mkdtemp(prefix="fp.")
        a = os.path.join(d, "a.py"); b = os.path.join(d, "b.py")
        io.open(a, "w").write(""); io.open(b, "w").write("")
        try:
            empty = H.gates_fingerprint([("g", a), ("h", b)])
            os.chmod(a, 0); os.chmod(b, 0)
            # ⚠⚠ chmod 0 DOES NOT MAKE A FILE UNREADABLE FOR ROOT, for a uid with
            # CAP_DAC_OVERRIDE, or on a filesystem that ignores mode bits — a cross-family review
            # raised it and it is right: the UNREADABLE branch would never be taken, src would be
            # "" not None, and this law would FAIL on such a machine while proving nothing on any
            # other. Measure whether the premise actually holds before asserting on it.
            # [[zero-needs-a-denominator]]
            if H._read_text(a) is not None:
                self.skipTest("chmod 0 did not make the file unreadable here (root, or a "
                              "filesystem that ignores mode bits) — the case this law is about "
                              "cannot be produced on this machine. UNMEASURED, not passing.")
            unread = H.gates_fingerprint([("g", a), ("h", b)])
            swapped = H.gates_fingerprint([("g", b), ("h", a)])
        finally:
            os.chmod(a, 0o644); os.chmod(b, 0o644); shutil.rmtree(d, ignore_errors=True)
        self.assertNotEqual(empty, unread,
                            "two UNREADABLE gate files hash the same as two EMPTY ones — the "
                            "fingerprint cannot tell 'I could not read it' from 'there was nothing "
                            "in it'")
        self.assertNotEqual(unread, swapped,
                            "two DIFFERENT unreadable files hash identically — the path is not in "
                            "the sentinel, so which instrument went dark is invisible")

    def test_the_fingerprint_covers_the_PROVER_too(self):
        """★★ Same review: the digest covered gate FILES only, so a change to gate_files(), to how
        the sabotage is injected, or to any decision heart2 makes about RED left it identical — and
        the lock would still call that proof current. A proof is only as true as the thing that
        produced it. [[the-unjoined-end]]

        ⚠⚠ THIS ASSERTED THE STRING "heart2.py" APPEARED IN THE FUNCTION SOURCE, and the same
        reviewer called it: that passes even if the fold is deleted, commented out, or put behind a
        flag nobody sets. The FIFTH time this session I wrote a law that checks a name instead of an
        act. It now changes what the prover READS and requires the digest to move.
        [[sabotage-is-usually-the-wrong-one]]"""
        import tempfile, shutil
        d = tempfile.mkdtemp(prefix="pv.")
        g = os.path.join(d, "g.py")
        io.open(g, "w", encoding="utf-8").write("# a gate\n")
        gates = [("g", g)]
        real = H._read_text
        try:
            before = H.gates_fingerprint(gates)
            # make ONLY the prover's own source read differently; the gate list is untouched
            def _fake(path):
                if os.path.basename(path) == "heart2.py":
                    return (real(path) or "") + "\n# the prover changed\n"
                return real(path)
            H._read_text = _fake
            after = H.gates_fingerprint(gates)
        finally:
            H._read_text = real
            shutil.rmtree(d, ignore_errors=True)
        self.assertNotEqual(
            before, after,
            "changing heart2.py's OWN source left the fingerprint identical (%s), so a change to "
            "the prover — how gates are found, how the tamper is applied, what counts as RED — "
            "does not invalidate the census and a stale proof reads as current" % before[:12])

if __name__ == "__main__":
    unittest.main(verbosity=2)
