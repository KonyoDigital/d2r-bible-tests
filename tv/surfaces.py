#!/usr/bin/env python3
"""THE ONE PLACE EVERY IN-GAME SURFACE IS DECLARED.

★ v2311 — Konyo: "the readers and ai analyzers all need the same upgraded logic and tools to read
everything necessary like it should be synced.. the only difference is the witnesses and bypasses
depending on the route of it ... it needs a unified additive only nothing should be stripped from
any of them and all should be logically updated accordingly the best versions and upgraded use and
techniques we built".

⚠ THIS IS A DECLARATION, NOT A REWRITE. Nothing is stripped and no reader changes behaviour by
importing it. It exists so the FACTS about each surface live in one table instead of being
rediscovered from two files — and so a guard can say when a surface is missing a technique the
others already have. The refactor it enables comes later; the drift it makes visible starts now.

WHAT WAS DRIFTING, measured 2026-08-30:
  · stash_eye reads a LEFT-ANCHORED panel and owns the richer toolkit: the aspect law,
    the deliberate crop + 3x enlarge, and the per-layout grid prep,
    tab_from_ocr_lines, classify_stash_grid.
  · chronicle_template reads a CENTERED MODAL and cannot copy that left-anchor math; it uses a
    center-preserving derivation instead. That difference is REAL and is recorded here, not
    "fixed".
  · Each carries its OWN calibration film of the SAME monitor — (2940, 1912) in both today. One
    re-measure updates one and silently leaves the other reading a screen shape that no longer
    exists. Watched by corroborate._inv_the_two_readers_measure_the_same_screen and
    health_engine.check_readers_agree.
  · the tooltip cropper — the enlarge-the-tooltip step, and the tooltip is the ONLY
    place an item name appears — had exactly ONE production caller (vault_retro). slot_identity
    describes it in a comment and does not call it.
[[copy-drift]] [[the-unjoined-end]]

⚠ CALL-SHAPED TEXT IS NOT WRITTEN HERE, AND THAT IS DELIBERATE. The first cut declared techniques
as strings that paired a reader's function name directly with an opening
parenthesis and its arguments. tv/test_reachability.py counts that exact shape across
every watched file to find functions with no caller — so a DECLARATION describing a technique made
an allowlisted orphan look alive, and a genuinely dead reader would have read as reachable because
this file mentions it. Techniques are (name, params) tuples for that reason.
⚠ AND THE NOTE YOU ARE READING TRIPPED IT TOO: the first version of this warning
quoted the bad example verbatim, so the scanner read the explanation as the call it
was warning about. A rule written in the shape it forbids is still that shape.
[[feedback-comments-vs-code]] [[source-reading-guard]]
"""

#: anchor laws. Not interchangeable: the difference is geometry, not preference.
LEFT_ANCHORED = "left"      # panel pinned at x=0; stash_eye's `x * cal_aspect/aspect` law
CENTER_MODAL = "center"     # modal centred in the viewport; center-preserving derivation

#: Every surface a reel can be declared as. The keys ARE control_app.MINI_FOCUSES, so a focus he
#: can press and a surface a reader can read are the same list — guarded below.
SURFACES = {
    "stash": {
        "reader": "stash_eye", "anchor": LEFT_ANCHORED, "layout": "stash",
        "tab_chrome": True, "enlarge": ("prep_tab_chrome", {"scale": 3}),
        "tooltip": True,
        "why": "the ownership surface; a GRID prints no names, so the tooltip is the only evidence",
    },
    "runes": {
        "reader": "stash_eye", "anchor": LEFT_ANCHORED, "layout": "runes",
        "tab_chrome": True, "enlarge": ("prep_stash_grid", {"layout": "runes"}),
        "tooltip": True, "why": "rune sheet — dense grid, names only on hover",
    },
    "gems": {
        "reader": "stash_eye", "anchor": LEFT_ANCHORED, "layout": "gems",
        "tab_chrome": True, "enlarge": ("prep_stash_grid", {"layout": "gems"}),
        "tooltip": True, "why": "gem stash; tab_from_gem gives an independent tab vote",
    },
    "materials": {
        "reader": "stash_eye", "anchor": LEFT_ANCHORED, "layout": "materials",
        "tab_chrome": True, "enlarge": ("prep_stash_grid", {"layout": "materials"}),
        "tooltip": True, "why": "materials tab",
    },
    "inventory": {
        "reader": "stash_eye", "anchor": LEFT_ANCHORED, "layout": "inventory",
        "tab_chrome": True, "enlarge": ("prep_tab_chrome", {"scale": 3}),
        "tooltip": True,
        "why": "read and registered, but LOCKED against throw suggestions (vault_retro.LOCKED_LANES)",
    },
    "chronicle-uniques": {
        "reader": "chronicle_template", "anchor": CENTER_MODAL, "layout": None,
        "tab_chrome": True, "enlarge": None,
        "tooltip": False,
        "why": "the Chronicle modal lists names as TEXT, so no tooltip is needed to read one",
    },
    "chronicle-sets": {
        "reader": "chronicle_template", "anchor": CENTER_MODAL, "layout": None,
        "tab_chrome": True, "enlarge": None,
        "tooltip": False, "why": "same modal, set ledger",
    },
}


def surface(name):
    """-> the declaration, or None. Never a guess."""
    return SURFACES.get(str(name or "").strip().lower())


