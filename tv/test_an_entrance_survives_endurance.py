# -*- coding: utf-8 -*-
"""AN ENTRANCE ANIMATION SURVIVES ENDURANCE MODE — a paused fade-in is an invisible control.

⚠⚠ HIS REPORT, 2026-09-24, twice, with screenshots: "i dont see SHADOW READER toggle on or off.. for
advanced we had more options there.. something regressed", then "primary default for the AI
claude/grok toggle too i dont see it even when i restarted the console" — and "see the mouse is
hovering over areas that should have buttons and show me tooltips". The ⚙ ADVANCED header read OPEN
and the space under it was black, while hovering that black space raised the EYES card's own title.

MEASURED on real pixels (a static copy of control_ui.html in headless Chrome, never his console):
v877 made EVERY console enter endurance after 10 minutes of uptime, idle or not, and endurance sets
`animation-play-state: paused !important` on `*`. The drawer's children reveal with a one-shot
`shellReveal` whose first keyframe is opacity 0. Sessions is the console's home and #sig-adv is
display:none there, so the hop to TV·D restarts that animation, and under endurance it restarts
PAUSED AT FRAME 0: computed opacity 0, play-state paused, rect 148px tall and hit-testable. Every
tooltip he found was a real control painted at opacity 0. A restart only hid it for ten minutes.

The sweep found 23 one-shot rules whose keyframes begin at opacity 0 — the tally overlay, the run
log, the legend, the theatre, the drawer, the shelf overlay, the HD view, the AI-reads lines, the
intake hero — every one invisible if first shown after minute ten. The LAW, not the roster: every
one-shot entrance that starts invisible must be exempted from the endurance pause. A new fade-in
added without the exemption goes red here. The driven, on-pixels half is render_check's ⚙ ADVANCED
targets, which now open the drawer UNDER endurance (the state his console lives in).
[[the-green-that-lies]] [[unknown-stays-unknown]]
"""
import io
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.join(HERE, "control_ui.html")
PREFIX = 'body[data-endurance="1"] '


def _css(src):
    styles = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", src, flags=re.S))
    # bounded, so a stray `/*` inside a string cannot eat the file ([[source-reading-guard]] §3)
    return re.sub(r"/\*.{0,6000}?\*/", " ", styles, flags=re.S)


def _norm(sel):
    return re.sub(r"\s+", " ", sel).strip()


def _split(sel_list):
    return [_norm(s) for s in sel_list.split(",") if s.strip()]


def invisible_start_keyframes(css):
    """-> {name} keyframes whose FIRST frame (from / 0%) sets opacity 0."""
    out = set()
    for m in re.finditer(r"@keyframes\s+([\w-]+)\s*\{((?:[^{}]*\{[^{}]*\})*[^{}]*)\}", css):
        first = re.search(r"(?:from|0%)\s*(?:,[^{]*)?\{([^}]*)\}", m.group(2))
        if first and re.search(r"opacity\s*:\s*0(?:\.0*)?\s*(;|$)", first.group(1).strip()):
            out.add(m.group(1))
    return out


def _rules(css):
    for m in re.finditer(r"([^{}@]+)\{([^{}]*)\}", css):
        yield m.group(1), m.group(2)


def one_shot_entrances(css):
    """-> {selector} rules running an invisible-start keyframe that is NOT infinite."""
    names = invisible_start_keyframes(css)
    out = set()
    for sel, decl in _rules(css):
        for d in re.findall(r"animation(?:-name)?\s*:\s*([^;]+)", decl):
            if "infinite" in d:
                continue
            if any(re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(n), d) for n in names):
                out.update(s for s in _split(sel) if not s.startswith(PREFIX))
    return out


def endurance_exempt(css):
    """-> {selector} that endurance mode leaves RUNNING (the prefix stripped)."""
    out = set()
    for sel, decl in _rules(css):
        if not re.search(r"animation-play-state\s*:\s*running\s*!important", decl):
            continue
        for s in _split(sel):
            if s.startswith(PREFIX):
                out.add(_norm(s[len(PREFIX):]))
    return out


class AnEntranceSurvivesEndurance(unittest.TestCase):

    def setUp(self):
        with io.open(UI, encoding="utf-8") as fh:
            self.css = _css(fh.read())

    def test_the_sweep_can_see_the_drawer_he_lost(self):
        """Premise: a parser that finds nothing passes the law vacuously."""
        got = one_shot_entrances(self.css)
        print("   one-shot entrances that start at opacity 0: %d" % len(got))
        self.assertIn("details.sig-adv[open] > *:not(summary)", got,
                      "premise: the sweep no longer sees the ⚙ ADVANCED reveal it was written for")
        self.assertGreaterEqual(len(got), 20, "premise: measured 23 on 2026-09-24 — re-measure")
        self.assertIn("shellReveal", invisible_start_keyframes(self.css))

    def test_the_endurance_pause_is_still_what_it_was(self):
        """The exemption only matters while endurance pauses `*`; if that changes, re-think this."""
        self.assertIn('%s*' % PREFIX, {s for sel, d in _rules(self.css)
                                       if re.search(r"animation-play-state\s*:\s*paused", d)
                                       for s in _split(sel)})

    def test_every_invisible_start_entrance_keeps_running_under_endurance(self):
        missing = sorted(one_shot_entrances(self.css) - endurance_exempt(self.css))
        self.assertEqual(missing, [],
                         "these fade-ins would restart PAUSED AT OPACITY 0 once the console has run "
                         "10 minutes — real controls he can hover and cannot see: %s" % missing)

    def test_the_reduced_motion_door_is_not_confused_with_this_one(self):
        """prefers-reduced-motion sets `animation: none` on the drawer, which is visible; it forces
        endurance too, so it is not the path he is on and must not be the only cover."""
        self.assertIn("details.sig-adv[open] > *:not(summary)", endurance_exempt(self.css))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#228 - the ⚙ ADVANCED reveal is paused again after minute ten: the EYES switch and the shadow reader paint at opacity 0 while their tooltips still answer (his 2026-09-24 report)",
        "file": "control_ui.html",
        "find": "  body[data-endurance=\"1\"] details.sig-adv[open] > *:not(summary),\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#228 - the whole exemption is gone: every one-shot fade-in first shown after minute ten stays invisible",
        "file": "control_ui.html",
        "find": "  body[data-endurance=\"1\"] .shell { animation-play-state: running !important; }\n",
        "replace": "  body[data-endurance=\"1\"] .shell { }\n",
        "matches": 1,
    },
]
