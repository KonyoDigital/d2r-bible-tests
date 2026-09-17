#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""★ v3271 — THE CONSOLE CAN BE MINIMISED AND WINDOWED ON WINDOWS AND LINUX, NOT ONLY ON A MAC.

HIS REPORT, 2026-09-17, across three machines:

    "on windows theres no way to minimize or windows mode it, it automatically opens fullscreen
     which is good but it needs to have an option available ... its like frameless when opened on
     linux pc on grokbot too ... only on my macbook the macbook has its own option to windows it
     regardless"

He described the platform difference precisely. `create_window(fullscreen=True)` is set
UNCONDITIONALLY unless `TV_WINDOWED` is in the environment, and:

    macOS     keeps its traffic-light controls in fullscreen, so he can always escape
    Windows   fullscreen means NO TITLEBAR — no minimise, no restore
    Linux     the same

So an escape hatch existed and was reachable only by setting an env var BEFORE launch, which is no
use at all from inside a running window. **This is the second report.** v3179 already recorded him
saying *"now i cant minimize or window mode the console"* after v3175 tried frameless; that attempt
was reverted and the unconditional fullscreen underneath it was left in place.

MEASURED on the installed pywebview: `Window.minimize`, `Window.restore` and
`Window.toggle_fullscreen` all exist — so this needed no new dependency and no relaunch, only a
door he can reach.

⚠ The controls are HIDDEN where they cannot act. `/api/window` answers ok:false with a reason on a
headless console, in `--no-open`, and in a browser tab (which has its own chrome), and a button
that does nothing is worse than no button.
"""

import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

SRC = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()


def _py_only(src):
    """Python with # comments stripped, so a law never reads its own commentary. -> str"""
    out = []
    for line in src.split("\n"):
        q = None
        cut = None
        for i, ch in enumerate(line):
            if q:
                if ch == q and (i == 0 or line[i - 1] != "\\"):
                    q = None
            elif ch in "\"'":
                q = ch
            elif ch == "#":
                cut = i
                break
        out.append(line[:cut] if cut is not None else line)
    return "\n".join(out)


def _js_only(src):
    """JS/HTML with /* ... */ comments removed. -> str"""
    out, i = [], 0
    while True:
        j = src.find("/*", i)
        if j < 0:
            out.append(src[i:]); break
        out.append(src[i:j])
        k = src.find("*/", j)
        if k < 0:
            break
        i = k + 2
    return "".join(out)


