# -*- coding: utf-8 -*-
"""REG-1906 - A SWEEP NEVER RE-TICKS WHAT HE UN-TICKED. Driven on the SHIPPED board.

d2r_grailUnfound is USER TRUTH: only he may overrule his own un-tick, and he does it by tapping the name in
"marked NOT found, by you". The testing-phase pre-run (UNTICK-01, 2026-10-07) found the Chronicle sweep's register
door never asked: chronicleApply sends every proposed unique through toggleOwned, and toggleOwned DELETES the name
from d2r_grailUnfound in the same call - so a sweep that read an item he had un-ticked re-ticked it and erased the
un-tick, with nothing on screen saying so. (Run on his real ledger with The Cat's Eye un-ticked, the console's
cross-reference also called it "new", which is the number that invites the press.)

WHAT THIS LAW HOLDS, each case driven in bible.html itself in its own headless Chrome (never re-typed):
  * THE POSITIVE CONTROL - a proposed unique he did NOT un-tick lands in d2r_foundLog in the same apply. A door
    that wrote nothing at all would pass every refusal below.
  * an un-ticked unique is HELD: not in d2r_foundLog, still in d2r_grailUnfound, named in res.untickedHeld;
  * the same, when the sweep spells it with a CURLY apostrophe (his store holds both byte forms);
  * an un-ticked SET PIECE in the sets half is held the same way, and d2r_setPieces does not gain it.
  * REG-2002 - his RECORDED ruling (the v1693 one-shot's lane) overrules his un-tick and says so; a lane that only
    sounds like a ruling is still held.
Game item names only - never his store. NO CHROME AT ALL = a declared skip, never a pass.
"""
import json
import os
import socket
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass


def _free_port():
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
    finally:
        s.close()


# BEFORE the import: render_check reads its port once, at import time.
if not os.environ.get("TV_RENDER_PORT"):
    os.environ["TV_RENDER_PORT"] = str(_free_port())
import render_check as RC  # noqa: E402

BIBLE = os.path.join(ROOT, "bible.html")
READY = "!!(window.chronicleApply&&window.LSR&&window.toggleOwned&&window.toggleSetPiece)"
UNTICKED = "The Cat's Eye"
CONTROL = "Nagelring"
PIECE = "Aldur's Advance (boots)"
RULED = "Gravepalm"          # one of the nine his v1693 ruling names


class Board(object):
    def __init__(self):
        self.t = None

    def open(self):
        if not RC._chrome_up():
            raise AssertionError("Chrome is INSTALLED at %s and would not start on :%d - a failure on a venue "
                                 "that is supposed to measure" % (RC.CHROME, RC.PORT))
        self.t = RC._Tab("about:blank")
        self.t.send("Page.enable")
        self.t.send("Runtime.enable")
        self.navigate()
        return self

    def navigate(self):
        self.t.send("Page.navigate", url="file://" + BIBLE)
        for _ in range(240):
            time.sleep(0.25)
            try:
                if self.t.ev(READY) is True:
                    time.sleep(0.4)
                    return
            except Exception:
                pass
        raise AssertionError("bible.html never exposed chronicleApply in 60 s - UNKNOWN, not passing")

    def run(self, body):
        r = self.t.ev("(async function(){ var OUT = {}; " + body + "\n; return JSON.stringify(OUT); })()")
        if r is None:
            raise AssertionError("the page threw: %s" % (self.t.last_exc,))
        return json.loads(r)

    def seed(self, stores):
        self.run("var S = %s; Object.keys(S).forEach(function(k){ if (S[k] === null) window.LSR.removeItem(k);"
                 " else window.LSR.setItem(k, typeof S[k] === 'string' ? S[k] : JSON.stringify(S[k])); });"
                 % json.dumps(stores))
        self.navigate()

    def close(self):
        try:
            if self.t is not None:
                self.t.close()
        except Exception:
            pass
        RC._chrome_down()


_B = {}


def board():
    if "b" not in _B:
        _B["b"] = Board().open()
    return _B["b"]


