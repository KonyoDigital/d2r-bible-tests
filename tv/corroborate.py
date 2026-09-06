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
    """★ THE v2223 NEAR-MISS — AND FOR MONTHS THIS INVARIANT CORROBORATED A THING AGAINST ITSELF.

    MEASURED 2026-09-01 on his live tree, and it is the reason a whole pipeline stage had never
    run without anything noticing:

        the vault watchdog                       owed  0
        reel_retention (this check's old right)  owed  0        -> AGREE ✅ for months
        _vault_lane_owes(), asked per reel       owed 43        -> the truth

    BOTH OLD SIDES READ plan()'s TAGS, and plan() checks its rules IN ORDER with first-match-wins.
    `vault-owes` is 8th of 10; his 44 reels all match an earlier rule (test-fixture 15,
    zero-pages 24, recent 5), so `vault-owes` fires ZERO times. Two derivations of one broken
    source agreeing with each other is not corroboration — it is one number wearing two names.

    ⚠ AND THE OLD `prove` LINE NAMED THE FIX AS THE SABOTAGE: "make _vault_owed_reels ask its own
    question instead of retention's, and this parts". The author knew. It was written down as the
    way to BREAK the invariant rather than as the way to build it.

    WHAT IT COST: no vault sweep -> no seal -> 72.5% of his 6,380 frames held as "not sealed" ->
    0 frames prunable -> 7.4 GB of reels -> 7 GB free against an 8 GB floor -> CAPTURE BLOCKED.
    Every stage individually correct. [[feedback-contradiction-is-the-finding]] [[the-unjoined-end]]

    The right side is now an INDEPENDENT question — _vault_lane_owes asked of each reel directory
    on disk — which is what "corroborate" was supposed to mean. It reads no plan and no tag, so it
    cannot inherit the ordering that hid the work.
    """
    import control_app as ca
    import reel_retention as rr
    hist = os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")

    def left():
        got = ca._vault_owed_reels(hist)
        return None if got is None else len(got)

    def right():
        # ⚠⚠ THIS SIDE WAS _vault_lane_owes() AND THAT BECAME SELF-CORROBORATION THE MOMENT THE
        # JOINT WAS FIXED. v2391 made _vault_owed_reels ask _vault_lane_owes directly — correct,
        # and it meant BOTH sides of this invariant now ran the same predicate. The independence
        # audit added in v2390 caught it on the next self-test run, on the person who had just
        # written the audit. That is the machine working.
        #
        # So the right side is now a plain directory count: independent by construction, and
        # honest about being the WEAK half. It catches gross over-reach — a worklist larger than
        # the disk it was built from — and nothing subtler.
        #
        # THE STRONG HALF IS A SEPARATE CHECK. `vault-lane-has-worked` is what actually catches
        # the failure that hid here for months (a lane that never swept while work waited); this
        # `<=` cannot, because 0 <= anything holds. Two failures, two checks, neither pretending
        # to be the other. [[unknown-stays-unknown]]
        try:
            return len([d for d in os.listdir(hist) if d.startswith("reel_")])
        except OSError:
            return None

    return ("vault-worklist",
            "the vault watchdog never queues more reels than exist on disk",
            "have the worklist invent or duplicate a path and it exceeds the directory count",
            "the vault watchdog", left, "reel directories on disk", right, "<=")


def _inv_a_lane_that_is_ON_has_either_worked_or_says_why_not():
    """★ THE SHAPE THAT HID A WHOLE PIPELINE STAGE, AND THE ONE `<=` CANNOT CATCH.

    Konyo: "how do we find these before i tell you about them?" — after the vault lane was found
    to have run every 45 seconds since it was built without ever sweeping anything.

    The vault-worklist invariant caught it ONCE, at `==` (0 vs 43). It is now `<=`, because after
    the fix the worklist legitimately narrows (owed AND unsealed = 35 of 43 owed) — and `0 <= 43`
    HOLDS. The relation that catches over-reach cannot catch emptiness. They are two failures and
    they need two checks.

    THE GENERAL RULE, worth more than this one lane: A LANE THAT IS ON AND HAS NEVER COMPLETED A
    SINGLE UNIT OF WORK IS EITHER UNNECESSARY OR BROKEN, AND IT MUST SAY WHICH. Reporting
    {on: True, reads: 0, lastTs: None, owed: 0} forever is not a status — it is the absence of
    one, and it reads identically to a lane with nothing to do.
    [[unknown-stays-unknown]] [[the-unjoined-end]]

    Left is what the lane has DONE; right is whether there is anything to do. A lane that has done
    nothing is fine only while the worklist is empty too.
    """
    import control_app as ca

    def left():
        # 1 if the lane has ever completed a read, else 0. lastTs is the durable tell — `reads`
        # is a process-local counter and resets on every restart.
        try:
            st = ca._vault_autoread_state() or {}
        except Exception:
            return None                       # could not ask -> UNKNOWN, never "it has worked"
        if not st:
            return None
        return 1 if (st.get("lastTs") or (st.get("reads") or 0) > 0) else 0

    def right():
        # 1 if there is work waiting, else 0. UNKNOWN stays UNKNOWN.
        w = ca._vault_owed_reels()
        if w is None:
            return None
        return 1 if len(w) > 0 else 0

    return ("vault-lane-has-worked",
            "a vault lane that has never swept anything is only acceptable while nothing is owed",
            "empty the worklist while the lane still reports work and this parts 0 vs 1",
            "the lane has ever swept", left, "there is work owed", right, ">=")


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
        # ⚠ v2393 — THE THIRD SITE OF THE SAME PROSE MATCH, AND IT WAS IN THE CORROBORATOR.
        # v2392 fixed one, a cross-family review found the second, and sweeping the class for the
        # second found this one — inside the module whose entire job is catching this. An
        # instrument built out of the defect it grades is the sharpest version of
        # [[feedback-suspect-the-instrument]]. Match the tag reel_retention._rule() writes.
        return len([k for k in (p.get("kept") or [])
                    if k.get("tag") == "never-chronicle-swept"])

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
            # ⚠⚠ THE KEY IS `prunable`, AND ASKING FOR THE WRONG ONE MADE THIS INVARIANT INERT.
            # It asked for "free" or "freeable"; `frame_authority.plan_frames` returns neither —
            # its keys are bytes/haveIndex/heldBy/kept/prunable/say/scanned/sealOk/sealedSessions/
            # witnessFrames/witnessOk. So `.get()` fell through to `[]` and this side answered 0
            # FOREVER, on every tree, whatever the deleter did. An invariant whose left side is a
            # constant zero cannot be violated, so it has never once been able to fire — and it
            # guards the DIRECTION WITH NO UNDO. A guard that cannot go red is measuring nothing.
            # ⚠ It REFUSES rather than defaulting when the key is absent: a missing `prunable` is
            # an unreadable plan, not an empty one, and answering 0 there is how this hid.
            # [[unknown-stays-unknown]] [[feedback-blind-fixture-green-gate]]
            if "prunable" not in plan:
                return None
            return len(plan.get("prunable") or [])
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
            # ⚠ SAME DEFECT, SECOND SITE — see the note above. Both invariants asked for a key
            # `plan_frames` has never returned, so both left sides were a constant 0.
            if "prunable" not in plan:
                return None
            return len(plan.get("prunable") or [])
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


