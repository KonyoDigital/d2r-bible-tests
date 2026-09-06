# -*- coding: utf-8 -*-
"""v2726 — THE COLD READER REFUSED A PANEL THAT WAS CORRECTLY EMPTY, AND KILLED THE WHOLE READ.

`coldread` photographs a shipped version so a DIFFERENT model family can look at the real pixels;
the push gate will not ship version N+1 until version N has had that look. Two of its eight
captures target `.vrg-cols`, the vault Registered ledger below the fold.

MEASURED 2026-09-06: those two captures had been failing with "'.vrg-cols' is not on this page",
and because ANY refusal aborts the run, `coldread` could not produce a cold read at all — the
renderer built to satisfy the second-eye gate could not satisfy it. Reproduced identically on the
two preceding ships (v2723 and v2724), so it was not a regression in either.

THE CAUSE, and it is not a defect in the product: `renderVaultRegistered()` in bible.html ends its
empty case with

    if(!all.length && !findNames.length && !_unkCount){ el.hidden=true; el.innerHTML=''; return; }

and `render_check` launches Chrome on a FRESH PROFILE every run, deliberately, so that no run can
pass because of state left by the last one. That harness world owns nothing, has found nothing and
has read nothing — so the panel hides itself exactly as designed and `.vrg-cols` is never built.
The reader was calling a correct empty state a broken capture.

⚠⚠ THE FIX MUST NOT BECOME AN EXCUSE, WHICH IS WHAT THIS FILE IS FOR. "The panel was empty" is
precisely the sentence a real regression would also produce if nobody checked WHICH empty. So the
distinction is measured against the host element's own declaration, an unrecognised state REFUSES
rather than being waved through, and `test_the_excuse_is_TRUE_of_bible_html` pins that the empty
branch being blamed actually exists in the product. An exemption whose premise nobody re-checks is
[[feedback-threshold-above-the-ceiling]] wearing different clothes.
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

import coldread as C  # noqa: E402

ROOT = os.path.dirname(HERE)


def _between(src, start, end, whence=0):
    """A window anchored at BOTH ends — never `src[i:i+N]`. [[source-reading-guard]]"""
    i = src.find(start, whence)
    if i < 0:
        return None
    j = src.find(end, i + len(start))
    return None if j < 0 else src[i:j + len(end)]


class EmptyIsNotBroken(unittest.TestCase):

    # ── the decision ──────────────────────────────────────────────────────────────────────────
    def test_only_a_DECLARED_EMPTY_host_earns_a_limit(self):
        """Every other state must refuse. An exemption is a door, so it opens on one key only."""
        region = sorted(C.REGION_EMPTY_STATE)[0]
        self.assertEqual("limit", C.region_absence_verdict(region, "declared-empty")[0])
        for st in ("present-but-not-empty", "no-host", "no-spec", "", None,
                   "DECLARED-EMPTY", "declared_empty", "empty", True):
            out, why = C.region_absence_verdict(region, st)
            self.assertEqual(
                "refuse", out,
                "host state %r was accepted as a stated limit. Only the host's own exact "
                "declaration may excuse a missing region; anything else — including a near-miss "
                "spelling — is a state this reader has not been taught, and an untaught state is "
                "not permission. [[unknown-stays-unknown]]" % (st,)
            )
            self.assertTrue(why, "it refused without saying why")

    def test_a_region_nobody_declared_always_refuses(self):
        out, why = C.region_absence_verdict(".this-was-never-declared", "declared-empty")
        self.assertEqual("refuse", out,
                         "an undeclared region was excused by a host state. The excuse must be "
                         "attached to a SPECIFIC region whose empty case somebody checked, or it "
                         "becomes a blanket permission for any missing element.")

    def test_a_visible_host_missing_its_region_is_still_a_REAL_DEFECT(self):
        region = sorted(C.REGION_EMPTY_STATE)[0]
        out, why = C.region_absence_verdict(region, "present-but-not-empty")
        self.assertEqual("refuse", out)
        self.assertIn("VISIBLE", why,
                      "the refusal does not say that the panel was visible and drew nothing, "
                      "which is the whole difference between this and an empty world")

    # ── the excuse has to be true of the product ──────────────────────────────────────────────
    def test_the_excuse_is_TRUE_of_bible_html(self):
        """⚠ THE LOAD-BEARING LAW. If the empty branch is gone, the exemption is a lie."""
        p = os.path.join(ROOT, "bible.html")
        if not os.path.exists(p):
            self.skipTest("bible.html is not in this tree")
        src = io.open(p, encoding="utf-8").read()
        fn = _between(src, "function renderVaultRegistered()", "el.hidden=false")
        self.assertIsNotNone(
            fn,
            "renderVaultRegistered() no longer exists, or no longer has an `el.hidden=false` after "
            "its empty case. coldread excuses a missing `.vrg-cols` on the strength of that "
            "function's empty branch — if the function moved, the excuse is unbacked and this "
            "gate must fail rather than let a real absence through."
        )
        self.assertRegex(
            fn, r"el\.hidden\s*=\s*true",
            "renderVaultRegistered() no longer HIDES the panel when there is nothing to show. "
            "coldread's whole justification is that a hidden host means an empty world; without "
            "this line the host would never report `declared-empty` and the exemption is dead "
            "config that will silently stop excusing anything."
        )
        self.assertRegex(
            fn, r"!all\.length\s*&&\s*!findNames\.length",
            "the empty condition is no longer 'owns nothing and found nothing'. The exemption's "
            "premise moved, so what it now excuses is not what was checked."
        )

    def test_every_declared_host_id_exists_in_the_page(self):
        p = os.path.join(ROOT, "bible.html")
        if not os.path.exists(p):
            self.skipTest("bible.html is not in this tree")
        src = io.open(p, encoding="utf-8").read()
        for region, spec in C.REGION_EMPTY_STATE.items():
            host_id = spec[0]
            self.assertTrue(
                re.search(r"id=[\"']%s[\"']" % re.escape(host_id), src),
                "region %r is excused by host #%s, which is not an id in bible.html. The probe "
                "would call getElementById on nothing, get 'no-host', and refuse forever — a dead "
                "exemption that reads as a working one. [[the-unjoined-end]]" % (region, host_id)
            )

    def test_every_declared_region_is_one_coldread_actually_photographs(self):
        """Dead config is not harmless: it reads as coverage that does not exist."""
        src = io.open(os.path.join(HERE, "coldread.py"), encoding="utf-8").read()
        shot = _between(src, "for tab, w, h, region, sfx in (", "):")
        self.assertIsNotNone(shot, "could not find the capture table to check against")
        for region in C.REGION_EMPTY_STATE:
            self.assertIn(
                repr(region).strip("u"), shot.replace('"', "'"),
                "region %r has an empty-state exemption but is not in the capture table, so the "
                "exemption is about a photograph nobody takes" % region
            )

    # ── the three outcomes stay three ─────────────────────────────────────────────────────────
    def test_a_stated_limit_is_neither_a_capture_nor_a_failure(self):
        src = io.open(os.path.join(HERE, "coldread.py"), encoding="utf-8").read()
        blk = _between(src, "p, why = _shoot(tab, w, h, out_dir, tag, region, sfx)",
                       "(made if p else failed).append(p or why)")
        self.assertIsNotNone(blk, "could not read the outcome-routing block")
        self.assertRegex(
            blk, r'if\s+p\s*==\s*""\s*:',
            "the run loop no longer separates the empty-string outcome. Folded into `made` it "
            "would count a photograph nobody took; folded into `failed` it would kill the read "
            "again, which is the defect this file exists for."
        )
        self.assertIn("skipped.append(why)", blk,
                      "a stated limit is not being carried into `skipped`, so the second eye would "
                      "never be told what it was not shown — and silence reads as agreement")

    def test_shoot_returns_the_empty_string_ONLY_through_the_limit_path(self):
        import ast
        tree = ast.parse(io.open(os.path.join(HERE, "coldread.py"), encoding="utf-8").read())
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "_shoot"), None)
        self.assertIsNotNone(fn, "_shoot is gone")
        bare = []
        for node in ast.walk(fn):
            if isinstance(node, ast.Return) and isinstance(node.value, ast.Tuple):
                first = node.value.elts[0] if node.value.elts else None
                if isinstance(first, ast.Constant) and first.value == "":
                    bare.append(node.lineno)
        self.assertEqual(
            [], bare,
            "_shoot returns a literal \"\" at line(s) %s. The stated-limit outcome must come from "
            "region_absence_verdict, which is the tested decision; a hand-written \"\" is an "
            "untested second door to the same exemption. [[copy-drift]]" % bare
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
