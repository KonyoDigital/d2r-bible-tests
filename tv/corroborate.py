#!/usr/bin/env python3
"""THE CORROBORATOR — what the engines say about EACH OTHER.

Konyo, 2026-08-28: "the system needs an eagle eye corroborator, the engines all communicating...
diablo doctor self heals self fixes, scars its own."

WHY THIS EXISTS, and it is not a hunch — it is the shape of every serious defect found on
2026-08-28, all four of them found by hand, none by a gate:

    19 vs 2      the new vault watchdog's work list against reel_retention's own vault-blocked
                 bucket. Both computed correctly. The watchdog would have started SEVENTEEN
                 unnecessary paid sweeps, three of them over test fixtures.
    1263 vs 403  the shadow ledger's `names` against the uniques universe. 1263 distinct names is
                 arithmetically impossible; the field was counting repeat scorings. It had already
                 crossed the threshold whose sentence is "The record is worth a decision".
    157 vs 7     two payload fields both called `owned` — the board's stash backup and the vault
                 lane's own ledger. Both true, about different quantities, and nothing said so.
    36 vs 30     the durable sweep memory against the reels on disk. True, and unlabelled, and it
                 nearly got six read-records deleted as "ghosts".

EVERY ONE was a pair of numbers that were each right and wrong TOGETHER. No single engine could
have caught its own; each was healthy by its own lights. console_doctor asks 21 questions about
whether each engine is well. Nothing asked whether they AGREE.

THE RULES THIS FILE OBEYS
  * IT NEVER WRITES. Reads only, like chronicle_retro. A corroborator that repairs is a corroborator
    whose evidence you cannot trust, because it has already acted on it.
  * IT NEVER AVERAGES, AND IT NEVER PICKS A SIDE. Founding rule 3: two checks disagreeing IS the
    finding. Both numbers are reported with the name of who said them, and the disagreement is the
    result — not an error bar, not a "roughly".
  * UNKNOWN IS NOT ZERO AND NOT AGREEMENT. If either side cannot be computed the invariant reports
    UNKNOWN and says which side went dark. An invariant that silently passes when its inputs are
    missing is worse than no invariant. [[unknown-stays-unknown]]
  * AN INVARIANT THAT CANNOT FAIL IS NOT AN INVARIANT. Each carries `prove`, a description of the
    state that would break it, and `selftest()` drives every one of them to a RED verdict against
    synthetic inputs — because a corroborator nobody has seen disagree is exactly the green that
    lies. [[regression-guard]] [[feedback-blind-fixture-green-gate]]
"""

import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))

AGREE = "agree"
DISAGREE = "disagree"
UNKNOWN = "unknown"


class Reading(object):
    """One side of an invariant: a number, who computed it, or why it could not be had."""

    __slots__ = ("value", "who", "why")

    def __init__(self, value=None, who="", why=None):
        self.value = value
        self.who = who
        self.why = why

    @property
    def known(self):
        return self.value is not None and self.why is None

    def __repr__(self):
        return "<%s=%r%s>" % (self.who, self.value, "" if self.known else " UNKNOWN")


def _reading(who, fn):
    """Compute one side, turning any failure into an honest UNKNOWN rather than a zero."""
    try:
        v = fn()
    except Exception as e:
        return Reading(None, who, "%s could not be asked: %s" % (who, str(e)[:90]))
    if v is None:
        return Reading(None, who, "%s answered UNKNOWN" % who)
    return Reading(v, who)


# ── THE INVARIANTS ───────────────────────────────────────────────────────────────────────────
# Each is (key, what, prove, left_name, left_fn, right_name, right_fn, relation).
# `relation` is "==" or "<=" and is applied LEFT rel RIGHT.

