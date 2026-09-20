#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3385 — A NICKNAME IS NOT AN IDENTITY, AND THE RAIL DREW TWO IDENTICAL ROWS.

Konyo, looking at THE FLEET: *"two grokbot account si see in fleet"*.

MEASURED on his live console the same minute, and BOTH rows are real machines that belong there:

    GrokBot   grok-bot-vm-346371813   v3383   install 1bba07477e40   online
    GrokBot   cursor                  v3377   install 1bba07477e40   offline 03:37

the Linux native seat and the Cursor guest seat — named as SEPARATE seats in his own standing
brief. So nothing may be merged, deduped or pruned: the defect is that the rail cannot tell him
WHICH IS WHICH.

⚠⚠ AND THE INSTALL ID IS IDENTICAL ON BOTH. Any fix that disambiguated by install would still
draw two identical lines and look correct doing it. `machine` is the only field that differs.

⚠ IT MATTERS MORE SINCE v3384, which made the peer's VERSION decide whether it can publish item
names. Two rows both reading "GrokBot" hide which one is the stale v3377 — a label that has
stopped identifying its referent. [[label-outlived-referent]]

⚠ FOUR SITES RENDERED THIS LABEL INDEPENDENTLY (stale list, two tooltips, the rail row), which is
why the fix is one helper rather than four edits. [[copy-drift]]

WHAT THIS FILE PINS — by RUNNING the shipped helper in node, not by re-implementing it:
  * two machines sharing a nickname each render with their machine appended
  * a nickname owned by ONE machine renders exactly as before — no churn for the common case
  * a row with no nickname still falls back to the machine, and then to '?'
  * every label site goes through the helper, so the fourth copy cannot creep back
