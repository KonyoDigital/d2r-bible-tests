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
import sys
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
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


def _blocks(css):
    """-> [(context, prelude, body, kind)] for every style rule and every @keyframes, where `context` is
    the tuple of enclosing at-rule preludes (@media / @supports). Brace-MATCHED, never regexed.

    ⚠⚠ THE SECOND EYE ON v3493 (grok-4.7), reproduced on crafted CSS before this was written: the
    regex helpers threw the @media condition away (an exemption living only under prefers-reduced-
    motion read as cover for everyone), read `0%` inside `100%` as the first frame (a reveal written
    100%-first went unseen - a false green), skipped a whole `animation:` value when `infinite`
    appeared ANYWHERE in it (a one-shot beside an infinite ambient layer escaped the law), ignored
    `animation-iteration-count: infinite`, and dropped any entrance written on an already-prefixed
    selector. [[source-reading-guard]]"""
    out = []

    def walk(text, ctx):
        i, n = 0, len(text)
        while i < n:
            j = text.find("{", i)
            if j < 0:
                return
            prelude = text[i:j].split(";")[-1].split("}")[-1].strip()
            depth, k = 1, j + 1
            while k < n and depth:
                if text[k] == "{":
                    depth += 1
                elif text[k] == "}":
                    depth -= 1
                k += 1
            body = text[j + 1:k - 1]
            if re.match(r"@(?:-webkit-)?keyframes\b", prelude):
                out.append((ctx, prelude, body, "keyframes"))
            elif prelude.startswith("@"):
                walk(body, ctx + (_norm(prelude),))
            else:
                out.append((ctx, prelude, body, "rule"))
            i = k

    walk(css, ())
    return out


def _decls(body):
    """-> {property: value}, the LAST declaration winning (the cascade inside one rule)."""
    d = {}
    for part in body.split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            d[k.strip().lower()] = v.strip()
    return d


def _layers(value):
    """Split a comma list at TOP level: cubic-bezier(.2,.8,.2,1) is one token, not four."""
    out, depth, cur = [], 0, ""
    for ch in value:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def invisible_start_keyframes(css):
    """-> {name} keyframes whose FIRST frame (`from` / `0%`, as a whole selector token) sets opacity 0."""
    out = set()
    for ctx, prelude, body, kind in _blocks(css):
        if kind != "keyframes":
            continue
        name = prelude.split(None, 1)[1].strip() if len(prelude.split(None, 1)) > 1 else ""
        first = {}
        for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", body):
            frames = [f.strip().lower() for f in m.group(1).split(",")]
            if "from" in frames or "0%" in frames:
                first.update(_decls(m.group(2)))
        op = first.get("opacity")
        if op is not None and re.match(r"^0(?:\.0*)?(?:\s*!important)?$", op.strip()):
            out.add(name)
    return out


def _one_shot_layers(decls, names):
    """-> True when this rule runs an invisible-start keyframe as a ONE-SHOT layer."""
    if "animation" in decls:
        for layer in _layers(decls["animation"]):
            toks = layer.split()
            if any(t in names for t in toks) and "infinite" not in toks:
                return True
        return False
    if "animation-name" in decls:
        nm = _layers(decls["animation-name"])
        it = _layers(decls.get("animation-iteration-count", "1")) or ["1"]
        for i, n in enumerate(nm):
            if n in names and it[i % len(it)].strip() != "infinite":
                return True
    return False


def _unprefixed(sel):
    return _norm(sel[len(PREFIX):]) if sel.startswith(PREFIX) else sel


def one_shot_entrances(css):
    """-> {(context, selector)} rules running an invisible-start keyframe that is NOT infinite. The
    selector is given WITHOUT the endurance prefix, so an entrance written on an already-prefixed
    selector is still an entrance - the `*` pause still reaches it."""
    names = invisible_start_keyframes(css)
    out = set()
    for ctx, prelude, body, kind in _blocks(css):
        if kind != "rule":
            continue
        d = _decls(body)
        if _one_shot_layers(d, names):
            self_exempt = bool(re.search(r"running\s*!important", d.get("animation-play-state", "")))
            for sel in _split(prelude):
                if not (self_exempt and sel.startswith(PREFIX)):
                    out.add((ctx, _unprefixed(sel)))
    return out


def endurance_exempt(css):
    """-> {(context, selector)} that endurance mode leaves RUNNING (the prefix stripped)."""
    out = set()
    for ctx, prelude, body, kind in _blocks(css):
        if kind != "rule":
            continue
        if not re.search(r"running\s*!important", _decls(body).get("animation-play-state", "")):
            continue
        for sel in _split(prelude):
            if sel.startswith(PREFIX):
                out.add((ctx, _unprefixed(sel)))
    return out


def uncovered(css):
    """-> sorted entrances with no exemption that applies WHEREVER they apply: an unconditional
    exemption covers every context; a conditional one covers only its own context."""
    ex = endurance_exempt(css)
    return sorted("%s%s" % ((" @ ".join(ctx) + " :: ") if ctx else "", sel)
                  for ctx, sel in one_shot_entrances(css)
                  if ((), sel) not in ex and (ctx, sel) not in ex)