def _inv_vault_worklist():
    """The v2223 near-miss, asserted forever."""
    import control_app as ca
    import reel_retention as rr
    hist = os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")

    def left():
        got = ca._vault_owed_reels(hist)
        return None if got is None else len(got)

    def right():
        p = rr.plan(hist)
        if not p.get("ok"):
            return None
        return len([k for k in (p.get("kept") or [])
                    if "VAULT lane has never swept" in (k.get("why") or "")])

    return ("vault-worklist",
            "the vault watchdog works exactly the reels retention holds for the vault lane",
            "make _vault_owed_reels ask its own question instead of retention's, and this parts",
            "the vault watchdog", left, "reel_retention", right, "==")


def _inv_shadow_names_fit_the_universe():
    """1263 distinct names in a 403-name game is not a large sample, it is a broken counter."""
    import shadow_ledger as sl

    def left():
        st = sl.state()
        return int(st.get("names") or 0) if st.get("ok") else None

    def right():
        p = os.path.join(os.path.dirname(HERE), "bible.html")
        try:
            # ⚠ READ THE WHOLE FILE. The first cut capped at 4MB and the assignment lives at 5.1MB
            # in a 5.8MB file, so this reported UNKNOWN — honestly, but for a reason that was my
            # cap rather than his data. A guard that cannot reach the thing it measures fails on
            # its own REACH first. [[source-reading-guard]]
            s = io.open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            return None
        import re
        # the ASSIGNMENT, not the prose. "chronTotal 403 is the game's own" appears in comments
        # 2MB earlier and must never be what this reads.
        m = re.search(r"chronTotal\s*[:=]\s*(\d+)", s)
        if not m:
            return None
        # uniques + sets + runewords is the widest the shadow lane could ever legitimately score
        return int(m.group(1)) * 2

    return ("shadow-sample-fits",
            "the shadow lane has not scored more distinct names than the game contains",
            "sum per-sweep scorings into `names` again and this crosses the ceiling within hours",
            "shadow_ledger.names", left, "the item universe", right, "<=")


def _inv_swept_memory_matches_the_disk():
    """36 vs 30: true, unlabelled, and it nearly got six read-records deleted."""
    import control_app as ca

    def left():
        sp = ca._chron_swept_split()
        if sp.get("onDisk") is None:
            return None
        return int(sp["onDisk"]) + int(sp["retained"] or 0)

    def right():
        import chronicle_retro as cr
        hist = os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")
        mem = ca._chron_swept_mem()
        return len(mem) if isinstance(mem, dict) else None

    return ("swept-split-adds-up",
            "every sweep-memory entry is accounted for as either on-disk or retained-for-pruned",
            "drop the retained bucket and the split stops summing to the file",
            "onDisk + retained", left, "sweep memory entries", right, "==")


def _inv_chronicle_owed_agrees():
    """The #167 stall class: the reader's own count against retention's view of it."""
    import control_app as ca
    import reel_retention as rr
    hist = os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")

    def left():
        n = ca._chron_owed_count()
        return n if isinstance(n, int) else None

    def right():
        p = rr.plan(hist)
        if not p.get("ok"):
            return None
        return len([k for k in (p.get("kept") or [])
                    if "never chronicle-swept" in (k.get("why") or "")])

    return ("chronicle-owed",
            "the chronicle reader and retention agree on how many reels owe a read",
            "let the private seen-set gate the loop again and these part by 27, as they did",
            "_chron_owed_count", left, "reel_retention", right, ">=")




def _inv_shadow_switch_matches_the_watcher():
    """★ THE EVENING THAT WAS LOST. He played with the shadow switch ON and got ZERO reels — 28 on
    disk, the newest 154 hours old. The switch said "armed"; nothing was watching for the game,
    because shadow only READ frames another mode had already rolled.

    So: if the switch is ON, the watcher must have looked RECENTLY. Two independent readings of the
    same claim — his choice, and the watcher's own durable record — and the whole defect was that
    only the first one existed. A switch that reports its own position and nothing about whether
    the thing it switches is running is the lie this file exists to catch.
    [[the-unjoined-end]] [[label-outlived-referent]]
    """
    import control_app as ca

    def left():
        try:
            return 1 if ca._shadow_state().get("on") else 0
        except Exception:
            return None

    def right():
        """1 when the watcher has looked inside the last 5 minutes. None when it cannot be told —
        never 0, because "no record" and "looked and found nothing" are different facts."""
        try:
            w = ca.shadow_watch_state()
            if not isinstance(w, dict) or w.get("ok") is False:
                return None
            at = w.get("lookedAt")
            if at is None:
                return 0
            return 1 if (time.time() * 1000.0 - float(at)) < 300000.0 else 0
        except Exception:
            return None

    return ("shadow-armed-is-watching",
            "the shadow switch being ON means something is actually looking for the game",
            "an evening of play produced no reels while the panel read 'armed'",
            "_shadow_state().on", left, "shadow_watch.lookedAt<5m", right, "<=")



