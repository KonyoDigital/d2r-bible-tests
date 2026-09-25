# -*- coding: utf-8 -*-
"""#178 (his ruling 2026-09-25: "the banner reads the heap") — ONE WRITER FOR THE HOST OS.

GrokBot's Linux seat read `machine: windows` from the board_build door beside a ribbon saying LINUX and filed it as
two writers contradicting each other. They answered two questions (D2R_MACHINE is the STORAGE world; the ribbon names
the OS), but the OS itself DID have two writers: the ribbon's own UA test and the door's raw navigator.platform.
Now it is computed ONCE on the heap (window.D2R_HOST_OS, beside D2R_MACHINE); the ribbon renders it and the door
reports it. Verified on pixels with an emulated Linux host: "🐧 LINUX — its own world · Mac untouched".

  · DRIVEN (node, the REAL D2R_HOST_OS block from bible.html) across Mac / Linux / Windows / Android hosts.
  · The ribbon's word comes from the heap, never from its own navigator probe (comment-stripped source).
  · The door reads the heap's reading first; the raw probe only for a board older than the field.
RED_PROOF below.
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
BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")
NODE = shutil.which("node")


def _src():
    with io.open(BIBLE, encoding="utf-8") as f:
        return f.read()


def _host_block(src):
    i = src.index("window.D2R_HOST_OS = (function(){")
    j = src.index("\n})();", i)
    return src[i:j + len("\n})();")]


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class TheHostIsReadOnce(unittest.TestCase):

    def _host(self, ua, plat, uad=None):
        nav = {"userAgent": ua, "platform": plat}
        if uad:
            nav["userAgentData"] = {"platform": uad}
        # a function scope: Node 21+ has a global `navigator` a top-level `var` cannot replace
        js = "(function(window, navigator){\n%s\nconsole.log(JSON.stringify(window.D2R_HOST_OS));\n})({}, %s);" % (
            _host_block(_src()), json.dumps(nav))
        r = subprocess.run([NODE, "-e", js], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise AssertionError("node could not run the shipped block - UNKNOWN: %s" % r.stderr[:300])
        return json.loads(r.stdout.strip().splitlines()[-1])

    def test_each_host_is_named(self):
        self.assertEqual(self._host("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", "MacIntel", "macOS"), "MAC")
        self.assertEqual(self._host("Mozilla/5.0 (X11; Linux x86_64)", "Linux x86_64", "Linux"), "LINUX")
        self.assertEqual(self._host("Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Win32", "Windows"), "WINDOWS")
        self.assertEqual(self._host("Mozilla/5.0 (Linux; Android 14; Pixel 8)", "Linux armv8l", "Android"), "ANDROID")


class OneWriter(unittest.TestCase):

    def test_the_ribbon_renders_the_heap(self):
        code = re.sub(r"/\*.{0,4000}?\*/", " ", _src(), flags=re.S)
        i = code.index("var _wm = (function(){")
        blk = code[i:code.index("})();", i)]
        self.assertIn("window.D2R_HOST_OS", blk, "the ribbon no longer reads the heap's host")
        self.assertNotIn("navigator", blk, "the ribbon derives its own host again - a second writer")

    def test_the_door_reports_the_heap(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as f:
            ca = f.read()
        i = ca.index("np=String(_ctx.D2R_HOST_OS||'')")
        j = ca.index("_n.userAgentData&&_n.userAgentData.platform", i)
        self.assertLess(i, j, "the door re-probes navigator before the heap's reading")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#178 - the ribbon stops reading the heap: the word on screen has its own writer again",
        "file": "bible.html",
        "find": "    var w = window.D2R_HOST_OS || 'THIS MACHINE';\n",
        "replace": "    var w = (navigator.platform || 'THIS MACHINE');\n",
        "matches": 1,
    },
    {
        "why": "#178 - a Linux host is named WINDOWS again (the ribbon's original lie)",
        "file": "bible.html",
        "find": "    if (/linux|x11|ubuntu|debian/i.test(s)) return 'LINUX';\n",
        "replace": "",
        "matches": 1,
    },
]
