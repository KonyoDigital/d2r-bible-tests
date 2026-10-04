# -*- coding: utf-8 -*-
"""A window control that fails says why. A page newer than the process behind it says so.

W on a console with no window says "this console has no window to resize". The fullscreen
control and the minimise control surface the console's own reason, and a fetch that fails
says the window did not answer. Silence is not an answer.

The page is served from disk. When that build differs from the running process, the window
says to reopen TV DIABLO from the Desktop icon. The fleet row shows each PC's window mode,
and a mode outside the known list stays silent.
"""
import json
import os
import subprocess as sp
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.join(HERE, "control_ui.html")
BANNER = ("this window is newer than the console behind it \u2014 reopen TV DIABLO "
          "from the Desktop icon")


def _page():
    with open(UI, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _say():
    src = _page()
    i = src.index("/* DEAN-WINDOW-SAY */") + len("/* DEAN-WINDOW-SAY */")
    j = src.index("/* /DEAN-WINDOW-SAY */", i)
    prog = ("var window = {};\n" + src[i:j] + "\n"
            "process.stdout.write(JSON.stringify({\n"
            "  ok: window._winTold({ok:true, why:'ignored'}, false),\n"
            "  why: window._winTold({ok:false, why:'the frame would not move'}, false),\n"
            "  empty: window._winTold({ok:false}, false),\n"
            "  failed: window._winTold({ok:true}, true),\n"
            "  hidden: window._wWithoutAWindow(true),\n"
            "  shown: window._wWithoutAWindow(false),\n"
            "  banner: window._pageNewerSay({drift:{running:'v1', disk:'v2', drift:true}}),\n"
            "  same: window._pageNewerSay({drift:{running:'v2', disk:'v2', drift:false}}),\n"
            "  missing: window._pageNewerSay({drift:{running:'v2'}}),\n"
            "  none: window._pageNewerSay({}),\n"
            "  full: window._fleetWin({windowMode:'fullscreen', relaunch:{head:'abc1234', autocrlf:'input', porcelain:'M tv/a.py'}, pull:{exit:0, err:'none'}}),\n"
            "  zero: window._fleetWin({windowMode:'front', pull:{exit:0}}),\n"
            "  bad: window._fleetWin({windowMode:'nope'}),\n"
            "  absent: window._fleetWin({})\n"
            "}));\n")
    r = sp.run(["node", "-"], input=prog.encode("utf-8"), stdout=sp.PIPE, stderr=sp.STDOUT,
               timeout=20)
    if r.returncode != 0:
        raise AssertionError(r.stdout.decode("utf-8", "replace")[-800:])
    return json.loads(r.stdout.decode("utf-8"))


class AWindowThatFailsSaysWhy(unittest.TestCase):

    def test_a_failure_is_said_and_a_success_is_quiet(self):
        got = _say()
        self.assertEqual(got["ok"], "")
        self.assertEqual(got["why"], "the frame would not move")
        self.assertEqual(got["empty"], "the window did not answer")
        self.assertEqual(got["failed"], "the window did not answer")
        self.assertEqual(got["hidden"], "this console has no window to resize")
        self.assertEqual(got["shown"], "")

    def test_a_newer_page_names_the_desktop_icon_and_a_match_is_silent(self):
        got = _say()
        self.assertEqual(got["banner"], BANNER)
        self.assertEqual(got["same"], "")
        self.assertEqual(got["missing"], "", "a missing version was called a mismatch")
        self.assertEqual(got["none"], "")

    def test_the_fleet_names_a_known_mode_and_stays_quiet_about_anything_else(self):
        got = _say()
        self.assertEqual(got["full"]["mode"], "fullscreen")
        self.assertEqual(got["full"]["head"], "abc1234")
        self.assertEqual(got["full"]["autocrlf"], "input")
        self.assertEqual(got["full"]["porcelain"], "M tv/a.py")
        self.assertEqual(got["full"]["exit"], 0)
        self.assertEqual(got["zero"]["exit"], 0, "a pull exit of 0 was dropped")
        self.assertIsNone(got["bad"])
        self.assertIsNone(got["absent"])

    def test_the_page_actually_shows_those_sentences(self):
        src = _page()
        i = src.index("async function refresh()")
        refresh = src[i:src.index("async function loadLog()", i)]
        self.assertIn("window._pageNewerSay(st)", refresh,
                      "the banner function exists and refresh never asks it")
        self.assertIn("page-newer", refresh, "refresh computes the sentence and never paints it")
        self.assertIn('id="page-newer" hidden', src, "the banner is visible when there is nothing to say")
        self.assertIn(".page-newer[hidden] { display: none !important; }", src,
                      "the banner's hide rule loses to a later author display without !important")
        k = src.find("k.toLowerCase() !== 'w'")
        self.assertGreater(k, -1)
        block = src[src.rfind("addEventListener('keydown'", 0, k):src.find("}, true);", k)]
        self.assertIn("_wWithoutAWindow", block, "W is silent when the console has no window")
        self.assertIn("_win('fullscreen')", block, "W no longer toggles a window that is up")
        row = src[src.index("var _row = function (m, online)"):src.index("fleet-pending", src.index("var _row = function"))]
        self.assertIn("window._fleetWin", row, "the fleet stores a mode it never draws")
        self.assertIn('class="fleet-win"', src)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "a failed window fetch is silent again",
        "file": "tv/control_ui.html",
        "find": "    if (failed) return 'the window did not answer';\n",
        "replace": "    if (failed) return '';\n",
        "matches": 1,
    },
    {
        "why": "a page newer than the process behind it stops saying so",
        "file": "tv/control_ui.html",
        "find": "    return 'this window is newer than the console behind it \\u2014 reopen TV DIABLO from the Desktop icon';\n",
        "replace": "    return '';\n",
        "matches": 1,
    },
    {
        "why": "refresh stops painting the banner, so the sentence exists and never appears",
        "file": "tv/control_ui.html",
        "find": "      var _newer = window._pageNewerSay ? window._pageNewerSay(st) : '';\n",
        "replace": "      var _newer = '';\n",
        "matches": 1,
    },
    {
        "why": "W is silent again when the console has no window",
        "file": "tv/control_ui.html",
        "find": "        if (window.toast) window.toast(window._wWithoutAWindow ? window._wWithoutAWindow(true) : 'this console has no window to resize');\n",
        "replace": "        ;\n",
        "matches": 1,
    },
]
