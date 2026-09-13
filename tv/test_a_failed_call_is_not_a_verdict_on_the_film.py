# -*- coding: utf-8 -*-
"""A CLASSIFY CALL THAT FAILED IS NOT A FRAME THAT COULD NOT BE CLASSIFIED.

`_classify` wrapped `_tv.claude_read(p)` in a bare `except Exception: return None`, and
`_surface_of(None)` is the SAME None a frame gets when it genuinely is not an ownership surface.
So two opposite facts produced one verdict, and `vault_retro.sweep` wrote

    "a still run in <sid> (frame <f>) could not be classified — held rather than guessed onto a shelf"

— a sentence about the FILM, describing something that had happened to the RUN. Nothing prompts a
retry, because nobody is told there is anything to retry.

MEASURED 2026-09-13 on reel_s_1788099999528_42457. Two consecutive sweeps reported
`classified=2` and `classified=2` (so the call WAS made) and held the run as unclassifiable —
while calling `tv_diablo.claude_read()` on the very same frame directly returned
`{'scene': 'stash', 'stashTab': 'shared', 'names': [...]}`. The frame is an unambiguous Shared
stash page 5/5 with ~25 items and the inventory open beside it. Nothing was wrong with the film.

After the lane recovered, the same sweep read it: `pagesRead=1`, "1 panel(s) READ CLEANLY and held
no readable name", "33 occupied / 7 free", sealed `examinedEmpty=True`, and the reel RELEASED —
`panels_never_banked` True -> False. The footage had been held by a transient call for as long as
nobody could see the difference. [[unknown-stays-unknown]] [[zero-needs-a-denominator]]

⚠ THE ERROR IS RECORDED ONCE, NOT PER FRAME — the same shape as `_pix_err` (v1998) beside it. A
per-frame record would turn one dead lane into thousands of identical lines.
"""
import ast
import io
import os
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))


def _fn(src, name):
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


class TestAFailedCallIsNotAVerdictOnTheFilm(unittest.TestCase):

    def setUp(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            self.src = fh.read()
        self.run_fn = _fn(self.src, "_vault_sweep_run")
        self.assertIsNotNone(self.run_fn, "_vault_sweep_run is gone — re-point this guard")

    def test_the_classify_lane_has_somewhere_to_record_a_failure(self):
        names = set()
        for n in ast.walk(self.run_fn):
            if (isinstance(n, ast.Assign) and len(n.targets) == 1
                    and getattr(n.targets[0], "id", None)):
                names.add(n.targets[0].id)
        print("lane error lists present: %s"
              % sorted(x for x in names if x.endswith("_err")))
        self.assertIn("_cls_err", names,
                      "the classify lane has nowhere to record why it went quiet, so a raised "
                      "call and a non-ownership frame stay the same answer")

    def test_the_except_branch_records_instead_of_swallowing(self):
        cls = None
        for n in ast.walk(self.run_fn):
            if isinstance(n, ast.FunctionDef) and n.name == "_classify":
                cls = n
        self.assertIsNotNone(cls, "_classify is gone — re-point this guard")
        handlers = [h for n in ast.walk(cls) if isinstance(n, ast.Try) for h in n.handlers]
        self.assertTrue(handlers, "_classify no longer guards the call at all")
        recorded = False
        for h in handlers:
            body = ast.dump(ast.Module(body=h.body, type_ignores=[]))
            if "_cls_err" in body:
                recorded = True
            self.assertIsNotNone(h.name,
                                 "the handler does not bind the exception, so its cause cannot "
                                 "be recorded even in principle")
        print("classify handlers: %d · records the cause: %s" % (len(handlers), recorded))
        self.assertTrue(recorded,
                        "the handler still swallows the cause — a failed call and a frame that is "
                        "not an ownership surface remain indistinguishable")

    def test_the_failure_is_published_where_a_reader_can_see_it(self):
        # ⚠ MATCH THE KEY EXACTLY, NOT A SUBSTRING OF IT. The first cut asserted the text
        # "classifyError" appeared anywhere in the dump, and heart2 proved it BLIND: renaming the
        # key to `_classifyError_unpublished` still CONTAINS it, so the guard stayed green while
        # the value went somewhere no reader looks. A substring is not a name.
        keys = set()
        for n in ast.walk(self.run_fn):
            if isinstance(n, ast.Assign) and len(n.targets) == 1:
                t = n.targets[0]
                if (isinstance(t, ast.Subscript) and getattr(t.value, "id", None) == "_VAULT_JOB"
                        and isinstance(t.slice, ast.Constant)):
                    keys.add(t.slice.value)
        print("keys published into _VAULT_JOB: %s" % sorted(k for k in keys if isinstance(k, str)))
        self.assertIn("classifyError", keys,
                      "the cause is recorded and never surfaced under that exact key; an error "
                      "nobody can read is the same as no error at all")

    def test_it_is_recorded_once_not_per_frame(self):
        """A dead lane must not print a line per frame."""
        cls = None
        for n in ast.walk(self.run_fn):
            if isinstance(n, ast.FunctionDef) and n.name == "_classify":
                cls = n
        guarded = False
        for n in ast.walk(cls):
            if isinstance(n, ast.If) and "_cls_err" in ast.dump(n.test):
                guarded = True
        self.assertTrue(guarded,
                        "the append is unguarded, so one dead lane becomes one record per frame — "
                        "the same mistake _pix_err was written to avoid")
        print("recorded once, guarded like _pix_err: yes")


RED_PROOF = [
    {
        "why": "the classify handler goes back to swallowing its cause, so a transient call "
               "failure is written as 'could not be classified' — a verdict about his FILM — and "
               "the reel is held for ever with nothing prompting a retry",
        "file": "control_app.py",
        "find": "                if not _cls_err:\n                    _cls_err.append(\"%s: %s\" % (type(_ce).__name__, str(_ce)[:160]))",
        "replace": "                if False:\n                    _cls_err.append(\"%s: %s\" % (type(_ce).__name__, str(_ce)[:160]))",
        "matches": 1,
    },
    {
        "why": "the recorded cause stops being published, so it exists in a local list nobody can "
               "read and the operator still cannot tell a dead lane from unreadable footage",
        "file": "control_app.py",
        "find": "                _VAULT_JOB[\"classifyError\"] = _cls_err[0]",
        "replace": "                _VAULT_JOB[\"_classifyError_unpublished\"] = _cls_err[0]",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