class AnEntranceSurvivesEndurance(unittest.TestCase):

    def setUp(self):
        with io.open(UI, encoding="utf-8") as fh:
            self.css = _css(fh.read())

    def test_the_sweep_can_see_the_drawer_he_lost(self):
        """Premise: a parser that finds nothing passes the law vacuously."""
        got = one_shot_entrances(self.css)
        print("   one-shot entrances that start at opacity 0: %d" % len(got))
        self.assertIn(((), "details.sig-adv[open] > *:not(summary)"), got,
                      "premise: the sweep no longer sees the ⚙ ADVANCED reveal it was written for")
        self.assertGreaterEqual(len(got), 29, "premise: measured 29 on 2026-09-24 (walker) - re-measure")
        self.assertIn("shellReveal", invisible_start_keyframes(self.css))

    def test_the_endurance_pause_is_still_what_it_was(self):
        """The exemption only matters while endurance pauses `*`; if that changes, re-think this."""
        paused = {sel for ctx, pre, body, kind in _blocks(self.css) if kind == "rule" and not ctx
                  and re.search(r"paused", _decls(body).get("animation-play-state", ""))
                  for sel in _split(pre)}
        self.assertIn("%s*" % PREFIX, paused)

    def test_every_invisible_start_entrance_keeps_running_under_endurance(self):
        missing = uncovered(self.css)
        self.assertEqual(missing, [],
                         "these fade-ins would restart PAUSED AT OPACITY 0 once the console has run "
                         "10 minutes - real controls he can hover and cannot see: %s" % missing)

    def test_the_reduced_motion_door_is_not_confused_with_this_one(self):
        """prefers-reduced-motion sets `animation: none` on the drawer, which is visible; it forces
        endurance too, so it is not the path he is on and must not be the only cover."""
        self.assertIn(((), "details.sig-adv[open] > *:not(summary)"), endurance_exempt(self.css),
                      "the drawer's exemption is not unconditional")


class TheHelpersReadCSSTheWayTheBrowserDoes(unittest.TestCase):
    """The second eye on v3493 (grok-4.7): each case below was REPRODUCED on the regex helpers first."""

    def test_the_first_frame_is_a_whole_token_not_a_substring(self):
        self.assertIn("rev", invisible_start_keyframes(
            "@keyframes rev { 100% { opacity: 1 } 0% { opacity: 0 } }"),
            "a reveal written 100%-first went unseen (0% read inside 100%)")
        self.assertNotIn("fo", invisible_start_keyframes(
            "@keyframes fo { 100% { opacity: 0 } 0% { opacity: 1 } }"),
            "a fade-OUT written 100%-first was taken for an invisible start")

    def test_a_one_shot_beside_an_infinite_layer_is_still_a_one_shot(self):
        css = ("@keyframes rev { from { opacity: 0 } to { opacity: 1 } } "
               ".c { animation: rev .4s cubic-bezier(.2,.8,.2,1), amb 8s linear infinite; }")
        self.assertEqual(one_shot_entrances(css), {((), ".c")})

    def test_an_iteration_count_of_infinite_is_not_a_one_shot(self):
        css = "@keyframes rev { from { opacity: 0 } } .d { animation-name: rev; animation-iteration-count: infinite; }"
        self.assertEqual(one_shot_entrances(css), set())

    def test_an_exemption_under_a_media_query_covers_only_that_query(self):
        css = ("@keyframes rev { from { opacity: 0 } } .e { animation: rev .4s; } "
               "@media (prefers-reduced-motion: reduce) { %s.e { animation-play-state: running !important; } }" % PREFIX)
        self.assertEqual(uncovered(css), [".e"], "a reduced-motion-only exemption read as cover for everyone")
        css2 = css + " %s.e { animation-play-state: running !important; }" % PREFIX
        self.assertEqual(uncovered(css2), [], "premise: an unconditional exemption covers it")

    def test_an_entrance_on_a_prefixed_selector_is_still_an_entrance(self):
        css = '@keyframes rev { from { opacity: 0 } } %s.f { animation: rev .4s; }' % PREFIX
        self.assertEqual(uncovered(css), [".f"])


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "the second eye on v3493 - a first frame read as a substring again: a 100%-first reveal goes unseen, a 100%-first fade-out is flagged",
        "file": "test_an_entrance_survives_endurance.py",
        "find": "            if \"from\" in frames or \"0%\" in frames:\n",
        "replace": "            if \"from\" in frames or any(\"0%\" in f for f in frames):\n",
        "matches": 1,
    },
    {
        "why": "the second eye on v3493 - an exemption under a media query covers every context again",
        "file": "test_an_entrance_survives_endurance.py",
        "find": "                  if ((), sel) not in ex and (ctx, sel) not in ex)\n",
        "replace": "                  if ((), sel) not in ex and (ctx, sel) not in ex and sel not in {s for c, s in ex})\n",
        "matches": 1,
    },
    {
        "why": "the second eye on v3493 - `infinite` anywhere in the value skips the whole animation again",
        "file": "test_an_entrance_survives_endurance.py",
        "find": "            if any(t in names for t in toks) and \"infinite\" not in toks:\n",
        "replace": "            if any(t in names for t in toks) and \"infinite\" not in decls[\"animation\"]:\n",
        "matches": 1,
    },
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
