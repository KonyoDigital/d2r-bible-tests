"""v2471 — THE PAGE MAY ONLY HIDE ITS OWN NAV WHEN SOMETHING ELSE IS PROVABLY CARRYING IT.

⚠ THE DEFECT THIS EXISTS FOR. Konyo, 2026-09-03, with a screenshot of an empty header band:
"i cant see any tabs... something is bugged". Measured on his build: `.tabs` computed
`display:none`, 0 of 19 tab buttons laid out, body carrying `app-ctx engine-driven`.

`?engine=1` is written in exactly ONE place in this repo — the `#tvd-eng` IFRAME in
tv/control_ui.html — and the rule it arms is:

    body.app-ctx.engine-driven .tabs { display:none !important }

whose own comment states the theory: "console header is the one clickable rail". True inside the
shell. Open that same URL as a top-level window and the flag still arms, the rail is not there,
and the document hides its navigation in favour of nothing. The flag was a CLAIM ABOUT CONTEXT and
nothing ever checked the context. [[the-unjoined-end]]

TWO LAWS, both pinned here, neither pinned to a number or a roster:

  1. The `engine-driven` CLASS is only added when the document is genuinely framed. Every site
     that adds it must test `window.top !== window.self`. (`ENGINE_DRIVEN` the VARIABLE is
     deliberately NOT gated — it also decides whether this page arms its own intake poll, and
     loosening that would let a top-level pane double-arm against the control process.)

  2. Every tab re-shown in app context lives in `.tabs-workshop`. `body.app-ctx .tabs-data
     {display:none}` hides the container holding `main` + the HUNT and LORE clusters, which would
     otherwise paint as empty captioned boxes. That is correct ONLY while law 2 holds — so if
     someone re-shows a data tab by name, this goes red instead of the tab silently vanishing,
     which is the exact trap the v2084 comment in bible.html warns about.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# this file prints ⚔/🪜 in its failure messages; without this it CRASHES WHILE REPORTING on a
# non-UTF-8 console, so a clean tree would exit non-zero for a reason that is not the code
from console_safe import enable  # noqa: E402

enable()
BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")
SHELL = os.path.join(HERE, "control_ui.html")


def _src():
    # anchored on __file__, never on the working directory — a zero result must be about the file
    return io.open(BIBLE, encoding="utf-8").read()


class AppCtxNav(unittest.TestCase):

    def test_engine_driven_class_requires_a_real_frame(self):
        """Every site adding the class must test window.top !== window.self."""
        src = _src()
        sites = [m for m in re.finditer(r"classList\.add\(\s*['\"]engine-driven['\"]\s*\)", src)]
        self.assertTrue(sites, "no site adds the engine-driven class — has it been renamed?")
        for m in sites:
            # read the enclosing statement/function, not a fixed character window:
            # walk back to the start of the nearest `try {` or `function` that contains it
            head = src.rfind("function ", max(0, m.start() - 2500), m.start())
            tryb = src.rfind("try {", max(0, m.start() - 2500), m.start())
            start = max(head, tryb)
            self.assertGreater(start, 0, "could not locate the scope adding engine-driven")
            scope = src[start:m.end()]
            # ⚠ FOLLOW THE CALL. The first cut of this guard read only the enclosing `try {` and
            # went red on a site that IS correct — the check lives one hop away in `engineDriven()`.
            # A guard that cannot see through a function call is measuring its own reach, not the
            # code. [[source-reading-guard]] So: inline the body of every same-file function the
            # scope calls, and judge the whole thing.
            # TRANSITIVELY — engineDriven() calls framed(), and the check is in framed().
            # One hop was not enough and the guard said so by staying red on correct code.
            seen = set()
            for _hop in range(4):
                grew = False
                for fn in set(re.findall(r"\b([A-Za-z_$][\w$]*)\s*\(\s*\)", scope)):
                    if fn in seen:
                        continue
                    d = re.search(r"function\s+%s\s*\([^)]*\)\s*\{" % re.escape(fn), src)
                    if not d:
                        continue
                    seen.add(fn)
                    i, depth = d.end(), 1
                    while i < len(src) and depth:
                        if src[i] == "{": depth += 1
                        elif src[i] == "}": depth -= 1
                        i += 1
                    scope += "\n/* inlined %s */ " % fn + src[d.end():i]
                    grew = True
                if not grew:
                    break
            self.assertRegex(
                scope, r"window\.top\s*!==\s*window\.self",
                "a site adds `engine-driven` without checking that the document is framed:\n"
                "  ...%s\n"
                "That class hides the whole tab row on the theory that the console shell's rail "
                "replaces it. Top-level there is no rail, and the page hides its nav for nothing."
                % scope[-220:].replace("\n", "\n  "))

    def test_engine_flag_is_only_ever_written_by_the_iframe(self):
        """The premise of law 1: the shell is the only writer of engine=1."""
        shell = io.open(SHELL, encoding="utf-8").read()
        writers = re.findall(r"engine=1", shell)
        self.assertTrue(writers, "the shell no longer writes engine=1 — re-derive law 1")
        for m in re.finditer(r"engine=1", shell):
            ctx = shell[max(0, m.start() - 400):m.start()]
            self.assertTrue(
                ("tvd-eng" in ctx) or ("iframe" in ctx.lower()) or ("_eng" in ctx),
                "engine=1 is now written somewhere that is not the #tvd-eng iframe:\n  ...%s"
                % ctx[-200:].replace("\n", "\n  "))

    def test_every_app_ctx_tab_is_a_workshop_tab(self):
        """Law 2 — the premise under `body.app-ctx .tabs-data{display:none}`."""
        src = _src()
        # assertTrue, not assertIn — assertIn prints the HAYSTACK, and the haystack here is a
        # 6 MB document. The first red proof of this guard emitted 6.1 MB of bible.html as its
        # failure message, which makes a real failure unreadable.
        self.assertTrue("body.app-ctx .tabs-data{display:none}" in src,
                        "the empty-cluster rule is gone; law 2 no longer guards anything")

        # every tab re-shown by name in app context
        shown = set()
        for m in re.finditer(r"body\.app-ctx\s+\.tabs\s+\.tab\[data-tab=\"([^\"]+)\"\]([^{]*)\{([^}]*)\}",
                             src):
            name, tail, body = m.group(1), m.group(2), m.group(3)
            if re.search(r"display\s*:\s*none", body):
                continue
            if re.search(r"display\s*:\s*(inline-flex|flex|block|inline-block)", body):
                shown.add(name)
            # a selector list: earlier names in the same rule share this body
            for n2 in re.findall(r"body\.app-ctx\s+\.tabs\s+\.tab\[data-tab=\"([^\"]+)\"\]", tail):
                shown.add(n2)
        self.assertTrue(shown, "no tab is re-shown in app context — the console would be empty")

        # where does each of those buttons actually LIVE in the markup?
        ws = re.search(r'<div class="tabs-workshop"(.*?)</div>\s*</div>', src, re.S)
        self.assertIsNotNone(ws, "could not find the .tabs-workshop container")
        workshop = set(re.findall(r'data-tab="([^"]+)"', ws.group(1)))
        self.assertTrue(workshop, "the workshop container holds no tabs")

        stray = sorted(shown - workshop)
        self.assertEqual(
            stray, [],
            "these tabs are re-shown in app context but do NOT live in .tabs-workshop: %s\n"
            "`body.app-ctx .tabs-data{display:none}` hides the container they sit in, so each one "
            "is built, styled, re-shown by name — and invisible. Either move the tab into the "
            "workshop row or drop that rule and hide the empty clusters individually." % stray)


if __name__ == "__main__":
    unittest.main(verbosity=2)
