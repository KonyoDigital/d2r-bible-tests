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
        "after": ["vault.sweep_start", "vault.apply"],
    },
}

# the four states, and they are four on purpose
OPEN = "OPEN"
LOCKED = "LOCKED"          # proven, and it did not clear the bar
UNPROVEN = "UNPROVEN"      # n == 0 — nobody has tested it. NOT a failure, NOT a score.
UNKNOWN = "UNKNOWN"        # the ledger could not be read. Fails closed, and says so.


def record(lock, kind, refused, note=""):
    """Append one SABOTAGE ATTEMPT and whether the guard refused. -> dict (the row written)

    `refused` True means the guard went RED for its own reason — that is the SUCCESS here, which
    reads backwards until you remember what is being measured: the ability to say no.
    """
    row = {
        "lock": str(lock), "kind": str(kind), "refused": bool(refused),
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
    # vault_wilson attempts proposals the WRITE door must reject — v1595's re-gate, which
    # returns before the board is ever asked. It never applies anything: every row it hands
    # in carries an empty evidence list, so it fails the witness gate by construction.
    # ⚠ It is declared for vault.apply ONLY. vault.forget has no refusal path at all (7
    # lines, one return, always ok), so nothing can prove it by sabotage and nothing here
    # pretends to.
    "vault_wilson": ("vault.apply",),
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
}


def bank(lock, kind, src, n, k, note="", ref=""):
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
    if lock not in LOCKS:
        raise ValueError("no such lock is declared: %r" % (lock,))
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
        "note": str(note or "")[:400], "ts": int(time.time() * 1000),
    }
    with io.open(_ledger_path(), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def _fold(rows):
    """Reduce banked aggregates to one row per (lock, kind, src), newest wins. -> list

    Single-attempt rows (no `src`) are never folded — each one is its own event and they
    accumulate, which is what record() means.
    """
    out, latest = [], {}
    for r in rows:
        src = r.get("src")
        if not src:
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
                if isinstance(r, dict):
                    out.append(r)
    except Exception as e:
        return None, "%s could not be read: %s" % (os.path.basename(p), e)
    return out, ""


def score(lock, rows=None):
    """The arithmetic for ONE lock. -> dict

    Never returns a wilson figure when n == 0. `wilson: None` means nobody looked; `0.0` would be
    a measurement nobody took. [[unknown-stays-unknown]]
    """
    spec = LOCKS.get(lock)
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
    out = {"lock": lock, "surface": spec["surface"], "acts": spec["acts"],
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
        return out
    w = wilson_lower(k, n)
    out["wilson"] = round(w, 4)
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
        out["state"] = OPEN
        out["why"] = ("%d of %d sabotages refused · wilson %.3f >= %.3f · kinds %s = %.2f >= %.2f"
                      % (k, n, w, spec["bar"], kinds, conf, spec["kinds_bar"]))
    return out


def may(lock):
    """May this surface act right now? -> (bool, why)

    THE ORDER IS CHECKED FIRST. A lock late in his chain reports its blocked prerequisite rather
    than its own score, so a high number is never mistaken for "nearly there".
    """
    spec = LOCKS.get(lock)
    if not spec:
        return False, "no such lock is declared — an undeclared surface is never permitted"
    rows, why = _rows()
    if rows is None:
        return False, "UNKNOWN: %s. An unreadable proof queue fails CLOSED." % why
    for pre in spec["after"]:
        s = score(pre, rows)
        if s.get("state") != OPEN:
            return False, ("blocked upstream: %s is %s — %s. Proving this surface in isolation "
                           "proves nothing about what feeds it." % (pre, s.get("state"), s.get("why")))
    s = score(lock, rows)
    return (s.get("state") == OPEN), s.get("why")


def report():
    """Every lock, for a surface that must show its work. -> dict"""
    rows, why = _rows()
    if rows is None:
        return {"ok": False, "why": why,
                "locks": [{"lock": k, "state": UNKNOWN, "why": why} for k in sorted(LOCKS)]}
    out = [score(k, rows) for k in sorted(LOCKS)]
    return {"ok": True, "locks": out,
            "open": len([x for x in out if x.get("state") == OPEN]), "total": len(out)}


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
