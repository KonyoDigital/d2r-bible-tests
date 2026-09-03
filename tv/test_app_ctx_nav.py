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


#: Every way JavaScript can put a class on an element. The point of the list is that the guard
#: must not be tied to ONE of them — that was the hole the v2471 review walked straight through.
_WRITE_SHAPES = (
    (r"classList\s*\.\s*add\s*\([^)]*['\"]engine-driven['\"]", "classList.add"),
    (r"classList\s*\.\s*toggle\s*\([^)]*['\"]engine-driven['\"]", "classList.toggle"),
    (r"className\s*\+?=\s*[^;]*engine-driven", "className assignment"),
    (r"setAttribute\s*\(\s*['\"]class['\"][^)]*engine-driven", "setAttribute('class')"),
    (r"classList\s*\[[^\]]*\]\s*\([^)]*['\"]engine-driven['\"]", "classList[computed]"),
)


def _script_regions(src):
    """(start, end) of every inline <script> body — the class literal also lives in CSS."""
    out = []
    for m in re.finditer(r"<script\b[^>]*>", src):
        end = src.find("</script>", m.end())
        if end > 0:
            out.append((m.end(), end))
    return out


def _class_write_sites(src):
    """-> [(pos, how)] every JS site that WRITES the engine-driven class, by any mechanism."""
    regions = _script_regions(src)
    sites = []
    for pat, how in _WRITE_SHAPES:
        for m in re.finditer(pat, src):
            if any(a <= m.start() < b for a, b in regions):
                sites.append((m.start(), how))
    return sorted(set(sites))


def _controlling_condition(src, pos):
    """The condition that decides whether the write at `pos` happens. -> str | None

    Two shapes carry a condition: an `if (...)` whose body contains the write, and
    `classList.toggle(name, <expr>)` whose second argument IS the condition. Anything else is
    unconditional, which is itself the finding.
    """
    line_start = src.rfind("\n", 0, pos) + 1
    stmt_start = max(src.rfind(";", 0, pos), src.rfind("{", 0, pos), line_start - 1) + 1
    stmt = src[stmt_start:src.find(";", pos) + 1 if src.find(";", pos) > 0 else pos]

    m = re.search(r"\bif\s*\(", stmt)
    if m:
        i, depth = m.end(), 1
        while i < len(stmt) and depth:
            if stmt[i] == "(":
                depth += 1
            elif stmt[i] == ")":
                depth -= 1
            i += 1
        return stmt[m.end():i - 1]

    t = re.search(r"classList\s*\.\s*toggle\s*\(\s*['\"]engine-driven['\"]\s*,", stmt)
    if t:
        i, depth = t.end(), 1
        while i < len(stmt) and depth:
            if stmt[i] == "(":
                depth += 1
            elif stmt[i] == ")":
                depth -= 1
            i += 1
        return stmt[t.end():i - 1]
    return None


#: Identifiers never worth following: globals, and names so common that resolving them drags the
#: whole document in. Following them cost 87 seconds against a 120-second gate — a pass that close
#: to its own timeout is a flake waiting for a slower runner.
_NOFOLLOW = frozenset((
    "window", "document", "location", "body", "self", "top", "search", "test", "e", "a", "b", "c",
    "i", "j", "k", "n", "s", "t", "v", "x", "y", "true", "false", "null", "undefined", "var",
    "let", "const", "function", "return", "if", "else", "try", "catch", "typeof", "new", "this",
    "String", "Number", "Boolean", "Object", "Array", "JSON", "Math", "classList", "className",
))


