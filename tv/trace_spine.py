# -*- coding: utf-8 -*-
"""THE SPINE — follow ONE named item across all four hops, and say where it STOPPED.

HIS ORDER, 2026-09-15: *"just making sure the routes and flows are properly connected and wired so
they flow as designed with the proper safeguards designed so when we soon test pinpointed reel and
scenarios and templates we will be able to really tell if they end up where they are suppose to end
up"* — and the negative half, which is the one that actually proves a filter exists: *"or a
chronicle scenario or a farming scenario it can not be vaulted"*.

★ WHY NOTHING COULD ANSWER THAT YET. Every hop is measurable on its own and NOTHING followed one
item across all four:

      reel ──▶ ledger ──▶ routing decision ──▶ endpoint (vault | chronicle | thrown)

A scenario test built on today's surfaces can only say THE COUNTS MOVED. It cannot say that *his*
item took the right road, and it cannot say that a farming reel put nothing in the vault.

★ THIS MODULE REPORTS. IT NEVER WRITES. Footage has no un-delete and the banking path is gated on
witnesses deliberately (console_doctor.py:721). The spine makes the road legible; the existing
witnessed machinery stays the only thing that writes.

═══ WHAT IT REUSES RATHER THAN RE-DERIVES ═════════════════════════════════════════════════════
Every predicate below already exists and is already someone's law. A second copy of any of them is
a second thing that drifts, and this file is a reader, not a second opinion. [[copy-drift]]

    chronicle_retro._reel_key   the reel-id normaliser (v1824)
    chronicle_retro.witnesses   the independence verdict
    extract_gap.holding_possible  PANEL/FLOOR/CHRONICLE -> can a holding exist (v2772)
    shelf_driver.OWED_BY / READ_CLEARS   which lane owes a reel, and what a READ can clear
    vault_bank.state            the ONE reader for the stash-side bank (v3171)
    bible.html _VAULT_LANES     PARSED, never re-typed — see _vault_lanes()

═══ THREE THINGS MEASURED WHILE BUILDING IT, EACH OF WHICH CHANGES A READING ═══════════════════

1. ⚠⚠ 3,914 OF HIS 8,517 SIGHTINGS ARE THE SAME ROW TWICE. `read_reel` takes
   `sid = idx.get("sessionId") or os.path.basename(reel_dir)`, so one reel lands as both
   "s_1786999742937_35523" and "reel_s_1786999742937_35523". Measured on chron_evidence.json:
   25 distinct reel strings are 15 real reels; 318 of 324 names carry a reel under both spellings.

   THE GATE IS SAFE AND THE NUMBERS ARE NOT. v1824 already normalises inside `witnesses()`, and it
   holds: 0 of 324 names change their witness tags after de-duplication, and 0 change their game
   date. But `count` (control_app.py:21027, `len(sightings)`) and `in_game_stamp`'s agreement `n`
   count ROWS, so 318 of 324 names report an inflated figure — 8,499 reported against 6,481 real,
   31% inflation, worst case Bloodmoon at 136 reported for 114 real.

   So this module reports `rows` and `independent` SIDE BY SIDE and never publishes one alone.
   A confidence built by re-sampling one witness is the 83/83 shape: 2 attacks x 40 reels, true
   0.5655. [[unknown-stays-unknown]] [[zero-needs-a-denominator]]

2. ⚠ THE TWO SWEEPS DISAGREE ABOUT THE KEY NAME. The chronicle sweep hangs sightings as `reel`;
   the vault sweep hangs witnesses as `session`. Same fact, two spellings — bible.html:45011
   already compensates board-side. So does `_sightings_of` here.

3. ⚠ A REFUSAL NAMES A FRAME, NOT AN ITEM. chron_evidence's 262 refusals are
   `{reel, frame, why}` with `reel: "hist"`. So "where was item X refused" is a question the data
   cannot answer, and the spine says UNKNOWN rather than inventing a clean "never refused".

═══ CHECKED AND REFUTED, recorded so nobody re-opens it ════════════════════════════════════════
`extract_gap.PANEL_SCENES` contains "inventory" and bible.html's `_VAULT_LANES` does not, which
reads as two filters disagreeing about one decision. It is not. `reel_segments._ACTIVITY_LANE`
maps `"inventory": None` ON PURPOSE — v2343 shipped `"inventory": "inventory"`, wrongly granted a
container lane to 8 names (Storm Emblem, Cloudy Sphere, Small Charm of Good...), and it was
reverted. The two files ask different questions: PANEL asks "can a CELL exist" (an inventory has
cells), the whitelist asks "does he OWN it" (holding is not owning). Both are right.
"""
import io
import json
import os
import re
import sys

