"""v1571 — VAULT ACCUMULATOR, the engine. Retro sweep of the sealed reels for what he OWNS.

Konyo: *"the vault manager is synced to also slowly analyze and remember especially between and among
sessions ... it should eventually in retro KAI READERS get a read on it and slowly also feed the vault
manager for throwing out or muling the items read at the time."*

RETRO IS THE PRIORITY LANE. A live read has one look at a panel; the sealed reels have every look he
has ever given one, and a mini stash session (MC-03) is the densest evidence in the whole archive —
he is parked, not fighting, and the panel is held still. So the sweep prefers those reels first.

This module is the CHRONICLE SWEEP pointed at a different target. It does not re-implement it: the
signature function, STILL_MAX_DIFF, MIN_RUN_FRAMES, the still-run grouping, the blank-capture probe
and the within-run dedupe are all imported from `chronicle_retro`. Two copies of a threshold
calibrated on his footage is two things that drift apart, and only one of them would get re-tuned.

THE FIVE LAWS, in his terms:

  1. MERGE-MAX ACROSS SESSIONS. A read NEVER lowers a count and never removes a row. An obstructed
     or half-scrolled stash frame is a NORMAL event, not evidence he threw something away. A later
     session that sees fewer says so in `held` and changes nothing. No ordering of the inputs can
     change the answer — every fold here is a max() or a sorted union.

  2. MULTI-WITNESS CORROBORATION. A name grounds on TWO INDEPENDENT witnesses, and independence is
     counted in SESSIONS: two still-runs inside one reel are the same eye looking twice at the same
     stash, so they are ONE witness. One witness goes to `unsure`, never to `owned`.

  3. THERE IS NO UN-THROW IN DIABLO. Advising him to bin an item is the only irreversible act in the
     whole app, so a throw-out clears a STRICTLY higher bar than a keep on BOTH axes — confidence and
     witnesses — and can never be reached on single-session evidence however confident the reader is.
     Everything in `throwOut` is a SUGGESTION for the Vault manager to show him. Nothing here is
     automatic and nothing here is a write.

  4. HONEST-ABSENT. An unknown count stays None; it never defaults to 1. A run that cannot be
     classified is `held` with a why, not guessed into a lane. A name the reader did not return is
     never invented. A missing sig/reader/classify returns ok:False with a why — never a fabricated
     empty success, which is the one failure shape that looks exactly like "you own nothing".

  5. NEVER WRITE. No filesystem writes, no ledger, no board access, no second apply path.
     `apply_payload()` only SHAPES the proposal so the caller can hand it to the ONE existing apply
     (window.chronicleApply), which owns the date stamp, the merge-max and the undo bar.

Pure by construction: the caller injects the signature fn, the classifier and the reader, so the
tests drive every law from fixtures with zero JPEGs and zero vision calls.
"""

import glob
import os
import json
import time

try:
    import chronicle_retro as _cr
except ImportError:  # pragma: no cover — running from the repo root rather than from tv/
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import chronicle_retro as _cr


# The production signature function, BORROWED not re-typed (see the module note on drift). The caller
# passes it in — this module never picks a default for itself, because law 4 says a missing sig is an
# answer ("I was not given eyes"), not something to paper over.
DEFAULT_SIG = _cr.jpeg_sig

# Grouping thresholds live in ONE place: chronicle_retro, calibrated on Konyo's own footage.
STILL_MAX_DIFF = _cr.STILL_MAX_DIFF
MIN_RUN_FRAMES = _cr.MIN_RUN_FRAMES

# The surfaces that show what he OWNS. Anything else in the footage — town, a fight, the Chronicle,
# character select — is not evidence of ownership and is skipped without paying a read.
OWNERSHIP_SURFACES = ("stash", "inventory", "equipment", "runes", "gems", "materials")

# Which lane a surface's items land in. Runes/gems/materials are STASH TABS in his game, so their
# items are stash items; the reader may override per item when it can actually see the split.
SURFACE_LANE = {
    "stash": "stash", "runes": "stash", "gems": "stash", "materials": "stash",
    "inventory": "inventory", "equipment": "equipment",
}
LANES = ("stash", "inventory", "equipment")

# A surface that already tells us what KIND of thing is on it. Used only as a fallback when the
# reader does not say — never to invent an item, only to type one it did return.
SURFACE_KIND = {"runes": "rune", "gems": "gem", "materials": "material"}
KINDS = ("rune", "gem", "material", "item")

# ── THE TWO BARS (law 3) ────────────────────────────────────────────────────────
# These floors are REASONED, not measured — exactly as honest as the chronicle gate is about its own
# CONF_FLOOR. The keep bar matches the chronicle's (an unsure reader is unsure twice over). The throw
# bar is deliberately stricter on BOTH axes because the two mistakes are not symmetrical: a missed
# keep costs one more look at the stash, a wrong throw costs an item that does not come back.
# v1792 — A RE-LOOK INSIDE ONE RECORDING COUNTS FOR THE KEEP BAR, AND NEVER FOR THE THROW BAR.
#
# Konyo: "maybe though like it can be smarter then this if in the same session but theres a 3-4 min
# gap between timestamped reels then it can be considered another witness?"
#
# The reasoning holds, and better than it first looks. Two candidate runs inside one reel are already
# separated by a SIGNATURE CHANGE — still_runs only starts a new run when the screen moves past
# STILL_MAX_DIFF — so a second run is not the same frozen screen, it is the panel left and returned
# to. Add a multi-minute gap and it is him walking away and coming back, which is a genuinely
# different look at the shelf: different scroll, different overlay, different mouse.
#
# WHAT IT DOES NOT BUY, which is why it stops at the keep bar. The failure this rule guards against
# is a SYSTEMATIC misread — same model, same prompt, same font, same row. Coming back four minutes
# later and reading "Ral" as "Ort" a second time is exactly as likely as the first time. Elapsed time
# buys independence of STATE, never independence of JUDGEMENT. A separate recording does not buy the
# latter either, strictly speaking, but it is the strongest signal available and law 3 spends it on
# the only irreversible act in the app.
#
# So: a re-look can ground `owned`, and can never on its own justify suggesting he bin something.
# UNMEASURED, and it must stay labelled that way — there is no ownership footage in the archive to
# calibrate it against (REG-185), so this is a reasoned bar exactly like the two below it.
REOPEN_GAP_MS = 180_000                   # 3 minutes — his number, taken as given rather than tuned

KEEP_CONF_FLOOR = _cr.CONF_FLOOR          # 0.55 — one number, shared with the chronicle gate
KEEP_MIN_WITNESSES = 2                    # two DIFFERENT sessions agreeing
THROWOUT_CONF_FLOOR = 0.85                # strictly above KEEP_CONF_FLOOR
THROWOUT_MIN_WITNESSES = 3                # strictly above KEEP_MIN_WITNESSES — and >1 session, always


# ── reel selection ──────────────────────────────────────────────────────────────

