#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REG-1880 (#86 gap audit 27) — A DOCTOR ROW THAT MEASURED NOTHING COUNTED AS A PASS.

/api/doctor carried `claude_probe`, a row that passed a literal True with the detail "not probed (doctor never
spawns the CLI)". It was a stub from v801: the doctor must never spawn the Claude CLI, so the probe was never run,
and the row said so in words while its state word said ok. Every machine's "N of N OK" counted it. The ALT read
"20 of 20" with one of the twenty a check nobody made. A row that did not measure is not a pass.

The row is gone. The claude_cli row still says whether the CLI is on the PATH the agent boots with, and the doctor
still never spawns it. The audit named three more rows that pass a literal True. Each of those measures something:
  · port_control - the request is being answered on the control port, so it is up.
  · journal_gens - it lists the generations it found, and a read that raises is a warn (REG-1777).
  · console_window - it names the window mode, and his ruling is that a backgrounded console is healthy.
They stay. [[unknown-stays-unknown]] [[zero-needs-a-denominator]]
"""
import os
import sys
import unittest
from unittest import mock

import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import control_app as ca  # noqa: E402


def _rows():
    # the extract row reads his sweep memory and shelf; this law is about the roster, not that row (REG-1788)
    with mock.patch.object(ca, "_extract_moving_facts", lambda: {"owed": 0, "memory": "absent", "ageKnown": True}):
        return {c["id"]: c for c in ca.doctor_payload()["checks"]}


class ADoctorRowThatMeasuredNothingIsNotAPass(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rows = _rows()

    def test_the_stub_probe_row_is_gone(self):
        self.assertNotIn("claude_probe", self.rows,
                         "claude_probe is back: %r. A row that never ran its probe passed as ok"
                         % (self.rows.get("claude_probe"),))

    def test_no_row_passes_on_a_sentence_that_says_it_did_not_look(self):
        for cid, c in self.rows.items():
            if c.get("ok") is True:
                self.assertNotIn("not probed", str(c.get("detail") or ""),
                                 "%s passes while its own detail says it was not probed: %r" % (cid, c))

    def test_the_cli_is_still_asked_and_never_spawned(self):
        self.assertIn("claude_cli", self.rows, "the row that does measure the CLI went with the stub")
        src = open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        body = src[src.index("def doctor_payload():"):src.index("def doctor_payload():") + 6000]
        self.assertNotIn("subprocess", body.split("# 3) agent bridge port")[0],
                         "the doctor's CLI rows spawn something - the doctor must never run the Claude CLI")


RED_PROOF = [
    {
        "why": "REG-1880 - the stub row comes back: 'not probed' passes as ok and inflates every N of N",
        "file": "control_app.py",
        "find": "    # 3) agent bridge port — OFF is normal, so warn only\n",
        "replace": "    checks.append(_chk(\"claude_probe\", True, \"warn\",\n"
                   "                       \"not probed (doctor never spawns the CLI)\"))\n\n"
                   "    # 3) agent bridge port — OFF is normal, so warn only\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
