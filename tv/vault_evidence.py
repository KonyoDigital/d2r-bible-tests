# -*- coding: utf-8 -*-
"""What a vault reset may put back, and only from evidence.

His ruling 2026-09-27: a reset clears the marks. An item comes back when its own looks prove it,
Wilson-style, or when it is the kind of thing that does not vanish by itself (equipped on the main
character, a sunder, Annihilus, Hellfire Torch, Gheed's). One tier table. The bound is
confidence.wilson_lower, not a second copy of that sum.

tier() and rebuild_plan() decide. plan_from_ledger() only reads a ledger the caller names and
turns its rows into that shape. It does not write the ledger and it does not file a mark.

A trial is a distinct VISIT, never a frame (his ruling 2026-09-28, §34.2): _measure counts the
re-look buckets vault_retro.gate counts, folded the same way. retro_plan() names every item
filed on a tier higher than its visits earn; it keeps them filed and never writes.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import confidence as _confidence

# The vault-apply bar already measured in this tree. 10 successes in 10 trials lands on it.
# A perfect 9 trials is 0.701, under that bar, so "under 10" and the bar agree on every
# perfect record. The trial floors still decide hardened, and a record with misses.
WILSON_BAR = 0.722
TRIALS_PROVEN = 10
TRIALS_HARDENED = 20
WATCHED, PROVEN, HARDENED = "WATCHED", "PROVEN", "HARDENED"

# Items that do not disappear because a stash was sorted. They are rebuilt even below the bar.
KEPT_KINDS = frozenset(("sunder", "annihilus", "torch", "gheed"))
# The `why` a retro-flagged WATCHED row is filed back with. The board's door (bible.html,
# window.vaultFile's rebuild branch) admits it by its flag and keepFiled, and stores this beside it.
RETRO_KEPT_WHY = "kept filed by his ruling (§34.2)"
# How many qualifying looks (distinct visits that saw it) a retro-flagged row needs to be KEPT
# filed. His ruling §34.2 keeps a row that was filed before; one real look is something to keep it
# filed ON. Zero is not: the plan holds that row, with RETRO_NO_LOOK_WHY, and never promises
# keepFiled. The board's door reads the same number (bible.html VAULT_RETRO_KEEP_MIN) and admits a
# keepFiled retro row on it instead of the 2-look bar (Ledger fix round 2, finding B).
RETRO_KEEP_MIN_LOOKS = 1
RETRO_NO_LOOK_WHY = ("flagged retro, but no visit saw it (0 qualifying looks: a look needs its own "
                     "frame and its own conf at the floor) — there is nothing to keep it filed on, "
                     "so it is held until one real look lands")


def tier(successes, trials):
    """-> {tier, bound, successes, trials, why}. tier is None when the counts cannot be read."""
    try:
        k = int(successes)
        n = int(trials)
    except (TypeError, ValueError):
        return {"tier": None, "bound": None, "successes": None, "trials": None,
                "why": "the look counts could not be read, so the tier is UNKNOWN"}
    if n < 0 or k < 0:
        return {"tier": None, "bound": None, "successes": None, "trials": None,
                "why": "a negative look count is not a measurement"}
    if k > n:
        # 2026-09-28 second eye (v3520, 4877464e): this clamped k to n, so 15 sightings over 10 looks scored as a
        # PERFECT 10/10 and could clear the bar. More successes than trials means the two counts were taken in
        # different units (frames against visits) - that is not a measurement of this item, so it is UNKNOWN.
        return {"tier": None, "bound": None, "successes": None, "trials": None,
                "why": "more sightings (%d) than looks (%d) - the two counts are not in the same unit, so the "
                       "tier is UNKNOWN" % (k, n)}
    bound = _confidence.wilson_lower(k, n)
    if n < TRIALS_PROVEN or bound < WILSON_BAR:
        name = WATCHED
    elif n >= TRIALS_HARDENED:
        name = HARDENED
    else:
        name = PROVEN
    return {"tier": name, "bound": bound, "successes": k, "trials": n, "why": ""}


def rebuild_plan(items):
    """Which cleared marks come back. `items` is the evidence already in hand, not a file.

    Each item is {name, successes, trials} and may say equipped=True or kind= one of KEPT_KINDS.
    A WATCHED item stays cleared. PROVEN is re-filed. HARDENED is re-filed and locked.
    An equipped item or a kept kind comes back even below the bar, and says why.

    An item may also carry retro="retro: <TIER>" — the flag retro_plan / _retro_row give an item
    filed above what its visits earn. HIS RULING 2026-09-28 (§34.2), his words: "Keep filed, flag
    'retro: WATCHED'". So a flagged item is rebuilt at its TRUE tier, never locked above it, with
    the flag and keepFiled beside it, even when that tier is WATCHED. It stays kept-filed on every
    later reset for as long as the ledger still flags it; real looks lift it to PROVEN/HARDENED.

    2026-09-28 (Ledger fix round 2, finding B): keepFiled is a promise the board's door must be
    able to keep. The door admits a keepFiled retro row on RETRO_KEEP_MIN_LOOKS (one) qualifying
    look. A flagged WATCHED row with ZERO qualifying looks has nothing to be filed on, so it is
    HELD with RETRO_NO_LOOK_WHY and its flag — never promised keepFiled.
    """
    rebuilt, held = [], []
    if not isinstance(items, list):
        return {"ok": False, "rebuilt": [], "held": [],
                "why": "the evidence could not be read, so nothing is rebuilt and nothing is called empty"}
    for it in items:
        if not isinstance(it, dict) or not it.get("name"):
            continue
        got = tier(it.get("successes"), it.get("trials"))
        row = {"name": it["name"], "tier": got["tier"], "bound": got["bound"],
               "successes": got["successes"], "trials": got["trials"]}
        if "rarity" in it:
            # #51 — what the item IS rides on every row, rebuilt or held: the board's door reads it
            # to send a magic or rare row to the MAGIC & RARE locker. None stays None (UNKNOWN).
            row["rarity"] = it.get("rarity")
            row["rarityBy"] = it.get("rarityBy")
        kept = bool(it.get("equipped")) or str(it.get("kind") or "") in KEPT_KINDS
        retro = it.get("retro") if isinstance(it.get("retro"), str) else ""
        if not retro.startswith("retro: "):
            retro = ""           # only the flag _retro_row mints; any other string is not his ruling
        if got["tier"] is None:
            row["why"] = got["why"]
            held.append(row)
        elif got["tier"] == WATCHED and not kept and not retro:
            row["why"] = "below the proven bar"
            held.append(row)
        elif got["tier"] == WATCHED and not kept and got["successes"] < RETRO_KEEP_MIN_LOOKS:
            row["why"] = RETRO_NO_LOOK_WHY
            row["flag"] = retro
            row["keepFiled"] = False
            held.append(row)
        else:
            row["locked"] = got["tier"] == HARDENED
            if kept and got["tier"] == WATCHED:
                row["why"] = "kept kind"
            elif retro and got["tier"] == WATCHED:
                row["why"] = RETRO_KEPT_WHY
            else:
                row["why"] = got["tier"]
            if retro:
                row["flag"] = retro
                row["keepFiled"] = True
            rebuilt.append(row)
    return {"ok": True, "rebuilt": rebuilt, "held": held, "why": ""}


_UNREAD = ("the witness ledger could not be read, so nothing is rebuilt "
           "and nothing is called empty")
# Where his MAIN carries a thing. The same places the filing door refuses as a mule witness.
_MAIN_LANES = frozenset(("equipment", "equipped", "inventory", "belt", "cube"))


def _unread(why=None):
    return {"ok": False, "rebuilt": [], "held": [], "retro": None, "why": why or _UNREAD}


def _conf_floor():
    """The look floor the vault gate already uses. None when that module cannot be read."""
    try:
        import vault_retro as VR
        return float(VR.KEEP_CONF_FLOOR)
    except Exception:
        return None


def _kind_of(rows):
    for row in rows:
        kind = str(row.get("kind") or "").strip().lower()
        if kind in KEPT_KINDS:
            return kind
    name = str(rows[0].get("name") or "").lower()
    for kind in sorted(KEPT_KINDS):
        if kind in name:
            return kind
    return ""


def _equipped_of(rows):
    for row in rows:
        if row.get("equipped") is True:
            return True
        if str(row.get("lane") or "").strip().lower() in _MAIN_LANES:
            return True
    return False


# ══ #51 — MAGIC (blue) AND RARE (gold) STAND ON THE SAME LOOKS AS A UNIQUE ═══════════════════════
# His ask 2026-09-28: witnessed looks, Wilson tiers, a rebuild after a reset, clickable evidence
# pictures and tallies for magic and rare items, the way uniques already get them. MEASURED before
# this was written: every look has carried `quality` since v3369 (vault_retro.normalize_item puts
# it on the sighting, _witness_rows banks it), and this table grouped the rows by NAME and read
# none of it — so a plan row, the census and the doctor's line could not say what an item IS, and
# the board's rebuild door, handed a rolled name, asked suggestMule, whose last line routes a name
# nothing recognises to the weapons mule. ONE resolver, called by the plan, the census, the
# evidence route and (through the plan row it carries) the board's door. [[copy-drift]]
#: what each rarity is called on a line he reads: the ledger's own vocabulary (vault_retro.QUALITIES)
#: beside his words ("magic (blue)", "rare (gold)"). UNKNOWN is never one of these.
RARITY_SAY = {"unique": "unique", "set": "set", "gold": "rare (gold)", "blue": "magic (blue)",
              "white": "white"}
RARITY_ORDER = ("unique", "set", "gold", "blue", "white")


def _roster_rarity(name):
    """'unique' | 'set' when the item rosters name it as exactly one of those, else ''.

    item_identity._rosters is the ONE roster index this tree keeps (unique_roster.json,
    set_roster.json, runeword_roster.json, folded by fold_rendering) — borrowed, never copied.
    A name on both a unique and a runeword roster (Crescent Moon) is not decided by the roster:
    '' here, and its looks may still say. A roster that cannot be read answers None (UNKNOWN - nobody
    could ask), never '' dressed as "the roster did not say" and never a rarity; the caller treats both
    as "no roster answer" and asks the looks.
    """
    try:
        import item_identity as _ii
        tags = _ii._rosters().get(_ii.fold_rendering(name).lower()) or set()
    except Exception:
        return None
    kinds = [k for k in ("unique", "set", "runeword") if k in tags]
    # exactly one roster, and it is an item roster: a name that is also a runeword (Crescent Moon,
    # measured: {unique, runeword}) is not decided here — a completed runeword in his stash reads
    # the same name, so the looks must say
    return kinds[0] if len(kinds) == 1 and kinds[0] != "runeword" else ""


def _votes_say(votes):
    return " · ".join("%s %d" % (RARITY_SAY.get(q, q), n)
                      for q, n in sorted(votes.items(), key=lambda kv: (-kv[1], kv[0])))


def rarity_of(name, rows):
    """What this item IS, from the SAME evidence its tier stands on. Never writes.

    -> {rarity, by, votes, why}. `rarity` is one of vault_retro.QUALITIES or None (UNKNOWN).

    The roster decides a unique or a set piece (a name IS its rarity — the law the console's name
    colour already follows). A rolled name is what its looks SAW: each witness row's `quality`,
    read through vault_retro._quality_of (the one vocabulary: magic -> blue, rare -> gold,
    normal -> white), by majority. A tie is UNKNOWN with the votes beside it — the contradiction
    is the finding, never averaged. No roster and no vote is UNKNOWN, never white: a row read
    before v3369 carries no quality, and a blank is not a colour. When the looks disagree with
    the roster, the roster's answer stands and `looksSay` carries theirs.
    """
    roster = _roster_rarity(name)
    try:
        import vault_retro as VR
        qual = VR._quality_of
    except Exception:
        qual = None
    if qual is None:
        if roster:
            return {"rarity": roster, "by": "roster", "votes": None,
                    "why": "the %s roster names it" % roster}
        return {"rarity": None, "by": None, "votes": None,
                "why": "vault_retro could not be read, so what the looks saw is UNKNOWN"}
    # ⚠ v3526 (#231 second eye on v3525, reproduced: one blue visit + one gold visit banked as TWO frames read
    # "gold 2, blue 1" -> gold) — A VOTE IS A VISIT, NOT A FRAME, exactly as the tier this stands beside is
    # (_measure: "a look is a distinct visit, never a frame of a still screen"). Each visit casts one vote for
    # each quality its looks saw, with vault_retro's own fold (a bare prior "sA" is its bucket "sA#0"); a look
    # that names no visit cannot be shown to be a separate one and casts none — the tier does not count it either.
    fold = _visit_fold()
    by_visit, order = {}, []
    for row in (rows or []):
        if not isinstance(row, dict):
            continue
        looks = row.get("witnesses") if "witnesses" in row else row.get("looks")
        for look in (looks if isinstance(looks, list) else []):
            if not isinstance(look, dict) or look.get("quality") is None:
                continue
            q = qual(look.get("quality"))
            if not q:
                continue
            try:
                visit = _visit_of(look)
            except Exception:
                visit = ""
            if not visit:
                continue
            if visit not in by_visit:
                by_visit[visit] = set()
                order.append(visit)
            by_visit[visit].add(q)
    kept = set(fold(order)) if (fold and order) else set(order)
    for v in order:
        if v in kept:
            continue
        home = next((k for k in kept if k.startswith(v + "#")), None)   # a bare prior folded into its bucket
        if home:
            by_visit[home] |= by_visit[v]
    votes = {}
    for v in order:
        if v in kept:
            for q in by_visit[v]:
                votes[q] = votes.get(q, 0) + 1
    seen = ""
    if votes:
        top = max(votes.values())
        lead = [q for q, n in votes.items() if n == top]
        seen = lead[0] if len(lead) == 1 else ""
    if roster:
        out = {"rarity": roster, "by": "roster", "votes": votes, "why": "the %s roster names it" % roster}
        if seen and seen != roster:
            out["looksSay"] = seen
            out["why"] += ("; its looks read it as %s (%s) — the roster stands"
                           % (RARITY_SAY.get(seen, seen), _votes_say(votes)))
        return out
    if seen:
        return {"rarity": seen, "by": "looks", "votes": votes,
                "why": "its looks read it as %s (%s)" % (RARITY_SAY.get(seen, seen), _votes_say(votes))}
    if votes:
        return {"rarity": None, "by": None, "votes": votes,
                "why": ("its looks disagree about what it is (%s) — UNKNOWN, never averaged"
                        % _votes_say(votes))}
    return {"rarity": None, "by": None, "votes": votes,
            "why": ("no roster names it and no look recorded its quality (a row read before v3369 "
                    "carries none), so what it is stays UNKNOWN — never white")}


def stand(name, rows):
    """One item's standing on its own looks: its tier by visits, and what it is. Never writes.

    -> {tier, bound, successes, trials, rarity, rarityBy, rarityWhy, why}. tier None is UNKNOWN
    (a row whose looks cannot be read), never WATCHED. The evidence route (control_app.evidence_for,
    the vault branch) answers a magic or rare name with this — the same tier() and the same
    _measure the plan and the census use, never a second count.
    """
    rar = rarity_of(name, rows)
    floor = _conf_floor()
    measured = None
    if floor is not None:
        measured = _measure([r for r in (rows or []) if isinstance(r, dict)], floor)
    if measured is None:
        got = {"tier": None, "bound": None, "successes": None, "trials": None,
               "why": "the look counts could not be read, so the tier is UNKNOWN"}
    else:
        got = tier(measured[0], measured[1])
    return {"tier": got["tier"], "bound": got["bound"], "successes": got["successes"],
            "trials": got["trials"], "rarity": rar["rarity"], "rarityBy": rar["by"],
            "rarityWhy": rar["why"], "why": got["why"]}


def _is_success(look, floor):
    """A look that saw this item: its own frame, its own conf at the vault floor, and not a miss.

    2026-09-28 (Ledger fix round 2, finding D): vault_retro.look_saw_it, CALLED — the one
    definition the keep gate counts with. The copy that lived here took float(conf), so a bool
    True or the string "0.9" was a success here and not at the gate. [[copy-drift]]
    """
    import vault_retro as VR
    return VR.look_saw_it(look, floor)


def _visit_fold():
    """vault_retro's own fold for look ids, or None when that module cannot be read.

    Borrowed, never copied: the rule that a bare prior "sA" and its own bucket "sA#0" are one look
    lives in vault_retro._fold_bare_sessions, and the live gate folds with it. A second copy here
    would be the drift this file exists to prevent. [[copy-drift]]
    """
    try:
        import vault_retro as VR
        return VR._fold_bare_sessions
    except Exception:
        return None


def _visit_of(look):
    """The visit one look belongs to, as vault_retro.gate names it. '' when the look names none.

    `witness` is "<session>#<bucket>". The sweep mints it (vault_retro.py, the re-look loop) and
    opens a new bucket at every REOPEN_GAP_MS gap between still runs, so one bucket is one time
    he opened the stash, however many frames that screen was held for. A row persisted before
    the bucket existed carries only `session`, and that recording counts once.

    2026-09-28 (Ledger fix, finding 7): this is vault_retro.look_id, called — not re-typed. The
    copy that lived here read the raw string, so "reel_sA#0" and "sA#0" were two visits while
    chronicle_retro._reel_key calls them one reel. Its only caller, _measure, asked _visit_fold()
    first — the same import — and answered UNKNOWN if that module could not be read.
    """
    import vault_retro as VR
    return VR.look_id(look, "witness")


def _group(rows):
    order, buckets = [], {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        if name not in buckets:
            buckets[name] = []
            order.append(name)
        buckets[name].append(row)
    return [(name, buckets[name]) for name in order]


def _measure(rows, floor):
    """-> (successes, trials, sessions, cells, witness_sessions, frames) or None when a row cannot
    be read.

    A missing witness list is UNKNOWN, not zero. An empty list is a real measurement of no looks.

    ══ A TRIAL IS A DISTINCT VISIT, NEVER A FRAME — his ruling 2026-09-28 (§34.2) ══════════════
    "P0 fixes the math: a look is a distinct visit, never a frame of a still screen."

    This counted `trials += 1` per witness ROW. MEASURED on his vault_accum.json, read-only:
    Radiance held 103 rows, 102 of them under ONE re-look id (one stash screen held still and
    photographed 102 times) and one from a second recording. It scored HARDENED 103/103, bound
    0.964, on two looks. The Horadric Cube did the same on 20 + 1. Both were filed back as
    HARDENED by the 2026-09-27 reset rebuild. Honest: WATCHED 2/2.

    vault_retro already had the law, beside its own Wilson note: "Wilson runs on the FOLDED
    WITNESS LIST, never on raw sightings". gate() counts _visit_of() folded by
    _fold_bare_sessions. So does this now: one trial per visit, a success when any look of that
    visit saw the item. A look that names no visit cannot be shown to be a separate one and adds
    no trial, exactly as gate() skips it. `misses` still adds failed trials, one per miss.

    `frames` is the old per-row count, {successes, trials, unplaced}, carried BESIDE the visit
    count and never instead of it. The retro plan reads it to say what the frame math filed an
    item as. No tier decision reads it.
    """
    fold = _visit_fold()
    if fold is None:
        return None
    frame_ok, frame_n, extra_total, unplaced = 0, 0, 0, 0
    order, by_visit = [], {}
    cells, seen_cells = [], set()
    for row in rows:
        if "witnesses" not in row and "looks" not in row:
            return None
        raw = row.get("witnesses") if "witnesses" in row else row.get("looks")
        if not isinstance(raw, list):
            return None
        if "misses" in row:
            extra = row.get("misses")
            if isinstance(extra, bool) or not isinstance(extra, int) or extra < 0:
                return None
        else:
            extra = 0
        for look in raw:
            frame_n += 1
            if not isinstance(look, dict):
                unplaced += 1
                continue
            cell = look.get("cell")
            if isinstance(cell, dict) and "x" in cell and "y" in cell:
                ck = (str(cell.get("tab") or ""), cell.get("x"), cell.get("y"))
                if ck not in seen_cells:
                    seen_cells.add(ck)
                    cells.append({"tab": cell.get("tab"), "x": cell.get("x"), "y": cell.get("y")})
            ok = _is_success(look, floor)
            if ok:
                frame_ok += 1
            visit = _visit_of(look)
            if not visit:
                unplaced += 1
                continue
            if visit not in by_visit:
                by_visit[visit] = []
                order.append(visit)
            by_visit[visit].append((look, ok))
        extra_total += extra
    visits = set(fold(order))
    # ══ 2026-09-28 (Ledger fix, finding 5) — FOLD THE SUCCESSES ON THEIR OWN, AS gate() DOES ═══
    # This folded ALL visits first and then asked each survivor for a success. gate() folds the
    # qualifying looks SEPARATELY (`sessions`) from every look (`looksSeen`). They part on a bare
    # prior that saw it beside its own bucket that did not: [{"session": "s1", frame, 0.9},
    # {"witness": "s1#0", frame None, 0.0}]. gate() reads 1 witness; the fold-first order dropped
    # "s1" for "s1#0", found no success in "s1#0", and read 0. Now: successes = the fold of the
    # visits that saw it, trials = the fold of every visit + misses — gate()'s two numbers. The
    # fold of a subset can never outnumber the fold of the whole, so successes <= trials.
    won = [v for v in order if any(ok for _look, ok in by_visit[v])]
    success_ids = set(fold(won))
    successes = 0
    sessions, witness_sessions, seen_sessions = [], [], set()
    for visit in order:
        if visit not in success_ids:
            continue            # never saw it, or a bare prior folded into its own bucket
        hit = None
        for look, ok in by_visit[visit]:
            if ok:
                hit = look
                break
        if hit is None:
            continue
        successes += 1
        session = str(hit.get("session") or "").strip() or visit
        if session not in seen_sessions:
            seen_sessions.add(session)
            sessions.append(session)
        witness_sessions.append({
            "witness": visit, "session": session,
            "frame": str(hit.get("frame") or "").strip(), "conf": float(hit.get("conf")),
        })
    trials = len(visits) + extra_total
    frames = {"successes": frame_ok, "trials": frame_n + extra_total, "unplaced": unplaced}
    return successes, trials, sessions, cells, witness_sessions, frames


# ── THE RETRO PLAN — his ruling 2026-09-28 (§34.2) ──────────────────────────────────────────────
# Konyo: "Keep filed, flag 'retro: WATCHED'". Radiance and the Horadric Cube came back HARDENED
# from the 2026-09-27 rebuild only because one still screen counted as 21 to 103 looks. They
# stay filed, show their true tier with a retro flag, and must earn PROVEN/HARDENED with real
# looks. So this NAMES them. It never unfiles, never writes, and has no apply half.
_TIER_RANK = {WATCHED: 0, PROVEN: 1, HARDENED: 2}
_RETRO_RULING = ("His ruling 2026-09-28 (§34.2): it stays filed, carries the flag, and earns "
                 "PROVEN/HARDENED with real looks — never auto-unfiled")


def _retro_row(name, measured, recorded=None, board_filed=False):
    """One item filed on a tier higher than its visits earn, or None. Never writes.

    `recorded` is the tier the board recorded when the caller handed it in. Without it, the
    recorded tier is what the FRAME math gives on these same rows — the math the 2026-09-27
    rebuild filed on — and `recordedBy` says so, so a derived tier never reads as the board's.
    `board_filed` (round-5 review, LOW): the board DID file this name but wrote no tier (every
    normal-door filing, per #41 rank 10) — the row then says "board (no tier)", never "frames",
    so the plan's summary and its rows name the same source. [[label-outlived-referent]]
    """
    honest = tier(measured[0], measured[1])
    frames = measured[5] if len(measured) > 5 else None
    if recorded is not None:
        rec, by = recorded, "board"
    elif isinstance(frames, dict):
        rec, by = tier(frames.get("successes"), frames.get("trials"))["tier"], ("board (no tier)" if board_filed else "frames")
    else:
        return None
    if rec not in _TIER_RANK or honest["tier"] not in _TIER_RANK:
        return None
    if _TIER_RANK[rec] <= _TIER_RANK[honest["tier"]]:
        return None
    visits = "%d/%d" % (honest["successes"], honest["trials"])
    if by == "frames":
        what = ("%s counted by frames (%d of %d frames), but those frames are %d visit(s)"
                % (rec, frames.get("successes") or 0, frames.get("trials") or 0, honest["trials"]))
    elif by == "board (no tier)":
        what = ("filed on the board with no tier; the frame math counts it %s (%d of %d frames), but those frames are "
                "%d visit(s)" % (rec, frames.get("successes") or 0, frames.get("trials") or 0, honest["trials"]))
    else:
        what = "filed %s on the board, but its looks are %d visit(s)" % (rec, honest["trials"])
    # finding B (round 2): keepFiled only where the door can keep it — one look that saw it
    keep = honest["successes"] >= RETRO_KEEP_MIN_LOOKS
    return {"name": name, "recordedTier": rec, "honestTier": honest["tier"],
            "flag": "retro: %s" % honest["tier"], "keepFiled": keep, "recordedBy": by,
            "visits": {"successes": honest["successes"], "trials": honest["trials"],
                       "bound": honest["bound"]},
            "frames": ({"successes": frames.get("successes"), "trials": frames.get("trials")}
                       if isinstance(frames, dict) else None),
            "sessions": list(measured[2]),
            "why": ("%s — its true tier is %s %s. %s." % (what, honest["tier"], visits, _RETRO_RULING))
                   if keep else
                   ("%s — its true tier is %s %s. It is %s." % (what, honest["tier"], visits,
                                                                RETRO_NO_LOOK_WHY))}


def _retro_answer(rows, by, unjudged=None):
    names = [r["name"] for r in rows]
    # finding B (round 2): a flagged row no visit saw is NOT kept filed — named apart, never
    # folded into the kept list the ruling sentence describes
    held = [r["name"] for r in rows if r.get("keepFiled") is not True]
    return {"ok": True, "n": len(rows), "rows": rows, "names": names, "recordedBy": by,
            "unjudged": list(unjudged or []), "heldNames": held,
            "why": ("%d item(s) filed above what their visits earn: %s. %s.%s"
                    % (len(rows), ", ".join(names[:8]), _RETRO_RULING,
                       (" %d of them held — no visit saw it: %s." % (len(held), ", ".join(held[:8])))
                       if held else "")) if rows
                   else "no item is filed above what its visits earn"}


def _recorded_tiers(recorded):
    """The board's recorded tiers, as {name: tier}. None when the shape cannot be read."""
    out = {}
    if isinstance(recorded, dict):
        pairs = list(recorded.items())
    elif isinstance(recorded, list):
        pairs = [(r.get("name"), r) for r in recorded if isinstance(r, dict)]
    else:
        return None
    for name, val in pairs:
        t = val.get("tier") if isinstance(val, dict) else val
        if name and isinstance(t, str) and t.strip().upper() in _TIER_RANK:
            out[str(name)] = t.strip().upper()
    return out


def retro_plan(path, recorded=None):
    """Every item whose recorded tier is HIGHER than its honest (visit) tier. Never writes.

    -> {ok, n, rows:[{name, recordedTier, honestTier, why, flag, keepFiled, ...}], names,
        recordedBy, unjudged, why}

    `recorded` is optional: the board's own filings, as {name: tier} or [{name, tier}], so the
    comparison is against what was really filed. Without it, the recorded tier is the frame
    math's (recordedBy "frames"). A name the board filed with no readable ledger row is listed
    in `unjudged`, never called honest. An unreadable ledger is UNKNOWN: rows and n are None.
    This plan has no unfile, by his ruling: a row one visit saw says keepFiled True. A row NO visit
    saw says keepFiled False with RETRO_NO_LOOK_WHY — there is nothing to keep it filed on, and a
    promise the door cannot keep is not made (Ledger fix round 2, finding B). `heldNames` lists them.
    """
    unread = {"ok": False, "n": None, "rows": None, "names": None, "recordedBy": None,
              "unjudged": None, "why": _UNREAD}
    doc = _load_owned(path)
    if doc is None:
        return unread
    floor = _conf_floor()
    if floor is None:
        return unread
    board = None
    if recorded is not None:
        board = _recorded_tiers(recorded)
        if board is None:
            return dict(unread, why=("the recorded tiers handed in could not be read, so which "
                                     "items are filed too high is UNKNOWN"))
    rows, unjudged, seen = [], [], set()
    for name, grp in _group(doc["owned"]):
        seen.add(name)
        measured = _measure(grp, floor)
        if board is not None and name not in board:
            continue             # never filed on the board, so it cannot be filed too high
        if measured is None:
            if board is not None:
                unjudged.append(name)
            continue
        flagged = _retro_row(name, measured, board.get(name) if board is not None else None)
        if flagged:
            rows.append(flagged)
    if board is not None:
        unjudged += sorted(n for n in board if n not in seen)
    return _retro_answer(rows, "board" if board is not None else "frames", unjudged)


def _recorded_filings(recorded):
    """The board's own filings, as the reset hands them in. -> (names, tiers) | None (not handed in) | False (unreadable).

    #41 rank 1 (2026-09-29): {name: tier | 'filed'} from the board (window._vaultRecordedFilings — the mule map's
    names and their witness rows' tiers, read BEFORE the reset's clears), or [{name, tier}]. A name whose value is
    not a tier is still a FILING (tier unknown), so the retro rule may keep it. None means the caller did not say
    (the frame math decides, as before); a shape that cannot be read is False, never an empty board.
    ⚠ round-5 review (MED) — THE TWO ENDS AGREED ON NOTHING FOR "UNREADABLE". The page sent `null` when a store would
    not read, and this read None as "the caller did not say" and fell back to the frame-surplus keep — the audit's own
    defect, through the unreadable door. The page now sends `false` for a board it could not read (bible.html
    _vaultAskRebuildPlan), and `false` is the unreadable arm here: UNKNOWN, nothing rebuilt. `null` / absent still means
    the caller did not say. [[unknown-stays-unknown]] [[the-unjoined-end]]
    """
    if recorded is None:
        return None
    if recorded is False:
        return False
    if isinstance(recorded, dict):
        pairs = list(recorded.items())
    elif isinstance(recorded, list):
        pairs = [(r.get("name"), r) for r in recorded if isinstance(r, dict)]
    else:
        return False
    names, tiers = set(), {}
    for name, val in pairs:
        if not name:
            continue
        names.add(str(name))
        t = val.get("tier") if isinstance(val, dict) else val
        if isinstance(t, str) and t.strip().upper() in _TIER_RANK:
            tiers[str(name)] = t.strip().upper()
    return names, tiers


def plan_from_ledger(path, recorded=None):
    """Read one witness ledger and ask rebuild_plan. Never writes the file.

    `path` is the caller's file. This does not know where his ledger lives, and a path that
    cannot be read is UNKNOWN — rebuilt stays empty and ok is false, which is not "nothing proven".

    ══ #41 rank 1 (2026-09-29) — THE RETRO KEEP IS PROMISED ONLY TO A ROW THE BOARD HELD ══════════
    One vault had three admission bars and nothing paired them: Wilson 0.722 over 10 visits here, 2
    looks at the normal door, 1 look for a keepFiled retro row — and the retro flag was derived from
    surplus FRAMES, never from what the board had actually filed. His board has held nothing since his
    09-27 reset (every backup: d2r_muleAssign {} and d2r_vaultProv {}), and this still promised
    keepFiled for Radiance and the Horadric Cube ("kept filed by his ruling (§34.2)") on the 1-look
    bar. §34.2 keeps a row FILED because it was filed before; a board that never filed it has nothing
    to keep. `recorded` is the board's own filings (see _recorded_filings): with it, a name the board
    did not hold is judged on its honest tier and HELD like any WATCHED row; the recorded tier, when
    the board wrote one, is the tier compared against. Without it (None) the frame math decides, as it
    always did — and `recordedBy` says which. An unreadable `recorded` is UNKNOWN: nothing is rebuilt.

    ⚠ THE RETRO FLAG IS NOT STORED ANYWHERE — it is RECOMPUTED on every reset from the frame
    surplus: _retro_row compares what the frame math would file (one success per witness ROW)
    against the visit math, and flags the difference. So the flag lives only as long as the extra
    frames do. If the ledger is ever compacted to one frame per visit, the flag vanishes — persist
    it before any compaction, or his §34.2 "keep filed" rows lose their reason (and a WATCHED one
    its way back onto the board) with no error. (Ledger fix round 2, note E.)
    """
    if not path or not os.path.isfile(path):
        return _unread()
    try:
        with io.open(path, "rb") as fh:
            blob = fh.read()
    except Exception:
        return _unread()
    try:
        doc = json.loads(blob.decode("utf-8"))
    except Exception:
        return _unread()
    if not isinstance(doc, dict) or not isinstance(doc.get("owned"), list):
        return _unread()
    floor = _conf_floor()
    if floor is None:
        return _unread()
    board = _recorded_filings(recorded)
    if board is False:
        return _unread("the board's recorded filings could not be read, so which rows it held is UNKNOWN — "
                       "nothing is rebuilt and nothing is called empty")
    held_names, held_tiers = (board if board is not None else (None, {}))
    items, filing, retro = [], {}, []
    for name, rows in _group(doc["owned"]):
        measured = _measure(rows, floor)
        rar = rarity_of(name, rows)
        if measured is None:
            item = {"name": name, "successes": None, "trials": None,
                    "rarity": rar["rarity"], "rarityBy": rar["by"]}
            extra = {"equipped": _equipped_of(rows), "kind": _kind_of(rows),
                     "cells": [], "sessions": [], "witness": None}
        else:
            successes, trials, sessions, cells, witness_sessions, _frames = measured
            # rank 1 — a row the board never filed is never flagged retro (nothing to keep filed); a filing the board
            # wrote with no tier is still the BOARD's (round-5 review, LOW: its row says "board (no tier)")
            flagged = (_retro_row(name, measured, held_tiers.get(name), board_filed=(held_names is not None))
                       if (held_names is None or name in held_names) else None)
            item = {"name": name, "successes": successes, "trials": trials,
                    "equipped": _equipped_of(rows), "kind": _kind_of(rows),
                    # #51 — the SAME looks say what it is (rarity_of); a magic or rare row is
                    # judged by the same tier and rebuilt through the same door as a unique
                    "rarity": rar["rarity"], "rarityBy": rar["by"]}
            if flagged:
                retro.append(flagged)
                # ══ 2026-09-28 (Ledger fix, finding 1) — THE RESET READS `rebuilt`, SO THE FLAG
                # RIDES THERE. The board's _vaultRefileFromPlan files plan.rebuilt and never reads
                # plan.retro, so Radiance and the Horadric Cube (WATCHED 2/2 by visits) were HELD —
                # un-filed on his next reset, against his ruling "Keep filed, flag 'retro:
                # WATCHED'". rebuild_plan now files a flagged row at its true tier.
                item["retro"] = flagged["flag"]
            extra = {"equipped": item["equipped"], "kind": item["kind"],
                     "cells": cells, "sessions": sessions,
                     "witness": {"lane": "stash", "by": "evidence", "sessions": witness_sessions}}
        items.append(item)
        filing[name] = extra
    plan = rebuild_plan(items)
    if not plan.get("ok"):
        return plan
    for row in plan["rebuilt"]:
        extra = filing.get(row["name"]) or {}
        row["equipped"] = bool(extra.get("equipped"))
        row["kind"] = extra.get("kind") or ""
        row["cells"] = extra.get("cells") or []
        row["sessions"] = extra.get("sessions") or []
        witness = extra.get("witness")
        if isinstance(witness, dict):
            witness = dict(witness)
            witness["wilson"] = row.get("bound")
            witness["gate"] = {"pass": True, "why": row.get("why"),
                               "looks": row.get("successes"), "wilson": row.get("bound")}
        row["witness"] = witness
        row["home"] = "__keep" if (row["equipped"] or row["kind"] in KEPT_KINDS) else None
    try:
        with io.open(path, "rb") as fh:
            again = fh.read()
    except Exception:
        return _unread()
    if again != blob:
        return _unread("the witness ledger changed while it was read, so nothing is rebuilt "
                       "and nothing is called empty")
    # The retro flags ride on the plan the console already serves (POST /api/vault_rebuild_plan),
    # read from these same bytes: here as the summary, and on each flagged row of `rebuilt` — the
    # field the board's reset actually files from. [[the-unjoined-end]]
    plan["retro"] = _retro_answer(retro, "board" if held_names is not None else "frames")
    plan["recordedBy"] = "board" if held_names is not None else "frames"
    return plan


def cited_frames(path):
    """Frame files a WATCHED, PROVEN or HARDENED item stands on. Never writes the ledger.

    A missing file is a measurement of nothing cited. A file that will not parse is UNKNOWN:
    `frames` is None, and a deleter that cannot tell must keep every picture.
    Only a look that saw the item is cited. A miss is not.
    """
    if not path or not os.path.isfile(path):
        return {"ok": True, "frames": [], "why": "there is no witness ledger at this path, so no frame is cited"}
    try:
        with io.open(path, "rb") as fh:
            blob = fh.read()
    except Exception:
        return {"ok": False, "frames": None, "why": _UNREAD}
    try:
        doc = json.loads(blob.decode("utf-8"))
    except Exception:
        return {"ok": False, "frames": None, "why": _UNREAD}
    if not isinstance(doc, dict):
        return {"ok": False, "frames": None, "why": _UNREAD}
    owned = doc.get("owned")
    # A readable ledger that simply has no owned rows cites nothing. That is the empty
    # vault_accum.json the reel planner already writes. A present owned value that is not a
    # list will not parse, and that stays UNKNOWN.
    if owned is None:
        return {"ok": True, "frames": [], "why": "this ledger names no owned rows, so no frame is cited"}
    if not isinstance(owned, list):
        return {"ok": False, "frames": None, "why": _UNREAD}
    floor = _conf_floor()
    if floor is None:
        return {"ok": False, "frames": None, "why": _UNREAD}
    found, seen = [], set()
    # #41 rank 4 — beside the bare list: which REEL each cited frame lives in and which ITEMS stand on
    # it, so a loss can be dated by the reel's tombstone and named by the item (never a bare filename)
    reels, items = {}, {}
    for name, rows in _group(doc["owned"]):
        measured = _measure(rows, floor)
        if measured is None:
            continue
        successes, trials, _sessions, _cells, shots, _frames = measured
        got = tier(successes, trials)
        if got["tier"] not in (WATCHED, PROVEN, HARDENED):
            continue
        for shot in shots:
            base = os.path.basename(str(shot.get("frame") or ""))
            if not base:
                continue
            items.setdefault(base, [])
            if name not in items[base]:
                items[base].append(name)
            sess = str(shot.get("session") or "").strip()
            if sess and base not in reels:
                reels[base] = sess
            if base in seen:
                continue
            seen.add(base)
            found.append(base)
    try:
        with io.open(path, "rb") as fh:
            if fh.read() != blob:
                return {"ok": False, "frames": None, "why": _UNREAD}
    except Exception:
        return {"ok": False, "frames": None, "why": _UNREAD}
    return {"ok": True, "frames": found, "reels": reels, "items": items, "why": ""}


def _load_owned(path):
    """The ledger's owned list, or None when the file cannot be read. Never writes."""
    if not path or not os.path.isfile(path):
        return None
    try:
        with io.open(path, "rb") as fh:
            raw = fh.read()
        doc = json.loads(raw.decode("utf-8"))
    except Exception:
        return None
    if not isinstance(doc, dict) or not isinstance(doc.get("owned"), list):
        return None
    return doc


def tier_census(path):
    """How many items sit in each tier, and whether that agrees with rebuild_plan.

    An unreadable ledger leaves every count None. A readable empty ledger is 0, which is
    a measurement. The two answers are not the same.
    """
    unread = {"ok": False, "watched": None, "proven": None, "hardened": None,
              "unknown": None, "disagree": None, "retro": None, "retroNames": None,
              "retroHeldNames": None, "provenNames": None, "byRarity": None,
              "rarityUnknown": None, "why": _UNREAD}
    doc = _load_owned(path)
    if doc is None:
        return unread
    floor = _conf_floor()
    if floor is None:
        return unread
    plan = plan_from_ledger(path)
    if not plan.get("ok"):
        return unread
    by_plan = {}
    for row in (plan.get("rebuilt") or []) + (plan.get("held") or []):
        if isinstance(row, dict) and row.get("name"):
            by_plan[row["name"]] = row.get("tier")
    counts = {WATCHED: 0, PROVEN: 0, HARDENED: 0, "unknown": 0}
    disagree, retro, retro_held, proven_names = [], [], [], []
    # #51 — the SAME count, split by what each item is: {rarity | "unknown": {watched, proven,
    # hardened, unknown}}. A name whose rarity nothing could tell sits under "unknown", counted,
    # never folded into white. The tallies he asked for are read off this by the doctor's line.
    by_rarity = {}
    for name, rows in _group(doc["owned"]):
        measured = _measure(rows, floor)
        if measured is None:
            got_tier = None
        else:
            successes, trials = measured[0], measured[1]
            got_tier = tier(successes, trials)["tier"]
            _flag = _retro_row(name, measured)
            if _flag:
                retro.append(name)
                if _flag.get("keepFiled") is not True:
                    retro_held.append(name)     # finding B: no visit saw it — held, not kept
        key = got_tier if got_tier in (WATCHED, PROVEN, HARDENED) else "unknown"
        counts[key] += 1
        rar = rarity_of(name, rows)["rarity"] or "unknown"
        bucket = by_rarity.setdefault(rar, {"watched": 0, "proven": 0, "hardened": 0, "unknown": 0})
        bucket[key.lower()] += 1
        if got_tier in (PROVEN, HARDENED):
            # the NAMES, not only the count: corroborate's a-tier-stands-on-its-looks checks each
            # one against the live gate, because a count can balance two wrong items (finding 4)
            proven_names.append(name)
        if by_plan.get(name) != got_tier:
            disagree.append(name)
    why = ""
    if disagree:
        why = ("the tier table and the witness ledger disagree on %s"
               % ", ".join(disagree[:8]))
    return {"ok": True, "watched": counts[WATCHED], "proven": counts[PROVEN],
            "hardened": counts[HARDENED], "unknown": counts["unknown"],
            "disagree": disagree, "retro": len(retro), "retroNames": retro,
            "retroHeldNames": retro_held,
            "provenNames": proven_names, "byRarity": by_rarity,
            "rarityUnknown": sum((by_rarity.get("unknown") or {}).values()), "why": why}


def rarity_tally_say(by_rarity):
    """The census split, in words: 'unique W1/P1/H0 · rare (gold) W0/P1/H0 · rarity UNKNOWN 1'.

    Read by the doctor's evidence-tiers row. None (an unread census) is said UNKNOWN, never a
    row of zeros. A bucket with an unreadable tier says it (/?N) so a count never hides one.
    """
    if not isinstance(by_rarity, dict):
        return "by rarity: UNKNOWN"
    bits = []
    order = list(RARITY_ORDER) + sorted(k for k in by_rarity if k not in RARITY_ORDER and k != "unknown")
    for k in order:
        b = by_rarity.get(k)
        if not b:
            continue
        bits.append("%s W%d/P%d/H%d%s" % (RARITY_SAY.get(k, k), b.get("watched") or 0, b.get("proven") or 0,
                                           b.get("hardened") or 0,
                                           ("/?%d" % b["unknown"]) if b.get("unknown") else ""))
    n_unk = sum((by_rarity.get("unknown") or {}).values())
    return "by rarity: " + (" · ".join(bits) if bits else "none") + " · rarity UNKNOWN %d" % n_unk


def pictures_gone(path, root):
    """Cited frames that are not on the shelf. Never writes.

    `root` None means the shelf was not opened: n is None, not 0. A shelf that cannot be
    read is the same answer. A shelf that was read and holds every cited frame is n 0.
    """
    cited = cited_frames(path)
    if not cited.get("ok") or cited.get("frames") is None:
        return {"ok": False, "gone": None, "n": None, "cited": None,
                "why": cited.get("why") or _UNREAD}
    if root is None:
        return {"ok": True, "gone": None, "n": None, "cited": len(cited["frames"]),
                "why": ("the picture shelf was not opened, so how many evidence links are "
                        "broken is UNKNOWN, not 0")}
    if not os.path.isdir(root):
        return {"ok": False, "gone": None, "n": None, "cited": None,
                "why": ("the picture shelf could not be read, so how many evidence links are "
                        "broken is UNKNOWN")}
    present = set()
    try:
        for dirpath, dirnames, files in os.walk(root):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for fname in files:
                if fname.lower().endswith(".jpg"):
                    present.add(fname)
    except Exception:
        return {"ok": False, "gone": None, "n": None, "cited": None,
                "why": ("the picture shelf could not be read, so how many evidence links are "
                        "broken is UNKNOWN")}
    gone = [f for f in cited["frames"] if f not in present]
    return {"ok": True, "gone": gone, "n": len(gone), "cited": len(cited["frames"]),
            "reels": {f: cited.get("reels", {}).get(f) for f in gone},
            "items": {f: cited.get("items", {}).get(f) or [] for f in gone}, "why": ""}


# ══ #41 rank 4 — WHEN A CITED PICTURE WENT, AGAINST WHEN THE KEEP LANDED ═══════════════════════════
# The keep (release_uncited holding a cited frame when its reel is drained, called by apply_plan) landed
# in c45c5840 on 2026-09-28 07:37:19Z. A picture that was gone before that moment was lost by a drain
# nothing could have stopped — it is BASELINE, reported beside an OK, never a red that hides the next
# loss. A picture gone AFTER it is a loss the keep should have prevented: MISSING, naming the item it
# stands on. A loss no tombstone dates cannot be put on either side and is said UNKNOWN-when — red,
# because an unexplained loss is not a baseline. [[unknown-stays-unknown]] [[stale-reading]]
# ⚠ round-5 review (LOW) — THE COMMIT TIME IS A LOWER BOUND, NOT THE MOMENT THE KEEP REACHED THIS MACHINE.
# The keep landed here when he pulled / deployed it, which is later than its commit; a reel drained in that
# gap reads as lost AFTER the keep though nothing could have kept it. The row says so in its words
# (KEEP_LANDED_WHY) rather than pretending the constant is exact. [[stale-reading]]
KEEP_LANDED_MS = 1790581039000
KEEP_LANDED_WHY = ("the keep's commit time, 2026-09-28 07:37Z — a lower bound: it reached this machine no "
                   "earlier, so a drain between that commit and the pull reads as after")


def _inside(path, tree):
    """Is `path` inside `tree`? realpath'd and case-folded, never a bare startswith (his Windows box is the other half)."""
    try:
        p = os.path.normcase(os.path.realpath(path))
        t = os.path.normcase(os.path.realpath(tree)).rstrip(os.sep)
    except Exception:
        return False
    return p == t or p.startswith(t + os.sep)


def _tombstone_times(root):
    """{session: deletedTs} from the reel tombstones of `root`'s tree, or None when there are none to read.

    ⚠ round-5 review (HIGH, reproduced on his tree) — THE RESOLVER'S ANSWER IS TRUSTED. The first cut only accepted a
    record under the shelf's parent, and his record is tv/reel_tombstones.json beside a shelf at tv/frames/hist: the
    guard dropped it, all 21 of his gone frames read 'undated', and the row was MISSING for ever again wearing the false
    sentence "no tombstone dates the loss". reel_retention._tombstone_path(root) already answers the FIXTURE case with a
    file inside the fixture's own tree; the one answer that must be refused is the ImportError fallback (HERE — his file)
    for a root OUTSIDE his tree. The shelf's own tree is asked first (a fixture that writes its record beside the shelf).
    [[feedback-fixtures-never-touch-live-data]] [[unknown-stays-unknown]]
    """
    cands = [os.path.join(root, "reel_tombstones.json"),
             os.path.join(os.path.dirname(os.path.realpath(root)), "reel_tombstones.json")]
    try:
        import reel_retention as _rr
        named, home = _rr._tombstone_path(root), _rr.HERE
    except Exception:
        named, home = None, None
    # a fixture root (outside HERE's tree) is never dated by a record inside it — his tombstones
    if named and not (home and not _inside(root, home) and _inside(named, home)):
        cands.append(named)
    seen = set()
    for p in cands:
        key = os.path.normcase(os.path.realpath(p)) if p else None
        if not p or key in seen or not os.path.isfile(p):
            continue
        seen.add(key)
        try:
            with io.open(p, encoding="utf-8") as fh:
                doc = json.load(fh)
        except Exception:
            return None
        rows = doc.get("reels") if isinstance(doc, dict) else None
        if not isinstance(rows, list):
            return None
        out = {}
        for r in rows:
            if not isinstance(r, dict):
                continue
            reel = str(r.get("reel") or "")
            sess = reel[len("reel_"):] if reel.startswith("reel_") else reel
            ts = r.get("deletedTs")
            if sess and isinstance(ts, (int, float)) and not isinstance(ts, bool):
                out[sess] = max(int(ts), out.get(sess, 0))
        return out
    return None


def picture_losses(path, root, landed_ms=None):
    """pictures_gone, dated. -> {ok, n, cited, gone, baseline:[..], after:[{frame,item,reel,deletedTs}], undated:[..], why}

    `n` / `cited` are pictures_gone's; the split is by each gone frame's reel tombstone against
    `landed_ms` (KEEP_LANDED_MS). A shelf not opened, or unreadable, is UNKNOWN as before.
    """
    got = pictures_gone(path, root)
    if got.get("n") is None:
        return dict(got, baseline=None, after=None, undated=None)
    landed = KEEP_LANDED_MS if landed_ms is None else landed_ms
    stones = _tombstone_times(root) if got["n"] else {}
    baseline, after, undated = [], [], []
    for f in got["gone"]:
        sess = (got.get("reels") or {}).get(f)
        names = (got.get("items") or {}).get(f) or []
        ts = (stones or {}).get(_bare_session(sess)) if sess else None
        row = {"frame": f, "item": ", ".join(names) or "an item the ledger does not name", "reel": sess, "deletedTs": ts}
        if ts is None:
            undated.append(row)
        elif ts < landed:
            baseline.append(row)
        else:
            after.append(row)
    return dict(got, baseline=baseline, after=after, undated=undated)


def _bare_session(sess):
    s = str(sess or "")
    s = s[len("reel_"):] if s.startswith("reel_") else s
    return s.split("#", 1)[0]


def keeps_diff(before, after):
    """Which kept stores changed between two digest maps, which could not be compared, and which the reset MATERIALISED.
    -> (touched, unknown, materialised)

    round-5 (seen on the captured pixels): a store absent before ('absent') and present after was written by the reset's
    own persistOwned() with the page's default — on a fresh board that is not a change to his data and must not read
    "a reset must never change ... it did"; it is named apart, never hidden. [[unknown-stays-unknown]]
    """
    touched, unknown, materialised = [], [], []
    for key in sorted(set(before) | set(after)):
        if key not in before or key not in after:
            unknown.append(key)
            continue
        if before[key] == "absent" and after[key] != "absent":
            materialised.append(key)
            continue
        if before[key] != after[key]:
            touched.append(key)
    return touched, unknown, materialised


def _refusals(receipt):
    """The plan rows the board's door refused, as the reset receipt carries them.

    -> (n, [{name, refused, why}]) — or (None, None) when the receipt does not say, which is
    UNKNOWN, never 0. An older receipt carried bare names; those keep the name and a None reason.
    """
    raw = receipt.get("rebuiltFailed")
    if not isinstance(raw, list):
        return None, None
    rows = []
    for r in raw:
        if isinstance(r, dict):
            rows.append({"name": (str(r.get("name")) if r.get("name") else None),
                         "refused": (str(r.get("refused")) if r.get("refused") else None),
                         "why": (str(r.get("why")) if r.get("why") else None)})
        else:
            rows.append({"name": (str(r) if r else None), "refused": None, "why": None})
    return len(rows), rows


def _rebuilt_by_rarity(receipt):
    """#51 — what the reset filed back, by rarity, as the board's receipt carries it.

    -> {rarity: n} | None when the receipt does not say (an older board), which is UNKNOWN,
    never {}. A receipt whose tally is not a mapping is UNKNOWN — and so, v3526 (#231 second eye on
    v3525), is one whose tally holds ANY count that is not a non-negative int: dropping it and keeping
    the rest printed a SHORTER tally as if it were the whole one ("rebuilt by rarity: none" over a
    reset that rebuilt four).
    """
    raw = receipt.get("rebuiltByRarity")
    if not isinstance(raw, dict):
        return None
    out = {}
    for k, v in raw.items():
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            return None
        out[str(k)] = v
    return out


def rebuilt_rarity_say(tally, rebuilt_n=None):
    """'rebuilt by rarity: 1 rare (gold) · 2 unique' — or that the receipt does not say."""
    if tally is None:
        return ("rebuilt by rarity UNKNOWN (the receipt does not say)" if rebuilt_n
                else "rebuilt by rarity: n/a (nothing rebuilt)" if rebuilt_n == 0
                else "rebuilt by rarity UNKNOWN (the receipt does not say)")
    total = sum(tally.values())
    if not total:
        # v3526 — an empty tally is "none" ONLY for a reset that rebuilt nothing; beside a rebuild it is a tally
        # that was not kept, which is UNKNOWN, never a measured none
        if rebuilt_n == 0:
            return "rebuilt by rarity: none"
        return ("rebuilt by rarity UNKNOWN (the receipt tallies none of the %s rebuilt)"
                % (rebuilt_n if isinstance(rebuilt_n, int) else "?"))
    # the board's own key for a row the plan could not place is "unknown" (bible.html _vaultRefileFromPlan);
    # said as such, in the same words the status line uses, never as a colour
    say = dict(RARITY_SAY, unknown="rarity UNKNOWN")
    order = list(RARITY_ORDER) + sorted(k for k in tally if k not in RARITY_ORDER)
    out = "rebuilt by rarity: " + " · ".join("%d %s" % (tally[k], say.get(k, "rarity " + k))
                                            for k in order if k in tally)
    if isinstance(rebuilt_n, int) and not isinstance(rebuilt_n, bool) and total != rebuilt_n:
        out += " — the tally covers %d of the %d rebuilt; the rest is UNKNOWN" % (total, rebuilt_n)
    return out


def _refusals_say(rows):
    bits = []
    for r in rows[:6]:
        bits.append("%s (%s)" % (r.get("name") or "an unnamed row",
                                 r.get("why") or r.get("refused") or "no reason recorded"))
    more = len(rows) - len(bits)
    return "; ".join(bits) + ((" and %d more" % more) if more > 0 else "")


def reset_receipt(receipt, before, after):
    """What a reset receipt claims, beside the kept-store bytes. Never writes.

    No receipt, or a receipt that does not say what it rebuilt, is UNKNOWN — rebuilt is
    None, not 0. A kept store whose bytes differ is named.

    2026-09-28 (Ledger fix round 2, finding B): a plan row the board's door REFUSED is named.
    _vaultRefileFromPlan writes them to the receipt as `rebuiltFailed` ({name, refused, why});
    this reads them, so a row the plan said comes back and did not is never a silent gap between
    `rebuilt` and `held`. A receipt that carries no rebuiltFailed leaves `refused` UNKNOWN.
    """
    blank = {"ok": False, "rebuilt": None, "held": None, "touched": None, "unknown": None,
             "refused": None, "refusedRows": None,
             "why": "the reset left no receipt, so what it cleared is UNKNOWN, not 0"}
    if not isinstance(receipt, dict):
        return blank
    if not isinstance(before, dict) or not isinstance(after, dict):
        return dict(blank, why="the kept stores could not be read, so whether they survived is UNKNOWN")

    def _n(key):
        if key not in receipt or receipt.get(key) is None:
            return None
        val = receipt.get(key)
        if isinstance(val, bool):
            return None
        if isinstance(val, list):
            return len(val)
        if isinstance(val, int):
            return val
        return None

    rebuilt_n, held_n = _n("rebuilt"), _n("held")
    refused_n, refused_rows = _refusals(receipt)
    touched, unknown, materialised = keeps_diff(before, after)
    # #51 — the tally by rarity rides on the receipt (bible.html _vaultRefileFromPlan writes
    # rebuiltByRarity from the plan rows the door filed); absent is UNKNOWN, never 0 of each
    by_rarity = _rebuilt_by_rarity(receipt)
    base = {"rebuilt": rebuilt_n, "held": held_n, "touched": touched, "unknown": unknown, "materialised": materialised,
            "refused": refused_n, "refusedRows": refused_rows, "byRarity": by_rarity}
    made = (" · wrote where no store existed (the page's defaults, not a change): %s" % ", ".join(materialised)) if materialised else ""
    # #41 rank 2 — "Reset assignments" (door vaultReset) never rebuilds: rebuilt / held are NOT APPLICABLE to it, not
    # UNKNOWN, so its receipt is judged on the kept stores alone and never reads as "rebuilt is UNKNOWN" for ever
    if receipt.get("door") == "vaultReset":
        base = dict(base, rebuilt=None, held=None, refused=None, notApplicable="rebuilt / held (Reset assignments never rebuilds)")
        if unknown:
            return dict(base, ok=False, why="a kept store could not be read: %s — UNKNOWN, not intact" % ", ".join(unknown))
        if touched:
            return dict(base, ok=False, why="a reset must never change %s — it did" % ", ".join(touched))
        return dict(base, ok=True, why="Reset assignments never rebuilds · kept stores unchanged" + made)
    if rebuilt_n is None or held_n is None:
        return dict(base, ok=False, why="rebuilt is UNKNOWN, not 0" if rebuilt_n is None
                    else "held is UNKNOWN, not 0")
    if unknown:
        return dict(base, ok=False,
                    why="a kept store could not be read: %s — UNKNOWN, not intact" % ", ".join(unknown))
    if touched:
        return dict(base, ok=False, why="a reset must never change %s — it did" % ", ".join(touched))
    if refused_n is None:
        return dict(base, ok=False,
                    why=("rebuilt %d · held %d · the receipt does not say whether the door refused "
                         "any plan row, so that is UNKNOWN, not 0" % (rebuilt_n, held_n)))
    if refused_n:
        return dict(base, ok=False,
                    why=("rebuilt %d · held %d · %d plan row(s) the door REFUSED to re-file: %s"
                         % (rebuilt_n, held_n, refused_n, _refusals_say(refused_rows))))
    return dict(base, ok=True,
                why="rebuilt %d · held %d · refused 0 · %s · kept stores unchanged%s"
                    % (rebuilt_n, held_n, rebuilt_rarity_say(by_rarity, rebuilt_n), made))
