#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ATTACKS ON THE VAULT WRITE DOOR, DESIGNED BY A DIFFERENT MODEL FAMILY.

⚠⚠ WHY THIS FILE EXISTS AND WHY ITS KIND IS `cross-family`. `vault.apply` guards *"mules items
between characters"* — the door that WRITES HIS LEDGER. It carried two evidence kinds, `sabotage`
and `live`, for a confluence of 1.70 against a HARDENED bar of 2.50. The honest way to close 0.80
is a genuinely independent third kind, and the one available without spending his money is a
different model family attacking axes I did not think of.

**This is not my attack list rewritten.** `vault_apply` was handed COLD to a non-Anthropic model —
the function body and the minimum context, no hint of what was thought to be strong or weak — and
asked to design concrete proposals that get an uncorroborated or destructive row past the gate.

WHAT CAME BACK, 2026-09-05, and what happened when each was run against the real function:

    A1  {"owned": [], "unsure": [<no evidence>], "throwOut": [...]}   LANDED — gate never consulted
    A3  {"owned": None, ...}                                          LANDED — same hole, new shape
    A2  {"owned": [{"evidence": "not-a-list"}]}                       REFUTED — gate already refused

A1 and A3 found a real hole: the re-gate loop iterated `owned` ONLY, so an uncorroborated row under
`unsure` reached the window check without the gate ever being asked. Measured directly: the gate
refused an uncorroborated `owned` row and did NOT refuse the identical row under `unsure`.

⚠ NOTHING WAS EXPOSED, and the distinction is the finding. The BOARD registers only `owned`
(`control_ui.html` — *"ONLY `owned` can be registered"*), so the row was stopped one station later.
Defence-in-depth held. It was fixed anyway because `vault_apply`'s own v1595 note says why: *"a rule
enforced in one place is a rule with a door beside it."*

⚠⚠ AND THIS IS THE SECOND TIME THE SAME FAMILY CAUGHT THE SAME DOOR. The v1595 comment records:
*"Grok's third-eye pass on v1594 flagged exactly this, and it was right."* A second family earns
its place by attacking along axes I do not — not by being right more often. [[grok-second-eye]]

⚠ SAFE BY CONSTRUCTION. Every attempt carries evidence that CANNOT clear the gate, so the only
outcome the door can produce is a refusal. No attempt is ever a corroborated row, so none can
write. The proposals are built here and passed as arguments; nothing touches a live store, opens a
window, or spends a token. [[feedback-fixtures-never-touch-live-data]]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

#: what a REFUSAL looks like: the door consulted the gate and the gate said no.
_GATE_SAID_NO = "do not clear the gate"


def _refused(rep):
    """Did the write door refuse on the GATE's authority? -> bool

    ⚠ NOT merely `ok is False`. Every one of these proposals would also be stopped later by "the
    board window is not open", and counting THAT as a refusal would bank the absence of a window
    as evidence about the gate — an agreement wearing a refusal's clothes, which is REG-600's
    exact shape. Only the gate's own sentence counts.
    """
    if not isinstance(rep, dict) or rep.get("ok") is not False:
        return False
    return _GATE_SAID_NO in str(rep.get("why") or "")


def _apply(prop):
    import control_app as ca
    try:
        return ca.vault_apply(proposal=prop)
    except Exception as exc:
        return {"ok": False, "why": "raised: %s" % type(exc).__name__}


#: evidence that cannot clear KEEP_MIN_WITNESSES — the payload every attack carries.
_BARE = []


def _attempt_unsure_bypasses_the_regate(n=8):
    """A1 — the strongest of the three. `owned` empty, an uncorroborated row under `unsure`."""
    caught = 0
    for i in range(n):
        r = _apply({"owned": [], "throwOut": [{"name": "Legendary Sword %d" % i}],
                    "unsure": [{"name": "Dragon Scale %d" % i, "evidence": _BARE}]})
        if _refused(r):
            caught += 1
    return n, caught


def _attempt_owned_is_None_not_absent(n=8):
    """A3 — the same hole through a different shape. `prop.get("owned") or []` makes None and []
    identical to the loop, while the later 'must have owned or unsure' check still passes."""
    caught = 0
    for i in range(n):
        r = _apply({"owned": None, "throwOut": [{"name": "Banned Mount %d" % i}],
                    "unsure": [{"name": "Suspicious Relic %d" % i, "evidence": _BARE}]})
        if _refused(r):
            caught += 1
    return n, caught