"""

import io
import os
import re
import json
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    import console_safe
    console_safe.enable()
except Exception:
    pass

UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()

START = "var _fleetName = function (m, rows) {"
END = "var _fleetRows = function (j) {"


def _node():
    for c in ("node", "/usr/local/bin/node", "/opt/homebrew/bin/node"):
        try:
            subprocess.run([c, "--version"], capture_output=True, timeout=10)
            return c
        except Exception:
            continue
    return None


def _helper_src():
    """The SHIPPED helper text, bounded by a real end anchor rather than a byte count.

    ⚠ A fixed-size window past the region reads as ABSENT and a law built on one measures my
    guess, not the file. [[source-reading-guard]] section 3
    """
    i = UI.find(START)
    j = UI.find(END, i + 1)
    if i < 0 or j < 0:
        return None
    return UI[i:j]


class AFleetRowIdentifiesItsMachine(unittest.TestCase):

    def setUp(self):
        self.node = _node()
        if not self.node:
            self.skipTest("no node on PATH — this law RUNS the shipped helper and will not "
                          "re-implement it")
        self.src = _helper_src()
        self.assertTrue(self.src, "the _fleetName helper is gone from control_ui.html")

    def _label(self, rows, idx):
        """Run the REAL helper over a fixture and return what the rail would draw."""
        prog = ("%s\nvar _rows = %s;\nprocess.stdout.write(String(_fleetName(_rows[%d], _rows)));"
                % (self.src, json.dumps(rows), idx))
        fh = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
        fh.write(prog)
        fh.close()
        try:
            r = subprocess.run([self.node, fh.name], capture_output=True, text=True, timeout=30)
            self.assertEqual(r.returncode, 0,
                             "the helper would not even run: %s" % (r.stderr or "")[:200])
            return r.stdout
        finally:
            try:
                os.unlink(fh.name)
            except Exception:
                pass

    # ---------- behaviour, on HIS measured roster ----------

    def test_two_machines_sharing_a_nickname_are_told_apart(self):
        """THE WHOLE POINT — his exact pair, with the install id identical on both."""
        rows = [
            {"nickname": "GrokBot", "machine": "grok-bot-vm-346371813", "install": "1bba07477e40"},
            {"nickname": "GrokBot", "machine": "cursor", "install": "1bba07477e40"},
        ]
        a, b = self._label(rows, 0), self._label(rows, 1)
        self.assertNotEqual(a, b,
                            "both rows still render %r — he cannot tell the live v3383 seat from "
                            "the stale v3377 one" % a)
        self.assertIn("grok-bot-vm-346371813", a)
        self.assertIn("cursor", b)
        self.assertIn("GrokBot", a, "the nickname he chose must survive, not be replaced")
        self.assertIn("GrokBot", b)

    def test_a_unique_nickname_is_untouched(self):
        """NO CHURN FOR THE COMMON CASE. Every other row on his rail must look as it did."""
        rows = [
            {"nickname": "Konyo", "machine": "konyo-3"},
            {"nickname": "Dean", "machine": "LAPTOP-QNFL860M"},
            {"nickname": "Wife PC", "machine": "AdiJusid"},
        ]
        self.assertEqual(self._label(rows, 0), "Konyo")
        self.assertEqual(self._label(rows, 1), "Dean")
        self.assertEqual(self._label(rows, 2), "Wife PC")

    def test_an_unnamed_row_still_falls_back_to_the_machine(self):
        rows = [{"machine": "diagnostic-probe"}, {"nickname": "  ", "machine": "bare-box"}]
        self.assertEqual(self._label(rows, 0), "diagnostic-probe")
        self.assertEqual(self._label(rows, 1), "bare-box",
                         "a whitespace-only nickname must be treated as absent, not drawn")

    def test_a_row_with_nothing_is_a_question_mark_not_an_empty_label(self):
        """An unidentifiable row must LOOK unidentifiable. [[unknown-stays-unknown]]"""
        rows = [{}]
        self.assertEqual(self._label(rows, 0), "?")

    def test_three_sharing_one_nickname_all_disambiguate(self):
        """The pair is what he saw; the law must not be written only for two."""
        rows = [{"nickname": "Box", "machine": "a"},
                {"nickname": "Box", "machine": "b"},
                {"nickname": "Box", "machine": "c"}]
        got = [self._label(rows, i) for i in range(3)]
        self.assertEqual(len(set(got)), 3, "three rows collapsed to %r" % (sorted(set(got)),))

    # ---------- the join: no fourth copy ----------

    def test_every_label_site_goes_through_the_helper(self):
        """A helper three of four sites use is still copy-drift. [[the-unjoined-end]]"""
        self.assertGreaterEqual(UI.count("_fleetName("), 4,
                                "a label site stopped using the helper, so one surface can drift "
                                "back to an ambiguous name while the others are fixed")
        code = re.sub(r"/\*.{0,4000}?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), UI, flags=re.S)
        self.assertNotIn("(m.nickname || '').trim() || m.machine", code,
                         "a raw nickname-or-machine label is back in the UI")


RED_PROOF = [
    {
        "why": "dropping the ambiguity branch returns both of his GrokBot rows to one identical "
               "label, which is the screen he reported",
        "file": "control_ui.html",
        "find": "    return (seen > 1 && mach) ? (nick + ' \\u00b7 ' + mach) : nick;",
        "replace": "    return nick;",
        "matches": 1,
    },
    {
        "why": "an unnamed row must still fall back to its machine; collapsing it to '?' makes "
               "every unnamed box indistinguishable, which is the same defect one level down",
        "file": "control_ui.html",
        "find": "    if (!nick) return mach || '?';",
        "replace": "    if (!nick) return '?';",
        "matches": 1,
    },
    {
        "why": "restoring the raw label at the rail row is the exact copy-drift regression, and "
               "the code law must catch it",
        "file": "control_ui.html",
        "find": "        var nameFor = _fleetName(m, _fleetRows(j));",
        "replace": "        var nameFor = (m.nickname || '').trim() || m.machine || '?';",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
