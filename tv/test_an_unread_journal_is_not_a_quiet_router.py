# -*- coding: utf-8 -*-
"""REG-1806 — AN UNREAD JOURNAL IS NOT A QUIET ROUTER.

The router organ treats a missing seen count as zero seen and zero routed.
While live, that pulse stays ok and the subtitle says quorum gate. The
dispatch strip under the spine paints the same zero. An unread journal
walk is that same missing count: the poll already publishes null, because
the walk did not copy the counters.

A measured zero still says 0 seen and 0 routed, and the strip still says 0.
A routed count is still that count. A re-fire is still a re-fire. A driver
error is still that error. A deep queue still warns. An unread walk says
the journal was not read, on the organ and on the strip, and the pulse is
not ok. A judge count is not added onto a zero that was not measured.

Nothing here reads his journal. RED_PROOF below. [[unknown-stays-unknown]]
"""
import json
import os
import subprocess
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

os.environ.setdefault("TV_STUB", "1")
import control_app as ca  # noqa: E402


_NOT_READ = "the journal was not read"


def _paint(mode="off", driver=None, judge_q=0, judge_fire=0, err=None):
    with open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
        ui = fh.read()
    start = ui.find("var _EH_STATE = { ok: 'HEALTHY'")
    end = ui.find("function _rnFeedRow", start)
    if start < 0 or end < 0:
        raise AssertionError("the router organ is not in control_ui.html")
    fn = ui[start:end]
    if "\x00" in fn:
        raise AssertionError("the organ slice crossed the null byte")
    dr = {} if driver is None else dict(driver)
    dr.setdefault("judgeQ", judge_q)
    dr.setdefault("judgeFire", judge_fire)
    if err is not None:
        dr["err"] = err
    st = {
        "mode": mode,
        "sessionHealth": {"verdict": "idle", "tabs": {}},
        "driver": dr,
        "eyes": {},
        "watchdog": {},
        "journalMB": 0,
    }
    js = (
        "function esc(s){return String(s==null?'':s);}\n"
        "function makeStep(){\n"
        "  var classes = {};\n"
        "  return {textContent:'', classList:{\n"
        "    remove:function(){for (var i=0;i<arguments.length;i++) delete classes[arguments[i]];},\n"
        "    add:function(c){classes[c]=true;}\n"
        "  }, classes:classes};\n"
        "}\n"
        "var steps = {seen:makeStep(), queued:makeStep(), fired:makeStep()};\n"
        "var meta = {textContent:''};\n"
        "var spine = {innerHTML:''};\n"
        "var box = {hidden:false,\n"
        "  querySelector:function(sel){\n"
        "    if (sel.indexOf('queued') >= 0) return steps.queued;\n"
        "    if (sel.indexOf('fired') >= 0) return steps.fired;\n"
        "    if (sel.indexOf('seen') >= 0) return steps.seen;\n"
        "    return null;\n"
        "  },\n"
        "  querySelectorAll:function(){return [steps.seen, steps.queued, steps.fired];}\n"
        "};\n"
        "var els = {'hd-spine':spine, 'eh-dispatch':box,\n"
        "  'eh-d-seen':steps.seen, 'eh-d-queued':steps.queued,\n"
        "  'eh-d-fired':steps.fired, 'eh-d-meta':meta};\n"
        "function $(id){return els[id] || null;}\n"
        "var document = {getElementById:function(id){return els[id] || null;}};\n"
        + fn
        + "var o=_engineOrganData(" + json.dumps(st) + ");\n"
        + "hdEngineHealth(" + json.dumps(st) + ");\n"
        + "var rt=o.filter(function(x){return x.key==='router';})[0];\n"
        + "process.stdout.write(JSON.stringify({pulse:rt.pulse,stat:rt.stat,"
        + "sub:rt.sub,state:rt.state,hidden:box.hidden,"
        + "seen:steps.seen.textContent,queued:steps.queued.textContent,"
        + "fired:steps.fired.textContent,meta:meta.textContent,"
        + "seenHot:!!steps.seen.classes.hot,queuedHot:!!steps.queued.classes.hot,"
        + "queuedWarn:!!steps.queued.classes.warn,firedHot:!!steps.fired.classes.hot}));\n"
    )
    got = subprocess.run(
        ["node", "-"], input=js.encode("utf-8"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    if got.returncode != 0:
        raise AssertionError(got.stderr.decode("utf-8", "replace")[:800])
    return json.loads(got.stdout.decode("utf-8"))


class AnUnreadJournalIsNotAQuietRouter(unittest.TestCase):

    def test_a_measured_zero_off_air_is_still_a_quiet_router(self):
        row = _paint(mode="off", driver={"seen": 0, "queued": 0, "fired": 0, "refire": 0})
        self.assertEqual(row["pulse"], "idle")
        self.assertEqual(row["state"], "IDLE")
        self.assertIn("0 seen", row["stat"])
        self.assertIn("0 routed", row["stat"])
        self.assertEqual(row["sub"], "quorum gate")
        self.assertNotIn("was not read", row["stat"])
        self.assertNotIn("was not read", row["sub"])
        self.assertTrue(row["hidden"])

    def test_a_live_measured_zero_is_still_that_zero(self):
        row = _paint(mode="live", driver={"seen": 0, "queued": 0, "fired": 0, "refire": 0})
        self.assertEqual(row["pulse"], "ok")
        self.assertEqual(row["state"], "HEALTHY")
        self.assertIn("0 seen", row["stat"])
        self.assertIn("0 routed", row["stat"])
        self.assertEqual(row["sub"], "quorum gate")
        self.assertEqual(row["seen"], "0")
        self.assertEqual(row["queued"], "0")
        self.assertEqual(row["fired"], "0")
        self.assertNotIn("was not read", row["seen"])
        self.assertTrue(row["seenHot"])
        self.assertFalse(row["hidden"])

    def test_an_unread_journal_is_not_a_quiet_router(self):
        row = _paint(mode="live", driver={
            "seen": None, "queued": None, "fired": None, "refire": None})
        self.assertEqual(row["pulse"], "warn")
        self.assertEqual(row["state"], "STRAINED")
        self.assertEqual(row["stat"], _NOT_READ)
        self.assertEqual(row["sub"], _NOT_READ)
        self.assertNotIn("0 seen", row["stat"])
        self.assertNotIn("0 routed", row["stat"])
        self.assertNotIn("quorum gate", row["sub"])
        self.assertNotEqual(row["pulse"], "ok")
        self.assertEqual(row["seen"], _NOT_READ)
        self.assertEqual(row["queued"], _NOT_READ)
        self.assertEqual(row["fired"], _NOT_READ)
        self.assertEqual(row["meta"], _NOT_READ)
        self.assertNotEqual(row["seen"], "0")
        self.assertFalse(row["seenHot"])
        self.assertFalse(row["queuedHot"])
        self.assertFalse(row["firedHot"])

    def test_an_off_air_unread_journal_is_not_a_hidden_zero(self):
        row = _paint(mode="off", driver={
            "seen": None, "queued": None, "fired": None, "refire": None})
        self.assertEqual(row["pulse"], "warn")
        self.assertNotEqual(row["pulse"], "idle")
        self.assertEqual(row["stat"], _NOT_READ)
        self.assertEqual(row["sub"], _NOT_READ)
        self.assertFalse(row["hidden"])
        self.assertEqual(row["seen"], _NOT_READ)
        self.assertNotEqual(row["seen"], "0")
        self.assertEqual(row["meta"], _NOT_READ)
        self.assertFalse(row["seenHot"])

    def test_a_routed_count_is_still_that_count(self):
        row = _paint(mode="live", driver={"seen": 4, "queued": 1, "fired": 3, "refire": 2})
        self.assertEqual(row["pulse"], "ok")
        self.assertIn("4 seen", row["stat"])
        self.assertIn("3 routed", row["stat"])
        self.assertEqual(row["sub"], "2 re-fired")
        self.assertNotIn("was not read", row["stat"])
        self.assertNotIn("was not read", row["sub"])
        self.assertEqual(row["seen"], "4")
        self.assertEqual(row["queued"], "1")
        self.assertEqual(row["fired"], "3")
        self.assertIn("2 re-fire", row["meta"])
        self.assertTrue(row["firedHot"])
        self.assertNotIn("was not read", row["seen"])

    def test_a_driver_error_is_still_that_error(self):
        row = _paint(
            mode="live",
            driver={"seen": 4, "queued": 0, "fired": 1, "refire": 0},
            err="no route")
        self.assertEqual(row["pulse"], "bad")
        self.assertEqual(row["state"], "DOWN")
        self.assertIn("4 seen", row["stat"])
        self.assertIn("no route", row["sub"])
        self.assertNotEqual(row["sub"], "quorum gate")
        self.assertNotIn("was not read", row["stat"])
        self.assertNotIn("was not read", row["sub"])
        self.assertIn("no route", row["meta"])

    def test_a_deep_queue_still_warns(self):
        row = _paint(mode="live", driver={"seen": 9, "queued": 12, "fired": 1, "refire": 0})
        self.assertEqual(row["pulse"], "warn")
        self.assertIn("9 seen", row["stat"])
        self.assertIn("1 routed", row["stat"])
        self.assertEqual(row["sub"], "quorum gate")
        self.assertNotIn("was not read", row["stat"])
        self.assertEqual(row["queued"], "12")
        self.assertTrue(row["queuedWarn"])

    def test_a_judge_count_is_still_added_when_the_router_was_read(self):
        row = _paint(
            mode="live",
            driver={"seen": 0, "queued": 0, "fired": 0, "refire": 0},
            judge_q=2, judge_fire=1)
        self.assertEqual(row["pulse"], "ok")
        self.assertIn("0 seen", row["stat"])
        self.assertEqual(row["seen"], "0")
        self.assertEqual(row["queued"], "2")
        self.assertEqual(row["fired"], "1")
        self.assertIn("judge", row["meta"])
        self.assertNotIn("was not read", row["seen"])

    def test_an_unread_walk_does_not_add_the_judge_onto_a_zero(self):
        row = _paint(
            mode="live",
            driver={"seen": None, "queued": None, "fired": None, "refire": None},
            judge_q=2, judge_fire=1)
        self.assertEqual(row["pulse"], "warn")
        self.assertEqual(row["stat"], _NOT_READ)
        self.assertEqual(row["seen"], _NOT_READ)
        self.assertEqual(row["queued"], _NOT_READ)
        self.assertEqual(row["fired"], _NOT_READ)
        self.assertNotEqual(row["queued"], "2")
        self.assertNotEqual(row["fired"], "1")
        self.assertNotEqual(row["seen"], "0")
        self.assertNotIn("judge", row["meta"])
        self.assertEqual(row["meta"], _NOT_READ)

    def test_a_missing_count_is_still_a_measured_zero(self):
        """A driver block that never sent the key is not the null the walk publishes."""
        row = _paint(mode="live", driver={})
        self.assertEqual(row["pulse"], "ok")
        self.assertIn("0 seen", row["stat"])
        self.assertEqual(row["sub"], "quorum gate")
        self.assertNotIn("was not read", row["stat"])
        self.assertEqual(row["seen"], "0")

    def test_the_poll_publishes_null_when_the_journal_was_not_read(self):
        saved = ca.__dict__.get("_STATUS_JOURNAL_CACHE")
        try:
            ca._STATUS_JOURNAL_CACHE = None
            with mock.patch.object(
                    ca, "_kai_journal_rows",
                    side_effect=lambda want_why=False:
                    ([], "PermissionError: denied") if want_why else []):
                st = ca.status_payload()
            dr = st.get("driver") or {}
            self.assertIsNone(dr.get("seen"))
            self.assertIsNone(dr.get("queued"))
            self.assertIsNone(dr.get("fired"))
            self.assertIsNone(dr.get("refire"))
            sh = st.get("sessionHealth") or {}
            self.assertEqual(sh.get("verdict"), "unknown")
        finally:
            ca._STATUS_JOURNAL_CACHE = saved

    def test_a_quiet_night_still_publishes_a_number(self):
        saved = ca.__dict__.get("_STATUS_JOURNAL_CACHE")
        try:
            ca._STATUS_JOURNAL_CACHE = None
            with mock.patch.object(
                    ca, "_kai_journal_rows",
                    side_effect=lambda want_why=False: ([], None) if want_why else []):
                st = ca.status_payload()
            dr = st.get("driver") or {}
            self.assertIsInstance(dr.get("seen"), int)
            self.assertIsNotNone(dr.get("seen"))
            self.assertIsInstance(dr.get("fired"), int)
            sh = st.get("sessionHealth") or {}
            self.assertNotEqual(sh.get("verdict"), "unknown")
        finally:
            ca._STATUS_JOURNAL_CACHE = saved

    def test_the_organ_asks_this_look(self):
        with open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
            ui = fh.read()
        self.assertEqual(ui.count("\x00"), 1)
        self.assertIn("    var routeUnread = (dr.seen === null);\n", ui)
        self.assertIn("        var routeUnread = (dr.seen === null);\n", ui)
        self.assertIn("var rtPulse = routeUnread ? 'warn'\n", ui)
        self.assertIn("? 'the journal was not read'\n", ui)
        self.assertIn("var has = routeUnread || on || seen || queued || fired || jq || jf;\n", ui)
        self.assertNotIn(
            "var rtPulse = dead || err ? 'bad' : (!on ? 'idle' : (qDepth > 8 ? 'warn' : 'ok'));",
            ui)
        with open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn(
            '{"seen": None, "queued": None, "fired": None, "refire": None,',
            src)
        self.assertIn('"seen": _drv.get("seen", 0)', src)


RED_PROOF = [
    {
        "why": "REG-1806 - an unread journal is painted as a quiet router",
        "file": "control_ui.html",
        "find": "    var routeUnread = (dr.seen === null);\n"
                "    var seen = dr.seen || 0, fired = dr.fired || 0, refire = dr.refire || 0, err = dr.err;\n",
        "replace": "    var routeUnread = false;\n"
                   "    var seen = dr.seen || 0, fired = dr.fired || 0, refire = dr.refire || 0, err = dr.err;\n",
        "matches": 1,
    },
    {
        "why": "REG-1806 - a measured zero is painted as a journal that was not read",
        "file": "control_ui.html",
        "find": "    var routeUnread = (dr.seen === null);\n"
                "    var seen = dr.seen || 0, fired = dr.fired || 0, refire = dr.refire || 0, err = dr.err;\n",
        "replace": "    var routeUnread = (dr.seen === 0);\n"
                   "    var seen = dr.seen || 0, fired = dr.fired || 0, refire = dr.refire || 0, err = dr.err;\n",
        "matches": 1,
    },
    {
        "why": "REG-1806 - the screen calls an unread journal zero seen",
        "file": "control_ui.html",
        "find": "    var rtStat = routeUnread\n"
                "      ? 'the journal was not read'\n"
                "      : (seen + ' seen <span class=\"eh-arrow\">→</span> ' + fired + ' routed');\n",
        "replace": "    var rtStat = seen + ' seen <span class=\"eh-arrow\">→</span> ' + fired + ' routed';\n",
        "matches": 1,
    },
    {
        "why": "REG-1806 - an unread journal stays an ok router",
        "file": "control_ui.html",
        "find": "    var rtPulse = routeUnread ? 'warn'\n"
                "      : (dead || err ? 'bad' : (!on ? 'idle' : (qDepth > 8 ? 'warn' : 'ok')));\n",
        "replace": "    var rtPulse = dead || err ? 'bad' : (!on ? 'idle' : (qDepth > 8 ? 'warn' : 'ok'));\n",
        "matches": 1,
    },
    {
        "why": "REG-1806 - the dispatch strip paints an unread journal as zero",
        "file": "control_ui.html",
        "find": "        var routeUnread = (dr.seen === null);\n",
        "replace": "        var routeUnread = false;\n",
        "matches": 1,
    },
    {
        "why": "REG-1806 - an off-air unread journal hides as no dispatch",
        "file": "control_ui.html",
        "find": "        var has = routeUnread || on || seen || queued || fired || jq || jf;\n",
        "replace": "        var has = on || seen || queued || fired || jq || jf;\n",
        "matches": 1,
    },
    {
        "why": "REG-1806 - the poll publishes a zero for a count it did not copy",
        "file": "control_app.py",
        "find": '        _drv = {"seen": None, "queued": None, "fired": None, "refire": None,\n',
        "replace": '        _drv = {"seen": 0, "queued": None, "fired": None, "refire": None,\n',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
