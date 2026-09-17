# -*- coding: utf-8 -*-
"""v3288 — A CONSOLE MUST BE ABLE TO SAY THAT ITS OWN SERVER IS OUT OF DATE.

Grok Bot, native LOOKED #5721820085: *"Chiliad Console v3283 · Agent v3284 · Board v3284 ·
CHILIAD panel 283 / footer 284"* — two numbers on one screen, each claiming to be the version,
with nothing saying which question either answers.

⚠ **TWO MECHANISMS ALREADY ASKED THIS AND THEY CONTRADICTED EACH OTHER**, measured 2026-09-18 on
one process in one second:

    hooks/pre-push   listener PID start vs file mtime   -> "started BEFORE the current file"
    _drift_once()    status_payload()["ver"] vs disk    -> "in sync on v3287"

The PID heuristic can be fooled by a supervisor or a re-exec; the literal comparison reads a baked
string whose provenance cannot be checked from outside. **Neither is first-hand, so neither
settles it** — and the second is worse than useless, because a detector that cannot be wrong is a
detector that cannot fire.

`module_freshness()` asks the only version of the question a running module can answer itself: it
captured its own file's mtime AT IMPORT, and compares that to the mtime NOW. No PID, no literal,
no guess about process ancestry. If the file was rewritten after this module loaded, the code
answering requests is not the code on disk.

⚠ **THIS TEST MONKEYPATCHES THE CLOCK, IT DOES NOT TOUCH THE FILE.** An earlier draft proved the
same thing by `os.utime`-ing control_app.py and restoring it. That works until it crashes between
the two, and then his LIVE console is left believing it is stale — a gate that perturbs the thing
it measures. [[a-gate-can-perturb-what-it-measures]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app  # noqa: E402


class TestAStaleServerSaysSo(unittest.TestCase):
    def test_a_freshly_loaded_module_is_not_stale(self):
        r = control_app.module_freshness()
        self.assertTrue(r.get("known"), "freshness must be MEASURED, not unknown, in a normal run")
        self.assertFalse(r.get("stale"),
                         "a module whose file has not changed since import must not claim to be "
                         "stale: %r" % (r.get("say"),))

    def test_a_rewritten_file_is_noticed_and_said_in_words(self):
        """The behaviour the whole thing exists for — and it must FIRE, not merely exist."""
        real = control_app.os.path.getmtime
        boot = control_app._BOOT_SRC_MTIME
        self.assertIsNotNone(boot, "the import-time mtime was never captured, so nothing can compare")

        def later(path):
            return boot + 2303 if os.path.abspath(path) == os.path.abspath(control_app.__file__) \
                else real(path)

        # ⚠ v3289 — THE HASH MUST MOVE TOO, AND THIS TEST WAS WRONG UNTIL IT DID. v3288 asserted
        # that a bare mtime bump meant stale, which is the false positive the cross-family eye
        # then raised: a `touch` changes no code. Simulating a REAL rewrite means new bytes, so
        # the sha is stubbed alongside the clock. The old assertion encoded the old bug.
        realsha = control_app._src_sha
        control_app._src_sha = lambda: "c0ffee" * 8
        control_app._FRESH_CACHE["val"] = None
        control_app.os.path.getmtime = later
        try:
            r = control_app.module_freshness()
        finally:
            control_app.os.path.getmtime = real          # always put the clock back
            control_app._src_sha = realsha
            control_app._FRESH_CACHE["val"] = None

        self.assertTrue(r.get("stale"),
                        "the file was rewritten 2303s after import and the module did not notice")
        self.assertEqual(r.get("agedS"), 2303, "the gap must be reported, not rounded away")
        say = r.get("say") or ""
        self.assertIn("38m", say,
                      "2303 seconds is not a thing anyone reads as forty minutes: %r" % say)
        self.assertIn("Restart", say,
                      "saying a server is stale without saying what to do about it leaves him "
                      "with a fact and no move")
        self.assertIn("PAGE changes are live", say,
                      "the boundary is the useful half: control_ui.html IS re-read per request, "
                      "so a reader who thinks nothing is live will chase a fix that already shipped")

    def test_an_unreadable_file_is_UNKNOWN_rather_than_in_sync(self):
        """A zero needs a denominator: absent evidence must never read as a clean bill."""
        real = control_app.os.path.getmtime

        def boom(path):
            raise OSError("simulated")

        control_app._FRESH_CACHE["val"] = None
        control_app.os.path.getmtime = boom
        try:
            r = control_app.module_freshness()
        finally:
            control_app.os.path.getmtime = real
            control_app._FRESH_CACHE["val"] = None

        self.assertFalse(r.get("known"), "an unreadable file must not be reported as known")
        self.assertIsNone(r.get("stale"), "unknown staleness must be None, never False")
        self.assertIn("UNMEASURED", r.get("say") or "",
                      "it must say it did not measure, rather than implying it did")

    def test_the_status_payload_carries_it(self):
        """Built and never published is the defect this board keeps re-learning."""
        import inspect
        src = inspect.getsource(control_app.status_payload)
        self.assertIn('"moduleFreshness": module_freshness()', src,
                      "the reading exists and no surface can reach it — an unjoined end")


    def test_the_panel_reads_it_and_stays_quiet_when_there_is_nothing_to_say(self):
        """The joint. A reading published and never read is the defect this board re-learns.

        ⚠ AND IT MUST NOT RENDER WHEN FRESH. v2397 stripped the footer's hover wall on his
        instruction — "i dont want this mess when i hover over it all the time. i want it clean"
        — so a permanent "in sync" chip would be re-adding exactly what he had removed. The line
        exists only when there is something to act on.
        """
        ui = io.open(os.path.join(os.path.dirname(HERE), "tv", "control_ui.html"),
                     encoding="utf-8").read()
        import frame_authority
        code = frame_authority._executable_only(ui, ".js")
        self.assertIn("st.moduleFreshness", code,
                      "the panel never reads the freshness, so the server can be stale and the "
                      "screen will not say so")
        self.assertIn("_mf.stale", code, "the stale branch is not consulted")
        self.assertIn("_mf.known === false", code,
                      "UNKNOWN is not distinguished from in-sync, which is the false-green this "
                      "whole reading exists to refuse")
        self.assertNotIn("in sync on v", code,
                         "the panel must not print a permanent in-sync chip - v2397 removed that "
                         "clutter on his instruction")


    def test_a_touch_that_changes_nothing_is_not_stale(self):
        """v3289, raised by the cross-family eye on v3288 and real.

        `touch`, a `cp -a`, or an editor writing identical bytes moves the mtime and changes no
        code. Claiming "SERVER changes are not live" then sends him to restart for nothing, and a
        warning that cries wolf is one he learns to scroll past.
        """
        real = control_app.os.path.getmtime
        boot = control_app._BOOT_SRC_MTIME

        def later(path):
            return boot + 2303 if os.path.abspath(path) == os.path.abspath(control_app.__file__) \
                else real(path)

        control_app._FRESH_CACHE["val"] = None
        control_app.os.path.getmtime = later
        try:
            r = control_app.module_freshness()
        finally:
            control_app.os.path.getmtime = real
            control_app._FRESH_CACHE["val"] = None

        self.assertFalse(r.get("stale"),
                         "the mtime moved but the BYTES are identical - this must not claim the "
                         "server is out of date: %r" % (r.get("say"),))
        self.assertIn("identical bytes", r.get("say") or "",
                      "it must say WHY it is not stale, or the next reader re-derives it")

    def test_an_OLDER_file_on_disk_is_stale_too_and_says_which_way(self):
        """The false green nobody would think to check.

        v3288 computed `stale = aged > 0`, so a file REPLACED BY AN OLDER ONE - a restore, a
        checkout, an mtime skew across machines - subtracted to a negative and reported IN SYNC
        while the process ran different code. Direction is part of the finding.
        """
        real = control_app.os.path.getmtime
        boot = control_app._BOOT_SRC_MTIME
        realsha = control_app._src_sha

        def earlier(path):
            return boot - 900 if os.path.abspath(path) == os.path.abspath(control_app.__file__) \
                else real(path)

        control_app._FRESH_CACHE["val"] = None
        control_app.os.path.getmtime = earlier
        control_app._src_sha = lambda: "deadbeef"      # different bytes, older stamp
        try:
            r = control_app.module_freshness()
        finally:
            control_app.os.path.getmtime = real
            control_app._src_sha = realsha
            control_app._FRESH_CACHE["val"] = None

        self.assertTrue(r.get("stale"),
                        "an OLDER file with different bytes is still not the code we are running")
        self.assertTrue(r.get("olderOnDisk"),
                        "which direction it drifted is part of the finding - a restore and a "
                        "forward ship need different moves")
        self.assertEqual(r.get("agedS"), 900, "the gap must be reported as a magnitude, not a "
                                              "negative that rounds to zero")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "pinning stale to False makes the detector one that cannot fire",
        "file": "tv/control_app.py",
        # ⚠ re-anchored at v3289: the old anchor `stale = aged > 0` was DELETED by the
        # content-aware rewrite, so the sabotage matched 0 times and proved nothing. A proof whose
        # anchor has rotted is inert, and inert proofs pile up exactly where the static law cannot
        # see them. [[matches-once-can-still-prove-nothing]]
        "find": '        "known": True, "stale": True, "agedS": aged, "olderOnDisk": _older,',
        "replace": '        "known": True, "stale": False, "agedS": aged, "olderOnDisk": _older,',
        "matches": 1,
    },
    {
        "why": "dropping the import-time mtime leaves nothing first-hand to compare against",
        "file": "tv/control_app.py",
        "find": "    _BOOT_SRC_MTIME = os.path.getmtime(os.path.abspath(__file__))",
        "replace": "    _BOOT_SRC_MTIME = None",
        "matches": 1,
    },
    {
        "why": "an unreadable file reported as in-sync is the false-green this exists to refuse",
        "file": "tv/control_app.py",
        "find": '        return {"known": False, "stale": None,\n                "say": "the source file cannot be read now, so this is UNMEASURED rather than "\n                       "in sync"}',
        "replace": '        return {"known": True, "stale": False, "say": "in sync"}',
        "matches": 1,
    },
    {
        "why": "dropping the hash confirmation makes a bare touch cry wolf on every poll",
        "file": "tv/control_app.py",
        "find": "    if _sha == _BOOT_SRC_SHA:",
        "replace": "    if False:",
        "matches": 1,
    },
    {
        "why": "an older file on disk must not subtract to a negative and read as in sync",
        "file": "tv/control_app.py",
        "find": "    aged = int(abs(now_mtime - _BOOT_SRC_MTIME))",
        "replace": "    aged = int(now_mtime - _BOOT_SRC_MTIME)",
        "matches": 1,
    },
    {
        "why": "a panel that never reads it leaves the server stale with the screen silent",
        "file": "tv/control_ui.html",
        "find": "      var _mf = st && st.moduleFreshness;",
        "replace": "      var _mf = null;",
        "matches": 1,
    },
    {
        "why": "not publishing it leaves the reading built and unreachable",
        "file": "tv/control_app.py",
        "find": '        "moduleFreshness": module_freshness(),',
        "replace": '        "moduleFreshnessX": module_freshness(),',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
