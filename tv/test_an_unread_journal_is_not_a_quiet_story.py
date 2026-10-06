# -*- coding: utf-8 -*-
"""REG-1809 — AN UNREAD JOURNAL IS NOT A QUIET STORY.

The story feed treats an empty story as a night that has not started.
An unread journal is that same empty list: the poll already says
verdict unknown, because the walk did not copy the story.

A measured empty night still says the story builds. A landed line is
still a line. An idle night with a line still shows that line. A miss
with no line still says the story builds. An unread walk says the
journal was not read, and a leftover list does not paint. A second
poll still repaints when the walk goes unread.

Nothing here reads his journal. RED_PROOF below. [[unknown-stays-unknown]]
"""
import json
import os
import subprocess
import unittest


HERE = os.path.dirname(os.path.abspath(__file__))

_NOT_READ = "the journal was not read"
_QUIET = "session story builds"


def _slice():
    with open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
        ui = fh.read()
    start = ui.find("    // REG-1809 — unknown is a journal that was not read.")
    end = ui.find("    var ev = st.events", start)
    if start < 0 or end < 0:
        raise AssertionError("the story feed is not in control_ui.html")
    fn = ui[start:end]
    if "\x00" in fn:
        raise AssertionError("the story slice crossed the null byte")
    if fn.count("window.__mindMode === 'story'") != 1:
        raise AssertionError("the story slice does not hold the one story feed")
    return fn


