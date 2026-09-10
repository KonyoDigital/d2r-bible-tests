#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🎞🚚 THE SHELF DRIVER — it RUNS what retention decides, and decides nothing itself.

Konyo, 2026-09-10, choosing this over a manager AI for THE SHELF: *"1. A driver — something that
executes what reel_retention.plan() already decides. No opinions, no second predicate... 2. Heart
2.0 supervision over the driver — so a lane that stops reading goes RED on its own"*.

⚠⚠ WHY THERE IS NO SECOND PREDICATE HERE, AND WHY THAT IS THE WHOLE DESIGN.
Every serious defect found on 2026-09-10 was TWO AUTHORITIES ANSWERING ONE QUESTION:

    _chron_owed_count()   41   vs   vaultAutoread.owed        0
    _vault_lane_owes      40   vs   _vault_owed_reels         0
    plan()                 2   vs   the watchdog's predicate 19   (2026-08-28: 17 needless paid sweeps)
    `--prove` "fix the skip"   vs   propose() "the law is weak"

`control_app._vault_owed_reels` already carries the ruling in its own docstring: *"ONE DEFINITION.
The reason string is retention's, so a reel leaves this list the moment retention stops calling it
vault-blocked, and the panel and the sweeper cannot drift apart."* A manager with judgement would be
a THIRD opinion about "is this reel done" — the exact failure mode, added on purpose.

So this module asks `reel_retention.plan()` and nothing else. It carries retention's own `tag` and
`why` through untouched. If it ever starts deciding, it has become the defect it was built to avoid.
[[the-unjoined-end]] [[copy-drift]] [[feedback-contradiction-is-the-finding]]

