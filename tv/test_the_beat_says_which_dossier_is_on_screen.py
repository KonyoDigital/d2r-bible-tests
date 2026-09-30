# -*- coding: utf-8 -*-
"""v3538 — THE PAGE SAYS WHICH SESSION'S DOSSIER IS ON SCREEN, BY NUMBER.

GrokBot's rotating visual pass on its PC (2026-10-01, relayed by him): the route rotated - zone, scroll depth and card
index all changed every tick - and the session that opened did not. The shelf's top tiles are always "Best run · Session
28" and "Most reads · Session 28", so every theatre shot said 28 whether or not anything had opened; on the last eight
ticks seven never left the shelf, and they still counted as opened, because "opened" meant the word Session was on
screen. Its driver (click by session number) is its own; what it cannot do without the console is VERIFY: nothing the
console published said which dossier - if any - was actually showing. `theatreOpen` is a bare boolean.

  · DRIVEN in node, the real page code cut by its markers: _sessionDossier(87) stamps the overlay with its number, and
    the beat then reads 87 off the overlay - the join. Hidden, zero-size and absent overlays read null (none shown); an
    overlay with no number, or a read that throws, reads "UNKNOWN" - never a guess, and never a throw that would
    silence the whole beat.
  · DRIVEN in python: the real ui_beat_record -> status_payload path publishes it under uiBeat.dossier; a page that did
    not send the key reads UNKNOWN, never "none shown".
No node on this PC = the page half SKIPS with its reason; a skip is not a pass. RED_PROOF below. [[unknown-stays-unknown]]
"""
import io
import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fixture_ledgers as _fx_ledgers  # noqa: E402  never HIS eagle ledgers
_fx_ledgers.redirect()

UI = os.path.join(HERE, "control_ui.html")
NODE = shutil.which("node")


def _src():
    with io.open(UI, encoding="utf-8") as fh:
        return fh.read()


def _between(src, begin, end):
    i = src.index(begin)
    j = src.index(end, i)
    return src[i + len(begin):j]


def _beat_field():
    return _between(_src(), "/* ⟦BEAT DOSSIER BEGIN⟧ */", "/* ⟦BEAT DOSSIER END⟧ */")


def _open_fn():
    return _between(_src(), "/* ⟦SESSION DOSSIER BEGIN⟧ */", "/* ⟦SESSION DOSSIER END⟧ */")


