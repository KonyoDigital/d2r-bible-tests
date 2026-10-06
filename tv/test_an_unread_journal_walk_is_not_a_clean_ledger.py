# -*- coding: utf-8 -*-
"""REG-1810 — AN UNREAD JOURNAL WALK IS NOT A CLEAN LEDGER.

The ledger organ treats a measured size and no watchdog breach as
"journal clean", and the pulse stays ok. An unread journal walk is
that same size: the file stat succeeded, and the poll already says
verdict unknown.

A measured empty night is idle, and that one stays clean. A real size
is still that size. A miss is still a gap. A partial night still says
clean. A breach is still that breach. An unread size still says the
size was not read. An unread walk says the journal was not read, and
the pulse does not stay ok.

Nothing here reads his journal. RED_PROOF below. [[unknown-stays-unknown]]
"""
import json
import os
import subprocess
import unittest


HERE = os.path.dirname(os.path.abspath(__file__))
import sys as _sys  # noqa: E402
if HERE not in _sys.path:
    _sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402  - REG-1834: these print non-ASCII
_console_safe_enable()

_NOT_READ = "the journal was not read"
_CLEAN = "journal clean"
_SIZE = "the journal size was not read"
_GAP = "last session had gaps"


def _slice():
    with open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
        ui = fh.read()
    start = ui.find("var _EH_STATE = { ok: 'HEALTHY'")
    end = ui.find("function _ehOrganHtml", start)
    if start < 0 or end < 0:
        raise AssertionError("the ledger organ is not in control_ui.html")
    fn = ui[start:end]
    if "\x00" in fn:
        raise AssertionError("the organ slice crossed the null byte")
    if fn.count("key: 'ledger'") != 1:
        raise AssertionError("the organ slice does not hold the one ledger")
    return fn


