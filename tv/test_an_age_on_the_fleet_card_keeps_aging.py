# -*- coding: utf-8 -*-
"""REG-1914 - AN AGE ON THE FLEET CARD KEEPS AGING, WITHOUT ASKING THE SERVER AGAIN.

GrokBot (#230): the rail read "also on the site ... no login name 6m ago" from 01:35 to 01:57, then "14m ago"; and again
02:14 -> 02:18 -> "20m ago". The age is computed at paint, and the card repaints on EVENTS only - his ruling, "not a
shorter poll" - so an open card said one age for as long as nobody pressed anything.

The law runs the SHIPPED `_fleetSince`, `_flAge` and `_flAgeTick` (cut from control_ui.html, never re-typed) against a
fake page whose clock moves: a painted label carries its stamp, and the tick re-reads it as the clock moves, with no
fetch. The source half pins both painters to `_flAge` and the 60 s tick to exist.
"""
import io
import json
import os
import shutil
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NODE = shutil.which("node")


def _ui():
    with io.open(os.path.join(ROOT, "tv", "control_ui.html"), encoding="utf-8") as f:
        return f.read()


def _cut(ui, start, end_after):
    a = ui.index(start)
    b = ui.index(end_after, a) + len(end_after)
    return ui[a:b]


def _node(js):
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("node could not run the shipped code - UNKNOWN, not passing: %s" % r.stderr[:400])
    return json.loads(r.stdout.strip().splitlines()[-1])


@unittest.skipUnless(NODE, "no node on this machine - UNMEASURED here, not passing")
class AnAgeKeepsAging(unittest.TestCase):

    def test_a_painted_age_moves_with_the_clock_and_asks_nothing(self):
        ui = _ui()
        since = _cut(ui, "  var _fleetSince = function (iso) {", "    return Math.round(h / 24) + 'd ago';\n  };\n")
        age = _cut(ui, "  var _flAge = function (iso) {", "  };\n")
        tick = _cut(ui, "  if (typeof window !== 'undefined') window._flAgeTick = function (root) {", "    return n;\n  };\n")
        js = r"""
var window = {}; var fetched = 0; function fetch(){ fetched++; }
function escC(s){ return String(s); }
var NOW = Date.parse('2026-10-07T01:41:00Z'); Date.now = function(){ return NOW; };
%s
%s
%s
var html = _flAge('2026-10-07T01:35:00Z');
var t = /data-fl-t="([^"]+)"/.exec(html)[1];
var el = { t: t, textContent: /<span[^>]*>([^<]*)</.exec(html)[1], getAttribute: function(){ return this.t; } };
var doc = { querySelectorAll: function(){ return [el]; } };
var first = el.textContent;
NOW = Date.parse('2026-10-07T01:57:00Z');
var changed = window._flAgeTick(doc);
console.log(JSON.stringify({ first: first, later: el.textContent, changed: changed, fetched: fetched, t: t }));
""" % (since, age, tick)
        o = _node(js)
        self.assertEqual(o["first"], "6m ago", o)
        self.assertEqual(o["later"], "22m ago", "the label stayed at %r while the clock moved 16 minutes (REG-1914)" % o["later"])
        self.assertEqual(o["changed"], 1)
        self.assertEqual(o["fetched"], 0, "the tick asked the server - his ruling is events, not a shorter poll")

    def test_both_painters_stamp_their_age_and_the_tick_runs(self):
        ui = _ui()
        self.assertEqual(ui.count("'<div class=\"ftt-age\">as of ' + _flAge("), 1, "the card's 'as of' age is not stamped")
        self.assertEqual(ui.count("|| 'no login name') + ' ' + _flAge(w.t);"), 1, "the 'also on the site' age is not stamped")
        self.assertEqual(ui.count("setInterval(function () { try { window._flAgeTick(); } catch (e) {} }, 60000);"), 1,
                         "nothing re-reads the stamped ages")
        # REG-1932 - the tick starts only on a page and never holds a process open: the node laws lift this block, and
        # a live interval kept node running until four fleet gates timed out (v3602's pre-flight).
        self.assertEqual(ui.count("    if (typeof document !== 'undefined' && document && document.querySelectorAll) {\n"
                                  "      var _flAgeTimer = setInterval("), 1, "the age tick starts where there is no page")
        self.assertEqual(ui.count("if (_flAgeTimer && typeof _flAgeTimer.unref === 'function') _flAgeTimer.unref();"), 1,
                         "the age tick can hold a node process open")


RED_PROOF = [
    {
        "why": "REG-1932 - the age tick is no longer unref'd: a node law that lifts its block never exits",
        "file": "tv/control_ui.html",
        "find": "      if (_flAgeTimer && typeof _flAgeTimer.unref === 'function') _flAgeTimer.unref();\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-1914 - the tick re-reads nothing: an open card keeps saying '6m ago' for 22 minutes",
        "file": "tv/control_ui.html",
        "find": "      if (els[i].textContent !== say) { els[i].textContent = say; n++; }\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-1914 - the age is painted without its stamp, so no tick can ever re-read it",
        "file": "tv/control_ui.html",
        "find": "    return '<span class=\"fl-age\" data-fl-t=\"' + escC(String(iso || '')) + '\">' + escC(_fleetSince(iso)) + '</span>';\n",
        "replace": "    return '<span class=\"fl-age\">' + escC(_fleetSince(iso)) + '</span>';\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
