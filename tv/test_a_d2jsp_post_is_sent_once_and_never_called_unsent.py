# -*- coding: utf-8 -*-
"""REG-2490 / REG-2491 - A d2jsp POST IS SENT ONCE, AND A CLICKED POST IS NEVER CALLED UNSENT.

#106 (Reviewer D), measured at v3784 (7285e7efc):
  - one 25 s deadline in _chrome_post covered loading the board, opening New Trade, filling the
    form, the submit and the redirect. A run that had clicked and had not reached topic.php came
    back as the post.php URL, which _send_through_chrome called 'not-posted', and any OSError after
    the click was 'unread'. Both read "nothing was posted" on the page, so he clicks again and a
    duplicate goes up.
  - the server had no lock. d2jsp_send ran once per request on a ThreadingHTTPServer, so a board
    reload or a second tab started a second Chrome post; only the page's `posting` flag guarded it.
#83: an ImportError of websocket escaped the route, and a Chrome that would not start read 'unread'.

No Chrome runs here: the REAL flow (_chrome_post, _run_flow, _flow_step) drives a board made of
strings through the same goto / act / snapshot a scratch Chrome answers, on a clock it advances.
  - two sends at once (threads and an Event): one Chrome post runs; the other is busy, reads no cookie.
  - the form and the receipt have their own budgets: a board that shows the form after 20 s and the
    new topic 25 s after the click is submitted.
  - a click with no receipt is maybe-sent with the board and the time, and so is a browser that stops
    answering once the fill was sent. The board sending the form back is not-posted, and so is a run
    that never clicked; unread when no forum page ever loaded.
  - after the receipt wait the board list is read again: a new topic whose text is exactly the subject
    is the receipt; an older one, listed before the click or bumped in from page 2, never is, and two
    new ones are maybe-sent.
  - the same draft inside 30 minutes of maybe-sent / submitted reads no cookie and starts no Chrome
    (maybe-sent-recently / already-posted); another body, or 30 minutes later, runs.
  - a missing websocket module, a missing Chrome and a Chrome that exits before its DevTools answers
    are chrome-start with a why, and leave no profile and nothing in flight.
  - every answer's reason is one of SEND_REASONS, and none carries the cookie.
RED_PROOF below.
"""
from __future__ import annotations

import contextlib
import json
import os
import sys
import tempfile
import threading
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402  #171 - this run's scratch dirs leave with it
_fx_tmp.contain()
from console_safe import enable  # noqa: E402
enable()

import d2jsp_chrome as desk  # noqa: E402

ORIGIN = "http://127.0.0.1:17772"
HOST = "127.0.0.1:17772"
PORT = 17772
COOKIE = "sid=SECRETCOOKIE"
SUBJECT = "Selling Grief Phase Blade"
BODY = "Selling Grief Phase Blade\n+340-400% Enhanced Damage\n30 fg"
BOARD_URL = "https://forums.d2jsp.org/forum.php?f=268"
FORM_URL = "https://forums.d2jsp.org/post.php?mode=newtrade&f=268"
T0 = 1800000000.0
# the board before the click: an older topic with this very subject (t=200) and newer ones beside it
LISTED = [(910, "Selling Shako"), (905, "WTB Enigma"), (200, SUBJECT), (880, "Selling Ber")]


class Clock(object):
    """The flow's clock. Its nap moves time on, so no case sleeps."""

    def __init__(self, t=1000.0):
        self.t = float(t)

    def __call__(self):
        return self.t

    def nap(self, seconds):
        self.t += float(seconds)


