# -*- coding: utf-8 -*-
"""#42 — WHICH VIEWPORTS A WIDTH LAW MEASURES IN THIS RUN. ONE owner of the variable, for the laws, the prover and the
gate set alike.

His words, 2026-09-28: pushes take too long ("do #42 right after v3522 lands"). MEASURED on the v3522 push: the pre-push
hook re-proves every red-proof of a changed law with `heart2.py --prove`, a proof is a clean run AND a tampered run, and
heart2 runs every proof of one gate back to back in the lane that owns it. The character builder's width law renders
~33 viewports (7 widths in 6 states, 3 with picked mods, 5 with charms, a 26-step sweep) - 98 s for ONE run on his Mac -
and carries 41 red-proofs: one ~105-minute thread. The mule window's (25 proofs, ~110 s a run) was the other long pole,
and the v3522 push gate took ~2h50m. Every one of those tampers shows its defect at one viewport or two; the other
renders prove nothing about it.

So a red-proof may DECLARE the viewports at which its defect shows (`"widths": ["1280x800"]`, measured - never guessed),
and at push time only (`heart2.py --prove NAMES --push`, which hooks/pre-push runs) its clean AND tampered runs are
handed TV_LAW_WIDTHS naming them. Every width loop in the law then measures only those viewports, a case whose viewports
are all outside the set is a declared SKIP, and the fixture's own steps (the entry, the equip, the fresh build) run as
they always do. Unset, the law is exactly what it was. MEASURED 2026-09-29: one restricted run of the builder's law is
~20 s at 1280x800, ~30 s at 375x812, ~47 s at 2000x1300 (its one-viewport passes), against 98 s for the full sweep.

⚠ IT IS A PROVING DEVICE, NEVER A VERDICT. run_gates.run() scrubs the variable (scrub() below) before its first gate and
no CI workflow sets it, so the full sweep stays the verdict of record. heart2's _run_gate removes it from every run it
did not restrict itself. test_a_push_proof_runs_only_where_its_defect_shows asserts all three.
⚠ AND IT FAILS CLOSED. A declared viewport at which the tamper stays green reads BLIND and refuses the push exactly as a
blind law does today - a wrong declaration can never read PROVEN. A viewport the law never measures measures nothing,
so a proof declared at it reads BLIND too (and the law's well-formedness case refuses it before any push).
"""
import os
import re

ENV = "TV_LAW_WIDTHS"
_ONE = re.compile(r"^\s*(\d{2,5})\s*x\s*(\d{2,5})\s*$")


def parse(raw):
    """'1280x800,375x812' (or a list of such strings) -> ((1280, 800), (375, 812)), in the order given, no repeats.

    Raises ValueError on anything else: an unreadable restriction is not "every width" and not "no width" - the caller
    must refuse it, because either silent reading would change what the law measures without saying so.
    [[unknown-stays-unknown]]"""
    parts = raw if isinstance(raw, (list, tuple)) else str(raw).split(",")
    out = []
    for p in parts:
        m = _ONE.match(str(p))
        if not m:
            raise ValueError("%r is not a viewport WIDTHxHEIGHT" % (p,))
        wh = (int(m.group(1)), int(m.group(2)))
        if wh not in out:
            out.append(wh)
    if not out:
        raise ValueError("no viewport named")
    return tuple(out)


def only(environ=None):
    """The viewports this run is restricted to -> None (EVERY width, the verdict of record) | tuple of (w, h).

    ⚠ An EMPTY value reads as unset, never as "no width at all": a restriction to nothing would make every width case
    skip and the law read green having measured nothing. A malformed value RAISES (parse), so the law dies loudly at
    import instead of measuring something nobody asked for."""
    raw = (os.environ if environ is None else environ).get(ENV)
    if raw is None or not str(raw).strip():
        return None
    return parse(raw)


def pick(seq, restricted):
    """The members of `seq` (viewports) this run measures, in `seq`'s own order. restricted None = all of them."""
    return tuple(tuple(x) for x in seq if restricted is None or tuple(x) in restricted)


def at(wh, restricted):
    """Is this ONE viewport measured in this run?"""
    return restricted is None or tuple(wh) in restricted


def label(whs):
    return ",".join("%dx%d" % tuple(x) for x in whs)


def declared(pr):
    """A red-proof's own `widths` -> None (it declares none: it runs at EVERY width) | tuple of (w, h).

    Raises ValueError when the declaration is present and unreadable - the well-formedness case reports it, and the
    prover refuses to guess (read as None it would silently run the proof at full width and hide the mistake; read as
    () it would measure nothing)."""
    if not isinstance(pr, dict) or "widths" not in pr:
        return None
    w = pr.get("widths")
    if not isinstance(w, (list, tuple)) or not w:
        raise ValueError("'widths' must be a non-empty list of 'WIDTHxHEIGHT' strings, got %r" % (w,))
    return parse(list(w))


def scrub(environ=None):
    """Remove the restriction from an environment a VERDICT is about to be taken in. -> the value removed, or None.

    run_gates.run() calls this before its first gate: every gate there is a subprocess that inherits the environment,
    so a value left in a shell - or exported by anything upstream - would turn every width law into a sample that
    still prints PASS."""
    env = os.environ if environ is None else environ
    return env.pop(ENV, None)


def banner(restricted, measured_by_law):
    """The line a restricted law prints first, so its output can never be read as a full sweep. -> str | None"""
    if restricted is None:
        return None
    law = set(tuple(y) for y in measured_by_law)
    unknown = [x for x in restricted if tuple(x) not in law]
    s = ("#42 %s=%s: this run measures %d of this law's %d viewports - a push-time red-proof, NEVER a verdict"
         % (ENV, label(restricted), len(restricted) - len(unknown), len(law)))
    if unknown:
        s += ("  ⚠ %s is a viewport this law NEVER measures, so nothing is measured there and a proof declared at it "
              "reads BLIND" % label(unknown))
    return s
