#!/usr/bin/env python3
"""A LOCK THAT UNLOCKS ITSELF — and cannot be opened by hand.

Konyo, 2026-09-02:

    "wilson scores all over.. once that's integrated anywhere and anyplace it can be, the system
     proves itself. START AT THE PRINTER AND REELS WITH THE WILSON SCORE FIRST so that can be done
     beforehand in order, and then once wilson score proves itself within the processing of reels —
     meaning THEATRE MODE AND THE SHELF... so if wilson score eventually proves itself within the
     optimizing and templated and routing down the river stream we mentioned, for each reel a
     unified logic, then it should work and THEN ARM ITSELF. arithmetic as you see.. A LOCK UNTIL
     IT AUTOMATICALLY UNLOCKS WITH A QUEUE FOR WILSON SCORE. this can be used in a bunch of places
     not yet built if we have them too."

This replaces "Konyo flips `_PRUNE_SAFE_TO_RUN` by hand". He does not want to be the arming
mechanism; he wants the system to EARN its permission and then take it.

═══ THE ONE THING THAT WOULD MAKE THIS A LIE ═══════════════════════════════════════════════════

**k and n count SABOTAGES, never agreements.** [[heart-first]] §5, and it is the whole risk:

    an invariant that always agrees may be perfect, or INERT, and those are indistinguishable.

A lock fed by an agreement-rate opens *because nobody ever tested it* — the exact failure the lock
exists to prevent, wearing the lock's own uniform. So:

    n = deliberate sabotages ATTEMPTED against this surface's guards
    k = times a guard REFUSED (went red) for its own reason

A guard that has never been sabotaged contributes NOTHING. `n == 0` is UNPROVEN, and unproven is
not failing — a low score names work to do, and a gate that turns amber at its own newest checks
is ignored within a week. [[heart-first]] again, and it is why `state()` has four values.

═══ WHY WILSON AND CONFLUENCE, BOTH ═══════════════════════════════════════════════════════════

`tv/confidence.py` is THE home for this maths and says why in its own words: "Wilson measures how
many looks agreed, never whether the looks were INDEPENDENT... The two run TOGETHER or neither
means anything." Four re-runs of one sabotage by one harness is one proof wearing four hats.

So a lock opens only when BOTH clear:

    wilson_lower(k, n) >= bar        how much evidence, honest about small n
    confluence(kinds)  >= kinds_bar  how many INDEPENDENT KINDS of evidence

⚠ This module CALLS confidence.py. It does not restate the maths. A second copy of a safety
routine is [[copy-drift]]'s worst case, because the two diverge and only one gets tuned.

═══ THE ORDER IS PART OF THE LOCK ═════════════════════════════════════════════════════════════

He gave a dependency chain, and a lock late in it cannot open early no matter how good its own
score is — proving the deleter in isolation proves nothing about the river feeding it:

    printer + reels  ->  theatre + shelf  ->  routing / the river  ->  the deleter

`after` encodes that. A lock whose prerequisite is not OPEN reports LOCKED with the prerequisite
named, never with its own score, so nobody reads a high number as "nearly there".

═══ WHAT THIS MODULE WILL NOT DO ═══════════════════════════════════════════════════════════════

It DECIDES and REPORTS. It never performs the action, never writes an unlock flag, and has no
override parameter — an override is the hand-arming this replaces. An unreadable ledger is
UNKNOWN, and UNKNOWN is LOCKED: fail closed, and say which of the two it is.
"""

import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from confidence import wilson_lower, confluence   # noqa: E402  — one home for the maths

# ⚠⚠ SNAPSHOT THIS MODULE'S IDENTITY AT IMPORT, and it must happen HERE rather than lazily.
# `registry_may_be_incomplete()` answers True for UNKNOWN as well as STALE — deliberately, since
# "I never checked whether my registry is current" is not grounds for confidence. But that makes
# an un-snapshotted process permanently forgiving: every unrecognised src would read as "UNKNOWN,
# relaunch to judge", and a genuinely forged row would be excused forever. The snapshot is what
# makes the softening narrow instead of universal. [[feedback-blind-fixture-green-gate]]
try:
    import code_staleness as _code_staleness   # noqa: E402
    _code_staleness.snapshot("self_arming")
except Exception:
    pass

#: runtime record of DECISIONS, like .console_scars.json and .second_eye.jsonl — untracked.
#: THE DEFAULT ONLY. Deliberately NOT `os.environ.get(...) or ...` at module level.
LEDGER = os.path.join(HERE, ".self_arming.jsonl")


def _ledger_path():
    """Where the proof queue lives, resolved at CALL time. -> str

    ⚠ v2438 — `test_import_bound_paths` CAUGHT THIS AS AN IMPORT-BOUND PATH AND IT WAS RIGHT.
    The first cut read the env var at module level, which freezes whatever the environment was at
    IMPORT: a fixture setting TV_SELF_ARMING_LEDGER afterwards is a silent no-op, and its proof
    rows land in HIS queue. That registry exists because exactly that truncated 525,187 bytes of
    paid page reads to 748. [[feedback-fixtures-never-touch-live-data]]

    Registering it as import-bound would have satisfied the gate. It is resolved at call time
    INSTEAD, because of what this file gates: a fixture that accidentally banks into the real
    queue does not merely corrupt a record — it RAISES A SCORE, and a raised score opens a lock
    that deletes footage. When a mistake's blast radius is his data, the fix goes in the
    fail-safe direction rather than the documented one.

    Both redirects work now: set TV_SELF_ARMING_LEDGER, or patch the module attribute.
    """
    return os.environ.get("TV_SELF_ARMING_LEDGER") or LEDGER

#: What counts as an INDEPENDENT KIND of proof, and what each is worth. Passed to confluence()
#: rather than hardcoded there, because what counts as independent differs per lane.
#: ⚠ An unknown kind scores 0 by design — a kind nobody has weighted is a kind nobody has thought
#: about, and a default would silently pay it as if someone had.
KINDS = {
    "sabotage": 1.0,    # a guard broken on purpose and watched to go red for its OWN reason
    "cross-family": 0.8,  # a different model family refused it on the real artifact
    "live": 0.7,        # measured against his running console, not a fixture
    "ci": 0.6,          # went red on a runner, on the same bytes
    "fixture": 0.3,     # a harness case — real, and the weakest kind on its own
}