class Board(object):
    """Board 268 as strings: its topic list with a New Trade link, the trade form, and what the
    submit does. The flow drives it through goto / act / snapshot, as it drives a scratch Chrome.

    then: 'topic' (the new topic loads land_after seconds after the click), 'stay' (the page never
    moves on), 'form' (the board sends the form back) or 'silent' (the browser stops answering
    once the fill was sent; the click still happened)."""

    def __init__(self, clock, listed=LISTED, then="stay", listed_after=None, new_id=0,
                 form_after=0.0, land_after=0.0, loads=True, trade_link=True):
        self.clock = clock
        self.listed = list(listed)
        self.listed_after = listed_after
        self.then = then
        self.new_id = new_id
        self.form_after = form_after
        self.land_after = land_after
        self.loads = loads
        self.trade_link = trade_link
        self.href = "about:blank"
        self.mark = False
        self.opened_at = None
        self.clicked_at = None
        self.gotos = []
        self.ran = []
        self.clicks = 0

    def _load(self, url):
        self.href = url
        self.mark = False

    def goto(self, url):
        self.gotos.append((url, self.clock()))
        self._load(url)

    def _form_up(self):
        return (self.href == FORM_URL and self.opened_at is not None
                and self.clock() - self.opened_at >= self.form_after)

    def act(self, name, script):
        self.ran.append(name)
        if name == "open-trade":
            if self.href == BOARD_URL and self.trade_link and 'label!=="New Trade"' in script:
                self.opened_at = self.clock()
                self._load(FORM_URL)
                return "opened"
            return "no-link"
        if name == "fill":
            if not self._form_up():
                return "no-form"
            # the script as it went out: its selectors are JSON strings inside the JavaScript
            for need in (json.dumps('textarea[name="Post"]'), json.dumps('input[name="ttitle"]'),
                         "Selling Item", json.dumps('input[name="submit"]'), "btn.click()",
                         json.dumps(SUBJECT)):
                if need not in script:
                    return "no-form"
            self.clicks += 1
            self.clicked_at = self.clock()
            self.mark = True
            if self.then == "silent":
                raise OSError("the browser stopped answering after the click")
            if self.then == "form":
                self._load(FORM_URL)
            return "clicked"
        return ""

    def snapshot(self):
        if (self.then == "topic" and self.clicked_at is not None and self.href == FORM_URL
                and self.clock() - self.clicked_at >= self.land_after):
            self._load("https://forums.d2jsp.org/topic.php?t=%d&f=268" % self.new_id)
        return {"href": self.href, "ready": "complete", "mark": self.mark, "html": self._html()}

    def _html(self):
        if not self.loads:
            return "<title>Just a moment...</title>"
        if self.href == BOARD_URL:
            rows = self.listed
            if self.clicked_at is not None and self.listed_after is not None:
                rows = self.listed_after
            links = "".join('<tr><td><a href="topic.php?t=%d&amp;f=268">%s</a></td></tr>' % row
                            for row in rows)
            trade = '<a href="post.php?mode=newtrade&amp;f=268">New Trade</a>' if self.trade_link else ""
            return ('<html><body><a href="login.php?mode=logout">Log Out</a>%s<table>%s</table>'
                    '</body></html>' % (trade, links))
        if self.href == FORM_URL:
            if not self._form_up():
                return "<html><body>Loading</body></html>"
            return ('<html><body><form action="post.php"><input name="ttitle">'
                    '<textarea name="Post"></textarea><label for="s1">Selling Item</label>'
                    '<input type="radio" id="s1" name="sType"><input type="submit" name="submit">'
                    '</form></body></html>')
        if "topic.php" in self.href:
            return "<html><body><h1>%s</h1></body></html>" % SUBJECT
        return "<html><head></head><body></body></html>"


class Seat(object):
    """One console posting through the real flow over a Board. Counts its cookie reads and Chrome starts."""

    def __init__(self, board=None, clock=None):
        self.clock = clock or Clock()
        self.board = board
        self.cookies = 0
        self.starts = 0
        self.prefixes = []

    def cookie_get(self):
        self.cookies += 1
        return COOKIE, "ok"

    def chrome(self, cookie, prefix):
        self.starts += 1
        self.prefixes.append(prefix)
        return contextlib.nullcontext(self.board)

    def chrome_post(self, subject, text, cookie):
        return desk._chrome_post(subject, text, cookie, 268, chrome=self.chrome,
                                 clock=self.clock, nap=self.clock.nap)

    def send(self, change=None, now=None):
        draft = {"subject": SUBJECT, "body": BODY, "forum": 268}
        draft.update(change or {})
        return desk.d2jsp_send(draft, ORIGIN, HOST, PORT, cookie_get=self.cookie_get,
                               chrome_post=self.chrome_post, open_login=lambda: False, now=now)


