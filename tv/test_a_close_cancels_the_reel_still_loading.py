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
            # REG-2118 - the step back now drops the reel itself, so the caption is what proves the late load stayed out
            self.assertEqual(out["beats"], [], "the step back did not let go of the reel (%s): %r" % (settle, out))

    def test_a_full_close_cancels_the_loading_reel(self):
        for settle in ("reject", "error"):
            out = _run({"settle": settle, "during": "close"})
            self.assertEqual(out["caption"], "WINNER CAPTION",
                             "a reel still loading when the theatre closed wrote the closed stage (%s): %r" % (settle, out))
            self.assertEqual(out["beats"], [], "the full close did not let go of the reel (%s): %r" % (settle, out))

    def test_a_full_close_holds_no_reel_and_no_frame(self):
        """REG-2118 (GrokBot tick 429 ACT K49) - thCinema(false) inside the close repainted the stage from the reel it still
        held, so the next shelf door opened over the closed reel's frame. The reel is dropped BEFORE that repaint."""
        if NODE is None:
            raise AssertionError("node is not on this machine - this gate does not skip")
        js = """
var EL = {};
function $(id){ return EL[id] || (EL[id] = { id: id, hidden: false, textContent: '',
  removeAttribute: function(k){ delete this[k]; } }); }
var document = { body: { classList: { add: function(){}, remove: function(){} } } };
var window = {};
var clearTimeout = function(){};
var TH = { open: true, reelFromShelf: false, beats: ['S53-a', 'S53-b'], allBeats: ['S53-a', 'S53-b'], i: 1 };
var SEEN = {};
function thLit(){} function thMore(){}
function thTimeline(){ SEEN.timeline = TH.beats.length; }
function thCinema(){ SEEN.cinema = TH.beats.length; }
$('th-film').src = 'S53-b.jpg'; $('th-film').__url = 'S53-b.jpg';
%s
thClose();
console.log(JSON.stringify({ beats: TH.beats, all: TH.allBeats, seen: SEEN, film: $('th-film').src || null,
                             url: $('th-film').__url }));
""" % _cut(_src(), CLOSE)
        r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, "thClose did not run in node: %s" % r.stderr[-600:])
        out = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual((out["beats"], out["all"]), ([], []), "a closed theatre still holds the reel: %r" % out)
        self.assertEqual(out["seen"].get("cinema"), 0,
                         "leaving cinema repainted the stage while it still held the closed reel: %r" % out)
        self.assertEqual(out["seen"].get("timeline"), 0, "the strip was not rebuilt empty: %r" % out)
        self.assertEqual((out["film"], out["url"]), (None, ""), "the closed reel's frame is still on the stage: %r" % out)


class AFilmlessReelLeavesNothingOfTheLastOne(unittest.TestCase):

    def test_a_reel_with_no_film_clears_the_last_reels_frame_and_line(self):
        """REG-2135 (GrokBot tick 434 ACT) - Session 28 (no film) opened over Session 48: the stage kept 48's frame and
        session line under a caption about 28. Drives the SHIPPED thLoadSession's film-less branch in node."""
        if NODE is None:
            raise AssertionError("node is not on this machine - this gate does not skip")
        s = _src()
        js = """
var EL = {};
function $(id){ return EL[id] || (EL[id] = { id: id, hidden: false, textContent: '', title: '',
  removeAttribute: function(k){ delete this[k]; } }); }
var document = { body: { classList: { add: function(){}, remove: function(){} } } };
var window = {};
var setTimeout = function(){ return 0; }, clearTimeout = function(){};
var TH = { open: true, sn: 48, beats: ['S48-a'], allBeats: ['S48-a'], sessionId: 's_48', sessions: [1, 2, 3], loadGen: 0 };
var SEEN = { ribbon: 0 };
function thRibbon(){ SEEN.ribbon = TH.sn; } function thTimeline(){} function thLit(){} function thShelf(){}
$('th-film').src = 'S48-frame.jpg'; $('th-sess').textContent = 'session 48 of all 216 · id s_48';
function fetch(){ return Promise.resolve({ json: function(){ return Promise.resolve({ sessionId: 's_28', beats: [{ ts: 1 }] }); } }); }
%s
(async function(){ await thLoadSession(28, false, 's_28');
  console.log(JSON.stringify({ sn: TH.sn, film: $('th-film').src || null, sess: $('th-sess').textContent, ribbon: SEEN.ribbon })); })();
""" % _cut(s, LOAD, keep_end=False)
        r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, "thLoadSession did not run in node: %s" % r.stderr[-500:])
        out = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual(out["sn"], 28)
        self.assertIsNone(out["film"], "the last reel's frame is still on the stage of a reel with no film: %r" % out)
        self.assertIn("session 28", out["sess"], "the session line still names the last reel: %r" % out)
        self.assertNotIn("48", out["sess"], "the session line still names the last reel: %r" % out)
        self.assertEqual(out["ribbon"], 28, "the ribbon is left on the last reel until a later repaint: %r" % out)


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
    {"why": "REG-2118 - a full close keeps the reel, and leaving cinema paints its frame back onto the closed stage",
     "file": "tv/control_ui.html",
     "find": "\n    try { TH.beats = []; TH.allBeats = []; TH.i = 0; thTimeline(); } catch (e) {}\n    try { var _cf",
     "replace": "\n    try { var _cf",
     "matches": 1},
    {"why": "REG-2118 - a full close leaves the closed reel's frame on the stage",
     "file": "tv/control_ui.html",
     "find": "    try { var _cf = $('th-film'); if (_cf){ _cf.__want = ''; _cf.__url = ''; _cf.removeAttribute('src'); _cf.title = ''; } } catch (e) {}\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2135 - a reel with no film leaves the last reel's frame and session line on the stage",
     "file": "tv/control_ui.html",
     "find": "      var _nf = $('th-film'); if (_nf && _nf.removeAttribute){ _nf.__want = ''; _nf.__url = ''; _nf.removeAttribute('src'); _nf.title = ''; }\n",
     "replace": "",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
