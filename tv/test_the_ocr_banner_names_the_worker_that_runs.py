# -*- coding: utf-8 -*-
"""REG-2380 — THE OCR BANNER NAMES THE WORKER THAT RUNS, NOT THE MAC'S BINARY.

The agent's startup banner printed `"ON " + OCR_BIN` whenever the OCR lane was available. OCR_BIN is always
tv/bin/ocr_mac, and on Windows _ocr_worker_cmd() runs tv/ocr_win.ps1 through PowerShell instead. MEASURED on a copy of
Dean's control_agent.log taken 2026-10-21: 139 agent boots (v2246 to v3767), every one printing
"ocr lane: ON ...\\tv\\bin\\ocr_mac" - a Mach-O path that can never run there - beside a lane that was reading at
34-50 ms through the PowerShell worker. A log line that names the wrong worker sends whoever reads it after the wrong
thing. The boot's "ocr ... missing" line named tv/bin/ocr_mac on Windows too.

  · DRIVEN: tv_diablo._ocr_lane_tag() under each platform branch of _ocr_worker_cmd() - the same argv
    OcrWorker._spawn runs - on Windows (worker present / missing), on the Mac, and with TV_OCR=0.
  · PINNED by AST: main()'s `ocr lane:` print interpolates the value assigned from _ocr_lane_tag(), main() never
    names OCR_BIN, and the missing-worker line asks _ocr_worker_wanted().
[[label-outlived-referent]]  RED_PROOF below.
"""
import ast
import io
import os
import shutil
import stat
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import tv_diablo as TV  # noqa: E402

SRC = os.path.join(HERE, "tv_diablo.py")


class _Lane(unittest.TestCase):
    """The seams that outrank the platform branch are absent and the lane is switched on, for this test only."""

    def setUp(self):
        env = mock.patch.dict(os.environ, {}, clear=False)
        env.start()
        self.addCleanup(env.stop)
        for k in ("TV_OCR_ARGV", "TV_OCR_BIN"):
            os.environ.pop(k, None)
        on = mock.patch.object(TV, "OCR_ENABLED", True)
        on.start()
        self.addCleanup(on.stop)
        self.d = tempfile.mkdtemp(prefix="ocr-banner-")
        self.addCleanup(shutil.rmtree, self.d, True)


class TheBannerNamesTheWorkerThatRuns(_Lane):

    def test_a_windows_agent_names_the_powershell_worker(self):
        self.assertTrue(os.path.isfile(TV.OCR_WIN_PS1), "premise: tv/ocr_win.ps1 is not beside the agent")
        with mock.patch.object(sys, "platform", "win32"):
            cmd = TV._ocr_worker_cmd()
            tag = TV._ocr_lane_tag()
        self.assertTrue(cmd, "premise: the Windows branch of _ocr_worker_cmd() offers no worker")
        self.assertEqual(tag, "ON " + " ".join(str(x) for x in cmd),
                         "the banner does not name the argv the spawn runs")
        self.assertIn("ocr_win.ps1", tag)
        self.assertNotIn("ocr_mac", tag, "a Windows agent announced the Mac binary again: %r" % tag)

    def test_a_windows_agent_without_its_worker_names_the_missing_ps1(self):
        with mock.patch.object(sys, "platform", "win32"), \
                mock.patch.object(TV, "OCR_WIN_PS1", os.path.join(self.d, "ocr_win.ps1")):
            tag = TV._ocr_lane_tag()
        self.assertTrue(tag.startswith("OFF"), "a Windows agent with no worker said %r" % tag)
        self.assertIn("ocr_win.ps1", tag, "the OFF reason does not name the worker this PC is missing")
        self.assertNotIn("ocr_mac", tag, "a Windows agent was told to build the Mac binary: %r" % tag)

    def test_a_mac_agent_names_its_binary_and_its_flag(self):
        exe = os.path.join(self.d, "ocr_mac")
        with io.open(exe, "w", encoding="utf-8") as fh:
            fh.write("#!/bin/sh\n")
        os.chmod(exe, os.stat(exe).st_mode | stat.S_IXUSR)
        with mock.patch.object(sys, "platform", "darwin"), mock.patch.object(TV, "OCR_BIN", exe):
            tag = TV._ocr_lane_tag()
        self.assertEqual(tag, "ON %s --worker" % exe)

    def test_a_switched_off_lane_says_which_switch(self):
        with mock.patch.object(TV, "OCR_ENABLED", False):
            self.assertEqual(TV._ocr_lane_tag(), "OFF (TV_OCR=0)")