⚠ IT NEVER DELETES. `_PRUNE_SAFE_TO_RUN` is Konyo's to arm, not this module's. `work()` reports;
`stages()` draws; neither removes a frame.
"""
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

def _beat_path():
    """Where the driver's own heartbeat lives, resolved at CALL time. -> str|None

    ⚠⚠ IT WAS A MODULE CONSTANT, WHICH MEANT A GATE WROTE INTO HIS LIVE tv/. `BEAT` was
    `os.path.join(HERE, ...)` computed at import, so `TV_HIST` — the one thing a caller sets to say
    "this is not his world" — could never reach it, and `beat()` writes on every call. control_app
    has already paid for this exact shape (`_shadow_watch_path`, v2423: *"an env honoured only at
    import is a redirect that silently does not take"*). [[feedback-fixtures-never-touch-live-data]]

    ⛔ AND A REQUEST FOR ISOLATION THAT CANNOT BE HONOURED REFUSES RATHER THAN DEGRADING. It asks
    `tv_diablo._fixture_root` — the ONE definition of the rule — and never restates it. If that
    resolver is unreachable while TV_HIST is set this returns None and `beat()` records that it
    could not persist, because the alternative is a FOURTH copy of a rule whose existing copies are
    already a live disagreement (REG-875). [[copy-drift]] [[unknown-stays-unknown]]
    """
    try:
        import tv_diablo as _tvd
        return os.path.join(_tvd._fixture_root(HERE), ".shelf_driver.json")
    except Exception:
        if os.environ.get("TV_HIST"):
            return None
        return os.path.join(HERE, ".shelf_driver.json")


#: Back-compat for readers of the module attribute. The CALLABLE above is the source of truth;
#: this is the same answer on his console, where TV_HIST is unset.
BEAT = os.path.join(HERE, ".shelf_driver.json")

#: Which retention tag means "a lane still owes this reel work", and which lane owes it.
#: ⚠ KEYED ON THE TAG, NOT THE SENTENCE — v2392's lesson: a `why` string is prose and improving
#: the wording must not silently change what runs. Tags come from reel_retention.RULES.
OWED_BY = {
    "never-chronicle-swept": "chronicle",
    "zero-pages":            "chronicle",
    "panels-never-banked":   "vault",
    "rows-not-banked":       "vault",
    "vault-owes":            "vault",
}

#: ⚠⚠ v2878 — OF THOSE, THE ONES A PAID RE-READ CAN ACTUALLY CLEAR.
#: A cross-family review of v2876: `OWED_BY` maps three tags to the vault lane, and v2876 queued
#: all three for a re-read. `rows-not-banked` is not a read — the sweep ALREADY ran and produced
#: rows; what is missing is a durable BANK. Queuing it spends up to _VAULT_AUTOREAD_MAX_TRIES paid
#: reads, the hold does not clear, and the reel is retired as "still owed" without ever banking.
#: Latent on his tree today (0 such reels) and the same over-queue shape as the 2026-08-28 incident,
#: aimed at the wrong verb.
#:
#: So the two questions are kept apart, because they are different questions:
#:     OWED_BY      -> WHICH LANE owns this reel   (what the panel reports as waiting)
#:     READ_CLEARS  -> can a READ clear it         (what the sweeper is allowed to pay for)
#: [[label-outlived-referent]] [[feedback-contradiction-is-the-finding]]
READ_CLEARS = ("never-chronicle-swept", "zero-pages", "panels-never-banked", "vault-owes")

#: Tags that mean the reel is finished and held for a reason no lane can clear.
HELD = ("recent", "test-fixture", "holds-proof", "target-met",
        "no-witness-index", "ledger-unreadable")


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# THE LANE CENSUS — Heart 2.0's discipline, aimed at LANES instead of GATES
# ═══════════════════════════════════════════════════════════════════════════════════════════════
#
# ⚠⚠ WHAT WAS MISSING, IN ONE SENTENCE FROM THIS FILE'S OWN DOCSTRING: *"a lane with work owed and
# a heartbeat that has stopped is the state `vaultAutoread` sat in for weeks with `reads: 0,
# lastTs: null` and nothing said so."* Heart 2.0 asks whether the GATES can still go red.
# `lane_liveness` asks whether a THREAD is still ticking. Nothing joined "there is work owed" to
# "this lane has done a unit of work", and those are the two halves of the only question that
# matters here. [[the-unjoined-end]] [[heart-first]]
#
# ⛔ AND THERE IS STILL NO SECOND PREDICATE. The census asks THREE different questions of THREE
# owners and joins them; it re-derives none of them:
#
#     is there work owed          `work()` -> reel_retention.plan()      (this module's one answer)
#     has this lane worked        the LANE'S OWN durable store           (asked of its owner)
#     is this lane allowed to act the flag its owner already keeps       (asked of its owner)
#
# If a "does this lane owe anything" function ever appears below, it is the defect this whole file
# is named after. [[feedback-contradiction-is-the-finding]]
#
# ⚠ AND IT READS THE **STORE**, NOT PROCESS MEMORY. That is #60's whole lesson one level up: a
# process-local counter reports a RESTART as "this lane has never swept", which is a completely
# different accusation from the truth. Every reading below comes off disk, so a restart cannot
# manufacture a dark lane — and where a lane keeps nothing on disk, that is reported as a
# durability failure rather than papered over. [[unknown-stays-unknown]]

#: Work owed, and this lane completed a unit inside its own declared bound.
FLOWING = "FLOWING"
#: Work owed, this lane HAS completed units, and staleness is not decidable — no WORK period is
#: declared for it, or nothing durable records WHEN the last unit happened. Not a clean bill.
UNTIMED = "UNTIMED"
#: Work owed, this lane has worked, and its last unit is older than its own declared bound.
STALLED = "STALLED"
#: ⚠ THE ONE THIS FILE EXISTS FOR. Work owed, and this lane has NEVER completed a unit of work.
#: NO THRESHOLD IS INVOLVED — which is why it is the red that can actually be trusted. A bound is a
#: number somebody guessed; "owed > 0 and works == 0" is two measurements and a conjunction. The
#: vault lane sat in exactly this state for weeks. [[feedback-threshold-above-the-ceiling]]
DARK = "DARK"
#: Nothing owed, measured, WITH the denominator printed beside it. A 0 with no denominator is not
#: IDLE, it is UNKNOWN. [[zero-needs-a-denominator]]
IDLE = "IDLE"
#: Not acting, and the reason is KNOWN and by design — copied from `lane_liveness.DORMANT`, for its
#: reason: collapsing a known reason into UNKNOWN sends a reader hunting a fault that is not there,
#: and hides the case that IS one.
DORMANT = "DORMANT"
#: Could not ask. NEVER renders as IDLE and never as "nothing owed".
UNKNOWN = "UNKNOWN"

#: How many of its own declared bounds a lane may miss before it is STALLED. Same number and same
#: reasoning as `lane_liveness.STALE_SLACK`: 1.0 would fire on ordinary jitter, and a gate that
#: cries wolf is one he learns to skip.
BOUND_SLACK = 3.0

#: ⚠⚠ EVERY LANE DECLARED, INCLUDING THE ONES WITH NOTHING TO DO TODAY — that is the whole
#: discipline borrowed from the gate census. `beat()` used to write `owedByLane`, which is built by
#: counting owed reels, so a lane owing zero was simply ABSENT from the record. MEASURED on his
#: tree 2026-09-10: `owedByLane` read `{"vault": 18}` and the chronicle lane — which exists, has a
#: store, and has a watchdog — appeared nowhere at all. Absent and healthy looked identical, which
#: is the exact failure `lane_census.py` was written about one level down. [[unknown-stays-unknown]]
#:
#: Each entry says where the lane's OWN record lives and which key in it means what. It never says
#: whether that record is durable — that is MEASURED from the store's own keys, because a hand-kept
#: durability flag is the rot `lane_census.supervisor_set_is_current` already had to make
#: falsifiable. [[label-outlived-referent]]
LANES = {
    "chronicle": {
        "what": "reads a reel's chronicle pages so its names can be banked",
        "owedFrom": "tags",
        "owner": "control_app",
        # ⚠ resolved at control_app's IMPORT time, not at call time. A census run after TV_HIST
        # changes reads whichever world that module was imported into. Named here rather than
        # worked around, because the fix belongs in control_app and this file does not own it.
        "store": "_CHRON_AUTOREAD_PATH",
        # ⚠⚠ `done` IS THE DURABLE UNIT COUNT, AND `reads` IS NOT. `_CHRON_AUTOREAD["reads"]` is a
        # process counter that no writer persists — `_chron_autoread_save`'s payload is exactly
        # {done, reels, retired, skipped}, measured on his store. Reading `reads` here would make
        # every restart report a lane that has never worked, which is #60 verbatim.
        "worksKey": "done",
        "worksAs": "len",
        # ⚠⚠ AND ITS `lastTs` IS NOT A CLOCK READING. `_CHRON_AUTOREAD["lastTs"] = ts` stores the
        # VISIT's timestamp; the vault's sibling field stores `int(time.time()*1000)`. Same field
        # name, two different quantities, in two sibling lanes — so "when did this lane last work"
        # is genuinely UNKNOWN for the chronicle lane and is reported as UNKNOWN, never guessed
        # from the newest visit it has read. [[label-outlived-referent]]
        "lastKey": None,
        "lastWhy": ("nothing durable records WHEN this lane last worked: its store carries "
                    "{done, reels, retired, skipped} and no clock reading, and the in-memory "
                    "`lastTs` holds a VISIT id rather than a time"),
        "boundS": None,
        "armedFrom": None,
    },
    "vault": {
        "what": "sweeps a reel so its panels reach the vault ledger",
        "owedFrom": "tags",
        "owner": "control_app",
        "store": "_vault_autoread_path",
        "worksKey": "reads",
        "worksAs": "int",
        "lastKey": "lastTs",
        "lastWhy": "",
        "boundS": None,
        "armedFrom": None,
    },
    "deleter": {
        # The outlet. Its work-list is the plan's OWN `candidates` — the same call, the same
        # answer, read off a different field. Not a second predicate.
        "what": "tombstones a reel every lane has finished with, then reclaims its frames",
        "owedFrom": "releasable",
        "owner": "reel_retention",
        "store": "_tombstone_path",
        "worksKey": "reels",
        "worksAs": "len",
        "lastKey": "updatedTs",
        "lastWhy": "",
        "boundS": None,
        # ⚠ ASKED, NOT DECIDED. `_PRUNE_SAFE_TO_RUN` is Konyo's to arm and this module must never
        # form an opinion about it. Without this read, a disarmed prune with releasable reels
        # waiting would be reported DARK — an alarm about a deliberate decision, which is how a
        # supervision layer teaches him to ignore it.
        "armedFrom": ("control_app", "_PRUNE_SAFE_TO_RUN"),
        "dormantWhy": ("the prune is armed by Konyo and is not armed. Reels may sit releasable "
                       "indefinitely and that is a decision, not a stall"),
    },
}


#: ⚠⚠ THE SCOPE, SAID OUT LOUD, BECAUSE A PARTIAL CENSUS THAT DOES NOT SAY SO IS A FULL ONE THAT
#: LIES. His console starts 12 background loops. THREE of them own a work-list on the shelf and are
#: declared above. The other NINE are named here with the reason they are not, so "absent from this
#: table" can never be mistaken for "forgotten" — which is the whole complaint this census answers
#: one level up. Whether those nine are ALIVE is a different question with a different owner:
#: `lane_liveness` asks it, and its answer is thread-local by design.
#:
#:     tvd-retro-triage    acts on reels, and its work-list is NOT in the retention plan. Declaring
#:                         it would mean writing a second "which reels need triage" predicate — the
#:                         exact defect this module is named after. It needs an owed-count from its
#:                         OWN authority before it can be supervised here.
#:     tvd-shadow-watch    watches for the game, not for reels
#:     tvd-stash-watch     seals a reel a lane already declared; no work-list of its own
#:     tvd-rolling-prune   prunes duplicate LIVE frames mid-recording, not shelved reels
#:     tvd-ledger-backup   copies a ledger out; nothing on the shelf waits on it
#:     tvd-space-warden    reclaims regenerable test output, never footage
#:     tvd-version-drift   announces a stale process
#:     tvd-eagle-watch     a supervisor, not a worker
#:     tvd-runaway-watch   a supervisor, not a worker
#: [[unknown-stays-unknown]] [[zero-needs-a-denominator]]
NOT_SHELF_LANES = ("tvd-retro-triage", "tvd-shadow-watch", "tvd-stash-watch", "tvd-rolling-prune",
                   "tvd-ledger-backup", "tvd-space-warden", "tvd-version-drift",
                   "tvd-eagle-watch", "tvd-runaway-watch")


def declared_covers_the_map(owed_by=None, lanes=None):
    """Does every lane the TAG MAP names also have a declaration here? -> (ok, why)

    ⚠⚠ A HAND-KEPT SET ROTS, AND THIS FILE ALREADY KNOWS IT. `lane_census.supervisor_set_is_current`
    exists for the same reason and says it best: a declaration that silently stops matching makes
    the warning disappear and the table render as if nothing were wrong. `LANES` is hand-kept; add a
    tag to `OWED_BY` pointing at a lane nobody declared and that lane's reels would be counted into
    a total and shown on no row.

    This does not make `LANES` self-deriving — a lane's store, its unit key and its arming flag
    cannot be inferred from a tag. It makes it FALSIFIABLE, which is the achievable half.
    """
    owed_by = OWED_BY if owed_by is None else owed_by
    lanes = LANES if lanes is None else lanes
    gone = sorted(set(owed_by.values()) - set(lanes))
    if gone:
        return False, ("%d lane(s) are named by the tag map and DECLARED NOWHERE: %s. Their reels "
                       "are counted as owed and appear on no row, so the shelf reports work that "
                       "belongs to nobody." % (len(gone), ", ".join(gone)))
    return True, "every lane the tag map names is declared"


def _owner_module(name, allow_import=False):
    """The module that OWNS a lane's record. -> (module|None, why)

    ⚠ IT DOES NOT IMPORT BY DEFAULT, AND THAT IS DELIBERATE. `control_app` is a 27,000-line module;
    importing it to answer an HTTP request would be the wrong shape, and importing it inside a gate
    drags a fixture's whole world in behind it. When it is already loaded — which is every case that
    matters, because the console IS control_app — its record is right there. When it is not, the
    answer is UNKNOWN with a reason, never a confident zero.
    """
    m = sys.modules.get(name)
    if m is not None:
        return m, ""
    if not allow_import:
        return None, ("%s is not loaded in this process, so this lane's own record cannot be "
                      "asked. That is UNKNOWN — not an idle lane" % name)
    try:
        return __import__(name), ""
    except Exception as e:
        return None, "%s could not be imported (%s)" % (name, type(e).__name__)


def _store_path(decl, allow_import=False):
    """Where a lane's durable record lives, asked of its OWNER. -> (path|None, why)

    ⚠ ONE DEFINITION OF THE PATH. Every one of these files already has an owner that computes its
    location, honours TV_HIST and has been fixed there more than once. Recomputing any of them here
    would be a second definition of a filename, which is this repo's most expensive habit — the
    `.heart2.json` literal that `_heart2_census` had to be taught to stop inventing is the same
    shape. [[copy-drift]]
    """
    mod, why = _owner_module(decl.get("owner"), allow_import=allow_import)
    if mod is None:
        return None, why
    attr = getattr(mod, decl.get("store") or "", None)
    if attr is None:
        return None, ("%s.%s is gone — the lane's store has been renamed or removed, so where its "
                      "record lives is UNKNOWN" % (decl.get("owner"), decl.get("store")))
    try:
        return (attr() if callable(attr) else str(attr)), ""
    except Exception as e:
        return None, ("%s.%s raised (%s), so where its record lives is UNKNOWN"
                      % (decl.get("owner"), decl.get("store"), type(e).__name__))


def _read_store(path):
    """-> (doc, readable). readable is True | False (no store yet) | None (UNKNOWN).

    The three outcomes are the vault store's own, and they are kept apart for its reason: an
    UNREADABLE store read as a fresh start turns "nobody could measure this" into "this lane has
    done nothing", and those are opposite facts. [[unknown-stays-unknown]]
    """
    if not path:
        return None, None
    if not os.path.isfile(path):
        return None, False
    try:
        with io.open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        return (d if isinstance(d, dict) else None), (True if isinstance(d, dict) else None)
    except Exception:
        return None, None


def lane_beat(lane, decl=None, allow_import=False):
    """What a lane's OWN durable record says it has done. -> dict

    Never a judgement, never a second opinion about work owed — only: how many units this lane has
    completed, when the last one was, and whether either of those survives a restart.
    """
    decl = LANES[lane] if decl is None else decl
    # ⚠⚠ DURABILITY HAS TWO HALVES AND THEY COME APART. A first cut reported one `durable` bool
    # measured from the unit-count key alone, and the chronicle lane — which persists `done` and NO
    # clock reading anywhere — came back `durable: True`. That is a right measurement under a word
    # that had stopped being true of the whole heartbeat: the count survives a restart and "when did
    # this lane last work" does not. So both halves are measured and `durable` means BOTH.
    # [[label-outlived-referent]] [[zero-needs-a-denominator]]
    out = {"lane": lane, "resolved": False, "store": None, "storeReadable": None,
           "works": None, "lastWorkAt": None,
           "durable": None, "durableWorks": None, "durableLast": None, "durableWhy": "", "why": ""}
    path, why = _store_path(decl, allow_import=allow_import)
    out["store"] = path
    if path is None:
        out["why"] = why
        return out
    doc, readable = _read_store(path)
    out["resolved"] = True
    out["storeReadable"] = readable
    if readable is None:
        out["why"] = ("this lane's store exists and could NOT be read, so how much it has done is "
                      "UNKNOWN. An empty count here would be a claim nobody measured")
        return out
    if readable is False:
        # A genuine fresh start IS a fact, and it is the fact that makes DARK reachable.
        out.update({"works": 0, "lastWorkAt": None, "durable": False,
                    "durableWorks": False, "durableLast": False,
                    "durableWhy": "there is no store on disk at all, so nothing this lane learns "
                                  "would survive a restart",
                    "why": "no store yet — this lane has genuinely never recorded a unit of work"})
        return out
    wkey = decl.get("worksKey")
    lkey = decl.get("lastKey")
    raw = (doc or {}).get(wkey)
    # ⚠ DURABILITY IS MEASURED FROM THE STORE'S OWN KEYS, not declared. Measured on his tree:
    # `.vault_autoread.json` carries reads AND lastTs; `chron_autoread.json` carries {done, reels,
    # retired, skipped} and no clock reading of any kind.
    out["durableWorks"] = wkey in (doc or {})
    out["durableLast"] = bool(lkey) and lkey in (doc or {})
    out["durable"] = bool(out["durableWorks"] and out["durableLast"])
    out["durableWhy"] = ("both halves survive a restart" if out["durable"] else
                         ("the unit COUNT survives a restart and no clock reading does, so after a "
                          "restart 'when did this lane last work' is UNKNOWN"
                          if out["durableWorks"] else
                          ("only the clock reading survives a restart; the unit count does not"
                           if out["durableLast"] else
                           "neither the unit count nor a clock reading survives a restart")))
    if raw is None:
        out["why"] = ("this lane's store carries no %r key, so how much it has done is UNKNOWN and "
                      "does not survive a restart" % wkey)
        return out
    try:
        out["works"] = len(raw) if decl.get("worksAs") == "len" else int(raw)
    except Exception:
        out["why"] = "this lane's %r is not a number this reader understands" % wkey
        return out
    if not lkey:
        out["why"] = decl.get("lastWhy") or ""
        return out
    try:
        v = (doc or {}).get(lkey)
        out["lastWorkAt"] = None if v in (None, 0) else int(v)
    except Exception:
        out["lastWorkAt"] = None
    if out["lastWorkAt"] is None:
        out["why"] = ("this lane's store carries no readable %r, so WHEN it last worked is UNKNOWN"
                      % lkey)
    return out


def lane_beats(allow_import=False):
    """Every declared lane's own record, in one dict. -> {lane: beat}"""
    return dict((k, lane_beat(k, v, allow_import=allow_import)) for k, v in LANES.items())


def _armed(decl, allow_import=False):
    """Is this lane allowed to act? -> (True|False|None, why). None is UNKNOWN, never False."""
    src = decl.get("armedFrom")
    if not src:
        return True, ""
    mod, why = _owner_module(src[0], allow_import=allow_import)
    if mod is None:
        return None, why
    if not hasattr(mod, src[1]):
        return None, ("%s.%s is gone, so whether this lane is allowed to act is UNKNOWN"
                      % (src[0], src[1]))
    return bool(getattr(mod, src[1])), ""


def _lane_state(row):
    """The one verdict, from readings already taken. -> (state, why)

    ⚠ THE ORDER IS THE LAW. Every early return here is a case that must not be allowed to fall
    through into a calmer word: an unmeasurable work-list must not become IDLE, a zero without a
    denominator must not become IDLE, and a lane nobody could ask about must not become DARK.
    """
    owed, on_disk = row.get("owed"), row.get("onDisk")
    # 1. WORK OWED COULD NOT BE MEASURED. "cannot ask" and "nothing owed" are opposite facts.
    if owed is None:
        return UNKNOWN, ("how much this lane owes could not be measured — %s. That is UNKNOWN, and "
                         "it is not an idle lane" % (row.get("owedWhy") or "no reason given"))
    # 2. A ZERO WITH NO DENOMINATOR IS UNKNOWN. Nothing owed out of nothing counted is not a
    #    measurement of an empty work-list, it is an absent measurement. [[zero-needs-a-denominator]]
    if owed == 0 and on_disk is None:
        return UNKNOWN, ("this lane owes 0 of an UNKNOWN number of reels. A count with no "
                         "denominator cannot say whether the shelf is clear or unread")
    # 3. DELIBERATELY NOT ACTING, WITH A REASON. Before IDLE, so a disarmed lane with a clear
    #    work-list still says WHY it is not acting rather than looking finished.
    if row.get("armed") is False:
        return DORMANT, ("%d owed of %s on the shelf, and this lane is not acting BY DESIGN: %s"
                         % (owed, on_disk, row.get("dormantWhy") or "no reason declared"))
    # 4. NOTHING OWED, AND THE DENOMINATOR IS RIGHT THERE.
    if owed == 0:
        return IDLE, "nothing owed of %s reel(s) on the shelf" % on_disk
    # 5. WORK IS OWED AND NOBODY COULD ASK THIS LANE WHAT IT HAS DONE.
    if not row.get("resolved") or row.get("works") is None:
        return UNKNOWN, ("%d reel(s) owed, and what this lane has done could not be measured — %s. "
                         "An unmeasured lane is not a stopped one, and it is not a working one"
                         % (owed, row.get("beatWhy") or "no reason given"))
    # 6. ⚠⚠ DARK. Work owed, and this lane has NEVER completed a unit. No threshold is involved.
    if not row.get("works"):
        return DARK, ("%d reel(s) owed of %s on the shelf, and this lane has completed 0 units of "
                      "work. That is the state the vault lane sat in for weeks with reads 0 and "
                      "lastTs null while nothing said so" % (owed, on_disk))
    # 7. It has worked, and nothing durable says when.
    if row.get("lastWorkAt") is None:
        return UNTIMED, ("%d reel(s) owed; this lane has completed %d unit(s) and nothing durable "
                         "records WHEN, so whether it has stopped cannot be decided from here — %s"
                         % (owed, row["works"], row.get("beatWhy") or "no clock reading is kept"))
    # 8. It has worked, recently enough to place in time, and no WORK period is declared for it.
    #    ⚠ A TICK PERIOD IS NOT A WORK PERIOD. The vault loop wakes every few seconds and a paid
    #    sweep takes minutes, so grading the work against the loop's sleep would report every
    #    healthy lane STALLED. No lane declares a measured work period today, and that gap is
    #    printed in the census `why` rather than papered over with a guess.
    bound = row.get("boundS")
    if bound is None:
        return UNTIMED, ("%d reel(s) owed; this lane last worked %s ago and declares no WORK "
                         "period, so whether that is late cannot be decided from here"
                         % (owed, _ago(row.get("lastWorkAgeMs"))))
    if (row.get("lastWorkAgeMs") or 0) > bound * 1000.0 * BOUND_SLACK:
        return STALLED, ("%d reel(s) owed and this lane last worked %s ago against its own %gs "
                         "period" % (owed, _ago(row.get("lastWorkAgeMs")), bound))
    return FLOWING, ("%d reel(s) owed and this lane worked %s ago, within its own %gs period"
                     % (owed, _ago(row.get("lastWorkAgeMs")), bound))


def _ago(ms):
    """A duration a person can read. -> str ('UNKNOWN' when nobody measured it)."""
    if ms is None:
        return "an UNKNOWN time"
    s = max(0.0, float(ms) / 1000.0)
    if s < 90:
        return "%.0fs" % s
    if s < 5400:
        return "%.0fm" % (s / 60.0)
    return "%.1fh" % (s / 3600.0)


def lane_census(hist=None, work_=None, beats=None, now_ms=None, allow_import=False):
    """Every declared lane: what it owes, when it last worked, and whether that survives. -> dict

    `work_` and `beats` exist so a law can drive this over a known shelf and a known set of lane
    records without touching his footage or his stores — the same door `reel_retention.plan(hist)`
    and `lane_census.census(src)` already open. Production callers pass neither.

    ⚠ UNKNOWN IS A FIRST-CLASS ANSWER IN EVERY COLUMN, and the counts never collapse it into a
    verdict: a census where nothing could be read reports 0 dark and 0 flowing, which is not a clean
    bill and does not read as one. [[unknown-stays-unknown]]
    """
    now_ms = int(time.time() * 1000) if now_ms is None else int(now_ms)
    w = work_ if work_ is not None else work(hist)
    if not w.get("ok"):
        # ⚠⚠ EVERY LANE STILL GETS A ROW, AND EVERY ROW SAYS UNKNOWN. A plan that could not be read
        # must never shorten the table — an absent lane and a clear lane look identical, which is
        # the defect this census exists to end.
        owed_all, owed_why = None, str(w.get("why") or "the shelf could not be read")
        on_disk = None
    else:
        owed_all, owed_why, on_disk = w.get("owed"), "", w.get("onDisk")
    beats = lane_beats(allow_import=allow_import) if beats is None else beats
    rows = []
    for lane in sorted(LANES):
        decl = LANES[lane]
        b = dict(beats.get(lane) or {})
        if decl.get("owedFrom") == "releasable":
            owed = None if owed_all is None else len(w.get("releasable") or [])
        elif owed_all is None:
            owed = None
        else:
            owed = len([r for r in owed_all if r.get("lane") == lane])
        armed, armed_why = _armed(decl, allow_import=allow_import)
        last_at = b.get("lastWorkAt")
        row = {
            "lane": lane,
            "what": decl.get("what"),
            "owedFrom": decl.get("owedFrom"),
            "tags": sorted(t for t, l in OWED_BY.items() if l == lane),
            "readClears": sorted(t for t, l in OWED_BY.items()
                                 if l == lane and t in READ_CLEARS),
            "owed": owed,
            "owedWhy": owed_why,
            "onDisk": on_disk,
            "resolved": bool(b.get("resolved")),
            "store": b.get("store"),
            "storeReadable": b.get("storeReadable"),
            "works": b.get("works"),
            "lastWorkAt": last_at,
            "lastWorkAgeMs": (None if last_at is None else max(0, now_ms - int(last_at))),
            "durable": b.get("durable"),
            "durableWorks": b.get("durableWorks"),
            "durableLast": b.get("durableLast"),
            "durableWhy": b.get("durableWhy") or "",
            "beatWhy": b.get("why") or "",
            "boundS": decl.get("boundS"),
            "armed": armed,
            "armedWhy": armed_why,
            "dormantWhy": decl.get("dormantWhy"),
        }
        row["state"], row["why"] = _lane_state(row)
        rows.append(row)
    counts = {"declared": len(rows)}
    for st in (FLOWING, UNTIMED, STALLED, DARK, IDLE, DORMANT, UNKNOWN):
        counts[st.lower()] = len([r for r in rows if r["state"] == st])
    counts["durable"] = len([r for r in rows if r["durable"] is True])
    counts["bounded"] = len([r for r in rows if r["boundS"] is not None])
    dec_ok, dec_why = declared_covers_the_map()
    if counts[DARK.lower()]:
        say = ("%d of %d lane(s) have work owed and have never done any of it"
               % (counts[DARK.lower()], counts["declared"]))
    elif counts[STALLED.lower()]:
        say = "%d of %d lane(s) have stopped working while work waits" % (
            counts[STALLED.lower()], counts["declared"])
    elif counts[UNKNOWN.lower()]:
        say = "%d of %d lane(s) could not be measured at all" % (
            counts[UNKNOWN.lower()], counts["declared"])
    elif counts[UNTIMED.lower()]:
        # ⚠⚠ UNTIMED IS NOT A CLEAN BILL AND MUST NOT BE SUMMARISED AS ONE. A first cut's closing
        # sentence read "3 of 3 lane(s) are working or idle with nothing owed" over a census whose
        # vault row carried owed 8 — a right count under a phrase that had stopped describing it.
        # This is the headline on his tree today, so it says exactly what is true: work is waiting
        # and nothing can decide whether the lane carrying it has stopped.
        # [[label-outlived-referent]] [[zero-needs-a-denominator]]
        say = ("%d of %d lane(s) have work owed and no way to tell whether they have stopped"
               % (counts[UNTIMED.lower()], counts["declared"]))
    else:
        say = ("no lane is dark or stalled — %d flowing · %d idle · %d dormant of %d declared"
               % (counts[FLOWING.lower()], counts[IDLE.lower()],
                  counts[DORMANT.lower()], counts["declared"]))
    # ⚠ THE TWO GAPS TRAVEL WITH THE VERDICT. `bounded` is how many lanes could ever reach STALLED;
    # with none declared, STALLED is a state nothing can produce and a reader deserves to know that
    # rather than trusting an absence. `durable` is how many survive a restart. Both are printed as
    # N of M, because a gap with no denominator is the thing this file argues against.
    say += (" · %d of %d keep a durable record · %d of %d declare a WORK period, so STALLED is "
            "reachable for %d" % (counts["durable"], counts["declared"],
                                  counts["bounded"], counts["declared"], counts["bounded"]))
    return {"ok": True, "rows": rows, "counts": counts, "say": say,
            "onDisk": on_disk, "declaredOk": dec_ok, "declaredWhy": dec_why,
            "slack": BOUND_SLACK}


def plan(hist=None):
    """Retention's own answer, unmodified. -> dict"""
    import reel_retention as _rr
    h = hist or os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")
    return _rr.plan(h)


def work(hist=None):
    """What the lanes still owe, straight off retention's plan. -> dict

    ⚠ UNKNOWN IS NOT "NOTHING OWED". A plan that could not be built returns ok False and an
    explicit why, never an empty work list — an empty list is a MEASUREMENT ("every lane is
    caught up") and must never be produced by a failed read. [[unknown-stays-unknown]]
    [[zero-needs-a-denominator]]
    """
    try:
        p = plan(hist)
    except Exception as e:
        return {"ok": False, "why": "retention could not plan (%s)" % type(e).__name__,
                "owed": None, "held": None, "releasable": None}
    if not p.get("ok"):
        return {"ok": False, "why": str(p.get("say") or "retention could not read this shelf"),
                "owed": None, "held": None, "releasable": None}
    owed, held = [], []
    for k in (p.get("kept") or []):
        tag = k.get("tag")
        row = {"reel": k.get("reel"), "tag": tag, "why": k.get("why"), "mb": k.get("mb")}
        if tag in OWED_BY:
            row["lane"] = OWED_BY[tag]
            owed.append(row)
        else:
            held.append(row)
    return {"ok": True, "why": "", "owed": owed, "held": held,
            "releasable": [c.get("reel") if isinstance(c, dict) else str(c)
                           for c in (p.get("candidates") or [])],
            "onDisk": p.get("onDisk"), "say": p.get("say")}


def stages(hist=None):
    """Every reel placed on the river, newest first. -> dict

    ⚠ NEWEST FIRST, because that is how he reads it: *"timestamps organzied from what came in
    last"*. The reel id carries the stamp (`reel_s_<ms>_<n>`), so the order is the film's own,
    never the filesystem's.
    """
    import reel_story as _rs
    w = work(hist)
    if not w.get("ok"):
        return {"ok": False, "why": w.get("why"), "rows": None}
    rows = []
    for row in (w["owed"] or []) + (w["held"] or []):
        stage = _rs.TAG_STAGE.get(row["tag"])
        rows.append(dict(row, stage=stage, ts=_reel_ts(row["reel"])))
    for r in (w["releasable"] or []):
        rows.append({"reel": r, "tag": "eligible", "why": "every lane is finished with it",
                     "lane": None, "stage": _rs.TAG_STAGE.get("eligible"), "ts": _reel_ts(r)})
    rows.sort(key=lambda r: (r["ts"] is None, -(r["ts"] or 0)))
    unplaced = [r["reel"] for r in rows if not r["stage"]]
    return {"ok": True, "why": "", "rows": rows, "stageOrder": list(_rs.STAGES),
            "unplaced": unplaced, "onDisk": w.get("onDisk")}


def _reel_ts(reel):
    """The millisecond stamp inside `reel_s_<ms>_<n>`. -> int|None (None is UNKNOWN, not 0)."""
    try:
        return int(str(reel).split("_")[2])
    except Exception:
        return None


def beat(hist=None, write=True):
    """Record that the driver looked, and what it saw. -> dict

    This is what Heart 2.0 supervises: a lane with work owed and a heartbeat that has stopped is
    the state `vaultAutoread` sat in for weeks with `reads: 0, lastTs: null` and nothing said so.
    """
    w = work(hist)
    lanes = {}
    for row in (w.get("owed") or []):
        lanes[row["lane"]] = lanes.get(row["lane"], 0) + 1
    # ⚠ THE SAME `work()` ANSWER, PASSED IN. Calling lane_census() bare here would build a SECOND
    # retention plan for one beat — two reads of a moving shelf, which can disagree, and paid for
    # twice. One question, asked once.
    try:
        cen = lane_census(hist, work_=w)
    except Exception as e:
        cen = {"ok": False, "rows": None, "counts": None,
               "say": "the lane census could not be built (%s), so nothing is known about any "
                      "lane — which is not the same as every lane being fine" % type(e).__name__}
    out = {"at": int(time.time() * 1000), "ok": bool(w.get("ok")), "why": w.get("why") or "",
           # ⚠ KEPT, AND NO LONGER THE WHOLE STORY. `owedByLane` is built by COUNTING owed reels,
           # so a lane owing zero is absent from it — measured on his tree, it read {"vault": 18}
           # and the chronicle lane appeared nowhere. Existing readers keep their field; `lanes`
           # below is the one that declares every lane whether it owes anything or not.
           "owedByLane": lanes,
           "lanes": cen.get("rows"),
           "laneCounts": cen.get("counts"),
           "laneSay": cen.get("say"),
           "owed": None if w.get("owed") is None else len(w["owed"]),
           "held": None if w.get("held") is None else len(w["held"]),
           "releasable": None if w.get("releasable") is None else len(w["releasable"]),
           "onDisk": w.get("onDisk")}
    if write:
        # ⚠⚠ tmp + os.replace, NEVER a bare open(p, "w"). That call TRUNCATES BEFORE it writes, so a
        # crash or a full disk mid-beat leaves an empty file that reads back as a lane census
        # nobody could build — and this repo has already emptied a 6 MB bible.html exactly that way.
        # [[open-for-write-truncates-first]] [[bible-writes-must-be-atomic]]
        dest = _beat_path()
        if dest is None:
            out["persisted"] = False
            out["persistWhy"] = ("TV_HIST asked for a fixture world and the isolation rule could "
                                 "not be resolved, so this beat was NOT written anywhere rather "
                                 "than written into his live tv/")
            return out
        try:
            tmp = dest + ".tmp"
            with io.open(tmp, "w", encoding="utf-8") as fh:
                json.dump(out, fh, indent=1)
            os.replace(tmp, dest)
            out["persisted"] = True
        except Exception as e:
            out["persisted"] = False
            out["persistWhy"] = "%s — the beat was not recorded" % str(e)[:120]
    return out


def last_beat():
    """The last recorded look. -> dict|None (None means it has NEVER run — not 'nothing owed')."""
    try:
        with io.open(_beat_path(), encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def main(argv):
    b = beat()
    print("🎞🚚 SHELF DRIVER — retention decides, this runs it")
    if not b["ok"]:
        print("   ⚠ UNMEASURED: %s" % b["why"])
        return 1
    print("   %s reel(s) on disk · %s owed · %s held · %s releasable"
          % (b["onDisk"], b["owed"], b["held"], b["releasable"]))
    # ── THE LANE CENSUS. Every declared lane gets a row, including the ones owing nothing. ──────
    cen = lane_census(allow_import=True)
    if not cen.get("declaredOk"):
        print("   🔴 %s" % cen.get("declaredWhy"))
    print("\n   LANES — %s" % cen["say"])
    _mark = {FLOWING: "🟢", IDLE: "⚪", DORMANT: "🟡", UNTIMED: "🟠",
             STALLED: "🔴", DARK: "🔴", UNKNOWN: "❔"}
    for r in cen["rows"]:
        print("      %s %-10s %-8s owed %-6s works %-7s durable %-5s  %s"
              % (_mark.get(r["state"], "❔"), r["lane"], r["state"],
                 "UNK" if r["owed"] is None else r["owed"],
                 "UNK" if r["works"] is None else r["works"],
                 {True: "yes", False: "no", None: "UNK"}[r["durable"]],
                 r["why"][:96]))
    st = stages()
    if st["ok"]:
        if st["unplaced"]:
            print("   ⚠ %d reel(s) have no stage on the river: %s"
                  % (len(st["unplaced"]), st["unplaced"][:3]))
        for s in st["stageOrder"]:
            n = sum(1 for r in st["rows"] if r["stage"] == s)
            print("      %-12s %d" % (s, n))
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable as _cs
        _cs()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