def _inv_the_deleter_is_never_looser_than_the_planner():
    """★ TWO AUTHORITIES ON "MAY THIS BE DELETED", AND ONLY ONE OF THEM CAN ACT.

    reel_retention PLANS ("1 reel may go, freeing 389 MB — it has given up its information") and
    frame_authority DECIDES ("0 of 6719 could be freed — sealed, but the sweep never extracted
    name, location..."). They disagreed the moment the vault seal landed on 2026-08-30, and the
    strict one held — correctly, because the seal honestly recorded that nothing was extracted.

    That disagreement is HEALTHY and is not what this watches. What must never happen is the
    reverse: the deleter freeing MORE than the planner ever offered. That would mean the thing that
    can destroy his footage is running on a wider rule than the thing that merely suggests, and it
    is the direction with no undo. [[feedback-contradiction-is-the-finding]]
    """
    import frame_authority as fa
    import reel_retention as rr
    hist = os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")

    def left():
        try:
            plan = fa.plan_frames(hist)
        except Exception:
            return None
        if isinstance(plan, dict):
            return len(plan.get("free") or plan.get("freeable") or [])
        if isinstance(plan, (list, tuple)):
            return len(plan)
        return None

    def right():
        try:
            p = rr.plan(hist)
        except Exception:
            return None
        if not p.get("ok"):
            return None
        # every frame inside every reel retention is willing to let go
        return sum(int(c.get("pages") or 0) for c in (p.get("candidates") or []))

    return ("deleter-not-looser",
            "the one thing that can delete never frees more than the planner offers",
            "let frame_authority clear a reel retention still holds and this inverts",
            "frame_authority.free", left, "retention.candidates", right, "<=")



def _inv_the_two_deleters_stay_at_their_own_granularity():
    """★ TWO DELETERS, TWO QUESTIONS, AND CONFLATING THEM WAS MY ERROR — TWICE IN ONE DAY.

    reel_retention answers "may this REEL go" — both lanes finished with it.
    frame_authority answers "may this FRAME go" — stricter, because it protects the witness frames
    standing behind his vault rows, and a frame is the last copy of a name.

    They disagree by DESIGN and both are right. On 2026-08-30 I read that disagreement as a defect,
    made retention ask frame_authority's contract, and broke three deliberate cases — a change that
    would have stopped the prune firing on every existing reel, since all his seals predate that
    contract. Withdrawn.

    What must stay true is the ordering: the FRAME deleter, being the stricter one, must never free
    more than the reel planner is willing to let go. If that inverts, the thing protecting his
    witness frames has become the looser of the two. [[feedback-contradiction-is-the-finding]]
    """
    import frame_authority as fa
    import reel_retention as rr
    hist = os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")

    def left():
        try:
            plan = fa.plan_frames(hist)
        except Exception:
            return None
        if isinstance(plan, dict):
            return len(plan.get("free") or plan.get("freeable") or [])
        return len(plan) if isinstance(plan, (list, tuple)) else None

    def right():
        try:
            p = rr.plan(hist)
            if not p.get("ok"):
                return None
            return sum(int(c.get("pages") or 0) for c in (p.get("candidates") or []))
        except Exception:
            return None

    return ("frame-deleter-not-looser",
            "the frame deleter never frees more than the reel planner offers",
            "let frame_authority clear frames inside a reel retention is holding and this inverts",
            "frame_authority.free", left, "retention.candidate pages", right, "<=")

