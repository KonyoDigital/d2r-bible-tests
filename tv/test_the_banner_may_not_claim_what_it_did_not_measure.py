#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2799 — THE STARTUP BANNER ANNOUNCED "OCR OFF" AND "ocr lane: ON" FIVE LINES APART.

⚠⚠ WHAT IT COST, 2026-09-08. He was reporting "its not reading anything or moving", and the
console's own log said, in the LIGHT branch:

    ⚡ LIGHT reader — screenshot every ~1.8s · film OFF · OCR OFF · 1 claude · plays nice…
    ocr lane: ON /Users/…/tv/bin/ocr_mac

Both, in one banner. The first is a HARDCODED string inside `if LIGHT_MODE:`; the second is
measured from `_OCR.available()`. I believed the false half and spent two minutes concluding the
reader was switched off — when `OCR_ENABLED = os.environ.get("TV_OCR", "1") != "0"` is ON by
default and has NOTHING to do with LIGHT mode.

⚠ AND `_film_on` WAS ALREADY COMPUTED ON THE LINE DIRECTLY ABOVE AND THROWN AWAY — a real
measurement sitting unused next to a hardcoded claim about the same thing.
[[label-outlived-referent]] [[plumbing-with-no-tap]]

★ THE LAW: a banner line may not state a hardcoded ON/OFF about a subsystem whose real state is
computed elsewhere in the same function. He reads that log to decide whether his machine is broken;
a line that is confidently wrong sends him — and me — after the wrong thing.

⚠ PARSED, NEVER GREPPED. A regex over this file matches the very comment above explaining the
defect. The check walks the AST for the `print` inside `if LIGHT_MODE:` and inspects its f-string
parts. [[source-reading-guard]]
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

SRC = os.path.join(HERE, "tv_diablo.py")


def _light_branch_prints():
    """Every print() inside the BANNER's `if LIGHT_MODE:` body. -> [ast.Call]

    ⚠⚠ SCOPED TO THE BANNER BRANCH, AND THE FIRST CUT WAS NOT. It collected prints from EVERY
    `if LIGHT_MODE:` in the file and pooled them. So the "has the banner gone silent" check counted
    f-strings belonging to OTHER branches, and a sabotage that replaced the banner with a bare
    `print("   LIGHT reader")` stayed GREEN — the other branches' interpolations covered for it.
    Caught only because the sabotage was run. A law that pools evidence from several subjects is
    measuring none of them. [[sabotage-is-usually-the-wrong-one]]

    The banner branch is the one whose own text says "LIGHT reader".
    """
    tree = ast.parse(io.open(SRC, encoding="utf-8").read())
    best = None
    for n in ast.walk(tree):
        if not isinstance(n, ast.If):
            continue
        t = n.test
        if not (isinstance(t, ast.Name) and t.id == "LIGHT_MODE"):
            continue
        # ⚠⚠ n.body ONLY — ast.walk(an ast.If) INCLUDES THE `orelse`. The first cut walked the
        # whole If and so counted the ELSE branch's four interpolations
        # (f"film: live ~{_FILM_FPS}fps · SIM {_FOOTAGE_FPS}fps · max {FILM_MAX_PX}px · q{...}")
        # as if they belonged to the LIGHT banner. MEASURED under the sabotage: 4 prints and 5
        # FormattedValues found where the branch really has 2 and 1 — so replacing the banner with
        # a bare string stayed GREEN twice, covered for by the branch it is not in.
        # [[sabotage-is-usually-the-wrong-one]] [[feedback-suspect-the-instrument]]
        prints = [c for stmt in n.body for c in ast.walk(stmt)
                  if isinstance(c, ast.Call) and getattr(c.func, "id", None) == "print"]
        text = " ".join(_literal_text(c) for c in prints)
        if "LIGHT reader" in text:
            best = prints
            break
    return best or []


def _literal_text(call):
    """The CONSTANT parts of a print's f-string — what it says regardless of any value."""
    bits = []
    for a in call.args:
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            bits.append(a.value)
        elif isinstance(a, ast.JoinedStr):
            for v in a.values:
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    bits.append(v.value)
    return " ".join(bits)