try:
    from console_safe import enable as _console_safe_enable
    _console_safe_enable()
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

BIBLE = os.path.join(ROOT, "bible.html")

#: the four hops, in order. A trace names the hop it stopped at by this id.
HOPS = ("reel", "ledger", "routing", "endpoint")


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# READING — every source can be UNREADABLE, and unreadable is never empty
# ═══════════════════════════════════════════════════════════════════════════════════════════════
def _load(name):
    """-> (obj, why). UNREADABLE IS NOT EMPTY. A missing bank and an empty bank are different
    facts and a trace that folds them reports a clean zero for a broken road."""
    p = os.path.join(HERE, name)
    if not os.path.isfile(p):
        return None, "%s is not on disk" % name
    try:
        return json.load(io.open(p, encoding="utf-8")), ""
    except Exception as e:
        return None, "%s could not be parsed (%s)" % (name, e)


def _reel_key(r):
    """The v1824 normaliser. Imported rather than re-implemented — if chronicle_retro is
    unreachable we FAIL LOUD instead of quietly counting one reel as two."""
    import chronicle_retro as _cr
    return _cr._reel_key(r)


def name_key(n):
    """Join key for a NAME. Case-folded, and the apostrophe glyphs unified.

    ⚠ MEASURED 2026-09-06 on his own store: "Saracen's Chance" is written with a STRAIGHT
    apostrophe (U+0027) in d2r_owned and a CURLY one (U+2019) in foundLog, gameFound AND the
    evidence ledger. It has testimony in all three and an exact-string join finds none of it —
    that one byte was reported as a missing record before it was reported as a glyph.
    """
    s = str(n or "")
    s = s.replace("’", "'").replace("ʼ", "'").replace("´", "'")
    return " ".join(s.lower().split())


def _vault_lanes():
    """The vault whitelist, PARSED OUT OF bible.html. -> (lanes, why)

    ⚠ NOT RE-TYPED. `_VAULT_LANES` is the front end's law about which locations may claim a vault
    row. A copy here would be a second list that drifts, and the drift would be silent in exactly
    the direction that matters — a lane added there and not here reads as "refused" in this trace
    while the real door lets it through. Anchored at BOTH ends. [[copy-drift]] [[source-reading-guard]]
    """
    if not os.path.isfile(BIBLE):
        return None, "bible.html is not on disk, so the vault whitelist is UNKNOWN"
    try:
        src = io.open(BIBLE, encoding="utf-8").read()
    except Exception as e:
        return None, "bible.html could not be read (%s)" % e
    m = re.search(r"window\._VAULT_LANES\s*=\s*\[(.*?)\]\s*;", src, re.S)
    if not m:
        return None, ("window._VAULT_LANES is no longer declared in bible.html — the whitelist "
                      "this trace judges against is UNKNOWN, not empty")
    lanes = tuple(x.strip().strip("'\"") for x in m.group(1).split(",") if x.strip())
    return (lanes, "") if lanes else (None, "window._VAULT_LANES parsed to an EMPTY list")


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# HOP 1 — THE REEL
# ═══════════════════════════════════════════════════════════════════════════════════════════════
def _sightings_of(key, chron, vault_accum, vault_seen):
    """Every sighting of this name, from BOTH sweeps, in one vocabulary.

    The chronicle sweep writes `reel`; the vault sweep writes `session`. Same fact, two keys —
    bible.html:45011 already bridges them board-side and so does this. `lane` is kept because a
    second LANE is an independent witness in a way a second frame is not.
    """
    out = []
    for n, sl in ((chron or {}).get("uniques") or {}).items():
        if name_key(n) != key:
            continue
        for s in (sl or []):
            if not isinstance(s, dict):
                continue
            out.append({"reel": s.get("reel"), "frame": s.get("frame"),
                        "lane": s.get("lane") or "claude", "conf": s.get("conf"),
                        "witness": s.get("witness"), "src": "chronicle"})
    for store, tag in ((vault_accum, "vault-accum"), (vault_seen, "vault-seen")):
        rows = (store or {}).get("owned") or (store or {}).get("rows") or []
        for r in rows:
            if not isinstance(r, dict) or name_key(r.get("name")) != key:
                continue
            for w in (r.get("witnesses") or []):
                if not isinstance(w, dict):
                    continue
                out.append({"reel": w.get("reel") or w.get("session"), "frame": w.get("frame"),
                            "lane": w.get("lane") or r.get("lane"), "conf": w.get("conf"),
                            "witness": None, "src": tag})
    return out