#: name -> what it would do · the bar it must clear · what must be OPEN before it may open at all.
#: THE ORDER IS HIS. Nothing here may be reordered to make something arm sooner.
LOCKS = {
    # ⚠⚠ v2570 — THE PRINTER HAD NO LOCK AT ALL, and it is step 1 of his own chain. Measured
    # 2026-09-04: fourteen locks and routes were declared and NOT ONE named the printer, the river
    # or reel selection, so the layer that walks every reel he owns was believed purely because
    # nobody had ever attempted to break it. That is the state this module calls INERT.
    # His words: "build the printer lock and wire the whole river".
    #
    # It earns trust in what it PRINTS rather than permission to act — printer.stream() writes
    # nothing and deletes nothing — but it is declared here rather than in ROUTES because the
    # deleter now waits on it, and `after` may only name something the chain can resolve.
    "printer.stream": {
        "surface": "THE RIVER", "acts": "walks every reel from the door to the far end",
        "bar": 0.510, "kinds_bar": 1.0, "after": [],
    },
    # step 1 — the printer and the reels
    "vault.sweep_start": {
        "surface": "VAULT", "acts": "starts a paid sweep",
        "bar": 0.510, "kinds_bar": 1.0, "after": [],
    },
    # step 1 — the actions that change his ledger
    "vault.apply": {
        "surface": "VAULT", "acts": "mules items between characters",
        "bar": 0.722, "kinds_bar": 1.3, "after": ["vault.sweep_start"],
    },
    # ⚠⚠ THIS ONE CAN NEVER BE PROVEN, AND THAT IS A PROPERTY OF THE DOOR, NOT A MISSING HARNESS.
    # `vault_forget()` is seven lines, one return, always ok — it has NO refusal path, so there is
    # no state in which it must say no and therefore nothing a sabotage could attempt. That is
    # deliberate: its own docstring says the swept memory is an optimisation and "an optimisation
    # he cannot clear is a cage", and the ledger it drops is rebuildable from the reels. Gating it
    # would be exactly the button-blocking his standing ruling forbids — locks are BADGED, never
    # enforced.
    #
    # So it sits at n=0 forever, and the panel used to explain that with the same sentence it uses
    # for a door nobody has got round to testing: "no sabotage has been attempted ... That is not a
    # failure." True, and it implies a harness is merely MISSING. Those are different facts —
    # nobody-looked versus there-is-nothing-to-look-at — and collapsing them is the seventh shape
    # of an unmeasured number. `unprovable` says which one this is, in the panel, out loud.
    # [[unknown-stays-unknown]]
    #: 154 — THE NUMBER HE MAKES STORAGE DECISIONS ON. `prunedMb` was HARDCODED to 0 at the only
    #: call site, so "the prune has never freed a byte" was a fact about the CALLER; that framing
    #: was retracted. The call site passes None now — measured on his store, 8,270 rows carrying 0
    #: against 280 carrying None — and the remainder is that nothing has ever passed a REAL figure.
    #: His ruling: *"fix it to the hardening and wilsons and to the heart so it proves itself
    #: before its unlocked."* So the reporter earns its unlock like every other surface.
    #: ⚠ IT GUARDS THE REPORT, NOT THE DELETER. `prune.arm` already guards whether the prune may
    #: act; this guards whether the row may CLAIM. They fail differently and must not share a lock.
    #: A7·ROUTE — WHERE A REEL IS IN THE RIVER, decided by the reel's own evidence and never by
    #: why we are keeping its bytes. Measured on his shelf 2026-09-05: 40 reels, 29 never read,
    #: `vault-owes` matching 0 of 40 because it is the LAST first-match-wins rule, and all 40
    #: sitting at two of `reel_story`'s six stages because `_stage_of(tag)` reads the RETENTION
    #: TAG. ⚠ IT GUARDS THE ROUTING, NOT THE READING: nothing here arms a paid sweep, and the
    #: queue this publishes is consumed by nobody. `prune.arm` guards whether the prune may act;
    #: this guards whether the keep-reason may decide a reel's read-fate. Different failures.
    "reel.route": {
        "surface": "THE RIVER",
        "acts": "decides where each reel is, and therefore what it is owed",
        "bar": 0.510, "kinds_bar": 1.0, "after": [],
    },
    "prune.reports": {
        "surface": "THE RIVER",
        "acts": "tells him how much space was freed",
        "bar": 0.510, "kinds_bar": 1.0, "after": [],
    },
    "vault.forget": {
        "surface": "VAULT", "acts": "drops the ledger",
        "bar": 0.722, "kinds_bar": 1.3, "after": ["vault.sweep_start"],
        "unprovable": ("the door has no refusal path by design — clearing a rebuildable "
                       "optimisation is a button, and gating it would be a cage. There is no "
                       "state in which it must refuse, so sabotage cannot produce evidence in "
                       "either direction"),
        "unprovable_fn": "vault_forget",
    },
    # step 1 — MINI AUTO. His ruling, 2026-09-02: "i want it not enforced... i want it BADGED...
    # my point was i want it KNOWN on the console is all", with "a logical coding to it with wilson
    # via connected to the heart for real".
    # ⚠ SO THIS LOCK IS A STAMP, NOT A GATE — nothing calls may("miniauto.run") to block the
    # button, and that is deliberate rather than unfinished. It still earns its state the same way
    # every other lock does, so the console can say what has been proven instead of staying silent.
    # It sits at step 1 because MINI AUTO drives the pointer over his stash and films what the game
    # draws: it is the printer and the reels, which is where he said Wilson starts.
    "miniauto.run": {
        "surface": "MINI AUTO", "acts": "moves the pointer over his stash and films the tooltips",
        "bar": 0.510, "kinds_bar": 1.0, "after": [],
    },
    # step 4 — the deleter. Last, and it cannot be reached early.
    "prune.arm": {
        "surface": "THE RIVER", "acts": "deletes footage — there is no undo",
        "bar": 0.839, "kinds_bar": 1.8,
        # ⚠⚠ v2570 — `printer.stream` ADDED, and this is the wiring he asked for. His order is
        # "printer + reels -> theatre + shelf -> routing -> the deleter", and this module's own
        # docstring says a lock late in it "cannot open early no matter how good its own score is
        # — proving the deleter in isolation proves nothing about the river feeding it." The
        # deleter was waiting on the two VAULT locks and on nothing in the river it deletes from.
        # This is strictly more conservative: prune.arm can now be held by a printer that is not
        # proven, and never opened by one.
        "after": ["printer.stream", "vault.sweep_start", "vault.apply"],
    },
}

#: ⚠⚠ THE ROUTES, ON THE SAME ARITHMETIC. His ruling: "each of the locked routes needs that same
#: unified logic for wilson score and that same lock/unlock prove themselves style ... and all
#: connected to the heart of the console obviously".
#:
#: A VALVE earns permission to ACT — it deletes footage, it mules items. A ROUTE only REPORTS, so
#: what it can earn is trust in the NUMBER IT PRINTS, not a licence. Same Wilson lower bound, same
#: kinds/confluence bars, same self-proving flip with nothing hand-set; the earned word is PROVEN
#: rather than OPEN. Keeping them in ONE table and ONE score() is the whole point — a second
#: implementation of this arithmetic would drift from the first within a week. [[copy-drift]]
#:
#: The bars are LOWER than a valve's on purpose: being wrong about a printed number is recoverable
#: and being wrong about the deleter is not. One kind of look is enough to trust a count.
ROUTES = {}
for _set, _keys in (("chronicle", ("runeword", "set", "unique")),
                    ("fleet", ("runewords", "sets", "uniques")),
                    ("roster", ("runeword", "set", "unique"))):
    for _k in _keys:
        ROUTES["%s.%s" % (_set, _k)] = {
            "surface": _set.upper(),
            "acts": "reports the %s count on the %s route" % (_k, _set),
            "bar": 0.510, "kinds_bar": 1.0, "after": [],
        }

