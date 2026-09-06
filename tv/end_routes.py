# -*- coding: utf-8 -*-
"""THE END ROUTE — reverse-engineered from the 410 reels that actually reached it.

Konyo, 2026-09-06: *"it should be also eventually tombstoned though why is not also processed
through the printer to get routed back at the end routes they should. **reverse engineeer it if
needed the ones that are working** im saying like the end routes needs to still be like they are
working if they are working obviously."*

His sentence settles the DESTINATION and not the PREDICATE, and it names the method: derive the
door from the reels that already went through it. This module is that derivation. It invents
nothing — every clause below was read back off `reel_tombstones.json` joined to the three stores
that were live when those reels were removed.

=== WHAT THE 410 ACTUALLY HAVE IN COMMON (measured 2026-09-06, his tree) ================

    410 rows in the ledger · 5,768.1 MB · deleted 2026-08-24 -> 2026-09-01

    STRUCTURAL door   retro_triage[reel].full is True AND panels == 0      396   1,792.0 MB
    SEMANTIC door     chronicle pages >= 1 AND the vault lane is settled    11   3,880.0 MB
    SEMANTIC, vault unconfirmable (pages 71 and 35, no seal, reel gone)      2      96.1 MB
    UNEXPLAINED                                                              1       9.5 MB

⚠⚠ SO THE DOOR THAT CARRIED 96.6% OF ALL END-ROUTE TRAFFIC IS **"THERE IS NOTHING HERE TO READ"**,
NOT "IT WAS READ". Of the 396 that went structural: **394 had `pages: 0`**, **392 had no vault seal
at all**, and **54 had no chronicle row whatsoever**. They were never read and never sealed. The
FREE structural pass surveyed every frame and found no panel on any of them, so there was nothing
for either lane to take.

⚠⚠ AND THE PERMANENT RECORD OF THAT IRREVERSIBLE ACT SAYS THE OPPOSITE. All 410 tombstones carry
`why: "read (N pages) and sealed by BOTH lanes — it has given up its information"`, written by
`reel_retention.plan()`'s single `eligible` branch. For 395 of them BOTH clauses are false. The
sentence describes the door the author had in mind, not the door the reel came through, and it is
the only record left of footage that has no un-delete. [[label-outlived-referent]]
`derived_from()` publishes that contradiction as a number rather than leaving it in prose.

=== WHY THIS IS A DISJUNCTION AND MUST STAY ONE ==========================================

Either door alone is sufficient. Conjoining them is not a stricter version of the same rule — it
is a different rule that has never once been satisfied: **392 of the 396 structural releases have
no vault seal**, so an AND would have refused 96% of every end-route journey that has ever
happened. That is the same collapse v2312 attempted on the reel/frame doors and WITHDREW at v2314.
[[feedback-contradiction-is-the-finding]]

=== WHAT THIS MODULE DECIDES, AND WHAT IT DOES NOT ======================================

It answers ONE question: **has this reel got anything left to give?** That is the CONTENT half.

It does NOT decide deletion. `reel_retention.plan()` owns the SAFETY ladder above it —
no-witness-index, ledger-unreadable, test-fixture, recent — and a reel can be QUALIFIED here and
correctly held there. Keeping the two apart is the whole point of his ruling: a reel held because
the suite opens it by name has NOT dead-ended, and a reel held because 123 unread stash panels sit
in it HAS. Today those two states are indistinguishable on every surface, because both just read
"not eligible". `report()` prints them as different columns.

**IT DELETES NOTHING, WRITES NOTHING, AND ARMS NOTHING.** The prune stays off by his 2026-09-02
ruling; this is a reader.

=== THE VALUABLE HALF: WHAT SPECIFICALLY IS MISSING ======================================

Every refusal names the artifact, the measured value and the needed value. A gap nobody has
measured carries `measured: None` and says so — `0` is measured-and-zero, `None` is nobody looked,
and this module never collapses them. [[unknown-stays-unknown]]

    python3 tv/end_routes.py                 # the shelf, one line per reel
    python3 tv/end_routes.py <reel>          # one reel, every clause
    python3 tv/end_routes.py --derived       # the 410 the predicate was derived FROM
    python3 tv/end_routes.py --json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

#: The two doors, in the order they are asked. STRUCTURAL first because it is FREE and because it
#: is how 96.6% of the ledger actually left.
DOORS = ("structural", "semantic")

DOOR_QUESTION = {
    "structural": "did a FULL structural pass find no panel at all? (free, no model call)",
    "semantic": "did the chronicle lane read a page, and is the vault lane settled?",
}

#: The stores each door reads, and who owns them. Named so a reader can check the claim.
DOOR_STORE = {
    "structural": ("retro_triage.json", "retro_triage"),
    "semantic": ("chronicle_swept.json + vault_swept.json", "reel_retention.plan"),
}

#: What the ledger must still look like for this predicate to be a DERIVATION rather than an
#: invention. If someone edits a door, `derived_from()` stops explaining the reels it came from
#: and `test_end_routes.py` goes red. See THE SELF-REFUTING LAW in that file.
DERIVED_COVERAGE_FLOOR = 0.95


def _min_pages():
    """The page floor, from its owner. -> (int, why)

    ⚠ NOT A LOCAL CONSTANT. `reel_retention.MIN_PAGES` is the number the deleter actually used on
    the 410, and a second copy here would be free to drift away from the door it claims to
    describe. If the owner cannot be reached the floor is UNKNOWN and the semantic door is not
    asked — never guessed at 1. [[copy-drift]] §1
    """
    try:
        import reel_retention as _rr
        v = getattr(_rr, "MIN_PAGES", None)
        if isinstance(v, bool) or not isinstance(v, int):
            return None, "reel_retention.MIN_PAGES is %r, not a whole number" % (v,)
        return v, ""
    except Exception as e:
        return None, "reel_retention would not import (%s)" % str(e)[:70]


def _lookup(store, reel):
    """One reel's row, by the AGREED key rule. -> (row, why)

    ⚠⚠ THE RULE IS reel_retention.lookup_either_way AND THERE IS NO COPY OF IT HERE. REG-563 and
    REG-564 are both this exact mistake: two modules hand-wrote the same three-key lookup with
    different precedence, and with both key forms present they returned DIFFERENT ROWS for the
    same reel. reel_river quotes the owner for the same reason. If the owner cannot be reached the
    answer is UNKNOWN, not a private guess that happens to be narrower.
    [[copy-drift]] [[unknown-stays-unknown]]
    """
    if not isinstance(store, dict):
        return None, "the store is not a mapping"
    try:
        import reel_retention as _rr
        return _rr.lookup_either_way(store, reel), ""
    except Exception as e:
        return None, ("the reel-lookup rule is unavailable (%s), so this store could not be "
                      "asked the agreed way" % str(e)[:70])


def _read(path):
    """-> (blob, state) where state is 'ok' | 'absent' | 'unreadable'.

    ⚠ ABSENT AND UNREADABLE ARE DIFFERENT FACTS. "no survey has ever run" and "the survey exists
    and will not parse" point at opposite actions, and only one of them is safe to act on.
    """
    if not os.path.isfile(path):
        return None, "absent"
    try:
        with open(path, "r", encoding="utf-8") as fh:
            blob = json.load(fh)
        return (blob if isinstance(blob, dict) else None), ("ok" if isinstance(blob, dict)
                                                            else "unreadable")
    except Exception:
        return None, "unreadable"


def _store_paths(hist_dir=None):
    """Where each store lives. -> dict of name -> path

    Two of these files have an OWNER WITH ITS OWN RESOLVER and this asks it rather than
    re-deriving: `retro_triage._store_path` and `reel_retention._tombstone_path`. Neither falls
    back to a second directory, and a private copy of a path rule is REG-563's class one file over.
    [[copy-drift]] §1

    ⚠⚠ AND UNDER A REDIRECT THERE IS NO FALLBACK TO HERE, WHICH DELIBERATELY DIFFERS FROM
    `reel_retention.plan._pick`. `_pick` tries the caller's directory then HERE, so the deleter
    never loses sight of a ledger. Mirroring that here was the FIRST cut and its own gate caught
    it: a fixture that omitted `reel_tombstones.json` silently read HIS LIVE 410-row ledger, and
    the law asserting an absent ledger reads UNKNOWN passed against real data it could not
    control — REG-570 exactly, reproduced inside the fix for a module about REG-570.
    A reader that cannot be pointed at a fixture cannot be graded at all, and this module is a
    reader. With no redirect in play the order is unchanged: HERE, where all four live.
    [[feedback-fixtures-never-touch-live-data]] [[gate-blind-to-unexercised-input]]
    """
    hist = hist_dir or os.environ.get("TV_HIST") or ""
    redirected = bool(hist)
    base = os.path.realpath(hist) if redirected else HERE
    out = {}
    try:
        import retro_triage as _rt
        out["retro_triage.json"] = _rt._store_path(root=base) if redirected else _rt._store_path()
    except Exception:
        out["retro_triage.json"] = os.path.join(base, "retro_triage.json")
    try:
        import reel_retention as _rr
        out["reel_tombstones.json"] = _rr._tombstone_path(base if redirected else None)
    except Exception:
        out["reel_tombstones.json"] = os.path.join(base, "reel_tombstones.json")
    for nm in ("chronicle_swept.json", "vault_swept.json"):
        if redirected:
            out[nm] = os.path.join(base, nm)
            continue
        pick = None
        for d in (HERE, base):
            p = os.path.join(d, nm)
            if os.path.isfile(p):
                pick = p
                break
        out[nm] = pick or os.path.join(HERE, nm)
    return out


def sources(hist_dir=None):
    """Every store this predicate reads, taken ONCE. -> dict

    Taken once and shared so two doors on the same row cannot disagree about the same reel because
    they asked at different moments — the rule `printer._sources` follows for the same reason.
    """
    paths = _store_paths(hist_dir)
    out = {"paths": paths, "unreadable": [], "absent": []}
    for nm, key in (("retro_triage.json", "structural"),
                    ("chronicle_swept.json", "chronicle"),
                    ("vault_swept.json", "vault"),
                    ("reel_tombstones.json", "ledger")):
        blob, st = _read(paths[nm])
        out[key] = blob
        out[key + "State"] = st
        if st == "unreadable":
            out["unreadable"].append(nm)
        elif st == "absent":
            out["absent"].append(nm)
    out["minPages"], out["minPagesWhy"] = _min_pages()
    return out


def _gap(what, measured, needed, why):
    """One named, refutable gap.

    ⚠ `measured is None` means NOBODY LOOKED and is never written for a measured zero. A caller
    tallying "how much is missing" must be able to tell the two apart without reading English.
    """
    return {"what": what, "measured": measured, "needed": needed, "why": why,
            "looked": measured is not None}


def structural_door(reel, src):
    """Has a FULL pass proven this reel holds no panel at all? -> (opened, gaps, evidence)

    `opened` is True / False / None(could not ask). This is `reel_retention._proven_empty`'s
    question, asked non-destructively and made to explain itself.

    ⚠⚠ A PARTIAL PASS IS NOT AN EMPTY ONE, and this is the clause that protects footage.
    `retro_triage.survey` refuses to produce a disposal list from a sampled pass, and every one of
    the 396 reels that left by this door carries `full: true`. A sampled pass that happened to miss
    the only stash frame would look identical to a genuinely empty reel. [[unknown-stays-unknown]]
    """
    ev = {"full": None, "panels": None, "surveyedFrames": None, "kinds": None}
    if src.get("structuralState") == "unreadable":
        return None, [_gap("a readable structural survey", None, "retro_triage.json to parse",
                           "retro_triage.json exists and will not parse, so what this reel holds "
                           "is UNKNOWN — not 'nothing'")], ev
    row, why = _lookup(src.get("structural") or {}, reel)
    if why:
        return None, [_gap("the structural survey", None, "the agreed lookup rule", why)], ev
    if row is None:
        return None, [_gap("a structural survey", None, "one full retro_triage pass",
                           "no structural pass has ever recorded this reel, so whether it holds a "
                           "panel is UNKNOWN. This is the FREE pass — running it costs no model "
                           "call.")], ev
    ev["full"] = bool(row.get("full"))
    _p = row.get("panels")
    ev["panels"] = _p if isinstance(_p, int) and not isinstance(_p, bool) else None
    ev["surveyedFrames"] = row.get("frames")
    ev["kinds"] = dict(row.get("kinds") or {}) or None
    gaps = []
    if not ev["full"]:
        gaps.append(_gap("a FULL structural pass", "partial", "full",
                         "the survey was SAMPLED, and a sample that missed the only panel frame "
                         "reads identically to an empty reel"))
    if ev["panels"] is None:
        gaps.append(_gap("a whole-number panel count", row.get("panels"), "an int",
                         "the survey recorded a panel count that is not a whole number, so it is "
                         "UNREADABLE — which holds, exactly as REG-573 holds an unreadable page "
                         "count"))
    elif ev["panels"] > 0:
        gaps.append(_gap("panels read", ev["panels"], 0,
                         "the structural pass found %d panel frame(s)%s — this reel still has "
                         "something to give, and nothing has read it"
                         % (ev["panels"],
                            (" (" + ", ".join("%s %d" % (k, v) for k, v in
                                              sorted((ev["kinds"] or {}).items())) + ")")
                            if ev["kinds"] else "")))
    if gaps:
        return False, gaps, ev
    return True, [], ev


def semantic_door(reel, src):
    """Was it read, and is the vault lane settled? -> (opened, gaps, evidence)

    The door 13 of the 410 came through. Two clauses, and the second one has a genuine UNKNOWN:
    with no vault seal, whether the lane still OWES anything can only be answered by looking at the
    reel's frames, so for a reel already gone the answer is unknowable and is reported as such
    rather than assumed settled. Measured: 2 of the 410 are in exactly that state.
    """
    ev = {"pages": None, "vaultSealed": None, "vaultRows": None, "minPages": src.get("minPages")}
    if src.get("minPages") is None:
        return None, [_gap("the page floor", None, "reel_retention.MIN_PAGES",
                           src.get("minPagesWhy") or "the page floor's owner could not be "
                                                     "reached, so this door was not asked")], ev
    if src.get("chronicleState") == "unreadable":
        return None, [_gap("a readable chronicle ledger", None, "chronicle_swept.json to parse",
                           "chronicle_swept.json will not parse, so whether this reel was read is "
                           "UNKNOWN")], ev
    crow, why = _lookup(src.get("chronicle") or {}, reel)
    if why:
        return None, [_gap("the chronicle ledger", None, "the agreed lookup rule", why)], ev
    gaps = []
    if crow is None:
        gaps.append(_gap("a chronicle sweep", None, ">= %d page(s)" % src["minPages"],
                         "the chronicle lane has never recorded this reel — it has not been read "
                         "even once"))
    else:
        _pv = crow.get("pages")
        if _pv is None or _pv == "":
            ev["pages"] = 0
        elif isinstance(_pv, bool) or not isinstance(_pv, int):
            # REG-573, one file over: a page count that is not a whole number is not a small
            # count, it is an unreadable ledger, and it holds.
            gaps.append(_gap("a whole-number page count", _pv, "an int",
                             "pages=%r is not a whole number, so the read is UNREADABLE" % (_pv,)))
        else:
            ev["pages"] = _pv
        if ev["pages"] is not None and ev["pages"] < src["minPages"]:
            gaps.append(_gap("chronicle pages", ev["pages"], src["minPages"],
                             "sealed with %d page(s) — that is 'this reader found nothing', not "
                             "'done'; the engine reopens these when the prompt improves"
                             % ev["pages"]))
    # ── the vault clause ──────────────────────────────────────────────────────────────────────
    if src.get("vaultState") == "unreadable":
        gaps.append(_gap("a readable vault ledger", None, "vault_swept.json to parse",
                         "vault_swept.json will not parse, so whether the vault lane is finished "
                         "is UNKNOWN — not 'yes'"))
    else:
        vrow, vwhy = _lookup(src.get("vault") or {}, reel)
        if vwhy:
            gaps.append(_gap("the vault ledger", None, "the agreed lookup rule", vwhy))
        elif vrow is None:
            ev["vaultSealed"] = False
            gaps.append(_gap("a vault seal", None, "one vault sweep",
                             "the VAULT lane has never swept it. Whether it still OWES stash rows "
                             "can only be answered from the reel's own frames — 2 of the 410 left "
                             "in exactly this state and it is not re-checkable now they are gone"))
        else:
            ev["vaultSealed"] = True
            ev["vaultRows"] = vrow.get("rows")
    if gaps:
        return False, gaps, ev
    return True, [], ev


def verdict(reel, src=None, hist_dir=None):
    """Does THIS reel qualify for the end route, and if not, what exactly is missing? -> dict

    say: QUALIFIED (a door opened) · HELD (every door that could be asked refused, with numbers) ·
    UNKNOWN (no door could be asked at all).

    ⚠ HELD NEVER HIDES AN UNASKED DOOR. `unasked` names any door that could not be put, and each
    such door contributes a gap whose `measured` is None. A reel refused on one door while the
    other was never asked is a reel that MIGHT qualify, and the row says so rather than reading as
    a settled refusal. [[unknown-stays-unknown]] [[zero-needs-a-denominator]]
    """
    src = src if src is not None else sources(hist_dir)
    doors, gaps, ev, opened, unasked = {}, [], {}, [], []
    for nm, fn in (("structural", structural_door), ("semantic", semantic_door)):
        o, g, e = fn(reel, src)
        doors[nm] = o
        ev[nm] = e
        gaps.extend([dict(gg, door=nm) for gg in g])
        if o is True:
            opened.append(nm)
        elif o is None:
            unasked.append(nm)
    asked = [d for d in DOORS if doors[d] is not None]
    if opened:
        say = "QUALIFIED"
        why = ("the %s door opened: %s. Its evidence: %s"
               % (opened[0], DOOR_QUESTION[opened[0]],
                  json.dumps(ev[opened[0]], sort_keys=True)))
    elif not asked:
        say = "UNKNOWN"
        why = ("neither door could be asked, so whether this reel has anything left to give is "
               "UNKNOWN — not 'no'. " + "; ".join(g["why"] for g in gaps))
    else:
        say = "HELD"
        why = ("%d door(s) asked and refused; %s. %s"
               % (len(asked),
                  ("no door was left unasked" if not unasked
                   else "⚠ the %s door was NEVER ASKED, so this refusal is not settled"
                        % " and ".join(unasked)),
                  " · ".join("%s: %s" % (g["what"], g["why"]) for g in gaps)))
    # ⚠⚠ `missing` IS ABOUT THE END ROUTE, NOT ABOUT EACH DOOR — and the first cut got this wrong
    # in the direction that matters, publishing the REFUSING door's gaps on a QUALIFIED reel. Its
    # own gate caught it on his real store: reel_s_1785082633657_72378 came back QUALIFIED while
    # still listing "chronicle pages: 0" as missing, which is a reel that has reached the end route
    # being described as stuck. The docstring above already said `missing` is [] when a door opens;
    # the code said otherwise, which is the comments-vs-code scar inside the fix for it.
    # The other door's findings are not thrown away — they ride in `doorGaps`, named by door, as
    # context rather than as a blocker. [[feedback-comments-vs-code]] [[label-outlived-referent]]
    return {"reel": reel, "say": say, "door": (opened[0] if opened else None),
            "openedDoors": opened, "askedDoors": asked, "unaskedDoors": unasked,
            # [] = measured, nothing is missing · None = nothing could be asked. Same rule as
            # `measured` on a gap: never collapse the two.
            "missing": ([] if say == "QUALIFIED" else (gaps if say == "HELD" else None)),
            "doorGaps": gaps,
            "unmeasuredGaps": sum(1 for g in gaps if g["measured"] is None),
            "evidence": ev, "why": why}


# ══ THE DERIVATION — the 410 this predicate was read off ═══════════════════════════════════════

def derived_from(hist_dir=None, src=None):
    """Re-run the predicate over every reel that ALREADY reached the end route. -> dict

    ⚠⚠ THIS IS THE PART THAT MAKES THE PREDICATE A DERIVATION RATHER THAN AN OPINION. His ruling
    said *"reverse engineeer it if needed the ones that are working"*. So the doors above are
    checked against the reels they were read off, every run: if a door is edited and the ledger
    stops being explained, `coverage` falls and the gate goes red. A predicate that no longer
    describes the journeys it came from is an invention wearing a derivation's clothes.

    ⚠ THE LEDGER'S ROWS NAME REELS THAT ARE GONE, so the two doors are asked from the STORES only
    — the reel's own frames cannot be consulted. Where that makes a clause unanswerable the row
    lands in `semanticUnconfirmed`, never quietly in `semantic`.
    """
    src = src if src is not None else sources(hist_dir)
    if src.get("ledgerState") != "ok":
        return {"ok": False, "rows": None, "why": "the tombstone ledger is %s (%s), so how many "
                                                  "reels have reached the end route is UNKNOWN — "
                                                  "not zero"
                % (src.get("ledgerState"), src["paths"]["reel_tombstones.json"])}
    rows = (src.get("ledger") or {}).get("reels") or []
    by_door, unexplained, label_lies, nameless = {}, [], 0, 0
    mb = {}
    for r in rows:
        if not isinstance(r, dict):
            nameless += 1
            continue
        nm = str(r.get("reel") or "").strip()
        if not nm:
            nameless += 1
            continue
        v = verdict(nm, src=src)
        s_open = v["evidence"]["structural"]
        sem = v["evidence"]["semantic"]
        if "structural" in v["openedDoors"]:
            bucket = "structural"
        elif "semantic" in v["openedDoors"]:
            bucket = "semantic"
        elif ((sem.get("pages") or 0) >= (src.get("minPages") or 1)
              and sem.get("vaultSealed") is False):
            # read, but the vault clause cannot be settled now the frames are gone.
            bucket = "semanticUnconfirmed"
        else:
            bucket = "unexplained"
            unexplained.append({"reel": nm, "mb": r.get("mb"),
                                "pages": sem.get("pages"), "panels": s_open.get("panels"),
                                "why": v["why"][:220]})
        by_door[bucket] = by_door.get(bucket, 0) + 1
        mb[bucket] = round(mb.get(bucket, 0.0) + float(r.get("mb") or 0), 1)
        # ⚠ THE LABEL CHECK. Every tombstone claims "sealed by BOTH lanes". Count the ones where
        # no vault seal exists at all — the permanent record of an act with no undo, describing a
        # door the reel did not come through. [[label-outlived-referent]]
        if "sealed by BOTH lanes" in str(r.get("why") or "") and sem.get("vaultSealed") is not True:
            label_lies += 1
    n = sum(by_door.values())
    explained = by_door.get("structural", 0) + by_door.get("semantic", 0)
    cov = (float(explained) / n) if n else None
    return {
        "ok": True, "rows": n, "nameless": nameless, "byDoor": by_door, "mbByDoor": mb,
        "unexplained": unexplained, "coverage": (round(cov, 4) if cov is not None else None),
        "coverageFloor": DERIVED_COVERAGE_FLOOR,
        "labelContradictions": label_lies,
        "why": ("%s of %d ledger row(s) are explained by a door this module still asks (%.2f%%, "
                "floor %.0f%%). %s ⚠ %d row(s) carry 'sealed by BOTH lanes' in the permanent "
                "record with no vault seal in any store."
                % (explained, n, (cov or 0) * 100, DERIVED_COVERAGE_FLOOR * 100,
                   ("Every row is explained." if not unexplained else
                    "UNEXPLAINED: " + ", ".join(u["reel"] for u in unexplained[:6])),
                   label_lies)
                if n else "the ledger holds no rows, so nothing could be derived from it"),
    }


# ══ THE SHELF ══════════════════════════════════════════════════════════════════════════════════

def _safety(hist_dir=None):
    """reel_retention's SAFETY ladder, per reel. -> (dict reel->tag, why)

    Its own question, asked of its owner and never re-derived here. A reel QUALIFIED by content and
    held by `test-fixture` has not dead-ended; a reel held by `zero-pages` has. Today every surface
    renders both as "not eligible", which is the distinction his ruling turns on.
    """
    try:
        import reel_retention as _rr
        p = _rr.plan(hist_dir=hist_dir)
        if not p.get("ok"):
            return None, str(p.get("why") or "reel_retention.plan would not answer")
        tags = {}
        for k in (p.get("kept") or []):
            tags[k.get("reel")] = k.get("tag")
        for c in (p.get("candidates") or []):
            tags[c.get("reel")] = c.get("tag") or "eligible"
        return tags, ""
    except Exception as e:
        return None, "reel_retention.plan would not answer (%s)" % str(e)[:90]


#: Which safety tags are about the REEL's content and which are about circumstance. A content tag
#: means the ladder and this module are answering the same question; a circumstance tag means the
#: reel is finished and held for a reason that has nothing to do with what is in it.
CIRCUMSTANTIAL_HOLDS = ("recent", "test-fixture", "target-met", "no-witness-index",
                        "ledger-unreadable")


def report(hist_dir=None, safety=True):
    """Every reel on the shelf, its verdict, and what is missing. -> dict. Writes nothing."""
    src = sources(hist_dir)
    hist = hist_dir or os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")
    try:
        reels = sorted(d for d in os.listdir(hist) if d.startswith("reel_"))
        walk_why = ""
    except OSError as e:
        reels, walk_why = [], "cannot read %s (%s)" % (hist, str(e)[:70])
    tags, tag_why = (_safety(hist_dir) if safety else (None, "safety ladder not asked"))
    rows, counts = [], {}
    for r in reels:
        v = verdict(r, src=src)
        v["safetyHold"] = (tags or {}).get(r) if tags is not None else None
        v["safetyHoldWhy"] = tag_why or None
        # ⚠ THE COLUMN HIS RULING NEEDS. QUALIFIED + a circumstantial hold = finished, waiting.
        # HELD = actually dead-ended, and `missing` says on what.
        v["deadEnded"] = (v["say"] == "HELD")
        v["finishedWaiting"] = (v["say"] == "QUALIFIED"
                                and v["safetyHold"] in CIRCUMSTANTIAL_HOLDS)
        rows.append(v)
        counts[v["say"]] = counts.get(v["say"], 0) + 1
    return {"ok": bool(rows), "hist": hist, "walked": len(reels), "rows": rows, "counts": counts,
            "doors": list(DOORS), "questions": dict(DOOR_QUESTION), "stores": dict(DOOR_STORE),
            "unreadableStores": src.get("unreadable"), "absentStores": src.get("absent"),
            "safetyAsked": tags is not None, "safetyWhy": tag_why or None,
            "derivedFrom": derived_from(hist_dir, src=src),
            "deadEnded": sum(1 for r in rows if r["deadEnded"]),
            "finishedWaiting": sum(1 for r in rows if r["finishedWaiting"]),
            "why": (walk_why or
                    ("%d reel(s) on the shelf: %d dead-ended (every door refused, with numbers), "
                     "%d finished and held only by circumstance. ⚠ A dead-ended reel is what his "
                     "ruling forbids; a finished-waiting one is not."
                     % (len(rows), sum(1 for r in rows if r["deadEnded"]),
                        sum(1 for r in rows if r["finishedWaiting"]))))}


def reprocessing_list(hist_dir=None):
    """Which reels would reach the end route if the missing thing were supplied. -> dict

    ⚠ IT NAMES THEM AND STOPS. It runs nothing, spends nothing and deletes nothing — the reels
    listed carry unread panels, and reading them is a paid lane behind his standing ruling.
    """
    rep = report(hist_dir)
    out = []
    for r in rep["rows"]:
        if r["say"] != "HELD":
            continue
        panels = (r["evidence"]["structural"] or {}).get("panels")
        out.append({"reel": r["reel"], "panels": panels,
                    "pages": (r["evidence"]["semantic"] or {}).get("pages"),
                    "safetyHold": r.get("safetyHold"),
                    "missing": [g["what"] for g in (r["missing"] or [])]})
    out.sort(key=lambda x: -(x["panels"] or 0))
    return {"ok": rep["ok"], "reels": out, "n": len(out),
            "panels": sum((x["panels"] or 0) for x in out),
            "why": "%d reel(s) hold %s unread panel frame(s) between them. Reading them is the "
                   "ONLY thing between these reels and the end route the other 410 went through."
                   % (len(out), sum((x["panels"] or 0) for x in out))}


def main(argv):
    reel = next((a for a in argv if not a.startswith("-")), None)
    if "--derived" in argv:
        d = derived_from()
        print(json.dumps(d, indent=2, sort_keys=True) if "--json" in argv else
              "\nDERIVED FROM — the reels that already reached the end route\n\n  %s\n\n  %s\n"
              % (json.dumps(d.get("byDoor"), sort_keys=True), d.get("why")))
        return 0
    if reel:
        v = verdict(reel)
        if "--json" in argv:
            print(json.dumps(v, indent=2, sort_keys=True, default=str))
            return 0
        print("\n  %s  ->  %s\n" % (reel, v["say"]))
        for g in (v["missing"] or []):
            print("     MISSING  %-28s measured=%-8s needed=%-8s"
                  % (g["what"], g["measured"], g["needed"]))
            print("              %s" % g["why"][:150])
        print("\n  %s\n" % v["why"][:400])
        return 0
    r = report()
    if "--json" in argv:
        print(json.dumps(r, indent=2, sort_keys=True, default=str))
        return 0
    print("\nTHE END ROUTE — derived from the %s reel(s) that already reached it\n"
          % (r["derivedFrom"].get("rows") if r["derivedFrom"].get("ok") else "UNKNOWN"))
    print("  %s\n" % r["derivedFrom"].get("why", ""))
    for row in r["rows"]:
        ev = row["evidence"]["structural"]
        print("  %-32s %-10s %-16s panels=%-5s pages=%-5s"
              % (row["reel"][:32], row["say"], row.get("safetyHold") or "-",
                 ev.get("panels"), (row["evidence"]["semantic"] or {}).get("pages")))
    print("\n  %s\n" % r["why"])
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