def independence(sightings):
    """rows vs INDEPENDENT evidence, published together and never one alone.

    Independent = a different REEL (normalised), a different LANE. Two rows that differ only in
    how the reel id was spelled are ONE witness; counting them twice is the 83/83 defect.
    """
    rows = len(sightings or [])
    seen, uniq = set(), []
    for s in (sightings or []):
        k = (_reel_key(s.get("reel")), s.get("frame"), s.get("lane"), s.get("conf"))
        if k in seen:
            continue
        seen.add(k)
        uniq.append(s)
    reels = {_reel_key(s.get("reel")) for s in uniq if s.get("reel")}
    lanes = {s.get("lane") for s in uniq if s.get("lane")}
    confs = [s.get("conf") for s in uniq if isinstance(s.get("conf"), (int, float))]
    return {"rows": rows, "deduped": len(uniq), "duplicateRows": rows - len(uniq),
            "reels": sorted(reels), "independentReels": len(reels),
            "lanes": sorted(lanes), "bestConf": (max(confs) if confs else None),
            "confKnown": len(confs)}


def hop_reel(key, stores):
    chron, va, vs = stores["chron"], stores["vault_accum"], stores["vault_seen"]
    if chron is None and va is None and vs is None:
        return {"hop": "reel", "reached": None,
                "why": "no evidence store could be read, so whether this name was ever seen is "
                       "UNKNOWN — not no"}
    sl = _sightings_of(key, chron, va, vs)
    ind = independence(sl)
    if not sl:
        return {"hop": "reel", "reached": False, "evidence": ind,
                "why": "no sighting of this name in any evidence store — no reel ever reported it"}
    return {"hop": "reel", "reached": True, "evidence": ind,
            "why": "%d row(s) -> %d independent, across %d reel(s) and %d lane(s)"
                   % (ind["rows"], ind["deduped"], ind["independentReels"], len(ind["lanes"]))}


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# HOP 2 — THE LEDGER
# ═══════════════════════════════════════════════════════════════════════════════════════════════
def hop_ledger(key, stores):
    """Did the evidence get BANKED, and by which lane?

    ⚠ THE REJECTED ROAD IS NOT NAME-KEYED. chron_evidence's refusals are {reel, frame, why} —
    262 of them, kept on purpose — and they name a FRAME, never an item. So "was this name
    refused?" is UNKNOWN here rather than False, and saying otherwise would turn an unasked
    question into a clean answer. [[unknown-stays-unknown]]
    """
    chron = stores["chron"]
    out = {"hop": "ledger", "chronicleBanked": None, "vaultBanked": None, "refused": None,
           "refusedWhy": "refusals name a frame, never an item — this ledger cannot be asked "
                         "whether a NAME was refused"}
    if chron is None:
        out["why"] = "chron_evidence could not be read — chronicle banking is UNKNOWN"
    else:
        names = {name_key(n) for n in ((chron.get("uniques") or {}))}
        names |= {name_key(n) for n in ((chron.get("sets") or {}))}
        out["chronicleBanked"] = key in names

    try:
        import vault_bank
        st = vault_bank.state()
        # ⚠ ASK FOR A KEY THAT IS NOT THERE AND `.get` HANDS BACK None, WHICH THIS MODULE WOULD
        #   THEN PUBLISH AS A MEASUREMENT. Caught on the first smoke run: the first cut asked for
        #   "sessions"/"rows", vault_bank answers "sweptN"/"rowsBanked", and the trace printed
        #   null for both while the bank was perfectly readable — UNKNOWN wearing the clothes of a
        #   clean zero, in the module written to stop exactly that. Name the missing keys.
        _want = ("sweptN", "yieldedN", "silentN", "rowsBanked", "whyFolded",
                 "chronUniques", "chronSightings", "chronRefused")
        _absent = [k for k in _want if k not in st]
        out["vaultBank"] = {k: st.get(k) for k in _want if k in st}
        if _absent:
            out["vaultBankDrift"] = ("vault_bank.state() no longer carries %s — this trace is "
                                     "reading a shape the bank has left" % ", ".join(_absent))
        # ⚠ AND THE HEADLINE NUMBER IS THE INFLATED ONE. `chronSightings` is len(sightings) over
        #   the raw rows, so the ONE reader four organs consume publishes 8,517 where the
        #   independent figure is 6,481. Republished here beside the honest count rather than
        #   corrected in place — vault_bank is not this module's to rewrite. [[copy-drift]]
        if "chronSightings" in st:
            out["vaultBankNote"] = ("chronSightings counts ROWS, not independent evidence — see "
                                    "this module's docstring, measured 31% inflation")
    except Exception as e:
        out["vaultBank"] = None
        out["vaultBankWhy"] = "vault_bank.state() is unreachable (%s) — the stash bank is " \
                              "UNKNOWN, not empty" % e

    va, vs = stores["vault_accum"], stores["vault_seen"]
    if va is None and vs is None:
        out["vaultBanked"] = None
    else:
        rows = list((va or {}).get("owned") or []) + list((vs or {}).get("rows") or [])
        out["vaultBanked"] = any(name_key(r.get("name")) == key
                                 for r in rows if isinstance(r, dict))
    out.setdefault("why", "chronicle=%s  vault=%s" % (out["chronicleBanked"], out["vaultBanked"]))
    out["reached"] = None if (out["chronicleBanked"] is None and out["vaultBanked"] is None) \
        else bool(out["chronicleBanked"] or out["vaultBanked"])
    return out


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# HOP 3 — THE ROUTING DECISION
# ═══════════════════════════════════════════════════════════════════════════════════════════════
def scenario_of(counts, names_known=True):
    """PANEL / FLOOR / CHRONICLE and whether a holding can exist — extract_gap's law, called.

    ⚠ NOT RE-IMPLEMENTED. `holding_possible` IS the predicate his ruling produced ("if its a FLOOR
    ITEM with no stash/inventory open then obviously it cant be in the same exact route"), and it
    already covers both refusals with ONE predicate so they cannot drift apart.
    """
    import extract_gap as EG
    lead = ("PANEL" if (counts or {}).get("panel")
            else "FLOOR" if (counts or {}).get("floor")
            else "CHRONICLE" if (counts or {}).get("chronicle") else "UNKNOWN")
    hold, why = EG.holding_possible(counts, names_known=names_known)
    return {"scenario": lead, "holdingPossible": hold, "why": why}