def _resolve(src, expr, hops=4):
    """Inline what the expression READS: same-file functions it calls, and vars it names.

    ⚠ Only identifiers the CONDITION actually references are followed. That is the whole point:
    a `var _framed = window.top !== window.self` left behind as a dead variable is not read by
    the condition, so it is never inlined, and the guard stays red — which is the regression the
    v2471 review reproduced against the previous version of this check.
    """
    # SEARCH THE SCRIPT BODIES, NOT THE 6 MB DOCUMENT. The class literal only ever appears in JS;
    # scanning the stylesheet and 45k lines of markup for every identifier is what made this slow.
    hay = "\n".join(src[a:b] for a, b in _script_regions(src)) or src
    seen, out = set(), expr
    for _ in range(hops):
        grew = False
        if len(seen) >= 40:      # a bounded walk; an unbounded one is how a gate becomes a hang
            break
        for ident in set(re.findall(r"\b([A-Za-z_$][\w$]*)\b", out)):
            if ident in seen or ident in _NOFOLLOW or len(ident) < 2:
                continue
            d = re.search(r"function\s+%s\s*\([^)]*\)\s*\{" % re.escape(ident), hay)
            if d:
                i, depth = d.end(), 1
                while i < len(hay) and depth:
                    if hay[i] == "{":
                        depth += 1
                    elif hay[i] == "}":
                        depth -= 1
                    i += 1
                seen.add(ident)
                out += "\n/* fn %s */ " % ident + hay[d.end():i]
                grew = True
                continue
            # ⚠ EVERY ASSIGNMENT, NOT THE FIRST. The real code declares `var _framed = true;` and
            # then REASSIGNS it inside a try: `_framed = (window.top !== window.self)`. Taking
            # only the declaration resolved the condition to the literal `true` and the guard went
            # red on correct code — its own reach again, one hop further out than last time.
            hits = re.findall(r"\b%s\s*=\s*([^;\n]+)" % re.escape(ident), hay)
            if hits:
                seen.add(ident)
                for h in hits[:8]:
                    out += "\n/* = %s */ " % ident + h
                grew = True
        if not grew:
            break
    return out


class AppCtxNav(unittest.TestCase):

    def test_engine_driven_class_requires_a_real_frame(self):
        """Every site that puts `engine-driven` on the body must be gated on a REAL frame.

        ⚠⚠ THIS TEST WAS DEFEATED TWICE BY THE v2471 REVIEW, BOTH REPRODUCED ON COPIES, AND BOTH
        HOLES ARE THE SAME MISTAKE: it measured its own reach instead of the code.

          1. ITS DETECTOR SAW ONE CALL SHAPE. It matched the literal
             `classList.add('engine-driven')`, so rewriting a site to
             `classList.toggle('engine-driven', <test>)`, to `className += ' engine-driven'`, or
             even to `classList.add('engine-driven','x')` — two arguments defeat the `\s*\)`
             tail — made that site INVISIBLE to it. Measured: the module went green with REG-443
             restored and a top-level board back to 0 of 19 tabs.
          2. ITS ASSERTION CHECKED PRESENCE, NOT CONTROL. It asked whether the framing test
             appeared anywhere in the enclosing scope. Leaving `var _framed = window.top !==
             window.self` in place as a DEAD VARIABLE while dropping `&& _framed` from the
             condition — the most ordinary kind of regression — also passed.

        So it now finds every WRITE of the class by any mechanism, and requires the framing test
        inside the CONTROLLING CONDITION of each: resolved transitively through same-file function
        calls AND through local `var x = …` assignments, so a variable only counts when the
        condition actually reads it. [[source-reading-guard]] [[regression-guard]]

        ⚠ A source guard can always be out-refactored. `tests/v2473_engine_driven_nav.spec.ts`
        asserts the same law BEHAVIOURALLY on a rendered page, and that one cannot be.
        """
        src = _src()
        sites = _class_write_sites(src)
        self.assertTrue(
            sites,
            "no site writes the engine-driven class by any mechanism this guard knows. Either it "
            "was removed — in which case the CSS that reads it is now dead — or it is written a "
            "way this detector cannot see, which is the hole the v2471 review reproduced.")
        for pos, how in sites:
            cond = _controlling_condition(src, pos)
            self.assertIsNotNone(
                cond,
                "a site writes engine-driven (%s) with no controlling condition at all — it is "
                "applied unconditionally, so a top-level board hides its own tab row." % how)
            resolved = _resolve(src, cond)
            self.assertRegex(
                resolved, r"window\.top\s*!==\s*window\.self",
                "a site writes `engine-driven` (%s) whose controlling condition does not test "
                "that the document is framed:\n    %s\nThat class hides the whole tab row on the "
                "theory that the console shell's rail replaces it. Top-level there is no rail, "
                "and the page hides its nav for nothing. (Condition resolved through calls and "
                "local assignments; a dead `_framed` variable the condition never reads does not "
                "count.)" % (how, cond.strip()[:200]))

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
