# -*- coding: utf-8 -*-
"""REG-2796 (GrokBot, his DAILY PICK flicker on v3829/v3830) - THE TASK FORCE REPAINTS ONLY WHEN ITS ROWS CHANGED.

hdTaskForce skipped an identical repaint only when `rowsEl.innerHTML === html`. The browser hands back what it parsed,
not the string it was given: esc() writes ' as &#39; and Chrome serializes a bare ' ("Cow King's Leathers"), and an
art <img> whose onerror removes it changes the DOM after the paint. So the skip never held for those rows and the whole
roster was rewritten on every 1.5 s poll - the flicker. The paint now leaves its own mark on the rows element
(data-tf-sig, a hash of what it wrote) and the skip reads that mark.

Measured on the shipped source and, in node, on the mark itself (the same function the page calls). RED_PROOF below.
"""
import io
import os
import re
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()
NODE = shutil.which("node")


def _block():
    i = UI.index("var box = $('hd-taskforce');")
    return UI[i:UI.index("} catch(e){}", i)]


class TheTaskForceRepaintsOnlyWhenItChanged(unittest.TestCase):

    def test_the_skip_reads_the_paints_own_mark_never_innerhtml(self):
        blk = _block()
        m = re.search(r"var landed\s*=\s*(.*?);", blk, re.S)
        self.assertIsNotNone(m, "nothing computes whether the paint landed")
        self.assertNotIn("innerHTML", m.group(1), "the skip compares the browser's re-serialized innerHTML again")
        self.assertIn("rowsEl.getAttribute('data-tf-sig') === _tfMark", m.group(1))

    def test_the_paint_leaves_the_mark_after_it_writes(self):
        blk = _block()
        self.assertLess(blk.index("rowsEl.innerHTML = html;"), blk.index("rowsEl.setAttribute('data-tf-sig', _tfMark);"))

    @unittest.skipUnless(NODE, "node is absent - the mark's own behaviour is UNMEASURED here, never a pass")
    def test_the_mark_is_the_same_for_the_same_rows_and_differs_when_they_change(self):
        fn = re.search(r"function _hdTfHash\(s\)\{.*?\n", UI).group(0)
        js = fn + ("var a = '<div aria-label=\"finish Cow King&#39;s Leathers\">x</div>';"
                   "console.log(JSON.stringify([_hdTfHash(a) === _hdTfHash(a), _hdTfHash(a) === _hdTfHash(a + ' '),"
                   " _hdTfHash('') === _hdTfHash(null)]));")
        out = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=60).stdout.strip()
        self.assertEqual(out, "[true,false,true]", out)


RED_PROOF = [
    {"why": "REG-2796 - the skip compares innerHTML again, so an apostrophe repaints the roster on every poll",
     "file": "control_ui.html",
     "find": "                      && (!rows.length || rowsEl.getAttribute('data-tf-sig') === _tfMark));\n",
     "replace": "                      && (!rows.length || rowsEl.innerHTML === html));\n",
     "matches": 1},
    {"why": "REG-2796 - the paint leaves no mark, so the skip can never hold",
     "file": "control_ui.html",
     "find": "        rowsEl.setAttribute('data-tf-sig', _tfMark);   // REG-2796 - the mark this paint landed\n",
     "replace": "",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