def may_vault(loc):
    """Would the front-end door let this location claim a vault row? -> (bool|None, why)"""
    lanes, why = _vault_lanes()
    if lanes is None:
        return None, why
    t = str("" if loc is None else loc).strip().lower()
    if not t:
        return False, ("no location was established for this name, and a vault row is a claim "
                       "about WHERE it physically is — an unestablished provenance is refused, "
                       "not guessed")
    ok = t in lanes
    return ok, ("'%s' is a vault lane (%s)" % (t, ", ".join(lanes)) if ok else
                "'%s' is not a vault lane — the whitelist is %s" % (t, ", ".join(lanes)))


def hop_routing(key, stores, counts=None, loc=None, names_known=True):
    sc = scenario_of(counts or {}, names_known=names_known)
    ok, why = may_vault(loc)
    out = {"hop": "routing", "loc": loc, "mayVault": ok, "mayVaultWhy": why}
    out.update(sc)
    # the two predicates must AGREE before a vault row is allowed. Either one refusing is a refusal.
    if sc["holdingPossible"] is None or ok is None:
        out["reached"] = None
        out["why"] = "one of the two predicates could not be evaluated, so the route is UNKNOWN"
    else:
        out["reached"] = bool(sc["holdingPossible"] and ok)
        out["why"] = ("routed to VAULT — %s, and %s" % (sc["why"], why)) if out["reached"] else \
                     ("NOT routed to the vault — %s"
                      % (sc["why"] if not sc["holdingPossible"] else why))
    return out


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# HOP 4 — THE ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════════════════════
def hop_endpoint(key, stores):
    """Where did it ACTUALLY end up?

    ⚠⚠ THE SPINE IS ASYMMETRIC HERE AND THAT IS A PROPERTY OF THE DATA, NOT A BUG IN THE TRACE.
    The vault side is per-NAME on disk (vault_accum / vault_seen carry names). The chronicle side
    is COUNT-ONLY — board_tally.json holds totals per route and never a name list — so "is this
    name in d2r_foundLog" cannot be answered from disk at all. It reports UNKNOWN, which is the
    honest answer and is exactly the join a future pass has to build. [[unknown-stays-unknown]]
    """
    va, vs = stores["vault_accum"], stores["vault_seen"]
    out = {"hop": "endpoint", "vault": None, "chronicle": None,
           "chronicleWhy": "board_tally.json carries totals per route and no name list, so "
                           "per-name chronicle membership is not on disk — UNKNOWN, not absent"}
    if va is not None or vs is not None:
        hits = []
        for store, tag in ((va, "vault_accum"), (vs, "vault_seen")):
            for r in ((store or {}).get("owned") or (store or {}).get("rows") or []):
                if isinstance(r, dict) and name_key(r.get("name")) == key:
                    hits.append({"store": tag, "lane": r.get("lane"), "conf": r.get("conf"),
                                 "witnesses": len(r.get("witnesses") or [])})
        out["vault"] = bool(hits)
        out["vaultRows"] = hits
    bt, _why = _load("board_tally.json")
    if isinstance(bt, dict):
        out["boardTotals"] = {k: bt.get(k) for k in ("uniques", "sets", "runewords") if k in bt}
    out["reached"] = None if out["vault"] is None else bool(out["vault"])
    out["why"] = ("in the vault (%d row(s))" % len(out.get("vaultRows") or [])) if out["vault"] \
        else ("no vault row for this name" if out["vault"] is False else
              "the vault stores could not be read — UNKNOWN")
    return out


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# THE SPINE
# ═══════════════════════════════════════════════════════════════════════════════════════════════
def _stores():
    chron, w1 = _load("chron_evidence.json")
    va, w2 = _load("vault_accum.json")
    vs, w3 = _load("vault_seen.json")
    return {"chron": chron, "vault_accum": va, "vault_seen": vs,
            "unreadable": [w for w in (w1, w2, w3) if w]}