def _inv_the_fleet_divides_by_the_same_number_the_board_does():
    """v2717 — THE FLEET AND THE BOARD'S OWN TABS PUBLISHED DIFFERENT UNIQUES, AND HE SAW IT.

    Konyo, 2026-09-06: *"no reason for it to render something in the roster or fleet different from
    the consoles main tabs Uniques/Sets/runewords"*. Measured on his live console, GET /api/fleet,
    twice six minutes apart on the SAME machine:

        10:33:26   uniques {have: 169, total: 398}
        10:39:39   uniques {have: 292, total: 403}
        the board's own Chronicle meter:  258 / 403

    ⚠ NEITHER SIDE WAS BROKEN. They were two coherent measures wearing one label: the fleet
    published `d2r_owned.length / _gUniqueRoster().length` (vault over vault roster, 398 — which
    keeps both spellings of all six sunders on purpose since v2685), while the tabs showed
    `funiScan().found / chronTotal` (chronicle over the pinned game count, 403). Two questions, one
    word. [[label-outlived-referent]] [[zero-needs-a-denominator]]

    ⚠⚠ AND v2714 DID NOT FIX IT. That ship unified NINE call sites inside bible.html and shipped
    believing the job done; the fleet's number is built in control_app.py, which it never touched.
    A read-only agent traced it afterwards. THIS invariant is the thing that would have said so —
    the reason it exists is that a fix was believed rather than corroborated.

    INDEPENDENCE, which is the whole point of living here: the left side is a LIVE read (the
    console asking the running board for its counts); the right side is a SOURCE PARSE of the
    pinned constant in bible.html. Neither can inherit the other's answer — one is a browser eval,
    the other is a regex over a file on disk. That distinction is what [[feedback-verify-not-proxy]]
    means, and the audit added in v2390 exists because a previous invariant quietly lost it.

    HONEST-ABSENT: a console that cannot be asked, or a board that cannot say, returns None on the
    left and the invariant reports UNMEASURED rather than a pass. A guest world, an unclaimed
    board, a console that is down — none of those are evidence of agreement.
    """
    import re as _re

    def left():
        """The denominator in the BANKED tally on disk — the row the beacon actually publishes.

        ⚠⚠ THIS WAS `ca.grail_tally()` AND IT WAS VACUOUS. Out of process there is no board window,
        so `board_ownership()` fails and grail_tally falls straight through to the disk bank — the
        very file the right side would then be compared against. MEASURED: sabotaging the live
        eval path (putting the fleet back on the vault roster) left this invariant GREEN, because
        `left()` never reached that code at all. The sabotage pass caught it, on the person who had
        just written it, which is the second time this file has caught its own author.
        [[feedback-suspect-the-instrument]]

        So it reads the BANK, which is a real artifact with a real denominator, and the sabotage
        below can move it. The live-eval path is a CODE law and lives in a unit test where it can
        actually be graded, not here where the process cannot reach it.
        """
        try:
            p = os.path.join(HERE, "board_tally.json")
            d = json.load(io.open(p, encoding="utf-8"))
            # ⚠ AND THE SHAPE WAS NOT WHAT I ASSUMED EITHER. board_tally.json is not a map of
            # routes — it carries `uniques`/`sets`/`runewords` at the TOP level (the headline the
            # beacon publishes) plus `byRoute` and `high` maps beneath. My first cut walked
            # d.values() expecting per-route dicts, hit an int, and returned UNKNOWN on a perfectly
            # readable file. Measured before fixing: top-level uniques = {"have":292,"total":403}.
            u = d.get("uniques") if isinstance(d, dict) else None
            n = (u or {}).get("total") if isinstance(u, dict) else None
            return int(n) if isinstance(n, int) and n > 0 else None
        except Exception:
            return None

    def right():
        """The PINNED chronicle total, read from bible.html's source. Never from the console."""
        try:
            p = os.path.join(os.path.dirname(HERE), "bible.html")
            src = io.open(p, encoding="utf-8").read()
            hits = sorted({int(m) for m in _re.findall(r"chronTotal\s*:\s*(\d+)", src)})
            # more than one pinned value is not a denominator, it is a disagreement
            return hits[0] if len(hits) == 1 else None
        except Exception:
            return None

    return ("fleet-divides-by-the-board's-number",
            "the fleet's uniques denominator is the board's own pinned chronicle total",
            "let the fleet publish the vault roster (398) while the tabs divide by chronTotal "
            "(403) and this parts — which is exactly what he was looking at",
            "the banked board_tally denominator (disk)", left,
            "chronTotal pinned in bible.html (source)", right, "==")


def _inv_the_deleter_releases_only_what_the_store_declares():
    """v2720 — THE DECIDER MUST NEVER RELEASE MORE SEALS THAN THE STORE ACTUALLY DECLARES.

    His ruling, 2026-09-06: an examined-empty reel *"can continue down the river to tombstone...
    and delete"* — **"as long as its ledgered and extracted properly and tallied where needed"**.
    A conditional yes. This is the invariant that keeps the condition attached to it.

    ⚠⚠ WHY IT EXISTS AT ALL, MEASURED. `seal_verdict` scores a seal EMPTY when `examinedEmpty` is
    set OR when `extractedWhy` merely contains the word "nothing". Across his 31 real seals that is
    23 EMPTY — but only 17 declared `examinedEmpty`; the other 6 qualify on the string alone, and
    their why is literally "nothing was taken", which is the DEFAULT branch of `_seal_extracted`
    for any sweep that grounded no rows. Wiring `!= UNEVIDENCED` into the deleter would have
    released six reels on a substring. The looser read is CORRECT for a report and WRONG for a
    deletion, and nothing but this invariant keeps the two apart over time.

    INDEPENDENCE, which is the whole point of living here: the LEFT side runs the predicate the
    deleter actually calls; the RIGHT side counts declarations straight out of the seal JSON,
    touching no frame_authority logic at all. A drift in the predicate cannot move the right side,
    which is exactly the property the v2390 audit exists to protect.

    RELATION IS `<=`, NOT `==`, AND THAT IS DELIBERATE. The deleter may be STRICTER than the store
    (it also demands a readable seal, and `rows == 0` before it will call a thing empty). It may
    never be LOOSER. An equality here would go red for a safe reason and teach us to ignore it.
    [[unknown-stays-unknown]] [[join-gate-heart]]
    """
    def left():
        """How many seals the DELETION-side predicate would release."""
        try:
            import frame_authority as FA
            sealed, ok = FA.sealed_sessions()
            if not ok or not isinstance(sealed, dict) or not sealed:
                return None            # nothing examined names nothing
            return sum(1 for r in sealed.values() if FA.seal_releases_frames(r)[0])
        except Exception:
            return None

    def right():
        """How many seals DECLARE a releasable state, read straight from the store."""
        try:
            import frame_authority as FA
            contract = set(FA.EXTRACTION_CONTRACT)
            sealed, ok = FA.sealed_sessions()
            if not ok or not isinstance(sealed, dict) or not sealed:
                return None
            n = 0
            for r in sealed.values():
                if not isinstance(r, dict):
                    continue
                got = r.get("extracted")
                covered = isinstance(got, (list, tuple, set)) and contract <= {str(x) for x in got}
                if covered or r.get("examinedEmpty") is True:
                    n += 1
            return n
        except Exception:
            return None

    return ("deleter-releases-only-what-is-declared",
            "the deleter releases no more seals than the store actually declares releasable",
            "let EMPTY-by-substring reach the deleter and this parts — 23 released against 17 "
            "declared, six of them on the words 'nothing was taken'",
            "seal_releases_frames over his seals", left,
            "seals declaring the contract or examinedEmpty (raw JSON)", right, "<=")


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


#: v2394 — how old the eagle's durable pass may be and still mean something. The loop runs every
#: few minutes; an hour is generous and still refuses a record from yesterday. [[stale-reading]]
_EAGLE_RECORD_MAX_AGE_MS = 60 * 60 * 1000
#: the canonical console port. ⚠ A SECOND COPY OF A CONSTANT IS A THING THAT CAN DRIFT — the cold
#: review flagged control_app's own `_PRIMARY_CONTROL_PORT = 17772` as already duplicating
#: TV_CONTROL_PORT's fallback. So this reads control_app's value and only falls back to the literal
#: when the module cannot be imported at all (a gate on a machine without it).
try:
    import control_app as _ca_for_port
    _PRIMARY_PORT = int(getattr(_ca_for_port, "_PRIMARY_CONTROL_PORT", 17772))
