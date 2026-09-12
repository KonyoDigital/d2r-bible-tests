# -*- coding: utf-8 -*-
"""v2992 — ONE reel_story.story() PER PRINTER SNAPSHOT.

`printer._sources()`'s own docstring promises it: *"Every owner's reading, taken ONCE ... so two
stations on the same row cannot disagree about the same reel because they asked at different
moments."* It was breaking that promise for the story.

MEASURED on his tree, by counting calls and reading the stack that made each one:
    river:98  <- _story:65 <- story:115
    routes:98 <- _story:52 <- story:115
`reel_story.story()` ran TWICE inside one snapshot — once through `reel_river.river()` and once
through `per_reel_routes.routes()` — and each story() does its own `reel_retention.plan()`.
After: story() 1, plan() 1.

⚠ THE WALL-CLOCK IS NOT THE CLAIM, AND SAYING SO IS THE POINT. A first reading looked like
0.312s -> 3.912s, which would read as a 12x regression; it is the OS page cache, because plan()
walks the disk and the two runs were not in comparable states. The honest measurement here is the
CALL COUNT, which is deterministic. A timing A/B on this function needs both sides warm, and
nothing in this law depends on one. [[ab-against-head-before-blaming-the-room]]

⚠ SHARING MUST NEVER TURN "COULD NOT READ" INTO "NOTHING THERE". When the shared snapshot fails,
`_story_rows` stays None and BOTH callees fall back to taking their own reading, exactly as before.
`reel_river.river(rows=...)` is optional and defaulted, so all 8 existing call sites — none of
which pass anything — are untouched. [[unknown-stays-unknown]]

⚠ AND A CONDITIONAL KEY IS NOT A DROPPED ONE. While checking this I asserted `reachWhy` must be
present and it was not — `_sources` sets it ONLY when printer_reach returns a why. The check was
wrong, not the code. A law that requires an optional field goes red on a healthy run.
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


class OneStoryPerSnapshot(unittest.TestCase):

    def test_river_accepts_a_supplied_snapshot(self):
        import reel_river as RR
        sig = list(RR.river.__code__.co_varnames[:RR.river.__code__.co_argcount])
        self.assertIn("rows", sig,
                      "reel_river.river() no longer accepts a shared snapshot, so the printer must "
                      "let it take its own reading and story() runs twice again: %r" % sig)

    def test_the_supplied_snapshot_is_actually_used(self):
        """⚠ A PARAMETER THAT IS ACCEPTED AND IGNORED IS THE SAME AS NO PARAMETER."""
        import reel_river as RR
        src = io.open(os.path.join(HERE, "reel_river.py"), encoding="utf-8").read()
        # ⚠⚠ READ THE FUNCTION'S CODE, NOT A FIXED WINDOW OF IT. The first cut took `fn[:600]`
        # and went red: the docstring is longer than that, so the branch it was looking for sat
        # just past the window and read as ABSENT. `src[i:i+N]` measures my guess at where a thing
        # is, never the file — and the docstring is stripped too, so prose describing the branch
        # can never stand in for the branch. [[source-reading-guard]]
        fn = None
        for n in ast.parse(src).body:
            if isinstance(n, ast.FunctionDef) and n.name == "river":
                body = list(n.body)
                if (body and isinstance(body[0], ast.Expr)
                        and isinstance(getattr(body[0], "value", None), ast.Constant)
                        and isinstance(body[0].value.value, str)):
                    body = body[1:]          # drop the docstring
                fn = "\n".join(ast.get_source_segment(src, st) or "" for st in body)
        self.assertIsNotNone(fn, "river() is gone")
        self.assertIn("if rows is None:", fn,
                      "river() takes `rows` but never branches on it, so the caller's snapshot is "
                      "accepted and thrown away")

    def test_the_printer_takes_one_story_and_threads_it(self):
        src = io.open(os.path.join(HERE, "printer.py"), encoding="utf-8").read()
        i = src.find("def _sources")
        j = src.find("\ndef ", i + 10)
        body = src[i:j]
        self.assertIn("_story_rows", body,
                      "_sources no longer takes a shared story snapshot")
        self.assertIn("rows=_story_rows", body,
                      "the snapshot is taken but not handed to reel_river.river()")
        self.assertIn("PRR.routes, _story_rows", body,
                      "the snapshot is taken but not handed to per_reel_routes.routes()")

    # ── the round trip ────────────────────────────────────────────────────────────────────────
    def test_one_snapshot_calls_story_once(self):
        import printer as P
        import reel_story as RS
        calls = {"n": 0}
        orig = RS.story
        def counted(*a, **k):
            calls["n"] += 1
            return orig(*a, **k)
        RS.story = counted
        try:
            src, _whys = P._sources()
        finally:
            RS.story = orig
        self.assertLessEqual(
            calls["n"], 1,
            "reel_story.story() ran %d times in ONE snapshot. Each one does its own "
            "reel_retention.plan(), and _sources' own docstring promises every owner's reading is "
            "taken ONCE so two stations cannot disagree about the same reel." % calls["n"])
        # and the snapshot must still be usable
        self.assertTrue((src.get("river") or {}).get("ok") is not None,
                        "the river answer went missing once the snapshot was shared")
        self.assertTrue((src.get("routes") or {}).get("ok") is not None,
                        "the routes answer went missing once the snapshot was shared")


RED_PROOF = [
    {
        "why": "dropping the `rows is None` branch makes river() ignore the caller's snapshot and "
               "take its own reading, so story() runs twice per printer snapshot again",
        "file": "reel_river.py",
        "find": "    if rows is None:\n        rows, why = _story()",
        "replace": "    if True:\n        rows, why = _story()",
        "matches": 1,
    },
    {
        "why": "not handing the snapshot to routes() restores the second story()/plan() pair",
        "file": "printer.py",
        "find": "        out[\"routes\"], w = _safe(PRR.routes, _story_rows)",
        "replace": "        out[\"routes\"], w = _safe(PRR.routes)",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
