# -*- coding: utf-8 -*-
"""AN ITEM NAME'S COLOUR IS ITS RARITY, NEVER THE TIER OF THE FIND THAT CARRIED IT.

Konyo, on a Vault screenshot, 2026-09-17: *"also the color for sets and uniques for the keyword
items need also syncing to the console so they match"*.

⚠⚠ THE TWO OBVIOUS SUSPECTS WERE BOTH INNOCENT, AND CHECKING THEM FIRST IS WHY THIS GATE EXISTS
AT ALL. The palettes had not drifted — every quality token in control_ui.html equals bible.html's
to the byte (--rar-unique #c7b377 = --q-unique, --rar-set #00fc00 = --q-set, and --rar-runeword is
#c7b377 ON PURPOSE because the game paints a completed runeword the same gold as a unique). And the
board classifies correctly: asked through CDP, **135 of 135 set pieces resolved 'set' and 397 of 398
uniques resolved 'unique'** (the exception, Crescent Moon, is a runeword name and answers 'rw').

WHAT WAS WRONG WAS WHICH QUESTION THE CONSOLE ASKED. `grail` in this console is a find TIER —
`_FIND_TIER` is {grail, keep, border} — and `control_app` promotes to tier='grail' any find whose
name appears in `_kai_fullnames()`, which is **3,212 names scraped out of bible.html, SET PIECES
INCLUDED**. Measured on the live helper: "sigon's visor", "arctic binding", "angelic halo" and
"vidala's snare" are all in that set. So a set piece found in a session was tier 'grail', and four
surfaces painted it UNIQUE GOLD — indistinguishable from a real unique, which is precisely what he
was looking at.

v1634/v1635 had already moved these surfaces off chrome gold and onto --rar-unique. Right move for
the surface, wrong constant for the item: it replaced "the wrong gold" with "the right gold,
applied unconditionally". A colour that is correct for most of its inputs is the hardest kind of
wrong to see.

THE LAW, stated so it survives a rewrite: **any line that puts one of the quality-painting classes
on an element AND interpolates an item `.name` must ask `_nameRarCls` for that name.** It does not
pin the emitted string, the class order, or the colours — only the joint. The count line beside the
beat chips (`'+N more'`) interpolates no name and is correctly exempt by the same rule.

[[the-unjoined-end]] [[unknown-stays-unknown]] [[source-reading-guard]] [[label-outlived-referent]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
# ⚠ This file prints ⚠ / — / ★ in its failure messages. On a cp1255 Windows console an un-wrapped
# stdout raises UnicodeEncodeError while REPORTING, so a clean tree exits non-zero and the reason is
# an encoding traceback rather than the verdict. test_control pins this for every CLI in the tree.
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

UI = os.path.join(HERE, "control_ui.html")

#: classes whose whole job is to paint a QUALITY onto a name. `fc-name` is included because on a
#: grail card it is the item's name and took --rar-unique; `bt-grail` / `hh-grail` /
#: `shc-headfind` are the other three v1634/v1635 moved onto the unique token.
PAINTERS = ("fc-name", "bt-grail", "hh-grail", "shc-headfind")


def _src():
    with io.open(UI, encoding="utf-8", errors="replace") as f:
        return f.read()


def _code(src):
    """`src` with COMMENTS removed, so prose can neither satisfy nor break a law here.

    Reuses frame_authority._executable_only rather than growing a third stripper — REG-1059's
    lesson, one file old. It is asked for ".js" so the JS/CSS comment path runs; ast.parse would
    refuse this document and hand back every comment intact.
    """
    try:
        from frame_authority import _executable_only
        return _executable_only(src, ".js")
    except Exception:
        return re.sub(r"/\*.*?\*/", " ", src, flags=re.S)


def _script_blocks(src):
    return re.findall(r"<script>(.*?)</script>", src, re.S)


def _painting_lines(src):
    """-> [(lineno, line)] every executable line that paints a painter class onto a NAME.

    The pair is the whole law: a class that colours, plus an interpolated `.name`. A line carrying
    the class with no name (the '+N more' beat chip) makes no claim about an item and is exempt.
    """
    out = []
    for js in _script_blocks(src):
        for i, ln in enumerate(_code(js).split("\n"), 1):
            if ".name" not in ln:
                continue
            if any(('class="' + p) in ln or ("'" + p + "'") in ln for p in PAINTERS):
                out.append((i, ln.strip()))
    return out


class ANameIsColouredByWhatItIs(unittest.TestCase):

    def test_baseline_the_surfaces_still_exist(self):
        """If nothing paints a name any more, every law below passes by describing nothing."""
        lines = _painting_lines(_src())
        self.assertGreaterEqual(
            len(lines), 4,
            "BASELINE: only %d line(s) paint an item name on a quality surface; this gate was "
            "written against 4 (fc-name, bt-grail, hh-grail, shc-headfind). Fewer means the "
            "surfaces moved and this law is now measuring nothing." % len(lines))

    def test_every_painted_name_asks_for_its_rarity(self):
        bad = [(n, ln) for n, ln in _painting_lines(_src()) if "_nameRarCls" not in ln]
        self.assertFalse(
            bad,
            "%d line(s) paint an item name on a quality surface without asking what quality it "
            "IS, so the colour comes from the find TIER again - and tier 'grail' covers set "
            "pieces (3,212 names in _kai_fullnames, sets included). Offenders: %s"
            % (len(bad), "; ".join("L%d %s" % (n, ln[:90]) for n, ln in bad)))

    def test_the_helper_asks_the_board_rather_than_keeping_its_own_table(self):
        """A second rarity table in the console is a second thing to drift. [[copy-drift]]"""
        src = _code(_src())
        i = src.find("function _nameRarCls")
        self.assertGreater(i, -1, "_nameRarCls is gone; the four surfaces have nothing to ask")
        body = src[i:src.find("window._cNameRarCls", i)]
        self.assertIn("_artRarity", body,
                      "_nameRarCls no longer consults the board's _artRarity - the board is the "
                      "only thing that knows an item's quality, and 135/135 + 397/398 is measured")
        self.assertIn("tvd-eng", body,
                      "_nameRarCls no longer reaches the board iframe by id")

    def test_a_miss_is_never_cached(self):
        """'' means BOTH 'the board has not loaded' and 'nothing recognised'.

        Caching the first freezes every later name cream for the whole session - a wrong answer
        that outlives its cause, on a surface nobody would re-check. [[stale-reading]]
        """
        src = _code(_src())
        i = src.find("function _nameRarCls")
        body = src[i:src.find("window._cNameRarCls", i)]
        writes = [ln.strip() for ln in body.split("\n") if "_NAMERAR[n] =" in ln]
        self.assertTrue(writes, "nothing writes the cache; the helper's shape changed")
        for w in writes:
            self.assertTrue(
                w.startswith("if (out)") or w.startswith("if(out)"),
                "the rarity cache is written unguarded (%r). An unreachable board answers '' and "
                "that '' would be remembered as the item's quality forever." % w[:80])

    def test_the_shared_rule_paints_from_the_tokens(self):
        css = _code(_src())
        for rar, tok in (("set", "--rar-set"), ("unique", "--rar-unique")):
            m = re.search(r"\.rq\.rq\.r-" + rar + r"\s*\{([^}]*)\}", css)
            self.assertIsNotNone(
                m, "there is no .rq.rq.r-%s rule, so a name classed r-%s paints nothing" % (rar, rar))
            self.assertIn(tok, m.group(1),
                          "the r-%s rule does not read %s - a quality colour spelled anywhere but "
                          "its token is a seventh palette waiting to drift" % (rar, tok))

    def test_the_doubled_class_is_not_tidied_away(self):
        """`.rq` alone is (0,2,0) and LOSES to `.find-card.fc-grail .fc-name` (0,3,0).

        This is the failure mode a later cleanup produces on sight: the rule reads redundant, gets
        simplified to a single `.rq`, and goes silently inert on the find cards - the one surface
        with a three-class selector. The doubling is load-bearing, so it is asserted.
        """
        css = _code(_src())
        self.assertIn(".find-card.fc-grail .fc-name", css,
                      "BASELINE: the (0,3,0) rule this doubling exists to out-specify is gone; "
                      "re-measure before trusting the assertion below")
        singles = re.findall(r"(?<!\.rq)\.rq\.r-(set|unique)\s*\{", css)
        self.assertFalse(
            singles,
            "a .rq.r-%s rule is present WITHOUT the doubled class. At (0,2,0) it loses to "
            ".find-card.fc-grail .fc-name at (0,3,0) regardless of source order, so grail find "
            "cards silently keep painting every name unique gold." % (singles[0] if singles else ""))


RED_PROOF = [
    {
        "why": "un-asking the hero line's rarity puts it back on the find tier - the whole defect",
        "file": "tv/control_ui.html",
        "find": "'<div class=\"hh-grail' + _nameRarCls(topGrail.name) + '\"",
        "replace": "'<div class=\"hh-grail' + '' + '\"",
        "matches": 1,
    },
    {
        "why": "caching a miss lets one unloaded board freeze every later name cream for the session",
        "file": "tv/control_ui.html",
        "find": "    if (out) _NAMERAR[n] = out;",
        "replace": "    _NAMERAR[n] = out;",
        "matches": 1,
    },
    {
        "why": "collapsing the doubled class is the tidy-up that makes the find-card rule inert",
        "file": "tv/control_ui.html",
        "find": "  .rq.rq.r-set      { color: var(--rar-set); }",
        "replace": "  .rq.r-set      { color: var(--rar-set); }",
        "matches": 1,
    },
    {
        "why": "spelling the colour instead of reading the token is how the two files drift apart",
        "file": "tv/control_ui.html",
        "find": "  .rq.rq.r-unique   { color: var(--rar-unique); }",
        "replace": "  .rq.rq.r-unique   { color: #c7b377; }",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
