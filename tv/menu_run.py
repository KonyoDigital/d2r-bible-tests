"""A stash is never in alphabetical order. A menu page always is.

WHY THIS EXISTS. Konyo, 2026-08-31, looking at 134 items in his vault's UNSORTED DOCK:
*"all these items are not my vault somethng is properly coded"*. He was right, and the proof
needed no AI, no template matching and no pixels - only the ORDER of the names:

    Iron Pelt, Ironstone, Islestrike, Kinemil's Awl, Lance Guard, Lance of Yaggai,
    Langer Briser, Leadcrow, Magewrath, Medusa's Gaze, Moonfall, Nord's Tenderizer, ...

Measured against his 398-name unique roster: **46 of 46 consecutive steps strictly ascending -
100%** - spanning roster positions 175..397 with a median gap of 3. That is the uniques Chronicle
read from about the letter I to Z, admitted into the vault as possessions.

**A container holds what he happened to find. A menu lists what exists, in order.** Items land in
a stash in the order he picked them up and moved them; the chance that 47 of them come out
alphabetically ascending is nil. So monotonic order is not weak evidence about the SOURCE of a
batch - it is nearly conclusive, and it is free.

⚠ THIS JUDGES A BATCH, NEVER A NAME. One item is not a run; two ascending items are a coin flip.
The signal only exists at size, which is why `looks_like_a_menu_page` takes a LIST and refuses to
answer for anything under MIN_RUN. A per-name verdict derived from this would be superstition.
[[unknown-stays-unknown]] [[d2r-vault-routing]]
"""

MIN_RUN = 8          # below this, ascending order is luck
STRONG = 0.90        # ascending fraction at or above this: a menu, essentially certainly
WEAK = 0.70          # between: suspicious, worth a second witness


def _positions(names, roster_sorted):
    """Roster index for each recognisable name, in the order given. Unknown names are DROPPED,
    not zeroed - a misread that is not in the roster says nothing about ordering."""
    idx = {n.strip().lower(): i for i, n in enumerate(roster_sorted)}
    out = []
    for n in (names or []):
        if not isinstance(n, str):
            continue
        p = idx.get(n.strip().lower())
        if p is not None:
            out.append(p)
    return out


def ascending_fraction(names, roster):
    """-> (fraction|None, matched, why). None means NOT ESTABLISHED - too few known names."""
    roster_sorted = sorted({str(r).strip() for r in (roster or []) if str(r).strip()},
                           key=lambda x: x.lower())
    pos = _positions(names, roster_sorted)
    if len(pos) < MIN_RUN:
        return None, len(pos), ("only %d of these names are in the roster - below the %d needed "
                                "for order to mean anything" % (len(pos), MIN_RUN))
    steps = list(zip(pos, pos[1:]))
    up = sum(1 for a, b in steps if b > a)
    return (up / float(len(steps))), len(pos), "%d of %d steps ascend" % (up, len(steps))


def looks_like_a_menu_page(names, roster):
    """Did this BATCH come off a menu rather than out of a container? -> (verdict, why)

    verdict is True / False / None, and None means NOT ESTABLISHED. It is never a licence to
    delete anything on its own - it is a witness, and the vault has other doors.
    """
    frac, matched, why = ascending_fraction(names, roster)
    if frac is None:
        return None, why
    if frac >= STRONG:
        return True, ("%s (%.0f%% ascending across %d roster names) - a stash is not sorted, a "
                      "menu is" % (why, frac * 100, matched))
    if frac >= WEAK:
        return None, ("%s (%.0f%%) - suspicious but not conclusive; wants a second witness"
                      % (why, frac * 100))
    return False, "%s (%.0f%% ascending) - not menu-ordered" % (why, frac * 100)


def longest_ascending_run(names, roster):
    """The longest strictly-ascending stretch, for showing him WHICH names look imported."""
    roster_sorted = sorted({str(r).strip() for r in (roster or []) if str(r).strip()},
                           key=lambda x: x.lower())
    idx = {n.strip().lower(): i for i, n in enumerate(roster_sorted)}
    best, cur = [], []
    for n in (names or []):
        p = idx.get(str(n).strip().lower()) if isinstance(n, str) else None
        if p is None:
            continue
        if cur and p > cur[-1][1]:
            cur.append((n, p))
        else:
            cur = [(n, p)]
        if len(cur) > len(best):
            best = list(cur)
    return [n for n, _ in best]


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    import io as _io, json as _json, os as _os, sys as _sys
    here = _os.path.dirname(_os.path.abspath(__file__))
    rost = _json.load(_io.open(_os.path.join(here, "unique_roster.json"), encoding="utf-8"))
    roster = rost.get("names") or []
    names = _sys.argv[1:]
    if not names:
        print("usage: menu_run.py <name> <name> ...")
        raise SystemExit(0)
    v, why = looks_like_a_menu_page(names, roster)
    print("menu page: %s" % v)
    print("  %s" % why)