class HisWindowIsHisOnEveryPlatform(unittest.TestCase):

    def setUp(self):
        import control_app as ca
        self.ca = ca
        self._prev = ca.__dict__.get("_MAIN_WIN")
        self.addCleanup(lambda: ca.__dict__.__setitem__("_MAIN_WIN", self._prev))

    class _Win(object):
        def __init__(self):
            self.calls = []

        def minimize(self):
            self.calls.append("minimize")

        def restore(self):
            self.calls.append("restore")

        def toggle_fullscreen(self):
            self.calls.append("toggle_fullscreen")

    def _with_window(self):
        w = self._Win()
        self.ca.__dict__["_MAIN_WIN"] = w
        return w

    # ── the behaviour ───────────────────────────────────────────────────────────────────────
    def test_every_action_reaches_the_pywebview_method_that_performs_it(self):
        """⚠ BEHAVIOURAL, not a presence check: it calls the function and reads what the window
        was actually told to do. A law asserting the NAME `toggle_fullscreen` appears would stay
        green over a handler that never calls it. [[presence-law-vs-reachability-law]]"""
        w = self._with_window()
        for ask, expect in (("minimize", "minimize"),
                            ("restore", "restore"),
                            ("fullscreen", "toggle_fullscreen")):
            r = self.ca.window_action(ask)
            self.assertTrue(r["ok"], "%r did not act: %s" % (ask, r.get("why")))
            self.assertEqual(r["did"], expect)
        self.assertEqual(w.calls, ["minimize", "restore", "toggle_fullscreen"],
                         "an action reported success without the window being told to do it")

    def test_a_console_with_NO_WINDOW_says_so_instead_of_claiming_success(self):
        """A headless console, `--no-open`, or a browser tab. ok:false with a reason — never a
        green that hides a control which did nothing. [[unknown-stays-unknown]]"""
        self.ca.__dict__["_MAIN_WIN"] = None
        r = self.ca.window_action("minimize")
        self.assertFalse(r["ok"])
        self.assertIsNone(r["did"])
        self.assertIn("no native window", r["why"])

    def test_a_BAD_ACTION_is_named_as_such_even_where_there_is_no_window(self):
        """⚠⚠ THE ORDER IS THE LAW. The first cut checked for a window FIRST, so
        `window_action("explode")` on a headless console answered "there is no native window" — a
        true sentence about the wrong question, which sends the caller to fix the wrong thing.
        [[a-wrong-answer-skips-the-fallback]]"""
        self.ca.__dict__["_MAIN_WIN"] = None
        r = self.ca.window_action("explode")
        self.assertFalse(r["ok"])
        self.assertIn("not a window action", r["why"])
        self.assertNotIn("no native window", r["why"])

    def test_an_action_that_RAISES_is_reported_not_swallowed(self):
        class _Angry(object):
            def minimize(self):
                raise RuntimeError("nope")
        self.ca.__dict__["_MAIN_WIN"] = _Angry()
        r = self.ca.window_action("minimize")
        self.assertFalse(r["ok"])
        self.assertIn("RuntimeError", r["why"])

    def test_a_build_WITHOUT_the_method_says_unavailable_rather_than_failed(self):
        class _Old(object):
            pass
        self.ca.__dict__["_MAIN_WIN"] = _Old()
        r = self.ca.window_action("fullscreen")
        self.assertFalse(r["ok"])
        self.assertIn("no Window.toggle_fullscreen", r["why"])

    # ── the banner he asked to be rid of ────────────────────────────────────────────────────
    def test_an_unanswerable_message_is_NEVER_SENT(self):
        """★ v3281 — THE ONLY REAL PROTECTION AGAINST THE v3206 LAUNCH CRASH.

        v3207 disabled the Mac chrome hooks and said exactly why, while not having this: *"an
        Objective-C exception or a bad selector does NOT raise a Python exception — it kills the
        process. A Python try cannot catch a SIGTRAP, so 'individually wrapped' bought nothing
        against the failure that actually happened."*

        `respondsToSelector_` asks BEFORE sending, so an unanswerable message is never sent and
        there is no exception to catch. An uncatchable process death becomes an ordinary `if`.
        """
        can = self.ca._objc_can
        self.assertFalse(can(None, "x:"), "a nil object was treated as answerable")
        self.assertFalse(can(object(), "x:"), "an object with no respondsToSelector_ passed")

        class _Raises(object):
            def respondsToSelector_(self, s):
                raise RuntimeError("boom")

        self.assertFalse(can(_Raises(), "x:"),
                         "a raising probe was treated as a yes — the guard must fail CLOSED")

        class _Yes(object):
            def respondsToSelector_(self, s):
                return True

        self.assertTrue(can(_Yes(), "x:"), "a genuine yes was refused, so the fix does nothing")

    def test_EVERY_dynamic_call_in_the_tint_is_gated(self):
        """⚠ The tint sends four messages. Three are documented NSWindow API; the fourth walks the
        PRIVATE theme frame — `contentView().superview().subviews().lastObject()` — and that is the
        crash candidate. Every hop is checked, so a macOS that changes the hierarchy produces
        NOTHING rather than a message to something that cannot answer it.

        MEASURED on his macOS against a real NSWindow: all three window selectors exist and the
        theme frame's last subview is an NSKVONotifying_NSTitlebarContainerView which DOES respond
        to setBackgroundColor:. The guard stays anyway — the next macOS is the one that changes it.
        """
        src = _py_only(SRC)
        i = src.find("def _mac_tint_caption(")
        self.assertGreater(i, -1, "the Mac tint is gone or renamed")
        j = src.find("def _mac_force_fullscreen(", i)
        body = src[i:j if j > i else i + 3000]
        for sel in ("setTitlebarAppearsTransparent:", "setTitleVisibility:", "setBackgroundColor:"):
            self.assertIn('_objc_can(', body, "the tint sends messages without asking first")
            self.assertIn(sel, body, "the tint no longer sends %s" % sel)
        for hop in ("contentView", "superview", "subviews"):
            self.assertIn('_objc_can(native, "contentView")' if hop == "contentView"
                          else '"%s")' % hop, body,
                          "the private theme-frame hop %r is walked unguarded" % hop)

    def test_the_TINT_is_armed_by_default_and_the_UNTESTED_hook_is_NOT(self):
        """★ HIS RULING, 2026-09-17: *"what banner? i dont wnat the banner uptop i want it clean"*.

        ⚠ v3207 disabled TWO hooks together after one crash and never isolated which died. They
        are not equal risks: the tint is documented API plus one guarded private hop;
        `_mac_force_fullscreen` is untested AND buys nothing, because fullscreen is already the
        default. So the tint is armed by default and that one stays behind the opt-in.
        """
        src = _py_only(SRC)
        i = src.find("win.events.shown += _mac_tint_caption")
        self.assertGreater(i, -1, "the tint is never armed, so the banner stays")
        guard = src[max(0, i - 400):i]
        self.assertIn('not in ("0", "false", "no", "off")', guard,
                      "the tint is behind an opt-IN again, so his console still shows the banner "
                      "unless he sets an env var before launch")
        j = src.find("win.events.shown += _mac_force_fullscreen")
        self.assertGreater(j, -1, "the untested hook vanished rather than staying opt-in")
        g2 = src[max(0, j - 300):j]
        self.assertIn('in ("1", "true", "yes", "on")', g2,
                      "the UNTESTED fullscreen hook is now armed by default — it was never "
                      "cleared of the v3206 crash")

    def test_he_can_turn_the_tint_OFF_without_editing_code(self):
        """⚠ An opt-OUT, because he asked for clean. If it ever misbehaves on launch he needs a
        way back in that is not a code edit."""
        src = _py_only(SRC)
        i = src.find("win.events.shown += _mac_tint_caption")
        guard = src[max(0, i - 400):i]
        self.assertIn("TV_MAC_CHROME", guard,
                      "there is no env switch to disable the tint, so a launch problem would need "
                      "a code change to escape")

    # ── the joins ───────────────────────────────────────────────────────────────────────────
    def test_the_route_EXISTS_and_reaches_the_helper(self):
        """⚠ a helper nobody routes to is [[the-unjoined-end]]: built, correct, unreachable."""
        src = _py_only(SRC)
        self.assertIn('if path == "/api/window":', src, "the window route is gone or renamed")
        i = src.find('if path == "/api/window":')
        blk = src[i:i + 700]
        self.assertIn("window_action(", blk,
                      "the route does not call the helper, so the buttons reach nothing")

    def test_the_UI_has_BOTH_controls_and_they_POST_to_the_route(self):
        ui = _js_only(UI)
        self.assertIn('id="win-min"', ui, "there is no minimise control")
        self.assertIn('id="win-full"', ui, "there is no fullscreen/windowed control")
        self.assertIn("'/api/window'", ui, "the controls do not call the route")
        self.assertIn("'minimize'", ui)
        self.assertIn("'fullscreen'", ui)

    def test_the_controls_are_HIDDEN_until_the_console_says_it_HAS_a_window(self):
        """⚠ a button that does nothing is worse than no button: in a browser tab the page has its
        own chrome and these would be inert."""
        ui = _js_only(UI)
        self.assertIn('id="win-ctl" hidden', ui,
                      "the window controls are shown before anything confirms a window exists")
        i = ui.find("var box = $('win-ctl')")
        self.assertGreater(i, -1, "the probe that reveals the controls is gone")
        blk = ui[i:i + 900]
        self.assertIn("box.hidden = false", blk,
                      "nothing ever reveals the controls, so they are permanently invisible")
        self.assertIn("d.ok", blk,
                      "the controls are revealed without asking whether the action succeeded")

    def test_FULLSCREEN_IS_STILL_THE_DEFAULT_he_asked_for(self):
        """⚠ HIS WORDS: "it automatically opens fullscreen WHICH IS GOOD". The fix adds a door;
        it must not change what he opens into. [[design-is-fine-until-he-says]]"""
        src = _py_only(SRC)
        self.assertIn('kwargs["fullscreen"] = True', src,
                      "fullscreen is no longer the default he explicitly said he likes")


if __name__ == "__main__":
    unittest.main(verbosity=2)