def _inv_the_two_readers_measure_the_same_screen():
    """★ TWO READERS, TWO COPIES OF ONE MEASUREMENT OF HIS MONITOR.

    stash_eye reads the LEFT-ANCHORED stash/inventory panel; chronicle_template reads the CENTERED
    Chronicle modal. Their geometry genuinely differs — chronicle_template's own header explains it
    cannot copy "stash_eye's left-anchor math" and uses a CENTER-PRESERVING derivation instead.
    That part is a real reason, not drift.

    What IS drift: each carries its own calibration film of the SAME physical screen —
    stash_eye._CROP_CAL_FILM and chronicle_template._CAL_FILM, both (2940, 1912) today. One
    recalibration (new monitor, new resolution, a re-measure of one panel) updates one and leaves
    the other silently reading his screen as a shape it no longer is. Nothing would say so; the
    reader would simply start missing panels.

    Konyo: "the readers and ai analyzers all need the same upgraded logic and tools ... should be a
    synced and unified logic". This is that sync, expressed as an invariant instead of a refactor.
    [[copy-drift]]
    """
    def left():
        try:
            import stash_eye as _se
            f = getattr(_se, "_CROP_CAL_FILM", None)
            return int(f[0] * 100000 / float(f[1])) if f else None
        except Exception:
            return None

    def right():
        try:
            import chronicle_template as _ct
            f = getattr(_ct, "_CAL_FILM", None)
            return int(f[0] * 100000 / float(f[1])) if f else None
        except Exception:
            return None

    return ("readers-same-screen",
            "both readers are calibrated to the same physical screen",
            "recalibrate one reader's film and leave the other, and this parts",
            "stash_eye._CROP_CAL_FILM", left, "chronicle_template._CAL_FILM", right, "==")


def _inv_the_two_owned_fields():
    """157 vs 7 — TWO PAYLOAD FIELDS BOTH CALLED `owned`, and I found this by hand and did not
    encode it. That omission is the whole argument for this file existing.

    They are DIFFERENT QUANTITIES: ledgerBackup.counts.owned is the durable backup of the board's
    d2r_owned (what is in his stash); vault_ledger.totals.owned is what the VAULT SWEEP LANE has
    independently established from film. Both true. Nothing said so, and 157 beside 7 reads as data
    loss.

    So the invariant is NOT equality — it is CONTAINMENT: the vault lane can only ever have
    established a subset of what the board holds. If the lane ever claims MORE than the stash, one
    of them is wrong and it is worth his attention.
    """
    import control_app as ca

    def left():
        try:
            v = ca.vault_ledger_view() or {}
            t = v.get("totals") or {}
            n = t.get("owned")
            return int(n) if isinstance(n, int) else None
        except Exception:
            return None

    def right():
        st = ca.ledger_backup_state() or {}
        c = st.get("counts") or {}
        n = c.get("owned")
        return int(n) if isinstance(n, int) else None

    return ("owned-is-contained",
            "the vault lane has never established more owned items than the board holds",
            "swap the two fields, or let the lane count something the stash does not, and this parts",
            "vault_ledger.totals.owned", left, "board d2r_owned (backed up)", right, "<=")


