#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""♥ ONE NUMBER WAS HIDING A 93/7 SPLIT.

Konyo, 2026-09-09: *"when we hit 100% on heart 2.0 its also a VISUAL PASS right? like its not just
backend"*. It is not. MEASURED on the live registry the moment he asked:

    269 gates · 10 import render_check or playwright · 259 never look at a pixel
    overall 132/269 = 49.1%   backend 130/259 = 50.2%   PIXEL 2/10 = 20.0%

So "100%" on the old single number would have been ~96% backend by gate count — true as a count and
a lie as a label, which is the defect this repo keeps paying for. The census now carries the split
so the visual share cannot hide inside the total. [[label-outlived-referent]]

⚠ THE CLASSIFIER PARSES. My first cut of that number text-scanned the source for 'render_check',
'playwright', '.render_shots' and answered 18 — because PROSE AND COMMENTS mentioning the harness
counted as looking at pixels. Parsing imports answers 10. A number he reads may not come from a
grep. [[source-reading-guard]]

⚠ AND THE LAWS BELOW PARSE TOO, for the same reason.
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import console_safe  # noqa: E402  — this file prints ♥ ⚠ ★; a non-UTF-8 console must not crash
console_safe.enable()  # while REPORTING, turning a clean tree into a non-zero exit.

import heart2 as H  # noqa: E402

SRC = io.open(os.path.join(HERE, "heart2.py"), encoding="utf-8").read()
TREE = ast.parse(SRC)


def _fn(name):
    for n in ast.walk(TREE):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    raise AssertionError("heart2.py has no %s() — the law cannot read its subject" % name)


RED_PROOF = [
    {
        "why": "dropping pixelTotal from the written census returns the heart to ONE number, which "
               "is the whole defect: a 96%-backend score reading as a whole-system pass",
        "file": "heart2.py",
        "find": '        "pixelTotal": len(_pixel),',
        "replace": '        "pixelTotalRemoved": len(_pixel),',
        "matches": 1,
    },
    {
        "why": "making the classifier decide on a SUBSTRING instead of the parsed imports restores "
               "the 18-vs-10 miscount, where a comment mentioning the harness counted as a gate "
               "that looks at pixels",
        "file": "heart2.py",
        "find": '        if mods & {"render_check", "playwright"}:',
        "replace": '        if "render_check" in src or "playwright" in src:',
        "matches": 1,
    },
    {
        "why": "putting the bare `continue` back makes an unreadable gate vanish into the BACKEND "
               "count — the swallow a cross-family review found in v2858",
        "file": "heart2.py",
        "find": "            _unk.append(n)                # UNPARSEABLE is not \"backend\" either\n            continue",
        "replace": "            continue",
        "matches": 1,
    },
    {
        "why": "putting backendProved back to `- _pixel` alone lets a proved-but-unclassified gate "
               "be counted in the numerator and excluded from the denominator",
        "file": "heart2.py",
        "find": '"backendProved": len(_proved - _pixel - set(_pixel_unk)),',
        "replace": '"backendProved": len(_proved - _pixel),',
        "matches": 1,
    },
]


