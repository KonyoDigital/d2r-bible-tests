"""A2 · step 4 — the deleter: can `retention_may_act()` refuse when it must?

`prune.arm` is the last of the five locks with any evidence still to gather. `vault.forget` cannot
be proven at all — it is 8 lines, 4 statements, 0 raises and 0 guarded exits, so there is no
refusal path to attempt anything against — which leaves this one.

⚠⚠ THIS HARNESS NEVER ARMS OR RUNS A PRUNE, and the shape of it is what guarantees that rather
than a promise in a comment. It calls exactly one function, `retention_may_act()`, whose own
docstring is *"Decides; never acts."* It never touches `apply_plan`, `_prune_once`, `_prune_loop`,
`_retention_loop`, `os.remove`, `unlink` or `rmtree`, and every value it ever writes to
`TV_AUTO_PRUNE` is a spelling of OFF or the empty string. There is no code path here that deletes
a byte, and `tv/test_prune_wilson.py` asserts that by reading this file's own source.

⚠ IMPORTING THE CONSOLE DOES NOT START THE DELETER — and the first version of this paragraph
OVERSTATED that. The v2472 review disproved it by re-deriving the measurement the paragraph told
the reader to trust, which is the whole point of writing measurements down. Corrected here rather
than quietly edited:

  WHAT I WROTE: "main() is the only module-level call". FALSE. An AST walk over control_app's
  module body finds 119 calls outside the `__main__` guard; even the charitable reading — bare
  call statements only — leaves 7, including `_beacon_state_load()` at line 1352 and `_log_root()`
  at 107. The transitive `import tv_diablo` additionally runs `os.makedirs(_VISION_CWD,
  exist_ok=True)`, so IMPORTING THE CONSOLE DOES WRITE TO DISK.

  WHAT IS TRUE, and is the property this harness actually needs: `main()` is the only call under
  the `__main__` guard, and `start_background_watchers()` — which owns both `_prune_loop` and
  `_retention_loop` — has no call site that runs on import. So importing does not start the
  DELETER. That is not the same statement as "nothing happens on import", and the difference is
  exactly the kind a reader would have accepted without re-deriving.

(My first attempt at that check also walked INTO every function body and reported 50 thread starts
— an artifact of the walk. The count was the tell, twice.)

WHAT IS BEING SABOTAGED, and why these four:

  offspelling  — v2082's scar, verbatim: the switch matched the exact byte "0" and nothing else, so
                 `off`, `false`, `no`, `OFF`, and "0" with a trailing space ALL ARMED an unattended
                 deleter. Measured then on six fixture reels: "0" held all six, every other
                 spelling deleted. This re-attempts every spelling.
  worldunknown — the board's world must be confirmed before footage belonging to it is deleted.
  worldraises  — if the world CANNOT be checked, the answer is no. A guard that fails open on its
                 own exception is worse than no guard, and this one's siblings failed open.
  worldshapeless — the drift check returning something that is not a dict, or a dict with no state,
                 must also refuse. An absent key is not a pass. [[unknown-stays-unknown]]

THE THREE STATES STAY THREE, as in hover_wilson and sweep_wilson: LEAKS (a state that MUST refuse
was accepted) is the only failure. UNPROVEN is a measurement nobody has taken, and it is not a
score of zero.

⚠ THIS ALONE CANNOT OPEN THE LOCK, ON PURPOSE. `prune.arm` carries `kinds_bar 1.8` and sabotage
weighs 1.0, so a perfect sabotage record still leaves the deleter shut. That is the design saying
the one door with no undo may not open on a single kind of look. Whatever this banks, the lock
stays closed until a SECOND kind of evidence exists. Said out loud in main() rather than left for
someone to discover from a bar that will not move.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

#: Every spelling of OFF the switch accepts, plus the whitespace and case variants that once did
#: NOT hold. Each is one sabotage attempt: the deleter must refuse on all of them.
OFF_SPELLINGS = ("0", "off", "false", "no", "none", "never",
                 "OFF", "False", "No", "NONE", "Never", "Off",
                 " 0 ", "0\t", " off", "FALSE ", "  no  ", "NEVER")


class _Env(object):
    """Set TV_AUTO_PRUNE for one attempt and always put it back.

    Restoring in `finally` is not enough on its own — the ORIGINAL may have been absent, and
    setting it to "" is a different state from unset. Both are restored exactly.
    """

    def __init__(self, value):
        self.value = value
        self.had = "TV_AUTO_PRUNE" in os.environ
        self.was = os.environ.get("TV_AUTO_PRUNE")

    def __enter__(self):
        # ⚠ THE REFUSAL IS HERE, NOT IN A COMMENT. Every call site passes a variable, so nothing
        # STATIC can prove the value is a spelling of OFF — its own guard said so by going red on
        # `<non-literal>`. Reading the source could never settle it, so the harness enforces it at
        # the moment of writing instead: an arming value raises rather than reaching the switch.
        # This is the difference between promising not to arm the deleter and being unable to.
        if self.value is not None and self.value != "" and self.value not in OFF_SPELLINGS:
            raise ValueError(
                "prune_wilson refused to set TV_AUTO_PRUNE=%r — it is not a spelling of OFF. "
                "This harness sabotages the one door with no undo and may only ever write a "
                "value that HOLDS it." % (self.value,))
        if self.value is None:
            os.environ.pop("TV_AUTO_PRUNE", None)
        else:
            os.environ["TV_AUTO_PRUNE"] = self.value
        return self

    def __exit__(self, *a):
        if self.had:
            os.environ["TV_AUTO_PRUNE"] = self.was
        else:
            os.environ.pop("TV_AUTO_PRUNE", None)
        return False


def _refused(r):
    """`retention_may_act()` -> (bool, why). Refusal is the False arm, WITH a reason.

    A bare False carrying no reason is not counted as a refusal: the console has to be able to say
    why it did not delete, and "it just said no" is the shape a stub returns.
    """
    if not isinstance(r, tuple) or len(r) != 2:
        return False
    ok, why = r
    return (ok is False) and bool(str(why or "").strip())


def _attempt_offspelling(ca, n=None):
    """Every spelling of OFF must hold the deleter. v2082's exact scar, re-run."""
    caught = 0
    spellings = OFF_SPELLINGS if n is None else OFF_SPELLINGS[:n]
    for spelling in spellings:
        with _Env(spelling):
            try:
                if _refused(ca.retention_may_act()):
                    caught += 1
            except Exception:
                # a guard that raises has not refused; it has failed to answer
                pass
    return len(spellings), caught


