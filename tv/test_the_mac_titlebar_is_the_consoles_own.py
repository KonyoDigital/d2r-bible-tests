# -*- coding: utf-8 -*-
"""THE GREY "TV DIABLO" STRIP, AND WHY THIS ONE IS NOT ANOTHER GUESS AT WINDOW FLAGS.

Konyo reported it twice: *"this TV diablo banner on top is now here when it wasnt"*, and again
2026-09-16 with two screenshots — *"the banner uptop TV DIABLO still ontop... it should be
fullscreened and just the console without that banner ontop too so fix that too"*.

⚠⚠ THE FIRST ATTEMPT COST HIM HIS WINDOW BUTTONS. v3175 paired `frameless` with `fullscreen` to
kill it. He answered *"now i cant minimize or window mode the console"* AND THE STRIP WAS STILL
THERE, so it paid a real price for nothing. v3179 reverted it and wrote the instruction this file
exists to honour: *"the strip is NOT the pywebview frame; it survives framelessness, so it is
something else and will be found by LOOKING rather than by guessing at window flags again."*

LOOKED. `webview/platforms/cocoa.py` (pywebview 6.2.1, measured on his Mac):

    if window.frameless:
        ... hide the three buttons ...
    else:
        # Set the titlebar color (so that it does not change with the window color)
        self.window.contentView().superview().subviews().lastObject().setBackgroundColor_(
            AppKit.NSColor.windowBackgroundColor()
        )

pywebview deliberately paints the titlebar container with the SYSTEM window background — a light
grey — above a #070605 console. And the branch it lives in is why framelessness looked like it
failed: frameless takes the OTHER branch, so v3175 removed the paint and the buttons together,
and the buttons were what he noticed.

So the fix reverses THAT LINE, down THAT PATH, and nothing else — keeping the frame, keeping the
buttons. [[source-reading-guard]] [[borrowed-surface]]

⚠ AND THE SECOND HALF: he asked for fullscreen and the screenshot shows a menu bar and traffic
lights. `create_window(fullscreen=True)` calls `toggle_fullscreen()` once at the end of cocoa's
`create()`, and it can be refused when the app is not frontmost. A one-shot request that can be
silently refused is UNKNOWN, not honoured. [[unknown-stays-unknown]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

APP = os.path.join(HERE, "control_app.py")


def _between(src, start, end):
    """both ends anchored — a fixed window past the anchor reads a grown region as ABSENT.
    [[source-window-shortcut]]"""
    i = src.find(start)
    if i < 0:
        return ""
    j = src.find(end, i + len(start))
    return src[i:j] if j > i else ""


def _code_only(src):
    """my own prose is not evidence about my own code. [[carved-skill-unloaded-is-unapplied]]

    Docstrings and # comments are stripped before any assertion reads the text. This law BANS the
    word `frameless`, and the docstrings above explain at length why frameless was wrong — so
    without this the guard would fail on its own explanation, which is the fifth time that shape
    has bitten this repo.
    """
    q = chr(34) * 3
    src = re.sub(re.escape(q) + ".*?" + re.escape(q), " ", src, flags=re.S)
    return re.sub(r"(?m)^\s*#.*$", " ", src)


class TheMacTitlebarIsTheConsolesOwn(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with io.open(APP, encoding="utf-8") as fh:
            cls.src = fh.read()
        cls.tint = _between(cls.src, "def _mac_tint_caption():", "def _mac_force_fullscreen():")
        cls.full = _between(cls.src, "def _mac_force_fullscreen():", "\ndef _win_tint_caption")
        assert cls.tint, "_mac_tint_caption is gone — this law is reading nothing"
        assert cls.full, "_mac_force_fullscreen is gone — this law is reading nothing"

    # ── the thing v3175 got wrong, pinned so it cannot be got wrong the same way ──────────
    def test_it_does_NOT_go_frameless(self):
        """frameless hides close, minimise and zoom. He said so, in those words."""
        code = _code_only(self.tint) + _code_only(self.full)
        self.assertNotIn("frameless", code,
                         "the mac caption fix is reaching for frameless again — that is what "
                         "cost him minimise and window mode in v3175, and it did not remove the "
                         "strip either")
        for btn in ("NSWindowCloseButton", "NSWindowMiniaturizeButton", "NSWindowZoomButton"):
            self.assertNotIn(btn, code,
                             "the fix is hiding %s — his window buttons are not cosmetics" % btn)

    def test_it_reverses_pywebviews_own_line_down_pywebviews_own_path(self):
        """a different path would paint a different view and leave the strip."""
        code = _code_only(self.tint)
        self.assertIn("contentView().superview().subviews().lastObject().setBackgroundColor_",
                      code,
                      "the repaint no longer walks the same lookup pywebview uses, so it is "
                      "painting some other view and the grey strip survives")

    def test_the_two_titlebar_calls_are_both_made(self):
        code = _code_only(self.tint)
        self.assertIn("setTitlebarAppearsTransparent_(True)", code)
        self.assertIn("setTitleVisibility_(", code,
                      "the title text is no longer hidden — that is half the grey strip")

    # ── the constants: the framework decides, a measured literal is the floor ────────────
    def test_the_constants_are_READ_from_the_framework_not_hardcoded(self):
        """⚠ THE FIRST CUT OF THIS LAW IMPORTED AppKit AND THE PRE-PUSH GATE REFUSED IT:
        "a suite imports something the CI runner does not have — it will pass here and take the
        deploy down there. CI installs only pillow." Dead right, and the fix is better than what
        it blocked. Instead of the SUITE checking the constant on one machine, the PRODUCTION
        code asks the running framework and falls back to the value measured on his Mac
        (NSWindowTitleHidden == 1, NSWindowStyleMaskFullScreen == 16384 == 1 << 14, both read out
        of AppKit on 2026-09-16). So it is self-correcting on every machine instead of verified
        on one, and nothing imports AppKit where CI can trip over it.
        [[unknown-stays-unknown]] [[the-unjoined-end]]"""
        tint, full = _code_only(self.tint), _code_only(self.full)
        self.assertIn('getattr(AppKit, "NSWindowTitleHidden", 1)', tint,
                      "the title-visibility constant is hardcoded again — ask the framework, and "
                      "keep the measured value only as the fallback")
        self.assertIn('setTitleVisibility_(_title_hidden)', tint,
                      "the constant is read and then not used")
        self.assertIn('getattr(AppKit, "NSWindowStyleMaskFullScreen", 1 << 14)', full,
                      "the fullscreen style mask is hardcoded again")
        self.assertIn("int(_fs_mask)", full,
                      "the style-mask constant is read and then not used")

    # ── cosmetics may never cost the window: this app has lost it three times ─────────────
    def test_every_native_call_is_individually_wrapped(self):
        """REG-051, REG-053 and v3175. A cosmetic change that can raise takes the console with it."""
        for name, blk in (("_mac_tint_caption", self.tint), ("_mac_force_fullscreen", self.full)):
            code = _code_only(blk)
            n_try = code.count("try:")
            self.assertGreaterEqual(n_try, 2,
                                    "%s has only %d try blocks — a native call outside one can "
                                    "take the window down, which has happened three times"
                                    % (name, n_try))
            self.assertIn("except Exception:", code,
                          "%s does not swallow a native failure" % name)

    def test_it_refuses_to_run_off_a_mac(self):
        for name, blk in (("_mac_tint_caption", self.tint), ("_mac_force_fullscreen", self.full)):
            code = _code_only(blk)
            self.assertIn('sys.platform != "darwin"', code,
                          "%s does not check the platform, so it would run its AppKit path on "
                          "Windows" % name)

    # ── the opt-out he asked for stays real ──────────────────────────────────────────────
    def test_TV_WINDOWED_still_wins(self):
        """a default nobody can leave is a trap — the create path already honours this and the
        retry must not undo it."""
        self.assertIn("TV_WINDOWED", _code_only(self.full),
                      "the fullscreen retry ignores TV_WINDOWED, so the documented opt-out is "
                      "silently overridden a moment after it is honoured")

    def test_it_never_fights_him_once_he_leaves_fullscreen(self):
        code = _code_only(self.full)
        self.assertIn("return", code)
        self.assertIn("styleMask()", code,
                      "nothing checks whether the window is ALREADY fullscreen, so this could "
                      "toggle a fullscreen window back OUT of fullscreen")

    # ── both hooks are actually joined to the event ──────────────────────────────────────
    def test_both_hooks_are_wired_to_shown(self):
        """[[the-unjoined-end]] — two halves built right and never joined is this repo's most
        repeated defect, and a window hook nobody subscribes runs never."""
        code = _code_only(self.src)
        for fn in ("_mac_tint_caption", "_mac_force_fullscreen"):
            self.assertIn("win.events.shown += %s" % fn, code,
                          "%s is defined and never subscribed — it can never run" % fn)

    def test_it_runs_on_shown_and_not_on_the_creation_path(self):
        """the NSWindow does not exist until the GUI thread builds it inside webview.start()."""
        code = _code_only(self.src)
        i = code.find("webview.create_window(**kwargs)")
        j = code.find("win.events.shown += _mac_tint_caption")
        self.assertGreater(i, 0, "create_window call not found")
        self.assertGreater(j, i,
                           "the caption hook is being called before the window exists")


RED_PROOF = [
    ("control_app.py", "setTitleVisibility_(1)", "setTitleVisibility_(0)",
     "test_the_two_titlebar_calls_are_both_made"),
    ("control_app.py", "win.events.shown += _mac_tint_caption",
     "win.events.shownX += _mac_tint_caption",
     "test_both_hooks_are_wired_to_shown"),
    # ⚠ ANCHORED ON `native.` — the bare lookup appears TWICE, because the docstring above quotes
    # pywebview's own line verbatim. The first proof run reported matches=2 and STAYED GREEN: the
    # tamper landed in the prose and left the code untouched. The match count is what told me, and
    # printing it is the whole reason this harness prints it. [[sabotage-is-usually-the-wrong-one]]
    ("control_app.py", "native.contentView().superview().subviews().lastObject()",
     "native.contentView()",
     "test_it_reverses_pywebviews_own_line_down_pywebviews_own_path"),
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
