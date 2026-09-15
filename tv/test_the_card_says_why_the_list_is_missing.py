# -*- coding: utf-8 -*-
"""v3170 (#82) — THE CARD SAYS WHY THE PER-ITEM LIST IS MISSING.

v3169 fixed the cross-reference SENTENCE. The CARD - the thing he actually hovers - stayed
silent: it printed the counts and a one-word verdict and never said the per-item mask was
absent or why, so the card and the panel disagreed about how much this console knows.

MEASURED before this shipped: `maskWhy` appeared in control_app.py 5 times and in
control_ui.html ZERO times. Published by the server on every fleet row, read by nothing.
[[the-unjoined-end]]

This law drives the SHIPPED block in node against a synthetic row, so it tests the code on
the page rather than a paraphrase of it.
"""
import io
import json
import os
import subprocess
import tempfile
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable
    enable()
except Exception:
    pass
UI = os.path.join(HERE, "control_ui.html")

START = "        var _mwLine = '';"
END = "        } catch (_) {}"


def _between(src, start, end):
    i = src.find(start)
    assert i >= 0, "start anchor missing - the maskWhy block is gone from the card"
    j = src.find(end, i)
    assert j > i, "end anchor missing"
    return src[i:j + len(end)]


def _block():
    with io.open(UI, encoding="utf-8") as fh:
        return _between(fh.read(), START, END)


HARNESS = """
function escC(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;')
                                  .replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
var m = %(row)s;
%(block)s
console.log(JSON.stringify({html: _mwLine}));
"""


class TheCardSaysWhyTheListIsMissing(unittest.TestCase):

    def drive(self, row):
        js = HARNESS % {"row": json.dumps(row), "block": _block()}
        # ⚠ A UNIQUE FILE PER RUN, CREATED INSIDE THE try. A cross-family review of v3170 caught
        # both halves: a FIXED name (.mwline_drive.js) means two concurrent runs write, run and
        # delete each other's harness — one sees the other's JS or an empty file, and the failure
        # looks like a defect in the page. And opening BEFORE the try leaves a partial file behind
        # if the write raises. mkstemp gives a per-run name and the unlink is unconditional.
        fd, p = tempfile.mkstemp(prefix=".mwline_drive_", suffix=".js", dir=HERE)
        try:
            with io.open(fd, "w", encoding="utf-8") as fh:
                fh.write(js)
            r = subprocess.run(["node", p], capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            self.skipTest("node unavailable - a skip is NOT a pass")
        finally:
            try:
                os.unlink(p)
            except OSError:
                pass
        self.assertEqual(r.returncode, 0, "the shipped block threw:\\n%s" % (r.stderr or "")[-800:])
        return json.loads(r.stdout.strip().splitlines()[-1])["html"]

    def test_deans_real_row_names_the_reason(self):
        html = self.drive({"nickname": "Dean",
                           "maskWhy": {"sets": "no board window", "uniques": "no board window"}})
        self.assertIn("no board window", html,
                      "the server published the reason and the card rendered nothing")

    def test_one_reason_is_named_once_not_per_ledger(self):
        """Dean's row carries the SAME reason twice. Printing it per ledger reads as two
        separate faults when it is one machine state."""
        html = self.drive({"maskWhy": {"sets": "no board window", "uniques": "no board window"}})
        self.assertEqual(html.count("no board window"), 1,
                         "one machine state must not print as two faults")
        self.assertIn("sets, uniques", html, "and both ledgers must still be named")

    def test_two_different_reasons_are_both_kept(self):
        html = self.drive({"maskWhy": {"sets": "no board window", "uniques": "roster mismatch"}})
        self.assertIn("no board window", html)
        self.assertIn("roster mismatch", html)

    def test_a_row_with_no_reason_adds_nothing(self):
        self.assertEqual(self.drive({"nickname": "Konyo"}), "",
                         "a machine with nothing to explain must not grow an empty line")

    def test_a_falsy_reason_is_not_a_reason(self):
        self.assertEqual(self.drive({"maskWhy": {"sets": "", "uniques": None}}), "",
                         "an absent reason rendered as a reason is a zero with no denominator")

    def test_the_reason_is_escaped(self):
        html = self.drive({"maskWhy": {"sets": "<img src=x onerror=1>"}})
        self.assertNotIn("<img", html, "a fleet row is remote input and must be escaped")
        self.assertIn("&lt;img", html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
