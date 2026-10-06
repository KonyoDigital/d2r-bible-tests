# -*- coding: utf-8 -*-
"""REG-1804 — AN UNREAD JOURNAL IS NOT A NIGHT WITH NO STASH TABS.

The funnels organ treats an empty tab list as a night that has not visited a
stash. While live, that pulse stays ok. An unread journal walk is that same
empty list: the poll already says verdict unknown. The organ said "no stash
tabs yet".

A measured empty night still says that. A landed tab is still landed. A miss
is still a gap. A gate that holds more than it proves still warns. An unread
walk says the journal was not read, and the pulse is not ok.

Nothing here reads his journal. RED_PROOF below. [[unknown-stays-unknown]]
"""
import inspect
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

import control_app as ca  # noqa: E402


def _funnels(mode="off", verdict="idle", tabs=None, gate=None, journal=None):
    with open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
        ui = fh.read()
    start = ui.find("var _EH_STATE = { ok: 'HEALTHY'")
    end = ui.find("function _ehOrganHtml", start)
    if start < 0 or end < 0:
        raise AssertionError("the funnels organ is not in control_ui.html")
    fn = ui[start:end]
    if "\x00" in fn:
        raise AssertionError("the organ slice crossed the null byte")
    sh = {"verdict": verdict, "tabs": {} if tabs is None else tabs}
    if gate is not None:
        sh["gate"] = gate
    st = {"mode": mode, "sessionHealth": sh, "driver": {}, "eyes": {}, "watchdog": {}}
    if journal is not None:
        st["journal"] = journal
    js = (
        "function esc(s){return String(s==null?'':s);}\n"
        + fn
        + "var o=_engineOrganData(" + json.dumps(st) + ");\n"
        + "var fun=o.filter(function(x){return x.key==='funnels';})[0];\n"
        + "process.stdout.write(JSON.stringify({pulse:fun.pulse,stat:fun.stat,"
        + "sub:fun.sub,state:fun.state,why:fun.why||null}));\n"
    )
    got = subprocess.run(
        ["node", "-"], input=js.encode("utf-8"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    if got.returncode != 0:
        raise AssertionError(got.stderr.decode("utf-8", "replace")[:600])
    return json.loads(got.stdout.decode("utf-8"))


class AnUnreadJournalIsNotANightWithNoStashTabs(unittest.TestCase):

    def test_a_measured_empty_night_still_says_no_stash_tabs(self):
        fun = _funnels(mode="off", verdict="idle")
        self.assertEqual(fun["pulse"], "idle")
        self.assertEqual(fun["state"], "IDLE")
        self.assertEqual(fun["sub"], "no stash tabs yet")
        self.assertNotIn("was not read", fun["sub"])

    def test_a_live_empty_night_is_still_that_empty(self):
        fun = _funnels(mode="live", verdict="idle")
        self.assertEqual(fun["pulse"], "ok")
        self.assertEqual(fun["state"], "HEALTHY")
        self.assertEqual(fun["sub"], "no stash tabs yet")
        self.assertNotIn("was not read", fun["sub"])

    def test_an_unread_journal_is_not_a_night_with_no_stash_tabs(self):
        fun = _funnels(mode="live", verdict="unknown")
        self.assertEqual(fun["pulse"], "unknown")  # REG-1824: not read is UNKNOWN, not strained
        self.assertEqual(fun["state"], "UNKNOWN")
        self.assertEqual(fun["sub"], "the journal was not read")
        self.assertNotIn("no stash tabs", fun["sub"])
        self.assertNotEqual(fun["pulse"], "ok")

    def test_an_off_air_unread_journal_is_not_an_idle_funnel(self):
        fun = _funnels(mode="off", verdict="unknown")
        self.assertEqual(fun["pulse"], "unknown")  # REG-1824: not read is UNKNOWN, not strained
        self.assertNotEqual(fun["pulse"], "idle")
        self.assertEqual(fun["sub"], "the journal was not read")
        self.assertNotIn("no stash tabs", fun["sub"])

    def test_a_landed_tab_is_still_landed(self):
        fun = _funnels(
            mode="live", verdict="ok",
            tabs={"gems": {"ok": True, "status": "ok", "total": 3}})
        self.assertEqual(fun["pulse"], "ok")
        self.assertIn("1 landed", fun["sub"])
        self.assertNotIn("was not read", fun["sub"])
        self.assertIn("1/1", fun["stat"])

    def test_a_miss_is_still_a_gap(self):
        fun = _funnels(
            mode="live", verdict="miss",
            tabs={"gems": {"ok": False, "status": "miss", "total": 0}})
        self.assertEqual(fun["pulse"], "warn")
        self.assertIn("gap", fun["sub"])
        self.assertNotIn("was not read", fun["sub"])
        self.assertNotIn("no stash tabs", fun["sub"])

    def test_a_gate_that_holds_more_than_it_proves_still_warns(self):
        fun = _funnels(
            mode="live", verdict="ok",
            gate={"proven": 1, "held": 4})
        self.assertEqual(fun["pulse"], "warn")
        self.assertIn("held", fun["sub"])
        self.assertIn("proven", fun["sub"])
        self.assertNotIn("no stash tabs", fun["sub"])
        self.assertNotIn("was not read", fun["sub"])

    def test_a_clean_gate_is_still_the_shield(self):
        fun = _funnels(
            mode="live", verdict="ok",
            tabs={"gems": {"ok": True, "status": "ok"}},
            gate={"proven": 4, "held": 1})
        self.assertEqual(fun["pulse"], "ok")
        self.assertIn("proven", fun["sub"])
        self.assertIn("held", fun["sub"])
        self.assertNotIn("was not read", fun["sub"])

    def test_an_unread_walk_wins_over_a_gate(self):
        fun = _funnels(
            mode="live", verdict="unknown",
            gate={"proven": 4, "held": 0})
        self.assertEqual(fun["pulse"], "unknown")  # REG-1824: not read is UNKNOWN, not strained
        self.assertEqual(fun["sub"], "the journal was not read")
        self.assertNotIn("proven", fun["sub"])

    def test_the_organ_follows_the_polls_one_journal_key(self):
        """REG-1824 — this pinned the organ's own copy of the check. The one key decides now."""
        fun = _funnels(mode="live", verdict="idle",
                       journal={"read": False, "why": "PermissionError: denied"})
        self.assertEqual(fun["pulse"], "unknown")
        self.assertEqual(fun["sub"], "the journal was not read")
        self.assertIn("PermissionError", fun["why"] or "")
        fun = _funnels(mode="live", verdict="idle", journal={"read": True, "why": None})
        self.assertEqual(fun["pulse"], "ok")
        self.assertEqual(fun["sub"], "no stash tabs yet")
        self.assertIsNone(fun["why"])
        src = inspect.getsource(ca.status_payload)
        self.assertIn('"verdict": "unknown"', src)
        self.assertIn('"error": "journal unread"', src)
        self.assertNotIn('"verdict": "idle"', src)


RED_PROOF = [
    {
        "why": "REG-1824 - the one predicate ignores the poll's journal key and an unread walk paints as read",
        "file": "control_ui.html",
        "find": "    if (j && typeof j.read === 'boolean') return j.read === false;\n",
        "replace": "    if (j && typeof j.read === 'boolean') return false;\n",
        "matches": 1,
    },
    {
        "why": "REG-1824 - unread maps to STRAINED again: _EH_STATE has no UNKNOWN",
        "file": "control_ui.html",
        "find": "idle: 'IDLE', unknown: 'UNKNOWN' };\n",
        "replace": "idle: 'IDLE' };\n",
        "matches": 1,
    },
    {
        "why": "REG-1804 - an unread journal is painted as a night with no stash tabs",
        "file": "control_ui.html",
        "find": "    var tabsUnread = _journalUnread(st);\n",
        "replace": "    var tabsUnread = false;\n",
        "matches": 1,
    },
    {
        "why": "REG-1804 - a measured empty night is painted as a journal that was not read",
        "file": "control_ui.html",
        "find": "    var tabsUnread = _journalUnread(st);\n",
        "replace": "    var tabsUnread = (tk.length === 0);\n",
        "matches": 1,
    },
    {
        "why": "REG-1804 - the screen calls an unread journal a night with no stash tabs",
        "file": "control_ui.html",
        # the funnel's own fnSub line - four other organs now say the same words (REG-1805..1810)
        "find": "    var fnSub = tabsUnread\n      ? 'the journal was not read'\n",
        "replace": "    var fnSub = tabsUnread\n      ? 'no stash tabs yet'\n",
        "matches": 1,
    },
    {
        "why": "REG-1804 - an unread journal stays an ok funnel",
        "file": "control_ui.html",
        "find": "    var fnPulse = tabsUnread ? 'unknown'\n"
                "      : ((!on && !tk.length && !hasGate) ? 'idle' : ((missTabs > 0 || (hasGate && (held || 0) > (proven || 0))) ? 'warn' : 'ok'));\n",
        "replace": "    var fnPulse = (!on && !tk.length && !hasGate) ? 'idle' : ((missTabs > 0 || (hasGate && (held || 0) > (proven || 0))) ? 'warn' : 'ok');\n",
        "matches": 1,
    },
    {
        "why": "REG-1804 - an unread journal walk is filed as an idle night",
        "file": "control_app.py",
        "find": '        _sess_h = {"tabs": {}, "leases": {}, "verdict": "unknown", "story": [],\n',
        "replace": '        _sess_h = {"tabs": {}, "leases": {}, "verdict": "idle", "story": [],\n',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
