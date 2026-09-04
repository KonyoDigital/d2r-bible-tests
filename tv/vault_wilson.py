"""A2 · can the VAULT APPLY refuse when it must? — and why vault.forget cannot be proven this way.

`vault.apply` guards "mules items between characters": the door that WRITES HIS LEDGER. Its bar is
0.722 and it sat UNPROVEN at n=0 because nothing was permitted to feed it.

⚠⚠ THIS HARNESS NEVER APPLIES ANYTHING. Every attempt is a proposal the door MUST reject, and each
one is rejected at the re-gate — v1595's check — which returns BEFORE the board is ever asked. The
only thing counted is whether it refused. There is no attempt here whose success path runs.

⚠ THE ROWS ARE BUILT TO FAIL. Each carries an EMPTY evidence list, so `vault_retro.gate()` refuses
it on witnesses alone. A row that might pass would be a row that might be written into his stash,
and that is not a risk a test may take. [[feedback-fixtures-never-touch-live-data]]

⚠⚠ AND THE FINDING THAT COMES WITH IT: `vault.forget` CANNOT BE PROVEN THIS WAY AT ALL. Measured by
AST — 7 lines, one return, and ZERO refusal paths. It clears the swept memory and always answers
ok. Its own docstring explains why that is correct: "an optimisation he cannot clear is a cage",
and the ledger is rebuildable from the reels. So there is no wrong input for it to catch, and its
lock will sit UNPROVEN forever — not because nobody tried, but because there is nothing to try.
That is a fact about the door, not a gap in the evidence, and inventing a sabotage for it would be
manufacturing proof. [[unknown-stays-unknown]]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _ungated_proposal(n_rows=1):
    """A proposal whose rows carry NO evidence — guaranteed to fail the witness gate."""
    return {"owned": [{"name": "SABOTAGE ROW %d — no evidence, must never be written" % i,
                       "evidence": []} for i in range(n_rows)],
            "unsure": [], "throwOut": []}


def _attempt_ungated(ca, n=8):
    """v1595's re-gate: a hand-supplied proposal is re-checked WHERE THE WRITE HAPPENS."""
    caught = 0
    for i in range(n):
        r = ca.vault_apply(proposal=_ungated_proposal(1 + (i % 3)))
        if isinstance(r, dict) and r.get("ok") is False and "gate" in str(r.get("why", "")).lower():
            caught += 1
    return n, caught


def _attempt_empty(ca, n=8):
    """An empty proposal must not be treated as 'apply whatever the sweep last found'."""
    caught = 0
    for _ in range(n):
        r = ca.vault_apply(proposal={"owned": [], "unsure": [], "throwOut": []})
        if isinstance(r, dict) and r.get("ok") is False:
            caught += 1
    return n, caught


CLAIMS = (
    ("ungated", "a hand-supplied proposal whose rows clear no witness gate must be refused AT THE "
                "WRITE, not only at the sweep", _attempt_ungated),
    ("empty", "an empty proposal must refuse rather than fall through to whatever was last swept",
     _attempt_empty),
)


def score():
    try:
        import confidence
        import control_app as ca
    except Exception as e:
        return [{"claim": c, "what": w, "attempts": None, "caught": None, "wilson": None,
                 "state": "UNKNOWN",
                 "notes": ["the console module would not import (%s) — UNKNOWN, not a pass"
                           % str(e)[:70]]} for c, w, _ in CLAIMS]
    rows = []
    for claim, what, fn in CLAIMS:
        notes = []
        try:
            n, k = fn(ca)
        except Exception as e:
            n, k = None, None
            notes.append("the attempt itself raised (%s) — UNKNOWN, the guard is unmeasured"
                         % str(e)[:90])
        if not n:
            state, wil = ("UNPROVEN" if n == 0 else "UNKNOWN"), None
        elif k < n:
            state = "LEAKS"
            wil = confidence.wilson_lower(k, n)
            notes.append("a proposal the vault MUST refuse was accepted %d time(s) of %d — that is "
                         "a write into his ledger on evidence nothing corroborated" % (n - k, n))
        else:
            state, wil = "PROVEN", confidence.wilson_lower(k, n)
        rows.append({"claim": claim, "what": what, "attempts": n, "caught": k, "wilson": wil,
                     "state": state, "notes": notes})
    return rows


def forget_note():
    """-> str. Why vault.forget carries no sabotage, stated rather than left blank."""
    return ("vault.forget has NO refusal path — 7 lines, one return, always ok. Its docstring says "
            "why that is right: 'an optimisation he cannot clear is a cage', and the ledger is "
            "rebuildable from the reels. There is no wrong input for it to catch, so its lock "
            "stays UNPROVEN by construction. That is a fact about the door, not a gap in the "
            "evidence, and a sabotage invented for it would be manufactured proof.")