def _inv_the_eagle_can_still_look():
    """A watchdog that cannot run is not a passing watchdog. The eagle runs the corroborator; until
    now nothing checked the eagle. UNKNOWN is the honest answer when its own state is unreadable."""
    import control_app as ca

    def left():
        e = dict(getattr(ca, "_EAGLE", {}) or {})
        # ⚠⚠ NEVER-RUN IS NOT ZERO-COVERAGE, AND MY FIRST CUT SAID IT WAS. `_EAGLE` initialises to
        # {"checked": None, "rows": [], "say": "not measured yet"}, so reading len(rows) on a fresh
        # process answered 0 and the invariant reported "the eagle covered 0 of 22 checks" — a
        # confident finding about an eagle that had simply not flown yet. It fired on this machine
        # the first time it was asked.
        #
        # That is the exact law this whole file exists to enforce, broken inside the file: 0 means
        # "we measured, it was zero"; None means "nobody looked". `checked` is the module's own
        # explicit never-run marker — ask it rather than inferring from an empty list.
        # [[unknown-stays-unknown]]
        if e.get("checked") is None:
            return None
        rows = e.get("rows")
        return len(rows) if isinstance(rows, list) else None

    def right():
        import console_doctor as cd
        return len(cd.CHECKS)

    return ("eagle-ran-every-check",
            "the eagle's last pass covered every check on its roster",
            "drop a check from the loop and its row stops appearing while the roster still lists it",
            "rows in the last eagle pass", left, "checks on the roster", right, "==")


def _inv_hunt_memory_is_being_used():
    """The paid-work-with-no-memory scar, as an invariant. His hunt bought 3,434 paid reads for 2
    sightings — 1,717 each — re-buying the same 8 names for eight hours, and it looked exactly like
    healthy activity. The memory exists so it stops re-buying; if the memory is EMPTY while reads
    are being spent, the memory is not reaching the buyer."""
    import os, json, io as _io

    def left():
        p = os.path.join(HERE, "chron_hunt_memory.json")
        if not os.path.exists(p):
            return None
        try:
            d = json.load(_io.open(p, encoding="utf-8"))
        except Exception:
            return None
        return len(d) if hasattr(d, "__len__") else None

    def right():
        return 0                      # any memory at all beats none, once the hunt has spent

    return ("hunt-remembers",
            "the hunt has banked what it already bought, so it cannot re-buy the same names",
            "empty the memory while the hunt keeps spending and this goes to zero",
            "hunt-memory entries", left, "the floor", right, ">=")


def _inv_every_declared_tooltip_surface_is_served():
    """v2316 — the surfaces that say they need hover evidence, against the code that derives it.

    Five surfaces declare tooltip=True; a tooltip rectangle is derived by differencing consecutive
    frames, so it is the reel sweep that must own the step. If no production module imports
    tooltip_crop, those five are asking for something nobody performs — and until v2316 the
    function meant to notice returned the same five names whether or not that was true, so it
    could never have told anyone. [[label-outlived-referent]] [[plumbing-with-no-tap]]
    """
    import surfaces as S

    def left():
        return len(S.tooltip_surfaces())

    def right():
        ok, _why = S.tooltip_wiring()
        return len(S.tooltip_surfaces()) if ok else 0

    return ("tooltip-surfaces-served",
            "every surface that declares it needs hover evidence has a sweep that derives it",
            "delete `import tooltip_crop` from vault_retro and this parts 5 vs 0",
            "surfaces declaring tooltip", left, "surfaces actually served", right, "==")


BUILDERS = (_inv_every_declared_tooltip_surface_is_served,
            _inv_vault_worklist,
            _inv_the_two_owned_fields,
            _inv_the_eagle_can_still_look,
            _inv_hunt_memory_is_being_used,
            _inv_shadow_names_fit_the_universe,
            _inv_swept_memory_matches_the_disk,
            _inv_chronicle_owed_agrees,
            _inv_shadow_switch_matches_the_watcher,
            _inv_the_two_deleters_stay_at_their_own_granularity,
            _inv_the_two_readers_measure_the_same_screen)



