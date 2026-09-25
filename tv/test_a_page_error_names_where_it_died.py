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
  · DRIVEN (the #231 eye on 1e1f946e: two other writers of the same list still cut to one line): _Tab.ev() -
    an exception out of an evaluated expression, where an activation click lands - names its place too; the
    in-page collector (the SHIPPED hook script, run in node) pushes the error's stack, and the drain keeps it.
RED_PROOF below.
"""
import io
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


    def test_an_exception_out_of_an_evaluated_expression_names_its_place(self):
        t = RC._Tab.__new__(RC._Tab)
        t.ws = _Socket([json.dumps({"id": 1, "result": {"result": {}, "exceptionDetails": {
            "exception": {"description": "TypeError: Cannot read properties of null (reading 'innerHTML')\n"
                                         "    at openTaskForce (http://h/board:5650:9)"}}}})])
        t.n = 0
        t.page_errors = []
        t.last_exc = None
        t.ev("document.body.click()")
        self.assertEqual(len(t.page_errors), 1)
        self.assertIn("at openTaskForce (http://h/board:5650:9)", t.page_errors[0],
                      "ev() still cuts the error to its first line: %r" % t.page_errors)

    def test_the_in_page_collector_keeps_the_stack(self):
        import shutil, subprocess
        node = shutil.which("node")
        if not node:
            self.skipTest("node is absent - this case is UNMEASURED, not passing")
        src = io.open(os.path.join(HERE, "render_check.py"), encoding="utf-8").read()
        i = src.index('        _ERR_HOOK = (')
        j = src.index('        tab.send("Page.addScriptToEvaluateOnNewDocument", source=_ERR_HOOK)', i)
        ns = {}
        exec(compile(src[i:j].strip(), "_ERR_HOOK", "exec"), {}, ns)
        js = ("var L={}; var window={addEventListener:function(t,f){L[t]=f;}};\n" + ns["_ERR_HOOK"] + "\n"
              "L.error({message:'TypeError: boom', error:{message:'boom', stack:'TypeError: boom\\n    at paint (http://h/board:39808:4)'}});\n"
              "console.log(JSON.stringify(window.__rcErrors));")
        r = subprocess.run([node, "-e", js], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr[:400])
        pushed = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual(len(pushed), 1)
        self.assertIn("at paint (http://h/board:39808:4)", RC._err_place(pushed[0]),
                      "the in-page collector drops the place: %r" % pushed)

if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-1306 - the shared rule keeps only the first line again: every writer names what died, never where",
        "file": "render_check.py",
        "find": "    return lines[0][:200] + (\"  \" + at[:160] if at else \"\")\n",
        "replace": "    return lines[0][:200]\n",
        "matches": 1,
    },
    {
        "why": "REG-1306 - a structured stackTrace is ignored, so an exception without a described stack loses its place",
        "file": "render_check.py",
        "find": "    if not at and isinstance(details, dict):\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "REG-1306 (#231 on 1e1f946e) - ev() cuts its exception to the first line again, where an activation click lands",
        "file": "render_check.py",
        "find": "                self.page_errors.append(_err_place(self.last_exc, _x))   # REG-1306 - and where\n",
        "replace": "                self.page_errors.append(str(self.last_exc).splitlines()[0][:200])\n",
        "matches": 1,
    },
    {
        "why": "REG-1306 (#231 on 1e1f946e) - the in-page collector pushes the bare message again, without the stack",
        "file": "render_check.py",
        "find": "\"if(m){p((e.error&&e.error.stack)||",
        "replace": "\"if(m){p((m)||",
        "matches": 1,
    },
]
