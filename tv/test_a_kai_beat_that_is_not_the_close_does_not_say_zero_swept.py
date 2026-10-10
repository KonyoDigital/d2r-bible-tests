# -*- coding: utf-8 -*-
"""REG-2154 - a kai beat that is not the session close must not say 0 frames swept.

GrokBot, #277: the theatre banner said "0 frames swept · 0 frames held text no eye read"
while the dossier, from the session summary, said the reel had misses. thCaption used
scanned||0 on every kai beat that carried no texts, so a judge, a grounded name, a
register row, and a beat with neither count all wore the close line.

Drives the shipped _thKaiCaption, cut from control_ui.html and run in node.
"""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
from cb_node_harness import NODE  # noqa: E402

UI = os.path.join(HERE, "control_ui.html")


def _src():
    with open(UI, encoding="utf-8") as f:
        return f.read()


def _fn(src):
    start = src.find("function _thKaiCaption(b){")
    if start < 0:
        raise AssertionError("_thKaiCaption is gone - the close line has no owner")
    if src.find("function _thKaiCaption(b){", start + 1) != -1:
        raise AssertionError("_thKaiCaption is declared more than once")
    i = src.find("{", start)
    depth = 0
    for j in range(i, len(src)):
        ch = src[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return src[start:j + 1]
    raise AssertionError("_thKaiCaption never closed")


def _say(cases):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    fn = _fn(_src())
    js = (
        "function esc(s){ return String(s == null ? '' : s); }\n%s\n"
        "console.log(JSON.stringify(%s.map(_thKaiCaption)));\n"
    ) % (fn, json.dumps(cases))
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("_thKaiCaption did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class AKaiBeatThatIsNotTheCloseDoesNotSayZeroSwept(unittest.TestCase):

    def test_the_caption_asks_the_helper_and_the_zero_fallback_is_gone(self):
        s = _src()
        self.assertEqual(s.count("return _thKaiCaption(b);"), 1,
                         "thCaption no longer asks the helper, so the close line can drift back")
        self.assertNotIn("kk.scanned||0", s, "a missing scanned is zero again")
        self.assertNotIn("kk.missedFrames||0", s, "a missing missedFrames is zero again")

    def test_a_beat_with_no_counts_is_not_the_close(self):
        out = _say([{"lane": "kai", "kai": {}}])[0]
        self.assertIn("not the session close", out)
        self.assertNotIn("0 frames swept", out)
        self.assertNotIn("KAI CLOSED", out)

    def test_a_judge_a_grounded_name_and_a_register_are_not_the_close(self):
        judge, grounded, reg = _say([
            {"lane": "kai", "kai": {"judge": {"name": "Flame Rift", "tier": "unique"}}},
            {"lane": "kai", "kai": {"grounded": ["Heart of the Oak"]}},
            {"lane": "kai", "kai": {"register": {"count": 12}}},
        ])
        for row in (judge, grounded, reg):
            self.assertNotIn("0 frames swept", row, row)
            self.assertNotIn("KAI CLOSED", row, row)
        self.assertIn("Flame Rift", judge)
        self.assertIn("Heart of the Oak", grounded)
        self.assertIn("12 items witnessed", reg)

    def test_unread_text_stays_on_its_frame(self):
        out = _say([{"lane": "kai", "kai": {"texts": ["Flame Rift"]}, "ts": 1700000000000}])[0]
        self.assertIn("unread text on this frame", out)
        self.assertIn("Flame Rift", out)
        self.assertNotIn("KAI CLOSED", out)

    def test_a_measured_zero_still_prints_zero(self):
        out = _say([{"lane": "kai", "kai": {"scanned": 0, "missedFrames": 0}}])[0]
        self.assertIn("KAI CLOSED THE SESSION", out)
        self.assertIn("0 frames swept", out)
        self.assertIn("0 frames held text no eye read", out)

    def test_a_missing_half_stays_unknown(self):
        out = _say([{"lane": "kai", "kai": {"missedFrames": 8}}])[0]
        self.assertIn("KAI CLOSED THE SESSION", out)
        self.assertIn("frames swept UNKNOWN", out)
        self.assertIn("8 frames held text no eye read", out)
        self.assertNotIn("0 frames swept", out)

    def test_the_summary_prints_the_numbers_it_carries(self):
        out = _say([{"lane": "kai", "kai": {"scanned": 217, "missedFrames": 108}}])[0]
        self.assertIn("217 frames swept", out)
        self.assertIn("108 frames held text no eye read", out)


RED_PROOF = [
    {
        "why": "REG-2154 - a beat with no counts wears the close line and a missing scanned becomes 0 again",
        "file": "tv/control_ui.html",
        "find": "if (!(sweptKnown || heldKnown)) return '<span style=\"color:#f0c060\">KAI · this beat is not the session close</span>';",
        "replace": "if (!(sweptKnown || heldKnown)) return '<span style=\"color:#f0c060\">KAI CLOSED THE SESSION · ' + (kk.scanned||0) + ' frames swept · ' + (kk.missedFrames||0) + ' frames held text no eye read</span>';",
        "matches": 1,
    },
    {
        "why": "REG-2154 - a measured scanned of 0 is treated as missing, so the honest zero disappears",
        "file": "tv/control_ui.html",
        "find": "var sweptKnown = typeof kk.scanned === 'number';",
        "replace": "var sweptKnown = !!kk.scanned;",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