except Exception:
    _PRIMARY_PORT = 17772

#: The durable pass. A MODULE CONSTANT so a test can point it somewhere harmless.
#: ⚠ THE FIRST CUT HARDCODED THIS PATH AND THE GUARD RACED HIS RUNNING CONSOLE. The live console
#: rewrites this file on every eagle pass; a test that wrote it, asserted, and restored it was
#: fighting a process that writes every few minutes — three of my own guards failed on the push
#: for exactly that. A test must never read or write a file the product is actively writing.
#: [[feedback-fixtures-never-touch-live-data]]
def _eagle_record_path():
    """Where the PRIMARY console's durable pass lives.

    ⚠ ASK THE WRITER RATHER THAN RE-DERIVING, BECAUSE THE TWO DERIVATIONS HAD ALREADY SPLIT. This
    computed `dirname(control_app.__file__)` while v2411 moved the writer onto `_decision_path`,
    whose directory comes from `_chron_swept_path()`. On his machine those resolve to the same
    folder, which is exactly why nothing noticed — but they are two different rules, and under a
    redirected state directory (any test, any packaged run) they genuinely diverge. A cold review
    named it; the join test then reproduced it, writer landing in a temp state dir while the reader
    looked beside the module.

    Two paths computed two ways is [[copy-drift]] with a filename instead of a function. Ask the
    owner. The fallback stays for a process that cannot import control_app at all — a gate on a
    machine without it — where UNKNOWN is the honest answer anyway.

    ⚠ ALWAYS THE PRIMARY'S PATH, never this process's own. A scratch console reading the record
    should read the record the CONSOLE wrote, not its own; asking `_decision_path` from inside a
    scratch would silently retarget the reader to the scratch's file and re-create the very
    self-agreement v2411 removed."""
    # ⚠ THE FALLBACK MUST FIRE ONLY WHEN control_app IS GENUINELY ABSENT. A first cut wrapped the
    # whole thing in `except Exception: pass` and fell through to `dirname(__file__)` — so if
    # `_chron_swept_path()` raised for any reason the reader would SILENTLY REVERT to the old rule
    # while the writer kept using the redirected one, re-creating the split this function exists to
    # close, invisibly. That is the same broad-catch mislabel being removed from the render gate in
    # the same ship. A cold review caught both.
    # ⚠ ImportError, NOT Exception. A cold review: catching Exception here means a BROKEN
    # control_app — a syntax error, a circular import — also falls back to this module's own
    # directory, which in this tree is the same `tv/`. Under a redirected TV_HIST that is the
    # writer/reader split all over again, just narrowed to the case where the import fails.
    try:
        import control_app as _ca
    except ImportError:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), ".eagle_last.json")
    # ⚠ AND A CORRECTION TO MY OWN COMMENT, which said an unguarded raise here "must surface".
    # It does not. The only production caller is _durable_pass, which ends `except Exception:
    # return (None, None)` — so a raise becomes UNKNOWN, silent about its cause. That is still the
    # right OUTCOME (no row count and no wrong file, rather than a confident read of the wrong
    # one), but the comment claimed something the code does not do, which is the defect I spent
    # this evening finding in my own commit messages.
    base = _ca._chron_swept_path()
    return os.path.join(os.path.dirname(os.path.abspath(base)), ".eagle_last.json")