def _with_drift(ca, fake, n):
    """Swap `board_identity_drift` for one that returns/raises `fake`, and count refusals.

    TV_AUTO_PRUNE is set to "" for these — NOT to an off-spelling — so the switch check above
    cannot short-circuit and hand back a refusal that has nothing to do with the world check. A
    guard that passes for the wrong reason is the failure this repo has the most scars from.
    """
    if not hasattr(ca, "board_identity_drift"):
        return 0, 0
    orig = ca.board_identity_drift
    caught = 0
    try:
        for _ in range(n):
            ca.board_identity_drift = fake
            with _Env(""):
                try:
                    if _refused(ca.retention_may_act()):
                        caught += 1
                except Exception:
                    pass
    finally:
        ca.board_identity_drift = orig
    return n, caught


def _attempt_worldunknown(ca, n=8):
    """The board's world is not confirmed — nothing belonging to it may be deleted."""
    return _with_drift(ca, lambda *a, **k: {"state": "stale", "why": "sabotage: world not ok"}, n)


def _attempt_worldraises(ca, n=8):
    """The world could not be checked at all. The answer to an unanswerable question is no."""
    def _boom(*a, **k):
        raise RuntimeError("sabotage: the world check itself failed")
    return _with_drift(ca, _boom, n)


def _attempt_worldshapeless(ca, n=8):
    """A non-dict, and a dict with no `state`. An absent key is not permission."""
    shapes = [None, "ok", 1, [], {}, {"why": "no state key"}, {"state": None}, {"state": ""}]
    if not hasattr(ca, "board_identity_drift"):
        return 0, 0
    orig = ca.board_identity_drift
    caught = 0
    try:
        for i in range(n):
            shape = shapes[i % len(shapes)]
            ca.board_identity_drift = (lambda s: (lambda *a, **k: s))(shape)
            with _Env(""):
                try:
                    if _refused(ca.retention_may_act()):
                        caught += 1
                except Exception:
                    pass
    finally:
        ca.board_identity_drift = orig
    return n, caught


