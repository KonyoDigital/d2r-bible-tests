# -*- coding: utf-8 -*-
"""v2732 — REBUILD A CHRONICLE FROM THE OTHER LEDGERS, RATHER THAN REPLAYING A COPY.

Konyo: *"lets do a rebuild/restore option for each chronicle that is ledger related.. progress date
whatever it needs to be"*, and then, when a snapshot was proposed: *"snap shot is not enough"*.

He was right, and the difference is the whole reason this module exists. A SAVE POINT restores THE
MOMENT — including whatever was already wrong at that moment. A REBUILD derives the chronicle from
independent evidence, so it repairs drift and corruption rather than replaying them.

⚠⚠ AND MY FIRST PROPOSAL FOR THIS WAS 11% OF A SOLUTION. I suggested rebuilding from
`d2r_gameFound`, the in-game Chronicle. MEASURED: it holds 29 keys against 169 owned — it would
have recovered NINETEEN of his items and I would have shipped it calling it a saviour. The real
answer needed every ledger at once. [[unknown-stays-unknown]]

=== WHAT IT ACTUALLY RECOVERS, MEASURED ON HIS REAL STORES ===
    owned                     169
    derivable from some store 167
    reachable from NOTHING      2   -> "Death Mask", "Black Cleft"
  provenance mix:
    evidence + foundLog                 130
    evidence + foundLog + gameFound      20
    foundLog                             13
    rwMade                                3
    foundLog + rwMade                     1

⚠ AN APOSTROPHE WAS HIDING ONE OF THEM IN THREE STORES AT ONCE. `d2r_owned` writes
"Saracen's Chance" with U+0027; foundLog, gameFound and the evidence ledger all use U+2019. An
exact-string join loses it entirely, and both this repo's earlier counts (t166's "8 with no log
row", my own "4 unreachable") were inflated by exactly that. Normalising is not cosmetic here — it
is the difference between "he has no record of this" and "he has three".

⚠ AND A PARENTHETICAL HID ANOTHER: owned carries "Crescent Moon (amulet)" and "Athena's Wrath (set
piece)"; the ledgers carry the bare name. The qualifier disambiguates on HIS screen and is not part
of the item's identity in any store.

=== ⚠⚠ WHAT THIS REBUILDS, AND WHAT IT MUST NEVER TRY TO ===
Konyo, on seeing the first cut: *"make sure to read the right one being tallied... right now my main
and fleet are reading 292/403 uniques and 123/135 sets. 99/99 runewordds"*. He was right and it
caught a real aim error:
    d2r_tally      uniques 292/403 · sets 123/135 · runewords 99/99   (matches his screen)
    d2r_setPieces  123 ✅        d2r_rwMade  99 ✅
    d2r_owned      169 ❌  <- the first cut rebuilt THIS. It is VAULT ownership, a different question.

⚠⚠ AND THE TALLY IS DERIVED, NOT STORED, SO THIS MODULE MUST NOT REPRODUCE IT. `funiScan()` computes
292 live. Reproducing it here (foundLog ∪ owned restricted to the unique roster) yields 298 — SIX
WRONG — because funiScan folds names with `_regKey` and honours the v2680 one-tally-per-sunder
ruling, and this module's `_norm` is a different fold. Shipping that would be a SECOND
implementation of the number he reads most, already wrong before it landed. [[copy-drift]]

So: THIS REBUILDS THE LEDGER STORES. The board recomputes the tally from them, exactly as it does
today. Verification is to ASK THE BOARD for its tally before and after — never to re-derive it here.
`owned` below is therefore whatever list the caller is rebuilding (d2r_owned for the vault,
d2r_setPieces for sets), and the caller says which; this module does not decide what "the chronicle"
means.

=== PER WORLD, ALWAYS ===
His clarification: *"for dean same logic make sure his is relative individually saving his consoles
data to his own ledgers and repair and everything all related to separately and individually"*.
This module is pure and takes the stores it is given, so it is per-world BY CONSTRUCTION — it can
only rebuild from what the caller hands it. ⚠ THE CALLER CARRIES THAT RESPONSIBILITY: stores must
come from ONE world's namespace (`window.LSR` already routes every d2r_* key: owner bare, ladder
`L·`, guest `I·<id8>·`, cousin `W·`). Mixing two worlds' stores into one call would merge two
people's chronicles, and nothing in here could detect it.

=== THE RULE THAT MAKES THIS A REBUILD AND NOT A GUESS ===
Sources disagree, and the disagreement is INFORMATION. Measured: "Crescent Moon" is dated
Aug 24 2026 in foundLog and Jun 22 2026 in rwMade — the first is when he ticked it, the second when
he forged it. A rebuild that silently picks one has invented history.
So every rebuilt row carries WHERE ITS VALUE CAME FROM, and every disagreement is REPORTED beside
it rather than resolved away. [[feedback-contradiction-is-the-finding]]

⚠⚠ THIS MODULE WRITES NOTHING. It returns a proposal. The console never writes the ledger — every
existing path (`board_tick`, `board_restore_dates`, `restore_ledger.py`) asks the BOARD to press
its own door, and anything built on this must do the same. A rebuild that could write would be a
second writer into his chronicle, which is the drift this repo keeps finding.
"""
import unicodedata