def _attempt_evidence_is_the_wrong_type(n=8):
    """A2 — REFUTED as a hole, kept as an attack. The gate already refused a string where a list
    of sightings belongs. Keeping it banked records that the axis was TRIED, which is the half of
    an audit that usually goes missing."""
    caught = 0
    for i in range(n):
        r = _apply({"owned": [{"name": "Fake Item %d" % i, "evidence": "not-a-list"}],
                    "unsure": [], "throwOut": []})
        if _refused(r):
            caught += 1
    return n, caught


def _attempt_a_corroborated_row_is_NOT_refused(n=4):
    """⚠⚠ THE BASELINE, AND IT IS COUNTED THE OTHER WAY ROUND ON PURPOSE.

    A guard that refuses everything is not a guard, and three attacks that all pass would look
    identical whether the gate worked or was simply broken shut. This attempts a row that SHOULD
    clear — three independent witnesses at 0.9 — and counts the door's refusal to refuse.

    It is deliberately NOT banked (see `prove`): banking it would count correct acceptance as a
    sabotage refusal, which is REG-600's defect pointing the other way.
    """
    ok = 0
    ev = [{"session": "s%d" % k, "frame": "f%d.jpg" % k, "conf": 0.9} for k in range(3)]
    for i in range(n):
        r = _apply({"owned": [], "throwOut": [],
                    "unsure": [{"name": "Real Find %d" % i, "evidence": ev}]})
        if not _refused(r):
            ok += 1
    return n, ok


ATTACKS = (
    ("unsure-bypass", _attempt_unsure_bypasses_the_regate,
     "an uncorroborated row under `unsure` reached the write path without the gate being asked"),
    ("owned-is-none", _attempt_owned_is_None_not_absent,
     "`owned: None` skipped the re-gate loop while still satisfying the has-something check"),
    ("evidence-type", _attempt_evidence_is_the_wrong_type,
     "a string where a list of sightings belongs — REFUTED, the gate already refused it"),
)


def prove():
    rows, n, k = [], 0, 0
    for name, fn, what in ATTACKS:
        try:
            an, ak = fn()
        except Exception as e:
            an, ak = 1, 0
            what = "%s — the attempt itself raised (%s)" % (what, str(e)[:60])
        rows.append({"attack": name, "n": an, "k": ak, "what": what, "leaks": ak < an})
        n += an
        k += ak
    bn, bk = _attempt_a_corroborated_row_is_NOT_refused()
    return {"rows": rows, "n": n, "k": k, "baselineN": bn, "baselineOk": bk,
            "baselineHolds": bk == bn,
            "why": "%d of %d attacks refused; baseline %d/%d corroborated rows accepted"
                   % (k, n, bk, bn)}


def bank_into_proof_queue(rep):
    """⚠ ONLY the attacks are banked, and only when the BASELINE holds.

    If a corroborated row is also refused, the door is broken shut and its refusals mean nothing —
    banking them would record a jammed gate as a proven one.
    """
    import self_arming as SA
    if not rep.get("baselineHolds"):
        return ["REFUSED TO BANK: the baseline failed — a corroborated row was also refused, so "
                "these refusals prove a jammed door, not a working one"]
    banked = []
    for r in rep["rows"]:
        try:
            # ⚠ ONE ROW = ONE ATTACK; `n` is how many times it was applied. REG-598.
            SA.bank("vault.apply", "cross-family", "vault_apply_crossfamily",
                    n=r["n"], k=r["k"], attacks=1,
                    ref=str(r["attack"]), note=str(r["what"])[:200])
            banked.append("%s %d/%d" % (r["attack"], r["k"], r["n"]))
        except ValueError as e:
            banked.append("%s REFUSED (%s)" % (r["attack"], str(e)[:70]))
    return banked


def main(argv):
    rep = prove()
    print("\nVAULT WRITE DOOR — attacks designed by a different model family\n")
    for r in rep["rows"]:
        print("  %-15s %d/%d  %s" % (r["attack"], r["k"], r["n"],
                                     "LEAKS" if r["leaks"] else "refused"))
        print("                  %s" % r["what"])
    print("\n  baseline: %d/%d corroborated rows accepted %s"
          % (rep["baselineOk"], rep["baselineN"],
             "" if rep["baselineHolds"] else "  <- THE DOOR IS JAMMED SHUT"))
    print("  %s · %s\n" % ("LEAKS" if rep["k"] < rep["n"] else "PROVEN", rep["why"]))
    if "--bank" in argv:
        for line in bank_into_proof_queue(rep):
            print("  banked: %s" % line)
    return 0 if (rep["k"] == rep["n"] and rep["baselineHolds"]) else 1


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