def tearDownModule():
    b = _B.pop("b", None)
    if b is not None:
        b.close()


def apply_world(b, unticked, wouldAdd, lanes=None):
    """A world where `unticked` are his un-ticks and nothing is found, then ONE chronicleApply of `wouldAdd`."""
    prop = {"wouldAdd": wouldAdd}
    if lanes is not None:
        prop["lanes"] = lanes
    b.seed({"d2r_grailUnfound": dict((n, 1) for n in unticked), "d2r_foundLog": {}, "d2r_owned": [],
            "d2r_setPieces": [], "d2r_muleAssign": {}, "d2r_chronApplied": None, "d2r_rwProfile": "fresh"})
    return b.run("var res = window.chronicleApply(%s);"
                 "OUT.res = { uniques: res.uniques, sets: res.sets, held: res.untickedHeld || [],"
                 " overruledBy: res.untickOverruledBy || '' };"
                 "OUT.foundLog = Object.keys(JSON.parse(window.LSR.getItem('d2r_foundLog') || '{}'));"
                 "OUT.setPieces = JSON.parse(window.LSR.getItem('d2r_setPieces') || '[]');"
                 "OUT.unfound = Object.keys(JSON.parse(window.LSR.getItem('d2r_grailUnfound') || '{}'));"
                 % json.dumps(prop))


@unittest.skipUnless(os.path.exists(RC.CHROME), "no Chrome/Chromium on this machine, so the shipped board was not "
                     "driven - UNMEASURED here, not passing")
class ASweepNeverReticksWhatHeUnticked(unittest.TestCase):

    def test_1_the_positive_control_lands_and_the_unticked_unique_is_held(self):
        o = apply_world(board(), [UNTICKED], {"uniques": [{"name": UNTICKED}, {"name": CONTROL}]})
        self.assertIn(CONTROL, o["foundLog"], "premise: the apply wrote nothing at all, so its refusals below "
                                              "prove nothing (%s)" % o)
        self.assertNotIn(UNTICKED, o["foundLog"], "the sweep RE-TICKED an item he un-ticked (REG-1906): %s" % o)
        self.assertIn(UNTICKED, o["unfound"], "the sweep ERASED his un-tick (REG-1906): %s" % o)
        self.assertIn(UNTICKED, o["res"]["held"], "the held name is not carried out to the receipt: %s" % o)
        self.assertNotIn(UNTICKED, o["res"]["uniques"])

    def test_2_a_curly_apostrophe_is_the_same_un_tick(self):
        curly = UNTICKED.replace("'", "’")
        o = apply_world(board(), [UNTICKED], {"uniques": [{"name": curly}]})
        self.assertNotIn(curly, o["foundLog"], "the curly spelling slipped past his un-tick: %s" % o)
        self.assertNotIn(UNTICKED, o["foundLog"])
        self.assertIn(UNTICKED, o["unfound"])

    def test_3_an_unticked_set_piece_is_held_in_the_sets_half(self):
        o = apply_world(board(), [PIECE], {"sets": [{"name": PIECE}]})
        self.assertNotIn(PIECE, o["setPieces"], "the sweep re-ticked a set piece he un-ticked: %s" % o)
        self.assertIn(PIECE, o["unfound"])
        self.assertIn(PIECE, o["res"]["held"])

    def test_4_his_recorded_ruling_overrules_his_un_tick(self):
        """REG-2002 - the v1693 one-shot is HIS ruling on names he un-ticked; held, it applied nothing and set its flag."""
        o = apply_world(board(), [RULED], {"uniques": [{"name": RULED}]}, lanes=["v1693-konyo-ruling-the-nine"])
        self.assertIn(RULED, o["foundLog"], "his recorded ruling was held by his own un-tick (REG-2002): %s" % o)
        self.assertNotIn(RULED, o["unfound"], "the ruled name kept its un-tick, so it re-surfaces as a conflict")
        self.assertEqual(o["res"]["overruledBy"], "v1693-konyo-ruling-the-nine", "the receipt does not say which "
                         "ruling overruled the un-tick: %s" % o)
        self.assertEqual(o["res"]["held"], [])

    def test_5_a_lane_that_only_sounds_like_a_ruling_is_still_held(self):
        o = apply_world(board(), [UNTICKED], {"uniques": [{"name": UNTICKED}]},
                        lanes=["sweep", "v9999-konyo-ruling-not-recorded"])
        self.assertNotIn(UNTICKED, o["foundLog"], "a lane nobody recorded overruled his un-tick: %s" % o)
        self.assertIn(UNTICKED, o["res"]["held"])
        self.assertEqual(o["res"]["overruledBy"], "")

    def test_6_the_ruling_overrules_only_the_names_it_ruled_on(self):
        """REG-2005 (the #231 eye on v3605) - a name he un-ticked that the ruling does not list stays held beside it."""
        o = apply_world(board(), [RULED, UNTICKED], {"uniques": [{"name": RULED}, {"name": UNTICKED}]},
                        lanes=["v1693-konyo-ruling-the-nine"])
        self.assertIn(RULED, o["foundLog"], "premise: the ruled name did not apply, so the hold below proves nothing")
        self.assertNotIn(UNTICKED, o["foundLog"], "a name outside the ruling rode in on its lane (REG-2005): %s" % o)
        self.assertIn(UNTICKED, o["unfound"])
        self.assertIn(UNTICKED, o["res"]["held"])


