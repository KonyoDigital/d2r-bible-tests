# -*- coding: utf-8 -*-
"""REG-1808 — AN UNREAD JOURNAL IS NOT A QUIET MIND.

The mind lamp treats an empty thought list as a quiet mind. While the
console is on, and while it is off, the line says there are no thoughts
yet. An unread journal is that same empty list: the poll already says
verdict unknown, because the walk did not copy the story.

A measured empty night still says quiet. A thought on air is still a
thought, and two still say thoughts. Off air, a measured night still
says quiet. An unread walk says the journal was not read, and a leftover
thought list does not light the lamp.

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
_QUIET = "quiet \u00b7 no thoughts yet"


def _mind(on=True, verdict="idle", story=None, mind_story=None, omit_health=False,
          omit_mind=True):
    with open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
        ui = fh.read()
    start = ui.find("    // REG-1808 — unknown is a journal that was not read.")
    end = ui.find("    var _ring = st.liveRing", start)
    if start < 0 or end < 0:
        raise AssertionError("the mind lamp is not in control_ui.html")
    fn = ui[start:end]
    if "\x00" in fn:
        raise AssertionError("the mind slice crossed the null byte")
    if fn.count("_engRow('mind'") != 1:
        raise AssertionError("the mind slice does not hold the one mind lamp")
    st = {}
    if not omit_health:
        sh = {}
        if verdict is not None:
            sh["verdict"] = verdict
        if story is not None:
            sh["story"] = story
        st["sessionHealth"] = sh
    if not omit_mind:
        st["mindStory"] = mind_story
    js = (
        "function paintMind(st, on){\n"
        "  var got = null;\n"
        "  function _engRow(id, lit, txt){\n"
        "    if (id === 'mind') got = {lit: !!lit, txt: String(txt)};\n"
        "  }\n"
        + fn
        + "\n  return got;\n"
        "}\n"
        "process.stdout.write(JSON.stringify(paintMind("
        + json.dumps(st) + ", " + ("true" if on else "false") + ")));\n"
    )
    got = subprocess.run(
        ["node", "-"], input=js.encode("utf-8"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    if got.returncode != 0:
        raise AssertionError(got.stderr.decode("utf-8", "replace")[:800])
    return json.loads(got.stdout.decode("utf-8"))


class AnUnreadJournalIsNotAQuietMind(unittest.TestCase):

    def test_a_measured_empty_night_on_air_still_says_quiet(self):
        row = _mind(on=True, verdict="idle", story=[], mind_story=[], omit_mind=False)
        self.assertFalse(row["lit"])
        self.assertEqual(row["txt"], _QUIET)
        self.assertNotIn("was not read", row["txt"])
        self.assertNotIn("thinking", row["txt"])

    def test_a_measured_empty_night_off_air_still_says_quiet(self):
        row = _mind(on=False, verdict="idle", story=[], mind_story=[], omit_mind=False)
        self.assertFalse(row["lit"])
        self.assertEqual(row["txt"], _QUIET)
        self.assertNotIn("was not read", row["txt"])

    def test_one_thought_on_air_is_still_a_thought(self):
        row = _mind(on=True, verdict="ok", mind_story=["visited gems"], omit_mind=False)
        self.assertTrue(row["lit"])
        self.assertEqual(row["txt"], "thinking \u00b7 1 thought")
        self.assertNotIn("was not read", row["txt"])
        self.assertNotEqual(row["txt"], _QUIET)

    def test_two_thoughts_on_air_still_say_thoughts(self):
        row = _mind(
            on=True, verdict="ok",
            mind_story=["visited gems", "named Magefist"], omit_mind=False)
        self.assertTrue(row["lit"])
        self.assertEqual(row["txt"], "thinking \u00b7 2 thoughts")
        self.assertNotIn("was not read", row["txt"])

    def test_a_measured_thought_off_air_stays_quiet(self):
        row = _mind(
            on=False, verdict="ok",
            mind_story=["visited gems", "named Magefist"], omit_mind=False)
        self.assertFalse(row["lit"])
        self.assertEqual(row["txt"], _QUIET)
        self.assertNotIn("thinking", row["txt"])
        self.assertNotIn("was not read", row["txt"])

    def test_a_session_story_is_still_a_thought_when_the_poll_omits_mind_story(self):
        row = _mind(on=True, verdict="ok", story=["visited gems", "judge Stone of Jordan"])
        self.assertTrue(row["lit"])
        self.assertEqual(row["txt"], "thinking \u00b7 2 thoughts")
        self.assertNotIn("was not read", row["txt"])

    def test_an_unread_journal_on_air_is_not_a_quiet_mind(self):
        row = _mind(on=True, verdict="unknown", story=[], mind_story=[], omit_mind=False)
        self.assertFalse(row["lit"])
        self.assertEqual(row["txt"], _NOT_READ)
        self.assertNotEqual(row["txt"], _QUIET)
        self.assertNotIn("thinking", row["txt"])
        self.assertNotIn("thought", row["txt"])

    def test_an_unread_journal_off_air_is_not_a_quiet_mind(self):
        row = _mind(on=False, verdict="unknown", story=[], mind_story=[], omit_mind=False)
        self.assertFalse(row["lit"])
        self.assertEqual(row["txt"], _NOT_READ)
        self.assertNotEqual(row["txt"], _QUIET)

    def test_a_leftover_thought_does_not_light_an_unread_mind(self):
        row = _mind(
            on=True, verdict="unknown",
            mind_story=["visited gems", "named Magefist"], omit_mind=False)
        self.assertFalse(row["lit"])
        self.assertEqual(row["txt"], _NOT_READ)
        self.assertNotIn("thinking", row["txt"])
        self.assertNotIn("2", row["txt"])

    def test_a_missing_session_health_is_still_the_quiet_mind(self):
        row = _mind(on=True, omit_health=True)
        self.assertFalse(row["lit"])
        self.assertEqual(row["txt"], _QUIET)
        self.assertNotIn("was not read", row["txt"])

    def test_the_mind_lamp_asks_this_look(self):
        with open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
            ui = fh.read()
        needle = "var _mindUnread = (_shMind.verdict === 'unknown');"
        self.assertEqual(ui.count(needle), 1)
        self.assertEqual(ui.count("_engRow('mind'"), 1)
        self.assertIn(
            "_engRow('mind', !_mindUnread && on && _story.length > 0,",
            ui)
        call = ui[ui.find("_engRow('mind'"):ui.find("_engRow('mind'") + 280]
        self.assertIn("? 'the journal was not read'", call)
        self.assertIn(_QUIET, call)


RED_PROOF = [
    {
        "why": "REG-1808 - an unread journal is painted as a quiet mind",
        "file": "control_ui.html",
        "find": "    var _mindUnread = (_shMind.verdict === 'unknown');\n",
        "replace": "    var _mindUnread = false;\n",
        "matches": 1,
    },
    {
        "why": "REG-1808 - a measured thought is painted as a journal that was not read",
        "file": "control_ui.html",
        "find": "    var _mindUnread = (_shMind.verdict === 'unknown');\n",
        "replace": "    var _mindUnread = true;\n",
        "matches": 1,
    },
    {
        "why": "REG-1808 - the lamp calls an unread journal a night with no thoughts yet",
        "file": "control_ui.html",
        "find": "      _mindUnread\n"
                "        ? 'the journal was not read'\n"
                "        : ((on && _story.length) ? ('thinking \u00b7 ' + _story.length + ' thought' + (_story.length > 1 ? 's' : '')) : 'quiet \u00b7 no thoughts yet'));\n",
        "replace": "      ((on && _story.length) ? ('thinking \u00b7 ' + _story.length + ' thought' + (_story.length > 1 ? 's' : '')) : 'quiet \u00b7 no thoughts yet'));\n",
        "matches": 1,
    },
    {
        "why": "REG-1808 - a leftover thought lights the lamp on an unread journal",
        "file": "control_ui.html",
        "find": "    _engRow('mind', !_mindUnread && on && _story.length > 0,\n",
        "replace": "    _engRow('mind', on && _story.length > 0,\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