def _declared_surface(idx):
    """The ownership surface HE declared for this reel, or None.

    v1603 — only an OWNERSHIP surface counts. `chronicle-uniques` / `chronicle-sets` are real mini
    focuses but they are the chronicle sweep's business, not this one, so they return None here and
    the run falls through to the classifier exactly as before.
    """
    idx = idx if isinstance(idx, dict) else {}
    f = str(idx.get("focus") or "").strip().lower()
    # v1783 — A DEFAULT IS NOT A DECLARATION. Trusting this stamp replaces a paid classify for
    # EVERY run in the reel, so an untouched default ("stash", which the console pre-selects) would
    # label town, a fight and a Chronicle page as a stash panel without one of them being looked at
    # — and any name read off them lands in the stash lane, where merge-max makes it permanent.
    # Reels stamped before v1783 carry no focusChosen key; those keep the old behaviour rather than
    # having their history reinterpreted, and only NEW reels are held to the stricter rule.
    if "focusChosen" in idx and not idx.get("focusChosen"):
        return None
    return f if f in OWNERSHIP_SURFACES else None


def is_mini_reel(idx, reel_dir=""):
    """Was this reel a MINI stash capture (MC-03)? Preferred first — densest evidence per read.

    Several markers are accepted on purpose: the journal field is MC-03's to name, and a sweep that
    silently mis-detects would just quietly read the reels in a worse order. Being wrong here costs
    ordering, never correctness — the laws below do not depend on it.
    """
    idx = idx if isinstance(idx, dict) else {}
    if idx.get("mini") is True:
        return True
    if str(idx.get("mode") or "").lower() in ("mini", "mini_stash", "ministash"):
        return True
    if str(idx.get("kind") or "").lower() in ("mini", "mini_stash"):
        return True
    if str(idx.get("focus") or "").lower() in OWNERSHIP_SURFACES:
        return True
    return "_mini" in os.path.basename(reel_dir or "").lower()


def _load_index(reel_dir):
    try:
        with open(os.path.join(reel_dir, "index.json"), encoding="utf-8") as fh:
            idx = json.load(fh)
        return idx if isinstance(idx, dict) else None
    except Exception:
        return None


def _frame_rows(frames):
    """A reel index's frame list, normalised to the {"f","ts"} rows the grouping expects.

    Real sealed reels always carry dicts, but an older or hand-built index can carry bare filenames,
    and chronicle_retro.still_runs() calls .get() on each row — a bare string raises AttributeError
    and takes the whole sweep down with it. Normalising HERE keeps that shape out of the borrowed
    grouping without touching it: a sweep that dies on one odd reel reads as "the vault is broken".
    """
    out = []
    for fr in (frames or []):
        if isinstance(fr, dict):
            out.append(fr)
        elif isinstance(fr, str) and fr.strip():
            out.append({"f": fr.strip(), "ts": 0})
    return out


def panel_density(reel_dir, panel_gate, sample_every=8, cap=24):
    """FREE: what fraction of sampled frames in this reel actually show an ownership panel.

    `panel_gate(path)` is control_app.stash_screen_open (or its cached twin) — a crop and an OCR,
    no model call, which is why the sweep can afford to ask it about every reel before paying to
    read any of them. Returns 0.0 when the reel is unreadable rather than raising: a reel we cannot
    measure must sort LAST, never first.
    """
    try:
        frames = sorted(glob.glob(os.path.join(reel_dir, "*.jpg")))
    except Exception:
        return 0.0
    probe = frames[::max(1, int(sample_every))][:max(1, int(cap))]
    if not probe:
        return 0.0
    hits = 0
    for f in probe:
        try:
            if panel_gate(f) is not None:
                hits += 1
        except Exception:
            continue
    return hits / float(len(probe))


def order_reels(hist_dirs, panel_gate=None):
    """Reels that actually SHOW a stash first; mini-ness only breaks ties.

    ── v2023 — "MINI-FIRST" WAS SORTING BY THE WRONG THING ─────────────────────────────────────
    Konyo, on being told the first real sweep read nothing: *"but didnt we say it needs to know like
    we have a identifed and classifer for templates when im in the vault/stashing it should know
    that when to grab the reels after that specific moment and until it closes"*. He is right, and
    the ordering was the reason it did not.

    MEASURED, 2026-08-23, the first vault sweep ever run. It took the 4 mini-first reels, examined
    234 frames, and read ZERO pages. Sampling those same four with the panel gate:

        reel_s_1787307553811_9452     25 frames   0 of  7 sampled show a panel
        reel_s_1787307317840_8033    148 frames   0 of 37 sampled show a panel
        reel_s_1787251265965_42930    22 frames   0 of  6 sampled show a panel
        reel_s_1787181101377_20439    39 frames   0 of 10 sampled show a panel
        ──────────────────────────────────────────────────────────────────────
        reel_s_1784984019250_95276   153 frames  23 of 39 sampled show a panel   <- NOT SWEPT

    Zero out of sixty against fifty-nine percent. The reader was never the problem; it was pointed
    at footage of him walking around. `is_mini_reel` asks whether he PRESSED MINI, which is a
    statement of intent and not evidence about the film — and the sweep had no way to prefer, or be
    pointed at, a reel that demonstrably contains what it is looking for.

    THE GATE COSTS NOTHING, WHICH IS THE WHOLE POINT. control_app already says so in its own words
    about the quote path: "The gate costs no model call — a crop and an OCR." So the sweep can price
    every reel by measured panel density before spending a single read on any of them.

    STILL A STABLE SORT. Reels of equal density keep the caller's order, so law 1 holds: this only
    chooses what we PAY to read first, never what the fold concludes. And with no gate supplied the
    behaviour is exactly the old one, so nothing that calls this without a gate changes.
    """
    dirs = [d for d in (hist_dirs or []) if d]
    if panel_gate is None:
        return sorted(dirs, key=lambda d: 0 if is_mini_reel(_load_index(d), d) else 1)
    dens = {}
    for d in dirs:
        dens[d] = panel_density(d, panel_gate)
    # HIGHEST density first; mini-ness only breaks ties; then the caller's order.
    return sorted(dirs, key=lambda d: (-dens.get(d, 0.0),
                                       0 if is_mini_reel(_load_index(d), d) else 1))


# ── normalisation (law 4: honest-absent) ────────────────────────────────────────

def _surface_of(verdict):
    """A classifier's answer → an ownership surface, or None. Accepts a bare string or a dict."""
    if isinstance(verdict, dict):
        verdict = verdict.get("surface") or verdict.get("scene") or verdict.get("kind")
    s = str(verdict or "").strip().lower()
    return s if s in OWNERSHIP_SURFACES else None


def _count_of(v):
    """A count, or None. None is NOT 1 and never becomes 1 (law 4)."""
    if v is None or isinstance(v, bool):
        return None
    try:
        n = int(v)
    except Exception:
        return None
    return n if 0 <= n <= 99999 else None


def _conf_of(v, fallback=0.0):
    try:
        return max(0.0, min(1.0, float(v)))
    except Exception:
        return fallback