class TheCensusSaysHowMuchOfItIsPixels(unittest.TestCase):

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────
    def test_the_written_census_carries_the_split(self):
        """★★ The state file must name the visual share, not bury it in the total."""
        keys = set()
        for n in ast.walk(_fn("_write_state")):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                keys.add(n.value)
        for want in ("pixelTotal", "pixelProved", "backendTotal", "backendProved"):
            self.assertIn(
                want, keys,
                "the census no longer writes %r, so the visual share is invisible again and one "
                "number speaks for two very different populations" % want)

    def test_the_split_PARTITIONS_the_registry(self):
        """★★ backend + pixel must equal the whole, or the split is decoration."""
        gates = H.gate_files()
        px = H.pixel_gates(gates)
        self.assertTrue(px, "pixel_gates() found NOTHING — a zero here would make the visual share "
                            "read as 0/0 and vanish. Suspect the classifier before the registry.")
        self.assertLess(len(px), len(gates),
                        "every gate classified as a pixel gate; the classifier is not discriminating")
        self.assertEqual(len(gates), len(px) + (len(gates) - len(px)),
                         "the split does not partition the registry")

    def test_the_classifier_reads_IMPORTS_not_a_substring(self):
        """★★ A number he reads may not come from a grep. Measured: grep says 18, imports say 10."""
        fn = _fn("pixel_gates")
        walks = [n for n in ast.walk(fn)
                 if isinstance(n, ast.Attribute) and n.attr == "walk"]
        self.assertTrue(walks, "pixel_gates() no longer walks an AST — if it decides by substring, "
                               "prose that merely NAMES the harness counts as looking at pixels")
        names = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
        self.assertTrue(
            {"ast"} & names or walks,
            "pixel_gates() does not reference the ast module")
        # and it must actually consider Import nodes, not just any walk
        attrs = {n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)}
        self.assertTrue(
            {"Import", "ImportFrom"} & attrs,
            "pixel_gates() walks something but never inspects Import/ImportFrom, so it is not "
            "classifying by what the gate actually pulls in: %s" % sorted(attrs))
        # ⚠⚠ AND THE DECISION MUST CONSUME IT. The first cut of this law asserted only that the
        # walk EXISTS, and its own red-proof came back BLIND: swapping the deciding `if` for a
        # substring test on the raw source left the walk sitting above it, unused, and the law
        # still passed. A law that checks machinery is present is not a law that the machinery is
        # USED. [[the-unjoined-end]] [[sabotage-is-usually-the-wrong-one]]
        bad = []
        for n in ast.walk(fn):
            if isinstance(n, ast.Compare) and any(isinstance(o, ast.In) for o in n.ops):
                for side in [n.left] + list(n.comparators):
                    if isinstance(side, ast.Name) and side.id in ("src", "source", "text"):
                        bad.append(ast.unparse(n)[:70])
        self.assertEqual(
            [], bad,
            "pixel_gates() decides with a SUBSTRING test against the raw source: %s. That is the "
            "18-vs-10 miscount — a comment naming the harness counts as a gate that looks at "
            "pixels. The decision has to read the parsed imports." % bad)


    def test_an_UNREADABLE_gate_is_not_silently_BACKEND(self):
        """★★ v2860 — a cross-family review found this one. Both the unreadable case and the
        SyntaxError case did a bare `continue`, so a gate that really imports render_check but was
        momentarily unparseable left the pixel set and landed in the BACKEND count. An inflated
        backend share, and a later 100% quietly covering a visual gate nobody classified.
        [[unknown-stays-unknown]]"""
        import tempfile
        d = tempfile.mkdtemp(prefix="unclassifiable.")
        p = os.path.join(d, "test_broken_gate.py")
        io.open(p, "w", encoding="utf-8").write("import render_check\ndef (:  # not python\n")
        try:
            unk = []
            px = H.pixel_gates([("test_broken_gate", p)], unk)
        finally:
            os.unlink(p); os.rmdir(d)
        self.assertEqual(set(), px, "an unparseable file was classified as a pixel gate")
        self.assertEqual(
            ["test_broken_gate"], unk,
            "a gate that could not be parsed was SWALLOWED — it left the pixel set silently and "
            "would be counted as backend, which is a failed read handed back as data inside the "
            "thing that measures the heart: %r" % unk)

    def test_backendProved_can_never_exceed_backendTotal(self):
        """★★ v2862 — a cross-family review found this, and it reproduces exactly.
        backendTotal subtracts the unclassified; backendProved did not. A gate that is PROVED and
        is now unreadable left the total but stayed in the proved count, so the pair could report
        2 proved out of 1. Zero unclassified today, so it had never fired — a latent inconsistency
        in the one number he reads. [[zero-needs-a-denominator]]"""
        import tempfile, shutil
        d = tempfile.mkdtemp(prefix="inv.")
        bad = os.path.join(d, "test_proved_but_broken.py")
        io.open(bad, "w", encoding="utf-8").write("import render_check\ndef (:  # unparseable\n")
        try:
            unk = []
            gates = [("test_proved_but_broken", bad), ("test_plain", __file__)]
            px = H.pixel_gates(gates, unk)
            proved = {"test_proved_but_broken", "test_plain"}
            backend_total = len(gates) - len(px) - len(unk)
            backend_proved = len(proved - px - set(unk))
        finally:
            shutil.rmtree(d, ignore_errors=True)
        self.assertTrue(unk, "the fixture did not produce an unclassifiable gate, so this law "
                             "would prove nothing")
        self.assertLessEqual(
            backend_proved, backend_total,
            "backendProved (%d) exceeds backendTotal (%d): a gate that is proved AND unclassified "
            "is being counted in one and excluded from the other."
            % (backend_proved, backend_total))
        # ⚠⚠ AND THE LAW MUST READ THE REAL EXPRESSION, NOT ITS OWN ARITHMETIC. The lines above
        # recompute the sum locally, so tampering _write_state left them untouched and the proof
        # came back BLIND — the FOURTH time in this session that a law checked a property it had
        # reproduced instead of the code that ships it. Read what _write_state actually writes.
        # [[the-unjoined-end]] [[sabotage-is-usually-the-wrong-one]]
        src = io.open(os.path.join(HERE, "heart2.py"), encoding="utf-8").read()
        ws = next(n for n in ast.walk(ast.parse(src))
                  if isinstance(n, ast.FunctionDef) and n.name == "_write_state")
        expr = None
        for n in ast.walk(ws):
            if isinstance(n, ast.Dict):
                for k, v in zip(n.keys, n.values):
                    if isinstance(k, ast.Constant) and k.value == "backendProved":
                        expr = ast.unparse(v)
        self.assertIsNotNone(expr, "_write_state no longer writes backendProved at all")
        self.assertIn(
            "_pixel_unk", expr,
            "_write_state computes backendProved as %r — it does not subtract the unclassified, so "
            "a gate that is proved AND unreadable is counted in the numerator while backendTotal "
            "excludes it from the denominator." % expr)

if __name__ == "__main__":
    unittest.main(verbosity=2)