class APostIsSentOnceAndNeverCalledUnsent(unittest.TestCase):

    def setUp(self):
        desk._SENT.clear()
        self.addCleanup(desk._SENT.clear)

    def patch(self, obj, name, value):
        old = getattr(obj, name)
        setattr(obj, name, value)
        self.addCleanup(setattr, obj, name, old)

    def patch_module(self, name, value):
        gone = object()
        old = sys.modules.get(name, gone)
        sys.modules[name] = value

        def restore():
            if old is gone:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old
        self.addCleanup(restore)

    def check(self, out):
        """Every answer: one of the declared reasons, and never the cookie."""
        self.assertIn(out.get("reason"), desk.SEND_REASONS, out)
        self.assertNotIn("SECRETCOOKIE", json.dumps(out))
        return out

    def post(self, board, clock):
        """The real post flow over `board`. -> its result"""
        seat = Seat(board, clock)
        got = desk._chrome_post(SUBJECT, BODY, COOKIE, 268, chrome=seat.chrome,
                                clock=clock, nap=clock.nap)
        self.assertEqual(seat.prefixes, ["d2jsp-post-"])
        self.assertLessEqual(board.clicks, 1, "the submit was clicked more than once")
        self.assertEqual(board.gotos[0][0], BOARD_URL, "the run did not start on the board list")
        self.assertFalse([u for u, _t in board.gotos if "mode=post" in u], "the old compose address was opened")
        return got

    def verdict(self, got, board=268):
        code, out = desk._send_verdict(got, board, desk._stamp(T0), lambda: False)
        self.assertEqual(code, 200)
        return self.check(out)

    def test_two_sends_at_once_start_one_chrome_post(self):
        inside = threading.Event()
        release = threading.Event()
        count = {"chrome": 0, "cookie": 0}
        guard = threading.Lock()

        def cookie_get():
            with guard:
                count["cookie"] += 1
            return COOKIE, "ok"

        def chrome_post(subject, text, cookie):
            with guard:
                count["chrome"] += 1
                n = count["chrome"]
            if n == 1:
                inside.set()
                release.wait(10)
            return "https://forums.d2jsp.org/topic.php?t=%d&f=268" % (800 + n)

        def send(subject):
            draft = {"subject": subject, "body": subject + "\n30 fg", "forum": 268}
            return desk.d2jsp_send(draft, ORIGIN, HOST, PORT, cookie_get=cookie_get,
                                   chrome_post=chrome_post, open_login=lambda: False)

        got = {}

        def first_send():
            try:
                got["first"] = send("Selling Grief Phase Blade")
            except BaseException as exc:          # a lock released twice raises here
                got["error"] = repr(exc)

        th = threading.Thread(target=first_send, daemon=True)
        th.start()
        try:
            self.assertTrue(inside.wait(10), "the first send never reached Chrome - UNKNOWN, not a pass")
            # another draft, so 'busy' can only come from the lock and never from the re-send record
            code, second = send("Selling Shako Harlequin Crest")
        finally:
            release.set()
            th.join(10)
        self.assertEqual(code, 200)
        self.check(second)
        self.assertEqual(second["reason"], "busy", "a second send ran while one was in flight")
        self.assertFalse(second["ok"])
        self.assertEqual(count["chrome"], 1, "two sends at once started %d Chrome posts" % count["chrome"])
        self.assertEqual(count["cookie"], 1, "a busy send read the cookie")
        self.assertNotIn("error", got)
        self.assertEqual(self.check(got["first"][1])["reason"], "submitted")
        code, third = send("Selling Shako Harlequin Crest")
        self.assertEqual(self.check(third)["reason"], "submitted", "the console stayed busy after the send")
        self.assertEqual(count["chrome"], 2)

    def test_a_slow_board_that_takes_the_post_is_submitted(self):
        # The form shows after 20 s and the topic loads 25 s after the click: 46 s in all. One 25 s
        # deadline for both called this post unsent.
        clock = Clock()
        board = Board(clock, then="topic", new_id=951, form_after=20.0, land_after=25.0)
        got = self.post(board, clock)
        out = self.verdict(got)
        self.assertTrue(out["ok"])
        self.assertEqual(out["reason"], "submitted")
        self.assertEqual(out["topic"], "https://forums.d2jsp.org/topic.php?t=951&f=268")
        self.assertEqual(board.clicks, 1)
        self.assertGreaterEqual(board.clicked_at - board.opened_at, 20.0)

    def test_a_click_with_no_receipt_is_maybe_sent_never_unsent(self):
        clock = Clock()
        board = Board(clock, then="stay")
        got = self.post(board, clock)
        self.assertTrue(got["clicked"])
        out = self.verdict(got)
        self.assertFalse(out["ok"])
        self.assertEqual(out["reason"], "maybe-sent")
        self.assertEqual(out["board"], 268)
        self.assertEqual(out["at"], desk._stamp(T0))
        self.assertNotIn("topic", out)
        self.assertEqual(board.clicks, 1)
        # the receipt was waited for at least 30 s after the click, and the board list read again
        reread = [t for u, t in board.gotos[1:] if u == BOARD_URL]
        self.assertTrue(reread, "the board list was not read again before maybe-sent")
        self.assertGreaterEqual(reread[0] - board.clicked_at, 30.0)

        clock = Clock()
        board = Board(clock, then="silent")
        got = self.post(board, clock)
        out = self.verdict(got)
        self.assertEqual(out["reason"], "maybe-sent",
                         "a fill that was sent and never answered may have clicked")
        self.assertEqual(board.clicks, 1, "an unanswered submit was sent again")

        # the same through d2jsp_send: the answer carries the time the send began
        clock = Clock()
        seat = Seat(Board(clock, then="stay"), clock)
        code, out = seat.send(now=T0)
        self.check(out)
        self.assertEqual(out["reason"], "maybe-sent")
        self.assertEqual(out["at"], desk._stamp(T0))

    def test_only_a_run_that_never_clicked_is_unsent(self):
        clock = Clock()
        board = Board(clock, then="form")
        got = self.post(board, clock)
        self.assertTrue(got["clicked"])
        self.assertTrue(got["back"])
        self.assertEqual(self.verdict(got)["reason"], "not-posted",
                         "the board sent the form back and showed no new topic")

        clock = Clock()
        board = Board(clock, trade_link=False)
        got = self.post(board, clock)
        self.assertFalse(got["clicked"])
        self.assertEqual(board.clicks, 0)
        self.assertEqual(self.verdict(got)["reason"], "not-posted")

        clock = Clock()
        board = Board(clock, loads=False)
        got = self.post(board, clock)
        self.assertFalse(got["clicked"])
        self.assertEqual(self.verdict(got)["reason"], "unread")

        clock = Clock()
        board = Board(clock, form_after=60.0)
        got = self.post(board, clock)
        self.assertFalse(got["clicked"])
        self.assertEqual(self.verdict(got)["reason"], "not-posted")

        # a topic page before any click is not a receipt
        st = desk._flow_begin("post", SUBJECT, 268, BOARD_URL)
        st, act = desk._flow_step(st, {"href": "https://forums.d2jsp.org/topic.php?t=9&f=268",
                                       "ready": "complete", "mark": False,
                                       "html": "<html><body>a topic</body></html>"}, 0.0)
        self.assertEqual(act, ("wait",))
        self.assertFalse(st["clicked"])

    def test_a_new_same_subject_topic_on_the_board_is_the_receipt(self):
        clock = Clock()
        board = Board(clock, then="stay", listed_after=[(960, SUBJECT)] + LISTED)
        got = self.post(board, clock)
        out = self.verdict(got)
        self.assertTrue(out["ok"])
        self.assertEqual(out["reason"], "submitted")
        self.assertEqual(out["topic"], "https://forums.d2jsp.org/topic.php?t=960&f=268")

        clock = Clock()
        board = Board(clock, then="stay", listed_after=[(961, SUBJECT), (960, SUBJECT)] + LISTED)
        got = self.post(board, clock)
        self.assertEqual(self.verdict(got)["reason"], "maybe-sent",
                         "two new topics carry the subject: which one is his is unknown")

    def test_an_older_same_subject_topic_is_never_the_receipt(self):
        # t=200 carries the subject and was on the list before the click: not his new post.
        clock = Clock()
        board = Board(clock, then="stay", listed_after=LISTED)
        got = self.post(board, clock)
        out = self.verdict(got)
        self.assertEqual(out["reason"], "maybe-sent", "a topic listed before the click was taken as the receipt")
        self.assertNotIn("topic", out)

        # t=640 was not on the list before the click (bumped in from page 2), and it is older than
        # the newest topic the list showed then (910): not his new post either.
        others = [row for row in LISTED if row[1] != SUBJECT]
        clock = Clock()
        board = Board(clock, listed=others, then="stay", listed_after=[(640, SUBJECT)] + others)
        got = self.post(board, clock)
        out = self.verdict(got)
        self.assertEqual(out["reason"], "maybe-sent", "an older topic bumped onto the list was taken as the receipt")
        self.assertNotIn("topic", out)

        clock = Clock()
        board = Board(clock, listed=others, then="form", listed_after=[(640, SUBJECT)] + others)
        got = self.post(board, clock)
        self.assertEqual(self.verdict(got)["reason"], "not-posted")

    def test_an_identical_resend_inside_30_minutes_starts_no_chrome(self):
        clock = Clock()
        seat = Seat(Board(clock, then="stay"), clock)
        code, out = seat.send(now=T0)
        self.assertEqual(self.check(out)["reason"], "maybe-sent")
        self.assertEqual((seat.starts, seat.cookies), (1, 1))

        seat.board = Board(clock, then="topic", new_id=970)
        code, out = seat.send(now=T0 + 29 * 60)
        self.check(out)
        self.assertEqual(out["reason"], "maybe-sent-recently")
        self.assertEqual(out["at"], desk._stamp(T0))
        self.assertEqual((seat.starts, seat.cookies), (1, 1), "a re-send inside 30 min started Chrome")

        code, out = seat.send({"body": BODY.replace("30 fg", "35 fg")}, now=T0 + 29 * 60)
        self.assertEqual(self.check(out)["reason"], "submitted", "another body is another draft")
        self.assertEqual(seat.starts, 2)

        seat.board = Board(clock, then="topic", new_id=971)
        code, out = seat.send(now=T0 + 31 * 60)
        self.assertEqual(self.check(out)["reason"], "submitted", "30 minutes on, the same draft runs")
        self.assertEqual(out["topic"], "https://forums.d2jsp.org/topic.php?t=971&f=268")
        self.assertEqual(seat.starts, 3)

        code, out = seat.send(now=T0 + 45 * 60)
        self.check(out)
        self.assertEqual(out["reason"], "already-posted")
        self.assertEqual(out["topic"], "https://forums.d2jsp.org/topic.php?t=971&f=268")
        self.assertEqual(out["at"], desk._stamp(T0 + 31 * 60))
        self.assertEqual((seat.starts, seat.cookies), (3, 3), "a re-send after a submit started Chrome")

    def test_a_chrome_that_cannot_start_is_chrome_start(self):
        made = []
        real_mkdtemp = tempfile.mkdtemp

        def mkdtemp(*args, **kwargs):
            path = real_mkdtemp(*args, **kwargs)
            made.append(path)
            return path
        self.patch(desk, "tempfile", types.SimpleNamespace(mkdtemp=mkdtemp, gettempdir=tempfile.gettempdir))
        swept = []
        self.patch(desk, "_sweep_stale_scratch", lambda now=None, tmp=None: swept.append(1) or 0)
        asked = []

        def no_chrome():
            asked.append(1)
            return None
        self.patch(desk, "_chrome_bin", no_chrome)

        def send():
            code, out = desk.d2jsp_send({"subject": SUBJECT, "body": BODY, "forum": 268},
                                        ORIGIN, HOST, PORT, cookie_get=lambda: (COOKIE, "ok"),
                                        open_login=lambda: False)
            self.assertEqual(code, 200)
            return self.check(out)

        self.patch_module("websocket", None)          # `import websocket` raises ImportError
        out = send()
        self.assertEqual(out["reason"], "chrome-start")
        self.assertEqual(out["why"], desk._START_WHY["websocket"])
        self.assertEqual((asked, made), ([], []), "a run without its websocket module went on to start Chrome")

        self.patch_module("websocket", types.ModuleType("websocket"))
        out = send()
        self.assertEqual(out["reason"], "chrome-start")
        self.assertEqual(out["why"], desk._START_WHY["no-chrome"])
        self.assertEqual(made, [])

        # a "browser" that exits on Chrome's flags: its DevTools never answers
        self.patch(desk, "_chrome_bin", lambda: sys.executable)
        held = []
        real_up = desk._devtools_up

        def devtools_up(base, proc, wait_s=12):
            held.append([pair[0] for pair in desk._IN_FLIGHT.values()] == [proc])
            return real_up(base, proc, wait_s)
        self.patch(desk, "_devtools_up", devtools_up)
        out = send()
        self.assertEqual(out["reason"], "chrome-start")
        self.assertEqual(out["why"], desk._START_WHY["devtools"])
        self.assertEqual(held, [True], "a starting Chrome was not held for the exit reaper")
        self.assertEqual(len(made), 1)
        self.assertTrue(os.path.basename(made[0]).startswith("d2jsp-post-"))
        self.assertFalse(os.path.exists(made[0]), "a Chrome that did not start left its profile")
        self.assertEqual(desk._IN_FLIGHT, {}, "a Chrome that did not start is still held as in flight")
        self.assertEqual(swept, [1], "the scratch Chrome was started without a sweep first")