# the four states, and they are four on purpose
#: ⚠⚠ A TIER ABOVE MERELY-PROVEN. His ruling: "is there a way for the confluence there to like
#: surpass the defaulted or standard proven state ... is there a HARD MODE for this".
#:
#: Clearing a bar is a floor, not a ceiling, and a surface that stops at the floor looks identical
#: to one that could not do better. HARDENED is what a surface earns by continuing: a much higher
#: Wilson lower bound AND evidence from genuinely INDEPENDENT kinds. The confluence axis is the
#: one that matters here — Wilson counts how many looks agreed, never whether they were the same
#: look repeated, so more attempts of one kind can reach 0.95 while proving only that one
#: instrument keeps agreeing with itself. The maximum confluence is 3.40 (all five kinds).
#:
#: It is EARNED the same way everything else here is: derived from the ledger, never assigned.
HARD_BAR = 0.900        #: the Wilson lower bound a HARDENED surface must clear
HARD_KINDS_BAR = 2.50   #: needs three genuinely different kinds — e.g. sabotage+cross-family+live

HARDENED = "HARDENED"
OPEN = "OPEN"
LOCKED = "LOCKED"          # proven, and it did not clear the bar
UNPROVEN = "UNPROVEN"      # n == 0 — nobody has tested it. NOT a failure, NOT a score.
#: ⚠⚠ A CLAIM THAT COULD NOT RUN IS NOT AN ABSENT CLAIM. A harness that banks a claim with n=0 and
#: a stated reason has declared an axis and then failed to exercise it — and because zero attempts
#: cannot move a Wilson bound, that failure was INVISIBLE: the lock scored on its other claims and
#: reported OPEN.
#:
#: HIS CATCH, 2026-09-04, and it is the sharpest one yet: *"miniauto.run … absolutely has not been
#: proven or done yet … its not working at all what do you mean? it should be locked as hell!"*
#: He is right, and the harness's own words say why. `hover_wilson.probe_anchor` banks n=0 because
#: `anchor_from_tooltip_rect` refuses: *"no tooltip->cell OFFSET has been calibrated, so the anchor
#: would be the tip's own corner and EVERY ITEM WOULD LAND IN WHICHEVER CELL THE TEXT COVERS."*
#: That is a precise description of MINI AUTO not working — and the lock over it read **OPEN, 55 of
#: 55 refused**, because the one probe that tests the broken thing contributed nothing.
#:
#: So an unexercised axis holds the lock instead of disappearing from it. This is a REPORT, not a
#: gate: `may()` is still never called and nothing is blocked. [[unknown-stays-unknown]]
INCOMPLETE = "INCOMPLETE"  # a declared claim banked n == 0 — an axis nobody could exercise
UNKNOWN = "UNKNOWN"        # the ledger could not be read. Fails closed, and says so.