#: Which store answers "when", in order of authority, per kind of thing.
#: ⚠ rwMade FIRST for a runeword because it records the FORGE — the act itself. foundLog's date for
#: the same name is when it was ticked on the board, which is a different event and usually later.
#: gameFound outranks foundLog for everything else: it is the GAME's own record, written outside
#: this app entirely, and is the only source here that cannot be wrong because of an app bug.
DATE_AUTHORITY = {
    "runeword": ("rwMade", "gameFound", "foundLog"),
    "item":     ("gameFound", "foundLog", "rwMade"),
}

#: Stores this rebuild reads. Order is irrelevant — authority is decided above, per field.
SOURCES = ("foundLog", "gameFound", "rwMade", "evidence")


def _norm(s):
    """Fold the two things that hide a name from an exact join, and nothing else.

    ⚠ DELIBERATELY NARROW. Every extra fold is a chance to merge two items that are genuinely
    different, and a rebuild that merges two names loses one of them silently — worse than the
    miss it was trying to fix. Curly quotes and case only.
    """
    s = unicodedata.normalize("NFKC", str(s))
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"')):
        s = s.replace(a, b)
    return " ".join(s.split()).casefold()


def _base(s):
    """The name without its disambiguating qualifier: "Crescent Moon (amulet)" -> "crescent moon".

    ⚠ The qualifier lives in `d2r_owned` to tell HIM which of two things he means; no ledger stores
    it. Matching on it would lose the row it exists to describe.
    """
    return _norm(str(s).split(" (")[0])


def _date_of(val):
    """A store's value for a name -> its date string, or None. Shapes differ per store."""
    if isinstance(val, str):
        return val or None
    if isinstance(val, dict):
        for k in ("at", "date", "made", "ts"):
            v = val.get(k)
            if isinstance(v, str) and v:
                return v
    if isinstance(val, list) and val:
        for row in val:
            if isinstance(row, dict):
                for k in ("at", "date"):
                    v = row.get(k)
                    if isinstance(v, str) and v:
                        return v
    return None


_MONTHS = {m: i + 1 for i, m in enumerate(
    ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"))}


def _instant(d):
    """A date string from ANY of these stores -> (y, m, d, hh, mm), or None if unparseable.

    ⚠⚠ THIS EXISTS BECAUSE MY OWN CONFLICT DETECTOR CRIED WOLF ON ITS FIRST RUN. Comparing the raw
    strings reported TWENTY-ONE disagreements on his tree, and almost all of them were one instant
    in two formats:
        foundLog   "Aug 16, 2026 · 01:25"
        gameFound  "08/16/2026, 01:25"
    Same minute, different writer. A conflict list that is mostly formatting is a list nobody reads,
    and I filed a row about exactly that failure an hour before building one.
    ⚠ UNPARSEABLE STAYS None, and two Nones are NOT equal — an unreadable date is not agreement.
    [[unknown-stays-unknown]] [[feedback-suspect-the-instrument]]
    """
    import re
    t = str(d or "").strip()
    if not t:
        return None
    # "Aug 16, 2026 · 01:25"  /  "Jun 22, 2026 · 01:35"
    m = re.match(r"([A-Za-z]{3})[a-z]*\s+(\d{1,2}),\s*(\d{4})(?:\D+(\d{1,2}):(\d{2}))?", t)
    if m and m.group(1).lower() in _MONTHS:
        return (int(m.group(3)), _MONTHS[m.group(1).lower()], int(m.group(2)),
                int(m.group(4) or 0), int(m.group(5) or 0))
    # "08/16/2026, 01:25"
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})(?:\D+(\d{1,2}):(\d{2}))?", t)
    if m:
        return (int(m.group(3)), int(m.group(1)), int(m.group(2)),
                int(m.group(4) or 0), int(m.group(5) or 0))
    return None