def spine(name, counts=None, loc=None, names_known=True, stores=None):
    """Follow ONE item across all four hops. -> dict

    `stoppedAt` names the FIRST hop that did not carry the item forward, and `stoppedWhy` says
    what stopped it. A trace that only shows successes cannot find a stall, so a hop that answers
    False AND a hop that answers None both stop the walk — and they are reported differently:
    False is a measured refusal, None is a question nobody could ask.
    """
    st = stores if stores is not None else _stores()
    key = name_key(name)
    hops = [hop_reel(key, st), hop_ledger(key, st),
            hop_routing(key, st, counts=counts, loc=loc, names_known=names_known),
            hop_endpoint(key, st)]
    stopped_at = stopped_why = None
    for h in hops:
        if h.get("reached") is not True:
            stopped_at = h["hop"]
            stopped_why = ("UNKNOWN — %s" % h.get("why")) if h.get("reached") is None \
                else h.get("why")
            break
    return {"name": name, "key": key, "hops": hops,
            "stoppedAt": stopped_at, "stoppedWhy": stopped_why,
            "complete": stopped_at is None,
            "unreadable": st.get("unreadable") or []}


#: ⟦#246⟧ the board's witness block, cut between two real boundaries of bible.html (never re-typed)
_BOARD_CUT = ("  var VAULT_WITNESS_FLOOR = 0.55;", "  function _vHomeOk(h){")


