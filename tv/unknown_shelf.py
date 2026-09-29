# -*- coding: utf-8 -*-
"""#77 — ONE "UNKNOWN, not an empty shelf" PER SENTENCE, HOWEVER MANY LAYERS PASS IT UP.

Seen 2026-09-29 in BLUEPRINT.md generated on a tree with no footage: the river line read
"UNKNOWN — UNKNOWN, not an empty shelf — printer.stream() could not answer: UNKNOWN, not an empty shelf — UNKNOWN, not
an empty shelf — no reel reached this probe ...". Five readers (reel_river, per_reel_routes, one_funnel, printer,
reel_router) each prefixed the phrase to a reason that, one layer down, already carried it. The reason is right; the
stutter buries it. Every one of them now asks this one function, which leads with the phrase only when the reason
does not already say UNKNOWN. [[unknown-stays-unknown]] [[copy-drift]]
"""

LEAD = "UNKNOWN, not an empty shelf — "
DEFAULT = "no reel reached this probe and nothing said why"


def not_an_empty_shelf(why, default=DEFAULT):
    """-> the reason, led by LEAD exactly once. An empty reason becomes `default`, never an empty sentence."""
    w = str(why or "").strip() or default
    return w if "UNKNOWN" in w else LEAD + w


def says_unknown(why):
    """-> the reason, led by 'UNKNOWN — ' only when it does not already say UNKNOWN (the blueprint's shape)."""
    w = str(why or "").strip()
    return w if w.startswith("UNKNOWN") else "UNKNOWN — " + w
