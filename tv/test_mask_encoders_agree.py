#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""THE TESTED ENCODER IS NOT THE USED ENCODER.

⚠⚠ THE DEFECT, measured 2026-09-05, closing B-84's surviving half.

There are TWO implementations of one job — turning "which of this roster do I own" into a base64url
bit mask for the wire — and only one of them runs in production:

  · `fleet_mask.encode()` — Python. Round-trip tested against `fleet_mask.decode()` in
    `test_fleet_mask.py`. **AST-measured: ZERO production callers.** `control_app` uses only
    `ledger_spec`, `load_roster_for`, `sanitize_for_wire`, `compare` and `LEDGERS`; `encode`,
    `decode`, `load_roster` and `roster_fingerprint` are never reached outside tests.
  · an INLINE JS SNIPPET built as a string inside `control_app.board_mask()` and run in the board
    window via `_ejs`. **This is the one that produces every mask that has ever gone on the wire.**

So the suite proves a pair — encode↔decode — that never runs together in production, while the code
that does run has no test of its own. That is [[feedback-blind-fixture-green-gate]] at its purest: a
green suite about code that is not the code that runs. [[copy-drift]] §7 — a routine that exists
twice, and a law that lands in one copy is not a law.

⚠ I BRIEFLY GOT THIS WRONG AND THE CORRECTION IS WORTH KEEPING. B-84's note said the mask is
"built in JS inside the board". I grepped `bible.html` (6.2 MB), found ZERO occurrences of
`fleetMask`/`maskEncode`/anything similar, and called the explanation refuted. It is not: the JS is
real, it is simply EMBEDDED IN PYTHON as a string literal rather than living in a .html file. An
absence found by searching the wrong artifact is not an absence. [[source-reading-guard]]

WHAT THIS PROVES: that the two encoders produce byte-identical output for the same input. Not that
either is correct — that both agree, which is the property that silently rots when one is edited.