def _durable_pass(max_age_ms=None):
    """The last durable eagle pass as ONE snapshot. -> (rows, slow) with either possibly None.

    ⚠ ONE READ, ONE POLICY, BECAUSE TWO READERS OF ONE RECORD IS HOW THIS BROKE TWICE. v2407 had
    `left()` reading rows here under freshness + author rules while a separate `_durable_slow_flag`
    read `slow` from the same file under NO rules — its docstring claimed "same file and freshness
    rules as the row count it accompanies" and it checked neither `ts` nor `port`. Two readers of
    one record with two policies is the same shape as the mixed-source bug it was written to fix,
    one level down; a cold review caught the docstring lying before it cost anything.

    Every refusal below returns (None, None): the pass is UNREADABLE, and reporting a row count
    without knowing which roster it was measured against is worse than reporting nothing.
    """
    try:
        import json as _json, os as _os, time as _time
        _p = _eagle_record_path()
        if not _os.path.isfile(_p):
            return (None, None)
        with io.open(_p, encoding="utf-8") as _fh:
            _row = _json.load(_fh)
        _ts = _row.get("ts")
        if not isinstance(_ts, (int, float)):
            return (None, None)
        cap = _EAGLE_RECORD_MAX_AGE_MS if max_age_ms is None else max_age_ms
        if (_time.time() * 1000 - float(_ts)) > cap:
            return (None, None)            # too old to mean anything
        # ⚠ v2409 — ASK WHETHER IT WAS THE PRIMARY CONSOLE, NOT WHETHER IT HAD A PORT.
        # v2408 refused a record whose port was None, reasoning that a portless process has no
        # window. Grok Bot then named the actual stray: `control_app.py --no-open` on **:17985** —
        # windowless, but serving. It writes port=17985 and would have sailed straight past that
        # check, so the guard was inert on the one case that produced it. A guard that cannot fail
        # on its own motivating example is measuring nothing. [[feedback-blind-fixture-green-gate]]
        #
        # `primary` comes from _is_primary_console(): only the canonical :17772 console is the one
        # anyone is asking about. Port is still recorded, for diagnosis rather than for judgement.
        #
        # ⚠ ABSENT IS NOT False. A pre-v2409 record carries no `primary` key at all and must still
        # be read, or upgrading blinds this on every machine until each rewrites its file.
        if _row.get("primary") is False:
            return (None, None)
        # ⚠ THE COMPATIBILITY HOLE THE COLD REVIEW FOUND, AND IT WAS THE ONE CASE THAT MATTERS.
        # A pre-v2409 record carries no `primary` key and is deliberately still read — but the
        # record an OLD SCRATCH actually produces is `{port: 17985}` with no `primary`, which sailed
        # straight through. The suite covered `{port: 17772}` with no primary and `{port: 17985,
        # primary: false}`, and missed exactly the combination a live older scratch writes.
        # `port` was already stamped by the previous writer, so it closes the hole without blinding
        # a genuinely keyless file.
        if _row.get("primary") is None and isinstance(_row.get("port"), int) \
                and _row.get("port") != _PRIMARY_PORT:
            return (None, None)
        if "port" in _row and _row.get("port") is None:
            return (None, None)
        _r = _row.get("rows")
        _s = _row.get("slow")
        return (int(_r) if isinstance(_r, int) else None,
                bool(_s) if isinstance(_s, bool) else None)
    except Exception:
        return (None, None)


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
            # ══ v2394 — READ THE DURABLE PASS, BECAUSE _EAGLE IS A MODULE GLOBAL ═════════════
            # Konyo: "the_eagle_can_still_look = UNKNOWN... no gaps... information is needed
            # obviously, so connect it to the heart of the console too."
            #
            # `_EAGLE` lives in the CONSOLE'S process. Everywhere else — this CLI, a gate, CI —
            # the module is fresh and `checked` is None, so the one invariant that watches the
            # watchdog could only ever be graded inside the thing it grades. v2394 makes
            # _eagle_once persist {checked, rows, ts}; this reads it.
            #
            # ⚠ STALE IS NOT FRESH, AND IT IS NOT A PASS EITHER. A pass from three days ago is
            # not evidence the eagle flew today, so a record older than the bound answers
            # UNKNOWN — the same answer as no record at all, which is the honest one.
            # [[stale-reading]] [[unknown-stays-unknown]]
            # ⚠ ONE READ FOR BOTH SIDES — see _durable_pass. This branch used to inline its own
            # loader while `slow` was read by a second function with different rules.
            return _durable_pass()[0]
        rows = e.get("rows")
        return len(rows) if isinstance(rows, list) else None

    def right():
        """The checks the eagle ACTUALLY RUNS — which is not the whole roster.

        ⚠ THIS RETURNED len(cd.CHECKS) AND THE INVARIANT COULD THEREFORE NEVER BE SATISFIED. The
        eagle calls `run(include_slow=False)` (control_app.py:14601) and `run` skips any name in
        `SLOW`, so it emits len(CHECKS) - len(SLOW) rows by design. Measured on his live console
        2026-09-01: 32 rows against a roster of 34, flagged as an engine pair disagreeing, when
        34 - 2 = 32 is exactly right. The two are `sweep would find` and `the other doctors`.

        He photographed the panel and asked what it meant. A corroborator comparing a filtered
        count against an unfiltered one is not detecting drift, it is reporting its own filter —
        and it had presumably been red since SLOW was introduced. A permanently-red alarm is worse
        than no alarm: it teaches the eye to skip the row, and then the row that MATTERS gets
        skipped with it. [[feedback-suspect-the-instrument]] [[label-outlived-referent]]

        ⚠ DERIVED FROM THE SAME CONSTANTS THE RUNNER USES, never a hardcoded 32. Adding a check
        must move this number automatically; pinning the literal would rot on the next check and
        reintroduce the identical defect one roster entry later. [[regression-guard]]
        """
        import console_doctor as cd
        full = len(cd.CHECKS)
        cheap = len([c for c in cd.CHECKS if c[0] not in cd.SLOW])
        # ⚠ THE EXPECTATION DEPENDS ON WHICH PASS RAN, AND MY FIRST FIX HARDCODED ONE OF THEM.
        # Returning `cheap` unconditionally traded a permanently-red alarm for one that goes red
        # whenever a COMPLETE pass runs — the suite caught it immediately
        # (test_an_eagle_that_flew_EVERY_check_agrees drives 34 rows and expects agreement).
        # v2407 makes the eagle RECORD `slow`, so this asks instead of assuming.
        #
        # ⚠ AND THE DEFAULT WHEN THE FLAG IS ABSENT IS `full`, DELIBERATELY. An old record, or a
        # caller that never set it, must not be silently reinterpreted as a cheap pass — that
        # would make a genuinely incomplete pass of 32 rows read as healthy, which is the exact
        # blindness this invariant exists to prevent. Defaulting to the STRICTER expectation means
        # an unlabelled pass can still be caught skipping checks. [[unknown-stays-unknown]]
        #
        # ⚠⚠ AND THE FLAG MUST COME FROM THE SAME PASS AS THE ROWS. The first cut read the flag
        # from the DURABLE record while left() was counting rows from the IN-MEMORY _EAGLE — so a
        # fixture's 34 rows got graded against his live console's `slow: False`, and the suite
        # failed with `34 != 32` for a reason that had nothing to do with either. Two halves of one
        # comparison sourced from two different passes is not a comparison at all, and it made the
        # test's verdict depend on the machine it ran on. left() decides which record it is reading
        # by asking whether `checked` is set; this mirrors that decision exactly rather than
        # guessing again. [[feedback-fixtures-never-touch-live-data]] [[copy-drift]]
        e = dict(getattr(ca, "_EAGLE", {}) or {})
        slow = e.get("slow") if e.get("checked") is not None else _durable_pass()[1]
        if slow is False:
            return cheap
        if slow is True:
            return full
        # ⚠⚠ AN UNLABELLED PASS IS UNKNOWN, NOT "ASSUME THE WHOLE ROSTER" — AND MY DEFENCE OF THE
        # STRICT DEFAULT WAS WRONG ON ITS OWN TERMS. I argued that defaulting to `full` keeps a
        # skipped check catchable. It does not: a skip is caught by a LABELLED cheap pass reporting
        # 31 against 32. The default fires only in the UNLABELLED case — where it reports 32
        # against 34, which is precisely the permanently-red row he photographed, back under
        # different arithmetic.
        #
        # A cold cross-family read put it exactly right: "it protects against a store nobody
        # writes, and alarms on the store everybody writes." Confirmed — nothing in production
        # RECORDS a complete pass. control_app.py:23398 runs one for an API response and never
        # touches _EAGLE or the durable file, so `full` was reachable only through this default.
        #
        # The engine already grades a None side as UNKNOWN, symmetrically with left(). Not knowing
        # which roster a pass was measured against is a fact about the record, and reporting a
        # count against a roster nobody chose is an expectation with no author.
        # [[unknown-stays-unknown]] [[label-outlived-referent]]
        return None

    return ("eagle-ran-every-check",
            "the eagle's last pass covered every check it actually runs (the roster minus SLOW)",
            "drop a check from the loop and its row stops appearing while the roster still lists it",
            # ⚠ THE NAME MUST NOT ASSERT A BRANCH IT CANNOT KNOW. It read "checks the eagle runs
            # (roster minus SLOW)" while right() may legitimately return the FULL roster — so a
            # human reading `34` under a label saying "minus SLOW" correctly works out that the
            # instrument is wrong, and no action follows. The tuple is static, so the name must be
            # true in every branch. [[label-outlived-referent]]
            "rows in the last eagle pass", left,
            "rows that pass was expected to cover", right, "==")


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


def _inv_the_console_and_the_law_agree_about_furniture():
    """v2319 — the console's own furniture verdict against the shared law it now delegates to.

    Konyo: "these are locked inventory items within the inventory template thats a LAW ... make
    this also a unified logic within the ai readers and console. it needs a hardcode logic."

    The law WAS already encoded three times — control_app._REGISTER_ANCHORS, vault_corpus's FIXED
    cells, and the live prompt's prose — and the retro readers could see none of them. Now there is
    one module and the console asks it. This pair fails the moment those two answers part, in
    either direction: a console that stops recognising the cube, or a law that starts calling loot
    furniture. [[copy-drift]]
    """
    import control_app as ca
    import inventory_law as il

    NAMES = ("Horadric Cube", "Tome of Identify", "Tome of Town Portal", "Wirt's Leg")

    def left():
        return sum(1 for n in NAMES if ca._register_is_anchor(n.lower()))

    def right():
        return sum(1 for n in NAMES if il.is_locked(n))

    return ("furniture-law-agrees",
            "the console and the shared inventory law name the same items as furniture",
            "drop one from inventory_law.LOCKED and this parts 4 vs 3",
            "console anchors", left, "the shared law", right, "==")


def _inv_the_tooltip_finder_refuses_more_than_it_finds():
    """v2321 — a finder that never refuses is not finding, it is guessing.

    Text density alone locates the HUD: on a reel that registered nothing it returned the same
    (2450, 0, 490, 318) corner box on five consecutive frames. The 8% area floor is what separates
    a real tooltip (33.4% of the frame) from that impostor (2.8%), and the tell that the floor is
    still doing its job is that REFUSALS outnumber LOCATIONS — most frames in a reel have no
    tooltip on them, because he is walking, fighting and looting between hovers.

    If locations ever outnumber refusals, either the floor has been lowered or he has started
    hovering on every single frame. The first is a defect and the second has never happened.
    """
    import tooltip_find as tf

    def left():
        return int((tf.report() or {}).get("refused") or 0)

    def right():
        return int((tf.report() or {}).get("located") or 0)

    return ("tooltip-finder-refuses",
            "the tooltip finder still refuses more frames than it claims (most frames have no tooltip)",
            "drop _MIN_AREA_FRAC and the HUD box starts counting as a tooltip on every frame",
            "frames refused", left, "tooltips located", right, ">=")