def _max_count(a, b):
    """MERGE-MAX on one count (law 1). Unknown loses to any number; unknown+unknown stays unknown.

    Commutative and idempotent by construction — that is what makes the fold order-independent.
    """
    if a is None:
        return b
    if b is None:
        return a
    return a if a >= b else b


def normalize_item(raw, surface, lane_default, page_conf):
    """One reader row → the canonical owned-row seed, or None if it is not an item at all.

    Never invents: no name, no row. Never types what it cannot type: an unknown kind falls back to
    the SURFACE's kind (a rune page holds runes) and only then to the generic 'item'.
    """
    if not isinstance(raw, dict):
        return None
    name = str(raw.get("name") or "").strip()[:80]
    if not name:
        return None
    lane = str(raw.get("lane") or "").strip().lower()
    if lane not in LANES:
        lane = lane_default
    kind = str(raw.get("kind") or "").strip().lower()
    if kind not in KINDS:
        kind = SURFACE_KIND.get(surface, "item")
    return {
        "name": name,
        "lane": lane,
        "kind": kind,
        "count": _count_of(raw.get("count")),
        "conf": _conf_of(raw.get("conf"), page_conf),
        "throwOut": raw.get("throwOut") is True,
        # v2011 — SAY WHEN THIS IS A DEFAULT. The reader was never asked for throwWhy in the JSON
        # shape (fixed in tv_diablo the same version), so this fallback fired on EVERY suggestion
        # and read like the reader's own words. A substituted default must be labelled as one, or
        # it is a sentence with no author. [[unknown-stays-unknown]]
        "throwWhy": (str(raw.get("throwWhy") or "").strip()[:160]
                     or "no reason given by the reader — flagged as junk on the throwOut flag alone"),
    }


# ── THE GATE (laws 2 and 3) ─────────────────────────────────────────────────────

def gate(evidence, conf_floor=KEEP_CONF_FLOOR, min_witnesses=KEEP_MIN_WITNESSES,
         witness_field="witness", witness_noun="look"):
    """Does this pile of sightings ground? Returns a verdict that EXPLAINS itself either way.

    evidence: [{"session","frame","lane","conf",...}, ...]
    -> {"pass", "why", "sessions": [sid...], "witnesses": n, "sightings": n, "bestConf": float}

    WITNESS IDENTITY (law 2): witnesses are DISTINCT SESSION IDS. Two still-runs inside one reel are
    one eye looking at the same stash twice — repetition, not corroboration.

    Law 3 is enforced here and not by the caller: whatever floors are passed in, a single-session
    pile can never satisfy a throw-out bar, because THROWOUT_MIN_WITNESSES is >1 and the witness
    count is a count of sessions. The `why` is what the Vault manager shows him when it declines.
    """
    ev = [e for e in (evidence or []) if isinstance(e, dict)]
    # v1792 — the KEEP bar counts distinct LOOKS (separate recordings, or one recording re-opened
    # after REOPEN_GAP_MS); the THROW bar is called with witness_field="session" so it can only ever
    # count distinct recordings. Falls back to the session id for evidence written before v1792.
    sessions = sorted({str(e.get(witness_field) or e.get("session"))
                       for e in ev if (e.get(witness_field) or e.get("session"))})
    best = max([_conf_of(e.get("conf")) for e in ev] or [0.0])
    base = {"sessions": sessions, "witnesses": len(sessions), "sightings": len(ev), "bestConf": best}
    if not ev:
        return dict(base, **{"pass": False, "why": "no evidence at all"})
    if best < conf_floor:
        return dict(base, **{"pass": False,
                             "why": "the reader itself was unsure (%.2f < %.2f) — unsure twice is "
                                    "still unsure" % (best, conf_floor)})
    if len(sessions) < min_witnesses:
        return dict(base, **{"pass": False,
                             "why": "only %d independent %s%s (%s) — needs %d; two runs of the same "
                                    "unbroken screen are ONE witness"
                                    % (len(sessions), witness_noun,
                                       "" if len(sessions) == 1 else "s",
                                       ", ".join(sessions) or "none", min_witnesses)})
    return dict(base, **{"pass": True,
                         "why": "corroborated across %d %ss (%s) at conf %.2f"
                                % (len(sessions), witness_noun, ", ".join(sessions), best)})


# ── THE FOLD (law 1) ────────────────────────────────────────────────────────────

def _witness_rows(evidence):
    """The provenance the board shows when he asks WHY it thinks he owns this. Sorted = stable."""
    # v1786 — CARRY conf. These rows are not only what the board shows: control_app re-gates a
    # caller-supplied proposal by feeding them straight back into gate(), and gate() reads conf.
    # Without it bestConf was 0.0, so a GENUINE proposal — two sessions at 0.97 and 0.95 — was
    # refused with "the reader itself was unsure (0.00 < 0.55)", blaming the reader for a field the
    # provenance never carried. It was fail-CLOSED only because the console posts an empty body
    # today; the moment anything posted the engine's own proposal back, apply would refuse
    # everything. Found by an adversarial review of this lane.
    rows = [{"session": e.get("session"), "frame": e.get("frame"), "lane": e.get("lane"),
             "conf": e.get("conf")}
            for e in evidence]
    return sorted(rows, key=lambda r: (str(r["session"]), str(r["frame"]), str(r["lane"])))


