# -*- coding: utf-8 -*-
"""REG-2087 - A RE-RENDER THAT CANNOT FIND ITS SESSION KEEPS THE DOSSIER HE IS READING; A FRESH OPEN WITH NO MATCH STILL CLOSES.

GrokBot tick 425 on #230: "First click opened the dossier and it closed itself within ~2 s; the second click held." The
art-map repaint and the poll re-render an OPEN dossier through _sessionDossier, and its lookup miss (`if (!sm) hide`) closed
it - a door that can produce exactly that close (whether it was THE cause is unproven). A miss on a dossier already showing
now keeps its last good session; a miss on a fresh open closes as before; a re-render of a different session never borrows.

Drives the SHIPPED two lines, cut from control_ui.html and run in node. A missing node raises.
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
START = "    if (!sm && !ov.hidden && DOSSIER.sm && ((sid && DOSSIER.sid === sid) || (!sid && DOSSIER.n === n))) "
END = "    if (!sm){ ov.hidden = true; return; }\n"


def _run(cases):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    with open(UI, encoding="utf-8") as f:
        s = f.read()
    if s.count(START) != 1:
        raise AssertionError("the keep line matched %d times - re-point this law" % s.count(START))
    i = s.index(START)
    body = s[i:s.index(END, i) + len(END)]
    js = """
function probe(c){ var ov = { hidden: c.hidden }, DOSSIER = c.D, sm = null, n = c.n, sid = c.sid;
%s
  return { kept: !!sm, hidden: ov.hidden, n: n };
}
console.log(JSON.stringify(%s.map(function(c){ var r = probe(c); return r || { kept: false, hidden: true, closed: true }; })));
""" % (body.replace("return; }", "return { kept: false, hidden: ov.hidden }; }"), json.dumps(cases))
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut lines did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


SHOWING = {"n": 28, "sid": "s_28", "sm": {"sessionId": "s_28"}}


class ARerenderKeepsTheDossierHeReads(unittest.TestCase):

    def test_a_rerender_miss_keeps_what_is_showing(self):
        out = _run([{"hidden": False, "D": SHOWING, "sid": "s_28", "n": 28}])[0]
        self.assertEqual((out["kept"], out["hidden"]), (True, False), "a re-render that missed closed the dossier: %r" % out)

    def test_a_fresh_open_with_no_match_still_closes(self):
        out = _run([{"hidden": True, "D": SHOWING, "sid": "s_28", "n": 28}])[0]
        self.assertTrue(out["hidden"], "a fresh open of a session nobody can find kept a dossier: %r" % out)

    def test_a_different_session_never_borrows_the_old_one(self):
        out = _run([{"hidden": False, "D": SHOWING, "sid": "s_99", "n": 99}])[0]
        self.assertTrue(out["hidden"], "a miss for ANOTHER session showed the old dossier under it: %r" % out)


RED_PROOF = [
    {"why": "REG-2087 - a re-render that misses its session closes the dossier he is reading again",
     "file": "tv/control_ui.html",
     "find": "(!sid && DOSSIER.n === n))) { sm = DOSSIER.sm; n = DOSSIER.n; }\n",
     "replace": "(!sid && DOSSIER.n === n))) { }\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