#: v2434 — INVARIANTS DELIBERATELY NOT IN BUILDERS, each with the reason it is not run.
#: ⚠ THIS EXISTS BECAUSE THE TWO REGISTRIES DISAGREED BY ONE AND NOTHING SAID SO.
#: `run()` / `verdict()` / the eagle iterate BUILDERS. `prove_each()` (:1017) and the independence
#: audit (:1116) enumerate `sorted(n for n in globals() if n.startswith("_inv_"))` instead. Those
#: two rosters are not the same roster, and for the whole life of this file they have differed by
#: `_inv_the_deleter_is_never_looser_than_the_planner` — graded by the self-proving surface as
#: proven=True, and never once evaluated by the live path. `git log -S` finds no commit that ever
#: added it to BUILDERS, so it has never run.
#: A surface that reports on an invariant the engine cannot run is the shape this whole module
#: exists to catch, one level up from the invariants themselves. Declaring it is not a fix for the
#: invariant; it is what stops the DIVERGENCE being silent. The selftest below now refuses any
#: `_inv_*` that is in neither list. [[the-unjoined-end]] [[unknown-stays-unknown]]
RETIRED = {
    "_inv_the_deleter_is_never_looser_than_the_planner":
        "superseded in practice by `frame-deleter-not-looser` (:401), which asks the same question "
        "-- the frame deleter must never free more than the reel planner offers -- against "
        "frame_authority.free vs retention.candidate pages. This earlier version was never "
        "registered. It is kept, not deleted, because its docstring records the 2026-08-30 "
        "disagreement between reel_retention and frame_authority and why the strict one was RIGHT "
        "to hold; that reasoning is worth more than the function. If it should run, move it into "
        "BUILDERS and delete this entry -- do not leave it in both.",
}

def _inv_every_door_counts_the_reels_it_opened():
    """v2687 — THE PARENT'S COUNTER vs THE CHILD'S STAMP. Two witnesses to one event.

    The defect this is written from: v2316 gave each capture door a Wilson score, and only
    `shadow` ever passed opened=True. Measured on his live ledger 2026-09-05 —

        shadow  opened=609  filmed=181        onair  opened=0        mini  opened=0

    — while ON AIR and MINI had been filming reels the whole time. Nothing reported it, and the
    report itself was HONEST: `wilson: null`, "no sealed reel from this door yet — nothing has been
    proved either way". Every word true. A broken counter and a door nobody pressed are the same
    sentence, and only a SECOND witness can tell them apart. [[zero-needs-a-denominator]]

    The second witness is the journal. Since v2687 the agent stamps `door` onto every row it
    writes, so the reels are counted twice by parties that do not talk to each other: the parent
    increments a counter at spawn, the child writes a name into its own file.

    NOT equality — CONTAINMENT, and the direction is the point. A reel can open and write nothing
    (a near-black shadow reel does exactly that, 263 of them), so the journal can only ever hold a
    SUBSET of what the doors opened. If the journal ever shows MORE door-stamped sessions than the
    doors admit opening, a counter is not being incremented — which is the original bug, and it is
    the only direction that can catch it.

    ⚠ PRE-v2687 REELS CARRY NO STAMP AND MUST NOT BE COUNTED. They are not evidence of a missing
    increment; they are evidence of nothing, and forging a door for them is the exact lie the
    stamp's own guard refuses. An unstamped reel is UNKNOWN. [[unknown-stays-unknown]]
    """
    import control_app as ca

    def left():
        """Distinct sessions the AGENT stamped with a door — the child's testimony."""
        try:
            import reel_templates as rt
            by, why = rt._journal_rows()
            if why:
                return None
            return len({sid for sid, rows in (by or {}).items()
                        if any(str((r or {}).get("door") or "").strip() for r in (rows or []))})
        except Exception:
            return None

    def right():
        """Opens claimed by the doors — the parent's testimony."""
        try:
            rep = ca.capture_door_report() or {}
            tot = 0
            for _d, row in rep.items():
                n = (row or {}).get("opened")
                if not isinstance(n, int):
                    return None
                tot += n
            return tot
        except Exception:
            return None

    return ("door-opens-are-counted",
            "no more door-stamped sessions in the journal than the doors admit opening",
            "stop passing opened=True in start_agent and film a reel: the journal gains a stamped "
            "session while the ledger's total stands still, and these part",
            "journal sessions carrying a door", left, "ledger opened (all doors)", right, "<=")


def _inv_only_a_declared_owner_world_posts_owner_numbers():
    """v2695 — WOULD HAVE FLAGGED HIS COUSIN'S BOARD THE DAY IT HAPPENED.

    Konyo: "this should be or have been connected to the heart of the console so regression for
    this.. or it suddenly not cross referencing should and could have been flagged?" He is right,
    and the two witnesses were already on disk.

    THE DEFECT IT WATCHES. bible.html carries `_GRAIL_SEED` (245 of HIS dated finds) and applies it
    to any board that resolves as OWNER. `_isCousinShell` is only `!_D2R_OWNER`, so pressing "claim
    this browser" flipped a stranger into the owner world and handed him another man's chronicle —
    his cousin Dean's Uniques tab read 243/403 of items he has never held. Fixed in v2692 by giving
    the seeds a named ledger; this is the alarm that says if it ever comes back.

    THE TWO WITNESSES, and they do not talk to each other:
      LEFT   `byRoute` — every route that actually POSTED a tally, each stamped with its install id
             and its namespace prefix. An owner-namespace post carries pfx ''.
      RIGHT  `ownerWorlds` — the worlds the console DECLARES are his.
    An install that posts owner numbers while not being a declared owner world is a stranger inside
    the owner namespace. That is the leak, stated as arithmetic.

    MEASURED on his tree when this was written: 404 routes — 401 guests, every one reading
    uniques.have 0 (the per-install ledger works and has never leaked to a guest), and 3 owner-pfx
    routes: 77f64154 (292/123/99), c5c2c92d (280/120/99) and one null-id bootstrap row. Both real
    ids are in ownerWorlds, so this holds at 0 today.

    ⚠ CONTAINMENT, NOT EQUALITY, and the direction is the point: undeclared-owner-posts <= 0. A
    world can be declared and never post (he has two and one is stale); the reverse — posting
    owner numbers without being declared — is the only direction that can be a leak.
    ⚠ THE NULL-ID ROW IS NOT A VIOLATION. It carries no install id at all, so it names nobody and
    cannot be a stranger; counting it would make this red forever over a bootstrap artifact.
    [[unknown-stays-unknown]]
    """
    import json as _json
    import os as _os

    def _tally():
        try:
            with open(_os.path.join(HERE, "board_tally.json"), encoding="utf-8") as fh:
                return _json.load(fh) or {}
        except Exception:
            return None

    def left():
        """Install ids that POSTED owner-namespace numbers and are NOT declared owner worlds."""
        d = _tally()
        if d is None:
            return None
        declared = set()
        for w in (d.get("ownerWorlds") or []):
            declared.add(str(w).split("|")[0])
        oid = d.get("ownerId")
        if oid:
            declared.add(str(oid))
        # ⚠⚠ v2703 — AN EMPTY ROSTER IS UNKNOWN, NOT A LEAK. `_tally()` returns None only when the
        # file is missing or will not parse. A tally written mid-update, or by a version that has
        # not yet populated ownerWorlds, parses fine and yields declared == set() — and then EVERY
        # owner-namespace route lands in `bad`. Measured on his real tally: ownerWorlds holds 2 and
        # ownerId is set, so this is LATENT today, not firing. But a reader failure must never
        # manufacture a red; the honest answer when nothing is declared is that nobody can say.
        if not declared:
            return None
        bad = set()
        for v in (d.get("byRoute") or {}).values():
            r = (v or {}).get("route") or {}
            # ⚠⚠ v2703 — A MISSING `pfx` IS UNKNOWN, NOT AN ASSERTION OF THE OWNER NAMESPACE.
            # This read `if r.get("pfx"): continue`, so an ABSENT key is falsy and fell through to
            # be judged as an owner-namespace post. Two lines below, an absent `id` is explicitly
            # treated as UNKNOWN with a comment citing unknown-stays-unknown by name — the same
            # file giving absent evidence opposite meanings depending on which field is missing.
            # Measured on his tally: 404 byRoute rows, 401 carry a truthy pfx, exactly ONE has no
            # pfx key at all, and that row also has no id, so the guard below catches it first.
            # LATENT today; it fires the moment a row lands with an id and no pfx.
            if "pfx" not in r:
                continue                      # nobody recorded a namespace; that names nobody
            if r.get("pfx"):
                continue                      # a guest route — its own namespace, not the owner's
            rid = r.get("id")
            if not rid:
                continue                      # no id names nobody; see the note above
            if str(rid) not in declared:
                bad.add(str(rid))
        return len(bad)

    def right():
        d = _tally()
        if d is None:
            return None
        declared = set(str(w).split("|")[0] for w in (d.get("ownerWorlds") or []))
        if d.get("ownerId"):
            declared.add(str(d.get("ownerId")))
        return None if not declared else 0

    return ("owner-namespace-is-declared",
            "no install posts owner-namespace numbers without being a declared owner world",
            "claim a fresh browser, let it post a tally, and its id appears with pfx '' while "
            "ownerWorlds still lists only his — these part",
            "undeclared installs posting owner numbers", left, "the allowed number of them", right,
            "<=")


