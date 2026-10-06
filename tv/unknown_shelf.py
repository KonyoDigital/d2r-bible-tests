# -*- coding: utf-8 -*-
"""#77 — ONE "UNKNOWN, not an empty shelf" PER SENTENCE, HOWEVER MANY LAYERS PASS IT UP.

Seen 2026-09-29 in BLUEPRINT.md generated on a tree with no footage: the river line read
"UNKNOWN — UNKNOWN, not an empty shelf — printer.stream() could not answer: UNKNOWN, not an empty shelf — UNKNOWN, not
an empty shelf — no reel reached this probe ...". Five readers (reel_river, per_reel_routes, one_funnel, printer,
reel_router) each prefixed the phrase to a reason that, one layer down, already carried it. The reason is right; the
stutter buries it. Every one of them now asks this one function, which leads with the phrase only when the reason
does not already carry the PHRASE. [[unknown-stays-unknown]] [[copy-drift]]

⚠⚠ REG-1512 (review of v3524) — THE PHRASE, NOT THE WORD. The first cut skipped the lead whenever the bare word
UNKNOWN appeared anywhere in the reason. But reasons say UNKNOWN about OTHER things: a lock ("printer.stream is
LOCKED — UNKNOWN: the proof queue would not parse") or the tombstone ledger ("... not a record — UNKNOWN, not zero
reels"). Reproduced with those two: printer.stream()'s why and reel_router.route()'s why carried the phrase ZERO
times, so no layer said the shelf was UNREAD rather than EMPTY, while the same refusal with a lock reason that
happened not to use the word still led with it — one refusal class, two framings. A reason that says UNKNOWN about a
lock has said nothing about the shelf. The suffix spelling extract_gap / reel_templates / river_walk write
("... — UNKNOWN, not an empty shelf") contains the phrase, so it is still never doubled.
"""

PHRASE = "UNKNOWN, not an empty shelf"
LEAD = PHRASE + " — "
DEFAULT = "no reel reached this probe and nothing said why"


def not_an_empty_shelf(why, default=DEFAULT):
    """-> the reason, led by LEAD exactly once. An empty reason becomes `default`, never an empty sentence."""
    w = str(why or "").strip() or default
    return w if PHRASE in w else LEAD + w


def says_unknown(why):
    """-> the reason, led by 'UNKNOWN — ' only when it does not already say UNKNOWN (the blueprint's shape)."""
    w = str(why or "").strip()
    return w if w.startswith("UNKNOWN") else "UNKNOWN — " + w


UNMEASURED = "UNMEASURED: "


def unmeasured(what, why=None, not_that=None):
    """-> 'UNMEASURED: <what> (<why>) — not <not_that>'. The one spelling of a check that could not read.

    REG-1824 — the journal readers wrote this sentence by hand five times, with two different dashes, so one failure
    read two ways. A `what` that already says UNMEASURED is not led twice; an empty `why` leaves no '()'."""
    w = str(what or "").strip() or "this was not read"
    if not w.startswith(UNMEASURED):
        w = UNMEASURED + w
    r = str(why or "").strip()
    if r:
        w += " (%s)" % r
    n = str(not_that or "").strip()
    return w + (" — not " + n if n else "")