#: ⚠⚠ ATTACKS A DIFFERENT MODEL FAMILY DESIGNED, NOT ONES I THOUGHT OF. This is the whole reason
#: `prune.arm` carries kinds_bar 1.8 against sabotage's 1.0: every case above came out of MY reading
#: of this function, and forty-two of my own attempts agreeing with each other is one instrument
#: agreeing with itself, however high the Wilson score climbs.
#:
#: These four were produced by handing `retention_may_act` COLD to grok-4-1 — no hint of what it
#: should find, no mention that anything had ever been tested — and asking it to design attacks that
#: would make the deleter say yes when it must say no. THREE REFUSED IMMEDIATELY and ONE LEAKED:
#:
#:     TV_AUTO_PRUNE="\u200b0"    ARMED   ⚠ a zero-width space before a valid OFF value
#:     TV_AUTO_PRUNE="\xa00ff"    held    (\xa0 IS stripped by str.strip; its prediction was wrong)
#:     a UserDict, not a dict     held    (it predicted this would pass; isinstance is False, so
#:                                        _st is None, so the guard refuses — the SAFE direction)
#:     state "оk" (Cyrillic о)    held    (it predicted a pass; a spoofed state is not "ok", refuse)
#:
#: So two of its four predictions were backwards, and the one that landed was real and is now
#: fixed (v2501). Both facts belong here: a second family is worth having because it attacks along
#: axes I do not, NOT because it is more often right. [[grok-second-eye]]
CROSS_FAMILY = (
    ("zero-width", "\u200b0"),        # invisible char before a valid OFF value
    ("nbsp", "\xa0off"),
    ("typo", "offf"),                 # the comment above says "a typo is not permission"
    ("plain-word", "disabled"),
    ("transposed", "flase"),
    ("garbage", "xyzzy"),
)


def _attempt_crossfamily(ca, n=None, permit_all=False):
    """Values a DIFFERENT FAMILY expected to defeat this switch. -> (attempted, refused)

    Every one of these is a value a person could plausibly have meant as OFF, or typed by mistake.
    The switch's own comment claims "A typo is not permission"; until v2501 a typo WAS permission,
    because the unrecognised arm was the permissive one.

    ⚠ The world guard is forced to "ok" so each case is tested on the SWITCH's own axis — a case
    that only refuses because a different guard caught it has not tested the thing it names.

    ⚠⚠ IT RUNS IN A CHILD PROCESS, AND THE HARNESS'S OWN INTERLOCK IS WHY. `_Env` REFUSES to
    write any value that is not a spelling of OFF — because a harness that can set an ARMING value
    in this process is a harness that can arm a real deleter, whatever its docstring promises. My
    first cut of these cases went straight into `_Env` and was refused by it:

        prune_wilson refused to set TV_AUTO_PRUNE='\u200b0' — it is not a spelling of OFF.

    That refusal was CORRECT and the interlock is not weakened to accommodate this. `xyzzy` and
    `flase` are exactly the values that USED to arm the deleter, which is the whole point of
    attempting them — so they are attempted somewhere that has no deleter to arm: a child process
    reading a scratch copy, with TV_STUB=1, which never starts a retention loop.
    """
    import json as _json
    import subprocess as _sp
    cases = CROSS_FAMILY if n is None else CROSS_FAMILY[:n]
    root = os.path.dirname(os.path.abspath(getattr(ca, "__file__", HERE) or HERE))
    prog = (
        "import os,sys,json\n"
        "sys.path.insert(0, %r)\n"
        "os.environ['TV_STUB']='1'\n"
        "import control_app as ca\n"
        "ca.board_identity_drift = lambda *a, **k: {'state':'ok','why':''}\n"
        # ⚠ THE RED PROOF HAS TO REACH WHERE THE CLAIM ACTUALLY RUNS. Every other claim here is
        # proven able to go red by stubbing `retention_may_act` IN THIS PROCESS — and this one is
        # immune to that, because it runs in a child that imports the real module. It was
        # therefore the one claim in the file that could not be shown to fail, which is the exact
        # shape of a guard that measures nothing. The parent passes the flag; the child honours it.
        "if os.environ.get('TV_PW_PERMIT_ALL') == '1':\n"
        "    ca.retention_may_act = lambda *a, **k: (True, 'sabotage: permits anything')\n"
        "out=[]\n"
        "for val in json.loads(sys.argv[1]):\n"
        "    os.environ['TV_AUTO_PRUNE']=val\n"
        "    try:\n"
        "        r=ca.retention_may_act()\n"
        "        ok = isinstance(r,tuple) and len(r)==2 and r[0] is False and bool(str(r[1] or '').strip())\n"
        "    except Exception:\n"
        "        ok=False\n"
        "    out.append(bool(ok))\n"
        "print(json.dumps(out))\n" % (root,)
    )
    env = dict(os.environ)
    env.pop("TV_AUTO_PRUNE", None)          # the CHILD sets it per case; the parent never does
    if permit_all:
        env["TV_PW_PERMIT_ALL"] = "1"
    else:
        env.pop("TV_PW_PERMIT_ALL", None)
    try:
        raw = _sp.check_output([sys.executable, "-c", prog, _json.dumps([v for _l, v in cases])],
                               stderr=_sp.STDOUT, timeout=180, env=env)
        got = _json.loads(raw.decode("utf-8", "replace").strip().splitlines()[-1])
    except Exception:
        # the probe could not answer — UNKNOWN, which banks nothing. Not a score of zero.
        return 0, 0
    return len(cases), sum(1 for x in got if x)


