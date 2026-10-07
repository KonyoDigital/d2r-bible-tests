# -*- coding: utf-8 -*-
"""REG-1991 - THE GROK "INSTALL FIRST" TIP NAMES THE SHELL OF THE PC IT IS SHOWN ON.

GrokBot (#230 tick 389, v3601, on a Linux console): "The TV·D EYES '⚡ Install first' on this Linux console offers a
Windows PowerShell command" - the tip carried only `irm https://x.ai/cli/install.ps1 | iex`. The console page always
runs on the PC it speaks for (it is served from 127.0.0.1), so its own platform names the shell. REG-1985 made Claude's
sign-in say the same thing on a PC with no Claude CLI.

Drives the REAL _g5InstallLine (lifted from tv/control_ui.html) in node over Windows, Mac and Linux platform strings, and
reads that the Install-first title is built from it.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

UI = os.path.join(HERE, "control_ui.html")
START = "    function _g5InstallLine(plat, ua){"
CALL = "          authBtn.title = 'Grok CLI missing — re-run TV installer, or ' + _g5InstallLine(\n"
CARD = "        bits.push('install Grok CLI via TV installer (or ' + _g5InstallLine("


def _src():
    with io.open(UI, encoding="utf-8") as fh:
        return fh.read()


def _code(src):
    return re.sub(r"/\*.{0,4000}?\*/", lambda m: "\n" * m.group(0).count("\n"), src, flags=re.S)


def _lift(src):
    if src.count(START) != 1:
        return None
    i = src.find(START)
    j = src.find("\n    }\n", i)
    return src[i:j + 6] if j > i else None


CASES = [
    ("Win32", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edg/120", "PowerShell"),
    ("", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "PowerShell"),
    ("MacIntel", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15", "Terminal"),
    ("Linux x86_64", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36", "Terminal"),
    ("", "", "Terminal"),
]


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class AnInstallLineNamesThisPcsShell(unittest.TestCase):

    def test_each_platform_gets_its_own_shell(self):
        fn = _lift(_src())
        self.assertIsNotNone(fn, "_g5InstallLine is gone from tv/control_ui.html (or appears more than once)")
        js = fn + "\nprocess.stdout.write(JSON.stringify(%s.map(function (c) { return _g5InstallLine(c[0], c[1]); })));" % (
            json.dumps([[p, u] for p, u, _w in CASES]))
        p = subprocess.run(["node", "-"], input=js, capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, "the shipped _g5InstallLine would not run: %s" % p.stderr[-600:])
        got = json.loads(p.stdout)
        for (plat, ua, want), line in zip(CASES, got):
            self.assertIn(want, line, "%r / %r was offered %r" % (plat, ua[:30], line))
            if want == "Terminal":
                self.assertNotIn("install.ps1", line, "a Mac or Linux PC was offered the Windows installer")

    def test_the_install_first_tip_is_built_from_it(self):
        code = _code(_src())
        self.assertEqual(code.count(CALL), 1, "the Install-first tip no longer asks _g5InstallLine for this PC's shell")
        self.assertEqual(code.count(CARD), 1, "the EYES card text no longer asks _g5InstallLine for this PC's shell")
        self.assertEqual(code.count("irm https://x.ai/cli/install.ps1 | iex"), 1,
                         "the Windows installer line is written somewhere other than the one helper")


RED_PROOF = [
    {"why": "REG-1991 - the EYES card text prints the bare Windows installer line again",
     "file": "tv/control_ui.html",
     "find": "        bits.push('install Grok CLI via TV installer (or ' + _g5InstallLine(",
     "replace": "        bits.push('install Grok CLI via TV installer (or: irm https://x.ai/cli/install.ps1 | iex)' || (",
     "matches": 1},
    {"why": "REG-1991 - every PC is offered the Windows PowerShell installer again (GrokBot's Linux console, tick 389)",
     "file": "tv/control_ui.html",
     "find": "      return win ? 'in PowerShell: irm https://x.ai/cli/install.ps1 | iex'\n",
     "replace": "      return true ? 'in PowerShell: irm https://x.ai/cli/install.ps1 | iex'\n",
     "matches": 1},
    {"why": "REG-1991 - the Install-first tip stops asking the helper and prints the bare Windows line",
     "file": "tv/control_ui.html",
     "find": "          authBtn.title = 'Grok CLI missing — re-run TV installer, or ' + _g5InstallLine(\n",
     "replace": "          authBtn.title = 'Grok CLI missing — re-run TV installer, or: irm https://x.ai/cli/install.ps1 | iex' || (\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
