# -*- coding: utf-8 -*-
"""v3291 — THE PIPELINE'S STRONGEST CLAIM MUST BE CHECKABLE.

Konyo at the pipeline board, 2026-09-18: *"pipeline though might need some updated 8 releasable?
3 not? make sure its not stale.. and its all moving along"*.

MEASURED on his console: `stages` reads `banked 3, releasable 8` — exactly the HELD BANKED 3 and
HELD DONE·AWAITING RELEASE 8 in his screenshot — across `onDisk 11` reels, `reelsUnmeasured 0`.

**The numbers were never stale.** `/api/reel_story` calls `reel_story.story()`, which re-reads
`reel_retention.plan()` on every request; nothing is cached. So his worry was not borne out.

**But the panel could not prove it, and it makes the strongest claim on the screen** — *"none of
them is free to move — every one is held, so these counts stand still by design, not by neglect"*.
Stillness-by-design and stillness-by-neglect look identical, and the board asked him to take the
difference on trust. The payload carried **no timestamp of any kind**: its keys were
`eligibleMb · hist · ok · onDisk · printerCounts · printerJoined · printerStations · printerWhy ·
reels · stages · unreadable · yield`.

"Trust me, it is current" and "measured 2s ago against 11 reels on disk" are different sentences,
and only the second one can be WRONG. [[stale-reading]]

⚠ **AN ABSENT STAMP IS UNKNOWN, NOT FRESH**, and that case is real rather than theoretical: an
older console that has not restarted still serves this panel from the module it imported, and its
payload has no `atMs`. Printing nothing there would let a reading of unknown age wear the same
face as one taken a second ago. [[zero-needs-a-denominator]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

from frame_authority import _executable_only  # noqa: E402

APP = os.path.join(ROOT, "tv", "control_app.py")
UI = os.path.join(ROOT, "tv", "control_ui.html")


class TestThePipelineReadingCarriesItsAge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = _executable_only(io.open(APP, encoding="utf-8").read(), APP)
        cls.ui = _executable_only(io.open(UI, encoding="utf-8").read(), ".js")

    def test_the_server_stamps_when_it_looked_and_at_what(self):
        self.assertIn('_story["atMs"] = int(time.time() * 1000)', self.app,
                      "the pipeline payload carries no timestamp, so its age is unknowable and "
                      "its stand-still-by-design claim cannot be checked")
        self.assertIn('_story["measuredReels"] = _story.get("onDisk")', self.app,
                      "a timestamp without a population says WHEN but not AT WHAT - both halves "
                      "are needed for the reading to mean anything")

    def test_the_panel_prints_the_age_beside_the_figures(self):
        # ⚠ re-anchored at v3292: the declaration gained a second variable, so the trailing
        # semicolon moved and the old anchor matched nothing. My own refactor rotted my own
        # assertion - the same shape the INVALID verdict exists to catch.
        self.assertIn("var _a = st.atMs,", self.ui,
                      "the panel never reads the stamp, so the server measures an age nothing "
                      "shows - built and unreachable")
        self.assertIn("' reel' + (n === 1 ? '' : 's') + ' on disk'", self.ui,
                      "the population is not said on screen, or its singular is wrong")

    def _age_clause(self):
        """The slice of the age branch itself.

        ⚠ WHY THIS IS SLICED RATHER THAN GREPPED, AND IT IS NOT FASTIDIOUSNESS. The first cut of
        this law asserted "this reading carries no " and "UNKNOWN</div>" against the WHOLE file.
        Both phrases occur **three times** — other panels share the idiom — so the assertions were
        satisfied by two unrelated sites and the law never pinned this branch at all. Its
        red-proof came back BLIND: the sabotage matched exactly once, deleted this clause, and the
        law stayed GREEN. The match count is what exposed it.
        [[presence-law-vs-reachability-law]] [[source-reading-guard]]
        """
        i = self.ui.find("var _a = st.atMs,")
        self.assertGreater(i, -1, "the age branch vanished")
        j = self.ui.find("})()", i)
        self.assertGreater(j, i, "the age branch has no end anchor")
        return self.ui[i:j]

    def test_a_missing_stamp_reads_as_UNKNOWN_and_not_as_fresh(self):
        """The case that actually happens: an un-restarted console serving the old payload."""
        clause = self._age_clause()
        self.assertIn("this reading carries no ", clause,
                      "an absent timestamp prints nothing HERE, so a reading of unknown age looks "
                      "exactly like one taken a second ago")
        self.assertIn("UNKNOWN</div>", clause,
                      "it must say UNKNOWN in the word he recognises, not merely omit the age")
        self.assertIn("if (_txt == null)", clause,
                      "there is no branch for the unusable stamp at all, so the UNKNOWN wording "
                      "below it can never be reached")


    def test_the_age_is_re_said_on_a_tick_so_it_cannot_itself_go_stale(self):
        """v3292, raised by the cross-family eye on v3291 — and it is the sharpest of the three.

        `_shStoryRender` runs once per shelf open. The only other callers of `thShelf()` are
        event-driven — a dossier note edit, an art-map repaint — so leaving the shelf open two
        minutes left it still reading "measured just now". **A staleness warning that goes stale
        is worse than none, because it is believed.** [[stale-reading]]
        """
        self.assertIn("window._shAgeTick = function ()", self.ui,
                      "nothing re-says the age, so it freezes at whatever it was when the panel "
                      "was opened")
        self.assertIn("setInterval(window._shAgeTick", self.ui,
                      "the tick exists and nothing runs it")
        self.assertIn("data-at=", self.ui,
                      "the stamp does not ride on the element, so the tick would have to re-fetch "
                      "to know what it is re-saying")
        self.assertIn("ov.hidden) return", self.ui,
                      "the tick must do nothing while the shelf is closed - a timer that works "
                      "when nobody is looking is a cost with no reader")

    def test_a_skewed_or_malformed_stamp_reads_UNKNOWN_rather_than_a_wrong_number(self):
        """Also raised on v3291. The console binds 0.0.0.0, so a second machine can hold this
        panel open against a clock that disagrees; and `if (!_a)` let the JSON string through,
        which rendered "measured NaNs ago"."""
        i = self.ui.find("window._shAgeText = function (a, n)")
        self.assertGreater(i, -1, "the age wording is not in one place, so the render and the "
                                  "tick can drift into two dialects")
        body = self.ui[i:self.ui.find("};", i)]
        self.assertIn("typeof a !== 'number' || !isFinite(a) || a <= 0", body,
                      "a string or a zero takes the good branch and renders NaN")
        self.assertIn("if (s < -5) return null", body,
                      "a client clock behind the server's renders a negative age as though it "
                      "were a measurement")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "without the stamp the board's stand-still claim goes back to being unfalsifiable",
        "file": "tv/control_app.py",
        "find": '                _story["atMs"] = int(time.time() * 1000)',
        "replace": "                pass",
        "matches": 1,
    },
    {
        "why": "a panel that does not read the stamp leaves the server measuring for nobody",
        "file": "tv/control_ui.html",
        # ⚠ RE-ANCHORED AT v3292, AND BY THE GUARD THIS VERSION SHIPS. The declaration gained a
        # second variable, so `var _a = st.atMs;` matched nothing and this proof went INVALID —
        # which until v3292 exited 0 and would have read as success. It was caught because the
        # same commit made an inert proof fail. Third rotted anchor in this one law today.
        "find": "              var _a = st.atMs, _n = (st.measuredReels != null) ? st.measuredReels : null;",
        "replace": "              var _a = 1, _n = null;",
        "matches": 1,
    },
    {
        "why": "without the tick the freshness line freezes and keeps saying just now for minutes",
        "file": "tv/control_ui.html",
        "find": "  try { setInterval(window._shAgeTick, 15000); } catch (e) {}",
        "replace": "  try { void 0; } catch (e) {}",
        "matches": 1,
    },
    {
        "why": "dropping the type guard renders a JSON string stamp as measured NaNs ago",
        "file": "tv/control_ui.html",
        "find": "    if (typeof a !== 'number' || !isFinite(a) || a <= 0) return null;",
        "replace": "    if (!a) return null;",
        "matches": 1,
    },
    {
        "why": "printing nothing for an absent stamp lets unknown age wear the face of fresh",
        "file": "tv/control_ui.html",
        "find": "                return '<div class=\"shs-ysub shs-age shs-age-unk\">\\u26a0 this reading carries no '",
        "replace": "                return '<div class=\"shs-ysub shs-age shs-age-unk\">' + '' + (''",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
