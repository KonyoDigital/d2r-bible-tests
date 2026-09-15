# -*- coding: utf-8 -*-
"""THE CONSOLE OPENS FULLSCREEN, AND A WINDOWED ONE STOPS PAINTING WITHIN TWENTY SECONDS.

Konyo, 2026-09-14: *"this console keeps opening up windows mode. and it should open up FULLSCREEN by
default with an option to go windows mode if wanted."*

⚠⚠ IT IS NOT ONLY A PREFERENCE — IT IS THE CAUSE OF EVERY BLACK STAGE THE EYES LANE HAS REPORTED.
MEASURED on his live console, three samples twenty seconds apart with nothing touching it:

    ver=v3095  painting=False hidden=True    -> raised
    ver=v3095  painting=True  hidden=False
    ver=v3095  painting=False hidden=True    -> raised again

A page that is not frontmost is `document.hidden`: it stops painting, so there is nothing to
photograph. The console was healthy over HTTP the entire time — `/api/status` answered in **31 ms**
— while Grok Bot reported `Quartz ON-SCREEN none` and "off-space white is not blank" tick after
tick. I read that as the bot being unable to look, when it was reporting that there was nothing on
screen to look AT. A floating window yields focus to anything; a fullscreen one owns its Space.

⚠ THE OPT-OUT MUST STAY REAL. He asked for "an option to go windows mode if wanted", and a default
nobody can leave is a trap. `TV_WINDOWED=1` starts windowed at the old 1120x660 geometry, which
v1464 sized to a 672-logical work area — fullscreen does not discard that.

⚠ AND IT MUST DEGRADE, NEVER RAISE. `fullscreen` is passed through the same `_cw_ok` signature
filter every other option goes through, so a pywebview build that does not accept it drops the key
and still gets a window. A console that refuses to start is worse than one that starts windowed.
[[unknown-stays-unknown]]
"""
import ast
import io
import os
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))


def _region():
    """The window-creation block, anchored at BOTH ends."""
    with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
        src = fh.read()
    # ⚠ start at the TV_WINDOWED read, not at `kwargs = dict(` — the opt-out is assigned ABOVE the
    # dict and a region anchored at the dict reports it ABSENT. [[source-window-shortcut]]
    a = src.find('_windowed = str(os.environ.get("TV_WINDOWED"')
    if a <= 0:
        a = src.find("    kwargs = dict(\n        title=\"TV DIABLO\",")
    assert a > 0, "the window kwargs are gone"
    b = src.find("globals()[\"_MAIN_WIN\"] = webview.create_window(**kwargs)", a)
    assert b > a, "the create_window call is gone"
    return src[a:b]


class TestTheConsoleOpensFullscreen(unittest.TestCase):

    def test_fullscreen_is_the_default(self):
        code = "\n".join(l.split("#", 1)[0] for l in _region().splitlines())
        self.assertIn('kwargs["fullscreen"] = True', code,
                      "the console no longer opens fullscreen — a windowed console stops painting "
                      "within ~20s of losing focus, which is the black stage every eyes-lane look "
                      "has hit")
        print("fullscreen is set on the default path")

    def test_the_windowed_opt_out_exists_and_is_env_driven(self):
        code = "\n".join(l.split("#", 1)[0] for l in _region().splitlines())
        self.assertIn("TV_WINDOWED", code,
                      "the windowed opt-out is gone — he asked for 'an option to go windows mode "
                      "if wanted', and a default nobody can leave is a trap")
        # ⚠ It must GUARD the fullscreen key, not merely sit near it. The region is an indented
        # fragment of a function, so ast.parse refuses it — assert the ordering textually instead
        # of parsing something that was never a module.
        i_env = code.find("_windowed")
        i_guard = code.find("if not _windowed:")
        i_full = code.find('kwargs["fullscreen"] = True')
        self.assertGreater(i_env, -1, "TV_WINDOWED is never read into a variable")
        self.assertGreater(i_guard, -1,
                           "nothing guards the fullscreen key — TV_WINDOWED would be decoration")
        self.assertLess(i_guard, i_full,
                        "the guard does not precede the fullscreen key, so it cannot gate it")
        print("TV_WINDOWED guards the fullscreen key")

    def test_the_windowed_geometry_survives(self):
        code = _region()
        self.assertIn("width=1120", code, "the windowed width was discarded")
        self.assertIn("height=660", code,
                      "the windowed height was discarded — v1464 sized 660 to a 672-logical work "
                      "area and fullscreen must not throw that away")
        print("windowed geometry kept: 1120x660")

    def test_an_unsupported_build_drops_the_key_rather_than_raising(self):
        """The signature filter must still run AFTER fullscreen is added."""
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            src = fh.read()
        i_full = src.find('kwargs["fullscreen"] = True')
        i_filter = src.find("kwargs = {k: v for k, v in kwargs.items() if k in _cw_ok}")
        self.assertGreater(i_full, 0, "fullscreen is gone")
        self.assertGreater(i_filter, 0, "the signature filter is gone")
        self.assertLess(i_full, i_filter,
                        "fullscreen is added AFTER the _cw_ok filter, so a pywebview that does not "
                        "accept it would raise TypeError and the console would not start at all")
        print("fullscreen is added before the _cw_ok filter — unsupported builds drop it")