def _index(stores):
    """name-key -> {source: (original_key, value)}. Both the full and the bare name are indexed."""
    idx = {}
    for src in SOURCES:
        store = stores.get(src)
        if not isinstance(store, dict):
            continue                      # absent or unreadable — the caller is told separately
        for k, v in store.items():
            for key in (_norm(k), _base(k)):
                idx.setdefault(key, {}).setdefault(src, (k, v))
    return idx


def rebuild(owned, stores):
    """Derive each owned name's record from the OTHER stores. -> dict. Writes nothing.

    `owned`  : the list of names he owns (d2r_owned)
    `stores` : {"foundLog": {...}, "gameFound": {...}, "rwMade": {...}, "evidence": {...}}
               A source that is absent or unreadable must be passed as None, NOT as {} — the two
               are different facts and this refuses to collapse them.
    """
    missing_src = [s for s in SOURCES if stores.get(s) is None]
    if not isinstance(owned, (list, tuple)):
        return {"ok": False, "why": "the owned list is %s, not a list — nothing was derived"
                                    % type(owned).__name__}
    if len(missing_src) == len(SOURCES):
        return {"ok": False, "why": "not one source store could be read, so nothing about his "
                                    "chronicle can be established — UNKNOWN, not empty"}

    idx = _index(stores)
    rows, unreachable, conflicts = {}, [], []
    for name in owned:
        if not isinstance(name, str) or not name.strip():
            continue
        found = idx.get(_norm(name)) or idx.get(_base(name)) or {}
        if not found:
            # ⚠ NAMED, NEVER COUNTED. "2 items could not be recovered" is not actionable; the two
            # NAMES are. This is the list he would have to re-enter by hand, and it is the whole
            # argument for a save point existing beside this.
            unreachable.append(name)
            continue
        kind = "runeword" if "rwMade" in found else "item"
        order = DATE_AUTHORITY[kind]
        dates = {}
        for src, (orig, val) in found.items():
            d = _date_of(val)
            if d:
                dates[src] = d
        chosen_src = next((s for s in order if s in dates), None)
        # ⚠ COMPARE INSTANTS, NOT SPELLINGS. See _instant: the raw-string version of this test
        # reported 21 conflicts on his tree and most were "Aug 16, 2026 · 01:25" against
        # "08/16/2026, 01:25" — the same minute written by two different stores.
        _inst = {}
        for _s, _d in dates.items():
            _i = _instant(_d)
            _inst[_s] = _i if _i is not None else ("UNPARSEABLE", _d)
        distinct = {repr(x) for x in _inst.values()}
        if len(distinct) > 1:
            # ⚠ REPORTED, NOT RESOLVED AWAY. Measured on his tree: "Crescent Moon" is Aug 24 in
            # foundLog and Jun 22 in rwMade — ticked versus forged. Both are true about different
            # events, and picking one silently would invent a history he never had.
            conflicts.append({"name": name, "dates": dict(dates), "took": chosen_src})
        rows[name] = {
            "date": dates.get(chosen_src) if chosen_src else None,
            "from": chosen_src,
            "kind": kind,
            "backedBy": sorted(found),
            "dates": dict(dates),
        }
    return {
        "ok": True,
        "rows": rows,
        "recovered": len(rows),
        "owned": len([n for n in owned if isinstance(n, str) and n.strip()]),
        "unreachable": unreachable,
        "conflicts": conflicts,
        "sourcesMissing": missing_src,
        "why": ("%d of %d name(s) derived from %d source(s); %d unreachable%s"
                % (len(rows), len([n for n in owned if isinstance(n, str) and n.strip()]),
                   len(SOURCES) - len(missing_src), len(unreachable),
                   ("; %d carry conflicting dates" % len(conflicts)) if conflicts else "")),
    }
