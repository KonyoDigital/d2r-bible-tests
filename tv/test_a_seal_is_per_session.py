# -*- coding: utf-8 -*-
"""v2743 — A SWEEP STAMPED ONE PASS-WIDE ROW COUNT ONTO EVERY SESSION IT READ.

Not latent. It fired, and the wrong record is on his disk. MEASURED on his real vault_swept.json —
one pass sealed SIX sessions in the same second, each stamped `rows=7`, while vault_accum says what
each actually witnessed:

    s_1784984019250_95276   6      s_1787495295689_1483    1
    s_1787520892804_95400   5      s_1785078127173_28278   0   <- contributed NOTHING
    s_1787512325134_62795   4      s_1787242455315_9654    0   <- nowhere in accum OR vault_seen
    claimed across the six: 42   ·   actual owned rows in the pass: 7

⚠⚠ AND THE PHANTOM 42 PROPAGATED INTO THE REPO'S OWN SELF-DIAGNOSIS. `frame_authority.py:252`,
`run_gates.py:789` and `test_seal_verdict.py:22` all cite "42 rows of real content sealed with no
record of what was taken. THAT is the defect." It is 7 counted six times, two of the six
contributing nothing — so the v2702 docstring diagnoses an evidence gap that never existed.

=== WHY IT MATTERS EVEN THOUGH THE RELEASE HALF IS LATENT ===
Those six seals predate v2305, carry no `extracted` key, and therefore land UNEVIDENCED — so
nothing has been wrongly released YET. Written by today's code the same pass yields six COVERED
seals, four earned and two inherited, and `seal_releases_frames` returns True unconditionally on
COVERED. But `rows` is load-bearing in two other places already consuming the inflated figure:
  · `seal_verdict` requires rows == 0 before it will say EMPTY
  · `reel_retention.py:540`'s `rows-not-banked` renders it into a sentence HE READS

=== THE FIX, AND WHY IT IS SAFE ===
The proposal's rows already carry `witnesses` built by `_witness_rows`, and every witness dict
carries `"session"` — so per-session attribution EXISTED and was being thrown away. Verified against
the real functions before the change was written:

    _seal_extracted(0) -> ([], 'nothing was taken')  -> seal_verdict EMPTY -> releases False (HELD)
    _seal_extracted(4) -> (['name','location','provenance'])        -> COVERED -> releases True

So a non-contributing session is now HELD rather than released — the direction that keeps footage.
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

SRC = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()


def _between(src, start, end):
    """Anchored at BOTH ends — never a fixed window. [[source-reading-guard]]"""
    i = src.find(start)
    if i < 0:
        return None
    j = src.find(end, i + len(start))
    return None if j < 0 else src[i:j + len(end)]


class ASealIsPerSession(unittest.TestCase):

    def test_the_guard_can_find_the_seal_writer_AT_ALL(self):
        """⚠ A law that finds nothing to grade passes having examined ZERO candidates."""
        blk = _between(SRC, "_rows_by_sess = {}", "_seal_pending = True")
        self.assertIsNotNone(blk, "the seal writer is gone or renamed — fix this guard before "
                                  "trusting a green from it")
        self.assertIn("sessionsRead", blk, "the seal loop no longer walks sessionsRead")

    # ── ⚠⚠ THE LAW ────────────────────────────────────────────────────────────────────────────
    def test_each_session_is_sealed_for_what_IT_witnessed(self):
        blk = _between(SRC, "_rows_by_sess = {}", "_seal_pending = True")
        self.assertIn('_srows = int(_rows_by_sess.get(str(sess), 0))', blk,
                      "the seal loop no longer looks the session up in the per-session map")
        self.assertIn('"rows": _srows', blk,
                      "the seal writes something other than the session's OWN row count. A "
                      "pass-wide figure stamped on every session is how six seals came to claim "
                      "42 rows over a pass that produced 7.")

    def test_the_pass_wide_figure_is_NOT_written_as_the_session_figure(self):
        """⚠ The exact regression. `"rows": int(_rows)` inside the loop is the original defect."""
        blk = _between(SRC, "for sess in (prop.get(\"sessionsRead\")", "_seal_pending = True")
        self.assertIsNotNone(blk, "could not read the seal loop")
        self.assertNotIn('"rows": int(_rows)', blk,
                         "the pass-wide count is being stamped on each session again")

    def test_the_attribution_comes_from_the_WITNESSES_not_a_guess(self):
        """The witness dicts already carry `session`; this must read them rather than divide the
        pass total or assume an even split."""
        blk = _between(SRC, "_rows_by_sess = {}", "for sess in (prop.get(\"sessionsRead\")")
        self.assertIsNotNone(blk, "the per-session map is gone")
        self.assertIn('_prow.get("witnesses")', blk,
                      "attribution no longer reads the witness rows")
        self.assertIn('_w.get("session")', blk,
                      "attribution no longer keys on the witness's own session id")
        for bad in ("/ len(", "// len(", "round(", "_rows /"):
            self.assertNotIn(bad, blk,
                             "attribution appears to DIVIDE the pass total (%r). An even split is "
                             "a guess wearing a measurement's clothes — two of his six sessions "
                             "witnessed nothing at all." % bad)

    # ── ⚠ THE PASS FIGURE SURVIVES, BESIDE IT ─────────────────────────────────────────────────
    def test_the_pass_total_is_kept_under_its_OWN_name(self):
        """The 42 happened because one number did two jobs. Both travel now, each named."""
        blk = _between(SRC, "_rows_by_sess = {}", "_seal_pending = True")
        self.assertIn('"passRows": int(_rows)', blk,
                      "the pass total is no longer recorded, so a reader has to infer it from the "
                      "per-session figures — which is how one number came to mean two things")

    # ── the consequence, run against the REAL deciders ────────────────────────────────────────
    def test_a_session_that_witnessed_NOTHING_is_held_not_released(self):
        """⚠ THE LOAD-BEARING DIRECTION, and it is why this fix is safe rather than merely tidy."""
        import frame_authority as FA
        import control_app as CA
        ex, why = CA._seal_extracted(0)
        seal = {"ts": 1, "rows": 0, "extracted": ex, "extractedWhy": why}
        ok, rwhy = FA.seal_releases_frames(seal)
        self.assertFalse(ok,
                         "a session that contributed nothing would RELEASE its frames. Under the "
                         "old pass-wide count it inherited rows=7 and scored COVERED; it must now "
                         "score EMPTY and be held. why=%r" % str(rwhy)[:120])

    def test_a_session_that_DID_witness_rows_still_releases(self):
        """The other direction: this must not turn into a blanket refusal. A fix that holds
        everything is not a fix, it is the disabled prune again."""
        import frame_authority as FA
        import control_app as CA
        ex, why = CA._seal_extracted(4)
        ok, _ = FA.seal_releases_frames({"ts": 1, "rows": 4, "extracted": ex, "extractedWhy": why})
        self.assertTrue(ok, "a genuine contributor stopped releasing — this fix must not become a "
                            "blanket hold")

    def test_it_still_parses(self):
        ast.parse(SRC)


if __name__ == "__main__":
    unittest.main(verbosity=2)
