# -*- coding: utf-8 -*-
"""A WATERMARK MAY ONLY COVER WHAT THE READER WAS SHOWN — and the prompt hook counts what is owed.

⚠⚠ MEASURED 2026-09-24 07:09Z: `handoff.py --mark` marked #230 through comment 5809493768, a GrokBot
tick posted AFTER the listing that had just been read. It took the newest comment at MARK time, so a
tick nobody had seen was filed as read — the loss this module's docstring says a drain must never
cause, done by the marker. Now `drain` records the newest comment it SHOWED, `--mark` marks through
that (or through `--through <id>`), names every newer comment it left unmarked, and refuses when
nothing was shown.

And `--summary`, the one line a UserPromptSubmit hook prints on every prompt, because on the same
morning #230 carried eight ticks and #231 five looks that went unread for two hours while the drain
existed and nothing ran it. His words: *"make it a part of your system regularly to check it
always"*. DRIVEN with a fake `gh` and a temp watermark file — never his real queue. RED_PROOF below.
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import handoff as H  # noqa: E402


def _c(i, minute, body="GB-L\n\nLOOKED"):
    ts = "2026-09-24T07:%02d:00Z" % minute
    return {"id": i, "created_at": ts, "updated_at": ts, "body": body}


class AMarkCoversOnlyWhatWasShown(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="handoff-marks-")
        self._marks, self._gh = H.MARKS, H._gh
        H.MARKS = os.path.join(self.tmp, "seen.json")
        self.rows = [_c(1, 0), _c(2, 1)]
        H._gh = self._fake_gh

    def _fake_gh(self, path, *a, **k):
        """GitHub's `since` filters on updated_at, INCLUSIVE — the fake must too, or it tests a
        queue that never shrinks."""
        since = path.split("since=", 1)[1].split("&", 1)[0] if "since=" in path else None
        return [dict(r) for r in self.rows if since is None or r["updated_at"] >= since]

    def tearDown(self):
        H.MARKS, H._gh = self._marks, self._gh
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _quiet(self, fn, *a, **k):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            fn(*a, **k)
        return out.getvalue()

    def _mark_of(self, issue="230"):
        with io.open(H.MARKS, encoding="utf-8") as fh:
            return json.load(fh).get(issue)

    def test_a_comment_that_arrives_after_the_drain_is_NOT_marked(self):
        self._quiet(H.drain, "230")
        self.rows.append(_c(3, 9))                 # the 07:09 tick, posted after the listing
        said = self._quiet(H.mark, "230")
        self.assertEqual(self._mark_of()["id"], 2, "the mark covered a comment nobody was shown")
        self.assertIn("NOT marked", said)
        self.assertIn("#3", said, "the unmarked comment was not named: %s" % said)

    def test_a_bucket_longer_than_the_limit_marks_only_what_was_listed(self):
        """#171 — the second eye on 4a222c64: a bucket past --limit printed '+N more not listed' and
        the mark still went through the newest comment overall."""
        self.rows = [_c(i, i) for i in range(1, 6)]          # five FYI ticks, 07:01 .. 07:05
        said = self._quiet(H.drain, "230", limit=2)
        self.assertIn("more not listed", said, "premise: the limit must cut this bucket")
        self._quiet(H.mark, "230")
        self.assertEqual(self._mark_of()["id"], 2,
                         "the mark covered comments the drain said it did not list")

    def test_nothing_shown_means_nothing_marked(self):
        said = self._quiet(H.mark, "230")
        self.assertIn("REFUSED", said)
        self.assertFalse(os.path.exists(H.MARKS), "a mark was written with nothing shown")

    def test_through_names_the_last_comment_read(self):
        self._quiet(H.mark, "230", through="1")
        self.assertEqual(self._mark_of()["id"], 1)
        said = self._quiet(H.mark, "230", through="999")
        self.assertIn("REFUSED", said, "a --through naming no comment moved the mark")

    def test_the_summary_counts_what_is_new_and_what_is_owed(self):
        self.rows.append(_c(3, 5, body="ASK: is the shelf blank on your seat?"))
        line = H.summary("230")
        self.assertIn("3 NEW", line, line)
        self.assertIn("1 ACT/ASK owed", line, line)
        self._quiet(H.drain, "230")
        self._quiet(H.mark, "230")
        self.assertIn("nothing new", H.summary("230"))

    def test_an_unreachable_queue_is_UNKNOWN_never_a_zero(self):
        def _boom(*a, **k):
            raise RuntimeError("gh timed out")
        H._gh = _boom
        line = H.summary("230")
        self.assertIn("UNKNOWN", line)
        self.assertNotIn("nothing new", line)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#171 - the drain records the newest comment overall as shown again, so --mark files the unlisted tail as read (second eye on 4a222c64)",
        "file": "handoff.py",
        "find": "        if str(c.get(\"id\")) not in shown_ids:\n            break\n",
        "replace": "        if False:\n            break\n",
        "matches": 1,
    },
    {
        "why": "--mark takes the newest comment at MARK time again: a tick posted after the drain is filed as read (07:09Z, 2026-09-24)",
        "file": "handoff.py",
        "find": "    newest = rows[hit[0]] if hit else rows[-1]\n    later = rows[hit[0] + 1:] if hit else []\n",
        "replace": "    newest = rows[-1]\n    later = []\n",
        "matches": 1,
    },
    {
        "why": "the summary stops counting ACT/ASK: a question to Claude reads as a plain tick in the prompt hook",
        "file": "handoff.py",
        "find": "    owed = sum(1 for v in verbs if v in OWED)\n",
        "replace": "    owed = 0\n",
        "matches": 1,
    },
]