CLAIMS = (
    ("crossfamily", "values a DIFFERENT model family designed to defeat the off-switch are held — "
                    "one of its four landed, and a typo used to be permission",
     _attempt_crossfamily),  # ⚠ runs OUT OF PROCESS; see PERMIT_ALL for how it is proven red
    ("offspelling", "every spelling of OFF holds the deleter — v2082 matched the byte \"0\" alone "
                    "and every other spelling armed it", _attempt_offspelling),
    ("worldunknown", "footage is not deleted while the board's world is unconfirmed",
     _attempt_worldunknown),
    ("worldraises", "a world check that cannot answer must refuse, not fail open",
     _attempt_worldraises),
    ("worldshapeless", "a drift answer of the wrong shape, or missing its state, is not permission",
     _attempt_worldshapeless),
)


def baseline_can_say_yes(ca):
    """CAN this guard say YES at all? -> (bool|None, why)

    ⚠⚠ REG-593 — 48 REFUSALS CANNOT TELL A CORRECT GUARD FROM ONE BROKEN SHUT, AND THIS IS THE
    LOCK HIS RULING TIES ARMING TO. Every axis here asserts a REFUSAL: `_refused()` counts only
    the False arm, and all five claims put the deleter in a state it must say no to. MEASURED by
    replacing `retention_may_act` with a stub hardwired to `(False, "hardwired")` and re-running
    this whole file:

        real guard        attempts 48   caught 48
        hardwired shut    attempts 48   caught 48      <- IDENTICAL

    So `prune.arm`'s 0.926 says *"it correctly says no under 48 kinds of pressure"* and **nothing
    whatever about the yes** — while arming is exactly the act of trusting the yes. An invariant
    that always agrees may be perfect or INERT, and those are indistinguishable until something
    proves the instrument can move. [[regression-guard]] §5

    ⚠ THIS IS A BASELINE, NOT A SIXTH AXIS. It does not add to `attempts` or `caught` and cannot
    raise the score — a control that inflated the number it validates would be worse than none.
    What it does is make the whole verdict conditional: if the guard cannot say yes even when
    every precondition is met, no claim here may read PROVEN.

    ⚠⚠ AND IT DELETES NOTHING, WHICH WAS VERIFIED BEFORE IT WAS WRITTEN. Measured: importing
    `control_app` starts ZERO threads, `_PRUNE_SAFE_TO_RUN` is False, and `retention_may_act`
    contains no `os.remove`/`rmtree`/`unlink` — it DECIDES and never acts. The switch is set inside
    a try/finally and restored, and the two collaborators are patched on the module rather than on
    disk. There is no window in which anything could act on the yes.
    """
    import os
    real_bid = getattr(ca, "board_identity_drift", None)
    real_nif = getattr(ca, "nothing_in_flight", None)
    if real_bid is None or real_nif is None:
        return None, "the console does not expose the collaborators this baseline patches"
    old = os.environ.get("TV_AUTO_PRUNE")
    try:
        ca.board_identity_drift = lambda *a, **k: {"state": "ok"}
        ca.nothing_in_flight = lambda why=None: (True, "nothing in flight (baseline fixture)")
        os.environ["TV_AUTO_PRUNE"] = "1"
        r = ca.retention_may_act()
    except Exception as e:
        return None, "the baseline itself raised (%s), so nothing was established" % str(e)[:80]
    finally:
        ca.board_identity_drift, ca.nothing_in_flight = real_bid, real_nif
        if old is None:
            os.environ.pop("TV_AUTO_PRUNE", None)
        else:
            os.environ["TV_AUTO_PRUNE"] = old
    if not (isinstance(r, tuple) and len(r) == 2):
        return False, "the guard did not answer with (bool, why): %r" % (r,)
    ok, why = r
    if ok is not True:
        return False, ("with EVERY precondition met the guard still refused (%s) — so it may be "
                       "hardwired shut, and all 48 refusals prove nothing about its correctness"
                       % str(why)[:80])
    if not str(why or "").strip():
        return False, "it permitted without saying why, which is the shape a stub returns"
    return True, "it permits when every precondition is met, and says why: %s" % str(why)[:70]