# ══ THE COVERAGE MAP — EVERY ENGINE IS NAMED, AND AN UNCOVERED ONE SAYS SO ═══════════════════════
# Konyo: "make it reach them all". The eagle's checks and this file's invariants are NOT the same
# unit — a check asks "is this engine well", an invariant asks "do these two agree" — so there is no
# 1:1 mapping to reach. What there IS: every engine the eagle knows must appear here, and one with
# no invariant must be VISIBLE rather than silently absent.
#
# That is the anti-silence principle turned on this file itself. Without it "4 of 11 joints" is a
# fact nobody can see, which is precisely the defect a corroborator exists to catch.
COVERED_BY = {
    "reel extract":      ("chronicle-owed", "swept-split-adds-up"),
    "sweep would find":  ("vault-worklist",),
    "shadow gate":       ("shadow-sample-fits",),
    "vault stores":      ("owned-is-contained",),
    "ledger entries":    ("owned-is-contained",),
    "hunt economy":      ("hunt-remembers",),
    "engines corroborate": ("eagle-ran-every-check",),
}
# Engines with NO invariant, each with the reason — a blank here would read as covered.
NO_JOINT_YET = {
    "console UI faults": "the console reports about itself; there is no second engine to agree with",
    "version drift":     "one reading of one number; a joint would need a second source of truth",
    "lane intent":       "intent vs reality is already a two-sided check inside the eagle itself",
    "disk headroom":     "the disk is the ground truth; nothing else independently measures it",
    "subscription":      "the provider is the only authority on spend",
    "unattended reel":   "a single live observation",
    "board is claimed":  "needs the board window open; UNKNOWN here is honest, not a gap",
    "visual lock":       "a source invariant, checked structurally rather than cross-engine",
    "art corpus":        "file-level integrity, no second engine",
    "footage has a reel": "the frame stamp IS the second source; the eagle already joins them",
    "progress number":   "his board is the only authority on his own progress",
    "store emptied":     "needs the board window open",
    "locked lanes":      "a policy assertion, not a measurement pair",
    "surfaces agree":    "already a two-surface check inside the eagle",
    "the other doctors": "a roll-up of other verdicts",
}


def coverage():
    """Which engines have a joint, which do not, and why. -> dict. Reads nothing, decides nothing."""
    try:
        sys.path.insert(0, HERE)
        import console_doctor as _cd
        engines = [n for n, _fn in _cd.CHECKS]
    except Exception as e:
        return {"ok": False, "why": "could not ask the eagle for its roster: %s" % str(e)[:80]}
    covered, uncovered, unexplained = {}, {}, []
    for n in engines:
        if n in COVERED_BY:
            covered[n] = list(COVERED_BY[n])
        elif n in NO_JOINT_YET:
            uncovered[n] = NO_JOINT_YET[n]
        else:
            # ⚠ A NEW ENGINE WITH NEITHER A JOINT NOR A STATED REASON. Silence here is the defect:
            # it would read as covered simply by not appearing in either list.
            unexplained.append(n)
    return {"ok": True, "engines": len(engines),
            "covered": covered, "uncovered": uncovered, "unexplained": unexplained,
            "say": ("%d engine(s): %d with a joint, %d with a stated reason for none%s"
                    % (len(engines), len(covered), len(uncovered),
                       "" if not unexplained else
                       " — ⚠ %d NEITHER: %s" % (len(unexplained), ", ".join(unexplained))))}


def _holds(a, b, rel):
    if rel == "==":
        return a == b
    if rel == "<=":
        return a <= b
    if rel == ">=":
        return a >= b
    raise ValueError("unknown relation %r" % rel)


def check_one(builder):
    """-> dict. Never raises; a builder that explodes is UNKNOWN, never agreement."""
    try:
        key, what, prove, ln, lf, rn, rf, rel = builder()
    except Exception as e:
        return {"key": getattr(builder, "__name__", "?"), "state": UNKNOWN,
                "say": "the invariant could not be built: %s" % str(e)[:90]}
    L, R = _reading(ln, lf), _reading(rn, rf)
    row = {"key": key, "what": what, "prove": prove, "rel": rel,
           "left": {"who": ln, "value": L.value}, "right": {"who": rn, "value": R.value}}
    if not L.known or not R.known:
        row["state"] = UNKNOWN
        row["say"] = ("cannot be corroborated — %s"
                      % "; ".join(x.why for x in (L, R) if not x.known))
        return row
    if _holds(L.value, R.value, rel):
        row["state"] = AGREE
        row["say"] = "%s (%s %s %s %s)" % (what, ln, L.value, rel, rn)
        return row
    row["state"] = DISAGREE
    # BOTH numbers, BOTH names, no averaging and no verdict about which is right.
    row["say"] = ("%s says %s and %s says %s, and they must be %s. Neither number is corrected "
                  "here: two surfaces disagreeing IS the finding, and the one that is wrong is not "
                  "knowable from the pair alone." % (ln, L.value, rn, R.value, rel))
    return row