def readers():
    """Which reader module owns each surface. -> {reader: [surface, ...]}"""
    out = {}
    for k, v in SURFACES.items():
        out.setdefault(v["reader"], []).append(k)
    return {k: sorted(v) for k, v in out.items()}


def tooltip_surfaces():
    """Surfaces that DECLARE they need the tooltip step. -> [name, ...]

    Pure declaration. It says what the table asks for, and nothing about whether anything answers.
    """
    return sorted(k for k, v in SURFACES.items() if v.get("tooltip"))


def tooltip_callers():
    """PRODUCTION modules that import tooltip_crop. -> [filename, ...]

    Comments and docstrings are stripped first. Several files DISCUSS tooltip_crop in prose —
    slot_identity.py names it in a comment while never calling it — and a scanner that counts its
    own documentation reports a lane as wired because somebody wrote about it.
    [[feedback-comments-vs-code]] [[source-reading-guard]]
    """
    import os
    import re
    here = os.path.dirname(os.path.abspath(__file__))
    out = []
    for fn in sorted(os.listdir(here)):
        # ⚠ EXCLUDE THIS FILE. tooltip_wiring() imports tooltip_crop in order to CHECK it,
        # so a scanner that counts every importer counts its own probe and reports the
        # wiring as honoured by the very function asking the question. Same shape as a
        # grep matching its own command line. [[feedback-suspect-the-instrument]]
        if (not fn.endswith(".py") or fn.startswith("test_")
                or fn in ("tooltip_crop.py", os.path.basename(__file__))):
            continue
        try:
            with open(os.path.join(here, fn), encoding="utf-8", errors="replace") as fh:
                src = fh.read()
        except Exception:
            continue
        src = re.sub(r'"""(.*?)"""', "", src, flags=re.S)
        src = re.sub(r"'''(.*?)'''", "", src, flags=re.S)
        src = re.sub(r"#[^\n]*", "", src)
        if re.search(r"^\s*(?:import|from)\s+tooltip_crop\b", src, re.M):
            out.append(fn)
    return out


def tooltip_wiring():
    """Is the declared tooltip need actually HONOURED by production code? -> (ok, why)

    THIS EXISTS BECAUSE ITS PREDECESSOR WAS A LABEL THAT OUTLIVED ITS REFERENT. It was called
    `missing_tooltip_wiring` and its body returned every surface with tooltip=True — so it
    answered ['gems','inventory','materials','runes','stash'] and would have answered exactly
    that forever, however well or badly the system was wired. Read as "5 surfaces are missing
    their wiring", it was reporting a constant. A number is only a finding if some state of the
    world would change it. [[label-outlived-referent]] [[feedback-threshold-above-the-ceiling]]

    WHY THIS IS NOT stash_eye's JOB, measured rather than assumed: a tooltip rectangle is derived
    by DIFFERENCING two consecutive frames (tooltip_crop.changed_rect). stash_eye reads a single
    frame and structurally cannot do that, so the step belongs to the reel sweep — which is where
    it already lives. ONE production importer is therefore CORRECT, not a shortfall. The earlier
    reading of this as "the cropper reaches only one reader, so four are starved" was wrong.

    The wiring is honoured when all three hold, and this goes RED if any stops being true:
      1. tooltip_crop imports at all,
      2. its bounds admit a real tooltip (a window nothing can fall inside is an absent gate),
      3. at least one PRODUCTION module actually imports it.
    """
    try:
        import tooltip_crop as _tc
    except Exception as e:
        return False, "tooltip_crop does not import: %s" % str(e)[:70]
    try:
        ok, why = _tc.bounds_are_reachable()
    except Exception as e:
        return False, "tooltip_crop.bounds_are_reachable raised: %s" % str(e)[:70]
    if not ok:
        return False, "the tooltip crop window could never fire: %s" % why
    callers = tooltip_callers()
    if not callers:
        return False, ("no production module imports tooltip_crop, so every surface declaring "
                       "tooltip=True is asking for a step that nobody performs")
    return True, "hover evidence is derived by %s" % ", ".join(callers)


def missing_tooltip_wiring():
    """Surfaces whose declared tooltip need is NOT honoured. -> [name, ...]

    Empty today, and it must be ABLE to be non-empty: remove the import from the sweep and every
    tooltip surface comes back. That is the whole difference between this and what it replaced.
    """
    ok, _why = tooltip_wiring()
    return [] if ok else tooltip_surfaces()


def main(argv=None):
    from console_safe import enable
    enable()
    print("── EVERY IN-GAME SURFACE, DECLARED ──")
    for r, names in sorted(readers().items()):
        print("  %-20s %s" % (r, ", ".join(names)))
    print()
    for k in sorted(SURFACES):
        v = SURFACES[k]
        e = v["enlarge"]
        print("  %-18s anchor=%-6s tooltip=%-5s enlarge=%s"
              % (k, v["anchor"], v["tooltip"],
                 ("%s %s" % (e[0], e[1])) if e else "-"))
    print()
    print("  surfaces needing the tooltip step: %s" % ", ".join(tooltip_surfaces()))
    _ok, _why = tooltip_wiring()
    print("  is that need honoured?             %s \u00b7 %s"
          % ("YES" if _ok else "NO", _why))
    _miss = missing_tooltip_wiring()
    if _miss:
        print("  UNHONOURED: %s" % ", ".join(_miss))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
