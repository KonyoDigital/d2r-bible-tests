#!/usr/bin/env python3
"""
VISUAL-LOCK invariant — freezes the tokenized TYPE SYSTEM so it can't silently drift.

Konyo's VISUAL-LOCK goal: after the weight type system was single-sourced onto CSS custom
properties (console + bible, v1288-v1321), lock it with an invariant test so no future edit
can quietly reintroduce a raw `font-weight:NNN` literal instead of a `var(--fw-*)` token.

Checks (both surfaces — bible.html + tv/control_ui.html):
  1. ZERO raw font-weight literals (`font-weight: NNN`, spaced or not) — every weight MUST be
     a `var(--fw-*)` token. Fails loudly naming file:line of any offender.
  2. The `--fw-*` token set is defined in :root (the source of truth for weights).
  3. STRUCTURE-LOCK (v1343, console only): the `--hd-*` spacing/structure token set is defined
     in :root — the region-gutter / card-pad / header-gap / console-card-radius rhythm the console
     structure is single-sourced onto. Their presence is locked (they can't be silently deleted);
     the values live in :root as the one place to tune the layout rhythm.

Run:  python3 visual_lock_invariant.py        (exit 0 = locked · exit 1 = drift, with details)
CI:   add to any gate — no deps, pure stdlib, ~instant.
Docs: LOCKED_TYPE_SYSTEM.md
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# Surfaces under lock + the --fw tokens each is expected to define in :root.
# (bible uses the full 6-weight range; the console uses the 4 it needs.)
SURFACES = {
    "bible.html":        {"path": os.path.join(ROOT, "bible.html"),
                          "fw": ["regular", "normal", "medium", "semibold", "bold", "black"],
                          # LS/LH-LOCK (v1344) — the bible's letter-spacing + line-height token scale
                          # (console-mirrored role names; the approved deliberate normalization).
                          "ls": ["tight", "snug", "normal", "wide", "label", "wider", "widest"],
                          "lh": ["none", "tightest", "tight", "snug", "normal", "relaxed", "loose"]},
    "tv/control_ui.html": {"path": os.path.join(ROOT, "tv", "control_ui.html"),
                           "fw": ["normal", "medium", "semibold", "bold"],
                           # STRUCTURE-LOCK (v1343): the console's shared spacing/structure rhythm.
                           "hd": ["gap", "gap-in", "gap-row", "pad-y", "pad-x", "head-mb",
                                  "head-ls", "head-size", "radius", "radius-in", "pad-row-y", "pad-row-x"]},
}

RAW_WEIGHT = re.compile(r"font-weight: *[0-9]+")   # spaced or not; !important-agnostic
# v1324 — also catch the `font:` SHORTHAND weight (font: 700 11px/1 …), which the
# font-weight:-only pattern missed (a real blind spot found after v1321). Only the 6
# named weight values, boundary-terminated so `font: 14px`/`font: var(--fw-*)` never match.
RAW_SHORTHAND = re.compile(r"font: *(?:400|500|600|700|800|900)\b")


def check():
    failures = []
    for name, cfg in SURFACES.items():
        try:
            with open(cfg["path"], encoding="utf-8") as fh:
                lines = fh.read().split("\n")
        except OSError as e:
            failures.append(f"{name}: cannot read ({e})")
            continue
        text = "\n".join(lines)
        # 1) no raw weight literals — every one must be var(--fw-*)
        for i, line in enumerate(lines, 1):
            for m in RAW_WEIGHT.finditer(line):
                failures.append(
                    f"{name}:{i}  RAW weight '{m.group(0).strip()}' — use var(--fw-*) instead")
            for m in RAW_SHORTHAND.finditer(line):
                failures.append(
                    f"{name}:{i}  RAW shorthand weight '{m.group(0).strip()}' — use font:var(--fw-*) instead")
        # 2) the --fw token set is defined
        for tok in cfg["fw"]:
            if not re.search(r"--fw-" + tok + r": *[0-9]+", text):
                failures.append(f"{name}  MISSING :root token --fw-{tok} (the weight source of truth)")
        # 3) STRUCTURE-LOCK — the --hd-* spacing/structure token set is defined (value-agnostic:
        #    px / clamp() / var() are all valid; we lock that the token EXISTS as the single source).
        for tok in cfg.get("hd", []):
            if not re.search(r"--hd-" + re.escape(tok) + r": *\S", text):
                failures.append(f"{name}  MISSING :root token --hd-{tok} (the structure rhythm source of truth)")
        # 4) LS/LH-LOCK — the letter-spacing / line-height token scales are defined (value-agnostic).
        for tok in cfg.get("ls", []):
            if not re.search(r"--ls-" + re.escape(tok) + r": *\S", text):
                failures.append(f"{name}  MISSING :root token --ls-{tok} (the letter-spacing scale source of truth)")
        for tok in cfg.get("lh", []):
            if not re.search(r"--lh-" + re.escape(tok) + r": *\S", text):
                failures.append(f"{name}  MISSING :root token --lh-{tok} (the line-height scale source of truth)")
    return failures


def main():
    failures = check()
    if failures:
        print("❌ VISUAL-LOCK DRIFT — the type system moved (%d issue%s):"
              % (len(failures), "" if len(failures) == 1 else "s"))
        for f in failures:
            print("   • " + f)
        print("\nFix: replace each raw font-weight:NNN with its token "
              "(400=regular 500=normal 600=medium 700=semibold 800=bold 900=black), "
              "e.g. font-weight:var(--fw-semibold). See LOCKED_TYPE_SYSTEM.md.")
        return 1
    print("✅ VISUAL-LOCK OK — 0 raw font-weight literals in both surfaces; "
          "--fw-* token sets intact; console --hd-* structure rhythm defined. "
          "The weight type system AND the structure rhythm are locked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
