"""A WELD JOINS A FIGURE TO ITS NOUN — IT MUST NEVER SHOW A WORD TWICE.

⚠⚠ MEASURED 2026-09-10 (#68), and it was LATENT, which is the whole reason this gate exists.
`_weld()` in the HEART's instruments header keeps a number from ending a line without the word that
says what it counts. It does that by wrapping the FIRST TWO and the LAST TWO words of a clause in
`.hrt-nw`, leaving the middle to wrap freely. For a three-word clause those two windows OVERLAP at
index 1, and the middle word was emitted by both:

    'a b c'  ->  <span>a b</span> <span>b c</span>      the reader meets `b` TWICE

No clause in the panel is three words TODAY — the live ones are 2, 6 and 8 — so every render was
green and every photograph was correct. That is exactly how this ships: the defect waits for the
first three-word phrase anyone writes, and the person who writes it has no reason to suspect the
helper. [[label-outlived-referent]] [[visual-regression-detector]]

⚠ THE LAW IS ARITHMETIC, NOT PROSE. A gate that greps for `w.length <= 3` passes the day someone
changes the slice widths and forgets the guard. What must hold is a RELATION between three numbers
this file actually parses out of the source: the head width, the tail width, and the guard. Two
windows of width H and T over N words overlap exactly when H + T > N, so the whole-string branch
must cover every N where that is true — i.e. `guard >= head + tail - 1`.
[[source-reading-guard]] [[sabotage-is-usually-the-wrong-one]]
"""
import io
import os
import re
import shutil
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.join(HERE, "control_ui.html")


def _between(src, start, end):
    """The text between two ANCHORS, both of which must be found. -> str

    ⚠ Anchored at BOTH ends on purpose. A fixed-size window (`src[i:i+400]`) reads a region that
    has moved as ABSENT, and this repo has lost measurements to that four times in one session.
    [[source-window-shortcut]]
    """
    i = src.index(start)
    j = src.index(end, i + len(start))
    return src[i:j + len(end)]


def _weld_source():
    src = io.open(UI, encoding="utf-8").read()
    return _between(src, "var _weld = function(t){", "};")


class AWeldNeverRepeatsAWord(unittest.TestCase):

    def test_the_helper_is_still_there_and_this_gate_found_it(self):
        """⚠ THE REACH CHECK FIRST. If `_weld` were renamed, every law below would read an empty
        string and pass for the wrong reason — a gate that cannot find its subject must fail, not
        go quiet. [[source-reading-guard]] [[feedback-silence-is-not-evidence]]"""
        body = _weld_source()
        self.assertGreater(len(body), 80,
                           "_weld's body came back at %d chars — this gate did not reach its "
                           "subject, so its silence is not evidence" % len(body))
        self.assertIn("slice", body, "_weld no longer slices — the law below is about a shape "
                                     "that has changed, and it must be re-derived, not assumed")

    def test_the_whole_string_guard_covers_every_overlapping_length(self):
        """The one law. Head window H, tail window T, whole-string guard G, all three read out of
        the source as NUMBERS. Two windows overlap whenever H + T > N, so G must be at least
        H + T - 1 or some N slips past the guard into the two-window branch and repeats a word."""
        body = _weld_source()

        m_head = re.search(r"slice\(\s*0\s*,\s*(\d+)\s*\)", body)
        m_tail = re.search(r"slice\(\s*-\s*(\d+)\s*\)", body)
        m_guard = re.search(r"w\.length\s*<=\s*(\d+)", body)
        self.assertIsNotNone(m_head, "no `slice(0, N)` head window found in _weld — UNKNOWN, "
                                     "not passing")
        self.assertIsNotNone(m_tail, "no `slice(-N)` tail window found in _weld — UNKNOWN, "
                                     "not passing")
        self.assertIsNotNone(m_guard, "no `w.length <= N` whole-string guard found in _weld — "
                                      "without one, EVERY overlapping length repeats a word")

        head, tail, guard = int(m_head.group(1)), int(m_tail.group(1)), int(m_guard.group(1))
        need = head + tail - 1
        self.assertGreaterEqual(
            guard, need,
            "the whole-string guard is `w.length <= %d`, but the head window is %d words and the "
            "tail window is %d, so they OVERLAP for every clause of %d words or fewer. A clause of "
            "%d words takes the two-window branch and emits word index %d twice. The guard must be "
            "at least %d." % (guard, head, tail, need, guard + 1 if guard + 1 <= need else need,
                              head - 1, need))

    @unittest.skipIf(shutil.which("node") is None,
                     "node is absent — the behavioural half is UNMEASURED, not passing. The "
                     "arithmetic law above still ran.")
    def test_every_clause_length_round_trips_to_its_own_words(self):
        """⚠ THE ARITHMETIC LAW IS THE ONE THAT CANNOT DRIFT, BUT IT IS STILL A CLAIM ABOUT SOURCE.
        This runs the real helper and asserts the only thing a reader cares about: the words that
        come out are the words that went in, in order, exactly once each. Proves the law is about
        BEHAVIOUR and not about how the source happens to be spelled."""
        body = _weld_source()
        js = """
        var _hrtEsc = function(s){ return String(s); };
        %s
        var bad = [];
        for (var n = 1; n <= 14; n++) {
          var w = []; for (var i = 0; i < n; i++) w.push("w" + i);
          var t = w.join(" ");
          var plain = _weld(t).replace(/<[^>]*>/g, "");
          if (plain !== t) bad.push(n + ": " + JSON.stringify(plain) + " != " + JSON.stringify(t));
        }
        console.log(bad.length ? "BAD " + bad.join(" | ") : "OK 14");
        """ % body
        r = subprocess.run([shutil.which("node"), "-e", js],
                           capture_output=True, text=True, timeout=60)
        out = (r.stdout or "").strip()
        self.assertEqual(r.returncode, 0,
                         "node could not run _weld — UNKNOWN, not passing: %s"
                         % (r.stderr or "")[:400])
        self.assertTrue(out.startswith("OK"),
                        "a weld changed the text it was given. Every clause length 1..14 must come "
                        "back as its own words, once each, in order: %s" % out[:600])
        self.assertEqual(out, "OK 14",
                         "the behavioural sweep did not report all 14 lengths — %r. A partial "
                         "sweep is not a verdict." % out)


RED_PROOF = [
    {
        "why": "restoring the overlap: with the guard back at 2, a three-word clause takes the "
               "two-window branch and `slice(0,2)`/`slice(-2)` both emit index 1, so the middle "
               "word is rendered twice. This is the exact defect measured on 2026-09-10.",
        "file": "control_ui.html",
        "find": "      if (w.length <= 3) return '<span class=\"hrt-nw\">' + _hrtEsc(t) + '</span>';",
        "replace": "      if (w.length <= 2) return '<span class=\"hrt-nw\">' + _hrtEsc(t) + '</span>';",
        "matches": 1,
    },
    {
        "why": "widening the head window to 3 without moving the guard re-opens the overlap at "
               "four words — proving the law is the RELATION between the three numbers and not a "
               "hardcoded 3.",
        "file": "control_ui.html",
        "find": "_hrtEsc(w.slice(0, 2).join(' '))",
        "replace": "_hrtEsc(w.slice(0, 3).join(' '))",
        "matches": 1,
    },
    {
        "why": "removing the whole-string guard entirely: without it EVERY short clause takes the "
               "two-window branch, and the reach check plus the arithmetic law must both refuse.",
        "file": "control_ui.html",
        "find": "if (w.length <= 3) return '<span class=\"hrt-nw\">' + _hrtEsc(t) + '</span>';",
        "replace": "if (false) return '';",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