class TheBannerMayNotClaimWhatItDidNotMeasure(unittest.TestCase):

    def test_the_scanner_finds_the_branch(self):
        """⚠ A law that cannot find its subject passes having examined nothing."""
        ps = _light_branch_prints()
        self.assertGreaterEqual(len(ps), 2,
                                "only %d print(s) found inside `if LIGHT_MODE:` — the banner moved "
                                "or was restructured; re-point this law" % len(ps))

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────
    def test_the_LIGHT_banner_states_no_hardcoded_OCR_verdict(self):
        """★★★ THE DEFECT. `OCR OFF` as a literal, while `ocr lane:` five lines below measures it
        and says ON."""
        said = " ".join(_literal_text(p) for p in _light_branch_prints())
        low = said.lower()
        for bad in ("ocr off", "ocr on"):
            self.assertNotIn(
                bad, low,
                "the LIGHT banner hardcodes %r. OCR_ENABLED is read from TV_OCR and is unrelated "
                "to LIGHT mode, and `ocr lane:` measures the real state a few lines below — so a "
                "literal here can (and did) contradict it in the same breath. Interpolate the "
                "measured value instead." % bad)

    def test_it_states_no_hardcoded_FILM_verdict_either(self):
        """⚠ Same shape, same function: `_film_on` is computed immediately above."""
        said = " ".join(_literal_text(p) for p in _light_branch_prints()).lower()
        for bad in ("film off", "film on"):
            self.assertNotIn(
                bad, said,
                "the LIGHT banner hardcodes %r while `_film_on` is computed on the line above it. "
                "A measurement thrown away beside a claim about the same thing is how the two "
                "drift apart." % bad)

    def test_the_banner_actually_INTERPOLATES_something(self):
        """⛔ The cheap way to pass the two laws above is to say nothing at all. A banner that
        stopped reporting would be worse than one that reported wrongly, because nobody would even
        know to doubt it."""
        ps = _light_branch_prints()
        joined = [p for p in ps
                  if any(isinstance(a, ast.JoinedStr) for a in p.args)]
        self.assertTrue(joined,
                        "no print inside `if LIGHT_MODE:` interpolates anything — the banner has "
                        "gone silent rather than truthful")
        vals = []
        for p in joined:
            for a in p.args:
                if isinstance(a, ast.JoinedStr):
                    vals += [v for v in a.values if isinstance(v, ast.FormattedValue)]
        self.assertGreaterEqual(
            len(vals), 3,
            "the LIGHT banner interpolates only %d value(s); it reports the poll cadence, the film "
            "state and the OCR state, so fewer than three means one of them went back to being a "
            "literal" % len(vals))


RED_PROOF = [
    {
        'why': 'Reinstates the exact v2799 defect: the LIGHT-mode startup banner stops interpolating the MEASURED OCR state (`_ocr_here`, computed from OCR_ENABLED and _OCR.available() on the two lines above) and goes back to a hardcoded literal "OCR OFF" — while `ocr lane: {ocr_tag}` five lines below still prints the real, measured state and says ON. The tamper deletes the real thing the law protects (the interpolation of a measurement) rather than a comment or a message-string mention: the gate PARSES the AST of the `if LIGHT_MODE:` body and inspects the constant parts of the banner print\'s f-string, so only an edit to the banner\'s own literal text can move it. It is not a shared constant (nothing else reads `_ocr_here`, count=1 use site) and not on the wrong side of a union (there is one derived set, the literal text of the banner branch).  MEASURED: untampered OK — 4 tests, all pass: `python3 tv/test_the_banner_may_not_claim_what_it_did_not_measure.; tampered (all 1) FAILED (failures=1), exit 1. Match count printed before the edit: matches=1, and after the; reddened law test_the_banner_may_not_claim_what_it_did_not_measure.TheBannerMayNotC; ALONE FAILS ALONE. `python3 -m unittest test_the_banner_may_not_claim_what_it_did_not_measure.TheBannerMayNotClaimWh.',
        'file': 'tv_diablo.py',
        'find': 'OCR {_ocr_here} · 1 claude',
        'replace': 'OCR OFF · 1 claude',
        'matches': 1,
    },
]


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
