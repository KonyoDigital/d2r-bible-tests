# -*- coding: utf-8 -*-
"""v3325 — A STORE IS NEVER WRITTEN OVER ONE THIS PROCESS COULD NOT READ.

Three stores in this tree are READ-MODIFY-WRITTEN: the reader loads a dict, a caller mutates it,
and the whole dict is written back. If the read SWALLOWS a failure and hands back `{}`, the write
replaces a good file with just the new keys — and the file then looks authoritative, which is
strictly worse than not writing at all.

MEASURED 2026-09-18, and the rule existed in exactly ONE of the three:

    .vault_autoread.json   _vault_autoread_load / _vault_autoread_save   GUARDED — refuses
    .handoff_seen.json     _marks / --mark                               WIPED the watermarks
    shadow_watch.json      _shadow_watch_stored / _shadow_watch_note     WIPED the watch record

`_vault_autoread_save` carries the lesson in its own comment — *"NEVER WRITE MEMORY OVER A STORE
THIS PROCESS HAS NOT READ ... an empty in-memory `retired` would be written straight over a good
store"*. It was learned once and generalised to nothing. [[copy-drift]] [[the-unjoined-end]]

⚠ THE handoff ONE IS THE QUEUE DRAIN. `--mark` reads the watermarks, adds one issue, writes them
all back. A corrupt file would have silently destroyed #179 and #180's marks while printing a
normal success line. It was LATENT, not fired: the file measured readable, 332 bytes, keys
179/180/230 intact.

⚠ AND `_shadow_watch_stored`'s OWN DOCSTRING CITES [[unknown-stays-unknown]] AND
[[label-outlived-referent]] — a function written about this scar, containing it.

THREE STATES, AND COLLAPSING ANY TWO IS THE DEFECT:
    {}     the file is ABSENT — nothing recorded yet, and that IS a measurement
    dict   read and parsed
    None   unreadable or malformed — UNKNOWN, and no write may proceed on it
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()


class TestAStoreIsNeverWrittenOverAnUnreadOne(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="storeguard-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _malformed(self, name):
        p = os.path.join(self.tmp, name)
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write("{ this is not json")
        return p

    # ── the readers ───────────────────────────────────────────────────────────

    def test_the_watermark_reader_tells_absent_from_unreadable(self):
        import handoff as H
        old = H.MARKS
        try:
            H.MARKS = os.path.join(self.tmp, "nope.json")
            self.assertEqual(
                H._marks(), {},
                "an ABSENT watermark store must read as {} — measured and empty. Nothing has been "
                "marked yet, which is a fact, not a failure.")
            H.MARKS = self._malformed("bad.json")
            self.assertIsNone(
                H._marks(),
                "a MALFORMED watermark store read as a dict. `--mark` writes this value back "
                "wholesale, so {} here replaces every other issue's watermark with nothing.")
        finally:
            H.MARKS = old

    def test_the_shadow_watch_reader_tells_absent_from_unreadable(self):
        import control_app as CA
        old = CA._shadow_watch_path
        try:
            CA._shadow_watch_path = lambda: os.path.join(self.tmp, "nope.json")
            self.assertEqual(CA._shadow_watch_stored(), {},
                             "an ABSENT shadow-watch store must read as {} — never written yet.")
            _bad = self._malformed("bad2.json")
            CA._shadow_watch_path = lambda: _bad
            self.assertIsNone(
                CA._shadow_watch_stored(),
                "a MALFORMED shadow-watch store read as a dict. `_shadow_watch_note` updates and "
                "writes it back, so {} here replaces the whole record with just the new keys.")
        finally:
            CA._shadow_watch_path = old

    # ── the writers, and this is the half that stops the damage ───────────────

    def test_the_shadow_watch_writer_refuses_on_UNKNOWN(self):
        """⚠ THE ONE THAT MATTERS: a refusal, proven by the file NOT changing."""
        import control_app as CA
        p = os.path.join(self.tmp, "watch.json")
        with io.open(p, "w", encoding="utf-8") as fh:
            json.dump({"keep": "me", "and": "me too"}, fh)
        before = io.open(p, encoding="utf-8").read()
        old_path, old_read = CA._shadow_watch_path, CA._shadow_watch_stored
        try:
            CA._shadow_watch_path = lambda: p
            CA._shadow_watch_stored = lambda: None          # the store could not be read
            CA._shadow_watch_note(fresh="key")
            after = io.open(p, encoding="utf-8").read()
            self.assertEqual(
                before, after,
                "the writer replaced a store it could not read. The file now holds only the new "
                "key and looks authoritative — strictly worse than never writing.")
        finally:
            CA._shadow_watch_path, CA._shadow_watch_stored = old_path, old_read

    def test_the_watermark_writer_refuses_on_UNKNOWN(self):
        """`--mark` must not turn an unreadable file into a one-key file."""
        import handoff as H
        p = os.path.join(self.tmp, "seen.json")
        with io.open(p, "w", encoding="utf-8") as fh:
            json.dump({"179": {"ts": "keep"}, "180": {"ts": "keep"}}, fh)
        before = io.open(p, encoding="utf-8").read()
        old_marks, old_path, old_gh = H._marks, H.MARKS, H._gh
        try:
            H.MARKS = p
            H._marks = lambda: None                         # the store could not be read
            H._gh = lambda *a, **k: [{"id": 1, "created_at": "2026-01-01T00:00:00Z",
                                      "updated_at": "2026-01-01T00:00:00Z"}]
            H.mark(230)
            after = io.open(p, encoding="utf-8").read()
            self.assertEqual(
                before, after,
                "--mark wrote over a watermark store it could not read. #179 and #180 would be "
                "gone, and the drain would re-answer the entire queue while the file looked fine.")
        finally:
            H._marks, H.MARKS, H._gh = old_marks, old_path, old_gh

    def test_the_guard_that_already_existed_still_does(self):
        """BASELINE: the vault store had this right first. It must not regress while the other
        two are being fixed."""
        import control_app as CA
        _saved = dict(CA._VAULT_AUTOREAD_STORE)
        try:
            CA._VAULT_AUTOREAD_STORE["tried"] = True
            CA._VAULT_AUTOREAD_STORE["readable"] = None
            self.assertFalse(
                CA._vault_autoread_save(),
                "the vault store lost the refusal it has carried since v2904 — the one place this "
                "rule was already correct.")
        finally:
            CA._VAULT_AUTOREAD_STORE.clear(); CA._VAULT_AUTOREAD_STORE.update(_saved)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "collapsing malformed back to {} lets --mark wipe every other issue's watermark",
        "file": "tv/handoff.py",
        # ⚠ v3358 — CODE ONLY. This anchored the line WITH its trailing comment, and v3355
        # reworded that comment from "malformed/unreadable" to "malformed OR unreadable" — so the
        # proof matched 0 times and stopped proving anything, silently, in the same push that
        # repaired the thing it guards. Anchor bytes the subject cannot reword.
        "find": "    except Exception:\n        return None",
        "replace": "        return {}            # malformed/unreadable: UNKNOWN",
        "matches": 1,
    },
    {
        "why": "removing the writer's refusal replaces an unread watermark store with one key",
        "file": "tv/handoff.py",
        "find": "    if marks is None:\n        # ⚠⚠ REFUSE, DO NOT OVERWRITE.",
        "replace": "    if False:\n        # ⚠⚠ REFUSE, DO NOT OVERWRITE.",
        "matches": 1,
    },
    {
        "why": "removing the shadow-watch refusal replaces the whole record with the new keys",
        "file": "tv/control_app.py",
        "find": "    cur = _shadow_watch_stored()\n    if cur is None:\n        return",
        "replace": "    cur = _shadow_watch_stored() or {}\n    if False:\n        return",
        "matches": 1,
    },
]
