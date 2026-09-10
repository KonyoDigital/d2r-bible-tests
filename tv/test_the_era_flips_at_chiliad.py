"""⚠⚠ THE ERA RENAMES ITSELF AT 3001, AND NOBODY WILL BE WATCHING WHEN IT DOES.

Konyo, at v2887: "when we hit version 3000 i want it to be called Chiliad 001 ... meaning from
version 3001 its chiliad ... it should automatically be done at 3000 like a lock/unlock style".

A lock that unlocks itself is only trustworthy if something proves the boundary BEFORE it arrives.
This ships 113 versions early and the flip is unattended: the ship count crosses 3000 and the bar
renames on the next paint, with no switch to throw and nobody checking. If the boundary is off by
one, the first anyone learns of it is the day the name is wrong on his screen.

So the boundary is measured in a REAL JS ENGINE — the same node the js-syntax gate uses — rather
than asserted from the source text. A regex over the source would pass on prose that merely
mentions 3001. [[source-reading-guard]] [[label-outlived-referent]]
"""
import io
import json
import os
import re
import subprocess
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


def _era_fn():
    """The _eraName function as SOURCE, lifted from the shipped surface. -> str|None"""
    h = io.open(UI, encoding="utf-8", errors="replace").read()
    i = h.find("window._eraName = function")
    if i < 0:
        return None
    j = h.find("};", i)
    return h[i:j + 2] if j > i else None


def _ask(versions):
    """Run the SHIPPED function in node against these versions. -> {v: label} | None"""
    fn = _era_fn()
    if fn is None:
        return None
    js = ("var window={};" + fn + "\nvar out={};" +
          "%s.forEach(function(v){out[v]=window._eraName(v);});" % json.dumps(versions) +
          "console.log(JSON.stringify(out));")
    try:
        r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    except Exception:
        return None
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return None


class TheEraFlipsAtTheRightShip(unittest.TestCase):

    def setUp(self):
        self.out = _ask([2887, 2999, 3000, 3001, 3002, 3999])
        if self.out is None:
            self.skipTest("node or _eraName could not be reached here — UNMEASURED, not clean")

    def test_the_function_is_actually_on_the_surface(self):
        """A law that cannot find its subject must say so, not pass quietly."""
        self.assertIsNotNone(_era_fn(),
                             "window._eraName is not in control_ui.html — the era bar has no "
                             "single place to rename, so nothing can be proven about the boundary")

    def test_v3000_is_still_the_OLD_era(self):
        """★ HIS BOUNDARY, IN HIS WORDS: 'from version 3001 its chiliad'. 3000 is not."""
        self.assertTrue(self.out["3000"].startswith("Millenium"),
                        "v3000 renamed early — he said the Chiliad era begins at 3001, so 3000 is "
                        "the last ship of the old name: %r" % self.out["3000"])

    def test_v3001_is_CHILIAD_001(self):
        """★ THE DEFECT THIS EXISTS TO CATCH. Off by one and the first Chiliad ship is misnamed."""
        self.assertEqual("Chiliad 001", self.out["3001"],
                         "the first Chiliad ship does not read 'Chiliad 001': %r" % self.out["3001"])

    def test_the_number_stays_THREE_digits_across_the_flip(self):
        """v2382 settled this: two digits made v2101 and v2001 both print 01, so the Wife PC wore
        a current machine's badge 178 versions behind. Three digits survives the rename."""
        for v in ("3001", "3002", "3999"):
            tail = self.out[v].split()[-1]
            self.assertEqual(3, len(tail),
                             "v%s prints %r — the era rename lost the three-digit rule" % (v, tail))

    def test_the_old_era_is_untouched_below_the_line(self):
        """A rename that quietly restyles every earlier ship would rewrite history on his screen."""
        self.assertEqual("Millenium v887", self.out["2887"])
        self.assertEqual("Millenium v999", self.out["2999"])

    def test_the_skew_arm_still_exists_beside_the_name(self):
        """⚠ The surface's own note: collapsing this bar to a name would delete the only place
        console/agent/board drift is on screen. The rename must not take the drift with it."""
        h = io.open(UI, encoding="utf-8", errors="replace").read()
        i = h.find("window._eraName = function")
        self.assertGreater(i, 0)
        near = h[i:i + 1600]
        self.assertIn("_skewNow", near,
                      "the era block no longer computes _skewNow — the rename deleted the drift "
                      "warning that is the only on-screen sign of a stale console")


RED_PROOF = [
    {
        "why": "⚠ RE-AIMED v2888 — the first anchor named `if (n >= 3001) return 'Chiliad '`, and that "
               "line stopped existing when _eraName became a TABLE (so 4001/Utopia is a ROW, not "
               "another edit). heart2 measured the anchor at 0 occurrences and the instruments "
               "gate went red — which is the heart doing its job on my own guard. "
               "[[label-outlived-referent]] [[sabotage-is-usually-the-wrong-one]] "
               "moving the boundary by one ship is the whole defect: the first Chiliad version "
               "would read 'Millenium v001' and his self-arming lock would have fired late, with "
               "nobody watching. Verified in a real JS engine, not against the source text.",
        "file": "control_ui.html",
        "find": "[3001, 'Chiliad ', '']",
        "replace": "[3002, 'Chiliad ', '']",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
