# -*- coding: utf-8 -*-
"""REG-2085 - A TZ ZONE'S "SUPER-UNIQUES" ROW HOLDS ONLY SUPER-UNIQUES; WHAT ELSE IS THERE IS SAID ON ITS OWN ROW.

The #231 code seat, on May's ac32a033 and re-measured at HEAD 2026-10-08: zoneDetailHtml split z.unique on the middle dot and
painted every piece as a super-unique chip - Worldstone Keep's 'Random Champion/Unique packs · multiple chests' became two
"super-uniques". And the TC87 line said "Terror LIFTS this zone to TC87" beside WSK's own note "WSK L3 hits TC87 even
Hell-only". Now a name the super-unique index knows is a chip, anything else sits on an 'also here' row, and the TC87 line
says what the zone is when terrorized.

Drives the SHIPPED chip lines, cut from bible.html and run in node with the index stubbed. A missing node raises.
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

PAGE = os.path.join(os.path.dirname(HERE), "bible.html")
START = "  const superHtml = supers.filter(s => suIndexByName(s) >= 0)"
END = ".join(' · ');\n"


def _src():
    with open(PAGE, encoding="utf-8") as f:
        return f.read()


def _rows(unique):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    s = _src()
    if s.count(START) != 1:
        raise AssertionError("the chip lines' anchor matched %d times - re-point this law" % s.count(START))
    i = s.index(START)
    j = s.index(END, s.index("  const alsoHtml = ", i)) + len(END)
    js = """
var KNOWN = { "Eldritch the Rectifier (Frigid Highlands)": 3, "Shenk the Overseer (Bloody Foothills)": 4 };
function suIndexByName(n){ return KNOWN.hasOwnProperty(n) ? KNOWN[n] : -1; }
var supers = %s.split('·').map(function(s){ return s.trim(); }).filter(Boolean);
%s
console.log(JSON.stringify({ su: superHtml, also: alsoHtml }));
""" % (json.dumps(unique), s[i:j])
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the chip lines did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class TheSuperUniquesRowHoldsSuperUniques(unittest.TestCase):

    def test_worldstone_keeps_packs_and_chests_are_not_super_uniques(self):
        out = _rows("Random Champion/Unique packs · multiple chests")
        self.assertEqual(out["su"], "", "a chest or a random pack was painted as a super-unique: %r" % out["su"])
        self.assertIn("multiple chests", out["also"])
        self.assertIn("Random Champion/Unique packs", out["also"])

    def test_a_real_super_unique_stays_a_clickable_chip(self):
        out = _rows("Shenk the Overseer (Bloody Foothills) · Eldritch the Rectifier (Frigid Highlands)")
        self.assertEqual(out["su"].count('class="zd-su" data-su-idx='), 2, out["su"])
        self.assertEqual(out["also"], "")

    def test_the_tc87_line_does_not_credit_terror_with_a_ceiling_the_zone_already_has(self):
        s = _src()
        self.assertEqual(s.count("? `Terrorized, this zone is mlvl ${z.mlvl} / TC87"), 1, "the TC87 line changed shape")
        self.assertEqual(s.count("Terror lifts this zone to mlvl ${z.mlvl} / TC87"), 0, "the TC87 line credits terror again")
        self.assertEqual(s.count("<span class=\"zd-k\">also here</span>"), 1, "nothing prints the 'also here' row")


RED_PROOF = [
    {"why": "REG-2085 - every dot-separated piece is a super-unique chip again (WSK's chests)",
     "file": "bible.html",
     "find": "  const superHtml = supers.filter(s => suIndexByName(s) >= 0).map(",
     "replace": "  const superHtml = supers.filter(s => true).map(",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