def score():
    """-> [row]. One row per claim, in hover_wilson's exact shape so the console reads them alike."""
    try:
        import confidence
        import control_app as ca
    except Exception as e:
        return [{"claim": c, "what": w, "attempts": None, "caught": None, "wilson": None,
                 "state": "UNKNOWN",
                 "notes": ["the console module would not import (%s), so nothing was attempted — "
                           "that is UNKNOWN, not a pass" % str(e)[:70]]}
                for c, w, _ in CLAIMS]
    rows = []
    for claim, what, fn in CLAIMS:
        notes = []
        try:
            n, k = fn(ca)
        except Exception as e:
            n, k = None, None
            notes.append("the attempt itself raised (%s) — UNKNOWN, and the guard is unmeasured"
                         % str(e)[:90])
        if not n:
            state, wil = ("UNPROVEN" if n == 0 else "UNKNOWN"), None
            if n == 0:
                notes.append("no attempt could be made against this guard, so there is no evidence "
                             "in either direction")
        elif k < n:
            state = "LEAKS"
            wil = confidence.wilson_lower(k, n)
            notes.append("a state the deleter MUST refuse was accepted %d time(s) of %d — and this "
                         "is the door with no undo" % (n - k, n))
        else:
            state, wil = "PROVEN", confidence.wilson_lower(k, n)
        rows.append({"claim": claim, "what": what, "attempts": n, "caught": k,
                     "wilson": wil, "state": state, "notes": notes})

    # ⚠⚠ THE CONTROL, APPLIED LAST AND TO EVERY ROW. See baseline_can_say_yes: a guard hardwired
    # shut scores exactly what the real one does, so PROVEN is not sayable until something shows
    # the instrument can move. This never raises a score; it can only withdraw one.
    can, can_why = baseline_can_say_yes(ca)
    if can is not True:
        for r in rows:
            if r["state"] == "PROVEN":
                r["state"] = "UNPROVEN" if can is False else "UNKNOWN"
            r["notes"].append(
                "BASELINE %s — %s. Every attempt here asserts a REFUSAL, so without this control "
                "a guard that can never say yes scores exactly what a correct one does (measured: "
                "48/48 either way). No claim may read PROVEN on that."
                % ("FAILED" if can is False else "UNKNOWN", can_why))
    else:
        for r in rows:
            r["notes"].append("baseline holds — %s" % can_why)
    return rows