def record(lock, kind, refused, note="", src=None):
    """Append one SABOTAGE ATTEMPT and whether the guard refused. -> dict (the row written)

    `refused` True means the guard went RED for its own reason — that is the SUCCESS here, which
    reads backwards until you remember what is being measured: the ability to say no.

    ⚠⚠ REG-591 — THIS DOOR HAD NO ALLOW-LIST, AND IT IS THE ONE RULE THAT MATTERS MOST HERE.
    `bank()` refuses any (src, lock) pair PROVES does not declare — that is what stops one
    surface's sabotage opening a DIFFERENT surface's lock, and it matters most for `prune.arm`,
    because footage has no undo. `record()` took no `src` at all, so a single call could credit
    ANY lock from anywhere, and nothing downstream could tell where the evidence came from.

    MEASURED when this was found (fixing REG-575): `record()` has **ZERO production callers** and
    his live ledger holds **51 bank-shaped rows and 0 record-shaped**. So this was never a leak —
    it was a loaded gun, and the first caller added would have fired it. Closing the writer is
    cheap precisely because nobody uses it yet.

    ⚠ THE READER IS DELIBERATELY UNCHANGED. `_row_fault` still accepts a src-less row, because
    historical rows and `test_self_arming`'s own `put()` helper write that shape directly, and
    rejecting them would fail the whole read — the exact defect REG-575 was. The hole is closed at
    the door where new evidence is created, not by refusing evidence that already exists.
    [[unknown-stays-unknown]]
    """
    src = str(src or "").strip()
    if not src:
        raise ValueError(
            "record() needs a `src`: which harness produced this attempt. Without one the row "
            "could credit any lock from anywhere, which is what the PROVES allow-list exists to "
            "prevent. Use bank() if you have counts; pass src= if you have a single attempt.")
    allowed = PROVES.get(src)
    if allowed is None:
        raise ValueError("src %r is not a declared evidence source (PROVES)" % src)
    if str(lock) not in allowed:
        raise ValueError("%r does not prove %r — PROVES declares it for %s"
                         % (src, lock, ", ".join(allowed) or "nothing"))
    row = {
        "lock": str(lock), "kind": str(kind), "refused": bool(refused), "src": src,
        "note": str(note or "")[:400], "ts": int(time.time() * 1000),
    }
    with io.open(_ledger_path(), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


# ── WHERE EACH HARNESS'S EVIDENCE IS ALLOWED TO LAND ─────────────────────────────────────────
# v2444 — AN ALLOW-LIST, BECAUSE THE FAILURE IT PREVENTS IS THE WORST ONE AVAILABLE HERE. A
# sabotage against the render gate proves THE RENDER GATE. It is real evidence and it says nothing
# whatever about whether the vault may mule an item or whether footage may be deleted. Banking it
# under prune.arm would let the deleter open itself on somebody else's proof, and footage has no
# undo. So a source declares what it bears on, and bank() refuses everything else.
#
# A source that proves NOTHING declared here is listed with an empty tuple ON PURPOSE — that is a
# statement that its evidence has no lock, not an oversight, and it keeps the next person from
# quietly wiring it to whichever lock happens to be nearby.
PROVES = {
    # hover_wilson scores the autopilot's four claims on real sabotage attempts, and the autopilot
    # IS mini-auto: "moves the pointer over his stash and films the tooltips". Same surface, same
    # guards, same three-state vocabulary (UNPROVEN / PROVEN / LEAKS).
    "hover_wilson": ("miniauto.run",),
    # render_check proves that the RENDER GATE can be seen red. There is no render lock, and there
    # should not be one — nothing it sabotages can delete footage or touch his ledger.
    "render_check": (),
    # A2 step 1 — "the printer and the reels", which is this table's own label for
    # vault.sweep_start. sweep_wilson attempts states in which chronicle_sweep_start MUST refuse
    # (a sweep already running; no lane to read with) and counts whether it did. It never starts a
    # sweep: there is no attempt in it whose success path runs, because the door it guards spends
    # money.
    "sweep_wilson": ("vault.sweep_start",),
    #: 154 — the disk row's own refusals. It NEVER prunes: every attempt is a state in which the
    #: row must decline to name a freed figure, and nothing here deletes a byte.
    "disk_report_wilson": ("prune.reports",),
    # ⚠ THE SECOND KIND for prune.reports — attacks a different model family designed COLD, three
    # of which LANDED and were all mine (negative zero past a `< 0` check; a flat +1 MB tolerance
    # licensing 0.9 MB against a 0-byte corpus and 2.0 MB against a 1 MiB one). Confluence only
    # moves on independent kinds; five more sabotages of mine would be one instrument in a new hat.
    "disk_report_crossfamily": ("prune.reports",),
    #: A7·ROUTE — seven refusals the router must make, each a way the keep-reason could creep back
    #: into the read-fate or an unmeasured reel could be dressed as a measured one. It reads no
    #: footage, arms no sweep and deletes nothing.
    "reel_router_wilson": ("reel.route",),
    #: A2·HARD — attacks on the vault WRITE door designed by a DIFFERENT model family, which is
    #: the third evidence KIND `vault.apply` needed and the only one available without spending
    #: his money. Two of the three found a real hole (an uncorroborated row under `unsure` reached
    #: the write path without the gate being asked); the third was refuted and is banked anyway so
    #: the tried-and-failed axis is on the record. Safe by construction: every attempt carries
    #: evidence that cannot clear the gate, so the only outcome the door can produce is a refusal.
    "vault_apply_crossfamily": ("vault.apply",),
    # vault_wilson attempts proposals the WRITE door must reject — v1595's re-gate, which
    # returns before the board is ever asked. It never applies anything: every row it hands
    # in carries an empty evidence list, so it fails the witness gate by construction.
    # ⚠ It is declared for vault.apply ONLY. vault.forget has no refusal path at all (7
    # lines, one return, always ok), so nothing can prove it by sabotage and nothing here
    # pretends to.
    "vault_wilson": ("vault.apply",),
    # printer_wilson removes each owner's ability to answer and requires the printer to say
    # UNKNOWN **with a reason** rather than guess, skip the station, or drop the reel. It calls
    # exactly one function, printer.stream(), whose own docstring is "IT PRINTS NOTHING AND
    # DELETES NOTHING ... This is a REPORT." No os.remove, no apply_plan, no TV_AUTO_PRUNE.
    "printer_wilson": ("printer.stream",),
    # the same refusal asked of the RUNNING console over its own HTTP route — a different
    # KIND, not a second helping of the same one. vault.apply carries kinds_bar 1.3 exactly
    # so that one kind cannot open it.
    "vault_live": ("vault.apply",),
    # A2 step 4 — the deleter. prune_wilson attempts states in which retention_may_act() MUST
    # refuse: every spelling of OFF (v2082's scar, where only the byte "0" held and every other
    # spelling armed an unattended deleter), an unconfirmed board world, a world check that
    # raises, and a drift answer of the wrong shape. It calls exactly one function, whose own
    # docstring is "Decides; never acts" — there is no path in it that deletes a byte, and
    # tv/test_prune_wilson.py asserts that from the source.
    # ⚠ It is declared for prune.arm ONLY, and even a perfect record cannot open that lock:
    # kinds_bar is 1.8 and sabotage weighs 1.0. The door with no undo does not open on one kind
    # of look, which is the point of the bar rather than a gap in this harness.
    "prune_wilson": ("prune.arm",),
    # ⚠ THE ROUTES. route_wilson removes what each lane CLAIMS TO HAVE FOUND — deletes the
    # artifact, deletes bible.html, blanks every mention of the roster stem, removes the file a
    # lane names — and counts whether the lane noticed. A lane that still says ok with its
    # evidence gone was decorative. It proves ONLY the routes, never a valve: evidence about a
    # thing that reports may not open a door that acts.
    "route_wilson": tuple(sorted(ROUTES)),
}


def withdraw(lock, kind, src, ref, why):
    """Retire one banked AXIS whose evidence was never about the lock. -> dict (the row written)

    ⚠⚠ WHY THIS HAD TO EXIST, MEASURED 2026-09-05. `_fold` keys on (lock, kind, src, ref) and keeps
    the NEWEST row per key. So rewriting a harness's attacks retires an axis only when the new axis
    reuses the old REF NAME. `disk_report_wilson`'s four corrected attacks are named
    notanumber/notfinite/negative/overcorpus; the three REG-600 axes they replaced were named
    noprune/unreadable/shrank. Nothing superseded those, so **`prune.reports` read n=56 — 32 real
    refusals PLUS the 24 identity assertions the rewrite existed to remove.**

    That is worse than not having fixed it: the lock LOOKS repaired while three-eighths of its
    evidence is still an event that could not fail, and the mixture is invisible in the total.

    ⚠ NOTHING IS DELETED. The ledger stays append-only — this appends a row that supersedes the
    axis with `n=0, k=0`, so it contributes nothing to any score while the original row and this
    retraction both remain on the record. A withdrawal you cannot read is a deletion with a nicer
    name. [[unknown-stays-unknown]]

    ⚠ A REASON IS REQUIRED. An axis retired with no stated reason is indistinguishable from one
    quietly dropped because it was inconvenient.
    """
    if not str(why or "").strip():
        raise ValueError("a withdrawal needs a REASON. An axis retired without one cannot be told "
                         "apart from evidence quietly dropped because it was inconvenient.")
    if not str(ref or "").strip():
        raise ValueError("a withdrawal needs the REF of the axis it retires — that is the fold key,"
                         " and without it this appends a new empty axis instead of superseding one")
    return bank(lock, kind, src, n=0, k=0, ref=ref, attacks=0, withdrawn=True,
                note="WITHDRAWN — %s" % str(why)[:360])


def bank(lock, kind, src, n, k, note="", ref="", attacks=None, withdrawn=False):
    """Bank a harness's OWN aggregate for one lock. -> dict (the row written)

    Idempotent by construction: the row carries `src`, and _fold keeps only the newest row per
    (lock, kind, src). Running the harness twice does not make the evidence twice as strong.

    ⚠ IT REFUSES RATHER THAN GUESSES, in three directions, because every one of them ends with a
    lock opening on evidence that was never about it:
      · an undeclared source, or a lock that source does not prove -> refuse
      · k > n -> refuse; more refusals than attempts is an instrument fault, not a great result
      · a lock that is not declared -> refuse
    [[unknown-stays-unknown]] [[feedback-suspect-the-instrument]]
    """
    if lock not in LOCKS and lock not in ROUTES:
        raise ValueError("no such lock or route is declared: %r" % (lock,))
    allowed = PROVES.get(str(src))
    if allowed is None:
        raise ValueError("%r is not a declared evidence source. Add it to PROVES and say what its "
                         "sabotages actually bear on — an undeclared source is how a lock opens on "
                         "somebody else's proof." % (src,))
    if lock not in allowed:
        raise ValueError("%r does not prove %r. It is declared as proving %s. Evidence about one "
                         "surface is not evidence about another, and this refusal is the whole "
                         "point of the allow-list." % (src, lock, allowed or "NOTHING"))
    # ⚠ AN UNDECLARED KIND IS A SILENT STOP, WHICH IS WORSE THAN A LOUD ONE. `kind` is the TIER
    # confluence() weighs, not a free label — KINDS maps sabotage 1.0 / cross-family 0.8 / live 0.7
    # / ci 0.6 / fixture 0.3. An unrecognised tier scores 0.00, so the lock stays shut FOREVER while
    # its Wilson figure reads 0.935 and every number on the page looks healthy. Measured here on the
    # first real run: banking the four hover claims under their own names gave kinds ['coordinate',
    # 'read', 'slot'] scoring 0.00 against a bar of 1.00. Refusing beats a lock nobody can explain.
    if str(kind) not in KINDS:
        raise ValueError("%r is not a declared evidence tier. confluence() weighs KINDS (%s), and "
                         "an unrecognised kind scores 0.00 — the lock would stay shut for ever with "
                         "a healthy-looking Wilson score and no reason on screen."
                         % (kind, ", ".join(sorted(KINDS))))
    n = int(n or 0)
    k = int(k or 0)
    if n < 0 or k < 0 or k > n:
        raise ValueError("k=%d of n=%d is not a possible sabotage record — more refusals than "
                         "attempts is an instrument fault" % (k, n))
    row = {
        "lock": str(lock), "kind": str(kind), "src": str(src), "ref": str(ref or ""),
        "n": n, "k": k, "refused": bool(k > 0),
        # ⚠⚠ HOW MANY DISTINCT SABOTAGES ARE BEHIND THOSE n TRIALS — the number that stops a score
        # being bought by repetition. Wilson tightens with n and has no way to know whether n is
        # 83 independent looks or ONE attack applied 83 times, so it must be told.
        # MEASURED 2026-09-04, and it is why this field exists: `printer.stream` banked 83/83 for
        # wilson 0.9558, and 80 of those 83 were TWO attack functions applied to 40 reels each.
        # Counted as the five distinct attacks it actually runs, the same evidence scores 0.5655
        # — barely over its 0.510 bar. Nothing was faked and every refusal was real; the SCORE was
        # inflated by looping. `None` means the harness did not say, which is not the same as one.
        "attacks": (None if attacks is None else int(attacks)),
        # ⚠⚠ A RETIRED AXIS IS NOT AN UNRUNNABLE ONE, and the report read them identically until
        # v2647. Both bank n == 0; only this field separates "I own this axis and could not run
        # it" from "this axis was exercised, found to prove nothing, and withdrawn". Reporting a
        # withdrawal as INCOMPLETE puts a true sentence under the wrong word.
        # [[label-outlived-referent]] [[unknown-stays-unknown]]
        "withdrawn": bool(withdrawn),
        "note": str(note or "")[:400], "ts": int(time.time() * 1000),
    }
    with io.open(_ledger_path(), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def _fold(rows):
    """Reduce banked AGGREGATES to one row per (lock, kind, src, ref), newest wins. -> list

    Single-attempt rows are never folded — each one is its own event and they accumulate, which
    is what record() means.

    ⚠⚠ v2612 — THIS KEYED ON `src` AND THAT STOPPED BEING THE RIGHT QUESTION. `record()` took no
    src until REG-591 closed the allow-list bypass at its door; the moment single events grew one,
    three separate attempts folded into ONE and the count read (0, 1) instead of (2, 3). The test
    that caught it says the rule in its own name: *record() rows are events and must keep adding
    up; only banked aggregates fold.*

    What makes a row foldable is that it is an AGGREGATE — a harness re-reporting its own running
    total, where the newest reading replaces the older. An EVENT is not a re-report of anything.
    Key on that and a src can be added to either writer without silently eating evidence.
    """
    out, latest = [], {}
    for r in rows:
        src = r.get("src")
        if not src or not (("n" in r) or ("k" in r)):
            out.append(r)
            continue
        # ⚠ ref IS PART OF THE KEY, and leaving it out cost three of four claims on the first
        # real run. The four hover claims are all `sabotage` tier, so (lock, kind, src) is the SAME
        # key for all of them — folding on that kept only the last one written and threw away
        # coordinate's 48/48, keeping slot's 2/2. n fell from 55 to 2 and nothing said so.
        key = (r.get("lock"), r.get("kind"), src, r.get("ref") or "")
        cur = latest.get(key)
        if cur is None or int(r.get("ts", 0) or 0) >= int(cur.get("ts", 0) or 0):
            latest[key] = r
    out.extend(latest.values())
    return out


def _row_fault(r):
    """Why this row could not have come from ANY writer in this module. -> str ("" when sound)

    ⚠ EVERY CHECK HERE IS ONE bank() ALREADY MAKES (self_arming.py, bank). It is not a second
    opinion — a second copy of a safety rule is [[copy-drift]]'s worst case. It is the SAME rules
    asked on the read side, because bank() guards its own door and nothing guarded the file.

    ⚠⚠ REG-575 — IT ONLY KNEW ONE OF THIS MODULE'S TWO WRITERS, AND FAILED THE WHOLE FILE ON THE
    OTHER. v2581 wrote this against bank()'s shape alone. `record()` — the single-attempt writer,
    documented in score() as *"everything record() has ever written"* — emits
    `{lock, kind, refused, ts}` with **no `src` and no `n`/`k`**, so every row it has ever produced
    was judged "src '' is not a declared evidence source". One bad row fails the entire read by
    design, so a single `record()` call would have turned all fifteen locks UNKNOWN at once.

    MEASURED 2026-09-04: `record()` has ZERO production callers and his live ledger holds 51
    bank() rows and 0 record() rows, so it never fired on his console — but `test_self_arming`
    (a REGISTERED gate) went red the version this shipped and stayed red. **A validator that
    rejects rows its own module writes is not strict, it is wrong**, and the gate said so.

    ⚠ SO IT JUDGES A ROW AGAINST THE SHAPE IT DECLARES. A row carrying `src` is a bank() row and
    gets every bank() rule. A row without one is a record() row and gets the rules that APPLY to
    it — never the three that cannot. Silently passing a record() row through the bank() checks
    would be the same defect wearing the opposite coat.

    ⚠ AND THE ASYMMETRY IS REAL, NOT RESOLVED HERE: a record() row carries no `src`, so the PROVES
    allow-list — the rule stopping one surface's proof from opening another's lock — cannot be
    applied to it at all. That was true before this function existed and is not made worse by it.
    It is safe TODAY only because record() has no callers; the moment one is added, a proof could
    land on any lock. Named in TASKS.md rather than left for someone to find. [[the-unjoined-end]]
    """
    lock, kind = str(r.get("lock") or ""), str(r.get("kind") or "")
    # ⚠⚠ THE DISCRIMINATOR IS AGGREGATE-vs-EVENT, NOT src, AND THAT DISTINCTION COST A SECOND
    # ROUND OF REG-575. It keyed on `"src" in r` — correct only while `record()` wrote no src.
    # v2612 gave record() a src to close the allow-list bypass, every single-event row grew one,
    # this branch judged them as bank() rows, demanded the `n`/`k` they never have, and the whole
    # read failed CLOSED again — all fifteen locks UNKNOWN, exactly the defect REG-575 was.
    # Caught by `test_single_attempts_still_ACCUMULATE_and_mix_with_aggregates`, which read
    # (None, None) instead of (2, 3).
    #
    # What actually separates the two writers is what they CARRY: `bank()` writes counts, and
    # `record()` writes one outcome. Key on that and a src can be added to either without
    # re-breaking the reader.
    _is_aggregate = ("n" in r) or ("k" in r)
    if "src" in r:
        src = str(r.get("src") or "")
        allowed = PROVES.get(src)
        if allowed is None:
            # ⚠⚠ AN UNRECOGNISED SOURCE IS NOT A FORGED ROW WHEN THIS PROCESS'S REGISTRY IS OLD.
            # MEASURED 2026-09-05: his console booted at 08:43 and ran that image for sixteen
            # hours. `reel_router_wilson` was declared in PROVES on disk and its rows appended to
            # the ledger; the running console did not recognise the source and published
            # ".self_arming.jsonl has a row that could not have been banked" — a definite
            # accusation of forgery against a row that was banked correctly. Read under the code
            # on disk the same ledger is clean (reel.route OPEN, 56/56).
            #
            # His ask, three times: *"stale in-memory so for this a safeguard on it? just like we
            # have regression watchdog?"* This is it. "I do not know this source" and "this source
            # may not exist" are different facts, and which one applies depends entirely on
            # whether THIS process's PROVES can be trusted to be complete.
            # [[unknown-stays-unknown]] [[stale-reading]]
            try:
                import code_staleness as _CS
                if _CS.registry_may_be_incomplete("self_arming"):
                    return ("src %r is not in THIS PROCESS's PROVES, and this process is running "
                            "an older self_arming than the one on disk — so whether the row is "
                            "legitimate is UNKNOWN, not refused. Relaunch to judge it." % src)
            except Exception:
                pass
            return "src %r is not a declared evidence source" % src
        if lock not in allowed:
            return "%r does not prove %r" % (src, lock)
    if not _is_aggregate:
        # a single attempt: its outcome is in `refused`. score() reads it as n=1.
        if not isinstance(r.get("refused"), bool):
            return ("refused=%r is not a boolean, and score() would have read it as an outcome "
                    "anyway" % r.get("refused"))
    elif "src" not in r:
        return ("a row carries n/k with no src, so nothing declares what it may prove and score() "
                "would still count it")
    if _is_aggregate and kind not in KINDS:
        # ⚠ ON BANK() ROWS ONLY, and that is not a softening. bank() validates the kind at its own
        # door, so an undeclared kind in a row claiming a src could not have come from it. A
        # record() row is different BY CONTRACT: `confluence()` weights an unlisted kind at ZERO,
        # and `test_an_UNWEIGHTED_kind_is_worth_zero_not_a_default` pins that a surface carrying
        # one stays LOCKED — a real, useful state. Failing the read instead turned "this evidence
        # counts for nothing" into "the file cannot be trusted", which are opposite facts about
        # the same row. Worth zero is a MEASUREMENT; unreadable is the absence of one.
        return "kind %r is not a declared evidence tier" % kind
    if _is_aggregate:
        n, k = r.get("n"), r.get("k")
        # ⚠ bool is a subclass of int, and `True` would otherwise pass as the count 1 — the same
        # shape REG-573 found writing "read (1 pages)" into a tombstone.
        for nm, v in (("n", n), ("k", k)):
            if isinstance(v, bool) or not isinstance(v, int):
                return "%s=%r is not a whole number, and score() would have defaulted it" % (nm, v)
        if not (0 <= k <= n):
            return "k=%d of n=%d is not a possible record" % (k, n)
    ts = r.get("ts")
    # ⚠ _fold keeps the GREATEST ts per (lock, kind, src, ref), so a row stamped in the future is
    # an unreplaceable pin: no honest later run could ever supersede it.
    if isinstance(ts, (int, float)) and ts > (time.time() + 300) * 1000:
        return "ts is in the future, which _fold could never supersede"
    return ""


def _rows():
    """-> (list|None, why). None means UNREADABLE, which is never 'no proofs'."""
    p = _ledger_path()
    if not os.path.exists(p):
        return [], ""          # absent is legitimately empty: nothing has been proven yet
    out = []
    try:
        with io.open(p, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except ValueError:
                    # a line that will not parse is a hole in the evidence, not a blank one
                    return None, "%s has an unparseable row" % os.path.basename(p)
                if not isinstance(r, dict):
                    continue
                # ⚠⚠ v2581 — THE VALIDATIONS LIVED ONLY IN bank(), SO THEY GUARDED THE DOOR AND
                # NOT THE ROOM. Anything that appended a line to this file — a stray script, a
                # hand edit, a crashed writer — bypassed every check bank() makes, and score()
                # then read it as evidence. Worse, score() defaults a missing count:
                # `int(r.get("n", 1) or 0)`, so a three-key row {lock, kind, refused:true} was
                # silently worth n=1 k=1 of whatever tier it named.
                #
                # These are bank()'s OWN rules re-applied on the way IN. Measured against his 51
                # real rows before it shipped: ZERO would fail, so this costs nothing that is
                # honest and closes the gap for everything that is not.
                #
                # ⚠ A BAD ROW FAILS THE WHOLE READ, exactly as an unparseable line does. Skipping
                # it would let a forged row be quietly dropped while the rest scored on — and the
                # lock would open on a ledger nobody could see had been edited. UNKNOWN is
                # LOCKED here (may() returns False), so this fails closed. [[unknown-stays-unknown]]
                _bad = _row_fault(r)
                if _bad:
                    return None, ("%s has a row that could not have been banked: %s"
                                  % (os.path.basename(p), _bad))
                out.append(r)
    except Exception as e:
        return None, "%s could not be read: %s" % (os.path.basename(p), e)
    return out, ""


def score(lock, rows=None):
    """The arithmetic for ONE lock. -> dict

    Never returns a wilson figure when n == 0. `wilson: None` means nobody looked; `0.0` would be
    a measurement nobody took. [[unknown-stays-unknown]]
    """
    # a route scores on the SAME arithmetic as a valve — one table lookup, one score()
    spec = LOCKS.get(lock) or ROUTES.get(lock)
    if not spec:
        return {"lock": lock, "state": UNKNOWN, "why": "no such lock is declared"}
    if rows is None:
        rows, why = _rows()
        if rows is None:
            return {"lock": lock, "state": UNKNOWN, "why": why,
                    "k": None, "n": None, "wilson": None, "kinds": None}
    mine = _fold([r for r in rows if r.get("lock") == lock])
    # v2444 — A ROW IS EITHER ONE ATTEMPT OR AN AGGREGATE, and the two must add up the same way.
    # A row with no "n" is a single attempt worth 1 (everything record() has ever written), so the
    # old arithmetic is unchanged for it. A row WITH "n" was banked by a harness that owns its own
    # counting, and _fold has already reduced its family to the newest one — so re-running that
    # harness replaces its evidence rather than doubling it.
    n = sum(int(r.get("n", 1) or 0) for r in mine)
    k = sum(int(r.get("k", 1 if r.get("refused") else 0) or 0) for r in mine)
    # a kind counts as evidence only where something was actually REFUSED under it
    kinds = sorted({str(r.get("kind")) for r in mine
                    if int(r.get("k", 1 if r.get("refused") else 0) or 0) > 0})
    conf = confluence(kinds, KINDS)
    # ⚠⚠ HOW MANY DISTINCT SABOTAGES ARE UNDER THAT n — the repetition check.
    # Wilson tightens with n and cannot tell 83 independent looks from ONE attack applied 83
    # times. MEASURED 2026-09-04: `printer.stream` banked 83/83 -> 0.9558, and 80 of the 83 were
    # TWO attack functions applied to 40 reels each. On its five distinct attacks the identical
    # evidence scores 0.5655. Nothing was faked and every refusal was real — the SCORE was bought
    # by looping, which is the same objection already standing against prune.arm ("one proof
    # wearing four hats") at forty hats. `None` = the harness did not say how many, which is NOT
    # the same as one, and must never be read as a clean bill. [[unknown-stays-unknown]]
    # ⚠⚠ CLAIMS THAT WERE DECLARED AND NEVER EXERCISED. A banked row with n == 0 is a harness
    # saying "I own this axis and I could not run it". Zero attempts cannot move a Wilson bound, so
    # without this the axis vanishes and the lock scores on its remaining claims. See INCOMPLETE.
    # ⚠ WITHDRAWN AXES ARE EXCLUDED FROM `blind` AND REPORTED SEPARATELY. Both bank n == 0, and
    # folding them together told a reader "3 claims were never exercised at all" about three axes
    # that WERE exercised, found to be identity assertions, and deliberately retired (REG-600).
    blind = sorted({str(r.get("ref") or r.get("note") or "?")[:60]
                    for r in mine
                    if int(r.get("n", 1) or 0) == 0 and not r.get("withdrawn")})
    withdrawn = sorted({str(r.get("ref") or "?")[:60]
                        for r in mine if r.get("withdrawn")})
    _atk = [r.get("attacks") for r in mine if isinstance(r.get("attacks"), int)]
    attacks = sum(_atk) if _atk else None
    out = {"lock": lock, "surface": spec["surface"], "acts": spec["acts"],
           "attacks": attacks,
           # REG-547 shape law — present on every path, so "no blind claim" and "never looked for
           # one" cannot render identically.
           "blindClaims": blind,
           # REG-547 shape law again: present on every path, so "nothing was retired" and "nobody
           # asked" cannot render identically.
           "withdrawnClaims": withdrawn,
           "wilsonByAttack": (None if not attacks else round(wilson_lower(min(k, attacks), attacks), 4)),
           "repetition": (None if not attacks else round(float(n) / attacks, 1)),
           "k": k, "n": n, "kinds": kinds, "confluence": conf,
           "bar": spec["bar"], "kindsBar": spec["kinds_bar"], "after": list(spec["after"])}
    if n == 0:
        out["wilson"] = None
        out["state"] = UNPROVEN
        # NOBODY LOOKED and THERE IS NOTHING TO LOOK AT are different facts. Both leave n=0 and
        # neither is a failure, but only one of them is waiting on work.
        if spec.get("unprovable"):
            out["provable"] = False
            out["why"] = ("this cannot be proven by sabotage and never will be: %s. n=0 here is "
                          "the correct and final state, not a harness anyone still owes."
                          % spec["unprovable"])
        else:
            out["provable"] = True
            out["why"] = ("no sabotage has been attempted against this surface's guards, so there "
                          "is no evidence in either direction. That is not a failure.")
        # ⚠ REG-547 SHAPE LAW — the key exists on EVERY path, including this one. A row that
        # carries `hardeningGap` only when there is a gap makes "no gap" and "never computed"
        # render identically, and a consumer would have to know which it was looking at.
        out["hardeningGap"] = _hardening_gap(None, conf, kinds, n, k)
        return out
    w = wilson_lower(k, n)
    out["wilson"] = round(w, 4)
    # the tier above the bar — reported on every row so a surface can show how far past it is
    out["hardBar"] = HARD_BAR
    out["hardKindsBar"] = HARD_KINDS_BAR
    out["hardened"] = bool(w >= HARD_BAR and conf >= HARD_KINDS_BAR)
    # what this surface still owes the tier above it, named on every scored row — see
    # _hardening_gap. Computed here so LOCKED rows carry it too: a lock below its own bar is
    # also below HARDENED, and hiding that until it opens would make the ladder look shorter
    # than it is.
    out["hardeningGap"] = _hardening_gap(w, conf, kinds, n, k)
    if w < spec["bar"]:
        out["state"] = LOCKED
        out["why"] = ("%d of %d sabotages were refused; the Wilson lower bound is %.3f against a "
                      "bar of %.3f" % (k, n, w, spec["bar"]))
    elif conf < spec["kinds_bar"]:
        out["state"] = LOCKED
        out["why"] = ("the score clears (%.3f) but the evidence is too alike: kinds %s score %.2f "
                      "against %.2f. Wilson counts how many looks agreed, never whether they were "
                      "independent." % (w, kinds or "[]", conf, spec["kinds_bar"]))
    else:
        # ⚠ THE LADDER, NOT A BOOLEAN. "Wilson score" here is his nickname for the WHOLE standard
        # — the lower bound AND the confluence — so the tier above the bar is a real STATE that
        # every surface can reach, not a flag riding alongside OPEN. Clearing the bar is the floor;
        # HARDENED says a surface kept going and did it with independent kinds.
        out["state"] = HARDENED if out.get("hardened") else OPEN
        out["why"] = ("%d of %d sabotages refused · wilson %.3f >= %.3f · kinds %s = %.2f >= %.2f"
                      % (k, n, w, spec["bar"], kinds, conf, spec["kinds_bar"]))
    # ⚠⚠ LAST, AND IT OUTRANKS OPEN. A lock cannot be called proven while one of the axes its own
    # harness declared has never been exercised — the score simply never saw that axis. Applied
    # after the ladder so it also refuses to let HARDENED stand on an untested claim.
    # ⚠ IT IS A REPORT, NOT A GATE. `may()` is still never called and no button is blocked; what
    # changes is that the badge stops saying proven. [[unknown-stays-unknown]]
    if blind:
        out["state"] = INCOMPLETE
        out["why"] = ("%d of %d ATTEMPTED sabotages were refused, but %d claim(s) this harness "
                      "declared were never exercised at all (%s). Zero attempts cannot move a "
                      "Wilson bound, so that axis is MISSING from the score rather than failing "
                      "it — the number below is about the other claims only. Nothing is blocked; "
                      "the badge just stops saying proven."
                      % (k, n, len(blind), ", ".join(blind)))
    return out


def _hardening_gap(w, conf, kinds, n, k):
    """What does this surface still OWE the HARDENED tier? -> dict, always the same shape.

    ⚠⚠ HARDENED WAS A TIER NOTHING COULD REACH AND NOTHING EXPLAINED. Measured 2026-09-04 across
    the whole table: **14 of 15 locks OPEN, 0 HARDENED**, and every `why` on those rows recited
    only the bar it had already cleared. A surface could sit one evidence-kind short of his own
    HARDENING stamp forever and the report would never say the word. An unreachable tier that
    gives no account of itself is indistinguishable from a broken one. [[unknown-stays-unknown]]

    ⚠ IT NAMES WHAT IS MISSING; IT NEVER LOWERS ANYTHING. The bars are his. This computes the
    shortfall and the CHEAPEST HONEST combination of kinds that would close it — and a kind is
    earned by doing that work, never by relabelling evidence already banked. Calling a fixture
    `live`, or an agreement a `sabotage`, would clear this gap on paper and prove nothing, which
    is the exact failure the confluence bar exists to stop.

    ⚠ THE SABOTAGE COUNT IS REAL ARITHMETIC, NOT AN ESTIMATE. `wilson_lower` rises with n at a
    fixed k/n, so "how many more consecutive refusals clear HARD_BAR" has one answer and it is
    computed here by asking, never by a rule of thumb.
    """
    out = {"hardened": bool(w is not None and w >= HARD_BAR and conf >= HARD_KINDS_BAR),
           "wilsonShort": None, "kindsShort": None, "moreRefusalsNeeded": None,
           "kindsWouldClose": [], "why": ""}
    if w is None:
        out["why"] = ("nothing has been attempted, so there is no gap to measure — an unmeasured "
                      "distance is not a short one")
        return out
    if out["hardened"]:
        out["why"] = "already HARDENED"
        return out

    if w < HARD_BAR:
        out["wilsonShort"] = round(HARD_BAR - w, 4)
        # how many MORE refused sabotages would clear it, asked rather than guessed
        if k == n:
            nn = n
            while nn < n + 500:
                nn += 1
                if wilson_lower(nn, nn) >= HARD_BAR:
                    out["moreRefusalsNeeded"] = nn - n
                    break
    if conf < HARD_KINDS_BAR:
        out["kindsShort"] = round(HARD_KINDS_BAR - conf, 4)
        have = set(kinds or ())
        missing = sorted((kd for kd in KINDS if kd not in have),
                         key=lambda kd: -KINDS[kd])
        # the smallest set of ABSENT kinds that closes the confluence gap, largest weight first
        run, chosen = conf, []
        for kd in missing:
            if run >= HARD_KINDS_BAR:
                break
            chosen.append(kd)
            run += KINDS[kd]
        out["kindsWouldClose"] = chosen if run >= HARD_KINDS_BAR else []

    bits = []
    if out["wilsonShort"] is not None:
        bits.append("wilson %.3f is %.3f short of %.3f%s"
                    % (w, out["wilsonShort"], HARD_BAR,
                       ("" if out["moreRefusalsNeeded"] is None else
                        " (%d more refused sabotage(s) would clear it)"
                        % out["moreRefusalsNeeded"])))
    if out["kindsShort"] is not None:
        bits.append("kinds %.2f is %.2f short of %.2f%s"
                    % (conf, out["kindsShort"], HARD_KINDS_BAR,
                       (" — adding %s would close it"
                        % " + ".join("%s (%.1f)" % (kd, KINDS[kd])
                                     for kd in out["kindsWouldClose"])
                        if out["kindsWouldClose"] else
                        " — NO combination of the remaining kinds can close it")))
    out["why"] = ("owes HARDENED: " + "; ".join(bits)) if bits else ""
    return out


def may(lock):
    """May this surface act right now? -> (bool, why)

    THE ORDER IS CHECKED FIRST. A lock late in his chain reports its blocked prerequisite rather
    than its own score, so a high number is never mistaken for "nearly there".
    """
    # a route scores on the SAME arithmetic as a valve — one table lookup, one score()
    spec = LOCKS.get(lock) or ROUTES.get(lock)
    if not spec:
        return False, "no such lock is declared — an undeclared surface is never permitted"
    rows, why = _rows()
    if rows is None:
        return False, "UNKNOWN: %s. An unreadable proof queue fails CLOSED." % why
    for pre in spec["after"]:
        s = score(pre, rows)
        if s.get("state") not in (OPEN, HARDENED):
            return False, ("blocked upstream: %s is %s — %s. Proving this surface in isolation "
                           "proves nothing about what feeds it." % (pre, s.get("state"), s.get("why")))
    s = score(lock, rows)
    # HARDENED is strictly stronger than OPEN — a surface that exceeded the bar may certainly act
    return (s.get("state") in (OPEN, HARDENED)), s.get("why")


def report():
    """Every lock, for a surface that must show its work. -> dict"""
    rows, why = _rows()
    if rows is None:
        return {"ok": False, "why": why,
                "locks": [{"lock": k, "state": UNKNOWN, "why": why} for k in sorted(LOCKS)]}
    # ⚠ ROUTES RIDE THE SAME REPORT, not a second one. The heart reads ONE self_arming.report(),
    # so a route appears beside the valves in the same four words and the corroborator sees them
    # as siblings — which is what he asked for: "all connected to the heart of the console
    # obviously.. so its all communicating and intertwined and integrated together properly".
    out = [score(k, rows) for k in sorted(LOCKS)]
    out += [dict(score(k, rows), kind="route") for k in sorted(ROUTES)]
    return {"ok": True, "locks": out,
            "open": len([x for x in out if x.get("state") in (OPEN, HARDENED)]),
            "hardened": len([x for x in out if x.get("state") == HARDENED]),
            "total": len(out)}


def main(argv):
    rep = report()
    print("SELF-ARMING LOCKS — %s" % ("%d of %d open" % (rep.get("open", 0), rep.get("total", 0))
                                      if rep.get("ok") else "UNREADABLE: " + rep.get("why", "")))
    for l in rep["locks"]:
        w = l.get("wilson")
        print("  %-9s %-20s %s" % (l.get("state"), l.get("lock"),
                                   ("wilson %.3f/%.3f" % (w, l["bar"])) if w is not None
                                   else "no sabotage attempted"))
        print("            %s" % (l.get("why") or ""))
    # a report is not a verdict: exit 0 always, because "nothing is open yet" is the CORRECT
    # state on a fresh tree and must not read as a broken build.
    return 0


if __name__ == "__main__":
    try:
        import console_safe as _cs
        _cs.enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
