# -*- coding: utf-8 -*-
"""#279 (REG-2057) - A REPLAY HOLDS ON A BEAT WITH NO PHOTO; THE STUCK-STAGE SELF-HEAL CLOSES ONLY A STAGE THAT NEVER LOADED.

GrokBot tick 418 on #230 (v3621, K07-K09): "Theatre for Session 41 closes itself with no input" - both opens closed within
~25 s; the second, mouse parked, played to T+8:56, at 11:43:29 the picture dropped to a caption-only beat and by 11:43:40 the
theatre was gone. Session 41 recorded only 8 stills (its film lane was off). The theatre's stuck-black self-heal closes a
stage whose film has no picture for ~12 s with no touch - and a beat the reel carries without a photo has no picture by
design. GrokBot asked: "should a replay that runs out of stills stop and hold, rather than close?" - it holds.

  * _thStageHolds: painted+loaded, touched, an overlay up -> holds (as before); a caption-only beat (no frame, or a
    frame not on disk) -> holds; a stage with a photo beat that never painted -> does not (the self-heal still has teeth);
  * the self-heal asks _thStageHolds with the current beat;
  * the caption no longer says "pruned" (the prune is OFF): no frame -> "no photo for this read", a missing frame ->
    "not on disk".
Drives the SHIPPED _thStageHolds, cut from control_ui.html and run in node. A missing node raises; this law does not skip.
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
FN = ("  function _thStageHolds(st){\n", "    return false;\n  }\n")
CALL = "        if (_thStageHolds({ painted: painted, loaded: loaded, ink: ink, touched: touchedRecently, overlay: _ovUp, beat: _cb })) {\n"


def _src():
    with open(UI, encoding="utf-8") as f:
        return f.read()


def _holds(states):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    s = _src()
    start, end = FN
    if s.count(start) != 1:
        raise AssertionError("_thStageHolds's anchor matched %d times - re-point this law" % s.count(start))
    i = s.index(start)
    fn = s[i:s.index(end, i) + len(end)]
    js = "var window = {};\n%s\nconsole.log(JSON.stringify(%s.map(_thStageHolds)));\n" % (fn, json.dumps(states))
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut function did not run in node: %s" % r.stderr[-400:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class AReplayHoldsOnABeatWithNoPhoto(unittest.TestCase):

    def test_a_caption_only_beat_holds_the_stage(self):
        got = _holds([{"painted": False, "loaded": False, "beat": {"n": 9}},
                      {"painted": True, "loaded": False, "beat": {"n": 9, "frame": "f9.jpg", "frameOk": False}}])
        self.assertEqual(got, [True, True], "the self-heal would close a replay standing on a beat with no photo: %r" % got)

    def test_a_photo_beat_that_never_painted_still_closes(self):
        got = _holds([{"painted": False, "loaded": False, "beat": {"n": 3, "frame": "f3.jpg"}},
                      {"painted": False, "loaded": False}])
        self.assertEqual(got, [False, False], "the self-heal lost its teeth for a stage that never loaded: %r" % got)

    def test_the_ordinary_reasons_still_hold(self):
        got = _holds([{"painted": True, "loaded": True, "ink": None, "beat": {"frame": "f.jpg"}},
                      {"touched": True, "beat": {"frame": "f.jpg"}}, {"overlay": True, "beat": {"frame": "f.jpg"}},
                      {"painted": True, "loaded": True, "ink": False, "beat": {"frame": "f.jpg"}}])
        self.assertEqual(got, [True, True, True, False], got)

    def test_the_self_heal_asks_it_and_the_caption_never_says_pruned(self):
        s = _src()
        self.assertEqual(s.count(CALL), 1, "the stuck-stage self-heal no longer asks _thStageHolds with the current beat")
        self.assertEqual(s.count("photo pruned from disk"), 0, "a caption still says 'pruned' while the prune is OFF")
        self.assertEqual(s.count("no photo for this read — the reel kept its caption only"), 1)


RED_PROOF = [
    {"why": "REG-2057 - a replay on a caption-only beat closes itself again",
     "file": "control_ui.html",
     "find": "    if (b && (b.frameOk === false || !b.frame)) return true;\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2057 - the self-heal stops asking about the current beat",
     "file": "control_ui.html",
     "find": "overlay: _ovUp, beat: _cb })) {\n",
     "replace": "overlay: _ovUp, beat: null })) {\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