RED_PROOF = [
    {
        "why": "the console goes back to opening windowed, so it stops painting within ~20s of "
               "losing focus and every visual pass photographs a black stage on a console that is "
               "perfectly healthy over HTTP",
        "file": "control_app.py",
        "find": '    if not _windowed:\n        kwargs["fullscreen"] = True',
        "replace": '    if False:\n        kwargs["fullscreen"] = True',
        "matches": 1,
    },
    {
        "why": "the windowed opt-out is removed, so fullscreen becomes a default he cannot leave",
        "file": "control_app.py",
        "find": '    _windowed = str(os.environ.get("TV_WINDOWED", "")).strip().lower() in ("1", "true", "yes", "on")',
        "replace": '    _windowed = False',
        "matches": 1,
    },
]

class TheFullscreenWindowHasNoTitleBar(unittest.TestCase):
    """v3175 — HIS SCREENSHOT: "this TV diablo banner on top is now here when it wasnt".

    MEASURED: `fullscreen` was passed AND accepted (present in this pywebview's create_window
    signature, and no drop-warning printed), yet the window came up windowed WITH its macOS title
    bar. On macOS the fullscreen transition is applied after creation and silently does not take
    when the app is not frontmost — the same state GROKBOT records as `painting False / hidden
    True`. Relaunching through the TCC-granted .app did not fix it, so activation timing cannot be
    relied on. `frameless` is decided at creation and cannot fail that way.

    ⚠ AND ONLY ON THE FULLSCREEN PATH. A frameless window that is merely maximized cannot be
    dragged by a title bar it does not have, so the TV_WINDOWED=1 opt-out keeps its frame. An
    opt-out that traps him in an unmovable window is not an opt-out.
    """

    def _src(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            return fh.read()

    def test_frameless_is_set_wherever_fullscreen_is(self):
        src = self._src()
        i = src.find('kwargs["fullscreen"] = True')
        self.assertGreater(i, 0, "the fullscreen default is gone")
        self.assertIn('kwargs["frameless"] = True', src[i:i + 2000],
                      "fullscreen is requested without frameless, so a failed fullscreen "
                      "transition puts the macOS title bar back over his console")

    def test_the_windowed_optout_keeps_its_frame(self):
        """PARSED, not grepped: both assignments must sit inside the same `if not _windowed`
        branch, so the opt-out cannot inherit framelessness and become undraggable."""
        import ast
        src = self._src()
        tree = ast.parse(src)
        found = False
        for n in ast.walk(tree):
            if not isinstance(n, ast.If):
                continue
            seg = ast.get_source_segment(src, n) or ""
            if 'kwargs["frameless"] = True' not in seg:
                continue
            found = True
            self.assertIn('kwargs["fullscreen"] = True', seg,
                          "frameless is set outside the fullscreen branch — the windowed opt-out "
                          "would lose its title bar and could not be moved")
        self.assertTrue(found, "no conditional guards the frameless assignment at all")


if __name__ == "__main__":
    unittest.main(verbosity=2)