def bank_into_proof_queue(rows):
    """Bank each claim's aggregate under prune.arm. -> {"banked", "skipped"}"""
    import self_arming as _sa
    banked, skipped = [], []
    # ⚠⚠ REG-593, THE SECOND HALF — THE CONTROL REACHED THE REPORT AND NOT THE LEDGER. This banked
    # on `attempts`/`caught` alone and never read `state`, so a guard hardwired shut — every row
    # withdrawn to UNPROVEN by the baseline — would STILL have banked 48/48 into `prune.arm`, and
    # the lock would go on reading OPEN at 0.926 on evidence the harness itself had just disowned.
    # A baseline that gates the printed verdict and not the stored one is a badge, not a control.
    # [[the-unjoined-end]]
    #
    # ⚠ IT REFUSES THE WHOLE RUN, not the individual rows. When the instrument cannot be shown to
    # move, every number it produced is unattributable — including the LEAKS rows, whose k<n would
    # otherwise look like honest bad news from a working probe.
    _failed = [r for r in rows
               if any(str(nt).startswith("BASELINE FAILED") or str(nt).startswith("BASELINE UNKNOWN")
                      for nt in (r.get("notes") or []))]
    if _failed:
        why = next((str(nt) for nt in (_failed[0].get("notes") or [])
                    if str(nt).startswith("BASELINE")), "the baseline did not hold")
        return {"banked": [],
                "skipped": ["ALL %d claim(s) — %s" % (len(rows), why[:200])]}
    for r in rows:
        n, k = r.get("attempts"), r.get("caught")
        if n is None or k is None:
            skipped.append("%s (%s — the probe could not answer, so it banks nothing)"
                           % (r.get("claim"), r.get("state")))
            continue
        try:
            _kind = "cross-family" if r["claim"] == "crossfamily" else "sabotage"
            # ⚠ src stays `prune_wilson` — it is the DECLARED evidence source in PROVES, and
            # bank() folds on (lock, kind, src), so the two kinds already stay apart without
            # inventing a source name the declaration does not know. My first cut appended the
            # claim and every bank was refused: "not a declared evidence source".
            _sa.bank("prune.arm", _kind, "prune_wilson", n=n, k=k,
                     attacks=1,   # ⚠ ONE ROW = ONE ATTACK FUNCTION; `n` is how many times it was
                     # applied. Summing these across rows gives the DISTINCT attack count,
                     # which is what stops a Wilson score being bought by looping one idea
                     # over many inputs. See self_arming.bank() and REG-598.
                     ref=str(r.get("claim")), note=str(r.get("what") or "")[:200])
            banked.append("%s %d/%d" % (r.get("claim"), k, n))
        except ValueError as e:
            skipped.append("%s REFUSED: %s" % (r.get("claim"), str(e)[:120]))
    return {"banked": banked, "skipped": skipped}


def main(argv=None):
    rows = score()
    b = bank_into_proof_queue(rows)
    print("PRUNE WILSON — can the deleter refuse when it must?")
    print("  (this harness never arms or runs a prune; it calls one function that decides "
          "and never acts)\n")
    print("  %-15s %9s %8s %8s  %s" % ("claim", "sabotages", "caught", "wilson", "state"))
    print("  " + "-" * 64)
    for r in rows:
        print("  %-15s %9s %8s %8s  %s" % (
            r["claim"], "?" if r["attempts"] is None else r["attempts"],
            "?" if r["caught"] is None else r["caught"],
            "—" if r["wilson"] is None else ("%.3f" % r["wilson"]), r["state"]))
    print()
    for r in rows:
        for nt in r.get("notes") or []:
            print("  ⚠ %s: %s" % (r["claim"], nt))
    if b["banked"]:
        print("  banked -> prune.arm: " + ", ".join(b["banked"]))
    for s in b["skipped"]:
        print("  not banked: %s" % s)

    # SAY WHAT THIS CANNOT DO, here, where it cannot be missed.
    try:
        import self_arming as _sa
        bar = _sa.LOCKS["prune.arm"]["kinds_bar"]
        one = _sa.KINDS.get("sabotage")
        print("\n  ⚠ SABOTAGE ALONE CANNOT OPEN THIS LOCK, BY DESIGN. prune.arm needs "
              "confluence %.1f\n     and sabotage weighs %.1f, so even a perfect record leaves the "
              "deleter shut until a\n     SECOND kind of evidence exists. That is the one door with "
              "no undo refusing to open\n     on a single kind of look." % (bar, one))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    # ⚠ THE LINE THAT CRASHES IS THE LINE THAT HAS SOMETHING TO SAY. main() prints "⚠ %s: %s" only
    # when a claim carries notes — on LEAKS or UNKNOWN — so a clean run prints fine and the run
    # reporting that the DELETER LEAKED dies with a UnicodeEncodeError on a console that cannot
    # encode U+26A0. Every other wilson harness enables this; this one did not.
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
