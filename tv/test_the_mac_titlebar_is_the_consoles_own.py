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
        # ⚠⚠ v3347 — THE WALK WAS SPLIT, NOT ABANDONED. This pinned ONE chained expression,
        # `contentView().superview().subviews().lastObject().setBackgroundColor_`, and the code now
        # takes the IDENTICAL path in _objc_can-guarded steps — each hop checked before it is made,
        # which is strictly safer on a PyObjC call that sits on his launch path and cannot be
        # caught if it fails natively. A law that pins the SYNTAX of a walk goes red the day
        # somebody makes that walk defensive, which is the opposite of what it wants. So it pins
        # the PATH: the four hops, IN ORDER, and a paint at the end.
        _hops = ("contentView()", "superview()", "subviews()", "lastObject()")
        _at = []
        for _hop in _hops:
            _i = code.find(_hop, (_at[-1] if _at else 0))
            self.assertGreater(
                _i, -1,
                "the repaint no longer calls %s, so it is not walking pywebview's own lookup and "
                "it is painting some other view — the grey strip survives" % _hop)
            _at.append(_i)
        self.assertEqual(
            _at, sorted(_at),
            "the hops appear out of order (%r). A different path paints a different view, which "
            "is the whole failure this law exists for." % (_at,))
        self.assertIn(
            "setBackgroundColor_", code,
            "the walk is made and nothing is painted at the end of it")

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
        """REG-051, REG-053, v3175 — a cosmetic change has cost this app its window three times.

        ⚠⚠ AND ON 2026-09-16 IT COST IT A FOURTH, WHILE THIS ASSERTION WAS GREEN. His console
        crashed on launch — "Python quit unexpectedly", splash reading "starting v3206" — and
        stayed down, because the relaunch path pauses the supervisor. Every native call WAS
        individually wrapped in `try/except Exception`, exactly as this test demanded, and the
        wrapping bought NOTHING.

        THE REASON IS A CATEGORY ERROR IN THE TEST ITSELF: an Objective-C exception or a bad
        selector does not raise a Python exception. It kills the process. **A Python `try` cannot
        catch a SIGTRAP.** So this assertion measured a defence that is structurally incapable of
        defending against the failure it names — a green gate over a live crash, which is the
        shape this repo calls the-green-that-lies. My own scratch probe had already died the same
        way earlier that night (exit 133) and I filed it as a teardown artefact.

        The wrapping still belongs — it catches the ordinary Python failures — so this stays. What
        it may never again do is stand alone as the reason a native call is safe.
        [[feedback-blind-fixture-green-gate]] [[regression-guard]]
        """
        for name, blk in (("_mac_tint_caption", self.tint), ("_mac_force_fullscreen", self.full)):
            code = _code_only(blk)
            n_try = code.count("try:")
            self.assertGreaterEqual(n_try, 2,
                                    "%s has only %d try blocks — a native call outside one can "
                                    "take the window down on the ORDINARY python failures"
                                    % (name, n_try))
            self.assertIn("except Exception:", code,
                          "%s does not swallow a native failure" % name)

    def test_the_native_hooks_are_OFF_unless_explicitly_opted_IN(self):
        """The defence that actually works, because it never runs the call at all.

        A Python try cannot catch what PyObjC does to the process, so the only honest protection
        for his LAUNCH PATH is not running these hooks by default. They are cosmetic — a grey
        titlebar strip and a fullscreen grant — and his console is not. Weighed against a console
        that will not open, the chrome loses every time.

        ⚠ AND IT MUST BE OFF BY DEFAULT, not merely toggleable. An opt-OUT would leave the crash
        on the path every ordinary launch takes, which is precisely where it happened.
        """
        code = _code_only(self.src)
        self.assertIn('os.environ.get("TV_MAC_CHROME"', code,
                      "the mac chrome hooks are no longer behind an explicit opt-in, so a native "
                      "crash is back on his everyday launch path")
        # ⚠ LOOK BACKWARDS FROM EACH HOOK, not forwards from the first guard. There are TWO
        # TV_MAC_CHROME guards now (the class-level tabbing call and these subscriptions), and a
        # forward window from the first one reads the wrong block entirely — the mistake this
        # file's own `_between` note warns about, made again. [[source-window-shortcut]]
        for hook in ("_mac_tint_caption", "_mac_force_fullscreen"):
            k = code.find("win.events.shown += " + hook)
            self.assertGreater(k, 0, "%s is no longer subscribed at all" % hook)
            before = code[max(0, k - 500):k]
            self.assertIn('os.environ.get("TV_MAC_CHROME"', before,
                          "%s is subscribed OUTSIDE the opt-in guard, so a native crash is back "
                          "on his everyday launch path" % hook)
        # and the class-level tabbing call, which runs before any window exists
        self.assertNotIn(
            'if sys.platform == "darwin":\n        try:\n            import AppKit\n'
            '            AppKit.NSWindow.setAllowsAutomaticWindowTabbing_',
            code,
            "setAllowsAutomaticWindowTabbing_ runs unconditionally on the launch path again")

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
    # ⚠ matches=0 on the first run: the anchor still said `setTitleVisibility_(1)` after the
    # constant moved to `_title_hidden`. A dead anchor tampers nothing and the proof runs green.
    ("control_app.py", "setTitleVisibility_(_title_hidden)", "setTitleVisibilityX_(_title_hidden)",
     "test_the_two_titlebar_calls_are_both_made"),
    # ⚠ matches=2 on the first run — there are TWO TV_MAC_CHROME guards (the class-level tabbing
    # call and these subscriptions) and replace(...,1) tampered the WRONG one, leaving the hooks
    # still guarded and the proof green. Anchor on the guard that actually wraps the hooks.
    # ⚠⚠ v3347 — matches=0, because THE GUARD INVERTED. It used to be an opt-IN
    # (`in ("1","true","yes","on")`); it is now an opt-OUT
    # (`.strip().lower() not in ("0","false","no","off")`), default ON, "because he asked for
    # clean". So TWO things were wrong, not one: the anchor was dead AND the tamper direction
    # had become inert — `if True:` cannot disable a guard that is already true. Re-anchored on
    # the live guard and flipped to `if False:`, which is what actually turns the hooks off.
    # A dead anchor is loud; an inert tamper is silent, and this entry had both.
    # [[sabotage-is-usually-the-wrong-one]]
    ("control_app.py",
     'if str(os.environ.get("TV_MAC_CHROME", "")).strip().lower() not in ("0", "false", "no", "off"):\n'
     '                    win.events.shown += _mac_tint_caption',
     'if False:\n                    win.events.shown += _mac_tint_caption',
     "test_the_native_hooks_are_OFF_unless_explicitly_opted_IN"),
    # ⚠ ANCHORED ON `native.` — the bare lookup appears TWICE, because the docstring above quotes
    # pywebview's own line verbatim. The first proof run reported matches=2 and STAYED GREEN: the
    # tamper landed in the prose and left the code untouched. The match count is what told me, and
    # printing it is the whole reason this harness prints it. [[sabotage-is-usually-the-wrong-one]]
    # ⚠⚠ v3347 — RE-ANCHORED ONTO A LINE THE LAW ACTUALLY READS. The old anchor
    # (`native.contentView().superview()...`) matched 0 after the walk was split into guarded
    # steps. My first repair pointed it at `self.window.contentView()...`, which DOES exist — in a
    # DIFFERENT function. That is this very defect wearing a fresh coat: an anchor that matches
    # once and tampers a site the law never looks at. The law reads `_mac_tint_caption`, so the
    # tamper must land inside it. Breaking the `subviews()` hop removes one step of the walk,
    # which is exactly what the law now pins.
    ("control_app.py",
     '_subs = _sv.subviews() if _objc_can(_sv, "subviews") else None',
     '_subs = _sv if _objc_can(_sv, "subviews") else None',
     "test_it_reverses_pywebviews_own_line_down_pywebviews_own_path"),
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
