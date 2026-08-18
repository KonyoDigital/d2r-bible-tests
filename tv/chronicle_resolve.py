"""Fold a reader's raw name onto the board's own unique roster — BEFORE the gate counts witnesses.

WHY THIS EXISTS, in the words of the measurement that produced it (2026-08-18).

His inbox held 36 chronicle names waiting for a hand-tick. Read one by eye and the queue's real
shape appeared: only SIX were unresolved uniques. Six more were OCR slips of items ALREADY
grounded — "Battlecage" for `Rattlecage`, "Naglring" for `Nagelring`, "Heart Garver" for
`Heart Carver`, "Twitchthrow" for `Twitchthroe`, "Gravepalms" for `Gravepalm` — the same row read
twice, once right and once wrong, carrying zero new information. The remaining 24 were reader
debris: base item names the Chronicle prints for an UNFOUND row (`Bone Visage`, `Templar Coat`,
`Wrist Sword`), and truncations where a tooltip covered the text (`Firel...`, `Natalya's...`,
`Heavas (partially obscured)`).

Two defects follow from that, and both live HERE rather than in the gate:

1. THE GATE COUNTED WITNESSES ON RAW STRINGS, so two spellings of one item never combined. Folding
   first grounded `Atma's Scarab`, `Black Cleft` and `Saracen's Chance` under the roster's own
   spelling — no threshold moved, no evidence was invented, the sightings simply found each other.

2. A GROUNDED NAME THAT IS NOT A ROSTER NAME CAN NEVER TICK. The ledger held `Latent Black Cleft`;
   the roster holds `Black Cleft`; `d2rResolveItem('Latent Black Cleft')` returns it UNCHANGED
   (verified live over CDP). So the reel found the item, the ledger grounded it, and the board
   could not count it — the-unjoined-end, silent by construction. After folding, every grounded
   name is a roster name; that invariant is now a test.

THE ROSTER HAS ONE SOURCE: `bible.html`'s own `window._gUniqueRoster()`. This module reads a
GENERATED artifact (`unique_roster.json`), never its own re-derivation of the rule — re-deriving
"ITEM_VALUE ∪ _UNI_EXTRA minus set pieces" in Python would be a second implementation of a rule
that already exists, which is exactly `copy-drift`. `roster_sync.py` regenerates the artifact and
stamps the source hash; `test_control.py` fails when bible.html's roster blocks move.

WHAT IT REFUSES TO DO. A name that resolves to nothing is RETIRED, not dropped: it lands in the
report with its reason. "We looked and it was not a grail item" and "nobody looked" must never
read the same — an unresolvable name that vanished silently would be a fabrication in the shape
of a tidy queue.
"""

import difflib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROSTER_PATH = os.path.join(HERE, "unique_roster.json")
SET_ROSTER_PATH = os.path.join(HERE, "set_roster.json")

# NO QUALITY-PREFIX STRIPPING, and the reason is the whole lesson of this module.
#
# "Latent Cold Rupture" LOOKS like a quality roll prefixed onto "Cold Rupture", and the first cut of
# this file stripped it. Then the roster was asked instead of assumed, and it carries BOTH forms as
# separate grail entries — all six of them:
#
#   Latent Black Cleft / Black Cleft            Latent Cold Rupture / Cold Rupture
#   Latent Bone Break  / Bone Break             Latent Crack of the Heavens / Crack of the Heavens
#   Latent Flame Rift  / Flame Rift             Latent Rotting Fissure / Rotting Fissure
#
# Those are TWELVE roster slots, not six. Stripping the prefix merged each pair, which would have
# credited him with an item he had not found and quietly deleted the other from his hunt list. It
# also produced a false diagnosis on the way past: a grounded "Latent Black Cleft" was reported as
# unable to tick, when it is a roster name in perfectly good standing.
#
# The roster is the authority on what is one item and what is two. A fold rule may only ever fold
# names the roster does not distinguish.

# 0.86 was chosen against his own data, not picked for looking safe. At this cutoff all five real
# OCR slips fold ("battlecage"->"rattlecage" .90, "naglring"->"nagelring" .94) and no debris name
# reaches a roster item. Lowering it to 0.80 pulls "the dragon" onto "the dragon chang", which is a
# GUESS about which item he saw; a wrong fold writes a find he never made, so this stays tight and
# an unfoldable name stays unknown.
NEAR_CUTOFF = 0.86

# The runner-up must be this much worse than the winner, or the fold is a guess. Measured on his
# ledger: every one of the five real OCR slips clears it comfortably, and nothing new folds.
AMBIGUITY_GAP = 0.04


def _norm(s):
    """Case/punctuation fold. Mirrors bible.html's `_norm` on the parts that matter here (case and
    non-letters), plus the parenthetical the reader adds for its own uncertainty."""
    s = str(s or "").replace("’", "'").lower()
    # the reader parenthesises its OWN uncertainty ("The Dragon Chang(?)"); that is a note about the
    # read, never part of the name
    s = re.sub(r"\s*\([^)]*\)\s*", " ", s)
    return re.sub(r"[^a-z]", "", s.strip())