def score_live(port=17772, n=8, timeout=6.0):
    """The SAME refusal, asked of the RUNNING console over HTTP. -> row or None

    ⚠ WHY THIS EXISTS AND WHY IT IS A DIFFERENT KIND. `score()` above imports the module and calls
    the function; that is a sabotage, and sabotage is one kind of evidence. vault.apply carries
    kinds_bar 1.3 precisely so that one kind cannot open it — "Wilson counts how many looks agreed,
    never whether they were independent". Asking the LIVE console, over the wire, through the route
    his own UI posts to, is a genuinely different witness: it exercises the routing, the JSON body
    handling and the running process, none of which an import touches.

    ⚠ IT IS STILL THE SAFE ATTEMPT. Every row carries an empty evidence list, so the re-gate
    rejects the proposal before the board is asked. Verified with ONE request before any batch was
    sent: ok False, and the response NAMES the rejected row.

    ⚠ AN UNREACHABLE CONSOLE BANKS NOTHING. Returns None, which the caller reports as UNKNOWN —
    never as a pass. A dead endpoint is an empty seat, not agreement.
    """
    import json as _json
    import urllib.request as _u
    caught, attempted = 0, 0
    body = _json.dumps({"proposal": {"owned": [{"name": "SABOTAGE PROBE — no evidence, must never "
                                                       "be written", "evidence": []}],
                                     "unsure": [], "throwOut": []}}).encode("utf-8")
    for _ in range(n):
        try:
            req = _u.Request("http://127.0.0.1:%d/api/vault_apply" % port, data=body,
                             headers={"Content-Type": "application/json"})
            r = _json.loads(_u.urlopen(req, timeout=timeout).read().decode("utf-8", "replace"))
        except Exception:
            return None                  # unreachable -> UNKNOWN, and nothing is banked
        attempted += 1
        if isinstance(r, dict) and r.get("ok") is False and "gate" in str(r.get("why", "")).lower():
            caught += 1
    if not attempted:
        return None
    import confidence
    return {"claim": "live-ungated", "attempts": attempted, "caught": caught,
            "wilson": confidence.wilson_lower(caught, attempted),
            "state": "PROVEN" if caught == attempted else "LEAKS",
            "what": "the RUNNING console, over its own HTTP route, refuses a proposal whose rows "
                    "clear no witness gate",
            "notes": ([] if caught == attempted else
                      ["the live console ACCEPTED %d of %d proposals it must refuse — that is a "
                       "write into his ledger over the wire" % (attempted - caught, attempted)])}


def bank_into_proof_queue(rows):
    import self_arming as _sa
    banked, skipped = [], []
    for r in rows:
        n, k = r.get("attempts"), r.get("caught")
        if n is None or k is None:
            skipped.append("%s (%s — banks nothing)" % (r.get("claim"), r.get("state")))
            continue
        try:
            _sa.bank("vault.apply", "sabotage", "vault_wilson", n=n, k=k,
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
    # the LIVE witness, banked under its own kind so confluence can see two independent sources
    live = score_live()
    live_note = ""
    if live is None:
        live_note = ("the running console could not be reached, so there is no LIVE witness — "
                     "UNKNOWN, not a pass, and nothing was banked for it")
    else:
        try:
            import self_arming as _sa
            _sa.bank("vault.apply", "live", "vault_live", n=live["attempts"], k=live["caught"],
                     attacks=1,   # ⚠ ONE ROW = ONE ATTACK FUNCTION; `n` is how many times it was
                     # applied. Summing these across rows gives the DISTINCT attack count,
                     # which is what stops a Wilson score being bought by looping one idea
                     # over many inputs. See self_arming.bank() and REG-598.
                     ref=live["claim"], note=live["what"][:200])
            live_note = ("banked LIVE -> vault.apply: %s %d/%d"
                         % (live["claim"], live["caught"], live["attempts"]))
        except ValueError as e:
            live_note = "live NOT banked: %s" % str(e)[:140]
    print("VAULT WILSON — can the write door refuse when it must?\n")
    print("  %-9s %9s %8s %8s  %s" % ("claim", "sabotages", "caught", "wilson", "state"))
    print("  " + "-" * 58)
    for r in rows:
        print("  %-9s %9s %8s %8s  %s" % (
            r["claim"], "?" if r["attempts"] is None else r["attempts"],
            "?" if r["caught"] is None else r["caught"],
            "—" if r["wilson"] is None else ("%.3f" % r["wilson"]), r["state"]))
    print()
    if b["banked"]:
        print("  banked -> vault.apply: " + ", ".join(b["banked"]))
    for sk in b["skipped"]:
        print("  NOT banked: " + sk)
    for r in rows:
        for n in (r["notes"] or []):
            print("  %-9s %s" % (r["claim"], n))
    if live is not None:
        print("  %-9s %9s %8s %8s  %s" % (live["claim"], live["attempts"], live["caught"],
                                          "%.3f" % live["wilson"], live["state"]))
    print("  " + live_note)
    print("\n  vault.forget: " + forget_note())
    print("\n  ⚠ nothing was applied. Every attempt is a proposal the door MUST reject, and each "
          "is rejected before the board is asked.")
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    raise SystemExit(main())
