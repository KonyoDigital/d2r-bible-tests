# -*- coding: utf-8 -*-
"""v3397 — `hidden` must actually hide.

`[hidden] { display: none }` comes from the USER-AGENT stylesheet. Author rules beat UA rules
regardless of specificity, so ANY author `display:` on the same element silently defeats the
attribute: the JS sets it, the element stays laid out, and the source and the screen disagree.

⚠ THIS HAS NOW COST HIM TWICE, AND HE FOUND IT BOTH TIMES.
  v2443 — `button.act`: "hidden DID NOTHING HERE, AND HE IS THE ONE WHO NOTICED". It fixed the one
          element, wrote the law into a comment naming four earlier instances, and shipped NO GATE.
  v3271 — `.win-ctl { display: inline-flex }`, added beside a `hidden` attribute by me. His window
          controls have rendered ever since whether or not they can act, which the JS beside them
          calls "worse than no button". He asked for that control a THIRD time on 2026-09-20.

A law written in a comment is a law with nothing enforcing it. This is that law, executable.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# ⚠ THIS FILE PRINTS ITS FINDINGS, AND THEY CARRY A WARNING SIGN AND BACKTICKED SELECTORS. On a
# cp1255 console that crashes WHILE REPORTING, so a clean tree exits non-zero for a reason that
# has nothing to do with the check — and his Windows box is exactly such a console. The pre-push
# gate refused this file for precisely that, which is the gate doing its job, and it is the same
# class as the cp1255 failure that cost four green-looking pushes earlier today.
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import console_doctor as cd

UI = os.path.join(HERE, "control_ui.html")

RED_PROOF = [
    {
        "why": "dropping .win-ctl from the guard block restores v3271 exactly - his window "
               "buttons render on a console that has no window to act on",
        "file": "tv/control_ui.html",
        "find": "  .win-ctl[hidden], .chron-run[hidden], .chron-visits[hidden], .fb-eta[hidden],",
        "replace": "  .chron-run[hidden], .chron-visits[hidden], .fb-eta[hidden],",
        "matches": 1,
    },
    {
        "why": "with comment stripping off, a guard that exists only inside a comment is credited "
               "as real - measured on this file, chron-waiting is guarded by prose and nothing else",
        "file": "tv/console_doctor.py",
        "find": "    STRIP_COMMENTS = True",
        "replace": "    STRIP_COMMENTS = False",
        "matches": 1,
    },
    {
        "why": "without subject-awareness a rule on a CHILD is read as a rule on the hidden "
               "PARENT, which a hidden parent already suppresses - 10 offenders where there are 7",
        "file": "tv/console_doctor.py",
        "find": "    def _subject(part):",
        "replace": "    def _subject(part):\n        return part.strip()",
        "matches": 1,
    },
]


def _page(css, body):
    return "<html><style>%s</style>%s</html>" % (css, body)


class TestAHiddenElementIsActuallyHidden(unittest.TestCase):

    def test_the_scanner_can_see_a_planted_offender(self):
        """BASELINE. A case that cannot fail is measuring the fixture, not the rule."""
        bad = cd.defeated_hidden(_page(".w { display: inline-flex; }",
                                       '<span class="w" hidden>x</span>'))
        self.assertIn("w", bad,
                      "the scanner cannot see an author display rule defeating `hidden`, so "
                      "every other case in this file is vacuous")

    def test_a_guard_clears_it(self):
        bad = cd.defeated_hidden(_page(".w { display: inline-flex; } .w[hidden] { display: none !important; }",
                                       '<span class="w" hidden>x</span>'))
        self.assertEqual(bad, {}, "a real `[hidden]` guard must clear the offender")

    def test_a_rule_on_a_child_is_not_an_offender(self):
        """`.bar > i` styles the i. A hidden PARENT already suppresses its children."""
        bad = cd.defeated_hidden(_page(".bar > i { display: block; }",
                                       '<div class="bar" hidden><i>x</i></div>'))
        self.assertEqual(bad, {}, "a rule whose SUBJECT is a child was counted against the "
                                  "parent - that is the instrument, not the file")

    def test_a_guard_that_exists_only_in_a_comment_is_not_credited(self):
        """The §4b trap, and it is measured on the real file: `chron-waiting`'s only guard is prose."""
        css = "/* .w[hidden] { display: none !important; } */ .w { display: flex; }"
        bad = cd.defeated_hidden(_page(css, '<span class="w" hidden>x</span>'))
        self.assertIn("w", bad,
                      "a guard quoted inside a COMMENT was credited as a real rule - a scanner "
                      "that reads its own documentation is lenient in the quiet direction")

    def test_the_live_console_file_has_no_defeated_hidden(self):
        """THE LAW."""
        bad = cd.defeated_hidden(io.open(UI, encoding="utf-8").read())
        self.assertEqual(
            bad, {},
            "%d element(s) carry `hidden` while an author display rule keeps them laid out: %s. "
            "Add `<selector>[hidden] { display: none !important; }`."
            % (len(bad), ", ".join("%s (%s)" % (k, sorted(v)[0]) for k, v in sorted(bad.items()))))

    def test_the_window_control_can_hide_itself(self):
        """#win-ctl specifically - the one he reported three times."""
        src = io.open(UI, encoding="utf-8").read()
        self.assertIn(".win-ctl[hidden]", src,
                      "his window controls cannot hide, so the probe's `box.hidden = false` "
                      "decides nothing and the buttons show on a console with no window")

    def test_every_guard_is_important_so_a_later_rule_cannot_re_defeat_it(self):
        """Order-independence: `!important` beats any non-important author rule, wherever it sits."""
        src = io.open(UI, encoding="utf-8").read()
        css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", src, re.S))
        css = re.sub(r"/\*.{0,4000}?\*/", lambda m: "\n" * m.group(0).count("\n"), css, flags=re.S)
        weak = []
        for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
            sel, body = m.group(1).strip(), m.group(2)
            if "[hidden]" not in sel:
                continue
            d = re.search(r"display\s*:\s*none\s*([^;}]*)", body)
            if d and "!important" not in d.group(0):
                weak.append(sel[:50])
        # ⚠ A RATCHET AT THE MEASURED COUNT, WHICH MAY ONLY FALL - never a guessed ceiling.
        # Measured 2026-09-20: 38 `[hidden]` guards carry display:none, 16 of them without
        # !important. Those 16 are NOT broken today (defeated_hidden reports 0 offenders, so
        # each one currently wins on order or specificity) - they are ORDER-DEPENDENT, and a
        # later author rule re-defeats them with nothing to say so. The first draft of this
        # line guessed 23, which would have permitted 7 new fragile guards while reading green.
        # [[feedback-threshold-above-the-ceiling]] [[regression-guard]]
        self.assertLessEqual(
            len(weak), 16,
            "%d `[hidden]` guard(s) omit !important, so a later author rule re-defeats them "
            "silently: %s" % (len(weak), weak[:5]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
