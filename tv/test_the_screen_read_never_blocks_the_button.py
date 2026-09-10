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





# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
# The tamper is the defect verbatim: read the screen on the request thread, which is what made the
# POST hang with zero bytes for 8-25s.
# ⚠⚠ v2865 — NO RED_PROOF, DELIBERATELY, AND THIS IS THE HONEST STATE.
# The block that stood here tampered the MINI(AUTOMATIC) planner in control_app.py — code v2857
# DELETED outright by his ruling. It matched 0 times and turned CI red on
# test_every_declared_red_proof_is_well_formed: "a sabotage that changes nothing proves nothing".
# A stale proof is worse than none: it reports coverage while proving nothing at all, and it took a
# CI run to say so because the pre-push suite runs only test_agent + test_control while the full
# registry runs on the runner. [[regression-guard]]
#
# The one surviving law asserts an ABSENCE — no request handler may call the screen reader on its
# own thread. Nothing can be DELETED to make an absence false; the sabotage would have to INSERT a
# call inside a handler, which this engine's find/replace cannot express. So this gate is UNPROVEN
# rather than falsely proved, and the census counts it that way. [[unknown-stays-unknown]]


    # ══ v2857 — FOUR LAWS RETIRED, THEIR SUBJECT WAS DELETED BY RULING (REG-823) ═══════════════
    #   test_the_reader_is_called_at_all
    #   test_the_plan_runs_on_a_named_thread
    #   test_planning_is_reported_as_its_own_state
    #   test_a_stop_invalidates_a_plan_still_in_flight
    # All four read control_app.py for the MINI(AUTOMATIC) planning machinery — the named plan
    # thread, _MINI_AUTO_PLAN's token, the planning state on the wire. v2857 DELETED that handler
    # body outright (237 lines) after a cross-family review pointed out that leaving mouse-driving
    # code unreachable-but-present brings it back live the moment anyone moves the guard above it.
    #
    # ★ THE FIFTH LAW STAYS, AND IT IS THE ONE WORTH KEEPING. test_no_request_handler_reads_the
    # _screen_on_its_own_thread is about EVERY handler, not this one — the general shape of the
    # v2801 defect. Retiring the whole class to silence four stale laws would have thrown away the
    # only law here that still guards something. [[regression-guard]]


RED_PROOF = [
    {
        'why': 'v2801 — a request handler that reads the screen INLINE blocks the HTTP response, and a POST that never returns is a button that looks dead (Grok measured 0 bytes for 8s, then 25s, on his live console). The tamper reintroduces that exact defect: the lattice+occupancy scan called on the request thread, inside the handler body.  MEASURED: untampered OK — `python3 test_the_screen_read_never_blocks_the_button.py` -> "Ran 1 test ..; tampered (all 2) FAILED (failures=1). AssertionError: \'do_GET\' unexpectedly found in (\'do_GET\',\'d; reddened law test_the_screen_read_never_blocks_the_button.TestScreenReadNeverBlocks; ALONE FAILS ALONE. Fresh process: `python3 -m unittest test_the_screen_read_never_blocks_the_button.TestSc.',
        'file': 'control_app.py',
        'find': '        if path == "/api/mini_auto":\n',
        'replace': '        if path == "/api/mini_auto":\n            _cells = _mini_cells_from_live_frame("stash")\n',
        'matches': 2,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