def board_would_file(sightings, loc):
    """#246 W7 — ASK THE BOARD'S OWN DOOR WHETHER IT WOULD FILE THIS. -> (True|False|None, why)

    negative() used to answer from a PYTHON MODEL of the routing (scenario_of + may_vault) and never
    drove the board. That model said a single stash sighting was allowed to vault — and the board's
    one door (window.vaultFile, #246) refuses one look: his rule is two looks, each with its own frame
    and conf. A negative law graded by a model of the filter grades the model. So the witness block
    is CUT from bible.html and executed in node, and its verdict is the answer.

    None (never False) when node or the cut is unavailable — "nobody asked the board" is not a refusal.
    [[the-unjoined-end]] [[unknown-stays-unknown]]
    """
    import shutil
    import subprocess
    node = shutil.which("node")
    if not node:
        return None, "node is not on this machine, so the board's door could not be asked"
    try:
        src = io.open(BIBLE, encoding="utf-8").read()
    except Exception as e:
        return None, "bible.html could not be read (%s)" % type(e).__name__
    a, b = _BOARD_CUT
    if src.count(a) != 1 or src.count(b) != 1:
        return None, "the board's witness block is not where this trace cuts it — UNKNOWN, not refused"
    i = src.index(a)
    j = src.index(b, i)
    looks = []
    for s in sightings or []:
        if isinstance(s, dict):
            looks.append({"session": s.get("session") or s.get("reel"), "witness": s.get("witness"),
                          "frame": s.get("frame"), "conf": s.get("conf")})
    wit = {"lane": loc, "sessions": looks, "by": "trace_spine"}
    prog = ("var window = {};\n" + src[i:j] +
            "\nprocess.stdout.write(JSON.stringify(window._vaultWitnessCheck(%s)));\n" % json.dumps(wit))
    try:
        r = subprocess.run([node, "-"], input=prog, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    except Exception as e:
        return None, "node could not run the board's block (%s)" % type(e).__name__
    if r.returncode != 0:
        return None, "the board's block would not execute: %s" % (r.stderr or "")[-200:]
    try:
        v = json.loads(r.stdout)
    except Exception:
        return None, "the board's block answered something unreadable"
    return bool(v.get("ok")), str(v.get("why") or ("files it — %d qualifying look(s) in your %s"
                                                   % (len(v.get("sessions") or []), v.get("lane"))))


def negative(sightings, counts, loc=None, names_known=True):
    """THE NEGATIVE PROOF — a FARMING or CHRONICLE scenario must produce ZERO vault rows.

    ⚠⚠ THIS IS THE HALF THAT PROVES A FILTER EXISTS. A filter that only ever says yes is
    indistinguishable from no filter at all, and extract_gap's own docstring records that the
    FLOOR arm is *currently unexercised on his store* — "of the four sealed reels carrying names,
    1 is chronicle-only and 0 are floor-only ... said out loud rather than left to look covered".
    So the floor road has never been driven by real data and can only be proven by driving it.

    ⚠ #246 W7 — `allowed` IS THE BOARD'S ANSWER NOW, NOT A MODEL'S. The two Python predicates still
    run first (a scenario that cannot hold anything is refused before the board is asked), and a
    route they allow is then put to the board's own vaultFile witness check, cut from bible.html.
    A single glimpse, a frameless look or an unsure one is refused THERE — which the model never knew.

    -> {allowed: bool|None, why, scenario, mayVault, boardFiles, boardWhy}
    """
    r = hop_routing(None, {}, counts=counts, loc=loc, names_known=names_known)
    board, bwhy = (None, "not asked — the route was refused before the board")
    allowed, why = r["reached"], r["why"]
    if r["reached"] is True:
        board, bwhy = board_would_file(sightings, loc)
        allowed = board
        why = ("%s — and the board's door files it: %s" % (r["why"], bwhy)) if board is True else \
              ("routing allowed it, and the BOARD'S DOOR REFUSED it: %s" % bwhy) if board is False else \
              ("routing allowed it; the board could not be asked, so it is UNKNOWN: %s" % bwhy)
    return {"allowed": allowed, "why": why, "scenario": r["scenario"],
            "holdingPossible": r["holdingPossible"], "mayVault": r["mayVault"],
            "boardFiles": board, "boardWhy": bwhy,
            "sightings": independence(sightings or [])}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("usage: trace_spine.py <item name> [--loc stash] [--panel N --floor N --chronicle N]")
        return 2
    name = argv[0]
    kw = {"panel": 0, "floor": 0, "chronicle": 0}
    loc = None
    for i, a in enumerate(argv):
        if a == "--loc" and i + 1 < len(argv):
            loc = argv[i + 1]
        for k in kw:
            if a == "--" + k and i + 1 < len(argv):
                kw[k] = int(argv[i + 1])
    print(json.dumps(spine(name, counts=kw, loc=loc), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