def _inv_every_rung_the_shelf_declares_is_one_the_funnel_can_ACCOUNT_FOR():
    """v2725 — THE RUNG VOCABULARY HAS TWO OWNERS, AND ONLY ONE OF THEM KNOWS IT.

    `reel_story.STAGES` is the ladder a reel climbs. `one_funnel` reports, per rung, how a reel's
    passage is observed — from a CACHE (`WAYPOINT_SOURCES`) or from a LIVE DECIDER
    (`DERIVED_SOURCES`, added v2725). Nothing made the second list follow the first.

    THE FAILURE THIS CATCHES, and it is not hypothetical: reel_story's own module docstring
    already names a SEVENTH stage that STAGES does not yet carry —

        PRUNED   gone, tombstoned   reel_retention._tombstone

    The day that lands in STAGES, one_funnel gains a rung it has never been taught about. It would
    not crash and it would not go red. `_store_of` would answer "no store records this rung",
    `DERIVED_SOURCES` would have no entry, and the new rung would report as TRACELESS — the exact
    false sentence v2725 was written to delete, reappearing on a different rung. The passage
    fraction would also silently change denominator, from `of 6` to `of 7`, with no edit to the
    text that prints it. [[label-outlived-referent]]

    THE TWO SIDES ARE INDEPENDENT, which is the whole point:
      LEFT   reel_story.STAGES               — the shelf's vocabulary, owned by reel_story
      RIGHT  the rungs one_funnel can account for — owned by one_funnel, and derived from two
             different maps neither of which reel_story imports

    ⚠ THE RELATION IS `<=`, NOT `==`, ON PURPOSE. one_funnel is allowed to know about a rung the
    shelf has retired; that is harmless and self-correcting. The dangerous direction is a stage the
    shelf declares and the funnel cannot see, which is the only one an inequality here forbids.
    ⚠ EITHER SIDE UNIMPORTABLE IS UNKNOWN, NEVER ZERO. `0 <= 0` would hold forever on any machine
    where these modules will not load, which is precisely how
    _inv_a_world_reporting_nothing_holds_nothing passed vacuously for months.
    """
    def left():
        import reel_story as RS
        st = tuple(getattr(RS, "STAGES", ()) or ())
        return len(st) if st else None

    def right():
        import one_funnel as OF
        known = set(getattr(OF, "WAYPOINT_SOURCES", {}) or {}) | set(
            getattr(OF, "DERIVED_SOURCES", {}) or {})
        return len(known) if known else None

    return ("every-rung-is-accounted-for",
            "every stage the reel shelf declares is a rung one_funnel can observe, by cache or by "
            "live decider",
            "add a stage to reel_story.STAGES and teach one_funnel nothing: the new rung reports "
            "as traceless and the passage denominator moves with no edit to the text printing it",
            "reel_story.STAGES", left,
            "rungs one_funnel accounts for", right, "<=")


def _inv_a_world_reporting_nothing_holds_nothing():
    """v2696 — WOULD HAVE CAUGHT DEAN'S BOARD, WHICH THE PREVIOUS INVARIANT COULD NOT.

    Konyo: "via the roster via the fleet maybe? like we have trackers within the console maybe?" —
    yes, and the two witnesses were already on disk, in the same snapshot.

    THE SYMPTOM HE REPORTED: his cousin's world showed 0/403 in the console FLEET while the same
    board's Uniques chronicle tab read 243/403. Both surfaces count with the same funiScan(), so
    they cannot differ by logic — only by TIME, and a fleet row is a snapshot read off disk.
    The honest, unambiguous half of that disagreement is this: a world that REPORTS zero finds while
    its own ledger HOLDS entries is contradicting itself, whatever the reason.

    THE TWO WITNESSES, and they are independent readings of one image:
      LEFT   d2r_tally.uniques.have — what the BOARD said about itself
      RIGHT  d2r_foundLog           — the ledger it said it from
    control_app._store_read_all() takes both keys in ONE snapshot, and its own docstring is why
    that matters: "a route can never be paired with another snapshot's values". Reading them
    separately would let a stale tally meet a fresh ledger and invent a disagreement.

    ⚠ ZERO-AND-EMPTY IS NOT A VIOLATION, and that distinction is the whole invariant. A fresh guest
    world reports 0 and holds nothing — correct, and the commonest state on his tree (401 guest
    routes, every one 0). Only 0-while-holding is a contradiction. [[zero-needs-a-denominator]]
    ⚠ IT DOES NOT COMPARE MAGNITUDES. foundLog holds uniques AND set pieces (measured on his own
    world: tally 292 uniques, foundLog 419 keys), so "292 != 419" is not a defect and asserting it
    would be a gate red from birth. Only the zero case is unambiguous.

    MEASURED when written: 1 board world readable on this machine — owner, tally 292, foundLog 419.
    Holds at 0.
    """
    def _worlds():
        try:
            import control_app as ca
        except Exception:
            return None
        out = []
        try:
            for db in ca._webkit_localstorage_dbs():
                got = ca._store_read_all(db, ("d2r_tally", "d2r_foundLog"))
                if not got or not got.get("isBoard"):
                    continue
                v = got.get("vals") or {}
                t = v.get("d2r_tally")
                fl = v.get("d2r_foundLog")
                if not isinstance(t, dict) or not isinstance(fl, dict):
                    continue
                have = ((t.get("uniques") or {}) if isinstance(t.get("uniques"), dict) else {}).get("have")
                out.append((have, len(fl)))
        except Exception:
            return None
        return out

    #: ⚠⚠ v2703 — AN EMPTY WORLD LIST IS UNKNOWN, NOT ZERO, AND THIS PASSED VACUOUSLY FOR MONTHS.
    #: `_worlds()` returns None only on an EXCEPTION. When ca._webkit_localstorage_dbs() simply
    #: yields nothing — Linux CI, the Windows PC, any machine that is not his Mac — it returns [].
    #: left() then summed an empty list to 0, right() returned 0, and `0 <= 0` held forever.
    #:
    #: MEASURED 2026-09-06: this Mac has 1 WebKit localStorage DB and 1 of them is a board world.
    #: CI and the Windows PC have 0. The invariant printed THE SAME GREEN on all three, having
    #: examined one board in one case and nothing at all in the others. Its own docstring says
    #: "MEASURED when written: 1 board world readable on this machine" — which is exactly the
    #: count it never printed at runtime. [[zero-needs-a-denominator]] inside a heart invariant,
    #: which is the layer built to catch this everywhere else.
    def left():
        w = _worlds()
        if w is None:
            return None
        if not w:
            return None      # nothing examined names nothing; a 0 here would be a lie with no author
        return sum(1 for have, held in w if have == 0 and held > 0)

    def right():
        w = _worlds()
        if w is None or not w:
            return None
        return 0

    return ("a-world-reporting-nothing-holds-nothing",
            "no board world reports zero uniques while its own ledger holds entries",
            "seed a world's foundLog and leave its tally at 0 — the fleet then shows 0/403 for a "
            "board that holds a chronicle, which is what he saw and what nothing flagged",
            "worlds reporting 0 while holding a ledger", left, "the allowed number of them", right,
            "<=")


