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

⚠ AND IMPORTING THE CONSOLE DOES NOT START THE DELETER — checked rather than assumed, because if
it did, merely importing it here would arm an unattended irreversible loop. Measured by AST:
`main()` is the only module-level call and it sits under `if __name__ == "__main__"`;
`start_background_watchers()`, which owns both `_prune_loop` and `_retention_loop`, has no call
site that runs on import. (My first version of that check walked INTO every function body and
reported 50 thread starts — an artifact of the walk, not of the module. The count was the tell.)

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


CLAIMS = (
    ("offspelling", "every spelling of OFF holds the deleter — v2082 matched the byte \"0\" alone "
                    "and every other spelling armed it", _attempt_offspelling),
    ("worldunknown", "footage is not deleted while the board's world is unconfirmed",
     _attempt_worldunknown),
    ("worldraises", "a world check that cannot answer must refuse, not fail open",
     _attempt_worldraises),
    ("worldshapeless", "a drift answer of the wrong shape, or missing its state, is not permission",
     _attempt_worldshapeless),
)


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
    return rows


def bank_into_proof_queue(rows):
    """Bank each claim's aggregate under prune.arm. -> {"banked", "skipped"}"""
    import self_arming as _sa
    banked, skipped = [], []
    for r in rows:
        n, k = r.get("attempts"), r.get("caught")
        if n is None or k is None:
            skipped.append("%s (%s — the probe could not answer, so it banks nothing)"
                           % (r.get("claim"), r.get("state")))
            continue
        try:
            _sa.bank("prune.arm", "sabotage", "prune_wilson", n=n, k=k,
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
    sys.exit(main(sys.argv[1:]))
