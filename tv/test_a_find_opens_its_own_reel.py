# -*- coding: utf-8 -*-
"""#293 (REG-2061) - A FIND LINK OPENS ITS OWN REEL, BY ID, NEVER BY THE POSITION ITS NUMBER HAPPENS TO SIT AT.

GrokBot ticks 420-421 on #230 (v3622): TV·D "+51 more" on Session 28 opened "THEATRE · SESSION 28" whose info line read
"session 48/216 · film 19 · all 28 photos" - and opening Session 48 from its own card gave exactly that info line. The find
doors (the "+N more" link, each find card, the dossier montage / evidence / timeline jumps) called
_tvdJumpFind(event, n, frameId, ts) with the session NUMBER only, and thLoadSession reads a bare number as a POSITION in its
newest-first list (REG-1933) - so "28" meant whatever sat 28th. #135 made every DOSSIER door pass the id it carries; these
were the doors it did not reach.

  * every _tvdJumpFind call in the page passes a fifth argument, the reel's own session id;
  * _thJumpToFind hands that id to thLoadSession, which finds the reel by it (and refuses one that comes back under
    another id);
  * a call with no id still opens by number (a door that has no id is not broken).
Drives the SHIPPED _thJumpToFind, cut from control_ui.html and run in node with the theatre stubbed. A missing node raises.
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
FN = ("  async function _thJumpToFind(n, frameId, ts, sid){\n", "\n    } catch (e) {}\n  }\n")


def _src():
    with open(UI, encoding="utf-8") as f:
        return f.read()


def _calls(args):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    s = _src()
    start, end = FN
    if s.count(start) != 1:
        raise AssertionError("_thJumpToFind's anchor matched %d times - re-point this law" % s.count(start))
    i = s.index(start)
    fn = s[i:s.index(end, i) + len(end)]
    js = """
var LOADS = [], TH = { open: true, beats: [] };
var document = { getElementById: function(){ return null; } };
function thOpen(){ return Promise.resolve(); }
function thLoadSession(n, isEntry, sid){ LOADS.push([n, isEntry, sid === undefined ? null : sid]); return Promise.resolve(); }
function thGo(){}
%s
(async function(){ for (var a of %s) { await _thJumpToFind.apply(null, a); } console.log(JSON.stringify(LOADS)); })();
""" % (fn, json.dumps(args))
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut function did not run in node: %s" % r.stderr[-400:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class AFindOpensItsOwnReel(unittest.TestCase):

    def test_the_id_reaches_the_loader(self):
        got = _calls([[28, "", 0, "s_1788000000000_48"], [28, "", 0]])
        self.assertEqual(got[0], [28, True, "s_1788000000000_48"], "the find door's id never reached thLoadSession: %r" % got)
        self.assertEqual(got[1], [28, True, None], "a door with no id must still open by number: %r" % got)

    def test_every_find_door_passes_the_reels_id(self):
        s = _src()
        # one call per line in the page; a regex that stops at the first ')' cuts each call inside (Number(n) || 0)
        lines = [l for l in s.split("\n") if "window._tvdJumpFind(event," in l]
        self.assertGreaterEqual(len(lines), 8, "premise: the find doors moved - this law reads %d" % len(lines))
        bare = [l.strip()[:120] for l in lines if "_sidq" not in l and "sm.sessionId" not in l]
        self.assertEqual(bare, [], "a find door still opens by number alone: %r" % bare[:3])
        self.assertEqual(s.count("  window._tvdJumpFind = function(ev, n, frameId, ts, sid){"), 1,
                         "the jump entry no longer takes the reel's id")


RED_PROOF = [
    {"why": "REG-2061 - a find link opens by its number's position again (Session 28 played Session 48's film)",
     "file": "control_ui.html",
     "find": "await thLoadSession(Number(n) || 1, true, sid ? String(sid) : undefined);\n",
     "replace": "await thLoadSession(Number(n) || 1, true);\n",
     "matches": 1},
    {"why": "REG-2061 - the +N more link stops handing its reel's id",
     "file": "control_ui.html",
     "find": "window._tvdJumpFind(event,' + (Number(n) || 0) + ',&quot;&quot;,0,' + _sidq + ')",
     "replace": "window._tvdJumpFind(event,' + (Number(n) || 0) + ',&quot;&quot;,0)",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