class MainPrintsTheTag(unittest.TestCase):
    """The banner is inside main(), which boots the whole agent, so its join to the helper is pinned by AST."""

    def setUp(self):
        with io.open(SRC, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        mains = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main"]
        self.assertEqual(len(mains), 1, "premise: tv_diablo.main() is not one top-level function")
        self.main = mains[0]

    def _ocr_lane_print_var(self):
        for c in ast.walk(self.main):
            if not (isinstance(c, ast.Call) and getattr(c.func, "id", None) == "print"):
                continue
            for a in c.args:
                if not isinstance(a, ast.JoinedStr):
                    continue
                text = "".join(v.value for v in a.values if isinstance(v, ast.Constant) and isinstance(v.value, str))
                if "ocr lane:" in text:
                    vals = [v.value for v in a.values if isinstance(v, ast.FormattedValue)]
                    return vals[0] if vals else None
        return None

    def test_the_ocr_lane_line_prints_what_the_helper_measured(self):
        v = self._ocr_lane_print_var()
        self.assertIsInstance(v, ast.Name, "premise: main() no longer prints an `ocr lane:` line with a value")
        sources = [a.value for a in ast.walk(self.main) if isinstance(a, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == v.id for t in a.targets)]
        self.assertTrue(sources, "premise: main() never assigns %r" % v.id)
        self.assertTrue(all(isinstance(s, ast.Call) and getattr(s.func, "id", None) == "_ocr_lane_tag"
                            for s in sources),
                        "the `ocr lane:` line prints %r, which main() no longer takes from _ocr_lane_tag()" % v.id)

    def test_main_never_names_the_mac_constant(self):
        hits = [n.lineno for n in ast.walk(self.main) if isinstance(n, ast.Name) and n.id == "OCR_BIN"]
        self.assertEqual(hits, [], "main() names OCR_BIN again (line %s) - a banner that says the Mac binary on "
                                   "every PC" % hits)

    def test_the_missing_worker_line_asks_which_worker(self):
        asks = [c for c in ast.walk(self.main) if isinstance(c, ast.Call)
                and getattr(c.func, "id", None) == "_ocr_worker_wanted"]
        self.assertTrue(asks, "main()'s missing-worker line no longer asks _ocr_worker_wanted()")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-2380 - the banner names OCR_BIN (the Mac binary) whenever the lane is available, on Windows too",
        "file": "tv_diablo.py",
        "find": "        return \"ON \" + \" \".join(str(x) for x in cmd)\n",
        "replace": "        return \"ON \" + OCR_BIN\n",
        "matches": 1,
    },
    {
        "why": "REG-2380 - main() prints its own OCR_BIN tag again instead of the worker the spawn runs",
        "file": "tv_diablo.py",
        "find": "    ocr_tag = _ocr_lane_tag()   # REG-2380",
        "replace": "    ocr_tag = \"ON \" + OCR_BIN if _OCR.available() else \"OFF\"   # REG-2380",
        "matches": 1,
    },
    {
        "why": "REG-2380 - a Windows PC missing ocr_win.ps1 is told to build tv/bin/ocr_mac",
        "file": "tv_diablo.py",
        "find": "    return \"tv/ocr_win.ps1\" if sys.platform.startswith(\"win\") else \"tv/bin/ocr_mac\"\n",
        "replace": "    return \"tv/bin/ocr_mac\"\n",
        "matches": 1,
    },
    {
        "why": "REG-2380 - the boot's missing-worker line hard-codes the Mac binary again",
        "file": "tv_diablo.py",
        "find": "            ev(\"skip\", \"ocr worker missing — Claude-only until %s is present\" % _ocr_worker_wanted())\n",
        "replace": "            ev(\"skip\", \"ocr binary missing — Claude-only until tv/bin/ocr_mac is built\")\n",
        "matches": 1,
    },
]
