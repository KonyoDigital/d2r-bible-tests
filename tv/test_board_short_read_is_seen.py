# -*- coding: utf-8 -*-
"""v2723 — A TORN READ WAS SERVED AS A NORMAL 200, AND THE ONLY WITNESS WAS THE PAGE IT BROKE.

REG-681 fixed the WRITE side: `bump_version` truncated on open, leaving his 6 MB bible.html at ZERO
BYTES for a measured 4.8% of concurrent reads. This closes the SERVE side, which nothing watched.

⚠⚠ WHY IT COULD NEVER HAVE BEEN CAUGHT BEFORE. An empty read does not raise, so the serve path's
`except` never fired: `body = b""` went out with a 200 and a Content-Length of 0. And both existing
blank-surface checks in console_doctor — `ui_faults_recent` and `uiBeat.panels` — depend on the
page's own JS running and self-reporting. A zero-byte document has no script to execute: no
heartbeat, no fetch, no fault. **The only instrument that could report this fault is the one the
fault disables.** So it had to be detected server-side, at the read. [[the-unjoined-end]]

⚠ NO DENOMINATOR DEBATE, unlike a DOM panel. A panel can be legitimately empty ("no runs recorded
yet"), which is why console_doctor keeps three states for those. bible.html has NO legitimate
near-empty case — it is a ~6.3 MB static asset. The repo already treats this same file this way:
`_KAI_NAMES_FLOOR` refuses a name harvest below a floor precisely because "a truncated or zero-byte
bible.html does not throw". [[zero-needs-a-denominator]]

⚠ AND THE FIRST CUT OF THE HOOKUP RECORDED NOTHING, FOREVER. `ui_fault_record`'s `path=` argument
is THE FILE TO WRITE TO, not the URL being served. Passing `path="/board"` made it try to open a
file called `/board`, fail, and be swallowed by its own `except Exception: return None`. A Doctor
row that can never fire is worse than no check, because it reads as "no faults". Caught by testing
the JOIN rather than trusting it — which is the whole reason step 3 exists.
[[feedback-suspect-the-instrument]] [[join-gate-heart]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import control_app as ca

SRC = os.path.join(HERE, "control_app.py")


def _code():
    s = io.open(SRC, encoding="utf-8").read()
    s = re.sub(r'"""(?:.|\n)*?"""', " ", s)
    return re.sub(r"(?m)#.*$", " ", s)


def _serve_block():
    """The /board serve path, bound at BOTH ends — not a fixed window."""
    s = _code()
    i = s.find('with open(BIBLE, "rb") as f:')
    if i < 0:
        raise AssertionError("GUARD CANNOT GRADE: the /board serve path is gone or renamed — fix "
                             "this test before trusting any verdict it prints")
    j = s.find("self.end_headers()", i)
    return s[i:j if j > 0 else i + 3000]


class BoardShortReadIsSeen(unittest.TestCase):

    def test_the_serve_path_checks_the_LENGTH(self):
        blk = _serve_block()
        # ⚠ GRADE THE COMPARISON, NOT A MENTION. The first cut asserted the constant appeared
        # anywhere in the block — and it also appears inside the message string, so replacing the
        # whole condition with `if False:` left it GREEN. The sabotage caught it.
        self.assertRegex(blk, r"if\s+len\(\s*body\s*\)\s*<\s*_BOARD_SHORT_FLOOR",
                         "the serve path does not COMPARE the length it read against the floor "
                         "(the constant may still be mentioned in a message, which proves nothing)")
        self.assertIn("_BOARD_SHORT_FLOOR", blk,
                      "the /board serve path does not compare what it read against a floor. An "
                      "empty read does NOT raise, so a torn file is served as a normal 200 and "
                      "nothing anywhere notices")

    def test_it_reports_to_the_channel_the_DOCTOR_actually_reads(self):
        """⚠ A check nobody consumes is the defect, not the fix."""
        blk = _serve_block()
        self.assertIn("ui_fault_record(", blk,
                      "the short read is detected and not REPORTED — console_doctor reads "
                      "ui_faults_recent(24), so a fault that never reaches it is invisible")

    def test_it_does_NOT_pass_a_url_as_the_file_path(self):
        """The bug that made the first cut a permanent no-op."""
        blk = _serve_block()
        # ⚠ A NON-GREEDY `\)` STOPS AT THE FIRST CLOSE PAREN, which is inside `len(body)` — so the
        # first cut never reached the `path=` argument and the sabotage stayed green. Take the call
        # to the END OF THE STATEMENT instead of guessing where it closes.
        i = blk.find("ui_fault_record(")
        self.assertGreaterEqual(i, 0, "no ui_fault_record call to grade")
        call = blk[i:i + 800]
        call = call[:call.find("\n\n")] if "\n\n" in call else call
        self.assertNotRegex(
            call, r'path\s*=\s*[\'"]/',
            "the call passes a URL as `path=`. That argument is the FILE the recorder writes to — "
            "a URL makes the open fail, the recorder swallows it, and the row is never written. "
            "The check would read as 'no faults' forever: %s" % call[:160])

    def test_the_floor_cannot_fire_on_a_healthy_read(self):
        """A floor tuned near the real size becomes a tripwire on ordinary growth."""
        real = os.path.getsize(os.path.join(os.path.dirname(HERE), "bible.html"))
        self.assertLess(ca._BOARD_SHORT_FLOOR, real / 5.0,
                        "the floor (%d) is within 5x of the real file (%d) — ordinary growth or a "
                        "trim would trip it, and a gate that cries wolf gets ignored"
                        % (ca._BOARD_SHORT_FLOOR, real))
        self.assertGreater(ca._BOARD_SHORT_FLOOR, 100000,
                           "the floor is so low that a badly truncated file would still pass it")

    def test_it_still_SERVES_rather_than_refusing(self):
        """⚠ Refusing would turn a transient torn read into a hard outage — worse than the defect."""
        blk = _serve_block()
        after = blk[blk.find("_BOARD_SHORT_FLOOR"):]
        for bad in ("return", "self._json(5", "raise "):
            self.assertNotIn(bad, after.split("ui_fault_record")[0],
                             "the serve path bails out on a short read instead of reporting it. "
                             "A transient torn read would become a visible outage")

    def test_the_recorder_and_the_reader_really_JOIN(self):
        """Anti-vacuity: every law above is source-shaped, so one must EXECUTE end to end.

        ⚠ Runs against a SCRATCH fault log, never his. `_ui_faults_path()` is port-scoped, so this
        sets TV_CONTROL_PORT first. A test must never write a file the product is actively writing.
        [[feedback-fixtures-never-touch-live-data]]
        """
        import importlib
        old_port = os.environ.get("TV_CONTROL_PORT")
        os.environ["TV_CONTROL_PORT"] = "17994"
        try:
            importlib.reload(ca)
            p = ca._ui_faults_path()
            self.assertIn("scratch", os.path.basename(p),
                          "this test would write HIS live fault log (%s) — refusing" % p)
            try:
                ca.ui_fault_record("board-served-short", why="test", where="/board serve path")
                rows, _ = ca.ui_faults_recent(24)
                kinds = {r.get("kind") for r in rows}
                self.assertIn("board-served-short", kinds,
                              "the fault was written but the reader cannot see it — the two halves "
                              "do not join")
            finally:
                try:
                    os.remove(p)
                except Exception:
                    pass
        finally:
            if old_port is None:
                os.environ.pop("TV_CONTROL_PORT", None)
            else:
                os.environ["TV_CONTROL_PORT"] = old_port
            importlib.reload(ca)


if __name__ == "__main__":
    unittest.main(verbosity=2)
