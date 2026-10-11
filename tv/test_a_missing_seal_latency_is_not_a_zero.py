# -*- coding: utf-8 -*-
"""REG-2157 (#277) - a measured seal of zero is not a missing seal.

sealed-in is how long KAI took after the run ended. ran is t0 to t1. plays is
the film. The engine dropped a gap of 0, so an instant seal looked like no
seal, and a short seal printed as seconds while the other clocks print NmNNs.
A missing seal stays off the chip. A measured 0 prints 0m00s.

Drives the shipped _sealSay, cut from control_ui.html and run in node, and
seal_latency_ms, cut from control_app.py and exec'd on its own.
"""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
from cb_node_harness import NODE  # noqa: E402

UI = os.path.join(HERE, "control_ui.html")
APP = os.path.join(HERE, "control_app.py")
CAP = 30 * 60 * 1000


def _src(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _js_fn(src, signature):
    start = src.find(signature)
    if start < 0:
        raise AssertionError("%s is gone" % signature)
    if src.find(signature, start + 1) != -1:
        raise AssertionError("%s is declared more than once" % signature)
    i = src.find("{", start)
    depth = 0
    for j in range(i, len(src)):
        ch = src[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return src[start:j + 1]
    raise AssertionError("%s never closed" % signature)


def _py_fn(src):
    signature = "def seal_latency_ms("
    start = src.find(signature)
    if start < 0:
        raise AssertionError("seal_latency_ms is gone - sealed-in has no one home")
    if src.find(signature, start + 1) != -1:
        raise AssertionError("seal_latency_ms is declared more than once")
    nxt = src.find("\ndef ", start + 1)
    if nxt < 0:
        raise AssertionError("seal_latency_ms never closed")
    return src[start:nxt]


def _say(cases):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    ui = _src(UI)
    js = (
        "%s\n%s\nconsole.log(JSON.stringify(%s.map(function(ms){\n"
        "  return {say: _sealSay(ms), chip: _dossierSealLatency({sealMs: ms})};\n"
        "})));\n"
    ) % (
        _js_fn(ui, "function _sealSay(ms){"),
        _js_fn(ui, "function _dossierSealLatency(sm){"),
        json.dumps(cases),
    )
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("_sealSay did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


def _latency():
    ns = {}
    exec(_py_fn(_src(APP)), ns)
    return ns["seal_latency_ms"]


class AMissingSealLatencyIsNotAZero(unittest.TestCase):

    def test_a_missing_seal_stays_off_the_chip_and_a_measured_zero_prints(self):
        missing, negative, zero, twenty_six, ten = _say([None, -1, 0, 26000, 618000])
        self.assertIsNone(missing["say"])
        self.assertEqual(missing["chip"], "")
        self.assertIsNone(negative["say"])
        self.assertEqual(negative["chip"], "")
        self.assertEqual(zero["say"], "0m00s")
        self.assertIn("sealed in 0m00s", zero["chip"])
        self.assertNotIn("0s", zero["chip"].replace("0m00s", ""))
        self.assertEqual(twenty_six["say"], "0m26s")
        self.assertIn("sealed in 0m26s", twenty_six["chip"])
        self.assertNotIn("26s", twenty_six["chip"].replace("0m26s", ""))
        self.assertEqual(ten["say"], "10m18s")
        self.assertIn("sealed in 10m18s", ten["chip"])

    def test_the_seal_chip_asks_its_own_clock(self):
        s = _src(UI)
        self.assertEqual(s.count("function _sealSay(ms){"), 1)
        self.assertEqual(s.count("function _dossierSealLatency(sm){"), 1)
        seal = s.find("function _dossierSealLatency(sm){")
        nxt = s.find("function _dossierRegret(sm){", seal)
        body = s[seal:nxt]
        self.assertIn("_sealSay(sm && sm.sealMs)", body)
        self.assertIn("sealed in ", body)
        self.assertNotIn("_runSpanSay", body, "sealed-in was folded into the run length")
        self.assertNotIn("_playSay", body, "sealed-in was folded into the film clock")
        self.assertNotIn("s + 's'", body, "a short seal still uses a different unit")

    def test_a_measured_zero_gap_is_a_seal_and_a_reseal_is_not(self):
        fn = _latency()
        end = 1700000000000
        self.assertIsNone(fn(None, end))
        self.assertIsNone(fn(end + 1000, None))
        self.assertIsNone(fn(True, end))
        self.assertIsNone(fn(end, True))
        self.assertIsNone(fn(end, 0))
        self.assertIsNone(fn(end - 1, end))
        self.assertEqual(fn(end, end), 0)
        self.assertEqual(fn(end + 618000, end), 618000)
        self.assertEqual(fn(end + CAP, end), CAP)
        self.assertIsNone(fn(end + CAP + 1, end))
        app = _src(APP)
        self.assertEqual(app.count("def seal_latency_ms("), 1)
        self.assertEqual(app.count("_seal_ms = seal_latency_ms("), 1)
        self.assertNotIn("0 < _dlt", app, "a measured zero is dropped again")


RED_PROOF = [
    {
        "why": "REG-2157 - a missing seal prints 0m00s again, so an unknown seal looks measured",
        "file": "tv/control_ui.html",
        "find": "    if (ms == null || !(+ms >= 0)) return null;\n",
        "replace": "    if (ms == null || !(+ms >= 0)) return '0m00s';\n",
        "matches": 1,
    },
    {
        "why": "REG-2157 - a measured zero-length seal is hidden as if the clock were missing",
        "file": "tv/control_ui.html",
        "find": "    var whole = Math.round(+ms / 1000);\n    return Math.floor(whole / 60) + 'm' + ('0' + (whole % 60)).slice(-2) + 's';\n",
        "replace": "    var whole = Math.round(+ms / 1000);\n    if (!whole) return null;\n    return Math.floor(whole / 60) + 'm' + ('0' + (whole % 60)).slice(-2) + 's';\n",
        "matches": 1,
    },
    {
        "why": "REG-2157 - the seal chip borrows the run length again",
        "file": "tv/control_ui.html",
        "find": "    var txt = _sealSay(sm && sm.sealMs);\n    if (txt == null) return '';\n",
        "replace": "    var txt = _runSpanSay(sm.t0, sm.t1) || '0m00s';\n",
        "matches": 1,
    },
    {
        "why": "REG-2157 - a measured zero gap is dropped again, so an instant seal looks missing",
        "file": "tv/control_app.py",
        "find": "    if dlt < 0 or dlt > cap_ms:  # REG-2157 measured 0 still returns\n        return None\n",
        "replace": "    if dlt <= 0 or dlt > cap_ms:  # REG-2157 measured 0 still returns\n        return None\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