def _node(script):
    r = subprocess.run([NODE, "-e", script], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=60)
    if r.returncode != 0:
        raise AssertionError("the page code would not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


_FAKE_OV = r"""
function makeOv(o){
  o = o || {};
  var attrs = {};
  return { hidden: o.hidden !== false, innerHTML: '', scrollTop: 0,
    setAttribute: function(k, v){ attrs[k] = String(v); },
    getAttribute: function(k){ return Object.prototype.hasOwnProperty.call(attrs, k) ? attrs[k] : null; },
    getBoundingClientRect: function(){ return o.rect || {width: 800, height: 600}; },
    querySelector: function(){ return null; }, _attrs: attrs };
}
"""


def _beat(ov_js):
    """the beat's dossier field with document.getElementById answering `ov_js` (a JS expression)"""
    script = (_FAKE_OV + "var OV = " + ov_js + ";\n"
              "var document = { getElementById: function(id){ if (id !== 'th-dossier-ov') return null;"
              " if (OV === 'THROW') throw new Error('boom'); return OV; } };\n"
              "var st = {" + _beat_field() + "};\n"
              "console.log(JSON.stringify(st.dossier === undefined ? 'MISSING' : st.dossier));\n")
    return _node(script)


@unittest.skipIf(NODE is None, "no node on this PC - the page half is UNMEASURED here, not passing")
class TheBeatReadsTheOverlay(unittest.TestCase):

    def test_a_shown_dossier_says_its_number(self):
        self.assertEqual(_beat("(function(){ var o = makeOv({hidden: false}); o.setAttribute('data-n', 87); return o; })()"), 87)

    def test_a_hidden_dossier_is_none_shown(self):
        self.assertIsNone(_beat("(function(){ var o = makeOv({hidden: true}); o.setAttribute('data-n', 87); return o; })()"))

    def test_a_dossier_with_no_size_is_none_shown(self):
        """un-hidden inside a closed parent: display:none upstream gives a 0x0 box - not on screen"""
        self.assertIsNone(_beat("(function(){ var o = makeOv({hidden: false, rect: {width: 0, height: 0}});"
                                " o.setAttribute('data-n', 87); return o; })()"))

    def test_no_overlay_is_none_shown(self):
        self.assertIsNone(_beat("null"))

    def test_a_shown_overlay_with_no_number_is_unknown(self):
        self.assertEqual(_beat("makeOv({hidden: false})"), "UNKNOWN")

    def test_a_read_that_throws_is_unknown_and_never_silences_the_beat(self):
        self.assertEqual(_beat("'THROW'"), "UNKNOWN")


@unittest.skipIf(NODE is None, "no node on this PC - the page half is UNMEASURED here, not passing")
class OpeningByNumberIsWhatTheBeatReports(unittest.TestCase):

    def _run(self, calls):
        script = (_FAKE_OV + "var OV = makeOv({hidden: true});\n"
                  "var document = { getElementById: function(id){ return id === 'th-dossier-ov' ? OV : null; } };\n"
                  "var TH = { sessions: [{n: 28, sessionId: 's28'}, {n: 87, sessionId: 's87'}] };\n"
                  "var DOSSIER = {}; function _dossierHtml(sm){ return '<div>Session ' + sm.n + '</div>'; }\n"
                  "function _animCounts(){}\n"
                  + _open_fn() + "\n" + calls + "\n"
                  "var st = {" + _beat_field() + "};\n"
                  "console.log(JSON.stringify({beat: st.dossier, n: OV.getAttribute('data-n'), hidden: OV.hidden}));\n")
        return _node(script)

    def test_opening_87_puts_87_on_the_beat(self):
        got = self._run("_sessionDossier(87);")
        self.assertEqual(got["n"], "87", "the dossier opened without saying which session it is")
        self.assertFalse(got["hidden"])
        self.assertEqual(got["beat"], 87, "the beat does not report the dossier that was just opened: %r" % got)

    def test_rotating_to_another_session_moves_the_beat(self):
        self.assertEqual(self._run("_sessionDossier(28); _sessionDossier(87);")["beat"], 87)
        self.assertEqual(self._run("_sessionDossier(87); _sessionDossier(28);")["beat"], 28)

    def test_a_session_not_on_the_shelf_opens_nothing(self):
        got = self._run("_sessionDossier(5);")
        self.assertTrue(got["hidden"])
        self.assertIsNone(got["beat"])


class TheStatusPublishesIt(unittest.TestCase):

    def setUp(self):
        import tempfile
        from unittest import mock
        import control_app as ca
        self.ca = ca
        self._beat = dict(ca._UI_BEAT)
        self.addCleanup(lambda: (ca._UI_BEAT.clear(), ca._UI_BEAT.update(self._beat)))
        # status_payload() mints an install identity when the tree has none (a fresh CI checkout does not): it
        # goes to a temp path, never into the tree this law grades - a state move there is a verdict
        d = tempfile.mkdtemp(prefix="dossier_id_")
        self.addCleanup(shutil.rmtree, d, True)
        p = mock.patch.object(ca, "IDENTITY_PATH", os.path.join(d, ".tvd_identity.json"))
        p.start()
        self.addCleanup(p.stop)

    def _published(self, state):
        self.ca.ui_beat_record(state)
        return self.ca.status_payload()["uiBeat"]["dossier"]

    def test_a_number_is_published_as_the_number(self):
        self.assertEqual(self._published({"hidden": False, "dossier": 87}), 87)

    def test_none_shown_is_published_as_none(self):
        self.assertIsNone(self._published({"hidden": False, "dossier": None}))

    def test_a_page_that_did_not_say_is_unknown_never_none_shown(self):
        self.assertEqual(self._published({"hidden": False}), "UNKNOWN")

    def test_a_malformed_value_is_unknown(self):
        for bad in ("87", True, 0, -3, 1.5, {"n": 87}):
            self.assertEqual(self._published({"hidden": False, "dossier": bad}), "UNKNOWN", "%r was published" % (bad,))


RED_PROOF = [
    {"why": "v3538 - the dossier opens without stamping its number: the beat can only say UNKNOWN",
     "file": "control_ui.html",
     "find": "    ov.setAttribute('data-n', String(n));   // v3538",
     "replace": "    void 0;   // v3538", "matches": 1},
    {"why": "v3538 - a HIDDEN dossier is reported as on screen (the shelf-tile false positive, one layer down)",
     "file": "control_ui.html",
     "find": "                if (!o || o.hidden) return null;\n",
     "replace": "                if (!o) return null;\n", "matches": 1},
    {"why": "v3538 - a dossier with no size (inside a closed parent) is reported as on screen",
     "file": "control_ui.html",
     "find": "                if (!(r && r.width > 0 && r.height > 0)) return null;\n",
     "replace": "", "matches": 1},
    {"why": "v3538 - a page that never sent the key reads as 'none shown' instead of UNKNOWN",
     "file": "control_app.py",
     "find": "        else:\n            _UI_BEAT[\"dossier\"] = \"UNKNOWN\"\n",
     "replace": "        else:\n            _UI_BEAT[\"dossier\"] = None\n", "matches": 1},
    {"why": "v3538 - the status never publishes it: the visual pass still has nothing to verify against",
     "file": "control_app.py",
     "find": "                   \"dossier\": _UI_BEAT.get(\"dossier\", \"UNKNOWN\"),\n",
     "replace": "", "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