⚠ NOTHING HERE TOUCHES HIS BOARD. The JS is executed against a synthetic `localStorage` in a
throwaway headless page; `board_mask` is never called and the live board window is never opened.
"""
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import fleet_mask as FM  # noqa: E402


def _inline_js_source():
    """The EXACT js string `board_mask` builds, lifted from the shipped source. -> str | None

    ⚠ IT IS READ FROM `board_mask` ITSELF, never re-typed here. A copy of the snippet in this file
    would make the test pass while the production snippet drifted — the very defect being guarded.
    """
    import ast
    import inspect
    import textwrap
    import control_app as ca
    # ⚠⚠ AST, NOT A REGEX OVER SOURCE TEXT — and this cost two rounds to learn. Matching quoted
    # runs returns the RAW SOURCE between quotes, so `\\+` inside the js regex literals stays
    # double-escaped and the snippet dies with "g is not defined". `ast.literal_eval` on the
    # concatenated constant yields the string Python actually builds, escapes resolved.
    # ⚠ `%%` survives literal_eval as `%%` and is collapsed by the `%` substitution below, exactly
    # as it is in production. Collapsing it here instead breaks the format string — my first cut
    # spent five ERRORs proving that too. [[source-reading-guard]]
    try:
        tree = ast.parse(textwrap.dedent(inspect.getsource(ca.board_mask)))
    except Exception:
        return None
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and node.targets
                and getattr(node.targets[0], "id", None) == "js"
                and isinstance(node.value, ast.BinOp) and isinstance(node.value.op, ast.Mod)):
            try:
                return ast.literal_eval(node.value.left)
            except Exception:
                return None
    return None


class ThereReallyAreTwoEncoders(unittest.TestCase):
    """The premise. If either half of this stops being true the guard below is measuring nothing."""

    def test_the_python_encoder_has_no_production_caller(self):
        import ast
        import io
        used = set()
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        for node in ast.walk(ast.parse(src)):
            if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                    and node.value.id in ("_fm", "fleet_mask")):
                used.add(node.attr)
        self.assertNotIn("encode", used,
                         "control_app now calls fleet_mask.encode — if the production path uses "
                         "the Python encoder, this whole guard is obsolete and should be retired "
                         "rather than left reporting clean")

    def test_the_inline_js_is_reachable_from_the_shipped_source(self):
        js = _inline_js_source()
        self.assertIsNotNone(js, "board_mask's js literal could not be lifted — the extraction "
                                 "anchor moved, and a guard that cannot find its subject must "
                                 "REFUSE, not pass")
        # ⚠ the PRE-substitution form: `%%` is still doubled until board_mask's `%` runs
        for token in ("btoa", "1<<(j%%8)", "String.fromCharCode"):
            self.assertIn(token, js, "the lifted snippet is missing %r — wrong region" % token)


class TheTwoEncodersAgreeByteForByte(unittest.TestCase):
    """★★ THE JOIN. Run the SHIPPED js against a synthetic store and compare to Python."""

    ROSTER = ["Item %02d" % i for i in range(37)]      # not a multiple of 8, on purpose
    FP = "abc123def456"
    _url = None
    _proc = None
    _probe_seq = [0]

    def _probe_n(self):
        self._probe_seq[0] += 1
        return self._probe_seq[0]

    @classmethod
    def setUpClass(cls):
        """⚠ A REAL HTTP ORIGIN IS REQUIRED, and `about:blank` is not one. My first cut opened
        about:blank and every case failed with "Access is denied for this document" — an OPAQUE
        origin has no localStorage, and the shipped snippet reads localStorage by design. The
        throwaway console server gives a real origin on a scratch port; nothing here touches his
        console on :17772 or his board's storage. [[borrowed-surface]]"""
        try:
            import render_check as RC
        except Exception:
            return
        if not RC._chrome_up():
            return
        try:
            cls._url, cls._proc = RC._serve_console()
        except Exception:
            cls._url, cls._proc = None, None

    @classmethod
    def tearDownClass(cls):
        if cls._proc is not None:
            try:
                cls._proc.terminate()
            except Exception:
                pass

    def _js_mask(self, owned):
        """Execute the shipped snippet in headless Chrome. -> dict | None (None = could not ask)"""
        try:
            import render_check as RC
        except Exception:
            return None
        if not RC._chrome_up() or not self._url:
            return None
        js = _inline_js_source()
        if js is None:
            return None
        # ⚠⚠ A UNIQUE KEY PER CALL, AND THIS NEARLY BECAME A FALSE FINDING. Every case shares one
        # origin and therefore one localStorage, and the served page carries a `window.LSR` wrapper
        # which the shipped snippet PREFERS over raw localStorage. With a fixed key, the write from
        # one case was still being read by the next: `test_owning_EVERYTHING` came back with
        # [0,1,7,8,9,31,36] — exactly the PREVIOUS test's input — and reported it as the two
        # encoders disagreeing. Decoding both masks is what exposed it; the bare inequality looked
        # like a real defect. State shared between cases is an instrument fault.
        # [[feedback-suspect-the-instrument]]
        key = "d2r_probe_store_%d" % (self._probe_n(),)
        body = js % (json.dumps(self.ROSTER), json.dumps(key))
        tab = None
        try:
            tab = RC._Tab(self._url)
            # write through BOTH doors: the snippet reads LSR when the page defines it, and raw
            # localStorage otherwise, so a fixture that writes only one can read the other's stale
            # value without ever saying so.
            tab.ev("localStorage.setItem(%s, %s); if (window.LSR && window.LSR.setItem) "
                   "window.LSR.setItem(%s, %s);"
                   % (json.dumps(key), json.dumps(json.dumps(owned)),
                      json.dumps(key), json.dumps(json.dumps(owned))))
            raw = tab.ev(body)
            return json.loads(raw) if raw else None
        except Exception as exc:
            # ⚠⚠ A HARNESS BUG IS NOT "COULD NOT ASK". My first cut returned None here, and a
            # TypeError in MY OWN format string became five silent skips — a broken guard wearing
            # the clothes of an unavailable one. Transport problems make the caller skip; anything
            # else RAISES. [[feedback-blind-fixture-green-gate]]
            raise AssertionError("the js encoder harness itself failed (%s: %s) — this is a broken "
                                 "guard, not an unavailable one"
                                 % (type(exc).__name__, str(exc)[:160]))
        finally:
            if tab is not None:
                try:
                    tab.close()
                except Exception:
                    pass

    def _compare(self, owned):
        py = FM.encode(owned, self.ROSTER, self.FP)
        self.assertIsNotNone(py, "the python encoder refused a legitimate input")
        js = self._js_mask(owned)
        if js is None:
            self.skipTest("no headless Chrome, so the js encoder could not be run — a skip is NOT "
                          "a pass, and this guard has established nothing on this machine")
        self.assertTrue(js.get("ok"), "the js encoder refused: %s" % js.get("why"))
        self.assertEqual(js["b"], py["b"],
                         "THE TWO ENCODERS DISAGREE on the bytes. js=%r python=%r — a mask on the "
                         "wire would not decode to what this machine owns" % (js.get("b"), py["b"]))
        self.assertEqual(js["have"], py["have"], "the two encoders disagree on the COUNT")
        self.assertEqual(js["n"], py["n"], "the two encoders disagree on the roster length")

    def test_a_typical_ownership_set(self):
        self._compare([self.ROSTER[i] for i in (0, 1, 7, 8, 9, 31, 36)])

    def test_owning_NOTHING(self):
        self._compare([])

    def test_owning_EVERYTHING(self):
        self._compare(list(self.ROSTER))

    def test_the_BYTE_BOUNDARY_bits(self):
        """⚠ Bit 7 and bit 8 are where an LSB/MSB disagreement first shows, and bit 36 is the
        partial last byte. An encoder pair can agree on every other input and differ here."""
        self._compare([self.ROSTER[7], self.ROSTER[8], self.ROSTER[36]])

    def test_a_name_NOT_in_the_roster_is_ignored_by_both(self):
        self._compare([self.ROSTER[3], "Not A Real Item"])


class TheGuardCanFail(unittest.TestCase):
    """⚠ A comparison that would pass whatever the js produced is not a comparison."""

    def test_a_perturbed_python_mask_would_not_match(self):
        roster = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]
        a = FM.encode(["A", "I"], roster, "fp")
        b = FM.encode(["B", "I"], roster, "fp")
        self.assertIsNotNone(a)
        self.assertNotEqual(a["b"], b["b"],
                            "two different ownership sets encode identically — the comparison "
                            "above could not detect a real disagreement")

    def test_the_extraction_returns_None_rather_than_a_wrong_snippet(self):
        """If the anchor moves, `_inline_js_source` must answer None so the test SKIPS loudly
        rather than comparing against something it happened to match."""
        import inspect
        src = inspect.getsource(_inline_js_source)
        self.assertIn("return None", src)


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
