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


def _retro_row(name, measured, recorded=None):
    """One item filed on a tier higher than its visits earn, or None. Never writes.

    `recorded` is the tier the board recorded when the caller handed it in. Without it, the
    recorded tier is what the FRAME math gives on these same rows — the math the 2026-09-27
    rebuild filed on — and `recordedBy` says so, so a derived tier never reads as the board's.
    """
    honest = tier(measured[0], measured[1])
    frames = measured[5] if len(measured) > 5 else None
    if recorded is not None:
        rec, by = recorded, "board"
    elif isinstance(frames, dict):
        rec, by = tier(frames.get("successes"), frames.get("trials"))["tier"], "frames"
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


def plan_from_ledger(path):
    """Read one witness ledger and ask rebuild_plan. Never writes the file.

    `path` is the caller's file. This does not know where his ledger lives, and a path that
    cannot be read is UNKNOWN — rebuilt stays empty and ok is false, which is not "nothing proven".

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
    items, filing, retro = [], {}, []
    for name, rows in _group(doc["owned"]):
        measured = _measure(rows, floor)
        if measured is None:
            item = {"name": name, "successes": None, "trials": None}
            extra = {"equipped": _equipped_of(rows), "kind": _kind_of(rows),
                     "cells": [], "sessions": [], "witness": None}
        else:
            successes, trials, sessions, cells, witness_sessions, _frames = measured
            flagged = _retro_row(name, measured)
            item = {"name": name, "successes": successes, "trials": trials,
                    "equipped": _equipped_of(rows), "kind": _kind_of(rows)}
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
    plan["retro"] = _retro_answer(retro, "frames")
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
            if not base or base in seen:
                continue
            seen.add(base)
            found.append(base)
    try:
        with io.open(path, "rb") as fh:
            if fh.read() != blob:
                return {"ok": False, "frames": None, "why": _UNREAD}
    except Exception:
        return {"ok": False, "frames": None, "why": _UNREAD}
    return {"ok": True, "frames": found, "why": ""}


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
              "retroHeldNames": None, "provenNames": None, "why": _UNREAD}
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
            "provenNames": proven_names, "why": why}


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
    return {"ok": True, "gone": gone, "n": len(gone), "cited": len(cited["frames"]), "why": ""}


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
    touched, unknown = [], []
    for key in sorted(set(before) | set(after)):
        if key not in before or key not in after:
            unknown.append(key)
            continue
        if before[key] != after[key]:
            touched.append(key)
    base = {"rebuilt": rebuilt_n, "held": held_n, "touched": touched, "unknown": unknown,
            "refused": refused_n, "refusedRows": refused_rows}
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
                why="rebuilt %d · held %d · refused 0 · kept stores unchanged" % (rebuilt_n, held_n))