RED_PROOF = [
    {
        "why": "REG-2490 - the send lock is not taken: a second send while one runs reads the cookie and "
               "starts a second Chrome post",
        "file": "tv/d2jsp_chrome.py",
        "find": '    if not _SEND_LOCK.acquire(False):\n        return 200, {"ok": False, "reason": "busy"}\n',
        "replace": "    _SEND_LOCK.acquire(False)\n",
        "matches": 1,
    },
    {
        "why": "REG-2490 - a clicked submit with no receipt is mapped back to not-posted, the 'nothing was "
               "posted' that invites a duplicate",
        "file": "tv/d2jsp_chrome.py",
        "find": '        return 200, {"ok": False, "reason": "maybe-sent", "board": int(board), "at": at}\n',
        "replace": '        return 200, {"ok": False, "reason": "not-posted"}\n',
        "matches": 1,
    },
    {
        "why": "REG-2490 - any same-subject topic on the board is taken as the receipt, so an older topic "
               "reads as his new post",
        "file": "tv/d2jsp_chrome.py",
        "find": '                         if tid not in before and st["top"] is not None and tid > st["top"])\n',
        "replace": "                         if True)\n",
        "matches": 1,
    },
    {
        "why": "REG-2490 - an identical re-send after a maybe-sent starts Chrome again: a second post of the "
               "same draft",
        "file": "tv/d2jsp_chrome.py",
        "find": '    return {"ok": False, "reason": "maybe-sent-recently", "at": prior["at"]}\n',
        "replace": "    return None\n",
        "matches": 1,
    },
    {
        "why": "REG-2490 - the receipt is given less than 30 s again, so a slow board that took the post "
               "reads as not confirmed",
        "file": "tv/d2jsp_chrome.py",
        "find": "_RECEIPT_S = 35.0",
        "replace": "_RECEIPT_S = 5.0",
        "matches": 1,
    },
    {
        "why": "REG-2490 - a fill that was sent and never answered is read as no click, so the submit is "
               "sent again and the run is called unsent",
        "file": "tv/d2jsp_chrome.py",
        "find": '        if word in ("clicked", _NO_ANSWER):\n',
        "replace": '        if word == "clicked":\n',
        "matches": 1,
    },
    {
        "why": "REG-2491 - a missing websocket module escapes as ImportError again instead of chrome-start",
        "file": "tv/d2jsp_chrome.py",
        "find": '        raise ChromeStart("websocket")\n',
        "replace": "        raise\n",
        "matches": 1,
    },
    {
        "why": "REG-2491 - a Chrome that could not start collapses into unread again",
        "file": "tv/d2jsp_chrome.py",
        "find": '        return None, {"ok": False, "reason": "chrome-start", "why": stop.why}\n',
        "replace": '        return None, {"ok": False, "reason": "unread"}\n',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
