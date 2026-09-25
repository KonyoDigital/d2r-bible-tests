# -*- coding: utf-8 -*-
"""#174 v-B2 — THE CONSOLE SERVES THE GAME'S ITEM FONT FROM HIS INSTALL, AND ONLY FROM THERE.

His order, 2026-09-25: the mule window in the d2planner's style, "literally the same". Their item text is set
in Blizzard's Exocet (measured on their builder: "Exocet Blizzard MixedCaps"). It is not ours to publish, so it
may never be committed to this public repo or served by the public site. His own install carries it (MEASURED
the same day: data\\hd\\ui\\fonts\\exocetblizzardot-medium.otf, 68,596 bytes, 'OTTO'), so the console streams it
from there, in memory only, and says why when it cannot.

  · DRIVEN (control_app.d2r_font, the install pull faked): a real font is served; it is pulled ONCE and then
    served from memory; nothing is written into the tree.
  · DRIVEN: no install / no extractor -> None + the reason (the board falls back to a free face).
  · DRIVEN: bytes that are not a font are refused, never served as one.
  · DRIVEN: a name outside the table - including a path - is refused WITHOUT asking the install, so the route
    can never become a reader of arbitrary game files.
  · JOINED: the GET route answers the font or a 404 with the reason.
RED_PROOF below.
"""
import inspect
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

import control_app as CA  # noqa: E402
import affix_lexicon as AL  # noqa: E402

FONT = b"OTTO" + b"\x00" * 64


class TheConsoleServesHisInstallFont(unittest.TestCase):

    def setUp(self):
        self.calls = []
        keep_pull, keep_cache = AL._pull, dict(CA._D2R_FONT_CACHE)
        CA._D2R_FONT_CACHE.clear()

        def _restore():
            AL._pull = keep_pull
            CA._D2R_FONT_CACHE.clear(); CA._D2R_FONT_CACHE.update(keep_cache)
        self.addCleanup(_restore)

    def _answer(self, blob):
        def _pull(path, timeout=150):
            self.calls.append(path)
            return blob
        AL._pull = _pull

    def test_the_install_font_is_served_once_then_from_memory(self):
        self._answer(FONT)
        before = sorted(os.listdir(HERE))
        a, why = CA.d2r_font("exocet")
        b, _ = CA.d2r_font("exocet")
        self.assertEqual(a, FONT, why)
        self.assertEqual(b, FONT)
        self.assertEqual(len(self.calls), 1, "the install was asked on every request - it must be pulled once")
        self.assertIn("exocetblizzardot-medium.otf", self.calls[0])
        self.assertEqual(sorted(os.listdir(HERE)), before, "the font was written into the tree")

    def test_no_install_answers_why_never_a_font(self):
        self._answer(None)
        data, why = CA.d2r_font("exocet")
        self.assertIsNone(data)
        self.assertIn("fallback", why)

    def test_bytes_that_are_not_a_font_are_refused(self):
        self._answer(b"<html>no</html>")
        data, why = CA.d2r_font("exocet")
        self.assertIsNone(data, "a non-font blob was served as the font")
        self.assertIn("not a font", why)

    def test_a_name_outside_the_table_never_reaches_the_install(self):
        self._answer(FONT)
        for bad in ("kodia", "../../etc/passwd", r"data:data\hd\ui\fonts\kodia.ttf", ""):
            data, why = CA.d2r_font(bad)
            self.assertIsNone(data, "%r was served" % bad)
        self.assertEqual(self.calls, [], "a name outside the table reached the install")

    def test_the_route_serves_the_font_or_says_why(self):
        src = inspect.getsource(CA)
        i = src.index('if path == "/api/d2r_font/exocet":')
        block = src[i:i + 900]
        self.assertIn('d2r_font("exocet")', block)
        self.assertIn('"font/otf"', block)
        self.assertIn("self._json(404", block)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#174 v-B2 - the font is pulled from the install on every request (a CASC extract per page load)",
        "file": "control_app.py",
        "find": "    _D2R_FONT_CACHE[key] = blob\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - whatever the install returns is served as a font, even when it is not one",
        "file": "control_app.py",
        "find": "    if blob[:4] not in (b\"OTTO\", b\"\\x00\\x01\\x00\\x00\", b\"true\", b\"ttcf\"):\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - a name outside the table reaches the install: the route becomes a reader of arbitrary game files",
        "file": "control_app.py",
        "find": "    path = D2R_FONTS.get(str(key or \"\"))\n",
        "replace": "    path = D2R_FONTS.get(str(key or \"\")) or str(key or \"\")\n",
        "matches": 1,
    },
]