def load_roster(path=None):
    """The roster as {normalised: canonical}. Raises rather than returning {} — an empty roster
    would silently classify every name as debris and retire his entire queue, which is the loudest
    possible failure wearing the quietest possible face."""
    p = path or ROSTER_PATH
    with open(p, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    names = doc.get("names") or []
    if not names:
        raise ValueError("unique_roster.json holds no names — refusing to fold against an empty roster")
    out = {}
    collisions = {}
    for n in names:
        k = _norm(n)
        if k in out and out[k] != n:
            collisions.setdefault(k, [out[k]]).append(n)
        out.setdefault(k, n)
    if collisions:
        # A fold rule that maps two DISTINCT roster items onto one key would silently pick a winner
        # and credit him with an item he never found. That must be a crash, not a preference — this
        # is precisely how the quality-prefix rule nearly merged six real pairs.
        raise ValueError("fold rule collapses distinct roster items: %s" % collisions)
    return out


def load_set_roster(path=None):
    """The SET-PIECE roster as {normalised: canonical}, canonical being the SUFFIXED ledger form.

    v1795 — sets get the same treatment as uniques, which is the whole point: one architecture, two
    ledgers. Pieces are stored suffixed ("Tal Rasha's Adjudication (amulet)") because that is what
    d2r_setPieces holds, while the in-game Chronicle row prints the BARE name. `_norm` already strips
    the parenthetical, so both collapse to one key and the canonical stays the suffixed form.

    Measured on the real catalogue before this was relied on (2026-08-18): 135 pieces produce 135
    DISTINCT keys, and ZERO of those keys also match a unique roster name. So a name cannot be both a
    unique and a set piece, and the two ledgers can be folded independently without leaking into each
    other. Both facts are pinned by tests — either one silently becoming false would let a set piece
    land in his grail tally, which is the exact harm the uniques fold was built to prevent.
    """
    p = path or SET_ROSTER_PATH
    with open(p, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    pieces = doc.get("pieces") or []
    if not pieces:
        raise ValueError("set_roster.json holds no pieces — refusing to fold against an empty roster")
    out = {}
    collisions = {}
    for n in pieces:
        k = _norm(n)
        if k in out and out[k] != n:
            collisions.setdefault(k, [out[k]]).append(n)
        out.setdefault(k, n)
    if collisions:
        raise ValueError("fold rule collapses distinct set pieces: %s" % collisions)
    return out


def canonical(name, roster):
    """Roster name for `name`, or None. Exact fold first, then ONE near match above NEAR_CUTOFF."""
    k = _norm(name)
    if not k:
        return None
    if k in roster:
        return roster[k]
    # Two candidates that score within AMBIGUITY_GAP of each other is not a near miss, it is a coin
    # flip between two of his grail items — and the roster deliberately holds near-twin pairs
    # ("Bone Break" / "Latent Bone Break"). An ambiguous fold stays UNFOLDED and reaches him as an
    # open question, because guessing here writes a find he never made.
    m = difflib.get_close_matches(k, list(roster), n=2, cutoff=NEAR_CUTOFF)
    if not m:
        return None
    if len(m) > 1:
        best = difflib.SequenceMatcher(None, k, m[0]).ratio()
        runner = difflib.SequenceMatcher(None, k, m[1]).ratio()
        if best - runner < AMBIGUITY_GAP:
            return None
    return roster[m[0]]


def classify(name, roster, grounded=()):
    """-> (verdict, canonical). 'duplicate' means it folds onto something ALREADY grounded, so it
    is a second reading of a row that is already counted — retire it, and never re-ask him."""
    c = canonical(name, roster)
    if c is None:
        return "debris", None
    if c in set(grounded or ()):
        return "duplicate", c
    return "real", c


def fold_proposal(proposal, roster, grounded=(), ledgers=("uniques",), set_roster=None):
    """Fold a proposal's sightings onto canonical roster names before the gate sees them.

    Only `uniques` is folded by default: the roster IS the unique roster, and folding a set piece
    or a complete-set claim against it would answer a question this artifact cannot answer.

    Returns (folded_proposal, report). The report is the receipt — `retired` names every string
    that left the queue and why, so a shrunken inbox stays explainable.
    """
    folded = dict(proposal or {})
    report = {"folded": {}, "retired": [], "kept": 0}
    grounded = set(grounded or ())
    # v1795 — SETS FOLD AGAINST THEIR OWN ROSTER. Folding a set piece against the UNIQUE roster would
    # be asking the wrong catalogue a question it cannot answer: every piece would resolve to nothing
    # and be retired as debris, silently emptying the sets ledger. Which roster answers is chosen by
    # the ledger being folded, never shared.
    for ledger in ledgers:
        active = set_roster if (ledger == "sets" and set_roster is not None) else roster
        src = (proposal or {}).get(ledger) or {}
        merged = {}
        for raw, sightings in src.items():
            verdict, c = classify(raw, active, grounded)
            if verdict != "real":
                report["retired"].append({"name": raw, "why": verdict, "resolvesTo": c})
                continue
            if c != raw:
                report["folded"][raw] = c
            merged.setdefault(c, []).extend(sightings or [])
        folded[ledger] = merged
        report["kept"] += len(merged)
    return folded, report