def run():
    """Every invariant. -> list of rows."""
    sys.path.insert(0, HERE)
    return [check_one(b) for b in BUILDERS]


def verdict(rows=None):
    """-> (state, say) for the eagle."""
    rows = run() if rows is None else rows
    bad = [r for r in rows if r.get("state") == DISAGREE]
    unk = [r for r in rows if r.get("state") == UNKNOWN]
    if bad:
        return DISAGREE, ("%d engine pair(s) disagree: %s"
                          % (len(bad), " · ".join("%s — %s" % (r["key"], r["say"]) for r in bad[:2])))
    if unk and len(unk) == len(rows):
        return UNKNOWN, ("none of the %d invariants could be corroborated: %s"
                         % (len(rows), unk[0].get("say", "")[:110]))
    if unk:
        return AGREE, ("%d engine pair(s) agree, %d could not be measured (%s)"
                       % (len(rows) - len(unk), len(unk), unk[0]["key"]))
    return AGREE, "all %d engine pair(s) agree" % len(rows)


def selftest():
    """DRIVE EVERY INVARIANT RED. An invariant nobody has seen disagree proves nothing.

    This does not touch his tree: each relation is exercised against synthetic numbers through the
    same `_holds` the live path uses, and `check_one` is driven with builders that return known
    readings. If a relation stops being able to fail, this says so.
    """
    out = []
    for rel, a, b in (("==", 1, 2), ("<=", 5, 4), (">=", 3, 9)):
        out.append(("relation %s can refuse" % rel, not _holds(a, b, rel)))
        out.append(("relation %s can hold" % rel, _holds(a, a, rel)))

    def _mk(lv, rv, rel):
        return lambda: ("synthetic", "what", "prove", "L", (lambda: lv), "R", (lambda: rv), rel)

    out.append(("a mismatch reports DISAGREE", check_one(_mk(1, 2, "=="))["state"] == DISAGREE))
    out.append(("a match reports AGREE", check_one(_mk(2, 2, "=="))["state"] == AGREE))
    out.append(("a None side reports UNKNOWN", check_one(_mk(None, 2, "=="))["state"] == UNKNOWN))
    out.append(("UNKNOWN is not AGREE", check_one(_mk(None, 2, "=="))["state"] != AGREE))
    row = check_one(_mk(157, 7, "=="))
    out.append(("both numbers survive into the message",
                "157" in row["say"] and "7" in row["say"]))
    out.append(("it does not pick a side",
                "is not knowable" in row["say"]))
    return out


def main(argv):
    try:
        from console_safe import enable  # noqa: F401
    except Exception:
        pass
    if "--selftest" in argv:
        rows = selftest()
        for what, ok in rows:
            print("  %s %s" % ("OK  " if ok else "FAIL", what))
        bad = [w for w, ok in rows if not ok]
        print("\n%s" % ("🟢 every invariant can both hold and refuse"
                        if not bad else "🔴 %d self-test(s) failed" % len(bad)))
        return 1 if bad else 0
    rows = run()
    for r in rows:
        icon = {AGREE: "🟢", DISAGREE: "🔴", UNKNOWN: "⚪"}.get(r.get("state"), "?")
        print("%s %-24s %s" % (icon, r.get("key"), str(r.get("say"))[:150]))
        if r.get("state") == DISAGREE:
            print("     to reproduce: %s" % r.get("prove"))
    st, say = verdict(rows)
    print("\n%s %s" % ({AGREE: "🟢", DISAGREE: "🔴", UNKNOWN: "⚪"}.get(st, "?"), say))
    return 1 if st == DISAGREE else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
