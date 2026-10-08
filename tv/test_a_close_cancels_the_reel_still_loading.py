# -*- coding: utf-8 -*-
"""REG-2091 - A CLOSE CANCELS THE REEL STILL LOADING; AN OVERTAKEN LOAD SAYS NOTHING.

The Grok CLI on v3624's thCloseReel (2026-10-08, a targeted look): the step back to the shelf "never increments TH.gen"
- so a reel still loading when ✕ is pressed lands afterwards and plays under the shelf. Re-measured: thLoadSession
stamps TH.loadGen, not TH.gen, and NEITHER close moved it - the shelf-back path (TH.open stays true) let the late
answer set TH.playing and paint, and thClose left it free to write a closed stage. Swept to the load's own error path:
an overtaken load that then timed out still wrote its caption and ran TH.beats = [] over the reel that won.
Drives the SHIPPED thLoadSession, thCloseReel and thClose, cut from control_ui.html and run in node over stubs, with the
fetch held open while the close happens. A missing node raises; this law does not skip.
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
LOAD = ("  async function thLoadSession(n, isEntry, sid){\n", "\n  function thPickEntrySession(strict){")
REEL = ("  function thCloseReel(){\n", "    thClose();\n  }\n")
CLOSE = ("  function thClose(){\n", "paint(window.__lastStatus); } catch(e){}\n  }\n")


def _src():
    with open(UI, encoding="utf-8") as f:
        return f.read()


def _cut(s, pair, keep_end=True):
    start, end = pair
    if s.count(start) != 1:
        raise AssertionError("anchor %r matched %d times - re-point this law" % (start[:40], s.count(start)))
    i = s.index(start)
    j = s.index(end, i)
    fn = s[i:j + len(end)] if keep_end else s[i:j]
    if fn.count("{") != fn.count("}"):
        raise AssertionError("the cut of %r is not a whole function" % start.strip()[:40])
    return fn


def _run(scenario):
    """scenario: how the held fetch settles ('reject' | 'error') and what happens while it is held
    ('none' | 'reel' | 'close'). -> what the stage holds afterwards."""
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    s = _src()
    js = """
var EL = {};
function $(id){ return EL[id] || (EL[id] = { id: id, hidden: false, textContent: '' }); }
var document = { body: { classList: { add: function(){}, remove: function(){} } } };
var window = {};
// the load's 12 s abort timer is not what this law asks about, and a real one holds node open for 12 s a run
var setTimeout = function(){ return 0; }, clearTimeout = function(){};
var TH = { open: true, reelFromShelf: false, shelfIsDoor: true, playing: false, beats: ['WINNER'], sessions: [] };
function thShelf(on){ if (on) $('th-shelfov').hidden = false; }
function thLit(){} function thRibbon(){} function thMore(){} function thCinema(){}
var SC = %s, HOLD = null;
function fetch(){ return new Promise(function(res, rej){ HOLD = { res: res, rej: rej }; }); }
%s
%s
%s
(async function(){
  $('th-shelfov').hidden = true;
  var p = thLoadSession(3, false, 'sid-3');
  await Promise.resolve();
  $('th-caption').textContent = 'WINNER CAPTION';
  if (SC.during === 'reel') { TH.open = true; TH.reelFromShelf = true; thCloseReel(); }
  if (SC.during === 'close') thClose();
  if (SC.settle === 'reject') HOLD.rej(new Error('aborted'));
  else HOLD.res({ json: function(){ return Promise.resolve({ error: 'LATE ANSWER' }); } });
  try { await p; } catch (e) { console.log(JSON.stringify({ threw: String(e) })); return; }
  console.log(JSON.stringify({ beats: TH.beats, caption: $('th-caption').textContent, playing: TH.playing,
                               shelf: !$('th-shelfov').hidden, loadGen: TH.loadGen }));
})();
""" % (json.dumps(scenario), _cut(s, LOAD, keep_end=False), _cut(s, REEL), _cut(s, CLOSE))
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut functions did not run in node: %s" % r.stderr[-600:])
    out = json.loads(r.stdout.strip().splitlines()[-1])
    if "threw" in out:
        raise AssertionError("thLoadSession threw in node: %s" % out["threw"])
    return out


class ACloseCancelsTheReelStillLoading(unittest.TestCase):

    def test_baseline_a_load_nobody_overtook_still_speaks(self):
        """Without a close, the late answer IS this load's: it writes its caption and clears the stage - so the two
        cases below can only pass because the close cancelled it, never because the harness hides the write."""
        out = _run({"settle": "reject", "during": "none"})
        self.assertIn("did not answer", out["caption"], "premise: an un-overtaken failed load says so: %r" % out)
        self.assertEqual(out["beats"], [])
        out = _run({"settle": "error", "during": "none"})
        self.assertIn("LATE ANSWER", out["caption"], "premise: an un-overtaken answer is painted: %r" % out)

    def test_the_step_back_to_the_shelf_cancels_the_loading_reel(self):
        for settle in ("reject", "error"):
            out = _run({"settle": settle, "during": "reel"})
            self.assertTrue(out["shelf"], "premise: ✕ stepped back to the shelf: %r" % out)
            self.assertEqual(out["caption"], "WINNER CAPTION",
                             "a reel still loading when ✕ stepped back to the shelf wrote the stage anyway (%s): %r"
                             % (settle, out))
            self.assertEqual(out["beats"], ["WINNER"], "the late load cleared the stage under the shelf (%s)" % settle)

    def test_a_full_close_cancels_the_loading_reel(self):
        for settle in ("reject", "error"):
            out = _run({"settle": settle, "during": "close"})
            self.assertEqual(out["caption"], "WINNER CAPTION",
                             "a reel still loading when the theatre closed wrote the closed stage (%s): %r" % (settle, out))
            self.assertEqual(out["beats"], ["WINNER"], "the late load cleared a closed stage's beats (%s)" % settle)


RED_PROOF = [
    {"why": "REG-2091 - the step back to the shelf leaves the loading reel free to land under the shelf",
     "file": "tv/control_ui.html",
     "find": "      TH.loadGen = (TH.loadGen || 0) + 1;   /* REG-2091 - a reel still loading must not land and play under the shelf */\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2091 - a full close leaves the loading reel free to write the closed stage",
     "file": "tv/control_ui.html",
     "find": "    TH.loadGen = (TH.loadGen || 0) + 1;   /* REG-2091 - and any REEL still loading: it must not paint a closed stage */\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2091 - an overtaken load's timeout clears the winner's beats again",
     "file": "tv/control_ui.html",
     "find": "      if (gen !== TH.loadGen) return;   /* REG-2091 - an overtaken load's timeout must not clear the winner's beats or caption */\n",
     "replace": "",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
