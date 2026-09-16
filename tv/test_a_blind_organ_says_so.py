# -*- coding: utf-8 -*-
"""AN ORGAN THAT COULD NOT LOOK MUST NOT REPORT WHAT IT WOULD HAVE SEEN.

Three sites in the supervision layer turned a failed read into a confident measurement. The
swallowed-exception ratchet had been red on them across **at least ten CI runs**, back to
2026-09-15, naming all three by file and count — `74 -> 77`. The number was correct and nobody
read it, which is its own lesson about a gate whose red becomes furniture.

**1. `heart_map._read()` returned `""`.** `surfaces()` runs the id regex over that string, so an
unreadable `control_ui.html` yields an EMPTY SET — and `render()` would write, into the file the
pre-push gate compares against the tree:

    | surfaces the console paints | **0** |
    | of those, watched           | **0** |
    | coverage                    | **0.0%** |

A heart map stating the console paints nothing, **banked into the repo**, from a failed open. The
organ built to notice blindness would have gone blind in exactly the shape it exists to catch.
Measured for real: 356 surfaces, 8 watched.

**2. `shelf_corroborate._live_sessions()` returned `[]` for both "no sessions" and "could not
ask"** — and its docstring approved of it: *"or return [] with nothing invented."* Nothing IS
invented; that is the problem. A console that is down and a console with nothing on it produce the
same `checked 0, disagreed 0`, so a witness that could not be reached reads as a clean sweep.

**3. `control_app` published `blobs: [], blobsN: 0` when the grouping RAISED.** The reason did
travel in `blobsWhy`, but anything counting blobs read a confident zero from a failed call.

⚠ A WATCHER THAT CANNOT BE READ IS THE WORST OF THE THREE, because it makes every surface it
covers look UNWATCHED — a coverage collapse that reads as a real one. `watched()` now names the
missing watchers instead of silently contributing an empty string.

[[zero-needs-a-denominator]] [[unknown-stays-unknown]] [[heart-v2-instruments-watch-themselves]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import heart_map as HM
import shelf_corroborate as SC


class TestABlindOrganSaysSo(unittest.TestCase):

    # ── THE HEART MAP ────────────────────────────────────────────────────────────────────────
    def test_an_unreadable_file_is_None_and_never_empty_string(self):
        self.assertIsNone(HM._read("no_such_file_%s.html" % os.getpid()),
                          "a failed open came back as a string, which the id regex happily "
                          "reports zero matches for")

    def test_surfaces_is_UNKNOWN_when_the_console_page_cannot_be_read(self):
        real = HM._read
        HM._read = lambda name: None if name == "control_ui.html" else real(name)
        self.addCleanup(setattr, HM, "_read", real)
        self.assertIsNone(HM.surfaces(),
                          "an unreadable control_ui.html produced a LIST — and an empty list of "
                          "surfaces is a claim about his console, not a missing file")

    def test_render_REFUSES_rather_than_banking_a_zero(self):
        """★ Writing the map is what banks it: pre-push then compares HEART.md to the tree."""
        real = HM._read
        HM._read = lambda name: None if name == "control_ui.html" else real(name)
        self.addCleanup(setattr, HM, "_read", real)
        with self.assertRaises(Exception) as cm:
            HM.render()
        self.assertIn("0 surfaces", str(cm.exception),
                      "it must say WHAT it refused to claim, so the reader is not left guessing "
                      "whether the heart is empty or unreadable: %r" % str(cm.exception))

    def test_an_unreadable_WATCHER_is_named_not_skipped(self):
        """It would otherwise read as every surface that watcher covers going unwatched."""
        real = HM._read
        HM._read = lambda name: None if name == HM.WATCHERS[0] else real(name)
        self.addCleanup(setattr, HM, "_read", real)
        blob, missing = HM.watched()
        self.assertEqual(missing, [HM.WATCHERS[0]],
                         "a watcher that could not be read was silently dropped, so its coverage "
                         "vanishes and looks like a real collapse: missing=%r" % (missing,))
        ids, seen, missing2 = HM.measure()
        self.assertIsNone(ids, "measure() returned a coverage figure while a watcher was blind")

    def test_the_real_tree_still_measures(self):
        """⚠ THE BASELINE. A guard that refuses everything is as useless as one that refuses
        nothing — this proves the honest path still produces the map."""
        ids, seen, missing = HM.measure()
        self.assertEqual(missing, [], "a watcher is genuinely unreadable on this tree: %r" % missing)
        self.assertIsNotNone(ids)
        self.assertGreater(len(ids), 100,
                           "the console paints %d surfaces — that is not a measurement, that is a "
                           "broken reader" % len(ids))

    # ── THE SHELF CORROBORATOR ───────────────────────────────────────────────────────────────
    def test_a_console_that_cannot_be_asked_is_None_not_empty(self):
        real = SC.urllib if hasattr(SC, "urllib") else None
        import urllib.request
        def _boom(*a, **k):
            raise OSError("connection refused (test)")
        realopen = urllib.request.urlopen
        urllib.request.urlopen = _boom
        self.addCleanup(setattr, urllib.request, "urlopen", realopen)
        self.assertIsNone(SC._live_sessions(),
                          "an unreachable console returned a LIST — indistinguishable from a "
                          "console with no sessions, which is how a blind witness reads as clean")

    def test_the_report_says_it_could_not_ask(self):
        """★ health_engine already refuses a bare 0; what it could not do was tell WHY it was 0."""
        real = SC._live_sessions
        SC._live_sessions = lambda: None
        self.addCleanup(setattr, SC, "_live_sessions", real)
        rep = SC.report()
        self.assertTrue(rep.get("sessionsUnknown"),
                        "the report did not flag that it could not ask: %r"
                        % {k: rep.get(k) for k in ("ok", "checked", "sessionsUnknown")})
        self.assertIsNone(rep.get("ok"),
                          "an organ that could not look reported a boolean verdict — UNKNOWN is "
                          "neither ok nor not-ok: ok=%r" % rep.get("ok"))
        self.assertIn("UNKNOWN", rep.get("say") or "",
                      "the sentence a human reads must carry it too, not only a flag: %r"
                      % rep.get("say"))

    def test_a_real_empty_list_is_still_a_real_zero(self):
        """⚠ The other half: genuinely no sessions must NOT be reported as unknown."""
        rep = SC.report(sessions=[])
        self.assertFalse(rep.get("sessionsUnknown"),
                         "an explicit empty list was reported as 'could not ask' — that would "
                         "turn every honest zero into an UNKNOWN and make the flag meaningless")


if __name__ == "__main__":
    unittest.main(verbosity=2)
