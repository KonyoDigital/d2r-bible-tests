#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2801 — THE START POST DID NOT RETURN, SO THE BUTTON LOOKED DEAD.

Grok bot drove the endpoint on his live console with the game running and fresh frames, and
measured the thing Konyo had been reporting for two days as "nothing happens when i click mini
automatic":

    POST /api/mini_auto {"on":true,"container":"stash"}
      -> hung with 0 bytes for 8s
      -> hung with 0 bytes for 25s          (curl timed out; no JSON body, no `why`)
    GET  /api/mini_auto  meanwhile:  {"running": false, "planned": 0, "moved": 0}

★ A HANG IS NOT A REFUSAL, AND THAT IS THE WHOLE POINT. v2798 gave this button a refusal toast so
the console would say why it declined — and a refusal that never returns cannot be toasted. The UI
`await`s the fetch; a POST that takes 25s is 25 seconds of a button that has visibly done nothing.
Every fix aimed at the REASON was aimed at the wrong half. [[unknown-stays-unknown]]

The cause: the handler called `_mini_cells_from_live_frame` INLINE — a lattice fit plus an occupancy
scan over a 1920x1080 frame — on the HTTP request thread, on a Mac simultaneously running the game,
the console, an OCR worker and a screen capture. That work has no ceiling; it costs whatever the
machine has left, which is why it measured 0.26s here and 25s there.

⚠ NOT A TIMEOUT, AND NOT A FASTER SCAN. Both would still block, just less. A start endpoint answers
immediately and the work runs behind it — the same shape `mini_start` has used since v1603 (arm the
watchdog, THEN spawn), so this is the console's existing pattern rather than a new one invented at
the point of failure. [[borrowed-surface]]

THE LAW: no request handler may call the screen reader on its own thread. Checked by PARSING —
`_mini_cells_from_live_frame` must never appear directly in a `do_GET`/`do_POST` body, only inside a
nested function that a thread runs. A grep for "threading.Thread" nearby would pass on a handler
that spawns a thread and then blocks anyway. [[source-reading-guard]]
"""
import os
import ast
import io
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "control_app.py")

if HERE not in sys.path:
    sys.path.insert(0, HERE)
# This file PARSES control_app rather than importing it, which is deliberate — but it also means it
# misses the exemption every other gate here gets for free (importing control_app enables this as a
# side effect). Its own docstring and output carry non-ASCII, so on a non-UTF-8 console it would
# crash while REPORTING and a clean tree would exit non-zero. [[the-unjoined-end]]
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

READER = "_mini_cells_from_live_frame"
HANDLERS = ("do_GET", "do_POST", "do_PUT", "do_DELETE")


def _tree():
    with io.open(SRC, encoding="utf-8") as fh:
        return ast.parse(fh.read())


def _parents(tree):
    p = {}
    for node in ast.walk(tree):
        for kid in ast.iter_child_nodes(node):
            p[kid] = node
    return p


def _innermost_func(node, parents):
    cur = parents.get(node)
    while cur is not None:
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return cur
        cur = parents.get(cur)
    return None


class TestScreenReadNeverBlocksTheButton(unittest.TestCase):

    def setUp(self):
        self.tree = _tree()
        self.parents = _parents(self.tree)

    def _reader_calls(self):
        out = []
        for n in ast.walk(self.tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == READER:
                out.append(n)
        return out

    def test_the_reader_is_called_at_all(self):
        """THE INSTRUMENT FIRST. If the name is ever renamed, every assertion below
        passes over an empty list and this file becomes decoration."""
        calls = self._reader_calls()
        self.assertTrue(calls,
                        "%s is never called anywhere — this law is measuring nothing" % READER)
        print("\n   reader call sites: %d" % len(calls))

    def test_no_request_handler_reads_the_screen_on_its_own_thread(self):
        for call in self._reader_calls():
            fn = _innermost_func(call, self.parents)
            self.assertIsNotNone(fn, "a %s call sits outside any function" % READER)
            self.assertNotIn(
                fn.name, HANDLERS,
                "%s is called directly in %s (line %d) — that blocks the HTTP response, "
                "and a POST that does not return is a button that looks dead"
                % (READER, fn.name, call.lineno))
            print("   line %-6d inside def %s()  -> off the request thread"
                  % (call.lineno, fn.name))

    def test_the_plan_runs_on_a_named_thread(self):
        names = []
        for n in ast.walk(self.tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
               and n.func.attr == "Thread":
                for kw in n.keywords:
                    if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                        names.append(kw.value.value)
        self.assertIn("tvd-miniauto-plan", names,
                      "no thread carries the plan — found: %s" % sorted(set(names))[:12])

    def test_planning_is_reported_as_its_own_state(self):
        """running:false during a 25s screen read is not false, it is UNKNOWN-shaped.
        The GET half must be able to say 'planning' or the UI has nothing to render."""
        with io.open(SRC, encoding="utf-8") as _fh:
            src = _fh.read()
        self.assertIn('_st["planning"] = True', src,
                      "the GET half never reports a plan in flight")
        self.assertIn("_MINI_AUTO_PLAN", src,
                      "there is no plan state for the GET half to read")

    def test_a_stop_invalidates_a_plan_still_in_flight(self):
        """Without this, a plan that began before STOP calls hover_mode.start() after it —
        a stop button that starts the mode."""
        with io.open(SRC, encoding="utf-8") as _fh:
            src = _fh.read()
        self.assertIn('_MINI_AUTO_PLAN["token"] += 1', src,
                      "nothing invalidates an in-flight plan, so STOP can be overtaken by it")


if __name__ == "__main__":
    unittest.main(verbosity=2)