def _paint(script):
    js = (
        "var window = {};\n"
        "var brainSig = '';\n"
        "var brain = {innerHTML: ''};\n"
        "function esc(s){return String(s==null?'':s);}\n"
        "function paintStory(st, windowStory, omitWindow){\n"
        "  window.__mindMode = 'story';\n"
        "  if (omitWindow) delete window.__mindStory;\n"
        "  else window.__mindStory = windowStory;\n"
        + _slice()
        + "\n}\n"
        + script
    )
    got = subprocess.run(
        ["node", "-"], input=js.encode("utf-8"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    if got.returncode != 0:
        raise AssertionError(got.stderr.decode("utf-8", "replace")[:800])
    return json.loads(got.stdout.decode("utf-8"))


def _story(verdict="idle", story=None, window_story=None, omit_window=False,
           omit_health=False):
    st = {}
    if not omit_health:
        sh = {}
        if verdict is not None:
            sh["verdict"] = verdict
        st["sessionHealth"] = sh
    if story is not None:
        st["mindStory"] = story
    window_js = "null" if window_story is None else json.dumps(window_story)
    return _paint(
        "paintStory("
        + json.dumps(st) + ", " + window_js + ", "
        + ("true" if omit_window else "false") + ");\n"
        "process.stdout.write(JSON.stringify(brain.innerHTML));\n"
    )


class AnUnreadJournalIsNotAQuietStory(unittest.TestCase):

    def test_a_measured_empty_night_still_says_the_story_builds(self):
        html = _story(verdict="idle", story=[], window_story=[])
        self.assertIn(_QUIET, html)
        self.assertNotIn(_NOT_READ, html)
        self.assertNotIn("visited", html)

    def test_a_missing_session_health_is_still_the_quiet_story(self):
        html = _story(omit_health=True, window_story=[])
        self.assertIn(_QUIET, html)
        self.assertNotIn(_NOT_READ, html)

    def test_a_landed_line_is_still_a_line(self):
        html = _story(verdict="ok", window_story=["visited gems"])
        self.assertIn("visited gems", html)
        self.assertNotIn(_QUIET, html)
        self.assertNotIn(_NOT_READ, html)

    def test_two_landed_lines_are_still_those_lines(self):
        html = _story(
            verdict="ok",
            window_story=["visited gems", "named Magefist"])
        self.assertIn("visited gems", html)
        self.assertIn("named Magefist", html)
        self.assertNotIn(_QUIET, html)
        self.assertNotIn(_NOT_READ, html)

    def test_an_idle_night_with_a_line_still_shows_that_line(self):
        html = _story(verdict="idle", window_story=["visited gems"])
        self.assertIn("visited gems", html)
        self.assertNotIn(_QUIET, html)
        self.assertNotIn(_NOT_READ, html)

    def test_a_miss_with_no_line_still_says_the_story_builds(self):
        html = _story(verdict="miss", story=[], window_story=[])
        self.assertIn(_QUIET, html)
        self.assertNotIn(_NOT_READ, html)

    def test_an_unread_journal_is_not_a_quiet_story(self):
        html = _story(verdict="unknown", story=[], window_story=[])
        self.assertIn(_NOT_READ, html)
        self.assertNotIn(_QUIET, html)
        self.assertNotIn("visited", html)

    def test_a_leftover_list_does_not_paint_an_unread_story(self):
        html = _story(
            verdict="unknown",
            window_story=["visited gems", "named Magefist"])
        self.assertIn(_NOT_READ, html)
        self.assertNotIn("visited", html)
        self.assertNotIn("Magefist", html)
        self.assertNotIn(_QUIET, html)

    def test_a_leftover_mind_story_does_not_paint_when_the_window_has_none(self):
        html = _story(
            verdict="unknown",
            story=["visited gems", "named Magefist"],
            omit_window=True)
        self.assertIn(_NOT_READ, html)
        self.assertNotIn("visited", html)
        self.assertNotIn("Magefist", html)
        self.assertNotIn(_QUIET, html)

    def test_a_second_poll_repaints_when_the_walk_goes_unread(self):
        got = _paint(
            "paintStory({sessionHealth:{verdict:'idle'}, mindStory:[]}, []);\n"
            "var a = brain.innerHTML;\n"
            "paintStory({sessionHealth:{verdict:'unknown'}, mindStory:[]}, []);\n"
            "var b = brain.innerHTML;\n"
            "process.stdout.write(JSON.stringify({a:a, b:b}));\n"
        )
        self.assertIn(_QUIET, got["a"])
        self.assertNotIn(_NOT_READ, got["a"])
        self.assertIn(_NOT_READ, got["b"])
        self.assertNotIn(_QUIET, got["b"])

    def test_the_story_feed_asks_this_look(self):
        fn = _slice()
        self.assertEqual(fn.count("var storyUnread = (_shStory.verdict === 'unknown');"), 1)
        self.assertEqual(fn.count(_NOT_READ), 1)
        self.assertEqual(fn.count(_QUIET), 1)
        self.assertIn("storyUnread ? 'unread'", fn)
        self.assertIn("if (storyUnread) {", fn)


RED_PROOF = [
    {
        "why": "REG-1809 - an unread journal is painted as a quiet story",
        "file": "control_ui.html",
        "find": "      var storyUnread = (_shStory.verdict === 'unknown');\n",
        "replace": "      var storyUnread = false;\n",
        "matches": 1,
    },
    {
        "why": "REG-1809 - a measured night is painted as a journal that was not read",
        "file": "control_ui.html",
        "find": "      var storyUnread = (_shStory.verdict === 'unknown');\n",
        "replace": "      var storyUnread = true;\n",
        "matches": 1,
    },
    {
        "why": "REG-1809 - the feed calls an unread journal a night that has not started",
        "file": "control_ui.html",
        "find": "      if (storyUnread) {\n"
                "        brain.innerHTML = '<div class=\"empty\">the journal was not read</div>';\n"
                "      } else if (!story.length) {\n",
        "replace": "      if (!story.length) {\n",
        "matches": 1,
    },
    {
        "why": "REG-1809 - a leftover list paints on an unread journal",
        "file": "control_ui.html",
        "find": "      if (storyUnread) {\n"
                "        brain.innerHTML = '<div class=\"empty\">the journal was not read</div>';\n"
                "      } else if (!story.length) {\n",
        "replace": "      if (storyUnread && !story.length) {\n"
                   "        brain.innerHTML = '<div class=\"empty\">the journal was not read</div>';\n"
                   "      } else if (!story.length) {\n",
        "matches": 1,
    },
    {
        "why": "REG-1809 - a second poll keeps the quiet story after the walk goes unread",
        "file": "control_ui.html",
        "find": "      var ssig = 'story|' + (storyUnread ? 'unread' : story.join('\u00a6'));\n",
        "replace": "      var ssig = 'story|' + story.join('\u00a6');\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