RED_PROOF = [
    {
        "why": "REG-2005 - the ruling's lane overrules EVERY un-tick in its proposal, not only the nine it names",
        "file": "bible.html",
        "find": "        window._CHRON_HIS_RULINGS[_ruled].forEach(function(n){ window._chUntickedNow.delete(window._chronUntickedFold(n)); });\n",
        "replace": "        window._chUntickedNow = new Set();\n",
        "matches": 1,
    },
    {
        "why": "REG-2002 - his recorded ruling is held by his own un-tick again: the v1693 nine apply nothing",
        "file": "bible.html",
        "find": "        window._CHRON_HIS_RULINGS[_ruled].forEach(function(n){ window._chUntickedNow.delete(window._chronUntickedFold(n)); });\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-2002 - any lane that says 'ruling' overrules his un-tick, so a sweep can name one",
        "file": "bible.html",
        "find": "if (Array.isArray(window._CHRON_HIS_RULINGS[l[i]])) return String(l[i]);",
        "replace": "if (/ruling/.test(l[i])) return String(l[i]);",
        "matches": 1,
    },
    {
        "why": "REG-1906 - the uniques half stops asking his un-ticks: a swept unique he un-ticked is ticked again and "
               "his un-tick erased",
        "file": "bible.html",
        "find": "      if (window._chronHeldByUntick(res, n)) return;   // REG-1906 — his un-tick stands\n      try {\n",
        "replace": "      try {\n",
        "matches": 1,
    },
    {
        "why": "REG-1906 - the un-tick store reads as empty, so every un-tick is overruled by the sweep",
        "file": "bible.html",
        "find": "Object.keys(un).forEach(function(k){ if (un[k]) out.add(window._chronUntickedFold(k)); });",
        "replace": "Object.keys(un).forEach(function(k){ if (false) out.add(window._chronUntickedFold(k)); });",
        "matches": 1,
    },
    {
        "why": "REG-1906 - the sets half stops asking: a set piece he un-ticked is ticked again by the sweep",
        "file": "bible.html",
        "find": "      if (window._chronHeldByUntick(res, n)) return;   // REG-1906 — his un-tick stands\n      /* #246 W2",
        "replace": "      /* #246 W2",
        "matches": 1,
    },
    {
        "why": "REG-1906 - the fold forgets the curly apostrophe, so 'The Cat’s Eye' slips past his un-tick of "
               "'The Cat's Eye'",
        "file": "bible.html",
        "find": "return String(n || '').replace(/[\\u2019\\u02bc\\u2018]/g, \"'\")",
        "replace": "return String(n || '')",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
