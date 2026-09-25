# -*- coding: utf-8 -*-
"""REG-1306 — THE RENDER GATE SAYS WHERE A PAGE ERROR THREW, NOT ONLY WHAT IT WAS.

2026-09-25: the pre-push render gate refused a push with "the page threw 1 uncaught error(s) while this target
ran ... TypeError: Cannot read properties of null (reading 'innerHTML')" on the Task Force target - which then
rendered CLEAN alone and in a full rerun. render_check kept only the exception's FIRST LINE, so the refusal named
what died and never where: an intermittent red with nothing to chase. It now also keeps the first stack frame
(from the description's `at ...` line, else from exceptionDetails.stackTrace), so the next occurrence names its
file and line.

  · DRIVEN (render_check._Tab.send on a fake CDP socket - the SHIPPED collector): an exception whose
    description carries a stack keeps its first `at` frame; one that carries only a structured stackTrace gets
    `at fn (file:line:col)` built from it; one with neither keeps just its first line (never an invented place).
RED_PROOF below.
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import render_check as RC  # noqa: E402


class _Socket(object):
    def __init__(self, frames):
        self.frames = list(frames)

    def settimeout(self, t):
        pass

    def send(self, payload):
        pass

    def recv(self):
        return self.frames.pop(0)


def _tab(exception_details):
    t = RC._Tab.__new__(RC._Tab)
    t.ws = _Socket([json.dumps({"method": "Runtime.exceptionThrown",
                                "params": {"exceptionDetails": exception_details}}),
                    json.dumps({"id": 1, "result": {"value": 1}})])
    t.n = 0
    t.page_errors = []
    t.send("Runtime.evaluate", expression="1")
    return t.page_errors


class APageErrorNamesWhereItDied(unittest.TestCase):

    def test_a_described_stack_keeps_its_first_frame(self):
        errs = _tab({"exception": {"description":
                    "TypeError: Cannot read properties of null (reading 'innerHTML')\n"
                    "    at renderTaskForce (http://127.0.0.1:17990/board:5655:12)\n"
                    "    at HTMLDivElement.<anonymous> (http://127.0.0.1:17990/board:5702:3)"}})
        self.assertEqual(len(errs), 1)
        self.assertIn("reading 'innerHTML'", errs[0])
        self.assertIn("at renderTaskForce (http://127.0.0.1:17990/board:5655:12)", errs[0],
                      "the refusal says what threw but not where: %r" % errs)

    def test_a_structured_stack_is_turned_into_a_place(self):
        errs = _tab({"text": "Uncaught", "exception": {"description": "TypeError: x is null"},
                     "stackTrace": {"callFrames": [{"functionName": "paintVault", "url": "http://h/board",
                                                    "lineNumber": 39808, "columnNumber": 4}]}})
        self.assertIn("at paintVault (board:39809:5)", errs[0], errs)

    def test_no_stack_at_all_keeps_the_sentence_and_invents_no_place(self):
        errs = _tab({"exception": {"description": "Error: thrown from nowhere in particular"}})
        self.assertEqual(errs, ["Error: thrown from nowhere in particular"])


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-1306 - the gate keeps only the first line again: an intermittent page error names what died, never where",
        "file": "render_check.py",
        "find": "                    self.page_errors.append((_lines[0][:200] + (\"  \" + _at[:160] if _at else \"\")) if _lines else \"\")\n",
        "replace": "                    self.page_errors.append(_lines[0][:200] if _lines else \"\")\n",
        "matches": 1,
    },
    {
        "why": "REG-1306 - a structured stackTrace is ignored, so an exception without a described stack loses its place",
        "file": "render_check.py",
        "find": "                    if not _at:\n                        _cf = (((_e.get(\"stackTrace\") or {}).get(\"callFrames\")) or [{}])[0]\n",
        "replace": "                    if False:\n                        _cf = (((_e.get(\"stackTrace\") or {}).get(\"callFrames\")) or [{}])[0]\n",
        "matches": 1,
    },
]