BUILDERS = (_inv_every_rung_the_shelf_declares_is_one_the_funnel_can_ACCOUNT_FOR,
            _inv_a_world_reporting_nothing_holds_nothing,
            _inv_only_a_declared_owner_world_posts_owner_numbers,
            _inv_every_door_counts_the_reels_it_opened,
            _inv_the_tooltip_finder_refuses_more_than_it_finds,
            _inv_the_console_and_the_law_agree_about_furniture,
            _inv_every_declared_tooltip_surface_is_served,
            _inv_vault_worklist,
            _inv_the_two_owned_fields,
            _inv_the_deleter_releases_only_what_the_store_declares,
            _inv_the_fleet_divides_by_the_same_number_the_board_does,
            _inv_the_eagle_can_still_look,
            _inv_hunt_memory_is_being_used,
            _inv_a_lane_that_is_ON_has_either_worked_or_says_why_not,
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
    "reel rungs":        ("every-rung-is-accounted-for",),
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


# ══ v2393 — EVERY INVARIANT PROVES ITSELF, OR SAYS IT HAS NOT ════════════════════════════════
# Konyo: "self-proving gaps i want taken care of everywhere all round the console — i want this
# logic and its own logic coded proving itself, and if it drifts it gets flagged accordingly."
#
# selftest() proves the RELATIONS can refuse (==, <=, >= against synthetic numbers). It has never
# proved that any PARTICULAR invariant can. Those are different claims, and the gap between them
# is where an inert check hides.
#
# MEASURED 2026-09-01, every invariant against his live tree — SIX OF FIFTEEN carry no information:
#     agreeing at ZERO vs ZERO (cannot tell healthy from inert)
#         a_lane_that_is_ON_has_either_worked_or_says_why_not   0 vs 0
#         chronicle_owed_agrees                                 0 vs 0
#         the_deleter_is_never_looser_than_the_planner          0 vs 0
#         the_tooltip_finder_refuses_more_than_it_finds         0 vs 0   <- and THAT is a finding:
#                                                                          the finder has never
#                                                                          located OR refused
#         the_two_deleters_stay_at_their_own_granularity        0 vs 0
#     UNKNOWN (a side could not be read)
#         the_eagle_can_still_look                           None vs 34
#         the_two_owned_fields                                  7 vs None
# Every one of them RENDERS AS "agree" — indistinguishable from a healthy check.
#
# ⚠ THIS SABOTAGES THE INVARIANT'S OWN OPERANDS, NEVER THE LIVE SYSTEM. Perturbing real state to
# test a check would be a test that can damage the thing it grades, on a machine he plays on. The
# perturbation is arithmetic on the value the builder already returned, fed through the SAME
# check_one the live path uses.
#
# ⚠ AND IT PROVES A NARROW THING, WHICH IT MUST SAY OUT LOUD: that the invariant's RELATION can
# refuse given its own operands. It does NOT prove the builders read the right engines — that is
# what the independence audit above is for, and what a runnable per-invariant sabotage would prove
# properly. An instrument that oversells its reach is the defect this whole file exists to catch.
# [[unknown-stays-unknown]] [[regression-guard]]

def _perturb(L, R, rel):
    """A left-hand value that MUST violate `rel` against R. -> (value, why) or (None, why)."""
    if R is None or isinstance(R, bool) or not isinstance(R, (int, float)):
        return None, "the right side is %r — no arithmetic perturbation is defined" % (R,)
    if rel == "==":
        return R + 1, "left made one greater than right"
    if rel == "<=":
        return R + 1, "left pushed above the ceiling it must stay under"
    if rel == ">=":
        return R - 1, "left pushed below the floor it must stay above"
    return None, "unknown relation %r" % (rel,)


def prove_each():
    """Can each invariant actually REFUSE? -> list of dicts, one per invariant.

    proven    the relation went red when its own left value was perturbed
    exercised BOTH sides were non-zero — i.e. it has been asked a real question, not 0 vs 0
    """
    out = []
    for name in sorted(n for n in globals() if n.startswith("_inv_")):
        f = globals()[name]
        if not callable(f):
            continue
        row = {"invariant": name[5:], "proven": False, "exercised": None, "why": ""}
        try:
            key, what, prove, ln, lf, rn, rf, rel = f()
        except Exception as e:
            row["why"] = "could not be built: %s" % str(e)[:70]
            out.append(row)
            continue
        L = _reading(ln, lf)
        R = _reading(rn, rf)
        row["rel"] = rel
        row["left"] = L.value if L.known else None
        row["right"] = R.value if R.known else None
        if not (L.known and R.known):
            # UNKNOWN is not a pass and not a failure — it is "this could not be graded today".
            row["why"] = "a side is UNKNOWN, so it cannot be perturbed or judged"
            out.append(row)
            continue
        # has it ever been asked a real question? 0 vs 0 agrees whatever the engines say.
        row["exercised"] = bool(L.value) or bool(R.value)
        bad, why = _perturb(L.value, R.value, rel)
        if bad is None:
            row["why"] = why
            out.append(row)
            continue
        probe = check_one(lambda: (key, what, prove, ln, (lambda: bad), rn, (lambda: R.value), rel))
        row["proven"] = (probe.get("state") == DISAGREE)
        row["why"] = why if row["proven"] else (
            "PERTURBED AND IT STILL AGREED — this invariant cannot refuse: %s" % probe.get("say", "")[:80])
        out.append(row)
    return out


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

    # ══ v2390 — AND THE CORROBORATOR NOW POLICES ITS OWN INVARIANTS ═══════════════════════════
    # Konyo: "that is why we built corroborator so all 54 modules/engines can be communicating..
    # and doctor that can fix it all and flag whats needed" — after a whole pipeline stage was
    # found never to have run.
    #
    # The machinery was not missing. `_inv_vault_worklist` existed and was GREEN for months
    # because BOTH of its sides read reel_retention.plan()'s tags: two derivations of one broken
    # source agreeing with each other. 0 == 0, while an independent question answered 43.
    #
    # Two numbers that share a source cannot corroborate anything, so this is now checked
    # STRUCTURALLY, on every invariant, forever — rather than by someone noticing.
    # [[feedback-contradiction-is-the-finding]] [[the-unjoined-end]]
    #
    # ⚠ ONE DELIBERATE EXCEPTION, NAMED RATHER THAN PATTERN-MATCHED AROUND.
    # `_inv_the_tooltip_finder_refuses_more_than_it_finds` reads two DIFFERENT COUNTERS out of one
    # report (refused >= located). That is an internal-ratio check, not self-corroboration: it
    # genuinely goes red when the area floor is lowered. An exception list of one, with its
    # reason, is honest; a regex that quietly excused this shape would not be.
    # ⚠ EXCEPTIONS ARE NAMED ONE BY ONE, WITH THE MEASUREMENT THAT EARNED THEM. A regex that
    # quietly excused this shape would re-open the hole this whole audit exists to close, and a
    # syntactic pass genuinely cannot tell "delegates entirely" from "consults, then falls back".
    # So each entry below was PROVEN independent by driving its own `prove` line and watching the
    # two sides part.
    _SHARED_SOURCE_OK = {
        # two DIFFERENT counters out of one report (refused >= located) — an internal ratio, not a
        # shared source. It goes red when _MIN_AREA_FRAC is lowered, which is what it is for.
        "_inv_the_tooltip_finder_refuses_more_than_it_finds",
        # left calls ca._register_is_anchor, which CONSULTS inventory_law.is_locked and then falls
        # back to its own frozenset and a "tome of" test — so the console keeps independent
        # knowledge. MEASURED 2026-09-01 by driving its own prove line: drop one entry from
        # inventory_law.LOCKED and the sides part 4 vs 3. A real invariant with a shared call in it.
        "_inv_the_console_and_the_law_agree_about_furniture",
    }
    try:
        import inspect as _insp
        import re as _re
        shared_bad = []
        unjudged = []
        # ⚠ v2434 — EVERY INVARIANT MUST BE IN ONE LIST OR THE OTHER. Without this an invariant
        # can sit in the file, be graded by prove_each() and audited for independence, and never be
        # evaluated by run() -- which is exactly what `deleter-not-looser` did from the day it was
        # written. Neither roster noticed, because neither was compared to the other.
        _declared = set(RETIRED) | {getattr(_b, "__name__", "") for _b in BUILDERS}
        _orphans = [n for n in sorted(globals())
                    if n.startswith("_inv_") and n not in _declared]
        out.append(("no invariant is graded but never RUN"
                    + (" — in neither BUILDERS nor RETIRED, so prove_each() and the independence "
                       "audit grade them while run() and the eagle can never evaluate them: %s"
                       % ", ".join(_orphans) if _orphans else ""),
                   not _orphans))
        for _name in sorted(n for n in globals() if n.startswith("_inv_")):
            _f = globals()[_name]
            if not callable(_f):
                continue
            try:
                src = _insp.getsource(_f)
            except Exception:
                unjudged.append(_name)
                continue
            if "def left()" not in src or "def right()" not in src:
                unjudged.append(_name)          # NOT the same as clean
                continue
            # local import aliases declared inside this invariant: {alias: real module}
            _aliases = dict((a, m) for m, a in
                            _re.findall(r"import\s+([A-Za-z_][\w.]*)\s+as\s+(\w+)", src))
            l = src[src.index("def left()"):src.index("def right()")]
            r = src[src.index("def right()"):]
            def _direct(b):
                return set(_re.findall(r"\b([a-z_]{2,}(?:\.[a-zA-Z_]+)+)\s*\(", b))

            def _norm(tok, al):
                """alias.fn -> realmodule.fn. The comparison must be on what a call RESOLVES to."""
                head, _, rest = tok.partition(".")
                return "%s.%s" % (al.get(head, head), rest) if rest else tok

            def _calls(b, depth=1):
                """Calls this body makes, plus the calls THOSE make, one level down.

                ⚠ ONE LEVEL IS NOT DECORATION — IT IS THE WHOLE POINT, AND THE FIRST CUT OF THIS
                AUDIT WITHOUT IT WOULD HAVE MISSED THE DEFECT IT WAS WRITTEN FOR. In the real
                case, left called `ca._vault_owed_reels(hist)` and right called `rr.plan(hist)`:
                two different literals, no direct overlap, "independent" by a syntactic reading —
                and _vault_owed_reels is nothing but a filter over plan(). The sharing was one
                hop down. Proven by sabotage: with direct-only matching, restoring the original
                shape kept the self-test GREEN. [[feedback-suspect-the-instrument]]
                """
                out = set(_norm(t, _aliases) for t in _direct(b))
                if depth <= 0:
                    return out
                for tok in list(out):
                    mod, _, fn = tok.rpartition(".")
                    # ⚠ THE ALIAS IS LOCAL TO THE INVARIANT, AND THE FIRST TWO CUTS OF THIS AUDIT
                    # BOTH DIED HERE. Invariants do `import control_app as ca` INSIDE themselves,
                    # so "ca" is not in globals() and __import__("ca") raises — every callee went
                    # unresolved, the expansion found nothing, and the self-test stayed green
                    # through a sabotage that restored the exact defect. Resolve the alias from
                    # the invariant's own import lines first. [[feedback-suspect-the-instrument]]
                    mod = _aliases.get(mod, mod)
                    try:
                        m = globals().get(mod) or __import__(mod)
                        tgt = getattr(m, fn, None)
                        if tgt is None or not callable(tgt):
                            continue
                        # ⚠ NORMALISE THE CALLEE'S OWN TOKENS TOO, THROUGH ITS OWN ALIASES.
                        # The fifth cut of this audit failed here and it is the subtlest step:
                        # control_app._vault_owed_reels calls `_rr.plan(...)` while the invariant's
                        # right side calls `rr.plan(...)`. Same module, different local alias, so a
                        # literal comparison found no overlap and the sabotage stayed GREEN.
                        # Compare RESOLVED module.function, never the alias someone happened to type.
                        _sub = _insp.getsource(tgt)
                        _sub_al = dict((a, m) for m, a in
                                       _re.findall(r"import\s+([A-Za-z_][\w.]*)\s+as\s+(\w+)", _sub))
                        out |= set(_norm(t, _sub_al) for t in _direct(_sub))
                    except Exception:
                        # a callee we cannot read is a callee whose sharing we cannot rule out.
                        # Record it so the pair is judged, never silently cleared.
                        out.add("?unreadable:" + tok)
                return out

            def _is_ours(tok):
                """Is this call into one of THIS PROJECT's engines?

                ⚠ THE THIRD CUT OF THIS AUDIT OVER-FIRED, and an over-firing gate is as useless
                as a silent one. Following callees one level surfaced os.path.join, io.open and
                json.load as "shared" on seven invariants — true, and meaningless: two sides both
                opening a file share PLUMBING, not a SOURCE. The question is only ever whether
                they read the same ENGINE. Resolved by asking where the module lives, not by a
                name blocklist that would rot the moment an engine is renamed.
                """
                mod = tok.split(".")[0]      # already normalised by _norm
                try:
                    m = globals().get(mod) or __import__(mod)
                    f = getattr(m, "__file__", "") or ""
                except Exception:
                    return False
                return os.path.dirname(os.path.abspath(f)) == HERE

            shared = {c for c in (_calls(l) & _calls(r))
                      if _is_ours(c)
                      and not c.split(".")[-1].startswith(("get", "int", "str", "len"))}
            if shared and _name not in _SHARED_SOURCE_OK:
                shared_bad.append("%s (%s)" % (_name, ",".join(sorted(shared))))
        out.append(("no invariant corroborates a thing against ITSELF"
                    + (" — %s" % "; ".join(shared_bad) if shared_bad else ""),
                    not shared_bad))
        # an invariant this audit could not read is UNJUDGED, and unjudged is not clean
        out.append(("every invariant was judgeable"
                    + (" — could not read: %s" % ",".join(unjudged) if unjudged else ""),
                    not unjudged))
    except Exception as _e:
        out.append(("the independence audit ran at all (%s)" % str(_e)[:60], False))
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
