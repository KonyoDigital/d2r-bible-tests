#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WHICH IMAGE IS ANSWERING — task #67, first half.

His console EXECS the working tree, so every save is a deploy. But a process already running keeps
its OLD image until it restarts, and until v2948 no surface could tell the two apart: `/api/status`
reported nothing that changes when the running image is replaced.

Every law here PARSES. [[source-reading-guard]] [[the-unjoined-end]]
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

import control_app as CA  # noqa: E402

SRC = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
TREE = ast.parse(SRC)


class TheConsoleSaysWhichImageIsAnswering(unittest.TestCase):

    def test_the_stamp_is_taken_at_IMPORT_not_per_request(self):
        """⚠⚠ THE WHOLE POINT, AND IT IS ONE LINE AWAY FROM USELESS. If `_PROC_START_MS` were
        computed inside the producer it would be `now` on every poll, identical for every image,
        and the detector would be a clock with extra steps. Parsed: the assignment must sit at
        MODULE level, and the producer must not call time.time()."""
        top = [n for n in TREE.body
               if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == "_PROC_START_MS" for t in n.targets)]
        self.assertEqual(1, len(top),
                         "_PROC_START_MS must be assigned exactly once at MODULE level (found %d)"
                         % len(top))
        fn = next((n for n in ast.walk(TREE)
                   if isinstance(n, ast.FunctionDef) and n.name == "_proc_identity"), None)
        self.assertIsNotNone(fn, "_proc_identity is gone")
        for n in ast.walk(fn):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                self.assertNotEqual("time", getattr(n.func.value, "id", None),
                                    "_proc_identity reads the clock, so every image would report "
                                    "the same 'start' and nothing could be told apart")

    def test_the_payload_actually_SERVES_it(self):
        """Not that the producer exists — that the response dict CALLS it. A law asserting only
        existence proves the tap was plumbed, never that water came out."""
        served = False
        for d in (n for n in ast.walk(TREE) if isinstance(n, ast.Dict)):
            for k, v in zip(d.keys, d.values):
                if isinstance(k, ast.Constant) and k.value == "proc":
                    served = True
        self.assertTrue(served, "no response dict carries a \"proc\" key")

    def test_it_is_NOT_the_agent_pid_wearing_a_new_name(self):
        """`pid` already exists in this payload and is the AGENT's (_pid_cached). Reusing it would
        be a label that outlived its referent. [[label-outlived-referent]]"""
        d = CA._proc_identity()
        self.assertEqual(os.getpid(), d.get("pid"),
                         "proc.pid is not this process")
        self.assertIsInstance(d.get("startedMs"), int)

    def test_the_version_comes_from_the_APP_not_a_literal(self):
        """⚠ A second \"vNNNN\" literal in control_app.py blanks _disk_ver() and silently kills the
        tvd-version-drift lane. Parsed: _proc_identity must call _app_ver()."""
        fn = next((n for n in ast.walk(TREE)
                   if isinstance(n, ast.FunctionDef) and n.name == "_proc_identity"), None)
        names = {n.func.id for n in ast.walk(fn)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertIn("_app_ver", names,
                      "_proc_identity does not call _app_ver() - a literal version here is a lie "
                      "the moment the next bump lands")

    def test_the_producer_NEVER_raises(self):
        """_t() returns what its producer returns INCLUDING on the raise path, so a throwing
        producer takes the whole /api/status payload down."""
        real = CA._app_ver
        try:
            CA._app_ver = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
            d = CA._proc_identity()
        finally:
            CA._app_ver = real
        self.assertIsNone(d.get("ver"), "a failed version read must be None, never a guess")
        self.assertEqual(os.getpid(), d.get("pid"), "the rest of the identity was lost")


# THE EXECUTABLE RED-PROOF
RED_PROOF = [
    {
        "why": "law: the stamp is taken at IMPORT. Moving the assignment into the producer makes "
               "every image report the same start, which is the defect this exists to detect.",
        "file": "control_app.py",
        "find": "_PROC_START_MS = int(time.time() * 1000)",
        "replace": "_PROC_START_MS_TAMPERED = int(time.time() * 1000)",
        "matches": 1,
    },
    {
        "why": "law: the payload SERVES it. Renaming the key leaves the producer defined and "
               "reachable by nobody - plumbing with no tap.",
        "file": "control_app.py",
        "find": '"proc": _t("proc", _proc_identity),',
        "replace": '"procTAMPERED": _t("proc", _proc_identity),',
        "matches": 1,
    },
    {
        "why": "law: the version comes from the app, not a literal. A hardcoded version blanks "
               "_disk_ver() and kills the tvd-version-drift lane.",
        "file": "control_app.py",
        "find": "        _v = _app_ver()",
        "replace": '        _v = "v0000"',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