def _ledger(journal_mb, verdict="omit", violations=0, journal=None):
    lit = "null" if journal_mb is None else json.dumps(journal_mb)
    health = "{}" if verdict == "omit" else json.dumps({"verdict": verdict})
    if journal is not None:
        health += ",journal:" + json.dumps(journal)
    js = (
        "function esc(s){return String(s==null?'':s);}\n"
        + _slice()
        + "var o=_engineOrganData({journalMB:" + lit
        + ",watchdog:{violations:" + str(int(violations))
        + "},sessionHealth:" + health
        + ",driver:{},eyes:{}});\n"
        + "var led=o.filter(function(x){return x.key==='ledger';})[0];\n"
        + "process.stdout.write(JSON.stringify({pulse:led.pulse,stat:led.stat,"
        + "sub:led.sub,state:led.state,why:led.why||null}));\n"
    )
    got = subprocess.run(
        ["node", "-"], input=js.encode("utf-8"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    if got.returncode != 0:
        raise AssertionError(got.stderr.decode("utf-8", "replace")[:600])
    return json.loads(got.stdout.decode("utf-8"))


class AnUnreadJournalWalkIsNotACleanLedger(unittest.TestCase):

    def test_a_measured_empty_night_still_reads_clean(self):
        led = _ledger(0.0, verdict="idle")
        self.assertEqual(led["pulse"], "ok")
        self.assertEqual(led["state"], "HEALTHY")
        self.assertEqual(led["sub"], _CLEAN)
        self.assertEqual(led["stat"], "0 MB")
        self.assertNotIn(_NOT_READ, led["sub"])

    def test_a_missing_session_health_is_still_clean(self):
        led = _ledger(0.0)
        self.assertEqual(led["pulse"], "ok")
        self.assertEqual(led["sub"], _CLEAN)
        self.assertNotIn(_NOT_READ, led["sub"])

    def test_a_real_size_is_still_that_size(self):
        led = _ledger(1.5, verdict="ok")
        self.assertEqual(led["pulse"], "ok")
        self.assertEqual(led["state"], "HEALTHY")
        self.assertEqual(led["sub"], _CLEAN)
        self.assertEqual(led["stat"], "1.5 MB")
        self.assertNotIn(_NOT_READ, led["sub"])

    def test_a_miss_is_still_a_gap(self):
        led = _ledger(1.5, verdict="miss")
        self.assertEqual(led["pulse"], "ok")
        self.assertIn(_GAP, led["sub"])
        self.assertNotIn(_NOT_READ, led["sub"])
        self.assertNotIn(_CLEAN, led["sub"])
        self.assertIn("1.5 MB", led["stat"])

    def test_a_partial_night_still_says_clean(self):
        led = _ledger(1.5, verdict="partial")
        self.assertEqual(led["pulse"], "ok")
        self.assertEqual(led["sub"], _CLEAN)
        self.assertNotIn(_NOT_READ, led["sub"])

    def test_an_unread_walk_is_not_a_clean_ledger(self):
        led = _ledger(1.5, verdict="unknown")
        self.assertEqual(led["pulse"], "unknown")  # REG-1824: not read is UNKNOWN, not strained
        self.assertEqual(led["state"], "UNKNOWN")
        self.assertEqual(led["sub"], _NOT_READ)
        self.assertNotIn(_CLEAN, led["sub"])
        self.assertIn("1.5 MB", led["stat"])
        self.assertNotIn(_SIZE, led["sub"])

    def test_a_measured_zero_with_an_unread_walk_is_not_clean(self):
        led = _ledger(0.0, verdict="unknown")
        self.assertEqual(led["pulse"], "unknown")  # REG-1824: not read is UNKNOWN, not strained
        self.assertEqual(led["sub"], _NOT_READ)
        self.assertEqual(led["stat"], "0 MB")
        self.assertNotIn(_CLEAN, led["sub"])

    def test_an_unread_size_still_says_the_size_was_not_read(self):
        led = _ledger(None, verdict="unknown")
        self.assertEqual(led["pulse"], "unknown")  # REG-1824: not read is UNKNOWN, not strained
        self.assertEqual(led["sub"], _SIZE)
        self.assertNotIn(_CLEAN, led["sub"])
        self.assertNotIn("MB", led["stat"])

    def test_a_measured_breach_is_still_a_breach(self):
        led = _ledger(1.5, verdict="unknown", violations=2)
        self.assertEqual(led["pulse"], "warn")
        self.assertEqual(led["sub"], "2 watchdog breach")
        self.assertIn("1.5 MB", led["stat"])
        self.assertNotIn(_NOT_READ, led["sub"])
        self.assertNotIn(_CLEAN, led["sub"])

    def test_the_ledger_organ_follows_the_polls_one_journal_key(self):
        """REG-1824 — this pinned the organ's own copy of the check. The one key decides now, and
        the reason the poll gave rides on the organ for its hover."""
        led = _ledger(1.5, verdict="idle", journal={"read": False, "why": "PermissionError: denied"})
        self.assertEqual(led["pulse"], "unknown")
        self.assertEqual(led["state"], "UNKNOWN")
        self.assertEqual(led["sub"], _NOT_READ)
        self.assertIn("PermissionError", led["why"] or "")
        led = _ledger(1.5, verdict="idle", journal={"read": True, "why": None})
        self.assertEqual(led["pulse"], "ok")
        self.assertEqual(led["sub"], _CLEAN)
        led = _ledger(None, verdict="idle", journal={"read": True, "why": None})
        self.assertEqual(led["pulse"], "unknown")
        self.assertEqual(led["sub"], _SIZE)
        self.assertIsNone(led["why"], "the size was not read; the walk was, so no walk reason")


RED_PROOF = [
    {
        "why": "REG-1824 - the one predicate forgets the marks an older poll left, and an unread walk paints as read",
        "file": "control_ui.html",
        "find": "    return sh.verdict === 'unknown' || dr.seen === null || dr.queued === null;\n",
        "replace": "    return false;\n",
        "matches": 1,
    },
    {
        "why": "REG-1824 - the organ drops the poll's reason, so its hover can never say why",
        "file": "control_ui.html",
        "find": "if (o.pulse === 'unknown' && _journalUnread(st)) o.why = _journalUnreadWhy(st);",
        "replace": "if (false) o.why = _journalUnreadWhy(st);",
        "matches": 1,
    },
    {
        "why": "REG-1810 - an unread walk is painted as a clean ledger",
        "file": "control_ui.html",
        "find": "    var walkUnread = _journalUnread(st);\n",
        "replace": "    var walkUnread = false;\n",
        "matches": 1,
    },
    {
        "why": "REG-1810 - a measured night is painted as a journal that was not read",
        "file": "control_ui.html",
        "find": "    var walkUnread = _journalUnread(st);\n",
        "replace": "    var walkUnread = true;\n",
        "matches": 1,
    },
    {
        "why": "REG-1810 - an unread walk stays ok",
        "file": "control_ui.html",
        "find": "    var ldPulse = viol > 0 ? 'warn' : ((journalUnread || walkUnread) ? 'unknown' : 'ok');\n",
        "replace": "    var ldPulse = viol > 0 ? 'warn' : (journalUnread ? 'unknown' : 'ok');\n",
        "matches": 1,
    },
    {
        "why": "REG-1810 - the screen calls an unread walk a clean journal",
        "file": "control_ui.html",
        "find": "viol ? viol + ' watchdog breach' : (walkUnread ? 'the journal was not read' : 'journal clean')",
        "replace": "viol ? viol + ' watchdog breach' : 'journal clean'",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
