# -*- coding: utf-8 -*-
"""#227 — THIS MACHINE CAN DECODE A FRAME.

MEASURED 2026-09-24 over SSH: his Windows ALT ran Python 3.12.10 with pywebview and NO Pillow, so every
frame it filmed was unreadable - and nothing said so, because every frame reader swallows its own
ImportError. The Windows launcher installed pywebview on first run and never Pillow.

  · DRIVEN: with Pillow blocked (sys.modules), the doctor row reads MISSING, names Pillow and the fix.
  · DRIVEN: with Pillow present it reads OK only after a BMP round-trips pixel for pixel.
  · STRUCTURAL: the launcher probes `import PIL` and installs Pillow in the same once-and-cache block
    as pywebview, and the installer installs it too (anchored on the pip line, not the word).
RED_PROOF below.
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import console_doctor as cd  # noqa: E402


def _ps1(name):
    with io.open(os.path.join(HERE, name), encoding="utf-8-sig") as f:
        return "\n".join(l.split("#", 1)[0] for l in f.read().split("\n"))


class TheRowReadsTheMachine(unittest.TestCase):

    def test_without_pillow_it_says_missing_and_names_the_fix(self):
        saved = {k: sys.modules.get(k) for k in ("PIL", "PIL.Image")}
        sys.modules["PIL"] = None
        sys.modules["PIL.Image"] = None
        try:
            state, why = cd._check_this_machine_can_decode_a_frame()
        finally:
            for k, v in saved.items():
                if v is None:
                    sys.modules.pop(k, None)
                else:
                    sys.modules[k] = v
        self.assertEqual(state, cd.MISSING, "a machine with no Pillow read: %s" % why)
        self.assertIn("pip install --user Pillow", why)

    @unittest.skipIf(__import__("importlib").util.find_spec("PIL") is None,
                     "Pillow is absent in this venue - the OK half is UNMEASURED here, not passing")
    def test_with_pillow_it_reads_ok_after_a_round_trip(self):
        state, why = cd._check_this_machine_can_decode_a_frame()
        self.assertEqual(state, cd.OK, why)
        self.assertIn("round-tripped a BMP", why)

    @unittest.skipIf(__import__("importlib").util.find_spec("PIL") is None,
                     "Pillow is absent in this venue - UNMEASURED here, not passing")
    def test_a_decoder_that_loses_the_pixels_is_missing(self):
        """An import is not a decode: a reader that hands back the wrong pixels must not read OK."""
        from PIL import Image
        real = Image.open
        Image.open = lambda *a, **k: Image.new("RGB", (4, 3), (0, 0, 0))
        try:
            state, why = cd._check_this_machine_can_decode_a_frame()
        finally:
            Image.open = real
        self.assertEqual(state, cd.MISSING, "pixels that did not survive the round trip read: %s" % why)

    def test_it_is_declared_in_both_registries(self):
        self.assertIn("this machine can decode a frame", {n for n, _ in cd.CHECKS})
        self.assertIn("this machine can decode a frame", cd.WATCHES)


class TheWindowsLauncherInstallsIt(unittest.TestCase):

    def test_the_launcher_probes_and_installs_pillow(self):
        src = _ps1("start_tvd_win.ps1")
        self.assertIn("@($py.Cmd, '-c', 'import PIL')", src, "the launcher never asks whether Pillow imports")
        self.assertIn("@($py.Cmd, '-m', 'pip', 'install', '--user', '--quiet', 'Pillow')", src,
                      "the launcher never installs Pillow, so a fresh Windows box films frames it cannot read")

    def test_the_installer_installs_pillow(self):
        self.assertIn("& $py -m pip install --user --quiet 'Pillow' | Out-Null", _ps1("install-tvd.ps1"))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#227 - the Windows launcher stops installing Pillow: a fresh box films frames it can never read",
        "file": "start_tvd_win.ps1",
        "find": "           else { @($py.Cmd, '-m', 'pip', 'install', '--user', '--quiet', 'Pillow') }\n",
        "replace": "           else { @($py.Cmd, '-m', 'pip', 'install', '--user', '--quiet', 'nothing') }\n",
        "matches": 1,
    },
    {
        "why": "#227 - the doctor row believes an import instead of a decode",
        "file": "console_doctor.py",
        "find": "    if size != (4, 3) or tuple(px) != (200, 40, 10):\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "#227 - a machine with no Pillow reads OK: the row swallows the ImportError like every reader did",
        "file": "console_doctor.py",
        "find": "        return MISSING, (\"Pillow will not import on this machine (%s), so no frame this console films \"\n",
        "replace": "        return OK, (\"Pillow will not import on this machine (%s), so no frame this console films \"\n",
        "matches": 1,
    },
]
