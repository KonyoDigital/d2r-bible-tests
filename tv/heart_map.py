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
    """-> (ids, seen, missing).

    `ids` is None ONLY when control_ui.html itself could not be read. `seen` is None whenever the
    map cannot be trusted — that is the unmeasurable signal, and it covers the watcher case where
    `ids` is a real list. `missing` names every watcher that could not be read.
    ⚠ v3237 — this used to say "`ids` is None when the map cannot be measured at all", which is
    what let a caller use `ids is None` as the "the page was unreadable" fact. The sentence
    outlived the shape it described. [[label-outlived-referent]]"""
    ids = surfaces()
    blob, missing = watched()
    # ⚠⚠ v3237 — `ids is None` MUST MEAN THE PAGE, AND IT DID NOT. This collapsed BOTH failures
    # into `ids = None`, and v3235 then handed `ids is None` to `_why_unmeasurable` as the
    # "control_ui.html could not be read" fact. So a perfectly readable page plus ONE unreadable
    # watcher printed "control_ui.html could not be read AND these watchers could not be read:
    # ..." — naming a healthy file first and sending the reader straight to it.
    #
    # A cross-family review of v3235 caught it AND named why the new law missed it: the test
    # calls the helper with a literal True and never goes through measure(), so the proxy itself
    # was never exercised. A fact passed as a PROXY is only ever as true as the proxy.
    # [[label-outlived-referent]] [[the-unjoined-end]]
    if ids is None:
        return None, None, missing          # the page itself could not be read
    if missing:
        return ids, None, missing           # the page is FINE; only watchers are missing
    seen = sorted(i for i in ids if i in blob)
    return ids, seen, missing


def _why_unmeasurable(missing, page_unreadable):
    """Say every reason the map could not be built, not the first one. -> str

    ⚠ THE CALLER TELLS IT; IT DOES NOT LOOK AGAIN. The first cut called `surfaces()` here, which
    re-opens control_ui.html — so between `measure()` deciding the page was unreadable and this
    sentence being built, the file could become readable again and the reason would VANISH from
    a refusal that still fires. Not hypothetical in this repo: `bump_version.py` writes the
    surfaces with an ATOMIC REPLACE, and an atomic replace is exactly a window in which a path
    is briefly missing and then fine. The refusal would read "no reason recorded".
    Found by a cross-family review of v3233, the version that added this helper.
    [[stale-reading]] [[unknown-stays-unknown]]
    """
    bits = []
    if page_unreadable:
        bits.append("control_ui.html could not be read")
    if missing:
        bits.append("these watchers could not be read: %s" % ", ".join(missing))
    return " AND ".join(bits) or "no reason recorded"


def render():
    ids, seen, missing = measure()
    # ⚠ REFUSE, DO NOT RENDER A ZERO. Writing the map is what banks it: the pre-push gate compares
    # HEART.md against the tree, so a map built from a failed read becomes the committed truth.
    # v3237 — refuse on EITHER failure, now that `ids` is no longer the single signal.
    if ids is None or missing:
        raise RuntimeError(
            # ⚠ the counterfactual must match the FAILURE. A watcher-only failure would not
            # have written "0 surfaces" — ids is the real list; what it would have written is a
            # COVERAGE figure computed without a watcher, which reads as a real collapse.
            "the heart map could not be measured: %s. Refusing to write it: an unreadable file "
            "is UNKNOWN, not empty, and a coverage figure missing a watcher is a collapse that "
            "did not happen."
            # v3233 — NAME BOTH. `missing` being non-empty used to hide that the console page
            # was ALSO unreadable, so a double failure reported as a watcher problem and sent
            # the reader to the wrong file. [[zero-needs-a-denominator]]
            % _why_unmeasurable(missing, ids is None))
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
    if ids is None or missing:
        print("🔴 the heart map could not be measured: %s"
              % _why_unmeasurable(missing, ids is None))
        print("   UNKNOWN is not a measurement. Refusing rather than banking a coverage figure "
              "nobody could take.")
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
