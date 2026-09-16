# -*- coding: utf-8 -*-
"""HEART.md — WHICH SURFACES OF THE CONSOLE ARE WATCHED, DERIVED FROM THE CONSOLE ITSELF.

⚠⚠ WHY THIS EXISTS, 2026-09-16. His standing order is JOIN -> GATE -> HEART -> BANK. It was
carved as prose in `join_gate_heart` on 2026-09-06 and I read it and then skipped HEART on FIVE
CONSECUTIVE SHIPS — v3201 through v3205 — every one carrying a law, a red-proof, a registered gate
and a BUGS entry, and not one carrying a heart row. Measured when he asked: 402 gates registered,
61 doctor rows, and `stationbar 0 · sh-filterfold 0 · shr-stkey 0 · sweep-box 0 · fleet-row 0`.

His answer: *"we need it all updated and blueprints updated and heart updated all derived from the
console"*, and then, when I said the heart was the one with no enforcement: *"fix this so it is
like blueprints too and has enforcemnt"*.

THE BLUEPRINT'S SHAPE, MIRRORED EXACTLY, because it is the one artefact here that has never
drifted:
  1. it is DERIVED — nobody writes it by hand, so it cannot disagree with the code
  2. `bump_version.py` REGENERATES it on every bump
  3. the pre-push REFUSES when it is stale, and does NOT regenerate it itself — a hook that
     rewrote the tree would dirty the very bytes it is grading
     [[d2r-push-grades-the-working-tree]]

⚠ AND THE TIMESTAMP IS EXCLUDED FROM THE COMPARISON. blueprint.py records that without it the
gate "is furniture on day one": a clock that changes every minute makes the diff red forever and
nobody reads it. Compare the MAP, not the clock.

WHAT IT MEASURES: the console's rendered surfaces (the ids and classes its own JS paints), against
the names that appear in anything that WATCHES — console_doctor, health_engine, corroborate,
heart2. A surface nobody names is UNWATCHED, and saying so is the whole point.
⚠ UNWATCHED IS NOT A FAILURE. Most surfaces do not need a watcher and never will. What this
refuses is a surface being unwatched SILENTLY — the count is a ratchet, and it may not get worse
without a human saying why. [[zero-needs-a-denominator]] [[unknown-stays-unknown]]
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(REPO, "HEART.md")
FLOOR = os.path.join(HERE, "heart_floor.json")

WATCHERS = ("console_doctor.py", "health_engine.py", "corroborate.py", "heart2.py")

# A surface is something the console PAINTS and he can therefore see go wrong. Ids are the honest
# unit: a class may be shared by forty nodes, an id names one thing.
_ID_RX = re.compile(r"""id=\\?["']([a-zA-Z][\w-]{2,})\\?["']""")


def _read(name):
    """-> the file's text, or None when it could not be read. NEVER "".

    ⚠⚠ IT RETURNED "" AND THAT MADE THE HEART MAP ITSELF THE LIE. `surfaces()` runs the id regex
    over this string, so an unreadable `control_ui.html` yields an EMPTY SET — and `render()`
    would then write, into the file the pre-push gate compares against the tree:

        | surfaces the console paints | **0** |
        | of those, watched           | **0** |
        | coverage                    | **0.0%** |

    A heart map stating that the console paints nothing, banked into the repo, from a failed open.
    The organ that exists to notice blindness would have gone blind in exactly the shape it was
    built to catch. [[zero-needs-a-denominator]] [[unknown-stays-unknown]]
    """
    try:
        with io.open(os.path.join(HERE, name), encoding="utf-8") as fh:
            return fh.read()
    except Exception:
        return None


def surfaces():
    """-> sorted ids the console paints, or None when the console page could not be read."""
    ui = _read("control_ui.html")
    if ui is None:
        return None
    return sorted({m.group(1) for m in _ID_RX.finditer(ui)})


def watched():
    """-> (blob of every watcher's text, [watchers that could not be read])

    A watcher that cannot be read makes every surface it covers look UNWATCHED — which would
    report as a coverage collapse and, worse, as a real one. It is named instead of skipped.
    """
    parts, missing = [], []
    for w in WATCHERS:
        t = _read(w)
        if t is None:
            missing.append(w)
        else:
            parts.append(t)
    return "\n".join(parts), missing


def measure():
    """-> (ids, seen, missing). `ids` is None when the map cannot be measured at all."""
    ids = surfaces()
    blob, missing = watched()
    if ids is None or missing:
        return None, None, missing
    seen = sorted(i for i in ids if i in blob)
    return ids, seen, missing


def _why_unmeasurable(missing):
    """Say every reason the map could not be built, not the first one. -> str"""
    bits = []
    if surfaces() is None:
        bits.append("control_ui.html could not be read")
    if missing:
        bits.append("these watchers could not be read: %s" % ", ".join(missing))
    return " AND ".join(bits) or "no reason recorded"


def render():
    ids, seen, missing = measure()
    # ⚠ REFUSE, DO NOT RENDER A ZERO. Writing the map is what banks it: the pre-push gate compares
    # HEART.md against the tree, so a map built from a failed read becomes the committed truth.
    if ids is None:
        raise RuntimeError(
            "the heart map could not be measured: %s. Refusing to write a map that would claim "
            "the console paints 0 surfaces — an unreadable file is UNKNOWN, not empty."
            # v3233 — NAME BOTH. `missing` being non-empty used to hide that the console page
            # was ALSO unreadable, so a double failure reported as a watcher problem and sent
            # the reader to the wrong file. [[zero-needs-a-denominator]]
            % _why_unmeasurable(missing))
    pct = (100.0 * len(seen) / len(ids)) if ids else 0.0
    lines = [
        "# THE HEART — what watches the console",
        "",
        "Derived by `tv/heart_map.py`. Do not edit by hand: it is regenerated on every bump and",
        "the pre-push refuses when it is stale, exactly like BLUEPRINT.md.",
        "",
        "A surface here is an `id` the console paints — the honest unit, because a class may be",
        "shared by forty nodes while an id names one thing. WATCHED means its name appears in",
        "`console_doctor.py`, `health_engine.py`, `corroborate.py` or `heart2.py`.",
        "",
        "⚠ UNWATCHED IS NOT A DEFECT. Most surfaces neither need nor will ever have a watcher.",
        "What is refused is a surface going unwatched SILENTLY — the count below is a ratchet and",
        "may not fall without a human saying why in `heart_floor.json`.",
        "",
        "| | |",
        "|---|---|",
        "| surfaces the console paints | **%d** |" % len(ids),
        "| of those, watched | **%d** |" % len(seen),
        "| coverage | **%.1f%%** |" % pct,
        "",
        "## Watched",
        "",
    ]
    lines += ["- `%s`" % s for s in seen] or ["_none_"]
    return "\n".join(lines) + "\n"


def _floor():
    try:
        with io.open(FLOOR, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def main(argv=None):
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    argv = argv or []
    ids, seen, missing = measure()
    # v3231 — an unmeasurable map is a REFUSAL at every door, not a quiet zero in one of them.
    if ids is None:
        print("🔴 the heart map could not be measured: %s"
              % _why_unmeasurable(missing))
        print("   UNKNOWN is not 0 surfaces. Refusing rather than rendering an empty heart.")
        return 1
    if "--print" in argv:
        print(render())
        return 0
    if "--check" in argv:
        # ⚠ REFUSE, NEVER REGENERATE — the pre-push grades the working tree.
        try:
            have = io.open(OUT, encoding="utf-8").read()
        except Exception:
            print("HEART.md is missing — run: python3 tv/heart_map.py")
            return 1
        if have.strip() != render().strip():
            print("HEART.md does not match the code — run: python3 tv/heart_map.py")
            return 1
        fl = _floor()
        if fl is None:
            print("heart_floor.json has never been written, so whether coverage SHRANK is "
                  "UNKNOWN — run: python3 tv/heart_map.py --bless")
            return 1
        was = int(fl.get("watched") or 0)
        if len(seen) < was:
            gone = sorted(set(fl.get("names") or []) - set(seen))
            print("HEART coverage FELL %d -> %d. A surface that was watched no longer is: %s"
                  % (was, len(seen), ", ".join(gone[:8]) or "(names not recorded)"))
            print("If that is deliberate, lower it by hand in tv/heart_floor.json and say why.")
            return 1
        print("heart: %d of %d painted surfaces watched (floor %d)" % (len(seen), len(ids), was))
        return 0
    if "--bless" in argv:
        io.open(FLOOR, "w", encoding="utf-8").write(json.dumps(
            {"_why": "HEART coverage ratchet — it may only RISE. A fall means a surface this "
                     "console used to watch is no longer watched, which in a green run reads "
                     "exactly like clean.",
             "watched": len(seen), "surfaces": len(ids), "names": seen},
            indent=2, sort_keys=True) + "\n")
        print("  blessed heart floor at %d of %d" % (len(seen), len(ids)))
    io.open(OUT, "w", encoding="utf-8").write(render())
    print("  wrote %s — %d of %d painted surfaces watched" % (os.path.relpath(OUT, REPO),
                                                              len(seen), len(ids)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
