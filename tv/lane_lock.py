"""ONE KEY. What is on screen decides which lane may write, and every other lane is LOCKED.

Konyo: "when i click ESC and im in the main menu ingame and then i click CHRONICLE... and then when im
obviously in the chronicle template it should obivously and logically know and understand to focus
automaticlaly on chronicle and any item it sees there has nothing to do with the vault manager ... so
either UNIQUES or SETS or RUNEWORDS ... something should switch on and off some sort of engine or key
like that unlocks or locks ... its kinda simple."

It is simple, and the signal already existed: `claude_read` returns BOTH `stashTab` and `chronicleTab`
on every frame. What did not exist was one place that turns them into a single decision. Each lane
guarded itself instead — vault_retro's `_surface_of` refuses a non-ownership verdict, the chronicle
prompt sets `wrongTab` — which is two correct guards that never compare notes, so nothing could state
what the frame IS, only what each lane individually declined.

THE LAW: AT MOST ONE LANE IS EVER UNLOCKED.

    stash / inventory / equipment / runes / gems / materials  →  the VAULT lane
    chronicle uniques / sets / runewords                      →  that ONE chronicle ledger
    anything else, or BOTH at once, or unreadable             →  nothing is unlocked

The "both at once" case is the one worth being strict about, and it is why this returns None instead of
picking. A frame that looks like a stash AND a chronicle page is a frame nobody has correctly
identified — and the cost of choosing wrong is not symmetrical: a Chronicle row filed as OWNERSHIP
claims he owns an item he has merely seen listed, and a stash item filed as a Chronicle FIND ticks a
grail row he never earned. Both are permanent-feeling writes made from a guess. Locking costs one
unread page; guessing costs the truth of his ledger.

MEASURED, on his own frames, before this file was trusted (2026-08-18): the pixel-level
`classify_stash_grid` calls a real CHRONICLE page "stash", and `_panel_open_from_features` agrees it is
an open panel — frac_dark 0.5364, 11 dark columns, both inside the stash thresholds. Only the AI
classifier gets it right (`scene: transition`, `stashTab: ''`). So a cheap pixel gate is NOT enough to
decide this, and that is exactly why the decision lives in one audited place rather than being
re-derived per lane.
"""

# v1999 — PERSONAL AND SHARED WERE MISSING, AND THEY ARE TWO OF THE FIVE REAL TAB NAMES.
# This tuple is matched against the reader's `stashTab`, and tv_diablo.py:259 says exactly what that
# field carries: "RotW left tabs: Personal·Shared·Gems·Materials·Runes". Three of the five happened
# to overlap; `personal` and `shared` — the two he is in most often — did not, so a frame claiming
# BOTH a personal stash and a chronicle tab was not seen as ambiguous and the lock stayed open on
# precisely the case it exists for. Measured: chronicle_kind({scene:'chronicle',
# chronicleTab:'uniques', stashTab:'personal'}) returned 'chronicle-uniques' before this line.
# A vocabulary that does not match its input is a gate blind to the data it grades.
# [[gate-blind-to-unexercised-input]]
VAULT_SURFACES = ("stash", "inventory", "equipment", "runes", "gems", "materials")
# The five names the reader actually puts in `stashTab` are the RotW LEFT TABS
# (tv_diablo.py:259 — "Personal·Shared·Gems·Materials·Runes"). Three overlap with the surfaces
# above; `personal` and `shared` did not, so a frame claiming BOTH a personal stash and a chronicle
# tab was not seen as ambiguous and the lock stayed open on precisely the case it exists for.
# They are FOLDED to "stash" rather than added as surfaces of their own, because `surface` is
# compared against vault_retro.LANES ("stash","inventory","equipment") and a lane named "personal"
# would be a value no consumer knows. Recognise the input, keep the output vocabulary.
_TAB_TO_SURFACE = {"personal": "stash", "shared": "stash"}
CHRONICLE_LEDGERS = ("uniques", "sets", "runewords")

VAULT = "vault"
CHRONICLE = "chronicle"


def _clean(v):
    return str(v or "").strip().lower()


def _vault_surface(verdict):
    """The ownership surface this frame shows, or None. Reads `stashTab` first because that is the
    field the classifier fills when a stash tab is actually open, then falls back to the scene."""
    if not isinstance(verdict, dict):
        s = _clean(verdict)
        return s if s in VAULT_SURFACES else None
    for key in ("surface", "stashTab", "scene", "kind"):
        s = _clean(verdict.get(key))
        s = _TAB_TO_SURFACE.get(s, s)
        if s in VAULT_SURFACES:
            return s
    return None


def _chronicle_ledger(verdict):
    """The chronicle ledger this frame shows, or None. `chronicleTab` is the field that names which
    tab he clicked — uniques, sets or runewords — and it is empty on every non-chronicle frame."""
    if not isinstance(verdict, dict):
        s = _clean(verdict)
        s = s.split("chronicle-")[-1] if "chronicle-" in s else s
        return s if s in CHRONICLE_LEDGERS else None
    for key in ("chronicleTab", "ledger", "chronicle"):
        s = _clean(verdict.get(key))
        s = s.split("chronicle-")[-1] if "chronicle-" in s else s
        if s in CHRONICLE_LEDGERS:
            return s
    s = _clean(verdict.get("scene"))
    if s.startswith("chronicle-"):
        s = s.split("chronicle-")[-1]
        if s in CHRONICLE_LEDGERS:
            return s
    return None


def lane_for(verdict):
    """-> {"lane": "vault"|"chronicle"|None, "surface": str|None, "ledger": str|None, "why": str}

    The ONLY function allowed to answer "what may this frame write to". Returns lane=None whenever the
    answer is not unambiguous, and the `why` says which of the three reasons it was, because "locked
    because it is gameplay" and "locked because two panels claim it" are different facts and a caller
    that cannot tell them apart cannot report honestly.
    """
    surface = _vault_surface(verdict)
    ledger = _chronicle_ledger(verdict)

    if surface and ledger:
        return {"lane": None, "surface": None, "ledger": None,
                "why": "AMBIGUOUS — this frame claims both a %s panel and the chronicle %s tab; "
                       "nothing is unlocked, because choosing wrong writes a find he never made"
                       % (surface, ledger)}
    if surface:
        return {"lane": VAULT, "surface": surface, "ledger": None,
                "why": "the %s panel is open — the VAULT lane is unlocked, the chronicle is locked"
                       % surface}
    if ledger:
        return {"lane": CHRONICLE, "surface": None, "ledger": ledger,
                "why": "the chronicle %s tab is open — that ONE ledger is unlocked, the vault is "
                       "locked" % ledger}
    return {"lane": None, "surface": None, "ledger": None,
            "why": "no ownership panel and no chronicle tab — nothing is unlocked"}


def may_write(verdict, lane, ledger=None):
    """Ask before writing. `lane` is 'vault' or 'chronicle'; `ledger` narrows the chronicle case.

    A chronicle write must name WHICH ledger, because unlocking "the chronicle" is not enough: the
    uniques tab must never tally a set piece and the reverse, which is the same rule the reader's own
    `wrongTab` flag exists for — stated once here so both halves cannot drift apart.
    """
    v = lane_for(verdict)
    if v["lane"] != lane:
        return False, v["why"]
    if lane == CHRONICLE and ledger is not None and v["ledger"] != ledger:
        return False, ("the chronicle %s tab is open, not %s — a row read here belongs to %s"
                       % (v["ledger"], ledger, v["ledger"]))
    return True, v["why"]