def _owned_row(key, evidence):
    """Fold one (name, lane) pile into an owned row. MERGE-MAX on count and conf; max on lastSeen.

    Law 1 lives here: `count` is a max() across every sighting, so no session can ever produce a row
    whose count is lower than one already seen, and the result does not depend on the order the
    sightings arrived in.
    """
    name, lane = key
    count = None
    conf = 0.0
    last = None
    kinds = {}
    for e in evidence:
        count = _max_count(count, e.get("count"))
        conf = max(conf, _conf_of(e.get("conf")))
        ts = e.get("ts")
        if isinstance(ts, (int, float)):
            last = ts if last is None else max(last, ts)
        k = e.get("kind") or "item"
        kinds[k] = kinds.get(k, 0) + 1
    # the kind the most sightings agreed on; ties broken by name so the answer is order-independent
    kind = sorted(kinds.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if kinds else "item"
    return {"name": name, "lane": lane, "kind": kind, "count": count, "conf": round(conf, 3),
            "witnesses": _witness_rows(evidence), "lastSeenTs": last}


def merge_vault(existing, incoming):
    """MERGE-MAX ACROSS SESSIONS (law 1) — fold a new proposal into the accumulated picture.

    Both sides may be a proposal dict, a list of owned rows, or a {key: row} map; the result is the
    same either way and merge_vault(a, b) agrees with merge_vault(b, a) on every count.

    A row the incoming read saw FEWER of does not subtract and does not disappear — the shortfall is
    reported in `held` with a why, because an obstructed or half-scrolled stash frame is a normal
    event and not evidence he threw something away. A row missing from the incoming read entirely is
    simply absent evidence, and absence is never a claim.

    -> {"owned": [...], "added": [...], "raised": [...], "held": [...], "byKey": {"lane|name": row}}
    """
    have = {}
    for row in _rows_of(existing):
        _absorb(have, row)
    added, raised, held = [], [], []
    for row in _rows_of(incoming):
        key = (row["name"], row["lane"])
        prev = have.get(key)
        if prev is None:
            _absorb(have, row)
            added.append(row["name"])
            continue
        pc, nc = prev.get("count"), row.get("count")
        if pc is not None and nc is not None and nc < pc:
            # LAW 1. Never lower a count. Say so instead.
            held.append({"name": row["name"],
                         "why": "this read saw %d in %s but %d was already recorded — kept the "
                                "higher count; a half-scrolled or obstructed panel is normal and is "
                                "not evidence anything was thrown away" % (nc, row["lane"], pc)})
        elif nc is not None and (pc is None or nc > pc):
            raised.append(row["name"])
        _absorb(have, row)
    owned = sorted(have.values(), key=lambda r: (r["lane"], r["name"].lower(), r["name"]))
    return {
        "owned": owned,
        "added": sorted(set(added)),
        "raised": sorted(set(raised)),
        "held": held,
        "byKey": {"%s|%s" % (r["lane"], r["name"]): r for r in owned},
    }


def _absorb(have, row):
    """Merge one row into the accumulator under MERGE-MAX. Idempotent: absorbing twice is a no-op."""
    key = (row["name"], row["lane"])
    cur = have.get(key)
    if cur is None:
        have[key] = dict(row)
        return
    cur["count"] = _max_count(cur.get("count"), row.get("count"))
    cur["conf"] = round(max(_conf_of(cur.get("conf")), _conf_of(row.get("conf"))), 3)
    a, b = cur.get("lastSeenTs"), row.get("lastSeenTs")
    cur["lastSeenTs"] = a if b is None else (b if a is None else max(a, b))
    seen = {(w.get("session"), w.get("frame"), w.get("lane")) for w in (cur.get("witnesses") or [])}
    for w in (row.get("witnesses") or []):
        if (w.get("session"), w.get("frame"), w.get("lane")) not in seen:
            cur.setdefault("witnesses", []).append(w)
            seen.add((w.get("session"), w.get("frame"), w.get("lane")))
    cur["witnesses"] = sorted(cur.get("witnesses") or [],
                              key=lambda r: (str(r.get("session")), str(r.get("frame")),
                                             str(r.get("lane"))))
    if cur.get("kind") in (None, "item"):
        cur["kind"] = row.get("kind") or cur.get("kind") or "item"


def _rows_of(blob):
    """Accept a proposal, a list of rows, or a {key: row} map. Anything else contributes nothing."""
    if not blob:
        return []
    if isinstance(blob, dict):
        rows = blob.get("owned") if "owned" in blob else list(blob.values())
    else:
        rows = list(blob)
    out = []
    for r in rows or []:
        if not isinstance(r, dict):
            continue
        name = str(r.get("name") or "").strip()
        lane = str(r.get("lane") or "").strip().lower()
        if not name or lane not in LANES:
            continue
        out.append({"name": name, "lane": lane, "kind": r.get("kind") or "item",
                    "count": _count_of(r.get("count")), "conf": _conf_of(r.get("conf")),
                    "witnesses": [w for w in (r.get("witnesses") or []) if isinstance(w, dict)],
                    "lastSeenTs": r.get("lastSeenTs")})
    return out


# ── THE SWEEP ───────────────────────────────────────────────────────────────────

def _empty(why, sessions_seen=0):
    """A refusal, fully shaped. ok:False with a why — never a fabricated empty success (law 4)."""
    return {"ok": False, "generatedTs": int(time.time() * 1000), "why": why, "sessionsRead": [],
            "owned": [], "throwOut": [], "unsure": [], "held": [],
            "totals": {"sessionsSeen": sessions_seen, "framesSeen": 0, "classified": 0,
                       "pagesRead": 0, "skipped": 0}}


_RESOLVER_WARNED = [False]


_GRAIL_WARNED = [False]


def _grail_guard():
    """A predicate: is this name a GRAIL ITEM — a named unique or set piece he is hunting?

    v1903 — THE BACKSTOP THE THROW LANE NEVER HAD. Whether an item is junk is decided entirely by
    the reader's `throwOut` flag: a vision model's opinion, arriving through a prompt (see
    tv_diablo.VAULT_READ_PROMPT) with real consequences. Law 3 of this file is that there is no
    un-throw in Diablo, and the whole gate above is built on that — a strictly higher confidence
    floor, three separate recordings, never automatic. All of it guards HOW MUCH evidence a throw
    needs, and none of it guards WHAT MAY BE THROWN.

    So one thing is settled in code rather than left to the reader's judgement: a name on his grail
    roster is never a throw-out suggestion, at any confidence, from any number of recordings. That
    is not a matter of degree — a unique or set piece is the thing this entire project exists to
    collect, and a suggestion to bin one is wrong even when the reader is certain.

    ⚠ AN UNLOADABLE ROSTER TURNS THE BACKSTOP OFF, so it says so once rather than returning a quiet
    False. A guard that cannot answer must not answer "no". [[feedback-silence-is-not-evidence]]
    """
    try:
        import chronicle_resolve as _res
        roster = _res.load_roster()
        set_roster = _res.load_set_roster()
    except Exception as e:
        if not _GRAIL_WARNED[0]:
            _GRAIL_WARNED[0] = True
            print("   \u26a0 grail backstop unavailable (%s) \u2014 a throw-out suggestion can no "
                  "longer be checked against his roster" % e)
        return None

    def is_grail(name):
        try:
            k = _res._norm(name)
        except Exception:
            return False
        return bool(k) and any(r and k in r for r in (roster, set_roster))

    return is_grail


def _name_folder(resolve=None):
    """A function that CORRECTS a reader's item name onto his roster, or leaves it alone.

    v1885 — THE VAULT LANE HAD NO FOLD AT ALL, and the chronicle lane has had one for versions.
    Measured on the exact corrections his chronicle sweep made on 2026-08-20 — 53 of them in one
    reel — pushed at the vault instead:

        pushed  Atma's Scarab · Battlecage · Saracen's Chance
        owned   Atma's Scarab · Battlecage · Saracen's Chance      (verbatim)
        both spellings together -> SIX owned rows for THREE real items

    And merge-max never subtracts, so each of those is PERMANENT. A systematic misread is exactly
    the kind that repeats across sessions — this file's own law-3 note says so: "Coming back four
    minutes later and reading 'Ral' as 'Ort' a second time is exactly as likely as the first time"
    — so the two-witness keep bar does not save it. Two sessions of one misread is a ghost item in
    his vault, forever.

    ⚠ THE ONE THING THIS MUST NOT DO IS RETIRE WHAT IT CANNOT FOLD. The chronicle fold may call an
    unfoldable name debris, because a Chronicle page holds nothing but grail items. A STASH holds
    runes, gems, materials, bases, charms and jewels — `canonical("Ral Rune")` is None and that is
    a real thing he owns. So: correct what folds, leave everything else EXACTLY as read.
    [[d2r-multiwitness-corroboration]] [[feedback-generalize-fixes]]
    """
    if resolve is not None:
        return resolve
    try:
        import chronicle_resolve as _res
        roster = _res.load_roster()
        set_roster = _res.load_set_roster()
    except Exception as e:
        if not _RESOLVER_WARNED[0]:
            _RESOLVER_WARNED[0] = True
            print("   \u26a0 vault name-fold unavailable (%s) \u2014 gating on RAW reader names, so a "
                  "misread can become a permanent row" % e)
        return lambda n: n

    # ⚠ EXACT FOLDS ONLY IN THE VAULT LANE — NO NEAR MATCHES. This is not caution, it is a defect
    # my own test caught within a minute of writing the fold: canonical() near-matched
    # "Isenhart's Armory (set)" — a SET AGGREGATE — onto "Isenhart's Parry (shield)", a specific
    # piece. That is not a correction, it is a find he never made, and it is exactly what the
    # resolver's own comment warns about ("guessing here writes a find he never made").
    #
    # WHY THE CHRONICLE LANE CAN AFFORD NEAR MATCHES AND THIS ONE CANNOT: a Chronicle page is a
    # CLOSED list of grail names, so every row IS a roster item and the nearest one is very likely
    # right. A STASH IS AN OPEN UNIVERSE — runes, gems, materials, bases, charms, jewels, set
    # aggregates, quest items — so "nearest roster entry" is a guess about which of two different
    # things he owns.
    #
    # WHAT THIS FIXES, measured: the apostrophe class, which is the common one and the one his own
    # sweep hit — "Atma's Scarab" and "Saracen's Chance" both normalise onto their curly-quoted
    # roster names EXACTLY (_norm folds ’ to ' and strips non-letters).
    # WHAT IT DELIBERATELY DOES NOT FIX: "Battlecage" -> "Rattlecage". That needs a near match, and
    # an uncorrected row he can SEE is better than a confident wrong attribution he cannot.
    def fold(name):
        try:
            k = _res._norm(name)
        except Exception:
            return name
        if not k:
            return name
        for r in (roster, set_roster):
            if r and k in r:
                return r[k]
        return name           # a rune, a gem, a base, a charm — not debris, just not a grail name

    return fold


def sweep(hist_dirs, sig=None, reader=None, classify=None, limit=None, resolve=None,
          panel_gate=None):
    """THE VAULT RETRO SWEEP: sealed reels in, a PROPOSAL of what he owns out. Writes nothing.

    hist_dirs: sealed reel directories, newest-first (mini/stash reels are re-ordered to the front).
    sig(frame_path)      -> fingerprint or None. Production value: DEFAULT_SIG (chronicle_retro.jpeg_sig).
    classify(frame_path) -> an ownership surface name, a dict carrying one, or None. ONE call per
                            candidate still-run, on the run's most settled frame.
    reader(frame_path, surface) -> {"items": [{name, kind, count, conf, lane, throwOut, throwWhy}],
                            "conf": float, "note": str|None}. Only ownership runs are ever read.
    limit: read at most N reels (after the mini-first re-ordering) — the cost dial, not a filter on
           what counts as evidence.

    PAY FOR RUNS, NOT FRAMES — inherited wholesale from the chronicle sweep: ~150 frames become a
    handful of still-runs, one classify each, and only ownership runs cost a read.
    """
    if sig is None or reader is None or classify is None:
        # Law 4. "I was not given eyes" is a fact; dressing it as an empty stash would read exactly
        # like "you own nothing", which is the one wrong answer that looks like a right one.
        missing = ", ".join(n for n, v in (("sig", sig), ("reader", reader), ("classify", classify))
                            if v is None)
        return _empty("cannot sweep: no %s was supplied — this is not an empty vault, it is a sweep "
                      "that never ran" % missing, len(hist_dirs or []))

    # v2023 — order by MEASURED panel density when a gate is supplied, so `limit` spends the
    # budget on reels that demonstrably show a stash instead of on the four most recent ones.
    dirs = order_reels(hist_dirs, panel_gate=panel_gate)
    if limit:
        dirs = dirs[:limit]
    evidence = {}          # (name, lane) -> [sighting...]
    throw_flags = {}       # (name, lane) -> [sighting...] the reader flagged as junk
    unsure, held = [], []
    sessions_read, sessions_seen = [], 0
    # v2020 — `classified` counts CALLS MADE. `answered` counts calls that came back with a
    # surface. They are the same number only when the classifier works, and the whole of
    # REG-382 is the case where they are not. See _verdict().
    # v2028 — `rescued` counts runs admitted only because a NEIGHBOUR frame resolved the tab
    # the probe's tooltip was covering. It is reported, not pocketed: if it ever reads 0 on
    # footage with tooltips, this fix has stopped working.
    frames_seen = classified = pages_read = skipped = answered = rescued = 0
    trusted = 0   # runs whose surface came from HIS declared focus rather than a paid read

    _fold = _name_folder(resolve)
    folded_names = {}
    for reel_dir in dirs:
        sessions_seen += 1
        idx = _load_index(reel_dir)
        if idx is None:
            held.append({"name": None, "why": "reel %s has no readable index.json — held, not guessed"
                                              % os.path.basename(reel_dir)})
            continue
        sid = str(idx.get("sessionId") or os.path.basename(reel_dir))
        # the focus HE declared when he pressed MINI — trusted below in place of a classify call,
        # but only when it names an ownership surface this sweep actually owns.
        declared = _declared_surface(idx)
        frames = _frame_rows(idx.get("frames"))
        frames_seen += len(frames)
        # BORROWED grouping — chronicle_retro owns STILL_MAX_DIFF / MIN_RUN_FRAMES and the run logic.
        sig_of = lambda n, _d=reel_dir: sig(os.path.join(_d, n))          # noqa: E731 — per-reel bind
        runs = _cr.still_runs(frames, sig_of)
        cands = _cr.candidate_runs(runs, min_frames=MIN_RUN_FRAMES)
        read_this_reel = False
        # v1792 — RE-LOOK BUCKETS. Candidate runs are already separated by a signature change, so a
        # multi-minute gap between two of them is the panel left and returned to rather than one
        # frozen screen. Each gap opens a new bucket, and the bucket is what the KEEP bar counts.
        # Compared against the PREVIOUS RUN'S END, not the reel's start, so three looks spread over
        # an hour are three buckets and three quick glances in one minute are still one.
        _wbucket = 0
        _prev_end = None
        for run in cands:
            _st = run.get("start_ts") or 0
            if _prev_end is not None and _st and (_st - _prev_end) >= REOPEN_GAP_MS:
                _wbucket += 1
            _prev_end = run.get("end_ts") or _st or _prev_end
            _wkey = "%s#%d" % (sid, _wbucket)
            names = run.get("frames") or []
            probe, _dead = _cr.live_probe(names, lambda n, _d=reel_dir: os.path.join(_d, n))
            if probe is None:
                skipped += 1
                held.append({"name": None,
                             "why": "a %d-frame run in %s was BLANK all the way through — the window "
                                    "was grabbed with nothing on it; that is a capture fault, not an "
                                    "empty stash" % (len(names), sid)})
                continue
            # ── v1603 — A DECLARED FOCUS IS NOT A GUESS. ─────────────────────────────────
            # When he presses MINI he TELLS the app what he is parked on, and that stamp lands in
            # the reel's index.json. Until now the sweep used it only to read mini reels first;
            # every run still paid a classify call to rediscover a fact already on disk, and could
            # still get it wrong — a rune tab misread as "inventory" files his runes in the wrong
            # lane, which merge-max then makes permanent.
            #
            # This is the same trade chronicle_retro.sweep_frames() already makes for the live
            # lane: "a recorded visit already knows two things a blind sweep has to pay a model to
            # discover". Cheaper AND more accurate, which is rare enough to be worth saying out
            # loud — the model call it removes was the one that could be wrong.
            #
            # TRUSTED NARROWLY, on purpose: only when the reel declares a focus that IS an
            # ownership surface. A chronicle-focused mini is NOT an ownership surface, so it falls
            # through to the classifier here and is read by the chronicle sweep instead.
            if declared:
                surface = declared
                trusted += 1
            else:
                classified += 1
                surface = _surface_of(classify(os.path.join(reel_dir, probe)))
                if surface is not None:
                    answered += 1
                else:
                    # ── v2028 — ONE OCCLUDED FRAME MUST NOT CONDEMN THE RUN ──────────────────
                    # THE ROOT CAUSE OF THE WHOLE "no name to be had" STORY, and it is the exact
                    # inverse of what anyone would guess.
                    #
                    # stash_screen_open identifies a stash panel by OCR-ing the TAB CHROME
                    # (PERSONAL / SHARED / GEMS / MATERIALS / RUNES). A D2R hover tooltip is drawn
                    # ON TOP of that row. So the gate rejects, with perfect consistency, exactly
                    # the frames that contain a readable item NAME — and keeps the ones showing a
                    # bare grid, which prints no names at all.
                    #
                    # LOOKED AT, not inferred. Two frames the gate refused:
                    #   f_1784984195842.jpg  "Sullied Grand Charm of Blight / Required Level: 42 /
                    #                         +1 to Eldritch Skills (Warlock Only)" — its
                    #                        "Ctrl + Left Click to Move to Inventory" line sits
                    #                        straight across the tab row.
                    #   f_1787508818939.jpg  "Marshal's Amulet / +3 to Offensive Auras" — same,
                    #                        "Shift + Left Click to Equip" over GEMS/MATERIALS.
                    #
                    # MEASURED across his four stash reels: 16 of 170 in-panel frames (9%, and 10%
                    # on each of the two best reels) are refused while BRACKETED by frames the gate
                    # resolves — i.e. the panel is provably still open. Every one of those is a
                    # frame he was hovering on.
                    #
                    # A still-run is ONE HELD SCREEN by construction. So a single frame's occluded
                    # tab row cannot be evidence about the run; any frame that resolves settles it.
                    # This is FREE — classify here is a crop and an OCR, no model call — and it is
                    # bounded at 3 extra looks so a genuinely non-stash run stays cheap.
                    #
                    # It rescues the RIGHT frames too: the reader below walks _distinct(names), so
                    # once the run is admitted the tooltip frames are read like any other.
                    # [[the-unjoined-end]] [[feedback-suspect-the-instrument]]
                    # ⚠ THE RESCUE MUST BE FREE. The first cut of this retried `classify`, and
                    # `classify` on the console is the FREE gate followed by a PAID model call
                    # (control_app._classify: `if stash_screen_open(p) is None: return None` then
                    # `_tv.claude_read(p)`). Three retries per rejected run would have tripled the
                    # classify spend on exactly the runs that are NOT stash panels — a cost
                    # regression wearing a fix's clothes.
                    #
                    # panel_gate is the free half on its own (a crop and an OCR), and v2023 already
                    # threads it in for the ordering. So: ask the FREE gate whether any neighbour
                    # sees the panel, and only then pay ONE classify, on that frame.
                    _alts = [n for n in names if n != probe]
                    if _alts and panel_gate is not None:
                        _step = max(1, len(_alts) // 4)
                        for _alt in _alts[::_step][:4]:
                            try:
                                _seen = panel_gate(os.path.join(reel_dir, _alt)) is not None
                            except Exception:
                                _seen = False
                            if not _seen:
                                continue
                            classified += 1
                            surface = _surface_of(classify(os.path.join(reel_dir, _alt)))
                            if surface is not None:
                                answered += 1
                                rescued += 1
                            break        # one paid look is the whole budget for a rescue
            if surface is None:
                # Law 4: unclassifiable is HELD, never guessed into a lane.
                skipped += 1
                held.append({"name": None,
                             "why": "a still run in %s (frame %s) could not be classified — held "
                                    "rather than guessed onto a shelf" % (sid, probe)})
                continue
            if surface not in OWNERSHIP_SURFACES:   # unreachable via _surface_of; kept as the law
                skipped += 1
                continue
            lane_default = SURFACE_LANE.get(surface, "stash")
            # A held-still panel is ONE page; a SCROLLED panel is several. _distinct is the chronicle's
            # calibrated "same pixels?" test — borrowed so the two sweeps pay alike.
            for name in _cr._distinct(names, sig_of):
                path = os.path.join(reel_dir, name)
                resp = reader(path, surface)
                if not isinstance(resp, dict) or resp.get("note"):
                    skipped += 1
                    held.append({"name": None,
                                 "why": "the reader refused %s in %s (%s)"
                                        % (name, sid, (resp or {}).get("note") if isinstance(resp, dict)
                                           else "no answer")})
                    continue
                pages_read += 1
                read_this_reel = True
                page_conf = _conf_of(resp.get("conf"))
                ts = resp.get("ts") if isinstance(resp.get("ts"), (int, float)) else run.get("end_ts")
                for raw in (resp.get("items") or []):
                    item = normalize_item(raw, surface, lane_default, page_conf)
                    if item is not None:
                        # v1885 — fold BEFORE the key is formed, or two spellings of one item are
                        # two piles of evidence and neither may reach two witnesses
                        _canon = _fold(item["name"])
                        if _canon and _canon != item["name"]:
                            folded_names[item["name"]] = _canon
                            item["name"] = _canon
                    if item is None:
                        unsure.append({"name": None,
                                       "why": "the reader returned a row with no name on %s in %s — "
                                              "nothing was invented for it" % (name, sid)})
                        continue
                    sight = {"session": sid, "witness": _wkey, "frame": name, "lane": item["lane"],
                             "conf": item["conf"], "count": item["count"], "kind": item["kind"],
                             "ts": ts}
                    key = (item["name"], item["lane"])
                    evidence.setdefault(key, []).append(sight)
                    if item["throwOut"]:
                        throw_flags.setdefault(key, []).append(dict(sight, why=item["throwWhy"]))
        if read_this_reel:
            sessions_read.append(sid)

    if folded_names:
        _eg = ", ".join("%s -> %s" % kv for kv in sorted(folded_names.items())[:3])
        print("   \U0001f9f9 %d reader name(s) folded onto the roster (%s)"
              % (len(folded_names), _eg))
    owned, throw_out = [], []
    for key in sorted(evidence, key=lambda k: (k[1], k[0].lower(), k[0])):
        ev = evidence[key]
        v = gate(ev, KEEP_CONF_FLOOR, KEEP_MIN_WITNESSES)
        if not v["pass"]:
            # Law 2: one witness is never `owned`. It is remembered as unsure so a later session can
            # corroborate it — the accumulator's whole point.
            unsure.append({"name": key[0], "why": "%s in %s — %s" % (key[0], key[1], v["why"])})
            continue
        owned.append(_owned_row(key, ev))
    _is_grail = _grail_guard()
    for key in sorted(throw_flags, key=lambda k: (k[1], k[0].lower(), k[0])):
        ev = throw_flags[key]
        # v1903 — A GRAIL NAME IS NEVER A THROW-OUT, at any confidence, from any number of
        # recordings. Every other guard on this lane is about HOW MUCH evidence a throw needs;
        # none of them was about WHAT MAY BE THROWN, and "is this junk" was the reader's opinion
        # alone. A unique or set piece is the thing this whole project exists to collect.
        if _is_grail is not None and _is_grail(key[0]):
            held.append({"name": key[0],
                         "why": "throw-out SUGGESTION refused for %s in %s \u2014 it is on his GRAIL "
                                "ROSTER. Evidence is not the question here: a named unique or set "
                                "piece is never junk, however sure the reader was"
                                % (key[0], key[1])})
            continue
        # Law 3: the STRICTER bar, on both axes. Single-session evidence can never clear it.
        # law 3 — the throw bar counts RECORDINGS, never re-looks. A single reel, however many times
        # he re-opened the panel in it, can never suggest binning an item.
        v = gate(ev, THROWOUT_CONF_FLOOR, THROWOUT_MIN_WITNESSES,
                 witness_field="session", witness_noun="recording")
        if not v["pass"]:
            held.append({"name": key[0],
                         "why": "throw-out SUGGESTION withheld for %s in %s — %s. There is no "
                                "un-throw in Diablo, so this bar is higher than the keep bar on "
                                "purpose" % (key[0], key[1], v["why"])})
            continue
        whys = sorted({str(e.get("why") or "").strip() for e in ev if e.get("why")})
        throw_out.append({"name": key[0], "lane": key[1],
                          "why": "; ".join(whys) or "the reader flagged it as junk",
                          "conf": round(v["bestConf"], 3), "witnesses": _witness_rows(ev),
                          "suggestion": True})   # never automatic — the Vault manager ASKS him

    totals = {"sessionsSeen": sessions_seen, "framesSeen": frames_seen, "classified": classified,
              "pagesRead": pages_read, "skipped": skipped,
              # v2020 — how many of those classify calls came back with an actual surface.
              "classifierAnswered": answered,
              # v2028 — runs saved from a tooltip-occluded probe frame.
              "occludedRescued": rescued,
              # v1603 — classify calls SKIPPED because he had already said what he was looking at.
              # Reported rather than silently pocketed: "9 classifies" and "9 classifies + 4 you
              # told us" are different facts about the same sweep.
              "trustedFocus": trusted}
    return {"ok": True, "generatedTs": int(time.time() * 1000), "why": _verdict(totals, owned, unsure),
            "sessionsRead": sorted(set(sessions_read)),
            "owned": owned, "throwOut": throw_out, "unsure": unsure, "held": held, "totals": totals}


def _verdict(totals, owned, unsure):
    """WHY an empty sweep is empty. Four different nothings, exactly as the chronicle sweep does it —
    collapsing them would send him debugging a reader when what he needs is to open his stash."""
    if owned:
        return ("%d item(s) grounded across %d session(s) from %d page(s) — %d more need a second "
                "session to corroborate." % (len(owned), totals["sessionsSeen"], totals["pagesRead"],
                                             len(unsure)))
    if not totals["sessionsSeen"]:
        return "There is no sealed footage to sweep yet — record a mini stash session first."
    # v1783 — THIS BRANCH ACCUSED HIS CAMERA FOR THE READER'S FAILURE. classified counts PAID
    # classifier calls, and the v1603 trusted-focus path never increments it: when he presses MINI
    # the focus is taken as a declaration and the classifier is skipped entirely. So for any mini
    # reel with a declared focus this is STRUCTURALLY 0, and the sweep answered "footage of moving,
    # not of looking at a stash" for a reel it had read pages from — sending him to steady the
    # camera when the reader is the thing to look at. Found by an adversarial review of this lane.
    if not totals["classified"] and not totals.get("trustedFocus"):
        return ("%d reel(s) held no screen still long enough to be worth reading — that is footage of "
                "moving, not of looking at a stash." % totals["sessionsSeen"])
    if not totals["classified"] and totals.get("trustedFocus") and not totals["pagesRead"]:
        return ("%d reel(s) carried a declared focus so no screen was classified, and no page was "
                "read from them — the reader, not the footage, is what to check."
                % totals["sessionsSeen"])
    if not totals["pagesRead"]:
        # ── v2020 (REG-382) — "NOBODY LOOKED" WAS BEING PRINTED AS "WE LOOKED AND FOUND NOTHING" ──
        # This branch used to fire on `pagesRead == 0` alone and announce that NONE of his stills was
        # a stash panel, and that this "is not a reader failure". Both halves were false whenever the
        # classifier never answered — and the FREE --cost pass installs `classify=lambda p: None`,
        # a classifier that refuses everything BY DESIGN, so the free pass was structurally
        # guaranteed to print it.
        #
        # MEASURED, 2026-08-23: `vault_retro.py --cost` reported "84 still screen(s) ... NONE was a
        # stash, inventory or equipment panel" over the same corpus in which vault_doctor finds 16
        # stash panels in 238 sampled frames, and in which frame f_1784984209709 carries a COMPLETE
        # Annihilus tooltip that a paid chronicle sweep had already read. Three witnesses against it.
        #
        # This is the most expensive possible wrong answer: the cost pass is what you run BEFORE
        # deciding to pay, and it told him his footage held nothing and the reader was blameless.
        # A sweep that has never run is why vault_swept.json has never existed.
        # [[unknown-stays-unknown]] [[feedback-contradiction-is-the-finding]]
        if not totals.get("classifierAnswered"):
            # v2024 — DO NOT NAME A CAUSE THIS FUNCTION CANNOT SEE. The first cut asserted the
            # --cost stub, which is only ONE way to reach this state; the first REAL sweep hit it
            # too, from a live classifier that refused every still. Naming the wrong cause sends
            # him to check the wrong thing, which is the same failure as the verdict this replaced.
            return ("%d still screen(s) were examined and the classifier answered about NONE of "
                    "them, so whether any is a stash panel is UNKNOWN — this says nothing about "
                    "the footage. Two things reach this state: the free --cost pass, which installs "
                    "a classifier that refuses everything by design, or a real sweep whose "
                    "classifier refused every still. Check which before concluding anything."
                    % totals["classified"])
        return ("%d still screen(s) were examined across %d reel(s), the classifier answered about "
                "%d of them, and NONE was a stash, inventory or equipment panel — there was nothing "
                "to read. This is not a reader failure."
                % (totals["classified"], totals["sessionsSeen"], totals["classifierAnswered"]))
    if unsure:
        return ("%d page(s) were read and every name so far has only ONE session behind it — open the "
                "same stash on camera once more and they ground." % totals["pagesRead"])
    return ("%d page(s) were read and produced no items. This one is the reading itself, not the "
            "footage." % totals["pagesRead"])


# ── APPLY (law 5: shapes, never writes) ─────────────────────────────────────────

def apply_payload(proposal):
    """Shape a proposal for the ONE existing apply path. It does not write and cannot write.

    The caller hands this to window.chronicleApply — the same function his hand-tick uses — so the
    write inherits the date stamp, the merge-max and the undo bar. A second write path is a second
    thing that drifts, and this module deliberately does not have one.

    THROW-OUTS ARE NOT IN `items`. They ride along as `suggestions`, flagged as suggestions, because
    nothing this module produces may bin anything on its own.
    

    ⚠ v1986 — WITNESSES SHIP AS ROWS, NOT AS A COUNT. This used to emit
    `"witnesses": len(...)`, turning the list _witness_rows builds into an int. Every reader on
    the board treats it as an ARRAY — `witnesses[0].session`, `witnesses.length` — so the
    production payload never looked like what the board expects, and a JS `for (i < w.length)`
    over a number simply never ran. That silently disabled REG-339's 3-session equipment lock
    on the only path that actually runs: it locked fine against hand-made arrays in tests and
    could not fire on a real apply. Measured: owned row `witnesses` is list len 3, the shaped
    item was int 3.

    The count survives as `witnessCount` for any surface that wants a number. Losing the rows
    also cost provenance — reel and frame live on those dicts and nowhere else in `items`."""
    p = proposal if isinstance(proposal, dict) else {}
    if not p.get("ok"):
        return {"ok": False, "source": "vault-retro", "mode": "merge-max", "items": [],
                "suggestions": [], "why": p.get("why") or "no proposal to apply",
                "generatedTs": p.get("generatedTs")}
    items = [{"name": r["name"], "lane": r["lane"], "kind": r.get("kind") or "item",
              "count": r.get("count"), "conf": r.get("conf"),
              "witnesses": [w for w in (r.get("witnesses") or []) if isinstance(w, dict)],
              "witnessCount": len(r.get("witnesses") or []),
              "lastSeenTs": r.get("lastSeenTs")}
             for r in (p.get("owned") or [])]
    return {
        "ok": True,
        "source": "vault-retro",
        "mode": "merge-max",            # the receiving apply must raise counts, never lower them
        "readOnlyUntilApply": True,     # nothing has been written; this is a proposal he presses
        "generatedTs": p.get("generatedTs"),
        "sessionsRead": p.get("sessionsRead") or [],
        "items": items,
        "suggestions": [dict(t, automatic=False) for t in (p.get("throwOut") or [])],
        "unsure": p.get("unsure") or [],
        "held": p.get("held") or [],
        "totals": p.get("totals") or {},
        # v1996 — CARRY THE FREE EVIDENCE THROUGH. The sweep computes two things from the PIXELS,
        # at no cost, on frames the paid reader had to give up on:
        #   glimpsed    cells that are visibly occupied on a panel whose read named nothing (v1989)
        #   reconciled  the per-frame comparison of names against occupied cells, and `overRead`,
        #               the subset where the model named MORE than the panel can physically hold —
        #               the only fabrication signal this lane has (v1994)
        # Both were written onto the proposal and DROPPED HERE, so the board could not have rendered
        # them however much it wanted to. Konyo asked for exactly this: "i want it to visually render
        # the backend through the ledger visually so we can visually surgically fix anything needed."
        # A signal computed and never carried is the same defect as one computed and never read.
        # [[the-unjoined-end]]
        "glimpsed": p.get("glimpsed") or [],
        "reconciled": p.get("reconciled") or [],
        "overRead": p.get("overRead") or [],
        # v2004 — the ROOM (which squares never move, which are open floor) and the reason the pixel
        # lane went quiet if it did. Both were computed and then dropped here, which is the same
        # defect v1996 fixed for glimpsed/reconciled — committed again eight versions later, by me.
        "room": p.get("room") or None,
        "pixelLaneError": p.get("pixelLaneError") or "",
        # v2006 — how much footage has given up its information, and how close the disk is to the
        # floor below which ON AIR refuses to record. A report, never an instruction to delete.
        "retention": p.get("retention") or None,
        "why": p.get("why") or "",
    }


# ── CLI ─────────────────────────────────────────────────────────────────────────
# Print-only, like the chronicle sweep's. This module may never write, and a CLI that dropped a
# proposal file would break the law the whole arc rests on.
if __name__ == "__main__":
    import console_safe  # noqa: F401  — emoji must survive a non-UTF-8 console
    import argparse

    ap = argparse.ArgumentParser(description="Vault accumulator: what the sealed reels say he owns.")
    ap.add_argument("--hist", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "frames", "hist"))
    ap.add_argument("--limit", type=int, default=None, help="only the N best reels")
    ap.add_argument("--cost", action="store_true",
                    help="FREE: group frames into runs and report what a real sweep WOULD cost")
    args = ap.parse_args()

    dirs = _cr.reel_dirs(args.hist)
    if args.cost:
        # the free pass: real grouping, a classifier that refuses everything, a reader that is never
        # reached. Nothing is read, nothing is charged, and the run/classify arithmetic is his own.
        res = sweep(dirs, sig=DEFAULT_SIG, classify=lambda p: None,
                    reader=lambda p, s: {"note": "cost-pass"}, limit=args.limit)
        t = res["totals"]
        print("🗄  %d reel(s) · %d frames → %d classifies · %d pages read"
              % (t["sessionsSeen"], t["framesSeen"], t["classified"], t["pagesRead"]))
        print("   mini-first order: %s" % ", ".join(os.path.basename(d) for d in order_reels(dirs)[:8]))
        print("   %s" % res["why"])
        raise SystemExit(0)

    print("This sweep needs a reader and a classifier. Use --cost for the free grouping pass, or")
    print("drive sweep() from the console, which owns the reader lanes and the apply step.")
