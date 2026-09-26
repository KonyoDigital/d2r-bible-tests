# -*- coding: utf-8 -*-
"""THE `measured` BIT CROSSES THE RELAY — the sixth joint of the fleet tally.

Found by the doctor row "a tally agrees with its own ledger verdict", read live on his console 2026-09-24:
3 of 3 judged rows published counts their own ledger verdict refuses, measured=None on every one. The row's
own docstring blamed consoles older than v3389, but the fleet showed v3499 consoles with no `measured`
either. The tally seals it (control_app._seal_tally_verdict); the site function that stores fleet rows
(functions/api/console.js) copies the tally through a FIXED KEY LIST that forwarded ledgerVerdict and
onOwnerSeed but not measured / measuredWhy - built at both ends, never joined, for the sixth time on this
one feature.

  · DRIVEN (node, the REAL shaper extracted from console.js): a sealed tally keeps measured False with its
    reason, True stays True, and a non-boolean arrives as null (UNKNOWN), never as a guessed value.
RED_PROOF below.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

WORKER = os.path.join(ROOT, "functions", "api", "console.js")


def _shaper():
    with io.open(WORKER, encoding="utf-8") as f:
        src = f.read()
    i = src.index("    tally: (function (t) {")
    j = src.index("    })(body.tally),", i)
    return "(" + src[i + len("    tally: "):j + len("    })")] + ")"


def _shape(tally):
    js = "var shape = %s;\nconsole.log(JSON.stringify(shape(%s)));" % (_shaper(), json.dumps(tally))
    r = subprocess.run([shutil.which("node"), "-"], input=js, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("node could not run the relay's shaper - UNKNOWN, not passing: %s" % r.stderr[:500])
    return json.loads(r.stdout.strip().splitlines()[-1])


def _tally(**extra):
    t = {"ok": True, "at": 1790000000000, "sets": {"have": 0, "total": 135},
         "uniques": {"have": 0, "total": 403}, "runewords": {"have": 0, "total": 99},
         "ledgerVerdict": {"ok": False}}
    t.update(extra)
    return t


@unittest.skipIf(shutil.which("node") is None, "node is absent - this law is UNMEASURED, not passing")
class TheMeasuredBitCrossesTheRelay(unittest.TestCase):

    def test_premise_the_counts_cross(self):
        out = _shape(_tally(measured=False))
        self.assertEqual(out["sets"], {"have": 0, "total": 135})

    def test_a_refused_tally_keeps_measured_false_and_its_reason(self):
        out = _shape(_tally(measured=False, measuredWhy="these counts are not a measurement: sets were never synced"))
        self.assertIs(out.get("measured"), False, "the relay dropped `measured` - every fleet row reads MISSING")
        self.assertIn("never synced", out.get("measuredWhy") or "")

    def test_a_measured_tally_stays_true(self):
        self.assertIs(_shape(_tally(measured=True, ledgerVerdict={"ok": True})).get("measured"), True)

    def test_a_non_boolean_is_unknown_never_guessed(self):
        self.assertIsNone(_shape(_tally(measured="yes")).get("measured"))
        self.assertIsNone(_shape(_tally()).get("measured"))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "the relay drops `measured` again - the sealed verdict exists at both ends and never arrives (the sixth joint)",
        "file": "functions/api/console.js",
        "find": "                    measured: (typeof t.measured === 'boolean') ? t.measured : null,\n",
        "replace": "",
        "matches": 1,
    },
]
