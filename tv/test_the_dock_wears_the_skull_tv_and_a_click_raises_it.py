"""v3844 - THE SKULL TV AND THE DOCK CLICK. Elad picked the CRT skull TV as the app icon (2026-10-29 21:25): the Mac
Dock wears tv/appicon.icns and Windows wears tv/appicon.ico on the window, the taskbar and the shortcut, both cut from
the one source. And a click on the console's Dock icon (21:22, "does not raise the window") now raises it above every
app: the reopen event activates the app and orders every visible or minimised console window to the front, and a
console in the background service comes back through console_to_front."""
from __future__ import annotations

import os
import struct
import time
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import control_app  # noqa: E402


class _Win:
    def __init__(self, visible=True, mini=False):
        self.visible, self.mini, self.log = visible, mini, []

    def isVisible(self):
        return self.visible

    def isMiniaturized(self):
        return self.mini

    def deminiaturize_(self, _):
        self.log.append("demini")
        self.mini = False

    def makeKeyAndOrderFront_(self, _):
        self.log.append("key-front")

    def orderFrontRegardless(self):
        self.log.append("front-regardless")


class _App:
    def __init__(self, wins):
        self.wins, self.active = wins, None

    def activateIgnoringOtherApps_(self, flag):
        self.active = flag

    def windows(self):
        return self.wins


class TheDockClickRaisesTheConsole(unittest.TestCase):
    def test_a_click_activates_the_app_and_raises_every_console_window(self):
        shown, mini, gone = _Win(), _Win(visible=False, mini=True), _Win(visible=False)
        app = _App([shown, mini, gone])
        did = control_app._mac_raise_windows(app)
        self.assertIs(app.active, True, "the app was not brought above the other apps")
        self.assertEqual(shown.log, ["key-front", "front-regardless"])
        self.assertEqual(mini.log, ["demini", "key-front", "front-regardless"], "a minimised window stays down")
        self.assertEqual(gone.log, [], "a closed window must not be resurrected by a Dock click")
        self.assertEqual(did.count("raised"), 2)

    def test_the_handler_is_installed_before_the_window_starts(self):
        src = open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        a = src.index("_mac_wear_icon_and_take_dock_clicks()\n", src.index("if globals().get(\"_HIDDEN_BOOT\"):"))
        self.assertLess(a, src.index("webview.start(**_start_kw)"))
        self.assertIn("0x61657674, 0x72617070", src, "the handler is not on the reopen event ('aevt','rapp')")
        self.assertIn("setApplicationIconImage_", src)
        front = src[src.index("def console_to_front("):src.index("def _refullscreen_after_restore(")]
        self.assertIn("activateIgnoringOtherApps_", front, "a launcher 'front' leaves the console behind other apps")

    def test_one_click_raises_once_and_the_event_is_answered(self):
        calls = []
        old_bg, old_ctf, old_last = dict(control_app._BACKGROUND), control_app.console_to_front, control_app._DOCK_LAST["t"]
        try:
            control_app._BACKGROUND["on"] = True
            control_app.console_to_front = lambda **k: calls.append(k)
            control_app._DOCK_LAST["t"] = 0.0
            r = [control_app._mac_on_dock_click(now=t) for t in (100.0, 100.6, 103.0)]
            time.sleep(0.3)
        finally:
            control_app._BACKGROUND.clear(); control_app._BACKGROUND.update(old_bg)
            control_app.console_to_front = old_ctf
            control_app._DOCK_LAST["t"] = old_last
        self.assertEqual(r, [["front"], ["same-click"], ["front"]], "a repeat reopen raised again: %r" % r)
        self.assertEqual(len(calls), 2, calls)
        src = open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        self.assertIn("descriptorWithBoolean_(True), 0x2d2d2d2d", src, "the reopen event is handled but never answered")


def _ico_sizes(path):
    with open(path, "rb") as f:
        head = f.read(6)
        _, kind, n = struct.unpack("<HHH", head)
        sizes = []
        for _ in range(n):
            w, h = struct.unpack("<BB", f.read(16)[:2])
            sizes.append((w or 256, h or 256))
    return kind, sizes


class TheIconIsTheSkullTv(unittest.TestCase):
    def test_windows_has_every_size_the_shell_asks_for(self):
        kind, sizes = _ico_sizes(os.path.join(HERE, "appicon.ico"))
        self.assertEqual(kind, 1, "appicon.ico is not an icon resource")
        for want in (16, 24, 32, 48, 256):
            self.assertIn((want, want), sizes, "appicon.ico has no %dpx frame" % want)

    def test_the_mac_icon_is_a_real_icns_with_a_retina_frame(self):
        with open(os.path.join(HERE, "appicon.icns"), "rb") as f:
            data = f.read()
        self.assertEqual(data[:4], b"icns")
        self.assertEqual(struct.unpack(">I", data[4:8])[0], len(data), "a truncated icns")
        self.assertIn(b"ic10", data, "no 1024px (512@2x) frame - the Dock would be blurry")
        self.assertEqual(control_app.APP_ICON_ICNS, os.path.join(HERE, "appicon.icns"))

    def test_the_installers_still_hand_out_these_files(self):
        self.assertIn("tv\\appicon.ico", open(os.path.join(HERE, "install-tvd.ps1"), encoding="utf-8").read())
        self.assertIn("tv/appicon.icns", open(os.path.join(HERE, "install-tvd.sh"), encoding="utf-8").read())


RED_PROOF = [
    {"why": "a repeat reopen raises again", "file": "tv/control_app.py",
     "find": "    if t - _DOCK_LAST[\"t\"] < 1.5:", "replace": "    if False:", "matches": 1},
]

if __name__ == "__main__":
    unittest.main()
